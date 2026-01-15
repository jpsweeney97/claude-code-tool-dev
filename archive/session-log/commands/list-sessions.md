---
description: Browse and search session history
argument-hint: "[project] [--after DATE] [--before DATE]"
allowed-tools:
  - Read
---

Browse session history for: $ARGUMENTS

Use the session-log MCP `list_sessions` tool to find matching sessions.

Display results in a table format showing:
- Date
- Project
- Branch
- Duration (minutes)
- Title

If a specific session is mentioned, use `get_session` to show its full content.
