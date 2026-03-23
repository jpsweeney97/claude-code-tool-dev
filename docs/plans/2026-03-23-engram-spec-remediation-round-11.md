# Engram Spec Remediation Plan — Round 11

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate 5 P0 and 38 P1 findings from engram spec review round 11 across 8 spec files.

**Architecture:** Three commits ordered by priority: (1) P0 fixes across all affected files, (2) P1 enforcement + contract clarifications, (3) P1 verification plan refinements + supporting files. Each commit produces a self-consistent spec state. 9 P2 findings deferred (4 trivial P2s bundled with related P0/P1 fixes).

**Tech Stack:** Markdown specification files in `docs/superpowers/specs/engram/`

---

**Source:** `.review-workspace/synthesis/report.md` (6-reviewer team, 2026-03-23)
**Scope:** 56 canonical findings (5 P0, 38 P1, 13 P2). Remediating 43 P0+P1 + 4 bundled P2.
**Spec:** `docs/superpowers/specs/engram/` (10 files, ~1350 lines)
**Dominant patterns:** guard algorithm underspecification (Cluster C, 7 findings), enforcement exception authority model (Cluster A, 3 findings), verification plan feasibility gaps (10 findings)

## Design Decisions

Five behavioral gaps require design decisions before editing.

### DD-1: Enforcement Exception Boundary Rule (SY-2 + SY-46)

**Decision:** Add a boundary rule `on_change_to: [foundation], review_authorities: [enforcement]` to spec.yaml, and add a comment on the `enforcement_mechanism` claim_precedence entry noting the exception subdomain inversion.

**Rationale:** The authority inversion (foundations.md controls exception creation; enforcement.md implements them) is intentional and documented in prose. The fix captures it in the machine-readable authority model without changing the design. A boundary rule makes the dependency discoverable by tooling.

### DD-2: Unified Engine Entrypoint Check Ordering (SY-14)

**Decision:** Add a numbered check ordering list to enforcement.md §Check Ordering that covers all 5 checks in sequence: (1) `.engram-id` existence, (2) payload containment, (3) payload file existence, (4) trust triple validation, (5) origin matching.

**Rationale:** The current spec has two partial ordering rules in different sections. Unifying them eliminates the ambiguity CE-5 identified. Containment (defense-in-depth) runs after `.engram-id` because the `.engram-id` check produces a more helpful error for the common case (uninitialized repo).

### DD-3: Branch 3 Diagnostic Message Format (SY-28)

**Decision:** Specify: `"engram_guard: write to protected path {canonical_path} blocked. Path class: {path_class}. Use engine entrypoints for {path_class} writes."`

**Rationale:** All other guard branches have exact diagnostic strings. Branch 3 is the most user-visible block (it fires when skills try to Write/Edit to `engram/work/` or `engram/knowledge/`). The message includes path_class so the user knows which engine to use.

### DD-4: Staging-Meta Schema Version (SY-20)

**Decision:** Add `"meta_version": "1.0"` to staging-meta JSON fields. Add a 7th entry to the version spaces table: "Knowledge staging format" at `"1.0"` with same-major tolerance.

**Rationale:** Staging-meta is the only persisted format without version awareness. While staging files are ephemeral, `/curate` reads them — a format change without versioning would break the reader silently. The cost of adding the field is minimal.

### DD-5: VR-NEW-7 Optional vs Required (SY-43)

**Decision:** Promote VR-NEW-7 from optional to required at the Step 2a exit gate. Add environment qualifier: "Requires two independent git worktrees from the same repo."

**Rationale:** The normative claim in types.md ("git's line-based merge handles append-only files well") needs a verification path. An optional test for a normative claim is a hope, not a guarantee. The environment qualifier makes CI feasibility explicit.

---

## Commit 1: P0 Fixes

5 P0 findings + 2 bundled P2s from Cluster A.

### Task 1: operations.md — Expand Branch D (SY-3)

**Files:**
- Modify: `docs/superpowers/specs/engram/operations.md`

- [ ] **Step 1: Read the Branch D definition**

Read operations.md lines 153–157 (Branch D definition in the promote state machine).

- [ ] **Step 2: Expand Branch D to cover lesson_id mismatch**

In operations.md, find the Branch D definition:
```
Branch D (promote-meta present, meta_version unrecognized or missing):
```

Replace with:
```
Branch D (promote-meta present, AND any of: meta_version unrecognized or missing, OR lesson_id does not match the immediately preceding lesson-meta.lesson_id):
```

Update the Branch D exclusion text to include both cases:
```
Exclude from candidate list. Surface warning:
- Missing/unrecognized meta_version: "Lesson <lesson_id> has unreadable promote-meta (missing or unrecognized meta_version). Run migration before re-promoting."
- lesson_id mismatch: "Lesson <lesson_id> has corrupt promote-meta (lesson_id mismatch with lesson-meta). Run migration before re-promoting."
```

- [ ] **Step 3: Verify the fix**

Confirm Branch D now covers both meta_version issues AND lesson_id cross-validation failures per types.md §promote-meta requirement.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/engram/operations.md
git commit -m "fix(spec): expand Branch D to cover lesson_id mismatch (SY-3)"
```

### Task 2: storage-and-indexing.md — Same-Major Tolerance (SY-4)

**Files:**
- Modify: `docs/superpowers/specs/engram/storage-and-indexing.md`

- [ ] **Step 1: Read the RecordMeta Field Mapping section**

Read storage-and-indexing.md lines 92–120 (RecordMeta Field Mapping per Subsystem).

- [ ] **Step 2: Add same-major tolerance rule for Context and Work readers**

After the field mapping table (around line 120, before "**Staged entry IndexEntry population**"), add:

```markdown
**Same-major version tolerance (Context and Work readers):** Context and Work readers apply the same `RecordMeta.schema_version` tolerance as Knowledge readers: parse `schema_version` as `<major>.<minor>`, accept entries with the same major version, skip entries with a different major version with a per-entry warning in `QueryDiagnostics.warnings`. Sentinel values (`"staged"`, `"0.0"`) are exempt from `<major>.<minor>` parsing — route to sentinel-specific handling instead. See [types.md §Compatibility Rules](types.md#compatibility-rules) for the governing contract and [types.md §Sentinel Exemption](types.md#compatibility-rules) for sentinel handling.
```

- [ ] **Step 3: Verify**

Confirm VR-NEW-9 now has normative backing — the behavior it tests (Context/Work reader skipping `schema_version: "2.0"`) is specified here.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/engram/storage-and-indexing.md
git commit -m "fix(spec): add same-major tolerance rule for Context/Work readers (SY-4)"
```

### Task 3: enforcement.md — Branch 2 Capability Gate (SY-6 + SY-26)

**Files:**
- Modify: `docs/superpowers/specs/engram/enforcement.md`

- [ ] **Step 1: Read the degraded-mode section**

Read enforcement.md lines 290–310 (§Inter-Hook Runtime State, degraded-mode bullets).

- [ ] **Step 2: Fix branch 2 degraded-mode bullet (SY-6)**

Find the branch 2 degraded-mode bullet:
```
- Branch 2: `"engram_guard degraded: worktree_id unavailable — {error}. Direct-write path authorization blocked."`
```

Replace with:
```
- Branch 2 (only when `context_direct_write_authorization` capability is active): `"engram_guard degraded: worktree_id unavailable — {error}. Direct-write path authorization blocked."` When `context_direct_write_authorization` is inactive, branch 2 is a no-op regardless of degraded-mode state — no blocking, no diagnostic.
```

- [ ] **Step 3: Clarify branch 2 fall-through diagnostic scope (SY-26)**

Find the guard algorithm note about branch 2 fall-through:
```
No diagnostic is emitted when Step 2 fails — silent fall-through to Step 3 is correct behavior for general writes.
```

Replace with:
```
No path-authorization diagnostic is emitted when Step 2 fails the Context-ownership check — silent fall-through to Step 3 is correct behavior for general writes. Git identity errors (from `identity.get_worktree_id()`) are always logged to stderr regardless of branch 2 outcome — these are infrastructure diagnostics, not path-authorization diagnostics.
```

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/engram/enforcement.md
git commit -m "fix(spec): branch 2 degraded-mode capability gate + diagnostic scope (SY-6 + SY-26)"
```

### Task 4: spec.yaml — Enforcement Exception Boundary Rule (SY-2 + SY-46)

**Files:**
- Modify: `docs/superpowers/specs/engram/spec.yaml`

- [ ] **Step 1: Read spec.yaml boundary_rules**

Read spec.yaml lines 51–61.

- [ ] **Step 2: Add foundation→enforcement boundary rule**

After the existing 3 boundary rules, add:

```yaml
  - on_change_to: [foundation]
    review_authorities: [enforcement]
    reason: Permitted exception additions/removals in foundations.md must be reflected in enforcement.md's enforcement exceptions table.
```

- [ ] **Step 3: Add enforcement exception precedence annotation**

In the `claim_precedence` section, after `enforcement_mechanism: [enforcement, foundation, operations, decisions]`, add a YAML comment:

```yaml
    # Exception subdomain: for enforcement *exception creation*, foundation is
    # the gatekeeper — see foundations.md §Adding New Exceptions. enforcement.md
    # owns enforcement mechanisms but cannot unilaterally expand the exception set.
```

- [ ] **Step 4: Update README.md boundary rules reference (SY-8 bundled)**

In README.md, update the precedence summary (line 27) to include `operations` as tertiary:

Replace:
```
`enforcement` wins for `enforcement_mechanism` claims, with `foundation` as secondary authority — see boundary rules in spec.yaml.
```
With:
```
`enforcement` wins for `enforcement_mechanism` claims; `foundation` is secondary, `operations` tertiary — see spec.yaml for full precedence and boundary rules.
```

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/engram/spec.yaml docs/superpowers/specs/engram/README.md
git commit -m "fix(spec): enforcement exception boundary rule + README precedence (SY-2 + SY-46 + SY-8)"
```

### Task 5: delivery.md — Cross-Repo Mitigation VR Test (SY-5)

**Files:**
- Modify: `docs/superpowers/specs/engram/delivery.md`

- [ ] **Step 1: Read VR-4A-19**

Read delivery.md lines 331–346 (VR-4A-19 context direct-write path authorization tests).

- [ ] **Step 2: Add companion triage-detection test**

After VR-4A-19 case (j), add a new VR test:

```markdown
- **VR-4A-43 (cross-repo Context write mitigation):** Write a snapshot to `Path(os.path.expanduser("~")) / ".claude" / "engram" / <different_repo_id> / "snapshots" / "test.md"` with missing `session_id` in frontmatter. Run `/triage`. Assert: `provenance_not_established` anomaly surfaced for that snapshot. This verifies the detection mitigation for the "Context any-source write authorization" named risk (decisions.md). Companion to VR-4A-19(c) which verifies the authorization gap.
```

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/engram/delivery.md
git commit -m "fix(spec): add VR-4A-43 cross-repo write mitigation test (SY-5)"
```

---

## Commit 2: P1 Enforcement + Contract Clarifications

~22 P1 findings across enforcement.md, types.md, and operations.md.

### Task 6: enforcement.md — Guard Algorithm Clarifications (SY-14 + SY-34 + SY-28)

**Files:**
- Modify: `docs/superpowers/specs/engram/enforcement.md`

- [ ] **Step 1: Add unified check ordering (SY-14)**

Replace the current §Check Ordering section (lines 236–241) with:

```markdown
#### Check Ordering

Each mutating Work and Knowledge engine entrypoint must execute checks in this order. A failure at any step short-circuits — do not proceed to later steps.

| Order | Check | On Failure |
|-------|-------|-----------|
| 1 | `.engram-id` existence | Return `"Engram not initialized: run 'engram init' to bootstrap."` |
| 2 | Payload containment (defense-in-depth) | Reject: `"Trust triple rejected: payload path outside containment boundary: {path}"` |
| 3 | Payload file existence and readability | Reject: `"trust triple not injected: payload file missing or unreadable at {path}"` |
| 4 | Trust triple validation (`collect_trust_triple_errors()`) | Reject with joined error strings |
| 5 | Origin matching (`validate_origin_match()`) | Reject: `"hook_request_origin: expected {expected!r} for this entrypoint, got {actual!r}"` |

Steps 1 precedes 2 so users see "Engram not initialized" rather than a confusing containment error. Steps 2–3 validate the payload delivery. Steps 4–5 validate the payload content. Context engine scripts must NOT invoke any of steps 2–5 — they use [direct-write path authorization](#direct-write-path-authorization).
```

- [ ] **Step 2: Make canonicalization order explicit (SY-34)**

In §Protected-Path Enforcement, find the canonicalization paragraph. Replace:
```
Paths canonicalized before matching: expand `~` (via `os.path.expanduser()` or equivalent), then resolve symlinks, collapse `..`, normalize to absolute (`os.path.realpath()` after expansion).
```
With:
```
**Canonicalization order** (both steps required, in this order): (1) `os.path.expanduser()` — expand `~` to the user's home directory, (2) `os.path.realpath()` — resolve symlinks, collapse `..`, normalize to absolute. Calling `realpath` before `expanduser` is incorrect — `realpath` does not resolve `~`, causing all home-relative paths to fail canonicalization silently (no error, wrong branch taken).
```

- [ ] **Step 3: Add branch 3 diagnostic format (SY-28)**

In §Guard Decision Algorithm, find branch 3:
```
3. If tool_name in {Write, Edit} AND path in protected-path table:
   → Block with path-class diagnostic
```
Replace with:
```
3. If tool_name in {Write, Edit} AND path in protected-path table:
   → Block (exit code 2) with diagnostic:
     "engram_guard: write to protected path {canonical_path} blocked.
      Path class: {path_class}. Use engine entrypoints for {path_class} writes."
```

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/engram/enforcement.md
git commit -m "fix(spec): unified check ordering + canonicalization order + branch 3 diagnostic (SY-14 + SY-34 + SY-28)"
```

### Task 7: enforcement.md — Hooks, Config, and Diagnostics (SY-25 + SY-24 + SY-7 + SY-30 + SY-27 + SY-15 + SY-32 + SY-33 + SY-54)

**Files:**
- Modify: `docs/superpowers/specs/engram/enforcement.md`

- [ ] **Step 1: Add .diag cleanup to SessionStart table (SY-25)**

In §SessionStart Hook table, add a new row after "Clean orphan payload files":

```markdown
| Clean old `.diag` files (>90d by filename session_id timestamp) | Max 20 files | Fail-open |
```

Update the .diag TTL section to reference this: "Cleaned up by `engram_session` at SessionStart (>90 days, max 20 per session)."

- [ ] **Step 2: Add structural exclusion note to protected-path table (SY-24)**

After the protected-path table, add:

```markdown
**Structural exclusions:** Rows marked "Register Fires? No" are by-design exclusions, not gaps. `knowledge_staging` writes are Bash-mediated engine invocations — routing them through Write/Edit tools to obtain ledger coverage would bypass trust injection. `context_private` writes are authorized via branch 2 (direct-write path) — `engram_register` observes Write/Edit tool calls but branch 2 paths are authorized, not audited.
```

- [ ] **Step 3: Clarify guard capability authority split (SY-7)**

In §Guard Capability Rollout, update the authoritativeness note:

Replace:
```
This table is the canonical source for guard capability activation (`enforcement_mechanism` authority).
```
With:
```
This table is the canonical source for guard capability behavioral contracts (`enforcement_mechanism` authority). delivery.md §Build Sequence owns the activation schedule (`implementation_plan` authority) — which step activates each capability.
```

- [ ] **Step 4: Add orphan payload overflow warning (SY-30)**

In §SessionStart Hook, after the orphan payload cleanup row, add:

```markdown
When orphan payload count at cleanup time exceeds 20, log: `"engram_session: orphan payload accumulation detected ({count} files, cleaned 20). Check for recurring engine crashes."` This surfaces the accumulation pattern without blocking session start.
```

- [ ] **Step 5: Add payload root cause distinguishing note (SY-27)**

In §Payload File Contract, "Missing at consumption" row, add:

```markdown
The uniform error message is acceptable for user-facing output. The engine should also log distinguishing context to stderr: whether the path was never present (guard-blocked retry) vs. present but zero-bytes/corrupt (partial fsync), so operators can distinguish failure modes in logs.
```

- [ ] **Step 6: Fix Step 3a cross-reference for Knowledge trust triple (SY-15)**

In enforcement.md line 233, find:
```
delivery.md Step 3a must include a verification step asserting collect_trust_triple_errors() is invoked at every documented Work and Knowledge mutating entrypoint
```
Replace with:
```
delivery.md must include verification steps asserting collect_trust_triple_errors() is invoked at every documented mutating entrypoint: Knowledge entrypoints at Step 2a (VR-2A-NEW-1), Work entrypoints at Step 3a (VR-3A-9)
```

- [ ] **Step 7: Add enforcement exceptions forward-pointer (SY-54)**

In §Enforcement Exceptions, after "The canonical source is foundations.md", add:

```markdown
To add a new exception: update [foundations.md §Permitted Exceptions](foundations.md#permitted-exceptions) first, then add a reference row to this table. See [foundations.md §Adding New Exceptions](foundations.md#adding-new-exceptions) for the sequencing rule.
```

- [ ] **Step 8: Add config value documentation notes (SY-32 + SY-33)**

In §Staging Inbox Cap, after the `>= 1` validation, add:
```markdown
No upper bound is enforced in v1 — operators are trusted to configure sensibly. See [decisions.md §Deferred Decisions](decisions.md#deferred-decisions).
```

In §Autonomy Model counter mechanism, after the counter description, add:
```markdown
When the counter includes entries with missing `auto_created` fields (treated as `True` per [VR-3A-24](delivery.md#step-3a-activate)), log: `"engram: {count} audit entries with missing auto_created field counted toward cap. Inspect .audit/<session_id>.jsonl for corruption."` This makes corrupt-entry cap consumption visible.
```

- [ ] **Step 9: Commit**

```bash
git add docs/superpowers/specs/engram/enforcement.md
git commit -m "fix(spec): hooks + config + diagnostics clarifications (SY-25 + SY-24 + SY-7 + SY-30 + SY-27 + SY-15 + SY-54 + SY-32 + SY-33)"
```

### Task 8: types.md — Schema Contract Clarifications (SY-19 + SY-20 + SY-23 + SY-16)

**Files:**
- Modify: `docs/superpowers/specs/engram/types.md`

- [ ] **Step 1: Add LedgerEntry.record_ref type note (SY-19)**

On the `record_ref: str | None` field in the LedgerEntry dataclass, add a comment:

```python
    record_ref: str | None        # RecordRef canonical serialization; non-null required for snapshot_written (see Event Vocabulary per-event-type rules)
```

- [ ] **Step 2: Add staging-meta schema_version (SY-20)**

In §Staging File Format, add `meta_version` to the staging-meta field list:

```markdown
The staging-meta JSON includes: `meta_version` (`"1.0"`), `content`, `durability`, `source_section`, `content_sha256`, `source_ref`, and `staged_at`.
```

In §Version Spaces table, add a 7th row:

```markdown
| Knowledge staging format | `staging-meta.meta_version` | Knowledge staging files | `"1.0"` |
```

In §Compatibility Rules table, add:

```markdown
| Knowledge staging format | **Same-major tolerance.** `/curate` readers accept staging-meta with same major version. Unknown fields ignored. | Writers emit the version they were built for. |
```

- [ ] **Step 3: Add staging-meta prohibited fields note (SY-23)**

In §Staging File Format, directly after the field enumeration, add:

```markdown
**Prohibited fields:** `DistillEnvelope.header.idempotency_key` MUST NOT be included in staging-meta — see [§Idempotency Enforcement Per Envelope Type](#idempotency-enforcement-per-envelope-type). Its omission is an active constraint: inclusion would make staging-meta a de facto dedup key, violating the trace-only contract for DistillEnvelope idempotency.
```

- [ ] **Step 4: Clarify PromoteEnvelope idempotency label (SY-16)**

In §Idempotency Enforcement Per Envelope Type table, change the PromoteEnvelope row:

Replace:
```
| `PromoteEnvelope` | **Enforced** | State-machine re-entry detection...
```
With:
```
| `PromoteEnvelope` | **Enforced (state-machine, not idempotency_key)** | State-machine re-entry detection...
```

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/engram/types.md
git commit -m "fix(spec): schema contract clarifications — record_ref, staging-meta version, prohibited fields, idempotency label (SY-19 + SY-20 + SY-23 + SY-16)"
```

### Task 9: storage-and-indexing.md + operations.md — Contract Fixes (SY-18 + SY-22 + SY-1 + SY-9 + SY-10 + SY-11 + SY-21 + SY-17)

**Files:**
- Modify: `docs/superpowers/specs/engram/storage-and-indexing.md`
- Modify: `docs/superpowers/specs/engram/operations.md`
- Modify: `docs/superpowers/specs/engram/enforcement.md`

- [ ] **Step 1: Resolve snippet contradiction (SY-18)**

In storage-and-indexing.md, find the normative note (line 136):
```
Reader-extracted (not first-N-chars).
```
Replace with:
```
Reader-extracted. Each subsystem reader owns its extraction logic — the staged entry table and published entry readers each define their own approach. Capped at 200 characters.
```

- [ ] **Step 2: Add word-boundary truncation to IndexEntry.snippet (SY-1, bundled P2)**

In the IndexEntry dataclass, update the snippet comment:
```python
    snippet: str                  # Reader-extracted preview, max 200 chars, truncated at word boundary. Display-only.
```

- [ ] **Step 3: Add Knowledge worktree_id join gap note (SY-22)**

In storage-and-indexing.md §RecordMeta Field Mapping, after "Fields marked N/A populate as `None` in `RecordMeta`", add:

```markdown
**Knowledge join gap:** Knowledge `RecordMeta.worktree_id` and `session_id` are `None` (shared root, no worktree/session scope). Queries filtering by `worktree_id` will exclude Knowledge entries. `/timeline` and `/search` correlate Knowledge records by `created_at` and content, not `worktree_id`. This is by design — Knowledge is project-scoped.
```

- [ ] **Step 4: Replace operations.md enforcement assertions with cross-references (SY-9)**

In operations.md §Core Rules, find lines 14–15 (trust triple precondition). Replace with:

```markdown
- **Precondition:** All mutating Work and Knowledge engine entrypoints require trust triple validation before making state changes. See [enforcement.md §Trust Injection](enforcement.md#trust-injection) for the enforcement mandate — which validator to call, check ordering, per-entrypoint origin matching, and rejection behavior.
```

Remove the redundant normative assertion ("Operations with missing or incomplete triples are rejected") — let enforcement.md own that claim.

- [ ] **Step 5: Clarify Branch A user confirmation (SY-11)**

In operations.md §Promote, Branch A, find:
```
User confirmation is implicit in lesson selection — the user chose this lesson for promotion. No separate approval prompt.
```
Replace with:
```
User confirmation is implicit in lesson selection — the user chose this lesson for promotion. No separate approval prompt. This is a skill-level behavioral contract (no enforcement mechanism) — the skill MUST display the promotion plan before proceeding to Step 2.
```

- [ ] **Step 6: Add PromoteEnvelope Step 1 equality check (SY-21)**

In operations.md §Promote Step 1, after "Returns promotion plan with target_section", add:

```markdown
Step 1 MUST verify `PromoteEnvelope.content_sha256 == lesson-meta.content_sha256` when no user edit is detected. If they diverge and the lesson content has not been modified since publication, this indicates a byte-range extraction bug — surface a diagnostic error and abort the promote. See [types.md §PromoteEnvelope](types.md#promoteenvelope--knowledge-to-claudemd-intent-record) for the equality constraint.
```

- [ ] **Step 7: Move recovery manifest rationale to appropriate authority (SY-10)**

In operations.md, find the parenthetical note about `migration_report.json` vs `save_recovery.json` (around line 298):
```
(Note: migration_report.json includes schema_version: "1.0" despite also being an operational aid — it may outlive its creating step...
```
Move this rationale to delivery.md §Step 4a, adjacent to the `migration_report.json` schema definition (around line 267-284). In operations.md, replace with a brief cross-reference:
```
(Note: `migration_report.json` includes `schema_version` unlike `save_recovery.json` — see [delivery.md §Context Cutover](delivery.md#step-4-context-cutover) for the design rationale.)
```

- [ ] **Step 8: Fix broken anchor enforcement.md → delivery.md (SY-17)**

In enforcement.md, find (around line 324):
```
The [intra-step ordering requirement](delivery.md#step-4a-context-subsystem)
```
Replace with:
```
The [intra-step ordering requirement](delivery.md#step-4a--activate)
```

- [ ] **Step 9: Commit**

```bash
git add docs/superpowers/specs/engram/storage-and-indexing.md docs/superpowers/specs/engram/operations.md docs/superpowers/specs/engram/enforcement.md
git commit -m "fix(spec): snippet contradiction + Knowledge join gap + operations cross-refs + promote checks + broken anchor (SY-18 + SY-22 + SY-1 + SY-9 + SY-10 + SY-11 + SY-21 + SY-17)"
```

---

## Commit 3: P1 Verification Plan Refinements

~15 P1 findings in delivery.md + decisions.md.

### Task 10: delivery.md — New VR Tests (SY-13 + SY-12 + SY-31)

**Files:**
- Modify: `docs/superpowers/specs/engram/delivery.md`

- [ ] **Step 1: Add DistillEnvelope idempotency_key prohibition VR (SY-13)**

In Step 2a Required Verification, add:

```markdown
- **VR-2A-NEW-10 (DistillEnvelope idempotency_key prohibition):** After staging a lesson via `/distill`, read the staging file's `staging-meta` JSON. Assert: no `idempotency_key` field is present. Assert: the Knowledge engine's staging write path does NOT check `DistillEnvelope.idempotency_key` against any stored key (instrument or mock the check to raise if called). See [types.md §Idempotency Enforcement Per Envelope Type](types.md#idempotency-enforcement-per-envelope-type).
```

- [ ] **Step 2: Add explicit validate_origin_match call site sentence (SY-12)**

In enforcement.md §Origin-Matching by Entrypoint (or delivery.md §Step 2a if more appropriate), add after the per-entrypoint origin table:

```markdown
**Explicit call sites:** The Knowledge engine publish entrypoint (shared by `/learn` and `/curate`) must call `validate_origin_match("user", actual)`. The staging write entrypoint (`/distill`) must call `validate_origin_match("agent", actual)`. The promote-meta write entrypoint must call `validate_origin_match("user", actual)`.
```

- [ ] **Step 3: Add guard pre-activation boundary test (SY-31)**

In Step 1 Required Verification, add:

```markdown
- **VR-1-5 (guard inactive at Step 1):** Invoke `engram_guard` with a valid Knowledge engine Bash call during Step 1 (before `engine_trust_injection` capability activates at Step 2a). Assert: no payload file is created (branch 1 is no-op). This verifies the capability-inactive state is truly inactive, preventing a default-active bug from silently injecting trust payloads before the guard is validated.
```

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/engram/delivery.md docs/superpowers/specs/engram/enforcement.md
git commit -m "fix(spec): new VR tests — DistillEnvelope prohibition + origin call sites + guard pre-activation (SY-13 + SY-12 + SY-31)"
```

### Task 11: delivery.md — VR Test Clarifications (SY-42 + SY-43 + SY-41 + SY-39 + SY-36 + SY-37 + SY-38 + SY-40 + SY-44 + SY-35 + SY-48)

**Files:**
- Modify: `docs/superpowers/specs/engram/delivery.md`

- [ ] **Step 1: Clarify VR-2A-3 flock test needs subprocess (SY-42)**

In VR-2A-3, find "hold the lock externally". Add parenthetical:
```
(via a subprocess — `fcntl.flock` locks are per-open-file-description; threads within the same process share file descriptors and cannot block each other)
```

- [ ] **Step 2: Promote VR-NEW-7 from optional to required (SY-43)**

Find VR-NEW-7. Remove "(Optional integration test.)" and replace with:
```
Required at Step 2a exit gate. Environment: requires two independent git worktrees from the same repo.
```

- [ ] **Step 3: Add VR-3A-8 test fixture resolution (SY-41)**

In VR-3A-8, add:
```
`<engram_scripts_dir>` in the test context: derive from the test's known plugin root path, or patch `engram_guard.__file__` to point to a fixture directory containing a known `scripts/engine_work.py`.
```

- [ ] **Step 4: Clarify VR-4A-3 mock test behavioral assertions (SY-39)**

In VR-4A-3, after "verified in standard CI via a mock filesystem", add:
```
The mock behavioral test must verify: (1) per-file abort logic fires (mock one file's cleanup to take >5ms, assert remaining files in that category are skipped), (2) elapsed-time guard fires (mock elapsed > 450ms after first optional operation, assert remaining operations skipped). Without these assertions, the mock test verifies nothing about timing behavior.
```

- [ ] **Step 5: Add VR-0B-1(e) exit code (SY-36)**

In VR-0B-1(e), after "assert the command refuses", add:
```
Exit code: 1 (user error). The warning text must match exactly: `"this will change repo_id; use --force --yes to confirm"`.
```

- [ ] **Step 6: Add engram init smoke test isolation (SY-37)**

In the minimal observable output table for `engram init`, change to:
```
`engram init` | Run in isolated temp directory (no existing `.engram-id`). Assert: `.engram-id` created, valid UUIDv4 content, exit code 0. If isolation is infeasible, assert "created or already initialized" with valid UUIDv4 in file.
```

- [ ] **Step 7: Add VR-3A-9 architecture documentation note (SY-38)**

In VR-3A-9, after the "if no single-function entrypoints exist" clause, add:
```
If method (a) is never used (all entrypoints are class-based), the test file must document this decision: "All 6 mutating entrypoints use class-based architecture — method (a) AST scan not applicable."
```

- [ ] **Step 8: Clarify VR-5-5 post-cleanup skill set (SY-40)**

In VR-5-5, replace current text with:
```
All skills in the progressive activation manifest pass their smoke test (final progressive gate). The Step 5 active skill set equals the Step 4a set (13 skills — no new skills activate at Step 5). VR-5-5 verifies the Step 4a skill set remains functional after cleanup operations.
```

- [ ] **Step 9: Add VR-4A-32 degradation scan-count case (SY-44)**

In VR-4A-32, add:
```
Degradation case: set private root to non-existent path. Assert: `scan("private")` is still called exactly once per reader (with reader returning `[]`). Assert: `diagnostics.degraded_roots == ["private"]`.
```

- [ ] **Step 10: Strengthen VR-4A-34 schema_version assertion (SY-35)**

In VR-4A-34, change the schema_version assertion to:
```
Assert: `"schema_version" not in recovery_data` (explicit absence check, not just non-assertion).
```

- [ ] **Step 11: Fix stale IE-14 label (SY-48, bundled P2)**

In VR-4A-19(j), replace `[IE-14 canonicalization](enforcement.md#protected-path-enforcement)` with `[path canonicalization](enforcement.md#protected-path-enforcement)`.

- [ ] **Step 12: Commit**

```bash
git add docs/superpowers/specs/engram/delivery.md
git commit -m "fix(spec): VR test clarifications — subprocess, optional→required, test fixtures, timing (SY-42 + SY-43 + SY-41 + SY-39 + SY-36 + SY-37 + SY-38 + SY-40 + SY-44 + SY-35 + SY-48)"
```

### Task 12: decisions.md — Double-Failure Named Risk (SY-29)

**Files:**
- Modify: `docs/superpowers/specs/engram/decisions.md`

- [ ] **Step 1: Add double-failure triage to Named Risks table**

In §Named Risks table, add a new row:

```markdown
| **Double-failure triage ambiguity** | Low | `worktree_id` unavailable + `engram_register` failure in same session → `/triage` reports "completion not proven" (indistinguishable from `ledger.enabled=false`). See [enforcement.md §WorktreeID Resolution Failure](enforcement.md#worktreeid-resolution-failure). | Disable ledger, cause worktree_id failure, run `/triage` — output says "completion not proven" with no additional context? |
```

- [ ] **Step 2: Add upper-bound config deferral**

In §Deferred Decisions table, add:

```markdown
| Upper bound on `knowledge_max_stages` / `work_max_creates` | No maximum value enforced in v1. Operators trusted to configure sensibly. Add if misconfiguration patterns emerge. |
```

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/engram/decisions.md
git commit -m "fix(spec): add double-failure Named Risk + config upper-bound deferral (SY-29 + SY-32)"
```

---

## Deferred Findings (P2)

9 P2 findings deferred to a future round. 4 P2s addressed above: SY-1 bundled with SY-18, SY-46 bundled with SY-2, SY-48 bundled with SY-35, SY-54 addressed in Task 7. Total P2: 13 (9 deferred + 4 addressed). Note: SY-8 is P1 (per ledger), addressed in Task 4.

| SY | Finding | Rationale for Deferral |
|----|---------|----------------------|
| SY-45 | enforcement.md §Autonomy Model delegation not in spec.yaml | Metadata annotation, no behavioral impact |
| SY-47 | Ledger append failure diagnostics.warnings mechanism | Aspirational contract, needs design work |
| SY-49 | migration_report.json version space entry | Operational aid, consumed by same script |
| SY-50 | Staging cap TOCTOU overshoot bound | Accepted non-atomic behavior, documentation-only |
| SY-51 | AuditEntry minor-bump safety contract | Same-major tolerance sufficient for v1 |
| SY-52 | Staged entry RecordMeta.session_id=None ambiguity | schema_version sentinel distinguishes cases |
| SY-53 | engram_quality checkpoint vs snapshot check divergence | Correctly specified in field tables, scope table is summary |
| SY-55 | HARNESS_EXCEPTIONS cap process gate | 5-cap assertion at test time is sufficient |
| SY-56 | VR-4A-23 grep scope includes test fixtures | Test author will scope correctly; add note if false positives occur |

## Verification

After all 12 tasks complete:
1. Run cross-reference validation: `grep -r '#[a-z]' docs/superpowers/specs/engram/*.md` to find all anchors, verify each resolves
2. Confirm all 5 P0 SY-IDs (SY-2 through SY-6) are addressed with exact text changes
3. Confirm all 37 P1 SY-IDs are either addressed or deferred with rationale
4. Read spec.yaml and verify the 4th boundary rule is well-formed
5. Read the updated §Check Ordering table and confirm 5-step ordering is self-consistent
