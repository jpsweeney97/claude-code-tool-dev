---
date: 2026-04-02
time: "12:49"
created_at: "2026-04-02T16:49:57Z"
session_id: 90cca67d-cf60-420d-b3e5-5e1db9c0255c
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-02_11-51_t04-t4-evidence-provenance-rev11-adversarial-review.md
project: claude-code-tool-dev
branch: docs/t04-t4-scouting-and-evidence-provenance
commit: 7b08fbcf
title: "T-04 T4 evidence provenance — revisions 12-14, claim ledger and G3 separation"
type: handoff
files:
  - docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md
  - docs/plans/2026-04-02-t04-t1-structured-termination-contract.md
  - docs/plans/2026-04-02-t04-t2-synthetic-claim-and-closure-contract.md
  - docs/plans/2026-04-02-t04-t3-deterministic-referential-continuity.md
  - docs/plans/2026-04-02-t04-t5-mode-strategy.md
  - docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md
  - packages/plugins/cross-model/agents/codex-dialogue.md
  - packages/plugins/cross-model/references/dialogue-synthesis-format.md
  - packages/plugins/cross-model/references/consultation-contract.md
  - packages/plugins/cross-model/scripts/event_schema.py
  - docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md
---

# Handoff: T-04 T4 evidence provenance — revisions 12-14, claim ledger and G3 separation

## Goal

Close gate G3 (evidence provenance retention) — the last remaining hard gate before T6 (composition check) can begin. G1, G2, G4, G5 are `Accepted (design)`. G3 requires: fixed scout-capture point, per-scout evidence record schema, synthesis citation surface. The risk register at `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md:67` governs G3.

**Trigger:** Previous session (handoff archived at `docs/handoffs/archive/2026-04-02_11-51_t04-t4-evidence-provenance-rev11-adversarial-review.md`) left revision 11 awaiting adversarial review. This session received that review and iterated through revisions 12, 13, and 14.

**Stakes:** All 5 hard gates must reach `Accepted (design)` before T6 composition check can start (`risk-register.md:79-81`). T4 is the parallel prerequisite that designs how evidence flows through the dialogue loop.

**Success criteria:** User accepts the T4 design contract. G3 moves to `Accepted (design)`.

**Pattern:** Claude drafts, user provides adversarial review with Critical/High severity ratings, specific file:line evidence, and required changes. Three review cycles completed this session (rev 11→12→13→14). Revision 14 is awaiting review.

## Session Narrative

### Rev 11 review → Revision 12: Semantic gaps in provenance story

Session began by loading the prior handoff and receiving the user's adversarial review of revision 11. The review contained 4 critical, 2 high findings. The shift from prior reviews: rev 8-10 had internal consistency issues; rev 11's review targeted **semantic gap** problems — places where the design assumed a capability (parsing, inventory, 1:1 mapping) that didn't exist and wasn't specified.

The 4 criticals were:

1. **`not_scoutable` claims had no deterministic provenance path** — the audit chain (L997) went synthesis → evidence_map → record index → evidence block, but `not_scoutable` claims have no evidence records. The chain was empty for them despite the design requiring them in scored synthesis.

2. **Checkpoint completeness didn't eliminate approximate matching** — rev 11 said "every factual narrative claim must have a checkpoint entry" but enforcing this requires inventorying factual narrative claims, which IS approximate matching. The problem was relocated, not eliminated.

3. **`[ref:]` with raw `ClaimRef` was not parse-safe** — `[ref: (3,compute_action behavior,0)]` embedded a normalized `claim_key` in tuple-like text. T3 normalization doesn't strip commas, brackets, or quotes. No escaping rules defined.

4. **Join model only handled 1:1 mapping** — synthesis naturally compresses multiple facts into one sentence but the checkpoint grammar only showed one `[ref:]` per entry.

I proposed 6 fixes. The user counter-reviewed the proposals before I edited, catching:
- C2: checkpoint-as-scored-surface creates a benchmark escape hatch (false narrative facts become unscored)
- C4: multi-ref conflates "one claim with multiple records" with "multiple claims compressed"
- C1: overloading evidence_map with ClassificationTrace mixes semantics
- C3: claim_id allocation must be normatively deterministic

Rev 12 integrated all adjusted findings (1492→1762 lines).

### Rev 12 review → Revision 13: Boundary completeness of new surfaces

User's review of rev 12 found 2 critical, 3 high. The review's character: fixes worked within T4 but the NEW surfaces introduced in rev 12 (claim_id, claim_provenance_index, read-scope rule) had their own contract problems.

Key findings:

1. **No benchmark penalty for missing checkpoint coverage** — the "bounded gap" story said missing entries weaken synthesis quality assessment, but the benchmark defines `supported_claim_rate`, `false_claim_count`, citations, safety — no checkpoint-completeness metric. A gap that's visible but not penalized is not bounded.

2. **`NOT_SCOUTABLE` as checkpoint tag mixed axes** — checkpoint taxonomy is outcome-based (RESOLVED/UNRESOLVED/EMERGED), `not_scoutable` is evidence-state-based. One tag can't describe both axes.

3. **`claim_provenance_index` had no canonical wire format** — internal dict, serialized as array, prose used direct indexing. Ambiguous.

4. **Read-scope rule contradicted itself** — said MUST be anchored, then said unanchored reads "not prohibited." Enclosing-scope heuristic chosen post-citation was exploitable.

5. **`claim_id` not fully deterministic** — no canonical intra-phase ordering before allocation. Extractor order could vary between equivalent runs.

Rev 13 fixes (1762→1881 lines):
- Upgraded narrative gap to hard G3 gate condition
- Checkpoint grammar kept outcome-based; `NOT_SCOUTABLE` tag → `[evidence: not_scoutable]` annotation
- Dense JSON array with `claim_id == index` invariant
- Full-file reads get full-file omission surface (no post-citation shrinking)
- Canonical `(claim_key, status)` ascending sort before each phase

### Rev 13 review → Revision 14: Structural separation of concerns

User's review of rev 13 found 2 critical, 3 high. The review's character: the design was "mostly honest" about the gap but had **structural failures in the closure story**.

Key findings:

1. **`checkpoint_coverage_rate` depends on the same checker machinery** — presented as alternative to T7 inventory, but the metric computes `checkpoint_factual_claims / total_factual_claims`, which requires enumerating `total_factual_claims` — which IS the inventory problem. False disjunction.

2. **Checkpoint asked to serve two incompatible jobs** — outcome summary (RESOLVED/UNRESOLVED/EMERGED) AND atomic factual claim inventory (one line per repo fact with [ref:]). Many repo facts are supporting observations, not dialogue outcomes. Agents either jam facts into `RESOLVED` inappropriately or leave them in narrative.

3. **Stale "bounded by incentives" language** — §5.3 still said gap was bounded, while §5.2 said it was a hard G3 blocker. Internal contradiction.

4. **Coverage metric allowed to be diagnostic-only** — a diagnostic metric creates no contract penalty.

5. **G3 gate definition drift** — G3's invariant is "accepted scout results retained as structured provenance." Stretching it to cover unscouted narrative claims is gate-definition drift.

Rev 14's structural breakthrough was **three separations** (1881→1916 lines):
- **G3 vs narrative coverage:** G3 is about scout provenance (T4 solves internally). Narrative coverage is a separate synthesis quality concern for T7
- **Checkpoint vs claim ledger:** New `## Claim Ledger` section with `FACT:` lines for provenance. Checkpoint stays outcome-based (unchanged from synthesis-format contract)
- **Coverage metric vs inventory:** The metric IS the inventory's output. Single mechanism: T7 delivers inventory; metric is downstream

## Decisions

### Introduce `claim_id: int` as parse-safe join key (rev 12)

**Choice:** Add `claim_id: int` to `VerificationEntry`, auto-incremented at registration. `[ref: N]` replaces `[ref: (turn,key,idx)]`.

**Driver:** User's rev 11 review finding C3: `claim_key` can contain commas, brackets, quotes after T3 normalization — `[ref: (3,compute_action behavior,0)]` has no escaping rules and is not parse-safe.

**Rejected:** Text-embedded `ClaimRef` tuple (rev 10-11) — structurally fragile, no round-trip guarantee.

**Implication:** All provenance surfaces now use integer join keys. `ClaimRef` retained for internal registry/lifecycle, `claim_id` for external surfaces.

**Trade-offs:** Adds a field to `VerificationEntry` and requires deterministic allocation order.

**Confidence:** High (E2) — integer parsing is unambiguous. Allocation determinism guaranteed by canonical intra-phase ordering.

**Reversibility:** Low — `claim_id` is embedded in provenance entries, claim ledger annotations, and the harness join path.

**Change trigger:** None — replacing text-embedded tuples with integers is unconditionally better.

### Two-tier provenance model (rev 12)

**Choice:** Separate `claim_provenance_index` with explicit `scouted` and `not_scoutable` variants replacing the overloaded `evidence_map`.

**Driver:** User's rev 11 review finding C1: `not_scoutable` claims had no provenance path despite appearing in scored synthesis. User's rev 12 counter-review finding: overloading `evidence_map` with `record_indices: []` + `ClassificationTrace` mixes evidence and classification semantics.

**Rejected:** (a) Single `evidence_map` with `not_scoutable` entries having `record_indices: []` (rev 12 proposal) — semantically muddy. (b) No provenance for `not_scoutable` claims (pre-rev 12) — leaves a hole in the audit story.

**Implication:** Deterministic-audit guarantee scoped to Tier 1 (scouted) only. Tier 2 has classification provenance (auditable, but no evidence chain). Clear about what each tier guarantees.

**Trade-offs:** Two-variant structure is more complex than a single evidence_map. Accepted because the alternatives are either semantically muddy or incomplete.

**Confidence:** High (E2) — the scouted/not_scoutable distinction is structurally real (one has evidence records, the other doesn't).

**Reversibility:** Medium — changing the provenance structure requires updating all consumers (harness, epilogue parser, checkpoint parser).

**Change trigger:** If a third provenance tier emerges (e.g., partially scoutable claims).

### Separate claim ledger from checkpoint (rev 14)

**Choice:** Introduce `## Claim Ledger` as a new synthesis section. Flat `FACT:` lines with `[ref: N]` and `[evidence:]` annotations. Checkpoint stays outcome-based (RESOLVED/UNRESOLVED/EMERGED), unchanged from synthesis-format contract.

**Driver:** User's rev 13 review finding C2: checkpoint was asked to serve two incompatible jobs — dialogue outcome summary AND atomic factual claim inventory. Many repo facts are supporting observations, not dialogue outcomes. Agents would jam facts into `RESOLVED` inappropriately or leave them in narrative prose.

**Rejected:** (a) Checkpoint as sole scored factual surface (rev 12 proposal) — buys determinism by no longer scoring narrative, creating a benchmark escape hatch. (b) Dual-purpose checkpoint with atomic lines (rev 12-13) — forces non-outcome facts into outcome grammar. (c) `NOT_SCOUTABLE` as checkpoint tag (rev 12) — mixes outcome and evidence-state axes.

**Implication:** Checkpoint contract unchanged. T7 needs to add the claim ledger section to synthesis-format. Two surfaces with clear separation of concerns. The claim ledger is where provenance lives; the checkpoint is where dialogue outcomes live.

**Trade-offs:** Adds a new synthesis section that agents must populate. More synthesis work, but each section has one job instead of two.

**Confidence:** Medium (E1) — structurally sound but untested against real synthesis assembly. Agents might under-populate the ledger under token pressure.

**Reversibility:** Medium — removing the ledger would require merging its content back into the checkpoint (re-creating the dual-purpose problem) or the narrative (losing provenance).

**Change trigger:** If agents consistently fail to populate the ledger, consider making it harness-generated from `claim_provenance_index` rather than agent-authored.

### Decouple G3 from narrative coverage (rev 14)

**Choice:** G3 is satisfied by T4's Tier 1 scouted provenance chain. Narrative coverage is a separate synthesis quality concern for T7, not a G3 gate condition.

**Driver:** User's rev 13 review finding H5: G3's invariant (`risk-register.md:35`) is "accepted scout results retained as structured provenance." Narrative-only claims are NOT accepted scout results — there are no scout results to retain. Making G3 depend on narrative coverage is gate-definition drift.

**Rejected:** (a) G3 gate condition for narrative coverage (rev 13) — stretches G3 beyond its definition. (b) `checkpoint_coverage_rate` as independent G3 option (rev 13) — the metric depends on the inventory (computing coverage requires enumerating narrative claims, which IS the inventory problem). (c) New gate G6 for narrative coverage — considered but unnecessary. Quality concern, not an invariant.

**Implication:** G3 can be accepted based on T4's internal design. The narrative coverage gap is honestly declared as a T7 dependency with no gate. T7 owns the narrative-claim inventory and any coverage metric downstream of it.

**Trade-offs:** Narrative-only claims remain unpenalized until T7 delivers the inventory. Accepted because the alternative (stretching G3 or creating a false closure mechanism) is worse.

**Confidence:** High (E2) — the G3 invariant text is clear about what it requires. T4's scouted chain satisfies it.

**Reversibility:** High — if the team decides narrative coverage needs a gate, one can be added.

**Change trigger:** If agents systematically exploit the narrative gap to hide unsupported facts, escalate narrative coverage to a gate.

### Canonical intra-phase ordering (rev 13)

**Choice:** Claims sorted by `(claim_key, status)` ascending before Phase 1 and Phase 2 processing.

**Driver:** User's rev 13 review finding H5: `claim_id` allocation was not deterministic because T2/T3 don't define intra-phase claim processing order. Extractor order could vary between equivalent runs.

**Rejected:** Relying on extractor order — non-deterministic, makes replay comparison brittle.

**Implication:** `claim_id` sequence is deterministic from claim text content. Same dialogue transcript → same `claim_id`s regardless of extractor internals. T2's raw extractor order preserved for counter computation (different concern).

**Trade-offs:** None — deterministic ordering is unconditionally better for a join key.

**Confidence:** High (E2) — `claim_key` is derived from normalized text (T3 normalization), `status` is one of a small enum.

**Reversibility:** High — the sort point can be moved without changing the rest of the design.

**Change trigger:** None.

### Full-file reads get full-file omission surface (rev 13)

**Choice:** Omission boundary determined at read time (scope the agent requested), not citation time. Full-file reads: every line is omission-relevant.

**Driver:** User's rev 13 review finding H4: the rev 12 enclosing-scope heuristic (omission boundary = enclosing scope of cited lines) was exploitable. Agent does broad read, cites narrow favorable function, boundary shrinks post-hoc.

**Rejected:** Enclosing-scope heuristic (rev 12) — boundary determined after citation selection, agent controls it via citation choice. Shape-gaming exploit.

**Implication:** Agents strongly incentivized to use targeted reads (small omission surface). `read_anchor` field records justification. Full-file reads are contract-legal but operationally expensive (massive diff surface).

**Trade-offs:** Justified whole-file reads on large files produce massive omission surfaces. Accepted because the alternative (post-citation shrinking) is exploitable.

**Confidence:** High (E2) — the exploit in the enclosing-scope heuristic is mechanically demonstrable.

**Reversibility:** Medium — changing the omission model affects the harness diff engine.

**Change trigger:** If justified whole-file reads become operationally toxic (too many false-positive omissions), consider a line-count threshold that triggers enclosing-scope scoping for reads above the threshold.

## Changes

### `docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` — T4 design contract

**Status:** Untracked (not committed). 1916 lines. Revision 14.

**Purpose:** Design contract for scouting position and evidence provenance in the T-04 benchmark-first local dialogue loop. Governs gate G3.

**Key structural changes in rev 12-14:**

*Rev 12:*
- `claim_id: int` added to `VerificationEntry` with deterministic allocation after Phase 1.5/Phase 2
- `evidence_map` replaced by `claim_provenance_index` with two variants (scouted, not_scoutable)
- `ClassificationTrace` struct for `not_scoutable` audit (structured, non-authoritative)
- `expected_contradiction_target` and `read_anchor` in `ScoutStep`
- `[ref:]` uses integer `claim_id`, not text-embedded `ClaimRef` tuple
- Checkpoint completeness relaxed from MUST to SHOULD
- Atomic checkpoint line rule: one line = one claim

*Rev 13:*
- G3 gate condition: narrative gap as hard blocker (later removed in rev 14)
- Checkpoint grammar kept outcome-based: `[evidence: not_scoutable]` annotation
- `claim_provenance_index` canonical wire format: dense JSON array, `claim_id == index`
- Full-file reads: full-file omission surface (no post-citation shrinking)
- Canonical intra-phase ordering: `(claim_key, status)` ascending

*Rev 14:*
- Claim ledger separated from checkpoint (`## Claim Ledger` with `FACT:` lines)
- G3 decoupled from narrative coverage (G3 = scouted provenance only)
- `checkpoint_coverage_rate` collapsed into T7 inventory dependency
- Stale "bounded by incentives" language removed

**Growth trajectory:** 1492 (rev 11) → 1762 (rev 12) → 1881 (rev 13) → 1916 (rev 14). Rev 12 was the largest jump (+270, new structures). Rev 14 was primarily reorganization (+35, separating concerns).

**Branch:** `docs/t04-t4-scouting-and-evidence-provenance`. Not committed.

## Codebase Knowledge

### Architecture: Evidence flow in the T-04 local dialogue loop (updated from rev 14)

| Layer | Step | Evidence interaction |
|-------|------|---------------------|
| 1 | Extract semantic data | Claims extracted from Codex response |
| 2a | Phase 1: status changes | Concessions remove from verification_state; reinforcements resolve referents. Claims sorted by `(claim_key, status)` ascending |
| 2b | Phase 1.5: reclassification | Dead-referent claims (`reinforced` AND `revised`) reclassified to `new`. Not-scoutable classification applied |
| 2c | Phase 2: registrations | Claims sorted by `(claim_key, status)` ascending. `claim_id` allocated at new entry creation. Scoutable → `unverified`. Not scoutable → `not_scoutable` (terminal, ClassificationTrace stored) |
| 3 | Compute counters | T2 counter computation (reclassified claims visible here) |
| 4 | Control decision | T1 ControlDecision — conclude/continue/scope_breach |
| 5a | Target selection | Priority: unverified(0) > conflicted(<2) > ambiguous(<2) > skip (terminal states incl. `not_scoutable`) |
| 5b | Tool execution | `scout_budget_spent += 1` here. 2-5 calls: definition + falsification mandatory. `read_anchor` recorded per Read. `expected_contradiction_target` recorded per falsification query. Post-containment capture |
| 5c | Assessment | Disposition from full post-containment output; citation selection with polarity preservation |
| 5d | Record creation | EvidenceRecord created, verification state updated, `scout_attempts += 1`, provenance index updated (record_indices appended) |
| 5e | Atomic commit | Evidence block re-emitted (captured in transcript) |
| 6 | Follow-up composition | Uses evidence record (entity, disposition, citations) |
| 7 | Send follow-up | Codex receives evidence-grounded question |

### Key contract surfaces and T4 interactions (updated)

| Surface | Location | T4 interaction |
|---------|----------|---------------|
| Follow-up evidence shape | `codex-dialogue.md:421-429` | Requires snippet + provenance + disposition + question |
| Pipeline-data scout_count | `dialogue-synthesis-format.md:150` | Maps to `evidence_count`. NOT `scout_budget_spent` |
| Pipeline-data claim_provenance_index | New (§5.2) | Dense JSON array, `claim_id`-keyed. T7 consumer |
| Evidence trajectory | `dialogue-synthesis-format.md:15` | Keys off `turn_history.scout_outcomes`. Record index included per entry |
| Claim trajectory | `dialogue-synthesis-format.md:16` | Needs `not_scoutable` in vocabulary (§6.2 blocker) |
| Claim ledger | New (§5.2) | `## Claim Ledger` section with `FACT:` lines, `[ref: N]`, `[evidence:]` annotations |
| Synthesis checkpoint | `dialogue-synthesis-format.md:126-134` | Outcome-based (RESOLVED/UNRESOLVED/EMERGED). Unchanged from synthesis-format contract |
| T2 counter computation | `t2:152-161` | `new_claims = count(status == "new")`. Forced-new reclassification feeds into this |
| Benchmark scoring | `benchmark.md:118-119` | Scores final synthesis (full, not just ledger/checkpoint) |
| Benchmark metrics | `benchmark.md:157` | `supported_claim_rate`, `false_claim_count`, citations, safety. No ledger-completeness metric |
| Scope envelope | `consultation-contract.md:127-131` | Immutable `allowed_roots` set at delegation time. Authority for containment |
| G3 invariant | `risk-register.md:35` | "accepted scout results retained as structured provenance" — satisfied by Tier 1 chain |

### Two provenance tiers

| Tier | Claims | Join chain | Guarantee |
|------|--------|-----------|-----------|
| 1 (scouted) | Claims that went through scouting | `claim_id` → `record_indices` → evidence blocks → tool output | Full mechanical chain (given transcript fidelity §3.9) |
| 2 (not_scoutable) | Claims classified not_scoutable | `claim_id` → `ClassificationTrace` → adjudicator audit | Classification provenance only. No evidence chain |
| None | Narrative-only claims | No join | No provenance. Adjudicator scores independently |

### Two budget surfaces

| Surface | Counter | Gate | Drives | Pipeline-data |
|---------|---------|------|--------|---------------|
| Evidence budget | `evidence_count` (`len(evidence_log)`) | `evidence_count >= max_evidence` | Synthesis trajectory, analytics, `scout_count` | Yes |
| Effort budget | `scout_budget_spent` | `scout_budget_spent >= max_scout_rounds` | Effort gate only | No (internal) |

### Per-tool omission relevance (rev 13)

| Tool | Omission-relevant output | Rationale |
|------|-------------------------|-----------|
| Grep | All match lines | Agent chose the query |
| Read (line_range) | All lines in requested range | Agent chose the scope |
| Read (full file) | All lines in the file | No post-citation shrinking. Boundary at read time |
| Glob | None (path list only) | No content |

### External blockers enumerated (§6.2, updated for rev 14)

| Category | Owner | Count | Key items |
|----------|-------|-------|-----------|
| T5 migration set | T5 | 5 | Mode enum, synthesis format, dialogue skill, tests |
| Transcript fidelity | T7 | 4 | Normative clause, parseable format, transcript parser, diff engine |
| Allowed-scope safety | T7 | 2 | Secret handling policy, redaction/provenance interaction |
| `claim_provenance_index` consumer | T7 | 4 | Epilogue schema, parser, schema validation, claim ledger [ref:] parser |
| Synthesis-format updates | T7 | 4 | Claim ledger section, `not_scoutable` in claim/evidence trajectory |
| Narrative-claim inventory | T7 | 3 | Inventory tool, ledger completeness checker, coverage metric (downstream of inventory) |

## Context

### Mental Model

This is a **contract convergence problem with adversarial review as the tightening mechanism**, now in a **separation-of-concerns phase**. The early revisions (8-11) fixed internal consistency. Rev 12 addressed semantic gaps. Rev 13-14 are about correctly scoping what each surface is responsible for.

**Convergence trajectory across this session:** Rev 11 review had 4 critical (semantic gaps — capability assumptions without specs). Rev 12 review had 2 critical, 3 high (new surface contract problems). Rev 13 review had 2 critical, 3 high (closure story failures and structural mismatches). Criticals are now about boundary and scope rather than design correctness — the internal architecture is stable.

**Key structural insight from rev 14:** Three things that seemed like one problem were actually three:
1. Scout provenance (G3, T4 owns) — solved by Tier 1 chain
2. Dialogue outcome tracking (checkpoint, existing contract) — unchanged
3. Factual claim inventory (narrative coverage, T7 owns) — new claim ledger + T7 dependency

### Project State

T-04 benchmark-first design plan at `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md`. 8-task dependency chain (T0-T8) with 5 hard gates (G1-G5). Critical path: T2→T3→T6→T7→T8. T4 is a parallel prerequisite for T6.

Gate status:
| Gate | Status | Contract |
|------|--------|----------|
| G1 | Accepted (design) | T1: structured termination |
| G2 | Accepted (design) | T2: synthetic claim and closure |
| G5 | Accepted (design) | T3: deterministic referential continuity |
| G4 | Accepted (design) | T5: mode strategy |
| **G3** | **Draft (rev 14 under review)** | **T4: scouting position and evidence provenance** |

## Learnings

### Gate definitions are invariants, not aspirations — don't stretch them

**Mechanism:** G3's invariant is precisely defined: "accepted scout results retained as structured provenance." Making G3 depend on narrative coverage for unscouted claims is gate-definition drift — changing what the gate means instead of what the design does.

**Evidence:** Rev 13 made narrative coverage a G3 blocker. User's review: "that is gate-definition drift, not just additional rigor... G3 can remain open even after T4 fully solves the original per-scout provenance problem."

**Implication:** When a design exceeds its gate's scope, declare the excess as a separate concern with a separate owner. Don't stretch the gate to cover it.

**Watch for:** Any gate condition that requires something the gate's invariant text doesn't mention.

### Coverage metrics depend on inventory — they can't replace it

**Mechanism:** `checkpoint_coverage_rate = checkpoint_factual_claims / total_factual_claims`. Computing `total_factual_claims` requires enumerating factual claims from narrative prose — which IS the inventory problem. The metric is downstream of the checker, not an alternative.

**Evidence:** Rev 13 offered the metric as an independent path to close G3. User's review: "the metric only makes sense if you can already enumerate narrative factual claims."

**Implication:** When proposing a metric as a closure mechanism, verify that the metric can be computed from existing data. If it requires new data, the data source is the real dependency.

**Watch for:** Metrics presented as alternatives to the machinery they depend on.

### Surfaces serving two masters need splitting, not adapting

**Mechanism:** The checkpoint was asked to be both an outcome summary and a provenance ledger. These require different grammars (outcome tags vs flat facts), different content (dialogue events vs repo assertions), and different consumers. Adapting one grammar to serve both purposes creates axis-mixing, dual-purpose edge cases, and downstream consumer confusion.

**Evidence:** Rev 12-13 tried to add `[ref:]` annotations to checkpoint lines. User's review: "many repo facts in a final synthesis are supporting observations, not dialogue outcomes... the agent either jams plain repo facts into RESOLVED lines... or leaves them narrative-only."

**Implication:** When a surface needs to serve a new purpose incompatible with its existing grammar, create a new surface rather than adapting the existing one.

**Watch for:** Annotations or state fields being added to surfaces whose existing grammar doesn't accommodate them.

### Honesty about gaps requires contractual backing, not just acknowledgment

**Mechanism:** Rev 12 said the narrative gap was "bounded by checkpoint completeness incentives." Rev 13 said it was a "hard G3 blocker." Neither worked — one was unpenalized, the other stretched G3. The honest path was: acknowledge the gap, declare it as a separate concern with a concrete owner (T7), and don't claim closure mechanisms that don't exist.

**Evidence:** Three revisions (12, 13, 14) iterating on the same gap until the right framing emerged: the gap is real, it's T7's problem, and T4 doesn't need to solve it for G3.

**Implication:** Gap acknowledgment is necessary but not sufficient. The gap needs: (1) concrete owner, (2) concrete mechanism, (3) correct scope (is it really this gate's problem?).

**Watch for:** "Bounded by incentives" language without a defined penalty mechanism.

### Omission boundaries must be fixed at read time, not citation time

**Mechanism:** If the omission boundary shrinks based on what the agent cites, the agent controls the audit surface. Cite narrowly in a broad read → contradictory lines elsewhere disappear from the diff.

**Evidence:** Rev 12 used "enclosing scope of cited lines" as the boundary. User's review: "an agent can do a broad file read, cite a narrow favorable function, and let the enclosing scope erase contradictory lines."

**Implication:** Omission relevance = what the agent asked for (read scope), not what the agent selected (citations). The agent's read request commits them to the full audit surface.

**Watch for:** Any audit boundary that can be retrospectively narrowed by agent choices.

## Next Steps

### 1. Await user's adversarial review of revision 14

**Dependencies:** None — draft is ready.

**What to read first:** The current T4 design contract at `docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` (1916 lines, revision 14). Key sections to verify:
- §3.1.2: canonical intra-phase ordering (`(claim_key, status)` ascending)
- §3.4: `claim_id` allocation rule and lifecycle table with `claim_id` annotations
- §3.5: `claim_provenance_index` ProvenanceEntry variants, `next_claim_id`
- §4.4: `expected_contradiction_target`, `read_anchor` in ScoutStep
- §4.7: `ClassificationTrace` struct, structured non-authoritative
- §5.2: claim ledger section (separate from checkpoint), provenance tiers, ledger completeness
- §5.3: per-tool omission relevance, read-scope rule (normative), G3 scope vs narrative coverage
- §6.2: all external blockers including narrative-claim inventory (NOT G3)

**Expected:** User stated "we will resume from here in a new session where I will share my review findings." If Accept → promote G3. If Reject → revision 15.

**Approach:** The convergence pattern suggests rev 14 is structurally clean. Criticals (if any) should be about boundary completeness of the new claim ledger and G3 separation, not fundamental design issues.

### 2. On acceptance: promote G3 to Accepted (design)

**Dependencies:** User accepts T4 design contract.

**What to read:** Risk register at `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md`.

**Approach:** Update G3 status. All 5 gates at Accepted (design) → T6 composition check can begin.

### 3. Consider committing the T4 design contract

**Note:** The T4 file is currently untracked on branch `docs/t04-t4-scouting-and-evidence-provenance`. 1916 lines, revision 14. Consider committing after acceptance (or before, to preserve revision history).

## In Progress

**In Progress:** T4 design contract revision 14, awaiting adversarial review.

- **Approach:** Iterative adversarial review — Claude drafts, user reviews with structured findings, Claude revises. Three review cycles this session (rev 11→12→13→14).
- **State:** Draft complete. 1916 lines. Not committed.
- **Working:** The core architecture (transcript-based evidence, single capture point, claim-only scouting, post-containment capture) has been stable since rev 6/7. The identity model (merger, concession, referent resolution, forced-new reclassification for both types) reached consistency in rev 9. The state model wiring (`not_scoutable` terminal status, two-surface budget, `claim_id`-keyed provenance) reached consistency in rev 12. The structural separation (claim ledger vs checkpoint, G3 vs narrative coverage) reached consistency in rev 14.
- **Not working / uncertain:** Whether the claim ledger will be reliably populated by agents under token pressure. Whether the `not_scoutable` classification criteria are tight enough. Whether full-file omission = full-file diff is operationally tolerable for justified whole-file reads on large files.
- **Open question:** Will the user find new boundary-completeness issues in the claim ledger / G3 separation?
- **Next action:** Wait for user's review of rev 14. Address findings if Reject. Promote G3 if Accept.

## Open Questions

1. **Will agents populate the claim ledger under token pressure?** The ledger is agent-authored. Under tight token budgets, agents may cut it first since it's a SHOULD. If this becomes systematic, consider making the ledger harness-generated from `claim_provenance_index` instead of agent-authored.

2. **Are the `not_scoutable` classification criteria tight enough?** An agent is incentivized to over-classify hard claims. The adjudicator audit mitigates this, but there's no harness-side enforcement during the run itself. The `ClassificationTrace` helps post-hoc audit but doesn't prevent misclassification.

3. **Is full-file omission operationally tolerable?** Justified whole-file reads on large files create massive omission surfaces. The `read_anchor: "whole_file"` field flags these for audit, but the adjudicator still has to process many irrelevant uncited lines. Possible mitigation: line-count threshold for enclosing-scope scoping (declared as a T7 concern).

4. **Should the T4 contract be committed before acceptance?** Currently untracked. 1916 lines. Committing preserves revision history but the file may need more revisions.

5. **Document size concern.** 1916 lines and growing. After acceptance, modular split would help. `/superspec:spec-writer` was mentioned in prior handoffs.

6. **`ClassificationTrace` is minimal for complex claims.** One `candidate_entity` and one `failed_criterion` — too lossy for relational or cross-system claims. The adjudicator still reconstructs most reasoning manually. Acknowledged as edge case, not blocking.

## Risks

### Rev 14 may still have boundary issues in claim ledger / G3 separation

The claim ledger is a new synthesis surface. The G3 decoupling changes what gate acceptance means. Both are structurally clean but untested against the user's adversarial review methodology.

**Mitigation:** The user's reviews are thorough and follow a consistent methodology. Each cycle finds fewer and more targeted issues.

### T7 dependency load is very heavy

§6.2 now has ~22 external blockers, most owned by T7. T7 owns: transcript parsing, diffing, claim_provenance_index schema, claim ledger section, narrative-claim inventory, ledger coverage metric, not_scoutable vocabulary updates. This is not a sidecar dependency — it's the missing half of the scored-synthesis contract.

**Mitigation:** The blockers are correctly identified and scoped. Some are true gating (transcript fidelity) while others can be deferred to implementation phase (claim ledger parser, coverage metric).

### 1916-line document is unwieldy

Each revision adds rejected alternatives, verification items, and rationale. The document has grown 45% across this session (1492→1916).

**Mitigation:** Post-acceptance, use /superspec:spec-writer to create a modular structure.

## References

| Document | Path | Why it matters |
|----------|------|---------------|
| T4 design contract (primary artifact) | `docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` | The artifact under review (rev 14, 1916 lines) |
| Benchmark-first design plan | `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md` | T0-T8 dependency chain, T4's position |
| Risk register | `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md` | G3 invariant (L35), gate acceptance criteria |
| Risk analysis | `docs/reviews/2026-04-01-t04-convergence-loop-risk-analysis.md` | Risks J, D, F, E details |
| T1 contract | `docs/plans/2026-04-02-t04-t1-structured-termination-contract.md` | ControlDecision, error boundary |
| T2 contract | `docs/plans/2026-04-02-t04-t2-synthetic-claim-and-closure-contract.md` | Counter computation, claim_source, extractor order (L101) |
| T3 contract | `docs/plans/2026-04-02-t04-t3-deterministic-referential-continuity.md` | Registry, normalization (L118), claim_key derivation, processing order (L157) |
| T5 contract | `docs/plans/2026-04-02-t04-t5-mode-strategy.md` | agent_local mode definition, migration set |
| Benchmark spec | `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md` | Scoring rules (L118-123), metrics (L157), safety (L145) |
| Dialogue agent | `packages/plugins/cross-model/agents/codex-dialogue.md` | Current loop, follow-up shape |
| Synthesis format | `packages/plugins/cross-model/references/dialogue-synthesis-format.md` | Checkpoint grammar (L55-65, L126-134), pipeline-data, scout_outcomes |
| Consultation contract | `packages/plugins/cross-model/references/consultation-contract.md` | scope_envelope (L127-131, immutable scope roots) |
| Event schema | `packages/plugins/cross-model/scripts/event_schema.py` | VALID_MODES (L137, still missing agent_local) |

## Gotchas

### Claim ledger is separate from checkpoint — don't conflate them

The checkpoint stays outcome-based (RESOLVED/UNRESOLVED/EMERGED). The claim ledger is fact-based (FACT: lines with [ref:]). Different grammars, different purposes, different consumers. The synthesis-format contract at `dialogue-synthesis-format.md:55-65` defines the checkpoint grammar — it's unchanged.

### G3 is about scouted provenance, not narrative coverage

G3's invariant (`risk-register.md:35`) is "accepted scout results retained as structured provenance." Narrative-only claims are NOT accepted scout results. Don't re-stretch G3 to cover them — that was the rev 13 error.

### `claim_id` allocation depends on intra-phase ordering

Claims must be sorted by `(claim_key, status)` ascending before Phase 1 and Phase 2 processing (§3.1.2). Without this sort, `claim_id` allocation is non-deterministic. T2's raw extractor order is preserved for counter computation but T4's processing order is independent.

### Coverage metric depends on the inventory

`ledger_coverage_rate` cannot be defined independently — computing coverage requires enumerating narrative claims, which IS the inventory problem. The metric is downstream of the T7 inventory, not an alternative to it.

### Omission boundary is fixed at read time

Full-file reads get full-file omission surface. No post-citation enclosing-scope shrinking. The `read_anchor` field in ScoutStep records the justification. Agents are incentivized to use targeted reads by contract consequence.

### Phase ordering matters for claim_id determinism

Within-turn claim processing order: Phase 1 (concessions/reinforcements, sorted) → Phase 1.5 (reclassification) → Phase 2 (registrations, sorted). Adding a new claim kind must update ALL three phases AND maintain the intra-phase sort.

### `ClassificationTrace` fields are non-authoritative

`candidate_entity`, `failed_criterion` are agent explanations, not proof. Same for `expected_contradiction_target` and `read_anchor` in ScoutStep. The authoritative surfaces remain: actual queries in `query`, tool outputs in transcript, mechanical diff. Audit fields reduce audit burden but are not evidence.

## User Preferences

**Review pattern:** User provides structured adversarial reviews with consistent format: Critical Failures, High-Risk Assumptions, Real-World Breakpoints, Hidden Dependencies, Required Changes. Each finding has: flaw description with file:line references, "Why it matters" (contract impact), "How it fails in practice" (concrete failure mode), severity, "What must change" (specific required fix).

**Rigor expectation:** Every finding has specific evidence. The user catches subtle contract interactions — gate-definition drift, axis mixing in grammars, false disjunctions between options that share machinery. Hand-waving is consistently rejected.

**Structural solutions preferred:** User prefers splitting concerns over adapting surfaces. Rev 14's separation of checkpoint/ledger/coverage was explicitly validated. The pattern: when a surface can't serve two masters, create a new surface.

**Clean separation valued:** The two-tier provenance model, the claim ledger vs checkpoint separation, the G3 vs narrative coverage decoupling — all validated by the user's acceptance pattern.

**Gate integrity:** User treats gate definitions as invariants. Stretching a gate beyond its invariant text is gate-definition drift. The fix is to correctly scope the gate, not to widen it.

**Counter-review before editing:** User counter-reviews proposed approaches before edits. This caught 4 issues in the rev 12 proposals that would have required another revision cycle if edited directly. The pattern works — present approach, receive counter-review, edit.

**Convergence tolerance:** The user accepts iterative convergence. Three review cycles in one session, each finding fewer and more targeted issues. The severity pattern (4 critical → 2 critical → 2 critical) shows criticals are shifting from design correctness to boundary/scope issues — the architecture is stable.
