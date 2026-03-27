"""Core models for Runtime Milestone R1."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal


CapabilityProfile = Literal["advisory", "execution"]
AuthStatus = Literal["authenticated", "expired", "missing"]


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
    session: Any
    started_at: float
    thread_count: int = 0
    app_server_version: str | None = None


@dataclass(frozen=True)
class StaleAdvisoryContextMarker:
    """Persisted stale advisory context marker."""

    repo_root: str
    promoted_head: str
    recorded_at: str


@dataclass(frozen=True)
class AuditEvent:
    """Minimal audit event persisted for R1 flows."""

    event_id: str
    timestamp: str
    actor: Literal["claude", "codex", "user", "system"]
    action: str
    collaboration_id: str
    runtime_id: str
    context_size: int | None = None
    policy_fingerprint: str | None = None
    turn_id: str | None = None
    # R1 only emits consult events. The spec's delegation-oriented audit fields
    # such as job_id, request_id, artifact_hash, decision, and causal_parent
    # are deferred until those flows exist in code.
    extra: dict[str, Any] = field(default_factory=dict)
