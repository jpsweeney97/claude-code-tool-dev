---
name: learn
description: Capture project insights. `/learn` appends an insight to `docs/learnings/learnings.md` for later promotion to CLAUDE.md via `/promote`. Use when user says "/learn", "capture this insight", "log this learning".
---

# Learn

Capture project insights for later promotion to CLAUDE.md via `/promote`.

## Procedure

1. **Identify the insight.** Review the current conversation and extract the most notable insight.

   - If the user provided a hint (e.g., `/learn the thing about Codex infrastructure`), focus on that topic.
   - If no hint, identify the insight that would be most valuable in a future session — patterns discovered, mistakes caught, techniques that worked, architectural decisions and their reasoning.
   - Prefer specific, actionable insights over general observations.

2. **Select tags** from the table below. Pick 1-3 tags that fit. Create a new tag if none fit.

3. **Draft the entry** using the structured format and present for confirmation:

   ```
   Draft learning:

   ### YYYY-MM-DD [tag1, tag2]

   **Context:** One sentence — what were you doing when this came up.

   **Insight:** The actual learning — what you discovered, decided, or confirmed.

   **Implication:** What to do differently going forward.

   Append to docs/learnings/learnings.md?
   ```

   **Why this structure:** Context helps `/promote` judge breadth (task-specific or general?). Insight is the core content that becomes a CLAUDE.md instruction. Implication signals actionability — no implication may mean not promotable.

   **Freeform accepted.** If the insight doesn't fit this structure naturally, a single self-contained paragraph is fine. Existing entries stay as-is; no migration.

4. **On confirmation, append the entry** to `docs/learnings/learnings.md`.

   If the file does not exist, create it with this header first:

   ```markdown
   # Learnings

   Project insights captured from consultations. Curate manually: delete stale entries, merge duplicates.
   ```

   Append using this format (preserve the blank line before the heading):

   ```markdown

   ### YYYY-MM-DD [tag1, tag2]

   **Context:** What you were doing.

   **Insight:** What you discovered.

   **Implication:** What to do differently.
   ```

   If using freeform format, write a single self-contained paragraph instead of the three fields.

5. **Confirm** with a one-line summary: the date, tags, and first ~10 words of the insight.

### Example Tags

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
