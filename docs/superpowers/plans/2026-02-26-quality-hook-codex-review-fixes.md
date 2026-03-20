# Quality Hook Codex Review Fixes — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Apply 3 blocking fixes and 7 should-fix items from the second Codex review to the quality hook implementation plan at `docs/plans/2026-02-26-handoff-quality-hook.md`.

**Architecture:** All changes are edits to the existing plan file. No code runs — this plan modifies the plan document's inline Python code and test code to fix bugs and add missing coverage before execution. The plan is a single markdown file with embedded Python code blocks.

**Tech Stack:** Markdown editing only. The embedded code is Python 3.11+ with pytest.

**Target file:** `docs/plans/2026-02-26-handoff-quality-hook.md`

---

## Fix Index

| ID | Severity | Issue | Location (plan line) |
|----|----------|-------|---------------------|
| B1 | Blocking | Hollow-handoff guardrail double-fires when content-required sections are absent | 947-958 |
| B2 | Blocking | Unused imports `count_body_lines` and `VALID_TYPES` will fail ruff F401 | 246-265 |
| B3 | Blocking | Stale "44 tests PASS" and "73 tests" counts | 1130, 1135 |
| S1 | P2 | `parse_frontmatter` sequential `.strip` corrupts mismatched quotes | 839 |
| S2 | P2 | `count_body_lines` uses `split("\n")` not `splitlines()` — trailing newline off-by-one | 966 |
| S3 | P2 | Missing `TestCountBodyLines` class (4 tests) | (new, after line 612) |
| S4 | P2 | Missing hollow double-fire regression test | (new, after line 568) |
| S5 | P3 | `test_invalid_type_errors` should assert early return (no section/line-count errors) | 648-656 |
| S6 | P3 | `main` tests don't assert `hookEventName` in output contract | 771-780 |
| S7 | P3 | Design table says "22-55" but code constants are 20-80 | 1489 |

---

## Task 1: Fix Implementation Code (B1, S1, S2)

**Files:**
- Modify: `docs/plans/2026-02-26-handoff-quality-hook.md` — inline code blocks for `validate_sections`, `parse_frontmatter`, `count_body_lines`

**Step 1: Fix B1 — Gate hollow-handoff guardrail on section presence**

In the `validate_sections` implementation (plan lines 945-958), change the guardrail to only fire when all 3 content-required sections exist but are all empty. Currently it fires even when the sections are entirely absent (producing a duplicate error alongside the missing-sections error).

Find this code inside the `validate_sections` code block:
```python
    # Hollow-handoff guardrail: at least 1 of {Decisions, Changes, Learnings}
    # must have non-empty content (handoffs only)
    if doc_type == "handoff":
        content_sections = [
            s for s in sections
            if s["heading"] in CONTENT_REQUIRED_SECTIONS
            and s["content"].strip()
        ]
        if not content_sections:
            issues.append(Issue(
                "error",
                "Hollow handoff: at least 1 of {Decisions, Changes, Learnings} "
                "must have substantive content.",
            ))
```

Replace with:
```python
    # Hollow-handoff guardrail: at least 1 of {Decisions, Changes, Learnings}
    # must have non-empty content (handoffs only).
    # Only fires when all 3 sections are present but empty — missing sections
    # are already caught by the missing-sections check above.
    if doc_type == "handoff":
        present_content_sections = [
            s for s in sections
            if s["heading"] in CONTENT_REQUIRED_SECTIONS
        ]
        if len(present_content_sections) == len(CONTENT_REQUIRED_SECTIONS):
            has_substance = any(
                s["content"].strip() for s in present_content_sections
            )
            if not has_substance:
                issues.append(Issue(
                    "error",
                    "Hollow handoff: at least 1 of {Decisions, Changes, Learnings} "
                    "must have substantive content.",
                ))
```

**Step 2: Fix S1 — Use paired-quote check in `parse_frontmatter`**

In the `parse_frontmatter` implementation (plan line 839), change sequential `.strip('"').strip("'")` to a paired-quote check matching `search.py:63-66`.

Find this line inside the `parse_frontmatter` code block:
```python
            frontmatter[key.strip()] = value.strip().strip('"').strip("'")
```

Replace with:
```python
            value = value.strip()
            if (value.startswith('"') and value.endswith('"')) or (
                value.startswith("'") and value.endswith("'")
            ):
                value = value[1:-1]
            frontmatter[key.strip()] = value
```

**Step 3: Fix S2 — Use `splitlines()` in `count_body_lines`**

In the `count_body_lines` implementation (plan line 966), change `split("\n")` to `splitlines()` to avoid the trailing-newline off-by-one.

Find this code inside the `count_body_lines` code block:
```python
def count_body_lines(content: str) -> int:
    lines = content.split("\n")
    if not lines or lines[0].strip() != "---":
        return len(lines)  # No frontmatter — all lines are body
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return len(lines) - (i + 1)
    return len(lines)  # No closing --- — all lines are body
```

Replace with:
```python
def count_body_lines(content: str) -> int:
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return len(lines)  # No frontmatter — all lines are body
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return len(lines) - (i + 1)
    return len(lines)  # No closing --- — all lines are body
```

**Step 4: Commit**

```bash
git add docs/plans/2026-02-26-handoff-quality-hook.md
git commit -m "fix(plan): B1 hollow-handoff guardrail, S1 quote stripping, S2 splitlines

B1: Gate guardrail on all 3 content-required sections being present —
    prevents double-fire when sections are absent.
S1: Paired-quote check matching search.py pattern — prevents
    corruption on mismatched quotes.
S2: splitlines() instead of split('\\n') — prevents trailing-newline
    off-by-one that could flip checkpoint boundaries."
```

---

## Task 2: Fix Test Code (B2, S3, S4, S5, S6)

**Files:**
- Modify: `docs/plans/2026-02-26-handoff-quality-hook.md` — inline test code blocks

**Step 1: Fix B2 — Add `TestCountBodyLines` class that uses the `count_body_lines` import**

This fixes the unused-import F401 for `count_body_lines`. Add this new test class inside the test file code block, after the `TestValidateLineCount` class (after plan line ~612) and before the `TestValidate` class (before plan line ~615):

```python

# --- Body line counting ---


class TestCountBodyLines:
    """Tests for count_body_lines — frontmatter-aware line counting."""

    def test_with_frontmatter(self) -> None:
        content = "---\ntype: handoff\ndate: 2026-01-01\n---\nLine 1\nLine 2\nLine 3"
        assert count_body_lines(content) == 3

    def test_without_frontmatter(self) -> None:
        content = "Line 1\nLine 2\nLine 3"
        assert count_body_lines(content) == 3

    def test_trailing_newline(self) -> None:
        """Trailing newline should not inflate the count."""
        with_newline = "---\ntype: handoff\n---\nLine 1\nLine 2\n"
        without_newline = "---\ntype: handoff\n---\nLine 1\nLine 2"
        assert count_body_lines(with_newline) == count_body_lines(without_newline)

    def test_unclosed_frontmatter(self) -> None:
        """Unclosed frontmatter means all lines are body."""
        content = "---\ntype: handoff\nLine 1\nLine 2"
        assert count_body_lines(content) == 4
```

Also fix B2 for `VALID_TYPES` — it is used by `test_invalid_type_errors` (S5 below) after the fix. But to be safe, also add a direct assertion. In the `test_invalid_type_errors` method (S5 fix below), we reference `VALID_TYPES` directly. This resolves the F401.

**Step 2: Fix S4 — Add hollow double-fire regression test**

Add this test to the `TestValidateSections` class, after `test_hollow_handoff_passes_with_one_content_section` (after plan line ~568):

```python

    def test_hollow_guardrail_skipped_when_sections_absent(self) -> None:
        """When content-required sections are entirely absent, only missing-sections fires."""
        sections = [
            {"heading": s, "content": "text"}
            for s in REQUIRED_HANDOFF_SECTIONS
            if s not in CONTENT_REQUIRED_SECTIONS
        ]
        issues = validate_sections(sections, "handoff")
        # Missing-sections error should fire
        assert any("Missing required sections" in i.message for i in issues)
        # Hollow-handoff guardrail should NOT fire (sections absent, not empty)
        assert not any("Hollow handoff" in i.message for i in issues)
```

**Step 3: Fix S5 — Strengthen `test_invalid_type_errors` to assert early return**

In the `TestValidate` class, find this test (plan lines 648-656):

```python
    def test_invalid_type_errors(self) -> None:
        """type: foo should produce an error, not silently validate."""
        content = _make_content(
            frontmatter=_make_frontmatter(overrides={"type": "foo"}),
        )
        issues = validate(content)
        assert any(
            i.severity == "error" and "foo" in i.message for i in issues
        )
```

Replace with:
```python
    def test_invalid_type_errors(self) -> None:
        """type: foo should produce an error and stop — no section/line-count errors."""
        content = _make_content(
            frontmatter=_make_frontmatter(overrides={"type": "foo"}),
        )
        issues = validate(content)
        assert len(issues) == 1, f"Expected exactly 1 issue (type error), got {len(issues)}: {issues}"
        assert issues[0].severity == "error"
        assert "foo" in issues[0].message
        assert all(t in issues[0].message for t in sorted(VALID_TYPES))
```

**Step 4: Fix S6 — Assert `hookEventName` in output contract**

In the `TestMain` class, find `test_invalid_handoff_outputs_context` (plan lines 771-780):

```python
    def test_invalid_handoff_outputs_context(self) -> None:
        """Invalid handoff produces additionalContext JSON."""
        content = "---\ntype: handoff\n---\n## Goal\nShort."
        result, output = _run_main(
            _make_hook_input(HANDOFF_PATH, content)
        )
        assert result == 0
        parsed = json.loads(output)
        ctx = parsed["hookSpecificOutput"]["additionalContext"]
        assert "error" in ctx.lower()
```

Replace with:
```python
    def test_invalid_handoff_outputs_context(self) -> None:
        """Invalid handoff produces additionalContext JSON with correct contract."""
        content = "---\ntype: handoff\n---\n## Goal\nShort."
        result, output = _run_main(
            _make_hook_input(HANDOFF_PATH, content)
        )
        assert result == 0
        parsed = json.loads(output)
        hook_output = parsed["hookSpecificOutput"]
        assert hook_output["hookEventName"] == "PostToolUse"
        assert "error" in hook_output["additionalContext"].lower()
```

**Step 5: Commit**

```bash
git add docs/plans/2026-02-26-handoff-quality-hook.md
git commit -m "fix(plan): B2 unused imports, S3-S6 test coverage gaps

B2: Add TestCountBodyLines class (4 tests) — uses count_body_lines import.
    VALID_TYPES used in strengthened test_invalid_type_errors.
S3: TestCountBodyLines covers frontmatter/no-frontmatter/trailing-newline/unclosed.
S4: test_hollow_guardrail_skipped_when_sections_absent — regression test.
S5: test_invalid_type_errors asserts exactly 1 issue (early return).
S6: test_invalid_handoff_outputs_context asserts hookEventName == PostToolUse."
```

---

## Task 3: Fix Documentation and Metadata (B3, S7)

**Files:**
- Modify: `docs/plans/2026-02-26-handoff-quality-hook.md` — step text, design table, test count

**Step 1: Fix B3 — Update stale test counts**

Find at plan line 1130:
```
Expected: All 44 tests PASS
```

Replace with:
```
Expected: All 55 tests PASS
```

(The new count is 50 original + 4 new `TestCountBodyLines` + 1 new `test_hollow_guardrail_skipped_when_sections_absent` = 55.)

Find at plan line 1135:
```
Expected: All 73 tests PASS (55 existing + 18... wait)
```

Replace with:
```
Expected: All 110 tests PASS (55 existing + 55 new)
```

Also update the test count note block (plan lines 1148-1159). Find:
```
New counts after Codex review fixes:
- TestParseFrontmatter: 4
- TestValidateFrontmatter: 5 (removed test_wrong_type — dead code)
- TestParseSections: 5 (added code fence test)
- TestValidateSections: 8 (added 2 hollow-handoff guardrail tests)
- TestValidateLineCount: 7
- TestValidate: 6 (added invalid type test)
- TestIsHandoffPath: 6
- TestFormatOutput: 3 (updated warnings_only test)
- TestMain: 6

Total: 50 tests. Plus 55 existing = 105 total.
```

Replace with:
```
New counts after Codex review fixes:
- TestParseFrontmatter: 4
- TestValidateFrontmatter: 5 (removed test_wrong_type — dead code)
- TestParseSections: 5 (added code fence test)
- TestValidateSections: 9 (added 2 hollow-handoff guardrail + 1 double-fire regression)
- TestCountBodyLines: 4 (new — frontmatter/no-frontmatter/trailing-newline/unclosed)
- TestValidateLineCount: 7
- TestValidate: 6 (added invalid type test)
- TestIsHandoffPath: 6
- TestFormatOutput: 3 (updated warnings_only test)
- TestMain: 6

Total: 55 tests. Plus 55 existing = 110 total.
```

Update the Step 6 expected count at plan line 1162:
```
Expected: All tests PASS (55 existing + 50 new = 105 total)
```

Replace with:
```
Expected: All tests PASS (55 existing + 55 new = 110 total)
```

**Step 2: Fix S7 — Design table checkpoint line range**

Find at plan line 1489:
```
| Body line count | Count lines after frontmatter closing `---` | Quality targets (400, 22-55) refer to body lines. Counting total lines inflated by ~15 frontmatter lines. (Codex review) |
```

Replace with:
```
| Body line count | Count lines after frontmatter closing `---` | Quality targets (400, 20-80) refer to body lines. Counting total lines inflated by ~15 frontmatter lines. (Codex review) |
```

**Step 3: Commit**

```bash
git add docs/plans/2026-02-26-handoff-quality-hook.md
git commit -m "fix(plan): B3 stale test counts, S7 design table constants

B3: Update 44→55 and 73→110 test counts. Add TestCountBodyLines (4)
    and hollow regression test (1) to count table.
S7: Design table 22-55 → 20-80 matching code constants."
```

---

## Task 4: Verify All Fixes

**Step 1: Verify B1 — Hollow guardrail code has the gate condition**

Run: `grep -n "len(present_content_sections)" docs/plans/2026-02-26-handoff-quality-hook.md`
Expected: Match at the `validate_sections` implementation showing the presence gate.

**Step 2: Verify S1 — Paired-quote check**

Run: `grep -n "startswith.*endswith" docs/plans/2026-02-26-handoff-quality-hook.md`
Expected: Match showing `if (value.startswith('"') and value.endswith('"'))` pattern.

**Step 3: Verify S2 — splitlines**

Run: `grep -n "splitlines" docs/plans/2026-02-26-handoff-quality-hook.md`
Expected: Match in `count_body_lines` implementation.

**Step 4: Verify B2 — TestCountBodyLines exists**

Run: `grep -n "TestCountBodyLines" docs/plans/2026-02-26-handoff-quality-hook.md`
Expected: Class definition and test count table entry.

**Step 5: Verify B3 — Test counts are consistent**

Run: `grep -n "55 tests\|110 total\|55 new" docs/plans/2026-02-26-handoff-quality-hook.md`
Expected: Consistent counts throughout (55 new tests, 110 total).

**Step 6: Verify S7 — Design table constants**

Run: `grep -n "20-80" docs/plans/2026-02-26-handoff-quality-hook.md`
Expected: Match in design table.

**Step 7: Commit (verification pass)**

No commit needed — this task is read-only verification.
