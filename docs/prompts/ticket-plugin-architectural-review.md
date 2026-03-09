# Architectural Review: Ticket Plugin

## Objective

Perform a deep structural and architectural review of the ticket plugin at `packages/plugins/ticket/`. Your goal is to evaluate module boundaries, abstraction quality, data flow design, error handling consistency, type safety, and maintainability — identifying engineering debt, design weaknesses, and opportunities for improvement that affect long-term evolution of the codebase.

This is NOT a security review.

## Review Model

The plugin implements a 4-stage mutation pipeline (classify → plan → preflight → execute) with a PreToolUse hook guard, two entrypoints (user/agent), and supporting modules for ID allocation, deduplication, parsing, rendering, auditing, and path resolution.

Evaluate the architecture against these quality dimensions:

1. **Modularity** — Are module boundaries drawn at the right places? Does each module have a single, clear responsibility?
2. **Coupling** — How tightly are modules connected? Can one be changed without cascading effects?
3. **Cohesion** — Does each module group related functionality, or does it accumulate unrelated concerns?
4. **Abstraction** — Are the right things abstracted? Are abstractions leaky, premature, or missing?
5. **Consistency** — Do similar operations follow the same patterns across the codebase?
6. **Extensibility** — How hard is it to add a new action, a new pipeline stage, or a new policy?
7. **Testability** — Does the architecture make testing easy or force contortions?

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

### Plugins

A plugin is a self-contained directory of components that extends Claude Code. Plugins bundle together:

- **Skills** — markdown instruction files (SKILL.md) that teach Claude how to perform specific tasks. Invoked via `/skill-name` slash commands. The ticket plugin has two: `/ticket` (create/update/close/reopen) and `/ticket-triage` (health dashboard).
- **Hooks** — event handlers (as described above). The ticket plugin has one PreToolUse hook.
- **Agents** — subagent definitions for autonomous task delegation. The ticket plugin declares none.
- **Scripts** — supporting code that skills and hooks invoke. The ticket plugin's core logic lives here.

Plugins are installed via `claude plugin install` and their components are auto-discovered. The `${CLAUDE_PLUGIN_ROOT}` environment variable resolves to the plugin's installation directory at runtime, used by hooks and skills to locate scripts.

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

### Phase 1: Module Decomposition

Read every `.py` file in `scripts/` and `hooks/`. Map the actual module graph.

1. **Responsibility analysis**: For each module, write a one-sentence description of what it does. If you need more than one sentence, it may have too many responsibilities. Specifically examine:
   - `ticket_engine_core.py` — Does it accumulate too many concerns (pipeline orchestration, validation, autonomy enforcement, file I/O)?
   - The relationship between `ticket_parse.py` and `ticket_render.py` — Are parse and render truly inverses? Is there shared logic that belongs in neither?
   - `ticket_paths.py` — Is it a coherent module or a grab-bag of path utilities?

2. **Dependency graph**: Trace import relationships between modules. Identify:
   - Circular dependencies (direct or transitive)
   - Modules that import from too many siblings (high fan-in suggests a god module; high fan-out suggests a module doing too many things)
   - Layers that skip levels (e.g., a utility module importing from the core engine)

3. **Interface quality**: For each module's public functions:
   - Are parameters well-typed, or do functions accept `dict` / `Any` when a narrower type would catch errors earlier?
   - Do return types clearly communicate success vs. failure, or do callers need to inspect return values heuristically?
   - Are there functions that exist only to satisfy one caller? (Should they be private or inlined?)

4. **Module size distribution**: Flag modules over 400 lines. Evaluate whether they could be split without creating artificial seams.

### Phase 2: Data Flow & Pipeline Design

Trace the full lifecycle of a ticket mutation from skill invocation through file write.

1. **Pipeline state threading**: How does state flow between the 4 pipeline stages?
   - Is state threaded through function parameters, shared mutable dicts, file reads, or global state?
   - Are intermediate representations well-defined, or does each stage operate on an amorphous payload dict?
   - Could a stage receive malformed input from its predecessor? What catches this?

2. **Payload schema**: The payload JSON evolves as it passes through stages. Examine:
   - Is the payload schema documented or enforced at any point, or is it implicitly defined by what each stage reads/writes?
   - Do stages add keys to the payload? Do any stages remove or rename keys?
   - Could a typed data model (dataclass, TypedDict, Pydantic) replace the raw dict and catch integration errors at definition time?

3. **Entrypoint duplication**: The user and agent entrypoints (`ticket_engine_user.py`, `ticket_engine_agent.py`) have overlapping logic.
   - How much code is duplicated between them?
   - Could they be a single entrypoint with a parameter, or does their divergence justify separate files?
   - What happens when shared behavior changes — must both files be updated?

4. **File I/O patterns**: Trace every file read and write in a single pipeline run.
   - How many times is the payload file read/written per pipeline invocation?
   - How many times are ticket files scanned (for ID allocation, dedup, dependency checks)?
   - Are there opportunities to read once and pass data through, rather than re-reading?

### Phase 3: Abstraction & Type Safety

1. **Stringly-typed values**: Identify values that are passed as strings where enums or typed constants would prevent typos and enable exhaustiveness checking:
   - Action names (`create`, `update`, `close`, `reopen`)
   - Status values (`open`, `in_progress`, `done`, `wontfix`, `blocked`)
   - Origin values (`user`, `agent`)
   - Pipeline stage names (`classify`, `plan`, `preflight`, `execute`)
   - Autonomy modes (`suggest`, `auto_audit`, `auto_silent`)

2. **Dict vs. structured types**: Find places where dicts carry structured data that has a known schema. Evaluate whether:
   - Field access could fail silently with `.get()` defaulting to `None`
   - Required fields are documented only in comments
   - The same dict shape is constructed in multiple places without a shared definition

3. **Error representation**: How do functions communicate errors?
   - Do some return `None`, some raise exceptions, some return error dicts?
   - Is there a consistent Result/Either pattern, or does each function invent its own?
   - Can callers distinguish between "operation failed" and "precondition not met" and "unexpected error"?

4. **Abstraction spectrum**: Identify both:
   - **Missing abstractions**: Repeated patterns that should be extracted (e.g., "read payload, validate, transform, write payload" if done in multiple stages)
   - **Premature abstractions**: Wrappers or helpers that serve a single call site and obscure rather than clarify
   - **Leaky abstractions**: Modules that expose internal details (file paths, format specifics) to callers that shouldn't need to know

### Phase 4: Error Handling & Failure Modes

1. **Error handling consistency**: Catalog the error handling patterns used across the codebase:
   - Which functions raise exceptions? Which return error indicators? Which do both?
   - Are there `except Exception` or bare `except` clauses? What do they catch and why?
   - Do error messages include sufficient context (the failing input, the expected format, the operation being attempted)?

2. **Silent fallbacks**: Identify places where unexpected input is silently normalized rather than rejected:
   - Default values used when a key is missing — is the default correct, or does it mask a bug?
   - String normalization that could hide semantic differences
   - Catch blocks that log but continue, potentially producing incorrect output

3. **Failure propagation**: Trace what happens when each component fails:
   - Hook crashes → fail-open (exit 0). Is this the right choice architecturally? What are the trade-offs?
   - Payload file missing or malformed → does the pipeline produce a clear error or a confusing traceback?
   - Ticket directory missing or read-only → where does this surface?
   - Config file (`ticket.local.md`) missing or malformed → graceful degradation or crash?

4. **Invariant enforcement**: Are critical invariants asserted or merely assumed?
   - "Every ticket has a valid ID" — enforced where?
   - "Payload files exist in `.claude/ticket-tmp/`" — checked by whom?
   - "Hook-injected fields are present for agent mutations" — validated at which layer(s)?

### Phase 5: Naming, Readability & Conventions

1. **Naming audit**: Read through function and variable names. Flag:
   - Names that don't match behavior (e.g., `get_*` that has side effects, `validate_*` that also transforms)
   - Inconsistent naming across modules (e.g., `load_*` vs `read_*` vs `parse_*` for similar operations)
   - Ambiguous names that require reading the implementation to understand (e.g., `process`, `handle`, `do_thing`)
   - Magic strings and numbers without named constants

2. **Comment quality**: Evaluate existing comments:
   - Do comments explain *why*, not *what*?
   - Are there stale comments that describe behavior the code no longer has?
   - Are there complex sections that lack any explanation?
   - Are there comments that merely restate the code?

3. **Code organization within files**: For larger files:
   - Are related functions grouped together?
   - Is there a logical reading order (public API at top, helpers below)?
   - Are there private functions that could be identified with `_` prefix conventions?

4. **Convention consistency**: Check whether patterns are applied uniformly:
   - Import ordering (stdlib, third-party, local)
   - Function signature style (keyword args, type annotations)
   - Path handling (pathlib vs. os.path vs. string manipulation)
   - JSON/YAML handling (consistent library usage, error handling)

### Phase 6: Test Architecture

1. **Test organization**: How are tests structured?
   - One test file per module, or a different mapping?
   - Are test names descriptive of the scenario and expected behavior?
   - Is there a consistent test naming convention?

2. **Test isolation**: Do tests depend on each other?
   - Shared mutable state (module-level variables, files on disk)
   - Test ordering dependencies
   - Fixtures that modify global state without cleanup

3. **Test granularity**: Are tests at the right level of abstraction?
   - Are there tests that assert implementation details (specific function calls, internal dict keys) rather than behavior (given input X, the output/side-effect is Y)?
   - Are there integration gaps — individual units tested but never exercised together?
   - Are there tests that duplicate coverage already provided by other tests?

4. **Test helpers and fixtures**: Evaluate shared test infrastructure:
   - Is setup code duplicated across test files?
   - Are there helper functions that could be shared fixtures?
   - Do fixtures do too much, making tests hard to understand in isolation?

5. **Edge case coverage**: For each module's critical functions, evaluate whether tests cover:
   - Empty inputs
   - Maximum/boundary values
   - Unicode content
   - Malformed/partial data
   - File system edge cases (missing dirs, permission errors, symlinks)

### Phase 7: Extensibility Assessment

1. **Adding a new action**: Walk through what it would take to add a 5th action (e.g., `archive`):
   - How many files need to change?
   - Are action lists hardcoded in multiple places, or defined once?
   - Does the pipeline design accommodate new actions naturally, or require special-casing?

2. **Adding a new pipeline stage**: If a new stage were needed between `plan` and `preflight`:
   - Where would it be added?
   - Would existing stages need modification?
   - Is the stage sequence hardcoded or configurable?

3. **Adding a new policy**: If a new autonomy mode were added (e.g., `auto_approved`):
   - How many code paths need updating?
   - Are policy checks concentrated or scattered?

4. **Schema evolution**: When the ticket format changes:
   - How is backward compatibility handled?
   - Is the migration path clear?
   - Are format versions tracked?

## Deliverables

For each finding, provide:

1. **ID**: Sequential (A-001, A-002, ...)
2. **Severity**: High / Medium / Low / Informational
3. **Category**: One of the categories below
4. **Description**: What the issue is
5. **Location**: File path(s) and line numbers
6. **Evidence**: Concrete code examples demonstrating the issue
7. **Impact**: What maintenance, reliability, or evolution cost this creates
8. **Suggested improvement**: How to remediate, with trade-offs noted
9. **Test gap**: Whether existing tests would catch regressions during remediation

### Categories

- **Module Design** — responsibility violations, coupling issues, cohesion problems, dependency graph concerns
- **Data Flow** — pipeline state threading, payload schema, I/O patterns, entrypoint duplication
- **Abstraction** — missing/premature/leaky abstractions, stringly-typed values, dict-as-schema
- **Type Safety** — missing type annotations, overly broad types, dict-based data models
- **Error Handling** — inconsistent patterns, silent fallbacks, swallowed errors, missing context
- **Naming/Readability** — misleading names, magic values, stale comments, convention inconsistency
- **Test Architecture** — isolation problems, granularity issues, missing edge cases, duplicated setup
- **Extensibility** — hardcoded lists, scattered policy checks, schema evolution gaps

### Severity Criteria

| Severity | Definition |
|----------|-----------|
| High | Architectural issue that will cause bugs, block refactoring, or force workarounds — e.g., god module, stringly-typed trust boundaries, inconsistent error model |
| Medium | Significant structural concern that increases maintenance cost — e.g., duplicated logic across entrypoints, missing types on critical paths, scattered policy checks |
| Low | Minor structural issue — e.g., magic numbers, inconsistent naming, single-use abstractions, unnecessary re-reads |
| Informational | Observation or style preference — e.g., import ordering, comment density, test naming convention |

## Key Files to Read

| Priority | File | Why |
|----------|------|-----|
| P0 | `scripts/ticket_engine_core.py` | Largest module, pipeline orchestration, most likely to have accumulated responsibilities |
| P0 | `hooks/ticket_engine_guard.py` | Trust boundary — evaluate interface quality and separation of concerns |
| P0 | `scripts/ticket_engine_user.py` | Entrypoint — evaluate duplication with agent entrypoint |
| P0 | `scripts/ticket_engine_agent.py` | Entrypoint — evaluate duplication with user entrypoint |
| P1 | `scripts/ticket_parse.py` | Data model — evaluate type safety and roundtrip fidelity |
| P1 | `scripts/ticket_render.py` | Data model — evaluate abstraction boundary with parse |
| P1 | `scripts/ticket_id.py` | Standalone module — evaluate interface quality |
| P1 | `scripts/ticket_dedup.py` | Standalone module — evaluate abstraction choices |
| P1 | `scripts/ticket_trust.py` | Trust triple validation — evaluate interface with entrypoints |
| P2 | `scripts/ticket_validate.py` | Field validation — evaluate type safety patterns |
| P2 | `scripts/ticket_audit.py` | Supporting module — evaluate I/O patterns |
| P2 | `scripts/ticket_paths.py` | Utility module — evaluate cohesion |
| P2 | `references/ticket-contract.md` | Authoritative specification — compare code against spec |
| P2 | `skills/ticket/references/pipeline-guide.md` | Pipeline design reference |
| P3 | `tests/` | All test files — evaluate test architecture |
| P3 | `.claude-plugin/plugin.json` | Plugin manifest — evaluate component registration |

## Constraints

- Read every P0 and P1 file completely before reporting findings
- Focus on structural concerns — defer security issues to the adversarial review
- Evaluate architecture as-built, not against an ideal framework. Flag issues that create real maintenance or evolution costs, not theoretical purity violations
- When suggesting improvements, consider the cost of the change relative to the benefit. A small inconsistency in a stable module is lower priority than a structural issue in actively-evolving code
- Trace code paths to verify findings — don't report concerns based on file names or function signatures alone
