# Capture Mode

Automatically detect and queue Claude Code claims made during a conversation. Useful for building the known-claims cache from real usage patterns.

## Workflow

```
Input: /verify --capture
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│ Step C1: Scan Conversation                               │
│ Read all messages in current session                     │
│ Focus on Claude's responses (primary claim source)       │
└─────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│ Step C2: Detect Claude Code Claims                       │
│ Pattern matching for:                                    │
│ • Feature existence ("supports", "has")                  │
│ • Configuration ("required", "optional", "default")      │
│ • Behavior ("when X", "exit code", "timeout")            │
│ • Capability ("can", "cannot", "allows")                 │
└─────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│ Step C3: Filter                                          │
│ Remove:                                                  │
│ • Questions (not assertions)                             │
│ • Opinions/preferences                                   │
│ • Non-Claude Code topics                                 │
│ • Duplicates (already in known-claims.md)                │
└─────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│ Step C4: Cluster and Queue                               │
│ Assign section: Skills, Hooks, Commands, etc.            │
│ Append to pending-claims.md with:                        │
│ • Verdict: ? Captured                                    │
│ • Evidence: (captured from conversation)                 │
│ • Date: today                                            │
└─────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│ Step C5: Report                                          │
│ "Captured N claims from conversation"                    │
│ List claims by section                                   │
│ "Run /verify to verify and promote"                      │
└─────────────────────────────────────────────────────────┘
```

## Triggers

- `/verify --capture` - Scan conversation for Claude Code claims
- "capture claims from this conversation" - Natural language
- "what Claude Code claims have I made?" - Reflective capture

## When to Use

- At end of session after discussing Claude Code features
- After receiving answers about Claude Code capabilities
- To build cache from real-world usage patterns
- Before closing a technical discussion about Claude Code

## Detection Patterns

Claims are detected using these pattern categories:

| Category | Patterns | Example |
|----------|----------|---------|
| **Feature existence** | "supports", "has", "includes" | "Claude Code supports hooks" |
| **Configuration** | "required", "optional", "default is" | "The name field is required" |
| **Behavior** | "when you", "exit code N means", "timeout" | "Exit code 2 blocks execution" |
| **Capability** | "can", "cannot", "allows", "prevents" | "Hooks cannot access network" |
| **Format** | "uses X format", "in Y syntax" | "MCP uses JSON format" |
| **Limits** | "max N", "up to N", "limited to" | "Skill names max 64 characters" |

## Filtering Rules

Not all statements are claims. Filter out:

| Filter | Example | Reason |
|--------|---------|--------|
| Questions | "Does Claude Code support X?" | Not an assertion |
| Opinions | "I think hooks are useful" | Subjective |
| Non-CC topics | "Python uses indentation" | Not Claude Code |
| Already known | (matches known-claims.md) | Duplicate |
| Hedged | "might", "possibly", "I'm not sure" | Insufficient confidence |

## Output Format

Captured claims are appended to `pending-claims.md`:

```markdown
| Claim | Verdict | Evidence | Section | Date |
|-------|---------|----------|---------|------|
| Exit code 2 blocks hook execution | ? Captured | (captured from conversation) | Hooks | 2026-01-06 |
| Skills require name field | ? Captured | (captured from conversation) | Skills | 2026-01-06 |
```

**Verdict `? Captured`** indicates the claim needs verification before promotion. Run `/verify` to:
1. Review captured claims
2. Verify against official docs
3. Update verdict (✓, ✗, ~)
4. Promote to known-claims.md

## Report Example

```markdown
## Capture Report

**Session scanned:** Current conversation
**Claims detected:** 12
**After filtering:** 7 (5 duplicates removed)

### Captured Claims by Section

**Hooks (3)**
- Exit code 2 blocks hook execution
- Hooks run in parallel when multiple match
- Default timeout is 60 seconds

**Skills (2)**
- Skills require name field in frontmatter
- allowed-tools restricts tool access

**MCP (2)**
- Project scope requires user approval
- Environment variables expand in .mcp.json

---

*Run `/verify` to verify these claims and promote to known-claims.md*
```

## Session-End Reminder Hook

A **SessionEnd hook** automatically reminds you to capture claims when Claude Code was discussed.

### How It Works

1. When your session ends, the hook scans the transcript
2. Looks for Claude Code keywords (hooks, skills, MCP, frontmatter, etc.)
3. If 3+ keywords detected, outputs a reminder
4. Suppressed if `/verify --capture` was already run

### Hook Location

`.claude/hooks/verify-capture-reminder.py`

### Example Reminder

```
---
Tip: This session discussed Claude Code topics.
Consider running `/verify --capture` to queue claims for verification.
(Detected 7 Claude Code keywords)
---
```

### To Enable

After promoting, run `uv run scripts/sync-settings` to add hook to settings.json.
