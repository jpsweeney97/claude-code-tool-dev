---
date: 2026-04-06
time: "22:51"
created_at: "2026-04-07T02:51:47Z"
session_id: 7a933ade-7ff5-41da-85d3-9272958f25dc
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-06_15-07_f6-concession-lifecycle-resolved-and-pr93-merged.md
project: claude-code-tool-dev
branch: fix/f7-f11-provenance-wire-format-blockers
commit: 7786ebee
title: F7/F11 resolved and PR #94 opened
type: handoff
files:
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/provenance-and-audit.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/state-model.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/benchmark-readiness.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/boundaries.md
---

# Handoff: F7/F11 resolved and PR #94 opened

## Goal

Resolve the remaining two provenance wire-format blockers (F7 and F11)
as post-closure T4 contract amendments, publish as a combined PR, and
leave governance/cleanup for a separate pass.

**Trigger:** Prior session resolved F6 (PR #93) and established the
blocker framework (PR #92). The handoff's next steps were: decide the
`docs/t04-f6-f7-f11-ownership` branch fate, resolve F7, resolve F11,
then governance/cleanup.

**Stakes:** Without F7 and F11 resolved, the benchmark-readiness gate
at `benchmark-readiness.md:110-113` continues blocking scored runs and
policy-influencing calibration for `claim_provenance_index` and
`ClassificationTrace`. T7 can only proceed with T4-BR-08(a) exploratory
shakedowns.

**Success criteria:**
- F7 exit condition satisfied: canonical contract names emitting
  component, composition step, and interface for
  `claim_provenance_index` serialization
- F11 exit condition satisfied: explicit versioning rules including
  version scope, bump triggers, and consumer expectations
- All three blocker rows (F6, F7, F11) marked resolved
- PR opened and mergeable
- Governance/cleanup explicitly deferred to next pass

**Connection to project arc:** T4 close-out (SY-13) → reclassification
→ Path-2 benchmark constraint → T6 composition review (PR #91) →
ownership resolution matrix → blocker amendment (PR #92) → F6 resolver
(PR #93) → **F7/F11 resolver (PR #94, this session)** → governance/
cleanup pass → T7 executable slice unblocked once all gate conditions
clear.

## Session Narrative

### Phase 1: Load, branch cleanup, and sequencing decision

Session opened with `/load`, archiving the prior handoff (F6 resolved,
PR #93 merged). Main at `a78ddef1`.

First task: decide the fate of `docs/t04-f6-f7-f11-ownership` branch.
User presented a structured decision analysis with four options. I
stress-tested the recommendation via `git cherry -v`, confirmed the
branch had exactly 2 unique commits (handoff-history only) and 1
already-represented product commit. Verified the unique archived handoff
file did NOT exist on main. Agreed with the user's ranking: preserve the
archived handoff on main, then delete the branch. Recommended blob
extraction over cherry-pick to avoid base-dependent merge artifacts.

User executed the cleanup: extracted the file, committed as `4bcb3cf1`,
deleted the branch. One open bookkeeping item resolved.

User then presented a decision record for F7/F11/governance sequencing.
I scrutinized it against the referenced documents. Found 2 required
corrections (wrong line reference in information gap 1, underspecified
Option 2 escape hatch) and 3 strengthening items (T6-close framing,
orphan characterization, F11-may-amend-F7 cost). User applied all five.

### Phase 2: F7 analysis and implementation

User presented the F7 analysis with a clear framing: "resolve an
integration-language gap, not redesign the surface." Identified that the
emitting component (Phase 3 synthesis assembler), composition step
(after markdown synthesis assembly), and interface (`<!-- pipeline-data
-->` JSON epilogue) all existed implicitly across documents but were
never stated canonically in one place.

The F7 analysis established three guardrails:
1. No F11 bump-trigger policy or consumer expectations
2. No `scout_outcomes` evidence-trajectory orphan ownership
3. No T7 consumer/schema work

I confirmed the scope was correct. User drafted the F7 packet across
three files. I scrutinized the draft against the exit condition and all
three guardrails. Found 1 low finding: `provenance-and-audit.md:104-106`
said the dict "is mechanically serialized as
`claim_provenance_index_schema_version` plus the dense array" — grouping
the version carrier with the serialization product, when state-model.md
says the transformation adds no information. User applied the precision
fix: "serialized as the dense array, accompanied by the version carrier."

Verdict: Defensible after the one fix.

### Phase 3: F11 analysis and implementation

User presented the F11 analysis with the framing: "one carrier, two
governed surfaces." Key insight: F11 is now a policy problem, not a
carrier-introduction problem. The F6 packet established the version
carrier and the inheritance model. What remained was: version scope
(single carrier governs both `claim_provenance_index` and embedded
`ClassificationTrace`), bump triggers, and consumer expectations.

I scrutinized the analysis. Found 2 medium findings:
1. `boundaries.md:39` has a forward reference to F11 ("full bump-trigger
   policy remains under F11") that would become stale — user's write set
   excluded `boundaries.md`
2. The F11 exit condition says "version fields" (plural) — the
   single-carrier model is a design decision requiring explicit
   justification, not a "possibly a cleanup"

User accepted both findings and revised the plan: added `boundaries.md`
to the write set (now four files) and upgraded the single-carrier model
to an explicit normative decision with a three-part justification.

User then drafted the F11 packet. I scrutinized it against the five
acceptance criteria. Found 1 medium finding: the blocker subsection
intro paragraph at `benchmark-readiness.md:106-108` said "the audit
findings below remain unassigned" — stale now that all three rows are
resolved. User applied the fix: updated the intro to reflect the
resolved state while preserving the shakedown-vs-scored-use distinction.

Verdict: Defensible after the one fix.

### Phase 4: Publish decision and PR

User presented a publish sequencing decision with four options. I
recommended Option 2 (combined F7+F11 PR) over Option 1 (separate PRs):
both packets share the same T4-PR-03 section and were scrutinized
against each other; re-splitting would require non-trivial `git add -p`
work for marginal review benefit; and the decision record already
budgeted for combining if the clauses proved textually adjacent.

User created branch `fix/f7-f11-provenance-wire-format-blockers` from
`origin/main`, committed as `7786ebee`, pushed, and opened PR #94.

## Decisions

### Decision 1: Preserve docs/t04-f6-f7-f11-ownership archive on main, then delete branch

**Choice:** Extract the branch's unique archived handoff onto `main` via
blob extraction, then delete the stale local branch.

**Driver:** `git cherry -v main docs/t04-f6-f7-f11-ownership` showed 2
unique handoff-history commits and 1 already-represented product commit.
The unique file (`docs/handoffs/archive/2026-04-05_04-50_...`) did not
exist on main.

**Alternatives considered:**
- **Keep the branch as-is:** Preserves the commits but the branch name
  implies unresolved product work. Rejected because the product-bearing
  commit is already on main.
- **Delete now without preserving:** Loses the only ref to the archived
  handoff. Rejected because the file was not found in the external Codex
  handoff store.
- **Cherry-pick the two commits:** Would replay diffs from a different
  base, potentially introducing merge noise. Rejected in favor of blob
  extraction which is base-independent.

**Trade-offs accepted:** One additional commit on main for the archived
handoff file.

**Confidence:** High (E2) — verified via `git cherry -v`, `git show
--name-only`, and `ls` on main worktree.

**Reversibility:** High — the branch ref is gone but the commits still
exist in git's object store for garbage collection window.

**What would change this decision:** Nothing — this was a cleanup
operation, not a preference.

### Decision 2: Sequential F7-then-F11 with deferred governance

**Choice:** Resolve F7 first (narrow boundary-naming), then F11
(versioning policy), then governance/cleanup pass for T6 close and
evidence-trajectory orphan.

**Driver:** F7 is a narrow boundary-naming obligation; F11 is a broader
versioning-policy obligation that benefits from the stabilized F7
baseline. Governance/cleanup touches different documents and asks a
different question.

**Alternatives considered:**
- **Combined F7+F11 packet:** Higher scope-creep risk and muddled
  review. Acceptable fallback only if F7 and F11 prove textually
  inseparable.
- **F11 first:** Reverses the natural dependency. Versioning policy is
  easier to state once the emission boundary is named.
- **Governance first:** Adds an administrative loop before resolving
  live blockers. No credible path.

**Trade-offs accepted:** Touches adjacent documents in two logical
packets. F11 may force a narrow follow-up amendment to F7 wording (known
cost of sequential landing).

**Confidence:** High (E2) — verified the dependency direction across
`state-model.md:451`, `provenance-and-audit.md:95-109`, and
`benchmark-readiness.md:123-124`.

**Reversibility:** High — the sequencing is about review clarity, not
technical constraint.

**What would change this decision:** F7 drafting proving the versioning
rule is textually inseparable from the serialization-boundary clause.
Did not happen — clauses are adjacent but independent.

### Decision 3: Combined F7+F11 PR over separate PRs

**Choice:** Land both resolver packets as a single PR (#94) rather than
two separate PRs.

**Driver:** Both packets share the same T4-PR-03 section in
`provenance-and-audit.md`. F11's version scope clause (`:121-132`)
directly builds on F7's emission interface (`:95-109`). Re-splitting
the four-file worktree would require identifying which hunks belong to
F7 vs. F11 in files both packets edited.

**Alternatives considered:**
- **Separate PRs preserving sequential boundaries:** Best review clarity
  but requires non-trivial `git add -p` work. Rejected because marginal
  review benefit doesn't justify the git surgery.
- **Governance-first then publish:** Wrong scope order. Would mix
  purposes and delay ready work.

**Trade-offs accepted:** Weakens the sequential-landing discipline
somewhat. Mitigated by the PR body separating the F7 and F11 scopes
into distinct sections.

**Confidence:** High (E2) — verified that the combined diff is coherent
and the PR body maintains logical separation.

**Reversibility:** High — if separate PRs are preferred, the combined
commit can be split via `git diff` filtering.

**What would change this decision:** Reviewer requesting F7 and F11 as
separate review units. Not currently expected since the PR body already
separates them.

### Decision 4: One version carrier for both governed surfaces (F11)

**Choice:** `claim_provenance_index_schema_version` is the sole version
carrier for both `claim_provenance_index` and embedded
`ClassificationTrace`. No independent `ClassificationTrace` version
field.

**Driver:** `ClassificationTrace` is embedded inside `not_scoutable`
`ProvenanceEntry` entries (`provenance-and-audit.md:114-115`). Any
schema change to embedded `ClassificationTrace` IS a schema change to
`claim_provenance_index`. Independent versioning adds no information.

**Alternatives considered:**
- **Two version fields (per original F11 audit wording):** The rev17
  audit at `2026-04-03_02-06_...:156` recommended "monotonic
  `schema_version: int` on `claim_provenance_index` and
  `ClassificationTrace` pipeline-data surfaces." Rejected because the
  F6 packet established that `ClassificationTrace` is embedded, not
  standalone.
- **Standalone `ClassificationTrace` with its own version:** Would
  require un-embedding `ClassificationTrace` — a much larger
  architectural change that would reopen F6.

**Trade-offs accepted:** If `ClassificationTrace` ever needs to become a
standalone artifact surface, the single-carrier model would need
redesigning. Accepted because no scenario currently exists where
independent evolution adds value.

**Confidence:** High (E2) — verified the embedding model at
`provenance-and-audit.md:114`, the structural coupling (trace changes
are parent changes), and the precedent at `context-injection-contract.md:7`
and `event_schema.py:37`.

**Reversibility:** Medium — the single-carrier decision is now normative
in the contract. Adding a second carrier would require a version bump
and contract amendment.

**What would change this decision:** `ClassificationTrace` becoming a
standalone pipeline-data field rather than an embedded structure.

### Decision 5: Exact-match consumer versioning posture (F11)

**Choice:** Consumers must declare exact support for specific
`claim_provenance_index_schema_version` values. Unsupported versions
must be rejected for scored-run readiness and policy-influencing
calibration. No silent fallback or best-effort coercion.

**Driver:** The repo's existing versioning precedent is fail-closed.
`context-injection-contract.md:7` says "any version mismatch is
rejected." `event_schema.py:37` uses exact-match resolution.
`emit_analytics.py:566-573` raises `ValueError` on mismatch. The
benchmark gate cares about comparability: scored runs must compare
like-for-like.

**Alternatives considered:**
- **Supported set/range model:** Allows consumers to accept a range of
  versions. Rejected because it introduces compatibility logic that
  doesn't serve pre-1.0 contracts and weakens the comparability
  guarantee.
- **Semver with compatibility semantics:** Implies major/minor/patch
  compatibility. Rejected because the exact-match policy deliberately
  rejects compatibility assumptions.

**Trade-offs accepted:** Every version bump requires consumer updates
before scored runs can proceed. This is the correct behavior for
benchmark comparability but creates a coordination cost when versions
change.

**Confidence:** High (E2) — verified against three independent codebase
precedents (context-injection contract, event schema, analytics
emission).

**Reversibility:** Medium — the exact-match posture is now normative.
Loosening to a range model would require amending the consumer
expectations clause.

**What would change this decision:** Evidence that version bumps are too
frequent for the exact-match coordination cost to be sustainable. Not
currently a concern since no T7 consumers exist yet.

## Changes

### `provenance-and-audit.md` (61 insertions, 4 deletions)

**Purpose:** Add the F7 synthesis emission interface and the F11
version scope + bump trigger policy to T4-PR-03.

**State before session:** T4-PR-03 had the canonical wire format
(`:85-93`), the version carrier intro text (`:111-118` with F11 forward
reference), and the embedded `claim_id` equality invariant. No emission
interface clause, no version scope clause, no bump trigger policy.

**State after session:**

1. **Synthesis Emission Interface (`:95-109`):** Names the emitting
   component (Phase 3 synthesis assembler of `codex-dialogue`), the
   composition step (after markdown synthesis assembly from
   `turn_history`), and the interface (`<!-- pipeline-data -->` JSON
   epilogue). States that no evidence block, `scout_outcomes` projection,
   or other synthesis section is an alternate artifact interface.

2. **Version carrier intro update (`:111-119`):** Replaced F11 forward
   reference ("full bump-trigger policy remains governed by F11") with
   forward reference to the version-scope and bump-trigger rules below.

3. **Version Scope (`:121-132`):** States
   `claim_provenance_index_schema_version` is the sole version carrier
   for both `claim_provenance_index` and embedded `ClassificationTrace`.
   Justifies: embedded traces are not standalone, trace changes are
   parent changes, independent versioning adds no information.

4. **Bump Trigger Policy (`:134-157`):** Monotonic integer. Version bump
   REQUIRED for: field addition/removal/rename/requiredness change,
   type/nullability/allowed-value/invariant change, variant-set change,
   discriminator change, dense-array/index semantics change,
   embedded-versus-standalone placement change. NOT required for:
   examples, cross-references, wording clarifications, adjudicator
   workflow guidance that doesn't alter emitted fields or consumer
   obligations.

### `state-model.md` (5 insertions, 2 deletions)

**Purpose:** Tie the existing mechanical transformation in T4-SM-07 to
the single artifact handoff point.

**State before session:** Serialization boundary note at `:451-458`
described the mechanical transformation but didn't name where the
artifact handoff occurs.

**State after session:** Added `:459-462`: "The artifact handoff occurs
only in the Phase 3 synthesis assembler's `<!-- pipeline-data -->` JSON
epilogue as specified in T4-PR-03."

### `benchmark-readiness.md` (36 insertions, 12 deletions)

**Purpose:** Resolve F7 and F11 rows, add consumer expectations, update
governance framing.

**State before session:** F7 and F11 active in the blocker table. Intro
paragraph said "remain unassigned." Closing paragraph scoped to
"remaining unresolved rows." Option B prose described F11 as "split
between" T4 and T7.

**State after session:**

1. **F7 resolved row (`:123`):** Marked `F7 (resolved)`. Exit condition
   replaced with citations: T4-SM-07 and T4-PR-03.

2. **F11 resolved row (`:124`):** Marked `F11 (resolved)`. Exit
   condition replaced with citations: T4-PR-03 and F11 Consumer
   Expectations.

3. **Option B prose update (`:126-131`):** "F11 resolves through a
   T4-side normative versioning rule in T4-PR-03 and a T7-side consumer
   expectation rule in this subsection."

4. **Closing paragraph update (`:133-137`):** Changed to "While any row
   in this subsection remains unresolved" — conditional that gracefully
   handles the empty set (all resolved).

5. **Intro paragraph update (`:106-113`):** Updated to reflect resolved
   state. No longer says "remain unassigned."

6. **F11 Consumer Expectations (`:139-148`):** New anchored subsection.
   Exact support for specific versions, reject unsupported for scored
   readiness and policy-influencing calibration, no silent fallback or
   best-effort coercion, consumer update required before scored runs
   on new versions.

### `boundaries.md` (2 insertions, 2 deletions)

**Purpose:** Replace stale F11 forward reference with direct policy
citation.

**State before session:** `:39` said "full bump-trigger policy remains
under F11."

**State after session:** `:39` says "version scope and bump-trigger
policy in [T4-PR-03]" and "governs embedded `ClassificationTrace`."

## Codebase Knowledge

### `benchmark-readiness.md` (292 lines, post-F7/F11)

| Section | Lines | State | Relevance |
|---|---|---|---|
| T4-BR-01: T5 Migration Surfaces | `:14-43` | Unchanged | |
| T4-BR-02: Transcript Fidelity | `:45-61` | Unchanged | |
| T4-BR-03: Allowed-Scope Safety | `:63-78` | Unchanged | |
| T4-BR-04: Provenance Index Consumer | `:79-91` | Unchanged | Consumer surface tables (T7-owned) |
| T4-BR-05: Synthesis-Format Contract Updates | `:92-103` | Unchanged | |
| **F6/F7/F11 Blockers** | **`:104-148`** | **Modified** | All three rows resolved, intro updated, consumer expectations added |
| T4-BR-06: Narrative Factual-Claim Inventory | `:150-165` | Unchanged | |
| T4-BR-07: Benchmark-Execution Prerequisites | `:167-231` | Unchanged | |
| T4-BR-08: Non-Scoring Run Classification | `:233-255` | Unchanged | Source of (a)/(b) classification |
| T4-BR-09: Benchmark-Contract Amendment | `:257-292` | Unchanged | |

### `provenance-and-audit.md` — key contract surfaces post-edit

| Section | Lines | State | F7/F11 relevance |
|---|---|---|---|
| T4-PR-01: Evidence Trajectory | `:14-48` | Unchanged | `scout_outcomes` projection — NOT the F7 interface |
| T4-PR-02: Synthesis-Record Join | `:50-64` | Unchanged | |
| T4-PR-03: Claim Provenance Index | `:65-173` | **Modified** | F7 emission interface, F11 version scope + bump triggers |
| T4-PR-04: Two Provenance Tiers | `:175-186` | Unchanged | |
| T4-PR-05: Claim Ledger | `:187-231` | Unchanged | |
| T4-PR-06: Narrative-to-Ledger | `:233-249` | Unchanged | |

### Cross-reference map (F7+F11 packets)

| Source | Target | Purpose |
|---|---|---|
| `provenance-and-audit.md:97-109` (Emission Interface) | `dialogue-synthesis-format.md:3`, `:140` | Names Phase 3 synthesis assembler and pipeline-data sentinel |
| `provenance-and-audit.md:104-106` (Emission Interface) | `state-model.md#t4-sm-07` | References mechanical transformation |
| `provenance-and-audit.md:121-132` (Version Scope) | Single-carrier justification | One carrier governs both surfaces |
| `provenance-and-audit.md:134-157` (Bump Trigger Policy) | Wire-level change categories | Required and non-required bump triggers |
| `state-model.md:459-462` (Serialization boundary) | `provenance-and-audit.md#t4-pr-03` | Ties artifact handoff to single emission point |
| `benchmark-readiness.md:123` (F7 row) | T4-SM-07, T4-PR-03 | Resolution citations |
| `benchmark-readiness.md:124` (F11 row) | T4-PR-03, F11 Consumer Expectations | Resolution citations |
| `benchmark-readiness.md:139-148` (Consumer Expectations) | Exact-match versioning rule | T7-side obligations |
| `boundaries.md:39` (Version carrier) | T4-PR-03 | Direct policy citation (replaced stale F11 forward reference) |

### Versioning precedent surfaces verified

| Surface | Location | Versioning posture |
|---|---|---|
| Context injection contract | `context-injection-contract.md:7` | Exact match, any mismatch rejected |
| Analytics event schema | `event_schema.py:37` | `resolve_schema_version()` feature-flag-based exact match |
| Analytics emission | `emit_analytics.py:566-573` | `ValueError` on schema_version mismatch |
| Analytics stats | `compute_stats.py:196-207` | Counts `schema_version` distributions |

### Evidence-trajectory consumer-projection orphan

The `scout_outcomes` projection at `provenance-and-audit.md:34-48` is
projected from `turn_history` (step 5d), NOT serialized into
`<!-- pipeline-data -->`. F7 explicitly states it is not an alternate
artifact interface. F11 does not assign it. It remains unowned in
current gate tables per
`2026-04-04-t04-t6-benchmark-first-design-composition-review.md:182-185`.
Disposition deferred to governance/cleanup pass.

## Context

### Mental model for this session

**Framing:** This session was about closing the blocker table — landing
the last two resolver packets to unblock scored benchmark runs. The
F6 session's core learning (coupled-constraint analysis, framing before
solving) was applied from the start: F7 was framed as an
integration-language gap, F11 was framed as policy codification over an
existing carrier.

**Core insight:** The progression F6 → F7 → F11 demonstrates narrowing
scope. F6 was a coupled-constraint problem (84 insertions, 5 scrutiny
rounds). F7 was a single-gap naming problem (21 insertions, 1 finding).
F11 was policy codification over an established foundation (66
insertions, 2+1 findings across analysis and draft scrutiny). Each
packet landed faster because the prior packets established clean
foundations.

**Secondary insight:** The single-carrier decision for F11 shows the
value of the F6 embedding model. By establishing that
`ClassificationTrace` is embedded (not standalone), F6 pre-answered
F11's biggest design question: one carrier or two? The answer was
already implicit in F6 — F11 just needed to make it explicit and
normative.

### Project state (post-session)

- **T4:** Closed at SY-13. F6, F7, F11 all resolved as post-closure
  contract amendments. The blocker table gate is now open — all exit
  conditions satisfied.
- **T5:** Designs accepted. `agent_local` ownership clarified in T6
  review.
- **T6:** Composition review shipped (PR #91). Administrative close
  still open. T6 done-when criterion requires blessing the final state
  (post-F7/F11 amendments).
- **F6:** Resolved (PR #93).
- **F7:** Resolved (PR #94 pending merge).
- **F11:** Resolved (PR #94 pending merge).
- **T7:** Unblocked for scored runs once PR #94 merges and all gate
  conditions are confirmed. May proceed with T4-BR-08(a) exploratory
  shakedowns immediately.

### Environment

- Working directory: `/Users/jp/Projects/active/claude-code-tool-dev`
- Branch: `fix/f7-f11-provenance-wire-format-blockers`
- Commit: `7786ebee`
- PR: #94 (ready, mergeable)
- Local `main` is ahead of `origin/main` by 3 local-only commits
  (handoff archive and branch-preserve commits)

## Learnings

### Each resolver packet lands faster when prior packets establish clean foundations

**Mechanism:** F6 was a coupled-constraint problem requiring 5 scrutiny
rounds and 84 insertions because it had to establish the embedding
model, the version carrier, and the concession lifecycle simultaneously.
F7 was 21 insertions with 1 low finding — it named an existing mechanism
without redesigning it. F11 was 66 insertions with 2+1 findings — it
codified policy over an established carrier. The narrowing scope is not
just about problem size; it's about foundation quality.

**Evidence:** F7 scrutiny verdict was "Defensible" on first review
(after 1 low phrasing fix). F11 analysis scrutiny surfaced 2 medium
findings (write set gap, design decision framing) that the user
incorporated before drafting. F11 draft scrutiny found 1 medium finding
(stale intro paragraph). Contrast with F6: the first analysis was
rejected outright for solving the wrong problem.

**Implication:** For future resolver packets, invest in making the
foundation explicit rather than leaving it for later packets to infer.
The F6 embedding model decision implicitly answered F11's biggest
question — but it took the F11 analysis to make that explicit.

**Watch for:** Packets that seem simple because they're building on
implicit foundations. The simplicity is real only if the foundation is
normatively stated, not just implied.

### Stale forward references are a systematic risk in multi-packet resolver sequences

**Mechanism:** When a blocker table has forward references to unresolved
findings ("full bump-trigger policy remains under F11"), resolving the
finding doesn't automatically update the references. Each resolver
packet must update not just the blocker row but all forward references
to that row across the authority set.

**Evidence:** The F11 analysis scrutiny found `boundaries.md:39` saying
"remains under F11" — excluded from the original write set. The F11
draft scrutiny found the intro paragraph at `benchmark-readiness.md:
106-108` saying "remain unassigned" with all rows resolved. Both were
the same class of stale-reference problem.

**Implication:** When resolving the last row in a governance subsection,
grep for forward references to the finding ID across all authority
documents. Update or remove each one.

**Watch for:** Forward references phrased as "remains under F[N]" or
"deferred to F[N]" in documents adjacent to the blocker table.

### The single-carrier decision demonstrates when implicit architecture answers design questions

**Mechanism:** The F6 packet's statement that "Embedded
`ClassificationTrace` inherits this version because it is serialized
inside `claim_provenance_index` entries, not as a standalone
pipeline-data field" was descriptive — it described what was true, not
what was decided. The F11 packet elevated this to a normative design
decision with a three-part justification. The design question (one
carrier or two?) was already answered by the F6 embedding model, but it
took explicit effort to recognize and codify this.

**Evidence:** The original F11 audit finding recommended two version
fields. The F6 packet implicitly resolved this by establishing the
embedding model. The F11 analysis made the connection explicit: "F11
should codify that shared version axis rather than invent a second
`ClassificationTrace` version field."

**Implication:** When working on resolver packets, check whether prior
packets' descriptive statements already answer the current packet's
design questions. If so, the current packet's job is to make the answer
normative, not to re-derive it.

**Watch for:** Audit findings whose original wording assumes an
architecture that has since changed. The finding's intent may still be
valid even if its literal recommendation is outdated.

## Next Steps

### 1. Merge PR #94

**Dependencies:** None — PR is ready and mergeable.

**What to do:** Review and merge via `gh pr merge 94`. Fast-forward
local main. Delete the delivery branch.

**Acceptance criteria:** Merge commit on main. Branch deleted (local
and remote). All three blocker rows visible as `(resolved)` on main.

### 2. Governance/cleanup pass

**Dependencies:** PR #94 merged.

**What to do:** Three items:
1. **T6 administrative close:** Read
   `2026-04-04-t04-t6-benchmark-first-design-composition-review.md:173-195`
   and `2026-04-01-t04-benchmark-first-design-plan.md:39`. Decide
   whether T6 closes now (final-state blessing) or stays open. The
   decision record says to use a final-state framing if closing after
   F7/F11.
2. **Evidence-trajectory consumer-projection orphan:** Read
   `provenance-and-audit.md:34-48`. Either assign an explicit owner or
   declare that no T4-T7 gate owns it.
3. **Stale branch cleanup:** Review `git branch -a` and prune.
   `feature/codex-collaboration-r2-dialogue` was flagged as unrelated in
   the prior handoff with a long stack of unique commits and upstream
   gone.

**What to read first:**
- `2026-04-04-t04-t6-benchmark-first-design-composition-review.md:173-195`
- `2026-04-01-t04-benchmark-first-design-plan.md:39`
- `provenance-and-audit.md:34-48`
- `git branch -a`

### 3. Push local-only commits on main

**Dependencies:** None — can be done any time.

**What to do:** Local `main` has 3 commits ahead of `origin/main`:
handoff archive commit from session start plus the
`docs/t04-f6-f7-f11-ownership` branch-preserve commit. Push to sync.

**Acceptance criteria:** `git status` shows `main` even with
`origin/main`.

## In Progress

**Clean stopping point.** PR #94 opened and mergeable. F7 and F11
resolved. Branch cleanup done from the prior session. No work in flight.

The decision record at
`docs/decisions/2026-04-06-f7-f11-resolution-sequencing.md` is
local-only (gitignored at `.gitignore:20`). This is by design — decision
records are session-local reference material.

## Open Questions

1. **Should T6 close administratively now?** The T6 done-when criterion
   at `2026-04-01-t04-benchmark-first-design-plan.md:39` asks whether
   the gates compose coherently. F7/F11 modified the composition surface
   after T6's review. The decision record says use a "final-state
   blessing" framing if closing after F7/F11.

2. **What happens to the evidence-trajectory consumer projection?**
   `provenance-and-audit.md:34-48` (`scout_outcomes`) is unowned in
   gate tables. It's NOT part of the F7 interface (explicitly excluded).
   Does it need an owner, or is it implicitly covered by the existing
   T7-owned `scout_outcomes` entry in T4-BD-01 at `boundaries.md:25`?

3. **Should `feature/codex-collaboration-r2-dialogue` be cleaned up?**
   Flagged in the prior handoff as having a long stack of unique commits
   with upstream gone. Out of scope for the blocker thread but worth a
   separate decision.

4. **Should the local-only commits on main be pushed?** Three
   handoff-lifecycle commits on local main that are not on origin. They
   don't affect the PR (which is based on `origin/main`) but create
   local/remote divergence.

## Risks

1. **PR #94 is pending merge.** Until merged, F7 and F11 are resolved
   only on the delivery branch. The blocker gate on main still blocks
   scored runs. Low risk — PR is ready and mergeable.

2. **Local main diverges from origin/main by 3 commits.** These are
   handoff-lifecycle commits, not product changes. No functional risk
   but creates confusion if forgotten.

3. **T6 administrative close has a chronological inversion.** If T6
   closes after F7/F11, the close note blesses a state that didn't exist
   when T6's review ran. The decision record recommends using a
   "final-state blessing" framing. If this framing is rejected, T6 may
   need a lighter follow-up review.

4. **Post-closure amendment framing may not survive larger packets.**
   F6 was 84 insertions, F7+F11 combined is 87 insertions. All three
   packets are "post-closure amendments." If future T4 work requires
   more substantial changes, the amendment framing starts resembling T4
   phase reopening. Same risk as prior sessions, carried forward.

## References

| What | Where |
|---|---|
| PR #94 (F7/F11 resolver, pending merge) | https://github.com/jpsweeney97/claude-code-tool-dev/pull/94 |
| PR #93 (F6 resolver, merged) | https://github.com/jpsweeney97/claude-code-tool-dev/pull/93 |
| PR #92 (blocker framework, merged) | https://github.com/jpsweeney97/claude-code-tool-dev/pull/92 |
| F7+F11 commit | `7786ebee docs(plans): resolve F7/F11 provenance wire-format blockers` |
| Branch-preserve commit | `4bcb3cf1 docs(handoff): preserve F6/F7/F11 branch-init archive` |
| F7 emission interface | `provenance-and-audit.md:95-109` |
| F11 version scope | `provenance-and-audit.md:121-132` |
| F11 bump trigger policy | `provenance-and-audit.md:134-157` |
| F11 consumer expectations | `benchmark-readiness.md:139-148` |
| F7 resolved row | `benchmark-readiness.md:123` |
| F11 resolved row | `benchmark-readiness.md:124` |
| Version carrier (updated) | `provenance-and-audit.md:111-119` |
| Serialization boundary (updated) | `state-model.md:451-462` |
| Boundaries version carrier (updated) | `boundaries.md:39` |
| Decision record (gitignored) | `docs/decisions/2026-04-06-f7-f11-resolution-sequencing.md` |
| T6 disposition | `docs/reviews/2026-04-04-t04-t6-benchmark-first-design-composition-review.md:173-195` |
| T6 done-when | `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md:39` |
| Evidence-trajectory orphan | `provenance-and-audit.md:34-48` |
| Versioning precedent: context-injection | `context-injection-contract.md:7` |
| Versioning precedent: event schema | `event_schema.py:37` |
| Versioning precedent: analytics | `emit_analytics.py:566-573` |

## Gotchas

1. **The `schema_version` references in scripts/ are NOT about
   `claim_provenance_index_schema_version`.** `event_schema.py:37`,
   `emit_analytics.py:430`, `codex_delegate.py:550`, and
   `compute_stats.py:203` all reference the analytics event schema
   version, not the provenance index version. These are different
   versioning surfaces. Grep for `claim_provenance_index` (not
   `schema_version`) to find actual provenance-index consumers.

2. **Local main diverges from origin/main.** Three local-only commits:
   handoff archive from session start and the branch-preserve commit.
   The PR (#94) is based on `origin/main`, so these don't affect the PR.
   But `git log main..origin/main` will show nothing while
   `git log origin/main..main` shows the local-only commits.

3. **The decision record is gitignored.** The F7/F11 sequencing decision
   at `docs/decisions/2026-04-06-f7-f11-resolution-sequencing.md` is
   local-only. It won't appear in `git status` or be included in any PR.
   If needed for reference, read it directly.

4. **The closing paragraph is now a dormant conditional.** With all three
   rows resolved, `benchmark-readiness.md:133` ("While any row in this
   subsection remains unresolved...") evaluates to false. The MUST
   obligation is inactive. The canonization gate is open. Don't read the
   closing paragraph as still blocking — check the table.

5. **All F7/F11 changes live on a delivery branch, not main.** Until PR
   #94 merges, `main` still shows F7 and F11 as active blockers. The
   resolved state exists only on
   `fix/f7-f11-provenance-wire-format-blockers`.

6. **The bump-trigger policy uses "consumer may rely on" as the
   criterion.** This is deliberately subjective — it means a T7 consumer
   that correctly implements the prior version. The subjectivity is
   intentional: a mechanical list would be incomplete because the
   potential change space is open-ended. The criterion is "would a
   correct prior-version consumer break?"

7. **User applied every scrutiny finding (100% apply rate, sixth
   session).** The same pattern from the F6 session continues. Every
   finding from analysis scrutiny, draft scrutiny, and decision record
   scrutiny was incorporated. The test for flagging: "would I apply this
   in my own work?"

## Conversation Highlights

### Stress-testing the branch decision

User presented a fully structured decision analysis for the
`docs/t04-f6-f7-f11-ownership` branch (four options, information gaps,
evaluation, sensitivity, ranking, recommendation, and readiness). I
verified via `git cherry -v`, `git show`, and `ls` — all claims
confirmed. Key contribution: recommending blob extraction over
cherry-pick to avoid base-dependent merge artifacts.

### F7 analysis acceptance

User's F7 framing was accepted without revision: "resolve an
integration-language gap, not redesign the surface." The three guardrails
(no F11 policy, no scout_outcomes ownership, no T7 consumer work) were
directly applied from the decision record's sequential-landing
discipline and the F6 session's co-gating constraint learning.

### F11 analysis scrutiny surfacing the boundaries.md gap

The analysis scrutiny's most consequential finding was that the write set
excluded `boundaries.md`, which had a forward reference to F11 that
would become stale. The user's response: "Accepted. The two findings
tighten the packet; they do not change the design direction." Added
`boundaries.md` to the write set immediately.

### Combined PR recommendation

User presented a four-option publish decision. I recommended Option 2
(combined F7+F11 PR) with three supporting arguments: shared T4-PR-03
section, non-trivial re-splitting cost, and the decision record already
budgeting for this possibility. User agreed and executed.

## User Preferences

**Writes substantive content themselves (sixth session now):** User
drafted the F7 analysis, F11 analysis, all implementation text, the
sequencing decision record, the branch decision analysis, and the
publish decision analysis. My role: scrutinize, surface findings, apply
minor edits per accepted text. Do not draft substantive normative content
unless explicitly asked.

**Treats every flagged item as actionable (100% apply rate — sixth
session):** Every finding from scrutiny was addressed. The test for
flagging: "would I apply this in my own work?"

**Presents decisions in structured format:** User consistently uses:
stakes, options, information gaps, evaluation, sensitivity, ranking,
recommendation, readiness. Expects the same structure in scrutiny
responses.

**Prefers scrutiny to be reject-until-proven-credible:** The user's
corrections and pushback are substantive (not stylistic). The F6
session's rejection of the first analysis set the bar. Quality of
scrutiny should match the quality the user delivers.

**Combined PRs acceptable when re-splitting is costly:** User agreed to
the combined F7+F11 PR recommendation. Strict sequential landing is
preferred but not absolute — operational simplicity can win when review
clarity is preserved via PR body structure.
