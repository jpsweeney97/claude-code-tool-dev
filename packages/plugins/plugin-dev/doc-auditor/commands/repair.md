---
name: repair
description: Interactive repair session for documentation issues
argument-hint: "[--critical | --category=X | ISSUE-ID]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Edit
  - Write
  - AskUserQuestion
---

Start an interactive documentation repair session.

## Your Task

Walk through detected issues from the last scan, presenting each with its proposed fix and letting the user decide how to proceed.

## Setup

1. **Load scan results**:
   - Location: `.claude/doc-auditor/scan-results.json`
   - If missing: inform user to run `/doc-auditor:scan` first and exit
   - If corrupted (invalid JSON or missing required fields): delete file, inform user, exit

2. **Validate scan results**:
   - Check `$schema` field exists
   - Check `generated` field exists
   - Check `issues` array exists
   - If any fail: delete file, prompt re-scan

3. **Check staleness**:
   - Parse `generated` timestamp
   - If >1 hour old, show warning:
     ```
     Scan performed: [timestamp]
     Current time: [now]

     If you've edited documentation since the scan, some fixes may fail.
     Run `/doc-auditor:scan` to refresh, or continue with current results.
     ```

4. **Apply filters** based on arguments:
   - `--critical`: Only CRITICAL and HIGH severity
   - `--category=X`: Only issues in category X (e.g., `--category=contradictions`)
   - `ISSUE-ID`: Single issue by its 8-character ID
   - No arguments: All issues, sorted by severity (CRITICAL first)

5. **Read suppressed count**:
   - Count items in `inline_suppressed[]` to report how many were skipped

## Interactive Loop

For each issue, present it clearly then ask the user what to do.

### Issue Presentation

```markdown
## Issue [N] of [total]: [Category]

**ID:** [issue.id]
**Severity:** [issue.severity]
**Category:** [issue.category] / [issue.subcategory]

**Problem:** [issue.description]

**Location:** [issue.location.file] (line ~[issue.location.line_hint])

**Evidence:**
> [quote from evidence]
> — [source file:line]

[If multiple evidence items, show each]

**Impact:** [issue.impact]

**Proposed Fix:**
[If type is replace/insert/delete, show the change]
[If type is manual, show options]

Confidence: [proposed_fix.confidence]
```

### User Decision

Use AskUserQuestion with these options:

| Option | Description |
|--------|-------------|
| Accept | Apply this fix |
| Skip | Move to next issue |
| Suppress | Add inline suppression, don't flag again |
| Exit | End session |

The user can also select "Other" to provide custom text (modify the fix).

### Handle Response

**Accept:**
1. If fix type is `replace`:
   - Use Edit tool with `old_string` and `new_string`
   - If Edit fails (text not found): report "Text changed since scan. Skipping."
2. If fix type is `insert`:
   - Use Edit to find `after_text` and replace with `after_text + insert_text`
3. If fix type is `delete`:
   - Use Edit with `old_string` and empty `new_string`
4. If fix type is `manual`:
   - Present options to user
   - Apply their choice
5. Track as fixed

**Skip:**
- Move to next issue
- Track as skipped

**Suppress:**
1. Determine suppression location from issue.location
2. Add inline comment: `<!-- doc-auditor:ignore-line [category] -->`
3. Use Edit tool to insert the comment
4. Track as suppressed

**Exit:**
- End loop
- Show summary

**Other (user provides text):**
- If text looks like replacement content: use as `new_string`
- If text is a batch command (e.g., "skip all LOW"): apply to remaining issues
- If unclear: ask for clarification

## Session Summary

When loop ends (all issues processed or user exits):

```markdown
## Session Complete

**Processed:** [N] issues

| Action | Count |
|--------|-------|
| Fixed | [X] |
| Skipped | [Y] |
| Suppressed | [Z] |

**Remaining:** [total - processed] issues not reviewed

[If inline_suppressed count > 0:]
Note: [N] issues were already suppressed via inline comments.

**Next Steps:**
- Run `/doc-auditor:scan` to verify fixes
- Review skipped issues with `/doc-auditor:repair`
```

## Edge Cases

| Situation | Behavior |
|-----------|----------|
| No scan results | "No scan results found. Run `/doc-auditor:scan` first." |
| Scan results corrupted | "Scan results corrupted. Run `/doc-auditor:scan` to regenerate." |
| Stale scan (>1 hour) | Show warning; continue |
| All issues fixed | "All issues resolved!" |
| Filter matches nothing | "No issues match filter. Try different options." |
| Fix text not found | "Text has changed since scan. Skipping." |
| old_string not unique | "Cannot auto-apply: text not unique. Please fix manually." |

## Important Notes

- This command runs in the MAIN CONVERSATION (not as an agent) to enable interactive back-and-forth
- Session state is NOT persisted — each invocation is fresh
- Fixed issues disappear on next scan (they're resolved in the docs)
- Skipped issues reappear on next fix invocation
- Suppressed issues don't reappear (they have inline comments)
