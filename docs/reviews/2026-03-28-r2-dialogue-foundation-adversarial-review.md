# Adversarial Review: R2 Dialogue Foundation Implementation Plan

## Top Findings

1. **[blocking] The operation journal payload is too thin to support deterministic replay.**
   The proposed `OperationJournalEntry` stores only `idempotency_key`, `operation`, `collaboration_id`, and `created_at`. That is not enough to replay `thread_creation` or `turn_dispatch`, nor to check whether the operation already completed after a crash. The recovery contract says replay must check outcome instead of guessing.

2. **[blocking] The plan claims the idempotent replay acceptance gate is covered, but it is not.**
   The tests only prove that a journal entry survives a simulated crash before trim. They do not prove replay, deduplication, or crash recovery orchestration. The plan explicitly defers `recover_pending_operations`, which leaves one of the R2 acceptance gates unmet.

3. **[high] `turn_sequence` is computed from in-memory controller state even though the contract requires `thread/read` derivation after crash recovery.**
   This breaks both the public `Dialogue Reply` contract and the turn-dispatch idempotency key. Any controller restart within the same session can reset numbering and produce duplicate or inconsistent sequences.

4. **[high] Journal trimming is crash-unsafe and can silently drop unrelated pending operations.**
   The proposed `trim_operation()` rewrites the entire session journal in place without temp-file replace or `fsync`. A crash during trim can truncate the journal and erase other in-flight operations that recovery still needs.

5. **[moderate] The plan quietly widens the audit schema with `dialogue_start`.**
   The current contracts enumerate `dialogue_turn` but not `dialogue_start`. The plan and tests add a new action without first changing the contract, which recreates the same spec drift this repo just spent a session removing.

## 1. Assumptions Audit

- **`ControlPlane.get_advisory_runtime()` is the right shared seam for dialogue work** - `plausible`. If wrong, dialogue runtime handling will fork from consult semantics and duplicate bootstrap, invalidation, and stale-context logic.
- **The consult packet builder and consult output schema can be reused unchanged for dialogue turns** - `validated` by the current R2 response-shape contract. If wrong, dialogue will either return the wrong shape or require a second prompt pipeline late in implementation.
- **A four-field `OperationJournalEntry` is enough for crash recovery replay** - `wishful`. If wrong, replay becomes impossible or guess-based, which defeats the whole journal contract.
- **Presence of a pending journal entry is equivalent to idempotent replay coverage** - `wishful`. If wrong, the test suite will go green while crash recovery still duplicates work or strands pending entries.
- **An in-memory turn counter is acceptable until later recovery work lands** - `wishful`. If wrong, controller restarts within the same session violate the contract immediately, not just in a future recovery enhancement.
- **Thread creation can be recovered without storing more outcome metadata** - `wishful`. If wrong, a crash after `thread/start` but before lineage persistence creates orphaned threads and duplicate starts.
- **A synchronous stdio loop is sufficient evidence of MCP serialization** - `plausible`. If wrong, the implementation passes unit tests but fails when exercised by a real client or by re-entrant request patterns.
- **`dialogue.start` should emit a dedicated audit action** - `wishful`. If wrong, the implementation bakes in contract drift and downstream consumers either ignore or misclassify the event.
- **Session cleanup via `cleanup()` is enough lifecycle coverage for the lineage store** - `plausible`. If wrong, stale session directories accumulate because startup pruning is never wired into control-plane lifecycle.

## 2. Pre-Mortem

1. **Most likely failure:** a crash lands after `turn/start` but before `trim_operation()`. On restart the journal still contains a pending `turn_dispatch`, but the entry does not record enough information to determine whether the turn already ran or how to replay it safely. The recovery path guesses, re-dispatches, or does nothing. Users then see duplicate turns, skipped turns, or hanging pending state with no single loud failure.

2. **Most damaging quiet failure:** a successful turn trims one journal key while another operation is still pending. The process crashes during the in-place rewrite in `trim_operation()`, truncating the file. Recovery now "forgets" unrelated in-flight work. Nothing crashes immediately; the system just stops being able to explain or recover a subset of operations, which is exactly the kind of silent state corruption the journal was supposed to prevent.

## 3. Dimensional Critique

### Correctness

- The journal design does not satisfy the stated semantics in [recovery-and-journal.md](../superpowers/specs/codex-collaboration/recovery-and-journal.md). Replay requires enough information to check outcome and continue deterministically; the plan stores too little.
- `turn_sequence` is wrong by construction after controller restart. The contract requires derivation from completed turn count via `thread/read`; the plan uses an in-memory counter.
- The `dialogue_start` audit action is a contract violation. It is not listed in the current audit action enum.
- The "serialized dispatch" test is not actually a serialization test. It invokes requests serially in a for-loop and therefore cannot detect queueing or concurrency bugs.
- The "invalidate runtime on thread failure" test is mislabeled. It injects `initialize_error`, which exercises bootstrap failure, not a `thread/start` failure after cache establishment.

### Completeness

- There is no explicit recovery task that scans pending journal entries and reconciles them with actual thread state.
- There is no plan for the crash window after `thread/start` succeeds but before `LineageStore.create()` persists the handle.
- There is no startup-pruning task for stale lineage session directories even though the lineage-store contract names it.
- There is no explicit wiring for `update_runtime()` during advisory runtime crash recovery or rotation, even though that is part of the contract.
- `dialogue.read` does not define how incomplete, failed, or non-JSON agent messages should be represented beyond a lossy fallback.

### Security / Trust Boundaries

- The new surface is mostly local-tooling, so there is no major new remote attack boundary here.
- Two trust edges are still thin: MCP handlers accept raw caller arguments without schema-level runtime validation, and `dialogue.read` may surface raw `agentMessage` content outside the normal redaction pipeline when parsing fails.

### Operational

- The crash-recovery story is not operationally credible yet. The plan proves only persistence of pending journal entries, not that 3 AM recovery will converge safely.
- In-place journal trimming is an operational footgun because it risks deleting unrelated recovery state during the act of cleanup.
- Observability is weak around pending journal backlog, replay attempts, and lineage/session cleanup. When this fails, operators will have to infer state from files rather than inspect first-class metrics or states.

### Maintainability

- The plan splits advisory runtime responsibilities between `ControlPlane` and a new `DialogueController`, but recovery, invalidation, and stale-context rules still fundamentally live in `ControlPlane`. That raises the odds of parallel semantics drifting.
- The plan imports test fixtures from `tests.test_control_plane` into other tests instead of moving shared doubles cleanly into `conftest.py`, which hardens cross-test coupling.
- The header still references nonexistent sub-skills, repeating a documentation hygiene issue the previous session already had to clean up.

### Alternatives Foregone

- The strongest alternative is to keep dialogue recovery, journaling, and runtime remapping inside `ControlPlane`, and let `DialogueController` be a thin facade over typed request/response handling. That would keep one owner for advisory runtime state instead of creating a second orchestrator.
- A second strong alternative is an append-only journal with tombstones or atomic compaction, instead of in-place rewrite trimming. It is more boring, but it aligns better with the journal's role as crash-recovery state.
- For MCP scaffolding, a protocol-harnessed implementation or a proven MCP library would trade some purity for much stronger interoperability guarantees than a hand-rolled loop.

## 4. Severity Summary

1. **[blocking] Journal entries are not replayable** - redesign the entry schema so each operation carries enough input and outcome-correlation data to support deterministic replay.
2. **[blocking] The replay acceptance gate is not actually implemented or tested** - add an explicit recovery task and tests for crash-after-dispatch, crash-before-trim, and restart reconciliation.
3. **[high] `turn_sequence` breaks after controller restart** - derive it from `thread/read` completed turns before dispatch, per the contract.
4. **[high] `trim_operation()` is crash-unsafe** - replace in-place rewrite with atomic rewrite or append-only tombstones plus safe compaction.
5. **[moderate] `dialogue_start` is a quiet spec expansion** - either remove it from R2 or change the contracts first and then implement it.

## 5. Confidence Check

**2** - The plan has a workable spine, but the crash-recovery and replay mechanics are not specified strongly enough to justify implementation as written.

Raise this to **4** by redesigning the operation journal around replayable entries, adding explicit recovery orchestration and tests, deriving `turn_sequence` from `thread/read`, and removing contract drift such as `dialogue_start` unless the spec is updated first.

## Re-review Update

The original five findings are addressed, and the two earlier follow-up issues were fixed. One stale integration inconsistency remains.

1. **[moderate] Integration test still expects the pre-resume thread ID after recovery.**
   The updated recovery path correctly performs `thread/read` + `thread/resume` and persists the resumed thread identity, and the focused recovery tests assert that behavior. But the integration section still contains an older expectation that recovered `thread_creation` uses `thr-orphan` rather than `thr-orphan-resumed`. The implementation plan is therefore not yet internally consistent end-to-end.

### Re-review Confidence

**4** - Probably works. The core recovery design is now coherent, but fix the stale integration assertion before calling the plan implementation-ready.
