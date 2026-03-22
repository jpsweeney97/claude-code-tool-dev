# Skill-Composability Spec Remediation Round 7 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate all 37 findings (2 P0, 24 P1, 11 P2) from skill-composability spec review round 7, incorporating revised fix directions from Codex dialogue stress-test on the durable-store and budget-mechanics clusters.

**Architecture:** Five sequential commits organized by priority and file dependency: P0 correctness → authority structure → normative behavior → verification coverage → P2 polish. Each commit is atomic and internally consistent. Tasks 1-2 can execute in parallel (no file overlap); Task 3 depends on Task 2; Task 4 depends on Tasks 1+3; Task 5 depends on Task 4.

**Tech Stack:** Markdown spec files in `docs/superpowers/specs/skill-composability/`. No code changes — all edits are normative spec text.

---

## Codex Dialogue Revisions

The following findings have **revised fix directions** from a Codex dialogue stress-test (thread `019d1663-b2e5-7971-a4c4-ec894dac9225`, full convergence in 5 turns). Use the revised directions below, NOT the original review fix directions:

| Finding | Original Direction | Revised Direction | Reason |
|---------|-------------------|-------------------|--------|
| CE-10 | Take latest `created_at`; fallback `created_at: 0` | Shared invalid-candidate rule: unparseable `created_at` = validation failure → exclude from selection. Apply to both discovery AND supersedes. | `created_at: 0` violates the spec's millisecond-precision ISO 8601 rule |
| IE-2 | Treat indeterminate override as not-pending (mirror counter) | Re-confirmation mechanism: emit prompt asking user to say "continue" again | Counter and override have opposite safety properties — counter is permissive heuristic, override is governance boundary |
| IE-5 | Add 6th case: corrupt → warn + fall through | Same recovery, but scope precisely to `record_status: ok` + present + corrupt content (including unparseable `created_at` in frontmatter) | Must not collide with `record_status: absent` behavior |
| CE-5 | Specify "unordered full-scan" | Direct algorithm specification: "Scan all visible candidates... Ignore invalid... Do not stop early... Result = count of valid visible matches." Broaden undercount note. | "Unordered" can be misread as implementation constraint or subset permission |
| VR-6 | Add verification scenario for subject_key/record_path coordination | Reframe: independence clarification + optional round-trip persistence integrity scenario. Downgrade severity. | Discovery and validation are independent mechanisms at different times |

Additional items surfaced by dialogue (incorporate into Task 3):
- **`created_at` source clarification**: Ordering uses in-band capsule frontmatter, never OS `mtime`
- **Single-writer v1 limitation note**: Concurrent same-subject writers declared unsupported
- **`supersedes: null` edge case**: When all prior artifacts are invalid, resolve to `null`
- **Cross-fix interaction: CE-10 ↔ IE-5**: Both share the invalid-candidate path for unparseable `created_at`

## File Structure

All files are under `docs/superpowers/specs/skill-composability/`:

| File | Tasks | Finding Count | Role |
|------|-------|---------------|------|
| `routing-and-materiality.md` | T1, T3 | 11 edits | Routing rules, materiality, budget, durable persistence |
| `verification.md` | T1, T4, T5 | 16 edits | Verification paths for normative claims |
| `capsule-contracts.md` | T2, T3, T5 | 6 edits | Inter-skill capsule schemas and contracts |
| `spec.yaml` | T2 | 3 edits | Authority model and precedence rules |
| `foundations.md` | T2 | 2 edits | Architectural invariants |
| `lineage.md` | T3 | 3 edits | Identity keys, consumption discovery, supersedes |
| `delivery.md` | T3, T5 | 4 edits | Implementation sequence, PR checklist |
| `decisions.md` | T2 | 1 edit | Locked design choices |
| `pipeline-integration.md` | T5 | 1 edit | Pipeline threading, tautology filter |

---

## Task 1: P0 Correctness Fixes

**Findings:** SY-4 (P0), VR-4 (P0)
**Commit message:** `fix(spec): remediate 2 P0 findings from skill-composability review round 7`

**Files:**
- Modify: `routing-and-materiality.md` §routing-classification (~line 10-25)
- Modify: `verification.md` §routing-and-materiality-verification (~line 67-80) and §interim-materiality-verification-protocol (~line 37)

### SY-4: Upstream-source routing boundary enforcement

- [ ] **Step 1: Read routing-classification section**

Read `routing-and-materiality.md` lines 10-25 (routing classification, deterministic routing rules). Identify where the deterministic routing pass reads upstream IDs. Note the current text — it does not constrain the source of AR IDs used during deterministic routing.

- [ ] **Step 2: Add algorithmic constraint to routing-and-materiality.md**

Add to the deterministic routing rules subsection (after the existing deterministic routing description, before model classification fallback):

```markdown
**Upstream source boundary:** The deterministic routing pass MUST read upstream IDs exclusively from `upstream_handoff.source_findings[]` and `upstream_handoff.source_assumptions[]`. Direct scanning of conversation context for AR capsules during deterministic routing classification is prohibited — an AR capsule present in conversation context but not forwarded via the NS handoff is invisible to deterministic routing. Items whose AR provenance is only available via conversation-context scanning fall through to the model classification pass, producing `classifier_source: model`.
```

- [ ] **Step 3: Add verification row to verification.md**

Add to the Routing and Materiality Verification table (after the existing routing rows):

```markdown
| Upstream-source routing boundary: deterministic routing reads only from `upstream_handoff` | [routing-and-materiality.md](routing-and-materiality.md#routing-classification) | Behavioral: AR capsule present in conversation context but NOT forwarded via NS handoff → verify deterministic routing does NOT fire on those AR IDs; verify item falls through to model classification pass; verify `classifier_source: model` on resulting entry. Fixture: inject AR capsule sentinel directly into conversation context (not via NS handoff) alongside a valid NS handoff that does NOT reference that AR capsule |
```

- [ ] **Step 4: Verify cross-references**

Grep for `routing-classification` and `upstream-source` across all spec files to confirm no broken anchors were introduced.

```bash
rg "routing-classification|upstream.source" docs/superpowers/specs/skill-composability/
```

### VR-4: Step 3c zero-output fallback with --plan not set

- [ ] **Step 5: Read Step 3c verification row**

Read `verification.md` lines 37-38 (Step 0 case c and Step 3c verification). Identify the current Step 3c test case — it covers `--plan` set but not `--plan` not set.

- [ ] **Step 6: Expand Step 3c verification scenario**

Add to the existing Step 3c verification (or add adjacent row in the Routing and Materiality Verification table):

```markdown
| Step 3c zero-output fallback: `--plan` NOT set + upstream context | [pipeline-integration.md](pipeline-integration.md#pipeline-threading) row 4 | Behavioral: `--plan` NOT set + `upstream_handoff` with `briefing_context: true` + gatherers return 0 parseable lines after retries → verify: (1) `briefing_context` is injected as sole grounding in the Codex briefing Context section (deterministic projection of `source_findings[]` and `decision_gates[]`), (2) zero-output fallback template emitted with `## Context` containing the upstream context (not empty), (3) `seed_confidence: low` with `low_seed_confidence_reasons: ["zero_output"]`. Distinguishes from `--plan`-set variant where Step 0 decomposition also runs |
```

- [ ] **Step 7: Commit**

```bash
git add docs/superpowers/specs/skill-composability/routing-and-materiality.md docs/superpowers/specs/skill-composability/verification.md
git commit -m "fix(spec): remediate 2 P0 findings from skill-composability review round 7

SY-4: Add upstream-source routing boundary constraint — deterministic
routing reads exclusively from upstream_handoff, not conversation context.

VR-4: Add Step 3c verification scenario for --plan-not-set + upstream
context path.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Authority Structure Fixes

**Findings:** AA-1 (P1), AA-3 (P1), AA-4 (P1), SY-3 (P1), AA-5 (P2), AA-6 (P2)
**Commit message:** `fix(spec): remediate 4 P1 + 2 P2 authority findings from skill-composability review round 7`

**Files:**
- Modify: `spec.yaml` lines 43-50, 60-64, 66-70
- Modify: `foundations.md` lines 59-95, 103-115
- Modify: `capsule-contracts.md` lines 216-221
- Modify: `decisions.md` lines 20-24

### AA-1: Move external authority hierarchy from YAML comment to foundations.md

- [ ] **Step 1: Read spec.yaml YAML comment block**

Read `spec.yaml` lines 66-70. Note the content about composition contract and inline stub positioning in the authority hierarchy.

- [ ] **Step 2: Move content to foundations.md**

Add to `foundations.md` §three-layer-delivery-authority (after the existing three-layer description, ~line 82):

```markdown
**External authority positioning:** The composition contract (`packages/plugins/cross-model/references/composition-contract.md`) is runtime-loaded by the dialogue skill and sits between the spec (layer 1, highest) and inline stubs (layer 3, lowest). It inherits authority from spec modules via explicit delegation — it cannot introduce normative claims not traceable to a spec module. Inline stubs are the default runtime layer — they operate without the composition contract and without this spec in context.
```

- [ ] **Step 3: Replace spec.yaml comment with pointer**

Replace the spec.yaml YAML comment block (lines 66-70) with:

```yaml
# External authority positioning: see foundations.md#three-layer-delivery-authority
```

### AA-3: Fix precedence comment contradiction

- [ ] **Step 4: Read spec.yaml precedence rules**

Read `spec.yaml` lines 43-50. Note the `behavior_contract` precedence order and the comment about contradictions being spec defects.

- [ ] **Step 5: Remove contradictory comment**

Remove the comment that says contradictions between routing and foundation indicate spec defects. The `fallback_authority_order` mechanical rule already handles conflict resolution — the comment restates what the rule does but with different semantics (defect vs. resolution). Replace with:

```yaml
# Conflict resolution: fallback_authority_order determines which authority
# wins when claims overlap. This is mechanical, not a defect signal.
```

### AA-4: Fix cross-family wire-format disambiguation

- [ ] **Step 6: Read spec.yaml cross-family comment**

Read `spec.yaml` lines 60-64. Note the cross-family disambiguation rules.

- [ ] **Step 7: Update cross-family disambiguation**

Update spec.yaml's cross-family disambiguation comment to acknowledge that `routing` authority governs wire-format correctness for the feedback capsule when it is a behavioral consequence of routing enforcement:

```yaml
# Cross-family disambiguation: routing authority (enforcement_mechanism) governs
# both pipeline state and wire-format correctness for entries passing through the
# correction pipeline. The emission-time gate in routing-and-materiality.md constrains
# capsule wire format as a consequence of routing enforcement, not as an independent
# interface contract claim.
```

### SY-3: Remove dual-authority enforcement MUSTs from capsule-contracts.md

- [ ] **Step 8: Read capsule-contracts.md schema constraints**

Read `capsule-contracts.md` lines 216-221. Note the enforcement MUST clauses for `classifier_source` and `materiality_source`.

- [ ] **Step 9: Replace enforcement MUSTs with schema definitions + cross-references**

Replace the enforcement MUST clauses at lines 219-220 with schema-only definitions:

```markdown
- `classifier_source` validation: MUST be `rule` or `model` — no other values permitted. Emission-time enforcement gate defined in [routing-and-materiality.md](routing-and-materiality.md#dimension-independence). Invalid values are corrected to `rule` with structured warning (always recoverable, does NOT trigger partial correction failure abort).
- `materiality_source` validation: MUST be `rule` or `model` — parallel to `classifier_source`. Emission-time enforcement gate defined in [routing-and-materiality.md](routing-and-materiality.md#affected-surface-validity). Same correction and recovery semantics.
```

### AA-5 (P2): Fix circular precedence reference in foundations.md

- [ ] **Step 10: Read foundations.md versioning section**

Read `foundations.md` lines 103-115. Note the self-asserting precedence sentence.

- [ ] **Step 11: Remove circular self-assertion**

Remove the sentence: "Contradictions between item #8 and this section are resolved in favor of this section..." The `spec.yaml` `fallback_authority_order` already determines precedence — a normative file should not self-assert. If needed, add a pointer in `delivery.md` item #8 instead.

### AA-6 (P2): Inline consumer class summary in decisions.md

- [ ] **Step 12: Read decisions.md D2**

Read `decisions.md` lines 20-24.

- [ ] **Step 13: Add inline summary to D2**

Add a one-line summary after the D2 decision text:

```markdown
Advisory/tolerant: validate if present, fall back to non-capsule behavior if absent or invalid. Strict/deterministic: reject invalid input, proceed in baseline mode. See [foundations.md](foundations.md#consumer-classes) for the full normative specification.
```

- [ ] **Step 14: Verify cross-references**

```bash
rg "three-layer-delivery-authority|schema-constraints|consumer-classes|dimension-independence" docs/superpowers/specs/skill-composability/
```

Confirm no broken anchors. Confirm foundations.md now contains the authority hierarchy content and spec.yaml points to it.

- [ ] **Step 15: Commit**

```bash
git add docs/superpowers/specs/skill-composability/spec.yaml docs/superpowers/specs/skill-composability/foundations.md docs/superpowers/specs/skill-composability/capsule-contracts.md docs/superpowers/specs/skill-composability/decisions.md
git commit -m "fix(spec): remediate 4 P1 + 2 P2 authority findings from skill-composability review round 7

AA-1: Move external authority hierarchy from spec.yaml comment to
foundations.md (single normative source).
AA-3: Remove contradictory precedence comment — mechanical rule suffices.
AA-4: Update cross-family disambiguation for routing wire-format claims.
SY-3: Remove dual-authority enforcement MUSTs from capsule-contracts.md —
keep schema definitions with cross-reference to routing authority.
AA-5: Remove circular self-assertion in foundations.md versioning section.
AA-6: Inline consumer class summary in decisions.md D2.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Normative Behavior Fixes

**Findings:** SY-1, CE-3, CE-4, CE-5 (revised), CE-7, CE-10 (revised), CE-11, IE-2 (revised), IE-5 (revised), SY-2, IE-4
**Plus dialogue-surfaced items:** `created_at` source clarification, single-writer v1 note, `supersedes: null` edge case, cross-fix interactions
**Commit message:** `fix(spec): remediate 11 P1 findings from skill-composability review round 7`

**Files:**
- Modify: `routing-and-materiality.md` §material-delta-gating (~line 86-97), §affected-surface-validity (~line 50-84), §budget-enforcement-mechanics (~line 178-195), §selective-durable-persistence (~line 216-242), §ambiguous-item-behavior (~line 33-48), §no-auto-chaining
- Modify: `capsule-contracts.md` §contract-3 (~line 143-227), §consumer-class-contract-2 (~line 82-86)
- Modify: `lineage.md` §consumption-discovery (~line 115-126), §dag-structure (~line 104-105), §artifact-id-format (~line 78-94)
- Modify: `delivery.md` §open-items (~line 40-55)

### SY-1: Add dialogue-orchestrated-briefing suppression to both abort paths

- [ ] **Step 1: Read both abort path enumerations**

Read `routing-and-materiality.md`:
- Step 0 case (c) post-abort enumeration (~line 94-97)
- Partial correction failure post-abort enumeration (~line 77)

Note the current assertion counts and items.

- [ ] **Step 2: Add suppression to Step 0 case (c)**

Add to the Step 0 case (c) post-abort assertion list:

```markdown
(vi) `<!-- dialogue-orchestrated-briefing -->` MUST NOT appear in any user-visible output — see [capsule-contracts.md](capsule-contracts.md#sentinel-registry) for sentinel scope.
```

Update the assertion count label from "5 assertions" to "6 assertions" (or adjust numbering if verification.md already pushed it to 6 via a prior edit).

- [ ] **Step 3: Add suppression to partial correction failure**

Add to the partial correction failure post-abort enumeration:

```markdown
(6) `<!-- dialogue-orchestrated-briefing -->` MUST NOT appear in any user-visible output (sentinel suppressed alongside capsule body — verify both `<!-- dialogue-feedback-capsule:v1 -->` AND `<!-- dialogue-orchestrated-briefing -->` are absent from output).
```

Add source cross-reference: `[capsule-contracts.md](capsule-contracts.md#sentinel-registry)`.

### CE-3: Add exhaustive proof for correction rule 5

- [ ] **Step 4: Read correction rules section**

Read `routing-and-materiality.md` §affected-surface-validity, the correction rules 1-5 block (~lines 63-69).

- [ ] **Step 5: Add exhaustive case argument**

After rule 5, add:

```markdown
**Completeness proof:** Rules 1-4 collectively cover all 18 invalid tuple combinations in the 24-case validity matrix (24 total minus 6 valid pass-throughs). For each invalid tuple, the first applicable rule corrects it:
- Rule 1 covers all 9 invalid tuples where `material: false` AND `suggested_arc ≠ dialogue_continue` (3 `affected_surface` values × 3 invalid `suggested_arc` values).
- Rule 2 covers `material: true, affected_surface: evidence-only` with any non-`dialogue_continue` arc (3 tuples).
- Rule 3 covers `material: true, affected_surface: diagnosis` with `suggested_arc ∈ {next-steps, dialogue_continue}` (2 tuples).
- Rule 4 covers `material: true, affected_surface: planning` with `suggested_arc ∈ {adversarial-review, dialogue_continue}` (2 tuples).
- Remaining: `material: true, affected_surface: {diagnosis, planning}` with `suggested_arc: ambiguous` (2 tuples) — these are held in `unresolved[]` with `hold_reason: routing_pending` before reaching rule 5.

Rule 5 fires only if a tuple survives rules 1-4 with an unexpected state — this requires either an `affected_surface` value outside `{evidence-only, diagnosis, planning}` or a novel `suggested_arc` value, both of which indicate a schema evolution gap rather than a logic error.
```

### CE-7: Add correction sequencing note

- [ ] **Step 6: Add sequencing note to emission-time enforcement**

Add to routing-and-materiality.md §affected-surface-validity, after the correction rules block:

```markdown
**Processing order per entry:** (1) Apply ordered correction rules 1-5 to `(affected_surface, material, suggested_arc)` tuple. (2) Apply `classifier_source` validation — correct invalid values to `rule` with structured warning (always recoverable). (3) Apply `materiality_source` validation — same semantics. Steps 2-3 are recoverable validations that never trigger partial correction failure. Partial correction failure is triggered only by unexpected states in step 1 that cause rule 5 to fire.
```

### CE-10 (REVISED): Shared invalid-candidate rule for unparseable created_at

- [ ] **Step 7: Read consumption discovery step 0 and supersedes minting rule**

Read `lineage.md`:
- Consumption discovery step 0 (~lines 119-120)
- Supersedes minting rule (~lines 104-105)
- Artifact ID format precision rule (~line 86)

- [ ] **Step 8: Add shared invalid-candidate rule to lineage.md**

Add a new subsection to lineage.md after the existing artifact ID format section (~after line 94):

```markdown
### Invalid Candidate Rule

Any artifact whose required `created_at` field is unparseable (not valid ISO 8601, missing, or malformed) is invalid for selection, ordering, and supersession. This rule applies uniformly to:
- **Consumption discovery** (step 0 durable store check and steps 1-5 conversation scan): invalid candidates are excluded from selection. Emit a one-line prose warning naming the excluded file or sentinel. If all candidates are invalid, treat as no match found.
- **Supersedes minting**: invalid candidates are excluded from predecessor selection. If no valid prior artifact remains after exclusion, resolve to `supersedes: null`.

Ordering key for multi-candidate disambiguation is the in-band capsule `created_at` frontmatter value — never OS filesystem `mtime` or any external timestamp source.
```

- [ ] **Step 9: Update consumption discovery step 0 for multi-file disambiguation**

Update lineage.md consumption discovery step 0 (~line 119-120) to add:

```markdown
When multiple durable files match by `subject_key`, take the one with the latest `created_at` (per artifact ID format precision rules). Candidates failing the invalid candidate rule are excluded before disambiguation.
```

- [ ] **Step 10: Add single-writer v1 limitation note**

Add to lineage.md after the invalid candidate rule:

```markdown
**v1 limitation — single writer assumed:** Concurrent dialogue invocations writing durable files with the same `subject_key` are unsupported. Concurrent writes to the same `subject_key` produce filename collisions (path overwrite via the deterministic path construction rule in [routing-and-materiality.md](routing-and-materiality.md#selective-durable-persistence)), not consumer-side ambiguity. This is declared unsupported rather than handled.
```

### CE-5 (REVISED): Direct algorithm specification for budget scan

- [ ] **Step 11: Read budget enforcement mechanics**

Read `routing-and-materiality.md` §budget-enforcement-mechanics, counting algorithm and counter storage (~lines 184-188).

- [ ] **Step 12: Replace scan direction with direct algorithm specification**

Update the budget counting description to:

```markdown
**Counting algorithm:** Scan all visible candidate capsules in the current conversation context for the target `lineage_root_id`. Ignore invalid capsules (unparseable sentinel, schema-invalid content) and continue scanning. Do not stop early. The result is the count of all valid visible matches — a complete count of every qualifying transition in the visible context.

**Visibility note:** Context compaction, non-durable artifact loss, and conversation truncation can all reduce the visible set. Any of these produces an undercount rather than an indeterminate state, which is acceptable for budget reasoning — the budget is a soft limit, and an undercount errs toward allowing a hop that may have been the Nth (permissive).
```

### IE-2 (REVISED): Re-confirmation mechanism for budget override

- [ ] **Step 13: Read override mechanism and context compression resilience**

Read `routing-and-materiality.md` §budget-enforcement-mechanics, override mechanism (~line 192) and context compression resilience (~line 188).

- [ ] **Step 14: Add override context-compression recovery**

Add after the existing context compression resilience paragraph:

```markdown
**Override context-compression recovery:** When `budget_override_pending` state is indeterminate (no visible "continue" message for the current `lineage_root_id` after budget exhaustion following context compression), do NOT silently treat as not-pending. Instead, emit a re-confirmation prompt: "Budget limit reached. Prior override confirmation is no longer visible due to context compression. Say `continue` again to allow one more hop." This differs from the counter's indeterminate rule because the counter is an approximate heuristic (permissive default is safe) while the override is a governance boundary requiring explicit user re-consent (suppressive default silently drops user intent).
```

### IE-5 (REVISED): Scoped 6th consumer recovery case for corrupt durable file

- [ ] **Step 15: Read consumer-side durable store contract**

Read `routing-and-materiality.md` §selective-durable-persistence, consumer-side contract (~line 236).

- [ ] **Step 16: Add 6th recovery case**

Add to the consumer-side contract enumeration:

```markdown
(6) `record_path` non-null, `record_status: ok`, file exists, but content is corrupt or unparseable (YAML parse failure, missing required frontmatter fields, truncated content, unparseable `created_at` per [lineage.md](lineage.md#invalid-candidate-rule)) → emit one-line prose warning identifying the corrupt file path + fall through to conversation-local sentinel scan (precedence level 3). Do NOT block the skill invocation. Priority-1 explicit references (where upstream capsule's `source_artifacts[]` entry directly names this artifact by `artifact_id`) remain strict: reject structured resolution for that reference, but the skill invocation continues via consumer-class fallback behavior — consumption failure is not invocation failure.
```

### CE-4: Inline two-stage admission definition in capsule-contracts.md

- [ ] **Step 17: Read capsule-contracts.md provenance rule**

Read `capsule-contracts.md` §contract-3, provenance rule (~line 205).

- [ ] **Step 18: Add inline definition**

Update the provenance rule text to include an inline definition:

```markdown
...the dialogue skill MUST omit `source_artifacts` entries for any upstream capsule (NS handoff) that was not structurally consumed — do not reference an NS `artifact_id` that was not validated via two-stage admission (sentinel detected in conversation context, schema validated against expected format, normalized to `upstream_handoff` pipeline state). See [pipeline-integration.md](pipeline-integration.md#two-stage-admission) for the full admission procedure.
```

### CE-11: Add placement rules for non-ambiguous items

- [ ] **Step 19: Read ambiguous item behavior section**

Read `routing-and-materiality.md` §ambiguous-item-behavior (~lines 33-48).

- [ ] **Step 20: Add placement rule table**

Add after the ambiguous item behavior section:

```markdown
### Post-Correction Placement Rules

After the correction pipeline completes, items are placed according to their post-correction state:

| Condition | Placement | Notes |
|-----------|-----------|-------|
| `material: true`, valid non-`ambiguous` `suggested_arc` | `feedback_candidates[]` | Normal path — item carries routing recommendation |
| `material: true`, `suggested_arc: ambiguous` (held) | `unresolved[]` with `hold_reason: routing_pending` | Routing undecided — requires user disambiguation |
| `material: false`, `suggested_arc: ambiguous` (post-correction: `dialogue_continue` via rule 1) | Prose synthesis only | Omit from both `feedback_candidates[]` and `unresolved[]` — informational mention only |
| `material: false`, non-`ambiguous` `suggested_arc` (post-correction: `dialogue_continue` via rule 1) | Omit from `feedback_candidates[]` | Not material — no downstream routing action |
```

### SY-2: Add interim hold_reason enforcement

- [ ] **Step 21: Read emission-time enforcement paragraph**

Read `routing-and-materiality.md` §affected-surface-validity, emission-time enforcement (~lines 73-75).

- [ ] **Step 22: Add hold_reason validation gate**

Add to the emission-time enforcement section:

```markdown
**`hold_reason` validation:** The emission-time gate MUST validate `hold_reason ∈ {routing_pending, null}` for every `unresolved[]` entry. Invalid values are corrected to `null` with a structured warning. This validation is always recoverable and does NOT trigger capsule assembly abort. Interim enforcement: add `hold_reason` to the grep-based CI check pattern alongside `classifier_source` and `materiality_source`.
```

### IE-4: Elevate co-review to PR checklist gate

- [ ] **Step 23: Read delivery.md item #8**

Read `delivery.md` item #8 (~line 51).

- [ ] **Step 24: Add explicit PR checklist item**

Add to delivery.md item #8's PR checklist template:

```markdown
**Stub composition co-review (mandatory gate):** Reviewer confirms no helper-mediated indirect skill delegation via static code inspection. PR checklist item: "Confirmed: stub does not programmatically invoke any skill via model output or helper delegation chains. Composition paths verified by static inspection of [list helper functions reviewed]."
```

- [ ] **Step 25: Verify all cross-references**

```bash
rg "invalid-candidate-rule|post-correction-placement|hold_reason.*validation|co-review" docs/superpowers/specs/skill-composability/
```

Confirm new anchors are consistent and no references are broken.

- [ ] **Step 26: Commit**

```bash
git add docs/superpowers/specs/skill-composability/routing-and-materiality.md docs/superpowers/specs/skill-composability/capsule-contracts.md docs/superpowers/specs/skill-composability/lineage.md docs/superpowers/specs/skill-composability/delivery.md
git commit -m "fix(spec): remediate 11 P1 findings from skill-composability review round 7

SY-1: Add dialogue-orchestrated-briefing suppression to both abort paths.
CE-3: Add exhaustive proof for correction rule 5 completeness.
CE-7: Add correction processing sequencing (rules 1-5 then validations).
CE-10: Add shared invalid-candidate rule for unparseable created_at
(Codex-revised: validation failure, not sentinel value; covers both
discovery and supersedes; includes source clarification and v1 note).
CE-5: Direct algorithm specification for budget scan (Codex-revised:
replaces 'unordered'; broader undercount note).
IE-2: Re-confirmation mechanism for budget override after compression
(Codex-revised: governance boundary requires re-consent, not silent drop).
IE-5: Scoped 6th consumer recovery case for corrupt durable file
(Codex-revised: precise scope, source-aware priority-1 handling).
CE-4: Inline two-stage admission definition in provenance rule.
CE-11: Add post-correction placement rule table.
SY-2: Add hold_reason validation gate to emission-time enforcement.
IE-4: Elevate co-review to mandatory PR checklist gate.

Dialogue thread: 019d1663-b2e5-7971-a4c4-ec894dac9225

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Verification Coverage Fixes

**Findings:** CC-2, VR-5, VR-3, VR-6 (revised), VR-8, VR-9, VR-13, VR-14, CC-3
**Commit message:** `fix(spec): remediate 9 P1 verification findings from skill-composability review round 7`

**Files:**
- Modify: `verification.md` — Capsule Contract Verification table (~lines 42-65), Routing and Materiality Verification table (~lines 67-80), Lineage Verification section, Interim Materiality Verification Protocol (~lines 24-40), standalone coherence test (~line 65)

### CC-2 + VR-5: Fix abort-path parity count and add comparison table

- [ ] **Step 1: Read abort-path parity note**

Read `verification.md` line 57. Note the current parity count (says 3 shared assertions).

- [ ] **Step 2: Update parity count and add comparison table**

Replace the parity note with an expanded version:

```markdown
**Abort-path parity:** Both abort paths (Step 0 case c and partial correction failure) MUST produce identical behavior for four shared assertions: (a) no feedback capsule sentinel (`<!-- dialogue-feedback-capsule:v1 -->`), (b) no durable file written at `.claude/composition/feedback/`, (c) no hop suggestion text in prose output, (d) no `<!-- dialogue-orchestrated-briefing -->` sentinel in user-visible output. Prose synthesis output is unaffected by both abort paths — the abort affects only the machine-readable capsule.

Verification: confirm by row comparison of both test case assertion lists:

| Assertion | Step 0 case (c) | Partial correction failure |
|-----------|-----------------|---------------------------|
| No feedback capsule sentinel | (i) | (1) |
| No capsule body emitted | (ii) | implicit in (1) |
| No durable file | (iii) | (5) |
| Structured warning in prose | (iv) | implicit in error output |
| No hop suggestion | (v) | N/A — hop suggestion only applies to Step 0 abort path |
| No `dialogue-orchestrated-briefing` | (vi) | (6) |
| Prose synthesis unaffected | implicit | post-abort assertion |
```

### VR-3: Acknowledge budget override as structural check

- [ ] **Step 3: Read budget override verification row**

Read `verification.md` ~line 83 (budget override row).

- [ ] **Step 4: Update to structural check**

Update the verification row:

```markdown
| Budget override flag reset: `budget_override_pending` MUST be single-use toggle | [routing-and-materiality.md](routing-and-materiality.md#budget-enforcement-mechanics) | Structural: verify the stub's override-handling code path explicitly resets `budget_override_pending` to `false` after permitting the override hop. Confirm via stub code review that the flag is a single-use toggle (reset after one use), not persistent-until-session-end. Behavioral test cannot distinguish "flag reset" from "new invocation without flag" — accepted as structural check responsibility, consistent with verification pattern for other conversation-local state in this spec |
```

### VR-6 (REVISED): Reframe as independence clarification

- [ ] **Step 5: Read lineage verification section**

Read `verification.md` ~line 98 (Lineage Verification, durable store scenarios).

- [ ] **Step 6: Add independence clarification and round-trip scenario**

Add or update the durable store verification:

```markdown
| Durable store discovery independence: `subject_key` scan and `record_path` validation are separate mechanisms | [lineage.md](lineage.md#consumption-discovery), [routing-and-materiality.md](routing-and-materiality.md#selective-durable-persistence) | Clarification (not a test): Store discovery is identity-based (`subject_key` metadata scan of `.claude/composition/feedback/` directory). Consumer-side `record_path` validation is locator-based (dereference a specific path). These are independent operations at different times — discovery finds candidates, `record_path` is a pointer stored in the capsule for consumer convenience. Existing scenario (5) already tests this independence (non-matching `subject_key` → fall through despite file existing at path) |
| Optional: round-trip persistence integrity | [lineage.md](lineage.md#consumption-discovery), [routing-and-materiality.md](routing-and-materiality.md#selective-durable-persistence) | Behavioral (optional): emitted feedback capsule's `record_path` resolves to a file whose frontmatter `artifact_id` matches the capsule's own `artifact_id`. Verifies the write-read round-trip integrity of the durable persistence mechanism |
```

### VR-8: Specify empty selected_tasks trigger

- [ ] **Step 7: Read NS empty selected_tasks verification row**

Read `verification.md` ~line 51.

- [ ] **Step 8: Add calibration acknowledgment**

Update the verification row:

```markdown
| NS MUST NOT emit handoff block with `selected_tasks: []` | [capsule-contracts.md](capsule-contracts.md#emission-contract-2) | Behavioral: invoke NS with a scenario where no tasks qualify for dialogue recommendation → verify NS omits the handoff block entirely (no `<!-- next-steps-dialogue-handoff:v1 -->` sentinel emitted). **Trigger condition:** This is a calibration test — "no tasks qualify" depends on model judgment about dialogue-worthiness. Use fixture: all tasks have explicit `done_when` conditions already demonstrably satisfied in the conversation context. If model still selects tasks, acknowledge as non-deterministic and add to interim manual review protocol |
```

### VR-9: Add supersedes cross-source scenario

- [ ] **Step 9: Read lineage verification supersedes rows**

Read `verification.md` ~line 105 (supersedes minting scenarios).

- [ ] **Step 10: Add scenario 4b**

Add after existing scenario 4:

```markdown
| `supersedes` cross-source max selection | [lineage.md](lineage.md#dag-structure) | Behavioral (scenario 4b): prior `dialogue_feedback` artifact A exists at durable path with older `created_at`; different prior `dialogue_feedback` artifact B with same `subject_key` exists in conversation context with newer `created_at`. Both are valid candidates (pass [invalid candidate rule](lineage.md#invalid-candidate-rule)). Verify `supersedes` references artifact B's `artifact_id` (the more recent across both sources), not artifact A's |
```

### VR-13: Add briefing_context determinism structural check

- [ ] **Step 11: Read briefing_context verification row**

Read `verification.md` ~line 89.

- [ ] **Step 12: Add structural check**

Add or update the row:

```markdown
| `briefing_context` determinism: projection MUST be non-model | [pipeline-integration.md](pipeline-integration.md#pipeline-threading) | Structural: verify the briefing assembly code path for `briefing_context` injection contains no conditional branch that calls a model or uses model-variable output — the projection MUST be a deterministic mapping from `source_findings[]` and `decision_gates[]` to briefing Context section text. No model call, no prompt, no sampling — pure data transformation |
```

### VR-14: Add dialogue-orchestrated-briefing normal-path assertion

- [ ] **Step 13: Read standalone coherence test**

Read `verification.md` ~line 65 (standalone coherence test).

- [ ] **Step 14: Add assertion to dialogue scenario**

Update the standalone coherence test's dialogue scenario to add:

```markdown
...(3 existing assertions)..., (4) verify `<!-- dialogue-orchestrated-briefing -->` does not appear anywhere in the emitted output — the sentinel is internal pipeline state and MUST NOT be externalized in the normal execution path
```

### CC-3: Fix orphaned SY-3 label

- [ ] **Step 15: Read verification.md line 55**

Read `verification.md` ~line 55. Note the orphaned `SY-3` label.

- [ ] **Step 16: Replace with inline description**

Replace `SY-3` with:

```markdown
exercises the `materiality_source` unexpected-state correction described in [routing-and-materiality.md](routing-and-materiality.md#affected-surface-validity)
```

- [ ] **Step 17: Verify all cross-references**

```bash
rg "invalid-candidate-rule|dag-structure|pipeline-threading|emission-contract-2|budget-enforcement-mechanics" docs/superpowers/specs/skill-composability/verification.md
```

Confirm all new cross-references resolve to existing anchors (including anchors added in Tasks 1-3).

- [ ] **Step 18: Commit**

```bash
git add docs/superpowers/specs/skill-composability/verification.md
git commit -m "fix(spec): remediate 9 P1 verification findings from skill-composability review round 7

CC-2 + VR-5: Fix abort-path parity count (3→4) and add comparison table.
VR-3: Acknowledge budget override flag-reset as structural check.
VR-6: Reframe as independence clarification + optional round-trip scenario
(Codex-revised: not a protocol fork).
VR-8: Add calibration test acknowledgment for empty selected_tasks trigger.
VR-9: Add supersedes cross-source max selection scenario (4b).
VR-13: Add briefing_context determinism structural check.
VR-14: Add dialogue-orchestrated-briefing normal-path assertion to
standalone coherence test.
CC-3: Replace orphaned SY-3 label with inline description.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: P2 Polish

**Findings:** CE-8, CE-9, CC-4, CC-6, VR-7, VR-10, VR-11, VR-12, IE-7
**Commit message:** `fix(spec): remediate 9 P2 findings from skill-composability review round 7`

**Files:**
- Modify: `capsule-contracts.md` §consumer-class-contract-2 (~line 82-86), §schema-constraints (~line 216-221)
- Modify: `verification.md` — multiple rows
- Modify: `delivery.md` §open-items (~line 40-55), §skill-text-changes (~line 31-38)
- Modify: `pipeline-integration.md` §two-stage-admission Stage B (~lines 34-39)
- Modify: `routing-and-materiality.md` §selective-durable-persistence (~line 238)
- Possibly modify: `foundations.md` (~line 57)

### CE-8: Clarify selected_tasks schema comment

- [ ] **Step 1: Read capsule-contracts.md consumer class contract 2**

Read `capsule-contracts.md` §consumer-class-contract-2 validity criteria (~line 120).

- [ ] **Step 2: Clarify comment**

Update the schema comment about `selected_tasks`:

```markdown
`selected_tasks` validity: MUST be present AND non-empty. Absent `selected_tasks` key = invalid (criterion 1: missing required field). Present but empty `selected_tasks: []` = invalid (criterion 3: explicit validity rule). Both produce the same consumer behavior: rejection + normal pipeline proceeds.
```

### CE-9: Clarify record_path pre-computation ordering

- [ ] **Step 3: Read selective durable persistence write failure section**

Read `routing-and-materiality.md` §selective-durable-persistence, write failure recovery (~lines 238-240).

- [ ] **Step 4: Add ordering clarification**

Add to the write-failure recovery text:

```markdown
The `record_path` value is pre-computed before the correction pipeline runs, ensuring the error handler always has the intended path available. If the correction pipeline aborts (partial correction failure), the pre-computed path is unused — no write is attempted and no capsule is emitted. The pre-computation ordering is a code review responsibility — see verification.md for the accepted deferral.
```

### CC-4: Fix GFM anchor mismatch with → character

- [ ] **Step 5: Identify headings with → character**

```bash
rg "→" docs/superpowers/specs/skill-composability/*.md --line-number
```

- [ ] **Step 6: Rename headings and update cross-references**

For `capsule-contracts.md` heading `## Contract 2: NS → Dialogue (NS Handoff Block)`, rename to:

```markdown
## Contract 2: NS to Dialogue (NS Handoff Block)
```

Update all cross-file links that reference the old anchor. Search for `#contract-2` across all spec files and update anchors to match the new heading.

Do the same for any other headings containing `→` in `capsule-contracts.md`, `foundations.md`, or other files.

### CC-6: Fix citation precision in verification.md

- [ ] **Step 7: Read verification.md lines 63-64**

Read `verification.md` lines 63-64 (contract heading citations).

- [ ] **Step 8: Update to precise anchors**

Update verification.md citations:
- Replace citations to broad contract headings with more precise anchors: `#validity-criteria-contract-3` for validity claims, `#schema-constraints` for `record_status` claims.

### VR-7: Add interim topic_key control

- [ ] **Step 9: Add interim stub review requirement**

Add to `delivery.md` item #8 interim drift mitigation protocol:

```markdown
**topic_key scope guard (interim):** During composition contract authoring (item #6 delivery window), manually scan the contract draft for `topic_key` appearances in any control path (conditional branches, budget counter expressions, staleness predicates). `topic_key` is non-authoritative metadata — if it appears in a control path, flag as a spec violation.
```

### VR-10: Add positive assertion to tautology filter tests

- [ ] **Step 10: Read tautology filter verification row**

Read `verification.md` ~line 85 (tautology filter row).

- [ ] **Step 11: Add positive assertion**

Add to each tautology filter test case:

```markdown
Additionally assert: (3) at least one assumption IS present in the output (confirming the model generated assumptions and the filter ran, not that the output was empty). If `assumptions[]` is empty, the test is inconclusive — re-run with a fixture that reliably produces at least one assumption.
```

### VR-11: Add completion criterion for dialogue-orchestrated-briefing deferral

- [ ] **Step 12: Read deferred verification table**

Read `verification.md` deferred verification section (~line 145).

- [ ] **Step 13: Add completion criterion**

Add to the `dialogue-orchestrated-briefing` deferral entry:

```markdown
**Activation trigger:** When the dialogue skill text is authored (per [delivery.md](delivery.md#skill-text-changes) §Dialogue Skill Text Addition), activate this structural check: verify sentinel emission path and external consumption absence. Alternatively, add to `validate_composition_contract.py` acceptance criteria (verification.md validator table) for automatic activation on item #6 delivery.
```

### VR-12: Add interim implements_composition_contract check

- [ ] **Step 14: Add to delivery.md PR checklist**

Add to `delivery.md` item #8 interim drift mitigation protocol:

```markdown
**Contract marker verification (interim):** During stub authoring, reviewer MUST verify that `implements_composition_contract: v1` appears in active composition stub frontmatter (not in a comment, example, or disabled section). PR checklist item: "Confirmed: implements_composition_contract marker is within active stub boundaries."
```

### IE-7: Clarify tautology_filter_applied absent vs false

- [ ] **Step 15: Read pipeline-integration.md Stage B capability flags**

Read `pipeline-integration.md` §two-stage-admission, Stage B (~lines 34-39).

- [ ] **Step 16: Add presence validation step**

Add to the `tautology_filter_applied` flag description:

```markdown
**Presence validation:** After the NS adapter populates `upstream_handoff`, verify that `tautology_filter_applied` key is present (not just that its value is valid). If absent, log a structured warning: "adapter omitted tautology_filter_applied; treating as false for evaluation — explicit false preferred for debuggability." The materiality evaluator ([routing-and-materiality.md](routing-and-materiality.md#material-delta-gating) Step 0) treats absent identically to `false`, but the warning distinguishes adapter implementation gaps from intentional `false` signals.
```

- [ ] **Step 17: Verify all cross-references**

```bash
rg "validity-criteria|schema-constraints|skill-text-changes|contract-2.*ns" docs/superpowers/specs/skill-composability/ | head -20
```

Confirm all updated anchors resolve correctly, especially any changed by the CC-4 heading rename.

- [ ] **Step 18: Commit**

```bash
git add docs/superpowers/specs/skill-composability/capsule-contracts.md docs/superpowers/specs/skill-composability/verification.md docs/superpowers/specs/skill-composability/delivery.md docs/superpowers/specs/skill-composability/pipeline-integration.md docs/superpowers/specs/skill-composability/routing-and-materiality.md docs/superpowers/specs/skill-composability/foundations.md
git commit -m "fix(spec): remediate 9 P2 findings from skill-composability review round 7

CE-8: Clarify selected_tasks validity criteria comment.
CE-9: Add record_path pre-computation ordering note.
CC-4: Fix GFM anchor mismatch (rename headings with → character).
CC-6: Update verification.md citations to precise anchors.
VR-7: Add interim topic_key scope guard to PR checklist.
VR-10: Add positive assertion to tautology filter tests.
VR-11: Add completion criterion for briefing sentinel deferral.
VR-12: Add interim contract marker verification to PR checklist.
IE-7: Add tautology_filter_applied presence validation step.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Finding-to-Task Cross-Reference

| Finding | Priority | Task | Step(s) | Files Modified |
|---------|----------|------|---------|----------------|
| SY-4 | P0 | T1 | 2-4 | routing-and-materiality.md, verification.md |
| VR-4 | P0 | T1 | 5-6 | verification.md |
| AA-1 | P1 | T2 | 1-3 | spec.yaml, foundations.md |
| AA-3 | P1 | T2 | 4-5 | spec.yaml |
| AA-4 | P1 | T2 | 6-7 | spec.yaml |
| SY-3 | P1 | T2 | 8-9 | capsule-contracts.md |
| AA-5 | P2 | T2 | 10-11 | foundations.md |
| AA-6 | P2 | T2 | 12-13 | decisions.md |
| SY-1 | P1 | T3 | 1-3 | routing-and-materiality.md |
| CE-3 | P1 | T3 | 4-5 | routing-and-materiality.md |
| CE-7 | P1 | T3 | 6 | routing-and-materiality.md |
| CE-10 | P1 | T3 | 7-10 | lineage.md |
| CE-5 | P1 | T3 | 11-12 | routing-and-materiality.md |
| IE-2 | P1 | T3 | 13-14 | routing-and-materiality.md |
| IE-5 | P1 | T3 | 15-16 | routing-and-materiality.md |
| CE-4 | P1 | T3 | 17-18 | capsule-contracts.md |
| CE-11 | P1 | T3 | 19-20 | routing-and-materiality.md |
| SY-2 | P1 | T3 | 21-22 | routing-and-materiality.md |
| IE-4 | P1 | T3 | 23-24 | delivery.md |
| CC-2 | P1 | T4 | 1-2 | verification.md |
| VR-5 | P1 | T4 | 1-2 | verification.md |
| VR-3 | P1 | T4 | 3-4 | verification.md |
| VR-6 | P1 | T4 | 5-6 | verification.md |
| VR-8 | P1 | T4 | 7-8 | verification.md |
| VR-9 | P1 | T4 | 9-10 | verification.md |
| VR-13 | P1 | T4 | 11-12 | verification.md |
| VR-14 | P1 | T4 | 13-14 | verification.md |
| CC-3 | P1 | T4 | 15-16 | verification.md |
| CE-8 | P2 | T5 | 1-2 | capsule-contracts.md |
| CE-9 | P2 | T5 | 3-4 | routing-and-materiality.md |
| CC-4 | P2 | T5 | 5-6 | capsule-contracts.md, foundations.md, verification.md, pipeline-integration.md |
| CC-6 | P2 | T5 | 7-8 | verification.md |
| VR-7 | P2 | T5 | 9 | delivery.md |
| VR-10 | P2 | T5 | 10-11 | verification.md |
| VR-11 | P2 | T5 | 12-13 | verification.md, delivery.md |
| VR-12 | P2 | T5 | 14 | delivery.md |
| IE-7 | P2 | T5 | 15-16 | pipeline-integration.md |

**Total: 37 findings → 5 tasks → 5 commits**
