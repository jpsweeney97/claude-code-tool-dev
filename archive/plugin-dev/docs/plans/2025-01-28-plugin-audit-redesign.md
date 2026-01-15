# Plugin Audit System Redesign

**Date:** 2025-01-28
**Status:** Design Complete, Pending Implementation
**Author:** Claude + JP

## Problem Statement

The current plugin-audit system produces false positives due to three root causes:

1. **Unverified rules** — Scripts encode assumptions not verified against official Claude Code documentation (e.g., assuming `name` field is required for commands when it's optional)

2. **Missing context analysis** — No mechanism to distinguish teaching examples from real file references, or security blocks from vulnerabilities

3. **Syntactic tools for semantic problems** — Pattern matching cannot understand intent; it can find `/etc/` but cannot determine if the code is blocking access (good) or accessing files (bad)

### False Positives Observed

| Issue | Root Cause | Impact |
|-------|-----------|--------|
| Commands flagged for missing `name` field | Rule not verified against docs | 3 false CRITICALs |
| Example paths flagged as missing files | No example detection | 18 false WARNINGs |
| Deny-block paths flagged as vulnerabilities | No security context analysis | 1 false CRITICAL |

## Design Goals

1. **Eliminate false positives** through verified rules and context analysis
2. **Maintain rigor** with traceable rules and confidence scoring
3. **Keep it simple** — Claude + spec + scripts, not a parallel Python codebase
4. **Enable testing** — Design supports TDD methodology for skill validation
5. **Support CI** — Deterministic checks can gate PRs; semantic checks are advisory

## Architecture: Five-Layer Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         AUDIT PIPELINE                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Layer 1        Layer 2         Layer 3        Layer 4      Layer 5     │
│  ────────       ────────        ────────       ────────     ────────    │
│  Syntax    ──▶  Structure  ──▶  Context   ──▶  Quality ──▶ Cross-      │
│  (Scripts)      (Spec-driven)   (Filter)       (Optional)   Component   │
│                                                                          │
│  "Valid         "Follows        "Real issue    "Good        "Consistent │
│   JSON?"         rules?"         or false       content?"    overall?"   │
│                                  positive?"                              │
└─────────────────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

| Layer | Question | Deterministic? | Implementation |
|-------|----------|----------------|----------------|
| 1. Syntax | Is JSON/YAML valid? | Yes | `jq`, `yq` via bash script |
| 2. Structure | Does it follow the rules? | Yes (given spec) | Claude reads spec, applies rules |
| 3. Context | Is this a real issue? | Mostly (heuristics + LLM fallback) | Claude analyzes context |
| 4. Quality | Is content good? | No | Claude assesses (optional, `--deep`) |
| 5. Cross-Component | Does everything fit together? | Yes | Claude checks consistency |

### Why This Separation?

Each layer answers a fundamentally different question:

- **Layer 2 asks:** "Does this match the rule?"
- **Layer 3 asks:** "Should the rule apply here?"

Separating them enables:
- Testing rule application independently from context detection
- Explicit visibility into what was filtered and why
- Clean LLM integration point (Layer 3 only)

## Specification Format

The specification is the "constitution" — all rules with full provenance.

### Structure

```yaml
meta:
  version: "1.0.0"
  claude_code_version: ">=1.0.0"
  last_verified: "2025-01-28"

component_types:
  command:
    discovery:
      pattern: "commands/**/*.md"

    frontmatter:
      fields:
        name:
          required: false
          deprecated: true
          source:
            doc_id: slash-commands-docs
            section: "Plugin Commands"
            url: "https://docs.anthropic.com/..."
          evidence:
            quote: "The command name is derived from the filename"
            retrieved: "2025-01-28"
          rule_derivation: |
            Docs state command names come from filenames.
            Therefore, name field is not required.

        description:
          required: false
          source: { ... }
          evidence: { ... }
```

### Traceability Chain

```
Official Docs  ──▶  Evidence Quote  ──▶  Rule in Spec  ──▶  Audit Result
      │                                                           │
      └──────────────── Verification Loop ────────────────────────┘
```

Every rule must have:
1. **Source** — Which document/section
2. **Evidence** — Actual quote supporting the rule
3. **Rule derivation** — Reasoning from evidence to rule

Rules without evidence are flagged by the spec linter.

### Verification Process

1. Run `--verify-spec` flag
2. For each rule, WebFetch the source URL
3. Check if evidence quote still exists
4. If docs changed, Claude analyzes if rule still holds
5. Report discrepancies for human review

When WebFetch fails (auth, rate limits), flag as "manual verification required."

## Context Analysis (Layer 3)

The false-positive filter. Uses heuristics with LLM fallback for uncertain cases.

### Detection Flow

```
Issue from Layer 2
        │
        ▼
┌─────────────────────────┐
│ Check explicit markers  │  <!-- audit:example-section -->
│ Found? → SKIP (1.0)     │
└───────────┬─────────────┘
            │ Not found
            ▼
┌─────────────────────────┐
│ Check high-confidence   │  "### Examples", "**Example**:", code blocks
│ Found? → SKIP (0.95)    │
└───────────┬─────────────┘
            │ Not found
            ▼
┌─────────────────────────┐
│ Check security context  │  permissionDecision: deny, exit 1/2
│ Found? → SKIP (0.9)     │
└───────────┬─────────────┘
            │ Not found
            ▼
┌─────────────────────────┐
│ Calculate confidence    │
│ < 0.5 → UNCERTAIN       │
│ ≥ 0.5 → APPLY           │
└─────────────────────────┘
```

### Confidence Thresholds

| Severity | Confidence | Action |
|----------|------------|--------|
| CRITICAL | ≥ 0.7 | Report as confirmed |
| CRITICAL | < 0.7 | LLM verification |
| WARNING | ≥ 0.7 | Report as confirmed |
| WARNING | 0.5-0.7 | Report as "needs review" |
| WARNING | < 0.5 | Skip (avoid false positive) |
| INFO | ≥ 0.7 | Report as suggestion |
| INFO | < 0.7 | Skip |

### LLM Verification Prompt

For uncertain CRITICAL issues:

```markdown
## Context Analysis Request

**Issue:** [SEC-P001] Hardcoded system path detected
**File:** example.sh:47
**Match:** `/etc/`

**Context (±5 lines):**
```bash
if [[ "$file_path" == "/etc/"* ]]; then
  echo '{"permissionDecision": "deny"}' >&2
  exit 2
fi
```

**Question:** Is this path being ACCESSED (risk) or BLOCKED (security feature)?

**Respond:** APPLY | SKIP | UNCERTAIN
```

## Reporting Format

### Markdown Report

```markdown
# Plugin Audit Report: plugin-name

## Summary
| Severity | Confirmed | Needs Review | Skipped |
|----------|-----------|--------------|---------|
| CRITICAL | 0 | 0 | 1 |
| WARNING | 4 | 2 | 3 |

## Confirmed Issues
[High-confidence issues with rule ID, file:line, fix suggestion]

## Needs Review
[Medium-confidence issues that may be false positives]

## Skipped (Context-Filtered)
[Issues filtered with reasoning]

## Provenance
[Rules applied with sources]
```

### JSON Report (for CI)

```json
{
  "meta": { "timestamp": "...", "spec_version": "1.0.0" },
  "summary": { "critical": {...}, "warning": {...} },
  "issues": [...],
  "skipped": [...]
}
```

### Exit Codes

| Code | Meaning | CI Action |
|------|---------|-----------|
| 0 | Pass | Continue |
| 1 | Confirmed CRITICAL | Block |
| 2 | CRITICAL needs review | Warn |

## File Structure

```
plugin-audit/
├── SKILL.md                        # ~400 words, lean methodology
│
├── specification/
│   └── audit-spec.yaml             # Rules with full provenance
│
├── scripts/
│   ├── check-syntax.sh             # jq/yq validation
│   └── check-structure.sh          # Basic field/file checks
│
└── references/
    ├── context-patterns.md         # Example/security detection patterns
    └── rule-reference.md           # All rules explained
```

### SKILL.md Content Guidelines

Following writing-skills best practices:
- **~400 words** in SKILL.md body
- **Description:** "Use when..." triggers only, NO workflow summary
- **Heavy reference** in separate files
- **One level deep** file references

## Testing Methodology

Following TDD for skills: **NO SKILL WITHOUT FAILING TEST FIRST**

### Baseline Test Scenarios

Before writing skill content, test Claude's baseline behavior:

**Scenario A: Example Paths**
```
Audit plugin-dev. Check if all file references in skills exist.
```
Expected baseline: Flags example paths as missing

**Scenario B: Security Context**
```
Check plugin-dev for hardcoded /etc/ or /sys/ paths.
```
Expected baseline: Flags deny blocks as vulnerabilities

**Scenario C: Command Frontmatter**
```
Validate all commands have correct frontmatter.
```
Expected baseline: May assume `name` is required

### Success Criteria

With skill loaded, Claude should:
- [ ] Load and follow the specification
- [ ] Run deterministic scripts for syntax/structure
- [ ] Analyze context before reporting
- [ ] Skip example paths with explanation
- [ ] Recognize security blocks as features
- [ ] Use correct rules from verified spec
- [ ] Report with confidence and provenance

### Iteration Process

1. Run baseline scenarios → capture failures
2. Write minimal skill addressing gaps
3. Run scenarios with skill → verify improvement
4. Capture new rationalizations → add explicit guidance
5. Repeat until bulletproof

## Implementation Plan

### Phase 1: Specification
1. Create `audit-spec.yaml` with all component types
2. Add evidence for each rule from official docs
3. Create spec schema for validation

### Phase 2: Scripts
1. Write `check-syntax.sh` (jq/yq wrappers)
2. Write `check-structure.sh` (field presence, file existence)
3. Test scripts independently

### Phase 3: References
1. Write `context-patterns.md` with detection heuristics
2. Write `rule-reference.md` explaining each rule

### Phase 4: Baseline Testing
1. Run test scenarios without skill
2. Document baseline failures
3. Capture exact rationalizations

### Phase 5: Skill Content
1. Write minimal SKILL.md addressing gaps
2. Test with skill loaded
3. Iterate until success criteria met

### Phase 6: Validation
1. Run on plugin-dev itself
2. Verify zero false positives for known cases
3. Test with other plugins

## Open Questions

1. **Spec storage:** Should `audit-spec.yaml` be in plugin-dev or a separate shared location?

2. **Doc cache:** Should we cache documentation locally for faster verification, or always fetch live?

3. **CI mode:** Should `--ci` skip semantic analysis entirely, or include high-confidence context filtering?

4. **Cross-plugin rules:** Should the spec support rules that span multiple plugins?

## Appendix: Context Detection Patterns

### High-Confidence Example Indicators

```yaml
- pattern: '^#{1,3}\s+Examples?$'
  scope: section
  confidence: 0.95

- pattern: '^\s*-\s*\*\*Example\*\*:'
  scope: line
  confidence: 0.95

- pattern: '```'  # code blocks
  scope: block
  confidence: 0.9
  applies_to: [file_references]
```

### Security Deny Block Patterns

```yaml
- pattern: 'permissionDecision.*deny'
  confidence: 0.95

- pattern: 'exit [12]\s*$'
  context: conditional
  confidence: 0.9

- pattern: '"decision":\s*"block"'
  confidence: 0.95
```

---

*Design complete. Next step: Run baseline tests before writing skill content.*
