# Delegate Skill UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the delegate skill UX — a stateless state-router skill over the codex.delegate.* MCP tools, with server-side prerequisites for status enrichment, widened discard, and a singleton attention invariant.

**Architecture:** Two slices. Slice 0 (Tasks 1-5) is the safety-bearing server enrichment: `list_user_attention_required()` on the job store, widened discard eligibility for failed/unknown pre-mutation jobs, widened busy gate to attention-active, and `active_delegation` populated in `codex.status` via MCP-side enrichment. Slice 1 (Task 6) is the SKILL.md with full grammar, state router, rendering, ceremony gates, and failure handling. Slice 0 must be fully green before Slice 1 starts.

**Tech Stack:** Python 3.12+, pytest, dataclasses, MCP JSON-RPC. Skill is pure Markdown.

**Design spec:** `docs/superpowers/specs/2026-04-21-delegate-skill-ux-design.md`

**Test runner:** `uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/ -v`

**Baseline:** 818 tests, all passing.

---

## File Structure

### New files

| File | Responsibility |
|------|---------------|
| `packages/plugins/codex-collaboration/skills/delegate/SKILL.md` | Skill definition (Task 6) |

### Modified files

| File | Changes |
|------|---------|
| `server/delegation_job_store.py` | Add `list_user_attention_required()` (Task 1) |
| `tests/test_delegation_job_store.py` | Tests for `list_user_attention_required()` (Task 1) |
| `server/delegation_controller.py` | Widen discard eligibility (Task 2), widen busy gate (Task 3) |
| `tests/test_delegation_controller.py` | Tests for widened discard (Task 2) and widened busy gate (Task 3) |
| `server/mcp_server.py` | MCP-side status enrichment with `active_delegation` (Task 4) |
| `tests/test_delegate_start_integration.py` | Integration tests for status enrichment and widened busy (Task 4) |
| `docs/superpowers/specs/codex-collaboration/contracts.md` | Update `active_delegation` description and discard eligibility (Task 5) |
| `docs/superpowers/specs/codex-collaboration/promotion-protocol.md` | Update discard allowed states (Task 5) |
| `docs/superpowers/specs/codex-collaboration/recovery-and-journal.md` | Update concurrency text for widened busy gate (Task 5) |

All paths are relative to `packages/plugins/codex-collaboration/` except doc paths which are repo-relative.

---

## Task 1: `list_user_attention_required()` on DelegationJobStore

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/delegation_job_store.py`
- Test: `packages/plugins/codex-collaboration/tests/test_delegation_job_store.py`

This is the foundation query for the singleton invariant. "User-attention-required" includes all non-terminal jobs: in-flight, completed awaiting review, failed/unknown with pre-mutation state, and partial/recovery promotion states. Terminal promotion states (`verified`, `discarded`, `rolled_back`) are excluded. Additionally, `completed + promotion_state=None` is excluded — this is an impossible state (the atomic `update_status_and_promotion` call always sets both), and if it ever appears via corruption/legacy, it cannot be promoted or discarded, so it must not poison the busy gate.

**Important:** The existing `_make_job()` helper in `test_delegation_job_store.py` defaults `promotion_state="pending"`, not `None`. Tests that need null promotion_state must pass `promotion_state=None` explicitly.

- [ ] **Step 1: Write failing tests for `list_user_attention_required()`**

Add to `tests/test_delegation_job_store.py`:

```python
# --- list_user_attention_required tests ---


def test_list_user_attention_required_returns_running_job(tmp_path: Path) -> None:
    """Running jobs are user-attention-required (in progress)."""
    store = DelegationJobStore(tmp_path, "sess-1")
    job = _make_job("job-1", status="running", promotion_state=None)
    store.create(job)

    result = store.list_user_attention_required()
    assert len(result) == 1
    assert result[0].job_id == "job-1"


def test_list_user_attention_required_returns_needs_escalation_job(
    tmp_path: Path,
) -> None:
    """Needs-escalation jobs are user-attention-required (waiting for decision)."""
    store = DelegationJobStore(tmp_path, "sess-1")
    job = _make_job("job-1", status="needs_escalation", promotion_state=None)
    store.create(job)

    result = store.list_user_attention_required()
    assert len(result) == 1
    assert result[0].status == "needs_escalation"


def test_list_user_attention_required_returns_completed_pending_promotion(
    tmp_path: Path,
) -> None:
    """Completed jobs with pending promotion are user-attention-required."""
    store = DelegationJobStore(tmp_path, "sess-1")
    job = _make_job("job-1", status="completed", promotion_state="pending")
    store.create(job)

    result = store.list_user_attention_required()
    assert len(result) == 1
    assert result[0].promotion_state == "pending"


def test_list_user_attention_required_returns_completed_prechecks_failed(
    tmp_path: Path,
) -> None:
    """Completed jobs with prechecks_failed are user-attention-required."""
    store = DelegationJobStore(tmp_path, "sess-1")
    job = _make_job("job-1", status="completed", promotion_state="prechecks_failed")
    store.create(job)

    result = store.list_user_attention_required()
    assert len(result) == 1
    assert result[0].promotion_state == "prechecks_failed"


def test_list_user_attention_required_returns_failed_null_promotion(
    tmp_path: Path,
) -> None:
    """Failed jobs with null promotion_state are user-attention-required."""
    store = DelegationJobStore(tmp_path, "sess-1")
    job = _make_job("job-1", status="failed", promotion_state=None)
    store.create(job)

    result = store.list_user_attention_required()
    assert len(result) == 1
    assert result[0].status == "failed"


def test_list_user_attention_required_returns_unknown_null_promotion(
    tmp_path: Path,
) -> None:
    """Unknown jobs with null promotion_state are user-attention-required."""
    store = DelegationJobStore(tmp_path, "sess-1")
    job = _make_job("job-1", status="unknown", promotion_state=None)
    store.create(job)

    result = store.list_user_attention_required()
    assert len(result) == 1
    assert result[0].status == "unknown"


def test_list_user_attention_required_returns_rollback_needed(
    tmp_path: Path,
) -> None:
    """Jobs with rollback_needed promotion state are user-attention-required."""
    store = DelegationJobStore(tmp_path, "sess-1")
    job = _make_job("job-1", status="completed", promotion_state="rollback_needed")
    store.create(job)

    result = store.list_user_attention_required()
    assert len(result) == 1
    assert result[0].promotion_state == "rollback_needed"


def test_list_user_attention_required_excludes_completed_null_promotion(
    tmp_path: Path,
) -> None:
    """Completed + null promotion_state is an impossible state — excluded to prevent
    poisoning the busy gate (cannot be promoted or discarded)."""
    store = DelegationJobStore(tmp_path, "sess-1")
    job = _make_job("job-1", status="completed", promotion_state=None)
    store.create(job)

    result = store.list_user_attention_required()
    assert len(result) == 0


def test_list_user_attention_required_excludes_verified(tmp_path: Path) -> None:
    """Verified promotion is terminal — excluded from attention set."""
    store = DelegationJobStore(tmp_path, "sess-1")
    job = _make_job("job-1", status="completed", promotion_state="verified")
    store.create(job)

    result = store.list_user_attention_required()
    assert len(result) == 0


def test_list_user_attention_required_excludes_discarded(tmp_path: Path) -> None:
    """Discarded promotion is terminal — excluded from attention set."""
    store = DelegationJobStore(tmp_path, "sess-1")
    job = _make_job("job-1", status="completed", promotion_state="discarded")
    store.create(job)

    result = store.list_user_attention_required()
    assert len(result) == 0


def test_list_user_attention_required_excludes_rolled_back(tmp_path: Path) -> None:
    """Rolled-back promotion is terminal — excluded from attention set."""
    store = DelegationJobStore(tmp_path, "sess-1")
    job = _make_job("job-1", status="completed", promotion_state="rolled_back")
    store.create(job)

    result = store.list_user_attention_required()
    assert len(result) == 0
```

Verify the test file already has a `_make_job` helper. If not, add one before the tests:

```python
def _make_job(
    job_id: str,
    *,
    status: str = "queued",
    promotion_state: str | None = None,
    runtime_id: str = "rt-1",
    collaboration_id: str = "collab-1",
    base_commit: str = "abc123",
    worktree_path: str = "/tmp/wt",
) -> DelegationJob:
    return DelegationJob(
        job_id=job_id,
        runtime_id=runtime_id,
        collaboration_id=collaboration_id,
        base_commit=base_commit,
        worktree_path=worktree_path,
        status=status,
        promotion_state=promotion_state,
    )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_delegation_job_store.py -k "list_user_attention" -v`
Expected: All 11 tests FAIL with `AttributeError: 'DelegationJobStore' object has no attribute 'list_user_attention_required'`

- [ ] **Step 3: Implement `list_user_attention_required()`**

Add to `packages/plugins/codex-collaboration/server/delegation_job_store.py`, after the `_ACTIVE_STATUSES` constant:

```python
_TERMINAL_PROMOTION_STATES: frozenset[str] = frozenset(
    {"verified", "discarded", "rolled_back"}
)
```

Add the method to `DelegationJobStore`, after `list_active()`:

```python
def list_user_attention_required(self) -> list[DelegationJob]:
    """Return jobs requiring user attention for the delegate skill UX.

    Broader than list_active() which covers only runtime-active states
    for the busy gate. This includes completed jobs awaiting review,
    failed/unknown jobs needing inspection, and partial promotion states
    needing recovery. Excludes terminal promotion states (verified,
    discarded, rolled_back).
    """
    return [
        j
        for j in self._replay().values()
        if j.promotion_state not in _TERMINAL_PROMOTION_STATES
        # Exclude completed + null promotion_state: impossible state
        # (update_status_and_promotion always sets both atomically).
        # If it appears via corruption/legacy, it cannot be promoted or
        # discarded, so it must not poison the busy gate.
        and not (j.status == "completed" and j.promotion_state is None)
    ]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_delegation_job_store.py -k "list_user_attention" -v`
Expected: All 11 tests PASS.

- [ ] **Step 5: Run full suite to confirm no regressions**

Run: `uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/ -v`
Expected: All 829 tests PASS (818 baseline + 11 new).

- [ ] **Step 6: Commit**

```bash
git add packages/plugins/codex-collaboration/server/delegation_job_store.py packages/plugins/codex-collaboration/tests/test_delegation_job_store.py
git commit -m "feat(t20260330-06): add list_user_attention_required to DelegationJobStore"
```

---

## Task 2: Widen discard eligibility for failed/unknown pre-mutation jobs

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/delegation_controller.py:1335-1378`
- Test: `packages/plugins/codex-collaboration/tests/test_delegation_controller.py`

The design spec requires discard to accept failed/unknown jobs with `promotion_state is None` (pre-mutation). Post-mutation states (`applied`, `rollback_needed`) remain rejected. The exact predicate: discard is allowed when `promotion_state in ("pending", "prechecks_failed")`, OR when `status in ("failed", "unknown")` and `promotion_state is None`.

- [ ] **Step 1: Write failing tests for widened discard**

Add to `tests/test_delegation_controller.py`, after `test_discard_rejects_applied_job`:

```python
def test_discard_accepts_failed_null_promotion(tmp_path: Path) -> None:
    """Discard accepts a failed job with null promotion_state (pre-mutation)."""
    controller, job_store, _journal, _repo, job_id, _hash, _cb = (
        _build_promote_scenario(tmp_path)
    )
    # Override status to failed with null promotion_state.
    job_store.update_status(job_id, "failed")
    job_store.update_promotion_state(job_id, promotion_state="pending")
    # Re-read baseline: job is failed + pending (from promote scenario).
    # We need failed + null. Use update_status_and_promotion to set both.
    job_store.update_status_and_promotion(
        job_id, status="failed", promotion_state=None
    )

    result = controller.discard(job_id=job_id)
    assert isinstance(result, DiscardResult)
    assert result.job.promotion_state == "discarded"


def test_discard_accepts_unknown_null_promotion(tmp_path: Path) -> None:
    """Discard accepts an unknown job with null promotion_state (pre-mutation)."""
    controller, job_store, _journal, _repo, job_id, _hash, _cb = (
        _build_promote_scenario(tmp_path)
    )
    job_store.update_status_and_promotion(
        job_id, status="unknown", promotion_state=None
    )

    result = controller.discard(job_id=job_id)
    assert isinstance(result, DiscardResult)
    assert result.job.promotion_state == "discarded"


def test_discard_rejects_failed_with_applied_promotion(tmp_path: Path) -> None:
    """Discard rejects a failed job with applied promotion_state (post-mutation)."""
    controller, job_store, _journal, _repo, job_id, _hash, _cb = (
        _build_promote_scenario(tmp_path)
    )
    job_store.update_status_and_promotion(
        job_id, status="failed", promotion_state="applied"
    )

    result = controller.discard(job_id=job_id)
    assert isinstance(result, DiscardRejectedResponse)
    assert result.reason == "job_not_discardable"


def test_discard_rejects_failed_with_rollback_needed(tmp_path: Path) -> None:
    """Discard rejects a failed job with rollback_needed promotion (post-mutation)."""
    controller, job_store, _journal, _repo, job_id, _hash, _cb = (
        _build_promote_scenario(tmp_path)
    )
    job_store.update_status_and_promotion(
        job_id, status="failed", promotion_state="rollback_needed"
    )

    result = controller.discard(job_id=job_id)
    assert isinstance(result, DiscardRejectedResponse)
    assert result.reason == "job_not_discardable"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_delegation_controller.py -k "test_discard_accepts_failed or test_discard_accepts_unknown or test_discard_rejects_failed_with" -v`
Expected: The two `accepts_failed` and `accepts_unknown` tests FAIL (current code rejects them). The two `rejects_failed_with` tests PASS (current code rejects all non-pending/prechecks_failed).

- [ ] **Step 3: Widen the discard eligibility predicate**

Edit `packages/plugins/codex-collaboration/server/delegation_controller.py`, the `discard()` method. Replace the current check at line ~1348:

```python
if job.promotion_state not in ("pending", "prechecks_failed"):
```

With the widened predicate:

```python
_discardable = job.promotion_state in ("pending", "prechecks_failed") or (
    job.status in ("failed", "unknown") and job.promotion_state is None
)
if not _discardable:
```

Also update the docstring from:
```python
"""Discard a completed delegation job without promoting.

Only jobs in 'pending' or 'prechecks_failed' promotion state can be discarded.
"""
```

To:
```python
"""Discard a delegation job without promoting.

Allowed when promotion_state in (pending, prechecks_failed), or when
status in (failed, unknown) and promotion_state is None (pre-mutation).
Post-mutation states (applied, rollback_needed) are never discardable.
"""
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_delegation_controller.py -k "discard" -v`
Expected: All 6 discard tests PASS (2 existing + 4 new).

- [ ] **Step 5: Run full suite to confirm no regressions**

Run: `uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/ -v`
Expected: All 833 tests PASS (829 + 4 new).

- [ ] **Step 6: Commit**

```bash
git add packages/plugins/codex-collaboration/server/delegation_controller.py packages/plugins/codex-collaboration/tests/test_delegation_controller.py
git commit -m "feat(t20260330-06): widen discard eligibility for failed/unknown pre-mutation jobs"
```

---

## Task 3: Widen the start busy gate to attention-active

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/delegation_controller.py:332-344`
- Test: `packages/plugins/codex-collaboration/tests/test_delegation_controller.py`

The current busy gate calls `self._job_store.list_active()` which returns only runtime-active jobs (`queued`, `running`, `needs_escalation`). Widen to also consult `list_user_attention_required()` so that completed-awaiting-review and failed/unknown jobs block new starts. This establishes the singleton user-attention invariant.

The three-source busy check stays: (a) job store, (b) runtime registry, (c) unresolved journal. Source (a) is widened from `list_active()` to `list_user_attention_required()`.

- [ ] **Step 1: Write failing tests for widened busy gate**

Add to `tests/test_delegation_controller.py`, after the existing busy tests:

```python
def test_start_returns_busy_when_completed_pending_job_exists(
    tmp_path: Path,
) -> None:
    """Start rejects when a completed job with pending promotion exists."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, job_store, _ls, _j, _r, _prs = _build_controller(
        tmp_path
    )

    # First start succeeds (complete immediately, no server request).
    first = controller.start(repo_root=repo_root)
    assert isinstance(first, DelegationJob)
    first_job_id = first.job_id

    # The job completed normally — status=completed, promotion_state=pending.
    # (The stub control plane produces a completed job with promotion_state set.)
    persisted = job_store.get(first_job_id)
    assert persisted is not None
    assert persisted.status == "completed"
    assert persisted.promotion_state == "pending"

    # Second start should be rejected.
    second = controller.start(repo_root=repo_root)
    assert isinstance(second, JobBusyResponse)
    assert second.busy is True
    assert second.active_job_id == first_job_id


def test_start_returns_busy_when_failed_null_promotion_job_exists(
    tmp_path: Path,
) -> None:
    """Start rejects when a failed job with null promotion_state exists."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, job_store, _ls, _j, _r, _prs = _build_controller(
        tmp_path
    )

    first = controller.start(repo_root=repo_root)
    assert isinstance(first, DelegationJob)
    first_job_id = first.job_id

    # Override to failed with null promotion.
    job_store.update_status_and_promotion(
        first_job_id, status="failed", promotion_state=None
    )

    second = controller.start(repo_root=repo_root)
    assert isinstance(second, JobBusyResponse)
    assert second.busy is True
    assert second.active_job_id == first_job_id


def test_start_succeeds_after_discard_clears_attention_job(
    tmp_path: Path,
) -> None:
    """Start succeeds once the user discards the attention-active job."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    controller, control_plane, _wm, job_store, _ls, _j, _r, _prs = _build_controller(
        tmp_path
    )

    first = controller.start(repo_root=repo_root)
    assert isinstance(first, DelegationJob)
    first_job_id = first.job_id

    # Discard the completed job.
    discard_result = controller.discard(job_id=first_job_id)
    assert isinstance(discard_result, DiscardResult)

    # Now start should succeed (discarded job is terminal, no longer attention-active).
    second = controller.start(repo_root=repo_root)
    assert not isinstance(second, JobBusyResponse)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_delegation_controller.py -k "test_start_returns_busy_when_completed_pending or test_start_returns_busy_when_failed_null or test_start_succeeds_after_discard" -v`
Expected: `test_start_returns_busy_when_completed_pending` and `test_start_returns_busy_when_failed_null` FAIL (current busy gate doesn't see these). `test_start_succeeds_after_discard` may pass or fail depending on stub behavior.

- [ ] **Step 3: Widen the busy gate**

Edit `packages/plugins/codex-collaboration/server/delegation_controller.py`. In the `start()` method, replace the first busy check (around line 332):

```python
active = self._job_store.list_active()
```

With:

```python
active = self._job_store.list_user_attention_required()
```

The rest of the busy check (registry and unresolved journal) stays unchanged — those are independent sources that catch different failure modes.

Update the comment at line ~320 from:
```python
# Busy check — max-1 concurrent job per session. Consults THREE sources:
#   (a) job_store.list_active(): healthy queued/running/needs_escalation jobs
```

To:
```python
# Busy check — max-1 user-attention job per session. Consults THREE sources:
#   (a) job_store.list_user_attention_required(): any non-terminal job
#       (in-flight, completed awaiting review, failed/unknown needing
#       inspection). Wider than list_active() to enforce the singleton
#       user-attention invariant.
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_delegation_controller.py -k "busy" -v`
Expected: All busy tests PASS (existing + new).

- [ ] **Step 5: Run full suite to confirm no regressions**

Run: `uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/ -v`
Expected: All tests PASS. Note: existing tests that assumed a completed job doesn't trigger busy may need adjustment. Check for failures and fix test expectations if needed.

- [ ] **Step 6: Commit**

```bash
git add packages/plugins/codex-collaboration/server/delegation_controller.py packages/plugins/codex-collaboration/tests/test_delegation_controller.py
git commit -m "feat(t20260330-06): widen start busy gate to attention-active for singleton invariant"
```

---

## Task 4: MCP-side status enrichment with `active_delegation`

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/mcp_server.py:344-351`
- Test: `packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py`

The MCP dispatch path for `codex.status` currently returns `control_plane.codex_status()` directly, which hardcodes `active_delegation: None`. Enrich the result after the control plane call using a recovery-capable helper that calls `_ensure_delegation_controller()`.

- [ ] **Step 1: Write failing tests for status enrichment**

Add to `tests/test_delegate_start_integration.py`. Adapt fixture names to match the existing test patterns in that file (check for `_call_tool` helper, `mcp_server`/`repo_root` fixtures, etc.).

```python
# --- codex.status active_delegation enrichment ---


def test_status_active_delegation_null_when_no_jobs(
    mcp_server: McpServer,
    repo_root: Path,
) -> None:
    """codex.status returns active_delegation=null when no delegation exists."""
    result = _call_tool(mcp_server, "codex.status", {"repo_root": str(repo_root)})
    assert result["active_delegation"] is None


def test_status_active_delegation_populated_after_start(
    mcp_server: McpServer,
    repo_root: Path,
) -> None:
    """codex.status returns active_delegation after a delegation job starts."""
    start_result = _call_tool(
        mcp_server,
        "codex.delegate.start",
        {"repo_root": str(repo_root), "objective": "test objective"},
    )
    job_id = start_result["job"]["job_id"] if "job" in start_result else start_result["job_id"]

    status = _call_tool(mcp_server, "codex.status", {"repo_root": str(repo_root)})
    assert status["active_delegation"] is not None
    assert status["active_delegation"]["job_id"] == job_id


def test_status_active_delegation_null_after_discard(
    mcp_server: McpServer,
    repo_root: Path,
) -> None:
    """codex.status returns active_delegation=null after job is discarded."""
    start_result = _call_tool(
        mcp_server,
        "codex.delegate.start",
        {"repo_root": str(repo_root), "objective": "test objective"},
    )
    job_id = start_result["job"]["job_id"] if "job" in start_result else start_result["job_id"]

    _call_tool(mcp_server, "codex.delegate.discard", {"job_id": job_id})

    status = _call_tool(mcp_server, "codex.status", {"repo_root": str(repo_root)})
    assert status["active_delegation"] is None


def test_status_active_delegation_includes_required_fields(
    mcp_server: McpServer,
    repo_root: Path,
) -> None:
    """active_delegation contains the required shape fields."""
    _call_tool(
        mcp_server,
        "codex.delegate.start",
        {"repo_root": str(repo_root), "objective": "test objective"},
    )

    status = _call_tool(mcp_server, "codex.status", {"repo_root": str(repo_root)})
    ad = status["active_delegation"]
    assert ad is not None
    for field in ("job_id", "status", "promotion_state", "base_commit", "artifact_hash", "artifact_paths", "attention_job_count"):
        assert field in ad, f"active_delegation missing field: {field}"
    assert ad["attention_job_count"] == 1


def test_status_active_delegation_null_when_factory_fails(
    tmp_path: Path,
) -> None:
    """When _ensure_delegation_controller() fails, active_delegation is null
    and a diagnostic is appended to errors."""
    # Build an McpServer with a delegation factory that raises.
    def failing_factory():
        raise RuntimeError("factory recovery failed")

    server = _build_mcp_server_with_delegation_factory(tmp_path, failing_factory)
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    result = _call_tool(server, "codex.status", {"repo_root": str(repo_root)})
    assert result["active_delegation"] is None
    # Diagnostic goes to dedicated field, NOT global errors
    # (global errors would block consult/dialogue status preflights).
    assert "delegation_status_error" in result
    assert "factory recovery failed" in result["delegation_status_error"]
```

The `test_status_active_delegation_null_when_factory_fails` test requires a helper `_build_mcp_server_with_delegation_factory` that creates an McpServer with a custom delegation factory. If no such helper exists, write one that mirrors the existing MCP server construction pattern but injects the factory. The key assertion: `active_delegation` is null AND `errors` contains a delegation diagnostic string.

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py -k "status_active_delegation" -v`
Expected: Tests that check `active_delegation is not None` FAIL (current code always returns None).

- [ ] **Step 3: Implement MCP-side status enrichment**

First, add a public method on `DelegationController` (in `delegation_controller.py`):

```python
def get_active_delegation_summary(self) -> tuple[DelegationJob | None, int]:
    """Return the active user-attention-required job and total count.

    Returns (job, count). job is the last in store replay order
    (most recently created). count > 1 is a pre-migration anomaly
    — the widened busy gate prevents new multi-attention states,
    but sessions started before the gate was widened may have
    multiple attention-active jobs.

    Used by codex.status enrichment. Preserves encapsulation —
    callers do not reach into the private job store.
    """
    attention = self._job_store.list_user_attention_required()
    if not attention:
        return None, 0
    # Last in replay order = most recently created (JSONL append order).
    return attention[-1], len(attention)
```

Then edit `packages/plugins/codex-collaboration/server/mcp_server.py`. In `_dispatch_tool()`, replace the `codex.status` branch (around line 350-351):

```python
if name == "codex.status":
    return self._control_plane.codex_status(Path(arguments["repo_root"]))
```

With inline enrichment that appends diagnostics to `errors` on failure:

```python
if name == "codex.status":
    result = self._control_plane.codex_status(Path(arguments["repo_root"]))
    # MCP-side delegation enrichment. Recovery-capable: calls
    # _ensure_delegation_controller() which initializes/recovers
    # from durable state if needed. Suppresses all errors —
    # status must never fail because delegation recovery failed.
    try:
        controller = self._ensure_delegation_controller()
        job, count = controller.get_active_delegation_summary()
        if job is not None:
            result["active_delegation"] = {
                "job_id": job.job_id,
                "status": job.status,
                "promotion_state": job.promotion_state,
                "base_commit": job.base_commit,
                "artifact_hash": job.artifact_hash,
                "artifact_paths": list(job.artifact_paths),
                "attention_job_count": count,
            }
    except Exception as exc:
        # Delegation recovery or query failed. Use a dedicated
        # non-blocking field — do NOT append to global `errors`,
        # because existing status consumers (consult, dialogue)
        # treat non-empty `errors` as blocking.
        result["delegation_status_error"] = (
            f"Delegation status query failed: {exc!r:.200}"
        )
    return result
```

No separate helper method needed. The inline try/except handles both the `_ensure_delegation_controller()` failure (factory/recovery error) and the `get_active_delegation_summary()` failure (query error) in one block. Diagnostics go to `errors`, making delegation failure distinguishable from "no active delegation."

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py -k "status_active_delegation" -v`
Expected: All 4 tests PASS.

- [ ] **Step 5: Run full suite to confirm no regressions**

Run: `uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/ -v`
Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add packages/plugins/codex-collaboration/server/mcp_server.py packages/plugins/codex-collaboration/server/delegation_controller.py packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py
git commit -m "feat(t20260330-06): populate active_delegation in codex.status via MCP-side enrichment"
```

---

## Task 5: Normative contract updates

**Files:**
- Modify: `docs/superpowers/specs/codex-collaboration/contracts.md`
- Modify: `docs/superpowers/specs/codex-collaboration/promotion-protocol.md`

These are normative doc updates to reflect the widened semantics from Tasks 1-4.

- [ ] **Step 1: Update `active_delegation` description in contracts.md**

In `docs/superpowers/specs/codex-collaboration/contracts.md`, find the Runtime Health table row:

```
| `active_delegation` | object? | Active delegation job summary |
```

Replace with:

```
| `active_delegation` | object? | Current delegation requiring user attention (in-flight, completed awaiting review, failed/unknown needing inspection, or partial promotion states needing recovery). Null when no job requires attention. Excluded: terminal promotion states (`verified`, `discarded`, `rolled_back`). |
```

- [ ] **Step 2: Update discard eligibility in promotion-protocol.md**

In `docs/superpowers/specs/codex-collaboration/promotion-protocol.md`, find the Discard Semantics section:

```
- **Allowed states:** `pending`, `prechecks_failed`
```

Replace with:

```
- **Allowed states:** `promotion_state in {pending, prechecks_failed}`, or `status in {failed, unknown}` with `promotion_state is None` (pre-mutation). Rejected for `prechecks_passed`, `applied`, `rollback_needed`, `verified`, `rolled_back`, and `discarded`.
```

- [ ] **Step 3: Update Job Busy section in contracts.md**

In `docs/superpowers/specs/codex-collaboration/contracts.md`, find the Job Busy response shape. Update the description to reflect that `busy` can now be returned for attention-active jobs (completed awaiting review, failed/unknown needing discard), not just runtime-active (running/queued/needs_escalation) jobs. Update the `active_job_status` description accordingly — it now covers all `JobStatus` values, not just runtime-active ones.

- [ ] **Step 4: Update concurrency text in recovery-and-journal.md**

In `docs/superpowers/specs/codex-collaboration/recovery-and-journal.md`, find the Concurrency Limits section. Update text that describes the busy gate as blocking only when "a job is already running" or similar runtime-active language. Replace with language that reflects the widened gate: the busy gate blocks when any user-attention-required job exists (in-flight, completed awaiting review, failed/unknown needing inspection), not just runtime-active jobs.

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/codex-collaboration/contracts.md docs/superpowers/specs/codex-collaboration/promotion-protocol.md docs/superpowers/specs/codex-collaboration/recovery-and-journal.md
git commit -m "docs(t20260330-06): update contracts, promotion protocol, and recovery docs for widened discard, active_delegation, and busy gate"
```

---

## Task 6: Delegate Skill SKILL.md

**Files:**
- Create: `packages/plugins/codex-collaboration/skills/delegate/SKILL.md`

This is the full skill definition — the state-router UX over the delegate MCP tools. The skill body is written directly from the design spec. This task is a single Markdown file with no code tests, but the implementation must faithfully transcribe the design spec's grammar, state router, rendering, ceremony gates, and failure handling into SKILL.md format matching the existing skill patterns (consult-codex, dialogue).

- [ ] **Step 1: Create the skill directory**

```bash
mkdir -p packages/plugins/codex-collaboration/skills/delegate
```

- [ ] **Step 2: Write SKILL.md**

Create `packages/plugins/codex-collaboration/skills/delegate/SKILL.md` with:

1. Frontmatter: name, description, argument-hint, user-invocable, allowed-tools (from design spec Skill Frontmatter section).
2. Body sections transcribed from the design spec:
   - Overview (stateless state router)
   - Procedure entry: repo root, status preflight (auth, errors), parse arguments
   - Grammar: parse order, disambiguation, verb escapes
   - Start routing: call `codex.delegate.start`, handle normal/escalation/busy
   - Resume routing: call `codex.status`, extract `active_delegation`, poll, state router
   - State router: tiered precedence (promotion-first, then status)
   - Review rendering: job metadata, changed files, test results, diff, assessment, choices
   - Escalation rendering: header, requested_scope per kind, agent context, decision prompt
   - request_user_input handling: render questions, user answers, `/delegate approve` triggers construction
   - Escalation continuation: user-mediated re-escalation loop
   - Ceremony gates: review-before-promote, approve/deny requires escalation, never auto-promote
   - Failure handling table
   - Verb-specific procedures (poll, approve, deny, promote, discard)

Use the existing consult-codex and dialogue skills as structure references. The skill body should be self-contained — an engineer with only the SKILL.md should be able to implement the behavior.

- [ ] **Step 3: Verify skill loads**

Run: `ls packages/plugins/codex-collaboration/skills/delegate/SKILL.md`
Expected: File exists.

Check frontmatter is valid YAML by reading the first 15 lines and confirming no syntax errors.

- [ ] **Step 4: Commit**

```bash
git add packages/plugins/codex-collaboration/skills/delegate/SKILL.md
git commit -m "feat(t20260330-06): add delegate skill with full grammar, state router, and ceremony gates"
```

---

## Task 7: Final verification

- [ ] **Step 1: Run full test suite**

Run: `uv run --package codex-collaboration pytest packages/plugins/codex-collaboration/tests/ -v`
Expected: All tests pass. Count should be baseline (818) + new tests from Tasks 1-4.

- [ ] **Step 2: Run ruff**

Run: `ruff check packages/plugins/codex-collaboration/`
Expected: Clean, no violations.

- [ ] **Step 3: Verify skill is in the plugin manifest** (if applicable)

Check if `packages/plugins/codex-collaboration/plugin.json` auto-discovers skills or needs an explicit entry. If explicit, add the delegate skill.

- [ ] **Step 4: Bounded skill behavior verification**

The ticket requires "Run the delegate skill through a full execution and promotion cycle." Full live verification requires a running Codex App Server, which is out of scope for unit/integration tests. Instead, verify the skill behavior through the MCP integration test surface:

**4a. Verify the delegate lifecycle is exercisable through MCP tools:**
- Call `codex.delegate.start` → confirm job created
- Call `codex.status` → confirm `active_delegation` populated with correct job_id
- Call `codex.delegate.poll` → confirm state returned
- Call `codex.delegate.discard` → confirm `active_delegation` returns null

**4b. Verify the widened busy gate blocks correctly:**
- Start a job, confirm it completes
- Attempt second start → confirm `busy` response
- Discard → confirm second start now succeeds

**4c. Verify the SKILL.md is structurally valid:**
- Confirm frontmatter parses as valid YAML
- Confirm `allowed-tools` lists all 8 required tools (Bash, Read, 6 MCP tools)
- Confirm all grammar verbs (start, poll, approve, deny, promote, discard) are documented
- Confirm all state router tiers are present (terminal, recovery, user-decision, runtime)

**Residual risk:** The skill's rendering behavior (diff display, escalation formatting, ceremony gates) cannot be tested without a live Claude session invoking `/delegate`. This is a product-level acceptance test, not an implementation verification. The server-side behavior (the safety-bearing part) IS tested.

- [ ] **Step 5: Verify design spec coverage**

Cross-check the design spec sections against implementation:

| Design Section | Implementation |
|----------------|---------------|
| Singleton Invariant | Task 3 (widened busy gate) |
| User-Attention-Required Definition | Task 1 (`list_user_attention_required`) |
| Invocation Grammar | Task 6 (SKILL.md) |
| State Router | Task 6 (SKILL.md) |
| Review Rendering | Task 6 (SKILL.md) |
| Escalation Rendering | Task 6 (SKILL.md) |
| Ceremony Gates | Task 6 (SKILL.md) |
| Failure Handling | Task 6 (SKILL.md) |
| active_delegation Shape | Task 4 (MCP enrichment) |
| Widened Discard | Task 2 |
| Contract Updates | Task 5 |
