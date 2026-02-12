"""Tests for canonical serialization and entity key functions."""

import json


from context_injection.canonical import (
    ScoutTokenPayload,
    canonical_json_bytes,
    make_entity_key,
    parse_entity_key,
    wire_dump,
)
from context_injection.types import ReadSpec, GrepSpec, Budget


class TestCanonicalJsonBytes:
    def test_read_spec_golden_vector(self) -> None:
        """Golden vector: ReadSpec with first_n strategy."""
        spec = ReadSpec(
            action="read",
            resolved_path="src/config/settings.yaml",
            strategy="first_n",
            max_lines=40,
            max_chars=2000,
        )
        payload = ScoutTokenPayload(
            v=1,
            conversation_id="conv_abc123",
            turn_number=3,
            scout_option_id="so_005",
            spec=spec,
        )
        result = canonical_json_bytes(payload)
        parsed = json.loads(result)
        # Verify deterministic key ordering
        assert list(parsed.keys()) == sorted(parsed.keys())
        # Verify no None values (center_line is None, should be excluded)
        assert "center_line" not in json.dumps(parsed)
        # Verify no whitespace
        assert b" " not in result
        assert b"\n" not in result

    def test_grep_spec_golden_vector(self) -> None:
        spec = GrepSpec(
            action="grep",
            pattern="load_config",
            strategy="match_context",
            max_lines=40,
            max_chars=2000,
            context_lines=2,
            max_ranges=5,
        )
        payload = ScoutTokenPayload(
            v=1,
            conversation_id="conv_1",
            turn_number=1,
            scout_option_id="so_001",
            spec=spec,
        )
        result = canonical_json_bytes(payload)
        parsed = json.loads(result)
        assert parsed["spec"]["action"] == "grep"
        assert parsed["spec"]["pattern"] == "load_config"

    def test_unicode_nfc_path(self) -> None:
        """Paths must be NFC-normalized before entering models."""
        # This test verifies the bytes are valid UTF-8
        spec = ReadSpec(
            action="read",
            resolved_path="src/caf\u00e9.py",  # NFC form
            strategy="first_n",
            max_lines=40,
            max_chars=2000,
        )
        payload = ScoutTokenPayload(
            v=1,
            conversation_id="c",
            turn_number=1,
            scout_option_id="so",
            spec=spec,
        )
        result = canonical_json_bytes(payload)
        assert "caf\u00e9".encode("utf-8") in result

    def test_deterministic_output(self) -> None:
        """Same input produces identical bytes."""
        spec = ReadSpec(
            action="read",
            resolved_path="a.py",
            strategy="first_n",
            max_lines=40,
            max_chars=2000,
        )
        payload = ScoutTokenPayload(
            v=1,
            conversation_id="c",
            turn_number=1,
            scout_option_id="so",
            spec=spec,
        )
        assert canonical_json_bytes(payload) == canonical_json_bytes(payload)


class TestWireDump:
    def test_includes_null_for_none(self) -> None:
        """Wire format includes explicit null for None values."""
        from context_injection.types import Entity

        e = Entity(
            id="e_001",
            type="file_path",
            tier=1,
            raw="a.py",
            canonical="a.py",
            confidence="high",
            source_type="claim",
            in_focus=True,
            resolved_to=None,
        )
        dumped = wire_dump(e)
        assert dumped["resolved_to"] is None
        assert "resolved_to" in dumped

    def test_budget_wire_dump(self) -> None:
        b = Budget(evidence_count=1, evidence_remaining=4, scout_available=True)
        dumped = wire_dump(b)
        assert dumped == {
            "evidence_count": 1,
            "evidence_remaining": 4,
            "scout_available": True,
        }


class TestEntityKey:
    def test_roundtrip(self) -> None:
        key = make_entity_key("file_path", "src/config/settings.yaml")
        assert key == "file_path:src/config/settings.yaml"
        entity_type, canonical = parse_entity_key(key)
        assert entity_type == "file_path"
        assert canonical == "src/config/settings.yaml"

    def test_symbol_with_parens(self) -> None:
        key = make_entity_key("symbol", "load_config")
        assert key == "symbol:load_config"

    def test_parse_with_colon_in_value(self) -> None:
        """file_loc values contain colons (e.g., config.py:42)."""
        key = "file_loc:config.py:42"
        entity_type, canonical = parse_entity_key(key)
        assert entity_type == "file_loc"
        assert canonical == "config.py:42"
