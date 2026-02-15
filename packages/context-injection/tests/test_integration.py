"""Integration test: full Call 1 → Call 2 pipeline with contract example input."""

import shutil

import pytest

from context_injection.execute import execute_scout
from context_injection.pipeline import process_turn
from context_injection.state import AppContext
from context_injection.types import (
    SCHEMA_VERSION,
    ScoutRequest,
    ScoutResultSuccess,
    TurnPacketSuccess,
    TurnRequest,
)


def test_contract_example_produces_valid_turn_packet() -> None:
    """The contract's Call 1 example input produces a valid TurnPacketSuccess.

    Exercises the full pipeline end-to-end:
    TurnRequest -> entities -> path decisions -> template candidates -> budget -> store
    """
    git_files = {
        "src/config/settings.yaml",
        "src/config/loader.py",
        "config.yaml",
    }
    ctx = AppContext.create(repo_root="/tmp/repo", git_files=git_files)

    request = TurnRequest.model_validate(
        {
            "schema_version": SCHEMA_VERSION,
            "turn_number": 3,
            "conversation_id": "conv_abc123",
            "focus": {
                "text": "Whether the project uses YAML or TOML for configuration",
                "claims": [
                    {
                        "text": "The project uses `src/config/settings.yaml` for all configuration",
                        "status": "new",
                        "turn": 3,
                    },
                    {
                        "text": "YAML was chosen over TOML for readability",
                        "status": "new",
                        "turn": 3,
                    },
                ],
                "unresolved": [
                    {
                        "text": "Whether `config.yaml` is the only config file or if there are environment overrides",
                        "turn": 3,
                    }
                ],
            },
            "context_claims": [
                {
                    "text": "The project follows a monorepo structure with `packages/` subdirectories",
                    "status": "reinforced",
                    "turn": 1,
                }
            ],
            "evidence_history": [
                {
                    "entity_key": "file_path:src/config/loader.py",
                    "template_id": "probe.file_repo_fact",
                    "turn": 1,
                }
            ],
            "posture": "evaluative",
        }
    )

    result = process_turn(request, ctx)
    assert isinstance(result, TurnPacketSuccess)
    assert result.schema_version == SCHEMA_VERSION
    assert result.status == "success"

    # --- Entities ---
    # Should have extracted entities from backticked paths in claims and unresolved.
    # Claim 1: `src/config/settings.yaml` -> file_path (has /, backticked)
    # Unresolved: `config.yaml` -> file_name (known extension, no /, backticked)
    # Context claim: `packages/` -> file_path (has /, backticked, in_focus=False)
    entity_types = {e.type for e in result.entities}
    assert "file_path" in entity_types
    assert "file_name" in entity_types

    # Verify in_focus propagation
    focus_entities = [e for e in result.entities if e.in_focus]
    context_entities = [e for e in result.entities if not e.in_focus]
    assert len(focus_entities) >= 2  # settings.yaml + config.yaml at minimum
    assert len(context_entities) >= 1  # packages/ from context_claims

    # Backticked entities should be high confidence
    settings_entities = [e for e in result.entities if "settings.yaml" in e.canonical]
    assert len(settings_entities) == 1
    assert settings_entities[0].confidence == "high"
    assert settings_entities[0].type == "file_path"
    assert settings_entities[0].canonical == "src/config/settings.yaml"

    config_entities = [e for e in result.entities if e.canonical == "config.yaml"]
    assert len(config_entities) == 1
    assert config_entities[0].confidence == "high"
    assert config_entities[0].type == "file_name"

    # --- Path decisions ---
    # Tier 1 file entities get path decisions.
    # src/config/settings.yaml -> allowed (in git_files)
    # config.yaml -> allowed (in git_files)
    # packages/ -> not_tracked (not in git_files as a file)
    allowed_decisions = [pd for pd in result.path_decisions if pd.status == "allowed"]
    assert len(allowed_decisions) >= 2  # settings.yaml + config.yaml

    # --- Budget ---
    # 1 prior evidence item -> evidence_count=1, remaining=4
    assert result.budget.evidence_count == 1
    assert result.budget.evidence_remaining == 4
    assert result.budget.scout_available is True

    # --- Deduped ---
    # No extracted entity has key "file_path:src/config/loader.py" because
    # loader.py is not mentioned in any claim/unresolved text. Dedupe only
    # matches extracted entities against evidence_history, so deduped is empty.
    assert result.deduped == []

    # --- Template candidates ---
    # src/config/settings.yaml: file_path, in_focus=True, allowed -> probe.file_repo_fact
    # config.yaml: file_name, in_focus=True, allowed -> probe.file_repo_fact
    # packages/: file_path, in_focus=False -> excluded by focus-affinity gate
    assert len(result.template_candidates) >= 2

    probe_candidates = [
        tc
        for tc in result.template_candidates
        if tc.template_id == "probe.file_repo_fact"
    ]
    assert len(probe_candidates) >= 2

    # Each probe candidate should have scout_options with HMAC tokens
    for tc in probe_candidates:
        assert len(tc.scout_options) > 0
        for so in tc.scout_options:
            assert so.scout_token  # Non-empty HMAC token

    # Probes should be ranked (rank 1 = best)
    ranks = [tc.rank for tc in probe_candidates]
    assert ranks == sorted(ranks)
    assert ranks[0] == 1

    # --- Store ---
    # TurnRequest should be stored for Call 2 validation
    ref = "conv_abc123:3"
    assert ref in ctx.store
    record = ctx.store[ref]
    assert record.turn_request is request
    assert not record.used
    # spec_registry should have scout option entries
    assert len(record.scout_options) > 0


def test_grep_call1_call2_round_trip(tmp_path) -> None:
    """Full Call 1 -> Call 2 flow for a grep scout.

    Creates a file with a searchable dotted symbol, runs process_turn
    (Call 1) to extract the symbol entity and create a grep scout option,
    then runs execute_scout (Call 2) to grep for the symbol and verify
    the result contains matching evidence.

    Requires ripgrep (rg) on PATH.
    """
    if shutil.which("rg") is None:
        pytest.skip("ripgrep (rg) not installed")

    # Setup: file containing a dotted symbol
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "loader.py").write_text(
        "from app.config.load import get_settings\n"
        "\n"
        "def init():\n"
        "    settings = app.config.load()\n"
        "    return settings\n"
    )

    git_files = {"src/loader.py"}
    ctx = AppContext.create(repo_root=str(tmp_path), git_files=git_files)

    # Call 1: process_turn with a focus mentioning the dotted symbol
    request = TurnRequest.model_validate(
        {
            "schema_version": SCHEMA_VERSION,
            "turn_number": 1,
            "conversation_id": "conv_grep_test",
            "focus": {
                "text": "How does `app.config.load` initialize settings?",
                "claims": [
                    {
                        "text": "`app.config.load` reads from YAML files",
                        "status": "new",
                        "turn": 1,
                    },
                ],
                "unresolved": [],
            },
            "posture": "exploratory",
        }
    )

    result = process_turn(request, ctx)
    assert isinstance(result, TurnPacketSuccess)

    # Find the grep scout option (probe.symbol_repo_fact)
    grep_candidates = [
        tc
        for tc in result.template_candidates
        if tc.template_id == "probe.symbol_repo_fact"
    ]
    assert len(grep_candidates) >= 1, (
        f"Expected grep candidate but got templates: "
        f"{[tc.template_id for tc in result.template_candidates]}"
    )

    grep_tc = grep_candidates[0]
    assert len(grep_tc.scout_options) == 1
    grep_option = grep_tc.scout_options[0]
    assert grep_option.action == "grep"

    # Call 2: execute_scout with the grep option
    ref = f"{request.conversation_id}:{request.turn_number}"
    scout_req = ScoutRequest(
        schema_version=SCHEMA_VERSION,
        scout_option_id=grep_option.id,
        scout_token=grep_option.scout_token,
        turn_request_ref=ref,
    )
    scout_result = execute_scout(ctx, scout_req)

    assert isinstance(scout_result, ScoutResultSuccess)
    assert scout_result.action == "grep"
    assert scout_result.grep_result is not None
    assert scout_result.grep_result.match_count > 0
    assert "app.config.load" in scout_result.grep_result.excerpt
    assert scout_result.evidence_wrapper.startswith("Grep for")
    assert scout_result.budget.scout_available is False


def test_grep_no_matches_returns_success(tmp_path) -> None:
    """Grep for a non-existent symbol returns success with 0 matches.

    Absence is data per design spec — the model learns the symbol
    doesn't exist in the repo.
    """
    if shutil.which("rg") is None:
        pytest.skip("ripgrep (rg) not installed")

    (tmp_path / "main.py").write_text("def hello():\n    return 1\n")
    git_files = {"main.py"}
    ctx = AppContext.create(repo_root=str(tmp_path), git_files=git_files)

    request = TurnRequest.model_validate(
        {
            "schema_version": SCHEMA_VERSION,
            "turn_number": 1,
            "conversation_id": "conv_no_match",
            "focus": {
                "text": "How does `nonexistent.symbol.name` work?",
                "claims": [
                    {
                        "text": "`nonexistent.symbol.name` is used somewhere",
                        "status": "new",
                        "turn": 1,
                    },
                ],
                "unresolved": [],
            },
            "posture": "exploratory",
        }
    )

    result = process_turn(request, ctx)
    assert isinstance(result, TurnPacketSuccess)

    grep_candidates = [
        tc for tc in result.template_candidates
        if tc.template_id == "probe.symbol_repo_fact"
    ]
    assert len(grep_candidates) >= 1

    grep_option = grep_candidates[0].scout_options[0]
    ref = f"{request.conversation_id}:{request.turn_number}"
    scout_req = ScoutRequest(
        schema_version=SCHEMA_VERSION,
        scout_option_id=grep_option.id,
        scout_token=grep_option.scout_token,
        turn_request_ref=ref,
    )
    scout_result = execute_scout(ctx, scout_req)

    assert isinstance(scout_result, ScoutResultSuccess)
    assert scout_result.grep_result.match_count == 0
    assert scout_result.grep_result.excerpt == ""
    assert "0 matches" in scout_result.evidence_wrapper


def test_grep_denied_file_filtered(tmp_path) -> None:
    """Matches in denied files (.env) are excluded from grep results."""
    if shutil.which("rg") is None:
        pytest.skip("ripgrep (rg) not installed")

    # The symbol appears ONLY in a .env file (denied)
    (tmp_path / ".env").write_text("app.config.load=true\n")
    git_files = {".env"}
    ctx = AppContext.create(repo_root=str(tmp_path), git_files=git_files)

    request = TurnRequest.model_validate(
        {
            "schema_version": SCHEMA_VERSION,
            "turn_number": 1,
            "conversation_id": "conv_denied",
            "focus": {
                "text": "Where is `app.config.load` used?",
                "claims": [
                    {
                        "text": "`app.config.load` is referenced in the codebase",
                        "status": "new",
                        "turn": 1,
                    },
                ],
                "unresolved": [],
            },
            "posture": "exploratory",
        }
    )

    result = process_turn(request, ctx)
    assert isinstance(result, TurnPacketSuccess)

    grep_candidates = [
        tc for tc in result.template_candidates
        if tc.template_id == "probe.symbol_repo_fact"
    ]
    assert len(grep_candidates) >= 1, (
        f"Expected grep candidate for app.config.load but got templates: "
        f"{[tc.template_id for tc in result.template_candidates]}"
    )

    grep_option = grep_candidates[0].scout_options[0]
    ref = f"{request.conversation_id}:{request.turn_number}"
    scout_req = ScoutRequest(
        schema_version=SCHEMA_VERSION,
        scout_option_id=grep_option.id,
        scout_token=grep_option.scout_token,
        turn_request_ref=ref,
    )
    scout_result = execute_scout(ctx, scout_req)

    assert isinstance(scout_result, ScoutResultSuccess)
    # rg may find the match, but filter_file should exclude .env
    assert scout_result.grep_result.match_count == 0
