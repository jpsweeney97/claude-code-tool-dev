# skill-wizard Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create an interactive skill that guides authors through spec-compliant SKILL.md creation with inline validation.

**Architecture:** A wizard skill with 8 section-specific checklists in `references/`, 3 template files in `templates/`, and a ~500 line SKILL.md that orchestrates discovery → risk assessment → section drafting → cross-section validation → final cleanup. Session recovery via incremental writing to the target SKILL.md.

**Tech Stack:** Pure markdown skill with Claude Code's built-in tools (Read, Write, Glob, Grep, AskUserQuestion). No external dependencies.

---

## Task 1: Create Directory Structure and SKILL.md Skeleton

**Files:**
- Create: `.claude/skills/skill-wizard/SKILL.md`
- Create: `.claude/skills/skill-wizard/references/` (directory)
- Create: `.claude/skills/skill-wizard/templates/` (directory)

**Step 1: Create the skill directory**

```bash
mkdir -p .claude/skills/skill-wizard/references
mkdir -p .claude/skills/skill-wizard/templates
```

**Step 2: Verify directories exist**

Run: `ls -la .claude/skills/skill-wizard/`
Expected: `references` and `templates` directories listed

**Step 3: Create SKILL.md skeleton with frontmatter**

Create `.claude/skills/skill-wizard/SKILL.md`:

```markdown
---
name: skill-wizard
description: >
  Guided skill creation with spec compliance validation. Use when creating
  a new Claude Code skill from scratch, when you want interactive authoring
  with inline validation, or when you need help meeting the skills-as-prompts
  spec requirements. Walks through all 8 required sections, generates draft
  content, validates against structural and semantic quality criteria, and
  produces a compliant SKILL.md.
license: MIT
metadata:
  version: "1.0.0"
  category: meta-skills
  risk_tier: low
  spec_version: "skills-as-prompts-strict-v1"
  timelessness_score: 8
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - AskUserQuestion
---

# Skill Wizard

<!-- Sections will be added in Task 6 -->
```

**Step 4: Verify SKILL.md created**

Run: `head -20 .claude/skills/skill-wizard/SKILL.md`
Expected: Frontmatter with `name: skill-wizard`

**Step 5: Commit**

```bash
git add .claude/skills/skill-wizard/
git commit -m "feat(skill-wizard): create directory structure and frontmatter"
```

---

## Task 2: Create Core Reference Files

**Files:**
- Create: `.claude/skills/skill-wizard/references/spec-requirements.md`
- Create: `.claude/skills/skill-wizard/references/section-order.md`
- Create: `.claude/skills/skill-wizard/references/risk-tier-guide.md`

### Step 1: Write the spec-requirements.md file

Create `.claude/skills/skill-wizard/references/spec-requirements.md`:

```markdown
# Spec Requirements Reference

Source: `skills-as-prompts-strict-spec.md` + `skills-semantic-quality-addendum.md`
Spec version: skills-as-prompts-strict-v1

## Requirement Levels

| Level | Meaning |
|-------|---------|
| **MUST** | Blocks approval; skill cannot proceed until fixed |
| **SHOULD** | Warns but allows continue; shown in compliance summary |
| **HIGH-MUST** | MUST for High-risk skills; WARN for Medium; skip for Low |
| **SEMANTIC** | Content quality check from semantic addendum |

## Core Invariants (8)

1. **All 8 sections present**: When to use, When NOT to use, Inputs, Outputs, Procedure, Decision points, Verification, Troubleshooting
2. **Objective DoD**: Outputs has checkable condition (not "verify it works")
3. **STOP/ask exists**: Procedure has explicit pause for missing inputs
4. **>=2 decision points**: With observable triggers (or justified exception)
5. **Quick check exists**: Verification has concrete check with expected result
6. **>=1 troubleshooting entry**: With symptoms, causes, next steps
7. **Assumptions declared**: Tools/network/permissions in Constraints
8. **Safe default**: Ask-first for breaking/destructive actions

## Tier 1: Normative Fail Codes

| Fail Code | Description |
|-----------|-------------|
| `FAIL.missing-content-areas` | One or more of 8 required sections absent |
| `FAIL.no-objective-dod` | Outputs lack objective, checkable DoD condition |
| `FAIL.no-stop-ask` | No explicit STOP/ask step for missing inputs |
| `FAIL.no-quick-check` | Verification lacks concrete quick check |
| `FAIL.too-few-decision-points` | <2 decision points without justified exception |
| `FAIL.undeclared-assumptions` | Uses tools/network/permissions without declaring |
| `FAIL.unsafe-default` | Destructive actions without ask-first |
| `FAIL.non-operational-procedure` | Procedure not numbered or generic advice |

## Tier 2: Semantic Anti-Patterns

| Anti-pattern | Detection Signal | Severity |
|--------------|------------------|----------|
| Placeholder language | "the inputs", "whatever is needed", "stuff" | FAIL |
| Proxy goals | "improve quality", "make better" without metric | FAIL |
| Subjective triggers | "if it seems", "when appropriate", "use judgment" | FAIL |
| Unbounded verbs | "clean up", "refactor", "optimize" without scope | WARN |
| Silent skipping | No "Not run (reason)" for skipped checks | WARN |
| Missing temptation | Troubleshooting lacks anti-pattern as temptation | WARN |
```

**Step 2: Write the section-order.md file**

Create `.claude/skills/skill-wizard/references/section-order.md`:

```markdown
# Section Order Reference

## Dependency Graph

```
1. When to use       <- Standalone
       |
       v (references activation)
2. When NOT to use
       |
       v (defines boundaries)
3. Inputs            <- What skill needs
       |
       v (enables)
4. Outputs           <- What skill produces
       |
       v (referenced by)
5. Procedure         <- References 3, produces 4
       |
       v (contains)
6. Decision points   <- Branches in 5
       |
       v (checks)
7. Verification      <- Checks 4
       |
       v (handles failures from)
8. Troubleshooting   <- Failures in 5
```

## Order Rationale

| Position | Section | Depends On | Enables |
|----------|---------|------------|---------|
| 1 | When to use | None | Activation context for all |
| 2 | When NOT to use | 1 | Boundaries, STOP triggers |
| 3 | Inputs | 1, 2 | What procedure can use |
| 4 | Outputs | 3 | What procedure produces |
| 5 | Procedure | 3, 4 | Steps to execute |
| 6 | Decision points | 5 | Branches in procedure |
| 7 | Verification | 4, 5 | Checks outputs |
| 8 | Troubleshooting | 5, 7 | Handles failures |
```

**Step 3: Write the risk-tier-guide.md file**

Create `.claude/skills/skill-wizard/references/risk-tier-guide.md`:

```markdown
# Risk Tier Guide

## Tier Selection Criteria

| Tier | Characteristics | Examples |
|------|-----------------|----------|
| **Low** | Read-only, no external deps, trivial/reversible | Documentation, exploration, analysis |
| **Medium** | Writes files/config, bounded and reversible | Code generation, config changes, test writing |
| **High** | Security, ops, data, deps, public contracts, costly to reverse | Deployments, migrations, auth changes, API changes |

## Auto-Escalation Rule

**If ANY mutating action detected -> treat as High until gating verified**

Mutating actions include:
- File writes, deletes
- Deployments
- Database changes
- Force operations (git push --force)
- External API calls with side effects

## Gating Validation for Downgrade

A skill with mutating actions MAY be treated as Medium ONLY IF ALL of:

1. **Ask-first gates exist** for every mutating step in Procedure
2. **Scope is bounded and reversible** (explicit scope fence)
3. **Category justifies Medium** (typical risk is Medium or lower)

## Validation Matrix

| Condition | Gating Required | Allowed Tiers |
|-----------|-----------------|---------------|
| No mutating actions | None | Low, Medium, High |
| Mutating + all gates + bounded | Full gating | Medium, High |
| Mutating + missing any gate | Incomplete | High only |
| Touches security/data/ops | Domain risk | High only |

## Tier-Specific Minimum Requirements

| Requirement | Low | Medium | High |
|-------------|-----|--------|------|
| All 8 sections | Y | Y | Y |
| 1 quick check | Y | Y | Y |
| 1 troubleshooting entry | Y | Y | Y |
| 1 STOP/ask (missing inputs) | Y | Y | Y |
| STOP/ask (ambiguity) | - | Y | Y |
| Explicit non-goals (>=3) | - | Y | Y |
| 2nd verification mode | - | SHOULD | Y |
| Ask-first gates | - | - | Y |
| >=2 STOP/ask gates | - | - | Y |
| Rollback/escape guidance | - | - | Y |

## User Override Handling

**If user requests downgrade from High to Medium:**

1. Check gating validation (all 3 criteria above)
2. If passes: Allow, log "Downgraded to Medium - gating validated"
3. If fails: Block, show "Cannot downgrade: [specific missing gate]"
4. User may NOT downgrade to Low if any mutating actions exist
```

**Step 4: Verify reference files created**

Run: `ls -la .claude/skills/skill-wizard/references/`
Expected: `spec-requirements.md`, `section-order.md`, `risk-tier-guide.md`

**Step 5: Commit**

```bash
git add .claude/skills/skill-wizard/references/
git commit -m "feat(skill-wizard): add core reference files"
```

---

## Task 3: Create Section Checklists (Part 1 - First 4)

**Files:**
- Create: `.claude/skills/skill-wizard/references/checklist-when-to-use.md`
- Create: `.claude/skills/skill-wizard/references/checklist-when-not-to-use.md`
- Create: `.claude/skills/skill-wizard/references/checklist-inputs.md`
- Create: `.claude/skills/skill-wizard/references/checklist-outputs.md`

**Step 1: Write checklist-when-to-use.md**

Create `.claude/skills/skill-wizard/references/checklist-when-to-use.md`:

```markdown
# When to Use Checklist

## Structural
- [MUST] Section exists with clear heading or equivalent
- [MUST] Contains activation triggers (when this skill applies)

## Semantic
- [MUST] Primary goal stated in 1-2 sentences
- [MUST] Triggers are specific enough to avoid over-broad activation
- [SHOULD] Includes example scenarios or user phrases that trigger activation

## Anti-patterns
- [SEMANTIC] Vague triggers: "when you need to do X" without specifics
- [SEMANTIC] Overlapping scope with other skills without differentiation
```

**Step 2: Write checklist-when-not-to-use.md**

Create `.claude/skills/skill-wizard/references/checklist-when-not-to-use.md`:

```markdown
# When NOT to Use Checklist

## Structural
- [MUST] Section exists with clear heading or equivalent
- [MUST] Contains at least 3 explicit non-goals or out-of-scope items

## Semantic
- [MUST] Non-goals prevent common scope failures
- [MUST] Includes STOP conditions (explicit triggers to halt and route elsewhere)
- [SHOULD] Default non-goals stated if applicable:
  - No dependency upgrades (unless skill's purpose)
  - No public API changes (unless skill's purpose)
  - No destructive actions (unless skill's purpose)
  - No schema/data migrations (unless skill's purpose)

## Anti-patterns
- [SEMANTIC] Non-goals are just routing suggestions without STOP language
- [SEMANTIC] Missing boundaries that would surprise reviewers
```

**Step 3: Write checklist-inputs.md**

Create `.claude/skills/skill-wizard/references/checklist-inputs.md`:

```markdown
# Inputs Checklist

## Structural
- [MUST] Required inputs sub-section exists
- [MUST] Optional inputs sub-section exists (or explicit "None")
- [MUST] Constraints/Assumptions sub-section exists

## Semantic
- [MUST] At least one required input defined
- [MUST] Each input is specific and actionable (not "the inputs needed")
- [MUST] Constraints declare non-universal assumptions:
  - Tools (specific CLIs, versions)
  - Network (API access, downloads)
  - Permissions (file write, env vars, secrets)
  - Repo layout (specific paths, conventions)
- [MUST] Fallback provided when assumptions not met (or STOP/ask)

## Anti-patterns
- [SEMANTIC] Placeholder language: "whatever is needed", "appropriate inputs"
- [SEMANTIC] Implicit tool assumptions without declaration
- [SEMANTIC] No fallback for network-dependent operations
```

**Step 4: Write checklist-outputs.md**

Create `.claude/skills/skill-wizard/references/checklist-outputs.md`:

```markdown
# Outputs Checklist

## Structural
- [MUST] Artifacts sub-section exists
- [MUST] Definition of Done sub-section exists

## Semantic
- [MUST] At least one artifact defined (files, patches, reports, commands)
- [MUST] At least one objective DoD check that is:
  - Artifact existence/shape, OR
  - Deterministic query/invariant, OR
  - Executable check with expected output, OR
  - Deterministic logical condition
- [MUST] DoD checks are verifiable without "reading the agent's mind"
- [SHOULD] Calibration: outputs distinguish Verified/Inferred/Assumed claims

## Anti-patterns (FAIL-level)
- [SEMANTIC] "Verify it works" - not objective
- [SEMANTIC] "Ensure quality" - not measurable
- [SEMANTIC] "Make sure tests pass" without specifying which tests
- [SEMANTIC] "Check for errors" without specifying where/how
```

**Step 5: Verify first 4 checklists created**

Run: `ls .claude/skills/skill-wizard/references/checklist-*.md | wc -l`
Expected: `4`

**Step 6: Commit**

```bash
git add .claude/skills/skill-wizard/references/checklist-*.md
git commit -m "feat(skill-wizard): add first 4 section checklists"
```

---

## Task 4: Create Section Checklists (Part 2 - Last 4)

**Files:**
- Create: `.claude/skills/skill-wizard/references/checklist-procedure.md`
- Create: `.claude/skills/skill-wizard/references/checklist-decision-points.md`
- Create: `.claude/skills/skill-wizard/references/checklist-verification.md`
- Create: `.claude/skills/skill-wizard/references/checklist-troubleshooting.md`

**Step 1: Write checklist-procedure.md**

Create `.claude/skills/skill-wizard/references/checklist-procedure.md`:

```markdown
# Procedure Checklist

## Structural
- [MUST] Steps are numbered (not bullets or prose)
- [MUST] Steps are executable actions (not generic advice)

## Semantic
- [MUST] At least one explicit STOP/ask step for missing inputs
- [MUST] At least one explicit STOP/ask step for ambiguity (Medium+ risk)
- [HIGH-MUST] Ask-first gate before any breaking/destructive/irreversible action
- [SHOULD] Order follows: inspect -> decide -> act -> verify
- [SHOULD] Prefers smallest correct change

## Command Mention Rule
- [MUST] Every command specifies expected result shape
- [MUST] Every command specifies preconditions (if non-obvious)
- [MUST] Every command has fallback for when it cannot run

## Mutating Action Gating
- [HIGH-MUST] Every mutating step has explicit ask-first gate
- [HIGH-MUST] Each ask-first gate names the specific risk
- [HIGH-MUST] Safe alternative offered (dry-run, read-only, or skip)
- [MEDIUM-MUST] Mutating steps are bounded by scope fence
- [MEDIUM-SHOULD] Rollback/undo steps provided for mutating actions

## Anti-patterns
- [SEMANTIC] "Use judgment" without observable decision criteria
- [SEMANTIC] Commands without expected outputs
- [SEMANTIC] Mutating steps without ask-first gates (High risk)
```

**Step 2: Write checklist-decision-points.md**

Create `.claude/skills/skill-wizard/references/checklist-decision-points.md`:

```markdown
# Decision Points Checklist

## Structural
- [MUST] At least 2 explicit decision points exist
- [MUST] Each uses "If... then... otherwise..." structure (or equivalent)

## Semantic
- [MUST] Each decision point names an observable trigger:
  - File/path exists or doesn't
  - Command output matches pattern
  - Test passes/fails
  - Grep finds/doesn't find pattern
  - Config contains/missing key
- [MUST] Triggers are not subjective ("if it seems", "when appropriate")
- [SHOULD] Covers common operational branches:
  - Tests exist vs not
  - Network available vs restricted
  - Breaking change allowed vs prohibited
  - Output format preference

## Exception Handling
- [MUST] If fewer than 2 decision points, justification is provided
- [MUST] Even with exception, at least one STOP/ask condition exists

## Anti-patterns
- [SEMANTIC] "Use judgment" as the decision criterion
- [SEMANTIC] Subjective triggers: "if it seems risky", "when appropriate"
```

**Step 3: Write checklist-verification.md**

Create `.claude/skills/skill-wizard/references/checklist-verification.md`:

```markdown
# Verification Checklist

## Structural
- [MUST] Quick check sub-section exists
- [SHOULD] Deep check sub-section exists (required for High risk)

## Semantic
- [MUST] Quick check is concrete and executable/observable
- [MUST] Quick check measures the primary success property (not just proxy)
- [MUST] Quick check specifies expected result shape
- [MUST] Failure interpretation: what to do if check fails
- [HIGH-MUST] At least two verification modes (quick + deep)
- [SHOULD] No-network fallback for verification when feasible

## Calibration
- [MUST] Skill instructs "Not run (reason)" reporting for skipped checks
- [SHOULD] Verification ladder (quick -> narrow -> broad) for Medium+ risk

## Anti-patterns
- [SEMANTIC] "Tests pass" without specifying which tests or showing output
- [SEMANTIC] Proxy-only verification (compiles but behavior unchecked)
- [SEMANTIC] No failure handling ("if check fails, continue anyway")
```

**Step 4: Write checklist-troubleshooting.md**

Create `.claude/skills/skill-wizard/references/checklist-troubleshooting.md`:

```markdown
# Troubleshooting Checklist

## Structural
- [MUST] At least one failure mode documented
- [MUST] Each failure mode has: symptoms, likely causes, next steps

## Semantic
- [MUST] Symptoms describe what user observes (error message, behavior)
- [MUST] Causes are specific (not "something went wrong")
- [MUST] Next steps are actionable (specific commands, inspections)
- [SHOULD] At least one anti-pattern phrased as temptation to avoid
  (e.g., "Don't just disable the test")
- [HIGH-MUST] Includes rollback/escape hatch guidance for partial success

## Anti-patterns
- [SEMANTIC] Generic causes: "configuration issue", "environment problem"
- [SEMANTIC] Vague next steps: "investigate further", "check the logs"
```

**Step 5: Verify all 8 checklists created**

Run: `ls .claude/skills/skill-wizard/references/checklist-*.md | wc -l`
Expected: `8`

**Step 6: Commit**

```bash
git add .claude/skills/skill-wizard/references/checklist-*.md
git commit -m "feat(skill-wizard): add remaining 4 section checklists"
```

---

## Task 5: Create Template Files

**Files:**
- Create: `.claude/skills/skill-wizard/templates/wording-patterns.md`
- Create: `.claude/skills/skill-wizard/templates/semantic-templates.md`
- Create: `.claude/skills/skill-wizard/templates/skill-skeleton.md`

**Step 1: Write wording-patterns.md**

Create `.claude/skills/skill-wizard/templates/wording-patterns.md`:

```markdown
# Wording Patterns (Appendix A)

Required patterns from the strict spec. Use verbatim or adapt while preserving intent.

## A.1 STOP/ask for Clarification

```
STOP. Ask the user for: <missing required input>. Do not proceed until provided.
```

```
STOP. The request is ambiguous. Ask: <clarifying question>. Proceed only after user confirms.
```

## A.2 Ask-first for Risky/Breaking Actions

```
Ask first: This step may be breaking/destructive (<risk>). Do not do it without explicit user approval.
```

```
If the user does not explicitly approve <action>, skip it and provide a safe alternative.
```

## A.3 Evidence-first (Debugging/Triage/Refactor)

```
Before suggesting a fix, gather evidence:
1. Read the failing test/error log
2. Identify the exact failure signature
3. Trace to the root cause
Only then propose a targeted fix with evidence.
```

## A.4 Minimal-change Default

```
Prefer the smallest correct change. Do not refactor surrounding code unless explicitly requested.
```

## A.5 Verification Requirements

```
Quick check: Run <command>. Expected: <exit code/output pattern>.
If the quick check fails, do not continue; go to Troubleshooting first.
```

## A.6 Offline/Restricted-Environment Fallback

```
If you cannot run <command> (missing <tool>, restricted permissions, no network):
STOP and ask the user to provide: <command output/logs>
OR perform manual inspection: <manual steps>
```

## A.7 Decision-point Phrasing

```
If <observable signal> is present, then <action>. Otherwise, <alternative>.
```

## Pattern Suggestions by Section

| Section | Patterns to Offer |
|---------|-------------------|
| Procedure | A.1, A.2 (High risk), A.3 (debugging/refactor), A.4 |
| Decision Points | A.1, A.2, A.7 |
| Verification | A.5 |
| Inputs (Constraints) | A.6 |
| Troubleshooting | Reference A.5 for "what to do if check fails" |
```

**Step 2: Write semantic-templates.md**

Create `.claude/skills/skill-wizard/templates/semantic-templates.md`:

```markdown
# Semantic Templates (T1-T7)

Copy/paste-ready templates from the semantic quality addendum.

## T1: Semantic Contract Block (When to Use)

```markdown
## When to Use

**Primary goal:** [1-2 sentence description of what this skill accomplishes]

**Triggers:**
- User says "[exact phrases that activate this skill]"
- User needs to [specific action] for [specific context]
- Before/after [specific event in workflow]
```

## T2: Scope Fence (Inputs or Procedure)

```markdown
**Scope fence:**
- MAY touch: [paths/modules/systems explicitly in scope]
- MUST NOT touch: [paths/modules/systems explicitly out of scope]
- Crossing the fence requires: STOP and ask user for explicit approval
```

## T3: Assumptions Ledger (Inputs or Outputs)

```markdown
**Assumptions:**
| Assumption | Verified | Evidence |
|------------|----------|----------|
| [assumption 1] | Verified/Inferred/Assumed | [file:line or "not checked"] |
| [assumption 2] | Verified/Inferred/Assumed | [file:line or "not checked"] |
```

## T4: Decision Point with Observable Trigger

```markdown
**If** `<file>` exists (check: `test -f <file>`)
**then** [action A]
**otherwise** [action B]
```

## T5: Verification Ladder (Medium/High Risk)

```markdown
**Verification ladder:**

1. **Quick check** (seconds): [primary signal]
   - Run: `<command>`
   - Expected: [pattern]

2. **Narrow check** (minutes): [neighbors/related]
   - Run: `<command>`
   - Expected: [pattern]

3. **Broad check** (longer): [system confidence]
   - Run: `<command>`
   - Expected: [pattern]

Each rung must pass before proceeding to the next.
```

## T6: Failure Interpretation Table (Troubleshooting)

```markdown
| Symptom | Likely Cause | Next Steps |
|---------|--------------|------------|
| [exact error/behavior] | [specific cause] | [specific commands/actions] |
| [exact error/behavior] | [specific cause] | [specific commands/actions] |
```

## T7: Calibration Wording (Procedure, Outputs, Verification)

```markdown
**Calibration:**
Label conclusions as:
- **Verified**: supported by direct evidence (paths/commands/observations)
- **Inferred**: derived from verified facts; call out inference explicitly
- **Assumed**: not verified; STOP/ask if assumption is material

If a verification step was not run, report:
`Not run (reason): <reason>. Run: <command>. Expected: <pattern>.`
```

## Template Suggestions by Section

| Section | Templates to Offer |
|---------|-------------------|
| When to use | T1 (semantic contract) |
| Inputs | T2 (scope fence), T3 (assumptions ledger) |
| Outputs | T3 (for audit skills producing reports) |
| Decision Points | T4 (observable trigger phrasing) |
| Verification | T5 (verification ladder for Medium/High), T7 (calibration) |
| Troubleshooting | T6 (failure interpretation table) |
```

**Step 3: Write skill-skeleton.md**

Create `.claude/skills/skill-wizard/templates/skill-skeleton.md`:

```markdown
# Skill Skeleton

Empty structure for assembly phase.

```yaml
---
name: <skill-name>
description: <brief description>
metadata:
  version: "1.0.0"
allowed-tools:
  - <tool1>
  - <tool2>
---
```

## When to Use

<!-- Activation triggers -->

## When NOT to Use

<!-- STOP conditions and non-goals -->

## Inputs

**Required:**
<!-- Required inputs -->

**Optional:**
<!-- Optional inputs or "None" -->

**Constraints:**
<!-- Tools, network, permissions, repo assumptions -->

## Outputs

**Artifacts:**
<!-- Files, reports, commands produced -->

**Definition of Done:**
<!-- Objective checks -->

## Procedure

<!-- Numbered steps -->

## Decision Points

<!-- If... then... otherwise... -->

## Verification

**Quick check:**
<!-- Concrete check with expected result -->

## Troubleshooting

**Symptom:** <!-- What user observes -->
**Cause:** <!-- Specific cause -->
**Next steps:** <!-- Actionable steps -->
```

**Step 4: Verify template files created**

Run: `ls .claude/skills/skill-wizard/templates/`
Expected: `wording-patterns.md`, `semantic-templates.md`, `skill-skeleton.md`

**Step 5: Commit**

```bash
git add .claude/skills/skill-wizard/templates/
git commit -m "feat(skill-wizard): add template files"
```

---

## Task 6: Create Category Integration Reference

**Files:**
- Create: `.claude/skills/skill-wizard/references/category-integration.md`

**Step 1: Write category-integration.md**

Create `.claude/skills/skill-wizard/references/category-integration.md`:

```markdown
# Category Integration Reference

When a category is selected during discovery, integrate these category-specific elements.

## Category List

| Category | Typical Risk | Dominant Failure Mode |
|----------|--------------|----------------------|
| debugging-triage | Medium | Missing regression guard |
| refactoring-modernization | Medium | Behavior change without detection |
| security-changes | High | Deny-path not verified |
| agentic-pipelines | High | Missing idempotency contract |
| documentation-generation | Low | Stale content |
| code-generation | Medium | Generated code doesn't compile |
| testing | Medium | Tests don't isolate failures |
| configuration-changes | Medium | Rollback not possible |
| dependency-changes | High | Breaking changes not detected |
| api-changes | High | Contract violation |
| data-migrations | High | Data loss or corruption |
| infrastructure-ops | High | Irreversible state change |
| meta-skills | Low | Produced skills don't comply |

## Category-Specific DoD Additions

### debugging-triage
- Failure signature captured (exact error/test name)
- Root cause statement includes evidence
- Regression guard exists or rationale for omission

### refactoring-modernization
- Invariants explicitly stated ("behavior-preserving means...")
- Scope fence defined (what must NOT change)
- Characterization tests exist or are added

### security-changes
- Threat model boundaries stated
- Deny-path verification included
- Rollback plan specified

### agentic-pipelines
- Idempotency contract stated
- Plan/apply/verify separation exists
- All mutating steps have ask-first gates

### code-generation
- Generated code compiles/parses
- Type-checks pass (if applicable)
- Linting passes (if applicable)

### testing
- Test isolation verified (each test independent)
- Failure messages are actionable
- Coverage target met or gap justified

## What to Pull from Category Guide

| Section | Category Guidance Source |
|---------|-------------------------|
| When NOT to use | Category's "When NOT to use (common misfires)" |
| Inputs | Category's "Input contract" |
| Outputs | Category's "Output contract" + "DoD checklist" |
| Decision points | Category's "Decision points library" |
| Verification | Category's "Verification menu" |
| Troubleshooting | Category's "Failure modes & troubleshooting" |
```

**Step 2: Verify category-integration.md created**

Run: `test -f .claude/skills/skill-wizard/references/category-integration.md && echo "exists"`
Expected: `exists`

**Step 3: Commit**

```bash
git add .claude/skills/skill-wizard/references/category-integration.md
git commit -m "feat(skill-wizard): add category integration reference"
```

---

## Task 7: Write SKILL.md Core Content (Part 1 - First 4 Sections)

**Files:**
- Modify: `.claude/skills/skill-wizard/SKILL.md`

**Step 1: Add When to Use section**

Append to `.claude/skills/skill-wizard/SKILL.md` after the frontmatter:

```markdown
## When to Use

- User wants to create a new Claude Code skill from scratch
- User has an idea but doesn't know the spec requirements
- User wants guided, interactive skill authoring with validation
- User says "create a skill", "new skill", "skill wizard", "/skill-wizard"

**Primary goal:** Guide authors from skill idea to spec-compliant SKILL.md through structured dialogue, draft generation, and inline validation.
```

**Step 2: Add When NOT to Use section**

Append to `.claude/skills/skill-wizard/SKILL.md`:

```markdown
## When NOT to Use

**STOP conditions:**

- **STOP** if user has an existing complete draft they want validated, not created.
  Route to: `skill-reviewer` agent or manual review against compliance checklist.

- **STOP** if user wants quick scaffolding without compliance validation.
  Route to: `skillforge --quick` or manual creation from `skill-skeleton.md`.

- **STOP** if user wants to audit multiple existing skills in batch.
  Route to: dedicated audit workflow or `skill-reviewer` in batch mode.

- **STOP** if the task is creating a simple command, not a full skill.
  Route to: `.claude/commands/` directory (commands don't need 8 sections).

- **STOP** if user cannot articulate what the skill should do after 2 clarifying questions.
  The wizard requires a clear purpose to generate meaningful drafts.

**Non-goals:**

- Does not review or grade existing skills (that's assessment, not creation)
- Does not generate skills autonomously without user input at each section
- Does not modify skills after initial creation (use Edit tool directly)
- Does not create skill directories or file structure (only writes SKILL.md)
- Does not install dependencies or configure the environment
```

**Step 3: Add Inputs section**

Append to `.claude/skills/skill-wizard/SKILL.md`:

```markdown
## Inputs

**Required:**

- **Skill purpose**: What the skill does (gathered during discovery)
- **Output path**: Where to write the final SKILL.md

**Optional:**

- Category hint: If user knows the category upfront
- Risk tier override: If user wants to force a specific tier
- Exception flags: Known exceptions to flag upfront

**Constraints:**

- Write access to target directory
- No external dependencies (wizard is self-contained)
- If target path has existing SKILL.md, wizard warns before overwrite

**Fallback:** If write fails, wizard presents skill content in conversation for manual copy.
```

**Step 4: Add Outputs section**

Append to `.claude/skills/skill-wizard/SKILL.md`:

```markdown
## Outputs

**Artifacts:**

- `SKILL.md` at user-specified path (complete skill with all 8 sections)
- Compliance summary in conversation

**Definition of Done:**

1. **File created:** `test -f <path>/SKILL.md` returns 0
2. **All 8 sections present:** `grep -c "^## " <path>/SKILL.md` returns >=8
3. **Zero MUST violations:** Compliance summary shows all MUST requirements passed
4. **Cross-section consistency:** Final check found no reference errors
5. **Frontmatter valid:** Name is kebab-case <=64 chars, description <=1024 chars
6. **Wizard metadata removed:** No `metadata.wizard` block in final file
```

**Step 5: Verify first 4 sections added**

Run: `grep -c "^## " .claude/skills/skill-wizard/SKILL.md`
Expected: `4` (or more if sections existed)

**Step 6: Commit**

```bash
git add .claude/skills/skill-wizard/SKILL.md
git commit -m "feat(skill-wizard): add first 4 sections to SKILL.md"
```

---

## Task 8: Write SKILL.md Core Content (Part 2 - Procedure)

**Files:**
- Modify: `.claude/skills/skill-wizard/SKILL.md`

**Step 1: Add Procedure section**

Append to `.claude/skills/skill-wizard/SKILL.md`:

```markdown
## Procedure

### Phase 1: Discovery

1. **Announce:** "Starting skill wizard. I'll guide you through creating a spec-compliant skill."

2. **Gather purpose (conversational):**
   - "What does this skill do?" (1-2 sentences)
   - "What artifact does it produce?"
   - "Who uses it and when?"

3. **Gather structured inputs (AskUserQuestion):**
   - Category selection (13 options from category-integration.md)
   - Mutating actions? (No / Writes files / External effects)
   - Network required? (No / Optional / Required)

4. **Confirm output path:**
   - If path provided: Validate it's writable
   - If not provided: Ask user for path
   - **STOP** if path not provided after asking.

5. **Create initial SKILL.md:**
   - Write frontmatter with name, description placeholder
   - Add `metadata.wizard` block with status: draft, risk tier, category, discovery answers
   - Write `<!-- wizard:next=when-to-use -->` marker

### Phase 2: Risk Assessment

6. **Determine tier from discovery:**
   - Load `references/risk-tier-guide.md`
   - Apply tier selection rules based on mutating actions and category
   - Auto-escalate to High if mutating actions detected

7. **Flag likely exceptions:**
   - Based on category, identify common exceptions (e.g., "Documentation skills often have <2 decision points")
   - Present to user for acknowledgment

8. **User confirms tier:**
   - Present determined tier with rationale
   - Allow adjustment (with gating validation if downgrading)
   - Update `metadata.wizard.risk_tier` in SKILL.md

### Phase 3: Section-by-Section Drafting

9. **For each section in order (When to use -> Troubleshooting):**

   a. **Show progress:**
      ```
      Y When to use
      -> When NOT to use  <- current
      O Inputs
      O Outputs
      O Procedure
      O Decision points
      O Verification
      O Troubleshooting
      ```

   b. **Generate draft:**
      - Use discovery answers and prior approved sections
      - Load relevant checklist from `references/checklist-<section>.md`
      - Offer templates from `templates/` if applicable

   c. **Present draft with spec requirements:**
      - Show draft content
      - Show checklist items alongside

   d. **Run inline validation:**
      - Check structural requirements ([MUST])
      - Check semantic requirements ([SEMANTIC])
      - Check anti-patterns

   e. **Handle validation results:**
      - **MUST fail:** Block approval, show specific violation, require fix
      - **SHOULD gap:** Warn, allow [Acknowledge and continue]
      - **Borderline:** Flag explicitly, offer [Accept as-is] [Apply suggested fix] [Edit manually]

   f. **User action:** [Approve] [Edit] [Regenerate]
      - If edit: User describes change, regenerate with edit applied
      - Loop until approved

   g. **Write approved section:**
      - Append section to SKILL.md
      - Update `<!-- wizard:next=X -->` marker to next section

### Phase 4: Cross-Section Validation

10. **Run 16 cross-section checks** (from design document):
    - Reference integrity (4 checks)
    - Core invariants (6 checks)
    - Category-specific coherence (3 checks)
    - Semantic coherence (3 checks)

11. **If issues found:**
    - Identify which sections need revision
    - Navigate user to those sections
    - Re-run section validation after edits
    - Loop until all checks pass

### Phase 5: Final Review and Cleanup

12. **Present compliance summary:**
    ```
    ====================================================
    COMPLIANCE SUMMARY: <skill-name>
    ====================================================
    Risk tier: <tier> | Category: <category>

    Structural compliance:   8/8 passed Y
    Semantic quality:        X/X passed Y
    Anti-pattern scan:       0 found Y
    Cross-section check:     Passed Y
    SHOULD requirements:     X/X passed, Y warnings

    SHOULD warnings (Y):
      - <warning 1>
      - <warning 2>

    Borderline acceptances (Z):
      - <acceptance 1>

    Justified exceptions (N):
      - <exception with rationale>

    Verdict: PASS
    ====================================================
    ```

13. **User approves final skill**

14. **Remove wizard metadata:**
    - Delete `metadata.wizard` block from frontmatter
    - Delete `<!-- wizard:next=X -->` marker

15. **Confirm completion:**
    - "Skill created successfully at: <path>/SKILL.md"
    - Suggest: "Test with `/<skill-name>` in this project"
```

**Step 2: Verify Procedure section added**

Run: `grep -c "### Phase" .claude/skills/skill-wizard/SKILL.md`
Expected: `5`

**Step 3: Commit**

```bash
git add .claude/skills/skill-wizard/SKILL.md
git commit -m "feat(skill-wizard): add Procedure section"
```

---

## Task 9: Write SKILL.md Core Content (Part 3 - Final Sections)

**Files:**
- Modify: `.claude/skills/skill-wizard/SKILL.md`

**Step 1: Add Decision Points section**

Append to `.claude/skills/skill-wizard/SKILL.md`:

```markdown
## Decision Points

- **If output path has SKILL.md with `metadata.wizard.status: draft`:**
  Offer to resume from where wizard left off. Present section progress.
  User can [Resume] or [Start fresh].

- **If output path has complete SKILL.md (no wizard metadata):**
  Ask user to confirm overwrite or choose new path.
  Do not overwrite without confirmation.

- **If discovery answers suggest multiple categories:**
  Present top 2-3 matches with trade-offs, ask user to choose.
  Do not guess.

- **If mutating actions detected but user selected Low risk:**
  Override to High, explain why.
  User can acknowledge but cannot downgrade without gating validation.

- **If user wants to skip a section:**
  STOP. All 8 sections required by spec.
  Explain which content areas must exist.
  Offer to generate minimal compliant content if user is stuck.

- **If user navigates back and edits earlier section:**
  Re-validate that section.
  If dependent sections are now inconsistent, flag them for review.

- **If cross-section check fails:**
  Identify the specific inconsistency.
  Navigate user to the section(s) that need revision.
  Do not remove wizard metadata until resolved.
```

**Step 2: Add Verification section**

Append to `.claude/skills/skill-wizard/SKILL.md`:

```markdown
## Verification

**Quick check:**

```bash
test -f <path>/SKILL.md && grep -c "^## " <path>/SKILL.md
```

Expected: File exists AND grep returns >=8.

**Deep check:**

1. Parse frontmatter, validate:
   - `name` is kebab-case, <=64 chars
   - `description` exists, <=1024 chars
   - No `metadata.wizard` block (indicates incomplete)

2. Re-run all 8 section checklists on written file

3. Confirm compliance summary matches:
   - Zero MUST violations
   - All SHOULD warnings acknowledged
   - All borderline acceptances documented

**If quick check fails:**
- If file missing: Write failed. Check path permissions. Ask user to verify path and retry.
- If <8 sections: Wizard interrupted. Offer to resume.

**Calibration:**
If any verification step was not run, report:
`Not run (reason): <reason>. Run: <command>. Expected: <pattern>.`
```

**Step 3: Add Troubleshooting section**

Append to `.claude/skills/skill-wizard/SKILL.md`:

```markdown
## Troubleshooting

**Symptom:** User stuck on a section, keeps failing validation
**Cause:** Skill concept doesn't map well to spec structure
**Next steps:**
- Ask what user is trying to achieve with this section
- Suggest restructuring the skill concept
- Check if this should be a command instead of a skill (commands don't need 8 sections)

**Symptom:** Cross-section check fails repeatedly
**Cause:** User navigated back and edited earlier sections, creating inconsistencies
**Next steps:**
- Show the specific inconsistency (e.g., "Procedure references 'file path' input but Inputs section no longer lists it")
- Navigate to source section
- Re-validate dependent sections after fix

**Symptom:** Too many borderline acceptances (>3)
**Cause:** User clicking "accept" without understanding implications
**Next steps:**
- At final review, flag high count of borderline items
- Ask user if they want to revisit any before finalizing
- Warn: "Skills with many borderline acceptances often fail in practice"

**Anti-pattern to avoid:** "Just accept everything to finish faster"
This produces structurally compliant but semantically weak skills.
If user seems to be rushing, note: "You have X borderline acceptances. Consider revising?"

**Symptom:** Write permission denied
**Cause:** Target directory not writable or doesn't exist
**Next steps:**
- Check if parent directory exists: `ls -la <parent>`
- Check permissions: `ls -la <target>`
- Offer alternative: present skill in conversation for manual copy
```

**Step 4: Add Session Recovery section**

Append to `.claude/skills/skill-wizard/SKILL.md`:

```markdown
## Session Recovery

The wizard writes approved sections incrementally to SKILL.md. **The artifact is the checkpoint.**

**Recovery procedure:**

When user says "continue wizard" or "resume skill-wizard", or when wizard detects partial SKILL.md:

1. **Read** existing SKILL.md at target path
2. **Parse** wizard metadata from frontmatter (risk tier, category, exceptions)
3. **Validate** each existing section against checklists
4. **Present summary:**
   - "Found X/8 sections for '<skill-name>'. All valid. Next: <section>."
   - If any section fails: "Found X/8 sections. '<section>' has MUST violation. Fix first?"
5. **Resume** from first missing or invalid section

**User edits between sessions:**
- Wizard re-reads and re-validates on resume
- External edits are handled as normal edit cycles
- If edits improved content -> passes validation, wizard continues
- If edits broke something -> validation catches it, wizard flags for revision

**Abandoning a draft:**
- Partial SKILL.md remains with `status: draft` marker
- User can delete it, or resume later
- The draft marker prevents confusion about completeness
```

**Step 5: Verify all sections present**

Run: `grep -c "^## " .claude/skills/skill-wizard/SKILL.md`
Expected: `9` (8 required + Session Recovery)

**Step 6: Commit**

```bash
git add .claude/skills/skill-wizard/SKILL.md
git commit -m "feat(skill-wizard): add Decision Points, Verification, Troubleshooting, Session Recovery"
```

---

## Task 10: Final Verification and Line Count Check

**Files:**
- Verify: `.claude/skills/skill-wizard/SKILL.md`
- Verify: All reference and template files

**Step 1: Count lines in SKILL.md**

Run: `wc -l .claude/skills/skill-wizard/SKILL.md`
Expected: 400-600 lines (meta-skill exception allows up to ~600)

**Step 2: Verify all reference files present**

Run: `ls .claude/skills/skill-wizard/references/ | wc -l`
Expected: `12` (spec-requirements, section-order, risk-tier-guide, category-integration, 8 checklists)

**Step 3: Verify all template files present**

Run: `ls .claude/skills/skill-wizard/templates/ | wc -l`
Expected: `3` (wording-patterns, semantic-templates, skill-skeleton)

**Step 4: Verify skill loads**

Run: `claude --debug 2>&1 | grep -i skill-wizard`
Expected: Shows skill-wizard being loaded (or no errors related to it)

**Step 5: Test skill invocation**

Invoke: `/skill-wizard`
Expected: Wizard starts discovery phase

**Step 6: Final commit if any fixes needed**

```bash
git add .claude/skills/skill-wizard/
git commit -m "feat(skill-wizard): complete implementation"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Directory structure + frontmatter | SKILL.md skeleton |
| 2 | Core references | spec-requirements, section-order, risk-tier-guide |
| 3 | Checklists part 1 | when-to-use, when-not-to-use, inputs, outputs |
| 4 | Checklists part 2 | procedure, decision-points, verification, troubleshooting |
| 5 | Templates | wording-patterns, semantic-templates, skill-skeleton |
| 6 | Category integration | category-integration.md |
| 7 | SKILL.md part 1 | When to Use, When NOT, Inputs, Outputs |
| 8 | SKILL.md part 2 | Procedure (all 5 phases) |
| 9 | SKILL.md part 3 | Decision Points, Verification, Troubleshooting, Session Recovery |
| 10 | Final verification | Line count, file verification, test invocation |

**Total files created:** 16
- 1 SKILL.md (~500 lines)
- 12 reference files (~500 lines total)
- 3 template files (~230 lines total)
