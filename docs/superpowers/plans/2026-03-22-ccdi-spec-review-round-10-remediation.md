# CCDI Spec Review Round 10 — Remediation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate all 48 findings (1 P0, 26 P1, 21 P2) from CCDI spec review round 10, plus 2 emerged items from Codex design consultation.

**Architecture:** Eight file-focused editing passes across 7 spec files (delivery.md splits into P1 and P2 commits). Each task applies all findings for its target file in a single pass. Design decisions from Codex dialogue `019d1826-13a6-7f50-8c61-1d587877fbf3` inform 5 behavioral fixes (CE-2, CE-8, CC-4, SP-5, SP-8).

**Tech Stack:** Markdown editing only — no code changes. All files in `docs/superpowers/specs/ccdi/`.

---

## Source Materials

| Resource | Path |
|----------|------|
| Synthesis report | `.review-workspace/synthesis/report.md` |
| Synthesis ledger | `.review-workspace/synthesis/ledger.md` |
| Per-reviewer findings | `.review-workspace/findings/*.md` |
| Spec files | `docs/superpowers/specs/ccdi/` |

## Design Decisions (Codex Dialogue)

| ID | Finding | Decision | Confidence |
|----|---------|----------|------------|
| D1 | CE-8 | Phase A always active. Graduation gate scoped to Phase B mid-dialogue only. | High |
| D2 | CC-4 | `skip_scout` gets `shadow_suppressed: true` in shadow mode. No `shadow_defer_intent`. | High |
| D3 | CE-2 | Auto-suppression pre-empts `--mark-injected`. Three explicit postconditions. | High |
| D4 | SP-5 | Add `remove_alias`, `replace_refs`, `replace_queries` to `AppliedRule.target` as `TopicKey`. | High |
| D5 | SP-8 | No load-time recovery for `pending_facets`. Preserve serialized order. | High |

## File Map

| File | P0 | P1 | P2 | Emerged | Total |
|------|----|----|----|---------| ------|
| `delivery.md` | 1 | 8 | 6 | 1 | 16 |
| `integration.md` | — | 6 | 2 | — | 8 |
| `data-model.md` | — | 6 | 6 | — | 12 |
| `registry.md` | — | 4 | 1 | — | 5 |
| `spec.yaml` | — | 2 | 3 | — | 5 |
| `decisions.md` | — | — | 1 | 1 | 2 |
| `README.md` | — | — | 2 | — | 2 |
| **Total** | **1** | **26** | **21** | **2** | **50** |

---

### Task 0: Fix P0 — `delivery.md` Field Name Conflict

**Files:**
- Modify: `delivery.md:189`

**Finding:** SY-2 (P0) — `graduation.json` latency field name conflict blocks validator implementation.

The test case at line 189 uses `p95_prepare_latency_ms`, a field that exists nowhere else in the spec. The graduation.json schema (line 152), kill criteria table (line 30), and aggregation definition (lines 155-157) all use `avg_latency_ms`.

- [ ] **Step 1: Fix field name at line 189**

Change `p95_prepare_latency_ms: 600` to `avg_latency_ms: 600` in the test case table row.

Old (line 189):
```
| Approved status with latency above threshold | `graduation.json` with `status: "approved"`, `p95_prepare_latency_ms: 600` (above 500ms threshold) | Exit 1, error reports latency above threshold |
```

New:
```
| Approved status with latency above threshold | `graduation.json` with `status: "approved"`, `avg_latency_ms: 600` (above 500ms threshold) | Exit 1, error reports latency above threshold |
```

- [ ] **Step 2: Verify consistency**

Grep for `p95_prepare_latency_ms` across all spec files — should return zero matches.
Grep for `avg_latency_ms` — should match lines 30, 99, 152, 155-157, and 189.

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/ccdi/delivery.md
git commit -m "fix(spec): fix P0 graduation.json latency field name (SY-2)

Change p95_prepare_latency_ms to avg_latency_ms at delivery.md:189 to match
the graduation.json schema, kill criteria table, and aggregation definition."
```

---

### Task 1: `spec.yaml` — Authority Model Fixes (2 P1, 3 P2)

**Files:**
- Modify: `spec.yaml:29-31` (AA-1), `spec.yaml:76-77` (AA-3), `spec.yaml:47-49` (AA-6), `spec.yaml:65` (AA-7), `spec.yaml:28-32` (AA-2)

#### P1 Fixes

- [ ] **Step 1: AA-1 — Fix elevated_sections anchor mismatch** (line 29)

The spec.yaml registers `section: "pipeline-isolation-invariants"` but the integration.md heading `### Pipeline Isolation Invariants (subset)` produces anchor `#pipeline-isolation-invariants-subset`.

Change `spec.yaml:29`:
```yaml
      - section: "pipeline-isolation-invariants-subset"
```

- [ ] **Step 2: AA-3 — Add `integration` to boundary rule 1** (line 76-77)

Boundary rule 1 (`on_change_to: [data-model]`) omits `integration` from `review_authorities`. Changes to the RegistrySeed envelope or `dump_index_metadata` schema in data-model.md would bypass integration review.

Change `spec.yaml:77`:
```yaml
    review_authorities: [classifier-contract, registry-contract, packet-contract, integration]
```

Update the `reason` field to note the addition:
```yaml
    reason: Schema changes to inventory, aliases, config, or RegistrySeed durable-field subset affect all downstream consumers. Integration is included because RegistrySeed envelope and dump_index_metadata schema changes affect CLI interface contracts.
```

#### P2 Fixes

- [ ] **Step 3: AA-6 — Clarify claim_precedence comment** (lines 47-61)

The comment at lines 51-56 could mislead readers into thinking `decisions` appears in chains because it holds those claims. Revise the comment to be clearer:

Replace lines 51-56 with:
```yaml
  # NOTE: Authorities appear in chains for claims they don't hold in
  # default_claims. Presence means "consulted for resolution," not "claims
  # this type." For example:
  # - `decisions` appears last in most chains as a fallback of last resort.
  #   Exception: decision_record chain, where decisions is first (it owns
  #   that claim).
  # - `integration` ranks first for interface_contract because it defines
  #   the external CLI interface consumed by agents.
```

- [ ] **Step 4: AA-7 — Add rationale for `integration` in persistence_schema chain** (line 65)

The `persistence_schema` chain includes `integration` without explaining why. Add inline comment:

Change `spec.yaml:65`:
```yaml
    persistence_schema: [data-model, integration, decisions]  # integration included: RegistrySeed envelope and dump_index_metadata schema surface persistence concerns at the CLI interface
```

- [ ] **Step 5: AA-2 — Document elevated_sections redundancy rationale** (lines 28-32)

Add a clarifying comment after the `elevated_sections` block:

After line 31, add:
```yaml
        # NOTE: This elevation is redundant with the claim_precedence chain for
        # behavior_contract (integration already ranks above decisions there).
        # Retained for explicitness: these invariants are cross-referenced from
        # decisions.md and the elevation makes the authority relationship visible
        # at the registration site rather than requiring chain traversal.
```

- [ ] **Step 6: Verify and commit**

Verify `spec.yaml` is valid YAML: `python3 -c "import yaml; yaml.safe_load(open('docs/superpowers/specs/ccdi/spec.yaml'))"`

```bash
git add docs/superpowers/specs/ccdi/spec.yaml
git commit -m "fix(spec): remediate 5 spec.yaml findings from review round 10

AA-1: Fix elevated_sections anchor to match integration.md heading
AA-3: Add integration to boundary rule 1 review_authorities
AA-6: Clarify claim_precedence comment to avoid misleading interpretation
AA-7: Add rationale for integration in persistence_schema chain
AA-2: Document elevated_sections redundancy rationale"
```

---

### Task 2: `integration.md` — Behavioral Spec Fixes (6 P1, 2 P2)

**Files:**
- Modify: `integration.md:246-249` (CE-2), `integration.md:246+` (CE-8), `integration.md:278-283` (CE-9), `integration.md:290` (CC-4), `integration.md:305-309` (CC-3, CC-4), `integration.md:317` (CC-4), `integration.md:365-385` (SY-3), `integration.md:424` (SY-3), `integration.md:106` (CC-7), `integration.md` flag name (CE-4)

#### P1 Fixes

- [ ] **Step 1: CE-2 + CE-8 — Replace initial commit partial-commit language with three postconditions** (lines 246-249)

Per design decisions D1 and D3. Replace lines 246-249:

Old:
```
│  │       If a per-topic build-packet --mark-injected exits non-zero, log the error
│  │       and continue with remaining entries — partial commit is acceptable
│  │       (uncommitted topics remain `detected` and are candidates for re-injection
│  │       in mid-dialogue turns)
```

New:
```
│  │       Per-topic postconditions (three outcomes):
│  │       1. Exit non-zero: log error, continue with remaining entries — topic
│  │          remains uncommitted (`detected`) and is a candidate for mid-dialogue
│  │          re-injection.
│  │       2. Exit 0 with empty stdout: automatic suppression fired — topic is
│  │          now `suppressed`. Do not log error; this is expected when results
│  │          fall below quality threshold. Continue with remaining entries.
│  │       3. Exit 0 with non-empty stdout: commit succeeded — topic is now
│  │          `injected`.
│  │
│  │       NOTE (CE-8 / D1): This initial commit is NOT subject to the shadow-mode
│  │       gate. Phase A (initial injection) is always active regardless of
│  │       `graduation.json` status. The shadow-mode gate governs only Phase B
│  │       mid-dialogue mutations in `codex-dialogue`. See delivery.md Phase A/B
│  │       risk boundary.
```

- [ ] **Step 2: CE-9 — Add `inventory_snapshot` to delegation envelope** (lines 278-283)

The delegation envelope table at line 278 is missing the `inventory_snapshot` path that `codex-dialogue` must pass on all CLI calls.

Add a new row after the `ccdi_seed` row (line 280):

```markdown
| `ccdi_inventory_snapshot` | file path (string) | ccdi-gatherer output | Pinned inventory snapshot for `--inventory-snapshot` on all `build-packet` CLI calls. Required when `ccdi_seed` is present. |
```

- [ ] **Step 3: CC-4 — Broaden `shadow_suppressed` scope** (line 290)

Per design decision D2. Change line 290 from:

Old:
```
Value is `true` when the trace entry describes an action whose registry mutation was suppressed by `--shadow-mode` (currently only `skip_cooldown`); `false` otherwise.
```

New:
```
Value is `true` when the trace entry describes an action whose registry mutation was suppressed by shadow mode — currently `skip_cooldown` (CLI-enforced via `--shadow-mode` flag) and `skip_scout` (agent-enforced abstention from `--mark-deferred scout_priority`); `false` otherwise.
```

- [ ] **Step 4: CC-3 + CC-4 — Add cross-references to action table rows** (lines 305-309)

Add parenthetical cross-references from action table entries to `deferred_reason` enum.

For the `defer` row (line 305), append to the meaning:
```
| `defer` | Topic deferred (`--mark-deferred` committed). Corresponds to `deferred_reason: "target_mismatch"` — see [registry.md#entry-structure](registry.md#entry-structure). | Yes — active mode only; prohibited in shadow mode |
```

For the `skip_cooldown` row (line 307), append `(deferred_reason: "cooldown")` to the first sentence and add shadow_suppressed detail.

For the `skip_scout` row (line 308), update to include shadow_suppressed behavior:

Old:
```
| `skip_scout` | Topic deferred due to scout priority. In active mode, `skip_scout` is emitted (not `defer`) even though `--mark-deferred` is committed — the scout reason takes priority over the generic defer action. In shadow mode, `skip_scout` indicates the intended deferral that was not committed. | Yes via `--mark-deferred` (active) / No (shadow — prohibited) |
```

New:
```
| `skip_scout` | Topic deferred due to scout priority (deferred_reason: `"scout_priority"` — see [registry.md#entry-structure](registry.md#entry-structure)). In active mode, `skip_scout` is emitted (not `defer`) even though `--mark-deferred` is committed — the scout reason takes priority over the generic defer action. In shadow mode, `skip_scout` has `shadow_suppressed: true` — the `--mark-deferred scout_priority` call that would have occurred in active mode is not made. | Yes via `--mark-deferred` (active) / No (shadow — `shadow_suppressed: true`) |
```

- [ ] **Step 5: CC-4 — Add clarifying note to `shadow_defer_intent` schema** (line 317)

After line 317, add:

```markdown
**Scope note:** `shadow_defer_intent` is scoped to deferrals that participate in shadow yield normalization (`cooldown`, `target_mismatch`). Scout-priority is represented by `skip_scout` with `shadow_suppressed: true` and by `packets_deferred_scout` in diagnostics; it does not emit `shadow_defer_intent` under the current normalization model because scout-priority defers before search/build and does not inflate `packets_prepared`.
```

- [ ] **Step 6: SY-3 — Change SHOULD to MUST and add `--shadow-mode` to pseudocode** (lines 365-385, 424)

At line 424, change:
```
The `codex-dialogue` agent SHOULD pass `--shadow-mode` to `build-packet`
```
to:
```
The `codex-dialogue` agent MUST pass `--shadow-mode` to `build-packet`
```

In the pseudocode at lines 366-371 (target-mismatch active-mode branch), the command is correct for active mode — no change needed.

At line 372, change:
```
│   │       └─ If shadow mode: no registry mutation (diagnostics record the intended deferral)
```
to:
```
│   │       └─ If shadow mode: Bash: python3 topic_inventory.py build-packet \
│   │                    --registry-file /tmp/ccdi_registry_<id>.json \
│   │                    --mode mid_turn \
│   │                    --mark-deferred <topic_key> --deferred-reason target_mismatch \
│   │                    --shadow-mode --skip-build
│   │            (--shadow-mode makes --mark-deferred a no-op; diagnostics record the intent)
```

At line 385, change:
```
│   │   └─ If shadow mode: no registry mutation (diagnostics record the intended deferral)
```
to:
```
│   │   └─ If shadow mode: Bash: python3 topic_inventory.py build-packet \
│   │                --registry-file /tmp/ccdi_registry_<id>.json \
│   │                --mode mid_turn \
│   │                --mark-deferred <topic_key> --deferred-reason scout_priority \
│   │                --shadow-mode --skip-build
│   │        (--shadow-mode makes --mark-deferred a no-op; diagnostics record the intent)
```

Add enforcement layer notes to the `skip_scout` action row (already done in Step 4).

#### P2 Fixes

- [ ] **Step 7: CC-7 — Add Facet cross-reference to candidates JSON schema** (line ~106)

In the candidates JSON schema table, find the `facet` row and add:
```
(see [data-model.md#queryplan](data-model.md#queryplan) for valid values)
```
to match the pattern used in classifier.md and registry.md.

- [ ] **Step 8: CE-4 — Add flag name enforcement cross-reference**

Locate the `--shadow-mode` flag description and add a cross-reference to the CLI argument table noting that `--shadow-mode` MUST match the flag name defined in the CLI interface section.

- [ ] **Step 9: Verify and commit**

Verify all cross-reference anchors resolve:
- `registry.md#entry-structure` exists
- `data-model.md#queryplan` exists
- `delivery.md` Phase A/B references resolve

```bash
git add docs/superpowers/specs/ccdi/integration.md
git commit -m "fix(spec): remediate 8 integration.md findings from review round 10

P1: SY-3 SHOULD→MUST + pseudocode --shadow-mode flags
P1: CE-2 three postconditions for initial commit (D3)
P1: CE-8 Phase A always-active note (D1)
P1: CE-9 add inventory_snapshot to delegation envelope
P1: CC-3 cross-references from action table to deferred_reason
P1: CC-4 shadow_suppressed scope + shadow_defer_intent scope note (D2)
P2: CC-7 Facet cross-reference in candidates schema
P2: CE-4 flag name enforcement cross-reference"
```

---

### Task 3: `registry.md` — State Machine Precision (4 P1, 1 P2)

**Files:**
- Modify: `registry.md` field update rules section (CE-3, CE-10), `registry.md` consecutive_medium_count section (CE-5), `registry.md:34` (SP-8), `registry.md` Alias section (SP-12)

#### P1 Fixes

- [ ] **Step 1: CE-3 — Add re-entry field refresh rule**

In the field update rules section, find the `redundant` suppression re-entry row. Add explicit rule:

```markdown
**Re-entry from `redundant` suppression:** When a `redundant`-suppressed topic re-enters `detected` state via new-leaf path (coverage state changed), `coverage_target` and `facet` retain their prior values from the suppressed entry. The topic is not schedulable until the classifier produces it in the next turn's output, at which point `coverage_target` and `facet` are refreshed from the new `ClassifierResult`.
```

- [ ] **Step 2: CE-5 — Add cross-reference note for consecutive_medium_count double-reset**

Locate the `deferred→detected` bypass row that resets `consecutive_medium_count` to 0. Add a cross-reference note:

```markdown
*Note: This reset is idempotent with the general non-medium re-detection rule (which also resets to 0 on any non-medium detection). Both rules fire in the same turn when a deferred topic returns at non-medium confidence. The double-reset is harmless — documented here for implementer clarity.*
```

- [ ] **Step 3: CE-10 — Add initialization rule for hint-driven deferred→detected**

Locate the hint-driven `deferred→detected` transition. Add explicit initialization:

```markdown
**Hint-driven `deferred→detected` initialization:** Uses TTL-expiry semantics consistent with `absent→detected`: `consecutive_medium_count` initializes to `1` when the classifier reports medium confidence AND leaf-kind; `0` otherwise (including family-kind, absent-from-classifier, and non-medium confidence cases).
```

- [ ] **Step 4: SP-8 — Add no-recovery note for pending_facets** (after line 34)

After the existing FIFO queue description at line 34, add:

```markdown
**Load-time recovery:** No load-time recovery is defined for `pending_facets` FIFO corruption. With the current schema, loaders cannot infer original insertion order from the serialized array alone (no timestamps or sequence metadata). Implementations MUST preserve serialized array order exactly as loaded; no load-time re-sort, reinitialization, or heuristic repair is defined. Correctness is enforced by the write-time invariant and serialization tests.
```

#### P2 Fix

- [ ] **Step 5: SP-12 — Specify Alias.source behavior on override_weight**

Locate the `Alias` type definition or the `override_weight` operation description. Add:

```markdown
**`Alias.source` on `override_weight`:** When `override_weight` modifies an alias's weight, the `Alias.source` field is unchanged — it retains the value set at alias creation (scaffold or overlay).
```

- [ ] **Step 6: Verify and commit**

```bash
git add docs/superpowers/specs/ccdi/registry.md
git commit -m "fix(spec): remediate 5 registry.md findings from review round 10

P1: CE-3 re-entry field refresh rule for redundant suppression
P1: CE-5 cross-reference note for consecutive_medium_count double-reset
P1: CE-10 hint-driven deferred→detected initialization rule
P1: SP-8 no load-time recovery for pending_facets (D5)
P2: SP-12 Alias.source behavior on override_weight"
```

---

### Task 4: `data-model.md` — Schema Precision (6 P1, 6 P2)

**Files:**
- Modify: `data-model.md:208` (SP-5), `data-model.md:312` (SP-2), `data-model.md` Version Axes section (SP-6, SP-11), `data-model.md` RegistrySeed section (SP-7, SP-10), `data-model.md:58-79` (SP-1, CC-8), `data-model.md` DenyRule section (SP-3), `data-model.md:310` (SP-4), `data-model.md` config section (SP-9), `data-model.md:56-57` (AA-4)

#### P1 Fixes

- [ ] **Step 1: SP-5 — Complete AppliedRule.target semantics** (line 208)

Per design decision D4. Expand the `target` field description to include all 8 operations:

Old (line 208):
```
| `target` | string | `target: string` — semantics depend on `operation`:<br>- **Topic-scoped operations** (`add_topic`, `override_weight`, `replace_aliases`): `target` is a `TopicKey` (e.g., `"hooks.pre_tool_use"`).<br>- **`add_deny_rule`**: `target` is the `deny_rule.id` (e.g., `"deny_stale_hooks"`).<br>- **`override_config`**: `target` is a dot-delimited config key path matching a leaf scalar in `ccdi_config.json` (e.g., `"classifier.confidence_high_min_weight"`). Only leaf scalars are valid targets — nested objects are not directly addressable. |
```

New:
```
| `target` | string | `target: string` — semantics depend on `operation`:<br>- **Topic-scoped operations** (`add_topic`, `override_weight`, `replace_aliases`, `remove_alias`, `replace_refs`, `replace_queries`): `target` is a `TopicKey` (e.g., `"hooks.pre_tool_use"`).<br>- **`add_deny_rule`**: `target` is the `deny_rule.id` (e.g., `"deny_stale_hooks"`).<br>- **`override_config`**: `target` is a dot-delimited config key path matching a leaf scalar in `ccdi_config.json` (e.g., `"classifier.confidence_high_min_weight"`). Only leaf scalars are valid targets — nested objects are not directly addressable. |
```

- [ ] **Step 2: SP-2 — Add missing fields to non-nullable enumeration** (line 312)

At line 312, the non-nullable always-present fields paragraph lists `consecutive_medium_count` and `coverage.*` sub-fields but omits `kind`, `coverage_target`, and `facet`.

Add to the non-nullable enumeration sentence:
```
This includes `kind` (string, always `"leaf"` or `"family"`), `coverage_target` (string, always `"leaf"` or `"family"`), `facet` (Facet enum), `consecutive_medium_count` (integer, ...
```

- [ ] **Step 3: SP-6 — Add cross-reference for merge_semantics_version**

In the Version Axes section (around line 35), locate the `merge_semantics_version` row. Add a cross-reference to the build/load asymmetry:

```markdown
**Build/load asymmetry:** `merge_semantics_version` is written by `build_inventory.py` at build time but consumed by the CLI at load time. The version semantics for build-time vs load-time are defined in the build pipeline, not in this specification — see the build/load lifecycle in the overlay merge semantics section.
```

- [ ] **Step 4: SP-7 — Add immutability cross-reference for inventory_snapshot_version**

In the RegistrySeed section, after the `inventory_snapshot_version` field description, add:

```markdown
**Immutability:** `inventory_snapshot_version` is set at seed creation and MUST NOT change during the dialogue. The CLI uses it for version-mismatch gating at seed load — a changed value would invalidate the mismatch check. See `build_inventory.py` for the source of the version value.
```

- [ ] **Step 5: SP-10 — Add forward-compatibility note for entries[] delegation**

In the RegistrySeed section, after the `entries` field description, add:

```markdown
**Authority delegation:** The entry-level field set within `entries[]` is defined authoritatively by [registry.md#entry-structure](registry.md#entry-structure), not by this file. Changes to entry fields in registry.md do not require updates to data-model.md unless they affect the envelope schema (the four top-level fields: `entries`, `docs_epoch`, `inventory_snapshot_version`, `results_file`).
```

- [ ] **Step 6: SP-11 — Scope merge_semantics_version "always present" assertion**

Find the `merge_semantics_version` discussion and add schema-evolution scoping:

```markdown
**Schema evolution note:** `merge_semantics_version` is "always present" in inventories built by the current `build_inventory.py`. For inventories built by older versions that predate this field, the failure mode is: inventory load continues with default merge semantics (version 1 behavior). This is not a load-time error — it is a graceful degradation consistent with the schema evolution constraint.
```

#### P2 Fixes

- [ ] **Step 7: SP-1 — Reorder coverage sub-fields in defaults table** (lines 58-79)

Move `coverage.overview_injected` (line 77) and `coverage.family_context_available` (line 78) to be adjacent to the other `coverage.*` fields (after line 71). The reordered block should group all five `coverage.*` defaults contiguously.

- [ ] **Step 8: CC-8 — Add footnote to consecutive_medium_count default** (line 64)

Change line 64 from:
```
| `consecutive_medium_count` | `0` |
```
to:
```
| `consecutive_medium_count` | `0`* |
```

Add footnote below the table:
```markdown
*\* Schema-migration fallback only — runtime initialization uses `1` for medium-confidence leaf-kind entries. See "Defaults vs initialization" below.*
```

- [ ] **Step 9: AA-4 — Add scope note to defaults table header** (lines 56-57)

After the existing header text at line 56, add:

```markdown
**Authority split note:** Field *definitions* (names, types, behavioral rules) are owned by [registry.md#entry-structure](registry.md#entry-structure) under `registry-contract` authority. This table owns only the *serialization defaults* for schema evolution under `data-model` (`persistence_schema`) authority.
```

- [ ] **Step 10: SP-3 — Add DenyRule penalty:0 load-time note**

In the DenyRule section, add:

```markdown
**`penalty: 0` at load time:** A DenyRule with `penalty: 0` is valid and produces no score impact. The classifier treats it as a no-op deny rule — the topic is still matched but not penalized. This may occur when an overlay sets `penalty` to 0 to effectively disable a rule without removing it.
```

- [ ] **Step 11: SP-4 — Consolidate docs_epoch null-serialization references**

The `docs_epoch: null` serialization requirement appears at 3 locations. At the two non-primary locations, replace the full description with a cross-reference:

Add "(see [Non-nullable always-present fields](#registryseed) for the null-serialization invariant)" at the secondary mention sites.

- [ ] **Step 12: SP-9 — Document config_overrides boolean type**

In the config_overrides section, add:

```markdown
**Boolean values:** Config override values include `boolean` as a valid scalar type (`true`/`false`). While no current config key is boolean-typed, the schema permits it for forward compatibility. Boolean values are serialized as JSON `true`/`false`, not as strings.
```

- [ ] **Step 13: Verify and commit**

```bash
git add docs/superpowers/specs/ccdi/data-model.md
git commit -m "fix(spec): remediate 12 data-model.md findings from review round 10

P1: SP-5 complete AppliedRule.target for all 8 operations (D4)
P1: SP-2 add kind/coverage_target/facet to non-nullable enumeration
P1: SP-6 merge_semantics_version build/load cross-reference
P1: SP-7 inventory_snapshot_version immutability cross-reference
P1: SP-10 entries[] authority delegation forward-compatibility note
P1: SP-11 merge_semantics_version schema evolution scoping
P2: SP-1 reorder coverage sub-fields contiguously
P2: CC-8 consecutive_medium_count footnote for default vs init
P2: AA-4 authority split scope note on defaults table
P2: SP-3 DenyRule penalty:0 load-time handling
P2: SP-4 consolidate docs_epoch null-serialization references
P2: SP-9 document config_overrides boolean type"
```

---

### Task 5: `delivery.md` P1 — Verification Spec Fixes (8 P1)

**Files:**
- Modify: `delivery.md` Layer 2b section (~lines 746+), Layer 2a section, boundary contract tests section (~line 402+), graduation protocol test table (~lines 185-190)

#### P1 Fixes

- [ ] **Step 1: VR-1 — Add authority enforcement note to Layer 2b**

In the Layer 2b: Agent Sequence Tests section, add a note:

```markdown
**Authority source note:** Each pipeline isolation invariant test in this section is a normative `behavior_contract` test sourced from [integration.md#pipeline-isolation-invariants](integration.md#pipeline-isolation-invariants). These tests verify behavior_contract authority (outranking decision_record) — do not weaken or reclassify these tests during code review. Additionally, add a boundary contract test in `test_ccdi_contracts.py` verifying the sentinel structure invariant at the agent-behavior level: `ccdi_seed` field in the delegation envelope is a file path, not an inline JSON object.
```

- [ ] **Step 2: VR-2 — Specify CLI backstop test observable**

In the Layer 2b test for `build-packet --shadow-mode --mark-deferred`, replace "zero registry mutations" with a precise definition:

```markdown
**Observable assertion:** JSON-parse semantic identity — load registry file before and after `build-packet --shadow-mode --mark-deferred scout_priority`, parse both as JSON, assert `json.loads(before) == json.loads(after)`. This detects no-op rewrites that would change file mtime but not content.
```

Add this as a named row in the Layer 2b test table.

- [ ] **Step 3: VR-3 — Expand classify_result_hash test dimensions**

In the `classify_result_hash` test specification, add test cases for `confidence` and `facet` dimensions:

```markdown
| Same topic_key, different confidence | `classify("hooks.pre_tool_use", confidence=0.8)` vs `classify("hooks.pre_tool_use", confidence=0.6)` | Different hashes |
| Same topic_key, different facet | `classify("hooks.pre_tool_use", facet="overview")` vs `classify("hooks.pre_tool_use", facet="configuration")` | Different hashes |
```

- [ ] **Step 4: VR-4 — Reclassify freshness guardrail positive-path test**

The positive-path freshness guardrail test at line 125 is currently specified as Layer 2b. Move it to the integration test section (`test_shadow_freshness_guardrail.py`) since it requires invoking `validate_graduation.py`:

Add to the `test_shadow_freshness_guardrail.py` section:
```markdown
**Positive-path test:** Fixture: classify produces *different* `classify_result_hash` values across turns for a topic with `shadow_defer_intent`. Assert: `shadow_adjusted_yield` IS used as the graduation gate (validator does NOT emit the guardrail warning). This is an integration test (requires validator invocation), not a Layer 2b test.
```

Remove or reclassify the Layer 2b reference at line 125.

- [ ] **Step 5: VR-5 — Add boundary rule 5 contract test**

In the Boundary Contract Tests section, add:

```markdown
| graduation.json status enum consistency | delivery.md `graduation.json` schema `status` field uses enum values that exist in integration.md shadow-mode gate algorithm | Assert: every `status` value in the graduation.json schema example is handled by the shadow-mode gate conditional in integration.md |
```

- [ ] **Step 6: VR-7 — Add injected forward-only CLI-level test**

In the appropriate test section, add:

```markdown
| `injected` forward-only invariant (CLI-level) | Integration test companion to the unit-level `injected` state transition test. Invoke `build-packet --mark-injected` on a topic in `injected` state, verify the CLI preserves `injected` state (no regression to `detected`). | `test_ccdi_contracts.py` — boundary test asserting that `--mark-injected` on an already-injected entry is idempotent |
```

- [ ] **Step 7: VR-11 — Add shadow-mode scout-priority Layer 2b fixture**

In the Layer 2b test section, add:

```markdown
| Shadow-mode scout-priority abstention | Fixture with active scout target + CCDI candidate in shadow mode. Assert: `skip_scout` action with `shadow_suppressed: true`; zero `--mark-deferred` CLI invocations; no `shadow_defer_intent` entry for scout-priority. | `shadow_skip_scout.replay.json` |
```

- [ ] **Step 8: VR-14 — Add results_file write-time exclusion test**

In the boundary contract tests section, add:

```markdown
| `results_file` write-time exclusion | Write a RegistrySeed with `results_file` field present. Load via registry loader. Assert `results_file` is stripped from the live registry (not just at load-time — verify the written file after initial commit does NOT contain `results_file`). | `test_ccdi_contracts.py` — verifies write-time stripping, not just load-time |
```

- [ ] **Step 9: Verify and commit**

```bash
git add docs/superpowers/specs/ccdi/delivery.md
git commit -m "fix(spec): remediate 8 P1 verification findings in delivery.md

VR-1: authority enforcement note for pipeline isolation tests
VR-2: JSON-parse semantic identity for CLI backstop test
VR-3: classify_result_hash confidence and facet dimensions
VR-4: reclassify freshness guardrail positive-path to integration test
VR-5: boundary rule 5 graduation.json status enum contract test
VR-7: injected forward-only CLI-level integration test
VR-11: shadow-mode scout-priority Layer 2b fixture
VR-14: results_file write-time exclusion boundary test"
```

---

### Task 6: `delivery.md` P2 + Emerged (6 P2, 1 emerged)

**Files:**
- Modify: `delivery.md` test sections, diagnostics section

#### P2 Fixes

- [ ] **Step 1: VR-6 — Specify freshness guardrail fixture mechanism**

Add to the freshness guardrail test specification:

```markdown
**Fixture construction:** The test fixture MUST construct a `graduation.json` where `classify_result_hash` is identical across all turns for at least one topic with `shadow_defer_intent`. This simulates a stale classify pipeline. The fixture generator can use a fixed hash string (e.g., `"stale_hash_fixture"`) for all turns of the target topic.
```

- [ ] **Step 2: VR-8 — Add pending_facets reload-write test**

Add to the replay harness test list:

```markdown
| `pending_facets` reload-then-write | Write registry with `pending_facets: ["config", "schema"]`. Load via registry loader. Write back to disk. Assert disk order is exactly `["config", "schema"]` (FIFO preserved through full round-trip, not just load). | `pending_facets_roundtrip.replay.json` |
```

- [ ] **Step 3: VR-9 — Add ast.parse meta-test false negative mitigation**

Add to the Layer 3 meta-test section:

```markdown
**False negative risk:** `ast.parse`-based meta-tests that verify test file structure can miss false negatives when the assertion target is a computed value (e.g., `assert result == expected` where `expected` is derived at runtime). Supplement `ast.parse` structural checks with at least one runtime canary test per test file that verifies the meta-test would detect a known-bad fixture.
```

- [ ] **Step 4: VR-10 — Add multi-entry docs_epoch scan test**

Add to the appropriate test section:

```markdown
| Multi-entry `docs_epoch` scan | Registry with 3+ entries, each with different `suppressed_docs_epoch` values. Change `docs_epoch`. Assert: only entries whose `suppressed_docs_epoch` matches the *old* `docs_epoch` are eligible for re-entry — entries with other `suppressed_docs_epoch` values remain suppressed. | Verifies the scan is per-entry, not registry-wide |
```

- [ ] **Step 5: VR-13 — Add strict=True to xfail placeholders**

Search for `xfail` markers in the test specification. For each `xfail` placeholder, add `strict=True`:

```python
@pytest.mark.xfail(strict=True, reason="...")
```

Add a note:
```markdown
**`xfail` convention:** All `xfail` markers in this spec MUST use `strict=True` to prevent silent test passes when the expected failure is fixed. An `xfail(strict=True)` test that unexpectedly passes is flagged as `XPASS` (failure), prompting removal of the marker.
```

- [ ] **Step 6: VR-15 — Add cooldown config divergence test**

Add:

```markdown
| Cooldown config divergence | Agent uses hardcoded cooldown default (2 turns). Overlay sets `config_overrides.scheduler.cooldown_turns: 5`. Assert: agent behavior uses hardcoded value (2), NOT overlay value (5). CLI respects overlay value for its own scheduling. | Verifies pipeline isolation — agent config is independent of CLI config |
```

#### Emerged Item

- [ ] **Step 7: CE-8 emerged — Add diagnostics counter scoping**

In the shadow-mode diagnostics section (around line 95-100), add:

```markdown
**Diagnostics scope:** `topics_injected` and `packets_injected` counters in shadow-mode diagnostics reflect Phase B (mid-dialogue) activity only, not all-dialogue totals. Phase A initial commit state is reflected in the seed file, not in these counters.
```

- [ ] **Step 8: Commit**

```bash
git add docs/superpowers/specs/ccdi/delivery.md
git commit -m "fix(spec): remediate 6 P2 + 1 emerged delivery.md findings

P2: VR-6 freshness guardrail fixture mechanism
P2: VR-8 pending_facets reload-write round-trip test
P2: VR-9 ast.parse meta-test false negative mitigation
P2: VR-10 multi-entry docs_epoch scan test
P2: VR-13 xfail strict=True convention
P2: VR-15 cooldown config divergence test
Emerged: CE-8 diagnostics counter Phase B scoping"
```

---

### Task 7: `decisions.md` + `README.md` — Remaining Fixes (1 P2 + 1 emerged + 2 P2)

**Files:**
- Modify: `decisions.md:61` (emerged CE-8), `decisions.md:41` (CC-5)
- Modify: `README.md:25-29` (SY-1), `README.md:16` (CC-6)

#### decisions.md

- [ ] **Step 1: CE-8 emerged — Narrow staged-rollout invariant** (line 61)

Update the staged-rollout decision row's description. Change the current text at line 61:

Old description column:
```
Does not commit injections or deferrals until graduation gate approves
```

New:
```
The graduation gate applies only to Phase B mid-dialogue CCDI mutations after delegation begins. Phase A initial injection (pre-delegation) is unconditional. See [integration.md#shadow-mode-gate](integration.md#shadow-mode-gate) for the authoritative behavioral constraint.
```

- [ ] **Step 2: CC-5 — Add four-layer link** (line ~41)

The decisions.md records "Four-layer test strategy" without linking to the implementation. Add cross-reference — if this decision appears as a row, add to the authoritative reference column:

```
[delivery.md#four-layer-approach](delivery.md#four-layer-approach)
```

#### README.md

- [ ] **Step 3: SY-1 — Fix broken authority table** (lines 25-29)

The `*Note:` annotation between the `integration` and `delivery` rows breaks the markdown table. Move the note to after the table closes.

Remove line 27 (`*Note: §pipeline-isolation-invariants holds elevated...`) from between table rows. Add it as a paragraph after the table's last row (line 30, after `| supporting |...`):

```markdown
*Note: §pipeline-isolation-invariants in integration.md holds elevated `behavior_contract` authority for behavioral invariants cross-referenced from decisions.md. See spec.yaml `elevated_sections`.*
```

- [ ] **Step 4: CC-6 — Clarify 9 authorities count** (line 16)

Change line 16 from:
```
9 authorities govern the spec.
```
to:
```
9 authorities govern the spec (8 normative files + this README as the `supporting` entry point).
```

- [ ] **Step 5: Verify and commit**

Verify README table renders correctly (all 9 authority rows visible).

```bash
git add docs/superpowers/specs/ccdi/decisions.md docs/superpowers/specs/ccdi/README.md
git commit -m "fix(spec): remediate decisions.md and README.md findings

Emerged: CE-8 narrow staged-rollout invariant to Phase B scope
P2: CC-5 add four-layer-approach cross-reference link
P2: SY-1 fix broken authority table (move Note after table)
P2: CC-6 clarify 9 authorities count (8 normative + README)"
```

---

## Verification Checklist

After all tasks complete, run these final checks:

- [ ] **Cross-reference audit:** Grep for all `](` patterns in modified files and verify each anchor resolves.
- [ ] **Count consistency:** Verify "9 authorities" count still matches spec.yaml entries.
- [ ] **Field name consistency:** Grep for `p95_prepare_latency_ms` — should return 0 matches across all spec files.
- [ ] **YAML validity:** Parse spec.yaml with Python yaml module.
- [ ] **No orphaned findings:** Verify all 48 finding IDs (SY-2, SY-3, AA-1 through AA-7, CE-1 through CE-10, CC-1 through CC-8, VR-1 through VR-15, SP-1 through SP-12) are addressed in one of the 7 commits.

## Commit Summary

| # | Task | Commit message prefix | Finding count |
|---|------|-----------------------|---------------|
| 0 | P0 fix | `fix(spec): fix P0 graduation.json latency field name` | 1 |
| 1 | spec.yaml | `fix(spec): remediate 5 spec.yaml findings` | 5 |
| 2 | integration.md | `fix(spec): remediate 8 integration.md findings` | 8 |
| 3 | registry.md | `fix(spec): remediate 5 registry.md findings` | 5 |
| 4 | data-model.md | `fix(spec): remediate 12 data-model.md findings` | 12 |
| 5 | delivery.md P1 | `fix(spec): remediate 8 P1 verification findings` | 8 |
| 6 | delivery.md P2 | `fix(spec): remediate 6 P2 + 1 emerged delivery.md` | 7 |
| 7 | decisions.md + README | `fix(spec): remediate decisions.md and README.md` | 4 |
| **Total** | | | **50** |
