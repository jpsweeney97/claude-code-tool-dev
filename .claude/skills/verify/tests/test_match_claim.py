#!/usr/bin/env python3
"""Tests for match_claim.py fuzzy matching."""

import sys
import tempfile
import unittest
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from match_claim import (
    parse_known_claims,
    find_best_match,
    find_top_matches,
    normalize_section,
    calculate_similarity,
    discover_sections,
    MatchResult,
    THRESHOLD_LOW,
)


class TestCalculateSimilarity(unittest.TestCase):
    """Tests for similarity scoring."""

    def test_exact_match(self):
        score = calculate_similarity("exit code 0 means success", "exit code 0 means success")
        self.assertEqual(score, 1.0)

    def test_case_insensitive(self):
        score = calculate_similarity("Exit Code 0", "exit code 0")
        self.assertGreater(score, 0.9)

    def test_partial_match(self):
        score = calculate_similarity("exit code 0", "exit code 0 means success")
        self.assertGreater(score, 0.5)

    def test_no_match(self):
        score = calculate_similarity("completely different text", "something else entirely unrelated")
        self.assertLess(score, 0.3)

    def test_word_overlap(self):
        score = calculate_similarity("hook exit code", "hooks use exit codes")
        self.assertGreater(score, 0.4)


class TestParseKnownClaims(unittest.TestCase):
    """Tests for parsing known-claims.md format."""

    def setUp(self):
        self.test_content = """# Known Claims

## Skills

**Source:** https://example.com/skills

| Claim | Verdict | Evidence | Verified |
|-------|---------|----------|----------|
| name field is required | ✓ Verified | "must include name" | 2026-01-05 |
| license is optional | ✓ Verified | "not required" | 2026-01-05 |

## Hooks

**Source:** https://example.com/hooks

| Claim | Verdict | Evidence | Verified |
|-------|---------|----------|----------|
| exit code 0 means success | ✓ Verified | "Exit code 0: Success" | 2026-01-05 |
"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        self.temp_file.write(self.test_content)
        self.temp_file.close()
        self.temp_path = Path(self.temp_file.name)

    def tearDown(self):
        self.temp_path.unlink()

    def test_parse_claims_count(self):
        claims = parse_known_claims(self.temp_path)
        self.assertEqual(len(claims), 3)

    def test_parse_claims_sections(self):
        claims = parse_known_claims(self.temp_path)
        sections = set(c["section"] for c in claims)
        self.assertEqual(sections, {"Skills", "Hooks"})

    def test_parse_claims_verdict(self):
        claims = parse_known_claims(self.temp_path)
        for c in claims:
            self.assertIn("✓", c["verdict"])

    def test_parse_claims_structure(self):
        claims = parse_known_claims(self.temp_path)
        # Check required keys exist
        for c in claims:
            self.assertIn("claim", c)
            self.assertIn("verdict", c)
            self.assertIn("evidence", c)
            self.assertIn("section", c)


class TestDiscoverSections(unittest.TestCase):
    """Tests for section discovery."""

    def setUp(self):
        self.test_content = """# Known Claims

## How to Use

Some documentation...

## Skills

| Claim | Verdict |

## Hooks

| Claim | Verdict |

## Maintenance

Some notes...
"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        self.temp_file.write(self.test_content)
        self.temp_file.close()
        self.temp_path = Path(self.temp_file.name)

    def tearDown(self):
        self.temp_path.unlink()

    def test_discover_sections_excludes_meta(self):
        sections = discover_sections(self.temp_path)
        self.assertIn("Skills", sections)
        self.assertIn("Hooks", sections)
        self.assertNotIn("How to Use", sections)
        self.assertNotIn("Maintenance", sections)

    def test_discover_sections_nonexistent_file(self):
        sections = discover_sections(Path("/nonexistent/path"))
        self.assertEqual(sections, set())


class TestFindBestMatch(unittest.TestCase):
    """Tests for best match finding."""

    def setUp(self):
        self.test_content = """# Known Claims

## Hooks

| Claim | Verdict | Evidence | Verified |
|-------|---------|----------|----------|
| Exit code 0 means success | ✓ Verified | "Success" | 2026-01-05 |
| Exit code 1 is non-blocking error | ✓ Verified | "Non-blocking" | 2026-01-05 |
| Exit code 2 blocks execution | ✓ Verified | "Blocking" | 2026-01-05 |
"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        self.temp_file.write(self.test_content)
        self.temp_file.close()
        self.temp_path = Path(self.temp_file.name)

    def tearDown(self):
        self.temp_path.unlink()

    def test_exact_match(self):
        claims = parse_known_claims(self.temp_path)
        result = find_best_match("Exit code 0 means success", claims, threshold=THRESHOLD_LOW)
        self.assertTrue(result.matched)
        self.assertGreater(result.confidence, 0.9)

    def test_partial_match(self):
        claims = parse_known_claims(self.temp_path)
        result = find_best_match("exit code 2", claims, threshold=THRESHOLD_LOW)
        self.assertTrue(result.matched)
        self.assertIn("2", result.known_claim)

    def test_no_match_below_threshold(self):
        claims = parse_known_claims(self.temp_path)
        result = find_best_match("something completely unrelated xyz", claims, threshold=0.5)
        self.assertFalse(result.matched)


class TestFindTopMatches(unittest.TestCase):
    """Tests for finding multiple matches."""

    def setUp(self):
        self.test_content = """# Known Claims

## Hooks

| Claim | Verdict | Evidence | Verified |
|-------|---------|----------|----------|
| Exit code 0 means success | ✓ Verified | "Success" | 2026-01-05 |
| Exit code 1 is non-blocking error | ✓ Verified | "Non-blocking" | 2026-01-05 |
| Exit code 2 blocks execution | ✓ Verified | "Blocking" | 2026-01-05 |
"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        self.temp_file.write(self.test_content)
        self.temp_file.close()
        self.temp_path = Path(self.temp_file.name)

    def tearDown(self):
        self.temp_path.unlink()

    def test_top_matches_returns_multiple(self):
        claims = parse_known_claims(self.temp_path)
        result = find_top_matches("exit code", claims, top_n=3, threshold=0.0)
        self.assertEqual(len(result.matches), 3)

    def test_top_matches_sorted_by_confidence(self):
        claims = parse_known_claims(self.temp_path)
        result = find_top_matches("exit code", claims, top_n=3, threshold=0.0)
        confidences = [m.confidence for m in result.matches]
        self.assertEqual(confidences, sorted(confidences, reverse=True))

    def test_top_matches_total_checked(self):
        claims = parse_known_claims(self.temp_path)
        result = find_top_matches("exit code", claims, top_n=3, threshold=0.0)
        self.assertEqual(result.total_checked, 3)


class TestNormalizeSection(unittest.TestCase):
    """Tests for section normalization."""

    def test_exact_match(self):
        valid = {"Skills", "Hooks", "Commands"}
        result = normalize_section("Skills", valid)
        self.assertEqual(result, "Skills")

    def test_case_insensitive(self):
        valid = {"Skills", "Hooks", "Commands"}
        result = normalize_section("skills", valid)
        self.assertEqual(result, "Skills")

    def test_alias(self):
        valid = {"Skills", "Hooks", "Commands"}
        result = normalize_section("hook", valid)
        self.assertEqual(result, "Hooks")

    def test_invalid(self):
        valid = {"Skills", "Hooks", "Commands"}
        result = normalize_section("NotASection", valid)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
