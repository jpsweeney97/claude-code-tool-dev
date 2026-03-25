# CCDI Spec Remediation Plan — Round 13

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate 39 findings (1 P0, 26 P1, 12 P2) from the 5-reviewer spec review of `docs/superpowers/specs/ccdi/`

**Architecture:** Nine tasks in three phases fix all findings in spec files, grouped by edit-locality and causal dependency. Phase 1 (T1–T4) parallel. Phase 2 (T5–T6) depends on T1. Phase 3 (T7–T9) depends on T1–T6.

**Tech Stack:** Markdown spec edits only — no code changes

**Source:** `.review-workspace/synthesis/report.md` (5-reviewer team, 2026-03-23)
**Scope:** 39 canonical findings (1 P0, 26 P1, 12 P2) across 8 normative files + spec.yaml + README.md
**Spec:** `docs/superpowers/specs/ccdi/` (10 files)

---

## Strategy

Nine tasks in three phases:

1. **Phase 1** — Four tasks, all parallel (non-overlapping file sections):
   - **T1:** P0 shadow-mode gate + sentinel emission authority (1 P0, 2 P1) — integration.md §shadow-mode-gate, §registry-seed-handoff; data-model.md §registryseed
   - **T2:** dialogue-turn completeness (2 P1) — integration.md §dialogue-turn-registry-side-effects
   - **T3:** Authority model fixes (3 P1, 1 P2) — spec.yaml, decisions.md, README.md
   - **T4:** Schema migration + documentation (3 P1, 2 P2) — data-model.md §schema-evolution-constraint, §denyrule, §configuration, §live-registry-file-schema

2. **Phase 2** — Two tasks (depend on T1 for shadow-mode gate prose):
   - **T5:** Shadow-mode/trace contract clarifications (4 P1, 1 P2) — integration.md §shadow-mode-registry-invariant, §ccditrace-output-contract, §cli-tool
   - **T6:** Graduation status enum + kill criteria (3 P1) — integration.md §shadow-mode-gate; delivery.md §graduation-protocol, §shadow-mode-kill-criteria

3. **Phase 3** — Three tasks (depend on T1–T6 for cross-references):
   - **T7:** delivery.md test fixes: examples + fixture assertions (5 P1, 3 P2) — delivery.md trace examples, fixture specs
   - **T8:** delivery.md test fixes: test design + layer classification (7 P1) — delivery.md test tables, harness design
   - **T9:** delivery.md test fixes: missing fixtures + mechanical enforcement (4 P1, 4 P2) — delivery.md new test rows + fixtures

**Edit-locality map** (confirming no Phase 1 conflicts):

| File | T1 | T2 | T3 | T4 |
|------|:--:|:--:|:--:|:--:|
| integration.md | §shadow-mode-gate, §registry-seed-handoff | §dialogue-turn-registry-side-effects | — | — |
| data-model.md | §registryseed (cross-ref only) | — | — | §schema-evolution, §denyrule, §configuration, §live-registry |
| spec.yaml | — | — | elevated_sections, authorities, precedence | — |
| decisions.md | — | — | §normative-decision-constraints | — |
| README.md | — | — | §authority-model footnote | — |

**Commit strategy:**
1. `fix(spec): P0 shadow-mode gate Phase A carve-out + sentinel emission authority (SY-1/2/3)` (T1)
2. `fix(spec): dialogue-turn side-effects completeness for hint-driven transitions (SY AA-7/CE-10)` (T2)
3. `fix(spec): authority model — elevated_sections, architecture_rule scope, circular authority (SY-4/5/6/26)` (T3)
4. `fix(spec): schema migration defaults + documentation clarity (SY-13/14/15/33/34)` (T4)
5. `fix(spec): shadow-mode/trace contract clarifications (SY-7/8/9/10/28)` (T5)
6. `fix(spec): graduation status enum authority + kill criteria Phase A/B (SY AA-4/CE-5/11)` (T6)
7. `fix(spec): delivery.md test examples + fixture assertions (SY-12/16/17/27/29/30/31/32)` (T7)
8. `fix(spec): delivery.md test design + layer fixes (SY-18/19/20/21/22/24/25)` (T8)
9. `fix(spec): delivery.md missing fixtures + mechanical enforcement tests (SY-23/35/36/37/38/39 + Clusters A/B)` (T9)

---

## Task 1 — P0 Shadow-Mode Gate + Sentinel Emission Authority (3 findings)

**Finding count:** 1 P0, 2 P1 (corroborated)
**Files:** integration.md, data-model.md (cross-ref update)
**Depends on:** nothing — start immediately
**Corroboration:** SY-1 (cross_lens_followup: AA-6 → CE-11), SY-2 (cross_lens_followup: SP-4 → CE-12)

### [SY-3] P0: Shadow-mode gate doesn't carve out Phase A initial injection

**Sources:** CE-1
**File:** integration.md §Shadow Mode Gate

The gate prose says it "determines whether CCDI runs in active or shadow mode" — encompasses all CCDI including Phase A. The Phase A carve-out is buried 60 lines later in a code-block comment. Implementer reading only the gate section would suppress initial injection in shadow mode.

- [ ] **Step 1:** Read integration.md §Shadow Mode Gate (search for `### Shadow Mode Gate`)
- [ ] **Step 2:** After the sentence "This gate determines only whether packets are delivered to Codex." (line ~352), insert:

```markdown
**Phase A carve-out:** This gate governs Phase B mid-dialogue mutations in `codex-dialogue` only. Phase A initial injection (pre-delegation, in `/dialogue`) is unconditional and not subject to this gate — initial CCDI commits fire regardless of `graduation.json` status. See the `NOTE (CE-8 / D1)` in the [data flow](#data-flow-full-ccdi-dialogue) for the inline confirmation.
```

- [ ] **Step 3:** Verify the inline NOTE at integration.md §Initial CCDI COMMIT (~line 261) is consistent with the new prose (it should be — both say Phase A is unconditional).
- [ ] **Step 4:** Commit checkpoint (or continue to next finding in same task).

### [SY-1] P1: Sentinel emission rule misplaced in data-model.md [CORROBORATED]

**Sources:** AA-6, CE-11
**File:** integration.md §Registry Seed Handoff; data-model.md §RegistrySeed (cross-ref update)

The behavioral MUST "ccdi-gatherer MUST NOT emit sentinel when inventory fails to load" lives in data-model.md under persistence_schema authority. Integration.md (the behavior_contract authority) is silent on this condition.

- [ ] **Step 5:** Read integration.md §Registry Seed Handoff (search for `### Registry Seed Handoff`)
- [ ] **Step 6:** After the sentinel block code example and before "The `/dialogue` skill:" list, insert:

```markdown
**Sentinel emission precondition:** `ccdi-gatherer` MUST NOT emit the `<!-- ccdi-registry-seed -->` sentinel block if the inventory failed to load at seed-build time. The sentinel MUST be emitted only when a valid `CompiledInventory` was loaded and `inventory_snapshot_version` can be sourced from a non-blank, non-null `schema_version` value. When the inventory fails to load or when `schema_version` is blank, null, or absent in the loaded inventory, the gatherer suppresses sentinel emission entirely — the `/dialogue` skill proceeds without `ccdi_seed` in the delegation envelope (Phase A initial injection is disabled for this session).
```

- [ ] **Step 7:** This also resolves **[SY-2]** (partial-defect case: blank schema_version). Verify the inserted text covers both total-failure AND blank-version cases.

- [ ] **Step 8:** In data-model.md §RegistrySeed, locate the `inventory_snapshot_version` field note (~line 311). Change the behavioral MUST language to a cross-reference:

Replace the sentence: "If the inventory fails to load at seed-build time, `ccdi-gatherer` MUST NOT emit a `<!-- ccdi-registry-seed -->` sentinel block."

With: "**Behavioral constraint (cross-reference):** The sentinel emission precondition is defined in [integration.md#registry-seed-handoff](integration.md#registry-seed-handoff) under `behavior_contract` authority. The persistence_schema constraint here is: `inventory_snapshot_version` MUST equal `CompiledInventory.schema_version` from a successfully loaded inventory."

- [ ] **Step 9:** Verify data-model.md no longer contains the standalone behavioral MUST on agent emission — it now defers to integration.md for the behavioral rule while retaining its own persistence_schema authority over the field definition.
- [ ] **Step 10:** Commit.

```bash
git add docs/superpowers/specs/ccdi/integration.md docs/superpowers/specs/ccdi/data-model.md
git commit -m "fix(spec): P0 shadow-mode gate Phase A carve-out + sentinel emission authority (SY-1/2/3)"
```

---

## Task 2 — dialogue-turn Side-Effects Completeness (2 findings)

**Finding count:** 2 P1 (independent convergence)
**Files:** integration.md §dialogue-turn Registry Side-Effects
**Depends on:** nothing (non-overlapping with T1 sections)
**Corroboration:** Cluster C — AA-7 and CE-10 independently found the same surface incomplete

### [AA-7] Hint-driven deferred→detected transitions missing from integration.md

- [ ] **Step 1:** Read integration.md §dialogue-turn Registry Side-Effects (search for `### \`dialogue-turn\` Registry Side-Effects`)
- [ ] **Step 2:** After the bullet "Transitions `deferred → detected` immediately (bypassing TTL) when a topic in `deferred` state is re-detected at high confidence" (~line 63), add a new bullet:

```markdown
- Transitions `deferred → detected` when a semantic hint (`prescriptive`, `contradicts_prior`, or `extends_topic`) resolves to a `deferred` topic — clears `deferred_reason` and `deferred_ttl`, applies `deferred → detected` field update rules from [registry.md#field-update-rules](registry.md#field-update-rules), then enters the lookup path from `detected`. This is distinct from the high-confidence bypass above: hint-driven transitions fire regardless of classifier confidence.
```

### [CE-10] Hint-triggered suppressed→detected re-entry missing as a distinct step

- [ ] **Step 3:** In the same section, locate the bullet about suppressed entries (~line 65, starting "For entries in `suppressed` state:"). After the existing `weak_results` and `redundant` sub-descriptions, add a dedicated hint-triggered re-entry bullet:

```markdown
- **Semantic hint re-entry (all suppression reasons):** When a semantic hint (`prescriptive`, `contradicts_prior`, or `extends_topic` via `--semantic-hints-file`) resolves to a `suppressed` topic (regardless of `suppression_reason`), transition to `detected` per the `suppressed → detected` re-entry field update rules in [registry.md#field-update-rules](registry.md#field-update-rules): `state` ← `detected`, `suppression_reason` ← null, `suppressed_docs_epoch` ← null, `last_seen_turn` ← current turn, `consecutive_medium_count` ← 0 (topic absent from classifier — no confidence to evaluate). This applies to both `weak_results` and `redundant` reasons.
```

- [ ] **Step 4:** Verify that the added bullets are consistent with registry.md §Suppression Re-Entry and §Semantic Hints scheduling effects table.
- [ ] **Step 5:** Commit.

```bash
git add docs/superpowers/specs/ccdi/integration.md
git commit -m "fix(spec): dialogue-turn side-effects completeness for hint-driven transitions (Cluster C)"
```

---

## Task 3 — Authority Model Fixes (4 findings)

**Finding count:** 3 P1, 1 P2
**Files:** spec.yaml, decisions.md, README.md
**Depends on:** nothing

### [SY-4] P1: `elevated_sections` is a no-op given claim_precedence

**File:** spec.yaml

- [ ] **Step 1:** Read spec.yaml `elevated_sections` block under `integration` authority (~line 32)
- [ ] **Step 2:** Replace the rationale with an accurate description:

Replace: `rationale: "Behavioral invariants cross-referenced from decisions.md elevated to outrank decision_record for behavioral claims"`

With: `rationale: "Cross-reference pointer: these invariants originate from decisions.md. This registration provides direct visibility of the provenance relationship; it does not change authority resolution — claim_precedence already ranks integration above decisions for behavior_contract."`

### [SY-5] P1: data-model.md architecture_rule scope contradicts precedence position

**File:** spec.yaml

- [ ] **Step 3:** In spec.yaml, strengthen the comment on data-model's architecture_rule claim (~line 12-14). Replace:

```yaml
    # NOTE: data-model.md's architecture_rule claim covers persistence-layer elaboration
    # of architectural principles owned by foundations.md, not independent architectural
    # authority. For cross-cutting architecture decisions, foundations.md governs.
```

With:

```yaml
    # NOTE: data-model.md's architecture_rule claim covers persistence-layer elaboration
    # of architectural principles owned by foundations.md, not independent architectural
    # authority. For cross-cutting architecture decisions, foundations.md governs.
    # SCOPE CONSTRAINT: data-model.md's position in claim_precedence.architecture_rule
    # ([foundation, data-model, decisions]) enables it to resolve architecture disputes
    # ahead of decisions, but only for persistence-layer elaboration. Architectural claims
    # in data-model.md that are not traceable to foundations.md are underdetermined.
```

### [SY-6] P1: Circular authority between decisions.md ↔ integration.md

**File:** decisions.md §Normative Decision Constraints

- [ ] **Step 4:** Read decisions.md §Normative Decision Constraints (~line 52)
- [ ] **Step 5:** Replace the introductory paragraph:

Replace: "Per `spec.yaml` claim_precedence, component contracts (classifier-contract, registry-contract, packet-contract, integration) outrank decisions for `behavior_contract` and `interface_contract` claims. The invariants below are authoritative only when component contracts are silent — when a component contract specifies the same behavior, the component contract is the normative source and these rows serve as cross-references."

With: "Per `spec.yaml` claim_precedence, component contracts outrank decisions for `behavior_contract` and `interface_contract` claims. **These rows are cross-references to the authoritative sources in component contracts, not independent normative claims.** When a component contract specifies the behavior (which it does for all rows below), the component contract is the sole normative source. This table provides traceability from design decisions to their implementation locations — it does not carry independent behavioral authority."

### [SY-26] P2: README footnote misrepresents elevated_sections

**File:** README.md

- [ ] **Step 6:** Read README.md (~line 32, footnote about pipeline-isolation-invariants-subset)
- [ ] **Step 7:** Replace: "*Note: §pipeline-isolation-invariants-subset in integration.md holds elevated `behavior_contract` authority for behavioral invariants cross-referenced from decisions.md. See spec.yaml `elevated_sections`.*"

With: "*Note: §pipeline-isolation-invariants-subset in integration.md contains behavioral invariants whose provenance is traced to decisions.md. The `elevated_sections` registration in spec.yaml is a cross-reference pointer, not an authority elevation — `claim_precedence` already ranks integration above decisions for `behavior_contract`.*"

- [ ] **Step 8:** Commit.

```bash
git add docs/superpowers/specs/ccdi/spec.yaml docs/superpowers/specs/ccdi/decisions.md docs/superpowers/specs/ccdi/README.md
git commit -m "fix(spec): authority model — elevated_sections, architecture_rule scope, circular authority (SY-4/5/6/26)"
```

---

## Task 4 — Schema Migration + Documentation (5 findings)

**Finding count:** 3 P1, 2 P2
**Files:** data-model.md
**Depends on:** nothing

### [SY-13] P1: coverage_target migration default "leaf" wrong for family-kind

- [ ] **Step 1:** Read data-model.md §Registry Entry Schema Field Defaults (~line 86-88, `coverage_target` row)
- [ ] **Step 2:** Change the `coverage_target` default row from `"leaf"` to a derivation rule. Replace the row:

`| coverage_target | "leaf" |`

With:

`| coverage_target | derived from `kind`: `"family"` when `kind == "family"`, `"leaf"` when `kind == "leaf"` or `kind` absent. Mirrors the `family_key` derivation pattern. |`

### [SY-14] P1: consecutive_medium_count migration ambiguous for family-kind

- [ ] **Step 3:** In the same defaults table, locate the `consecutive_medium_count` row (~line 74) and its footnote (~line 90-94). After the footnote, add:

```markdown
**Family-kind migration:** The default `0` is correct for both family-kind and leaf-kind entries. Family-kind entries always have `consecutive_medium_count` = 0 at runtime (per [registry.md#scheduling-rules](registry.md#scheduling-rules) step 4), so the migration default produces the correct value. Leaf-kind entries may have been mid-streak — see "Known migration imprecision" above.
```

### [SY-15] P1: Config cross-key validation unclear on post-fallback values

- [ ] **Step 4:** Read data-model.md §Configuration cross-key validation (~line 418-422)
- [ ] **Step 5:** After "Do not fall back for each key independently", add:

```markdown
**Evaluation order:** The cross-key check runs on the effective values after per-key validation has applied fallbacks — not on the raw config file values. If per-key validation replaced one key with its default and the resulting pair violates `min ≤ max`, the cross-key check fires on the effective (post-fallback) values and replaces both with defaults.
```

### [SY-33] P2: DenyRule load-time conflates union and range violations

- [ ] **Step 6:** Read data-model.md §DenyRule load-time validation (~line 154)
- [ ] **Step 7:** After "skip the offending rule with a warning log entry", add:

```markdown
**Warning differentiation (recommended):** Union violations (e.g., `drop` + non-null penalty) indicate structural data corruption and should log at WARNING level with a "schema corruption" prefix. Range violations (e.g., `penalty: -0.5`) may be legitimate prior-schema artifacts and should log at INFO level with a "backward-compat skip" prefix. Both result in the same behavior (rule skipped), but the differentiation aids operational monitoring.
```

### [SY-34] P2: docs_epoch "NOT read" proximity may cause omission

- [ ] **Step 8:** Read data-model.md §Live Registry File Schema, `docs_epoch` field (~line 355)
- [ ] **Step 9:** After "retained for traceability only", add inline: "(MUST be serialized per the [null-field serialization invariant](#registryseed) — present in live file even when null)"

- [ ] **Step 10:** Commit.

```bash
git add docs/superpowers/specs/ccdi/data-model.md
git commit -m "fix(spec): schema migration defaults + documentation clarity (SY-13/14/15/33/34)"
```

---

## Task 5 — Shadow-Mode / Trace Contract Clarifications (5 findings)

**Finding count:** 4 P1, 1 P2
**Files:** integration.md §shadow-mode-registry-invariant, §ccditrace-output-contract, §cli-tool
**Depends on:** T1 (shadow-mode gate prose established)

### [SY-7] P1: --mark-deferred backstop is agent-dependent

- [ ] **Step 1:** Read integration.md §Shadow-mode Registry Invariant (~line 462-474)
- [ ] **Step 2:** After "the CLI backstop makes `--mark-deferred` a no-op when `--shadow-mode` is set", add:

```markdown
**Enforcement asymmetry:** The `--shadow-mode` backstop for `--mark-deferred` is conditional on the agent passing the flag — it is not independent CLI enforcement. If the agent omits `--shadow-mode`, `--mark-deferred` executes normally. This provides weaker isolation than `--mark-injected` (which relies on true agent abstention with no CLI backstop). The CLI backstop converts accidental `--mark-deferred` calls to no-ops only when `--shadow-mode` is present; the primary enforcement is agent policy.
```

### [SY-8] P1: deferred_reason → trace action mapping informal

- [ ] **Step 3:** Read integration.md §ccdi_trace Output Contract, after the action table (~line 327)
- [ ] **Step 4:** Add a formal mapping table:

```markdown
**`deferred_reason` → `action` mapping:**

| `deferred_reason` | `action` value | Notes |
|-------------------|---------------|-------|
| `"cooldown"` | `skip_cooldown` | CLI-enforced via `--shadow-mode` in shadow mode |
| `"scout_priority"` | `skip_scout` | Agent-enforced with CLI `--shadow-mode` backstop |
| `"target_mismatch"` | `defer` | Agent-enforced with CLI `--shadow-mode` backstop |
```

### [SY-9] P1: --shadow-mode per-call independence not stated

- [ ] **Step 5:** Read integration.md §CLI Tool, the `--shadow-mode` flag description (~line 24-26)
- [ ] **Step 6:** After the `--shadow-mode` flag scope paragraph, add:

```markdown
**Per-call flag:** `--shadow-mode` on `dialogue-turn` and `--shadow-mode` on `build-packet` are independent per-call flags. Passing it to one command does not affect behavior of the other. Each command invocation in shadow mode must include its own `--shadow-mode` flag. The flag does not set global session state.
```

### [SY-10] P1: Initial-mode facet consistency has no runtime check

- [ ] **Step 7:** Read integration.md §Facet in initial mode (~line 43)
- [ ] **Step 8:** After "No cross-check mechanism exists in initial mode", add:

```markdown
The absence of a runtime cross-check is acceptable because both prepare and commit facets originate from the same source (`ClassifierResult.resolved_topics[].facet` via `RegistrySeed`). The [RegistrySeed immutability invariant](data-model.md#registryseed) is the enforcement mechanism — any violation of that invariant would introduce facet drift. A test verifying that the seed file's `facet` field is unchanged after a prepare-only call provides the mechanical backstop.
```

### [SY-28] P2: shadow_suppressed always false for suppress not stated

- [ ] **Step 9:** Read integration.md §ccdi_trace action table, `suppress` row (~line 324)
- [ ] **Step 10:** Amend the `suppress` row's registry mutation column to add: "`shadow_suppressed`: always `false` (automatic suppression is permitted in both modes)"
- [ ] **Step 11:** Commit.

```bash
git add docs/superpowers/specs/ccdi/integration.md
git commit -m "fix(spec): shadow-mode/trace contract clarifications (SY-7/8/9/10/28)"
```

---

## Task 6 — Graduation Status Enum Authority + Kill Criteria (3 findings)

**Finding count:** 3 P1
**Files:** integration.md §shadow-mode-gate; delivery.md §graduation-protocol, §shadow-mode-kill-criteria
**Depends on:** T1 (shadow-mode gate section is established)

### [AA-4 + CE-5] Cluster D: graduation.json status enum authority + contract tension

- [ ] **Step 1:** Read integration.md §Shadow Mode Gate (~line 344-352)
- [ ] **Step 2:** Add the normative status enum definition to integration.md §Shadow Mode Gate, after step 3:

```markdown
**`status` enum (normative source):** Valid values are `"approved"` and `"rejected"`. This enum is closed for validator purposes (see [delivery.md#graduation-protocol](delivery.md#graduation-protocol) — validator MUST reject unknown values) but the runtime gate is intentionally permissive via its catch-all `else → shadow mode`. These are consistent: the validator ensures approved `graduation.json` files contain only recognized values; the gate's permissiveness handles unexpected file corruption or forward migration scenarios at runtime. When extending the enum, add the value here AND update the validator in delivery.md.
```

- [ ] **Step 3:** Read delivery.md §Graduation Protocol, the `status` enum paragraph (~line 161)
- [ ] **Step 4:** Replace: "Valid `status` values are `\"approved\"` and `\"rejected\"`. The validator tool (`validate_graduation.py`) MUST reject unknown status values."

With: "Valid `status` values are defined in [integration.md#shadow-mode-gate](integration.md#shadow-mode-gate) (normative source under `behavior_contract` authority). The validator tool (`validate_graduation.py`) MUST reject unknown status values — see integration.md for the enum definition and the reconciliation between closed-validator and permissive-gate semantics."

### [SY-11] Phase A/B boundary not in kill criteria section

- [ ] **Step 5:** Read delivery.md §Shadow Mode Kill Criteria (~line 26)
- [ ] **Step 6:** After the kill criteria table, add:

```markdown
**Scope note:** Kill criteria are evaluated on Phase B mid-dialogue activity only. Phase A initial injection is unconditional (see [integration.md#shadow-mode-gate](integration.md#shadow-mode-gate)) and is not captured in these diagnostics metrics. `topics_injected` and `packets_injected` counters in shadow-mode diagnostics reflect Phase B activity only — Phase A state is in the seed file.
```

- [ ] **Step 7:** Commit.

```bash
git add docs/superpowers/specs/ccdi/integration.md docs/superpowers/specs/ccdi/delivery.md
git commit -m "fix(spec): graduation status enum authority + kill criteria Phase A/B (Cluster D + SY-11)"
```

---

## Task 7 — delivery.md Test Fixes: Examples + Fixture Assertions (8 findings)

**Finding count:** 5 P1, 3 P2
**Files:** delivery.md
**Depends on:** T5 (trace contract established)

### [SY-12] P1: ccdi_trace example missing shadow_suppressed

- [ ] **Step 1:** Read delivery.md §Debug-Gated ccdi_trace (~line 222-244, both JSON examples)
- [ ] **Step 2:** Add `"shadow_suppressed": false` to both trace entries (turn 1 and turn 3) in the illustrative example.

### [SY-16] P1: hint_no_effect fixture missing last_seen_turn assertion

- [ ] **Step 3:** Read delivery.md `hint_no_effect_already_injected.replay.json` fixture row (~line 731-732)
- [ ] **Step 4:** Add to the fixture description: `final_registry_file_assertions` MUST include `{"path": "<topic>.last_seen_turn", "equals": <current_turn>}` (assertion (d) per registry.md scheduling table).

### [SY-17] P1: Flag-name rejection tests accept exit 0 + warning

- [ ] **Step 5:** Read delivery.md CLI Integration Tests, three flag-rejection rows (~lines 419-422)
- [ ] **Step 6:** For all three (`classify rejects --inventory-snapshot`, `dialogue-turn rejects --inventory`, `build-packet rejects --inventory`), change "non-zero exit or warning emitted" to "non-zero exit with descriptive error" in each Expected column.

### [SY-27] P2: target_match fixture doesn't verify pinned snapshot path

- [ ] **Step 7:** Read delivery.md `target_match_classifier_branch.replay.json` row (~line 747)
- [ ] **Step 8:** Amend the required assertion to: "CLI call log shows `classify --text-file <composed_target_tempfile> --inventory <pinned_snapshot_path>` was invoked, where `<pinned_snapshot_path>` matches the dialogue-pinned snapshot (not the canonical `data/topic_inventory.json` path)."

### [SY-29] P2: Link text "graduation schema" → "graduation-protocol"

- [ ] **Step 9:** At delivery.md ~line 125, change `[graduation schema](#graduation-protocol)` to `[graduation protocol](#graduation-protocol)`.

### [SY-30] P2: Kill criteria "In active mode" framing

- [ ] **Step 10:** Read delivery.md §Shadow Mode Kill Criteria, effective prepare yield row (~line 29)
- [ ] **Step 11:** Rewrite the metric cell: "`shadow_adjusted_yield` (subject to freshness guardrail; see [Diagnostics](#diagnostics)). In active mode: equivalent to `packets_surviving_precedence / packets_prepared`. The 40% threshold applies to whichever formula is active."

### [SY-31] P2: Orphaned SY-7/VR-2 references

- [ ] **Step 12:** At delivery.md ~lines 421-422, replace "Symmetric with SY-7/VR-2's `classify` test" with "Symmetric with the `classify rejects --inventory-snapshot flag` CLI integration test above."

### [SY-32] P2: Normative strength "should" vs "MUST"

- [ ] **Step 13:** At delivery.md ~line 734, in the `hint_re_enters_suppressed.replay.json` row, remove the sentence "A companion fixture `hint_re_enters_suppressed_redundant.replay.json` should exercise `suppressed:redundant`..." (the companion already has its own required row at line 735).

- [ ] **Step 14:** Commit.

```bash
git add docs/superpowers/specs/ccdi/delivery.md
git commit -m "fix(spec): delivery.md test examples + fixture assertions (SY-12/16/17/27/29/30/31/32)"
```

---

## Task 8 — delivery.md Test Fixes: Test Design + Layer Classification (7 findings)

**Finding count:** 7 P1
**Files:** delivery.md
**Depends on:** T5 (shadow-mode trace contract)

### [SY-18] P1: test_false_positive_field_always_zero has no test file

- [ ] **Step 1:** Add `test_ccdi_diagnostics.py` to the testing strategy as a named test file. In the Four-Layer Approach table or just before the Unit Tests section, add:

```markdown
### Diagnostics Emitter Tests: `test_ccdi_diagnostics.py`

| Test | Verifies |
|------|----------|
| `test_false_positive_field_always_zero` | Emitter always outputs `false_positive_topic_detections: 0` regardless of detection count |
| Active mode fields absent in shadow mode | Shadow-mode diagnostics contain shadow-only fields; active-mode diagnostics do not |
| `status: "unavailable"` schema | When `claude-code-docs` unavailable: only `status` and `phase` populated |
```

### [SY-19] P1: Hash stability fixture format/runner mismatch

- [ ] **Step 2:** In Layer 2b section, locate `shadow_defer_intent_hash_stability.fixture.json` named fixture requirement (~line 720)
- [ ] **Step 3:** Clarify: change "MUST be extracted into a named Layer 2b fixture: `shadow_defer_intent_hash_stability.fixture.json`" to:

"MUST be extracted into a named **replay harness fixture**: `shadow_defer_intent_hash_stability.replay.json` (Layer 2a). The hash stability assertion exercises CLI-deterministic behavior (same classify input → same hash) which is testable without agent infrastructure. The `.replay.json` suffix and `tests/fixtures/ccdi/` directory are correct. The assertion: two consecutive turns with identical classifier input for a topic with `shadow_defer_intent` → assert `classify_result_hash` values are identical."

### [SY-20] P1: Freshness guardrail positive-path test fragile

- [ ] **Step 4:** In delivery.md `test_shadow_freshness_guardrail.py` positive-path test (~line 129), add affirmative assertion:

After "Assert: `shadow_adjusted_yield` IS used as the graduation gate (validator does NOT emit the guardrail warning)."

Add: "Additionally assert: the validator exits 0. And in a companion negative-path variant of the same fixture (same `graduation.json` but with `shadow_adjusted_yield: 0.35`, below 40% threshold): the validator exits 1 citing `shadow_adjusted_yield` below threshold — confirming the field is actively evaluated, not vacuously passing."

### [SY-21] P1: CLI backstop test misclassified in Layer 2b

- [ ] **Step 5:** In Layer 2b, locate the CLI backstop test (~line 714)
- [ ] **Step 6:** Add a duplicate entry in the CLI Integration Tests table:

```markdown
| `build-packet --shadow-mode --mark-deferred` zero registry mutations | `build-packet --shadow-mode --mark-deferred scout_priority --skip-build --registry-file <path>` → exit 0, registry file semantically unchanged (JSON-parse before and after, assert deep equality). Stderr contains log entry with topic key and reason. | Primary CLI-level test (no agent infrastructure needed) |
```

And in the Layer 2b entry, revise to: "**Companion Layer 2b test:** Verify the `codex-dialogue` agent passes `--shadow-mode` to `build-packet --mark-deferred` when graduation status is not approved. This complements the CLI integration test above."

### [SY-22] P1: Phase A unconditional test targets wrong layer

- [ ] **Step 7:** In Layer 2b, locate "Graduation gate: Phase A unconditional" (~line 708)
- [ ] **Step 8:** Replace "agent tool-call log for the `/dialogue` skill (pre-delegation)" with:

"At `codex-dialogue` start, the registry file (from `ccdi_seed`) already has `injected` entries (post-initial-commit). Assert: the registry file passed via `ccdi_seed` contains at least one entry in `injected` state (confirming `/dialogue` performed the initial commit before delegation). This tests the post-condition observable from `codex-dialogue`'s perspective, not the `/dialogue` skill's tool-call sequence."

### [SY-24] P1: Missing test for shadow_adjusted_yield absent + approved

- [ ] **Step 9:** In `test_validate_graduation.py` table, add:

```markdown
| Approved status with `shadow_adjusted_yield` absent (freshness guardrail) | `graduation.json` with `status: "approved"`, `shadow_adjusted_yield` field absent (freshness guardrail fired), `effective_prepare_yield: 0.65` above threshold, all other fields consistent | Exit 0, validation passes — `effective_prepare_yield` used as fallback gate |
```

### [SY-25] P1: intra_turn_hint_ordering requires mid-turn assertion

- [ ] **Step 10:** In `intra_turn_hint_ordering.replay.json` fixture (~line 767), change the assertion strategy. Replace the `final_registry_file_assertions` MUST for `pending_facets` with:

"The fixture uses a **two-turn design** to avoid mid-turn assertions: Turn 1 — `dialogue-turn` with two hints (contradicts_prior adding F, then extends_topic at F). The harness does NOT call `build-packet` on turn 1 (no search_results provided for the `pending_facet` candidate). Turn 2 — no hints, no classifier output. `final_registry_file_assertions` after turn 2: `{"path": "T.pending_facets", "equals": [F]}` (still pending, never served because no build-packet committed it). This proves hint 1 was processed before hint 2 without requiring mid-turn snapshots."

- [ ] **Step 11:** Commit.

```bash
git add docs/superpowers/specs/ccdi/delivery.md
git commit -m "fix(spec): delivery.md test design + layer fixes (SY-18/19/20/21/22/24/25)"
```

---

## Task 9 — delivery.md Missing Fixtures + Mechanical Enforcement Tests (8 findings)

**Finding count:** 4 P1, 4 P2
**Files:** delivery.md
**Depends on:** T4 (data-model.md defaults table, for Cluster B cross-ref)

### [SY-23] P1: Multi-entry epoch scan replay fixture missing

- [ ] **Step 1:** In the Required fixture scenarios table, add:

```markdown
| `multi_entry_epoch_scan_discrimination.replay.json` | Registry with 3 `suppressed:weak_results` entries: A at `suppressed_docs_epoch="old"`, B at `suppressed_docs_epoch="old"`, C at `suppressed_docs_epoch="different"`. Inventory snapshot `docs_epoch="new"` (changed from "old"). All 3 topics absent from classifier output. Assert: A and B transition to `detected` (epoch changed from their stored value); C remains `suppressed` (epoch mismatch is relative to each entry's `suppressed_docs_epoch`, not the registry-wide value). `final_registry_file_assertions`: `{"path": "A.state", "equals": "detected"}`, `{"path": "B.state", "equals": "detected"}`, `{"path": "C.state", "equals": "suppressed"}`. |
```

### [Cluster A] P1: Transport-only field allowlist test (SP-2 + VR-15)

- [ ] **Step 2:** In `test_ccdi_contracts.py` boundary tests table, add:

```markdown
| Transport-only field allowlist completeness | Introspect the serializer's transport-only field exclusion set and assert it equals exactly `{"results_file", "inventory_snapshot_path"}`. Guards against new transport-only fields added to the serializer without updating the spec's closed allowlist. |
```

### [Cluster B] P1: Defaults table sync test (SP-6 + VR-16)

- [ ] **Step 3:** In `test_ccdi_contracts.py` boundary tests table, add:

```markdown
| Defaults table ↔ TopicRegistryEntry durable fields synchronization | Enumerate all durable `TopicRegistryEntry` fields from registry.md's entry structure. Assert each has a corresponding entry in data-model.md's schema defaults table. Guards against new fields added to `TopicRegistryEntry` without a migration default. |
```

### [SY-39 + SY-38] P1: Config isolation Phase A test

- [ ] **Step 4:** In CLI Integration Tests table, add:

```markdown
| Agent gate config isolation (Phase A) | `ccdi_config.json` with `injection.initial_threshold_high_count: 999` (impossible threshold). Input has 1 high-confidence topic. Assert: agent-side gate dispatches ccdi-gatherer (uses hardcoded threshold 1, not configured 999). Additionally verify agent tool-call log for the pre-dispatch path contains zero Read invocations on `*ccdi_config*` paths. Phase A-compatible — no Layer 2b infrastructure required. |
```

### [SY-35] P2: assert_registry_unchanged overlap undocumented

- [ ] **Step 5:** In `weak_results_scan_noop_absent.replay.json` fixture, after the `assert_registry_unchanged` definition, add: "(Note: this assertion intentionally overlaps with the `Registry null-field serialization` boundary contract test — the overlap provides defense-in-depth for the null-field serialization invariant at the integration level.)"

### [SY-36] P2: ccdi_inventory_snapshot boundary test has no Layer 2b analog

- [ ] **Step 6:** After the `ccdi_inventory_snapshot absent with ccdi_seed present` boundary test row, add a note: "**Layer 2b companion (Phase B):** Add a Layer 2b fixture verifying `codex-dialogue` agent behavior when receiving this malformed envelope — zero `dialogue-turn` invocations and warning logged."

### [SY-37] P2: Boundary rule 5 test is prose, not executable

- [ ] **Step 7:** In the `graduation.json status enum consistency` test row (~line 469), amend the assertion: "Assert: parse the graduation validator's `VALID_STATUS_VALUES` constant and the gate implementation's conditional branches. Both handle identical status values. This is a code-level assertion (not a prose cross-reference)."

### [SY-38] P2: Agent gate test doesn't verify no config read (already addressed by SY-39 in step 4)

- [ ] **Step 8:** Already covered by the SY-39 test added in step 4 (includes "verify agent tool-call log contains zero Read invocations on `*ccdi_config*` paths"). No additional edit needed.

- [ ] **Step 9:** Commit.

```bash
git add docs/superpowers/specs/ccdi/delivery.md
git commit -m "fix(spec): delivery.md missing fixtures + mechanical enforcement tests (SY-23/35/36/37/38/39 + Clusters A/B)"
```

---

## Verification Checklist

After all 9 tasks, verify:

- [ ] All 39 SY findings have a corresponding edit (cross-reference against ledger)
- [ ] No cross-reference anchor was broken by edits (search for `](#` patterns in edited files)
- [ ] spec.yaml `elevated_sections` rationale is consistent with README.md footnote
- [ ] integration.md §shadow-mode-gate Phase A carve-out is consistent with §data-flow inline NOTE
- [ ] integration.md §registry-seed-handoff sentinel precondition covers both total-failure and blank-version
- [ ] data-model.md no longer has standalone behavioral MUST on agent emission
- [ ] decisions.md §Normative Decision Constraints is explicitly non-authoritative (cross-reference only)
- [ ] delivery.md test counts match actual table rows (re-count after additions)
- [ ] delivery.md graduation.json `status` enum now defers to integration.md
