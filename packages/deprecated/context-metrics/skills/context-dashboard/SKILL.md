---
name: context-dashboard
description: Show detailed context window metrics. Use when user asks about context usage, token counts, or window occupancy.
---

# Context Dashboard

Show detailed context window occupancy metrics by reading the current session's JSONL transcript.

## Procedure

1. Read the current session's transcript path from the conversation context (look for `transcript_path` in recent hook inputs or system state).
2. If transcript path is not available, inform the user: "Cannot determine transcript path. Context metrics require an active session with transcript logging."
3. Read the JSONL file at the transcript path.
4. Scan ALL records (not just tail) to compute:
   - **Current occupancy:** Last valid assistant record's usage (input + cache_read + cache_create tokens)
   - **Message count:** Count of records with `type == "user"` or `type == "assistant"`
   - **Compaction count:** Count of records with `subtype == "compact_boundary"` or `type == "system"` with compact metadata
   - **Session duration:** Time from first to last record timestamp
5. Read config from `~/.claude/context-metrics.local.md` for window size and soft boundary.
6. Format and display:

```
## Context Dashboard

**Window:** {occupancy}/{window} tokens ({pct}%)
**Messages:** {count} | **Compactions:** {compaction_count}
**Phase:** {compaction_count + 1} (current)
```

If soft_boundary is configured and occupancy approaches or exceeds it, add a warning line.

## Limitations (v1)

- No category breakdown (requires devtools `/groups` endpoint — deferred to v1.1)
- No phase history (requires tracking pre-compaction sizes from `compact_boundary` markers — deferred to v1.1)
- No cost data unless devtools is running
- Reading full JSONL may be slow for very long sessions (>100MB transcripts)
