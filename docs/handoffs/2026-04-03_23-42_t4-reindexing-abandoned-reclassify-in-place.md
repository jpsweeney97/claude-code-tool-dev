---
date: 2026-04-03
time: "23:42"
created_at: "2026-04-04T03:42:14Z"
session_id: b05cf5b6-416f-4a67-97cf-0ce7bfa19840
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-03_20-38_t04-t4-merge-to-main-and-cleanup.md
project: claude-code-tool-dev
branch: chore/t4-reindexing-plan-revision
commit: 13696552
title: T4 reindexing abandoned — reclassify in place instead
type: handoff
files:
  - docs/plans/2026-04-03-T4-peer-spec-reindexing.md
  - docs/plans/04-03-2026-reclassify-t4-in-place.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/README.md
  - docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md
  - docs/superpowers/specs/codex-collaboration/README.md
  - docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md
  - packages/plugins/superspec/skills/spec-review-team/SKILL.md
  - packages/plugins/superspec/references/shared-contract.md
---

# Handoff: T4 reindexing abandoned — reclassify in place instead

## Goal

Determine how to handle the T4 modular spec tree at
`docs/plans/t04-t4-scouting-position-and-evidence-provenance/`, which had outgrown
its `docs/plans/` home. The tree has its own README, `spec.yaml`, 7-authority model,
59 stable requirement IDs, a crosswalk, and a conformance matrix — it is a normative
peer spec, not planning scratch.

**Trigger:** The T4 close-out session (SY-13, session 4 of 4) landed the final
commit (`8b1c807f`) and merged to main. With T4 complete, the classification mismatch
between its normative status and its `docs/plans/` location became a housekeeping
question.

**Stakes:** Low — T4 is closed with no planned active development. The question is
taxonomic correctness vs. stability. Getting this wrong doesn't break anything
immediately; it either creates unnecessary migration risk (moving) or leaves a
classification blemish (staying).

**Outcome:** After three rounds of adversarial plan review, the session concluded that
physical relocation creates more risk than benefit for a closed spec. The approved
approach is in-place reclassification: add cross-references and normative declarations
at the four reader entrypoints that matter, without moving any files.

**Connection to project arc:** T4 is part of the T-04 track (scouting position and
evidence provenance) within the D-prime cross-model capability work. The benchmark
contract in codex-collaboration (`dialogue-supersession-benchmark.md`) is the primary
consumer of T4's readiness gates and amendment obligations.

## Session Narrative

The session opened by loading the T4 close-out handoff from the previous session.
The context summary established that a reindexing plan had already been drafted in a
prior conversation and partially reviewed, with the user having decided on peer
placement at `docs/superpowers/specs/scouting-position-and-evidence-provenance/`
instead of child placement under codex-collaboration.

The user provided the first adversarial review of the peer-spec reindexing plan
(`docs/plans/2026-04-03-T4-peer-spec-reindexing.md`), with 9 findings across
Critical/High/Medium severity. The two critical findings were:

1. **Breadcrumb shims claim archival continuity they don't deliver.** The plan
   replaced old modular files with 5-line redirect stubs, but archived Codex handoffs
   cite those files by exact line range (e.g., `state-model.md:225-228`). A stub file
   destroys that reference surface.

2. **Keeping old `spec.yaml` alongside stub markdown creates a fake spec root.**
   `spec-review-team` enters full-contract mode on any directory containing
   `spec.yaml` (confirmed at `SKILL.md:87`). Reviewing a directory of stubs against
   a real authority model produces nonsense.

These findings led to the first major revision: replacing the shim model with a
**frozen archive** model where old files stay byte-for-byte identical, and
`spec.yaml` is removed to prevent tooling confusion.

The user then provided the second adversarial review. Its central finding was an
**unresolved architectural contradiction**: the plan simultaneously claimed "full
historical preservation" and "tooling demotion via spec.yaml removal," but:
- Archived handoffs cite `spec.yaml` itself by line range (`spec.yaml:1-52` at
  `2026-04-03_13-33_t4-modular-spec-review-and-integrity-closure.md:269`), so
  deleting it breaks historical references.
- Removing `spec.yaml` doesn't actually prevent tooling discovery —
  `spec-review-team` enters degraded mode on frontmatter-bearing markdown even
  without a manifest (`SKILL.md:100`).

This led to the second revision: keep `spec.yaml` frozen too (zero deletions, zero
modifications, only add `FROZEN.md`), and be honest about the tradeoff in a new
"Known Tradeoffs" section.

The pivotal moment came after the second revision. The user stepped back entirely
and asked the question the planning work had been avoiding: **"Should we even move
the T4 spec at all?"** The user's analysis:

- The upside is classification hygiene and future discoverability — real but modest.
- The downside is operational: duplicate spec roots, split-brain maintenance, ongoing
  confusion about which copy is canonical.
- T4 is closed (SY-13). No active development friction from the wrong directory.
- The mandatory cross-references — the actual high-value deliverable — are achievable
  without moving any files.
- Quote: "the permanent split-brain avoidance is" the hard part, not the migration
  mechanics.

This reframed the entire problem. The value was always the cross-references, not the
directory taxonomy. The physical move was the most expensive possible way to deliver
them.

The user then drafted a minimal in-place reclassification plan
(`docs/plans/04-03-2026-reclassify-t4-in-place.md`): four prose edits to four files,
no path changes, no tooling changes, no migration. Claude reviewed it and gave a
"Defensible" verdict with two minor clarifications (README insertion point ambiguity,
`normative: false` frontmatter distinction).

At this point, the working tree shows the user has already started executing the
in-place reclassification: all four target files are modified (unstaged).

## Decisions

### Decision 1: Abandon physical migration, reclassify in place

**Choice:** Do not move T4 spec files. Keep all existing paths intact. Add
cross-references and normative declarations at the four reader entrypoints.

**Driver:** Three rounds of adversarial review demonstrated that every migration
approach creates durable ambiguity:
- Shims break line-level references (Round 1, Critical)
- spec.yaml deletion breaks line-range citations AND doesn't achieve tooling demotion
  (Round 2, Critical)
- Frozen archive with spec.yaml kept works mechanically but creates permanent
  duplicate spec root with no tooling to distinguish frozen from canonical (Round 2,
  accepted tradeoff)

User's synthesis: "the permanent split-brain avoidance is" the hard part. "Tidy is
not enough reason to accept durable ambiguity."

**Alternatives considered:**
- **Child-spec under codex-collaboration/** — rejected in prior session because
  superspec shared contract has no parent-child `spec.yaml` mechanism
  (`shared-contract.md:7-10`). Would break `spec-review-team` authority validation.
- **Peer-spec with breadcrumb shims** — rejected because archived Codex handoffs
  cite old files by exact line range. Stubs destroy that surface while claiming
  to preserve it.
- **Peer-spec with frozen archive, spec.yaml removed** — rejected because (a)
  `spec.yaml:1-52` is cited by line range in archived handoffs, and (b) removing
  spec.yaml doesn't prevent tooling discovery (degraded mode at `SKILL.md:100`).
- **Peer-spec with frozen archive, spec.yaml kept** — technically viable but creates
  permanent duplicate spec root with no mechanism to distinguish frozen from
  canonical. Accepted tradeoff was tolerable but the benefit didn't justify it.

**Trade-offs accepted:** T4 remains under `docs/plans/` despite being a normative
spec. Future readers browsing `docs/superpowers/specs/` won't find it there. The
cross-references from codex-collaboration mitigate this at the actual reader
entrypoints.

**Confidence:** High (E2) — three independent adversarial review rounds all converged
on the same signal: migration mechanics are more costly than the classification
problem they fix.

**Reversibility:** High — the migration plan exists at
`docs/plans/2026-04-03-T4-peer-spec-reindexing.md` if conditions change. The
in-place reclassification doesn't block future relocation.

**What would change this decision:**
- T4 becomes actively developed again and the `docs/plans/` location causes repeated
  mistakes.
- Tooling support for frozen spec roots is added (e.g., `frozen: true` in spec.yaml
  schema).
- `docs/superpowers/specs/` becomes machine-meaningful (auto-discovery, indexing),
  not just aesthetically organized.

### Decision 2: Core surfaces only — four files

**Choice:** Reclassification touches exactly four files: T4 README, monolith shim,
codex-collaboration README, and dialogue-supersession-benchmark.md.

**Driver:** User's explicit instruction: "Core surfaces only." Global docs index or
broader discoverability sweep would be over-engineering for a closed spec.

**Alternatives considered:**
- **Add docs-level index** — rejected as inventing new infrastructure for a closed
  spec, same over-engineering trap the migration fell into.
- **Broader docs sweep** — rejected for the same reason.

**Trade-offs accepted:** No global discoverability improvement beyond the
codex-collaboration reader path.

**Confidence:** High (E1) — user's explicit scope decision.

**Reversibility:** High — can always add more surfaces later.

**What would change this decision:** If there are other active reader entrypoints
into T4 that the session didn't identify.

### Decision 3: Mandatory benchmark backlink in Change Control section

**Choice:** Place the cross-spec review rule in `dialogue-supersession-benchmark.md`'s
Change Control section (after the existing three-item amendment list at L207), not as
optional README-only prose.

**Driver:** The benchmark file is the actual normative consumer surface. Its Change
Control section is where future editors look before making amendments. A cross-spec
dependency placed there is load-bearing; placed only in the README, it's decorative.

**Alternatives considered:**
- **README-only mention** — rejected because README is non-normative (`normative:
  false` in frontmatter). A non-normative cross-reference for a normative dependency
  is structurally wrong.
- **Optional "also add to benchmark"** — rejected after Round 1 review finding 4
  identified it as the highest-risk discoverability gap.

**Trade-offs accepted:** Adds a fourth rule to a three-item Change Control list.
Future benchmark editors have one more constraint to honor. This is intentional —
the dependency already exists; the plan makes it explicit.

**Confidence:** High (E2) — confirmed by reading both the benchmark contract and the
codex-collaboration README, verified by two review rounds.

**Reversibility:** High — one line removal.

**What would change this decision:** If `spec-review-team` gains cross-spec
dependency tracking, the prose rule could become redundant (but harmless to keep).

## Changes

### `docs/plans/2026-04-03-T4-peer-spec-reindexing.md` — Obsolete migration plan

**Purpose:** Three revisions of a physical migration plan for moving T4 from
`docs/plans/` to `docs/superpowers/specs/scouting-position-and-evidence-provenance/`.

**State:** Untracked, never committed. Superseded by the in-place reclassification
plan. Contains 552 lines of detailed migration mechanics including link rewrite
rules, verification scripts, and execution phases. Retains value as documentation of
why the migration was rejected — each revision addresses specific adversarial
findings.

**Future-Claude note:** This file can be deleted or kept as historical context. It
was never part of the committed plan surface.

### `docs/plans/04-03-2026-reclassify-t4-in-place.md` — Approved in-place plan

**Purpose:** The approved reclassification plan. Four prose edits to four files, no
path changes.

**State:** Untracked, 83 lines. Reviewed with "Defensible" verdict. Two minor
clarifications recommended:
1. Specify README edit placement: after the Context block (line 24), before
   Authority Model (line 26).
2. Note that `normative: false` in frontmatter describes the README file itself,
   not the spec tree — so writing "normative peer specification" in README body
   prose is consistent.

**Future-Claude note:** Filename uses MM-DD-YYYY convention
(`04-03-2026-reclassify-t4-in-place.md`) rather than the repo's YYYY-MM-DD pattern.
Cosmetic inconsistency flagged in review.

### Working tree modifications (4 files modified, unstaged)

The user appears to have started executing the in-place reclassification plan after
the review. The following files show unstaged modifications:

- `docs/plans/t04-t4-scouting-position-and-evidence-provenance/README.md`
- `docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md`
- `docs/superpowers/specs/codex-collaboration/README.md`
- `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md`

These are exactly the four target files from the reclassification plan.

## Codebase Knowledge

### T4 Modular Spec Tree

**Location:** `docs/plans/t04-t4-scouting-position-and-evidence-provenance/`

**Structure (12 files):**

| File | Authority | Normative | Purpose |
|------|-----------|-----------|---------|
| README.md | supporting | no | Entry point, authority model, reading order |
| spec.yaml | — | — | Machine manifest: 7 authorities, boundary rules |
| foundations.md | foundation | yes | Core decisions T4-F-01–T4-F-13 |
| state-model.md | state-model | yes | Occurrence registry, ClaimRef, evidence record |
| scouting-behavior.md | scouting-behavior | yes | Per-turn loop, targeting, classification |
| containment.md | containment | yes | Scope breach, scope_root derivation |
| provenance-and-audit.md | provenance | yes | Evidence trajectory, audit chain |
| benchmark-readiness.md | benchmark-readiness | yes | Prerequisite gates, amendment table |
| boundaries.md | boundaries | yes | Non-changes, migration |
| rejected-alternatives.md | supporting | no | 61 rejected alternatives |
| conformance-matrix.md | supporting | no | 70-item verification matrix |
| crosswalk.md | supporting | no | Monolith section→modular ID mapping |

**Key patterns:**
- Requirement IDs: `T4-{prefix}-{seq}` (e.g., `T4-SM-01`). Stable across
  reorganization. Each normative clause carries its ID as a heading anchor.
- Cross-file links use ID-based anchors: `[T4-CT-03](containment.md#t4-ct-03)`
- Authority model has NO precedence hierarchy — normative conflicts resolve to
  `ambiguity_finding` (not "foundation beats behavior")
- Boundary rules trigger cross-authority review: e.g., changes to `state-model`
  require reviewing `scouting-behavior`, `provenance`, and `benchmark-readiness`

### spec-review-team Tooling Behavior

**Key discovery for this session:**

| spec.yaml present? | Frontmatter present? | Behavior |
|---------------------|----------------------|----------|
| Yes | Yes | Full-contract mode — authority validation, claims, precedence |
| Yes | No | Full-contract mode with degraded files |
| No | Yes | **Degraded mode** — still reviews, uses heuristic clusters |
| No | No | Degraded mode with path heuristics only |

**Critical implication:** Removing `spec.yaml` does NOT make a directory invisible to
spec-review-team. It changes the MODE of review (full-contract → degraded), not
whether review happens. This was the key finding that killed the spec.yaml-removal
approach.

Source: `packages/plugins/superspec/skills/spec-review-team/SKILL.md:85-102`

### Shared Contract

`spec.yaml` is machine truth. README summarizes it. Contradictions between them are
defects (`shared-contract.md:9-11`). No parent-child spec.yaml mechanism exists — one
manifest per directory (`shared-contract.md:7`).

### Codex-Collaboration README Structure

**Location:** `docs/superpowers/specs/codex-collaboration/README.md`

Sections in order: Frontmatter → Title → Description → Relationship to Official
Plugin → Authority Model → Reading Order → Cross-Reference Conventions (line 54-58,
currently the last section).

Natural insertion point for "Related Specs": after Cross-Reference Conventions.

### Benchmark Contract Change Control

**Location:** `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md:200-207`

Current content:
```
## Change Control

The benchmark corpus, adjudication labels, metrics, and pass rule are fixed for
this contract version. Any future change to them requires:

1. editing this contract,
2. explaining why the previous contract was insufficient, and
3. rerunning any comparison that relied on the changed rule.
```

The cross-spec review rule goes after item 3. It is a complementary rule (about when
changes to this contract must also review another contract), not a fourth numbered
item in the existing list.

### Historical Reference Surface

Archived Codex handoffs cite T4 files by exact line range at their current paths:

| Citation | Handoff |
|----------|---------|
| `state-model.md:225-228` | `~/.codex/handoffs/.../2026-04-03_20-38_t4-sy-13-closeout-...md:1074` |
| `state-model.md:383-384` | Same handoff, line 1076 |
| `provenance-and-audit.md:27-32` | Same handoff, line 1078 |
| `spec.yaml:1-52` | `~/.codex/handoffs/.../2026-04-03_13-33_t4-modular-spec-review-...md:269` |
| `spec.yaml` (as reference) | `docs/handoffs/archive/2026-04-03_13-36_...md:519` |
| `spec.yaml` (as reference) | `docs/handoffs/archive/2026-04-03_14-08_...md:530` |

This is why any migration that deletes, stubs, or modifies files at the old path
breaks the historical surface. The in-place approach avoids this entirely.

### Pre-Existing Broken Anchors

Three anchors on the monolith shim are broken (since original modularization, not
caused by any current work):

| Broken anchor | Crosswalk target |
|---------------|------------------|
| `#scope_root-derivation` | `containment.md#t4-ct-02` |
| `#benchmark-contract-amendment-dependencies` | `benchmark-readiness.md#t4-br-09` |
| `#benchmark-execution-prerequisites-comprehensive` | `benchmark-readiness.md#t4-br-07` |

Referenced from:
`docs/decisions/2026-04-03-conceptual-query-scope-constraint-for-benchmark-v1.md`
(gitignored). The reclassification plan explicitly defers this fix as a separate
concern.

## Context

### Mental Model

This is a **cost-benefit analysis problem, not a classification problem.** The
original framing ("T4 is in the wrong directory") led to treating it as a taxonomy
fix requiring a physical move. Three rounds of adversarial review reframed it: the
cost of moving exceeds the benefit for a closed spec.

Core insight: the mandatory cross-references were always the value. The physical
move was just the most expensive possible way to deliver them. Once this was clear,
the right approach fell out naturally: add the cross-references where they matter (the
benchmark contract's Change Control section, the codex-collaboration README), declare
T4's normative status in its own README, and stop.

### Project State

T4 is complete. The D-prime cross-model capability work (T1-T4 + fixes) is verified
end-to-end. SY-13 close-out committed at `8b1c807f`. No planned T4 modifications.

Branch `chore/t4-reindexing-plan-revision` was created for the migration plan work.
With the migration abandoned, this branch now holds:
- Two untracked plan files (migration plan and reclassification plan)
- Four modified files (the in-place reclassification edits, apparently already
  started by the user)

### Environment

Working in the `claude-code-tool-dev` monorepo. The superspec plugin
(`packages/plugins/superspec/`) provides `spec-review-team` and `spec-writer` skills.
The shared contract at `packages/plugins/superspec/references/shared-contract.md` is
authoritative for `spec.yaml` schema.

Codex handoffs live at both:
- `docs/handoffs/archive/` (repo-local, tracked)
- `~/.codex/handoffs/claude-code-tool-dev/.archive/` (Codex-local, external)

Both surfaces cite T4 files by exact path and line range.

## Learnings

### Migration cost scales with reference ecosystem, not file count

**Mechanism:** Moving 12 files should be trivial. But T4 has an unusually dense
historical reference ecosystem: archived handoffs, audits, and reviews cite files by
exact line range. Any migration that changes file content at the old path — whether by
replacing with stubs, adding frontmatter fields, or deleting files — breaks those
references.

**Evidence:** `state-model.md:225-228` cited in Codex handoff at
`~/.codex/handoffs/.../2026-04-03_20-38_...md:1074`. `spec.yaml:1-52` cited at
`~/.codex/handoffs/.../2026-04-03_13-33_...md:269`.

**Implication:** Before proposing any future file move in this repo, audit the
reference ecosystem first. The question isn't "how many files" but "who cites these
files and how precisely."

**Watch for:** Any spec that goes through multiple review rounds accumulates this
kind of dense reference surface. T4 had 6 hostile review rounds, 4 development
sessions, and a conformance matrix — more reference points than most specs.

### spec.yaml presence is a binary tooling trigger, not just metadata

**Mechanism:** `spec-review-team` checks for `spec.yaml` at `SKILL.md:85-87`. If
present: full-contract mode (authority validation, claims, precedence). If absent:
degraded mode. There is no "frozen" or "archived" state.

**Evidence:** `SKILL.md:87` ("If present: parse authority registry") and `SKILL.md:100`
("If spec.yaml is absent AND zero files have parseable frontmatter, classify all
files by path heuristics").

**Implication:** Leaving `spec.yaml` at a deprecated path is equivalent to leaving a
loaded trigger in a decommissioned system. But removing it doesn't actually
decommission the directory — degraded mode still processes it.

**Watch for:** Future `spec.yaml` schema extensions should consider a `frozen: true`
field. This was identified as out of scope for the current work but is the proper
tooling fix for the frozen-archive pattern.

### Adversarial review naturally converges on "should we do this at all?"

**Mechanism:** Iterative adversarial review of a plan will eventually find the plan's
structural contradictions. If the structural contradictions are inherent to the
approach (not fixable by mechanical revision), the correct response is to question
the approach itself, not to add more patches.

**Evidence:** Round 1 found 9 mechanical issues. Round 2 found the architectural
contradiction (preservation vs. demotion). The user then asked "should we even move
it?" — the question that three rounds of plan revision had been implicitly circling.

**Implication:** When adversarial review keeps finding new categories of problems
after each fix, stop patching and re-evaluate the premise. "Is this the right
approach?" is a higher-value question than "how do we fix this approach?"

## Conversation Highlights

**The pivotal question (user, after Round 2):**
"We should step back and ask the important question that has been ignored so far:
Should we even move the T4 spec at all? Does the benefit outweigh the risk?"

This was the turning point. Three rounds of plan review had been improving the
migration mechanics without questioning whether the migration itself was the right
choice.

**User's cost-benefit framing:**
"the permanent split-brain avoidance is" the hard part, not the migration mechanics.
"Tidy is not enough reason to accept durable ambiguity."

**Scope decision:**
Claude asked "How minimal should the reclassification plan stay?" with four options.
User responded: "Core surfaces only." This set the scope for the approved plan.

**Review approach:** User provided detailed adversarial reviews with:
- Exact line references to the plan and source files
- Severity ratings (Critical/High/Medium)
- "Stronger change" prescriptions for each finding
- "What Must Change Before This Plan Is Trustworthy" bottom-line sections
- "Bottom-Line Verdict" synthesis

## Rejected Approaches

### Physical migration: Child-spec under codex-collaboration/

**Approach:** Place T4 as a subdirectory within
`docs/superpowers/specs/codex-collaboration/`.

**Why it seemed promising:** T4's benchmark-readiness module directly constrains
codex-collaboration's benchmark contract, suggesting a containment relationship.

**Specific failure:** The superspec shared contract defines `spec.yaml` as one
manifest per directory with no parent-child mechanism (`shared-contract.md:7`).
Placing T4's `spec.yaml` inside `codex-collaboration/` would cause `spec-review-team`
to either crash on authority validation or miscategorize every T4 file.

**What it taught:** The relationship is cross-reference, not containment. T4 has 7
independent authorities; codex-collaboration has 8. They share zero authority labels.

### Physical migration: Peer-spec with breadcrumb shims

**Approach:** Move files to `docs/superpowers/specs/scouting-position-and-evidence-
provenance/`, replace old files with 5-line redirect stubs.

**Why it seemed promising:** Clean conceptual model — old paths become thin pointers,
new path is canonical.

**Specific failure:** Archived Codex handoffs cite old files by exact line range
(e.g., `state-model.md:225-228`). A 5-line stub at that path operationally destroys
the historical reference while claiming to preserve it. Additionally, keeping
`spec.yaml` alongside stubs creates a fake spec root that `spec-review-team` would
try to review in full-contract mode.

**What it taught:** "Old pathname still opens" is not the same as "historical
references still resolve." Line-level compatibility requires content preservation,
not just path preservation.

### Physical migration: Frozen archive, spec.yaml removed

**Approach:** Keep all old markdown files byte-for-byte identical, but remove
`spec.yaml` to prevent `spec-review-team` from entering full-contract mode.

**Why it seemed promising:** Preserves line-level content for historical references
while theoretically demoting the directory from spec-tooling recognition.

**Specific failure:** (a) `spec.yaml` itself is cited by line range
(`spec.yaml:1-52` at Codex handoff line 269), so deleting it breaks references.
(b) Removing `spec.yaml` doesn't actually prevent tooling discovery —
`spec-review-team` enters degraded mode on frontmatter-bearing markdown even without
a manifest (`SKILL.md:100`). The plan claimed both "full preservation" and "tooling
demotion" — these goals are in direct conflict.

**What it taught:** The preservation-vs-demotion tension is inherent, not fixable
by mechanical plan revision. This is what prompted stepping back to question the
migration itself.

### Physical migration: Frozen archive, spec.yaml kept

**Approach:** Keep EVERYTHING frozen at old path (zero deletions, zero modifications),
add only `FROZEN.md` as a marker. Be honest about the tradeoff: old tree remains a
valid spec root.

**Why it seemed promising:** Resolves the architectural contradiction by choosing
preservation and documenting the residual risk. Includes SHA256 hash verification,
safe stop points, atomic cutover.

**Why it was abandoned:** Not because it was technically wrong — it was the
least-bad migration option. Abandoned because the user identified that the benefit
(correct directory taxonomy) doesn't justify accepting the permanent tradeoffs
(duplicate spec root, ongoing confusion risk, split-brain maintenance) for a closed
spec with no planned modifications.

**What it taught:** The right question was "should we do this at all?" not "how do
we do this with the least damage?" The 552-line migration plan was the most
expensive possible way to deliver what turned out to be four prose edits.

## User Preferences

**Review style:** User provides structured adversarial reviews with exact line
references, severity ratings, and "Stronger change" prescriptions. Reviews follow a
consistent template: Highest-Risk Failure Points → Hidden Assumptions → Sequencing
Problems → Resource Risks → Edge Cases → What Must Change → Verdict.

**Scope discipline:** User explicitly asked for "core surfaces only" when given four
scope options. Rejected broader docs sweep and index creation as the "same
over-engineering trap the migration fell into."

**Values stepping back:** The most valuable contribution in the session was the user
questioning the fundamental premise after two rounds of mechanical improvement. User
said: "The right move is probably: reclassify T4 socially and normatively now,
relocate it physically later only if tooling or future churn makes that worth paying
for."

**Prefers honest tradeoffs:** User's reviews consistently flagged cases where the
plan claimed two incompatible benefits. Preferred plans that choose one side and
document the residual risk over plans that assert both benefits without acknowledging
the contradiction.

## Next Steps

### 1. Complete in-place reclassification execution

**Dependencies:** The reclassification plan is reviewed and approved with
"Defensible" verdict. The user has already started — four target files show unstaged
modifications.

**What to read first:** `docs/plans/04-03-2026-reclassify-t4-in-place.md` (the
approved plan, 83 lines).

**Approach:** Execute the four prose edits described in the plan, following these
clarifications from the review:
- T4 README: insert reclassification note after the Context block (line 24), before
  Authority Model (line 26).
- Monolith shim: strengthen "canonical spec" wording to say "canonical normative T4
  spec."
- Codex-collaboration README: add "Related Specs" section after Cross-Reference
  Conventions (currently line 59, last section).
- Benchmark contract: add cross-spec review rule after the three-item Change Control
  list at line 207. Use the exact text from step 4c of the (now-obsolete) migration
  plan, or write new prose that links to both T4 README and
  `benchmark-readiness.md#t4-br-09`.

**Acceptance criteria:** All test plan items in the reclassification plan pass.
Single commit, all four files.

### 2. Decide on obsolete migration plan files

**Dependencies:** None.

**What to decide:** Two untracked plan files exist on the branch:
- `docs/plans/2026-04-03-T4-peer-spec-reindexing.md` (552-line migration plan, 3
  revisions)
- `docs/plans/04-03-2026-reclassify-t4-in-place.md` (83-line reclassification plan)

Options: (a) Commit the reclassification plan as documentation, delete the migration
plan. (b) Commit both as historical record. (c) Delete both after execution (the git
diff tells the story). (d) Keep only the reclassification plan.

### 3. Fix pre-existing broken anchor aliases (optional, separate concern)

**Dependencies:** None — unrelated to reclassification.

**What to do:** Three anchors on the monolith shim are broken since the original
modularization. The decision record at
`docs/decisions/2026-04-03-conceptual-query-scope-constraint-for-benchmark-v1.md`
(gitignored) has four links using these broken anchors. Fix the links in the decision
record to point to the correct canonical targets via the crosswalk mapping (see
Pre-Existing Broken Anchors in Codebase Knowledge above).

## In Progress

The user has already started executing the in-place reclassification. The four target
files show unstaged modifications in `git status`. This session did not make those
modifications — they were made by the user outside Claude.

**State:** Plan reviewed and approved. Execution apparently in progress by user.
No Claude-side work is in flight.

**Next action:** Verify the user's modifications match the plan's intent, or let the
user complete execution and commit.

## Open Questions

1. **Branch strategy:** Should the reclassification commit land on
   `chore/t4-reindexing-plan-revision` and merge to main? Or should it go on a new
   branch with a more accurate name (e.g., `chore/t4-reclassification-in-place`)?

2. **Plan file disposition:** Should either or both plan files
   (migration plan, reclassification plan) be committed for posterity?

## Risks

1. **Filename convention inconsistency:** The reclassification plan uses
   `04-03-2026-` (MM-DD-YYYY) prefix instead of the repo's `2026-04-03-` (YYYY-MM-DD)
   convention. Low risk — cosmetic only.

2. **Future T4 reopening without relocation:** If T4 is reopened for active
   development, the `docs/plans/` location will cause the same classification friction
   that triggered this work. The reclassification plan's assumptions section documents
   this explicitly and defers to "revisit physical relocation only together with
   tooling/policy support."

## References

| What | Where |
|------|-------|
| In-place reclassification plan (approved) | `docs/plans/04-03-2026-reclassify-t4-in-place.md` |
| Obsolete migration plan (3 revisions) | `docs/plans/2026-04-03-T4-peer-spec-reindexing.md` |
| T4 modular spec root | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/README.md` |
| T4 spec.yaml (authority model) | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/spec.yaml` |
| Monolith shim | `docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` |
| Codex-collaboration README | `docs/superpowers/specs/codex-collaboration/README.md` |
| Benchmark contract | `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md` |
| spec-review-team skill | `packages/plugins/superspec/skills/spec-review-team/SKILL.md` |
| Shared contract (spec.yaml schema) | `packages/plugins/superspec/references/shared-contract.md` |
| Crosswalk (monolith→modular mapping) | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/crosswalk.md` |
| T4 close-out handoff (prior session) | `docs/handoffs/archive/2026-04-03_20-38_t04-t4-merge-to-main-and-cleanup.md` |
| Codex handoff with line-range citations | `~/.codex/handoffs/claude-code-tool-dev/.archive/2026-04-03_20-38_t4-sy-13-closeout-main-merge-and-remote-publish.md` |
| Decision record (broken anchors) | `docs/decisions/2026-04-03-conceptual-query-scope-constraint-for-benchmark-v1.md` |

## Gotchas

1. **`normative: false` in T4 README frontmatter:** This describes the README file
   itself (a supporting document), not the spec tree. Writing "normative peer
   specification" in README body prose is consistent — but an executor seeing
   `normative: false` while writing "normative" prose may hesitate. The frontmatter
   field applies to the file, not to the spec.

2. **spec-review-team degraded mode:** Removing `spec.yaml` from a directory does NOT
   make it invisible to tooling. If markdown files with frontmatter still exist,
   `spec-review-team` enters degraded mode and reviews anyway. This was the finding
   that killed the spec.yaml-removal approach.

3. **Archived Codex handoffs live in two locations:** Repo-local at
   `docs/handoffs/archive/` AND Codex-local at
   `~/.codex/handoffs/claude-code-tool-dev/.archive/`. Both cite T4 files by path and
   line range. Any migration must audit both surfaces.

4. **Working tree has user modifications:** The four target files are already modified
   (unstaged) when this handoff was created. These modifications were made by the user,
   not by Claude. Verify they match the approved plan before committing.
