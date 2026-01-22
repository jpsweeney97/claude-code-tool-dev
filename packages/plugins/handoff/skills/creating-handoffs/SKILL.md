---
name: creating-handoffs
description: Used when user says "wrap this up", "new session", or "handoff"; when stopping work with context to preserve.
---

**Session ID:** ${CLAUDE_SESSION_ID}

# Creating Handoffs

Capture session context at stopping points.

**Core Promise:** One action to save (`/handoff`).

## When to Use

- User explicitly runs `/handoff` or `/handoff <title>`
- User says signal phrases: "wrap this up", "new session", "handoff"
- Session contains at least one of: decision made, file changed, gotcha discovered, next step identified
- User is stopping work and wants to resume later with context

## When NOT to Use

- Session was trivial (quick Q&A with no decisions, changes, or learnings)
- User explicitly declines handoff offer
- Context is already captured elsewhere (PR description, committed docs, issue tracker)
- Session is exploratory research with no actionable next steps
- **Resuming from a handoff** — use the `resuming-handoffs` skill instead

**Non-goals (this skill does NOT):**
- Resume from handoffs (that's the `resuming-handoffs` skill)
- Replace proper documentation (handoffs are ephemeral, docs are permanent)
- Capture every detail (focus on decisions and next steps, not transcript)
- Work across different machines (handoffs are local to `~/.claude/`)

**STOP:** If unclear whether session has meaningful content, ask: "Should I create a handoff? This session seems light on decisions/changes."

## Inputs

**Required:**
- Session context (gathered from conversation history)

**Optional:**
- `title` argument for `/handoff <title>` — if omitted, Claude generates a descriptive title

**Constraints/Assumptions:**

| Assumption | Required? | Fallback |
|------------|-----------|----------|
| Git repository | No | Omit `branch` and `commit` fields from frontmatter |
| Write access to `~/.claude/handoffs/` | Yes | **STOP** and ask for alternative path |
| Project name determinable | No | Use parent directory name; if ambiguous, ask user |

**STOP:** If `~/.claude/handoffs/` doesn't exist and cannot be created, ask: "I can't write to ~/.claude/handoffs/. Where should I save handoffs?"

## Outputs

**Artifacts:**
- Markdown file at `~/.claude/handoffs/<project>/YYYY-MM-DD_HH-MM_<slug>.md`
- Frontmatter with session metadata (date, time, created_at, project, title, files)
- Body with relevant sections from checklist (only non-empty sections included)

**Definition of Done:**

| Check | Expected |
|-------|----------|
| File exists at expected path | `ls ~/.claude/handoffs/<project>/YYYY-MM-DD_HH-MM_*.md` returns file |
| Frontmatter parses as valid YAML | No YAML syntax errors |
| Required fields present | `date`, `time`, `created_at`, `project`, `title` all have values |
| At least one body section | File contains at least one H2 section with content |
| Content is resumable | Reading the handoff provides enough context to continue work |

**Quick check:** After writing, verify file exists and contains the title. If missing, check write permissions and path.

## Commands

| Command | Action |
|---------|--------|
| `/handoff` | Create handoff (Claude generates title) |
| `/handoff <title>` | Create handoff with specified title |

## Decision Points

1. **Signal phrase detected:**
   - If user says "wrap this up", "new session", or "handoff", then offer: "Create a handoff before ending?"
   - If user declines, **STOP**. Do not re-prompt or proceed.

2. **Session content assessment:**
   - If session contains at least one of: decision made, file changed, gotcha discovered, next step identified, then proceed with handoff.
   - Otherwise, ask: "This session seems light — create a handoff anyway, or skip?"

3. **Git repository detection:**
   - If `.git/` directory exists in current or parent directories, then include `branch` and `commit` in frontmatter.
   - Otherwise, omit `branch` and `commit` fields entirely (don't use placeholders).

4. **Timestamp generation:**
   - Generate `created_at` as ISO 8601 UTC timestamp (e.g., `2026-01-12T14:30:00Z`)
   - Use the current time when the handoff is created

5. **Write permission check:**
   - If `~/.claude/handoffs/<project>/` is writable (or can be created), write handoff there.
   - Otherwise, **STOP** and ask: "Can't write to ~/.claude/handoffs/. Where should I save this handoff?"

## Procedure

When user runs `/handoff [title]` or confirms a signal phrase offer:

1. **Check prerequisites:**
   - If session appears trivial (no decisions, changes, or learnings), ask: "This session seems light — create a handoff anyway?"
   - If user declines, **STOP**. Do not proceed.

2. **Note the session ID** from the "Session ID:" line at the top of this skill (substituted by Claude Code at load time)

3. **Complete the synthesis process:**
   - YOU MUST read [synthesis-guide.md](synthesis-guide.md) completely before proceeding
   - Answer every applicable synthesis prompt in the guide
   - This is not optional — do not skip to filling sections
   - The synthesis prompts are THINKING; the handoff sections are OUTPUT

4. **Gather context** from the session (informed by your synthesis work)

5. **Select relevant sections** using the checklist in [format-reference.md](../../references/format-reference.md)
   - If no sections have content, **STOP** and ask: "I don't see anything to hand off. What should I capture?"
   - Omit empty sections from output
   - **Calibration:** Distinguish verified facts (explicitly discussed) from inferred conclusions (reasonable next steps) from assumed context (background not verified this session)

6. **Determine output path:**
   - If `~/.claude/handoffs/<project>/` is not writable, **STOP** and ask for alternative path
   - If project name is ambiguous (not in git, generic directory name), ask user to specify

7. **Generate markdown** with frontmatter per [format-reference.md](../../references/format-reference.md):
   - Include `session_id:` with the UUID from step 2
   - Check for `~/.claude/.session-state/handoff-<session_id>` (using the UUID from step 2)
   - If state file exists, read path and include as `resumed_from`
   - Use fallbacks for optional fields (see Inputs → Constraints/Assumptions)

8. **Write file** to `~/.claude/handoffs/<project>/YYYY-MM-DD_HH-MM_<slug>.md`

9. **Clean up state file** (delete `~/.claude/.session-state/handoff-<session_id>` if exists)

10. **Verify and confirm:**
    - Check file exists and frontmatter is valid
    - Confirm: "Handoff saved: <title> (N decisions, N changes, N next steps)"

## Verification

After creating handoff, verify:

- [ ] File exists at `~/.claude/handoffs/<project>/YYYY-MM-DD_HH-MM_<slug>.md`
- [ ] Frontmatter parses as valid YAML
- [ ] Required fields present: date, time, created_at, project, title
- [ ] At least one section has content

**Quick check:** Run `ls ~/.claude/handoffs/<project>/` and confirm new file appears. If not, check write permissions.

**If verification fails:** Do not report success. Check Troubleshooting section and resolve before confirming.

## Troubleshooting

### Handoff file not created

**Symptoms:** `/handoff` completes but no file appears at `~/.claude/handoffs/<project>/`

**Likely causes:**
- Permission denied on `~/.claude/` directory
- Project name couldn't be determined (not in git, ambiguous directory)
- Disk full or path too long

**Next steps:**
1. Check if `~/.claude/handoffs/` exists: `ls -la ~/.claude/handoffs/`
2. Check write permissions: `touch ~/.claude/handoffs/test && rm ~/.claude/handoffs/test`
3. If permissions issue, ask user for alternative path
4. If project undetermined, ask user to specify project name

### Handoff content missing key decisions

**Symptoms:** Resumed handoff lacks important context from original session

**Likely causes:**
- Handoff created too early (before key decisions made)
- Section checklist didn't capture all relevant categories
- Session had implicit decisions not stated explicitly

**Next steps:**
1. Review session history for decisions made after handoff
2. Create new handoff with more complete context
3. Consider adding to existing handoff manually if file still accessible

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| Handoff for trivial sessions | Noise accumulation | Skip if no meaningful decisions/progress |
| Including every file touched | Information overload | Focus on key artifacts with purpose |
| Missing decisions/rationale | Just listing changes isn't useful | Always capture at least one "why" |
| Re-prompting after user declines | Annoying, ignores user intent | Respect "no" and move on |
| Guessing when uncertain | May create useless handoff | Ask user if handoff is needed |

## Related Skills

| Skill | Relationship |
|-------|--------------|
| `resuming-handoffs` | Complementary: creating-handoffs creates, resuming-handoffs loads |
