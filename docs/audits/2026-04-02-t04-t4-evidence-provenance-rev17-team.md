# Design Review Report: T4 Scouting Position and Evidence Provenance

**Target:** `docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` (rev 17, 2253 lines)
**Date:** 2026-04-02
**Review type:** Team (6 reviewers)
**Scope:** Subsystem | Archetypes: Data pipeline + Financial/regulated | Stakes: High

---

## 1. Review Snapshot

| Metric | Value |
|--------|-------|
| Raw findings | 28 |
| Canonical findings | 22 (14 P1, 8 P2) |
| Duplicate clusters merged | 4 |
| Corroborated (multi-reviewer) | 4 |
| Contradictions | 0 |
| Tensions mapped | 3 |
| Reviewers completed | 6/6 |

**Coverage assessment:** All 8 categories reviewed. 4 at primary emphasis (Behavioral, Data, Reliability, Trust & Safety), 1 at secondary (Change), 2 at background (Structural, Cognitive). No categories suppressed.

**Overall:** The core architecture is sound — no P0 findings, no structural critiques of the scouting loop, evidence model, or provenance chain design. All 14 P1 findings are about **specification gaps at contract boundaries**: underspecified wire formats, missing validation rules, unguarded configuration defaults, and absent lifecycle policies for edge cases (concession, crash, degradation). These are the expected finding class for a rev 17 design approaching acceptance — the architecture holds, the boundary contracts need tightening.

---

## 2. Focus and Coverage

| Category | Reviewer | Emphasis | Status | Findings |
|----------|----------|----------|--------|----------|
| Structural | structural-cognitive | background | deep (2 lenses) | SC-1, SC-2 |
| Cognitive | structural-cognitive | background | screened | SC-3 |
| Behavioral | behavioral | primary | deep (5 lenses) | BH-1 through BH-5 |
| Data | data | primary | deep (5 lenses) | DA-1 through DA-7 |
| Reliability | reliability-operational | primary | deep (4 lenses) | RO-1 through RO-4, RO-6 |
| Operational | reliability-operational | background | screened | RO-5 |
| Change | change | secondary | deep (4 lenses) | CH-1 through CH-4 |
| Trust & Safety | trust-safety | primary | deep (5 lenses) | TS-1 through TS-3 |

**Per-reviewer summary:**
- **structural-cognitive:** 3 findings. Boundary Definition surfaced two schema-level gaps (residual_reason nullability, detail field typing). Cognitive check found one legibility gap (Phase 1 dead-referent path). Clean on Purpose Fit, Dependency Direction, Composability.
- **behavioral:** 5 findings. Correctness surfaced two genuine loopholes (sort tiebreaker, query diversity). Performance Envelope and Failure Containment each produced one characterization gap. max_evidence undefined corroborated by data and reliability reviewers.
- **data:** 7 findings. Heaviest finding density — expected for a data pipeline archetype. Four P1s at the provenance/ledger boundary, three P2s. Concession boundary is the dominant theme.
- **reliability-operational:** 6 findings. Degradation Strategy, Recoverability, Availability Model each produced a P1. Layer-2 atomicity confirmed as followup from behavioral. Configuration Clarity gap corroborates max_evidence finding.
- **change:** 4 findings. Schema versioning and testability partition are the two P1s. Extensibility and reversibility gaps are P2 documentation notes.
- **trust-safety:** 3 findings. Secret handling and scope_envelope defaults are the two P1s. Audit chain conditionality is P2 (quality-of-audit improvement).

---

## 3. Findings

### F1. Intra-phase sort tiebreaker underspecified — claim_id determinism violated

- **priority:** P1
- **lens:** Correctness
- **decision_state:** underspecified
- **anchor:** t4.md §3.1.2 (lines 248-298)
- **corroboration:** singleton (behavioral)

**Problem:** The canonical intra-phase ordering sorts by `(claim_key, status)` ascending with no tiebreaker. Two `new` claims with the same `claim_key` but different texts (merger inapplicable — different truth conditions) sort to the same position. Their relative order determines `occurrence_index` and `claim_id` allocation. The spec asserts determinism "from text content" but the sort key does not include `claim_text`.

**Impact:** Non-deterministic `claim_id` allocation across reruns of the same transcript. Directly violates the §3.4 determinism guarantee and breaks `claim_provenance_index` reproducibility.

**Recommendation:** Add `claim_text` as tertiary sort key: `(claim_key, status, claim_text)`. Merger already prevents identical `(claim_key, claim_text)` among live occurrences, so this produces a total order. Update verification item 64.

---

### F2. Falsification query diversity check allows mandatory types to be reused

- **priority:** P1
- **lens:** Correctness
- **decision_state:** explicit decision
- **anchor:** t4.md §4.4 (lines 850-858)
- **corroboration:** singleton (behavioral)

**Problem:** Second-attempt diversity requires "at least one query in round 2 MUST differ from ALL queries in round 1." An agent can reuse identical definition AND falsification queries, adding only a novel supplementary query. The formal criterion is satisfied without any new investigative direction on the mandatory query types.

**Impact:** The loophole defeats the stated purpose — a second attempt on an ambiguous/conflicted claim with the same core queries produces the same evidence. The adjudicator has no mechanical signal.

**Recommendation:** Tighten to type-aware diversity: at least one `definition` or `falsification` query in round 2 MUST differ from all `definition`/`falsification` queries in round 1. Supplementary queries don't count. Update verification item 18 and §7.34.

---

### F3. ClassificationTrace residual_reason nullability rule not schema-encoded

- **priority:** P1
- **lens:** Boundary Definition
- **decision_state:** underspecified
- **anchor:** t4.md §4.7 (lines 1005-1035)
- **corroboration:** singleton (structural-cognitive)

**Problem:** Schema declares `residual_reason: str | null`. Prose says: "null only when `subclaims_considered` is non-empty and explains itself." This conditional-required rule is not encoded in the schema type. A validator reading only the type silently accepts `{decomposition_attempted: true, subclaims_considered: [], residual_reason: null}` — a trace the prose says is invalid.

**Impact:** Undermines decomposition audit: adjudicator sees empty subclaims with no explanation, indistinguishable from a meaningful trace.

**Recommendation:** Add explicit invariant alongside schema: "`residual_reason` MUST be non-null when `subclaims_considered` is empty."

---

### F4. Methodology finding detail field is untyped and per-kind unstructured

- **priority:** P1
- **lens:** Boundary Definition
- **decision_state:** underspecified
- **anchor:** t4.md §6.2 (line 1564)
- **corroboration:** singleton (structural-cognitive)

**Problem:** The methodology finding row schema includes `detail` with no type, format, or per-kind content specification. The five finding kinds likely require structurally different `detail` content (e.g., `shape_inadequacy` needs expected-vs-actual claim structure; `decomposition_skipped` needs a ClassificationTrace reference). No guidance on what T4 populates vs. T7.

**Impact:** T4 and T7 will produce incompatible `detail` structures. Audit chain for methodology findings cannot be mechanically processed if T4 emits free-text while T7 expects structured JSON.

**Recommendation:** Specify minimum `detail` content per finding kind. At minimum: (1) free-text vs. structured, (2) per-kind floor that T4 provides, (3) T7 may extend.

---

### F5. ClassificationTrace wire format example omits three required fields

- **priority:** P1
- **lens:** Schema Governance
- **decision_state:** underspecified
- **anchor:** t4.md §5.2 (lines 1126-1131), §4.7 (lines 1005-1035)
- **corroboration:** singleton (data)

**Problem:** Wire example shows `classification_trace: { candidate_entity: "module", failed_criterion: 3 }` — omitting `decomposition_attempted`, `subclaims_considered`, and `residual_reason`. Since `decomposition_attempted: false` is always a methodology finding, the omission is ambiguous: truncated illustration or pipeline-data contract?

**Impact:** T7 epilogue parser may accept entries with no decomposition record, making `decomposition_skipped` undetectable from provenance index alone.

**Recommendation:** Update wire example to show complete ClassificationTrace with all six fields. State whether pipeline-data contract requires all fields or only the three shown.

---

### F6. Concession lifecycle incompletely specified across provenance surfaces

- **priority:** P1
- **lens:** Source of Truth / Schema Governance
- **decision_state:** explicit tradeoff
- **anchor:** t4.md §3.4 (lines 446-531), §5.2 (lines 1134-1196)
- **corroboration:** related_pattern_extension (3 findings from data reviewer: DA-3, DA-4, DA-7)

**Problem:** Three related gaps at the concession boundary:
1. **Status gap:** Conceded claims' `ProvenanceEntry` is retained but has no status field — a harness navigating the join path cannot determine concession without consulting the transcript.
2. **Wire format gap:** The dense-array invariant (`claim_id == index`) requires all positions populated, but the representation of conceded slots is undefined (historical entry? tombstone? null?).
3. **Ledger policy gap:** No stated policy on whether conceded claims appear in the claim ledger. A harness expecting one-to-one coverage between ledger and provenance index will produce false positives.

**Impact:** Root cause: the concession lifecycle removes from `verification_state` and retains in `claim_provenance_index`, but the contract doesn't specify how this split presents to external consumers. The harness audit chain hits this on every run with concessions.

**Recommendation:** (a) Add `conceded: bool` flag to ProvenanceEntry or define conceded slots as typed entries, (b) specify dense-array representation for conceded positions, (c) state that conceded claims do not appear in ledger and this is expected, not a completeness violation.

---

### F7. claim_provenance_index serialization handoff to synthesis assembler unspecified

- **priority:** P1
- **lens:** Data Flow Clarity
- **decision_state:** underspecified
- **anchor:** t4.md §3.5 (lines 533-597), §5.2 (lines 1113-1267)
- **corroboration:** singleton (data)

**Problem:** The contract specifies that `claim_provenance_index` is agent working state (§3.5) and must appear in `<!-- pipeline-data -->` at synthesis (§5.2), but never names the mechanism by which agent state is serialized into synthesis output — which component, which step, what interface.

**Impact:** Integration gap between agent-owned state and synthesis-assembled output. T7 epilogue parser consumers are named but the emission step is not.

**Recommendation:** Add explicit sentence: "The agent serializes `claim_provenance_index` into `<!-- pipeline-data -->` at layer 5 synthesis composition, after all scouting rounds are complete."

---

### F8. Transcript fidelity degradation produces silent audit regime split

- **priority:** P1
- **lens:** Degradation Strategy / Auditability
- **decision_state:** explicit tradeoff
- **anchor:** t4.md §3.9 (lines 686-718), §5.3 (lines 1275-1296)
- **corroboration:** independent_convergence (RO-1 + TS-3)

**Problem:** The audit chain's authority is contingent on §3.9 transcript fidelity. Without resolution, the system degrades from "fully verifiable via mechanical diff" to "verifiable up to match_digest." The degradation is declared but produces no artifact-level signal — an auditor cannot distinguish a transcript-fidelity-compliant run from a non-compliant one without external knowledge.

**Impact:** Retroactive audit of pre-resolution runs is ambiguous. The same artifact represents either guarantee level with no distinguishing signal.

**Recommendation:** Add `transcript_fidelity_contract_resolved: bool` to `manifest.json` schema (§6.2). Runs before T7 clause lands set `false`. Audit tools surface this prominently.

---

### F9. Crash/abort recovery path has no harness detection mechanism

- **priority:** P1
- **lens:** Recoverability
- **decision_state:** underspecified
- **anchor:** t4.md §3.8 (line 684)
- **corroboration:** singleton (reliability-operational)

**Problem:** Terminal path table defines crash/abort as "Run invalid. Rerun." with no definition of: what constitutes crash vs. T1 error, how harness detects crash, whether stale state needs isolation, or who initiates rerun.

**Impact:** Automated benchmark evaluation cannot reliably distinguish completed from aborted runs. An aborted run mistakenly treated as complete contributes invalid data.

**Recommendation:** Define harness-side crash detection boundary (e.g., "run is valid iff synthesis artifact and complete `runs.json` entry both exist"). Add to §6.2 if specification belongs to T7.

---

### F10. T7 prerequisite block has no fallback owner or partial-readiness path

- **priority:** P1
- **lens:** Availability Model
- **decision_state:** default likely inherited
- **anchor:** t4.md §6.2 (lines 1534-1558)
- **corroboration:** singleton (reliability-operational)

**Problem:** Four T7 items are an atomic prerequisite block for scored runs. No fallback owner if T7 is delayed, no partial-readiness path, no escalation policy. The items are not equally critical — item 1 (narrative inventory) gates `supported_claim_rate` validity while items 2-4 gate artifact structural completeness.

**Impact:** Single-point availability gate. Any one item blocked = all scored runs blocked.

**Recommendation:** Either decompose into priority tiers (item 1 gates comparisons, items 2-4 gate artifact completeness) or explicitly document that T7 is the sole unblocking authority by design.

---

### F11. No schema versioning on wire formats with named T7 consumers

- **priority:** P1
- **lens:** Versioning & Migration
- **decision_state:** default likely inherited
- **anchor:** t4.md §3.3-§3.4
- **corroboration:** singleton (change)

**Problem:** `EvidenceRecord`, `VerificationEntry`, `ClassificationTrace`, and `ScoutStep` schemas have no version fields. Rev 9-12 each contained breaking schema changes — safe against a design doc but not against deployed T7 consumers.

**Impact:** Once T7 components exist, the same change pattern without versioning causes silent parse failures.

**Recommendation:** Add a monotonic `schema_version: int` to the two external wire formats (`claim_provenance_index`, `ClassificationTrace` in pipeline-data). Define what a version bump requires.

---

### F12. Pre-T7 testability surface unpartitioned in verification checklist

- **priority:** P1
- **lens:** Testability
- **decision_state:** default likely inherited
- **anchor:** t4.md §8 (lines 1965-2253)
- **corroboration:** singleton (change)

**Problem:** §8's 70 verification items mix pre-T7-verifiable and T7-required items with no partition marker. Items 14, 26, 55, 58, 68, 70 require harness infrastructure that doesn't exist yet.

**Impact:** T4 implementors cannot write a scoped test plan without guessing which items are in scope pre-T7.

**Recommendation:** Tag each item as "pre-T7 verifiable" vs "T7-required." Metadata on existing content, no contract change.

---

### F13. Allowed-scope secret handling has no interim constraint

- **priority:** P1
- **lens:** Data Sensitivity Classification
- **decision_state:** explicit tradeoff
- **anchor:** t4.md §4.6 (lines 924-933)
- **corroboration:** singleton (trust-safety)

**Problem:** T4 removed helper-era `redactions_applied`/`risk_signal` and assumes allowed-scope content is "safe to capture" for "curated corpora." This assumption is not enforced as a corpus pre-condition. Run transcripts are stored artifacts — secrets in `allowed_roots` appear verbatim.

**Impact:** Any corpus not carefully pre-audited leaks secrets into transcript artifacts.

**Recommendation:** Add interim pre-execution safeguard (warn/reject known secret-file patterns) and make "curated corpus" a named audit prerequisite.

---

### F14. Absent scope_envelope defaults to unrestricted — no benchmark guard

- **priority:** P1
- **lens:** Trust Boundary Integrity
- **decision_state:** default likely inherited
- **anchor:** t4.md §4.6 (lines 902-904); consultation-contract.md §6 (line 127)
- **corroboration:** singleton (trust-safety)

**Problem:** Consultation contract has backwards-compatibility default: absent `scope_envelope` = unrestricted. T4 grounds containment in `scope_envelope.allowed_roots` but doesn't specify fail-closed behavior when the envelope is absent in a benchmark run.

**Impact:** Misconfigured delegation envelope silently removes all scope enforcement. Containment checks become vacuously satisfied.

**Recommendation:** One-line addition to §4.6 or §6.2: "Benchmark runs MUST verify `scope_envelope` is present and `allowed_roots` is non-empty; absent envelope is a run-configuration error."

---

### F15. max_evidence undefined — budget gates, compression, and effort budget ungrounded

- **priority:** P2
- **lens:** Consistency Model / Retention & Lifecycle / Configuration Clarity
- **decision_state:** underspecified
- **anchor:** t4.md §3.5 (lines 567-597), §3.6 (lines 600-631), §4.2 (lines 744-749)
- **corroboration:** independent_convergence (BH-3, DA-6, RO-5 — 3 reviewers independently)

**Problem:** Both budget gates (`evidence_count >= max_evidence`, `scout_budget_spent >= max_scout_rounds`) reference undefined values. Neither `max_evidence` nor its derivation is specified. The compression-accounting table (§3.6) implies 6-8 in practice but never states this normatively. The `+2` formula tethers effort budget silently to evidence configuration.

**Impact:** Budget gates are formally correct but operationally inert. Compression tier thresholds are illustrative. Implementers must derive cap values from unspecified benchmark context.

**Recommendation:** Either define normative `max_evidence` values per task class, or explicitly delegate to benchmark contract as an external blocker with the same rigor as transcript fidelity. One knob, not two (confirm `max_scout_rounds` is always derived).

---

### F16. Layer-2 mid-phase failure produces intermediate state with no rollback

- **priority:** P2
- **lens:** Failure Containment / Recoverability
- **decision_state:** underspecified
- **anchor:** t4.md §3.1.2 (lines 245-298), §3.8 (lines 678-684)
- **corroboration:** cross_lens_followup_confirmation (BH-5 + RO-6)

**Problem:** Phase 1 mutates `verification_state` (removing conceded entries) before Phase 2 registers new claims. A mid-Phase 2 failure leaves state partially updated: some concessions applied, some registrations incomplete, `claim_id` counter partially incremented. The crash=invalid-run rule covers process termination but not recoverable validation errors.

**Impact:** Intermediate state produces non-deterministic `claim_id` allocation and silently corrupt provenance chains for all subsequent turns.

**Recommendation:** Define atomicity contract: either layer-2 is atomic (any failure rolls back to pre-turn state, treated as T1 error) or name specific acceptable partial states with continuation behavior.

---

### F17. Mechanical diff performance envelope uncharacterized for full-file reads

- **priority:** P2
- **lens:** Performance Envelope
- **decision_state:** default likely inherited
- **anchor:** t4.md §5.3 (lines 1297-1334)
- **corroboration:** singleton (behavioral)

**Problem:** Full-file reads produce full-file omission diffs with no bound on file size. The read-scope rule permits whole-file reads for presence/absence and pattern claims, which could apply to large modules. No characterization of harness performance, no size threshold, no online/offline distinction for diff computation.

**Impact:** CT-1 tension: correctness guarantee has unbounded per-record computational cost. Multiple full-file reads could produce multi-megabyte diff tables.

**Recommendation:** Add performance note to §5.3: expected file size ceiling, online vs. offline computation, storage budget for diff artifacts. Preserve the correctness property (no post-citation shrinking).

---

### F18. Phase 1 reinforced processing doesn't describe NO_LIVE_REFERENT path inline

- **priority:** P2
- **lens:** Legibility
- **decision_state:** default likely inherited
- **anchor:** t4.md §3.1.2 (lines 257-286), §3.1.1 (lines 300-330)
- **corroboration:** singleton (structural-cognitive)

**Problem:** Phase 1's `reinforced` description says "resolve referent, share ClaimRef. No state change." This applies only to successful resolution. The dead-referent path (→ Phase 1.5 reclassification) requires cross-referencing §3.1.1 and then finding Phase 1.5 separately.

**Impact:** Implementors may raise errors or silently skip claims on NO_LIVE_REFERENT.

**Recommendation:** Add branch: "If §3.1.1 returns NO_LIVE_REFERENT: defer — queued for Phase 1.5 reclassification."

---

### F19. Claim-class taxonomy closed with no documented extension blast radius

- **priority:** P2
- **lens:** Extensibility
- **decision_state:** explicit decision
- **anchor:** t4.md §4.7 (lines 935-1078)
- **corroboration:** singleton (change)

**Problem:** Three-class taxonomy is intentionally closed (§7.36, 7.46, 7.49 all close escape hatches). No extension protocol documented. Corpus calibration (§4.7) could reveal a need for a 4th class at a point where T7 consumers exist.

**Impact:** Cost of adding a new class is undocumented. Affects §3.4, §4.3, ClassificationTrace, benchmark findings, T7 schema.

**Recommendation:** Add a short blast-radius enumeration to §4.7 (documentation only, not a design change).

---

### F20. Benchmark-execution prerequisite has no amendment path for threshold errors

- **priority:** P2
- **lens:** Reversibility
- **decision_state:** underspecified
- **anchor:** t4.md §6.2 (lines 1532-1558)
- **corroboration:** singleton (change)

**Problem:** The threshold is "pinned in the versioned benchmark contract." No procedure for what happens if it's miscalibrated after initial runs — no defined process for retroactive re-evaluation of condition 5 across runs with different threshold values.

**Impact:** A threshold change invalidates cross-run comparisons with no defined handling.

**Recommendation:** Add threshold amendment procedure: specify that threshold changes invalidate condition 5 comparisons, manifest records threshold per run for retrospective re-evaluation. 2-3 sentences.

---

### F21. Evidence durability depends on transcript retention T4 doesn't own

- **priority:** P2
- **lens:** Durability
- **decision_state:** explicit decision
- **anchor:** t4.md §3.8 (lines 658-685), §3.9
- **corroboration:** singleton (reliability-operational)

**Problem:** All evidence durability routes through the transcript. If benchmark infrastructure doesn't retain complete transcripts (truncation, purge after scoring), the entire Tier 1 provenance chain is unreconstructable.

**Impact:** Post-run audit is only as durable as the transcript store, which T4 doesn't specify.

**Recommendation:** Add durability statement scoping T4's guarantees to "lifetime of a durably-retained complete transcript." Add transcript retention policy row to §6.2 blocker table.

---

### F22. ledger_claim_id vs claim_id naming inconsistency in finding row schema

- **priority:** P2
- **lens:** Source of Truth
- **decision_state:** explicit decision
- **anchor:** t4.md §6.2 (line 1564), §5.2 (lines 1218-1221)
- **corroboration:** singleton (data)

**Problem:** Finding row uses `ledger_claim_id?` as cross-reference field name. The same integer is called `claim_id` everywhere in §3.4, §5.2, claim ledger grammar, and provenance index. Naming mismatch.

**Impact:** Implementer friction. Bounded — namespaces are correctly separated conceptually.

**Recommendation:** Rename to `t4_claim_id?` or add parenthetical clarifying it's the integer from `claim_provenance_index` and `[ref:]` annotations.

---

## 4. Tension Map

### [T1] Correctness ↔ Performance (CT-1)

- **tension_id:** CT-1
- **kind:** canonical
- **sides:** Full omission surface correctness ↔ Harness computational cost
- **what_is_traded:** The anti-gaming design (full-file reads produce full-file diffs, no post-citation boundary shrinking) guarantees correctness of the omission surface. This guarantee has unbounded per-record computational cost at the harness layer for large files.
- **why_it_hid:** The correctness property is well-argued (§7.50 explicitly rejected the enclosing-scope heuristic that would have bounded cost). The performance cost is at the harness layer, not the agent layer — it doesn't affect the design contract's own scope, so it wasn't characterized.
- **likely_failure_story:** A benchmark corpus with presence/absence claims on modules of 1000+ lines produces multi-megabyte diff tables per evidence record. Harness performance degrades, audit time increases non-linearly, or diff storage becomes a constraint. The fix (narrowing the diff surface) reopens the shape-gaming exploit.
- **linked_findings:** F17
- **anchors:** side_a: t4.md §5.3 (read-scope rule, omission boundary); side_b: t4.md §5.3 (harness diff computation)
- **reviewers_involved:** behavioral

### [T2] Security ↔ Operability (CT-4)

- **tension_id:** CT-4
- **kind:** canonical
- **sides:** Trust boundary enforcement ↔ Corpus selection and operational flexibility
- **what_is_traded:** The safety dependency (allowed-scope secret handling) blocks non-curated corpus use until T7 resolves redaction/provenance interaction. This is a correct safety constraint that limits operational flexibility — no interim safeguard means either accepting the risk or restricting corpus selection.
- **why_it_hid:** The safety dependency is declared as an external blocker (visible), but the interim period between T4 implementation and T7 resolution has no guard. The "curated corpus" assumption is stated but not enforced — making it easy to miss that the assumption is load-bearing for safety.
- **likely_failure_story:** A benchmark run on a "curated" corpus that actually contains `.env` files or test fixtures with embedded tokens. Secrets appear verbatim in the transcript artifact. The artifact persists. The safety violation is discovered post-run with no mitigation path.
- **linked_findings:** F13
- **anchors:** side_a: t4.md §4.6 (allowed-scope safety dependency); side_b: t4.md §4.6 ("correct for benchmark corpora that are curated")
- **reviewers_involved:** trust-safety, reliability-operational

### [T3] Completeness ↔ Changeability (CT-3)

- **tension_id:** CT-3
- **kind:** canonical
- **sides:** Specification completeness ↔ Schema evolution cost
- **what_is_traded:** The design's high specification level (2253 lines, 70 verification items, 61 rejected alternatives, 8+ schemas) is the product of 17 adversarial revisions. Each schema field, lifecycle rule, and verification item was earned through counter-review. This completeness makes evolution expensive: revisions 9-12 each changed load-bearing schemas, and once T7 consumers exist, those changes require coordinated version bumps.
- **why_it_hid:** The adversarial review process validates each specification element individually. The aggregate change cost is less visible because no single revision feels heavy — but the total schema surface now has ~30+ fields across 8 structures with named consumers.
- **likely_failure_story:** Corpus calibration (§4.7) or benchmark execution reveals a need for a 4th claim class or a new finding kind. The change touches §3.4 status model, §4.3 target selection, §4.7 classification, ClassificationTrace, benchmark findings, T7 schema — and there's no versioning mechanism to manage the transition.
- **linked_findings:** F11, F19
- **anchors:** side_a: t4.md §8 (70 verification items, high specification); side_b: t4.md §3.3-3.4 (unversioned schemas with T7 consumers)
- **reviewers_involved:** change, structural-cognitive

---

## 5. Questions / Next Probes

1. **Should concession lifecycle be fully specified before G3 acceptance, or deferred to implementation?** F6 identifies three gaps at the concession boundary. None block the scouted provenance chain (G3's invariant), but they will block T7 harness implementation. If G3 acceptance means "T7 can start building," the concession boundary needs resolution now.

2. **Is the T7 prerequisite block intentionally atomic, or should it decompose?** F10 asks whether all four items must land together. If the narrative-claim inventory (item 1) is the hardest dependency and items 2-4 are structural completeness, a tiered delivery would unblock artifact-schema validation earlier.

3. **What is the expected max_evidence range?** F15 (corroborated by 3 reviewers) identifies this as the single most-referenced undefined parameter. The compression accounting, budget gates, and effort formula all depend on it. Is this a T4 parameter, a benchmark-contract parameter, or a per-task-class parameter?

4. **Should the verification checklist be partitioned before acceptance?** F12 asks whether implementors need the pre-T7/T7-required partition now (before starting implementation) or whether it can wait. If T4 implementation starts immediately after acceptance, the partition is needed at acceptance time.
