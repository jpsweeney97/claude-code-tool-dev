# CCDI Spec Remediation Plan — Review Round 4

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate all 38 findings (2 P0, 23 P1, 13 P2) from the round-4 spec review at `.review-workspace/synthesis/report.md`.

**Architecture:** All changes target spec files in `docs/superpowers/specs/ccdi/`. No code. Five tasks grouped by target file to avoid merge conflicts. Ordered by dependency: data-model foundations first (authority moves OUT), then registry (authority moves IN + behavioral fixes), then integration and delivery in parallel, then minor single-file fixes.

**Tech Stack:** Markdown spec files

**Review source:** `.review-workspace/synthesis/report.md` (38 canonical findings from 45 raw, 7 duplicate clusters merged, 7 corroborated across reviewers)

---

## File Map

| File | Task | Findings | Priority Breakdown |
|------|------|----------|-------------------|
| `data-model.md` | 1 | SY-6, SY-7, SY-11(out), SY-12(out), SY-16, SY-17, SY-18, SY-33, SY-34, SY-35 | 7 P1, 3 P2 |
| `registry.md` | 2 | SY-1, SY-3, SY-5, SY-10, SY-11(in), SY-12(in), SY-15, SY-29 | 6 P1, 2 P2 |
| `integration.md` | 3 | SY-2, SY-13, SY-14, SY-24, SY-25, SY-30 | 5 P1, 1 P2 |
| `delivery.md` + `decisions.md` | 4 | SY-4, SY-8, SY-9, SY-19, SY-20, SY-21, SY-22, SY-23, SY-26, SY-32, SY-36, SY-37, SY-38 | 2 P0, 8 P1, 3 P2 |
| `classifier.md`, `foundations.md`, `packets.md` | 5 | SY-27, SY-28, SY-31 | 3 P2 |

## Dependency Graph

```
Task 1 (data-model.md) ──→ Task 2 (registry.md) ──→ Task 3 (integration.md)
                                    │
                                    └──→ Task 4 (delivery.md + decisions.md)
                                              ↑ (delivery.md step citation from Task 2)

Task 5 (classifier/foundations/packets) — independent, any time
```

**Critical path:** Task 1 → Task 2 → Task 3

**Parallelism:** After Task 2 completes, Tasks 3 and 4 can run in parallel. Task 5 can run at any time.

**Why Task 1 must be first:** SY-11 and SY-12 move behavioral content FROM data-model.md TO registry.md. Task 1 removes content and adds cross-reference stubs. Task 2 adds the moved content to registry.md. Doing them in the wrong order risks orphaning the content.

**Why Task 2 before Tasks 3–4:** SY-10 renumbers registry.md scheduling steps. Task 2 updates the step numbers. Tasks 3 and 4 must use the new numbers in cross-references (delivery.md cites "step 7" which will become "step 8" after reorder).

---

## Verification Protocol

After each task, before committing:

1. **Cross-reference check:** Grep for all `registry.md#`, `integration.md#`, `data-model.md#` anchors in modified files. Verify target headings exist.
2. **Step number check:** After Task 2, grep all files for `step [0-9]` references to scheduling rules. Verify they match the new numbering.
3. **Term consistency:** After any rename (e.g., SY-4 test rename), grep for old term across all 8 spec files.
4. **Authority model:** Verify modified content's claim family matches the file's `default_claims` in `spec.yaml`.

```bash
# Cross-reference verification (run from spec directory)
grep -rn 'registry\.md#\|integration\.md#\|data-model\.md#\|delivery\.md#\|classifier\.md#\|packets\.md#\|foundations\.md#\|decisions\.md#' *.md | while read line; do
  anchor=$(echo "$line" | grep -oP '(?<=\.md#)[a-z0-9-]+' | head -1)
  target_file=$(echo "$line" | grep -oP '[a-z-]+\.md(?=#)' | head -1)
  if [ -n "$anchor" ] && [ -n "$target_file" ] && [ -f "$target_file" ]; then
    heading=$(echo "$anchor" | tr '-' ' ')
    if ! grep -qi "^#.*$heading" "$target_file" 2>/dev/null; then
      echo "BROKEN: $line → $target_file#$anchor"
    fi
  fi
done
```

---

### Task 1: Fix data-model.md — Authority Moves + Schema Validation Gaps

**Files:**
- Modify: `data-model.md`

**Findings:** SY-6, SY-7, SY-11(move out), SY-12(move out), SY-16, SY-17, SY-18, SY-33, SY-34, SY-35

This task removes behavioral content that belongs under `registry-contract` authority (SY-11, SY-12), adds missing schema-level specifications (SY-6, SY-7, SY-16, SY-17, SY-18), and tightens three P2 precision issues (SY-33, SY-34, SY-35).

- [ ] **Step 1: SY-11 — Move behavioral Failure Modes rows to registry.md (Part 1: Remove from data-model.md)**

In the Failure Modes section (~line 358), three rows prescribe registry state-machine behavior that belongs under `registry-contract` authority, not `persistence_schema`:

1. **`deferred_ttl: 0` row** — prescribes "apply the `deferred → detected` or `deferred → deferred` transition rule on the next `dialogue-turn` call"
2. **`results_file` stripping row** — prescribes "Strip `results_file` from the in-memory representation and log warning... the stripped state is written back on the next normal mutation"
3. **RegistrySeed version mismatch rewrite-deferral** — prescribes "the registry file is NOT rewritten at load time... Rewriting is deferred to the next normal `--mark-injected` or `--mark-deferred` mutation"

Replace each row's behavioral content with a schema-level fact plus cross-reference:

| Original behavioral content | Replacement |
|---|---|
| `deferred_ttl: 0` recovery behavior | "A value of 0 is a valid persisted state indicating TTL expired before transition was written. See [registry.md#failure-modes](registry.md#failure-modes) for recovery behavior." |
| `results_file` stripping behavior | "`results_file` is a transient field not intended for long-term persistence. See [registry.md#failure-modes](registry.md#failure-modes) for load-time handling." |
| RegistrySeed version mismatch rewrite | "Version mismatch is a valid load-time state. See [registry.md#failure-modes](registry.md#failure-modes) for rewrite-deferral behavior." |

- [ ] **Step 2: SY-12 — Move consecutive_medium_count load-time validation to registry.md (Part 1: Remove from data-model.md)**

In the RegistrySeed section (~line 264), the "Load-time validation" paragraph prescribes: "CLI MUST validate that family-kind entries have `consecutive_medium_count == 0`." This derives from a registry scheduling rule (step 4), not a schema constraint.

Replace with schema note:
```
**Load-time schema note:** `consecutive_medium_count` is always serialized including when 0.
Family-kind entries MUST have this field present with value 0
(see [registry.md#failure-modes](registry.md#failure-modes) for load-time validation and recovery).
```

- [ ] **Step 3: SY-7 — Add schema_version mismatch Failure Modes row**

Add a new row to the Failure Modes table (~line 358) for `CompiledInventory.schema_version` mismatch at CLI load time. Currently the test in delivery.md validates this behavior but no normative spec row exists.

New row:
| Condition | Behavior | Resilience |
|---|---|---|
| `CompiledInventory.schema_version` does not match the CLI's expected version | CLI logs warning and proceeds with best-effort field mapping. Fields absent in the loaded version use schema defaults. Fields present but unrecognized are preserved on write-back. | Fail-open: stale inventory is better than no inventory. |

- [ ] **Step 4: SY-6 — Add DenyRule load-time validation**

In the DenyRule section (~line 89), the discriminated union (downrank-penalty XOR null-results) is validated only at build time. Add a load-time validation paragraph after the DenyRule schema definition:

```
**Load-time validation:** When loading a compiled inventory, each DenyRule MUST
satisfy exactly one branch of the discriminated union (either `downrank_penalty`
is non-null OR `null_results` is true, never both). On violation: skip the
offending rule with a warning log entry. Do not fail the entire inventory load.
This aligns with the resilience principle (foundations.md#resilience-principle).
```

- [ ] **Step 5: SY-16 — Resolve aliases non-empty constraint inconsistency**

The OverlayRule table (~line 227, `add_topic` row) requires non-empty `aliases`, but the TopicRecord base schema (~line 60) allows empty `aliases` (type: `list[Alias]`, no minimum length).

Add minimum-length constraint to the TopicRecord schema:
```
aliases: list[Alias]  # minimum 1 — every topic must have at least one searchable alias
```

This makes the TopicRecord schema and add_topic overlay consistent. If the design intent is to allow empty aliases on base topics (only requiring them on overlay-added topics), then instead remove the non-empty constraint from the add_topic row and add a note: "Topics with empty aliases are not searchable; overlay authors should provide at least one."

**Decision needed:** Which direction — constrain TopicRecord or relax add_topic? The report recommends the former (constrain TopicRecord) since a topic with zero aliases is unsearchable.

- [ ] **Step 6: SY-17 — Add cross-key min≤max validation for token budgets**

In the Configuration section (~line 312), `token_budget_min` and `token_budget_max` are validated independently with per-key fallback to defaults. But two individually valid values can produce min > max.

Add after the per-key validation paragraph:
```
**Cross-key validation:** After per-key validation, if `token_budget_min > token_budget_max`,
fall back to defaults for **both** keys as a unit and log a warning. Do not fall back
for each key independently — independent fallback can itself produce min > max when
only one key was invalid.
```

- [ ] **Step 7: SY-18 — Add default_facet validation for replace_queries**

In the OverlayRule table (~line 233, `replace_queries` row), a QueryPlan without `default_facet` makes the topic unsearchable at scheduling time (silently suppressed).

Add validation note to the replace_queries row:
```
replace_queries: Replaces the topic's entire query plan. Build-time validation:
MUST include `default_facet` — a QueryPlan without `default_facet` makes the
topic unsearchable. On violation: reject the overlay rule with descriptive error.
```

Also add the same `default_facet` validation to the `add_topic` row since it also accepts a full QueryPlan.

- [ ] **Step 8: SY-33 (P2) — Clarify AppliedRule.target semantic overload**

The `AppliedRule.target` field (~line 168) is used for both TopicKey references (in topic-scoped rules) and config key paths (in config-scoped rules). Add a disambiguation note:

```
target: str  # Semantics depend on rule scope:
             # - Topic-scoped rules: TopicKey (e.g., "python/asyncio")
             # - Config-scoped rules: dot-delimited config key path (e.g., "packets.token_budget_max")
```

- [ ] **Step 9: SY-34 (P2) — Define config_version supported value**

The `config_version` field (~line 298) references a "supported version" but does not state what that value is.

Add: `config_version: int  # Current supported version: 1. CLI rejects files with config_version > 1 (see Failure Modes).`

- [ ] **Step 10: SY-35 (P2) — Scope null-field serialization invariant**

The null-field serialization paragraph (~line 266) states all fields are serialized including nulls, but `inventory_snapshot_version` is non-nullable (it has a concrete integer value). Scope the invariant:

Change from: "All fields are serialized, including null values"
To: "All **nullable** fields are serialized including when null (never omitted). Non-nullable fields (`inventory_snapshot_version`, `schema_version`) are always present with their concrete values."

- [ ] **Step 11: Verify cross-references**

Run: `grep -n 'registry\.md#' data-model.md` — verify all new cross-references point to existing headings.

Verify the Failure Modes table still has consistent column structure after row modifications.

- [ ] **Step 12: Commit**

```bash
git add docs/superpowers/specs/ccdi/data-model.md
git commit -m "fix(spec): remediate 10 findings in data-model.md (SY-6,7,11-out,12-out,16,17,18,33,34,35)

Authority corrections:
- SY-11: Replace behavioral Failure Modes rows with schema facts + cross-refs to registry.md
- SY-12: Replace consecutive_medium_count validation with schema note + cross-ref

Schema validation gaps:
- SY-6: Add DenyRule load-time validation (skip invalid rules per resilience principle)
- SY-7: Add CompiledInventory.schema_version mismatch Failure Modes row
- SY-16: Add non-empty constraint to TopicRecord.aliases
- SY-17: Add cross-key token_budget min≤max validation
- SY-18: Add default_facet build-time validation for replace_queries and add_topic

P2 precision:
- SY-33: Disambiguate AppliedRule.target (TopicKey vs config key path)
- SY-34: Define config_version supported value (1)
- SY-35: Scope null-field serialization to nullable fields only"
```

---

### Task 2: Fix registry.md — Authority Moves In + Behavioral Fixes + Scheduling Restructure

**Files:**
- Modify: `registry.md`
- Modify: `delivery.md` (one-line step citation update after reorder)

**Findings:** SY-1, SY-3, SY-5, SY-10, SY-11(move in), SY-12(move in), SY-15, SY-29

**Depends on:** Task 1 (content moved out of data-model.md)

This task receives behavioral content from data-model.md (SY-11, SY-12), restructures the scheduling rules section (SY-10 + SY-29), fixes three behavioral specification gaps (SY-1, SY-5, SY-15), and adds a missing cross-reference (SY-3).

- [ ] **Step 1: SY-11 — Receive behavioral Failure Modes content from data-model.md (Part 2: Add to registry.md)**

Add three new rows to registry.md's Failure Modes section (~line 228). These contain the behavioral content removed from data-model.md in Task 1:

| Condition | Behavior | Resilience |
|---|---|---|
| Registry file loaded with `deferred_ttl: 0` | Treat as TTL-expired: apply the `deferred → detected` or `deferred → deferred` transition rule on the next `dialogue-turn` call (see [field update rules](#field-update-rules) for transition details). | Recover forward: deferred state with expired TTL indicates interrupted processing. |
| Registry file loaded with `results_file` field present | Strip `results_file` from the in-memory representation and log warning. The `results_file` is a transient field populated by `--prepare` and consumed by the agent within a single turn. Its presence at load time indicates abnormal shutdown. The stripped state is written back on the next normal mutation. | Fail-safe: stale results_file would cause the agent to re-send a previous packet. |
| RegistrySeed `schema_version` mismatch | Proceed with best-effort field mapping. The registry file is NOT rewritten at load time due to version mismatch. Rewriting is deferred to the next normal `--mark-injected` or `--mark-deferred` mutation. | Fail-open: stale schema is better than data loss from premature rewrite. |

- [ ] **Step 2: SY-12 — Receive consecutive_medium_count load-time validation (Part 2: Add to registry.md)**

Add a "Load-time validation" paragraph to the Failure Modes section (or Entry Structure section, whichever is more natural):

```
**Load-time validation:** CLI MUST validate that family-kind entries have
`consecutive_medium_count == 0`. A non-zero value on a family-kind entry indicates
data corruption — family-kind topics never participate in consecutive-medium tracking
(per [scheduling rules](#scheduling-rules) step 4). On violation: reset to 0 and log
warning.
```

Note: After SY-10 reorders steps, verify the step citation ("step 4") is still correct. Step 4 (consecutive-medium injection condition) is not affected by the 7↔8 swap — it stays as step 4.

- [ ] **Step 3: SY-10 + SY-29 — Restructure scheduling rules section**

**SY-10:** Steps 7 and 8 are inverted — step 7 (target-match check after building a packet) logically depends on step 8 (schedule a topic for lookup). Swap them so the operational order matches the numbered sequence.

**SY-29:** The scheduling rules mix CLI-side steps (scheduling, candidate emission) with an agent-side step (target-match verification) without structural boundary markers.

**Combined fix:** Reorder and add boundary markers. The current steps are:

```
Current:                          Fixed:
1. State machine                  1. State machine
2. Confidence filter              2. Confidence filter
3. Topic-kind dispatch            3. Topic-kind dispatch
4. Consecutive-medium injection   4. Consecutive-medium injection
5. Cooldown                       5. Cooldown
6. Scout priority                 6. Scout priority
7. Target-match (agent-side) ←    7. Schedule highest-priority topic  (was 8)
8. Schedule topic            ←    8. Pending_facet candidate emission  (was 9)
9. Pending_facet emission         9. Facet_expansion candidate emission (was 10)
10. Facet_expansion emission      --- Agent-side (post-build) ---
                                  10. Target-match check               (was 7)
```

Add a structural boundary marker before the agent-side step:

```markdown
**Steps 1–9 run in the CLI via `dialogue-turn`.** Step 10 runs agent-side after
`build-packet` returns.

10. **Target-match check (agent-side):** After building a packet for a scheduled
    candidate, the agent verifies the packet supports the composed follow-up target.
    ...
```

**Cross-reference update:** After renumbering, update `delivery.md` where it cites "registry.md#scheduling-rules step 7" for the target-match condition. This becomes "step 10."

- [ ] **Step 4: SY-1 — Fix scout-priority deferral condition**

In scheduling step 6 (~line 165), remove the narrow "targeting the same code boundary" qualifier. Three other sources (registry.md Failure Modes, integration.md Step 5.5, decisions.md) use the broader condition "scout target exists for turn."

Change from:
```
6. If context-injection has a scout candidate targeting the same code boundary, defer the CCDI candidate
```

To:
```
6. If context-injection has a scout candidate for the current turn, defer the CCDI candidate
   (→ `deferred` state with `scout_priority` reason).
```

- [ ] **Step 5: SY-15 — Define re-entry fields when topic absent from classifier output**

In the field update rules (~line 109), the `suppressed → detected` re-entry row references `coverage_target` and `facet` from classifier output. But a `docs_epoch` change can trigger re-entry when the topic is NOT in the current classifier output.

Add a conditional branch to the field update rule:

```
suppressed → detected (re-entry):
  If topic is present in classifier output:
    coverage_target ← classifier.coverage_target
    facet ← classifier.facet
    confidence ← classifier.confidence
  If topic is absent from classifier output (docs_epoch-triggered re-entry):
    Retain prior values for coverage_target, facet, confidence.
    Reset suppression_reason ← null, consecutive_medium_count ← 0.
```

- [ ] **Step 6: SY-5 — Add pending_facets assertion to prescriptive hint fixture**

In the semantic hints table (~line 201), the `prescriptive` hint on an `injected` topic is specified as a no-op (topic already injected, hint is informational only). The replay fixture for this case lacks a positive assertion that `pending_facets` is unchanged.

Add to the fixture specification (or reference the fixture in the semantic hints section):

```
**Replay fixture assertion:** For `prescriptive` hint on `injected` topic,
`final_registry_file_assertions` MUST include:
  - `pending_facets` array is unchanged from initial state
  - No injection or deferral mutations occur
```

- [ ] **Step 7: SY-3 (P2) — Add cross-reference for confidence:null type extension**

The scheduling rules sort candidates using `confidence` as a sort key, but `confidence: null` is a valid value (defined as a type extension in integration.md). The registry.md scheduling section does not acknowledge this dependency.

Add a note at the point of use (scheduling priority sort):

```
**Note:** `confidence` may be `null` for `pending_facet` and `facet_expansion`
candidates (see [integration.md#dialogue-turn-registry-side-effects](integration.md#dialogue-turn-registry-side-effects)
for the type extension). Null-confidence candidates sort after all non-null candidates.
```

- [ ] **Step 8: Update delivery.md step citation**

After the SY-10 reorder, find and update any delivery.md references to the old step numbers. Known reference: delivery.md cites "registry.md#scheduling-rules step 7" for the target-match condition — update to "step 10."

Run: `grep -n 'step 7\|step 8\|step 9\|step 10' docs/superpowers/specs/ccdi/delivery.md` and verify each reference.

- [ ] **Step 9: Verify cross-references**

Run:
```bash
grep -n 'registry\.md#\|data-model\.md#\|integration\.md#' docs/superpowers/specs/ccdi/registry.md
grep -n 'step [0-9]' docs/superpowers/specs/ccdi/registry.md docs/superpowers/specs/ccdi/delivery.md
```

Verify all anchors resolve and all step numbers are consistent.

- [ ] **Step 10: Commit**

```bash
git add docs/superpowers/specs/ccdi/registry.md docs/superpowers/specs/ccdi/delivery.md
git commit -m "fix(spec): remediate 8 findings in registry.md (SY-1,3,5,10,11-in,12-in,15,29)

Authority moves (from data-model.md):
- SY-11: Add 3 behavioral Failure Modes rows (deferred_ttl:0, results_file, schema_version)
- SY-12: Add consecutive_medium_count load-time validation

Scheduling restructure:
- SY-10: Reorder scheduling steps — move agent-side target-match from step 7 to step 10
- SY-29: Add CLI/agent boundary marker before agent-side target-match step

Behavioral fixes:
- SY-1: Remove 'same code boundary' qualifier from scout-priority deferral (step 6)
- SY-15: Add conditional branch for docs_epoch-triggered re-entry (topic absent from classifier)
- SY-5: Add pending_facets unchanged assertion for prescriptive hint on injected topic

P2:
- SY-3: Add cross-reference for confidence:null type extension at scheduling sort"
```

---

### Task 3: Fix integration.md — Anchor Fixes + Behavioral Specification Gaps

**Files:**
- Modify: `integration.md`

**Findings:** SY-2, SY-13, SY-14, SY-24, SY-25, SY-30

**Depends on:** Task 2 (SY-24/SY-25 anchor fixes reference sections that Task 2 may cross-reference; step numbers must be stable)

This task promotes two bold-text sections to proper headings for anchor resolution (SY-24, SY-25), resolves the facet mismatch ambiguity (SY-2), adds a missing qualifier (SY-13), specifies multi-candidate handling (SY-14), and describes the TTL reset stay-deferred branch (SY-30).

- [ ] **Step 1: SY-24 + SY-25 — Promote bold text to headings for anchor resolution**

**SY-24:** `registry.md` line ~140 links to `integration.md#dialogue-turn-registry-side-effects`, but the target is bold text (`**dialogue-turn registry side-effects:**` at ~line 45), not a heading. Convert to a heading:

Change: `**\`dialogue-turn\` registry side-effects:**`
To: `### \`dialogue-turn\` Registry Side-Effects`

**SY-25:** Same pattern. `registry.md` line ~233 links to `integration.md#build-packet-automatic-suppression`, but the target is bold text (~line 56). Convert to heading:

Change: `**\`build-packet\` automatic suppression:**`
To: `### \`build-packet\` Automatic Suppression`

Verify the generated anchors match what registry.md expects (lowercase, hyphens for spaces, backticks stripped).

- [ ] **Step 2: SY-2 — Resolve facet mismatch enforcement**

The spec says facet at commit time "MUST match" the prepare-phase facet (~line 35), but the CLI integration test (~line 301) permits two behaviors ("assert either non-zero exit... or document that the commit-phase facet is used regardless"). This `or` contradicts the MUST.

Choose non-zero exit (enforces the invariant). Update:

1. **Facet consistency paragraph** (~line 35): Keep "MUST match" wording as-is.
2. **CLI integration test row** (~line 301): Change from "assert either non-zero exit with facet mismatch error, or document that the commit-phase facet is used regardless" to: "Assert non-zero exit with descriptive error including both facet values. The prepare-phase facet is authoritative; commit-phase callers MUST provide the matching value."

Remove the "or" branch entirely.

- [ ] **Step 3: SY-13 — Add leaf-kind qualifier to consecutive_medium_count**

In the dialogue-turn side-effects section (~line 45, now a heading after Step 1), the description says: "Updates `last_seen_turn` and `consecutive_medium_count` for existing entries on re-detection."

This omits the leaf-kind restriction. Change to:
```
Updates `last_seen_turn` for all re-detected entries; increments
`consecutive_medium_count` only for **leaf-kind** entries re-detected at medium
confidence — family-kind entries leave `consecutive_medium_count` unchanged
(per [registry.md#scheduling-rules](registry.md#scheduling-rules) step 4).
```

- [ ] **Step 4: SY-14 — Specify multi-candidate turn handling**

Step 5.5 (~line 275) processes a single candidate ("the scheduled candidate's query plan"), but `dialogue-turn` can emit multiple candidates (a `new` candidate from step 7 plus a `pending_facet` from step 8, using post-reorder numbering).

Add multi-candidate specification after the Step 5.5 candidates processing:

```
**Multi-candidate turns:** When `dialogue-turn` emits multiple candidates:
- Process candidates in scheduling priority order (highest priority first).
- The per-turn cooldown (registry.md scheduling step 5) applies only to
  `candidate_type: "new"` entries. `pending_facet` and `facet_expansion`
  candidates are exempt from the cooldown and may be processed in the same
  turn as a `new` candidate.
- If multiple candidates remain after cooldown filtering, process all in
  sequence within the same turn. Each candidate gets its own search → build-packet
  → target-match cycle.
```

**Decision needed:** The above specifies "process all." Alternative: "process first-by-priority, defer rest to next turn." The report leans toward processing all since `pending_facet`/`facet_expansion` are operations on already-injected topics with low overhead.

- [ ] **Step 5: SY-30 (P2) — Add deferred→deferred TTL reset description**

In the dialogue-turn section, the `deferred → deferred` (TTL=0, topic absent from classifier output) branch is underdescribed. The topic stays deferred and the TTL resets to the configured default.

Add a note to the dialogue-turn side-effects or link to registry.md's field update rules:

```
When a deferred topic has TTL=0 and is absent from the current classifier output:
the topic remains in `deferred` state with `deferred_ttl` reset to the configured
default (see [registry.md#field-update-rules](registry.md#field-update-rules),
`deferred → deferred` row).
```

- [ ] **Step 6: Verify cross-references**

Verify new heading anchors match what registry.md expects:
```bash
grep -n 'integration\.md#' docs/superpowers/specs/ccdi/registry.md
```

Check that the newly promoted headings generate correct anchors.

- [ ] **Step 7: Commit**

```bash
git add docs/superpowers/specs/ccdi/integration.md
git commit -m "fix(spec): remediate 6 findings in integration.md (SY-2,13,14,24,25,30)

Anchor fixes:
- SY-24: Promote dialogue-turn side-effects bold text to heading
- SY-25: Promote build-packet suppression bold text to heading

Behavioral specification:
- SY-2: Resolve facet mismatch — non-zero exit enforces MUST; remove or-branch from test
- SY-13: Add leaf-kind qualifier to consecutive_medium_count update
- SY-14: Specify multi-candidate turn handling (process all, cooldown exemption for pending_facet)

P2:
- SY-30: Add deferred→deferred TTL reset stay-deferred branch description"
```

---

### Task 4: Fix delivery.md + decisions.md — P0 Verification + Test Naming + Fixture Gaps

**Files:**
- Modify: `delivery.md`
- Modify: `decisions.md`

**Findings:** SY-4, SY-8(P0), SY-9(P0), SY-19, SY-20, SY-21, SY-22, SY-23, SY-26, SY-32, SY-36, SY-37, SY-38

**Depends on:** Task 2 (delivery.md step citation already updated by Task 2 Step 8; also SY-26 may reference layer structure that Task 2's scheduling restructure clarifies)

This task fixes both P0 verification gaps (SY-8, SY-9), renames the misleading shadow-mode test (SY-4), adds five missing test/fixture specifications (SY-19, SY-20, SY-21, SY-22, SY-23), fixes a count mismatch (SY-26), and addresses three P2 gaps (SY-32, SY-36, SY-37, SY-38).

- [ ] **Step 1: SY-8 (P0) — Add validate_graduation.py test specification**

The graduation protocol (~line 107) normatively requires `validate_graduation.py` but the script has no test coverage. Add a test section after the graduation protocol:

```markdown
#### `test_validate_graduation.py`

| Test | Input | Expected |
|------|-------|----------|
| Valid graduation report | Shadow registry + active inventory with matching topics | Exit 0, report lists all matched topics |
| Missing topic in inventory | Shadow registry entry referencing topic absent from active inventory | Exit 1, error identifies missing topic |
| Coverage threshold unmet | Shadow topic with coverage below configured minimum | Exit 1, error reports coverage gap |
| TTL consistency check | Shadow entry with deferred_ttl inconsistent with active config | Exit 1, error identifies TTL mismatch |
| Empty shadow registry | No shadow entries to graduate | Exit 0, report states "no candidates" |
```

- [ ] **Step 2: SY-9 (P0) — Add test_ccdi_hooks.py specification**

The inventory tests section (~line 397) declares `test_ccdi_hooks.py` as a Phase A prerequisite but it appears nowhere in the test strategy tables. Add a named section:

```markdown
#### `test_ccdi_hooks.py`

Tests the PostToolUse hook that triggers `build_inventory.py` on `docs_epoch` change.

| Test | Setup | Expected |
|------|-------|----------|
| Hook fires on docs_epoch change | Mock PostToolUse event with `docs_epoch` field change | `build_inventory.py` invoked with updated epoch |
| Hook skips non-epoch changes | Mock PostToolUse event without `docs_epoch` change | `build_inventory.py` not invoked |
| Hook handles build failure | Mock PostToolUse + `build_inventory.py` exits non-zero | Hook logs warning, does not block tool use |

**Runner:** pytest with subprocess fixture (same pattern as CLI integration tests).
**Phase:** A prerequisite — must pass before shadow mode activation.
```

- [ ] **Step 3: SY-4 — Rename shadow mode test + update decisions.md**

**delivery.md:** In the Layer 2b Agent Sequence Tests table (~line 504), rename:
- From: "Shadow mode: zero registry mutations"
- To: "Shadow mode: no injected or deferred registry mutations"

Update the test description to: "Verifies shadow mode does not write `--mark-injected` or `--mark-deferred` to the registry. Automatic suppression (via build-packet empty-output) is permitted — `suppressed` state reflects failed lookup, not agent commitment."

**decisions.md:** In the Normative Decision Constraints table (~line 54), find the shadow mode constraint row and add the suppression exception:

Change from: "Shadow mode MUST NOT commit injections or deferrals"
To: "Shadow mode MUST NOT commit injections (`--mark-injected`) or deferrals (`--mark-deferred`). Automatic suppression via `build-packet` empty output IS permitted — it reflects classifier-driven state, not agent commitment."

- [ ] **Step 4: SY-26 — Fix "Three-Layer Approach" count mismatch**

The heading (~line 113) says "Three-Layer Approach" but the table has four rows (Layer 1: unit, Layer 2a: CLI integration, Layer 2b: agent sequence, Layer 3: replay). decisions.md also says "three-layer."

Two options:
- **(a)** Rename to "Four-Layer Approach" and update decisions.md reference.
- **(b)** Treat Layer 2a and 2b as sub-layers of Layer 2, keeping "Three-Layer" accurate (Layer 1, Layer 2, Layer 3). Clarify in the table with "Layer 2a" and "Layer 2b" sub-rows.

**Recommended:** Option (b) — Layer 2a and 2b are already named as sub-layers, so the heading is defensible if clarified. Add a parenthetical: "Three-Layer Approach (Layer 2 has two sub-layers: CLI integration and agent sequence)."

- [ ] **Step 5: SY-21 — Enumerate ccdi_trace action values**

In the ccdi_trace schema section (~line 122), the `action` field has no normative enumeration. Add:

```markdown
`action`: One of the following normative values:
| Value | Meaning |
|-------|---------|
| `classify` | Classifier pipeline executed |
| `schedule` | Topic scheduled for lookup |
| `search` | Search query executed |
| `build_packet` | Packet construction attempted |
| `inject` | Topic injected (--mark-injected committed) |
| `defer` | Topic deferred (--mark-deferred committed) |
| `suppress` | Topic suppressed (build-packet returned empty) |
| `skip_cooldown` | Topic skipped due to per-turn cooldown |
| `skip_scout` | Topic deferred due to scout priority |
```

Verify this list covers all state transitions in registry.md and integration.md.

- [ ] **Step 6: SY-19 — Add seed_medium_baseline replay fixture**

In the replay harness section (~line 399), add a fixture specification for consecutive_medium_count initialization at the serialization boundary (JSON → seed → first dialogue-turn):

```markdown
#### `seed_medium_baseline.replay.json`

Exercises seed-build initialization of `consecutive_medium_count` across the
JSON → RegistrySeed → first `dialogue-turn` boundary.

- **Initial state:** Registry file with one leaf topic in `detected` state,
  `consecutive_medium_count: 2` (pre-existing from prior session).
- **Classifier output:** Same topic at medium confidence.
- **Expected:** `consecutive_medium_count` increments to 3 (seed correctly
  preserves the counter across serialization boundary).
```

- [ ] **Step 7: SY-20 — Add deferred_ttl:0 recovery tests**

In the registry tests table (~line 189), add two test rows for the load-time recovery path:

```markdown
| deferred_ttl:0 at load, topic present in classifier | Load registry with deferred entry (TTL=0), run dialogue-turn with topic in classifier output | Entry transitions to `detected`, TTL field reset |
| deferred_ttl:0 at load, topic absent from classifier | Load registry with deferred entry (TTL=0), run dialogue-turn without topic in classifier output | Entry remains `deferred`, TTL reset to configured default |
```

- [ ] **Step 8: SY-22 — Add multi_pending_facets replay fixture**

Add fixture specification:

```markdown
#### `multi_pending_facets.replay.json`

Exercises `pending_facets` array ordering across a multi-turn pipeline.

- **Initial state:** Registry with one injected topic having
  `pending_facets: ["security", "performance"]` (two pending facets).
- **Turn 1:** `dialogue-turn` emits `pending_facet` candidate for "security."
  Agent processes it. Commit marks "security" as resolved.
- **Turn 2:** `dialogue-turn` emits `pending_facet` candidate for "performance."
- **Expected:** After Turn 1, `pending_facets: ["performance"]` (FIFO order
  preserved). After Turn 2, `pending_facets: []`.
- **Serialization check:** Registry file written after Turn 1 must preserve
  array ordering when reloaded.
```

- [ ] **Step 9: SY-23 — Specify inventory pinning mechanism**

The integration test for inventory pinning (~delivery.md integration tests section) is infeasible as written — each CLI subprocess loads inventory fresh from disk, so there's no way to "pin" an inventory version across subprocesses.

Add a specification for the pinning mechanism:

```markdown
**Inventory pinning:** The `--inventory-snapshot` flag accepts a path to a
compiled inventory file. When provided, the CLI uses this file instead of
the default inventory location, ignoring any on-disk changes during the session.
This enables testing with a known inventory state across multiple CLI invocations.

The pinning test uses `--inventory-snapshot` to load a stale inventory, then
verifies the CLI uses the pinned version rather than the on-disk current version.
```

Update the test row to reference `--inventory-snapshot` instead of the ambiguous "pinning" concept.

- [ ] **Step 10: SY-32 (P2) — Fix "Design Turn 3" attribution**

In decisions.md (~line 59), "Design Turn 3" is used to attribute the registry seed sentinel decision. This is ambiguous — there are multiple design dialogue threads.

Disambiguate: "Design Turn 3" → "Design Dialogue Turn 3 (thread: `<thread-id>` if available, or remove the turn-level attribution in favor of: "Decided during initial design dialogue; see normative constraint below."

- [ ] **Step 11: SY-36 (P2) — Assert false_positive_topic_detections invariant**

In the shadow-mode diagnostics, `false_positive_topic_detections` is described as always 0 in shadow mode (no ground truth to compare against). Add an explicit test assertion:

```markdown
| false_positive_topic_detections always 0 in shadow | Shadow mode diagnostics JSON | Assert `false_positive_topic_detections == 0` with comment: "No ground truth available in shadow mode; field reserved for Phase B active-mode validation." |
```

- [ ] **Step 12: SY-37 (P2) — Add chunk-ordering determinism test**

Add a test row for build-packet chunk ordering:

```markdown
| build-packet chunk ordering deterministic | Same input (topic, facet, search results) run twice | Assert identical chunk sequence in both outputs. Order: citations first, then summary, then verbatim snippets (per packets.md#rendering-order). |
```

- [ ] **Step 13: SY-38 (P2) — Add --source codex|user equivalence replay fixture**

Add fixture specification:

```markdown
#### `source_equivalence.replay.json`

Exercises behavioral equivalence between `--source codex` and `--source user`
invocations of `dialogue-turn`.

- **Setup:** Identical registry state and classifier output.
- **Run 1:** `dialogue-turn --source codex` — record candidates and trace.
- **Run 2:** `dialogue-turn --source user` — record candidates and trace.
- **Expected:** Identical candidate lists, identical scheduling decisions.
  The `--source` flag affects only trace metadata, not behavioral output.
```

- [ ] **Step 14: Verify cross-references**

Run:
```bash
grep -n 'registry\.md#\|integration\.md#\|data-model\.md#' docs/superpowers/specs/ccdi/delivery.md docs/superpowers/specs/ccdi/decisions.md
```

Verify renamed test does not appear under old name in any file.

- [ ] **Step 15: Commit**

```bash
git add docs/superpowers/specs/ccdi/delivery.md docs/superpowers/specs/ccdi/decisions.md
git commit -m "fix(spec): remediate 13 findings in delivery.md + decisions.md (SY-4,8,9,19-23,26,32,36-38)

P0 verification prerequisites:
- SY-8: Add validate_graduation.py test specification (5 test cases)
- SY-9: Add test_ccdi_hooks.py section with fixture format and runner

Test naming and invariants:
- SY-4: Rename shadow mode test to 'no injected or deferred mutations'; update decisions.md
- SY-26: Clarify Three-Layer heading (Layer 2 has sub-layers 2a and 2b)

Verification gaps:
- SY-19: Add seed_medium_baseline replay fixture (serialization boundary)
- SY-20: Add deferred_ttl:0 recovery tests (present + absent branches)
- SY-21: Enumerate ccdi_trace action values (9 normative actions)
- SY-22: Add multi_pending_facets replay fixture (FIFO ordering + serialization)
- SY-23: Specify --inventory-snapshot pinning mechanism for integration tests

P2:
- SY-32: Disambiguate Design Turn 3 attribution
- SY-36: Add false_positive_topic_detections always-0 assertion
- SY-37: Add build-packet chunk-ordering determinism test
- SY-38: Add --source codex|user equivalence replay fixture"
```

---

### Task 5: Fix classifier.md, foundations.md, packets.md — Single-File P2 Fixes

**Files:**
- Modify: `classifier.md`
- Modify: `foundations.md`
- Modify: `packets.md`

**Findings:** SY-27, SY-28, SY-31

**Depends on:** Nothing (independent)

Three minor P2 fixes in files with a single finding each.

- [ ] **Step 1: SY-27 — Restructure classifier.md mid-dialogue threshold row**

In the Injection Thresholds table (~line 85), the mid-dialogue row describes registry scheduling behavior ("1 medium-confidence leaf in 2+ consecutive turns") that belongs to `registry-contract` authority.

Restructure the row to describe only classifier output. Change from:
```
Mid-dialogue | 1 medium-confidence leaf in 2+ consecutive turns (governed by
               the registry scheduling layer — see registry.md#scheduling-rules
               step 4; config key: injection.mid_turn_consecutive_medium_turns)
```

To:
```
Mid-dialogue | Medium-confidence leaf topic in classifier output. Injection
               governed by registry scheduling (see [registry.md#scheduling-rules](registry.md#scheduling-rules)
               step 4 for consecutive-turn threshold).
```

Remove the "2+ consecutive turns" threshold value from classifier.md — it is a registry scheduling parameter.

- [ ] **Step 2: SY-28 — Separate rationale from normative assertion in foundations.md**

In the CLI/Agent Separation section (~line 43), the "Boundary rule" paragraph blurs rationale with an interface constraint.

Change from:
```
The prepare/commit protocol (integration.md#...) exists because of this separation —
the agent must confirm send success before instructing the CLI to commit state.
```

To:
```
The prepare/commit protocol (integration.md#...) exists because of this separation —
ensuring injection is only registered after delivery.
See [integration.md#mid-dialogue-phase-per-turn-in-codex-dialogue](integration.md#mid-dialogue-phase-per-turn-in-codex-dialogue)
for the protocol's behavioral definition.
```

This keeps the architectural rationale in foundations.md but moves the normative interface detail ("agent must confirm send success") to where it's already defined: integration.md.

- [ ] **Step 3: SY-31 — Align packets.md section title with enum**

The section (~line 39) is titled "Verbatim vs Paraphrase" but the actual mode enum value is `"snippet"`, not `"verbatim"`. Align the heading:

Change: `## Verbatim vs Paraphrase`
To: `## Snippet vs Paraphrase`

Or, if "Verbatim" is the human-readable concept and "snippet" is the enum value, add clarification:
`## Verbatim vs Paraphrase (mode: \`snippet\` | \`paraphrase\`)`

**Decision needed:** Check whether `snippet` and `verbatim` are used interchangeably elsewhere. If "verbatim" appears in other spec files as the mode value, this is a deeper inconsistency.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/ccdi/classifier.md docs/superpowers/specs/ccdi/foundations.md docs/superpowers/specs/ccdi/packets.md
git commit -m "fix(spec): remediate 3 P2 findings in classifier, foundations, packets (SY-27,28,31)

- SY-27: classifier.md — remove registry scheduling threshold from injection table
- SY-28: foundations.md — separate architectural rationale from interface constraint
- SY-31: packets.md — align section title with snippet enum value"
```

---

## Summary

| Task | File(s) | Findings | Commit |
|------|---------|----------|--------|
| 1 | data-model.md | 7 P1 + 3 P2 = 10 | Authority moves out + schema validation |
| 2 | registry.md (+delivery.md citation) | 6 P1 + 2 P2 = 8 | Authority moves in + scheduling restructure |
| 3 | integration.md | 5 P1 + 1 P2 = 6 | Anchor fixes + behavioral spec |
| 4 | delivery.md + decisions.md | 2 P0 + 8 P1 + 3 P2 = 13 | P0 verification + test naming + fixtures |
| 5 | classifier.md, foundations.md, packets.md | 3 P2 = 3 | Single-file authority precision |
| **Total** | **8 files** | **2 P0 + 23 P1 + 13 P2 = 38** | **5 commits** |

## Decisions Required During Execution

Three findings surface design decisions that the remediation plan cannot resolve unilaterally:

| Finding | Decision | Recommended | Alternative |
|---------|----------|-------------|-------------|
| SY-16 | Should TopicRecord require non-empty aliases, or should add_topic allow empty? | Constrain TopicRecord (unsearchable topics are useless) | Relax add_topic (allow scaffold topics) |
| SY-14 | Process all candidates per turn, or first-by-priority? | Process all (pending_facet/facet_expansion are lightweight) | First only (simpler, consistent cooldown) |
| SY-31 | Rename heading to "Snippet" or clarify "Verbatim" is the concept? | Parenthetical clarification (preserves prose readability) | Full rename to match enum |

If not resolved before execution, use the recommended option and note the decision in the commit message.
