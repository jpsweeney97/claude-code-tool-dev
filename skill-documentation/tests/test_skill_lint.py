#!/usr/bin/env python3
"""Tests for skill_lint.py"""

from pathlib import Path
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from skill_lint import (
    CONTENT_AREAS,
    _count_decision_points,
    _find_section_chunk,
    _has_quick_check_with_expected,
    _has_stop,
    _heading_spans,
    _looks_like_dangerous_command,
    _parse_headings,
    lint_text,
)


class TestDecisionPointDetection:
    """Test decision point counting with various formats."""

    def test_if_then_otherwise_detected(self):
        """Standard if/then/otherwise pattern should be detected."""
        body = "If the file exists, then read it, otherwise create it."
        assert _count_decision_points(body) >= 1

    def test_else_detected(self):
        """'else' should be recognized as a decision point branch."""
        body = "If the file exists, then read it, else create it."
        assert _count_decision_points(body) >= 1

    def test_multiple_decision_points(self):
        """Multiple decision points should all be counted."""
        body = """
        If A, then B, otherwise C.
        If X, then Y, otherwise Z.
        """
        assert _count_decision_points(body) >= 2


class TestQuickCheckDetection:
    """Test quick check with expected detection."""

    def test_quick_check_with_expected_detected(self):
        """Standard 'Quick check' + 'Expected' should pass."""
        chunk = """
        ## Quick check
        Run: `pytest`
        Expected: All tests pass
        """
        assert _has_quick_check_with_expected(chunk) is True

    def test_verification_checkbox_detected(self):
        """Verification with checkboxes should now pass."""
        chunk = """
        ## Verification
        - [ ] Tests pass
        - [ ] Build succeeds
        """
        assert _has_quick_check_with_expected(chunk) is True


class TestStopDetection:
    """Test STOP pattern detection."""

    def test_stop_detected(self):
        """Explicit STOP should be detected."""
        assert _has_stop("STOP and ask the user") is True

    def test_stop_in_sentence(self):
        """STOP in a sentence should be detected."""
        assert _has_stop("If missing, stop.") is True


class TestDangerousCommandDetection:
    """Test dangerous command detection."""

    def test_deploy_in_command_detected(self):
        """'deploy' in a command should be flagged."""
        assert _looks_like_dangerous_command("kubectl deploy") is True

    def test_deploy_in_prose_still_detected(self):
        """'deploy' anywhere triggers - documents current false positive behavior."""
        # This is a false positive we want to fix
        assert _looks_like_dangerous_command("deploy to production") is True


class TestContentAreaDetection:
    """Test section/content area detection."""

    def test_triggers_section_detected_as_when_to_use(self):
        """'Triggers' section should be recognized as when_to_use."""
        lines = ["# Triggers", "Use when you need to audit"]
        headings = _parse_headings(lines)
        spans = _heading_spans(lines, headings)
        chunk = _find_section_chunk(lines, headings, spans, CONTENT_AREAS["when_to_use"])
        # "Triggers" is now in synonyms
        assert chunk is not None


class TestDecisionPointSynonyms:
    """Test expanded decision point detection."""

    def test_else_detected_as_otherwise(self):
        """'else' should be recognized like 'otherwise'."""
        body = "If the file exists, then read it, else create it."
        assert _count_decision_points(body) >= 1

    def test_if_not_detected(self):
        """'if not' patterns should count as decision points."""
        body = "If not found, then search deeper, otherwise report missing."
        assert _count_decision_points(body) >= 1


class TestVerificationFormats:
    """Test various verification format acceptance."""

    def test_checkbox_verification_accepted(self):
        """Verification with checkboxes should pass."""
        chunk = """
        ## Verification

        Audit is complete when:
        - [ ] All agents returned findings
        - [ ] Convergent findings identified
        - [ ] Recommendations prioritized
        """
        assert _has_quick_check_with_expected(chunk) is True

    def test_verification_heading_with_criteria(self):
        """'Verification' heading with any criteria should pass."""
        chunk = """
        ## Verification

        - Tests pass
        - Build succeeds
        """
        assert _has_quick_check_with_expected(chunk) is True


class TestDangerousCommandContext:
    """Test context-aware dangerous command detection."""

    def test_deploy_in_fenced_code_not_flagged(self):
        """Commands in fenced code blocks are examples, not instructions."""
        body = """
        ## Example

        ```bash
        kubectl deploy my-app
        ```

        This shows how deployment works.
        """
        fail_codes, details = lint_text(body)
        # Should NOT trigger unsafe-default for example code
        assert "FAIL.unsafe-default" not in fail_codes

    def test_deploy_in_inline_code_flagged(self):
        """Inline backtick commands ARE instructions."""
        body = """
        Run `kubectl deploy my-app` to deploy.
        """
        fail_codes, details = lint_text(body)
        # Should trigger - inline code is actionable
        assert "FAIL.unsafe-default" in fail_codes

    def test_deploy_in_prose_not_flagged(self):
        """'deploy' in prose text shouldn't trigger."""
        body = """
        This skill helps you deploy applications safely.
        We deploy to staging first.
        """
        fail_codes, details = lint_text(body)
        # Should NOT trigger for prose
        assert "FAIL.unsafe-default" not in fail_codes


class TestContentAreaSynonyms:
    """Test expanded synonym detection."""

    def test_triggers_detected_as_when_to_use(self):
        """'Triggers' should be recognized as when_to_use."""
        md = """# My Skill

## Triggers
- `/command arg` — Do something
"""
        fail_codes, details = lint_text(md)
        # Should NOT have when_to_use in missing areas
        missing_areas_detail = next((d for d in details if "Missing content areas:" in d), "")
        assert "when_to_use" not in missing_areas_detail, f"'Triggers' should map to when_to_use but got: {missing_areas_detail}"

    def test_anti_patterns_detected_as_when_not_to_use(self):
        """'Anti-Patterns' should be recognized as when_not_to_use."""
        md = """# My Skill

## Anti-Patterns
| Avoid | Why |
|-------|-----|
| Bad thing | Reason |
"""
        fail_codes, details = lint_text(md)
        # Should NOT have when_not_to_use in missing areas
        missing_areas_detail = next((d for d in details if "Missing content areas:" in d), "")
        assert "when_not_to_use" not in missing_areas_detail, f"'Anti-Patterns' should map to when_not_to_use but got: {missing_areas_detail}"
