#!/usr/bin/env python3
"""Tests for coverage analysis functionality."""

import sys
import tempfile
import unittest
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


class TestCoverageAnalysis(unittest.TestCase):
    """Tests for documentation coverage analysis."""

    def setUp(self):
        self.test_content = """# Known Claims

## Skills

**Source:** https://code.claude.com/docs/en/skills.md

| Claim | Verdict | Evidence | Verified |
|-------|---------|----------|----------|
| name field is required | ✓ Verified | "required" | 2026-01-05 |
| description is required | ✓ Verified | "required" | 2026-01-05 |

## Hooks

**Source:** https://code.claude.com/docs/en/hooks.md

| Claim | Verdict | Evidence | Verified |
|-------|---------|----------|----------|
| exit code 0 means success | ✓ Verified | "success" | 2026-01-05 |
"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        self.temp_file.write(self.test_content)
        self.temp_file.close()
        self.temp_path = Path(self.temp_file.name)

    def tearDown(self):
        self.temp_path.unlink()

    def test_analyze_coverage_returns_dict(self):
        from coverage_analysis import analyze_coverage
        result = analyze_coverage(self.temp_path)
        self.assertIsInstance(result, dict)

    def test_analyze_coverage_counts_by_section(self):
        from coverage_analysis import analyze_coverage
        result = analyze_coverage(self.temp_path)
        self.assertEqual(result["sections"]["Skills"]["count"], 2)
        self.assertEqual(result["sections"]["Hooks"]["count"], 1)

    def test_analyze_coverage_identifies_sparse_sections(self):
        from coverage_analysis import analyze_coverage
        result = analyze_coverage(self.temp_path, min_claims=2)
        # Hooks has only 1 claim, below threshold
        sparse = [s for s, d in result["sections"].items() if d["sparse"]]
        self.assertIn("Hooks", sparse)

    def test_known_sections_constant(self):
        from coverage_analysis import KNOWN_SECTIONS
        self.assertIn("Skills", KNOWN_SECTIONS)
        self.assertIn("Hooks", KNOWN_SECTIONS)
        self.assertIn("Commands", KNOWN_SECTIONS)

    def test_analyze_coverage_missing_sections(self):
        from coverage_analysis import analyze_coverage, KNOWN_SECTIONS
        result = analyze_coverage(self.temp_path)
        # Test file only has Skills and Hooks - others should be missing
        for section in KNOWN_SECTIONS:
            if section not in ["Skills", "Hooks"]:
                self.assertIn(section, result["missing_sections"])

    def test_analyze_coverage_total_claims(self):
        from coverage_analysis import analyze_coverage
        result = analyze_coverage(self.temp_path)
        self.assertEqual(result["total_claims"], 3)

    def test_analyze_coverage_score(self):
        from coverage_analysis import analyze_coverage
        result = analyze_coverage(self.temp_path)
        # Score should be between 0 and 1
        self.assertGreaterEqual(result["coverage_score"], 0.0)
        self.assertLessEqual(result["coverage_score"], 1.0)

    def test_analyze_coverage_nonexistent_file(self):
        from coverage_analysis import analyze_coverage
        result = analyze_coverage(Path("/nonexistent/path"))
        self.assertEqual(result["total_claims"], 0)
        self.assertEqual(result["coverage_score"], 0.0)


class TestCoverageAnalysisThreshold(unittest.TestCase):
    """Tests for coverage threshold behavior."""

    def setUp(self):
        # Content with varying claim counts per section
        self.test_content = """# Known Claims

## Skills

| Claim | Verdict | Evidence | Verified |
|-------|---------|----------|----------|
| claim 1 | ✓ Verified | "1" | 2026-01-05 |
| claim 2 | ✓ Verified | "2" | 2026-01-05 |
| claim 3 | ✓ Verified | "3" | 2026-01-05 |
| claim 4 | ✓ Verified | "4" | 2026-01-05 |

## Hooks

| Claim | Verdict | Evidence | Verified |
|-------|---------|----------|----------|
| hook claim | ✓ Verified | "hook" | 2026-01-05 |
"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        self.temp_file.write(self.test_content)
        self.temp_file.close()
        self.temp_path = Path(self.temp_file.name)

    def tearDown(self):
        self.temp_path.unlink()

    def test_sparse_detection_with_min_claims_3(self):
        from coverage_analysis import analyze_coverage
        result = analyze_coverage(self.temp_path, min_claims=3)
        # Skills has 4 claims (not sparse), Hooks has 1 (sparse)
        self.assertFalse(result["sections"]["Skills"]["sparse"])
        self.assertTrue(result["sections"]["Hooks"]["sparse"])

    def test_sparse_detection_with_min_claims_5(self):
        from coverage_analysis import analyze_coverage
        result = analyze_coverage(self.temp_path, min_claims=5)
        # Both should be sparse with threshold of 5
        self.assertTrue(result["sections"]["Skills"]["sparse"])
        self.assertTrue(result["sections"]["Hooks"]["sparse"])


if __name__ == "__main__":
    unittest.main()
