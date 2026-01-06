# Scripts Reference

Complete documentation for verify skill scripts.

## Overview

| Script | Purpose | Key Exit Codes |
|--------|---------|----------------|
| `match_claim.py` | Fuzzy match against known-claims.md | 0=high, 1=confirm, 10=none |
| `promote_claims.py` | Move pending → known-claims.md | 0=success, 10=nothing |
| `extract_claims.py` | Extract claims from documents | 0=success, 10=none |
| `refresh_claims.py` | Find/update stale claims | 0=success |
| `check_version.py` | Track Claude Code versions | 0=match, 2=refresh |
| `batch_verify.py` | Batch verify pending claims | 0=success |

---

## match_claim.py

Fuzzy-match claims against `known-claims.md` using weighted Jaccard similarity with query-focal boosting.

### Algorithm

1. Tokenize and normalize (synonyms: "need" → "required", "licence" → "license")
2. Identify focal terms (domain terms in query)
3. Compute weighted Jaccard with 2x boost for matching focal terms
4. Apply penalty for missing focal terms (caps score below 0.60)

### Usage

```bash
# Single match (default)
python scripts/match_claim.py "Skills require a license"

# Show top N candidates
python scripts/match_claim.py "required field" --top 5

# Filter by section
python scripts/match_claim.py "timeout" --section Hooks

# Debug: show token breakdown
python scripts/match_claim.py "license required" --debug

# JSON output for scripting
python scripts/match_claim.py "exit code" --json

# List sections
python scripts/match_claim.py --list-sections

# Check freshness (show staleness warnings)
python scripts/match_claim.py "timeout" --check-freshness

# Find stale claims needing refresh
python scripts/match_claim.py "*" --top 100 --stale-only

# Custom TTL threshold (60 days)
python scripts/match_claim.py "exit code" --check-freshness --max-age 60
```

### Modes

| Mode | Behavior |
|------|----------|
| `auto` (default) | ≥0.60 returns, 0.40-0.59 shows candidates, <0.40 no match |
| `confirm` | Always show top 3 candidates |
| `search` | Only match if ≥0.60 (strict) |

### Freshness Flags

| Flag | Purpose |
|------|---------|
| `--check-freshness` | Show verification date and staleness warnings |
| `--max-age DAYS` | Custom TTL (default: 90 days) |
| `--stale-only` | Filter to only stale claims (use with --top) |

### Exit Codes

- `0` - High confidence match (≥0.60)
- `1` - Confirm needed (0.40-0.59)
- `10` - No match (<0.40)

---

## promote_claims.py

Move claims from `pending-claims.md` to `known-claims.md`, inserting into the appropriate section.

### Usage

```bash
# Promote all pending claims (default, records version)
python scripts/promote_claims.py

# Preview without writing
python scripts/promote_claims.py --dry-run

# Confirm each claim interactively
python scripts/promote_claims.py --interactive

# Don't record Claude Code version
python scripts/promote_claims.py --no-version

# JSON output for scripting
python scripts/promote_claims.py --json
```

### Features

- Automatic section detection and insertion
- Duplicate detection (skips existing claims)
- Section normalization (e.g., "hook" → "Hooks")
- Dynamic section creation for unknown sections
- Updates "Last verified" date in known-claims.md
- **Version tracking**: Records Claude Code version in verification date (e.g., "2026-01-06 (v2.0.76)")
- Clears pending-claims.md after promotion

### Exit Codes

- `0` - Success (≥1 claim promoted)
- `1` - Input error
- `10` - No claims to promote

---

## refresh_claims.py

Find stale claims and manage the refresh workflow. Supports version-aware staleness checking.

### Usage

```bash
# List all stale claims
python scripts/refresh_claims.py

# Cache health summary with version check
python scripts/refresh_claims.py --version-aware --summary

# Filter by section
python scripts/refresh_claims.py --section Hooks

# Custom TTL (days)
python scripts/refresh_claims.py --max-age 60

# Update verification date for a claim
python scripts/refresh_claims.py --update "Exit code 0 means success"

# Mark all claims as freshly verified
python scripts/refresh_claims.py --update-all

# JSON output
python scripts/refresh_claims.py --json
```

### Version-Aware Mode

When `--version-aware` is specified, the script also checks if Claude Code version has changed:
- Major/minor version change → exit code 2, all claims flagged for review
- Patch version change → no impact on staleness
- Same version → normal time-based staleness check

### Exit Codes

- `0` - Success (or stale claims found)
- `1` - Input error
- `2` - Version changed (major/minor) - all claims need review

---

## check_version.py

Detect Claude Code version changes that may invalidate cached claims.

### Usage

```bash
# Compare current vs stored version
python scripts/check_version.py

# Update stored version to current
python scripts/check_version.py --update

# JSON output
python scripts/check_version.py --json
```

### Version Change Types

| Type | Example | Impact |
|------|---------|--------|
| none | Same version | No action |
| patch | 2.0.76 → 2.0.77 | Unlikely to affect claims |
| minor | 2.0.76 → 2.1.0 | May affect some claims |
| major | 2.0.76 → 3.0.0 | Likely affects many claims |
| downgrade | Version went backwards | Unusual, investigate |

### Exit Codes

- `0` - Version matches or patch-only change
- `1` - Input error
- `2` - Major/minor version change (refresh recommended)

---

## batch_verify.py

Verify all pending claims in batch, using parallel agents for efficiency.

### Usage

```bash
# Verify all pending claims
python scripts/batch_verify.py

# Verify specific sections only
python scripts/batch_verify.py --section Hooks

# Dry run (show what would be verified)
python scripts/batch_verify.py --dry-run

# Auto-promote verified claims
python scripts/batch_verify.py --auto-promote

# JSON output
python scripts/batch_verify.py --json
```

### Features

- Groups claims by topic for efficient batching
- Uses parallel claude-code-guide agents
- Updates verdicts in pending-claims.md
- Optional auto-promotion to known-claims.md

### Exit Codes

- `0` - Success (claims verified)
- `1` - Input error
- `10` - No pending claims

---

## verify-health-check.py (Hook)

SessionStart hook that checks cache health and warns when issues are detected.

### Purpose

Runs at session start to alert you if:
- Claude Code version changed since last verification (major/minor)
- More than 20% of claims are stale (>90 days old)

### Integration

Add to settings.json hooks array:
```json
{
  "event": "SessionStart",
  "type": "command",
  "command": "python ~/.claude/skills/verify/hooks/verify-health-check.py"
}
```

### Behavior

- **Silent when healthy**: No output if cache is fresh and version matches
- **Warns when unhealthy**: Emits warnings to stdout (injected into session context)
- **Non-blocking**: Always exits 0 to avoid blocking session start

### Output Example

```
[Verify Skill Health Check]
⚠️ Claude Code minor version change - verify cache may be outdated
⚠️ Verify cache: 18/76 claims (24%) are stale (>90d)
Run: python scripts/refresh_claims.py --version-aware --summary
```

---

## Common Patterns

### Result Dataclass

All scripts use a consistent result pattern:

```python
@dataclass
class OperationResult:
    """Result of script operation."""
    success: bool
    items_processed: int = 0
    items_skipped: int = 0
    errors: list[str] = field(default_factory=list)
```

### Exit Code Convention

| Code | Meaning |
|------|---------|
| 0 | Success / operation completed |
| 1 | Input error (file not found, invalid args) |
| 2 | Special signal (version change detected) |
| 10 | Nothing to do (no matches, no claims) |

### JSON Output

All scripts support `--json` for pipeline integration:

```bash
# Chain scripts together
python scripts/match_claim.py "timeout" --json | jq '.confidence'
```
