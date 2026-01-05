# Synthesis Guidance

How to merge agent findings into a coherent deliverable.

---

## Key Metrics for Cross-Validation

Before synthesizing, extract these metrics from each agent to detect conflicts:

### Standard Metrics

All agents should report counts where applicable:

| Metric | Inventory | Patterns | Documentation | Gaps |
|--------|-----------|----------|---------------|------|
| Primary components (files, scripts, etc.) | Required | Optional | Optional | Optional |
| Secondary components (tests, configs) | Required | - | - | Required |
| Categories/types | Required | - | Required | - |
| Quality issues found | - | Required | - | Required |

### Conflict Detection

1. Compare counts across agents
2. Flag any discrepancy > 0
3. Investigate each discrepancy before proceeding

**Example conflict:**
```
Inventory: 9 categories
Documentation: 10 categories in user-facing docs
→ Investigate: grep for missing category in authoritative source
```

---

## Synthesis Process

### Step 1: Extract Key Metrics

Pull counts from each agent report. Create comparison table.

### Step 2: Identify Conflicts

Any metric where agents disagree triggers investigation:
- Read the relevant files directly
- Determine which finding is correct
- Document resolution in Conflict Log

### Step 3: Merge Findings

Combine non-conflicting findings by category:
- Architecture/Structure (from Inventory + Patterns)
- Quality Assessment (from Patterns + Gaps)
- Documentation Accuracy (from Documentation)
- Opportunities (from Gaps, ranked by impact)

### Step 4: Write Deliverable

Apply writing principles below. Fill every section of the deliverable template.

---

## Writing Principles for Synthesis

Adapted from Strunk's *Elements of Style*. These rules produce clear, credible deliverables.

### Use Active Voice

The active voice is direct and identifies the actor.

| Passive (avoid) | Active (prefer) |
|-----------------|-----------------|
| "31 scripts were found in the repository" | "The repository contains 31 scripts" |
| "It was determined that tests are missing" | "The Gaps agent found missing tests" |
| "The category inconsistency was discovered" | "Cross-validation revealed a category inconsistency" |

**Exception:** Use passive when the actor is unknown or irrelevant: "The file was last modified in 2023."

### Put Statements in Positive Form

State what is, not what isn't. Positive statements are stronger.

| Negative (avoid) | Positive (prefer) |
|------------------|-------------------|
| "Tests don't cover 71% of scripts" | "Tests cover 29% of scripts" |
| "The documentation isn't complete" | "The documentation omits 7 columns" |
| "No rate limiting was found" | "Rate limiting is absent" |

**Exception:** Negative findings are valuable when stating what was looked for but not found: "Searched for CLAUDE.md at root; not present."

### Use Definite, Specific, Concrete Language

Vague language undermines credibility. Specific claims are verifiable.

| Vague (avoid) | Specific (prefer) |
|---------------|-------------------|
| "Several scripts lack tests" | "24 of 31 scripts lack tests" |
| "A large file" | "validate_links.py (1,068 lines)" |
| "Recently updated" | "Last modified 2025-12-25" |
| "Some issues were found" | "4 silent exception handlers found" |

**Rule:** If you can add a number, file path, or date, add it.

### Omit Needless Words

Every word should serve a purpose. Cut filler.

| Wordy (avoid) | Concise (prefer) |
|---------------|------------------|
| "It is important to note that" | (delete) |
| "In order to understand" | "To understand" |
| "The fact that tests are missing" | "Missing tests" |
| "There are 31 scripts that exist" | "31 scripts exist" |
| "Due to the fact that" | "Because" |

**Common filler to cut:**
- "It should be noted that"
- "Basically"
- "In terms of"
- "As a matter of fact"
- "For all intents and purposes"

### Keep Related Words Together

Don't separate subject from verb, or verb from object, with parentheticals.

| Separated (avoid) | Together (prefer) |
|-------------------|-------------------|
| "The script, which handles validation and was written last year, fails silently" | "The validation script fails silently" |
| "Tests for the two largest scripts—validate_links.py and submit_resource.py—are missing" | "The two largest scripts (validate_links.py, submit_resource.py) lack tests" |

### Place Emphatic Words at End

The end of a sentence carries emphasis. Put the key finding there.

| Weak ending | Strong ending |
|-------------|---------------|
| "Test coverage is a problem at 29%" | "Test coverage stands at 29%" |
| "Missing from categories.yaml is 'Output Styles'" | "'Output Styles' is missing from categories.yaml" |
| "In the scripts directory, there is dead code" | "The scripts directory contains dead code" |

**For findings:** End with the fact, not the source.
- Weak: "According to the Gaps agent, tests are missing"
- Strong: "24 scripts have no tests"

---

## Synthesis Checklist

Before finalizing the deliverable:

- [ ] All key metrics extracted and compared
- [ ] All conflicts investigated and resolved
- [ ] Conflict resolution log complete
- [ ] Every finding cites evidence (file:line)
- [ ] Active voice used throughout
- [ ] Statements in positive form (except negative findings)
- [ ] Specific numbers, paths, dates (no vague language)
- [ ] Needless words cut
- [ ] Key findings at sentence ends
- [ ] Coverage matrix complete (no `[ ]` or `[?]`)
- [ ] Opportunities ranked by impact

---

## Common Synthesis Errors

| Error | Example | Fix |
|-------|---------|-----|
| **Unsupported claim** | "The architecture is clean" | Add evidence: "All scripts import via category_utils.py singleton" |
| **Passive findings** | "Issues were identified" | Name the agent: "The Gaps agent found 4 issues" |
| **Vague quantities** | "Many scripts lack tests" | Count: "24 of 31 scripts lack tests" |
| **Buried finding** | "It should be noted that there's a category missing" | Lead with fact: "categories.yaml omits 'Output Styles'" |
| **Conflict ignored** | Agent A says 9, Agent B says 10, report says 9 | Investigate and document resolution |

---

## Example: Before and After

### Before (Weak)

> It was found that there are some issues with the test coverage in the repository. Several scripts don't have tests, and it should be noted that the largest scripts in particular are not covered. Documentation accuracy is generally okay but there are some problems.

### After (Strong)

> Test coverage stands at 29% (9 test files for 31 scripts). The two largest scripts—validate_links.py (1,068 lines) and submit_resource.py (1,607 lines)—have no tests. Documentation is mostly accurate; the main issue is referencing a non-existent file (submit-resource.yml instead of recommend-resource.yml).

**Changes made:**
- Passive → active ("It was found" → direct statement)
- Vague → specific ("some issues" → "29%", "several" → "9 of 31")
- Added file paths and line counts
- Cut filler ("it should be noted")
- Positive form ("don't have" → "have no")
