## Adversarial Review: Conservative `run_turn` Quarantine + Durable Parse-Failure Finalization

### 1. Assumptions Audit
- **A `run_turn()` exception that later proves committed only needs TurnStore + journal repair** - `wishful`. If this is wrong, the system silently loses the required `dialogue_turn` audit record even though the turn crossed the trust boundary. The plan's repair helper only writes TurnStore and journal completion, while the normative audit contract says every dialogue turn dispatch emits `dialogue_turn`.
- **`status == "unknown"` is specific enough to decide which handles are safe to auto-reattach** - `wishful`. If this is wrong, startup recovery can reactivate handles that were quarantined for unrelated or future failure modes, because the plan keys eligibility off a coarse lifecycle bit instead of provenance.
- **Changing startup recovery semantics without updating the normative specs is acceptable** - `wishful`. If this is wrong, the implementation and the contract will disagree immediately: the current contract says startup recovery enumerates `active` handles, while the plan intentionally widens that to `unknown`.
- **Catching only `ValueError` and `AttributeError` is sufficient to preserve the committed-turn parse semantics** - `plausible`. If this is wrong, a future parse/projection failure type will escape as a raw post-commit exception, and callers will get inconsistent guidance for the same "turn already committed" condition.
- **The proposed test matrix is enough to lock in the intended behavior** - `plausible`. If this is wrong, the plan can merge with its headline semantics seemingly covered while the audit gap and contract drift remain untested. The file map is already inconsistent with the actual test additions, which is a warning sign.

### 2. Pre-Mortem
1. **Most likely failure:** the `run_turn()`-failure repair path ships exactly as written, a later confirmed turn gets TurnStore metadata and a completed journal phase, `read()` starts working again, and nobody notices that the required `dialogue_turn` audit event was never emitted. Two weeks later an incident review tries to reconstruct what Codex actually did and the audit trail is missing the very turn the plan claims it durably recovered.
2. **Most damaging quiet failure:** a handle lands in `unknown` for a reason outside this new reply-time path, but startup recovery now treats all `unknown` handles with complete metadata as eligible for reattach. The handle is silently promoted back to `active`, subsequent replies continue on top of a state that was supposed to stay quarantined, and the system creates a correctness bug that looks like ordinary post-restart continuation.

### 3. Dimensional Critique
#### Correctness
The biggest correctness hole is the confirmed-repair branch in Task 2. The helper at the center of the plan writes TurnStore metadata and a `completed` journal phase, but it never emits the `dialogue_turn` audit event the specs require for every dispatched dialogue turn. That means the plan restores read-path integrity while still leaving the system durably inconsistent on the audit side.

The startup widening in Task 5 also leans too hard on `unknown` as if it were a reason code. In the current contract, `unknown` means "state uncertain," not "safe to reattach once metadata is complete." The plan turns that coarse state into an eligibility signal. That works for the specific reply-time quarantine it is trying to add, but it is not semantically stable for other `unknown` causes.

The parse branch is directionally right, but the wrapper around `parse_consult_response()` is narrower than the new semantics imply. Once the plan declares "the turn is committed; projection failed," the boundary should be robust against future parser/projection exceptions, not only the current `ValueError`-shaped ones.

#### Completeness
The plan changes the recovery contract but does not schedule any normative spec update. The file map explicitly says no changes to models, journal, lineage store, control plane, or prompt builder, and it does not mention [contracts.md](/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/contracts.md) or [recovery-and-journal.md](/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/recovery-and-journal.md), even though the current contract still says startup recovery enumerates `active` handles.

The test plan is also incomplete in the place that matters most: it adds no test that a confirmed `run_turn()` repair emits the missing audit event. That omission is not cosmetic. It is the difference between "all durable state repaired" and "read works but the audit contract is broken."

The execution plan is internally inconsistent about its own scope. The file map says `tests/test_dialogue.py` gets 6 new tests, but Tasks 2, 3, and 4 together actually prescribe 10 new tests there. That is not fatal by itself, but it shows the plan is already drifting at the inventory level before implementation starts.

#### Security / Trust Boundaries
No new external trust boundary is introduced beyond existing advisory-runtime and MCP error-surfacing paths. Skipping further security-specific review here.

#### Operational
The broadened startup recovery path can produce repetitive reattach attempts on persistent `unknown` handles, and the plan accepts that as out of scope. That is survivable, but it means the operational behavior after deployment may be noisy and difficult to distinguish from legitimate recovery.

The plan also gives no observability hook for why an `unknown` handle was reactivated. Once Task 5 ships, "became active again" could mean "reply-time quarantine later proved safe" or "some unrelated unknown state happened to satisfy the generic metadata check."

#### Maintainability
The plan duplicates the turn-confirmation rule and journal-repair logic in a new private helper instead of carving out a shared primitive with explicit policy differences. That may be the right short-term tradeoff, but it raises the risk that `_best_effort_repair_turn()` and `_recover_turn_dispatch()` drift apart in subtle ways while still looking "basically the same."

Overloading `unknown` as both a quarantine outcome and a future reattach candidate also makes the lifecycle harder to reason about. The more code paths that write `unknown`, the less obvious Task 5's generic reactivation rule becomes.

#### Alternatives Foregone
The strongest alternative not chosen is to introduce an explicit quarantine reason or recovery-eligibility bit instead of inferring eligibility from `status == "unknown"`. That would preserve the conservative reply semantics without making every present and future `unknown` handle look alike at startup.

### 4. Severity Summary
1. **[blocking] Confirmed reply-time repair omits the required `dialogue_turn` audit event** - add explicit audit behavior and coverage for the confirmed-turn repair path before implementation proceeds.
2. **[high] The plan changes startup recovery semantics without updating the normative contract** - update the recovery spec alongside the implementation so `unknown`-handle reattach is an intentional, documented rule rather than immediate spec drift.
3. **[moderate] Task 5 treats all `unknown` handles as candidates for auto-reattach** - narrow eligibility with provenance or an explicit predicate so startup does not reactivate unrelated quarantine states.
4. **[moderate] The test plan misses the highest-value regression and is already internally inconsistent** - add the missing audit assertion and reconcile the file-map/test-count drift before handing this to an implementer.

### 5. Confidence Check
**3** - The core direction is workable, but the plan is not ready to execute as written because it leaves one normative audit requirement unspecified and broadens recovery semantics more loosely than the current lifecycle model supports.

Raise this to 4 by specifying and testing the audit behavior for confirmed `run_turn()` repairs, updating the normative recovery docs to match the new `unknown` semantics, and narrowing startup reattach eligibility so it is not keyed off raw `unknown` status alone.
