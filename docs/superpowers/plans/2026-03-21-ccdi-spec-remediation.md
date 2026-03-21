# CCDI Spec Review Remediation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Remediate all open P0 and P1 findings from the spec review at `.review-workspace/synthesis/report.md`.

**Architecture:** All changes are to spec files in `docs/superpowers/specs/ccdi/`. No code changes. Each task produces a self-contained commit of related spec edits. Ordered by dependency: schema foundations → CLI interface → contracts → authority model → test specifications.

**Tech Stack:** Markdown spec files, YAML manifest (spec.yaml)

**Prior remediation:** 10 commits already fixed SY-1, CE-1, SP-6, VR-4–9, VR-11. This plan covers the 20 remaining open findings (5 P0 + 15 P1).

---

## File Map

| File | Changes | Findings Addressed |
|------|---------|-------------------|
| `data-model.md` | Add overlay file format section; fix config_keys mapping; replace embedded precedence ruling | SY-4, SP-3, AA-1 |
| `integration.md` | Add coverage_target to candidates JSON + build-packet flag; add scout-deferral CLI; define composed target; fix threshold enforcement; fix confidence type; add overview_injected to mark-injected | SP-1, CE-4, VR-1, CE-7, CE-8, CE-6 |
| `registry.md` | Add extends_topic Field Update Rule | CE-5 |
| `spec.yaml` | Merge duplicate boundary rules; document claim_precedence semantics | AA-9, CC-8 |
| `README.md` | Fix authority table data-model claims | SY-2 |
| `delivery.md` | Add shadow fields to diagnostics JSON; specify Layer 2b; fix trace field list; add boundary/alignment/assertion/penalty tests | VR-2, VR-3, VR-10, VR-12, VR-13, VR-14, VR-18 |

---

### Task 1: Fix coverage_target CLI propagation chain [P0: SP-1, P1: CE-6]

The `ClassifierResult` carries `coverage_target: "family" | "leaf"` but neither the `dialogue-turn` candidates JSON nor `build-packet` propagates it. This breaks `coverage.overview_injected` and the downstream `family_context_available` inheritance chain.

**Files:**
- Modify: `docs/superpowers/specs/ccdi/integration.md:32-46` (candidates JSON schema)
- Modify: `docs/superpowers/specs/ccdi/integration.md:18` (build-packet CLI command)
- Modify: `docs/superpowers/specs/ccdi/integration.md:26` (mark-injected side-effects)
- Modify: `docs/superpowers/specs/ccdi/delivery.md:211` (boundary contract test)

- [x] **Step 1: Add `coverage_target` to the `dialogue-turn` candidates JSON example**

In `integration.md`, add `"coverage_target": "leaf"` to the JSON example block (lines 34–43) and update the field description (line 46) to include `coverage_target` (`"family" | "leaf"` — the classifier's resolved coverage target for this candidate).

- [x] **Step 2: Add `--coverage-target` flag to `build-packet` CLI command**

In `integration.md` line 18, update the command signature:

```
| `build-packet --results-file <path> [--registry-file <path>] --mode initial|mid_turn [--coverage-target family|leaf] [--mark-injected] [--mark-deferred <topic_key> --deferred-reason <reason>] [--skip-build] [--config <path>]` | ...
```

Add a paragraph after the `--skip-build` paragraph explaining: `--coverage-target family|leaf` is required when `--mark-injected` is passed with `--registry-file`. Determines whether `coverage.overview_injected` is set (when `family` + facet=overview). Omitted in CCDI-lite mode (no registry).

- [x] **Step 3: Add `coverage.overview_injected` to `--mark-injected` side-effects**

In `integration.md` line 26, add to the field list: "when `--coverage-target family` and `facet=overview`: additionally `coverage.overview_injected` ← true."

- [x] **Step 4: Update boundary contract test**

In `delivery.md` line 211, update the "Classifier → registry" row to include: `coverage_target` flows through candidates JSON.

- [x] **Step 5: Update mid-dialogue flow to pass `--coverage-target`**

In `integration.md` lines 196-220, update the `build-packet` calls in both the prepare step (line 196-199) and commit step (lines 217-220) to include `--coverage-target <target>` from the candidates output.

- [x] **Step 6: Verify cross-references**

Check that `registry.md` lines 93-95 (Field Update Rules for overview_injected and family_context_available) are consistent with the new integration.md text.

- [x] **Step 7: Commit**

```bash
git add docs/superpowers/specs/ccdi/integration.md docs/superpowers/specs/ccdi/delivery.md
git commit -m "fix(ccdi): add coverage_target propagation through CLI pipeline (SP-1, CE-6)"
```

---

### Task 2: Add scout-priority deferral CLI invocation [P0: CE-4]

The mid-dialogue flow says "defer CCDI (scout wins)" but shows no CLI command to write `deferred: scout_priority` state, unlike the `target_mismatch` path which explicitly invokes `--mark-deferred`.

**Files:**
- Modify: `docs/superpowers/specs/ccdi/integration.md:210` (mid-dialogue flow)

- [x] **Step 1: Add CLI invocation to scout-priority branch**

In `integration.md` line 210, replace:
```
│   ├─ If candidates AND scout target exists: defer CCDI (scout wins)
```
With:
```
│   ├─ If candidates AND scout target exists:
│   │   └─ Bash: python3 topic_inventory.py build-packet \
│   │            --registry-file /tmp/ccdi_registry_<id>.json \
│   │            --mode mid_turn \
│   │            --mark-deferred <topic_key> --deferred-reason scout_priority \
│   │            --skip-build
```

Note: `--results-file` is omitted because no search has run for this candidate — the search step was skipped when the scout target was detected. `--skip-build` ensures no packet construction is attempted.

- [x] **Step 2: Add note about `--results-file` optionality for `--skip-build` path**

Add a clarification after the `--skip-build` paragraph in integration.md: "When `--skip-build` is passed with `--mark-deferred`, `--results-file` is not required — no packet construction occurs."

- [x] **Step 3: Commit**

```bash
git add docs/superpowers/specs/ccdi/integration.md
git commit -m "fix(ccdi): add scout-priority deferral CLI invocation (CE-4)"
```

---

### Task 3: Define "composed follow-up target" [P0: VR-1]

Scheduling rule 6 and integration.md reference "composed follow-up target" without ever defining it. The `target_mismatch_deferred.replay.json` fixture is unimplementable without this definition.

**Files:**
- Modify: `docs/superpowers/specs/ccdi/integration.md:200-201` (target-match check)
- Modify: `docs/superpowers/specs/ccdi/registry.md:146` (scheduling rule 6)
- Modify: `docs/superpowers/specs/ccdi/registry.md:205` (failure modes — fix "Step 6" label)
- Modify: `docs/superpowers/specs/ccdi/delivery.md:295` (fixture description)

- [x] **Step 1: Add target-match definition to integration.md**

After the mid-dialogue flow diagram (after line 224), add a new subsection:

```markdown
### Target-Match Predicate

The **composed follow-up target** is the follow-up question text that `codex-dialogue` has composed for the current turn (the text that will be sent to Codex via `codex-reply`). This text exists after Step 4 (composition) and before Step 5.5 (CCDI PREPARE).

The target-match check determines whether a CCDI packet is relevant to the composed question. A packet is **target-relevant** when at least one of the packet's `topics` appears as a substring (case-insensitive) in the composed follow-up text, OR the packet's primary `facet` matches a concept referenced in the follow-up text (determined by running the classifier on the follow-up text and checking for topic overlap).

**CLI interface:** The target-match check is performed by the agent, not the CLI. The agent:
1. Reads the `build-packet` stdout (rendered markdown).
2. Compares the packet's topic coverage against the composed follow-up text.
3. If not target-relevant: invokes `build-packet --mark-deferred --deferred-reason target_mismatch --skip-build`.

**Replay fixture assertion:** The `target_mismatch_deferred.replay.json` fixture provides a `composed_target` field in each trace entry. The harness feeds this to the target-match check logic. The assertion verifies the registry transitions to `deferred: target_mismatch` when the packet topics do not appear in the composed target.
```

- [x] **Step 2: Update registry.md scheduling rule 6**

In registry.md line 146, update the cross-reference to point to the new subsection: "The definition of 'composed follow-up target' is specified in [integration.md#target-match-predicate](integration.md#target-match-predicate)."

- [x] **Step 3: Fix registry.md failure modes "Step 6" label (CC-4)**

In registry.md line 205, change `"Target-match check in [Step 6]"` to `"Target-match check in [Step 5.5 (CCDI PREPARE)]"`.

- [x] **Step 4: Update fixture description**

In delivery.md line 295, update `target_mismatch_deferred.replay.json` description to reference the target-match predicate: "Fixture includes `composed_target` field; packet topics absent from target → `deferred: target_mismatch`."

- [x] **Step 5: Commit**

```bash
git add docs/superpowers/specs/ccdi/integration.md docs/superpowers/specs/ccdi/registry.md docs/superpowers/specs/ccdi/delivery.md
git commit -m "fix(ccdi): define composed follow-up target and target-match predicate (VR-1, CC-4)"
```

---

### Task 4: Add shadow mode fields to diagnostics schema [P0: VR-2]

Three kill-criterion fields are described as prose but absent from the normative JSON schema block.

**Files:**
- Modify: `docs/superpowers/specs/ccdi/delivery.md:37-56` (diagnostics JSON schema)
- Modify: `docs/superpowers/specs/ccdi/delivery.md:60-66` (shadow mode prose)

- [x] **Step 1: Add shadow fields to the diagnostics JSON block**

In delivery.md, add three fields inside the `"ccdi": { ... }` JSON block (after line 54, before the closing `}`):

```json
    "packets_target_relevant": 2,
    "packets_surviving_precedence": 1,
    "false_positive_topic_detections": 0
```

Add a comment line after the JSON block: "Fields `packets_target_relevant`, `packets_surviving_precedence`, and `false_positive_topic_detections` are present only when `status: "shadow"`. In active mode, they are omitted."

- [x] **Step 2: Update prose description**

Replace the "Additional fields" paragraph (lines 60-64) with: "The three shadow-mode fields listed in the schema above (`packets_target_relevant`, `packets_surviving_precedence`, `false_positive_topic_detections`) are emitted only when `status: "shadow"`. Their definitions:" followed by the existing bullet descriptions.

- [x] **Step 3: Commit**

```bash
git add docs/superpowers/specs/ccdi/delivery.md
git commit -m "fix(ccdi): add shadow mode fields to normative diagnostics schema (VR-2)"
```

---

### Task 5: Specify Layer 2b or explicitly defer [P0: VR-3]

Layer 2b (agent sequence tests) lists 3 test cases with no fixture format, runner, file location, or mock interface.

**Files:**
- Modify: `docs/superpowers/specs/ccdi/delivery.md:280-286` (Layer 2b section)
- Modify: `docs/superpowers/specs/ccdi/delivery.md:220` (boundary contract test Layer 2b reference)

- [x] **Step 1: Add Layer 2b specification section**

After the replay harness required fixtures table (after line 303), add:

```markdown
### Layer 2b: Agent Sequence Tests

Tests that the `codex-dialogue` agent invokes CLI commands in the correct sequence. Requires a live agent invocation with mocked tools — cannot be tested via the replay harness.

**File location:** `tests/test_ccdi_agent_sequence.py`

**Runner:** `uv run pytest tests/test_ccdi_agent_sequence.py -v`

**Mock interface:** Tests use a tool-call interceptor that records all Bash invocations matching `topic_inventory.py *`. The test asserts on the sequence of recorded commands, their arguments, and their relative ordering. `search_docs` calls are intercepted and return canned results. `codex-reply` calls are intercepted and return success unless the fixture specifies failure.

**Fixture format:** Each test case provides:
- `delegation_envelope`: the envelope passed to `codex-dialogue` (with/without `ccdi_seed`)
- `codex_responses`: array of canned Codex response strings (one per turn)
- `search_results`: canned `search_docs` results per query
- `expected_tool_sequence`: ordered array of expected CLI command patterns
```

- [x] **Step 2: Update boundary contract test reference**

In delivery.md line 220, change the parenthetical from "(Layer 2b test — requires live agent with mocked tools)" to "(Layer 2b test — see [Layer 2b: Agent Sequence Tests](#layer-2b-agent-sequence-tests))".

- [x] **Step 3: Commit**

```bash
git add docs/superpowers/specs/ccdi/delivery.md
git commit -m "fix(ccdi): specify Layer 2b agent sequence test infrastructure (VR-3)"
```

---

### Task 6: Fix contract completeness [P1: CE-5, CE-7, CE-8, VR-10]

Four P1 contract gaps: missing Field Update Rule for `extends_topic` on `injected`; initial injection threshold not enforced in pre-dialogue flow; candidates schema allows "low" confidence; trace field list incomplete.

**Files:**
- Modify: `docs/superpowers/specs/ccdi/registry.md:91-99` (Field Update Rules)
- Modify: `docs/superpowers/specs/ccdi/integration.md:46` (candidates confidence type)
- Modify: `docs/superpowers/specs/ccdi/integration.md:110` (pre-dialogue flow)
- Modify: `docs/superpowers/specs/ccdi/delivery.md:233` (ccdi_debug test)

- [x] **Step 1: Add `extends_topic` on `injected` Field Update Rule (CE-5)**

In registry.md, after line 91 (the `contradicts_prior` row), add:

```
| `extends_topic` hint resolves to `injected` topic | `coverage.pending_facets` ← append resolved facet (if not already in `facets_injected`; state stays `injected`) |
```

- [x] **Step 2: Fix candidates confidence type (CE-8)**

In integration.md line 46, change:
```
`confidence` (`"high" | "medium" | "low"`)
```
To:
```
`confidence` (`"high" | "medium"`)
```

Add a note: "Low-confidence topics are tracked in the registry but excluded from injection candidates — see [classifier.md#injection-thresholds](classifier.md#injection-thresholds)."

- [x] **Step 3: Specify initial threshold enforcement point (CE-7)**

In integration.md, update the pre-dialogue flow (around line 110). Change:
```
│  ├─ If topics → dispatch ccdi-gatherer in parallel with context-gatherers
```
To:
```
│  ├─ If injection threshold met → dispatch ccdi-gatherer in parallel
│  │   (threshold: 1 high-confidence OR 2+ medium-confidence same family;
│  │    per classifier.md#injection-thresholds)
│  ├─ If topics below threshold → proceed without CCDI
```

- [x] **Step 4: Fix ccdi_debug trace field list (VR-10)**

In delivery.md line 233, update the required fields list from:
```
(`classifier_result`, `candidates`, `action`, `packet_staged`, `scout_conflict`, `commit`)
```
To:
```
(`turn`, `classifier_result`, `semantic_hints`, `candidates`, `action`, `packet_staged`, `scout_conflict`, `commit`)
```

Add: "`semantic_hints` is present only when hints were provided for the turn; `null` otherwise."

- [x] **Step 5: Commit**

```bash
git add docs/superpowers/specs/ccdi/registry.md docs/superpowers/specs/ccdi/integration.md docs/superpowers/specs/ccdi/delivery.md
git commit -m "fix(ccdi): extends_topic rule, confidence type, threshold enforcement, trace fields (CE-5, CE-7, CE-8, VR-10)"
```

---

### Task 7: Fix authority model and structure [P1: SY-2, AA-1, AA-9, CC-8]

README omits architecture_rule for data-model; duplicate boundary rules; embedded precedence ruling; undocumented claim_precedence semantics.

**Files:**
- Modify: `docs/superpowers/specs/ccdi/README.md:21` (authority table)
- Modify: `docs/superpowers/specs/ccdi/spec.yaml:61-69` (boundary rules)
- Modify: `docs/superpowers/specs/ccdi/data-model.md:248` (precedence ruling)
- Modify: `docs/superpowers/specs/ccdi/spec.yaml:43-51` (precedence section)

- [x] **Step 1: Fix README authority table (SY-2)**

In README.md line 21, change:
```
| `data-model` | persistence_schema | Topic inventory schema, version axes, overlay merge, config, lifecycle |
```
To:
```
| `data-model` | persistence_schema, architecture_rule | Topic inventory schema, version axes, overlay merge semantics, config schema, lifecycle |
```

- [x] **Step 2: Merge duplicate boundary rules (AA-9)**

In spec.yaml, merge lines 61-69 (two rules with `on_change_to: [registry-contract]`) into one:

```yaml
  - on_change_to: [registry-contract]
    review_authorities: [integration, delivery, data-model]
    reason: Registry state changes and semantic hints schema affect CLI command behavior, argument shapes, test strategy, and RegistrySeed.entries durable-field subset.
```

- [x] **Step 3: Replace embedded precedence ruling (AA-1)**

In data-model.md line 248, replace:
```
**Authority scope:** This section is normative for the config file's **schema** (field names, types, default values) under the `persistence_schema` claim. The **behavioral meaning** of each parameter is authoritative in its consumer file — see `spec.yaml` → `claim_precedence` for resolution order.
```
With:
```
**Authority scope:** This section is normative for the config file's **schema** (field names, types, default values) under the `persistence_schema` claim. For behavioral meaning of each parameter, see the consumer file listed in the config consumers table above. See `spec.yaml` → `claim_precedence` for resolution order when consumer files conflict.
```

- [x] **Step 4: Document claim_precedence semantics (CC-8)**

In spec.yaml, add a comment block after the `precedence:` line (after line 42):

```yaml
  # NOTE: claim_precedence lists include authorities that may not hold the
  # arbitrated claim in their default_claims. This is intentional:
  # - `decisions` appears in all chains as a global override (locked decisions
  #   supersede all other authorities for any claim they address)
  # - Other authorities appear where they provide implementation-level
  #   elaboration relevant to resolving conflicts in that claim family
```

- [x] **Step 5: Commit**

```bash
git add docs/superpowers/specs/ccdi/README.md docs/superpowers/specs/ccdi/spec.yaml docs/superpowers/specs/ccdi/data-model.md
git commit -m "fix(ccdi): README claims, boundary rules, precedence ruling, claim_precedence docs (SY-2, AA-1, AA-9, CC-8)"
```

---

### Task 8: Add overlay file format and fix config_keys [P1: SY-4, SP-3]

The overlay file is a normative component with no defined JSON structure. The `dump_index_metadata` response field `config_keys` has no consumer mapping.

**Files:**
- Modify: `docs/superpowers/specs/ccdi/data-model.md:153-159` (after AppliedRule, before RegistrySeed)
- Modify: `docs/superpowers/specs/ccdi/integration.md:265` (dump_index_metadata response)
- Modify: `docs/superpowers/specs/ccdi/integration.md:275` (consumption description)

- [x] **Step 1: Add overlay file format section to data-model.md (SY-4)**

In data-model.md, after the Overlay Merge Semantics section (after line 159), add:

```markdown
### Overlay File Format

The overlay file (`topic_overlay.json`) is a JSON object with these root keys:

```json
{
  "overlay_version": "1",
  "overlay_schema_version": "1",
  "rules": [
    {
      "rule_id": "add-tool-inputs-alias",
      "operation": "remove_alias",
      "topic_key": "hooks.pre_tool_use",
      "alias_text": "tool inputs"
    },
    {
      "rule_id": "boost-pretooluse",
      "operation": "override_weight",
      "topic_key": "hooks.pre_tool_use",
      "alias_text": "tool inputs",
      "weight": 0.5
    },
    {
      "rule_id": "add-custom-topic",
      "operation": "add_topic",
      "topic_key": "hooks.user_prompt_submit",
      "topic_record": { "...": "full TopicRecord" }
    }
  ],
  "config_overrides": {
    "classifier.confidence_high_min_weight": 0.9
  }
}
```

| Root key | Type | Required | Purpose |
|----------|------|----------|---------|
| `overlay_version` | string | Yes | Instance version — monotonically incremented by curator on each edit |
| `overlay_schema_version` | string | Yes | Format version — validated against `build_inventory.py`'s supported range |
| `rules` | `OverlayRule[]` | Yes | Ordered list of overlay operations |
| `config_overrides` | `Record<string, scalar>` | No | See [Config Overrides in Overlay](#config-overrides-in-overlay) |

**OverlayRule fields by operation:**

| Operation | Required fields | Optional fields |
|-----------|----------------|-----------------|
| `add_topic` | `rule_id`, `operation`, `topic_key`, `topic_record` | — |
| `remove_alias` | `rule_id`, `operation`, `topic_key`, `alias_text` | — |
| `add_deny_rule` | `rule_id`, `operation`, `deny_rule` (DenyRule object) | — |
| `override_weight` | `rule_id`, `operation`, `topic_key`, `alias_text`, `weight` | — |
| `replace_aliases` | `rule_id`, `operation`, `topic_key`, `aliases` (Alias[]) | — |
| `replace_refs` | `rule_id`, `operation`, `topic_key`, `canonical_refs` (DocRef[]) | — |
| `replace_queries` | `rule_id`, `operation`, `topic_key`, `query_plan` (QueryPlan) | — |
| `override_config` | Expressed via `config_overrides` root key, not as a rule entry | — |

`override_config` is not expressed as an `OverlayRule`. It uses the separate `config_overrides` root key. `build_inventory.py` records each applied config override as an `AppliedRule` with `operation: "override_config"` — see [Config Overrides in Overlay](#config-overrides-in-overlay).
```

- [x] **Step 2: Define config_keys consumer mapping (SP-3)**

In integration.md, update the consumption description (around line 275) to add `config_keys`:

Change:
```
category names → family topics, headings → leaf topics, code literals → exact aliases, distinctive terms → phrase/token aliases.
```
To:
```
category names → family topics, headings → leaf topics, code literals → exact aliases, distinctive terms → phrase/token aliases, config_keys → exact aliases with `facet_hint: "config"`.
```

- [x] **Step 3: Add overlay format validation test to delivery.md**

In delivery.md Inventory Tests table (after line 247), add:

```
| Overlay format validation | Unknown root keys warned, missing `overlay_version` → non-zero exit |
| Overlay rule unknown operation | Rule with unrecognized `operation` → warning, rule skipped |
```

- [x] **Step 4: Commit**

```bash
git add docs/superpowers/specs/ccdi/data-model.md docs/superpowers/specs/ccdi/integration.md docs/superpowers/specs/ccdi/delivery.md
git commit -m "fix(ccdi): add overlay file format, define config_keys mapping (SY-4, SP-3)"
```

---

### Task 9: Add remaining test specifications [P1: VR-12, VR-13, VR-14, VR-18]

Four P1 verification gaps: boundary edge schema-evolution tests, durable-field alignment test, replay harness assertion capability, DenyRule penalty constraint tests.

**Files:**
- Modify: `docs/superpowers/specs/ccdi/delivery.md` (boundary contract tests, inventory tests, replay harness)

- [x] **Step 1: Add schema-evolution tests for boundary edges 1a-1c (VR-12)**

In delivery.md boundary contract tests table (around line 210), add rows:

```
| Inventory → classifier: schema evolution | Unknown TopicRecord field present → ignored (not crash); required Alias field missing → non-zero exit; `schema_version` mismatch at classifier load → warning |
| Inventory → registry: schema evolution | Unknown TopicRegistryEntry field in seed → ignored; required field missing → reinitialize empty (resilience principle) |
| Inventory → packet builder: schema evolution | Unknown QueryPlan facet → skipped; missing `default_facet` → fallback to `overview` |
```

- [x] **Step 2: Add durable-field alignment test (VR-13)**

In delivery.md boundary contract tests table, add:

```
| RegistrySeed ↔ TopicRegistryEntry durable fields | Every durable field in TopicRegistryEntry (all except attempt-local states `looked_up`, `built`) is present in RegistrySeed.entries field enumeration — schema-comparison test |
```

- [x] **Step 3: Extend replay harness assertion schema (VR-14)**

In delivery.md, after the fixture format example (around line 268), add:

```markdown
**Deep registry assertions:** In addition to `final_registry_state` (flat topic→state map), fixtures may include `final_registry_file_assertions` — an array of key-path assertions on the written registry JSON file:

```json
{
  "final_registry_file_assertions": [
    {"path": "hooks.pre_tool_use.coverage.pending_facets", "equals": []},
    {"path": "hooks.pre_tool_use.coverage.facets_injected", "contains": ["schema"]},
    {"path": "hooks.pre_tool_use.coverage.injected_chunk_ids", "length_gte": 1}
  ]
}
```

Supported operators: `equals` (deep equality), `contains` (array membership), `length_gte` (minimum array length), `is_null`, `not_null`.
```

- [x] **Step 4: Add DenyRule penalty constraint tests (VR-18)**

In delivery.md Inventory Tests table (after line 247), add:

```
| DenyRule drop + non-null penalty → warning | `action: "drop"`, `penalty: 0.35` → `build_inventory.py` emits warning, sets penalty to null |
| DenyRule downrank + null penalty → error | `action: "downrank"`, `penalty: null` → non-zero exit with "downrank requires non-null penalty" |
| DenyRule downrank + zero penalty → warning | `action: "downrank"`, `penalty: 0` → warning "zero penalty is a no-op" |
```

- [x] **Step 5: Commit**

```bash
git add docs/superpowers/specs/ccdi/delivery.md
git commit -m "fix(ccdi): add schema-evolution, durable-field, assertion, penalty tests (VR-12, VR-13, VR-14, VR-18)"
```

---

## Verification Checklist

After all tasks complete:

- [x] All cross-references still resolve (run anchor check on all 9 spec files)
- [x] spec.yaml boundary_rules has no duplicate `on_change_to` entries
- [x] README authority table matches spec.yaml authorities
- [x] Field Update Rules table covers all transitions referenced in scheduling rules
- [x] All delivery.md test entries reference defined spec concepts (no undefined terms)
- [x] candidates JSON schema matches ClassifierResult output fields
- [x] `--mark-injected` side-effects in integration.md match Field Update Rules in registry.md
