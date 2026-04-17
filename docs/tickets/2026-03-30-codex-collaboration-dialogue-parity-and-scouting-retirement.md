# T-20260330-04: Codex-collaboration dialogue parity and scouting retirement

```yaml
id: T-20260330-04
date: 2026-03-30
status: closed
priority: high
tags: [codex-collaboration, dialogue, agents, benchmark, supersession]
blocked_by: [T-20260330-03]
blocks: [T-20260330-07]
effort: large
```

## Context

Dialogue is the user-adoption gate for codex-collaboration. Cross-model cannot
be retired in practice until users can switch their `/dialogue` workflow.

The runtime side already has `codex.dialogue.start`, `.reply`, and `.read`.
What is missing is the user surface and the evidence-gathering layer around it:

- dialogue skill
- dialogue orchestration agent
- context gatherer agents
- synthesis format
- convergence detection
- benchmark execution for the context-injection retirement decision

## Problem

Without a production dialogue surface, codex-collaboration remains an internal
runtime rather than the actual successor plugin. The open design question is no
longer whether dialogue should exist. It is whether Claude-side scouting is
good enough to replace cross-model's plugin-side context-injection subsystem.

That question must be answered by the fixed benchmark contract from
`T-20260330-03`, not by ad hoc impressions.

## Scope

**In scope:**

- Add the codex-collaboration dialogue skill
- Add the codex-dialogue orchestration agent for the new package
- Add the code gatherer and falsifier agents for the new package
- Implement deterministic briefing assembly for the dialogue flow
- Implement convergence detection and final synthesis formatting
- Use Claude-side scouting with standard host tools (`Glob`, `Grep`, `Read`) as
  the default evidence-gathering mechanism
- Run the benchmark defined in
  `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md`
- Record the benchmark result and make the context-injection retirement decision
  explicit

**Explicitly out of scope:**

- Porting context-injection before the benchmark says it is necessary
- Delegation and promotion
- Analytics dashboard or cutover work
- Any change to the execution-domain runtime

## Decision Rule

- If the benchmark passes, codex-collaboration keeps Claude-side scouting as
  the default dialogue evidence path and context-injection remains retired by
  default.
- If the benchmark fails, do not port context-injection opportunistically.
  Create a focused follow-up packet that names the measured shortfall and the
  minimal subsystem needed to close it.

**Closeout note (2026-04-17):** This ticket resolved on a demonstrated-not-scored
benchmark result. See the Resolution section below for the retirement decision
that supersedes the original aggregate-score assumption.

## Acceptance Criteria

- [x] A codex-collaboration dialogue skill exists and routes through
      `codex.dialogue.start`, `.reply`, and `.read`
- [x] A codex-dialogue orchestration agent exists in the codex-collaboration
      package
- [x] Code and falsifier gatherer agents exist in the codex-collaboration
      package and use standard Claude-side tools
- [x] Dialogue runs produce a final synthesis with bounded evidence citations
      and a convergence result
- [x] The benchmark contract is executed on the fixed corpus without changing
      the corpus or pass rule mid-run
- [x] The benchmark artifacts are recorded in repo artifacts; neither per-task
      score rendering nor aggregate pass/fail is produced because this closeout
      preserves the capture set as demonstrated-not-scored evidence
- [x] The context-injection retirement decision is updated from provisional to
      explicit based on the captured architectural signature and its caveats

## Verification

- ✅ End-to-end dialogue runs were captured through the packaged
  codex-collaboration surface across the full B1/B3/B5/B8 corpus — see
  `docs/benchmarks/dialogue-supersession/v1/runs.json` and the imported
  transcript set under `docs/benchmarks/dialogue-supersession/v1/transcripts/`
- ✅ Gatherer outputs, assembled briefings, and final syntheses were inspected
  through the imported capture set — see
  `docs/benchmarks/dialogue-supersession/v1/transcripts/` and
  `docs/benchmarks/dialogue-supersession/v1/summary.md`
- ✅ The benchmark artifact set now includes raw run records, imported
  transcripts/syntheses, and demonstrated-not-scored closeout notes — see
  `docs/benchmarks/dialogue-supersession/v1/{manifest.json,runs.json,adjudication.json,summary.md}`
- ✅ The retirement decision follows the captured benchmark evidence and its
  caveats rather than an ungrounded narrative summary — see the Resolution and
  Closeout Notes sections below plus
  `docs/benchmarks/dialogue-supersession/v1/summary.md`

## Dependencies

This ticket depends on the shared substrate and benchmark contract from
`T-20260330-03`. It can run in parallel with `T-20260330-05` once that shared
substrate is stable.

## References

| Resource | Location | Purpose |
|----------|----------|---------|
| Dialogue runtime surface | `packages/plugins/codex-collaboration/server/dialogue.py` | Existing runtime foundation |
| Current MCP tool exposure | `packages/plugins/codex-collaboration/server/mcp_server.py` | Existing tool routing |
| Cross-model dialogue skill | `packages/plugins/cross-model/skills/dialogue/SKILL.md` | Semantic source only |
| Cross-model gatherer agents | `packages/plugins/cross-model/agents/` | Semantic source only |
| Benchmark authority | `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md` | Fixed evaluation contract |

## Execution Addendum (2026-04-16)

### Open Governance Decision: Scope-enforcement scope

**Historical status at addendum authoring time:** Open. Blocks aggregate scoring
(AC-6) and the retirement decision (AC-7) until resolved explicitly in this
ticket. Candidate runs may continue for evidence collection, but current
baseline artifacts must not be used for aggregate scoring unless this ticket
ratifies or replaces them.

**Controlling contract citations** (`docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md`):

- `:167-168` — "any out-of-scope scouting in the raw transcript makes the run invalid"
- `:182-183` — adjudicator reviews the raw transcript and invalidates any run that scouts beyond recorded `allowed_roots`
- `:282-283` — "Any scouting outside that scope invalidates the run and requires rerun from the same commit"

The contract text does not distinguish agent-side scouting from Codex-side `exec_command` reads. "Scouting in the raw transcript" is the operative phrase.

**Retroactive impact:**

All three current baseline runs recorded `valid: true` in their staging metadata under a lenient interpretation that treated Codex-side out-of-scope reads as edge-case observations rather than invalidation. That interpretation is not contract-authorized.

- B1 baseline: 0 agent scouts; 8+ out-of-scope Codex reads in transcript
- B3 baseline: 0 agent scouts; 4 out-of-scope Codex reads (self-flagged at `B3-baseline-synthesis.md:111`)
- B5 baseline: 0 agent scouts; multiple out-of-scope Codex reads — `foundations.md` (2 reads), `models.py`, `recovery-and-journal.md`, plus cross-references to additional spec and server files surfaced in the final synthesis

Staging metadata for all three is preserved as captured, but not yet ratified for aggregate use.

**Options:**

- **A. Strict reading.** Enforce the contract text as written. All three baseline runs invalid. Rerun with stricter scope-enforcement prompting. Risk: baseline's Codex-side autonomy means prompt-only scope control may not hold under breadth-inviting topics, making the baseline structurally unscorable.
- **B. Contract amendment.** Formally narrow scope-invalidation to agent-side scouting. Acknowledges the architectural split (baseline's Codex delegation vs candidate's agent-side scouting) and re-establishes scorability of current baseline artifacts. Requires an explicit amendment to `dialogue-supersession-benchmark.md`.
- **C. Methodology revision.** Redesign the benchmark to measure scope discipline as a separate comparative dimension rather than a run-level invalidator. Broader scope than A or B.

**Decision owner:** this ticket (`T-20260330-04`). Resolve here as an explicit benchmark-governance decision before AC-6 can be closed or AC-7 can be updated from provisional to explicit.

### Resolution (2026-04-17)

**Status:** Closed. The project chose an AC-7-direct closeout.

Benchmark v1 served its diagnostic purpose without producing a formal aggregate
score. The captured architectural signature across B1/B3/B5/B8 is sufficient to
resolve the retirement decision for this repo: the candidate architecture
maintained the cleaner agent-side scope profile across the corpus, while the
baseline repeatedly produced transcript-visible Codex-side scope escapes
(`B1: 8+`, `B3: 4`, `B5: multiple`, `B8: 26`).

This ticket therefore closes on a **demonstrated-not-scored** benchmark result:

- **AC-5:** satisfied. The fixed B1/B3/B5/B8 corpus was executed without
  changing the corpus or the benchmark pass rule mid-capture.
- **AC-6:** reclassified, not passed. Repo artifacts preserve the capture set,
  but the aggregate scoring instrument was not applied.
- **AC-7:** resolved. Context-injection remains retired by default for
  codex-collaboration dialogue flows; no rollback is warranted on the evidence
  captured in this benchmark track.

Three caveats remain attached to that retirement decision:

1. `T-20260416-01` remains open. The extraction mismatch reproduced on B3
   candidate and B5 candidate, then did not reproduce on B8 candidate.
2. The strongest candidate comparative synthesis still names three mechanism
   losses relative to the retired baseline: L1 scout integrity, L2 plateau /
   budget control, and L3 per-scout redaction of raw host-tool output.
3. The capture sequence spans multiple documentation-only benchmark-history
   commits. That history is preserved as an audit fact, but it is not
   reconciled into a single scored `run_commit` because aggregate scoring was
   not pursued.

The Scope-Rule Governance Addendum above is therefore **resolved as moot**. Its
Options A/B/C governed how a formal aggregate score would treat baseline scope
contamination. This closeout does not pursue aggregate scoring, so no
scope-rule amendment, rerun path, or methodology revision is selected here.

## Closeout Notes

### Retirement Decision

The candidate architecture demonstrated consistent agent-side scope discipline
across the capture set and supplied the stronger operational answer for this
repo's `/dialogue` workflow. That is enough to make the supersession decision
explicit. The benchmark instrument exposed meaningful caveats, but it did not
surface a repo-local reason to restore context-injection as the default path.

### Benchmark Artifact Status

The benchmark artifacts are imported under
`docs/benchmarks/dialogue-supersession/v1/` as a demonstrated-not-scored
capture set. `summary.md` records the retirement decision, the scoring
reclassification, and the remaining caveats. `manifest.json` preserves the
historical multi-commit capture sequence as an audit fact rather than forcing a
synthetic reconciliation.

### Open Follow-Up Work

- `T-20260416-01` remains the live product-defect ticket for the reply-path
  extraction mismatch.
- The candidate's self-identified mechanism losses (L1/L2/L3) remain future
  spec/runtime evolution work rather than blockers to this ticket's closure.
- Staging artifacts remain relevant benchmark evidence even though aggregate
  scoring is not rendered.
