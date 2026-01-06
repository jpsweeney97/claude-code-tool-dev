---
name: verify
description: Verify claims about Claude Code against official Anthropic documentation. Use when fact-checking Claude Code features, behaviors, or configurations.
license: MIT
metadata:
  version: "1.7.0"
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

**Output:** Confidence symbol (✓ ~ ? ✗) + evidence + source URL

---

## Triggers

**Single claim mode:**
- `/verify "..."` - Verify a specific claim
- "Is it true that..." - Natural language verification
- "Does Claude Code support..." - Feature verification
- "fact-check" / "verify claim" - General verification

**Document mode:**
- `/verify /path/to/document.md` - Verify all claims in a document
- `/verify guide.md --verbose` - Aggressive claim extraction
- "verify claims in [file path]" - Natural language

## When to Use

- Before acting on information about Claude Code capabilities
- When documentation seems inconsistent or outdated
- When verifying third-party tutorials or guides
- After "I think..." or "I believe..." statements about Claude Code
- **Document mode:** When auditing a guide, tutorial, or reference doc for accuracy

---

## Document Mode

Verify all verifiable claims in a markdown document. Useful for auditing guides, tutorials, or reference documentation.

### Document Workflow

```
Input: /verify /path/to/document.md
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│ Step D0: Extract Claims                                  │
│ scripts/extract_claims.py scans document for:            │
│ • **Bold:** labeled assertions                           │
│ • Technical values (timeouts, limits, exit codes)        │
│ • Required/optional field statements                     │
│ • Capability assertions (supports X, cannot Y)           │
└─────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│ Step D1: Group by Topic                                  │
│ Claims clustered by detected topic:                      │
│ Hooks, Skills, Commands, MCP, Agents, Settings, CLI     │
└─────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│ Step D2: Cache Lookup                                    │
│ For each claim, run match_claim.py                       │
│ • Match found → use cached verdict                       │
│ • No match → queue for verification                      │
└─────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│ Step D3: Batch Verification                              │
│ Launch parallel claude-code-guide agents by topic        │
│ (e.g., all Hooks claims in one query)                    │
└─────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│ Step D4: Document Report                                 │
│ Generate summary with reliability score                  │
│ List contradicted claims with corrections                │
└─────────────────────────────────────────────────────────┘
```

### Extraction Modes

| Mode | Pattern | Coverage |
|------|---------|----------|
| Conservative (default) | High-confidence technical assertions | Lower recall, fewer false positives |
| Verbose (`--verbose`) | Aggressive pattern matching | Higher recall, more noise |

### Document Report Format

```markdown
## Document Verification Report

**Document:** /path/to/guide.md
**Claims extracted:** 47
**Verified:** 38 (81%)

### Summary by Topic

| Topic | Claims | ✓ | ~ | ? | ✗ |
|-------|--------|---|---|---|---|
| Hooks | 15 | 12 | 1 | 1 | 1 |
| Skills | 8 | 7 | 0 | 1 | 0 |
| MCP | 6 | 5 | 1 | 0 | 0 |

### Contradicted Claims (Corrections Needed)

| Line | Claim | Correct Value |
|------|-------|---------------|
| 142 | "Exit code 1 blocks execution" | Exit code 1 is non-blocking |

### Reliability Score: 87%

Formula: (✓ + 0.5×~) / total
```

## Quick Reference

| Confidence | Symbol | Meaning |
|------------|--------|---------|
| Verified | ✓ | Exact match in official docs with citation |
| Partial | ~ | Concept exists, details may differ |
| Unverified | ? | No official documentation found |
| Contradicted | ✗ | Official docs state otherwise |

## Documentation Clusters

Claims map to documentation sections. Clusters optimize query routing.

| Cluster | Keywords | Primary Source |
|---------|----------|----------------|
| **Skills** | frontmatter, triggers, allowed-tools, SKILL.md | skills documentation |
| **Hooks** | exit codes, events, matchers, timeout | hooks documentation |
| **Commands** | $ARGUMENTS, command discovery | commands documentation |
| **Agents** | subagent_type, Task tool | agents documentation |
| **MCP** | .mcp.json, server configuration | MCP documentation |
| **Settings** | permissions, settings.json | settings documentation |
| **CLI** | flags, environment variables, modes | CLI documentation |

> **Note:** Clusters are heuristics. The claude-code-guide agent searches across all docs regardless of cluster assignment.

## Process

### Step 0: Check Cache and Pending

**0a. Check for pending claims:**

First, check `references/pending-claims.md`. If non-empty:

```
"You have N pending claims awaiting review. Promote to known-claims.md now? [Y/n]"
```

If user confirms, for each pending claim:
1. Add to appropriate section in `known-claims.md`
2. Remove from `pending-claims.md`

**0b. Quick check known claims:**

Use `scripts/match_claim.py` to fuzzy-match against `references/known-claims.md`:

```bash
python scripts/match_claim.py "Skills require a license field"
```

**Script responses (exit codes):**

| Exit Code | Meaning | Action |
|-----------|---------|--------|
| 0 | HIGH confidence (≥0.60) | Return cached verdict immediately |
| 1 | CONFIRM needed (0.40-0.59) | Show candidates, ask user to confirm |
| 10 | No match (<0.40) | Proceed to Step 1 |

**Example flow:**
```
Input: "is license field required"
  ↓
match_claim.py → Score 0.80 (HIGH) → Exit 0
  ↓
Return: ✗ False | license field is required in frontmatter
```

**When to skip to Step 1:**
- Script returns exit code 10 (no match)
- User explicitly requests fresh verification
- Claim requires current documentation (behavioral edge cases)

### Step 1: Extract and Cluster Claims

Parse input, decompose compound claims, and assign clusters.

**Claim types:**
- Feature existence ("Claude Code has X")
- Behavior assertions ("When you do X, Y happens")
- Configuration details ("The field X accepts Y values")
- Limitations ("Claude Code cannot do X")

**Decomposition rules:**

| Claim Type | Example | Action |
|------------|---------|--------|
| **Single-cluster** | "Skills require license field" | Assign to Skills |
| **Compound** | "Skills and hooks support timeout" | Split → "Skills support timeout" + "Hooks support timeout" |
| **Relational** | "Hook exit codes affect skill loading" | Query primary subject (Hooks), flag interaction |

**Example extraction:**

```
Input: "Skills require a license field, hooks only return 0 or 2,
        and skill descriptions are limited to 500 characters"

Claims (clustered):
  Skills: [1] license field required, [3] description limit 500 chars
  Hooks:  [2] only exit codes 0 or 2

Query plan: 2 parallel agents (Skills batch, Hooks single)
```

### Step 2: Query Official Sources

Use `claude-code-guide` agent (Task tool with subagent_type='claude-code-guide').

**Query strategy based on clustering:**

| Scenario | Strategy |
|----------|----------|
| Single cluster, 1 claim | Single focused query |
| Single cluster, 2+ claims | Batched query (shared context) |
| Multiple clusters | Parallel agents (one per cluster) |

**Single/Batched query:**
```
Task prompt: "What does official Claude Code documentation say about
[topic(s)]? Quote relevant documentation if found."
```

**Parallel queries (multiple clusters):**
```
[Launch simultaneously in single message]

Agent 1 (Skills): "What does skills.md say about [skill claims]?"
Agent 2 (Hooks): "What does hooks.md say about [hook claims]?"
Agent 3 (MCP): "What does mcp.md say about [MCP claims]?"
```

**Source priority:**
1. code.claude.com/docs/en/* (primary)
2. platform.claude.com/docs (API/SDK)
3. github.com/anthropics/claude-code (repo)

### Step 3: Assess Confidence

For each claim, determine confidence level:

| Evidence | Confidence |
|----------|------------|
| Direct quote matches claim | ✓ Verified |
| Topic documented but claim differs | ~ Partial |
| No documentation on topic | ? Unverified |
| Documentation contradicts claim | ✗ Contradicted |

### Step 4: Synthesize and Report

Generate a unified response, not per-claim write-ups.

**Report structure by claim count:**

| Claims | Format |
|--------|--------|
| 1 | Detailed single-claim report |
| 2-3 | Summary table + brief synthesis |
| 4+ | Summary table + synthesis + corrections only |

**Template for multi-claim (4+):**

```markdown
## Verification Results

| Claim | Verdict | Source |
|-------|---------|--------|
| Skills use YAML frontmatter | ✓ Verified | skills.md |
| Hooks use YAML frontmatter | ✗ Contradicted | hooks.md |
| MCP uses YAML frontmatter | ✗ Contradicted | mcp.md |

## Synthesis

[Unified answer to the original question, identifying patterns]

Example: "The claim is **partially true**. Content-based extensions
(Skills, Commands, Agents) use YAML frontmatter in Markdown files.
System configuration (Hooks, MCP, Settings) uses JSON files."

## Corrections

[Only for contradicted claims - what the user should know instead]

- **Hooks**: Configured via JSON in settings.json, not YAML
- **MCP**: Uses .mcp.json (JSON format)

## Summary

✓ 3 Verified | ~ 1 Partial | ? 0 Unverified | ✗ 3 Contradicted

**Reliability:** 50% ((3 + 0.5×1) / 7)
```

**Template for single claim:**

```markdown
## Claim: [Statement]

**Verdict:** ✓ Verified / ✗ Contradicted / ~ Partial / ? Unverified

**Evidence:**
> [Direct quote from official docs]

**Source:** [URL]

[If contradicted: **Correction:** accurate information]
```

### Step 5: Capture to Pending

After reporting, automatically append verified/contradicted claims to `references/pending-claims.md` for later review.

**Trigger conditions:**
- Claim has verdict ✓ Verified or ✗ Contradicted (not ~ Partial or ? Unverified)
- Claim is not already in known-claims.md or pending-claims.md
- Evidence came from official documentation

**Action (automatic, no prompt):**

Append to `references/pending-claims.md`:

```markdown
| Default timeout is 60 seconds | ✓ Verified | "60-second execution limit" | hooks | 2026-01-05 |
```

**Confirmation message:**
```
Added 2 claims to pending-claims.md. They'll be reviewed on next /verify.
```

**Skip when:**
- Claim already exists in known-claims.md or pending-claims.md
- Verdict is Partial or Unverified (insufficient confidence for caching)

**Review happens in Step 0a** of the next `/verify` invocation.

## Handling Edge Cases

| Situation | Action |
|-----------|--------|
| Claim is vague | Ask for clarification or state assumption |
| Multiple interpretations | Verify all plausible interpretations |
| Documentation outdated | Note version/date, flag uncertainty |
| Undocumented feature | Report as "? Unverified - not officially documented" |
| Behavioral claim | Note that behavior may change; cite observed patterns if available |

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| Assuming "works in practice" = verified | Undocumented behavior can change | Require official source |
| Partial quote matching | Context matters | Quote sufficient context |
| Trusting non-Anthropic sources | Third parties can be wrong | Verify against official docs |
| Conflating "not documented" with "false" | May be true but undocumented | Report as unverified |

## Example Invocations

```
/verify "Hooks can only return exit code 0 or 2"

/verify "Skills support a metadata field in frontmatter"

/verify "The claude-code-guide agent has access to official documentation"
```

## Verification Criteria

| Criterion | Required |
|-----------|----------|
| All claims addressed | Yes |
| Each claim has confidence symbol | Yes |
| Verified/Contradicted cite sources | Yes |
| Unverified state "not documented" | Yes |
| Synthesis for 2+ claims | Yes |
| Corrections for contradicted | Yes |
| Summary statistics | 4+ claims |

---

## Components

| Component | Purpose |
|-----------|---------|
| `references/known-claims.md` | Permanent cache of verified claims |
| `references/pending-claims.md` | Transient queue awaiting promotion |
| `scripts/extract_claims.py` | Extract claims from documents (doc mode) |
| `scripts/match_claim.py` | Fuzzy matching against known claims |
| `scripts/promote_claims.py` | Promote pending claims to known cache |

## Scripts

### extract_claims.py

Extract verifiable claims from a markdown document. Used in document mode (Step D0).

**Algorithm:**
1. Scan for **bold-label:** patterns (common in docs)
2. Detect technical values (timeouts, exit codes, limits)
3. Identify required/optional/capability assertions
4. Cluster by topic keywords (Hooks, Skills, MCP, etc.)

**Usage:**

```bash
# Conservative extraction (default)
python scripts/extract_claims.py /path/to/guide.md

# Aggressive extraction
python scripts/extract_claims.py guide.md --verbose

# Group by topic
python scripts/extract_claims.py guide.md --by-topic

# Group by document section
python scripts/extract_claims.py guide.md --by-section

# JSON output for pipeline
python scripts/extract_claims.py guide.md --json

# Filter by confidence
python scripts/extract_claims.py guide.md --min-confidence high

# Limit output
python scripts/extract_claims.py guide.md --limit 30
```

**Extraction patterns:**

| Pattern | Example | Confidence |
|---------|---------|------------|
| `**Label:** value` | "**Timeout:** 60s default" | High |
| `exit code N` | "Exit code 2 means blocking" | High |
| `N seconds/tokens` | "default is 60 seconds" | High |
| `required/optional` | "`name` field is required" | High |
| Table rows | Technical spec tables | Medium |

**Exit codes:** 0 = success, 1 = input error, 10 = no claims found

---

### match_claim.py

Fuzzy-match claims against `known-claims.md` using weighted Jaccard similarity with query-focal boosting.

**Algorithm:**
1. Tokenize and normalize (synonyms: "need" → "required", "licence" → "license")
2. Identify focal terms (domain terms in query)
3. Compute weighted Jaccard with 2x boost for matching focal terms
4. Apply penalty for missing focal terms (caps score below 0.60)

**Usage:**

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
```

**Modes:**

| Mode | Behavior |
|------|----------|
| `auto` (default) | ≥0.60 returns, 0.40-0.59 shows candidates, <0.40 no match |
| `confirm` | Always show top 3 candidates |
| `search` | Only match if ≥0.60 (strict) |

**Exit codes:** 0 = high confidence, 1 = confirm needed, 10 = no match

### promote_claims.py

Move claims from `pending-claims.md` to `known-claims.md`, inserting into the appropriate section.

**Usage:**

```bash
# Promote all pending claims (default)
python scripts/promote_claims.py

# Preview without writing
python scripts/promote_claims.py --dry-run

# Confirm each claim interactively
python scripts/promote_claims.py --interactive

# JSON output for scripting
python scripts/promote_claims.py --json
```

**Features:**
- Automatic section detection and insertion
- Duplicate detection (skips existing claims)
- Updates "Last verified" date in known-claims.md
- Clears pending-claims.md after promotion

**Exit codes:** 0 = success, 1 = input error, 10 = no claims to promote

## Extension Points

| Extension | How | Status |
|-----------|-----|--------|
| New documentation source | Add to source priority in Step 2 | Open |
| New claim type | Add to claim types in Step 1 | Open |
| Custom confidence levels | Extend the 4-level taxonomy | Open |
| Fuzzy matching | `scripts/match_claim.py` | **Implemented** |
| Known claims | `references/known-claims.md` | **Implemented** |
| Pending claims | `references/pending-claims.md` | **Implemented** |
| Claim promotion | `scripts/promote_claims.py` | **Implemented** |

---

## Dependencies

- **claude-code-guide agent** - Provides access to official Claude Code documentation
- **Task tool** - Launches verification queries

---

## Changelog

### v1.7.0
- **Document mode**: Verify all claims in a markdown document
  - New trigger: `/verify /path/to/document.md`
  - Batch verification by topic cluster
  - Document-level reliability scoring
- Added `scripts/extract_claims.py` for claim extraction
  - Conservative (default) and verbose extraction modes
  - Topic clustering (Hooks, Skills, MCP, etc.)
  - Bold-label, exit code, and technical value detection
  - `--by-topic`, `--by-section`, `--json` output options
- Updated SKILL.md with Document Mode section and workflow diagram
- Updated Components table with extract_claims.py

### v1.6.0
- **Section normalization**: Common variants automatically mapped (e.g., "Hook" → "Hooks", "Feature" → "Features")
- **Dynamic section discovery**: Both scripts now discover sections from known-claims.md instead of hardcoding
- `match_claim.py`: Removed hardcoded `VALID_SECTIONS`, now discovers from file
- `match_claim.py`: Added `--section` normalization with user feedback
- `promote_claims.py`: Added section normalization during promotion
- `promote_claims.py`: Reports normalized sections in output

### v1.5.1
- **Dynamic section creation**: `promote_claims.py` now creates new sections automatically
- New sections inserted alphabetically before Maintenance section
- Placeholder source URL signals need for human curation

### v1.5.0
- Added `scripts/match_claim.py` for fuzzy claim matching
  - Weighted Jaccard similarity with synonym normalization
  - Query-focal boosting: domain terms in query get 2x weight when matched
  - Missing focal penalty: prevents wrong high-confidence matches
  - Tiered thresholds: ≥0.60 auto-return, 0.40-0.59 confirm, <0.40 no match
  - Exit codes: 0 (high), 1 (confirm), 10 (no match)
- Added `scripts/promote_claims.py` for cache management
  - Automatic section detection and insertion
  - Duplicate detection
  - Dry-run and interactive modes
- Updated Step 0b to use match_claim.py with tiered response
- Added Scripts section with usage documentation

### v1.4.0
- Added `references/pending-claims.md` for transient claim queue
- Step 5 now auto-appends to pending (no prompt, automatic capture)
- Step 0 split into 0a (check pending) and 0b (check known)
- Review/promotion happens at start of next /verify

### v1.3.0
- Added Step 5: Capture to Cache — prompts to add verified claims to known-claims.md
- Rebuilt known-claims.md from official documentation with citations

### v1.2.1
- Removed `scripts/parse_claims.py` — premature optimization that added fragility
- Simplified to Step 0 (known claims) + existing Steps 1-4

### v1.2.0
- Added `references/known-claims.md` for pre-verified common claims
- Added Step 0 (quick check) to process
- Added Components section
- Updated Extension Points with implementation status

### v1.1.0
- Added Quick Start section
- Added metadata block (version, model, timelessness_score)
- Added MIT license
- Clarified clusters are heuristics
- Added extension points
- Added dependencies section
- Streamlined verification criteria

### v1.0.0
- Initial skill creation
- 4-level confidence taxonomy
- Claim clustering and parallel queries
- Output templates for single/multi-claim
