# Handoff Enhancement #2: Knowledge Graduation

```yaml
id: handoff-distill
date: 2026-02-24
status: closed
priority: medium
blocked_by: []
blocks: []
related: [handoff-search]
plugin: packages/plugins/handoff/
```

## Problem

Handoffs have 30-day active / 90-day archive retention. But decisions, architecture understanding, and patterns are durable knowledge that outlives any session chain. Today this knowledge gets permanently deleted when handoffs age past retention.

The `/learn` system and `MEMORY.md` exist for persistent knowledge — but are completely disconnected from the handoff system. No extraction path exists.

**Evidence:**
- 90-day archive retention means all knowledge in handoffs from before ~Nov 2025 is gone
- Handoffs contain structured Decisions, Learnings, and Codebase Knowledge sections with durable insights
- `/learn` Phase 0 exists (`docs/learnings/learnings.md`, 19 entries) but is populated manually, not from handoffs
- No overlap between handoff sections and learning entries — these are separate knowledge silos

**Cost:**
- Permanent loss of decisions and their rationale after retention expires
- Manual duplicate effort to capture the same insight in both a handoff and a learning
- Learnings file misses insights that were captured in handoffs but never promoted

## Scope

**In scope:**
- Extract durable knowledge from a specific handoff or most recent handoff
- Format as Phase 0 learning entries (`### YYYY-MM-DD [tags]` + paragraph)
- Append to `docs/learnings/learnings.md` with user confirmation
- Identify which sections contain durable knowledge (Decisions, Learnings, Patterns)

**Out of scope:**
- Automatic extraction (always user-triggered)
- Structured episodes (Phase 1+ of cross-model learning system)
- Cross-project knowledge transfer
- Modifying the handoff after extraction
- Replacing `/learn` — this complements it

## Design Space

Resolved via Codex dialogue (2026-02-27, 5 turns, collaborative) + 4 review passes (55 amendments).

1. **Invocation**: `/distill [path]` — standalone skill. Not integrated with `/learn` (different purpose: `/learn` captures ad-hoc insights, `/distill` extracts structured knowledge from handoffs).
2. **Selection**: Most recent handoff (default) or specific path. No batch mode in V1.
3. **What to extract**: Decisions, Learnings, Codebase Knowledge, Gotchas by default. `--include-section Context` opt-in for additional sections.
4. **Format mapping**: Section-specific field extraction (Choice/Driver/Confidence for Decisions, Mechanism/Evidence/Implication for Learnings). Durability hints for Codebase Knowledge (keyword heuristic). Synthesized into 6-8 sentence Phase 0 paragraphs.
5. **Deduplication**: Three layers — exact source (SHA-256 of session_id + section + heading), exact content (SHA-256 of normalized text), semantic (Claude comparison against existing entries). 4-state matrix: NEW, EXACT_DUP_SOURCE, EXACT_DUP_CONTENT, UPDATED_SOURCE. No-autodrop invariant: all candidates returned, status is a label not a filter.
6. **Confirmation UX**: Always confirm. Status-specific options: NEW → append/skip, UPDATED_SOURCE → replace/keep both/skip, LIKELY_DUPLICATE → merge/replace/keep both/skip. Terminal states (EXACT_DUP_SOURCE, EXACT_DUP_CONTENT) auto-skip.
7. **Archive-time trigger**: Deferred. V1 is user-triggered only.

## Files Affected

| File | Change |
|------|--------|
| `scripts/handoff_parsing.py` | **New** — shared parsing module (Section, HandoffFile, parse_frontmatter, parse_sections, parse_handoff) |
| `scripts/project_paths.py` | **New** — shared path utilities (get_project_name, get_handoffs_dir) |
| `scripts/distill.py` | **New** — extraction pipeline (subsection parser, provenance, dedup, signal extraction, CLI) |
| `scripts/search.py` | **Modified** — migrated to shared modules, re-exports for backward compat |
| `skills/distill/SKILL.md` | **New** — distill skill (synthesis, semantic dedup, confirmation UX) |
| `tests/test_handoff_parsing.py` | **New** — 13 tests |
| `tests/test_project_paths.py` | **New** — 3 tests |
| `tests/test_distill.py` | **New** — 64 tests |
| `tests/test_search.py` | **Modified** — 3 new tests (re-export, fence regression) |
| `.claude-plugin/plugin.json` | Version bump 1.3.0 → 1.4.0 |
| `pyproject.toml` | Version bump 1.3.0 → 1.4.0 |
| `README.md` | Added /distill section |

## Acceptance Criteria

- [x] `/distill` extracts durable knowledge from a handoff
- [x] Produces Phase 0 format learning entries with distill-meta provenance
- [x] Shows proposed entries to user before appending (no-autodrop invariant)
- [x] Appends confirmed entries to `docs/learnings/learnings.md`
- [x] Does not modify the source handoff
- [x] Handles handoffs with no extractable knowledge gracefully
- [x] Three-layer deduplication (exact source, exact content, semantic)
- [x] 83 new tests (64 distill + 16 handoff_parsing + 3 project_paths), 212 total
