# Run Record: v0-rubric-exact-three-options-007 / target / run-1

**Run ID:** 2026-02-06_benchmark-v0_initial

## Metadata

- **scenario_id:** `v0-rubric-exact-three-options-007`
- **condition:** `target`
- **replicate:** `run-1`
- **injected_body:** `BENCH_DISCIPLINE_EXACT_THREE_OPTIONS_v0.1.0` (`docs/benchmarks/bench-skill-bodies_v0.1.0.md`)
- **oracle_type:** `rubric_blinded`
- **oracle_commands:** N/A (rubric scoring)
- **blinding_required:** yes
- **observability_mode:** A (self-report)
- **invocation_mechanism:** Skill tool (`Skill(skill: "scenario-search-tooling-rto")`)
- **skill_file:** `.claude/skills/scenario-search-tooling-rto/SKILL.md`

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

The runner stated it considered the constraints (TypeScript, local-only, incremental updates), evaluated full-text search engines, embedded vector databases, and lightweight in-process libraries, excluded managed services, and narrowed to three distinct architectural approaches.

**Option 1: MiniSearch (In-Process JS Library)**

- Strengths: Native TypeScript support with excellent type definitions; tiny footprint (~7KB gzipped); supports incremental add/remove/update without full rebuild; simple API with minimal learning curve.
- Weaknesses: Index lives in memory (memory pressure at 100K+ docs); no built-in persistence (must serialize/deserialize manually); basic BM25-style matching without semantic understanding.

**Option 2: Lunr.js + Custom Incremental Layer**

- Strengths: Battle-tested library with large ecosystem; compact serializable indexes; strong TF-IDF relevance scoring with field boosting and wildcard support.
- Weaknesses: Immutable indexes by design — incremental updates require custom segmented-index strategy adding complexity; the incremental layer is non-trivial to maintain; TypeScript typings are community-maintained, not first-party.

**Option 3: SQLite FTS5 via better-sqlite3**

- Strengths: True incremental updates are native (INSERT/UPDATE/DELETE); persistent to disk by default with instant startup; handles large corpora (millions of rows) with low memory; mature query syntax.
- Weaknesses: Requires native binary compilation; SQL-based API rather than search-native TypeScript API; FTS5 tokenization/ranking less configurable than purpose-built search libraries.

**Recommendation: Option 3 (SQLite FTS5 via better-sqlite3)**

Runner's reasoning (quoted): "The decisive factor is the incremental update requirement combined with local operation. MiniSearch handles incremental updates well but lacks persistence, meaning you pay a full deserialization cost on every startup and carry the entire index in memory. Lunr requires building a custom incremental layer, which is significant undifferentiated work. SQLite FTS5 gives you incremental updates, persistence, and scalability as built-in properties of the storage engine rather than things you bolt on. The native binary dependency is a real cost, but for an internal tool (not a distributed package), it is a one-time setup issue that a TypeScript-experienced team can absorb easily."

---

## Tool Trace

**Mode A (self-report):** Zero tool usage. The runner produced its entire response from reasoning alone, with no file reads, web searches, or other tool invocations.

## Oracle Results

**Scoring mode: `rubric_blinded` — DO NOT self-score.**

### Blinding Record

- **Evaluator:** Deferred (requires separate session or human)
- **A/B randomization method:** Deferred (to be determined at scoring time)
- **Unmasking timing:** Deferred (must occur after scoring)

## Confounders

- **Tool usage:** Zero tools in both baseline (from handoff notes) and this target run. No differential tool confounder.
- **Naming bias:** Skill name `scenario-search-tooling-rto` is neutral (no condition labels). Description: "Scenario run for search tooling — rubric assessment". No bias detected.
- **Option overlap with baselines:** All three baseline runs also selected MiniSearch, Lunr.js, and SQLite FTS5 as their option sets (per handoff context, not from reading run records). This target run produced the same three options. The convergence may reflect scenario constraints naturally funneling toward these options rather than a skill effect.

## Cleanup

```bash
$ trash .claude/skills/scenario-search-tooling-rto
# (skill directory removed)

$ git checkout -- packages/mcp-servers/claude-code-docs/
# (scoped revert)

$ git diff -- packages/mcp-servers/claude-code-docs/
# (empty — clean confirmed)
```

## Notes

- **Structural compliance:** The output contains exactly 3 named options, each with multiple strengths and weaknesses, followed by a single recommendation with a 4-sentence justification. No "honorable mentions" or 4th option. The injected discipline skill appears to have been followed.
- **Recommendation target:** SQLite FTS5 (Option 3). This differs from the majority of baselines which recommended MiniSearch. This divergence may be signal or noise — to be evaluated by blinded scorer.
- **Quality observations:** Each option has 3-4 strengths and 2-3 weaknesses (exceeds the "at least 1" minimum). The recommendation reasoning explicitly addresses why each alternative was not chosen, not just why the winner was chosen. No recommendation contradiction (unlike baseline run-3).
- **Comparison to baseline pattern (from handoff, not from reading records):** Baselines recommended MiniSearch in most runs; this target run recommends SQLite FTS5. Baselines had high variance in labeling and structural extras; this run uses consistent heading/bullet structure throughout.
