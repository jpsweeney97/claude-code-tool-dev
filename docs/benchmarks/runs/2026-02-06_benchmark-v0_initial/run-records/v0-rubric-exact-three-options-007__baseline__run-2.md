# Run Record: v0-rubric-exact-three-options-007 / baseline / run-2

**Run ID:** 2026-02-06_benchmark-v0_initial

## Metadata

- **scenario_id:** `v0-rubric-exact-three-options-007`
- **condition:** `baseline`
- **replicate:** run-2
- **injected_body:** none
- **oracle_type:** `rubric_blinded`
- **oracle_commands:** N/A (rubric scoring)
- **blinding_required:** yes
- **allowed_tools_expectation:** no_web
- **skill_file:** `.claude/skills/rubric-007-runner/SKILL.md` (temporary; cleaned up after run)
- **invocation:** `Skill(skill: "rubric-007-runner")` → `context: fork` → `assessment-runner`

## Preflight

```
$ git diff -- packages/mcp-servers/claude-code-docs/
(empty — clean start)
```

## Output

Runner produced a structured evaluation of local Markdown search tool options for a TypeScript team. The output included:

**Options presented (4 total — NON-COMPLIANT with "exactly 3" criterion):**

1. **SQLite with FTS5 via `better-sqlite3`** (Recommended)
   - Strengths: Battle-tested FTS5, sub-ms search, native incremental updates (INSERT/UPDATE/DELETE), single-file DB, no external services, extensible with metadata columns
   - Weaknesses: SQLite FTS5 query syntax (not Lucene-style), no fuzzy matching out of the box, requires native addon compilation (though prebuilt binaries exist), no built-in semantic/vector search

2. **Lunr.js / MiniSearch** (pure JavaScript)
   - Strengths: No native compilation, MiniSearch supports add/remove/discard for incremental updates, simple API, good TypeScript types
   - Weaknesses: In-memory index scales poorly past ~10K large docs, must serialize/deserialize entire index on startup, no SQL for complex filtering, serialized index can be 10x-50x raw text size

3. **Embedded Elasticsearch alternative (Meilisearch or Typesense, self-hosted)**
   - Strengths: Best search UX (typo tolerance, faceted filtering, highlighting), designed for incremental updates, sub-ms search, REST API is language-agnostic
   - Weaknesses: Requires separate process (not embedded), more operational complexity, heavier dependency (~50MB binary), overkill for small internal tool

4. **Custom Inverted Index in TypeScript**
   - Strengths: Full control, no dependencies, can be tailored exactly to use case
   - Weaknesses: Substantial engineering effort, must implement tokenization/stemming/ranking/incremental updates manually, likely bugs and performance gaps vs mature libraries

**Recommendation:** SQLite FTS5 via `better-sqlite3`. Reasoning: incremental updates are first-class, scales naturally (millions of rows), operational simplicity (single .db file), good TypeScript ergonomics, extensible via SQL columns. Caveat: no native fuzzy/typo-tolerant search.

**Additional output elements:** Process explanation (2 steps: understand problem space, identify candidates), pro/con tables per option, SQL schema sketch for FTS5 virtual table, TypeScript code sketch for upsert, summary comparison table (7 criteria × 4 options).

## Tool Trace

- No tools used by runner (knowledge-only task)
- No web search attempted
- No files under `docs/benchmarks/runs/` read by runner
- Runner used only internal knowledge to evaluate search library options

## Oracle Results

Rubric scoring deferred to blinded evaluation per `docs/benchmarks/suites/benchmark-v0_v0.1.0.md` Section "Blinding Policy."

### Blinding Record

- **Evaluator:** TBD (separate session or human — must not be this session)
- **A/B randomization method:** TBD (assigned during blinded eval)
- **Unmasking timing:** TBD (must be after scoring)

## Confounders

- **Option count drift:** Runner produced 4 options despite the scenario only asking to "provide options and a recommendation" without specifying a count. This is expected baseline behavior — the scenario deliberately omits count constraints to measure natural drift. Consistent with baseline run-1 which also produced 4 options.
- **Always-loaded rules files:** The runner had access to always-loaded project rules (methodology, git workflow, etc.) that are part of the standard Claude Code environment. These are not benchmark-specific and are present in all conditions equally.

## Cleanup

```
$ trash /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/rubric-007-runner
(success — no output)

$ git checkout -- packages/mcp-servers/claude-code-docs/
(success — no output)

$ git diff -- packages/mcp-servers/claude-code-docs/
(empty — clean state confirmed)
```

**Explicit confirmation:** Did NOT run `git checkout -- .` (only ran targeted checkout on `packages/mcp-servers/claude-code-docs/`).

## Notes

- **Cross-replicate pattern (run-1 → run-2):** Both baseline replicates independently produced 4 options. Run-1 chose Lunr.js, MiniSearch, SQLite FTS5, and Flexsearch. Run-2 chose SQLite FTS5, MiniSearch, Meilisearch/Typesense, and Custom Inverted Index. The option rosters overlap (SQLite FTS5 and MiniSearch appear in both) but are not identical, showing natural variation in option selection while converging on the same count (4).
- **Recommendation divergence:** Run-1 recommended MiniSearch; run-2 recommended SQLite FTS5. Both are reasonable for the constraints — this variation is expected and healthy for baseline measurement.
- **Output quality:** Run-2 produced more structured output than run-1 (pro/con tables, SQL schema sketch, TypeScript code sketch, 7-criterion comparison table). This is natural variation in output elaboration level.
- **Compliance verdict (for blinded scoring reference):** NON-COMPLIANT with "exactly 3 options" criterion (produced 4). Each option has strengths and weaknesses (compliant). Single recommendation provided (compliant).

## Canonical References

1. `docs/simulation-assessment-context-official.md`
2. `docs/frameworks/simulation-effectiveness-benchmark_v0.1.0.md`
3. `docs/benchmarks/suites/benchmark-v0_v0.1.0.md`
4. `docs/benchmarks/target-skills_v0.1.0.md`
5. `docs/benchmarks/control-bodies_v0.1.0.md`
6. `docs/benchmarks/bench-skill-bodies_v0.1.0.md`
