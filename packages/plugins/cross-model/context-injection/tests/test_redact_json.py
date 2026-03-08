"""Tests for JSON/JSONC format redactor."""

from context_injection.redact_formats import (
    FormatRedactResult,
    redact_json,
)
from tests.redaction_harness import assert_redact_result, assert_suppressed

_RV = "[REDACTED:value]"


class TestRedactJson:
    # --- Basic functionality ---

    def test_simple_object(self) -> None:
        r = assert_redact_result(redact_json('{"name": "secret"}'))
        assert '"name"' in r.text
        assert "secret" not in r.text
        assert r.redactions_applied == 1

    def test_multiple_keys(self) -> None:
        text = '{"a": "x", "b": "y", "c": "z"}'
        r = assert_redact_result(redact_json(text))
        assert r.redactions_applied == 3
        for key in ('"a"', '"b"', '"c"'):
            assert key in r.text
        for val in ("x", "y", "z"):
            assert val not in r.text

    def test_nested_objects(self) -> None:
        text = '{"outer": {"inner": "secret"}}'
        r = assert_redact_result(redact_json(text))
        assert '"outer"' in r.text
        assert '"inner"' in r.text
        assert "secret" not in r.text

    def test_arrays(self) -> None:
        text = '{"items": [1, 2, 3]}'
        r = assert_redact_result(redact_json(text))
        assert '"items"' in r.text
        assert r.redactions_applied == 3

    def test_boolean_values(self) -> None:
        text = '{"flag": true, "other": false}'
        r = assert_redact_result(redact_json(text))
        assert "true" not in r.text
        assert "false" not in r.text
        assert r.redactions_applied == 2

    def test_null_value(self) -> None:
        r = assert_redact_result(redact_json('{"key": null}'))
        assert "null" not in r.text
        assert r.redactions_applied == 1

    def test_number_varieties(self) -> None:
        text = '{"int": 42, "neg": -1, "float": 3.14, "exp": 1e10}'
        r = assert_redact_result(redact_json(text))
        assert r.redactions_applied == 4
        for num in ("42", "-1", "3.14", "1e10"):
            assert num not in r.text

    def test_string_with_escapes(self) -> None:
        text = '{"key": "val\\"ue"}'
        r = assert_redact_result(redact_json(text))
        assert r.redactions_applied == 1

    def test_empty_string_value(self) -> None:
        r = assert_redact_result(redact_json('{"key": ""}'))
        assert r.redactions_applied == 1

    def test_empty_object_no_redactions(self) -> None:
        r = assert_redact_result(redact_json('{"config": {}}'))
        assert r.redactions_applied == 0
        assert '"config"' in r.text

    def test_compact_no_spaces(self) -> None:
        r = assert_redact_result(redact_json('{"a":1,"b":2}'))
        assert r.redactions_applied == 2
        assert '"a"' in r.text
        assert '"b"' in r.text

    def test_multiline_structure(self) -> None:
        text = '{\n  "name": "test",\n  "count": 42\n}'
        r = assert_redact_result(redact_json(text))
        assert '"name"' in r.text
        assert '"count"' in r.text
        assert r.redactions_applied == 2

    def test_colon_in_string_value(self) -> None:
        """Colon inside string value doesn't trigger key detection."""
        r = assert_redact_result(redact_json('{"url": "http://host:8080"}'))
        assert '"url"' in r.text
        assert "host" not in r.text
        assert r.redactions_applied == 1

    def test_key_with_whitespace_before_colon(self) -> None:
        r = assert_redact_result(redact_json('{"key"  :  "val"}'))
        assert '"key"' in r.text
        assert r.redactions_applied == 1

    def test_array_of_objects(self) -> None:
        text = '[{"a": 1}, {"b": 2}]'
        r = assert_redact_result(redact_json(text))
        assert r.redactions_applied == 2
        assert '"a"' in r.text
        assert '"b"' in r.text

    def test_trailing_comma_tolerance(self) -> None:
        """JSONC trailing comma doesn't cause desync."""
        r = assert_redact_result(redact_json('{"a": 1, "b": 2,}'))
        assert r.redactions_applied == 2

    # --- JSONC comments ---

    def test_jsonc_line_comment(self) -> None:
        text = '{\n  "key": "secret" // comment\n}'
        r = assert_redact_result(redact_json(text))
        assert "// [REDACTED:comment]" in r.text
        assert "comment" not in r.text.replace("[REDACTED:comment]", "")
        assert "secret" not in r.text
        assert r.redactions_applied == 1

    def test_jsonc_block_comment(self) -> None:
        text = '{"key": /* inline */ "secret"}'
        r = assert_redact_result(redact_json(text))
        assert "/* [REDACTED:comment] */" in r.text
        assert "inline" not in r.text
        assert "secret" not in r.text
        assert r.redactions_applied == 1

    def test_jsonc_unterminated_block_comment_redacted(self) -> None:
        """P2 fix: unterminated /* at EOF is redacted without closing */."""
        text = '{"key": "val"} /* secret note'
        r = assert_redact_result(redact_json(text))
        assert "/* [REDACTED:comment]" in r.text
        assert "*/" not in r.text
        assert "secret" not in r.text

    def test_jsonc_line_comment_standalone(self) -> None:
        """Standalone // comment on its own line is redacted."""
        text = '{\n  // secret config note\n  "key": "val"\n}'
        r = assert_redact_result(redact_json(text))
        assert "// [REDACTED:comment]" in r.text
        assert "secret" not in r.text

    def test_jsonc_block_comment_multiline(self) -> None:
        """Multi-line /* */ block comment collapsed to single redaction marker."""
        text = '{\n  /* line one\n     line two */\n  "key": "val"\n}'
        r = assert_redact_result(redact_json(text))
        assert "/* [REDACTED:comment] */" in r.text
        assert "line one" not in r.text
        assert "line two" not in r.text

    # --- Partial document tolerance ---

    def test_partial_document_no_braces(self) -> None:
        """40-line excerpt window without enclosing braces."""
        text = '  "host": "localhost",\n  "port": 5432'
        r = assert_redact_result(redact_json(text))
        assert '"host"' in r.text
        assert "localhost" not in r.text
        assert "5432" not in r.text
        assert r.redactions_applied == 2

    def test_eof_in_string_no_desync(self) -> None:
        """Scanner ending in IN_STRING tolerates partial doc."""
        result = redact_json('{"key": "unterminated')
        assert isinstance(result, FormatRedactResult)

    def test_eof_in_block_comment_no_desync(self) -> None:
        result = redact_json('{"key": "val"} /* unterminated')
        assert isinstance(result, FormatRedactResult)

    def test_eof_partial_keyword(self) -> None:
        """Truncated keyword at EOF doesn't desync."""
        result = redact_json('{"key": tru')
        assert isinstance(result, FormatRedactResult)

    # --- Desync ---

    def test_desync_unquoted_key(self) -> None:
        assert_suppressed(
            redact_json("{key: value}"),
            reason_contains="json_scanner_desync",
        )

    def test_desync_unexpected_char(self) -> None:
        assert_suppressed(
            redact_json("@invalid"),
            reason_contains="json_scanner_desync",
        )

    # --- Edge cases ---

    def test_empty_input(self) -> None:
        r = assert_redact_result(redact_json(""))
        assert r.redactions_applied == 0

    def test_whitespace_only(self) -> None:
        r = assert_redact_result(redact_json("  \n  \n"))
        assert r.redactions_applied == 0

    def test_trailing_newline_preserved(self) -> None:
        r = assert_redact_result(redact_json('{"k": "v"}\n'))
        assert r.text.endswith("\n")

    def test_no_trailing_newline_preserved(self) -> None:
        r = assert_redact_result(redact_json('{"k": "v"}'))
        assert not r.text.endswith("\n")

    def test_deeply_nested(self) -> None:
        text = '{"a":{"b":{"c":"SECRET"}}}'
        r = assert_redact_result(redact_json(text))
        assert '"a"' in r.text
        assert '"b"' in r.text
        assert '"c"' in r.text
        assert "SECRET" not in r.text
        assert r.redactions_applied == 1

    def test_empty_array_no_redactions(self) -> None:
        r = assert_redact_result(redact_json('{"items":[]}'))
        assert r.redactions_applied == 0

    def test_bare_negative_desyncs(self) -> None:
        """Bare - without following digit is not a valid JSON number."""
        assert_suppressed(
            redact_json('{"key": -}'),
            reason_contains="json_scanner_desync",
        )
