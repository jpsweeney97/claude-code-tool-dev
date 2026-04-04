---
date: 2026-04-03
time: "13:36"
created_at: "2026-04-03T17:36:57Z"
session_id: 358bd4cb-07a1-454a-a320-e85b2a0ba655
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-04-03_06-24_t04-t4-rev21-proof-surface-and-g3-acceptance.md
project: claude-code-tool-dev
branch: docs/t04-t4-scouting-and-evidence-provenance
commit: 86a81773
title: T-04 T4 modular spec compilation — 59 requirement IDs, topology validated
type: handoff
files:
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/spec.yaml
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/README.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/foundations.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/state-model.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/scouting-behavior.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/containment.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/provenance-and-audit.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/benchmark-readiness.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/boundaries.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/rejected-alternatives.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/conformance-matrix.md
  - docs/plans/t04-t4-scouting-position-and-evidence-provenance/crosswalk.md
  - docs/plans/archive/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md
  - docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md
---

# Handoff: T-04 T4 modular spec compilation — 59 requirement IDs, topology validated

## Goal

Compile the 2441-line monolithic T4 design contract (revision 21, "Defensible" verdict
after 6 hostile review rounds) into a modular spec with explicit authority boundaries,
stable requirement IDs, and cross-file linking.

**Trigger:** Prior session achieved T4 rev 21 acceptance and G3 gate closure. The handoff
proposed three next steps: T6 composition check, T7 conceptual-query corpus design, and
modular split. User chose modularization first: "We should prioritize modularizing T4 first
— use /spec-writer."

**Stakes:** The monolith path (`docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-
provenance.md`) is referenced by tracked artifacts — T7 ticket, audit reports, handoffs,
and review materials. Any modular split must preserve referential integrity for those
consumers while enabling navigable, authority-bounded maintenance going forward.

**Success criteria:**
- Every normative clause lives in exactly one canonical location
- Stable requirement IDs (`T4-{prefix}-{seq}`) with explicit HTML anchors
- Authority model formalized in `spec.yaml`
- Original monolith archived, compatibility shim at old path
- Zero unresolved link targets across the modular spec

**Connection to project arc:** T4 is one of seven benchmark-first design tracks (T1-T7).
The monolith reached "Defensible" at rev 21. Modularization makes T4 maintainable for T7
integration (conceptual-query corpus, methodology findings, benchmark amendments) without
reopening the 2441-line monolith.

## Session Narrative

Loaded the prior handoff documenting T4 rev 21's "Defensible" verdict and G3 acceptance.
The handoff proposed three next steps. User immediately chose modularization using the
spec-writer skill, which provides an 8-phase workflow: Entry Gate, Analysis, Architecture
Checkpoint, Manifest, Scaffold, Author, Validate, Handoff.

### Architecture review rounds (three adversarial passes)

**Round 1:** Proposed architecture with 8 authorities, precedence hierarchy, and verification
as a peer authority. User identified 6 findings including 3 P1s:

- P1: Split-brain authority — keeping monolith as "frozen source" alongside live modules
  guarantees drift. User: "If the monolith stays 'source' while the modules become the
  readable surface, drift is guaranteed unless one is mechanically derived from the other."
- P1: Wrong precedence model — `claim_precedence` hierarchy means when mirrored normative
  surfaces disagree, one silently wins. User: "When mirrored normative surfaces disagree,
  the right outcome is a blocking ambiguity finding, not 'foundation wins' or 'behavior
  wins.'"
- P1: No citation model — no stable requirement IDs, so navigability improves while
  auditability gets worse. User: "Without requirement IDs and explicit back-links,
  navigability improves while auditability gets worse."

**Round 2:** Revised architecture with contradiction policy, requirement IDs, and conformance
matrix. User found 4 findings including 1 P1:

- P1: `claim-classification.md` as half-owned separate file with CL prefix but no authority
  in spec.yaml, no boundary rules. User: "That is not cosmetic because §4.7 drives
  load-bearing semantics." Fixed by folding classification back into scouting-behavior.md
  with SB prefix.
- P2: No foundation boundary rule. User: "Transcript fidelity directly constrains
  provenance, containment, and readiness. A change there should not be able to bypass
  review."
- P2: Historical line-number citations from handoffs not preserved — added crosswalk.
- P2: Archive breadcrumb breaks existing references — added compatibility shim.

**Round 3:** User approved: "No blocking architectural findings." Three residual risks
noted (governance metadata without enforcement, shim must be unmistakably non-normative,
migration must land atomically).

### Writing and midpoint checkpoint

Wrote manifest (`spec.yaml`), scaffold (`README.md`), then the normative backbone in
dependency order: foundations → provenance-and-audit → benchmark-readiness. User reviewed
the midpoint checkpoint and found 3 findings:

- P1: Standard Markdown heading slugs generate `#t4-pr-11-mechanical-omission-diff`, not
  `#t4-pr-11`. Fixed by adding 36 explicit `<a id="t4-xx-yy"></a>` HTML anchors.
- P2: README and foundations pointed to nonexistent archive path (archive not yet created).
- P3: "Graduated readiness" attributed to rev 20 but belongs in rev 21.

After fixes, user approved continuation: "The next meaningful review point is after the
remaining six content files are written and the migration surfaces land together."

### Remaining files and whole-contract review

Wrote: state-model, scouting-behavior, containment, boundaries, rejected-alternatives,
conformance-matrix, crosswalk, compatibility shim. Archived monolith.

User conducted whole-contract integrity review using a local link/fragment validator. Found
4 findings:

- P1: 50 missing file targets — repo-relative paths inherited from monolith were one
  directory too shallow after the move into `docs/plans/t04-t4-.../`
- P1: 12 missing fragments — cross-module links used descriptive slugs (`#claim-class-scope`)
  instead of requirement ID anchors (`#t4-sb-05`)
- P2: Crosswalk source link pointed to compatibility shim instead of archived monolith
- P2: `claim_provenance_index` defined with two shapes (internal dict vs wire format array)
  without explicit serialization boundary

Fixed all four. Path fixes: `../../packages/` → `../../../packages/` in 6 files,
`../superpowers/` → `../../superpowers/` in 5 files, T3 sibling reference, crosswalk source
link. Fragment fixes: 5 descriptive slug patterns replaced with requirement ID anchors across
3 files (12 total replacements). Added serialization boundary note in `state-model.md`.

User revalidated: "0 unresolved targets." Committed atomically at `86a81773` — 14 files,
5130 insertions, 2441 deletions.

### Topology challenge

User asked: "Is frontmatter bloat masking if modules actually talk?" Then: "Foundations
touching everything — classic star topology mess." Analysis showed foundations is 5th of 7
in link participation (23 links, 10%). Provenance is the actual hub (66 links, 29%). Non-
foundation modules route the majority of outbound links to peers — containment and boundaries
send 100% to non-foundation targets. The link graph is a mesh with provenance as the hub,
not a star with foundations at the center.

## Decisions

### Empty precedence model (all normative conflicts → ambiguity_finding)

**Choice:** `claim_precedence: {}`, `fallback_authority_order: []`, `unresolved: ambiguity_finding`
in `spec.yaml`. No authority wins over another.

**Driver:** User identified that T4's mirrored normative surfaces (e.g., prerequisite block
in benchmark-readiness ↔ checklist item 70 in conformance matrix) must agree, and disagreement
is always a defect. "When mirrored normative surfaces disagree, the right outcome is a blocking
ambiguity finding."

**Rejected:**
- Precedence hierarchy (`foundation > state-model > ...`) — silently resolves conflicts by
  letting one authority win, masking spec defects that should be caught and fixed.

**Trade-offs:** No automatic resolution means every apparent conflict requires manual investigation.
Accepted because the spec should have zero normative conflicts — each clause lives in exactly one
canonical location.

**Confidence:** High (E2) — mirrored surfaces were a known drift problem in the monolith (rev 21
spent review rounds fixing this exact failure mode).

**Reversibility:** High — changing `spec.yaml` precedence rules requires no content changes.

**Change trigger:** If the spec grows large enough that ambiguity findings become frequent and
resolution becomes a bottleneck, a limited precedence hierarchy could be justified.

### Conformance matrix as non-normative (cites IDs, does not define)

**Choice:** The 70-item verification checklist is recast as a non-normative conformance matrix
under `authority: supporting` that cites canonical requirement IDs rather than being a peer
normative authority.

**Driver:** User identified that giving verification its own strategy authority invites authors
to write or reinterpret requirements there. "Giving 'verification' its own strategy authority
invites authors to write or reinterpret requirements there." The monolith's checklist mirrors
were drift-prone (rev 21 review rounds spent fixing this).

**Rejected:**
- Verification as normative peer authority with its own claims — creates a second normative
  surface for the same requirements, recreating the drift problem the modular split was
  supposed to eliminate.

**Trade-offs:** The conformance matrix cites 48 distinct requirement IDs across all 7 prefixes
but uses plain text, not clickable links. It's the densest cross-reference surface in the spec
yet the least navigable.

**Confidence:** High (E2) — mirrors the failure mode already observed in the monolith.

**Reversibility:** Medium — promoting to normative would require adding an authority, claims,
and boundary rules in spec.yaml plus reviewing all 70 items for normative language.

**Change trigger:** If a reviewer discovers the matrix has drifted from the canonical requirements
it cites, that would validate the design (the drift would be caught as a matrix bug, not a
normative conflict).

### Compatibility shim at original monolith path

**Choice:** Replace the original monolith file with a non-normative compatibility shim (31 lines)
that redirects to the modular spec, archived monolith, and crosswalk.

**Driver:** The T4 monolith path is referenced by tracked artifacts — T7 ticket, audit reports,
handoffs, review materials. Deleting the file would break those references. User required
atomic migration: "the migration must land atomically."

**Rejected:**
- Keeping the monolith alongside modules (split-brain, guaranteed drift)
- Deleting the monolith (breaks existing references)
- Symlink to modular README (filesystem-dependent, not portable)

**Trade-offs:** The shim is one more file to maintain, though its content is intentionally
trivial and marked "Do not edit this file."

**Confidence:** High (E2) — referencing artifacts verified as tracked.

**Reversibility:** High — shim can be deleted once all references are updated, or replaced with
a redirect.

**Change trigger:** If all referencing artifacts are updated to point to the modular directory,
the shim becomes unnecessary.

### Serialization boundary for claim_provenance_index

**Choice:** Added explicit note in `state-model.md` T4-SM-07 distinguishing `dict[int,
ProvenanceEntry]` (internal working state) from the dense JSON array wire format (T4-PR-03).

**Driver:** User finding P2: "the same term names both surfaces without an explicit serialization
boundary, so implementers and validators can reasonably read the contract two different ways."

**Rejected:**
- Leaving the ambiguity (inherited from monolith) — two valid interpretations for implementers.

**Trade-offs:** Adds 4 lines to state-model.md. No semantic change — the two representations
are isomorphic.

**Confidence:** High (E2) — the ambiguity existed in the monolith and was flagged independently
by the user's review.

**Reversibility:** High — clarification note, no structural change.

**Change trigger:** None — this corrects an ambiguity, not a preference.

## Changes

### Modular spec directory (`docs/plans/t04-t4-scouting-position-and-evidence-provenance/`)

14 files total. 11 .md + 1 .yaml in the modular directory, 1 archived monolith, 1 compatibility
shim. Committed atomically at `86a81773`.

| File | Authority | Lines | Requirement IDs | Purpose |
|------|-----------|-------|-----------------|---------|
| `spec.yaml` | — | 74 | — | Machine source of truth: 8 authorities, empty precedence, 6 boundary rules |
| `README.md` | supporting | 83 | — | Entry point: authority model, 10-item reading order, cross-ref conventions |
| `foundations.md` | foundation | 322 | T4-F-01–T4-F-13 | Core decisions (12 locked), rationale, transcript fidelity dependency |
| `state-model.md` | state-model | 547 | T4-SM-01–T4-SM-10 | Schemas (7), two-phase processing, verification lifecycle, budgets |
| `scouting-behavior.md` | scouting-behavior | 335 | T4-SB-01–T4-SB-05 | Loop mechanics, targeting, query coverage, claim classification |
| `containment.md` | containment | 148 | T4-CT-01–T4-CT-05 | Scope confinement, scope_root derivation, safety interaction |
| `provenance-and-audit.md` | provenance | 414 | T4-PR-01–T4-PR-14 | Citation surface, provenance index, claim ledger, omission diff |
| `benchmark-readiness.md` | benchmark-readiness | 231 | T4-BR-01–T4-BR-09 | Blockers, 8-item prerequisite gate, 10 amendment rows |
| `boundaries.md` | boundaries | 58 | T4-BD-01–T4-BD-03 | Non-changes, declared input changes, helper-era migration |
| `rejected-alternatives.md` | supporting | 267 | — | Entries 7.1–7.61 with cross-refs to canonical IDs |
| `conformance-matrix.md` | supporting | 89 | — | 70-item verification, cites IDs (plain text, not linked) |
| `crosswalk.md` | supporting | 90 | — | Monolith section/line → modular file/ID mapping |

### Archived monolith (`docs/plans/archive/`)

`2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` — immutable 2441-line copy
of revision 21. Referenced by crosswalk for historical line-range resolution.

### Compatibility shim (`docs/plans/`)

`2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` — 31-line non-normative
redirect with block quote "Do not edit this file." Links to modular root, archived snapshot,
and crosswalk. Quick navigation table linking all modular files.

## Codebase Knowledge

### Authority model

8 authorities defined in `spec.yaml:8-52`. No precedence hierarchy — all normative conflicts
escalate to `ambiguity_finding`. 6 boundary rules define review triggers (e.g., change to
foundation requires review of provenance, containment, benchmark-readiness).

### Requirement ID scheme

Format: `T4-{prefix}-{seq}`. 59 IDs total across 7 normative prefixes:

| Prefix | Authority | Count |
|--------|-----------|-------|
| T4-F | foundation | 13 |
| T4-SM | state-model | 10 |
| T4-SB | scouting-behavior | 5 |
| T4-CT | containment | 5 |
| T4-PR | provenance | 14 |
| T4-BR | benchmark-readiness | 9 |
| T4-BD | boundaries | 3 |

Each ID has an explicit `<a id="t4-xx-yy"></a>` HTML anchor before the heading. Cross-file
links use `[T4-CT-03](containment.md#t4-ct-03)` — ID-based, not section-number-based.

### Link topology (validated)

Provenance is the hub, not foundations. Measured at commit `86a81773`:

| Module | Out | In | Total | % |
|--------|----:|---:|------:|--:|
| provenance-and-audit | 17 | 49 | 66 | 29% |
| state-model | 16 | 24 | 40 | 17% |
| benchmark-readiness | 9 | 30 | 39 | 17% |
| scouting-behavior | 9 | 27 | 36 | 16% |
| foundations | 12 | 11 | 23 | 10% |
| boundaries | 13 | 1 | 14 | 6% |
| containment | 7 | 4 | 11 | 5% |

Non-foundation modules route the majority of outbound links to peers. Containment and
boundaries send 100% of outbound links to non-foundation targets.

### Cross-reference surfaces

Three cross-reference surfaces serve different audiences:
1. **Conformance matrix** — 70-item verification checklist citing 48 distinct requirement IDs
   across all 7 prefixes. Plain text references (not clickable links). Densest cross-reference
   surface, least navigable.
2. **Crosswalk** — section-level (30 rows) and frequently-referenced line-range (17 rows)
   mapping from monolith to modular locations. For historical reference resolution.
3. **Compatibility shim** — quick navigation table for consumers of the old monolith path.

### Relative path structure

From files at `docs/plans/t04-t4-scouting-position-and-evidence-provenance/`:
- `../` → `docs/plans/` (sibling plan files, compatibility shim)
- `../../` → `docs/` (reviews at `docs/reviews/`, superpowers at `docs/superpowers/`)
- `../../../` → project root (packages at `packages/plugins/cross-model/`)

The path depth was a session-long bug class. Monolith-relative paths inherited during
compilation were one `../` too shallow. All 62 broken targets (50 files + 12 fragments)
fixed before commit.

## Context

### What this spec represents

T4 is the scouting and evidence provenance contract for the dialogue-supersession benchmark.
It defines: how the agent scouts claims (query types, attempt limits, containment), how
evidence is structured and compressed, how provenance connects scouted evidence to scored
synthesis claims, and what benchmark prerequisites must land before scored runs proceed.

The monolith went through 21 revisions and 6 hostile review rounds reaching "Defensible"
verdict. The modular split preserves all normative content at revision 21 fidelity — the
spec-writer skill's transformation rule prohibits inventing new decisions or silently
resolving ambiguities.

### Mental model

This is a **compiler task, not a design task**. The design space was already closed (rev 21
accepted). The job was faithful decomposition along authority boundaries — splitting the
monolith into files where each normative clause lives in exactly one canonical location,
connected by stable requirement IDs.

The user treated the architecture review as adversarial review of the compiler's output:
testing whether the decomposition introduced new failure modes (split-brain authority, star
topology, drift-prone mirrors) rather than reviewing the T4 design decisions themselves.

### Spec-writer skill context

The spec-writer skill (`packages/plugins/superspec/skills/spec-writer/SKILL.md`) provides
the 8-phase compilation workflow. Key constraint: the shared contract at
`packages/plugins/superspec/references/shared-contract.md` defines the Claims Enum (8 fixed
values), spec.yaml schema, and the Producer Failure Model (hard failures that block handoff).

The skill has one mandatory approval gate (Phase 3: Architecture Checkpoint) and one optional
midpoint gate (Phase 6, for large docs). This session used both: user conducted three
adversarial review rounds at the architecture checkpoint and one at the midpoint.

## Learnings

### Modular split introduces a systematic path-depth bug class

When compiling a monolith into a subdirectory, every repo-relative link inherited from the
source is one `../` too shallow. This session found 62 broken targets (50 files + 12
fragments). The fix pattern is mechanical: `../../X` → `../../../X` for project-root targets,
`../X` → `../../X` for doc-sibling targets. A post-compilation link validator is essential —
the broken links are invisible during authoring because the content looks correct.

### Descriptive heading slugs don't survive the modular split

Standard Markdown heading slugs (e.g., `#verification-state-model`) are fragile across
file reorganization. Explicit HTML anchors (`<a id="t4-sm-06">`) create stable, short IDs
that survive heading renames and section moves. 36 anchors were needed across the T4 spec.
This was caught at the midpoint checkpoint — the initial implementation used standard slugs.

### Adversarial architecture review catches structural failures that self-review misses

Three rounds of user review produced fundamentally different spec architecture than the initial
proposal. Key shifts: precedence hierarchy → contradiction policy, verification as peer
authority → non-normative conformance matrix, classification as separate file → folded into
scouting-behavior. Each was a structural failure mode (drift, reinterpretation, half-ownership)
that the spec-writer skill's analysis phase did not detect because the analysis derives
structure from content, not from failure mode analysis.

## Conversation Highlights

**Modularization priority:**
User: "We should prioritize modularizing T4 first — use /spec-writer"
— Cut the decision space immediately. No discussion of T6 or T7 first.

**Precedence model rejection:**
User: "When mirrored normative surfaces disagree, the right outcome is a blocking ambiguity
finding, not 'foundation wins' or 'behavior wins.'"
— Drove the empty-precedence decision that defines the spec's contradiction policy.

**Verification authority rejection:**
User: "Giving 'verification' its own strategy authority invites authors to write or reinterpret
requirements there."
— Drove the conformance matrix recast from normative to supporting.

**Classification half-ownership:**
User: "That is not cosmetic because §4.7 drives load-bearing semantics."
— Drove folding claim-classification back into scouting-behavior.

**Topology challenge:**
User: "Is frontmatter bloat masking if modules actually talk?"
Then: "Foundations touching everything — classic star topology mess"
— Prompted quantitative link analysis showing provenance as the actual hub (29%) vs
foundations (10%). User's framing was factually wrong but the challenge was productive —
it forced validation of the coupling topology.

**Review style observed:** The user conducts adversarial architectural review with numbered
priorities (P1/P2/P3), explicit verdicts ("Revise", "Approve"), and stated assumptions.
Corrections are specific ("What I Would Change Before Writing" with 6 concrete items).
Reviews conclude with explicit scope: "Once the broken links are fixed, I will re-review."

## User Preferences

**Review-then-approve workflow:** User reviews output at each gate with explicit P1/P2/P3
findings and verdicts. Does not accept "looks good" — validates claims independently
(ran a local link/fragment validator).

**Direct review over automation:** When offered spec-review-team automation, user said
"I will review directly first." Prefers first-person validation before delegating to agents.

**Adversarial framing:** Tests proposed architectures for failure modes, not just correctness.
Questions like "Is frontmatter bloat masking if modules actually talk?" and "Foundations
touching everything — classic star topology mess" are probes, not complaints.

**Atomic landing:** Required all files to commit together: "the migration must land atomically."
No intermediate state where the monolith is gone but replacement surfaces are missing.

## Next Steps

### 1. Run spec-review-team on the modular T4 spec

**Dependencies:** Commit `86a81773` on branch `docs/t04-t4-scouting-and-evidence-provenance`.

**What to read first:** `docs/plans/t04-t4-scouting-position-and-evidence-provenance/README.md`
(reading order and authority model summary).

**Approach:** The spec-review-team is a superspec plugin agent team that reviews modular specs.
User explicitly stated: "Next session we will run a spec-review-team."

**Acceptance criteria:** Review team findings triaged and addressed. Spec ready for merge to
main or further iteration based on findings.

**Potential obstacles:** The conformance matrix uses plain-text ID references (not clickable
links) — a review agent may flag this. The user already knows (raised during topology
discussion). The residual risk the user noted: "spec.yaml, conformance-matrix.md, and
crosswalk.md are still procedural governance surfaces rather than mechanically enforced ones."

### 2. Merge to main (after review)

**Dependencies:** Spec-review-team findings addressed.

**Approach:** Standard PR from `docs/t04-t4-scouting-and-evidence-provenance` → `main`.

## In Progress

Clean stopping point — modular spec compiled, all link targets validated, committed
atomically. No work in flight.

## Open Questions

1. **Should the conformance matrix use clickable links?** Currently cites 48 requirement IDs
   as plain text. The matrix is non-normative and functions as a lookup table, but clickable
   links would improve navigability. Not blocking — flagged for review team consideration.

2. **Governance enforcement.** User noted spec.yaml, conformance-matrix, and crosswalk are
   "procedural governance surfaces rather than mechanically enforced ones." Whether to add
   mechanical enforcement (e.g., CI validation of link resolution, conformance matrix
   consistency checks) is a separate decision.

## Risks

1. **Conformance matrix drift.** The matrix cites canonical requirement IDs but is non-normative.
   If a requirement changes, the matrix entry may become stale. Mitigation: the matrix explicitly
   states "the cited requirements are authoritative; this matrix is a strict reference that does
   NOT define, reinterpret, or extend requirements." Stale entries are matrix bugs, not
   normative conflicts.

2. **Crosswalk staleness.** The crosswalk maps monolith line ranges to modular locations. If
   modular files are reorganized (sections moved, IDs renumbered), the crosswalk becomes stale.
   Mitigation: the crosswalk is a historical reference aid, not a maintenance surface. It maps
   from the immutable archived monolith to modular locations at the time of split.

3. **Compatibility shim maintenance.** The shim at the original monolith path exists because
   tracked artifacts reference that path. If those artifacts are never updated, the shim must
   be maintained indefinitely.

## References

| What | Where |
|------|-------|
| Modular spec root | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/README.md` |
| spec.yaml (authority model) | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/spec.yaml` |
| Archived monolith (rev 21) | `docs/plans/archive/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` |
| Compatibility shim | `docs/plans/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md` |
| Crosswalk | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/crosswalk.md` |
| Benchmark spec | `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md` |
| Risk register (G3) | `docs/reviews/2026-04-01-t04-convergence-loop-risk-register.md` |
| Benchmark-first design plan | `docs/plans/2026-04-01-t04-benchmark-first-design-plan.md` |
| T2 contract (dependency) | `docs/plans/2026-04-02-t04-t2-synthetic-claim-and-closure-contract.md` |
| T3 contract (dependency) | `docs/plans/2026-04-02-t04-t3-deterministic-referential-continuity.md` |
| Spec-writer skill | `packages/plugins/superspec/skills/spec-writer/SKILL.md` |
| Shared contract (spec.yaml schema) | `packages/plugins/superspec/references/shared-contract.md` |

## Gotchas

1. **Path depth after monolith-to-directory compilation.** Every repo-relative link inherited
   from the monolith is one `../` too shallow because the modular files live one directory
   deeper. This affected 62 of 62 external link targets. A post-compilation link validator
   is non-optional for any future spec-writer compilation.

2. **Markdown heading slug fragility.** Standard Markdown heading slugs do not match the
   short-form requirement ID anchors. `## T4-SM-06: Verification State Model` generates
   slug `#t4-sm-06-verification-state-model`, not `#t4-sm-06`. Explicit `<a id>` HTML
   anchors are required for the ID-based cross-reference model.

3. **Conformance matrix link format.** The matrix cites 48 requirement IDs in plain text
   (e.g., `T4-SB-01, T4-F-01`) rather than as markdown links. This was a deliberate
   trade-off (the matrix is a lookup table, not a navigation surface) but review agents
   may flag it.
