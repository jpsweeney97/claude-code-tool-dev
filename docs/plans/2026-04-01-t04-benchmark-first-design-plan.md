# T-04 Benchmark-First Design Plan

Date: 2026-04-01
Ticket: [T-20260330-04](../tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md)
Risk register: [2026-04-01-t04-convergence-loop-risk-register.md](../reviews/2026-04-01-t04-convergence-loop-risk-register.md)
Benchmark contract: dialogue-supersession-benchmark.md (as of 2026-04-01, 8 tasks, 4 pass-rule metrics)

## 1. Current State

The design-side gate work is still correct, but the first executable verification cannot happen until there is a minimal candidate loop that can actually store ledger state, attach scout records, and emit synthesis fields. That means the pre-benchmark dry-run is not a pre-implementation gate; it is a post-minimal-implementation gate that should happen before the broader T-04 build-out. T-05, the full benchmark corpus, and broader parity work remain parked.

## 2. Dependency Map

- `T0: verify the benchmark contract pin still matches plan assumptions` - depends on: none
- `T1: resolve the structured termination contract` - depends on: T0
- `T2: resolve synthetic-claim handling and unresolved-closure accounting` - depends on: T0
- `T3: resolve deterministic referential continuity` - depends on: T2
- `T4: resolve the scouting position and evidence-retention contract` - depends on: T0
- `T5: resolve the mode strategy` - depends on: T0
- `T6: consolidate T1-T5 into one consistent benchmark-first design` - depends on: T1, T3, T4, T5
- `T7: define the minimal executable slice required for a real dry-run` - depends on: T6
- `T8: implement that minimal executable slice and run the pre-benchmark dry-run` - depends on: T7

## 3. Sequenced Plan

**Phase 0** (can start now):
- `T0: verify the benchmark contract pin still matches plan assumptions` - done when: the benchmark contract is confirmed unchanged from the pinned version, or drift is identified before design decisions continue

**Phase 1** (after Phase 0, parallelizable):
- `T1: resolve the structured termination contract` - done when: the user explicitly accepts the machine contract for termination and G1 is ready to move to `Accepted`
- `T2: resolve synthetic-claim handling and unresolved-closure accounting` - done when: the user explicitly accepts the fallback-claim and closure-diff rules and G2 is ready to move to `Accepted`
- `T4: resolve the scouting position and evidence-retention contract` - done when: the user explicitly accepts the scout-capture point, evidence-record shape, and provenance-debt model and G3 is ready to move to `Accepted`
- `T5: resolve the mode strategy` - done when: the user explicitly accepts reuse vs. migration and G4 is ready to move to `Accepted`

**Phase 2** (after T2):
- `T3: resolve deterministic referential continuity` - done when: the user explicitly accepts the continuity mechanism and its documented non-goals, and G5 is ready to move to `Accepted`

**Phase 3** (after T1, T3, T4, T5):
- `T6: consolidate T1-T5 into one consistent benchmark-first design` - done when: the accepted gates compose into a single coherent state model, loop structure, and synthesis contract; if they do not, the conflicting gates are reopened
  - **Closed 2026-04-06.** State model and loop structure compose. Remaining synthesis-contract consolidation is routed work — see [administrative close](../reviews/2026-04-04-t04-t6-benchmark-first-design-composition-review.md#t6-administrative-close-2026-04-06) for ownership details. All F6/F7/F11 wire-format blockers resolved (PRs #93, #94).

**Phase 4** (after T6):
- `T7: define the minimal executable slice required for a real dry-run` - done when: there is an agreed smallest buildable slice that can execute one dialogue and expose the fields the dry-run must inspect

**Phase 5** (after T7):
- `T8: implement that minimal executable slice and run the pre-benchmark dry-run` - done when: one real dialogue has been executed against the agreed pass criteria and the project either has a green light for the broader implementation packet or a precise list of gates/design controls to reopen

## 4. Decision Gates

- `After T0: if the benchmark contract drifted, re-rank the plan before more gate work; otherwise continue.`
- `After T3: if referential continuity is credible enough for benchmark use, continue to consolidation; otherwise narrow the accepted non-goals or reopen the continuity decision.`
- `After T5: if an existing mode can be reused with a defensible rationale, avoid migration; otherwise expand the design to include the contract updates.`
- `After T6: if the accepted gates do not compose, reopen the conflicting gates before defining the executable slice.`
- `After T8: if the real dry-run passes, proceed to the broader T-04 implementation packet; otherwise route the failure back to the specific gate or design-control task it invalidates.`

## 5. Critical Path

**Scheduling:** `T2 -> T3 -> T6 -> T7 -> T8`

**Highest-risk task:** `T3` - likelihood: high; impact: high; on critical path: yes; why: deterministic referential continuity is still the hardest unresolved decision and the most likely reason the design needs an extra loop before it can stabilize.

## 6. Out of Scope (Parked)

- T-05 execution-domain work unless T-04 exposes a real dependency on it
- The full benchmark corpus before T8 passes
- Phase support and broader parity work beyond the benchmark-first candidate
- Analytics dashboard and cutover work after the benchmark result
- Routine repo-operational cleanup unless it starts blocking coordination

## Session Sketch

- Session 1: `T0`, `T2`, start `T1`
- Session 2: `T3`, finish `T1`, start `T4` or `T5`
- Session 3: finish `T4` and `T5`
- Session 4: `T6` adversarial composition pass
- Session 5: `T7` plus the minimal executable slice work if the slice is small enough
- Session 6: `T8` real dry-run, then only if clean, move into the broader implementation packet

If session 5 can both define and complete the minimal slice, sessions 5 and 6 may collapse. Otherwise assume 6 before the broader build starts.
