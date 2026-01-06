#!/usr/bin/env python3
"""Tests for cache statistics functionality."""

import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


class TestCacheStats(unittest.TestCase):
    """Tests for cache statistics calculation."""

    def setUp(self):
        self.test_content = """# Known Claims

## Skills

**Source:** https://example.com/skills

| Claim | Verdict | Evidence | Verified |
|-------|---------|----------|----------|
| name is required | ✓ Verified | "required" | 2026-01-05 |
| license is optional | ✓ Verified | "optional" | 2025-12-01 |

## Hooks

**Source:** https://example.com/hooks

| Claim | Verdict | Evidence | Verified |
|-------|---------|----------|----------|
| exit code 0 means success | ✓ Verified | "success" | 2026-01-05 |
| exit code 1 blocks | ✗ False | "non-blocking" | 2025-10-01 |
| exit code 2 blocks | ~ Partial | "depends" | 2026-01-03 |
"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        self.temp_file.write(self.test_content)
        self.temp_file.close()
        self.temp_path = Path(self.temp_file.name)

    def tearDown(self):
        self.temp_path.unlink()

    def test_calculate_stats_total_count(self):
        from verify import calculate_cache_stats
        stats = calculate_cache_stats(self.temp_path)
        self.assertEqual(stats["total"], 5)

    def test_calculate_stats_by_section(self):
        from verify import calculate_cache_stats
        stats = calculate_cache_stats(self.temp_path)
        self.assertEqual(stats["by_section"]["Skills"], 2)
        self.assertEqual(stats["by_section"]["Hooks"], 3)

    def test_calculate_stats_by_verdict(self):
        from verify import calculate_cache_stats
        stats = calculate_cache_stats(self.temp_path)
        self.assertEqual(stats["by_verdict"]["verified"], 3)
        self.assertEqual(stats["by_verdict"]["false"], 1)
        self.assertEqual(stats["by_verdict"]["partial"], 1)

    def test_calculate_stats_by_age(self):
        from verify import calculate_cache_stats
        stats = calculate_cache_stats(self.temp_path, max_age_days=90)
        # Age buckets: fresh (<30d), aging (30-90d), stale (>90d)
        self.assertIn("fresh", stats["by_age"])
        self.assertIn("aging", stats["by_age"])
        self.assertIn("stale", stats["by_age"])

    def test_calculate_stats_empty_file(self):
        """Test stats on a non-existent file returns empty stats."""
        from verify import calculate_cache_stats
        non_existent = Path("/tmp/does-not-exist-12345.md")
        stats = calculate_cache_stats(non_existent)
        self.assertEqual(stats["total"], 0)
        self.assertEqual(stats["by_section"], {})
        self.assertEqual(stats["by_verdict"], {})
        self.assertEqual(stats["by_age"], {"fresh": 0, "aging": 0, "stale": 0})
        self.assertIsNone(stats["oldest_claim"])
        self.assertIsNone(stats["newest_claim"])

    def test_calculate_stats_oldest_newest(self):
        """Test that oldest and newest claims are tracked."""
        from verify import calculate_cache_stats
        stats = calculate_cache_stats(self.temp_path)
        # The test data has dates: 2026-01-05, 2025-12-01, 2026-01-05, 2025-10-01, 2026-01-03
        # Oldest should be 2025-10-01 ("exit code 1 blocks")
        # Newest should be one of 2026-01-05
        self.assertEqual(stats["oldest_claim"], "exit code 1 blocks")
        self.assertIn(stats["newest_claim"], ["name is required", "exit code 0 means success"])


if __name__ == "__main__":
    unittest.main()
