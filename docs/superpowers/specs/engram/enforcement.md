---
module: enforcement
status: active
normative: true
authority: enforcement
---

# Enforcement

## Hooks

| Hook | Event | Order | Purpose | On Failure |
|---|---|---|---|---|
| `engram_guard` | PreToolUse | 1st | [Protected-path enforcement](#protected-path-enforcement) + [trust injection](#trust-injection) | **Block** |
| `engram_quality` | PostToolUse (Write, Edit) | 2nd | [Snapshot quality checks](#quality-validation) | **Warn** |
| `engram_register` | PostToolUse (Write) | 3rd | Ledger append | **Silent** (best-effort) |
| `engram_session` | SessionStart | — | [TTL cleanup, worktree_id init](#sessionstart-hook) | See below |

## Protected-Path Enforcement

Policy-based, not tool-specific. Protects subsystem-owned paths from direct mutation regardless of which tool is used.

| Path Class | Protected Paths | Allowed Mutators |
|---|---|---|
| `work` | `engram/work/**` | Engine entrypoints only |
| `knowledge_published` | `engram/knowledge/**` | Engine entrypoints only |
| `knowledge_staging` | `~/.claude/engram/<repo_id>/knowledge_staging/**` | Engine entrypoints only |

Paths canonicalized before matching (resolve symlinks, collapse `..`, normalize to absolute).

### Enforcement Scope (Bounded Guarantee)

Write and Edit mutations to protected paths are reliably blocked. Authorized engine Bash invocations (`python3 engine_*.py` patterns) are detected and supported with trust injection. Arbitrary Bash writes (`echo >`, `cp`, `tee`, etc.) are caught on a best-effort basis only — PreToolUse input parsing cannot reliably detect all shell write patterns.

This is an honest boundary, not a gap to close: the design provides reliable enforcement for the tools Claude uses natively (Write, Edit) and for the authorized engine invocation pattern, but does not claim to prevent all possible filesystem mutations. See [Bash enforcement gap](decisions.md#named-risks) for severity assessment and [drift scan](decisions.md#deferred-decisions) for the deferred detection strategy.

## Quality Validation

`engram_quality` (PostToolUse) validates snapshot content quality for Write and Edit tool calls on snapshot-owned paths.

- **Write:** reads `tool_input.content` from the payload
- **Edit:** reads the file from disk after the edit completes (post-state validation)

This is advisory quality lint, not trust enforcement — the small race between write completion and validation readback is acceptable for warnings. Follows the [pre/post-write validation layering](foundations.md#prepost-write-validation-layering) principle. It does **not** detect Bash-mediated writes to protected paths.

## Trust Injection

`engram_guard` injects a trust triple into the engine payload for every authorized Bash invocation of a subsystem engine. Three-step mechanism:

### Step 1: Injection (PreToolUse)

When `engram_guard` detects an authorized engine invocation pattern (`python3 engine_*.py`), it writes `hook_injected=True`, `hook_request_origin`, and `session_id` to the engine's payload file atomically (temp file -> `fsync` -> `os.replace`). Carries forward the ticket plugin's proven trust injection pattern.

### Step 2: Validation (Engine Entrypoint)

Every **mutating** entrypoint in each subsystem engine must invoke a shared trust validator (`collect_trust_triple_errors()`) before making state changes. This gates all [cross-subsystem operations](operations.md#core-rules) that flow through engine entrypoints. The validator checks that all three fields are present and non-empty. Missing or incomplete triples reject the operation. Read-only entrypoints are exempt.

### Step 3: Per-Subsystem Enforcement

Each subsystem engine owns its trust boundary. The shared validator lives in `engram_core/` but enforcement is at the engine level — Engram's indexing layer never sees or checks trust triples.

## SessionStart Hook

`engram_session`: bounded and idempotent. <500ms startup budget.

| Operation | Budget | On Failure |
|---|---|---|
| Resolve `worktree_id` | 1 call | Fail-closed: session needs identity |
| Clean expired snapshots (>90d by filename timestamp) | Max 50 files | Fail-open: retry next session |
| Clean expired chain state (>24h) | Max 20 files | Fail-open |
| Clean `.failed/` envelopes (>7d) | Max 20 files | Fail-open |
| Verify `.engram-id` exists | 1 read | Warn if missing (diagnostic only — does not create) |

### Bootstrap Relationship

SessionStart does not create `.engram-id` — it requires a git commit, which is inappropriate during session initialization. Bootstrap occurs via `engram init` (see [skills table](skill-surface.md#skills-13-total)). Until `.engram-id` exists, all mutating Engram operations (save, defer, distill, ticket create) fail closed with error: `"Engram not initialized: run 'engram init' to bootstrap."` Read-only operations (search, triage) degrade gracefully via the [degradation model](storage-and-indexing.md#degradation-model).

## Autonomy Model

| Subsystem | Model | Rationale |
|---|---|---|
| Work | `suggest` / `auto_audit` | Trust boundary: agents propose, users approve |
| Context | None | Agents save their own session state |
| Knowledge staging | Staging inbox cap + idempotency | Dedup prevents repeated staging; cumulative cap limits volume |

### Configuration

`.claude/engram.local.md` (YAML frontmatter in markdown, parsed by `engram_core` using the same fenced-YAML extraction as the ticket plugin):

```yaml
autonomy:
  work_mode: suggest          # suggest | auto_audit
  work_max_creates: 5
  knowledge_max_stages: 10    # Cumulative files in staging inbox, not per-session
ledger:
  enabled: true               # Default on. Opt-out here.
```

### Staging Inbox Cap

The Knowledge engine checks the cumulative count of files in `knowledge_staging/` **before** writing new staged candidates. If `count + batch_size > knowledge_max_stages`, the entire batch is rejected (whole-batch reject for determinism — no partial staging). The rejection response includes current count, cap, and a suggestion to run `/curate` to clear the inbox.

Scope is cumulative (total files in directory), not per-session. This matches the stated risk ([staging accumulation](decisions.md#named-risks)), not per-session agent autonomy. The engine reads `knowledge_max_stages` from `.claude/engram.local.md` at invocation time — no caching.
