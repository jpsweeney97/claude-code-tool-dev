# claude-tool-audit Skill Design

**Date:** 2026-01-09
**Status:** Draft
**Category:** `category=auditing-assessment` (primary), `category=agentic-pipelines` (secondary)
**Risk:** medium (agentic orchestration with 4+ subagents)

## Primary Goal

Audit Claude Code tool design documents (skills, plugins, hooks, commands, subagents) using 4 specialized lenses that create productive tension, synthesize findings via an Arbiter, and produce actionable outputs for both humans and Claude.

## Non-Goals

1. **Not implementation validation** — Does not execute code or run tests; audits design documents only
2. **Not security audit of running systems** — Does not probe live services or credentials
3. **Not code review** — Does not review implementation code, only design documents
4. **Not a replacement for brainstorming** — Does not help crystallize vague concepts into designs
5. **Not a general document editor** — Does not fix issues, only identifies them
6. **Not for trivial designs** — Designs under 100 words have insufficient content to audit meaningfully

---

## Quality Standards

This skill follows:
- `skills-semantic-quality-addendum.md` — semantic minimums (intent, constraints, decision points, verification)
- `skills-domain-annexes.md` — auditing annex (`annex.audit.local-repo`) + pipelines annex (`annex.pipeline.local-repo`)

Key requirements satisfied:
- **Intent fidelity**: Primary goal + non-goals explicit; no proxy goals
- **Evidence-backed claims**: Every finding includes path + query + observation
- **Claim strength discipline**: Sampled vs global coverage disclosed; confidence labeled
- **Observable decision points**: Each DP references file existence, command output, or user response
- **Calibration honesty**: Verified/Inferred/Assumed labeling required; "Not run (reason)" for skipped checks
- **Safe-by-default**: Read-only analysis; produces reports, not changes
- **Step-level signals**: Each procedure step has explicit success/failure criteria

---

## When to Use

Use this skill when:

- You have a **design document** for a Claude Code tool (skill, plugin, hook, command, subagent) and want to identify issues before implementation
- You want **multiple analytical perspectives** applied systematically (compliance, feasibility, robustness, scope)
- You need **convergent findings** — issues flagged by multiple lenses carry higher confidence
- You want **actionable output** — both a human-readable report and a JSON spec Claude can use for implementation

Activation signals:
- User says "audit this design", "review this plan", "check this spec"
- User has a file in `docs/plans/` or a `SKILL.md` draft
- User is about to implement and wants a final design check

## When NOT to Use

Do NOT use this skill when:

- **Design is too vague** — Conceptual ideas without artifact type or structure (redirect to `/brainstorming`)
- **Design is trivial** — Under 100 words; insufficient content for meaningful audit
- **User wants implementation** — They need code written, not analysis (use implementation skills)
- **User wants code review** — They have implementation code to review (use code review skills)
- **User wants security testing** — They need runtime security analysis (use security audit skills)
- **Artifact type cannot be determined** — STOP if user cannot clarify what they're building

STOP conditions:
- Target document cannot be read or doesn't exist
- Artifact type is unclear AND user cannot clarify after options presented
- Design stage is unknown AND user cannot specify (early/working/final)

---

## Inputs

### Required

| Input | Description | STOP if missing? |
|-------|-------------|------------------|
| **Target document** | Path to design document (or pasted content) | Yes — cannot audit nothing |
| **Artifact type** | skill / plugin / hook / command / subagent (or detectable) | Yes, after proposing options |

### Optional

| Input | Description | Default |
|-------|-------------|---------|
| **Design stage** | early / working / final | Ask if unclear |
| **Focus areas** | Specific concerns to prioritize | All lenses equally weighted |
| **Mode** | full / quick | full |

### Constraints / Assumptions

| Constraint | Fallback |
|------------|----------|
| claude-code-guide agent available | Use `references/fallback-specs.md` |
| Target document < 50K tokens | Hierarchical audit (structure pass → deep dive) |
| Network available | Fallback specs are local; no network required for core audit |

### Mode Detection

Parse the user's arguments to detect mode:
- If arguments contain `--quick` or `-q`: Quick mode (2 lenses, no Arbiter)
- Otherwise: Full mode (4 lenses + Arbiter)

Extract the target path by removing the flag from arguments.

**Example invocations:**
- `/claude-tool-audit docs/plans/my-design.md` → Full mode
- `/claude-tool-audit docs/plans/my-design.md --quick` → Quick mode
- `/claude-tool-audit --quick docs/plans/my-design.md` → Quick mode (flag position flexible)

---

## Outputs

### Artifacts

| Artifact | Format | Purpose |
|----------|--------|---------|
| `audit-report.md` | Markdown | Human-readable report with convergent findings, recommendations, verdict |
| `audit-impl-spec.json` | JSON | Machine-parseable spec for Claude to use during implementation |

### Definition of Done (Objective Checks)

**Full Mode:**
1. Both output files exist (`audit-report.md`, `audit-impl-spec.json`)
2. All 4 lens outputs contain structured findings with Element/Issue/Evidence/Severity/Classification fields
3. Arbiter synthesis identifies convergent findings (or explicitly states none found)
4. Prioritized recommendations ranked P1/P2/P3 with effort estimates
5. Verdict includes ship_readiness: ready | needs_work | major_revision

**Quick Mode:**
1. Single output file exists (`quick-audit.md`)
2. Both lens outputs (Spec Auditor, Behavioral Realist) contain structured findings
3. Main thread merge produces combined findings list
4. Verdict includes likely_to_work: yes | needs_attention | major_issues

---

## Procedure

1. **Read target document** — Load the design document specified by the user.

2. **Detect artifact type** — Scan for signals (SKILL.md, plugin.json, hook events, etc.).
   - If clear: proceed
   - If unclear: propose options and **STOP. Ask user to confirm artifact type.**

3. **Confirm design stage** — Check if user specified early/working/final.
   - If not specified: **STOP. Ask: "Is this an early draft, working draft, or final design?"**

4. **Check document size** — If > 50K tokens, switch to hierarchical audit mode.

5. **Query domain knowledge** — Invoke claude-code-guide agent with:
   ```
   What are the official specifications for Claude Code {{ARTIFACT_TYPE}}?

   Include:
   1. Required fields — What must be present (frontmatter, structure)
   2. File structure — Where files go, naming conventions
   3. Valid values — Documented options for key fields
   4. Documented patterns — Exit codes, events, transports, etc.
   5. Anti-patterns — Explicitly discouraged approaches

   Focus on specifications from official Anthropic documentation, not community conventions.
   ```
   - If unavailable/timeout: load `references/fallback-specs.md` and note warning.

6. **Build lens prompts** — Inject specs into 4 lens prompt templates.

7. **Execute lenses in parallel** — Launch 4 Task tool calls simultaneously:
   - Spec Auditor
   - Behavioral Realist
   - Robustness Critic
   - Scope Minimalist

8. **Collect lens outputs** — Wait for all 4 to complete.

9. **Execute Arbiter** — Launch synthesis subagent with all 4 lens outputs.

10. **Generate outputs** — Write `audit-report.md` and `audit-impl-spec.json`.

11. **Present summary** — Show executive summary and verdict to user.

---

## Decision Points

### DP1: Artifact Type Detection
If artifact type is clear from document signals (SKILL.md, plugin.json, hook events, etc.), then proceed with detected type.
Otherwise, propose options: "This could be implemented as a skill, hook, plugin, or command. Which should I audit for?" and **STOP** until user confirms.

### DP2: Design Stage Confirmation
If user specified design stage (early/working/final), then apply stage-appropriate rigor.
Otherwise, **STOP** and ask: "What stage is this design? Early draft (directional feedback), Working draft (full audit, gaps as 'incomplete'), or Final design (full rigor, gaps as findings)?"

### DP3: Document Size
If document exceeds 50K tokens, then switch to hierarchical audit: structure pass first, then deep dive on high-risk sections.
Otherwise, proceed with standard full-document audit.

### DP4: Domain Knowledge Availability
If claude-code-guide returns specs successfully, then inject into lens prompts.
Otherwise, load fallback specs and add warning: "⚠️ Using cached specs (may not reflect latest Claude Code changes)."

### DP5: Multiple Artifact Types (Plugin)
If design describes a plugin with multiple components (skills + hooks + MCP), then use plugin-aware mode: query specs for ALL component types.
Otherwise, query specs for single artifact type only.

### DP6: Quick vs Full Mode
If user specifies `--quick`, then run only Spec Auditor + Behavioral Realist (no Arbiter, condensed output).
Otherwise, run full 4-lens + Arbiter workflow.

### DP7: Conceptual Design (No Artifact)
If design is purely conceptual with no artifact type, then suggest artifact mapping and offer to redirect to `/brainstorming`.
Otherwise, proceed with audit.

---

## Verification

### Quick Check
**Check:** All 4 lens outputs are valid markdown with structured findings tables.
**Expected:** Each lens output contains at least one `### Finding` section OR explicitly states "No findings in this lens."
**Command:** Validate that `audit-report.md` contains "Convergent Findings" and "Verdict" sections.

### Deep Check
**Check:** Cross-reference a sample finding against the target document.
**Expected:** The `Evidence` field quotes actual content from the design; the `Element` field uses the taxonomy (`frontmatter.*`, `workflow.*`, etc.).
**Command:** Spot-check 2-3 findings manually to confirm evidence accuracy.

### Hierarchical Audit Verification (if applicable)
**Check:** Structure pass identified high-risk sections; deep dive covered those sections.
**Expected:** Output notes which sections received deep analysis and which were structure-only.

---

## Troubleshooting

### Common Failure: Lens outputs are unstructured or incomplete
**Symptoms:** Missing tables, prose-only findings, no Element/Issue/Evidence fields.
**Likely causes:** Lens prompt not followed correctly; target document too vague to analyze.
**What to do:** Re-run failing lens with explicit format reminder; if persistent, check if target document has sufficient structure to audit.

### Common Failure: No convergent findings despite multiple lenses
**Symptoms:** Arbiter reports 0 convergence; all findings are "unique to one lens."
**Likely causes:** Design has no significant issues (rare), or lenses used incompatible terminology for same issues.
**What to do:** Check if element taxonomy was applied consistently; manually review lens outputs for semantic similarity that Arbiter missed.

### Common Failure: claude-code-guide times out or returns empty
**Symptoms:** Warning appears about using fallback specs.
**Likely causes:** Network issues; agent overload; malformed query.
**What to do:** Audit proceeds with fallback specs; if accuracy is critical, retry after resolving network/agent issues.

### Common Failure: Artifact type detection is wrong
**Symptoms:** Lenses apply wrong specs (e.g., hook specs for a skill design).
**Likely causes:** Design document has ambiguous signals; user didn't correct the detection.
**What to do:** Re-run with explicit artifact type specified by user.

### Anti-Pattern: User asks to audit implementation code
**Symptoms:** Target is `.py`, `.ts`, or similar code file instead of design document.
**What to do:** Redirect to code review skills; this skill audits designs, not implementations.

---

## Lens Specifications

### Universal Output Schema

All lenses MUST use this output structure for Arbiter compatibility:

```markdown
## [Lens Name] Findings

### Scope Statement
- **Assessed:** [list of design sections/elements examined]
- **Not assessed:** [elements skipped or out of scope]
- **Confidence:** Full / Sampled / Partial

### Finding 1: [Short title]
- **Element:** [taxonomy reference]
- **Issue:** [What's wrong]
- **Evidence:** [Quote from design]
- **Severity:** Critical / Major / Minor
- **Classification:** Verified / Inferred / Assumed
- **[Lens-specific field]:** [value]

### Finding 2: ...

## Summary
- Total findings: X (Y Critical, Z Major, W Minor)
- [Lens-specific summary]
```

### Element Taxonomy

Consistent naming enables convergence detection across lenses:

| Type | Pattern | Example |
|------|---------|---------|
| Frontmatter | `frontmatter.<field>` | `frontmatter.license` |
| Workflow | `workflow.<name>` | `workflow.synthesis` |
| Structure | `structure.<path>` | `structure.references/` |
| Behavior | `behavior.<topic>` | `behavior.multi-step-reliability` |
| Scope | `scope.<feature>` | `scope.parallel-execution` |
| Input | `input.<name>` | `input.target-document` |
| Output | `output.<artifact>` | `output.report-format` |

### Classification Labels

Each finding MUST be labeled:
- **Verified:** Supported by direct evidence quoted from design
- **Inferred:** Derived from verified facts; inference stated explicitly
- **Assumed:** Not verified in design; flagged for confirmation

---

### Lens 1: Spec Auditor

**Core question:** "Does this design comply with official Claude Code documentation?"

**Lens-specific field:** `Requirement` (which spec requirement is violated)

**Analysis vectors:**

| Vector | Examines |
|--------|----------|
| Frontmatter compliance | Required fields, constraints, forbidden terms |
| Structural compliance | Files in correct locations, directory structure |
| Field validity | Only documented fields, no invented properties |
| Documented patterns | Exit codes, events, transports match official docs |
| Cross-references | References to other artifacts are valid |
| Semantic compliance | Description explains when/why, not just field present |
| Deprecated patterns | Any documented anti-patterns used? |

**Full Prompt Template:**

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

---

### Lens 2: Behavioral Realist

**Core question:** "Does this design match how Claude actually behaves?"

**Lens-specific field:** `Mitigation` (how to adjust for realistic behavior)

**Analysis vectors:**

| Vector | Examines |
|--------|----------|
| State assumptions | Persistence that doesn't exist, cross-session memory |
| Reasoning reliability | Multi-step instructions Claude can/can't follow |
| Proactive behavior | Expects Claude to act without prompting? |
| Context limitations | Exceeds practical context limits? |
| Tool behavior | Assumes tool behaviors that don't match reality |
| User interaction | Expects user behavior that won't happen |
| Permission model | Assumes autonomy levels requiring config changes? |
| Model selection | Appropriate model for task complexity? |

**Full Prompt Template:**

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

---

### Lens 3: Robustness Critic

**Core question:** "What breaks this design?"

**Lens-specific field:** `Scenario` (how this manifests in practice)

**Analysis vectors:**

| Vector | Examines |
|--------|----------|
| Edge cases | Inputs/scenarios not covered |
| Error handling | What happens on failure, silent failures |
| State transitions | Workflow interrupted mid-process |
| Integration points | Handoffs between components could fail |
| Underspecification | Guidance too vague to implement consistently |
| Failure recovery | How user knows something went wrong, how to recover |
| Security risks | Credential exposure, destructive ops, input sanitization |
| Testability | How to verify this works, can it be tested incrementally |

**Full Prompt Template:**

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

---

### Lens 4: Scope Minimalist

**Core question:** "What can be cut from this design?"

**Lens-specific field:** `Verdict` (Keep / Cut / Simplify)

**Analysis vectors:**

| Vector | Examines |
|--------|----------|
| Essential vs. nice-to-have | Absolute minimum viable version |
| YAGNI violations | Solves problems that don't exist yet |
| Complexity audit | Abstractions that add overhead without value |
| Redundancy | Duplicated elements that could be unified |
| Cognitive load | How many concepts must someone learn |
| Incremental value | 20% that delivers 80% of benefit |
| Alternative approaches | Simpler way to achieve same goal? |
| Operational cost | Token costs, latency, maintenance burden |

**Full Prompt Template:**

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

---

## Arbiter Specification

**Role:** Synthesize 4 lens outputs into actionable prioritized findings.

**Inputs:**
- All 4 lens outputs (full markdown)
- Original target document (for reference)
- Artifact type and design stage

**Core responsibilities:**

1. **Convergence detection** — Identify findings that appear in multiple lenses (potentially with different vocabulary)
   - Use semantic reasoning to detect same underlying issue across lenses
   - Group convergent findings and note which lenses flagged them
   - Explain WHY findings are considered the same issue

2. **Unique insight extraction** — Identify valuable findings that only one lens caught
   - These may be lens-specific expertise (e.g., only Spec Auditor catches deprecated patterns)

3. **Prioritization** — Rank all findings by:
   - Convergence count (more lenses = higher priority)
   - Severity (Critical > Major > Minor)
   - Effort to fix (Low effort fixes get priority boost)
   - Classification confidence (Verified > Inferred > Assumed)

4. **Verdict synthesis** — Produce overall assessment:
   - Ship readiness: ready / needs_work / major_revision
   - Critical path: what MUST be fixed
   - Deferred items: what can wait for later iteration

**Full Prompt Template:**

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

**Output format:** Structured content for both `audit-report.md` and `audit-impl-spec.json`.

---

## Output Format: audit-report.md

```markdown
# Claude Tool Audit: [Target Name]

**Artifact type:** [type]
**Design stage:** [early / working / final]
**Mode:** [full / quick]
**Date:** YYYY-MM-DD
**Warnings:** [Any caveats, e.g., fallback specs used]

---

## Executive Summary

[2-3 sentences: Overall assessment, biggest risks, verdict]

---

## Convergent Findings (Highest Priority)

Issues flagged by multiple lenses — highest confidence problems.

| Finding | Lenses | Severity | Element | Classification |
|---------|--------|----------|---------|----------------|
| [Issue] | Spec + Behavioral | Critical | `frontmatter.license` | Verified |
| [Issue] | Robustness + Minimalist | Major | `workflow.error-handling` | Inferred |

### [Finding 1 Title]
- **What:** [Description]
- **Why it matters:** [Impact]
- **Evidence:** [Quote from design]
- **Suggested fix:** [Recommendation]

---

## Prioritized Recommendations

| Priority | Finding | Fix | Effort | Convergence | Classification |
|----------|---------|-----|--------|-------------|----------------|
| P1 | [title] | [action] | Low | 3 lenses | Verified |
| P2 | [title] | [action] | Medium | 2 lenses | Verified |
| P3 | [title] | [action] | Low | 1 lens | Inferred |

---

## Lens-Specific Insights

Unique findings from individual lenses (not convergent but valuable).

### Spec Auditor Only
- [Finding not caught by other lenses]

### Behavioral Realist Only
- ...

### Robustness Critic Only
- ...

### Scope Minimalist Only
- ...

---

## What Was NOT Assessed

- [Elements or sections explicitly out of scope]
- [Limitations due to design stage or document size]

---

## Verdict

**Ship readiness:** [ready / needs_work / major_revision]

**Critical path:** [What MUST be fixed before proceeding]

**Deferred items:** [What can wait for later iteration]

---

<details>
<summary>Raw Lens Outputs</summary>

### Spec Auditor
[Full output]

### Behavioral Realist
[Full output]

### Robustness Critic
[Full output]

### Scope Minimalist
[Full output]

</details>
```

---

## Output Format: audit-impl-spec.json

```json
{
  "audit_metadata": {
    "target": "docs/plans/my-skill-design.md",
    "artifact_type": "skill",
    "stage": "working_draft",
    "mode": "full",
    "date": "2026-01-09",
    "warnings": ["Using fallback specs - claude-code-guide unavailable"]
  },
  "scope": {
    "assessed": ["frontmatter", "workflow", "inputs", "outputs", "procedure"],
    "not_assessed": ["examples section - not present in design"],
    "confidence": "full"
  },
  "findings": [
    {
      "id": "F001",
      "title": "Undocumented frontmatter field",
      "element": "frontmatter.license",
      "severity": "major",
      "classification": "verified",
      "convergence": ["spec_auditor", "behavioral_realist"],
      "issue": "The 'license' field is not documented in official Claude Code specs.",
      "evidence": "```yaml\nlicense: MIT\n```",
      "status": "open"
    },
    {
      "id": "F002",
      "title": "Missing timeout handling",
      "element": "workflow.api-call",
      "severity": "critical",
      "classification": "verified",
      "convergence": ["robustness_critic"],
      "issue": "No error handling specified for API timeout scenarios.",
      "evidence": "Step 3 calls external API but has no timeout or retry logic.",
      "status": "open"
    }
  ],
  "recommendations": [
    {
      "priority": "P1",
      "finding_id": "F002",
      "action": "Add timeout handling with user-visible error message",
      "effort": "low",
      "acceptance_criteria": [
        "Timeout value specified (recommend 30s)",
        "Error message defined for user",
        "Recovery path documented"
      ]
    },
    {
      "priority": "P2",
      "finding_id": "F001",
      "action": "Remove 'license' field from frontmatter",
      "effort": "low",
      "acceptance_criteria": [
        "Field removed from YAML frontmatter",
        "No other undocumented fields present"
      ]
    }
  ],
  "verdict": {
    "ship_readiness": "needs_work",
    "critical_path": ["F002"],
    "deferred": [],
    "summary": "Design has one critical gap (timeout handling) that must be addressed."
  }
}
```

---

## Edge Case Handling

### EC1: Multiple Artifact Types (Plugin)
**Scenario:** Design describes a plugin with skills, hooks, and MCP server.
**Handling:** Plugin-aware mode — recognize plugin as composite type, query specs for ALL component types, inject all relevant specs into lenses.

### EC2: Unclear Artifact Type
**Scenario:** Design is vague about what it's building.
**Handling:** Propose options with descriptions:
> "This design doesn't specify an artifact type. It could be:
> - **Skill**: Guidance/workflow for Claude to follow
> - **Hook**: Validates/modifies tool behavior
> - **Plugin**: Package containing skills, hooks, MCP servers
> - **Command**: User-invoked slash action
> - **Subagent**: Specialized Task tool agent
>
> Which should I audit for?"

**STOP** until user confirms.

### EC3: Very Long Design (>50K tokens)
**Scenario:** Design document exceeds reasonable prompt size.
**Handling:** Hierarchical audit with two phases:

**Phase 1: Structure Pass**
Each lens receives ONLY:
- Document title and frontmatter
- All headings (H1-H4) with line numbers
- First paragraph of each major section
- Any sections named: Error, Security, Edge Case, Constraint, Assumption

Lenses output:
- 2-3 sections flagged as HIGH_RISK with rationale
- Confidence level for structure-only assessment

**High-Risk Indicators by Lens:**
| Lens | Flags as High-Risk |
|------|-------------------|
| Spec Auditor | Sections mentioning frontmatter, configuration, structure |
| Behavioral Realist | Sections mentioning state, context, multi-step workflows |
| Robustness Critic | Sections mentioning error handling, edge cases, security |
| Scope Minimalist | Sections with many subsections, complex workflows |

**Phase 2: Deep Dive**
- Union of all lens HIGH_RISK flags (deduplicated)
- Maximum 5 sections receive full analysis
- Each lens receives full content of flagged sections only
- Standard lens output format applies

**Output Annotation:**
```markdown
## Audit Coverage
- **Mode:** Hierarchical (document exceeded 50K tokens)
- **Structure-only sections:** [list]
- **Deep-dive sections:** [list with rationale]
- **Limitation:** Findings may exist in structure-only sections
```

### EC4: No Artifact Type (Conceptual)
**Scenario:** Design is purely conceptual, no specific Claude Code artifact.
**Handling:**
1. Suggest artifact mapping with options
2. If user can't choose: "This concept isn't ready for audit. Consider using `/brainstorming` to develop it into a concrete design first."
3. **STOP** — do not audit conceptual documents

### EC5: Partial Design (Early Draft)
**Scenario:** Design has major sections missing.
**Handling:** Stage-appropriate audit:
- **Early draft:** Focus on direction, flag major gaps as "incomplete" not "wrong"
- **Working draft:** Full audit, gaps noted with "needs completion"
- **Final design:** Full rigor, all gaps are findings

### EC6: claude-code-guide Unavailable
**Scenario:** Agent times out or returns errors.
**Handling:**
1. Load `references/fallback-specs.md`
2. Add warning to output: "⚠️ This audit used cached specifications (last updated: YYYY-MM-DD). Live spec lookup failed."
3. Proceed with audit using fallback specs

---

## Workflow Variants

### Full Mode (Default)

**Invocation:** `/claude-tool-audit <path>` or `/claude-tool-audit <path> --full`

**Components:**
- 4 lenses (Spec Auditor, Behavioral Realist, Robustness Critic, Scope Minimalist)
- Arbiter synthesis
- Both outputs (audit-report.md + audit-impl-spec.json)

**Cost:** ~5 subagent invocations (4 lenses + 1 Arbiter)

**Use when:** Final design review, comprehensive audit needed

### Quick Mode

**Invocation:** `/claude-tool-audit <path> --quick`

**Components:**
- 2 lenses only (Spec Auditor, Behavioral Realist)
- No Arbiter (main thread does simple merge)
- Single condensed output (no JSON impl-spec)

**Cost:** ~2 subagent invocations

**Use when:** Fast sanity check, early draft review, time-constrained

**Quick mode output structure:**

```markdown
# Quick Audit: [Target Name]

**Mode:** Quick (Spec + Behavioral)
**Artifact type:** [type]
**Date:** YYYY-MM-DD

## Spec Compliance
[Condensed Spec Auditor findings]

## Behavioral Feasibility
[Condensed Behavioral Realist findings]

## Verdict
**Likely to work?** Yes / Needs attention / Major issues
**Key concerns:** [Top 2-3 issues if any]
**Recommendation:** Proceed to full audit / Address issues first / Good to implement
```

---

## Skill Structure

```
.claude/skills/claude-tool-audit/
├── SKILL.md                          # Main orchestrator skill
├── lenses/
│   ├── spec-auditor.md               # Lens 1 prompt template
│   ├── behavioral-realist.md         # Lens 2 prompt template
│   ├── robustness-critic.md          # Lens 3 prompt template
│   └── scope-minimalist.md           # Lens 4 prompt template
├── arbiter/
│   └── synthesis-prompt.md           # Arbiter prompt template
├── references/
│   └── fallback-specs.md             # Cached specs if claude-code-guide unavailable
└── examples/                         # Deferred to v1.1
    ├── skill-audit-full.md           # Deferred to v1.1
    └── hook-audit-quick.md           # Deferred to v1.1
```

### File Responsibilities

| File | Purpose |
|------|---------|
| `SKILL.md` | Orchestrator workflow, procedure, decision points, inputs/outputs |
| `lenses/*.md` | Prompt templates (Spec Auditor uses `{{ARTIFACT_SPECS}}`; others have embedded verified patterns) |
| `arbiter/synthesis-prompt.md` | Instructions for convergence detection and prioritization |
| `references/fallback-specs.md` | Minimal embedded specs for offline/fallback operation |
| `examples/*.md` | Worked examples demonstrating output format and value (deferred to v1.1) |

---

## Worked Example: Hook Design Audit (Full Mode)

This example demonstrates the complete audit workflow from target document through final output.

### Target Document (excerpt)

```yaml
# Validation Hook Design

**Artifact:** Hook
**Purpose:** Block dangerous bash commands before execution

## Configuration
- Event: PreToolUse
- Matcher: Bash
- Exit code 1 to block dangerous commands

## Dangerous Patterns
- rm -rf
- DROP TABLE
- format c:

## Implementation
Script reads stdin JSON, checks command against patterns,
exits with appropriate code.
```

---

### Lens Outputs (excerpts)

**Spec Auditor:**
```markdown
### Finding 1: Incorrect exit code semantics
- **Element:** behavior.exit-codes
- **Issue:** Design specifies exit code 1 to block, but hooks use exit code 2 for blocking
- **Evidence:** "Exit code 1 to block dangerous commands"
- **Severity:** Critical
- **Classification:** Verified
- **Requirement:** EXIT_CODES table in hook spec: 2=block, 1=non-blocking error
```

**Behavioral Realist:**
```markdown
### Finding 1: Exit code will not block as intended
- **Element:** behavior.exit-codes
- **Issue:** Exit code 1 logs error but allows command to proceed
- **Evidence:** "Exit code 1 to block dangerous commands"
- **Severity:** Critical
- **Classification:** Verified
- **Mitigation:** Change to exit code 2 for blocking behavior
```

**Robustness Critic:**
```markdown
### Finding 1: Pattern matching is bypassable
- **Element:** workflow.pattern-matching
- **Issue:** Substring matching allows bypass via: r\m -rf, rm  -rf (double space)
- **Evidence:** "checks command against patterns"
- **Severity:** Major
- **Classification:** Inferred
- **Scenario:** Attacker uses unicode lookalikes or whitespace variations
```

**Scope Minimalist:**
```markdown
### Finding 1: Windows pattern unnecessary
- **Element:** scope.patterns
- **Issue:** "format c:" is Windows-only; Claude Code runs on macOS/Linux
- **Evidence:** Listed in Dangerous Patterns
- **Severity:** Minor
- **Classification:** Verified
- **Verdict:** Cut
```

---

### Arbiter Synthesis (excerpt)

```markdown
### Convergent Findings

#### C1: Exit code 1 does not block commands
- **Lenses:** Spec Auditor, Behavioral Realist
- **Why convergent:** Both identify same issue — exit code semantics incorrect. Spec Auditor cites the spec violation, Behavioral Realist explains the runtime consequence.
- **Unified severity:** Critical
- **Element:** behavior.exit-codes
- **Issue:** Design uses exit 1 to block but hooks require exit 2 for blocking. Exit 1 logs an error but allows the command to execute, defeating the hook's purpose entirely.
- **Evidence:** "Exit code 1 to block dangerous commands"

### Unique Insights

#### U1: Pattern matching bypass risk
- **Lens:** Robustness Critic
- **Why valuable:** Security-critical gap not covered by other lenses. Substring matching is naive for security context.

#### U2: Unnecessary Windows pattern
- **Lens:** Scope Minimalist
- **Why valuable:** Minor scope creep, easy to remove.

### Prioritized Recommendations

| Priority | Finding | Action | Effort | Confidence |
|----------|---------|--------|--------|------------|
| P1 | C1 | Change exit code from 1 to 2 | Low | High (2 lenses, verified) |
| P2 | U1 | Use regex with word boundaries, not substring | Medium | Medium (1 lens, inferred) |
| P3 | U2 | Remove "format c:" pattern | Low | High (1 lens, verified) |

### Verdict
- **Ship readiness:** needs_work
- **Critical path:** C1 (exit code) — hook will not function as designed
- **Deferred:** None — all findings are low-to-medium effort
- **Summary:** Design has one critical flaw (exit code semantics) that would make the hook ineffective. Fix is trivial. Secondary concern about pattern bypass robustness should be addressed for security-critical use case.
```

---

### Output Files

**audit-report.md:** Contains human-readable report with sections above, plus raw lens outputs in collapsible `<details>` block.

**audit-impl-spec.json:**
```json
{
  "audit_metadata": {
    "target": "validation-hook-design.md",
    "artifact_type": "hook",
    "stage": "working_draft",
    "mode": "full",
    "date": "2026-01-09"
  },
  "findings": [
    {"id": "C1", "element": "behavior.exit-codes", "severity": "critical", "convergence": ["spec_auditor", "behavioral_realist"], "status": "open"},
    {"id": "U1", "element": "workflow.pattern-matching", "severity": "major", "convergence": ["robustness_critic"], "status": "open"},
    {"id": "U2", "element": "scope.patterns", "severity": "minor", "convergence": ["scope_minimalist"], "status": "open"}
  ],
  "verdict": {"ship_readiness": "needs_work", "critical_path": ["C1"]}
}
```

---

## Implementation Notes

### Prompt Template Placeholders

Each lens prompt template uses these injection points:

| Placeholder | Source | Content |
|-------------|--------|---------|
| `{{TARGET_CONTENT}}` | User-provided path | Full text of design document |
| `{{ARTIFACT_TYPE}}` | Detected or confirmed | skill / plugin / hook / command / subagent |
| `{{DESIGN_STAGE}}` | User-specified | early / working / final |
| `{{ARTIFACT_SPECS}}` | claude-code-guide or fallback | Official specs for artifact type |

### Subagent Configuration

| Subagent | Type | Model | Max Turns |
|----------|------|-------|-----------|
| Spec Auditor | Task (general-purpose) | sonnet | 10 |
| Behavioral Realist | Task (general-purpose) | sonnet | 10 |
| Robustness Critic | Task (general-purpose) | sonnet | 10 |
| Scope Minimalist | Task (general-purpose) | sonnet | 10 |
| Arbiter | Task (general-purpose) | sonnet | 15 |
| claude-code-guide | Task (claude-code-guide) | haiku | 5 |

### Error Handling

| Error | Recovery |
|-------|----------|
| Lens fails to return structured output | Re-prompt with explicit format reminder |
| Lens times out | Note in output, proceed with available lenses |
| Arbiter fails | Fall back to main thread doing simple merge |
| All lenses fail | Abort audit, report error to user |

### Performance Expectations

| Mode | Subagents | Expected Duration | Token Cost |
|------|-----------|-------------------|------------|
| Full | 5 (4 lenses + Arbiter) | 3-5 minutes | ~50K tokens |
| Quick | 2 (2 lenses) | 1-2 minutes | ~20K tokens |

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2026-01-09 | Initial design from brainstorming session |
| 0.2 | 2026-01-09 | Added full lens prompt templates, Arbiter prompt with semantic convergence, claude-code-guide query template, mode-conditional DoD, hierarchical audit specification, worked example |
| 0.3 | 2026-01-09 | Replaced lens placeholders with verified embedded patterns; added Quality Standards section referencing semantic-quality-addendum and domain-annexes; added Mode Detection section for --quick flag parsing; marked examples/ as deferred to v1.1 |
