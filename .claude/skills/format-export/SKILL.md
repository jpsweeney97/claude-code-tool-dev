---
name: format-export
description: Transforms Claude Code /export output into structured markdown. Use after running /export to create readable documentation. Produces two files - a clean conversation narrative and a separate tool calls reference. Use when you need to share, archive, or review a conversation in markdown format.
argument-hint: <path-to-export-file>
---

# Format Export

Converts `/export` output from terminal-formatted plain text into structured markdown optimized for readability and sharing.

## Output Files

Given input `conversation.txt`, produces:

| File | Contents |
|------|----------|
| `conversation.md` | Clean narrative with ToC, turn sections, inline tool references |
| `conversation-tools.md` | Sequential tool call details, numbered for cross-reference |

## Workflow

1. Read the export file at the provided path
2. Parse terminal formatting (banners, prefixes, ASCII art)
3. Transform to markdown following formatting rules
4. Extract tool calls to companion file
5. Write both files alongside the original

## Parsing Rules

### Input Syntax

| Pattern | Meaning |
|---------|---------|
| `▐▛███▜▌ Claude Code...` | Header banner — extract version, model, directory |
| `❯ ...` | User turn |
| `⏺ ...` | Assistant turn |
| `⎿ ...` | Tool call or result |
| `✻ Churned for Ns` | Timing info — discard |
| `★ Insight ───...───` | Insight block |
| `@path/to/file` | File reference |

### Turn Boundaries

A new turn starts when:

- Line begins with `❯` (user)
- Line begins with `⏺` (assistant)

Content between turn markers belongs to the preceding turn.

## Output Structure

### Main File (`<name>.md`)

```markdown
---
title: <extracted from first user prompt or filename>
date: <from filename if present, else file creation date>
model: <from banner>
---

# <title>

## Table of Contents

- [Turn 1: User](#turn-1-user)
- [Turn 2: Assistant](#turn-2-assistant)
...

## Turn 1: User

<user content>

## Turn 2: Assistant

<assistant content with inline tool references>

**Insight:** <content>
```

### Tools File (`<name>-tools.md`)

```markdown
# Tool Calls: <title>

## Tool #1: Read

**File:** `path/to/file.md`
**Lines:** 245

---

## Tool #2: Task

**Description:** Explored authentication code
**Result:** Found 3 relevant files...
**Stats:** 12 tool uses · 45.2k tokens · 38s
```

## Element Transformations

| Input | Output |
|-------|--------|
| ASCII table | Markdown table (preserve alignment) |
| `★ Insight ───` block | `**Insight:** content` |
| `⎿ Read path (N lines)` | `[Tool #N: Read path]` inline |
| `⎿ Task(desc)` ... `Done (stats)` | `[Tool #N: Task — desc]` inline |
| `⎿ Wrote to path` | `[Tool #N: Write path]` inline |
| `⎿ command` + output | `[Tool #N: Bash command]` inline |
| `@path/to/file` | `path/to/file` (remove @) |
| Indented code blocks | Fenced code blocks with language hint if detectable |

## Formatting Rules

### Text Styling

| Element | Use for | Avoid |
|---------|---------|-------|
| **Bold** | Key terms (first use), critical warnings | General emphasis |
| _Italics_ | Introducing terms, names | General emphasis |
| `inline code` | Commands, filenames, literals | Non-code jargon |
| Code blocks | Multi-line code/config/examples | Single commands |
| > Blockquotes | External quotes, callouts | Self-emphasis |

### Whitespace Normalization

| Context | Rule |
|---------|------|
| Before headings | One blank line (two if preceded by content) |
| After headings | One blank line |
| Between paragraphs | One blank line |
| Before lists/tables | One blank line |
| After lists/tables | One blank line |
| Inside code blocks | Preserve exactly |
| Trailing whitespace | Remove from all lines |
| End of file | Single newline |

### Heading Discipline

| Level | Usage | Rule |
|-------|-------|------|
| H1 | Document title | Exactly one per file |
| H2 | Major sections (turns, ToC) | TOC-level divisions |
| H3 | Subsections within turns | Within H2 |
| H4 | Rare | Prefer splitting into H3s |
| H5+ | **Never** | Demote to H4 or restructure |

### Table Conversion

When converting ASCII tables:

1. Detect column boundaries from `│` or consistent spacing
2. Detect header row from `─` separator line
3. Preserve column alignment (left/center/right)
4. Use standard markdown table syntax with `:---`, `:---:`, `---:`

## Edge Cases

### Nested Tool Results

When tool results contain their own structure, extract the summary to the tools file. The inline reference shows only the description:

- Main: `[Tool #N: Task — desc]`
- Tools file: Full result including nested content

### Malformed Tables

If ASCII table detection fails:

1. Preserve as fenced code block with no language
2. Add comment: `<!-- Table conversion failed, preserved as-is -->`

### Missing Banner

If export lacks the ASCII banner:

- Set `model: unknown` in frontmatter
- Use filename as title
- Use file modification date as date

### Empty Turns

If a turn marker has no content before the next marker:

- Omit the empty turn from output
- Do not create a ToC entry for it

### Truncated Exports

If file ends mid-turn:

- Include partial content in final turn
- Add note: `<!-- Export appears truncated -->`

## Troubleshooting

### "File not found"

Verify the path argument points to an existing export file. Use absolute path if relative path fails.

### Output overwrites existing file

The skill checks for existing `<name>.md` before writing. If found:

1. Prompt user for confirmation
2. Or append timestamp: `<name>-2026-02-04-1430.md`

### Large exports

For large conversations (>500 lines output), split into multiple files:

| File | Contents |
|------|----------|
| `<name>.md` | Frontmatter, ToC, and index linking to parts |
| `<name>-part1.md` | Turns 1-N (aim for ~400 lines per part) |
| `<name>-part2.md` | Turns N+1-M |
| `<name>-tools.md` | All tool calls (unchanged) |

**Never summarize.** Always include full content. Split into multiple files if needed.

**Processing strategy for large files:**

1. Count turns using `grep -n "^❯"` to identify user turn boundaries
2. Divide turns into roughly equal groups (4-6 turns per part)
3. Launch parallel Task agents to process each section simultaneously
4. Each agent reads its line range and outputs transformed markdown
5. Write the index file with ToC while agents process
6. Collect agent outputs and write part files
