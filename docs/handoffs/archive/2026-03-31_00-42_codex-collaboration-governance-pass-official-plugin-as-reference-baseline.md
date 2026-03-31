---
date: 2026-03-31
time: "00:42"
created_at: "2026-03-31T04:42:09Z"
session_id: faf08c70-425b-46d0-af9a-5b4e1e3fca4d
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-03-30_23-09_checkpoint-t03-plan-revised-ready-for-implementation.md
project: claude-code-tool-dev
branch: main
commit: 488e9cc5
title: "Codex-collaboration governance pass: official plugin as reference baseline"
type: handoff
files:
  - docs/superpowers/specs/codex-collaboration/official-plugin-rewrite-map.md
  - docs/superpowers/specs/codex-collaboration/README.md
  - docs/superpowers/specs/codex-collaboration/foundations.md
  - docs/superpowers/specs/codex-collaboration/contracts.md
  - docs/superpowers/specs/codex-collaboration/delivery.md
  - docs/superpowers/specs/codex-collaboration/decisions.md
---

# Codex-collaboration governance pass: official plugin as reference baseline

## Goal

Resolve the governance question for the codex-collaboration spec packet: what is the relationship between the local spec and the official OpenAI plugin (`openai/codex-plugin-cc`, pinned to `9cb4fe4`)?

**Trigger:** The prior session (not captured in the loaded checkpoint) exhaustively compared the local spec against the official plugin and produced `official-plugin-rewrite-map.md` (`19999eb1`). That map was written from a convergence perspective (Option B) and needed a governance decision before being executed against normative spec files.

**Stakes:** The governance choice determines whether the spec shrinks to an extension-only supplement (convergence) or retains full architectural authority with the official plugin as documented context (reference baseline). This fundamentally shapes every future spec edit, implementation decision, and build sequence.

**Success criteria:**
- Governance question resolved with a recorded decision
- Rewrite map revised to match the chosen governance model
- Annotations applied to all 5 target spec files
- Consistency sweep of remaining spec files confirms no contradictions
- Everything committed cleanly

**Connection to project arc:** The codex-collaboration spec is the planned successor to the cross-model plugin. The governance decision determines how much of the integration architecture the spec owns vs. inherits from upstream. This is a prerequisite to any implementation work (T-03 or otherwise).

## Session Narrative

Session began by loading the most recent checkpoint, which described T-03 safety substrate plan revision work. The user immediately corrected this: the prior session had actually pivoted away from T-03 implementation and instead performed an exhaustive comparison of the local `codex-collaboration` spec against the official `openai/codex-plugin-cc` repository. The checkpoint was stale — it captured the state before the pivot, not after.

The user framed the governance question precisely: "is the official plugin merely the reference baseline, or is it the shell this spec should converge toward?" They pointed to `official-plugin-rewrite-map.md` as the concrete artifact to review before deciding.

Read the rewrite map (333 lines, ~45 instructions). The map was unambiguously written from a convergence perspective — every instruction said "delete universal claim X" or "replace with baseline-first framing Y." Identified this embedded bias as important context for the decision.

Presented three options to the user:
- **Option A: Reference baseline** — official plugin acknowledged as context, spec retains full architectural authority, annotations are additive
- **Option B: Full convergence** — spec restructures around official plugin as the shell, two-lane baseline/extension architecture in every file
- **Option C: Convergence with divergence rights** — Option B's structure plus an explicit clause allowing extensions to replace baseline behavior

Analyzed the key differentiators across six dimensions: spec scope, coupling to upstream, maintenance burden, upstream change impact, build sequence, and language alignment. Noted that Option B couples the spec to a moving target (the official plugin could change), while Option A means maintaining a full-stack spec for capabilities the official plugin already ships.

User chose Option A decisively: "I definitely want to go in the direction of A - Reference baseline."

Analyzed how Option A transforms the rewrite map per-file. The key shift: ~45 "delete/replace" instructions became ~12 "keep + annotate" instructions. Presented a before/after table for each of the 5 target files showing which instructions survive, which are dropped, and which are revised.

User asked for the map file to be rewritten. Rewrote `official-plugin-rewrite-map.md` from convergence (Option B) to reference-baseline (Option A). The file went from 333 lines of restructuring surgery to ~140 lines of additive annotations.

User then manually applied all annotations across the 5 target files (README.md, foundations.md, contracts.md, delivery.md, decisions.md). Reported: "The packet now treats the official plugin as documented reference context, preserves the existing control-plane architecture as the design center, records the upstream pin in both README.md:24 and decisions.md:49, and leaves spec.yaml untouched."

Reviewed all 5 annotated files against the rewrite map — confirmed 12/12 instructions covered. Verified specific line numbers for each annotation.

User then requested a contradiction audit of the 4 untouched spec files: advisory-runtime-policy.md (147 lines), promotion-protocol.md (100 lines), recovery-and-journal.md (178 lines), and dialogue-supersession-benchmark.md (208 lines). Read all four in full. Found no contradictions — these files operate at the behavioral layer (how specific mechanisms work) rather than the architectural layer (what the system is), so the governance decision doesn't affect them. This clean result reflects good spec layering: architectural claims live in the 5 annotated files, behavioral claims live in the 4 untouched protocol files.

Committed all changes as `488e9cc5` with message "docs: annotate codex-collaboration spec against official plugin". The diff was +175 / -289 (net -114 lines), with the reduction coming from the rewrite map slimming.

## Decisions

### Official plugin as reference baseline, not convergence target

**Choice:** Option A — the official OpenAI plugin (`openai/codex-plugin-cc`) is reference context for the Codex integration landscape. The codex-collaboration spec retains independent architectural authority.

**Driver:** User stated: "I definitely want to go in the direction of A - Reference baseline." The spec's control-plane mediation, structured flows, durable lineage, isolated execution, and promotion machinery provide capabilities the official plugin does not. Architectural independence preserves the spec's coherence as a unified system.

**Alternatives considered:**
- **Option B: Full convergence** — Restructure the spec around the official plugin as the shell, with a two-lane baseline/extension architecture in every file. Rejected because it would split the product into upstream baseline (deferred to external dependency) plus local extensions (owned locally), creating two integration models instead of one. Also creates coupling to a moving target — the official plugin could restructure its hook/command surface, change its app-server interaction model, or add capabilities that overlap with extensions.
- **Option C: Convergence with divergence rights** — Option B's structure plus an explicit promotion clause allowing extensions to replace baseline behavior when proven superior. Not explicitly rejected by user, but Option A was chosen without considering C further — the user preferred full independence over any form of convergence.

**Trade-offs accepted:** Higher maintenance burden — the spec owns the full integration stack including capabilities the official plugin already ships. This means specifying, implementing, and testing behavior that already exists elsewhere. Accepted in exchange for architectural independence and freedom to evolve without upstream coupling.

**Confidence:** High (E2) — decision based on reading both the official plugin repo and the local spec, understanding both approaches thoroughly, and analyzing the rewrite map's implications across all 5 target files. Two independent inputs: the rewrite map's instruction-level analysis and the per-file impact assessment.

**Reversibility:** Medium — the rewrite map could be revised back to Option B, but the 5 spec files now have Option A annotations baked in. Switching to convergence would require removing these annotations and performing the heavier two-lane restructuring. Not permanently locked, but not trivial to reverse either.

**Change trigger:** If upstream adds lineage, isolation, or promotion equivalents that are strictly superior to the spec's approach, re-evaluate. The upstream pin (`9cb4fe4`) in both README.md:24 and decisions.md:49 creates a concrete staleness trigger.

### Rewrite map: additive annotations over structural surgery

**Choice:** Rewrite the existing convergence-oriented rewrite map (Option B, ~45 instructions) into a reference-baseline map (Option A, ~12 instructions) that prescribes additive annotations rather than structural reshaping.

**Driver:** Follows directly from the governance decision. The map's instructions must match the chosen governance model — additive context for reference baseline, not delete/replace for convergence.

**Alternatives considered:**
- **Keep Option B map alongside Option A annotations** — Maintain both maps for future reference. Rejected because two contradictory maps would confuse any future session loading this context.
- **Delete the map entirely** — The annotations are now applied; the map is no longer needed. Rejected because the map documents what annotations exist and why, serving as an audit trail for the governance decision.

**Trade-offs accepted:** The map is now a supporting document (instructions executed, annotations applied) rather than an active execution plan. Its ongoing value is as governance provenance.

**Confidence:** High (E2) — the instruction reduction was analyzed per-file with explicit before/after tables.

**Reversibility:** High — the map file can be rewritten again if governance changes.

**Change trigger:** Same as the governance decision itself.

## Changes

### `docs/superpowers/specs/codex-collaboration/official-plugin-rewrite-map.md` — Rewritten from convergence to reference-baseline

**Purpose:** Transform the rewrite map from a convergence execution plan (~45 structural instructions) to a reference-baseline execution plan (~12 additive instructions).

**Approach:** Replaced the introduction's three-category framing (Baseline/Extension/Delete) with a single integration principle (reference context, not convergence target). Rewrote each per-file section: "delete/replace" instructions became "add annotation" or "drop" (most dropped). Net result: 333 lines down to ~140 lines.

**Key implementation detail:** The map preserves per-file organization so each annotation can be traced back to its rewrite-map instruction. The "Follow-On Note" about spec.yaml was removed because the authority model doesn't need a baseline/extension axis under Option A.

### `docs/superpowers/specs/codex-collaboration/README.md` — Added "Relationship to Official Plugin" section

**Purpose:** Establish the official plugin as documented reference context, not the spec's architectural foundation.

**Approach:** Added a new section after the introduction (before Authority Model) at lines 14-24. Describes the official plugin, states the spec's different approach, notes intentional overlap, and includes the upstream pin at line 24.

**Key implementation detail:** The upstream pin (`9cb4fe4`) appears here and in decisions.md — two locations create a concrete staleness trigger without requiring monitoring infrastructure.

### `docs/superpowers/specs/codex-collaboration/foundations.md` — Added goal and scope annotations

**Purpose:** Acknowledge Codex-native primitives in goals; scope the Prompting and Context Assembly contracts relative to official plugin capabilities.

**Approach:** Three additions: one new goal (line 25), one Prompting Contract annotation (line 191), one Context Assembly Contract annotation (line 206). All additive — no existing content changed.

**Key implementation detail:** The scope annotations follow a consistent pattern: name what the official plugin does, then state why the spec's approach is different.

### `docs/superpowers/specs/codex-collaboration/contracts.md` — Added comparison note and "no equivalent" annotations

**Purpose:** Note the architectural divergence (mediation vs. direct exposure) and mark spec components that have no official-plugin counterpart.

**Approach:** One comparison note after the tool-surface preamble (line 16). Three "no equivalent" annotations on Lineage Store (line 95), Operation Journal (line 176), and Promotion Protocol (line 31).

**Key implementation detail:** The "no equivalent" annotations are the most strategically significant — they mark the spec's core value proposition (what you get from this spec that you can't get from the official plugin).

### `docs/superpowers/specs/codex-collaboration/delivery.md` — Added Official Plugin Equivalents table

**Purpose:** Map each build step to its official-plugin equivalent or gap.

**Approach:** Added a comparison table at lines 163-175, after the existing build-sequence table. All 7 build steps mapped. Concluded with: "Steps with no official-plugin equivalent are the core value proposition of this spec's extension architecture."

### `docs/superpowers/specs/codex-collaboration/decisions.md` — Added governance decision record, Option E, and open question

**Purpose:** Record the governance decision, add the thin-bridge option to the architecture analysis, and register the `codex.consult` retirement question.

**Approach:** Three additions: governance decision record at lines 41-49 (with upstream pin), Option E in the architecture table at line 83, and the `codex.consult` open question at lines 115-117.

**Key implementation detail:** Option E ("Thin bridge to official plugin") was the considered-and-rejected alternative corresponding to Option B. Recording it in the architecture analysis table makes the governance decision auditable alongside the original architectural choices.

## Codebase Knowledge

### Spec Packet Architecture

The codex-collaboration spec packet at `docs/superpowers/specs/codex-collaboration/` has 12 files organized in two layers:

| Layer | Files | Scope | Governance Impact |
|-------|-------|-------|-------------------|
| **Architectural** | README.md, foundations.md, contracts.md, delivery.md, decisions.md | What the system IS, how it relates to the landscape | Annotated with official-plugin context |
| **Behavioral** | advisory-runtime-policy.md, promotion-protocol.md, recovery-and-journal.md | HOW specific mechanisms work within the architecture | Unaffected by governance decision |
| **Benchmark** | dialogue-supersession-benchmark.md | Internal supersession question (retiring context-injection) | Unaffected — orthogonal axis |
| **Supporting** | official-plugin-rewrite-map.md, spec.yaml | Governance provenance, authority model | Map rewritten; spec.yaml untouched |

This two-layer design is well-factored: governance decisions live at the architectural layer and don't propagate to behavioral protocols. A future governance change would only affect the 5 architectural files plus the rewrite map.

### Annotation Pattern

All official-plugin annotations across the 5 target files follow a consistent rhetorical pattern:
1. Name what the official plugin does for the relevant capability
2. State why this spec takes a different approach
3. (Where applicable) Note that the overlap is intentional

This pattern makes divergence auditable — each annotation documents both the official plugin's approach and the spec's rationale for differing.

### Upstream Pin Locations

The official plugin comparison is pinned to commit `9cb4fe4` in two locations:
- `README.md:24` — visible on first read of the spec packet
- `decisions.md:49` — part of the governance decision record

Both include the re-evaluation trigger: "If upstream changes materially, re-evaluate comparison claims."

### Key Files Read This Session

| File | Lines | Purpose | Key Finding |
|------|-------|---------|-------------|
| `official-plugin-rewrite-map.md` | 333 (pre-rewrite) | Rewrite plan from prior session | Written from convergence perspective; every instruction was "delete/replace" |
| `README.md` | 47 → 59 | Spec packet introduction | Split-runtime framing at line 12 preserved; new section at lines 14-24 |
| `decisions.md` | ~100 → ~118 | Decision records | Option E added to architecture table; governance decision at lines 41-49 |
| `foundations.md` | ~310 → ~323 | Scope, architecture, trust model | Three annotations: goal (line 25), Prompting (line 191), Context Assembly (line 206) |
| `contracts.md` | ~280 → ~293 | Tool surface, data models | Four annotations: preamble (line 16), lineage (line 95), journal (line 176), promotion (line 31) |
| `delivery.md` | ~288 → ~300 | Build sequence, test strategy | Equivalents table at lines 163-175 |
| `advisory-runtime-policy.md` | 147 | Policy fingerprints, rotation, reaping | No contradictions — purely behavioral scope |
| `promotion-protocol.md` | 100 | Worktree-to-workspace promotion | No contradictions — purely behavioral scope |
| `recovery-and-journal.md` | 178 | Crash recovery, journaling, concurrency | No contradictions — purely behavioral scope |
| `dialogue-supersession-benchmark.md` | 208 | Context-injection supersession benchmark | No contradictions — orthogonal comparison axis |

### Spec Packet Dependencies

The spec packet's internal cross-reference structure (relevant for future edits):

```
README.md ──references──→ all files (reading order table)
foundations.md ──references──→ contracts.md (data models, audit events)
contracts.md ──references──→ promotion-protocol.md, recovery-and-journal.md
promotion-protocol.md ──references──→ contracts.md, recovery-and-journal.md, advisory-runtime-policy.md
advisory-runtime-policy.md ──references──→ contracts.md, foundations.md, recovery-and-journal.md
recovery-and-journal.md ──references──→ contracts.md, advisory-runtime-policy.md
delivery.md ──references──→ contracts.md, promotion-protocol.md, recovery-and-journal.md
decisions.md ──references──→ contracts.md, delivery.md, dialogue-supersession-benchmark.md
dialogue-supersession-benchmark.md ──references──→ contracts.md, delivery.md, decisions.md
```

All cross-references use relative markdown links with semantic kebab-case anchors (convention documented at README.md:56).

### Consistency Sweep: Untouched Files Detail

The contradiction audit read all 4 untouched spec files in full. Each was checked for implicit assumptions about the official plugin relationship, claims that position the spec as a convergence target, or language that contradicts the reference-baseline governance stance.

**advisory-runtime-policy.md (147 lines):** Defines policy fingerprint model, privilege widening/narrowing rotation protocol, freeze-and-rotate semantics, reap conditions, turn boundary invariants, and post-promotion coherence. The core enforcement invariant is "never mutate advisory policy in place." All concepts (fingerprints, rotation, reaping) are internal to the spec's control plane. The file references `codex.consult` at line 44 (widening trigger) and `foundations.md`, `contracts.md`, `recovery-and-journal.md` — but never makes claims about integration landscape positioning. Clean.

**promotion-protocol.md (100 lines):** Defines 5 preconditions (HEAD match, clean tree/index, artifact hash, job completed), the promotion state machine (7 states, 8 transitions), rollback semantics, and workspace effects. Every concept is specific to isolated-worktree-to-primary-workspace promotion — a capability the official plugin has no equivalent of. The file references `contracts.md` (typed rejections, DelegationJob) and `recovery-and-journal.md` (journal entries, retention). No external positioning claims. Clean.

**recovery-and-journal.md (178 lines):** Defines the two-log architecture (operation journal for idempotent replay, audit log for human reconstruction), crash recovery paths for advisory and delegation runtimes, concurrency limits (max-1 delegation), advisory-delegation race handling, and retention defaults. All concepts are internal control-plane mechanics. The stale advisory context marker (lines 63-71) is specific to the spec's post-promotion coherence protocol. No external positioning claims. Clean.

**dialogue-supersession-benchmark.md (208 lines):** Fixed-corpus benchmark for deciding whether codex-collaboration dialogue can retire cross-model's context-injection. Compares two internal systems (cross-model baseline vs. codex-collaboration candidate). The benchmark's comparison axis (context-injection quality) is orthogonal to the official-plugin governance question. Eight benchmark tasks (B1-B8) reference codex-collaboration implementation files but not the official plugin. Clean.

## Conversation Highlights

**Handoff correction — the loaded checkpoint was stale:**
User provided critical context that the prior session pivoted away from T-03 implementation to official-plugin comparison work. The loaded checkpoint (`2026-03-30_23-09_checkpoint-t03-plan-revised-ready-for-implementation.md`) captured state before the pivot, not after. The rewrite map (`19999eb1`) was the actual session output. User gave a full paragraph of corrective context including the upstream pin commit, the governance question formulation, and the specific artifact path — demonstrating a preference for thorough corrections over brief "that's wrong" messages.

**Governance question framing — user set the terms precisely:**
User framed the decision as: "is the official plugin merely the reference baseline, or is it the shell this spec should converge toward?" This framing was adopted directly — it defined the two poles of the analysis. User also specified: "The next action is to review the rewrite map and decide one governance question before editing docs" — establishing that the governance decision must precede any spec edits.

**Governance decision — immediate and decisive:**
When presented with three options (A: reference baseline, B: full convergence, C: convergence with divergence rights), user chose A without deliberation: "I definitely want to go in the direction of A - Reference baseline." No follow-up questions about Option C's middle ground. Then asked a focused follow-up: "How would that change official-plugin-rewrite-map.md" — moving straight to execution implications.

**Per-file impact analysis — user wanted concrete before/after:**
After Claude presented the per-file summary table showing ~45 instructions reduced to ~12, user said "rewrite the map file to reflect Option A" — no further discussion needed. The table format (current instruction vs. Option A version, per file) gave sufficient detail for the user to greenlight the rewrite.

**Manual annotation application:**
User chose to apply the annotations themselves rather than delegate to Claude. Reported the results with specific line references (README.md:24, decisions.md:49). This working pattern — Claude analyzes and plans, user executes changes, Claude verifies — was efficient for this type of spec editing work. User's self-verification report was structured: "The packet now treats the official plugin as documented reference context, preserves the existing control-plane architecture as the design center, records the upstream pin in both README.md:24 and decisions.md:49, and leaves spec.yaml untouched."

**Next-step selection — chose from structured options:**
When offered three options (1: contradiction audit, 2: codex.consult decision memo, 3: commit governance pass), user selected option 1 first. After the audit found no contradictions, user then said "Read for stage and commit" — combining options 1 and 3 sequentially while deferring option 2.

**Commit message collaboration:**
User suggested the commit message: "docs: annotate codex-collaboration spec against official plugin." Concise, follows the `docs:` prefix convention observed in recent git history. Also specified: "I'd treat this as one coherent docs commit" — confirming all 6 files should be in a single commit.

## Context

### Mental Model

This is a **governance architecture problem**, not a code problem. The question isn't "what should the spec say about the official plugin" but "what authority relationship does the spec have with the official plugin." The answer to that question determines how every future spec edit is framed.

The core insight: the rewrite map as originally written (Option B) had already made the governance decision implicitly — it was a convergence plan disguised as a neutral rewrite. Making the governance question explicit before executing the map prevented a structural commitment that would have been difficult to reverse.

The two-layer spec design (architectural vs. behavioral) meant the governance decision could be applied cleanly to 5 files without touching 4 others. This is good spec factoring — architectural claims and behavioral claims are separated.

### Project State

The codex-collaboration spec packet is post-governance-pass. The implementation landscape:

- **Spec packet:** 12 files in `docs/superpowers/specs/codex-collaboration/`, all consistent with the reference-baseline governance stance. The spec owns the full integration architecture independently.
- **T-03 plan:** `docs/superpowers/plans/2026-03-30-codex-collaboration-safety-substrate.md` (~2580 lines, 9 tasks + deferred Task 10). Written before the official-plugin comparison and governance decision. Needs reassessment — the architectural framing is unchanged (Option A preserves the split-runtime model), but the governance context has evolved. The plan went through 3 review rounds (13 findings fixed) and was declared implementation-ready before the pivot.
- **Implementation code:** None written yet. All work to date is spec, plan, and governance. The `packages/plugins/codex-collaboration/` directory contains code from earlier prototyping, but T-03 plan work has not started.
- **Cross-model plugin:** The existing `cross-model` plugin at `packages/plugins/cross-model/` remains operational. `codex-collaboration` is its planned successor. 840 cross-model tests passing (post-CCDI excision).
- **Open question:** Whether `codex.consult` should be retired in favor of native review/task patterns (decisions.md:115-117). This is the most strategically significant tension point between the spec and the official plugin.

### Environment

- Branch: `main` (governance pass committed directly — doc-only changes, no feature branch needed)
- Commit: `488e9cc5` (governance pass), preceded by `0728c6f0` (handoff archive)
- The feature branch `feature/codex-collaboration-safety-substrate` was merged to `main` at `664fc249` before this session
- Main is ahead of origin by 2 commits (handoff archive + governance pass) — not yet pushed

## Learnings

### Rewrite maps embed governance decisions implicitly

**Mechanism:** A rewrite map's instructions ("delete X", "replace Y with Z") implicitly commit to an architectural stance. The original map used "delete universal claim" and "split into two lanes" — these are convergence instructions, not neutral rewrites.

**Evidence:** Every instruction in the original 333-line map was a convergence instruction. When revised to reference-baseline, ~33 of ~45 instructions were simply dropped because they only made sense under convergence.

**Implication:** Before executing any rewrite map, surface the implicit governance assumption and get explicit confirmation. The cost of asking is one question; the cost of executing the wrong governance model is undoing structural changes across multiple files.

**Watch for:** Future rewrite maps or refactoring plans that embed assumptions about system boundaries, ownership, or authority.

### Spec layering determines governance blast radius

**Mechanism:** The codex-collaboration spec's two-layer design (architectural files vs. behavioral protocol files) meant the governance decision affected exactly 5 of 12 files. The 4 behavioral protocol files were untouched because they specify mechanisms within the architecture, not the architecture itself.

**Evidence:** Contradiction audit of all 4 untouched files found zero conflicts. advisory-runtime-policy.md (147 lines), promotion-protocol.md (100 lines), recovery-and-journal.md (178 lines), and dialogue-supersession-benchmark.md (208 lines) — none reference the official plugin or make claims about integration landscape positioning.

**Implication:** Well-factored specs localize the impact of governance decisions. If the spec had mixed architectural and behavioral claims in the same files, the governance pass would have been more invasive.

### Upstream pins create concrete staleness triggers

**Mechanism:** Pinning the official plugin comparison to commit `9cb4fe4` in two locations (README.md:24 and decisions.md:49) with explicit re-evaluation language creates a concrete trigger for revisiting the governance decision.

**Evidence:** The upstream pin pattern comes from the rewrite map's original "upstream-pin note" instruction, preserved through the governance change.

**Implication:** Any spec that references external systems should pin the comparison point and include a re-evaluation trigger. Unpinned comparisons become invisibly stale.

## Next Steps

### 1. Reassess T-03 plan against governance decision

**Dependencies:** None — this is analysis, not implementation.

**What to read first:** `docs/superpowers/plans/2026-03-30-codex-collaboration-safety-substrate.md` (the ~2580-line T-03 plan, written before the official-plugin comparison and governance decision).

**Approach suggestion:** Check whether the T-03 plan's assumptions about the integration architecture are still valid under the reference-baseline governance model. The plan was written when the spec presented the split-runtime model as the universal default — that framing is unchanged (Option A preserves it), but the governance context around it has evolved.

**Acceptance criteria:** Either confirm the T-03 plan is unaffected, or identify specific tasks/steps that need revision.

**Potential obstacles:** The T-03 plan is 2580 lines — this is a significant read. May benefit from a focused grep for "baseline", "official", "native" to check for assumptions that conflict with the governance decision.

### 2. Evaluate the `codex.consult` open question

**Dependencies:** Governance decision (complete).

**What to read first:** `decisions.md:115-117` (the open question), `contracts.md` codex.consult surface, and the official plugin's native review/task flow.

**Approach suggestion:** Write a concrete decision memo comparing `codex.consult` against native review/task patterns. The open question is the one place where the spec explicitly acknowledges the official plugin's approach might be sufficient.

**Acceptance criteria:** Either close the question (keep `codex.consult` with rationale) or escalate it (propose retirement path with migration plan).

### 3. Begin T-03 implementation (if plan holds)

**Dependencies:** T-03 plan reassessment (#1).

**What to read first:** T-03 plan Task 1 (secret taxonomy port).

**Approach suggestion:** User's prior preference was subagent-driven execution: dispatch a fresh agent per task, review between tasks.

## In Progress

Clean stopping point. The governance pass is complete — rewrite map revised, annotations applied to 5 files, consistency sweep of 4 remaining files found no contradictions, everything committed at `488e9cc5`.

No work in flight. The session reached a natural boundary.

## Open Questions

### T-03 plan alignment with governance decision

The T-03 safety substrate plan was written before the official-plugin comparison. While the governance decision (reference baseline) preserves the spec's split-runtime architecture, the context around it has changed. Need to verify T-03 assumptions are still valid.

### `codex.consult` surface retirement

Open question registered in `decisions.md:115-117`: whether `codex.consult` should be retired in favor of native review/task patterns plus a lighter wrapper. This is the spec's most strategically interesting tension point — the one place where it openly considers that the official plugin's approach might be sufficient.

## Risks

### Upstream evolution could invalidate comparison claims

The governance annotations reference the official plugin's capabilities as of commit `9cb4fe4`. If upstream adds lineage, isolation, or promotion capabilities, the annotations become stale. The upstream pin and re-evaluation triggers mitigate this, but require someone to notice upstream changes.

### T-03 plan may need revision

The 2580-line implementation plan was written under a different governance context. While the architectural framing is preserved, specific implementation choices or build-sequence assumptions may need adjustment.

## References

| What | Where |
|------|-------|
| Rewrite map (revised) | `docs/superpowers/specs/codex-collaboration/official-plugin-rewrite-map.md` |
| Governance decision record | `docs/superpowers/specs/codex-collaboration/decisions.md:41-49` |
| Option E (thin bridge, rejected) | `docs/superpowers/specs/codex-collaboration/decisions.md:83` |
| `codex.consult` open question | `docs/superpowers/specs/codex-collaboration/decisions.md:115-117` |
| Upstream pin (README) | `docs/superpowers/specs/codex-collaboration/README.md:24` |
| Upstream pin (decisions) | `docs/superpowers/specs/codex-collaboration/decisions.md:49` |
| T-03 implementation plan | `docs/superpowers/plans/2026-03-30-codex-collaboration-safety-substrate.md` |
| Official plugin repo | `openai/codex-plugin-cc` (pinned to `9cb4fe4`) |
| Spec packet | `docs/superpowers/specs/codex-collaboration/` (12 files) |

## Gotchas

### Loaded checkpoint was stale

The loaded checkpoint (`2026-03-30_23-09_checkpoint-t03-plan-revised-ready-for-implementation.md`) described T-03 plan revision work, but the prior session actually pivoted to official-plugin comparison after that checkpoint was saved. The rewrite map (`19999eb1`) was the actual output. Always verify loaded handoff context against recent git history when the user provides corrections.

### Feature branch already merged

The `feature/codex-collaboration-safety-substrate` branch was merged to `main` at `664fc249` before this session. The governance pass was committed directly to `main` as doc-only changes. If implementation work begins, a new feature branch will be needed (branch protection hook blocks edits on `main`).

## User Preferences

**Decision style:** Decisive, preference-driven. When presented with structured options (A/B/C), chooses quickly without deliberation. Said "I definitely want to go in the direction of A" without exploring Option C's middle ground.

**Working pattern for spec edits:** Prefers to apply spec annotations manually rather than delegating to Claude. Claude analyzes, plans, and verifies; user executes the actual edits. This pattern was effective — user applied all 12 annotations across 5 files accurately.

**Commit message style:** Provides commit messages directly. Prefers concise `type: description` format. Suggested: "docs: annotate codex-collaboration spec against official plugin."

**Option presentation:** Prefers numbered options with clear labels. Chose between 1/2/3 when offered next steps. Open-ended "what next?" prompts are less effective than structured choices.

**Context corrections:** Provides detailed corrections when loaded context is wrong. Gave a full paragraph explaining the prior session's actual work, including the upstream pin commit hash and the governance question formulation.
