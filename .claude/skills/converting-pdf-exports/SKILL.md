---
name: converting-pdf-exports
description: Use when a markdown file is actually a PDF export with layout artifacts (page numbers, column merges, missing heading markers). Use when user says "convert this PDF export", "clean up this PDF-to-markdown", or "this markdown came from a PDF".
argument-hint: [file-path]
---

# Converting PDF Exports

Convert PDF exports into clean, native markdown. PDF-to-markdown conversions often contain layout artifacts — page numbers, two-column text merged into single lines, missing heading markers, chapter prefixes. This skill systematically identifies and removes these artifacts while preserving all actual content.

**Relationship to markdown-formatter:** This skill performs *conversion* (lossy — removes artifacts). The `markdown-formatter` skill performs *formatting* (lossless — normalizes structure). They compose: run this skill first, optionally run markdown-formatter after for polish.

**Outputs:**

- Clean markdown file (overwrites original or creates new file, per user choice)

**Definition of Done:**

- All PDF artifacts identified and removed
- Proper heading hierarchy established
- Content preserved (no prose rewriting)
- User confirmed output location
- Ambiguous cases resolved with user

---

## Triggers

- "convert this PDF export"
- "clean up this PDF-to-markdown"
- "this markdown came from a PDF"
- "convert this to proper markdown"
- "this file has PDF artifacts"

---

## Process

### 1. Read and Assess

Read the entire file. Identify artifact types present:

| Artifact Type | Signature |
|---------------|-----------|
| Page numbers | Standalone numbers (often on their own line), "Page N", or numbers at regular intervals |
| Chapter markers | "Chapter N" followed by title on separate line |
| Column merges | Mid-sentence topic shifts; text from adjacent columns concatenated |
| Missing headings | Lines that function as headings but lack `#` markers |
| Table of contents | Page numbers after section names (e.g., "Introduction    3") |
| Headers/footers | Repeated text at regular intervals (document title, author, date) |

**If file appears clean** (no artifacts detected): Stop and confirm with user — "This file appears to already be clean markdown. Should I proceed anyway?"

**If file is heavily mangled** (extensive artifacts, unclear structure): Stop and present issues to user. Ask: "Should I proceed with best effort, or is manual conversion better for this file?"

### 2. Establish Structure

Identify the document's intended hierarchy:

1. **Find the title** — Usually at the start, often split across lines or lacking `#`
2. **Identify major sections** — Chapter titles, main headings (become H2)
3. **Identify subsections** — Section divisions within chapters (become H3)
4. **Identify sub-subsections** — If present, become H4 (max depth)

**When ambiguous:** Stop and ask. "Is '[text]' a heading or regular content?"

### 3. Plan Artifact Removal

For each artifact type identified in Step 1, plan the removal:

- **Page numbers:** Remove entirely
- **Chapter markers:** Merge with title, convert to heading
- **Column merges:** Separate into proper paragraphs (light cleanup allowed)
- **TOC with page numbers:** Convert to markdown TOC with anchor links, or remove if redundant
- **Headers/footers:** Remove entirely

### 4. Confirm Output Location

Ask user: "Should I overwrite the original file, or create a new file (e.g., `filename-converted.md`)?"

Wait for response before proceeding.

### 5. Execute Conversion

Apply planned changes systematically:

1. Remove page numbers and headers/footers
2. Establish H1 (document title)
3. Convert section markers to proper headings (H2/H3/H4)
4. Fix column-merge breaks (rejoin sentences, separate paragraphs)
5. Normalize whitespace (blank lines around headings, single trailing newline)
6. Convert or remove TOC as planned

**Constraint:** Change structure, fix obvious breaks. Never rewrite prose.

### 6. Verify and Report

After conversion, provide a summary:

```
## Conversion Summary

**Artifacts removed:**
- [list what was removed]

**Structure changes:**
- [heading hierarchy established]

**Content preserved:** Yes / No (if no, explain)

**Ambiguities resolved:** [list any questions asked and answers received]
```

---

## Decision Points

**File assessment unclear:**

- If uncertain whether file needs conversion → Ask: "This file has some markdown structure but also some PDF-like patterns. Should I convert it or leave it as-is?"
- If file is already clean markdown → Stop and inform user; don't process unnecessarily

**Ambiguous heading vs. content:**

- If a line could be a heading OR regular content → Stop and ask: "Is '[text]' a section heading or regular paragraph text?"
- Never guess on heading hierarchy — wrong guesses cascade through the document

**Column merge reconstruction:**

- If sentence breaks are clear → Fix silently (rejoin "The quick brown" + "fox jumps")
- If reconstruction requires judgment → Ask: "These lines appear to be merged columns. Should '[text A]' connect to '[text B]', or are they separate paragraphs?"

**Heavily mangled file:**

- If >30% of content is ambiguous → Present issues and ask whether to proceed with best effort or abort
- If user says proceed → Convert what's clear, mark uncertain sections with `<!-- REVIEW: [issue] -->`

**Structure conflicts:**

- If document has multiple apparent H1s → Ask which is the true title
- If heading hierarchy is inconsistent (H1 → H4 jump) → Ask whether to normalize or preserve original intent

---

## Examples

**Scenario:** User provides a `.md` file that's actually a PDF export of a technical guide.

### BAD: Quick cleanup without systematic process

Claude sees the file, recognizes it's messy, and makes quick edits:

- Removes some obvious page numbers
- Adds `#` to a few lines that look like headings
- Leaves column-merged text as-is ("it's readable enough")
- Doesn't ask about ambiguities
- Overwrites original without asking

Result: Document is still inconsistent. Some page numbers remain. Heading hierarchy is wrong (H1 → H3 jumps). A paragraph that was actually a heading is now buried in text. User's original is gone.

**Why it's bad:** No systematic artifact identification. No user checkpoints. Guessed instead of asking. Irreversible action without confirmation.

### GOOD: Systematic conversion with checkpoints

Claude follows the process:

1. **Read and Assess:** Identifies page numbers (lines 22, 107, 156...), chapter markers ("Chapter 1" + "Fundamentals"), column merges (line 24-28), missing headings
2. **Establish Structure:** Title is lines 1-3, chapters become H2, subsections become H3
3. **Plan Removal:** Documents what will be removed/changed
4. **Confirm Output:** Asks "Overwrite or new file?" — user says overwrite
5. **Execute:** Systematic conversion following the plan
6. **Verify:** Reports what was done

During conversion, encounters ambiguity: "Is 'Two Paths Through This Guide' a heading or emphasized text?" Asks user. User says heading. Proceeds.

Result: Clean markdown with proper hierarchy. All artifacts removed. Content preserved. User confirmed key decisions.

**Why it's good:** Systematic identification. User checkpoints on output location and ambiguities. Reversible until confirmed. Summary shows what changed.

---

## Anti-Patterns

### Jumping straight to editing

**Pattern:** Claude sees a messy file and starts making changes immediately without reading the whole file first.

**Why it fails:** Artifact patterns repeat throughout the document. Without reading the whole file, you miss patterns and make inconsistent changes. Page numbers at line 22 and line 500 need the same treatment.

**Fix:** Always read the entire file first. Identify all artifact types before changing anything.

---

### Guessing on ambiguities

**Pattern:** Claude encounters something that could be a heading or content, makes a judgment call, and continues.

**Why it fails:** Wrong heading decisions cascade — everything nested under a wrong H2 is now misplaced. The user knows their document; Claude is guessing.

**Fix:** When genuinely ambiguous, stop and ask. "Is '[text]' a heading?" takes 5 seconds. Fixing a wrong heading hierarchy takes minutes.

---

### "Light cleanup" scope creep

**Pattern:** Claude starts improving prose while converting: fixing awkward phrasing, adding transitions, "clarifying" sentences.

**Why it fails:** This skill converts structure, not content. Prose changes violate user trust — they expected artifact removal, not editing. Changes may alter meaning.

**Fix:** Structure and obvious breaks only. If a sentence is awkward but intact, leave it. The user can edit prose separately.

---

### Overwriting without asking

**Pattern:** Claude writes directly to the original file without confirming.

**Why it fails:** The original may be the only copy. The user may want to compare before/after. Overwriting is irreversible.

**Fix:** Always ask: "Overwrite or create new file?" Wait for answer.

---

## Troubleshooting

**Symptom:** Conversion removed content that wasn't an artifact
**Cause:** Misidentified actual content as a page number or header (e.g., a section titled "3" or a repeated phrase that was intentional)
**Next steps:** Review the artifact identification step. When in doubt, ask before removing. If already removed, restore from original and re-convert with more care.

---

**Symptom:** Heading hierarchy is inconsistent after conversion
**Cause:** Document had ambiguous structure; guesses were made instead of asking
**Next steps:** Check the structure establishment step. Identify where hierarchy went wrong. Ask user to clarify the intended structure.

---

**Symptom:** Column-merged text is still garbled
**Cause:** The merge pattern was too complex to reconstruct automatically
**Next steps:** Flag specific sections for user review. Mark with `<!-- REVIEW: column merge unclear -->`. Don't guess at paragraph breaks when unclear.

---

**Symptom:** User says "this changed my content"
**Cause:** Either (a) prose was accidentally edited, or (b) user perceives structure changes as content changes
**Next steps:** If (a): this violates the skill's constraints — apologize and restore. If (b): explain that heading markers and whitespace are structure, not content; the words are unchanged.

---

**Symptom:** Skill triggered on a file that didn't need conversion
**Cause:** File had some PDF-like patterns but was actually intentional formatting
**Next steps:** The assessment step should have caught this. Ask before proceeding on borderline files.

---

## Rationalizations to Watch For

| Excuse | Reality |
|--------|---------|
| "This file is almost clean, I'll just make quick edits" | "Almost clean" files still need systematic assessment. Quick edits miss patterns and create inconsistency. |
| "I can see what the structure should be" | Confidence isn't proof. If it's truly obvious, asking takes 5 seconds. If you're wrong, fixing takes much longer. |
| "The user seems in a hurry" | Rushing creates errors that take longer to fix than doing it right. Acknowledge the pressure, complete the process. |
| "This is clearly a heading, no need to ask" | "Clearly" to you may not match the author's intent. Ask on any genuine ambiguity. |
| "I'll just overwrite, they can undo" | They may not have version control. They may not know how to undo. Always ask about output location. |
| "The column merge is obvious" | If reconstruction requires any judgment about what connects to what, ask. Obvious to you ≠ correct. |

**All of these mean: Complete the process. No shortcuts.**

---

## Extension Points

| Extension | How |
|-----------|-----|
| Compose with markdown-formatter | After conversion, run `/markdown-formatter` on the output for additional structure normalization (heading discipline, whitespace, table formatting) |
| Batch conversion | For multiple files, establish patterns from first file, then apply consistently (still ask on new ambiguities) |
| Source-specific patterns | If you frequently convert from a specific source (e.g., Notion exports, Google Docs), document its artifact patterns for faster identification |
