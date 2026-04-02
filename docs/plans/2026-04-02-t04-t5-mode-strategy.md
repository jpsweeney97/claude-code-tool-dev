# T-04 T5 Decision: Mode Strategy

**Date:** 2026-04-02
**Context:** T5 from [2026-04-01-t04-benchmark-first-design-plan.md](2026-04-01-t04-benchmark-first-design-plan.md)
**Related gate:** G4 in [2026-04-01-t04-convergence-loop-risk-register.md](../reviews/2026-04-01-t04-convergence-loop-risk-register.md)
**Related risks:** H in [2026-04-01-t04-convergence-loop-risk-analysis.md](../reviews/2026-04-01-t04-convergence-loop-risk-analysis.md)
**Status:** `Accepted (design)` artifact for T5.

## 1. Decision

Adopt a third dialogue mode value for the T-04 benchmark-first candidate:
`agent_local`.

The mode contract becomes:

```text
DialogueMode = "server_assisted" | "agent_local" | "manual_legacy"
```

T5 chooses the migration branch, not the reuse branch:

1. T-04 benchmark-first dialogue runs emit `mode="agent_local"`.
2. `server_assisted` remains the label for the current helper-mediated dialogue
   loop where an external helper/service owns structured turn processing or
   scout mediation.
3. `manual_legacy` remains the no-helper, no-scout fallback loop.
4. The mode field describes dialogue orchestration ownership, not raw Codex
   transport and not the mere presence of any evidence citations.
5. T5 is scoped to the dialogue benchmark path. `/codex` consultation events
   remain `server_assisted` in this slice.

This is the narrower truthful contract. Reusing `server_assisted` would require
either silently contradicting the current normative definition or broadening it
far enough that it stops distinguishing the cross-model helper loop from the
T-04 local ledger loop.

## 2. Why This Direction

The current cross-model mode definitions are mechanism-bound, not aspirational:

- [codex-dialogue.md](../../packages/plugins/cross-model/agents/codex-dialogue.md)
  starts in `server_assisted` specifically when the context-injection helper is
  available and falls back to `manual_legacy` when it is not.
- [dialogue-synthesis-format.md](../../packages/plugins/cross-model/references/dialogue-synthesis-format.md)
  defines `server_assisted` as the actual mode used when context-injection tools
  are available and `manual_legacy` as the fallback.

The T-04 benchmark-first candidate is structurally different from both:

- it does **not** use `process_turn` / `execute_scout`
- it does **not** have a helper-owned ledger or helper-owned convergence logic
- it **does** keep structured local state
- it **does** scout mid-dialogue with direct host tools

That means:

- it is not `manual_legacy`, because `manual_legacy` is explicitly the
  no-server, no-scout fallback
- it is not `server_assisted`, because the structured dialogue loop is not
  helper-mediated

The accurate dividing line is therefore ownership of the dialogue mechanism:

- who owns state and convergence computation?
- who chooses and executes scouting?
- is the agent consuming structured outputs from an external dialogue helper,
  or is it running the loop itself?

Under that boundary, T-04 is clearly a third case.

This also composes better with T4 than a scouting-capability definition would.
T4 may still refine scout timing, evidence schema, or citation projection, but
as long as scouting remains direct host-tool work inside the agent-local loop,
the mode stays `agent_local`. T4 does not need to preserve a fragile claim like
"this is still `server_assisted` because it scouts."

## 3. Mode Contract

### 3.1 `server_assisted`

`server_assisted` means:

1. a dialogue helper/service outside the agent owns structured turn processing,
   convergence state, or scout mediation
2. the agent consumes helper-produced structured outputs between turns
3. the helper boundary is part of the correctness model, not just an
   implementation detail

Current cross-model `process_turn` / `execute_scout` dialogue is the reference
instance of `server_assisted`.

### 3.2 `agent_local`

`agent_local` means:

1. the agent itself owns structured dialogue state between turns
2. the agent itself computes validation, counters, and control decisions from
   that local state
3. scouting, when it exists, is selected and executed directly by the agent via
   standard host tools rather than helper-issued scout instructions
4. no external dialogue helper/service is required to maintain the loop's
   correctness state

The T-04 benchmark-first candidate is the reference instance of `agent_local`.

### 3.3 `manual_legacy`

`manual_legacy` means:

1. no helper-owned structured loop
2. no agent-local structured ledger equivalent
3. no mid-dialogue scouting
4. continuation/conclusion managed by the fallback manual loop

This remains the degraded no-scout fallback, not a general label for any
non-helper dialogue.

### 3.4 Boundary Notes

- Mode describes dialogue-loop ownership, not whether Codex transport is MCP,
  CLI, or App Server.
- Mode also does not mean "how good was the evidence." A run with citations is
  not automatically `server_assisted`.
- A future transport migration may still need to revisit the mode taxonomy for
  consultation events, but that is separate from T-04's dialogue gate.

### 3.5 `mode_source` for `agent_local`

For `agent_local` dialogue outcomes, `mode_source` is `null`.

Rationale:

1. `mode_source` currently distinguishes values parsed from a dialogue agent's
   machine-readable epilogue (`"epilogue"`) from values supplied by parser
   fallback (`"fallback"`).
2. `agent_local` is not an inferred or parsed classification in T-04. It is a
   property of the loop implementation itself: if the conversation is running
   under the local structured loop, the mode is already known by orchestration
   state before any synthesis text is emitted.
3. Using `mode_source="epilogue"` for `agent_local` would be misleading even if
   the implementation emits a machine-readable block carrying the mode value.
   That block may transport the value, but it is not the authority that decides
   it.
4. Introducing a new `mode_source` enum such as `"direct"` is unnecessary for
   this slice. `null` already correctly means "no epilogue/fallback provenance
   applies."

Operational consequences:

- If a T-04 dialogue runs under the local structured loop and ends normally, it
  emits `mode="agent_local"` with `mode_source=null`.
- If that same loop terminates with an error after the local loop has started,
  it still emits `mode="agent_local"` with `mode_source=null`; the termination
  cause is carried by the structured termination fields, not by rewriting mode.
- If an implementation abandons the local loop before it starts and instead
  runs the degraded no-scout fallback for the conversation, that conversation
  is `manual_legacy`, not `agent_local`.

This keeps `mode_source` narrow: it remains a parser-provenance field for the
cross-model dialogue path, not a generic "how was mode decided?" taxonomy.

## 4. T-04 Candidate Classification

The benchmark-first T-04 loop should emit `agent_local` because it has all of
the properties below:

| Property | T-04 candidate | Implication |
|---|---|---|
| Structured local entries / counters / control state | Yes | Not `manual_legacy` |
| External helper computing dialogue state between turns | No | Not `server_assisted` |
| Direct host-tool scouting (`Glob` / `Grep` / `Read`) | Yes | Strong fit for `agent_local` |
| Manual degraded no-scout fallback | No | Not `manual_legacy` |

This remains true even if T4 changes the exact scout-capture point or evidence
record schema. Those are T4 questions. T5 only needs the more stable ownership
boundary.

If T6 later finds that the accepted T4 design reintroduces helper-mediated
scout direction or helper-owned state, T6 must reopen T5 rather than forcing
that result under `agent_local`.

## 5. Owning Layers

| Layer | Ownership under T5 |
|---|---|
| 4-6 dialogue contract surfaces | Define mode semantics and emitted value |
| 1-5 T-04 candidate loop | Emit `agent_local` when the loop is locally owned |
| Consultation path | Remains outside this decision except for shared enum acceptance |

This keeps T5 focused on dialogue-mode truthfulness without widening scope to a
full analytics taxonomy redesign.

## 6. Primary Migration Set

If T5 chooses `agent_local`, the primary migration set is:

| Layer | Surface | Location | Required change |
|---|---|---|---|
| Normative contract | Conversation summary mode definition | `packages/plugins/cross-model/references/dialogue-synthesis-format.md` | Document `agent_local` in the human-readable synthesis contract |
| Normative contract | Pipeline epilogue field | `packages/plugins/cross-model/references/dialogue-synthesis-format.md` | Add `agent_local` to the JSON epilogue contract |
| Schema | Enum definition | `packages/plugins/cross-model/scripts/event_schema.py` | Add `agent_local` to `VALID_MODES` |
| Producer contract | Dialogue skill pipeline | `packages/plugins/cross-model/skills/dialogue/SKILL.md` | Accept `agent_local` as a valid parsed mode; do not fall back when it is present |
| Test enforcement | Schema enum assertion | `packages/plugins/cross-model/tests/test_event_schema.py` | Assert `agent_local` is in `VALID_MODES` |
| Test enforcement | Analytics builder / validator | `packages/plugins/cross-model/tests/test_emit_analytics_legacy.py` | Add propagation and validation coverage for `agent_local`; keep invalid-mode rejection for truly unknown values |
| Test enforcement | Active parser fixtures | `packages/plugins/cross-model/tests/test_emit_analytics.py` | Add at least one synthesis fixture using `agent_local` |

Support-document follow-up, but not gate-blocking for T5 design acceptance:

- `packages/plugins/cross-model/HANDBOOK.md`
- `packages/plugins/cross-model/README.md`

Those should be updated in the implementation packet so operator guidance does
not drift after the contract change lands.

Deliberate non-migration for this slice:

- `packages/plugins/cross-model/agents/codex-dialogue.md`

That agent continues to define only the helper-mediated `server_assisted` path
and the degraded `manual_legacy` fallback. It will not emit `agent_local`.
`agent_local` is instead defined by this T5 decision and by the future T-04
candidate's own contract/runtime surfaces.

## 7. Explicit Non-Changes

T5 does **not** require code changes in these surfaces for the design to be
coherent:

| Surface | Location | Why no direct change is required |
|---|---|---|
| Required-field sets | `packages/plugins/cross-model/scripts/event_schema.py` | `mode` remains required for `dialogue_outcome` and `consultation_outcome`; only the enum expands |
| Hard validation logic | `packages/plugins/cross-model/scripts/emit_analytics.py` | Validation already delegates to `VALID_MODES`; adding the enum is sufficient |
| Dialogue outcome builder | `packages/plugins/cross-model/scripts/emit_analytics.py` | Builder already passes through parsed `mode`; it does not hardcode the allowed values |
| Consultation outcome builder | `packages/plugins/cross-model/scripts/emit_analytics.py` | `/codex` remains `server_assisted` in this slice |
| `/codex` skill | `packages/plugins/cross-model/skills/codex/SKILL.md` | T5 does not broaden consultation semantics or relabel `/codex` |
| Stats aggregation | `packages/plugins/cross-model/scripts/compute_stats.py` | `Counter` already handles new mode keys without code changes |
| Consultation contract note | `packages/plugins/cross-model/references/consultation-contract.md` | T5 does not change consultation-flow behavior; any future consultation taxonomy rewrite is separate |
| Delegation events | `packages/plugins/cross-model/scripts/event_schema.py` | `delegation_outcome` does not use `mode` and remains out of scope |

The important boundary is that "no direct change required" does **not** mean
"this surface is irrelevant." It means the surface still composes after the
enum expansion without needing its own contract rewrite in T5.

## 8. Rejected Alternatives

### A. Reuse `server_assisted`

Rejected because the current normative definition is tied to helper-mediated
dialogue, not just to "a conversation with evidence."

To make reuse work, T5 would have to redefine `server_assisted` away from the
cross-model mechanism that the docs currently describe. That would erase the
main distinction the field currently carries.

It is not enough to say "the mode describes scouting capability, and T-04 has
scouting." The benchmark-first candidate's scouting is direct host-tool work,
while `server_assisted` currently means the helper-directed `process_turn` /
`execute_scout` loop.

### B. Reuse `manual_legacy`

Rejected because `manual_legacy` is the degraded no-scout, no-helper fallback.
T-04 has a local ledger, structured control, and planned scouting. Calling that
`manual_legacy` would collapse the distinction between a benchmark candidate
with structured state and the existing degraded fallback path.

### C. Introduce a transport-specific value such as `cli_exec`

Rejected because T5 is about dialogue-loop semantics, not the transport used to
reach Codex. A transport label would be fragile under future runtime changes
and would still fail to capture the T4 composition question around scouting and
local state ownership.

### D. Split the field into multiple orthogonal fields now

Rejected for this slice because it widens the contract more than G4 requires.
T5 only needs to prevent a silent semantic lie in the current single-field
contract. A future analytics redesign can add richer transport/orchestration
dimensions if the benchmark proves that the current taxonomy is too coarse.

## 9. Verification Path

T5 should be considered complete only if the implementation demonstrates all of
the following:

1. A dialogue synthesis epilogue containing `mode="agent_local"` is accepted as
   valid and is not rewritten to `server_assisted`.
2. The dialogue analytics validator accepts `agent_local` and still rejects
   truly unknown values.
3. Existing `server_assisted` and `manual_legacy` fixtures continue to pass
   unchanged.
4. At least one T-04 candidate-style fixture or replay produces
   `mode="agent_local"` end to end.
5. Manual fallback remains `manual_legacy`, not `agent_local`, when the loop
   drops to the degraded no-scout path.
6. A baseline cross-model helper-mediated dialogue still emits
   `server_assisted`.
7. The mode definition in the synthesis contract matches the agent/gating docs
   and the analytics enum — no surface describes a different meaning.
8. `agent_local` dialogue outcomes emit `mode_source=null`, and that value is
   accepted by the analytics validator without introducing a new
   `VALID_MODE_SOURCES` enum value.

## 10. What T5 Does Not Decide

T5 resolves the mode taxonomy only. It does not:

- decide T4's final scout-capture point
- choose the exact evidence record schema
- choose consultation-event mode taxonomy beyond keeping `/codex` unchanged
- redesign analytics around separate transport and orchestration fields
- resolve T6 composition if later accepted gates fail to fit together

Those remain separate decisions.

## 11. Accepted Direction

Adopt `agent_local` as the T5 design direction.

The decisive reason is mechanism-level accuracy: the benchmark-first candidate
is a structured local dialogue loop with direct scouting, which is neither the
cross-model helper loop (`server_assisted`) nor the degraded fallback
(`manual_legacy`).

This is the higher-ceremony branch, but it is also the less misleading one.
If the project wants the cheaper reuse branch, it would need to first rewrite
the normative meaning of `server_assisted` so that it still draws a real
distinction after absorbing T-04. This draft does not find that rewrite
credible enough.
