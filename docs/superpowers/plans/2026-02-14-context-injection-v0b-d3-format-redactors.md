# Context Injection v0b D3: Format Redactors Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the `UNSUPPORTED_CONFIG_FORMAT` suppression path for JSON, YAML, and TOML files with format-aware redactors that preserve structural keys while redacting values.

**Architecture:** Three format redactors added to `redact_formats.py`, each following the established pattern: take `text: str`, return `FormatRedactOutcome`. None use full parsers — these operate on 40-line excerpt windows that won't parse as complete documents. JSON uses a streaming token scanner (character-by-character state machine tracking string/number/keyword contexts). YAML uses a 2-state machine with `find_mapping_colon()` predicate and 5 lexical guard states for bracket counting in flow collections. TOML uses line-oriented `key = value` detection with 4 string states for multi-line awareness. JSON fails closed on desync: `FormatSuppressed(reason="json_scanner_desync")`. YAML and TOML have no desync path — unrecognized lines pass through to the generic token backstop. Each task also wires its redactor into `_dispatch_format()` and incrementally removes the format from the `test_unsupported_config_suppressed` parametrization.

**Tech Stack:** Python 3.14, pytest, ruff, dataclasses (frozen), StrEnum

**Reference:** `docs/plans/2026-02-13-context-injection-v0b-master-plan.md` (Tasks 4, 5, 6-TOML)

**Branch:** Create `feature/context-injection-v0b-d3` from `main`.

**Test command:** `cd packages/context-injection && uv run pytest`

**Dependencies between tasks:**
- Task 1 (JSON scanner): independent
- Task 2 (YAML state machine): independent (parallel-safe with Task 1)
- Task 3 (TOML redactor): independent (parallel-safe with Tasks 1-2)

Each task is self-contained: redactor implementation + dispatch wiring + test file + integration test updates. No cross-task dependencies.

---

### Task 1: JSON Streaming Scanner (master plan Task 4)

**Files:**
- Create: `packages/context-injection/tests/test_redact_json.py`
- Modify: `packages/context-injection/context_injection/redact_formats.py`
- Modify: `packages/context-injection/context_injection/redact.py:14-19,150-163` (imports + dispatch)
- Modify: `packages/context-injection/tests/test_redact.py:302-303` (parametrize list)

**Key design decision:** Key-vs-value discrimination uses colon lookahead — after reading a string token, skip whitespace and check if the next character is `:`. If yes, the string is a key (preserve). If no, the string is a value (redact). This works for well-formed JSON because values are never followed by `:`. Limitation: comments between key and colon in JSONC cause misclassification (key treated as value); generic token pass is backstop.

**Step 1: Write the failing tests**

Create `packages/context-injection/tests/test_redact_json.py`:

```python
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
        assert "// comment" in r.text
        assert "secret" not in r.text
        assert r.redactions_applied == 1

    def test_jsonc_block_comment(self) -> None:
        text = '{"key": /* inline */ "secret"}'
        r = assert_redact_result(redact_json(text))
        assert "/* inline */" in r.text
        assert "secret" not in r.text
        assert r.redactions_applied == 1

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
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/context-injection && uv run pytest tests/test_redact_json.py -v 2>&1 | head -5`
Expected: FAIL — `ImportError: cannot import name 'redact_json'`

**Step 3: Write the implementation**

Add to the end of `packages/context-injection/context_injection/redact_formats.py` (after the `_split_ini_kv` function at line 229):

```python


# --- JSON/JSONC redactor ---


def redact_json(text: str) -> FormatRedactOutcome:
    """Redact values in JSON/JSONC format.

    Streaming token scanner: preserves object keys, redacts all value tokens
    (strings, numbers, booleans, null). Handles JSONC extensions (// line
    comments, /* block comments). Tolerates partial documents at both
    boundaries (excerpt windows).

    Key detection: after reading a string, skip whitespace and check if next
    char is ``:``. If yes → key (preserve). If no → value (redact).

    On unrecoverable scanner state: FormatSuppressed(reason="json_scanner_desync").
    """
    if not text.strip():
        return FormatRedactResult(text=text, redactions_applied=0)

    out: list[str] = []
    redactions = 0
    i = 0
    n = len(text)

    while i < n:
        ch = text[i]

        # Whitespace — preserve
        if ch in " \t\n\r":
            out.append(ch)
            i += 1
            continue

        # JSONC line comment: //
        if ch == "/" and i + 1 < n and text[i + 1] == "/":
            j = i + 2
            while j < n and text[j] != "\n":
                j += 1
            out.append(text[i:j])
            i = j
            continue

        # JSONC block comment: /* ... */
        if ch == "/" and i + 1 < n and text[i + 1] == "*":
            j = i + 2
            while j < n and not (text[j] == "*" and j + 1 < n and text[j + 1] == "/"):
                j += 1
            if j < n:
                j += 2  # consume */
            else:
                j = n  # unterminated — partial doc tolerance
            out.append(text[i:j])
            i = j
            continue

        # String literal
        if ch == '"':
            j = i + 1
            while j < n and text[j] != '"':
                if text[j] == "\\":
                    j += 2  # skip escape sequence
                else:
                    j += 1
            if j < n:
                j += 1  # consume closing quote
            # j now past string (or at EOF if unterminated)
            string_text = text[i:j]

            # Lookahead: is next non-whitespace a colon? → key
            k = j
            while k < n and text[k] in " \t\n\r":
                k += 1

            if k < n and text[k] == ":":
                out.append(string_text)  # Preserve key
            else:
                out.append(_REDACTED_VALUE)
                redactions += 1

            i = j
            continue

        # Structural characters
        if ch in "{}[],:":
            out.append(ch)
            i += 1
            continue

        # Number literal (structured: optional -, digits, optional .digits, optional eE[+-]digits)
        if ch == "-" or ch.isdigit():
            j = i
            if text[j] == "-":
                j += 1
                if j >= n or not text[j].isdigit():
                    return FormatSuppressed(reason="json_scanner_desync")
            while j < n and text[j].isdigit():
                j += 1
            if j < n and text[j] == ".":
                j += 1
                while j < n and text[j].isdigit():
                    j += 1
            if j < n and text[j] in "eE":
                j += 1
                if j < n and text[j] in "+-":
                    j += 1
                while j < n and text[j].isdigit():
                    j += 1
            out.append(_REDACTED_VALUE)
            redactions += 1
            i = j
            continue

        # Keyword (true, false, null)
        if ch in "tfn":
            matched_kw = False
            for kw in ("true", "false", "null"):
                if text[i : i + len(kw)] == kw:
                    out.append(_REDACTED_VALUE)
                    redactions += 1
                    i += len(kw)
                    matched_kw = True
                    break
            if matched_kw:
                continue
            # Partial keyword at EOF — tolerate
            j = i
            while j < n and text[j].isalpha():
                j += 1
            if j == n:
                out.append(_REDACTED_VALUE)
                redactions += 1
                i = j
                continue
            return FormatSuppressed(reason="json_scanner_desync")

        # Unrecognized character — desync
        return FormatSuppressed(reason="json_scanner_desync")

    return FormatRedactResult(text="".join(out), redactions_applied=redactions)
```

**Step 4: Run JSON tests to verify they pass**

Run: `cd packages/context-injection && uv run pytest tests/test_redact_json.py -v`
Expected: All ~30 tests PASS

**Step 5: Wire dispatch and update integration tests**

5a. In `packages/context-injection/context_injection/redact.py`, add `redact_json` to the import (line 14-19):

```python
# old:
from context_injection.redact_formats import (
    FormatRedactOutcome,
    FormatSuppressed,
    redact_env,
    redact_ini,
)

# new:
from context_injection.redact_formats import (
    FormatRedactOutcome,
    FormatSuppressed,
    redact_env,
    redact_ini,
    redact_json,
)
```

5b. In `_dispatch_format` (line 162-163), add JSON dispatch:

```python
# old:
    # CONFIG_JSON, CONFIG_YAML, CONFIG_TOML — no D2a redactor yet
    return None

# new:
    if classification == FileKind.CONFIG_JSON:
        return redact_json(text)
    # CONFIG_YAML, CONFIG_TOML — no D3 redactor yet
    return None
```

5c. In `packages/context-injection/tests/test_redact.py`, update parametrize (line 302-303):

```python
# old:
    @pytest.mark.parametrize("kind", [
        FileKind.CONFIG_JSON, FileKind.CONFIG_YAML, FileKind.CONFIG_TOML,
    ])

# new:
    @pytest.mark.parametrize("kind", [
        FileKind.CONFIG_YAML, FileKind.CONFIG_TOML,
    ])
```

5d. In `test_redact.py`, add JSON integration tests after the `test_ini_dispatch` method (~line 322):

```python
    def test_json_dispatch(self) -> None:
        result = redact_text(text='{"key": "secret"}', classification=FileKind.CONFIG_JSON)
        assert isinstance(result, RedactedText)
        assert "secret" not in result.text
        assert result.stats.format_redactions == 1

    def test_json_desync_suppresses(self) -> None:
        result = redact_text(text="{key: value}", classification=FileKind.CONFIG_JSON)
        assert isinstance(result, SuppressedText)
        assert result.reason == SuppressionReason.FORMAT_DESYNC
```

**Step 6: Run full test suite**

Run: `cd packages/context-injection && uv run pytest -v`
Expected: All tests pass (544 existing + ~33 new JSON tests + 2 integration - 1 removed parametrize = ~578)

Run: `ruff check packages/context-injection`
Expected: No errors

**Step 7: Commit**

```bash
git add packages/context-injection/context_injection/redact_formats.py \
       packages/context-injection/context_injection/redact.py \
       packages/context-injection/tests/test_redact_json.py \
       packages/context-injection/tests/test_redact.py
git commit -m "feat(context-injection): add JSON streaming scanner redactor

D3 Task 1: character-by-character scanner for JSON/JSONC.
Preserves object keys, redacts all value tokens (strings, numbers,
booleans, null). Key detection via colon lookahead. JSONC // and /*
comments preserved. Partial document tolerance at both boundaries.
Desync on unrecognized characters -> FormatSuppressed.

Wired into _dispatch_format for FileKind.CONFIG_JSON.
Removes CONFIG_JSON from unsupported config suppression test."
```

---

### Task 2: YAML State Machine (master plan Task 5)

**Files:**
- Create: `packages/context-injection/tests/test_redact_yaml.py`
- Modify: `packages/context-injection/context_injection/redact_formats.py`
- Modify: `packages/context-injection/context_injection/redact.py:14-20,162-163`
- Modify: `packages/context-injection/tests/test_redact.py:302-303`

**Key design decisions:**
1. Key detection uses strict charset regex `[A-Za-z0-9_.-]+` — no quoted-key parsing in v0b. Unrecognized keys pass through to generic token backstop.
2. Block scalar content replaced with single `[REDACTED:value]` marker at content indent. Indicator line (`|`, `>`) preserved.
3. Multi-line flow collections: key line emits `key: [REDACTED:value]`, continuation lines consumed until bracket depth returns to 0.
4. Anchors (`&name`) preserved. Aliases (`*name`) preserved entirely (references, not secrets).
5. Unrecognized lines preserved (lenient for partial documents) — no desync for YAML. The format is too permissive for reliable desync detection.

**Step 1: Write the failing tests**

Create `packages/context-injection/tests/test_redact_yaml.py`:

```python
"""Tests for YAML format redactor."""

from context_injection.redact_formats import (
    FormatRedactResult,
    redact_yaml,
)
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
        """Key with sub-keys below — preserved as-is."""
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
        """host:8080 (no space after colon) is NOT a mapping — it's a value."""
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
        """Anchor with sub-keys below — line preserved."""
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
        """Bare '- ' with no value — preserved."""
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
        """Excerpt starting mid-file — works because line-oriented."""
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
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/context-injection && uv run pytest tests/test_redact_yaml.py -v 2>&1 | head -5`
Expected: FAIL — `ImportError: cannot import name 'redact_yaml'`

**Step 3: Write the implementation**

Add to the end of `packages/context-injection/context_injection/redact_formats.py` (after `redact_json`):

```python


# --- YAML redactor ---


_YAML_KEY_RE = re.compile(
    r"^(\s*(?:-\s+)?)"  # Group 1: indent + optional sequence indicator
    r"([A-Za-z0-9_.-]+)"  # Group 2: unquoted key
    r"(\s*:(?:\s|$))"  # Group 3: colon + (space or EOL)
)

_BLOCK_SCALAR_RE = re.compile(r"^[|>][+-]?[0-9]?$")


def redact_yaml(text: str) -> FormatRedactOutcome:
    """Redact values in YAML format.

    Line-oriented processor with block-scalar tracking and flow-collection
    depth counting. Uses ``find_mapping_colon()`` (regex) for key detection
    with strict key charset ``[A-Za-z0-9_.-]+``.

    State check ordering (load-bearing): block-scalar → flow → mapping → sequence.
    """
    if not text.strip():
        return FormatRedactResult(text=text, redactions_applied=0)

    lines = text.splitlines()
    result: list[str] = []
    redactions = 0

    in_block_scalar = False
    block_scalar_indent = -1
    block_content_emitted = False

    flow_depth = 0

    for line in lines:
        stripped = line.strip()
        indent = len(line) - len(line.lstrip()) if stripped else 0

        # --- State 1: Block scalar ---
        if in_block_scalar:
            if stripped and indent <= block_scalar_indent:
                # Dedent on non-empty line: exit block scalar
                in_block_scalar = False
                block_content_emitted = False
                # Fall through to process this line normally
            else:
                # Content line or empty line within block scalar
                if not block_content_emitted and stripped:
                    result.append(f"{' ' * indent}{_REDACTED_VALUE}")
                    redactions += 1
                    block_content_emitted = True
                elif not stripped:
                    pass  # consume empty line
                # else: subsequent content line, skip
                continue

        # --- State 2: Flow collection ---
        if flow_depth > 0:
            depth_change = _yaml_bracket_depth(stripped)
            flow_depth += depth_change
            if flow_depth <= 0:
                flow_depth = 0
            continue

        # --- Comment ---
        if stripped.startswith("#"):
            result.append(line)
            continue

        # --- Document markers ---
        if stripped in ("---", "..."):
            result.append(line)
            continue

        # --- Mapping detection ---
        m = _YAML_KEY_RE.match(line)
        if m:
            key_end = m.end()
            key_prefix = line[:key_end]
            value_part = line[key_end:]
            value_stripped = value_part.strip()

            # Block scalar indicator?
            if value_stripped and _BLOCK_SCALAR_RE.match(value_stripped):
                in_block_scalar = True
                block_scalar_indent = indent
                block_content_emitted = False
                result.append(line)
                continue

            # Flow collection start?
            if value_stripped and value_stripped[0] in "{[":
                depth = _yaml_bracket_depth(value_stripped)
                if depth > 0:
                    flow_depth = depth
                result.append(f"{key_prefix}{_REDACTED_VALUE}")
                redactions += 1
                continue

            # Anchor?
            if value_stripped.startswith("&"):
                parts = value_stripped.split(None, 1)
                anchor = parts[0]
                if len(parts) > 1:
                    result.append(f"{key_prefix}{anchor} {_REDACTED_VALUE}")
                    redactions += 1
                else:
                    result.append(line)  # Anchor with no inline value
                continue

            # Alias?
            if value_stripped.startswith("*"):
                result.append(line)
                continue

            # Regular value
            if value_stripped:
                result.append(f"{key_prefix}{_REDACTED_VALUE}")
                redactions += 1
            else:
                result.append(line)  # Key with no value (sub-keys below)
            continue

        # --- Sequence item ---
        seq_match = re.match(r"^(\s*-\s+)(.*)", line)
        if seq_match:
            prefix, value = seq_match.groups()
            value_stripped = value.strip()
            if value_stripped:
                if value_stripped.startswith("*"):
                    result.append(line)  # Alias in sequence
                elif value_stripped[0] in "{[":
                    depth = _yaml_bracket_depth(value_stripped)
                    if depth > 0:
                        flow_depth = depth
                    result.append(f"{prefix}{_REDACTED_VALUE}")
                    redactions += 1
                else:
                    result.append(f"{prefix}{_REDACTED_VALUE}")
                    redactions += 1
            else:
                result.append(line)  # Bare sequence marker
            continue

        # --- Unrecognized line ---
        result.append(line)

    redacted = "\n".join(result)
    if text.endswith("\n"):
        redacted += "\n"

    return FormatRedactResult(text=redacted, redactions_applied=redactions)


def _yaml_bracket_depth(text: str) -> int:
    """Count net bracket depth change, respecting quotes and comments.

    5 lexical guard states: in_single_quote, in_double_quote, double_escape,
    in_line_comment (# to EOL), in_block_scalar (outer state, not tracked here).
    """
    depth = 0
    in_single = False
    in_double = False
    i = 0
    while i < len(text):
        ch = text[i]
        if in_single:
            if ch == "'":
                in_single = False
        elif in_double:
            if ch == "\\":
                i += 1  # skip escaped char (double_escape guard)
            elif ch == '"':
                in_double = False
        elif ch == "#" and (i == 0 or text[i - 1] in " \t"):
            break  # in_line_comment guard: # is comment only after whitespace/BOL
        elif ch == "'":
            in_single = True
        elif ch == '"':
            in_double = True
        elif ch in "{[":
            depth += 1
        elif ch in "}]":
            depth -= 1
        i += 1
    return depth
```

**Step 4: Run YAML tests to verify they pass**

Run: `cd packages/context-injection && uv run pytest tests/test_redact_yaml.py -v`
Expected: All ~30 tests PASS

**Step 5: Wire dispatch and update integration tests**

5a. In `redact.py`, add `redact_yaml` to the import:

```python
# old:
from context_injection.redact_formats import (
    FormatRedactOutcome,
    FormatSuppressed,
    redact_env,
    redact_ini,
    redact_json,
)

# new:
from context_injection.redact_formats import (
    FormatRedactOutcome,
    FormatSuppressed,
    redact_env,
    redact_ini,
    redact_json,
    redact_yaml,
)
```

5b. In `_dispatch_format`, add YAML dispatch (after the JSON branch):

```python
# old:
    if classification == FileKind.CONFIG_JSON:
        return redact_json(text)
    # CONFIG_YAML, CONFIG_TOML — no D3 redactor yet
    return None

# new:
    if classification == FileKind.CONFIG_JSON:
        return redact_json(text)
    if classification == FileKind.CONFIG_YAML:
        return redact_yaml(text)
    # CONFIG_TOML — no D3 redactor yet
    return None
```

5c. In `test_redact.py`, update parametrize:

```python
# old:
    @pytest.mark.parametrize("kind", [
        FileKind.CONFIG_YAML, FileKind.CONFIG_TOML,
    ])

# new:
    @pytest.mark.parametrize("kind", [
        FileKind.CONFIG_TOML,
    ])
```

5d. In `test_redact.py`, add YAML integration test:

```python
    def test_yaml_dispatch(self) -> None:
        result = redact_text(text="host: secret_host\n", classification=FileKind.CONFIG_YAML)
        assert isinstance(result, RedactedText)
        assert "secret_host" not in result.text
        assert result.stats.format_redactions == 1
```

**Step 6: Run full test suite**

Run: `cd packages/context-injection && uv run pytest -v`
Expected: All tests pass (~578 existing + ~33 new YAML + 1 integration = ~612)

Run: `ruff check packages/context-injection`
Expected: No errors

**Step 7: Commit**

```bash
git add packages/context-injection/context_injection/redact_formats.py \
       packages/context-injection/context_injection/redact.py \
       packages/context-injection/tests/test_redact_yaml.py \
       packages/context-injection/tests/test_redact.py
git commit -m "feat(context-injection): add YAML state machine redactor

D3 Task 2: line-oriented processor with block-scalar tracking,
flow-collection depth counting (5 lexical guard states), and
find_mapping_colon() key detection. Preserves anchors/aliases.
Block scalar content collapsed to single redaction marker.
Multi-line flows consumed until bracket depth returns to zero.

Wired into _dispatch_format for FileKind.CONFIG_YAML.
Removes CONFIG_YAML from unsupported config suppression test."
```

---

### Task 3: TOML Redactor (master plan Task 6-TOML)

**Files:**
- Create: `packages/context-injection/tests/test_redact_toml.py`
- Modify: `packages/context-injection/context_injection/redact_formats.py`
- Modify: `packages/context-injection/context_injection/redact.py:14-21,164-165`
- Modify: `packages/context-injection/tests/test_redact.py:302-308`

**Key design decisions:**
1. First `=` in the line is always the key-value separator. TOML bare keys can't contain `=`. Quoted keys with `=` inside are an accepted edge case — generic token pass is backstop.
2. Multi-line strings (`"""`, `'''`) tracked across lines. Content lines consumed, single redaction counted at opening line.
3. Multi-line arrays and inline tables NOT tracked (value on opening line redacted, continuation lines pass through as unrecognized). Generic token pass is backstop.
4. Orphaned closing triple-quote (appears on a non-key-value line when not in multi-line state) → skip the line and continue processing. Indicates excerpt starts inside a multi-line string; prior lines were already processed (some redacted, some preserved for backstop). No desync/suppression — treating excerpt boundary artifacts as "assume prior state" is more appropriate than "parse error" for 40-line windows.

**Step 1: Write the failing tests**

Create `packages/context-injection/tests/test_redact_toml.py`:

```python
"""Tests for TOML format redactor."""

from context_injection.redact_formats import redact_toml
from tests.redaction_harness import assert_redact_result

_RV = "[REDACTED:value]"


class TestRedactToml:
    # --- Basic key=value ---

    def test_basic_string_value(self) -> None:
        r = assert_redact_result(redact_toml('host = "localhost"\n'))
        assert "host =" in r.text
        assert "localhost" not in r.text
        assert r.redactions_applied == 1

    def test_integer_value(self) -> None:
        r = assert_redact_result(redact_toml("port = 5432\n"))
        assert "port =" in r.text
        assert "5432" not in r.text

    def test_boolean_value(self) -> None:
        r = assert_redact_result(redact_toml("debug = true\n"))
        assert "debug =" in r.text
        assert "true" not in r.text

    def test_multiple_keys(self) -> None:
        text = 'host = "localhost"\nport = 5432\n'
        r = assert_redact_result(redact_toml(text))
        assert r.redactions_applied == 2

    def test_no_space_around_equals(self) -> None:
        r = assert_redact_result(redact_toml('key="value"\n'))
        assert "key=" in r.text
        assert r.redactions_applied == 1

    def test_whitespace_after_equals_preserved(self) -> None:
        r = assert_redact_result(redact_toml('key =  "value"\n'))
        assert "key =  " in r.text

    def test_empty_string_value(self) -> None:
        r = assert_redact_result(redact_toml('key = ""\n'))
        assert r.redactions_applied == 1

    def test_dotted_key(self) -> None:
        r = assert_redact_result(redact_toml('server.host = "localhost"\n'))
        assert "server.host =" in r.text
        assert "localhost" not in r.text

    # --- Structure preserved ---

    def test_table_header_preserved(self) -> None:
        text = '[database]\nhost = "localhost"\n'
        r = assert_redact_result(redact_toml(text))
        assert "[database]" in r.text
        assert r.redactions_applied == 1

    def test_array_of_tables_preserved(self) -> None:
        text = '[[servers]]\nname = "alpha"\n'
        r = assert_redact_result(redact_toml(text))
        assert "[[servers]]" in r.text
        assert r.redactions_applied == 1

    def test_comment_preserved(self) -> None:
        text = '# Database config\nhost = "localhost"\n'
        r = assert_redact_result(redact_toml(text))
        assert "# Database config" in r.text
        assert r.redactions_applied == 1

    # --- Multi-line strings ---

    def test_multiline_basic_string(self) -> None:
        text = 'desc = """\nLine one\nLine two\n"""\nkey = "val"\n'
        r = assert_redact_result(redact_toml(text))
        assert "Line one" not in r.text
        assert "Line two" not in r.text
        assert "key =" in r.text
        assert r.redactions_applied == 2

    def test_multiline_literal_string(self) -> None:
        text = "desc = '''\nLine one\nLine two\n'''\nkey = 'val'\n"
        r = assert_redact_result(redact_toml(text))
        assert "Line one" not in r.text
        assert r.redactions_applied == 2

    def test_same_line_triple_quote(self) -> None:
        """Triple-quoted string opening and closing on same line."""
        r = assert_redact_result(redact_toml('key = """value"""\n'))
        assert "value" not in r.text
        assert r.redactions_applied == 1

    def test_eof_in_multiline_no_desync(self) -> None:
        """Excerpt ends inside multi-line string — normal for windows."""
        result = redact_toml('key = """\nunclosed content')
        assert isinstance(result, FormatRedactResult)

    # --- Complex values ---

    def test_inline_table(self) -> None:
        r = assert_redact_result(redact_toml("point = {x = 1, y = 2}\n"))
        assert "point =" in r.text
        assert r.redactions_applied == 1

    def test_array_value(self) -> None:
        r = assert_redact_result(redact_toml("ports = [8080, 443, 80]\n"))
        assert "ports =" in r.text
        assert "8080" not in r.text

    # --- Orphaned triple-quote (mid-excerpt) ---

    def test_orphaned_triple_quote_continues(self) -> None:
        """Closing triple-quote without opener → assume prior multiline, continue."""
        text = 'leftover content\n"""\nkey = "val"\n'
        r = assert_redact_result(redact_toml(text))
        assert "key =" in r.text
        assert "val" not in r.text
        assert r.redactions_applied >= 1

    def test_orphaned_literal_triple_quote_continues(self) -> None:
        text = "leftover\n'''\nkey = 'val'\n"
        r = assert_redact_result(redact_toml(text))
        assert "key =" in r.text
        assert r.redactions_applied >= 1

    def test_multiline_array_continuation_passthrough(self) -> None:
        """Multi-line array: opening line redacted, continuations pass through.

        Known limitation — continuation lines are not tracked. Generic token
        backstop handles any secrets in continuation lines.
        """
        text = "ports = [\n  8080,\n  443\n]\nkey = 'val'\n"
        r = assert_redact_result(redact_toml(text))
        assert "ports =" in r.text
        assert "key =" in r.text

    # --- Edge cases ---

    def test_empty_input(self) -> None:
        r = assert_redact_result(redact_toml(""))
        assert r.redactions_applied == 0

    def test_whitespace_only(self) -> None:
        r = assert_redact_result(redact_toml("  \n  \n"))
        assert r.redactions_applied == 0

    def test_trailing_newline_preserved(self) -> None:
        r = assert_redact_result(redact_toml('key = "val"\n'))
        assert r.text.endswith("\n")

    def test_no_trailing_newline_preserved(self) -> None:
        r = assert_redact_result(redact_toml('key = "val"'))
        assert not r.text.endswith("\n")

    def test_unrecognized_line_preserved(self) -> None:
        """Lines without = that don't match any pattern pass through."""
        text = "some random text\nkey = val\n"
        r = assert_redact_result(redact_toml(text))
        assert "some random text" in r.text
        assert r.redactions_applied == 1
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/context-injection && uv run pytest tests/test_redact_toml.py -v 2>&1 | head -5`
Expected: FAIL — `ImportError: cannot import name 'redact_toml'`

**Step 3: Write the implementation**

Add to the end of `packages/context-injection/context_injection/redact_formats.py` (after `_yaml_bracket_depth`):

```python


# --- TOML redactor ---


_TOML_TABLE_RE = re.compile(r"^\s*\[")


def redact_toml(text: str) -> FormatRedactOutcome:
    """Redact values in TOML format.

    Line-oriented ``key = value`` matching with multi-line string awareness.
    Tracks triple-quote delimiters (``\"\"\"``, ``'''``) across lines.
    Table headers and comments preserved. Orphaned closing triple-quote
    without opener treated as excerpt boundary artifact (skip and continue
    processing) — not desync. Prior lines already processed by earlier
    pattern branches; subsequent lines processed normally.

    EOF inside multi-line string is normal (excerpt window tolerance).
    """
    if not text.strip():
        return FormatRedactResult(text=text, redactions_applied=0)

    lines = text.splitlines()
    result: list[str] = []
    redactions = 0

    in_multiline: str | None = None  # '"""' or "'''" when active

    for line in lines:
        stripped = line.strip()

        # Multi-line string continuation
        if in_multiline is not None:
            if in_multiline in stripped:
                in_multiline = None
            continue

        # Empty line
        if not stripped:
            result.append(line)
            continue

        # Comment
        if stripped.startswith("#"):
            result.append(line)
            continue

        # Table header ([table] or [[array]])
        if _TOML_TABLE_RE.match(line):
            result.append(line)
            continue

        # Key-value pair: first = is the separator
        eq_idx = stripped.find("=")
        if eq_idx > 0:
            key_part_stripped = stripped[:eq_idx]
            if key_part_stripped.rstrip():  # non-empty key
                # Map back to original line indentation
                orig_indent = len(line) - len(line.lstrip())
                abs_eq_idx = orig_indent + eq_idx

                key_part = line[: abs_eq_idx + 1]  # includes =
                value_part = line[abs_eq_idx + 1 :]
                value_stripped = value_part.strip()

                # Check for multi-line string opening
                for delim in ('"""', "'''"):
                    if delim in value_stripped:
                        after_open = value_stripped[value_stripped.index(delim) + 3 :]
                        if delim not in after_open:
                            in_multiline = delim
                        break

                # Preserve whitespace between = and value
                ws = value_part[: len(value_part) - len(value_part.lstrip())]
                result.append(f"{key_part}{ws}{_REDACTED_VALUE}")
                redactions += 1
                continue

        # Orphaned closing triple-quote (mid-excerpt boundary artifact)
        # Excerpt started inside a multi-line string. Prior lines were
        # already processed (some redacted, some preserved for backstop).
        # Skip the closing delimiter and continue processing normally.
        orphaned = False
        for delim in ('"""', "'''"):
            if delim in stripped:
                orphaned = True
                break
        if orphaned:
            continue

        # Unrecognized line — preserve (lenient for partial docs)
        result.append(line)

    redacted = "\n".join(result)
    if text.endswith("\n"):
        redacted += "\n"

    return FormatRedactResult(text=redacted, redactions_applied=redactions)
```

**Step 4: Run TOML tests to verify they pass**

Run: `cd packages/context-injection && uv run pytest tests/test_redact_toml.py -v`
Expected: All ~25 tests PASS

**Step 5: Wire dispatch and update integration tests**

5a. In `redact.py`, add `redact_toml` to the import:

```python
# old:
from context_injection.redact_formats import (
    FormatRedactOutcome,
    FormatSuppressed,
    redact_env,
    redact_ini,
    redact_json,
    redact_yaml,
)

# new:
from context_injection.redact_formats import (
    FormatRedactOutcome,
    FormatSuppressed,
    redact_env,
    redact_ini,
    redact_json,
    redact_toml,
    redact_yaml,
)
```

5b. In `_dispatch_format`, add TOML dispatch and remove the comment:

```python
# old:
    if classification == FileKind.CONFIG_JSON:
        return redact_json(text)
    if classification == FileKind.CONFIG_YAML:
        return redact_yaml(text)
    # CONFIG_TOML — no D3 redactor yet
    return None

# new:
    if classification == FileKind.CONFIG_JSON:
        return redact_json(text)
    if classification == FileKind.CONFIG_YAML:
        return redact_yaml(text)
    if classification == FileKind.CONFIG_TOML:
        return redact_toml(text)
    return None
```

5c. In `test_redact.py`, **remove** the entire `test_unsupported_config_suppressed` method (lines 302-308) and replace with a comprehensive check:

```python
    # --- All config formats handled ---

    def test_all_config_kinds_dispatched(self) -> None:
        """No config kind triggers UNSUPPORTED_CONFIG_FORMAT suppression."""
        for kind in FileKind:
            if kind.is_config:
                result = redact_text(text="key = value\n", classification=kind)
                if isinstance(result, SuppressedText):
                    assert result.reason != SuppressionReason.UNSUPPORTED_CONFIG_FORMAT, (
                        f"{kind} still triggers UNSUPPORTED_CONFIG_FORMAT"
                    )
```

5d. Add TOML integration tests:

```python
    def test_toml_dispatch(self) -> None:
        result = redact_text(text='key = "secret"\n', classification=FileKind.CONFIG_TOML)
        assert isinstance(result, RedactedText)
        assert "secret" not in result.text
        assert result.stats.format_redactions == 1

    def test_toml_orphaned_close_still_redacts(self) -> None:
        """Orphaned triple-quote is an excerpt boundary artifact, not desync."""
        result = redact_text(
            text='orphaned\n"""\nkey = "val"\n', classification=FileKind.CONFIG_TOML,
        )
        assert isinstance(result, RedactedText)
        assert "val" not in result.text
```

**Step 6: Run full test suite**

Run: `cd packages/context-injection && uv run pytest -v`
Expected: All tests pass (~612 existing + ~28 new TOML + 2 integration - 1 removed = ~641)

Run: `ruff check packages/context-injection`
Expected: No errors

**Step 7: Commit**

```bash
git add packages/context-injection/context_injection/redact_formats.py \
       packages/context-injection/context_injection/redact.py \
       packages/context-injection/tests/test_redact_toml.py \
       packages/context-injection/tests/test_redact.py
git commit -m "feat(context-injection): add TOML redactor with multiline string awareness

D3 Task 3: line-oriented key=value matching with triple-quote tracking
across lines. Table headers and comments preserved. Orphaned closing
triple-quote treated as excerpt boundary artifact (skip and continue),
not desync. EOF inside multiline string tolerated for excerpt windows.

Wired into _dispatch_format for FileKind.CONFIG_TOML.
Removes test_unsupported_config_suppressed entirely — replaced with
test_all_config_kinds_dispatched (no config kind triggers unsupported)."
```

---

## Final Verification

Run: `cd packages/context-injection && uv run pytest -v`
Expected: All tests pass (544 existing + ~94 new ≈ 638 total)

Run: `ruff check packages/context-injection`
Expected: No errors

## Summary of Deliverables

| Module | New/Modified | What This Plan Adds |
|--------|-------------|---------------------|
| `redact_formats.py` | Modified | `redact_json()` (~85 LOC), `redact_yaml()` + `_yaml_bracket_depth()` (~130 LOC), `redact_toml()` (~65 LOC) |
| `redact.py` | Modified | `_dispatch_format` routes JSON/YAML/TOML to new redactors |
| `test_redact_json.py` | New | ~33 tests: scanner, JSONC, partial docs, desync, deep nesting, number DFA |
| `test_redact_yaml.py` | New | ~33 tests: mapping, block scalar, flow, anchors/aliases, sequences, `#` in scalars, multi-document, tags |
| `test_redact_toml.py` | New | ~28 tests: key=value, tables, multiline strings, orphaned close (continue), multiline array passthrough |
| `test_redact.py` | Modified | Removes unsupported parametrize, adds dispatch + desync integration tests, adds `test_all_config_kinds_dispatched` |

## Known Limitations

1. **JSON key detection via lookahead:** Comments between key and colon in JSONC cause the key to be misclassified as a value (over-redaction). Generic token pass is backstop.
2. **YAML quoted keys:** Keys like `"special:key"` don't match the `[A-Za-z0-9_.-]+` charset — line passes through unredacted. Generic token pass is backstop.
3. **YAML unrecognized lines preserved:** Lines that don't match any YAML pattern pass through to generic token backstop. Opaque secrets with non-indicative variable names may survive if not caught by backstop keyword list. Follow-up: expand generic backstop keyword list (separate task, not D3).
4. **TOML multi-line arrays/inline tables:** Not tracked across lines. Opening line value is redacted; continuation lines pass through as unrecognized. Generic token pass is backstop. Tested explicitly: `test_multiline_array_continuation_passthrough`.
5. **TOML quoted keys with `=`:** First `=` in line is always treated as separator. Quoted keys containing `=` cause mis-split. Generic token pass is backstop.
