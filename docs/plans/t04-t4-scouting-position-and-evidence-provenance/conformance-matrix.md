---
module: conformance-matrix
status: active
normative: false
authority: supporting
---

# Conformance Matrix

Non-normative verification matrix. Each item cites one or more canonical
requirement IDs. The cited requirements are authoritative; this matrix is
a strict reference that does NOT define, reinterpret, or extend
requirements.

If an entry appears to conflict with the canonical requirement, the
requirement wins and the matrix has a bug.

| # | Refs | Verification |
|---|------|-------------|
| 1 | T4-SB-01, T4-F-01 | **Loop order:** No record for turns where `action == "conclude"` |
| 2 | T4-SB-02, T4-SM-07 | **Scout skip:** Conclude, evidence budget exhausted, effort budget exhausted, or all claims at skip priority |
| 3 | T4-SM-01 | **Occurrence registry — merger for new AND revised:** Both types checked against live occurrences. Same key + same normalized text + live → merge. Conceded occurrences excluded |
| 4 | T4-SM-01 | **Concession exception:** Conceded occurrences excluded from merger AND resolution. Reintroduction → new occurrence |
| 5 | T4-SM-01 | **No counter impact from merger:** Merged claims keep original status for T2/T3 |
| 6 | T4-SM-02 | **Forced-new reclassification:** Both `reinforced` AND `revised` with dead referent → reclassified to `new` before ANY consumer |
| 7 | T4-SM-02 | **Two-phase processing:** Phase 1 → Phase 1.5 → Phase 2. Same-turn concession + reintroduction → deterministic fresh identity |
| 8 | T4-SM-04 | **ClaimRef uniqueness:** `(turn, key, occurrence_index)` unique |
| 9 | T4-SM-03 | **Referent resolution — dead exclusion:** Filters to live candidates. No live → routed to Phase 1.5 reclassification |
| 10 | T4-SM-05 | **Evidence record structure:** `index == evidence_log` position. `claim_text` non-empty. `entity` follows grammar. Steps 2-5. Each citation has valid `source_step_index`. Total citations ≤ 5, Glob = 0. `match_digest` capped at 20 lines |
| 11 | T4-SB-04 | **Query coverage:** At least one `definition` and one `falsification` query per round |
| 12 | T4-SM-05, T4-F-04 | **Disposition from full output:** Mixed evidence → `conflicted` |
| 13 | T4-SM-05, T4-F-05 | **Polarity preservation:** `conflicted` cites both polarities |
| 14 | T4-PR-11 | **Mechanical omission diff:** Post-containment output minus citations = uncited lines. Harness computes by default. match_digest is convenience, not gate |
| 15 | T4-SM-06, T4-F-06 | **Verification derivation:** Same rule everywhere |
| 16 | T4-PR-09 | **Synthesis aggregation:** `supported` = `status == "supported"` |
| 17 | T4-SB-03, T4-F-09 | **Graduated attempt limit:** `not_found` → skip after 1. `ambiguous`/`conflicted` → skip after 2. Terminal → skip |
| 18 | T4-SB-04 | **Second-attempt queries:** MUST differ from first attempt (objective criterion) |
| 19 | T4-SM-08 | **Compression accounting (example scenario from T4-SM-08):** 6-turn → tier 2, 8-turn → tier 3 |
| 20 | T4-SM-08, T4-F-07 | **No snippet recovery:** Tier 3 uses `path:line_range`. No reads during synthesis |
| 21 | T4-SM-10, T4-F-08 | **Evidence NOT in synthesis:** No machine blocks |
| 22 | T4-SM-08 | **Evidence in transcript:** Atomic round commit (step 5e) |
| 23 | T4-SM-09 | **Pending round on interruption:** Target, steps, reason. No fabricated disposition |
| 24 | T4-SM-10 | **Error path independence:** No synthesis dependency |
| 25 | T4-SM-10 | **Crash = invalid run.** Rerun |
| 26 | T4-PR-10, T4-F-13 | **Audit chain transcript-complete.** No artifact beyond synthesis + transcript needed. Authority conditional on transcript fidelity |
| 27 | T4-CT-01 | **Scope breach:** Per-call counting, pending marker |
| 28 | T4-PR-03, T4-BD-01 | **Pipeline-data:** `scout_count` unchanged. New field: `claim_provenance_index` for claim→record join |
| 29 | T4-SB-03, T4-F-09 | **Claim-only scouting.** One-turn delay accepted |
| 30 | T4-BD-03 | **Helper-era migration.** Scouting surfaces enumerated. External blockers declared |
| 31 | T4-BD-02 | **T2/T3/synthesis input changes declared.** Forced-new reclassification for both types. Claim-history surface included |
| 32 | T4-F-13, T4-BR-02 | **Transcript fidelity — blocking external dependency.** Full dependency shape: normative clause, parseable format, operational parser and diff engine. Degradation path declared |
| 33 | T4-SM-01 | **Revised-claim merger.** Convergent revisions merge. No identical-text live collisions |
| 34 | T4-PR-01 | **`scout_outcomes` projection.** `evidence_log[i].turn == N`. `EvidenceRecord` replaces `evidence_wrapper` |
| 35 | T4-CT-02, T4-CT-03, T4-CT-05 | **Direct-tool containment.** Pre-execution confinement grounded in `scope_envelope`. Post-containment capture. Safety violation on leak. Allowed-scope safety declared as external blocker |
| 36 | T4-SB-05, T4-SM-06 | **Claim-class scope.** Scoutable, relational-scoutable, `not_scoutable`. Terminal status. All registration paths. Objective criteria. Adjudicator audit |
| 37 | T4-PR-02, T4-PR-03, T4-PR-05 | **Synthesis→record join.** `claim_provenance_index` keyed by `claim_id`. Two variants. Claim ledger `[ref: N]` annotations |
| 38 | T4-SM-09 | **Abandoned-round accounting.** Any round executing ≥1 tool call increments `scout_attempts` |
| 39 | T4-SB-04 | **Round budget.** 2-5 tool calls per round. Minimum 2. Hard cap 5 |
| 40 | T4-BR-01 through T4-BR-09 | **External blockers declared.** T5 migration, transcript fidelity, provenance consumer, safety, narrative inventory — all named with owners |
| 41 | T4-PR-10, T4-F-13 | **Authority claims conditional.** Contingent on transcript fidelity. Without it, audit degrades to evidence-block level |
| 42 | T4-SM-07 | **Two budget surfaces.** Evidence: `evidence_count >= max_evidence`. Effort: `scout_budget_spent >= max_scout_rounds`. `max_evidence` under benchmark change control. Single increment at step 5b |
| 43 | T4-SB-05, T4-PR-09 | **`not_scoutable` synthesis policy.** MUST appear in scored synthesis. Cannot suppress via classification. Adjudicator scores independently |
| 44 | T4-CT-02, T4-CT-03 | **Containment source.** `scope_envelope` from consultation contract (immutable). NOT benchmark tool-class restriction |
| 45 | T4-PR-06, T4-BR-06 | **Ledger completeness.** MUST — synthesis-contract violation if missing. Enforcement deferred to T7. Benchmark runs blocked until operational. NOT a G3 concern |
| 46 | T4-SM-06, T4-SB-05 | **`not_scoutable` across all registration paths.** New, revised, forced-new, reintroduction all have scoutable/`not_scoutable` split |
| 47 | T4-SM-07 | **Single increment point for `scout_budget_spent`.** Step 5b only. NOT in lifecycle entries |
| 48 | T4-BR-05 | **Synthesis-format contract updates declared.** Claim ledger grammar, atomic line rule, `not_scoutable` in trajectories — all named with owner and target |
| 49 | T4-SM-06, T4-SM-02 | **`claim_id` allocation deterministic.** After Phase 1.5 and Phase 2 merger resolution. Merged claims reuse. Same transcript → same IDs |
| 50 | T4-PR-04 | **Two provenance tiers.** Scouted: full mechanical chain. Not_scoutable: classification provenance. Deterministic-audit guarantee scoped to Tier 1 |
| 51 | T4-PR-03 | **`claim_provenance_index` replaces `evidence_map`.** Keyed by `claim_id`. Dense JSON array. Two explicit variants. All allocated IDs persist |
| 52 | T4-PR-05 | **Atomic claim ledger lines.** One `FACT:` line = one atomic factual claim. One `[ref: N]` per line |
| 53 | T4-PR-03 | **Parse-safe `[ref:]` annotation.** `[ref: N]` where N is integer `claim_id`. No embedded claim text |
| 54 | T4-PR-11 | **Per-tool omission relevance.** Grep: all matches. Read (range): all requested lines. Read (full file): all lines. Glob: none |
| 55 | T4-PR-12 | **Read-scope rule.** Anchored to query result, entity span, or justified whole-file class. Under-reading is methodology finding |
| 56 | T4-SB-04 | **Claim-shape adequacy.** Query-type quota is necessary but not sufficient. Shape-inadequacy is methodology finding |
| 57 | T4-SM-05, T4-SB-05 | **Structured non-authoritative audit fields.** ScoutStep and ClassificationTrace fields. All explicitly non-authoritative |
| 58 | T4-SB-05 | **Decomposition analysis (MUST).** Agent MUST perform check before `not_scoutable`. Records in ClassificationTrace. `false` is always finding. MUST NOT register subclaims |
| 59 | T4-SB-05 | **Corpus calibration.** `not_scoutable` rate validated via dry run. Report by task ID. Tighten criteria if material fraction unprovenanced |
| 60 | T4-PR-06, T4-BR-07 | **Narrative-claim enforcement.** Every scored factual claim MUST have ledger entry. Narrative-only = synthesis-contract violation. Runs blocked until T7. NOT G3 |
| 61 | T4-PR-05 | **Checkpoint taxonomy outcome-based.** Tags: RESOLVED, UNRESOLVED, EMERGED. Evidence state is `[evidence:]` annotation. Axes orthogonal |
| 62 | T4-PR-03 | **`claim_provenance_index` wire format canonical.** Dense JSON array. `claim_id == index`. Length == `next_claim_id`. No sparse IDs. Conceded persist |
| 63 | T4-PR-11 | **Full-file read omission = full file.** No post-citation shrinking. Boundary at read time. Closes shape-gaming exploit |
| 64 | T4-SM-02 | **Canonical intra-phase ordering.** `(claim_key, status, claim_text)` ascending. Makes `claim_id` deterministic from text content |
| 65 | T4-PR-08 | **G3 satisfied by Tier 1 scouted provenance.** EvidenceRecord → provenance index → [ref:] → transcript. Narrative coverage NOT G3 |
| 66 | T4-PR-05 | **Claim ledger separate from checkpoint.** Different surfaces, different grammars, different purposes |
| 67 | T4-BR-06 | **Coverage metric downstream of inventory.** Cannot be defined independently. Single mechanism: T7 inventory |
| 68 | T4-BR-09, T4-SB-04, T4-SB-05, T4-PR-13 | **Methodology findings.** Five kinds. Keyed by `inventory_claim_id`. Do not change claim labels. Threshold gate as condition 5. T7 owns adding to benchmark contract |
| 69 | T4-BR-01 | **Mode-mismatch failure artifact.** `agent_local` with missing T5 surfaces → invalid-run entry in `runs.json`. Benchmark behavior |
| 70 | T4-BR-07, T4-BR-08 | **Benchmark-execution prerequisite.** All runs require `scope_envelope`. Scored runs blocked until all 8 T7 dependencies. Exploratory shakedowns permitted (non-evidentiary). Policy-influencing calibration requires all 8. Independent of G3 |
