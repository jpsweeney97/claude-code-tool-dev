# Packet 1 Carry-Forward Tracker

Running list of deferred items discovered during execution of Packet 1 (T-20260423-02). Items are appended as they're found and removed when resolved. Intent: prevent indefinite accumulation (handoff Risk: "By Task 22 we may have 30+ deferred items").

**Scope:** Minor findings that are non-blocking for the current task but should be addressed at an appropriate later point. Critical and Important findings are fixed in-scope, never carried forward.

**When to sweep:** End-of-phase polish, or when a later task naturally touches the same area.

---

## Open items

### From Phase A (originally in prior handoff)

| # | Item | Lands at / How to resolve | Source |
|---|---|---|---|
| A1 | Task 15 catch site for `_WorkerTerminalBranchSignal` must log `signal.reason` not `str(signal)` — the `@dataclass(frozen=True)` exception has empty `args`, so `str(signal) == ""` | When Task 15 implements the catch site | Phase A handoff |
| A2 | Task 16 raise sites: absorb caller-contract docs from the sentinel class into the raise-site comments | When Task 16 lands the 6 raise sites | Phase A handoff |
| A3 | Task 14 `_project_request_to_view` rewrite will resolve the expected Pyright error at `delegation_controller.py:~965` (`PendingRequestKind` vs. `EscalatableRequestKind` at construction site) | When Task 14 lands the runtime guard | Phase A handoff |
| A4 | Unused `import pytest` in Task 3 and Task 4 test files | End-of-phase polish (below threshold per user policy) | Phase A code review |
| A5 | Class-level annotation style on `DelegationStartError` (`reason: str`, `cause: Exception \| None`) is style-divergent from `replay.py`'s exception classes | Design discussion at end-of-phase | Phase A code review |

### From Phase B Task 6

| # | Item | Lands at / How to resolve | Source |
|---|---|---|---|
| B6.1 | `test_has_resolution_action_field` is redundant with `test_default_values_are_safe` — both assert `req.resolution_action is None` on a default-constructed instance. Consider removing or repurposing to test a non-default value | End-of-phase polish | Task 6 code quality review |
| B6.2 | Inline `import json` inside `test_existing_records_replay_cleanly_with_none_defaults` and `test_new_fields_survive_update_status_roundtrip` — style-divergent from module-level imports used elsewhere in the file | End-of-phase polish | Task 6 code quality review |

### From Phase B Task 7

| # | Item | Lands at / How to resolve | Source |
|---|---|---|---|
| B7.1 | Unused `import pytest` in `test_pending_request_store_mutators.py` (no `pytest.*` symbol used in file) — same pattern as A4 | End-of-phase polish | Task 7 code quality review |
| B7.2 | Variable name inconsistency in `_replay`: `update_status` branch uses `req_id`; the 3 new branches (`mark_resolved`, `record_response_dispatch`, `record_protocol_echo`) use `rid`. Normalize on a future polish pass | End-of-phase polish | Task 7 code quality review |

### From Phase B Task 8

| # | Item | Lands at / How to resolve | Source |
|---|---|---|---|
| B8.1 | Style asymmetry between `record_response_dispatch` replay (line 294, reads `dispatch_result=record.get(...)`) and `record_dispatch_failure` replay (line 327, hardcodes `dispatch_result="failed"`). Both mutators write the value unconditionally, so behavior matches under normal flow; under hand-edit JSONL corruption the read-path drifts to `None` while the hardcode stays `"failed"`. Tautological-but-safe; pick one style on a future pass. | End-of-phase polish | Task 8 code quality review |
| B8.2 | No explicit reopen round-trip tests for `record_timeout` and `record_dispatch_failure` in `test_pending_request_store_atomic_mutators.py`. Only `test_record_internal_abort_round_trip_via_replay` instantiates a fresh `PendingRequestStore` to force file-open replay; the other two paths exercise replay via same-instance `store.get()`. Same `_replay()` code path; gap is the `__init__` (mkdir + store_path) coverage, already exercised by the abort round-trip. | End-of-phase test polish | Task 8 code quality review |

---

## Closed items

_(Move items here when resolved, with the commit SHA that resolved them)_

### From Phase B Task 6

- **[Resolved `3fbba140`]** `update_status` replay branch silently dropped 11 new fields. Originally triaged as carry-forward; code quality review upgraded to Critical-in-Task-6-scope. Fixed via `dataclasses.replace` + round-trip test.

### From Phase B Task 7

- **[Resolved `b623548b`]** `record_protocol_echo` replay branch crashed all store reads on `protocol_echo_signals: null` JSONL records (`tuple(None)` raises `TypeError`). Code quality reviewer flagged as Important I-1; fixed in-scope per Phase A protocol via `record.get(...) or ()` plus null-injection regression test.

### From Phase B Task 9 + closeout

- **[Resolved `c6bf834c`]** `DelegationJobStore._replay` used `asdict(existing)` + dict-spread, recursively coercing `artifact_paths` from `tuple` to `list` before reconstructing `DelegationJob`. Python doesn't runtime-validate generic types, so the dataclass silently accepted the list, violating the `tuple[str, ...]` field contract on every normal-path `update_status` / `update_status_and_promotion` / `update_promotion_state` replay. Symptom was bounded — one spurious `update_artifacts` write per poll at `delegation_controller.py:988` — but the type-contract violation was load-bearing for Phase B's replay-preservation principle. Discovered by Task 9 code-quality reviewer (P1, Important — pre-existing). Fixed in Phase B closeout by migrating all five replay branches to `dataclasses.replace()`, plus three regression tests asserting `type(retrieved.artifact_paths) is tuple` after each affected branch's replay. Same closeout commit also bundled Task 9 cleanup: `jid` → `job_id` rename and `isinstance(job_id, str)` guard for symmetry with the migrated branches (covers what would otherwise have been B9.1/B9.2/B9.3 carry-forward items).

---

## How to add an item

Append to the appropriate "Open items" subsection with:
- **#**: stable identifier (phase-letter + task number + sequence, e.g., `B6.3`)
- **Item**: one-sentence description of the finding
- **Lands at / How to resolve**: natural resolution point
- **Source**: where it was found (review, dispatch, etc.)

When resolving, move the row to "Closed items" and append the resolving commit SHA in brackets.
