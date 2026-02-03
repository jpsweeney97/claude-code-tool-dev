---
name: claude-md-improver
description: Audit and improve CLAUDE.md files in repositories. Use when user asks to check, audit, update, improve, or fix CLAUDE.md files. Scans for all CLAUDE.md files, evaluates quality against templates, outputs quality report, then makes targeted updates. Also use when the user mentions "CLAUDE.md maintenance" or "project memory optimization".
allowed-tools: Read, Glob, Grep, Bash, Edit
---

# CLAUDE.md Improver

Audit, evaluate, and improve CLAUDE.md files across a codebase to ensure Claude Code has optimal project context.

**This skill can write to CLAUDE.md files.** After presenting a quality report and getting user approval, it updates CLAUDE.md files with targeted improvements.

## Workflow

### Phase 1: Discovery

Find all CLAUDE.md files in the repository using the Glob tool:

```
Pattern: **/{CLAUDE.md,.claude.md,.claude.local.md}
```

**File Types & Locations:**

| Type             | Location                 | Purpose                                                      |
| ---------------- | ------------------------ | ------------------------------------------------------------ |
| Project root     | `./CLAUDE.md`            | Primary project context (checked into git, shared with team) |
| Local overrides  | `./.claude.local.md`     | Personal/local settings (gitignored, not shared)             |
| Global defaults  | `~/.claude/CLAUDE.md`    | User-wide defaults across all projects                       |
| Package-specific | `./packages/*/CLAUDE.md` | Module-level context in monorepos                            |
| Subdirectory     | Any nested location      | Feature/domain-specific context                              |

**Note:** Claude auto-discovers CLAUDE.md files in parent directories, making monorepo setups work automatically.

**If no CLAUDE.md files are found:** Inform the user and recommend creating a `CLAUDE.md` at the project root. Point them to the templates in [references/templates.md](references/templates.md). Do not create the file automatically — this skill is for auditing and improving existing files.

### Phase 2: Quality Assessment

For each CLAUDE.md file, evaluate against:
- **Content criteria**: [references/quality-criteria.md](references/quality-criteria.md)
- **Language principles**: [references/language-principles.md](references/language-principles.md)

**Quick Assessment Checklist:**

| Criterion                     | Weight | Check                                         |
| ----------------------------- | ------ | --------------------------------------------- |
| Commands/workflows documented | High   | Are build/test/deploy commands present?       |
| Architecture clarity          | High   | Can Claude understand the codebase structure? |
| User Preferences              | High   | Are user's preferences clear?                 |
| Non-obvious patterns          | Medium | Are gotchas and quirks documented?            |
| Conciseness                   | Medium | No verbose explanations or obvious info?      |
| Currency                      | Medium | Does it reflect current codebase state?       |
| Actionability                 | Medium | Are instructions executable, not vague?       |

**Quality Scores:**

Calculate as percentage: (total points / 120) × 100

- **A (90-100%)**: Comprehensive, current, actionable
- **B (70-89%)**: Good coverage, minor gaps
- **C (50-69%)**: Basic info, missing key sections
- **D (30-49%)**: Sparse or outdated
- **F (0-29%)**: Missing or severely outdated

### Phase 3: Quality Report Output

**ALWAYS output the quality report BEFORE making any updates.**

Format:

```
## CLAUDE.md Quality Report

### Summary
- Files found: X
- Average score: X/100
- Files needing update: X

### File-by-File Assessment

#### 1. ./CLAUDE.md (Project Root)
**Content: XX/100 (Grade: X) | Language: X**

| Criterion | Score | Notes |
|-----------|-------|-------|
| Commands/workflows | X/20 | ... |
| Architecture clarity | X/20 | ... |
| User Preferences | X/20 | ... |
| Non-obvious patterns | X/15 | ... |
| Conciseness | X/15 | ... |
| Currency | X/15 | ... |
| Actionability | X/15 | ... |

**Content Issues:**
- [List specific content problems]

**Language Issues:**
- [List principle violations with location, e.g., "Economy: filler in line 12"]

**Recommended additions:**
- [List what should be added]

#### 2. ./packages/api/CLAUDE.md (Package-specific)
...
```

After presenting the report, ask: **"Would you like to discuss preferences, or proceed directly to updates?"**

- If user wants to discuss → proceed to Phase 4
- If user wants to proceed → skip to Phase 5

### Phase 4: Dialogue

**Understanding the user's personal preferences:**

- Discover the user's preferences through collaborative dialogue.
- Ask questions one at a time to understand the user's preferences.
- Only one question per message - if a topic needs more exploration, break it into multiple questions

**Exploring approaches:**

- Propose 2-3 different ideas for preferences
- Present options conversationally with your recommendation and reasoning
- Lead with your recommended option and explain why
- Transform preferences into clear, concise, and concrete instructions for Claude.

**When assessing preferences, evaluate content through Claude's perspective:**

- Do these preferences contradict anything in Claude's system prompt?
- What failure modes or edge cases need to be considered?
- Do any of these preferences describe something Claude already does?
- Which preferences add genuine value, and which impose limiting rigidity?
- Are any of these preferences explaining something Claude already knows from training?

**Presenting the draft:**

- Once you believe you understand the user's preferences, present the drafted section
- Be ready to go back and adjust if the user wants to change anything

**Useful Prompts for Preference Discovery:**

| Situation | Prompt |
|-----------|--------|
| Vague preference | "Can you give me an example of when this matters?" |
| Unclear scope | "Should this apply everywhere, or specific situations?" |
| Potential conflict | "How should Claude handle it when [X] and [Y] conflict?" |
| Checking understanding | "So if I understand correctly: [restatement]. Is that right?" |
| Testing actionability | "If Claude saw this instruction, what would it do differently?" |

**Example Dialogue:**

> **User:** "I want Claude to be more careful with changes."
>
> **Claude:** "Can you give me an example of when Claude wasn't careful enough?"
>
> **User:** "It often makes changes without checking how they affect other parts of the codebase. Like renaming a function without finding all the call sites."
>
> **Claude:** "So you'd prefer Claude analyze cross-cutting impacts before making changes?"
>
> **User:** "Yes, especially for anything that could break other files."
>
> **Claude:** "Got it. Should this apply to all changes, or only certain types like renames and interface changes?"
>
> **User:** "Renames, deleting code, and changing function signatures. Small internal edits are fine."
>
> *Drafted instruction: "Before renaming, deleting, or changing function signatures: search for all usages and verify changes won't break callers."*

Notice how "be more careful" became a specific, actionable instruction through dialogue.

### Phase 5: Targeted Updates

After outputting the quality report (and dialoguing about preferences if requested), ask user for confirmation before updating.

**Update Guidelines (Critical):**

1. **Propose targeted additions only** - Focus on genuinely useful info:
   - Commands or workflows discovered during analysis
   - Gotchas or non-obvious patterns found in code
   - Unique user preferences
   - Package relationships that weren't clear
   - Testing approaches that work
   - Configuration quirks

2. **Keep it minimal** - Avoid:
   - Restating what's obvious from the code
   - Generic best practices already covered
   - One-off fixes unlikely to recur
   - Verbose explanations when a one-liner suffices

3. **Apply language principles** - When drafting updates, follow [references/language-principles.md](references/language-principles.md). Show before/after when improving existing text.

4. **Show diffs** - For each change, show:
   - Which CLAUDE.md file to update
   - The specific addition (as a diff or quoted block)
   - Brief explanation of why this helps future sessions

**Diff Format:**

`````markdown
### Update: ./CLAUDE.md

**Why:** Build command was missing, causing confusion about how to run the project.

````diff
+ ## Quick Start
+
+ ```bash
+ npm install
+ npm run dev  # Start development server on port 3000
+ ```
````
`````

### Phase 6: Apply Updates

After user approval, apply changes using the Edit tool. Preserve existing content structure.

**Before finishing, verify:**

- [ ] Re-read updated sections — are instructions actionable, not vague?
- [ ] Do referenced file paths actually exist?
- [ ] Would a fresh Claude session understand and follow these instructions?
- [ ] Is each addition project-specific, not generic advice?

## Templates

See [references/templates.md](references/templates.md) for CLAUDE.md templates by project type.

## Common Issues

See the "Red Flags" section in [references/quality-criteria.md](references/quality-criteria.md) for issues to watch for during assessment.

## User Tips to Share

When presenting recommendations, remind users:

- **`#` key shortcut**: During a Claude session, press `#` to have Claude auto-incorporate learnings into CLAUDE.md
- **Keep it concise**: CLAUDE.md should be human-readable; dense is better than verbose
- **Actionable commands**: All documented commands should be copy-paste ready
- **Use `.claude.local.md`**: For personal preferences not shared with team (add to `.gitignore`)
- **Global defaults**: Put user-wide preferences in `~/.claude/CLAUDE.md`

## Rationalization Table

| Rationalization | Reality |
|-----------------|---------|
| "The user clearly wants updates, I'll skip the report" | Report-first ensures informed consent. Always show it. |
| "I know what good CLAUDE.md looks like, no need for dialogue" | User preferences are personal. Dialogue discovers them. |
| "I should explain this thoroughly" | Conciseness is a core principle. Dense beats verbose. |
| "Best practices are always helpful to add" | Project-specific only. Generic advice wastes context. |
| "This preference sounds reasonable, I should include it" | Does Claude already do this? If so, it's noise. Only include preferences that change Claude's default behavior. |
| "I've captured what the user said" | Statements aren't instructions. Transform preferences into concrete, actionable guidance. |
| "I removed the redundant content" | Removal without replacement leaves gaps. Verify both parts of any consolidate/replace action. |

## What Makes a Great CLAUDE.md

**Key principles:**

- Concise and human-readable
- Actionable commands that can be copy-pasted
- Project-specific patterns, not generic advice
- Non-obvious gotchas and warnings

**Recommended sections** (use only what's relevant):

- Commands (build, test, dev, lint)
- Architecture (directory structure)
- Rules (user preferences, personalization, styles)
- Key Files (entry points, config)
- Code Style (project conventions)
- Environment (required vars, setup)
- Testing (commands, patterns)
- Gotchas (quirks, common mistakes)
- Workflow (when to do what)
