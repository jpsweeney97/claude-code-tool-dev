---
date: 2026-04-05
time: "04:50"
created_at: "2026-04-05T04:50:17Z"
session_id: 01018e07-45dc-4392-b52e-364ab02e5734
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-05_04-14_t6-review-adjudication-correction-patch-and-scrutiny-findings.md
project: claude-code-tool-dev
branch: docs/t04-f6-f7-f11-ownership
commit: a3dc5cd3
title: T6 review correction merged (PR #91) and F6/F7/F11 branch initialized
type: handoff
files:
  - docs/reviews/2026-04-04-t04-t6-benchmark-first-design-composition-review.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/benchmark-readiness.md
---

# Handoff: T6 review correction merged (PR #91) and F6/F7/F11 branch initialized

## Goal

Close out the T6 review adjudication-correction work cleanly and stage the
next project-level thread (F6/F7/F11 ownership assignment in
`benchmark-readiness.md`).

**Trigger:** Prior session ended with the T6 review correction patch applied
to the working tree plus 6 scrutiny findings awaiting user response. User's
explicit next-session direction was verbatim *"I will respond to your review
in the next session."* This session picked up that commitment.

**Stakes:** Medium. The T6 review correction is now a shipped artifact on
`main` (merged via PR #91), which means the ownership error it fixes is no
longer in the repo's load-bearing review doc. The next thread — F6/F7/F11
ownership assignment — is the one the committed review explicitly points
at by saying those findings *"remain unassigned in current gate tables."*
Resolving that closes the open question the prior session's scrutiny
Finding 1 elevated.

**Success criteria:**
- All 6 scrutiny findings addressed substantively (user's responsibility;
  Claude's job was verification)
- T6 review correction committed and landed on `main`
- Local state clean; ready to start new work
- F6/F7/F11 branch initialized from updated `main`

**Connection to project arc:** T4 close-out (SY-13) → reclassification →
Path-2 benchmark constraint → T6 composition (7 review passes across 3
sessions) → ownership resolution matrix → review-doc correction patched
and scrutinized → **correction refinements applied, committed, merged to
main via PR #91 (this session)** → **F6/F7/F11 ownership assignment
(next session, fresh branch)** → T7 executable slice (unblocked once
F6/F7/F11 owners declared or explicit gate-declarations in place).

## Session Narrative

### Phase 1: Load and absorption

Session opened with `/handoff:load` resolving to the prior session's
handoff (1330 lines). Loaded in one Read call, archived the source to
`docs/handoffs/archive/2026-04-05_04-14_t6-review-adjudication-correction-patch-and-scrutiny-findings.md`
(commit `f092671f`), wrote state file to `docs/handoffs/.session-state/handoff-01018e07-45dc-4392-b52e-364ab02e5734`.

Verified working tree matched the handoff's claimed state exactly: one
unstaged modification to the T6 review doc on `chore/track-t6-review`.
Surfaced the 6 scrutiny findings (3 Medium, 3 Low) plus a
premise-check observation ("DOES NOT YET COMPOSE" header tension) for
the user's response.

### Phase 2: User's findings response

User delivered their response using Response Contract format
(What/Why/Verification/Remaining Risks) as a single substantive message.
Summary of what they applied:

- **Finding 1 (Medium) — softened F6/F7/F11 wording**: from "producer-side
  spec gaps in the T4 authority set" to *"unassigned in current gate tables
  even though they target gaps in the T4 provenance/state-model authority
  set that must be resolved before the affected wire formats can be stably
  canonized."* This precisely separates where-gaps-live from who-owns-remediation.
- **Finding 3 (Medium) — bridge paragraph added at `:79-81`**: new text
  *"Ownership of fixing these paths is corrected below: `agent_local`
  documentation is T5-owned, while the consumer-code breakpoints are T7
  executable-slice work."*
- **Finding 4 (Medium) — orphan surfaced in disposition**: added at
  `:182-185` — *"The evidence-trajectory consumer projection likewise
  remains unassigned in current gate tables and needs either an explicit
  owner or an explicit declaration that no T4-T7 gate owns it."*
- **Finding 5 (Low-Medium) — "specification" → "documentation" surfaces**:
  matches the scope of the `:35-36` citation.
- **Finding 2 (Low) — "producer-side" jargon eliminated entirely** (not
  defined; removed).
- **Finding 6 (Low) — adjudication principle concrete example added**:
  *"For example, `benchmark-readiness.md:87` describes the provenance
  index as 'claim_id-keyed schema', while `provenance-and-audit.md:84-90`
  defines the canonical dense-array wire format."*

User's note on "Remaining Risks": the "DOES NOT YET COMPOSE" header tension
was kept by design; patch uncommitted at time of report.

### Phase 3: Verification pass on applied fixes

Dispatched 4 parallel reads: full T6 review doc (current state, ~195
lines), full diff, `benchmark-readiness.md:80-100` (verify `:87` citation
content), `provenance-and-audit.md:80-94` (verify `:84-90` citation
content).

**All citations verified exactly.** `benchmark-readiness.md:87` literally
contains *"claim_id-keyed schema"* in the pipeline epilogue schema row.
`provenance-and-audit.md:84-90` is precisely the Canonical Wire Format
section declaring *"Dense JSON array. Invariant: `claim_provenance_index[i].claim_id == i`..."*

The two phrasings are substantively in tension — "claim_id-keyed schema"
reads as map-like (`{0: entry, 1: entry}`) while "dense JSON array" with
position=claim_id is array-like. The Finding 6 citation example is not
decorative; it's load-bearing. This raised the Finding 6 fix from a
token check-the-box to a substantively stronger artifact.

**One minor observation surfaced:** The T6 Verdict table row at `:170`
still read *"Ownership correction below; remediation routed to T4/T5/T7"*.
After Finding 1's fix explicitly declined T4 ownership, the "T4" in the
table shorthand could now be read as re-asserting what the prose
disposition denies. Flagged as optional with 3 options (keep, tighten to
"see disposition", specify "T5/T7 owners; F6/F7/F11 unassigned"). Honored
the prior session's Learning that I shouldn't hide recommendations-I'd-apply.

### Phase 4: User applied `:170` tightening and committed

User took the `:170` observation, rephrased it to *"Ownership correction
below; see disposition for routed and unassigned surfaces"* (cleaner than
any of my 3 suggested options — acknowledges both routed and unassigned
categories in one compact phrase), and created commit `09a7e767` with the
drafted commit message.

User's Response Contract summary confirmed: `git diff --check` passed;
working tree clean on `chore/track-t6-review`; verdict row verified.

### Phase 5: Landing strategy decision

User delivered a Recommendation/Why/sequence-plan message choosing Option 1
(land PR #91 as-is, 12 commits and all). Key reasoning: the 12-commit
count was a volume difference from earlier framing, not a kind difference
— *"the extra six commits are still the same class of work this repo
already carries on `main`: `docs(handoff)` lifecycle history. That makes
this a scope-expansion in volume, not in kind."*

Explicit sequence delivered: (1) merge PR #91, (2) save a handoff, (3)
start F6/F7/F11 ownership-assignment work on a fresh branch from updated
`main`.

### Phase 6: Merge execution

Checked repo merge pattern by reading `git log --oneline --merges origin/main -5`
— found 5 merge commits in recent history including `f1085302 Merge pull
request #85`. Pattern matched: repo uses merge commits for PR landings,
not squash/rebase. Executed `gh pr merge 91 --merge`.

PR #91 state transitioned to MERGED at `2026-04-05T04:47:50Z` with merge
commit `a3dc5cd3`. Verified via `gh pr view 91 --json state,mergedAt,mergeCommit`.
Fetched origin main — local main was 7 commits behind origin (6 pre-existing
+ the merge itself).

### Phase 7: Branch setup for F6/F7/F11 work

Subtle ordering constraint surfaced: the handoff-save skill writes a new
markdown file and auto-commits. Branch protection on `main` blocks `Write`
operations. So save-before-branch-creation would fail. Adjusted user's
declared sequence to: checkout main → pull → create new branch → save
handoff on the new branch.

Executed `git checkout main && git pull origin main && git checkout -b
docs/t04-f6-f7-f11-ownership` in one compound command. Fast-forward
updated local main by 7 commits. New branch created from updated main
head (`a3dc5cd3`). Working tree clean on new branch.

Branch name chosen to match repo convention (`docs/t04-*` pattern used by
`docs/t04-t4-scouting-and-evidence-provenance` from earlier T-04 work).

### Phase 8: Save invoked (this step)

Invoked `handoff:save` skill via the Skill tool. Reading synthesis-guide
and format-reference, then drafting this handoff.

## Decisions

### Decision 1: Verification verdict "Ready to commit" on user's applied fixes

**Choice:** After reading the current file state, the full diff, and
verifying both citations in the Finding 6 example, issue the verdict
"Ready to commit" with one optional observation (`:170` table cell)
flagged as a judgment call.

**Driver:** Per-finding verification showed all 6 findings addressed
substantively, both new citations verified exactly against source files,
no new implicit claims introduced, and the diff was bounded to the single
review file. The Finding 1 fix in particular correctly closed the
scope-displacement recursion from the prior session's Learnings by making
"unassigned" explicit rather than inferred.

**Alternatives considered:**
- **Hold the verdict for a second adversarial pass:** Would find more
  issues if any exist. Rejected because the prior session had already
  applied 5 adversarial perspectives, and the current fixes addressed
  every identified issue. Marginal additional pass has diminishing returns.
- **Verdict "Defensible" without flagging `:170`:** Would mean the patch
  is ready with zero residual observations. Rejected because `:170`
  had a subtle inconsistency with the Finding 1 fix — honoring the
  prior-session Learning that I shouldn't hide recommendations-I'd-apply.
- **Verdict "Needs more work" on the residual `:170` issue:** Would block
  commit on a minor table-cell phrasing. Rejected because the full-prose
  disposition two paragraphs later already clarifies; `:170` is a
  compression artifact, not a factual error.

**Implications:**
- User took the `:170` observation as actionable (consistent with prior
  pattern) and applied a tightening better than my 3 options.
- The verification leg closed cleanly on the second pass, allowing
  direct commit without additional iteration.
- The prior-session Learning about "flagged = actionable regardless of
  severity" held at 100% again across this session.

**Trade-offs accepted:**
- Flagging the `:170` observation lengthened the verification response.
  But the user applied the fix, so the additional content was productive.
- The observation could have been framed as "keep as-is" (my lean) but
  I surfaced it honestly per the Learning. This might occasionally
  generate work when "keep as-is" would have been acceptable — but the
  user's apply-rate suggests they'd prefer the option to decide.

**Confidence:** High (E3) — triangulated across current file state
(195 lines read), diff (71 insertions / 40 deletions), and source file
citations (`benchmark-readiness.md:87`, `provenance-and-audit.md:84-90`).

**Reversibility:** High — verification findings can be revised if
counter-evidence emerges; user can choose not to apply any given
observation.

**What would change this decision:** If the citation verification had
failed (e.g., `benchmark-readiness.md:87` didn't contain "claim_id-keyed
schema"), the verdict would have been "Needs revision" instead.

### Decision 2: Use `--merge` strategy (merge commit) for PR #91

**Choice:** When merging PR #91, use `gh pr merge 91 --merge` to produce
a merge commit, matching the repo's existing pattern for PR landings.

**Driver:** Checked recent merge history via `git log --oneline --merges
origin/main -5` and found 5 merge commits including the last PR merge:

```
2a82edb6 Merge branch 'docs/t04-t4-scouting-and-evidence-provenance'
80ae21f5 Merge chore/plan-revision-persistence-hardening: plan review rounds 1-4
664fc249 Merge branch 'feature/codex-collaboration-safety-substrate'
0af1e3de Merge branch 'worktree-claude-md-refining'
f1085302 Merge pull request #85 from jpsweeney97/feature/claude-code-docs-auto-build
```

The pattern is clear: PR merges produce merge commits, not squash
commits or fast-forward rebases.

**Alternatives considered:**
- **`--squash`:** Would collapse 12 commits into one. Rejected because
  the handoff-lifecycle commits are semantically distinct entities and
  squashing would lose the individual `docs(handoff)` history this repo
  intentionally preserves.
- **`--rebase`:** Would replay commits linearly without a merge commit.
  Rejected because it doesn't match repo pattern and would obscure the
  feature-branch boundary.

**Implications:**
- Main history at `a3dc5cd3` now has a merge commit showing the PR
  boundary. Future `git log --graph` visualizes the correction work as
  a discrete branch.
- All 12 commits are preserved individually on `main`, consistent with
  the repo's handoff-history tracking intent.

**Trade-offs accepted:**
- Linear-history purists would prefer rebase for cleaner `git log`.
  Accepted because the repo's existing pattern indicates the user
  (solo dev) prefers merge commits for feature/chore PR boundaries.

**Confidence:** High (E2) — verified via 5 prior merge commits in recent
history, all using the same pattern.

**Reversibility:** Low — once merged, the merge strategy is baked into
history. Revert would require `git revert -m 1 a3dc5cd3` which creates
a revert commit, not a re-do.

**What would change this decision:** If the repo were to adopt linear
history (e.g., squash-only GitHub setting), the choice would change. As
of this session, the branch protection/PR rules appear to allow all
three strategies.

### Decision 3: Checkout-then-save ordering instead of user's declared save-then-checkout

**Choice:** Execute `git checkout main → git pull → git checkout -b docs/t04-f6-f7-f11-ownership`
BEFORE invoking the save skill, even though the user's declared sequence
had "save a handoff" at step 2 and "start F6/F7/F11 work on a fresh branch"
at step 3.

**Driver:** The handoff-save skill creates a markdown file and auto-commits
via `auto_commit.py`. The project's PreToolUse branch-protection hook
blocks `Write` operations on `main`. If I had checked out main and then
invoked save, the save would fail when it tried to write the new handoff
file. The only way to satisfy both the save operation and the branch
protection is to be on a non-main branch at save time.

**Alternatives considered:**
- **Save on `chore/track-t6-review` (merged but still checked out):**
  The handoff file would be committed to the merged branch, creating an
  orphan commit that wouldn't reach main without another merge. Rejected
  because it creates stranded state.
- **Skip save entirely until next session:** Would respect user's
  declared order but lose session context. Rejected because the user
  explicitly asked for a handoff between merge and new-branch work.
- **Save with manual file write bypassing auto-commit:** Would work but
  departs from the save skill's contract. Rejected because the
  auto-commit step ensures the handoff is tracked as soon as it exists.

**Implications:**
- Handoff commit lands on `docs/t04-f6-f7-f11-ownership` branch, not on
  main directly. This means the handoff will merge to main when
  F6/F7/F11 work lands (via PR or direct merge).
- User's declared sequence order is preserved in spirit (save → new
  work) even though the branch creation precedes save by a few seconds.

**Trade-offs accepted:**
- Slight departure from user's literal sequence. Mitigated by explicit
  explanation in chat before executing the reorder.

**Confidence:** High (E1) — single source reasoning from the
branch-protection hook's known behavior (blocks Write on `main`).

**Reversibility:** High — the handoff file can be moved or the branch
deleted if the ordering creates problems. No irreversible action.

**What would change this decision:** If the branch-protection hook were
disabled or reconfigured to allow Write on main for handoff files
specifically, the save-then-branch ordering would become viable.

### Decision 4: Branch name `docs/t04-f6-f7-f11-ownership`

**Choice:** Name the new branch `docs/t04-f6-f7-f11-ownership` rather
than `feature/*`, `fix/*`, or another pattern.

**Driver:** The work is amending `benchmark-readiness.md` (a spec/plan
document) to add explicit ownership assignments for audit findings
F6/F7/F11. The existing repo pattern for T-04 spec work is
`docs/t04-t4-scouting-and-evidence-provenance` — `docs/` prefix with
`t04-*` body.

**Alternatives considered:**
- **`feature/f6-f7-f11-ownership-assignment`:** "Feature" framing works
  for adding new content. Rejected because the repo uses `docs/*` for
  spec amendments specifically.
- **`fix/t04-f6-f7-f11-ownership`:** "Fix" framing emphasizes the gap
  being closed. Rejected because the work is additive (adding
  assignments) rather than correcting existing wrong assignments.
- **`chore/t04-f6-f7-f11-ownership`:** "Chore" framing matches the
  prior session's `chore/track-t6-review`. Rejected because this work
  is more substantive than tracking/maintenance — it's amending a
  normative spec to resolve an open question.

**Implications:**
- Branch semantics match repo convention, making it easy for future
  readers to understand the work's type from the branch name alone.
- Consistent with the `docs/*` pattern for content additions to
  existing specs.

**Trade-offs accepted:**
- Branch name is long (34 characters). Shorter would be possible but
  at cost of clarity.

**Confidence:** Medium (E1) — based on one similar prior branch name
and the global CLAUDE.md's recognized-patterns list.

**Reversibility:** High — branch can be renamed or recreated before
any commits land.

**What would change this decision:** If the user expresses a preference
for a different naming, switch immediately.

## Changes

### `docs/reviews/2026-04-04-t04-t6-benchmark-first-design-composition-review.md`

**Purpose:** The T6 composition review artifact. This session applied
the user's finding responses (substance was user-drafted; this session's
role was verification and scrutiny verdict).

**State before session:** 187 lines, uncommitted in working tree, with
6 unaddressed scrutiny findings from the prior session.

**State after session:** 195 lines, committed as `09a7e767` on
`chore/track-t6-review`, then merged to `main` via PR #91 (merge commit
`a3dc5cd3`).

**Changes applied (all by user, verified by Claude):**

1. **Bridge paragraph at `:76-81`** — Added closing sentence to the
   "concrete failure paths" paragraph: *"Ownership of fixing these paths
   is corrected below: `agent_local` documentation is T5-owned, while
   the consumer-code breakpoints are T7 executable-slice work."*
   (Finding 3 fix — bridges failure paths to the ownership map.)

2. **Finding 1 soft wording at `:179-185`** — Reframed F6/F7/F11 from
   "producer-side spec gaps in the T4 authority set" to *"remain
   unassigned in current gate tables even though they target gaps in
   the T4 provenance/state-model authority set that must be resolved
   before the affected wire formats can be stably canonized."*

3. **Orphan surface in disposition at `:182-185`** — Added new sentence:
   *"The evidence-trajectory consumer projection likewise remains
   unassigned in current gate tables and needs either an explicit owner
   or an explicit declaration that no T4-T7 gate owns it."* (Finding 4
   fix.)

4. **"specification surfaces" → "documentation surfaces"** at `:89-90`
   and `:178-179` — Narrows wording to match the scope of `:35-36`
   citation. (Finding 5 fix.)

5. **"producer-side" jargon eliminated** — Word removed entirely rather
   than defined. (Finding 2 fix by elimination.)

6. **Adjudication principle concrete example at `:94-98`** — Added:
   *"For example, `benchmark-readiness.md:87` describes the provenance
   index as 'claim_id-keyed schema', while `provenance-and-audit.md:84-90`
   defines the canonical dense-array wire format."* (Finding 6 fix —
   substantively load-bearing, not decorative.)

7. **Verdict table row at `:170` tightened** — From *"Ownership
   correction below; remediation routed to T4/T5/T7"* to *"Ownership
   correction below; see disposition for routed and unassigned surfaces."*
   (My minor observation; user's rephrase is better than any of my
   3 suggested options.)

**Diff stats:** 71 insertions, 40 deletions, 111 changed lines in one
file. Total file size: 195 lines.

### Branch and PR lifecycle

**PR #91 created:** `docs(reviews): track and correct T6 composition review`
- URL: https://github.com/jpsweeney97/claude-code-tool-dev/pull/91
- Base: `main`, Head: `chore/track-t6-review`
- 12 commits (2 substantive + 10 handoff-lifecycle)
- 4841 additions, 0 deletions

**PR #91 merged:** At `2026-04-05T04:47:50Z` via `--merge` strategy
- Merge commit: `a3dc5cd3`
- Commit message: `Merge pull request #91 from jpsweeney97/chore/track-t6-review`

**New branch created:** `docs/t04-f6-f7-f11-ownership` from `main@a3dc5cd3`
- For next work: F6/F7/F11 ownership assignment in benchmark-readiness.md
- Clean working tree, no uncommitted changes

### Git state summary

| Before session | After session |
|---|---|
| Branch: `chore/track-t6-review` (2 commits ahead of main; 1 unstaged) | Branch: `docs/t04-f6-f7-f11-ownership` (0 commits ahead of updated main; clean) |
| Local main: 6 ahead of origin | Local main: synced to origin (`a3dc5cd3`) |
| T6 review patch: uncommitted | T6 review correction: merged to main |
| PR #91: does not exist | PR #91: MERGED |
| Handoffs: prior handoff in active | Handoffs: prior archived, new handoff being written |

## Codebase Knowledge

### T6 review doc (final state, 195 lines)

| Section | Lines | State |
|---|---|---|
| Scope | `:3` | Filename normalized to `2026-04-01-t04-benchmark-first-design-plan.md` |
| State Model: COMPOSES | `:5-25` | Unchanged |
| Loop Structure: COMPOSES | `:27-48` | Unchanged |
| Synthesis Contract: DOES NOT YET COMPOSE | `:50-113` | **Heavy revision.** Contains adjudication correction, ownership map, Finding 6 concrete example |
| Coverage Adequacy | `:115-127` | Unchanged |
| Scope / Comparability | `:129-150` | **Minor revision.** Mode migration paragraph now cites T5+T7 correctly |
| B8 Anchor Adequacy | `:152-160` | Unchanged |
| T6 Verdict header + table | `:162-171` | **Revised.** Synthesis contract row updated to "see disposition" |
| T6 Disposition | `:173-190` | **Heavy revision.** Adjudication correction disposition with F6/F7/F11 framing |
| Deferred to T7 | `:192-195` | Unchanged |

### `benchmark-readiness.md:87` verified content

```
| Pipeline epilogue schema | Add `claim_provenance_index` field to epilogue contract with `claim_id`-keyed schema, two variants (scouted, not_scoutable) | T7 | [dialogue-synthesis-format.md:138-147](...) |
```

The "claim_id-keyed schema" phrase appears on exactly line 87. This is
the informal description that the committed Finding 6 example contrasts
against the canonical wire format.

### `provenance-and-audit.md:84-90` verified content

```
84: ### Canonical Wire Format
85: 
86: Dense JSON array. Invariant: `claim_provenance_index[i].claim_id == i`
87: for all entries. Array length equals `next_claim_id`. All allocated
88: `claim_id`s persist in the index, including claims later conceded
89: (concession removes from `verification_state` but the provenance entry
90: is historical). No sparse IDs, no gaps, no reordering.
```

This is exactly the section cited as the canonical definition. The
"dense JSON array" phrasing is substantively different from the
informal "claim_id-keyed schema" — the Finding 6 example is not a
token citation but a load-bearing demonstration of the ownership-vs-shape
distinction.

### PR #91 commit layout (now on main)

The 12 commits that landed with PR #91:

| # | Commit | Description | Type |
|---|---|---|---|
| 1 | `87526c25` | save T4 reclassification and Path-2 benchmark contract | handoff |
| 2 | `58e07db2` | archive T4 reclassification | handoff |
| 3 | `fd966428` | save T6 composition check — three passes to defensible verdict | handoff |
| 4 | `2f22bdc9` | archive T6 composition 3-pass | handoff |
| 5 | `106f77ea` | save T6 composition analysis — four review passes | handoff |
| 6 | `0b8f6a9f` | archive T6 composition 4-pass | handoff |
| 7 | **`40e30b2c`** | **track T6 benchmark-first design composition review** | **substantive** |
| 8 | `45baa358` | save T6/T7 ownership resolution and per-surface status matrix | handoff |
| 9 | `13ef3b92` | archive T6/T7 ownership resolution | handoff |
| 10 | `48e01fe2` | save T6 review adjudication-correction patch and scrutiny findings | handoff |
| 11 | `f092671f` | archive T6 review adjudication-correction | handoff |
| 12 | **`09a7e767`** | **correct T6 ownership framing via adjudication correction** | **substantive** |

**Then:** merge commit `a3dc5cd3` on main.

### Repo merge-strategy pattern

Verified via `git log --oneline --merges origin/main -5`:

| Commit | Style |
|---|---|
| `2a82edb6 Merge branch 'docs/t04-t4-scouting-and-evidence-provenance'` | `Merge branch` (local merge) |
| `80ae21f5 Merge chore/plan-revision-persistence-hardening: plan review rounds 1-4` | `Merge chore/` (local merge with subject) |
| `664fc249 Merge branch 'feature/codex-collaboration-safety-substrate'` | `Merge branch` (local merge) |
| `0af1e3de Merge branch 'worktree-claude-md-refining'` | `Merge branch` (local merge) |
| `f1085302 Merge pull request #85 from jpsweeney97/feature/claude-code-docs-auto-build` | `Merge pull request` (GitHub PR merge) |

**Pattern:** Both local merges (`git merge`) and GitHub PR merges (via
`gh pr merge --merge`) produce merge commits. This repo does not use
squash-merge or fast-forward-only. The pattern held for PR #91 —
`Merge pull request #91 from jpsweeney97/chore/track-t6-review`.

### Branch naming conventions observed

| Pattern | Example | Used For |
|---|---|---|
| `chore/*` | `chore/track-t6-review` | Review tracking, maintenance |
| `docs/*` | `docs/t04-t4-scouting-and-evidence-provenance` | Spec/docs work |
| `feature/*` | `feature/claude-code-docs-auto-build` | New functionality |
| `feat/*` | (recognized but not seen recent) | Alias for feature |

For T-04 related spec amendments, `docs/t04-*` is the established pattern.

## Context

### Mental model for this session

**Framing:** This session is a closure/transition session — close out the
T6 review correction arc cleanly, then stage the next thread. It's not
substantive content work; it's verification, merging, and handoff.

**Core insight:** The verification-to-apply loop is symmetric. When I
(Claude) produce review/scrutiny output, the user's pattern is to apply
every flagged item regardless of severity label. This session confirmed
the pattern at 100% for the third consecutive session (6 findings + 1
optional observation = 7 items flagged, 7 items applied). The Learning
from the prior session is now a workflow invariant, not a hypothesis.

**Secondary insight:** Scope-displacement recursion, when applied to a
correction artifact, terminates at the table-cell level. The T6 review
correction had three layers of displacement:
1. **Layer 1:** Original review over-assigned T7/T5 work to T6 (corrected
   via adjudication patch).
2. **Layer 2:** Call 2 reframe's implicit F6/F7/F11 → T4 assignment (caught
   by scrutiny Finding 1; corrected via "unassigned in current gate tables"
   phrasing).
3. **Layer 3:** `:170` verdict table cell's "remediation routed to T4/T5/T7"
   shorthand (caught as a minor observation; corrected via "see disposition"
   rephrase).

Each layer was thinner than the previous. Layer 3 was one line; the fix
was one phrase. Beyond Layer 3, the only remaining "tension" is the
"DOES NOT YET COMPOSE" header rhetorical friction, which the user chose
to keep by design. The recursion is structurally closed.

**Tertiary insight:** Local main and origin main can diverge significantly
without visible effect until a PR is created. Before this session, local
main was 6 commits ahead of origin. The `git rev-list --count main..chore/track-t6-review`
reported 6 (measured against LOCAL main), but the PR compared against
`origin/main` and reported 12 commits. This discrepancy is invisible
until a push operation forces reconciliation.

### Project state (post-merge)

- **T4:** Closed at SY-13. Tracked, reviewed, committed.
- **T5:** Designs accepted. `agent_local` mode ownership clarified in
  corrected T6 review.
- **Benchmark contract:** Path-2 constraint encoded.
- **T6:** Composition review landed. Verdict preserved. Ownership
  correction shipped. No gates reopened. Open thread: whether "T6 is
  done" in an administrative sense (the review itself doesn't settle
  this; the disposition says T6 won't own the missing consolidation).
- **Audit findings F6/F7/F11:** Still unresolved in any gate table.
  Committed review says they "remain unassigned in current gate tables"
  targeting the T4 authority set. Resolution is the project-level open
  thread this branch (`docs/t04-f6-f7-f11-ownership`) exists to address.
- **T7:** Scope clarified (consumer/gate owner, not spec author). Still
  blocked on F6/F7/F11 resolution before wire formats can be canonized.

### Environment

- Working directory: `/Users/jp/Projects/active/claude-code-tool-dev`
- Branch: `docs/t04-f6-f7-f11-ownership` (0 commits ahead of main; clean)
- Main: `a3dc5cd3` (in sync with origin/main)
- No pushes this session beyond PR #91 push/merge
- No tests run (docs-only session)

## Learnings

### 100% apply rate across 3 sessions is now a workflow invariant

**Mechanism:** When I flag any item in verification or scrutiny output,
the user applies it in the subsequent response. Severity labels (Medium,
Low, "optional") don't affect application probability. This held at 100%
for:
- Prior session 1: 2 "optional" tightenings applied
- Prior session 2 (this session's prior): 6 scrutiny findings applied
- This session: 6 findings + 1 optional `:170` observation = 7 items
  applied

**Evidence:** Phase 2 of this session (user's Response Contract message)
explicitly listed fixes for all 6 findings. Phase 4 (user's `:170`
response) applied my optional observation. Every flagged item became a
commit-level change.

**Implication:** Future verification passes should treat flagging as
committing-to-user's-workflow. If I wouldn't apply a fix myself, I
shouldn't flag it. If I would, I should flag it without severity
hedging. The test: "would I apply this in my own work?" If yes, flag.
If no, don't mention.

**Watch for:** The inverse failure mode — flagging items I wouldn't
apply. This would inflate user workload. Mitigation: before flagging,
imagine doing the fix; if it feels like over-engineering, don't flag.

### User's rephrases frequently improve on my starting points

**Mechanism:** When I offer multiple options for a fix, the user often
synthesizes a cleaner version than any individual option. This session's
`:170` fix is the clearest example: I offered 3 options (keep,
"see disposition", "T5/T7 owners; F6/F7/F11 unassigned"), and the user
produced *"see disposition for routed and unassigned surfaces"* — which
combines the brevity of option 2 with the category-acknowledgment of
option 3.

**Evidence:** Phase 4 commit `09a7e767` shows the final `:170` wording.
Compare against my 3 options in Phase 3 verification output.

**Implication:** When offering options, frame them as "starting points
for your synthesis" rather than "pick one." The user's judgment on
wording is reliably better than my individual proposals.

**Watch for:** Don't force options when the user has a clear preference.
Sometimes a single recommendation is better than a menu.

### Branch protection + save skill creates an ordering constraint

**Mechanism:** The handoff-save skill writes a markdown file via Write
and auto-commits via `auto_commit.py`. The project's PreToolUse
branch-protection hook blocks `Write` on `main`. Therefore, saving a
handoff while on `main` fails. The only way to save post-merge is to
checkout a non-main branch first.

**Evidence:** This session's Phase 7 — I adjusted the user's declared
sequence (save at step 2, branch at step 3) to branch-first-then-save
because of this constraint. Explained the adjustment in chat before
executing.

**Implication:** Any session that follows merge-to-main with handoff-save
must create the next working branch BEFORE the save. The handoff commit
lands on the new branch, which is semantically correct because the
handoff documents the transition to the new work.

**Watch for:** Forgetting this constraint and attempting save-on-main.
The Write hook will block; user will see an error. The fix is to
checkout-then-retry.

### Local main can diverge from origin main invisibly

**Mechanism:** Local commits on `main` accumulate without automatic
push. `git log` on local shows them; `origin/main` doesn't. Branches
created from local main inherit the divergence. `git rev-list --count
main..branch` measures against LOCAL main; PR comparisons measure
against ORIGIN main. These can report very different counts.

**Evidence:** Before PR #91, local main was 6 commits ahead of origin.
My Phase 5 message reported "6 commits ahead of main" (measured
locally). The PR then reported 12 commits (measured against origin).
The 6-commit difference surprised the user's expectations.

**Implication:** When describing branch state to the user, clarify
whether the baseline is local or origin. If they're about to push or
PR, origin is the relevant baseline.

**Watch for:** Using `git rev-list --count main..branch` without
checking whether local main is synced to origin. If unsure, fetch first
or use `origin/main` as the explicit base.

### Finding 6's citation example is substantively load-bearing

**Mechanism:** A citation example can be either decorative (check the
box that the principle is concretized) or load-bearing (the specific
example demonstrates a real tension that the principle resolves). The
user's Finding 6 fix was the latter: `benchmark-readiness.md:87` uses
"claim_id-keyed schema" (reads as map-like) while
`provenance-and-audit.md:84-90` defines "Dense JSON array" (position =
claim_id). These are genuinely different shapes, making the principle
"benchmark-readiness governs ownership; it does not override canonical
shape" demonstrably true rather than merely asserted.

**Evidence:** Verified both citations this session. Line 87 of
benchmark-readiness.md contains exactly "claim_id-keyed schema" in the
pipeline epilogue schema row. Lines 84-90 of provenance-and-audit.md
are the Canonical Wire Format section with the dense array spec.

**Implication:** When asked to add a concrete example to an abstract
principle, pick one where the abstraction actually does work. Random
examples weaken the principle; load-bearing examples strengthen it.

**Watch for:** Adding examples for their own sake. The test is: does
this example demonstrate a tension or conflict that the principle
resolves? If no, find a better example or drop the request.

## Next Steps

### 1. F6/F7/F11 ownership assignment in `benchmark-readiness.md` (user's step 3)

**Dependencies:** None — branch is ready (`docs/t04-f6-f7-f11-ownership`,
clean working tree, based on updated main).

**What to read first:** The audit file for F6/F7/F11 exact content:
`docs/audits/2026-04-02-t04-t4-evidence-provenance-rev17-team.md` —
specifically `:141-148` (F6 concession boundary), `:152-164` (F7
serialization handoff), and `:216-228` (F11 schema versioning).

Then the current state of `benchmark-readiness.md` to identify where
ownership assignments should land. The T4-BR-01 through T4-BR-09 gate
tables are the likely targets.

**Approach suggestion (user drives):** The committed T6 review says
F6/F7/F11 "remain unassigned in current gate tables even though they
target gaps in the T4 provenance/state-model authority set." The
assignment amendment needs to either:
- (a) Explicitly assign owners (to whom? T7? T-post-hoc? A new packet?)
- (b) Explicitly declare no current owner with trigger conditions for
  when assignment must happen
- (c) Gate the dependent work (T7 wire-format surfaces can't be
  canonized until F6/F7/F11 resolve)

Per the user's verbalized workflow pattern: expect the user to draft
the amendment themselves. My role: gather context, surface options,
verify final draft.

**Acceptance criteria:** `benchmark-readiness.md` has an explicit
ownership or gating declaration for each of F6, F7, F11 that would
survive adversarial scrutiny (i.e., no implicit inference the way the
prior "producer-side" framing did).

**Potential obstacles:** F6/F7/F11 may span multiple wire format
surfaces. The ownership answer might differ per finding. Don't assume
uniformity.

### 2. Verify F6/F7/F11 resolution unblocks T7 executable slice

**Dependencies:** Next Step 1 must land first.

**What to read first:** Whatever T7 acceptance criteria exist in the
current spec tree. Likely in `t7-conceptual-query-corpus-design-constraint.md`
or similar.

**Approach:** After F6/F7/F11 assignment, re-check whether T7's
prerequisites are satisfied. The committed T6 review says T7 is "blocked
on audit resolution." Verify this block is removed by the assignment
work (or is still pending additional conditions).

**Acceptance criteria:** Clear statement of whether T7 can proceed
post-F6/F7/F11-assignment, and what (if any) additional prerequisites
remain.

### 3. Eventually decide "T6 close" in an administrative sense

**Dependencies:** The committed review doesn't settle this. The user
explicitly chose not to say "T6 is done" in the correction patch.

**What to read first:** `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md:39`
and `:52` (T6's done-when criteria).

**Approach:** The done-when was *"one consistent benchmark-first design."*
The committed review says the consolidation remains outstanding, routed
to T7 (wire formats) and T5 (agent_local docs). One interpretation: T6
cannot close until that consolidation lands. Another: T6 records the
boundary; consolidation is T7's problem; T6 is closable now. The user
will decide.

**Acceptance criteria:** Explicit T6 close-or-keep-open decision
recorded somewhere normative.

## In Progress

**Clean stopping point.** T6 review correction merged to main via PR #91
(merge commit `a3dc5cd3`). New branch `docs/t04-f6-f7-f11-ownership`
created from updated main, clean working tree, ready for F6/F7/F11 work.

No work in flight. This handoff is the transition document.

## Open Questions

1. **Who owns F6/F7/F11 remediation?** The committed T6 review explicitly
   says they "remain unassigned in current gate tables." This is the
   question the next branch exists to answer. Options: assign to T7
   (consumer-driven), assign to a new remediation packet (fresh ticket),
   or declare no current owner with trigger conditions.

2. **Does T6 close administratively or stay open?** The correction patch
   preserved the "DOES NOT YET COMPOSE" verdict without settling whether
   T6 itself is closable. User explicitly declined to say "T6 is done" in
   the correction. The decision is outstanding.

3. **When should T7 executable slice begin?** The committed review says
   T7 is "blocked on audit resolution." F6/F7/F11 assignment may or may
   not unblock it. Additional T7 prerequisites (not identified this
   session) may remain.

4. **Should the evidence-trajectory consumer projection be formally
   assigned to a gate?** The committed disposition says it "remains
   unassigned in current gate tables and needs either an explicit owner
   or an explicit declaration that no T4-T7 gate owns it." This is a
   micro-instance of Open Question 1.

5. **Does the F6/F7/F11 amendment benefit from user-drafted text or
   Claude-drafted text?** Pattern suggests user drafts substantive
   amendments. But this is an operational question about workflow
   division for the next session.

## Risks

1. **F6/F7/F11 may have different ownership answers.** Three findings
   about three different wire-format aspects. Assuming uniformity (all
   assigned to the same packet) may hide substantive differences.
   Mitigation: read each finding's audit file section independently
   before drafting assignments.

2. **The "no current owner" option may be unsatisfying.** Declaring
   gaps exist without assigning owners could feel like the same
   scope-displacement pattern the T6 correction fixed. Mitigation: if
   that option is chosen, pair it with explicit trigger conditions
   (when must assignment happen?).

3. **T7 may still be blocked after F6/F7/F11 assignment.** Even with
   ownership clarified, T7's wire formats may depend on additional
   prerequisites. Mitigation: verify T7 acceptance criteria as Next
   Step 2 before claiming F6/F7/F11 unblocks T7.

4. **The new branch's first commit is this handoff file.** That's
   unusual — most feature branches start with substantive work and
   add handoff commits later. If the F6/F7/F11 amendment turns out to
   be out of scope or the branch gets abandoned, the handoff commit
   becomes a minor orphan. Mitigation: if the branch is abandoned,
   move the handoff commit to main via cherry-pick or similar.

5. **Local main diverged from origin main invisibly.** This session
   surfaced the issue (6 commits ahead of origin); the PR brought them
   in sync. But the same pattern could recur if future sessions
   accumulate local main commits without pushing. Mitigation: periodic
   `git push origin main` or explicit sync before creating branches.

## References

| What | Where |
|---|---|
| T6 review doc (committed) | `docs/reviews/2026-04-04-t04-t6-benchmark-first-design-composition-review.md` |
| T6 correction commit | `09a7e767 docs(reviews): correct T6 ownership framing via adjudication correction` |
| Prior handoff (archived) | `docs/handoffs/archive/2026-04-05_04-14_t6-review-adjudication-correction-patch-and-scrutiny-findings.md` |
| PR #91 | https://github.com/jpsweeney97/claude-code-tool-dev/pull/91 |
| Merge commit | `a3dc5cd3 Merge pull request #91 from jpsweeney97/chore/track-t6-review` |
| Current branch | `docs/t04-f6-f7-f11-ownership` (at `a3dc5cd3`) |
| Finding 6 citation 1 | `benchmark-readiness.md:87` ("claim_id-keyed schema") |
| Finding 6 citation 2 | `provenance-and-audit.md:84-90` (Canonical Wire Format — dense array) |
| F6 audit location | `docs/audits/2026-04-02-t04-t4-evidence-provenance-rev17-team.md:141-148` |
| F7 audit location | Same file, `:152-164` |
| F11 audit location | Same file, `:216-228` |
| T4-BR gate tables | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/benchmark-readiness.md` |
| T6 done-when criteria | `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md:39,:52` |

## Gotchas

1. **`chore/track-t6-review` branch still exists on origin** post-merge.
   `gh pr merge --merge` doesn't delete the remote branch without
   `--delete-branch`. Cleanup can be deferred or handled via the
   `clean_gone` skill.

2. **Local main was 6 commits ahead of origin** before this session.
   The PR brought them in sync when it merged. Future sessions should
   be aware this divergence can happen and check for it before creating
   branches from local main.

3. **Handoff commit lands on the new F6/F7/F11 branch, not on main
   directly.** This is a side effect of the branch-protection +
   save-ordering constraint. The handoff will merge to main when the
   F6/F7/F11 work lands. Don't be surprised that `git log main` doesn't
   show the save commit until that merge.

4. **The "DOES NOT YET COMPOSE" header tension is kept by design.** User
   explicitly chose not to rewrite it. The rhetorical friction between
   "yet" (implying T6 will eventually compose) and the disposition
   ("T6 won't own the composition") is deliberate. Don't "fix" it
   without explicit user direction.

5. **`benchmark-readiness.md:87` vs `provenance-and-audit.md:84-90`
   shape language is genuinely in tension.** The former says "claim_id-keyed
   schema" (reads as map); the latter says "dense JSON array"
   (position = claim_id). The canonical form is the array. The
   informal phrasing at `:87` is the one that should eventually be
   tightened (maybe as part of F6/F7/F11 assignment or later).

6. **Repo merge strategy is merge-commit, not squash or rebase.**
   Verified via 5 recent merge commits. Don't offer squash/rebase when
   recommending merge strategy for this repo.

7. **`docs(handoff)` commits belong on main in this repo.** The user
   stated: *"This repo already accepts `docs(handoff)` history on `main`;
   the four handoff-lifecycle commits on this branch are consistent with
   existing project history, not noise that needs to be peeled off first."*
   Don't offer to peel off handoff commits in future PRs for this repo.

8. **User applies every flagged item regardless of severity.** Three
   sessions of 100% apply rate. Don't flag "optional" items unless you'd
   apply them yourself. Severity labels don't affect user decisions.

## Conversation Highlights

### User's Response Contract response to 6 scrutiny findings

Structured as What/Why/Verification/Remaining Risks. Key excerpts:

**Finding 1 softening:** *"Softened the F6/F7/F11 sentence so it no
longer invents remediation ownership; it now says those findings remain
unassigned in current gate tables while targeting gaps in the T4
provenance/state-model authority set."*

**Finding 3 bridge:** *"Added the missing bridge after the failure-path
paragraph so the reader is told, in prose, that `agent_local` documentation
is T5-owned while the consumer breakpoints are T7 work."*

**Finding 4 orphan surface:** *"Surfaced the orphaned evidence-trajectory
projection in the disposition instead of leaving it only in the ownership
table."*

**Finding 6 example:** *"Added the concrete `benchmark-readiness.md:87`
vs `provenance-and-audit.md:84-90` example so the ownership-vs-shape
principle is evidenced, not just asserted."*

**Scope discipline:** *"I kept the patch narrow: review-doc maintenance
only, no normative spec edits, no attempt to resolve the deliberate
'does not yet compose' rhetorical tension."*

### User's `:170` tightening and commit

**My observation framing:** *"If you want perfect consistency with the
softened F6/F7/F11 framing, `:170` still says 'routed to T4/T5/T7' which
could be read as asserting T4 ownership that the disposition explicitly
denies."*

**User's response:** *"Your optional `:170` note was worth taking. After
the F6/F7/F11 wording was softened to 'unassigned in current gate
tables,' the old table shorthand was the one remaining place that could
be read as reassigning those findings to T4."*

**User's final wording (better than my 3 options):** *"Ownership
correction below; see disposition for routed and unassigned surfaces."*

### User's landing strategy recommendation

**User framing:** *"The new information changes the count, not the
decision. The PR is larger than I stated because it is based on
`origin/main`, not local `main`, but the extra six commits are still the
same class of work this repo already carries on `main`: `docs(handoff)`
lifecycle history. That makes this a scope-expansion in volume, not in
kind."*

**User's correction to prior framing:** *"My only correction to the
prior recommendation is this: PR #91 is acceptable because the repo norm
appears to tolerate handoff-history commits on `main`, not because it is
a 'small' branch. It is not small. It is just consistent with the repo's
actual history."*

**User's execution sequence:** *"I would recommend the following
sequence: 1. merge PR #91, 2. Save a handoff, 3. start the F6/F7/F11
ownership-assignment work on a fresh branch from updated `main`."*

### Decision rule framing (user)

**User provided a reusable decision rule for PR #91:** *"Merge PR #91 if
the older six commits are intended to land at all. Only avoid PR #91 if
you now believe those older six commits should not reach `main` yet."*

This is a cleaner framing than my "accept as-is vs. peel off" dichotomy
— it reduces the decision to a single question about the older commits'
eventual destination.

## User Preferences

**Response Contract format for reporting:** User uses What/Why/Verification/Remaining
Risks structure from their global CLAUDE.md as their default for reporting
completed work. When they use it, they're signaling "apply verification
rigor to this report."

**Explicit recommendations with reasoning:** User delivers landing
decisions as "Recommendation/Why/Sequence" rather than asking "what do
you think?" The phrasing is imperative; my job is to execute or explain
why not.

**Treats scrutiny as actionable, 100% apply rate confirmed:** Across 3
sessions, every flagged item (including those I labeled "optional") has
been applied. This is now a workflow invariant for this user.

**Writes substantive content themselves:** User drafted all 7 fixes this
session (6 findings + `:170` tightening). My role: verify, scrutinize,
offer options, explain reasoning. Do not draft substantive content
unless explicitly asked.

**Prefers decisive, defensible decisions over hedging:** User said
*"Only avoid PR #91 if you now believe those older six commits should
not reach `main` yet"* — a clean bivalent framing rather than a multi-option
analysis.

**Verifies decisions empirically before committing:** Prior session used
`git branch --contains` to verify branch reasoning; this session read
and compared citations manually before committing. Don't take my
verification claims at face value — the user will re-check.

**Branch naming follows repo conventions:** User expects branch names
to match the semantic type of work (`docs/*` for spec work, `chore/*`
for housekeeping, `feature/*` for new functionality). Don't deviate
without reason.

**Commits via git directly, not asking Claude to commit:** User created
`09a7e767` themselves after I delivered verification. Pattern: I verify,
user commits. Don't auto-commit user-drafted work.

**Keeps correction scope narrow:** *"I kept the patch narrow: review-doc
maintenance only, no normative spec edits."* When fixing one thing, don't
expand to related things unless explicitly scoped.

**Closes sessions with explicit next-session or next-step direction:**
This session closed with a 3-step sequence (merge → save → new branch).
Prior session closed with "I will respond to your review in the next
session." Pattern: user states what they'll do next; the handoff should
preserve enough context for that declared next action.

**Welcomes hard feedback; applies corrections fast:** No softening needed
for scrutiny findings. User applied every finding within a single
response without objection.

## Rejected Approaches

### Squash merge for PR #91

**Approach:** Use `gh pr merge 91 --squash` to collapse 12 commits into
one on main.

**Why it seemed promising:** Cleaner history — single commit on main
representing the T6 review correction work. Easier to revert. Common
PR workflow in many repos.

**Why rejected:** Repo pattern is merge commits (verified via 5 recent
merges on `origin/main`). Squashing would lose the individual
`docs(handoff)` commits that this repo intentionally preserves as
session history. The user explicitly said handoff-lifecycle commits
belong on main in this repo.

**What I learned:** Don't impose generic best practices ("squash for
clean history") on a repo with an established different pattern. Check
recent merges before choosing strategy.

### Rebase merge for PR #91

**Approach:** Use `gh pr merge 91 --rebase` to replay commits linearly
on main without a merge commit.

**Why it seemed promising:** Linear history. No merge commit noise in
`git log`. Some repos prefer this.

**Why rejected:** Not the repo's pattern. Also obscures the feature-branch
boundary that merge commits preserve.

**What I learned:** Strategies that work well in isolation can conflict
with established repo patterns. Always check the pattern first.

### Peel off older 6 commits before PR #91

**Approach:** Close PR #91, push local main directly (bypassing PR
review for the older 6 commits), then re-open a smaller 6-commit PR
for just the T6 review tracking + correction.

**Why it seemed promising:** Cleaner scope separation — the PR would be
exactly the T6 review work, not mixed with earlier handoff commits.
"One PR, one purpose" discipline.

**Why rejected:** User explicitly stated the repo accepts handoff-history
commits on main, making the "peeling" unnecessary. Additionally, direct
push to main requires bypassing any PR-based branch protection, which
may not be available or advisable. The 12-commit PR is consistent with
the repo's actual history.

**What I learned:** Don't apply "clean PR scope" hygiene universally.
Some repos batch related work across commits intentionally. The
question isn't "is this PR clean?" but "does this PR match the repo's
established norms?"

### Save handoff on `chore/track-t6-review` before checkout

**Approach:** After merge, stay on `chore/track-t6-review` (now merged
but still checked out) and save the handoff there.

**Why it seemed promising:** Literal reading of user's sequence — save
is step 2, branch creation is step 3. Doing them in declared order
respects the user's plan.

**Why rejected:** Would commit the handoff to a merged branch, creating
a stranded commit that wouldn't reach main without another merge. The
handoff needs to be on a live branch (one that will eventually merge
to main) for long-term accessibility.

**What I learned:** When user's declared sequence conflicts with
technical constraints (branch protection, merged-branch state), adjust
the order but preserve the spirit. Explain the adjustment in chat
before executing so the user can correct if needed.
