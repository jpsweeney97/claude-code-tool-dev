---
date: 2026-04-04
time: "00:49"
created_at: "2026-04-04T04:49:29Z"
session_id: b0e32c6a-c772-4453-aba5-063346f2c817
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-03_23-42_t4-reindexing-abandoned-reclassify-in-place.md
project: claude-code-tool-dev
branch: main
commit: 64cec979
title: T4 reclassification landed and Path-2 benchmark contract encoded
type: handoff
files:
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/README.md
  - docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md
  - docs/superpowers/specs/codex-collaboration/README.md
  - docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md
  - docs/plans/04-03-2026-reclassify-t4-in-place.md
  - docs/tickets/2026-04-03-t7-conceptual-query-corpus-design-constraint.md
---

# Handoff: T4 reclassification landed and Path-2 benchmark contract encoded

## Goal

Two closed units of work in one session:

1. **Complete T4 in-place reclassification.** Verify and commit the four prose
   edits that reclassify T4 as a normative peer spec at its reader entrypoints
   without moving files. This was the approved outcome of three rounds of
   adversarial review in the prior session.

2. **Encode the Path-2 corpus-design constraint in the benchmark contract.**
   Amend `dialogue-supersession-benchmark.md` to make the Path-2 decision
   normative: conceptual scored tasks must be single-root, deterministic
   cross-root, or executed through documented anchored decomposition. Resolve
   B8's compliance status explicitly. Close the T4 s4.6 blocker on scored
   benchmark runs.

**Trigger:** The prior session's handoff left four modified files (unstaged)
matching the approved reclassification plan, plus a recommendation to treat T6
and the broader T4-BR-07 obligations as separate follow-through. This session
executed both closable units.

**Stakes:** Medium. The reclassification was low-stakes housekeeping for a
closed spec. The Path-2 amendment is higher-stakes: it determines the scouting
scope rules for all scored benchmark runs and resolves whether B8 stays in the
scored corpus. Getting the amendment wrong would either block scored runs
unnecessarily (too strict) or permit non-comparable results (too loose).

**Connection to project arc:** T4 close-out (SY-13) -> reclassification ->
Path-2 encoding -> T6 composition check -> remaining T4-BR-07 prerequisites ->
scored benchmark runs. This session completed steps 2 and 3 in that sequence.

## Session Narrative

The session opened by loading the prior handoff (`2026-04-03_23-42_t4-
reindexing-abandoned-reclassify-in-place.md`), which documented the decision to
abandon physical T4 migration and reclassify in place. Four target files already
had unstaged modifications from the user's manual edits.

### Phase 1: Reclassification verification and commit

Read the approved plan (`docs/plans/04-03-2026-reclassify-t4-in-place.md`) and
all four diffs in parallel. Compared each diff against the plan's requirements
using a structured checklist.

Three files matched cleanly:

- T4 README: normative status declaration inserted after the Context block,
  before Authority Model — matching the handoff's placement clarification.
- Monolith shim: "canonical spec" strengthened to "canonical normative T4 spec"
  with historical-continuity rationale added.
- Codex-collaboration README: Related Specs section added after the
  reading-order table, pointing to T4 as the normative scouting/evidence
  contract.

One structural discrepancy found in the benchmark contract: the cross-spec
review rule had been added as **item 4 in the numbered list** rather than as
separate conditional prose after the list. This mattered because items 1-3 are
universal requirements for ANY benchmark change, while the T4 rule is
conditional — it applies only when changes affect scouting scope, evidence
provenance, or benchmark-readiness assumptions. Making it item 4 falsely implies
it applies to all changes.

The user fixed the numbering. Re-verification confirmed all four files matched
the plan. Committed at `e130b4db`, merged to main, pushed to origin.

### Phase 2: Path-2 benchmark contract amendment

The user then brought in analysis from archived Codex handoffs about T6 and T7.
The key source was `~/.codex/handoffs/claude-code-tool-dev/.archive/
2026-04-03_02-23_t4-rev21-defensible-g3-accepted-and-conceptual-query-
constraint.md`, which recorded:

- Decision 5 (line 448): Path-2 over Path-1/Path-3 for conceptual-query
  resolution
- Dependency graph (line 698): T7 must update the benchmark contract before
  scored runs
- Next steps 1-3 (line 980): T6 composition, Path-2 contract encoding, corpus
  design

Read the T7 ticket (`docs/tickets/2026-04-03-t7-conceptual-query-corpus-design-
constraint.md`), the benchmark contract's run conditions and corpus table, and
T4's scope_root derivation rules at `containment.md:47-76`.

**Key analysis: corpus compliance.** Assessed all 8 benchmark tasks against
T4-CT-02's three scope_root derivation cases:

- **B1-B3, B5-B7:** Path-targeted or cross-root deterministic. Compliant as
  written — prompts name or imply specific paths, evidence anchors determine
  roots.
- **B4:** Cross-root deterministic for scope_root purposes, but the "what is
  still missing" prompt is open-ended. Anchor set intentionally narrower than a
  full-repo installability audit. Flagged as compliant with a coverage caveat.
- **B8:** The only task requiring special treatment. Prompt is comparative
  across two entire subsystems ("Claude-side scouting" vs "context-injection")
  without path-anchoring one side. Proposed resolution: anchored decomposition
  across three workstreams rather than exclusion.

Created branch `chore/t7-path2-benchmark-contract`. User manually implemented
the amendment, then ran `/scrutinize` for adversarial review.

### Phase 3: Scrutiny review

The adversarial review found 7 issues:

1. **Critical — T4-BR-07 prerequisite status invisible.** The benchmark contract
   now looked complete (9 run conditions, corpus compliance, change control)
   without signaling that T4-BR-07 has six more prerequisites blocking scored
   runs. Someone reading the amended contract could conclude scored runs are
   ready when they are not.

2. **High — anchor elevation unacknowledged.** The Corpus Compliance section
   retroactively declared evidence anchors as "load-bearing scope constraints,
   not advisory reading suggestions" — a semantic elevation from the original
   column header intent. Without explicit justification, this reads as
   retrospective rationalization.

3. **High — B4 over-classified.** The compliance matrix said "Cross-root
   deterministic: Compliant as written" without flagging that B4's anchor set
   is narrower than the full answer space for an open-ended installability audit.

4. **Medium — B8 workstream boundary fuzzy.** "Stay anchored to one of those
   path groups" could be read as target constraint per tool call OR independent
   workstream isolation. Needed clarification.

5. **Medium — Change Control self-compliance.** The amendment adds scouting
   scope rules, which triggers the contract's own T4 cross-spec review
   requirement. The review wasn't documented.

6. **Low — T7 ticket status stale.** Acceptance criteria 1-3 satisfied but
   ticket still marked `open` without a delivery status split.

7. **Low — No forward guidance for future corpus rows.** Run condition 9
   applies to all scored tasks but Corpus Compliance only evaluates B1-B8.

User incorporated all 7 findings. Re-review elevated the verdict from "Minor
Revision" to "Defensible." User committed at `64cec979`, Claude merged to main
and pushed.

## Decisions

### Decision 1: Restructure cross-spec review rule as conditional prose

**Choice:** Move the T4 cross-spec review rule from item 4 in the numbered
Change Control list to separate conditional prose after the list.

**Driver:** Items 1-3 are universal (required for ANY benchmark change). The T4
rule is conditional (only when changes affect scouting scope, evidence
provenance, or benchmark-readiness assumptions). Mixing them in one list creates
a false equivalence — an editor seeing "4 things required for any change" would
either always do step 4 (waste) or learn to skip it (erosion of the rule).

**Alternatives considered:**
- **Keep as item 4** — simpler structure. Rejected because it conflates
  universal and conditional rules, misrepresenting the scope of the T4
  dependency.

**Trade-offs accepted:** The Change Control section now has two structural
elements (list + paragraph) instead of one. Minor complexity increase.

**Confidence:** High (E2) — derived from reading both the plan's intent and the
existing contract structure.

**Reversibility:** High — one-paragraph restructuring.

**What would change this decision:** If the T4 cross-spec dependency becomes
universal (applies to ALL benchmark changes, not just scouting-scope changes),
it should rejoin the numbered list.

### Decision 2: Add Scored-Run Prerequisite Status section

**Choice:** Add a normative section to the benchmark contract that explicitly
declares the contract is not ready for scored runs, lists what was delivered and
what remains open from T4-BR-07.

**Driver:** The scrutiny review's Critical finding: after the amendment, the
contract has 9 run conditions, a corpus compliance section, and change control
— it looks complete. Without an explicit prerequisite status, someone reading
the contract would conclude scored runs are ready when T4-BR-07 has 7 more
hard gates. The amendment creates a false readiness signal.

**Alternatives considered:**
- **Rely on T4-BR-07 in the T4 spec tree** — the prerequisite gate is already
  documented there. Rejected because the benchmark contract is the document
  people read before running. The gap must be visible in the contract itself,
  not only in T4.
- **Add a one-line note in Run Conditions** — simpler but insufficient. The
  gap is too important for an inline note. A named section makes it impossible
  to miss.

**Trade-offs accepted:** The contract now contains a section about its own
incompleteness, which is unusual for normative documents. This is intentional —
a contract that knows and declares its gaps prevents the most dangerous
misreading.

**Confidence:** High (E2) — the scrutiny review identified this gap, the
remediation was verified in re-review.

**Reversibility:** High — section can be removed when T4-BR-07 is fully
satisfied.

**What would change this decision:** When all T4-BR-07 prerequisites are
operational, the section should be replaced with a "Prerequisite Status: All
gates satisfied as of [date]" declaration.

### Decision 3: B8 stays in scored corpus via anchored decomposition

**Choice:** B8 remains in benchmark v1 scored corpus, but only through anchored
decomposition across three path groups. Not excluded, not deferred.

**Driver:** B8 is the highest-value benchmark task — it directly answers the
supersession question. Excluding it would leave the benchmark unable to answer
its own purpose statement. The Path-2 constraint eliminates the ambiguous
conceptual multi-root case; what remains is deterministic cross-root scouting
across three explicit path groups.

**Alternatives considered:**
- **Exclude B8 from scored runs** — eliminates all scope_root ambiguity.
  Rejected because the benchmark's purpose is to answer the supersession
  question, and B8 is the task that asks it.
- **Defer B8 classification** — wait for T6 to resolve. Rejected because B8's
  compliance status is a contract question, not a composition question. T6
  evaluates coverage adequacy; the contract must define compliance rules.
- **Free-form conceptual multi-root** — let B8 proceed without anchor
  constraints. Rejected because it violates T4-CT-02's blocker.

**Trade-offs accepted:** B8 scouting is constrained to three path groups, which
may miss evidence outside those surfaces. Both baseline and candidate face the
same constraint, preserving fairness, but the benchmark result may not capture
the full answer space for the supersession question.

**Confidence:** High (E2) — grounded in the T4 blocker text, the benchmark
contract's purpose statement, and the corpus table's evidence anchors.

**Reversibility:** Medium — changing B8's status would require a contract
revision under Change Control (items 1-3 plus T4 review).

**What would change this decision:** If T6 finds that the three path groups
don't provide adequate coverage for the supersession question, B8 may need
additional anchor groups or a different decomposition.

### Decision 4: Separate merge for T7 and T6

**Choice:** Merge the T7 Path-2 amendment to main immediately. Run T6 as a
separate effort from a fresh branch only if it produces repo changes.

**Driver:** User's explicit rationale: "This change is already a clean,
review-closed unit" and "Keeping the branch open for T6 would blur two
different things: a finished contract/ticket amendment and a separate
composition review."

**Alternatives considered:**
- **Keep branch open for T6** — rejected because it treats T6 as continuation
  of the same patch when it's a different checkpoint with different criteria.

**Trade-offs accepted:** T6 might identify issues that require amending the
contract again. A separate branch for those changes is more work than
continuing on the same branch.

**Confidence:** High (E1) — user's explicit scope decision.

**Reversibility:** High — can always create a new branch.

**What would change this decision:** Nothing — the merge is done. Future T6
findings would create new branches as needed.

## Changes

### `docs/plans/t04-t4-scouting-position-and-evidence-provenance/README.md`

**Purpose:** Add normative status declaration to the T4 spec's entry point.

**What changed:** Inserted a **Status** block after the Context section
(line 24), before Authority Model. States: "This README is supporting
documentation for the canonical normative T4 specification in this directory.
The T4 spec remains under `docs/plans/` for historical continuity and stable
references; that location is not a signal that the contract is planning scratch
or otherwise non-normative."

**Commit:** `e130b4db`

### `docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md`

**Purpose:** Strengthen the monolith shim's normative language.

**What changed:** "The canonical spec" -> "The canonical normative T4 spec"
with historical-continuity rationale. Added forward-looking edit guidance:
"Future normative edits should continue to land in that modular directory unless
a later tooling-backed relocation is explicitly approved."

**Commit:** `e130b4db`

### `docs/superpowers/specs/codex-collaboration/README.md`

**Purpose:** Add discoverability cross-reference from codex-collaboration to T4.

**What changed:** Added `## Related Specs` section after the reading-order
table, linking to T4 as "the canonical normative scouting and
evidence-provenance contract that the benchmark and related dialogue work depend
on."

**Commit:** `e130b4db`

### `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md`

**Purpose:** Two amendments across two commits.

**First commit (`e130b4db`):** Added cross-spec review rule in Change Control
section — separate conditional prose after the three-item universal list.
Changes affecting scouting scope, evidence provenance, or benchmark-readiness
assumptions must review T4 and T4-BR-09.

**Second commit (`64cec979`):** Path-2 encoding. Three new sections:
- **Corpus Compliance** (after Fixed Corpus table): Declares evidence anchors as
  load-bearing scope constraints with explicit comparability-over-breadth
  justification. Classifies B1-B7 as compliant, flags B4's anchor narrowing,
  defines B8's anchored decomposition across three path groups, requires future
  rows to be classified before scoring.
- **Run Condition 9** (in Run Conditions): Conceptual scored tasks must be
  single-root, cross-root, or decomposed from evidence anchors. Evidence
  anchors define benchmark-scoped `allowed_roots`.
- **Scored-Run Prerequisite Status** (new section after Run Conditions): Declares
  this amendment does not make scored runs ready. Lists what was delivered
  (allowed_roots, conceptual-query elimination) and what remains open (rest of
  T4-BR-07 items 1-8).

### `docs/plans/04-03-2026-reclassify-t4-in-place.md`

**Purpose:** Committed as the design record for the reclassification decision.

**State:** New file, 83 lines. The approved plan for four prose edits to four
files. Reviewed with "Defensible" verdict in the prior session.

**Note:** Filename uses MM-DD-YYYY convention rather than repo's YYYY-MM-DD
pattern. Cosmetic inconsistency flagged in prior session's review.

**Commit:** `e130b4db`

### `docs/tickets/2026-04-03-t7-conceptual-query-corpus-design-constraint.md`

**Purpose:** Record T7's Path-2 delivery and link to the benchmark contract.

**What changed:** Added four new sections:
- **Corpus Compliance Review:** Matrix classifying all 8 tasks against T4's
  scope_root derivation cases. B4 flagged for anchor narrowing. B8 flagged as
  "Compliant only via benchmark-contract decomposition."
- **B8 Resolution:** References the benchmark contract's Corpus Compliance
  section as authoritative. States B8 is Path-2 compliant by documented
  decomposition.
- **Change Control Review Note:** Documents the T4-BR-09/T4-BR-07 review.
  Lists what was delivered and what remains open.
- **Delivery Status:** Splits delivered work (Path-2 rule, corpus classification,
  B8 resolution) from remaining follow-through (T6 coverage review, broader
  T4-BR-07 prerequisites).

Ticket status left `open` because T6 composition check still needs to evaluate
coverage adequacy.

**Commit:** `64cec979`

### Trashed file

`docs/plans/2026-04-03-T4-peer-spec-reindexing.md` — the 552-line obsolete
migration plan from the prior session. Trashed before the reclassification
commit. Superseded by the in-place reclassification plan.

## Codebase Knowledge

### Benchmark Contract Structure (Post-Amendment)

`dialogue-supersession-benchmark.md` sections in document order:

| # | Section | Lines | Purpose |
|---|---------|-------|---------|
| 1 | Frontmatter | 1-6 | module, status: active, normative: true, authority: delivery |
| 2 | Purpose | 16-25 | One question: can codex-collaboration replace context-injection? |
| 3 | Scope | 27-43 | Dialogue evidence gathering and synthesis only |
| 4 | Systems Under Test | 45-53 | baseline (cross-model /dialogue) vs candidate (codex-collaboration) |
| 5 | Fixed Corpus | 55-69 | 8-task table with prompts and evidence anchors |
| 6 | **Corpus Compliance** | 71-102 | **NEW.** Anchor elevation, B1-B7 status, B8 decomposition |
| 7 | Known Limitation | 104-113 | Single-repo corpus |
| 8 | Run Conditions | 115-144 | Items 1-9 (item 9 is Path-2 constraint) |
| 9 | **Scored-Run Prerequisite Status** | 146-175 | **NEW.** T4-BR-07 gap disclosure |
| 10 | Required Benchmark Artifacts | 177-190 | manifest.json, runs.json, adjudication.json, summary.md |
| 11 | Adjudication Rules | 192-227 | Claim inventory, labels, safety findings |
| 12 | Metrics | 229-243 | supported_claim_rate, safety_pass, methodology_findings |
| 13 | Pass Rule | 245-258 | Four conditions, all must pass |
| 14 | Decision Consequences | 260-275 | What happens if candidate passes or fails |
| 15 | Change Control | 277-293 | Three universal rules + conditional T4 cross-spec review |

### T4-BR-07 Prerequisite Gate

Location: `benchmark-readiness.md:121-172`

Eight-item gate. ALL required for scored runs. The benchmark runner MUST reject
scored runs when any item is unavailable (enforcement at line 144-148).

| # | Category | Status After This Session |
|---|----------|--------------------------|
| 1 | Artifact: narrative-claim inventory | Open |
| 2 | Artifact: methodology-finding format | Open |
| 3 | Artifact: mode-mismatch schema | Open |
| 4 | Artifact: methodology_finding_threshold | Open |
| 5 | Comparability: scope formalization | **Partially addressed** — allowed_roots from anchors, conceptual-query elimination. Missing: scope_envelope, allowed_roots equivalence, source_classes |
| 6 | Comparability: evidence budget | Open |
| 7 | Comparability: artifact auditability | Open |
| 8 | Operational: transcript parser + omission proof | Open |

### T4 scope_root Derivation

Location: `containment.md:47-76`

| Case | Trigger | Deterministic? | Benchmark Status |
|------|---------|----------------|------------------|
| Path-targeted | Query names/implies a path | Yes — shallowest root | B1-B7 use this or cross-root |
| Cross-root | Query spans multiple roots | Yes — per-target root per tool call | B1-B7 and B8 (via decomposition) |
| Conceptual multi-root | No specific path, multiple roots | No — T4 defers to benchmark contract | Eliminated by Path-2 corpus constraint |

Anti-narrowing constraint (`containment.md:66-68`): agent MUST NOT select a
narrower root to exclude files that might contain contradictory evidence.

### B8 Anchored Decomposition

Three path groups defined in Corpus Compliance:

| Group | Surface | Paths |
|-------|---------|-------|
| 1 | Baseline dialogue | `packages/plugins/cross-model/skills/dialogue/SKILL.md`, `packages/plugins/cross-model/agents/`, `packages/plugins/cross-model/context-injection/` |
| 2 | Candidate spec | `docs/superpowers/specs/codex-collaboration/` |
| 3 | Candidate runtime | `packages/plugins/codex-collaboration/server/` |

Operational rule: the `path` parameter of each `Glob`/`Grep`/`Read` step must
target one of these groups. Cross-group reasoning is expected; cross-group
target expansion is not. The final synthesis integrates findings across groups.

### T7 Ticket State

Location: `docs/tickets/2026-04-03-t7-conceptual-query-corpus-design-constraint.md`

```yaml
status: open
blocks: [T6-composition-check]
```

Acceptance criteria status:
1. Benchmark contract run conditions include corpus design constraint -> **Done**
2. No scored task requires ambiguous conceptual multi-root selection -> **Done**
3. T4 s4.6 blocker satisfied -> **Done**
4. T6 composition check can evaluate coverage adequacy -> **Enabled but not run**

Ticket stays open until T6 records whether coverage remains adequate.

### Archived Codex Handoff References

| Archive | Key Content | Lines |
|---------|-------------|-------|
| `~/.codex/handoffs/claude-code-tool-dev/.archive/2026-04-03_02-23_t4-rev21-defensible-g3-accepted-and-conceptual-query-constraint.md` | Decision 5 (Path-2), dependency graph, next steps | 448, 698, 980 |
| `~/.codex/handoffs/claude-code-tool-dev/.archive/2026-04-01_23-38_t5-accepted-g4-closed-g3-next.md` | T6 definition | 1099 |

## Context

### Mental Model

This session completed two units in a pipeline where each step builds on the
previous: T4 close-out -> reclassification -> Path-2 encoding -> T6
composition -> remaining prerequisites -> scored runs.

The reclassification was a **discoverability problem** — the value was always
the cross-references, not the directory taxonomy. The Path-2 encoding was a
**comparability problem** — the value was making scored scouting deterministic,
not defining a general root-selection algorithm.

Both problems shared a pattern: the mechanically obvious solution (move files;
define a selection algorithm) was more expensive than the actual need required.
The prior session discovered this for the reclassification; the archived Codex
handoff discovered it for Path-2 (Decision 5: "corpus design constraints rather
than a general conceptual multi-root selection algorithm").

### Project State

All D-prime cross-model capability work (T1-T5) is verified end-to-end. T4 is
closed at SY-13. The benchmark contract now has the Path-2 corpus constraint but
is not ready for scored runs — T4-BR-07 items 1-4, 6-8, and part of item 5
remain open.

T6 composition check is unblocked. T7 ticket is open (Path-2 slice delivered,
T6 follow-through pending).

### Environment

Working in the `claude-code-tool-dev` monorepo on `main` at `64cec979`.
Origin is up to date.

## Learnings

### Anchor elevation requires explicit justification

**Mechanism:** Repurposing a corpus table column ("Primary evidence anchors") as
formal T4 `allowed_roots` changes its semantic role from evaluator guidance to
scouting constraint. Without explicit documentation, the reinterpretation reads
as retrospective rationalization.

**Evidence:** The scrutiny review (finding #2, High) caught this. The fix was
adding "This is a deliberate comparability-over-breadth trade" to the Corpus
Compliance section.

**Implication:** Any future schema reuse across contract boundaries should
document the semantic change at the point of use, not assume readers will
track the original column intent.

**Watch for:** Future corpus rows where the evidence anchors are designed as
evaluator guidance but would be treated as allowed_roots under run condition 9.

### Contract self-honesty prevents false readiness signals

**Mechanism:** A normative contract section that declares its own incompleteness
("Scored-Run Prerequisite Status") prevents the most dangerous misreading:
"all the sections are here, so we're ready to run."

**Evidence:** The scrutiny review's Critical finding: after the amendment, the
contract had 9 run conditions, corpus compliance, and change control — it
looked complete. Without the prerequisite status section, a reader would
reasonably conclude scored runs are ready.

**Implication:** For any normative document that is built incrementally across
multiple sessions, include a gap-declaration section that maps delivered vs.
remaining obligations. Remove it only when all obligations are met.

**Watch for:** The Scored-Run Prerequisite Status section becoming stale as
other T4-BR-07 items are addressed. Update it as each item is completed.

### Scrutiny review as a quality gate catches material gaps

**Mechanism:** The `/scrutinize` adversarial review found 7 issues (1 Critical,
2 High) that the original amendment draft missed. The Critical finding (T4-BR-07
invisibility) would have created a false readiness signal in production.

**Evidence:** Full round-trip: draft -> scrutiny (7 findings) -> revision ->
re-review (all addressed, verdict: Defensible). One cycle, no rework.

**Implication:** For normative contract amendments, running `/scrutinize` before
committing catches structural gaps that are invisible from the authoring
perspective. The author sees what they built; the reviewer sees what's missing.

**Watch for:** Scrutiny fatigue — if every change gets a 7-finding review, the
process may feel heavy. The T4 reclassification (4 prose edits) didn't need
scrutiny; the Path-2 amendment (new contract sections) did. Calibrate to
stakes and complexity.

## Conversation Highlights

**The numbering fix:** Claude identified that the cross-spec review rule in the
benchmark contract was structurally wrong as item 4 in the numbered list.
User agreed and restructured it as conditional prose. The semantic distinction
(universal vs. conditional rules) mattered more than the visual simplicity of
a single numbered list.

**Pivoting from reclassification to T7:** After merging the reclassification,
the user brought in a detailed analysis of archived Codex handoffs, identifying
T6/T7 as still-open follow-through. The transition was the user's initiative —
they had already done the handoff archaeology and formed a recommendation
before involving Claude.

**Scrutiny review adoption:** The user ran `/scrutinize` on their own draft
after completing the amendment. They incorporated all 7 findings and
re-submitted for re-review. The round-trip worked as designed: the adversarial
frame caught structural gaps (especially the T4-BR-07 invisibility) that
self-review would miss.

**Scope discipline on T6:** When Claude asked "Merge to main, or keep this
branch open for the T6 composition check?", the user explicitly separated the
two: "This change is already a clean, review-closed unit... Keeping the branch
open for T6 would blur two different things: a finished contract/ticket
amendment and a separate composition review that may or may not produce new
doc changes."

## Next Steps

### 1. Run T6 composition check

**Dependencies:** All five hard gates are at `Accepted (design)`. Path-2 corpus
constraint is now encoded. T7 ticket is open and blocking T6.

**What to read first:**
- `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md:31-37`
  (hard-gate state) and `:77-82` (design acceptance checklist)
- `docs/tickets/2026-04-03-t7-conceptual-query-corpus-design-constraint.md:59-97`
  (corpus compliance matrix and B8 resolution)
- The benchmark contract's Corpus Compliance section

**Approach:** Treat T6 as a narrow composition/coverage test, not a reopening of
T4 hostile review. Answer three questions:
1. Do the accepted gates (T1-T5) still compose into one coherent state model
   and synthesis contract now that Path-2 constrains the corpus?
2. Does benchmark v1 still have adequate task coverage after the Path-2
   constraint applies?
3. Are there gaps between what T4 requires and what the benchmark contract
   now says?

**Acceptance criteria:** T6 can name whether benchmark-v1 coverage remains
adequate, any affected tasks are identified, and no one reopens T4 merely
because T7 benchmark work is still pending.

**If T6 produces repo changes:** Create a fresh branch (e.g.,
`chore/t6-composition-check`). If T6 is analysis-only, no branch needed.

### 2. Address remaining T4-BR-07 prerequisites (future sessions)

**Dependencies:** T6 should complete first for coverage adequacy.

**What to read first:**
- `benchmark-readiness.md:121-172` (the 8-item gate)
- The Scored-Run Prerequisite Status section in the benchmark contract

**Scope:** Items 1-4 (artifact completeness), item 5 remainder (scope_envelope,
allowed_roots equivalence, source_classes), items 6-8 (evidence budget,
artifact auditability, omission-audit proof). Each is a separate unit of work.

### 3. Update T7 ticket when T6 completes

**Dependencies:** T6 outcome.

**What to do:** If T6 confirms adequate coverage, close the T7 ticket and update
its delivery status. If T6 finds coverage gaps, the ticket may need additional
work items or the benchmark contract may need further amendment.

## In Progress

Clean stopping point. Both units of work (reclassification and Path-2
amendment) are committed, merged, and pushed. No work is in flight.

**State:** `main` at `64cec979`, origin up to date. Working tree clean.

## Open Questions

1. **T6 scope and format:** Should T6 produce a formal report document, or is a
   ticket update sufficient? The archived handoff says "treat T6 as a
   coverage/composition test" but doesn't prescribe the output format.

2. **T4-BR-07 work decomposition:** The eight prerequisite items span artifact
   schemas, scope formalization, evidence budgets, and operational tooling.
   Should they be tackled as one work stream or decomposed into independent
   tickets?

## Risks

1. **False readiness despite gap declaration.** The Scored-Run Prerequisite
   Status section exists, but readers who skim the contract may still miss it.
   Risk is mitigated by the section's prominent placement (between Run
   Conditions and Required Benchmark Artifacts) but not eliminated.

2. **B4 anchor narrowing.** B4's evidence anchors are narrower than the full
   answer space for "what is still missing to make installable." Both systems
   face the same constraint, so fairness is preserved, but B4's benchmark
   result may not capture real-world capability. If B4 results look anomalous,
   anchor adequacy should be the first hypothesis.

3. **B8 decomposition adequacy.** The three path groups were derived from the
   corpus table's evidence anchors, not from an independent analysis of what a
   full supersession comparison needs. If the groups miss important surfaces
   (e.g., cross-model hooks, MCP server dispatch), the scored B8 result may
   be incomplete. T6 should evaluate this.

4. **Scored-Run Prerequisite Status staleness.** The section lists what's open
   as of this session. As T4-BR-07 items are addressed in future sessions, the
   section must be updated. If it falls out of date, it becomes misleading in
   the opposite direction (suggesting more work remains than actually does).

## References

| What | Where |
|------|-------|
| T4 reclassification plan (approved) | `docs/plans/04-03-2026-reclassify-t4-in-place.md` |
| T4 modular spec root | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/README.md` |
| T4 spec.yaml | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/spec.yaml` |
| T4 containment (scope_root rules) | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/containment.md` |
| T4 benchmark-readiness | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/benchmark-readiness.md` |
| Monolith shim | `docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` |
| Benchmark contract | `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md` |
| Codex-collaboration README | `docs/superpowers/specs/codex-collaboration/README.md` |
| T7 ticket | `docs/tickets/2026-04-03-t7-conceptual-query-corpus-design-constraint.md` |
| Risk register | `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md` |
| Codex handoff (Path-2 decision) | `~/.codex/handoffs/claude-code-tool-dev/.archive/2026-04-03_02-23_t4-rev21-defensible-g3-accepted-and-conceptual-query-constraint.md` |
| Codex handoff (T6 definition) | `~/.codex/handoffs/claude-code-tool-dev/.archive/2026-04-01_23-38_t5-accepted-g4-closed-g3-next.md` |
| Prior session handoff | `docs/handoffs/archive/2026-04-03_23-42_t4-reindexing-abandoned-reclassify-in-place.md` |
| Shared contract (spec.yaml schema) | `packages/plugins/superspec/references/shared-contract.md` |
| spec-review-team skill | `packages/plugins/superspec/skills/spec-review-team/SKILL.md` |

## Gotchas

1. **T4-BR-07 vs T4-BR-09:** These are related but distinct. T4-BR-09
   (line 196) defines 10 amendment rows — T7's obligations to the benchmark
   contract. T4-BR-07 (line 121) defines 8 prerequisites — hard gates that must
   be operational before scored runs. The amendment addresses T4-BR-09 row 5
   partially and T4-BR-07 item 5 partially. They reference each other but have
   different completeness criteria.

2. **"Primary evidence anchors" are now `allowed_roots`:** The Corpus
   Compliance section retroactively elevates the corpus table column to a
   formal T4 scouting constraint. This semantic change is documented in the
   contract ("deliberate comparability-over-breadth trade") but the column
   header in the Fixed Corpus table was not changed. A reader seeing "Primary
   evidence anchors" may not realize these are hard scouting boundaries.

3. **Reclassification plan filename:** `04-03-2026-reclassify-t4-in-place.md`
   uses MM-DD-YYYY instead of the repo's YYYY-MM-DD pattern. Committed as-is
   since it was already reviewed under that name. Cosmetic only.

4. **ADR is local-only:** The conceptual-query scope constraint ADR at
   `docs/decisions/2026-04-03-conceptual-query-scope-constraint-for-benchmark-
   v1.md` is gitignored (`.gitignore:20`). The T7 ticket is the tracked
   version-controlled artifact. Future sessions should not assume the ADR is in
   git history.

5. **Two handoff archives cite T4 files:** Both repo-local
   (`docs/handoffs/archive/`) and Codex-local
   (`~/.codex/handoffs/claude-code-tool-dev/.archive/`) archives contain
   line-range citations to T4 spec files. This is the same gotcha from the
   prior session and remains relevant — any future T4 file modifications must
   audit both surfaces.

## User Preferences

**Works in closed units.** User explicitly said T7 and T6 are different units
that shouldn't share a branch: "Keeping the branch open for T6 would blur two
different things: a finished contract/ticket amendment and a separate
composition review."

**Writes substantive amendments themselves.** For both the reclassification and
the Path-2 amendment, the user authored the doc changes manually. Claude's role
was analysis, corpus assessment, verification, and adversarial review — not
authoring the contract text.

**Values adversarial review before committing.** Invoked `/scrutinize` on their
own draft before committing. Incorporated all findings and re-submitted for
re-review.

**Prefers honest tradeoff documentation.** User's own benchmark contract
revision included the Scored-Run Prerequisite Status section (responding to the
scrutiny review's Critical finding) and the B4 anchor-narrowing caveat.
Prefers contracts that acknowledge gaps over contracts that appear complete.

**Scope discipline.** Continued the prior session's "core surfaces only"
approach. Did not expand into broader docs sweeps, T4-BR-07 work, or T6.

**Provides structured analysis before engaging Claude.** For both the
reclassification review and the T7 analysis, the user arrived with pre-formed
analysis (prior adversarial reviews, archived handoff archaeology) and engaged
Claude for verification and review, not exploration.
