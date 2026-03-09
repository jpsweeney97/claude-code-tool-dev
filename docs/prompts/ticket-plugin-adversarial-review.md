# Adversarial Review: Ticket Plugin

## Objective

Perform an adversarial security and correctness review of the ticket plugin at `packages/plugins/ticket/`. Your goal is to find bugs, bypass vectors, logic errors, and design weaknesses that the authors may have missed — including vulnerabilities that existing tests don't cover.

You are reviewing a Claude Code plugin that manages work tickets through a 4-stage mutation pipeline (classify → plan → preflight → execute), gated by a PreToolUse hook that validates commands and injects trust metadata.

## Threat Model

The plugin defends against **accidental autonomy** — a subagent creating/modifying tickets without proper authorization. It does NOT claim resistance against a deliberately adversarial Claude instance, but it should be robust against:

1. **Subagent boundary violations** — agents performing mutations they shouldn't
2. **Trust field forgery** — bypassing hook-injected trust metadata
3. **Pipeline stage skipping** — jumping to execute without classify/plan/preflight
4. **Data corruption** — race conditions, malformed input, partial writes
5. **Policy bypass** — circumventing autonomy config, session caps, or dedup windows

## Claude Code Background

If you're unfamiliar with Claude Code's extension system, this section explains the two key primitives this plugin uses: **hooks** and **plugins**.

### What is Claude Code?

Claude Code is Anthropic's CLI tool that lets Claude operate as an interactive coding agent — it reads files, writes code, runs commands, and manages projects. Claude Code has an extension system that lets developers customize its behavior.

### Hooks

Hooks are event handlers that fire at specific lifecycle points during a Claude Code session. When Claude is about to use a tool (read a file, run a bash command, write a file), the runtime fires events that hooks can intercept.

The critical hook event for this review is **PreToolUse** — it fires *before* a tool call executes and can **allow**, **deny**, or **escalate** the action. This is how the ticket plugin gates all mutations: a PreToolUse hook on the `Bash` tool inspects every shell command Claude is about to run, and either allows it (with injected trust metadata) or denies it.

**How hooks work:**
1. Claude Code fires an event (e.g., "Claude wants to run `python3 scripts/ticket_engine_user.py classify payload.json`")
2. The hook script receives the event as JSON on stdin (includes `session_id`, `cwd`, `tool_name`, `tool_input`, and optionally `agent_id` if a subagent initiated the action)
3. The script validates the command and returns a JSON decision on stdout:
   - `permissionDecision: "allow"` — proceed
   - `permissionDecision: "deny"` — cancel with a reason fed back to Claude
4. Exit code 0 = proceed (or use JSON decision); exit code 2 = block

**Key property for this review:** The `agent_id` field in the hook input is the authoritative signal for whether a subagent (vs. the main Claude session) initiated the action. The ticket plugin uses this to determine trust origin — it's the foundation of the entire autonomy enforcement model.

### Plugins

A plugin is a self-contained directory of components that extends Claude Code. Plugins bundle together:

- **Skills** — markdown instruction files (SKILL.md) that teach Claude how to perform specific tasks. Invoked via `/skill-name` slash commands. The ticket plugin has two: `/ticket` (create/update/close/reopen) and `/ticket-triage` (health dashboard).
- **Hooks** — event handlers (as described above). The ticket plugin has one PreToolUse hook.
- **Agents** — subagent definitions for autonomous task delegation. The ticket plugin declares none.
- **Scripts** — supporting code that skills and hooks invoke. The ticket plugin's core logic lives here.

Plugins are installed via `claude plugin install` and their components are auto-discovered. The `${CLAUDE_PLUGIN_ROOT}` environment variable resolves to the plugin's installation directory at runtime, used by hooks and skills to locate scripts.

**Key property for this review:** A plugin's hook runs for *all* Bash commands in the session, not just those related to the plugin. The ticket plugin's hook must correctly pass through non-ticket commands (branch 4 in the guard) while only validating and injecting trust into ticket engine invocations.

## Architecture Summary

### Hook Guard (`hooks/ticket_engine_guard.py`)
- Single PreToolUse hook on Bash commands
- 5-branch decision tree:
  - Branch 1: engine mutations (`ticket_engine_user.py`, `ticket_engine_agent.py`) → validate subcommand/payload + inject trust fields
  - Branch 2: read-only scripts (`ticket_read.py`, `ticket_triage.py`) → allow, no injection
  - Branch 2b: audit script (`ticket_audit.py`) → allow for users, deny for agents
  - Branch 3: unrecognized `ticket_*.py` invocations → deny (catch-all for rogue/wrapped scripts)
  - Branch 4: non-ticket Bash commands → pass through silently
- Injects `session_id`, `hook_injected=true`, `hook_request_origin` into payload files atomically (temp + fsync + os.replace)
- Blocks shell metacharacters: `|;&\`$><\n\r`
- Validates payload paths resolve inside workspace root
- Derives `request_origin` from `event.agent_id` (authoritative), not from which entrypoint is called
- **Fail-open on crash**: exit 0 with empty JSON

### Engine Pipeline (`scripts/ticket_engine_{user,agent}.py`)
- Two entrypoints: user (hardcoded `request_origin="user"`) and agent (hardcoded `request_origin="agent"`)
- Both entrypoints import `ticket_trust.py` for trust triple validation (hook_injected, hook_request_origin, session_id)
- Origin mismatch rejection: hook-injected origin must match entrypoint origin
- 4 stages: classify (intent + confidence) → plan (dedup, field validation) → preflight (autonomy, TOCTOU, dependencies) → execute (write file)
- Payload files at `.claude/ticket-tmp/payload-<action>-<timestamp>-<hex>.json`

### Autonomy Enforcement
- Config in `.claude/ticket.local.md` YAML frontmatter: `autonomy_mode` (suggest/auto_audit/auto_silent), `max_creates_per_session`
- `suggest` (default): blocks all agent mutations
- `auto_audit`: allows agent mutations with session cap + JSONL audit trail
- `auto_silent`: reserved, currently blocked
- Agent mutations require `hook_injected=true` (defense-in-depth)
- Live policy reread before agent execute stage
- Audit trail fail-closed: if audit write fails, agent mutation blocked

### Data Model
- Tickets: `docs/tickets/YYYY-MM-DD-<slug>.md` with fenced YAML block
- IDs: `T-YYYYMMDD-NN` (date + daily sequence, zero-padded)
- Statuses: open → in_progress → done/wontfix (with blocked state)
- Dependencies: `blocked_by`/`blocks` lists with resolution-aware validation
- Dedup: SHA-256 fingerprint of normalized problem text + sorted key_file_paths, 24h window
- TOCTOU: SHA-256 of file bytes + mtime, checked before execute

### Test Coverage
- 500 tests across 18 files
- Covers: pipeline stages, autonomy, audit, hook allowlist, ID allocation, dedup, parse/render, triage, legacy migration, field validation, entrypoints, read operations, trust triple, hook integration, autonomy integration
- Known gap: no concurrency tests

## Review Instructions

### Phase 1: Hook Guard Analysis

Read `hooks/ticket_engine_guard.py` completely. Examine:

1. **Allowlist completeness**: Can a Bash command invoke the ticket engine in a form the hook doesn't recognize? Consider:
   - Python launcher variants (`python`, `python3.11`, `/usr/bin/python3`, `env python3`)
   - Path variations (relative, symlinked, `./scripts/...`)
   - Argument injection (extra arguments after valid ones)
   - Unicode homoglyphs in command strings
   - Whitespace manipulation (tabs, multiple spaces, leading/trailing)

2. **Metacharacter bypass**: The hook strips `2>&1` suffix before validation. Can this stripping be exploited? Are there other diagnostic suffixes that could carry payloads?

3. **Payload injection atomicity**: The hook writes trust fields to the payload file. What happens if:
   - The payload file is replaced between hook write and engine read (TOCTOU)
   - The payload file is a symlink to a file outside workspace
   - Two hooks fire simultaneously on the same payload file
   - The JSON in the payload file is crafted to survive field injection (e.g., duplicate keys)

4. **Fail-open implications**: The hook exits 0 on crash. What specific crash paths exist? Can an attacker trigger them intentionally to bypass validation?

5. **Origin determination**: `agent_id` presence determines origin. What if `agent_id` is present but empty string? What if the Claude Code runtime sends unexpected values?

### Phase 2: Pipeline Integrity

Read `scripts/ticket_engine_core.py` and both entrypoints. Examine:

1. **Stage skipping**: Can an agent call `execute` directly without going through classify/plan/preflight? The hook validates subcommand names but does it enforce ordering?

2. **Payload manipulation between stages**: The skill reads JSON responses, merges data back into payload, and writes the file before the next stage. Can the skill (or a subagent) modify the payload between stages to alter the pipeline's behavior?

3. **Origin mismatch edge cases**: The user entrypoint hardcodes `request_origin="user"` and the agent entrypoint hardcodes `request_origin="agent"`. The hook injects `hook_request_origin`. What happens when:
   - A user invokes the agent entrypoint directly
   - An agent invokes the user entrypoint directly
   - The hook fails to inject (fail-open path)

4. **Confidence threshold**: Classify returns a confidence score (default 0.95). Is this actually checked anywhere? Can low-confidence classifications proceed unchecked?

### Phase 3: Autonomy & Policy Bypass

Read `scripts/ticket_engine_core.py` (preflight/execute sections) and the autonomy config loading. Examine:

1. **Policy file manipulation**: `.claude/ticket.local.md` is read at preflight and re-read at execute. Can an agent modify this file between reads to escalate its own permissions? Is the file in the hook's allowlist?

2. **Session cap enforcement**: `max_creates_per_session` is enforced by counting existing audit entries. Can an agent:
   - Create tickets faster than the audit trail can record them?
   - Delete or corrupt audit entries to reset the count?
   - Use a different session ID to get a fresh cap?

3. **Dedup override**: `dedup_override: true` bypasses dedup checks. The contract says agents can't set this. Is this actually enforced in code?

4. **Reopen restrictions**: Reopen is documented as user-only. Is this enforced at the hook level, engine level, or both? Can an agent reopen by updating status directly?

5. **Dependency override**: `dependency_override: true` bypasses blocked_by checks. Is this agent-restricted?

### Phase 4: Data Integrity

Read `scripts/ticket_id.py`, `ticket_dedup.py`, `ticket_parse.py`, `ticket_render.py`. Examine:

1. **ID collision**: `allocate_id()` scans directories for same-day IDs. With no locking:
   - Two concurrent creates on the same day could allocate the same ID
   - Exclusive write (`O_CREAT | O_EXCL`) catches file-level collision, but the retry loop could produce unexpected IDs
   - What happens if the retry exhausts attempts?

2. **YAML injection**: Can ticket field values contain YAML that, when rendered and re-parsed, changes the document structure? Test with:
   - Values containing `\n` followed by YAML keys
   - Values containing fenced code block markers (`` ``` ``)
   - Values with YAML anchors/aliases (`*alias`, `&anchor`)

3. **Dedup normalization**: The fingerprint normalizes text (strip, collapse whitespace, lowercase, remove punctuation, NFC). Can two semantically different problems produce the same fingerprint? Can the same problem evade dedup by inserting non-normalized characters?

4. **TOCTOU fingerprint**: Uses `sha256(file_bytes + mtime)`. Mtime has second-level precision. Two modifications within the same second produce the same fingerprint even if content differs.

5. **Render roundtrip fidelity**: Does `parse → render → parse` produce identical results? Test with edge cases in field values (special YAML characters, multi-line strings, empty lists).

### Phase 5: Integration & System-Level

1. **Cross-plugin interaction**: The ticket plugin lives alongside other plugins. Can another plugin's hook interfere with ticket operations? Can ticket hooks interfere with other plugins?

2. **Git operations**: Tickets are git-tracked files. What happens during:
   - `git checkout` while a mutation is in progress
   - `git stash` that removes the payload file mid-pipeline
   - Merge conflicts in ticket files

3. **Workspace boundary**: The hook validates paths against `event.cwd`. What if `cwd` is different from the git root? What if the workspace has symlinks pointing outside?

4. **Audit trail integrity**: JSONL files in `docs/tickets/.audit/`. Can they be:
   - Appended to by agents (creating false audit entries)?
   - Truncated (losing history)?
   - The session_id sanitization removes `/\` and `\0` — are there other path-unsafe characters?

5. **Legacy format migration**: Old tickets (Gen 1-4) are normalized on read. Updates write v1.0 schema. Is this migration lossy? Can it produce invalid tickets?

### Phase 6: Code Quality & Technical Debt

Read all `scripts/*.py` files and `hooks/ticket_engine_guard.py`. This phase focuses on maintainability, efficiency, and engineering quality — not security.

1. **Dead code and unreachable branches**: Identify functions, parameters, imports, or conditional branches that are never exercised by any caller. Check for:
   - Functions defined but never called (or only called from tests)
   - Parameters with default values that no caller ever overrides
   - `if`/`elif` branches guarding conditions that can never be true given upstream validation
   - Imports used only in type annotations that could use `TYPE_CHECKING` guards

2. **Redundant validation**: The 4-stage pipeline validates at multiple layers (hook, entrypoint, core engine). Identify where the same check is performed more than once without adding defense-in-depth value. Distinguish between:
   - **Intentional redundancy** (defense-in-depth at a trust boundary — document but don't flag)
   - **Accidental redundancy** (same check repeated within the same trust domain — flag as waste)
   - Example: if the hook validates metacharacters AND the engine re-validates the same metacharacters on the same input, the second check adds no value because the engine only runs if the hook allowed it

3. **Abstraction quality**: Evaluate the module boundaries and function decomposition:
   - Functions doing too many things (>1 responsibility, >50 lines, >3 levels of nesting)
   - Functions that are too granular (single-line wrappers that obscure rather than clarify)
   - Data passed as dicts where a dataclass/namedtuple would catch errors at construction time
   - Stringly-typed values (status strings, action strings) that could be enums
   - God functions or god modules that accumulate unrelated responsibilities

4. **Error handling patterns**: Look for inconsistencies in how errors are handled:
   - Mix of exception styles (some functions raise, some return error dicts, some return None)
   - Bare `except` or overly broad `except Exception` that swallows useful diagnostics
   - Error messages that don't include the failing input or context
   - Silent fallbacks that mask bugs (e.g., defaulting to "user" on unexpected input instead of failing)

5. **Code duplication**: Identify repeated patterns that should be extracted:
   - Payload file read/write sequences repeated across stages
   - Path resolution logic duplicated between hook and engine
   - YAML parsing/rendering patterns copy-pasted across modules
   - Test setup code duplicated across test files instead of using fixtures

6. **Performance concerns**: Not critical for a ticket system, but flag obvious inefficiency:
   - Reading and re-parsing the same file multiple times in a single pipeline run
   - Scanning the entire tickets directory when an index or cache could work
   - O(n²) or worse algorithms where O(n) is straightforward
   - Blocking I/O in hot paths (e.g., fsync on every audit append)

7. **Naming and readability**:
   - Variables or functions whose names don't match their actual behavior
   - Inconsistent naming conventions across modules (e.g., `snake_case` vs `camelCase`, `get_*` vs `fetch_*` vs `load_*`)
   - Magic numbers or strings without named constants
   - Comments that are stale, misleading, or restate the code without adding insight

8. **Test quality**: Beyond coverage gaps (Phase 1-5), evaluate test engineering:
   - Tests that assert implementation details rather than behavior (brittle to refactoring)
   - Missing edge case coverage for boundary conditions (empty inputs, max values, Unicode)
   - Test names that don't describe the scenario being tested
   - Shared mutable state between tests (order-dependent test suites)
   - Assertion messages that don't help diagnose failures

## Deliverables

For each finding, provide:

1. **ID**: Sequential (F-001, F-002, ...)
2. **Severity**: Critical / High / Medium / Low / Informational
3. **Category**: One of the categories below
4. **Description**: What the issue is
5. **Reproduction**: Concrete steps or payload to trigger it (for security findings); code location and example (for quality findings)
6. **Impact**: What an attacker/runaway subagent could achieve (security), or what maintenance/reliability cost this creates (quality)
7. **Affected code**: File path and line numbers
8. **Suggested fix**: How to remediate
9. **Test gap**: Whether existing tests cover this scenario

### Categories

**Security categories** (Phases 1-5):
- Hook Bypass
- Pipeline Integrity
- Policy Bypass
- Data Corruption
- Race Condition
- Information Disclosure

**Quality categories** (Phase 6):
- Dead Code — unreachable branches, unused functions/parameters/imports
- Redundant Logic — duplicated validation or repeated code patterns
- Abstraction — poor module boundaries, god functions, missing type safety
- Error Handling — inconsistent patterns, swallowed errors, silent fallbacks
- Performance — unnecessary I/O, algorithmic inefficiency, repeated parsing
- Naming/Readability — misleading names, magic values, stale comments
- Test Quality — brittle assertions, missing edge cases, shared mutable state

### Severity Criteria

| Severity | Security Definition | Quality Definition |
|----------|--------------------|--------------------|
| Critical | Bypasses trust model entirely — agent can perform arbitrary mutations without authorization | N/A — quality issues are never Critical |
| High | Bypasses a specific control — agent can exceed caps, skip stages, or corrupt data | Architectural issue that will cause bugs or block refactoring — e.g., god module, stringly-typed trust boundaries |
| Medium | Weakens a control — theoretical bypass under specific conditions | Significant code smell that increases maintenance cost — e.g., duplicated validation across trust domains, inconsistent error patterns |
| Low | Minor issue — defense-in-depth gap or edge case handling | Minor inefficiency or readability issue — e.g., magic numbers, stale comments, unnecessary re-reads |
| Informational | Observation — no immediate risk but worth documenting | Style observation or potential future concern — e.g., naming inconsistency, test verbosity |

## Key Files to Read

| Priority | File | Why |
|----------|------|-----|
| P0 | `hooks/ticket_engine_guard.py` | All trust decisions flow through here |
| P0 | `scripts/ticket_engine_core.py` | Pipeline logic, autonomy enforcement |
| P0 | `scripts/ticket_engine_user.py` | User entrypoint — origin hardcoding |
| P0 | `scripts/ticket_engine_agent.py` | Agent entrypoint — origin hardcoding |
| P1 | `references/ticket-contract.md` | Authoritative specification |
| P1 | `skills/ticket/references/pipeline-guide.md` | State machine, payload schemas |
| P1 | `scripts/ticket_dedup.py` | Dedup fingerprinting |
| P1 | `scripts/ticket_id.py` | ID allocation |
| P1 | `scripts/ticket_trust.py` | Trust triple validation — imported by both entrypoints |
| P2 | `scripts/ticket_parse.py` | YAML parsing, legacy migration |
| P2 | `scripts/ticket_render.py` | Ticket file rendering |
| P2 | `scripts/ticket_validate.py` | Field type and value validation |
| P2 | `scripts/ticket_audit.py` | Audit trail management |
| P2 | `scripts/ticket_paths.py` | Path resolution, boundary checks |
| P3 | `tests/` | All test files — look for gaps |
| P3 | `.claude-plugin/plugin.json` | Plugin manifest |
| P3 | `skills/ticket/SKILL.md` | Skill instructions (what Claude sees) |
| P3 | `skills/ticket-triage/SKILL.md` | Triage skill instructions |

## Constraints

- Read every P0 and P1 file completely before reporting findings
- Do not assume tests are correct — verify test assertions against the contract
- Consider both the code AS WRITTEN and the contract AS SPECIFIED — discrepancies are findings
- Focus on exploitable issues over theoretical concerns
- If you find a bypass, verify it by tracing the code path — don't report speculative issues without evidence
