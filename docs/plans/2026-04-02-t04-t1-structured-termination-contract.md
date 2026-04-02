# T-04 T1 Decision: Structured Termination Contract

**Date:** 2026-04-02
**Context:** T1 from [2026-04-01-t04-benchmark-first-design-plan.md](2026-04-01-t04-benchmark-first-design-plan.md)
**Related gate:** G1 in [2026-04-01-t04-convergence-loop-risk-register.md](../reviews/2026-04-01-t04-convergence-loop-risk-register.md)
**Related risks:** B, G in [2026-04-01-t04-convergence-loop-risk-analysis.md](../reviews/2026-04-01-t04-convergence-loop-risk-analysis.md)
**Status:** `Accepted (design)` artifact for T1.

## 1. Decision

Adopt an orchestration-level structured termination contract that separates
control flow from terminal cause.

1. The controller/orchestrator returns a structured `ControlDecision`, not
   `(action, prose reason)`.
2. `action` remains the immediate control directive:
   `continue_dialogue`, `closing_probe`, or `conclude`.
3. Terminal cause is carried separately as `termination_code`, which is
   `null` for non-terminal decisions and one of:
   `convergence`, `budget_exhausted`, `scope_breach`, or `error`.
4. `converged`, `convergence_reason_code`, and `termination_reason` are
   projected mechanically from `termination_code` plus structured state such as
   `unresolved_open`. They are never inferred from prose and never derived by
   checking whether `action == "conclude"`.
5. Scope-breach exit uses the same termination contract as normal dialogue
   conclusion. It is not a side-channel epilogue override.

Human-readable reason text may still exist for logs or debugging, but it is a
derived display field only. It is not part of the machine contract.

## 2. Why This Direction

The current cross-model split already shows the correct principle. The control
layer computes actions from structured ledger state, while analytics projects
benchmark-facing convergence fields from structured state rather than from
`action_reason` prose
([control.py](../../packages/plugins/cross-model/context-injection/context_injection/control.py),
[emit_analytics.py](../../packages/plugins/cross-model/scripts/emit_analytics.py)).

T-04 needs the same separation inside the candidate loop. Otherwise two bad
shortcuts become tempting:

- parse a prose string like `"Budget exhausted"` to decide whether the run
  converged
- treat any `conclude` action as successful convergence, even though
  `conclude` can also mean budget exhaustion, scope breach, or error

Both violate the benchmark contract's requirement that
`converged_within_budget` be a binary result recorded by the dialogue
orchestrator, not a narrative assessment.

## 3. State Shape

The local control decision object is:

```text
ControlDecision {
  action: "continue_dialogue" | "closing_probe" | "conclude"
  termination_code: null | "convergence" | "budget_exhausted" | "scope_breach" | "error"
}
```

Notes:

- `action` answers "what happens next in the loop?"
- `termination_code` answers "if the loop stops here, why?"
- Non-terminal states always use `termination_code = null`.
- Terminal states always use `action = "conclude"` plus a non-null
  `termination_code`.

Required structured inputs to the decision function are:

- `budget_remaining`
- `closing_probe_fired`
- `scope_breach_count`
- current `entries`
- optional `phase_entries`

`unresolved_open` is derived from the latest entry in `entries`; it is not a
separate caller-owned input.

## 4. Owning Layers

| Layer | Ownership |
|---|---|
| 1-3 | Produce validated ledger state and phase-local control inputs |
| Cross-cutting orchestration | Evaluate scope-breach and budget precedence, then compute `ControlDecision` |
| 6 | Project benchmark-facing epilogue fields from `ControlDecision` plus structured state |

This keeps the benchmark-facing fields downstream from the control contract
instead of letting synthesis invent them independently.

## 5. Deterministic Algorithm Boundary

The orchestration-level decision order is:

```text
if scope_breach_count >= 3:
    return {action: "conclude", termination_code: "scope_breach"}

if budget_remaining <= 0:
    return {action: "conclude", termination_code: "budget_exhausted"}

if no entries exist yet:
    return {action: "continue_dialogue", termination_code: null}

plateau = last two phase-local effective_deltas are STATIC
unresolved_open = len(latest_entry.unresolved)

if plateau and not closing_probe_fired:
    return {action: "closing_probe", termination_code: null}

if plateau and closing_probe_fired and unresolved_open > 0:
    return {action: "continue_dialogue", termination_code: null}

if plateau and closing_probe_fired and unresolved_open == 0:
    return {action: "conclude", termination_code: "convergence"}

return {action: "continue_dialogue", termination_code: null}
```

Important boundaries:

- Scope breach is orchestration-owned and has higher precedence than budget,
  matching the current analytics priority.
- Budget exhaustion is a terminal cause, not a prose explanation.
- Budget exhaustion takes precedence even if the current turn would otherwise
  satisfy convergence criteria. This is an intentional tightening relative to
  the current analytics split: once T-04 adopts a single structured authority,
  "used the final available turn and would have converged" still records as
  `budget_exhausted`, not as converged.
- Plateau detection remains phase-local when phase tracking is in use.
- Open unresolved items prevent convergence after the probe; they do not create
  a special terminal code.

### 5.1 Error Boundary

`termination_code="error"` is produced by the orchestration wrapper outside the
normal decision branches above.

It is reserved for cases where the loop cannot produce a valid
`ControlDecision` from structured state, for example:

- unrecoverable local pipeline failure before control evaluation
- invalid or missing structured state at the point where control evaluation
  should occur
- explicit orchestration abort after a local invariant failure

The happy-path decision function in Section 5 does not synthesize `error` from
normal dialogue state. `error` is the terminal cause for failures outside that
decision function's domain.

## 6. Mechanical Projection To Benchmark Fields

The benchmark-facing fields are derived only from `termination_code` plus
structured unresolved state:

| termination_code | unresolved_open | converged | convergence_reason_code | termination_reason |
|---|---:|---|---|---|
| `convergence` | `0` | `true` | `all_resolved` | `convergence` |
| `convergence` | `> 0` | `true` | `natural_convergence` | `convergence` |
| `budget_exhausted` | any | `false` | `budget_exhausted` | `budget` |
| `scope_breach` | any | `false` | `scope_breach` | `scope_breach` |
| `error` | any | `false` | `error` | `error` |

Notes:

- The current plateau logic is expected to emit only the first `convergence`
  row because it concludes only when `unresolved_open == 0`.
- `natural_convergence` remains valid in the projection table because the
  schema already allows it, but T1 does not introduce a new control rule that
  would emit it.
- The intentional consequence of the budget-precedence rule is that exact-last-
  turn convergence does not get a special exception. If no budget remains, the
  run projects as `budget_exhausted`.
- `converged_within_budget` is the same binary as `converged` for the
  benchmark-facing candidate output.

## 7. Rejected Alternatives

### A. Keep `(action, prose reason)` and parse the reason later

Rejected because prose is not a stable machine contract. The exact risk under
G1 is that a future template change silently changes the meaning of the parser.

### B. Treat `action == "conclude"` as convergence

Rejected because `conclude` is overloaded. Budget exhaustion, scope breach, and
error also conclude the loop.

### C. Keep scope breach outside the termination contract

Rejected because that creates split-brain state: control says one thing while
epilogue fields say another. Scope breach must terminate through the same
structured path as every other terminal cause.

### D. Recompute benchmark fields from narrative synthesis only

Rejected because the synthesis is a reporting surface, not the authority for
whether the controller actually converged within budget.

## 8. Verification Path

The T1 implementation should be considered correct only if it has tests for:

1. Scope-breach precedence: `scope_breach_count >= 3` yields
   `action="conclude"` and `termination_code="scope_breach"` even if budget is
   also exhausted.
2. Budget exhaustion: `budget_remaining <= 0` yields
   `termination_code="budget_exhausted"` and projects to
   `converged=false`, `convergence_reason_code="budget_exhausted"`,
   `termination_reason="budget"`.
3. Plateau before probe: plateau with `closing_probe_fired=false` yields
   `action="closing_probe"` and `termination_code=null`.
4. Plateau after probe with unresolved items: yields
   `action="continue_dialogue"` and `termination_code=null`.
5. Plateau after probe with zero unresolved: yields
   `action="conclude"` and `termination_code="convergence"`, which projects to
   `all_resolved` + `convergence`.
6. Error terminal path: unrecoverable local pipeline failure in the
   orchestration wrapper yields
   `action="conclude"` and `termination_code="error"`, projecting to
   `converged=false`, `convergence_reason_code="error"`,
   `termination_reason="error"`.
7. Integration assertion: the pipeline-data epilogue is emitted from this
   structured projection, not from `action_reason` parsing.

## 9. What T1 Does Not Change

T1 resolves only the machine contract for termination. It does not:

- change the plateau policy itself
- change the once-per-phase closing-probe policy
- change the evidence budget rules
- decide the mode strategy or scouting placement

Those remain governed by other gates and tasks. T1 only makes the terminal
state explicit and mechanically projectable.
