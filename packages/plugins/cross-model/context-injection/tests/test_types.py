"""Tests for protocol Pydantic models."""

from typing import get_args

import pytest
from pydantic import TypeAdapter, ValidationError

from context_injection.enums import EffectiveDelta, QualityLabel
from context_injection.types import (
    SCHEMA_VERSION,
    Budget,
    Claim,
    Clarifier,
    CumulativeState,
    DedupRecord,
    Entity,
    ErrorDetail,
    Focus,
    GrepOption,
    GrepSpec,
    LedgerEntry,
    LedgerEntryCounters,
    PathDecision,
    ReadOption,
    ReadResult,
    ReadSpec,
    SchemaVersionLiteral,
    ScoutResult,
    ScoutResultFailure,
    ScoutResultInvalid,
    ScoutResultSuccess,
    ScoutSpec,
    TemplateCandidate,
    TurnPacket,
    TurnPacketError,
    TurnPacketSuccess,
    TurnRequest,
    Unresolved,
)


# --- Shared test helpers ---


def _minimal_ledger_entry() -> LedgerEntry:
    """Minimal valid LedgerEntry for use in TurnPacketSuccess tests."""
    return LedgerEntry(
        position="Test position",
        claims=[Claim(text="test claim", status="new", turn=1)],
        delta="static",
        tags=["test"],
        unresolved=[],
        counters=LedgerEntryCounters(
            new_claims=1, revised=0, conceded=0, unresolved_closed=0,
        ),
        quality=QualityLabel.SUBSTANTIVE,
        effective_delta=EffectiveDelta.STATIC,
        turn_number=1,
    )


def _minimal_cumulative() -> CumulativeState:
    """Minimal valid CumulativeState for use in TurnPacketSuccess tests."""
    return CumulativeState(
        total_claims=1,
        reinforced=0,
        revised=0,
        conceded=0,
        unresolved_open=0,
        unresolved_closed=0,
        turns_completed=1,
        effective_delta_sequence=[EffectiveDelta.STATIC],
    )


class TestProtocolModel:
    """ProtocolModel base enforces extra=forbid, strict=True, frozen=True."""

    def test_rejects_extra_fields(self) -> None:
        with pytest.raises(ValidationError, match="extra_forbidden"):
            Claim(text="test", status="new", turn=1, bogus="field")

    def test_rejects_type_coercion(self) -> None:
        """strict=True means string '1' is not coerced to int."""
        with pytest.raises(ValidationError):
            Claim(text="test", status="new", turn="1")  # type: ignore[arg-type]

    def test_frozen_immutability(self) -> None:
        claim = Claim(text="test", status="new", turn=1)
        with pytest.raises(ValidationError):
            claim.text = "modified"  # type: ignore[misc]


class TestClaim:
    def test_valid_claim(self) -> None:
        c = Claim(text="The project uses YAML", status="new", turn=3)
        assert c.text == "The project uses YAML"
        assert c.status == "new"
        assert c.turn == 3

    def test_all_statuses(self) -> None:
        for status in ("new", "reinforced", "revised", "conceded"):
            c = Claim(text="claim", status=status, turn=1)
            assert c.status == status


class TestFocus:
    def test_valid_focus(self) -> None:
        f = Focus(
            text="Config format question",
            claims=[Claim(text="Uses YAML", status="new", turn=1)],
            unresolved=[Unresolved(text="Are there overrides?", turn=1)],
        )
        assert len(f.claims) == 1
        assert len(f.unresolved) == 1

    def test_empty_claims_and_unresolved(self) -> None:
        f = Focus(text="Empty focus", claims=[], unresolved=[])
        assert f.claims == []
        assert f.unresolved == []


class TestTurnRequest:
    def test_parse_contract_example(self) -> None:
        """Parse a 0.2.0 contract example with ledger fields."""
        data = {
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
            "posture": "evaluative",
            "position": "YAML is the primary config format",
            "claims": [
                {"text": "Uses YAML", "status": "new", "turn": 3},
            ],
            "delta": "advancing",
            "tags": ["config"],
            "unresolved": [
                {"text": "Are there environment overrides?", "turn": 3},
            ],
        }
        req = TurnRequest.model_validate(data)
        assert req.turn_number == 3
        assert req.conversation_id == "conv_abc123"
        assert len(req.focus.claims) == 2
        assert req.posture == "evaluative"
        assert req.position == "YAML is the primary config format"
        assert req.delta == "advancing"
        assert len(req.claims) == 1
        assert req.tags == ["config"]
        assert len(req.unresolved) == 1

    def test_wrong_schema_version_rejected(self) -> None:
        """Pydantic strict Literal rejects wrong version."""
        data = {
            "schema_version": "0.3.0",
            "turn_number": 1,
            "conversation_id": "conv_1",
            "focus": {"text": "test", "claims": [], "unresolved": []},
            "posture": "exploratory",
            "position": "test",
            "claims": [{"text": "c", "status": "new", "turn": 1}],
            "delta": "static",
            "tags": [],
            "unresolved": [],
        }
        with pytest.raises(ValidationError):
            TurnRequest.model_validate(data)

    def test_checkpoint_fields_optional(self) -> None:
        """state_checkpoint and checkpoint_id default to None."""
        data = {
            "schema_version": SCHEMA_VERSION,
            "turn_number": 1,
            "conversation_id": "conv_1",
            "focus": {"text": "test", "claims": [], "unresolved": []},
            "posture": "exploratory",
            "position": "test",
            "claims": [{"text": "c", "status": "new", "turn": 1}],
            "delta": "static",
            "tags": [],
            "unresolved": [],
        }
        req = TurnRequest.model_validate(data)
        assert req.state_checkpoint is None
        assert req.checkpoint_id is None


class TestTurnRequest020:
    """0.2.0 TurnRequest schema: new required fields, removed fields."""

    def test_new_required_fields_present(self) -> None:
        """All new 0.2.0 required fields are accepted."""
        req = TurnRequest(
            schema_version=SCHEMA_VERSION,
            turn_number=1,
            conversation_id="conv_1",
            focus=Focus(text="test", claims=[], unresolved=[]),
            posture="exploratory",
            position="Test position",
            claims=[Claim(text="c", status="new", turn=1)],
            delta="advancing",
            tags=["t1"],
            unresolved=[Unresolved(text="q?", turn=1)],
        )
        assert req.position == "Test position"
        assert req.delta == "advancing"
        assert req.tags == ["t1"]
        assert len(req.claims) == 1
        assert len(req.unresolved) == 1

    def test_checkpoint_fields_optional_absent(self) -> None:
        """Checkpoint fields default to None when absent."""
        req = TurnRequest(
            schema_version=SCHEMA_VERSION,
            turn_number=1,
            conversation_id="conv_1",
            focus=Focus(text="test", claims=[], unresolved=[]),
            posture="exploratory",
            position="p",
            claims=[Claim(text="c", status="new", turn=1)],
            delta="static",
            tags=[],
            unresolved=[],
        )
        assert req.state_checkpoint is None
        assert req.checkpoint_id is None

    def test_checkpoint_fields_set(self) -> None:
        """Checkpoint fields can be explicitly set."""
        req = TurnRequest(
            schema_version=SCHEMA_VERSION,
            turn_number=2,
            conversation_id="conv_1",
            focus=Focus(text="test", claims=[], unresolved=[]),
            posture="exploratory",
            position="p",
            claims=[Claim(text="c", status="new", turn=2)],
            delta="advancing",
            tags=[],
            unresolved=[],
            state_checkpoint="base64data==",
            checkpoint_id="cp_abc123",
        )
        assert req.state_checkpoint == "base64data=="
        assert req.checkpoint_id == "cp_abc123"

    def test_context_claims_removed(self) -> None:
        """context_claims is no longer accepted (extra=forbid)."""
        data = {
            "schema_version": SCHEMA_VERSION,
            "turn_number": 1,
            "conversation_id": "conv_1",
            "focus": {"text": "test", "claims": [], "unresolved": []},
            "posture": "exploratory",
            "position": "p",
            "claims": [{"text": "c", "status": "new", "turn": 1}],
            "delta": "static",
            "tags": [],
            "unresolved": [],
            "context_claims": [],
        }
        with pytest.raises(ValidationError, match="extra_forbidden"):
            TurnRequest.model_validate(data)

    def test_evidence_history_removed(self) -> None:
        """evidence_history is no longer accepted (extra=forbid)."""
        data = {
            "schema_version": SCHEMA_VERSION,
            "turn_number": 1,
            "conversation_id": "conv_1",
            "focus": {"text": "test", "claims": [], "unresolved": []},
            "posture": "exploratory",
            "position": "p",
            "claims": [{"text": "c", "status": "new", "turn": 1}],
            "delta": "static",
            "tags": [],
            "unresolved": [],
            "evidence_history": [],
        }
        with pytest.raises(ValidationError, match="extra_forbidden"):
            TurnRequest.model_validate(data)

    def test_invalid_delta_rejected(self) -> None:
        """delta must be one of advancing/shifting/static."""
        data = {
            "schema_version": SCHEMA_VERSION,
            "turn_number": 1,
            "conversation_id": "conv_1",
            "focus": {"text": "test", "claims": [], "unresolved": []},
            "posture": "exploratory",
            "position": "p",
            "claims": [{"text": "c", "status": "new", "turn": 1}],
            "delta": "regressing",
            "tags": [],
            "unresolved": [],
        }
        with pytest.raises(ValidationError):
            TurnRequest.model_validate(data)


class TestTurnPacketSuccess020:
    """0.2.0 TurnPacketSuccess: new fields present."""

    def test_new_fields_present(self) -> None:
        """All new 0.2.0 fields are accepted and stored."""
        entry = _minimal_ledger_entry()
        cumulative = _minimal_cumulative()
        pkt = TurnPacketSuccess(
            schema_version=SCHEMA_VERSION,
            status="success",
            entities=[],
            path_decisions=[],
            template_candidates=[],
            budget=Budget(
                evidence_count=0, evidence_remaining=5,
                scout_available=True, budget_status="under_budget",
            ),
            deduped=[],
            validated_entry=entry,
            warnings=[],
            cumulative=cumulative,
            action="continue_dialogue",
            action_reason="No plateau",
            ledger_summary="T1: Test (static, test)",
            state_checkpoint="base64==",
            checkpoint_id="cp_001",
        )
        assert pkt.validated_entry is entry
        assert pkt.warnings == []
        assert pkt.cumulative is cumulative
        assert pkt.action == "continue_dialogue"
        assert pkt.action_reason == "No plateau"
        assert pkt.ledger_summary == "T1: Test (static, test)"
        assert pkt.state_checkpoint == "base64=="
        assert pkt.checkpoint_id == "cp_001"


class TestTurnPacketCheckpointRequired:
    """0.2.0 TurnPacketSuccess requires checkpoint fields."""

    def test_checkpoint_fields_required(self) -> None:
        """state_checkpoint and checkpoint_id are required on TurnPacketSuccess."""
        with pytest.raises(ValidationError):
            TurnPacketSuccess(
                schema_version=SCHEMA_VERSION,
                status="success",
                entities=[],
                path_decisions=[],
                template_candidates=[],
                budget=Budget(
                    evidence_count=0, evidence_remaining=5,
                    scout_available=True, budget_status="under_budget",
                ),
                deduped=[],
                validated_entry=_minimal_ledger_entry(),
                warnings=[],
                cumulative=_minimal_cumulative(),
                action="continue_dialogue",
                action_reason="test",
                ledger_summary="test",
                # state_checkpoint and checkpoint_id omitted
            )


class TestErrorDetail020:
    """0.2.0 ErrorDetail: new error codes."""

    def test_new_error_codes_accepted(self) -> None:
        """New 0.2.0 error codes are valid."""
        new_codes = [
            "ledger_hard_reject",
            "checkpoint_missing",
            "checkpoint_invalid",
            "checkpoint_stale",
            "turn_cap_exceeded",
        ]
        for code in new_codes:
            err = ErrorDetail(code=code, message=f"Test {code}")
            assert err.code == code

    def test_existing_codes_still_work(self) -> None:
        """Original error codes remain valid."""
        original_codes = [
            "invalid_schema_version",
            "missing_required_field",
            "malformed_json",
            "internal_error",
        ]
        for code in original_codes:
            err = ErrorDetail(code=code, message=f"Test {code}")
            assert err.code == code


class TestSchemaVersion020:
    """0.2.0 schema version constant and validation."""

    def test_version_constant(self) -> None:
        """SCHEMA_VERSION is '0.2.0'."""
        assert SCHEMA_VERSION == "0.2.0"

    def test_valid_version_accepted(self) -> None:
        """'0.2.0' is accepted by SchemaVersionLiteral."""
        # If the literal is correct, SCHEMA_VERSION assignment would fail at import.
        # This test makes it explicit.
        args = get_args(SchemaVersionLiteral)
        assert "0.2.0" in args

    def test_old_version_rejected(self) -> None:
        """'0.1.0' is rejected by TurnRequest."""
        data = {
            "schema_version": "0.1.0",
            "turn_number": 1,
            "conversation_id": "conv_1",
            "focus": {"text": "test", "claims": [], "unresolved": []},
            "posture": "exploratory",
            "position": "p",
            "claims": [{"text": "c", "status": "new", "turn": 1}],
            "delta": "static",
            "tags": [],
            "unresolved": [],
        }
        with pytest.raises(ValidationError):
            TurnRequest.model_validate(data)


def test_action_literal_matches_conversation_action() -> None:
    """Parity: TurnPacketSuccess.action literal values match ConversationAction enum."""
    from context_injection.control import ConversationAction

    # Get the Literal args from TurnPacketSuccess.action field
    action_field = TurnPacketSuccess.model_fields["action"]
    literal_values = set(get_args(action_field.annotation))

    # Get ConversationAction enum values
    enum_values = {a.value for a in ConversationAction}

    assert literal_values == enum_values, (
        f"TurnPacketSuccess.action literal {literal_values} != "
        f"ConversationAction values {enum_values}"
    )


class TestEntity:
    def test_parse_file_path_entity(self) -> None:
        e = Entity(
            id="e_005",
            type="file_path",
            tier=1,
            raw="src/config/settings.yaml",
            canonical="src/config/settings.yaml",
            confidence="high",
            source_type="claim",
            in_focus=True,
            resolved_to=None,
        )
        assert e.type == "file_path"
        assert e.in_focus is True
        assert e.resolved_to is None

    def test_parse_file_name_with_resolution(self) -> None:
        e = Entity(
            id="e_006",
            type="file_name",
            tier=1,
            raw="config.yaml",
            canonical="config.yaml",
            confidence="high",
            source_type="unresolved",
            in_focus=True,
            resolved_to="e_008",
        )
        assert e.resolved_to == "e_008"


class TestPathDecision:
    def test_allowed_path(self) -> None:
        pd = PathDecision(
            entity_id="e_005",
            status="allowed",
            user_rel="src/config/settings.yaml",
            resolved_rel="src/config/settings.yaml",
            risk_signal=False,
            deny_reason=None,
            candidates=None,
            unresolved_reason=None,
        )
        assert pd.status == "allowed"
        assert pd.resolved_rel == "src/config/settings.yaml"

    def test_unresolved_with_candidates(self) -> None:
        pd = PathDecision(
            entity_id="e_010",
            status="unresolved",
            user_rel="config.yaml",
            resolved_rel=None,
            risk_signal=False,
            deny_reason=None,
            candidates=["src/config.yaml", "lib/config.yaml"],
            unresolved_reason="multiple_candidates",
        )
        assert pd.candidates == ["src/config.yaml", "lib/config.yaml"]
        assert pd.unresolved_reason == "multiple_candidates"


class TestBudget:
    def test_budget(self) -> None:
        b = Budget(
            evidence_count=1, evidence_remaining=4,
            scout_available=True, budget_status="under_budget",
        )
        assert b.evidence_remaining == 4
        assert b.budget_status == "under_budget"


class TestTemplateCandidate:
    def test_probe_candidate_with_scout_option(self) -> None:
        tc = TemplateCandidate(
            id="tc_001",
            template_id="probe.file_repo_fact",
            entity_id="e_005",
            focus_affinity=True,
            rank=1,
            rank_factors="file_path > file_name; high confidence",
            scout_options=[],  # Scout options tested separately in Task 5
            clarifier=None,
        )
        assert tc.rank == 1

    def test_clarifier_candidate(self) -> None:
        tc = TemplateCandidate(
            id="tc_003",
            template_id="clarify.file_path",
            entity_id="e_007",
            focus_affinity=False,
            rank=3,
            rank_factors="Tier 2 entity",
            scout_options=[],
            clarifier=Clarifier(
                question="Which file is 'the auth module'?",
                choices=["src/auth/middleware.py", "src/auth/handler.py"],
            ),
        )
        assert tc.clarifier is not None
        assert len(tc.clarifier.choices) == 2


# --- Discriminated union tests (Task 5) ---


class TestScoutSpec:
    def test_read_spec_first_n(self) -> None:
        spec = ReadSpec(
            action="read",
            resolved_path="src/config/settings.yaml",
            strategy="first_n",
            max_lines=40,
            max_chars=2000,
        )
        assert spec.action == "read"
        assert spec.strategy == "first_n"
        assert spec.center_line is None

    def test_read_spec_centered(self) -> None:
        spec = ReadSpec(
            action="read",
            resolved_path="src/config/settings.yaml",
            strategy="centered",
            max_lines=40,
            max_chars=2000,
            center_line=42,
        )
        assert spec.center_line == 42

    def test_grep_spec(self) -> None:
        spec = GrepSpec(
            action="grep",
            pattern="load_config",
            strategy="match_context",
            max_lines=40,
            max_chars=2000,
            context_lines=2,
            max_ranges=5,
        )
        assert spec.action == "grep"
        assert spec.context_lines == 2

    def test_discriminated_union_parses_read(self) -> None:
        data = {
            "action": "read",
            "resolved_path": "src/app.py",
            "strategy": "first_n",
            "max_lines": 40,
            "max_chars": 2000,
        }
        adapter = TypeAdapter(ScoutSpec)
        spec = adapter.validate_python(data)
        assert isinstance(spec, ReadSpec)

    def test_discriminated_union_parses_grep(self) -> None:
        data = {
            "action": "grep",
            "pattern": "main",
            "strategy": "match_context",
            "max_lines": 40,
            "max_chars": 2000,
            "context_lines": 2,
            "max_ranges": 5,
        }
        adapter = TypeAdapter(ScoutSpec)
        spec = adapter.validate_python(data)
        assert isinstance(spec, GrepSpec)


class TestScoutOption:
    def test_read_option(self) -> None:
        opt = ReadOption(
            id="so_005",
            scout_token="hmac_a1b2c3d4e5f6",
            action="read",
            target_display="src/config/settings.yaml",
            strategy="first_n",
            max_lines=40,
            max_chars=2000,
            risk_signal=False,
        )
        assert opt.action == "read"
        assert opt.center_line is None

    def test_grep_option(self) -> None:
        opt = GrepOption(
            id="so_006",
            scout_token="hmac_f6e5d4c3b2a1",
            action="grep",
            target_display="load_config",
            strategy="match_context",
            max_lines=40,
            max_chars=2000,
            context_lines=2,
            max_ranges=5,
        )
        assert opt.action == "grep"
        assert opt.context_lines == 2


class TestTurnPacket:
    def test_success_packet(self) -> None:
        entry = _minimal_ledger_entry()
        cumulative = _minimal_cumulative()
        data = {
            "schema_version": SCHEMA_VERSION,
            "status": "success",
            "entities": [],
            "path_decisions": [],
            "template_candidates": [],
            "budget": {
                "evidence_count": 0,
                "evidence_remaining": 5,
                "scout_available": True,
                "budget_status": "under_budget",
            },
            "deduped": [],
            "validated_entry": entry.model_dump(),
            "warnings": [],
            "cumulative": cumulative.model_dump(),
            "action": "continue_dialogue",
            "action_reason": "test",
            "ledger_summary": "test",
            "state_checkpoint": "base64==",
            "checkpoint_id": "cp_001",
        }
        adapter = TypeAdapter(TurnPacket)
        packet = adapter.validate_python(data)
        assert isinstance(packet, TurnPacketSuccess)

    def test_error_packet(self) -> None:
        data = {
            "schema_version": SCHEMA_VERSION,
            "status": "error",
            "error": {
                "code": "invalid_schema_version",
                "message": "Unsupported schema version",
                "details": None,
            },
        }
        adapter = TypeAdapter(TurnPacket)
        packet = adapter.validate_python(data)
        assert isinstance(packet, TurnPacketError)


class TestScoutResult:
    def test_success_read_result(self) -> None:
        data = {
            "schema_version": SCHEMA_VERSION,
            "scout_option_id": "so_005",
            "status": "success",
            "template_id": "probe.file_repo_fact",
            "entity_id": "e_005",
            "entity_key": "file_path:src/config/settings.yaml",
            "action": "read",
            "read_result": {
                "path_display": "src/config/settings.yaml",
                "excerpt": "port: 8080\nhost: 0.0.0.0",
                "excerpt_range": [1, 7],
                "total_lines": 42,
            },
            "grep_result": None,
            "truncated": False,
            "truncation_reason": None,
            "redactions_applied": 0,
            "risk_signal": False,
            "evidence_wrapper": "From `src/config/settings.yaml:1-7`",
            "budget": {
                "evidence_count": 2,
                "evidence_remaining": 3,
                "scout_available": False,
                "budget_status": "under_budget",
            },
        }
        adapter = TypeAdapter(ScoutResult)
        result = adapter.validate_python(data)
        assert isinstance(result, ScoutResultSuccess)
        assert result.read_result is not None
        assert result.grep_result is None

    def test_failure_not_found(self) -> None:
        data = {
            "schema_version": SCHEMA_VERSION,
            "scout_option_id": "so_005",
            "status": "not_found",
            "template_id": "probe.file_repo_fact",
            "entity_id": "e_005",
            "entity_key": "file_path:src/config/settings.yaml",
            "action": "read",
            "error_message": "File not found",
            "budget": {
                "evidence_count": 1,
                "evidence_remaining": 4,
                "scout_available": False,
                "budget_status": "under_budget",
            },
        }
        adapter = TypeAdapter(ScoutResult)
        result = adapter.validate_python(data)
        assert isinstance(result, ScoutResultFailure)

    def test_invalid_request(self) -> None:
        data = {
            "schema_version": SCHEMA_VERSION,
            "scout_option_id": "so_005",
            "status": "invalid_request",
            "error_message": "Scout token invalid",
            "budget": None,
        }
        adapter = TypeAdapter(ScoutResult)
        result = adapter.validate_python(data)
        assert isinstance(result, ScoutResultInvalid)
        assert result.budget is None


class TestDedupRecordInvariant:
    def test_template_already_used_requires_template_id(self) -> None:
        with pytest.raises(
            ValidationError, match="template_already_used requires template_id"
        ):
            DedupRecord(
                entity_key="file_path:src/app.py",
                template_id=None,
                reason="template_already_used",
                prior_turn=1,
            )

    def test_entity_already_scouted_forbids_template_id(self) -> None:
        with pytest.raises(
            ValidationError, match="entity_already_scouted must not have template_id"
        ):
            DedupRecord(
                entity_key="file_path:src/app.py",
                template_id="probe.file_repo_fact",
                reason="entity_already_scouted",
                prior_turn=1,
            )

    def test_valid_entity_already_scouted(self) -> None:
        d = DedupRecord(
            entity_key="file_path:src/app.py",
            template_id=None,
            reason="entity_already_scouted",
            prior_turn=1,
        )
        assert d.reason == "entity_already_scouted"

    def test_valid_template_already_used(self) -> None:
        d = DedupRecord(
            entity_key="file_path:src/app.py",
            template_id="probe.file_repo_fact",
            reason="template_already_used",
            prior_turn=1,
        )
        assert d.template_id == "probe.file_repo_fact"


class TestReadResultExcerptRangeNullable:
    def test_nullable_excerpt_range_accepts_none(self) -> None:
        """PEM suppression and zero-content scenarios need excerpt_range=None."""
        result = ReadResult(
            path_display="src/app.py",
            excerpt="[REDACTED:key_block]",
            excerpt_range=None,
            total_lines=100,
        )
        assert result.excerpt_range is None

    def test_non_null_excerpt_range_still_validates(self) -> None:
        result = ReadResult(
            path_display="src/app.py",
            excerpt="content here",
            excerpt_range=[1, 40],
            total_lines=100,
        )
        assert result.excerpt_range == [1, 40]

    def test_excerpt_range_rejects_wrong_length_when_not_none(self) -> None:
        with pytest.raises(Exception):
            ReadResult(
                path_display="src/app.py",
                excerpt="content",
                excerpt_range=[1],
                total_lines=100,
            )

    def test_excerpt_range_rejects_too_long(self) -> None:
        with pytest.raises(Exception):
            ReadResult(
                path_display="src/app.py",
                excerpt="content",
                excerpt_range=[1, 40, 80],
                total_lines=100,
            )

    def test_excerpt_range_rejects_wrong_item_type(self) -> None:
        """Strict mode rejects string items in list[int] field."""
        with pytest.raises(Exception):
            ReadResult(
                path_display="src/app.py",
                excerpt="content",
                excerpt_range=["1", "40"],
                total_lines=100,
            )


class TestBaseTypeReexports:
    """Verify types.py re-exports are identity-equal to base_types.py originals."""

    def test_reexport_identity(self) -> None:
        from context_injection.base_types import Claim as BaseClaim
        from context_injection.base_types import ProtocolModel as BaseProtocolModel
        from context_injection.base_types import Unresolved as BaseUnresolved
        from context_injection.types import Claim, ProtocolModel, Unresolved

        assert ProtocolModel is BaseProtocolModel
        assert Claim is BaseClaim
        assert Unresolved is BaseUnresolved
