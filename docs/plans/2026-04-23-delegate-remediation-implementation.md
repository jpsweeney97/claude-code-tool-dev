# T-20260423-01: Delegate Remediation Implementation Plan

## Overview

| Attribute | Value |
|-----------|-------|
| Ticket | T-20260423-01 |
| Branch | `feature/delegate-remediation-sandbox-approval` |
| Dependency | T-20260423-01 ticket merged (PR #124 at `005d4b44`) |
| Authority | Ticket at `docs/tickets/2026-04-23-codex-collaboration-delegate-execution-remediation.md` |
| Type | Defect fix (sandbox policy + approval handler + state machine) |

## Diagnostic Evidence

Phase 1 and 2 diagnostics completed in-conversation. Key findings:

| Finding | Source | Evidence |
|---------|--------|----------|
| `includePlatformDefaults: True` is curated, not full-access | [OpenAI App Server docs](https://developers.openai.com/codex/app-server#sandbox-read-access-readonlyaccess) | "curated platform-default Seatbelt policy...without broadly allowing all of /System" |
| `accept` resumes action inline, `cancel` denies + interrupts | Vendored schemas at `tests/fixtures/codex-app-server/0.117.0/` | Schema descriptions for each decision value |
| `fullAccess` default allows reading `~/.ssh`, `~/.config/gh` | Empirical test with `codex sandbox macos --full-auto` | `~/.config/gh/hosts.yml` readable, `~/.ssh/` listable |
| `approval_policy="untrusted"` triggers requests regardless of sandbox | [OpenAI config reference](https://developers.openai.com/codex/config-reference) | "Controls when Codex pauses for approval" |
| `_finalize_turn` marks `needs_escalation` based on `captured_request.kind`, not turn outcome | `delegation_controller.py:1473` | Unconditional check against `_CANCEL_CAPABLE_KINDS` |

## Design Model

### Three-category handler response

| Category | Request shape | Handler response | State effect |
|----------|---------------|------------------|-------------|
| **Inline accept** | `command_approval`/`file_change` within delegation boundary, `accept` in `available_decisions` | `{"decision": "accept"}` | No `captured_request` set; turn continues; job completes normally |
| **Fail closed** | `command_approval`/`file_change` with boundary-crossing fields OR `accept` not in `available_decisions` | `{"decision": "cancel"}` | `captured_request` set; turn interrupted; job `needs_escalation`; view advertises `("deny",)` only; `decide(approve)` returns typed rejection |
| **Unknown/interrupt** | Unknown method, parse failure | `None` (interrupt) | Existing behavior preserved |
| **User input** | `request_user_input` | `{"answers": {}}` | Existing behavior preserved; `decide(approve)` valid with answers |

### Why `decide(approve)` must reject for fail-closed command/file approvals

`cancel` interrupts the original App Server request. A later `decide(approve)` starts
a NEW turn with a natural-language resume prompt. The new turn retries the same action,
App Server asks again, the handler cancels again — the existing cancel-retry loop under
a new name.

`decide(approve)` remains valid for:
- **Unknown kinds**: the new turn carries NL instruction (a different model from wire-level grant)
- **`request_user_input`**: approve with answers is a data-passing mechanism, not a wire grant

For command/file approvals, `decide` returns a `DecisionRejectedResponse` with reason
`"request_not_approvable"` rather than raising an exception. This follows the existing
typed rejection contract (`_reject_decision` pattern, `DecisionRejectedReason` Literal).

### Boundary validation rules

Explicit field checks against the delegation worktree boundary:

| Request kind | Field | In-boundary when |
|---|---|---|
| `command_approval` | `networkApprovalContext` | Absent or `null` |
| `command_approval` | `cwd` | Absent, `null`, or absolute path under `worktree_path` |
| `file_change` | `grantRoot` | Absent, `null`, or absolute path under `worktree_path` |

Path validation constraints:
- **Null/absent**: in-boundary (no expanded scope requested)
- **Absolute path**: resolve and check `is_relative_to(worktree_path.resolve())`
- **Relative path**: out-of-boundary (fail closed — cannot resolve safely against ambient cwd)
- **Resolution errors** (symlink loops, OS errors): out-of-boundary (fail closed)

Do NOT use fuzzy key-pattern matching. Validate only documented fields. Unknown request
methods already escalate through the existing unknown-kind path.

### `available_decisions` gating

The handler must verify `"accept" in parsed.available_decisions` before returning accept.
The file-change fallback in `approval_router.py:31` is currently `()` — update to match
the vendored schema: `("accept", "acceptForSession", "decline", "cancel")`.

## Changes

### Group 1: Sandbox policy (isolated, no dependencies)

**File: `server/runtime.py:33`**

```python
# Before
"includePlatformDefaults": False,
# After
"includePlatformDefaults": True,
```

**File: `tests/test_runtime.py:178`**

Update expected value in `test_build_workspace_write_sandbox_policy_restricts_reads_and_writes`.

### Group 2: Approval router — file-change fallback and boundary validation

**File: `server/approval_router.py`**

1. Update `_AVAILABLE_DECISIONS["file_change"]` from `()` to
   `("accept", "acceptForSession", "decline", "cancel")` to match vendored schema.

2. Add boundary validation function:

```python
def is_within_delegation_boundary(
    parsed: PendingServerRequest,
    worktree_path: Path,
) -> bool:
```

Logic:
- If `parsed.kind == "command_approval"`:
  - Reject if `requested_scope` contains non-null `networkApprovalContext`
  - Reject if `requested_scope` contains `cwd` that is non-null, non-absolute, or outside worktree
- If `parsed.kind == "file_change"`:
  - Reject if `requested_scope` contains `grantRoot` that is non-null, non-absolute, or outside worktree
- All other kinds: return `False` (only cancel-capable kinds are boundary-checkable)

Extract path validation into `_is_path_within_boundary(value, worktree_path) -> bool`:
- `None` → `True` (absent/null — no expanded scope)
- Non-string → `False` (unexpected type — fail closed)
- Relative path → `False` (fail closed)
- Absolute path → `Path(value).resolve().is_relative_to(worktree_path.resolve())`
- Wrap in try/except for resolution errors → `False`

### Group 3: Handler restructure and state machine

**File: `server/delegation_controller.py`, `_execute_live_turn` method**

Restructure `_server_request_handler` closure (lines 650-720):

1. Add closure variable: `inline_accepted_requests: list[PendingServerRequest] = []`

2. For `_CANCEL_CAPABLE_KINDS`, replace unconditional `cancel` with:

```python
if parsed.kind in _CANCEL_CAPABLE_KINDS:
    if (
        "accept" in parsed.available_decisions
        and is_within_delegation_boundary(parsed, worktree_path)
    ):
        inline_accepted_requests.append(parsed)
        return {"decision": "accept"}
    # Out-of-boundary or accept not available — escalate.
    if captured_request is None:
        self._pending_request_store.create(parsed)
        captured_request = parsed
    return {"decision": "cancel"}
```

3. Pass `inline_accepted_requests` to `_finalize_turn` for audit (new parameter).

**Key invariant:** `captured_request` is ONLY set when the handler escalates. Inline-accepted
requests do not set it. `_finalize_turn`'s existing logic at line 1473 then works unchanged:
- `captured_request is None` + turn completed → `completed` (line 1520)
- `captured_request` set + kind in `_CANCEL_CAPABLE_KINDS` → `needs_escalation` (line 1473)

### Group 4: `_finalize_turn` — inline-accept audit

**File: `server/delegation_controller.py`, `_finalize_turn` method**

1. Add parameter: `inline_accepted_requests: list[PendingServerRequest]`

2. Emit inline-accept audit events in a dedicated helper called at the top of
   `_finalize_turn`, before any state-transition logic or conditional branch:

```python
def _emit_inline_accept_audit(
    self,
    *,
    inline_accepted_requests: list[PendingServerRequest],
    collaboration_id: str,
    runtime_id: str,
    job_id: str,
) -> None:
    for accepted in inline_accepted_requests:
        try:
            self._journal.append_audit_event(
                AuditEvent(
                    event_id=self._uuid_factory(),
                    timestamp=self._journal.timestamp(),
                    actor="system",
                    action="inline_accept",
                    collaboration_id=collaboration_id,
                    runtime_id=runtime_id,
                    job_id=job_id,
                    request_id=accepted.request_id,
                )
            )
        except Exception:
            logger.warning(
                "Inline-accept audit emission failed for request %s",
                accepted.request_id,
                exc_info=True,
            )
```

`actor="system"` is a valid `AuditEvent.actor` value (`Literal["claude", "codex", "user", "system"]`).
Audit is best-effort: failure to emit does NOT affect job status or turn outcome.
The try/except ensures a journal write error cannot prevent the method from returning
the correct state transition result.

**Placement:** Call this helper at the top of `_finalize_turn`, before any state-transition
logic or conditional branch. The intent is: record what the handler decided even if
finalization later fails or takes a different branch (e.g., a later fail-closed request
causes escalation after earlier inline accepts). Audit of handler decisions precedes
and is independent of job-state derivation.

**Scope limitation:** Inline-accept audit only covers requests where `_finalize_turn` is
reached — i.e., `run_execution_turn` returned a `TurnExecutionResult`. If
`run_execution_turn` raises before returning (transport failure, timeout), the handler
may have accepted requests at the wire level but `_finalize_turn` is never called, so
inline-accept audit events are not emitted. This is acceptable: the handler accepted
inline (App Server acted on it), but no durable turn result exists to finalize. The
handler's wire-level accept is the authority; audit is observability, not enforcement.

```python
def _finalize_turn(self, *, ..., inline_accepted_requests, ...):
    # 1. Audit inline-accepted requests (best-effort, pre-state-transition).
    self._emit_inline_accept_audit(
        inline_accepted_requests=inline_accepted_requests,
        collaboration_id=collaboration_id,
        runtime_id=runtime_id,
        job_id=job_id,
    )
    # 2. Existing state-transition logic follows unchanged...
    if captured_request is not None:
        ...
```

### Group 5: `decide(approve)` guard for cancel-capable kinds

**File: `server/models.py`**

Add `"request_not_approvable"` to `DecisionRejectedReason`:

```python
DecisionRejectedReason = Literal[
    "invalid_decision",
    "job_not_found",
    "job_not_awaiting_decision",
    "request_not_found",
    "request_job_mismatch",
    "request_already_decided",
    "runtime_unavailable",
    "answers_required",
    "answers_not_allowed",
    "request_not_approvable",  # NEW
]
```

**File: `docs/superpowers/specs/codex-collaboration/contracts.md:297`**

Add `request_not_approvable` to the `Decision Rejection.reason` enum in the
caller-facing contract table.

**File: `server/delegation_controller.py`, `decide` method**

After the answers validation block (line ~1649) and before the runtime lookup (line ~1651),
add the cancel-capable guard. Uses the existing `_reject_decision` pattern (returns
`DecisionRejectedResponse`, does not raise):

```python
_CANCEL_CAPABLE_KINDS = frozenset({"command_approval", "file_change"})

if decision == "approve" and request.kind in _CANCEL_CAPABLE_KINDS:
    return self._reject_decision(
        reason="request_not_approvable",
        detail=(
            f"Delegation decide failed: cannot approve a {request.kind} "
            "request after wire-level cancel. The original App Server request "
            "was interrupted; a new turn cannot grant it. Use 'deny' or discard."
        ),
        job_id=job_id,
        request_id=request_id,
    )
```

### Group 5b: `PendingEscalationView` projection for fail-closed requests

**File: `server/delegation_controller.py`, `_project_request_to_view` method**

Currently `_PLUGIN_DECISIONS = ("approve", "deny")` is used for all views (line 847).
Fail-closed command/file requests must not advertise `approve`:

```python
_PLUGIN_DECISIONS: tuple[str, ...] = ("approve", "deny")
_DENY_ONLY_DECISIONS: tuple[str, ...] = ("deny",)

def _project_request_to_view(
    self, request: PendingServerRequest
) -> PendingEscalationView:
    _CANCEL_CAPABLE_KINDS = frozenset({"command_approval", "file_change"})
    decisions = (
        self._DENY_ONLY_DECISIONS
        if request.kind in _CANCEL_CAPABLE_KINDS
        else self._PLUGIN_DECISIONS
    )
    return PendingEscalationView(
        request_id=request.request_id,
        kind=request.kind,
        requested_scope=request.requested_scope,
        available_decisions=decisions,
    )
```

This ensures `poll` surfaces the correct action set. Callers see `("deny",)` for
boundary-crossing command/file requests and `("approve", "deny")` for unknown/user-input.

**Trust boundary note:** File-change requests without `grantRoot` are accepted inline
because they stay within the sandbox's `writableRoots`. The request payload does not
include individual file paths — App Server's sandbox enforcement is the boundary, not
the handler's scope check. The handler verifies scope at the grant-root level; the
sandbox enforces it at the filesystem level.

### Group 6: Ticket AC update

**File: `docs/tickets/2026-04-23-codex-collaboration-delegate-execution-remediation.md`**

Update acceptance criterion 2:

```markdown
# Before
- [ ] `codex.delegate.decide(approve)` grants the original App Server request
      using the schema-valid `accept` decision. If live `accept` does not
      resume the original action as expected, record the mismatch as an App
      Server/handler integration failure with diagnostic evidence.

# After
- [ ] The server request handler returns schema-valid `accept` for in-boundary
      `command_approval` and `file_change` requests. App Server continues the
      same turn without interruption. The job completes without a pending
      escalation. `codex.delegate.decide(approve)` is rejected for these
      request kinds with a typed reason (the original wire request was
      interrupted; a new turn cannot grant it). `decide(deny)` and `discard`
      remain valid.
```

### Group 7: Test infrastructure

**File: `tests/test_delegation_controller.py`**

1. **Extend `_FakeSession` to record handler responses:**

```python
class _FakeSession:
    def __init__(self, ...):
        ...
        self._handler_responses: list[dict[str, Any] | None] = []

    def run_execution_turn(self, ..., server_request_handler=None):
        ...
        for req in self._server_requests:
            if server_request_handler is not None:
                response = server_request_handler(req)
                self._handler_responses.append(response)
        ...
```

**File: `tests/test_delegate_start_integration.py`**

1b. **Extend `_ConfigurableStubSession` to record handler responses (same pattern):**

```python
class _ConfigurableStubSession(_StubSession):
    def __init__(self, ...):
        ...
        self._handler_responses: list[dict[str, Any] | None] = []

    def run_execution_turn(self, ..., server_request_handler=None):
        for req in self._server_requests:
            if server_request_handler is not None:
                response = server_request_handler(req)
                self._handler_responses.append(response)
        ...
```

Both stubs must record responses. Unit tests assert handler response shape directly;
integration tests assert serialized MCP effects AND may optionally verify response shape
for critical paths (inline accept, fail-closed cancel).

2. **New fixture: `_command_approval_with_network_context`:**

```python
def _command_approval_with_network_context(
    *, request_id=42, item_id="item-1", ...
) -> dict[str, Any]:
    return {
        "id": request_id,
        "method": "item/commandExecution/requestApproval",
        "params": {
            "itemId": item_id, "threadId": "thr-1", "turnId": "turn-1",
            "command": "curl https://evil.com",
            "networkApprovalContext": {"host": "evil.com", "protocol": "https"},
        },
    }
```

3. **New fixture: `_file_change_request` (in-boundary):**

```python
def _file_change_request(
    *, request_id=43, item_id="item-fc", ...
) -> dict[str, Any]:
    return {
        "id": request_id,
        "method": "item/fileChange/requestApproval",
        "params": {
            "itemId": item_id, "threadId": "thr-1", "turnId": "turn-1",
        },
    }
```

4. **New fixture: `_file_change_with_out_of_worktree_grant_root`:**

```python
def _file_change_with_out_of_worktree_grant_root(
    *, request_id=44, item_id="item-fc-oot", grant_root="/etc", ...
) -> dict[str, Any]:
    return {
        "id": request_id,
        "method": "item/fileChange/requestApproval",
        "params": {
            "itemId": item_id, "threadId": "thr-1", "turnId": "turn-1",
            "grantRoot": grant_root,
        },
    }
```

### Group 8: New tests

| # | Test | Asserts |
|---|------|---------|
| T1 | `test_sandbox_policy_includes_platform_defaults` | `build_workspace_write_sandbox_policy` returns `includePlatformDefaults: True` |
| T2 | `test_command_approval_inline_accepted_completes_job` | In-boundary command approval → handler returns `{"decision": "accept"}` (via `_handler_responses`) → job `completed`, no escalation, runtime closed |
| T3 | `test_file_change_inline_accepted_completes_job` | In-boundary file change → handler returns `{"decision": "accept"}` → job `completed` |
| T4 | `test_command_approval_with_network_context_escalates` | `networkApprovalContext` present → handler returns `{"decision": "cancel"}` → job `needs_escalation` |
| T5 | `test_file_change_with_out_of_worktree_grant_root_escalates` | `grantRoot` outside worktree → handler returns `{"decision": "cancel"}` → job `needs_escalation` |
| T6 | `test_command_approval_with_out_of_worktree_cwd_escalates` | `cwd` outside worktree → handler returns `{"decision": "cancel"}` → job `needs_escalation` |
| T7 | `test_command_approval_with_relative_cwd_escalates` | `cwd` relative → handler returns `{"decision": "cancel"}` → job `needs_escalation` |
| T8 | `test_decide_approve_rejected_for_command_approval` | `decide(approve)` on a captured `command_approval` → returns `DecisionRejectedResponse` with reason `"request_not_approvable"` |
| T9 | `test_decide_approve_rejected_for_file_change` | `decide(approve)` on a captured `file_change` → returns `DecisionRejectedResponse` with reason `"request_not_approvable"` |
| T10 | `test_decide_deny_still_works_for_command_approval` | `decide(deny)` on a captured `command_approval` → job `failed` (existing behavior) |
| T11 | `test_unknown_request_still_interrupts_and_escalates` | Existing `_permissions_request` → unchanged behavior |
| T12 | `test_inline_accept_emits_audit_event` | Inline-accepted request → `inline_accept` audit event with `actor="system"` in journal |
| T13 | `test_multiple_inline_accepts_all_complete` | Two in-boundary requests in same turn → both accepted, job `completed` |
| T14 | `test_fail_closed_escalation_view_omits_approve` | Captured `command_approval` (boundary-crossing) → `PendingEscalationView.available_decisions == ("deny",)` |
| T15 | `test_decide_approve_still_valid_for_request_user_input` | `decide(approve)` with answers on `request_user_input` → NOT rejected (existing behavior preserved) |
| T16 | `test_mixed_inline_accept_then_fail_closed` | First request accepted inline, second has `networkApprovalContext` → cancel → `needs_escalation`. Audit: one `inline_accept` event (first request) + one `escalate` event (second request) |
| T17 | `test_accept_not_in_available_decisions_escalates` | In-boundary `command_approval` with `availableDecisions: ["decline", "cancel"]` → handler returns `cancel` (not `accept`), job `needs_escalation`, view `("deny",)`, `decide(approve)` returns rejection |
| T18 | `test_command_approval_with_explicit_in_worktree_cwd_accepted` | `command_approval` with `cwd` set to an absolute path inside the worktree → handler returns `accept`, job `completed` |
| T19 | `test_file_change_with_explicit_in_worktree_grant_root_accepted` | `file_change` with `grantRoot` set to an absolute path inside the worktree → handler returns `accept`, job `completed` |

### Group 9: Existing test updates

#### Unit tests (`test_delegation_controller.py`) — full `_command_approval_request()` disposition

Every usage of `_command_approval_request()` is listed. Disposition is one of:
- **→ inline-accept**: update expectations to `completed` (no escalation)
- **→ boundary-crossing fixture**: replace fixture to preserve escalation behavior
- **→ redesign**: test's premise changes fundamentally

| Line | Test | Disposition |
|------|------|-------------|
| 1329 | `test_start_with_command_approval_returns_escalation` | → boundary-crossing fixture. Rename to reflect fail-closed escalation. Verify `_handler_responses[0] == {"decision": "cancel"}` and `available_decisions == ("deny",)` |
| 1395-96 | `test_start_with_two_requests_responds_to_both` | → inline-accept. Two in-boundary requests → both `accept`, job `completed`. Verify `_handler_responses` |
| 1610 | `test_later_parse_failure_does_not_prevent_captured_request_resolution` | → mixed. First request (`request_id=10`) is in-boundary → inline accept. Second request is a parse-failure → captured. The parse-failure resolution logic should still work. Verify inline-accept for first, captured for second |
| 1653* | `test_start_escalation_keeps_execution_handle_active` | → boundary-crossing fixture. Needs escalation to test handle lifecycle |
| 1660 | `test_decide_approve_resumes_runtime_and_returns_completed_result` | → redesign. approve on command_approval now rejected. Switch to unknown-kind fixture for approve-resume test |
| 1686* | (same test, second use) | → same redesign |
| 1724 | `test_decide_approve_can_reescalate_with_new_pending_request` | → redesign. approve rejected for command_approval. Switch to unknown-kind fixture for reescalation test |
| 1763 | `test_decide_deny_marks_job_failed_and_closes_runtime` | → boundary-crossing fixture |
| 1803 | `test_decide_deny_emits_terminal_outcome` | → boundary-crossing fixture |
| 1835 | `test_decide_rejects_when_runtime_is_missing` | → boundary-crossing fixture |
| 1859 | `test_decide_rejects_invalid_decision_value` | → boundary-crossing fixture |
| 1947 | `test_decide_rejects_request_not_found` | → boundary-crossing fixture |
| 1968 | `test_decide_rejects_request_job_mismatch` | → boundary-crossing fixture |
| 2004 | `test_decide_rejects_deny_with_answers` | → boundary-crossing fixture |
| 2027 | `test_decide_rejects_answers_for_non_request_user_input` | → boundary-crossing fixture |
| 2100 | `test_decide_approve_turn_failure_raises_committed_decision_finalization_error` | → redesign. approve rejected for command_approval. Switch to unknown-kind fixture |
| 2270 | `test_decide_rejects_stale_request_id_after_reescalation` | → redesign. Stale request-cycle identity is sensitive. The test needs an initial escalation (use boundary-crossing fixture), then the reescalation cycle uses unknown-kind. Must verify stale-id rejection still works with the new request-kind mix |
| 2316 | `test_decide_approve_post_turn_journal_failure_raises_committed_decision_finalization_error` | → redesign. Switch to unknown-kind fixture for approve path |
| 2364 | `test_decide_deny_post_commit_failure_raises_committed_decision_finalization_error` | → boundary-crossing fixture |
| 2410 | `test_start_escalation_keeps_promotion_state_none` | → boundary-crossing fixture |
| 2469 | `test_poll_needs_escalation_projects_pending_request_without_raw_ids` | → boundary-crossing fixture. Also verify `available_decisions == ("deny",)` in projected view |

**Summary:** 20 usages across 19 tests. 11 → boundary-crossing fixture swap, 3 → inline-accept expectation update, 5 → redesign (approve path now rejected for command_approval), 1 → mixed (parse-failure test).

#### Integration tests (`test_delegate_start_integration.py`)

The integration test file has its own `_command_approval_request_msg()` fixture (line 514)
with the same in-boundary shape and its own `_ConfigurableStubSession` (line 191) that
also discards handler responses. Both need updates.

**Stub update:** Extend `_ConfigurableStubSession.run_execution_turn` to record handler
responses (same pattern as `_FakeSession` in Group 7).

**New fixture:** Add `_command_approval_with_network_context_msg()` to the integration
test file for escalation tests.

| Test | Current behavior | New behavior | Change needed |
|------|-----------------|-------------|---------------|
| `test_e2e_command_approval_produces_escalation` (554) | `_command_approval_request_msg()` → cancel → escalation | In-boundary → accept → completed | Replace fixture with boundary-crossing variant for escalation test |
| `test_e2e_busy_gate_blocks_when_job_needs_escalation` (662) | Same | Same | Same fixture replacement |
| `test_delegate_poll_needs_escalation_returns_projected_request` (785) | Polls escalation with `available_decisions=("approve","deny")` | View now shows `("deny",)` | Replace fixture + update assertion to `("deny",)` |
| `test_delegate_decide_approve_end_to_end_through_mcp_dispatch` (841) | approve → new turn → completed | approve REJECTED for command_approval | Replace with test that `decide(approve)` returns rejection, or switch to unknown-kind fixture |
| `test_delegate_decide_deny_end_to_end_through_mcp_dispatch` (902) | deny → failed | deny → failed (unchanged behavior) | Replace initial fixture with boundary-crossing variant |
| `test_start_escalation_uses_pending_escalation_key` (974) | Escalation key contract | Same contract | Replace fixture |
| `test_decide_reescalation_uses_pending_escalation_key` (1016) | Reescalation after approve | approve REJECTED | Replace with unknown-kind fixture or adapt |

## Build Sequence

| Step | Group | Dependencies | Scope |
|------|-------|-------------|-------|
| 1 | Group 1 | None | Sandbox policy change + unit test |
| 2 | Group 2 | None | Approval router: fallback + boundary validator |
| 3 | Group 7 (unit) | None | `_FakeSession` response recording + new unit fixtures |
| 4 | Group 7 (integration) | None | `_ConfigurableStubSession` response recording + new integration fixtures |
| 5 | Group 5 (models) | None | Add `"request_not_approvable"` to `DecisionRejectedReason` |
| 6 | Group 3 | Groups 2, 3 | Handler restructure |
| 7 | Group 4 | Group 6 | Finalize-turn audit |
| 8 | Group 5 (decide) | Groups 5, 6 | Decide guard + rejection |
| 9 | Group 5b | Group 8 | Escalation view projection |
| 10 | Group 9b (skill) | Group 5b | Delegate skill UX + design spec mirror |
| 11 | Group 6 (ticket) | Groups 6-10 | Ticket AC update |
| 12 | Groups 8-9 | Groups 1-11 | All new + updated tests (19 new, 26 updated) |
| 13 | Group 10 | Step 12 passing | Live-smoke verification (ticket Phase 5) |

Steps 1-5 are independent and can be implemented in parallel.

`DecisionRejectedReason` consumers:
- `server/models.py` (type definition)
- `server/delegation_controller.py` (`_reject_decision` method signature)
- `docs/superpowers/specs/codex-collaboration/contracts.md:297` (caller-facing contract
  listing `Decision Rejection.reason` enum — must add `request_not_approvable`)

## Risks

1. **`_FakeSession` response recording may affect existing interrupt behavior.**
   The handler closure calls `entry.session.interrupt_turn()` for unknown kinds, which
   sets `_interrupted = True`. Recording the (None) response before the interrupt call
   must not change execution order. The recording is passive (append to list).

2. **Existing tests depend on `_command_approval_request()` → escalation.**
   20 unit-test usages across 19 tests, plus 7 integration-test usages across 7 tests.
   See the full disposition checklist in Group 9. Do not modify the fixture itself —
   create new boundary-crossing fixtures and update each test per its disposition
   (11 fixture swap, 3 inline-accept update, 5 redesign, 1 mixed, 7 integration).

3. **`is_within_delegation_boundary` needs the worktree path from the closure.**
   The `worktree_path` parameter is already available in `_execute_live_turn`. Pass it
   into the handler closure scope. No new plumbing needed.

4. **Audit UUID exhaustion in tests.**
   The `_build_controller` UUID factory has a fixed iterator. Adding inline-accept audit
   events consumes additional UUIDs. Tests that rely on specific UUID values need iterator
   expansion.

5. **`DecisionRejectedReason` change cascades to serialization tests.**
   Adding `"request_not_approvable"` to the `Literal` type may affect MCP tool
   serialization tests or any tests that exhaustively check rejection reasons. Grep
   for `DecisionRejectedReason` consumers before implementing.

6. **`_CANCEL_CAPABLE_KINDS` defined in multiple scopes.**
   Currently defined as a local in `_execute_live_turn` (line 642) and `_finalize_turn`
   (line 1456). The decide guard and view projection also need it. Promote to a
   module-level constant to avoid drift.

### Group 9b: Delegate skill UX update

**File: `packages/plugins/codex-collaboration/skills/delegate/SKILL.md`**

The skill currently hard-codes `approve, deny` in the decision prompt (line 203) and
routes `/delegate approve` unconditionally to `codex.delegate.decide(approve)` (line 264).
After the handler change, fail-closed command/file escalations return
`available_decisions == ("deny",)`, but the skill still tells users to approve.

**Changes:**

1. **Decision prompt (line 200-206):** Replace hard-coded `approve, deny` with dynamic
   rendering from `pending_escalation.available_decisions` (a list of strings in the
   MCP JSON payload):
   - If `"approve"` is in the list: show both verbs (current behavior for unknown/user-input)
   - If `"approve"` is absent: show only deny, with explanation: "This escalation cannot be
     approved because the original request was interrupted at the wire level.
     You can deny it or discard the job."

2. **Approve verb (line 259-265):** Add a pre-call guard:
   - Before calling `decide`, check `pending_escalation.available_decisions`
   - If `"approve"` is not in `available_decisions`: reject locally with
     "Cannot approve this escalation — approve is not available for this request kind.
     Use `/delegate deny` or `/delegate discard`." Do NOT call `decide`.

3. **Gate 2 (line 237-242):** Update Gate 2 text to reflect that approve may not
   always be available: "approve/deny requires pending escalation" →
   "decision requires pending escalation; available decisions depend on escalation kind."

**File: `docs/superpowers/specs/2026-04-21-delegate-skill-ux-design.md`**

The design spec (line 256) has the same hard-coded approve/deny prompt and approve flow.
Update to match the SKILL.md changes: render `available_decisions`, guard approve verb,
note that command/file approvals are deny-only after wire-level cancel.

## Group 10: Live-smoke verification (ticket Phase 5)

The ticket acceptance criteria require live verification, not just unit/integration tests.
This group executes after all code changes land and all tests pass.

**Objective:** Run a live `/delegate` with a real file-creation or file-edit objective.

**Sequence:**
1. `codex.delegate.start` with a concrete, non-colliding objective (e.g., "Create the
   directory `docs/scratch/` if it does not exist, then create the file
   `docs/scratch/T-20260423-01-smoke.md` with the heading 'Delegate Smoke Test'
   and a one-line description of the current date")
2. If the job completes without escalation: proceed to step 4
3. If the job needs escalation:
   - If escalation kind is `command_approval`/`file_change`: the sandbox/approval fix failed.
     **STOP — investigate.**
   - If escalation kind is unknown/other: `codex.delegate.decide(deny)` and record
     the escalation kind as a diagnostic finding
4. `codex.delegate.poll` — verify:
   - `full.diff` is non-empty
   - `changed_files` is non-empty
   - `artifact_hash` is stable (poll twice, same hash)
5. Final disposition:
   - Successful `codex.delegate.promote` → AC met
   - OR typed `PromotionRejectedResponse` unrelated to sandbox/approval → AC met
     (the rejection is not about execution capability)
   - OR empty diff despite no escalation → sandbox fix insufficient, investigate

**Expected outcome after fix:** The job completes without `command_approval`/`file_change`
escalation (sandbox allows shell execution, approval requests auto-accepted inline).
Artifacts are produced. Promotion succeeds or fails on content grounds, not execution
capability.

**Recording:** Document live-smoke findings in the PR description. If any acceptance
criterion fails, record the diagnostic evidence before proceeding.

## Non-Goals

- Changing `approval_policy` from `"untrusted"` to another value
- Modifying the resume prompt builder or advisory turn path
- Adding support for `acceptForSession` or `acceptWithExecpolicyAmendment`
  (future optimization — `accept` is the minimum viable grant)
- Auto-pruning the `decide(approve)` → new-turn code path (preserved for unknown kinds)
