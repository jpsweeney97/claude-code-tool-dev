---
name: markdown-formatter
description: Reformat markdown files for structural consistency (heading hierarchy, whitespace, tables) with guaranteed lossless content preservation. Targets GFM.
license: MIT
metadata:
  version: 1.0.0
  model: claude-opus-4-5-20251101
  timelessness_score: 8
---

# Markdown Formatter

Normalize markdown structure without changing content. Every word in, every word out.

---

## Triggers

- `format this markdown file`
- `normalize the heading structure in {{file}}`
- `clean up markdown formatting`
- `fix heading hierarchy`
- `reformat {{file}} for consistency`

---

## When NOT to Use

- **Non-markdown files** — `.txt`, `.rst`, `.adoc`, or other formats (will fail validation)
- **Intentionally non-standard structure** — ASCII art, creative layouts, or files where heading levels carry domain-specific meaning
- **Generated markdown** — Output from tools that will regenerate and overwrite changes
- **Markdown flavors with incompatible syntax** — If the file relies on extensions that conflict with GFM (e.g., custom directives that use `#` syntax)

---

## Guarantee

**Lossless transformation.** This skill changes markdown *structure* (headings, whitespace, tables), never *content* (text, code, references). Verification proves it.

---

## Quick Reference

### Constraint Hierarchy

| Priority | Constraint | Behavior |
|----------|------------|----------|
| **Hard** | Lossless content | No text added, removed, or reworded. Ever. |
| **Hard** | Preserve order | Sections stay in original sequence |
| **Hard** | Preserve references | URLs, images, code blocks byte-for-byte identical |
| **Soft** | Heading discipline | Normalize H1-H4 levels per rules |
| **Soft** | Formatting rules | Whitespace, tables, code fences |

**Conflict resolution:** If a soft constraint would require changing content, skip that change and log it.

### Allowed Changes

Only these markdown structural changes are permitted:

- Heading levels and markers (`#`, `##`, etc.)
- Table formatting (alignment, spacing)
- Blockquote markers
- Code-fence markers (language tags, fence length) — NOT contents
- Whitespace and line breaks
- Removing unnecessary escape backslashes (e.g., `\!` → `!`)

---

## Process

```
1. READ     → Read entire file, validate it's markdown
2. BASELINE → Extract plaintext from original (verification baseline)
3. HEADINGS → Normalize heading hierarchy
4. FORMAT   → Apply formatting rules (whitespace, tables, fences)
5. EXTRACT  → Extract plaintext from result
6. COMPARE  → Plaintexts MUST match exactly
7. CHECK    → Run structural checks
8. WRITE    → If all pass: write file + report
            → If any fail: abort + report divergence
```

---

## Heading Discipline

| Level | Usage | Rule |
|-------|-------|------|
| H1 | Document title | Exactly one per file |
| H2 | Major sections | TOC-level divisions |
| H3 | Subsections | Within H2 |
| H4 | Rare | Prefer splitting into H3s |
| H5+ | **Never** | Demote to H4 or restructure |

### H1 Normalization

| Condition | Action |
|-----------|--------|
| Zero H1s | Promote first H2 to H1 |
| One H1 | Keep as-is |
| Multiple H1s | Keep first, demote rest to H2 |

---

## Formatting Rules

| Element | Use for | Avoid |
|---------|---------|-------|
| **Bold** | Key terms (first use), critical warnings | General emphasis |
| *Italics* | Introducing terms, names | General emphasis |
| `inline code` | Commands, filenames, literals | Non-code jargon |
| Code blocks | Multi-line code/config/examples | Single commands |
| > Blockquotes | External quotes, callouts | Self-emphasis |
| Lists | 3+ parallel items, steps | — |
| Tables | Structured comparisons | Prose comparisons |
| `---` | Major topic shifts only | Section breaks |

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

### Special Cases

**2-item lists:** Warn in report but do NOT convert to prose. Lists carry semantic meaning (parallel structure, equal weight) that prose loses.

**Nested code blocks:** If a code block contains triple backticks, use a longer outer fence (e.g., four backticks).

**Unknown syntax:** If the input contains non-GFM syntax (footnotes, definition lists, directives), preserve it verbatim.

**YAML frontmatter:** If the file starts with `---` on line 1, preserve the entire frontmatter block (up to and including the closing `---`) byte-for-byte. Do not parse, reformat, or validate it.

---

## Verification

### Losslessness Check (Gate — Must Pass)

1. Extract plaintext from original file
2. Extract plaintext from reformatted file (same method)
3. Normalize whitespace in both (collapse runs to single space, trim)
4. Compare strings exactly

**If mismatch:** Report failure with first divergence point. Do NOT save changes.

**Plaintext extraction rules:**
- **Keep:** All visible text, link text (`[text](url)` → `text`), image alt text (`![alt](url)` → `alt`), code block contents
- **Strip:** Markdown syntax markers (`#`, `*`, `` ` ``, `|`, `>`), URLs, HTML tags
- **Remove entirely:** HTML comments (`<!-- ... -->`), YAML frontmatter

**Method:** Process the markdown line by line, applying regex or string operations to strip syntax markers while preserving text. The exact implementation may vary, but the rules above define what the output must contain.

### Structural Checks (Report)

| Check | Criterion |
|-------|-----------|
| H1 count | Exactly 1 |
| H5+ count | 0 |
| Link count | Unchanged |
| Image count | Unchanged |
| Code block count | Unchanged |

---

## Error Handling

| Condition | Action |
|-----------|--------|
| File does not exist | Report error; do not create file |
| File is empty | Report "Empty file — no changes needed" |
| File is binary/non-markdown | Report error; do not modify |
| Soft constraint conflicts with losslessness | Skip change; log in "Skipped changes" |

---

## Output Format

After formatting, return this verification report:

```markdown
## Verification Report

### Losslessness
- Plaintext match: ✓ PASS / ✗ FAIL (divergence at: "...")

### Structural Checks
| Check | Result |
|-------|--------|
| H1 count = 1 | ✓ / ✗ (actual: N) |
| H5+ count = 0 | ✓ / ✗ (actual: N) |
| Links intact | ✓ / ✗ (N links) |
| Images intact | ✓ / ✗ (N images) |
| Code blocks intact | ✓ / ✗ (N blocks) |

### Changes Made
- (List of structural changes, e.g., "Promoted H2 to H1", "Demoted 3 H5s to H4")

### Warnings
- (e.g., "Found 2-item list at line 45 — preserved as-is")

### Skipped Changes
- (Any changes skipped due to losslessness conflict, or "None")
```

---

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| Rewriting prose | Violates losslessness; this is structure formatting, not editing | Only change markdown markers |
| Converting 2-item lists to prose | Semantically lossy — lists convey parallel structure | Warn but preserve |
| Modifying code block contents | Code must be byte-identical; whitespace matters | Only touch fence markers |
| Changing URLs | Any change could break links | Preserve byte-for-byte |
| Over-padding tables | Creates noisy git diffs | Normalize alignment, don't over-pad |

---

## Decision Points

| Situation | Decision |
|-----------|----------|
| Zero H1s in file | Promote first H2 to H1 |
| Multiple H1s | Keep first, demote rest to H2 |
| H5+ headings | Demote to H4 (max depth) |
| 2-item list | Warn but preserve (don't convert to prose) |
| Soft constraint conflicts with hard constraint | Skip the soft change; log in "Skipped Changes" |
| Unknown markdown syntax | Preserve verbatim |
| YAML frontmatter present | Preserve byte-for-byte; do not parse or reformat |
| Losslessness check fails | Abort; do not save changes; report divergence point |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Losslessness check fails | Content was accidentally modified during formatting | Review plaintext extraction; ensure only structure markers changed |
| H1 count ≠ 1 after formatting | Edge case in H1 normalization logic | Check for frontmatter title vs body H1 confusion |
| Code block contents changed | Code fence markers were processed incorrectly | Ensure only fence markers (not contents) are touched |
| Links/images count changed | Link syntax was malformed or accidentally modified | Check for escaped brackets or nested link syntax |
| File rejected as non-markdown | Binary content or wrong encoding | Verify file is UTF-8 text without null bytes |
| Whitespace normalization breaks code | Whitespace inside code blocks was changed | Ensure code block boundaries are correctly detected |

---

## Examples

### BAD: Modifying content while formatting

An agent reformats the file but also "improves" the text:

```markdown
# My Document

Some introductory text explaining the purpose.  <!-- Changed "intro" to "introductory" -->

## Section One

Here are the details.  <!-- Changed "Details here" -->
```

**Why it's bad:** The agent changed "Some intro text" to "Some introductory text" and "Details here" to "Here are the details." This violates the losslessness guarantee. The plaintext comparison will fail.

### GOOD: Structure-only changes

### Before

```markdown
## My Document

Some intro text.

### Section One
Details here.

##### Deep Heading
More details.

**Important:** Don't do this.

- Item A
- Item B
```

### After

```markdown
# My Document

Some intro text.

## Section One

Details here.

### Deep Heading

More details.

**Important:** Don't do this.

- Item A
- Item B
```

### Verification Report

```markdown
## Verification Report

### Losslessness
- Plaintext match: ✓ PASS

### Structural Checks
| Check | Result |
|-------|--------|
| H1 count = 1 | ✓ |
| H5+ count = 0 | ✓ |
| Links intact | ✓ (0 links) |
| Images intact | ✓ (0 images) |
| Code blocks intact | ✓ (0 blocks) |

### Changes Made
- Promoted H2 "My Document" to H1
- Demoted H5 "Deep Heading" to H3
- Normalized blank lines before headings

### Warnings
- Found 2-item list at line 17 — preserved as-is

### Skipped Changes
- None
```

---

## Markdown Flavor

This formatter targets **GitHub Flavored Markdown (GFM)** per the [GFM spec v0.29](https://github.github.com/gfm/) (2019-04-06).

Supported extensions beyond CommonMark:
- Tables (pipe syntax)
- Strikethrough (`~~text~~`)
- Autolinks (bare URLs)
- Task lists (`- [ ]`, `- [x]`)

Unknown syntax from other flavors (footnotes, definition lists, directives): preserve verbatim.

---

## Extension Points

| Location | Purpose | How to Extend |
|----------|---------|---------------|
| Heading Discipline table | Custom heading rules | Add/modify rows |
| Formatting Rules table | New element handling | Add rows for new elements |
| Structural Checks table | Additional verification | Add rows for new checks |
| Special Cases section | Flavor-specific handling | Document new edge cases |
