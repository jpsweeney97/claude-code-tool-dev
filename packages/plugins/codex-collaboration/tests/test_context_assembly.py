from __future__ import annotations

from pathlib import Path

import pytest

from server.context_assembly import ContextAssemblyError, assemble_context_packet
from server.models import ConsultRequest, RepoIdentity


def _repo_identity(repo_root: Path) -> RepoIdentity:
    return RepoIdentity(repo_root=repo_root, branch="main", head="abc123")


def test_assemble_context_packet_records_context_size(tmp_path: Path) -> None:
    file_path = tmp_path / "src.py"
    file_path.write_text("print('hello')\n", encoding="utf-8")
    request = ConsultRequest(
        repo_root=tmp_path,
        objective="Explain the file",
        user_constraints=("Be precise",),
        acceptance_criteria=("Mention the entrypoint",),
        explicit_paths=(Path("src.py"),),
    )

    packet = assemble_context_packet(
        request,
        _repo_identity(tmp_path),
        profile="advisory",
    )

    assert packet.context_size == len(packet.payload.encode("utf-8"))
    assert '"repo_root": "' + str(tmp_path) + '"' in packet.payload
    assert "src.py" in packet.payload


def test_assembly_trims_low_priority_categories_first(tmp_path: Path) -> None:
    file_path = tmp_path / "focus.py"
    file_path.write_text("print('focus')\n", encoding="utf-8")
    large_summaries = tuple("b" * 8000 for _ in range(6))
    request = ConsultRequest(
        repo_root=tmp_path,
        objective="Review the focused file",
        explicit_paths=(Path("focus.py"),),
        broad_repository_summaries=large_summaries,
    )

    packet = assemble_context_packet(
        request,
        _repo_identity(tmp_path),
        profile="advisory",
    )

    assert "focus.py" in packet.payload
    assert "broad_repository_summaries" in packet.omitted_categories
    assert packet.context_size <= 24 * 1024


def test_assembly_redacts_secrets_from_files_and_snippets(tmp_path: Path) -> None:
    file_path = tmp_path / "secret.txt"
    file_path.write_text(
        "token = sk-abcdefghijklmnopqrstuvwxyz\n"
        "password = hunter2secret\n"
        "-----BEGIN PRIVATE KEY-----\nsecret-material\n-----END PRIVATE KEY-----\n",
        encoding="utf-8",
    )
    request = ConsultRequest(
        repo_root=tmp_path,
        objective="Summarize secret handling",
        explicit_paths=(Path("secret.txt"),),
        explicit_snippets=("Bearer abcdefghijklmnop",),
    )

    packet = assemble_context_packet(
        request,
        _repo_identity(tmp_path),
        profile="advisory",
    )

    assert "sk-abcdefghijklmnopqrstuvwxyz" not in packet.payload
    assert "Bearer abcdefghijklmnop" not in packet.payload
    assert "hunter2secret" not in packet.payload
    assert "BEGIN PRIVATE KEY" not in packet.payload
    assert packet.payload.count("[redacted]") >= 4


def test_assembly_rejects_out_of_repo_paths(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("nope\n", encoding="utf-8")
    request = ConsultRequest(
        repo_root=tmp_path,
        objective="Summarize the outside file",
        explicit_paths=(outside,),
    )

    with pytest.raises(ContextAssemblyError, match="escapes repository root"):
        assemble_context_packet(
            request,
            _repo_identity(tmp_path),
            profile="advisory",
        )


def test_assembly_rejects_when_packet_exceeds_hard_cap(tmp_path: Path) -> None:
    request = ConsultRequest(
        repo_root=tmp_path,
        objective="x" * (60 * 1024),
    )

    with pytest.raises(ContextAssemblyError, match="exceeds hard cap"):
        assemble_context_packet(
            request,
            _repo_identity(tmp_path),
            profile="advisory",
        )


def test_assembly_rejects_external_research_without_widened_policy(tmp_path: Path) -> None:
    request = ConsultRequest(
        repo_root=tmp_path,
        objective="Review external material",
        external_research_material=("A web summary",),
        network_access=False,
    )

    with pytest.raises(ContextAssemblyError, match="requires widened advisory policy"):
        assemble_context_packet(
            request,
            _repo_identity(tmp_path),
            profile="advisory",
        )


def test_assembly_keeps_delegation_summaries_separate_from_supplementary_context(tmp_path: Path) -> None:
    request = ConsultRequest(
        repo_root=tmp_path,
        objective="Review delegation artifacts",
        delegation_summaries=("diff summary",),
        supplementary_context=("extra notes",),
    )

    packet = assemble_context_packet(
        request,
        _repo_identity(tmp_path),
        profile="advisory",
    )

    assert "delegation_summaries" in packet.payload
    assert "supplementary_context" in packet.payload


def test_assembly_truncates_large_file_excerpts(tmp_path: Path) -> None:
    file_path = tmp_path / "large.txt"
    file_path.write_text("a" * 5000, encoding="utf-8")
    request = ConsultRequest(
        repo_root=tmp_path,
        objective="Review the large file",
        explicit_paths=(Path("large.txt"),),
    )

    packet = assemble_context_packet(
        request,
        _repo_identity(tmp_path),
        profile="advisory",
    )

    assert "...[truncated]" in packet.payload


def test_execution_profile_records_denied_categories_as_omitted(tmp_path: Path) -> None:
    request = ConsultRequest(
        repo_root=tmp_path,
        objective="Execute a task",
        broad_repository_summaries=("broad summary",),
    )

    packet = assemble_context_packet(
        request,
        _repo_identity(tmp_path),
        profile="execution",
    )

    assert "broad_repository_summaries" in packet.omitted_categories
