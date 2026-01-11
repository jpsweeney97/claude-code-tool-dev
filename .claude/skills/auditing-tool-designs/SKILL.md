---
name: auditing-tool-designs
description: Audits tool designs (skills, plugins, hooks, commands, subagents) using 4 parallel lenses with Arbiter synthesis. Identifies spec violations, behavioral mismatches, failure modes, and scope creep before implementation.
model: claude-sonnet-4-20250514
---

# auditing-tool-designs

## Primary Goal

Audit Claude Code tool design documents (skills, plugins, hooks, commands, subagents) using 4 specialized lenses that create productive tension, synthesize findings via an Arbiter, and produce actionable outputs for both humans and Claude.

## Non-Goals

1. **Not implementation validation** — Does not execute code or run tests; audits design documents only
2. **Not security audit of running systems** — Does not probe live services or credentials
3. **Not code review** — Does not review implementation code, only design documents
4. **Not a replacement for brainstorming** — Does not help crystallize vague concepts into designs
5. **Not a general document editor** — Does not fix issues, only identifies them
6. **Not for trivial designs** — Designs under 100 words have insufficient content to audit meaningfully

## Quality Standards

This skill follows:
- `skills-semantic-quality-addendum.md` — semantic minimums (intent, constraints, decision points, verification)
- `skills-domain-annexes.md` — auditing annex + pipelines annex

Key requirements:
- **Evidence-backed claims**: Every finding includes path + query + observation
- **Claim strength discipline**: Sampled vs global coverage disclosed; confidence labeled
- **Calibration honesty**: Verified/Inferred/Assumed labeling required
- **Safe-by-default**: Read-only analysis; produces reports, not changes

---

## When to Use

Use this skill when:
- You have a **design document** for a Claude Code tool (skill, plugin, hook, command, subagent) and want to identify issues before implementation
- You want **multiple analytical perspectives** applied systematically (compliance, feasibility, robustness, scope)
- You need **convergent findings** — issues flagged by multiple lenses carry higher confidence
- You want **actionable output** — both a human-readable report and a JSON spec Claude can use for implementation

**Activation signals:**
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

**STOP conditions:**
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
| Network available | Fallback specs are local; no network required |

### Constants

| Constant | Value | Purpose |
|----------|-------|---------|
| `MIN_VERIFIED_LENSES` | 2 | Minimum lenses that must pass verification to proceed |
| `READ_INSTRUCTION_BLOCK` | See below | Standardized instruction for lenses to read target file |

**READ_INSTRUCTION_BLOCK:**
```
**File:** {{TARGET_PATH}}

⚠️ **MANDATORY FIRST STEP:** Read this file using the Read tool before any analysis.
Do not proceed without reading the entire file.

If you cannot read the file, output only:
"LENS FAILURE: Cannot read {{TARGET_PATH}}: [error reason]"
```

### Mode Detection

Parse `$ARGUMENTS` to detect mode:
- If arguments contain `--quick` or `-q`: Quick mode (2 lenses, no Arbiter)
- Otherwise: Full mode (4 lenses + Arbiter)

Extract target path by removing the flag from arguments.

**Examples:**
- `/auditing-tool-designs docs/plans/my-design.md` → Full mode
- `/auditing-tool-designs docs/plans/my-design.md --quick` → Quick mode
- `/auditing-tool-designs --quick docs/plans/my-design.md` → Quick mode

### Context Assessment

Context is gathered interactively via AskUserQuestion before lens execution. See [references/context-assessment.md](references/context-assessment.md) for the full framework.

**Questions asked:**
1. Deployment scope (Personal/Team/Public)
2. Input trust level (Trusted/Partial/Untrusted)
3. Failure impact (Low/Medium/High)

**Output:** Calibration level (Light/Standard/Deep) that adjusts severity thresholds across all lenses.

---

## Outputs

### Output Location

All outputs are written to `docs/audits/` (relative to project root). Create the directory if it doesn't exist.

### Artifacts

| Artifact | Format | Purpose |
|----------|--------|---------|
| `docs/audits/audit-report.md` | Markdown | Human-readable report with convergent findings, recommendations, verdict |
| `docs/audits/audit-impl-spec.json` | JSON | Machine-parseable spec for Claude to use during implementation |

### Definition of Done

**Full Mode:**
1. Both output files exist (`docs/audits/audit-report.md`, `docs/audits/audit-impl-spec.json`)
2. All 4 lens outputs contain structured findings with Element/Issue/Evidence/Severity/Classification fields
3. Arbiter synthesis identifies convergent findings (or explicitly states none found)
4. Prioritized recommendations ranked P1/P2/P3 with effort estimates
5. Verdict includes ship_readiness: ready | needs_work | major_revision

**Quick Mode:**
1. Single output file exists (`docs/audits/quick-audit.md`)
2. Both lens outputs (Spec Auditor, Behavioral Realist) contain structured findings
3. Main thread merge produces combined findings list
4. Verdict includes likely_to_work: yes | needs_attention | major_issues

---

## Procedure

### Step 1: Read target document
Load the design document specified by the user.
- **Success:** Document content loaded
- **Failure:** File not found or unreadable → STOP with error

### Step 2: Detect artifact type
Scan for signals (SKILL.md, plugin.json, hook events, etc.).
- **Success:** Clear artifact type detected
- **Failure:** Unclear → Propose options and **STOP. Ask user to confirm artifact type.**

### Step 2.5: Assess context

Gather context to calibrate severity across all lenses.

Use AskUserQuestion tool with 3 questions:

**Q1:** "Who will use this {{ARTIFACT_TYPE}}?"
- Personal (just me)
- Team (internal users)
- Public (external consumers)

**Q2:** "Who controls the inputs this tool will process?"
- Developer-controlled (config files, env vars, version-controlled data)
- Internal users (team members, authenticated users)
- External/untrusted (user uploads, public API, external data)

**Q3:** "What happens if this tool has a bug or security issue?"
- Learning/experiment (no real impact)
- Internal tool (team inconvenience)
- Production system (data loss, security breach, outage)

Calculate calibration level per `references/context-assessment.md`.

- **Success:** `{{CONTEXT_ASSESSMENT}}` and `{{SEVERITY_CALIBRATION}}` populated
- **Failure:** User cannot answer → Use "Standard" calibration with warning

### Step 3: Confirm design stage
Check if user specified early/working/final.
- **Success:** Stage confirmed
- **Failure:** Not specified → **STOP. Ask: "Is this an early draft, working draft, or final design?"**

### Step 4: Check document size
If > 50K tokens, switch to hierarchical audit mode.
- **Success:** Size determined, mode selected
- **Failure:** N/A

### Step 5: Query domain knowledge
Invoke claude-code-guide agent with:
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
- **Success:** Specs returned → inject as `{{ARTIFACT_SPECS}}` into lens prompts (Step 6)
- **Failure:** Timeout/error → Load `references/fallback-specs.md` as `{{ARTIFACT_SPECS}}` and add warning

### Step 6: Build lens prompts
Inject specs into 4 lens prompt templates from `lenses/` directory.
- **Success:** All prompts populated with {{ARTIFACT_TYPE}}, {{ARTIFACT_SPECS}}, {{TARGET_CONTENT}}, {{CONTEXT_ASSESSMENT}}, {{SEVERITY_CALIBRATION}}
- **Failure:** Template not found → STOP with error

### Step 7: Execute lenses in parallel
Launch Task tool calls simultaneously:
- **Full mode:** 4 lenses (Spec Auditor, Behavioral Realist, Robustness Critic, Scope Minimalist)
- **Quick mode:** 2 lenses (Spec Auditor, Behavioral Realist only)

Use `subagent_type: "general-purpose"` for each lens.
- **Success:** All lens tasks launched
- **Failure:** Task tool error → Retry once, then STOP

### Step 8: Collect lens outputs
Wait for all lenses to complete.
- **Success:** All outputs received with valid structure
- **Failure:** Lens output malformed → Note in report, continue with valid outputs

### Step 9: Execute Arbiter (Full mode only)
Launch synthesis subagent with all lens outputs using `arbiter/synthesis-prompt.md`.
- **Success:** Arbiter returns convergent findings and verdict
- **Failure:** Arbiter error → Main thread performs simple merge as fallback

### Step 10: Generate outputs
Create `docs/audits/` directory if it doesn't exist, then write output files:
- **Full mode:** `docs/audits/audit-report.md` and `docs/audits/audit-impl-spec.json`
- **Quick mode:** `docs/audits/quick-audit.md` only
- **Success:** Files written successfully
- **Failure:** Write error → Output to conversation instead

### Step 11: Present summary
Show executive summary and verdict to user.
- **Success:** User sees summary
- **Failure:** N/A

---

## Decision Points

### DP1: Artifact Type Detection
**Observable trigger:** Document signals (SKILL.md, plugin.json, hook events, etc.)
- If clear: proceed with detected type
- If unclear: propose options and **STOP** until user confirms

### DP2: Design Stage Confirmation
**Observable trigger:** User's explicit specification or lack thereof
- If specified: apply stage-appropriate rigor
- If not: **STOP** and ask: "What stage is this design? Early draft, Working draft, or Final design?"

### DP2.5: Context Calibration
**Observable trigger:** User answers to 3 context questions
- If score 3-5: Light calibration (relaxed severity)
- If score 6-7: Standard calibration (normal thresholds)
- If score 8-9: Deep calibration (strict thresholds)
- If user cannot answer: Standard calibration with warning

### DP3: Document Size
**Observable trigger:** Token count > 50K
- If exceeded: switch to hierarchical audit
- If not: proceed with standard audit

### DP4: Domain Knowledge Availability
**Observable trigger:** claude-code-guide response status
- If success: inject live specs
- If failure: use fallback specs with warning

### DP5: Multiple Artifact Types (Plugin)
**Observable trigger:** Plugin contains multiple component types
- If composite: query specs for ALL component types
- If single: query specs for single type

### DP6: Quick vs Full Mode
**Observable trigger:** `--quick` or `-q` in `$ARGUMENTS`
- If present: run 2 lenses, no Arbiter, condensed output
- If absent: run 4 lenses + Arbiter, full output

### DP7: Conceptual Design (No Artifact)
**Observable trigger:** No artifact type determinable
- If conceptual: suggest `/brainstorming` and **STOP**
- If concrete: proceed with audit

---

## Verification

### Quick Check
**Check:** Output files exist and contain required sections.
**Full mode:** Run `grep -c "## Convergent Findings\|## Verdict" docs/audits/audit-report.md`. Expected: 2 matches.
**Quick mode:** Run `grep -c "## Verdict" docs/audits/quick-audit.md`. Expected: 1 match.
**If check fails:** Do not mark complete; review lens outputs for malformed structure.

### Deep Check
**Check:** Findings cite actual evidence from target document.
**Method:** Select 2-3 findings at random. For each:
1. Locate the `Evidence` field quote in the original target document
2. Verify `Element` uses taxonomy pattern (e.g., `frontmatter.*`, `workflow.*`)
**Expected:** All sampled findings have verifiable evidence; Element follows taxonomy.
**If check fails:** Flag findings as potentially hallucinated; re-run lens with stricter format instructions.

### Hierarchical Audit Verification (when applicable)
**Check:** Output declares coverage scope.
**Method:** Verify `## Audit Coverage` section exists with `Structure-only sections` and `Deep-dive sections` lists.
**Expected:** Lists are non-empty and rationale is provided for deep-dive selection.

---

## Troubleshooting

### Lens outputs are unstructured or incomplete
**Symptoms:** Missing tables, prose-only findings, no Element/Issue/Evidence fields.
**Likely causes:** Lens prompt not followed correctly; target document too vague.
**Fix:** Re-run failing lens with explicit format reminder; check if target has sufficient structure.

### No convergent findings despite multiple lenses
**Symptoms:** Arbiter reports 0 convergence; all findings "unique to one lens."
**Likely causes:** Design has no significant issues (rare), or lenses used incompatible terminology.
**Fix:** Check element taxonomy consistency; review lens outputs for semantic similarity Arbiter missed.

### claude-code-guide times out or returns empty
**Symptoms:** Warning about using fallback specs.
**Likely causes:** Network issues; agent overload; malformed query.
**Fix:** Audit proceeds with fallback specs; retry after resolving issues if accuracy critical.

### Artifact type detection is wrong
**Symptoms:** Lenses apply wrong specs (e.g., hook specs for skill design).
**Likely causes:** Ambiguous document signals; user didn't correct detection.
**Fix:** Re-run with explicit artifact type specified by user.

### Anti-Pattern: User asks to audit implementation code
**Symptoms:** Target is `.py`, `.ts`, or similar code file.
**Fix:** Redirect to code review skills; this skill audits designs, not implementations.

---

## Lens Specifications

### Universal Output Schema

All lenses use this structure for Arbiter compatibility:

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

## Summary
- Total findings: X (Y Critical, Z Major, W Minor)
```

### Element Taxonomy

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

### Lens Prompts

Full lens prompts are in `lenses/` directory:
- `lenses/spec-auditor.md` — Spec compliance (lens-specific field: `Requirement`)
- `lenses/behavioral-realist.md` — Behavioral feasibility (lens-specific field: `Mitigation`)
- `lenses/robustness-critic.md` — Failure modes (lens-specific field: `Scenario`)
- `lenses/scope-minimalist.md` — Scope creep (lens-specific field: `Verdict`)

---

## Output Formats

Output templates are in [references/output-templates.md](references/output-templates.md):

| Template | Purpose |
|----------|---------|
| `audit-report.md` | Full mode human-readable report with convergent findings |
| `audit-impl-spec.json` | Machine-parseable spec for implementation |
| `quick-audit.md` | Quick mode condensed output |

---

## Edge Case Handling

### EC1: Multiple Artifact Types (Plugin)
**Scenario:** Design describes a plugin with skills, hooks, and MCP server.
**Handling:** Plugin-aware mode — query specs for ALL component types, inject all relevant specs into lenses.

### EC2: Unclear Artifact Type
**Scenario:** Design is vague about what it's building.
**Handling:** Propose options:
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
**Handling:** Hierarchical audit:

**Phase 1: Structure Pass** — Each lens receives only headings, frontmatter, first paragraphs, and risk-indicator sections.

**Phase 2: Deep Dive** — Union of HIGH_RISK flags from all lenses (max 5 sections) receive full analysis.

**Output annotation:**
```markdown
## Audit Coverage
- **Mode:** Hierarchical (document exceeded 50K tokens)
- **Structure-only sections:** [list]
- **Deep-dive sections:** [list with rationale]
```

### EC4: No Artifact Type (Conceptual)
**Scenario:** Design is purely conceptual, no specific Claude Code artifact.
**Handling:** Suggest `/brainstorming` to develop concept into concrete design. **STOP** — do not audit conceptual documents.

### EC5: Partial Design (Early Draft)
**Scenario:** Design has major sections missing.
**Handling:** Stage-appropriate audit:
- **Early draft:** Focus on direction, flag gaps as "incomplete" not "wrong"
- **Working draft:** Full audit, gaps noted with "needs completion"
- **Final design:** Full rigor, all gaps are findings

### EC6: claude-code-guide Unavailable
**Scenario:** Agent times out or returns errors.
**Handling:**
1. Load `references/fallback-specs.md`
2. Add warning: "⚠️ This audit used cached specifications. Live spec lookup failed."
3. Proceed with audit

---

## Workflow Variants

### Full Mode (Default)

**Invocation:** `/auditing-tool-designs <path>` or `/auditing-tool-designs <path> --full`

**Components:**
- 4 lenses (Spec Auditor, Behavioral Realist, Robustness Critic, Scope Minimalist)
- Arbiter synthesis
- Both outputs (audit-report.md + audit-impl-spec.json)

**Cost:** ~5 subagent invocations

### Quick Mode

**Invocation:** `/auditing-tool-designs <path> --quick`

**Components:**
- 2 lenses only (Spec Auditor, Behavioral Realist)
- No Arbiter (main thread does simple merge)
- Single condensed output (quick-audit.md)

**Cost:** ~2 subagent invocations

**Use when:** Fast sanity check, early draft review, time-constrained
