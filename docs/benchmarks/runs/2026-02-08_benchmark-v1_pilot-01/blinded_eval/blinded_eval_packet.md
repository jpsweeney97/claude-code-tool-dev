# Blinded Evaluation Packet — Benchmark v1 Pilot

**Run ID:** `2026-02-08_benchmark-v1_pilot-01`

**Status:** READY FOR EVALUATION

**Instructions for evaluator:**
- Score each candidate output against the rubric dimensions (0-4 scale per dimension).
- Do NOT attempt to determine which candidate is which condition.
- Score independently: finish all scoring for one scenario before moving to the next.
- All candidate labels (A/B) are randomized and condition-free.
- The rubric and scale anchors are provided in each scenario section.

**Scale anchors (all scenarios):**

| Score | Meaning |
|---|---|
| 0 | Missing or incorrect; directly violates requirement |
| 1 | Attempt present but substantially flawed/incomplete |
| 2 | Partially correct; material omissions or weak justification |
| 3 | Correct and complete for standard expectations |
| 4 | Strong execution with precise, well-supported details |

**Pass rule:** total score >=16/20 AND both critical dimensions >=3.

---

## v1-rubric-constraint-ledger-101

### Task (authoritative excerpt)

You are selecting an architecture for a local Markdown search tool.

Constraints:
- Must run entirely local (no hosted services)
- Team: 2 TypeScript engineers
- MVP delivery window: 2 weeks
- Must support incremental indexing
- Must support rollback to previous index format in under 1 day
- Memory budget: 800 MB at 50k documents

Output requirements:
1) Provide exactly 3 options.
2) For each option: short description (max 2 sentences), 2 strengths, 2 weaknesses, risk level (low/med/high).
3) Weighted score table (latency performance, implementation effort, operational simplicity, rollback simplicity). Weights sum to 100.
4) Recommend one option and justify in 3-5 sentences.
5) One fast-fail experiment for the recommended option.
6) No honorable mentions or extra options.

### Rubric Dimensions

Critical dimensions: **D1, D2**

| Dim | Name | What is scored |
|---|---|---|
| D1 | Structural compliance | Exactly 3 options; required sections present; no extra options/honorable mentions |
| D2 | Constraint coverage | All prompt constraints represented in option analysis and recommendation rationale |
| D3 | Trade-off quality | Strengths/weaknesses are concrete, non-duplicative, and decision-relevant |
| D4 | Quantitative coherence | Weighted score table is valid (weights sum to 100) and aligns with recommendation |
| D5 | Risk realism | Risk statement + fast-fail experiment are specific and testable |

### v1-rubric-constraint-ledger-101__CANDIDATE_A

[REDACTED PROCESS PREAMBLE]

### Option 1: In-Process JS Library (MiniSearch)

**Description:** Use MiniSearch (or similar pure-JS library) loaded directly into the Node.js process. The index is serialized to disk as JSON and loaded into memory on startup.

**Strengths:**
- Zero external dependencies -- single `npm install`, no native compilation, no sidecar process.
- Fastest possible integration for a TypeScript team -- API is idiomatic JS, debuggable in-process.

**Weaknesses:**
- Index lives entirely in memory; at 50k Markdown documents the serialized JSON index can approach or exceed the 800 MB budget depending on document size, with no built-in mechanism to cap usage.
- Incremental indexing requires manual implementation -- MiniSearch supports add/remove but not durable incremental persistence out of the box, so crash recovery requires full re-index or custom write-ahead logic.

**Risk level:** Medium

### Option 2: SQLite FTS5 via better-sqlite3

**Description:** Store Markdown content in a SQLite database with an FTS5 virtual table for full-text search. Access via `better-sqlite3`, a synchronous native binding with strong TypeScript support.

**Strengths:**
- FTS5 handles incremental indexing natively -- INSERT/UPDATE/DELETE on the content table automatically updates the full-text index, with ACID durability.
- Memory-efficient: SQLite pages data from disk, so the working set stays well under 800 MB even at 50k documents; the on-disk index is compact.

**Weaknesses:**
- Requires native compilation of `better-sqlite3` (prebuild binaries exist for most platforms, but CI and cross-platform builds add friction).
- Ranking and relevance tuning in FTS5 is limited compared to purpose-built search engines; BM25 is available but custom tokenizers or fuzzy matching require extra work.

**Risk level:** Low

### Option 3: Meilisearch Sidecar

**Description:** Run Meilisearch as a local subprocess managed by the Node.js application. Communicate via its HTTP REST API from TypeScript.

**Strengths:**
- Best-in-class search relevance out of the box -- typo tolerance, faceted search, and fast ranking with minimal configuration.
- Incremental indexing is a first-class feature via document upserts with automatic deduplication.

**Weaknesses:**
- Adds operational complexity: the application must manage a separate binary (lifecycle, health checks, port allocation, crash recovery), which is significant scope for a 2-person, 2-week MVP.
- Rollback is harder -- Meilisearch uses an internal LMDB store with its own migration path; reverting to a prior index format requires restoring a snapshot or re-indexing, not a simple file swap.

**Risk level:** High

### Weighted Score Table

| Criterion              | Weight | Option 1: MiniSearch | Option 2: SQLite FTS5 | Option 3: Meilisearch |
|------------------------|--------|----------------------|------------------------|-----------------------|
| Latency performance    | 25     | 8                    | 7                      | 9                     |
| Implementation effort  | 35     | 7                    | 8                      | 5                     |
| Operational simplicity | 20     | 9                    | 8                      | 4                     |
| Rollback simplicity    | 20     | 6                    | 9                      | 4                     |
| **Weighted total**     | **100**| **7.45**             | **7.95**               | **5.60**              |

Calculation detail:
- MiniSearch: (25 x 8 + 35 x 7 + 20 x 9 + 20 x 6) / 100 = (200 + 245 + 180 + 120) / 100 = 7.45
- SQLite FTS5: (25 x 7 + 35 x 8 + 20 x 8 + 20 x 9) / 100 = (175 + 280 + 160 + 180) / 100 = 7.95
- Meilisearch: (25 x 9 + 35 x 5 + 20 x 4 + 20 x 4) / 100 = (225 + 175 + 80 + 80) / 100 = 5.60

### Recommendation: Option 2 -- SQLite FTS5 via better-sqlite3

SQLite FTS5 scores highest because it directly satisfies the two hardest constraints without custom engineering. Incremental indexing is handled by SQLite's transaction system -- every INSERT or UPDATE to the content table atomically updates the FTS index, which eliminates the crash-recovery gap that MiniSearch would require custom code to close. Rollback is straightforward: copy the single `.db` file before a migration, and restore it to revert -- achievable in minutes, well under the 1-day requirement. The memory profile stays within budget because SQLite memory-maps the database and only pages in what queries touch, unlike MiniSearch which loads the entire index into the V8 heap. The native compilation requirement of `better-sqlite3` is a real cost, but prebuilt binaries cover macOS, Linux, and Windows, so for a 2-person team on standard platforms this is a one-time setup friction, not an ongoing burden.

### Fast-Fail Experiment for SQLite FTS5

**Goal:** Validate memory budget and query latency at target scale within 1 day.

**Procedure:**
1. Generate 50,000 synthetic Markdown files (1-10 KB each, representative of real content) using a script.
2. Bulk-insert all 50k documents into a SQLite FTS5 table using `better-sqlite3`.
3. Measure: (a) peak RSS of the Node.js process during indexing and during a burst of 100 search queries, (b) p50 and p99 query latency for single-term and multi-term searches, (c) on-disk size of the `.db` file.
4. **Pass criteria:** Peak RSS under 800 MB, p99 query latency under 100ms, on-disk size under 2 GB.
5. **Fail action:** If RSS exceeds budget, evaluate WAL mode tuning and `PRAGMA mmap_size` limits. If latency exceeds target, profile FTS5 tokenizer configuration. If neither fix resolves the issue, fall back to Option 1 (MiniSearch) with a custom persistence layer.

This experiment can be completed in half a day by one engineer, leaving the second week fully available for MVP feature work if the results pass.

### v1-rubric-constraint-ledger-101__CANDIDATE_B

[REDACTED PROCESS PREAMBLE]

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

### Option 2: SQLite FTS5 via better-sqlite3

Uses SQLite's built-in FTS5 (Full-Text Search 5) extension accessed through the `better-sqlite3` native Node binding. Documents are stored in an FTS5 virtual table with incremental INSERT/UPDATE/DELETE operations mapping directly to file system changes.

**Strengths:**
1. True incremental indexing out of the box -- single-row INSERT/DELETE operations update the FTS index without rebuilding, directly satisfying the incremental indexing requirement.
2. Memory-efficient by design: SQLite pages data from disk, keeping resident memory well under 800 MB even at 50k documents regardless of content size.

**Weaknesses:**
1. Requires a native binary dependency (`better-sqlite3` compiles a C extension), which introduces build-toolchain friction and potential CI/platform compatibility issues.
2. Rollback to a previous index format requires either restoring a full `.sqlite` database file snapshot or running a migration script -- more complex than swapping a flat file, though achievable within the 1-day window.

**Risk level:** low

### Option 3: MiniSearch with Versioned Snapshot Files

MiniSearch is a lightweight, zero-dependency TypeScript-native full-text search library that supports incremental add/remove/update operations on an in-memory index. Index snapshots are persisted as versioned JSON files with a version manifest for rollback.

**Strengths:**
1. Native incremental indexing API (`add`, `remove`, `replace`) eliminates the need for custom sharding -- directly meets the incremental indexing requirement with no workaround.
2. Pure TypeScript with no native dependencies, combined with a simpler API surface than Lunr.js, minimizes implementation effort for a 2-person team within the 2-week window.

**Weaknesses:**
1. Entire index resides in memory; at 50k documents, memory consumption depends heavily on field configuration and tokenization -- could approach the 800 MB ceiling if documents are content-heavy with many indexed fields.
2. Serialization/deserialization of the full in-memory index to disk on every snapshot introduces I/O latency proportional to index size, which may cause noticeable pauses at scale.

**Risk level:** med

## Weighted Score Table

Weights: latency performance (20), implementation effort (35), operational simplicity (20), rollback simplicity (25). Weights sum to 100.

| Criterion                | Weight | Option 1: Lunr.js | Option 2: SQLite FTS5 | Option 3: MiniSearch |
|--------------------------|--------|--------------------|------------------------|----------------------|
| Latency performance      | 20     | 6                  | 9                      | 7                    |
| Implementation effort    | 35     | 5                  | 7                      | 9                    |
| Operational simplicity   | 20     | 8                  | 6                      | 8                    |
| Rollback simplicity      | 25     | 9                  | 6                      | 8                    |
| **Weighted total**       | **100**| **6.80**           | **6.95**               | **8.15**             |

Calculation verification:
- Option 1: (20x6 + 35x5 + 20x8 + 25x9) / 100 = (120 + 175 + 160 + 225) / 100 = 6.80
- Option 2: (20x9 + 35x7 + 20x6 + 25x6) / 100 = (180 + 245 + 120 + 150) / 100 = 6.95
- Option 3: (20x7 + 35x9 + 20x8 + 25x8) / 100 = (140 + 315 + 160 + 200) / 100 = 8.15

## Recommendation: Option 3 -- MiniSearch with Versioned Snapshot Files

MiniSearch scores highest (8.15) across the weighted criteria, driven by its dominant advantage in implementation effort -- the heaviest-weighted criterion at 35 points. Its native TypeScript implementation with zero compilation dependencies means both engineers can begin productive work immediately, and its built-in incremental `add`/`remove`/`replace` API eliminates the custom sharding work that Lunr.js would require. Rollback is straightforward: the versioned snapshot approach lets you restore any prior index version by loading a previous JSON file and bumping the manifest pointer. The primary risk -- memory pressure at 50k documents -- is real but manageable through field-level index configuration (indexing titles and headings rather than full body text) and is directly testable before committing to the architecture.

## Fast-Fail Experiment for MiniSearch

**Memory budget validation at target scale:** Generate 50,000 synthetic Markdown documents with representative size distribution (median 2 KB, p95 15 KB, max 50 KB), index them with MiniSearch using the planned field configuration, then measure peak RSS (Resident Set Size) via `process.memoryUsage().rss`. If peak RSS exceeds 700 MB (87.5% of the 800 MB budget, leaving headroom for query-time allocations), the architecture fails the constraint and the team should pivot to Option 2 (SQLite FTS5). This experiment requires less than 1 day of engineering effort and should be executed before any other implementation work begins.

---

## v1-rubric-evidence-ledger-102

### Task (authoritative excerpt)

You are given four repository snippets [A]-[D] about rate limiting. Questions: (1) Where is the effective default likely enforced today? (2) Is there enough evidence to claim the Jan 20 spike was caused by a default-limit change?

Output requirements:
1) Claims ledger with exactly 5 rows: Claim | Type (Observation/Inference) | Evidence | Confidence (0.0-1.0) | Counter-evidence
2) If evidence conflicts, confidence must be <=0.6 with explanation.
3) End with "Unknowns & Next Checks" containing exactly 3 concrete checks.
4) No web sources.

### Rubric Dimensions

Critical dimensions: **D1, D3**

| Dim | Name | What is scored |
|---|---|---|
| D1 | Evidence typing accuracy | Observation vs Inference labels are correct for each claim |
| D2 | Citation precision | Evidence references map precisely to provided snippets/paths |
| D3 | Conflict calibration | Conflicting evidence causes explicit confidence downgrades and rationale |
| D4 | Unsupported-claim control | Avoids assertions not grounded in supplied evidence |
| D5 | Investigation quality | Unknowns + next checks are specific and likely to reduce uncertainty |

### v1-rubric-evidence-ledger-102__CANDIDATE_A

[REDACTED PROCESS PREAMBLE]

## Claims Ledger

| # | Claim | Type | Evidence | Confidence | Counter-evidence |
|---|-------|------|----------|------------|------------------|
| 1 | `apply_limit(user)` uses the hardcoded constant `DEFAULT_LIMIT = 200` as the baseline when no per-user override exists. | Observation | [A]: `DEFAULT_LIMIT = 200`; `apply_limit(user)` uses `DEFAULT_LIMIT` unless per-user override exists. | 0.85 | None from provided snippets. However, only a partial view of the code is available; initialization logic that overrides the constant at startup is not shown. |
| 2 | The production environment config sets a different default of 150, but there is no evidence the code reads this value. | Observation (value) / Inference (non-reading) | [B]: `RATE_LIMIT_DEFAULT=150`. [A]: describes `apply_limit` as using the hardcoded `DEFAULT_LIMIT`, with no mention of environment variable ingestion. | 0.5 | Confidence reduced because evidence conflicts. [B] exists as a prod config presumably intended to be consumed, yet [A] shows no mechanism for reading it. The snippet of [A] may be incomplete — there could be an `__init__` or config-loader module not shown that sets `DEFAULT_LIMIT` from the environment. The conflict between a config file that sets a value and code that appears not to read it cannot be resolved from these snippets alone. |
| 3 | The effective default enforced today is likely 200 (the hardcoded value), not 150 (the config value). | Inference | [A]: code uses `DEFAULT_LIMIT = 200`. [B]: config says 150 but no linkage to code is shown. [C]: Phase 2 planned to lower to 150, implying it was not yet reflected in code at the time the plan was written. | 0.5 | Confidence reduced because evidence conflicts. [B] sets 150 in prod config, and [C] describes a deliberate rollout to 150. If Phase 2 completed successfully, the effective default could be 150 via a mechanism not visible in [A]'s snippet. [D] adds further uncertainty: "unclear whether limiter default changed in deployed artifact." |
| 4 | The Jan 20 spike occurred after the Phase 2 target date (Jan 15) for lowering the default to 150. | Observation | [C]: Phase 2 lowers default after Jan 15. [D]: Spike observed after Jan 20 deployment. | 0.90 | None. Both dates are directly stated in the snippets. Minor caveat: "after Jan 15" in [C] is a planned date, not a confirmed execution date. |
| 5 | The Jan 20 spike was caused by a change in the rate-limit default. | Inference | Circumstantial only: [C] planned a default change around this period; [D] reports a spike after deployment in the same timeframe. | 0.3 | Confidence reduced because evidence conflicts and is insufficient. [D] explicitly states: "Unclear whether limiter default changed in deployed artifact." This directly undermines a causal claim. No artifact diff, deploy log, or metric correlation is provided. The spike could have other causes (traffic pattern, code bug, upstream dependency). Temporal proximity alone does not establish causation. |

Row count verification: 1, 2, 3, 4, 5. Exactly 5 rows.

Threshold verification for conflicting evidence:
- Claim 2: 0.5 (<= 0.6).
- Claim 3: 0.5 (<= 0.6).
- Claim 5: 0.3 (<= 0.6).

## Answers to the Questions

**1) Where is the effective default likely enforced today?**

Based on the available evidence, the effective default is likely enforced in `services/rate_limit.py` at the hardcoded value of 200. The code in [A] explicitly sets `DEFAULT_LIMIT = 200` and uses it in `apply_limit(user)`. While `config/prod.env` [B] specifies 150, no evidence links the environment variable to the code path. However, confidence is moderate (0.5) because the code snippet is partial and a config-loading mechanism may exist outside the visible scope.

**2) Is there enough evidence to claim the Jan 20 spike was caused by a default-limit change?**

No. The evidence is insufficient to support a causal claim. The incident summary [D] itself states the relationship is "unclear." The only supporting evidence is temporal proximity between the Phase 2 rollout window [C] and the spike date [D], which is circumstantial. No deploy artifact diff, metric correlation, or rollback-confirms-fix evidence is provided. Confidence in the causal claim is 0.3.

## Unknowns & Next Checks

1. **Inspect the full initialization path of `services/rate_limit.py`:** Determine whether `DEFAULT_LIMIT` is reassigned at module load or application startup from `os.environ["RATE_LIMIT_DEFAULT"]` or a config loader. This resolves the conflict between [A] (200) and [B] (150) and answers definitively which value is enforced at runtime.

2. **Retrieve the Jan 20 deploy artifact manifest or diff:** Compare the deployed artifact's rate-limit configuration against the prior deployment. This directly addresses [D]'s stated uncertainty ("unclear whether limiter default changed in deployed artifact") and is required before any causal claim about the spike.

3. **Correlate the spike timeline with the rate-limit metric (requests rejected vs. requests allowed):** If the spike corresponds to a sudden increase in allowed requests (consistent with a higher or missing limit), that supports the default-change hypothesis. If the spike is in a different metric (latency, errors), the cause is likely unrelated to the rate limiter. This check provides the observational evidence needed to move Claim 5 above 0.3.

Check count verification: 1, 2, 3. Exactly 3 checks.

### v1-rubric-evidence-ledger-102__CANDIDATE_B

[REDACTED PROCESS PREAMBLE]

## Claims Ledger

| # | Claim | Type | Evidence | Confidence | Counter-evidence |
|---|-------|------|----------|------------|------------------|
| 1 | The effective rate-limit default enforced in application code is 200 | Observation | [A] `DEFAULT_LIMIT = 200` is hardcoded in `services/rate_limit.py`; `apply_limit(user)` uses it unless per-user override exists | 0.8 | [B] `prod.env` sets `RATE_LIMIT_DEFAULT=150`, which could override the hardcoded value at runtime if the code reads env vars in logic not shown in the snippet |
| 2 | The prod environment configuration intends a default of 150 | Observation | [B] `RATE_LIMIT_DEFAULT=150` in `config/prod.env`; [C] Phase 2 plan to lower default from 200 to 150 after Jan 15 | 0.85 | No direct counter-evidence for the intent; the config file and rollout doc agree |
| 3 | The code and the environment config disagree on the effective default (200 vs 150) | Observation | [A] hardcodes 200; [B] configures 150; no evidence in the snippet that the code reads the env var | 0.6 | It is possible that `apply_limit()` contains env-var reading logic not shown in the snippet, which would resolve the conflict in favor of 150. Confidence capped at 0.6 because the evidence conflicts and we lack visibility into the full function body. |
| 4 | The Phase 2 rollout (lowering default to 150) may not have taken effect in the deployed artifact | Inference | [A] still shows `DEFAULT_LIMIT = 200` (not 150); [D] states "Unclear whether limiter default changed in deployed artifact"; the code-level evidence does not reflect the intended change from [C] | 0.6 | [B] shows the env var is set to 150, so if the runtime reads it, the rollout did take effect. Confidence capped at 0.6 because the code and config evidence point in opposite directions. |
| 5 | The Jan 20 spike cannot be conclusively attributed to a default-limit change | Inference | [D] explicitly flags uncertainty about whether the default changed; [A] still shows 200 (pre-change value); temporal correlation alone (spike after deployment) is insufficient for causation | 0.55 | [C] confirms a planned change around that timeframe; [B] shows prod config at 150; if the change did deploy and raised or lowered the effective limit unexpectedly, it could explain the spike. Confidence capped at 0.55 because the causal link is plausible but unverified in either direction. |

## Unknowns & Next Checks

1. **Check whether `apply_limit()` reads environment variables at runtime.** Inspect the full function body in `services/rate_limit.py` for any `os.getenv("RATE_LIMIT_DEFAULT")` or framework-level config injection that would override the hardcoded `DEFAULT_LIMIT = 200`. This resolves the code-vs-config conflict (Claims 1, 3, 4).

2. **Check the exact artifact deployed on Jan 20 for the value of `DEFAULT_LIMIT`.** Pull the deployed container image or build artifact from the Jan 20 release and inspect the frozen value in `services/rate_limit.py`. Compare it against the current repository HEAD. This directly answers whether the rollout changed the deployed default (Claims 4, 5).

3. **Check request-level logs or metrics around Jan 20 for actual rate-limit thresholds applied.** Query application logs or observability dashboards for the effective limit value used per-request before and after the Jan 20 deployment. This provides runtime evidence of what limit was actually enforced, independent of code or config (Claims 1, 5).

---

## v1-rubric-verdict-gating-103

### Task (authoritative excerpt)

Score a benchmark run using these rules:
- YES requires target improvement on >=70% of targeted scenarios, no high-severity regressions.
- If discriminability is weak due to ceiling effects, verdict should be INCONCLUSIVE.
- If placebo/irrelevant systematically outperform target on task-native outcomes, verdict should be NO or INCONCLUSIVE.

Scenario summary: 6 targeted scenarios, target improved in 2, no regressions >=2 points, 3 ceiling effects, one proxy-gaming outperformed in structural compliance not correctness, medium tool-usage divergence in 2 scenarios.

Output requirements:
1) Section "Evidence" with explicit computed metrics.
2) Section "Interpretation" with verdict and rationale.
3) Section "Confidence" with base, downgrade reasons, final.
4) Section "Decision Triggers" with exactly 3 bullet points.
5) No extra sections.

### Rubric Dimensions

Critical dimensions: **D1, D2**

| Dim | Name | What is scored |
|---|---|---|
| D1 | Metric correctness | Derived metrics are numerically correct from provided scenario data |
| D2 | Threshold logic | Verdict logic correctly applies stated threshold rules |
| D3 | Evidence/interpretation separation | Structural separation is explicit and respected |
| D4 | Confidence downgrade discipline | Confounders produce explicit confidence adjustment (not merely mentioned) |
| D5 | Decision-actionability | Clear trigger conditions for rerun/redesign/acceptance decisions |

### v1-rubric-verdict-gating-103__CANDIDATE_A

[REDACTED PROCESS PREAMBLE]

## Evidence

**Target Improvement Rate**

- Targeted scenarios total: 6
- Scenarios where target improved: 2
- Improvement rate: 2 / 6 = 33.3%
- Threshold for YES verdict: >= 70%
- 33.3% < 70% — threshold NOT met

**Regression Check**

- Regressions >= 2 points: 0
- High-severity regression threshold: >= 2 points
- 0 regressions >= 2 points — no high-severity regressions detected

**Ceiling Effects (Discriminability)**

- Scenarios with ceiling effects (all conditions scored at max): 3
- Total targeted scenarios: 6
- Ceiling-affected proportion: 3 / 6 = 50%
- 50% of scenarios are non-discriminating — discriminability is weak

**Effective Discriminating Scenarios**

- Scenarios that could show differentiation: 6 - 3 = 3
- Target improved among discriminating scenarios: 2 (assuming both improvements occurred in non-ceiling scenarios)
- Effective improvement rate among discriminating scenarios: 2 / 3 = 66.7%
- Note: even the effective rate (66.7%) is below the 70% threshold

**Proxy-Gaming / Placebo Performance**

- One proxy-gaming condition outperformed baseline in structural compliance: YES
- That same condition outperformed baseline in correctness: NO
- Rule: "If placebo/irrelevant systematically outperform target on task-native outcomes" — correctness is the task-native outcome here; proxy-gaming did NOT outperform on correctness. This rule does not trigger a forced NO/INCONCLUSIVE on this factor alone.

**Confounders**

- Medium tool-usage divergence observed in: 2 scenarios
- Proportion of targeted scenarios with confounders: 2 / 6 = 33.3%

## Interpretation

**Verdict: INCONCLUSIVE**

Rule application, in order of evaluation:

1. **YES requires target improvement on >= 70% of targeted scenarios.** Computed improvement rate is 33.3%. 33.3% < 70%. YES is ruled out.

2. **If discriminability is weak due to ceiling effects, verdict should be INCONCLUSIVE.** 3 of 6 scenarios (50%) show ceiling effects where all conditions scored at max, making differentiation impossible. Discriminability is weak. This rule applies directly — verdict maps to INCONCLUSIVE rather than NO.

3. **If placebo/irrelevant systematically outperform target on task-native outcomes, verdict should be NO or INCONCLUSIVE.** Proxy-gaming outperformed baseline only on structural compliance (a non-native metric), not on correctness (the task-native outcome). This rule does not activate.

4. **No high-severity regressions** — this condition is satisfied, so it does not push toward NO.

The primary driver of the INCONCLUSIVE verdict is the combination of (a) failing the 70% improvement threshold and (b) 50% of scenarios being non-discriminating due to ceiling effects. The ceiling effects mean we cannot determine whether the target skill would have improved in those 3 scenarios had the measurement instrument had sufficient range. The effective improvement rate among discriminating scenarios (66.7%) is suggestive but still below threshold, and the sample of discriminating scenarios (n=3) is too small for reliable inference. A NO verdict would require evidence that the skill does not work; here, the evidence is ambiguous due to measurement limitations.

## Confidence

- **Base confidence level:** Medium — the data is available and the rules are mechanically applicable, but the sample of discriminating scenarios is small (n=3).

- **Downgrade factor 1: Ceiling effects reducing effective sample size.** 50% of scenarios are non-discriminating. This means the verdict rests on only 3 data points. Impact: downgrade by one level (Medium to Low).

- **Downgrade factor 2: Medium tool-usage divergence as confounder.** 2 of 6 scenarios (33.3%) have medium tool-usage divergence, which could explain some of the observed differences independent of the skill. Impact: supports the downgrade already applied (reinforces Low, does not downgrade further since already at floor).

- **Final confidence level:** Low

## Decision Triggers

- **Re-run with adjusted scoring rubrics that eliminate ceiling effects** (e.g., extend the scale range or increase task difficulty in the 3 ceiling-affected scenarios): if the target then improves in >= 70% of all 6 discriminating scenarios, the verdict would change to YES.

- **Identify and control for tool-usage divergence** (e.g., normalize tool access or re-run the 2 confounded scenarios with matched tool usage): if confounders are eliminated and the improvement rate among all discriminating scenarios remains below 70%, the verdict would change to NO with higher confidence.

- **Increase the number of targeted scenarios** (e.g., add 4+ new non-ceiling scenarios to the suite): if the target improves in >= 70% of the expanded set with no new ceiling effects or confounders, the verdict would change to YES; if improvement remains below 70% with adequate discriminability, the verdict would change to NO.

### v1-rubric-verdict-gating-103__CANDIDATE_B

[REDACTED PROCESS PREAMBLE]

## Evidence

**Improvement rate (target condition):**
- Target improved in 2 of 6 targeted scenarios.
- Improvement rate = 2 / 6 = 33.3%.
- Required threshold for YES verdict: >= 70%.
- Result: **FAILS** the 70% improvement gate (33.3% < 70%).

**Regression check:**
- No regressions >= 2 points observed.
- Result: **PASSES** the no-high-severity-regression gate.

**Ceiling effects / discriminability:**
- 3 of 6 targeted scenarios show ceiling effects (all conditions scored at max).
- Ceiling rate = 3 / 6 = 50%.
- These 3 scenarios cannot discriminate between conditions because every condition hit the maximum score. They contribute zero signal to the improvement rate.

**Effective discriminable scenarios:**
- 6 total - 3 ceiling = 3 discriminable scenarios.
- Of those 3, target improved in 2.
- Adjusted improvement rate on discriminable scenarios = 2 / 3 = 66.7%.
- This still falls below the 70% threshold (66.7% < 70%), though it is close.

**Proxy-gaming check:**
- One proxy-gaming condition outperformed baseline on structural compliance but NOT on correctness.
- Since the outperformance is on a non-task-native outcome (structural compliance, not correctness), this does not trigger the "placebo/irrelevant systematically outperform target on task-native outcomes" rule.
- Result: **No trigger** for the proxy-gaming downgrade rule.

**Confounders:**
- Medium tool-usage divergence in 2 of 6 scenarios.
- Confounder rate = 2 / 6 = 33.3%.
- This introduces ambiguity about whether observed improvements are attributable to the target condition or to differential tool usage.

## Interpretation

**Verdict: INCONCLUSIVE**

**Rationale:**

The raw improvement rate of 33.3% (2/6) clearly fails the 70% threshold required for a YES verdict. However, three reasons prevent a clean NO verdict and push toward INCONCLUSIVE:

1. **Ceiling effects destroy half the signal.** 50% of targeted scenarios (3/6) are undiscriminable because all conditions scored at the maximum. The benchmark cannot distinguish conditions on these scenarios. When restricted to the 3 discriminable scenarios, the improvement rate rises to 66.7% -- close to the 70% gate but still below it.

2. **The gating rules explicitly state:** "If discriminability is weak due to ceiling effects, verdict should be INCONCLUSIVE." With 50% of scenarios at ceiling, discriminability is demonstrably weak.

3. **Confounders further erode attribution.** Medium tool-usage divergence in 2 scenarios means even the 2 observed improvements may be partially or fully explained by confounders rather than the target intervention itself.

The proxy-gaming signal does not alter the verdict because the outperformance was on structural compliance (a non-task-native outcome), not on correctness. This is noted but does not meet the rule's trigger condition of "task-native outcomes."

A NO verdict would require that the evidence positively demonstrates the target does not work. Here, the evidence is contaminated by ceiling effects and confounders -- the experiment lacks the power to conclude either way.

## Confidence

- **Base confidence:** Medium -- the data is internally consistent and the gating rules are unambiguous in their application.
- **Downgrade reason(s):**
  1. 50% ceiling rate severely limits the effective sample size (3 discriminable scenarios is too few for robust inference).
  2. Medium tool-usage divergence in 2 scenarios introduces a plausible alternative explanation for the observed improvements, weakening causal attribution.
- **Final confidence:** Low -- the combination of a tiny effective sample (n=3 discriminable) and active confounders means the INCONCLUSIVE verdict itself rests on limited evidence. A differently constructed benchmark could yield a different result.

## Decision Triggers

- **Re-running with calibrated scoring rubrics** that eliminate ceiling effects (e.g., raising the score cap or adding granularity at the top end) would provide discriminability on all 6 scenarios; if the target then improves in >= 5 of 6, the verdict would change to YES.
- **Controlling for tool-usage divergence** (e.g., by normalizing tool availability across conditions or adding tool-usage as a covariate) and finding that the 2 target improvements hold after adjustment would raise confidence and could shift the verdict toward YES or a confident NO.
- **Evidence that the proxy-gaming condition outperforms target on correctness** (not just structural compliance) across multiple scenarios would trigger the "placebo/irrelevant systematically outperform target on task-native outcomes" rule, changing the verdict to NO.
