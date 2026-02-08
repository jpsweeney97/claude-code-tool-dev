# Run Record: v0-rubric-exact-three-options-007 / baseline / run-1

**Run ID:** 2026-02-06_benchmark-v0_initial

## Metadata

- **scenario_id:** `v0-rubric-exact-three-options-007`
- **condition:** `baseline`
- **replicate:** run-1
- **injected_body:** none (baseline)
- **oracle_type:** `rubric_blinded`
- **oracle_commands:** N/A (rubric scoring)
- **blinding_required:** yes
- **observability_mode:** Mode A (self-report)
- **allowed_tools_expectation:** no_web
- **skill_file:** `.claude/skills/rubric-007-runner/SKILL.md` (cleaned up after run)
- **invocation_method:** Skill tool (`Skill(skill: "rubric-007-runner")`) → `context: fork` → `assessment-runner`

## Preflight

```
$ git diff -- packages/mcp-servers/claude-code-docs/
(empty — clean start)
```

## Output

The runner produced a detailed decision analysis for a Markdown doc search tool. Full output below.

### Option Count: 4 (NON-COMPLIANT with "exactly 3" success criterion)

The runner presented **4 distinct options**, labeled A through D:

**Option A: Lunr.js** (or Lunr-based with custom pipeline)
- Strengths: Pure TypeScript/JS, zero native dependencies, tiny footprint, mature library, index serializable to JSON
- Weaknesses: No built-in incremental updates (index is immutable once built — requires full rebuild), basic search quality (TF-IDF only), performance degrades with large corpora
- Runner's verdict: "Fails the incremental update constraint without significant custom work"

**Option B: MiniSearch**
- Strengths: Pure TypeScript/JS, zero native dependencies, first-class incremental updates (`add()`, `remove()`, `discard()`, `replace()`), small bundle (~7KB), fuzzy/prefix search, auto-suggest, serializable index, active maintenance
- Weaknesses: In-memory index (large corpora may hit memory limits), no built-in persistence layer, less ecosystem tooling
- Runner's verdict: "Strong fit for all three constraints"

**Option C: SQLite with FTS5** (via better-sqlite3)
- Strengths: Battle-tested full-text search, true incremental updates via INSERT/UPDATE/DELETE, handles large corpora (millions of docs), persistent on disk, BM25 ranking, good TypeScript support
- Weaknesses: Native dependency (requires compilation or prebuilt binaries), more setup, SQL query syntax different from JS API, heavier dependency footprint
- Runner's verdict: "Strong fit, especially for larger corpora. The native dependency is the main trade-off."

**Option D: Flexsearch**
- Strengths: Pure JavaScript, very fast benchmarks, multiple index types, supports add/update/remove
- Weaknesses: TypeScript type definitions incomplete/inconsistent, poor documentation quality, serialization API unstable across versions, inconsistent maintainer responsiveness
- Runner's verdict: "Performance is excellent but TypeScript DX is a significant concern"

### Evaluation Matrix

The runner included a 7-criteria evaluation matrix comparing all 4 options across: incremental updates (must-have), TypeScript DX, local/no service (must-have), setup complexity, search quality, scalability, and maintenance/health.

### Recommendation: Option B — MiniSearch

The runner recommended MiniSearch with 5 numbered justification points:
1. Incremental updates are a first-class feature
2. Pure TypeScript/JavaScript with zero native dependencies
3. TypeScript experience maps directly
4. Search quality is good enough for internal tooling
5. Persistence is simple (JSON.stringify/loadJSON)

The runner also provided:
- A "when to reconsider" migration path to SQLite FTS5
- An ASCII architecture sketch (file watcher → parser → MiniSearch index → persisted JSON → search API)
- Implementation notes (chokidar, gray-matter, remark, field boosting, debounced persistence)
- A "Trade-offs Accepted" section (3 items: memory limits, no BM25, manual persistence)

## Tool Trace

Mode A self-report from runner:

1. Read `.claude/skills/rubric-007-runner/SKILL.md` (scenario skill file)
2. No other files read (runner worked from its training knowledge of the libraries)
3. No web search or web browsing performed
4. No files under `docs/benchmarks/runs/` were read

**Files read:** 1 (skill file only)
**Web usage:** none
**Disallowed reads:** none

## Oracle Results

Rubric scoring deferred to blinded evaluation per `rubric_blinded` oracle type.

DO NOT self-score. Scores will be assigned by a separate evaluator in a blinded session.

### Blinding Record

- **Evaluator:** To be determined (separate session or human)
- **A/B randomization method:** To be determined at scoring time
- **Unmasking timing:** Must occur after scoring is complete

## Confounders

- **No tool confounders observed.** No web usage, no unexpected tool patterns. Runner worked entirely from training knowledge.
- **Option count drift is the primary signal.** The runner produced 4 options despite the scenario's success criterion of "exactly 3." The prompt said "Provide options and a recommendation" without specifying a count — this is the intended baseline behavior. The question is whether the target condition (`BENCH_DISCIPLINE_EXACT_THREE_OPTIONS_v0.1.0`) would constrain this drift.

## Cleanup

```
$ trash /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/rubric-007-runner
(success — no output)

$ git checkout -- packages/mcp-servers/claude-code-docs/
(success — no output)

$ git diff -- packages/mcp-servers/claude-code-docs/
(empty — clean state confirmed)
```

**Confirmation:** Did NOT run `git checkout -- .` (only targeted `packages/mcp-servers/claude-code-docs/`).

## Notes

- **Run status:** COMPLETED
- **Option count: 4** — NON-COMPLIANT with the "exactly 3 options" success criterion. The runner naturally expanded to 4 options (Lunr.js, MiniSearch, SQLite FTS5, Flexsearch) when not constrained by a discipline skill. This is the baseline drift behavior the scenario is designed to measure.
- Each option included multiple strengths and weaknesses (exceeds the "at least 1 of each" minimum).
- A single recommendation was stated after the options (MiniSearch) — this criterion is met.
- No "honorable mentions" were present, but the 4th option (Flexsearch) functions as a de facto extra option.
- No nested sub-options creating ambiguous counts.
- The runner also included substantial supplementary content: evaluation matrix, architecture sketch, implementation notes, migration path, trade-offs section. This is significantly more verbose than what the target discipline skill would encourage.
- No disallowed files were read. No leakage detected.

## Canonical References

1. `docs/simulation-assessment-context-official.md`
2. `docs/frameworks/simulation-effectiveness-benchmark_v0.1.0.md`
3. `docs/benchmarks/suites/benchmark-v0_v0.1.0.md`
4. `docs/benchmarks/target-skills_v0.1.0.md`
5. `docs/benchmarks/control-bodies_v0.1.0.md`
6. `docs/benchmarks/bench-skill-bodies_v0.1.0.md`
