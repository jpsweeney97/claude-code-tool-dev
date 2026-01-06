#!/usr/bin/env python3
"""Tests for backup_cache.py backup/restore functionality."""

import sys
import tempfile
import shutil
import unittest
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from backup_cache import create_backup, list_backups, restore_backup, diff_backup, MAX_BACKUPS


class TestBackupCache(unittest.TestCase):
    """Tests for backup and restore operations."""

    def setUp(self):
        # Create temp directory for testing
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_file = self.temp_dir / "known-claims.md"
        self.backup_dir = self.temp_dir / ".backups"

        # Create test content
        self.test_file.write_text("# Known Claims\n\nTest content line 1\nTest content line 2\n")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_create_backup(self):
        backup_path = create_backup(self.test_file, self.backup_dir)
        self.assertIsNotNone(backup_path)
        self.assertTrue(backup_path.exists())
        self.assertTrue(backup_path.name.startswith("known-claims_"))

    def test_backup_content_matches(self):
        backup_path = create_backup(self.test_file, self.backup_dir)
        original_content = self.test_file.read_text()
        backup_content = backup_path.read_text()
        self.assertEqual(original_content, backup_content)

    def test_backup_nonexistent_source(self):
        nonexistent = self.temp_dir / "nonexistent.md"
        result = create_backup(nonexistent, self.backup_dir)
        self.assertIsNone(result)

    def test_list_backups_empty(self):
        backups = list_backups(self.backup_dir)
        self.assertEqual(len(backups), 0)

    def test_list_backups_after_create(self):
        create_backup(self.test_file, self.backup_dir)
        backups = list_backups(self.backup_dir)
        self.assertEqual(len(backups), 1)

    def test_list_backups_order(self):
        # Create backup files directly to avoid timing issues
        # (backup timestamps use seconds precision)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        older = self.backup_dir / "known-claims_20260101_100000.md"
        newer = self.backup_dir / "known-claims_20260101_100001.md"
        older.write_text("older content")
        newer.write_text("newer content")

        backups = list_backups(self.backup_dir)
        self.assertEqual(len(backups), 2)
        # Newest should be first (reverse sorted by name which includes timestamp)
        self.assertEqual(backups[0].name, "known-claims_20260101_100001.md")
        self.assertEqual(backups[1].name, "known-claims_20260101_100000.md")

    def test_max_backups_enforced(self):
        # Create backup files directly to avoid timing issues
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Create more than MAX_BACKUPS files
        for i in range(MAX_BACKUPS + 3):
            backup = self.backup_dir / f"known-claims_20260101_10000{i}.md"
            backup.write_text(f"backup {i}")

        # Now call create_backup which should trigger cleanup
        create_backup(self.test_file, self.backup_dir)

        backups = list_backups(self.backup_dir)
        self.assertEqual(len(backups), MAX_BACKUPS)

    def test_restore_backup(self):
        # Create backup
        backup_path = create_backup(self.test_file, self.backup_dir)

        # Modify original
        self.test_file.write_text("Modified content")
        self.assertEqual(self.test_file.read_text(), "Modified content")

        # Restore
        success = restore_backup(backup_path, self.test_file)
        self.assertTrue(success)
        self.assertIn("Test content", self.test_file.read_text())

    def test_restore_preserves_content(self):
        # Test that restore properly overwrites target with backup content
        # Note: The backup-before-restore feature uses module-level BACKUP_DIR
        # which cannot be easily tested without modifying production code
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = self.backup_dir / "known-claims_20250101_100000.md"
        backup_path.write_text("Original content from backup")

        # Modify the target file
        self.test_file.write_text("Modified content")

        # Restore
        restore_backup(backup_path, self.test_file)

        # Target should now have backup content
        self.assertEqual(self.test_file.read_text(), "Original content from backup")

    def test_restore_nonexistent_backup(self):
        nonexistent = self.backup_dir / "nonexistent.md"
        result = restore_backup(nonexistent, self.test_file)
        self.assertFalse(result)

    def test_diff_backup(self):
        # Create backup
        backup_path = create_backup(self.test_file, self.backup_dir)

        # Modify original (add lines)
        current_content = self.test_file.read_text()
        self.test_file.write_text(current_content + "New line 1\nNew line 2\n")

        added, removed, unchanged = diff_backup(backup_path, self.test_file)
        self.assertEqual(added, 2)  # Two new lines
        self.assertEqual(removed, 0)

    def test_diff_backup_removed_lines(self):
        # Create backup with more content
        self.test_file.write_text("Line 1\nLine 2\nLine 3\n")
        backup_path = create_backup(self.test_file, self.backup_dir)

        # Remove lines
        self.test_file.write_text("Line 1\n")

        added, removed, unchanged = diff_backup(backup_path, self.test_file)
        self.assertEqual(added, 0)
        self.assertEqual(removed, 2)  # Line 2 and Line 3 removed
        self.assertEqual(unchanged, 1)  # Line 1 unchanged

    def test_diff_backup_nonexistent_files(self):
        added, removed, unchanged = diff_backup(
            self.backup_dir / "nonexistent.md",
            self.temp_dir / "also_nonexistent.md"
        )
        self.assertEqual((added, removed, unchanged), (0, 0, 0))


class TestMaxBackupsConstant(unittest.TestCase):
    """Tests for MAX_BACKUPS constant."""

    def test_max_backups_value(self):
        self.assertEqual(MAX_BACKUPS, 5)


if __name__ == "__main__":
    unittest.main()
