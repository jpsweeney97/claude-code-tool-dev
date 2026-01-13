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
| Validation | Section-specific checklists | Tailored checks, less filtering |
| Navigation | Full state visibility, jump anywhere | Maximum user control |
| Strictness | Tiered (MUST blocks, SHOULD warns) | Matches spec hierarchy |
| Borderline cases | Flag and ask with severity friction | Transparent, respects agency |
| Cross-section | Smart ordering + final consistency check | Prevents 90% of issues by construction |
| Impossible requirements | Justification + alternative mitigation | Addresses underlying concern |
| Empty content | Structural + semantic checks | Catches both missing structure and weak content |

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
├── SKILL.md                          # Core interaction flow (~400 lines)
├── references/
│   ├── spec-requirements.md          # MUST/SHOULD extracted from strict spec
│   ├── section-order.md              # Smart ordering with dependency rationale
│   ├── checklist-when-to-use.md      # 4 items
│   ├── checklist-when-not-to-use.md  # 5 items
│   ├── checklist-inputs.md           # 6 items
│   ├── checklist-outputs.md          # 5 items
│   ├── checklist-procedure.md        # 6 items
│   ├── checklist-decision-points.md  # 5 items
│   ├── checklist-verification.md     # 5 items
│   ├── checklist-troubleshooting.md  # 4 items
│   └── risk-tier-guide.md            # Tier selection criteria + minimums
└── templates/
    └── skill-skeleton.md             # Empty structure for assembly
```

### Why This Structure

**SKILL.md stays focused (~400 lines):** Contains the interaction flow, phase transitions, and validation orchestration. Does not embed the full spec.

**Section-specific checklists:** Each checklist is small (4-6 items), loads only when validating that section. Easier to maintain than one monolithic checklist.

**Spec requirements extracted:** The strict spec and semantic addendum are synthesized into a single reference. When specs update, one file changes.

**Smart ordering documented:** Section dependencies and rationale are explicit, not buried in SKILL.md logic.

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

### Implementation: Hybrid Checklist

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
└─────────────────────────────────────────────────────┘
```

### Validation Layers

**Layer 1 — Structural:** Required sub-parts exist (headings, format)

**Layer 2 — Semantic:** Content is specific and actionable per spec criteria

**Layer 3 — Cross-section:** References between sections are consistent

### Strictness by Tag

| Tag | Behavior |
|-----|----------|
| `[MUST]` | Blocks approve for all tiers |
| `[SHOULD]` | Warns all tiers, allows continue |
| `[HIGH-MUST]` | Blocks High tier, warns Medium, skips Low |
| `[SEMANTIC]` | Evaluates content quality against spec criteria |

### Edge Case Handling

**Empty/minimal content:**
- Structural check: sub-parts exist
- Semantic check: content is specific, not placeholder ("the inputs")
- Both must pass

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

Run at final assembly:

| Check | Catches |
|-------|---------|
| STOP/ask references valid input | Procedure says "ask for X" but X not in Inputs |
| Verification ties to artifact | Quick check doesn't relate to declared outputs |
| Decision triggers are observable | Subjective language that slipped through |
| Procedure produces declared outputs | Outputs promises artifact that procedure never creates |

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

- Reviewing an existing skill (use `skill-reviewer` agent instead)
- Quick skill scaffolding without compliance validation (use `skillforge --quick`)
- Batch auditing multiple skills (use a dedicated audit workflow)
- Simple command creation (use `.claude/commands/` directly)
- User already has a complete draft and just wants validation

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
- Anti-pattern definitions with detection patterns and fail codes

### references/section-order.md

Documents the smart ordering and dependency rationale.

Contents:
- Dependency graph visualization
- Order rationale table (position, section, depends on, enables)
- Cross-section reference types

### references/risk-tier-guide.md

Criteria for tier selection and tier-specific requirements.

Contents:
- Tier selection criteria (Low/Medium/High)
- Auto-escalation rule
- Tier-specific minimum requirements table
- Exception patterns by category

### references/checklist-*.md (8 files)

One per section. Each contains:
- Structural checks (MUST)
- Semantic quality checks (MUST/SHOULD)
- Anti-pattern checks (SEMANTIC)
- Evidence format guidance

### templates/skill-skeleton.md

Empty structure for assembly phase with placeholders for each section.

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
| Session recovery | Low | Currently stateless; could persist partial state |
| Example walkthrough | Medium | Would validate design end-to-end |
| Testing strategy | Medium | Define test scenarios for wizard |

---

## Changelog

- 2026-01-12: Initial design document created
