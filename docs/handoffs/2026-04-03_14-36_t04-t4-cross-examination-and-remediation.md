---
date: 2026-04-03
time: "14:36"
created_at: "2026-04-03T18:36:43Z"
session_id: 23a753e9-13bc-43a1-8a93-f6e0951e5c17
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-03_14-08_t04-t4-spec-review-team-6-reviewer-41-findings.md
project: claude-code-tool-dev
branch: docs/t04-t4-scouting-and-evidence-provenance
commit: a6b63e76
title: T-04 T4 cross-examination verdict and remediation — 9 fixes, 2 P0s downgraded, report patched
type: handoff
files:
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/state-model.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/boundaries.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/containment.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/foundations.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/scouting-behavior.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/conformance-matrix.md
  - .review-workspace/synthesis/report.md
---

# Handoff: T-04 T4 cross-examination verdict and remediation — 9 fixes, 2 P0s downgraded, report patched

## Goal

Apply remediation to the modular T4 spec based on the user's adversarial
cross-examination of the spec-review-team findings from the prior session.

**Trigger:** The prior session ran a 6-reviewer spec-review-team producing 51
raw findings (41 canonical, 2 P0). The user stated they would "analyze the
full report, and share my thoughts in the next session." This session received
and executed that analysis.

**Stakes:** The T4 spec at
`docs/plans/t04-t4-scouting-position-and-evidence-provenance/` is the
canonical scouting and evidence provenance contract for the
dialogue-supersession benchmark. Defects in the spec propagate to T7
integration and scored benchmark runs. Equally important: overcorrecting based
on inflated review findings would introduce unnecessary complexity or concede
design positions the spec doesn't actually break.

**Success criteria:**
- Confirmed text-verifiable defects fixed
- Wording-precision issues tightened without overcorrecting
- Review artifact (report.md) patched to match actual findings
- No fixes applied for dismissed/deferred findings
- Branch ready to merge when user decides

**Connection to project arc:** T4 is one of seven benchmark-first design tracks
(T1-T7). The monolith reached "Defensible" at rev 21. Modularization was
completed two sessions ago. Review was run last session. This session closes
the review-remediation loop. Merge to main is the next step (user controls
timing).

## Session Narrative

### User arrives with complete cross-examination verdict

The session began by loading the prior handoff documenting the spec-review-team
run. The user then provided their analysis as a single structured document — a
complete adversarial cross-examination of the review findings. This was not a
request for investigation or explanation; it was a finished verdict with
specific rulings on each finding.

The verdict sorted the 41 canonical findings into three bins:

1. **Claims that hold up** (confirmed defects): SY-3, SY-1, SY-5, SY-8,
   SY-12, SY-4 — all text-verifiable schema/coherence issues.
2. **Claims that overreach or collapse under scrutiny**: SY-6 (former P0),
   SY-2 (former P0), CE-12, IE-4, IE-5/IE-6/IE-8, AA-5/CE-7/CE-10,
   VR-1/VR-2/VR-4/VR-11, IE-9 — findings that attacked a weaker reading
   of the spec than the strongest plausible interpretation, or that treated
   reviewer preferences as defects.
3. **Hidden assumptions and unfair framing**: The review assumed every MUST
   needs harness-side pre-execution enforcement, that absent restatement
   means absent actor, that the conformance matrix promises exhaustive
   coverage, and that weaker readings should be attacked over stronger ones.

The user's key analytical insight: the review's strongest findings were the
concrete, text-verifiable ones (missing Phase 2 logic, schema gaps, wrong
cross-ref). Its weakest were the enforcement-heavy conclusions, where reviewers
repeatedly treated "not stated in the reviewer's preferred operational form"
as "spec defect."

### Distilling into actionable categories

I organized the verdict into a structured remediation plan with three tiers:
confirmed defects (6), wording-precision items (3, former P0s downgraded), and
dismissed/deferred findings. The user was offered four options:

1. Implement confirmed fixes only
2. Confirmed fixes + wording-precision changes
3. Write a plan first
4. Something else

### User selects Option 2 with explicit guardrails

The user chose Option 2 — "but keep it narrow" — and provided specific
guardrails for each wording-precision fix:

- **SY-6 (CT-02):** "Mirror the harness-owned language already present in
  T4-CT-03. Do not rewrite it as if you discovered a proven P0 containment
  failure."
- **SY-2 (BD-01):** "Qualify boundaries.md so 'no new required artifacts' is
  scoped correctly. Do not frame it as resolving a true contradiction."
- **CE-12 (read_anchor):** "Clarify that read_anchor is a non-authoritative
  declared justification reviewed against query/output evidence. That is a
  compatibility clarification, not a conflict resolution."

The user also recommended patching the report: "If this review will be
circulated or used for prioritization, patch report.md too. Right now the
synthesis overclaims convergence and severity."

### First round: 9 spec fixes + report patch

All 9 spec fixes applied in parallel across 6 files (5 in state-model.md, 1
each in foundations, conformance-matrix, scouting-behavior, containment,
boundaries). The report received 8 targeted patches: correction note, P0/P1
counts, SY-6 and SY-2 entries rewritten, corroboration table fixed,
contradiction section corrected, enforcement section reframed, overall
assessment updated.

### User reviews and catches 3 precision issues

The user reviewed the diff and identified three remaining issues:

1. **BD-01 still had hostile-reading surface:** "No new required files beyond
   synthesis + transcript" could still be attacked from benchmark-readiness.md,
   which requires a persisted omission-audit artifact per scored run. Fix:
   scope to "agent-produced files" and explicitly mention T7 proof-surface
   exception.

2. **Report bookkeeping stale:** `contradictions_surfaced = 0` contradicted
   the newly admitted SY-2 disagreement, and SY-6/SY-2 were still labeled
   P0 in the remediation priority section.

3. **Conformance matrix item 19:** "worst-case, 3 cites avg" was improved
   but still soft — "3 cites avg" is not literal worst case given the cap
   of 5. Fix: "example scenario from T4-SM-08" is tighter.

### Second round: 4 precision fixes

Applied all four corrections. BD-01 now scoped to agent-produced files with
explicit T7 exception. Report metrics and remediation labels synchronized.
Conformance matrix phrasing tightened.

### Commit and approval

User approved the final diff (+33/-7 across 6 tracked files) and requested
the commit with a suggested title. Committed at `a6b63e76`.

## Decisions

### Remediation scope: confirmed defects + wording precision, defer everything else

**Choice:** Land the 6 confirmed text-verifiable defects and the 3
wording-precision changes (former P0s). Defer all enforcement-cluster findings,
matrix-exhaustiveness complaints, and "repeat every global blocker locally"
findings.

**Driver:** User's cross-examination verdict: "That gives you the best ratio
of correctness to churn: you fix the real defects, and you also remove the two
biggest sources of future misreadings without conceding the review's overstated
enforcement narrative."

**Rejected:**
- Option 1 (confirmed defects only) — rejected because it "leaves known
  ambiguity in places the review already overfit": containment.md, boundaries.md,
  and the read_anchor relationship. Quote: "Option 1 is defensible, but..."
- Option 3 (plan first) — rejected because "there are not many real design
  forks left. Most of the remaining disputed items are wording scope, not
  architecture."
- Enforcement cluster fixes — rejected because "the spec permits
  judgment-based and deferred enforcement" and the review "repeatedly treats
  'not stated in the reviewer's preferred operational form' as 'spec defect.'"

**Trade-offs:** SY-13 (EvidenceRecord.index construction rule) intentionally
left out of this pass. Some legitimate P1 hardening opportunities deferred.
The enforcement surface remains as-is by design, not by oversight.

**Confidence:** High (E2) — user's cross-examination is the authoritative
assessment, grounded in line-level spec citations.

**Reversibility:** High — future passes can address any remaining items.

**Change trigger:** If a dismissed finding proves to be a real contradiction
during implementation, revisit.

### SY-6 downgraded from P0 to wording precision

**Choice:** CT-02's Grep/Glob confinement description is imprecise wording,
not a containment failure. Mirror CT-03's harness-ownership language in CT-02.

**Driver:** User's cross-examination: "containment.md explicitly says
containment is a harness function applied before the agent sees output
(CT-03), and disposition is assessed from post-containment output. The review
proves wording asymmetry in the table, not the claimed failure mode."

**Rejected:**
- Original P0 assessment — the review posited two failure modes (agent bypass,
  undetectable provenance corruption) but could not cite spec text showing the
  agent receives pre-filter output. CT-03 explicitly denies this.
- Rewriting CT-02 as if a containment failure was proven — user guardrail:
  "Do not rewrite it as if you discovered a proven P0 containment failure."

**Trade-offs:** CT-02's table rows for Grep/Glob still don't say "checked
BEFORE execution" like Read does. The added preamble establishes harness
ownership for the entire section, which is sufficient.

**Confidence:** High (E2) — CT-03 text is unambiguous. The review's failure
mode claims are unsupported by spec text.

**Reversibility:** High — further tightening of CT-02 table language is
trivial if desired.

**Change trigger:** If CT-03's language is ever weakened or removed, CT-02
would need its own explicit harness-ownership statement.

### SY-2 downgraded from P0 to wording precision

**Choice:** BD-01 "No new required artifacts" is unqualified scope, not a
contradiction with BR-09. Qualify to "no new agent-produced files" with T7
exception.

**Driver:** User's cross-examination: "CC-3 explicitly says the claim is 'not
false' and likely just unqualified." The synthesis overclaimed triple
convergence when one reviewer substantively softened the finding.

**Rejected:**
- Original P0 "contradiction" framing — BD-01 refers to the artifact *set*
  (files), not content within them. Content additions are declared in BD-02.
  T7 proof-surface artifacts are T7 deliverables, not T4 outputs.
- First-round fix ("No new required files beyond synthesis + transcript") —
  user caught this still left a hostile-reading surface against BR-09 item 8.
  Tightened in second round to "No new agent-produced files" with explicit T7
  exception.

**Trade-offs:** The BD-01 cell is now longer than the original. Acceptable
because the longer text is defensible under hostile reading.

**Confidence:** High (E2) — scoping is factual (T4 produces synthesis +
transcript, T7 produces audit artifacts), and CC-3's softening is in the
findings file.

**Reversibility:** High — text edit.

**Change trigger:** If T4 ever produces a new output file (beyond synthesis +
transcript), BD-01 needs updating.

### CE-12 compatibility clarification

**Choice:** `read_anchor`'s non-authoritative status (SM-05) is compatible
with adjudicator audit use (PR-12). Added clarification paragraph to SM-05.

**Driver:** User's cross-examination: "SM-05 says read_anchor is not proof;
PR-12 says it records the claimed class and the adjudicator verifies misuse.
Those are compatible. A non-authoritative explanation can still be auditable
as a claim checked against stronger evidence."

**Rejected:**
- CE-12's original "normative conflict" framing — no spec text says
  read_anchor alone settles compliance, or forbids its audit use.
- Not addressing it — user included it in wording-precision scope because
  the review overfit on this area.

**Trade-offs:** Adds 7 lines to SM-05. The clarification is self-evident but
prevents future reviewers from repeating CE-12's misreading.

**Confidence:** High (E2) — the compatibility is logical (non-authoritative
evidence ≠ unauditable evidence), and both spec sections are explicit.

**Reversibility:** High — text addition.

**Change trigger:** If SM-05 or PR-12 change in ways that actually conflict.

### Patch the review report

**Choice:** Correct overclaimed convergence and severity in the gitignored
synthesis report at `.review-workspace/synthesis/report.md`.

**Driver:** User recommendation: "If this review will be circulated or used
for prioritization, patch report.md too. Right now the synthesis overclaims
convergence and severity, especially on SY-6 and SY-2. If you fix the spec
without correcting the review artifact, the record stays noisier than the
spec."

**Rejected:**
- Leaving report as-is — would be a misleading historical record.
- Full rewrite — disproportionate to the corrections needed.

**Trade-offs:** Report is gitignored, so patches are local-only. The original
findings files are untouched — the correction note at the top of the report
is transparent about what changed and why.

**Confidence:** High (E2) — the corrections are factual (CC-3's softening,
CT-03's explicit language).

**Reversibility:** High — gitignored file, can be reverted or deleted.

**Change trigger:** If the report is promoted to a tracked file, the
corrections travel with it.

## Changes

### `state-model.md` — 5 fixes (+26/-2)

The largest set of changes, all in T4-SM sections:

| Fix | Section | Change |
|-----|---------|--------|
| SY-3 | SM-02 Phase 2 | Added `not_scoutable` classification step. 6 lines: classification via SB-05 determines initial verification status before entry creation |
| SY-1 | SM-07 ProvenanceEntry | Added `type: "scouted"` and `type: "not_scoutable"` discriminator fields to the two variants |
| SY-5 | SM-04 ClaimRef | Added wire format declaration: dense array `[introduction_turn, claim_key, occurrence_index]` for serialization in `claim_provenance_index` |
| SY-8 | SM-06 Status Derivation | Fixed cross-ref: `T4-SB-02` (skip conditions) → `T4-SB-03` (target selection). The status derivation rule drives target selection priority, not the skip-condition table |
| CE-12 | SM-05 Audit Fields | Added 7-line compatibility clarification: `read_anchor` is non-authoritative as evidence but IS the auditable surface the adjudicator checks against. Explicitly states these roles are compatible |

### `boundaries.md` — BD-01 scope qualification (+1/-1)

Changed "No new required artifacts" → "No new agent-produced files. T7
proof-surface artifacts (T4-BR-09 item 8) are T7 deliverables, not T4 outputs.
Content additions within synthesis + transcript declared in T4-BD-02."

Two iterations:
1. First round: "No new required files beyond synthesis + transcript" — still
   attackable from BR-09 item 8.
2. Second round: scoped to "agent-produced files" and added T7 exception —
   closes hostile-reading surface.

### `containment.md` — CT-02 harness ownership (+4)

Added 3-line preamble to Pre-Execution Confinement section: "Confinement is a
harness function, consistent with T4-CT-03. The harness enforces these
constraints before tool execution; the agent receives only post-confinement
results."

Does NOT change the table entries or claim a containment failure was found.
Mirrors CT-03's explicit language.

### `foundations.md` — decision count (+1/-1)

SY-12: "Twelve" → "Thirteen" locked design decisions. T4-F-13 exists but
wasn't counted.

### `conformance-matrix.md` — item 19 + item 46 term consistency (+2/-2)

SY-4: Item 19 qualified from rule-like "6-turn tier 2, 8-turn tier 3" to
"example scenario from T4-SM-08" — the matrix is non-normative and should not
extend SM-08's worst-case accounting examples into rules.

SY-35: Item 46 term consistency — "scoutable/not-scoutable" → "scoutable/
`not_scoutable`" (backtick code format, underscore).

### `scouting-behavior.md` — term consistency (+1/-1)

SY-35: "not-scoutable" → "`not_scoutable`" in synthesis policy section
(line 312). Matches the status value used everywhere else.

### `.review-workspace/synthesis/report.md` — 8 report patches (gitignored)

Patched the synthesis report to match the cross-examination verdict:

| Patch | What changed |
|-------|-------------|
| Correction note | Added blockquote at top documenting the cross-examination and downgrades |
| Summary metrics | P0: 2 → 0 (downgraded), P1: 20 → 22 (includes former P0s) |
| Overall assessment | Removed enforcement-gap cluster from headline themes |
| SY-6 entry | Rewritten: P0 containment failure → P1 wording precision. Downgrade rationale added |
| SY-2 entry | Rewritten: P0 contradiction → P1 scope ambiguity. CC softening noted |
| Corroboration table | SY-2: "strongest signal" → "nature of defect disputed". SY-6: "two failure modes" → "wording asymmetry" |
| Contradiction section | "No contradictions" → "One substantive disagreement" (CC-3 vs AA-2) |
| contradictions_surfaced metric | 0 → 1 with annotation |
| Remediation priority | SY-6/SY-2 moved to new "Wording-precision fixes (former P0)" section |
| Enforcement section | "systemic pattern" → "hardening suggestions, not material defects" |

## Codebase Knowledge

### CT-02 / CT-03 containment relationship

`containment.md` has two sections that work together:

- **CT-02** (line 33): Describes per-tool confinement as a table. Originally
  lacked explicit actor for Grep/Glob. Now has a preamble establishing
  harness ownership.
- **CT-03** (line 74): The authoritative statement of the containment
  pipeline — explicitly says "Containment is a harness function applied
  before the agent sees the output" and describes the 5-step pipeline:
  pre-execution → post-execution filter → post-containment output enters
  transcript → agent assesses from post-containment → evidence references
  post-containment.

CT-03 is the stronger section. CT-02 is the implementation detail table.
The fix added CT-03's framing to CT-02 without duplicating CT-03's content.

### BD-01 scoping logic

`boundaries.md` T4-BD-01 "Explicit Non-Changes" table describes what T4
does NOT change at the *file level*:

- The benchmark artifact *set* (number/type of files) stays at synthesis +
  transcript. No new files are introduced.
- Content additions *within* those files are declared in BD-02 (claim
  ledger in synthesis, `claim_provenance_index` in pipeline-data).
- T7 proof-surface artifacts (BR-09 item 8) are T7 deliverables produced
  by the harness, not T4 agent outputs.

This three-part scoping closes the hostile-reading surface where a reviewer
could cite BR-09 item 8 against BD-01.

### read_anchor's dual role

`state-model.md` SM-05 "Audit Fields Are Non-Authoritative" (line 285) and
`provenance-and-audit.md` PR-12 "Read-Scope Rule" (line 339) describe
`read_anchor` from two compatible perspectives:

- **SM-05:** `read_anchor` is "not proof" and "not evidence" — it's a
  structured agent explanation that reduces audit burden but is not
  authoritative. The authoritative surfaces are queries, tool outputs,
  and the mechanical diff.
- **PR-12:** `read_anchor` records which justification class the agent
  claims. The adjudicator verifies: a 2000-line module read with
  `read_anchor: "whole_file"` is auditable misuse.

These are compatible: `read_anchor` is not evidence of justification, but
it IS the surface against which the adjudicator checks justification. The
added clarification paragraph in SM-05 makes this compatibility explicit.

### Phase 2 classification step

`state-model.md` SM-02 Phase 2 (line 113) originally described only merger
checks for `new` and `revised` claims. But `scouting-behavior.md` SB-05
(line 222) says "The classification decision is made during Phase 2
registration," and SM-06's lifecycle table has entries for both scoutable and
not-scoutable paths at registration.

The fix adds the classification step after merger resolution: claims that
don't merge undergo scoutable classification (SB-05 criteria) to determine
the initial verification status before entry creation.

### ProvenanceEntry type discriminator

`state-model.md` SM-07 (line 414) defined two ProvenanceEntry variants
distinguished by their fields (scouted has `record_indices`, not_scoutable
has `classification_trace`). But `provenance-and-audit.md` PR-03 (line 71)
shows the wire format with an explicit `type` field: `type: "scouted"` or
`type: "not_scoutable"`. PR-03 line 103 even says "The `type` field
distinguishes scouted from not_scoutable." The struct definitions needed to
match the wire format.

### ClaimRef serialization

`state-model.md` SM-04 (line 168) defined ClaimRef as a struct with three
named fields. `provenance-and-audit.md` PR-03 (line 70) shows it serialized
as a dense array: `[3, "compute_action behavior", 0]`. The wire format was
undeclared in SM-04.

## Context

### What this session represents

This was an **adversarial triage session** — the user cross-examined
automated review output, sorted findings by defensibility, and directed
surgical remediation. The session pattern is:

1. User provides complete verdict (not a request for analysis)
2. Claude distills into actionable categories
3. User selects scope and provides guardrails
4. Claude executes
5. User reviews and refines
6. Commit

This is the third session in the T4 modular spec sequence:
- Session 1: Compiled monolith into modular spec (59 IDs, 8 authorities)
- Session 2: Ran spec-review-team (6 reviewers, 51→41 findings)
- **Session 3 (this one):** Cross-examined and remediated

### Mental model

**Court ruling with damages assessment.** The review was the prosecution
(adversarial by design). The user's verdict is the court ruling (adversarial
cross-examination of the prosecution's case). The remediation is the awarded
damages (confirmed fixes). The key distinction: "confirmed defects" (the
prosecution proved its case) vs "reviewer preferences" (the prosecution
failed to prove inconsistency and instead attacked design choices).

The review's strongest findings were concrete and text-verifiable: missing
Phase 2 logic, schema mismatches, a wrong cross-reference. Its weakest were
the enforcement-heavy conclusions, where the review assumed a stronger
enforcement model than the spec intends. The spec permits judgment-based and
deferred enforcement — the review treated that design choice as a defect.

### What the cross-examination revealed about the review process

The spec-review-team skill produced high-quality concrete findings (SY-3,
SY-1, SY-5, SY-8, SY-12 all confirmed) but overcalibrated severity on
enforcement and convergence claims. Three patterns:

1. **Severity inflation:** SY-6 and SY-2 were called P0 based on
   constructions the spec text doesn't support. CT-03's explicit
   harness-ownership language was ignored when evaluating CT-02.

2. **Convergence overclaiming:** SY-2 was called "triple independent
   convergence" and "strongest signal in review" despite CC-3 explicitly
   softening to "not false, likely just unqualified." The synthesis
   resolved the disagreement by taking the highest severity rather than
   acknowledging the substantive split.

3. **Design-choice-as-defect:** The 9 integration-enforcement P1 findings
   largely attacked the spec's design choice to permit judgment-based and
   deferred enforcement, rather than proving contradictions. Quote from
   user's verdict: "The review assumes that every normative MUST needs
   harness-side, preferably pre-execution, enforcement. The spec itself
   repeatedly permits judgment-based and deferred enforcement."

### Project state

Branch `docs/t04-t4-scouting-and-evidence-provenance` has:
- Modular spec (committed at `86a81773`)
- Handoff archive commits
- **Remediation commit at `a6b63e76`** (this session)

No merge to main — user controls timing. The `.review-workspace/` directory
(gitignored) contains all review artifacts with report patches applied.

## Learnings

### Cross-examination catches severity inflation that synthesis doesn't

The spec-review-team's synthesis mechanically merged findings and took
highest severity, producing 2 P0s. The user's adversarial cross-examination
read each finding against the spec's strongest plausible interpretation and
downgraded both P0s. The synthesis process has no adversarial step — it
trusts reviewer severity assessments and resolves disagreements by escalating,
not by checking the underlying evidence.

**Key mechanism:** The synthesis merged CC-3's "not false, likely just
unqualified" with AA-2's "true contradiction" by taking AA-2's severity.
This overclaimed convergence. An adversarial step would have asked: "does the
spec text actually support a contradiction reading?"

**Implication:** Spec-review-team outputs should be treated as prosecution
arguments, not verdicts. Post-review cross-examination is valuable for any
spec where the review produces P0/P1 findings.

### Hostile-reading surfaces require multi-pass tightening

BD-01 required two rounds of tightening. The first round ("No new required
files beyond synthesis + transcript") closed the obvious gap but left a
subtler hostile-reading surface — BR-09 item 8 requires a T7-produced
proof-surface artifact, which could be attacked as a "new required artifact."
The second round scoped to "agent-produced files" and explicitly named the
T7 exception.

**Key mechanism:** Hostile readers attack scope gaps, not logical errors.
A statement that is technically true but unscoped (like "no new required
artifacts") invites the reader to find any artifact requirement anywhere
and declare a contradiction.

**Implication:** When fixing scope-related findings in specs with empty
precedence models, test each fix against the strongest hostile reading before
committing. One pass is often insufficient.

### Report artifacts should be patched alongside spec fixes

When the spec changes but the review artifact doesn't, the historical record
is self-contradictory: the report says P0, the spec shows the "P0" was a
3-line wording fix. User recommendation: "If you fix the spec without
correcting the review artifact, the record stays noisier than the spec."

**Key mechanism:** Review artifacts are point-in-time documents, but they
persist as reference material. If they overclaim, future readers (including
future reviewers) may inherit the inflated severity assessment.

**Implication:** When remediating review findings with severity downgrades,
patch the review artifact too. A correction note at the top is sufficient —
transparent about what changed and why, without pretending the original said
something different.

### Empty precedence catches contradictions but also catches false positives

The T4 spec's empty precedence model (`claim_precedence: {}`,
`fallback_authority_order: []`, `unresolved: ambiguity_finding`) successfully
surfaced the BD-01/BR-09 scope issue as an `ambiguity_finding`. But it also
made the review treat that scope issue as a "P0 contradiction" when it was
actually an unqualified statement that CC-3 correctly identified as "not
false." Empty precedence is a sensitive detector — it catches real
contradictions but also catches ambiguities that hostile readers
over-interpret.

## Next Steps

### 1. Merge `docs/t04-t4-scouting-and-evidence-provenance` to main

**Dependencies:** User approval. No technical blockers.

**What to read first:** This handoff's Changes section for the commit
history. The branch has 7 commits: modular spec compilation, handoff
archives, and the remediation commit.

**Approach:** Standard merge or PR from
`docs/t04-t4-scouting-and-evidence-provenance` → `main`. The spec lives
in its own directory — no conflicts expected.

**Acceptance criteria:** All 11 spec files present on main. `spec.yaml`
and all normative files intact.

**Potential obstacles:** None anticipated. Branch is clean, no conflicts
with main.

### 2. (Optional) Address SY-13: EvidenceRecord.index construction rule

**Dependencies:** None — can be done any time.

**What to read first:** `state-model.md` SM-05
(`EvidenceRecord.index` field at line 181), `provenance-and-audit.md`
PR-03 (`record_indices` usage).

**Approach:** Declare the construction rule for `EvidenceRecord.index` —
likely auto-increment from `len(evidence_log)` at creation time. This is
the remaining confirmed P1 that was intentionally kept out of this
remediation pass.

**Acceptance criteria:** SM-05's `index` field has a declared construction
rule that makes the `record_indices` join chain unambiguous.

### 3. (Optional) Cleanup `.review-workspace/`

**Dependencies:** Merge to main should happen first.

**Approach:** `trash .review-workspace/` — gitignored, local-only. The
patched report and all findings are there for reference but have no
persistent value after the spec is landed.

## In Progress

Clean stopping point. All 9 spec fixes and 8 report patches applied and
committed at `a6b63e76`. No work in flight. Branch ready to merge at user's
discretion.

## Open Questions

1. **When to merge to main?** User controls timing. No urgency. The branch
   has been open since the monolith compilation but no conflicts are expected
   (the spec lives in its own directory).

2. **Address SY-13 before or after merge?** The `EvidenceRecord.index`
   construction rule is the only remaining confirmed P1. Can be addressed
   as a separate commit before or after merge.

3. **Preserve or clean `.review-workspace/`?** The gitignored directory
   has all review artifacts including the patched report. Value diminishes
   after merge since the spec is the authoritative record.

## Risks

1. **`.review-workspace/` is gitignored.** All review artifacts (findings,
   ledger, patched report) live in the gitignored `.review-workspace/`
   directory. They are local to this working directory and will not survive
   `git clean -xfd`. If the review needs to be referenced after cleanup,
   the patched report should be copied somewhere persistent first.

2. **SY-13 remains open.** `EvidenceRecord.index` has no declared
   construction rule. The `record_indices` join chain in PR-03 assumes
   deterministic index values but SM-05 doesn't state how they're assigned.
   Low risk — the construction rule is almost certainly `len(evidence_log)`
   at creation time — but it's an undeclared invariant.

## References

| What | Where |
|------|-------|
| Remediation commit | `a6b63e76` on `docs/t04-t4-scouting-and-evidence-provenance` |
| Modular spec root | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/README.md` |
| spec.yaml | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/spec.yaml` |
| Patched report | `.review-workspace/synthesis/report.md` (gitignored) |
| Synthesis ledger | `.review-workspace/synthesis/ledger.md` (gitignored) |
| All findings | `.review-workspace/findings/*.md` (gitignored) |
| Prior handoff (archived) | `docs/handoffs/archive/2026-04-03_14-08_t04-t4-spec-review-team-6-reviewer-41-findings.md` |
| Spec-review-team skill | `packages/plugins/superspec/skills/spec-review-team/SKILL.md` |
| Shared contract | `packages/plugins/superspec/references/shared-contract.md` |

## Gotchas

1. **Report patches are local-only.** The `.review-workspace/synthesis/
   report.md` has 8 corrections applied, but it's gitignored. If the
   patched report needs to persist, copy it to a tracked location before
   cleaning up the workspace.

2. **BD-01 required two iterations.** The first-round fix closed the obvious
   gap but not the hostile-reading surface. When tightening scope statements
   in specs with empty precedence, test against the strongest hostile reading
   before committing — one pass may not be sufficient.

3. **Enforcement-cluster findings are deferred, not invalid.** The 9
   integration-enforcement P1 findings were assessed as hardening
   suggestions, not material defects. If a future implementation pass
   reveals that the enforcement surface genuinely needs actors and gate
   timing, these findings provide a reasonable starting list.

4. **CE-12 (late finding) was addressed.** The contracts-enforcement
   reviewer filed CE-12 after the synthesis was written. It was assessed as
   a compatibility clarification (not a contradiction) and addressed in the
   `read_anchor` clarification in SM-05. The original synthesis ledger and
   report do not include CE-12, but the patched report's correction note
   implicitly covers it.

## Conversation Highlights

**User arrived with a complete verdict, not a question.** The entire
cross-examination was delivered as a single structured document with specific
line references, severity rulings, and rewrite suggestions for each
finding. No investigation or analysis was requested — only execution.

**Guardrails were specific and framing-aware.** For each wording-precision
fix, the user stated both what to do AND what not to do:
- "Mirror the harness-owned language already present in T4-CT-03. Do not
  rewrite it as if you discovered a proven P0 containment failure."
- "Qualify boundaries.md so 'no new required artifacts' is scoped correctly.
  Do not frame it as resolving a true contradiction."
- "That is a compatibility clarification, not a conflict resolution."

**Review after first round was constructive.** User approved the state-model
fixes as "the strongest part of the remediation" and identified three
specific precision issues without requesting rework of approved changes.

**Commit message was user-suggested.** "Land it. A commit title like
`docs(t04): tighten T4 schema and wording clarifications` would fit the
patch."

## User Preferences

**Cross-examines automated output.** Does not trust review severity
assessments at face value. Reads every finding against the actual spec text
before acting. Sorts findings into confirmed/overreached/dismissed bins.

**Provides explicit fix guardrails.** For wording-precision changes, states
both what the fix should do AND what framing to avoid. The "do not" clauses
are as important as the "do" clauses.

**Reviews implementation output.** Checks the diff after fixes are applied
and catches precision issues (BD-01 hostile-reading surface, stale report
bookkeeping).

**Values defensibility under hostile reading.** The BD-01 tightening was
specifically about closing surfaces a hostile reader could attack, not about
logical correctness.

**Prefers surgical scope.** "Keep it narrow" — fix confirmed defects and
close misreading surfaces, but don't over-correct or concede the review's
enforcement narrative.

**Minimal interaction during execution.** Provided the verdict, selected
option, added guardrails, reviewed results, approved. No mid-execution
steering or course corrections.

**Controls merge timing.** "Do not merge docs/t04-t4-scouting-and-evidence-
provenance to main" (from prior session). This session didn't change that
stance — the branch stays open until the user decides.
