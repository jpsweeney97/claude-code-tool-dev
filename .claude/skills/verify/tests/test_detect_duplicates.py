#!/usr/bin/env python3
"""Tests for duplicate detection functionality."""

import sys
import tempfile
import unittest
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


class TestDuplicateDetection(unittest.TestCase):
    """Tests for finding duplicate/similar claims."""

    def setUp(self):
        self.test_content = """# Known Claims

## Skills

| Claim | Verdict | Evidence | Verified |
|-------|---------|----------|----------|
| name field is required | ✓ Verified | "required" | 2026-01-05 |
| the name field is required in frontmatter | ✓ Verified | "required" | 2026-01-04 |
| license is optional | ✓ Verified | "optional" | 2026-01-05 |

## Hooks

| Claim | Verdict | Evidence | Verified |
|-------|---------|----------|----------|
| exit code 0 means success | ✓ Verified | "success" | 2026-01-05 |
| exit code 0 indicates success | ✓ Verified | "success" | 2026-01-03 |
| exit code 2 blocks execution | ✓ Verified | "blocks" | 2026-01-05 |
"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        self.temp_file.write(self.test_content)
        self.temp_file.close()
        self.temp_path = Path(self.temp_file.name)

    def tearDown(self):
        self.temp_path.unlink()

    def test_find_duplicates_returns_groups(self):
        from detect_duplicates import find_duplicate_groups
        groups = find_duplicate_groups(self.temp_path, threshold=0.7)
        self.assertIsInstance(groups, list)

    def test_find_duplicates_detects_similar_claims(self):
        from detect_duplicates import find_duplicate_groups
        groups = find_duplicate_groups(self.temp_path, threshold=0.7)
        # Should find at least 2 groups: name field and exit code 0
        self.assertGreaterEqual(len(groups), 2)

    def test_find_duplicates_group_structure(self):
        from detect_duplicates import find_duplicate_groups
        groups = find_duplicate_groups(self.temp_path, threshold=0.7)
        if groups:
            group = groups[0]
            self.assertIn("claims", group)
            self.assertIn("similarity", group)
            self.assertGreaterEqual(len(group["claims"]), 2)

    def test_find_duplicates_respects_threshold(self):
        from detect_duplicates import find_duplicate_groups
        # High threshold = fewer matches
        groups_high = find_duplicate_groups(self.temp_path, threshold=0.95)
        groups_low = find_duplicate_groups(self.temp_path, threshold=0.5)
        self.assertLessEqual(len(groups_high), len(groups_low))

    def test_find_duplicates_nonexistent_file(self):
        from detect_duplicates import find_duplicate_groups
        groups = find_duplicate_groups(Path("/nonexistent/path"), threshold=0.7)
        self.assertEqual(groups, [])

    def test_find_duplicates_same_section_only(self):
        from detect_duplicates import find_duplicate_groups
        # With same_section_only=True, should only find duplicates within sections
        groups = find_duplicate_groups(self.temp_path, threshold=0.7, same_section_only=True)
        for group in groups:
            # All claims in group should have the same section
            if group["claims"]:
                sections = set(c["section"] for c in group["claims"])
                self.assertEqual(len(sections), 1)


class TestCalculateDuplicateSimilarity(unittest.TestCase):
    """Tests for similarity calculation used in duplicate detection."""

    def test_identical_strings(self):
        from detect_duplicates import calculate_duplicate_similarity
        score = calculate_duplicate_similarity("exit code 0", "exit code 0")
        self.assertEqual(score, 1.0)

    def test_similar_strings(self):
        from detect_duplicates import calculate_duplicate_similarity
        score = calculate_duplicate_similarity(
            "exit code 0 means success",
            "exit code 0 indicates success"
        )
        self.assertGreater(score, 0.7)

    def test_different_strings(self):
        from detect_duplicates import calculate_duplicate_similarity
        score = calculate_duplicate_similarity(
            "exit code 0",
            "license is optional"
        )
        self.assertLess(score, 0.3)


if __name__ == "__main__":
    unittest.main()
