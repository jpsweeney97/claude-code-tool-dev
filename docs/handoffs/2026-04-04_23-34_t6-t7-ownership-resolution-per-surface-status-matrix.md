---
date: 2026-04-04
time: "23:34"
created_at: "2026-04-05T03:34:58Z"
session_id: 063a8cbe-ec2e-439b-bec0-56a7ab026392
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-04_14-56_t6-composition-analysis-four-review-passes.md
project: claude-code-tool-dev
branch: chore/track-t6-review
commit: 40e30b2c
title: T6/T7 ownership resolution and per-surface status matrix
type: handoff
files:
  - docs/reviews/2026-04-04-t04-t6-benchmark-first-design-composition-review.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/benchmark-readiness.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/provenance-and-audit.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/state-model.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/boundaries.md
  - docs/plans/2026-04-02-t04-t5-mode-strategy.md
  - docs/audits/2026-04-02-t04-t4-evidence-provenance-rev17-team.md
  - packages/plugins/cross-model/references/dialogue-synthesis-format.md
  - packages/plugins/cross-model/scripts/emit_analytics.py
  - packages/plugins/cross-model/scripts/event_schema.py
  - packages/plugins/cross-model/skills/dialogue/SKILL.md
  - packages/plugins/cross-model/agents/codex-dialogue.md
  - packages/plugins/cross-model/HANDBOOK.md
---

# Handoff: T6/T7 ownership resolution and per-surface status matrix

## Goal

Resume the T6 composition check from the prior session, verify the last fix the
user applied to the review doc, then carry forward to T6 closeout. The prior
handoff's first next step was "User reviews T6 analysis draft and shares
findings." The user arrived with a completed fix (not a new review pass) and
the intent to move toward consolidation work.

**Trigger:** The prior session ended at "Minor revision" after four adversarial
review passes. The user committed to one more targeted fix (narrowing T3's role
in the dead-referent path) and stated in the prior handoff: *"I will review
this draft and then share my findings in the next session."*

**Stakes:** High. T6 is the design gate between accepted T1-T5 designs and T7
(executable slice). Moving past T6 prematurely — or through a misframed
consolidation — would push design bugs into implementation. The session's real
stakes became visible mid-session when the user's rejection of the consolidation
prep map revealed that the T6 review artifact itself is overstating T6's
ownership of work that normative docs assign to T7.

**Success criteria (revised mid-session):** Not "start consolidation work." The
session pivoted to resolving a prerequisite question: who owns the
synthesis-format updates (T6 vs T7), and what blocks them (three open audit
P1s). Produced a per-surface status matrix as the analysis artifact under
unresolved state.

**Connection to project arc:** T4 close-out → reclassification → Path-2
benchmark constraint → T6 composition (3 review passes in prior-prior session)
→ T6 composition (4 review passes in prior session, reached "Minor revision")
→ **T6 review-doc fix + ownership resolution (this session)** → T7 executable
slice (blocked on audit P1s F6, F7, F11 that must resolve before wire-format
work can proceed).

## Session Narrative

### Phase 1: Load and fix verification

Loaded the prior handoff via `/load`. Archived it to
`docs/handoffs/archive/2026-04-04_14-56_t6-composition-analysis-four-review-passes.md`
(commit `0b8f6a9f`) and created the session state file. Read the archived
handoff to pick up context — seven review passes total across two sessions,
"Minor revision" verdict, one remaining T3/T4 table contradiction flagged.

The user opened the session by reporting a completed fix in the
**Response Contract format** from their global CLAUDE.md (*What changed / Why
/ Verification / Remaining risks*). Two surprises emerged:

1. **The file had moved.** The prior handoff referenced
   `docs/notes/t6-composition-check-analysis.md`, but the user cited
   `docs/reviews/2026-04-04-t04-t6-benchmark-first-design-composition-review.md`.
   Verified via `ls`: the notes file no longer exists; the reviews file is
   19966 bytes, untracked, modified at 22:33. The user had graduated the
   working draft from `notes/` to `reviews/` between sessions. This is a
   convention signal in this repo (note → review = promotion from working
   draft to decision artifact of record).

2. **The fix was specific.** First column of the summary table at line 11 now
   reads "Case entering T4" (previously a framing that conflated T3/T4
   ownership). Dead-referent rows explicitly say "Dead referent after T3
   acceptance" and name Phase 1.5 as the reclassification step.

Verified the fix against three sources in parallel:
`docs/plans/2026-04-02-t04-t3-deterministic-referential-continuity.md:160-200`,
`docs/plans/t04-t4-scouting-position-and-evidence-provenance/state-model.md:80-160`,
and the lifecycle table at `state-model.md:370-400`. All five table citations
matched exactly (`:380`, `:382`, `:386`, `:387`, `:388`). Ran a file-wide grep
for T3/T4 concept carriers to check for residual conflation elsewhere — none
found. The fix was clean.

Noted one cosmetic observation: the table row "Revised (live referent, new
occurrence)" cites `:380` only (scoutable variant), not `:381` (not-scoutable
variant), creating an asymmetry versus the dead-referent rows which distinguish
both. Flagged as below-the-threshold and not a finding.

### Phase 2: Branch strategy decision and tracking commit

The user decided "Option 2 first, then Option 1" — track the review artifact
first, then do consolidation prep. Reasoning:

> "The review artifact is settled now. Leaving [the review doc] untracked
> while starting consolidation work creates an unnecessary coupling: the
> accepted review state can drift at the same time as the synthesis-contract
> edits it is evaluating."

I accepted the git work. Verified state, proposed the plan (branch name
`chore/track-t6-review`, single file, commit message following repo pattern),
executed the chained command:
`git checkout -b chore/track-t6-review && git add <file> && git commit && git log -1 && git status`.

Result: commit `40e30b2c`, 164 insertions, working tree clean.

### Phase 3: Consolidation prep map production and delivery

Built what I called a "consolidation prep map" — a detailed mapping of 5
surfaces (EvidenceRecord, claim_provenance_index, Claim Ledger, not_scoutable,
agent_local) to specific target locations in `dialogue-synthesis-format.md`.
Read 4 files in parallel to build it: the target doc (236 lines, entire),
`provenance-and-audit.md:1-170`, `t5-mode-strategy.md:180-250`, and grepped
`boundaries.md` for T4-BD-02.

Delivered the map as a per-surface breakdown with "Source", "Where it lands in
the target", "Merge action", and "Scope" for each of the 5 surfaces. Included
cross-cutting observations (line-9 "7 items" hardcoding, frontmatter absence,
section numbering drift) and proposed two modes: "user edits from map, Claude
verifies" vs "Claude drafts diffs, user reviews." Recommended a hybrid
(mechanical surfaces by Claude, semantic framing by user).

### Phase 4: The rejection

The user returned with a structured adversarial review:

- **Verdict:** Reject.
- **4 Critical failures:** T6 vs T7 ownership contradiction; `claim_provenance_index` consumer path drops the field; unhandled "Do not include raw ledger entries" collision at line 233; wire formats unsafe to freeze due to open P1 audit findings (F7, F11 cited).
- **4 Fragile assumptions:** EvidenceRecord schema location wrong; dense-array-vs-keyed confusion; example already incomplete; mode wording semantically sloppy.
- **3 Real-world breakpoints:** External citations to "7 items"; `not_scoutable` semantics ambiguity; ledger-completeness checklist as compliance theater.
- **2 Hidden dependencies:** `SKILL.md` relay guidance; `HANDBOOK.md` as contract hub.
- **Branch recommendation weak** (chore/ advertises housekeeping for a normative contract change).
- **8 items** that must change before the map is credible.

The user's closing framing captured what was wrong at a root level:
*"This map is not trustworthy as a consolidation plan. It confuses ownership,
undercounts active consumers, hardens a wire-format surface that prior review
already flagged as unsafe, and misses at least one direct self-contradiction
in the target doc. It reads like a local editing checklist for a change that
is actually cross-contract work."*

### Phase 5: Verification pass and acceptance

Invoked the `superpowers:receiving-code-review` skill per the rule that
structured review feedback requires verification, not performative agreement.

Dispatched 10 parallel reads to verify every cited file:line: `benchmark-readiness.md:1-160`,
`state-model.md:170-260`, `t5-mode-strategy.md:100-190`, `emit_analytics.py:270-450`,
`event_schema.py:1-160`, `audit file:140-240`, `provenance-and-audit.md:170-250`,
`codex-dialogue.md:490-520`, `SKILL.md:375-455`, `HANDBOOK.md:820-860`.

**14 of 14 findings confirmed.** Plus discovered audit F6 at
`2026-04-02-t04-t4-evidence-provenance-rev17-team.md:141-148` as a third
adjacent P1 finding on the same wire formats (user cited F7 and F11 only,
but F6 reinforces CF4).

Withdrew the map. Produced a finding-by-finding verification response with
evidence from every read. The deepest error was CF1 — I treated the T6
review's consolidation artifact as authoritative without checking whether
`benchmark-readiness.md` T4-BR-04 / T4-BR-05 agreed. They don't. Both
authoritative normative docs assign those synthesis-format updates to T7,
while the T6 review places them in T6 consolidation. **The contradiction is
Ø-order — my map was building on top of it without flagging it.**

Proposed three ownership resolutions:
- **Option 1:** T6 review wins, benchmark-readiness amended (T7 rows → T6).
- **Option 2:** benchmark-readiness wins, review narrowed (T6 rows → T7).
- **Option 3:** Split packet — T7 owns wire-format surfaces, T5 owns `agent_local`, T6 owns only the review-framing correction.

Recommended Option 3 based on the open P1 audit findings: the wire format
cannot be canonized until F6/F7/F11 resolve, and moving to T7 aligns ownership
with where the unresolved work actually lives.

### Phase 6: Decision and matrix production

The user chose **Option 3 with a refinement** that reframed the problem more
precisely than I had: *"ownership follows benchmark-readiness, semantic shape
follows the canonical provenance/state-model specs."* This split is
load-bearing — `benchmark-readiness.md` is a gate-ownership doc, not a shape
doc, and its informal phrasings (like `:87`'s "`claim_id`-keyed schema") must
not override `provenance-and-audit.md:84-90`'s unambiguous "Dense JSON array"
specification. I had not noticed this distinction.

The user also directed: *"Do NOT step back entirely until F6/F7/F11 resolve.
... The matrix is the right artifact for unresolved state. It does not
pretend the work is ready to implement; it makes the blockers explicit."*

Accepted the offer to produce the matrix (reading "If you want, I'll produce
that matrix" as the same pattern as the earlier git-work offer — ambiguous
pronoun, proceed-if-sensible). Built a 5-surface × 9-field matrix:

| Field | Purpose |
|---|---|
| Source of truth (shape) | Canonical spec with file:line |
| Ownership authority | `benchmark-readiness.md` with T5/T6/T7 label |
| Open issues | Audit findings, design gaps, downstream collisions |
| Stable to transcribe now? | Binary with justification |
| Producer status | Does any agent currently emit this? |
| Parser status | Does `emit_analytics.py` extract it? |
| Schema status | Does `event_schema.py` validate it? |
| Harness status | Does any benchmark component consume it? |
| Consumer impact if landed early | What breaks or silently drifts |

Key outcomes from the matrix:

1. **Surfaces 1-4 are all blocked.** `claim_provenance_index`, `## Claim Ledger`, and both `not_scoutable` updates are deferred to T7 and blocked on F6/F7/F11. Cannot be transcribed under current audit state.
2. **Surface 5 is stable for spec-only landing.** `agent_local` mode documentation (T5 Primary Migration Set rows 199-200) has no open audits, no downstream coupling, and can land any time — but consumer code still rejects/coerces, so runs remain invalid until rows 201-205 also land.
3. **EvidenceRecord is an orphan.** The T6 review claimed it as a consolidation surface, but it has no corresponding row in `benchmark-readiness.md` T4-BR-04 or T4-BR-05. Ownership is unassigned. Needs review-doc correction.
4. **Transitive dependencies.** Surfaces 1-4 form a coupled block — Surface 2 (Claim Ledger) depends on Surface 1 (`claim_provenance_index`) because `[ref: N]` annotations point into the index. Surface 4 (`not_scoutable` in evidence trajectory) depends on Surface 3 (`not_scoutable` in claim trajectory) for vocabulary symmetry. They cannot be transcribed independently.
5. **Producer status uniformity.** All 5 surfaces have `NOT EMITTED` producer status. The codex-dialogue agent reads `dialogue-synthesis-format.md` verbatim at Phase 3 entry (`codex-dialogue.md:501`), which doesn't mention four of the five surfaces; the fifth (`agent_local`) is coerced away at `SKILL.md:435`. None of this is live traffic — deferral is safe.

Delivered the matrix with cross-cutting observations (benchmark-readiness.md:87 shape phrasing is informal, line 233 collision persists, T4-BR-05:101 transition-vs-terminal conflation, transitive dependency block) and three next decision points (T6 review-correction timing, F6/F7/F11 ownership, Surface 5 spec-only landing).

**Clean stopping point reached.** User runs `/save`.

## Decisions

### Decision 1: Option 3 ownership split with semantic refinement

**Choice:** T7 owns the four consumer-facing wire-format surfaces
(`claim_provenance_index`, `## Claim Ledger`, `not_scoutable` in claim
trajectory, `not_scoutable` in evidence trajectory). T5 owns `agent_local`
mode semantics. T6 owns only the correction to its own review framing. **Plus
refinement:** "ownership follows benchmark-readiness, semantic shape follows
the canonical provenance/state-model specs."

**Driver:** User's verbatim reasoning: *"I would not pick Option 1. It would
canonize surfaces that still have open P1 audit gaps and no live end-to-end
consumer path. I also would not pick Option 2 in the strong form of
'benchmark-readiness wins wholesale,' because benchmark-readiness.md itself
currently says `claim_id`-keyed schema, while provenance-and-audit.md defines
the canonical wire format as a dense array. So the clean resolution is not
'one doc wins'; it is 'ownership follows benchmark-readiness, semantic shape
follows the canonical provenance/state-model specs.'"*

**Alternatives considered:**
- **Option 1 (T6 wins wholesale):** Amend `benchmark-readiness.md` T4-BR-04/T4-BR-05 to move synthesis-format update rows from T7 to T6, matching the review doc's consolidation artifact. **Rejected** because three open P1 audit findings (F6/F7/F11 in `docs/audits/2026-04-02-t04-t4-evidence-provenance-rev17-team.md`) directly target the same wire formats. Canonizing them now regresses stability.
- **Option 2 (benchmark-readiness wins wholesale):** Narrow the T6 review's "Surfaces to merge" table to match `benchmark-readiness.md` ownership. **Rejected** in its strong form because `benchmark-readiness.md:87` uses informal shape phrasing ("`claim_id`-keyed schema") that contradicts the canonical spec at `provenance-and-audit.md:84-90` ("Dense JSON array"). Treating benchmark-readiness as authoritative for shape would regress the wire format at the moment T4-BR-04 is transcribed.

**Implications:**
- Surfaces 1-4 deferred to T7; cannot proceed until F6/F7/F11 resolve.
- Surface 5 (`agent_local`) remains T5 scope and can land in isolation.
- T6 review doc (`docs/reviews/2026-04-04-t04-t6-benchmark-first-design-composition-review.md:83-93`) needs a targeted correction: narrow or remove the "Surfaces to merge" table's T7-owned rows, handle the EvidenceRecord orphan explicitly.
- The split distinguishes ownership authority from shape authority — future analysis must apply this distinction when reading any gate-ownership doc.

**Trade-offs accepted:**
- T6 doesn't "close" with a consolidation artifact. Its disposition remains "remains open pending synthesis contract consolidation," but the consolidation happens downstream in T7, not in T6.
- The wire-format work is held up pending audit resolution. This is the correct outcome — the audit findings are prerequisites for T7, not deliverables of it — but it lengthens the critical path before benchmark runs can produce valid data.
- EvidenceRecord has ambiguous ownership between "T4 declared breaking migration" (T4-BD-01) and "nobody explicitly claims the format-doc update." The review tried to claim it as T6 work; the matrix surfaces this as a review-correction item.

**Confidence:** High (E2) — grounded in two independent sources: the user's explicit reasoning (verbatim quote above) plus the verification pass that confirmed all 14 of the user's critical findings against cited sources. The refinement (ownership vs shape authority) emerged from the user's own reading, not from my map.

**Reversibility:** Medium-High — the split can be reframed by amending either `benchmark-readiness.md` or the T6 review doc. But once T7 begins work under the split, the ownership frame becomes harder to unwind (T7 deliverables depend on audit resolution; reverting to T6 scope would require reopening closed gates).

**What would change this decision:** (1) F6/F7/F11 resolution landing earlier than expected, making the wire formats safe to canonize — in which case the T6 review's original framing becomes retroactively defensible. (2) A `benchmark-readiness.md` amendment that adds explicit shape references to the canonical specs, which would eliminate the "shape authority" half of the refinement and collapse it back to a single-authority question. (3) An authoritative statement (from the user) that the "T6 consolidation doesn't need to close T6" framing is unacceptable, which would force Option 1.

### Decision 2: Track the T6 review on `chore/track-t6-review` before any consolidation work

**Choice:** Create `chore/track-t6-review` branch from `main`, commit the
previously-untracked review file as a standalone atomic change, before
proceeding to any consolidation prep.

**Driver:** User's verbatim reasoning: *"Leaving [the review doc] untracked
while starting consolidation work creates an unnecessary coupling: the
accepted review state can drift at the same time as the synthesis-contract
edits it is evaluating. So the cleaner sequence is: 1. Track the review
artifact on a working branch. 2. Then do the consolidation-prep mapping."*

**Alternatives considered:**
- **Bundle tracking + consolidation on one branch:** My initial (weaker) recommendation. **Rejected** by the user in favor of sequential separation, because the branches have different semantic purposes: tracking is housekeeping, consolidation is a normative contract change.
- **Leave the review untracked during consolidation:** The pre-pivot default. **Rejected** because two untracked working-tree changes evaluating each other creates coupling that makes review-state drift during edit-state drift.

**Implications:**
- The review doc is now committed as `40e30b2c` on `chore/track-t6-review`. It's an immutable reference point — consolidation work can cite it by sha:path.
- Future consolidation work must NOT happen on `chore/track-t6-review`. The branch name would mislabel a contract mutation as housekeeping. User was explicit on this branch-semantics point.
- Main is now 7 commits ahead of origin (was 6 before this session's archive commit; 6+1 tracking = 7). Not pushed. User decides when.

**Trade-offs accepted:**
- Two branches for what could have been one. Slightly more PR overhead if these are eventually pushed upstream.
- The tracking commit is isolated without the context that motivated tracking (which lives in this session's analysis). Mitigated by the commit message body, which explains the review reached stable verdict after seven adversarial passes.

**Confidence:** High (E2) — user provided explicit reasoning and executed the decision immediately upon verification. No subsequent pushback on the branch name or commit content.

**Reversibility:** High — the tracking commit can be reset, the branch deleted, and the work redone on a different branch if the branch-semantics decision changes later.

**What would change this decision:** Nothing; this is settled.

### Decision 3: Produce per-surface status matrix now (not step back until F6/F7/F11 resolve)

**Choice:** Build the per-surface status matrix as the session's deliverable
under the ownership decision, without waiting for audit P1 resolution.

**Driver:** User's verbatim reasoning: *"I should build the per-surface
status matrix next. Do NOT step back entirely until F6/F7/F11 resolve.
Reason: the matrix is the right artifact for unresolved state. It does not
pretend the work is ready to implement; it makes the blockers explicit.
Waiting for the audit P1s to resolve before writing the matrix would throw
away the exact analysis that should drive that resolution."*

**Alternatives considered:**
- **Step back entirely until audit P1s resolve:** The "safest" option from a "don't canonize unstable things" stance. **Rejected** by the user because it discards the analytic work that could inform P1 resolution itself. The matrix is not an implementation artifact; it's a mapping of what's blocked and why.
- **Produce the edit checklist for `dialogue-synthesis-format.md` anyway, with caveats:** **Rejected** (implicitly — not even proposed) because it would reproduce the same error class as the withdrawn map.

**Implications:**
- The matrix is the next deliverable. No edits to `dialogue-synthesis-format.md` until ownership resolution ratifies and audit P1s resolve.
- The matrix makes F6/F7/F11 ownership an explicit open question (captured in Next Steps and Open Questions).
- The matrix surfaces the EvidenceRecord orphan as a T6 review-correction item, separating it from T7 wire-format work.

**Trade-offs accepted:**
- The matrix is long (5 surfaces × 9 fields + cross-cutting observations). Not easily glanceable. But the density is what makes it credible under unresolved state.
- Time spent on the matrix is time not spent on other work. Justified by the user's direction.

**Confidence:** High (E2) — user was explicit on the direction and the reasoning.

**Reversibility:** High — the matrix is analysis-only; it doesn't constrain downstream work.

**What would change this decision:** Audit P1 resolution would upgrade the matrix from "blocked" to "actionable," at which point an edit checklist becomes the next artifact.

### Decision 4 (Claude-made): Withdraw the consolidation prep map

**Choice:** After verification, explicitly withdraw the consolidation prep map I produced in Phase 3 and replace it with the status matrix.

**Driver:** Verification confirmed all 14 of the user's critical findings against cited sources. The map had four kinds of errors: (a) confused ownership (treated review-doc position as settled over benchmark-readiness), (b) missed audit gaps (F6/F7/F11 not referenced), (c) factual errors about source locations (EvidenceRecord schema at state-model.md:184 not provenance-and-audit.md), (d) semantic sloppiness (keyed-vs-array, example claimed "already has every other section" when it was demonstrably incomplete).

**Alternatives considered:**
- **Patch the map surface-by-surface:** Address each finding without withdrawing the framework. **Rejected** because the errors were structural (cross-contract work misframed as local edit), not localized. Patching would leave the underlying frame intact and reproduce the class of errors on the next iteration.
- **Defend the map's position on any finding:** **Rejected** per the skill's rule ("push back with technical reasoning if wrong") combined with the verification evidence (14/14 findings held up; nothing to defend).

**Implications:**
- The original map is in the Rejected Approaches section of this handoff as a full failure record. Future-Claude should read it and the verification pass to avoid repeating the class of errors.
- The status matrix replaces the map entirely. The two artifacts serve different purposes: the map was "here's how to execute consolidation"; the matrix is "here's the state of the surfaces, what's blocked, and by what."

**Trade-offs accepted:**
- Time spent on the withdrawn map is time wasted in the narrow sense. But the verification pass against it generated specific source knowledge that flows directly into the matrix, so the cost is partial.
- Withdrawal risks looking like capitulation rather than technical judgment. Mitigated by the finding-by-finding verification response, which showed each finding was verified against source, not accepted on authority.

**Confidence:** High (E3) — 14 independent findings triangulated against 10 different source files. No pushback points survived verification.

**Reversibility:** Low — the map is withdrawn and its errors documented. Un-withdrawing would require resolving all 14 findings, which would effectively produce a different artifact anyway.

**What would change this decision:** Only if the findings were themselves wrong, which verification showed they weren't.

## Changes

### `docs/reviews/2026-04-04-t04-t6-benchmark-first-design-composition-review.md`

**Purpose:** The T6 composition review artifact, graduated from `docs/notes/`
to `docs/reviews/` by the user between sessions. Completed seven adversarial
review passes across two sessions, reached "Minor revision" verdict, then one
targeted fix (T3/T4 table framing) before this session started.

**State when tracked:** 164 lines. Contains: Scope, State Model section
(with fixed T3/T4 identity boundary and corrected lifecycle table citations),
Loop Structure section (COMPOSES verdict after consultation contract added),
Synthesis Contract section (DOES NOT YET COMPOSE verdict, "Surfaces to merge"
table with 5 surfaces — **this table's T6 ownership claim is now known to be
wrong per Decision 1 and needs narrowing**), Coverage Adequacy section (B8
conditional), T6 Verdict table, consolidation artifact specification,
deferred-to-T7 items.

**Tracking approach:** Committed on `chore/track-t6-review` branch from `main`
via the user's directed sequence (Decision 2). No content changes in this
session.

**Future-Claude note:** The "Surfaces to merge" table at lines 83-93
overstates T6 ownership per the ownership resolution (Decision 1). The fix
is a T6 review-correction task. Options: (a) narrow the table to remove
T7-owned rows, keeping only the `agent_local` row as T5 scope; (b) rewrite
the table as a "what T6 references, who owns it" map; (c) remove the
consolidation artifact concept entirely since T6 doesn't do consolidation
under the resolution. Pick (a) or (b) — (c) is too large a frame shift.

### Git state

| Before session | After session |
|---|---|
| Branch: `main` (6 commits ahead of origin) | Branch: `chore/track-t6-review` (1 commit ahead of main) |
| Working tree: 1 untracked file (review doc) | Working tree: clean |
| Prior handoff: in `docs/handoffs/` | Prior handoff: archived, new handoff being written |

**Commits this session:**
- `0b8f6a9f docs(handoff): archive 2026-04-04_14-56_t6-composition-analysis-four-review-passes.md` (on main)
- `40e30b2c docs(reviews): track T6 benchmark-first design composition review` (on chore/track-t6-review)

**Branch:** `chore/track-t6-review` is 1 commit ahead of main. Not pushed.
Main remains 6 commits ahead of origin (pre-existing state).

**Future-Claude note:** Do NOT append the consolidation work to
`chore/track-t6-review`. Per Decision 2's branch-semantics reasoning, the
next branch should advertise "synthesis contract mutation" or similar. The
chore branch exists only to preserve the accepted review state.

## Codebase Knowledge

### Architecture: T4 spec tree and ownership authority

The T4 spec tree lives at
`docs/plans/t04-t4-scouting-position-and-evidence-provenance/` with several
normative files each declaring its own authority domain via frontmatter:

| File | Authority | Content type |
|---|---|---|
| `state-model.md` | state-model | Data structures, lifecycle transitions, state transitions |
| `provenance-and-audit.md` | provenance | Synthesis citation surface, provenance index, claim ledger grammar, audit chain |
| `boundaries.md` | (declares breaking migrations) | T4-BD-* input change declarations with downstream impacts |
| `benchmark-readiness.md` | benchmark-readiness | Gate ownership tables, T7 prerequisite gate, benchmark amendment obligations |
| `containment.md` | containment | Scope envelope, allowed_roots, scope breach detection |
| `scouting-behavior.md` | scouting | Per-turn loop, scout attempts, classification |
| `foundations.md` | foundations | Axioms (T4-F-*) |

**Key insight:** `benchmark-readiness.md` is a **gate-ownership** doc, not a
shape doc. When it references data shapes (like `:87`'s "`claim_id`-keyed
schema"), that phrasing is informal shorthand. The authoritative shape lives
in `provenance-and-audit.md` or `state-model.md` depending on the surface.

### `benchmark-readiness.md` ownership tables (the ones that matter)

| Section | Lines | Scope | Rows that touch `dialogue-synthesis-format.md` |
|---|---|---|---|
| T4-BR-01 "T5 Migration Surfaces" | `:14-43` | `agent_local` mode enablement | Row 2 (`:35`, conversation summary mode, owner T5), Row 3 (`:36`, pipeline epilogue field, owner T5) |
| T4-BR-04 "Provenance Index Consumer" | `:79-90` | `claim_provenance_index` wiring | Row 1 (`:87`, pipeline epilogue schema, owner T7) |
| T4-BR-05 "Synthesis-Format Contract Updates" | `:92-102` | Claim Ledger + not_scoutable | Row 1 (`:99`, Claim Ledger section, owner T7), Row 2 (`:100`, ledger rules, owner T7), Row 3 (`:101`, not_scoutable in claim trajectory, owner T7), Row 4 (`:102`, not_scoutable in evidence trajectory, owner T7) |

**All five T7 rows** are the wire-format surfaces in Decision 1's split.

T4-BR-06 at `:104-119` is "Narrative Factual-Claim Inventory" — three T7
rows for the semantic extraction components needed to enforce ledger
completeness (T4-PR-06). Not in the matrix directly but gates Surface 2
(Claim Ledger) for enforcement.

T4-BR-07 at `:121-142` is the "Eight-Item Prerequisite Gate" — comprehensive
T7 gate that benchmark-run validity depends on.

### `provenance-and-audit.md` — semantic authority for synthesis surfaces

Structure:

| Section | Lines | Defines |
|---|---|---|
| T4-PR-01 "Evidence Trajectory" | `:14-48` | Projection of `evidence_log` to human-facing table (5 columns: index, entity, found, disposition, impact). **NOT the EvidenceRecord schema.** |
| T4-PR-02 "Synthesis-Record Join" | `:50-63` | Deterministic join via `claim_id`, two structured surfaces |
| T4-PR-03 "Claim Provenance Index" | `:65-106` | **Dense JSON array** with `index[i].claim_id == i` invariant. Two variants: `scouted` (has `record_indices`) and `not_scoutable` (has `classification_trace`). Canonical wire format at `:84-90`. |
| T4-PR-04 "Two Provenance Tiers" | `:108-119` | Tier 1 (scouted, has evidence chain), Tier 2 (`not_scoutable`, classification only, **no evidence chain**) |
| T4-PR-05 "Claim Ledger" | `:121-163` | `FACT: <text> [ref: N]` grammar, separation-from-checkpoint table, ledger rules |
| T4-PR-06 "Narrative-to-Ledger Relationship" | `:164-210` | MUST relationship, mechanical enforcement gap at `:202-210` (requires T7 semantic extraction) |
| T4-PR-07 "Provenance Coverage of Scored Claims" | `:212-234` | Narrative-only violations, `ledger_coverage_rate` metric |
| T4-PR-08 "G3 Scope" | `:235-248` | G3 satisfied by Tier 1 scouted chain only |

**Key locations future-Claude should know:**
- Dense array canonical form: `provenance-and-audit.md:84-90`
- Classification trace equality invariant: `:92-101`
- Separation of checkpoint from ledger: `:135-149`
- Claim ledger rules list: `:151-162`
- Mechanical enforcement gap: `:202-210`

### `state-model.md` — EvidenceRecord lives here (not in provenance-and-audit)

| Section | Lines | Defines |
|---|---|---|
| Phase 1 "Status Changes" | `:81-88` | Processing of conceded/reinforced |
| Phase 1.5 "Forced-New Reclassification" | `:89-97` | Dead-referent reclassification for reinforced/revised |
| Phase 2 "New Registrations" | `:113-127` | Merger checks for new/revised |
| T2/T3/Synthesis Interaction | `:129-134` | Reclassification visible to all downstream |
| T4-SM-03 "Referent Resolution" | `:136-162` | Live-occurrence filtering, NO_LIVE_REFERENT return |
| T4-SM-04 "ClaimRef" | `:164-182` | Wire format: dense array `[turn, key, idx]` |
| **T4-SM-05 "Evidence Record"** | **`:184-221`** | **Full EvidenceRecord schema: 8 fields (index, turn, claim_ref, claim_text, entity, steps, citations, disposition). Plus ScoutStep (10 fields) and CitationSpan (4 fields).** |
| T4-SM-06 — lifecycle | Around `:300+` | Claim lifecycle |
| Lifecycle table | `:376-392` | All terminal paths including forced-new rows at `:387-388` |
| T4-SM-07 "Agent Working State" | `:400+` | `claim_provenance_index` lives here structurally |

**Critical distinction:** `provenance-and-audit.md:14-48` (T4-PR-01) defines
the Evidence **Trajectory** (the projection for human-facing output).
`state-model.md:184-221` (T4-SM-05) defines the Evidence **Record** (the
full data schema). My withdrawn map conflated these — an implementer
following the map would transcribe 5 trajectory columns and miss the 5
record fields (turn, claim_ref, claim_text, steps, citations).

### `dialogue-synthesis-format.md` — the target doc

236 lines, **no frontmatter** (conspicuous absence relative to peer specs
that declare `normative`, `authority`, `status`). Structure:

| Section | Lines | Content |
|---|---|---|
| Assembly Process | `:5-17` | 7 numbered items. Line 9 literally says "These 7 items". Line 15 = item 5 (Evidence trajectory). Line 16 = item 6 (Claim trajectory). |
| Confidence Annotations | `:19-27` | High/Medium/Low table |
| Your Assessment | `:29-34` | Agree/disagree/emerged |
| Pre-Flight Checklist | `:36-49` | 8 checklist items |
| Synthesis Checkpoint | `:51-74` | Checkpoint grammar + cross-reference rules |
| Output Format | `:76-227` | H3 sections |
| Conversation Summary | `:78-86` | **Line 86 declares mode vocabulary: `server_assisted` or `manual_legacy`. No `agent_local`.** |
| Key Outcomes | `:88-100` | |
| Areas of Agreement | `:101-103` | |
| Contested Claims | `:105-112` | |
| Open Questions | `:114-116` | |
| Continuation | `:118-123` | Line 123 has "Evidence trajectory" field |
| Synthesis Checkpoint | `:125-136` | |
| Pipeline Data | `:138-173` | **Table at `:142-154` has 11 fields. No `claim_provenance_index` row.** JSON template at `:156-171`. |
| Example | `:175-227` | **INCOMPLETE**: omits Mode line, omits Synthesis Checkpoint block, omits Pipeline Data JSON block. Title says "Complete example" but is not. |
| Do not include | `:229-235` | **Line 233: "Raw ledger entries (keep internal — only the trajectory line appears in output)." This contradicts any addition of `## Claim Ledger` section.** |

### Consumer code path

**`emit_analytics.py` parse path:**
- `:270-282` `_parse_epilogue_fallback()` returns default dict with 10 keys
- `:284-329` `parse_synthesis()` — top-level parser. Extracts epilogue via `_parse_epilogue()`, returns fixed dict with **14 keys** (resolved_count, unresolved_count, emerged_count, converged, turn_count, thread_id, scout_count, mode, convergence_reason_code, scope_breach_count, termination_reason, parse_truncated, parse_failed, parse_fallback_used). **Any unknown epilogue field is silently dropped at this layer.**
- `:337-368` `map_convergence()` — maps dialogue state to convergence_reason_code and termination_reason
- `:376-449+` `build_dialogue_outcome()` — constructs event with 20+ fields. **Does not include `claim_provenance_index` or any ledger-related fields.** Mode fallback at `:441`: `parsed.get("mode") or pipeline.get("mode", "server_assisted")` — default is `server_assisted`, not `agent_local`.

**`event_schema.py` contract:**
- `:28` `SCHEMA_VERSION = "0.1.0"`
- `:53-70` `REQUIRED_FIELDS_BY_EVENT["dialogue_outcome"]` — frozenset of 15 required field names. **No `claim_provenance_index`.**
- `:104-109` STRUCTURED_EVENT_TYPES and KNOWN_UNSTRUCTURED_TYPES
- `:133-135` `VALID_CONVERGENCE_CODES` — 5 values (includes `scope_breach`)
- **`:137` `VALID_MODES = frozenset({"server_assisted", "manual_legacy"})` — `agent_local` not in enum**
- `:139` `VALID_MODE_SOURCES = frozenset({"epilogue", "fallback"})` — does NOT include `null` directly (T5 §3.5 says mode_source should be null for agent_local, but the enum doesn't model null as a valid state)
- `:145-147` `VALID_TERMINATION_REASONS` — 5 values

**`SKILL.md` (dialogue) relay and producer path:**
- `:381-386` Step 6 "Present synthesis" — lists 3 items to relay: narrative synthesis, Synthesis Checkpoint, assessment. **No mention of Claim Ledger.**
- `:435` Step 7a pipeline field definition for `mode`: *"If the epilogue is missing, unparseable, missing the `mode` key, or has an invalid mode value, fall back to `'server_assisted'` and set `mode_source` to `'fallback'`."* **This is the silent coercion path for `agent_local`.**

**`codex-dialogue.md` agent:**
- `:499-501` Phase 3 section: *"When entering Phase 3, read and apply [dialogue-synthesis-format.md]. It defines the assembly process **(7 items)**, confidence annotations, pre-flight checklist, synthesis checkpoint, output format, pipeline data epilogue, and a complete example."* The "(7 items)" is hardcoded — externalizes the section count.
- `:514-519` Constraints: read-only, no implementation.

**`HANDBOOK.md`:**
- `:829-831` Declares `dialogue-synthesis-format.md` as the edit surface for Phase 3 changes. Contract hub. Surrounding entries list `composition-contract.md`, `contract-agent-extract.md` — each declares its own edit surface.

### Audit file: `2026-04-02-t04-t4-evidence-provenance-rev17-team.md`

Two days older than the T6 review. Contains multiple P1 findings directly
on the wire formats the T6 review's consolidation artifact would canonize:

| Finding | Line | Priority | Content |
|---|---|---|---|
| F6 | `:141-148` | P1 | Concession boundary — three gaps: (1) conceded `ProvenanceEntry` has no status field, (2) dense-array invariant requires all positions populated but conceded-slot representation is undefined, (3) no stated policy on whether conceded claims appear in claim ledger. |
| F7 | `:152-164` | P1 | `claim_provenance_index` serialization handoff to synthesis assembler unspecified. Integration gap between agent-owned state and synthesis-assembled output. |
| F8 | `:168-180` | P1 | Transcript fidelity degradation produces silent audit regime split. |
| F9 | `:184-196` | P1 | Crash/abort recovery path has no harness detection mechanism. |
| F10 | `:200-212` | P1 | T7 prerequisite block has no fallback owner or partial-readiness path. |
| **F11** | `:216-228` | **P1** | **No schema versioning on wire formats with named T7 consumers.** EvidenceRecord, VerificationEntry, ClassificationTrace, ScoutStep have no version fields. Rev 9-12 each contained breaking schema changes. |
| F12 | `:232-244` | P1 | Pre-T7 testability surface unpartitioned. |
| F13 | `:248+` | P1 | Allowed-scope secret handling. |

**F6, F7, F11 are the three that directly block Surfaces 1-4 in the status
matrix.** F8-F10, F12, F13 are adjacent but not directly blocking wire format
canonization. All eight F-findings are P1, all unresolved at session time.

### `t5-mode-strategy.md` — mode semantics authority

| Section | Lines | Content |
|---|---|---|
| §3.2 `agent_local` | ~`:90-105` | Definition: local structured loop, direct host tools, no helper-issued scouts, no external dialogue helper. T-04 benchmark-first candidate is the reference instance. |
| §3.3 `manual_legacy` | `:106-116` | Definition: no helper-owned structured loop, no agent-local ledger equivalent, no mid-dialogue scouting, fallback manual loop. |
| §3.4 Boundary Notes | `:118-126` | **"Mode describes dialogue-loop ownership, not whether Codex transport is MCP, CLI, or App Server." "Mode also does not mean 'how good was the evidence.'"** |
| §3.5 `mode_source` for `agent_local` | `:127-147` | For agent_local outcomes, `mode_source=null`. Four-point rationale. |
| §4 T-04 Candidate Classification | `:162-180` | Property table: structured local entries yes, external helper no, direct host-tool scouting yes, manual degraded fallback no → agent_local. |
| §5 Owning Layers | `:182-191` | 4-6 dialogue contract surfaces define mode semantics; 1-5 T-04 candidate loop emits; consultation path outside this decision. |
| §6 Primary Migration Set | `:193-206` | 7-row table of required changes. Rows 199-200 are `dialogue-synthesis-format.md` spec updates (owner T5). Rows 201-205 are consumer code. |
| §7 Explicit Non-Changes | `:224-242` | Surfaces that don't need direct change for design coherence. |

## Context

### Mental Model

**The problem was "what kind of work is T6 consolidation?"** My withdrawn map
treated it as a localized documentation edit — read the sources, project them
into the target doc, handle some cross-references. The user's rejection
reframed it as **cross-contract work**: ownership spans T5/T6/T7, semantic
shape spans multiple normative specs, consumer paths span multiple files,
and audit findings gate the whole thing.

The correct frame: **T6 doesn't do consolidation under the current audit
state.** The consolidation work is T7's, and T7 is blocked on audit P1
resolution. T6's role is narrower than I thought — it's a design coherence
checkpoint that verifies composition, not a packaging exercise that merges
specs into a single authoritative document.

The user's refinement captured a distinction I had missed even after accepting
the rejection: **ownership authority and shape authority are different kinds
of authority, and a single doc (like `benchmark-readiness.md`) can be
authoritative on one and not the other.** The matrix applies this distinction
systematically — every row separates "who owns this work" from "where is the
shape defined."

**The recurring pattern across all my errors this session (and across the
prior session's review passes, and the session before that):** scope
displacement. My first map displaced T6 work to T7 (pushed too far). My
withdrawn consolidation map displaced T7 work to T6 (pulled too far). The
user catches these at every iteration because they know the shape of T6 and
T7 better than I've internalized. The correction is always the same: anchor
to `benchmark-first-design-plan.md`'s definition of T6 and T7, and follow
`benchmark-readiness.md`'s ownership tables.

### Project State

All D-prime cross-model work (T1-T5) verified end-to-end. T4 closed at SY-13.
Benchmark contract has Path-2 corpus constraint. T6 analysis went through
seven adversarial review passes across three sessions and reached "Minor
revision" then one final fix. **The review artifact is now tracked in git
for the first time** (`40e30b2c`), but the T6 disposition itself is unchanged
— "remains open pending synthesis contract consolidation."

**Ownership resolution (this session's contribution):** The consolidation
work is T7's, not T6's. T6's remaining scope is narrowed to a review-doc
correction that removes T6's over-claimed ownership.

**Audit state:** `2026-04-02-t04-t4-evidence-provenance-rev17-team.md` has
13 unresolved P1 findings. F6, F7, F11 directly block the four T7 wire-format
surfaces. Ownership of audit remediation is not assigned in any gate table.

**T7 state:** Blocked. Cannot proceed on wire formats until F6/F7/F11
resolve. Cannot skip them because audit findings are prerequisites, not
deliverables.

### Environment

`claude-code-tool-dev` monorepo. Branch `chore/track-t6-review` (just
created). Main is 6 commits ahead of origin; chore branch is 1 commit ahead
of main. Working tree clean. No files modified this session except the
archived handoff (committed on main) and the newly-tracked review file
(committed on the chore branch).

No tests run this session — analysis only.

### Mode Taxonomy (for session reference)

`server_assisted`: helper-mediated dialogue. Current production mode for
codex-dialogue agent. Tool availability yes, structured local ledger no.

`manual_legacy`: degraded no-scout fallback. Used when tools unavailable.

`agent_local`: local structured loop with direct host tools. **Does not
exist yet as a running producer.** T-04 benchmark-first candidate is the
reference instance. Currently rejected by `event_schema.py:137` VALID_MODES,
silently coerced to `server_assisted` with `mode_source="fallback"` by
`SKILL.md:435`.

**Mode describes dialogue-loop ownership, not transport or evidence quality**
(per `t5-mode-strategy.md:118-126`). This is the distinction my original map
got wrong.

## Learnings

### Ownership authority and shape authority are different kinds of authority

**Mechanism:** A single normative doc can be authoritative on ownership (who
owns the work, what gates block what) without being authoritative on shape
(what the data structure looks like). `benchmark-readiness.md` is a
gate-ownership doc. When it mentions shapes in row descriptions (like
"`claim_id`-keyed schema" at `:87`), those are informal shorthands to give
context; the authoritative shape lives elsewhere (at `provenance-and-audit.md:84-90`
for this example).

**Evidence:** User's refinement: *"The clean resolution is not 'one doc
wins'; it is 'ownership follows benchmark-readiness, semantic shape follows
the canonical provenance/state-model specs.'"* Verified against
`benchmark-readiness.md:87` (says keyed) and `provenance-and-audit.md:84-90`
(says dense array). The two are inconsistent; the canonical spec wins.

**Implication:** When reading any gate-ownership doc, separate ownership
claims from shape claims and treat them as independent authority statements.
Don't let informal shape phrasing override the canonical spec. The matrix
format enforces this by having "Ownership authority" and "Semantic authority
(shape)" as distinct columns.

**Watch for:** This same pattern applies to `boundaries.md` (T4-BD-* rows
declare input changes with informal descriptions), `scouting-behavior.md`
(T4-SB-* rows reference state model surfaces), and likely any future gate
spec. The canonical data-shape authority is in `state-model.md` or
`provenance-and-audit.md` depending on the surface.

### Scope displacement is my recurring failure mode on T6 analysis

**Mechanism:** I reclassify T6 work as belonging elsewhere, either by
pushing it forward (to T7, to implementation) or by pulling work from
elsewhere into T6's scope. The displacement happens at the framing level —
my first thought about what "counts as T6" is almost always wrong.

**Evidence:** (1) Prior-prior session Pass 2 displaced T6 work to T7/T8
implementation readiness. (2) Prior-prior session Pass 3 displaced T6 work
to an "orchestration layer." (3) This session's consolidation prep map
pulled T7 work (per `benchmark-readiness.md` T4-BR-04/05) into T6 scope.
(4) Even my initial response to the rejection displaced the problem again,
proposing three options that framed T6 vs T7 as a binary rather than
recognizing that the ownership split is the whole point.

**Implication:** Before framing any T6-related work, I should verify against
`benchmark-first-design-plan.md` (T6's definition) and `benchmark-readiness.md`
(the ownership tables). Anchor to the authoritative frame before describing
what the work is.

**Watch for:** Any sentence I write about T6 or T7 that doesn't cite the
gate-ownership doc. If I'm describing T6's scope without a
`benchmark-readiness.md` reference, I'm inventing frame.

### Consumer path is the falsification test for spec additions

**Mechanism:** Adding a field to a specification doc means nothing if the
consumer path drops it silently. For any proposed spec addition, walk the
consumer path: producer → parser → schema → event construction → harness.
If any layer drops the field, the addition is contract theater.

**Evidence:** `claim_provenance_index` traversal — `emit_analytics.py:299-317`
returns a fixed 14-key dict, `:428-449` builds an event with 20+ fields but
no provenance index, `event_schema.py:53-70` has no required-field entry.
Silent drop at every layer. Documented in CF2 of the user's rejection.

**Implication:** The status matrix's "Producer/Parser/Schema/Harness status"
columns make this test explicit. A "stable to transcribe" verdict requires
either (a) a live consumer path, or (b) explicit labeling as producer-only
and unconsumed until a specific future milestone.

**Watch for:** The inverse — code that consumes a field that has no spec
obligation. If `emit_analytics.py` added handling for `claim_provenance_index`
without spec backing, the consumer would silently accept whatever shape the
agent emitted.

### Receiving-code-review skill: verify before acknowledging

**Mechanism:** The skill's rule is "verify each finding against the cited
source before responding." No performative agreement; no blanket acceptance;
push back only with evidence. Verification produces three outcomes: (1)
finding confirmed → accept, state what I got wrong, no gratitude
expressions; (2) finding wrong → push back with counter-evidence; (3)
finding can't be verified → say so, ask for direction.

**Evidence:** This session. User gave 14 findings with specific file:line
citations. I dispatched 10 parallel reads to verify each against cited
sources. 14 of 14 confirmed. Plus discovered F6 as an adjacent P1 finding
(not cited by the user, strengthens CF4). Wrote a finding-by-finding
response with verification evidence from each read.

**Implication:** The skill is specifically for this situation. Reading the
skill on the first invocation of this session was the right trigger — the
user's rejection was dense, specific, and evidence-backed. Without the
skill's explicit "verify each" rule, I might have accepted some findings
based on their phrasing alone.

**Watch for:** Any future adversarial review. Pattern: invoke skill, read it
fully, dispatch parallel verification reads, respond with evidence. Do not
skip the verification step even when findings "seem right."

## Next Steps

### 1. Correct the T6 review doc's "Surfaces to merge" table (T6 review-correction scope)

**Dependencies:** None. This is a standalone T6 review-doc edit.

**What to read first:**
- `docs/reviews/2026-04-04-t04-t6-benchmark-first-design-composition-review.md:83-93` (the table to correct)
- The ownership resolution in this handoff (Decision 1) for the semantic frame
- The status matrix (this handoff's Codebase Knowledge section or the matrix in chat history)

**Work to do:** The table currently lists 5 surfaces with the framing that
T6 consolidation merges them into `dialogue-synthesis-format.md`. Per the
ownership resolution, this is wrong. Options:

- **Option A (narrow the table):** Keep only the `agent_local` row (owner
  T5, not T6), remove the four T7-owned rows. The table becomes a single
  row, which implies it should be rewritten as prose instead.
- **Option B (reframe the table):** Rename it "Surfaces T6 references for
  composition check" or similar, change the "Target location" column to
  "Owner" (T5/T7), and keep all 5 rows as a cross-reference rather than a
  merge plan.
- **Option C (remove the consolidation artifact concept):** Delete the
  consolidation artifact subsection entirely. T6 doesn't do consolidation
  under the resolution. The T6 verdict remains "synthesis contract does
  not yet compose" but that "does not yet" is T7's responsibility, not
  T6's.

**Recommendation if I draft:** Option B — preserves the cross-reference
value, doesn't require deleting content, accurately represents the new
frame. But the decision is the user's; substantive amendments are their
role.

**Acceptance criteria:** The table no longer implies T6 owns the
synthesis-format updates. The EvidenceRecord orphan is handled explicitly
(either as a row with T4 ownership declaration + deferred label, or removed).
Line 233 "Do not include raw ledger entries" remains unchanged at this stage
(it's a T7 consolidation concern, not a T6 review-correction concern).

**Branch strategy:** The edit should happen on a new branch (NOT
`chore/track-t6-review`). Suggested: `docs/t6-review-correction` or similar.

**Note:** The user writes substantive amendments themselves. Claude's role
is verification and review.

### 2. Assign ownership of audit P1s F6/F7/F11

**Dependencies:** None — this is a meta-question, not a work item itself.

**What to read first:**
- `docs/audits/2026-04-02-t04-t4-evidence-provenance-rev17-team.md:141-230` (F6, F7, F11 findings)
- `benchmark-readiness.md` (check whether audit remediation is declared anywhere)
- `benchmark-first-design-plan.md` (the gate-ordering doc — might declare audit remediation scope)

**Question to answer:** Who owns F6/F7/F11 remediation? T4 (because they're
T4 spec gaps)? T7 (because they're T7 prerequisites)? A dedicated remediation
packet? Without someone claiming these, T7 is structurally blocked and the
benchmark execution timeline stalls indefinitely.

**Work to do:** Identify where audit remediation ownership lives or should
live. If it's unclaimed, surface that as a decision for the user. Likely
outcome: a benchmark-readiness.md amendment that adds audit-remediation as
an explicit T4 or T7 obligation, with gating language.

**Acceptance criteria:** F6/F7/F11 have explicit owners; gating logic is
documented; T7's "blocked on audit" state becomes tractable.

### 3. Decide on Surface 5 (`agent_local`) spec-only landing

**Dependencies:** None. This is isolated from the T6/T7 wire-format block.

**What to read first:**
- `2026-04-02-t04-t5-mode-strategy.md:193-206` (Primary Migration Set rows 199-200 are the spec changes)
- `benchmark-readiness.md:14-43` (T4-BR-01 ownership confirmation)
- `dialogue-synthesis-format.md:86` and `:144` (target lines)
- Surface 5 detail in this handoff's status matrix

**Question:** Should T5's spec-only documentation of `agent_local` (the
two dialogue-synthesis-format.md rows) land now as an isolated commit,
ahead of the consumer code changes? Or wait until all 7 rows of the Primary
Migration Set can land together?

**Trade-off:** Landing now documents a mode that the enum still rejects
(`event_schema.py:137`) and the parser still coerces (`SKILL.md:435`). But
zero producers exist today, so there's no runtime impact. Landing accurately
documents the target state; not landing leaves a known gap in the spec.

**Recommendation if I draft:** Defer. The isolated spec-only commit creates
a spec-vs-code gap that's visible but not actionable. Better to land all 7
T5 Primary Migration Set rows as a single T5 commit/PR when a T-04 candidate
loop exists that will actually emit `agent_local`. The `HANDBOOK.md` and
`README.md` follow-ups at t5:209-210 can ride along.

**Acceptance criteria:** Either a decision to defer (captured somewhere
durable), or a commit/PR that lands rows 199-200 with explicit labeling as
"spec documentation, consumer code follows in T7/later."

### 4. Push `chore/track-t6-review` to origin (or decide not to)

**Dependencies:** None.

**What to do:** Decide whether `chore/track-t6-review` should be pushed to
origin as a PR. The tracking commit is a legitimate atomic change (164 lines,
clean, follows repo commit style). PR-worthy. But the review artifact it
tracks will likely need the Next Step 1 correction before the content is in
its final form.

**Options:**
- **Push as-is:** Creates a PR for the tracking commit. Review doc content
  will need a second PR for the correction.
- **Rebase after correction:** Apply the correction as a second commit on
  the same branch, then push. Single PR for "track + correct."
- **Merge to main locally:** Use the `merge-branch` skill to fast-path. No
  PR review; simpler for solo work.

**Decision is the user's.** No default.

## In Progress

Clean stopping point. The session produced:
- Fix verification (complete)
- Tracking commit `40e30b2c` on `chore/track-t6-review` (complete)
- Withdrawal of consolidation prep map (complete, documented in Rejected Approaches)
- Ownership resolution (Decision 1, complete)
- Per-surface status matrix (complete, delivered in chat)

No work is in flight. The matrix is the session's final deliverable.

## Open Questions

1. **Is Option B or Option A the right T6 review-correction approach?** The status matrix implies Option B (reframe the table) but the decision is the user's. Either works for the ownership-resolution purpose.

2. **Who owns F6/F7/F11 remediation?** Unassigned in every gate table checked this session. Likely a T4 spec-amendment obligation but not declared.

3. **Should Surface 5 (`agent_local` spec docs) land as an isolated commit?** The matrix argues weakly against (creates visible gap without unblocking any producer) but it's a judgment call.

4. **Push `chore/track-t6-review` upstream?** No strong default.

5. **Does the T6 disposition change after the ownership resolution?** The review currently says "remains open pending synthesis contract consolidation." Under the new frame, T6 doesn't do consolidation — so what does "T6 remains open" mean? Possible answers: (a) T6 remains open pending the review-correction itself (Next Step 1); (b) T6 closes with "composes conditionally on T7 consolidation work" as the new verdict; (c) T6's composition verdict decouples from the consolidation frame entirely (all three composition checks were COMPOSES-ish; the "does not yet compose" for synthesis contract was the consolidation frame, not a composition failure). **This is an interpretive question the T6 review-correction must answer explicitly.**

## Risks

1. **The T6 review-correction might surface additional issues.** Each prior review pass found issues the prior pass missed. The correction work is a substantive edit by the user; there's no guarantee it completes cleanly.

2. **F6/F7/F11 remediation may take significant time.** The findings are dated 2026-04-02 (two days before this session). If they've been waiting that long without ownership assignment, the backlog pattern suggests this could stall indefinitely.

3. **My scope-displacement failure mode may recur.** Even with the explicit learning captured, the pattern has appeared in 4+ iterations. Future sessions on T6 or T7 should expect this and compensate (anchor to ownership tables before framing any work).

4. **The matrix's "stable to transcribe" verdicts may be wrong.** Surface 5 is rated "partial — yes for spec-only" but I'm not 100% sure the spec-only landing is coupling-free. Edge case: if `codex-dialogue.md:499-501`'s hardcoded "(7 items)" becomes "(8 items)" via some future T7 edit, the Surface 5 edit would race with it. Mitigated by Surface 5 not changing the assembly process count.

5. **The withdrawn map exists in conversation history and might be referenced in future sessions.** If a future Claude session reads the prior map without the rejection/verification context, the error class reproduces. Mitigation: the Rejected Approaches section in this handoff documents the map and its failure reasons explicitly.

## References

| What | Where |
|---|---|
| T6 review doc (now tracked) | `docs/reviews/2026-04-04-t04-t6-benchmark-first-design-composition-review.md` |
| T6 "Surfaces to merge" table (needs correction) | Same file, `:83-93` |
| Ownership authority (T7 rows) | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/benchmark-readiness.md:79-102` (T4-BR-04, T4-BR-05) |
| Ownership authority (T5 rows) | Same file, `:14-43` (T4-BR-01) |
| T6/T7 gate definitions | `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md:38-42, :52` |
| Canonical wire format (dense array) | `provenance-and-audit.md:84-90` |
| EvidenceRecord schema | `state-model.md:184-221` (T4-SM-05) |
| Claim Ledger grammar | `provenance-and-audit.md:121-163` (T4-PR-05) |
| Ledger enforcement gap | Same file, `:202-210` (T4-PR-06 Mechanical Enforcement) |
| Two provenance tiers | Same file, `:108-119` (T4-PR-04) |
| `not_scoutable` declaration | `boundaries.md:35` (T4-BD-02 row 5) |
| Mode semantics (ownership, not transport) | `t5-mode-strategy.md:118-126` (§3.4) |
| `mode_source=null` rationale | Same file, `:127-147` (§3.5) |
| T5 Primary Migration Set | Same file, `:193-206` (§6) |
| Audit P1 F6 (concession boundary) | `docs/audits/2026-04-02-t04-t4-evidence-provenance-rev17-team.md:141-148` |
| Audit P1 F7 (serialization handoff) | Same file, `:152-164` |
| Audit P1 F11 (no schema versioning) | Same file, `:216-228` |
| Target doc (to-be-edited in T7) | `packages/plugins/cross-model/references/dialogue-synthesis-format.md` |
| Line 233 collision | Same file, `:233` ("Raw ledger entries") |
| Incomplete example | Same file, `:175-227` (missing Mode, Synthesis Checkpoint, Pipeline Data) |
| Parser drop path | `packages/plugins/cross-model/scripts/emit_analytics.py:299-317, :428-449` |
| Schema rejection | `packages/plugins/cross-model/scripts/event_schema.py:53-70, :137` |
| Silent mode coercion | `packages/plugins/cross-model/skills/dialogue/SKILL.md:435` |
| Relay step (no Claim Ledger) | Same file, `:381-386` |
| "(7 items)" hardcoded citation | `packages/plugins/cross-model/agents/codex-dialogue.md:501` |
| HANDBOOK contract-hub declaration | `packages/plugins/cross-model/HANDBOOK.md:829-831` |
| Prior session handoff | `docs/handoffs/archive/2026-04-04_14-56_t6-composition-analysis-four-review-passes.md` |
| Tracking commit | `40e30b2c` on `chore/track-t6-review` |

## Rejected Approaches

### The consolidation prep map (withdrawn)

**Approach:** Produce a 5-surface "consolidation prep map" mapping T4-PR-01,
T4-PR-03, T4-PR-05, T4-BD-02, and T5 §6 to specific target locations in
`dialogue-synthesis-format.md`. Deliver as per-surface breakdowns with
Source, Where-it-lands, Merge action, and Scope, plus cross-cutting
observations and a proposed two-mode delivery (Claude drafts mechanical
surfaces, user handles semantic framing).

**Why it seemed promising:** The user had framed the next step as
"consolidation prep mapping" and explicitly endorsed producing a map. The
T6 review's "Surfaces to merge" table listed exactly 5 surfaces, which
matched my approach 1:1. The canonical sources existed and were readable.
A per-surface format felt tractable.

**Specific failure:** Fourteen findings in a structured rejection, all
verified against cited sources:

- **CF1:** Treated T6 review's position on ownership as authoritative without checking `benchmark-readiness.md` T4-BR-04/T4-BR-05, which assigned the same surfaces to T7. Ø-order contradiction between the two docs that I missed entirely.
- **CF2:** Assumed adding `claim_provenance_index` to the spec was mostly a doc change. `emit_analytics.py:299-317` drops the field at parse time; `event_schema.py:53-70` has no contract for it; `SKILL.md:435` falls back on invalid mode values. Contract theater.
- **CF3:** Did not notice `dialogue-synthesis-format.md:233` "Do not include: Raw ledger entries" directly collides with a proposed `## Claim Ledger` section addition.
- **CF4:** Did not reference or check `docs/audits/2026-04-02-t04-t4-evidence-provenance-rev17-team.md`, which has three open P1 findings (F6, F7, F11) on the exact wire formats the map would canonize.
- **FA1:** Cited `provenance-and-audit.md:15-63` as the EvidenceRecord schema source. Wrong — that's the Evidence Trajectory (5-column projection). Actual EvidenceRecord schema is at `state-model.md:184-221` (8 fields including turn, claim_ref, claim_text, steps, citations).
- **FA2:** Described `claim_provenance_index` as "keyed by `claim_id`." Wrong — it's a dense JSON array where `index[i].claim_id == i` per `provenance-and-audit.md:84-90`. "Keyed" phrasing invites an object-map implementation that violates the invariant.
- **FA3:** Claimed the example at `:175-227` "already has every other section." False — the example omits Mode (required by `:86`), Synthesis Checkpoint (required by `:125-136`), and Pipeline Data JSON block (required by `:138-173`).
- **FA4:** Proposed mode wording framed by tool availability. Wrong — `t5-mode-strategy.md:118-126` explicitly says mode describes dialogue-loop ownership, not transport or evidence quality.
- **RB1:** Treated "7 items" as a local edit. External active citations at `codex-dialogue.md:501` and line-specific references at `benchmark-readiness.md:35-36, :101-102` would break.
- **RB2:** Asserted `not_scoutable` claims don't appear in evidence trajectory. Wrong — `benchmark-readiness.md:102` says they DO appear as a typed absence marker; format is unspecified.
- **RB3:** Proposed a pre-flight checklist item for ledger completeness. Wrong — `provenance-and-audit.md:202-210` says this is not mechanically enforceable without T7 semantic extraction. Compliance theater.
- **HD1:** Missed that `SKILL.md:381-386` Step 6 relay doesn't list Claim Ledger; proposed ledger addition would produce output the relay drops.
- **HD2:** Missed that `HANDBOOK.md:829-831` declares `dialogue-synthesis-format.md` as a contract hub with adjacent editing obligations.
- **Branch recommendation:** Recommended appending consolidation work to `chore/track-t6-review`. Wrong branch semantics — `chore/` advertises housekeeping, not a normative contract change.

**What it taught:**

1. **Cross-contract work looks like localized work until you check ownership.** The surest tell is that a single gate spec doesn't own the whole change. If editing a file requires changes governed by three different ownership tables, it's cross-contract.

2. **Adjacent audit files matter.** The `docs/audits/` tree is a first-class source. I never checked it; that alone invalidated CF4.

3. **Ownership authority and shape authority can be separate.** Even within a single "normative" gate doc, ownership claims and shape descriptions can diverge. The matrix format now makes this explicit.

4. **Producer/parser/schema/harness is a mandatory traversal.** Any spec addition must be followed through the consumer path to the point where it either lands or drops. No shortcuts.

5. **"Surely future-Claude will read the source, right?" is not a safety net.** The map put line numbers in the Source column but didn't verify those line numbers against actual file content for the schema question. `provenance-and-audit.md:15-63` is a projection, not the record schema — an implementer following the map would transcribe the wrong fields without knowing to double-check.

**Documented in:** This session's chat history, including the full rejection
text, the verification response, and the withdrawal statement.

## Gotchas

1. **Benchmark-readiness.md `:87` uses informal shape phrasing ("`claim_id`-keyed schema") that contradicts the canonical spec at `provenance-and-audit.md:84-90` ("Dense JSON array"). The canonical wins.** Do not let gate-doc phrasings override shape-doc definitions. This is specifically where my withdrawn map went wrong on FA2. Any future reader of the gate doc should check the canonical source for shape questions.

2. **EvidenceRecord and Evidence Trajectory are different things.** EvidenceRecord is the data schema at `state-model.md:184-221` (T4-SM-05), 8 fields. Evidence Trajectory is the projection at `provenance-and-audit.md:14-48` (T4-PR-01), 5 columns. Consumer-facing synthesis surfaces emit the trajectory; internal state holds the record. Confusing the two under-specifies any implementation work.

3. **Line 233 "Do not include: Raw ledger entries" applies to the internal dialogue ledger (turn_history), not to a future `## Claim Ledger` output section.** They are technically different "ledgers," but the target doc doesn't disambiguate. Any T7 consolidation pass that adds a `## Claim Ledger` section must also edit line 233 to distinguish the two concepts or reframe the negative rule — otherwise the consolidated doc lands self-contradictory.

4. **The codex-dialogue agent reads `dialogue-synthesis-format.md` verbatim at Phase 3 entry (`codex-dialogue.md:499-501`).** The agent doesn't have an internal mental model of the assembly process — it reads the spec live. This means any change to the synthesis format immediately changes agent behavior on the next invocation. No caching layer. High leverage; high blast radius.

5. **`SKILL.md:435` silently coerces `agent_local` to `server_assisted` with `mode_source="fallback"`.** This is a live bug for any future T-04 candidate loop emitting `agent_local` — the event gets emitted with the wrong mode AND mis-labeled provenance. Not currently triggering because no producer exists, but would be a silent data-corruption bug the moment one does.

6. **`t5-mode-strategy.md:118-126` is explicit: mode describes dialogue-loop ownership, NOT transport or evidence quality.** Any mode-related writing must lead with ownership framing. Tool-availability heuristics are a different taxonomy.

7. **`claim_provenance_index[i].claim_id == i` is a dense-array invariant that persists across concessions.** Per `provenance-and-audit.md:84-90`, conceded claims retain their index entry for history, so the array has no gaps. But per audit F6 at `:141-148`, the representation of conceded slots is undefined — you can't actually emit this array today without inventing the conceded-slot format. That's the unblock F6 addresses.

8. **T4-PR-06 ledger completeness MUST is a synthesis-contract obligation without mechanical enforcement until T7 delivers semantic extraction.** Adding it to a pre-flight checklist is compliance theater (RB3). The MUST exists; the enforcement doesn't. Don't pretend otherwise.

9. **`state-model.md` lifecycle table at `:376-392` has `not_scoutable` terminal rows at `:379, :381, :388, :391`.** The not_scoutable classification happens at registration time (T4-SB-05), not as a lifecycle transition. T4-BR-05:101's syntax "`new → reinforced/revised/conceded/not_scoutable`" conflates terminals with transitions — it's a framing inaccuracy, not a vocabulary error.

10. **`benchmark-readiness.md:20-30` (T4-BR-01): silent mode downgrade is PROHIBITED during benchmark execution. Must produce an explicit mode-mismatch failure artifact.** This means the current `SKILL.md:435` silent-coercion path is incompatible with benchmark runs — a benchmark `agent_local` run today would emit a silently-coerced `server_assisted` event that violates this contract. Not currently triggering (no T-04 producer) but is a time-bomb for when one exists.

## Conversation Highlights

**Pattern across this session and all prior T6 sessions: user's reviews are surgically evidence-backed.** Every finding in the rejection cited specific file:line locations; verification could proceed mechanically. No hand-waving. The user's global CLAUDE.md instruction "Values evidence-backed analysis. Every finding cites specific file paths and line numbers" is consistently applied in practice.

**Fix-verification exchange (Phase 1):**

User: *"What changed since the handoff was written ... I fixed the summary table in [review doc]. The first column is now `Case entering T4`, and the dead-referent rows now say `Dead referent after T3 acceptance ...` and explicitly name Phase 1.5 as the reclassification step."*

User's format was Response Contract (What changed / Why / Verification / Remaining risks) — the same format their global CLAUDE.md mandates for code-change reports. The user mirrored the format back to me, which signaled "this is a verification-worthy update, apply the same rigor."

**Branch strategy exchange (Phase 2):**

User: *"The review artifact is settled now. Leaving [review doc] untracked while starting consolidation work creates an unnecessary coupling."*

User: *"So the cleaner sequence is: 1. Track the review artifact on a working branch. 2. Then do the consolidation-prep mapping against [synthesis format doc]."*

User's reasoning was procedural — about working-tree discipline, not about content. This is a pattern: they separate "housekeeping" from "substantive work" at the git level, and insist on the separation even when both could fit in one commit.

**Rejection opening (Phase 4):**

User: *"Verdict: Reject. This map is not trustworthy as a consolidation plan. It confuses ownership, undercounts active consumers, hardens a wire-format surface that prior review already flagged as unsafe, and misses at least one direct self-contradiction in the target doc. It reads like a local editing checklist for a change that is actually cross-contract work."*

The framing ("cross-contract work") was the key reframe. I had been thinking of the work as a documentation exercise; the user's frame was that the work touches multiple normative contracts with different ownership and different consumers.

**Option 3 refinement (Phase 6):**

User: *"I would not pick Option 1. It would canonize surfaces that still have open P1 audit gaps and no live end-to-end consumer path. I also would not pick Option 2 in the strong form of 'benchmark-readiness wins wholesale,' because benchmark-readiness.md itself currently says `claim_id`-keyed schema, while provenance-and-audit.md defines the canonical wire format as a dense array. So the clean resolution is not 'one doc wins'; it is 'ownership follows benchmark-readiness, semantic shape follows the canonical provenance/state-model specs.'"*

This is the session's most consequential user contribution. I had framed the three options as if one doc had to win; the user saw that ownership authority and shape authority are separable and picked both independently.

**Matrix direction (Phase 6):**

User: *"I should build the per-surface status matrix next. Do NOT step back entirely until F6/F7/F11 resolve. Reason: the matrix is the right artifact for unresolved state. It does not pretend the work is ready to implement; it makes the blockers explicit. Waiting for the audit P1s to resolve before writing the matrix would throw away the exact analysis that should drive that resolution."*

The user explicitly rejected the "step back and wait" option that seemed defensible from a safety standpoint. The reasoning ("the matrix is the right artifact for unresolved state") reframes the matrix from "plan for future work" to "analysis artifact under blocked conditions."

**Offer ambiguity pattern (recurring):**

Twice this session, the user wrote "If you want, I'll produce that [thing] next" — once for the tracking commit, once for the matrix. The phrasing is ambiguous: "I'll" could mean the user offering to do it themselves or offering to let me do it. In both cases I took the work myself after noting the ambiguity, and neither time did the user correct me. The pattern seems to be: the user offers to do clerical/analytic work that's within Claude's role, and is happy to let me execute if I can do it immediately and correctly.

**Sequencing language:**

User repeatedly uses "2 first, then 1" style ordering when correcting option order. Pattern: they will either accept my option order or invert it with an explicit callout. They do not leave ordering implicit.

## User Preferences

**Provides structured adversarial reviews with severity labels and specific file:line citations.** Pattern across this session, the prior session, and the prior-prior session. Sections: Verdict, Critical failures, Fragile assumptions, Real-world breakpoints, Hidden dependencies, What a hostile reviewer would exploit, What must change. Closing paragraph identifies what survives scrutiny.

**Values evidence-backed analysis.** User said (verbatim, past session): *"Every finding cites specific file paths and line numbers. Analysis that makes claims without citations is 'inference, not proof.'"* This session: every finding in the rejection had a citation; verification could proceed mechanically.

**Expects correct scope and ownership framing.** The recurring correction across multiple sessions is scope displacement — user catches and corrects when work is mis-assigned to a phase, gate, or scope boundary.

**Writes substantive amendments themselves.** User's verbatim (prior session): *"I will review this draft and then share my findings in the next session."* Claude's role is analysis, verification, and review. Git commits that preserve the state or perform housekeeping are negotiable — user is willing to let me do them.

**Expects precision over convenience.** User catches conflation (T3/T4, fairness/adequacy, specification/implementation, T6/T7 scope, ownership/shape authority) and requires the distinction to be explicit in the artifact. Verbatim from prior session: *"Those two positions do not coexist cleanly."*

**Works in closed units with clear scope boundaries.** Each review pass, each decision, each edit maintains a clear boundary between what is in scope and what is deferred. The user does NOT like mixed concerns in single artifacts.

**Uses Response Contract format for reporting changes.** The global CLAUDE.md format (What changed / Why / Verification performed / Remaining risks) is the user's default for reporting code or doc changes. When they use it in a message, they're signaling "apply verification rigor to this."

**Sequencing language is explicit.** The user uses "2 first, then 1" or similar ordering callouts rather than leaving sequencing implicit. They will either accept my option order or invert it with a callout.

**Offer pronoun ambiguity is a pattern.** Twice this session: "If you want, I'll [do X]." Both times I interpreted this as "the user offering to do X themselves, asking Claude's preference" and took the work myself. User did not correct either interpretation. The offered work was within Claude's role (git commit, analytic matrix) and could be executed immediately. Future-Claude: treat these as offers-with-choice; take the work if it's within Claude's role (analysis, verification, git hygiene) and defer if it's substantive amendment to a normative artifact.

**Review language is direct and evaluative.** User uses "Reject" and "Major revision" and "Minor revision" as verdict categories. No hedging. When they accept, they use shorter acknowledgments. The directness is a feature — it makes status unambiguous.

**Trust calibration increases with verification evidence.** User's initial rejection included phrases like "contract theater" and "compliance theater" — strong skepticism. After the verification pass confirming all 14 findings, the next message was collaborative ("Option 3 with one refinement"). The tonal shift correlates with Claude demonstrating the verification discipline the skill prescribes.
