# Codex Delegate Poll Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `codex.delegate.poll` so callers can inspect delegation jobs through the merged typed contract, including pending-escalation projection, lazy review-snapshot materialization for completed jobs, and inspection-only snapshots for failed or unknown jobs.

**Architecture:** Keep the `poll` slice narrow but honest. Add a small inspection-artifact helper that materializes deterministic review artifacts under each delegation job directory, extend the job model/store so `promotion_state` matches the merged contract with an atomic lifecycle update op, then layer `DelegationController.poll()` and MCP dispatch on top. Do not fold in `codex.delegate.promote`, worktree cleanup, or the start/decide raw-`PendingServerRequest` serializer cleanup; those remain separate packets.

**Tech Stack:** Python 3.11, append-only JSONL stores, git subprocesses, MCP JSON-RPC dispatch, pytest, `uv`, `ruff`

---

## Scope Lock

### In Scope

1. Add the typed `codex.delegate.poll` MCP surface with required `job_id`.
2. Add poll result models for `Poll Rejection`, `Pending Escalation View`, `Artifact Inspection Snapshot`, and `Poll Result`.
3. Make `DelegationJob.promotion_state` nullable in code and align lifecycle writes with the merged contract:
   - `queued`, `running`, `needs_escalation`, `failed`, `unknown` => `promotion_state=None`
   - `completed` => `promotion_state="pending"`
4. Preserve replay/backcompat for legacy records that still carry `promotion_state="pending"` on non-completed jobs.
5. Materialize deterministic inspection artifacts on first poll of terminal jobs:
   - completed => review snapshot + stored hash
   - failed / unknown => inspection-only snapshot with `artifact_hash=None`
6. Persist completed-job review artifacts so repeated polls are idempotent and do not recompute.
7. Project `PendingServerRequest` into the narrower `Pending Escalation View` for `poll`.
8. Add targeted tests and end-to-end MCP coverage for completed, needs-escalation, failed, unknown, and job-not-found paths.
9. Add explicit PreToolUse policy wiring for the new `codex.delegate.poll` tool name.

### Explicitly Out Of Scope

1. `codex.delegate.promote`
2. `codex.delegate.discard`
3. Worktree cleanup TTL / deletion behavior
4. The raw `PendingServerRequest` leak in `codex.delegate.start` and `codex.delegate.decide`
5. `/delegate` skill UX
6. List mode or job enumeration in `codex.delegate.poll`
7. Automatic stale-advisory-context marking after promotion

### Design Locks

1. `codex.delegate.poll` remains single-job only. Input schema is `{ "job_id": string }`.
2. `poll` returns `Pending Escalation View`; do not silently widen this slice into start/decide serializer cleanup.
3. First poll of a completed job materializes a stable review snapshot under `${CLAUDE_PLUGIN_DATA}/runtimes/delegation/<job_id>/inspection/`.
4. The canonical review set for the hash is exactly three persisted files in v1:
   - `full.diff`
   - `changed-files.json`
   - `test-results.json`
5. `snapshot.json` may be written beside those files to persist `reviewed_at` and make repeat polls cheap, but `snapshot.json` does not participate in the review hash and does not go into `DelegationJob.artifact_paths`.
6. `snapshot.json` is the poll-cache authority. If it exists but the job store is missing `artifact_paths` / `artifact_hash`, `poll` rehydrates the store from the cached snapshot instead of recomputing from the worktree.
7. The worktree-local `.codex-collaboration/test-results.json` file is instrumentation output, not a user-facing changed file. Exclude it from `changed_files` and `full.diff`; represent test results only through the canonical persisted `test-results.json` inspection artifact.
8. The test-results record must be reproducible from `base_commit + worktree_path`. If the worktree does not contain a persisted test-results file, `poll` writes a deterministic `"not_recorded"` stub instead of guessing from `agent_message`.
9. Execution prompts must instruct the agent to persist test results at `.codex-collaboration/test-results.json` when it runs verification, but older jobs without that file still remain pollable through the deterministic stub.
10. Job lifecycle transitions that couple `status` and `promotion_state` must use a single append-only store op. A crash must not be able to strand a job in `status="completed"` with `promotion_state=None`.
11. `unknown` after recovery is inspection-only. `poll` should explain restart/discard territory in `detail`; it must not pretend the outcome is known-good.

## File Structure

### New Production File

| Path | Responsibility |
|---|---|
| `packages/plugins/codex-collaboration/server/artifact_store.py` | Deterministically materialize and reload poll inspection artifacts, including canonical diff/manifest/test-results files and review-hash computation. |

### Modified Production Files

| Path | Responsibility In This Slice |
|---|---|
| `packages/plugins/codex-collaboration/server/models.py` | Add poll result dataclasses and make `DelegationJob.promotion_state` nullable. |
| `packages/plugins/codex-collaboration/server/delegation_job_store.py` | Accept nullable promotion state, add an atomic lifecycle update op plus artifact update operations, and replay them safely. |
| `packages/plugins/codex-collaboration/server/delegation_controller.py` | Align lifecycle writes with nullable `promotion_state`, implement `poll()`, project pending escalations, and load/materialize inspection snapshots. |
| `packages/plugins/codex-collaboration/server/mcp_server.py` | Register and dispatch `codex.delegate.poll`. |
| `packages/plugins/codex-collaboration/server/consultation_safety.py` | Add a total policy entry for `codex.delegate.poll`. |
| `packages/plugins/codex-collaboration/server/execution_prompt_builder.py` | Instruct execution turns to persist deterministic test-results records in the worktree. |
| `packages/plugins/codex-collaboration/server/__init__.py` | Export poll result types if they are part of the public server surface. |
| `packages/plugins/codex-collaboration/scripts/codex_runtime_bootstrap.py` | Construct and inject `ArtifactStore` into `DelegationController`. |

### Modified Test Files

| Path | Coverage Added |
|---|---|
| `packages/plugins/codex-collaboration/tests/test_models_r2.py` | Poll dataclass shapes and nullable `promotion_state`. |
| `packages/plugins/codex-collaboration/tests/test_delegation_job_store.py` | Nullable promotion-state replay, atomic lifecycle replay, artifact update replay, and legacy-record acceptance. |
| `packages/plugins/codex-collaboration/tests/test_artifact_store.py` | Canonical review-set materialization, deterministic hash recipe, and missing-test-results stub behavior. |
| `packages/plugins/codex-collaboration/tests/test_execution_prompt_builder.py` | Execution prompt instructions for deterministic test-results persistence. |
| `packages/plugins/codex-collaboration/tests/test_delegation_controller.py` | Poll happy paths, poll rejection, repeat-poll idempotence, snapshot-store rehydration, and promotion-state lifecycle alignment. |
| `packages/plugins/codex-collaboration/tests/test_mcp_server.py` | Tool definition, schema, dispatch, and poll serialization. |
| `packages/plugins/codex-collaboration/tests/test_consultation_safety.py` | Policy lookup for `codex.delegate.poll`. |
| `packages/plugins/codex-collaboration/tests/test_codex_guard.py` | Hook-guard clean path for the new tool name. |
| `packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py` | End-to-end `start -> poll` completed and `start -> escalate -> poll` projection paths. |

## Acceptance Coverage For This Plan

| Requirement | Planned Task |
|---|---|
| Delegation results can be polled through the typed `codex.delegate.poll` surface | Tasks 1, 3, and 4 |
| `poll` exposes a typed pending-escalation projection without raw internal Codex IDs | Tasks 1, 3, and 4 |
| Completed jobs materialize review artifacts and store a deterministic reviewed hash | Tasks 2 and 3 |
| Failed / unknown jobs remain inspectable without pretending they are promotion-ready | Tasks 2 and 3 |
| Merged contract for nullable/backcompat-aware `promotion_state` becomes real in code | Tasks 1 and 3 |
| Poll remains out of scope for promote/discard logic | Scope lock + Task 3 tests |

## Pre-Flight

- [ ] **Step P0: Work in a dedicated implementation worktree**

Run:

```bash
git worktree add ../claude-code-tool-dev-poll -b feature/t06-delegate-poll main
```

Expected:

- a fresh sibling worktree exists at `../claude-code-tool-dev-poll`
- the new branch is `feature/t06-delegate-poll`
- the dirty files in the current checkout do not contaminate implementation work

- [ ] **Step P1: Re-anchor on live `main` before editing**

Run:

```bash
git branch --show-current
git rev-parse --short HEAD
git status --short --branch
```

Expected:

- branch is `main` before creating the worktree, then `feature/t06-delegate-poll` inside the worktree
- `HEAD` is `db7fd1da` or a consciously-reviewed newer mainline commit
- the implementation worktree starts clean

- [ ] **Step P2: Confirm the current delegation baseline is green**

Run:

```bash
uv run pytest \
  packages/plugins/codex-collaboration/tests/test_delegation_controller.py \
  packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py \
  packages/plugins/codex-collaboration/tests/test_mcp_server.py \
  packages/plugins/codex-collaboration/tests/test_delegation_job_store.py \
  -q
```

Expected:

- PASS on the current start/decide substrate before layering `poll`

If baseline is red, stop and fix that first. Do not stack `poll` changes on a broken delegation base.

---

### Task 1: Pin Poll Types And Job-Store Contract

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/models.py`
- Modify: `packages/plugins/codex-collaboration/server/delegation_job_store.py`
- Modify: `packages/plugins/codex-collaboration/server/__init__.py`
- Test: `packages/plugins/codex-collaboration/tests/test_models_r2.py`
- Test: `packages/plugins/codex-collaboration/tests/test_delegation_job_store.py`

- [ ] **Step 1: Write the failing model/store tests**

Add to `packages/plugins/codex-collaboration/tests/test_models_r2.py`:

```python
def test_delegation_job_allows_nullable_promotion_state() -> None:
    from server.models import DelegationJob

    job = DelegationJob(
        job_id="job-1",
        runtime_id="rt-1",
        collaboration_id="collab-1",
        base_commit="abc123",
        worktree_path="/tmp/wk",
        promotion_state=None,
        status="queued",
    )

    assert job.promotion_state is None


def test_poll_result_shapes() -> None:
    from server.models import (
        ArtifactInspectionSnapshot,
        DelegationJob,
        DelegationPollResult,
        PendingEscalationView,
        PollRejectedResponse,
    )

    job = DelegationJob(
        job_id="job-1",
        runtime_id="rt-1",
        collaboration_id="collab-1",
        base_commit="abc123",
        worktree_path="/tmp/wk",
        promotion_state="pending",
        status="completed",
        artifact_paths=("/tmp/wk/inspection/full.diff",),
        artifact_hash="abc",
    )
    pending = PendingEscalationView(
        request_id="req-1",
        kind="command_approval",
        requested_scope={"command": "make test"},
        available_decisions=("approve", "deny"),
    )
    inspection = ArtifactInspectionSnapshot(
        artifact_hash="abc",
        artifact_paths=("/tmp/wk/inspection/full.diff",),
        changed_files=("README.md",),
        reviewed_at="2026-04-20T00:00:00Z",
    )

    result = DelegationPollResult(
        job=job,
        pending_escalation=pending,
        inspection=inspection,
        detail="Completed and ready for review.",
    )
    rejected = PollRejectedResponse(
        rejected=True,
        reason="job_not_found",
        detail="Delegation poll failed: job not found. Got: 'job-404'",
        job_id="job-404",
    )

    assert result.job.job_id == "job-1"
    assert result.pending_escalation is pending
    assert result.inspection is inspection
    assert rejected.reason == "job_not_found"
```

Add to `packages/plugins/codex-collaboration/tests/test_delegation_job_store.py`:

```python
def _make_job(
    job_id: str = "job-1",
    runtime_id: str = "rt-1",
    status: str = "queued",
    promotion_state: str | None = "pending",
) -> DelegationJob:
    return DelegationJob(
        job_id=job_id,
        runtime_id=runtime_id,
        collaboration_id=f"collab-{job_id}",
        base_commit="abc123",
        worktree_path=f"/tmp/wk-{job_id}",
        promotion_state=promotion_state,  # type: ignore[arg-type]
        status=status,  # type: ignore[arg-type]
    )


def test_update_status_and_promotion_last_write_wins(tmp_path: Path) -> None:
    store = DelegationJobStore(tmp_path, "sess-1")
    store.create(_make_job(job_id="job-1", status="queued", promotion_state=None))

    store.update_status_and_promotion(
        "job-1",
        status="completed",
        promotion_state="pending",
    )

    job = store.get("job-1")
    assert job is not None
    assert job.status == "completed"
    assert job.promotion_state == "pending"


def test_update_artifacts_last_write_wins(tmp_path: Path) -> None:
    store = DelegationJobStore(tmp_path, "sess-1")
    store.create(_make_job(job_id="job-1", status="completed", promotion_state="pending"))

    store.update_artifacts(
        "job-1",
        artifact_paths=("/tmp/inspection/full.diff", "/tmp/inspection/test-results.json"),
        artifact_hash="sha-1",
    )

    job = store.get("job-1")
    assert job is not None
    assert job.artifact_paths == (
        "/tmp/inspection/full.diff",
        "/tmp/inspection/test-results.json",
    )
    assert job.artifact_hash == "sha-1"


def test_replay_accepts_legacy_pending_on_non_completed_job(tmp_path: Path) -> None:
    import json

    store_path = tmp_path / "delegation_jobs" / "sess-1" / "jobs.jsonl"
    store_path.parent.mkdir(parents=True)
    with store_path.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "op": "create",
                    "job_id": "job-legacy",
                    "runtime_id": "rt-1",
                    "collaboration_id": "c-1",
                    "base_commit": "abc",
                    "worktree_path": "/tmp/wk",
                    "promotion_state": "pending",
                    "status": "queued",
                    "artifact_paths": [],
                    "artifact_hash": None,
                }
            )
            + "\n"
        )

    replay = DelegationJobStore(tmp_path, "sess-1")
    job = replay.get("job-legacy")
    assert job is not None
    assert job.status == "queued"
    assert job.promotion_state == "pending"
```

- [ ] **Step 2: Run the targeted tests to verify the gap**

Run:

```bash
uv run pytest \
  packages/plugins/codex-collaboration/tests/test_models_r2.py \
  packages/plugins/codex-collaboration/tests/test_delegation_job_store.py \
  -q
```

Expected:

- FAIL with one or more of:
  - `TypeError` because `DelegationJob` rejects `promotion_state=None`
  - `ImportError` for missing poll result classes
  - `AttributeError` because `DelegationJobStore` has no `update_status_and_promotion` or `update_artifacts`

- [ ] **Step 3: Implement the model/store contract**

In `packages/plugins/codex-collaboration/server/models.py`, add the poll types and make `promotion_state` nullable:

```python
PollRejectedReason = Literal["job_not_found"]


@dataclass(frozen=True)
class DelegationJob:
    job_id: str
    runtime_id: str
    collaboration_id: str
    base_commit: str
    worktree_path: str
    promotion_state: PromotionState | None
    status: JobStatus
    artifact_paths: tuple[str, ...] = ()
    artifact_hash: str | None = None


@dataclass(frozen=True)
class PendingEscalationView:
    request_id: str
    kind: PendingRequestKind
    requested_scope: dict[str, Any]
    available_decisions: tuple[str, ...]


@dataclass(frozen=True)
class ArtifactInspectionSnapshot:
    artifact_hash: str | None
    artifact_paths: tuple[str, ...]
    changed_files: tuple[str, ...]
    reviewed_at: str


@dataclass(frozen=True)
class DelegationPollResult:
    job: DelegationJob
    pending_escalation: PendingEscalationView | None = None
    inspection: ArtifactInspectionSnapshot | None = None
    detail: str | None = None


@dataclass(frozen=True)
class PollRejectedResponse:
    rejected: bool
    reason: PollRejectedReason
    detail: str
    job_id: str | None = None
```

In `packages/plugins/codex-collaboration/server/delegation_job_store.py`, accept nullable promotion states and replay the new update operations:

```python
_VALID_PROMOTION_STATES: frozenset[str] = frozenset(get_args(PromotionState))


def _is_valid_promotion_state(value: object) -> bool:
    return value is None or value in _VALID_PROMOTION_STATES


def update_status_and_promotion(
    self,
    job_id: str,
    *,
    status: JobStatus,
    promotion_state: PromotionState | None,
) -> None:
    if status not in _VALID_STATUSES:
        raise ValueError(
            "DelegationJobStore.update_status_and_promotion failed: unknown status. "
            f"Got: {status!r:.100}"
        )
    if not _is_valid_promotion_state(promotion_state):
        raise ValueError(
            "DelegationJobStore.update_status_and_promotion failed: unknown promotion_state. "
            f"Got: {promotion_state!r:.100}"
        )
    self._append(
        {
            "op": "update_status_and_promotion",
            "job_id": job_id,
            "status": status,
            "promotion_state": promotion_state,
        }
    )


def update_artifacts(
    self,
    job_id: str,
    *,
    artifact_paths: tuple[str, ...],
    artifact_hash: str | None,
) -> None:
    self._append(
        {
            "op": "update_artifacts",
            "job_id": job_id,
            "artifact_paths": list(artifact_paths),
            "artifact_hash": artifact_hash,
        }
    )
```

Extend `_replay()` so `create`, `update_status_and_promotion`, and `update_artifacts` all use `_is_valid_promotion_state()` and convert list-backed `artifact_paths` to tuples before instantiating `DelegationJob`.

In `packages/plugins/codex-collaboration/server/__init__.py`, export the new public result types:

```python
from .models import (
    ArtifactInspectionSnapshot,
    PendingEscalationView,
    DelegationPollResult,
    PollRejectedResponse,
)

__all__ = [
    "ArtifactInspectionSnapshot",
    "PendingEscalationView",
    "DelegationPollResult",
    "PollRejectedResponse",
    # keep the existing exports below this line
]
```

- [ ] **Step 4: Re-run the targeted tests to verify the contract passes**

Run:

```bash
uv run pytest \
  packages/plugins/codex-collaboration/tests/test_models_r2.py \
  packages/plugins/codex-collaboration/tests/test_delegation_job_store.py \
  -q
```

Expected:

- PASS

- [ ] **Step 5: Commit the contract groundwork**

Run:

```bash
git add \
  packages/plugins/codex-collaboration/server/models.py \
  packages/plugins/codex-collaboration/server/delegation_job_store.py \
  packages/plugins/codex-collaboration/server/__init__.py \
  packages/plugins/codex-collaboration/tests/test_models_r2.py \
  packages/plugins/codex-collaboration/tests/test_delegation_job_store.py
git commit -m "feat(t20260330-06): pin poll model and job-store contract"
```

Expected:

- one commit containing only model/store groundwork

---

### Task 2: Add Deterministic Inspection Artifact Materialization

**Files:**
- Create: `packages/plugins/codex-collaboration/server/artifact_store.py`
- Modify: `packages/plugins/codex-collaboration/server/execution_prompt_builder.py`
- Test: `packages/plugins/codex-collaboration/tests/test_artifact_store.py`
- Test: `packages/plugins/codex-collaboration/tests/test_execution_prompt_builder.py`

- [ ] **Step 1: Write the failing artifact-store and prompt tests**

Create `packages/plugins/codex-collaboration/tests/test_artifact_store.py`:

```python
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from server.artifact_store import ArtifactStore
from server.models import DelegationJob


def _init_repo(repo_path: Path) -> str:
    repo_path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "--initial-branch=main"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)
    (repo_path / "README.md").write_text("hello\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo_path, check=True)
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def test_materialize_completed_snapshot_writes_canonical_files_and_hash(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    base_commit = _init_repo(repo_root)
    (repo_root / "README.md").write_text("hello\nworld\n", encoding="utf-8")
    (repo_root / "new_file.py").write_text("print('hi')\n", encoding="utf-8")
    results_path = repo_root / ".codex-collaboration" / "test-results.json"
    results_path.parent.mkdir(parents=True)
    results_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "status": "passed",
                "commands": ["uv run pytest -q"],
                "summary": "1 passed",
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    store = ArtifactStore(tmp_path / "plugin-data", timestamp_factory=lambda: "2026-04-20T10:00:00Z")
    snapshot = store.materialize_snapshot(
        job=DelegationJob(
            job_id="job-1",
            runtime_id="rt-1",
            collaboration_id="collab-1",
            base_commit=base_commit,
            worktree_path=str(repo_root),
            promotion_state="pending",
            status="completed",
        )
    )

    assert snapshot.artifact_hash is not None
    assert [Path(p).name for p in snapshot.artifact_paths] == [
        "full.diff",
        "changed-files.json",
        "test-results.json",
    ]
    assert snapshot.changed_files == ("README.md", "new_file.py")
    full_diff = Path(snapshot.artifact_paths[0]).read_text(encoding="utf-8")
    assert ".codex-collaboration/test-results.json" not in full_diff


def test_materialize_completed_snapshot_hash_matches_spec_recipe(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    base_commit = _init_repo(repo_root)
    (repo_root / "README.md").write_text("hello\nworld\n", encoding="utf-8")
    results_path = repo_root / ".codex-collaboration" / "test-results.json"
    results_path.parent.mkdir(parents=True)
    results_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "status": "passed",
                "commands": ["uv run pytest -q"],
                "summary": "1 passed",
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    store = ArtifactStore(tmp_path / "plugin-data", timestamp_factory=lambda: "2026-04-20T10:00:00Z")
    snapshot = store.materialize_snapshot(
        job=DelegationJob(
            job_id="job-4",
            runtime_id="rt-4",
            collaboration_id="collab-4",
            base_commit=base_commit,
            worktree_path=str(repo_root),
            promotion_state="pending",
            status="completed",
        )
    )

    inspection_dir = Path(snapshot.artifact_paths[0]).parent
    expected = hashlib.sha256()
    for artifact_path in snapshot.artifact_paths:
        path = Path(artifact_path)
        expected.update(path.relative_to(inspection_dir).as_posix().encode("utf-8"))
        expected.update(b"\0")
        expected.update(path.read_bytes())

    assert snapshot.artifact_hash == expected.hexdigest()


def test_materialize_unknown_snapshot_omits_hash(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    base_commit = _init_repo(repo_root)
    (repo_root / "README.md").write_text("unknown-state\n", encoding="utf-8")

    store = ArtifactStore(tmp_path / "plugin-data", timestamp_factory=lambda: "2026-04-20T10:00:00Z")
    snapshot = store.materialize_snapshot(
        job=DelegationJob(
            job_id="job-2",
            runtime_id="rt-2",
            collaboration_id="collab-2",
            base_commit=base_commit,
            worktree_path=str(repo_root),
            promotion_state=None,
            status="unknown",
        )
    )

    assert snapshot.artifact_hash is None
    assert snapshot.changed_files == ("README.md",)


def test_missing_test_results_file_produces_deterministic_stub(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    base_commit = _init_repo(repo_root)
    (repo_root / "README.md").write_text("changed\n", encoding="utf-8")

    store = ArtifactStore(tmp_path / "plugin-data", timestamp_factory=lambda: "2026-04-20T10:00:00Z")
    snapshot = store.materialize_snapshot(
        job=DelegationJob(
            job_id="job-3",
            runtime_id="rt-3",
            collaboration_id="collab-3",
            base_commit=base_commit,
            worktree_path=str(repo_root),
            promotion_state="pending",
            status="completed",
        )
    )

    test_results_path = Path(snapshot.artifact_paths[2])
    record = json.loads(test_results_path.read_text(encoding="utf-8"))
    assert record["status"] == "not_recorded"
    assert record["source_path"] == ".codex-collaboration/test-results.json"
```

Extend `packages/plugins/codex-collaboration/tests/test_execution_prompt_builder.py`:

```python
def test_build_execution_turn_text_instructs_agent_to_persist_test_results() -> None:
    result = build_execution_turn_text(
        objective="Add tests",
        worktree_path="/wt/abc",
    )

    assert ".codex-collaboration/test-results.json" in result
    assert "schema_version" in result
    assert "commands" in result


def test_build_execution_resume_turn_text_repeats_test_results_requirement() -> None:
    from server.execution_prompt_builder import build_execution_resume_turn_text

    request = PendingServerRequest(
        request_id="req-1",
        runtime_id="rt-1",
        collaboration_id="collab-1",
        codex_thread_id="thr-1",
        codex_turn_id="turn-1",
        item_id="item-1",
        kind="command_approval",
        requested_scope={"command": "uv run pytest -q"},
        status="resolved",
    )

    result = build_execution_resume_turn_text(
        pending_request=request,
        answers=None,
    )

    assert ".codex-collaboration/test-results.json" in result
    assert "status" in result
```

- [ ] **Step 2: Run the new tests and verify they fail**

Run:

```bash
uv run pytest \
  packages/plugins/codex-collaboration/tests/test_artifact_store.py \
  packages/plugins/codex-collaboration/tests/test_execution_prompt_builder.py \
  -q
```

Expected:

- FAIL because `server.artifact_store` does not exist yet
- FAIL because the execution prompt builders do not mention deterministic test-results persistence

- [ ] **Step 3: Implement `ArtifactStore` and prompt instructions**

Create `packages/plugins/codex-collaboration/server/artifact_store.py`:

```python
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Callable

from .models import ArtifactInspectionSnapshot, DelegationJob

TEST_RESULTS_RECORD_RELATIVE_PATH = ".codex-collaboration/test-results.json"


class ArtifactStore:
    def __init__(
        self,
        plugin_data_path: Path,
        *,
        timestamp_factory: Callable[[], str],
    ) -> None:
        self._plugin_data_path = plugin_data_path
        self._timestamp_factory = timestamp_factory

    def materialize_snapshot(self, *, job: DelegationJob) -> ArtifactInspectionSnapshot:
        inspection_dir = self._inspection_dir(job.job_id)
        inspection_dir.mkdir(parents=True, exist_ok=True)

        changed_files = self._changed_files(job)
        full_diff_path = inspection_dir / "full.diff"
        changed_files_path = inspection_dir / "changed-files.json"
        test_results_path = inspection_dir / "test-results.json"
        snapshot_path = inspection_dir / "snapshot.json"

        full_diff_path.write_text(self._full_diff(job, changed_files), encoding="utf-8")
        changed_files_path.write_text(
            json.dumps({"changed_files": list(changed_files)}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        test_results_path.write_text(
            json.dumps(self._test_results_record(Path(job.worktree_path)), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        artifact_paths = (
            str(full_diff_path),
            str(changed_files_path),
            str(test_results_path),
        )
        artifact_hash = self._review_hash(inspection_dir, artifact_paths) if job.status == "completed" else None
        reviewed_at = self._timestamp_factory()

        snapshot = ArtifactInspectionSnapshot(
            artifact_hash=artifact_hash,
            artifact_paths=artifact_paths,
            changed_files=changed_files,
            reviewed_at=reviewed_at,
        )
        snapshot_path.write_text(
            json.dumps(
                {
                    "artifact_hash": snapshot.artifact_hash,
                    "artifact_paths": list(snapshot.artifact_paths),
                    "changed_files": list(snapshot.changed_files),
                    "reviewed_at": snapshot.reviewed_at,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return snapshot

    def load_snapshot(self, *, job: DelegationJob) -> ArtifactInspectionSnapshot | None:
        snapshot_path = self._inspection_dir(job.job_id) / "snapshot.json"
        if not snapshot_path.exists():
            return None
        payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
        return ArtifactInspectionSnapshot(
            artifact_hash=payload["artifact_hash"],
            artifact_paths=tuple(payload["artifact_paths"]),
            changed_files=tuple(payload["changed_files"]),
            reviewed_at=payload["reviewed_at"],
        )

    def _inspection_dir(self, job_id: str) -> Path:
        return self._plugin_data_path / "runtimes" / "delegation" / job_id / "inspection"

    def _changed_files(self, job: DelegationJob) -> tuple[str, ...]:
        tracked = subprocess.run(
            ["git", "-C", job.worktree_path, "diff", "--name-only", job.base_commit, "--"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        untracked = subprocess.run(
            ["git", "-C", job.worktree_path, "ls-files", "--others", "--exclude-standard"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        return tuple(
            sorted(
                {
                    path
                    for path in tracked + untracked
                    if path and path != TEST_RESULTS_RECORD_RELATIVE_PATH
                }
            )
        )

    def _full_diff(self, job: DelegationJob, changed_files: tuple[str, ...]) -> str:
        tracked_diff = subprocess.run(
            [
                "git",
                "-C",
                job.worktree_path,
                "diff",
                "--binary",
                "--no-color",
                job.base_commit,
                "--",
                ".",
                f":!{TEST_RESULTS_RECORD_RELATIVE_PATH}",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        sections = [tracked_diff.rstrip()]
        worktree = Path(job.worktree_path)
        tracked_set = set(
            subprocess.run(
                ["git", "-C", job.worktree_path, "diff", "--name-only", job.base_commit, "--"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.splitlines()
        )
        for relative_path in changed_files:
            if relative_path in tracked_set:
                continue
            file_path = worktree / relative_path
            extra = subprocess.run(
                ["git", "diff", "--no-index", "--binary", "--no-color", "--", "/dev/null", str(file_path)],
                check=False,
                capture_output=True,
                text=True,
            ).stdout
            if extra:
                sections.append(extra.rstrip())
        return "\n\n".join(section for section in sections if section) + "\n"

    def _test_results_record(self, worktree_path: Path) -> dict[str, Any]:
        record_path = worktree_path / TEST_RESULTS_RECORD_RELATIVE_PATH
        if not record_path.exists():
            return {
                "schema_version": 1,
                "status": "not_recorded",
                "commands": [],
                "summary": "Execution agent did not persist test results.",
                "source_path": TEST_RESULTS_RECORD_RELATIVE_PATH,
            }
        return json.loads(record_path.read_text(encoding="utf-8"))

    def _review_hash(self, inspection_dir: Path, artifact_paths: tuple[str, ...]) -> str:
        sha = hashlib.sha256()
        for artifact_path in artifact_paths:
            path = Path(artifact_path)
            relative_path = path.relative_to(inspection_dir).as_posix().encode("utf-8")
            sha.update(relative_path)
            sha.update(b"\0")
            sha.update(path.read_bytes())
        return sha.hexdigest()
```

In `packages/plugins/codex-collaboration/server/execution_prompt_builder.py`, import the shared path constant and tell the execution agent exactly what to write:

```python
from .artifact_store import TEST_RESULTS_RECORD_RELATIVE_PATH


def build_execution_turn_text(*, objective: str, worktree_path: str) -> str:
    return (
        "You are working in an isolated worktree. Your workspace is:\n"
        f"  {worktree_path}\n\n"
        "Objective:\n"
        f"  {objective}\n\n"
        "When you run verification, persist a deterministic test-results record at:\n"
        f"  {TEST_RESULTS_RECORD_RELATIVE_PATH}\n"
        "Write JSON with keys: schema_version, status, commands, summary.\n"
        "Work within the worktree boundary. Commands that require approval "
        "will be escalated to the caller for review."
    )


def build_execution_resume_turn_text(
    *,
    pending_request: PendingServerRequest,
    answers: dict[str, tuple[str, ...]] | None,
) -> str:
    requested_scope = json.dumps(
        pending_request.requested_scope,
        indent=2,
        sort_keys=True,
    )
    lines = [
        "Continue the existing isolated delegation thread.",
        "The earlier server request has already been resolved at the wire layer.",
        "Do not re-ask for the same approval; treat the caller decision below as authoritative.",
        f"Persist verification output at {TEST_RESULTS_RECORD_RELATIVE_PATH} when you run tests.",
        "",
        f"Escalation kind: {pending_request.kind}",
        f"Request id: {pending_request.request_id}",
        "Captured request scope:",
        requested_scope,
    ]
    if answers:
        answer_payload = json.dumps(
            {key: {"answers": list(value)} for key, value in answers.items()},
            indent=2,
            sort_keys=True,
        )
        lines.extend(
            [
                "",
                "Caller-supplied answers:",
                answer_payload,
            ]
        )
    return "\n".join(lines)
```

- [ ] **Step 4: Re-run the artifact and prompt tests**

Run:

```bash
uv run pytest \
  packages/plugins/codex-collaboration/tests/test_artifact_store.py \
  packages/plugins/codex-collaboration/tests/test_execution_prompt_builder.py \
  -q
```

Expected:

- PASS

- [ ] **Step 5: Commit the artifact materialization layer**

Run:

```bash
git add \
  packages/plugins/codex-collaboration/server/artifact_store.py \
  packages/plugins/codex-collaboration/server/execution_prompt_builder.py \
  packages/plugins/codex-collaboration/tests/test_artifact_store.py \
  packages/plugins/codex-collaboration/tests/test_execution_prompt_builder.py
git commit -m "feat(t20260330-06): add delegation poll artifact materialization"
```

Expected:

- one commit containing the deterministic review-artifact helper and prompt contract

---

### Task 3: Implement Controller Poll Flow And Honest Lifecycle Transitions

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/delegation_controller.py`
- Modify: `packages/plugins/codex-collaboration/scripts/codex_runtime_bootstrap.py`
- Test: `packages/plugins/codex-collaboration/tests/test_delegation_controller.py`

- [ ] **Step 1: Write the failing controller tests**

Add to `packages/plugins/codex-collaboration/tests/test_delegation_controller.py`:

```python
class _FakeArtifactStore:
    def __init__(self) -> None:
        self._snapshots: dict[str, ArtifactInspectionSnapshot] = {}

    def materialize_snapshot(
        self, *, job: DelegationJob
    ) -> ArtifactInspectionSnapshot:
        snapshot = ArtifactInspectionSnapshot(
            artifact_hash=f"hash-{job.job_id}" if job.status == "completed" else None,
            artifact_paths=(
                f"/tmp/inspection/{job.job_id}/full.diff",
                f"/tmp/inspection/{job.job_id}/changed-files.json",
                f"/tmp/inspection/{job.job_id}/test-results.json",
            ),
            changed_files=("README.md",),
            reviewed_at="2026-04-20T10:00:00Z",
        )
        self._snapshots[job.job_id] = snapshot
        return snapshot

    def load_snapshot(
        self, *, job: DelegationJob
    ) -> ArtifactInspectionSnapshot | None:
        return self._snapshots.get(job.job_id)


def _build_controller(
    tmp_path: Path,
    *,
    head_sha: str = "head-abc",
    session_id: str = "sess-1",
) -> tuple[
    DelegationController,
    _FakeControlPlane,
    _FakeWorktreeManager,
    DelegationJobStore,
    LineageStore,
    OperationJournal,
    ExecutionRuntimeRegistry,
    PendingRequestStore,
]:
    plugin_data = tmp_path / "data"
    plugin_data.mkdir(parents=True, exist_ok=True)
    job_store = DelegationJobStore(plugin_data, session_id)
    lineage_store = LineageStore(plugin_data, session_id)
    journal = OperationJournal(plugin_data)
    pending_request_store = PendingRequestStore(plugin_data, session_id)
    control_plane = _FakeControlPlane()
    worktree_manager = _FakeWorktreeManager()
    registry = ExecutionRuntimeRegistry()
    uuid_counter = iter(
        [
            "job-1",
            "collab-1",
            "delegate-start-evt-1",
            "escalation-evt-1",
            "decision-evt-1",
            "re-escalation-evt-1",
            "job-2",
            "collab-2",
            "delegate-start-evt-2",
            "escalation-evt-2",
        ]
    )
    artifact_store = _FakeArtifactStore()
    controller = DelegationController(
        control_plane=control_plane,
        worktree_manager=worktree_manager,
        job_store=job_store,
        lineage_store=lineage_store,
        runtime_registry=registry,
        journal=journal,
        session_id=session_id,
        plugin_data_path=plugin_data,
        pending_request_store=pending_request_store,
        artifact_store=artifact_store,
        head_commit_resolver=lambda repo_root: head_sha,
        uuid_factory=lambda: next(uuid_counter),
    )
    return (
        controller,
        control_plane,
        worktree_manager,
        job_store,
        lineage_store,
        journal,
        registry,
        pending_request_store,
    )


def test_start_completed_job_sets_promotion_state_pending(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    controller, _cp, _wm, job_store, _lineage, _journal, _registry, _prs = _build_controller(tmp_path)

    result = controller.start(repo_root=repo_root)

    assert isinstance(result, DelegationJob)
    assert result.status == "completed"
    assert result.promotion_state == "pending"
    persisted = job_store.get(result.job_id)
    assert persisted is not None
    assert persisted.promotion_state == "pending"


def test_start_escalation_keeps_promotion_state_none(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    controller, control_plane, _wm, job_store, _lineage, _journal, _registry, _prs = _build_controller(tmp_path)
    control_plane._next_session_requests = [_command_approval_request()]

    result = controller.start(repo_root=repo_root)

    assert isinstance(result, DelegationEscalation)
    assert result.job.status == "needs_escalation"
    assert result.job.promotion_state is None
    persisted = job_store.get(result.job.job_id)
    assert persisted is not None
    assert persisted.promotion_state is None


def test_poll_completed_job_materializes_snapshot_and_reuses_it(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    controller, _cp, _wm, job_store, _lineage, _journal, _registry, _prs = _build_controller(tmp_path)

    start_result = controller.start(repo_root=repo_root)
    assert isinstance(start_result, DelegationJob)
    first = controller.poll(job_id=start_result.job_id)
    second = controller.poll(job_id=start_result.job_id)

    assert isinstance(first, DelegationPollResult)
    assert first.inspection is not None
    assert first.inspection.artifact_hash is not None
    assert second.inspection == first.inspection


def test_poll_rehydrates_store_from_cached_snapshot_when_artifacts_are_missing(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    controller, _cp, _wm, job_store, _lineage, _journal, _registry, _prs = _build_controller(tmp_path)

    start_result = controller.start(repo_root=repo_root)
    assert isinstance(start_result, DelegationJob)
    first = controller.poll(job_id=start_result.job_id)
    assert isinstance(first, DelegationPollResult)
    assert first.inspection is not None

    job_store.update_artifacts(
        start_result.job_id,
        artifact_paths=(),
        artifact_hash=None,
    )

    second = controller.poll(job_id=start_result.job_id)
    persisted = job_store.get(start_result.job_id)

    assert isinstance(second, DelegationPollResult)
    assert second.inspection == first.inspection
    assert persisted is not None
    assert persisted.artifact_paths == first.inspection.artifact_paths
    assert persisted.artifact_hash == first.inspection.artifact_hash


def test_poll_needs_escalation_projects_pending_request_without_raw_ids(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    controller, control_plane, _wm, _job_store, _lineage, _journal, _registry, _prs = _build_controller(tmp_path)
    control_plane._next_session_requests = [_command_approval_request()]

    start_result = controller.start(repo_root=repo_root)
    assert isinstance(start_result, DelegationEscalation)

    polled = controller.poll(job_id=start_result.job.job_id)

    assert isinstance(polled, DelegationPollResult)
    assert polled.pending_escalation is not None
    assert polled.pending_escalation.request_id == "42"
    assert not hasattr(polled.pending_escalation, "codex_thread_id")


def test_poll_returns_job_not_found_rejection(tmp_path: Path) -> None:
    controller, _cp, _wm, _js, _lineage, _journal, _registry, _prs = _build_controller(tmp_path)

    result = controller.poll(job_id="job-missing")

    assert isinstance(result, PollRejectedResponse)
    assert result.reason == "job_not_found"
```

- [ ] **Step 2: Run the controller tests to verify the missing behavior**

Run:

```bash
uv run pytest packages/plugins/codex-collaboration/tests/test_delegation_controller.py -q
```

Expected:

- FAIL because `DelegationController` has no `poll()` method
- FAIL because lifecycle writes still seed `"pending"` at job creation and never clear/set it honestly

- [ ] **Step 3: Implement `poll()` and the lifecycle transition helper**

In `packages/plugins/codex-collaboration/server/delegation_controller.py`, inject `ArtifactStore`, add a status-to-promotion-state helper, and implement `poll()`:

```python
from .artifact_store import ArtifactStore
from .models import (
    ArtifactInspectionSnapshot,
    DelegationPollResult,
    PendingEscalationView,
    PollRejectedResponse,
)


class DelegationController:
    def __init__(
        self,
        *,
        control_plane: _ControlPlaneLike,
        worktree_manager: _WorktreeManagerLike,
        job_store: DelegationJobStore,
        lineage_store: LineageStore,
        runtime_registry: ExecutionRuntimeRegistry,
        journal: OperationJournal,
        session_id: str,
        plugin_data_path: Path,
        pending_request_store: PendingRequestStore,
        artifact_store: ArtifactStore,
        approval_policy: str = "untrusted",
        head_commit_resolver: Callable[[Path], str] | None = None,
        uuid_factory: Callable[[], str] | None = None,
    ) -> None:
        self._control_plane = control_plane
        self._worktree_manager = worktree_manager
        self._job_store = job_store
        self._lineage_store = lineage_store
        self._runtime_registry = runtime_registry
        self._journal = journal
        self._session_id = session_id
        self._plugin_data_path = plugin_data_path
        self._pending_request_store = pending_request_store
        self._artifact_store = artifact_store
        self._approval_policy = approval_policy
        self._head_commit_resolver = head_commit_resolver or _resolve_head_commit
        self._uuid_factory = uuid_factory or (lambda: str(uuid.uuid4()))
        self._decided_request_ids: set[str] = set()

    def _persist_job_transition(self, job_id: str, status: JobStatus) -> DelegationJob:
        # One compound append keeps replay honest: completed jobs must not be
        # strandable as status="completed" with promotion_state=None.
        self._job_store.update_status_and_promotion(
            job_id,
            status=status,
            promotion_state="pending" if status == "completed" else None,
        )
        updated = self._job_store.get(job_id)
        assert updated is not None
        return updated

    def _project_pending_escalation(
        self, collaboration_id: str
    ) -> PendingEscalationView | None:
        requests = self._pending_request_store.list_by_collaboration_id(collaboration_id)
        if not requests:
            return None
        request = requests[-1]
        return PendingEscalationView(
            request_id=request.request_id,
            kind=request.kind,
            requested_scope=request.requested_scope,
            available_decisions=request.available_decisions,
        )

    def _load_or_materialize_inspection(
        self, job: DelegationJob
    ) -> ArtifactInspectionSnapshot | None:
        if job.status not in ("completed", "failed", "unknown"):
            return None
        existing = self._artifact_store.load_snapshot(job=job)
        if existing is not None:
            if (
                job.artifact_paths != existing.artifact_paths
                or job.artifact_hash != existing.artifact_hash
            ):
                self._job_store.update_artifacts(
                    job.job_id,
                    artifact_paths=existing.artifact_paths,
                    artifact_hash=existing.artifact_hash,
                )
            return existing
        snapshot = self._artifact_store.materialize_snapshot(job=job)
        self._job_store.update_artifacts(
            job.job_id,
            artifact_paths=snapshot.artifact_paths,
            artifact_hash=snapshot.artifact_hash,
        )
        refreshed = self._job_store.get(job.job_id)
        assert refreshed is not None
        return snapshot

    def poll(self, *, job_id: str) -> DelegationPollResult | PollRejectedResponse:
        job = self._job_store.get(job_id)
        if job is None:
            return PollRejectedResponse(
                rejected=True,
                reason="job_not_found",
                detail=f"Delegation poll failed: job not found. Got: {job_id!r:.100}",
                job_id=job_id,
            )

        inspection = self._load_or_materialize_inspection(job)
        refreshed = self._job_store.get(job_id) or job
        pending_escalation = None
        if refreshed.status == "needs_escalation":
            pending_escalation = self._project_pending_escalation(refreshed.collaboration_id)

        detail = None
        if refreshed.status == "failed":
            detail = "Delegation execution failed. Inspect artifacts before retrying or discarding."
        elif refreshed.status == "unknown":
            detail = "Delegation outcome could not be confirmed after recovery. Inspect artifacts, then restart or discard."

        return DelegationPollResult(
            job=refreshed,
            pending_escalation=pending_escalation,
            inspection=inspection,
            detail=detail,
        )
```

Replace every controller status write that currently assumes seeded `"pending"` with `_persist_job_transition(...)`:

```python
job = DelegationJob(
    job_id=job_id,
    runtime_id=runtime_id,
    collaboration_id=collaboration_id,
    base_commit=resolved_base,
    worktree_path=str(worktree_path),
    promotion_state=None,
    status="queued",
)

# later
updated_job = self._persist_job_transition(job_id, final_status)
```

Use the helper in:

1. `_finalize_turn_result()` for completed / needs_escalation / failed / unknown
2. `decide()` deny path (`failed`)
3. `recover_startup()` orphan reconciliation (`unknown`)

In `packages/plugins/codex-collaboration/scripts/codex_runtime_bootstrap.py`, construct and inject the new helper:

```python
from server.artifact_store import ArtifactStore


def factory() -> DelegationController:
    session_id = _read_session_id(plugin_data_path)
    job_store = DelegationJobStore(plugin_data_path, session_id)
    lineage_store = LineageStore(plugin_data_path, session_id)
    pending_request_store = PendingRequestStore(plugin_data_path, session_id)
    artifact_store = ArtifactStore(
        plugin_data_path,
        timestamp_factory=journal.timestamp,
    )
    return DelegationController(
        control_plane=control_plane,
        worktree_manager=WorktreeManager(),
        job_store=job_store,
        lineage_store=lineage_store,
        runtime_registry=runtime_registry,
        journal=journal,
        session_id=session_id,
        plugin_data_path=plugin_data_path,
        pending_request_store=pending_request_store,
        artifact_store=artifact_store,
    )
```

- [ ] **Step 4: Re-run the controller tests**

Run:

```bash
uv run pytest packages/plugins/codex-collaboration/tests/test_delegation_controller.py -q
```

Expected:

- PASS

- [ ] **Step 5: Commit the controller slice**

Run:

```bash
git add \
  packages/plugins/codex-collaboration/server/delegation_controller.py \
  packages/plugins/codex-collaboration/scripts/codex_runtime_bootstrap.py \
  packages/plugins/codex-collaboration/tests/test_delegation_controller.py
git commit -m "feat(t20260330-06): implement delegation poll controller flow"
```

Expected:

- one commit containing controller behavior and factory wiring

---

### Task 4: Wire The MCP Tool, Safety Policy, And End-To-End Coverage

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/mcp_server.py`
- Modify: `packages/plugins/codex-collaboration/server/consultation_safety.py`
- Test: `packages/plugins/codex-collaboration/tests/test_mcp_server.py`
- Test: `packages/plugins/codex-collaboration/tests/test_consultation_safety.py`
- Test: `packages/plugins/codex-collaboration/tests/test_codex_guard.py`
- Test: `packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py`

- [ ] **Step 1: Write the failing MCP, safety, and end-to-end tests**

Add to `packages/plugins/codex-collaboration/tests/test_mcp_server.py`:

```python
class FakeDelegationControllerWithPoll:
    def __init__(self) -> None:
        self.last_poll_job_id: str | None = None

    def recover_startup(self) -> None:
        return None

    def poll(self, *, job_id: str) -> object:
        from server.models import DelegationJob, DelegationPollResult

        self.last_poll_job_id = job_id
        return DelegationPollResult(
            job=DelegationJob(
                job_id=job_id,
                runtime_id="rt-1",
                collaboration_id="collab-1",
                base_commit="abc123",
                worktree_path="/tmp/wk",
                promotion_state="pending",
                status="completed",
            ),
            detail="Completed and ready for review.",
        )


def test_delegate_poll_tool_registered() -> None:
    tool_names = {t["name"] for t in TOOL_DEFINITIONS}
    assert "codex.delegate.poll" in tool_names


def test_handle_tools_call_delegate_poll() -> None:
    controller = FakeDelegationControllerWithPoll()
    server = McpServer(
        control_plane=FakeControlPlane(),
        delegation_controller=controller,
    )
    server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "test"},
            },
        }
    )

    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.poll",
                "arguments": {"job_id": "job-1"},
            },
        }
    )

    payload = json.loads(response["result"]["content"][0]["text"])
    assert payload["job"]["job_id"] == "job-1"
    assert controller.last_poll_job_id == "job-1"
```

Add to `packages/plugins/codex-collaboration/tests/test_consultation_safety.py`:

```python
def test_delegate_poll_returns_poll_policy() -> None:
    assert (
        policy_for_tool(
            "mcp__plugin_codex-collaboration_codex-collaboration__codex.delegate.poll"
        )
        == DELEGATE_POLL_POLICY
    )
```

Add to `packages/plugins/codex-collaboration/tests/test_codex_guard.py`:

```python
def test_delegate_poll_clean(self) -> None:
    result = self._run_guard(
        "mcp__plugin_codex-collaboration_codex-collaboration__codex.delegate.poll",
        {"job_id": "job-1"},
    )
    assert result == {"decision": "approve"}
```

Add to `packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py`:

```python
def test_delegate_poll_completed_job_materializes_snapshot_through_mcp(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    _init_repo(repo_root)

    server, job_store, _prs, _journal, _plugin_data = _build_e2e_setup(
        tmp_path,
        session_factory=lambda: _ConfigurableStubSession(),
    )

    start_response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.start",
                "arguments": {"repo_root": str(repo_root), "objective": "Fix the bug"},
            },
        }
    )
    start_payload = json.loads(start_response["result"]["content"][0]["text"])
    assert start_payload["status"] == "completed"

    poll_response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.poll",
                "arguments": {"job_id": start_payload["job_id"]},
            },
        }
    )
    poll_payload = json.loads(poll_response["result"]["content"][0]["text"])

    assert poll_payload["job"]["promotion_state"] == "pending"
    assert poll_payload["inspection"]["artifact_hash"] is not None
    assert len(poll_payload["inspection"]["artifact_paths"]) == 3


def test_delegate_poll_needs_escalation_returns_projected_request(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _init_repo(repo_root)

    server, _job_store, _prs, _journal, _plugin_data = _build_e2e_setup(
        tmp_path,
        session_factory=lambda: _ConfigurableStubSession(
            server_requests=[_command_approval_request_msg()],
        ),
    )

    start_response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.start",
                "arguments": {"repo_root": str(repo_root), "objective": "Fix the bug"},
            },
        }
    )
    start_payload = json.loads(start_response["result"]["content"][0]["text"])
    assert start_payload["job"]["status"] == "needs_escalation"

    poll_response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "codex.delegate.poll",
                "arguments": {"job_id": start_payload["job"]["job_id"]},
            },
        }
    )
    poll_payload = json.loads(poll_response["result"]["content"][0]["text"])

    assert poll_payload["pending_escalation"]["request_id"] == "42"
    assert "codex_thread_id" not in poll_payload["pending_escalation"]
```

- [ ] **Step 2: Run the targeted tool/safety/integration tests to verify they fail**

Run:

```bash
uv run pytest \
  packages/plugins/codex-collaboration/tests/test_mcp_server.py \
  packages/plugins/codex-collaboration/tests/test_consultation_safety.py \
  packages/plugins/codex-collaboration/tests/test_codex_guard.py \
  packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py \
  -q
```

Expected:

- FAIL because `codex.delegate.poll` is not registered or dispatched
- FAIL because `consultation_safety.py` does not know the new tool name
- FAIL because the integration path cannot call `codex.delegate.poll`

- [ ] **Step 3: Implement MCP registration, safety policy, and dispatch**

In `packages/plugins/codex-collaboration/server/mcp_server.py`, register the new tool and dispatch it through the controller:

```python
TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "codex.delegate.poll",
        "description": "Read delegation job state and materialize review artifacts when needed.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string"},
            },
            "required": ["job_id"],
        },
    },
    # keep the existing tool definitions below or above in the current order
]

if name == "codex.delegate.poll":
    controller = self._ensure_delegation_controller()
    return asdict(controller.poll(job_id=arguments["job_id"]))
```

In `packages/plugins/codex-collaboration/server/consultation_safety.py`, add a total policy entry for the new tool:

```python
DELEGATE_POLL_POLICY = ToolScanPolicy(
    expected_fields=frozenset({"job_id"}),
    content_fields=frozenset(),
)

_TOOL_POLICY_MAP: dict[str, ToolScanPolicy] = {
    "mcp__plugin_codex-collaboration_codex-collaboration__codex.delegate.poll": DELEGATE_POLL_POLICY,
    # keep existing entries here
}
```

Do not add `job_id` to `content_fields`; it is an identifier, not free-form user content.

This task adds policy coverage for `codex.delegate.poll` only. The pre-existing absence of a `codex.delegate.start` policy entry remains a separate hardening item and is not expanded here.

- [ ] **Step 4: Re-run the targeted tests**

Run:

```bash
uv run pytest \
  packages/plugins/codex-collaboration/tests/test_mcp_server.py \
  packages/plugins/codex-collaboration/tests/test_consultation_safety.py \
  packages/plugins/codex-collaboration/tests/test_codex_guard.py \
  packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py \
  -q
```

Expected:

- PASS

- [ ] **Step 5: Run the broad delegation package suite**

Run:

```bash
uv run pytest packages/plugins/codex-collaboration/tests -q
ruff check packages/plugins/codex-collaboration/server packages/plugins/codex-collaboration/tests
```

Expected:

- full package test suite PASS
- `ruff check` PASS

- [ ] **Step 6: Commit the outward-facing poll surface**

Run:

```bash
git add \
  packages/plugins/codex-collaboration/server/mcp_server.py \
  packages/plugins/codex-collaboration/server/consultation_safety.py \
  packages/plugins/codex-collaboration/tests/test_mcp_server.py \
  packages/plugins/codex-collaboration/tests/test_consultation_safety.py \
  packages/plugins/codex-collaboration/tests/test_codex_guard.py \
  packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py
git commit -m "feat(t20260330-06): wire codex delegate poll mcp surface"
```

Expected:

- one commit containing tool registration, hook-guard wiring, and end-to-end coverage

---

## Final Verification

- [ ] `uv run pytest packages/plugins/codex-collaboration/tests/test_models_r2.py -q`
- [ ] `uv run pytest packages/plugins/codex-collaboration/tests/test_delegation_job_store.py -q`
- [ ] `uv run pytest packages/plugins/codex-collaboration/tests/test_artifact_store.py -q`
- [ ] `uv run pytest packages/plugins/codex-collaboration/tests/test_execution_prompt_builder.py -q`
- [ ] `uv run pytest packages/plugins/codex-collaboration/tests/test_delegation_controller.py -q`
- [ ] `uv run pytest packages/plugins/codex-collaboration/tests/test_mcp_server.py -q`
- [ ] `uv run pytest packages/plugins/codex-collaboration/tests/test_consultation_safety.py -q`
- [ ] `uv run pytest packages/plugins/codex-collaboration/tests/test_codex_guard.py -q`
- [ ] `uv run pytest packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py -q`
- [ ] `uv run pytest packages/plugins/codex-collaboration/tests -q`
- [ ] `ruff check packages/plugins/codex-collaboration/server packages/plugins/codex-collaboration/tests`

## Self-Review

### 1. Spec Coverage

- `codex.delegate.poll` typed MCP surface: covered by Tasks 1, 3, and 4.
- Nullable/backcompat-aware `promotion_state`: covered by Tasks 1 and 3.
- Canonical review-set materialization and hash recipe: covered by Task 2.
- Inspection-only snapshots for `failed` / `unknown`: covered by Tasks 2 and 3.
- Pending escalation projection without raw internal IDs: covered by Tasks 1, 3, and 4.
- Deliberate non-goals preserved:
  - no `promote`
  - no `discard`
  - no start/decide serializer cleanup

Gaps found: none.

### 2. Placeholder Scan

- Searched for placeholder-style red-flag phrases and found none in the executable tasks.
- Replaced the only ambiguous area (`test-results record`) with an explicit deterministic file path and stub format.
- No placeholders remain.

### 3. Type Consistency

- `DelegationJob.promotion_state` is consistently `PromotionState | None`.
- `PendingEscalationView`, `ArtifactInspectionSnapshot`, `DelegationPollResult`, and `PollRejectedResponse` are introduced in Task 1 and reused under the same names in later tasks.
- `ArtifactStore.materialize_snapshot()` and `ArtifactStore.load_snapshot()` are the only materialization/reload entry points referenced later.
- `DelegationController.poll()` is the only controller method name used for the new surface.
