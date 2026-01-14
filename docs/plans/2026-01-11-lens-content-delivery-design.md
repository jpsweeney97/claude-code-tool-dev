# Lens Content Delivery Redesign

**Date:** 2026-01-11
**Status:** Draft
**Skill:** auditing-tool-designs
**Problem:** Lens failures due to placeholder content in parallel subagent prompts

## Problem Statement

The auditing-tool-designs skill launches 4 parallel lenses via Task tool. Each lens needs the target document content to perform analysis. The current approach attempted to use placeholder text (`[Same target content as...]`) to avoid repeating large documents, which failed because:

1. **Subagents are isolated** — Task tool creates independent contexts with no shared memory
2. **Placeholders are literal text** — References to "other lenses" are meaningless strings
3. **Failure modes vary** — Robustness Critic reported missing content; Scope Minimalist hallucinated an entirely different design

**Root cause:** Token optimization instinct led to using placeholders instead of actual content, and nothing validated prompts before launch.

## Solution

Replace inline content injection with file path references. Each lens reads the target document itself using the Read tool.

## Design

### Core Mechanism

Instead of injecting `{{TARGET_CONTENT}}` (full document) into lens prompts, inject `{{TARGET_PATH}}` (file path) with mandatory read instructions.

**Lens prompt template:**

```markdown
## Target Document

**File:** {{TARGET_PATH}}

MANDATORY FIRST STEP: Read this file using the Read tool before any analysis.
Do not proceed without reading the entire file.

If you cannot read the file, output only:
"LENS FAILURE: Cannot read {{TARGET_PATH}}: [error reason]"
```

**Token impact:**
- Before: ~15K tokens × 4 lenses = ~60K tokens for content delivery
- After: ~100 tokens × 4 lenses = ~400 tokens for path references
- Savings: ~99% reduction in content delivery tokens

**What stays inline:**
- `{{ARTIFACT_SPECS}}` — Standardized specs (~3-5K tokens), needed for analysis framing
- `{{CONTEXT_ASSESSMENT}}` — Small, calibration context
- `{{SEVERITY_CALIBRATION}}` — Small, threshold settings

### Read Verification

To detect hallucination (lens produces findings without reading file), require content proof in output.

**Required output section:**

```markdown
### Read Verification
- **File read:** [path you read]
- **File size:** [X lines / Y characters]
- **First heading:** [first H1 or H2 found in document]
```

**Why this works:**
- "First heading" is specific to each document — hard to guess
- File size provides sanity check
- Missing or mismatched verification → lens marked as failed

**Arbiter validation:**
1. Check "Read Verification" section exists in each lens output
2. Compare "First heading" against actual document
3. If mismatch or missing: mark lens as FAILED, exclude from synthesis

### Error Handling

**File doesn't exist (caught early):**
```
Step 1: Validate file exists and is readable
  - If not: STOP with "Target file not found: {{PATH}}"
  - Don't launch any lenses
```

**Lens can't read file:**
```markdown
## LENS FAILURE

- **Reason:** Cannot read file
- **Path:** {{TARGET_PATH}}
- **Error:** [Permission denied / File not found / etc.]

No findings produced.
```

**Verification mismatch:**
- "First heading" doesn't match → lens excluded from synthesis
- Arbiter notes which lenses were excluded and why

**Graceful degradation:**

| Lenses Verified | Action |
|-----------------|--------|
| 4 of 4 | Full audit |
| 3 of 4 | Proceed with note in report |
| 2 of 4 | Proceed with warning |
| 1 of 4 | Abort — insufficient coverage |
| 0 of 4 | Abort — systematic failure |

### Procedure Changes

**Step 1: Read target document** — CHANGED
```
Before: Load document content into {{TARGET_CONTENT}}
After:  Validate file exists, store {{TARGET_PATH}}, capture metadata
        - Record expected first heading for verification
        - Record file size for sanity checks
```

**Step 6: Build lens prompts** — CHANGED
```
Before: Inject {{TARGET_CONTENT}} into all lens prompts
After:  Inject {{TARGET_PATH}} with read instructions
        - Use standardized READ_INSTRUCTION_BLOCK
        - Remove TARGET_CONTENT variable entirely
```

**Step 8: Collect lens outputs** — CHANGED
```
Before: Check for valid structure
After:  Check for valid structure AND read verification
        - Extract "First heading" from each lens output
        - Compare against expected value from Step 1
        - Mark unverified lenses as FAILED
        - If verified < MIN_VERIFIED_LENSES: abort
```

**Step 9: Execute Arbiter** — CHANGED
```
Before: Synthesize all lens outputs
After:  Synthesize only VERIFIED lens outputs
        - Pass verification status to Arbiter
        - Arbiter notes excluded lenses in report
```

**New constants:**
```
MIN_VERIFIED_LENSES = 2
READ_INSTRUCTION_BLOCK = """
**File:** {{TARGET_PATH}}

MANDATORY FIRST STEP: Read this file using the Read tool before any analysis.
Do not proceed without reading the entire file.

If you cannot read the file, output only:
"LENS FAILURE: Cannot read {{TARGET_PATH}}: [error reason]"
"""
```

### Lens Template Structure

Example for Spec Auditor (all 4 lenses follow same pattern):

```markdown
You are the **Spec Auditor** lens. Your goal is to verify strict compliance
with official Claude Code specifications.

## Context Assessment
- **Calibration Level:** {{SEVERITY_CALIBRATION}}
{{CONTEXT_ASSESSMENT}}

## Target Document

**File:** {{TARGET_PATH}}

MANDATORY FIRST STEP: Read this file using the Read tool before any analysis.
Do not proceed without reading the entire file.

If you cannot read the file, output only:
"LENS FAILURE: Cannot read {{TARGET_PATH}}: [error reason]"

## Artifact Specifications
{{ARTIFACT_SPECS}}

## Task
Analyze the target document for compliance with specifications...

## Required Output Format

### Read Verification
- **File read:** [path you read]
- **File size:** [lines / characters]
- **First heading:** [first H1 or H2 in document]

### Scope Statement
- **Assessed:** [list of sections examined]
- **Not assessed:** [elements skipped]
- **Confidence:** Full / Sampled / Partial

### Findings
[Standard finding format...]

### Summary
[Standard summary format...]
```

## Trade-offs

| Aspect | Impact | Accepted? |
|--------|--------|-----------|
| Each lens makes Read tool call | ~300-500ms latency per lens | Yes — parallel execution minimizes wall-clock impact |
| Specs still inline (~3-5K/lens) | ~12-20K tokens for specs | Yes — specs are standardized and smaller than docs |
| Verification adds output overhead | ~50 tokens per lens | Yes — negligible cost for reliability |
| Requires file on disk | Can't audit pasted content | Partial — could add temp file fallback |

## Implementation Checklist

- [ ] Update SKILL.md procedure (Steps 1, 6, 8, 9)
- [ ] Add READ_INSTRUCTION_BLOCK constant
- [ ] Add MIN_VERIFIED_LENSES constant
- [ ] Update all 4 lens templates with file reference block
- [ ] Add Read Verification to lens output schemas
- [ ] Add verification logic to Step 8
- [ ] Update Arbiter prompt to handle partial lens coverage
- [ ] Add graceful degradation logic
- [ ] Test with real audit to verify fix

## Verification

**Test case 1: Normal operation**
- Run audit on medium doc (~1000 lines)
- All 4 lenses should report matching "First heading"
- Full audit should complete

**Test case 2: File not found**
- Run audit on non-existent path
- Should fail at Step 1 with clear error
- No lenses should launch

**Test case 3: Lens read failure**
- Simulate lens that can't read (e.g., permission issue)
- Should see "LENS FAILURE" output
- Other lenses should continue
- Report should note excluded lens

**Test case 4: Hallucination detection**
- Manually corrupt a lens output with wrong "First heading"
- Verification should catch mismatch
- Lens should be excluded from synthesis
