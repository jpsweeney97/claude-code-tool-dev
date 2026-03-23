# Skill Composability Spec Remediation Plan — Round 11

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate all 34 canonical findings from the round 11 spec review

**Architecture:** Text-only spec edits across 9 files in `docs/superpowers/specs/skill-composability/`. Seven design decisions resolved via Codex dialogue (thread `019d18aa-0c09-7683-958a-b92413367a28`). All edits are mechanical or apply agreed dialogue resolutions — no open design questions remain.

**Tech Stack:** Markdown spec files, YAML authority model (spec.yaml)

---

**Source:** `.review-workspace/synthesis/report.md` (5-reviewer team, 2026-03-22)
**Scope:** 34 canonical findings (2 P0, 20 P1, 12 P2) across 9 normative files + spec.yaml
**Spec:** `docs/superpowers/specs/skill-composability/` (10 files, 9 normative + 1 supporting + spec.yaml)
**Dialogue:** Codex collaborative dialogue resolved all 7 contract ambiguities (SY-3, SY-7, SY-8, SY-9, SY-10, SY-11, SY-23)
**Dominant patterns:** Invalid authority metadata cascade (7 raw → SY-1), enforcement gaps without gates (10 P1), verification table coverage holes (6 P1), three related enforcement clusters (`hold_reason`, `record_path`, `thread continuation`)

## Strategy

Eight tasks in three phases, ordered by dependency and edit-locality:

1. **Phase 1** — Four tasks, all parallel (touch different files or non-overlapping sections):
   - **T1:** Authority model repair (3 findings) — spec.yaml, README.md
   - **T2:** P0 verification gaps (2 findings) — verification.md (consumer test section)
   - **T3:** Contract clarity — dialogue-resolved design decisions (7 findings) — capsule-contracts.md, routing-and-materiality.md, pipeline-integration.md, foundations.md, lineage.md
   - **T4:** Verification table + editorial batch (12 findings) — verification.md (routing section + lineage section), routing-and-materiality.md, decisions.md, README.md

2. **Phase 2** — After T1 (governance claims must be valid):
   - **T5:** Governance + delivery enforcement repairs (4 findings) — governance.md, delivery.md

3. **Phase 3** — After T3 (normative contracts must be stable):
   - **T6:** hold_reason enforcement cluster (3 findings) — routing-and-materiality.md, verification.md
   - **T7:** record_path enforcement chain (2 findings) — verification.md, delivery.md
   - **T8:** Thread continuation structural enforcement (1 finding) — delivery.md

**Dependency chains:**
1. SY-1 (T1) → SY-11 governance alignment (T3): governance needs valid `enforcement_mechanism` claim before SY-11 can cite it
2. SY-1 (T1) → SY-18 (T5): governance gates reference claim type
3. SY-3 teardown semantics (T3) → SY-19 hold_reason non-overwrite assertion references abort-path parity (T6)
4. SY-9 empty decomposition (T3) → SY-6 NS adapter guard test references case (a) subcase (T2 — but T2 adds deferred entry, no dependency on SY-9 resolution)

**Commit strategy:**
1. `fix(spec): remediate 3 authority model findings from review round 11` (T1)
2. `fix(spec): remediate 2 P0 verification findings from review round 11` (T2)
3. `fix(spec): remediate 7 contract clarity findings from review round 11` (T3)
4. `fix(spec): remediate 12 verification + editorial findings from review round 11` (T4)
5. `fix(spec): remediate 4 governance + delivery findings from review round 11` (T5)
6. `fix(spec): remediate 3 hold_reason enforcement findings from review round 11` (T6)
7. `fix(spec): remediate 2 record_path enforcement findings from review round 11` (T7)
8. `fix(spec): remediate 1 thread continuation enforcement finding from review round 11` (T8)

---

## Task 1 — Authority Model Repair (3 findings)

**Finding count:** 1 P1, 2 P2
**Findings:** SY-1, SY-25, SY-26
**Files:** spec.yaml, README.md
**Depends on:** nothing — start immediately

### [SY-1] `review_gate` invalid claim — governance has zero effective claims (7 raw merged)

**Sources:** AA-1, AA-2, AA-3, AA-5, AA-6, AA-7, CE-7
**File:** spec.yaml:31, spec.yaml:52; README.md:24, README.md:36

`review_gate` is not in the fixed 8-claim enum (`architecture_rule`, `behavior_contract`, `decision_record`, `interface_contract`, `enforcement_mechanism`, `implementation_plan`, `verification_strategy`). Governance's description says "derivative enforcement" — `enforcement_mechanism` is the correct claim.

- [ ] **Step 1: Fix spec.yaml governance default_claims (line 31)**

Change:
```yaml
    default_claims: [review_gate]
```
To:
```yaml
    default_claims: [enforcement_mechanism]
```

- [ ] **Step 2: Fix spec.yaml claim_precedence (line 52)**

Change:
```yaml
    review_gate: [governance]
```
To:
```yaml
    enforcement_mechanism: [routing, governance]
```

Note: `routing` already holds `enforcement_mechanism` (line 23). Adding governance as second in precedence reflects that routing is the normative source and governance is derivative enforcement.

- [ ] **Step 3: Fix README.md authority table (line 24)**

Change:
```markdown
| `governance` | PR review gate procedures — derivative enforcement citing normative clauses | `review_gate` |
```
To:
```markdown
| `governance` | PR review gate procedures — derivative enforcement citing normative clauses | `enforcement_mechanism` |
```

- [ ] **Step 4: Fix README.md precedence section (line 36)**

Change:
```markdown
- `review_gate`: governance (sole holder)
```
To:
```markdown
- `enforcement_mechanism`: routing > governance
```

### [SY-25] `delivery_layers` extra spec.yaml key + deprecated term

**Source:** AA-4
**File:** spec.yaml:67-85

`delivery_layers` is informational and already noted as a convenience summary of `foundations.md §Three-Layer Delivery Authority`. It introduces a duplicate authority source with a deprecated term (`inline_stubs`). Remove the entire block — the normative definition in foundations.md is authoritative.

- [ ] **Step 5: Remove `delivery_layers` block from spec.yaml (lines 67-85)**

Remove this entire block (including the NOTE comment on lines 67-69):
```yaml
  # NOTE: delivery_layers is informational — a convenience summary of the three-layer
  # authority hierarchy defined normatively in foundations.md §Three-Layer Delivery Authority.
  # On conflict, foundations.md is authoritative per fallback_authority_order.
delivery_layers:
  # Three-layer authority hierarchy for composition delivery.
  # Full rationale: foundations.md#three-layer-delivery-authority
  - layer: 1
    name: spec_files
    description: Normative spec authority files defined in the authorities block above.
    precedence: highest
  - layer: 2
    name: composition_contract
    description: Runtime projection of spec invariants for inter-skill composition.
    precedence: below spec_files
  - layer: 3
    name: inline_stubs
    description: Composition-specific blocks within each participating skill's SKILL.md.
    precedence: lowest
  precedence_order: [spec_files, composition_contract, inline_stubs]
```

This also resolves **[SY-26]** (CC-2 — `inline_stubs` vs `composition_stubs` term) since the only occurrence is in the removed block.

- [ ] **Step 6: Verify no remaining `review_gate` references**

Run: `grep -rn 'review_gate' docs/superpowers/specs/skill-composability/`
Expected: no matches

- [ ] **Step 7: Verify no remaining `inline_stubs` references**

Run: `grep -rn 'inline_stubs' docs/superpowers/specs/skill-composability/`
Expected: no matches (only `composition_stubs` in foundations.md)

- [ ] **Step 8: Commit**

```bash
git add docs/superpowers/specs/skill-composability/spec.yaml docs/superpowers/specs/skill-composability/README.md
git commit -m "fix(spec): remediate 3 authority model findings from review round 11"
```

---

## Task 2 — P0 Verification Gaps (2 findings)

**Finding count:** 2 P0
**Findings:** SY-5, SY-6
**Files:** verification.md
**Depends on:** nothing — start immediately

### [SY-5] Corrupt durable file consumer path has no verification entry

**Source:** VR-1
**File:** verification.md — Consumer-side `write_failed` handling row (line 63)

The consumer-side contract for durable store lookup defines 6 ordered checks. Case (6) — `record_status: ok`, file exists, content corrupt — has no verification entry. Also missing: re-encounter rule (same corrupt content at level 3 → don't retry parse).

- [ ] **Step 1: Add test cases 4 and 5 to consumer-side verification row (line 63)**

After the existing test case `(3)` in the consumer-side `write_failed` handling row, append two additional test cases. Find the text ending with:
```
verify consumer does NOT attempt to read the file at `record_path` (even though it exists) and does NOT block.
```

Immediately before the closing `**Fixture setup:**` paragraph, insert:
```
(4) feedback capsule with `record_status: ok` + `record_path` pointing to an existing file whose content is corrupt (malformed YAML, truncated sentinel, or unparseable frontmatter) → consumer emits one-line prose warning including the `record_path` value + falls through to conversation-local sentinel scan (precedence level 3). **Fixture setup:** Pre-seed a durable file at a known `record_path` with corrupt content (e.g., truncated mid-field or invalid YAML). Emit a capsule with `record_path` set to this path and `record_status: ok`. **Pass criterion:** Consumer does NOT crash, does NOT block, and does NOT use the corrupt content — emits a diagnostic and falls through. (5) Re-encounter guard: same corrupt file at `record_path` is encountered at precedence level 3 (conversation-local scan also finds the corrupt sentinel) → consumer does NOT retry parse. **Fixture setup:** Use the same corrupt file from case (4). Inject the same corrupt sentinel into conversation context. **Pass criterion:** Consumer emits at most one warning (not two — no retry), and does NOT block.
```

### [SY-6] NS adapter `decomposition_seed: true` guard untested with no-recovery failure mode

**Source:** VR-3
**File:** verification.md — new deferred entry after NS adapter row (line 94)

Setting `decomposition_seed: true` when `--plan` was not active causes a false Step 0 case (c) abort with no recovery. No verification entry tests the adapter guard.

- [ ] **Step 2: Add deferred verification entry for NS adapter guard**

After the NS adapter verification row (the row starting with `NS adapter MUST set tautology_filter_applied` around line 94), add a new row to the table:

```
| NS adapter MUST NOT set `decomposition_seed: true` when `--plan` was not active | [pipeline-integration.md](pipeline-integration.md#two-stage-admission) | Validates: pipeline-integration.md §Two-Stage Admission (Stage B). **Deferred:** activation trigger — when NS composition stub is authored. Behavioral (when active): configure NS adapter with `--plan` not active, verify `decomposition_seed` is absent or `false` in the resulting `upstream_handoff`. Negative case: configure NS adapter with `--plan` not active, force `decomposition_seed: true` → verify downstream dialogue hits Step 0 case (c) abort. This is a P0 merge gate prerequisite — the stub MUST NOT pass co-review without this test. |
```

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/skill-composability/verification.md
git commit -m "fix(spec): remediate 2 P0 verification findings from review round 11"
```

---

## Task 3 — Contract Clarity: Dialogue-Resolved Design Decisions (7 findings)

**Finding count:** 7 P1
**Findings:** SY-3, SY-7, SY-8, SY-9, SY-10, SY-11, SY-23
**Files:** routing-and-materiality.md, capsule-contracts.md, pipeline-integration.md, foundations.md, lineage.md
**Depends on:** T1 (SY-11 cites governance `enforcement_mechanism` claim from T1)
**Dialogue:** All 7 resolutions from Codex thread `019d18aa-0c09-7683-958a-b92413367a28`

### [SY-3] Capability flag teardown — text fix (convergence, High confidence)

**Sources:** CE-4, IE-3, IE-9
**File:** routing-and-materiality.md:126 — Step 0 case (c) item (vii)

Step 0 case (c) says flags "MUST remain absent from pipeline state after rejection — no partial initialization." But Stage B has already set these flags before Step 0 fires. The correct semantics is teardown, not absence — symmetric with partial correction failure item (7).

- [ ] **Step 1: Fix Step 0 case (c) assertion (vii) in routing-and-materiality.md**

In the Step 0 case (c) post-abort assertions (line 126), find:
```
(vii) verify all `upstream_handoff` capability flags (`decomposition_seed`, `gatherer_seed`, `briefing_context`, `tautology_filter_applied`) remain absent from pipeline state after rejection — no partial initialization.
```

Replace with:
```
(vii) All `upstream_handoff` capability flags (`decomposition_seed`, `gatherer_seed`, `briefing_context`, `tautology_filter_applied`) MUST be torn down after rejection — flags set during Stage B MUST NOT persist into post-abort pipeline state. Both abort paths (Step 0 case (c) and partial correction failure) achieve the same end state: no capability flags in post-abort pipeline state.
```

- [ ] **Step 2: Fix the corresponding note in verification.md abort-path parity table**

In verification.md line 59, the partial correction failure row contains:
```
Step 0 requires physical absence (never initialized); partial correction failure requires teardown (flags set at Stage B are removed). Both achieve the same end state: no capability flags in post-abort pipeline state.
```

Replace with:
```
Both abort paths require teardown of flags set at Stage B. Both achieve the same end state: no capability flags in post-abort pipeline state. The pipeline ordering invariant (Stage B runs before Step 0) means case (c) always operates on initialized flags — "teardown" is the correct term for both paths.
```

### [SY-7] `review_target` is required for Contract 1 validity (convergence, High confidence)

**Source:** CE-1
**File:** capsule-contracts.md:41

`review_target` appears in the AR schema but not in the required or optional field lists. It is basis data for `subject_key` derivation — required at emission time, not optional.

- [ ] **Step 3: Add `review_target` to Contract 1 required fields**

In capsule-contracts.md line 41, find:
```
Required fields: `artifact_id`, `artifact_kind`, `lineage_root_id`, `created_at`, `subject_key`, `findings`.
```

Replace with:
```
Required fields: `artifact_id`, `artifact_kind`, `lineage_root_id`, `created_at`, `subject_key`, `review_target`, `findings`. `review_target` is basis data for `subject_key` derivation (see [lineage.md](lineage.md#basis-fields)) — without it, the capsule cannot mint a stable lineage key.
```

### [SY-8] Contract 3 inherits fallback diagnostic from foundations.md (convergence, High confidence)

**Source:** CE-2
**File:** capsule-contracts.md:160, foundations.md:44

foundations.md requires advisory/tolerant consumers to "emit a one-line prose diagnostic when falling back." Contract 3's consumer class definition omits this obligation.

- [ ] **Step 4: Add fallback diagnostic to Contract 3 consumer class**

In capsule-contracts.md line 160, find:
```
Advisory/tolerant. AR and NS validate the feedback capsule if present; fall back to conversation context if absent or invalid.
```

Replace with:
```
Advisory/tolerant. AR and NS validate the feedback capsule if present; fall back to conversation context if absent or invalid. When falling back, the consumer MUST emit a one-line prose diagnostic per [foundations.md](foundations.md#consumer-classes).
```

- [ ] **Step 5: Add verification row for Contract 3 fallback diagnostic**

In verification.md, after the standalone coherence row (line 69), add a new row to the Capsule Contract Verification table:

```
| AR and NS MUST emit prose diagnostic when falling back from feedback capsule | [capsule-contracts.md](capsule-contracts.md#consumer-class-contract-3), [foundations.md](foundations.md#consumer-classes) | Validates: capsule-contracts.md §Consumer Class Contract 3 + foundations.md §Consumer Classes. Behavioral: two test cases — (1) AR consuming absent feedback capsule → verify one-line prose diagnostic emitted before falling back to conversation context, (2) NS consuming invalid feedback capsule (missing required field) → verify prose diagnostic emitted. Parallel to Contract 1 NS fallback diagnostic test cases (2) and (3) in the AR capsule row above |
```

### [SY-9] Empty decomposition: vacuously true, subcase of case (a) (concession→convergence, High confidence)

**Source:** CE-3
**File:** routing-and-materiality.md:124, pipeline-integration.md:41

When decomposition produces zero items, `tautology_filter_applied:true` is vacuously satisfied — the filter stage completed over an empty domain. This is a subcase of existing Step 0 case (a), not a new precondition case.

- [ ] **Step 6: Add empty decomposition clarification to Step 0 case (a)**

In routing-and-materiality.md line 124, find:
```
- (a) If `upstream_handoff` exists and `tautology_filter_applied` is `true`: precondition satisfied — items were filtered during decomposition seeding.
```

Replace with:
```
- (a) If `upstream_handoff` exists and `tautology_filter_applied` is `true`: precondition satisfied — the tautology filter stage completed over the decomposition domain. This includes the empty-set subcase: when decomposition produces zero items, `tautology_filter_applied:true` means "the filter stage completed" (vacuously — zero items trivially pass all tiers), not "at least one item survived filtering." Materiality evaluation proceeds over zero items, producing `feedback_candidates: []` (explicit empty list, not field omission).
```

- [ ] **Step 7: Add clarification to pipeline-integration.md tautology_filter_applied description**

In pipeline-integration.md line 41, after the existing text about `tautology_filter_applied`, find the sentence:
```
The NS adapter MUST set this flag to `true` only after all three tautology filter tiers have been evaluated for all decomposition items during `handoff_enriched` mode.
```

After that sentence, insert:
```
When decomposition produces zero items, all three tiers are vacuously evaluated (no items to filter) — the adapter sets the flag to `true`. The flag means "the tautology filter stage completed over the decomposition domain," not "items survived filtering."
```

### [SY-10] AR write-failure: out of scope for v1 (convergence, Medium confidence)

**Source:** CE-5
**File:** capsule-contracts.md — AR schema area (around line 60), lineage.md:165

AR capsule has no `record_status` field. Write-failure is only contracted for dialogue feedback capsules.

- [ ] **Step 8: Add explicit out-of-scope declaration for AR write-failure**

In capsule-contracts.md, after the AR Design Notes section (around line 81), add:

```markdown

**AR `record_path` write-failure:** Out of scope for v1. `record_path` for AR capsules is optional best-effort metadata (`null` or a path to `docs/reviews/`). `null` is permitted to mean either "no write attempted" or "durable write not available." No `record_status` field is defined for AR capsules — the write-failure recovery contract (including `record_status: write_failed`) applies only to Contract 3 (dialogue feedback capsules) per [routing-and-materiality.md §Selective Durable Persistence](routing-and-materiality.md#selective-durable-persistence).
```

### [SY-11] Elevate `tautology_filter_applied` to conformance MUST (convergence, High confidence)

**Source:** CE-8
**File:** pipeline-integration.md:41, governance.md:20

governance.md escalates `tautology_filter_applied` key absence to a merge-blocking MUST. pipeline-integration.md treats absence as a debuggability preference. Resolution: elevate the normative source to match, making governance derivative of a normative MUST.

- [ ] **Step 9: Tighten pipeline-integration.md wording**

In pipeline-integration.md line 41, find the paragraph starting with:
```
**Functional note:** absence and explicit `false` are treated identically by the materiality evaluator
```

Replace the entire functional note paragraph with:
```
**Conformance requirement:** The NS adapter MUST emit `tautology_filter_applied` explicitly as `true` or `false` — key omission is a conformance violation. The materiality evaluator MUST treat omission equivalently to `false` if malformed state is encountered (defensive recovery), but omission is not a valid adapter output. Explicit `false` is required for conformance and debuggability, not runtime branching — the evaluator's defensive recovery does not make omission acceptable. **Enforcement surface:** [governance.md §Stub Composition Co-Review Gate](governance.md#stub-composition-co-review-gate) enforces key-presence as a merge-blocking gate, citing this clause.
```

### [SY-23] `supersedes`: emitter-required, consumer-absent-as-null (concession→convergence, High confidence)

**Source:** CE-9
**File:** capsule-contracts.md:221, lineage.md:115

`supersedes` is listed as optional in Contract 3 validity, but the minting rule in lineage.md requires emitters to always set it. Resolution: emitters MUST include `supersedes`; consumers MUST treat absent key as null for v1 validity.

- [ ] **Step 10: Add supersedes compatibility rule to capsule-contracts.md**

In capsule-contracts.md, after the Contract 3 optional field absence paragraph (around line 225), add:

```markdown

**`supersedes` field compatibility (all three contracts):** Emitters MUST include `supersedes` in every capsule and set it to either the prior `artifact_id` of the same kind and subject, or `null` (per the minting rule in [lineage.md §DAG Structure](lineage.md#dag-structure)). Consumers MUST treat an absent `supersedes` key as equivalent to `supersedes: null` for v1 validity — absent `supersedes` does NOT make the capsule invalid. This is a narrow field-specific compatibility exception for `supersedes` only, not a broad reclassification of "optional" semantics. Governance and conformance tooling SHOULD still flag `supersedes` omission as an emitter defect (the minting rule is a MUST).
```

- [ ] **Step 11: Verify Contract 1 and Contract 2 optional field lists include `supersedes`**

Confirm `supersedes` appears in the optional lists for Contract 1 (line 41) and Contract 2 (line 93). It already does — no edit needed, but verify.

Run: `grep -n 'supersedes' docs/superpowers/specs/skill-composability/capsule-contracts.md`
Expected: `supersedes` appears in all three schema blocks AND in all three optional field lists.

- [ ] **Step 12: Commit**

```bash
git add docs/superpowers/specs/skill-composability/routing-and-materiality.md \
  docs/superpowers/specs/skill-composability/capsule-contracts.md \
  docs/superpowers/specs/skill-composability/pipeline-integration.md \
  docs/superpowers/specs/skill-composability/verification.md
git commit -m "fix(spec): remediate 7 contract clarity findings from review round 11"
```

---

## Task 4 — Verification Table + Editorial Batch (12 findings)

**Finding count:** 6 P1, 6 P2
**Findings:** SY-12, SY-13, SY-14, SY-15, SY-16, SY-24, SY-27, SY-28, SY-29, SY-30, SY-31, SY-32
**Files:** verification.md, routing-and-materiality.md, capsule-contracts.md, decisions.md, README.md
**Depends on:** nothing — start immediately

### [SY-13] Validator check #2 says "All 3 sentinels" but registry has 4 (P1)

**Source:** CC-1
**File:** verification.md — `validate_composition_contract.py` acceptance criteria (grep for "All 3 sentinels")

The internal-only `dialogue-orchestrated-briefing` sentinel is implicitly excluded.

- [ ] **Step 1: Add "external" qualifier to sentinel count**

Find the acceptance criterion referencing "All 3 sentinels" and change to:
```
All 3 external sentinels (excluding internal-only `dialogue-orchestrated-briefing`)
```

### [SY-14] Combined budget/override indeterminate prose warning not verified (P1)

**Source:** VR-2
**File:** verification.md — Budget indeterminate state row (line 89)

Individual indeterminate states are tested. The combined state (both counter and override unavailable) has specific required prose with no test.

- [ ] **Step 2: Add combined indeterminate verification entry**

After the budget override row (line 90), add a new row:

```
| Combined budget/override indeterminate: both counter and override state unavailable | [routing-and-materiality.md](routing-and-materiality.md#budget-enforcement-mechanics) | Validates: routing-and-materiality.md §Budget Enforcement Mechanics. Behavioral: dialogue test — pre-seed a feedback capsule with `lineage_root_id` but NO upstream AR/NS artifacts (counter indeterminate), AND simulate context compression that removed a prior "continue" turn (override indeterminate). Verify (1) budget treated as not-exhausted, (2) prose warning emitted referencing both indeterminate sources (budget counter AND override state), matching the specific combined prose text in routing-and-materiality.md |
```

### [SY-15] Interim Protocol items 6-7 not mirrored in Routing Verification table (P1)

**Source:** VR-5
**File:** verification.md — Routing and Materiality Verification table, correction rule ordering row (line 79) and upstream-source boundary row

Protocol item 7 (upstream-source routing boundary) maps to a table row with no "Interim:" tag.

- [ ] **Step 3: Add Interim tags to applicable verification rows**

In the correction rule ordering row (line 79), after the existing "**Interim:**" line, verify it references "§Interim Materiality Verification Protocol item 6."

In the upstream-source routing boundary row (line 102), add at the end:
```
**Interim:** Manual walk-through per §Interim Materiality Verification Protocol item 7. Active P0 gate.
```

### [SY-16] Thread continuation scenario 9 infeasible (P1)

**Source:** VR-6
**File:** verification.md — Thread continuation row (line 103), scenario (9)

Asserting `thread_id` absence from the Codex API call requires API-level introspection unavailable in a skill context.

- [ ] **Step 4: Reclassify scenario 9 as structural check**

In verification.md line 103, find scenario `(9)` text starting with:
```
(9) Fresh start required (new artifact detected) — verify Codex API call does NOT include prior `thread_id`:
```

After the existing text of scenario (9), append:
```
**Infeasibility acknowledgment:** Asserting `thread_id` absence from the Codex API call requires API-level parameter introspection unavailable in a skill context. Reclassify as structural check: verify the stub code path for fresh-start (new artifact detected) does not pass a prior `thread_id` to the Codex tool call. Verify by reviewing the tool-call construction code, not by intercepting the API call. Parallel to other infeasible tests (e.g., `chmod 000`, partial-tier injection) that are explicitly reclassified elsewhere in this table.
```

### [SY-30] `lineage_root_id` test lacks regression classification (P2)

**Source:** VR-7
**File:** verification.md — `lineage_root_id` immutability row (line 112)

- [ ] **Step 5: Add regression classification**

In verification.md line 112, append to the `lineage_root_id` immutability row:
```
**Regression classification:** Required permanent regression test — MUST be included in the standing test suite and re-run on any PR touching key propagation or capsule minting logic.
```

### [SY-31] `materiality_source: null/typo` tests SHOULD vs MUST (P2)

**Source:** VR-8
**File:** verification.md — `material`/`suggested_arc` coherence row (line 57)

The test says "Test SHOULD also cover `materiality_source: null` and `materiality_source: <typo>`" but the normative source uses MUST for `materiality_source ∈ {rule, model}`.

- [ ] **Step 6: Upgrade SHOULD to MUST**

In verification.md line 57, find:
```
Test SHOULD also cover `materiality_source: null` and `materiality_source: <typo>`
```

Replace with:
```
Test MUST also cover `materiality_source: null` and `materiality_source: <typo>`
```

### [SY-32] Standalone coherence instrument overstates coverage (P2)

**Source:** VR-9
**File:** verification.md — Standalone coherence row (line 69)

The standalone coherence test claims 3 scenarios but dialogue assertion (4) (`dialogue-orchestrated-briefing` not externalized) is deferred.

- [ ] **Step 7: Add deferred qualifier**

In verification.md line 69, find:
```
verify: (4) `<!-- dialogue-orchestrated-briefing -->` does not appear anywhere in the emitted output
```

After this assertion, append:
```
(dialogue assertion 4 coverage is deferred until the dialogue composition stub is authored — the stub must be present for the externalization check to be meaningful)
```

### [SY-12] Completeness proof "ambiguous" framing misleading (P2)

**Source:** CE-10
**File:** routing-and-materiality.md:93 — completeness proof

`ambiguous` appears in the proof as a valid pass-through, but readers may misinterpret it as always-invalid.

- [ ] **Step 8: Add clarifying parenthetical**

In routing-and-materiality.md line 93, find:
```
The 2 `material: true` + `suggested_arc: ambiguous` tuples (`diagnosis/true/ambiguous` and `planning/true/ambiguous`) are valid pass-throughs
```

After "valid pass-throughs" insert:
```
(`ambiguous` is only invalid under `material: false`, where rule 1 corrects it to `dialogue_continue`)
```

### [SY-24] `record_path` non-null MUST stated in three files (P2)

**Source:** CE-11
**File:** capsule-contracts.md:237

The `record_path` non-null MUST is stated in routing-and-materiality.md (normative authority), capsule-contracts.md, and lineage.md. Capsule-contracts.md should defer to the normative source.

- [ ] **Step 9: Demote capsule-contracts.md record_path to cross-reference**

In capsule-contracts.md line 237, find:
```
- `record_path` MUST be non-null for feedback capsules. See [routing-and-materiality.md#selective-durable-persistence](routing-and-materiality.md#selective-durable-persistence) for the normative enforcement rule, write-failure recovery procedure (including the `record_path`-to-intended-path requirement on failure), and consumer-side contract.
```

Replace with:
```
- `record_path` non-null requirement for feedback capsules: see [routing-and-materiality.md §Selective Durable Persistence](routing-and-materiality.md#selective-durable-persistence) (normative authority for the enforcement rule, write-failure recovery, and consumer-side contract).
```

### [SY-27] Duplicate terminal phrase in §No Auto-Chaining (P2)

**Source:** CC-3
**File:** routing-and-materiality.md:196

- [ ] **Step 10: Remove trailing duplicate sentence**

In routing-and-materiality.md line 196, find the duplicate sentence at the end of the capsule-level prohibition paragraph. The sentence "These fields inform the hop suggestion text presented to the user only, not an automatic dispatch." appears after the main prohibition text that already covers this point. Remove the trailing duplicate.

### [SY-28] Orphaned duplicate parenthetical in D2 (P2)

**Source:** CC-4
**File:** decisions.md:22

- [ ] **Step 11: Remove trailing parenthetical in D2**

In decisions.md line 22, find:
```
(Advisory/tolerant: validate if present, fall back to alternative source if absent or invalid.)
```

Remove this trailing parenthetical — it duplicates the preceding sentence.

### [SY-29] README pipeline description omits items from spec.yaml (P2)

**Source:** CC-5
**File:** README.md

- [ ] **Step 12: Align README descriptions with spec.yaml**

Verify the README authority table descriptions (lines 16-27) match spec.yaml authority descriptions. Specifically check that:
- `routing` row mentions "feedback persistence" (present in spec.yaml:22 but may be abbreviated in README)
- `pipeline` row mentions "pipeline threading" (present in spec.yaml:18)

Fix any omissions to match spec.yaml descriptions.

- [ ] **Step 13: Commit**

```bash
git add docs/superpowers/specs/skill-composability/verification.md \
  docs/superpowers/specs/skill-composability/routing-and-materiality.md \
  docs/superpowers/specs/skill-composability/capsule-contracts.md \
  docs/superpowers/specs/skill-composability/decisions.md \
  docs/superpowers/specs/skill-composability/README.md
git commit -m "fix(spec): remediate 12 verification + editorial findings from review round 11"
```

---

## Task 5 — Governance + Delivery Enforcement Repairs (4 findings)

**Finding count:** 3 P1, 1 P2
**Findings:** SY-2, SY-17, SY-18, SY-34
**Files:** governance.md, delivery.md, verification.md
**Depends on:** T1 (governance claims must be valid)

### [SY-2] No-auto-chaining helper-mediated gap — no behavioral test or closure timeline

**Sources:** CE-6, IE-1
**File:** delivery.md:55, verification.md

The helper-mediated indirect delegation gap has no behavioral test. Grep-based CI cannot detect indirect delegation through helpers.

- [ ] **Step 1: Add behavioral test reference to delivery.md**

In delivery.md line 55, find:
```
deeper static analysis is deferred to `validate_composition_contract.py` (item #6).
```

After this sentence, append:
```
`validate_composition_contract.py` acceptance criteria MUST include (item #6 scope): behavioral test for helper functions listed in `COMPOSITION_HELPERS.md` — verify no listed function delegates to another skill via model output or helper delegation chains.
```

### [SY-17] `budget_override_pending` initialization — no enforcement gate

**Source:** IE-4
**File:** governance.md, delivery.md

The MUST for `budget_override_pending` initialization to `false` at stub entry has no verification path.

- [ ] **Step 2: Add governance checklist item**

In governance.md, after the Thread Freshness section (line 60), add:

```markdown

## `budget_override_pending` Initialization Check

Validates: routing-and-materiality.md §Budget Enforcement Mechanics (initialization invariant)

PR checklist item: "Confirmed: `budget_override_pending` is explicitly initialized to `false` at dialogue stub entry — not left to default-falsy behavior. Verified by reviewing the initialization code path at stub entry point."
```

### [SY-18] Governance gates dormant until artifacts exist

**Source:** IE-5
**File:** delivery.md — Skill Text Changes section (line 10)

Governance gates reference composition contract, `COMPOSITION_HELPERS.md`, and stubs — none exist yet. No activation mechanism.

- [ ] **Step 3: Add activation checklist to delivery.md**

After the Skill Text Changes table (line 17), add:

```markdown

### Governance Gate Activation Checklist

Governance gates in [governance.md](../skill-composability/governance.md) become active when their referenced artifacts are first created. When authoring any of the following, the PR MUST confirm the corresponding governance gates are applied:

| Artifact | Gates Activated |
|----------|----------------|
| Composition contract (`composition-contract.md`) | Contract Marker Verification, `topic_key` Scope Guard |
| Composition stubs (AR, NS, dialogue) | Stub Composition Co-Review, Helper Function Tracking, Constrained Field Literal-Assignment, `budget_override_pending` Initialization |
| `COMPOSITION_HELPERS.md` | Helper Function Tracking (diffing requirement) |
```

### [SY-34] No-auto-chaining grep scope excludes contract until authored

**Source:** IE-12
**File:** verification.md — No auto-chaining row (line 92)

The grep CI check file scope should explicitly require enabling when the composition contract is authored.

- [ ] **Step 4: Add authoring-PR requirement**

In verification.md line 92, find the file scope list:
```
`adversarial-review/SKILL.md`, `next-steps/SKILL.md`, `dialogue/SKILL.md` (composition stub blocks), `packages/plugins/cross-model/references/composition-contract.md` (when authored), and `COMPOSITION_HELPERS.md` (when present).
```

After this list, append:
```
The PR that creates `composition-contract.md` MUST enable the grep check for the contract file in CI configuration — the check is not activated retroactively.
```

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/skill-composability/governance.md \
  docs/superpowers/specs/skill-composability/delivery.md \
  docs/superpowers/specs/skill-composability/verification.md
git commit -m "fix(spec): remediate 4 governance + delivery findings from review round 11"
```

---

## Task 6 — hold_reason Enforcement Cluster (3 findings)

**Finding count:** 2 P1, 1 P2
**Findings:** SY-4, SY-19, SY-33
**Files:** routing-and-materiality.md, verification.md
**Depends on:** T3 (normative contracts stable)
**Cluster:** Cluster A from synthesis (three independent gaps in the `hold_reason` enforcement surface)

### [SY-4] `hold_reason` interim verification/activation gaps

**Sources:** VR-4, IE-10
**File:** verification.md — Interim Protocol, `hold_reason` grep check

The `hold_reason` emission-time gate is not covered by the Interim Protocol. The grep CI check has no activation statement.

- [ ] **Step 1: Add item 8 to Interim Protocol**

In verification.md, after item 7 of the Interim Materiality Verification Protocol (line 40), add:

```
8. The `hold_reason` emission-time gate: verify `hold_reason ∈ {routing_pending, null}` for every `unresolved[]` entry. Inject one `unresolved[]` entry with `hold_reason: invalid_value` → verify gate corrects to `null` and emits structured warning containing the original value.
```

- [ ] **Step 2: Add activation statement to `hold_reason` grep check**

In verification.md line 61, the `hold_reason` grep-based CI enforcement row, append:
```
**Activation:** Active immediately for stub authoring PRs. Not deferred to the validator.
```

### [SY-19] `hold_reason` non-overwrite invariant — no enforcement

**Source:** IE-6
**File:** verification.md, routing-and-materiality.md:52

The precedence rule (routing-stage assignment is authoritative; capsule assembly MUST NOT overwrite) has no test.

- [ ] **Step 3: Add behavioral test to verification.md**

After the `hold_reason` emission-time gate row (line 66), add a new row:

```
| `hold_reason` routing-stage assignment MUST NOT be overwritten by capsule assembly | [routing-and-materiality.md](routing-and-materiality.md#ambiguous-item-behavior) | Validates: routing-and-materiality.md §Ambiguous Item Behavior (assignment precedence). Behavioral: inject a held ambiguous item with `hold_reason: routing_pending` set at routing stage → verify `hold_reason` value survives capsule assembly unchanged. The test asserts the final emitted `hold_reason` equals the routing-stage value — capsule assembly MUST NOT clear, replace, or default over an existing `routing_pending` value |
```

### [SY-33] Emission-time steps 2-4 ordering unspecified

**Source:** IE-2
**File:** routing-and-materiality.md:97

The processing order per entry says steps 2-4 are applied after the correction pipeline, but doesn't specify they must be evaluated in listed order.

- [ ] **Step 4: Add ordering requirement**

In routing-and-materiality.md line 97, find:
```
**Processing order per entry:** (1) Apply ordered correction rules 1-5
```

After "(4) Apply `hold_reason` validation", append:
```
Steps 2, 3, and 4 MUST be evaluated in listed order (2, then 3, then 4). While all three are independently recoverable (no step depends on the outcome of another), consistent ordering is required for reproducible diagnostic output — a structured warning from step 2 must appear before step 3's warning in the log.
```

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/skill-composability/routing-and-materiality.md \
  docs/superpowers/specs/skill-composability/verification.md
git commit -m "fix(spec): remediate 3 hold_reason enforcement findings from review round 11"
```

---

## Task 7 — record_path Enforcement Chain (2 findings)

**Finding count:** 2 P1
**Findings:** SY-20, SY-22
**Files:** verification.md, delivery.md
**Depends on:** T3 (normative contracts stable)
**Cluster:** Cluster B from synthesis (gaps in the `record_path` enforcement chain)

### [SY-20] Consumer-side 5-step check ordering — no enforcement gate

**Source:** IE-7
**File:** verification.md

The strict ordering (nullity → existence → presence → value → integrity) is normative but only verified by outcome.

- [ ] **Step 1: Add structural check to deferred verification**

In delivery.md open items, after item 8 (line 52), add:

```
| 10 | Consumer-side 5-step check ordering structural verification | Deferred | Add to `validate_composition_contract.py` scope: verify consumer code implements the 5-step durable store check in strict sequential order (nullity → existence → presence → value → integrity) with explicit short-circuit at each step. Activation: when consumer stub code is authored. |
```

### [SY-22] `record_path` null-prevention gap for path construction failure

**Source:** IE-11
**File:** delivery.md, governance.md

Happy-path and write-failure are covered. Path construction failure (exception before write attempt) is not.

- [ ] **Step 2: Add structural review checklist item to governance.md**

In governance.md, after the `record_path` Pre-Computation Ordering Check section (line 54), add:

```markdown

## `record_path` Null-Prevention Review

Validates: capsule-contracts.md §Schema Constraints (`record_path` non-null requirement)

PR checklist item: "Confirmed: no null or uninitialized state is reachable for `record_path` from any emission path. Verified by tracing all code paths from capsule assembly entry to `record_path` assignment — including exception paths before write attempt (path construction failure). The path variable is assigned before any operation that could throw."
```

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/skill-composability/delivery.md \
  docs/superpowers/specs/skill-composability/governance.md
git commit -m "fix(spec): remediate 2 record_path enforcement findings from review round 11"
```

---

## Task 8 — Thread Continuation Structural Enforcement (1 finding)

**Finding count:** 1 P1
**Findings:** SY-21
**Files:** delivery.md
**Depends on:** T3 (normative contracts stable)
**Cluster:** Cluster C from synthesis (thread continuation enforcement)

### [SY-21] Thread continuation timestamp comparison — no automated structural enforcement

**Source:** IE-8
**File:** verification.md, delivery.md

Behavioral regression tests (7) and (8) verify specific inputs but not the structural property (parsed numeric comparison).

- [ ] **Step 1: Add static analysis check to delivery.md**

In delivery.md open items, after item 10 (added in T7), add:

```
| 11 | Thread continuation parsed-numeric enforcement | Deferred | Add to `validate_composition_contract.py` scope: static analysis check that thread continuation comparison code uses parsed numeric timestamps (millisecond precision), not string comparison. Activation: when dialogue stub's thread continuation code is authored. Cross-reference: verification.md scenarios (7) and (8) provide behavioral regression tests; this item adds structural enforcement that the implementation uses parsed comparison, not just that specific inputs produce correct output. |
```

- [ ] **Step 2: Commit**

```bash
git add docs/superpowers/specs/skill-composability/delivery.md
git commit -m "fix(spec): remediate 1 thread continuation enforcement finding from review round 11"
```

---

## Finding Coverage Matrix

| SY # | Priority | Task | Status |
|------|----------|------|--------|
| SY-1 | P1 | T1 | Steps 1-4 |
| SY-2 | P1 | T5 | Step 1 |
| SY-3 | P1 | T3 | Steps 1-2 |
| SY-4 | P1 | T6 | Steps 1-2 |
| SY-5 | P0 | T2 | Step 1 |
| SY-6 | P0 | T2 | Step 2 |
| SY-7 | P1 | T3 | Step 3 |
| SY-8 | P1 | T3 | Steps 4-5 |
| SY-9 | P1 | T3 | Steps 6-7 |
| SY-10 | P1 | T3 | Step 8 |
| SY-11 | P1 | T3 | Step 9 |
| SY-12 | P2 | T4 | Step 8 |
| SY-13 | P1 | T4 | Step 1 |
| SY-14 | P1 | T4 | Step 2 |
| SY-15 | P1 | T4 | Step 3 |
| SY-16 | P1 | T4 | Step 4 |
| SY-17 | P1 | T5 | Step 2 |
| SY-18 | P1 | T5 | Step 3 |
| SY-19 | P1 | T6 | Step 3 |
| SY-20 | P1 | T7 | Step 1 |
| SY-21 | P1 | T8 | Step 1 |
| SY-22 | P1 | T7 | Step 2 |
| SY-23 | P1 | T3 | Steps 10-11 |
| SY-24 | P2 | T4 | Step 9 |
| SY-25 | P2 | T1 | Step 5 |
| SY-26 | P2 | T1 | Step 5 (resolved by SY-25 removal) |
| SY-27 | P2 | T4 | Step 10 |
| SY-28 | P2 | T4 | Step 11 |
| SY-29 | P2 | T4 | Step 12 |
| SY-30 | P2 | T4 | Step 5 |
| SY-31 | P2 | T4 | Step 6 |
| SY-32 | P2 | T4 | Step 7 |
| SY-33 | P2 | T6 | Step 4 |
| SY-34 | P2 | T5 | Step 4 |
