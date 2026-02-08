# Run Record: v0-rubric-exact-three-options-007 / baseline / run-3

**Run ID:** 2026-02-06_benchmark-v0_initial

## Metadata

- **scenario_id:** `v0-rubric-exact-three-options-007`
- **condition:** `baseline`
- **replicate:** run-3
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

1. **Lunr.js / Elasticlunr.js with file-watcher pipeline**
   - Strengths: Pure TS/JS ecosystem, battle-tested, zero native dependencies; Elasticlunr adds incremental add/update/remove; serialized index is a single JSON blob
   - Weaknesses: In-memory index (memory concern at 100K+ docs); no fuzzy/typo-tolerant search out of the box with Lunr; Lunr itself lacks native incremental updates (Elasticlunr does)

2. **SQLite with FTS5 via better-sqlite3**
   - Strengths: True incremental updates via SQL INSERT/UPDATE/DELETE; FTS5 supports BM25 ranking, prefix/phrase/boolean queries; handles large corpora (disk-backed); single .db file
   - Weaknesses: Native addon requires compilation step; more complex setup than pure JS; search logic lives in SQL (different paradigm)

3. **MiniSearch** (Recommended)
   - Strengths: Pure JS, zero dependencies, TypeScript types included; native incremental add/remove/discard; built-in fuzzy and prefix search; small footprint (~7KB minified)
   - Weaknesses: In-memory (same scaling ceiling as Lunr); less battle-tested than Lunr or SQLite FTS5; serialization/deserialization less mature than Lunr's

4. **Embedded Tantivy via tantivy-js or custom WASM build**
   - Strengths: Production-grade search quality; fast indexing and querying; true incremental indexing with segment merging
   - Weaknesses: WASM/FFI boundary adds complexity; TypeScript bindings immature; significantly more complex setup/debug/maintain; overkill for internal tool

**Recommendation:** MiniSearch. Reasoning: first-class incremental updates (add/remove/discard), pure TypeScript ecosystem (no native compilation), built-in fuzzy and prefix search, right-sized complexity for internal tool over Markdown corpus. Suggested migration path to SQLite FTS5 if corpus exceeds ~50K documents.

**Additional output elements:** Process explanation (2 steps: understand problem space, identify candidates), per-option trade-off tables with pros/cons, "best for" summaries per option, architecture sketch (chokidar watcher → remark parser → MiniSearch index → JSON serialization → CLI/HTTP interface), process summary section.

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

- **Option count drift:** Runner produced 4 options despite the scenario only asking to "provide options and a recommendation" without specifying a count. This is expected baseline behavior — the scenario deliberately omits count constraints to measure natural drift. Consistent with baseline run-1 (4 options) and run-2 (4 options). All 3 baselines independently converged on 4 options.
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

- **Cross-replicate convergence (N=3 complete):** All 3 baseline replicates independently produced 4 options. This is strong evidence that the natural baseline behavior for this prompt is 4 options, not 3. The target skill (`BENCH_DISCIPLINE_EXACT_THREE_OPTIONS_v0.1.0`) should constrain this to exactly 3 — if it does, the delta is clear and consistent across all replicates.
- **Option roster variation across replicates:**
  - Run-1: Lunr.js, MiniSearch, SQLite FTS5, Flexsearch
  - Run-2: SQLite FTS5, MiniSearch, Meilisearch/Typesense, Custom Inverted Index
  - Run-3: Lunr.js/Elasticlunr, SQLite FTS5, MiniSearch, Tantivy
  - Common across all 3: SQLite FTS5, MiniSearch. Lunr appears in run-1 and run-3.
- **Recommendation variation:** Run-1 recommended MiniSearch; run-2 recommended SQLite FTS5; run-3 recommended MiniSearch. 2/3 converge on MiniSearch.
- **Output style variation:** Run-3 introduced Elasticlunr as a Lunr variant and Tantivy (Rust/WASM) as a novel option not seen in prior baselines. Also included an architecture diagram (ASCII pipeline) not present in run-1 or run-2.
- **Compliance verdict (for blinded scoring reference):** NON-COMPLIANT with "exactly 3 options" criterion (produced 4). Each option has strengths and weaknesses (compliant). Single recommendation provided (compliant).

## Canonical References

1. `docs/simulation-assessment-context-official.md`
2. `docs/frameworks/simulation-effectiveness-benchmark_v0.1.0.md`
3. `docs/benchmarks/suites/benchmark-v0_v0.1.0.md`
4. `docs/benchmarks/target-skills_v0.1.0.md`
5. `docs/benchmarks/control-bodies_v0.1.0.md`
6. `docs/benchmarks/bench-skill-bodies_v0.1.0.md`
