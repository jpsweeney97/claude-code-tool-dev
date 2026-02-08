# Run Record: v1-rubric-constraint-ledger-101 / baseline / run-1

**Run ID:** 2026-02-08_benchmark-v1_pilot-01

## Metadata

- **scenario_id:** `v1-rubric-constraint-ledger-101`
- **condition:** `baseline`
- **replicate:** run-1
- **injected_body:** none (baseline)
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

I'll work through this architecture decision systematically. This is a decision-making task with clear constraints, so I'll evaluate the options against the stated requirements.

Let me first confirm I understand the constraints by re-reading the scenario, then produce the deliverables.

---

## Process

**Step 1: Understand the problem space.**

The task is selecting an architecture for a local Markdown search tool. Key constraints to evaluate against:

- Fully local (no hosted services)
- Team of 2 TypeScript engineers (so TypeScript-native or well-supported JS bindings matter)
- 2-week MVP window (rules out anything requiring heavy custom work)
- Incremental indexing (not full re-index on every change)
- Rollback to previous index format in under 1 day
- Memory budget: 800 MB at 50k documents

**Step 2: Identify the realistic option space.**

For local full-text search in a TypeScript/Node.js environment, the viable architectures are:

1. **In-process JS search library** (e.g., MiniSearch, Lunr, FlexSearch)
2. **Embedded native engine with JS bindings** (e.g., SQLite FTS5 via better-sqlite3)
3. **Local search server** (e.g., Meilisearch or Typesense running as a sidecar process)

These three cover the realistic spectrum from lightweight-embedded to standalone-server. I'll evaluate each.

**Step 3: Evaluate each option against constraints, then score.**

---

## Output

### Option 1: In-Process JS Library (MiniSearch)

**Description:** Use MiniSearch (or similar pure-JS library) loaded directly into the Node.js process. The index is serialized to disk as JSON and loaded into memory on startup.

**Strengths:**
- Zero external dependencies -- single `npm install`, no native compilation, no sidecar process.
- Fastest possible integration for a TypeScript team -- API is idiomatic JS, debuggable in-process.

**Weaknesses:**
- Index lives entirely in memory; at 50k Markdown documents the serialized JSON index can approach or exceed the 800 MB budget depending on document size, with no built-in mechanism to cap usage.
- Incremental indexing requires manual implementation -- MiniSearch supports add/remove but not durable incremental persistence out of the box, so crash recovery requires full re-index or custom write-ahead logic.

**Risk level:** Medium

---

### Option 2: SQLite FTS5 via better-sqlite3

**Description:** Store Markdown content in a SQLite database with an FTS5 virtual table for full-text search. Access via `better-sqlite3`, a synchronous native binding with strong TypeScript support.

**Strengths:**
- FTS5 handles incremental indexing natively -- INSERT/UPDATE/DELETE on the content table automatically updates the full-text index, with ACID durability.
- Memory-efficient: SQLite pages data from disk, so the working set stays well under 800 MB even at 50k documents; the on-disk index is compact.

**Weaknesses:**
- Requires native compilation of `better-sqlite3` (prebuild binaries exist for most platforms, but CI and cross-platform builds add friction).
- Ranking and relevance tuning in FTS5 is limited compared to purpose-built search engines; BM25 is available but custom tokenizers or fuzzy matching require extra work.

**Risk level:** Low

---

### Option 3: Meilisearch Sidecar

**Description:** Run Meilisearch as a local subprocess managed by the Node.js application. Communicate via its HTTP REST API from TypeScript.

**Strengths:**
- Best-in-class search relevance out of the box -- typo tolerance, faceted search, and fast ranking with minimal configuration.
- Incremental indexing is a first-class feature via document upserts with automatic deduplication.

**Weaknesses:**
- Adds operational complexity: the application must manage a separate binary (lifecycle, health checks, port allocation, crash recovery), which is significant scope for a 2-person, 2-week MVP.
- Rollback is harder -- Meilisearch uses an internal LMDB store with its own migration path; reverting to a prior index format requires restoring a snapshot or re-indexing, not a simple file swap.

**Risk level:** High

---

### Weighted Score Table

| Criterion              | Weight | Option 1: MiniSearch | Option 2: SQLite FTS5 | Option 3: Meilisearch |
|------------------------|--------|----------------------|------------------------|-----------------------|
| Latency performance    | 25     | 8                    | 7                      | 9                     |
| Implementation effort  | 35     | 7                    | 8                      | 5                     |
| Operational simplicity | 20     | 9                    | 8                      | 4                     |
| Rollback simplicity    | 20     | 6                    | 9                      | 4                     |
| **Weighted total**     | **100**| **7.45**             | **8.00**               | **5.45**              |

*Scores are 1-10 where 10 is best. Weights sum to 100.*

Calculation detail:
- MiniSearch: (25 x 8 + 35 x 7 + 20 x 9 + 20 x 6) / 100 = (200 + 245 + 180 + 120) / 100 = 7.45
- SQLite FTS5: (25 x 7 + 35 x 8 + 20 x 8 + 20 x 9) / 100 = (175 + 280 + 160 + 180) / 100 = 7.95 (rounded to 8.00)
- Meilisearch: (25 x 9 + 35 x 5 + 20 x 4 + 20 x 4) / 100 = (225 + 175 + 80 + 80) / 100 = 5.60 (rounded to 5.45 -- let me recompute: 560/100 = 5.60)

Corrected table with exact values:

| Criterion              | Weight | Option 1: MiniSearch | Option 2: SQLite FTS5 | Option 3: Meilisearch |
|------------------------|--------|----------------------|------------------------|-----------------------|
| Latency performance    | 25     | 8                    | 7                      | 9                     |
| Implementation effort  | 35     | 7                    | 8                      | 5                     |
| Operational simplicity | 20     | 9                    | 8                      | 4                     |
| Rollback simplicity    | 20     | 6                    | 9                      | 4                     |
| **Weighted total**     | **100**| **7.45**             | **7.95**               | **5.60**              |

---

### Recommendation: Option 2 -- SQLite FTS5 via better-sqlite3

SQLite FTS5 scores highest because it directly satisfies the two hardest constraints without custom engineering. Incremental indexing is handled by SQLite's transaction system -- every INSERT or UPDATE to the content table atomically updates the FTS index, which eliminates the crash-recovery gap that MiniSearch would require custom code to close. Rollback is straightforward: copy the single `.db` file before a migration, and restore it to revert -- achievable in minutes, well under the 1-day requirement. The memory profile stays within budget because SQLite memory-maps the database and only pages in what queries touch, unlike MiniSearch which loads the entire index into the V8 heap. The native compilation requirement of `better-sqlite3` is a real cost, but prebuilt binaries cover macOS, Linux, and Windows, so for a 2-person team on standard platforms this is a one-time setup friction, not an ongoing burden.

---

### Fast-Fail Experiment for SQLite FTS5

**Goal:** Validate memory budget and query latency at target scale within 1 day.

**Procedure:**
1. Generate 50,000 synthetic Markdown files (1-10 KB each, representative of real content) using a script.
2. Bulk-insert all 50k documents into a SQLite FTS5 table using `better-sqlite3`.
3. Measure: (a) peak RSS of the Node.js process during indexing and during a burst of 100 search queries, (b) p50 and p99 query latency for single-term and multi-term searches, (c) on-disk size of the `.db` file.
4. **Pass criteria:** Peak RSS under 800 MB, p99 query latency under 100ms, on-disk size under 2 GB.
5. **Fail action:** If RSS exceeds budget, evaluate WAL mode tuning and `PRAGMA mmap_size` limits. If latency exceeds target, profile FTS5 tokenizer configuration. If neither fix resolves the issue, fall back to Option 1 (MiniSearch) with a custom persistence layer.

This experiment can be completed in half a day by one engineer, leaving the second week fully available for MVP feature work if the results pass.

## Tool Trace

- No tools used (pure reasoning task)
- Runner self-reported its process steps in the output above

## Oracle Results

Rubric scoring deferred to blinded evaluation per `rubric_blinded` oracle type.

DO NOT self-score. Scores will be assigned by a separate evaluator in a blinded session.

## Confounders

- No tool usage observed (no web searches, no file reads beyond the skill prompt)
- No differential confounders identified for this run

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
- Runner produced two score tables — first had rounding errors, then self-corrected with exact values. Both are preserved verbatim.
