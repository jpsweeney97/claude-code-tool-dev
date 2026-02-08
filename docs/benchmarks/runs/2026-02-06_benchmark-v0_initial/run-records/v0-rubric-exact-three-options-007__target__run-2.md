# Run Record: v0-rubric-exact-three-options-007 / target / run-2

**Run ID:** 2026-02-06_benchmark-v0_initial

## Metadata

- **scenario_id:** `v0-rubric-exact-three-options-007`
- **condition:** `target`
- **replicate:** `run-2`
- **injected_body:** `BENCH_DISCIPLINE_EXACT_THREE_OPTIONS_v0.1.0` (`docs/benchmarks/bench-skill-bodies_v0.1.0.md`)
- **oracle_type:** `rubric_blinded`
- **oracle_commands:** N/A (rubric scoring)
- **blinding_required:** yes
- **observability_mode:** A (self-report)
- **invocation_mechanism:** Skill tool (`Skill(skill: "scenario-search-tooling-kfn")`)
- **skill_file:** `.claude/skills/scenario-search-tooling-kfn/SKILL.md`

### Canonical References

- Framework: `docs/frameworks/simulation-effectiveness-benchmark_v0.1.0.md`
- Suite matrix: `docs/benchmarks/suites/benchmark-v0_v0.1.0.md`
- Bench skill bodies: `docs/benchmarks/bench-skill-bodies_v0.1.0.md`
- Target roster: `docs/benchmarks/target-skills_v0.1.0.md`
- Control bodies: `docs/benchmarks/control-bodies_v0.1.0.md`
- Official context: `docs/simulation-assessment-context-official.md`

## Preflight

```bash
$ git diff -- packages/mcp-servers/claude-code-docs/
# (empty — clean start confirmed)
```

## Output

The runner produced three options with strengths/weaknesses and a recommendation, following the injected discipline skill. Full raw output below.

---

**Process section (runner self-report):**

The runner restated constraints (Markdown ingestion, fast search, TypeScript team, local-only, incremental updates), then evaluated the landscape along axes of full-text search quality, incremental update support, operational simplicity, and TypeScript ecosystem fit. Narrowed to three distinct approaches.

**Option 1: MiniSearch (Pure JS In-Process Library)**

- Strengths: Native TypeScript/JavaScript with no FFI or binary dependencies; extremely simple to embed (`npm install minisearch`); supports `add`, `remove`, and `replace` on individual documents for incremental updates.
- Weaknesses: Entire index lives in memory (won't scale to very large corpora); search quality is basic TF-IDF with limited fuzzy/typo tolerance.

**Option 2: Orama (TypeScript-Native Search Engine)**

- Strengths: Written in TypeScript from the ground up with first-class type safety; richer feature set than MiniSearch (schema validation, faceted search, filters, stemming); supports insert/update/remove for incremental updates.
- Weaknesses: Heavier than MiniSearch with more abstractions; also in-memory with persistence requiring full serialization; smaller community with documentation gaps for advanced use cases.

**Option 3: SQLite FTS5 via better-sqlite3**

- Strengths: Truly incremental (INSERT/UPDATE/DELETE are durable immediately); handles much larger document sets via disk-backed index; BM25 ranking out of the box with column filters, prefix queries, and phrase matching.
- Weaknesses: Native Node addon requiring C compiler at install time; API is SQL strings rather than typed methods; more operational surface (`.db` file, migrations, WAL mode, vacuuming).

**Recommendation: Option 2 (Orama)**

Runner's reasoning (quoted): "The team's strong TypeScript experience makes Orama's TypeScript-native API a natural fit -- they get full type safety with zero impedance mismatch. It handles incremental updates cleanly via insert/update/remove, and its richer feature set (stemming, facets, filters) provides room to grow without switching tools. For a small internal tool ingesting Markdown docs, the in-memory constraint is not a practical concern, and the operational simplicity of 'no native dependencies, no sidecar, no database file' outweighs the marginal scalability advantage of SQLite FTS5."

---

## Tool Trace

**Mode A (self-report):** Zero tool usage. The runner produced its entire response from reasoning alone, with no file reads, web searches, or other tool invocations.

## Oracle Results

**Scoring mode: `rubric_blinded` — DO NOT self-score.**

Scoring deferred to blinded evaluator per `rubric_blinded` protocol.

### Blinding Record

- **Evaluator:** Deferred (requires separate session or human)
- **A/B randomization method:** Deferred (to be determined at scoring time)
- **Unmasking timing:** Deferred (must occur after scoring)

## Confounders

- **Tool usage:** Zero tools in this target run (matches baseline pattern of zero tool usage). No differential tool confounder.
- **Naming bias:** Skill name `scenario-search-tooling-kfn` is neutral (no condition labels). Description: "Scenario run for search tooling — rubric assessment". No bias detected.
- **Novel option (Orama):** This run introduced Orama as Option 2, which did not appear in baselines or in target run-1. Orama was also the recommendation. This is a new entrant in the option set and represents between-run variance in option selection.

## Cleanup

```bash
$ trash .claude/skills/scenario-search-tooling-kfn
# (skill directory removed)

$ git checkout -- packages/mcp-servers/claude-code-docs/
# (scoped revert — NOT git checkout -- .)

$ git diff -- packages/mcp-servers/claude-code-docs/
# (empty — clean confirmed)
```

## Notes

- **Structural compliance:** Exactly 3 named options, each with multiple strengths and weaknesses, followed by a single recommendation with a 4-sentence justification. No "honorable mentions" or 4th option. The injected discipline skill was followed.
- **Recommendation target:** Orama (Option 2). This differs from target run-1 (SQLite FTS5) and from the majority of baselines (MiniSearch). Three different recommendations across three conditions so far.
- **New option entrant:** Orama (formerly Lyra) appeared for the first time in this run. Baselines and target run-1 used {MiniSearch, Lunr.js, SQLite FTS5}. This run replaced Lunr.js with Orama. The option set variance continues to be high.
- **Quality observations:** Each option has 3 strengths and 2 weaknesses. The runner included a "constraints recap" section before the process section. Recommendation reasoning explicitly contrasts Orama against both alternatives. No recommendation contradiction.
