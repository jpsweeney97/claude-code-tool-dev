#!/usr/bin/env python3
"""Tests for export/import functionality."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from export_import import (
    export_to_json,
    export_to_csv,
    export_claims,
    parse_json_import,
    parse_csv_import,
    find_import_conflicts,
)


class TestExportJson(unittest.TestCase):
    """Tests for JSON export."""

    def setUp(self):
        self.claims = [
            {
                "claim": "name is required",
                "section": "Skills",
                "verdict": "✓ Verified",
                "evidence": "docs confirm",
                "verified_date": "2026-01-05",
            },
            {
                "claim": "exit code 0 means success",
                "section": "Hooks",
                "verdict": "✓ Verified",
                "evidence": "success indicator",
                "verified_date": "2026-01-04",
            },
        ]

    def test_export_json_structure(self):
        content = export_to_json(self.claims)
        data = json.loads(content)

        self.assertIn("version", data)
        self.assertIn("exported_at", data)
        self.assertIn("count", data)
        self.assertIn("claims", data)

    def test_export_json_count(self):
        content = export_to_json(self.claims)
        data = json.loads(content)

        self.assertEqual(data["count"], 2)
        self.assertEqual(len(data["claims"]), 2)

    def test_export_json_claim_fields(self):
        content = export_to_json(self.claims)
        data = json.loads(content)

        claim = data["claims"][0]
        self.assertIn("claim", claim)
        self.assertIn("section", claim)
        self.assertIn("verdict", claim)
        self.assertIn("evidence", claim)
        self.assertIn("verified_date", claim)


class TestExportCsv(unittest.TestCase):
    """Tests for CSV export."""

    def setUp(self):
        self.claims = [
            {
                "claim": "name is required",
                "section": "Skills",
                "verdict": "✓ Verified",
                "evidence": "docs confirm",
                "verified_date": "2026-01-05",
            },
        ]

    def test_export_csv_has_header(self):
        content = export_to_csv(self.claims)
        lines = content.strip().split("\n")

        self.assertEqual(lines[0], "claim,section,verdict,evidence,verified_date")

    def test_export_csv_has_data(self):
        content = export_to_csv(self.claims)
        lines = content.strip().split("\n")

        self.assertEqual(len(lines), 2)  # Header + 1 claim


class TestImportJson(unittest.TestCase):
    """Tests for JSON import."""

    def test_parse_json_import(self):
        json_content = json.dumps({
            "version": "1.0",
            "claims": [
                {
                    "claim": "test claim",
                    "section": "Skills",
                    "verdict": "✓ Verified",
                    "evidence": "evidence",
                    "verified_date": "2026-01-05",
                }
            ]
        })

        claims = parse_json_import(json_content)
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0]["claim"], "test claim")
        self.assertEqual(claims[0]["section"], "Skills")


class TestImportCsv(unittest.TestCase):
    """Tests for CSV import."""

    def test_parse_csv_import(self):
        csv_content = "claim,section,verdict,evidence,verified_date\ntest claim,Skills,✓ Verified,evidence,2026-01-05\n"

        claims = parse_csv_import(csv_content)
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0]["claim"], "test claim")


class TestFindConflicts(unittest.TestCase):
    """Tests for import conflict detection."""

    def test_no_conflicts_different_claims(self):
        existing = [
            {"claim": "claim A", "section": "Skills", "verdict": "✓ Verified", "evidence": "ev", "verified_date": "2026-01-05"},
        ]
        incoming = [
            {"claim": "claim B", "section": "Skills", "verdict": "✓ Verified", "evidence": "ev", "verified_date": "2026-01-05"},
        ]

        conflicts = find_import_conflicts(existing, incoming)
        self.assertEqual(len(conflicts), 0)

    def test_conflict_same_claim_different_verdict(self):
        existing = [
            {"claim": "name is required", "section": "Skills", "verdict": "✓ Verified", "evidence": "ev1", "verified_date": "2026-01-05"},
        ]
        incoming = [
            {"claim": "name is required", "section": "Skills", "verdict": "✗ False", "evidence": "ev2", "verified_date": "2026-01-06"},
        ]

        conflicts = find_import_conflicts(existing, incoming)
        self.assertEqual(len(conflicts), 1)

    def test_no_conflict_same_claim_same_verdict(self):
        existing = [
            {"claim": "name is required", "section": "Skills", "verdict": "✓ Verified", "evidence": "ev1", "verified_date": "2026-01-05"},
        ]
        incoming = [
            {"claim": "name is required", "section": "Skills", "verdict": "✓ Verified", "evidence": "ev1", "verified_date": "2026-01-05"},
        ]

        conflicts = find_import_conflicts(existing, incoming)
        self.assertEqual(len(conflicts), 0)


class TestExportClaims(unittest.TestCase):
    """Tests for full export workflow."""

    def setUp(self):
        self.test_content = """# Known Claims

## Skills

**Source:** https://example.com/skills

| Claim | Verdict | Evidence | Verified |
|-------|---------|----------|----------|
| name is required | ✓ Verified | "required" | 2026-01-05 |

## Hooks

**Source:** https://example.com/hooks

| Claim | Verdict | Evidence | Verified |
|-------|---------|----------|----------|
| exit code 0 success | ✓ Verified | "success" | 2026-01-05 |
"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        self.temp_file.write(self.test_content)
        self.temp_file.close()
        self.temp_path = Path(self.temp_file.name)

    def tearDown(self):
        self.temp_path.unlink()

    def test_export_all_sections(self):
        content, result = export_claims(self.temp_path, format="json")
        self.assertEqual(result.count, 2)
        self.assertIn("Skills", result.sections)
        self.assertIn("Hooks", result.sections)

    def test_export_single_section(self):
        content, result = export_claims(self.temp_path, format="json", section_filter="Skills")
        self.assertEqual(result.count, 1)
        self.assertEqual(result.sections, ["Skills"])


if __name__ == "__main__":
    unittest.main()
