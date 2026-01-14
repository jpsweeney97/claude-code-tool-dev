# claude-tool-audit Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the claude-tool-audit skill that audits Claude Code tool design documents using 4 parallel lenses and an Arbiter synthesis.

**Architecture:** Multi-file skill with main orchestrator (SKILL.md), 4 lens prompt templates with embedded verified patterns, 1 Arbiter prompt, and fallback specs reference. Lenses execute in parallel via Task tool, Arbiter synthesizes findings.

**Tech Stack:** Claude Code skills (markdown-based), Task tool for parallel execution, claude-code-guide agent for live specs.

**Quality Standards:** This plan follows `skills-semantic-quality-addendum.md` and `skills-domain-annexes.md` (auditing + pipelines annexes).

---

## Task 1: Create Directory Structure

**Files:**
- Create: `.claude/skills/claude-tool-audit/`
- Create: `.claude/skills/claude-tool-audit/lenses/`
- Create: `.claude/skills/claude-tool-audit/arbiter/`
- Create: `.claude/skills/claude-tool-audit/references/`

**Step 1: Create skill directory with subdirectories**

```bash
mkdir -p .claude/skills/claude-tool-audit/{lenses,arbiter,references}
```

**Step 2: Verify structure exists**

Run: `ls -la .claude/skills/claude-tool-audit/`
Expected: Shows lenses/, arbiter/, references/ subdirectories

*(No commit — Git doesn't track empty directories. First file commit in Task 2.)*

---

## Task 2: Create All 4 Lens Prompt Templates

**Files:**
- Create: `.claude/skills/claude-tool-audit/lenses/spec-auditor.md`
- Create: `.claude/skills/claude-tool-audit/lenses/behavioral-realist.md`
- Create: `.claude/skills/claude-tool-audit/lenses/robustness-critic.md`
- Create: `.claude/skills/claude-tool-audit/lenses/scope-minimalist.md`

**Step 1: Write Spec Auditor lens**

```markdown
# Spec Auditor Lens

You audit Claude Code {{ARTIFACT_TYPE}} designs for compliance with official specifications.

## Your Core Question
"Does this design comply with official Claude Code documentation?"

## Specifications to Apply
{{ARTIFACT_SPECS}}

## Analysis Checklist
For each, note violations with evidence:
- [ ] Frontmatter: Required fields present, no undocumented fields, constraints valid
- [ ] Structure: Files in correct locations, directory conventions followed
- [ ] Field values: Only documented values used, no invented properties
- [ ] Patterns: Exit codes, events, transports match official docs
- [ ] Cross-references: References to other artifacts are valid paths
- [ ] Semantics: Description explains when/why, not just present
- [ ] Deprecations: No documented anti-patterns used

## Output Format
Use this exact structure:

### Scope Statement
- **Assessed:** [sections examined]
- **Not assessed:** [sections skipped]
- **Confidence:** Full / Sampled / Partial

### Finding N: [Title]
- **Element:** [taxonomy: frontmatter.*, workflow.*, etc.]
- **Issue:** [what's wrong]
- **Evidence:** [quote from design]
- **Severity:** Critical / Major / Minor
- **Classification:** Verified / Inferred / Assumed
- **Requirement:** [which spec requirement violated]

### Summary
- Total findings: X (Y Critical, Z Major, W Minor)

## Design to Audit
{{TARGET_CONTENT}}
```

**Step 2: Write Behavioral Realist lens**

```markdown
# Behavioral Realist Lens

You audit Claude Code {{ARTIFACT_TYPE}} designs for alignment with how Claude actually behaves.

## Your Core Question
"Does this design match how Claude actually behaves in practice?"

## Claude Code Behavioral Context (Verified)

Consider these documented behaviors when auditing:

**Memory & State:**
- No persistent memory across sessions; state must be saved to CLAUDE.md files explicitly
- Context window is 200K tokens; attention quality may degrade in very long contexts
- Each new session starts fresh unless context explicitly preserved

**Tool Behaviors:**
- Read tool: 2000 lines max by default; long lines truncated at 2000 chars
- Bash tool: 60-second timeout default; environment variables don't persist between commands
- Task tool: Subagents run in separate context windows; cannot spawn other subagents
- WebFetch: Content capped at 25K tokens; 10K token warning threshold

**Reasoning Limitations:**
- No official reliability percentages documented for multi-step reasoning
- Complex tasks benefit from chain-of-thought, iterative refinement, or best-of-N verification
- Knowledge cutoffs vary by model (Opus 4.5: May 2025, Sonnet 4.5: Jan 2025)

**Proactive Behavior:**
- Claude delegates to subagents based on task relevance, not spontaneously
- Explicit triggers in prompts required for proactive actions

## Analysis Checklist
For each, note unrealistic assumptions with evidence:
- [ ] State: Assumes persistence that doesn't exist, cross-session memory
- [ ] Reasoning: Multi-step instructions Claude can't reliably follow
- [ ] Proactivity: Expects Claude to act without prompting
- [ ] Context: Exceeds practical token/attention limits
- [ ] Tools: Assumes tool behaviors that don't match reality
- [ ] Users: Expects user behavior patterns that won't happen
- [ ] Permissions: Assumes autonomy requiring config changes
- [ ] Model fit: Task complexity vs recommended model

## Output Format
Use this exact structure:

### Scope Statement
- **Assessed:** [sections examined]
- **Not assessed:** [sections skipped]
- **Confidence:** Full / Sampled / Partial

### Finding N: [Title]
- **Element:** [taxonomy: behavior.*, workflow.*, etc.]
- **Issue:** [what's unrealistic]
- **Evidence:** [quote from design]
- **Severity:** Critical / Major / Minor
- **Classification:** Verified / Inferred / Assumed
- **Mitigation:** [how to adjust for realistic behavior]

### Summary
- Total findings: X (Y Critical, Z Major, W Minor)

## Design to Audit
{{TARGET_CONTENT}}
```

**Step 3: Write Robustness Critic lens**

```markdown
# Robustness Critic Lens

You audit Claude Code {{ARTIFACT_TYPE}} designs for failure modes and edge cases.

## Your Core Question
"What breaks this design?"

## Common Failure Patterns (Verified)

Consider these documented failure modes when auditing:

**Hook-Specific Failures:**
- Exit code 1 logs error but CONTINUES execution (doesn't block)
- Exit code 2 blocks but ignores JSON in stdout (only stderr used)
- JSON output only processed at exit 0; malformed JSON silently ignored
- Default 60-second timeout; timed-out hooks don't retry
- Hooks run in parallel; no shared state without explicit locking

**Input/Output Failures:**
- stdin JSON parsing crashes if missing try/except
- Missing fields cause KeyError without .get() defaults
- Unquoted shell variables enable injection attacks
- Relative paths fail because hook cwd varies

**Tool Failures:**
- Read exceeds 2000 lines: file truncated silently
- Bash exceeds 60s: command killed, no retry
- Task subagent can't spawn nested subagents
- Environment variables lost between Bash commands

**Security Failures:**
- Path traversal via `..` in tool inputs
- Credential logging in stderr exposes secrets
- Trusting tool_input without validation enables injection

**Recovery Gaps:**
- No documented retry mechanisms for tool failures
- Timeout treated as failure, not ambiguous outcome
- User may not see stderr unless verbose mode enabled

## Analysis Checklist
For each, identify what could go wrong:
- [ ] Edge cases: Inputs or scenarios not covered
- [ ] Error handling: What happens on failure, silent failures
- [ ] State transitions: Workflow interrupted mid-process
- [ ] Integration: Handoffs between components could fail
- [ ] Underspecification: Guidance too vague to implement consistently
- [ ] Recovery: How user knows something failed, how to recover
- [ ] Security: Credential exposure, destructive ops, input sanitization
- [ ] Testability: How to verify this works, incremental testing possible

## Output Format
Use this exact structure:

### Scope Statement
- **Assessed:** [sections examined]
- **Not assessed:** [sections skipped]
- **Confidence:** Full / Sampled / Partial

### Finding N: [Title]
- **Element:** [taxonomy: workflow.*, behavior.*, etc.]
- **Issue:** [what breaks]
- **Evidence:** [quote from design]
- **Severity:** Critical / Major / Minor
- **Classification:** Verified / Inferred / Assumed
- **Scenario:** [how this manifests in practice]

### Summary
- Total findings: X (Y Critical, Z Major, W Minor)

## Design to Audit
{{TARGET_CONTENT}}
```

**Step 4: Write Scope Minimalist lens**

```markdown
# Scope Minimalist Lens

You audit Claude Code {{ARTIFACT_TYPE}} designs for unnecessary complexity and scope creep.

## Your Core Question
"What can be cut from this design?"

## Minimal Viable Patterns (Verified)

Use these baselines when auditing scope:

**Skills:**
- Minimum: SKILL.md with `name` + `description` frontmatter (2 required fields)
- Supporting files (references/, scripts/, examples/) are all optional
- Most skills don't need subdirectories at all

**Plugins:**
- Minimum: plugin.json with only `name` field (1 required field)
- version, description, author are all optional
- Default directories (commands/, agents/, skills/) auto-load if present

**Commands:**
- Minimum: .md file in .claude/commands/ directory
- No frontmatter required (description is optional)
- $ARGUMENTS substitution is the only special syntax

**Hooks:**
- Minimum: settings.json entry + executable script
- Can be inline command string, no separate file needed

**General:**
- If something works without a feature, the feature is optional
- Token/latency cost scales with complexity; simpler = faster + cheaper

## Analysis Checklist
For each, identify what could be removed or simplified:
- [ ] Essential vs nice-to-have: What's the absolute minimum viable version
- [ ] YAGNI: Features solving problems that don't exist yet
- [ ] Complexity: Abstractions adding overhead without value
- [ ] Redundancy: Duplicated elements that could be unified
- [ ] Cognitive load: How many concepts must someone learn
- [ ] Incremental value: Which 20% delivers 80% of benefit
- [ ] Alternatives: Simpler way to achieve the same goal
- [ ] Operational cost: Token costs, latency, maintenance burden

## Output Format
Use this exact structure:

### Scope Statement
- **Assessed:** [sections examined]
- **Not assessed:** [sections skipped]
- **Confidence:** Full / Sampled / Partial

### Finding N: [Title]
- **Element:** [taxonomy: scope.*, workflow.*, etc.]
- **Issue:** [what's unnecessary]
- **Evidence:** [quote from design]
- **Severity:** Critical / Major / Minor
- **Classification:** Verified / Inferred / Assumed
- **Verdict:** Keep / Cut / Simplify

### Summary
- Total findings: X (Y Critical, Z Major, W Minor)
- Estimated complexity reduction if findings addressed: X%

## Design to Audit
{{TARGET_CONTENT}}
```

**Step 5: Verify all 4 lenses exist**

Run: `ls .claude/skills/claude-tool-audit/lenses/`
Expected: behavioral-realist.md, robustness-critic.md, scope-minimalist.md, spec-auditor.md

**Step 6: Verify line counts are reasonable**

Run: `wc -l .claude/skills/claude-tool-audit/lenses/*.md`
Expected: ~45 lines for spec-auditor, ~65-70 lines for others (with embedded patterns)

**Step 7: Commit all lenses together**

```bash
git add .claude/skills/claude-tool-audit/lenses/
git commit -m "feat(claude-tool-audit): add 4 lens prompt templates with embedded verified patterns"
```

---

## Task 3: Create Arbiter Synthesis Prompt

**Files:**
- Create: `.claude/skills/claude-tool-audit/arbiter/synthesis-prompt.md`

**Step 1: Write the Arbiter prompt**

```markdown
# Arbiter Synthesis

You synthesize findings from 4 audit lenses into prioritized, actionable results.

## Your Core Task
1. Identify **convergent findings** — issues that multiple lenses flagged, even using different vocabulary
2. Extract **unique insights** — valuable findings only one lens caught
3. Prioritize all findings for action
4. Render verdict on ship-readiness

## Inputs

### Lens Outputs
{{SPEC_AUDITOR_OUTPUT}}

{{BEHAVIORAL_REALIST_OUTPUT}}

{{ROBUSTNESS_CRITIC_OUTPUT}}

{{SCOPE_MINIMALIST_OUTPUT}}

### Context
- **Artifact type:** {{ARTIFACT_TYPE}}
- **Design stage:** {{DESIGN_STAGE}}

## Convergence Detection

Findings converge when they describe **the same underlying issue**, even if:
- Different Element taxonomy was used
- Different vocabulary or framing
- Different severity assigned
- One lens sees cause, another sees effect

For each potential convergence:
- State which findings you're grouping
- Explain WHY they're the same underlying issue
- Note any tension (e.g., different severity assessments)

## Prioritization Criteria

Rank findings by:
1. **Convergence count** — More lenses = higher confidence = higher priority
2. **Severity** — Critical > Major > Minor
3. **Effort to fix** — Low-effort fixes get priority boost
4. **Classification** — Verified > Inferred > Assumed

## Output Format

### Convergent Findings

#### C1: [Unified Title]
- **Lenses:** [which lenses flagged this]
- **Why convergent:** [your reasoning]
- **Unified severity:** [reconciled severity]
- **Element:** [most specific Element from any lens]
- **Issue:** [synthesized description]
- **Evidence:** [strongest evidence from any lens]

### Unique Insights
Findings from single lenses that add value:

#### U1: [Title]
- **Lens:** [source]
- **Why valuable:** [why this matters despite no convergence]
- [rest of finding fields]

### Prioritized Recommendations

| Priority | Finding | Action | Effort | Confidence |
|----------|---------|--------|--------|------------|
| P1 | C1 | [fix] | Low | High (3 lenses) |
| P2 | ... | ... | ... | ... |

### Verdict
- **Ship readiness:** ready / needs_work / major_revision
- **Critical path:** [findings that MUST be fixed]
- **Deferred:** [can wait for later iteration]
- **Summary:** [2-3 sentence assessment]
```

**Step 2: Verify file exists**

Run: `head -10 .claude/skills/claude-tool-audit/arbiter/synthesis-prompt.md`
Expected: Shows "Arbiter Synthesis" title

**Step 3: Commit**

```bash
git add .claude/skills/claude-tool-audit/arbiter/synthesis-prompt.md
git commit -m "feat(claude-tool-audit): add Arbiter synthesis prompt"
```

---

## Task 4: Create Fallback Specs Reference

**Files:**
- Create: `.claude/skills/claude-tool-audit/references/fallback-specs.md`

**Step 1: Write the fallback specs reference**

This is a machine-optimized document with verified specs for each artifact type.

```markdown
# Claude Code Artifact Specifications (Fallback)

> **Last verified:** 2026-01-09
> **Update trigger:** Re-verify when claude-code-guide returns significantly different specs
> **Owner:** Manual update by skill maintainer
> **Source:** Official Anthropic documentation via claude-code-guide agent

---

## Skills

### Required Structure
| Element | Requirement |
|---------|-------------|
| File | `SKILL.md` in skill directory |
| Frontmatter | YAML with `name`, `description` (required) |
| Location | `.claude/skills/<name>/SKILL.md` |

### Valid Frontmatter Fields
| Field | Required | Type | Notes |
|-------|----------|------|-------|
| name | Yes | string | Lowercase, numbers, hyphens. Max 64 chars. |
| description | Yes | string | What it does + when to use. Max 1024 chars. |
| model | No | string | Specific Claude model for this skill |
| allowed-tools | No | string | Restrict which tools Claude can use |
| user-invocable | No | boolean | Hide from slash menu if false |

### Anti-patterns
- Hardcoded file paths (use relative or ask user)
- Dependencies on external packages (skills run in minimal environment)
- Assuming cross-session memory

---

## Hooks

### Required Structure
| Element | Requirement |
|---------|-------------|
| File | Script with settings.json entry |
| Location | Configured in settings.json hooks section |

### Event Types
| Event | Runs When | Can Block |
|-------|-----------|-----------|
| PreToolUse | Before tool call | Yes |
| PostToolUse | Tool completes | No |
| UserPromptSubmit | User submits prompt | Yes |
| Stop | Main agent finishes | Yes |
| SubagentStop | Subagent finishes | Yes |
| SessionStart | Session begins | No |
| SessionEnd | Session terminates | No |
| PreCompact | Before compact | No |
| Notification | Notification sent | No |
| PermissionRequest | Permission dialog | Yes |

### Exit Codes
| Code | Meaning |
|------|---------|
| 0 | Allow / success |
| 1 | Error (logged, does NOT block) |
| 2 | Block with message (stderr used) |

### Anti-patterns
- Exit code 1 for blocking (use 2)
- JSON in stdout at exit 2 (ignored; use stderr)
- Not reading stdin JSON
- Synchronous network calls without timeout

---

## Plugins

### Required Structure
| Element | Requirement |
|---------|-------------|
| Manifest | `.claude-plugin/plugin.json` |
| Location | Any directory with manifest |

### Manifest Fields
| Field | Required | Type |
|-------|----------|------|
| name | Yes | string |
| version | No | semver string |
| description | No | string |
| author | No | object with name |
| skills | No | path or array |
| commands | No | path or array |
| agents | No | array of file paths |
| mcpServers | No | path to .mcp.json |

### Path Conventions
- All paths use `./` prefix for portability
- Skills: `"./skills/"` or `["./skills/one.md"]`

---

## Commands

### Required Structure
| Element | Requirement |
|---------|-------------|
| File | Markdown file |
| Location | `.claude/commands/<name>.md` |

### Frontmatter Fields
| Field | Required | Notes |
|-------|----------|-------|
| description | No | Shown in command list (recommended) |
| argument-hint | No | Placeholder text for arguments |

### Placeholder
- `$ARGUMENTS` — substituted with user input after command name

---

## Subagents

### Configuration via Task Tool
| Field | Type | Notes |
|-------|------|-------|
| subagent_type | string | Agent type identifier |
| prompt | string | Task description |
| model | string | sonnet, opus, haiku |
| max_turns | number | API round-trips limit |

### Built-in Types
- general-purpose: Multi-step tasks with all tools
- Explore: Fast codebase exploration
- Plan: Architecture planning
- claude-code-guide: Documentation queries (uses haiku)

---

## Common Behavioral Patterns

### Claude Limitations
- No cross-session memory without explicit persistence (CLAUDE.md files)
- Context window 200K tokens; attention quality degrades in very long contexts
- Multi-step reasoning reliability decreases with complexity
- Proactive behavior requires explicit triggers in prompts

### Model Selection
| Task | Recommended |
|------|-------------|
| Simple queries, doc lookup | haiku |
| Standard development | sonnet |
| Complex architecture | opus |

### Tool Behaviors
| Tool | Behavior |
|------|----------|
| Task | Subagents run in separate context; cannot nest |
| Read | Max 2000 lines default; truncates long lines at 2000 chars |
| Bash | 60-second timeout default; env vars don't persist |
| WebFetch | 25K token cap; 10K warning threshold |
```

**Step 2: Verify file word count is reasonable**

Run: `wc -w .claude/skills/claude-tool-audit/references/fallback-specs.md`
Expected: ~600-800 words (machine-optimized, not prose)

**Step 3: Commit**

```bash
git add .claude/skills/claude-tool-audit/references/fallback-specs.md
git commit -m "feat(claude-tool-audit): add fallback specs reference with verified content"
```

---

## Task 5: Create Main SKILL.md Orchestrator

**Files:**
- Create: `.claude/skills/claude-tool-audit/SKILL.md`

**Pre-writing checklist (from quality specs):**

Before writing, verify the content will satisfy:

**Semantic minimums (`skills-semantic-quality-addendum.md`):**
- [ ] Primary goal stated in 1-2 sentences
- [ ] >=3 non-goals listed
- [ ] Hard constraints declared
- [ ] Each decision point has observable trigger
- [ ] Quick check measures primary success property
- [ ] Failure interpretation exists
- [ ] Calibration wording (Verified/Inferred/Assumed)

**Auditing annex (`annex.audit.local-repo`):**
- [ ] Evidence trail format specified (path + query + observation)
- [ ] Claim strength policy documented (sampled vs global)
- [ ] Scope section includes "What was NOT assessed"
- [ ] Findings include next step + verification

**Pipelines annex (`annex.pipeline.local-repo`):**
- [ ] Safe-by-default: read-only analysis
- [ ] Step-level signals for each procedure step
- [ ] Partial run recovery documented
- [ ] Idempotency considered

**Step 1: Write the main orchestrator skill**

Extract content from design document (`docs/plans/2026-01-09-claude-tool-audit-design.md`).

**Frontmatter (use documented fields only):**

```yaml
---
name: claude-tool-audit
description: Audit Claude Code tool designs using 4 parallel lenses with Arbiter synthesis
model: claude-sonnet-4-20250514
---
```

**Sections to INCLUDE in SKILL.md** (extract from design doc):

| Section | Design Lines | Notes |
|---------|--------------|-------|
| Primary Goal | 8-10 | 1-2 sentences |
| Non-Goals | 12-20 | All 6 items |
| Quality Standards | 22-37 | Reference to quality specs |
| When to Use | 40-53 | Activation signals |
| When NOT to Use | 55-69 | STOP conditions |
| Inputs | 71-109 | Required, Optional, Constraints, Mode Detection |
| Outputs | 111-135 | Artifacts + Definition of Done (both modes) |
| Procedure | 137-181 | All 11 steps |
| Decision Points | 183-213 | All 7 DPs with observable triggers |
| Verification | 215-232 | Quick Check + Deep Check |
| Troubleshooting | 234-259 | Common failures + anti-patterns |
| Lens Specifications | 262-312 | Universal schema, taxonomy, classification (NOT full prompts) |
| Output Formats | 777-949 | audit-report.md + audit-impl-spec.json templates |
| Edge Case Handling | 953-1030 | EC1-EC6 |
| Workflow Variants | 1033-1082 | Full + Quick mode descriptions |

**Sections to EXCLUDE from SKILL.md** (remain in design doc only):

| Section | Reason |
|---------|--------|
| Full lens prompt templates (lines 332-656) | Already in `lenses/*.md` files |
| Full Arbiter prompt (lines 690-774) | Already in `arbiter/synthesis-prompt.md` |
| Worked Example (lines 1116-1254) | Deferred to v1.1 |
| Implementation Notes (lines 1258-1296) | Developer reference, not runtime |
| Revision History (lines 1300-1307) | Design doc metadata |
| Skill Structure diagram (lines 1085-1113) | Developer reference |

**Key transformation notes:**

1. Lens Specifications section: Include the Universal Output Schema and Element Taxonomy tables, but reference `lenses/*.md` for full prompts instead of embedding them
2. Mode Detection: Ensure `$ARGUMENTS` parsing for `--quick` flag is explicit in procedure
3. Add explicit success/failure signals to each procedure step
4. Include Calibration labeling instructions (Verified/Inferred/Assumed)

**Step 2: Verify frontmatter is valid**

Run: `head -6 .claude/skills/claude-tool-audit/SKILL.md`
Expected: Valid YAML with only name, description, model (no metadata wrapper)

**Step 3: Verify sections exist**

Run: `grep -c "^## " .claude/skills/claude-tool-audit/SKILL.md`
Expected: ~15-20 major sections

Run: `grep -c "^### DP" .claude/skills/claude-tool-audit/SKILL.md`
Expected: 7 decision points

**Step 4: Verify line count**

Run: `wc -l .claude/skills/claude-tool-audit/SKILL.md`
Expected: ~380-420 lines

**Step 5: Commit**

```bash
git add .claude/skills/claude-tool-audit/SKILL.md
git commit -m "feat(claude-tool-audit): add main orchestrator SKILL.md"
```

---

## Task 6: Test Skill Discovery

**Files:**
- None (verification only)

**Step 1: Verify skill is discoverable**

Run: `ls -la .claude/skills/claude-tool-audit/`
Expected: Shows SKILL.md, lenses/, arbiter/, references/

**Step 2: Count total files**

Run: `find .claude/skills/claude-tool-audit -type f | wc -l`
Expected: 7 files (SKILL.md + 4 lenses + arbiter + fallback-specs)

**Step 3: Verify frontmatter is valid**

Run: `head -6 .claude/skills/claude-tool-audit/SKILL.md`
Expected: Valid YAML frontmatter with name, description, model (no metadata wrapper)

---

## Task 7: Integration Test with Design Document

**Files:**
- Test: `docs/plans/2026-01-09-claude-tool-audit-design.md` (existing)

**Step 1: Invoke skill on its own design document (quick mode)**

Run the skill manually:
```
/claude-tool-audit docs/plans/2026-01-09-claude-tool-audit-design.md --quick
```

**Step 2: Verify output structure**

Expected:
- Output file `quick-audit.md` created (not `audit-report.md` + JSON)
- Contains "## Spec Compliance" section
- Contains "## Behavioral Feasibility" section
- Contains "## Verdict" with "Likely to work?" assessment
- No Arbiter synthesis (quick mode skips it)

**Step 3: Test edge case - trivial document**

Create a temp file and test rejection:
```bash
echo "# Test\n\nShort design." > /tmp/trivial-design.md
```

Run: `/claude-tool-audit /tmp/trivial-design.md`
Expected: Skill notes insufficient content or suggests brainstorming

**Step 4: Test edge case - ambiguous artifact type**

Create a file without clear artifact signals:
```bash
echo "# Feature Design\n\nThis feature will improve performance.\n\n## Goals\n- Be faster\n- Use less memory" > /tmp/ambiguous-design.md
```

Run: `/claude-tool-audit /tmp/ambiguous-design.md`
Expected: Skill STOPs and asks user to confirm artifact type

**Step 5: Commit any fixes discovered**

If skill execution reveals issues, fix them and commit:
```bash
git add .claude/skills/claude-tool-audit/
git commit -m "fix(claude-tool-audit): address issues found in integration test"
```

---

## Task 8: Final Verification and Summary

**Files:**
- None (git operations only)

**Step 1: Verify all files committed**

Run: `git status`
Expected: Working tree clean (or only unrelated changes)

**Step 2: Create summary commit if needed**

If there are any remaining staged changes:
```bash
git commit -m "feat(claude-tool-audit): complete skill implementation v1.0.0"
```

**Step 3: Document completion**

The skill is now ready for use. Key files:
- `.claude/skills/claude-tool-audit/SKILL.md` — main orchestrator
- `.claude/skills/claude-tool-audit/lenses/*.md` — 4 lens prompts with embedded patterns
- `.claude/skills/claude-tool-audit/arbiter/synthesis-prompt.md` — Arbiter
- `.claude/skills/claude-tool-audit/references/fallback-specs.md` — verified offline specs

---

## Appendix: File Summary

| File | Lines | Purpose |
|------|-------|---------|
| SKILL.md | ~400 | Main orchestrator with procedure, inputs/outputs |
| lenses/spec-auditor.md | ~45 | Spec compliance lens (uses {{ARTIFACT_SPECS}}) |
| lenses/behavioral-realist.md | ~70 | Behavioral realism lens with embedded context |
| lenses/robustness-critic.md | ~75 | Failure mode lens with embedded patterns |
| lenses/scope-minimalist.md | ~70 | Scope creep lens with embedded patterns |
| arbiter/synthesis-prompt.md | ~75 | Convergence detection and prioritization |
| references/fallback-specs.md | ~180 | Verified cached specs for offline operation |

**Total:** ~915 lines across 7 files

---

## Appendix: Changes from Original Plan

| Original | Updated | Reason |
|----------|---------|--------|
| Tasks 2-5 separate lens commits | Single Task 2 with combined commit | Reduce git noise |
| Lens templates without embedded patterns | Embedded verified behavioral/failure/minimal patterns | Better analysis without extra subagent queries |
| Fallback specs with inaccuracies | Verified specs (Bash 60s, plugin needs only name, etc.) | Documentation audit found errors |
| Task 8 no pre-checklist | Pre-writing checklist for quality specs | Ensure semantic quality |
| Task 10 happy path only | Added 2 edge case tests | Verify STOP behavior |
| metadata wrapper in frontmatter | Documented fields only (name, description, model) | Spec compliance |
