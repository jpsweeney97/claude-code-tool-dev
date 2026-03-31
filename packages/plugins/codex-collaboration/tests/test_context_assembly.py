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
    # sk- key needs 40+ chars after prefix for new taxonomy (openai_api_key family)
    sk_key = "sk-abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMN"
    # Bearer token needs 20+ chars for new taxonomy (bearer_auth_header family)
    bearer_token = "Bearer abcdefghijklmnopqrst"
    # PEM is redact_enabled=False in taxonomy (egress-only). Use JWT instead.
    jwt = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJzdWIiOiIxMjM0NTY3ODkwIn0."
        "dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
    )
    file_path = tmp_path / "secret.txt"
    file_path.write_text(
        f"api_secret = {sk_key}\n"
        "password = hunter2secret\n"
        f"{jwt}\n",
        encoding="utf-8",
    )
    request = ConsultRequest(
        repo_root=tmp_path,
        objective="Summarize secret handling",
        explicit_paths=(Path("secret.txt"),),
        explicit_snippets=(bearer_token,),
    )

    packet = assemble_context_packet(
        request,
        _repo_identity(tmp_path),
        profile="advisory",
    )

    assert sk_key not in packet.payload
    assert "abcdefghijklmnopqrst" not in packet.payload
    assert "hunter2secret" not in packet.payload
    assert jwt not in packet.payload
    assert packet.payload.count("[REDACTED:value]") >= 4


def test_assembly_redacts_low_ambiguity_credential_forms(tmp_path: Path) -> None:
    file_path = tmp_path / "credentials.txt"
    gh_suffix = "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
    basic_secret = "dXNlcjpwYXNz"
    url_secret = "supersecret"
    # Use an AWS key without bypass words (AKIAIOSFODNN7EXAMPLE contains "EXAMPLE"
    # which triggers placeholder bypass for nearby contextual tokens).
    aws_key = "AKIAZXCVBNMQWERTYU10"
    file_path.write_text(
        f"aws_access_key_id = {aws_key}\n"
        f"github_pat = ghp_{gh_suffix}\n"
        f"github_oauth = gho_{gh_suffix}\n"
        f"github_server = ghs_{gh_suffix}\n"
        f"github_refresh = ghr_{gh_suffix}\n"
        f"basic_header = Authorization: Basic {basic_secret}\n"
        f"url = https://build:{url_secret}@ci.internal/path\n",
        encoding="utf-8",
    )
    request = ConsultRequest(
        repo_root=tmp_path,
        objective="Summarize credential handling",
        explicit_paths=(Path("credentials.txt"),),
    )

    packet = assemble_context_packet(
        request,
        _repo_identity(tmp_path),
        profile="advisory",
    )

    assert aws_key not in packet.payload
    assert f"ghp_{gh_suffix}" not in packet.payload
    assert f"gho_{gh_suffix}" not in packet.payload
    assert f"ghs_{gh_suffix}" not in packet.payload
    assert f"ghr_{gh_suffix}" not in packet.payload
    assert basic_secret not in packet.payload
    assert url_secret not in packet.payload
    assert "Authorization: Basic [REDACTED:value]" in packet.payload
    assert "://build:[REDACTED:value]@" in packet.payload


def test_assembly_does_not_redact_code_like_false_positives(tmp_path: Path) -> None:
    file_path = tmp_path / "config.py"
    file_path.write_text(
        "basic_auth_setup = True\n"
        "basic_config = {'mode': 'safe'}\n"
        "ghp_enabled = False\n"
        "akia_prefix = 'AKIA'\n",
        encoding="utf-8",
    )
    request = ConsultRequest(
        repo_root=tmp_path,
        objective="Review config symbols",
        explicit_paths=(Path("config.py"),),
    )

    packet = assemble_context_packet(
        request,
        _repo_identity(tmp_path),
        profile="advisory",
    )

    assert "basic_auth_setup" in packet.payload
    assert "basic_config" in packet.payload
    assert "ghp_enabled" in packet.payload
    assert "akia_prefix" in packet.payload


def test_assembly_does_not_redact_off_by_one_akia_lengths(tmp_path: Path) -> None:
    file_path = tmp_path / "akia_lengths.txt"
    file_path.write_text(
        "akia_short = AKIAIOSFODNN7EXAMPL\n"
        "akia_long = AKIAIOSFODNN7EXAMPLE1\n",
        encoding="utf-8",
    )
    request = ConsultRequest(
        repo_root=tmp_path,
        objective="Review AKIA length boundaries",
        explicit_paths=(Path("akia_lengths.txt"),),
    )

    packet = assemble_context_packet(
        request,
        _repo_identity(tmp_path),
        profile="advisory",
    )

    assert "AKIAIOSFODNN7EXAMPL" in packet.payload
    assert "AKIAIOSFODNN7EXAMPLE1" in packet.payload


def test_assembly_preserves_assignment_label_for_overlapping_redaction_rules(tmp_path: Path) -> None:
    file_path = tmp_path / "overlap.txt"
    file_path.write_text("api_key = AKIAIOSFODNN7EXAMPLE\n", encoding="utf-8")
    request = ConsultRequest(
        repo_root=tmp_path,
        objective="Review overlapping redaction rules",
        explicit_paths=(Path("overlap.txt"),),
    )

    packet = assemble_context_packet(
        request,
        _repo_identity(tmp_path),
        profile="advisory",
    )

    assert "AKIAIOSFODNN7EXAMPLE" not in packet.payload
    assert "api_key = [REDACTED:value]" in packet.payload
    assert packet.payload.count("[REDACTED:value]") == 1


def test_assembly_handles_binary_file_in_explicit_paths(tmp_path: Path) -> None:
    binary_path = tmp_path / "image.png"
    binary_path.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")
    request = ConsultRequest(
        repo_root=tmp_path,
        objective="Review the image reference",
        explicit_paths=(Path("image.png"),),
    )

    packet = assemble_context_packet(
        request,
        _repo_identity(tmp_path),
        profile="advisory",
    )

    assert "binary or non-UTF-8 file" in packet.payload


def test_assembly_preserves_valid_files_alongside_binary(tmp_path: Path) -> None:
    valid_path = tmp_path / "code.py"
    valid_path.write_text("print('hello')\n", encoding="utf-8")
    binary_path = tmp_path / "data.bin"
    binary_path.write_bytes(b"\xff\xfe\x00\x01" * 100)
    request = ConsultRequest(
        repo_root=tmp_path,
        objective="Review files",
        explicit_paths=(Path("code.py"), Path("data.bin")),
    )

    packet = assemble_context_packet(
        request,
        _repo_identity(tmp_path),
        profile="advisory",
    )

    assert "print('hello')" in packet.payload
    assert "binary or non-UTF-8 file" in packet.payload


def test_assembly_handles_binary_file_in_task_local_paths(tmp_path: Path) -> None:
    binary_path = tmp_path / "compiled.wasm"
    binary_path.write_bytes(b"\x00asm\x01\x00\x00\x00")
    request = ConsultRequest(
        repo_root=tmp_path,
        objective="Review task context",
        task_local_paths=(Path("compiled.wasm"),),
    )

    packet = assemble_context_packet(
        request,
        _repo_identity(tmp_path),
        profile="advisory",
    )

    assert "binary or non-UTF-8 file" in packet.payload


def test_assembly_rejects_missing_file(tmp_path: Path) -> None:
    request = ConsultRequest(
        repo_root=tmp_path,
        objective="Reference a nonexistent file",
        explicit_paths=(Path("does_not_exist.py"),),
    )

    with pytest.raises(ContextAssemblyError, match="file reference missing"):
        assemble_context_packet(
            request,
            _repo_identity(tmp_path),
            profile="advisory",
        )


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


class TestTaxonomyBackedRedaction:
    """Verify _redact_text uses the full secret taxonomy."""

    def test_aws_key_redacted(self) -> None:
        from server.context_assembly import _redact_text
        result = _redact_text("key is AKIAIOSFODNN7EXAMPLE here")
        assert "AKIAIOSFODNN7EXAMPLE" not in result
        assert "[REDACTED:value]" in result

    def test_gitlab_pat_redacted(self) -> None:
        from server.context_assembly import _redact_text
        pat = "glpat-" + "A" * 20
        result = _redact_text(f"export TOKEN={pat}")
        assert pat not in result

    def test_slack_bot_token_redacted(self) -> None:
        from server.context_assembly import _redact_text
        result = _redact_text("token xoxb-1234567890-abcdef")
        assert "xoxb-" not in result

    def test_jwt_redacted(self) -> None:
        from server.context_assembly import _redact_text
        jwt = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiIxMjM0NTY3ODkwIn0."
            "dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        )
        result = _redact_text(f"token: {jwt}")
        assert jwt not in result

    def test_placeholder_context_not_redacted(self) -> None:
        from server.context_assembly import _redact_text
        pat = "ghp_" + "A" * 36
        text = f"for example the format is {pat}"
        result = _redact_text(text)
        # Contextual family with placeholder bypass — should NOT redact
        assert pat in result

    def test_per_match_bypass_does_not_suppress_real_tokens(self) -> None:
        """One example token must not suppress redaction of a real token in the same string."""
        from server.context_assembly import _redact_text
        pat = "ghp_" + "A" * 36
        real_pat = "ghp_" + "B" * 36
        # First occurrence has "example" nearby, second does not.
        # Separator is 110 chars to push "example" beyond the 100-char window of real_pat.
        separator = "\n" + "x" * 110 + "\nproduction: "
        text = f"example format: {pat}{separator}{real_pat}"
        result = _redact_text(text)
        # Example token kept, real token redacted
        assert pat in result
        assert real_pat not in result

    def test_clean_text_unchanged(self) -> None:
        from server.context_assembly import _redact_text
        text = "This is a normal code review comment."
        assert _redact_text(text) == text

    def test_branch_name_redacted_in_render(self) -> None:
        """repo_identity.branch passes through _redact_text."""
        from server.context_assembly import _redact_text
        # A branch name containing a secret pattern should be redacted
        branch = "feature/password=hunter2abc"
        result = _redact_text(branch)
        assert "hunter2abc" not in result
