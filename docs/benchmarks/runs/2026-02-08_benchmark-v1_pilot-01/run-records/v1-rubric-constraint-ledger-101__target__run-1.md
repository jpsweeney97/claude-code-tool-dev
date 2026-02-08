# Run Record: v1-rubric-constraint-ledger-101 / target / run-1

**Run ID:** 2026-02-08_benchmark-v1_pilot-01

## Metadata

- **scenario_id:** `v1-rubric-constraint-ledger-101`
- **condition:** `target`
- **replicate:** run-1
- **injected_body:** BENCH_DISCIPLINE_CONSTRAINT_LEDGER_v1.0.0
- **oracle_type:** `rubric_blinded`
- **oracle_commands:** N/A (rubric scoring)
- **blinding_required:** yes
- **observability_mode:** Mode A (self-report)
- **allowed_tools_expectation:** no_web
- **skill_file:** `.claude/skills/scenario-constraint-ledger/SKILL.md`
- **invocation_method:** Skill tool (`Skill(skill: "scenario-constraint-ledger")`)

## Preflight

```
$ git diff -- packages/mcp-servers/claude-code-docs/
(empty — clean)
```

## Output

No directly relevant reference materials for this specific architecture decision. This is a pure technical analysis. Let me now produce the complete output following the skill constraints exactly.

---

## Architecture Options for Local Markdown Search Tool

### Option 1: Lunr.js with File-Based Index Persistence

A lightweight, pure-JavaScript full-text search library that builds an inverted index serializable to JSON files on disk. Incremental indexing is achieved by maintaining a document manifest and rebuilding affected index segments on file change detection.

**Strengths:**
1. Zero native dependencies -- installs via npm with no compilation step, meaning both engineers are productive on day one with familiar TypeScript tooling.
2. Serialized index is a single JSON file, making rollback trivial: swap the current index file for a timestamped previous version.

**Weaknesses:**
1. Lunr.js rebuilds the entire index on any mutation (no true incremental update API), so incremental indexing requires a custom sharding or segment strategy that adds implementation effort.
2. In-memory index size scales roughly 3-5x the raw text volume; at 50k documents with moderate content, approaching or exceeding the 800 MB memory budget is a realistic risk.

**Risk level:** med

---

### Option 2: SQLite FTS5 via better-sqlite3

Uses SQLite's built-in FTS5 (Full-Text Search 5) extension accessed through the `better-sqlite3` native Node binding. Documents are stored in an FTS5 virtual table with incremental INSERT/UPDATE/DELETE operations mapping directly to file system changes.

**Strengths:**
1. True incremental indexing out of the box -- single-row INSERT/DELETE operations update the FTS index without rebuilding, directly satisfying the incremental indexing requirement.
2. Memory-efficient by design: SQLite pages data from disk, keeping resident memory well under 800 MB even at 50k documents regardless of content size.

**Weaknesses:**
1. Requires a native binary dependency (`better-sqlite3` compiles a C extension), which introduces build-toolchain friction and potential CI/platform compatibility issues.
2. Rollback to a previous index format requires either restoring a full `.sqlite` database file snapshot or running a migration script -- more complex than swapping a flat file, though achievable within the 1-day window.

**Risk level:** low

---

### Option 3: MiniSearch with Versioned Snapshot Files

MiniSearch is a lightweight, zero-dependency TypeScript-native full-text search library that supports incremental add/remove/update operations on an in-memory index. Index snapshots are persisted as versioned JSON files with a version manifest for rollback.

**Strengths:**
1. Native incremental indexing API (`add`, `remove`, `replace`) eliminates the need for custom sharding -- directly meets the incremental indexing requirement with no workaround.
2. Pure TypeScript with no native dependencies, combined with a simpler API surface than Lunr.js, minimizes implementation effort for a 2-person team within the 2-week window.

**Weaknesses:**
1. Entire index resides in memory; at 50k documents, memory consumption depends heavily on field configuration and tokenization -- could approach the 800 MB ceiling if documents are content-heavy with many indexed fields.
2. Serialization/deserialization of the full in-memory index to disk on every snapshot introduces I/O latency proportional to index size, which may cause noticeable pauses at scale.

**Risk level:** med

---

## Weighted Score Table

Weights: latency performance (20), implementation effort (35), operational simplicity (20), rollback simplicity (25). Weights sum to 100.

| Criterion                | Weight | Option 1: Lunr.js | Option 2: SQLite FTS5 | Option 3: MiniSearch |
|--------------------------|--------|--------------------|------------------------|----------------------|
| Latency performance      | 20     | 6                  | 9                      | 7                    |
| Implementation effort    | 35     | 5                  | 7                      | 9                    |
| Operational simplicity   | 20     | 8                  | 6                      | 8                    |
| Rollback simplicity      | 25     | 9                  | 6                      | 8                    |
| **Weighted total**       | **100**| **6.70**           | **7.10**               | **8.25**             |

Calculation verification:
- Option 1: (20x6 + 35x5 + 20x8 + 25x9) / 100 = (120 + 175 + 160 + 225) / 100 = 6.80
- Option 2: (20x9 + 35x7 + 20x6 + 25x6) / 100 = (180 + 245 + 120 + 150) / 100 = 6.95
- Option 3: (20x7 + 35x9 + 20x8 + 25x8) / 100 = (140 + 315 + 160 + 200) / 100 = 8.15

Corrected table:

| Criterion                | Weight | Option 1: Lunr.js | Option 2: SQLite FTS5 | Option 3: MiniSearch |
|--------------------------|--------|--------------------|------------------------|----------------------|
| Latency performance      | 20     | 6                  | 9                      | 7                    |
| Implementation effort    | 35     | 5                  | 7                      | 9                    |
| Operational simplicity   | 20     | 8                  | 6                      | 8                    |
| Rollback simplicity      | 25     | 9                  | 6                      | 8                    |
| **Weighted total**       | **100**| **6.80**           | **6.95**               | **8.15**             |

---

## Recommendation: Option 3 -- MiniSearch with Versioned Snapshot Files

MiniSearch scores highest (8.15) across the weighted criteria, driven by its dominant advantage in implementation effort -- the heaviest-weighted criterion at 35 points. Its native TypeScript implementation with zero compilation dependencies means both engineers can begin productive work immediately, and its built-in incremental `add`/`remove`/`replace` API eliminates the custom sharding work that Lunr.js would require. Rollback is straightforward: the versioned snapshot approach lets you restore any prior index version by loading a previous JSON file and bumping the manifest pointer. The primary risk -- memory pressure at 50k documents -- is real but manageable through field-level index configuration (indexing titles and headings rather than full body text) and is directly testable before committing to the architecture.

---

## Fast-Fail Experiment for MiniSearch

**Memory budget validation at target scale:** Generate 50,000 synthetic Markdown documents with representative size distribution (median 2 KB, p95 15 KB, max 50 KB), index them with MiniSearch using the planned field configuration, then measure peak RSS (Resident Set Size) via `process.memoryUsage().rss`. If peak RSS exceeds 700 MB (87.5% of the 800 MB budget, leaving headroom for query-time allocations), the architecture fails the constraint and the team should pivot to Option 2 (SQLite FTS5). This experiment requires less than 1 day of engineering effort and should be executed before any other implementation work begins.

---

## Process Report

**Tools used:**
- `Glob`: Searched `docs/references/` for any existing architectural references or patterns relevant to this decision. Found none directly applicable, confirming this is a standalone technical analysis.

**Decisions made:**
1. Weighted implementation effort highest (35) because the 2-week MVP window with only 2 engineers makes development velocity the dominant constraint.
2. Weighted rollback simplicity second (25) because the explicit "under 1 day" rollback requirement is a hard constraint that eliminates architectures with complex migration paths.
3. Weighted latency and operational simplicity equally (20 each) as important but secondary concerns for an MVP.
4. Scored SQLite FTS5 highest on latency (9) because disk-backed paging avoids the memory-bound performance cliffs that in-memory solutions face at scale.
5. Scored MiniSearch highest on implementation effort (9) because its TypeScript-native API with built-in incremental operations requires the least custom code.

**Verification step (per skill instructions):** Confirmed that the recommended option (Option 3, MiniSearch) has the highest weighted score (8.15) in the table. Initial draft had arithmetic errors in the weighted totals; recalculated and corrected before finalizing. The recommendation and the scores are now consistent.

## Tool Trace

- Glob tool: searched `docs/references/` for architectural references (no matches)
- No web searches, no file reads of scenario files
- Runner self-reported verification step checking recommendation-score consistency

## Oracle Results

Rubric scoring deferred to blinded evaluation per `rubric_blinded` oracle type.

DO NOT self-score. Scores will be assigned by a separate evaluator in a blinded session.

## Confounders

- Runner used Glob tool (file search) in target condition; baseline used no tools. This is a minor differential confounder — tool usage was non-informative (no results found) but the act of searching may have affected reasoning time/process.
- Runner changed the weighting scheme (20/35/20/25) vs the prompt's listing order — this is a decision difference, not a confounder.

## Cleanup

```
$ trash /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/scenario-constraint-ledger
(success — directory removed)

$ git checkout -- packages/mcp-servers/claude-code-docs/
(success)

$ git diff -- packages/mcp-servers/claude-code-docs/
(empty — clean)
```

**Confirmation:** Did NOT run `git checkout -- .`.

## Notes

- **Run status:** COMPLETED
- Scaffolded by Codex from pilot matrix.
- Runner self-corrected arithmetic errors in score table (original totals 6.70/7.10/8.25 revised to 6.80/6.95/8.15). Both versions preserved verbatim.
- Runner explicitly performed the verification step from the injected skill body ("verify that your recommended option is the highest-scoring option").
- Injected body matches canonical definition at `docs/benchmarks/bench-skill-bodies_v1.0.0.md` lines 18-34.
