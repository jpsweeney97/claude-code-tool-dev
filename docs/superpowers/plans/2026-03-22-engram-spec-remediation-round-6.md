# Engram Spec Review Round 6 — Remediation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate all 60 findings (3 P0, 33 P1, 24 P2) from engram spec review round 6.

**Architecture:** All changes are spec text edits across 8 normative files in `docs/superpowers/specs/engram/`. Three design decisions were resolved via Codex dialogue (thread `019d173d-eaec-7080-ada9-b15073793275`): IE-7 scopes fail-closed to branches 1-2 only; CE-8 changes the test (not the table); SP-2 simplifies to single-stage content_sha256 dedup. Each task targets a thematic cluster of findings, ordered by dependency.

**Tech Stack:** Markdown spec files. No code changes.

**Review reference:** `.review-workspace/synthesis/report.md`

---

## File Map

All edits target `docs/superpowers/specs/engram/`:

| File | Tasks |
|------|-------|
| `enforcement.md` | 1, 2, 3, 4, 5, 8, 9 |
| `delivery.md` | 1, 3, 6, 7, 10 |
| `operations.md` | 1, 5, 6, 7, 9 |
| `types.md` | 7, 8 |
| `skill-surface.md` | 9 |
| `decisions.md` | 9 |
| `storage-and-indexing.md` | 11 |
| `README.md` | 11 |

---

### Task 1: Fix broken anchors and duplicate SY tags

**Findings:** CC-1, CC-2, CC-3, CC-4

**Files:**
- Modify: `delivery.md:194` (CC-1 broken anchor)
- Modify: `delivery.md:199` (CC-3 wrong anchor suffix)
- Modify: `delivery.md:272,283-286,296-299` (CC-4 duplicate SY tags)
- Modify: `operations.md:15` (CC-2 broken anchor)
- Modify: `enforcement.md:200` (CC-2 target: convert bold to heading)

These are mechanical fixes that restore navigability. Must land first — subsequent tasks reference these anchors.

- [ ] **Step 1: Fix CC-1 — broken anchor in delivery.md line 194**

Replace:
```
[collect_trust_triple_errors()](enforcement.md#collect_trust_triple_errors-contract)
```
With:
```
[collect_trust_triple_errors()](enforcement.md#step-2-validation-engine-entrypoint)
```

- [ ] **Step 2: Fix CC-2 — convert bold text to heading in enforcement.md**

At enforcement.md line 200, replace:
```
**Check ordering:** Each mutating entrypoint must check
```
With:
```
#### Check Ordering

Each mutating entrypoint must check
```

This creates the `#check-ordering` anchor that operations.md line 15 already links to.

- [ ] **Step 3: Fix CC-2 — verify operations.md link now resolves**

Read operations.md line 15. Confirm the link `enforcement.md#check-ordering` now resolves to the new heading.

- [ ] **Step 4: Fix CC-3 — wrong anchor suffix in delivery.md line 199**

Replace:
```
[VR-3A-11](#required-verification-3)
```
With:
```
[VR-3A-11](#required-verification-4)
```

- [ ] **Step 5: Fix CC-4 — renumber duplicate SY tags**

The 7 second-occurrence tags (SY-24 through SY-30) in Steps 3a and 4a must be renumbered. Assign SY-62 through SY-68 (continuing from the highest existing unique tag SY-61).

| Old Tag | Line | New Tag |
|---------|------|---------|
| SY-24 (2nd) | 283 (VR-4A-14) | SY-62 |
| SY-25 (2nd) | 296 (VR-4A-27) | SY-63 |
| SY-26 (2nd) | 197 (VR-3A-13) | SY-64 |
| SY-27 (2nd) | 297 (VR-4A-28) | SY-65 |
| SY-28 (2nd) | 369 (smoke table header) | SY-66 |
| SY-29 (2nd) | 298 (VR-4A-29) | SY-67 |
| SY-30 (2nd) | 299 (VR-4A-30) | SY-68 |

- [ ] **Step 6: Verify no remaining duplicate SY tags**

Run: `grep -o "(SY-[0-9]*)" delivery.md | sort | uniq -c | awk '$1 > 1'`
Expected: no output (all SY tags unique).

- [ ] **Step 7: Commit**

```bash
git add docs/superpowers/specs/engram/delivery.md docs/superpowers/specs/engram/operations.md docs/superpowers/specs/engram/enforcement.md
git commit -m "fix(spec): fix 3 broken anchors and 7 duplicate SY tags (CC-1, CC-2, CC-3, CC-4)"
```

---

### Task 2: Guard degraded mode — scoped fail-closed (IE-7, IE-14)

**Findings:** IE-7 (P1), IE-14 (P1)

**Files:**
- Modify: `enforcement.md:57` (IE-14 canonicalization)
- Modify: `enforcement.md:238` (IE-7 degraded mode)

Design decision resolved via Codex dialogue: scope fail-closed to branches 1-2 only. Branches 3-4 continue with stderr warning.

- [ ] **Step 1: Fix IE-14 — expand canonicalization rule**

At enforcement.md line 57, replace:
```
Paths canonicalized before matching (resolve symlinks, collapse `..`, normalize to absolute).
```
With:
```
Paths canonicalized before matching: expand `~` (via `os.path.expanduser()` or equivalent), then resolve symlinks, collapse `..`, normalize to absolute (`os.path.realpath()` after expansion).
```

- [ ] **Step 2: Fix IE-7 — replace unconditional fail-closed with branch-local degraded mode**

At enforcement.md line 238, replace the sentence:
```
If recomputation fails (e.g., `git rev-parse --git-dir` returns an error), block fail-closed and surface the specific git error.
```
With:
```
If recomputation fails (e.g., `git rev-parse --git-dir` returns an error), the guard enters **degraded mode** for that invocation:

- **Branches 1 and 2** (engine trust injection, direct-write path authorization): These branches require `worktree_id` for trust payload and provenance. Block (exit code 2) with diagnostic: `"engram_guard: worktree_id unavailable — {git_error}. Engine trust injection and direct-write authorization require worktree_id."` This scopes the blocking to Engram-relevant write paths only.
- **Branch 3** (protected-path enforcement): Evaluate normally — protected-path matching does not depend on `worktree_id`. No degradation.
- **Branch 4** (allow unconditionally): Evaluate normally — no `worktree_id` dependency. No degradation.
- **Observability:** Log the git error to stderr. The diagnostic channel path (`ledger/<worktree_id>/<session_id>.diag`) cannot be constructed without `worktree_id`, so stderr is the only available channel — this is structurally correct, not a gap.

This resolves the `engram_session`/`engram_guard` asymmetry: both hooks scope their failure response proportionally to what they need `worktree_id` for. `engram_session` is fail-open because session startup is not blocked by `worktree_id` failure. `engram_guard` blocks only branches 1-2 because only those branches depend on `worktree_id`.
```

- [ ] **Step 3: Verify consistency with WorktreeID Resolution Failure section**

Read enforcement.md lines 270-274. Confirm the WorktreeID Resolution Failure section's fail-open language for `engram_session` is consistent with the new degraded-mode language for `engram_guard`.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/engram/enforcement.md
git commit -m "fix(spec): scope guard fail-closed to branches 1-2 only, add tilde expansion (IE-7, IE-14)"
```

---

### Task 3: Payload file lifecycle (VR-2, CE-4, IE-11)

**Findings:** VR-2 (P0), CE-4 (P1), IE-11 (P1) — Cluster A

**Files:**
- Modify: `enforcement.md:200` (CE-4 check ordering gap)
- Modify: `enforcement.md:166` (IE-11 engine-side missing-payload)
- Modify: `delivery.md` (VR-2 add test)

Three coordinated fixes at the guard-engine boundary.

- [ ] **Step 1: Fix CE-4 — add payload file read failure to check ordering**

After the Check Ordering paragraph (enforcement.md, around line 200), add:

```
If the payload file is absent or unparseable after the `.engram-id` check succeeds, the engine must reject the operation with: `"trust triple not injected: payload file missing or unreadable at {path}"`. Do not attempt to invoke `collect_trust_triple_errors()` with `None` values as a substitute for a missing payload file.
```

- [ ] **Step 2: Fix IE-11 — add engine-side missing-payload contract**

After enforcement.md line 166 (Consumer row in Payload File Contract table), add a new row or paragraph:

```
| **Missing at consumption** | If the payload file path argument is present but the file does not exist at engine startup, the engine must reject with: `"Trust triple missing: payload file not found at {path}"`. Do not proceed with state changes. This handles two root causes uniformly: (a) guard blocked (exit 2) but engine invoked on retry, and (b) partial fsync (file created but incompletely written). |
```

- [ ] **Step 3: Fix VR-2 — add guard write failure test to delivery.md Step 3a**

In delivery.md Required Verification for Step 3a, add after VR-3A-13:

```
- Guard atomic write failure (VR-3A-16): Mock the payload file write to raise `OSError` (disk full simulation). Assert: `engram_guard` returns exit code 2 and diagnostic contains `"engram_guard: payload write failed:"`. Then invoke the engine with a valid payload file path argument pointing to a non-existent file. Assert: engine rejects with `"Trust triple missing: payload file not found"`. (SY-69)
```

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/engram/enforcement.md docs/superpowers/specs/engram/delivery.md
git commit -m "fix(spec): specify payload file lifecycle at hook-engine boundary (VR-2, CE-4, IE-11)"
```

---

### Task 4: Protected-path table and register scope (SY-2, IE-1)

**Findings:** SY-2 (P1), IE-1 (P1)

**Files:**
- Modify: `enforcement.md:51-55` (SY-2 add register column)
- Modify: `enforcement.md:140-154` (IE-1 inactive capability note)

- [ ] **Step 1: Fix SY-2 — add "Register Fires?" column to protected-path table**

Replace the protected-path table at enforcement.md lines 51-55:

```markdown
| Path Class | Protected Paths | Allowed Mutators | Register Fires? |
|---|---|---|---|
| `work` | `engram/work/**` | Engine entrypoints only | Yes |
| `knowledge_published` | `engram/knowledge/**` | Engine entrypoints only | Yes |
| `knowledge_staging` | `~/.claude/engram/<repo_id>/knowledge_staging/**` | Engine entrypoints only | No (Bash-mediated) |
```

- [ ] **Step 2: Fix IE-1 — add inactive capability note to guard algorithm**

After enforcement.md line 154 (capability gating paragraph), add:

```
**Inactive capability behavior:** When a capability is inactive, its branch is skipped (no-op) — execution continues to the next branch as if the match did not occur. No diagnostic is emitted for inactive-capability skips. This is a silent allow, consistent with the "falls through to branch 4" behavior documented in the rollout table above.
```

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/engram/enforcement.md
git commit -m "fix(spec): add register column to protected-path table, document inactive capability behavior (SY-2, IE-1)"
```

---

### Task 5: Authority placement — mode definitions (SY-1)

**Findings:** SY-1 (P1), AA-4 (P2)

**Files:**
- Modify: `enforcement.md:298-300` (remove mode definitions, keep reference)
- Modify: `operations.md` (add mode definitions after Core Rules)

- [ ] **Step 1: Add mode definitions to operations.md**

After operations.md line 19 (end of Core Rules), add a new section:

```markdown
### Work Mode Definitions

The Work subsystem operates in one of two modes, configured via `work_mode` in [`.claude/engram.local.md`](enforcement.md#configuration):

- **`suggest`:** Engine prepares the operation but surfaces it to the user for confirmation before writing. The user sees what will be created and approves or rejects. If the user abandons the session without confirming, the proposed operation is discarded — no write is performed. The `suggest` flow is entirely in-session; there is no queued state to persist.
- **`auto_audit`:** Engine creates the work item automatically. The item is marked for user review at next `/triage`. `work_max_creates` limits cumulative automatic creations per session. Trust injection still applies — `engram_guard` validates the trust triple regardless of mode. Cap enforcement (`work_max_creates`) is the engine's responsibility, not the guard's — `engram_guard` is mode-agnostic.
```

- [ ] **Step 2: Replace mode definitions in enforcement.md with cross-reference**

At enforcement.md lines 298-300, replace:
```
**Mode definitions** (behavioral semantics — these are `behavior_contract`-class claims placed here for co-location with the configuration contract; for precedence purposes, [operations.md](operations.md) has not been amended to incorporate them):
- **`suggest`:** Engine prepares the operation but surfaces it to the user for confirmation before writing. The user sees what will be created and approves or rejects. If the user abandons the session without confirming, the proposed operation is discarded — no write is performed. The `suggest` flow is entirely in-session; there is no queued state to persist.
- **`auto_audit`:** Engine creates the work item automatically. The item is marked for user review at next `/triage`. `work_max_creates` limits cumulative automatic creations per session. Trust injection still applies — `engram_guard` validates the trust triple regardless of mode. Cap enforcement (`work_max_creates`) is the engine's responsibility, not the guard's — `engram_guard` is mode-agnostic.
```
With:
```
**Mode definitions:** See [operations.md §Work Mode Definitions](operations.md#work-mode-definitions) for behavioral semantics (`behavior_contract` authority). This section retains the configuration schema and enforcement-level caps (`enforcement_mechanism` authority).
```

- [ ] **Step 3: Fix AA-4 — extend disclaimer to cover the Autonomy Model table**

After the new cross-reference line in enforcement.md, add:

```
**Behavioral characterizations in the table above** (rationale column entries like "agents propose, users approve" and "auto-stages without user confirmation") are summaries of the authoritative specifications in [operations.md](operations.md). If the table rationale conflicts with operations.md, operations.md prevails.
```

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/engram/enforcement.md docs/superpowers/specs/engram/operations.md
git commit -m "fix(spec): move mode definitions to operations.md, fix authority placement (SY-1, AA-4)"
```

---

### Task 6: Promote state machine precision (CE-1, CE-2)

**Findings:** CE-1 (P1), CE-2 (P1)

**Files:**
- Modify: `operations.md:128` (CE-2 Step 1 CLAUDE.md read)
- Modify: `operations.md:139` (CE-1 B2 discriminator)

- [ ] **Step 1: Fix CE-2 — make Step 1 CLAUDE.md read explicit**

At operations.md line 128, after "Step 1 (engine): Knowledge engine validates promotability via state machine:", add:

```
        Step 1 reads CLAUDE.md to perform marker search and drift detection.
        The Branch C1/C2 determination is complete before Step 2 begins.
        The engine returns the branch classification to the skill as part of the promotion plan.
```

- [ ] **Step 2: Fix CE-1 — define B2 discriminator as detected mismatch**

At operations.md line 139, replace:
```
            B2 (target_section changed by user request): Manual reconcile.
```
With:
```
            B2 (target_section mismatch — promote-meta.target_section differs from
                detected marker location via global marker search): Manual reconcile.
                On re-entry after a prior B2 Step 3 failure, this mismatch is detected
                structurally (promote-meta has old target_section, markers at new location)
                without requiring an active user request.
```

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/engram/operations.md
git commit -m "fix(spec): clarify B2 re-entry discriminator and Step 1 CLAUDE.md read (CE-1, CE-2)"
```

---

### Task 7: Distill dedup simplification and schema fixes (SP-2, SP-1, SP-3)

**Findings:** SP-2 (P1), SP-1 (P1), SP-3 (P1)

**Files:**
- Modify: `operations.md:50-55` (SP-2 distill dedup sequence)
- Modify: `types.md:302-332` (SP-2 per-envelope semantics table)
- Modify: `types.md:352` (SP-1 lesson-meta example reorder)
- Modify: `types.md:428-443` (SP-3 record_ref population rules)
- Modify: `delivery.md:155` (SP-2 VR-2A-5 rewrite)

Design decision resolved via Codex dialogue: simplify to single-stage content_sha256 dedup; keep idempotency_key as trace-only with per-envelope semantics table.

- [ ] **Step 1: Fix SP-2 — simplify distill dedup sequence in operations.md**

At operations.md lines 50-55, replace:
```
    -> Duplicate check: idempotency_key against staged + published entries
    -> If duplicate: skip
    -> If new: creates staged candidate
```

**Distill dedup sequence:** (1) Envelope-level: check `idempotency_key` against existing staged/published envelopes. If match, return existing result. (2) Per-candidate: check each `DistillCandidate.content_sha256` against existing staged/published files. If match, skip that candidate. Within a single batch, candidates with identical `content_sha256` are deduplicated (only one written).
```
With:
```
    -> Per-candidate dedup: content_sha256 against staged + published entries
    -> If match: skip that candidate
    -> If new: creates staged candidate (atomic via O_CREAT|O_EXCL)
```

**Distill dedup:** Per-candidate `content_sha256` dedup via atomic `O_CREAT | O_EXCL` staging file creation. Identical candidates from concurrent operations coalesce at the filesystem level. Within a single batch, candidates with identical `content_sha256` are deduplicated (only one written). The `DistillEnvelope.idempotency_key` is not persisted or checked for distill operations — see [types.md §Idempotency Enforcement Per Envelope Type](types.md#idempotency-enforcement-per-envelope-type).
```

- [ ] **Step 2: Fix SP-2 — add per-envelope idempotency semantics table to types.md**

After types.md line 332 (end of Dedup section), add:

```markdown
### Idempotency Enforcement Per Envelope Type

| Envelope | Enforcement | Mechanism | Rationale |
|---|---|---|---|
| `DeferEnvelope` | **Enforced** | Engine checks `idempotency_key` against existing tickets | Ticket creation is not content-addressed; envelope-level dedup is the sole protection against retry duplicates |
| `DistillEnvelope` | **Trace-only** | `idempotency_key` is computed and included in the header but NOT persisted or checked | Per-candidate `content_sha256` dedup via `O_CREAT\|O_EXCL` provides content-addressed dedup. Published dedup uses `content_sha256` in `lesson-meta`. Envelope-level identity adds no correctness guarantee beyond what per-candidate dedup already provides. |
| `PromoteEnvelope` | **Enforced** | Engine checks `idempotency_key` against `promote-meta` state | Promote is a state-machine transition; re-entry detection is structural (Branch B1 rejection) |

The `idempotency_key` field remains in `EnvelopeHeader` (shared type) for all envelope types. For `DistillEnvelope`, the field serves as a trace/observability aid — it is available in the envelope for logging and debugging but is not persisted to staging-meta and is not checked at any dedup stage.
```

- [ ] **Step 3: Fix SP-2 — remove "checked against existing staged/published" claim from types.md**

At types.md around line 308-320 (Idempotency — Same Operation Retried section), find and update text that claims all envelope types participate in envelope-level idempotency checking. Update the opening paragraph:

Replace:
```
The `idempotency_key` in `EnvelopeHeader` is computed as `sha256(canonical_json_bytes(idempotency_material)).hexdigest()` where the material is envelope-type-specific:
```
With:
```
The `idempotency_key` in `EnvelopeHeader` is computed as `sha256(canonical_json_bytes(idempotency_material)).hexdigest()` where the material is envelope-type-specific. Enforcement semantics vary by envelope type — see [§Idempotency Enforcement Per Envelope Type](#idempotency-enforcement-per-envelope-type):
```

- [ ] **Step 4: Fix SP-2 — rewrite VR-2A-5 in delivery.md**

At delivery.md line 155, replace VR-2A-5:
```
- Distill dedup envelope-level-first ordering (VR-2A-5): Submit a `DistillEnvelope` with 2 candidates (A, B) → both staged. Instrument per-candidate dedup check to record calls. Submit the same `DistillEnvelope` (identical `idempotency_key`) again. Assert: per-candidate check was NOT called on the second submission (envelope-level short-circuit). Assert: staging directory still contains exactly 2 files (no new files). This verifies envelope-level match precedes per-candidate processing. (SY-23)
```
With:
```
- Distill per-candidate dedup ordering (VR-2A-5): Submit a `DistillEnvelope` with 2 candidates (A, B) → both staged as files named by `content_sha256[:16]`. Submit the same `DistillEnvelope` again (identical candidates). Assert: `O_CREAT | O_EXCL` on each candidate's staging file path returns `FileExistsError` (atomic coalesce). Assert: staging directory still contains exactly 2 files (no new files, no corruption). Submit a third `DistillEnvelope` with 1 new candidate (C) + 1 duplicate (A). Assert: staging directory contains 3 files (C added, A deduplicated). (SY-23)
```

- [ ] **Step 5: Fix SP-1 — reorder lesson-meta example to alphabetical**

At types.md line 352, replace:
```
<!-- lesson-meta {"meta_version": "1.0", "lesson_id": "<UUIDv4>", "content_sha256": "<hex>", "created_at": "<ISO8601>", "producer": "learn|curate"} -->
```
With:
```
<!-- lesson-meta {"content_sha256": "<hex>", "created_at": "<ISO8601>", "lesson_id": "<UUIDv4>", "meta_version": "1.0", "producer": "learn|curate"} -->
```

- [ ] **Step 6: Fix SP-3 — add record_ref column to Event Vocabulary table**

At types.md lines 439-443, replace the Event Vocabulary table with:

```markdown
| Event Type | Producer | Payload Fields | `record_ref` | Purpose |
|---|---|---|---|---|
| `snapshot_written` | orchestrator | `{ref: str, orchestrated_by: str}` | `payload.ref` | Timeline fidelity — records snapshot creation. `orchestrated_by` values: `"save"`, `"quicksave"`, `"load"`. See [operations.md §Snapshot Event Emission](operations.md#snapshot-event-emission) for per-producer emit conditions. |
| `defer_completed` | engine | `{source_ref: str, emitted_count: int}` | `null` | Completion evidence for /triage inference |
| `distill_completed` | engine | `{source_ref: str, emitted_count: int}` | `null` | Completion evidence for /triage inference |
```

Also update the LedgerEntry schema comment at line 428:
```
    record_ref: str | None        # RecordRef canonical serialization; see Event Vocabulary for per-event-type population rules
```

- [ ] **Step 7: Commit**

```bash
git add docs/superpowers/specs/engram/types.md docs/superpowers/specs/engram/operations.md docs/superpowers/specs/engram/delivery.md
git commit -m "fix(spec): simplify distill dedup to single-stage, fix lesson-meta ordering, add record_ref rules (SP-2, SP-1, SP-3)"
```

---

### Task 8: Remaining enforcement.md P1 fixes (CE-13, CE-17, IE-3, IE-6, IE-9)

**Findings:** CE-13 (P1), CE-17 (P1), IE-3 (P1), IE-6 (P1), IE-9 (P1)

**Files:**
- Modify: `enforcement.md` (multiple sections)

- [ ] **Step 1: Fix IE-6 — expand SessionStart table worktree_id failure row**

At enforcement.md line 262, replace the On Failure column for worktree_id resolution:
```
Log warning to diagnostic channel (if `worktree_id` available); guard re-derives independently; session not blocked. See [WorktreeID Resolution Failure](#worktreeid-resolution-failure) below.
```
With:
```
Log warning to diagnostic channel if `worktree_id` available; otherwise log to stderr only (see [WorktreeID Resolution Failure](#worktreeid-resolution-failure)). Guard re-derives independently. Session not blocked.
```

- [ ] **Step 2: Fix IE-3 — document double-failure path as accepted limitation**

At enforcement.md line 274, after "log to stderr only", add:

```
If `worktree_id` is unavailable and `engram_register` fails in the same session, `/triage` cannot distinguish this from a legitimate "completion not proven" outcome — it reports "completion not proven" rather than "ledger unavailable." This is an accepted limitation of the double-failure path, consistent with the [diagnostic channel directory creation failure](#session-diagnostic-channel) limitation.
```

- [ ] **Step 3: Fix CE-13 — mandate .get() access for TrustPayload fields**

After enforcement.md line 200 (Check Ordering section), add:

```
**Payload field access:** Engine code must access `TrustPayload` fields via `.get()` (dict-style) rather than direct attribute access. This ensures `None` values from missing fields are captured by `collect_trust_triple_errors()` validation rather than raising `KeyError`. Example: `payload.get("hook_injected")` not `payload["hook_injected"]`.
```

- [ ] **Step 4: Fix IE-9 — document origin-matching enforcement gap**

At enforcement.md line 211, after the origin-matching table, add:

```
**Enforcement mechanism:** Origin-matching has no shared runtime validator. `collect_trust_triple_errors()` validates structural correctness (`hook_request_origin` is a valid string in `{"user", "agent"}`) but does not enforce per-entrypoint origin rules. Each entrypoint is responsible for checking that the origin value matches its expected category (see table above). VR-3A-14 verifies this convention via AST scan or instrumented test. A shared helper `validate_origin_match(expected, actual)` is recommended but not mandated — the enforcement is per-entrypoint by design.
```

- [ ] **Step 5: Fix CE-17 — expand triage case (4) for missing emitted_count key**

Read operations.md lines 84-86. At the parenthetical "(if emitted_count absent from event vocabulary, treat as 'completion not proven')", expand to:

```
            (if the completion event is present but `emitted_count` key is absent
            from the payload dict, treat as "completion not proven" — this is a
            producer bug, distinct from case where the event itself is absent)
```

- [ ] **Step 6: Commit**

```bash
git add docs/superpowers/specs/engram/enforcement.md docs/superpowers/specs/engram/operations.md
git commit -m "fix(spec): fix 6 P1 enforcement precision gaps (CE-5, CE-13, CE-17, IE-3, IE-6, IE-9)"
```

---

### Task 9: Remaining P1 spec text fixes (CE-5, VR-1)

**Findings:** CE-5 (P1), VR-1 (P0)

**Files:**
- Modify: `skill-surface.md` (CE-5 trigger differentiation)
- Modify: `delivery.md` (VR-1 add test)

- [ ] **Step 1: Fix CE-5 — verify /learn trigger differentiation wording**

In skill-surface.md line 82, verify the `/distill` vs `/learn` trigger differentiation row does NOT use the phrase "publishes directly" without clarification. The current text should read "publishes to `learnings.md` via the Knowledge engine entrypoint" (not "publishes directly"). If "publishes directly" appears anywhere in this row, replace with "publishes immediately (via engine, not staging)". If the text already clarifies the engine path, this finding is pre-resolved — skip.

- [ ] **Step 2: Fix VR-1 — add .engram-id ordering test to delivery.md Step 3a**

In delivery.md Required Verification for Step 3a, add:

```
- `.engram-id` pre-trust-triple ordering (VR-3A-17): Invoke a mutating Work engine entrypoint with a valid trust triple but no `.engram-id` file present. Assert: error message contains `"Engram not initialized"` and does NOT contain any trust-triple error string (`"hook_injected"`, `"hook_request_origin"`, `"session_id"`). This verifies the [check ordering](enforcement.md#check-ordering) rule that `.engram-id` existence is checked before `collect_trust_triple_errors()`. (SY-70)
```

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/engram/skill-surface.md docs/superpowers/specs/engram/delivery.md
git commit -m "fix(spec): fix /learn trigger wording, add .engram-id ordering test (CE-5, VR-1)"
```

---

### Task 10: CE-8 VR-4A-19 rewrite and VR additions (CE-8, VR-3–VR-18)

**Findings:** CE-8 (P1), VR-3 through VR-18 (mixed P0/P1/P2)

**Files:**
- Modify: `delivery.md:288` (CE-8 VR-4A-19 rewrite)
- Modify: `delivery.md` (VR additions throughout)

Design decision resolved via Codex dialogue: change VR-4A-19 to capability-scoped test matrix with canonical absolute paths.

- [ ] **Step 1: Fix CE-8 — rewrite VR-4A-19 as capability-scoped test matrix**

At delivery.md line 288, replace:
```
- Context direct-write path authorization (VR-4A-19): (a) Write to `~/.claude/engram/<different_repo_id>/snapshots/test.md` → assert blocked by `engram_guard`; (b) Write to correct repo's `snapshots/test.md` → assert allowed; (c) Write with path traversal (`snapshots/../other_file.md`) → assert blocked after canonicalization.
```
With:
```
- Context direct-write path authorization (VR-4A-19): Capability-scoped test matrix using canonical absolute paths (not tilde-relative). The `context_direct_write_authorization` capability state is a test fixture parameter.

  With capability **active** (Step 4a+):
  (a) Write to `/home/user/.claude/engram/<correct_repo_id>/snapshots/test.md` → assert allowed (branch 2)
  (b) Write to `/home/user/.claude/engram/<correct_repo_id>/checkpoints/test.md` → assert allowed (branch 2)
  (c) Write to `/home/user/.claude/engram/<different_repo_id>/snapshots/test.md` → assert allowed via branch 4 (path is outside this repo's Context root, falls through to allow)
  (d) Write to `/home/user/.claude/engram/<different_repo_id>/checkpoints/test.md` → assert allowed via branch 4

  With capability **inactive** (before Step 4a):
  (e-h) Same 4 paths as above → all assert allowed via branch 4 (branch 2 is no-op when inactive)

  Path canonicalization (independent of capability state):
  (i) Write with path traversal (`snapshots/../other_file.md`) → assert blocked or allowed based on canonicalized path resolution, not raw path
  (j) Tilde expansion: tilde-relative paths must match canonical absolute paths after `expanduser()` — see [IE-14 canonicalization](enforcement.md#protected-path-enforcement)
```

- [ ] **Step 2: Add VR-3 — guard engine-detection diagnostic test**

In delivery.md Step 3a verification, add:
```
- Guard engine-detection failure diagnostic (VR-3A-18): Invoke `engram_guard` with a Bash tool call where the path matches `engine_*.py` filename but resolves outside `<engram_scripts_dir>`. Assert: diagnostic output contains `"engine invocation not recognized"`. (SY-71)
```

- [ ] **Step 3: Add VR-4 — worktree_id resolution failure diagnostic test**

In delivery.md Step 4a verification, add:
```
- WorktreeID resolution failure diagnostic (VR-4A-32): (a) Mock `identity.get_worktree_id()` to raise. Assert: `engram_session` does not block session startup and output goes to stderr (not to `.diag`). (b) Mock `git rev-parse --git-dir` to succeed but return empty string. Assert: `worktree_id` diagnostic is written to `.diag`. (SY-72)
```

- [ ] **Step 4: Add VR-5 — version space traceability note**

In delivery.md cross-cutting verification section, add:
```
| Version space coverage | All 5 version spaces (envelope, record provenance, ledger format, knowledge entry, promotion state) have at least one VR-* rejection/degradation test before Step 5 is complete | Progressive |
```

- [ ] **Step 5: Add VR-6 — corrupt staging file detection test**

In delivery.md Step 2a verification, add:
```
- Corrupt staging file detection (VR-2A-7): Construct a staging file where the markdown body content differs from the `content_sha256` in the `staging-meta` comment. Run `/curate`. Assert: corrupt file is skipped, `QueryDiagnostics.warnings` contains a message referencing the filename, and no publish occurs for that candidate. (SY-73)
```

- [ ] **Step 6: Add VR-7 fix — clarify environment probe as precondition**

In delivery.md VR-4A-3 (line 272), append:
```
The environment probe (per-file latency > 10ms → skip timing assertion) is a precondition check executed before the 200-file test, not a conditional within it. This test is marked `@pytest.mark.slow` and excluded from default CI runs.
```

- [ ] **Step 7: Add VR-8, VR-9, VR-10, VR-11, VR-15 tests**

In delivery.md Step 4a/3a verification sections, add:
```
- operation_id None when standalone (VR-3A-19): Run standalone `/defer` (not via `/save`). Assert: all ledger entries from that operation have `operation_id == None`. (SY-74)
- Branch B2 Step 3 failure detection by /triage (VR-4A-33): Fixture where CLAUDE.md has markers at `## New Section` but `promote-meta.target_section == "## Old Section"`. Assert: `/triage` reports `target_section_mismatch` anomaly. (SY-75)
- save_recovery.json success-path write (VR-4A-34): Run `/save` where all sub-operations succeed. Assert: `save_recovery.json` exists with `results.snapshot.status == "ok"`, `results.defer.status == "ok"`, `results.distill.status == "ok"`. (SY-76)
- Knowledge anomaly detection split (VR-4A-11 amendment): Split fixture into two independent cases: (a) entry missing `lesson-meta` → assert `provenance_not_established`; (b) entry with valid `lesson-meta` but `producer: "unknown_tool"` → assert `provenance_not_established`. Both must pass independently.
- emitted_count missing key fixture (VR-4A-35): Fixture with a `defer_completed` event in the ledger shard where payload dict contains `source_ref` but no `emitted_count` key. Assert: `/triage` reports case (4) ("completion not proven"), not case (3). (SY-77)
```

- [ ] **Step 8: Fix VR-16 — restrict AST scan applicability**

In delivery.md VR-3A-9, append:
```
AST scan (method a) is acceptable only for single-function entrypoints where both calls appear in the same function body. For class-based or OOP entrypoints, use method (b) exclusively.
```

- [ ] **Step 9: Fix VR-17 — add field-exactness assertion to bridge test**

In delivery.md Step 1 bridge compatibility test, add:
```
- Bridge field-exactness (VR-1-2): Assert the converted JSON from the bridge adapter contains exactly the expected fields and no additional ones. This catches accidental field additions to `EnvelopeHeader` that the bridge adapter fails to filter. (SY-78)
```

- [ ] **Step 10: Commit**

```bash
git add docs/superpowers/specs/engram/delivery.md
git commit -m "fix(spec): rewrite VR-4A-19 as capability matrix, add 12 missing verification tests (CE-8, VR-3-VR-18)"
```

---

### Task 11: P2 documentation items (24 findings)

**Findings:** AA-2, AA-3, CE-6, CE-7, CE-9, CE-10, CE-11, CE-12, CE-14, CC-4 (done in Task 1), VR-12, VR-13, VR-14, VR-18, SP-4, SP-5, SP-6, SP-7, IE-4, IE-5, IE-8, IE-10, IE-12, IE-13

**Files:**
- Modify: `types.md` (SP-4, SP-6, SP-7)
- Modify: `enforcement.md` (IE-4, IE-8, IE-12, IE-13, CE-7, CE-9)
- Modify: `delivery.md` (VR-12, VR-13, VR-14, VR-18, CE-12)
- Modify: `operations.md` (CE-6, CE-10, CE-11, IE-10)
- Modify: `decisions.md` (IE-5)
- Modify: `storage-and-indexing.md` (CE-14, SP-5)

These are lower-risk documentation improvements. Apply in a single batch.

- [ ] **Step 1: Fix SP-6 — add UTC to promoted_at comment**

At types.md line 170, replace:
```
    promoted_at: str              # ISO 8601
```
With:
```
    promoted_at: str              # ISO 8601 UTC (suffix Z or +00:00)
```

- [ ] **Step 2: Fix SP-4 — state body-to-content invariant**

After types.md line 148 (content authority rule), add:
```
**Body identity invariant:** The markdown body (after the staging-meta comment) MUST be byte-identical to `DistillCandidate.content`. The Knowledge engine MUST write the body as the raw content string with no additional normalization. If normalization is required before writing, it must be applied to `DistillCandidate.content` before computing `content_sha256`.
```

- [ ] **Step 3: Fix SP-7 — document RecordRef.from_str slash handling**

After types.md line 30 (RecordRef canonical serialization), add:
```
**Parsing rule for `from_str`:** The canonical form `<subsystem>/<record_kind>/<record_id>` is split on the first two `/` characters. Any `/` characters in `record_id` are preserved verbatim. Example: `"work/ticket/T-2026-03/01"` → `subsystem="work"`, `record_kind="ticket"`, `record_id="T-2026-03/01"`.
```

- [ ] **Step 4: Fix IE-8 — add scope comment to work_max_creates config**

At enforcement.md line 309, replace:
```
  work_max_creates: 5
```
With:
```
  work_max_creates: 5         # Per-session automatic creations (resets each session)
```

- [ ] **Step 5: Fix IE-12 — specify orphan cleanup target path**

At enforcement.md line 265, replace:
```
| Clean orphan payload files (>24h) | Max 20 files | Fail-open |
```
With:
```
| Clean orphan payload files (>24h) in `<repo_root>/.claude/engram-tmp/` | Max 20 files | Fail-open |
```

- [ ] **Step 6: Fix IE-13 — state co-deployment invariant**

After enforcement.md line 180 (authorized engine invocation pattern), add:
```
**Co-deployment invariant:** The `hooks/` and `scripts/` directories must be deployed together — `engram_guard`'s `__file__`-relative path resolution requires that both reside under the same plugin root. Promoting `engram_guard` without co-promoting engine scripts (or vice versa) will cause pattern match failures for all engine invocations.
```

- [ ] **Step 7: Fix IE-5 — add named risk for Context any-source write**

In decisions.md Named Risks table, add:
```
| Context any-source write authorization | Low | Branch 2 allows any Write/Edit to Context paths regardless of calling skill. Non-Context skills writing to Context paths are not blocked — `/triage` anomaly detection (`session_id` missing) is the sole detection mechanism post-write. |
```

- [ ] **Step 8: Fix IE-4 — specify engram_quality warning prefix**

At enforcement.md quality validation section, where the missing-file warning is specified, clarify the prefix:
```
emit a warning at `[engram_quality:warn]` level: `"snapshot file not found at post-write readback — quality check skipped"`
```

- [ ] **Step 9: Fix IE-10 — add opaque-entry handling to operations.md triage**

At operations.md line 73, in the `.diag` file check, add:
```
        (`.diag` non-empty, including all-opaque entries where all entries have
        unrecognized schema_version — see enforcement.md §Session Diagnostic Channel)
```

- [ ] **Step 10: Fix remaining P2 items (CE-6, CE-7, CE-9, CE-10, CE-11, CE-12, CE-14, VR-12, VR-13, VR-14, VR-18, SP-5, AA-2, AA-3)**

Apply these mechanical fixes:
- **CE-6:** In operations.md `/curate` mechanics, clarify sort key: "sorted by `durability` (likely_durable first), then by `staged_at` (oldest first)."
- **CE-7:** In enforcement.md, note that symlinks in engine paths are handled by canonicalization.
- **CE-9:** In enforcement.md, add: "The `TrustPayload` TypedDict defined in types.md is the canonical schema for the JSON payload file."
- **CE-10:** In operations.md Branch A, clarify: "User confirmation is implicit in lesson selection — the user chose this lesson for promotion. No separate approval prompt."
- **CE-11:** In operations.md recovery manifest, add: "The `save_recovery.json` schema does not include a `schema_version` field — recovery manifests are ephemeral operational aids, not versioned contracts."
- **CE-12:** In delivery.md VR-4A-19 (already rewritten in Task 10), confirm `checkpoints/` coverage is included.
- **CE-14:** In storage-and-indexing.md storage layout diagram, add `.diag` files under `ledger/<worktree_id>/`.
- **VR-12:** In delivery.md VR-5-5, replace "All 13 skill smoke tests pass" with "All skills in the progressive activation manifest pass their smoke test."
- **VR-13:** In delivery.md Step 2a verification, add: "Staging-meta sort_keys=True determinism (VR-2A-8): Submit same DistillCandidate twice. Assert staging-meta JSON comment is byte-identical."
- **VR-14:** In delivery.md VR-3A-6, add: "Assert: `len(harness_exceptions) <= 5`."
- **VR-18:** In delivery.md Step 4a verification, add: "engram_quality Edit-path file-missing warning (VR-4A-36): Delete a snapshot file immediately after Edit. Assert: exit code 0, warning contains 'snapshot file not found at post-write readback'."
- **SP-5:** In storage-and-indexing.md, note: "Work ticket YAML schema is inherited from the ticket plugin format — field requirements (`schema_version`, `worktree_id`, `session_id`, `status`) are specified in the RecordMeta field mapping table."
- **AA-2:** Contingent on SY-1 fix (done in Task 5) — no README change needed since mode definitions moved to operations.md.
- **AA-3:** In delivery.md VR-4A-23, add note: "Any new PostToolUse hook added at any step must trigger a re-run of the Enforcement Boundary Constraint AST scan."

- [ ] **Step 11: Commit**

```bash
git add docs/superpowers/specs/engram/
git commit -m "fix(spec): remediate 24 P2 documentation items from spec review round 6"
```

---

## Verification

After all tasks complete:

- [ ] **Final verification: grep for remaining broken anchors**

```bash
grep -oP '\[.*?\]\(.*?#.*?\)' docs/superpowers/specs/engram/*.md | head -50
```

Spot-check that anchor targets exist. Full automation is post-implementation work.

- [ ] **Final verification: SY tag uniqueness**

```bash
grep -ohP '\(SY-\d+\)' docs/superpowers/specs/engram/delivery.md | sort | uniq -c | awk '$1 > 1'
```

Expected: no output.

- [ ] **Final verification: count changes match findings**

The remediation should touch exactly these counts:
- 3 P0 findings: VR-1, VR-2, VR-17 — all addressed
- 33 P1 findings — all addressed
- 24 P2 findings — all addressed
- Total: 60 findings remediated across 11 tasks and ~11 commits
