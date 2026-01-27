---
name: brainstorming-hooks
description: Use when designing a hook, exploring what hooks can do, improving an existing hook, or when behavior feels automatable but unsure how to hook it.
---

# Brainstorming Hooks

## Overview

Turn hook ideas into concrete designs through collaborative exploration of the hook design space. Hooks have a rich surface area (12 event types, 3 hook types, JSON output control, matchers) that's easy to underuse — this skill surfaces creative possibilities before converging on a design.

**Outputs:**
- Multiple candidate approaches (sketches) with trade-offs
- Implemented hook in appropriate location:
  - Script hooks: `.claude/hooks/<name>.py` + settings.json entry
  - Prompt hooks: settings.json entry only
  - Component-scoped: frontmatter in skill/command/agent
  - Plugin hooks: `hooks/hooks.json` + script
- Design context at `docs/plans/YYYY-MM-DD-<hook-name>-design.md`

**Definition of Done:**
- Goal understood through discussion
- Design space explored (event types, hook types, output mechanisms)
- Multiple approaches surfaced with trade-offs
- One approach selected and fully specified
- Hook implemented in appropriate location
- Settings synced if needed (`uv run scripts/sync-settings`)
- Checkpoint checklist verified
- User confirmed hook addresses their intent

## When to Use

- **Specific behavior wanted** — "I want to X" but unsure if/how hooks can help
- **Vague sense hooks could help** — "Something feels automatable" but no clear target
- **Improving an existing hook** — have one, want to explore what else it could do
- **Proactive exploration** — no immediate need, just want to understand capabilities

**Not for:**
- Testing a hook (separate concern)
- Deciding hook vs. other mechanism (this skill assumes hooks are the answer)

## Process

### Phase 1: Understand the Goal

Start from whatever the user brings:
- **Specific behavior:** "I want to block X" → clarify exactly what triggers it and what should happen
- **Vague sense:** "Something feels automatable" → explore what's repetitive or error-prone
- **Existing hook:** "I have this hook" → understand what it does and what's missing
- **Exploration:** "What can hooks do?" → start with the patterns catalog

Ask questions one at a time. Prefer multiple choice when possible.

**Assumption traps** — when tempted to skip asking because:
- The answer seems "obvious" — this is when assumptions are most dangerous
- The pattern looks familiar — this case may differ in ways not yet visible
- The user seems impatient — rushing creates rework
- A coherent interpretation comes quickly — first interpretation isn't always right
- The hook resembles a common pattern — importing assumptions misses what's unique
- User seems confident about their approach — unexamined confidence creates blind spots

If any of these apply, ask anyway.

**Convergence tracking:**

Track whether each question round surfaces new information or just confirms existing understanding.

*A question round yields if it surfaces:*
- New requirement or constraint
- Correction to existing understanding
- New edge case or failure mode
- Priority change to existing concern

*A question round does NOT yield if it only:*
- Confirms existing understanding ("yes, that's right")
- Adds detail without changing conclusions
- Rephrases what's already known

**Convergence rule:** Understanding has converged when two consecutive question rounds yield nothing new. Do not proceed to Phase 2 until converged.

**Dimensions to cover:**

Before claiming convergence, verify these dimensions have been explored:

| Dimension | Explored? |
|-----------|-----------|
| Goal | What should happen? What problem does this solve? |
| Trigger | What event/action should activate this hook? |
| Scope | What should it affect? What should it NOT affect? |
| Behavior | Block? Warn? Log? Transform? Inject context? |
| Constraints | Performance requirements? Must work with existing hooks? |
| Edge cases | What could go wrong? False positives/negatives? |

Not all dimensions apply to every hook — mark inapplicable ones as such and move on.

### Phase 2: Explore the Design Space

**Provoke creative options.** Don't settle for the first obvious solution. For each goal, surface at least 2-3 approaches by considering:

| Dimension | Questions to Ask |
|-----------|------------------|
| Event type | Could this happen at a different point? (PreToolUse vs PostToolUse? SessionStart vs UserPromptSubmit?) |
| Hook type | Would a prompt hook be simpler? Would an agent hook (plugin) be more powerful? |
| Output mechanism | Exit codes sufficient, or could JSON control do more? (updatedInput, permissionDecision, additionalContext) |
| Scope | Block vs warn vs log? Transform input vs reject? |
| Cross-event patterns | Would state from an earlier event help? |

**Surface non-obvious possibilities:**
- "You could block this, OR inject a warning and let Claude decide"
- "PreToolUse blocks it, but PostToolUse could log for later review"
- "A prompt hook lets Haiku make the judgment call instead of pattern matching"

Consult [references/creative-patterns-catalog.md](references/creative-patterns-catalog.md) for non-obvious patterns.

### Phase 3: Present Candidates

**Prerequisite:** You must have at least 2-3 candidate approaches from Phase 2 before presenting sketches. If you only have one obvious approach, return to Phase 2 and apply the dimension questions to surface alternatives.

For each viable approach, provide a **sketch**:

```
**Approach: [name]**
- Event: [which event]
- Hook type: [command/prompt/agent]
- Matcher: [pattern]
- Behavior: [one sentence]
- Trade-off: [what you gain vs give up]
```

Present 2-4 sketches. Each approach should be genuinely viable — don't pad with options that are clearly worse. Recommend one and explain why.

**Phase 3 is complete when:** User selects an approach to implement.

### Phase 4: Expand the Chosen Approach

Once user selects an approach, fully specify:

1. **Event type** — which event and why
2. **Hook type** — command, prompt, or agent
3. **Matcher** — specific pattern (not too broad, not too narrow)
4. **Input handling** — what fields from stdin JSON are used
5. **Logic** — what the hook checks/does
6. **Output mechanism** — exit codes, JSON structure, stdout/stderr behavior
7. **Performance** — expected latency, any concerns
8. **Independence** — can run without assuming other hooks

Document the specification inline or as a design context file at `docs/plans/YYYY-MM-DD-<hook-name>-design.md`.

### Phase 5: Implement

Based on hook type and scope:

**Command hook (script):**
1. Create script at `.claude/hooks/<name>.py` with frontmatter
2. Make executable: `chmod +x`
3. Sync settings: `uv run scripts/sync-settings`

**Prompt hook:**
1. Add directly to settings.json (no script needed)

**Component-scoped hook:**
1. Add to skill/command/agent frontmatter
2. Only PreToolUse, PostToolUse, Stop supported

**Plugin hook:**
1. Create in `hooks/hooks.json` within plugin
2. Create script if command type

Consult [references/hook-implementation-checklist.md](references/hook-implementation-checklist.md) for format details.

**After implementation:** Verify the hook matches the Phase 4 specification — event, matcher, logic, and output mechanism should all align with the design.

### Phase 6: Verify Checkpoint

Before declaring done, verify all dimensions:

- [ ] **Event fit** — Is this the right event for the goal?
- [ ] **Hook type fit** — Command vs prompt vs agent appropriate?
- [ ] **Matcher scope** — Specific enough? Not too broad?
- [ ] **Output mechanism** — Exit codes sufficient? JSON control needed?
- [ ] **Format** — stdout/stderr/JSON structure correct for this event?
- [ ] **Performance** — Will this add acceptable latency?
- [ ] **Independence** — Can run without assuming other hooks ran?
- [ ] **Exit codes** — Using exit 2 to block (not exit 1)?
- [ ] **User confirmation** — Does the user confirm the hook addresses their original intent?

## Decision Points

**User unsure what they want:**
- If goal is vague → Start with "What's repetitive or error-prone in your workflow?"
- If user says "I don't know" → Offer the patterns catalog as a menu: "Here are things hooks can do — anything resonate?"

**Multiple events could work:**
- If PreToolUse vs PostToolUse → PreToolUse can block, PostToolUse can only react. Which fits?
- If SessionStart vs UserPromptSubmit → SessionStart runs once; UserPromptSubmit runs every prompt. Which timing?
- If genuinely equivalent → Prefer the simpler event (fewer fields to handle, less coupling)

**Command vs prompt hook:**
- If logic is deterministic (pattern matching, file checks) → Command hook
- If logic requires judgment ("is this safe?", "is this complete?") → Prompt hook
- If need tool access for verification → Agent hook (plugins only)

**Matcher scope unclear:**
- If too broad (`*` on PreToolUse) → Every tool call slows down. Narrow it.
- If too narrow (exact tool only) → Might miss related tools. Consider regex: `Edit|Write`

**Exit codes vs JSON output:**
- If just allow/block → Exit codes sufficient (0 = allow, 2 = block)
- If need to modify input → JSON with `updatedInput`
- If need to inject context → JSON with `additionalContext`
- If need auto-approve without prompt → JSON with `permissionDecision: "allow"`

**User wants to skip exploration:**
- If user says "just give me the hook" → Present ONE sketch of the obvious approach, then ask: "Before I implement this, are you open to a quick alternative?" If no, proceed with their choice.

**Hook seems too complex:**
- If logic exceeds ~50 lines → Consider: is this really a hook, or should it be a skill?
- If needs conversation → Hooks can't converse. Redirect to skill.
- If needs multiple steps with user input → Not a hook.

**Performance concerns:**
- If hook does network calls → Add timeout, consider async
- If hook runs on every tool call → Must be <1 second
- If slow is acceptable → Use PostToolUse (doesn't block the operation)

## Examples

**Scenario:** User says "I want to be notified when Claude is waiting for input"

### ❌ BAD: Jumping to the obvious solution

```
Claude: "I'll create a Notification hook that sends a desktop notification."

[Immediately writes hook without exploring alternatives]
```

**Why it's bad:**
- Only one approach considered
- Didn't explore event type options (Notification has multiple matchers)
- Didn't consider hook type (command vs prompt)
- No trade-offs surfaced
- User might have wanted something different (sound? Slack message? only after N seconds?)

### ✅ GOOD: Exploring the design space first

```
Claude: "What kind of notification do you want?"
User: "Desktop notification is fine"

Claude: "Should this trigger for all idle moments, or only specific ones?"
User: "Only when Claude needs permission to do something"

Claude: "Here are a few approaches:

**Approach 1: Notification hook with permission_prompt matcher (Recommended)**
- Event: Notification
- Matcher: permission_prompt
- Behavior: Desktop notification via notify-send
- Trade-off: Simple, but only covers permission prompts

**Approach 2: Notification hook with idle_prompt matcher**
- Event: Notification
- Matcher: idle_prompt
- Behavior: Desktop notification after 60s idle
- Trade-off: Catches all idle states, but may be noisy

**Approach 3: PermissionRequest hook**
- Event: PermissionRequest
- Matcher: *
- Behavior: Notification + can auto-approve patterns
- Trade-off: More powerful, but more complex

I recommend Approach 1 since you specifically want permission prompts. Want me to implement it?"

User: "Yes, approach 1"

[Now implements with full specification]
```

**Why it's good:**
- Clarified what "waiting for input" actually meant
- Surfaced multiple event types that could work
- Presented trade-offs for each approach
- Made a recommendation with reasoning
- Got user confirmation before implementing

## Anti-Patterns

**Pattern:** Jumping to PreToolUse + Bash + block
**Why it fails:** This is the most common hook pattern, so Claude defaults to it. But many goals are better served by other events (PostToolUse for logging, SessionStart for context, Notification for alerts) or other behaviors (warn instead of block, transform instead of reject).
**Fix:** Always explore at least one alternative event type before settling on the obvious choice.

**Pattern:** Using exit code 1 to block
**Why it fails:** Only exit code 2 blocks operations. Exit 1 is a non-blocking error — the operation proceeds and stderr is only shown in verbose mode.
**Fix:** Exit 2 for blocking, exit 0 for allow, other codes for non-blocking errors.

**Pattern:** Broad matcher on slow hooks
**Why it fails:** A `*` matcher on PreToolUse means EVERY tool call waits for your hook. If it's slow, everything slows down.
**Fix:** Narrow the matcher to specific tools. If you need broad coverage, make the hook fast (<100ms) or use PostToolUse (doesn't block).

**Pattern:** Complex logic in hooks that should be skills
**Why it fails:** Hooks are synchronous, can't converse, and have timeout limits. Trying to do complex analysis or multi-step reasoning in a hook creates brittle, hard-to-debug code.
**Fix:** If logic exceeds ~50 lines or needs judgment, use a skill instead. Hooks are for deterministic, fast checks.

**Pattern:** Ignoring JSON output capabilities
**Why it fails:** Many users only know exit codes. But JSON output enables input transformation (`updatedInput`), auto-approval (`permissionDecision`), context injection (`additionalContext`), and more.
**Fix:** Ask: "Do you need to modify the input? Inject context? Auto-approve?" If yes, use JSON output.

**Pattern:** Not checking `stop_hook_active` in Stop hooks
**Why it fails:** If a Stop hook blocks and Claude continues, and the hook blocks again, you get an infinite loop.
**Fix:** Check `stop_hook_active` in input. If true, don't block again.

## Troubleshooting

**Symptom:** Hook doesn't fire at all
**Cause:** Settings not synced, wrong event name, script not executable, or matcher doesn't match
**Next steps:**
1. Run `/hooks` to verify hook is registered
2. Check matcher matches tool name exactly (case-sensitive: `Bash` not `bash`)
3. Verify script is executable: `chmod +x`
4. Run `uv run scripts/sync-settings` to regenerate settings.json

**Symptom:** Hook fires but doesn't block
**Cause:** Using wrong exit code (exit 1 instead of exit 2)
**Next steps:** Exit code 2 blocks. Exit 1 is a non-blocking error. Check your exit codes.

**Symptom:** Hook blocks but Claude doesn't see the message
**Cause:** Message sent to stdout instead of stderr on exit 2
**Next steps:** On exit 2, only stderr is shown to Claude. Move your error message to stderr: `print("message", file=sys.stderr)`

**Symptom:** JSON output not being processed
**Cause:** Exit code is not 0, or JSON is malformed
**Next steps:** JSON output only processed on exit 0. Check exit code. Validate JSON structure.

**Symptom:** Hook is slow, everything lags
**Cause:** Broad matcher, slow logic, or network calls without timeout
**Next steps:** Narrow matcher, optimize logic, add timeouts to network calls. Target <1s for PreToolUse.

**Symptom:** Claude ignores the design space exploration
**Cause:** User pushed to skip, or Claude rationalized past it
**Next steps:** Slow down. "Before I implement, let me surface one alternative you might not have considered." Present at least one non-obvious option.

**Symptom:** Implemented hook doesn't match the design
**Cause:** Drifted during implementation, or design was underspecified
**Next steps:** Return to the checkpoint. Verify each dimension (event, hook type, matcher, output, format) matches the design.

## References

**Required reading during exploration:**
- [references/hook-design-space.md](references/hook-design-space.md) — Event types, hook types, matchers, output mechanisms, exit codes
- [references/creative-patterns-catalog.md](references/creative-patterns-catalog.md) — Non-obvious hook uses organized by goal (enforce, capture, inject, integrate)

**Quick reference during implementation:**
- [references/hook-implementation-checklist.md](references/hook-implementation-checklist.md) — Frontmatter format, exit code semantics, JSON output schemas, common mistakes
