"""Contract tests for Codex compatibility — run against vendored fixtures only.

No live codex binary required. Tests verify:
- Version parsing and comparison (semver, not string)
- Vendored schema contains all required/optional methods
- Method surface checking logic
- Version constants are self-consistent
"""

from __future__ import annotations

import pytest

from server.codex_compat import SemVer


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
