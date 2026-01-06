#!/usr/bin/env python3
"""Tests for _common.py utilities."""

import sys
import unittest
from datetime import date
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from _common import parse_verified_date, Version, DEFAULT_MAX_AGE_DAYS, SECTION_ALIASES


class TestParseVerifiedDate(unittest.TestCase):
    """Tests for parse_verified_date function."""

    def test_plain_date(self):
        result = parse_verified_date("2026-01-05")
        self.assertEqual(result, date(2026, 1, 5))

    def test_version_tagged_date(self):
        result = parse_verified_date("2026-01-05 (v2.0.76)")
        self.assertEqual(result, date(2026, 1, 5))

    def test_version_tagged_with_extra_spaces(self):
        result = parse_verified_date("2026-01-05  (v2.0.76)")
        self.assertEqual(result, date(2026, 1, 5))

    def test_none_input(self):
        result = parse_verified_date(None)
        self.assertIsNone(result)

    def test_invalid_date(self):
        result = parse_verified_date("not-a-date")
        self.assertIsNone(result)

    def test_empty_string(self):
        result = parse_verified_date("")
        self.assertIsNone(result)

    def test_partial_date(self):
        result = parse_verified_date("2026-01")
        self.assertIsNone(result)


class TestVersion(unittest.TestCase):
    """Tests for Version class."""

    def test_parse_simple(self):
        v = Version.parse("2.0.76")
        self.assertIsNotNone(v)
        self.assertEqual(v.major, 2)
        self.assertEqual(v.minor, 0)
        self.assertEqual(v.patch, 76)
        self.assertIsNone(v.prerelease)

    def test_parse_with_v_prefix(self):
        v = Version.parse("v2.0.76")
        self.assertIsNotNone(v)
        self.assertEqual(v.major, 2)

    def test_parse_with_prerelease(self):
        v = Version.parse("3.0.0-beta.1")
        self.assertIsNotNone(v)
        self.assertEqual(v.prerelease, "beta.1")

    def test_parse_invalid(self):
        v = Version.parse("not-a-version")
        self.assertIsNone(v)

    def test_str(self):
        v = Version(2, 0, 76)
        self.assertEqual(str(v), "2.0.76")

    def test_str_with_prerelease(self):
        v = Version(3, 0, 0, "beta.1")
        self.assertEqual(str(v), "3.0.0-beta.1")

    def test_comparison_major(self):
        v1 = Version(1, 0, 0)
        v2 = Version(2, 0, 0)
        self.assertLess(v1, v2)

    def test_comparison_minor(self):
        v1 = Version(2, 0, 0)
        v2 = Version(2, 1, 0)
        self.assertLess(v1, v2)

    def test_comparison_patch(self):
        v1 = Version(2, 0, 0)
        v2 = Version(2, 0, 1)
        self.assertLess(v1, v2)


class TestConstants(unittest.TestCase):
    """Tests for module constants."""

    def test_default_max_age_days(self):
        self.assertEqual(DEFAULT_MAX_AGE_DAYS, 90)

    def test_section_aliases_exist(self):
        self.assertIn("hook", SECTION_ALIASES)
        self.assertIn("skill", SECTION_ALIASES)
        self.assertEqual(SECTION_ALIASES["hook"], "Hooks")


if __name__ == "__main__":
    unittest.main()
