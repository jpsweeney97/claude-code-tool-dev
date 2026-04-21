# Codex Delegate Promote / Discard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `codex.delegate.promote` and `codex.delegate.discard` with apply-only promotion, reviewed-artifact integrity checks, promotion journal replay, and post-promotion advisory stale-context signaling.

**Architecture:** Keep the implementation inside the existing execution-domain modules. `ArtifactStore` owns canonical artifact generation for the execution worktree. `DelegationController` owns promotion/discard lifecycle, primary-workspace verification, rollback, and promotion replay. `ControlPlane` owns advisory-runtime stale-marker policy through a callback invoked only after promotion reaches `verified`. MCP and safety wiring stay in `mcp_server.py` and `consultation_safety.py`.

**Tech Stack:** Python 3.12+, pytest, append-only JSONL stores, git subprocess calls, MCP JSON-RPC tool dispatch.

**References (read-only — do not modify during implementation):**
- `docs/superpowers/specs/codex-collaboration/contracts.md`
- `docs/superpowers/specs/codex-collaboration/promotion-protocol.md`
- `docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md`
- `docs/superpowers/specs/codex-collaboration/recovery-and-journal.md`

---

## File Structure

### Production files

| Path | Responsibility |
|---|---|
| `packages/plugins/codex-collaboration/server/models.py` | Add promote/discard result + rejection types, `promotion_attempt`, and the new stale-marker shape. |
| `packages/plugins/codex-collaboration/server/delegation_job_store.py` | Persist and replay `promotion_attempt`; add a promotion-state-only update helper. |
| `packages/plugins/codex-collaboration/server/journal.py` | Accept `promotion` journal operations and the updated stale-marker payload. |
| `packages/plugins/codex-collaboration/server/artifact_store.py` | Factor canonical execution-worktree artifact generation into a reusable bundle. |
| `packages/plugins/codex-collaboration/server/delegation_controller.py` | Implement `promote()`, `discard()`, promotion replay, primary-workspace verification, rollback, and the advisory-stale callback seam. |
| `packages/plugins/codex-collaboration/server/control_plane.py` | Rename the stale-marker consumer from `promoted_head` to `promoted_artifact_hash` + `job_id`, update the consult-time stale summary, and expose the callback that writes stale advisory context only when an advisory runtime exists. |
| `packages/plugins/codex-collaboration/server/mcp_server.py` | Register, validate, and dispatch `codex.delegate.promote` and `codex.delegate.discard`. |
| `packages/plugins/codex-collaboration/server/consultation_safety.py` | Add PreToolUse policies for the new tools. |

### Test files

| Path | Coverage |
|---|---|
| `packages/plugins/codex-collaboration/tests/test_models_r2.py` | New dataclasses and stale-marker shape. |
| `packages/plugins/codex-collaboration/tests/test_delegation_job_store.py` | `promotion_attempt` replay and promotion-state-only updates. |
| `packages/plugins/codex-collaboration/tests/test_journal.py` | `promotion` operation validation and the breaking stale-marker field rename from `promoted_head` to `promoted_artifact_hash` + `job_id`. |
| `packages/plugins/codex-collaboration/tests/test_artifact_store.py` | `CanonicalArtifactBundle` generation and promote-time recomputation parity. |
| `packages/plugins/codex-collaboration/tests/test_delegation_controller.py` | Promote/discard success paths, typed rejections, replay, verification, and rollback. |
| `packages/plugins/codex-collaboration/tests/test_control_plane.py` | Advisory stale-marker callback behavior, breaking stale-summary rename, and next-turn injection. |
| `packages/plugins/codex-collaboration/tests/test_mcp_server.py` | Tool registration, input validation, and serialization for promote/discard. |
| `packages/plugins/codex-collaboration/tests/test_consultation_safety.py` | Policy routing for promote/discard. |
| `packages/plugins/codex-collaboration/tests/test_codex_guard.py` | Hook behavior for clean and secret-bearing promote/discard inputs. |

---

## Pre-Flight

- [ ] **Step P0: Preserve the spec-amendment boundary before runtime edits**

Run:
```bash
git switch -c feature/t06-promote-discard
git add \
  docs/superpowers/specs/codex-collaboration/contracts.md \
  docs/superpowers/specs/codex-collaboration/promotion-protocol.md \
  docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md \
  docs/superpowers/specs/codex-collaboration/recovery-and-journal.md \
  docs/superpowers/plans/2026-04-20-codex-delegate-promote-discard.md
git commit -m "docs: reconcile promote discard contract and plan"
```

Expected:
- the spec amendments are captured as a docs-only first commit on the feature branch
- runtime implementation starts from that committed contract, not from unstaged edits on `main`

- [ ] **Step P1: Re-anchor on live branch state**

Run:
```bash
git branch --show-current
git rev-parse --short HEAD
git status --short --branch
```

Expected:
- branch is the intended implementation branch
- `HEAD` is the reviewed promote/discard baseline
- unrelated local drift is understood before editing

- [ ] **Step P2: Confirm the current delegation baseline is green**

Run:
```bash
uv run pytest \
  packages/plugins/codex-collaboration/tests/test_artifact_store.py \
  packages/plugins/codex-collaboration/tests/test_delegation_controller.py \
  packages/plugins/codex-collaboration/tests/test_mcp_server.py \
  packages/plugins/codex-collaboration/tests/test_control_plane.py -q
```

Expected: PASS before layering promote/discard changes on top.

---

### Task 1: Models, Job Store, And Journal Vocabulary

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/models.py`
- Modify: `packages/plugins/codex-collaboration/server/delegation_job_store.py`
- Modify: `packages/plugins/codex-collaboration/server/journal.py`
- Modify: `packages/plugins/codex-collaboration/server/control_plane.py`
- Test: `packages/plugins/codex-collaboration/tests/test_models_r2.py`
- Test: `packages/plugins/codex-collaboration/tests/test_delegation_job_store.py`
- Test: `packages/plugins/codex-collaboration/tests/test_journal.py`
- Test: `packages/plugins/codex-collaboration/tests/test_control_plane.py`

- [ ] **Step 1: Write the failing tests**

Append tests equivalent to:

```python
def test_delegation_job_persists_promotion_attempt() -> None:
    from server.models import DelegationJob

    job = DelegationJob(
        job_id="job-1",
        runtime_id="rt-1",
        collaboration_id="collab-1",
        base_commit="abc123",
        worktree_path="/tmp/wk",
        promotion_state="pending",
        promotion_attempt=0,
        status="completed",
    )
    assert job.promotion_attempt == 0


def test_promotion_result_shape() -> None:
    from server.models import DelegationJob, PromotionResult

    job = DelegationJob(
        job_id="job-1",
        runtime_id="rt-1",
        collaboration_id="collab-1",
        base_commit="abc123",
        worktree_path="/tmp/wk",
        promotion_state="verified",
        promotion_attempt=1,
        status="completed",
    )
    result = PromotionResult(
        job=job,
        artifact_hash="hash-1",
        changed_files=("README.md",),
        stale_advisory_context=True,
    )
    assert result.stale_advisory_context is True


def test_journal_accepts_promotion_operation(tmp_path: Path) -> None:
    journal = OperationJournal(tmp_path / "plugin-data")
    journal.write_phase(
        OperationJournalEntry(
            idempotency_key="job-1:1",
            operation="promotion",
            phase="intent",
            collaboration_id="collab-1",
            created_at="2026-04-20T00:00:00Z",
            repo_root="/repo",
            job_id="job-1",
        ),
        session_id="sess-1",
    )
    unresolved = journal.list_unresolved(session_id="sess-1")
    assert unresolved[0].operation == "promotion"


def test_stale_marker_shape_uses_artifact_hash_and_job_id(tmp_path: Path) -> None:
    journal = OperationJournal(tmp_path / "plugin-data")
    journal.write_stale_marker(
        StaleAdvisoryContextMarker(
            repo_root=str(tmp_path.resolve()),
            promoted_artifact_hash="hash-1",
            job_id="job-1",
            recorded_at="2026-04-20T00:00:00Z",
        )
    )
    marker = journal.load_stale_marker(tmp_path)
    assert marker is not None
    assert marker.promoted_artifact_hash == "hash-1"
    assert marker.job_id == "job-1"
```

- [ ] **Step 2: Run the focused tests and confirm they fail**

Run:
```bash
uv run pytest \
  packages/plugins/codex-collaboration/tests/test_models_r2.py \
  packages/plugins/codex-collaboration/tests/test_delegation_job_store.py \
  packages/plugins/codex-collaboration/tests/test_journal.py -q
```

Expected: FAIL on missing types/fields and unknown `promotion` journal operation.

- [ ] **Step 3: Implement the model/store/journal changes**

Apply the following shape:

```python
# models.py
PromotionRejectedReason = Literal[
    "head_mismatch",
    "index_dirty",
    "worktree_dirty",
    "artifact_hash_mismatch",
    "job_not_completed",
    "job_not_reviewed",
]
DiscardRejectedReason = Literal["job_not_found", "job_not_discardable"]

@dataclass(frozen=True)
class StaleAdvisoryContextMarker:
    repo_root: str
    promoted_artifact_hash: str
    job_id: str
    recorded_at: str

@dataclass(frozen=True)
class PromotionResult:
    job: DelegationJob
    artifact_hash: str
    changed_files: tuple[str, ...]
    stale_advisory_context: bool

@dataclass(frozen=True)
class DiscardRejectedResponse:
    rejected: bool
    reason: DiscardRejectedReason
    detail: str
    job_id: str | None = None
```

`DelegationJob` must stay backward-compatible for existing call sites and JSONL replay:

```python
@dataclass(frozen=True)
class DelegationJob:
    ...
    promotion_state: PromotionState | None
    promotion_attempt: int = 0
    status: JobStatus = "queued"
```

`OperationJournalEntry.operation` must explicitly accept the new literal:

```python
operation: Literal[
    "thread_creation",
    "turn_dispatch",
    "job_creation",
    "approval_resolution",
    "promotion",
]
```

```python
# delegation_job_store.py
def update_promotion_state(
    self,
    job_id: str,
    *,
    promotion_state: PromotionState,
    promotion_attempt: int | None = None,
) -> None:
    self._append(
        {
            "op": "update_promotion_state",
            "job_id": job_id,
            "promotion_state": promotion_state,
            "promotion_attempt": promotion_attempt,
        }
    )
```

```python
# journal.py
_VALID_OPERATIONS = frozenset(
    ("thread_creation", "turn_dispatch", "job_creation", "approval_resolution", "promotion")
)
```

Also perform the breaking stale-marker rename across the live code and tests:
- `server/models.py`: rename `promoted_head` -> `promoted_artifact_hash`, add `job_id`
- `server/journal.py`: read/write the new fields
- `server/control_plane.py`: replace `"Most recent promoted HEAD"` formatting with artifact-hash/job-id phrasing
- `tests/test_journal.py` and `tests/test_control_plane.py`: update all existing stale-marker fixtures and assertions to the new shape

- [ ] **Step 4: Re-run the focused tests**

Run the Step 2 command again.

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add \
  packages/plugins/codex-collaboration/server/models.py \
  packages/plugins/codex-collaboration/server/delegation_job_store.py \
  packages/plugins/codex-collaboration/server/journal.py \
  packages/plugins/codex-collaboration/server/control_plane.py \
  packages/plugins/codex-collaboration/tests/test_models_r2.py \
  packages/plugins/codex-collaboration/tests/test_delegation_job_store.py \
  packages/plugins/codex-collaboration/tests/test_journal.py \
  packages/plugins/codex-collaboration/tests/test_control_plane.py
git commit -m "feat: add promote discard model and journal primitives"
```

### Task 2: Factor Canonical Execution-Worktree Artifacts

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/artifact_store.py`
- Test: `packages/plugins/codex-collaboration/tests/test_artifact_store.py`

- [ ] **Step 1: Write the failing artifact-store tests**

Append tests equivalent to:

```python
def test_generate_canonical_artifacts_returns_bundle_with_hash(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path / "plugin-data", timestamp_factory=lambda: "2026-04-20T00:00:00Z")
    repo = tmp_path / "repo"
    repo.mkdir()
    base_commit = _init_repo(repo)
    (repo / "README.md").write_text("# Changed\n", encoding="utf-8")

    bundle = store.generate_canonical_artifacts(
        job=_make_job(worktree_path=str(repo), base_commit=base_commit),
        output_dir=tmp_path / "bundle",
    )

    assert bundle.artifact_hash is not None
    assert bundle.changed_files == ("README.md",)
    assert bundle.full_diff_path.name == "full.diff"
```

- [ ] **Step 2: Run the artifact-store tests and confirm they fail**

Run:
```bash
uv run pytest packages/plugins/codex-collaboration/tests/test_artifact_store.py -q
```

Expected: FAIL on missing `generate_canonical_artifacts()` / `CanonicalArtifactBundle`.

- [ ] **Step 3: Implement the artifact-store refactor**

Use this structure:

```python
@dataclass(frozen=True)
class CanonicalArtifactBundle:
    artifact_paths: tuple[str, ...]
    artifact_hash: str | None
    changed_files: tuple[str, ...]
    full_diff_path: Path
    changed_files_path: Path
    test_results_path: Path


def generate_canonical_artifacts(
    self,
    *,
    job: DelegationJob,
    output_dir: Path,
) -> CanonicalArtifactBundle:
    output_dir.mkdir(parents=True, exist_ok=True)
    changed_files = self._changed_files(job)
    full_diff_path = output_dir / "full.diff"
    changed_files_path = output_dir / "changed-files.json"
    test_results_path = output_dir / "test-results.json"
    ...
```

Then make `materialize_snapshot()` call `generate_canonical_artifacts()` instead of duplicating that logic.

- [ ] **Step 4: Re-run the artifact-store tests**

Run the Step 2 command again.

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add \
  packages/plugins/codex-collaboration/server/artifact_store.py \
  packages/plugins/codex-collaboration/tests/test_artifact_store.py
git commit -m "refactor: factor canonical artifact generation for promote"
```

### Task 3: Implement Promote / Discard In DelegationController

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/delegation_controller.py`
- Test: `packages/plugins/codex-collaboration/tests/test_delegation_controller.py`

- [ ] **Step 1: Write the failing controller tests**

Append tests covering:

```python
def test_promote_rejects_dirty_primary_workspace(tmp_path: Path) -> None: ...
def test_promote_rejects_job_without_reviewed_hash(tmp_path: Path) -> None: ...
def test_promote_applies_reviewed_diff_and_sets_verified(tmp_path: Path) -> None: ...
def test_promote_rolls_back_when_primary_workspace_verification_fails(tmp_path: Path) -> None: ...
def test_promote_rollback_removes_new_files_created_by_reviewed_diff(tmp_path: Path) -> None: ...
def test_discard_accepts_pending_job(tmp_path: Path) -> None: ...
def test_discard_rejects_applied_job(tmp_path: Path) -> None: ...
def test_recover_startup_replays_promotion_dispatched_state(tmp_path: Path) -> None: ...
```

- [ ] **Step 2: Run the controller tests and confirm they fail**

Run:
```bash
uv run pytest packages/plugins/codex-collaboration/tests/test_delegation_controller.py -q
```

Expected: FAIL on missing controller methods and replay logic.

- [ ] **Step 3: Implement `promote()`, `discard()`, and promotion replay**

Add these seams:

```python
class _PromotionCallbackLike(Protocol):
    def on_promotion_verified(
        self,
        *,
        repo_root: Path,
        artifact_hash: str,
        job_id: str,
    ) -> bool: ...


def promote(self, *, job_id: str) -> PromotionResult | PromotionRejectedResponse: ...
def discard(self, *, job_id: str) -> DiscardResult | DiscardRejectedResponse: ...
```

Required behavior:
- increment `promotion_attempt` before writing `promotion:intent`
- prechecks enforce clean `git status --porcelain`, clean index, `HEAD == base_commit`, `status == "completed"`, reviewed hash present, regenerated worktree hash match
- apply the reviewed persisted `full.diff` with `git apply --binary`
- verify primary workspace by byte-comparing diff and changed-file set
- before apply, compute the set of reviewed paths that are not tracked in the primary workspace; on verification failure, use that set to remove new files produced by the diff after `git checkout -- .`
- on verification failure: transition through `rollback_needed` and `rolled_back`
- after `verified`: invoke the callback and return its boolean as `stale_advisory_context`
- allow discard only from `pending` and `prechecks_failed`
- extend `recover_startup()` to reconcile `promotion` journal records using journal authority for mutation
- leave `prechecks_failed` without a promotion journal record untouched during recovery; it is already a safe discardable resting state

The rollback identification rule must be explicit:

```python
reviewed_paths = set(reviewed_changed_files)
new_paths = {
    path for path in reviewed_paths
    if not _path_is_tracked(primary_repo_root, path)
}
...
subprocess.run(["git", "-C", str(primary_repo_root), "checkout", "--", "."], check=True)
for relative_path in sorted(new_paths):
    target = primary_repo_root / relative_path
    if target.exists():
        target.unlink()
```

- [ ] **Step 4: Re-run the controller tests**

Run the Step 2 command again.

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add \
  packages/plugins/codex-collaboration/server/delegation_controller.py \
  packages/plugins/codex-collaboration/tests/test_delegation_controller.py
git commit -m "feat: implement delegation promote discard lifecycle"
```

### Task 4: Advisory Stale-Context Callback

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/control_plane.py`
- Test: `packages/plugins/codex-collaboration/tests/test_control_plane.py`

- [ ] **Step 1: Write the failing control-plane tests**

Append tests equivalent to:

```python
def test_on_promotion_verified_writes_marker_only_when_runtime_exists(tmp_path: Path) -> None: ...
def test_codex_consult_injects_workspace_changed_summary_from_artifact_hash_marker(tmp_path: Path) -> None: ...
```

- [ ] **Step 2: Run the control-plane tests and confirm they fail**

Run:
```bash
uv run pytest packages/plugins/codex-collaboration/tests/test_control_plane.py -q
```

Expected: FAIL on stale-marker shape and missing callback.

- [ ] **Step 3: Implement the callback and summary update**

Use this shape:

```python
def on_promotion_verified(
    self,
    *,
    repo_root: Path,
    artifact_hash: str,
    job_id: str,
) -> bool:
    resolved_root = repo_root.resolve()
    if str(resolved_root) not in self._advisory_runtimes:
        return False
    self._journal.write_stale_marker(
        StaleAdvisoryContextMarker(
            repo_root=str(resolved_root),
            promoted_artifact_hash=artifact_hash,
            job_id=job_id,
            recorded_at=self._journal.timestamp(),
        )
    )
    return True
```

Then update the consult-time stale summary to mention the promoted artifact hash / job id plus live repo identity.

- [ ] **Step 4: Re-run the control-plane tests**

Run the Step 2 command again.

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add \
  packages/plugins/codex-collaboration/server/control_plane.py \
  packages/plugins/codex-collaboration/tests/test_control_plane.py
git commit -m "feat: mark advisory context stale after verified promote"
```

### Task 5: MCP Surface, Safety Policies, And End-To-End Verification

**Files:**
- Modify: `packages/plugins/codex-collaboration/server/mcp_server.py`
- Modify: `packages/plugins/codex-collaboration/server/consultation_safety.py`
- Test: `packages/plugins/codex-collaboration/tests/test_mcp_server.py`
- Test: `packages/plugins/codex-collaboration/tests/test_consultation_safety.py`
- Test: `packages/plugins/codex-collaboration/tests/test_codex_guard.py`

- [ ] **Step 1: Write the failing MCP / safety tests**

Append tests covering:

```python
def test_delegate_promote_tool_registered() -> None: ...
def test_delegate_discard_tool_registered() -> None: ...
def test_handle_tools_call_delegate_promote() -> None: ...
def test_handle_tools_call_delegate_discard() -> None: ...
def test_delegate_promote_returns_promote_policy() -> None: ...
def test_delegate_discard_returns_discard_policy() -> None: ...
def test_delegate_promote_guard_blocks_secret_in_job_id_payload() -> None: ...
```

- [ ] **Step 2: Run the MCP / safety tests and confirm they fail**

Run:
```bash
uv run pytest \
  packages/plugins/codex-collaboration/tests/test_mcp_server.py \
  packages/plugins/codex-collaboration/tests/test_consultation_safety.py \
  packages/plugins/codex-collaboration/tests/test_codex_guard.py -q
```

Expected: FAIL on missing tools and policy routing.

- [ ] **Step 3: Implement MCP dispatch and PreToolUse policies**

Apply this shape:

```python
# mcp_server.py TOOL_DEFINITIONS
{
    "name": "codex.delegate.promote",
    "description": "Apply reviewed delegation results to the primary workspace.",
    "inputSchema": {
        "type": "object",
        "properties": {"job_id": {"type": "string"}},
        "required": ["job_id"],
    },
},
{
    "name": "codex.delegate.discard",
    "description": "Discard unpromoted delegation results.",
    "inputSchema": {
        "type": "object",
        "properties": {"job_id": {"type": "string"}},
        "required": ["job_id"],
    },
},
```

```python
# consultation_safety.py
DELEGATE_PROMOTE_POLICY = ToolScanPolicy(
    expected_fields=frozenset({"job_id"}),
    content_fields=frozenset(),
)
DELEGATE_DISCARD_POLICY = ToolScanPolicy(
    expected_fields=frozenset({"job_id"}),
    content_fields=frozenset(),
)
```

- [ ] **Step 4: Run the targeted full slice**

Run:
```bash
uv run pytest \
  packages/plugins/codex-collaboration/tests/test_models_r2.py \
  packages/plugins/codex-collaboration/tests/test_delegation_job_store.py \
  packages/plugins/codex-collaboration/tests/test_journal.py \
  packages/plugins/codex-collaboration/tests/test_artifact_store.py \
  packages/plugins/codex-collaboration/tests/test_delegation_controller.py \
  packages/plugins/codex-collaboration/tests/test_control_plane.py \
  packages/plugins/codex-collaboration/tests/test_mcp_server.py \
  packages/plugins/codex-collaboration/tests/test_consultation_safety.py \
  packages/plugins/codex-collaboration/tests/test_codex_guard.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add \
  packages/plugins/codex-collaboration/server/mcp_server.py \
  packages/plugins/codex-collaboration/server/consultation_safety.py \
  packages/plugins/codex-collaboration/tests/test_mcp_server.py \
  packages/plugins/codex-collaboration/tests/test_consultation_safety.py \
  packages/plugins/codex-collaboration/tests/test_codex_guard.py
git commit -m "feat: expose delegate promote discard over MCP"
```

---

## Final Verification

- [ ] Run the full targeted slice from Task 5 Step 4.
- [ ] Run `ruff check packages/plugins/codex-collaboration/server packages/plugins/codex-collaboration/tests`.
- [ ] Run `ruff format --check packages/plugins/codex-collaboration/server packages/plugins/codex-collaboration/tests`.
- [ ] Verify no spec drift remains by re-reading:
  - `docs/superpowers/specs/codex-collaboration/contracts.md`
  - `docs/superpowers/specs/codex-collaboration/promotion-protocol.md`
  - `docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md`
  - `docs/superpowers/specs/codex-collaboration/recovery-and-journal.md`

## Self-Review

- Spec coverage: promote prechecks, apply-only verification, rollback, discard legality, stale callback, and journal replay each have a dedicated task.
- Placeholder scan: no `TBD`, `TODO`, or deferred implementation gaps remain in this plan.
- Type consistency: `promotion_attempt`, `PromotionResult`, `DiscardResult`, and `StaleAdvisoryContextMarker` use one naming scheme across tasks.
