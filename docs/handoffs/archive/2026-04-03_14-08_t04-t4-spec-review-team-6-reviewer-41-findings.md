---
date: 2026-04-03
time: "14:08"
created_at: "2026-04-03T18:08:25Z"
session_id: fcdb30b7-a41a-4f8b-88eb-1201ef99c817
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-03_13-36_t04-t4-modular-spec-compilation-and-topology-validation.md
project: claude-code-tool-dev
branch: docs/t04-t4-scouting-and-evidence-provenance
commit: 68a332d9
title: T-04 T4 spec-review-team — 6 reviewers, 51 raw → 41 canonical findings, 2 P0
type: handoff
files:
  - .review-workspace/preflight/packet.md
  - .review-workspace/synthesis/report.md
  - .review-workspace/synthesis/ledger.md
  - .review-workspace/findings/authority-architecture.md
  - .review-workspace/findings/contracts-enforcement.md
  - .review-workspace/findings/completeness-coherence.md
  - .review-workspace/findings/verification-regression.md
  - .review-workspace/findings/schema-persistence.md
  - .review-workspace/findings/integration-enforcement.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/spec.yaml
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/README.md
---

# Handoff: T-04 T4 spec-review-team — 6 reviewers, 51 raw → 41 canonical findings, 2 P0

## Goal

Run the spec-review-team skill against the modular T4 spec to validate the
monolith-to-modular compilation before merging to main.

**Trigger:** Prior session compiled the 2441-line T4 monolith (rev 21, "Defensible"
verdict) into a modular spec with 59 requirement IDs, 8 authorities, and 13 boundary
edges. The user explicitly stated in that session: "Next session we will run a
spec-review-team." This session executed that instruction.

**Stakes:** The modular T4 spec at `docs/plans/t04-t4-scouting-position-and-evidence-
provenance/` is the canonical scouting and evidence provenance contract for the
dialogue-supersession benchmark. Structural or semantic defects in the modular split
would propagate to T7 integration and scored benchmark runs. The review is the quality
gate before merging to main.

**Success criteria:**
- All 6 review lenses (4 core + 2 optional specialists) complete
- Findings triaged by priority with corroboration evidence
- Synthesis report with audit metrics and remediation guidance
- User receives actionable findings for next-session remediation

**Connection to project arc:** T4 is one of seven benchmark-first design tracks
(T1-T7). The monolith reached "Defensible" at rev 21. Modularization was completed
in the prior session. This review validates the modular compilation's structural and
semantic integrity.

## Session Narrative

### Loading prior context

Loaded the handoff from the prior session documenting the T4 modular spec compilation.
The handoff proposed three next steps; user had already chosen spec-review-team as the
immediate next action. The handoff was archived to `docs/handoffs/archive/` and a state
file written for chain protocol continuity.

### Phase 1-3: Discovery, routing, and preflight

Read `spec.yaml` and frontmatter from all 11 spec files. Built the authority map:

- 7 normative files across 5 distinct derived roles (foundation, state, behavior,
  enforcement, execution)
- 4 non-normative files (reference role)
- 13 directional boundary edges from 6 boundary rules
- state-model.md flagged as high-attention (multi-role: state + behavior)

The routing gate evaluated 4 conditions against redirect thresholds — all exceeded
(5 derived roles vs ≤2, 13 edges vs ≤2, 2 specialist triggers vs 0). No redirect
to reviewing-designs. Full team review warranted.

Preflight mechanical checks: all frontmatter valid, all authority references resolve,
no unknown claims, no normative files with zero effective claims, max 2 effective
claims per file (under the 3-claim cap). Semantic manifest validation clean.
Cross-references validated at commit `86a81773` with 0 unresolved targets — branch
unchanged since.

Specialist spawning was deterministic (full contract mode):
- `schema-persistence` triggered by `persistence_schema` on normative state-model.md
- `integration-enforcement` triggered by `enforcement_mechanism` on normative
  containment.md and benchmark-readiness.md

Materialized the preflight packet at `.review-workspace/preflight/packet.md` with
authority map, boundary edges, signal matrix, mechanical checks, route decision, spawn
plan, and key spec characteristics.

### Phase 4: Review — 6 parallel Sonnet reviewers

Created the `spec-review` team via TeamCreate. Created 6 tasks (one per reviewer).
Spawned all 6 reviewers in parallel with Sonnet model, each pointed to the preflight
packet (not embedded in spawn prompts — they read it themselves per the skill's
anti-compression rule).

**Completion sequence:**
1. contracts-enforcement — first to complete. 8 initial findings. Sent cross-domain
   alerts to schema-persistence (CE-1 re ProvenanceEntry `type` gap), authority-
   architecture (CE-2 re BD-01/BR-09 contradiction), and integration-enforcement
   (CE-6 re PR-12 read-scope enforcement).
2. authority-architecture — 6 findings. Sent DM to completeness-coherence about AA-2
   (BD-01/BR-09 conflict). Later filed AA-6 as followup confirming CE-3.
3. integration-enforcement — highest-severity output. 9 initial findings including
   1 P0 (IE-1: Grep/Glob self-enforcement gap). Sent cross-domain alerts to
   contracts-enforcement, verification-regression, and completeness-coherence.
4. verification-regression — 11 findings. Sent DM to integration-enforcement about
   T4-CT-04 conformance matrix gap (VR-1).
5. schema-persistence — 7 findings. SP-7 confirmed CE-3 (Phase 2 missing
   not_scoutable step) as followup.
6. completeness-coherence — last to complete (broadest scope: all cross-references,
   counts, terms across 11 files). 5 findings, no P0 behavioral conflicts. Confirmed
   all 59 IDs, 70 matrix items, 10-item reading order.

**Lateral messaging was exceptionally productive.** Cross-reviewer DMs produced:
- CE-3 → AA-6 + SP-7: triple convergence on Phase 2 gap
- IE-1 → CE-9: P0 enforcement gap confirmed from contracts lens
- CE-6 → IE-10: read-scope enforcement gap confirmed from enforcement lens
- VR-1 → IE-11: CT-04 matrix gap confirmed from enforcement lens
- SP-5 → CE-11: field name mismatch confirmed from contracts lens
- IE-9 → VR-6 alignment: proof surface self-validation confirmed as load-bearing

**Late activity:** After synthesis was written but before shutdown, contracts-
enforcement filed CE-12 (read_anchor normative conflict as `ambiguity_finding` under
empty precedence). This was confirmed by integration-enforcement as consistent with
IE-10's synthesis_note. CE-12 is captured in the findings file but not in the
synthesis ledger.

### Phase 5: Synthesis

Read all 6 findings files (51 raw findings total). Executed synthesis mechanical passes:

1. **Canonicalize:** All findings used correct schema. 0 normalization rewrites.
2. **Build ledger:** 7 duplicate clusters merged (reducing 17 raw findings to 7
   canonical), 5 related-pattern clusters identified.
3. **Verify deferrals:** All cross-domain alerts received and addressed. 0 unverified
   deferrals.
4. **Compute metrics:** All 10 audit metrics computed.
5. **Boundary coverage:** All 13 edges examined — no boundary coverage gaps.

Wrote synthesis ledger to `.review-workspace/synthesis/ledger.md` and full report
to `.review-workspace/synthesis/report.md`.

### Phase 6: Present and cleanup

Delivered report summary to user. Sent shutdown requests to all 6 reviewers.
All 6 shut down gracefully (shutdown_approved). Called TeamDelete — team cleaned up
successfully.

User chose to preserve `.review-workspace/` for remediation reference and deferred
merge to main.

## Decisions

### Preserve `.review-workspace/` for remediation reference

**Choice:** Keep the review workspace directory with all findings, ledger, and report
artifacts.

**Driver:** User explicitly requested: "Preserve .review-workspace/ for reference
during remediation."

**Rejected:**
- Clean up immediately — rejected because user wants to analyze the full report in
  the next session before acting on findings.

**Trade-offs:** Gitignored directory persists on disk. Negligible cost.

**Confidence:** High (E2) — user's explicit instruction.

**Reversibility:** High — `trash .review-workspace/` at any time.

**Change trigger:** After remediation is complete and findings are addressed.

### Do not merge to main

**Choice:** Keep `docs/t04-t4-scouting-and-evidence-provenance` branch unmerged.

**Driver:** User explicitly stated: "Do not merge docs/t04-t4-scouting-and-evidence-
provenance to main." User wants to analyze the full report and share thoughts before
any merge.

**Rejected:**
- Merge now with review findings as follow-up work — rejected because user wants to
  assess findings first. Some may require spec changes before merge.

**Trade-offs:** Branch remains open. No risk — clean branch with no conflicts.

**Confidence:** High (E2) — user's explicit instruction.

**Reversibility:** High — merge whenever ready.

**Change trigger:** User completes review analysis and addresses findings.

## Changes

### `.review-workspace/` — Spec review artifacts (gitignored)

All files created by the review team and synthesis process. Not committed — gitignored
by `.gitignore:60` (`.review-workspace/`).

| File | Purpose | Lines |
|------|---------|-------|
| `preflight/packet.md` | Authority map, boundary edges, spawn plan | ~120 |
| `findings/authority-architecture.md` | AA-1 through AA-6 | ~123 |
| `findings/contracts-enforcement.md` | CE-1 through CE-11 (CE-12 late addition) | ~200 |
| `findings/completeness-coherence.md` | CC-1 through CC-5 | ~127 |
| `findings/verification-regression.md` | VR-1 through VR-11 | ~244 |
| `findings/schema-persistence.md` | SP-1 through SP-7 | ~136 |
| `findings/integration-enforcement.md` | IE-1 through IE-11 | ~201 |
| `synthesis/ledger.md` | 41 canonical findings, merge rationale, clusters | ~220 |
| `synthesis/report.md` | Full report with priorities, corroboration, metrics | ~280 |

## Codebase Knowledge

### Spec-review-team skill architecture

The skill lives at `packages/plugins/superspec/skills/spec-review-team/SKILL.md` with
5 reference files:

| Reference | Path | Purpose |
|-----------|------|---------|
| Role rubrics | `skills/spec-review-team/references/role-rubrics.md` | Shared scaffold, claim_family classifier, 6 domain briefs |
| Synthesis guidance | `skills/spec-review-team/references/synthesis-guidance.md` | Consolidation rules, corroboration taxonomy, worked examples |
| Preflight taxonomy | `skills/spec-review-team/references/preflight-taxonomy.md` | 6 canonical clusters, specialist spawn signals, sampling policy |
| Agent teams platform | `skills/spec-review-team/references/agent-teams-platform.md` | TeamCreate, SendMessage, TaskCreate, shutdown protocol |
| Failure patterns | `skills/spec-review-team/references/failure-patterns.md` | Troubleshooting for all failure modes |
| Shared contract | `packages/plugins/superspec/references/shared-contract.md` | spec.yaml schema, claims enum, derivation table, precedence |

**Key operational detail:** The skill runs in full contract mode when `spec.yaml`
is present (deterministic specialist spawning from claims, mechanical precedence
resolution, boundary coverage analysis). Without `spec.yaml`, it falls back to
degraded mode (heuristic clustering, sampling-based specialist scoring).

**Team lifecycle:** TeamCreate → TaskCreate (one per reviewer) → Agent spawn with
`team_name` parameter (makes them teammates, not subagents) → idle notifications as
completion signal → SendMessage shutdown requests → TeamDelete.

### T4 spec authority model (as reviewed)

8 authorities in `spec.yaml`:

| Authority | Default Claims | Normative Files |
|-----------|---------------|-----------------|
| foundation | architecture_rule, decision_record | foundations.md |
| state-model | persistence_schema, interface_contract | state-model.md |
| scouting-behavior | behavior_contract | scouting-behavior.md |
| containment | enforcement_mechanism | containment.md |
| provenance | interface_contract, behavior_contract | provenance-and-audit.md |
| benchmark-readiness | enforcement_mechanism | benchmark-readiness.md |
| boundaries | implementation_plan | boundaries.md |
| supporting | *(none)* | README.md, rejected-alternatives.md, conformance-matrix.md, crosswalk.md |

**Empty precedence model:** `claim_precedence: {}`, `fallback_authority_order: []`,
`unresolved: ambiguity_finding`. No authority silently wins — all normative conflicts
escalate. This design was validated by the review: the BD-01/BR-09 contradiction was
mechanically detectable because no hierarchy resolved it silently.

**Link topology (from prior session):** Provenance is the hub (29% of links, target
of 5 boundary rules). Foundations is only 10%. Non-foundation modules route majority
of outbound links to peers.

### Review findings landscape

**51 raw → 41 canonical findings** across 6 reviewers. Distribution:

| Reviewer | Raw | Canonical (after merges) | Highest |
|----------|-----|-------------------------|---------|
| authority-architecture | 6 | 3 standalone + 4 merged | P0 |
| contracts-enforcement | 11 (12 with late CE-12) | 5 standalone + 6 merged | P0 |
| completeness-coherence | 5 | 3 standalone + 2 merged | P1 |
| verification-regression | 11 | 9 standalone + 2 merged | P1 |
| schema-persistence | 7 | 4 standalone + 3 merged | P1 |
| integration-enforcement | 11 | 9 standalone + 2 merged | P0 |

**7 corroborated findings** (multi-reviewer convergence):
- SY-2 (P0): BD-01/BR-09 artifact contradiction — **triple independent** (AA, CE, CC)
- SY-6 (P0): Grep/Glob self-enforcement — cross_lens_followup (IE, CE)
- SY-3 (P1): Phase 2 missing not_scoutable step — **triple** (CE, AA, SP)
- SY-4 (P1): Matrix item 19 extends normative — **triple independent** (AA, CE, VR)
- SY-1 (P1): ProvenanceEntry missing `type` — independent_convergence (CE, SP)
- SY-5 (P1): ClaimRef wire format undeclared — independent_convergence (CE, SP)
- SY-7 (P1): BD-01 framing misleading — independent_convergence (AA, CC)

**5 related-pattern clusters:**
- Cluster A: Conceptual-query scope enforcement (CE-5, IE-3, IE-8)
- Cluster B: Read-scope enforcement surface (CE-6, IE-10)
- Cluster C: Proof surface / diff capability readiness (VR-6, CE-10, IE-9)
- Cluster D: CT-04 verification gap (VR-1, IE-11)
- Cluster E: decomposition_skipped schema/extraction (SP-5, CE-11)

**Systemic pattern:** 9 of 20 P1 findings come from integration-enforcement identifying
enforcement MUSTs that omit *who* enforces and *when* the gate fires. A single pass
through enforcement MUSTs to assign actors and gate timing would address IE-2, IE-3,
IE-5, IE-6, IE-7, IE-8, IE-10 collectively.

### Audit metrics

| # | Metric | Value |
|---|--------|-------|
| 1 | `raw_finding_count` | 51 |
| 2 | `canonical_finding_count` | 41 |
| 3 | `duplicate_clusters_merged` | 7 |
| 4 | `related_finding_clusters` | 5 (12 findings) |
| 5 | `corroborated_findings` | 7 |
| 6 | `contradictions_surfaced` | 0 |
| 7 | `normalization_rewrites` | 0 |
| 8 | `ambiguous_review_clusters` | 0 |
| 9 | `reviewers_failed` | 0 |
| 10 | `unverified_deferrals` | 0 |

## Context

### What this session represents

This was a **formal quality gate review** — not design work or implementation. The T4
spec's design space was closed at rev 21 ("Defensible" verdict). The modular compilation
was completed in the prior session. This session assessed whether the compilation
introduced structural or semantic defects, and what gaps exist in the spec's enforcement
surface.

### Mental model

**Quality gate on a compiler output.** The spec-review-team treats the modular spec as
an artifact to validate, not a design to critique. The 6 reviewers examine the same
files through different defect-class lenses (authority placement, contract enforcement,
coherence, verification coverage, schema integrity, enforcement surface). Cross-lens
convergence is the strongest quality signal — when 3 reviewers independently find the
same defect through different lenses, it's almost certainly real.

### What the review revealed about the spec

The T4 spec's **normative content is structurally sound** — the monolith-to-modular
compilation preserved all requirement IDs, cross-references resolve correctly, and the
authority model is internally consistent. The single-canonical-location principle held
for all but one requirement (the `not_scoutable` classification step in Phase 2).

The spec's **weakest area is its enforcement surface** — the gap between "MUST" and
"who checks." The integration-enforcement specialist's 9 P1 findings all share this
pattern: the spec specifies what must be enforced but omits the enforcement actor and
gate timing. This is a systemic pattern, not a series of isolated gaps.

The **empty-precedence model worked exactly as designed.** The BD-01/BR-09
contradiction (SY-2, P0) was mechanically detectable because no precedence hierarchy
silently resolved it. In a spec with a precedence hierarchy, this contradiction would
have been silently "resolved" by whichever file was higher in the hierarchy — masking
the defect.

### Project state

Branch `docs/t04-t4-scouting-and-evidence-provenance` has the modular spec (committed
at `86a81773`) plus the handoff archive commit. No merge to main — user deferred
pending review analysis. The `.review-workspace/` directory (gitignored) contains all
review artifacts.

## Learnings

### Lateral messaging produces exceptional cross-lens confirmation

The spec-review-team's lateral messaging design had reviewers sending targeted DMs when
they found cross-lens findings. This session produced 7 corroborated findings out of 41
canonical — a 17% corroboration rate. Three findings had triple convergence (3
independent reviewers). The DM summaries visible in idle notifications gave the lead
(me) synthesis-relevant context without polling.

**Key mechanism:** Reviewers are scoped by defect class, not file assignment. Every
reviewer reads every file through their lens. When `authority-architecture` finds a
misplaced claim, it messages `contracts-enforcement` to check downstream references —
creating cross-lens confirmation that neither could produce alone.

### Integration-enforcement specialist justified its deterministic spawn

The specialist was triggered deterministically by `enforcement_mechanism` claims on two
normative files. It produced the P0 finding (IE-1: Grep/Glob self-enforcement) and 9
P1 findings — the highest yield of any reviewer. Without the specialist, the enforcement
surface gap pattern (the systemic "who enforces?" omission) would not have been
identified as a coherent defect class.

### Late findings arrive after synthesis — snapshot limitation

Contracts-enforcement filed CE-12 (read_anchor normative conflict) after the synthesis
ledger and report were written but before shutdown. This is an inherent limitation:
synthesis is a point-in-time snapshot. The finding is captured in the findings file but
not in the canonical ledger or report. Future sessions should check findings files for
any late additions not reflected in the synthesis.

### Empty precedence catches contradictions that hierarchies mask

SY-2 (P0) — the BD-01/BR-09 artifact contradiction — was independently found by 3
reviewers because the empty precedence model surfaces it as an `ambiguity_finding` (a
spec defect). With a precedence hierarchy (e.g., `benchmark-readiness > boundaries`),
this contradiction would be silently "resolved" by letting one file win, masking a
genuine normative conflict.

## Conversation Highlights

**User's directive was minimal and precise.** The entire session was driven by two user
messages: the `/load` command and the final `/save` instruction with explicit
constraints: "Preserve .review-workspace/ for reference during remediation. Do not
merge docs/t04-t4-scouting-and-evidence-provenance to main."

**Review style continuity from prior session:** The user's prior-session review
approach (adversarial, P1/P2/P3 priorities, explicit verdicts) carried forward as the
review standard. The spec-review-team's finding schema (P0/P1/P2, violated_invariant,
affected_surface, evidence, recommended_fix) aligns with the user's review framework.

**User deferred all remediation decisions.** Rather than acting on findings immediately:
"I will analyze the full report, and share my thoughts in the next session." This is
consistent with the prior session's pattern of direct-review-before-delegation.

## User Preferences

**Direct review before action:** User explicitly chose to analyze the full report
before remediation. Quote: "I will analyze the full report, and share my thoughts in
the next session."

**Preserve review artifacts:** User wants the full .review-workspace/ directory
available for reference, not just the synthesis report.

**No premature merges:** User explicitly blocked merge to main until review findings
are analyzed. This is consistent with the prior session's preference for atomic landing
— the modular spec should be correct before it reaches main.

**Minimal interaction during automated work:** User provided only the `/load` command
and the final save instruction. No mid-review intervention or steering — trusted the
spec-review-team skill to execute its full workflow.

## Next Steps

### 1. Analyze the spec-review-team report and share remediation decisions

**Dependencies:** None — report and all artifacts are in `.review-workspace/`.

**What to read first:** `.review-workspace/synthesis/report.md` — the full report with
prioritized findings, corroboration table, and remediation guidance. The report's
"Remediation Priority" section groups fixes into three categories: immediate mechanical
fixes, design-decision fixes, and systemic enforcement architecture review.

**Approach:** User stated they will analyze the full report and share their thoughts.
The next session should start with the user's assessment — which findings to address,
which to defer, and which to reject.

**Key items requiring user decision:**
- SY-6 (P0): Grep/Glob enforcement — option (a) harness-side enforcement vs (b)
  qualify T4-F-11 and add benchmark-readiness item
- SY-2 (P0): BD-01 scope qualification — option (a) qualify the row vs (b) remove it
- Systemic enforcement actor pattern — address individually or via a single pass
- CE-12 (late finding): Not in synthesis — needs manual triage

**Acceptance criteria:** User provides remediation decisions for at least the 2 P0
findings. Remaining P1/P2 findings can be batched.

### 2. Implement remediation (after user analysis)

**Dependencies:** User's remediation decisions from step 1.

**What to read first:** Individual findings files in `.review-workspace/findings/` for
full evidence and recommended fixes.

**Approach:** Start with the 4 mechanical fixes (SY-8: wrong cross-ref, SY-12: count
mismatch, SY-35: term drift, SY-34: stale history) — these require no design decisions.
Then address the P0 design-decision fixes. Then the P1 batch.

**Potential obstacles:** Some P1 findings (CE-5, CE-7) involve pre-T7 enforcement
impossibility — the spec may need to explicitly acknowledge these as known pre-T7
limitations rather than "fixing" them.

### 3. Merge to main (after remediation)

**Dependencies:** Remediation from step 2 complete. User approves.

**Approach:** Standard PR from `docs/t04-t4-scouting-and-evidence-provenance` → `main`.

## In Progress

Clean stopping point — spec review complete, report delivered, team shut down. No work
in flight. User will analyze the full report in the next session.

## Open Questions

1. **How should the systemic enforcement actor pattern be addressed?** The report
   identifies 9 P1 enforcement findings that share a common pattern (MUST without "who
   checks"). A single pass through enforcement MUSTs to assign actors and gate timing
   is proposed, but the user may prefer addressing them individually or accepting some
   as deliberate design (e.g., agent self-enforcement for some constraints).

2. **What is the disposition of CE-12 (late finding)?** The read_anchor normative
   conflict (T4-SM-05 declares audit fields "non-authoritative" while T4-PR-12 uses
   `read_anchor` as the verification surface) was filed after synthesis. It needs
   manual triage and may be a third P0 under the empty-precedence model.

3. **Are pre-T7 enforcement impossibility findings (CE-5, CE-7) defects or known
   limitations?** The spec has active MUSTs with enforcement infrastructure that
   doesn't exist yet. The report treats these as P1 findings, but the user may want
   to document them as explicit pre-T7 limitations instead.

## Risks

1. **Late finding not in synthesis.** CE-12 was filed after the synthesis ledger was
   written. The findings file has it; the report and ledger do not. The next session
   must manually triage CE-12.

2. **Enforcement surface pattern may require architectural decisions.** The 9
   enforcement-gap P1 findings suggest the spec systematically omits enforcement actors.
   Fixing this may require decisions about the harness architecture that go beyond
   spec text edits.

3. **Branch divergence risk is low but real.** The feature branch has been open since
   the monolith compilation. No conflicts expected (the spec lives in its own directory),
   but the longer it stays unmerged, the higher the risk of other work creating
   adjacency conflicts.

## References

| What | Where |
|------|-------|
| Full review report | `.review-workspace/synthesis/report.md` |
| Synthesis ledger | `.review-workspace/synthesis/ledger.md` |
| Preflight packet | `.review-workspace/preflight/packet.md` |
| AA findings | `.review-workspace/findings/authority-architecture.md` |
| CE findings | `.review-workspace/findings/contracts-enforcement.md` |
| CC findings | `.review-workspace/findings/completeness-coherence.md` |
| VR findings | `.review-workspace/findings/verification-regression.md` |
| SP findings | `.review-workspace/findings/schema-persistence.md` |
| IE findings | `.review-workspace/findings/integration-enforcement.md` |
| Modular spec root | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/README.md` |
| spec.yaml | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/spec.yaml` |
| Archived monolith | `docs/plans/archive/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` |
| Prior handoff (archived) | `docs/handoffs/archive/2026-04-03_13-36_t04-t4-modular-spec-compilation-and-topology-validation.md` |
| Spec-review-team skill | `packages/plugins/superspec/skills/spec-review-team/SKILL.md` |
| Shared contract | `packages/plugins/superspec/references/shared-contract.md` |

## Gotchas

1. **CE-12 is in the findings file but not in the synthesis.** contracts-enforcement
   filed CE-12 (read_anchor normative conflict as ambiguity_finding) after the
   synthesis ledger and report were written. The findings file
   `.review-workspace/findings/contracts-enforcement.md` has it; the report and ledger
   do not. Check the findings file directly for this late addition.

2. **`.review-workspace/` is gitignored.** All review artifacts live in the gitignored
   `.review-workspace/` directory. They are local to this working directory and will
   not survive a `git clean -xfd`. The user explicitly asked to preserve them.

3. **Structured shutdown messages cannot be broadcast.** The Agent Teams platform does
   not allow structured JSON messages (like `shutdown_request`) to be sent via `to: "*"`
   broadcast. Each shutdown must be sent individually to each teammate by name.
