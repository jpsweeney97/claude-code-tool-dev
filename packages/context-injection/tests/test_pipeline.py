"""Tests for the Call 1 pipeline: process_turn().

Tests cover:
1. Schema version validation (correct version succeeds, wrong version → TurnPacketError)
2. Entity extraction from focus.claims, focus.unresolved, context_claims
3. Path decisions for file entities (file_loc, file_path, file_name), not symbol
4. Template matching produces candidates for eligible entities
5. Budget computation reflects evidence_history length
6. TurnRequest stored in ctx.store for Call 2 validation
7. Unexpected exceptions produce TurnPacketError with internal_error
8. End-to-end: realistic TurnRequest → full TurnPacketSuccess
"""

from typing import Any
from unittest.mock import patch

from context_injection.pipeline import process_turn
from context_injection.state import AppContext
from context_injection.types import (
    Claim,
    EvidenceRecord,
    Focus,
    SCHEMA_VERSION,
    TurnPacketError,
    TurnPacketSuccess,
    TurnRequest,
    Unresolved,
)


# --- Test helpers ---


def _make_turn_request(**overrides: Any) -> TurnRequest:
    """Convenience TurnRequest constructor with sensible defaults."""
    defaults: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "turn_number": 1,
        "conversation_id": "conv_test",
        "focus": Focus(text="test focus", claims=[], unresolved=[]),
        "context_claims": [],
        "evidence_history": [],
        "posture": "exploratory",
    }
    defaults.update(overrides)
    return TurnRequest(**defaults)  # type: ignore[arg-type]


def _make_ctx(git_files: set[str] | None = None) -> AppContext:
    """Create AppContext with test defaults."""
    return AppContext.create(
        repo_root="/tmp/repo",
        git_files=git_files or set(),
    )


# ============================================================
# Schema version validation
# ============================================================


class TestSchemaValidation:
    def test_correct_schema_version_succeeds(self) -> None:
        """Correct schema version → TurnPacketSuccess (guard against future version bumps)."""
        ctx = _make_ctx()
        req = _make_turn_request(schema_version="0.1.0")
        # Guard: if SCHEMA_VERSION changes, this test will catch the mismatch.
        result = process_turn(req, ctx)
        assert isinstance(result, TurnPacketSuccess)

    def test_schema_version_mismatch_returns_error(self) -> None:
        """Bypassed Pydantic validation with wrong version → TurnPacketError."""
        ctx = _make_ctx()
        # Use model_construct to bypass Pydantic's Literal validation
        req = TurnRequest.model_construct(
            schema_version="99.0.0",
            turn_number=1,
            conversation_id="conv_test",
            focus=Focus(text="test", claims=[], unresolved=[]),
            context_claims=[],
            evidence_history=[],
            posture="exploratory",
        )
        result = process_turn(req, ctx)
        assert isinstance(result, TurnPacketError)
        assert result.error.code == "invalid_schema_version"

    def test_schema_version_mismatch_detected(self) -> None:
        """When request has a different schema_version, error returned.

        TurnRequest enforces SchemaVersionLiteral via Pydantic, so we use
        model_construct to bypass validation and inject a mismatched version.
        """
        ctx = _make_ctx()
        req = TurnRequest.model_construct(
            schema_version="0.0.0",
            turn_number=1,
            conversation_id="conv_test",
            focus=Focus(text="test", claims=[], unresolved=[]),
            context_claims=[],
            evidence_history=[],
            posture="exploratory",
        )

        result = process_turn(req, ctx)

        assert isinstance(result, TurnPacketError)
        assert result.error.code == "invalid_schema_version"
        assert "0.0.0" in result.error.message


# ============================================================
# Entity extraction
# ============================================================


class TestEntityExtraction:
    def test_entities_extracted_from_focus_claims(self) -> None:
        """Entities in focus.claims are extracted with in_focus=True, source_type=claim."""
        ctx = _make_ctx(git_files={"src/app.py"})
        req = _make_turn_request(
            focus=Focus(
                text="investigating bug",
                claims=[
                    Claim(text="The error is in `src/app.py`", status="new", turn=1),
                ],
                unresolved=[],
            ),
        )

        result = process_turn(req, ctx)
        assert isinstance(result, TurnPacketSuccess)
        assert len(result.entities) >= 1

        file_entities = [e for e in result.entities if e.canonical == "src/app.py"]
        assert len(file_entities) >= 1
        assert file_entities[0].in_focus is True
        assert file_entities[0].source_type == "claim"

    def test_entities_extracted_from_focus_unresolved(self) -> None:
        """Entities in focus.unresolved are extracted with in_focus=True, source_type=unresolved."""
        ctx = _make_ctx(git_files={"config.yaml"})
        req = _make_turn_request(
            focus=Focus(
                text="checking config",
                claims=[],
                unresolved=[
                    Unresolved(text="What is in `config.yaml`?", turn=1),
                ],
            ),
        )

        result = process_turn(req, ctx)
        assert isinstance(result, TurnPacketSuccess)

        file_entities = [e for e in result.entities if e.canonical == "config.yaml"]
        assert len(file_entities) >= 1
        assert file_entities[0].in_focus is True
        assert file_entities[0].source_type == "unresolved"

    def test_entities_extracted_from_context_claims(self) -> None:
        """Entities in context_claims are extracted with in_focus=False, source_type=claim."""
        ctx = _make_ctx(git_files={"tests/test_api.py"})
        req = _make_turn_request(
            context_claims=[
                Claim(text="Tests are in `tests/test_api.py`", status="new", turn=1),
            ],
        )

        result = process_turn(req, ctx)
        assert isinstance(result, TurnPacketSuccess)

        file_entities = [
            e for e in result.entities if e.canonical == "tests/test_api.py"
        ]
        assert len(file_entities) >= 1
        assert file_entities[0].in_focus is False
        assert file_entities[0].source_type == "claim"

    def test_entities_from_all_three_sources_combined(self) -> None:
        """Entities from focus.claims, focus.unresolved, and context_claims
        are combined into a single flat list."""
        ctx = _make_ctx(git_files={"src/app.py", "config.yaml", "tests/test_api.py"})
        req = _make_turn_request(
            focus=Focus(
                text="investigating",
                claims=[
                    Claim(text="File is `src/app.py`", status="new", turn=1),
                ],
                unresolved=[
                    Unresolved(text="What about `config.yaml`?", turn=1),
                ],
            ),
            context_claims=[
                Claim(text="Tests at `tests/test_api.py`", status="new", turn=1),
            ],
        )

        result = process_turn(req, ctx)
        assert isinstance(result, TurnPacketSuccess)

        canonicals = {e.canonical for e in result.entities}
        assert "src/app.py" in canonicals
        assert "config.yaml" in canonicals
        assert "tests/test_api.py" in canonicals

    def test_no_entities_when_no_text_references(self) -> None:
        """Plain text without file/symbol references produces no entities."""
        ctx = _make_ctx()
        req = _make_turn_request(
            focus=Focus(
                text="general question",
                claims=[
                    Claim(text="The code has a bug", status="new", turn=1),
                ],
                unresolved=[],
            ),
        )

        result = process_turn(req, ctx)
        assert isinstance(result, TurnPacketSuccess)
        assert len(result.entities) == 0


# ============================================================
# Path decisions
# ============================================================


class TestPathDecisions:
    def test_file_path_entity_gets_path_decision(self) -> None:
        """Tier 1 file_path entities get a PathDecision."""
        ctx = _make_ctx(git_files={"src/app.py"})
        req = _make_turn_request(
            focus=Focus(
                text="check file",
                claims=[
                    Claim(text="Error in `src/app.py`", status="new", turn=1),
                ],
                unresolved=[],
            ),
        )

        result = process_turn(req, ctx)
        assert isinstance(result, TurnPacketSuccess)
        assert len(result.path_decisions) >= 1

        pd = result.path_decisions[0]
        assert pd.status == "allowed"
        assert pd.user_rel == "src/app.py"

    def test_file_loc_entity_gets_path_decision(self) -> None:
        """Tier 1 file_loc entities get a PathDecision (canonical strips line number)."""
        ctx = _make_ctx(git_files={"src/app.py"})
        req = _make_turn_request(
            focus=Focus(
                text="check line",
                claims=[
                    Claim(text="Bug at `src/app.py:42`", status="new", turn=1),
                ],
                unresolved=[],
            ),
        )

        result = process_turn(req, ctx)
        assert isinstance(result, TurnPacketSuccess)

        # The file_loc entity's canonical is "src/app.py" (line number stripped)
        file_loc_entities = [e for e in result.entities if e.type == "file_loc"]
        assert len(file_loc_entities) >= 1
        assert file_loc_entities[0].canonical == "src/app.py"

        # PathDecision exists for the file_loc entity
        pd_ids = {pd.entity_id for pd in result.path_decisions}
        assert file_loc_entities[0].id in pd_ids

    def test_symbol_entity_no_path_decision(self) -> None:
        """Symbol entities are grep targets — they do NOT get path decisions."""
        ctx = _make_ctx()
        req = _make_turn_request(
            focus=Focus(
                text="check symbol",
                claims=[
                    Claim(
                        text="Uses `os.path.join` extensively",
                        status="new",
                        turn=1,
                    ),
                ],
                unresolved=[],
            ),
        )

        result = process_turn(req, ctx)
        assert isinstance(result, TurnPacketSuccess)

        symbol_entities = [e for e in result.entities if e.type == "symbol"]
        assert len(symbol_entities) >= 1

        # No path decisions for symbol entities
        pd_entity_ids = {pd.entity_id for pd in result.path_decisions}
        for se in symbol_entities:
            assert se.id not in pd_entity_ids

    def test_not_tracked_file_gets_not_tracked_status(self) -> None:
        """A file not in git_files gets status=not_tracked."""
        ctx = _make_ctx(git_files=set())  # No tracked files
        req = _make_turn_request(
            focus=Focus(
                text="check",
                claims=[
                    Claim(text="See `src/app.py`", status="new", turn=1),
                ],
                unresolved=[],
            ),
        )

        result = process_turn(req, ctx)
        assert isinstance(result, TurnPacketSuccess)
        assert len(result.path_decisions) >= 1
        assert result.path_decisions[0].status == "not_tracked"


# ============================================================
# Template matching
# ============================================================


class TestTemplateMatching:
    def test_eligible_file_entity_gets_probe_template(self) -> None:
        """In-focus, high-confidence, allowed file_path → probe.file_repo_fact."""
        ctx = _make_ctx(git_files={"src/app.py"})
        req = _make_turn_request(
            focus=Focus(
                text="check file",
                claims=[
                    Claim(text="Error in `src/app.py`", status="new", turn=1),
                ],
                unresolved=[],
            ),
        )

        result = process_turn(req, ctx)
        assert isinstance(result, TurnPacketSuccess)

        probe_candidates = [
            c
            for c in result.template_candidates
            if c.template_id == "probe.file_repo_fact"
        ]
        assert len(probe_candidates) >= 1
        assert len(probe_candidates[0].scout_options) >= 1

    def test_symbol_entity_gets_grep_template(self) -> None:
        """In-focus, high-confidence symbol → probe.symbol_repo_fact with GrepOption."""
        ctx = _make_ctx()
        req = _make_turn_request(
            focus=Focus(
                text="check symbol",
                claims=[
                    Claim(
                        text="Calls `os.path.join` frequently",
                        status="new",
                        turn=1,
                    ),
                ],
                unresolved=[],
            ),
        )

        result = process_turn(req, ctx)
        assert isinstance(result, TurnPacketSuccess)

        probe_candidates = [
            c
            for c in result.template_candidates
            if c.template_id == "probe.symbol_repo_fact"
        ]
        assert len(probe_candidates) >= 1
        opt = probe_candidates[0].scout_options[0]
        assert opt.action == "grep"

    def test_out_of_focus_entity_no_probe(self) -> None:
        """Context_claims entities (in_focus=False) don't get probe templates."""
        ctx = _make_ctx(git_files={"src/app.py"})
        req = _make_turn_request(
            context_claims=[
                Claim(text="See `src/app.py`", status="new", turn=1),
            ],
        )

        result = process_turn(req, ctx)
        assert isinstance(result, TurnPacketSuccess)

        # Entities exist but are not in focus
        file_entities = [e for e in result.entities if e.canonical == "src/app.py"]
        assert len(file_entities) >= 1
        assert file_entities[0].in_focus is False

        # No probe templates for out-of-focus entities
        probe_candidates = [
            c for c in result.template_candidates if c.template_id.startswith("probe.")
        ]
        assert len(probe_candidates) == 0


# ============================================================
# Budget
# ============================================================


class TestBudget:
    def test_empty_history_full_budget(self) -> None:
        """No evidence history → evidence_count=0, evidence_remaining=5."""
        ctx = _make_ctx()
        req = _make_turn_request()

        result = process_turn(req, ctx)
        assert isinstance(result, TurnPacketSuccess)
        assert result.budget.evidence_count == 0
        assert result.budget.evidence_remaining == 5
        assert result.budget.scout_available is True

    def test_history_reduces_remaining(self) -> None:
        """evidence_history length reduces evidence_remaining."""
        ctx = _make_ctx()
        history = [
            EvidenceRecord(
                entity_key="file_path:src/app.py",
                template_id="probe.file_repo_fact",
                turn=1,
            ),
            EvidenceRecord(
                entity_key="symbol:os.path.join",
                template_id="probe.symbol_repo_fact",
                turn=2,
            ),
        ]
        req = _make_turn_request(evidence_history=history)

        result = process_turn(req, ctx)
        assert isinstance(result, TurnPacketSuccess)
        assert result.budget.evidence_count == 2
        assert result.budget.evidence_remaining == 3

    def test_exhausted_budget(self) -> None:
        """5 evidence records → scout_available=False."""
        ctx = _make_ctx()
        history = [
            EvidenceRecord(
                entity_key=f"file_path:file_{i}.py",
                template_id="probe.file_repo_fact",
                turn=i,
            )
            for i in range(5)
        ]
        req = _make_turn_request(evidence_history=history)

        result = process_turn(req, ctx)
        assert isinstance(result, TurnPacketSuccess)
        assert result.budget.evidence_count == 5
        assert result.budget.evidence_remaining == 0
        assert result.budget.scout_available is False


# ============================================================
# Store record
# ============================================================


class TestStoreRecord:
    def test_turn_request_stored(self) -> None:
        """After process_turn, the TurnRequest is stored in ctx.store."""
        ctx = _make_ctx(git_files={"src/app.py"})
        req = _make_turn_request(
            conversation_id="conv_42",
            turn_number=7,
        )

        result = process_turn(req, ctx)
        assert isinstance(result, TurnPacketSuccess)

        ref = "conv_42:7"
        assert ref in ctx.store
        record = ctx.store[ref]
        assert record.turn_request is req
        assert record.used is False

    def test_spec_registry_stored(self) -> None:
        """Stored record's scout_options contains spec/token pairs for each scout option."""
        ctx = _make_ctx(git_files={"src/app.py"})
        req = _make_turn_request(
            focus=Focus(
                text="check",
                claims=[
                    Claim(text="Error in `src/app.py`", status="new", turn=1),
                ],
                unresolved=[],
            ),
        )

        result = process_turn(req, ctx)
        assert isinstance(result, TurnPacketSuccess)

        ref = "conv_test:1"
        record = ctx.store[ref]

        # If there are probe templates, the spec_registry should have entries
        probe_candidates = [
            c for c in result.template_candidates if c.template_id.startswith("probe.")
        ]
        if probe_candidates:
            assert len(record.scout_options) > 0
            for so_id, (spec, token) in record.scout_options.items():
                assert so_id.startswith("so_")
                assert isinstance(token, str)
                assert len(token) > 0

    def test_duplicate_ref_raises_on_second_call(self) -> None:
        """Same conversation_id + turn_number twice → ValueError from store_record."""
        ctx = _make_ctx()
        req = _make_turn_request(conversation_id="conv_dup", turn_number=1)

        result1 = process_turn(req, ctx)
        assert isinstance(result1, TurnPacketSuccess)

        # Second call with same ref → internal_error (caught by exception handler)
        result2 = process_turn(req, ctx)
        assert isinstance(result2, TurnPacketError)
        assert result2.error.code == "internal_error"
        assert "Duplicate" in result2.error.message


# ============================================================
# Error handling
# ============================================================


class TestErrorHandling:
    def test_unexpected_exception_returns_internal_error(self) -> None:
        """Any unexpected exception → TurnPacketError with internal_error."""
        ctx = _make_ctx()
        req = _make_turn_request(
            focus=Focus(
                text="check",
                claims=[
                    Claim(text="Error in `src/app.py`", status="new", turn=1),
                ],
                unresolved=[],
            ),
        )

        with patch(
            "context_injection.pipeline.extract_entities",
            side_effect=RuntimeError("boom"),
        ):
            result = process_turn(req, ctx)

        assert isinstance(result, TurnPacketError)
        assert result.error.code == "internal_error"
        assert "boom" in result.error.message

    def test_error_packet_has_schema_version(self) -> None:
        """Error packets always include the current schema_version."""
        ctx = _make_ctx()
        req = _make_turn_request(
            focus=Focus(
                text="trigger extraction",
                claims=[
                    Claim(text="See `src/app.py`", status="new", turn=1),
                ],
                unresolved=[],
            ),
        )

        with patch(
            "context_injection.pipeline.extract_entities",
            side_effect=TypeError("unexpected"),
        ):
            result = process_turn(req, ctx)

        assert isinstance(result, TurnPacketError)
        assert result.schema_version == SCHEMA_VERSION


# ============================================================
# End-to-end
# ============================================================


class TestEndToEnd:
    def test_realistic_turn_request_produces_full_packet(self) -> None:
        """Realistic TurnRequest with multiple sources → TurnPacketSuccess
        with entities, path_decisions, template_candidates, budget, deduped."""
        git_files = {"src/app.py", "src/config.yaml", "tests/test_app.py"}
        ctx = _make_ctx(git_files=git_files)

        req = _make_turn_request(
            conversation_id="conv_e2e",
            turn_number=3,
            focus=Focus(
                text="investigating authentication bug",
                claims=[
                    Claim(
                        text="The auth logic in `src/app.py:42` is incorrect",
                        status="new",
                        turn=3,
                    ),
                    Claim(
                        text="Config is loaded from `src/config.yaml`",
                        status="reinforced",
                        turn=2,
                    ),
                ],
                unresolved=[
                    Unresolved(
                        text="What does `os.environ.get` return for missing keys?",
                        turn=3,
                    ),
                ],
            ),
            context_claims=[
                Claim(
                    text="Tests exist at `tests/test_app.py`",
                    status="new",
                    turn=1,
                ),
            ],
            evidence_history=[
                EvidenceRecord(
                    entity_key="file_path:README.md",
                    template_id="probe.file_repo_fact",
                    turn=1,
                ),
            ],
            posture="adversarial",
        )

        result = process_turn(req, ctx)
        assert isinstance(result, TurnPacketSuccess)
        assert result.schema_version == SCHEMA_VERSION
        assert result.status == "success"

        # Entities extracted from all three sources
        assert (
            len(result.entities) >= 3
        )  # At least app.py:42, config.yaml, os.environ.get

        # Path decisions for file entities (not symbols)
        assert len(result.path_decisions) >= 1
        pd_entity_ids = {pd.entity_id for pd in result.path_decisions}
        for entity in result.entities:
            if entity.tier == 1 and entity.type in (
                "file_loc",
                "file_path",
                "file_name",
            ):
                assert entity.id in pd_entity_ids

        # Budget reflects 1 prior evidence
        assert result.budget.evidence_count == 1
        assert result.budget.evidence_remaining == 4
        assert result.budget.scout_available is True

        # Template candidates exist for in-focus file entities
        assert len(result.template_candidates) >= 1

        # Deduped list is present (may be empty if no collisions)
        assert isinstance(result.deduped, list)

        # TurnRequest stored for Call 2
        ref = "conv_e2e:3"
        assert ref in ctx.store
        record = ctx.store[ref]
        assert record.turn_request is req
        assert record.used is False

    def test_empty_focus_produces_empty_success(self) -> None:
        """TurnRequest with no claims/unresolved → success with empty collections."""
        ctx = _make_ctx()
        req = _make_turn_request()

        result = process_turn(req, ctx)
        assert isinstance(result, TurnPacketSuccess)
        assert result.entities == []
        assert result.path_decisions == []
        assert result.template_candidates == []
        assert result.deduped == []
        assert result.budget.evidence_count == 0

    def test_multiple_entity_types_in_single_claim(self) -> None:
        """A single claim referencing both a file and a symbol produces both entity types."""
        ctx = _make_ctx(git_files={"src/app.py"})
        req = _make_turn_request(
            focus=Focus(
                text="debugging",
                claims=[
                    Claim(
                        text="The function `os.path.join` in `src/app.py` fails",
                        status="new",
                        turn=1,
                    ),
                ],
                unresolved=[],
            ),
        )

        result = process_turn(req, ctx)
        assert isinstance(result, TurnPacketSuccess)

        entity_types = {e.type for e in result.entities}
        # Should have at least a file_path and a symbol
        assert "file_path" in entity_types or "file_name" in entity_types
        assert "symbol" in entity_types

    def test_entity_ids_are_unique(self) -> None:
        """All entity IDs across the response are unique."""
        ctx = _make_ctx(git_files={"src/app.py", "config.yaml"})
        req = _make_turn_request(
            focus=Focus(
                text="multi-file",
                claims=[
                    Claim(
                        text="File `src/app.py` imports `config.yaml`",
                        status="new",
                        turn=1,
                    ),
                ],
                unresolved=[],
            ),
        )

        result = process_turn(req, ctx)
        assert isinstance(result, TurnPacketSuccess)

        entity_ids = [e.id for e in result.entities]
        assert len(entity_ids) == len(set(entity_ids))
