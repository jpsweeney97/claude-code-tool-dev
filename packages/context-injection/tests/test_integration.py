"""Integration test: full Call 1 pipeline with contract example input."""

from context_injection.pipeline import process_turn
from context_injection.state import AppContext
from context_injection.types import SCHEMA_VERSION, TurnRequest, TurnPacketSuccess


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
    settings_entities = [
        e for e in result.entities if "settings.yaml" in e.canonical
    ]
    assert len(settings_entities) == 1
    assert settings_entities[0].confidence == "high"
    assert settings_entities[0].type == "file_path"
    assert settings_entities[0].canonical == "src/config/settings.yaml"

    config_entities = [
        e for e in result.entities if e.canonical == "config.yaml"
    ]
    assert len(config_entities) == 1
    assert config_entities[0].confidence == "high"
    assert config_entities[0].type == "file_name"

    # --- Path decisions ---
    # Tier 1 file entities get path decisions.
    # src/config/settings.yaml -> allowed (in git_files)
    # config.yaml -> allowed (in git_files)
    # packages/ -> not_tracked (not in git_files as a file)
    allowed_decisions = [
        pd for pd in result.path_decisions if pd.status == "allowed"
    ]
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
