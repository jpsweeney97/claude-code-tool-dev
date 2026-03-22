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
| `engram_guard` | PreToolUse (Write, Edit, Bash) | 1st | [Engine trust injection + direct-write path authorization](#trust-injection) | **Block** |
| `engram_quality` | PostToolUse (Write, Edit) | 2nd | [Snapshot quality checks](#quality-validation) | **Warn** |
| `engram_register` | PostToolUse (Write, Edit) on protected paths | 3rd | Ledger append ([hook-class events](types.md#producer-classes)) | **Silent** (best-effort) |
| `engram_session` | SessionStart | — | [TTL cleanup, worktree_id init](#sessionstart-hook) | See below |

### Ledger Multi-Producer Note

`engram_register` fires on Write and Edit tool calls to protected paths. It does **not** observe engine Bash invocations (`python3 engine_*.py`). Staging writes (`knowledge_staging/`) are engine-initiated and not observable by this hook — staging events, if needed for the ledger, must be emitted by the engine as producer-class events. Engine-authored ledger events ([`defer_completed`](types.md#event-vocabulary-v1), [`distill_completed`](types.md#event-vocabulary-v1)) are appended by engines post-commit, not by hooks. This separation means:
- Hook events and engine events have distinct observation scopes — no dedup concern between producer classes
- The "ledger-backed" timeline label applies only to engine/orchestrator events, not hook events
- All producers use the shared locked append primitive defined in [types.md](types.md#write-semantics)
- Step 3 promote-meta failures are only detectable via `/triage` (engine Bash writes are not observable by `engram_register`)

**`engram_register` failure modes:** (1) Lock timeout → log warning, do not block. (2) Permission denied → log error, do not block. (3) Disk full → log error, do not block. All failures are written to the [session diagnostic channel](#session-diagnostic-channel). See that section for the `/triage` read protocol.

### Session Diagnostic Channel

Hook failures are written to a per-session diagnostic file at `~/.claude/engram/<repo_id>/ledger/<worktree_id>/<session_id>.diag`. Format: one JSON object per line (same JSONL as ledger shards).

```json
{"ts": "<ISO 8601 UTC>", "hook": "engram_register", "failure_type": "lock_timeout", "message": "..."}
```

**Write semantics:** Append-only, best-effort (diagnostic writes must not fail-closed). No lock required — single producer (the hook that failed).

**Read protocol:** `/triage` checks for `<session_id>.diag` files. If present and non-empty, surfaces `"ledger unavailable in session <session_id>"` instead of `"completion not proven"` for that session's operations. See [/triage inference matrix](operations.md#triage-read-work-and-context).

**TTL:** Same as ledger shards — append-only, no TTL. Cleaned up if parent session directory is removed.

## Protected-Path Enforcement

Policy-based enforcement covering all currently supported write tools (Write, Edit, Bash). Adding new write-capable platform tools requires updating `engram_guard` hook registration.

| Path Class | Protected Paths | Allowed Mutators |
|---|---|---|
| `work` | `engram/work/**` | Engine entrypoints only |
| `knowledge_published` | `engram/knowledge/**` | Engine entrypoints only |
| `knowledge_staging` | `~/.claude/engram/<repo_id>/knowledge_staging/**` | Engine entrypoints only |

Paths canonicalized before matching (resolve symlinks, collapse `..`, normalize to absolute).

**Intentional exclusions:** Snapshot and checkpoint paths (`~/.claude/engram/<repo_id>/snapshots/**`, `checkpoints/**`) are not in this table. Context subsystem writes use Write/Edit tools natively — excluded from both protected-path enforcement and [trust triple validation](#step-2-validation-engine-entrypoint). See [direct-write path authorization](#direct-write-path-authorization) for the enforcement model. Advisory quality checks via [`engram_quality`](#quality-validation) cover content quality.

**Reserved paths:** When content is added to `engram/.engram/` (reserved for future shared metadata), a corresponding path class entry must be added to this table before implementation.

### Enforcement Scope (Bounded Guarantee)

Write and Edit mutations to protected paths are reliably blocked. Authorized engine Bash invocations (`python3 engine_*.py` patterns) are detected and supported with trust injection. Arbitrary Bash writes (`echo >`, `cp`, `tee`, etc.) are caught on a best-effort basis only — PreToolUse input parsing cannot reliably detect all shell write patterns.

This is an honest boundary, not a gap to close: the design provides reliable enforcement for the tools Claude uses natively (Write, Edit) and for the authorized engine invocation pattern, but does not claim to prevent all possible filesystem mutations. See [Bash enforcement gap](decisions.md#named-risks) for severity assessment and [drift scan](decisions.md#deferred-decisions) for the deferred detection strategy.

## Quality Validation

`engram_quality` (PostToolUse) validates snapshot content quality for Write and Edit tool calls on snapshot-owned paths.

- **Write:** reads `tool_input.content` from the payload
- **Edit:** reads the file from disk after the edit completes (post-state validation). If the file is missing at readback time (deleted between edit completion and hook execution), emit a warning (`snapshot file not found at post-write readback — quality check skipped`) and return exit code 0. Do not treat as a hook failure.

This is advisory quality lint, not trust enforcement — the small race between write completion and validation readback is acceptable for warnings. See [enforcement boundary constraint](#enforcement-boundary-constraint) for the governing principle and [pre/post-write validation layering](foundations.md#prepost-write-validation-layering) for design rationale. It does **not** detect Bash-mediated writes to protected paths.

### Quality Validation Scope

| Path Class | Paths | Checks |
|---|---|---|
| `snapshot` | `~/.claude/engram/<repo_id>/snapshots/**` | Frontmatter completeness, section count |
| `checkpoint` | `~/.claude/engram/<repo_id>/checkpoints/**` | Frontmatter completeness |

Quality validation paths are separate from [protected-path enforcement](#protected-path-enforcement). Protected paths gate *authorization* (who may write). Quality paths gate *content checks* (what was written). A path can be in both sets. Staging writes (`knowledge_staging/`) are excluded — the Knowledge engine validates content at write time, making post-write quality hooks redundant for staging.

**Hook self-failure:** If `engram_quality` itself fails (unhandled exception, timeout), the failure is logged as `[engram_quality:error]` (distinct from quality warnings at `[engram_quality:warn]`) but does not block the underlying write. The implementation must catch all exceptions in the hook body to prevent hook-level failures from propagating to the tool call result.

Implementation must never return exit code 2 (Block). Even if the quality check detects a severe issue, the response must be exit code 0 with warning text. This is enforced by the [enforcement boundary constraint](#enforcement-boundary-constraint).

### Enforcement Boundary Constraint

See [foundations.md §Enforcement Boundary Constraint](foundations.md#enforcement-boundary-constraint) for the governing architecture rule (authoritative). `engram_quality` uses **Warn** (not Block) as its failure mode in compliance with this constraint.

## Trust Injection

Two enforcement mechanisms share a single `engram_guard` hook, distinguished by `tool_name`:

| Mechanism | Transport | Applies To | How |
|-----------|-----------|------------|-----|
| **Engine trust injection** | Bash (`python3 engine_*.py`) | Work, Knowledge | Payload file with trust triple → engine validates via `collect_trust_triple_errors()` |
| **Direct-write path authorization** | Write, Edit | Context | Path ownership check → embedded provenance in content → post-write quality validation |

**Governing principle:** Uniformity of policy (every mutation is authorized), not uniformity of transport.

**Guard capability rollout:** Each build step lists the `engram_guard` capabilities it requires. No subsystem may activate a mutating route before the guard capabilities required for that route are active.

| Capability | Ships At | Covers |
|-----------|----------|--------|
| `engine_trust_injection` | Step 2a | Knowledge engine mutating entrypoints (Bash-mediated) |
| `engine_trust_injection` (extended) | Step 3a | Work engine mutating entrypoints |
| `work_path_enforcement` | Step 3a | Protected-path block for Write/Edit to Work and Knowledge paths |
| `context_direct_write_authorization` | Step 4a | Direct-write path authorization for Context snapshot/checkpoint paths |

### Guard Decision Algorithm

`engram_guard` evaluates incoming tool calls in this order. Branches are evaluated sequentially; the first match determines the action.

```
engram_guard decision algorithm:
  1. If tool_name == Bash AND matches engine_*.py pattern:
     → Engine trust injection (write TrustPayload, allow)
  2. If tool_name in {Write, Edit} AND path within Context private root:
     → Direct-write path authorization (allow + post-write quality)
  3. If tool_name in {Write, Edit} AND path in protected-path table:
     → Block with path-class diagnostic
  4. Otherwise:
     → Allow unconditionally (engram_guard does not restrict general writes)
Branches evaluated in this order. Step 2 failing (not Context-owned) routes to step 3.
```

**Capability gating:** Each branch is only active when its corresponding guard capability has shipped. Branch 1 activates at Step 2a (`engine_trust_injection`). Branch 3 activates at Step 3a (`work_path_enforcement`). Branch 2 activates at Step 4a (`context_direct_write_authorization`). Before a capability ships, its branch is a no-op (falls through to branch 4).

### Payload File Contract

The engine trust injection mechanism uses a payload file as the communication channel between `engram_guard` (PreToolUse hook) and subsystem engines.

| Property | Value |
|----------|-------|
| **Directory** | `.claude/engram-tmp/` (workspace-local, created on first use) |
| **Naming** | `<subsystem>-<operation>-<uuid>.json` (e.g., `work-defer-550e8400.json`) |
| **Schema** | `{"hook_injected": true, "hook_request_origin": "<origin>", "session_id": "<uuid>"}` |
| **Creator** | `engram_guard` creates the file atomically (temp file → `fsync` → `os.replace`) |
| **Consumer** | Subsystem engine reads the file, validates via `collect_trust_triple_errors()`, then deletes it |
| **Cleanup** | Engine deletes after consuming. `engram_session` prunes orphans older than 24h on startup. |
| **Containment** | `engram_guard` validates the payload file path is within the workspace `.claude/engram-tmp/` directory before writing |

**Containment failure mode:** If the containment check fails (payload path resolves outside `.claude/engram-tmp/`), `engram_guard` blocks the Bash tool call (exit code 2) with diagnostic: `"engram_guard: payload path outside containment boundary: {path}"`. This is a security-critical check and must fail-closed.

### Step 1: Injection (PreToolUse)

When `engram_guard` detects an authorized engine invocation, it writes the [TrustPayload](types.md#trustpayload--trust-triple-wire-format) to a new [payload file](#payload-file-contract) atomically. The file path is passed to the engine via the Bash command's argument list (matching the proven ticket plugin pattern).

**Atomic write failure mode:** If the atomic write fails (fsync error, disk full, permission denied), `engram_guard` blocks the Bash tool call (exit code 2) with diagnostic: `"engram_guard: payload write failed: {error}"`. Do not allow the engine invocation to proceed with a missing payload — the resulting trust triple rejection produces a misleading error.

**Authorized engine invocation pattern:** Engine binaries must be named `engine_<subsystem>.py` and reside in the plugin's scripts directory. `engram_guard` matches the **full path** `<engram_scripts_dir>/engine_*.py` — not just the filename. This prevents false matches on user scripts with `engine_` prefixes outside the plugin directory.

**Detection failure mode:** If the full-path pattern fails to match a legitimate engine invocation, the trust triple is not injected. The engine then rejects via `collect_trust_triple_errors()` (correct behavior — fail-closed). The diagnostic should indicate `"engine invocation not recognized by engram_guard — verify script path matches <engram_scripts_dir>/engine_<subsystem>.py"`.

### Step 2: Validation (Engine Entrypoint)

### collect_trust_triple_errors() Contract

```python
# engram_core/trust.py
def collect_trust_triple_errors(
    hook_injected: bool,
    hook_request_origin: str | None,
    session_id: str | None,
) -> list[str]:
    """Validate trust triple fields. Returns empty list on success, error strings on failure."""
```

**Parameter types — `str | None` is intentional:** The validator accepts `None` to provide specific error messages when a hook omits a required field. Callers constructing a well-formed `TrustPayload` always pass `str`. The `None` path catches structural errors in payload file parsing (missing JSON key → `None` after `.get()`).

**Validation rules (order matters):**
1. `hook_injected` must be `True` (identity check: `hook_injected is True`). `False`, `None`, or non-bool → error.
2. `hook_request_origin` must be a non-empty string in `{"user", "agent"}`. `None`, empty string, or unrecognized value → error.
3. `session_id` must be a non-empty string. `None` or empty string → error.

**Stable error strings:** `"hook_injected: must be True, got {value!r}"`, `"hook_request_origin: must be one of {{'user', 'agent'}}, got {value!r}"`, `"session_id: must be non-empty string, got {value!r}"`.

**Caller obligation:** If the returned list is non-empty, the engine must reject the operation with a structured error containing the error list and return without making state changes. The engine must not catch or suppress errors from this function.

**Origin-matching responsibility:** `collect_trust_triple_errors()` validates that the triple is well-formed. Whether the `hook_request_origin` matches the expected origin for a given entrypoint (e.g., `_user.py` expects `"user"`) is the entrypoint's responsibility — the validator does not enforce route-specific origin rules.

**Module location:** `engram_core/trust.py`. Add to [package structure](foundations.md#package-structure).

Every **mutating** entrypoint in Work and Knowledge subsystem engines must invoke [`collect_trust_triple_errors()`](#collect_trust_triple_errors-contract) before making state changes. Trust validation precedes all other processing, including idempotency key lookups and dedup reads — the trust triple is verified as the first operation in any engine entrypoint call. This gates all [cross-subsystem operations](operations.md#core-rules) that flow through engine entrypoints. See the function contract above for validation rules, error format, and caller obligation. Read-only entrypoints are exempt.

**Mutating entrypoints** are any engine functions that create, update, or delete files in protected paths. Complete enumeration per subsystem:
- **Work:** ticket creation, ticket update, ticket close
- **Knowledge:** knowledge publish (both `/learn` and `/curate` staged-publish paths), staging write, promote-meta write
- **Context:** See [direct-write path authorization](#direct-write-path-authorization) (Write/Edit path, not engine trust injection)

All writes from `/learn` route through the Knowledge engine entrypoint — `/learn` does **not** write directly to `learnings.md` via the Write tool. This ensures trust injection covers the `/learn` path.

Read-only queries and index scans are exempt. Each subsystem engine documents its mutating entrypoints in its module docstring. delivery.md Step 3a must include a verification step asserting `collect_trust_triple_errors()` is invoked at every documented Work and Knowledge mutating entrypoint (unit test or static analysis check). Context engine scripts must **not** invoke `collect_trust_triple_errors()` — this is verified by a separate negative test.

**Check ordering:** Each mutating entrypoint must check `.engram-id` existence before invoking `collect_trust_triple_errors()`. If `.engram-id` is absent, return the initialization error immediately without trust triple validation. This ensures users see "Engram not initialized" rather than a confusing trust triple rejection.

### Step 3: Per-Subsystem Enforcement

Each subsystem engine owns its trust boundary. The shared validator lives in `engram_core/` but enforcement is at the engine level — Engram's indexing layer never sees or checks trust triples.

### Direct-Write Path Authorization

Context subsystem writes (`/save`, `/quicksave`, `/load`) use the Write and Edit tools natively — they do not route through engine Bash invocations. When `engram_guard` detects a Write or Edit call to a Context-owned path (snapshots, checkpoints), it performs **path authorization** rather than engine trust injection:

1. **Path ownership check:** Verify the target path is within the Context subsystem's private root (`~/.claude/engram/<repo_id>/snapshots/**` or `checkpoints/**`). Paths outside these directories are not Context-owned.
2. **Allow the write.** Context paths are intentionally excluded from [protected-path enforcement](#protected-path-enforcement) (they are not engine-managed).
3. **Post-write quality validation** via [`engram_quality`](#quality-validation) checks content quality (frontmatter completeness, section count).
4. **Provenance is embedded** in the written content (frontmatter `session_id`, `worktree_id`, `orchestrated_by`), validated by `/triage` [anomaly detection](operations.md#triage-read-work-and-context).

This is explicitly **path authorization plus provenance/integrity validation**, not engine trust injection. The `collect_trust_triple_errors()` validator is not invoked for direct-write paths.

### Trust Triple Scope

The trust triple is `{hook_injected, hook_request_origin, session_id}` — three fields, by design. `worktree_id` is **not** part of the trust triple. Engines derive `worktree_id` independently via `git rev-parse --git-dir` (see [identity resolution](types.md#identity-resolution)) and populate it in `RecordMeta`. This separation ensures that trust validation (was this request authorized?) and provenance tracking (which worktree originated this?) are independently verifiable.

### Inter-Hook Runtime State

`engram_session` (SessionStart) resolves `worktree_id` and `session_id` at session start. `engram_guard` (PreToolUse) requires these values for trust injection.

`engram_guard` MUST obtain `worktree_id` by calling `identity.get_worktree_id()` at invocation time — same `git rev-parse --git-dir` derivation, but never from any cached session state. `session_id` MUST be obtained from the Claude Code session context. No shared state file or environment variable is required or permitted.

**Future platform fallback:** The shared-state approach (producing hook writes, consuming hook reads) applies only if Claude Code session context becomes unavailable in a future platform change. Until then, recomputation is the sole supported approach. If recomputation fails (e.g., `git rev-parse --git-dir` returns an error), block fail-closed and surface the specific git error.

### Bridge Period Limitations

Phase-scoped idempotency is a delivery-period limitation. See [delivery.md §Bridge Cutover](delivery.md#step-1-bridge-cutover) for the authoritative phase schedule and [operations.md §Phase-Scoped Idempotency](operations.md#envelope-invariants) for the operational specification.

`engram_guard` ships at Step 2a with the `engine_trust_injection` capability only — covering Knowledge engine mutating entrypoints. Step 3a extends the guard with `work_path_enforcement` for Work paths. Step 4a adds `context_direct_write_authorization` for Context direct-write paths. During Steps 0a–1, no guard capabilities are active — the bridge adapter routes through the old ticket engine's existing authorization model.

## SessionStart Hook

`engram_session`: bounded and idempotent. <500ms startup budget.

| Operation | Budget | On Failure |
|---|---|---|
| Resolve `worktree_id` | 1 call | Fail-closed: `engram_session` returns exit code 0 but stores error state. All subsequent Engram mutating operations fail-closed with: `"Engram: cannot resolve worktree identity — check git repository state. Fix git state or remove engram_session from settings.json to bypass."` Read-only operations degrade gracefully. Session startup is **not** blocked. |
| Clean expired snapshots (>90d by filename timestamp) | Max 50 files | Fail-open: retry next session |
| Clean expired chain state (>24h) | Max 20 files | Fail-open |
| Clean orphan payload files (>24h) | Max 20 files | Fail-open |
| Verify `.engram-id` exists | 1 read | Warn if missing (diagnostic only — does not create) |

Per-file cleanup that exceeds 5ms is aborted (skip remaining files). This prevents a single slow file from blowing the startup budget.

### Bootstrap Relationship

SessionStart does not create `.engram-id` — it requires a git commit, which is inappropriate during session initialization. Bootstrap occurs via `engram init` (see [skills table](skill-surface.md#skills-13-total)). Until `.engram-id` exists, all mutating Engram operations (save, defer, distill, ticket create) fail closed with error: `"Engram not initialized: run 'engram init' to bootstrap."` Read-only operations (search, triage) degrade gracefully via the [degradation model](storage-and-indexing.md#degradation-model).

## Enforcement Exceptions

| Exception | Scope | Rationale |
|---|---|---|
| `/promote` Step 2 CLAUDE.md write | Single skill, single target | CLAUDE.md is an external sink, not an Engram-managed record. The Knowledge engine owns promotion *state* via [promote-meta](types.md#promote-meta-promotion-state-record). See [permitted exceptions](foundations.md#permitted-exceptions). |

No other skill-level write to a protected or externally-owned path is sanctioned. New exceptions require an entry in both this table and foundations.md.

**Sequencing:** The authoritative exception definition lives in [foundations.md §Permitted Exceptions](foundations.md#permitted-exceptions). This table references it for enforcement-level discoverability.

## Autonomy Model

| Subsystem | Model | Rationale |
|---|---|---|
| Work | `suggest` / `auto_audit` | Trust boundary: agents propose, users approve |
| Context | None | Agents save their own session state |
| Knowledge staging | `gated` | User reviews via `/curate` before publication. `/distill` auto-stages without user confirmation; `/learn` publishes directly. Staging inbox cap + idempotency bound autonomous volume. |

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

**Configuration read semantics:** All configuration values in `.claude/engram.local.md` are read at engine invocation time — no session-level caching. Config changes take effect on the next operation. This applies to both `autonomy.*` and `ledger.*` settings.

### Staging Inbox Cap

The staging inbox cap is configured via `knowledge_max_stages` in `.claude/engram.local.md`. Values less than 1 are invalid; the engine rejects the configuration at parse time with `"knowledge_max_stages must be >= 1"`.

The cap enforces whole-batch rejection for determinism. See [operations.md §Distill](operations.md#distill-context-to-knowledge-staged) for the behavioral specification (rejection logic, formula, error message format, edge cases, and recovery path).
