"""Runtime Milestone R1 control plane for codex-collaboration."""

from __future__ import annotations

import hashlib
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from time import time
from typing import Callable

from .codex_compat import (
    OPTIONAL_METHODS,
    REQUIRED_METHODS,
    check_live_runtime_compatibility,
)
from .context_assembly import assemble_context_packet
from .journal import OperationJournal, default_plugin_data_path
from .models import (
    AdvisoryRuntimeState,
    AuditEvent,
    ConsultRequest,
    ConsultResult,
    RepoIdentity,
)
from .prompt_builder import (
    CONSULT_OUTPUT_SCHEMA,
    build_consult_turn_text,
    parse_consult_response,
)
from .runtime import AppServerRuntimeSession


@dataclass(frozen=True)
class _RuntimeProbeResult:
    runtime: AdvisoryRuntimeState | None
    app_server_version: str | None
    auth_status: str | None
    available_methods: frozenset[str]
    error: str | None


class ControlPlane:
    """Implements the advisory subset of the codex-collaboration plugin."""

    def __init__(
        self,
        *,
        plugin_data_path: Path | None = None,
        runtime_factory: Callable[[Path], AppServerRuntimeSession] | None = None,
        compat_checker: Callable[[], object] = check_live_runtime_compatibility,
        repo_identity_loader: Callable[[Path], RepoIdentity] | None = None,
        clock: Callable[[], float] = time,
        uuid_factory: Callable[[], str] | None = None,
        journal: OperationJournal | None = None,
    ) -> None:
        self._plugin_data_path = (plugin_data_path or default_plugin_data_path()).resolve()
        self._runtime_factory = runtime_factory or (lambda repo_root: AppServerRuntimeSession(repo_root=repo_root))
        self._compat_checker = compat_checker
        self._repo_identity_loader = repo_identity_loader or load_repo_identity
        self._clock = clock
        self._uuid_factory = uuid_factory or (lambda: str(uuid.uuid4()))
        self._journal = journal or OperationJournal(self._plugin_data_path)
        self._advisory_runtimes: dict[str, AdvisoryRuntimeState] = {}

    def codex_status(self, repo_root: Path) -> dict[str, object]:
        """Return live health, auth, version, and runtime diagnostics.

        The first status call for a repo root probes the advisory runtime and,
        on success, caches it for later consult reuse.
        """

        resolved_root = repo_root.resolve()
        runtime = self._advisory_runtimes.get(str(resolved_root))
        errors: list[str] = []
        compat_result = self._compat_checker()
        codex_version = getattr(compat_result, "codex_version", None)
        app_server_version = runtime.handshake.user_agent if runtime is not None else None
        auth_status = runtime.account_state.auth_status if runtime is not None else "missing"
        advisory_runtime = None
        available_methods = getattr(compat_result, "available_methods", frozenset())

        probe_result = self._probe_runtime(
            resolved_root,
            compat_result=compat_result,
            existing_runtime=runtime,
        )
        if probe_result.app_server_version is not None:
            app_server_version = probe_result.app_server_version
        if probe_result.auth_status is not None:
            auth_status = probe_result.auth_status
        available_methods = probe_result.available_methods
        if probe_result.error is not None:
            errors.append(probe_result.error)
        runtime = probe_result.runtime
        if runtime is not None:
            app_server_version = runtime.handshake.user_agent
            auth_status = runtime.account_state.auth_status

        if runtime is not None:
            advisory_runtime = {
                "id": runtime.runtime_id,
                "policy_fingerprint": runtime.policy_fingerprint,
                "thread_count": runtime.thread_count,
                "uptime": int(self._clock() - runtime.started_at),
            }
            app_server_version = runtime.handshake.user_agent
            auth_status = runtime.account_state.auth_status

        errors.extend(getattr(compat_result, "errors", ()))
        return {
            "codex_version": str(codex_version) if codex_version is not None else None,
            "app_server_version": app_server_version,
            "auth_status": auth_status,
            "advisory_runtime": advisory_runtime,
            "active_delegation": None,
            "plugin_data_path": str(self._plugin_data_path),
            "required_methods": {
                method: method in available_methods
                for method in sorted(REQUIRED_METHODS)
            },
            "optional_methods": {
                method: method in available_methods
                for method in sorted(OPTIONAL_METHODS)
            },
            "errors": tuple(dict.fromkeys(errors)),
        }

    def codex_consult(self, request: ConsultRequest) -> ConsultResult:
        """Execute a one-shot advisory consultation."""

        # INVARIANT: safe only while advisory turns stay read-only and
        # no-network. Any policy widening must revisit fingerprint
        # invalidation semantics.
        if request.network_access:
            raise RuntimeError(
                "Consult failed: advisory widening is not implemented in R1. "
                f"Got: {request.network_access!r:.100}"
            )

        resolved_root = request.repo_root.resolve()
        runtime = self._bootstrap_runtime(resolved_root, strict=True)
        repo_identity = self._repo_identity_loader(resolved_root)
        stale_marker = self._journal.load_stale_marker(resolved_root)
        stale_summary = None
        if stale_marker is not None:
            stale_summary = (
                "Workspace changed since the last advisory turn. "
                f"Most recent promoted HEAD: {stale_marker.promoted_head}. "
                f"Current HEAD: {repo_identity.head}. "
                "Re-ground reasoning in the current repository state."
            )
        packet = assemble_context_packet(
            request,
            repo_identity,
            profile="advisory",
            stale_workspace_summary=stale_summary,
        )
        posture: str | None = None
        effort: str | None = None
        if request.profile is not None:
            from .profiles import resolve_profile
            resolved = resolve_profile(profile_name=request.profile)
            posture = resolved.posture
            effort = resolved.effort
        try:
            thread_id = (
                runtime.session.fork_thread(request.parent_thread_id)
                if request.parent_thread_id is not None
                else runtime.session.start_thread()
            )
            runtime.thread_count += 1
            turn_result = runtime.session.run_turn(
                thread_id=thread_id,
                prompt_text=build_consult_turn_text(packet.payload, posture=posture),
                output_schema=CONSULT_OUTPUT_SCHEMA,
                effort=effort,
            )
            if stale_marker is not None:
                self._journal.clear_stale_marker(resolved_root)
            position, evidence, uncertainties, follow_up_branches = parse_consult_response(
                turn_result.agent_message
            )
        except Exception:
            self._invalidate_runtime(resolved_root)
            raise
        collaboration_id = self._uuid_factory()
        # INVARIANT: minimal audit schema covers consult/dialogue_turn only.
        # Any new first-class audit action should revisit AuditEvent shape
        # before it is emitted.
        self._journal.append_audit_event(
            AuditEvent(
                event_id=self._uuid_factory(),
                timestamp=self._journal.timestamp(),
                actor="claude",
                action="consult",
                collaboration_id=collaboration_id,
                runtime_id=runtime.runtime_id,
                context_size=packet.context_size,
                policy_fingerprint=runtime.policy_fingerprint,
                turn_id=turn_result.turn_id,
                extra={"repo_root": str(resolved_root)},
            )
        )
        return ConsultResult(
            collaboration_id=collaboration_id,
            runtime_id=runtime.runtime_id,
            position=position,
            evidence=evidence,
            uncertainties=uncertainties,
            follow_up_branches=follow_up_branches,
            context_size=packet.context_size,
        )

    def get_advisory_runtime(self, repo_root: Path) -> AdvisoryRuntimeState:
        """Bootstrap and return the advisory runtime for a repo root.

        Raises RuntimeError if the runtime cannot be established.
        Used by DialogueController for shared runtime access.
        """
        resolved_root = repo_root.resolve()
        runtime = self._bootstrap_runtime(resolved_root, strict=True)
        assert runtime is not None  # strict=True guarantees non-None or raises
        return runtime

    def invalidate_runtime(self, repo_root: Path) -> None:
        """Drop a cached runtime. Public wrapper for error recovery paths."""
        self._invalidate_runtime(repo_root.resolve())

    def close(self) -> None:
        """Close all cached runtimes."""

        for runtime in self._advisory_runtimes.values():
            runtime.session.close()
        self._advisory_runtimes.clear()

    def _bootstrap_runtime(self, repo_root: Path, *, strict: bool) -> AdvisoryRuntimeState | None:
        cached = self._advisory_runtimes.get(str(repo_root))
        compat_result = self._compat_checker()
        probe_result = self._probe_runtime(
            repo_root,
            compat_result=compat_result,
            existing_runtime=cached,
        )
        if probe_result.error is not None:
            if strict:
                raise RuntimeError(probe_result.error)
            return None
        return probe_result.runtime

    def _probe_runtime(
        self,
        repo_root: Path,
        *,
        compat_result: object,
        existing_runtime: AdvisoryRuntimeState | None = None,
    ) -> _RuntimeProbeResult:
        codex_version = getattr(compat_result, "codex_version", None)
        if codex_version is None:
            return _RuntimeProbeResult(
                runtime=None,
                app_server_version=None,
                auth_status=None,
                available_methods=frozenset(),
                error="Runtime bootstrap failed: codex version unavailable. Got: None",
            )

        runtime_key = str(repo_root)
        session = existing_runtime.session if existing_runtime is not None else self._runtime_factory(repo_root)
        try:
            # INVARIANT: safe only while initialize + account/read remain
            # the complete advisory bootstrap surface. Adding any new
            # bootstrap-critical method should revisit the parked bootstrap
            # assertion debt before rollout.
            handshake = existing_runtime.handshake if existing_runtime is not None else session.initialize()
        except Exception as exc:  # pragma: no cover - defensive path
            if existing_runtime is not None:
                self._invalidate_runtime(repo_root)
            else:
                session.close()
            return _RuntimeProbeResult(
                runtime=None,
                app_server_version=None,
                auth_status=None,
                available_methods=frozenset(),
                error=(
                    "Runtime bootstrap failed: initialize failed. "
                    f"Got: {str(exc)!r:.100}"
                ),
            )
        try:
            account_state = session.read_account()
        except Exception as exc:  # pragma: no cover - defensive path
            if existing_runtime is not None:
                self._invalidate_runtime(repo_root)
            else:
                session.close()
            return _RuntimeProbeResult(
                runtime=None,
                app_server_version=handshake.user_agent,
                auth_status=None,
                available_methods=getattr(compat_result, "available_methods", frozenset()),
                error=(
                    "Runtime bootstrap failed: account/read failed. "
                    f"Got: {str(exc)!r:.100}"
                ),
            )

        if not getattr(compat_result, "passed", False):
            if existing_runtime is not None:
                self._invalidate_runtime(repo_root)
            else:
                session.close()
            return _RuntimeProbeResult(
                runtime=None,
                app_server_version=handshake.user_agent,
                auth_status=account_state.auth_status,
                available_methods=getattr(compat_result, "available_methods", frozenset()),
                error=(
                    "Runtime bootstrap failed: compatibility checks failed. "
                    f"Got: {getattr(compat_result, 'errors', ())!r:.200}"
                ),
            )
        if account_state.auth_status != "authenticated":
            if existing_runtime is not None:
                self._invalidate_runtime(repo_root)
            else:
                session.close()
            return _RuntimeProbeResult(
                runtime=None,
                app_server_version=handshake.user_agent,
                auth_status=account_state.auth_status,
                available_methods=getattr(compat_result, "available_methods", frozenset()),
                error=(
                    "Runtime bootstrap failed: advisory auth unavailable. "
                    f"Got: {account_state.auth_status!r:.100}"
                ),
            )

        available_methods = getattr(compat_result, "available_methods", frozenset())
        if existing_runtime is not None:
            existing_runtime.account_state = account_state
            existing_runtime.available_methods = available_methods
            existing_runtime.app_server_version = handshake.user_agent
            runtime = existing_runtime
            self._advisory_runtimes[runtime_key] = runtime
        else:
            runtime = AdvisoryRuntimeState(
                runtime_id=self._uuid_factory(),
                repo_root=repo_root,
                policy_fingerprint=build_policy_fingerprint(),
                handshake=handshake,
                account_state=account_state,
                available_methods=available_methods,
                required_methods=REQUIRED_METHODS,
                optional_methods=OPTIONAL_METHODS,
                session=session,
                started_at=self._clock(),
                app_server_version=handshake.user_agent,
            )
            self._advisory_runtimes[runtime_key] = runtime
        return _RuntimeProbeResult(
            runtime=runtime,
            app_server_version=handshake.user_agent,
            auth_status=account_state.auth_status,
            available_methods=available_methods,
            error=None,
        )

    def _invalidate_runtime(self, repo_root: Path) -> None:
        """Drop a cached runtime after transport or turn failures."""

        runtime = self._advisory_runtimes.pop(str(repo_root), None)
        if runtime is not None:
            runtime.session.close()


def build_policy_fingerprint() -> str:
    """Return the advisory runtime's immutable policy fingerprint."""

    # Keep this material aligned with the actual advisory runtime policy
    # inputs. R1/R2 dev-repo rollout accepts hardcoded values only while the
    # request gate and runtime settings preserve this exact advisory posture.
    material = {
        "transport_mode": "stdio",
        "sandbox_level": "read_only",
        "network_access": "disabled",
        "approval_mode": "never",
        "app_connectors": "disabled",
    }
    digest = hashlib.sha256(repr(sorted(material.items())).encode("utf-8")).hexdigest()
    return digest[:16]


def load_repo_identity(repo_root: Path) -> RepoIdentity:
    """Load the repo root, branch, and HEAD SHA from git."""

    resolved_root = repo_root.resolve()
    branch = _git_output(resolved_root, ["git", "rev-parse", "--abbrev-ref", "HEAD"])
    head = _git_output(resolved_root, ["git", "rev-parse", "HEAD"])
    return RepoIdentity(repo_root=resolved_root, branch=branch, head=head)


def _git_output(repo_root: Path, command: list[str]) -> str:
    try:
        result = subprocess.run(
            command,
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"Git metadata failed: command timed out. Got: {command!r:.100}"
        ) from exc
    if result.returncode != 0:
        raise RuntimeError(
            "Git metadata failed: command returned non-zero exit code. "
            f"Got: {result.stderr.strip()!r:.100}"
        )
    return result.stdout.strip()
