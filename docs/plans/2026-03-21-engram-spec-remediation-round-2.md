# Engram Spec Remediation Plan — Round 2

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate 47 canonical findings (3 P0, 31 P1, 13 P2) from the Round 2 spec review by editing spec markdown files — no code changes.

**Architecture:** Five commits, ordered by dependency. Commit 1 (trust injection contract) is the critical path — it defines contracts that Commits 4-5 reference in verification items. Commits 2-3 are independent of each other but must precede Commit 4 (VR renumbering produces unique IDs that new verification items need). Commit 5 batches all P2 fixes.

**Tech Stack:** Markdown spec files at `docs/superpowers/specs/engram/` (10 files, ~1769 lines). No code, no tests, no dependencies.

**Review findings:** `.review-workspace/synthesis/report.md` (47 findings), `.review-workspace/synthesis/ledger.md` (full ledger)

**Codex dialogue outcomes:** Thread `019d138b-05ea-7e93-8a7e-4ffdedec4de9` — resolved T1 design decisions (split contract model, payload file contract, function signature, bridge gap elimination, /quicksave routing)

---

## Commit 1 — Trust Injection Unified Contract

**Finding count:** 4 P1 contract gaps (SY-10, SY-11, SY-12, SY-13) — these also unblock 2 P0 verification fixes (SY-1, SY-2) in Commit 4.

**Files:**
- Modify: `enforcement.md` — §Trust Injection (lines 75-118), §Hooks table (line 14), §Protected-Path (line 41), §Inter-Hook Runtime State (lines 108-114)
- Modify: `delivery.md` — §Build Sequence (lines 18-32), §Step 2a (lines 124-133)
- Modify: `foundations.md` — §Package Structure (lines 46-64)
- Modify: `skill-surface.md` — `/quicksave` row (line 16)

**Design decisions (from Codex dialogue):**

| Decision | Resolution |
|----------|-----------|
| Contract model | **Split:** engine trust injection (Bash+payload) for Work/Knowledge vs. direct-write path authorization (Write/Edit) for Context |
| Payload file | `.claude/engram-tmp/<subsystem>-<operation>-<uuid>.json`, workspace-local, caller creates/cleans up |
| `collect_trust_triple_errors()` | `(hook_injected: bool, hook_request_origin: str \| None, session_id: str \| None) -> list[str]`. Returns errors, doesn't raise. Hardcoded origin set `{"user", "agent"}`. |
| Bridge trust gap | **Eliminated** — ship `engine_trust_injection` capability at Step 2a (with Knowledge engine), not Step 3a |
| `/quicksave` routing | **Stays on Write/Edit** — uses path authorization + embedded provenance, not engine trust injection |

### Task 1.1: Add split contract preamble to §Trust Injection

- [ ] **Step 1:** In `enforcement.md`, replace the existing §Trust Injection introductory paragraph (line 77) with the split contract model description:

```markdown
## Trust Injection

Two enforcement mechanisms share a single `engram_guard` hook, distinguished by `tool_name`:

| Mechanism | Transport | Applies To | How |
|-----------|-----------|------------|-----|
| **Engine trust injection** | Bash (`python3 engine_*.py`) | Work, Knowledge | Payload file with trust triple → engine validates via `collect_trust_triple_errors()` |
| **Direct-write path authorization** | Write, Edit | Context | Path ownership check → embedded provenance in content → post-write quality validation |

**Governing principle:** Uniformity of policy (every mutation is authorized), not uniformity of transport.
```

- [ ] **Step 2:** Update the §Hooks table (line 14) `engram_guard` Purpose cell to reference both mechanisms:

```markdown
| `engram_guard` | PreToolUse (Write, Edit, Bash) | 1st | [Engine trust injection + direct-write path authorization](#trust-injection) | **Block** |
```

- [ ] **Step 3:** Verify no broken cross-references by searching for `#trust-injection` anchors across all spec files.

### Task 1.2: Define payload file contract (SY-10)

- [ ] **Step 1:** After the new §Trust Injection preamble table (from Task 1.1), add a new subsection `### Payload File Contract` before the existing `### Step 1: Injection`:

```markdown
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
```

- [ ] **Step 2:** Update §Step 1: Injection (line 81) to reference the payload file contract. Replace the current sentence about writing `hook_injected=True` to the payload file with:

```markdown
When `engram_guard` detects an authorized engine invocation, it writes the trust triple to a new [payload file](#payload-file-contract) atomically. The file path is passed to the engine via the Bash command's argument list (matching the proven ticket plugin pattern).
```

- [ ] **Step 3:** Add `.claude/engram-tmp/` to §SessionStart Hook operations table (line 122) as a cleanup operation:

```markdown
| Clean orphan payload files (>24h) | Max 20 files | Fail-open |
```

### Task 1.3: Define collect_trust_triple_errors() function contract (SY-11)

- [ ] **Step 1:** After §Step 2: Validation heading (line 87), add a function contract subsection before the existing paragraph:

```markdown
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

**Validation rules (order matters):**
1. `hook_injected` must be `True` (identity check: `hook_injected is True`). `False`, `None`, or non-bool → error.
2. `hook_request_origin` must be a non-empty string in `{"user", "agent"}`. `None`, empty string, or unrecognized value → error.
3. `session_id` must be a non-empty string. `None` or empty string → error.

**Stable error strings:** `"hook_injected: must be True, got {value!r}"`, `"hook_request_origin: must be one of {{'user', 'agent'}}, got {value!r}"`, `"session_id: must be non-empty string, got {value!r}"`.

**Caller obligation:** If the returned list is non-empty, the engine must reject the operation with a structured error containing the error list and return without making state changes. The engine must not catch or suppress errors from this function.

**Origin-matching responsibility:** `collect_trust_triple_errors()` validates that the triple is well-formed. Whether the `hook_request_origin` matches the expected origin for a given entrypoint (e.g., `_user.py` expects `"user"`) is the entrypoint's responsibility — the validator does not enforce route-specific origin rules.

**Module location:** `engram_core/trust.py`. Add to [package structure](foundations.md#package-structure).
```

- [ ] **Step 2:** Update foundations.md §Package Structure to include `trust.py`:

```python
│   ├── trust.py             # collect_trust_triple_errors() — shared trust validator
```

Insert after the `canonical.py` line (line 56 in foundations.md).

- [ ] **Step 3:** Update the existing §Step 2 paragraph (line 89 of enforcement.md) to reference the function contract. Replace **only** the first sentence of line 89 ("Every **mutating** entrypoint... structured error.") with:

```markdown
Every **mutating** entrypoint in each subsystem engine must invoke [`collect_trust_triple_errors()`](#collect_trust_triple_errors-contract) before making state changes. This gates all [cross-subsystem operations](operations.md#core-rules) that flow through engine entrypoints. See the function contract above for validation rules, error format, and caller obligation.
```

**Keep all subsequent content intact:** the mutating entrypoints enumeration (lines 91-96), the `/learn` routing note (line 96), and the read-only exemption + delivery.md mandate (line 98). The Context row in the enumeration (line 94) will be modified by Task 1.4 Step 3 — leave it unchanged for now.

### Task 1.4: Add direct-write path authorization contract (SY-13)

- [ ] **Step 1:** After §Step 3: Per-Subsystem Enforcement (line 100-102), add a new section:

```markdown
### Direct-Write Path Authorization

Context subsystem writes (`/save`, `/quicksave`, `/load`) use the Write and Edit tools natively — they do not route through engine Bash invocations. When `engram_guard` detects a Write or Edit call to a Context-owned path (snapshots, checkpoints), it performs **path authorization** rather than engine trust injection:

1. **Path ownership check:** Verify the target path is within the Context subsystem's private root (`~/.claude/engram/<repo_id>/snapshots/**` or `checkpoints/**`). Paths outside these directories are not Context-owned.
2. **Allow the write.** Context paths are intentionally excluded from [protected-path enforcement](#protected-path-enforcement) (they are not engine-managed).
3. **Post-write quality validation** via [`engram_quality`](#quality-validation) checks content quality (frontmatter completeness, section count).
4. **Provenance is embedded** in the written content (frontmatter `session_id`, `worktree_id`, `orchestrated_by`), validated by `/triage` [anomaly detection](operations.md#triage-read-work-and-context).

This is explicitly **path authorization plus provenance/integrity validation**, not engine trust injection. The `collect_trust_triple_errors()` validator is not invoked for direct-write paths.
```

- [ ] **Step 2:** Update the §Protected-Path Enforcement intentional exclusions paragraph (line 41) to reference the new section:

Replace:
```markdown
Context subsystem writes use Write/Edit tools natively (session orchestration) rather than routing through engine Bash invocations, so PreToolUse path blocking would prevent normal operation. Advisory quality checks via [`engram_quality`](#quality-validation) cover these paths instead.
```

With:
```markdown
Context subsystem writes use Write/Edit tools natively. See [direct-write path authorization](#direct-write-path-authorization) for the enforcement model. Advisory quality checks via [`engram_quality`](#quality-validation) cover content quality.
```

- [ ] **Step 3:** Remove "Context: snapshot write, checkpoint write" from the mutating entrypoints enumeration (line 94). Replace with a cross-reference:

```markdown
- **Context:** See [direct-write path authorization](#direct-write-path-authorization) (Write/Edit path, not engine trust injection)
```

- [ ] **Step 4:** Add an explicit routing statement to skill-surface.md `/quicksave` row (line 16). Change:

```markdown
| `/quicksave` | Context | Lightweight: 5 sections, no defer, no distill. |
```

To:

```markdown
| `/quicksave` | Context | Lightweight: 5 sections, no defer, no distill. Writes checkpoint directly via Write tool (not through engine Bash) — see [direct-write path authorization](enforcement.md#direct-write-path-authorization). |
```

### Task 1.5: Eliminate bridge trust gap via incremental guard delivery (SY-12)

- [ ] **Step 1:** In delivery.md §Build Sequence (lines 18-32), add a note between Step 1 and Step 2:

```markdown
Step 2: Knowledge cutover + engram_guard engine_trust_injection capability
```

Replace the current `Step 2: Knowledge cutover` line (line 25).

- [ ] **Step 2:** In delivery.md §Step 2a table (lines 126-131), add `engram_guard` as a Step 2a deliverable:

```markdown
| `engram_guard` hook (engine trust injection only) | [Engine trust injection](enforcement.md#trust-injection) for Knowledge engine. Write/Edit path authorization deferred to Step 3a. |
```

- [ ] **Step 3:** In delivery.md §Step 3a table (lines 155-162), change the engram_guard entry from introducing the hook to extending it:

Replace:
```markdown
| `engram_guard` hook | [Protected-path enforcement](enforcement.md#protected-path-enforcement) + [trust injection](enforcement.md#trust-injection) |
```

With:
```markdown
| `engram_guard` hook (full) | Extends Step 2a hook with [protected-path enforcement](enforcement.md#protected-path-enforcement) + [direct-write path authorization](enforcement.md#direct-write-path-authorization) for Work paths |
```

- [ ] **Step 4:** In enforcement.md §Trust Injection, after the split contract table (Task 1.1), add a guard capability rollout gating note:

```markdown
**Guard capability rollout:** Each build step lists the `engram_guard` capabilities it requires. No subsystem may activate a mutating route before the guard capabilities required for that route are active.

| Capability | Ships At | Covers |
|-----------|----------|--------|
| `engine_trust_injection` | Step 2a | Knowledge engine mutating entrypoints (Bash-mediated) |
| `engine_trust_injection` (extended) | Step 3a | Work engine mutating entrypoints |
| `write_path_authorization` | Step 4a | Context direct-write paths (Write/Edit-mediated) |
```

- [ ] **Step 5:** Commit.

```bash
git add docs/superpowers/specs/engram/enforcement.md docs/superpowers/specs/engram/delivery.md docs/superpowers/specs/engram/foundations.md docs/superpowers/specs/engram/skill-surface.md
git commit -m "fix(spec): define trust injection unified contract (SY-10,11,12,13)

Split contract model: engine trust injection (Bash+payload) for Work/Knowledge
vs. direct-write path authorization (Write/Edit) for Context. Defines payload
file contract, collect_trust_triple_errors() signature, incremental guard
delivery, and /quicksave routing.

Resolves: SY-10, SY-11, SY-12, SY-13
Unblocks: SY-1, SY-2 (P0 verification gaps in Commit 4)

Design: Codex dialogue 019d138b-05ea-7e93-8a7e-4ffdedec4de9"
```

---

## Commit 2 — Authority and Structural Fixes

**Finding count:** 3 P1 authority (SY-7, SY-22, SY-23) + 2 P1 structural (SY-4, SY-21) = 5 findings.

**Files:**
- Modify: `enforcement.md` — §Enforcement Boundary Constraint (lines 71-73), §Bridge Period Limitations (lines 116-118)
- Modify: `foundations.md` — §Design Principles (lines 69-85)
- Modify: `delivery.md` — all Required Verification sections (VR ID renumbering), VR-7 assertion text (line 50)

### Task 2.1: Fix authority misplacements in enforcement.md (SY-7, SY-23)

- [ ] **Step 1:** Replace enforcement.md §Enforcement Boundary Constraint body (lines 71-73). Keep the section heading, replace content with a cross-reference only:

```markdown
### Enforcement Boundary Constraint

See [foundations.md §Enforcement Boundary Constraint](foundations.md#enforcement-boundary-constraint) for the governing architecture rule (authoritative). `engram_quality` uses **Warn** (not Block) as its failure mode in compliance with this constraint.
```

- [ ] **Step 2:** Replace enforcement.md §Bridge Period Limitations body (lines 116-118). Keep the section heading, replace content with a cross-reference:

```markdown
### Bridge Period Limitations

Phase-scoped idempotency is a delivery-period limitation. See [delivery.md §Bridge Cutover](delivery.md#step-1-bridge-cutover) for the authoritative phase schedule and [operations.md §Phase-Scoped Idempotency](operations.md#envelope-invariants) for the operational specification.
```

### Task 2.2: Promote Enforcement Boundary Constraint to invariant (SY-22)

- [ ] **Step 1:** In foundations.md, restructure §Design Principles (lines 69-85). Change the preamble (lines 69-71) to distinguish principles from the constraint:

Replace:
```markdown
## Design Principles

Three cross-cutting principles guide implementation decisions across subsystems. These are not invariants (they have no enforcement mechanism) but inform trade-offs.
```

With:
```markdown
## Design Principles

Three cross-cutting principles guide implementation decisions across subsystems. The first two are advisory (they have no enforcement mechanism) but inform trade-offs. The third — the Enforcement Boundary Constraint — is a hard invariant enforced structurally by hook registration.
```

- [ ] **Step 2:** In the §Enforcement Boundary Constraint subsection (lines 83-85), add an explicit invariant marker:

Replace:
```markdown
#### Enforcement Boundary Constraint

PostToolUse hooks **must not** become enforcement boundaries.
```

With:
```markdown
#### Enforcement Boundary Constraint (Invariant)

**Invariant:** PostToolUse hooks **must not** become enforcement boundaries.
```

The rest of the subsection (lines 84-85) stays unchanged.

### Task 2.3: Global VR ID renumbering (SY-4)

- [ ] **Step 1:** In delivery.md, apply the following VR ID renumbering table across all Required Verification sections. Use step-prefixed IDs for global uniqueness:

| Old ID | Step | New ID | Test Name |
|--------|------|--------|-----------|
| VR-1 | 0a | VR-0A-1 | Core invariant structural tests |
| VR-6 | 0a | VR-0A-2 | canonical_json_bytes() contract |
| VR-7 | 0a | VR-0A-3 | VERSION_UNSUPPORTED error |
| VR-9 | 0a | VR-0A-4 | parse_sha256_hex() contract |
| VR-10 | 0a | VR-0A-5 | Degradation model |
| VR-14 | 0a | VR-0A-6 | Normalization boundary |
| VR-19 | 0a | VR-0A-7 | Text search contract |
| VR-21 | 0a | VR-0A-8 | Namespace status filtering |
| T1-gate-1 | 0a→2a | T1-gate-1 | (unchanged — cross-step) |
| T1-gate-2 | 0a→2a | T1-gate-2 | (unchanged — cross-step) |
| VR-15 | 0b | VR-0B-1 | engram init idempotency |
| VR-9 | 1 | VR-1-1 | Bridge old engine acceptance |
| VR-15 | 2a | VR-2A-1 | Promote-path wiring |
| VR-16 | 2a | VR-2A-2 | Promote hash recomputation |
| VR-4 | 2a | VR-2A-3 | Write concurrency |
| VR-5 | 2a | VR-2A-4 | PromoteEnvelope idempotency |
| *(no VR tag)* | 3a | VR-3A-1 | Envelope idempotency (currently cited as `SY-5` inline — assign VR tag) |
| VR-11 | 3a | VR-3A-2 | Phase-scoped idempotency gate |
| VR-8 | 3a | VR-3A-3 | Staging inbox cap |
| VR-17 | 3a | VR-3A-4 | Staging cap edge case |
| VR-8 | 3a | VR-3A-5 | Trust triple partial validation |
| VR-7 | 3a | VR-3A-6 | Compatibility harness |
| VR-13 | 3a | VR-3A-7 | Ledger append failure isolation |
| VR-5 | 4a | VR-4A-1 | Chain state migration |
| *(no VR tag)* | 4a | VR-4A-2 | Migration idempotency (currently cited as `SY-6` inline — assign VR tag. Includes new-source test from VR-18) |
| VR-4 | 4a | VR-4A-3 | SessionStart timing |
| VR-6 | 4a | VR-4A-4 | /triage promote-meta |
| VR-10 | 4a | VR-4A-5 | Promote marker lifecycle |
| VR-12+VR-16 | 4a | VR-4A-6 | Snapshot intent fields |
| VR-12b | 4a | VR-4A-7 | Archive-before-state-write |
| VR-14 | 4a | VR-4A-8 | engram_quality advisory |
| VR-13 | 4a | VR-4A-9 | Triage inference matrix |
| VR-18 | 4a | VR-4A-10 | Triage ledger-off |
| VR-19 | 4a | VR-4A-11 | Triage provenance anomaly |

- [ ] **Step 2:** Apply the renumbering across all Required Verification sections in delivery.md. For each section (Step 0a, 0b, 1, 2a, 3a, 4a), replace old VR IDs with new ones.

- [ ] **Step 3:** Check enforcement.md line 98 for VR ID references. The mandate ("delivery.md Step 3a must include a verification step...") references the step by name, not by VR ID, so no VR ID update is needed here. Verify no other enforcement.md cross-references use old VR IDs.

### Task 2.4: Fix VERSION_UNSUPPORTED assertion (SY-21)

- [ ] **Step 1:** In delivery.md §Step 0a Required Verification, find the VR-0A-3 line (was VR-7, line 50). Replace:

```markdown
assert error code and expected version range
```

With:

```markdown
assert `error_code == "VERSION_UNSUPPORTED"`, `received_version == "99.0"`, and `expected_version` is a single string matching the engine's built-in version (not a list or range). See [types.md §Compatibility Rules](types.md#compatibility-rules).
```

- [ ] **Step 2:** Commit.

```bash
git add docs/superpowers/specs/engram/enforcement.md docs/superpowers/specs/engram/foundations.md docs/superpowers/specs/engram/delivery.md
git commit -m "fix(spec): authority fixes + VR ID renumbering (SY-4,7,21,22,23)

Replace enforcement.md authority misplacements with cross-references.
Promote Enforcement Boundary Constraint to invariant in foundations.md.
Global VR ID renumbering: step-prefixed scheme (VR-0A-1, VR-3A-1, etc.).
Fix VERSION_UNSUPPORTED assertion from range to singular.

Resolves: SY-4, SY-7, SY-21, SY-22, SY-23"
```

---

## Commit 3 — Session, Schema, and Behavioral Contracts

**Finding count:** 3 session (SY-5, SY-6, SY-14) + 4 schema (SY-8, SY-9, SY-18, SY-19) + 4 behavioral (SY-15, SY-16, SY-17, SY-20) = 11 findings.

**Files:**
- Modify: `enforcement.md` — §SessionStart Hook (lines 120-134), §Ledger Multi-Producer Note (line 27), §Inter-Hook Runtime State (line 112)
- Modify: `types.md` — §promote-meta (lines 107-130), §Idempotency (lines 250-256), §RecordRef (lines 22-26), §Event Vocabulary (lines 357-367)
- Modify: `storage-and-indexing.md` — §Dual-Root Storage Layout (lines 20-38), §Key Storage Decisions (line 50)
- Modify: `operations.md` — §Distill (curate dedup), §Promote Branch B2

### Task 3.1: Define session diagnostic channel (SY-5)

- [ ] **Step 1:** In enforcement.md, after §Ledger Multi-Producer Note (line 27), add a new subsection:

```markdown
### Session Diagnostic Channel

Hook failures are written to a per-session diagnostic file at `~/.claude/engram/<repo_id>/ledger/<worktree_id>/<session_id>.diag`. Format: one JSON object per line (same JSONL as ledger shards).

```json
{"ts": "<ISO 8601 UTC>", "hook": "engram_register", "failure_type": "lock_timeout", "message": "..."}
```

**Write semantics:** Append-only, best-effort (diagnostic writes must not fail-closed). No lock required — single producer (the hook that failed).

**Read protocol:** `/triage` checks for `<session_id>.diag` files. If present and non-empty, surfaces `"ledger unavailable in session <session_id>"` instead of `"completion not proven"` for that session's operations. See [/triage inference matrix](operations.md#triage-read-work-and-context).

**TTL:** Same as ledger shards — append-only, no TTL. Cleaned up if parent session directory is removed.
```

- [ ] **Step 2:** Update line 27 to reference the new section. Replace the two sentences starting with "All failures are written to the session diagnostic channel. `/triage` surfaces..." with a single cross-reference:

```
All failures are written to the [session diagnostic channel](#session-diagnostic-channel). See that section for the `/triage` read protocol.
```

This removes the inline `/triage` behavior description (now fully specified in the new section).

### Task 3.2: Specify fail-closed scope for engram_session (SY-6)

- [ ] **Step 1:** In enforcement.md §SessionStart Hook table (line 126), expand the `worktree_id` failure mode:

Replace:
```markdown
| Resolve `worktree_id` | 1 call | Fail-closed: session needs identity |
```

With:
```markdown
| Resolve `worktree_id` | 1 call | Fail-closed: `engram_session` returns exit code 0 but stores error state. All subsequent Engram mutating operations fail-closed with: `"Engram: cannot resolve worktree identity — check git repository state. Fix git state or remove engram_session from settings.json to bypass."` Read-only operations degrade gracefully. Session startup is **not** blocked. |
```

### Task 3.3: Fix worktree_id contradictory language (SY-14)

- [ ] **Step 1:** In enforcement.md §Inter-Hook Runtime State (line 112), replace:

```markdown
`engram_guard` MUST recompute `worktree_id` independently via `identity.get_worktree_id()`
```

With:

```markdown
`engram_guard` MUST obtain `worktree_id` by calling `identity.get_worktree_id()` at invocation time (not from any cached session state)
```

### Task 3.4: Add PromoteMeta uniqueness invariant and write mechanism (SY-8)

- [ ] **Step 1:** In types.md §promote-meta (after line 119), add a uniqueness invariant:

```markdown
**Uniqueness invariant:** At most one `promote-meta` comment per `lesson_id` may exist in `learnings.md`. On Step 3 write, the Knowledge engine scans for an existing `promote-meta` with matching `lesson_id` and replaces it in-place (not append). If two `promote-meta` comments with the same `lesson_id` are found (corrupted state), treat as Branch D (unreadable promote-meta) and surface a migration warning.
```

### Task 3.5: Add DeferEnvelope nullable context construction rule (SY-9)

- [ ] **Step 1:** In types.md §Idempotency material table (line 252), after the `DeferEnvelope` row's field inclusion rationale, add:

```markdown
**Construction rule for nullable fields:** When `DeferEnvelope.context` is `None`, omit the `context` key from the material dict entirely. Do not include `{"context": None}` — [`canonical_json_bytes()`](#canonical-json) rejects `None` values with `ValueError`. This applies to all envelope types: omit nullable fields from the material dict when their value is `None`.
```

### Task 3.6: Fix RecordRef from_str() lossy claim (SY-18)

- [ ] **Step 1:** In types.md §RecordRef (lines 22-26), replace:

```python
    def from_str(s: str) -> RecordRef: ...  # Inverse of to_str
```

With:

```python
    @classmethod
    def from_str(cls, s: str, repo_id: str) -> RecordRef: ...
    # Not a pure inverse of to_str — repo_id is required because
    # canonical serialization omits it. Callers provide the current
    # repo's repo_id.
```

And update the canonical serialization paragraph (line 26) to remove the word "inverse" — replace "Implemented as `RecordRef.to_str()` / `RecordRef.from_str()`" with "Implemented as `RecordRef.to_str()` for serialization and `RecordRef.from_str(s, repo_id)` for deserialization (`repo_id` required — not a pure inverse since canonical form omits `repo_id`)."

### Task 3.7: Address staging filename truncation (SY-19)

- [ ] **Step 1:** In storage-and-indexing.md §Key Storage Decisions point 4 (line 50), after "identical candidates from concurrent operations coalesce to the same filename," add:

```markdown
When `O_CREAT | O_EXCL` fails (file already exists), the engine compares the full `content_sha256` of the existing staging file with the new candidate's `content_sha256`. If they match, this is a genuine duplicate — coalesce (no action). If they differ, this is a hash-prefix collision — write the new candidate with a disambiguating suffix (`-1`, `-2`, etc.) and log a diagnostic. Collision probability with 16 hex chars (64-bit space) is negligible for expected staging volumes (<1000 candidates).
```

### Task 3.8: Event vocabulary decision (SY-15)

- [ ] **Step 1:** In types.md §Event Vocabulary (line 367), after the "Completion events are success-only" paragraph, add an explicit exclusion note:

```markdown
**Excluded from v1:** `/learn`, `/curate`, and `/promote` do not emit completion events. These operations are user-interactive (not orchestrated by `/save`) and their completion is verifiable by examining the resulting artifacts — published entries in `learnings.md` (for `/learn`, `/curate`) and promote-meta + CLAUDE.md markers (for `/promote`). Adding completion events for these operations is a candidate for v2 if `/triage` requires finer-grained completion tracking.
```

### Task 3.9: Specify /learn dedup lock scope (SY-16)

- [ ] **Step 1:** In types.md §Write Concurrency (line 310), after the lock description, add:

```markdown
**Dedup-within-lock:** Both `/learn` and `/curate` publish paths must perform the `content_sha256` dedup check against published entries within the same `fcntl.flock(LOCK_EX)` scope as the write to `learnings.md`. Performing the dedup check before acquiring the lock creates a TOCTOU race between concurrent publish operations.
```

### Task 3.10: Clarify Promote B2 reconcile path (SY-17)

- [ ] **Step 1:** In operations.md §Promote, find the Branch B2 description. Add clarification about Step 3 execution after manual placement:

```markdown
After the user confirms manual placement in the new section, the skill writes the promoted text wrapped in markers at the user-confirmed location. Step 3 then reads back the text between markers at the new location and computes `transformed_text_sha256` via `drift_hash()`. Step 3 also updates `promote-meta.target_section` to the user-confirmed section. If the skill cannot locate markers at the new location after user confirmation, Step 3 rejects the promote-meta write (lesson remains eligible for next `/promote`).
```

### Task 3.11: Add .archive/ to storage layout (SY-20)

- [ ] **Step 1:** In storage-and-indexing.md §Dual-Root Storage Layout (line 27), add `.archive/` under `snapshots/`:

```markdown
├── snapshots/                       # Full session handoffs
│   ├── YYYY-MM-DD_HH-MM_<slug>.md
│   └── .archive/                    # Archived snapshots (moved by /load chain protocol)
```

- [ ] **Step 2:** In the TTL table (line 56), find the full row:

```markdown
| Snapshots/checkpoints | 90-day TTL from creation (filename timestamp). [SessionStart](enforcement.md#sessionstart-hook) deletes files older than 90 days. No intermediate "archive" tier. | Private root |
```

Replace that entire row with:

```markdown
| Snapshots/checkpoints | 90-day TTL from creation (filename timestamp). [SessionStart](enforcement.md#sessionstart-hook) deletes files older than 90 days. Archived snapshots (`.archive/`) follow the same 90-day TTL. | Private root |
```

- [ ] **Step 3:** Commit.

```bash
git add docs/superpowers/specs/engram/enforcement.md docs/superpowers/specs/engram/types.md docs/superpowers/specs/engram/storage-and-indexing.md docs/superpowers/specs/engram/operations.md
git commit -m "fix(spec): session, schema, and behavioral contracts (SY-5,6,8,9,14,15,16,17,18,19,20)

Define session diagnostic channel. Specify fail-closed scope for engram_session.
Fix worktree_id contradictory language. Add PromoteMeta uniqueness invariant.
Add nullable context construction rule. Fix RecordRef from_str() lossy claim.
Address staging truncation collision. Document event vocabulary exclusions.
Specify /learn dedup lock scope. Clarify Promote B2. Add .archive/ to layout.

Resolves: SY-5, SY-6, SY-8, SY-9, SY-14, SY-15, SY-16, SY-17, SY-18, SY-19, SY-20"
```

---

## Commit 4 — Verification Gap Backfill

**Finding count:** 3 P0 (SY-1, SY-2, SY-3) + 11 P1 singletons (SY-24 through SY-34) = 14 findings.

**Depends on:** Commit 1 (trust contracts for SY-1, SY-2 test specs), Commit 2 (unique VR IDs for new items).

**Files:**
- Modify: `delivery.md` — §Step 3a Required Verification, §Step 4a Required Verification, §Step 0a Required Verification, §Cross-Cutting Verification

### Task 4.1: Add engram_guard negative-case test (SY-1, P0)

- [ ] **Step 1:** In delivery.md §Step 3a Required Verification, add:

```markdown
- Trust injection path matching negative test (VR-3A-8): invoke `engram_guard` with a Bash tool call executing `python3 /tmp/engine_work.py` (valid filename, outside `<engram_scripts_dir>`). Assert: [payload file](enforcement.md#payload-file-contract) is NOT created. Then invoke with `python3 <engram_scripts_dir>/engine_work.py` (correct path). Assert: payload file IS created with valid trust triple fields.
```

### Task 4.2: Add trust triple call-site completeness test (SY-2, P0)

- [ ] **Step 1:** In delivery.md §Step 3a Required Verification, add:

```markdown
- Trust triple call-site completeness (VR-3A-9): for each documented mutating entrypoint (Work: ticket creation, ticket update, ticket close; Knowledge: knowledge publish, staging write, promote-meta write), assert via AST scan or instrumented test that [`collect_trust_triple_errors()`](enforcement.md#collect_trust_triple_errors-contract) is called before any filesystem write. Acceptable methods: (a) `ast.parse` + visitor asserting the call appears before `open(..., 'w')` / `os.replace` / `shutil` calls; (b) mock `collect_trust_triple_errors` to raise on first call, invoke entrypoint, assert exception propagated.
```

- [ ] **Step 2:** In delivery.md §Step 4a Required Verification, add the Context counterpart:

```markdown
- Context call-site completeness (VR-4A-12): Context write paths do not use `collect_trust_triple_errors()` (they use [direct-write path authorization](enforcement.md#direct-write-path-authorization)). Verify: `grep -r "collect_trust_triple_errors" scripts/context/` returns no matches — Context engine must NOT call the trust validator.
```

### Task 4.3: Add worktree isolation test (SY-3, P0)

- [ ] **Step 1:** In delivery.md §Step 4a Required Verification, add:

```markdown
- Worktree isolation test (VR-4A-13): create two worktrees from the same repo (same `repo_id`, distinct `worktree_id`). Run `/save` in each. Assert: (a) `query(subsystems=["context"])` in worktree A returns no entries from worktree B's `snapshots/` or `chain/` directories; (b) same assertion for worktree B. Assert: both entries have identical `repo_id` but distinct `worktree_id` in `RecordMeta`.
```

### Task 4.4: Add remaining verification gap items (SY-24 through SY-34)

- [ ] **Step 1:** In delivery.md §Step 4a Required Verification, add:

```markdown
- engram_quality catch-all exception test (VR-4A-14): monkey-patch the hook's internal validation function to raise `RuntimeError`. Assert: exit code 0, `[engram_quality:error]` log entry present. Verifies the outermost catch-all, not just specific failure paths. (SY-24)
```

- [ ] **Step 2:** In delivery.md §Step 0a Required Verification, add a deferred gate tracking note:

```markdown
- Deferred gate stubs (VR-0A-9): T1-gate-1 and T1-gate-2 fixture stubs must exist as empty test files with TODO comments citing target behaviors before Step 0a is marked complete. This ensures deferred obligations are tracked structurally. (SY-25)
```

- [ ] **Step 3:** In delivery.md §Step 0a Required Verification, add (`IndexEntry` is a Step 0a deliverable):

```markdown
- IndexEntry.snippet contract test (VR-0A-10): for each NativeReader (context, work, knowledge), create a fixture file with body exceeding 500 characters. Assert: `IndexEntry.snippet` ≤ 200 characters. Assert: snippet does not end mid-word. (SY-26)
```

- [ ] **Step 4:** In delivery.md §Step 4a Required Verification, add:

```markdown
- /timeline git integration test (VR-4A-15): (a) commit a ticket to the shared root; (b) run `/timeline` for that session; (c) assert output includes at least one entry attributed via `git log` (labeled "inferred"); (d) mock `git log` to raise CalledProcessError — assert `/timeline` returns partial result with degradation warning. (SY-27)
```

- [ ] **Step 5:** In delivery.md §Cross-Cutting Verification, expand the smoke test specification:

```markdown
**Minimal observable output per skill (SY-28):**

| Skill | Minimal Assertion |
|-------|-------------------|
| `engram init` | `.engram-id` created, valid UUIDv4 content, exit code 0 |
| `/save` | Per-step results dict present, `snapshot` field non-empty |
| `/quicksave` | Checkpoint file created, frontmatter parseable |
| `/load` | Snapshot content displayed, chain state updated |
| `/defer` | Ticket created, `RecordRef` returned |
| `/distill` | ≥1 staging file created |
| `/curate` | Published entry in `learnings.md` |
| `/learn` | Published entry in `learnings.md` with `lesson-meta` |
| `/promote` | Markers in CLAUDE.md, `promote-meta` in `learnings.md` |
| `/search` | ≥1 result returned, subsystem label present |
| `/timeline` | ≥1 entry returned, label present |
| `/ticket` | Ticket file created in `engram/work/` |
| `/triage` | Report rendered, no unhandled exceptions |
```

- [ ] **Step 6:** In delivery.md §Step 4a Required Verification, add:

```markdown
- Context status derivation test (VR-4A-16): (a) snapshot in `snapshots/` → `query(status="context:active")` returns it; (b) same file moved to `snapshots/.archive/` → `query(status="context:archived")` returns it, `query(status="context:active")` does not. (SY-29)
- Ledger multi-producer concurrency test (VR-4A-17): spawn 10 concurrent threads, each appending one `LedgerEntry` to the same shard. Assert: shard has exactly 10 valid JSON lines, no partial lines, lock file absent post-completion. (SY-30)
```

- [ ] **Step 7:** In delivery.md §Step 0a Required Verification, add:

```markdown
- `since` filter test (VR-0A-11): fixture with 3 entries at different timestamps. `query(since=<cutoff>)` returns only post-cutoff entries. UTC normalization: entry with +05:30 timestamp → `IndexEntry.created_at` is UTC-normalized. (SY-31)
```

- [ ] **Step 8:** In delivery.md §Step 4a Required Verification, add:

```markdown
- Promote Branch D exclusion test (VR-4A-18): fixture with `promote-meta` having `meta_version: "99.0"`. Run `/promote`. Assert: lesson NOT in selectable candidate list. Assert: warning containing lesson_id and "unreadable promote-meta" surfaced. (SY-32)
```

- [ ] **Step 9:** In delivery.md §Step 1 Required Verification, add:

```markdown
- SourceResolver exact-value assertion (VR-1-2): assert `source.type == f"engram:{source_ref.subsystem}:{source_ref.record_kind}"`, `source.ref == source_ref.to_str()`, `source.session == <expected_session_id>` with known fixture. (SY-33)
```

- [ ] **Step 10:** In delivery.md §Step 4a Required Verification, add an environment qualifier to VR-4A-3 (SessionStart timing):

```markdown
Environment probe: before asserting <500ms, measure median per-file read latency on a 10-file fixture. If per-file latency exceeds 10ms, mark the timing assertion as skipped/environment with a warning. (SY-34)
```

- [ ] **Step 11:** Commit.

```bash
git add docs/superpowers/specs/engram/delivery.md
git commit -m "fix(spec): backfill 14 verification gaps including 3 P0s (SY-1,2,3,24-34)

Add engram_guard negative-case test (P0), trust triple call-site completeness
test (P0), worktree isolation test (P0), plus 11 additional verification items.
Per-skill smoke test observable output table. New VR IDs: VR-3A-8 through
VR-4A-18.

Resolves: SY-1, SY-2, SY-3, SY-24, SY-25, SY-26, SY-27, SY-28, SY-29,
SY-30, SY-31, SY-32, SY-33, SY-34"
```

---

## Commit 5 — P2 Batch Fixes

**Finding count:** 13 P2 findings (SY-35 through SY-47).

**Files:**
- Modify: `README.md` — §Authority Model (line 27)
- Modify: `enforcement.md` — §Enforcement Exceptions (lines 135-141), §Hooks table (line 16), §Autonomy Model (lines 143-149), §Inter-Hook Runtime State (line 112)
- Modify: `types.md` — §Compatibility Rules (lines 411-419), §LedgerEntry (line 353), §EnvelopeHeader (line 65), §LedgerEntry (line 347), §RecordRef (lines 16-24)
- Modify: `operations.md` — §Promote, §Recovery Manifest
- Modify: `storage-and-indexing.md` — §Key Storage Decisions

### Task 5.1: README precedence summary (SY-35)

- [ ] **Step 1:** In README.md (line 27), expand the behavior_contract precedence:

Replace:
```
`operations` wins over `skill-contract` for `behavior_contract` claims.
```

With:
```
`operations` > `skill-contract` > `foundation` > `decisions` for `behavior_contract` claims.
```

### Task 5.2: Circular authority reference (SY-36)

- [ ] **Step 1:** In enforcement.md §Enforcement Exceptions (line 141), move the substantive exception definition to clarify direction. Replace the sequencing note:

```markdown
**Sequencing:** The authoritative exception definition lives in [foundations.md §Permitted Exceptions](foundations.md#permitted-exceptions). This table references it for enforcement-level discoverability.
```

### Task 5.3: Broken compatibility table (SY-37)

- [ ] **Step 1:** In types.md §Compatibility Rules (lines 411-419), the table is split by a prose paragraph. Current state: line 411-413 = table header + first row (Envelope protocol), line 415 = `VERSION_UNSUPPORTED` prose paragraph, lines 416-419 = remaining rows (Record provenance, Ledger format, Knowledge entry, Promotion state).

Fix: move lines 416-419 (the remaining table rows) immediately after line 413, making all five version space rows contiguous in one markdown table. Then move the `VERSION_UNSUPPORTED` paragraph to appear after the completed table (after the Promotion state row). The table must have 5 data rows plus the header — all contiguous with no interrupting prose.

### Task 5.4: Hook scope inconsistency (SY-38)

- [ ] **Step 1:** In enforcement.md §Hooks table (line 16), add path qualification to engram_register:

Replace:
```
| `engram_register` | PostToolUse (Write, Edit) | 3rd | Ledger append |
```

With:
```
| `engram_register` | PostToolUse (Write, Edit) on protected paths | 3rd | Ledger append |
```

### Task 5.5: operation_id format (SY-39)

- [ ] **Step 1:** In types.md §LedgerEntry (after line 353), add:

```markdown
**`operation_id` format:** UUIDv4 generated by the orchestrator (e.g., `/save`) at flow start and passed to all sub-engine calls. Engines must use the provided `operation_id` — they must not self-generate one. `None` when not part of an orchestrated flow.
```

### Task 5.6: Manifest schema_version (SY-40)

- [ ] **Step 1:** In operations.md, find the `save_recovery.json` JSON block (§Recovery Manifest). Add `"schema_version": "1.0"` as the first field inside the JSON object. In delivery.md §Step 4a, find the `migration_report.json` inline JSON block (around line 206). Add `"schema_version": "1.0"` as the first field inside the JSON object.

### Task 5.7: Timestamp UTC enforcement (SY-41)

- [ ] **Step 1:** In types.md, after §Write Semantics (line 389, the last paragraph in the LedgerEntry section), add:

```markdown
**Timestamp validation:** Producers must emit `LedgerEntry.ts` and `EnvelopeHeader.emitted_at` with UTC offset (`Z` or `+00:00`). Parsers encountering a timestamp without UTC offset should treat it as UTC (not local time) and log a warning.
```

### Task 5.8: RecordRef deferral annotation (SY-42)

- [ ] **Step 1:** In types.md §RecordRef (line 18), expand the inline comment:

Replace:
```python
    subsystem: str        # "context" | "work" | "knowledge"
```

With:
```python
    subsystem: str        # "context" | "work" | "knowledge" — enforced at construction, not schema-level Literal (deferred per decisions.md)
```

### Task 5.9: Policy-based claim (SY-43)

- [ ] **Step 1:** In enforcement.md §Protected-Path Enforcement (line 31), qualify the claim:

Replace:
```
Policy-based, not tool-specific.
```

With:
```
Policy-based enforcement covering all currently supported write tools (Write, Edit, Bash). Adding new write-capable platform tools requires updating `engram_guard` hook registration.
```

### Task 5.10: Knowledge autonomy mode (SY-44)

- [ ] **Step 1:** In enforcement.md §Autonomy Model (line 149), replace the informal Knowledge staging description:

Replace:
```
| Knowledge staging | Staging inbox cap + idempotency | Dedup prevents repeated staging; cumulative cap limits volume |
```

With:
```
| Knowledge staging | `gated` | User reviews via `/curate` before publication. `/distill` auto-stages without user confirmation; `/learn` publishes directly. Staging inbox cap + idempotency bound autonomous volume. |
```

### Task 5.11: Check ordering (SY-45)

- [ ] **Step 1:** In enforcement.md §Trust Injection Step 2, after the `collect_trust_triple_errors()` contract reference (see Task 1.3), add:

```markdown
**Check ordering:** Each mutating entrypoint must check `.engram-id` existence before invoking `collect_trust_triple_errors()`. If `.engram-id` is absent, return the initialization error immediately without trust triple validation. This ensures users see "Engram not initialized" rather than a confusing trust triple rejection.
```

### Task 5.12: /search grouping assertion (SY-46)

- [ ] **Step 1:** In delivery.md §Cross-Cutting Verification, expand the /search grouping test:

Replace:
```
Multi-subsystem query, assert contiguous grouping
```

With:
```
Multi-subsystem query, assert contiguous grouping: for each adjacent pair `(entries[i], entries[i+1])` where subsystems differ, assert `entries[i+1].ref.subsystem` does not appear in `entries[0..i-1]`
```

### Task 5.13: RecordRef round-trip test (SY-47)

- [ ] **Step 1:** In delivery.md §Step 0a Required Verification, add:

```markdown
- RecordRef serialization round-trip (VR-0A-12): for each subsystem, assert `RecordRef.from_str(ref.to_str(), ref.repo_id) == ref`. Edge case: `record_id` containing hyphens. (SY-47)
```

- [ ] **Step 2:** Commit.

```bash
git add docs/superpowers/specs/engram/README.md docs/superpowers/specs/engram/enforcement.md docs/superpowers/specs/engram/types.md docs/superpowers/specs/engram/operations.md docs/superpowers/specs/engram/delivery.md docs/superpowers/specs/engram/storage-and-indexing.md
git commit -m "fix(spec): remediate 13 P2 findings (SY-35 through SY-47)

README precedence, broken table, hook scope, operation_id format, manifest
versions, timestamp UTC, deferral annotations, policy claim qualification,
Knowledge autonomy mode, check ordering, search grouping, round-trip test.

Resolves: SY-35, SY-36, SY-37, SY-38, SY-39, SY-40, SY-41, SY-42, SY-43,
SY-44, SY-45, SY-46, SY-47"
```

---

## Verification Checklist

After all 5 commits, run these cross-file consistency checks:

- [ ] All VR IDs in delivery.md are globally unique — `grep -oE 'VR-[0-9A-Z]+-[0-9]+' delivery.md | sort | uniq -d` returns empty
- [ ] All internal markdown anchors resolve — `grep -oE '\[.*?\]\(([^)]+)\)' *.md` cross-checked against headings
- [ ] enforcement.md contains no `implementation_plan` or `architecture_rule` claims (only cross-references)
- [ ] `collect_trust_triple_errors` is referenced consistently across enforcement.md, delivery.md, types.md
- [ ] No remaining "session diagnostic channel" references without a link to the defined section
- [ ] `from_str(s, repo_id)` signature is consistent between types.md definition and all call sites
- [ ] `.archive/` appears in both the storage layout diagram and the TTL table
- [ ] Smoke test observable output table in delivery.md has exactly 13 rows (one per skill)

## Parked (Not In This Plan)

- **SP-8 / SY-42:** RecordRef Literal type constraints — deliberately deferred per decisions.md
- **VR-4 / SY-34 CI bound:** Exact CI timeout multiplier — best determined during implementation when CI infra is known
- **IE-6 / SY-44 Knowledge autonomy design:** The P2 fix (Task 5.10) adds a formal mode name; deeper autonomy semantics (should `/distill` have a gated mode?) is a future design discussion
