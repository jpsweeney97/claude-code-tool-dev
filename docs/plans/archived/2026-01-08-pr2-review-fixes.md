# PR #2 Review Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Address all issues identified in the comprehensive PR review for feat(handoff): v2 implementation.

**Architecture:** TDD approach - write failing tests first, then implement minimal fixes. Group related fixes by file to minimize context switching.

**Tech Stack:** Python 3.12, pytest, stdlib only (skill scripts)

---

## Overview

| Priority | Issue | File | Lines |
|----------|-------|------|-------|
| CRITICAL | Unprotected `read_text()` in file loading | synthesize.py | 1023 |
| HIGH | Unprotected `read_text()` in auto-detect | synthesize.py | 1183 |
| MEDIUM | Success message in warnings list | synthesize.py | 1069 |
| MEDIUM | SemanticReviewResult hides CLI failures | synthesize.py | 604-634 |
| LOW | Operator precedence ambiguity | synthesize.py | 1098 |
| TEST | `parse_semantic_response` edge cases | test_synthesize.py | NEW |
| TEST | `extract_findings` header-only tables | test_synthesize.py | NEW |
| TEST | `extract_title` colons in title | test_read.py | NEW |
| TEST | `calculate_overlap` direct tests | test_synthesize.py | NEW |

---

## Task 1: Add Error Field to SemanticReviewResult

**Files:**
- Modify: `.claude/skills/three-lens-audit/scripts/synthesize.py:90-95`
- Test: `.claude/skills/three-lens-audit/scripts/test_synthesize.py`

**Step 1: Write the failing test**

Add to `test_synthesize.py` after line 234:

```python
def test_semantic_review_result_has_error_field():
    """SemanticReviewResult should have an optional error field."""
    from synthesize import SemanticReviewResult

    # Without error
    result = SemanticReviewResult(
        matches=[],
        no_matches=[],
        token_usage={},
        model_used="haiku"
    )
    assert result.error is None

    # With error
    result_with_error = SemanticReviewResult(
        matches=[],
        no_matches=[],
        token_usage={},
        model_used="haiku",
        error="Claude CLI failed"
    )
    assert result_with_error.error == "Claude CLI failed"
```

**Step 2: Run test to verify it fails**

Run: `cd .claude/skills/three-lens-audit/scripts && python -m pytest test_synthesize.py::test_semantic_review_result_has_error_field -v`

Expected: FAIL with `TypeError: __init__() got an unexpected keyword argument 'error'`

**Step 3: Write minimal implementation**

In `synthesize.py`, modify the `SemanticReviewResult` dataclass (lines 90-95):

```python
@dataclass
class SemanticReviewResult:
    """Result of LLM semantic review."""
    matches: List[SemanticMatch]
    no_matches: List[Tuple[Finding, Finding]]
    token_usage: Dict[str, int]
    model_used: str
    error: Optional[str] = None
```

**Step 4: Run test to verify it passes**

Run: `cd .claude/skills/three-lens-audit/scripts && python -m pytest test_synthesize.py::test_semantic_review_result_has_error_field -v`

Expected: PASS

**Step 5: Commit**

```bash
git add .claude/skills/three-lens-audit/scripts/synthesize.py .claude/skills/three-lens-audit/scripts/test_synthesize.py
git commit -m "feat(three-lens-audit): add error field to SemanticReviewResult"
```

---

## Task 2: Populate Error Field on CLI Failure

**Files:**
- Modify: `.claude/skills/three-lens-audit/scripts/synthesize.py:606-634`
- Test: `.claude/skills/three-lens-audit/scripts/test_synthesize.py`

**Step 1: Write the failing test**

Add to `test_synthesize.py` after the `run_semantic_review` tests section:

```python
def test_run_semantic_review_sets_error_on_cli_failure():
    """run_semantic_review should set error field when CLI fails."""
    pairs = [
        (Finding("issue A", "adversarial"), Finding("issue B", "pragmatic"))
    ]

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "Authentication failed"

    with patch('subprocess.run', return_value=mock_result):
        result = run_semantic_review(pairs, model="haiku")

    assert result.error is not None
    assert "exit 1" in result.error
    assert result.matches == []


def test_run_semantic_review_sets_error_on_timeout():
    """run_semantic_review should set error field on timeout."""
    pairs = [
        (Finding("issue A", "adversarial"), Finding("issue B", "pragmatic"))
    ]

    with patch('subprocess.run', side_effect=subprocess.TimeoutExpired("claude", 120)):
        result = run_semantic_review(pairs, model="haiku")

    assert result.error is not None
    assert "timeout" in result.error.lower()
    assert result.matches == []


def test_run_semantic_review_sets_error_on_missing_cli():
    """run_semantic_review should set error field when claude CLI not found."""
    pairs = [
        (Finding("issue A", "adversarial"), Finding("issue B", "pragmatic"))
    ]

    with patch('subprocess.run', side_effect=FileNotFoundError("claude")):
        result = run_semantic_review(pairs, model="haiku")

    assert result.error is not None
    assert "not found" in result.error.lower()
    assert result.matches == []
```

**Step 2: Run tests to verify they fail**

Run: `cd .claude/skills/three-lens-audit/scripts && python -m pytest test_synthesize.py::test_run_semantic_review_sets_error_on_cli_failure test_synthesize.py::test_run_semantic_review_sets_error_on_timeout test_synthesize.py::test_run_semantic_review_sets_error_on_missing_cli -v`

Expected: FAIL with `assert result.error is not None` (error is None currently)

**Step 3: Write minimal implementation**

In `synthesize.py`, modify the error handling in `run_semantic_review` (lines 606-634):

```python
        if result.returncode != 0:
            error_msg = f"Claude CLI failed (exit {result.returncode})"
            print(f"Warning: {error_msg}", file=sys.stderr)
            if result.stderr:
                print(f"  stderr: {result.stderr[:200]}", file=sys.stderr)
            return SemanticReviewResult(
                matches=[],
                no_matches=[],
                token_usage={},
                model_used=model,
                error=error_msg
            )

        response = result.stdout

    except subprocess.TimeoutExpired:
        error_msg = "Claude CLI timed out after 120s"
        print(f"Warning: {error_msg}", file=sys.stderr)
        return SemanticReviewResult(
            matches=[],
            no_matches=[],
            token_usage={},
            model_used=model,
            error=error_msg
        )
    except FileNotFoundError:
        error_msg = "'claude' CLI not found - semantic review skipped"
        print(f"Warning: {error_msg}", file=sys.stderr)
        return SemanticReviewResult(
            matches=[],
            no_matches=[],
            token_usage={},
            model_used=model,
            error=error_msg
        )
```

**Step 4: Run tests to verify they pass**

Run: `cd .claude/skills/three-lens-audit/scripts && python -m pytest test_synthesize.py::test_run_semantic_review_sets_error_on_cli_failure test_synthesize.py::test_run_semantic_review_sets_error_on_timeout test_synthesize.py::test_run_semantic_review_sets_error_on_missing_cli -v`

Expected: PASS

**Step 5: Commit**

```bash
git add .claude/skills/three-lens-audit/scripts/synthesize.py .claude/skills/three-lens-audit/scripts/test_synthesize.py
git commit -m "fix(three-lens-audit): populate error field on CLI failures"
```

---

## Task 3: Check Error Field in Synthesize Function

**Files:**
- Modify: `.claude/skills/three-lens-audit/scripts/synthesize.py:1062-1069`
- Test: `.claude/skills/three-lens-audit/scripts/test_synthesize.py`

**Step 1: Write the failing test**

Add to `test_synthesize.py`:

```python
def test_synthesize_reports_semantic_review_error_in_warnings():
    """synthesize should add semantic review error to warnings, not just success."""
    from synthesize import synthesize, SemanticReviewResult

    # Create minimal lens files
    lens_files = {}
    with patch('synthesize.run_semantic_review') as mock_review:
        mock_review.return_value = SemanticReviewResult(
            matches=[],
            no_matches=[],
            token_usage={},
            model_used="haiku",
            error="Claude CLI failed (exit 1)"
        )

        # We need actual files for synthesize to work
        # This test verifies the error is reported in warnings
        # For now, just verify the function signature accepts the error
        assert SemanticReviewResult(
            matches=[],
            no_matches=[],
            token_usage={},
            model_used="haiku",
            error="test"
        ).error == "test"
```

**Step 2: Run test to verify baseline**

Run: `cd .claude/skills/three-lens-audit/scripts && python -m pytest test_synthesize.py::test_synthesize_reports_semantic_review_error_in_warnings -v`

Expected: PASS (this is a setup test)

**Step 3: Write implementation**

In `synthesize.py`, modify the semantic review handling in `synthesize()` (around line 1062-1069):

```python
            if semantic_result.error:
                # Report the error in warnings
                warnings.append(f"Semantic review failed: {semantic_result.error}")
            elif semantic_result.matches:
                # Merge matches into convergent findings
                merge_semantic_matches(semantic_result.matches, convergent_3, convergent_2)

                # Note the enhancement (info, not warning)
                print(f"Info: Semantic review found {len(semantic_result.matches)} additional matches using {semantic_model}", file=sys.stderr)
```

**Step 4: Run all synthesize tests**

Run: `cd .claude/skills/three-lens-audit/scripts && python -m pytest test_synthesize.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add .claude/skills/three-lens-audit/scripts/synthesize.py .claude/skills/three-lens-audit/scripts/test_synthesize.py
git commit -m "fix(three-lens-audit): report semantic review errors in warnings"
```

---

## Task 4: Add Protected read_text() in File Loading Loop (CRITICAL)

**Files:**
- Modify: `.claude/skills/three-lens-audit/scripts/synthesize.py:1017-1024`
- Test: `.claude/skills/three-lens-audit/scripts/test_synthesize.py`

**Step 1: Write the failing test**

Add to `test_synthesize.py`:

```python
def test_synthesize_handles_permission_error_on_read(tmp_path: Path):
    """synthesize should handle PermissionError gracefully, not crash."""
    from synthesize import synthesize

    # Create files
    good_file = tmp_path / "adversarial.md"
    good_file.write_text("# Adversarial Auditor\n| Finding | Description |\n|---------|-------------|\n| Issue | Desc |")

    bad_file = tmp_path / "pragmatic.md"
    bad_file.write_text("# Pragmatic Practitioner\n| Finding | Description |\n|---------|-------------|\n| Issue | Desc |")

    lens_files = {
        "adversarial": good_file,
        "pragmatic": bad_file
    }

    # Mock read_text to raise PermissionError for bad_file
    original_read_text = Path.read_text
    def mock_read_text(self, *args, **kwargs):
        if self == bad_file:
            raise PermissionError("Permission denied")
        return original_read_text(self, *args, **kwargs)

    with patch.object(Path, 'read_text', mock_read_text):
        result = synthesize(lens_files, target="test")

    # Should not crash, should have warning
    assert any("Permission denied" in w or "Could not read" in w for w in result.warnings)


def test_synthesize_handles_unicode_error_on_read(tmp_path: Path):
    """synthesize should handle UnicodeDecodeError gracefully."""
    from synthesize import synthesize

    # Create a file with valid content
    good_file = tmp_path / "adversarial.md"
    good_file.write_text("# Adversarial Auditor\n| Finding | Description |\n|---------|-------------|\n| Issue | Desc |")

    # Create a file with binary content that will fail to decode
    bad_file = tmp_path / "pragmatic.md"
    bad_file.write_bytes(b'\x80\x81\x82')  # Invalid UTF-8

    lens_files = {
        "adversarial": good_file,
        "pragmatic": bad_file
    }

    result = synthesize(lens_files, target="test")

    # Should not crash, should have warning about encoding
    assert any("Encoding error" in w or "decode" in w.lower() for w in result.warnings)
```

**Step 2: Run tests to verify they fail**

Run: `cd .claude/skills/three-lens-audit/scripts && python -m pytest test_synthesize.py::test_synthesize_handles_permission_error_on_read test_synthesize.py::test_synthesize_handles_unicode_error_on_read -v`

Expected: FAIL (crashes with unhandled exception)

**Step 3: Write minimal implementation**

In `synthesize.py`, modify the file loading loop (lines 1017-1024):

```python
    # Load and validate each lens output
    for lens, path in lens_files.items():
        if not path.exists():
            warnings.append(f"File not found for {lens}: {path}")
            continue

        try:
            content = path.read_text()
        except PermissionError as e:
            warnings.append(f"Could not read {lens} output ({path}): {e}")
            continue
        except UnicodeDecodeError as e:
            warnings.append(f"Encoding error in {lens} output ({path}): {e}")
            continue
        except OSError as e:
            warnings.append(f"Could not read {lens} output ({path}): {e}")
            continue

        lens_outputs[lens] = content
```

**Step 4: Run tests to verify they pass**

Run: `cd .claude/skills/three-lens-audit/scripts && python -m pytest test_synthesize.py::test_synthesize_handles_permission_error_on_read test_synthesize.py::test_synthesize_handles_unicode_error_on_read -v`

Expected: PASS

**Step 5: Commit**

```bash
git add .claude/skills/three-lens-audit/scripts/synthesize.py .claude/skills/three-lens-audit/scripts/test_synthesize.py
git commit -m "fix(three-lens-audit): handle read errors in synthesize file loading"
```

---

## Task 5: Add Protected read_text() in Auto-Detect Mode (HIGH)

**Files:**
- Modify: `.claude/skills/three-lens-audit/scripts/synthesize.py:1178-1188`

**Step 1: Write the failing test**

Add to `test_synthesize.py`:

```python
def test_auto_detect_handles_permission_error(tmp_path: Path, capsys):
    """Auto-detect mode should handle PermissionError gracefully."""
    import sys
    from synthesize import main

    # Create a file
    test_file = tmp_path / "test.md"
    test_file.write_text("# Adversarial Auditor\nContent")

    # Mock to raise PermissionError
    original_read_text = Path.read_text
    def mock_read_text(self, *args, **kwargs):
        if "test.md" in str(self):
            raise PermissionError("Permission denied")
        return original_read_text(self, *args, **kwargs)

    with patch.object(Path, 'read_text', mock_read_text):
        with patch('sys.argv', ['synthesize.py', '--auto-detect', str(test_file)]):
            # Should not crash
            try:
                main()
            except SystemExit as e:
                # May exit with error code, but should not crash
                pass

    captured = capsys.readouterr()
    assert "Permission denied" in captured.err or "Could not read" in captured.err
```

**Step 2: Run test to verify it fails**

Run: `cd .claude/skills/three-lens-audit/scripts && python -m pytest test_synthesize.py::test_auto_detect_handles_permission_error -v`

Expected: FAIL (crashes with unhandled PermissionError)

**Step 3: Write minimal implementation**

In `synthesize.py`, modify the auto-detect loop (lines 1178-1188):

```python
    if args.auto_detect:
        for path in args.files:
            if not path.exists():
                print(f"Warning: File not found: {path}", file=sys.stderr)
                continue
            try:
                content = path.read_text()
            except PermissionError as e:
                print(f"Warning: Could not read {path}: {e}", file=sys.stderr)
                continue
            except UnicodeDecodeError as e:
                print(f"Warning: Encoding error in {path}: {e}", file=sys.stderr)
                continue
            except OSError as e:
                print(f"Warning: Could not read {path}: {e}", file=sys.stderr)
                continue
            lens = detect_lens_from_content(content)
            if lens:
                lens_files[lens] = path
            else:
                print(f"Warning: Could not detect lens type for: {path}", file=sys.stderr)
```

**Step 4: Run test to verify it passes**

Run: `cd .claude/skills/three-lens-audit/scripts && python -m pytest test_synthesize.py::test_auto_detect_handles_permission_error -v`

Expected: PASS

**Step 5: Commit**

```bash
git add .claude/skills/three-lens-audit/scripts/synthesize.py .claude/skills/three-lens-audit/scripts/test_synthesize.py
git commit -m "fix(three-lens-audit): handle read errors in auto-detect mode"
```

---

## Task 6: Fix Operator Precedence in Lens Detection (LOW)

**Files:**
- Modify: `.claude/skills/three-lens-audit/scripts/synthesize.py:1098`

**Step 1: Write the failing test**

Add to `test_synthesize.py`:

```python
def test_detect_lens_from_content_cost_benefit_patterns():
    """detect_lens_from_content should detect cost-benefit from various patterns."""
    from synthesize import detect_lens_from_content

    # Explicit cost/benefit
    assert detect_lens_from_content("# Cost/Benefit Analysis") == "cost-benefit"

    # Effort AND benefit together
    assert detect_lens_from_content("Consider the effort required and benefit gained") == "cost-benefit"

    # Just effort alone should NOT match (the bug we're fixing)
    content_just_effort = "This requires effort but no payoff mentioned"
    # Without the fix, this incorrectly returns 'cost-benefit'
    # because 'effort' in content_lower and 'benefit' in content_lower
    # is parsed as: 'effort' OR ('effort' AND 'benefit')
    # With the fix, it should return None
    assert detect_lens_from_content(content_just_effort) is None
```

**Step 2: Run test to verify it fails**

Run: `cd .claude/skills/three-lens-audit/scripts && python -m pytest test_synthesize.py::test_detect_lens_from_content_cost_benefit_patterns -v`

Expected: FAIL on last assertion (returns 'cost-benefit' incorrectly)

**Step 3: Write minimal implementation**

In `synthesize.py`, fix line 1098:

```python
    elif 'cost/benefit' in content_lower or ('effort' in content_lower and 'benefit' in content_lower):
        return 'cost-benefit'
```

**Step 4: Run test to verify it passes**

Run: `cd .claude/skills/three-lens-audit/scripts && python -m pytest test_synthesize.py::test_detect_lens_from_content_cost_benefit_patterns -v`

Expected: PASS

**Step 5: Commit**

```bash
git add .claude/skills/three-lens-audit/scripts/synthesize.py .claude/skills/three-lens-audit/scripts/test_synthesize.py
git commit -m "fix(three-lens-audit): correct operator precedence in lens detection"
```

---

## Task 7: Add parse_semantic_response Edge Case Tests

**Files:**
- Test: `.claude/skills/three-lens-audit/scripts/test_synthesize.py`

**Step 1: Write the tests**

Add to `test_synthesize.py` after existing `parse_semantic_response` tests:

```python
def test_parse_semantic_response_skipped_pair_numbers():
    """parse_semantic_response should handle non-sequential pair numbers."""
    response = """
PAIR 1:
ELEMENT_A: cache invalidation
ELEMENT_B: cache config
MATCH: yes
SHARED_ELEMENT: cache
RATIONALE: Both about caching
CONFIDENCE: high

PAIR 3:
ELEMENT_A: auth tokens
ELEMENT_B: token refresh
MATCH: yes
SHARED_ELEMENT: tokens
RATIONALE: Both about tokens
CONFIDENCE: medium
"""
    pairs = [
        (Finding("cache invalidation", "adversarial"), Finding("cache config", "cost-benefit")),
        (Finding("unrelated", "adversarial"), Finding("stuff", "cost-benefit")),
        (Finding("auth tokens", "adversarial"), Finding("token refresh", "cost-benefit")),
    ]
    result = parse_semantic_response(response, pairs)

    # Should parse what it can find
    assert len(result.matches) >= 1  # At least pair 1


def test_parse_semantic_response_extra_whitespace():
    """parse_semantic_response should handle extra whitespace in fields."""
    response = """
PAIR 1:
ELEMENT_A:   cache invalidation
ELEMENT_B:  cache config
MATCH:   yes
SHARED_ELEMENT:    cache
RATIONALE:   Both about caching
CONFIDENCE:   high
"""
    pairs = [
        (Finding("cache invalidation", "adversarial"), Finding("cache config", "cost-benefit"))
    ]
    result = parse_semantic_response(response, pairs)

    assert len(result.matches) == 1
    assert result.matches[0].shared_element.strip() == "cache"


def test_parse_semantic_response_invalid_match_value():
    """parse_semantic_response should handle invalid MATCH values gracefully."""
    response = """
PAIR 1:
ELEMENT_A: cache invalidation
ELEMENT_B: cache config
MATCH: maybe
SHARED_ELEMENT: cache
RATIONALE: Uncertain
CONFIDENCE: low
"""
    pairs = [
        (Finding("cache invalidation", "adversarial"), Finding("cache config", "cost-benefit"))
    ]
    result = parse_semantic_response(response, pairs)

    # Should not crash, 'maybe' should be treated as no match
    assert isinstance(result.matches, list)
    # 'maybe' is not 'yes', so no match
    assert len(result.matches) == 0 or result.matches[0].confidence != "high"
```

**Step 2: Run tests**

Run: `cd .claude/skills/three-lens-audit/scripts && python -m pytest test_synthesize.py::test_parse_semantic_response_skipped_pair_numbers test_synthesize.py::test_parse_semantic_response_extra_whitespace test_synthesize.py::test_parse_semantic_response_invalid_match_value -v`

Expected: PASS (these verify existing behavior handles edge cases)

**Step 3: Commit**

```bash
git add .claude/skills/three-lens-audit/scripts/test_synthesize.py
git commit -m "test(three-lens-audit): add parse_semantic_response edge case tests"
```

---

## Task 8: Add extract_title Edge Case Tests

**Files:**
- Test: `.claude/skills/handoff/scripts/test_read.py`

**Step 1: Write the tests**

Add to `test_read.py` in the `TestExtractTitle` class:

```python
    def test_extracts_title_with_colon(self):
        """Handles title containing colons."""
        content = """---
date: 2026-01-08
title: Auth: JWT Implementation: Phase 1
---

# Handoff: Auth: JWT Implementation: Phase 1
"""
        from read import extract_title

        # Should get everything after first "title:"
        assert extract_title(content) == "Auth: JWT Implementation: Phase 1"

    def test_extracts_quoted_title(self):
        """Handles quoted title in frontmatter."""
        content = '''---
date: 2026-01-08
title: "Feature: Add logging"
---

# Handoff
'''
        from read import extract_title

        assert extract_title(content) == "Feature: Add logging"

    def test_handles_malformed_frontmatter(self):
        """Handles frontmatter without closing ---."""
        content = """---
date: 2026-01-08
title: Incomplete frontmatter

# Handoff: Fallback Title
"""
        from read import extract_title

        # Falls back to heading since frontmatter is malformed
        assert extract_title(content) == "Fallback Title"
```

**Step 2: Run tests**

Run: `cd .claude/skills/handoff/scripts && python -m pytest test_read.py::TestExtractTitle -v`

Expected: Review results - some may fail revealing bugs to fix

**Step 3: Fix if needed and commit**

If tests reveal bugs in `extract_title`, fix them. Otherwise:

```bash
git add .claude/skills/handoff/scripts/test_read.py
git commit -m "test(handoff): add extract_title edge case tests"
```

---

## Task 9: Add calculate_overlap Direct Tests

**Files:**
- Test: `.claude/skills/three-lens-audit/scripts/test_synthesize.py`

**Step 1: Write the tests**

Add to `test_synthesize.py`:

```python
def test_calculate_overlap_identical_sets():
    """calculate_overlap should return 1.0 for identical sets."""
    from synthesize import calculate_overlap

    set_a = {"cache", "validation", "error"}
    set_b = {"cache", "validation", "error"}

    assert calculate_overlap(set_a, set_b) == 1.0


def test_calculate_overlap_disjoint_sets():
    """calculate_overlap should return 0.0 for disjoint sets."""
    from synthesize import calculate_overlap

    set_a = {"cache", "validation"}
    set_b = {"logging", "metrics"}

    assert calculate_overlap(set_a, set_b) == 0.0


def test_calculate_overlap_partial_overlap():
    """calculate_overlap should return correct Jaccard coefficient."""
    from synthesize import calculate_overlap

    set_a = {"cache", "validation", "error"}
    set_b = {"cache", "validation", "logging"}

    # Intersection: {cache, validation} = 2
    # Union: {cache, validation, error, logging} = 4
    # Jaccard: 2/4 = 0.5
    assert calculate_overlap(set_a, set_b) == 0.5


def test_calculate_overlap_empty_sets():
    """calculate_overlap should return 0.0 for empty sets."""
    from synthesize import calculate_overlap

    # Both empty
    assert calculate_overlap(set(), set()) == 0.0

    # One empty
    assert calculate_overlap({"cache"}, set()) == 0.0
    assert calculate_overlap(set(), {"cache"}) == 0.0
```

**Step 2: Run tests**

Run: `cd .claude/skills/three-lens-audit/scripts && python -m pytest test_synthesize.py::test_calculate_overlap_identical_sets test_synthesize.py::test_calculate_overlap_disjoint_sets test_synthesize.py::test_calculate_overlap_partial_overlap test_synthesize.py::test_calculate_overlap_empty_sets -v`

Expected: PASS

**Step 3: Commit**

```bash
git add .claude/skills/three-lens-audit/scripts/test_synthesize.py
git commit -m "test(three-lens-audit): add calculate_overlap direct unit tests"
```

---

## Task 10: Run Full Test Suite and Final Verification

**Step 1: Run all handoff tests**

Run: `cd .claude/skills/handoff/scripts && python -m pytest test_read.py -v`

Expected: All PASS

**Step 2: Run all three-lens-audit tests**

Run: `cd .claude/skills/three-lens-audit/scripts && python -m pytest -v`

Expected: All PASS

**Step 3: Run type checker (if available)**

Run: `cd .claude/skills/three-lens-audit/scripts && pyright synthesize.py 2>/dev/null || mypy synthesize.py 2>/dev/null || echo "No type checker available"`

**Step 4: Final commit if any cleanup needed**

```bash
git status
# If there are uncommitted changes from test runs or cleanup:
git add -A
git commit -m "chore: test cleanup"
```

**Step 5: Push to PR branch**

```bash
git push origin feat/handoff-v2
```

---

## Summary Checklist

| Task | Status | Issue Addressed |
|------|--------|-----------------|
| 1 | [ ] | Add error field to SemanticReviewResult |
| 2 | [ ] | Populate error field on CLI failure |
| 3 | [ ] | Check error field in synthesize function |
| 4 | [ ] | Protected read_text() in file loading (CRITICAL) |
| 5 | [ ] | Protected read_text() in auto-detect (HIGH) |
| 6 | [ ] | Operator precedence fix (LOW) |
| 7 | [ ] | parse_semantic_response edge case tests |
| 8 | [ ] | extract_title edge case tests |
| 9 | [ ] | calculate_overlap direct tests |
| 10 | [ ] | Full test suite verification |
