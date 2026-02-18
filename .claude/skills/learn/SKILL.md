---
name: learn
description: Capture a project insight for re-injection in future sessions. Claude drafts the insight from the current conversation, user confirms. Appends a timestamped, tagged entry to docs/learnings/learnings.md. Use when user says "/learn", "capture this insight", "remember this for future sessions", or "log this learning".
argument-hint: "[optional: hint about what to capture]"
---

# Learn

Extract an insight from the current conversation and append it to the project's learnings file for re-injection in future sessions.

## Instructions

1. **Identify the insight.** Review the current conversation and extract the most notable insight.

   - If the user provided a hint (e.g., `/learn the thing about Codex infrastructure`), focus on that topic.
   - If no hint, identify the insight that would be most valuable in a future session — patterns discovered, mistakes caught, techniques that worked, architectural decisions and their reasoning.
   - Prefer specific, actionable insights over general observations.

2. **Select tags** from the example table below. Pick 1-3 tags that fit. Create a new tag if none fit.

3. **Draft the entry** and present it to the user for confirmation:

   ```
   Draft learning:

   ### YYYY-MM-DD [tag1, tag2]

   One paragraph capturing the insight — specific enough to be actionable
   when re-read in a future session without the original context.

   Append to docs/learnings/learnings.md?
   ```

   Write the insight as a single paragraph. It should be self-contained — a future Claude session reading this entry should understand the insight without access to the original conversation.

4. **On confirmation, append the entry** to `docs/learnings/learnings.md`.

   If the file does not exist, create it with this header first:

   ```markdown
   # Learnings

   Project insights captured from consultations. Curate manually: delete stale entries, merge duplicates.
   ```

   Append using this exact format (preserve the blank line before the heading):

   ```markdown

   ### YYYY-MM-DD [tag1, tag2]

   The insight paragraph.
   ```

5. **Confirm** with a one-line summary: the date, tags, and first ~10 words of the insight.

## Example Tags

Use consistent tags across entries. Common tags for this project:

| Tag | Use for |
|-----|---------|
| `codex` | Insights from Codex dialogues |
| `architecture` | Architectural decisions and patterns |
| `debugging` | Debugging techniques and root causes |
| `workflow` | Process and workflow improvements |
| `testing` | Testing strategies and patterns |
| `security` | Security considerations |
| `pattern` | Reusable code or design patterns |
| `performance` | Performance optimization |
| `skill-design` | Skill authoring insights |
| `review` | Code review and feedback patterns |

These are examples, not a closed set. Create new tags when none fit.

## Examples

### After a Codex dialogue

**User runs `/learn`** after a Codex dialogue about module boundaries.

**Claude reviews the conversation**, identifies the most reusable insight from the dialogue, and drafts:

```
Draft learning:

### 2026-02-17 [codex, review]

When using Codex for design review, expect infrastructure-grade defaults on
the first turn (compatibility shims, explicit anchors, semver versioning).
The value comes from the challenge phase — push back on cost-benefit for the
actual project scale. 5 of 5 contested claims in the migration dialogue
followed this pattern: Codex proposed general-purpose infrastructure, Claude
challenged for project-specific context, Codex conceded.

Append to docs/learnings/learnings.md?
```

### After debugging

**User runs `/learn`** after a session that uncovered a non-obvious root cause.

**Claude identifies the debugging insight** and drafts:

```
Draft learning:

### 2026-02-17 [debugging, pattern]

When a hook's additionalContext doesn't appear in Claude's context, check the
system-reminder tag format — it arrives as "PostToolUseFailure:Bash hook
additional context:" not as a standalone message. Searching for the wrong
format leads to false negatives.

Append to docs/learnings/learnings.md?
```

### With a hint

**User:** `/learn the Codex infrastructure pattern`

**Claude focuses on that topic** and drafts:

```
Draft learning:

### 2026-02-17 [codex, architecture]

Codex consistently over-proposes infrastructure (compatibility shims, explicit
anchor IDs, semver versioning). Challenge every first-turn proposal on
cost-benefit for project scale — the value comes from the challenge phase, not
the initial breadth. 5 of 5 contested claims in the migration dialogue
followed this pattern.

Append to docs/learnings/learnings.md?
```

### User wants to edit

If the user says "change the tags" or "rephrase to...": revise the draft and present again. Do not append until the user confirms.
