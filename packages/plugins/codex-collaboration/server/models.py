"""Core models for Runtime Milestone R1."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from .runtime import AppServerRuntimeSession


CapabilityProfile = Literal["advisory", "execution"]
AuthStatus = Literal["authenticated", "expired", "missing"]
HandleStatus = Literal["active", "completed", "crashed", "unknown"]
PendingRequestKind = Literal[
    "command_approval", "file_change", "request_user_input", "unknown"
]
TurnStatus = Literal["completed", "interrupted", "failed"]
PendingRequestStatus = Literal["pending", "resolved", "canceled"]
JobStatus = Literal[
    "queued", "running", "needs_escalation", "completed", "failed", "unknown"
]
PromotionState = Literal[
    "pending",
    "prechecks_passed",
    "applied",
    "verified",
    "prechecks_failed",
    "rollback_needed",
    "rolled_back",
    "discarded",
]
DecisionAction = Literal["approve", "deny"]
ConsultWorkflow = Literal["consult", "review"]
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
]
PollRejectedReason = Literal["job_not_found"]
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
class RepoIdentity:
    """Repository identity included in assembled packets."""

    repo_root: Path
    branch: str
    head: str


@dataclass(frozen=True)
class FileReference:
    """File path requested for packet assembly."""

    path: Path


@dataclass(frozen=True)
class ConsultRequest:
    """Caller-facing consult request for the advisory runtime."""

    repo_root: Path
    objective: str
    user_constraints: tuple[str, ...] = ()
    acceptance_criteria: tuple[str, ...] = ()
    explicit_paths: tuple[Path, ...] = ()
    explicit_snippets: tuple[str, ...] = ()
    task_local_paths: tuple[Path, ...] = ()
    broad_repository_summaries: tuple[str, ...] = ()
    promoted_summaries: tuple[str, ...] = ()
    delegation_summaries: tuple[str, ...] = ()
    supplementary_context: tuple[str, ...] = ()
    external_research_material: tuple[str, ...] = ()
    parent_thread_id: str | None = None
    network_access: bool = False
    profile: str | None = None
    workflow: ConsultWorkflow = "consult"


@dataclass(frozen=True)
class AssembledPacket:
    """Final packet sent to Codex after assembly, redaction, and trimming."""

    profile: CapabilityProfile
    payload: str
    context_size: int
    omitted_categories: tuple[str, ...] = ()


@dataclass(frozen=True)
class ConsultEvidence:
    """Single evidence item projected from the consult result."""

    claim: str
    citation: str


@dataclass(frozen=True)
class ConsultResult:
    """Structured result returned to Claude from `codex.consult`."""

    collaboration_id: str
    runtime_id: str
    position: str
    evidence: tuple[ConsultEvidence, ...]
    uncertainties: tuple[str, ...]
    follow_up_branches: tuple[str, ...]
    context_size: int


@dataclass(frozen=True)
class RuntimeHandshake:
    """Initialize response values retained by the runtime."""

    codex_home: str
    platform_family: str
    platform_os: str
    user_agent: str


@dataclass(frozen=True)
class AccountState:
    """Auth state projected from `account/read`."""

    auth_status: AuthStatus
    account_type: str | None
    requires_openai_auth: bool


@dataclass(frozen=True)
class TurnExecutionResult:
    """Projected result of a single `turn/start` execution."""

    turn_id: str
    status: TurnStatus
    agent_message: str
    notifications: tuple[dict[str, Any], ...] = ()


@dataclass
class AdvisoryRuntimeState:
    """Live advisory runtime cached by the control plane."""

    runtime_id: str
    repo_root: Path
    policy_fingerprint: str
    handshake: RuntimeHandshake
    account_state: AccountState
    available_methods: frozenset[str]
    required_methods: frozenset[str]
    optional_methods: frozenset[str]
    session: AppServerRuntimeSession
    started_at: float
    thread_count: int = 0
    app_server_version: str | None = None


@dataclass(frozen=True)
class StaleAdvisoryContextMarker:
    """Persisted stale advisory context marker."""

    repo_root: str
    promoted_artifact_hash: str
    job_id: str
    recorded_at: str


@dataclass(frozen=True)
class AuditEvent:
    """Audit event record. See contracts.md §AuditEvent."""

    event_id: str
    timestamp: str
    actor: Literal["claude", "codex", "user", "system"]
    action: str
    collaboration_id: str
    runtime_id: str
    context_size: int | None = None
    policy_fingerprint: str | None = None
    turn_id: str | None = None
    job_id: str | None = None
    request_id: str | None = None
    decision: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OutcomeRecord:
    """Analytics outcome record for consult and dialogue success paths.

    Separate from AuditEvent (trust-boundary record). Persisted to
    analytics/outcomes.jsonl via OperationJournal.append_outcome().
    """

    outcome_id: str
    timestamp: str
    outcome_type: Literal["consult", "dialogue_turn"]
    collaboration_id: str
    runtime_id: str
    context_size: int | None
    turn_id: str
    turn_sequence: int | None = None
    policy_fingerprint: str | None = None
    repo_root: str | None = None
    workflow: ConsultWorkflow = "consult"


@dataclass(frozen=True)
class CollaborationHandle:
    """Lineage-persisted handle for dialogue or delegation.

    Consultation handles are ephemeral (not lineage-persisted).
    See contracts.md §CollaborationHandle.
    """

    collaboration_id: str
    capability_class: CapabilityProfile
    runtime_id: str
    codex_thread_id: str
    claude_session_id: str
    repo_root: str
    created_at: str
    status: HandleStatus
    parent_collaboration_id: str | None = None
    fork_reason: str | None = None
    resolved_posture: str | None = None
    resolved_effort: str | None = None
    resolved_turn_budget: int | None = None


@dataclass(frozen=True)
class PendingServerRequest:
    """Plugin-owned record for an execution or advisory server request.

    The execution approval-routing layer preserves request-relevant payloads
    opaquely in ``requested_scope``. Normalized request-scope comparison is a
    later T-05 concern and is intentionally not implemented here.
    """

    request_id: str
    runtime_id: str
    collaboration_id: str
    codex_thread_id: str
    codex_turn_id: str
    item_id: str
    kind: PendingRequestKind
    requested_scope: dict[str, Any]
    available_decisions: tuple[str, ...] = ()
    status: PendingRequestStatus = "pending"


@dataclass(frozen=True)
class DialogueStartResult:
    """Response shape for codex.dialogue.start. See contracts.md §Dialogue Start."""

    collaboration_id: str
    runtime_id: str
    status: HandleStatus
    created_at: str


@dataclass(frozen=True)
class DialogueTurnSummary:
    """Single turn entry within a DialogueReadResult."""

    turn_sequence: int
    position: str
    context_size: int
    timestamp: str


@dataclass(frozen=True)
class DialogueReplyResult:
    """Response shape for codex.dialogue.reply. See contracts.md §Dialogue Reply."""

    collaboration_id: str
    runtime_id: str
    position: str
    evidence: tuple[ConsultEvidence, ...]
    uncertainties: tuple[str, ...]
    follow_up_branches: tuple[str, ...]
    turn_sequence: int
    context_size: int


@dataclass(frozen=True)
class DialogueReadResult:
    """Response shape for codex.dialogue.read. See contracts.md §Dialogue Read."""

    collaboration_id: str
    status: HandleStatus
    turn_count: int
    created_at: str
    turns: tuple[DialogueTurnSummary, ...]


@dataclass(frozen=True)
class OperationJournalEntry:
    """Phased operation record for deterministic crash recovery replay.

    Lifecycle: intent (before dispatch) → dispatched (after dispatch, with
    outcome correlation data) → completed (confirmed, eligible for compaction).
    See recovery-and-journal.md §Write Ordering.
    """

    idempotency_key: str
    operation: Literal[
        "thread_creation",
        "turn_dispatch",
        "job_creation",
        "approval_resolution",
        "promotion",
    ]
    phase: Literal["intent", "dispatched", "completed"]
    collaboration_id: str
    created_at: str
    repo_root: str
    # Outcome correlation — set when logically knowable
    codex_thread_id: str | None = None
    turn_sequence: int | None = None  # turn_dispatch only
    runtime_id: str | None = None  # turn_dispatch and job_creation
    context_size: int | None = None  # turn_dispatch only, set at intent
    job_id: str | None = None  # job_creation and approval_resolution
    request_id: str | None = None  # approval_resolution only
    decision: str | None = None  # approval_resolution only


@dataclass(frozen=True)
class DelegationJob:
    """Persisted delegation job record. See contracts.md §DelegationJob.

    Status transitions (running, completed, needs_escalation, failed, unknown)
    are managed by ``DelegationController`` and ``recover_startup()``.

    No ``created_at`` field by design — creation timestamp is captured in the
    ``job_creation`` journal entry under the same idempotency key.
    """

    job_id: str
    runtime_id: str
    collaboration_id: str
    base_commit: str
    worktree_path: str
    promotion_state: PromotionState | None
    promotion_attempt: int = 0
    status: JobStatus = "queued"
    artifact_paths: tuple[str, ...] = ()
    artifact_hash: str | None = None


@dataclass(frozen=True)
class JobBusyResponse:
    """Typed rejection returned by codex.delegate.start when a job is active.

    See contracts.md §Job Busy.
    """

    busy: bool
    active_job_id: str
    active_job_status: JobStatus
    detail: str


@dataclass(frozen=True)
class DelegationEscalation:
    """Returned when codex.delegate.start dispatched a turn that needs escalation.

    Separates persisted job lifecycle state from transient escalation state.
    ``pending_escalation`` is the caller-visible projection — internal Codex
    IDs are stripped before the response leaves the controller.
    Plugin escalation lifecycle is tracked by ``DelegationJob.status``.
    """

    job: DelegationJob
    pending_escalation: PendingEscalationView
    agent_context: str | None = None


@dataclass(frozen=True)
class DelegationDecisionResult:
    """Returned by codex.delegate.decide after approve or deny."""

    job: DelegationJob
    decision: DecisionAction
    resumed: bool
    pending_escalation: PendingEscalationView | None = None
    agent_context: str | None = None


@dataclass(frozen=True)
class DecisionRejectedResponse:
    """Typed rejection returned by codex.delegate.decide."""

    rejected: bool
    reason: DecisionRejectedReason
    detail: str
    job_id: str | None = None
    request_id: str | None = None


@dataclass(frozen=True)
class PendingEscalationView:
    """Projected view of a pending escalation for poll results.

    Minimal subset of PendingServerRequest fields needed by the caller
    to render an escalation prompt. Does not carry internal correlation
    ids (codex_thread_id, codex_turn_id, item_id).
    """

    request_id: str
    kind: PendingRequestKind
    requested_scope: dict[str, Any]
    available_decisions: tuple[str, ...] = ()


@dataclass(frozen=True)
class ArtifactInspectionSnapshot:
    """Point-in-time snapshot of inspection artifacts for poll results.

    Captures the artifact state at poll time so the caller can present
    a diff summary without re-reading the worktree.
    """

    artifact_hash: str | None
    artifact_paths: tuple[str, ...]
    changed_files: tuple[str, ...]
    reviewed_at: str


@dataclass(frozen=True)
class DelegationPollResult:
    """Successful poll result returned by codex.delegate.poll."""

    job: DelegationJob
    pending_escalation: PendingEscalationView | None = None
    inspection: ArtifactInspectionSnapshot | None = None
    detail: str | None = None


@dataclass(frozen=True)
class PollRejectedResponse:
    """Typed rejection returned by codex.delegate.poll."""

    rejected: bool
    reason: PollRejectedReason
    detail: str
    job_id: str | None = None


@dataclass(frozen=True)
class PromotionResult:
    """Successful promotion result returned by codex.delegate.promote."""

    job: "DelegationJob"
    artifact_hash: str
    changed_files: tuple[str, ...]
    stale_advisory_context: bool


@dataclass(frozen=True)
class PromotionRejectedResponse:
    """Typed rejection returned by codex.delegate.promote."""

    rejected: bool
    reason: PromotionRejectedReason
    detail: str
    job_id: str | None = None
    expected: str | None = None
    actual: str | None = None


@dataclass(frozen=True)
class DiscardResult:
    """Successful discard result returned by codex.delegate.discard."""

    job: "DelegationJob"


@dataclass(frozen=True)
class DiscardRejectedResponse:
    """Typed rejection returned by codex.delegate.discard."""

    rejected: bool
    reason: DiscardRejectedReason
    detail: str
    job_id: str | None = None
