"""Contract tests for Codex compatibility — run against vendored fixtures only.

No live codex binary required. Tests verify:
- Version parsing and comparison (semver, not string)
- Vendored schema contains all required/optional methods
- Method surface checking logic
- Version constants are self-consistent
"""

from __future__ import annotations

import subprocess

import pytest

from pathlib import Path

from unittest.mock import patch

from server.codex_compat import (
    MINIMUM_CODEX_VERSION,
    OPTIONAL_METHODS,
    REQUIRED_METHODS,
    TESTED_CODEX_VERSION,
    CompatCheckResult,
    SemVer,
    check_live_runtime_compatibility,
    check_method_surface,
    check_version_floor,
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
        mock_result = type(
            "Result", (), {"stdout": stdout, "returncode": 0, "stderr": ""}
        )()
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


class TestGetCodexVersionErrors:
    """Unit tests for get_codex_version() failure-mode translation."""

    def test_binary_not_found(self):
        with patch("server.codex_compat.subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(RuntimeError, match="not found on PATH"):
                get_codex_version()

    def test_timeout(self):
        with patch(
            "server.codex_compat.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="codex", timeout=10),
        ):
            with pytest.raises(RuntimeError, match="timed out"):
                get_codex_version()

    def test_nonzero_exit(self):
        mock_result = subprocess.CompletedProcess(
            args=["codex", "--version"], returncode=1, stdout="", stderr="error msg"
        )
        with patch("server.codex_compat.subprocess.run", return_value=mock_result):
            with pytest.raises(RuntimeError, match="exit code 1"):
                get_codex_version()


class TestCheckVersionFloorMocked:
    """Mocked unit tests for check_version_floor() — the three startup outcomes."""

    def test_binary_unavailable(self):
        with patch(
            "server.codex_compat.get_codex_version",
            side_effect=RuntimeError("Codex binary not found on PATH"),
        ):
            result = check_version_floor()
        assert result.passed is False
        assert result.codex_version is None
        assert result.available_methods == frozenset()
        assert len(result.errors) == 1
        assert "not found" in result.errors[0]

    def test_below_minimum(self):
        old_version = SemVer(0, 1, 0)
        with patch("server.codex_compat.get_codex_version", return_value=old_version):
            result = check_version_floor()
        assert result.passed is False
        assert result.codex_version == old_version
        assert result.available_methods == frozenset()
        assert len(result.errors) == 1
        assert "below minimum" in result.errors[0]

    def test_exact_tested_version(self):
        tested = SemVer.parse(TESTED_CODEX_VERSION)
        with patch("server.codex_compat.get_codex_version", return_value=tested):
            result = check_version_floor()
        assert result.passed is True
        assert result.codex_version == tested
        assert result.errors == ()
        assert REQUIRED_METHODS <= result.available_methods
        assert OPTIONAL_METHODS <= result.available_methods

    def test_newer_than_tested_version(self):
        newer = SemVer(99, 0, 0)
        with patch("server.codex_compat.get_codex_version", return_value=newer):
            result = check_version_floor()
        assert result.passed is True
        assert result.codex_version == newer
        assert result.errors == ()
        assert result.available_methods == frozenset()


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
        assert minimum <= tested, (
            "MINIMUM_CODEX_VERSION must not exceed TESTED_CODEX_VERSION"
        )

    def test_required_and_optional_disjoint(self):
        overlap = REQUIRED_METHODS & OPTIONAL_METHODS
        assert overlap == frozenset(), (
            f"Methods in both required and optional: {overlap}"
        )


class TestExtractClientMethods:
    def test_extracts_methods_from_vendored_schema(self, client_request_schema: Path):
        methods = extract_client_methods(client_request_schema)
        assert isinstance(methods, frozenset)
        assert len(methods) > 0

    def test_vendored_schema_contains_all_required_methods(
        self, client_request_schema: Path
    ):
        methods = extract_client_methods(client_request_schema)
        missing = REQUIRED_METHODS - methods
        assert missing == frozenset(), (
            f"Vendored schema missing required methods: {sorted(missing)}"
        )

    def test_vendored_schema_contains_all_optional_methods(
        self, client_request_schema: Path
    ):
        methods = extract_client_methods(client_request_schema)
        missing = OPTIONAL_METHODS - methods
        assert missing == frozenset(), (
            f"Vendored schema missing optional methods: {sorted(missing)}"
        )

    def test_vendored_schema_contains_initialize(self, client_request_schema: Path):
        methods = extract_client_methods(client_request_schema)
        assert "initialize" in methods

    def test_rejects_schema_without_one_of(self, tmp_path: Path):
        schema_file = tmp_path / "ClientRequest.json"
        schema_file.write_text('{"anyOf": []}')
        with pytest.raises(ValueError, match="no 'oneOf' key"):
            extract_client_methods(schema_file)

    def test_rejects_variants_with_no_methods(self, tmp_path: Path):
        schema_file = tmp_path / "ClientRequest.json"
        schema_file.write_text('{"oneOf": [{"properties": {}}]}')
        with pytest.raises(ValueError, match="0 methods extracted"):
            extract_client_methods(schema_file)


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


class TestLiveRuntimeCompatibilityMocked:
    def test_live_probe_success(self):
        available = REQUIRED_METHODS | OPTIONAL_METHODS
        with (
            patch(
                "server.codex_compat.check_version_floor",
                return_value=CompatCheckResult.from_version_check(
                    codex_version=SemVer.parse(TESTED_CODEX_VERSION),
                    available_methods=available,
                ),
            ),
            patch(
                "server.codex_compat.probe_live_method_surface",
                return_value=available,
            ),
        ):
            result = check_live_runtime_compatibility()
        assert result.passed is True
        assert result.available_methods == available

    def test_live_probe_missing_required_fails_closed(self):
        available = REQUIRED_METHODS - {"thread/start"}
        with (
            patch(
                "server.codex_compat.check_version_floor",
                return_value=CompatCheckResult.from_version_check(
                    codex_version=SemVer.parse(TESTED_CODEX_VERSION),
                    available_methods=available,
                ),
            ),
            patch(
                "server.codex_compat.probe_live_method_surface",
                return_value=available,
            ),
        ):
            result = check_live_runtime_compatibility()
        assert result.passed is False
        assert "required methods missing" in result.errors[0]

    def test_live_probe_error_translates_to_failed_result(self):
        with (
            patch(
                "server.codex_compat.check_version_floor",
                return_value=CompatCheckResult.from_version_check(
                    codex_version=SemVer.parse(TESTED_CODEX_VERSION),
                ),
            ),
            patch(
                "server.codex_compat.probe_live_method_surface",
                side_effect=RuntimeError("boom"),
            ),
        ):
            result = check_live_runtime_compatibility()
        assert result.passed is False
        assert result.errors == ("boom",)


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
