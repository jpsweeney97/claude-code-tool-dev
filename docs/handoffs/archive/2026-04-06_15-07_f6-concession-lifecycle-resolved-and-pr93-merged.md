---
date: 2026-04-06
time: "15:07"
created_at: "2026-04-06T19:07:19Z"
session_id: aaf4ffa6-82c1-438a-a37f-8354a3de5d0c
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-06_01-21_f6-f7-f11-blocker-amendment-published-and-ownership-decided.md
project: claude-code-tool-dev
branch: main
commit: a78ddef1
title: F6 concession lifecycle resolved and PR #93 merged
type: handoff
files:
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/state-model.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/provenance-and-audit.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/boundaries.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/benchmark-readiness.md
---

# Handoff: F6 concession lifecycle resolved and PR #93 merged

## Goal

Resolve F6 (concession lifecycle contract) as the first blocker cleared
under the F6/F7/F11 governance framework established in PR #92, then
merge the result as PR #93.

**Trigger:** PR #92 merged in the prior session, establishing the
blocker table, enforcement wiring, and canonization gate in
`benchmark-readiness.md`. The handoff's next step was to start the F6
resolver packet on a fresh branch.

**Stakes:** Without F6 resolution, `claim_provenance_index` and
`ClassificationTrace` remain provisional under
`benchmark-readiness.md:111-113`. T7 consumer work can only proceed as
T4-BR-08(a) exploratory shakedowns — no scored benchmark runs, no
policy-influencing calibration, no stability claims.

**Success criteria:**
- F6 exit condition satisfied: contract states how concession status
  appears in `claim_provenance_index`, how conceded positions appear in
  the dense array, and whether conceded claims appear in the claim ledger
- Minimum F11 versioning guardrail in place so the schema change doesn't
  create an unversioned external wire-format mutation
- F7 and F11 explicitly left active
- Option B ownership posture landed durably in `benchmark-readiness.md`
- PR merged to main

**Connection to project arc:** T4 close-out (SY-13) → reclassification
→ Path-2 benchmark constraint → T6 composition (7 review passes across
3 sessions) → ownership resolution matrix → review-doc correction (PR
#91) → blocker amendment (PR #92, merged at start of this session) →
**F6 resolver packet (PR #93, merged this session)** → F7/F11 resolver
packets → T7 executable slice unblocked once all blocker rows clear.

## Session Narrative

### Phase 1: Load, orientation, and PR #92 clause fix

Session opened with `/load`, resolving to the prior handoff (958 lines).
Archived and wrote state file per chain protocol. Confirmed branch
`fix/f6-f7-f11-blockers-publish` at `9b16e79e` (2 commits ahead of
origin — two handoff-lifecycle commits from the prior session plus the
original blocker amendment).

User immediately raised a finding against PR #92 before merge:
`benchmark-readiness.md:121-124` contained a normative softening — "MUST
either resolve the applicable row directly **or** assign a remediation
owner in current gate tables before canonization can be claimed" — which
created an escape path where merely assigning an owner could be read as
sufficient for canonization.

I analyzed the three-clause structure: the blocker rule (`:111-113`),
the enforcement hook (`:182-187`), and the closing paragraph
(`:121-124`). The first two were unconditional; only the third had the
"or assign" disjunction. User accepted that the loophole was real but
constrained (canonization requires a scored run, which clauses 1+2
block), and directed Option A: split into two sentences preserving the
obligation but making canonization explicitly wait on exit conditions.

Applied the one-line edit. User identified that the local branch had
accumulated handoff-lifecycle commits that would leak into PR #92 if
pushed. User executed a safety-branch-then-reset sequence: created
`chore/backup-pr92-handoff-history`, stashed the clause fix, reset to
`origin/fix/f6-f7-f11-blockers-publish`, reapplied the fix, committed
as `758901a3`, pushed, then cleaned up the backup branch and stash.

User then merged PR #92 via `gh`, fetched origin, and fast-forwarded
local main to `20c6b338`.

### Phase 2: F6 analysis — first attempt rejected

User requested a thorough pre-implementation analysis of the F6 resolver
packet. I read all contract surfaces per the handoff's read-first list:
`benchmark-readiness.md:104`, the F6 audit at
`2026-04-02-t04-t4-evidence-provenance-rev17-team.md:133`,
`provenance-and-audit.md:65` (T4-PR-03), `:151` (T4-PR-05), `:166`
(T4-PR-06), `state-model.md:418-430` (ProvenanceEntry schema), `:374-392`
(lifecycle table), and `:53-60` (concession exception).

Delivered six findings. User rejected the analysis with a detailed
adversarial review identifying three critical failures:

1. **F11 co-gating ignored.** `state-model.md:437-442` says
   serialization is mechanical — any `ProvenanceEntry` schema change IS
   an external wire-format change. My analysis treated F11 as a later
   dependency instead of a co-gating constraint.

2. **Ledger annotation path dead on arrival.** I proposed evaluating
   `[conceded]` annotations as a serious alternative even though
   `provenance-and-audit.md:155` explicitly says "No outcome tags. Facts
   are facts, not dialogue events."

3. **Reintroduction-after-concession ignored.** `state-model.md:390-391`
   allows reintroduction with new `claim_id`, creating coexistence
   between old conceded entries and new live entries. My analysis didn't
   address this.

The user's systemic diagnosis: I was solving the problem too locally,
optimizing within a single blocker's boundary when the constraint surface
spans three coupled documents and two other unresolved blockers.

### Phase 3: Corrected analysis — minor revision

User delivered a corrected analysis from the coupled-constraint premise:
"What F6 change can land without creating a new unversioned external
contract break or leaving the lifecycle model underspecified?" This
reframing eliminated the dead options and exposed the minimum viable
packet shape: F6 + minimum F11a guardrails.

I scrutinized the corrected analysis. Verdict: minor revision. Three
medium findings:
1. Version-carrier scope needed to explicitly state it covers
   `claim_provenance_index` (with embedded `ClassificationTrace`), not
   pipeline-data generically.
2. The T4-PR-06 exemption for concession-history reporting may already be
   implicit in the scope restriction (repository-facing categories) —
   verify before writing a new exception clause.
3. `scouting-behavior.md` should be listed as "verified unchanged" not
   "likely needed."

User accepted all three findings and produced a revised packet shape
with the revisions incorporated.

### Phase 4: Pre-implementation checklist — minor revision

User delivered a detailed pre-implementation checklist: exact edits with
line references, dependency-ordered sequence, blocker-clearance tests
with pass/fail criteria, and stop conditions. I scrutinized it. Verdict:
minor revision. Two high findings:

1. **Missing lifecycle table edit point.** The lifecycle table at
   `state-model.md:389` wasn't explicitly listed alongside the Phase 1
   processing (`:83`) and Concession Exception (`:53`) edit points.

2. **Missing lifecycle step specification.** No edit item said "add a
   step to Phase 1 that sets `claim_provenance_index[claim_id].conceded
   = true`." A field in the schema without a processing step is exactly
   the kind of gap F6 exists to close.

Plus three medium findings: category-based vs. section-based scoping for
T4-PR-06, unspecified `conceded: bool` default/optionality, and
unspecified version carrier field name and initial value.

User folded all findings into the implementation.

### Phase 5: Implementation, review, and merge

User created `fix/f6-concession-lifecycle-contract` from main and
implemented the full checklist across four files. 84 insertions, 29
deletions. I scrutinized the implementation against all blocker-clearance
tests. All seven tests passed. Two medium findings:

1. **T4-BR-07 cross-reference phrasing** at
   `benchmark-readiness.md:165-170` said "until those blockers are
   resolved" — could be read as all or specific. Not a regression but
   worth tightening to "until all applicable blocker conditions in that
   subsection are satisfied."

2. **Missing blank line** at `provenance-and-audit.md:192-193` merged
   the category-boundary clarification with the MUST NOT paragraph.

User applied both fixes, committed as `1453665d`, pushed, and opened
draft PR #93. I marked it ready and merged via `gh`. Merge commit
`a78ddef1`.

### Phase 6: Branch cleanup

Deleted three safe merged branches (local and remote):
- `fix/f6-f7-f11-blockers-publish` (PR #92)
- `chore/track-t6-review` (PR #91)
- `fix/f6-concession-lifecycle-contract` (PR #93)

Left `docs/t04-f6-f7-f11-ownership` alone per user's recommendation —
it carries two unique handoff-history commits not represented on main.
Left `feature/codex-collaboration-r2-dialogue` out of scope for this
thread.

## Decisions

### Decision 1: Clause tightening before PR #92 merge

**Choice:** Split the closing paragraph of the blocker subsection into
two sentences — one for the obligation (resolve or assign), one for
the canonization gate (exit conditions must be satisfied).

**Driver:** User identified that the disjunction "MUST either resolve
... or assign a remediation owner ... before canonization can be claimed"
created an escape-path reading where merely assigning an owner could be
read as sufficient for canonization.

**Alternatives considered:**
- **Leave as-is (Option B from my analysis):** The operational bypass is
  constrained because canonization requires a scored run, which clauses
  1+2 block. Rejected by user: "A reader should not need to reconcile
  three clauses to discover that owner assignment is not sufficient for
  canonization."
- **Remove the "or assign" path entirely:** Would lose the governance
  intent that the next packet must at minimum assign ownership. Rejected
  as too restrictive.

**Implications:** The three normative clauses in the blocker subsection
now converge on the same scope test: blocker rule (`:111-113`),
closing paragraph (`:124-125`), and enforcement hook (`:182-187`).

**Trade-offs accepted:** None material. The edit adds one sentence
without changing the normative structure.

**Confidence:** High (E2) — verified alignment across all three clauses
post-edit.

**Reversibility:** High — the edit is additive (one sentence added) and
can be removed without affecting the other two clauses.

**What would change this decision:** Nothing — this corrects a normative
ambiguity, not a preference.

### Decision 2: F6 + minimum F11a guardrails as packet shape (not pure F6-only)

**Choice:** The resolver packet includes F6 concession lifecycle
semantics AND the minimum versioning guardrail needed to make the
`claim_provenance_index` schema change legal. It does not claim to
resolve F7 or full F11.

**Driver:** `state-model.md:437-442` says serialization is mechanical —
any `ProvenanceEntry` schema change propagates directly to the external
wire format. `claim_provenance_index` has no version metadata
(`provenance-and-audit.md:65-106`). F11 names `claim_provenance_index`
as an unversioned format (`benchmark-readiness.md:119`). Therefore, any
F6 schema mutation without a version carrier deepens the exact F11
defect the blocker table says is unresolved.

**Alternatives considered:**
- **Pure F6-only packet:** Would add `conceded: bool` to the wire format
  without any versioning. Rejected because it creates an unversioned
  external schema mutation — exactly the problem F11 identifies.
- **Full F6 + F7 + F11 combined packet:** Would resolve all three
  blockers at once. Rejected as too broad — F7 requires naming the
  serialization mechanism (emitting component, composition step,
  interface), and F11 requires full bump-trigger and consumer-expectation
  policy. Neither is needed for F6 to be defensibly resolved.

**Implications:** F11 inherits a named version carrier field
(`claim_provenance_index_schema_version: 1`) with explicit scope. The
F11 resolver packet defines the full policy; it doesn't need to also
invent the carrier.

**Trade-offs accepted:** The version carrier exists with an initial value
but incomplete policy. A consumer seeing version 1 knows the shape but
not the bump rules. Accepted because no consumers exist yet (T7 hasn't
built anything) and the full policy is F11's scope.

**Confidence:** High (E2) — verified the serialization coupling at
`state-model.md:437-442` and the F11 blocker row at
`benchmark-readiness.md:119`.

**Reversibility:** Medium — the version carrier field name and initial
value are now in the contract. Changing the field name would be a
migration. Changing the value or policy is straightforward.

**What would change this decision:** If a future packet discovers that
the version carrier needs to wrap the array into an object (rather than
being a sibling field), that would force a larger migration.

### Decision 3: Orthogonal `conceded: bool` over third `type` variant

**Choice:** Add `conceded: bool` as a required field on both
`ProvenanceEntry` variants, defaulting to `false` at creation, flipping
to `true` during Phase 1 concession processing.

**Driver:** The `type` field discriminates provenance tier (scouted vs.
not_scoutable) at `provenance-and-audit.md:103-106`. Concession is a
lifecycle event, not a classification. A scouted claim that is conceded
still has its full evidence chain; a not_scoutable claim that is
conceded still has its `ClassificationTrace`. Adding `type: "conceded"`
would conflate provenance depth with lifecycle status.

**Alternatives considered:**
- **Third `type` variant (`"conceded"`):** Would lose the provenance
  tier information — a consumer couldn't tell whether a conceded entry
  was originally scouted or not_scoutable without consulting external
  state. Rejected because it breaks the two-tier model at
  `provenance-and-audit.md:108-119` (T4-PR-04).
- **Optional field (present only when `true`):** Would mean consumers
  must handle two entry shapes (with and without the field). Rejected in
  favor of required field with default, which gives one shape for all
  entries.
- **Tombstone or null slots:** The contract at
  `provenance-and-audit.md:86-90` says "All allocated `claim_id`s
  persist in the index ... No sparse IDs, no gaps, no reordering."
  Tombstones would contradict the retention guarantee. Rejected.

**Implications:** `conceded: bool` is the first field that represents
lifecycle state (rather than provenance structure) on `ProvenanceEntry`.
Future lifecycle fields (if any) should follow the same orthogonal
pattern.

**Trade-offs accepted:** Every entry now carries a boolean that is
`false` for the majority of entries in most runs. Minimal overhead.

**Confidence:** High (E2) — verified the `type` field's semantic role
across `state-model.md:418-430`, `provenance-and-audit.md:103-106`, and
`provenance-and-audit.md:108-119`.

**Reversibility:** Low — the field is now in the external wire format
at version 1. Removing it would require a version bump and migration.

**What would change this decision:** If a future lifecycle event
(beyond concession) also needs to be represented on `ProvenanceEntry`,
the orthogonal-boolean pattern may not scale. At that point, a
structured `lifecycle_state` field might replace `conceded: bool`.

### Decision 4: Exclude conceded claims from the claim ledger

**Choice:** Conceded claims do not appear in the claim ledger. The
T4-PR-06 MUST clause applies to repository-facing factual claims, not
dialogue-state reporting about concessions.

**Driver:** `provenance-and-audit.md:155` says "No outcome tags. Facts
are facts, not dialogue events." Concession is a dialogue event. Adding
`[conceded]` annotations to the ledger would violate the existing
grammar.

**Alternatives considered:**
- **Include with `[conceded]` annotation:** Would violate "No outcome
  tags" at `provenance-and-audit.md:155`. Also, `FACT: X [conceded]
  [ref: N]` is semantically odd — the synthesis isn't asserting X as a
  fact. Rejected as dead on arrival under current grammar.
- **Include without annotation (bare `FACT:` line):** Would falsely
  assert conceded content as current fact. Rejected.

**Implications:** The T4-PR-06 scope clarification is category-based
(repository-facing vs. dialogue-state), not section-based. A
repository-facing factual claim embedded in a concession reporting
section still needs a ledger entry. The scope test is the content of
the assertion, not the section it appears in.

**Trade-offs accepted:** Breaks any expectation of 1:1 mapping between
provenance index entries and ledger lines. The contract never guaranteed
this mapping, and the audit at `:144` explicitly warned that "a harness
expecting one-to-one coverage between ledger and provenance index will
produce false positives."

**Confidence:** High (E2) — verified against the ledger grammar at
`provenance-and-audit.md:153-155` and the T4-PR-06 scope categories at
`provenance-and-audit.md:167-171`.

**Reversibility:** Medium — the scope clarification is a normative
statement in T4-PR-06. Reversing it would require reinstating the
universal MUST and defining a ledger grammar for conceded claims.

**What would change this decision:** If a future benchmark requirement
needs to track which claims were conceded (not just that concession
occurred), the ledger might need a concession surface. That would
require reopening the grammar.

### Decision 5: Option B landed as prose, not table column

**Choice:** Record the Option B ownership posture as a prose paragraph
below the blocker table in `benchmark-readiness.md`, not as a new
`Owner` column in the table.

**Driver:** Two reasons:
1. F11 is still a monolithic row. The T2 decision splits it into F11a
   (T4 normative) and F11b (T7 adoption), but the table hasn't been
   decomposed. An Owner column would require either a single cell for a
   split blocker or row decomposition — both premature.
2. The blocker table schema (Finding | Blocking surface | Exit condition)
   was just merged as PR #92's governance baseline. Changing the column
   structure in the very next packet weakens the baseline's stability.

**Alternatives considered:**
- **Owner column in the table:** Would provide at-a-glance ownership
  information. Rejected because F11's monolithic row can't cleanly
  receive a split owner, and the table schema is freshly established.
- **Separate ownership table:** Would duplicate information and create
  a synchronization burden. Rejected.

**Implications:** The prose records: F6/F7 → T4 contract surfaces as
post-closure amendments; F11 → split between T4 normative versioning
and T7 consumer adoption. When F11 is decomposed into separate rows,
the Owner column can be added.

**Trade-offs accepted:** Ownership is less discoverable in prose than
in a table column. Accepted because the table will evolve when F11 is
resolved.

**Confidence:** High (E2) — verified the table schema against PR #92's
original structure.

**Reversibility:** High — adding a column later is additive.

**What would change this decision:** F11 being decomposed into F11a/F11b
rows, at which point an Owner column becomes viable.

## Changes

### `state-model.md` (27 insertions, 4 deletions)

**Purpose:** Lock the internal lifecycle, coexistence, and serialization
semantics for concession in the provenance model.

**State before session:** `ProvenanceEntry` had two variants (scouted,
not_scoutable) with no concession field. The lifecycle table said
"Remove entry from `verification_state`" for concession — no mention of
the provenance index. The Concession Exception text said occurrences
remain in the registry but said nothing about the provenance entry's
fate.

**State after session:** Four edit points, all verified:

1. **Concession Exception (`:55-62`):** Added that the retained
   provenance entry at the conceded `claim_id` remains historical and
   flips `conceded` from `false` to `true`; no other provenance fields
   are removed or rewritten.

2. **Phase 1 processing (`:85-89`):** Added explicit lifecycle step:
   "In the same lifecycle event, set
   `claim_provenance_index[claim_id].conceded = true` on the retained
   provenance entry."

3. **claim_id allocation rule (`:342-344`):** Made coexistence explicit:
   after concession, the earlier `claim_id` remains a distinct historical
   join target with `conceded = true`; a reintroduced claim allocates a
   new `claim_id` and `ClaimRef` rather than reviving the old one.

4. **ProvenanceEntry schema (`:424-459`):** Added `conceded: bool` to
   both variants. Required on all entries, defaults to `false` at
   creation time, flips to `true` only during Phase 1. Concession does
   not change `type`, does not remove `claim_ref`, `record_indices`, or
   `classification_trace`. Updated serialization boundary note to say
   `conceded` serializes directly without changing tier semantics.

5. **Lifecycle table (`:396`):** Updated the `conceded` row: "Set
   retained provenance entry's `conceded=true`."

### `provenance-and-audit.md` (57 insertions, 25 deletions)

**Purpose:** Update the authoritative external contract surfaces for
F6(a), F6(b), F6(c), and the minimum versioning guardrail.

**State before session:** T4-PR-03 example showed two entry shapes with
no concession field. The canonical wire-format text had one parenthetical
about concession. T4-PR-06 had a universal MUST for ledger completeness.
The scoring interaction applied to all narrative-only claims. No version
metadata on `claim_provenance_index`.

**State after session:**

1. **T4-PR-03 example (`:69-82`):** Shows
   `claim_provenance_index_schema_version: 1` as a sibling pipeline-data
   field. Array entries show `conceded: false` (scouted), `conceded:
   true` (scouted), and `conceded: true` (not_scoutable).

2. **Canonical Wire Format (`:85-102`):** States `conceded: bool` is
   required on all entries, defaults to `false`, flips to `true` after
   Phase 1. Introduces
   `claim_provenance_index_schema_version` as a sibling pipeline-data
   field versioning the array contract. Version 1 includes the `conceded`
   field. Embedded `ClassificationTrace` inherits this version. Full
   bump-trigger policy deferred to F11.

3. **Claim Ledger Rules (`:165-170`):** Added policy: conceded claims
   do not gain a claim-ledger tag solely by virtue of concession status.
   Concession-history reporting is dialogue-state reporting, not a new
   ledger annotation class.

4. **T4-PR-06 (`:181-195`):** Added category-based scope clarification:
   ledger completeness MUST applies to repository-facing factual claims
   in the named benchmark categories, not dialogue-state reporting.
   A repository-facing claim requires a ledger entry regardless of
   which synthesis section contains it. Dialogue-state reporting about
   concessions, position shifts, or disagreement resolution does not
   require a ledger entry unless it also introduces a repository-facing
   factual claim.

5. **Scoring Interaction (`:199-213`):** Scoped to "narrative-only
   repository-facing factual claim in the categories above." Added:
   "Dialogue-state reporting alone does not create this finding class."

6. **Dedup Rule (`:223-224`):** Deliberate no-change: "Dialogue-state
   concession reporting does not create a competing ledger join and
   therefore does not change this rule."

7. **Mechanical Enforcement (`:228-236`):** Scoped to "repository-facing
   narrative facts in the categories above." Added: "Dialogue-state
   reporting alone is out of scope for this check."

### `boundaries.md` (7 insertions, 5 deletions)

**Purpose:** Declare the new pipeline-data surface and versioning
carrier.

**State before session:** T4-BD-01 listed `claim_provenance_index` as a
single new field. T4-BD-02 listed "two variants: scouted and
not_scoutable."

**State after session:**

1. **T4-BD-01 (`:18`):** Changed "New field" to "New fields" — lists
   both `claim_provenance_index_schema_version` and
   `claim_provenance_index`.

2. **T4-BD-02 (`:37`):** Updated ledger completeness change to say
   "Repository-facing factual narrative claims" and notes dialogue-state
   reporting is outside that category boundary.

3. **T4-BD-02 (`:38`):** Updated `claim_provenance_index` row to note
   "each carrying required `conceded: bool`."

4. **T4-BD-02 (`:39`):** New row for
   `claim_provenance_index_schema_version`: "Versions the
   `claim_provenance_index` array contract specifically. Initial value
   `1`; full bump-trigger policy remains under F11."

### `benchmark-readiness.md` (30 insertions, 9 deletions)

**Purpose:** Add resolved-row convention, mark F6 resolved, land
Option B, and tighten the T4-BR-07 cross-reference.

**State before session:** F6/F7/F11 all active in the blocker table.
Closing paragraph said "Ownership remains intentionally deferred here."
T4-BR-07 cross-reference said "until those blockers are resolved."

**State after session:**

1. **Resolved-row convention (`:115-118`):** Resolved findings remain
   in the table. The Finding cell gains `(resolved)`, and the Exit
   condition cell is replaced by `Resolved in ...` citations.

2. **F6 row (`:122`):** Marked `F6 (resolved)`. Exit condition replaced
   with citations: T4-SM-01, T4-SM-02, T4-SM-06, T4-SM-07, T4-PR-03,
   T4-PR-06.

3. **Option B prose (`:126-130`):** F6 and F7 target T4 contract
   surfaces as post-closure amendments. F11 remains split between T4
   normative versioning and T7 consumer adoption. Recorded as prose, not
   a table column, while the F11 row remains monolithic.

4. **Canonization gate (`:132-136`):** "For the remaining unresolved
   rows" scopes the MUST to F7 and F11. Canonization still gated on all
   exit conditions.

5. **T4-BR-07 cross-reference (`:165-170`):** Changed to "until all
   applicable blocker conditions in that subsection are satisfied" —
   matches the enforcement paragraph's "all applicable rows" language.

## Codebase Knowledge

### `benchmark-readiness.md` (282 lines, post-amendment)

| Section | Lines | State | Relevance |
|---|---|---|---|
| T4-BR-01: T5 Migration Surfaces | `:14-43` | Unchanged | |
| T4-BR-02: Transcript Fidelity | `:45-61` | Unchanged | |
| T4-BR-03: Allowed-Scope Safety | `:63-78` | Unchanged | |
| T4-BR-04: Provenance Index Consumer | `:79-91` | Unchanged | Now governed by blocker provisional-work rule |
| T4-BR-05: Synthesis-Format Contract Updates | `:92-103` | Unchanged | Now governed by blocker provisional-work rule |
| **F6/F7/F11 Blockers** | **`:104-136`** | **Modified** | Resolved-row convention, F6 resolved, Option B prose, scoped canonization gate |
| T4-BR-06: Narrative Factual-Claim Inventory | `:138-153` | Unchanged | |
| T4-BR-07: Benchmark-Execution Prerequisites | `:155-219` | **Modified** | Tightened cross-reference (`:165-170`) |
| T4-BR-08: Non-Scoring Run Classification | `:221-243` | Unchanged | Source of (a)/(b) classification |
| T4-BR-09: Benchmark-Contract Amendment | `:245-282` | Unchanged | |

### `provenance-and-audit.md` — key contract surfaces post-edit

| Section | Lines | State | F6/F7/F11 relevance |
|---|---|---|---|
| T4-PR-03: Claim Provenance Index | `:65-120` | **Modified** | F6(a)(b) exit condition satisfied. Version carrier established |
| T4-PR-04: Two Provenance Tiers | `:121-132` | Unchanged | `type` still discriminates tier only |
| T4-PR-05: Claim Ledger | `:133-177` | **Modified** | F6(c): conceded claims excluded, grammar unchanged |
| T4-PR-06: Narrative-to-Ledger | `:179-195` | **Modified** | Category-based scope clarification |
| Scoring Interaction | `:197-213` | **Modified** | Scoped to repository-facing claims |
| Dedup Rule | `:215-224` | **Modified** | Deliberate no-change with rationale |
| Mechanical Enforcement | `:226-236` | **Modified** | Scoped to repository-facing claims |

### `state-model.md` — lifecycle and schema surfaces

| Section | Lines | State | Relevance |
|---|---|---|---|
| T4-SM-01: Claim Occurrence Registry | `:13-66` | **Modified** | Concession Exception updated |
| T4-SM-02: Within-Turn Processing Order | `:68-134` | **Modified** | Phase 1 concession step |
| T4-SM-06: Verification State Model | `:307-462` | **Modified** | claim_id coexistence, ProvenanceEntry schema, lifecycle table, serialization boundary |

### Cross-reference map (F6 packet)

| Source | Target | Purpose |
|---|---|---|
| `state-model.md:85-89` (Phase 1) | `claim_provenance_index[claim_id]` | Write timing for `conceded = true` |
| `state-model.md:342-344` (claim_id) | Coexistence rule | Old conceded + new reintroduced are distinct |
| `state-model.md:424-459` (schema) | Both variants | `conceded: bool` required, defaults false |
| `provenance-and-audit.md:70` (example) | Version carrier | `claim_provenance_index_schema_version: 1` |
| `provenance-and-audit.md:95-102` (wire format) | Version carrier text | Scope, initial value, ClassificationTrace inheritance |
| `provenance-and-audit.md:187-192` (T4-PR-06) | Category boundary | Repository-facing vs. dialogue-state |
| `benchmark-readiness.md:122` (F6 row) | Resolution citations | T4-SM-01, T4-SM-02, T4-SM-06, T4-SM-07, T4-PR-03, T4-PR-06 |
| `benchmark-readiness.md:126-130` (Option B) | Ownership prose | F6/F7 → T4, F11 → split T4/T7 |
| `boundaries.md:38-39` (T4-BD-02) | Surface declarations | `conceded: bool` and version carrier |

## Context

### Mental model for this session

**Framing:** This session was about executing a coupled-constraint
resolution — landing a change to one blocker (F6) without silently
deepening the adjacent blocker defects (F7, F11). The key insight from
the user's rejection of my first analysis was that F6 is not a local
schema-shape question; it's a governance problem where the viable answer
space is determined by mechanical coupling between the internal state
model, the external wire format, and the unresolved versioning policy.

**Core insight:** When multiple blocker rows name the same contract
surface, solving one row in isolation is always suspect. The mechanical
serialization boundary at `state-model.md:437-442` means any internal
schema change IS an external change, which means the versioning blocker
(F11) constrains the schema blocker (F6) up front, not later.

**Secondary insight:** The difference between a correct analysis and a
useful one is framing. My first analysis read all the right sources and
produced structurally sound findings — but it solved the wrong problem
because the question was "what's the nicest schema?" instead of "what
change can land given the coupled constraints?" Good framing eliminates
dead options before analysis begins.

### The category-based scope boundary

The T4-PR-06 scope clarification is the most normatively significant
edit in the packet. It establishes that ledger completeness, scoring
interaction, and mechanical enforcement all use the same category test:
repository-facing factual claims (repository state, implementation
behavior, contract/spec requirements, code relationships) require ledger
entries; dialogue-state reporting (who conceded, when positions shifted,
how disagreements resolved) does not. This boundary is category-based,
not section-based — a repository-facing claim in the contested-claims
section still needs a ledger entry.

The four surfaces that were aligned:
1. T4-PR-06 MUST clause (`:181-192`)
2. Scoring interaction (`:199-213`)
3. Dedup rule (`:215-224`, deliberate no-change)
4. Mechanical enforcement (`:226-236`)

### Project state (post-session)

- **T4:** Closed at SY-13. F6 resolved as post-closure contract
  amendment. F7 still needs the serialization mechanism named. F11 still
  needs full versioning policy.
- **T5:** Designs accepted. `agent_local` ownership clarified in T6
  review.
- **T6:** Composition review shipped on main (PR #91). Administrative
  close still open.
- **F6:** Resolved (PR #93). `conceded: bool` on both `ProvenanceEntry`
  variants, category-based ledger boundary, version carrier established.
- **F7:** Active. Exit condition unchanged: name the emitting component,
  composition step, and interface.
- **F11:** Active. Version carrier exists
  (`claim_provenance_index_schema_version: 1`), but full bump-trigger
  policy and consumer expectations not yet defined.
- **T7:** Still blocked on F7/F11 for scored runs and calibration. May
  proceed with T4-BR-08(a) exploratory shakedowns.

### Environment

- Working directory: `/Users/jp/Projects/active/claude-code-tool-dev`
- Branch: `main`
- Main: `a78ddef1` (PR #93 merge commit)
- All delivery branches cleaned up
- `docs/t04-f6-f7-f11-ownership` still exists (unique handoff-history
  commits, keep/discard pending)

## Learnings

### When multiple blocker rows name the same contract surface, solving one row in isolation is always suspect

**Mechanism:** If blocker A modifies a surface that blocker B says is
unversioned, resolving A without addressing the versioning constraint
deepens B. The "boundary rule" from the prior session (record the
dependency but keep other blockers active) is correct governance — but
it's insufficient as a design constraint. The resolver must prove its
change is viable under the co-gating constraints, not just acknowledge
they exist.

**Evidence:** My first analysis acknowledged F7/F11 as dependencies but
treated them as follow-on concerns. The user's rejection identified that
`state-model.md:437-442` (mechanical serialization) makes F11 a
precondition, not a successor.

**Implication:** For any future blocker resolution, check whether
other active blockers name the same surface. If so, the resolver packet
must either prove its change doesn't touch the co-gated surface, or
include the minimum guardrail needed from the co-gating blocker.

**Watch for:** Resolver packets that claim blocker independence while
making schema changes to shared surfaces.

### A correct analysis that solves the wrong problem is still a failure

**Mechanism:** The first F6 analysis read all the right sources,
produced structurally sound findings, and was internally consistent. It
failed because it answered "what's the nicest concession schema?" instead
of "what F6 change can land without creating a new unversioned external
contract break?" Good framing eliminates dead options before analysis
begins; bad framing generates findings about options that were never
viable.

**Evidence:** The user's rejection identified three critical failures,
all of which stemmed from the wrong question rather than wrong facts.
The ledger annotation option was dead on arrival under
`provenance-and-audit.md:155`; I proposed evaluating it anyway. The
reintroduction coexistence problem at `state-model.md:390-391` was in
my read set; I still missed it because my framing didn't require
lifecycle completeness.

**Implication:** Before starting any analysis, state the governing
constraints as hard filters, then check whether proposed options survive
them. Options eliminated by hard constraints should be discarded before
analysis, not evaluated for elegance.

**Watch for:** Analysis that reads all the right sources but frames the
question as a local optimization rather than a constraint-satisfaction
problem.

### Category-based scope boundaries are more durable than section-based ones

**Mechanism:** A scope clarification that exempts "synthesis sections
like concessions, claim trajectory, or contested-claims summaries" is
section-based. A repository-facing factual claim embedded in those
sections would be incorrectly exempted. A scope clarification that
exempts "dialogue-state reporting" regardless of section is
category-based — the test is the content of the assertion, not its
location.

**Evidence:** The pre-implementation checklist review identified this
risk. The edit instruction originally said "not dialogue-state reporting
in synthesis sections like..." which could be read as section-based. The
user revised to make the category boundary explicit: "a repository-facing
factual claim in those categories requires a ledger entry regardless of
which synthesis section contains it."

**Implication:** When writing normative scope clarifications, test them
with an adversarial placement: "what if the exempted content appears in
a non-exempted location?" If the scope still works, it's category-based.
If it breaks, it's section-based and fragile.

**Watch for:** Scope language that names document sections rather than
content categories. Especially watch for "in sections like" or
"sections such as" phrasing.

### The clause-tightening pattern: rule → enforcement → closing paragraph alignment

**Mechanism:** When a normative subsection has a rule statement,
an enforcement hook, and a closing governance paragraph, all three must
use the same scope test. Mismatches create escape paths. The PR #92
clause fix and the T4-PR-06 scope alignment both followed this pattern:
identify the three clauses, verify they converge, and tighten the one
that diverges.

**Evidence:** PR #92's original closing paragraph had an "or assign"
disjunction that the rule and enforcement didn't share. T4-PR-06's
original scoring interaction applied to all narrative-only claims while
the rule applied only to repository-facing claims. Both were fixed by
aligning the divergent clause to the controlling standard.

**Implication:** After writing any normative gate with multiple access
points (rule, enforcement, governance), check all access points for the
same scope test. Three clauses that each look correct in isolation can
still conflict with each other.

**Watch for:** Closing paragraphs that summarize the rule with a softer
standard, enforcement paragraphs that add qualifiers not in the rule,
and governance paragraphs that use a different scope than the enforcement
actor can verify.

## Next Steps

### 1. Decide on `docs/t04-f6-f7-f11-ownership` branch

**Dependencies:** None.

**What to do:** The branch has 3 commits: 2 handoff-lifecycle commits
plus the original blocker amendment (`f9d4a8f8`). The amendment is
redundant with PR #92's cherry-pick (`92b23ac6`). The handoff commits
are lifecycle history. Decide: delete the branch (losing the handoff
commit history) or keep it as a historical record.

**Acceptance criteria:** Branch either deleted or explicitly kept with
documented reason.

### 2. Resolve F7 (serialization boundary)

**Dependencies:** None — can proceed independently of F11.

**What to read first:**
- `benchmark-readiness.md:123` (F7 blocker row and exit condition)
- `state-model.md:451-459` (serialization boundary note)
- `provenance-and-audit.md:95-102` (version carrier text)
- `2026-04-02-t04-t4-evidence-provenance-rev17-team.md:152-164` (F7 audit finding)

**F7 exit condition:** Canonical contract names the emitting component,
composition step, and interface that serialize `claim_provenance_index`
into synthesis output.

**Approach suggestion:** The audit recommends adding one explicit
sentence: "The agent serializes `claim_provenance_index` into
`<!-- pipeline-data -->` at layer 5 synthesis composition, after all
scouting rounds are complete." This may be sufficient, but the F6
experience shows that one-sentence fixes need to be verified against
all surfaces that reference the serialization boundary.

**Key constraint:** The serialization boundary at `state-model.md:451`
already says "mechanical — no information is added or removed." The F7
fix names WHO does the serialization and WHEN, not WHAT changes. This
should be a smaller packet than F6.

**Potential complication:** If naming the emitting component requires
specifying whether it's the agent, the synthesis assembler, or the
epilogue parser — these are different T7 components with different
trust boundaries.

### 3. Resolve F11 (versioning policy)

**Dependencies:** F7 should ideally be resolved first (the serialization
mechanism informs what a "version bump" means), but F11 can proceed
independently if the version carrier from F6 is treated as the baseline.

**What to read first:**
- `benchmark-readiness.md:124` (F11 blocker row and exit condition)
- `provenance-and-audit.md:95-102` (version carrier established by F6)
- `boundaries.md:39` (version carrier declaration)
- `2026-04-02-t04-t4-evidence-provenance-rev17-team.md:216-228` (F11 audit finding)

**F11 exit condition:** Canonical contract adds explicit versioning rules
for `claim_provenance_index` and `ClassificationTrace`, including version
fields, bump triggers, and consumer expectations.

**Key decisions needed:**
- Bump-trigger policy: what constitutes a version bump (new field, field
  removal, semantic change)?
- Consumer expectations: must consumers reject unknown versions? Accept
  with best-effort? The F11 audit says "safe against a design doc but
  not against deployed T7 consumers" — consumer behavior must be
  specified.
- F11a/F11b decomposition: the T2 decision splits F11 into T4 normative
  (versioning rule) and T7 consumer adoption. The blocker table row may
  need to be decomposed when this work starts.
- Whether `ClassificationTrace` needs its own standalone version field
  or inherits from the containing `claim_provenance_index` entry (the
  F6 packet established inheritance, but the F11 resolver may decide
  otherwise).

### 4. Clean up stale branches after F7/F11

**Dependencies:** After F7 and/or F11 PRs merge.

**What to do:** The branch list should be reviewed after each merge.
`feature/codex-collaboration-r2-dialogue` was flagged as unrelated and
out of scope for this thread, but it has a long stack of unique commits
with its upstream gone — worth a separate decision.

## In Progress

**Clean stopping point.** PR #93 merged. F6 resolved. Branch cleanup
done (three merged branches deleted). Local main at `a78ddef1`.

No work in flight. The `docs/t04-f6-f7-f11-ownership` branch keep/discard
decision is the only open bookkeeping item.

## Open Questions

1. **Should `docs/t04-f6-f7-f11-ownership` branch be kept or deleted?**
   It carries two unique handoff-history commits not on main, plus the
   redundant original blocker amendment. The handoff content itself is
   archived in `docs/handoffs/archive/`. The branch is historical only.

2. **Does T6 close administratively?** Same open question from prior
   sessions. The committed T6 review preserved "DOES NOT YET COMPOSE"
   without settling whether T6 itself is closable.

3. **Should F7 and F11 be resolved sequentially or in parallel?** F7
   is likely a smaller packet. F11 may benefit from knowing the
   serialization mechanism (F7) but doesn't strictly depend on it.

4. **Should the evidence-trajectory consumer projection orphan be
   addressed?** Still unassigned per `docs/reviews/2026-04-04-t04-t6-benchmark-first-design-composition-review.md:182-185`.
   Parked unless a future packet pulls it forward.

## Risks

1. **The version carrier has incomplete policy.** Version 1 exists but
   bump triggers and consumer expectations are unspecified. A consumer
   implemented between now and the F11 resolver packet would need to
   tolerate this ambiguity. Mitigation: no consumers exist yet (T7
   hasn't built anything), and F11 is the designated owner of the full
   policy.

2. **The F6 packet added a required field to an external wire format.**
   `conceded: bool` is now on every `ProvenanceEntry` in the pipeline-
   data surface. Any pre-version-1 pipeline-data (if it existed) would
   lack this field. Mitigation: no pipeline-data consumers exist yet,
   and the version carrier enables future consumers to detect the schema
   shape.

3. **The category-based scope boundary depends on the adjudicator
   correctly classifying dialogue-state vs. repository-facing claims.**
   The boundary is normative in T4-PR-06 but the actual classification
   is a T7 adjudicator judgment. If the adjudicator misclassifies
   concession-history reporting as repository-facing, false
   `narrative_ledger_violation` findings result. Mitigation: the
   category definition is explicit (four named categories at
   `provenance-and-audit.md:182-184`), and concession reporting doesn't
   fit any of them.

4. **Post-closure amendment framing may not survive larger resolver
   packets.** F6 was a targeted amendment (84 insertions across 4 files).
   If F7 or F11 require restructuring rather than amending, the
   "post-closure amendment" framing starts resembling T4 phase reopening.
   Same risk as prior session, carried forward.

## References

| What | Where |
|---|---|
| PR #93 (F6 resolver, merged) | https://github.com/jpsweeney97/claude-code-tool-dev/pull/93 |
| PR #92 (blocker framework, merged) | https://github.com/jpsweeney97/claude-code-tool-dev/pull/92 |
| F6 commit | `1453665d docs(plans): resolve F6 concession lifecycle contract` |
| Clause tightening commit | `758901a3 docs(plans): tighten blocker canonization gate` |
| Merge commit (PR #93) | `a78ddef1` |
| Merge commit (PR #92) | `20c6b338` |
| F6 resolved row | `benchmark-readiness.md:122` |
| Option B prose | `benchmark-readiness.md:126-130` |
| Resolved-row convention | `benchmark-readiness.md:115-118` |
| T4-BR-07 tightened cross-ref | `benchmark-readiness.md:165-170` |
| ProvenanceEntry schema (with conceded) | `state-model.md:424-459` |
| Phase 1 concession step | `state-model.md:85-89` |
| Lifecycle table (conceded row) | `state-model.md:396` |
| claim_id coexistence rule | `state-model.md:342-344` |
| Concession Exception (updated) | `state-model.md:55-62` |
| Version carrier | `provenance-and-audit.md:95-102` |
| T4-PR-03 example (with conceded) | `provenance-and-audit.md:69-82` |
| T4-PR-06 scope clarification | `provenance-and-audit.md:187-192` |
| Scoring interaction (scoped) | `provenance-and-audit.md:202-213` |
| Dedup rule (deliberate no-change) | `provenance-and-audit.md:223-224` |
| Mechanical enforcement (scoped) | `provenance-and-audit.md:228-236` |
| Ledger rules (concession policy) | `provenance-and-audit.md:168-170` |
| Boundaries version carrier | `boundaries.md:18, :39` |
| F6 audit finding | `2026-04-02-t04-t4-evidence-provenance-rev17-team.md:133-148` |
| F7 audit finding | Same file, `:152-164` |
| F11 audit finding | Same file, `:216-228` |
| T6 review disposition | `docs/reviews/2026-04-04-t04-t6-benchmark-first-design-composition-review.md:173-195` |

## Gotchas

1. **The version carrier is a sibling field, not a wrapper.** The
   pipeline-data surface has `claim_provenance_index_schema_version: 1`
   alongside `claim_provenance_index: [...]`, not a wrapping object like
   `{ version: 1, data: [...] }`. If the F11 resolver decides a wrapper
   is needed, that's a migration from the current shape. The F6 packet's
   stop condition explicitly warned against this.

2. **`conceded: bool` is required on ALL entries, including non-conceded
   ones.** Every entry carries `conceded: false` unless conceded. This is
   a deliberate consumer-simplicity choice: one shape, always present.
   Don't assume the field is optional or present only when true.

3. **The T4-PR-06 scope boundary is category-based, not section-based.**
   "Repository-facing factual claims in the named benchmark categories"
   is the scope. A repository fact in the contested-claims section still
   needs a ledger entry. Don't exempt by section.

4. **F6 (resolved) stays in the blocker table.** The resolved-row
   convention keeps resolved findings visible with `(resolved)` in the
   Finding cell and citations in the Exit condition cell. Don't remove
   the row — it's the governance record of what was resolved and where.

5. **The closing paragraph now scopes to "remaining unresolved rows."**
   `benchmark-readiness.md:132` says "For the remaining unresolved
   rows..." — the canonization MUST only applies to F7 and F11 now that
   F6 is resolved. Don't re-read it as applying to all rows.

6. **`docs/t04-f6-f7-f11-ownership` is NOT merged to main.** It carries
   the original blocker amendment (`f9d4a8f8`) plus two handoff commits.
   The amendment is redundant with PR #92's cherry-pick. Don't continue
   work on this branch — it's historical.

7. **The T4-BR-07 cross-reference was tightened.** The phrasing changed
   from "until those blockers are resolved" to "until all applicable
   blocker conditions in that subsection are satisfied." This matches the
   enforcement paragraph's "all applicable rows" language. Don't revert
   to the looser phrasing.

8. **User applies every flagged item regardless of severity (five
   sessions now).** Every finding from scrutiny, plan review, and
   implementation review was addressed. The test for whether to flag
   something: "would I apply this in my own work?"

## Conversation Highlights

### User's rejection of the first F6 analysis

User delivered a structured adversarial review with three critical
failures, four high-risk assumptions, three real-world breakpoints, three
hidden dependencies, and three adversarial perspectives. Key framing:

*"This is not yet solving the right problem. The target treats F6 as a
mostly local schema-design question, but F6 is coupled to two external
governance constraints the analysis does not treat as gating."*

*"The real question is not 'what is the nicest representation for
concession state?' The real question is 'what F6 change can be landed
without creating an unversioned external schema mutation or leaving the
blocker row only cosmetically resolved?'"*

### User's corrected analysis

User delivered the complete corrected analysis from the coupled-constraint
premise, including hard constraints, dead options, viable packet shape,
required contract edits, versioning constraint, and acceptance criteria.
This was not a sketch — it was a fully formed pre-implementation design
that passed scrutiny with minor revision.

### User's pre-implementation checklist

Delivered as a complete checklist with exact edit points (file:line),
dependency-ordered sequence, blocker-clearance tests with pass/fail
criteria, and stop conditions. Each edit point specified what to change
and what NOT to change.

### User's implementation verification

User applied all scrutiny findings from both the checklist review and the
implementation review, committed, and verified before requesting merge.
Response contract format used throughout: "What changed / Why it changed
/ Verification performed / Remaining risks."

### User's merge-first-then-prune recommendation

*"Recommendation: merge PR #93 first, then do a narrow safe branch
cleanup. ... Short version: push the workstream forward before doing
repo tidying. #93 changes project state; branch pruning mostly changes
clutter."*

## User Preferences

**Writes substantive content themselves (five sessions now):** User
drafted the corrected analysis, the pre-implementation checklist, and
executed the implementation. My role: scrutinize, surface findings, apply
minor edits per accepted text. Do not draft substantive normative content
unless explicitly asked.

**Treats every flagged item as actionable (100% apply rate — five
sessions now):** Every finding from scrutiny, plan review, checklist
review, and implementation review was addressed. The test for flagging:
"would I apply this in my own work?"

**Drives tightening iteratively:** The PR #92 clause fix, the three
scrutiny rounds (analysis → checklist → implementation), and the two
post-implementation fixes all followed the same pattern: user reviews
current state, identifies a normative precision gap, directs the fix.

**Expects adversarial-quality scrutiny with specific evidence:** The
user's own rejection of my first analysis used structured adversarial
review format with severity ratings, evidence citations, and specific
remediation language. The scrutiny quality I deliver should match what
the user delivers.

**Prefers clear separation between governance and implementation:** The
prior session published PR #92 as a governance baseline before starting
resolver work. This session's user recommendation explicitly said
"merge PR #93 first, then do repo tidying" — move the workstream forward
before bookkeeping.

**Uses consistent Response Contract format:** "What changed / Why it
changed / Verification performed / Remaining risks" — used for every
status update.

**Decision style: recommendations-first with structured trade-off
analysis:** Every proposal came with pre-staged options, per-option
rationale with citations, and rejection of alternatives with specific
reasons. Expects the same structure back during scrutiny.

**Cherry-pick over mixed-commit PRs (established in prior session):**
User used the same pattern this session — clean single-purpose branches
for governance PRs. The safety-branch-then-reset sequence was user-
executed to keep PR #92's commit history clean.
