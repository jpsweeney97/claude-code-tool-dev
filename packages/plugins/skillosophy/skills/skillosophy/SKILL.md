---
name: skillosophy
description: Collaborative skill creation with deep methodology and multi-agent synthesis. Merges skill-wizard's interactive dialogue with skillforge's deep analysis.
license: MIT
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - Task
  - AskUserQuestion
  - TodoWrite
user-invocable: true
metadata:
  version: "1.0.0"
  category: meta-skills
  risk_tier: "Medium — creates artifacts that affect other workflows"
---

# skillosophy

Collaborative skill creation with deep methodology and multi-agent synthesis.

## Triggers

- "create a skill"
- "new skill for"
- "build a skill"
- "design a skill"
- "skillosophy"
- "help me make a skill"

## When to Use

- User wants to create a new reusable skill
- User wants to review an existing skill with synthesis panel
- User wants to validate a skill against checklists
- Task involves creating automation that should be repeatable
- User describes a workflow they want to codify

## When NOT to Use

- One-off task that won't be repeated
- User wants to execute an existing skill (just run it)
- User wants to edit skill content directly (use Edit tool)
- Modifying skillosophy itself (circular dependency)

## Inputs

### Required
- **User intent**: Natural language description of skill goal (for CREATE mode)
- **Skill path**: Path to existing SKILL.md (for REVIEW/VALIDATE modes)

### Optional
- **Mode override**: Explicit "create", "review", or "validate" to skip detection
- **Existing skill context**: For MODIFY mode, the skill to improve

### Assumptions
- User has write access to target directory
- Python available for triage scripts (graceful degradation if not)
- Opus model available for synthesis panel (falls back to Sonnet)

## Outputs

### Primary Artifact
- **SKILL.md**: Complete skill file with all 11 sections + frontmatter

### Embedded Metadata
- **metadata.decisions**: Requirements, approach, alternatives, risk tier, methodology insights
- **Session State**: Transient progress tracking (removed after approval)

### Definition of Done
- [ ] All 11 body sections present and pass [MUST] validation
- [ ] Frontmatter parses correctly with required fields
- [ ] metadata.decisions captures collaborative dialogue
- [ ] Synthesis panel returns unanimous APPROVED (CREATE mode)
- [ ] Session State removed (CREATE mode, after approval)

## Procedure

### Phase 0: Triage

1. **Parse user intent** — Identify if CREATE, REVIEW, VALIDATE, or ambiguous
2. **Check for mode signals**:
   - "review", "panel", "synthesis" + path → REVIEW
   - "validate", "check", "lint" + path → VALIDATE
   - "create", "new", "build", "design" → CREATE
   - Path only → Ask: "Review or Validate?"
   - Ambiguous → Ask: "What would you like to do?"
3. **Self-modification guard** — If target path is within skillosophy plugin directory, block with explanation
4. **Run triage script** (CREATE mode only):
   ```bash
   python scripts/triage_skill_request.py "<user goal>" --json
   ```
5. **Handle triage result**:
   - `USE_EXISTING` (≥80% match) → Recommend existing; ask to proceed or create anyway
   - `IMPROVE_EXISTING` (50-79%) → Offer to modify existing skill
   - `CREATE_NEW` (<50%) → Proceed to Phase 1
   - `CLARIFY` → Ask clarifying question
   - Script failure → Warn and proceed to CREATE

### Phase 1: Deep Analysis (Collaborative)

6. **Initialize TodoWrite** with high-level tasks
7. **Requirements discovery dialogue**:
   - Ask about purpose, constraints, success criteria
   - One question at a time, prefer multiple choice
   - Apply 11 thinking lenses internally
   - Surface insights that advance conversation
8. **Capture explicit requirements** in growing metadata.decisions
9. **Explore approaches** (2-3 alternatives):
   - Present options with trade-offs
   - Lead with recommendation and rationale
   - Document chosen approach and rejected alternatives
10. **Determine risk tier**:
    - Low: Documentation, research, read-only
    - Medium: Code generation, refactoring, testing
    - High: Security, data migration, infrastructure, agentic
11. **Select category** from 21 defined categories
12. **Run regression questioning** internally (up to 7 rounds)
13. **Create Session State** at end of Phase 1

### Phase 2: Specification Checkpoint (Collaborative)

14. **Present consolidated summary**:
    ```
    Based on our discussion, here's what we're building:

    **Purpose:** [one sentence]

    **Requirements:**
    - Explicit: [what you asked for]
    - Implicit: [what you expect]
    - Discovered: [what analysis revealed]

    **Approach:** [chosen] because [rationale]
    **Rejected:** [alternatives] because [reasons]

    **Risk Tier:** [level] because [justification]
    **Category:** [category]

    Does this capture your intent correctly?
    ```
15. **Iterate until user validates** — If corrections needed, update metadata.decisions
16. **Lock decisions** — After validation, decisions are stable for generation

### Phase 3: Generation (Collaborative)

17. **Generate sections in order**:
    1. Triggers
    2. When to use
    3. When NOT to use
    4. Inputs
    5. Outputs
    6. Procedure
    7. Decision Points
    8. Verification
    9. Troubleshooting
    10. Anti-Patterns
    11. Extension Points

18. **For each section**:
    a. Draft content informed by Phase 1-2 decisions
    b. Run section checklist ([MUST], [SHOULD], [SEMANTIC])
    c. Present draft + validation results to user
    d. User approves, edits, or requests regeneration
    e. Write approved section to SKILL.md
    f. Update Session State progress

19. **Handle Session State ordering**:
    - Session State is always last section
    - If it exists from previous partial run, read it, remove it, append new section, re-append Session State

20. **After all 11 sections**:
    - Run cross-section validation (Semantic Coherence)
    - Update Session State to show 11/11 complete

### Phase 4: Synthesis Panel (Autonomous)

21. **Check skill size** — If >1000 lines, warn about scope creep
22. **Launch 4 agents in parallel** via Task tool:
    ```
    Task: Executability Auditor - review skill
    Task: Semantic Coherence Checker - review skill
    Task: Dialogue Auditor - review skill
    Task: Adversarial Reviewer - review skill
    ```
23. **Handle model fallback**:
    - Try Opus for all agents
    - If any fail, retry failed agents with Sonnet
    - If still failing, skip panel with warning
24. **Collect verdicts** — All 4 must return
25. **Check for unanimous APPROVED**:
    - All APPROVED → Proceed to finalization
    - Any CHANGES_REQUIRED → Loop-back

### Loop-Back (if needed)

26. **Classify severity** of each issue:
    - Minor: Single section, wording/clarity → Propose-and-confirm
    - Major: Multiple sections, design/decision → Full collaboration
27. **Handle contradictions** between agents:
    - Present all findings together
    - Flag conflicts explicitly
    - User decides resolution
28. **Apply adaptive iteration limits**:
    - Progress made? Continue (up to 5 iterations)
    - Same issues recurring? Escalate immediately
    - Different issues? Continue (up to 3 iterations)
29. **Re-submit to panel** after fixes

### Finalization

30. **Remove Session State**:
    - Find `## Session State` (must be last H2)
    - Truncate from that point forward
    - Write cleaned SKILL.md
31. **Confirm completion**:
    ```
    ✅ Skill approved and finalized.

    Created: <path>/SKILL.md
    Sections: 11/11
    Panel: Unanimous APPROVED

    Next: Test with "/<skill-name>" or install plugin
    ```

## Decision Points

### Mode Detection
| Signal | Mode | Confidence |
|--------|------|------------|
| "create", "new", "build" | CREATE | High |
| "review", "panel" + path | REVIEW | High |
| "validate", "check" + path | VALIDATE | High |
| Path only | — | Ask user |
| Ambiguous | — | Ask user |

**Default:** If genuinely unclear after asking, default to CREATE.

### Triage Routing
| Match Score | Action |
|-------------|--------|
| ≥80% | Recommend existing, ask to proceed |
| 50-79% | Offer MODIFY or CREATE |
| <50% | Proceed to CREATE |

**Default:** On script failure, proceed to CREATE with warning.

### Loop-Back Severity
| Signal | Severity |
|--------|----------|
| Single section affected | Minor |
| Multiple sections affected | Major |
| Wording/clarity issue | Minor |
| Design/decision issue | Major |

**Default:** When uncertain, escalate to Major (safer).

### Model Selection
| Attempt | On Failure |
|---------|------------|
| All agents Opus | Retry failed with Sonnet |
| Mixed Opus/Sonnet | Continue |
| All Sonnet failing | Skip panel, mark skill |

**Default:** Prefer Opus for quality; accept Sonnet as fallback.

## Verification

### Quick Checks
1. **Frontmatter parses**: `Read SKILL.md` → YAML loads without error
2. **All sections present**: 11 H2 headings (Triggers through Extension Points)
3. **Session State removed**: No `## Session State` in final skill
4. **metadata.decisions present**: Contains requirements, approach, risk_tier

### Full Validation
Run checklists for each section:
```bash
# Conceptual — implemented as inline checks
for section in [triggers, when-to-use, ...]:
    run_checklist(section)
    report_violations()
```

### Panel Verification
All 4 agents return one of:
- `APPROVED` — No blocking issues
- `CHANGES_REQUIRED` — Issues need resolution

Unanimous `APPROVED` required for finalization.

## Troubleshooting

### Triage Script Failures

| Symptom | Cause | Recovery |
|---------|-------|----------|
| "command not found" | Python not available | Skip triage; proceed to CREATE with warning |
| Non-zero exit code | Script error | Log output; proceed to CREATE |
| Malformed JSON | Script bug | Ask user: create new or specify existing path |
| Timeout (>30s) | Large index or slow disk | Skip triage with warning |

### Panel Agent Failures

| Symptom | Cause | Recovery |
|---------|-------|----------|
| Model error on Opus | Quota/availability | Retry with Sonnet |
| All agents timeout | Network/service issue | Skip panel; mark skill as `panel_status: skipped` |
| Contradictory verdicts | Genuine ambiguity | Present both; user decides |

### Session Recovery

| Symptom | Cause | Recovery |
|---------|-------|----------|
| Malformed SKILL.md | Interrupted write | Check for .backup file; offer restore |
| Missing Session State | Clean or old skill | Reconstruct from metadata.decisions + section count |
| Progress mismatch | Bug or manual edit | Re-validate existing sections; update state |

### Backup Failures

| Symptom | Cause | Recovery |
|---------|-------|----------|
| Can't create backup | Disk full/permissions | Warn user; proceed without backup |
| .backup exists but stale | >24 hours old | Ignore or delete; use current file |

## Anti-Patterns

### Process Anti-Patterns

| Pattern | Consequence | Instead |
|---------|-------------|---------|
| Skipping Phase 2 checkpoint | Misalignment surfaces in Phase 3 | Always validate understanding before generation |
| Accepting all panel feedback | May conflict or be wrong | Evaluate each finding; contradictions need user judgment |
| Rushing through dialogue | Poor requirements capture | One question at a time; let user think |

### Content Anti-Patterns

| Pattern | Consequence | Instead |
|---------|-------------|---------|
| Vague triggers ("help me") | False positives | Specific verb+noun phrases |
| Procedure with "as appropriate" | Unexecutable | Specify exact action |
| Methodology insights = "considered X" | Appears superficial | Document specific findings and affected sections |

### Scope Anti-Patterns

| Pattern | Consequence | Instead |
|---------|-------------|---------|
| >1000 line skill | Scope creep; hard to maintain | Split into focused skills |
| Skill does everything | Jack of all trades | Compose multiple focused skills |
| Modifying skillosophy itself | Circular dependency | Edit plugin files directly |

## Extension Points

1. **Batch validation mode**: Run VALIDATE on multiple skills in directory
2. **Category-specific templates**: Pre-populated sections for common categories
3. **Panel feedback history**: Show what previous iterations flagged
4. **CI/CD integration**: Exit codes for automated validation pipelines
5. **Skill composition**: Creating skills that chain with others
6. **Custom panel agents**: Allow users to add domain-specific reviewers
