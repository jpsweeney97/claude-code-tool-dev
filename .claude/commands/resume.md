---
description: Resume from a previous handoff document
argument-hint: [path]
allowed-tools: Bash, Glob, Read, Write
---

Load a handoff to restore session context.

## Procedure

1. **Find the handoff:**
   - If `$ARGUMENTS` provided: use that path directly
   - Otherwise: use Glob to find `~/.claude/handoffs/<project>/*.md` (project = git root name or cwd name), select the most recent by filename

2. **If no handoffs found:** Report "No handoffs found for this project" and STOP

3. **Read and display** the handoff content

4. **Summarize key points** from the handoff (Goal, Decisions, Next Steps)

5. **Delete the handoff file** after displaying (handoffs are single-use):
   ```bash
   rm "<handoff-path>"
   ```

6. **Ask:** "Ready to continue with [first next step]?"
