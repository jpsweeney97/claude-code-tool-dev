# PR #31 Review Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix all 22 findings (C1-C7, I1-I13, T1-T2) from the 5-agent PR review of the deferred work tracking system.

**Architecture:** Fix-forward on `feature/deferred-work-tracking`. Each task is a single commit targeting specific files. Tasks are ordered by dependency: correctness fixes first (Tasks 1-5), then test gaps (Task 6), then code quality (Tasks 7-8). All work in `packages/plugins/handoff/`.

**Tech Stack:** Python 3.12+, PyYAML, pytest, `uv run pytest` from `packages/plugins/handoff/`

**Branch:** `feature/deferred-work-tracking` (continue existing PR #31)

**Test command:** `cd packages/plugins/handoff && uv run pytest`

> **Adversarial review note (line-number drift):** Tasks that add `import` lines (Tasks 3, 4) shift subsequent line numbers by +1. Later tasks (especially Task 7) reference line numbers that become stale after earlier tasks execute. **Implementers must match by code anchors** (e.g., "the `try/except ModuleNotFoundError` import block") not absolute line numbers. Line numbers in this plan are accurate for the pre-edit state of each file, not the post-prior-task state.

---

## Task 1: Fix `_quote()` YAML escaping (C1, C2, I12)

> **Amendment (Codex deep-review, 2026-02-28):** Added `\t`, `\x85` (NEL), `\u2028` (LS), `\u2029` (PS) to trigger set and escape chain for defense against copy-paste from editors. Added 2 round-trip tests for YAML implicit scalar coercion (`"yes"`, `"on"`). `yaml.safe_dump` replacement rejected as scope creep.
>
> **Amendment (Codex adversarial review, 2026-02-28):** CRITICAL: Added `_YAML_IMPLICIT_SCALARS` guard — "yes"/"on"/"true"/"false"/"null"/"~" contain no trigger characters and would pass through unquoted, causing `yaml.safe_load` to coerce them to booleans/None. Without this guard, the deep-review's own round-trip tests fail. Also: add round-trip tests for `\N`/`\L`/`\P` Unicode escapes (untested in deep-review amendment).
>
> **Amendment (Codex adversarial-challenge, 2026-02-28):** (1) `_YAML_IMPLICIT_SCALARS` only covers booleans/null — YAML 1.1 also coerces octals (`"0777"` → `511`) and `.inf`/`.nan` to floats. These contain no trigger characters and pass through unquoted. Added `_YAML_NUMERIC_RE` regex guard for numeric implicit scalars. Note: sexagesimal like `"1:00"` is already caught by `:` trigger character. Added 4 round-trip tests: `"123"`, `"0777"`, `".inf"`, `".nan"`. (2) Test YAML extraction regex `r"```yaml\n(.*?)```"` is fragile (unanchored closing fence). Updated all tests to line-anchored `r"^```yaml\n(.*?)^```"` with `re.MULTILINE | re.DOTALL`.

**Issues:** C1 (`_quote` doesn't escape backslashes), C2 (`_quote` doesn't handle newlines), I12 (`_quote` docstring inaccurate)

**Files:**
- Modify: `scripts/defer.py:92-103`
- Modify: `tests/test_defer.py` — add `TestQuoteEscaping` class

**Context:** `_quote()` is a nested function inside `render_ticket()` at line 92. It wraps YAML values in double quotes when they contain special characters. Currently it only escapes `"` but not `\` or `\n`, which produces invalid YAML for inputs like `C:\Users` (interpreted as `\U` escape) or multiline values.

**Step 1: Write failing tests**

Add after `TestFilenameSlugThreeDigit` class (after line 88) in `tests/test_defer.py`:

```python
class TestQuoteEscaping:
    """C1/C2: _quote must escape backslashes and newlines for valid YAML."""

    def test_backslash_yaml_round_trip(self) -> None:
        import re as re_mod

        import yaml
        from scripts.defer import render_ticket

        candidate = {
            "id": "T-20260228-01",
            "date": "2026-02-28",
            "summary": "Test",
            "problem": "P",
            "source_text": "S",
            "proposed_approach": "A",
            "acceptance_criteria": ["Done"],
            "source_ref": "C:\\Users\\test\\file.py",
        }
        result = render_ticket(candidate)
        yaml_match = re_mod.search(r"^```yaml\n(.*?)^```", result, re_mod.MULTILINE | re_mod.DOTALL)
        assert yaml_match is not None
        parsed = yaml.safe_load(yaml_match.group(1))
        assert parsed["source_ref"] == "C:\\Users\\test\\file.py"

    def test_newline_yaml_round_trip(self) -> None:
        import re as re_mod

        import yaml
        from scripts.defer import render_ticket

        candidate = {
            "id": "T-20260228-01",
            "date": "2026-02-28",
            "summary": "Test",
            "problem": "P",
            "source_text": "S",
            "proposed_approach": "A",
            "acceptance_criteria": ["Done"],
            "source_ref": "line1\nline2",
        }
        result = render_ticket(candidate)
        yaml_match = re_mod.search(r"^```yaml\n(.*?)^```", result, re_mod.MULTILINE | re_mod.DOTALL)
        assert yaml_match is not None
        parsed = yaml.safe_load(yaml_match.group(1))
        assert parsed["source_ref"] == "line1\nline2"

    def test_implicit_yes_yaml_round_trip(self) -> None:
        """Codex amendment: YAML implicit scalar coercion defense."""
        import re as re_mod

        import yaml
        from scripts.defer import render_ticket

        candidate = {
            "id": "T-20260228-01",
            "date": "2026-02-28",
            "summary": "Test",
            "problem": "P",
            "source_text": "S",
            "proposed_approach": "A",
            "acceptance_criteria": ["Done"],
            "source_ref": "yes",
        }
        result = render_ticket(candidate)
        yaml_match = re_mod.search(r"^```yaml\n(.*?)^```", result, re_mod.MULTILINE | re_mod.DOTALL)
        assert yaml_match is not None
        parsed = yaml.safe_load(yaml_match.group(1))
        assert parsed["source_ref"] == "yes"

    def test_implicit_on_yaml_round_trip(self) -> None:
        """Codex amendment: YAML implicit scalar coercion defense."""
        import re as re_mod

        import yaml
        from scripts.defer import render_ticket

        candidate = {
            "id": "T-20260228-01",
            "date": "2026-02-28",
            "summary": "Test",
            "problem": "P",
            "source_text": "S",
            "proposed_approach": "A",
            "acceptance_criteria": ["Done"],
            "branch": "on",
        }
        result = render_ticket(candidate)
        yaml_match = re_mod.search(r"^```yaml\n(.*?)^```", result, re_mod.MULTILINE | re_mod.DOTALL)
        assert yaml_match is not None
        parsed = yaml.safe_load(yaml_match.group(1))
        # "on" must round-trip as the string "on", not boolean True
        assert parsed["branch"] == "on"

    def test_nel_yaml_round_trip(self) -> None:
        """Codex adversarial amendment: Unicode NEL escape must round-trip."""
        import re as re_mod

        import yaml
        from scripts.defer import render_ticket

        candidate = {
            "id": "T-20260228-01",
            "date": "2026-02-28",
            "summary": "Test",
            "problem": "P",
            "source_text": "S",
            "proposed_approach": "A",
            "acceptance_criteria": ["Done"],
            "source_ref": "before\x85after",
        }
        result = render_ticket(candidate)
        yaml_match = re_mod.search(r"^```yaml\n(.*?)^```", result, re_mod.MULTILINE | re_mod.DOTALL)
        assert yaml_match is not None
        parsed = yaml.safe_load(yaml_match.group(1))
        assert parsed["source_ref"] == "before\x85after"

    def test_ls_ps_yaml_round_trip(self) -> None:
        """Codex adversarial amendment: Unicode LS/PS escapes must round-trip."""
        import re as re_mod

        import yaml
        from scripts.defer import render_ticket

        candidate = {
            "id": "T-20260228-01",
            "date": "2026-02-28",
            "summary": "Test",
            "problem": "P",
            "source_text": "S",
            "proposed_approach": "A",
            "acceptance_criteria": ["Done"],
            "source_ref": "ls\u2028ps\u2029end",
        }
        result = render_ticket(candidate)
        yaml_match = re_mod.search(r"^```yaml\n(.*?)^```", result, re_mod.MULTILINE | re_mod.DOTALL)
        assert yaml_match is not None
        parsed = yaml.safe_load(yaml_match.group(1))
        assert parsed["source_ref"] == "ls\u2028ps\u2029end"

    def test_numeric_string_yaml_round_trip(self) -> None:
        """Codex adversarial-challenge: bare numeric strings must round-trip."""
        import re as re_mod

        import yaml
        from scripts.defer import render_ticket

        candidate = {
            "id": "T-20260228-01",
            "date": "2026-02-28",
            "summary": "Test",
            "problem": "P",
            "source_text": "S",
            "proposed_approach": "A",
            "acceptance_criteria": ["Done"],
            "source_ref": "123",
        }
        result = render_ticket(candidate)
        yaml_match = re_mod.search(r"^```yaml\n(.*?)^```", result, re_mod.MULTILINE | re_mod.DOTALL)
        assert yaml_match is not None
        parsed = yaml.safe_load(yaml_match.group(1))
        assert parsed["source_ref"] == "123"

    def test_octal_string_yaml_round_trip(self) -> None:
        """Codex adversarial-challenge: octal-like strings must round-trip as strings."""
        import re as re_mod

        import yaml
        from scripts.defer import render_ticket

        candidate = {
            "id": "T-20260228-01",
            "date": "2026-02-28",
            "summary": "Test",
            "problem": "P",
            "source_text": "S",
            "proposed_approach": "A",
            "acceptance_criteria": ["Done"],
            "source_ref": "0777",
        }
        result = render_ticket(candidate)
        yaml_match = re_mod.search(r"^```yaml\n(.*?)^```", result, re_mod.MULTILINE | re_mod.DOTALL)
        assert yaml_match is not None
        parsed = yaml.safe_load(yaml_match.group(1))
        assert parsed["source_ref"] == "0777"

    def test_inf_string_yaml_round_trip(self) -> None:
        """Codex adversarial-challenge: .inf must round-trip as string."""
        import re as re_mod

        import yaml
        from scripts.defer import render_ticket

        candidate = {
            "id": "T-20260228-01",
            "date": "2026-02-28",
            "summary": "Test",
            "problem": "P",
            "source_text": "S",
            "proposed_approach": "A",
            "acceptance_criteria": ["Done"],
            "source_ref": ".inf",
        }
        result = render_ticket(candidate)
        yaml_match = re_mod.search(r"^```yaml\n(.*?)^```", result, re_mod.MULTILINE | re_mod.DOTALL)
        assert yaml_match is not None
        parsed = yaml.safe_load(yaml_match.group(1))
        assert parsed["source_ref"] == ".inf"

    def test_nan_string_yaml_round_trip(self) -> None:
        """Codex adversarial-challenge: .nan must round-trip as string."""
        import re as re_mod

        import yaml
        from scripts.defer import render_ticket

        candidate = {
            "id": "T-20260228-01",
            "date": "2026-02-28",
            "summary": "Test",
            "problem": "P",
            "source_text": "S",
            "proposed_approach": "A",
            "acceptance_criteria": ["Done"],
            "source_ref": ".nan",
        }
        result = render_ticket(candidate)
        yaml_match = re_mod.search(r"^```yaml\n(.*?)^```", result, re_mod.MULTILINE | re_mod.DOTALL)
        assert yaml_match is not None
        parsed = yaml.safe_load(yaml_match.group(1))
        assert parsed["source_ref"] == ".nan"
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_defer.py::TestQuoteEscaping -v`
Expected: FAIL — backslash test fails with YAML parse error, newline test fails with parse error or wrong value

**Step 3: Fix `_quote()` in `defer.py`**

Replace lines 92-103 of `scripts/defer.py`:

```python
    _YAML_IMPLICIT_SCALARS = frozenset({
        "yes", "no", "on", "off", "true", "false", "null", "~",
        "Yes", "No", "On", "Off", "True", "False", "Null",
        "YES", "NO", "ON", "OFF", "TRUE", "FALSE", "NULL",
    })
    _YAML_NUMERIC_RE = re.compile(r'^[-+]?(?:\d|\.(?:inf|nan))', re.IGNORECASE)

    def _quote(val: str) -> str:
        """Quote a YAML string value if it contains YAML-significant characters.

        Handles colons, quotes, braces, backslashes, newlines, YAML
        implicit scalars (yes/no/true/false/null/~ which safe_load coerces),
        and numeric implicit scalars (octals, .inf, .nan which coerce to int/float).
        Values without special characters pass through unquoted.
        """
        if not val:
            return '""'
        if val in _YAML_IMPLICIT_SCALARS or _YAML_NUMERIC_RE.match(val) or any(c in val for c in (':', '#', '{', '}', '[', ']', ',', '&', '*', '?', '|', '-', '<', '>', '=', '!', '%', '@', '`', '"', "'", '\\', '\n', '\r', '\t', '\x85', '\u2028', '\u2029')):
            escaped = val.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t').replace('\x85', '\\N').replace('\u2028', '\\L').replace('\u2029', '\\P')
            return f'"{escaped}"'
        return val
```

Key changes:
- Added `_YAML_NUMERIC_RE` regex guard for YAML 1.1 numeric implicit scalars (octals, .inf, .nan)
- Added `\\`, `\n`, `\r`, `\t`, `\x85`, `\u2028`, `\u2029` to the special character trigger set
- Escape order: backslash first (before `"`), then `"`, then newline/CR, then tab, then Unicode line terminators
- Unicode escapes use YAML named escapes: `\N` (NEL), `\L` (LS), `\P` (PS)
- Docstring rewritten (I12): "YAML-significant characters" replaces inaccurate "leading special chars"

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_defer.py::TestQuoteEscaping -v`
Expected: PASS

**Step 5: Run full test suite**

Run: `cd packages/plugins/handoff && uv run pytest`
Expected: All tests pass (320+)

**Step 6: Commit**

```
git add scripts/defer.py tests/test_defer.py
git commit -m "fix(handoff): escape backslash and newline in _quote for valid YAML (C1, C2, I12)"
```

---

## Task 2: Fix SKILL.md documentation (C6, C7, I13)

**Issues:** C6 (defer SKILL.md missing `critical` priority), C7 (triage SKILL.md stale regex patterns), I13 (30-day lookback undocumented)

**Files:**
- Modify: `skills/defer/SKILL.md:63`
- Modify: `skills/triage/SKILL.md:140,224`

**Step 1: Fix priority enum in defer SKILL.md**

In `skills/defer/SKILL.md`, line 63, replace:

```
| `priority` | `high`, `medium`, or `low` | Yes (default: `medium`) |
```

with:

```
| `priority` | `critical`, `high`, `medium`, or `low` | Yes (default: `medium`) |
```

**Step 2: Fix regex patterns in triage SKILL.md**

In `skills/triage/SKILL.md`, line 140, replace:

```
2. **id_ref** -- handoff text contains a ticket ID matching regex patterns: `T-\d{8}-\d{2}` (new format), `T-\d{3}` (legacy numeric), `T-[A-F]` (legacy alpha), `handoff-\w+` (legacy noun).
```

with:

```
2. **id_ref** -- handoff text contains a ticket ID matching regex patterns: `T-\d{8}-\d{2,}` (new format, 2+ digit sequence), `T-\d{3}` (legacy numeric), `T-[A-F]` (legacy alpha), `handoff-[\w-]+` (legacy noun, supports hyphens).
```

**Step 3: Add 30-day lookback note to triage SKILL.md**

In `skills/triage/SKILL.md`, after the Step 1 code block (after line 29), add:

```
Note: handoff scanning is limited to files modified within the last 30 days. Older handoffs are excluded from the orphan scan.
```

**Step 4: Commit**

```
git add skills/defer/SKILL.md skills/triage/SKILL.md
git commit -m "docs(handoff): fix SKILL.md priority enum, regex patterns, and lookback note (C6, C7, I13)"
```

---

## Task 3: Add parse_ticket failure diagnostics (C3, C5)

> **Amendment (Codex deep-review, 2026-02-28):** (1) Added `MALFORMED_YAML` constant definition — was referenced but undefined. (2) Changed malformed YAML test assertion from `>= 1` to exactly 2 warnings, making the double-warning (one from `parse_yaml_frontmatter`, one from `parse_ticket`) an intentional, documented design choice. (3) Added code comment in implementation noting double-warning intent.
>
> **Amendment (Codex adversarial-challenge, 2026-02-28):** (1) `test_warns_on_schema_validation_with_errors` assertion `any("status" in ...)` is brittle — depends on `validate_schema` including field name in error text. Changed to assert on stable prefix `"Schema validation failed for"`. (2) Double-warning stacklevel design is coherent but non-obvious: `parse_yaml_frontmatter` `stacklevel=2` blames `parse_ticket`, while `parse_ticket` `stacklevel=2` blames the caller — different frames for the two warnings. Added documentation comment noting intentional frame split.

**Issues:** C3 (`parse_ticket` returns None for 4 failure modes with no diagnostics), C5 (`yaml.YAMLError` discards line/column info)

**Files:**
- Modify: `scripts/ticket_parsing.py:1,57-60,110-125`
- Modify: `tests/test_ticket_parsing.py` — add `TestParseTicketWarnings` class

**Prereqs:** `MALFORMED_YAML` constant must be defined before the test class (see Step 1 below). `Path` must be imported at module level in the test file (already exists in `test_ticket_parsing.py`).

**Context:** `parse_ticket` is the foundational parser called by `allocate_id`, `read_open_tickets`, and `_load_tickets_for_matching`. Currently it returns `None` for 4 distinct failures with zero diagnostic info. `validate_schema` computes a rich error list then throws it away. `yaml.YAMLError` has line/column info that's also discarded.

**Step 1: Write failing tests**

Add at end of `tests/test_ticket_parsing.py`. First, add the `MALFORMED_YAML` constant before the class:

```python
MALFORMED_YAML = '# Bad\n\n```yaml\nid: T-1\ndate: [invalid\n```\n\n## Problem\n\nBad YAML.'
```

Then add the test class:

```python
class TestParseTicketWarnings:
    """C3/C5: parse_ticket must emit warnings with diagnostic info for each failure mode."""

    def test_warns_on_unreadable_file(self, tmp_path: Path) -> None:
        import warnings

        from scripts.ticket_parsing import parse_ticket

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = parse_ticket(tmp_path / "nonexistent.md")
        assert result is None
        assert len(w) == 1
        assert "Cannot read" in str(w[0].message)

    def test_warns_on_no_yaml_block(self, tmp_path: Path) -> None:
        import warnings

        from scripts.ticket_parsing import parse_ticket

        (tmp_path / "no-yaml.md").write_text("# Just text\n\nNo YAML here.")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = parse_ticket(tmp_path / "no-yaml.md")
        assert result is None
        assert len(w) == 1
        assert "No fenced YAML" in str(w[0].message)

    def test_warns_on_malformed_yaml_with_detail(self, tmp_path: Path) -> None:
        import warnings

        from scripts.ticket_parsing import parse_ticket

        (tmp_path / "bad.md").write_text(MALFORMED_YAML)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = parse_ticket(tmp_path / "bad.md")
        assert result is None
        # Exactly 2 warnings: one from parse_yaml_frontmatter (YAML detail),
        # one from parse_ticket (file path context). This double-warning is
        # intentional — see parse_ticket implementation comment.
        assert len(w) == 2, f"Expected exactly 2 warnings for malformed YAML, got {len(w)}"
        yaml_warns = [x for x in w if "YAML parse error" in str(x.message)]
        path_warns = [x for x in w if "bad.md" in str(x.message)]
        assert len(yaml_warns) == 1, "Should include YAML error detail"
        assert len(path_warns) == 1, "Should include file path context"

    def test_warns_on_schema_validation_with_errors(self, tmp_path: Path) -> None:
        import warnings

        from scripts.ticket_parsing import parse_ticket

        # Missing required 'status' field
        bad_schema = '# Bad\n\n```yaml\nid: T-1\ndate: 2026-02-28\n```\n\n## Problem\n\nNo status.'
        (tmp_path / "schema.md").write_text(bad_schema)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = parse_ticket(tmp_path / "schema.md")
        assert result is None
        assert any("Schema validation failed for" in str(x.message) for x in w), "Should include schema error detail"
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_ticket_parsing.py::TestParseTicketWarnings -v`
Expected: FAIL — no warnings are currently emitted

**Step 3: Add warnings to `ticket_parsing.py`**

Add `import warnings` at the top of `scripts/ticket_parsing.py` (after line 5, before `import re`):

```python
import warnings
```

Replace `parse_yaml_frontmatter`'s except block (lines 57-60):

```python
    try:
        result = yaml.safe_load(yaml_text)
    except yaml.YAMLError as exc:
        warnings.warn(f"YAML parse error: {exc}", stacklevel=2)
        return None
```

Replace `parse_ticket` body (lines 110-131):

```python
def parse_ticket(path: Path) -> TicketFile | None:
    """Parse a ticket markdown file into a TicketFile.

    Returns None if:
    - File doesn't exist or can't be read
    - No fenced YAML block found
    - YAML is malformed
    - Required fields missing (id, date, status)

    Emits warnings with diagnostic detail for each failure mode.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        warnings.warn(f"Cannot read ticket {path}: {exc}", stacklevel=2)
        return None

    yaml_text = extract_fenced_yaml(text)
    if yaml_text is None:
        warnings.warn(f"No fenced YAML block in {path}", stacklevel=2)
        return None

    frontmatter = parse_yaml_frontmatter(yaml_text)
    if frontmatter is None:
        # Intentional double-warning design: parse_yaml_frontmatter warns with
        # stacklevel=2 (blames parse_ticket), this second warning warns with
        # stacklevel=2 (blames the caller). Two warnings, two different frames.
        # Callers see exactly 2 warnings for malformed YAML (tested explicitly).
        warnings.warn(f"Cannot parse frontmatter in {path}", stacklevel=2)
        return None

    errors = validate_schema(frontmatter)
    if errors:
        warnings.warn(
            f"Schema validation failed for {path}: {'; '.join(errors)}",
            stacklevel=2,
        )
        return None

    # Body is everything after the fenced YAML block's closing ```
    m = _FENCED_YAML_RE.search(text)
    body = text[m.end() :].strip() if m else ""

    return TicketFile(path=str(path), frontmatter=frontmatter, body=body)
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_ticket_parsing.py::TestParseTicketWarnings -v`
Expected: PASS

**Step 5: Run full test suite**

Run: `cd packages/plugins/handoff && uv run pytest`
Expected: All tests pass. Some existing tests may now emit warnings (which is expected — they test failure paths). Warnings don't cause test failures.

**Step 6: Commit**

```
git add scripts/ticket_parsing.py tests/test_ticket_parsing.py
git commit -m "fix(handoff): add diagnostic warnings to parse_ticket failure paths (C3, C5)"
```

---

## Task 4: Add warnings to silent failure points (I3, I4, I5, I6, I7)

**Issues:** I3 (provenance JSON parse silent None), I4 (triage silent file skip), I5 (triage silent stat skip), I6 (enum coercion without warning), I7 (inconsistent warning patterns)

**Files:**
- Modify: `scripts/provenance.py:1,20-23,31-34`
- Modify: `scripts/triage.py:239-243,269-272`
- Modify: `scripts/defer.py:38-39,86-90`
- Modify: `tests/test_provenance.py` — add warning test
- Modify: `tests/test_defer.py` — add enum coercion warning test

**Context:** After Task 3, `parse_ticket` warns on failure. `allocate_id` at line 38-39 now has a redundant warning ("Skipping malformed ticket") because `parse_ticket` already warns. Remove it and add warnings to the remaining silent failure points.

**Step 1: Write failing tests**

Add to `tests/test_provenance.py` after `TestSessionMatch`:

```python
class TestProvenanceWarnings:
    """I3: JSON parse failures must warn, not silently return None."""

    def test_warns_on_malformed_defer_meta_json(self) -> None:
        import warnings

        from scripts.provenance import parse_defer_meta

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = parse_defer_meta('<!-- defer-meta {bad json} -->')
        assert result is None
        assert len(w) == 1
        assert "JSON" in str(w[0].message)

    def test_warns_on_malformed_distill_meta_json(self) -> None:
        import warnings

        from scripts.provenance import parse_distill_meta

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = parse_distill_meta('<!-- distill-meta {bad} -->')
        assert result is None
        assert len(w) == 1
        assert "JSON" in str(w[0].message)
```

Add to `tests/test_defer.py` after `TestFilenameSlug`:

```python
class TestEnumCoercionWarning:
    """I6: Invalid priority/effort must warn when coerced to default."""

    def test_warns_on_invalid_priority(self) -> None:
        import warnings

        from scripts.defer import render_ticket

        candidate = {
            "id": "T-20260228-01",
            "date": "2026-02-28",
            "summary": "Test",
            "problem": "P",
            "source_text": "S",
            "proposed_approach": "A",
            "acceptance_criteria": ["Done"],
            "priority": "urgent",
        }
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = render_ticket(candidate)
        assert "priority: medium" in result or 'priority: "medium"' in result
        assert any("priority" in str(x.message) and "urgent" in str(x.message) for x in w)

    def test_warns_on_invalid_effort(self) -> None:
        import warnings

        from scripts.defer import render_ticket

        candidate = {
            "id": "T-20260228-01",
            "date": "2026-02-28",
            "summary": "Test",
            "problem": "P",
            "source_text": "S",
            "proposed_approach": "A",
            "acceptance_criteria": ["Done"],
            "effort": "XXL",
        }
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = render_ticket(candidate)
        assert any("effort" in str(x.message) and "XXL" in str(x.message) for x in w)
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_provenance.py::TestProvenanceWarnings tests/test_defer.py::TestEnumCoercionWarning -v`
Expected: FAIL — no warnings currently emitted

**Step 3: Add warnings to provenance.py**

Add `import warnings` to `scripts/provenance.py` (after line 8, `import re`):

```python
import warnings
```

Replace the `except json.JSONDecodeError` blocks in both functions:

In `parse_defer_meta` (lines 20-23):
```python
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError as exc:
        warnings.warn(f"Malformed JSON in defer-meta comment: {exc}", stacklevel=2)
        return None
```

In `parse_distill_meta` (lines 31-34):
```python
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError as exc:
        warnings.warn(f"Malformed JSON in distill-meta comment: {exc}", stacklevel=2)
        return None
```

**Step 4: Add warnings to triage.py file skips**

In `scripts/triage.py`, `_scan_handoff_dirs` (lines 239-243), replace:
```python
            except OSError:
                continue
```
with:
```python
            except OSError as exc:
                warnings.warn(f"Cannot stat handoff file {p}: {exc}", stacklevel=2)
                continue
```

Add `import warnings` to the top of `scripts/triage.py` (after line 11, `from pathlib import Path`):
```python
import warnings
```

In `generate_report` (lines 269-272), replace:
```python
        except (OSError, UnicodeDecodeError):
            continue
```
with:
```python
        except (OSError, UnicodeDecodeError) as exc:
            warnings.warn(f"Cannot read handoff file {path}: {exc}", stacklevel=2)
            continue
```

**Step 5: Add enum coercion warnings to defer.py**

In `scripts/defer.py`, replace lines 86-90:
```python
    # Validate enum values, warn and fall back to defaults on invalid
    if priority not in _VALID_PRIORITIES:
        warnings.warn(
            f"Invalid priority {priority!r}, defaulting to 'medium'",
            stacklevel=2,
        )
        priority = "medium"
    if effort not in _VALID_EFFORTS:
        warnings.warn(
            f"Invalid effort {effort!r}, defaulting to 'S'",
            stacklevel=2,
        )
        effort = "S"
```

**Step 6: Remove redundant warning from allocate_id (I7)**

In `scripts/defer.py`, replace lines 38-40:
```python
            if ticket is None:
                warnings.warn(f"Skipping malformed ticket: {path}", stacklevel=2)  # P2-11
                continue
```
with:
```python
            if ticket is None:
                continue  # parse_ticket emits diagnostic warnings
```

**Step 7: Run tests to verify they pass**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_provenance.py::TestProvenanceWarnings tests/test_defer.py::TestEnumCoercionWarning -v`
Expected: PASS

**Step 8: Run full test suite**

Run: `cd packages/plugins/handoff && uv run pytest`
Expected: All tests pass

**Step 9: Commit**

```
git add scripts/provenance.py scripts/triage.py scripts/defer.py tests/test_provenance.py tests/test_defer.py
git commit -m "fix(handoff): add warnings to silent failure points (I3, I4, I5, I6, I7)"
```

---

## Task 5: Fix defer.main() and add CLI tests (C4, T1)

> **Amendment (Codex deep-review, 2026-02-28):** (1) Broadened exception handling from `KeyError | OSError` to `(KeyError, OSError, TypeError, ValueError, AttributeError)` — 3 concrete crash paths demonstrated: non-dict candidate → TypeError, None summary → AttributeError, wrong field type → TypeError in `_quote()`. (2) Added `isinstance(cand, dict)` guard before mutation. (3) Added top-level `json.JSONDecodeError` for malformed stdin. (4) Added `test_non_dict_candidate` test (highest priority missing coverage). (5) Added prereq note about json/Path imports.
>
> **Amendment (Codex adversarial review, 2026-02-28):** CRITICAL: Fixed `test_non_dict_candidate` — second candidate `{"summary": "Good"}` was missing required fields (`problem`, `source_text`, etc.), causing both candidates to error. Expected status was `"error"` (2 errors), not `"partial_success"` (1 error, 1 created). Second candidate now has all required fields. Also: `sys.stdin` restore uses `old_stdin` variable instead of `sys.__stdin__` to avoid clobbering pytest fixtures.
>
> **Amendment (Codex adversarial-challenge, 2026-02-28):** CRITICAL: The adversarial review's `old_stdin` fix was incomplete — `test_malformed_json_stdin` (line 785) and `test_partial_success` (line 811) still use `sys.stdin = sys.__stdin__` in their `finally` blocks. Updated both tests to use `old_stdin = sys.stdin` / `sys.stdin = old_stdin` pattern consistently with the other 3 tests.

**Issues:** C4 (bare `except Exception` catches everything, exit code always 0), T1 (`defer.main()` CLI completely untested)

**Files:**
- Modify: `scripts/defer.py:185-220`
- Modify: `tests/test_defer.py` — add `TestMain` class

**Prereqs:** `json`, `Path`, `io`, and `sys` must be importable. `json` and `Path` are already at module level in `test_defer.py`. `io` and `sys` are imported inside test methods.

**Context:** `defer.main()` has a bare `except Exception` that catches `KeyError`, `OSError`, `MemoryError`, etc. indiscriminately. It always returns 0 even on total failure. The error dict has only `str(exc)` which is unhelpful for `KeyError` (just the key name with no context).

**Step 1: Write failing tests**

Add at end of `tests/test_defer.py`:

```python
class TestMain:
    """T1/C4: defer.main() CLI tests."""

    def test_ok_status(self, tmp_path: Path, capsys) -> None:
        from scripts.defer import main

        tickets_dir = tmp_path / "tickets"
        candidate = json.dumps([{
            "summary": "Test ticket",
            "problem": "P",
            "source_text": "S",
            "proposed_approach": "A",
            "acceptance_criteria": ["Done"],
        }])
        import io
        import sys

        old_stdin = sys.stdin
        sys.stdin = io.StringIO(candidate)
        try:
            exit_code = main(["--tickets-dir", str(tickets_dir), "--date", "2026-02-28"])
        finally:
            sys.stdin = old_stdin
        output = json.loads(capsys.readouterr().out)
        assert output["status"] == "ok"
        assert len(output["created"]) == 1
        assert exit_code == 0

    def test_error_status_returns_nonzero(self, tmp_path: Path, capsys) -> None:
        from scripts.defer import main

        # Pass a candidate missing required fields to trigger KeyError
        candidate = json.dumps([{"summary": "Incomplete"}])
        import io
        import sys

        old_stdin = sys.stdin
        sys.stdin = io.StringIO(candidate)
        try:
            exit_code = main(["--tickets-dir", str(tmp_path), "--date", "2026-02-28"])
        finally:
            sys.stdin = old_stdin
        output = json.loads(capsys.readouterr().out)
        assert output["status"] == "error"
        assert len(output["errors"]) == 1
        assert exit_code == 1

    def test_non_dict_candidate_returns_error(self, tmp_path: Path, capsys) -> None:
        """Codex amendment: non-dict candidates must not crash with TypeError."""
        from scripts.defer import main

        # Second candidate has all required fields so it succeeds → partial_success
        candidate = json.dumps([
            "not a dict",
            {
                "summary": "Good ticket",
                "problem": "P",
                "source_text": "S",
                "proposed_approach": "A",
                "acceptance_criteria": ["Done"],
            },
        ])
        import io
        import sys

        old_stdin = sys.stdin
        sys.stdin = io.StringIO(candidate)
        try:
            exit_code = main(["--tickets-dir", str(tmp_path), "--date", "2026-02-28"])
        finally:
            sys.stdin = old_stdin
        output = json.loads(capsys.readouterr().out)
        assert output["status"] == "partial_success"
        assert len(output["created"]) == 1
        assert len(output["errors"]) == 1
        assert "dict" in output["errors"][0]["error"]
        assert exit_code == 1

    def test_malformed_json_stdin(self, tmp_path: Path, capsys) -> None:
        """Codex amendment: malformed JSON on stdin must not crash."""
        from scripts.defer import main

        import io
        import sys

        old_stdin = sys.stdin
        sys.stdin = io.StringIO("{bad json")
        try:
            exit_code = main(["--tickets-dir", str(tmp_path), "--date", "2026-02-28"])
        finally:
            sys.stdin = old_stdin
        output = json.loads(capsys.readouterr().out)
        assert output["status"] == "error"
        assert "JSON" in output["errors"][0]["error"]
        assert exit_code == 1

    def test_partial_success(self, tmp_path: Path, capsys) -> None:
        from scripts.defer import main

        candidates = json.dumps([
            {
                "summary": "Good ticket",
                "problem": "P",
                "source_text": "S",
                "proposed_approach": "A",
                "acceptance_criteria": ["Done"],
            },
            {"summary": "Bad ticket"},  # missing required fields
        ])
        import io
        import sys

        old_stdin = sys.stdin
        sys.stdin = io.StringIO(candidates)
        try:
            exit_code = main(["--tickets-dir", str(tmp_path), "--date", "2026-02-28"])
        finally:
            sys.stdin = old_stdin
        output = json.loads(capsys.readouterr().out)
        assert output["status"] == "partial_success"
        assert len(output["created"]) == 1
        assert len(output["errors"]) == 1
        assert exit_code == 1
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_defer.py::TestMain -v`
Expected: FAIL — `test_error_status_returns_nonzero` fails (exit code is 0), error messages are unhelpful

**Step 3: Fix `defer.main()`**

Replace lines 185-220 of `scripts/defer.py`:

```python
def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Reads candidate JSON from stdin, writes ticket files."""
    import argparse

    parser = argparse.ArgumentParser(description="Create deferred work tickets")
    parser.add_argument("--tickets-dir", type=Path, default=Path("docs/tickets"))
    parser.add_argument("--date", required=True, help="Date in YYYY-MM-DD format")
    args = parser.parse_args(argv)

    try:
        candidates = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        json.dump({"status": "error", "created": [], "errors": [{"summary": "stdin", "error": f"Invalid JSON input: {exc}"}]}, sys.stdout)
        return 1

    if not isinstance(candidates, list):
        candidates = [candidates]

    created: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []
    for cand in candidates:
        if not isinstance(cand, dict):
            errors.append({
                "summary": "unknown",
                "error": f"Candidate must be a dict, got {type(cand).__name__}",
            })
            continue
        try:
            tid = allocate_id(args.date, args.tickets_dir)
            cand["id"] = tid
            cand["date"] = args.date
            path = write_ticket(cand, args.tickets_dir)
            created.append({"id": tid, "path": str(path)})
        except (KeyError, OSError, TypeError, ValueError, AttributeError) as exc:
            errors.append({
                "summary": cand.get("summary", "unknown"),
                "error": f"{type(exc).__name__}: {exc}",
            })

    if errors and created:
        json.dump({"status": "partial_success", "created": created, "errors": errors}, sys.stdout)
    elif errors:
        json.dump({"status": "error", "created": [], "errors": errors}, sys.stdout)
    else:
        json.dump({"status": "ok", "created": created}, sys.stdout)
    return 1 if errors else 0
```

Key changes:
- Top-level `json.JSONDecodeError` handling for malformed stdin
- `isinstance(cand, dict)` guard before mutation (prevents TypeError on list/string candidates)
- `except Exception` replaced with `except (KeyError, OSError, TypeError, ValueError, AttributeError)` — covers missing fields, I/O, wrong types, invalid values, and attribute access on None
- Error message format: `{ExceptionType}: {message}` for consistent diagnostics
- Return 1 when any errors occurred (was always 0)

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_defer.py::TestMain -v`
Expected: PASS

**Step 5: Run full test suite**

Run: `cd packages/plugins/handoff && uv run pytest`
Expected: All tests pass

**Step 6: Commit**

```
git add scripts/defer.py tests/test_defer.py
git commit -m "fix(handoff): specific exception handling and nonzero exit code in defer.main() (C4, T1)"
```

---

## Task 6: Add priority/effort validation tests (T2)

**Issues:** T2 (`render_ticket` priority/effort validation untested — P1-9 fix)

**Files:**
- Modify: `tests/test_defer.py` — add `TestPriorityEffortValidation` class

**Context:** The enum coercion warning tests from Task 4 verify the warning is emitted, but don't verify the rendered output contains the correct fallback value. This task adds explicit validation tests for the P1-9 fix.

**Step 1: Write tests**

Add after `TestEnumCoercionWarning` in `tests/test_defer.py`:

```python
class TestPriorityEffortValidation:
    """T2: P1-9 fix — invalid priority/effort falls back to defaults."""

    def test_invalid_priority_falls_back_to_medium(self) -> None:
        import warnings

        from scripts.defer import render_ticket

        candidate = {
            "id": "T-20260228-01",
            "date": "2026-02-28",
            "summary": "Test",
            "problem": "P",
            "source_text": "S",
            "proposed_approach": "A",
            "acceptance_criteria": ["Done"],
            "priority": "urgent",
        }
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = render_ticket(candidate)
        # "urgent" is not in _VALID_PRIORITIES, should fall back to "medium"
        assert "priority: medium" in result or 'priority: "medium"' in result

    def test_invalid_effort_falls_back_to_s(self) -> None:
        import warnings

        from scripts.defer import render_ticket

        candidate = {
            "id": "T-20260228-01",
            "date": "2026-02-28",
            "summary": "Test",
            "problem": "P",
            "source_text": "S",
            "proposed_approach": "A",
            "acceptance_criteria": ["Done"],
            "effort": "XXL",
        }
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = render_ticket(candidate)
        assert "effort: S" in result or 'effort: "S"' in result

    def test_valid_critical_priority_preserved(self) -> None:
        """C6 companion: 'critical' is a valid priority, must not be coerced."""
        from scripts.defer import render_ticket

        candidate = {
            "id": "T-20260228-01",
            "date": "2026-02-28",
            "summary": "Test",
            "problem": "P",
            "source_text": "S",
            "proposed_approach": "A",
            "acceptance_criteria": ["Done"],
            "priority": "critical",
        }
        result = render_ticket(candidate)
        assert "priority: critical" in result or 'priority: "critical"' in result

    def test_all_valid_efforts_accepted(self) -> None:
        import warnings

        from scripts.defer import render_ticket

        for effort in ("XS", "S", "M", "L", "XL"):
            candidate = {
                "id": "T-20260228-01",
                "date": "2026-02-28",
                "summary": "Test",
                "problem": "P",
                "source_text": "S",
                "proposed_approach": "A",
                "acceptance_criteria": ["Done"],
                "effort": effort,
            }
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                render_ticket(candidate)
            effort_warns = [x for x in w if "effort" in str(x.message)]
            assert len(effort_warns) == 0, f"Valid effort {effort!r} should not warn"
```

**Step 2: Run tests**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_defer.py::TestPriorityEffortValidation -v`
Expected: PASS (these test existing behavior that already works, they just weren't covered)

**Step 3: Commit**

```
git add tests/test_defer.py
git commit -m "test(handoff): add priority/effort validation tests (T2)"
```

---

## Task 7: Code improvements (I1, I2)

> **Amendment (Codex deep-review, 2026-02-28):** Task 7's import block replacement must preserve `import warnings` added by Task 4. The code block below includes it. After this task, re-run Task 4's warning tests (`tests/test_triage.py` warning assertions) to verify no regression.

**Issues:** I1 (duplicated `_section_name` in triage.py and distill.py), I2 (`allocate_id` concurrency docstring), plus cleanup of unused `get_archive_dir` import

**Files:**
- Modify: `scripts/handoff_parsing.py` — add `section_name()` public function
- Modify: `scripts/triage.py:19,25,100-108` — remove `_section_name`, import from handoff_parsing, remove unused `get_archive_dir` import
- Modify: `scripts/distill.py:381-387` — remove `_section_name`, import from handoff_parsing
- Modify: `scripts/defer.py:27-31` — add concurrency note to docstring

**Step 1: Add `section_name` to handoff_parsing.py**

Add after the `Section` dataclass (after line 19) in `scripts/handoff_parsing.py`:

```python

def section_name(heading: str) -> str:
    """Strip the '## ' prefix from a Section heading.

    Section.heading stores headings with prefix (e.g., '## Open Questions').
    This returns the bare name (e.g., 'Open Questions').
    """
    if heading.startswith("## "):
        return heading[3:].strip()
    return heading.strip()
```

**Step 2: Update triage.py imports and remove `_section_name`**

In `scripts/triage.py`, update the import lines (15-25) to include `section_name` and remove `get_archive_dir`:

Replace:
```python
try:
    from scripts.ticket_parsing import parse_ticket
    from scripts.provenance import read_provenance, session_matches
    from scripts.handoff_parsing import parse_frontmatter, parse_sections
    from scripts.project_paths import get_handoffs_dir, get_archive_dir
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from scripts.ticket_parsing import parse_ticket  # type: ignore[no-redef]
    from scripts.provenance import read_provenance, session_matches  # type: ignore[no-redef]
    from scripts.handoff_parsing import parse_frontmatter, parse_sections  # type: ignore[no-redef]
    from scripts.project_paths import get_handoffs_dir, get_archive_dir  # type: ignore[no-redef]
```

with:

```python
import warnings

try:
    from scripts.ticket_parsing import parse_ticket
    from scripts.provenance import read_provenance, session_matches
    from scripts.handoff_parsing import parse_frontmatter, parse_sections, section_name
    from scripts.project_paths import get_handoffs_dir
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from scripts.ticket_parsing import parse_ticket  # type: ignore[no-redef]
    from scripts.provenance import read_provenance, session_matches  # type: ignore[no-redef]
    from scripts.handoff_parsing import parse_frontmatter, parse_sections, section_name  # type: ignore[no-redef]
    from scripts.project_paths import get_handoffs_dir  # type: ignore[no-redef]
```

Note: `import warnings` is preserved from Task 4. Do not remove it.

Remove `_section_name` function (lines 100-108) from `triage.py`.

Replace `_section_name(section.heading)` call at line 138 with `section_name(section.heading)`.

**Step 3: Update distill.py**

In `scripts/distill.py`, add `section_name` to the handoff_parsing import. Remove the local `_section_name` function (lines 381-387). Replace all calls to `_section_name(...)` with `section_name(...)`.

Note: check distill.py's import block and call sites first. The implementer should `grep -n '_section_name' scripts/distill.py` to find all call sites.

> **Adversarial review note:** `distill.py` has a `try/except ModuleNotFoundError` dual-import path (lines 21-25). You MUST add `, section_name` to BOTH the `try` import line AND the `except` fallback import line. Updating only the `try` path causes `NameError` in alternate invocation contexts. Tests often exercise only the `try` path, so this bug can ship undetected.
>
> **Amendment (Codex adversarial-challenge, 2026-02-28):** Added explicit replacement snippets for both import paths. The grep instruction alone is insufficient — an implementer could update only the `try` path.

**Explicit replacement for `distill.py` lines 21-25:**

Replace:
```python
try:
    from scripts.handoff_parsing import parse_handoff
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from scripts.handoff_parsing import parse_handoff  # type: ignore[no-redef]
```

with:
```python
try:
    from scripts.handoff_parsing import parse_handoff, section_name
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from scripts.handoff_parsing import parse_handoff, section_name  # type: ignore[no-redef]
```

**Verification:** After replacement, `grep -c 'section_name' scripts/distill.py` must return ≥ 2 (both import lines). If it returns 1, the `except` path was missed.

**Step 4: Add concurrency note to allocate_id**

In `scripts/defer.py`, replace the `allocate_id` docstring (lines 27-31):

```python
def allocate_id(date_str: str, tickets_dir: Path) -> str:
    """Allocate the next ticket ID for a given date.

    Scans all .md files in tickets_dir, parses their YAML to extract id fields,
    finds the highest sequence number for the date, and returns the next one.

    Not concurrency-safe: assumes single-writer access to tickets_dir.
    Concurrent calls for the same date may produce duplicate IDs.
    """
```

**Step 5: Run full test suite**

Run: `cd packages/plugins/handoff && uv run pytest`
Expected: All tests pass (the shared `section_name` function has identical behavior to the old `_section_name` copies)

**Step 6: Commit**

```
git add scripts/handoff_parsing.py scripts/triage.py scripts/distill.py scripts/defer.py
git commit -m "refactor(handoff): extract section_name to handoff_parsing, add allocate_id concurrency note (I1, I2)"
```

---

## Task 8: Type design improvements (I8, I9, I10, I11)

> **Amendment (Codex deep-review, 2026-02-28):** Added `Literal` type for `MatchResult.match_type` — this is a closed protocol that drives branching logic. Kept `dict[str, int]` for `match_counts` (more flexible for future match strategies). Full dataclasses rejected as scope creep.
>
> **Amendment (Codex adversarial-challenge, 2026-02-28):** Code block imports `Literal, TypedDict` but `MatchResult` uses `dict[str, Any]` — `Any` missing from import. Updated to canonical form: `from typing import Any, Literal, TypedDict`. The existing `from typing import Any` line must be replaced (not supplemented) with this consolidated import.

**Issues:** I8 (MatchResult as raw dict), I9 (TicketFile mutable frontmatter), I10 (no TicketFile construction validation), I11 (untyped return dicts)

**Files:**
- Modify: `scripts/triage.py` — add `MatchResult`, `OpenTicket`, `TriageReport` TypedDicts
- Modify: `scripts/ticket_parsing.py:74-80` — add docstring note about frontmatter mutability
- Modify: `tests/test_triage.py` — update type references if needed

**Context:** The type-analyzer found that validated structure exists at runtime but is invisible to the type system. The dominant pattern is `dict[str, Any]` for structures with guaranteed keys. TypedDicts add type safety without runtime cost or API changes.

**Step 1: Add TypedDicts to triage.py**

Add after the imports block (after line 26) in `scripts/triage.py`:

```python
from typing import Any, Literal, TypedDict


class OpenTicket(TypedDict):
    id: str
    date: str
    priority: str
    status_raw: str
    status_normalized: str
    normalization_confidence: str
    summary: str
    path: str


class MatchResult(TypedDict):
    match_type: Literal["uid_match", "id_ref", "manual_review"]
    matched_ticket: str | None
    item: dict[str, Any]


class TriageReport(TypedDict):
    open_tickets: list[OpenTicket]
    orphaned_items: list[MatchResult]
    matched_items: list[MatchResult]
    match_counts: dict[str, int]
    skipped_prose_count: int
```

Note: `TypedDict` and `Literal` are available from `typing` in Python 3.8+. Since the file already imports `from typing import Any`, consolidate to a single import: `from typing import Any, Literal, TypedDict`. Do not add a separate `from typing import` line (PEP 8 style).

**Step 2: Update return type annotations**

Update function signatures in `scripts/triage.py`:

- `read_open_tickets` (line 52): `-> list[dict[str, Any]]` → `-> list[OpenTicket]`
- `match_orphan_item` (line 186): `-> dict[str, Any]` → `-> MatchResult`
- `generate_report` (line 247): `-> dict[str, Any]` → `-> TriageReport`

Internal variables that hold these types should also be updated:
- `_load_tickets_for_matching` return type stays `list[dict[str, Any]]` (internal, not a public API)
- `generate_report`'s local vars: `orphaned: list[MatchResult] = []`, `matched: list[MatchResult] = []`

**Step 3: Document TicketFile limitations (I9, I10)**

In `scripts/ticket_parsing.py`, update the `TicketFile` docstring (lines 75-76):

```python
@dataclass(frozen=True)
class TicketFile:
    """Parsed ticket with typed frontmatter and markdown body.

    Note: frozen prevents field reassignment but the frontmatter dict
    is mutable at runtime. All production code constructs TicketFile
    via parse_ticket() which validates schema. Direct construction
    (e.g., in tests) bypasses validation.
    """

    path: str
    frontmatter: dict[str, Any]
    body: str
```

**Step 4: Run full test suite**

Run: `cd packages/plugins/handoff && uv run pytest`
Expected: All tests pass. TypedDicts are backward compatible — they're still dicts at runtime. Type checkers will benefit from the annotations, but runtime behavior is unchanged.

**Step 5: Commit**

```
git add scripts/triage.py scripts/ticket_parsing.py
git commit -m "refactor(handoff): add TypedDicts for return types, document TicketFile limits (I8, I9, I10, I11)"
```

---

## Verification

After all 8 tasks:

1. Run full test suite: `cd packages/plugins/handoff && uv run pytest -v`
   - Expected: All tests pass (320 existing + 24 new ≈ 344+)
2. Push to remote: `git push`
3. Verify PR #31 is updated with new commits
