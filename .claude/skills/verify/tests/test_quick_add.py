#!/usr/bin/env python3
"""Tests for simplified quick-add functionality."""

import sys
import unittest
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


class TestSimplifiedQuickAdd(unittest.TestCase):
    """Tests for streamlined quick-add CLI."""

    def test_quick_add_standalone_infers_section(self):
        """--quick-add alone should work without --add when input has claim."""
        from verify import infer_section
        # Test that inference works
        section = infer_section("hooks use exit code 2 to block")
        self.assertEqual(section, "Hooks")

    def test_quick_add_standalone_infers_severity(self):
        """--quick-add should infer severity from claim text."""
        from verify import infer_severity
        severity = infer_severity("exit code 2 blocks execution")
        self.assertEqual(severity, "CRITICAL")

    def test_quick_add_parses_inline_claim(self):
        """--quick-add 'claim text' should extract claim from positional arg."""
        from verify import parse_quick_add_input
        claim, verdict, evidence = parse_quick_add_input(
            "hooks timeout defaults to 60 seconds"
        )
        self.assertEqual(claim, "hooks timeout defaults to 60 seconds")
        self.assertIsNone(verdict)  # Not provided inline
        self.assertIsNone(evidence)

    def test_quick_add_parses_verdict_evidence(self):
        """--quick-add with verdict:evidence syntax."""
        from verify import parse_quick_add_input
        claim, verdict, evidence = parse_quick_add_input(
            "exit code 0 means success | verified | docs confirm"
        )
        self.assertEqual(claim, "exit code 0 means success")
        self.assertEqual(verdict, "verified")
        self.assertEqual(evidence, "docs confirm")


if __name__ == "__main__":
    unittest.main()
