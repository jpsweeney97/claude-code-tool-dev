# CCDI Spec Remediation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all P0 (4) and P1 (22) findings from the CCDI spec review, producing a consistent, implementation-ready specification.

**Architecture:** All changes are spec-document edits in `docs/superpowers/specs/ccdi/`. Tasks are ordered by dependency: spec.yaml metadata → data-model.md schema → registry.md/classifier.md/integration.md contracts → delivery.md test specifications. Each task targets one file and groups related findings.

**Tech Stack:** Markdown spec files with YAML frontmatter. No code changes.

**Source findings:** `.review-workspace/synthesis/report.md` (run 2). Finding IDs prefixed SY- reference canonical findings; source reviewer IDs (AA-, CE-, CC-, SP-, VR-) reference `.review-workspace/findings/{role-id}.md`.

---

## File Map

| File | Findings addressed | Task |
|------|-------------------|------|
| `spec.yaml` | SY-8, SY-29 | 1 |
| `data-model.md` | SY-1, SY-7, SY-27, SY-28, SY-32 | 2 |
| `registry.md` | SY-2, SY-9, SY-30, SY-32 (entry structure) | 3 |
| `classifier.md` | SY-6 | 4 |
| `integration.md` | SY-5, SY-31 | 5 |
| `delivery.md` — P0 fixes | SY-11, SY-12, SY-13 | 6 |
| `delivery.md` — P1 test specs | SY-14, SY-15, SY-16, SY-17, SY-18, SY-19, SY-20, SY-21, SY-22, SY-23 | 7 |

**Dependency order:** Task 1 → Task 2 → Task 3 (depends on 2 for new field) → Tasks 4, 5 (parallel, no deps) → Tasks 6, 7 (depend on 2, 3 for schema/rule changes).

---

### Task 1: spec.yaml — Fix Metadata Inconsistencies

**Findings:** SY-8 (data-model in architecture_rule precedence without claim), SY-29 (RegistrySeed boundary rule unidirectional)

**Files:**
- Modify: `docs/superpowers/specs/ccdi/spec.yaml`

- [ ] **Step 1: Read spec.yaml and review current authorities and boundary_rules**

Read `spec.yaml` fully. Note:
- Line 10: `data-model.default_claims: [persistence_schema]` — no `architecture_rule`
- Line 44: `claim_precedence.architecture_rule: [foundation, data-model, decisions]` — data-model listed
- Boundary rules 1a-1c: `on_change_to: [data-model]` → review `[classifier-contract, registry-contract, packet-contract]` — does NOT include registry-contract for RegistrySeed-specific changes (only for general schema changes)

- [ ] **Step 2: Add `architecture_rule` to data-model default_claims (SY-8)**

data-model.md's version axes, overlay merge semantics, and config schema are cross-cutting architectural constraints. Adding the claim is the correct fix (option (a) from AA-4).

Change line 11 from:
```yaml
    default_claims: [persistence_schema]
```
to:
```yaml
    default_claims: [persistence_schema, architecture_rule]
```

**Verification:** This grounds the existing `claim_precedence.architecture_rule` entry that already lists `data-model` at position 2. Check that effective claims for data-model.md do not exceed 3 (now 2: persistence_schema + architecture_rule ✓).

- [ ] **Step 3: Annotate boundary rule 1 to cover RegistrySeed changes (SY-29)**

Boundary rule 1 (`on_change_to: [data-model]`) already routes to `[classifier-contract, registry-contract, packet-contract]`. The RegistrySeed→TopicRegistryEntry dependency is covered by the existing data-model→registry-contract edge. Add a `reason` clarification rather than a new rule.

Change boundary rule 1's reason from:
```yaml
    reason: Schema changes to inventory, aliases, or config affect all downstream consumers.
```
to:
```yaml
    reason: Schema changes to inventory, aliases, config, or RegistrySeed durable-field subset affect all downstream consumers.
```

- [ ] **Step 4: Verify cross-references**

Confirm `data-model.md` line 248 "Authority scope" paragraph still makes sense with the new claim. (It will — adding `architecture_rule` makes the paragraph's implicit claim explicit.)

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/ccdi/spec.yaml
git commit -m "fix(ccdi): add architecture_rule to data-model claims, annotate boundary rule 1 for RegistrySeed"
```

---

### Task 2: data-model.md — Fix Schema Definitions

**Findings:** SY-1 (AppliedRule.operation enum, P0), SY-7 (precedence ruling removal), SY-27 (DenyRule.penalty semantics), SY-28 (RegistrySeed coverage sub-fields), SY-32 (suppressed_docs_epoch field)

**Files:**
- Modify: `docs/superpowers/specs/ccdi/data-model.md`

- [ ] **Step 1: Read data-model.md — note lines 77–88 (DenyRule), 144–153 (AppliedRule), 161–177 (RegistrySeed), 248 (Authority scope)**

- [ ] **Step 2: Add "override_config" to AppliedRule.operation enum (SY-1, P0)**

Change the `operation` field in the AppliedRule table (line 151) from:
```
| `operation` | `"add_topic" \| "remove_alias" \| "add_deny_rule" \| "override_weight" \| "replace_aliases" \| "replace_refs" \| "replace_queries"` | What the rule did |
```
to:
```
| `operation` | `"add_topic" \| "remove_alias" \| "add_deny_rule" \| "override_weight" \| "replace_aliases" \| "replace_refs" \| "replace_queries" \| "override_config"` | What the rule did |
```

Also update the `target` field description (line 152) from:
```
| `target` | string | TopicKey or alias text affected |
```
to:
```
| `target` | string | TopicKey or alias text affected; for `override_config`, the dot-separated config key path (e.g., `classifier.confidence_high_min_weight`) |
```

- [ ] **Step 3: Clarify DenyRule.penalty semantics for action=drop (SY-27)**

In the DenyRule table (line 85), change the `penalty` row from:
```
| `penalty` | number \| null | Weight reduction for `downrank`; null or omit for `drop` (penalty is not applied when action is `drop`) |
```
to:
```
| `penalty` | number \| null | Weight reduction for `downrank` (required, non-null). Must be null for `drop` — penalty is not applied when action is `drop`. |
```

- [ ] **Step 4: Enumerate coverage sub-fields in RegistrySeed (SY-28)**

In the RegistrySeed `entries` field description (line 172), change:
```
containing only durable-state fields (`topic_key`, `family_key`, `state`, `first_seen_turn`, `last_seen_turn`, `last_injected_turn`, `last_query_fingerprint`, `consecutive_medium_count`, `suppression_reason`, `deferred_reason`, `deferred_ttl`, `coverage`). Attempt-local fields (`looked_up`, `built`) are never included.
```
to:
```
containing only durable-state fields (`topic_key`, `family_key`, `state`, `first_seen_turn`, `last_seen_turn`, `last_injected_turn`, `last_query_fingerprint`, `consecutive_medium_count`, `suppression_reason`, `suppressed_docs_epoch`, `deferred_reason`, `deferred_ttl`, `coverage` — all sub-fields: `overview_injected`, `facets_injected`, `pending_facets`, `family_context_available`, `injected_chunk_ids`). Topics in attempt-local states (`looked_up`, `built`) are not persisted to the seed — these states exist only within a single CLI invocation.
```

Note: `suppressed_docs_epoch` is a new field being added in step 5. The terminology fix (SY-37 "fields" → "states") is P2 but included here since we're editing the same sentence.

- [ ] **Step 5: Add `suppressed_docs_epoch` field concept to RegistrySeed (SY-32)**

This field will be formally added to `TopicRegistryEntry` in Task 3 (registry.md). In data-model.md, it only needs to appear in the durable-field list (done in step 4 above). No separate schema definition needed here — the field's schema lives in registry.md's entry structure.

- [ ] **Step 6: Remove behavior_contract precedence ruling from Authority scope paragraph (SY-7)**

In the "Authority scope" paragraph (line 248), change:
```
**Authority scope:** This section is normative for the config file's **schema** (field names, types, default values) under the `persistence_schema` claim. The **behavioral meaning** of each parameter is authoritative in its consumer file (classifier-contract, registry-contract, or packet-contract). For precedence between config schema and behavioral contracts, see `spec.yaml` → `claim_precedence`.
```
to:
```
**Authority scope:** This section is normative for the config file's **schema** (field names, types, default values) under the `persistence_schema` claim. The **behavioral meaning** of each parameter is authoritative in its consumer file — see `spec.yaml` → `claim_precedence` for resolution order.
```

This removes the arbitration statement while preserving the reference to spec.yaml for precedence resolution.

- [ ] **Step 7: Verify cross-references**

Check that:
- Line 239 `operation: "override_config"` now matches the enum
- RegistrySeed durable-field list matches registry.md entry structure (after Task 3)
- Config consumers table (lines 241–244) is unaffected

- [ ] **Step 8: Commit**

```bash
git add docs/superpowers/specs/ccdi/data-model.md
git commit -m "fix(ccdi): add override_config to enum, clarify DenyRule.penalty, enumerate RegistrySeed coverage fields, add suppressed_docs_epoch"
```

---

### Task 3: registry.md — Fix State Lifecycle Rules

**Findings:** SY-2 (coverage fields missing from Field Update Rules), SY-9 (reinit-on-corruption vs resilience), SY-30 (last_seen_turn ambiguity), SY-32 (suppressed_docs_epoch in entry structure)

**Files:**
- Modify: `docs/superpowers/specs/ccdi/registry.md`

- [ ] **Step 1: Read registry.md — note lines 13–33 (entry structure), 80–95 (Field Update Rules), 119–128 (Family vs Leaf Coverage), 195–205 (Failure Modes)**

- [ ] **Step 2: Add `suppressed_docs_epoch` to TopicRegistryEntry (SY-32)**

In the entry structure (after `suppression_reason` at line 25), add:
```
├── suppressed_docs_epoch: string | null  # docs_epoch at time of suppression; used for re-entry comparison
```

- [ ] **Step 3: Add Field Update Rules for coverage.overview_injected and family_context_available (SY-2)**

Add two new rows to the Field Update Rules table (after the `[built] → injected` row at line 90):

```
| `[built] → injected` (coverage_target=family, facet=overview) | Additionally: `coverage.overview_injected` ← true |
| `absent → detected` (leaf, parent family has `coverage.overview_injected = true`) | Additionally: `coverage.family_context_available` ← true |
| `absent → detected` (leaf, parent family not injected or not overview-covered) | `coverage.family_context_available` ← false |
```

- [ ] **Step 4: Add Field Update Rule for suppressed_docs_epoch (SY-32)**

Add to the Field Update Rules table after the `[looked_up] → suppressed` row:

```
| `[looked_up] → suppressed` | Additionally: `suppressed_docs_epoch` ← current inventory's `docs_epoch` |
| `suppressed → detected` (re-entry) | Additionally: `suppressed_docs_epoch` ← null |
```

- [ ] **Step 5: Clarify last_seen_turn "(if present)" qualifier (SY-30)**

Change the "Re-detection at non-medium confidence (or topic absent)" row from:
```
| Re-detection at non-medium confidence (or topic absent) | `last_seen_turn` ← current turn (if present), `consecutive_medium_count` ← 0 |
```
to two separate rows:
```
| Re-detection at non-medium confidence (entry exists) | `last_seen_turn` ← current turn, `consecutive_medium_count` ← 0 |
| Topic absent from classifier output (entry exists) | `consecutive_medium_count` ← 0 |
```

The "topic absent" case does NOT update `last_seen_turn` — the topic wasn't seen, so the "last seen" turn shouldn't change. The "(if present)" qualifier was trying to express "if the entry exists in the registry" which is always true for these re-detection rows.

- [ ] **Step 6: Reconcile registry reinit with resilience principle (SY-9)**

In the Failure Modes table (line 202), change:
```
| Registry file missing or corrupt | CLI error | Reinitialize empty registry, lose coverage history |
```
to:
```
| Registry file missing or corrupt | CLI error | Reinitialize empty registry, log warning. Coverage history is lost — topics already sent may be re-injected. This is an acceptable degradation: premise enrichment is idempotent from Codex's perspective (duplicate context is low-harm). See [resilience principle](foundations.md#resilience-principle). |
```

Also add a note in `foundations.md` (Task 3 sub-step):

- [ ] **Step 6a: Add registry reinit acknowledgment to foundations.md**

In `foundations.md` Resilience Principle section (after line 46), add:

```
**Registry reinit exception:** When the topic registry is corrupted mid-dialogue, CCDI reinitializes an empty registry and continues. This may re-inject topics already sent — an acceptable degradation because premise enrichment is idempotent (duplicate context is low-harm, unlike missing context).
```

- [ ] **Step 7: Update Suppression Re-Entry section**

In the Suppression Re-Entry section (line 114), update the `weak_results` re-entry trigger to reference the new field:

Change:
```
| `weak_results` | `docs_epoch` changes (index updated) OR a new query facet is requested for the topic OR an `extends_topic` semantic hint resolves to the suppressed topic (see [Semantic Hints](#semantic-hints)) |
```
to:
```
| `weak_results` | `docs_epoch` differs from `suppressed_docs_epoch` (index updated since suppression — uses null comparison rules below) OR a new query facet is requested for the topic OR an `extends_topic` semantic hint resolves to the suppressed topic (see [Semantic Hints](#semantic-hints)) |
```

- [ ] **Step 8: Verify cross-references**

Check that:
- RegistrySeed durable-field list in data-model.md (updated in Task 2) matches the new entry structure
- Field Update Rules table is complete for all durable fields
- Suppression Re-Entry now references the stored epoch for comparison

- [ ] **Step 9: Commit**

```bash
git add docs/superpowers/specs/ccdi/registry.md docs/superpowers/specs/ccdi/foundations.md
git commit -m "fix(ccdi): complete Field Update Rules, add suppressed_docs_epoch, clarify last_seen_turn, reconcile reinit with resilience"
```

---

### Task 4: classifier.md — Qualify Low-Confidence Claim

**Findings:** SY-6 (low-confidence claim unqualified for CCDI-lite mode)

**Files:**
- Modify: `docs/superpowers/specs/ccdi/classifier.md`

- [ ] **Step 1: Read classifier.md line 81 (low-confidence statement)**

Current text: "Low-confidence detections are recorded in the [topic registry](registry.md) but never trigger injection alone."

- [ ] **Step 2: Qualify the statement for CCDI-lite mode**

Change line 81 from:
```
Low-confidence detections are recorded in the [topic registry](registry.md) but never trigger injection alone.
```
to:
```
In Full CCDI mode, low-confidence detections are recorded in the [topic registry](registry.md) but never trigger injection alone. In CCDI-lite mode (no registry), low-confidence detections are silently discarded after classification.
```

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/ccdi/classifier.md
git commit -m "fix(ccdi): qualify low-confidence detection claim for CCDI-lite mode"
```

---

### Task 5: integration.md — Fix Contract Gaps

**Findings:** SY-5 (ccdi_debug in wrong authority), SY-31 (injected_chunk_ids omitted from CLI contract)

**Files:**
- Modify: `docs/superpowers/specs/ccdi/integration.md`

- [ ] **Step 1: Read integration.md — note lines 14–20 (CLI command table), 142–162 (Registry Seed Handoff)**

- [ ] **Step 2: Add ccdi_debug to delegation envelope definition (SY-5)**

In the Registry Seed Handoff section (after the `ccdi_seed` envelope description at line 158), add a new subsection:

```markdown
### Delegation Envelope Fields

The `/dialogue` skill passes these optional fields to `codex-dialogue`:

| Field | Type | Source | Purpose |
|-------|------|--------|---------|
| `ccdi_seed` | file path (string) | ccdi-gatherer output | Initial registry file for mid-dialogue CCDI loop. Absent → mid-dialogue CCDI disabled. |
| `scope_envelope` | object | context-gatherers | Existing field — repo evidence scope. |
| `ccdi_debug` | boolean \| absent | `/dialogue` skill | When `true`, `codex-dialogue` emits `ccdi_trace` in its output. Absent or `false` → no trace. Testing-only; see [delivery.md#debug-gated-ccdi_trace](delivery.md#debug-gated-ccdi_trace) for trace schema. |
```

- [ ] **Step 3: Add --mark-injected side-effect details to CLI contract (SY-31)**

In the `build-packet` command description (line 18), after "registry updated in-place if `--mark-injected`", add a parenthetical or note:

Change:
```
| `build-packet --results-file <path> [--registry-file <path>] --mode initial\|mid_turn [--mark-injected] [--mark-deferred <topic_key> --deferred-reason <reason>] [--skip-build] [--config <path>]` | Search results + optional registry | Rendered markdown (stdout); registry updated in-place if `--mark-injected` or `--mark-deferred` | Both modes |
```
After this table, add a new paragraph:

```markdown
**`--mark-injected` registry side-effects:** When `--mark-injected` is passed with `--registry-file`, the following fields are updated per the [Field Update Rules](registry.md#field-update-rules): `state` → `injected`, `last_injected_turn`, `last_query_fingerprint`, `coverage.injected_chunk_ids` (appended from built packet's chunk IDs), `coverage.facets_injected` (appended), `coverage.pending_facets` (served facet removed if present), `consecutive_medium_count` ← 0.
```

- [ ] **Step 4: Verify cross-references**

Check that:
- delivery.md references to `ccdi_debug` can now point to integration.md
- `--mark-injected` field list matches registry.md Field Update Rules (after Task 3)

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/ccdi/integration.md
git commit -m "fix(ccdi): add ccdi_debug to delegation envelope, document --mark-injected side-effects"
```

---

### Task 6: delivery.md — Fix P0 Test Specification Gaps

**Findings:** SY-11 (low-confidence injection-gating test, P0), SY-12 (single medium negative test, P0), SY-13 (replay harness category mismatch, P0)

**Files:**
- Modify: `docs/superpowers/specs/ccdi/delivery.md`

- [ ] **Step 1: Read delivery.md — note lines 107–127 (Classifier Tests), 129–166 (Registry Tests), 239–268 (Replay Harness)**

- [ ] **Step 2: Add low-confidence injection-gating test to Registry Tests (SY-11)**

Add a new row to the Registry Tests table (after the existing "Consecutive-turn medium threshold" row at line 152):

```
| Low-confidence topic → detected but never injected | Topic with `confidence: low` → enters `detected` state AND is excluded from `dialogue-turn` injection candidates output; no injection fires regardless of turn count |
```

**Note:** Check if this test row already exists — VR-1 found it was added at delivery.md line 165 in a prior spec update. If already present, verify the description matches the above. If present, mark this step as already-fixed and skip.

- [ ] **Step 3: Add single medium-confidence negative test to Registry Tests (SY-12)**

Add a new row to the Registry Tests table:

```
| Single medium-confidence → no initial injection | 1 medium-confidence topic (no same-family companion) → injection candidates empty; no CCDI packet built |
```

**Note:** Same as step 2 — check if this was added at delivery.md line 164 in a prior update. If already present, verify and skip.

- [ ] **Step 4: Fix Three-Layer table description and replay harness claims (SY-13)**

First, update the Three-Layer Approach table (line 77) to reflect the narrowed harness scope. Change the Replay harness row from:
```
| **Replay harness** | Agent integration ([prepare/commit](integration.md#mid-dialogue-phase-per-turn-in-codex-dialogue) loop, [semantic hints](registry.md#semantic-hints), tool-call sequence) | Structured `ccdi_trace` + assertion on tool-call sequence and outcomes, not prose |
```
to:
```
| **Replay harness (Layer 2a)** | CLI pipeline correctness ([prepare/commit](integration.md#mid-dialogue-phase-per-turn-in-codex-dialogue) loop, [semantic hints](registry.md#semantic-hints), state transitions) | Structured `ccdi_trace` + assertion on CLI input/output and registry state, not prose |
| **Agent sequence tests (Layer 2b)** | Agent tool-call ordering (codex-dialogue invokes CLI commands in correct sequence) | Live agent invocation with mocked tools |
```

Then, in the Replay Harness section (line 97), change the tool-call sequence assertion description from:
```
- **Tool-call sequence:** classify → dialogue-turn → search_docs → build-packet (prepare) → codex-reply → build-packet --mark-injected (commit)
```
to:
```
- **CLI pipeline sequence:** classify → dialogue-turn → build-packet (prepare) → build-packet --mark-injected (commit). The harness validates the deterministic CLI pipeline produces correct outputs given canned inputs. `search_docs` results are canned from fixture data; `codex-reply` is assumed successful unless the fixture sets `codex_reply_error: true`.
```

Finally, add a clarifying paragraph after the execution model description (line 268):

```markdown
**Scope limitation:** The replay harness verifies CLI pipeline correctness (Layer 2a). It does NOT verify that the `codex-dialogue` agent invokes CLI commands in the correct sequence — that requires a live agent invocation with mocked tools (Layer 2b). Layer 2b is a separate integration test category:

| Test | Verifies |
|------|----------|
| Agent invokes classify before dialogue-turn | Tool-call ordering in codex-dialogue |
| Agent skips build-packet when no candidates | Conditional tool invocation |
| Agent calls --mark-injected only after successful codex-reply | Prepare/commit ordering |
```

- [ ] **Step 5: Verify cross-references**

Check that:
- The Three-Layer table description now correctly matches Layer 2a (replay harness) and 2b (agent sequence) scopes
- Replay harness fixture format references are still accurate

- [ ] **Step 6: Commit**

```bash
git add docs/superpowers/specs/ccdi/delivery.md
git commit -m "fix(ccdi): add missing P0 test specs, clarify replay harness scope"
```

---

### Task 7: delivery.md — Fix P1 Test Specification Gaps

**Findings:** SY-14 (ccdi_seed absent test), SY-15 (hint×state fixtures), SY-16 (docs_epoch null-case tests), SY-17 (consecutive_medium_count reset test), SY-18 (ccdi_debug trace completeness), SY-19 (false-positive labeling protocol), SY-20 (pending_facets removal test), SY-21 (automatic suppression test), SY-22 (injected_chunk_ids population test), SY-23 (--skip-build test)

**Files:**
- Modify: `docs/superpowers/specs/ccdi/delivery.md`

- [ ] **Step 1: Read delivery.md — note lines 129–166 (Registry Tests), 167–178 (Packet Builder Tests), 183–192 (CLI Integration Tests), 271–282 (Replay Fixtures), 60–68 (Diagnostics/labeling)**

- [ ] **Step 2: Add missing Registry Tests (SY-16, SY-17, SY-20, SY-22)**

Add to the Registry Tests table:

```
| docs_epoch null comparison: null == null → no re-entry | Suppressed topic at docs_epoch=null, re-evaluated at docs_epoch=null → suppression_reason unchanged, state stays `suppressed` |
| docs_epoch null comparison: null → non-null → re-entry | Suppressed topic at docs_epoch=null, re-evaluated at docs_epoch="2026-03-20" → state transitions to `detected`, `suppressed_docs_epoch` ← null |
| docs_epoch null comparison: non-null → null → re-entry | Suppressed topic at docs_epoch="A", re-evaluated at docs_epoch=null → state transitions to `detected` |
| consecutive_medium_count reset after injection | Medium topic turn 1 (count=1), turn 2 (count=2, injection fires, committed) → turn 3 same medium topic → injection does NOT fire (counter reset to 0 at injection; count=1, threshold not yet met) |
| pending_facets cleared after serving | `contradicts_prior` hint adds facet F to `pending_facets` → injection at facet F succeeds via `--mark-injected` → verify `coverage.pending_facets` does NOT contain F AND `coverage.facets_injected` DOES contain F |
| injected_chunk_ids populated at commit | `build-packet --mark-injected` with result set containing chunk IDs [X, Y] → verify `coverage.injected_chunk_ids` contains [X, Y] → subsequent `build-packet` call with same results → chunk IDs excluded from output |
```

- [ ] **Step 3: Add missing CLI Integration Tests (SY-21, SY-23)**

Add to the CLI Integration Tests table:

```
| Automatic suppression requires registry | `build-packet` returns empty output WITHOUT `--registry-file` → no suppression written (stdout empty, no side effects). With `--registry-file` → `suppressed: weak_results` written. Tests the conditional nature of automatic suppression. |
| `--skip-build` with `--mark-deferred` skips packet construction | `build-packet --mark-deferred <key> --deferred-reason <r> --skip-build --registry-file <path>` → registry writes deferred state AND stdout is empty (no packet built) |
| `--skip-build` without `--mark-deferred` is ignored | `build-packet --skip-build --results-file <path> --mode initial` → normal packet construction proceeds (flag silently ignored) |
```

- [ ] **Step 4: Strengthen ccdi_seed absent test (SY-14)**

In the Boundary Contract Tests table (line 210), change:
```
| Mid-dialogue CCDI disabled without ccdi_seed | Delegation envelope without `ccdi_seed` field → `codex-dialogue` agent does not invoke `dialogue-turn` or `build-packet` during turn loop; diagnostics show `phase: initial_only` |
```
to:
```
| Mid-dialogue CCDI disabled without ccdi_seed | Delegation envelope without `ccdi_seed` field → diagnostics show `phase: initial_only` AND agent tool-call log contains zero invocations of `dialogue-turn` or `build-packet` (Layer 2b test — requires live agent with mocked tools) |
```

- [ ] **Step 5: Add missing replay harness fixture scenarios (SY-15)**

Add to the Required fixture scenarios table:

```
| `hint_contradicts_prior_on_deferred.replay.json` | `contradicts_prior` hint on deferred topic → elevated to materially new, scheduled for lookup |
| `hint_extends_topic_on_deferred.replay.json` | `extends_topic` hint on deferred topic → elevated to materially new, scheduled for lookup |
| `hint_unknown_topic_ignored.replay.json` | Hint with `claim_excerpt` matching no inventory topic → hint ignored, no state change, no scheduling effect |
```

- [ ] **Step 6: Strengthen ccdi_debug trace test (SY-18)**

In the Integration Tests table (line 223), change:
```
| `ccdi_debug` gating of trace emission | With `ccdi_debug=true` in delegation envelope → `ccdi_trace` key present in agent output; with `ccdi_debug` absent → no `ccdi_trace` key |
```
to:
```
| `ccdi_debug` gating of trace emission | With `ccdi_debug=true` → `ccdi_trace` key present in agent output AND each trace entry contains all required fields (`classifier_result`, `candidates`, `action`, `packet_staged`, `scout_conflict`, `commit`); with `ccdi_debug` absent → no `ccdi_trace` key |
```

- [ ] **Step 7: Add false-positive labeling protocol (SY-19)**

In the Shadow Mode Kill Criteria section (after line 68), add:

```markdown
**False-positive labeling protocol:** During shadow evaluation, label a minimum of 100 detected topics across 10+ dialogues. For each topic in `topics_detected`, a labeler checks whether the input text genuinely discusses a Claude Code extension concept. Topics where the input text uses extension terminology in a non-Claude-Code context (e.g., "React hook", "webpack plugin") are false positives. `false_positive_rate` = `false_positive_topic_detections / len(topics_detected)`. The 10% kill threshold requires statistical confidence: label at least 100 topics before evaluating.
```

**Note:** Check if this text already exists — VR-9 noted it might have been added in a prior update. If already present at lines 64–68, verify the content matches and skip.

- [ ] **Step 8: Verify all new test rows have unique names and don't duplicate existing rows**

Scan the full Registry Tests, CLI Integration Tests, Boundary Contract Tests, and Replay Fixtures tables for duplicates.

- [ ] **Step 9: Commit**

```bash
git add docs/superpowers/specs/ccdi/delivery.md
git commit -m "fix(ccdi): add missing test specs for P1 verification gaps"
```

---

## Post-Completion Verification

After all 7 tasks:

- [ ] **V1: Cross-reference audit** — Run a grep for all `#anchor` links across all 9 spec files. Verify each anchor resolves to a heading in the target file.
- [ ] **V2: Field Update Rules completeness** — Read registry.md Field Update Rules table. Verify every durable field in TopicRegistryEntry has at least one transition row that writes it.
- [ ] **V3: RegistrySeed durable-field list** — Compare data-model.md RegistrySeed durable-field list against registry.md entry structure. Every durable field in the entry should appear in the RegistrySeed list.
- [ ] **V4: spec.yaml consistency** — Verify all authorities in `claim_precedence` and `fallback_authority_order` have default_claims that include (or plausibly could include) the claims they govern.
- [ ] **V5: Boundary rules** — Verify all 5 boundary rules still reference valid authorities.
