"""Integration tests for Codex compatibility — require a live codex binary.

These tests are skipped in CI environments without codex installed.
They verify the version-floor startup check against the actual installed binary.

Method-surface probing (initialize handshake + capability check) is deferred to
build step 1 when the JSON-RPC client exists. T1 relies on the version floor
plus vendored-schema contract tests to guarantee method presence.
"""

from __future__ import annotations

import shutil

import pytest

from server.codex_compat import (
    MINIMUM_CODEX_VERSION,
    OPTIONAL_METHODS,
    REQUIRED_METHODS,
    CompatCheckResult,
    SemVer,
    check_version_floor,
    get_codex_version,
)

pytestmark = pytest.mark.skipif(
    shutil.which("codex") is None,
    reason="codex binary not found on PATH",
)


class TestGetCodexVersion:
    def test_returns_semver(self):
        version = get_codex_version()
        assert isinstance(version, SemVer)

    def test_version_meets_minimum(self):
        version = get_codex_version()
        minimum = SemVer.parse(MINIMUM_CODEX_VERSION)
        assert version >= minimum, (
            f"Installed codex {version} is below minimum {minimum}"
        )


class TestCheckVersionFloor:
    def test_passes_with_current_binary(self):
        result = check_version_floor()
        assert result.passed, f"Version floor check failed: {result.errors}"

    def test_reports_version(self):
        result = check_version_floor()
        assert result.codex_version is not None

    def test_errors_empty_on_pass(self):
        result = check_version_floor()
        if result.passed:
            assert result.errors == ()


class TestFeatureGating:
    def test_has_capability_true_for_required(self):
        result = CompatCheckResult.from_version_check(
            codex_version=SemVer.parse("0.117.0"),
            available_methods=REQUIRED_METHODS | OPTIONAL_METHODS,
        )
        assert result.has_capability("thread/start")

    def test_has_capability_false_for_nonexistent(self):
        result = CompatCheckResult.from_version_check(
            codex_version=SemVer.parse("0.117.0"),
            available_methods=REQUIRED_METHODS | OPTIONAL_METHODS,
        )
        assert not result.has_capability("nonexistent/method")

    def test_has_capability_for_optional_method(self):
        result = CompatCheckResult.from_version_check(
            codex_version=SemVer.parse("0.117.0"),
            available_methods=REQUIRED_METHODS,  # no optional
        )
        assert not result.has_capability("turn/steer")

    def test_has_capability_returns_bool(self):
        result = CompatCheckResult.from_version_check(
            codex_version=SemVer.parse("0.117.0"),
            available_methods=REQUIRED_METHODS | OPTIONAL_METHODS,
        )
        assert isinstance(result.has_capability("turn/steer"), bool)
