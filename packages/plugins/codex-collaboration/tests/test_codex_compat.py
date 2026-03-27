"""Contract tests for Codex compatibility — run against vendored fixtures only.

No live codex binary required. Tests verify:
- Version parsing and comparison (semver, not string)
- Vendored schema contains all required/optional methods
- Method surface checking logic
- Version constants are self-consistent
"""

from __future__ import annotations

import pytest

from pathlib import Path

from unittest.mock import patch

from server.codex_compat import (
    MINIMUM_CODEX_VERSION,
    OPTIONAL_METHODS,
    REQUIRED_METHODS,
    TESTED_CODEX_VERSION,
    SemVer,
    check_method_surface,
    extract_client_methods,
    get_codex_version,
)


class TestSemVerParsing:
    def test_parse_three_part(self):
        v = SemVer.parse("0.117.0")
        assert v == SemVer(0, 117, 0)

    def test_parse_with_suffix_ignores_suffix(self):
        v = SemVer.parse("1.2.3-beta.1")
        assert v == SemVer(1, 2, 3)

    def test_parse_rejects_non_semver(self):
        with pytest.raises(ValueError, match="expected X.Y.Z"):
            SemVer.parse("not-a-version")

    def test_parse_rejects_empty(self):
        with pytest.raises(ValueError):
            SemVer.parse("")

    def test_parse_rejects_two_part(self):
        with pytest.raises(ValueError):
            SemVer.parse("1.2")


class TestSemVerComparison:
    def test_equal(self):
        assert SemVer(0, 117, 0) == SemVer(0, 117, 0)

    def test_less_than_major(self):
        assert SemVer(0, 117, 0) < SemVer(1, 0, 0)

    def test_less_than_minor(self):
        assert SemVer(0, 116, 9) < SemVer(0, 117, 0)

    def test_less_than_patch(self):
        assert SemVer(0, 117, 0) < SemVer(0, 117, 1)

    def test_greater_than(self):
        assert SemVer(0, 118, 0) > SemVer(0, 117, 0)

    def test_greater_equal(self):
        assert SemVer(0, 117, 0) >= SemVer(0, 117, 0)
        assert SemVer(0, 118, 0) >= SemVer(0, 117, 0)

    def test_not_equal(self):
        assert SemVer(0, 117, 0) != SemVer(0, 117, 1)

    def test_str(self):
        assert str(SemVer(0, 117, 0)) == "0.117.0"


class TestGetCodexVersionParsing:
    """Unit tests for get_codex_version() output parsing with mocked subprocess."""

    def _mock_version_output(self, stdout: str) -> SemVer:
        """Run get_codex_version() with mocked subprocess returning stdout."""
        mock_result = type("Result", (), {"stdout": stdout, "returncode": 0, "stderr": ""})()
        with patch("server.codex_compat.subprocess.run", return_value=mock_result):
            return get_codex_version()

    def test_parses_codex_cli_prefix(self):
        v = self._mock_version_output("codex-cli 0.117.0\n")
        assert v == SemVer(0, 117, 0)

    def test_parses_codex_prefix(self):
        v = self._mock_version_output("codex 0.117.0\n")
        assert v == SemVer(0, 117, 0)

    def test_rejects_unrecognized_output(self):
        with pytest.raises(RuntimeError, match="Unexpected codex version format"):
            self._mock_version_output("something-else 0.117.0\n")


class TestVersionConstants:
    def test_tested_version_is_valid_semver(self):
        v = SemVer.parse(TESTED_CODEX_VERSION)
        assert v.major >= 0

    def test_minimum_version_is_valid_semver(self):
        v = SemVer.parse(MINIMUM_CODEX_VERSION)
        assert v.major >= 0

    def test_minimum_not_above_tested(self):
        tested = SemVer.parse(TESTED_CODEX_VERSION)
        minimum = SemVer.parse(MINIMUM_CODEX_VERSION)
        assert minimum <= tested, "MINIMUM_CODEX_VERSION must not exceed TESTED_CODEX_VERSION"

    def test_required_and_optional_disjoint(self):
        overlap = REQUIRED_METHODS & OPTIONAL_METHODS
        assert overlap == frozenset(), f"Methods in both required and optional: {overlap}"


class TestExtractClientMethods:
    def test_extracts_methods_from_vendored_schema(self, client_request_schema: Path):
        methods = extract_client_methods(client_request_schema)
        assert isinstance(methods, frozenset)
        assert len(methods) > 0

    def test_vendored_schema_contains_all_required_methods(self, client_request_schema: Path):
        methods = extract_client_methods(client_request_schema)
        missing = REQUIRED_METHODS - methods
        assert missing == frozenset(), f"Vendored schema missing required methods: {sorted(missing)}"

    def test_vendored_schema_contains_all_optional_methods(self, client_request_schema: Path):
        methods = extract_client_methods(client_request_schema)
        missing = OPTIONAL_METHODS - methods
        assert missing == frozenset(), f"Vendored schema missing optional methods: {sorted(missing)}"

    def test_vendored_schema_contains_initialize(self, client_request_schema: Path):
        methods = extract_client_methods(client_request_schema)
        assert "initialize" in methods


class TestCheckMethodSurface:
    def test_all_present_returns_empty(self):
        available = REQUIRED_METHODS | OPTIONAL_METHODS | {"extra/method"}
        missing_req, missing_opt = check_method_surface(available)
        assert missing_req == frozenset()
        assert missing_opt == frozenset()

    def test_missing_required_detected(self):
        available = frozenset({"thread/start", "turn/start"})
        missing_req, _missing_opt = check_method_surface(available)
        assert len(missing_req) > 0
        assert "thread/resume" in missing_req

    def test_missing_optional_detected(self):
        available = REQUIRED_METHODS  # no optional methods
        missing_req, missing_opt = check_method_surface(available)
        assert missing_req == frozenset()
        assert "turn/steer" in missing_opt

    def test_empty_available_misses_all(self):
        missing_req, missing_opt = check_method_surface(frozenset())
        assert missing_req == REQUIRED_METHODS
        assert missing_opt == OPTIONAL_METHODS


class TestDerivedManifest:
    def test_manifest_required_matches_constant(self, vendored_schema_dir: Path):
        manifest_path = vendored_schema_dir / "required-methods.json"
        if not manifest_path.exists():
            pytest.skip("required-methods.json not yet generated")
        import json

        with open(manifest_path) as f:
            manifest = json.load(f)
        assert frozenset(manifest["required"]) == REQUIRED_METHODS

    def test_manifest_optional_matches_constant(self, vendored_schema_dir: Path):
        manifest_path = vendored_schema_dir / "required-methods.json"
        if not manifest_path.exists():
            pytest.skip("required-methods.json not yet generated")
        import json

        with open(manifest_path) as f:
            manifest = json.load(f)
        assert frozenset(manifest["optional"]) == OPTIONAL_METHODS

    def test_manifest_version_matches_constant(self, vendored_schema_dir: Path):
        manifest_path = vendored_schema_dir / "required-methods.json"
        if not manifest_path.exists():
            pytest.skip("required-methods.json not yet generated")
        import json

        with open(manifest_path) as f:
            manifest = json.load(f)
        assert manifest["codex_version"] == TESTED_CODEX_VERSION
