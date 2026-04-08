# T8 Execution Plan V3: Minimum Runnable Shakedown Delivery

**Date:** 2026-04-08
**Status:** `Proposed`
**Design authority:** [2026-04-07-t7-executable-slice-definition.md](2026-04-07-t7-executable-slice-definition.md), [2026-04-07-t8-minimum-runnable-shakedown-packet.md](2026-04-07-t8-minimum-runnable-shakedown-packet.md)
**Accepted snapshot:** `feature/t8-ordering-validation` at commit `4d3851d0`
**Purpose:** Convert the accepted T7/T8 design packet into an executable delivery sequence with explicit ownership, gate artifacts, calibration evidence, and fallback paths.

## Authorities

| Authority | What it governs | Reference |
|-----------|-----------------|-----------|
| T7 executable slice | Behavioral surface, containment contract, inspection model, failure routing | [2026-04-07-t7-executable-slice-definition.md](2026-04-07-t7-executable-slice-definition.md) |
| T8 implementation packet | Concrete implementation surfaces, runtime artifacts, hook and harness mechanics | [2026-04-07-t8-minimum-runnable-shakedown-packet.md](2026-04-07-t8-minimum-runnable-shakedown-packet.md) |
| This plan | Execution sequence, ownership, evidence, gate logic, stabilization thresholds | this document |

This plan does **not** replace T7 or T8. It governs how the accepted packet is landed, built, stabilized, and inspected.

## Current State

- T7 and T8 reached `Defensible` after 15 scrutiny rounds across the project.
- The accepted plan pair is committed at `4d3851d0`.
- No implementation code exists for the behavioral layer.
- The following remain missing:
  - containment hooks
  - dialogue agent
  - `dialogue-codex` skill
  - `shakedown-b1` harness
  - transcript/schema validator
  - shakedown inspection artifact
- The highest-risk unknowns are now operational, not architectural:
  - synthetic timing evidence vs. real runtime timing
  - behavioral-skill stability under real transcripts
  - B1 scoutability sufficiency
  - transcript-marker visibility after `SubagentStop`

## Execution Principles

### Runtime vs. Informational Dependencies

Only runtime dependencies are fully serial.

- Runtime dependency: a later task requires earlier code or artifacts to exist.
- Informational dependency: a later decision needs evidence, but not compiled code.

This plan keeps runtime dependencies serial and allows informational work to run in parallel.

### Smoke-Test Evidence vs. Calibration Evidence

- Phase 0 timing measurement is a **smoke test**. It determines whether the provisional bootstrap strategy is plausible enough to proceed.
- Real poll-budget calibration uses telemetry from the live containment guard during rehearsal runs.
- Transcript-marker retry calibration is a separate measurement problem from startup ordering and is handled only in rehearsal and formal runs.

## Roles

| Role | Responsibility |
|------|----------------|
| Plan owner | Owns gate decisions, branch/worktree state, scope changes, and fallback activation |
| Runtime owner | Implements hooks, agent, skill, harness, and live telemetry |
| Schema owner | Owns machine-readable emission contract and validator behavior |
| Inspector | Reviews rehearsal/formal shakedown artifacts and adjudicates checklist results |

One person may hold multiple roles, but each gate still requires its artifact before approval.

## Authoritative Environment

Before runtime work begins, record one authoritative execution environment:

- Claude Code version
- plugin loading mode (`--plugin-dir` or installed plugin path)
- operating system
- machine class
- repo commit
- permission mode assumptions

Evidence from other environments is exploratory only unless the plan owner explicitly marks them equivalent.

## Machine-Readable Emission Contract

This contract exists so the validator in `P3` can validate a stable surface rather than prose interpretation.

### Turn Boundary

Each assistant turn emitted by `shakedown-dialogue` MUST contain exactly one state block with this structure:

1. Literal opening sentinel: `<SHAKEDOWN_TURN_STATE>`
2. One fenced `json` block
3. Literal closing sentinel: `</SHAKEDOWN_TURN_STATE>`

All prose follows the closing sentinel. No other JSON fence is permitted in the turn.

### State Object

```json
{
  "turn": 1,
  "scouted": true,
  "target_claim_id": 3,
  "target_claim": "string or null",
  "scope_root": "/abs/path or null",
  "queries": [
    {
      "type": "definition|falsification|supplementary",
      "tool": "Read|Grep|Glob",
      "target": "string"
    }
  ],
  "disposition": "supports|contradicts|ambiguous|conflicted|null",
  "citations": [
    {
      "path": "/abs/path",
      "lines": "12-18",
      "snippet": "string"
    }
  ],
  "claims": [
    {
      "id": 3,
      "text": "string",
      "status": "unverified|supported|contradicted|conflicted|ambiguous|not_scoutable",
      "scout_attempts": 1
    }
  ],
  "counters": {
    "total_claims": 4,
    "supported": 1,
    "contradicted": 0,
    "conflicted": 0,
    "ambiguous": 0,
    "not_scoutable": 1,
    "unverified": 2,
    "evidence_count": 1
  },
  "effective_delta": {
    "total_claims": 1,
    "supported": 1,
    "contradicted": 0,
    "conflicted": 0,
    "ambiguous": 0,
    "not_scoutable": 0,
    "unverified": 0,
    "evidence_count": 1
  },
  "terminal": false,
  "epilogue": null
}
```

### Turn Rules

- Every turn MUST emit exactly one state block.
- Non-scouting turns MUST set:
  - `scouted: false`
  - `target_claim_id: null`
  - `target_claim: null`
  - `scope_root: null`
  - `queries: []`
  - `disposition: null`
  - `citations: []`
- Scouting turns MUST include at least one `definition` query and one `falsification` query.
- Terminal turn MUST set `terminal: true` and include:

```json
{
  "ledger_summary": "string",
  "converged": true,
  "effective_delta_overall": {
    "total_claims": 0,
    "supported": 0,
    "contradicted": 0,
    "conflicted": 0,
    "ambiguous": 0,
    "not_scoutable": 0,
    "unverified": 0,
    "evidence_count": 0
  }
}
```

### Parse Failure Conditions

Any of the following is a parse failure:

- missing sentinel
- more than one state block in a single turn
- invalid JSON
- missing required keys
- wrong enum or type
- `scouted: true` without required query coverage
- terminal turn without `epilogue`
- non-monotonic `turn`

### Validator Success Bar

- 100% parseability across all rehearsal turns
- 100% parseability across all scouting turns and the terminal turn
- zero semantic failures on required coverage fields

## Workstreams

### Parallel Preparatory Work

These items require domain reasoning, not implemented runtime surfaces.

| Task | Owner | Done when | Artifact |
|------|-------|-----------|----------|
| `P0` Freeze emission contract | Schema owner | Contract approved | This section + two valid fixtures + two invalid fixtures |
| `P1` B1 scoutability preflight | Plan owner | B1 reviewed and fallback chosen if needed | 1-page memo with confidence level and fallback task |
| `P2` Draft `dialogue-codex` skill | Runtime owner | v0 draft exists | Skill draft mapped to T4 behaviors |
| `P3` Build rubric + validator | Schema owner | Validator runs against fixtures and inspection rubric is ready | Validator script + checklist template |

`P1`, `P2`, and `P3` may overlap with runtime phases if staffing permits.

### Serial Runtime Chain

| Task | Depends on | Owner | Done when | Artifact |
|------|------------|-------|-----------|----------|
| `T1` Land plan + create implementation worktree | none | Plan owner | T7/T8 on `main`, worktree created from `main`, branch `feature/t8-shakedown-implementation` opened | branch/worktree record |
| `T2` Environment baseline | `T1` | Runtime owner | authoritative environment recorded and basic runtime surfaces verified | environment log |
| `T3` Phase 0 synthetic timing smoke | `T2` | Runtime owner | 5 runs complete and `delta_ms` summary written | timing summary |
| `T4` Containment infrastructure + live branch coverage | `T3` | Runtime owner | tests pass and live smoke covers all load-bearing branches | live smoke log + `poll-telemetry.jsonl` |
| `T5` Agent + skill + harness assembly | `T4`, `P2` | Runtime owner | end-to-end lifecycle runs and artifacts exist | dry lifecycle packet |
| `T6` Stabilization rehearsal | `T5`, `P3` | Runtime owner + Schema owner | 2 rehearsal runs pass validator and telemetry review | rehearsal packet + validator report + telemetry summary |
| `T7` Formal shakedown | `T6`, `P1` | Inspector | rubric complete within 48 hours and result adjudicated | filled rubric + outcome note |

## Detailed Gates

### `T1`: Land Plan + Create Implementation Worktree

Done when:

- accepted docs are merged to `main`
- implementation worktree exists
- implementation branch is created from `main`
- plan owner records the branch and worktree path

This task does **not** end with "branch cleaned up." The implementation locus must exist before runtime work begins.

### `T2`: Environment Baseline

Done when:

- authoritative environment is recorded
- plugin discovery works in that environment
- `/reload-plugins` works
- existing codex-collaboration tests pass
- live plugin usage path is confirmed (`--plugin-dir` or installed plugin)

### `T3`: Phase 0 Synthetic Timing Smoke

Run at least 5 times:

- 3 cold runs
- 2 runs under moderate load

Record for each run:

- `marker_found`
- `delta_ms`
- cold vs. warm
- load condition

Decision rule:

- if median `delta_ms <= 1000ms` and all runs show `marker_found: true`, proceed
- if any run shows `marker_found: false`, or median `delta_ms > 1000ms`, write a warning note before proceeding
- do **not** change the final bootstrap budget from synthetic evidence alone unless the failure is clearly structural

Phase 0 is smoke evidence only. It does not finalize the poll budget.

### `T4`: Containment Infrastructure + Live Branch Coverage

Required before exit:

- unit/subprocess tests pass
- live smoke covers all load-bearing branches:
  - scope file create
  - scope file remove
  - Grep rewrite
  - pathless deny
  - main-thread passthrough
  - `agent_id` mismatch passthrough
  - seed-present poll success
  - seed-present poll timeout deny
- live poll telemetry is written to `${CLAUDE_PLUGIN_DATA}/shakedown/poll-telemetry.jsonl`

If any live branch is untested, `T4` is incomplete.

### `T5`: Agent + Skill + Harness Assembly

Done when:

- `shakedown-dialogue` is spawnable
- `dialogue-codex` preloads
- `shakedown-b1` runs the full lifecycle:
  - seed
  - scope
  - containment
  - cleanup
  - artifact write

This is still assembly, not stabilization.

### `T6`: Stabilization Rehearsal

Minimum requirement:

- 2 non-scored rehearsal runs
- validator success on 100% of turns
- explicit telemetry review

One refinement round is:

1. one skill/schema edit bundle
2. one rehearsal run
3. one validator report
4. one decision note

Cap: 5 refinement rounds

If the cap is hit, stop and choose one alternate path:

- simplify schema
- reduce per-turn behavioral obligations
- split output responsibilities

Stabilization decision rules:

- Poll gate:
  - `0-5%` poll hit rate: healthy
  - `>5%`: investigate
  - `>10%` or any wait `>1500ms`: increase bootstrap window before `T7`
- Transcript-marker gate:
  - record lag from Agent return to `.done` visibility
  - if any rehearsal run exceeds `1s`, review and adjust transcript retry before `T7`

### `T7`: Formal Shakedown

Inspector completes the 12-item rubric within 48 hours of run completion.

Outcomes:

- `pass`
- `fail` with routed component owner
- `inconclusive`

If `inconclusive`, execute the pre-authorized fallback task from `P1` immediately. Do not open a new planning loop first.

## Decision Ownership

| Gate | Decision owner | Required evidence |
|------|----------------|-------------------|
| `P1` B1 adequacy / fallback | Plan owner | scoutability memo |
| `T3` synthetic timing acceptance | Plan owner | timing summary |
| `T4` live runtime readiness | Runtime owner | live smoke log + poll telemetry |
| `T6` skill stability | Runtime owner + Schema owner | rehearsal packet + validator report |
| `T6` bootstrap window adjustment | Plan owner | real poll telemetry summary |
| `T6` transcript retry adjustment | Plan owner | transcript-marker lag summary |
| `T7` pass/fail/inconclusive | Inspector | completed rubric |

## Acceptance Thresholds

| Surface | Threshold |
|---------|-----------|
| Phase 0 smoke | evidence only, not final calibration |
| Rehearsal parseability | 100% of turns |
| Bootstrap poll health | `0-5%` hit rate healthy |
| Bootstrap poll adjustment | `>10%` hit rate or any wait `>1500ms` |
| Transcript-marker adjustment | any measured lag `>1s` during rehearsal |
| Formal inspection turnaround | within 48 hours |

## B1 Adequacy and Fallback

`P1` is heuristic, not predictive certainty. Reading the B1 anchor files can estimate likely scoutability shape, but cannot prove the final `not_scoutable` ratio because dialogue output may introduce claims not obvious from source review alone.

Therefore:

- `P1` must nominate at least one fallback task
- the fallback must be preflighted to the same standard as B1
- `inconclusive` at `T7` triggers fallback immediately

## Out of Scope

- scored-run harness work (`T4-BR` series)
- post-execution canonical-path filtering (`T4-CT-01`)
- B8 anchor-adequacy beyond the pre-authorized fallback task
- T5 `agent_local` mode migration
- multi-environment reproducibility claims

## Deliverables

| Deliverable | Produced by |
|-------------|-------------|
| environment log | `T2` |
| timing summary | `T3` |
| live smoke log | `T4` |
| poll telemetry | `T4`, reviewed at `T6` |
| dry lifecycle packet | `T5` |
| validator report | `T6` |
| transcript-marker lag summary | `T6` |
| completed inspection rubric | `T7` |

## Success Condition

This execution plan succeeds when:

1. the accepted T7/T8 packet is implemented on an explicit implementation branch
2. the runtime unknowns are reduced by evidence rather than assumption
3. the behavioral layer stabilizes against a real validator, not a prose interpretation
4. the first formal shakedown has a prepared fallback path instead of a late planning reset
