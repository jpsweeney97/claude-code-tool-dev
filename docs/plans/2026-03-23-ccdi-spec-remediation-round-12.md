# CCDI Spec Remediation Plan — Round 12

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate 30 findings (1 P0, 18 P1, 11 P2) from the 5-reviewer spec review of `docs/superpowers/specs/ccdi/`

**Architecture:** Six tasks in two phases fix all findings in spec files, grouped by edit-locality and causal dependency. Tasks 1–4 are parallel (non-overlapping file sections). Task 5 depends on Task 1 (references shadow_adjusted_yield test rows). Task 6 (P2 batch) collects remaining P2s after all P1s land.

**Tech Stack:** Markdown spec edits only — no code changes

**Source:** `.review-workspace/synthesis/report.md` (5-reviewer team, 2026-03-23)
**Scope:** 30 canonical findings (1 P0, 18 P1, 11 P2) across 8 normative files + spec.yaml
**Spec:** `docs/superpowers/specs/ccdi/` (10 files, 8 normative + 1 supporting + spec.yaml)

---

## Strategy

Six tasks in two phases, ordered by dependency and edit-locality:

1. **Phase 1** — Four tasks, all parallel (touch non-overlapping sections of shared files):
   - **T1:** P0 + schema completeness (1 P0, 3 P1, 1 P2) — data-model.md schema defaults/counts, delivery.md graduation schema + tests, registry.md TTL lifecycle
   - **T2:** CLI flag corrections (3 P1, 1 P2) — integration.md Step 5.5/7.5 flag additions, delivery.md replay harness
   - **T3:** Authority boundary fixes (5 P1) — data-model.md disclaimers, decisions.md language, integration.md pipeline isolation, spec.yaml precedence chain, delivery.md enum scope
   - **T4:** Mechanical cross-reference + term fixes (3 P1, 1 P2) — registry.md anchor, integration.md heading + key count, delivery.md config key

2. **Phase 2** — Two tasks, parallel (non-overlapping delivery.md sections):
   - **T5:** Verification gap remediation (4 P1) — delivery.md test specifications (depends on T1 for shadow_adjusted_yield test names)
   - **T6:** P2 batch (8 P2) — all remaining P2 findings across multiple files

**Dependency chain:**
1. T1 → T5: SY-16 (acknowledged test gaps remediation gate) should reference the shadow_adjusted_yield test rows added by SY-1 in T1
2. T2 → T6 (weak): SY-20 (replay harness) in T2 establishes the --inventory-snapshot fix pattern that T6's delivery.md P2s should not contradict

**Edit-locality map** (sections each task touches, confirming no Phase 1 conflicts):

| File | T1 | T2 | T3 | T4 |
|------|:--:|:--:|:--:|:--:|
| data-model.md | §Schema Evolution (L70), §RegistrySeed (L305–340) | — | §RegistrySeed Informative disclaimers | — |
| delivery.md | §graduation.json schema (L156), §test_validate_graduation (L183) | §replay fixtures (L710–754) | §graduation.json status enum | §Layer 2b config (L699) |
| integration.md | — | §Step 5.5/7.5 CLI calls | §Pipeline Isolation Invariants | §shadow-mode heading (L448), §ccdi_trace (L307) |
| registry.md | §TTL Lifecycle (L144) | — | — | §field-update-rules link (L106) |
| decisions.md | — | — | §Normative Decision Constraints | — |
| spec.yaml | — | — | claim_precedence.decision_record | — |

**Commit strategy:**
1. `fix(spec): remediate P0 shadow_adjusted_yield + 3 P1 schema findings from review round 12` (T1)
2. `fix(spec): remediate 3 P1 CLI flag omission findings from review round 12` (T2)
3. `fix(spec): remediate 5 P1 authority boundary findings from review round 12` (T3)
4. `fix(spec): remediate 3 P1 cross-reference + term drift findings from review round 12` (T4)
5. `fix(spec): remediate 4 P1 verification gap findings from review round 12` (T5)
6. `fix(spec): remediate 11 P2 findings from review round 12` (T6)

---

## Task 1 — P0 + Schema Completeness (5 findings)

**Finding count:** 1 P0, 3 P1, 1 P2
**Files:** delivery.md, data-model.md, registry.md
**Depends on:** nothing — start immediately
**Corroboration:** SY-3 has independent_convergence (CC-3 + CE-8)

### [SY-1] P0: `shadow_adjusted_yield` absent from graduation.json schema — kill criterion unverifiable

**Sources:** VR-1, VR-5
**Files:** delivery.md

The normative kill criterion for shadow-mode graduation has no field in the graduation.json schema, no validator enforcement, and no test coverage. All 16 `test_validate_graduation.py` tests check only `effective_prepare_yield`.

- [ ] Add `shadow_adjusted_yield` field to the `graduation.json` schema example at delivery.md line 156. Mark as required when `status: "approved"` and shadow dialogues were conducted.
- [ ] Add `test_validate_graduation.py` row: "Approved status with `shadow_adjusted_yield` below 40% threshold → Exit 1"
- [ ] Add `test_validate_graduation.py` row: "Approved status with valid `shadow_adjusted_yield` and valid `effective_prepare_yield` → Exit 0"
- [ ] Add validation description (parallel to `effective_prepare_yield` validation at lines 163–164): "validates that `shadow_adjusted_yield` is consistent with `repeat_detections_from_missing_deferral` and `packets_prepared` from per-dialogue diagnostics, subject to the freshness guardrail check"
- [ ] Update `test_shadow_freshness_guardrail.py` description to reference the now-existing `shadow_adjusted_yield` field in the schema

### [SY-5] P1: `last_seen_turn` schema default `null` conflicts with `integer` type

**Sources:** SP-2
**Files:** data-model.md

Migration fallback `null` on a non-nullable `integer` field. Adjacent `last_injected_turn` explicitly uses `integer | null` union; `last_seen_turn` does not.

- [ ] In data-model.md §Schema Evolution Constraint defaults table (line 70), change `last_seen_turn` default from `null` to `0`
- [ ] Add inline note: "Default `0` is consistent with `first_seen_turn` defaulting to `0` and avoids null-handling in integer consumers"

### [SY-4] P1: `deferred_ttl: 0` recovery ordering ambiguity

**Sources:** SP-1
**Files:** registry.md, data-model.md

If the standard decrement rule runs before the TTL-expired transition check on a loaded `deferred_ttl: 0` entry, the value becomes -1 and the `== 0` transition never fires.

- [ ] In registry.md §TTL Lifecycle (line 144), add explicit load-time handling: "When loading a registry file containing a `deferred_ttl: 0` entry, the `dialogue-turn` implementation MUST apply the transition rule (§deferred → detected/deferred) BEFORE the standard per-turn decrement step. Do NOT decrement a `deferred_ttl` that is already `0` at load time."
- [ ] In data-model.md §Failure Modes (line 473), add cross-reference to the new registry.md ordering clause: "See registry.md#ttl-lifecycle for the required evaluation order"

### [SY-3] P1: RegistrySeed claims "four" envelope fields but schema defines five

**Sources:** CC-3, CE-8 (independent convergence)
**Files:** data-model.md

Both reviewers independently found that lines 320 and 322 omit `inventory_snapshot_path`.

- [ ] At data-model.md line 320, update to: "owns the RegistrySeed envelope schema (`entries`, `docs_epoch`, `inventory_snapshot_version`, `results_file`, `inventory_snapshot_path`)"
- [ ] At data-model.md line 322, update "four" to "five" and add `inventory_snapshot_path` to the field list

### [SY-24] P2: Non-nullable always-present field enumeration omits 5 core identity fields

**Sources:** SP-3
**Files:** data-model.md

- [ ] At data-model.md line 340, expand the "This includes" list to explicitly enumerate ALL non-nullable fields: add `topic_key`, `family_key`, `state`, `first_seen_turn`, `last_seen_turn` alongside the existing `kind`, `coverage_target`, `facet`, `consecutive_medium_count`, and `coverage.*` sub-fields
- [ ] Change "This includes" to "These are" to make the list unambiguously exhaustive

---

## Task 2 — CLI Flag Corrections (4 findings)

**Finding count:** 3 P1, 1 P2
**Files:** integration.md, delivery.md
**Depends on:** nothing — start immediately

### [SY-2] P1: Systematic `--inventory-snapshot` omission across mid-dialogue flow

**Sources:** CE-1, CE-2, CE-3, CE-4
**Files:** integration.md

Four CLI call sites in the mid-dialogue flow use `--registry-file` without the required `--inventory-snapshot`. Per footnote ‡, omitting this flag triggers non-zero exit before any other validation.

- [ ] integration.md Step 5.5 `dialogue-turn` call: add `--inventory-snapshot <ccdi_snapshot_path>`
- [ ] integration.md Step 5.5 target-mismatch `build-packet --mark-deferred` calls (both active and shadow branches): add `--inventory-snapshot <ccdi_snapshot_path>`
- [ ] integration.md Step 5.5 scout-priority `build-packet --mark-deferred` calls (both active and shadow branches): add `--inventory-snapshot <ccdi_snapshot_path>`
- [ ] integration.md Step 7.5 commit-phase `build-packet --mark-injected` call: add `--inventory-snapshot <ccdi_snapshot_path>`
- [ ] After adding all 4 sites, verify no other `--registry-file` usage in integration.md omits `--inventory-snapshot` (grep for `--registry-file` and confirm each occurrence has the companion flag)

### [SY-6] P1: `dialogue-turn` never passes `--shadow-mode` in shadow mode

**Sources:** CE-5
**Files:** integration.md

Step 5.5 `dialogue-turn` shows no `--shadow-mode` branching, unlike `build-packet` calls.

- [ ] In integration.md Step 5.5, add conditional `--shadow-mode` flag to the `dialogue-turn` invocation, matching the active/shadow branching pattern used by `build-packet` calls

### [SY-7] P1: `skip_scout` description contradicts implementation flow

**Sources:** CE-6
**Files:** integration.md

Prose says the `--mark-deferred scout_priority` call "is not made" in shadow mode; Step 5.5 shows it IS made with `--shadow-mode`.

- [ ] Correct the `skip_scout` action description to match the Step 5.5 flow: the call IS made in shadow mode with `--shadow-mode` appended as a CLI backstop for cooldown deferral suppression

### [SY-20] P2: Replay harness inherits `--inventory-snapshot` omission

**Sources:** CE-9
**Files:** delivery.md

- [ ] In delivery.md replay harness execution model, add `--inventory-snapshot` to CLI call patterns that use `--registry-file`, matching the integration.md corrections from SY-2

---

## Task 3 — Authority Boundary Fixes (5 findings)

**Finding count:** 5 P1
**Files:** data-model.md, decisions.md, integration.md, delivery.md, spec.yaml
**Depends on:** nothing — start immediately

### [SY-9] P1: data-model.md `(Informative)` disclaimers on sections with normative MUST-strength content

**Sources:** AA-4
**Files:** data-model.md

RegistrySeed and Live Registry File Schema sections carry blanket `(Informative)` disclaimers but contain normative persistence_schema MUST constraints not stated in integration.md.

- [ ] Replace the blanket `(Informative — behavioral authority: integration.md)` disclaimers with scoped annotations that distinguish: (1) informative behavioral narrative → "Behavioral authority: integration.md", (2) normative persistence_schema content (null-field serialization, transport-only field stripping, FIFO ordering) → remove the informative label, as these are normative under data-model.md's own `persistence_schema` claim

### [SY-10] P1: decisions.md states behavioral invariants normatively despite cross-reference-only intent

**Sources:** AA-5
**Files:** decisions.md

Preamble says component contracts outrank it and rows are "cross-references only," but the invariant column uses normative MUST NOT phrasing.

- [ ] Reformulate the invariant column entries from direct normative statements ("MUST NOT produce false-positive detections") to cross-references: "See classifier.md#false-positive-prevention" or "Enforced by: classifier.md §False-Positive Prevention"
- [ ] Keep the preamble's claim that component contracts are authoritative, making this purely a referencing aid

### [SY-11] P1: integration.md §Pipeline Isolation Invariants — 2 of 6 invariants not in decisions.md

**Sources:** AA-6
**Files:** integration.md, decisions.md

Section header claims "subset cross-referenced from decisions.md" but sentinel structure and shadow-mode commitment prohibition have no matching decisions.md row.

- [ ] **Option A (preferred):** Add rows to decisions.md for the two orphan invariants (sentinel structure, shadow-mode commitment prohibition), making the cross-reference claim accurate
- [ ] **Option B:** Change integration.md section header from "subset cross-referenced from decisions.md" to "behavioral invariants (some cross-referenced from decisions.md)" to make the scope claim accurate
- [ ] Whichever option, verify all 6 invariant items in integration.md §Pipeline Isolation Invariants are accounted for

### [SY-12] P1: `delivery` in `decision_record` claim_precedence chain with no decision_record content

**Sources:** AA-2
**Files:** spec.yaml

- [ ] In spec.yaml `claim_precedence.decision_record`, remove `delivery` from the authority list `[decisions, foundation, delivery]` → `[decisions, foundation]`
- [ ] Verify no other claim_precedence or fallback_authority_order entry relies on delivery for decision_record resolution

### [SY-8] P1: graduation.json status enum — open vs closed behavioral conflict

**Sources:** CE-7
**Files:** delivery.md

delivery.md says unknown status values "MUST be rejected" (closed enum); integration.md says the enum is intentionally open. Per claim_precedence, integration.md is authoritative for behavior_contract.

- [ ] Scope delivery.md's "MUST reject unknown status values" constraint to `validate_graduation.py` specifically: "The validator tool (`validate_graduation.py`) MUST reject unknown status values. The runtime gate (integration.md §Shadow-mode Graduation) is intentionally permissive of enum expansion per integration.md's behavioral authority."

---

## Task 4 — Mechanical Cross-Reference + Term Fixes (4 findings)

**Finding count:** 3 P1, 1 P2
**Files:** registry.md, integration.md, delivery.md
**Depends on:** nothing — start immediately

### [SY-13] P1: Broken anchor `data-model.md#schema-defaults`

**Sources:** CC-1
**Files:** registry.md

- [ ] In registry.md line 106, change `data-model.md#schema-defaults` to `data-model.md#schema-evolution-constraint`

### [SY-14] P1: Broken anchor `integration.md#shadow-mode-registry-invariant`

**Sources:** CC-2
**Files:** integration.md

Target at line 448 is bold text, not a heading. Markdown does not generate anchors from bold text.

- [ ] Promote `**Shadow-mode registry invariant:**` at integration.md line 448 to a `#### Shadow-mode Registry Invariant` heading
- [ ] Verify the generated anchor `#shadow-mode-registry-invariant` matches references at integration.md line 137 and delivery.md line 733

### [SY-15] P1: Layer 2b test uses non-existent config key `scheduler.cooldown_turns` with wrong default

**Sources:** CC-4
**Files:** delivery.md

- [ ] In delivery.md line 699, replace `config_overrides.scheduler.cooldown_turns: 5` with `config_overrides.injection.cooldown_max_new_topics_per_turn: 3` (any value ≠ 1)
- [ ] Update "hardcoded value (2)" to "hardcoded value (1)" to match the built-in default in data-model.md §Configuration

### [SY-26] P2: `ccdi_trace` MUST statement lists 8 keys but 9th key is also mandatory

**Sources:** CC-5
**Files:** integration.md

- [ ] In integration.md line 307, add `shadow_suppressed` to the MUST-include key list, making it 9 keys explicitly
- [ ] Remove or revise the "not counted in the 8-key invariant" parenthetical at line 308 to reflect the updated count

---

## Task 5 — Verification Gap Remediation (4 findings)

**Finding count:** 4 P1
**Files:** delivery.md
**Depends on:** T1 (SY-16 should reference shadow_adjusted_yield test rows from SY-1)

### [SY-16] P1: Multi-alias accumulation and overview_injected test gaps — no remediation gate

**Sources:** VR-2
**Files:** delivery.md

- [ ] Add named classifier unit test specification: "Multi-alias score accumulation: phrase and token both match, phrase suppresses token contribution → final score is phrase weight only" and "Multi-alias score accumulation: exact and phrase both match on different aliases of same topic (no suppression) → score is sum"
- [ ] Add named registry unit test specification: "overview_injected propagation: inject family at facet=overview → `overview_injected: true`; subsequent absent→detected for leaf → `family_context_available: true`"
- [ ] Reference these test names in the graduation protocol step 1 preflight check (delivery.md line 151), alongside the shadow_adjusted_yield tests added in T1

### [SY-17] P1: Layer 2b interception feasibility — no contingency if both mechanisms fail

**Sources:** VR-3
**Files:** delivery.md

- [ ] Add a contingency clause to the Phase A feasibility gate section (delivery.md lines 803–806): "If neither mechanism produces a passing `test_layer2b_mechanism_selection`, raise a blocking issue before Phase B begins. Layer 2b tests cannot be substituted with Layer 2a tests — agent sequencing is not testable via the replay harness."
- [ ] Add a feasibility pre-test: verify exit code 2 from the PreToolUse hook actually blocks the tool call in the test environment

### [SY-18] P1: False-positive kill criterion — statistical power under-specified

**Sources:** VR-4
**Files:** delivery.md

- [ ] Add a sample-size escalation rule to the graduation protocol: "If the preliminary false-positive rate from the first 50 labels is ≥ 7%, double the minimum sample to ≥ 200 before finalizing the graduation decision"
- [ ] Add a `test_validate_graduation.py` row: "Approved status with preliminary_rate ≥ 7% but labeled_topics < 200 → Exit 1 with insufficient-power warning"
- [ ] OR: Explicitly state that statistical rigor is deferred and note the known false-negative risk at N=100

### [SY-19] P1: Intra-turn hint ordering MUST invariant has no replay fixture

**Sources:** VR-6
**Files:** delivery.md

- [ ] Add required replay fixture: `intra_turn_hint_ordering.replay.json` — fixture has two hints in a single `--semantic-hints-file`: (1) `contradicts_prior` on an injected topic adding facet F to `pending_facets`; (2) `extends_topic` on the same topic where F is the cascade-resolved facet. Assert: `dialogue-turn` cascades to `pending_facets[0]` (F), proving sequential processing
- [ ] Add companion negative fixture: reverse hint order, assert different candidate result

---

## Task 6 — P2 Batch (8 findings)

**Finding count:** 8 P2
**Files:** spec.yaml, data-model.md, README.md, delivery.md
**Depends on:** T1–T5 (run after all P1 work lands to avoid edit conflicts)

### [SY-21] P2: `elevated_sections` documented as redundant but cited as normative

**Sources:** AA-1
**Files:** spec.yaml or data-model.md

- [ ] Clarify the status of `elevated_sections` in spec.yaml: either (a) mark it normative with a comment explaining its role, or (b) update the four files that cite it to reference the operative mechanism instead

### [SY-22] P2: data-model.md `architecture_rule` claim overstated

**Sources:** AA-3
**Files:** spec.yaml or data-model.md

- [ ] Add a clarifying note to spec.yaml `data-model.architecture_rule` or data-model.md: "data-model.md's `architecture_rule` claim covers persistence-layer elaboration of architectural principles owned by foundations.md — not architectural authority in its own right"

### [SY-23] P2: README authority table drift-prone

**Sources:** AA-7
**Files:** README.md

- [ ] Add a sync note to README.md's authority table: "This table mirrors spec.yaml — see spec.yaml for the authoritative source"

### [SY-25] P2: `applied_rules[]` serialization order unspecified

**Sources:** SP-4
**Files:** data-model.md

- [ ] Add ordering constraint to §AppliedRule: "`applied_rules[]` MUST be serialized in application order: `rules[]`-sourced entries first (in `rules[]` processing order), followed by `config_overrides`-sourced entries"

### [SY-27] P2: `consecutive_medium_count` post-cooldown preservation untested

**Sources:** VR-7
**Files:** delivery.md

- [ ] Add registry unit test: "Cooldown deferral preserves consecutive_medium_count: medium leaf at count=1, second topic consumes cooldown slot → medium leaf deferred, `consecutive_medium_count` remains 1"
- [ ] Add `final_registry_file_assertions` to `cooldown_defers_second_candidate.replay.json` for the deferred topic's counter

### [SY-28] P2: `ast.parse` meta-test canary under-specified

**Sources:** VR-8
**Files:** delivery.md

- [ ] Add CLI Integration Tests table row: "Source divergence canary: temp module with `if args.source == 'codex': <branch>` → meta-test scanner returns True. Module without source branch → returns False"

### [SY-29] P2: `false_positive_topic_detections` key-presence-only assertion

**Sources:** VR-9
**Files:** delivery.md

- [ ] Change integration test assertion to include value check: `assert diagnostics['ccdi']['false_positive_topic_detections'] == 0`
- [ ] Add unit test for diagnostics emitter: `test_false_positive_field_always_zero`

### [SY-30] P2: Suppressed re-detection CLI companion test uses weaker assertion

**Sources:** VR-10
**Files:** delivery.md

- [ ] Update integration test at delivery.md line 490 to use `assert_registry_unchanged` (deep JSON equality) instead of "byte-identical or `last_seen_turn` unchanged at minimum"

---

## Verification

After all 6 tasks, run these checks:

- [ ] **Anchor integrity:** Grep all `](#` and `](*.md#` patterns across the spec; verify every anchor resolves to an existing heading
- [ ] **Field count consistency:** Verify every enumerated count in the spec matches its accompanying list
- [ ] **Config key consistency:** Verify every `config_overrides.*` reference uses keys that exist in data-model.md §Configuration
- [ ] **CLI flag consistency:** Verify every `--registry-file` usage is paired with `--inventory-snapshot`; verify every shadow-mode CLI call includes `--shadow-mode` where appropriate
- [ ] **claim_precedence consistency:** Verify every authority in every claim_precedence list has that claim in its `default_claims`

---

## Summary Table

| Task | Phase | Findings | P0 | P1 | P2 | Primary Files | Depends On |
|------|-------|----------|:--:|:--:|:--:|--------------|:----------:|
| T1 | 1 | 5 | 1 | 3 | 1 | data-model.md, delivery.md, registry.md | — |
| T2 | 1 | 4 | 0 | 3 | 1 | integration.md, delivery.md | — |
| T3 | 1 | 5 | 0 | 5 | 0 | data-model.md, decisions.md, integration.md, delivery.md, spec.yaml | — |
| T4 | 1 | 4 | 0 | 3 | 1 | registry.md, integration.md, delivery.md | — |
| T5 | 2 | 4 | 0 | 4 | 0 | delivery.md | T1 |
| T6 | 2 | 8 | 0 | 0 | 8 | data-model.md, delivery.md, README.md, spec.yaml | T1–T5 |
| **Total** | | **30** | **1** | **18** | **11** | | |
