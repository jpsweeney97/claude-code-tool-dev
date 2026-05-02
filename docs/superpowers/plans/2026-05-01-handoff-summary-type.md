# Handoff Summary Type Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `summary` handoff type that captures session context at moderate depth (120-250 lines, 8 sections) and synthesizes the project arc across sessions.

**Architecture:** New `summary` type joins the existing `handoff`/`checkpoint` type system. Uses the same chain protocol, frontmatter schema, and storage conventions. The quality check hook learns summary validation rules. A new skill file drives the `/summary` command. Three existing skills get minor updates (load display string, defer source_type).

**Tech Stack:** Python (quality_check.py, tests), Markdown (skill files, reference docs)

**Design spec:** `docs/superpowers/specs/2026-05-01-handoff-summary-type-design.md`

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `scripts/quality_check.py` | Modify | Add summary constants, validation rules, line count range |
| `tests/test_quality_check.py` | Modify | Add summary-specific test cases |
| `references/handoff-contract.md` | Modify | Add summary to type field, title convention, filename convention |
| `references/format-reference.md` | Modify | Add summary section table and quality calibration row |
| `skills/summary/SKILL.md` | Create | New skill driving `/summary` command |
| `skills/load/SKILL.md` | Modify | Add summary display string |
| `skills/defer/SKILL.md` | Modify | Accept `summary` as valid `source_type` |
| `.claude-plugin/plugin.json` | Modify | Version bump to 1.6.0 |

All paths are relative to `packages/plugins/handoff/`.

---

### Task 1: Add summary validation to quality_check.py (TDD)

**Files:**
- Modify: `packages/plugins/handoff/scripts/quality_check.py`
- Modify: `packages/plugins/handoff/tests/test_quality_check.py`

- [ ] **Step 1: Write failing tests for summary constants and valid type**

Add to the top of `tests/test_quality_check.py` — update the import block to include the new constants, then add a test class:

Update the import to add the new symbols:

```python
from scripts.quality_check import (
    CHECKPOINT_MAX_LINES,
    CHECKPOINT_MIN_LINES,
    CONTENT_REQUIRED_SECTIONS,
    HANDOFF_MIN_LINES,
    REQUIRED_CHECKPOINT_SECTIONS,
    REQUIRED_HANDOFF_SECTIONS,
    REQUIRED_SUMMARY_SECTIONS,
    SUMMARY_MAX_LINES,
    SUMMARY_MIN_LINES,
    VALID_TYPES,
    Issue,
    count_body_lines,
    format_output,
    is_handoff_path,
    main,
    parse_frontmatter,
    parse_sections,
    validate,
    validate_frontmatter,
    validate_line_count,
    validate_sections,
)
```

Add a new test class after `TestValidate`:

```python
# --- Summary type ---


class TestSummaryConstants:
    """Tests for summary type constants and basic type acceptance."""

    def test_summary_in_valid_types(self) -> None:
        assert "summary" in VALID_TYPES

    def test_summary_sections_defined(self) -> None:
        assert len(REQUIRED_SUMMARY_SECTIONS) == 8
        assert "Project Arc" in REQUIRED_SUMMARY_SECTIONS
        assert "Goal" in REQUIRED_SUMMARY_SECTIONS
        assert "Session Narrative" in REQUIRED_SUMMARY_SECTIONS
        assert "Decisions" in REQUIRED_SUMMARY_SECTIONS
        assert "Changes" in REQUIRED_SUMMARY_SECTIONS
        assert "Codebase Knowledge" in REQUIRED_SUMMARY_SECTIONS
        assert "Learnings" in REQUIRED_SUMMARY_SECTIONS
        assert "Next Steps" in REQUIRED_SUMMARY_SECTIONS

    def test_summary_line_count_constants(self) -> None:
        assert SUMMARY_MIN_LINES == 120
        assert SUMMARY_MAX_LINES == 250
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_quality_check.py::TestSummaryConstants -v`

Expected: ImportError — `REQUIRED_SUMMARY_SECTIONS`, `SUMMARY_MAX_LINES`, `SUMMARY_MIN_LINES` not defined.

- [ ] **Step 3: Add summary constants to quality_check.py**

In `scripts/quality_check.py`, add after the `REQUIRED_CHECKPOINT_SECTIONS` constant (line 58):

```python
REQUIRED_SUMMARY_SECTIONS: tuple[str, ...] = (
    "Goal",
    "Session Narrative",
    "Decisions",
    "Changes",
    "Codebase Knowledge",
    "Learnings",
    "Next Steps",
    "Project Arc",
)
```

Update `VALID_TYPES` (line 60) to:

```python
VALID_TYPES: frozenset[str] = frozenset({"handoff", "checkpoint", "summary"})
```

Add after `CHECKPOINT_MAX_LINES` (line 71):

```python
SUMMARY_MIN_LINES: int = 120
SUMMARY_MAX_LINES: int = 250
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_quality_check.py::TestSummaryConstants -v`

Expected: 3 passed.

- [ ] **Step 5: Write failing tests for summary frontmatter validation**

Add to `TestValidateFrontmatter` class:

```python
    def test_summary_title_missing_prefix(self) -> None:
        fm = _make_frontmatter(
            overrides={"type": "summary", "title": "No Prefix"}
        )
        issues = validate_frontmatter(fm, "summary")
        assert any("Summary:" in i.message for i in issues)

    def test_summary_title_valid(self) -> None:
        fm = _make_frontmatter(
            overrides={"type": "summary", "title": "Summary: Valid Title"}
        )
        assert validate_frontmatter(fm, "summary") == []
```

- [ ] **Step 6: Run tests to verify they fail**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_quality_check.py::TestValidateFrontmatter::test_summary_title_missing_prefix tests/test_quality_check.py::TestValidateFrontmatter::test_summary_title_valid -v`

Expected: `test_summary_title_missing_prefix` FAILS (no prefix check for summary type). `test_summary_title_valid` may pass vacuously.

- [ ] **Step 7: Update validate_frontmatter for summary title prefix**

In `scripts/quality_check.py`, in `validate_frontmatter()`, after the checkpoint title check (around line 205), add:

```python
    if doc_type == "summary" and "title" in frontmatter:
        title = frontmatter["title"]
        if not title.startswith("Summary:"):
            issues.append(Issue(
                "warning",
                f"Summary title should start with 'Summary:', "
                f"got: '{title[:60]}'",
            ))
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_quality_check.py::TestValidateFrontmatter -v`

Expected: All pass including the 2 new tests.

- [ ] **Step 9: Write failing tests for summary section validation**

Add to `TestValidateSections` class:

```python
    def test_all_summary_sections_present(self) -> None:
        sections = [
            {"heading": s, "content": "text"}
            for s in REQUIRED_SUMMARY_SECTIONS
        ]
        assert validate_sections(sections, "summary") == []

    def test_summary_missing_section(self) -> None:
        sections = [
            {"heading": s, "content": "text"}
            for s in REQUIRED_SUMMARY_SECTIONS
            if s != "Project Arc"
        ]
        issues = validate_sections(sections, "summary")
        assert any("Project Arc" in i.message for i in issues)

    def test_hollow_summary_guardrail(self) -> None:
        """All 8 sections present but Decisions/Changes/Learnings all empty."""
        sections = []
        for s in REQUIRED_SUMMARY_SECTIONS:
            if s in CONTENT_REQUIRED_SECTIONS:
                sections.append({"heading": s, "content": ""})
            else:
                sections.append({"heading": s, "content": "text"})
        issues = validate_sections(sections, "summary")
        assert any(
            i.severity == "error" and "Hollow" in i.message
            for i in issues
        )

    def test_hollow_guardrail_not_applied_to_checkpoints_still(self) -> None:
        """Hollow guardrail is for handoff and summary only, not checkpoint."""
        sections = [
            {"heading": s, "content": ""} for s in REQUIRED_CHECKPOINT_SECTIONS
        ]
        issues = validate_sections(sections, "checkpoint")
        assert not any("Hollow" in i.message for i in issues)
```

- [ ] **Step 10: Run tests to verify they fail**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_quality_check.py::TestValidateSections::test_all_summary_sections_present tests/test_quality_check.py::TestValidateSections::test_summary_missing_section tests/test_quality_check.py::TestValidateSections::test_hollow_summary_guardrail -v`

Expected: `test_all_summary_sections_present` FAILS — `validate_sections` doesn't know about summary required sections. `test_summary_missing_section` may pass or fail depending on fallback. `test_hollow_summary_guardrail` FAILS — guardrail only checks `doc_type == "handoff"`.

- [ ] **Step 11: Update validate_sections for summary type**

In `scripts/quality_check.py`, update `validate_sections()`:

Change the `required` assignment (around line 222) from:

```python
    required = (
        REQUIRED_HANDOFF_SECTIONS
        if doc_type == "handoff"
        else REQUIRED_CHECKPOINT_SECTIONS
    )
```

to:

```python
    if doc_type == "handoff":
        required = REQUIRED_HANDOFF_SECTIONS
    elif doc_type == "summary":
        required = REQUIRED_SUMMARY_SECTIONS
    else:
        required = REQUIRED_CHECKPOINT_SECTIONS
```

Change the hollow-handoff guardrail condition (around line 243) from:

```python
    if doc_type == "handoff":
```

to:

```python
    if doc_type in ("handoff", "summary"):
```

- [ ] **Step 12: Run tests to verify they pass**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_quality_check.py::TestValidateSections -v`

Expected: All pass including the 4 new tests.

- [ ] **Step 13: Write failing tests for summary line count validation**

Add to `TestValidateLineCount` class:

```python
    def test_summary_within_range(self) -> None:
        content = "\n".join(["line"] * 180)
        assert validate_line_count(content, "summary") == []

    def test_summary_below_minimum(self) -> None:
        content = "\n".join(["line"] * 80)
        issues = validate_line_count(content, "summary")
        assert len(issues) == 1
        assert issues[0].severity == "error"
        assert "80" in issues[0].message

    def test_summary_above_maximum(self) -> None:
        content = "\n".join(["line"] * 300)
        issues = validate_line_count(content, "summary")
        assert len(issues) == 1
        assert issues[0].severity == "warning"
        assert "300" in issues[0].message

    def test_summary_at_exact_boundaries(self) -> None:
        at_min = "\n".join(["line"] * SUMMARY_MIN_LINES)
        at_max = "\n".join(["line"] * SUMMARY_MAX_LINES)
        assert validate_line_count(at_min, "summary") == []
        assert validate_line_count(at_max, "summary") == []
```

- [ ] **Step 14: Run tests to verify they fail**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_quality_check.py::TestValidateLineCount::test_summary_within_range tests/test_quality_check.py::TestValidateLineCount::test_summary_below_minimum tests/test_quality_check.py::TestValidateLineCount::test_summary_above_maximum tests/test_quality_check.py::TestValidateLineCount::test_summary_at_exact_boundaries -v`

Expected: All FAIL — `validate_line_count` has no `summary` branch.

- [ ] **Step 15: Update validate_line_count for summary type**

In `scripts/quality_check.py`, in `validate_line_count()`, add after the checkpoint block (around line 307):

```python
    elif doc_type == "summary":
        if body_lines < SUMMARY_MIN_LINES:
            issues.append(Issue(
                "error",
                f"Summary body is {body_lines} lines "
                f"(minimum: {SUMMARY_MIN_LINES}). "
                "Under-capturing session content.",
            ))
        elif body_lines > SUMMARY_MAX_LINES:
            issues.append(Issue(
                "warning",
                f"Summary body is {body_lines} lines "
                f"(maximum: {SUMMARY_MAX_LINES}). "
                "Consider a full handoff instead.",
            ))
```

- [ ] **Step 16: Run tests to verify they pass**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_quality_check.py::TestValidateLineCount -v`

Expected: All pass including the 4 new tests.

- [ ] **Step 17: Write end-to-end test for valid summary**

Add to `TestValidate` class:

```python
    def test_valid_summary(self) -> None:
        content = _make_content(
            frontmatter=_make_frontmatter(
                overrides={
                    "type": "summary",
                    "title": "Summary: Test Session",
                }
            ),
            sections=list(REQUIRED_SUMMARY_SECTIONS),
            lines_per_section=15,
        )
        assert validate(content) == []
```

Add to `TestMain` class:

```python
    def test_valid_summary_end_to_end_silent(self) -> None:
        """Valid summary through full main() pipeline produces no output."""
        content = _make_content(
            frontmatter=_make_frontmatter(
                overrides={
                    "type": "summary",
                    "title": "Summary: Test Session",
                }
            ),
            sections=list(REQUIRED_SUMMARY_SECTIONS),
            lines_per_section=15,
        )
        result, output = _run_main(
            _make_hook_input(HANDOFF_PATH, content)
        )
        assert result == 0
        assert output == ""
```

- [ ] **Step 18: Run the end-to-end tests**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_quality_check.py::TestValidate::test_valid_summary tests/test_quality_check.py::TestMain::test_valid_summary_end_to_end_silent -v`

Expected: Both pass.

- [ ] **Step 19: Write test verifying invalid type error message includes summary**

Add to `TestValidate` class:

```python
    def test_invalid_type_error_lists_all_types(self) -> None:
        """Error message for invalid type should list all valid types including summary."""
        content = _make_content(
            frontmatter=_make_frontmatter(overrides={"type": "bogus"}),
        )
        issues = validate(content)
        assert len(issues) == 1
        assert "summary" in issues[0].message
        assert "handoff" in issues[0].message
        assert "checkpoint" in issues[0].message
```

- [ ] **Step 20: Run the invalid-type test**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_quality_check.py::TestValidate::test_invalid_type_error_lists_all_types -v`

Expected: PASS — the existing code uses `sorted(VALID_TYPES)` in the error message, which automatically includes the new `summary` entry.

- [ ] **Step 21: Run full test suite**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_quality_check.py -v`

Expected: All existing tests pass, all new tests pass. No regressions.

- [ ] **Step 22: Commit**

```bash
git add packages/plugins/handoff/scripts/quality_check.py packages/plugins/handoff/tests/test_quality_check.py
git commit -m "feat(handoff): add summary type validation to quality_check.py

Add REQUIRED_SUMMARY_SECTIONS, SUMMARY_MIN_LINES (120),
SUMMARY_MAX_LINES (250). Summary validates 8 required sections,
title prefix, line count range, and hollow-summary guardrail."
```

---

### Task 2: Update reference docs (contract and format reference)

**Files:**
- Modify: `packages/plugins/handoff/references/handoff-contract.md`
- Modify: `packages/plugins/handoff/references/format-reference.md`

- [ ] **Step 1: Update handoff-contract.md — type field**

In `references/handoff-contract.md`, update the frontmatter schema `type` line from:

```yaml
type: <handoff|checkpoint>          # Required: distinguishes file type
```

to:

```yaml
type: <handoff|checkpoint|summary>  # Required: distinguishes file type
```

- [ ] **Step 2: Update handoff-contract.md — type field description**

Update the **Type field** paragraph from:

```markdown
**Type field:** `handoff` for full handoffs, `checkpoint` for checkpoints. Existing files without a `type` field are treated as `handoff` for backwards compatibility.
```

to:

```markdown
**Type field:** `handoff` for full handoffs, `checkpoint` for checkpoints, `summary` for summaries. Existing files without a `type` field are treated as `handoff` for backwards compatibility.
```

- [ ] **Step 3: Update handoff-contract.md — title convention**

Update the **Title convention** paragraph from:

```markdown
**Title convention:** Checkpoint titles use `"Checkpoint: <title>"` prefix. Full handoff titles have no prefix.
```

to:

```markdown
**Title convention:** Checkpoint titles use `"Checkpoint: <title>"` prefix. Summary titles use `"Summary: <title>"` prefix. Full handoff titles have no prefix.
```

- [ ] **Step 4: Update handoff-contract.md — filename slug**

Update the **Filename slug** paragraph from:

```markdown
**Filename slug:** Lowercase, hyphens for spaces, no special characters. Checkpoints use `checkpoint-<slug>`, full handoffs use `<slug>` directly.
```

to:

```markdown
**Filename slug:** Lowercase, hyphens for spaces, no special characters. Checkpoints use `checkpoint-<slug>`, summaries use `summary-<slug>`, full handoffs use `<slug>` directly.
```

- [ ] **Step 5: Update format-reference.md — frontmatter schema type field**

In `references/format-reference.md`, update the frontmatter schema `type` line from:

```yaml
type: <handoff|checkpoint>          # Required: distinguishes file type
```

to:

```yaml
type: <handoff|checkpoint|summary>  # Required: distinguishes file type
```

- [ ] **Step 6: Update format-reference.md — type field description**

Update the **Type field** paragraph from:

```markdown
**Type field:** `handoff` for full handoffs, `checkpoint` for checkpoints. Files without a `type` field are treated as `handoff` for backwards compatibility.
```

to:

```markdown
**Type field:** `handoff` for full handoffs, `checkpoint` for checkpoints, `summary` for summaries. Files without a `type` field are treated as `handoff` for backwards compatibility.
```

- [ ] **Step 7: Add summary section table to format-reference.md**

After the **Checkpoint Quality Calibration** table (end of "Checkpoint Format" section, before the `### Filename Convention` heading), add:

```markdown
## Summary Format

Summaries capture session context at moderate depth and synthesize the project arc across sessions. They use the same frontmatter schema as full handoffs (see above) with `type: summary`.

### Summary Sections

| Section | Required? | Depth | Purpose |
|---------|-----------|-------|---------|
| **Goal** | Yes | 5-10 lines | What we're working on, why, and how it connects to the project |
| **Session Narrative** | Yes | 20-40 lines | What happened, pivots, key understanding shifts — story, not list |
| **Decisions** | Yes | 10-15 lines per decision | Choice, driver, alternatives considered, trade-offs accepted (4 elements) |
| **Changes** | Yes | 5-10 lines per file | Files modified/created with purpose and key details |
| **Codebase Knowledge** | Yes | 20-40 lines | Patterns, architecture, key locations with file:line references |
| **Learnings** | Yes | 5-10 lines per item | Insights gained — gotchas fold in here |
| **Next Steps** | Yes | 5-10 lines per item | What to do next — dependencies, blockers, open questions fold in here |
| **Project Arc** | Yes | 20-50 lines | Where the project stands across sessions — accomplishments, current position, what's ahead, load-bearing decisions, drift risks, downstream impacts |

### Summary Quality Calibration

| Metric | Target |
|--------|--------|
| Body lines | 120-250 |
| Required sections | 8 (all above) |
| Error: under | 120 lines (under-capturing) |
| Warning: over | 250 lines (drifting toward full handoff) |

### Filename Convention

Summary filenames use `summary-` prefix in slug: `YYYY-MM-DD_HH-MM_summary-<slug>.md`
```

- [ ] **Step 8: Update Quality Calibration table in format-reference.md**

Update the existing Quality Calibration table (in the full handoff section) to add a row. The table currently has 3 rows. After the last row, the updated table should be:

```markdown
## Quality Calibration

| Complexity | Target Lines | Characteristics |
|------------|-------------|-----------------|
| All sessions | 400+ | All 13 required sections present with meaningful content |
| Moderate (decisions, exploration) | 500+ | Deep decisions with reasoning chains, learnings with mechanisms, rich context |
| Complex (pivots, design work, discovery) | 500-700+ | All sections fully populated, deep decision analysis with trade-off matrices, architecture maps, conversation highlights with quotes |

A handoff under 400 lines almost certainly has significant information loss. Re-examine the session for: implicit decisions, codebase knowledge gained, conversation dynamics, exploration arc, and files that produced understanding worth preserving.
```

This table specifically covers full handoffs. Summary and checkpoint calibration live in their own sections. No change needed here.

- [ ] **Step 9: Commit**

```bash
git add packages/plugins/handoff/references/handoff-contract.md packages/plugins/handoff/references/format-reference.md
git commit -m "docs(handoff): add summary type to contract and format reference

Update type field, title convention, and filename slug convention.
Add summary section table and quality calibration to format reference."
```

---

### Task 3: Create summary skill

**Files:**
- Create: `packages/plugins/handoff/skills/summary/SKILL.md`

- [ ] **Step 1: Create the skill directory**

```bash
mkdir -p packages/plugins/handoff/skills/summary
```

- [ ] **Step 2: Write the SKILL.md**

Create `packages/plugins/handoff/skills/summary/SKILL.md`:

```markdown
---
name: summary
description: Session summary with project arc context. Use when a full /save is overkill but /quicksave would lose decisions, codebase knowledge, and session narrative. Captures session context at moderate depth (120-250 lines) and synthesizes the project arc across sessions to prevent drift.
allowed-tools: Write, Read, Bash, Glob
---

**Session ID:** ${CLAUDE_SESSION_ID}
**Read [handoff-contract.md](../../references/handoff-contract.md) for:** frontmatter schema, chain protocol, storage conventions.

# Summary

Capture what happened this session and where the project stands. Moderate depth — more than a checkpoint, less than a full handoff.

**Core Promise:** One action to summarize (`/summary`).

## When to Use

- End of a meaningful session where `/save` feels like overkill but `/quicksave` would lose too much
- Session had decisions, exploration, or codebase learning worth preserving at moderate depth
- Working on a multi-session project where arc awareness matters
- User says "summary" or "summarize"

## When NOT to Use

- **Context pressure / need to cycle fast** — use `/quicksave`
- **Complex session with deep decisions, pivots, or design work** — use `/save` (the 8-element decision analysis and full narrative matter)
- **Session was trivial** — skip entirely
- **Resuming from a handoff** — use the `load` skill instead

**Heuristic:** If the session had 3+ significant decisions with trade-offs worth recording in depth, lean toward `/save`. If the session was mostly execution with 0-2 decisions, `/summary` is the right fit.

## Inputs

**Required:**
- Session context (gathered from conversation history)

**Optional:**
- `title` argument for `/summary <title>` — if omitted, Claude generates a descriptive title

**Constraints/Assumptions:**

| Assumption | Required? | Fallback |
|------------|-----------|----------|
| Git repository | No | Omit `branch` and `commit` fields from frontmatter |
| Write access to `<project_root>/docs/handoffs/` | Yes | **STOP** and ask for alternative path. If `docs/handoffs/` doesn't exist, create it with `mkdir -p`. |
| Project root determinable | No | Use current directory; if ambiguous, ask user |

## Outputs

**Artifacts:**
- Markdown file at `<project_root>/docs/handoffs/YYYY-MM-DD_HH-MM_summary-<slug>.md`
- Frontmatter with session metadata
- Body with 8 required sections

**Definition of Done:**

| Check | Expected |
|-------|----------|
| File exists at expected path | `ls` confirms file |
| Frontmatter parses as valid YAML | No YAML syntax errors |
| Required fields present | `date`, `time`, `created_at`, `session_id`, `project`, `title`, `type` all have values |
| Body line count | 120-250 |
| All 8 sections present | Goal, Session Narrative, Decisions, Changes, Codebase Knowledge, Learnings, Next Steps, Project Arc |
| At least 1 of {Decisions, Changes, Learnings} has substantive content | Hollow-summary guardrail |
| Project Arc populated | Contains arc context, not just session context |

## Commands

| Command | Action |
|---------|--------|
| `/summary` | Create summary (Claude generates title) |
| `/summary <title>` | Create summary with specified title |

## Procedure

When user runs `/summary [title]` or confirms an offer:

1. **Check prerequisites:**
   - If session appears trivial (no decisions, changes, or learnings), ask: "This session seems light — create a summary anyway?"
   - If user declines, **STOP**.

2. **Note the session ID** from the "Session ID:" line at the top of this skill (substituted by Claude Code at load time)

3. **Gather arc context:**
   - List files in `<project_root>/docs/handoffs/archive/` — scan titles and dates to identify relevant prior handoffs
   - Read any archived handoffs/checkpoints/summaries that appear relevant to the current project arc. Use judgment — not all archived files may be relevant, especially in repos with multiple workstreams.
   - Check recent git history: `git log --oneline -30` or similar. Look at commit messages for what's been done across sessions.
   - Combine with: conversation context, any loaded handoff from the current session, and general awareness of the project.

4. **Answer the 7 synthesis prompts (INTERNAL — do not output to chat):**

   **Prompt 1 — Goal:** What did I set out to do, and why does it matter?

   **Prompt 2 — Session Narrative:** What happened this session — what was the arc from start to finish? What pivoted? Where did understanding shift?

   **Prompt 3 — Decisions:** What choices were made, and what were the alternatives? For each: the choice, what drove it, what alternatives existed, and what trade-offs were accepted.

   **Prompt 4 — Changes:** What did I build or change? For each file: purpose, approach, key implementation details.

   **Prompt 5 — Codebase Knowledge:** What did I learn about the codebase that future-Claude needs? Patterns, architecture, key locations with file:line references.

   **Prompt 6 — Learnings:** What insights or gotchas should survive this session? What was surprising?

   **Prompt 7 — Project Arc + Next Steps:** Where does the project stand now — what's done, what's next, what's at risk of being forgotten? Did anything we did this session necessitate changes elsewhere — downstream impacts, cascading updates, things that are now out of sync?

   You are not summarizing prior handoffs. You are answering: where does this project stand right now, and what would a new Claude need to know to avoid drift? Prior handoffs and git history are *input* to this synthesis, not the output.

   **IMPORTANT:** The synthesis work is internal reasoning. Do NOT present synthesis answers in chat. Only the final summary file is the deliverable.

5. **Determine output path:**
   - Resolve project root: `$(git rev-parse --show-toplevel)` (falls back to cwd if not in a git repo)
   - If `<project_root>/docs/handoffs/` is not writable, **STOP** and ask for alternative path

6. **Check state file** per chain protocol in [handoff-contract.md](../../references/handoff-contract.md):
   - Read `<project_root>/docs/handoffs/.session-state/handoff-<session_id>` — if exists, set `resumed_from` to its content

7. **Generate markdown** with frontmatter per [handoff-contract.md](../../references/handoff-contract.md):
   - Include `session_id:` with the UUID from step 2
   - Include `type: summary` in frontmatter
   - Title: `"Summary: <descriptive-title>"`
   - Populate frontmatter `files:` from file paths mentioned in Changes and Codebase Knowledge sections

8. **Write file** to `<project_root>/docs/handoffs/YYYY-MM-DD_HH-MM_summary-<slug>.md`

   Summaries are local-only working memory — the file is durable on disk but is not committed. See `references/handoff-contract.md` for the Git Tracking section.

9. **Cleanup state file** per chain protocol in [handoff-contract.md](../../references/handoff-contract.md):
   - `trash` the state file at `<project_root>/docs/handoffs/.session-state/handoff-<session_id>` if it exists. If `trash` fails, warn the user that the state file persists but do not block — the 24-hour TTL will clean it up.

10. **Verify and confirm (brief summary only):**
    - Check file exists and frontmatter is valid
    - Confirm briefly: "Summary saved: `<path>` — <title>"
    - **Do NOT** reproduce summary content or synthesis answers in chat. The file is the deliverable.

## Sections

| Section | Depth Target | Purpose |
|---------|-------------|---------|
| **Goal** | 5-10 lines | What we're working on, why, connection to project |
| **Session Narrative** | 20-40 lines | What happened — story with pivots, not a list of actions |
| **Decisions** | 10-15 lines per decision | Choice, driver, alternatives, trade-offs (4 elements) |
| **Changes** | 5-10 lines per file | Files modified/created with purpose and key details |
| **Codebase Knowledge** | 20-40 lines | Patterns, architecture, key locations with file:line |
| **Learnings** | 5-10 lines per item | Insights, gotchas, surprising discoveries |
| **Next Steps** | 5-10 lines per item | What to do next — includes dependencies, blockers, open questions |
| **Project Arc** | 20-50 lines | Where the project stands across sessions |

### Project Arc Elements

| Element | Description |
|---------|-------------|
| **Accomplishments** | What's been completed across the project arc — not just this session |
| **Current position** | Where we are — what phase, what milestone |
| **What's ahead** | Remaining work, upcoming milestones, known future decisions |
| **Load-bearing decisions** | Key decisions from prior sessions still governing the work |
| **Accumulated understanding** | Mental model, architecture insights, constraints from multiple sessions |
| **Drift risks** | Things easy to forget — subtle constraints, rejected approaches, scope boundaries |
| **Downstream impacts** | Things done this session that necessitate changes elsewhere |

## Verification

After creating summary, verify:

- [ ] File exists at `<project_root>/docs/handoffs/YYYY-MM-DD_HH-MM_summary-<slug>.md`
- [ ] Frontmatter parses as valid YAML
- [ ] Required fields present and non-blank: date, time, created_at, session_id, project, title, type (hook-enforced)
- [ ] All 8 required sections present (hook-enforced)
- [ ] At least 1 of {Decisions, Changes, Learnings} has substantive content (hook-enforced)
- [ ] Body line count 120-250 (hook-enforced)
- [ ] Project Arc contains arc context, not just session context

**Quick check:** Run `ls "$(git rev-parse --show-toplevel)/docs/handoffs/"` and confirm new file appears.

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| Using summary for complex sessions | Loses 8-element decision depth and full narrative | Use `/save` |
| Skipping arc context gathering | Defeats the primary purpose — arc awareness | Always scan archive and git before writing |
| Writing Project Arc as a digest of prior handoffs | Arc is a synthesis of project state, not a handoff summary | Answer "where does the project stand?" not "what happened before?" |
| Exceeding 250 lines | Drifting toward full handoff territory | If content demands it, switch to `/save` |
| Reproducing content in chat | File is the deliverable | Brief confirmation only |
| Full 8-element decision analysis | That's `/save`'s job | 4 elements: choice, driver, alternatives, trade-offs |

## Troubleshooting

### Summary file not created

**Symptoms:** `/summary` completes but no file appears at `<project_root>/docs/handoffs/`

**Likely causes:**
- Permission denied on project `docs/` directory
- Project root couldn't be determined (not in git, ambiguous directory)

**Next steps:**
1. Check if `docs/handoffs/` exists: `ls -la "$(git rev-parse --show-toplevel)/docs/handoffs/"`
2. Check write permissions: `touch "$(git rev-parse --show-toplevel)/docs/handoffs/test" && trash "$(git rev-parse --show-toplevel)/docs/handoffs/test"`
3. If permissions issue, ask user for alternative path

### Summary body exceeds 250 lines

**Symptoms:** Hook warns about line count

**Likely causes:**
- Session was more complex than expected
- Sections exceeded depth targets

**Next steps:**
- This is a warning, not an error — the summary is still valid
- Consider whether this session warranted a full `/save` instead
- If depth is justified, the warning can be accepted

## Related Skills

| Skill | Relationship |
|-------|--------------|
| `save` | For deeper capture: complex sessions, design work, pivots |
| `quicksave` | For lighter capture: context pressure, quick state dump |
| `load` | Complementary: summary creates, load resumes |
```

- [ ] **Step 3: Verify skill file exists and reads cleanly**

```bash
wc -l packages/plugins/handoff/skills/summary/SKILL.md
head -5 packages/plugins/handoff/skills/summary/SKILL.md
```

Expected: ~200 lines, frontmatter starts with `---`.

- [ ] **Step 4: Commit**

```bash
git add packages/plugins/handoff/skills/summary/SKILL.md
git commit -m "feat(handoff): create summary skill

New /summary command for moderate-depth session capture (120-250 lines,
8 sections) with Project Arc section that synthesizes project state
across sessions using archived handoffs and git history."
```

---

### Task 4: Update load skill for summary display

**Files:**
- Modify: `packages/plugins/handoff/skills/load/SKILL.md`

- [ ] **Step 1: Update the display/summarize step**

In `skills/load/SKILL.md`, in step 4 of the Load procedure (line 124), update from:

```markdown
   - Note the type: "Resuming from **checkpoint**: ..." or "Resuming from **handoff**: ..."
```

to:

```markdown
   - Note the type: "Resuming from **checkpoint**: ...", "Resuming from **summary**: ...", or "Resuming from **handoff**: ..."
```

- [ ] **Step 2: Update the verification checklist**

In `skills/load/SKILL.md`, in the Verification section (line 176), update from:

```markdown
- [ ] Type displayed on load ("Resuming from **checkpoint**:" or "Resuming from **handoff**:")
```

to:

```markdown
- [ ] Type displayed on load ("Resuming from **checkpoint**:", "Resuming from **summary**:", or "Resuming from **handoff**:")
```

- [ ] **Step 3: Commit**

```bash
git add packages/plugins/handoff/skills/load/SKILL.md
git commit -m "docs(handoff): add summary type to load skill display strings"
```

---

### Task 5: Update defer skill for summary source_type

**Files:**
- Modify: `packages/plugins/handoff/skills/defer/SKILL.md`

- [ ] **Step 1: Update source_type field**

In `skills/defer/SKILL.md`, update the `source_type` row in the fields table (line 64) from:

```markdown
| `source_type` | One of: `pr-review`, `codex`, `handoff`, `ad-hoc` | Infer from context | Optional — defaults to `ad-hoc` |
```

to:

```markdown
| `source_type` | One of: `pr-review`, `codex`, `handoff`, `summary`, `ad-hoc` | Infer from context | Optional — defaults to `ad-hoc` |
```

- [ ] **Step 2: Commit**

```bash
git add packages/plugins/handoff/skills/defer/SKILL.md
git commit -m "docs(handoff): add summary to defer skill source_type values"
```

---

### Task 6: Version bump and final verification

**Files:**
- Modify: `packages/plugins/handoff/.claude-plugin/plugin.json`

- [ ] **Step 1: Bump plugin version**

In `.claude-plugin/plugin.json`, update version from `"1.5.0"` to `"1.6.0"`.

- [ ] **Step 2: Run full test suite**

```bash
cd packages/plugins/handoff && uv run pytest tests/ -v
```

Expected: All tests pass. No regressions.

- [ ] **Step 3: Verify file structure**

```bash
ls packages/plugins/handoff/skills/summary/SKILL.md
```

Expected: File exists.

- [ ] **Step 4: Commit**

```bash
git add packages/plugins/handoff/.claude-plugin/plugin.json
git commit -m "chore(handoff): bump version to 1.6.0 for summary type"
```

- [ ] **Step 5: Verify all commits on feature branch**

```bash
git log --oneline feature/handoff-summary-type ^main
```

Expected: 6 commits:
1. Design spec
2. quality_check.py + tests
3. Contract and format reference
4. Summary skill
5. Load skill update
6. Defer skill update + version bump (or split)
