# Document Mode

Verify all verifiable claims in a markdown document. Useful for auditing guides, tutorials, or reference documentation.

## Workflow

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

## Extraction Modes

| Mode | Pattern | Coverage |
|------|---------|----------|
| Conservative (default) | High-confidence technical assertions | Lower recall, fewer false positives |
| Verbose (`--verbose`) | Aggressive pattern matching | Higher recall, more noise |

## Report Format

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

## Triggers

- `/verify /path/to/document.md` - Verify all claims in a document
- `/verify guide.md --verbose` - Aggressive claim extraction
- "verify claims in [file path]" - Natural language

## When to Use

- Auditing a guide or tutorial for accuracy
- Reviewing third-party documentation
- Pre-publication validation of technical content
- Identifying outdated information in existing docs

## extract_claims.py

Extract verifiable claims from a markdown document. Used in document mode (Step D0).

### Algorithm

1. Scan for **bold-label:** patterns (common in docs)
2. Detect technical values (timeouts, exit codes, limits)
3. Identify required/optional/capability assertions
4. Cluster by topic keywords (Hooks, Skills, MCP, etc.)

### Usage

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

### Extraction Patterns

| Pattern | Example | Confidence |
|---------|---------|------------|
| `**Label:** value` | "**Timeout:** 60s default" | High |
| `exit code N` | "Exit code 2 means blocking" | High |
| `N seconds/tokens` | "default is 60 seconds" | High |
| `required/optional` | "`name` field is required" | High |
| Table rows | Technical spec tables | Medium |

### Exit Codes

- `0` - Success (claims extracted)
- `1` - Input error (file not found)
- `10` - No claims found
