---
name: implementing-commands
description: Use when building a command from a design document. TDD-focused
  workflow with iron law "test invocation exhaustively before orchestration."
  Follows brainstorming-commands output.
---

# Implementing Commands

Build commands using test-driven development: verify invocation works first, then add delegation.

## Quick Start

```
User: "Implement this command design"
Claude: Uses TDD workflow

0. Design verification (8 anti-pattern checks)
1. Create stub (frontmatter only)
2. Test invocation (all argument variations)
3. Add delegation (skill, agent, or script)
4. Test end-to-end (full workflow)
5. Validate (verification checklist)

→ Command ready for use
```

## Triggers

- `implement this command`
- `build the command from this design`
- `test my command`
- `TDD for commands`
- After `brainstorming-commands` produces design

## Prerequisites Check

Before proceeding, verify:

1. **Design document exists?**
   - If yes: "I see the design at `[path]`. Proceeding with implementation."
   - If no: "No design found. Should we start with `/brainstorming-commands`?"

2. **Design has required sections?**
   - Purpose statement
   - Arguments & context gathering
   - Pre-flight validation
   - Delegation target
   - Frontmatter block

If missing: "The design is missing [sections]. Complete it first?"

## Pipeline Context

This skill is **Stage 3: Implement** in the commands pipeline.

| Aspect | Value |
|--------|-------|
| This stage | Build command from design using TDD |
| Previous | `/brainstorming-commands` (design document) |
| Next | `/optimizing-plugins` or personal use |
| Reference | `command-development` (structural details) |

## The Iron Law

```
TEST INVOCATION EXHAUSTIVELY BEFORE ORCHESTRATION
```

The command must trigger correctly before you test what it does. Mixing invocation bugs with delegation bugs creates confusion.

**No exceptions:** Not for "simple commands" or "obvious implementations."

## Step 0: Design Verification

Before writing any code, confirm the design from brainstorming-commands passes all anti-pattern checks:

| Anti-pattern check | What to verify |
|--------------------|----------------|
| Has clear description and argument-hint | `description` < 60 chars, `argument-hint` shows expected input |
| `disable-model-invocation: true` if destructive | Commits, deploys, deletes require explicit invocation |
| Delegates work (not monolithic) | Prompt < 100 lines; work in skill/agent/script |
| No `${CLAUDE_PLUGIN_ROOT}` in user/project scope | Only plugin commands have this variable |
| Is a command (not a skill in disguise) | Users invoke via `/command`, not natural language |
| Focused scope (one thing, not A/B/C/D) | Single responsibility |
| Has post-processing feedback | Users know what happened |
| Verb-noun, specific, action-first naming | `create-skill`, not `skill-creator` |

**If any check fails:** Return to brainstorming-commands to fix the design before implementing.

## The TDD Workflow

### Step 1: Create Stub

Create minimal command with frontmatter and debug output only.

**Stub template:**

```markdown
---
description: [from design Step 6]
argument-hint: [from design Step 2]
---
DEBUG: Testing invocation
- ARGUMENTS: $ARGUMENTS
- ARG1: $1
- ARG2: $2

[Validation and delegation will go here after invocation tests pass]
```

**File location:**
- Plugin command: `plugin-name/commands/command-name.md`
- User command: `~/.claude/commands/command-name.md`
- Project command: `.claude/commands/command-name.md`

### Step 2: Test Invocation

**The invocation test matrix:**

| Test | Input | Expected behavior | How to test |
|------|-------|-------------------|-------------|
| No arguments | `/command` | Graceful handling (help, default, or clear error) | Run command with no args |
| Valid arguments | `/command valid-path` | `$1`/`$ARGUMENTS` available in prompt | Add DEBUG output |
| Invalid arguments | `/command /nonexistent/path` | Validation catches before delegation | Pre-flight check fails with clear message |
| Edge cases | `/command "path with spaces"` | Quotes preserved, no word splitting | Test paths with spaces, special chars |

**Testing workflow:**

1. Run `claude --plugin-dir ./plugins/your-plugin` (for plugin commands)
2. Invoke command: `/command-name test-arg`
3. Verify DEBUG output shows arguments correctly
4. Try each row in the test matrix

**Critical:** Do NOT proceed to Step 3 until all invocation tests pass.

### Step 3: Add Delegation

After invocation passes, add the actual work:

1. Remove DEBUG lines
2. Add pre-flight validation (from design Step 3)
3. Add delegation (from design Step 4)
4. Add post-processing (from design Step 5)

**Example progression:**

```markdown
---
description: Optimize plugin through 6 analytical lenses
argument-hint: "<plugin-path>"
---
# Before (stub)
DEBUG: args=$1

# After (complete)
Validate plugin path:
`test -d $1 && echo "OK" || echo "MISSING: $1"`

Use the optimizing-plugins skill to analyze this plugin:
@$1

After analysis, suggest: "Run /fix-plugin to address identified issues"
```

### Step 4: Test End-to-End

| Test type | What to verify |
|-----------|----------------|
| Happy path | Valid input produces expected output |
| Error path | Invalid input caught and reported clearly |
| Edge path | Unusual but valid input handled correctly |

**For each test:**
1. Run command with test input
2. Verify output matches design expectations
3. Check artifacts produced (files, commits, etc.)
4. Verify hooks fired if expected

### Step 5: Validate

Run verification checklist:

| Check | Evidence |
|-------|----------|
| All invocation tests pass | Matrix completed |
| End-to-end happy path works | Output shown |
| Error messages are actionable | Clear guidance on how to fix |
| Hooks fire correctly (if applicable) | Debug output shows hook execution |
| Portability verified | Works after installation |

## Common Failures

| Symptom | Likely cause | Debug step |
|---------|--------------|------------|
| Command not found | Wrong location or name mismatch | Check `commands/` dir; verify filename matches invocation |
| Arguments empty | Wrong variable (`$ARGUMENTS` vs `$1`) | Add DEBUG output; check if using blob vs positional |
| Validation always fails | Bash syntax error in `!` block | Test validation command in terminal first |
| Delegation doesn't fire | Skill/agent name typo or missing | Verify skill exists; check exact name |
| Works locally, fails installed | `${CLAUDE_PLUGIN_ROOT}` in wrong scope | User/project commands can't use this variable |
| Path with spaces fails | Unquoted variable | Use `"$1"` not `$1` |
| Context not injected | Wrong `@` syntax | Check `@$1` vs `@path` usage |

## Checklist

**Use TodoWrite to track progress.**

**Step 0 - Design Verification:**
- [ ] All 8 anti-pattern checks pass
- [ ] Design document path confirmed

**Step 1 - Stub:**
- [ ] Stub created with frontmatter
- [ ] DEBUG output includes all argument variables
- [ ] File in correct location

**Step 2 - Invocation Tests:**
- [ ] No arguments test
- [ ] Valid arguments test
- [ ] Invalid arguments test
- [ ] Edge cases test (spaces, special chars)

**Step 3 - Delegation:**
- [ ] DEBUG lines removed
- [ ] Pre-flight validation added
- [ ] Delegation implemented
- [ ] Post-processing added

**Step 4 - End-to-End:**
- [ ] Happy path works
- [ ] Error path caught
- [ ] Edge path handled

**Step 5 - Validation:**
- [ ] All tests pass
- [ ] Portable (works after installation)
- [ ] Committed to git

## Output

Working command in correct location:
- **Plugin command:** `plugin-name/commands/command-name.md`
- **User command:** `~/.claude/commands/command-name.md`
- **Project command:** `.claude/commands/command-name.md`

## Next Step

| Situation | Command |
|-----------|---------|
| More components to build | `/brainstorming-{component}` |
| Plugin complete, want polish | `/optimizing-plugins` |
| Personal use only | Done — command is active |

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| Writing command before design | Can't verify it solves real need | brainstorming-commands first |
| Testing delegation before invocation | Bugs compound and confuse | Iron law: invocation first |
| Skipping Step 0 verification | Design issues become implementation bugs | Always verify 8 checks |
| Hardcoded paths in portable command | Breaks after installation | Use `$ARGUMENTS`, `@$1`, relative paths |
| Complex logic inline | Hard to debug and maintain | Delegate to skill or agent |
| No post-processing feedback | Users confused about outcome | Always report what happened |

## References

- command-development — Structural reference (frontmatter, arguments, patterns)
- brainstorming-commands — Design phase (if design needed)
- Official commands docs — `docs/claude-code-documentation/commands-*.md`
