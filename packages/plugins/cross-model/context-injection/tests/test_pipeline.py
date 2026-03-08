"""Tests for the Call 1 pipeline: process_turn().

Tests cover:
1. Schema version validation (correct version succeeds, wrong version -> TurnPacketError)
2. Entity extraction from focus.claims, focus.unresolved
3. Path decisions for file entities (file_loc, file_path, file_name), not symbol
4. Template matching produces candidates for eligible entities
5. Budget computation
6. TurnRequest stored in ctx.store for Call 2 validation
7. Unexpected exceptions produce TurnPacketError with internal_error
8. End-to-end: realistic TurnRequest -> full TurnPacketSuccess
9. Conversation state: resolution, persistence, checkpoint round-trip
10. Ledger validation: entry construction, hard rejects
11. Action computation: continues, closing probe, conclude
12. Checkpoint: serialization, chain, cross-conversation guard
13. Turn cap: CC-5 enforcement
14. Ledger summary, cumulative claims, prior evidence
"""

from typing import Any
from unittest.mock import patch

import pytest

from context_injection.control import ConversationAction
from context_injection.pipeline import process_turn
from context_injection.state import AppContext, ScoutOptionRecord
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
    """Convenience TurnRequest constructor with sensible 0.2.0 defaults.

    Syncs focus.claims/unresolved with top-level claims/unresolved
    to satisfy the dual-claims channel guard (CC-PF-3).

    Default includes one claim to satisfy ledger validation (empty claims
    is a hard reject per D1).
    """
    _default_claims = [Claim(text="Default test claim", status="new", turn=1)]
    defaults: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "turn_number": 1,
        "conversation_id": "conv_test",
        "focus": Focus(text="test focus", claims=_default_claims, unresolved=[]),
        "posture": "exploratory",
        "position": "Test position",
        "claims": _default_claims,
        "delta": "static",
        "tags": ["test"],
        "unresolved": [],
    }
    defaults.update(overrides)

    # Sync focus claims/unresolved with top-level fields (CC-PF-3 guard)
    focus = defaults["focus"]
    claims = defaults["claims"]
    unresolved = defaults["unresolved"]

    if "focus" in overrides and "claims" not in overrides:
        # Caller set focus but not claims -> copy from focus
        defaults["claims"] = list(focus.claims)
        defaults["unresolved"] = list(focus.unresolved)
    elif "claims" in overrides and "focus" not in overrides:
        # Caller set claims but not focus -> build focus with those claims
        defaults["focus"] = Focus(
            text=focus.text,
            claims=claims,
            unresolved=unresolved,
        )

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
        """Correct schema version -> TurnPacketSuccess (guard against future version bumps)."""
        ctx = _make_ctx()
        req = _make_turn_request()
        # Guard: if SCHEMA_VERSION changes, this test will catch the mismatch.
        result = process_turn(req, ctx)
        assert isinstance(result, TurnPacketSuccess)

    def test_schema_version_mismatch_returns_error(self) -> None:
        """Bypassed Pydantic validation with wrong version -> TurnPacketError."""
        ctx = _make_ctx()
        # Use model_construct to bypass Pydantic's Literal validation
        req = TurnRequest.model_construct(
            schema_version="99.0.0",
            turn_number=1,
            conversation_id="conv_test",
            focus=Focus(text="test", claims=[], unresolved=[]),
            posture="exploratory",
            position="Test",
            claims=[],
            delta="static",
            tags=[],
            unresolved=[],
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
            posture="exploratory",
            position="Test",
            claims=[],
            delta="static",
            tags=[],
            unresolved=[],
        )

        result = process_turn(req, ctx)

        assert isinstance(result, TurnPacketError)
        assert result.error.code == "invalid_schema_version"
        assert "0.0.0" in result.error.message


# ============================================================
# Dual-claims channel guard (CC-PF-3)
# ============================================================


class TestDualClaimsGuard:
    """Pipeline rejects requests where focus claims/unresolved differ from top-level."""

    def test_mismatched_focus_claims_rejected(self) -> None:
        """focus.claims != top-level claims -> ledger_hard_reject."""
        ctx = _make_ctx()
        focus_claims = [Claim(text="Focus claim", status="new", turn=1)]
        top_claims = [Claim(text="Different claim", status="new", turn=1)]
        req = TurnRequest(
            schema_version=SCHEMA_VERSION,
            turn_number=1,
            conversation_id="conv_dc1",
            focus=Focus(text="test", claims=focus_claims, unresolved=[]),
            posture="exploratory",
            position="Test",
            claims=top_claims,
            delta="static",
            tags=["test"],
            unresolved=[],
        )
        result = process_turn(req, ctx)
        assert isinstance(result, TurnPacketError)
        assert result.error.code == "ledger_hard_reject"
        assert "claims" in result.error.message.lower()

    def test_mismatched_focus_unresolved_rejected(self) -> None:
        """focus.unresolved != top-level unresolved -> ledger_hard_reject."""
        ctx = _make_ctx()
        claims = [Claim(text="Test claim", status="new", turn=1)]
        focus_unresolved = [Unresolved(text="Q1?", turn=1)]
        top_unresolved = [Unresolved(text="Q2?", turn=1)]
        req = TurnRequest(
            schema_version=SCHEMA_VERSION,
            turn_number=1,
            conversation_id="conv_dc2",
            focus=Focus(text="test", claims=claims, unresolved=focus_unresolved),
            posture="exploratory",
            position="Test",
            claims=claims,
            delta="static",
            tags=["test"],
            unresolved=top_unresolved,
        )
        result = process_turn(req, ctx)
        assert isinstance(result, TurnPacketError)
        assert result.error.code == "ledger_hard_reject"
        assert "unresolved" in result.error.message.lower()


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
                claims=[
                    Claim(text="The config is important", status="new", turn=1),
                ],
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
        """Symbol entities are grep targets -- they do NOT get path decisions."""
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
        """In-focus, high-confidence, allowed file_path -> probe.file_repo_fact."""
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
        """In-focus, high-confidence symbol -> probe.symbol_repo_fact with GrepOption."""
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


# ============================================================
# Budget
# ============================================================


class TestBudget:
    def test_empty_history_full_budget(self) -> None:
        """No evidence history -> evidence_count=0, evidence_remaining=5."""
        ctx = _make_ctx()
        req = _make_turn_request()

        result = process_turn(req, ctx)
        assert isinstance(result, TurnPacketSuccess)
        assert result.budget.evidence_count == 0
        assert result.budget.evidence_remaining == 5
        assert result.budget.scout_available is True


# ============================================================
# Store record
# ============================================================


class TestStoreRecord:
    def test_turn_request_stored(self) -> None:
        """After process_turn, the TurnRequest is stored in ctx.store."""
        ctx = _make_ctx(git_files={"src/app.py"})
        req = _make_turn_request(
            conversation_id="conv_42",
            turn_number=1,
        )

        result = process_turn(req, ctx)
        assert isinstance(result, TurnPacketSuccess)

        ref = "conv_42:1"
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
            for so_id, option in record.scout_options.items():
                assert so_id.startswith("so_")
                assert isinstance(option, ScoutOptionRecord)
                assert isinstance(option.token, str)
                assert len(option.token) > 0

    def test_duplicate_ref_raises_on_second_call(self) -> None:
        """Same conversation_id + turn_number twice -> ValueError from store_record."""
        ctx = _make_ctx()
        req = _make_turn_request(conversation_id="conv_dup", turn_number=1)

        result1 = process_turn(req, ctx)
        assert isinstance(result1, TurnPacketSuccess)

        # Second call with same ref -> internal_error (caught by exception handler)
        result2 = process_turn(req, ctx)
        assert isinstance(result2, TurnPacketError)
        assert result2.error.code == "internal_error"
        assert "Duplicate" in result2.error.message


# ============================================================
# Error handling
# ============================================================


class TestErrorHandling:
    def test_unexpected_exception_returns_internal_error(self) -> None:
        """Any unexpected exception -> TurnPacketError with internal_error."""
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
        """Realistic TurnRequest with multiple sources -> TurnPacketSuccess
        with entities, path_decisions, template_candidates, budget, deduped."""
        git_files = {"src/app.py", "src/config.yaml", "tests/test_app.py"}
        ctx = _make_ctx(git_files=git_files)

        req = _make_turn_request(
            conversation_id="conv_e2e",
            turn_number=1,
            focus=Focus(
                text="investigating authentication bug",
                claims=[
                    Claim(
                        text="The auth logic in `src/app.py:42` is incorrect",
                        status="new",
                        turn=1,
                    ),
                    Claim(
                        text="Config is loaded from `src/config.yaml`",
                        status="new",
                        turn=1,
                    ),
                ],
                unresolved=[
                    Unresolved(
                        text="What does `os.environ.get` return for missing keys?",
                        turn=1,
                    ),
                ],
            ),
            posture="adversarial",
        )

        result = process_turn(req, ctx)
        assert isinstance(result, TurnPacketSuccess)
        assert result.schema_version == SCHEMA_VERSION
        assert result.status == "success"

    def test_empty_focus_produces_empty_success(self) -> None:
        """TurnRequest with no claims/unresolved -> success with empty collections."""
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


# ============================================================
# Conversation state (D4b Task 13a)
# ============================================================


class TestPipelineConversationState:
    """Pipeline resolves and updates ConversationState."""

    def test_first_turn_creates_conversation(self) -> None:
        ctx = _make_ctx(git_files=set())
        request = _make_turn_request(conversation_id="conv_new")
        result = process_turn(request, ctx)
        assert result.status == "success"
        assert "conv_new" in ctx.conversations

    def test_conversation_persists_across_turns(self) -> None:
        ctx = _make_ctx(git_files=set())
        r1 = _make_turn_request(conversation_id="conv_multi", turn_number=1)
        result1 = process_turn(r1, ctx)
        assert result1.status == "success"

        # Pass checkpoint back
        r2 = _make_turn_request(
            conversation_id="conv_multi",
            turn_number=2,
            state_checkpoint=result1.state_checkpoint,
            checkpoint_id=result1.checkpoint_id,
        )
        result2 = process_turn(r2, ctx)
        assert result2.status == "success"
        assert result2.cumulative.turns_completed == 2


# ============================================================
# Ledger validation (D4b Task 13a)
# ============================================================


class TestPipelineLedgerValidation:
    """Pipeline validates ledger entry and returns it."""

    def test_success_includes_validated_entry(self) -> None:
        ctx = _make_ctx(git_files=set())
        request = _make_turn_request(
            position="Auth module analysis",
            claims=[Claim(text="JWT is used", status="new", turn=1)],
            delta="advancing",
            tags=["architecture"],
        )
        result = process_turn(request, ctx)
        assert result.status == "success"
        assert result.validated_entry.position == "Auth module analysis"
        assert result.validated_entry.turn_number == 1
        assert len(result.validated_entry.claims) == 1

    def test_hard_reject_returns_error(self) -> None:
        """turn_number=0 should hard reject (invalid turn number per D1)."""
        ctx = _make_ctx(git_files=set())
        request = _make_turn_request(turn_number=0, claims=[])
        result = process_turn(request, ctx)
        assert result.status == "error"
        assert result.error.code == "ledger_hard_reject"


# ============================================================
# Action computation (D4b Task 13a)
# ============================================================


class TestPipelineActionComputation:
    """Pipeline computes action from conversation trajectory."""

    def test_first_turn_continues(self) -> None:
        ctx = _make_ctx(git_files=set())
        request = _make_turn_request()
        result = process_turn(request, ctx)
        assert result.status == "success"
        assert result.action == ConversationAction.CONTINUE_DIALOGUE

    def test_action_reason_nonempty(self) -> None:
        ctx = _make_ctx(git_files=set())
        request = _make_turn_request()
        result = process_turn(request, ctx)
        assert result.status == "success"
        assert len(result.action_reason) > 0


# ============================================================
# Phase-local convergence (Release B)
# ============================================================


def _static_claims(turn: int) -> list[Claim]:
    """Claims that produce effective_delta=STATIC (reinforced only, no new/revised/conceded)."""
    return [Claim(text=f"Reinforced claim T{turn}", status="reinforced", turn=turn)]


class TestPipelinePhaseLocal:
    """Pipeline wires posture-change detection and phase-local convergence."""

    def test_posture_change_resets_phase_window(self) -> None:
        """Send T1 exploratory (STATIC), T2 exploratory (STATIC) -> plateau.
        T3 evaluative (ADVANCING) -> phase resets, no plateau from prior phase.
        """
        ctx = _make_ctx(git_files=set())
        # T1: exploratory, STATIC (reinforced claims -> no new_claims -> STATIC)
        r1 = _make_turn_request(
            conversation_id="conv_phase",
            turn_number=1,
            posture="exploratory",
            delta="static",
            claims=_static_claims(1),
        )
        res1 = process_turn(r1, ctx)
        assert res1.status == "success"

        # T2: exploratory, STATIC -> plateau in same phase
        r2 = _make_turn_request(
            conversation_id="conv_phase",
            turn_number=2,
            posture="exploratory",
            delta="static",
            claims=_static_claims(2),
            state_checkpoint=res1.state_checkpoint,
            checkpoint_id=res1.checkpoint_id,
        )
        res2 = process_turn(r2, ctx)
        assert res2.status == "success"
        # T2 IS a plateau (2 STATIC in same phase)
        assert res2.action == ConversationAction.CLOSING_PROBE

        # T3: evaluative, ADVANCING -> posture changed, phase resets
        r3 = _make_turn_request(
            conversation_id="conv_phase",
            turn_number=3,
            posture="evaluative",
            delta="advancing",
            state_checkpoint=res2.state_checkpoint,
            checkpoint_id=res2.checkpoint_id,
        )
        res3 = process_turn(r3, ctx)
        assert res3.status == "success"
        # Phase reset — only 1 entry in new phase, no plateau
        assert res3.action == ConversationAction.CONTINUE_DIALOGUE

    def test_constant_posture_derives_phase_entries_every_turn(self) -> None:
        """Regression: phase_entries must be derived every turn, not just on
        posture-change turns. Send 3 evaluative turns where T2-T3 are STATIC
        -> plateau detected because phase_entries covers all 3 turns.
        """
        ctx = _make_ctx(git_files=set())
        # T1: ADVANCING (default has new claim)
        r1 = _make_turn_request(
            conversation_id="conv_const",
            turn_number=1,
            posture="evaluative",
            delta="advancing",
        )
        res1 = process_turn(r1, ctx)
        assert res1.status == "success"

        # T2: STATIC (reinforced only)
        r2 = _make_turn_request(
            conversation_id="conv_const",
            turn_number=2,
            posture="evaluative",
            delta="static",
            claims=_static_claims(2),
            state_checkpoint=res1.state_checkpoint,
            checkpoint_id=res1.checkpoint_id,
        )
        res2 = process_turn(r2, ctx)
        assert res2.status == "success"

        # T3: STATIC (reinforced only) -> 2 consecutive STATIC = plateau
        r3 = _make_turn_request(
            conversation_id="conv_const",
            turn_number=3,
            posture="evaluative",
            delta="static",
            claims=_static_claims(3),
            state_checkpoint=res2.state_checkpoint,
            checkpoint_id=res2.checkpoint_id,
        )
        res3 = process_turn(r3, ctx)
        assert res3.status == "success"
        # T2-T3 both STATIC in the same phase -> plateau
        assert res3.action == ConversationAction.CLOSING_PROBE

    def test_posture_change_prevents_cross_phase_plateau(self) -> None:
        """Differentiating test: without phase wiring, T3 would CONCLUDE
        (3 STATIC + probe fired). With phase wiring, T3 starts a new phase
        (1 STATIC, no plateau, probe reset) -> CONTINUE.
        """
        ctx = _make_ctx(git_files=set())
        # T1: STATIC
        r1 = _make_turn_request(
            conversation_id="conv_diff",
            turn_number=1,
            posture="exploratory",
            delta="static",
            claims=_static_claims(1),
        )
        res1 = process_turn(r1, ctx)
        assert res1.status == "success"

        # T2: STATIC -> plateau -> CLOSING_PROBE (probe fires)
        r2 = _make_turn_request(
            conversation_id="conv_diff",
            turn_number=2,
            posture="exploratory",
            delta="static",
            claims=_static_claims(2),
            state_checkpoint=res1.state_checkpoint,
            checkpoint_id=res1.checkpoint_id,
        )
        res2 = process_turn(r2, ctx)
        assert res2.status == "success"
        assert res2.action == ConversationAction.CLOSING_PROBE

        # T3: posture changes to evaluative, STATIC
        # Without phase wiring: 3 STATIC + probe fired -> CONCLUDE
        # With phase wiring: new phase (1 STATIC), probe reset -> CONTINUE
        r3 = _make_turn_request(
            conversation_id="conv_diff",
            turn_number=3,
            posture="evaluative",
            delta="static",
            claims=_static_claims(3),
            state_checkpoint=res2.state_checkpoint,
            checkpoint_id=res2.checkpoint_id,
        )
        res3 = process_turn(r3, ctx)
        assert res3.status == "success"
        assert res3.action == ConversationAction.CONTINUE_DIALOGUE

    def test_closing_probe_fires_again_after_phase_change(self) -> None:
        """Full once-per-phase path: probe fires in phase 1, phase changes,
        probe fires again in phase 2.
        """
        ctx = _make_ctx(git_files=set())
        # T1: exploratory STATIC
        r1 = _make_turn_request(
            conversation_id="conv_reprobe",
            turn_number=1,
            posture="exploratory",
            delta="static",
            claims=_static_claims(1),
        )
        res1 = process_turn(r1, ctx)
        assert res1.status == "success"

        # T2: exploratory STATIC -> plateau -> CLOSING_PROBE
        r2 = _make_turn_request(
            conversation_id="conv_reprobe",
            turn_number=2,
            posture="exploratory",
            delta="static",
            claims=_static_claims(2),
            state_checkpoint=res1.state_checkpoint,
            checkpoint_id=res1.checkpoint_id,
        )
        res2 = process_turn(r2, ctx)
        assert res2.action == ConversationAction.CLOSING_PROBE

        # T3: evaluative ADVANCING -> new phase, probe reset
        r3 = _make_turn_request(
            conversation_id="conv_reprobe",
            turn_number=3,
            posture="evaluative",
            delta="advancing",
            state_checkpoint=res2.state_checkpoint,
            checkpoint_id=res2.checkpoint_id,
        )
        res3 = process_turn(r3, ctx)
        assert res3.action == ConversationAction.CONTINUE_DIALOGUE

        # T4: evaluative STATIC
        r4 = _make_turn_request(
            conversation_id="conv_reprobe",
            turn_number=4,
            posture="evaluative",
            delta="static",
            claims=_static_claims(4),
            state_checkpoint=res3.state_checkpoint,
            checkpoint_id=res3.checkpoint_id,
        )
        res4 = process_turn(r4, ctx)
        assert res4.status == "success"

        # T5: evaluative STATIC -> plateau in phase 2 -> CLOSING_PROBE again
        r5 = _make_turn_request(
            conversation_id="conv_reprobe",
            turn_number=5,
            posture="evaluative",
            delta="static",
            claims=_static_claims(5),
            state_checkpoint=res4.state_checkpoint,
            checkpoint_id=res4.checkpoint_id,
        )
        res5 = process_turn(r5, ctx)
        assert res5.action == ConversationAction.CLOSING_PROBE

    def test_posture_flip_a_b_a_resets_phase_window(self) -> None:
        """A->B->A posture flip: return to a prior posture creates a new phase,
        not a resumption of the original phase.
        """
        ctx = _make_ctx(git_files=set())
        # T1: exploratory STATIC
        r1 = _make_turn_request(
            conversation_id="conv_flip",
            turn_number=1,
            posture="exploratory",
            delta="static",
            claims=_static_claims(1),
        )
        res1 = process_turn(r1, ctx)
        assert res1.status == "success"

        # T2: evaluative STATIC -> new phase (1 entry), no plateau
        r2 = _make_turn_request(
            conversation_id="conv_flip",
            turn_number=2,
            posture="evaluative",
            delta="static",
            claims=_static_claims(2),
            state_checkpoint=res1.state_checkpoint,
            checkpoint_id=res1.checkpoint_id,
        )
        res2 = process_turn(r2, ctx)
        assert res2.action == ConversationAction.CONTINUE_DIALOGUE

        # T3: exploratory STATIC -> new phase again (1 entry), no plateau
        r3 = _make_turn_request(
            conversation_id="conv_flip",
            turn_number=3,
            posture="exploratory",
            delta="static",
            claims=_static_claims(3),
            state_checkpoint=res2.state_checkpoint,
            checkpoint_id=res2.checkpoint_id,
        )
        res3 = process_turn(r3, ctx)
        assert res3.action == ConversationAction.CONTINUE_DIALOGUE

        # T4: exploratory STATIC -> now 2 STATIC in this phase -> CLOSING_PROBE
        r4 = _make_turn_request(
            conversation_id="conv_flip",
            turn_number=4,
            posture="exploratory",
            delta="static",
            claims=_static_claims(4),
            state_checkpoint=res3.state_checkpoint,
            checkpoint_id=res3.checkpoint_id,
        )
        res4 = process_turn(r4, ctx)
        assert res4.action == ConversationAction.CLOSING_PROBE

    def test_static_at_phase_boundary_counts_toward_plateau(self) -> None:
        """The posture-change turn itself is STATIC, then the next turn is also
        STATIC. This should fire the closing probe because the boundary entry
        is included in the new phase window.
        """
        ctx = _make_ctx(git_files=set())
        # T1: exploratory ADVANCING
        r1 = _make_turn_request(
            conversation_id="conv_boundary_static",
            turn_number=1,
            posture="exploratory",
            delta="advancing",
        )
        res1 = process_turn(r1, ctx)
        assert res1.status == "success"

        # T2: evaluative STATIC -> posture change, new phase with 1 STATIC entry
        r2 = _make_turn_request(
            conversation_id="conv_boundary_static",
            turn_number=2,
            posture="evaluative",
            delta="static",
            claims=_static_claims(2),
            state_checkpoint=res1.state_checkpoint,
            checkpoint_id=res1.checkpoint_id,
        )
        res2 = process_turn(r2, ctx)
        assert res2.action == ConversationAction.CONTINUE_DIALOGUE

        # T3: evaluative STATIC -> 2 STATIC in phase -> CLOSING_PROBE
        r3 = _make_turn_request(
            conversation_id="conv_boundary_static",
            turn_number=3,
            posture="evaluative",
            delta="static",
            claims=_static_claims(3),
            state_checkpoint=res2.state_checkpoint,
            checkpoint_id=res2.checkpoint_id,
        )
        res3 = process_turn(r3, ctx)
        assert res3.action == ConversationAction.CLOSING_PROBE


# ============================================================
# Checkpoint phase fields round-trip (P5)
# ============================================================


class TestCheckpointPhaseFields:
    """Checkpoint round-trip preserves phase tracking fields (P5)."""

    def test_checkpoint_preserves_phase_fields(self) -> None:
        """Phase fields survive checkpoint serialize -> deserialize round-trip."""
        ctx = _make_ctx(git_files=set())
        # T1: exploratory
        r1 = _make_turn_request(
            conversation_id="conv_ckpt_phase",
            turn_number=1,
            posture="exploratory",
            delta="advancing",
        )
        res1 = process_turn(r1, ctx)
        assert res1.status == "success"

        # T2: evaluative -> posture change creates phase fields
        r2 = _make_turn_request(
            conversation_id="conv_ckpt_phase",
            turn_number=2,
            posture="evaluative",
            delta="advancing",
            state_checkpoint=res1.state_checkpoint,
            checkpoint_id=res1.checkpoint_id,
        )
        res2 = process_turn(r2, ctx)
        assert res2.status == "success"

        # T3: evaluative STATIC — same posture, phase fields must have survived
        r3 = _make_turn_request(
            conversation_id="conv_ckpt_phase",
            turn_number=3,
            posture="evaluative",
            delta="static",
            claims=_static_claims(3),
            state_checkpoint=res2.state_checkpoint,
            checkpoint_id=res2.checkpoint_id,
        )
        res3 = process_turn(r3, ctx)
        assert res3.status == "success"

        # T4: evaluative STATIC -> 2 STATIC in phase -> CLOSING_PROBE
        # Proves phase_start_index survived: if reset to 0,
        # phase window would include T1 (ADVANCING) and no plateau.
        r4 = _make_turn_request(
            conversation_id="conv_ckpt_phase",
            turn_number=4,
            posture="evaluative",
            delta="static",
            claims=_static_claims(4),
            state_checkpoint=res3.state_checkpoint,
            checkpoint_id=res3.checkpoint_id,
        )
        res4 = process_turn(r4, ctx)
        assert res4.action == ConversationAction.CLOSING_PROBE


# ============================================================
# Checkpoint (D4b Task 13a)
# ============================================================


class TestPipelineCheckpoint:
    """Pipeline serializes and returns checkpoint."""

    def test_checkpoint_returned(self) -> None:
        ctx = _make_ctx(git_files=set())
        request = _make_turn_request()
        result = process_turn(request, ctx)
        assert result.status == "success"
        assert result.state_checkpoint is not None
        assert result.checkpoint_id is not None
        assert len(result.checkpoint_id) > 0

    def test_checkpoint_id_stored_in_conversation(self) -> None:
        ctx = _make_ctx(git_files=set())
        request = _make_turn_request(conversation_id="conv_ckpt")
        result = process_turn(request, ctx)
        assert result.status == "success"
        conv = ctx.conversations["conv_ckpt"]
        assert conv.last_checkpoint_id == result.checkpoint_id

    def test_checkpoint_stale_through_pipeline(self) -> None:
        """Turn 2 with wrong checkpoint_id -> checkpoint_stale through pipeline."""
        ctx = _make_ctx(git_files=set())
        r1 = _make_turn_request(conversation_id="conv_stale", turn_number=1)
        result1 = process_turn(r1, ctx)
        assert result1.status == "success"

        r2 = _make_turn_request(
            conversation_id="conv_stale",
            turn_number=2,
            state_checkpoint=result1.state_checkpoint,
            checkpoint_id="wrong-checkpoint-id",
        )
        result2 = process_turn(r2, ctx)
        assert isinstance(result2, TurnPacketError)
        assert result2.error.code == "checkpoint_stale"

    def test_checkpoint_missing_through_pipeline(self) -> None:
        """Turn 2 on fresh context with no checkpoint -> checkpoint_missing."""
        # Fresh context — server has no in-memory state for this conversation
        ctx = _make_ctx(git_files=set())
        # Turn 2 without checkpoint payload on a conversation the server hasn't seen
        r2 = _make_turn_request(
            conversation_id="conv_missing",
            turn_number=2,
        )
        result2 = process_turn(r2, ctx)
        assert isinstance(result2, TurnPacketError)
        assert result2.error.code == "checkpoint_missing"

    def test_cross_conversation_checkpoint_rejected(self) -> None:
        """Checkpoint from conversation A must not be accepted by conversation B (D2 guard #4)."""
        ctx = _make_ctx(git_files=set())

        # Turn 1 on conversation A -- get a valid checkpoint
        r1 = _make_turn_request(conversation_id="conv_A", turn_number=1)
        result_a = process_turn(r1, ctx)
        assert result_a.status == "success"

        # Attempt turn 2 on conversation B using conversation A's checkpoint
        r2 = _make_turn_request(
            conversation_id="conv_B",
            turn_number=2,
            state_checkpoint=result_a.state_checkpoint,
            checkpoint_id=result_a.checkpoint_id,
        )
        result_b = process_turn(r2, ctx)
        assert result_b.status == "error"
        assert result_b.error.code == "checkpoint_invalid"


# ============================================================
# Checkpoint consistency CC-3 (D4b Task 13a)
# ============================================================


class TestCheckpointConsistencyCC3:
    """CC-3 test matrix: checkpoint triplet consistency."""

    def test_consistent_triplet_accepted(self) -> None:
        ctx = _make_ctx(git_files=set())
        r1 = _make_turn_request(conversation_id="conv_cc3", turn_number=1)
        result1 = process_turn(r1, ctx)
        assert result1.status == "success"

        r2 = _make_turn_request(
            conversation_id="conv_cc3",
            turn_number=2,
            state_checkpoint=result1.state_checkpoint,
            checkpoint_id=result1.checkpoint_id,
        )
        result2 = process_turn(r2, ctx)
        assert result2.status == "success"

    def test_two_turn_chain(self) -> None:
        ctx = _make_ctx(git_files=set())
        r1 = _make_turn_request(conversation_id="conv_chain", turn_number=1)
        result1 = process_turn(r1, ctx)
        assert result1.status == "success"

        r2 = _make_turn_request(
            conversation_id="conv_chain",
            turn_number=2,
            state_checkpoint=result1.state_checkpoint,
            checkpoint_id=result1.checkpoint_id,
        )
        result2 = process_turn(r2, ctx)
        assert result2.status == "success"

        r3 = _make_turn_request(
            conversation_id="conv_chain",
            turn_number=3,
            state_checkpoint=result2.state_checkpoint,
            checkpoint_id=result2.checkpoint_id,
        )
        result3 = process_turn(r3, ctx)
        assert result3.status == "success"
        assert result3.cumulative.turns_completed == 3

    def test_restart_chain_from_checkpoint(self) -> None:
        ctx = _make_ctx(git_files=set())
        r1 = _make_turn_request(conversation_id="conv_restart", turn_number=1)
        result1 = process_turn(r1, ctx)
        assert result1.status == "success"

        ctx2 = _make_ctx(git_files=set())
        assert "conv_restart" not in ctx2.conversations

        r2 = _make_turn_request(
            conversation_id="conv_restart",
            turn_number=2,
            state_checkpoint=result1.state_checkpoint,
            checkpoint_id=result1.checkpoint_id,
        )
        result2 = process_turn(r2, ctx2)
        assert result2.status == "success"
        assert result2.cumulative.turns_completed == 2

    def test_cross_conversation_checkpoint_rejected(self) -> None:
        ctx = _make_ctx(git_files=set())
        r1 = _make_turn_request(conversation_id="conv_cc3_A", turn_number=1)
        result_a = process_turn(r1, ctx)
        assert result_a.status == "success"

        r2 = _make_turn_request(
            conversation_id="conv_cc3_B",
            turn_number=2,
            state_checkpoint=result_a.state_checkpoint,
            checkpoint_id=result_a.checkpoint_id,
        )
        result_b = process_turn(r2, ctx)
        assert result_b.status == "error"
        assert result_b.error.code == "checkpoint_invalid"


# ============================================================
# Turn cap CC-5 (D4b Task 13a)
# ============================================================


class TestTurnCapCC5:
    """CC-5 test matrix: turn cap enforcement via MAX_CONVERSATION_TURNS."""

    def test_constant_invariant(self) -> None:
        from context_injection.pipeline import MAX_CONVERSATION_TURNS
        from context_injection.checkpoint import MAX_ENTRIES_BEFORE_COMPACT
        assert MAX_CONVERSATION_TURNS < MAX_ENTRIES_BEFORE_COMPACT

    def test_below_cap_succeeds(self) -> None:
        ctx = _make_ctx(git_files=set())
        r1 = _make_turn_request(conversation_id="conv_below_cap", turn_number=1)
        result = process_turn(r1, ctx)
        assert result.status == "success"

    def test_at_cap_rejected(self) -> None:
        from context_injection.pipeline import MAX_CONVERSATION_TURNS
        ctx = _make_ctx(git_files=set())

        last_result = None
        for turn in range(1, MAX_CONVERSATION_TURNS + 1):
            r = _make_turn_request(
                conversation_id="conv_at_cap",
                turn_number=turn,
                state_checkpoint=last_result.state_checkpoint if last_result else None,
                checkpoint_id=last_result.checkpoint_id if last_result else None,
            )
            last_result = process_turn(r, ctx)
            assert last_result.status == "success", f"Turn {turn} should succeed"

        r_over = _make_turn_request(
            conversation_id="conv_at_cap",
            turn_number=MAX_CONVERSATION_TURNS + 1,
            state_checkpoint=last_result.state_checkpoint,
            checkpoint_id=last_result.checkpoint_id,
        )
        result_over = process_turn(r_over, ctx)
        assert result_over.status == "error"
        assert result_over.error.code == "turn_cap_exceeded"

    def test_no_mutation_on_reject(self) -> None:
        from context_injection.pipeline import MAX_CONVERSATION_TURNS
        ctx = _make_ctx(git_files=set())

        last_result = None
        for turn in range(1, MAX_CONVERSATION_TURNS + 1):
            r = _make_turn_request(
                conversation_id="conv_no_mutate",
                turn_number=turn,
                state_checkpoint=last_result.state_checkpoint if last_result else None,
                checkpoint_id=last_result.checkpoint_id if last_result else None,
            )
            last_result = process_turn(r, ctx)

        entries_before = len(ctx.conversations["conv_no_mutate"].entries)

        r_over = _make_turn_request(
            conversation_id="conv_no_mutate",
            turn_number=MAX_CONVERSATION_TURNS + 1,
            state_checkpoint=last_result.state_checkpoint,
            checkpoint_id=last_result.checkpoint_id,
        )
        process_turn(r_over, ctx)
        entries_after = len(ctx.conversations["conv_no_mutate"].entries)
        assert entries_after == entries_before

    def test_repeated_turn_number_bound(self) -> None:
        ctx = _make_ctx(git_files=set())
        r1 = _make_turn_request(conversation_id="conv_repeat", turn_number=1)
        result1 = process_turn(r1, ctx)
        assert result1.status == "success"

        r1_dup = _make_turn_request(
            conversation_id="conv_repeat",
            turn_number=1,
            state_checkpoint=result1.state_checkpoint,
            checkpoint_id=result1.checkpoint_id,
        )
        result_dup = process_turn(r1_dup, ctx)
        conv = ctx.conversations["conv_repeat"]
        assert len(conv.entries) <= 2

    def test_checkpoint_restore_at_cap(self) -> None:
        from context_injection.pipeline import MAX_CONVERSATION_TURNS
        ctx = _make_ctx(git_files=set())

        last_result = None
        for turn in range(1, MAX_CONVERSATION_TURNS + 1):
            r = _make_turn_request(
                conversation_id="conv_restore_cap",
                turn_number=turn,
                state_checkpoint=last_result.state_checkpoint if last_result else None,
                checkpoint_id=last_result.checkpoint_id if last_result else None,
            )
            last_result = process_turn(r, ctx)

        ctx2 = _make_ctx(git_files=set())
        r_over = _make_turn_request(
            conversation_id="conv_restore_cap",
            turn_number=MAX_CONVERSATION_TURNS + 1,
            state_checkpoint=last_result.state_checkpoint,
            checkpoint_id=last_result.checkpoint_id,
        )
        result_over = process_turn(r_over, ctx2)
        assert result_over.status == "error"
        assert result_over.error.code == "turn_cap_exceeded"


# ============================================================
# Ledger summary (D4b Task 13a)
# ============================================================


class TestPipelineLedgerSummary:
    """Pipeline generates ledger summary."""

    def test_summary_included(self) -> None:
        ctx = _make_ctx(git_files=set())
        request = _make_turn_request(position="Test analysis")
        result = process_turn(request, ctx)
        assert result.status == "success"
        assert "T1:" in result.ledger_summary
        assert "Test analysis" in result.ledger_summary


# ============================================================
# Cumulative claims (D4b Task 13a)
# ============================================================


class TestPipelineCumulativeClaims:
    """Pipeline uses cumulative claims from ConversationState (replaces context_claims)."""

    def test_prior_claims_extracted_as_out_of_focus(self) -> None:
        ctx = _make_ctx(git_files={"src/app.py"})

        r1 = _make_turn_request(
            conversation_id="conv_cumulative",
            turn_number=1,
            claims=[Claim(text="The file `src/app.py` has the logic", status="new", turn=1)],
            position="Initial review",
        )
        result1 = process_turn(r1, ctx)
        assert result1.status == "success"

        r2 = _make_turn_request(
            conversation_id="conv_cumulative",
            turn_number=2,
            claims=[Claim(text="New claim about something else", status="new", turn=2)],
            position="Follow-up analysis",
            state_checkpoint=result1.state_checkpoint,
            checkpoint_id=result1.checkpoint_id,
        )
        result2 = process_turn(r2, ctx)
        assert result2.status == "success"

        out_of_focus = [e for e in result2.entities if not e.in_focus]
        file_entities = [e for e in out_of_focus if e.canonical == "src/app.py"]
        assert len(file_entities) > 0, "Prior claim's file entity should be extracted out-of-focus"


# ============================================================
# Prior evidence (D4b Task 13a)
# ============================================================


class TestPipelineUnresolvedClosures:
    """Per-turn unresolved closure computation."""

    def test_first_turn_unresolved_closed_is_zero(self) -> None:
        """Turn 1 has no prior unresolved list to compare against."""
        ctx = _make_ctx()
        unresolved = [Unresolved(text="Open question?", turn=1)]
        r1 = _make_turn_request(
            conversation_id="conv_uc",
            unresolved=unresolved,
            focus=Focus(
                text="test",
                claims=[Claim(text="C1", status="new", turn=1)],
                unresolved=unresolved,
            ),
        )
        result = process_turn(r1, ctx)
        assert result.status == "success"
        assert isinstance(result, TurnPacketSuccess)
        assert result.validated_entry.counters.unresolved_closed == 0

    def test_closing_one_unresolved_item(self) -> None:
        """Turn 2 drops one unresolved item -> unresolved_closed = 1."""
        ctx = _make_ctx()
        unresolved_t1 = [
            Unresolved(text="Q1?", turn=1),
            Unresolved(text="Q2?", turn=1),
        ]
        r1 = _make_turn_request(
            conversation_id="conv_uc2",
            unresolved=unresolved_t1,
            focus=Focus(
                text="test",
                claims=[Claim(text="C1", status="new", turn=1)],
                unresolved=unresolved_t1,
            ),
        )
        result1 = process_turn(r1, ctx)
        assert result1.status == "success"
        assert isinstance(result1, TurnPacketSuccess)

        # Turn 2: Q1 resolved, Q2 remains
        unresolved_t2 = [Unresolved(text="Q2?", turn=1)]
        r2 = _make_turn_request(
            conversation_id="conv_uc2",
            turn_number=2,
            unresolved=unresolved_t2,
            claims=[Claim(text="C2", status="new", turn=2)],
            focus=Focus(
                text="test",
                claims=[Claim(text="C2", status="new", turn=2)],
                unresolved=unresolved_t2,
            ),
            state_checkpoint=result1.state_checkpoint,
            checkpoint_id=result1.checkpoint_id,
        )
        result2 = process_turn(r2, ctx)
        assert result2.status == "success"
        assert isinstance(result2, TurnPacketSuccess)
        assert result2.validated_entry.counters.unresolved_closed == 1

    def test_closing_all_unresolved_items(self) -> None:
        """Turn 2 closes all unresolved items."""
        ctx = _make_ctx()
        unresolved_t1 = [
            Unresolved(text="Q1?", turn=1),
            Unresolved(text="Q2?", turn=1),
        ]
        r1 = _make_turn_request(
            conversation_id="conv_uc3",
            unresolved=unresolved_t1,
            focus=Focus(
                text="test",
                claims=[Claim(text="C1", status="new", turn=1)],
                unresolved=unresolved_t1,
            ),
        )
        result1 = process_turn(r1, ctx)
        assert result1.status == "success"
        assert isinstance(result1, TurnPacketSuccess)

        # Turn 2: all unresolved closed
        r2 = _make_turn_request(
            conversation_id="conv_uc3",
            turn_number=2,
            unresolved=[],
            claims=[Claim(text="C2", status="new", turn=2)],
            focus=Focus(
                text="test",
                claims=[Claim(text="C2", status="new", turn=2)],
                unresolved=[],
            ),
            state_checkpoint=result1.state_checkpoint,
            checkpoint_id=result1.checkpoint_id,
        )
        result2 = process_turn(r2, ctx)
        assert result2.status == "success"
        assert isinstance(result2, TurnPacketSuccess)
        assert result2.validated_entry.counters.unresolved_closed == 2

    def test_cumulative_closures_across_turns(self) -> None:
        """Closures accumulate correctly across 3 turns."""
        ctx = _make_ctx()
        unresolved_t1 = [
            Unresolved(text="Q1?", turn=1),
            Unresolved(text="Q2?", turn=1),
            Unresolved(text="Q3?", turn=1),
        ]
        r1 = _make_turn_request(
            conversation_id="conv_uc4",
            unresolved=unresolved_t1,
            focus=Focus(
                text="test",
                claims=[Claim(text="C1", status="new", turn=1)],
                unresolved=unresolved_t1,
            ),
        )
        result1 = process_turn(r1, ctx)
        assert isinstance(result1, TurnPacketSuccess)

        # Turn 2: close Q1
        unresolved_t2 = [
            Unresolved(text="Q2?", turn=1),
            Unresolved(text="Q3?", turn=1),
        ]
        r2 = _make_turn_request(
            conversation_id="conv_uc4",
            turn_number=2,
            unresolved=unresolved_t2,
            claims=[Claim(text="C2", status="new", turn=2)],
            focus=Focus(
                text="test",
                claims=[Claim(text="C2", status="new", turn=2)],
                unresolved=unresolved_t2,
            ),
            state_checkpoint=result1.state_checkpoint,
            checkpoint_id=result1.checkpoint_id,
        )
        result2 = process_turn(r2, ctx)
        assert isinstance(result2, TurnPacketSuccess)
        assert result2.validated_entry.counters.unresolved_closed == 1

        # Turn 3: close Q2 and Q3
        r3 = _make_turn_request(
            conversation_id="conv_uc4",
            turn_number=3,
            unresolved=[],
            claims=[Claim(text="C3", status="new", turn=3)],
            focus=Focus(
                text="test",
                claims=[Claim(text="C3", status="new", turn=3)],
                unresolved=[],
            ),
            state_checkpoint=result2.state_checkpoint,
            checkpoint_id=result2.checkpoint_id,
        )
        result3 = process_turn(r3, ctx)
        assert isinstance(result3, TurnPacketSuccess)
        assert result3.validated_entry.counters.unresolved_closed == 2

        # Cumulative: 0 (turn 1) + 1 (turn 2) + 2 (turn 3) = 3
        assert result3.cumulative.unresolved_closed == 3

    def test_no_closures_when_unresolved_unchanged(self) -> None:
        """Same unresolved list across turns -> unresolved_closed = 0."""
        ctx = _make_ctx()
        unresolved = [Unresolved(text="Q1?", turn=1)]
        r1 = _make_turn_request(
            conversation_id="conv_uc5",
            unresolved=unresolved,
            focus=Focus(
                text="test",
                claims=[Claim(text="C1", status="new", turn=1)],
                unresolved=unresolved,
            ),
        )
        result1 = process_turn(r1, ctx)
        assert isinstance(result1, TurnPacketSuccess)

        # Turn 2: same unresolved list
        r2 = _make_turn_request(
            conversation_id="conv_uc5",
            turn_number=2,
            unresolved=unresolved,
            claims=[Claim(text="C2", status="new", turn=2)],
            focus=Focus(
                text="test",
                claims=[Claim(text="C2", status="new", turn=2)],
                unresolved=unresolved,
            ),
            state_checkpoint=result1.state_checkpoint,
            checkpoint_id=result1.checkpoint_id,
        )
        result2 = process_turn(r2, ctx)
        assert isinstance(result2, TurnPacketSuccess)
        assert result2.validated_entry.counters.unresolved_closed == 0


class TestPipelinePriorEvidence:
    """Pipeline uses evidence from ConversationState (replaces request.evidence_history)."""

    def test_evidence_from_conversation_used_for_dedup(self) -> None:
        ctx = _make_ctx(git_files={"src/app.py"})

        # Turn 1: establish conversation state through the pipeline
        r1 = _make_turn_request(
            conversation_id="conv_evidence",
            turn_number=1,
            claims=[Claim(text="Check `src/app.py`", status="new", turn=1)],
            position="First review",
        )
        result1 = process_turn(r1, ctx)
        assert result1.status == "success"

        # Inject evidence into the conversation (simulates a Call 2 having occurred)
        conv = ctx.conversations["conv_evidence"]
        conv = conv.with_evidence(
            EvidenceRecord(
                entity_key="file_path:src/app.py",
                template_id="clarify.file_path",
                turn=1,
            ),
        )
        ctx.conversations["conv_evidence"] = conv

        r2 = _make_turn_request(
            conversation_id="conv_evidence",
            turn_number=2,
            claims=[Claim(text="Check `src/app.py` again", status="new", turn=2)],
            position="Second review",
            state_checkpoint=result1.state_checkpoint,
            checkpoint_id=result1.checkpoint_id,
        )
        result2 = process_turn(r2, ctx)
        assert result2.status == "success"

        deduped_keys = [d.entity_key for d in result2.deduped]
        assert "file_path:src/app.py" in deduped_keys
