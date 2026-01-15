---
name: implementing-hooks
description: Use when building a hook from a design, "implement this hook",
  "write the hook", "test my hook", or "TDD for hooks". For structure reference,
  see hook-development.
---

# Implementing Hooks

Build hooks using test-driven development: observe undesired behavior first, then write the hook to fix it.

## Pipeline Context

This skill is **Stage 3: Implement** in the hooks pipeline.

| Aspect | Value |
|--------|-------|
| This stage | Build hook from design using TDD |
| Previous | `/brainstorming-hooks` (design document) |
| Next | `/optimizing-plugins` or personal use |
| Reference | `hook-development` (structural details) |

## Prerequisites Check

Before proceeding, verify:

1. **Design document exists?**
   - If yes: "I see the design at `[path]`. Proceeding with implementation."
   - If no: "No design found. Should we start with `/brainstorming-hooks`?"

2. **Design has required sections?**
   - Problem statement
   - Event selection
   - Type decision (command/prompt)
   - Security checklist

If missing: "The design is missing [sections]. Complete it first?"

## The Iron Law

```
NO HOOK CODE WITHOUT OBSERVING UNDESIRED BEHAVIOR FIRST
```

Wrote hook before testing? Delete it. Start over.

**No exceptions:** Not for "simple hooks" or "obvious fixes."

## The TDD Process

### RED: Observe Undesired Behavior

| Step | Action |
|------|--------|
| 1 | Create realistic test scenario |
| 2 | Run Claude Code WITHOUT the hook |
| 3 | Document what actually happens |
| 4 | Confirm: "This is the problem" |

**Critical:** If you cannot observe the problem, you do not understand it.

**Example:**
```bash
# Scenario: Claude writes to .env file
# Run claude --debug, ask it to edit .env
# Observe: It writes without restriction
# Document: "Without hook, Claude modifies sensitive files"
```

### GREEN: Minimal Hook

| Step | Action |
|------|--------|
| 1 | Write minimal hook addressing observed problem |
| 2 | Test with real input: `echo '<json>' \| ./hook.sh` |
| 3 | Verify output matches expectation |
| 4 | Integration test: `claude --debug` |
| 5 | Observe: Problem now blocked |

**Minimal means minimal.** Only what passes the test.

**For plugin hooks:**
- Use `${CLAUDE_PLUGIN_ROOT}` for paths
- Place in `hooks/hooks.json` with wrapper format

### REFACTOR: Harden

| Test | Input |
|------|-------|
| Empty input | `echo '{}' \| ./hook.sh` |
| Malformed JSON | `echo 'not json' \| ./hook.sh` |
| Missing fields | `echo '{"tool_name":"Write"}' \| ./hook.sh` |
| Path traversal | Paths containing `../` |

After each change: re-run all tests. Stay green.

## Testing Workflow

**Integration test with Claude Code:**

1. Register hook via `/hooks` or edit settings
2. Restart Claude Code (hooks load at startup)
3. Run `claude --debug`
4. Trigger the event
5. Verify debug output shows hook execution

**Sample input templates:**

**PreToolUse:**
```json
{
  "session_id": "test",
  "hook_event_name": "PreToolUse",
  "tool_name": "Write",
  "tool_input": { "file_path": "/path/to/file.txt", "content": "..." }
}
```

**PostToolUse:**
```json
{
  "session_id": "test",
  "hook_event_name": "PostToolUse",
  "tool_name": "Write",
  "tool_input": { "file_path": "/path/to/file.txt" },
  "tool_response": { "success": true }
}
```

**UserPromptSubmit:**
```json
{
  "session_id": "test",
  "hook_event_name": "UserPromptSubmit",
  "prompt": "User's prompt text"
}
```

## Checklist

**Use TodoWrite to track progress.**

**RED Phase:**
- [ ] Create realistic test scenario
- [ ] Run WITHOUT hook — document baseline
- [ ] Confirm observed problem matches design

**GREEN Phase:**
- [ ] Write minimal hook addressing problem
- [ ] Test with sample input
- [ ] Verify exit code and output
- [ ] Integration test with `claude --debug`
- [ ] Problem is now blocked/handled

**REFACTOR Phase:**
- [ ] Test empty input
- [ ] Test malformed JSON
- [ ] Test missing fields
- [ ] Test path traversal (if applicable)
- [ ] Security checklist passed (see brainstorming-hooks Step 5)

**Deployment:**
- [ ] Hook in correct location (settings or plugin hooks.json)
- [ ] Scripts executable (`chmod +x`)
- [ ] Commit to git

## Output

Working hook in correct location:
- **Settings hook:** `~/.claude/settings.json` or `.claude/settings.json`
- **Plugin hook:** `plugin-name/hooks/hooks.json`

Plus any scripts in `hooks/` or `scripts/` directories.

## Next Step

| Situation | Command |
|-----------|---------|
| More components to build | `/brainstorming-{component}` |
| Plugin complete, want polish | `/optimizing-plugins` |
| Personal use only | Done — hook is active |

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| Writing hook before observing | Can't verify it solves real issue | RED phase first |
| Hardcoded paths | Breaks after installation | `$CLAUDE_PROJECT_DIR` or `$CLAUDE_PLUGIN_ROOT` |
| Unquoted variables | Shell injection risk | Always `"$VAR"` |
| Exit code 0 with error intent | Wrong behavior | Exit 2 for blocking |
| Skipping edge case tests | Breaks on unexpected input | REFACTOR phase required |

## Verification

Before marking complete:

| Check | Evidence |
|-------|----------|
| Observed undesired behavior | Documented baseline |
| Hook addresses that behavior | Test passes |
| Tested with real input | Command and output shown |
| Integration tested | `claude --debug` output |
| Edge cases handled | All REFACTOR tests pass |
| Security checklist passed | 5 checks from brainstorming-hooks confirmed |

## References

- hook-development — Structural reference (file format, events, scripts)
- brainstorming-hooks — Design phase (if design needed)
- Official hooks docs — `docs/claude-code-documentation/hooks-*.md`
