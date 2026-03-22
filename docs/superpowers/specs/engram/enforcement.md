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

`engram_register` fires on Write and Edit tool calls to protected paths. It does **not** observe engine Bash invocations (`python3 engine_*.py`). Staging writes (`knowledge_staging/`) are engine-initiated and not observable by this hook — staging events, if needed for the ledger, must be emitted by the engine as producer-class events. Engine-authored ledger events ([`defer_completed`](types.md#event-vocabulary-v1), [`distill_completed`](types.md#event-vocabulary-v1)) are appended by engines post-commit, not by hooks. This separation means:
- Hook events and engine events have distinct observation scopes — no dedup concern between producer classes
- The "ledger-backed" timeline label applies only to engine/orchestrator events, not hook events
- All producers use the shared locked append primitive defined in [types.md](types.md#write-semantics)
- Step 3 promote-meta failures are only detectable via `/triage` (engine Bash writes are not observable by `engram_register`)

**`engram_register` failure modes:** (1) Lock timeout → log warning, do not block. (2) Permission denied → log error, do not block. (3) Disk full → log error, do not block. All failures are written to the session diagnostic channel. `/triage` surfaces "ledger unavailable in session X" (rather than "completion not proven") when the ledger producer has recorded failures in the diagnostic channel.

## Protected-Path Enforcement

Policy-based, not tool-specific. Protects subsystem-owned paths from direct mutation regardless of which tool is used.

| Path Class | Protected Paths | Allowed Mutators |
|---|---|---|
| `work` | `engram/work/**` | Engine entrypoints only |
| `knowledge_published` | `engram/knowledge/**` | Engine entrypoints only |
| `knowledge_staging` | `~/.claude/engram/<repo_id>/knowledge_staging/**` | Engine entrypoints only |

Paths canonicalized before matching (resolve symlinks, collapse `..`, normalize to absolute).

**Intentional exclusions:** Snapshot and checkpoint paths (`~/.claude/engram/<repo_id>/snapshots/**`, `checkpoints/**`) are not in this table. Context subsystem writes use Write/Edit tools natively (session orchestration) rather than routing through engine Bash invocations, so PreToolUse path blocking would prevent normal operation. Advisory quality checks via [`engram_quality`](#quality-validation) cover these paths instead.

**Reserved paths:** When content is added to `engram/.engram/` (reserved for future shared metadata), a corresponding path class entry must be added to this table before implementation.

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

Quality validation paths are separate from [protected-path enforcement](#protected-path-enforcement). Protected paths gate *authorization* (who may write). Quality paths gate *content checks* (what was written). A path can be in both sets. Staging writes (`knowledge_staging/`) are excluded — the Knowledge engine validates content at write time, making post-write quality hooks redundant for staging.

**Hook self-failure:** If `engram_quality` itself fails (unhandled exception, timeout), the failure is logged as `[engram_quality:error]` (distinct from quality warnings at `[engram_quality:warn]`) but does not block the underlying write. The implementation must catch all exceptions in the hook body to prevent hook-level failures from propagating to the tool call result.

### Enforcement Boundary Constraint

PostToolUse hooks **must not** become enforcement boundaries. The race between write completion and validation readback is acceptable for warnings, not for trust authorization. This is why `engram_quality` uses **Warn** (not Block) as its failure mode.

This constraint applies to all current and future PostToolUse hooks in the Engram system.

## Trust Injection

`engram_guard` injects a trust triple into the engine payload for every authorized Bash invocation of a subsystem engine. Three-step mechanism:

### Step 1: Injection (PreToolUse)

When `engram_guard` detects an authorized engine invocation, it writes `hook_injected=True`, `hook_request_origin`, and `session_id` to the engine's payload file atomically (temp file -> `fsync` -> `os.replace`). Carries forward the ticket plugin's proven trust injection pattern.

**Authorized engine invocation pattern:** Engine binaries must be named `engine_<subsystem>.py` and reside in the plugin's scripts directory. `engram_guard` matches the **full path** `<engram_scripts_dir>/engine_*.py` — not just the filename. This prevents false matches on user scripts with `engine_` prefixes outside the plugin directory.

**Detection failure mode:** If the full-path pattern fails to match a legitimate engine invocation, the trust triple is not injected. The engine then rejects via `collect_trust_triple_errors()` (correct behavior — fail-closed). The diagnostic should indicate `"engine invocation not recognized by engram_guard — verify script path matches <engram_scripts_dir>/engine_<subsystem>.py"`.

### Step 2: Validation (Engine Entrypoint)

Every **mutating** entrypoint in each subsystem engine must invoke a shared trust validator (`collect_trust_triple_errors()`) before making state changes. This gates all [cross-subsystem operations](operations.md#core-rules) that flow through engine entrypoints. The validator checks: (1) `hook_injected` is present **and equals `True`** (not just non-empty — `False` must be rejected), (2) `hook_request_origin` is present and is a non-empty string, (3) `session_id` is present and is a non-empty string. Missing, incomplete, or invalid triples reject the operation with a structured error. Read-only entrypoints are exempt.

**Mutating entrypoints** are any engine functions that create, update, or delete files in protected paths. Complete enumeration per subsystem:
- **Work:** ticket creation, ticket update, ticket close
- **Knowledge:** knowledge publish (both `/learn` direct-publish and `/curate` staged-publish paths), staging write, promote-meta write
- **Context:** snapshot write, checkpoint write

All writes from `/learn` route through the Knowledge engine entrypoint — `/learn` does **not** write directly to `learnings.md` via the Write tool. This ensures trust injection covers the `/learn` path.

Read-only queries and index scans are exempt. Each subsystem engine documents its mutating entrypoints in its module docstring. delivery.md Step 3a must include a verification step asserting `collect_trust_triple_errors()` is invoked at every documented mutating entrypoint (unit test or static analysis check).

### Step 3: Per-Subsystem Enforcement

Each subsystem engine owns its trust boundary. The shared validator lives in `engram_core/` but enforcement is at the engine level — Engram's indexing layer never sees or checks trust triples.

### Trust Triple Scope

The trust triple is `{hook_injected, hook_request_origin, session_id}` — three fields, by design. `worktree_id` is **not** part of the trust triple. Engines derive `worktree_id` independently via `git rev-parse --git-dir` (see [identity resolution](types.md#identity-resolution)) and populate it in `RecordMeta`. This separation ensures that trust validation (was this request authorized?) and provenance tracking (which worktree originated this?) are independently verifiable.

### Inter-Hook Runtime State

`engram_session` (SessionStart) resolves `worktree_id` and `session_id` at session start. `engram_guard` (PreToolUse) requires these values for trust injection.

`engram_guard` MUST recompute `worktree_id` independently via `identity.get_worktree_id()` (same `git rev-parse --git-dir` derivation). `session_id` MUST be obtained from the Claude Code session context. No shared state file or environment variable is required or permitted.

**Future platform fallback:** The shared-state approach (producing hook writes, consuming hook reads) applies only if Claude Code session context becomes unavailable in a future platform change. Until then, recomputation is the sole supported approach. If recomputation fails (e.g., `git rev-parse --git-dir` returns an error), block fail-closed and surface the specific git error.

### Bridge Period Limitations

During Steps 1–3 of the [build sequence](delivery.md), envelope-level idempotency keys are not checked — the old ticket engine's legacy dedup is the active mechanism. Full envelope idempotency enforcement begins at Step 4. See [operations.md §Phase-Scoped Idempotency](operations.md#envelope-invariants) for the operational specification of this temporary limitation.

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

No other skill-level write to a protected or externally-owned path is sanctioned. New exceptions require an entry in both this table and foundations.md. **Sequencing:** foundations.md is the authoritative source for new exceptions — a new exception is effective only when present in foundations.md. This table then references it.

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
                                    # Disabling degrades /triage inference —
                                    # see storage-and-indexing.md degradation model.
```

### Staging Inbox Cap

The staging inbox cap is configured via `knowledge_max_stages` in `.claude/engram.local.md`. Values less than 1 are invalid; the engine rejects the configuration at parse time with `"knowledge_max_stages must be >= 1"`.

The cap enforces whole-batch rejection for determinism. See [operations.md §Distill](operations.md#distill-context-to-knowledge-staged) for the behavioral specification (rejection logic, formula, error message format, edge cases, and recovery path).
