---
description: Resume from a previous handoff document
argument-hint: [path]
allowed-tools: Bash, Glob, Read, Write
---

**Session ID:** ${CLAUDE_SESSION_ID}

Load a handoff to restore session context.

## Procedure

When user runs `/resume [path]`:

1. **Note the session ID** from the "Session ID:" line above (substituted by Claude Code at load time)

2. **Find the handoff:**
   - If `$ARGUMENTS` provided: use that path directly
   - Otherwise: use Glob to find `~/.claude/handoffs/<project>/*.md` (project = git root name or cwd name), select the most recent by filename

3. **If no handoffs found:** Report "No handoffs found for this project" and STOP

4. **Read and display** the handoff content

5. **Summarize key points** from the handoff (Goal, Decisions, Next Steps)

6. **Archive the handoff:**
   - Create `~/.claude/handoffs/<project>/.archive/` if needed
   - Move handoff to `.archive/<filename>`:
     ```bash
     mkdir -p ~/.claude/handoffs/<project>/.archive
     mv "<handoff-path>" ~/.claude/handoffs/<project>/.archive/
     ```

7. **Write state file:**
   - Create `~/.claude/.session-state/` if needed
   - Write archive path to `~/.claude/.session-state/handoff-<session_id>` (using UUID from step 1):
     ```bash
     mkdir -p ~/.claude/.session-state
     echo "<archive-path>" > ~/.claude/.session-state/handoff-<session_id>
     ```

8. **Ask:** "Ready to continue with [first next step]?"
