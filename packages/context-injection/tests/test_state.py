"""Tests for server state management, HMAC tokens, and TurnRequest store."""

import pytest

from context_injection.canonical import ScoutTokenPayload
from context_injection.conversation import ConversationState
from context_injection.state import (
    MAX_TURN_RECORDS,
    AppContext,
    ScoutOptionRecord,
    TurnRequestRecord,
    generate_token,
    make_turn_request_ref,
    verify_token,
)
from context_injection.types import Focus, GrepSpec, ReadSpec, TurnRequest, SCHEMA_VERSION


def _make_read_spec(**overrides) -> ReadSpec:
    defaults = dict(
        action="read",
        resolved_path="src/app.py",
        strategy="first_n",
        max_lines=40,
        max_chars=2000,
    )
    defaults.update(overrides)
    return ReadSpec(**defaults)


def _make_turn_request(
    conversation_id: str = "conv_1", turn_number: int = 1
) -> TurnRequest:
    return TurnRequest(
        schema_version=SCHEMA_VERSION,
        turn_number=turn_number,
        conversation_id=conversation_id,
        focus=Focus(text="test", claims=[], unresolved=[]),
        evidence_history=[],
        posture="exploratory",
    )


class TestAppContext:
    def test_creates_hmac_key(self) -> None:
        ctx = AppContext.create(repo_root="/tmp/repo")
        assert len(ctx.hmac_key) == 32

    def test_different_instances_different_keys(self) -> None:
        ctx1 = AppContext.create(repo_root="/tmp/repo")
        ctx2 = AppContext.create(repo_root="/tmp/repo")
        assert ctx1.hmac_key != ctx2.hmac_key


class TestTokenGeneration:
    def test_roundtrip(self) -> None:
        """Generate a token and verify it."""
        ctx = AppContext.create(repo_root="/tmp/repo")
        spec = _make_read_spec()
        payload = ScoutTokenPayload(
            v=1,
            conversation_id="conv_1",
            turn_number=1,
            scout_option_id="so_001",
            spec=spec,
        )
        token = generate_token(ctx.hmac_key, payload)
        assert isinstance(token, str)
        assert verify_token(ctx.hmac_key, payload, token)

    def test_wrong_key_fails(self) -> None:
        ctx1 = AppContext.create(repo_root="/tmp/repo")
        ctx2 = AppContext.create(repo_root="/tmp/repo")
        spec = _make_read_spec()
        payload = ScoutTokenPayload(
            v=1,
            conversation_id="conv_1",
            turn_number=1,
            scout_option_id="so_001",
            spec=spec,
        )
        token = generate_token(ctx1.hmac_key, payload)
        assert not verify_token(ctx2.hmac_key, payload, token)

    def test_modified_payload_fails(self) -> None:
        ctx = AppContext.create(repo_root="/tmp/repo")
        spec = _make_read_spec()
        payload = ScoutTokenPayload(
            v=1,
            conversation_id="conv_1",
            turn_number=1,
            scout_option_id="so_001",
            spec=spec,
        )
        token = generate_token(ctx.hmac_key, payload)
        # Different spec
        modified_spec = _make_read_spec(resolved_path="src/evil.py")
        modified_payload = ScoutTokenPayload(
            v=1,
            conversation_id="conv_1",
            turn_number=1,
            scout_option_id="so_001",
            spec=modified_spec,
        )
        assert not verify_token(ctx.hmac_key, modified_payload, token)

    def test_token_is_base64url_encoded(self) -> None:
        """Token is base64url-encoded, length matches TAG_LEN."""
        import base64
        from context_injection.state import TAG_LEN

        ctx = AppContext.create(repo_root="/tmp/repo")
        spec = _make_read_spec()
        payload = ScoutTokenPayload(
            v=1,
            conversation_id="conv_1",
            turn_number=1,
            scout_option_id="so_001",
            spec=spec,
        )
        token = generate_token(ctx.hmac_key, payload)
        # Decode should succeed (valid base64url)
        decoded = base64.urlsafe_b64decode(token)
        assert len(decoded) == TAG_LEN


class TestTurnRequestStore:
    def test_store_and_retrieve(self) -> None:
        ctx = AppContext.create(repo_root="/tmp/repo")
        req = _make_turn_request()
        ref = make_turn_request_ref(req)
        spec = _make_read_spec()
        token = "token_123"
        option = ScoutOptionRecord(
            spec=spec,
            token=token,
            template_id="probe.file_repo_fact",
            entity_id="e_001",
            entity_key="file_path:src/app.py",
            risk_signal=False,
            path_display="src/app.py",
            action="read",
        )
        record = TurnRequestRecord(
            turn_request=req,
            scout_options={"so_001": option},
        )
        ctx.store_record(ref, record)
        assert ref in ctx.store
        assert ctx.store[ref].scout_options["so_001"] is option

    def test_duplicate_ref_rejected(self) -> None:
        ctx = AppContext.create(repo_root="/tmp/repo")
        req = _make_turn_request()
        ref = make_turn_request_ref(req)
        record = TurnRequestRecord(turn_request=req, scout_options={})
        ctx.store_record(ref, record)
        with pytest.raises(ValueError, match="Duplicate turn_request_ref"):
            ctx.store_record(ref, record)

    def test_bounded_capacity_evicts_oldest(self) -> None:
        ctx = AppContext.create(repo_root="/tmp/repo")
        # Fill store to capacity
        for i in range(MAX_TURN_RECORDS + 5):
            req = _make_turn_request(turn_number=i + 1)
            ref = make_turn_request_ref(req)
            record = TurnRequestRecord(turn_request=req, scout_options={})
            ctx.store_record(ref, record)
        assert len(ctx.store) == MAX_TURN_RECORDS
        # Oldest should be evicted
        oldest_ref = make_turn_request_ref(_make_turn_request(turn_number=1))
        assert oldest_ref not in ctx.store

    def test_used_bit_lifecycle(self) -> None:
        ctx = AppContext.create(repo_root="/tmp/repo")
        req = _make_turn_request()
        ref = make_turn_request_ref(req)
        record = TurnRequestRecord(turn_request=req, scout_options={})
        ctx.store[ref] = record
        assert record.used is False
        record.used = True
        assert ctx.store[ref].used is True


class TestMakeTurnRequestRef:
    def test_format(self) -> None:
        req = _make_turn_request(conversation_id="conv_abc", turn_number=3)
        assert make_turn_request_ref(req) == "conv_abc:3"


class TestScoutOptionRecord:
    def test_construction_and_fields(self) -> None:
        spec = _make_read_spec()
        record = ScoutOptionRecord(
            spec=spec,
            token="tok_abc",
            template_id="probe.file_repo_fact",
            entity_id="e_001",
            entity_key="file_path:src/app.py",
            risk_signal=False,
            path_display="src/app.py",
            action="read",
        )
        assert record.spec is spec
        assert record.token == "tok_abc"
        assert record.template_id == "probe.file_repo_fact"
        assert record.entity_id == "e_001"
        assert record.entity_key == "file_path:src/app.py"
        assert record.risk_signal is False
        assert record.path_display == "src/app.py"
        assert record.action == "read"

    def test_frozen(self) -> None:
        record = ScoutOptionRecord(
            spec=_make_read_spec(),
            token="tok_abc",
            template_id="probe.file_repo_fact",
            entity_id="e_001",
            entity_key="file_path:src/app.py",
            risk_signal=False,
            path_display="src/app.py",
            action="read",
        )
        with pytest.raises(AttributeError):
            record.token = "different"

    def test_grep_action(self) -> None:
        spec = GrepSpec(
            action="grep",
            pattern="MyClass",
            strategy="match_context",
            max_lines=40,
            max_chars=2000,
            context_lines=2,
            max_ranges=5,
        )
        record = ScoutOptionRecord(
            spec=spec,
            token="tok_xyz",
            template_id="probe.symbol_repo_fact",
            entity_id="e_002",
            entity_key="symbol:MyClass",
            risk_signal=False,
            path_display="MyClass",
            action="grep",
        )
        assert record.action == "grep"
        assert record.entity_key == "symbol:MyClass"


def _setup_consume_test(
    ctx: AppContext | None = None,
) -> tuple[AppContext, str, str, str, ScoutOptionRecord]:
    """Set up a valid consume_scout scenario.

    Returns (ctx, turn_request_ref, scout_option_id, token, expected_record).
    """
    if ctx is None:
        ctx = AppContext.create(repo_root="/tmp/repo")
    req = _make_turn_request()
    ref = make_turn_request_ref(req)

    spec = _make_read_spec()
    so_id = "so_001"
    payload = ScoutTokenPayload(
        v=1,
        conversation_id=req.conversation_id,
        turn_number=req.turn_number,
        scout_option_id=so_id,
        spec=spec,
    )
    token = generate_token(ctx.hmac_key, payload)

    option = ScoutOptionRecord(
        spec=spec,
        token=token,
        template_id="probe.file_repo_fact",
        entity_id="e_001",
        entity_key="file_path:src/app.py",
        risk_signal=False,
        path_display="src/app.py",
        action="read",
    )
    record = TurnRequestRecord(
        turn_request=req,
        scout_options={so_id: option},
    )
    ctx.store_record(ref, record)

    return ctx, ref, so_id, token, option


class TestConsumeScout:
    def test_valid_consume_returns_record(self) -> None:
        ctx, ref, so_id, token, expected = _setup_consume_test()
        result = ctx.consume_scout(ref, so_id, token)
        assert result is expected

    def test_marks_record_used(self) -> None:
        ctx, ref, so_id, token, _ = _setup_consume_test()
        assert ctx.store[ref].used is False
        ctx.consume_scout(ref, so_id, token)
        assert ctx.store[ref].used is True

    def test_returns_all_metadata_fields(self) -> None:
        ctx, ref, so_id, token, _ = _setup_consume_test()
        result = ctx.consume_scout(ref, so_id, token)
        assert result.template_id == "probe.file_repo_fact"
        assert result.entity_id == "e_001"
        assert result.entity_key == "file_path:src/app.py"
        assert result.risk_signal is False
        assert result.path_display == "src/app.py"
        assert result.action == "read"

    def test_unknown_ref_raises(self) -> None:
        ctx, _, so_id, token, _ = _setup_consume_test()
        with pytest.raises(ValueError, match="turn_request_ref not found"):
            ctx.consume_scout("nonexistent:1", so_id, token)

    def test_unknown_option_id_raises(self) -> None:
        ctx, ref, _, token, _ = _setup_consume_test()
        with pytest.raises(ValueError, match="scout_option_id not found"):
            ctx.consume_scout(ref, "so_999", token)

    def test_bad_token_raises(self) -> None:
        ctx, ref, so_id, _, _ = _setup_consume_test()
        with pytest.raises(ValueError, match="token verification failed"):
            ctx.consume_scout(ref, so_id, "AAAAAAAAAAAAAAAAAAAAAA==")

    def test_replay_raises(self) -> None:
        ctx, ref, so_id, token, _ = _setup_consume_test()
        ctx.consume_scout(ref, so_id, token)  # First use
        with pytest.raises(ValueError, match="already used"):
            ctx.consume_scout(ref, so_id, token)

    def test_bad_token_does_not_set_used(self) -> None:
        """Used-bit not set on verification failure (D10 design decision)."""
        ctx, ref, so_id, _, _ = _setup_consume_test()
        with pytest.raises(ValueError, match="token verification failed"):
            ctx.consume_scout(ref, so_id, "AAAAAAAAAAAAAAAAAAAAAA==")
        assert ctx.store[ref].used is False

    def test_different_option_after_used_raises(self) -> None:
        """One scout per turn: consuming any option after used=True fails.

        Protocol guarantees scout_available=false after one consumption.
        The used bit is per-record, not per-option.
        """
        ctx = AppContext.create(repo_root="/tmp/repo")
        req = _make_turn_request()
        ref = make_turn_request_ref(req)
        spec1 = _make_read_spec()
        spec2 = _make_read_spec(resolved_path="src/other.py")
        payload1 = ScoutTokenPayload(
            v=1,
            conversation_id=req.conversation_id,
            turn_number=req.turn_number,
            scout_option_id="so_001",
            spec=spec1,
        )
        payload2 = ScoutTokenPayload(
            v=1,
            conversation_id=req.conversation_id,
            turn_number=req.turn_number,
            scout_option_id="so_002",
            spec=spec2,
        )
        token1 = generate_token(ctx.hmac_key, payload1)
        token2 = generate_token(ctx.hmac_key, payload2)
        option1 = ScoutOptionRecord(
            spec=spec1, token=token1,
            template_id="probe.file_repo_fact", entity_id="e_001",
            entity_key="file_path:src/app.py", risk_signal=False,
            path_display="src/app.py", action="read",
        )
        option2 = ScoutOptionRecord(
            spec=spec2, token=token2,
            template_id="probe.file_repo_fact", entity_id="e_002",
            entity_key="file_path:src/other.py", risk_signal=False,
            path_display="src/other.py", action="read",
        )
        record = TurnRequestRecord(
            turn_request=req,
            scout_options={"so_001": option1, "so_002": option2},
        )
        ctx.store_record(ref, record)
        ctx.consume_scout(ref, "so_001", token1)
        with pytest.raises(ValueError, match="already used"):
            ctx.consume_scout(ref, "so_002", token2)


class TestAppContextConversations:
    """AppContext conversation management."""

    def test_conversations_empty_by_default(self) -> None:
        ctx = AppContext.create(repo_root="/tmp/test")
        assert ctx.conversations == {}

    def test_get_or_create_new(self) -> None:
        ctx = AppContext.create(repo_root="/tmp/test")
        state = ctx.get_or_create_conversation("conv-1")
        assert isinstance(state, ConversationState)
        assert state.conversation_id == "conv-1"
        assert state.entries == ()

    def test_get_or_create_returns_existing(self) -> None:
        ctx = AppContext.create(repo_root="/tmp/test")
        state1 = ctx.get_or_create_conversation("conv-1")
        state2 = ctx.get_or_create_conversation("conv-1")
        assert state1 is state2

    def test_multiple_conversations(self) -> None:
        ctx = AppContext.create(repo_root="/tmp/test")
        s1 = ctx.get_or_create_conversation("conv-1")
        s2 = ctx.get_or_create_conversation("conv-2")
        assert s1.conversation_id == "conv-1"
        assert s2.conversation_id == "conv-2"
        assert len(ctx.conversations) == 2

    def test_conversation_replacement(self) -> None:
        """Pipeline commits by replacing dict entry."""
        ctx = AppContext.create(repo_root="/tmp/test")
        state = ctx.get_or_create_conversation("conv-1")
        projected = state.with_checkpoint_id("cp-1")
        ctx.conversations["conv-1"] = projected
        retrieved = ctx.get_or_create_conversation("conv-1")
        assert retrieved.last_checkpoint_id == "cp-1"


class TestConversationGuardLimit:
    """DD-3: CONVERSATION_GUARD_LIMIT overflow protection."""

    def test_below_limit_creates(self) -> None:
        """Creating conversations below the limit succeeds."""
        ctx = AppContext.create(repo_root="/tmp/test")
        for i in range(ctx.CONVERSATION_GUARD_LIMIT):
            state = ctx.get_or_create_conversation(f"conv-{i}")
            assert state.conversation_id == f"conv-{i}"
        assert len(ctx.conversations) == ctx.CONVERSATION_GUARD_LIMIT

    def test_overflow_on_new_id_raises(self) -> None:
        """Creating a new conversation at the limit raises ValueError."""
        ctx = AppContext.create(repo_root="/tmp/test")
        for i in range(ctx.CONVERSATION_GUARD_LIMIT):
            ctx.get_or_create_conversation(f"conv-{i}")
        with pytest.raises(ValueError, match="Conversation limit exceeded"):
            ctx.get_or_create_conversation("conv-overflow")

    def test_existing_id_returns_at_limit(self) -> None:
        """Retrieving an existing conversation at the limit succeeds."""
        ctx = AppContext.create(repo_root="/tmp/test")
        for i in range(ctx.CONVERSATION_GUARD_LIMIT):
            ctx.get_or_create_conversation(f"conv-{i}")
        # Existing ID should still be retrievable
        state = ctx.get_or_create_conversation("conv-0")
        assert state.conversation_id == "conv-0"
