# Type Example: Template/Generation Skills

**Load this reference when:** brainstorming-skills identifies the skill type as Template/Generation.

## Core Question

**Does output match the required format?**

Template/Generation skills produce specific output formats, documents, or structured artifacts. The failure mode is malformed output — structurally incorrect, missing required fields, or wrong format.

## Type Indicators

Your skill is Template/Generation if it:
- Specifies output structure, format, or schema
- Produces documents, reports, or artifacts
- Has required fields that must be present
- Success is measurable by structural compliance

## The Format Challenge

Template skills must verify:
1. **Structural compliance** — Does output match required structure?
2. **Field completeness** — Are all required fields present and populated?
3. **Content quality** — Is content meaningful, not just structurally correct?
4. **Edge case handling** — Does the template adapt to unusual inputs?

## Section Guidance

### Process Section

**Define the exact output structure:**

**Example (handoff document):**

```markdown
## Process

**Required Output Structure:**

```yaml
---
date: YYYY-MM-DD
time: "HH:MM"
project: <project-name>
branch: <current-branch>
commit: <short-hash>
title: <descriptive-title>
files:
  - <list of key files>
---

# Handoff: <title>

## Goal
<What we were trying to accomplish — 1-2 sentences>

## Decisions
<Key decisions made, with brief rationale>
- **Decision 1** — rationale
- **Decision 2** — rationale

## Changes
<What was modified>
`path/to/file`:
- Line X: description of change

## Next Steps
<Numbered list of what to do next>
1. First thing to do
2. Second thing to do

## References
<Links to relevant files, docs, or resources>
- `path/to/relevant/file` — why it's relevant
```

**Field Requirements:**

| Field | Required | Constraints |
|-------|----------|-------------|
| date | Yes | YYYY-MM-DD format |
| time | Yes | HH:MM in quotes (YAML string) |
| project | Yes | Git root directory name |
| branch | Yes | Current git branch |
| commit | Yes | Short hash (7 chars) |
| title | Yes | Descriptive, no colons |
| Goal | Yes | 1-2 sentences max |
| Decisions | Yes | At least 1 if decisions were made, "None" otherwise |
| Changes | If applicable | List files and line-level changes |
| Next Steps | Yes | Numbered, actionable items |
| References | Yes | At least 1 relevant file |
```

**Anti-pattern:** Vague structure like "include relevant information."

### Decision Points Section

Focus on **format adaptation and edge cases**:

**Example:**

```markdown
## Decision Points

**Missing information:**
- If no changes were made → Use "## Changes\nNone — research/exploration session only"
- If no decisions were made → Use "## Decisions\nNone — execution only, no decision points"
- If next steps are unclear → Use "## Next Steps\n1. [To be determined based on X]"

**Content doesn't fit structure:**
- If a section would be very long → Summarize in the section, reference a separate file for details
- If information spans multiple sections → Put it in the most relevant section, cross-reference

**Edge cases:**
- Research session (no code changes) → Adapt Changes to describe what was learned
- Failed attempt → Document what was tried and why it failed in Changes
- Multiple unrelated tasks → Consider separate handoff documents

**Format vs content tradeoff:**
- If content is valuable but doesn't fit structure → Prefer capturing the content. Add a "Notes" section if needed.
- Structure serves content, not the other way around
```

### Examples Section

Show **format compliance comparison**:
- Before: Malformed or incomplete structure
- After: Correct structure with all required fields

**Example:**

```markdown
## Examples

**Scenario:** Create handoff after a debugging session

**Before** (without skill):
```
# Session Notes

Spent time debugging the login issue. Found it was a race condition in the auth flow. Fixed it by adding a mutex. Still need to add tests.

Files changed:
- auth.py
- tests/test_auth.py (not yet)
```

Problems:
- No YAML frontmatter
- Missing required fields (date, branch, commit)
- "Changes" doesn't specify what changed in auth.py
- "Next Steps" is prose, not numbered actionable items
- No References section

**After** (with skill):
```yaml
---
date: 2026-01-19
time: "14:30"
project: myapp
branch: fix/login-race-condition
commit: a1b2c3d
title: Login race condition fix
files:
  - src/auth.py
---

# Handoff: Login race condition fix

## Goal
Fix intermittent login failures caused by race condition in authentication flow.

## Decisions
- **Used mutex over queue** — simpler for this case, queue would be overengineering
- **Fixed in auth.py only** — the race was isolated, no need to refactor broader flow

## Changes
`src/auth.py`:
- Line 45: Added `threading.Lock()` for token refresh
- Line 52-58: Wrapped token check in lock context manager

## Next Steps
1. Add test case for concurrent login attempts
2. Monitor for any performance impact from locking
3. Consider async refactor if lock becomes bottleneck

## References
- `src/auth.py` — the fix location
- `docs/auth-flow.md` — architecture context for the auth system
```
```

### Anti-Patterns Section

Focus on **format violations and content shortcuts**:

**Example:**

```markdown
## Anti-Patterns

**Pattern:** Correct structure but placeholder content
**Why it fails:** "## Decisions\n- Decision 1" passes structural validation but isn't useful.
**Fix:** Each field must have meaningful content. Empty or placeholder values should be explicitly marked ("None" or "N/A — reason").

**Pattern:** Prose instead of structured fields
**Why it fails:** "I worked on auth stuff" isn't parseable. Future readers can't quickly scan.
**Fix:** Use the specified format. Bullets, tables, and structured fields enable scanning.

**Pattern:** Skipping "optional" sections entirely
**Why it fails:** "Optional" means "if applicable," not "skip to save time." References are always applicable.
**Fix:** Fill all sections. Use "None" or "N/A" with reason if truly not applicable.

**Pattern:** Adapting structure without noting deviation
**Why it fails:** Reader expects standard format. Surprises cause confusion.
**Fix:** If you must deviate, note it: "Note: Combining Changes and Decisions due to overlap."
```

### Troubleshooting Section

Address **format failures**:

**Example:**

```markdown
## Troubleshooting

**Symptom:** YAML frontmatter causes parsing errors
**Cause:** Special characters in fields (colons in title, unquoted times)
**Next steps:** Quote string values, escape special characters, validate YAML syntax.

**Symptom:** Document is structurally correct but not useful
**Cause:** Content is too terse or generic to be actionable
**Next steps:** Expand content. "Fixed bug" → "Fixed race condition in auth by adding mutex to token refresh."

**Symptom:** Document is too long to scan
**Cause:** Too much detail in main sections
**Next steps:** Summarize in main sections, move details to References or separate files.

**Symptom:** Required information isn't available
**Cause:** Generating document before information exists (e.g., commit hash before committing)
**Next steps:** Generate document at the right time, or use placeholder with instruction: "[commit hash — fill after committing]"
```

## Testing This Type

Template/Generation skills need **structural validation**:

1. **Structure test:** Does output have all required sections?
2. **Field test:** Are all required fields present and populated?
3. **Format test:** Does output pass format validation (YAML parsing, markdown rendering)?
4. **Edge case test:** Does template adapt gracefully to unusual inputs?
5. **Content test:** Is content meaningful, not just structurally valid?

See `type-specific-testing.md` → Type 8: Template/Generation Skills for scenario templates.

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Vague structure definition | Can't verify compliance | Specify exact format, required fields, constraints |
| Placeholder content | Structurally valid but useless | Every field needs meaningful content |
| No edge case handling | Breaks on unusual inputs | Add Decision Points for missing/unusual data |
| Format over content | Valid structure, worthless information | Structure serves content; prioritize usefulness |
