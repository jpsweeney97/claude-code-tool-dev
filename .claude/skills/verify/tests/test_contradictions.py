#!/usr/bin/env python3
"""Tests for contradiction detection functionality."""

import sys
import tempfile
import unittest
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from detect_contradictions import (
    find_contradictions,
    has_opposite_verdict,
    has_antonym_pair,
    extract_subject,
    normalize_claim_text,
)


class TestNormalizeClaimText(unittest.TestCase):
    """Tests for claim text normalization."""

    def test_lowercase(self):
        result = normalize_claim_text("Exit Code 0")
        self.assertEqual(result, "exit code 0")

    def test_removes_backticks(self):
        result = normalize_claim_text("`name` field")
        self.assertEqual(result, "name field")

    def test_removes_quotes(self):
        result = normalize_claim_text("'name' field")
        self.assertEqual(result, "name field")


class TestExtractSubject(unittest.TestCase):
    """Tests for subject extraction."""

    def test_extract_exit_code_subject(self):
        result = extract_subject("exit code 2 blocks execution")
        self.assertIn("exit code", result.lower())

    def test_extract_field_subject(self):
        result = extract_subject("`name` field is required")
        self.assertIn("name", result.lower())


class TestHasOppositeVerdict(unittest.TestCase):
    """Tests for verdict comparison."""

    def test_verified_vs_false(self):
        self.assertTrue(has_opposite_verdict("✓ Verified", "✗ False"))

    def test_verified_vs_contradicted(self):
        self.assertTrue(has_opposite_verdict("✓ Verified", "✗ Contradicted"))

    def test_both_verified(self):
        self.assertFalse(has_opposite_verdict("✓ Verified", "✓ Verified"))

    def test_both_false(self):
        self.assertFalse(has_opposite_verdict("✗ False", "✗ False"))


class TestHasAntonymPair(unittest.TestCase):
    """Tests for antonym pair detection."""

    def test_required_optional(self):
        has_antonym, desc = has_antonym_pair(
            "name field is required",
            "name field is optional"
        )
        self.assertTrue(has_antonym)
        self.assertIn("required", desc)

    def test_blocks_nonblocking(self):
        has_antonym, desc = has_antonym_pair(
            "exit code 1 blocks",
            "exit code 1 is non-blocking"
        )
        self.assertTrue(has_antonym)

    def test_no_antonyms(self):
        has_antonym, desc = has_antonym_pair(
            "name field is required",
            "description field is required"
        )
        self.assertFalse(has_antonym)


class TestFindContradictions(unittest.TestCase):
    """Tests for finding contradictions in claims."""

    def setUp(self):
        # Test content with contradictions
        self.test_content_with_contradictions = """# Known Claims

## Skills

| Claim | Verdict | Evidence | Verified |
|-------|---------|----------|----------|
| name field is required | ✓ Verified | "required" | 2026-01-05 |
| name field is optional | ✓ Verified | "optional" | 2026-01-04 |

## Hooks

| Claim | Verdict | Evidence | Verified |
|-------|---------|----------|----------|
| exit code 0 means success | ✓ Verified | "success" | 2026-01-05 |
"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        self.temp_file.write(self.test_content_with_contradictions)
        self.temp_file.close()
        self.temp_path = Path(self.temp_file.name)

    def tearDown(self):
        self.temp_path.unlink()

    def test_finds_antonym_contradiction(self):
        contradictions = find_contradictions(self.temp_path)
        self.assertGreaterEqual(len(contradictions), 1)

        # Should find required vs optional contradiction
        reasons = [c.reason for c in contradictions]
        has_antonym = any("Antonym" in r for r in reasons)
        self.assertTrue(has_antonym)

    def test_contradiction_has_severity(self):
        contradictions = find_contradictions(self.temp_path)
        if contradictions:
            self.assertIn(contradictions[0].severity, ["HIGH", "MEDIUM", "LOW"])


class TestFindContradictionsNoConflicts(unittest.TestCase):
    """Tests with no contradictions."""

    def setUp(self):
        self.test_content_clean = """# Known Claims

## Skills

| Claim | Verdict | Evidence | Verified |
|-------|---------|----------|----------|
| name field is required | ✓ Verified | "required" | 2026-01-05 |
| description field is required | ✓ Verified | "required" | 2026-01-05 |

## Hooks

| Claim | Verdict | Evidence | Verified |
|-------|---------|----------|----------|
| exit code 0 means success | ✓ Verified | "success" | 2026-01-05 |
| exit code 2 means block | ✓ Verified | "block" | 2026-01-05 |
"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        self.temp_file.write(self.test_content_clean)
        self.temp_file.close()
        self.temp_path = Path(self.temp_file.name)

    def tearDown(self):
        self.temp_path.unlink()

    def test_no_contradictions_found(self):
        contradictions = find_contradictions(self.temp_path)
        self.assertEqual(len(contradictions), 0)


class TestFindContradictionsCrossSection(unittest.TestCase):
    """Tests for cross-section contradictions."""

    def setUp(self):
        self.test_content = """# Known Claims

## Skills

| Claim | Verdict | Evidence | Verified |
|-------|---------|----------|----------|
| description field is required | ✓ Verified | "required for skills" | 2026-01-05 |

## Commands

| Claim | Verdict | Evidence | Verified |
|-------|---------|----------|----------|
| description field is required | ✗ False | "optional for commands" | 2026-01-05 |
"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        self.temp_file.write(self.test_content)
        self.temp_file.close()
        self.temp_path = Path(self.temp_file.name)

    def tearDown(self):
        self.temp_path.unlink()

    def test_finds_cross_section_contradiction(self):
        contradictions = find_contradictions(self.temp_path)
        self.assertGreaterEqual(len(contradictions), 1)

    def test_same_section_only_skips_cross_section(self):
        contradictions = find_contradictions(self.temp_path, same_section_only=True)
        self.assertEqual(len(contradictions), 0)


if __name__ == "__main__":
    unittest.main()
