"""Context assembly, redaction, and trimming for Codex-facing packets."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .models import AssembledPacket, CapabilityProfile, ConsultRequest, RepoIdentity


_SOFT_TARGETS = {
    "advisory": 24 * 1024,
    "execution": 12 * 1024,
}
_HARD_CAPS = {
    "advisory": 48 * 1024,
    "execution": 24 * 1024,
}
_TRIM_ORDER = {
    "advisory": [
        "explicit_references",
        "task_local_context",
        "delegation_summaries",
        "promoted_summaries",
        "broad_repository_summaries",
        "supplementary_context",
        "external_research_material",
    ],
    "execution": [
        "explicit_references",
        "task_local_context",
        "delegation_summaries",
        "promoted_summaries",
        "supplementary_context",
    ],
}
_MAX_FILE_EXCERPT_BYTES = 4096
_BINARY_SNIFF_BYTES = 8192
_BINARY_PLACEHOLDER = "[binary or non-UTF-8 file \u2014 content not shown]"


class ContextAssemblyError(RuntimeError):
    """Raised when packet assembly cannot satisfy the active profile contract."""


@dataclass(frozen=True)
class _ContextEntry:
    category: str
    label: str
    content: str


def assemble_context_packet(
    request: ConsultRequest,
    repo_identity: RepoIdentity,
    *,
    profile: CapabilityProfile,
    stale_workspace_summary: str | None = None,
) -> AssembledPacket:
    """Assemble, redact, and trim a packet for the given capability profile."""

    if profile not in _SOFT_TARGETS:
        raise ContextAssemblyError(
            f"Context assembly failed: unsupported profile. Got: {profile!r:.100}"
        )

    if request.external_research_material and profile != "advisory":
        raise ContextAssemblyError(
            "Context assembly failed: external research is not allowed outside advisory. "
            f"Got: {profile!r:.100}"
        )
    if request.external_research_material and not request.network_access:
        raise ContextAssemblyError(
            "Context assembly failed: external research requires widened advisory policy. "
            f"Got: {request.network_access!r:.100}"
        )

    explicit_entries = _build_explicit_entries(request.repo_root, request.explicit_paths)
    for index, snippet in enumerate(request.explicit_snippets, start=1):
        explicit_entries.append(
            _ContextEntry(
                category="explicit_references",
                label=f"snippet:{index}",
                content=_redact_text(snippet),
            )
        )

    task_local_entries = _build_sorted_file_entries(
        request.repo_root,
        request.task_local_paths,
        category="task_local_context",
    )
    promoted_entries = _build_text_entries(
        "promoted_summaries",
        request.promoted_summaries,
    )
    broad_entries = _build_text_entries(
        "broad_repository_summaries",
        request.broad_repository_summaries,
    )
    if stale_workspace_summary is not None:
        broad_entries.append(
            _ContextEntry(
                category="broad_repository_summaries",
                label="workspace_changed_summary",
                content=_redact_text(stale_workspace_summary),
            )
        )
    delegation_entries = _build_text_entries(
        "delegation_summaries",
        request.delegation_summaries,
    )
    supplementary_entries = _build_text_entries(
        "supplementary_context",
        request.supplementary_context,
    )
    external_entries = _build_text_entries(
        "external_research_material",
        request.external_research_material,
    )
    denied_categories: list[str] = []
    if profile != "advisory":
        if broad_entries:
            denied_categories.append("broad_repository_summaries")
        if external_entries:
            denied_categories.append("external_research_material")

    entries: dict[str, list[_ContextEntry]] = {
        "explicit_references": explicit_entries,
        "task_local_context": task_local_entries,
        "delegation_summaries": delegation_entries,
        "promoted_summaries": promoted_entries,
        "broad_repository_summaries": broad_entries if profile == "advisory" else [],
        "supplementary_context": supplementary_entries,
        "external_research_material": external_entries if profile == "advisory" else [],
    }
    omitted_categories: list[str] = denied_categories.copy()

    packet = _render_packet(
        request=request,
        repo_identity=repo_identity,
        profile=profile,
        entries=entries,
    )
    context_size = len(packet.encode("utf-8"))
    soft_target = _SOFT_TARGETS[profile]
    hard_cap = _HARD_CAPS[profile]
    if context_size > soft_target:
        trimmed = _trim_entries(
            entries=entries,
            profile=profile,
            request=request,
            repo_identity=repo_identity,
            omitted_categories=omitted_categories,
        )
        packet = trimmed[0]
        context_size = trimmed[1]
    if context_size > hard_cap:
        raise ContextAssemblyError(
            "Context assembly failed: packet exceeds hard cap after trimming. "
            f"Got: {context_size!r:.100}"
        )
    return AssembledPacket(
        profile=profile,
        payload=packet,
        context_size=context_size,
        omitted_categories=tuple(dict.fromkeys(omitted_categories)),
    )


def _trim_entries(
    *,
    entries: dict[str, list[_ContextEntry]],
    profile: CapabilityProfile,
    request: ConsultRequest,
    repo_identity: RepoIdentity,
    omitted_categories: list[str],
) -> tuple[str, int]:
    while True:
        packet = _render_packet(
            request=request,
            repo_identity=repo_identity,
            profile=profile,
            entries=entries,
        )
        size = len(packet.encode("utf-8"))
        if size <= _SOFT_TARGETS[profile]:
            return packet, size
        removed = False
        for category in reversed(_TRIM_ORDER[profile]):
            bucket = entries[category]
            if bucket:
                bucket.pop()
                omitted_categories.append(category)
                removed = True
                break
        if not removed:
            return packet, size


def _render_packet(
    *,
    request: ConsultRequest,
    repo_identity: RepoIdentity,
    profile: CapabilityProfile,
    entries: dict[str, list[_ContextEntry]],
) -> str:
    payload = {
        "objective": _redact_text(request.objective),
        "relevant_repository_context": {
            "repository_identity": {
                "repo_root": str(repo_identity.repo_root),
                "branch": _redact_text(repo_identity.branch),
                "head": repo_identity.head,
            },
        },
        "user_constraints": {
            "constraints": [_redact_text(item) for item in request.user_constraints],
            "acceptance_criteria": [
                _redact_text(item) for item in request.acceptance_criteria
            ],
        },
        "safety_envelope": _build_safety_envelope(profile=profile, network_access=request.network_access),
        "expected_output_shape": {
            "position": "string",
            "evidence": [{"claim": "string", "citation": "string"}],
            "uncertainties": ["string"],
            "follow_up_branches": ["string"],
        },
        "capability_specific_instructions": _capability_instructions(profile),
    }
    repository_context = payload["relevant_repository_context"]
    for category, label in (
        ("explicit_references", "explicit_references"),
        ("task_local_context", "task_local_context"),
        ("delegation_summaries", "delegation_summaries"),
        ("promoted_summaries", "promoted_summaries"),
        ("broad_repository_summaries", "broad_repository_summaries"),
        ("supplementary_context", "supplementary_context"),
        ("external_research_material", "external_research_material"),
    ):
        if entries[category]:
            repository_context[label] = [
                {"label": entry.label, "content": entry.content}
                for entry in entries[category]
            ]
    return json.dumps(payload, indent=2, sort_keys=False)


def _build_safety_envelope(*, profile: CapabilityProfile, network_access: bool) -> dict[str, object]:
    if profile == "advisory":
        return {
            "sandbox": "read_only",
            "approval_mode": "per_request_only",
            "network_access": "enabled" if network_access else "disabled",
            "prohibitions": [
                "no file mutation",
                "no approval persistence",
                "no implicit escalation",
            ],
        }
    return {
        "sandbox": "isolated_worktree",
        "approval_mode": "explicit_review",
        "network_access": "enabled" if network_access else "disabled",
        "prohibitions": [
            "promotion is a separate step",
            "no writes outside the isolated worktree",
        ],
    }


def _capability_instructions(profile: CapabilityProfile) -> list[str]:
    if profile == "advisory":
        return [
            "Provide a grounded second opinion for the current repository state.",
            "Keep reasoning scoped to read-only advisory work.",
            "Use concise evidence-backed citations when available.",
            "Return valid JSON matching the requested output schema.",
        ]
    return [
        "Operate only within the isolated writable worktree.",
        "Do not assume promotion into the primary workspace is authorized.",
        "Return valid JSON matching the requested output schema.",
    ]


def _build_explicit_entries(repo_root: Path, paths: tuple[Path, ...]) -> list[_ContextEntry]:
    entries: list[_ContextEntry] = []
    for path in paths:
        entries.append(
            _ContextEntry(
                category="explicit_references",
                label=_display_path(repo_root, path),
                content=_read_file_excerpt(repo_root, path),
            )
        )
    return entries


def _build_sorted_file_entries(
    repo_root: Path,
    paths: tuple[Path, ...],
    *,
    category: str,
) -> list[_ContextEntry]:
    sorted_paths = sorted(paths, key=lambda item: _normalized_path(repo_root, item))
    return [
        _ContextEntry(
            category=category,
            label=_display_path(repo_root, path),
            content=_read_file_excerpt(repo_root, path),
        )
        for path in sorted_paths
    ]


def _build_text_entries(category: str, values: tuple[str, ...]) -> list[_ContextEntry]:
    return [
        _ContextEntry(category=category, label=f"{category}:{index}", content=_redact_text(value))
        for index, value in enumerate(values, start=1)
    ]


def _read_file_excerpt(repo_root: Path, path: Path) -> str:
    resolved_repo_root = repo_root.resolve()
    candidate = (resolved_repo_root / path).resolve() if not path.is_absolute() else path.resolve()
    try:
        candidate.relative_to(resolved_repo_root)
    except ValueError as exc:
        raise ContextAssemblyError(
            "Context assembly failed: file reference escapes repository root. "
            f"Got: {str(candidate)!r:.100}"
        ) from exc
    if not candidate.exists():
        raise ContextAssemblyError(
            f"Context assembly failed: file reference missing. Got: {str(candidate)!r:.100}"
        )
    prefix = candidate.read_bytes()[:_BINARY_SNIFF_BYTES]
    if b"\x00" in prefix:
        return _BINARY_PLACEHOLDER
    try:
        raw = candidate.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return _BINARY_PLACEHOLDER
    excerpt = raw[:_MAX_FILE_EXCERPT_BYTES]
    if len(raw) > _MAX_FILE_EXCERPT_BYTES:
        excerpt = excerpt + "\n...[truncated]"
    return _redact_text(excerpt)


def _redact_text(value: str) -> str:
    """Redact secrets using the shared taxonomy with per-match placeholder bypass.

    Contextual families check each match independently against its local
    100-char window. A placeholder near one match does NOT suppress redaction
    of other matches of the same family elsewhere in the string.

    Bypass decisions are evaluated against the pre-redaction snapshot of the
    string from the start of each family's pass. This prevents injected
    [REDACTED:value] markers from prior passes from triggering bypass for
    unrelated matches in subsequent passes.

    Templates that use backreferences (e.g. r"\\1[REDACTED:value]\\3") are
    expanded via match.expand() so capture groups resolve correctly inside
    the replacement function.
    """
    from .secret_taxonomy import FAMILIES, PLACEHOLDER_BYPASS_WINDOW

    redacted = value
    for family in FAMILIES:
        if not family.redact_enabled:
            continue
        if family.tier == "contextual" and family.placeholder_bypass:
            # Per-match bypass: each match is independently checked against
            # its local window using the ORIGINAL value as context source.
            # Using the original prevents [REDACTED:value] markers injected by
            # prior passes from triggering the "[redact" bypass word and
            # suppressing unrelated matches in subsequent family passes.
            bypass_words = tuple(w.lower() for w in family.placeholder_bypass)

            def _replace(
                match: re.Match[str],
                _bw: tuple[str, ...] = bypass_words,
                _original: str = value,
            ) -> str:
                start = max(0, match.start() - PLACEHOLDER_BYPASS_WINDOW)
                end = min(len(_original), match.end() + PLACEHOLDER_BYPASS_WINDOW)
                context = _original[start:end].lower()
                if any(word in context for word in _bw):
                    return match.group(0)  # Keep original — placeholder context
                return match.expand(family.redact_template)

            redacted = family.pattern.sub(_replace, redacted)
        else:
            # Strict/broad tiers: always redact, no bypass
            redacted = family.pattern.sub(family.redact_template, redacted)
    return redacted


def _normalized_path(repo_root: Path, path: Path) -> str:
    resolved_repo_root = repo_root.resolve()
    candidate = (resolved_repo_root / path).resolve() if not path.is_absolute() else path.resolve()
    try:
        return candidate.relative_to(resolved_repo_root).as_posix()
    except ValueError as exc:
        raise ContextAssemblyError(
            "Context assembly failed: file reference escapes repository root. "
            f"Got: {str(candidate)!r:.100}"
        ) from exc


def _display_path(repo_root: Path, path: Path) -> str:
    resolved_repo_root = repo_root.resolve()
    candidate = (resolved_repo_root / path).resolve() if not path.is_absolute() else path.resolve()
    try:
        return candidate.relative_to(resolved_repo_root).as_posix()
    except ValueError as exc:
        raise ContextAssemblyError(
            "Context assembly failed: file reference escapes repository root. "
            f"Got: {str(candidate)!r:.100}"
        ) from exc
