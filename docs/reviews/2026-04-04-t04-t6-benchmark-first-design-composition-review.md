# T-04 T6: Benchmark-First Design Composition Review

**Scope:** T6 asks whether the five accepted gate designs (T1-T5) compose into a single coherent state model, loop structure, and synthesis contract (`benchmark-first-design-plan.md:39`). If they do not, the conflicting gates are reopened (`benchmark-first-design-plan.md:52`). The T7 ticket additionally requires T6 to record whether benchmark-v1 coverage remains adequate under the constrained corpus (`t7-conceptual-query-corpus-design-constraint.md:113-114`, acceptance criterion 4 at `:125`).

### State Model: COMPOSES

T4's `occurrence_registry` is parallel to T3's `prior_registry` by explicit design (T4-F-03). T2's `claim_source` exclusion from T4's evidence model is declared (T4-SM-06 lifecycle). T1's `ControlDecision` is consumed read-only by T4. No circular dependencies, no dual-write conflicts, no incompatible shapes.

**T3/T4 identity boundary.** The hardest shared-state surface is T3 referential validation feeding into T4 claim-identity allocation. T3 validates referential claims by checking `referent_text` presence and `referent_key` membership in `prior_registry` (`t3:171-183`). T3 reclassifies to `new` only when `referent_text` is null or `referent_key` is absent from `prior_registry`. When the referent was conceded but the key remains in `prior_registry`, T3 accepts the claim — the no-live-occurrence check belongs to T4-SM-03 (`state-model.md:141-153`), which routes to Phase 1.5 forced-new reclassification (`state-model.md:89-97`). T4 handles all paths through Phase 1.5 and the lifecycle table:

| Case entering T4 | T4 lifecycle path | Identity outcome |
|---|---|---|
| Dead referent after T3 acceptance (scoutable) | Phase 1.5 reclassifies to `new`, then allocates new `claim_id`, new `ClaimRef`, new `unverified` entry (`state-model.md:387`) | Fresh identity; dead referent's entry already removed by concession (`:389`) |
| Dead referent after T3 acceptance (not scoutable) | Phase 1.5 reclassifies to `new`, then allocates new `claim_id`, new `ClaimRef`, new `not_scoutable` entry (`state-model.md:388`) | Fresh identity; terminal |
| Reinforced (live referent) | Shares referent's `ClaimRef`, no new entry (`state-model.md:386`) | Shared identity with referent |
| Revised (live referent, merged) | Reuses existing `claim_id`, shares `ClaimRef` (`state-model.md:382`) | Shared identity |
| Revised (live referent, new occurrence) | Allocate new `claim_id`, new `ClaimRef`, new entry (`state-model.md:380`) | Fresh identity |

**Conceded-referent path (referential claims).** When a claim is conceded, T4 removes its entry from `verification_state` but the occurrence stays in the registry (`state-model.md:389`). T3's `prior_registry` still contains the conceded claim's `referent_key`, so a subsequent `reinforced`/`revised` claim referencing it passes T3's referential validation. But T4-SM-03 referent resolution filters to live occurrences only (`state-model.md:141-144`). If all matching occurrences are conceded, resolution returns `NO_LIVE_REFERENT` (`state-model.md:149-153`), routing the claim to Phase 1.5 forced-new reclassification (`state-model.md:89-97`). The claim enters Phase 2 as `new` with a fresh `claim_id`. This is the same forced-new path as the dead-referent rows in the table above — T3 acceptance and T4-SM-03 dead-referent exclusion compose correctly.

**Reintroduction after concession (separate mechanism).** The lifecycle rows at `state-model.md:390-391` handle a different case: a `new` extracted claim whose normalized text matches a previously conceded occurrence. Phase 2 registration sees the conceded occurrence but excludes it from merger (`state-model.md:389`: "excluded from merger and resolution"). The result is a new occurrence with "concession exception" treatment — new `claim_id`, new `ClaimRef`, fresh verification entry. This path does NOT go through T4-SM-03 or Phase 1.5; it is a Phase 2 registration edge case for re-extraction, not for referential claims with dead referents.

**Ordering guarantee.** `claim_id` allocation happens AFTER Phase 1.5 reclassification AND Phase 2 merger resolution (`state-model.md:323-324`). Phase 1.5 reclassification changes claim status before ANY consumer sees it — T2 counters, T3 registry, and synthesis trajectory all see the reclassified status (`state-model.md:131-134`). No consumer can observe a pre-reclassification state paired with a post-reclassification `claim_id`.

No gates need reopening.

### Loop Structure: COMPOSES

The per-turn loop (T4-SB-01, `scouting-behavior.md:15-31`) is correctly ordered: extract → validate/register → counters → control decision → scout → compose → send. The dual budget system (turn budget via T1, evidence/effort budgets via T4-SM-07) has independent counters checked at different points with no interaction conflict. Phase 1.5 reclassification (T4-SM-02) feeds back into T2/T3 consumers as a declared input change (T4-BD-02) before T1's control decision at step 4.

**Scope-breach mid-round exit.** Four authoritative specs compose into a coherent control flow:

| Step | Authority | Behavior |
|---|---|---|
| Detection | T4-CT-01:23 (`containment.md:23`) | Per-call counting. N out-of-scope results from one call = 1 breach |
| Threshold | T4-CT-01:30 (`containment.md:30`) | `scope_breach_count >= 3` mid-round triggers exit |
| Immediate stop | Consultation contract §6 (`consultation-contract.md:131-132`) | "Stop the consultation immediately" |
| State capture | T4-SM-09 (`state-model.md:516-527`) | Emit pending-round marker: target, steps completed, abandonment reason |
| Termination | T4-CT-01:30 → T1 | T1-format termination with `termination_reason: scope_breach` |
| Synthesis | Consultation contract §6 (`consultation-contract.md:133`) | Phase 3 synthesis with `scope_breach` in pipeline-data epilogue |

The prior draft omitted the consultation contract, which resolves the top-level ambiguity. The consultation contract specifies immediate stop on scope breach. The per-turn loop's interrupt point is between tool calls during step 5b — scope-breach detection fires post-execution (`containment.md:23`), and "stop immediately" means the next tool call does not execute. Steps 5c-5e are skipped (round interrupted before evidence record creation — T4-SM-09's trigger condition). Steps 6-7 are skipped. Pending-round marker is emitted. Termination proceeds.

**Attempt accounting is consistent.** `scout_budget_spent` increments at step 5b on the first tool call executed (`state-model.md:452-453`), before any breach can be detected. An interrupted round still consumed one increment. Both completed and abandoned rounds count (`state-model.md:455`). `max_scout_rounds = max_evidence + 2` allows up to 2 abandoned rounds per run (`state-model.md:457-458`). `scout_attempts` for the target claim increments for any round executing at least one tool call (`state-model.md:534-536`).

**Terminal paths are consistent.** T4-SM-10 (`state-model.md:568-573`) defines four terminal paths. Scope breach mid-round produces "Pending-round marker + prior committed rounds." This matches T4-SM-09's pending-round emission followed by committed evidence blocks from prior rounds.

No gates need reopening.

### Synthesis Contract: DOES NOT YET COMPOSE

T4's synthesis extensions are:

| Extension | Kind | Declared Where |
|---|---|---|
| `scout_outcomes` entries → `EvidenceRecord` | Breaking migration | T4-BD-01, T4-PR-01 |
| `claim_provenance_index` in `<!-- pipeline-data -->` | Additive field | T4-BD-01, T4-PR-03 |
| `## Claim Ledger` section | Additive section | T4-BD-02, T4-PR-05 |
| `not_scoutable` in trajectory vocabulary | Enum expansion | T4-BD-02, T4-BR-05 |
| `agent_local` mode value | Enum expansion | T5 §6 Primary Migration Set |

These extensions are compatible — no field conflicts, no semantic contradictions. T4-BD-01 and T4-BD-02 explicitly declare what changes and what doesn't. No gate needs reopening.

**But the accepted design is not yet consolidated into one synthesis contract.** The contract is split across two documents:

| Document | What it specifies |
|---|---|
| `dialogue-synthesis-format.md` (current consumer-facing synthesis contract) | 7 assembly sections, checkpoint grammar, `server_assisted\|manual_legacy` epilogue |
| T4 spec tree (`provenance-and-audit.md`, `boundaries.md`, `state-model.md`) | `EvidenceRecord` schema, `claim_provenance_index` wire format, `## Claim Ledger` grammar, `not_scoutable` |

T6's done-when requires "one consistent benchmark-first design" (`benchmark-first-design-plan.md:39`). Two compatible documents describing different surfaces of the same contract is not one consistent contract.

**The split creates concrete failure paths.** `event_schema.py:137` rejects `agent_local`. `SKILL.md:435` falls back to `server_assisted`. Current consumers either ignore the new surfaces or coerce the new vocabulary. These are live invalid-run paths: the T6 consolidation artifact addresses the specification gap (what the synthesis contract says); the consumer-code changes (`event_schema.py`, `SKILL.md`, test fixtures) are T7 executable-slice work defined by T5's Primary Migration Set (`t5:195-206`, 7 surfaces across normative contract, schema, producer contract, and test enforcement layers).

**Consolidation artifact:**

| Property | Value |
|---|---|
| **Canonical surface** | `dialogue-synthesis-format.md` — becomes the single authoritative specification of what the synthesis artifact contains |
| **Derivative surfaces** | T4 spec files (`provenance-and-audit.md`, `boundaries.md`) retain design-rationale authority but are no longer required reading for synthesis consumers |
| **Deprecation path** | None — T4 spec files remain authoritative for provenance design semantics. Only the consumer-facing synthesis specification consolidates into one document |

**Surfaces to merge:**

| Surface | Authoritative design source | Target location in `dialogue-synthesis-format.md` |
|---|---|---|
| `EvidenceRecord` schema | T4-PR-01 (`provenance-and-audit.md:15-63`) | Evidence trajectory section |
| `claim_provenance_index` wire format | T4-PR-03 (`provenance-and-audit.md:65-106`) | Pipeline-data epilogue |
| `## Claim Ledger` grammar | T4-PR-05 (`provenance-and-audit.md:121-163`) | New assembly section (8th section) |
| `not_scoutable` vocabulary | T4-BD-02 | Claim trajectory and evidence trajectory sections |
| `agent_local` mode | T5 §6 (`t5:195-206`) | Mode vocabulary and epilogue |

**Done when:** `dialogue-synthesis-format.md` specifies every surface that T4 and T5 designs require, and no consumer needs to read the T4 spec tree to know what the synthesis contains.

### Coverage Adequacy Under the Constrained Corpus

The T7 ticket requires T6 to record whether benchmark-v1 coverage remains adequate under the Path-2 constrained corpus (`t7-conceptual-query-corpus-design-constraint.md:113-114`, acceptance criterion 4 at `:125`).

**B1-B7:** Corpus-compliant as written (`dialogue-supersession-benchmark.md:81-84`). The Path-2 constraint does not change their anchor sets or gate-mechanic exercise.

**B4 (narrowed anchor set):** B4's anchors intentionally narrow the discoverable answer space for an installability audit relative to a full-repo review (`dialogue-supersession-benchmark.md:85-87`). The narrowing affects answer-space breadth but not gate-mechanic exercise — B4 still runs the full per-turn loop (T1 control, T2 counting, T3 referential, T4 scouting/evidence, T5 mode) within a narrower anchor set. Both systems operate on the same narrowed surface, preserving comparability. **Verdict: adequate for benchmark-v1.** The breadth narrowing is a known and accepted trade — comparability over breadth (`dialogue-supersession-benchmark.md:77-79`).

**B8 (anchored decomposition):** B8 is scored through a 3-path-group decomposition (`dialogue-supersession-benchmark.md:92-113`): baseline dialogue, candidate spec, candidate runtime. Each scouting step must stay anchored to one group; cross-group reasoning is allowed, cross-group target expansion is not. B8 retains the longest turn budget (8 turns) and exercises cross-root scouting — the most complex scouting structure in the corpus. **Verdict: adequate for comparability; conditional for supersession credibility.** The decomposition preserves cross-root mechanics, scope confinement, evidence budget, and the full per-turn loop — both systems face the same anchor constraints, so fairness is preserved. However, B8 can still admit structurally weak decompositions with no benchmark consequence (no `methodology_finding_threshold`, T4-BR-07 item 4) and has no decision rule for anchor inadequacy (see B8 Anchor Adequacy below). Adequacy for credibly answering the supersession question depends on those enforcement gaps being closed in T7.

**Structural coverage note:** All 8 tasks exercise the per-turn loop structurally. No task is designed to force specific edge cases (fallback-claim creation, referential failure, scope breach, budget exhaustion). Edge-case calibration is T7/T8 dry-run work — the T7 ticket asks whether the constrained corpus is adequate for benchmark-v1, not whether it forces every edge case. The Path-2 constraint does not reduce structural coverage.

**Coverage adequacy verdict: adequate for comparability; B8 supersession credibility is conditional.** The Path-2 constraint narrows B4's answer space and decomposes B8's multi-root structure without eliminating any gate mechanic from the benchmark. Comparability is preserved — both systems operate on the same constrained surfaces. B8's supersession credibility depends on T7 closing the enforcement gaps: `methodology_finding_threshold` (T4-BR-07 item 4) and anchor-adequacy decision rule.

### Scope / Comparability

**`scope_envelope` ↔ corpus anchor bridge.** The benchmark contract says primary evidence anchors define benchmark-scoped `allowed_roots` for scored runs (`dialogue-supersession-benchmark.md:147-152`). T4 containment requires `scope_envelope` with non-empty `allowed_roots` in consultation configuration for any benchmark run (`containment.md:106-118`, T4-CT-04). T4-BR-07 item 5 tracks this as an open T7 prerequisite (`benchmark-readiness.md:139`).

**This is NOT a T1-T5 composition failure.** Proof:

1. T4 specifies WHAT `scope_envelope` must contain and HOW containment uses it (`containment.md:94-100`). Internally consistent.
2. The benchmark contract specifies WHAT `allowed_roots` are — primary evidence anchor paths for each corpus row (`dialogue-supersession-benchmark.md:73-76, 147-152`). Internally consistent.
3. Path-anchor population is a direct mapping: each corpus row's listed anchors ARE the `allowed_roots`. However, T4-BR-07 item 5 subrequirements beyond path-anchor population remain open in the benchmark contract (`dialogue-supersession-benchmark.md:170-173`): named `scope_envelope` as a benchmark run parameter, `allowed_roots` equivalence for compared runs, and `source_classes` inclusion or explicit irrelevance. These are unresolved benchmark-policy specifications, not T1-T5 design gaps.
4. No change to any T1-T5 gate design is required to build this bridge.
5. T4 anticipated this gap and explicitly deferred it via T4-BR-07 item 5 (`benchmark-readiness.md:139`), alongside seven other T7 prerequisites (`benchmark-readiness.md:131-142`).

**This is T7 executable-slice work:** the benchmark harness must read corpus metadata and populate consultation configuration at setup time. The design of what goes into `scope_envelope` is specified (T4-CT-04). The design of where `allowed_roots` come from is specified (benchmark contract). The wiring is harness plumbing.

**Mode migration spans T6 and T7.** The specification gap (`agent_local` absent from `dialogue-synthesis-format.md`) is addressed by the T6 consolidation artifact. The consumer-code breakpoints (`event_schema.py:137` rejection, `SKILL.md:435` fallback) are T7 executable-slice work — T5's Primary Migration Set (`t5:195-206`) defines 7 surfaces that must accept `agent_local` (normative contract, schema, producer contract, test enforcement). T6 consolidation makes the specification consistent; T7 implementation makes the code consistent with the specification.

### B8 Anchor Adequacy

B8 is unblocked for `scope_root` determinism (Path-2 resolved the conceptual multi-root blocker). But two enforcement gaps remain:

1. **No `methodology_finding_threshold`** (T4-BR-07 item 4, T4-BR-09 row 2). A structurally weak decomposition — where scouting stays within anchors but query coverage is inadequate for the supersession question — can score as a valid run with no benchmark consequence until pass-rule condition 5 is live.

2. **No decision rule for anchor inadequacy.** If B8 results look suspect, there is no defined procedure for determining whether the cause is anchor coverage gaps vs. genuine system differences. The benchmark has Change Control for adding anchor groups (`dialogue-supersession-benchmark.md:284-294`), but no trigger condition for when to invoke it.

**T7 item: define a decision rule for B8 anchor-adequacy review — when should the benchmark operator invoke Change Control to expand B8's path groups?**

---

## T6 Verdict

| Boundary | Status | Gate action |
|---|---|---|
| State model | **Composes** | None — T3/T4 identity boundary verified |
| Loop structure | **Composes** | None — four-spec control flow coherent (consultation contract resolves ambiguity) |
| Synthesis contract | **Does not yet compose** | T6 consolidation artifact below |
| Coverage adequacy | **Adequate for comparability; B8 conditional** | B8 supersession credibility depends on T7 enforcement gaps |

**T6 disposition: T6 remains open pending synthesis contract consolidation.** No gate needs reopening — T4's extensions are compatible with the existing format, and T5's `agent_local` is a valid addition. The composition failure is that T6 has not yet produced the consolidated contract.

The governing plan provides two exit states: gates compose (done) or gates don't compose (reopen conflicting gates, `benchmark-first-design-plan.md:52`). The synthesis contract gap is not a gate conflict — no gate's design is wrong. It is incomplete T6 consolidation work: the accepted designs are compatible but have not yet been merged into the single consistent contract that T6 promises.

**T6 consolidation artifact: unified synthesis contract**

| Property | Value |
|---|---|
| Canonical surface | `dialogue-synthesis-format.md` |
| Authoritative design sources | T4-PR-01, T4-PR-03, T4-PR-05, T4-BD-01, T4-BD-02, T5 §6 |
| Surfaces to add | `EvidenceRecord`, `claim_provenance_index`, `## Claim Ledger`, `not_scoutable`, `agent_local` |
| Includes | T5 Primary Migration Set specification surfaces (`agent_local` in mode vocabulary and epilogue). Consumer-code surfaces (schema, parser, tests) are T7 implementation of this specification |
| Done when | `dialogue-synthesis-format.md` specifies all surfaces that T4 and T5 designs require; no consumer needs the T4 spec tree to know what the synthesis contains. Consumer-code acceptance of `agent_local` is T7 work per T5 §6 |
| Authority after consolidation | `dialogue-synthesis-format.md` is the single authoritative synthesis specification. T4 spec files retain design-rationale authority |

**Deferred to T7 (genuinely executable-slice work):**

1. **B8 anchor-adequacy decision rule** — define when the benchmark operator should invoke Change Control to expand B8's path groups. Benchmark execution procedure, not design composition.
2. **`scope_envelope` harness wiring** — populate consultation-layer `scope_envelope` from corpus anchor metadata at setup time. T4 specifies what `scope_envelope` must contain (T4-CT-04); T4-BR-07 item 5 explicitly defers the harness wiring to T7. No T1-T5 design change required (proof above).
