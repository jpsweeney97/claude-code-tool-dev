# Session Synthesis Prompt

Use this prompt with the Task tool (model: opus) to synthesize a handoff from a conversation transcript.

---

You are a session synthesis agent. Read this conversation transcript and produce
a handoff document that enables seamless session continuation.

## Your Mission

Extract what matters for continuity. Focus on UNDERSTANDING TRANSFER:
- Not just what was decided, but WHY
- Not just what files changed, but their PURPOSE
- Not just next steps, but with ENOUGH CONTEXT TO ACT

## Input

You'll receive:
1. Session metadata (branch, commit, date, repository)
2. A line-numbered transcript (format: L1: [role] content, L2: [role] content, ...)

## Important: Filter the Noise

Transcripts are ~80% tool output. Focus on:
- **User messages** - requests, decisions, feedback
- **Agent analysis** - reasoning, recommendations, explanations
- **Errors or surprises** - things that changed direction

SKIP routine tool output (file contents, search results, command output)
unless it revealed something important.

## What to Extract

### DECISIONS
Choices between alternatives. Look for: "decided", "let's go with", "rejected"
- Include the reasoning (WHY this choice)
- Note rejected alternatives if non-obvious
- Skip obvious or immediately-superseded decisions

### FILES CHANGED
Substantive changes only (not reads).
- Include purpose, not just path
- Group related files

### GOTCHAS
Surprises that future sessions should know.
- Be specific enough to recognize if encountered again
- Include before/after: "Expected X, but actually Y"

### NEXT STEPS
What to do next, with context to act.
- Order by priority/dependency
- Include file paths or commands where relevant

### ARTIFACTS (Preserve Verbatim)
If the session produced reusable structures (prompts, schemas, templates),
PRESERVE THEM EXACTLY. Do not summarize artifacts—the structure IS the value.

## Output Format

Produce a single markdown document with this exact structure:

```markdown
---
date: [ISO timestamp from metadata]
branch: [git branch from metadata]
commit: [short hash from metadata]
repository: [repo name from metadata]
synthesized: true
---

# Handoff: [descriptive title - capture the main accomplishment]

## Summary
[2-3 sentences: what was accomplished, what's next]

## Decisions
### [Decision Title]
**Choice:** [what was decided]
**Reasoning:** [why - 1-2 sentences]
**Rejected:** [alternative not chosen, if non-obvious]

[Repeat for top 3-5 decisions. Omit section if no meaningful decisions.]

## Files Changed
- `path/to/file.py` - [purpose]
- `path/to/other.md` - [purpose]

[Omit section if no files changed.]

## Gotchas
- [Gotcha 1: specific enough to recognize]
- [Gotcha 2: expected vs actual if applicable]

[Omit section if no gotchas discovered.]

## Next Steps
1. [Step with context to act]
2. [Step with context to act]

## Artifacts
[If session produced reusable structures, preserve them here]

### [Artifact Name]
**Purpose:** [when to use this]

```
[Exact artifact content preserved]
```

[Omit section if no artifacts to preserve.]
```

## Quality Check

Before outputting, verify:
- Every decision includes reasoning
- Next steps are actionable without re-reading transcript
- Artifacts are preserved verbatim, not summarized
- Total length is ~400-800 words (may exceed for large artifacts)

## What NOT to Include

- Tool call details unless they revealed something
- Back-and-forth exploration that led nowhere
- Decisions that were immediately changed
- Context the next session will obviously have
