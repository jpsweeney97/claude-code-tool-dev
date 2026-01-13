# Skill Design: skill-wizard

**Date:** 2026-01-12
**Status:** Draft
**Category:** Meta-skills
**Risk Tier:** Low

## Summary

An interactive skill that guides authors from goal to spec-compliant SKILL.md through structured dialogue, draft generation, and inline validation.

## Problem Statement

Authors creating Claude Code skills face two challenges:
1. The skills-as-prompts strict spec has ~25 requirements across 8 sections
2. Structurally compliant skills can still be semantically weak ("verify it works")

Existing tooling (skillforge, skill-reviewer) focuses on creation depth and post-hoc review. Neither provides guided, interactive compliance during authoring.

## Solution

A wizard that:
- Gathers skill purpose through conversational + structured questions
- Determines risk tier and flags likely exceptions upfront
- Generates draft content for each of 8 required sections
- Presents drafts alongside spec requirements for transparency
- Validates inline with section-specific checklists
- Blocks on MUST violations, warns on SHOULD gaps
- Assembles final skill with compliance summary

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Discovery | Conversational + AskUserQuestion | Balance flexibility with efficiency |
| Draft presentation | Full section + spec visible | Educational, transparent |
| Edit handling | Free-form text | Natural conversation flow |
| Validation | Two-tier system (normative fail codes + semantic anti-patterns) | Aligns with spec hierarchy |
| Navigation | Full state visibility, jump anywhere | Maximum user control |
| Strictness | Tiered (MUST blocks, SHOULD warns) | Matches spec hierarchy |
| Borderline cases | Flag and ask with severity friction | Transparent, respects agency |
| Cross-section | 16 checks across 4 categories | Comprehensive coverage of core invariants |
| Risk escalation | Auto-escalate + gating validation for downgrade | Enforces safe defaults |
| Category integration | Per-category DoD, decision points, failure modes | Leverages rich category-specific guidance |
| Session recovery | Conversation-based checkpoints | Prevents progress loss without file side effects |
| Wording patterns | Offer Appendix A templates during drafting | Ensures spec-compliant language |
| Calibration | Require Verified/Inferred/Assumed labeling | Prevents overconfident claims |

---

## Frontmatter Specification

```yaml
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
```

### Frontmatter Rationale

| Field | Value | Rationale |
|-------|-------|-----------|
| `name` | `skill-wizard` | Clear, memorable, describes function |
| `description` | (see above) | Includes trigger phrases: "creating a new skill", "interactive authoring", "spec requirements" |
| `license` | MIT | Standard for this repo |
| `metadata.category` | meta-skills | Produces other skills |
| `metadata.risk_tier` | low | Read-only analysis + single file write with confirmation |
| `metadata.spec_version` | skills-as-prompts-strict-v1 | Documents which spec version wizard validates against |
| `metadata.timelessness_score` | 8 | Principle-based, not tied to volatile tooling |

### Allowed Tools

| Tool | Purpose | Usage |
|------|---------|-------|
| `Read` | Load reference files | Checklists, spec-requirements, templates |
| `Write` | Create SKILL.md | Single file write at end with user approval |
| `Glob` | Find existing skills | Check for naming conflicts, locate skill directories |
| `Grep` | Validate written file | Quick check that sections exist in output |
| `AskUserQuestion` | Structured input | Category selection, risk confirmation, approve/edit choices |

### Tools NOT Included

| Tool | Reason Excluded |
|------|-----------------|
| `Bash` | No shell operations needed; validation is content-based |
| `Edit` | Creates new file, doesn't edit existing |
| `WebFetch` | Self-contained, no external lookups |
| `WebSearch` | Spec knowledge is in references, not searched |
| `Task` | Single-threaded wizard, no subagent delegation |

---

## Skill Structure

```
.claude/skills/skill-wizard/
├── SKILL.md                          # Core interaction flow (~500 lines)
├── references/
│   ├── spec-requirements.md          # MUST/SHOULD + fail codes (~100 lines)
│   ├── section-order.md              # Dependency graph + rationale (~40 lines)
│   ├── risk-tier-guide.md            # Tier selection + gating validation (~80 lines)
│   ├── category-integration.md       # Per-category overrides (~150 lines)
│   ├── checklist-when-to-use.md      # ~25 lines
│   ├── checklist-when-not-to-use.md  # ~30 lines
│   ├── checklist-inputs.md           # ~35 lines
│   ├── checklist-outputs.md          # ~35 lines
│   ├── checklist-procedure.md        # ~45 lines
│   ├── checklist-decision-points.md  # ~35 lines
│   ├── checklist-verification.md     # ~40 lines
│   └── checklist-troubleshooting.md  # ~30 lines
└── templates/
    ├── wording-patterns.md           # Appendix A patterns (~80 lines)
    ├── semantic-templates.md         # T1-T7 templates (~100 lines)
    └── skill-skeleton.md             # Empty structure (~50 lines)
```

Total reference content: ~875 lines (loaded on demand)
Total template content: ~230 lines (offered during drafting)

### Why This Structure

**SKILL.md stays focused (~500 lines):** Contains the interaction flow, phase transitions, and validation orchestration. Does not embed the full spec.

**Section-specific checklists:** Each checklist is small, loads only when validating that section. Easier to maintain than one monolithic checklist.

**Spec requirements extracted:** The strict spec and semantic addendum are synthesized into a single reference. When specs update, one file changes.

**Smart ordering documented:** Section dependencies and rationale are explicit, not buried in SKILL.md logic.

**Category integration:** Per-category DoD checklists, decision point libraries, and failure modes from `skills-categories-guide.md`.

**Templates for consistency:** Wording patterns (Appendix A) and semantic templates (T1-T7) offered during drafting to ensure spec-compliant language.

### Checklist Format

Each checklist uses tagged requirements:

```markdown
## Inputs Checklist

### Structural
- [MUST] Required/Optional/Constraints sub-sections present
- [MUST] At least one required input defined

### Semantic
- [MUST] Each input is specific and actionable (not "the inputs")
- [MUST] Constraints declare assumptions likely to be guessed incorrectly
- [SHOULD] Fallback path when assumptions not met
- [HIGH-MUST] STOP/ask step if required inputs might be missing

### Anti-patterns
- [SEMANTIC] No placeholder language ("whatever is needed", "stuff")
```

Tags: `[MUST]` `[SHOULD]` `[HIGH-MUST]` `[SEMANTIC]`

### Size and Progressive Disclosure

**Expected size: 500-600 lines**

This skill exceeds the standard 500-line guideline for SKILL.md. This is acceptable because:

1. **Meta-skills are an acknowledged exception** — they produce other skills, requiring comprehensive guidance that cannot be safely abbreviated
2. **Validation orchestration is core functionality** — moving it to references would fragment the procedure and introduce context-switching overhead
3. **The categories guide precedent** — `skills-categories-guide.md` is 1400+ lines because comprehensive category coverage requires it

---

## Session Recovery

### Risk

Long wizard sessions (8 sections × multiple edit cycles) are vulnerable to:
- Session timeout or disconnect
- User closing terminal accidentally
- Claude context limits forcing summarization

### State to Preserve

At minimum, persist after each section approval:
- Discovery answers (skill purpose, category, risk tier)
- Approved section content (verbatim markdown)
- Exception flags and justifications
- Borderline acceptances with user decisions
- Current phase and section index

### Persistence Strategy: Conversation-Based Checkpoints

After each section approval, emit a checkpoint summary block:

```yaml
# skill-wizard checkpoint (paste to resume)
checkpoint_version: 1
skill_name: pr-security-reviewer
discovery:
  purpose: "Reviews PRs for security vulnerabilities"
  category: security-changes
  risk_tier: high
  mutating_actions: false
approved_sections:
  when_to_use: |
    - User requests security review of a PR
    ...
  when_not_to_use: |
    ...
current_phase: 3
current_section: inputs
exceptions: []
borderline_acceptances: []
```

**Checkpoint emission format:**

```
<details>
<summary>💾 Checkpoint saved (5/8 sections complete)</summary>

[full state YAML]

</details>
```

### Recovery Procedure

When resuming from checkpoint:
1. Parse checkpoint state
2. Validate: does the target skill directory still exist? Any conflicts?
3. Present summary: "Resuming wizard for '<name>'. Completed: 5/8 sections. Next: Procedure."
4. Continue from `current_section`
5. Run cross-section validation on previously approved sections before continuing

---

## Interaction Flow

### Phase 1: Discovery

Gather skill purpose through mixed question types:

**Conversational (open-ended):**
- "What does this skill do?" (1-2 sentences)
- "What artifact does it produce?"
- "Who uses it and when?"

**Structured (AskUserQuestion):**
- Category selection (13 options from spec)
- Mutating actions? (No / Writes files / External effects)
- Network required? (No / Optional / Required)

**Output:** Skill profile used for draft generation and risk assessment.

### Phase 2: Risk Assessment

Determine tier based on discovery answers:

```
Low risk:  Read-only, no external deps, trivial/reversible
Medium:    Writes files/config, bounded and reversible
High:      Security, ops, data, deps, public contracts, or hard to reverse
```

**Auto-escalation:** Any mutating action → treat as High until procedure explicitly gates with ask-first.

**Exception flagging:** Based on category + risk, identify likely exceptions:
- "Documentation skills often have <2 decision points"
- "Low-risk skills may skip deep verification checks"

User confirms or adjusts tier. Exceptions are noted for later.

### Phase 3: Section-by-Section Drafting

For each section in dependency order:

```
1. When to use        ← Standalone
2. When NOT to use    ← References activation
3. Inputs             ← What skill needs
4. Outputs            ← What skill produces
5. Procedure          ← References 3, produces 4
6. Decision points    ← Branches in 5
7. Verification       ← Checks 4
8. Troubleshooting    ← Failures in 5
```

**Each section follows this loop:**

```
┌─────────────────────────────────────────────────────┐
│ 1. Show progress bar (✓ done, → current, ○ pending) │
│ 2. Generate draft from discovery + prior sections   │
│ 3. Present draft alongside spec requirements        │
│ 4. Run checklist validation inline                  │
│    - MUST fail → block approve                      │
│    - SHOULD gap → warn, allow continue              │
│    - Borderline → flag and ask                      │
│ 5. User: [Approve] [Edit] [Regenerate]              │
│ 6. If edit: user describes change, regenerate      │
│ 7. Loop until approved                              │
└─────────────────────────────────────────────────────┘
```

**Navigation:** User can say "go to [section]" anytime to revise earlier work.

### Phase 4: Assembly and Output

After all sections approved:

1. Assemble sections into complete SKILL.md
2. Generate frontmatter (name, description, risk tier)
3. Run final cross-section consistency check
4. Present complete skill + compliance summary
5. User approves → write to specified path

---

## Validation Logic

### Two-Tier Validation System

Validation uses two tiers aligned with the spec hierarchy:

**Tier 1: Normative Fail Codes (from `spec.review.fail-codes`)**

These are automatic FAIL conditions:

| Fail Code | Description | Checklist Reference |
|-----------|-------------|---------------------|
| `FAIL.missing-content-areas` | One or more of 8 required sections absent or not findable | checklist-*.md (all) |
| `FAIL.no-objective-dod` | Outputs lack objective, checkable DoD condition | checklist-outputs.md |
| `FAIL.no-stop-ask` | No explicit STOP/ask step for missing inputs or ambiguity | checklist-procedure.md |
| `FAIL.no-quick-check` | Verification lacks concrete quick check with expected result | checklist-verification.md |
| `FAIL.too-few-decision-points` | Fewer than 2 explicit decision points without justified exception | checklist-decision-points.md |
| `FAIL.undeclared-assumptions` | Relies on tools/network/permissions/repo without declaring | checklist-inputs.md |
| `FAIL.unsafe-default` | Default procedure performs destructive actions without ask-first | checklist-procedure.md |
| `FAIL.non-operational-procedure` | Procedure not numbered or written as generic advice | checklist-procedure.md |

**Tier 2: Semantic Anti-Patterns (from semantic addendum)**

| Anti-pattern | Detection Signal | Severity |
|--------------|------------------|----------|
| Placeholder language | "the inputs", "whatever is needed", "stuff", "appropriate" | FAIL |
| Proxy goals | "improve quality", "make better", "optimize" without metric | FAIL |
| Subjective triggers | "if it seems", "when appropriate", "use judgment" | FAIL |
| Unbounded verbs | "clean up", "refactor", "optimize" without scope | WARN |
| Silent skipping | No "Not run (reason)" for skipped checks | WARN |
| Missing temptation | Troubleshooting has no anti-pattern phrased as temptation | WARN |

### Validation Behavior by Severity

| Severity | Behavior | User Options |
|----------|----------|--------------|
| FAIL (Tier 1) | Blocks section approval | Must fix before proceeding |
| FAIL (Tier 2) | Blocks section approval | Must fix before proceeding |
| WARN | Flags issue, allows continue | [Fix now] [Acknowledge and continue] |

When WARN is acknowledged, it's logged and included in compliance summary.

### Implementation: Evidence-Based Checklist

Claude evaluates against structured checklists, explicitly citing evidence:

```
Validating: Decision Points

┌─ Checklist ─────────────────────────────────────────┐
│ □ [MUST] ≥2 decision points                         │
│   Found: 3                                          │
│   Evidence: Lines 12, 18, 24                        │
│   Status: ✓ PASS                                    │
│                                                     │
│ □ [MUST] Observable triggers (not subjective)       │
│   Found: 2/3 observable                             │
│   Evidence: Line 24 uses "if it seems risky"        │
│   Status: ✗ FAIL — revise line 24                   │
│   Fail code: FAIL.subjective-trigger                │
└─────────────────────────────────────────────────────┘
```

### Edge Case Handling

**Impossible requirements:**
1. Wizard asks: "Is this feasible?"
2. If no: require written justification
3. AND require alternative mitigation (e.g., STOP/ask instead of fallback)
4. Both become part of skill content

**Borderline compliance:**
1. Wizard flags explicitly: "This is close but not spec-compliant"
2. Explains what spec wants and why this falls short
3. Offers suggested fix
4. User chooses: [Accept as-is] [Apply fix] [Edit manually]
5. MUST borderline gets higher friction ("I strongly recommend revising")

**Justified exceptions:**
- Detected during discovery based on category/risk
- Flagged upfront: "You may have <2 decision points; I'll ask for justification"
- When reached: wizard accepts with brief justification recorded in skill

### Cross-Section Consistency Check

Run at final assembly (Phase 4). Total: 16 checks across 4 categories.

**Reference integrity checks (4):**

| Check | What it catches |
|-------|-----------------|
| STOP/ask → Inputs | Procedure says "ask for X" but X not in Required Inputs |
| Verification → Outputs | Quick check doesn't measure any declared artifact |
| Procedure → Outputs | Procedure never creates a declared output artifact |
| Decision triggers → observable | Subjective language that slipped through section review |

**Core invariant checks (6):**

| Invariant | Cross-section validation |
|-----------|-------------------------|
| Input sufficiency | Every Required Input has a STOP/ask in Procedure if it might be missing |
| Output contract | Every artifact in Outputs has a corresponding DoD check |
| Branching clarity | Decision points cover all branches implied by Procedure conditionals |
| Verification-first | Verification section is referenced in Procedure (not orphaned) |
| Failure recovery | At least one Troubleshooting entry maps to a Verification failure mode |
| Assumptions declared | Every tool/network/permission in Procedure is declared in Inputs → Constraints |

**Category-specific coherence (3):**

| Check | What it catches |
|-------|-----------------|
| Category DoD coverage | All category-required DoD items present in Outputs |
| Category decision branches | Decision points include category's "common operational branches" |
| Category failure modes | Troubleshooting includes at least one category-specific failure |

**Semantic coherence checks (3):**

| Check | What it catches |
|-------|-----------------|
| Goal alignment | Primary goal in "When to use" matches what Outputs actually produces |
| Non-goal enforcement | "When NOT to use" items have corresponding STOP/ask or scope fence |
| Constraint propagation | Hard constraints in Inputs appear as decision points or procedure guards |

Smart ordering prevents most issues; final check catches drift from edits.

---

## Outputs

### Artifacts

| Artifact | Location | Description |
|----------|----------|-------------|
| SKILL.md | User-specified path | Complete skill with all 8 sections |
| Compliance summary | In conversation | Structural + semantic pass/warn status |
| Exception log | Embedded in skill | Justified exceptions with rationale |

### Definition of Done (Objective Checks)

**Structural criteria (MUST):**

1. **File created:** SKILL.md exists at specified path
   - Check: `test -f <path>/SKILL.md`

2. **All 8 sections present:** Headings exist and contain content
   - Check: Grep for section headers, each returns non-empty content

3. **Zero MUST violations:** All `[MUST]` checklist items passed
   - Check: Compliance summary shows "MUST requirements: X/X passed"

4. **Cross-section consistency:** Final check found no issues
   - Check: Compliance summary shows no cross-reference errors

5. **Frontmatter valid:** Name is kebab-case ≤64 chars, description ≤1024 chars
   - Check: Parse YAML frontmatter, validate constraints

**Semantic quality criteria (MUST):**

6. **Intent fidelity:** Primary goal stated in 1-2 sentences; ≥3 non-goals listed
   - Check: "When to use" has goal statement; "When NOT to use" has ≥3 bullets

7. **Objective DoD:** Outputs section has checkable condition (not "verify it works")
   - Check: DoD contains artifact existence, command exit/output, or logical condition

8. **Observable triggers:** Decision points use observable signals (not "if it seems")
   - Check: Each decision point references file/command/grep/test result

9. **Constraint completeness:** Assumptions declared for tools/network/permissions
   - Check: Constraints sub-section exists with ≥1 assumption

10. **Calibration:** Verification includes expected result shape
    - Check: Quick check specifies exit code, output pattern, or file content

**Anti-pattern checks (FAIL if found):**

| Anti-pattern | Detection | Fail Code |
|--------------|-----------|-----------|
| Placeholder language | "the inputs", "whatever is needed", "stuff" | `FAIL.placeholder-content` |
| Proxy goals | "improve quality", "make better" without metric | `FAIL.proxy-goal` |
| Subjective triggers | "if it seems", "when appropriate", "use judgment" | `FAIL.subjective-trigger` |
| Non-objective DoD | "verify it works", "ensure quality", "check for errors" | `FAIL.non-objective-dod` |
| Missing STOP/ask | Procedure has no explicit pause for missing inputs | `FAIL.no-stop-ask` |
| Unbounded verbs | "optimize", "clean up", "refactor" without scope | `FAIL.unbounded-verb` |

**Secondary criteria (SHOULD-level):**

11. **SHOULD warnings addressed or acknowledged:** User saw all warnings
12. **Borderline acceptances documented:** Any "accept as-is" choices visible
13. **Troubleshooting has anti-pattern:** Includes at least one "temptation to avoid"

### Compliance Summary Format

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COMPLIANCE SUMMARY: pr-security-reviewer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Risk tier: High │ Category: Security changes

Structural compliance:   8/8 passed ✓
Semantic quality:        5/5 passed ✓
Anti-pattern scan:       0 found ✓
Cross-section check:     Passed ✓
SHOULD requirements:     6/7 passed, 1 warning

SHOULD warnings (1):
  • Verification: Consider adding second verification mode

Borderline acceptances (0): None

Justified exceptions (1):
  • Decision points: 2 instead of 3 — "linear security scan
    with no meaningful branch points beyond pass/fail"

Verdict: PASS

Written to: .claude/skills/pr-security-reviewer/SKILL.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## SKILL.md Body Outline

### When to Use

- User wants to create a new Claude Code skill from scratch
- User has an idea but doesn't know the spec requirements
- User wants guided, interactive skill authoring with validation
- User says "create a skill", "new skill", "skill wizard", "/skill-wizard"

### When NOT to Use

**STOP conditions (halt and route elsewhere):**

- **STOP** if user has an existing complete draft they want validated, not created.
  Route to: `skill-reviewer` agent or manual review against compliance checklist.

- **STOP** if user wants quick scaffolding without compliance validation.
  Route to: `skillforge --quick` or manual creation from `skill-skeleton.md`.

- **STOP** if user wants to audit multiple existing skills in batch.
  Route to: dedicated audit workflow or `skill-reviewer` in batch mode.

- **STOP** if the task is creating a simple command, not a full skill.
  Route to: `.claude/commands/` directory (commands don't need 8 sections).

- **STOP** if user cannot articulate what the skill should do after 2 clarifying
  questions. The wizard requires a clear purpose to generate meaningful drafts.

**Non-goals (what this skill does not do):**

- Does not review or grade existing skills (that's assessment, not creation)
- Does not generate skills autonomously without user input at each section
- Does not modify skills after initial creation (use Edit tool directly)
- Does not create skill directories or file structure (only writes SKILL.md)
- Does not install dependencies or configure the environment

### Inputs

**Required:**
- Skill purpose: What the skill does (gathered during discovery)
- Output path: Where to write the final SKILL.md

**Optional:**
- Category hint: If user knows the category upfront
- Risk tier override: If user wants to force a specific tier
- Exception flags: Known exceptions to flag upfront

**Constraints/Assumptions:**
- Write access to target directory
- No external dependencies (wizard is self-contained)
- If target path has existing SKILL.md, wizard warns before overwrite

### Outputs

**Artifacts:**
- `SKILL.md` at user-specified path
- Compliance summary in conversation

**Definition of Done:**
- SKILL.md exists with all 8 sections
- Zero MUST violations (structural + semantic)
- Zero anti-patterns detected
- Cross-section consistency check passed
- User approved final assembly

### Procedure

1. **Start discovery**
   - Ask skill purpose (conversational)
   - Ask category, mutating actions, network needs (structured)
   - Confirm output path

2. **Assess risk tier**
   - Apply tier selection rules from discovery answers
   - Auto-escalate if mutating actions detected
   - Flag likely exceptions based on category
   - User confirms or adjusts

3. **Draft sections in order**
   - For each section (smart dependency order):
     a. Show progress (✓ done, → current, ○ pending)
     b. Generate draft from discovery + prior sections
     c. Present draft + spec requirements side-by-side
     d. Run section checklist (structural + semantic + anti-pattern)
     e. Handle validation results:
        - MUST fail → block, require fix
        - SHOULD gap → warn, allow continue
        - Borderline → flag and ask
        - Anti-pattern → FAIL, require removal
     f. User approves, edits, or regenerates
     g. Loop until approved
   - Allow "go to [section]" navigation anytime

4. **Assemble and validate**
   - Combine all approved sections
   - Generate frontmatter (name, description, tier)
   - Run cross-section consistency check
   - If issues found, identify which sections need revision

5. **Final review and output**
   - Present complete SKILL.md
   - Show compliance summary (structural, semantic, anti-patterns, warnings)
   - User approves → write file
   - Confirm success with path

### Decision Points

- **If output path already has SKILL.md:** Ask user to confirm overwrite or choose new path. Do not overwrite without confirmation.

- **If discovery answers suggest multiple categories:** Present top 2-3 matches with trade-offs, ask user to choose. Do not guess.

- **If mutating actions detected but user selected Low risk:** Override to High, explain why. User can acknowledge but cannot downgrade.

- **If user wants to skip a section:** STOP. All 8 sections required by spec. Explain which content areas must exist. Offer to generate minimal compliant content if user is stuck.

- **If cross-section check fails after all sections approved:** Identify the specific inconsistency, navigate user to the section(s) that need revision. Do not write file until resolved.

### Verification

**Quick check:**
- SKILL.md exists at output path
- File contains all 8 section headers
- `grep -c "^## "` returns ≥8

**Deep check:**
- Parse frontmatter, validate name/description constraints
- Re-run all section checklists on written file
- Confirm compliance summary matches expectations

**If quick check fails:** File write failed. Check path permissions, retry.

### Troubleshooting

**Symptom:** User stuck on a section, keeps failing validation
- Likely cause: Skill concept doesn't map well to spec structure
- Next steps: Ask what user is trying to achieve, suggest restructuring the skill concept, or identify if this should be a command instead of a skill

**Symptom:** Cross-section check fails repeatedly
- Likely cause: User edited earlier sections after later ones were approved
- Next steps: Show the specific inconsistency, navigate to source section, re-validate dependent sections after fix

**Symptom:** Too many borderline acceptances
- Likely cause: User clicking "accept" without understanding implications
- Next steps: At final review, flag high count of borderline items, ask user if they want to revisit any before writing file

**Anti-pattern to avoid:** "Just accept everything to finish faster" — produces structurally compliant but semantically weak skills. If user seems to be rushing, wizard can note: "You have 4 borderline acceptances. Skills with this pattern often fail in practice. Consider revising?"

---

## Reference File Specifications

### references/spec-requirements.md

Synthesized requirements from strict spec + semantic addendum. Single source of truth for what the wizard validates against.

Contents:
- Source document versions
- Requirement level definitions (MUST/SHOULD/HIGH-MUST/SEMANTIC)
- Core invariants (all 8)
- Anti-pattern definitions with detection patterns and fail codes (Tier 1 + Tier 2)

### references/section-order.md

Documents the smart ordering and dependency rationale.

Contents:
- Dependency graph visualization
- Order rationale table (position, section, depends on, enables)
- Cross-section reference types

### references/risk-tier-guide.md

Criteria for tier selection, gating validation, and tier-specific requirements.

Contents:
- Tier selection criteria (Low/Medium/High)
- Auto-escalation rule for mutating actions
- Gating validation for tier downgrade (see Fix #8 below)
- Tier-specific minimum requirements table
- Exception patterns by category

### references/category-integration.md

Per-category overrides from `skills-categories-guide.md`.

Contents:
- Category-specific DoD additions by category
- Template suggestions by section
- How to load and merge category guidance during drafting

### references/checklist-when-to-use.md

```markdown
# When to Use Checklist

## Structural
- [MUST] Section exists with clear heading or equivalent
- [MUST] Contains activation triggers (when this skill applies)

## Semantic (from semantic.minimums.intent-and-non-goals)
- [MUST] Primary goal stated in 1-2 sentences
- [MUST] Triggers are specific enough to avoid over-broad activation
- [SHOULD] Includes example scenarios or user phrases that trigger activation

## Anti-patterns
- [SEMANTIC] Vague triggers: "when you need to do X" without specifics
- [SEMANTIC] Overlapping scope with other skills without differentiation
```

### references/checklist-when-not-to-use.md

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

### references/checklist-inputs.md

```markdown
# Inputs Checklist

## Structural
- [MUST] Required inputs sub-section exists
- [MUST] Optional inputs sub-section exists (or explicit "None")
- [MUST] Constraints/Assumptions sub-section exists

## Semantic (from spec.prompt-engineering-requirements.3)
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

### references/checklist-outputs.md

```markdown
# Outputs Checklist

## Structural
- [MUST] Artifacts sub-section exists
- [MUST] Definition of Done sub-section exists

## Semantic (from spec.prompt-engineering-requirements.1)
- [MUST] At least one artifact defined (files, patches, reports, commands)
- [MUST] At least one objective DoD check that is:
  - Artifact existence/shape, OR
  - Deterministic query/invariant, OR
  - Executable check with expected output, OR
  - Deterministic logical condition
- [MUST] DoD checks are verifiable without "reading the agent's mind"
- [SHOULD] Calibration: outputs distinguish Verified/Inferred/Assumed claims

## Anti-patterns (FAIL-level)
- [SEMANTIC] "Verify it works" — not objective
- [SEMANTIC] "Ensure quality" — not measurable
- [SEMANTIC] "Make sure tests pass" without specifying which tests
- [SEMANTIC] "Check for errors" without specifying where/how
```

### references/checklist-procedure.md

```markdown
# Procedure Checklist

## Structural
- [MUST] Steps are numbered (not bullets or prose)
- [MUST] Steps are executable actions (not generic advice)

## Semantic (from spec.prompt-engineering-requirements.4)
- [MUST] At least one explicit STOP/ask step for missing inputs
- [MUST] At least one explicit STOP/ask step for ambiguity (Medium+ risk)
- [HIGH-MUST] Ask-first gate before any breaking/destructive/irreversible action
- [SHOULD] Order follows: inspect → decide → act → verify
- [SHOULD] Prefers smallest correct change

## Command mention rule (from spec.command-mention)
- [MUST] Every command specifies expected result shape
- [MUST] Every command specifies preconditions (if non-obvious)
- [MUST] Every command has fallback for when it cannot run

## Mutating action gating
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

### references/checklist-decision-points.md

```markdown
# Decision Points Checklist

## Structural
- [MUST] At least 2 explicit decision points exist
- [MUST] Each uses "If... then... otherwise..." structure (or equivalent)

## Semantic (from spec.prompt-engineering-requirements.5)
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

## Exception handling
- [MUST] If fewer than 2 decision points, justification is provided
- [MUST] Even with exception, at least one STOP/ask condition exists

## Anti-patterns
- [SEMANTIC] "Use judgment" as the decision criterion
- [SEMANTIC] Subjective triggers: "if it seems risky", "when appropriate"
```

### references/checklist-verification.md

```markdown
# Verification Checklist

## Structural
- [MUST] Quick check sub-section exists
- [SHOULD] Deep check sub-section exists (required for High risk)

## Semantic (from spec.prompt-engineering-requirements.6)
- [MUST] Quick check is concrete and executable/observable
- [MUST] Quick check measures the primary success property (not just proxy)
- [MUST] Quick check specifies expected result shape
- [MUST] Failure interpretation: what to do if check fails
- [HIGH-MUST] At least two verification modes (quick + deep)
- [SHOULD] No-network fallback for verification when feasible

## Calibration (from semantic.minimums.calibration)
- [MUST] Skill instructs "Not run (reason)" reporting for skipped checks
- [SHOULD] Verification ladder (quick → narrow → broad) for Medium+ risk

## Anti-patterns
- [SEMANTIC] "Tests pass" without specifying which tests or showing output
- [SEMANTIC] Proxy-only verification (compiles but behavior unchecked)
- [SEMANTIC] No failure handling ("if check fails, continue anyway")
```

### references/checklist-troubleshooting.md

```markdown
# Troubleshooting Checklist

## Structural
- [MUST] At least one failure mode documented
- [MUST] Each failure mode has: symptoms, likely causes, next steps

## Semantic (from spec.objective-checks.7-troubleshooting)
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

---

## Template File Specifications

### templates/wording-patterns.md

Required wording patterns from `spec.templates` (Appendix A). Use verbatim or adapt while preserving intent.

Contents:
- A.1 STOP/ask for clarification
- A.2 Ask-first for risky or breaking actions
- A.3 Evidence-first (debugging/triage/refactor)
- A.4 Minimal-change default
- A.5 Verification requirements
- A.6 Offline/restricted-environment fallback
- A.7 Decision-point phrasing

Pattern suggestions by section:

| Section | Patterns to suggest |
|---------|---------------------|
| Procedure | A.1, A.2 (if High risk), A.3 (if debugging/refactor), A.4 |
| Decision Points | A.1, A.2, A.7 |
| Verification | A.5 |
| Inputs (Constraints) | A.6 |
| Troubleshooting | Reference A.5 for "what to do if check fails" |

### templates/semantic-templates.md

Semantic quality templates from `semantic.templates` (T1-T7). Copy/paste-ready.

Contents:
- T1: Semantic contract block (When to use)
- T2: Scope fence (Inputs or Procedure)
- T3: Assumptions ledger (Inputs or Outputs for audit skills)
- T4: Decision point with observable trigger (Decision Points)
- T5: Verification ladder (Verification for Medium/High)
- T6: Failure interpretation table (Troubleshooting)
- T7: Calibration wording (Procedure, Outputs, Verification)

Template suggestions by section:

| Section | Templates to offer |
|---------|-------------------|
| When to use | T1 (semantic contract) as optional enhancement |
| Inputs | T2 (scope fence), T3 (assumptions ledger) |
| Outputs | T3 (for audit skills producing reports) |
| Decision Points | T4 (observable trigger phrasing) |
| Verification | T5 (verification ladder for Medium/High), T7 (calibration) |
| Troubleshooting | T6 (failure interpretation table) |

### templates/skill-skeleton.md

Empty structure for assembly phase with placeholders for each section.

---

## Category Integration

When a category is selected in Phase 1 (Discovery), the wizard integrates category-specific guidance.

### Category Selection

Present top 3 matching categories based on skill purpose. Show each category's "dominant failure mode" from the categories guide index. User selects one; wizard loads that category's full section.

### Category-Specific Overrides

| Section | What to pull from category guide |
|---------|----------------------------------|
| When NOT to use | Category's "When NOT to use (common misfires)" |
| Inputs | Category's "Input contract" |
| Outputs | Category's "Output contract" + "DoD checklist (objective)" |
| Decision points | Category's "Decision points library" (offer as templates) |
| Verification | Category's "Verification menu" |
| Troubleshooting | Category's "Failure modes & troubleshooting" |

### Category DoD Additions

These are IN ADDITION TO the base 10 DoD checks. Examples by category:

**debugging-triage:**
- Failure signature captured (exact error/test name)
- Root cause statement includes evidence
- Regression guard exists or rationale for omission

**refactoring-modernization:**
- Invariants explicitly stated ("behavior-preserving means...")
- Scope fence defined (what must NOT change)
- Characterization tests exist or are added

**security-changes:**
- Threat model boundaries stated
- Deny-path verification included
- Rollback plan specified

**agentic-pipelines:**
- Idempotency contract stated
- Plan/apply/verify separation exists
- All mutating steps have ask-first gates

See `references/category-integration.md` for full category coverage.

---

## Risk Tier Gating Validation

### Tier Selection Rules

**Step 1: Category default**
Start with the `Typical risk:` from the selected category.

**Step 2: Mutating action detection**
If discovery reveals ANY mutating step (writes, deletes, deploys, migrations, force operations):
- Auto-escalate to High regardless of category default
- Flag: "Mutating actions detected — treating as High risk until gating verified"

**Step 3: Gating validation (for downgrade)**
A skill with mutating actions MAY be treated as Medium risk ONLY IF all of:

1. **Ask-first gates exist** for every mutating step in Procedure
2. **Scope is bounded and reversible**
3. **Category justifies Medium** (Typical risk is Medium or lower, doesn't touch security/data/ops)

### Validation Matrix

| Condition | Gating requirement | Allowed tiers |
|-----------|-------------------|---------------|
| No mutating actions | None | Low, Medium, High |
| Mutating + all gates present + bounded scope | Full gating | Medium, High |
| Mutating + missing any gate | Incomplete | High only |
| Touches security/data/ops regardless of gating | Domain risk | High only |

### User Override Handling

If user requests to downgrade from High to Medium:

1. Wizard checks gating validation (Step 3)
2. If validation passes: Allow downgrade, log "Downgraded to Medium — gating validated"
3. If validation fails: Block downgrade, show "Cannot downgrade: [specific missing gate]"
4. User may NOT downgrade to Low if any mutating actions exist

---

## Calibration Requirements

Per the semantic addendum (`semantic.minimums.calibration`), skills MUST include calibration guidance.

### Required Calibration Elements

**In Verification section:**
- Skill instructs agent to label skipped verification as: `Not run (reason): <reason>. Run: <command> to verify.`

**In Outputs section (for skills producing recommendations/findings):**
- Output format distinguishes Verified vs Inferred vs Assumed claims
- High-risk skills require explicit calibration for any recommendations

**Calibration wording template (T7):**
```
Label conclusions as:
- Verified: supported by direct evidence (paths/commands/observations).
- Inferred: derived from verified facts; call out inference explicitly.
- Assumed: not verified; do not proceed without STOP/ask if assumption is material.

If a verification step was not run, report:
Not run (reason): <reason>. Run: <command>. Expected: <pattern>.
```

---

## Command Mention Rule

Per the strict spec (`spec.command-mention`), every command in a skill MUST specify three elements.

### Required Elements

1. **Expected result shape:** What constitutes success/failure (exit code and/or output pattern)
2. **Preconditions (when non-obvious):**
   - Required tools (with version if relevant)
   - Required environment variables
   - Required working directory
   - Required permissions
3. **Fallback path when command cannot run:**
   - Low risk: fallback SHOULD be provided
   - Medium risk: fallback SHOULD be provided; if omitted, skill MUST explain why
   - High risk: fallback MUST be provided; if impossible, skill MUST STOP and ask user

### Template

```
Run: `<command>` (from `<dir>`). Expected: `<exit/output pattern>`.
If you cannot run this (missing `<tool>` / restricted permissions / no network),
STOP and ask the user to provide: `<command output/logs>` or perform manual
inspection: `<manual steps>`.
```

### Destructive Command Requirements

If a command MAY be destructive or irreversible (deploy, migration, delete, force):
- [MUST] Ask-first gate: explicit user approval before running
- [SHOULD] Dry-run or read-only alternative offered

---

## Terminology Definitions

Key terms used in this skill:

| Term | Definition |
|------|------------|
| **Section** | One of the 8 required content areas in a skill (When to use, When NOT to use, Inputs, Outputs, Procedure, Decision points, Verification, Troubleshooting) |
| **Draft** | Generated content for a section, pending user approval. Drafts are created from discovery answers and prior approved sections. |
| **Checklist** | Section-specific validation criteria stored in `references/checklist-*.md`. Contains MUST/SHOULD/SEMANTIC tagged items. |
| **MUST** | Requirement level that blocks approval. Skill cannot proceed until fixed. |
| **SHOULD** | Requirement level that warns but allows continue. Shown in compliance summary. |
| **HIGH-MUST** | MUST for High-risk skills only. Warns for Medium, skips for Low. |
| **SEMANTIC** | Content quality check derived from semantic addendum. Detects anti-patterns and weak content. |
| **Borderline** | Content that structurally passes but doesn't clearly meet spec intent. Flagged for user decision. |
| **Quick check** | Fast verification (~seconds) of primary success property. Required for all skills. |
| **Deep check** | Slower verification (~minutes) providing higher confidence. Required for High-risk skills. |
| **Cross-section check** | Validation that references between sections are consistent (e.g., STOP/ask references valid input). |
| **Observable trigger** | A signal that can be checked programmatically: file exists, command output, grep result, test pass/fail. Contrast with subjective judgment. |
| **Objective DoD** | Definition of Done that can be verified without reading the agent's mind: artifact exists, command exits 0, pattern found/not found. |
| **Risk tier** | Classification (Low/Medium/High) that determines minimum validation requirements. Based on blast radius and reversibility. |
| **Exception** | A justified deviation from a spec requirement. Requires written rationale and alternative mitigation when applicable. |
| **Anti-pattern** | Content that indicates a quality problem: placeholder language, proxy goals, subjective triggers, etc. Detected by SEMANTIC checks. |
| **Progressive disclosure** | Keeping SKILL.md focused (<500 lines) by moving detailed content to references/ files. |
| **ask-first** | A step that requests explicit user approval before executing a breaking, destructive, irreversible, or otherwise high-risk action. An ask-first step MUST be explicit (use the phrase "ask first" or unambiguous equivalent), MUST name the specific action(s) being approved, and when feasible, MUST offer a safer alternative (dry-run/read-only or plan-only). Contrast with STOP, which pauses for missing inputs or ambiguity. |
| **STOP** | An instruction for the agent to pause execution and ask the user for clarification or approval before proceeding. A STOP step MUST be explicit (use the word "STOP" or unambiguous equivalent) and MUST name exactly what input/approval is required. Typically used for missing required inputs or ambiguity, not for risk approval (use ask-first for that). |
| **Scope fence** | An explicit boundary declaring what paths/modules the skill may touch and what it must not touch. Crossing the fence requires STOP/ask-first. |
| **Verification ladder** | A graduated verification approach: quick check (primary signal, seconds), narrow check (neighbors, minutes), broad check (system confidence, longer). Each rung must pass before proceeding. |
| **Evidence trail** | For audit/assessment skills: documentation of what was inspected (paths/queries/samples) so findings are reproducible. |
| **Idempotency** | For pipeline skills: the property that a second run produces the same result or is a no-op. |
| **Calibration** | The practice of labeling conclusions as Verified (direct evidence), Inferred (derived from verified facts), or Assumed (not verified). Also requires reporting skipped checks as "Not run (reason)". |

---

## Verification Against Official Docs

Design verified against:
- `docs/extension-reference/skills/skills-frontmatter.md` — ✓ All required fields
- `docs/extension-reference/skills/skills-content-sections.md` — ✓ All 8 sections, risk tiering
- `docs/extension-reference/skills/skills-anti-patterns.md` — ✓ All anti-patterns addressed
- `docs/extension-reference/skills/skills-validation.md` — ✓ All checklist items
- `docs/extension-reference/skills/skills-quality-dimensions.md` — ✓ All 9 dimensions

---

## Open Items

| Item | Priority | Notes |
|------|----------|-------|
| Integration with skillforge | Low | Clarify when to use wizard vs skillforge |
| Example walkthrough | Medium | Would validate design end-to-end |
| Testing strategy | Medium | Define test scenarios for wizard |

---

## Changelog

- 2026-01-13: Design review incorporating 14 fixes:
  - Fix #1: Added calibration requirements (Verified/Inferred/Assumed labeling)
  - Fix #2: Aligned fail codes with spec (two-tier validation system)
  - Fix #3: Added command mention rule (preconditions + fallbacks)
  - Fix #4: Added category integration (per-category DoD, decision points, failure modes)
  - Fix #5: Added wording patterns (Appendix A templates)
  - Fix #6: Added semantic templates (T1-T7)
  - Fix #7: Expanded cross-section check (16 checks across 4 categories)
  - Fix #8: Added risk tier gating validation (downgrade requires gating)
  - Fix #9: Specified all 8 checklist files with exact items
  - Fix #10: Documented meta-skill exception to 500-line guideline
  - Fix #11: Added session recovery via conversation checkpoints
  - Fix #12: Added terminology definitions (ask-first, STOP, scope fence, etc.)
  - Fix #13: Completed anti-pattern table (unsafe default, undeclared assumptions, etc.)
  - Fix #14: Rewrote "When NOT to Use" with explicit STOP conditions
- 2026-01-12: Initial design document created
