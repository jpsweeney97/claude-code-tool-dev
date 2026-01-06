---
name: verify
description: Verify claims about Claude Code against official Anthropic documentation. Use when fact-checking Claude Code features, behaviors, or configurations.
license: MIT
metadata:
  version: "1.4.0"
  model: claude-sonnet-4-20250514
  timelessness_score: 8
---

# Verify Claude Code Claims

Fact-check claims about Claude Code against official documentation.

---

## Quick Start

```
/verify "Skills require a license field in frontmatter"

→ Extracts claim → Queries claude-code-guide → Returns verdict with citation
```

**Output:** Confidence symbol (✓ ~ ? ✗) + evidence + source URL

---

## Triggers

- `/verify "..."` - Verify a specific claim
- "Is it true that..." - Natural language verification
- "Does Claude Code support..." - Feature verification
- "fact-check" / "verify claim" - General verification
- "Check if [statement about Claude Code] is accurate"

## When to Use

- Before acting on information about Claude Code capabilities
- When documentation seems inconsistent or outdated
- When verifying third-party tutorials or guides
- After "I think..." or "I believe..." statements about Claude Code

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

Check `references/known-claims.md` for pre-verified claims.

```
Input: "Skills require a license field"
  ↓
Check known-claims.md → Match found: "Skills require license" = ✗ False
  ↓
Return immediately (no query needed)
```

**When to skip to Step 1:**
- Claim not in known-claims.md
- Claim requires current documentation (behavioral edge cases)
- User explicitly requests fresh verification

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

## Extension Points

| Extension | How | Status |
|-----------|-----|--------|
| New documentation source | Add to source priority in Step 2 | Open |
| New claim type | Add to claim types in Step 1 | Open |
| Custom confidence levels | Extend the 4-level taxonomy | Open |
| Claim caching | Add scripts/cache.py + data/verified-claims.json | Open |
| Known claims | Add to references/known-claims.md | **Implemented** |

---

## Dependencies

- **claude-code-guide agent** - Provides access to official Claude Code documentation
- **Task tool** - Launches verification queries

---

## Changelog

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
