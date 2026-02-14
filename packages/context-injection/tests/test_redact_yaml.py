"""Tests for YAML format redactor."""

from context_injection.redact_formats import redact_yaml
from tests.redaction_harness import assert_redact_result

_RV = "[REDACTED:value]"


class TestRedactYaml:
    # --- Basic key:value ---

    def test_basic_key_value(self) -> None:
        r = assert_redact_result(redact_yaml("host: localhost\n"))
        assert "host:" in r.text
        assert "localhost" not in r.text
        assert r.redactions_applied == 1

    def test_multiple_keys(self) -> None:
        text = "host: localhost\nport: 5432\nname: mydb\n"
        r = assert_redact_result(redact_yaml(text))
        assert r.redactions_applied == 3
        assert "host:" in r.text
        assert "port:" in r.text

    def test_indented_mapping(self) -> None:
        text = "database:\n  host: localhost\n  port: 5432\n"
        r = assert_redact_result(redact_yaml(text))
        assert "database:" in r.text
        assert "host:" in r.text
        assert "localhost" not in r.text
        assert r.redactions_applied == 2

    def test_key_no_value(self) -> None:
        """Key with sub-keys below -- preserved as-is."""
        text = "database:\n  host: localhost\n"
        r = assert_redact_result(redact_yaml(text))
        assert "database:" in r.text
        assert r.redactions_applied == 1  # only host value

    def test_key_colon_end_of_line(self) -> None:
        """Colon at end of line (no space) is a valid mapping."""
        r = assert_redact_result(redact_yaml("items:\n"))
        assert "items:" in r.text
        assert r.redactions_applied == 0  # no value to redact

    # --- False positive prevention ---

    def test_url_in_value_redacted(self) -> None:
        """The mapping colon is after 'website', not in the URL."""
        r = assert_redact_result(redact_yaml("website: http://example.com\n"))
        assert "website:" in r.text
        assert "http://example.com" not in r.text
        assert r.redactions_applied == 1

    def test_port_no_space_not_mapping(self) -> None:
        """host:8080 (no space after colon) is NOT a mapping -- it's a value."""
        r = assert_redact_result(redact_yaml("- host:8080\n"))
        assert "host:8080" not in r.text
        assert r.redactions_applied == 1

    def test_comment_with_colon_preserved(self) -> None:
        text = "# server: old_host\nserver: new_host\n"
        r = assert_redact_result(redact_yaml(text))
        assert "# server: old_host" in r.text
        assert "new_host" not in r.text
        assert r.redactions_applied == 1

    # --- Block scalars ---

    def test_block_scalar_literal(self) -> None:
        text = "desc: |\n  Line one\n  Line two\nnext: value\n"
        r = assert_redact_result(redact_yaml(text))
        assert "desc: |" in r.text
        assert "Line one" not in r.text
        assert "Line two" not in r.text
        assert "next:" in r.text
        assert r.redactions_applied == 2  # block content (1) + next value (1)

    def test_block_scalar_folded(self) -> None:
        text = "desc: >\n  Line one\n  Line two\n"
        r = assert_redact_result(redact_yaml(text))
        assert "desc: >" in r.text
        assert "Line one" not in r.text

    def test_block_scalar_with_chomp_indicator(self) -> None:
        r = assert_redact_result(redact_yaml("key: |+\n  content\n"))
        assert "key: |+" in r.text
        assert "content" not in r.text

    def test_block_scalar_empty_line_within(self) -> None:
        text = "desc: |\n  Line one\n\n  Line three\nnext: val\n"
        r = assert_redact_result(redact_yaml(text))
        assert "Line one" not in r.text
        assert "Line three" not in r.text
        assert "next:" in r.text

    # --- Anchors and aliases ---

    def test_anchor_no_inline_value(self) -> None:
        """Anchor with sub-keys below -- line preserved."""
        r = assert_redact_result(redact_yaml("base: &defaults\n  host: localhost\n"))
        assert "&defaults" in r.text
        assert r.redactions_applied == 1  # only host

    def test_anchor_with_inline_value(self) -> None:
        r = assert_redact_result(redact_yaml("name: &name John\n"))
        assert "&name" in r.text
        assert "John" not in r.text
        assert r.redactions_applied == 1

    def test_alias_preserved(self) -> None:
        """Aliases are references, not secrets."""
        r = assert_redact_result(redact_yaml("child: *defaults\n"))
        assert "*defaults" in r.text
        assert r.redactions_applied == 0

    def test_alias_in_sequence(self) -> None:
        r = assert_redact_result(redact_yaml("items:\n  - *ref\n"))
        assert "*ref" in r.text
        assert r.redactions_applied == 0

    # --- Flow collections ---

    def test_single_line_flow_sequence(self) -> None:
        r = assert_redact_result(redact_yaml("ports: [8080, 443, 80]\n"))
        assert "ports:" in r.text
        assert "8080" not in r.text
        assert r.redactions_applied == 1

    def test_single_line_flow_mapping(self) -> None:
        r = assert_redact_result(redact_yaml("config: {host: localhost, port: 5432}\n"))
        assert "config:" in r.text
        assert "localhost" not in r.text
        assert r.redactions_applied == 1

    def test_multiline_flow(self) -> None:
        text = "config: {\n  host: localhost,\n  port: 5432\n}\n"
        r = assert_redact_result(redact_yaml(text))
        assert "config:" in r.text
        assert "localhost" not in r.text
        assert r.redactions_applied == 1

    def test_flow_bracket_in_quoted_string(self) -> None:
        """Regression: } inside quoted string does not affect depth."""
        text = 'config: {"key": "val}ue"}\n'
        r = assert_redact_result(redact_yaml(text))
        assert "config:" in r.text
        assert r.redactions_applied == 1

    # --- Sequences ---

    def test_sequence_items(self) -> None:
        text = "items:\n  - first\n  - second\n"
        r = assert_redact_result(redact_yaml(text))
        assert "first" not in r.text
        assert "second" not in r.text
        assert r.redactions_applied == 2

    def test_sequence_with_mapping(self) -> None:
        text = "- name: John\n  age: 30\n"
        r = assert_redact_result(redact_yaml(text))
        assert "name:" in r.text
        assert "John" not in r.text
        assert "age:" in r.text
        assert r.redactions_applied == 2

    def test_bare_sequence_marker(self) -> None:
        """Bare '- ' with no value -- preserved."""
        r = assert_redact_result(redact_yaml("items:\n  - \n"))
        assert r.redactions_applied == 0

    # --- Document markers ---

    def test_document_markers_preserved(self) -> None:
        text = "---\nkey: value\n...\n"
        r = assert_redact_result(redact_yaml(text))
        assert "---" in r.text
        assert "..." in r.text
        assert r.redactions_applied == 1

    # --- Edge cases ---

    def test_empty_input(self) -> None:
        r = assert_redact_result(redact_yaml(""))
        assert r.redactions_applied == 0

    def test_whitespace_only(self) -> None:
        r = assert_redact_result(redact_yaml("  \n  \n"))
        assert r.redactions_applied == 0

    def test_partial_document(self) -> None:
        """Excerpt starting mid-file -- works because line-oriented."""
        text = "  host: localhost\n  port: 5432\n"
        r = assert_redact_result(redact_yaml(text))
        assert r.redactions_applied == 2

    def test_trailing_newline_preserved(self) -> None:
        r = assert_redact_result(redact_yaml("key: value\n"))
        assert r.text.endswith("\n")

    def test_no_trailing_newline_preserved(self) -> None:
        r = assert_redact_result(redact_yaml("key: value"))
        assert not r.text.endswith("\n")

    def test_unrecognized_line_preserved(self) -> None:
        """Lines that don't match any pattern pass through."""
        text = "}\nkey: value\n"
        r = assert_redact_result(redact_yaml(text))
        assert "}" in r.text
        assert r.redactions_applied == 1

    def test_hash_in_flow_scalar(self) -> None:
        """Hash inside unquoted scalar is not a comment."""
        r = assert_redact_result(redact_yaml("config: {color: red#ff0000}\n"))
        assert "config:" in r.text
        assert r.redactions_applied == 1

    def test_multi_document_state_reset(self) -> None:
        text = "---\nkey1: val1\n---\nkey2: val2\n"
        r = assert_redact_result(redact_yaml(text))
        assert "---" in r.text
        assert "key1:" in r.text
        assert "key2:" in r.text
        assert r.redactions_applied == 2

    def test_tag_preserved_value_redacted(self) -> None:
        r = assert_redact_result(redact_yaml("key: !!str SECRET\n"))
        assert "key:" in r.text
        assert "SECRET" not in r.text
        assert r.redactions_applied == 1
