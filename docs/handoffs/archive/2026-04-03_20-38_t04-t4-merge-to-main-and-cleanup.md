---
date: 2026-04-03
time: "20:38"
created_at: "2026-04-04T00:38:38Z"
session_id: d701cdfd-a52a-4422-bb0e-6c5218dc9e2d
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-03_14-36_t04-t4-cross-examination-and-remediation.md
project: claude-code-tool-dev
branch: main
commit: 2a82edb6
title: T-04 T4 merge to main — SY-13 close-out, review rationale preserved, pushed to origin
type: handoff
files:
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/state-model.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/provenance-and-audit.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/conformance-matrix.md
  - docs/decisions/2026-04-03-t04-t4-review-remediation-scope.md
---

# Handoff: T-04 T4 merge to main — SY-13 close-out, review rationale preserved, pushed to origin

## Goal

Close out the T4 modular spec work: commit the final schema fix (SY-13),
merge the feature branch to main, preserve the review-calibration
rationale in durable form, clean up scratch artifacts, and push to
origin.

**Trigger:** The prior session landed 9 spec fixes and 8 report patches
at `a6b63e76`, leaving three items: merge to main, optional SY-13 fix,
and optional `.review-workspace/` cleanup. The user arrived having
already applied SY-13 independently and ready to close the branch.

**Stakes:** Low for this session specifically — the hard work (modular
compilation, review, cross-examination, remediation) was done in
sessions 1-3. This session is execution: commit, merge, preserve
rationale, push. The only judgment call was the form of the durable
record for the review-calibration narrative.

**Success criteria:**
- SY-13 committed and merged to main
- Feature branch deleted
- Review-calibration rationale preserved in a form that answers "why was
  the remediation this small?"
- `.review-workspace/` cleaned up
- `origin/main` updated

**Connection to project arc:** This is the fourth and final session in
the T4 modular spec sequence. T4 is one of seven benchmark-first design
tracks (T1-T7). The T4 spec is now landed on main and pushed to remote.

| Session | What happened |
|---------|--------------|
| Session 1 | Compiled T4 monolith into modular spec (59 IDs, 8 authorities, 11 files) |
| Session 2 | Ran spec-review-team (6 reviewers, 51 raw → 41 canonical findings, 2 P0) |
| Session 3 | Cross-examined findings, applied 9 fixes + 8 report patches |
| **Session 4 (this)** | SY-13 close-out, merge to main, rationale preserved, pushed |

## Session Narrative

### Resuming from the remediation handoff

Session began by loading the prior handoff documenting the
cross-examination and remediation work. The handoff described a clean
stopping point: 9 spec fixes committed at `a6b63e76`, branch ready to
merge at user's discretion, SY-13 (EvidenceRecord.index construction
rule) identified as the one remaining confirmed P1.

### User arrives with SY-13 already applied

The user had independently executed the SY-13 fix before this session —
a three-file patch across `state-model.md`, `provenance-and-audit.md`,
and `conformance-matrix.md`. They provided a structured change report
(What changed / Why / Verification / Remaining risks) and requested
review.

This is a continuation of the pattern from the prior session: the user
does the analytical and editorial work, then presents finished changes
for review rather than requesting investigation or implementation.

### Reviewing the SY-13 patch

I read all four change sites and the full `git diff`:

1. **state-model.md L223 (Key Fields):** Added `index` as first Key
   Fields entry. Defines construction rule: `len(evidence_log)`
   immediately before append, with invariant `evidence_log[i].index == i`.
   Links to `record_indices` and synthesis trajectory joins.

2. **state-model.md L383 (Lifecycle):** The "Evidence stored" and
   "`not_found` stored" rows now explicitly state
   `index = len(evidence_log)` (pre-append) instead of the former
   "Append index." The "(pre-append)" parenthetical correctly
   distinguishes from post-append length.

3. **provenance-and-audit.md L27 (PR-01):** Added sentence after
   existing PR-02 cross-reference: "Deterministic here means the
   T4-SM-05 invariant holds: for `evidence_log[i]`, `record.index == i`."
   Ties the "deterministic join" language to the now-declared invariant.

4. **conformance-matrix.md L29 (item 10):** Prepended
   `index == evidence_log position` to the existing checks. Makes the
   invariant explicitly verifiable.

Verified `index: int` exists in the EvidenceRecord struct definition at
L188. The invariant statement is identical across all three files. No
issues found — confirmed clean and commit-ready.

### Merge to main

User invoked `/merge-branch`. I committed SY-13 at `8b1c807f` with
message "docs(t04): declare EvidenceRecord.index construction rule
(SY-13)", then merged `docs/t04-t4-scouting-and-evidence-provenance` to
main at `2a82edb6` (merge commit, `ort` strategy, clean). The merge
brought 12,114 lines onto main — the entire T4 arc across 4 sessions.
Deleted the feature branch with `-d` (safe delete).

### User's final state assessment

The user verified the local state independently and provided a structured
assessment:

- `main` at merge commit `2a82edb6`, tracked worktree clean
- Only leftover: gitignored `.review-workspace/`
- Local `main` 49 commits ahead of `origin/main`

They then articulated the remaining decision: whether the
review-calibration narrative deserves a durable record.

### Preserving the review-calibration rationale

The user's recommendation: "My preference is the middle path: save the
rationale, not the scratchpad." They specifically rejected promoting
`.review-workspace/` wholesale into tracked history ("That directory is
doing the right job as scratch analysis") and framed the question as:
will future sessions need to answer "why was the remediation this small?"
or "why weren't the enforcement findings landed?"

I wrote a decision record at
`docs/decisions/2026-04-03-t04-t4-review-remediation-scope.md` covering
the P0 downgrades, enforcement cluster deferral, confirmed defect list,
and the calibration principle (automated review output = prosecution
arguments, not verdicts).

When committing, discovered `docs/decisions/` is gitignored (line 20 of
`.gitignore`). The existing 9 decision records in that directory are all
local-only artifacts. This is actually the correct tier: the decision
record serves as local working memory for future sessions, not shared
project history. The canonical outcome is in the merged commits; the
rationale is in the local decision record.

### Cleanup and push

Trashed `.review-workspace/` — gitignored scratch directory containing
all review artifacts (findings, ledger, patched report). Then pushed
`main` to origin at user's request: 49 commits from `5fea6a6d` to
`2a82edb6`.

## Decisions

### Preserve review rationale as local decision record, not tracked history

**Choice:** Write a concise decision record at
`docs/decisions/2026-04-03-t04-t4-review-remediation-scope.md` capturing
the P0 downgrades, enforcement cluster deferral logic, and calibration
principle. Do not promote `.review-workspace/` or raw review artifacts to
tracked history.

**Driver:** User's assessment: "My preference is the middle path: save
the rationale, not the scratchpad." The user identified the specific
future question this answers: "why was the remediation this small?" and
"why weren't the enforcement findings landed?"

**Rejected:**
- Promoting `.review-workspace/` wholesale — user: "That directory is
  doing the right job as scratch analysis." Raw findings, ledger, and
  patched report are process artifacts, not durable knowledge.
- Letting git history stand alone — user identified the gap: the merged
  commits capture the canonical outcome but not the reasoning for why
  the remediation was narrower than the review implied.
- Full handoff as the durable record — handoffs are session context, not
  permanent reference material. The decision record is more focused.

**Trade-offs:** The decision record is in gitignored `docs/decisions/`,
so it's local to this machine. If the reasoning needs to be shared with
others, it would need to be moved to a tracked location or communicated
separately. Accepted because the primary audience is future local
sessions.

**Confidence:** High (E2) — user stated the need explicitly, the form
matches the existing `docs/decisions/` pattern, and the content was
synthesized from the prior session's handoff.

**Reversibility:** High — text file, can be promoted to tracked history
if needed.

**Change trigger:** If someone outside this machine needs to understand
the remediation scope decision. At that point, move the file to a
tracked location or reference the prior handoff archive.

### Merge directly to main (no PR)

**Choice:** Merge `docs/t04-t4-scouting-and-evidence-provenance` to
main locally via fast merge, no pull request.

**Driver:** User invoked `/merge-branch` explicitly. The work is
docs-only, solo-authored, and already reviewed across 4 sessions
including a 6-reviewer automated review and adversarial cross-examination.

**Rejected:**
- PR workflow — unnecessary overhead for docs-only changes with no
  reviewers besides the user. The user controls merge timing and has been
  doing so across 4 sessions.

**Trade-offs:** No remote review record. Acceptable because the review
record exists in the archived handoffs and the local decision record.

**Confidence:** High (E2) — user explicitly chose this path.

**Reversibility:** Medium — merge is on main, revert would require a
new commit.

**Change trigger:** If the project adopts mandatory PR reviews for docs
changes.

## Changes

### SY-13: EvidenceRecord.index construction rule (commit `8b1c807f`)

Three-file patch, +9/-4 lines. Closes the last confirmed P1 from spec
review.

| File | Change |
|------|--------|
| `state-model.md` L223 (Key Fields) | Added `index` entry: `len(evidence_log)` pre-append, invariant `evidence_log[i].index == i` |
| `state-model.md` L383 (Lifecycle) | "Evidence stored" and "`not_found` stored" rows now state `index = len(evidence_log)` (pre-append) explicitly |
| `provenance-and-audit.md` L27 (PR-01) | Back-reference: "Deterministic here means the T4-SM-05 invariant holds" |
| `conformance-matrix.md` L29 (item 10) | Prepended `index == evidence_log position` to verifiable checks |

**Design pattern:** Same invariant declared at four sites, each serving
a different role: normative definition (Key Fields), operational
restatement (Lifecycle), consumer contract (PR-01), verifiable check
(conformance matrix). This is the spec's standard approach to
reinforcing invariants across surfaces without redundancy.

### Merge commit `2a82edb6`

Merged `docs/t04-t4-scouting-and-evidence-provenance` to main.
12,114 lines across 29 files. The merge brought the full T4 arc:
modular spec (11 files), handoff archives (13 files), design plan
(2 files), audit (1 file), ticket (1 file), risk register update (1 file).

### Decision record (local, gitignored)

`docs/decisions/2026-04-03-t04-t4-review-remediation-scope.md` — captures
P0 downgrades, enforcement cluster deferral, confirmed defect list, and
calibration principle. Not committed (gitignored directory).

### `.review-workspace/` cleanup

Trashed the gitignored scratch directory containing all review artifacts:
6 reviewer findings files, synthesis ledger, patched report. These were
point-in-time process artifacts; the spec is the authoritative record.

## Codebase Knowledge

### T4 spec is now on main

The complete T4 modular spec lives at
`docs/plans/t04-t4-scouting-position-and-evidence-provenance/` with
11 files:

| File | Authority | Role |
|------|-----------|------|
| `spec.yaml` | Manifest | Topology, build order, authority model |
| `README.md` | — | Human-readable overview |
| `state-model.md` | SM | Core data structures, lifecycle, status derivation |
| `scouting-behavior.md` | SB | Query protocol, classification, attempt limits |
| `provenance-and-audit.md` | PR | Evidence synthesis, trajectories, audit rules |
| `containment.md` | CT | Pre/post-execution confinement, pipeline |
| `foundations.md` | F | Locked design decisions (13 total) |
| `boundaries.md` | BD | Explicit non-changes, compatibility surface |
| `benchmark-readiness.md` | BR | Integration points with T1-T3, T5-T7 |
| `conformance-matrix.md` | — | Non-normative verifiable checklist (48 items) |
| `crosswalk.md` | — | Non-normative ID-to-section mapping |
| `rejected-alternatives.md` | — | Rejected design alternatives with reasoning |

### `docs/decisions/` is gitignored

Line 20 of `.gitignore`: `docs/decisions/`. All 10 decision records in
that directory (including the new one) are local-only artifacts. They
serve as working memory for future local sessions — durable enough to
survive across sessions, but not shared via remote.

Existing decision records:
- `2026-01-29-skill-template-structure.md`
- `2026-02-08-benchmark-v1-next-steps.md`
- `2026-02-08-orchestrator-reset-strategy.md`
- `2026-02-09-post-tier-a-next-steps.md`
- `2026-02-09-evaluate-making-recommendations-skill.md`
- `2026-02-11-multi-dialogue-synthesis-scope-preservation.md`
- `2026-03-06-ticket-plugin-priority-recalibration.md`
- `2026-03-27-advisory-coherence-after-promotion.md`
- `2026-04-03-conceptual-query-scope-constraint-for-benchmark-v1.md`
- `2026-04-03-t04-t4-review-remediation-scope.md` (new, this session)

### Review artifact lifecycle

The `.review-workspace/` directory (now trashed) held all spec-review-team
output: per-reviewer findings, synthesis ledger, and the patched report.
These were gitignored by design — scratch analysis that lives for the
duration of the review cycle, not beyond. The trashing closes that cycle.

The archived handoff at
`docs/handoffs/archive/2026-04-03_14-36_t04-t4-cross-examination-and-remediation.md`
contains the detailed narrative of what was in the review workspace and
how findings were triaged. That archive is the tracked record of the
review process.

## Context

### What this session represents

This was a **close-out session** — the final step in a four-session arc
that took the T4 scouting and evidence provenance spec from monolith
through modularization, automated review, adversarial cross-examination,
remediation, and landing on main. The session itself was lightweight:
review one patch, merge, preserve rationale, clean up, push.

### Mental model

**Closing a case file.** The T4 spec went through prosecution (automated
review), cross-examination (user's adversarial triage), sentencing
(remediation), and appeal (SY-13 follow-up). This session is the clerk
filing the verdict and archiving the case materials. The substantive
decisions were already made; this session executed the bookkeeping.

### Project state after this session

Branch `docs/t04-t4-scouting-and-evidence-provenance` no longer exists.
All T4 work is on `main` at `2a82edb6`, pushed to `origin/main`.

All confirmed review findings are landed:
- SY-1, SY-3, SY-4, SY-5, SY-8, SY-12, SY-35 (remediation commit
  `a6b63e76`)
- SY-13 (separate commit `8b1c807f`)
- SY-6, SY-2, CE-12 (wording-precision fixes in `a6b63e76`)

Deferred findings (enforcement cluster, 9 P1s) remain as hardening
suggestions. Decision record explains why.

## Learnings

### Three-site invariant declaration pattern in specs

When a spec has an invariant that multiple surfaces depend on, declaring
it at a single site is insufficient — consumers need their own
references to close the interpretation gap. The SY-13 fix used four
sites for the same invariant:

| Site | Role |
|------|------|
| SM-05 Key Fields | Normative definition (authority) |
| SM-05 Lifecycle | Operational restatement (how it happens) |
| PR-01 | Consumer back-reference (what "deterministic" means) |
| Conformance matrix item 10 | Verifiable check (how to test it) |

**Mechanism:** Each site serves a different reader: the definition tells
a spec reader what the invariant IS; the lifecycle tells an implementer
WHEN it's enforced; the back-reference tells a consumer WHY a join is
safe; the check tells a validator HOW to verify it. A single declaration
would leave three of these four audiences guessing.

**Implication:** When adding invariants to the T4 spec (or similar
multi-surface specs), check whether consumers, implementers, and
validators each have their own reference. A conformance matrix entry
without a normative backing is a claim without authority; a normative
rule without a conformance matrix entry is unverifiable.

### Gitignored `docs/decisions/` provides the right persistence tier for process rationale

Decision records in this repo are intentionally local-only. They sit
between ephemeral context (conversation, `.review-workspace/`) and
tracked history (git, handoff archives). This is the correct tier for
"why did we decide X?" artifacts that future local sessions need but
remote collaborators don't.

**Mechanism:** The question "why was the remediation this small?" can
arise in any future session touching the T4 spec. The git history shows
WHAT was changed; the archived handoff shows the full session narrative;
the decision record captures the REASONING in a compact, scannable form
(P0 downgrades, enforcement cluster deferral, calibration principle).

**Implication:** When a review process produces findings that are
partially accepted, write a decision record capturing the triage logic.
Don't rely on the archived handoff alone — handoffs capture the session
arc, but decision records answer specific "why" questions directly.

### User applies fixes independently between sessions

The user executed the SY-13 fix outside of a Claude session, then
presented the completed work for review with a structured change report
(What changed / Why / Verification / Remaining risks). This is consistent
with the pattern from the prior session where the user arrived with a
complete cross-examination verdict rather than requesting analysis.

**Implication:** When resuming from a handoff that identified next steps,
the user may have already completed some of them. Check the current
state before proposing work — the role may be reviewer, not implementer.

## Next Steps

### No immediate T4 follow-ups

The T4 spec is fully landed on main. All confirmed review findings
remediated. The enforcement-cluster findings (9 P1s) are deferred as
hardening suggestions — the decision record at
`docs/decisions/2026-04-03-t04-t4-review-remediation-scope.md` explains
why. These can be revisited during implementation if the enforcement
surface genuinely needs actors and gate timing.

### T7 integration is the next consumer

The T4 spec's primary integration points are with T7 (benchmark
readiness). `benchmark-readiness.md` (BR-01 through BR-09) defines
these touchpoints. T7 proof-surface artifacts reference T4 output
structures. When T7 work begins, read `benchmark-readiness.md` first.

### Potential future work

- **Enforcement hardening:** The 9 deferred P1 integration-enforcement
  findings provide a starting list if implementation reveals the
  enforcement surface needs explicit actors and gate timing. See the
  decision record for the triage logic.
- **Spec-review-team calibration:** The cross-examination revealed
  severity inflation patterns (P0s based on weaker-than-strongest
  readings, convergence overclaiming). Consider adding an adversarial
  step to the synthesis process. Documented in the prior handoff's
  Learnings section.

## In Progress

Clean stopping point. All T4 spec work landed on main at `2a82edb6` and
pushed to `origin/main`. Feature branch deleted. Review scratch workspace
trashed. Decision record written. No work in flight.

## Open Questions

No open questions for T4. The spec is landed and the review cycle is
closed. The only "open" items are the deferred enforcement-cluster
findings, which are explicitly deferred (not unresolved).

## Risks

1. **Decision record is local-only.** The review-calibration rationale
   at `docs/decisions/2026-04-03-t04-t4-review-remediation-scope.md` is
   in a gitignored directory. If this machine's local state is lost
   (fresh clone, disk failure), the detailed triage logic is lost with
   it. The archived handoff
   (`docs/handoffs/archive/2026-04-03_14-36_t04-t4-cross-examination-and-remediation.md`)
   captures the same information in more narrative form, so the risk is
   low — but the compact decision-record format would need to be
   recreated from the handoff.

2. **49 commits pushed in one batch.** Local main was 49 commits ahead
   of origin before push. All pushed at once. If any downstream CI or
   integration is sensitive to batch size, this could trigger unusual
   behavior. Low risk for a docs-heavy repo.

## References

| What | Where |
|------|-------|
| SY-13 commit | `8b1c807f` |
| Merge to main | `2a82edb6` |
| Remediation commit (prior session) | `a6b63e76` |
| T4 spec directory | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/` |
| Decision record (local) | `docs/decisions/2026-04-03-t04-t4-review-remediation-scope.md` |
| Prior handoff (archived) | `docs/handoffs/archive/2026-04-03_14-36_t04-t4-cross-examination-and-remediation.md` |
| Session 2 handoff (archived) | `docs/handoffs/archive/2026-04-03_14-08_t04-t4-spec-review-team-6-reviewer-41-findings.md` |
| Session 1 handoff (archived) | `docs/handoffs/archive/2026-04-03_13-36_t04-t4-modular-spec-compilation-and-topology-validation.md` |

## Gotchas

1. **`docs/decisions/` is gitignored.** Decision records don't get
   committed or pushed. This is intentional — they're local working
   memory. If you need to share a decision record, copy it to a tracked
   location first.

2. **`.review-workspace/` is gone.** The review scratch directory was
   trashed this session. If review artifacts are needed, the archived
   handoff at
   `docs/handoffs/archive/2026-04-03_14-36_t04-t4-cross-examination-and-remediation.md`
   contains the narrative account including all finding IDs, severity
   rulings, and fix descriptions.

3. **The T4 branch no longer exists.** Deleted after merge. All work is
   on main. Don't look for
   `docs/t04-t4-scouting-and-evidence-provenance` as a branch — it's
   a directory under `docs/plans/`.

## Conversation Highlights

**User arrived with SY-13 already done.** Provided a complete change
report with the four standard sections (What changed / Why / Verification
/ Remaining risks) rather than requesting implementation.

**Review was brief and positive.** No corrections needed on the SY-13
patch. The only observation was the insight about the four-role invariant
declaration pattern.

**User's final state assessment was structured and complete.** Verified
local state independently, identified the one remaining decision
(review-calibration preservation), provided three options with their
preference: "My preference is the middle path: save the rationale, not
the scratchpad."

**Merge and push were user-directed.** User invoked `/merge-branch`
explicitly and then requested push separately. No ambiguity about
timing or method.

## User Preferences

**Applies fixes independently.** The user executed SY-13 between sessions
and presented finished work for review. This is the second consecutive
session where the user arrived with completed analytical or editorial
work rather than requesting implementation.

**Provides structured change reports.** The SY-13 presentation followed
a four-section format: What changed, Why it changed, Verification
performed, Remaining risks. This format is concise and reviewer-friendly.

**Assesses state before requesting actions.** Before requesting merge,
push, or cleanup, the user verified local state independently and
provided a structured summary. They don't rely on Claude for state
assessment — they do it themselves and present the result.

**Articulates preservation decisions explicitly.** The user framed the
review-rationale question as a decision with options ("If you expect
future questions like X... If not...") and stated their preference with
reasoning: "save the rationale, not the scratchpad."

**Controls pacing.** Merge, push, and save were each triggered by
explicit user commands, not offered proactively. The user's message
"We should push this" came as a separate request after merge, not as
part of the merge flow.
