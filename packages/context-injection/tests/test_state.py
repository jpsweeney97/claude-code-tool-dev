"""Tests for server state management, HMAC tokens, and TurnRequest store."""

import pytest

from context_injection.canonical import ScoutTokenPayload
from context_injection.state import (
    MAX_TURN_RECORDS,
    AppContext,
    TurnRequestRecord,
    generate_token,
    make_turn_request_ref,
    verify_token,
)
from context_injection.types import Focus, ReadSpec, TurnRequest, SCHEMA_VERSION


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
        record = TurnRequestRecord(
            turn_request=req,
            scout_options={"so_001": (spec, token)},
        )
        ctx.store_record(ref, record)
        assert ref in ctx.store
        assert ctx.store[ref].scout_options["so_001"] == (spec, token)

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
