---
date: 2026-04-05
time: "04:14"
created_at: "2026-04-05T04:14:33Z"
session_id: 063a8cbe-ec2e-439b-bec0-56a7ab026392
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-04_23-34_t6-t7-ownership-resolution-per-surface-status-matrix.md
project: claude-code-tool-dev
branch: chore/track-t6-review
commit: 13ef3b92
title: T6 review adjudication-correction patch and scrutiny findings
type: handoff
files:
  - docs/reviews/2026-04-04-t04-t6-benchmark-first-design-composition-review.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/benchmark-readiness.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/state-model.md
  - docs/plans/2026-04-02-t04-t5-mode-strategy.md
---

# Handoff: T6 review adjudication-correction patch and scrutiny findings

## Goal

Continue from the prior session's ownership resolution (Decision 1: T7 owns
four wire-format surfaces, T5 owns `agent_local`, T6 owns only the
review-framing correction) and per-surface status matrix. Execute Next Step 1
from the prior handoff: correct the T6 review doc's "Surfaces to merge" table
that overstated T6 ownership of T7/T5 work.

**Trigger:** The prior handoff explicitly flagged the T6 review correction as
Next Step 1. User's message pasting the matrix opened with *"That matrix is
the right artifact. I would not replace it"* and delivered three calls, the
first being *"Correct the T6 review now, but do it as an explicit adjudication
correction, not a silent rewrite of history."* The correction is independent
of F6/F7/F11 resolution — the ownership error is already proven against
`benchmark-readiness.md`, so waiting gains nothing.

**Stakes:** Medium-high. The T6 review is now tracked in git (`40e30b2c`
from the prior session) and is the load-bearing document for the T6
composition verdict. An uncorrected ownership map in the tracked review
would mislead any future reader about T6's responsibilities and could
recreate the scope-displacement pattern that the prior session's
rejection already identified. The correction is bounded (review-doc edit,
no normative spec changes), but it must be precise enough to survive
adversarial review itself — which is exactly what this session's scrutiny
pass tested.

**Connection to project arc:** T4 close-out → reclassification → Path-2
benchmark constraint → T6 composition (7 review passes across 3 sessions)
→ ownership resolution (prior session Decision 1) → **T6 review-doc
correction patched + scrutiny review surfacing 6 refinements (this
session)** → user response to scrutiny findings + commit of corrected
patch (next session) → benchmark-readiness.md amendments (F6/F7/F11
ownership) → T7 executable slice.

**Session's real contribution:** Not "apply a correction" — the
correction was mostly the user's draft. The session's load-bearing output
is the scrutiny pass that surfaced six refinements the user can respond
to. Specifically: an implicit F6/F7/F11 ownership assignment to T4 (Issue
1), a truncated failure-paths paragraph (Issue 3), and an orphan surface
buried in a table row that the disposition doesn't surface (Issue 4) —
three Medium findings that materially affect how the correction reads.

## Session Narrative

### Phase 1: Load and matrix absorption

Loaded the 1082-line prior handoff via `/load`. Archived it to
`docs/handoffs/archive/2026-04-04_23-34_t6-t7-ownership-resolution-per-surface-status-matrix.md`
(commit `13ef3b92`) and created the session state file at
`.session-state/handoff-063a8cbe-ec2e-439b-bec0-56a7ab026392`. Read the
handoff in chunks (1-400, 400-800, 800-1081) to absorb the four
decisions, the per-surface status matrix, the F6/F7/F11 blocker context,
and the Next Steps.

User's first substantive message pasted the complete per-surface status
matrix from the prior session as context, with explicit direction: *"Read
this for context, then I will share my response."* Per the user's
preferences (writes substantive amendments themselves; values being
listened to), I acknowledged matrix receipt in one response, highlighted
two load-bearing insights (the coupling block in Surfaces 1-4; the
`NOT EMITTED` uniformity as safe-deferral signal), and stood by.

### Phase 2: User's three calls

User delivered three calls as a structured response to the matrix:

**Call 1 — T6 review correction now:**
> "Correct the T6 review now, but do it as an explicit adjudication
> correction, not a silent rewrite of history. The ownership error in
> [review doc] is already proven against [benchmark-readiness.md].
> Waiting for F6/F7/F11 does not change that. Leaving the review
> artifact uncorrected keeps a false ownership map in the repo and
> invites the same mistake again. The clean fix is: preserve the
> original composition verdict, but amend the consolidation section..."

**Call 2 — F6/F7/F11 ownership to T4, not T7:**
> "F6/F7/F11 should be driven by the T4 provenance/state-model authority
> set, not by T7. Those findings are design-contract gaps in
> [provenance-and-audit.md] and adjacent normative material, not
> benchmark harness implementation tasks. T7 is the consumer/gate owner.
> It should not be forced to invent concession representation,
> serialization handoff, or versioning policy while implementing
> consumers."

**Call 3 — Defer Surface 5:**
> "Do not land Surface 5 as a spec-only isolated commit yet. It is the
> only semantically stable surface, but the payoff is low and the
> mismatch is real... Because nothing emits `agent_local` today, there
> is no urgency."

User closed: *"If you want the next step from me, the highest-signal one
is drafting the exact correction language for the T6 review artifact
only, with no broader plan and no implementation checklist. Let me know
if I should do this."*

### Phase 3: Alignment and branch question

Agreed on all three calls. Substantive acknowledgment of Call 2 as the
load-bearing refinement — it resolves the prior handoff's Open Question
#2 (*"Who owns F6/F7/F11 remediation?"*) by pushing ownership back one
level from consumer to producer. The structural rule generalizes: *"when
an audit finding targets a wire format, ownership is whoever writes the
wire format, not whoever reads it."*

Confirmed the user should draft the correction text themselves (matches
their pattern of writing substantive amendments). Asked one logistical
question before proceeding: branch. The prior handoff's Decision 2 note
said *"do NOT append consolidation work to `chore/track-t6-review`"* —
but a review correction isn't consolidation work. It's an adjudication
amendment to the review artifact itself. Does it land on the same branch
as a second commit, or on a new branch?

### Phase 4: Branch answer and full draft delivery

User answered: keep on `chore/track-t6-review` as a second commit.
Reasoning: `40e30b2c` is only on that branch (not on `main`), the
correction amends the same review artifact (not the normative
contracts), and `chore/*` is still semantically acceptable because this
is review-artifact maintenance, not synthesis-contract mutation.

User delivered two complete draft replacement blocks:

**Block 1:** Replace the review's old *"consolidation artifact / surfaces
to merge / done when"* block (originally `:75-93`) with an adjudication
correction paragraph + a corrected ownership map table. The table has
5 rows: 4 T7-owned wire-format surfaces, 1 T5-owned `agent_local`
surface, and a 5th orphan row (evidence-trajectory consumer projection)
marked as *"Unassigned in current gate tables"* with an explicit note
that the prior row conflated the EvidenceRecord schema with the
trajectory projection.

**Block 2:** Replace the old *"T6 disposition"* paragraph + *"T6
consolidation artifact"* table (originally `:146-159`) with an
adjudication-correction disposition routing T7 wire-format work to
benchmark-readiness.md T4-BR-04/05, T5 `agent_local` work to T4-BR-01,
and F6/F7/F11 to the T4 provenance/state-model authority set.

User pre-flagged two self-identified notes: (a) also update the stale
`benchmark-first-design-plan.md` filename to
`2026-04-01-t04-benchmark-first-design-plan.md` while touching the
section; (b) do NOT say "T6 is done" — the correction proves the
ownership table was wrong; it does not settle the open/close
interpretation of T6.

### Phase 5: Verification pass against the draft

Dispatched 4 parallel reads: the full review doc (164 lines),
`benchmark-readiness.md:14-110` (to verify T4-BR-01 + T4-BR-04 + T4-BR-05
tables), `state-model.md:163-221` (to verify ClaimRef wire format +
T4-SM-05 EvidenceRecord schema location), `t5-mode-strategy.md:115-210`
(to verify §3.4 / §3.5 / §6 line ranges).

**All citations verified.** Two minor looseness items:

1. `benchmark-readiness.md:34-38` covers all 5 T4-BR-01 rows (including
   schema enum at `:34`, parser at `:37`, tests at `:38`) when the prose
   says "documentation." The documentation rows specifically are
   `:35-36`. Tighter citation available.
2. `t5-mode-strategy.md:118-147` cuts §3.5 before operational
   consequences at `:148-160`. Range is defensible as "canonical shape
   authority" because the shape is defined in `:118-147`, but loses
   derivations. Extended range `:118-160` would include everything.

**Two structural issues flagged** (real, not looseness):

- **Issue A:** Review line `:123` (Mode migration paragraph) still says
  *"addressed by the T6 consolidation artifact"* — would dangle after
  the patch removes the artifact.
- **Issue B:** Review line `:143` (T6 Verdict table) says *"T6
  consolidation artifact below"* in the Gate action column — would
  dangle after the second replacement removes the table.

Delivered three specific fix proposals: (a) rewrite `:123` to name T5
and T7 explicitly (replacement text provided), (b) rewrite `:143` Gate
action (three options, recommended *"Ownership correction below;
remediation routed to T4/T5/T7"*), (c) update `:71` filename in same
commit.

Confirmed the substance of the draft was correct and the two replacement
blocks fit the review's structure cleanly.

### Phase 6: User applied the patch with all fixes

User executed `/scrutinize` against a Response Contract summary of the
applied patch. Key observations:

- Both replacement blocks landed cleanly at correct locations.
- `:123` mode-migration paragraph updated to "T5 and T7" per my
  replacement text.
- `:143` verdict table Gate action updated to
  *"Ownership correction below; remediation routed to T4/T5/T7"* —
  user chose my third option.
- **`:71` + `:3` filename normalized** to
  `2026-04-01-t04-benchmark-first-design-plan.md` at both sites.
- **Both "optional" tightenings applied:**
  `benchmark-readiness.md:34-38` → `:35-36` in three places;
  `t5-mode-strategy.md:118-147` → `:118-160` in the ownership map row.

Patch status: working tree modified, not committed.

### Phase 7: Scrutiny pass (the session's main deliverable)

Invoked scrutinize discipline — *"unforgiving reviewer, assume not ready,
prove it."* Read the current file state (187 lines), the full diff, and
git status to confirm what landed. Ran a mental check for stale
references to "T6 consolidation" — found 4 remaining mentions, all
intentional supersession framing. No broken supersession references.

**Verdict: Minor revision.** 6 findings:

| # | Severity | Finding | Location |
|---|---|---|---|
| 1 | Medium | Implicit F6/F7/F11 ownership assignment to T4 (review says "producer-side spec gaps in the T4 authority set" but no normative doc assigns remediation there) | disposition `:173-176` |
| 3 | Medium | "Concrete failure paths" paragraph truncated without closing bridge to ownership map | `:76-79` |
| 4 | Medium | Orphan surface (row 5, evidence-trajectory projection) buried in table row, not surfaced in disposition | table `:102` vs disposition `:167-181` |
| 5 | Low-Medium | "Specification surfaces" phrasing at `:172-173` is broader than `:35-36` citation supports | disposition `:172-173` |
| 2 | Low | "Producer-side" jargon introduced without definition | disposition `:173` |
| 6 | Low | Adjudication principle stated without showing the specific shape conflict it resolves | `:91-92` |

Plus a premise-check observation: the *"DOES NOT YET COMPOSE"* header at
`:50` has an implicit promise ("yet" = eventual delivery by T6) that's
contradicted by the disposition's "T6 won't own the consolidation."
Defensible because the extensions themselves compose, but carries
rhetorical friction.

**Two patterns** across the findings:
1. Load left in table rows that should be surfaced in prose (Issues 3, 4)
2. Implicit claims where explicit ones would cost little (Issues 1, 6)

Both traced to the same root cause: the patch minimized additions to
avoid scope creep — a good instinct, but the correction's most important
claims are exactly the ones most worth making explicit.

**Required changes:** 3 Medium findings take ~4 sentences total. 3 Low
findings are polish. The patch does not need rewriting, rejecting, or
reframing — it needs about 4 sentences added and 1 phrase tightened,
then it's ready to commit.

### Phase 8: Save triggered

User ran `/handoff:save` with explicit direction: *"save a handoff. I
will respond to your review in the next session."* Clean stopping point.

## Decisions

### Decision 1: Agreement with user's three calls

**Choice:** Endorse all three calls without modification. Specifically:
(a) Apply T6 review correction now, independent of F6/F7/F11 resolution.
(b) Reframe F6/F7/F11 as T4 remediation work rather than T7
prerequisites. (c) Defer Surface 5 (`agent_local` spec-only) landing
until the consumer slice is ready.

**Driver:** Each call had independent verifiable reasoning. Call 1
stands because the ownership error is proven against
`benchmark-readiness.md` T4-BR-04/05 (assignments to T7) independently
of F6/F7/F11 state — no dependency chain would change on audit
resolution. Call 2's structural logic (spec gaps live in specs, not in
consumer code) resolves the prior session's Open Question #2 more
elegantly than my three-option framework. Call 3's reasoning ("zero
producers exist today; spec-only landing creates visible gap without
unblocking anything") matches the matrix Surface 5 analysis.

**Alternatives considered:**

- **Push back on Call 2:** The alternative framing would place F6/F7/F11
  under T7 as prerequisites T7 must invent solutions for while
  implementing consumers. **Rejected** because T7's role is consumer/gate
  implementation, not spec authoring. The user's structural rule
  generalizes: audit findings targeting a wire format belong to whoever
  writes the format.
- **Push back on Call 3:** The alternative would land Surface 5's
  spec-only rows immediately (they have no audit blockers). **Rejected**
  because the risk of creating a spec-vs-code gap that a future T-04
  candidate would trip over (silent coercion at `SKILL.md:435`) exceeds
  the benefit of documenting a mode that no producer emits.
- **Propose modifications to any call:** **Rejected** because
  verification against sources showed all three calls were internally
  consistent and fit the matrix findings.

**Implications:**
- The session's work becomes: verify the user's draft correction (Phase
  5), then apply scrutiny discipline to the landed patch (Phase 7).
- Call 2 reshapes future work — F6/F7/F11 resolution is a T4 remediation
  packet, not part of T7's executable slice. This means T7 has a
  cleaner scope (consumer implementation) and T4 has ongoing spec-gap
  remediation obligations.
- Call 3's deferral becomes a project-level gate: Surface 5 doesn't
  land until T5's Primary Migration Set can land together.

**Trade-offs accepted:**
- Call 2's reframe pushes the ownership question onto T4, which has no
  currently-assigned remediation authority in any gate table. This
  creates a new unassigned-ownership problem (who in T4 owns audit
  remediation?) even as it resolves the T7 overload problem.
- Call 3's deferral leaves the `agent_local` spec-vs-code mismatch
  visible in the repo until the full T5 slice lands.

**Confidence:** High (E2) — each call verified against independent
sources (benchmark-readiness.md for Call 1, audit file structure + T7
scope definition for Call 2, matrix Surface 5 analysis for Call 3).

**Reversibility:** Medium — Calls 1 and 3 are easily reversed (the
correction can be amended; Surface 5 can still land any time). Call 2
is harder to reverse once T4 starts remediating, because the normative
specs will change to incorporate the fixes.

**What would change this decision:** (a) A benchmark-readiness.md
amendment that explicitly assigns F6/F7/F11 to T7 would force Call 2
reversal. (b) A T-04 candidate loop appearing in the repo would make
Call 3 deferral untenable. (c) A new audit pass finding issues in the
adjudication correction itself would force Call 1 to be redone.

### Decision 2: Accept user's draft with two structural fixes

**Choice:** Endorse the user's complete draft for both replacement
blocks (adjudication correction + ownership map table + corrected
disposition). Flag two structural issues downstream of the replacement
blocks that require matching updates in the same commit: `:123`
mode-migration paragraph and `:143` verdict table Gate action.

**Driver:** Verification against cited sources showed all file:line
citations in the draft resolve correctly. Two structural issues were
real: after the patch removes the "T6 consolidation artifact" concept,
`:123` still references it ("addressed by the T6 consolidation
artifact") and `:143` still points at it ("T6 consolidation artifact
below"). These are stale references that would create internal
contradictions post-patch.

**Alternatives considered:**
- **Approve the draft as-is without flagging the downstream issues:**
  **Rejected** because the resulting patch would create self-contradictions
  in the review doc — a failure of the same class (dangling references)
  the correction is fixing.
- **Propose edits to the user's replacement block text itself:**
  **Rejected** because the user writes substantive amendments and the
  draft text was correct in substance. Edits to the draft would be
  style changes, not verification findings.
- **Reject the draft because of the downstream issues:** **Rejected**
  because the issues are bounded (two specific lines, one file) and
  fixable in the same commit — not a reason to reject the whole
  correction.

**Implications:**
- User's patch incorporated both my structural fixes (my suggested
  replacement text at `:123` landed verbatim; my recommended option for
  `:143` was chosen from three).
- User also applied both "optional" tightenings (Issues 5 and 6 minor
  items from my review) — suggesting that in this user's workflow,
  flagged items are treated as actionable recommendations regardless of
  my severity labeling.

**Trade-offs accepted:**
- Flagging the downstream issues made the verification response longer
  than a bare yes/no. User preferred that depth (applied all fixes).
- The tightening items I marked as optional became de facto required by
  user application. Future verification passes should assume flagged
  items are recommendations, not options.

**Confidence:** High (E3) — triangulated across 4 parallel file reads
plus the prior session's handoff verification notes.

**Reversibility:** High — verification findings can be withdrawn if
proven wrong; user can choose not to apply any given fix.

**What would change this decision:** If the downstream issues had been
phantoms (false positives), the verification response would have been
"substance correct, ready to apply" without any fixes. The real change
driver would be evidence that the references at `:123`/`:143` don't
actually reference the removed concept.

### Decision 3: Scrutiny verdict "Minor revision" with 6 findings

**Choice:** Apply `/scrutinize` discipline unforgivingly, produce 6
findings (3 Medium, 3 Low), identify 2 patterns, issue verdict "Minor
revision." Specifically NOT "Defensible" (the patch has real issues) and
NOT "Major revision" (the issues are bounded and fixable in ~4
sentences).

**Driver:** The scrutinize skill explicitly mandates "unforgiving
reviewer, assume not ready, prove it." Applied the discipline honestly:
scanned the current file for stale references, verified all citations,
looked for structural issues the patch might have introduced, and
attacked the correction from 5 adversarial perspectives (future T7
implementer, future F6/F7/F11 remediator, first-time skimmer of the
Synthesis Contract section, future T6 closer, hostile reviewer looking
for scope displacement in the correction itself).

**Alternatives considered:**
- **Verdict: Defensible:** Would mean the patch has no material issues.
  **Rejected** because Issue 1 (implicit F6/F7/F11 ownership to T4) is a
  real claim not backed by any normative doc, and the same scope-
  displacement pattern the correction fixes appears one level up.
- **Verdict: Major revision:** Would mean the patch needs rewriting.
  **Rejected** because none of the 6 findings are critical, no factual
  errors exist, all citations verify, and the core correction is
  substantively correct. The patch doesn't need to be rewritten — it
  needs ~4 sentences added.
- **Soften the findings to avoid tension:** **Rejected** per the skill's
  rule ("do not soften findings with hedging unless uncertainty is
  genuinely unavoidable"). The user's workflow welcomes hard feedback
  and applies it.

**Implications:**
- Next session begins with user responding to the scrutiny findings.
  User has explicit direction: "I will respond to your review in the
  next session."
- The 3 Medium findings (1, 3, 4) are the ones the user will most
  likely address. Issue 1 in particular is the most interesting because
  it identifies a scope-displacement pattern in the correction itself —
  the same class of error the correction fixes, one level up.
- The patch remains uncommitted in working tree. Commit must wait for
  the scrutiny response.

**Trade-offs accepted:**
- The scrutiny report is long (~200 lines of findings). Longer than
  needed for a verdict, but the depth is what makes the findings
  actionable.
- Finding 1 creates tension for Call 2 (the user's own reframe) — the
  scrutiny is criticizing a claim the user made. Defensible because the
  discipline mandates honest feedback, but worth noting that the
  finding isn't about the patch's text in isolation, it's about the
  user's ownership framing that the patch encodes.

**Confidence:** High (E2) — two independent sources for each finding
(the file content + the cited normative sources + the handoff's prior
verification work).

**Reversibility:** High — findings can be withdrawn if counter-evidence
emerges; verdict can be revised.

**What would change this decision:** User's response in the next session
might demonstrate that Finding 1 is wrong (e.g., if a gate table does
assign F6/F7/F11 to T4 and I missed it). Other findings could similarly
be refuted if I misread the current file state.

### Decision 4: Recommend same branch (`chore/track-t6-review`) for correction commit

**Choice:** When the user asked about branch, recommend keeping the
correction on `chore/track-t6-review` as a second commit rather than
creating a new branch.

**Driver:** The prior handoff's Decision 2 said *"do NOT append
consolidation work to `chore/track-t6-review`"* — but a review correction
is not consolidation work. It's an adjudication amendment to the review
artifact itself, not a mutation of the normative contracts the review
evaluates. The branch name `chore/*` remains semantically accurate
because this is review-artifact maintenance, not a synthesis-contract
mutation.

**Alternatives considered:**
- **New branch `docs/t6-review-correction`:** Clean separation between
  tracking commit and correction commit. **Rejected** because it would
  split one unmerged review artifact across two branches with no
  semantic gain. The tracking commit (`40e30b2c`) and the correction
  commit amend the same file and serve the same purpose.
- **Leave the correction uncommitted until the branch policy decision
  resolves:** **Rejected** because the branch-semantics question has a
  defensible answer (same branch) and blocking on it would stall the
  patch.

**Implications:**
- Both commits (`40e30b2c` tracking + upcoming correction commit) live
  on `chore/track-t6-review`.
- The branch will now have 2 commits when the correction is committed.
- Future work on the same review artifact should also land on this
  branch if it's still unmerged.

**Trade-offs accepted:**
- Slightly overloads the `chore/*` naming — one commit is housekeeping
  (tracking), the other is substantive content (adjudication
  correction). But both are review-artifact scope, not normative spec
  scope.

**Confidence:** High (E1) — single-source reasoning from the prior
Decision 2 note's intent ("chore/ is OK for tracking, not for normative
mutation"). User ratified the recommendation.

**Reversibility:** High — the correction commit could be cherry-picked
to a new branch at any time.

**What would change this decision:** If the correction commit expanded
to touch normative specs (e.g., amending `benchmark-readiness.md` to
fix the `:87` shape phrasing), then the branch semantics would need to
change.

## Changes

### `docs/reviews/2026-04-04-t04-t6-benchmark-first-design-composition-review.md`

**Purpose:** The T6 composition review artifact. This session applied
an adjudication-correction patch.

**State before session:** 164 lines, committed as `40e30b2c` on
`chore/track-t6-review` (from prior session). Contains the T3/T4 fix the
user applied between sessions, but the "Surfaces to merge" table at
`:83-93` and "T6 consolidation artifact" table at `:150-159` overstate
T6's ownership of T7/T5 work.

**State after session:** 187 lines, modified in working tree, **NOT
committed**. Two replacement blocks landed:

1. **Synthesis Contract section (`:81-107`):** Replaced the old
   consolidation artifact / surfaces to merge / done-when block with:
   - A bridging paragraph: *"T4's synthesis extensions remain
     compatible, but the original version of this section overstated
     T6's ownership of the remaining surfaces."*
   - An "Adjudication correction" paragraph citing
     `benchmark-readiness.md:79-102` (T7 ownership) and `:35-36`
     (T5 ownership), plus the ownership-vs-shape distinction from
     Decision 1 of the prior session.
   - A "Corrected ownership map" table with 5 rows: 4 T7-owned
     surfaces, 1 T5-owned surface, and the evidence-trajectory
     consumer projection marked "Unassigned in current gate tables."
   - A closing sentence preserving the verdict: *"This correction
     changes the ownership reading, not the composition verdict."*

2. **T6 Verdict section (`:167-181`):** Replaced the old disposition
   paragraph + T6 consolidation artifact table with:
   - New disposition header: *"T6 disposition: adjudication correction
     to ownership framing."*
   - Body routing T7 wire-format surfaces to `benchmark-readiness.md:79-102`,
     T5 specification surfaces to `:35-36`, and F6/F7/F11 to
     *"producer-side spec gaps in the T4 provenance/state-model
     authority set."*
   - Closing: *"The original 'T6 consolidation artifact' table should
     be read as superseded by this adjudication correction."*

3. **Mode migration paragraph (`:137-144`):** Updated from "Mode
   migration spans T6 and T7" to "Mode migration spans T5 and T7" with
   my replacement text. Now cites
   `2026-04-02-t04-t5-mode-strategy.md:195-206` instead of the shorthand
   `t5:195-206`.

4. **T6 Verdict table row (`:164`):** Gate action for Synthesis contract
   row changed from "T6 consolidation artifact below" to "Ownership
   correction below; remediation routed to T4/T5/T7" — my third
   suggested option.

5. **Filename normalization (`:3`, `:71-72`):** Updated
   `benchmark-first-design-plan.md` to
   `2026-04-01-t04-benchmark-first-design-plan.md` at all three cited
   sites.

6. **Two "optional" tightenings applied:**
   - `benchmark-readiness.md:34-38` → `:35-36` (three locations: `:88`,
     `:139`, `:173`). Narrows the citation from the full T4-BR-01 table
     to just the dialogue-synthesis-format.md documentation rows.
   - `t5-mode-strategy.md:118-147` → `:118-160` in the ownership map row
     (`:101`). Extends to include §3.5 operational consequences.

**Future-Claude note:** The patch is uncommitted. The correction commit
has not been created yet. User will respond to the 6 scrutiny findings
in the next session, likely apply 3 Medium fixes, then commit.

### Git state

| Before session | After session |
|---|---|
| Branch: `chore/track-t6-review` (1 commit ahead of main) | Branch: `chore/track-t6-review` (2 commits ahead of main; 1 unstaged modification) |
| Working tree: clean | Working tree: `M docs/reviews/2026-04-04-t04-t6-benchmark-first-design-composition-review.md` |
| Prior handoff: in `docs/handoffs/` | Prior handoff: archived as `13ef3b92` |

**Commits this session:**
- `13ef3b92 docs(handoff): archive 2026-04-04_23-34_t6-t7-ownership-resolution-per-surface-status-matrix.md`

**Uncommitted:**
- Review correction patch (23 lines added, per diff).

## Codebase Knowledge

### Current T6 review doc structure (post-patch, 187 lines)

| Section | Lines | Content |
|---|---|---|
| Scope | `:3` | Now cites `2026-04-01-t04-benchmark-first-design-plan.md:39` and `:52` |
| State Model: COMPOSES | `:5-25` | Unchanged from prior session |
| Loop Structure: COMPOSES | `:27-48` | Unchanged from prior session |
| Synthesis Contract: DOES NOT YET COMPOSE | `:50-107` | **Modified.** Header unchanged. Body: the 5-extension table (unchanged), the two-document split table (unchanged), the done-when paragraph (only filename updated), the concrete-failure-paths paragraph (**truncated** — original closing sentence removed), the new bridging paragraph, the "Adjudication correction" paragraph, the "Corrected ownership map" table, the closing-verdict-preservation sentence |
| Coverage Adequacy | `:109-121` | Unchanged |
| Scope / Comparability | `:123-144` | **Modified.** Mode migration paragraph updated to T5+T7 framing |
| B8 Anchor Adequacy | `:146-154` | Unchanged |
| T6 Verdict header + table | `:156-165` | **Modified.** Synthesis contract row Gate action updated |
| T6 Disposition + Adjudication body | `:167-181` | **Modified.** Replaced disposition, removed T6 consolidation artifact table |
| Deferred to T7 | `:183-186` | Unchanged |

### Adjudication correction table (exact rows, `:96-102`)

```
| Surface | Owner | Canonical semantic source | Correction |
| `claim_provenance_index` wire format | T7 | `provenance-and-audit.md:65-106`, `state-model.md:180-182` | Not T6 consolidation work; also blocked by audit F6/F7/F11 |
| `## Claim Ledger` grammar | T7 | `provenance-and-audit.md:121-210` | Not T6 consolidation work |
| `not_scoutable` in claim/evidence trajectory | T7 | `boundaries.md:35`, `provenance-and-audit.md:108-119`, `state-model.md:376-392` | Not T6 consolidation work |
| `agent_local` mode vocabulary and epilogue | T5 | `2026-04-02-t04-t5-mode-strategy.md:118-160,195-206` | Not T6 consolidation work |
| Evidence-trajectory consumer projection | Unassigned in current gate tables | `provenance-and-audit.md:14-48` | The prior row labeled this as `EvidenceRecord` schema; that was too broad. The consumer-facing surface is the evidence-trajectory projection, not the full state-model `EvidenceRecord` schema. |
```

### `benchmark-readiness.md` sub-ranges (newly verified this session)

| Range | Content |
|---|---|
| `:14-43` | T4-BR-01 "T5 Migration Surfaces" full section |
| `:32-38` | T4-BR-01 table header + 5 rows |
| `:34` | Row 1: Mode enum definition (event_schema.py:137) — T5 |
| `:35` | Row 2: Conversation summary mode (dialogue-synthesis-format.md:86) — T5 |
| `:36` | Row 3: Pipeline epilogue field (dialogue-synthesis-format.md:144) — T5 |
| `:37` | Row 4: Dialogue skill parser (SKILL.md:435) — T5 |
| `:38` | Row 5: Test enforcement — T5 |
| `:35-36` | **Specifically the dialogue-synthesis-format.md documentation rows.** This is the tightened citation the user applied. |
| `:22-30` | Benchmark-run behavior clause: silent downgrade to `server_assisted` is PROHIBITED; must produce explicit mode-mismatch failure artifact |
| `:79-90` | T4-BR-04 "Provenance Index Consumer" — 4 rows, all owner T7 |
| `:92-102` | T4-BR-05 "Synthesis-Format Contract Updates" — 4 rows, all owner T7 |

### `state-model.md` sub-ranges (verified this session)

| Range | Content |
|---|---|
| `:168-178` | T4-SM-04 "Claim Reference" header + ClaimRef struct definition (3 fields: introduction_turn, claim_key, occurrence_index) + derivation comment |
| **`:180-182`** | **Wire format declaration: *"When serialized in `claim_provenance_index`, `ClaimRef` is a dense array: `[introduction_turn, claim_key, occurrence_index]`."*** This is the exact 3 lines — no padding. |
| `:184-221` | T4-SM-05 "Evidence Record" — full 8-field EvidenceRecord struct + ScoutStep (10 fields) + CitationSpan (4 fields) |

### `t5-mode-strategy.md` sub-ranges (verified this session)

| Range | Content |
|---|---|
| `:115-116` | End of §3.3 `manual_legacy` definition |
| `:118-126` | §3.4 "Boundary Notes" — mode describes ownership not transport, not evidence quality |
| `:127-147` | §3.5 `mode_source` for `agent_local` — opens at :129 "For `agent_local` dialogue outcomes, `mode_source` is `null`", then 4-point rationale ending at :147 |
| `:148-160` | §3.5 continues with "Operational consequences" — 3 bullets covering normal termination, error termination, abandoned-loop-before-start (`:157` says that's `manual_legacy` not `agent_local`) |
| `:161` | Blank |
| `:162` | `## 4. T-04 Candidate Classification` header |
| `:193` | `## 6. Primary Migration Set` header |
| `:195` | Intro sentence: "If T5 chooses `agent_local`, the primary migration set is:" |
| `:197-198` | Table header |
| `:199-205` | Seven table rows (2 normative contract, 1 schema, 1 producer contract, 3 test enforcement) |
| `:206` | Blank transition line |
| **`:118-160`** | **Extended canonical shape authority range — what the user tightened TO.** Includes §3.4 + complete §3.5. |

### Patch diff summary (what actually landed)

Per `git diff`:
- `:3` — Two filename updates in Scope line
- `:71-74` → `:71-74` — Done-when paragraph reformatted (line wrapping)
- `:76-93` → `:76-107` — Major replacement (consolidation block → ownership correction)
- `:123-135` → `:137-144` — Mode migration paragraph rewrite
- `:143` → `:164` — Verdict table Gate action row
- `:146-159` → `:167-181` — Disposition block replacement

Total insertions: 23 lines (164 → 187).

## Context

### Mental model for this session

**Framing:** This session is the verification leg of a two-leg exchange
where the user writes substantive amendments and Claude verifies them.
Leg 1 was the prior session's matrix production. Leg 2 is the patch:
user drafts → Claude verifies draft → user applies → Claude scrutinizes
applied patch.

**Core insight:** The user's workflow treats scrutiny as actionable, not
advisory. Two "optional" tightenings I flagged as non-blocking were both
applied by the user. Future verification passes should assume flagged
items are recommendations regardless of my severity labeling.

**Second insight:** The scrutiny discipline is at its most useful when
applied to the user's own framing, not just to Claude's. Finding 1 (the
implicit F6/F7/F11 ownership assignment to T4) is a criticism of the
user's Call 2 reframe that the patch encodes. The scrutiny isn't
"checking Claude's work" — it's checking the resulting artifact,
regardless of whose reasoning shaped it.

**Third insight:** The scope-displacement pattern has a recursive
structure. The original T6 review overstated T6's ownership (scope
displaced from T7). The correction fixes that but introduces a new
implicit claim (F6/F7/F11 owned by T4 by inference). The same pattern
reproduces one level up — both the error and the fix have implicit
ownership claims that aren't backed by gate tables.

### Project state

T4 closed at SY-13. T5 designs accepted. Benchmark contract has Path-2
constraint. T6 composition check reached "Minor revision" verdict with
ownership adjudication correction patch applied (but not committed).
Audit state: F6/F7/F11 unresolved, now explicitly reassigned to T4
authority set by the review (though this assignment is itself flagged
as implicit by this session's scrutiny). T7 state: scope clarified
(consumer implementation only, not spec authoring), still blocked on
audit resolution.

### Environment

Working directory: `/Users/jp/Projects/active/claude-code-tool-dev`.
Branch: `chore/track-t6-review` (2 commits ahead of main; 1 unstaged
modification). Main: 6 commits ahead of origin. No pushes this session.
No tests run (docs-only changes).

## Learnings

### Flagged recommendations are treated as actionable regardless of severity

**Mechanism:** The user's verification-to-apply loop treats any
flagged item as worth addressing. I labeled two tightenings as
"optional minor looseness items (not blocking)" — the user applied both
in the landed patch. The tightening labels didn't affect application
probability.

**Evidence:** Session Phase 5 flagged `benchmark-readiness.md:34-38 →
:35-36` and `t5-mode-strategy.md:118-147 → :118-160` as optional. Phase 6
confirmed both tightenings landed at all three locations for :35-36 and
at `:101` for :118-160.

**Implication:** Future verification passes should frame findings
directly without hedging severity. If I wouldn't recommend applying a
fix, I shouldn't flag it. If I would, I should say so without "optional"
softening. This user reads every flagged item as a recommendation.

**Watch for:** The inverse risk — flagging items Claude wouldn't
actually apply in its own work. That would inflate the user's workload.
The test is: would I apply this fix if I were doing the work? If yes,
flag as recommended. If no, don't mention it.

### Scope-displacement has a recursive structure

**Mechanism:** The T6 review's original scope error (overstating T6's
ownership of T7/T5 work) was fixed by the adjudication correction. But
the correction introduces a new implicit scope claim (F6/F7/F11 owned
by T4 authority set) that has the same failure class: ownership asserted
by inference, not by gate table assignment. The scope-displacement
pattern repeats one level up.

**Evidence:** Scrutiny Finding 1 identified the pattern. The disposition
at `:173-176` says *"audit findings F6/F7/F11 are producer-side spec
gaps in the T4 provenance/state-model authority set."* The claim is
true as a statement of where the gaps live, but is read as an ownership
assignment — which no normative doc makes. The prior handoff's Open
Question #2 ("Who owns F6/F7/F11 remediation?") was unanswered when this
session opened; the patch now implies an answer without authorizing it.

**Implication:** When a correction fixes a scope error, the correction
itself must be checked for new scope claims. Every "the work belongs
to X" statement should be backed by a gate table reference. If the gate
tables don't say, the claim is an inference and should be labeled as
such.

**Watch for:** Language like "these are spec gaps in the T4 authority
set" — true but read as "T4 owns remediation." Tighter phrasing: "these
spec gaps remain without assigned remediation ownership; they target
T4-authored docs and must be resolved before the affected wire formats
can be canonized."

### Load-bearing claims in table cells are structurally underserved

**Mechanism:** Tables are good for structured comparison (parallel rows
with parallel semantics) but poor for surfacing items with fundamentally
different semantics from their peers. Row 5 of the corrected ownership
map (the orphan) has different semantics than rows 1-4 (unassigned vs
owned), but the table format flattens the distinction into "just
another row."

**Evidence:** Scrutiny Finding 4 — the orphan is buried in the table at
`:102` and the disposition at `:167-181` doesn't surface it. A reader
navigating via headers and paragraphs could miss that one row in the
ownership map demands different action from the others.

**Implication:** When a table row represents fundamentally different
semantics than its peers, promote the claim to prose in the surrounding
text. Tables are structure; prose is emphasis. Load-bearing claims
should use both.

**Watch for:** Any situation where 4 out of 5 rows (or similar majority)
have parallel semantics and one row breaks the pattern. That outlier
row needs prose treatment.

### Scrutinize discipline reveals implicit assertions that explicit ones would eliminate

**Mechanism:** The "unforgiving reviewer" framing forces examination of
every asserted claim for backing. Implicit claims (where backing is
obvious-to-author but not stated) fail this test because the reviewer
can't verify what isn't written.

**Evidence:** Scrutiny Findings 1 and 6 — both cases where a stronger
form of the claim would be defensible without materially enlarging the
patch. Finding 1: the F6/F7/F11 placement could be explicit ("T4
authority set by inference; not yet in any gate table") with one
caveat. Finding 6: the adjudication principle could cite
`benchmark-readiness.md:87` as the specific shape conflict it resolves.
Both cost ~1 sentence each; both are left implicit.

**Implication:** When applying scrutiny discipline, look for places
where 1 more sentence would make an implicit claim explicit. These are
the cheapest improvements to text quality.

**Watch for:** The author (or verifying Claude) thinking "everyone knows
what I mean" about a claim. If it's not written, a hostile reviewer
can't verify it, and neither can future-Claude.

### Patterns-and-root-causes identification has more value than individual findings

**Mechanism:** Scrutiny findings are often symptoms of a common cause.
Calling out the pattern makes the fix easier to generalize. In this
session's scrutiny, two patterns (load in table cells; implicit claims
where explicit ones would cost little) covered 4 of 6 findings. Both
traced to the same root cause: the patch author minimized additions to
avoid scope creep.

**Evidence:** Scrutiny report's "Patterns and root causes" section
identified both patterns with the single root cause. Without the
pattern identification, the findings would read as 6 independent issues;
with it, they read as 2 correctable tendencies.

**Implication:** Always include the patterns section in scrutiny
reports. It shifts the fix from "address these 6 items" to "address
this 1 tendency across the document."

**Watch for:** Findings that are genuinely independent vs findings that
share a structural cause. If findings cluster around a theme, name the
theme.

## Next Steps

### 1. User responds to the 6 scrutiny findings (next session opener)

**Dependencies:** None — this is what the user explicitly committed to.

**User's verbatim direction:** *"I will respond to your review in the
next session."*

**What the user is likely to address:**

- **Finding 1 (Medium)** — F6/F7/F11 implicit ownership assignment.
  The scrutiny criticizes a claim that the user's own Call 2 reframe
  put into the patch. User will need to decide whether to: (a) soften
  the claim to "producer-side spec gaps targeting T4-authored docs;
  remediation ownership not yet assigned in any gate table," (b) defend
  the claim by adding a caveat that makes it explicit, or (c) push back
  on the finding itself. This is the most interesting finding.

- **Finding 3 (Medium)** — Truncated failure paths paragraph. Fix is
  one sentence at `:79` bridging to the ownership map. Low effort, high
  readability gain. User will likely apply this unless they disagree.

- **Finding 4 (Medium)** — Orphan row buried in table. Fix is one
  sentence in the disposition at `:167-181` surfacing the orphan. Also
  low effort.

- **Findings 2, 5, 6 (Low)** — Polish items. User may apply or skip.
  Based on the pattern that "flagged = actionable," I expect them to be
  applied.

**Acceptance criteria:** User delivers their verdict on each finding.
Either agreement + applied fixes, or counter-arguments + defended
positions. The session closes with the patch in a "ready to commit"
state.

### 2. Commit the corrected patch (after finding responses)

**Dependencies:** Finding responses (Next Step 1).

**Work to do:** Once the scrutiny findings are addressed, commit the
patch on `chore/track-t6-review`. Commit message following repo pattern:

```
docs(reviews): correct T6 ownership framing via adjudication correction

Amend the T6 benchmark-first design composition review to correct an
overstated T6 ownership claim. T7 owns the four consumer-facing
wire-format surfaces (claim_provenance_index, Claim Ledger, not_scoutable
in claim/evidence trajectories) per benchmark-readiness.md T4-BR-04/05.
T5 owns agent_local specification surfaces per T4-BR-01. The original
"T6 consolidation artifact" table is superseded by the adjudication
correction; T6's composition verdict is preserved.
```

**Acceptance criteria:** `git status` clean on `chore/track-t6-review`;
branch is 2 commits ahead of main (tracking + correction).

### 3. Decide on pushing `chore/track-t6-review` or merging locally (still open from prior handoff)

**Dependencies:** Committed correction (Next Step 2).

**Options:**
- Push as PR to origin
- Merge to main locally (bypass PR review for solo work)
- Hold the branch until a larger batch of T6/T7 work is ready

**Decision is the user's.** Not acted on this session.

### 4. Address F6/F7/F11 ownership assignment in benchmark-readiness.md (project-level open question)

**Dependencies:** None structurally, but user may want the patch
committed first.

**Work to do:** Per Scrutiny Finding 1, the F6/F7/F11 placement is
currently an inference. A `benchmark-readiness.md` amendment that
explicitly assigns remediation ownership (to T4, or to a new remediation
packet, or with gating language) would resolve the Open Question and
close the loop on Call 2.

**Acceptance criteria:** F6/F7/F11 have explicit owners in a gate table,
or have explicit "no current owner" declarations with trigger conditions
for assignment.

## In Progress

**Uncommitted patch.** The adjudication correction is applied to the
working tree but not committed. `git status` shows:

```
On branch chore/track-t6-review
Changes not staged for commit:
    modified:   docs/reviews/2026-04-04-t04-t6-benchmark-first-design-composition-review.md
```

**Approach:** User applied the full draft in Phase 6, including the two
downstream fixes I flagged and both "optional" tightenings. The patch is
mechanically complete and correct in substance. The 6 scrutiny findings
are refinements, not blockers.

**State:** Patch applied, scrutiny delivered, awaiting user response.

**Working:** All file:line citations verify; all replacement blocks
landed at correct locations; no stale references to "T6 consolidation
artifact" outside intentional supersession context; diff is bounded to
the single review file.

**Not working:** 6 scrutiny findings (3 Medium, 3 Low) remain
unaddressed. Patch is uncommitted pending finding response.

**Open question:** How user will respond to Finding 1 specifically —
it's the most interesting because it criticizes the user's own Call 2
reframe that the patch encodes.

**Next action (user's, not mine):** User reads scrutiny report, decides
which findings to address, applies fixes or defends positions, commits.

## Open Questions

1. **How will the user respond to Scrutiny Finding 1?** The implicit
   F6/F7/F11 ownership assignment to T4 is a criticism of the user's
   Call 2 reframe. Options: soften the claim, defend it explicitly,
   push back on the finding. This is the session's most substantive
   open question.

2. **Will the user apply all 6 findings or selectively?** The pattern
   from this session (user applied both "optional" tightenings) suggests
   all 6. But the Medium findings require more judgment than the Low
   findings.

3. **Who owns F6/F7/F11 remediation officially?** Still unresolved in
   any gate table. The patch encodes an implicit T4 placement; the
   scrutiny questions it; no normative doc has made the assignment.

4. **Should Scrutiny Finding 6 (adjudication principle without example)
   be addressed by adding a benchmark-readiness.md:87 citation?** This
   would make the principle concrete but also embeds a citation to
   informal phrasing the canonical spec contradicts. Meta-question: does
   adding the citation help or entrench the informal phrasing?

5. **Does the "DOES NOT YET COMPOSE" header need revision?** The
   scrutiny's premise-check flagged tension between "yet" (implying T6
   will fix) and the disposition (T6 won't own the fix). User may
   accept this tension as deliberate or revise the header.

## Risks

1. **Finding 1 pushback creates a recursive verification loop.** If the
   user defends the F6/F7/F11 placement on the grounds that "the gaps
   live in T4 specs, so T4 must own remediation by inference," the
   scrutiny would need to rebut: "inference isn't assignment; the gate
   tables don't say." This could loop. Mitigation: the scrutiny report
   already proposes two concrete fixes (soften the claim OR add an
   explicit caveat); user can pick one without a philosophical debate.

2. **Uncommitted state risk.** The patch is in working tree only.
   A session crash, branch switch, or accidental stash could lose the
   work. Mitigation: user knows the state (flagged in their `/scrutinize`
   arguments as a remaining risk); this handoff documents the full patch
   content so it could be reconstructed if lost.

3. **Scrutiny may have missed issues.** Six findings is bounded; an
   unforgiving reviewer on a second pass might find more. Mitigation:
   the scrutiny explicitly applied 5 adversarial perspectives and two
   pass discipline; it's more thorough than a first-pass review.

4. **Call 2's reframe may be wrong.** If F6/F7/F11 actually belong to T7
   (because T7 is the consumer that needs the spec clarified), then
   Call 2 is wrong, the correction encodes the wrong ownership, and the
   patch itself needs further revision. Mitigation: the scrutiny Finding
   1 already flags this as an implicit claim; resolution would go
   through a gate-table amendment anyway.

5. **Scope-displacement pattern continues.** This is the 5th+ iteration
   where scope-displacement has appeared in T6 analysis work. Each
   iteration is caught, but the pattern keeps reappearing. Mitigation:
   The recursive structure (correction itself has displacement) is now
   documented in this session's Learnings; future sessions should
   anticipate it.

## References

| What | Where |
|---|---|
| T6 review doc (uncommitted patch) | `docs/reviews/2026-04-04-t04-t6-benchmark-first-design-composition-review.md` |
| T6 review "Adjudication correction" block | Same file, `:84-92` |
| T6 review "Corrected ownership map" table | Same file, `:96-102` |
| T6 review disposition (post-patch) | Same file, `:167-181` |
| Mode migration paragraph (updated) | Same file, `:137-144` |
| T6 Verdict table (updated row) | Same file, `:160-165` |
| T4-BR-01 agent_local ownership (tightened citation) | `benchmark-readiness.md:35-36` |
| T4-BR-04 provenance index ownership | `benchmark-readiness.md:79-90` |
| T4-BR-05 synthesis format updates ownership | `benchmark-readiness.md:92-102` |
| ClaimRef wire format (exact) | `state-model.md:180-182` |
| T4-SM-05 EvidenceRecord schema (8 fields) | `state-model.md:184-221` |
| §3.4 mode ownership definition | `t5-mode-strategy.md:118-126` |
| §3.5 mode_source for agent_local | `t5-mode-strategy.md:127-160` |
| §6 Primary Migration Set (7 rows) | `t5-mode-strategy.md:195-205` |
| Canonical wire format (dense array) | `provenance-and-audit.md:84-90` |
| Audit P1 F6 (concession boundary) | `docs/audits/2026-04-02-t04-t4-evidence-provenance-rev17-team.md:141-148` |
| Audit P1 F7 (serialization handoff) | Same file, `:152-164` |
| Audit P1 F11 (schema versioning) | Same file, `:216-228` |
| Prior handoff (archived) | `docs/handoffs/archive/2026-04-04_23-34_t6-t7-ownership-resolution-per-surface-status-matrix.md` |
| Tracking commit (from prior session) | `40e30b2c` on `chore/track-t6-review` |
| Archive commit (this session) | `13ef3b92` on `chore/track-t6-review` |
| Uncommitted correction | Working tree modification to T6 review doc |

## Rejected Approaches

### Softening the scrutiny findings to avoid tension with Call 2

**Approach:** Phrase Finding 1 as "minor wording consideration" or
remove it from the Medium tier, to avoid criticizing a claim the user
made in Call 2.

**Why it seemed tempting:** Finding 1 criticizes the user's own framing.
The user has explicitly called out scope-displacement as a recurring
failure mode, and Finding 1 essentially says "Call 2 has the same
failure class one level up." There's interpersonal tension in that
critique.

**Why rejected:** The scrutinize skill explicitly mandates *"Do not
soften findings with hedging unless uncertainty is genuinely
unavoidable."* The user's workflow welcomes hard feedback and applies
it; softening would be dishonest. Also: the finding stands on its
merits — the F6/F7/F11 placement is an inference, not a gate-table
assignment, and that's verifiable independent of who first made the
inference.

**What I learned:** Scrutiny discipline is at its most useful when
applied evenly to everyone's reasoning, including the user's. The test
is always "is this claim backed by evidence?" — not "whose claim is
this?"

### Verdict "Defensible" instead of "Minor revision"

**Approach:** Call the patch "Defensible" (no material issues, ship it)
rather than "Minor revision" (worth addressing findings before commit).

**Why it seemed tempting:** The patch is mechanically correct. All
citations verify. The two downstream issues from Phase 5 were caught
and fixed. The core correction is substantively right. From 30,000
feet, this looks like a successful patch.

**Why rejected:** Finding 1 (implicit F6/F7/F11 ownership), Finding 3
(truncated failure paths paragraph), and Finding 4 (orphan in table)
are all real issues that materially affect how the correction reads.
They're not critical, but they're not cosmetic either. "Defensible"
would have been an evasion.

**What I learned:** The line between "Minor revision" and "Defensible"
is whether flagged findings meaningfully affect the artifact's
utility. In this case, yes — an ambiguous F6/F7/F11 placement could
propagate into future planning work.

### Verdict "Major revision" for the same patch

**Approach:** Call the patch "Major revision" to emphasize the
scope-displacement pattern recurring at one level up.

**Why it seemed tempting:** The recursive structure (correction itself
has displacement) is a significant finding. "Major revision" would
signal its weight.

**Why rejected:** The verdict levels map to effort, not importance.
Major revision means "this needs substantial rework." The patch doesn't
need substantial rework — it needs ~4 sentences added and 1 phrase
tightened. That's minor effort for a meaningful improvement, which is
exactly what "Minor revision" means.

**What I learned:** Verdict calibration should reflect effort required,
not the intellectual weight of the findings. A finding can be important
AND require minimal fix effort.

## Gotchas

1. **The patch is uncommitted.** All the work described in this session
   lives in working tree only. `git status` shows
   `M docs/reviews/2026-04-04-t04-t6-benchmark-first-design-composition-review.md`.
   Commit does not happen until next session after user responds to
   scrutiny findings.

2. **Flagged items are actionable regardless of severity labels.** User
   applied both "optional minor looseness items" in Phase 6. Future
   verification passes should assume any flagged item will be addressed.
   Do not flag things you wouldn't fix yourself.

3. **`benchmark-readiness.md:35-36` is narrower than
   `benchmark-readiness.md:34-38`** — the first is just the
   dialogue-synthesis-format.md documentation rows; the second is the
   full T4-BR-01 table. When the prose says "documentation," use
   `:35-36`. When the prose says "the full T5 ownership set," use
   `:34-38`.

4. **`state-model.md:180-182` is the ClaimRef wire format declaration
   (exactly 3 lines).** The surrounding T4-SM-04 section is
   `:168-182`. Do not cite the whole section when pointing at the wire
   format specifically.

5. **`t5-mode-strategy.md:118-160` includes §3.4 + complete §3.5.** The
   tighter range `:118-147` cuts before operational consequences. User
   expanded to `:118-160` in this session's patch.

6. **"Producer-side spec gaps" is undefined jargon** that appears once
   in the patched disposition at `:173`. It contrasts implicitly with
   "consumer-side" but no definition exists. Scrutiny Finding 2 flags
   this.

7. **The disposition does not surface the evidence-trajectory
   projection orphan** from the corrected ownership map row 5. A reader
   who only reads the disposition misses that row 5 has unassigned
   ownership. Scrutiny Finding 4 flags this.

8. **"DOES NOT YET COMPOSE" header has rhetorical friction with the
   disposition.** Header implies "T6 will eventually compose"; disposition
   says "T6 won't own the composition." Premise-check observation from
   scrutiny, not a finding.

9. **Finding 1 is a self-referential scope-displacement criticism.**
   The user's Call 2 reframe (F6/F7/F11 to T4) is itself subject to the
   same scope-displacement critique that the T6 review correction fixes.
   This is a real pattern, not a gotcha.

10. **Uncommitted work is visible to the branch-protection hook but not
    blocked.** `chore/track-t6-review` is an allowed branch; edits work
    fine. No hook concerns.

## Conversation Highlights

**The three calls framing (Phase 2):**

User: *"That matrix is the right artifact. I would not replace it."*

This opening statement was load-bearing. It told me the matrix was not
the session's concern; the session's concern was what to do about it.
Then the three calls followed.

**Call 1 (Correct T6 review now):**

User: *"Correct the T6 review now, but do it as an explicit adjudication
correction, not a silent rewrite of history. The ownership error in [T6
review doc] is already proven against [benchmark-readiness.md]. Waiting
for F6/F7/F11 does not change that. Leaving the review artifact
uncorrected keeps a false ownership map in the repo and invites the same
mistake again."*

The framing "explicit adjudication correction, not a silent rewrite of
history" is worth preserving — it names a review-discipline pattern.
Silent rewrites update text to match new understanding without marking
what was corrected; adjudication corrections preserve the original
state and explicitly mark what's being amended.

**Call 2 (F6/F7/F11 to T4 authority set):**

User: *"F6/F7/F11 should be driven by the T4 provenance/state-model
authority set, not by T7. Those findings are design-contract gaps in
[provenance-and-audit.md] and adjacent normative material, not benchmark
harness implementation tasks. T7 is the consumer/gate owner. It should
not be forced to invent concession representation, serialization
handoff, or versioning policy while implementing consumers."*

This reframe is the session's most substantive user contribution. It
resolves the prior session's Open Question #2 ("Who owns F6/F7/F11?")
by pushing ownership back one level from consumer to producer.

**Call 3 (Defer Surface 5):**

User: *"Do not land Surface 5 as a spec-only isolated commit yet. It is
the only semantically stable surface, but the payoff is low and the
mismatch is real."*

The "payoff is low and the mismatch is real" framing is a useful
two-factor test: spec-only landings need to clear both bars (high
enough payoff to justify the work AND low enough mismatch risk to avoid
confusion).

**Draft offer (Phase 2 closing):**

User: *"If you want the next step from me, the highest-signal one is
drafting the exact correction language for the T6 review artifact only,
with no broader plan and no implementation checklist. Let me know if I
should do this."*

The phrasing "the next step from me" (not "from you") was clear once I
noticed it — the user was offering to draft themselves, asking for
confirmation. I confirmed.

**Branch answer and full draft (Phase 4):**

User: *"Keep it on `chore/track-t6-review` as a second commit. Reason:
`40e30b2c` is only on that branch, not on `main` (`git branch --contains
40e30b2c` returns only `chore/track-t6-review`). This correction amends
the same review artifact, not the normative contracts the review
evaluates."*

The user verified the branch reasoning empirically (with `git branch
--contains`) before committing to the answer. This is the same
evidence-backed pattern the user applies to all decisions.

**Patch report (Phase 6):**

User: *"Applied the adjudication-correction patch to [T6 review] on
`chore/track-t6-review`."* Response Contract format with What changed /
Why / Verification / Remaining risks. Explicit list of 5 changes.

User's "Remaining risks": *"The branch is still uncommitted:
`chore/track-t6-review` with one modified file."*

The user self-flagged the uncommitted state as a remaining risk, which
suggests they're tracking it and will commit after the scrutiny
response.

**Scrutinize direction:**

User invoked `/scrutinize` with explicit arguments that passed the
patch summary as context. The skill runs with the "unforgiving
reviewer" mandate. I applied it.

**Save direction:**

User: *"save a handoff. I will respond to your review in the next
session."*

Explicit direction for what happens in the next session. The handoff
must preserve all 6 findings with enough substance to drive the
response.

## User Preferences

**Treats scrutiny as actionable, not advisory.** Two "optional"
tightenings I labeled as non-blocking (Issues 5 and 6 of the verification
pass) were both applied in the patch. Flagged items become
recommendations regardless of severity labels.

**Delivers directions as decisions, not questions.** The three calls
were phrased as "correct the T6 review," "F6/F7/F11 should be driven
by...," "do not land Surface 5" — imperative mood, not interrogative.
When user asks questions, they're logistical (branch) not substantive.

**Uses verbatim evidence-backed reasoning.** Every substantive claim
cites a specific source or verifiable fact. Call 2 cites
`provenance-and-audit.md` by name; Call 3 cites benchmark runtime state
("nothing emits agent_local today"); branch answer cites
`git branch --contains` output.

**Uses Response Contract format for reporting implementation work.** The
format from their global CLAUDE.md (What changed / Why / Verification /
Remaining risks) is the user's default for code or doc changes. When
they use it, they're signaling "apply verification rigor to this."

**Invokes `/scrutinize` for adversarial review discipline.** Not for
generic review — specifically for unforgiving quality assessment. The
skill's framing ("assume not ready, prove it") is what the user wants
applied.

**Writes substantive amendments themselves.** User delivered the full
draft for both replacement blocks in Phase 4. Claude's role is
verification and scrutiny, not drafting.

**Pre-flags self-identified concerns in their reports.** User's patch
summary in Phase 6 included "Remaining risks: the branch is still
uncommitted" — signaling awareness without asking for action. This
pattern lets me skip defensive "have you noticed X?" questions.

**Applies every actionable verification finding.** Phase 6's patch
incorporated all 3 of my Phase 5 structural fixes (2 required +
`:71` filename update) plus both "optional" tightenings. Zero findings
were skipped. Future sessions should expect this pattern.

**Sequencing language is explicit.** User uses "2 first, then 1" or
similar ordering callouts when correcting my default order. In this
session, they didn't need to correct ordering because the three calls
were delivered in decision order (correction first, F6/F7/F11
reframe second, deferral third).

**Prefers branch-semantic clarity over git efficiency.** User verified
the branch answer empirically before committing to same-branch placement
instead of "just picking one." The branch name must match the work's
semantic type — chore for housekeeping, correction for adjudication
amendments (still review-artifact scope).

**Verdict directness.** User accepts "Reject / Major revision / Minor
revision / Defensible" verdict categories from scrutiny. No hedging
expected or wanted. When the user accepts, they apply; when they
disagree, they push back explicitly.

**Closes sessions with explicit next-session direction.** This session
closed with "I will respond to your review in the next session." Prior
session closed with "save a handoff; I will review the draft." The
pattern: user states what they'll do, Claude saves the handoff with
that state preserved, next session begins with the declared action.
