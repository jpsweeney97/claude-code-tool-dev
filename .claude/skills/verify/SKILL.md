---
name: verify
description: Verify claims about Claude Code against official Anthropic documentation. Use when fact-checking Claude Code features, behaviors, or configurations.
license: MIT
metadata:
  version: "3.1.0"
  model: claude-sonnet-4-20250514
  timelessness_score: 8
---

# Verify Claude Code Claims

Fact-check claims about Claude Code against official documentation.

---

## Quick Start

**Single claim:**
```
/verify "Skills require a license field in frontmatter"

→ Extracts claim → Queries claude-code-guide → Returns verdict with citation
```

**Document mode:**
```
/verify /path/to/document.md

→ Extracts claims → Batches by topic → Parallel verification → Document report
```

**Capture mode:**
```
/verify --capture

→ Scans conversation → Detects Claude Code claims → Queues to pending
```

**Batch verify:**
```
/verify --batch

→ Verifies all pending claims → Updates verdicts → Optional auto-promote
```

**Interactive batch:**
```
python scripts/batch_verify.py --interactive

→ Per-claim confirm/skip/edit/quit → Human oversight for batch operations
```

**Quick-add mode:**
```
python scripts/verify.py --quick-add "claim text"

→ Smart section/severity inference → Adds to pending with minimal input
```

**Validate source URLs:**
```
python scripts/verify.py --validate-urls

→ Checks documentation URLs → Reports broken links
```

**Backup and restore:**
```
python scripts/backup_cache.py backup    # Create backup
python scripts/backup_cache.py list      # List backups
python scripts/backup_cache.py restore   # Restore latest
```

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

**Add claim (after verification):**
```
python scripts/verify.py --add --claim "Exit code 2 blocks" --verdict verified \
  --evidence "Exit code 2: Blocking error" --add-section Hooks \
  --severity CRITICAL --source "https://code.claude.com/docs/en/hooks.md"

→ Appends to pending-claims.md with severity and source URL
```

**Output:** Confidence symbol (✓ ~ ? ✗) + severity + evidence + source URL

---

## Triggers

| Mode | Triggers |
|------|----------|
| **Single** | `/verify "..."`, "Is it true that...", "Does Claude Code support..." |
| **Document** | `/verify /path/to/file.md`, "verify claims in [file]" |
| **Capture** | `/verify --capture`, "capture claims from this conversation" |
| **Batch** | `/verify --batch`, "verify pending claims" |
| **Add** | `--add --claim "..." --verdict ... --evidence ... --add-section ...` |

## When to Use

- Before acting on information about Claude Code capabilities
- When documentation seems inconsistent or outdated
- When verifying third-party tutorials or guides
- After "I think..." or "I believe..." statements about Claude Code
- **Document mode:** When auditing a guide for accuracy
- **Capture mode:** At end of session after discussing Claude Code
- **Batch mode:** To process accumulated pending claims

---

## Quick Reference

| Confidence | Symbol | Meaning |
|------------|--------|---------|
| Verified | ✓ | Exact match in official docs with citation |
| Partial | ~ | Concept exists, details may differ |
| Unverified | ? | No official documentation found |
| Contradicted | ✗ | Official docs state otherwise |

## Claim Severity

Claims can be tagged with severity to prioritize verification:

| Severity | Meaning | Example |
|----------|---------|---------|
| **CRITICAL** | Breaks workflows if wrong | Exit code handling, required fields |
| **HIGH** | Behavior change impact | Default values, feature capabilities |
| **LOW** | Guidance/best practice | Recommended patterns, style |

**Usage:** `--severity CRITICAL` when adding claims
**Display:** `[CRITICAL]` shown after verdict in output

## Per-Claim Source URLs

Claims can include direct links to source documentation:

**Format:** `(https://code.claude.com/docs/en/hooks.md#exit-codes)` appended to evidence
**Display:** `Source:` line shown in output when present

This improves traceability and speeds up re-verification.

## Cache Freshness

Claims track verification dates with 90-day TTL. Stale claims are flagged for re-verification.

**Version-aware staleness:** When Claude Code version changes (major/minor), all claims are flagged for review regardless of age.

| Indicator | Meaning |
|-----------|---------|
| (no marker) | Fresh - verified within TTL |
| ⚠️ STALE | Verified date exceeds TTL |
| ⚠️ VERSION | Claude Code version changed since verification |

```bash
# Find stale claims (time-based)
python scripts/match_claim.py "*" --top 100 --stale-only

# View cache health with version check
python scripts/refresh_claims.py --version-aware --summary

# Refresh a claim after re-verification
python scripts/refresh_claims.py --update "claim text"
```

## Documentation Clusters

Claims map to documentation sections for efficient query batching.

| Cluster | Keywords | Source |
|---------|----------|--------|
| **Skills** | frontmatter, triggers, allowed-tools | skills.md |
| **Hooks** | exit codes, events, matchers | hooks.md |
| **Commands** | $ARGUMENTS, slash commands | slash-commands.md |
| **Agents** | subagent_type, Task tool | agents.md |
| **MCP** | .mcp.json, server configuration | mcp.md |
| **Settings** | permissions, settings.json | interactive-mode.md |
| **CLI** | flags, environment variables | cli.md |

---

## Core Process

### Step 0: Define Scope

Before verification, determine if the claim is in scope:

| In Scope | Out of Scope |
|----------|--------------|
| Claude Code CLI features | General Claude model capabilities |
| Configuration (settings.json, .mcp.json) | API pricing or quotas |
| Hooks, skills, commands, agents | Anthropic Console features |
| MCP servers | Claude.ai web interface |
| Permissions system | Third-party integrations |

**Boundary claims** (handle carefully):
- "Claude Code can..." → In scope (CLI behavior)
- "Claude can..." → Likely out of scope (model capability)
- "The model in Claude Code..." → In scope only if about CLI-specific behavior

**Action:** If out of scope, respond: "This claim is about [X], not Claude Code. The verify skill covers Claude Code CLI features."

### Step 1: Check Cache

**1a. Check pending claims:**

If `pending-claims.md` has entries:
```
"You have N pending claims awaiting review. Promote now? [Y/n]"
```

**1b. Check known claims:**

```bash
python scripts/match_claim.py "Skills require a license field"
```

| Exit Code | Meaning | Action |
|-----------|---------|--------|
| 0 | HIGH (≥0.60) | Return cached verdict |
| 1 | CONFIRM (0.40-0.59) | Show candidates |
| 10 | No match (<0.40) | Proceed to Step 2 |

### Step 2: Extract and Cluster

Parse input, decompose compound claims, assign clusters:

| Claim Type | Action |
|------------|--------|
| Single-cluster | Assign to cluster (e.g., Skills) |
| Compound | Split ("Skills and hooks...") |
| Relational | Query primary subject |

### Step 3: Query Official Sources

Use `claude-code-guide` agent via Task tool:

| Scenario | Strategy |
|----------|----------|
| Single cluster, 1 claim | Single focused query |
| Single cluster, 2+ claims | Batched query |
| Multiple clusters | Parallel agents |

**Source priority:** code.claude.com/docs → platform.claude.com → github.com/anthropics

### Step 4: Assess Confidence

| Evidence | Confidence |
|----------|------------|
| Direct quote matches | ✓ Verified |
| Topic documented, details differ | ~ Partial |
| No documentation | ? Unverified |
| Documentation contradicts | ✗ Contradicted |

### Step 5: Disconfirmation

Before finalizing, actively search for contradicting evidence:

| Check | What to Look For |
|-------|------------------|
| **Exceptions** | "except when...", "unless...", "only if..." |
| **Version notes** | "as of v2.0...", "deprecated in...", "changed in..." |
| **Caveats** | "Note:", "Warning:", "Important:" |
| **Contradictions** | Same topic, different answer elsewhere |
| **Scope limits** | Feature exists but with restrictions |

**Required action:** Document disconfirmation search:
```
Disconfirmation search: Checked [sources]. Found: [evidence or "no contradicting evidence"]
```

**Confidence adjustments:**

| Finding | Adjustment |
|---------|------------|
| Exception applies to claim | ✓ → ~ Partial |
| Deprecated/changed feature | ✓ → ~ with version note |
| Contradicting documentation | ✓ → ✗ Contradicted |
| No contradicting evidence found | Confidence unchanged |

**Why this matters:** Confirmation bias leads to finding only supporting evidence. Disconfirmation actively seeks what would prove the claim wrong.

### Step 6: Report

| Claims | Format |
|--------|--------|
| 1 | Detailed single-claim report |
| 2-3 | Summary table + synthesis |
| 4+ | Table + synthesis + corrections only |

### Step 7: Auto-Capture

Automatically append verified/contradicted claims to `pending-claims.md`:
- Verdict ✓ or ✗ (not ~ or ?)
- Not already in cache
- Evidence from official docs

---

## Edge Cases

| Situation | Action |
|-----------|--------|
| Vague claim | Ask for clarification |
| Multiple interpretations | Verify all plausible ones |
| Documentation outdated | Note version, flag uncertainty |
| Undocumented feature | Report as "? Unverified" |
| Behavioral claim | Note behavior may change |

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| "Works in practice" = verified | Undocumented behavior changes | Require official source |
| Partial quote matching | Context matters | Quote sufficient context |
| Trusting non-Anthropic sources | Can be wrong | Verify against official docs |
| "Not documented" = false | May be true but undocumented | Report as unverified |

---

## Components

| Component | Purpose |
|-----------|---------|
| `references/known-claims.md` | Permanent cache of verified claims |
| `references/pending-claims.md` | Transient queue awaiting promotion |
| `references/document-mode.md` | Document verification workflow |
| `references/capture-mode.md` | Conversation capture workflow |
| `references/scripts-reference.md` | Complete script documentation |
| `scripts/verify.py` | **Unified CLI** - single entry point for all operations |
| `scripts/match_claim.py` | Fuzzy matching against cache |
| `scripts/promote_claims.py` | Move pending → known (with version tracking) |
| `scripts/extract_claims.py` | Extract claims from documents |
| `scripts/refresh_claims.py` | Find/update stale claims (version-aware) |
| `scripts/check_version.py` | Track Claude Code versions |
| `scripts/batch_verify.py` | Batch verification |
| `hooks/verify-capture-reminder.py` | Session-end reminder |
| `hooks/verify-health-check.py` | SessionStart health warning |
| `scripts/validate_sources.py` | Validate documentation source URLs |
| `scripts/backup_cache.py` | Backup and restore cache |
| `scripts/detect_duplicates.py` | Find similar/duplicate claims |
| `scripts/coverage_analysis.py` | Analyze documentation coverage |
| `tests/` | Unit tests for scripts |

## Scripts Quick Reference

| Script | Common Usage |
|--------|--------------|
| `verify.py` | `python scripts/verify.py --quick "claim"` ← **Start here** |
| `verify.py` | `python scripts/verify.py --health` |
| `verify.py` | `python scripts/verify.py --refresh` |
| `verify.py` | `python scripts/verify.py --promote --dry-run` |
| `verify.py` | `python scripts/verify.py --add --claim "..." --verdict ... --evidence ... --add-section ...` |
| `match_claim.py` | `python scripts/match_claim.py "claim" --top 5` (advanced) |
| `refresh_claims.py` | `python scripts/refresh_claims.py --version-aware --summary` |
| `batch_verify.py` | `python scripts/batch_verify.py --auto-promote` |
| `batch_verify.py` | `python scripts/batch_verify.py --interactive` |
| `verify.py` | `python scripts/verify.py --quick-add "claim"` |
| `verify.py` | `python scripts/verify.py --validate-urls` |
| `verify.py` | `python scripts/verify.py --backup` |
| `verify.py` | `python scripts/verify.py --restore` |
| `backup_cache.py` | `python scripts/backup_cache.py list --diff` |
| `verify.py` | `python scripts/verify.py --stats` |
| `verify.py` | `python scripts/verify.py --find-duplicates` |
| `verify.py` | `python scripts/verify.py --coverage` |

See `references/scripts-reference.md` for full documentation.

---

## Extension Points

| Extension | How | Status |
|-----------|-----|--------|
| New documentation source | Add to source priority in Step 2 | Open |
| New claim type | Add to claim types in Step 1 | Open |
| Fuzzy matching | `scripts/match_claim.py` | ✓ |
| Cache management | `scripts/promote_claims.py` | ✓ |
| Stale claim refresh | `scripts/refresh_claims.py` | ✓ |
| Version tracking | `scripts/check_version.py` | ✓ |
| Version-aware staleness | `--version-aware` flag | ✓ |
| Document mode | `references/document-mode.md` | ✓ |
| Capture mode | `references/capture-mode.md` | ✓ |
| Batch verification | `scripts/batch_verify.py` | ✓ |
| Health check hook | `hooks/verify-health-check.py` | ✓ |

---

## Dependencies

- **claude-code-guide agent** - Provides access to official Claude Code documentation
- **Task tool** - Launches verification queries

---

## Changelog

### v3.1.0
- **Cache statistics**: `--stats` shows comprehensive breakdown by verdict, section, and age
- **Duplicate detection**: `--find-duplicates` identifies similar claims using fuzzy matching
- **Coverage analysis**: `--coverage` finds documentation sections lacking verification
- **Simplified quick-add**: `--quick-add` now works standalone with interactive prompts
- Test coverage expanded with test_stats.py, test_detect_duplicates.py, test_quick_add.py, test_coverage.py

### v3.0.0
- **Source URL validation**: New `validate_sources.py` detects broken documentation links
  - Rate limiting prevents server blocking
  - `--validate-urls` flag in unified CLI
- **Cache backup/restore**: Automatic backups before promotion, manual control via `backup_cache.py`
  - Rolling backups (keeps last 5)
  - `--backup`, `--restore`, `--list-backups` flags
- **Interactive batch mode**: `batch_verify.py --interactive` for human oversight
  - Per-claim confirm/skip/edit/quit
- **Quick-add mode**: `verify.py --quick-add` with smart section/severity inference
- **Test coverage**: Unit tests for _common.py, match_claim.py, validate_sources.py, backup_cache.py
- Timelessness score increased from 7 to 8 (added resilience, not just features)

### v2.6.1
- **Fix**: Consistent severity display - severity now always appears next to verdict, not between status markers
- **Fix**: Adjusted timelessness score to 7 (was 9) - reflects schema constraints on extensibility
- Note: Core concept remains highly timeless; score reflects implementation architecture limitations

### v2.6.0
- **Auto-add claims**: New `--add` command to add verified claims directly to pending-claims.md
  - `python scripts/verify.py --add --claim "..." --verdict ... --evidence ... --add-section ...`
  - Supports optional `--severity` (CRITICAL, HIGH, LOW) and `--source` URL
  - Duplicate detection with `--force` override
- **Claim severity classification**: Claims can be tagged with severity level
  - CRITICAL: Breaks workflows if wrong (exit codes, required fields)
  - HIGH: Behavior change impact
  - LOW: Guidance/best practice
  - Displayed as `[CRITICAL]` after verdict in output
- **Per-claim source URLs**: Claims can include direct documentation links
  - Appended to evidence: `"evidence text (https://...)"`
  - Displayed as `Source:` line in output
  - Improves traceability and re-verification speed
- **Parsing improvements**: `parse_severity()` and `parse_source_url()` functions extract embedded metadata

### v2.5.1
- **Bug fix**: Fixed section insertion offset bug in `promote_claims.py` that could corrupt file structure
- **Bug fix**: Fixed case-sensitive section lookup causing duplicate detection failures
- **Safety**: Added atomic write pattern to all file-modifying scripts (prevents data corruption on interrupted writes)
- **Refactor**: Consolidated `Version` class into `_common.py` (was duplicated in 3 files)
- **Refactor**: Canonical import source for `DEFAULT_MAX_AGE_DAYS` from `_common.py`
- **Improvement**: Added verbose mode to `get_claude_code_version()` for debugging

### v2.5.0
- **Scope Definition (Step 0)**: New step clarifies what claims are in/out of scope
  - Explicit in-scope: Claude Code CLI features, configuration, hooks, skills, etc.
  - Explicit out-of-scope: General Claude model capabilities, API pricing, Console features
  - Boundary claim guidance for ambiguous "Claude can..." vs "Claude Code can..." statements
- **Disconfirmation (Step 5)**: New step actively searches for contradicting evidence
  - Checks for exceptions, version notes, caveats, contradictions, scope limits
  - Required documentation of disconfirmation search in verdict
  - Confidence adjustment rules when contradicting evidence found
- Core Process now has 8 steps (0-7) vs previous 6 (0-5)

### v2.4.0
- **Unified CLI**: Added `scripts/verify.py` as single entry point for all operations
  - `verify.py --quick "claim"` - fast cache-only check
  - `verify.py --health` - cache health summary
  - `verify.py --refresh` - list stale claims
  - `verify.py --promote` - promote pending claims
  - `verify.py --sections` - list available sections
- Reduces friction: one script to remember instead of five

### v2.3.0
- **Bug fix**: Date parsing now handles version-tagged dates (e.g., `"2026-01-05 (v2.0.76)"`)
  - Added `parse_verified_date()` utility to `match_claim.py`, `refresh_claims.py`, and health hook
  - Fixes `ValueError` when checking freshness of claims promoted with `--version` tracking
- Scripts now correctly report staleness for both plain and version-tagged verification dates

### v2.2.0
- **Version-aware staleness**: `refresh_claims.py --version-aware` flags all claims when Claude Code version changes
- **SessionStart health hook**: `hooks/verify-health-check.py` warns when cache is unhealthy at session start
- **Version-per-claim tracking**: `promote_claims.py` records Claude Code version in verification date (e.g., "2026-01-06 (v2.0.76)")
- Exit code 2 from refresh_claims.py signals version change requiring review

### v2.1.0
- **Structure refactor**: Reduced SKILL.md from 1030→490 lines
  - Moved Document Mode workflow to `references/document-mode.md`
  - Moved Capture Mode workflow to `references/capture-mode.md`
  - Moved script details to `references/scripts-reference.md`
- **Batch verification**: Added `scripts/batch_verify.py` for processing pending claims
- **Extended SECTION_SOURCES**: Added Memory, IDE, Permissions, Plugins mappings
- Added `/verify --batch` trigger

### v2.0.0
- **Capture mode**: Automatically detect and queue Claude Code claims from conversations
- **Session-end hook**: `verify-capture-reminder.py` reminds to run capture

### v1.9.0
- **Stale claim management**: Added `scripts/refresh_claims.py`
- **Version tracking**: Added `scripts/check_version.py`
- **Source URL inference**: `promote_claims.py` infers documentation URLs

### v1.8.0
- **Cache freshness**: Claims track verification dates with 90-day TTL

### v1.7.0
- **Document mode**: Verify all claims in a markdown document
- Added `scripts/extract_claims.py` for claim extraction

### v1.6.0
- **Section normalization**: Common variants mapped automatically
- **Dynamic section discovery**: Both scripts discover sections from file

### v1.5.0
- Added `scripts/match_claim.py` for fuzzy claim matching
- Added `scripts/promote_claims.py` for cache management

### v1.4.0
- Added `references/pending-claims.md` for transient claim queue
- Auto-capture to pending on verification

### v1.0.0-v1.3.0
- Initial skill creation through Step 5 capture-to-cache
