# Delegation Capability — Design Spec

**Date:** 2026-03-06
**Status:** Design — reviewed (3 rounds: 7 evaluative + 10 adversarial/collaborative + 5 adversarial amendments)
**Source:** Comparison with [skill-codex](https://github.com/skills-directory/skill-codex.git) + 2 Codex consultations + 3 Codex dialogues (evaluative `019cc3c6`, adversarial `019cc3f0`, collaborative `019cc41a`)

---

## Problem

The cross-model plugin treats Codex exclusively as an **advisor** (text-in/text-out consultation via MCP). It cannot delegate execution tasks — have Codex read files, run commands, write code, and produce diffs. This is a fundamentally different interaction pattern (worker vs. peer) that the plugin currently lacks.

The `skill-codex` project solves this with a 65-line skill that shells out to `codex exec`. That approach works but has no credential protection, no analytics, no diff review, and no dirty-tree safety. This spec designs a delegation capability that integrates with the existing plugin infrastructure.

## Prior Art: skill-codex

| Dimension | skill-codex | cross-model (current) |
|-----------|-------------|----------------------|
| Integration | Bash → `codex exec` | MCP server (`codex mcp-server`) |
| Codex role | Worker (executes tasks) | Advisor (gives opinions) |
| Credential protection | None | Tiered hook guard (strict/contextual/broad) |
| Analytics | None | Event log + consultation stats |
| Diff review | None | N/A (no file changes) |
| Multi-turn | `codex exec resume --last` | Full dialogue pipeline with convergence |

The two patterns are complementary. Delegation fills a gap that consultation deliberately doesn't address.

---

## Architecture

### New verb, not an extension of `/codex`

Delegation gets a separate `/delegate` skill. Reasons:

1. `/codex` is hardwired to `consultation_outcome` events and `mode="server_assisted"` throughout the skill, analytics emitter, and event reader.
2. The consultation contract frames Codex as a consultant, not an executor. Adding `--exec` would overload the verb and muddy the safety model.
3. Separate verb = separate contract, separate analytics, separate safety invariants.

### Adapter script, not raw shell construction

The skill does not construct `codex exec` commands inline. A local adapter script (`scripts/codex_delegate.py`) provides one deterministic boundary for:

- Flag parsing and validation
- Prompt credential scanning (pre-dispatch)
- `codex exec` subprocess invocation
- JSONL event stream parsing
- Thread ID extraction
- Analytics event emission

The skill's only job is to: parse user arguments, write input JSON, run the adapter, review changes, report results.

### Clean-tree gate

`codex exec` modifies the working tree. Reliable diff attribution requires knowing what Codex changed vs. what was already dirty. Step 1 enforces a clean-tree precondition.

**Gate implementation:** The adapter runs `git status --porcelain=v1 -z --ignore-submodules=none` and blocks if the output is non-empty.

| State | Blocks | Rationale |
|-------|--------|-----------|
| Staged changes | Yes | Would conflate with Codex's changes in `git diff` |
| Unstaged modifications | Yes | Same attribution problem |
| Untracked files | Yes | Codex may create files with conflicting names |
| Dirty submodules | Yes | `--ignore-submodules=none` catches these |
| Ignored files | No | Not visible to `git diff`, no attribution risk |

**Non-git directories:** Fail deterministically with `"repo resolution failed: not a git repository"`. The adapter requires a git repo.

**Scope:** The gate blocks on *any* dirty file, not just files in the task's scope. Task-scoped gating without a path envelope gives false precision — Codex may touch files the user didn't anticipate. Broad blocking is the correct Step 1 behavior.

Future steps add worktree-based execution (create a disposable worktree, run Codex there, review changes, merge or discard).

### Readable-secret-file gate

The clean-tree gate passes ignored files (they don't affect `git diff` attribution). But `.gitignore`'d files like `.env`, `*.pem`, and `*.key` are fully readable by Codex within the `workspace-write` sandbox. The adapter includes a best-effort gate to catch common secret files.

**Gate implementation:** After the clean-tree gate passes, run `git ls-files --others --ignored --exclude-standard` and match output against high-confidence secret pathspecs:

```
.env  .env.*  *.pem  *.key  *.p12  .npmrc  .netrc  auth.json
```

**Template exemptions:** Files matching `.env.example`, `.env.sample`, `.env.template` are excluded from the match.

**On match:** Block with `status=blocked` listing matched paths. No bypass flag in Step 1 — per-invocation bypass undermines the guard. Allowlist configuration deferred to Step 2.

**Limitations:** This is a best-effort gate, not a guarantee. It catches common patterns but cannot detect secrets in arbitrarily-named files. The trust model section documents this explicitly.

---

## Safety & Trust Model

`/delegate` operates under a **narrower safety contract** than `/codex` or `/dialogue`. The consultation contract (`references/consultation-contract.md`) does NOT govern delegation.

**Single-user assumption:** This plugin is used by a single developer who controls `.codex/config.toml` and the Codex CLI environment. Ambient Codex configuration (approval policy, network settings, writable roots) is always aligned with the user's intent. The adapter does not preflight or constrain Codex's effective configuration.

| Layer | Consultation (`/codex`, `/dialogue`) | Delegation (`/delegate`) |
|-------|--------------------------------------|--------------------------|
| **Primary enforcement** | Prompt sanitization (credential guard hook) | Sandbox containment + repo-state gating |
| **Secondary** | MCP transport isolation | Prompt credential scan (defense-in-depth) |
| **Tertiary** | — | Readable-secret-file gate (best-effort) |
| **Contract** | Consultation contract | This spec (delegation contract) |
| **Trust boundary** | Codex sees only the prompt text | Codex reads repo files autonomously within sandbox |

### Security posture

`/delegate` is appropriate for repos whose **tracked readable contents** the user is willing to expose to Codex. The readable-secret-file gate provides best-effort blocking of common `.gitignore`'d secret files, but does not guarantee repos are secret-free.

Specifically:
- Tracked files in the repo are readable by Codex during autonomous execution.
- Common untracked secret files (`.env`, `*.pem`, `*.key`) are blocked by the readable-secret-file gate.
- Arbitrarily-named secret files in `.gitignore` are NOT detected.
- The sandbox constrains writes and command execution, not reads.

### Key implications

1. **Sandbox is the primary enforcement layer.** The sandbox constrains what commands Codex can execute and what files it can write.

2. **Prompt scanning is defense-in-depth only.** The adapter scans the delegation prompt for credentials before dispatch. This catches accidental credential inclusion in the user's instruction but does NOT prevent Codex from reading credentials in repo files.

3. **`danger-full-access` is blocked entirely in Step 1.** This prevents arbitrary system access until stronger controls exist (Step 2+).

4. **`-c` config overrides are adapter-synthesized only.** The adapter synthesizes exactly one `-c` override: `-c model_reasoning_effort=...` from the `reasoning_effort` enum field. Arbitrary `-c` is not exposed in the input schema.

### Governance rules

1. **No auto-escalation:** `danger-full-access` is blocked entirely in Step 1.
2. **`--full-auto` is opt-in only:** Never auto-enable. Never "offer" it implicitly. Requires explicit user flag.
3. **Clean tree required:** Delegation fails deterministically on dirty trees.
4. **Credential scan is fail-closed:** If scan cannot complete (scanner error), block dispatch.
5. **Claude reviews all changes:** The skill always runs `git status --short` after delegation and presents Claude's assessment before considering the task complete.
6. **No user content echoed before credential scan:** Error messages from pipeline steps before the credential scan never include user-provided string values.

---

## Deliverables

### 1. Shared event log helper (`scripts/event_log.py`)

Extract log infrastructure into a shared module for use by `emit_analytics.py` and `codex_delegate.py`.

**Scope:** Analytics-emitter only. `codex_guard.py` is **not migrated** — it keeps its own `_ts()` (microsecond precision) and `session_id="unknown"` default. This avoids unrelated behavior changes to the guard's existing log shape.

**Exports:**

```python
LOG_PATH: Path          # ~/.claude/.codex-events.jsonl
def ts() -> str         # ISO 8601 UTC with Z suffix (second precision)
def append_log(entry: dict) -> bool  # Atomic append, returns success
def session_id() -> str | None       # From CLAUDE_SESSION_ID, nullable, never fabricated
```

**Consumers:** `emit_analytics.py` (replaces local `_append_log`, `_ts`, `_session_id`) and `codex_delegate.py` (new).

### 2. Shared credential scanner (`scripts/credential_scan.py`)

Extract credential detection from `codex_guard.py` into a public module. Both the hook and the adapter import from it.

**Exports:**

```python
@dataclass
class ScanResult:
    action: Literal["allow", "block", "shadow"]
    tier: str | None       # "strict", "contextual", "broad", or None for allow
    reason: str | None     # Human-readable match description

def scan_text(text: str) -> ScanResult
```

**`scan_text` behavior:** Runs strict tier, then contextual tier (with placeholder suppression), then broad tier. Returns on first match. `action="allow"` if no patterns match.

**Migration:** `codex_guard.py` imports `scan_text` from `credential_scan.py` and calls it from `_check_prompt()`. Hook entry point (`main()`), stdin parsing, exit code semantics, and all `PostToolUse` logic remain in `codex_guard.py`. The hook's external interface is unchanged.

### 3. Adapter script (`scripts/codex_delegate.py`)

Single entry point for all delegation. Claude makes one Bash call; the adapter handles everything.

#### Input

JSON file with fields:

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `prompt` | string | Yes | — |
| `model` | string | No | Codex default |
| `sandbox` | enum | No | `workspace-write` |
| `reasoning_effort` | enum | No | `high` |
| `full_auto` | bool | No | `false` |

**Sandbox values:** `read-only`, `workspace-write`. `danger-full-access` is rejected: `"policy: danger-full-access not supported in Step 1"`.

**`prompt` is required.** Absent or empty prompt → `"validation failed: prompt required"`.

#### Pipeline

```
 1. Resolve repo root: git rev-parse --show-toplevel → chdir
 2. Allocate temp files (0600 permissions via Python tempfile API)
 3. Read input JSON (Phase A — file exists, parses as JSON object)
 4. Credential scan on prompt field (before any user content is echoed)
 5. Validate fields (Phase B — reject unknown, check enums, check conflicts)
 6. CLI version check: codex --version → require >= 0.111.0
 7. Clean-tree gate: git status --porcelain=v1 -z --ignore-submodules=none
 8. Readable-secret-file gate: git ls-files --others --ignored --exclude-standard
 9. Build codex exec command:
    codex exec --json -o {output_tempfile}
    Resolved flags: -s, -m, -c model_reasoning_effort=..., --full-auto
    No --skip-git-repo-check
10. Run subprocess, capture JSONL stdout + exit code
11. Parse JSONL events (tolerant — see JSONL Parsing below)
12. Read -o output file → summary (nullable)
13. Emit delegation_outcome event to log (only if step 3 succeeded)
14. Clean up temp files in finally block
    → Return structured JSON to stdout
```

**Split validation (P0-3 fix):** Steps 3-5 implement a two-phase validation. Phase A (step 3) parses the input without echoing content. Step 4 runs the credential scan on the `prompt` field. Phase B (step 5) performs semantic validation (enums, conflicts) and may reference field names and enum literals in error messages but never echoes arbitrary user-provided string values. This ensures no credential can leak via error messages.

**`-c` config overrides:** The adapter synthesizes `-c model_reasoning_effort={value}` from the `reasoning_effort` input field. This is the only `-c` override. Arbitrary `-c` passthrough is not exposed in the input schema.

#### JSONL Parsing

Tolerance model matches `read_events.py:read_all()` — parse what you can, skip what you can't.

| Condition | Handling |
|-----------|----------|
| Non-JSON line | Skip, log warning to stderr, continue |
| Valid JSON but not an object | Skip, continue |
| Unknown event type | Ignore (forward compatibility) |
| Known event missing expected fields | Degrade gracefully — use `None` for missing fields |
| `turn.failed` event | Capture as runtime failure detail in output |
| `error` event | Capture error details for reporting |
| Zero usable events after parsing | Fatal — return `status=error` with reason `"no usable JSONL events"` |

**Extraction targets:**

| Event | Extraction | Nullable |
|-------|-----------|----------|
| `thread.started` | `thread_id` | Yes — if missing, generate UUID and log warning |
| `item.completed` (type=`command_execution`) | `command`, `exit_code` → `commands_run` | Yes — empty list if no commands |
| `item.completed` (type=`agent_message`) | `text` → last message as candidate summary | Yes |
| `turn.completed` | `usage.input_tokens`, `usage.output_tokens` → `token_usage` | Yes |
| `turn.failed` | Error details → `runtime_failures` | Yes — empty list if none |

#### Failure Modes

Each pipeline step has deterministic failure handling:

| Step | Failure | Status | Exit | Message pattern |
|------|---------|--------|------|-----------------|
| 1 | Not a git repo | `error` | 1 | `"repo resolution failed: not a git repository"` |
| 2 | Temp file creation fails | `error` | 1 | `"temp allocation failed: {reason}"` |
| 3 | Input file missing/unreadable | `error` | 1 | `"input read failed: {reason}"` |
| 3 | Input is not valid JSON | `error` | 1 | `"input parse failed: invalid JSON"` |
| 4 | Credential match | `blocked` | 0 | Log block event, report matched tier |
| 4 | Scanner error | `blocked` | 0 | `"credential scan failed: {reason}"` |
| 5 | Unknown field in input | `error` | 1 | `"validation failed: unknown field '{field}'"` |
| 5 | Invalid enum value | `error` | 1 | `"validation failed: invalid {field} value"` |
| 5 | --full-auto + read-only | `error` | 1 | `"conflict: --full-auto and -s read-only are mutually exclusive"` |
| 6 | `codex` not found in PATH | `error` | 1 | `"version check failed: codex not found in PATH"` |
| 6 | Version below 0.111.0 | `error` | 1 | `"version check failed: codex {version} < 0.111.0"` |
| 6 | Unparseable version output | `error` | 1 | `"version check failed: cannot parse codex --version output"` |
| 7 | Dirty tree | `blocked` | 0 | List dirty paths in error field |
| 8 | Readable secret file found | `blocked` | 0 | List matched secret file paths |
| 9 | Flag-building logic error | `error` | 1 | `"command build failed: {reason}"` |
| 10 | Subprocess spawn failure | `error` | 1 | `"exec failed: subprocess spawn error. {reason}"` |
| 10 | Subprocess timeout/signal | `error` | 1 | `"exec failed: process {signal/timeout}. Exit: {code}"` |
| 11 | Zero usable JSONL events | `error` | 1 | `"parse failed: no usable JSONL events from codex exec"` |
| 11 | Partial parse (some malformed) | `ok` (degraded) | 0 | Log warnings, proceed with parsed events |
| 12 | Output file absent | `ok` (degraded) | 0 | `summary=null`, log warning |
| 13 | Log write failure | `ok` (degraded) | 0 | Event lost, log warning to stderr |
| 14 | Temp cleanup failure | N/A | N/A | Non-fatal, log warning to stderr |

**Note:** Steps 3 and 5 never echo arbitrary user-provided string values in error messages. Step 3 reports structural parse errors only. Step 5 may reference field names and enum literals but not the prompt or other user-authored content.

**Emission rule:** `delegation_outcome` events are emitted only if step 3 (Phase A parse) succeeds. If the input file is missing, unreadable, or not valid JSON, no event is logged — the adapter has insufficient data to construct a meaningful event.

#### Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success, blocked, or degraded (check `status` field) |
| 1 | Adapter error (bad input, internal failure) |

Exit 0 for `blocked` is intentional — the adapter communicates blocks cleanly via structured JSON. A non-zero exit for `blocked` would trigger the `PostToolUseFailure` Bash hook in `hooks.json`, causing unintended nudge behavior.

#### Output

```json
{
  "status": "ok|error|blocked",
  "thread_id": "...",
  "summary": null,
  "commands_run": [
    {"command": "...", "exit_code": 0}
  ],
  "exit_code": null,
  "token_usage": null,
  "runtime_failures": [],
  "error": null
}
```

`summary` is nullable — a failing run may not produce a final assistant message. `token_usage` is nullable — an erroring run may not emit `turn.completed`. `exit_code` is nullable — only present when Codex actually ran (status `ok`). `runtime_failures` captures `turn.failed` events (empty list if none).

**Status values:**

| Status | Meaning |
|--------|---------|
| `ok` | `codex exec` completed (exit code may still be non-zero) |
| `blocked` | Pre-dispatch gate failed (credential, dirty tree, readable secret, or scanner error) |
| `error` | Adapter-level failure (bad input, subprocess crash, parse failure, version mismatch) |

#### Temp file cleanup

> **Amended (F6):** Creation-ownership — each creator cleans its own file. The skill creates the input JSON and cleans it. The adapter creates the `-o` output file and cleans it. This replaces the original design where the adapter cleaned both.

The adapter must unlink the `-o` output file in a `finally` block on all Python exit paths (success, error, blocked). The skill cleans the input JSON file after the adapter returns. SIGKILL bypasses Python's `finally` — this is accepted as a local same-user residue risk, not a remote disclosure. Cleanup failure is non-fatal but logged to stderr.

### 4. Delegation skill (`skills/delegate/SKILL.md`)

#### Frontmatter

```yaml
---
name: delegate
description: >-
  Delegate coding tasks to Codex CLI for autonomous execution.
  Use when user says "delegate", "have codex do", "codex exec",
  "run this with codex", or wants Codex to write code, fix bugs,
  or refactor autonomously. Not for consultation — use /codex
  or /dialogue for second opinions.
argument-hint: "[-m <model>] [-s {read-only|workspace-write}] [-t {minimal|low|medium|high|xhigh}] [--full-auto] PROMPT"
user-invocable: true
---
```

#### Skill flow

```
1. Parse flags from $ARGUMENTS:
   -m <model>           → model (optional)
   -s <sandbox>         → sandbox (default: workspace-write)
   -t <effort>          → reasoning_effort (default: high)
   --full-auto          → full_auto (requires explicit flag)

2. Validate:
   - --full-auto + -s read-only → error
   - danger-full-access → error ("not supported in this version")

3. Write input JSON to $TMPDIR/codex_delegate_input_{random}.json

4. Run adapter:
   python3 {plugin_root}/scripts/codex_delegate.py $TMPDIR/codex_delegate_input_{random}.json

5. Read adapter output. Branch on status:
   - blocked → relay block reason to user
   - error → relay error to user
   - ok → proceed to review

6. Resolve repo root for review:
   - Run: git rev-parse --show-toplevel → cd to repo root

7. Review changes:
   - Run: git status --short (from repo root — catches all changes including new files)
   - Run: git diff (for modified tracked files)
   - Present summary: what Codex did, which files changed, commands it ran
   - Claude's own assessment of the changes (quality, correctness, completeness)

8. Report to user:
   - Codex's summary (from adapter output)
   - Files changed (from git status --short)
   - Claude's assessment
   - Thread ID (diagnostic — for manual codex exec resume if needed)
```

### 5. Analytics event (`delegation_outcome`)

New event type in the JSONL log.

```json
{
  "schema_version": "0.1.0",
  "event": "delegation_outcome",
  "ts": "2026-03-06T12:00:00Z",
  "consultation_id": "uuid",
  "session_id": "from-env-or-null",
  "thread_id": "from-codex-jsonl-or-null",
  "dispatched": true,
  "sandbox": "workspace-write",
  "model": null,
  "reasoning_effort": "high",
  "full_auto": false,
  "credential_blocked": false,
  "dirty_tree_blocked": false,
  "readable_secret_file_blocked": false,
  "commands_run_count": 3,
  "exit_code": 0,
  "termination_reason": "complete"
}
```

**`termination_reason` values:**

| Value | Meaning |
|-------|---------|
| `complete` | Codex ran and exited 0 |
| `error` | Codex ran with non-zero exit, or adapter failure post-gates |
| `blocked` | Pre-dispatch gate failed (credential, dirty tree, readable secret) |

**`dispatched` field:** `true` if Codex actually ran (steps 10+ executed), `false` if blocked or errored before dispatch. Separates "Codex ran" from "adapter handled an invocation."

**`exit_code`:** Nullable. Only present when `dispatched=true`. The subprocess exit code from `codex exec`.

**`thread_id`:** Nullable. Only present when `dispatched=true` and JSONL contained a `thread.started` event. Diagnostic only — not used as a resume token in Step 1.

**`consultation_id`:** Opaque event instance UUID. Preserved for compatibility as a universal event correlation key across `dialogue_outcome`, `consultation_outcome`, and `delegation_outcome`. Not a consultation-scoped key despite the name.

**`session_id` contract:** Nullable, never fabricated. Read from `CLAUDE_SESSION_ID` environment variable. Absent or whitespace-only → `null`. Mirrors `emit_analytics.py` behavior exactly.

**`token_usage` observability boundary:** The adapter output includes `token_usage` for the skill's benefit (Claude can report cost to the user). The analytics event intentionally omits it — consistent with `dialogue_outcome` and `consultation_outcome`, neither of which persists token usage.

**`schema_version` bump policy:** Hard-coded `"0.1.0"` for initial release. Bump to `"0.2.0"` when adding new required fields.

**Emission:** The adapter writes directly to `~/.claude/.codex-events.jsonl` via the shared `event_log.py` helper. No routing through `emit_analytics.py` — delegation events don't need synthesis parsing or convergence mapping. Events are emitted only if input JSON parsing (step 3) succeeds.

### 6. Event reader update (`read_events.py`)

Add `delegation_outcome` to `_REQUIRED_FIELDS` with schema validation:

```python
_REQUIRED_FIELDS = {
    "dialogue_outcome": [...existing...],
    "consultation_outcome": [...existing...],
    "delegation_outcome": [
        "schema_version",
        "event",
        "ts",
        "consultation_id",
        "session_id",
        "thread_id",
        "dispatched",
        "sandbox",
        "model",
        "reasoning_effort",
        "full_auto",
        "credential_blocked",
        "dirty_tree_blocked",
        "readable_secret_file_blocked",
        "commands_run_count",
        "exit_code",
        "termination_reason",
    ],
}
```

**Nullable fields:** `session_id`, `model`, `reasoning_effort`, `thread_id`, `exit_code` — present in event but may be `null`. Validation checks field presence, not value.

### 7. Stats update (`scripts/compute_stats.py`)

Add delegation support with a new section type and template.

**New `_DELEGATION_TEMPLATE`:**

```python
_DELEGATION_TEMPLATE = {
    "included": False,
    "sample_size": 0,
    "complete_count": 0,
    "error_count": 0,
    "blocked_count": 0,
    "credential_block_count": 0,
    "dirty_tree_block_count": 0,
    "readable_secret_file_block_count": 0,
    "sandbox_counts": {},            # {"workspace-write": N, "read-only": N}
    "full_auto_count": 0,
    "avg_commands_run": 0.0,
    "avg_commands_run_observed_count": 0,
}
```

**Section matrix:** Add `"delegation"` key mapping to `_compute_delegation` function. Add `--type delegation` support.

**Usage template:** Add `delegations_completed_total` field to `_USAGE_TEMPLATE`. Computed as count of `delegation_outcome` events where `dispatched=true`. No `posture_counts` contribution — delegation has no posture.

**`--json` no-op flag:** Add `--json` to `argparse` as a no-op flag (script always outputs JSON). Fixes pre-existing bug: `consultation-stats/SKILL.md` passes `--json` which currently causes an unrecognized argument error.

---

## Credential Scanning

The adapter imports `scan_text()` from the shared `credential_scan.py` module (strict + contextual tiers). This is the same credential detection that guards MCP-based consultation, applied to the delegation prompt before it reaches `codex exec`.

**Why not a Bash PreToolUse hook?** The existing hook infrastructure only matches the two Codex MCP tools. A Bash PreToolUse hook would fire on every Bash call — not just delegation. The adapter-level scan is more precise: it only runs when delegation is the intent.

Step 2 of the roadmap adds a Bash hook or adapter-level credential scan for users who run `codex exec` manually (outside the `/delegate` skill). That's a separate concern.

---

## Codex CLI Surface (verified against codex-cli 0.111.0)

**Minimum version:** `>= 0.111.0`. The adapter checks `codex --version` on every invocation and fails closed if the version is below the floor or unparseable.

### `codex exec` flags

| Flag | Supported | Notes |
|------|-----------|-------|
| `--json` | Yes | JSONL output with `thread.started`, `turn.*`, `item.*`, `error` events |
| `-o / --output-last-message` | Yes | Writes final assistant message to file |
| `-m / --model` | Yes | Model selection |
| `-s / --sandbox` | Yes | `read-only`, `workspace-write`, `danger-full-access` |
| `-c key=value` | Yes | Config overrides (adapter-synthesized `model_reasoning_effort` only) |
| `--full-auto` | Yes | Convenience alias: `-s workspace-write` + approval `on-request` |
| `--skip-git-repo-check` | Yes | **Not used** — adapter requires git repo |
| `-a / --ask-for-approval` | **No** | Not available in exec mode |

### JSONL event families (from official docs)

| Event type | Key fields | Adapter use |
|------------|-----------|-------------|
| `thread.started` | `thread_id` | Extract thread ID |
| `turn.started` | — | Ignored |
| `turn.completed` | `usage.input_tokens`, `usage.output_tokens` | Token usage (nullable) |
| `turn.failed` | Error details | Capture as runtime failure |
| `item.started` | `item.type`, `item.command` | Ignored |
| `item.completed` | `item.type`, `item.command`, `item.exit_code`, `item.text` | Commands run, messages |
| `error` | Error details | Capture for reporting |

---

## What This Spec Does NOT Cover

These are explicitly deferred to future steps:

| Step | Capability | Depends on |
|------|-----------|------------|
| 1b | Resume support (`codex exec resume`) | Step 1 deployed + identity-based resume design |
| 2 | Bash PreToolUse hook for manual `codex exec` calls | Step 1 deployed |
| 2 | Per-invocation secret-file allowlist configuration | Step 1 deployed + usage feedback |
| 3 | Dirty-tree gating with temp-worktree execution | Step 1 deployed |
| 4 | MCP server wrapping `codex exec` (typed delegation tools) | Other skills/agents needing typed calls |
| 5 | `codex-executor` agent (orchestrated multi-step delegation) | Stable transport contract from Steps 1-4 |

**Resume rationale (D20):** `codex exec resume --last` is CWD-scoped and heuristic — any manual `codex exec` from the repo root can cause the next resume to target the wrong session. Identity-based resume (using `thread_id` as an explicit token) requires verifying that the JSONL `thread_id` is a valid resumable session identifier, which is not documented for `codex-cli 0.111.0`. Deferred until verified.

---

## Decision Log

| # | Decision | Rationale | Source |
|---|----------|-----------|--------|
| D1 | Separate `/delegate` verb, not `--exec` on `/codex` | `/codex` is hardwired to consultation analytics; mixing paradigms muddies safety model | Design discussion |
| D2 | Adapter script, not raw Bash in skill | One deterministic boundary for flag parsing, credential scan, JSONL capture, analytics | User (hybrid proposal) |
| D3 | Clean-tree hard requirement (Step 1) | Warning-only defeats reliable diff attribution; worktree support deferred to Step 3 | Codex consultation 1 |
| D4 | `workspace-write` default sandbox | Delegation implies execution; `read-only` is explicit opt-in for analysis-only | Codex consultation 1 |
| D5 | Block `danger-full-access` in Step 1 | Defer until stronger controls exist; official docs label it elevated risk | Codex consultation 1 |
| D6 | `--full-auto` requires explicit user flag | Never auto-enable, never offer implicitly; `--full-auto` + `-s read-only` is a deterministic error | Codex consultation 1 |
| D7 | Drop `--skip-git-repo-check` | Adapter requires git repo for clean-tree gate and diff review; Codex's own repo guard is additive | Codex consultation 2 |
| D8 | `thread_id` canonical, no `session_id` from JSONL | Docs document `thread_id` in JSONL; no documented `session_id` in event stream | Codex consultation 2 |
| D9 | `files_changed` from `git status --short`, not JSONL | JSONL shows commands, not authoritative file state; `git status --short` also catches new untracked files | Codex consultation 2 |
| D10 | `delegation_outcome` in `_REQUIRED_FIELDS` with schema validation | Prevents false validation on `--validate` and catches malformed events early | Codex consultations 2+3 |
| D11 | Shared `event_log.py` module (analytics-emitter scope) | Prevents duplication between adapter and emitter; `codex_guard.py` stays untouched | Codex consultation 2 + adversarial review |
| D12 | `summary` and `token_usage` nullable in adapter output | Docs guarantee JSONL event families, not that every run produces a final message or completed turn | Codex consultation 2 |
| D13 | Exit 0 for blocked status | Non-zero would trigger PostToolUseFailure Bash hook, causing unintended nudge behavior | Codex deep review |
| D14 | Separate safety/trust model from consultation contract | Delegation has narrower trust: sandbox is primary, prompt scan is defense-in-depth | Codex deep review |
| D15 | Pre-step for repo root resolution + secure temp allocation | Pipeline assumed CWD is repo root; explicit resolution prevents path mismatches | Codex deep review |
| D16 | Tolerant JSONL parsing (skip malformed, degrade on missing fields) | Matches `read_events.py:read_all()` tolerance model; forward-compatible | Codex deep review |
| D17 | Deterministic failure handling for all 14 pipeline steps | Each step has defined status/exit/message pattern; no silent failures | Codex deep review + adversarial review |
| D18 | Temp file cleanup in finally block (best-effort, not SIGKILL-proof) | Matches `emit_analytics.py` cleanup pattern; SIGKILL bypass is accepted local risk | Codex deep review + adversarial review |
| D19 | Readable-secret-file gate with pathspec matching | Best-effort protection against common `.gitignore`'d secret files; not a guarantee | Adversarial review (P0-2) |
| D20 | Defer resume from Step 1 | `--last` is heuristic and prone to same-repo hijack; identity-based resume unverified | Adversarial review (P1-2) + collaborative ideation |
| D21 | Split validation: Phase A / credential scan / Phase B | Credential scan must run before any user content is echoed in error messages | Adversarial review (P0-3) |
| D22 | Per-invocation CLI version check (>= 0.111.0) | No version pinning means undefined behavior on older CLIs; fail closed on mismatch | Adversarial review (P1-3) |
| D23 | Shared `credential_scan.py` with `ScanResult` + `scan_text` API | Patterns are private names in `codex_guard.py`; adapter needs public import contract | Adversarial review + collaborative ideation |
| D24 | `dispatched:bool` in analytics + coarse `termination_reason` | Separates "Codex ran" from "adapter handled"; no Codex exit-code taxonomy exists for finer mapping | Adversarial review (P1-1) + collaborative ideation |
| D25 | `-c` restricted to adapter-synthesized `model_reasoning_effort` only | Arbitrary `-c` is an unspecified security surface; single override is deterministic | Adversarial review + collaborative ideation |
| D26 | `event_log.py` does NOT migrate `codex_guard.py` | Guard's `session_id="unknown"` and microsecond timestamps are existing behavior; changing them has no benefit and breaks downstream queries | Adversarial review |
| D27 | `compute_stats.py` delegation section with `_DELEGATION_TEMPLATE` | One-sentence deliverable was not implementable; full template prevents undocumented decisions | Collaborative ideation |
| D28 | `--json` no-op flag in `compute_stats.py` | Pre-existing bug: `consultation-stats/SKILL.md` passes `--json` which errors | Adversarial review |
| D29 | `consultation_id` is an opaque event instance UUID | Name preserved for compatibility; prose clarifies it is not consultation-scoped | Adversarial review + collaborative ideation |
| D30 | No user content echoed before credential scan (governance rule 6) | Error messages before scan could leak credentials via `Got: {value!r}` patterns | Adversarial review (P0-3) |

---

## File Manifest

| File | Action | Purpose |
|------|--------|---------|
| `scripts/event_log.py` | Create | Shared event log helper (analytics-emitter scope) |
| `scripts/credential_scan.py` | Create | Public credential scan API (extracted from codex_guard.py) |
| `scripts/codex_delegate.py` | Create | Delegation adapter (14-step pipeline) |
| `skills/delegate/SKILL.md` | Create | `/delegate` skill |
| `scripts/codex_guard.py` | Edit | Import `scan_text` from `credential_scan.py` |
| `scripts/emit_analytics.py` | Edit | Import from `event_log.py` |
| `scripts/read_events.py` | Edit | Add `delegation_outcome` to `_REQUIRED_FIELDS` |
| `scripts/compute_stats.py` | Edit | Add delegation section, `_DELEGATION_TEMPLATE`, `--json` no-op |

All paths relative to `packages/plugins/cross-model/`.
