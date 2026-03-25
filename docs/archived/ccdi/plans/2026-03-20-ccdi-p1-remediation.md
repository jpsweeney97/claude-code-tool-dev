# CCDI Spec P1 Remediation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all 24 P1 findings from the CCDI spec review — underspecified state lifecycle, authority misplacements, missing operational definitions, and test coverage gaps.

**Architecture:** All changes are spec-level edits to markdown files in `docs/superpowers/specs/ccdi/`. No code changes. Tasks are ordered by dependency: registry schema → registry behavior → data model → CLI contracts → cross-references → tests.

**Tech Stack:** Markdown (spec files), YAML (spec.yaml)

**Source:** Review report at `.review-workspace/synthesis/report.md`. Raw findings at `.review-workspace/findings/`.

**Prerequisite:** P0 remediation plan (`docs/superpowers/plans/2026-03-20-ccdi-p0-remediation.md`) should be applied first — P0 Task 1 modifies `registry.md` Suppression Re-Entry which is adjacent to work here.

---

## File Map

| File | Tasks | Findings Addressed |
|------|-------|-------------------|
| `registry.md` | 1, 2, 3 | SY-3, SY-5, SY-7, SY-13, SY-16, SY-38, SY-41 |
| `data-model.md` | 4, 5 | SY-1, SY-4, SY-5 (part), SY-10, SY-19, SY-36 |
| `integration.md` | 6 | SY-3 (part), SY-8 (part), SY-14, SY-15 |
| `spec.yaml` | 7 | SY-37 |
| `decisions.md` | 7 | SY-17 |
| `data-model.md` | 7 | SY-8 (part) |
| `delivery.md` | 8 | SY-23, SY-24, SY-25, SY-26, SY-27, SY-28, SY-29 |

## Dependencies

```
Task 1 (schema extensions) ─┐
                             ├─→ Task 3 (scheduling rules)
Task 2 (field update rules) ─┘         │
                                       ├─→ Task 6 (CLI contracts)
Task 4 (data model fixes) ────────────┤
Task 5 (config_overrides) ────────────┤
                                       └─→ Task 7 (cross-refs)
                                                 │
                                                 └─→ Task 8 (test specs)
```

Tasks 1+2, 4, 5 can run in parallel (Phase 1). Tasks 3+6 after Phase 1. Task 7 after 3+6. Task 8 last.

---

### Task 1: Registry Entry Schema Extensions (SY-5, SY-13)

**Findings:** SY-5 (consecutive-turn counter missing), SY-13 (contradicts_prior has no operational definition)

**Files:**
- Modify: `docs/superpowers/specs/ccdi/registry.md:14-31`

- [ ] **Step 1: Add two new fields to TopicRegistryEntry schema**

In `registry.md`, replace the entry structure block (lines 14-31):

Old:
```
TopicRegistryEntry
├── topic_key: TopicKey
├── family_key: TopicKey
├── state: "detected" | "injected" | "suppressed" | "deferred"
├── first_seen_turn: number
├── last_seen_turn: number
├── last_injected_turn: number | null
├── last_query_fingerprint: string | null
├── suppression_reason: "weak_results" | "redundant" | null
├── deferred_reason: "cooldown" | "scout_priority" | "target_mismatch" | null
├── deferred_ttl: number | null       # turns remaining before re-evaluation
└── coverage
    ├── overview_injected: boolean
    ├── facets_injected: Facet[]
    ├── family_context_available: boolean
    └── injected_chunk_ids: string[]
```

New:
```
TopicRegistryEntry
├── topic_key: TopicKey
├── family_key: TopicKey
├── state: "detected" | "injected" | "suppressed" | "deferred"
├── first_seen_turn: number
├── last_seen_turn: number
├── last_injected_turn: number | null
├── last_query_fingerprint: string | null
├── consecutive_medium_count: number   # consecutive turns at medium confidence; reset on injection or confidence change
├── suppression_reason: "weak_results" | "redundant" | null
├── deferred_reason: "cooldown" | "scout_priority" | "target_mismatch" | null
├── deferred_ttl: number | null       # turns remaining before re-evaluation
└── coverage
    ├── overview_injected: boolean
    ├── facets_injected: Facet[]
    ├── pending_facets: Facet[]        # facets flagged for re-injection by contradicts_prior hint
    ├── family_context_available: boolean
    └── injected_chunk_ids: string[]
```

Two additions:
1. `consecutive_medium_count` — tracks consecutive turns at medium confidence for the mid-dialogue injection threshold
2. `coverage.pending_facets` — stores facets flagged for re-injection by `contradicts_prior` semantic hints

- [ ] **Step 2: Update RegistrySeed durable field enumeration in data-model.md**

In `data-model.md` line 169, the `RegistrySeed.entries` description enumerates durable fields by name. Update to include the new fields:

Old: `(...topic_key, family_key, state, first_seen_turn, last_seen_turn, last_injected_turn, last_query_fingerprint, suppression_reason, deferred_reason, deferred_ttl, coverage)`
New: `(...topic_key, family_key, state, first_seen_turn, last_seen_turn, last_injected_turn, last_query_fingerprint, consecutive_medium_count, suppression_reason, deferred_reason, deferred_ttl, coverage)`

Note: `pending_facets` lives inside `coverage` which is already listed as a whole — no separate enumeration needed.

- [ ] **Step 3: Verify schema consistency**

Confirm:
1. `consecutive_medium_count` is a durable field (it must persist across CLI invocations)
2. `pending_facets` sits in the `coverage` sub-object alongside `facets_injected` (semantically related)
3. The Durable vs Attempt-Local States table (lines 36-45) does not need updating — both new fields are durable
4. `data-model.md` RegistrySeed field list now includes `consecutive_medium_count`

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/ccdi/registry.md docs/superpowers/specs/ccdi/data-model.md
git commit -m "fix(ccdi): add consecutive_medium_count and pending_facets to TopicRegistryEntry

consecutive_medium_count: tracks consecutive turns at medium confidence
for mid-dialogue injection threshold (SY-5).
pending_facets: stores facets flagged for re-injection by
contradicts_prior semantic hints (SY-13).

Fixes: SY-5 (CE-3+CC-5), SY-13 (CE-2) — P1 (schema part)"
```

---

### Task 2: Registry Field Update Rules (SY-7, SY-38)

**Findings:** SY-7 (last_injected_turn, last_seen_turn, last_query_fingerprint have no update rules), SY-38 (injected_chunk_ids population at commit unspecified)

**Files:**
- Modify: `docs/superpowers/specs/ccdi/registry.md` — insert new section after State Transitions (after line 73, before `## TTL Lifecycle`)

- [ ] **Step 1: Add Field Update Rules section**

Insert after the State Transitions section (after the `**Forward-only for injected**` paragraph, before `### TTL Lifecycle`):

```markdown
### Field Update Rules

Fields updated at each state transition. Fields not listed are unchanged.

| Transition | Fields updated |
|-----------|----------------|
| `absent → detected` | `first_seen_turn` ← current turn, `last_seen_turn` ← current turn, `consecutive_medium_count` ← (1 if medium, else 0) |
| Re-detection (topic already in registry, any state) | `last_seen_turn` ← current turn |
| `[built] → injected` (via `--mark-injected`) | `state` ← `injected`, `last_injected_turn` ← current turn, `last_query_fingerprint` ← normalized fingerprint of query used, `coverage.injected_chunk_ids` ← append chunk IDs from built packet, `coverage.facets_injected` ← append facet, `consecutive_medium_count` ← 0 |
| `detected → deferred` (via `--mark-deferred`) | `state` ← `deferred`, `deferred_reason` ← reason, `deferred_ttl` ← `injection.deferred_ttl_turns` from config |
| `[looked_up] → suppressed` | `state` ← `suppressed`, `suppression_reason` ← reason |
| `suppressed → detected` (re-entry) | `state` ← `detected`, `suppression_reason` ← null, `last_seen_turn` ← current turn |
| `deferred → detected` (TTL expiry + reappearance) | `state` ← `detected`, `deferred_reason` ← null, `deferred_ttl` ← null, `last_seen_turn` ← current turn |

**`last_query_fingerprint` normalization:** Lowercased query string with whitespace collapsed. Includes `docs_epoch` if available — same key composition as the [session-local cache](#session-local-cache).
```

- [ ] **Step 2: Verify cross-references**

Confirm:
1. The `--mark-injected` row is consistent with `integration.md` build-packet command description
2. The `--mark-deferred` row is consistent with the deferred transitions table above
3. The `#session-local-cache` anchor exists in registry.md

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/ccdi/registry.md
git commit -m "fix(ccdi): add Field Update Rules section to registry.md

Define which fields are updated at each state transition, including
injected_chunk_ids population at commit and last_query_fingerprint
normalization. Resolves underspecified field-level update semantics.

Fixes: SY-7 (SP-4+5+6), SY-38 (SP-3) — P1"
```

---

### Task 3: Registry Scheduling Completeness (SY-3, SY-5 part, SY-13 part, SY-16, SY-41)

**Findings:** SY-3 (target_mismatch rule missing), SY-5 (consecutive-turn tracking rule missing), SY-13 (contradicts_prior scheduling behavior), SY-16 (hint facet resolution), SY-41 (null docs_epoch comparison)

**Files:**
- Modify: `docs/superpowers/specs/ccdi/registry.md:107-118` (Scheduling Rules)
- Modify: `docs/superpowers/specs/ccdi/registry.md:88-96` (Suppression Re-Entry — null docs_epoch)
- Modify: `docs/superpowers/specs/ccdi/registry.md:144-155` (Semantic Hints — facet resolution + contradicts_prior)

- [ ] **Step 1: Expand Scheduling Rules with target_mismatch and consecutive-turn tracking**

In `registry.md`, replace Scheduling Rules (lines 107-118):

Old:
```markdown
## Scheduling Rules

Each turn, after the [classifier](classifier.md) runs on Codex's latest response:

1. **Diff** new resolved topics against registry.
2. **Materially new** = one of:
   - New leaf under an already-covered family
   - Agent provides a `semantic_hint` (see [below](#semantic-hints)) referencing a claim that touches a detected topic
   - Codex contradicts or extends an injected topic (coverage gap)
3. **Cooldown:** Max one new docs topic injection per turn (configurable via [`ccdi_config.json`](data-model.md#configuration-ccdi_configjson) → `injection.cooldown_max_new_topics_per_turn`).
4. **Scout priority:** If context-injection has a scout candidate targeting the same code boundary, defer the CCDI candidate (→ `deferred` state with `scout_priority` reason).
5. **Schedule** highest-priority materially new topic for lookup.
```

New:
```markdown
## Scheduling Rules

Each turn, after the [classifier](classifier.md) runs on Codex's latest response:

1. **Diff** new resolved topics against registry.
2. **Materially new** = one of:
   - New leaf under an already-covered family
   - Agent provides a `semantic_hint` (see [below](#semantic-hints)) referencing a claim that touches a detected topic
   - Codex contradicts or extends an injected topic (coverage gap)
3. **Consecutive-turn medium tracking:** For each `detected` topic at medium confidence, increment `consecutive_medium_count`. Reset to 0 if the topic is absent from classifier output or appears at a different confidence level. Injection fires when `consecutive_medium_count` reaches `injection.mid_turn_consecutive_medium_turns` (default: 2). Reset to 0 after injection fires.
4. **Cooldown:** Max one new docs topic injection per turn (configurable via [`ccdi_config.json`](data-model.md#configuration-ccdi_configjson) → `injection.cooldown_max_new_topics_per_turn`).
5. **Scout priority:** If context-injection has a scout candidate targeting the same code boundary, defer the CCDI candidate (→ `deferred` state with `scout_priority` reason).
6. **Target-match check:** After building a packet for a scheduled candidate, verify the packet supports the composed follow-up target. If not target-relevant, defer the topic (→ `deferred` state with `target_mismatch` reason via `--mark-deferred`). The definition of "composed follow-up target" and the CLI invocation are specified in [integration.md#mid-dialogue-phase-per-turn-in-codex-dialogue](integration.md#mid-dialogue-phase-per-turn-in-codex-dialogue).
7. **Schedule** highest-priority materially new topic for lookup.
```

Two additions: step 3 (consecutive-turn tracking with `consecutive_medium_count` from Task 1) and step 6 (target-match check with cross-reference to integration.md).

- [ ] **Step 2: Add null docs_epoch comparison semantics to Suppression Re-Entry**

In `registry.md`, after the Suppression Re-Entry table (after line 95, before `## Family vs Leaf Coverage`), add:

```markdown

**`docs_epoch` comparison semantics:** `null == null` is not a change (no re-entry). `null → non-null` is a change (re-entry fires). `non-null → null` is a change (re-entry fires). Comparison is string equality on non-null values.
```

- [ ] **Step 3: Add facet resolution rule and contradicts_prior operational definition to Semantic Hints**

In `registry.md`, after the Semantic Hints scheduling effects table (after line 155, before `## Session-Local Cache`), add:

```markdown

**Hint facet resolution:** When a semantic hint elevates a topic, the CLI classifies `claim_excerpt` through the standard two-stage pipeline to resolve both the topic key and the facet hint from matched aliases. The resolved facet from `claim_excerpt` classification is used as the candidate facet, overriding any facet from prior detection.

**`contradicts_prior` on `injected` — operational definition:** When a `contradicts_prior` hint resolves to an `injected` topic, the CLI appends the resolved facet to `coverage.pending_facets` (the field added in the entry structure). The topic's `state` does not change — it remains `injected`. On subsequent scheduling passes, the scheduler checks `pending_facets` and schedules a lookup at the first pending facet not already in `facets_injected`. After successful injection at the pending facet, remove it from `pending_facets`.
```

- [ ] **Step 4: Verify consistency**

Confirm:
1. Step 3 in scheduling rules references `consecutive_medium_count` (added in Task 1)
2. Step 6 references `integration.md#mid-dialogue-phase-per-turn-in-codex-dialogue` (anchor exists)
3. Hint facet resolution paragraph is consistent with the Semantic Hints scheduling effects table
4. `pending_facets` field was added in Task 1
5. Null docs_epoch semantics are consistent with the `weak_results` re-entry trigger

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/ccdi/registry.md
git commit -m "fix(ccdi): complete registry scheduling rules and semantic hint definitions

Add consecutive-turn medium tracking (step 3), target-match check
(step 6), null docs_epoch comparison semantics, hint facet resolution
rule, and contradicts_prior operational definition.

Fixes: SY-3 (AA-3+CE-9), SY-5 part, SY-13 part, SY-16 (CE-7), SY-41 (SP-11) — P1"
```

---

### Task 4: Data Model Cleanup (SY-1, SY-10, SY-19, SY-36)

**Findings:** SY-1 (broken #entry-structure link), SY-10 (precedence ruling outside authority), SY-19 (overlay_version undefined), SY-36 (DenyRule.penalty on drop)

**Files:**
- Modify: `docs/superpowers/specs/ccdi/data-model.md:21, 25-34, 77-83, 169, 228`

- [ ] **Step 1: Fix broken #entry-structure link (SY-1)**

In `data-model.md` line 169, replace:

Old: `(see [above](#entry-structure))`
New: `(see [registry.md#entry-structure](registry.md#entry-structure))`

- [ ] **Step 2: Remove precedence ruling from Authority scope paragraph (SY-10)**

In `data-model.md`, replace lines 228:

Old:
```markdown
**Authority scope:** This section is normative for the config file's **schema** (field names, types, default values) under the `persistence_schema` claim. The **behavioral meaning** of each parameter is authoritative in its consumer file (classifier-contract, registry-contract, or packet-contract). If a consumer file's description of a parameter's behavioral effect conflicts with the default value here, the consumer file's behavioral contract takes precedence per `claim_precedence` for `behavior_contract`.
```

New:
```markdown
**Authority scope:** This section is normative for the config file's **schema** (field names, types, default values) under the `persistence_schema` claim. The **behavioral meaning** of each parameter is authoritative in its consumer file (classifier-contract, registry-contract, or packet-contract). For precedence between config schema and behavioral contracts, see `spec.yaml` → `claim_precedence`.
```

The last sentence now defers to spec.yaml rather than making its own precedence ruling.

- [ ] **Step 3: Define overlay_version (SY-19)**

In `data-model.md`, add a row to the Version Axes table (after line 33):

```markdown
| Overlay instance | `overlay_meta.overlay_version` | Which version of the curated overlay file was applied | Manual edit (human) |
```

And add a note after the table:

```markdown

`overlay_version` is an **instance version** (which edit of the overlay file), not a **compatibility axis** (whether the overlay format is readable). It is monotonically incremented by the overlay curator on each manual edit. `build_inventory.py` records it in `overlay_meta` for traceability but does not validate compatibility — that is the job of `overlay_schema_version`.
```

- [ ] **Step 4: Clarify DenyRule.penalty conditionality (SY-36)**

In `data-model.md`, replace the `penalty` row in the DenyRule table (line 82):

Old:
```markdown
| `penalty` | number | Weight reduction for downrank |
```

New:
```markdown
| `penalty` | number \| null | Weight reduction for `downrank`; null or omit for `drop` (penalty is not applied when action is `drop`) |
```

Update the denylist example (line 137) to use `null` for the drop rule:

Old: `{"id": "drop-overview", "pattern": "overview", "match_type": "token", "action": "drop", "penalty": 1.0, "reason": "too generic"}`
New: `{"id": "drop-overview", "pattern": "overview", "match_type": "token", "action": "drop", "penalty": null, "reason": "too generic"}`

- [ ] **Step 5: Verify consistency**

Confirm:
1. `#entry-structure` link now resolves to registry.md (heading exists at registry.md line 12)
2. Authority scope paragraph no longer makes a precedence ruling
3. Version Axes table now has 4 rows (3 compatibility + 1 instance) — the count "Three independent version axes" in the heading should update to "Four version axes" or add a note distinguishing axes from instance versions
4. DenyRule example is consistent with updated schema
5. Penalty application paragraph (line 85) already says "downrank reduces" — consistent with null-for-drop

- [ ] **Step 6: Update Version Axes heading**

Step 3 added a 4th row, so the heading count is now wrong. Replace:

Old: `Three independent version axes prevent coupled evolution:`
New: `Four version axes prevent coupled evolution (three compatibility axes + one instance version):`

- [ ] **Step 7: Commit**

```bash
git add docs/superpowers/specs/ccdi/data-model.md
git commit -m "fix(ccdi): fix broken link, remove precedence ruling, define overlay_version, clarify DenyRule.penalty

- Fix #entry-structure → registry.md#entry-structure (SY-1)
- Defer precedence ruling to spec.yaml (SY-10)
- Define overlay_version as instance version (SY-19)
- Make penalty null for drop action (SY-36)

Fixes: SY-1 (AA-4+CC-1+SP-14), SY-10 (AA-1), SY-19 (CC-4), SY-36 (SP-1) — P1"
```

---

### Task 5: Config Overrides Schema (SY-4, SY-5 part)

**Findings:** SY-4 (config_overrides schema undefined), SY-5 part (Config consumers table needs registry.md for consecutive-turn)

**Files:**
- Modify: `docs/superpowers/specs/ccdi/data-model.md:219-226`

- [ ] **Step 1: Replace vague config_overrides reference with defined schema**

In `data-model.md`, replace lines 219-226:

Old:
```markdown
The overlay can override config values via an optional `config_overrides` section — same merge semantics as topic overrides.

**Config consumers:** Parameters are referenced by:
- [classifier.md](classifier.md#confidence-levels) — `classifier.*` keys (confidence thresholds) and `injection.*` keys (injection thresholds)
- [registry.md](registry.md#scheduling-rules) — `injection.cooldown_max_new_topics_per_turn` and `injection.deferred_ttl_turns`
- [packets.md](packets.md#token-budgets) — `packets.*` keys (token budgets, quality thresholds)

Changes to config keys require checking all consumer files.
```

New:
```markdown
### Config Overrides in Overlay

The overlay file may include an optional `config_overrides` object that overrides default values in `ccdi_config.json`. Merge semantics: **scalar replace only** (config values are flat scalars, not arrays or nested objects). Unknown keys are warned and skipped.

```json
{
  "config_overrides": {
    "classifier.confidence_high_min_weight": 0.9,
    "packets.initial_max_topics": 2
  }
}
```

Keys use dot-separated paths matching the config schema above (e.g., `classifier.confidence_high_min_weight`). Only keys defined in the `ccdi_config.json` schema are valid override targets.

`build_inventory.py` records each applied config override in `overlay_meta.applied_rules[]` with `operation: "override_config"` and `target` set to the config key path.

**Config consumers:** Parameters are referenced by:
- [classifier.md](classifier.md#confidence-levels) — `classifier.*` keys (confidence thresholds) and `injection.*` keys (injection thresholds)
- [registry.md](registry.md#scheduling-rules) — `injection.cooldown_max_new_topics_per_turn`, `injection.deferred_ttl_turns`, and `injection.mid_turn_consecutive_medium_turns`
- [packets.md](packets.md#token-budgets) — `packets.*` keys (token budgets, quality thresholds)

Changes to config keys require checking all consumer files.
```

Two changes: (1) defined `config_overrides` schema with JSON example and merge semantics, (2) added `injection.mid_turn_consecutive_medium_turns` to registry.md consumer entry (SY-5 part).

- [ ] **Step 2: Verify consistency**

Confirm:
1. The `override_config` operation value will need to be added to `AppliedRule.operation` enum — this is P2 finding SY-39, not in this plan's scope. Note it for the P2 plan.
2. `registry.md#scheduling-rules` anchor exists
3. Config override merge semantics ("scalar replace only") is appropriate — config has no arrays
4. The JSON example uses valid config key paths from the schema above

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/ccdi/data-model.md
git commit -m "fix(ccdi): define config_overrides schema and update config consumers

Add config_overrides overlay schema with scalar-replace merge semantics,
JSON example, and validation behavior. Add mid_turn_consecutive_medium_turns
to registry.md consumer entry.

Fixes: SY-4 (SP-8+CE-11), SY-5 part — P1"
```

---

### Task 6: CLI Interface Contracts (SY-14, SY-15)

**Findings:** SY-14 (--mark-deferred requires redundant rebuild), SY-15 (automatic suppression pre-empts --mark-deferred)

**Files:**
- Modify: `docs/superpowers/specs/ccdi/integration.md:16-25, 177-202`

- [ ] **Step 1: Add --skip-build flag to build-packet command**

In `integration.md`, update the `build-packet` command in the CLI table (line 18):

Old:
```markdown
| `build-packet --results-file <path> [--registry-file <path>] --mode initial\|mid_turn [--mark-injected] [--mark-deferred <topic_key> --deferred-reason <reason>] [--config <path>]` | Search results + optional registry | Rendered markdown (stdout); registry updated in-place if `--mark-injected` or `--mark-deferred` | Both modes |
```

New:
```markdown
| `build-packet --results-file <path> [--registry-file <path>] --mode initial\|mid_turn [--mark-injected] [--mark-deferred <topic_key> --deferred-reason <reason>] [--skip-build] [--config <path>]` | Search results + optional registry | Rendered markdown (stdout); registry updated in-place if `--mark-injected` or `--mark-deferred` | Both modes |
```

- [ ] **Step 2: Document --skip-build behavior**

After the `--registry-file optionality` paragraph (line 22), add:

```markdown

**`--skip-build` flag:** When passed with `--mark-deferred`, skips packet construction and only writes deferred state to the registry. This avoids redundant rebuilds when the target-match check already determined the packet is not target-relevant. `--skip-build` is only valid with `--mark-deferred`; ignored otherwise.
```

- [ ] **Step 3: Specify suppression/deferred interaction**

After the `build-packet automatic suppression` paragraph (line 25), add:

```markdown

**Suppression and deferral precedence:** If `build-packet` returns empty output (below quality threshold), automatic suppression writes `suppressed: weak_results` to the registry. In this case, the target-match check has no packet to evaluate — skip the `--mark-deferred` path entirely. The topic is already handled by suppression. The mid-dialogue flow should check for empty output before proceeding to target-match.
```

- [ ] **Step 4: Update mid-dialogue flow to reflect both fixes**

In `integration.md`, update the mid-dialogue flow comment at lines 184-189:

Old:
```markdown
│   │   ├─ Target-match check: verify staged packet supports the composed follow-up target
│   │   ├─ If target-relevant: stage for prepending
│   │   └─ If not target-relevant:
│   │       └─ Bash: python3 topic_inventory.py build-packet \
│   │                --results-file /tmp/ccdi_results_<id>.json \
│   │                --registry-file /tmp/ccdi_registry_<id>.json \
│   │                --mode mid_turn \
│   │                --mark-deferred <topic_key> --deferred-reason target_mismatch
```

New:
```markdown
│   │   ├─ If build-packet returned empty: no packet to stage (automatic suppression already fired); skip target-match
│   │   ├─ Target-match check: verify staged packet supports the composed follow-up target
│   │   ├─ If target-relevant: stage for prepending
│   │   └─ If not target-relevant:
│   │       └─ Bash: python3 topic_inventory.py build-packet \
│   │                --results-file /tmp/ccdi_results_<id>.json \
│   │                --registry-file /tmp/ccdi_registry_<id>.json \
│   │                --mode mid_turn \
│   │                --mark-deferred <topic_key> --deferred-reason target_mismatch \
│   │                --skip-build
```

- [ ] **Step 5: Verify consistency**

Confirm:
1. `--skip-build` is only used with `--mark-deferred` in the flow
2. Automatic suppression fires before target-match check (order is correct)
3. The build-packet command table includes the new flag

- [ ] **Step 6: Commit**

```bash
git add docs/superpowers/specs/ccdi/integration.md
git commit -m "fix(ccdi): add --skip-build flag and specify suppression/deferred precedence

Add --skip-build to avoid redundant rebuild on --mark-deferred.
Specify that automatic suppression pre-empts target-match check
when build-packet returns empty.

Fixes: SY-14 (CE-4), SY-15 (CE-6) — P1"
```

---

### Task 7: Cross-Reference, Lifecycle & Coherence (SY-3 part, SY-8, SY-17, SY-37)

**Findings:** SY-3 (integration.md cross-reference), SY-8 (seed lifecycle), SY-17 (decisions.md terminology), SY-37 (boundary rule)

**Files:**
- Modify: `docs/superpowers/specs/ccdi/integration.md:42`
- Modify: `docs/superpowers/specs/ccdi/integration.md:139-157`
- Modify: `docs/superpowers/specs/ccdi/data-model.md:169-172`
- Modify: `docs/superpowers/specs/ccdi/decisions.md:35`
- Modify: `docs/superpowers/specs/ccdi/spec.yaml:60-67`

- [ ] **Step 1: Demote --source behavioral claim in integration.md (SY-3 part)**

In `integration.md`, replace line 42:

Old:
```markdown
**`--source codex|user` on `dialogue-turn`:** `codex` = classifier runs on Codex's response text; `user` = classifier runs on the user's turn text. Both sources use the same two-stage pipeline. Behavioral divergence in scheduling (if any) is deferred to implementation — currently treated identically.
```

New:
```markdown
**`--source codex|user` on `dialogue-turn`:** `codex` = classifier runs on Codex's response text; `user` = classifier runs on the user's turn text. Both sources use the same two-stage pipeline. Scheduling behavior by source is defined in [registry.md#scheduling-rules](registry.md#scheduling-rules); see [delivery.md#known-open-items](delivery.md#known-open-items) for deferred divergence.
```

- [ ] **Step 2: Add seed lifecycle in-place mutation note (SY-8)**

In `integration.md`, after the Registry Seed Handoff paragraph ending "The consultation contract §6 does not need modification..." (line 156), add:

```markdown

**Seed file identity invariant:** The registry seed file written by `/dialogue` at `/tmp/ccdi_registry_<id>.json` is the same file path passed to the commit-phase `build-packet --mark-injected` call. The commit mutates the seed file in-place. By the time `codex-dialogue` receives `ccdi_seed` and begins its mid-dialogue loop, the registry file reflects post-commit state (`injected` entries). The seed is not a separate read-only artifact — it is the live registry file from dialogue start.
```

In `data-model.md`, after line 171 ("Before the commit, entries are in `detected` state."), add:

```markdown

**In-place mutation:** The `/dialogue` skill writes the seed to a temp file, which is then updated in-place by the commit-phase `build-packet --mark-injected` call at the same path. After commit, entries at that path reflect `injected` state. See [integration.md#registry-seed-handoff](integration.md#registry-seed-handoff) for the full lifecycle.
```

- [ ] **Step 3: Fix decisions.md terminology (SY-17)**

In `decisions.md`, replace line 35:

Old:
```markdown
| Briefing-carried ccdi_seed + opaque checkpoint for registry handoff | Convergence | High |
```

New:
```markdown
| ccdi_seed delegation-envelope field (file path) with sentinel-wrapped registry seed for handoff | Convergence | High |
```

- [ ] **Step 4: Add boundary rule to spec.yaml (SY-37)**

In `spec.yaml`, after the last boundary rule (after line 67), add:

```yaml
  - on_change_to: [registry-contract]
    review_authorities: [data-model]
    reason: TopicRegistryEntry field changes affect RegistrySeed.entries durable-field subset in data-model.md.
```

- [ ] **Step 5: Verify consistency**

Confirm:
1. `registry.md#scheduling-rules` anchor exists (yes — scheduling rules section)
2. `delivery.md#known-open-items` anchor exists (yes — Known Open Items section)
3. `integration.md#registry-seed-handoff` anchor exists (yes — Registry Seed Handoff)
4. The new boundary rule uses authorities defined in spec.yaml (`registry-contract`, `data-model`)
5. decisions.md terminology matches integration.md's resolved mechanism

- [ ] **Step 6: Commit**

```bash
git add docs/superpowers/specs/ccdi/integration.md docs/superpowers/specs/ccdi/data-model.md docs/superpowers/specs/ccdi/decisions.md docs/superpowers/specs/ccdi/spec.yaml
git commit -m "fix(ccdi): fix cross-refs, add seed lifecycle invariant, fix terminology, add boundary rule

- Demote --source behavioral claim to cross-reference (SY-3 part)
- Add seed file in-place mutation invariant (SY-8)
- Fix 'Briefing-carried' terminology in decisions.md (SY-17)
- Add registry-contract → data-model boundary rule (SY-37)

Fixes: SY-3 part, SY-8 (SP-7+CE-8), SY-17 (CC-2), SY-37 (SP-2) — P1"
```

---

### Task 8: Test Specifications (SY-23, SY-24, SY-25, SY-26, SY-27, SY-28, SY-29)

**Findings:** All 7 verification-regression P1 findings — missing or underspecified test entries in delivery.md.

**Files:**
- Modify: `docs/superpowers/specs/ccdi/delivery.md:145, 156, 184-189, 233-265`

- [ ] **Step 1: Strengthen TTL reset test (SY-24)**

In `delivery.md`, replace Registry Tests line 145:

Old:
```markdown
| Deferred TTL expiry without reappearance | TTL=0 but topic absent from classifier → TTL reset, stays `deferred` |
```

New:
```markdown
| Deferred TTL expiry without reappearance | TTL=0 but topic absent from classifier → TTL resets to `ccdi_config.injection.deferred_ttl_turns` (not hardcoded), stays `deferred`; verify with non-default config value (e.g., `deferred_ttl_turns=5`) |
```

- [ ] **Step 2: Strengthen auto-suppression test (SY-27)**

In `delivery.md`, replace CLI Integration Tests entry (line ~184):

Old:
```markdown
| `build-packet` empty output writes suppressed | Empty result + registry → `suppressed: weak_results` in registry |
```

New:
```markdown
| `build-packet` empty output writes suppressed automatically | Empty result + `--registry-file` present (NO explicit suppression flag) → `suppressed: weak_results` in registry; verify flag absence is the test condition |
```

- [ ] **Step 3: Add ccdi_debug gating test (SY-25)**

In `delivery.md`, add to CLI Integration Tests table:

```markdown
| `ccdi_debug` gating of trace emission | With `ccdi_debug=true` in delegation envelope → `ccdi_trace` key present in agent output; with `ccdi_debug` absent → no `ccdi_trace` key |
```

- [ ] **Step 4: Add ccdi_seed absent test (SY-28)**

In `delivery.md`, add to Integration Tests table:

```markdown
| Mid-dialogue CCDI disabled without ccdi_seed | Delegation envelope without `ccdi_seed` field → `codex-dialogue` agent does not invoke `dialogue-turn` or `build-packet` during turn loop; diagnostics show `phase: initial_only` |
```

- [ ] **Step 5: Add hint×state replay fixtures (SY-23)**

In `delivery.md`, add 4 entries to the Required fixture scenarios table (after line ~265):

```markdown
| `hint_no_effect_already_injected.replay.json` | Prescriptive hint on already-injected topic → no additional injection, no state change |
| `hint_coverage_gap.replay.json` | `contradicts_prior` hint on injected topic → facet added to `pending_facets`, scheduled for re-injection at new facet |
| `hint_re_enters_suppressed.replay.json` | `extends_topic` hint on suppressed topic → re-enters as `detected`, scheduled for lookup |
| `hint_facet_expansion.replay.json` | `extends_topic` hint on injected topic → facet expansion lookup at a facet not yet in `facets_injected` |
```

- [ ] **Step 6: Specify replay harness execution model (SY-29)**

In `delivery.md`, after the Replay Harness runner line (line 254), add:

```markdown

**Execution model:** The replay harness operates in **static validation mode** — it validates pre-recorded traces against assertion schemas without re-running the agent. Each fixture's `trace` array is the input (a recorded sequence of CCDI decisions per turn); `assertions` is the expected outcome. The harness:

1. Replays the trace entries in order, feeding each turn's `classifier_result` and `semantic_hints` into the CLI commands (`classify`, `dialogue-turn`, `build-packet`) via subprocess calls with fixture data as input files.
2. Compares CLI stdout (candidates, registry state) against the fixture's `assertions`.
3. Does NOT invoke `codex-reply` or `search_docs` — these are stubbed: `search_docs` returns canned results from a `search_results` field in the fixture; `codex-reply` is assumed successful unless the fixture explicitly sets `codex_reply_error: true`.

This model tests the deterministic CLI pipeline end-to-end without requiring a live Codex connection or LLM invocation.
```

- [ ] **Step 7: Specify shadow mode labeling process (SY-26)**

In `delivery.md`, after the shadow mode diagnostics additional fields paragraph (after line ~64), add:

```markdown

**False-positive labeling protocol:** During shadow evaluation, label a minimum of 100 detected topics across 10+ dialogues. For each topic in `topics_detected`, a labeler checks whether the input text genuinely discusses a Claude Code extension concept. Topics where the input text uses extension terminology in a non-Claude-Code context (e.g., "React hook", "webpack plugin") are false positives. `false_positive_rate` = `false_positive_topic_detections / len(topics_detected)`. The 10% kill threshold requires statistical confidence: label at least 100 topics before evaluating.
```

- [ ] **Step 8: Verify consistency**

Confirm:
1. All new replay fixtures reference states/transitions defined in registry.md (post-Task 3)
2. TTL reset test references `ccdi_config.injection.deferred_ttl_turns` (config key exists in data-model.md)
3. Replay harness execution model is consistent with fixture format (trace + assertions)
4. Shadow mode labeling references the 10% threshold from kill criteria table
5. All new test entries use consistent table formatting

- [ ] **Step 9: Commit**

```bash
git add docs/superpowers/specs/ccdi/delivery.md
git commit -m "fix(ccdi): add missing test specs, replay model, and labeling protocol

- Strengthen TTL reset and auto-suppression tests (SY-24, SY-27)
- Add ccdi_debug gating and ccdi_seed absent tests (SY-25, SY-28)
- Add 4 hint×state replay fixtures (SY-23)
- Specify replay harness static validation model (SY-29)
- Add false-positive labeling protocol for shadow mode (SY-26)

Fixes: SY-23..SY-29 (VR-4..VR-10) — P1"
```

---

## Pre-Execution Checklist

- [ ] P0 remediation plan applied first (especially Task 1 — registry.md suppression re-entry)
- [ ] Create feature branch: `git checkout -b fix/ccdi-p1-remediation`
- [ ] Phase 1 (parallel): Tasks 1, 2, 4, 5
- [ ] Phase 2 (after Phase 1): Tasks 3, 6
- [ ] Phase 3 (after Phase 2): Task 7
- [ ] Phase 4 (after Phase 3): Task 8
- [ ] Final: re-read all 7 modified files + spec.yaml to verify no introduced inconsistencies
- [ ] Cross-reference check: verify all new `[anchor](file#anchor)` links resolve
