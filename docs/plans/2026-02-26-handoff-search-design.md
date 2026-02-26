# Handoff Search/Query Design

```yaml
date: 2026-02-26
status: approved
enhancement: "#1 Search/Query"
ticket: docs/tickets/handoff-search.md
plugin: packages/plugins/handoff/
```

## Overview

Add `/handoff:search <query>` to search across handoff history for decisions, learnings, and context. Hybrid architecture: Python script for search + section extraction, skill for invocation and presentation.

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Search depth | Section-aware | Return full `##` sections, not just context lines. Decisions and learnings make more sense as complete blocks. |
| Implementation | Markdown parser (pure Python) | Corpus is small (~75k lines). Clean section tree is the right abstraction. Foundation for Enhancement #2 (distill). |
| Result limits | Show all, Claude summarizes | No artificial cap. Skill handles presentation: full display for ≤5, table + top 3 for 6+. |
| Search scope | Always both (active + archived) | No flags. Simplest UX — search everything. |
| Invocation | Hybrid (script + skill) | Script handles deterministic search/parsing. Skill handles presentation. Testable + flexible. |
| Shared code | Extract to `lib/project.py` | `get_project_name()` and `get_handoffs_dir()` used by both `cleanup.py` and `search.py`. Enhancement #2 will also need them. |

## Architecture

```
/handoff:search <query>
        │
        ▼
┌─────────────────────┐
│  Skill (SKILL.md)   │  Invocation + presentation
│  ~60-80 lines       │
└────────┬────────────┘
         │ Bash: uv run scripts/search.py "<query>"
         ▼
┌─────────────────────┐
│  scripts/search.py  │  Parse markdown → search sections → JSON output
│  ~120-150 lines     │
└────────┬────────────┘
         │ imports
         ▼
┌─────────────────────┐
│  lib/project.py     │  get_project_name(), get_handoffs_dir()
│  ~40 lines          │
└─────────────────────┘
```

## Search Script (`scripts/search.py`)

### Input

```bash
uv run scripts/search.py <query> [--regex]
```

- `<query>` — text string or regex pattern
- `--regex` — treat query as regex (default: literal case-insensitive match)

### File Discovery

- Walks `~/.claude/handoffs/<project>/*.md` (active)
- Walks `~/.claude/handoffs/<project>/.archive/*.md` (archived)
- Project name from `lib.project.get_project_name()`

### Parsing Model

```
HandoffFile
  ├── path: str
  ├── frontmatter: dict (title, date, type, branch, commit)
  └── sections: list[Section]
        ├── heading: str ("## Decisions")
        ├── level: int (2)
        ├── content: str (full section text including subsections)
        └── line_start: int
```

Parser splits on `## ` boundaries. Each section includes everything from its `## ` heading until the next `## ` heading (or EOF). `### ` subsections are included within their parent `## ` section.

### Search Logic

1. For each file: parse frontmatter + sections
2. For each section: check if query matches anywhere in `heading + content`
3. If match: include the full section in results

### Output (JSON to stdout)

```json
{
  "query": "merge strategy",
  "total_matches": 3,
  "results": [
    {
      "file": "2026-02-25_22-34_pr26-reviewed-merged.md",
      "title": "PR #26 reviewed, merged",
      "date": "2026-02-25",
      "type": "handoff",
      "archived": true,
      "section_heading": "## Decisions",
      "section_content": "### Regular merge over squash merge for PR #26\n\n**Choice:** Regular merge..."
    }
  ]
}
```

Results sorted by date descending (most recent first).

### Error Handling

| Condition | Behavior |
|-----------|----------|
| No handoffs directory | `{"query": "...", "total_matches": 0, "results": [], "error": null}` |
| Invalid regex | `{"error": "Invalid regex: ..."}` |
| File read error | Skip file, continue |

## Skill (`skills/searching-handoffs/SKILL.md`)

### Frontmatter

```yaml
name: searching-handoffs
description: Search across handoff history for decisions, learnings, and context. Use when user says "search handoffs", "find in handoffs", "what did we decide about", or runs /handoff:search.
argument-hint: "<query> [--regex]"
```

### Behavior

1. Receive query from user argument
2. Run `uv run scripts/search.py "<query>"` via Bash
3. Parse JSON output
4. Present results:
   - **0 results:** "No handoffs matched `<query>`."
   - **1-5 results:** Show each with file date, title, and full section content
   - **6+ results:** Table of all matches (file, date, section heading), then 3 most recent in full. Offer: "Want to see the rest?"

### Context Budget

Under 80 lines. Thin wrapper: run script, format results. No search logic in the skill.

## Shared Module (`lib/project.py`)

Extract from `cleanup.py`:
- `get_project_name() -> str` — git root dir name or cwd fallback
- `get_handoffs_dir() -> Path` — `~/.claude/handoffs/<project>/`

## File Changes

### New Files

| File | Purpose | Est. Lines |
|------|---------|------------|
| `lib/__init__.py` | Package init | 0 |
| `lib/project.py` | Shared project utilities | ~40 |
| `scripts/search.py` | Search script | ~120-150 |
| `skills/searching-handoffs/SKILL.md` | Skill wrapper | ~60-80 |
| `tests/test_search.py` | Search tests | ~200-250 |

### Modified Files

| File | Change |
|------|--------|
| `scripts/cleanup.py` | Import `get_project_name`, `get_handoffs_dir` from `lib.project` |
| `tests/test_cleanup.py` | Update mock paths to `lib.project.*` |
| `.claude-plugin/plugin.json` | Version bump to 1.2.0 |

## Testing

### Parser Tests

- Frontmatter extraction (title, date, type)
- `##` section splitting with subsections included
- File with no sections (frontmatter only)
- File with no frontmatter

### Search Tests

- Literal match (case-insensitive)
- Regex match
- No matches → empty results
- Match in section heading
- Multiple matches across files → sorted by date descending
- Multiple sections match in same file → both returned
- Invalid regex → error in JSON

### Integration Tests

- End-to-end: temp handoff files → search → verify JSON
- File discovery: finds both active and `.archive/` files
- Skips non-`.md` files
- Missing handoffs directory → graceful empty result

### Test Strategy

All tests use `tmp_path` with synthetic handoff files. No dependency on real handoff data. Reuse `get_project_name` patching pattern from `test_cleanup.py`.
