# Verify Skill v3.1.0 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add introspection capabilities to the verify skill: cache statistics, duplicate detection, simplified quick-add CLI, and coverage analysis.

**Architecture:** Four independent features extending verify.py CLI. Each feature adds a new flag and supporting functions. Statistics and quick-add are pure additions; duplicates and coverage add new scripts with verify.py integration.

**Tech Stack:** Python 3.12, standard library only, pytest for tests

---

## Summary

| Task | Feature | Effort | New Files |
|------|---------|--------|-----------|
| 1 | Cache Statistics (`--stats`) | Low | test only |
| 2 | Duplicate Detection (`--find-duplicates`) | Low | detect_duplicates.py |
| 3 | Simplified Quick-Add | Low | test only |
| 4 | Coverage Analysis (`--coverage`) | Medium | coverage_analysis.py |

**Order rationale:** Lowest effort first for fast value delivery.

---

## Task 1: Cache Statistics (`--stats`)

**Priority:** Medium | **Effort:** Low

**Files:**
- Modify: `.claude/skills/verify/scripts/verify.py`
- Create: `.claude/skills/verify/tests/test_stats.py`

### Step 1: Write the failing test

Create test file:

```python
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


if __name__ == "__main__":
    unittest.main()
```

### Step 2: Run test to verify it fails

```bash
cd .claude/skills/verify
python -m pytest tests/test_stats.py -v
```

Expected: FAIL with `ImportError: cannot import name 'calculate_cache_stats'`

### Step 3: Write the calculate_cache_stats function

Add to `.claude/skills/verify/scripts/verify.py` after the `infer_severity` function (around line 117):

```python
# =============================================================================
# CACHE STATISTICS
# =============================================================================

def calculate_cache_stats(known_path: Path, max_age_days: int = 90) -> dict:
    """
    Calculate comprehensive cache statistics.

    Returns dict with:
        total: int
        by_section: dict[str, int]
        by_verdict: dict[str, int]  # verified, false, partial, unverified
        by_age: dict[str, int]  # fresh (<30d), aging (30-90d), stale (>90d)
        oldest_claim: str | None
        newest_claim: str | None
    """
    from datetime import date as date_module, timedelta

    if not known_path.exists():
        return {
            "total": 0,
            "by_section": {},
            "by_verdict": {},
            "by_age": {"fresh": 0, "aging": 0, "stale": 0},
            "oldest_claim": None,
            "newest_claim": None,
        }

    claims = parse_known_claims(known_path)
    today = date_module.today()

    stats = {
        "total": len(claims),
        "by_section": {},
        "by_verdict": {"verified": 0, "false": 0, "partial": 0, "unverified": 0},
        "by_age": {"fresh": 0, "aging": 0, "stale": 0},
        "oldest_claim": None,
        "newest_claim": None,
    }

    oldest_date = None
    newest_date = None

    for claim in claims:
        # Count by section
        section = claim.section
        stats["by_section"][section] = stats["by_section"].get(section, 0) + 1

        # Count by verdict
        verdict_lower = claim.verdict.lower()
        if "verified" in verdict_lower and "unverified" not in verdict_lower:
            stats["by_verdict"]["verified"] += 1
        elif "false" in verdict_lower or "contradicted" in verdict_lower:
            stats["by_verdict"]["false"] += 1
        elif "partial" in verdict_lower:
            stats["by_verdict"]["partial"] += 1
        else:
            stats["by_verdict"]["unverified"] += 1

        # Count by age
        from _common import parse_verified_date
        verified_date = parse_verified_date(claim.verified_date)
        if verified_date:
            age_days = (today - verified_date).days
            if age_days < 30:
                stats["by_age"]["fresh"] += 1
            elif age_days < max_age_days:
                stats["by_age"]["aging"] += 1
            else:
                stats["by_age"]["stale"] += 1

            # Track oldest/newest
            if oldest_date is None or verified_date < oldest_date:
                oldest_date = verified_date
                stats["oldest_claim"] = claim.claim
            if newest_date is None or verified_date > newest_date:
                newest_date = verified_date
                stats["newest_claim"] = claim.claim

    return stats
```

### Step 4: Run test to verify it passes

```bash
cd .claude/skills/verify
python -m pytest tests/test_stats.py -v
```

Expected: All 4 tests PASS

### Step 5: Add cmd_stats handler and CLI flag

Add handler after `cmd_sections` function (around line 378):

```python
def cmd_stats(args: argparse.Namespace) -> int:
    """Display comprehensive cache statistics."""
    if not KNOWN_CLAIMS_PATH.exists():
        print("No cache file found.")
        return 1

    stats = calculate_cache_stats(KNOWN_CLAIMS_PATH, args.max_age)

    print("Cache Statistics")
    print("=" * 40)
    print()

    # Total
    print(f"Total claims: {stats['total']}")
    print()

    # By verdict
    print("By verdict:")
    for verdict, count in sorted(stats["by_verdict"].items(), key=lambda x: -x[1]):
        if count > 0:
            pct = count / stats["total"] * 100 if stats["total"] else 0
            print(f"  {verdict.capitalize():12} {count:3} ({pct:4.1f}%)")
    print()

    # By section
    print("By section:")
    for section, count in sorted(stats["by_section"].items(), key=lambda x: -x[1]):
        print(f"  {section:12} {count:3}")
    print()

    # By age
    print(f"By age (TTL: {args.max_age}d):")
    for age_bucket in ["fresh", "aging", "stale"]:
        count = stats["by_age"][age_bucket]
        pct = count / stats["total"] * 100 if stats["total"] else 0
        label = {"fresh": "Fresh (<30d)", "aging": f"Aging (30-{args.max_age}d)", "stale": f"Stale (>{args.max_age}d)"}
        print(f"  {label[age_bucket]:20} {count:3} ({pct:4.1f}%)")

    return 0
```

Add CLI flag in the mode_group (around line 668):

```python
    mode_group.add_argument(
        "--stats",
        action="store_true",
        help="Display comprehensive cache statistics",
    )
```

Add dispatch in main() (around line 766, before `elif args.health:`):

```python
    if args.stats:
        return cmd_stats(args)
```

### Step 6: Test the CLI

```bash
cd .claude/skills/verify
python scripts/verify.py --stats
```

Expected: Statistics output showing counts by verdict, section, and age

### Step 7: Commit

```bash
git add .claude/skills/verify/scripts/verify.py
git add .claude/skills/verify/tests/test_stats.py
git commit -m "feat(verify): add cache statistics command

- New --stats flag displays comprehensive cache analysis
- Breakdown by verdict, section, and age bucket
- Helps identify cache health trends"
```

---

## Task 2: Duplicate Detection (`--find-duplicates`)

**Priority:** High | **Effort:** Low

**Files:**
- Create: `.claude/skills/verify/scripts/detect_duplicates.py`
- Create: `.claude/skills/verify/tests/test_detect_duplicates.py`
- Modify: `.claude/skills/verify/scripts/verify.py`

### Step 1: Write the failing test

Create test file:

```python
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


if __name__ == "__main__":
    unittest.main()
```

### Step 2: Run test to verify it fails

```bash
cd .claude/skills/verify
python -m pytest tests/test_detect_duplicates.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'detect_duplicates'`

### Step 3: Write the detect_duplicates.py script

Create `.claude/skills/verify/scripts/detect_duplicates.py`:

```python
#!/usr/bin/env python3
"""
Detect duplicate or near-duplicate claims in known-claims.md.

Uses fuzzy matching to find claims that are semantically similar,
which may indicate redundancy or inconsistency.

Exit codes:
    0 - No duplicates found
    1 - Input error
    2 - Duplicates found
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

# Import from sibling modules
from match_claim import parse_known_claims, KnownClaim


@dataclass
class DuplicateGroup:
    """A group of similar claims."""
    claims: list[KnownClaim]
    similarity: float
    section: str | None  # None if cross-section


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two strings using word overlap."""
    # Normalize
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    # Remove common stopwords
    stopwords = {"the", "a", "an", "is", "are", "in", "to", "for", "of", "and", "or"}
    words1 -= stopwords
    words2 -= stopwords

    if not words1 or not words2:
        return 0.0

    # Jaccard similarity
    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union if union else 0.0


def find_duplicate_groups(
    known_path: Path,
    threshold: float = 0.7,
    same_section_only: bool = False,
) -> list[dict]:
    """
    Find groups of similar claims.

    Args:
        known_path: Path to known-claims.md
        threshold: Minimum similarity (0.0-1.0) to consider duplicate
        same_section_only: Only compare within same section

    Returns:
        List of duplicate groups, each with claims and similarity score
    """
    if not known_path.exists():
        return []

    claims = parse_known_claims(known_path)
    if len(claims) < 2:
        return []

    # Track which claims are already in a group
    grouped: set[int] = set()
    groups: list[dict] = []

    for i, claim1 in enumerate(claims):
        if i in grouped:
            continue

        group_claims = [claim1]
        group_indices = {i}
        best_similarity = 0.0

        for j, claim2 in enumerate(claims[i + 1:], start=i + 1):
            if j in grouped:
                continue

            # Skip cross-section if requested
            if same_section_only and claim1.section != claim2.section:
                continue

            similarity = calculate_similarity(claim1.claim, claim2.claim)

            if similarity >= threshold:
                group_claims.append(claim2)
                group_indices.add(j)
                best_similarity = max(best_similarity, similarity)

        # Only create group if we found duplicates
        if len(group_claims) > 1:
            grouped.update(group_indices)
            groups.append({
                "claims": group_claims,
                "similarity": best_similarity,
                "section": claim1.section if same_section_only else None,
            })

    # Sort by similarity (highest first)
    groups.sort(key=lambda g: -g["similarity"])

    return groups


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect duplicate claims in cache")
    parser.add_argument(
        "--known-claims",
        type=Path,
        default=Path(__file__).parent.parent / "references" / "known-claims.md",
        help="Path to known-claims.md",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.7,
        help="Similarity threshold (0.0-1.0, default: 0.7)",
    )
    parser.add_argument(
        "--same-section",
        action="store_true",
        help="Only compare claims within the same section",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    args = parser.parse_args()

    if not args.known_claims.exists():
        print(f"Error: {args.known_claims} not found", file=sys.stderr)
        return 1

    groups = find_duplicate_groups(
        args.known_claims,
        threshold=args.threshold,
        same_section_only=args.same_section,
    )

    if args.json:
        import json
        output = [
            {
                "similarity": g["similarity"],
                "section": g["section"],
                "claims": [
                    {"claim": c.claim, "section": c.section, "verdict": c.verdict}
                    for c in g["claims"]
                ],
            }
            for g in groups
        ]
        print(json.dumps(output, indent=2))
    else:
        if not groups:
            print("No duplicate claims found.")
            return 0

        print(f"Found {len(groups)} group(s) of similar claims:\n")

        for i, group in enumerate(groups, 1):
            print(f"Group {i} (similarity: {group['similarity']:.2f}):")
            for claim in group["claims"]:
                print(f"  [{claim.section}] {claim.claim}")
                print(f"    Verdict: {claim.verdict}")
            print()

        print("Consider consolidating or removing redundant claims.")

    return 2 if groups else 0


if __name__ == "__main__":
    sys.exit(main())
```

### Step 4: Run test to verify it passes

```bash
cd .claude/skills/verify
python -m pytest tests/test_detect_duplicates.py -v
```

Expected: All 4 tests PASS

### Step 5: Integrate with verify.py

Add import in verify.py (after line 75):

```python
from detect_duplicates import find_duplicate_groups
```

Add handler after `cmd_stats` (around line 420):

```python
def cmd_find_duplicates(args: argparse.Namespace) -> int:
    """Find duplicate or similar claims in cache."""
    if not KNOWN_CLAIMS_PATH.exists():
        print("No cache file found.")
        return 1

    threshold = getattr(args, 'threshold', 0.7)
    groups = find_duplicate_groups(KNOWN_CLAIMS_PATH, threshold=threshold)

    if not groups:
        print("No duplicate claims found.")
        return 0

    print(f"Found {len(groups)} group(s) of similar claims:\n")

    for i, group in enumerate(groups, 1):
        print(f"Group {i} (similarity: {group['similarity']:.2f}):")
        for claim in group["claims"]:
            print(f"  [{claim.section}] {claim.claim}")
            print(f"    Verdict: {claim.verdict}")
        print()

    print("Consider consolidating or removing redundant claims.")
    return 2
```

Add CLI flag in mode_group:

```python
    mode_group.add_argument(
        "--find-duplicates",
        action="store_true",
        help="Find duplicate or similar claims in cache",
    )
```

Add threshold argument after other options:

```python
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.7,
        help="Similarity threshold for duplicate detection (default: 0.7)",
    )
```

Add dispatch in main():

```python
    if args.find_duplicates:
        return cmd_find_duplicates(args)
```

### Step 6: Test the CLI

```bash
cd .claude/skills/verify
python scripts/verify.py --find-duplicates
python scripts/verify.py --find-duplicates --threshold 0.5
```

Expected: Lists groups of similar claims (if any exist)

### Step 7: Commit

```bash
git add .claude/skills/verify/scripts/detect_duplicates.py
git add .claude/skills/verify/scripts/verify.py
git add .claude/skills/verify/tests/test_detect_duplicates.py
git commit -m "feat(verify): add duplicate claim detection

- New detect_duplicates.py finds similar claims using fuzzy matching
- --find-duplicates flag in unified CLI
- Configurable similarity threshold (default: 0.7)
- Helps identify redundant or inconsistent claims"
```

---

## Task 3: Simplified Quick-Add

**Priority:** Medium | **Effort:** Low

**Files:**
- Modify: `.claude/skills/verify/scripts/verify.py`
- Create: `.claude/skills/verify/tests/test_quick_add.py`

### Step 1: Write the failing test

Create test file:

```python
#!/usr/bin/env python3
"""Tests for simplified quick-add functionality."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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
```

### Step 2: Run test to verify it fails

```bash
cd .claude/skills/verify
python -m pytest tests/test_quick_add.py -v
```

Expected: FAIL with `ImportError: cannot import name 'parse_quick_add_input'`

### Step 3: Add parse_quick_add_input function

Add to verify.py after `infer_severity` function (around line 117):

```python
def parse_quick_add_input(text: str) -> tuple[str, str | None, str | None]:
    """
    Parse quick-add input text.

    Supports formats:
        "claim text"
        "claim text | verdict | evidence"

    Args:
        text: Raw input string

    Returns:
        Tuple of (claim, verdict, evidence) - verdict/evidence may be None
    """
    if "|" in text:
        parts = [p.strip() for p in text.split("|")]
        claim = parts[0]
        verdict = parts[1] if len(parts) > 1 else None
        evidence = parts[2] if len(parts) > 2 else None
        return claim, verdict, evidence
    return text.strip(), None, None
```

### Step 4: Run test to verify it passes

```bash
cd .claude/skills/verify
python -m pytest tests/test_quick_add.py -v
```

Expected: All 4 tests PASS

### Step 5: Modify CLI to support standalone quick-add

Modify `cmd_add` function to handle `--quick-add` without requiring `--add`:

Replace the validation section at the start of `cmd_add` (around line 384):

```python
def cmd_add(args: argparse.Namespace) -> int:
    """Add a verified claim to pending-claims.md for later promotion."""
    from datetime import date as date_module

    # Handle standalone --quick-add with positional input
    if args.quick_add and args.input and not args.claim:
        claim, verdict, evidence = parse_quick_add_input(args.input)
        args.claim = claim
        if verdict:
            args.verdict = verdict
        if evidence:
            args.evidence = evidence

    # Validate required args
    if not args.claim:
        print("Error: --claim is required (or provide claim text with --quick-add)", file=sys.stderr)
        return 1

    # For quick-add, prompt interactively if verdict/evidence missing
    if args.quick_add:
        if not args.verdict:
            try:
                args.verdict = input("Verdict (verified/false/partial/unverified): ").strip() or "unverified"
            except (EOFError, KeyboardInterrupt):
                print("\nCancelled.")
                return 1
        if not args.evidence:
            try:
                args.evidence = input("Evidence: ").strip() or "(pending verification)"
            except (EOFError, KeyboardInterrupt):
                print("\nCancelled.")
                return 1

    if not args.verdict:
        print("Error: --verdict is required", file=sys.stderr)
        return 1
    if not args.evidence:
        print("Error: --evidence is required", file=sys.stderr)
        return 1

    # Rest of function unchanged...
```

Update dispatch in `main()` to handle standalone quick-add:

Find the dispatch section and add before `elif args.input:`:

```python
    elif args.quick_add:
        # Standalone --quick-add mode
        args.add = True  # Enable add mode
        return cmd_add(args)
```

### Step 6: Test the CLI

```bash
cd .claude/skills/verify

# Test interactive quick-add
echo -e "verified\nfrom docs" | python scripts/verify.py --quick-add "test claim for hooks" --dry-run

# Test inline quick-add
python scripts/verify.py --quick-add "test claim | verified | evidence here" --dry-run
```

Expected: Shows inferred section/severity, accepts input, displays dry-run output

### Step 7: Commit

```bash
git add .claude/skills/verify/scripts/verify.py
git add .claude/skills/verify/tests/test_quick_add.py
git commit -m "feat(verify): simplify quick-add CLI

- --quick-add now works standalone without --add
- Supports inline 'claim | verdict | evidence' syntax
- Interactive prompts when verdict/evidence not provided
- Reduces friction for common claim capture workflow"
```

---

## Task 4: Coverage Analysis (`--coverage`)

**Priority:** High | **Effort:** Medium

**Files:**
- Create: `.claude/skills/verify/scripts/coverage_analysis.py`
- Create: `.claude/skills/verify/tests/test_coverage.py`
- Modify: `.claude/skills/verify/scripts/verify.py`

### Step 1: Write the failing test

Create test file:

```python
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


if __name__ == "__main__":
    unittest.main()
```

### Step 2: Run test to verify it fails

```bash
cd .claude/skills/verify
python -m pytest tests/test_coverage.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'coverage_analysis'`

### Step 3: Write the coverage_analysis.py script

Create `.claude/skills/verify/scripts/coverage_analysis.py`:

```python
#!/usr/bin/env python3
"""
Analyze documentation coverage in known-claims.md.

Identifies sections with few or no claims, helping prioritize
verification efforts.

Exit codes:
    0 - Good coverage (all sections meet threshold)
    1 - Input error
    2 - Sparse coverage detected
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from match_claim import parse_known_claims, discover_sections


# Known documentation sections that should have claims
KNOWN_SECTIONS = [
    "Skills",
    "Hooks",
    "Commands",
    "MCP",
    "Agents",
    "Settings",
    "CLI",
    "IDE",
    "Permissions",
    "Memory",
]


def analyze_coverage(
    known_path: Path,
    min_claims: int = 3,
) -> dict:
    """
    Analyze claim coverage across documentation sections.

    Args:
        known_path: Path to known-claims.md
        min_claims: Minimum claims for "adequate" coverage

    Returns:
        Dict with:
            total_claims: int
            sections: dict[str, {count, sparse, source_url}]
            missing_sections: list[str]
            coverage_score: float (0-1)
    """
    if not known_path.exists():
        return {
            "total_claims": 0,
            "sections": {},
            "missing_sections": KNOWN_SECTIONS.copy(),
            "coverage_score": 0.0,
        }

    claims = parse_known_claims(known_path)
    existing_sections = discover_sections(known_path)

    # Count claims per section
    section_counts: dict[str, int] = {}
    for claim in claims:
        section = claim.section
        section_counts[section] = section_counts.get(section, 0) + 1

    # Build section analysis
    sections = {}
    for section in existing_sections:
        count = section_counts.get(section, 0)
        sections[section] = {
            "count": count,
            "sparse": count < min_claims,
            "source_url": None,  # Could extract from file
        }

    # Find missing known sections
    missing = [s for s in KNOWN_SECTIONS if s not in existing_sections]

    # Calculate coverage score
    # Score = (sections with adequate claims) / (total known sections)
    adequate_sections = sum(1 for s in sections.values() if not s["sparse"])
    total_expected = len(KNOWN_SECTIONS)
    coverage_score = adequate_sections / total_expected if total_expected else 0.0

    return {
        "total_claims": len(claims),
        "sections": sections,
        "missing_sections": missing,
        "coverage_score": coverage_score,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze claim coverage")
    parser.add_argument(
        "--known-claims",
        type=Path,
        default=Path(__file__).parent.parent / "references" / "known-claims.md",
        help="Path to known-claims.md",
    )
    parser.add_argument(
        "--min-claims",
        type=int,
        default=3,
        help="Minimum claims for adequate coverage (default: 3)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    args = parser.parse_args()

    if not args.known_claims.exists():
        print(f"Error: {args.known_claims} not found", file=sys.stderr)
        return 1

    result = analyze_coverage(args.known_claims, args.min_claims)

    if args.json:
        import json
        print(json.dumps(result, indent=2))
    else:
        print("Coverage Analysis")
        print("=" * 40)
        print()
        print(f"Total claims: {result['total_claims']}")
        print(f"Coverage score: {result['coverage_score']:.0%}")
        print()

        # Sections with claims
        print(f"Sections (min {args.min_claims} claims for adequate):")
        for section, data in sorted(result["sections"].items(), key=lambda x: -x[1]["count"]):
            status = "⚠️ SPARSE" if data["sparse"] else "✓"
            print(f"  {status} {section}: {data['count']} claims")

        # Missing sections
        if result["missing_sections"]:
            print()
            print("Missing sections (no claims):")
            for section in result["missing_sections"]:
                print(f"  ✗ {section}")

        print()
        if result["coverage_score"] < 0.7:
            print("Action: Add claims for sparse/missing sections")

    return 2 if result["coverage_score"] < 0.7 else 0


if __name__ == "__main__":
    sys.exit(main())
```

### Step 4: Run test to verify it passes

```bash
cd .claude/skills/verify
python -m pytest tests/test_coverage.py -v
```

Expected: All 4 tests PASS

### Step 5: Integrate with verify.py

Add import (after detect_duplicates import):

```python
from coverage_analysis import analyze_coverage, KNOWN_SECTIONS
```

Add handler after `cmd_find_duplicates`:

```python
def cmd_coverage(args: argparse.Namespace) -> int:
    """Analyze documentation coverage."""
    if not KNOWN_CLAIMS_PATH.exists():
        print("No cache file found.")
        return 1

    min_claims = getattr(args, 'min_claims', 3)
    result = analyze_coverage(KNOWN_CLAIMS_PATH, min_claims)

    print("Coverage Analysis")
    print("=" * 40)
    print()
    print(f"Total claims: {result['total_claims']}")
    print(f"Coverage score: {result['coverage_score']:.0%}")
    print()

    # Sections with claims
    print(f"Sections (min {min_claims} claims for adequate):")
    for section, data in sorted(result["sections"].items(), key=lambda x: -x[1]["count"]):
        status = "⚠️ SPARSE" if data["sparse"] else "✓"
        print(f"  {status} {section}: {data['count']} claims")

    # Missing sections
    if result["missing_sections"]:
        print()
        print("Missing sections (no claims):")
        for section in result["missing_sections"]:
            print(f"  ✗ {section}")

    print()
    if result["coverage_score"] < 0.7:
        print("Action: Add claims for sparse/missing sections")
        return 2

    return 0
```

Add CLI flag:

```python
    mode_group.add_argument(
        "--coverage",
        action="store_true",
        help="Analyze documentation coverage",
    )
```

Add min-claims argument:

```python
    parser.add_argument(
        "--min-claims",
        type=int,
        default=3,
        help="Minimum claims for adequate coverage (default: 3)",
    )
```

Add dispatch:

```python
    if args.coverage:
        return cmd_coverage(args)
```

### Step 6: Test the CLI

```bash
cd .claude/skills/verify
python scripts/verify.py --coverage
python scripts/verify.py --coverage --min-claims 5
```

Expected: Coverage report showing sections, counts, and missing areas

### Step 7: Commit

```bash
git add .claude/skills/verify/scripts/coverage_analysis.py
git add .claude/skills/verify/scripts/verify.py
git add .claude/skills/verify/tests/test_coverage.py
git commit -m "feat(verify): add coverage analysis

- New coverage_analysis.py identifies verification blind spots
- --coverage flag shows claims per section with sparse warnings
- Configurable minimum claims threshold (default: 3)
- Reports missing documentation sections
- Coverage score helps track verification completeness"
```

---

## Task 5: Update Documentation

**Priority:** Low | **Effort:** Low

**Files:**
- Modify: `.claude/skills/verify/SKILL.md`
- Modify: `.claude/skills/verify/references/scripts-reference.md`

### Step 1: Update SKILL.md frontmatter

Change version from 3.0.0 to 3.1.0:

```yaml
metadata:
  version: "3.1.0"
```

### Step 2: Add new commands to Quick Start

Add after "Backup and restore" section:

```markdown
**Cache statistics:**
```
python scripts/verify.py --stats

→ Shows claims by verdict, section, and age bucket
```

**Find duplicates:**
```
python scripts/verify.py --find-duplicates

→ Detects similar claims that may need consolidation
```

**Coverage analysis:**
```
python scripts/verify.py --coverage

→ Identifies documentation sections lacking claims
```

**Simplified quick-add:**
```
python scripts/verify.py --quick-add "hooks timeout is 60 seconds"

→ Interactive prompts for verdict/evidence, infers section/severity
```
```

### Step 3: Add to Components table

```markdown
| `scripts/detect_duplicates.py` | Find similar/duplicate claims |
| `scripts/coverage_analysis.py` | Analyze documentation coverage |
```

### Step 4: Add to Scripts Quick Reference

```markdown
| `verify.py` | `python scripts/verify.py --stats` |
| `verify.py` | `python scripts/verify.py --find-duplicates` |
| `verify.py` | `python scripts/verify.py --coverage` |
```

### Step 5: Add changelog entry

```markdown
### v3.1.0
- **Cache statistics**: `--stats` shows comprehensive breakdown by verdict, section, and age
- **Duplicate detection**: `--find-duplicates` identifies similar claims using fuzzy matching
- **Coverage analysis**: `--coverage` finds documentation sections lacking verification
- **Simplified quick-add**: `--quick-add` now works standalone with interactive prompts
- Test coverage expanded with test_stats.py, test_detect_duplicates.py, test_quick_add.py, test_coverage.py
```

### Step 6: Update scripts-reference.md

Add new sections for detect_duplicates.py and coverage_analysis.py with usage examples.

### Step 7: Commit

```bash
git add .claude/skills/verify/SKILL.md
git add .claude/skills/verify/references/scripts-reference.md
git commit -m "docs(verify): update documentation for v3.1.0

- Add --stats, --find-duplicates, --coverage to quick reference
- Document simplified --quick-add workflow
- Add changelog entry for v3.1.0"
```

---

## Final Steps

### Run Full Test Suite

```bash
cd .claude/skills/verify
python -m pytest tests/ -v
```

Expected: All tests pass (62 existing + ~16 new = ~78 total)

### Version Tag

```bash
git tag -a verify-v3.1.0 -m "Verify skill v3.1.0: introspection features"
```

---

## Verification Checklist

After implementation:

- [ ] `python scripts/verify.py --stats` shows statistics
- [ ] `python scripts/verify.py --find-duplicates` detects similar claims
- [ ] `python scripts/verify.py --coverage` shows coverage analysis
- [ ] `python scripts/verify.py --quick-add "test claim"` prompts interactively
- [ ] `python -m pytest tests/ -v` all tests pass
- [ ] SKILL.md shows version 3.1.0
- [ ] scripts-reference.md includes new scripts
