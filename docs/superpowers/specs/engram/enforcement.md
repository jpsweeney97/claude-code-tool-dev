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
| `engram_guard` | PreToolUse (Write, Edit, Bash) | 1st | [Protected-path enforcement](#protected-path-enforcement) + [trust injection](#trust-injection) | **Block** |
| `engram_quality` | PostToolUse (Write, Edit) | 2nd | [Snapshot quality checks](#quality-validation) | **Warn** |
| `engram_register` | PostToolUse (Write, Edit) | 3rd | Ledger append ([hook-class events](types.md#producer-classes)) | **Silent** (best-effort) |
| `engram_session` | SessionStart | — | [TTL cleanup, worktree_id init](#sessionstart-hook) | See below |

### Ledger Multi-Producer Note

`engram_register` fires on Write and Edit tool calls to protected paths. It does **not** observe engine Bash invocations (`python3 engine_*.py`). Engine-authored ledger events ([`defer_completed`](types.md#event-vocabulary-v1), [`distill_completed`](types.md#event-vocabulary-v1)) are appended by engines post-commit, not by hooks. This separation means:
- Hook events and engine events have distinct observation scopes — no dedup concern between producer classes
- The "ledger-backed" timeline label applies only to engine/orchestrator events, not hook events
- All producers use the shared locked append primitive defined in [types.md](types.md#write-semantics)

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

This is advisory quality lint, not trust enforcement — the small race between write completion and validation readback is acceptable for warnings. See [enforcement boundary constraint](#enforcement-boundary-constraint) for the governing principle and [pre/post-write validation layering](foundations.md#prepost-write-validation-layering) for design rationale. It does **not** detect Bash-mediated writes to protected paths.

### Quality Validation Scope

| Path Class | Paths | Checks |
|---|---|---|
| `snapshot` | `~/.claude/engram/<repo_id>/snapshots/**` | Frontmatter completeness, section count |
| `checkpoint` | `~/.claude/engram/<repo_id>/checkpoints/**` | Frontmatter completeness |

Quality validation paths are separate from [protected-path enforcement](#protected-path-enforcement). Protected paths gate *authorization* (who may write). Quality paths gate *content checks* (what was written). A path can be in both sets.

### Enforcement Boundary Constraint

PostToolUse hooks **must not** become enforcement boundaries. The race between write completion and validation readback is acceptable for warnings, not for trust authorization. This is why `engram_quality` uses **Warn** (not Block) as its failure mode.

This constraint applies to all current and future PostToolUse hooks in the Engram system.

## Trust Injection

`engram_guard` injects a trust triple into the engine payload for every authorized Bash invocation of a subsystem engine. Three-step mechanism:

### Step 1: Injection (PreToolUse)

When `engram_guard` detects an authorized engine invocation pattern (`python3 engine_*.py`), it writes `hook_injected=True`, `hook_request_origin`, and `session_id` to the engine's payload file atomically (temp file -> `fsync` -> `os.replace`). Carries forward the ticket plugin's proven trust injection pattern.

### Step 2: Validation (Engine Entrypoint)

Every **mutating** entrypoint in each subsystem engine must invoke a shared trust validator (`collect_trust_triple_errors()`) before making state changes. This gates all [cross-subsystem operations](operations.md#core-rules) that flow through engine entrypoints. The validator checks that all three fields are present and non-empty. Missing or incomplete triples reject the operation. Read-only entrypoints are exempt.

**Mutating entrypoints** are any engine functions that create, update, or delete files in protected paths. At minimum: ticket creation/update, knowledge publish, staging write, snapshot write. Read-only queries and index scans are exempt. Each subsystem engine documents its mutating entrypoints in its module docstring.

### Step 3: Per-Subsystem Enforcement

Each subsystem engine owns its trust boundary. The shared validator lives in `engram_core/` but enforcement is at the engine level — Engram's indexing layer never sees or checks trust triples.

### Trust Triple Scope

The trust triple is `{hook_injected, hook_request_origin, session_id}` — three fields, by design. `worktree_id` is **not** part of the trust triple. Engines derive `worktree_id` independently via `git rev-parse --git-dir` (see [identity resolution](types.md#identity-resolution)) and populate it in `RecordMeta`. This separation ensures that trust validation (was this request authorized?) and provenance tracking (which worktree originated this?) are independently verifiable.

### Inter-Hook Runtime State

`engram_session` (SessionStart) resolves `worktree_id` and `session_id` at session start. `engram_guard` (PreToolUse) requires these values for trust injection.

**Preferred approach:** `engram_guard` recomputes `worktree_id` independently via the same `git rev-parse --git-dir` derivation. `session_id` is available from the Claude Code session context. No shared state file or environment variable is required.

**If shared state is unavoidable:** The producing hook (`engram_session`) writes; the consuming hook (`engram_guard`) reads. Define: (1) storage mechanism (env var, temp file), (2) data format, (3) lifetime (session-scoped), (4) failure behavior (guard blocks all mutations if state is missing — fail-closed).

## SessionStart Hook

`engram_session`: bounded and idempotent. <500ms startup budget.

| Operation | Budget | On Failure |
|---|---|---|
| Resolve `worktree_id` | 1 call | Fail-closed: session needs identity |
| Clean expired snapshots (>90d by filename timestamp) | Max 50 files | Fail-open: retry next session |
| Clean expired chain state (>24h) | Max 20 files | Fail-open |
| Verify `.engram-id` exists | 1 read | Warn if missing (diagnostic only — does not create) |

### Bootstrap Relationship

SessionStart does not create `.engram-id` — it requires a git commit, which is inappropriate during session initialization. Bootstrap occurs via `engram init` (see [skills table](skill-surface.md#skills-13-total)). Until `.engram-id` exists, all mutating Engram operations (save, defer, distill, ticket create) fail closed with error: `"Engram not initialized: run 'engram init' to bootstrap."` Read-only operations (search, triage) degrade gracefully via the [degradation model](storage-and-indexing.md#degradation-model).

## Enforcement Exceptions

| Exception | Scope | Rationale |
|---|---|---|
| `/promote` Step 2 CLAUDE.md write | Single skill, single target | CLAUDE.md is an external sink, not an Engram-managed record. The Knowledge engine owns promotion *state* via [promote-meta](types.md#promote-meta-promotion-state-record). See [permitted exceptions](foundations.md#permitted-exceptions). |

No other skill-level write to a protected or externally-owned path is sanctioned. New exceptions require an entry in both this table and foundations.md.

## Autonomy Model

| Subsystem | Model | Rationale |
|---|---|---|
| Work | `suggest` / `auto_audit` | Trust boundary: agents propose, users approve |
| Context | None | Agents save their own session state |
| Knowledge staging | Staging inbox cap + idempotency | Dedup prevents repeated staging; cumulative cap limits volume |

**Mode definitions:**
- **`suggest`:** Engine prepares the operation but surfaces it to the user for confirmation before writing. The user sees what will be created and approves or rejects.
- **`auto_audit`:** Engine creates the work item automatically. The item is marked for user review at next `/triage`. `work_max_creates` limits cumulative automatic creations per session. Trust injection still applies — `engram_guard` validates the trust triple regardless of mode.

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
