"""Tests for ticket_stage_models.py — stage boundary input models."""
from __future__ import annotations

import pytest

from scripts.ticket_stage_models import (
    ClassifyInput,
    PayloadError,
    PlanInput,
)


class TestPayloadError:
    def test_carries_code_and_state(self):
        exc = PayloadError("missing field: action", code="need_fields", state="need_fields")
        assert str(exc) == "missing field: action"
        assert exc.code == "need_fields"
        assert exc.state == "need_fields"

    def test_parse_error_variant(self):
        exc = PayloadError("args must be a dict", code="parse_error", state="escalate")
        assert exc.code == "parse_error"
        assert exc.state == "escalate"


class TestClassifyInput:
    def test_valid_payload(self):
        inp = ClassifyInput.from_payload({
            "action": "create",
            "args": {"ticket_id": "T-001"},
            "session_id": "sess-1",
        })
        assert inp.action == "create"
        assert inp.args == {"ticket_id": "T-001"}
        assert inp.session_id == "sess-1"

    def test_defaults(self):
        inp = ClassifyInput.from_payload({
            "action": "create",
            "session_id": "sess-1",
        })
        assert inp.args == {}

    def test_empty_defaults_for_missing_strings(self):
        """Preserves current _dispatch() behavior: missing action/session_id default to ''."""
        inp = ClassifyInput.from_payload({})
        assert inp.action == ""
        assert inp.session_id == ""
        assert inp.args == {}

    def test_args_wrong_type_raises_parse_error(self):
        with pytest.raises(PayloadError) as exc_info:
            ClassifyInput.from_payload({
                "action": "create",
                "args": "not a dict",
                "session_id": "sess-1",
            })
        assert exc_info.value.code == "parse_error"
        assert exc_info.value.state == "escalate"

    def test_extra_keys_ignored(self):
        inp = ClassifyInput.from_payload({
            "action": "create",
            "args": {},
            "session_id": "sess-1",
            "extra_field": "ignored",
            "hook_injected": True,
        })
        assert inp.action == "create"

    def test_frozen(self):
        inp = ClassifyInput.from_payload({"action": "create", "session_id": "s"})
        with pytest.raises(AttributeError):
            inp.action = "update"


class TestPlanInput:
    def test_valid_payload(self):
        inp = PlanInput.from_payload({
            "intent": "create",
            "fields": {"title": "Test"},
            "session_id": "sess-1",
        })
        assert inp.intent == "create"
        assert inp.fields == {"title": "Test"}
        assert inp.session_id == "sess-1"

    def test_intent_falls_back_to_action(self):
        inp = PlanInput.from_payload({
            "action": "update",
            "session_id": "sess-1",
        })
        assert inp.intent == "update"

    def test_intent_prefers_intent_over_action(self):
        inp = PlanInput.from_payload({
            "intent": "create",
            "action": "update",
            "session_id": "sess-1",
        })
        assert inp.intent == "create"

    def test_defaults(self):
        inp = PlanInput.from_payload({})
        assert inp.intent == ""
        assert inp.fields == {}
        assert inp.session_id == ""

    def test_fields_wrong_type_raises_parse_error(self):
        with pytest.raises(PayloadError) as exc_info:
            PlanInput.from_payload({
                "intent": "create",
                "fields": ["not", "a", "dict"],
                "session_id": "sess-1",
            })
        assert exc_info.value.code == "parse_error"

    def test_frozen(self):
        inp = PlanInput.from_payload({"session_id": "s"})
        with pytest.raises(AttributeError):
            inp.intent = "update"
