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
  - Edit
  - Glob
  - Grep
  - Bash
  - AskUserQuestion
---

# Skill Wizard

## When to Use

- User wants to create a new Claude Code skill from scratch
- User has an idea but doesn't know the spec requirements
- User wants guided, interactive skill authoring with validation
- User says "create a skill", "new skill", "skill wizard", "/skill-wizard"

**Primary goal:** Guide authors from skill idea to spec-compliant SKILL.md through structured dialogue, draft generation, and inline validation.

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

## Decision Points

- **If output path has SKILL.md with `metadata.wizard.status: draft`:**
  Offer to resume from where wizard left off. Present section progress.
  User can [Resume] or [Start fresh].

- **If output path has complete SKILL.md (no wizard metadata):**
  Ask user to confirm overwrite or choose new path.
  Do not overwrite without confirmation.

- **If the skill's purpose involves activities from 2+ categories** (e.g., "refactoring security code" spans refactoring-modernization and security-changes):
  Present the matching categories with trade-offs, ask user to choose.
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

## Verification

**Quick check:**

```bash
test -f <path>/SKILL.md && grep -c -- "^## " <path>/SKILL.md
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

**If deep check fails:**
- If `name` invalid: Fix frontmatter. Name must be kebab-case, <=64 chars.
- If `description` missing/too long: Add or trim description (<=1024 chars).
- If `metadata.wizard` block present: Wizard didn't complete cleanup. Remove block manually or re-run final phase.
- If section checklist fails: Navigate to failing section, show specific violation, re-validate after fix.
- If compliance summary mismatch: Re-run cross-section validation (Phase 4).

**Calibration:**
If any verification step was not run, report:
`Not run (reason): <reason>. Run: <command>. Expected: <pattern>.`

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
- Check if parent directory exists: `ls -la <parent-of-output-path>`
- Check permissions on target: `ls -la <output-path>`
- Offer alternative: present skill in conversation for manual copy

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
