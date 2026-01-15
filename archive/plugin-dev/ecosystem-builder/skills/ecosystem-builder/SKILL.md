---
name: ecosystem-builder
description: |
  Trigger autonomous ecosystem expansion. Use when asked to "build skills", "expand ecosystem", "find gaps", or "generate artifacts".
license: MIT
metadata:
  version: 0.2.0
  model: claude-opus-4-5-20251101
  domains: [meta, automation, skills]
  type: orchestrator
allowed-tools:
  - Bash
  - Read
  - Task
---

# Ecosystem Builder

Autonomous workflow that expands the skill ecosystem by finding gaps, building artifacts, and staging for review.

## Triggering

When the user asks to:
- "Build N skills"
- "Expand the ecosystem"
- "Find gaps in skills"
- "Generate new skills"

## Process

1. **Parse the request** to determine budget:
   - Number of artifacts (required)
   - Time limit (optional, default 4 hours)
   - Cost limit (optional, default $50)

2. **Start the run:**
   ```bash
   # For testing (uses mock callable)
   ~/.claude/plugins/ecosystem-builder/bin/ecosystem-builder run --artifacts N --mock

   # For production (requires Claude Code callable)
   ~/.claude/plugins/ecosystem-builder/bin/ecosystem-builder run --artifacts N
   ```

3. **Monitor progress:**
   ```bash
   ~/.claude/plugins/ecosystem-builder/bin/ecosystem-builder status
   ```

4. **Report completion** with summary of:
   - Artifacts analyzed, built, passed, failed
   - Location of staged artifacts
   - Next step: review with `ecosystem-builder review`

## Example

User: "Build 5 new skills for me"

Response: "I'll start an ecosystem-builder run to generate 5 skills."

```bash
~/.claude/plugins/ecosystem-builder/bin/ecosystem-builder run --artifacts 5
```

"The run is in progress. I'll monitor and report when complete."

## Architecture

### Hybrid Generation Strategy

| Gap Complexity | Method | When Used |
|---------------|--------|-----------|
| Simple | Direct template | MISSING_SKILL with confidence ≥ 0.7 |
| Complex | Subagent | WORKFLOW_HOLE, INCOMPLETE_ARTIFACT, or confidence < 0.7 |

Complex gaps use the `SkillGeneratorAgent` which:
1. Builds a prompt with gap context and type-specific guidance
2. Invokes Claude Code's Task tool for generation
3. Validates response structure before staging

## Limitations

- Subagent generation requires Claude Code runtime (mock callable for tests)
- Skills are staged, not auto-deployed to production
- Human review required via `ecosystem-builder review`
- Validation panel checks structure, quality, integration (no semantic analysis)
- Gap analysis uses heuristics (expected patterns, structural checks)
