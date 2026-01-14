# Three-Lens-Audit Scrutiny Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Address P1 and P2 findings from rigorous scrutiny of three-lens-audit skill.

**Architecture:** TDD approach—write failing tests first, then implement minimal code to pass. Consolidate shared utilities into `common.py` to reduce duplication. Fix documentation to match implementation reality.

**Tech Stack:** Python 3.12, pytest, stdlib only (no external deps in skill scripts)

**Findings Addressed:**

| Priority | Issue | Task |
|----------|-------|------|
| P1 | `--impl-spec` docs don't match implementation | Task 1 |
| P1 | Missing tests for `finalize()` | Task 2 |
| P1 | Missing tests for `synthesize()` | Task 3 |
| P1 | Missing tests for `find_convergent_findings()` | Task 4 |
| P2 | Duplicate table parsing logic | Task 5 |
| P2 | Missing tests for `detect_lens_from_content()` | Task 6 |

---

## Task 1: Fix Documentation-Implementation Mismatch for `--impl-spec`

**Files:**
- Modify: `.claude/skills/three-lens-audit/SKILL.md:77`
- Modify: `.claude/skills/three-lens-audit/references/scripts-reference.md`

The SKILL.md shows `/three-lens-audit <file> --impl-spec` as if it's a slash command flag, but `--impl-spec` is actually a flag on `run_audit.py finalize`. Fix the documentation to be accurate.

**Step 1: Update SKILL.md Commands table**

In `.claude/skills/three-lens-audit/SKILL.md`, change line 77 from:
```markdown
| `/three-lens-audit <file> --impl-spec` | Output implementation spec for fixes |
```

To:
```markdown
| `finalize ... --impl-spec` | Output implementation spec instead of synthesis |
```

**Step 2: Update SKILL.md Workflow section**

In `.claude/skills/three-lens-audit/SKILL.md`, update the workflow section (around line 89) to show the `--impl-spec` flag usage:

Change:
```markdown
# 3. Finalize — validate + synthesize
python scripts/run_audit.py finalize adversarial.md pragmatic.md cost-benefit.md --target "Name"
```

To:
```markdown
# 3. Finalize — validate + synthesize
python scripts/run_audit.py finalize adversarial.md pragmatic.md cost-benefit.md --target "Name"

# 3b. (Alternative) Generate implementation spec for execution
python scripts/run_audit.py finalize adversarial.md pragmatic.md cost-benefit.md --target "Name" --impl-spec
```

**Step 3: Verify scripts-reference.md is accurate**

Check `.claude/skills/three-lens-audit/references/scripts-reference.md` lines 101-107 already correctly document `--impl-spec` as part of finalize. No changes needed if accurate.

**Step 4: Update CHANGELOG.md**

Add entry to CHANGELOG.md:
```markdown
## [1.16.1] - 2026-01-07

### Fixed
- SKILL.md Commands table incorrectly showed `--impl-spec` as slash command flag
```

**Step 5: Commit**

```bash
git add .claude/skills/three-lens-audit/SKILL.md .claude/skills/three-lens-audit/CHANGELOG.md
git commit -m "docs(three-lens-audit): fix --impl-spec documentation accuracy"
```

---

## Task 2: Add Tests for `finalize()` Function

**Files:**
- Modify: `.claude/skills/three-lens-audit/scripts/tests/test_run_audit.py`

The `finalize()` function has no test coverage. It orchestrates validation + synthesis and has several edge cases.

**Step 1: Write test for successful finalize with all valid outputs**

Add to `test_run_audit.py`:

```python
from run_audit import finalize, FinalizeResult


class TestFinalize:
    """Tests for finalize function."""

    def test_successful_finalize_with_valid_outputs(self, tmp_path):
        """Finalize succeeds when all outputs are valid."""
        # Create valid adversarial output
        adv = tmp_path / "adversarial.md"
        adv.write_text("""# Adversarial
| Vulnerability | Evidence | Attack Scenario | Severity |
|---------------|----------|-----------------|----------|
| Test vuln | Line 1 | Attacker does X | Major |
""")
        # Create valid pragmatic output
        prag = tmp_path / "pragmatic.md"
        prag.write_text("""# Pragmatic
## What Works
- Good stuff
## What's Missing
- Missing stuff
## Friction Points
- Friction
## Verdict
Acceptable.
""")
        # Create valid cost-benefit output
        cb = tmp_path / "cost-benefit.md"
        cb.write_text("""# Cost/Benefit
| Element | Effort | Benefit | Verdict |
|---------|--------|---------|---------|
| Feature | H | M | Keep |

## High-ROI
- Good investment
## Low-ROI
- Cut this
## Recommendations
- Do X
""")

        result = finalize([adv, prag, cb], target="test.md")

        assert result.validation.all_passed
        assert result.synthesis_result is not None
        assert len(result.warnings) == 0
```

**Step 2: Run test to verify it fails**

```bash
cd .claude/skills/three-lens-audit/scripts && python -m pytest tests/test_run_audit.py::TestFinalize::test_successful_finalize_with_valid_outputs -v
```

Expected: Should pass (function exists). If it fails, check import.

**Step 3: Write test for finalize with insufficient valid outputs**

Add to `TestFinalize` class:

```python
    def test_finalize_with_insufficient_outputs_returns_no_synthesis(self, tmp_path):
        """Finalize returns no synthesis when < 2 outputs pass validation."""
        # Create one valid file
        adv = tmp_path / "adversarial.md"
        adv.write_text("""# Adversarial
| Vulnerability | Evidence | Attack Scenario | Severity |
|---------------|----------|-----------------|----------|
| Issue | Proof | Attack | Major |
""")
        # Create one invalid file (too short)
        prag = tmp_path / "pragmatic.md"
        prag.write_text("too short")

        # Create another invalid file
        cb = tmp_path / "cost-benefit.md"
        cb.write_text("also too short")

        result = finalize([adv, prag, cb], target="test.md")

        assert not result.validation.all_passed
        assert result.synthesis_result is None
        assert any("Insufficient" in w for w in result.warnings)
```

**Step 4: Run test to verify behavior**

```bash
cd .claude/skills/three-lens-audit/scripts && python -m pytest tests/test_run_audit.py::TestFinalize::test_finalize_with_insufficient_outputs_returns_no_synthesis -v
```

**Step 5: Write test for finalize with missing files**

Add to `TestFinalize` class:

```python
    def test_finalize_handles_missing_files(self, tmp_path):
        """Finalize handles missing files gracefully."""
        missing1 = tmp_path / "nonexistent1.md"
        missing2 = tmp_path / "nonexistent2.md"
        missing3 = tmp_path / "nonexistent3.md"

        result = finalize([missing1, missing2, missing3], target="test.md")

        assert not result.validation.all_passed
        assert result.synthesis_result is None
```

**Step 6: Run all finalize tests**

```bash
cd .claude/skills/three-lens-audit/scripts && python -m pytest tests/test_run_audit.py::TestFinalize -v
```

**Step 7: Commit**

```bash
git add .claude/skills/three-lens-audit/scripts/tests/test_run_audit.py
git commit -m "test(three-lens-audit): add finalize() test coverage"
```

---

## Task 3: Add Tests for `synthesize()` Function

**Files:**
- Modify: `.claude/skills/three-lens-audit/scripts/tests/test_synthesize.py`

The core `synthesize()` function lacks tests despite being the most important function.

**Step 1: Write test for synthesize with valid inputs**

Add to `test_synthesize.py`:

```python
from synthesize import synthesize, SynthesisResult


class TestSynthesize:
    """Tests for synthesize function."""

    def test_synthesize_returns_synthesis_result(self, tmp_path):
        """Synthesize returns SynthesisResult with valid inputs."""
        # Create minimal valid outputs
        adv = tmp_path / "adversarial.md"
        adv.write_text("""# Adversarial
| Vulnerability | Evidence | Attack Scenario | Severity |
|---------------|----------|-----------------|----------|
| Input validation missing | line 42 | Inject bad data | Major |
""")
        prag = tmp_path / "pragmatic.md"
        prag.write_text("""# Pragmatic
## What Works
- Clear structure
## What's Missing
- Input validation is missing
## Friction Points
- Setup is complex
## Verdict
Needs work.
""")
        cb = tmp_path / "cost-benefit.md"
        cb.write_text("""# Cost/Benefit
| Element | Effort | Benefit | Verdict |
|---------|--------|---------|---------|
| Validation | L | H | Add |
## High-ROI
- Add input validation
## Low-ROI
- Complex features
## Recommendations
- Start with validation
""")

        lens_files = {
            "adversarial": adv,
            "pragmatic": prag,
            "cost-benefit": cb
        }

        result = synthesize(lens_files, target="test.md")

        assert isinstance(result, SynthesisResult)
        assert result.target == "test.md"
        assert "adversarial" in result.lens_outputs
        assert "pragmatic" in result.lens_outputs
        assert "cost-benefit" in result.lens_outputs
```

**Step 2: Run test**

```bash
cd .claude/skills/three-lens-audit/scripts && python -m pytest tests/test_synthesize.py::TestSynthesize::test_synthesize_returns_synthesis_result -v
```

**Step 3: Write test for synthesize with missing file**

```python
    def test_synthesize_warns_on_missing_file(self, tmp_path):
        """Synthesize adds warning for missing files."""
        existing = tmp_path / "adversarial.md"
        existing.write_text("Some content here that is long enough to pass")
        missing = tmp_path / "missing.md"

        lens_files = {
            "adversarial": existing,
            "pragmatic": missing
        }

        result = synthesize(lens_files, target="test.md")

        assert any("not found" in w.lower() for w in result.warnings)
```

**Step 4: Run test**

```bash
cd .claude/skills/three-lens-audit/scripts && python -m pytest tests/test_synthesize.py::TestSynthesize::test_synthesize_warns_on_missing_file -v
```

**Step 5: Write test for synthesize with insufficient outputs**

```python
    def test_synthesize_warns_with_single_output(self, tmp_path):
        """Synthesize warns when only one lens output provided."""
        single = tmp_path / "adversarial.md"
        single.write_text("Content that is long enough to be processed by the system")

        lens_files = {"adversarial": single}

        result = synthesize(lens_files, target="test.md")

        assert any("insufficient" in w.lower() for w in result.warnings)
        assert result.convergent_3 == []
        assert result.convergent_2 == []
```

**Step 6: Run all synthesize tests**

```bash
cd .claude/skills/three-lens-audit/scripts && python -m pytest tests/test_synthesize.py::TestSynthesize -v
```

**Step 7: Commit**

```bash
git add .claude/skills/three-lens-audit/scripts/tests/test_synthesize.py
git commit -m "test(three-lens-audit): add synthesize() test coverage"
```

---

## Task 4: Add Tests for `find_convergent_findings()` Function

**Files:**
- Modify: `.claude/skills/three-lens-audit/scripts/tests/test_synthesize.py`

This is the core algorithm—it needs thorough testing.

**Step 1: Write test for no convergence when findings are disjoint**

Add to `test_synthesize.py`:

```python
from synthesize import find_convergent_findings, Finding


class TestFindConvergentFindings:
    """Tests for find_convergent_findings function."""

    def test_no_convergence_with_disjoint_findings(self):
        """No convergent findings when keywords don't overlap."""
        findings = {
            "adversarial": [
                Finding(text="Security vulnerability in auth", lens="adversarial",
                        keywords={"security", "vulnerability", "auth"})
            ],
            "pragmatic": [
                Finding(text="Database performance issues", lens="pragmatic",
                        keywords={"database", "performance", "issues"})
            ],
            "cost-benefit": [
                Finding(text="Marketing budget allocation", lens="cost-benefit",
                        keywords={"marketing", "budget", "allocation"})
            ]
        }

        conv_3, conv_2 = find_convergent_findings(findings, threshold=0.3)

        assert conv_3 == []
        assert conv_2 == []
```

**Step 2: Run test**

```bash
cd .claude/skills/three-lens-audit/scripts && python -m pytest tests/test_synthesize.py::TestFindConvergentFindings::test_no_convergence_with_disjoint_findings -v
```

**Step 3: Write test for 2-lens convergence**

```python
    def test_two_lens_convergence_detected(self):
        """Detects convergence when 2 lenses share keywords."""
        findings = {
            "adversarial": [
                Finding(text="Input validation missing causes security risk", lens="adversarial",
                        keywords={"input", "validation", "missing", "security", "risk"})
            ],
            "pragmatic": [
                Finding(text="Input validation is confusing to users", lens="pragmatic",
                        keywords={"input", "validation", "confusing", "users"})
            ],
            "cost-benefit": [
                Finding(text="Completely unrelated topic here", lens="cost-benefit",
                        keywords={"completely", "unrelated", "topic"})
            ]
        }

        conv_3, conv_2 = find_convergent_findings(findings, threshold=0.3)

        assert conv_3 == []
        assert len(conv_2) >= 1
        # Verify the convergent finding involves adversarial and pragmatic
        lenses_found = set()
        for c in conv_2:
            lenses_found.update(c.lenses.keys())
        assert "adversarial" in lenses_found
        assert "pragmatic" in lenses_found
```

**Step 4: Run test**

```bash
cd .claude/skills/three-lens-audit/scripts && python -m pytest tests/test_synthesize.py::TestFindConvergentFindings::test_two_lens_convergence_detected -v
```

**Step 5: Write test for 3-lens convergence**

```python
    def test_three_lens_convergence_detected(self):
        """Detects convergence when all 3 lenses share keywords."""
        findings = {
            "adversarial": [
                Finding(text="Authentication system has critical vulnerability", lens="adversarial",
                        keywords={"authentication", "system", "critical", "vulnerability"})
            ],
            "pragmatic": [
                Finding(text="Authentication system is hard to use correctly", lens="pragmatic",
                        keywords={"authentication", "system", "hard", "correctly"})
            ],
            "cost-benefit": [
                Finding(text="Authentication system maintenance is expensive", lens="cost-benefit",
                        keywords={"authentication", "system", "maintenance", "expensive"})
            ]
        }

        conv_3, conv_2 = find_convergent_findings(findings, threshold=0.3)

        assert len(conv_3) >= 1
        # 3-lens convergent should have all 3 lenses
        for c in conv_3:
            assert len(c.lenses) == 3
```

**Step 6: Write test for empty findings**

```python
    def test_handles_empty_findings(self):
        """Handles empty findings gracefully."""
        findings = {
            "adversarial": [],
            "pragmatic": [],
            "cost-benefit": []
        }

        conv_3, conv_2 = find_convergent_findings(findings, threshold=0.3)

        assert conv_3 == []
        assert conv_2 == []

    def test_handles_single_lens(self):
        """Returns empty when only one lens provided."""
        findings = {
            "adversarial": [
                Finding(text="Some finding", lens="adversarial", keywords={"some", "finding"})
            ]
        }

        conv_3, conv_2 = find_convergent_findings(findings, threshold=0.3)

        assert conv_3 == []
        assert conv_2 == []
```

**Step 7: Run all convergence tests**

```bash
cd .claude/skills/three-lens-audit/scripts && python -m pytest tests/test_synthesize.py::TestFindConvergentFindings -v
```

**Step 8: Commit**

```bash
git add .claude/skills/three-lens-audit/scripts/tests/test_synthesize.py
git commit -m "test(three-lens-audit): add find_convergent_findings() test coverage"
```

---

## Task 5: Consolidate Table Parsing into `common.py`

**Files:**
- Create: `.claude/skills/three-lens-audit/scripts/common.py`
- Create: `.claude/skills/three-lens-audit/scripts/tests/test_common.py`
- Modify: `.claude/skills/three-lens-audit/scripts/synthesize.py`
- Modify: `.claude/skills/three-lens-audit/scripts/validate_output.py`

Both `synthesize.py` and `validate_output.py` implement markdown table parsing independently. Consolidate.

**Step 1: Create test file for common.py**

Create `.claude/skills/three-lens-audit/scripts/tests/test_common.py`:

```python
"""Tests for common.py shared utilities."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from common import parse_markdown_table, count_table_rows


class TestParseMarkdownTable:
    """Tests for parse_markdown_table function."""

    def test_parses_simple_table(self):
        """Parses a simple markdown table with headers and rows."""
        content = """\
| Header1 | Header2 |
|---------|---------|
| value1  | value2  |
| value3  | value4  |
"""
        rows = parse_markdown_table(content)
        assert len(rows) == 2
        assert rows[0]["Header1"] == "value1"
        assert rows[0]["Header2"] == "value2"
        assert rows[1]["Header1"] == "value3"

    def test_returns_empty_for_no_table(self):
        """Returns empty list when no table present."""
        content = "Just some text without tables."
        rows = parse_markdown_table(content)
        assert rows == []

    def test_handles_table_with_extra_whitespace(self):
        """Handles cells with extra whitespace."""
        content = """\
|   Header1   |   Header2   |
|-------------|-------------|
|   value1    |   value2    |
"""
        rows = parse_markdown_table(content)
        assert rows[0]["Header1"] == "value1"


class TestCountTableRows:
    """Tests for count_table_rows function."""

    def test_counts_data_rows(self):
        """Counts only data rows, not header or separator."""
        content = """\
| Header |
|--------|
| row1   |
| row2   |
| row3   |
"""
        assert count_table_rows(content) == 3

    def test_returns_zero_for_no_table(self):
        """Returns 0 when no table present."""
        assert count_table_rows("No tables here") == 0

    def test_returns_zero_for_header_only(self):
        """Returns 0 when table has only header."""
        content = """\
| Header |
|--------|
"""
        assert count_table_rows(content) == 0
```

**Step 2: Run tests to verify they fail (common.py doesn't exist)**

```bash
cd .claude/skills/three-lens-audit/scripts && python -m pytest tests/test_common.py -v
```

Expected: ImportError (module doesn't exist)

**Step 3: Create common.py with consolidated table parsing**

Create `.claude/skills/three-lens-audit/scripts/common.py`:

```python
#!/usr/bin/env python3
"""
common.py - Shared utilities for three-lens-audit scripts

Provides consolidated implementations used by multiple scripts:
- Markdown table parsing
- Keyword extraction
"""

import re
from typing import List, Dict


def parse_markdown_table(content: str) -> List[Dict[str, str]]:
    """
    Parse markdown tables and return data rows as dicts.

    Args:
        content: Markdown content potentially containing tables

    Returns:
        List of dicts mapping header names to cell values.
        Empty list if no valid table found.
    """
    rows = []
    lines = content.split('\n')
    current_headers = []
    in_table = False

    for line in lines:
        stripped = line.strip()
        if '|' in stripped:
            # Extract cells (skip empty first/last from leading/trailing |)
            cells = [c.strip() for c in stripped.split('|')[1:-1]]

            if re.match(r'^[\s\-:|]+$', stripped.replace('|', '')):
                # Separator row - previous row was headers
                in_table = True
            elif not in_table and cells:
                # Potential header row
                current_headers = cells
            elif in_table and cells:
                # Data row
                if len(cells) == len(current_headers):
                    rows.append(dict(zip(current_headers, cells)))
                else:
                    # Mismatched columns - store raw
                    rows.append({'raw': ' | '.join(cells)})
        else:
            if stripped and not stripped.startswith('#'):
                in_table = False

    return rows


def count_table_rows(content: str) -> int:
    """
    Count data rows in markdown tables (excludes header and separator).

    Args:
        content: Markdown content potentially containing tables

    Returns:
        Number of data rows found across all tables.
    """
    lines = content.split('\n')
    row_count = 0
    in_table = False

    for line in lines:
        stripped = line.strip()
        if '|' in stripped:
            if re.match(r'^\|[\s\-:|]+\|$', stripped):
                # Separator row - table body starts after this
                in_table = True
            elif in_table and stripped.startswith('|') and stripped.endswith('|'):
                # Data row
                row_count += 1
            elif not stripped.startswith('|'):
                in_table = False
        else:
            in_table = False

    return row_count
```

**Step 4: Run tests to verify they pass**

```bash
cd .claude/skills/three-lens-audit/scripts && python -m pytest tests/test_common.py -v
```

**Step 5: Update validate_output.py to use common.py**

In `.claude/skills/three-lens-audit/scripts/validate_output.py`, add import and replace `find_table_rows`:

```python
# At top, add import
try:
    from common import count_table_rows
except ImportError:
    from .common import count_table_rows

# Then delete the local find_table_rows function (lines 148-169)
# And rename usage from find_table_rows to count_table_rows
```

Find and replace in validate_output.py:
- Remove `def find_table_rows(content: str) -> int:` function entirely
- Change `row_count = find_table_rows(content)` to `row_count = count_table_rows(content)`

**Step 6: Run validate_output tests to ensure they still pass**

```bash
cd .claude/skills/three-lens-audit/scripts && python -m pytest tests/test_validate_output.py -v
```

**Step 7: Update synthesize.py to use common.py**

In `.claude/skills/three-lens-audit/scripts/synthesize.py`, add import and replace `extract_table_rows`:

```python
# At top, add import
try:
    from common import parse_markdown_table
except ImportError:
    from .common import parse_markdown_table

# Then delete the local extract_table_rows function (lines 107-136)
# And rename usage from extract_table_rows to parse_markdown_table
```

Find and replace in synthesize.py:
- Remove `def extract_table_rows(content: str) -> List[Dict[str, str]]:` function entirely
- Change `for row in extract_table_rows(content):` to `for row in parse_markdown_table(content):`

**Step 8: Run synthesize tests to ensure they still pass**

```bash
cd .claude/skills/three-lens-audit/scripts && python -m pytest tests/test_synthesize.py -v
```

**Step 9: Update test imports**

In `tests/test_synthesize.py`, update the imports to remove `extract_table_rows`:

```python
from synthesize import (
    STOP_WORDS,
    Finding,
    ConvergentFinding,
    SynthesisResult,
    calculate_overlap,
    extract_keywords,
    extract_sections,
    # Remove: extract_table_rows,
    generate_implementation_spec_markdown,
)

# Add import for common
from common import parse_markdown_table
```

And update `TestExtractTableRows` to test `parse_markdown_table` from common:

```python
class TestParseMarkdownTable:
    """Tests for parse_markdown_table function (moved to common.py)."""

    def test_extracts_data_rows(self):
        """Extracts data rows from a markdown table."""
        content = """\
| Header1 | Header2 |
|---------|---------|
| value1  | value2  |
| value3  | value4  |
"""
        rows = parse_markdown_table(content)
        assert len(rows) == 2
        assert rows[0]["Header1"] == "value1"
```

**Step 10: Run all tests**

```bash
cd .claude/skills/three-lens-audit/scripts && python -m pytest tests/ -v
```

**Step 11: Commit**

```bash
git add .claude/skills/three-lens-audit/scripts/common.py \
        .claude/skills/three-lens-audit/scripts/tests/test_common.py \
        .claude/skills/three-lens-audit/scripts/synthesize.py \
        .claude/skills/three-lens-audit/scripts/validate_output.py \
        .claude/skills/three-lens-audit/scripts/tests/test_synthesize.py
git commit -m "refactor(three-lens-audit): consolidate table parsing into common.py"
```

---

## Task 6: Add Tests for `detect_lens_from_content()` Function

**Files:**
- Modify: `.claude/skills/three-lens-audit/scripts/tests/test_synthesize.py`

This function is used by `--auto-detect` but has no tests.

**Step 1: Write tests for lens detection**

Add to `test_synthesize.py`:

```python
from synthesize import detect_lens_from_content


class TestDetectLensFromContent:
    """Tests for detect_lens_from_content function."""

    def test_detects_adversarial(self):
        """Detects adversarial lens from content."""
        content = "As an Adversarial Auditor, I found these attack vectors..."
        assert detect_lens_from_content(content) == "adversarial"

    def test_detects_pragmatic(self):
        """Detects pragmatic lens from content."""
        content = "As a Pragmatic Practitioner, here's what works..."
        assert detect_lens_from_content(content) == "pragmatic"

    def test_detects_cost_benefit(self):
        """Detects cost-benefit lens from content."""
        content = "The Cost/Benefit analysis shows effort vs benefit..."
        assert detect_lens_from_content(content) == "cost-benefit"

    def test_detects_robustness(self):
        """Detects robustness lens from content."""
        content = "As the Robustness Advocate, I identified gaps..."
        assert detect_lens_from_content(content) == "robustness"

    def test_detects_minimalist(self):
        """Detects minimalist lens from content."""
        content = "The Minimalist Advocate recommends cutting..."
        assert detect_lens_from_content(content) == "minimalist"

    def test_detects_capability(self):
        """Detects capability lens from content."""
        content = "As the Capability Realist, the assumption vs reality..."
        assert detect_lens_from_content(content) == "capability"

    def test_detects_arbiter(self):
        """Detects arbiter lens from content."""
        content = "The Arbiter's verdict on critical path..."
        assert detect_lens_from_content(content) == "arbiter"

    def test_returns_none_for_unknown(self):
        """Returns None when lens cannot be detected."""
        content = "This is some generic content without lens markers."
        assert detect_lens_from_content(content) is None

    def test_case_insensitive(self):
        """Detection is case-insensitive."""
        content = "ADVERSARIAL AUDITOR found vulnerabilities"
        assert detect_lens_from_content(content) == "adversarial"
```

**Step 2: Run tests**

```bash
cd .claude/skills/three-lens-audit/scripts && python -m pytest tests/test_synthesize.py::TestDetectLensFromContent -v
```

**Step 3: Commit**

```bash
git add .claude/skills/three-lens-audit/scripts/tests/test_synthesize.py
git commit -m "test(three-lens-audit): add detect_lens_from_content() test coverage"
```

---

## Task 7: Update CHANGELOG and Version

**Files:**
- Modify: `.claude/skills/three-lens-audit/CHANGELOG.md`
- Modify: `.claude/skills/three-lens-audit/SKILL.md`

**Step 1: Update CHANGELOG.md**

Add comprehensive entry at the top of CHANGELOG.md:

```markdown
## [1.17.0] - 2026-01-07

### Added
- `common.py` module with consolidated markdown table parsing
- Test coverage for `finalize()` function (3 tests)
- Test coverage for `synthesize()` function (3 tests)
- Test coverage for `find_convergent_findings()` function (5 tests)
- Test coverage for `detect_lens_from_content()` function (9 tests)

### Changed
- `synthesize.py` now imports table parsing from `common.py`
- `validate_output.py` now imports table parsing from `common.py`

### Fixed
- SKILL.md Commands table incorrectly showed `--impl-spec` as slash command flag
```

**Step 2: Update SKILL.md version**

Change line 7 in SKILL.md from:
```yaml
  version: 1.16.0
```

To:
```yaml
  version: 1.17.0
```

**Step 3: Final test run**

```bash
cd .claude/skills/three-lens-audit/scripts && python -m pytest tests/ -v
```

Expected: All tests pass (should be 57 + new tests = ~75+ tests)

**Step 4: Final commit**

```bash
git add .claude/skills/three-lens-audit/CHANGELOG.md .claude/skills/three-lens-audit/SKILL.md
git commit -m "chore(three-lens-audit): bump version to 1.17.0"
```

---

## Summary

| Task | Tests Added | Files Changed | Commit |
|------|-------------|---------------|--------|
| 1 | 0 | SKILL.md, CHANGELOG.md | docs fix |
| 2 | 3 | test_run_audit.py | finalize tests |
| 3 | 3 | test_synthesize.py | synthesize tests |
| 4 | 5 | test_synthesize.py | convergence tests |
| 5 | 5 | common.py, synthesize.py, validate_output.py, test_common.py | refactor |
| 6 | 9 | test_synthesize.py | detection tests |
| 7 | 0 | CHANGELOG.md, SKILL.md | version bump |

**Total new tests:** ~25
**Total files created:** 2 (common.py, test_common.py)
**Total commits:** 7
