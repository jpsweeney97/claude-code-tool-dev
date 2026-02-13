"""Tests for entity extraction with disambiguation and normalization.

Tests cover the 4 MVP extraction categories:
1. Paths (file_loc, file_path, file_name with disambiguation)
2. URLs (mapped to file_path)
3. Dotted symbols (mapped to symbol)
4. Structured errors (error class name mapped to symbol)

Also tests:
- Confidence assignment (backticked -> high, strong pattern -> medium)
- Span tracking (no overlapping extractions)
- Canonicalization
- Entity construction (correct fields, IDs, types)
"""

from context_injection.entities import extract_entities
from context_injection.state import AppContext
from context_injection.types import Entity


# --- Helpers ---


def _make_ctx() -> AppContext:
    return AppContext.create(repo_root="/tmp/repo")


def _extract(
    text: str, source_type: str = "claim", in_focus: bool = True
) -> list[Entity]:
    """Convenience wrapper around extract_entities."""
    from context_injection.entities import extract_entities

    ctx = _make_ctx()
    return extract_entities(text, source_type=source_type, in_focus=in_focus, ctx=ctx)


def _extract_one(text: str, **kwargs) -> Entity:
    """Extract exactly one entity, assert count == 1."""
    entities = _extract(text, **kwargs)
    assert len(entities) == 1, (
        f"Expected 1 entity, got {len(entities)}: {[e.raw for e in entities]}"
    )
    return entities[0]


# ============================================================
# Category 1: Paths — disambiguation rules
# ============================================================


class TestFileLocExtraction:
    """file_loc: has :line or :line:col suffix, or #L anchor."""

    def test_colon_line(self) -> None:
        e = _extract_one("The error is in `config.py:42`")
        assert e.type == "file_loc"
        assert e.raw == "config.py:42"
        assert e.canonical == "config.py"  # canon strips line suffix

    def test_colon_line_col(self) -> None:
        e = _extract_one("See `src/app.ts:10:5`")
        assert e.type == "file_loc"
        assert e.raw == "src/app.ts:10:5"
        assert e.canonical == "src/app.ts"

    def test_github_anchor(self) -> None:
        e = _extract_one("Check `config.py#L42`")
        assert e.type == "file_loc"
        assert e.raw == "config.py#L42"
        assert e.canonical == "config.py"

    def test_path_with_line_is_file_loc_not_file_path(self) -> None:
        """Disambiguation: :line suffix wins over path separator."""
        e = _extract_one("See `src/api/auth.py:100`")
        assert e.type == "file_loc"
        assert e.raw == "src/api/auth.py:100"
        assert e.canonical == "src/api/auth.py"


class TestFilePathExtraction:
    """file_path: has path separator (/) or prefix (./, ../)."""

    def test_path_separator(self) -> None:
        e = _extract_one("The module is in `src/api/auth.py`")
        assert e.type == "file_path"
        assert e.raw == "src/api/auth.py"
        assert e.canonical == "src/api/auth.py"

    def test_dot_slash_prefix(self) -> None:
        e = _extract_one("Use `./config.yaml`")
        assert e.type == "file_path"
        assert e.raw == "./config.yaml"
        assert e.canonical == "config.yaml"  # canon strips ./ prefix

    def test_directory_path(self) -> None:
        """Path ending in / is still a file_path (dir_path is post-MVP)."""
        e = _extract_one("Look in `src/config/`")
        assert e.type == "file_path"
        assert e.raw == "src/config/"

    def test_unquoted_path_with_separator(self) -> None:
        """Unquoted path-like with / gets medium confidence."""
        e = _extract_one("The file is at src/api/auth.py somewhere")
        assert e.type == "file_path"
        assert e.raw == "src/api/auth.py"
        assert e.confidence == "medium"


class TestFileNameExtraction:
    """file_name: no separator, has known file extension."""

    def test_known_extension(self) -> None:
        e = _extract_one("Check `config.yaml` for settings")
        assert e.type == "file_name"
        assert e.raw == "config.yaml"
        assert e.canonical == "config.yaml"

    def test_python_extension(self) -> None:
        e = _extract_one("Look at `setup.py`")
        assert e.type == "file_name"
        assert e.raw == "setup.py"

    def test_json_extension(self) -> None:
        e = _extract_one("The `package.json` file has the deps")
        assert e.type == "file_name"
        assert e.raw == "package.json"


# ============================================================
# Category 2: URLs
# ============================================================


class TestURLExtraction:
    """URLs map to file_path type."""

    def test_https_url(self) -> None:
        e = _extract_one("See `https://docs.example.com/api`")
        assert e.type == "file_path"
        assert e.raw == "https://docs.example.com/api"
        assert e.canonical == "https://docs.example.com/api"  # URLs: canon = raw

    def test_http_url(self) -> None:
        e = _extract_one("Reference: `http://localhost:8080/health`")
        assert e.type == "file_path"
        assert e.raw == "http://localhost:8080/health"

    def test_unquoted_url(self) -> None:
        e = _extract_one("Visit https://docs.example.com/api for details")
        assert e.type == "file_path"
        assert e.confidence == "medium"


# ============================================================
# Category 3: Dotted symbols
# ============================================================


class TestDottedSymbolExtraction:
    """Dotted symbols (2+ dots, no spaces) map to symbol type."""

    def test_three_part_symbol(self) -> None:
        e = _extract_one("Uses `pkg.mod.func`")
        assert e.type == "symbol"
        assert e.raw == "pkg.mod.func"
        assert e.canonical == "pkg.mod.func"

    def test_two_part_symbol(self) -> None:
        e = _extract_one("Calls `os.path.join`")
        assert e.type == "symbol"
        assert e.raw == "os.path.join"

    def test_symbol_with_trailing_parens(self) -> None:
        """canon() strips trailing ()."""
        e = _extract_one("Calls `os.path.join()`")
        assert e.type == "symbol"
        assert e.raw == "os.path.join()"
        assert e.canonical == "os.path.join"


# ============================================================
# Category 4: Structured errors
# ============================================================


class TestStructuredErrorExtraction:
    """Structured error patterns — extract error class as symbol."""

    def test_value_error(self) -> None:
        e = _extract_one("Raises `ValueError: invalid literal`")
        assert e.type == "symbol"
        assert e.raw == "ValueError"
        assert e.canonical == "ValueError"

    def test_type_error(self) -> None:
        e = _extract_one("`TypeError: unsupported operand`")
        assert e.type == "symbol"
        assert e.raw == "TypeError"

    def test_unquoted_error_pattern(self) -> None:
        e = _extract_one("Got a KeyError: 'missing_key'")
        assert e.type == "symbol"
        assert e.raw == "KeyError"
        assert e.confidence == "medium"


# ============================================================
# Confidence assignment
# ============================================================


class TestConfidenceAssignment:
    """Backticked -> high, strong pattern -> medium."""

    def test_backticked_entity_is_high(self) -> None:
        e = _extract_one("Uses `src/api/auth.py`")
        assert e.confidence == "high"

    def test_unquoted_path_is_medium(self) -> None:
        e = _extract_one("The file src/api/auth.py has the code")
        assert e.confidence == "medium"

    def test_backticked_file_name_is_high(self) -> None:
        e = _extract_one("Check `config.yaml`")
        assert e.confidence == "high"

    def test_backticked_url_is_high(self) -> None:
        e = _extract_one("See `https://example.com/docs`")
        assert e.confidence == "high"

    def test_unquoted_url_is_medium(self) -> None:
        e = _extract_one("Visit https://example.com/docs for info")
        assert e.confidence == "medium"

    def test_backticked_error_is_high(self) -> None:
        e = _extract_one("`ValueError: bad input`")
        assert e.confidence == "high"

    def test_double_backtick_entity_gets_high_confidence(self) -> None:
        """Entity within double backticks gets high confidence."""
        ctx = AppContext.create(repo_root="/tmp/repo", git_files=set())
        entities = extract_entities(
            "Check ``src/config.yaml`` for settings",
            source_type="claim",
            in_focus=True,
            ctx=ctx,
        )
        file_entities = [e for e in entities if e.canonical == "src/config.yaml"]
        assert len(file_entities) == 1
        assert file_entities[0].confidence == "high"


# ============================================================
# Source type and in_focus flags
# ============================================================


class TestSourceMetadata:
    def test_source_type_claim(self) -> None:
        e = _extract_one("Uses `config.yaml`", source_type="claim")
        assert e.source_type == "claim"

    def test_source_type_unresolved(self) -> None:
        e = _extract_one("Uses `config.yaml`", source_type="unresolved")
        assert e.source_type == "unresolved"

    def test_in_focus_true(self) -> None:
        e = _extract_one("Uses `config.yaml`", in_focus=True)
        assert e.in_focus is True

    def test_in_focus_false(self) -> None:
        e = _extract_one("Uses `config.yaml`", in_focus=False)
        assert e.in_focus is False


# ============================================================
# Entity construction
# ============================================================


class TestEntityConstruction:
    """Entities must be valid Entity models with correct field types."""

    def test_entity_id_format(self) -> None:
        e = _extract_one("Uses `config.yaml`")
        assert e.id.startswith("e_")

    def test_entity_ids_are_sequential(self) -> None:
        from context_injection.entities import extract_entities

        ctx = _make_ctx()
        entities = extract_entities(
            "Uses `config.yaml` and `src/app.py`",
            source_type="claim",
            in_focus=True,
            ctx=ctx,
        )
        assert len(entities) >= 2
        ids = [int(e.id.split("_")[1]) for e in entities]
        assert ids == sorted(ids)
        # Sequential with no gaps within a single call
        assert ids[-1] - ids[0] == len(ids) - 1

    def test_tier_assignment_tier1(self) -> None:
        e = _extract_one("Uses `src/api/auth.py`")
        assert e.tier == 1

    def test_resolved_to_is_none(self) -> None:
        """At extraction time, resolved_to is always None."""
        e = _extract_one("Uses `config.yaml`")
        assert e.resolved_to is None

    def test_entity_is_valid_pydantic_model(self) -> None:
        """Entity must pass Pydantic validation (strict mode)."""
        e = _extract_one("Uses `src/config.yaml`")
        # Roundtrip through model_dump to verify no coercion issues
        data = e.model_dump()
        Entity.model_validate(data)


# ============================================================
# Canonicalization
# ============================================================


class TestCanonicalization:
    """canon() rules per entity type."""

    def test_file_loc_strips_line_suffix(self) -> None:
        e = _extract_one("`config.py:42`")
        assert e.canonical == "config.py"

    def test_file_loc_strips_line_col_suffix(self) -> None:
        e = _extract_one("`src/app.ts:10:5`")
        assert e.canonical == "src/app.ts"

    def test_file_loc_strips_github_anchor(self) -> None:
        e = _extract_one("`config.py#L42`")
        assert e.canonical == "config.py"

    def test_file_path_strips_dot_slash(self) -> None:
        e = _extract_one("`./config.yaml`")
        assert e.canonical == "config.yaml"

    def test_file_path_no_dot_slash_unchanged(self) -> None:
        e = _extract_one("`src/api/auth.py`")
        assert e.canonical == "src/api/auth.py"

    def test_file_name_unchanged(self) -> None:
        e = _extract_one("`config.yaml`")
        assert e.canonical == "config.yaml"

    def test_url_unchanged(self) -> None:
        e = _extract_one("`https://example.com/api`")
        assert e.canonical == "https://example.com/api"

    def test_symbol_strips_trailing_parens(self) -> None:
        e = _extract_one("`os.path.join()`")
        assert e.canonical == "os.path.join"

    def test_error_symbol_unchanged(self) -> None:
        e = _extract_one("`ValueError: bad input`")
        assert e.canonical == "ValueError"


# ============================================================
# Span tracking (no overlapping extractions)
# ============================================================


class TestSpanTracking:
    """Span tracking prevents double-extraction of overlapping text."""

    def test_file_loc_not_also_file_path(self) -> None:
        """src/config.py:42 should extract as file_loc only, not also file_path."""
        entities = _extract("See `src/config.py:42`")
        types = [e.type for e in entities]
        assert "file_loc" in types
        assert types.count("file_path") == 0  # No file_path from the same span

    def test_file_loc_not_also_file_name(self) -> None:
        """config.py:42 should extract as file_loc only, not also file_name."""
        entities = _extract("See `config.py:42`")
        types = [e.type for e in entities]
        assert types == ["file_loc"]

    def test_url_not_double_extracted(self) -> None:
        """A URL should not also be extracted as a file_path for its path component."""
        entities = _extract("See `https://docs.example.com/api/v2`")
        assert len(entities) == 1
        assert entities[0].type == "file_path"


# ============================================================
# Multiple entities in one text
# ============================================================


class TestMultipleEntities:
    def test_two_different_entities(self) -> None:
        entities = _extract("Uses `config.yaml` and `src/app.py`")
        assert len(entities) == 2
        types = {e.type for e in entities}
        assert "file_name" in types
        assert "file_path" in types

    def test_contract_example_claim(self) -> None:
        """From the contract's Focus Bundle example."""
        entities = _extract(
            "The project uses `src/config/settings.yaml` for all configuration"
        )
        assert len(entities) == 1
        e = entities[0]
        assert e.type == "file_path"
        assert e.raw == "src/config/settings.yaml"
        assert e.confidence == "high"

    def test_contract_example_unresolved(self) -> None:
        entities = _extract(
            "Whether `config.yaml` is the only config file or if there are environment overrides",
            source_type="unresolved",
        )
        assert len(entities) == 1
        e = entities[0]
        assert e.type == "file_name"
        assert e.source_type == "unresolved"

    def test_contract_example_context_claim(self) -> None:
        entities = _extract(
            "The project follows a monorepo structure with `packages/` subdirectories",
            source_type="claim",
            in_focus=False,
        )
        # packages/ has a path separator, so file_path
        assert len(entities) == 1
        assert entities[0].type == "file_path"
        assert entities[0].in_focus is False


# ============================================================
# Empty / no-match cases
# ============================================================


class TestNoMatch:
    def test_plain_text_no_entities(self) -> None:
        entities = _extract("The project uses YAML for configuration")
        assert entities == []

    def test_empty_string(self) -> None:
        entities = _extract("")
        assert entities == []

    def test_bare_word_not_extracted(self) -> None:
        """Explicitly excluded: bare single tokens like README, config."""
        entities = _extract("Check the README for details")
        assert entities == []

    def test_bare_function_call_not_extracted(self) -> None:
        """Explicitly excluded: bare function calls like foo()."""
        entities = _extract("Calls authenticate() for login")
        assert entities == []

    def test_traversal_path_not_extracted(self) -> None:
        """Paths with .. are filtered (always fail downstream path checking)."""
        entities = _extract("See `../config.yaml`")
        assert entities == []

    def test_double_traversal_not_extracted(self) -> None:
        entities = _extract("At `../../etc/passwd`")
        assert entities == []

    def test_filename_with_double_dots_not_rejected(self) -> None:
        """A file like 'utils..helpers.py' should not be rejected as traversal."""
        ctx = AppContext.create(repo_root="/tmp/repo", git_files=set())
        entities = extract_entities(
            "Check `src/utils..helpers.py` for the fix",
            source_type="claim",
            in_focus=True,
            ctx=ctx,
        )
        file_entities = [e for e in entities if "utils..helpers" in e.raw]
        assert len(file_entities) == 1


# ============================================================
# Input length cap (ReDoS mitigation)
# ============================================================


class TestInputLengthCap:
    def test_long_text_is_truncated(self) -> None:
        """Text beyond MAX_TEXT_LEN is truncated before extraction."""
        from context_injection.entities import MAX_TEXT_LEN

        # Entity placed beyond the cap — should not be extracted
        padding = "x" * (MAX_TEXT_LEN + 10)
        text = padding + " `config.yaml`"
        entities = _extract(text)
        assert entities == []

    def test_entity_within_cap_is_extracted(self) -> None:
        """Entity within MAX_TEXT_LEN is extracted normally."""
        entities = _extract("Uses `config.yaml` in the project")
        assert len(entities) == 1
        assert entities[0].type == "file_name"
