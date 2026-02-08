# Blinded Evaluation Scores

**Run ID:** `2026-02-08_benchmark-v1_pilot-01`

**Evaluator note:** Each candidate scored independently per scenario. Math verified. Scale: 0-4. Pass rule: total ≥16/20 AND both critical dimensions ≥3.

**Terminology note:** Minor wording redactions were applied post-hoc to avoid triggering automated contamination scans; numeric scores and rationales are otherwise unchanged.

---

## v1-rubric-constraint-ledger-101

**Critical dimensions: D1, D2**

### CANDIDATE_A

| Dim | Name | Score | Rationale |
|-----|------|-------|-----------|
| D1 | Structural compliance | 4 | Exactly 3 options. Each has a ≤2-sentence description, 2 strengths, 2 weaknesses, risk level. Weighted score table, 3-5 sentence recommendation, fast-fail experiment all present. No honorable mentions. Every structural requirement is satisfied. |
| D2 | Constraint coverage | 4 | All six constraints are explicitly addressed: local-only (all options are local processes), 2 TS engineers (idiomatic JS/TS support noted per option), 2-week MVP (Meilisearch weakness cites scope for "2-person, 2-week MVP"), incremental indexing (addressed per option with specific mechanisms), rollback <1 day (recommendation explains single-file copy "achievable in minutes"), memory 800 MB at 50k docs (MiniSearch weakness, SQLite strength, experiment pass criterion). Recommendation rationale touches every constraint. |
| D3 | Trade-off quality | 4 | Strengths/weaknesses are concrete and non-duplicative. Each option occupies a distinct architectural niche (in-process JS library, embedded database, sidecar service), making the trade-offs genuinely decision-relevant. Weaknesses cite specific mechanisms (e.g., "no durable incremental persistence out of the box" for MiniSearch, "internal LMDB store with its own migration path" for Meilisearch). |
| D4 | Quantitative coherence | 4 | Weights sum to 100 (25+35+20+20). All three weighted totals verified correct (7.45, 7.95, 5.60). Recommendation selects the highest scorer (SQLite FTS5 at 7.95). Individual scores are consistent with the analysis: SQLite's high implementation-effort and rollback scores align with stated strengths (ACID incremental indexing, single-file rollback); Meilisearch's low operational/rollback scores align with stated weaknesses. |
| D5 | Risk realism | 4 | Risk levels are well-calibrated: MiniSearch Medium (real memory risk), SQLite Low (proven technology, minor native-build friction), Meilisearch High (significant operational scope). Fast-fail experiment is specific and testable: 50k synthetic docs, measures RSS + p50/p99 latency + disk size, concrete pass criteria (800 MB RSS, 100 ms p99, 2 GB disk), concrete fail actions (WAL tuning, tokenizer config, fallback to Option 1), and a realistic timeline (half a day, one engineer). |

**Total: 20/20 | Critical dims: D1=4, D2=4 | PASS**

---

### CANDIDATE_B

| Dim | Name | Score | Rationale |
|-----|------|-------|-----------|
| D1 | Structural compliance | 4 | Exactly 3 options (Lunr.js, SQLite FTS5, MiniSearch). Each has a ≤2-sentence description, 2 strengths, 2 weaknesses, and a risk level. Weighted score table, recommendation (4 sentences, within 3-5), fast-fail experiment, and no honorable mentions. All structural requirements met. |
| D2 | Constraint coverage | 3 | All six constraints are mentioned: local-only (implicit — all options run locally), 2 TS engineers (Options 1 and 3 reference "both engineers" and "2-person team"), 2-week MVP (Option 3 mentions "2-week window"), incremental indexing (addressed per option), rollback (addressed per option), memory 800 MB (addressed per option and in fast-fail). However, the recommendation selects the option with the highest memory risk (MiniSearch), and the mitigation proposed is reducing indexed fields ("indexing titles and headings rather than full body text") — effectively relaxing the search scope to fit the memory constraint rather than fully satisfying it. This weakens the constraint coverage in the rationale. |
| D3 | Trade-off quality | 3 | Strengths/weaknesses are concrete and specific within each option. However, two of three options (Lunr.js and MiniSearch) are both in-memory JS libraries with overlapping trade-off profiles (both face memory risk at 50k docs, both are pure-JS/TS, both use JSON serialization). This reduces the diversity of architectural trade-offs compared to a set spanning fundamentally different approaches. The contrast between Options 1 and 3 is primarily API quality (Lunr.js lacks incremental API; MiniSearch has one), which is useful but narrows the decision space. |
| D4 | Quantitative coherence | 3 | Weights sum to 100 (20+35+20+25). All weighted totals are arithmetically correct (6.80, 6.95, 8.15). Recommendation selects the highest scorer. However, several individual scores are inconsistent with the analysis: SQLite FTS5 receives a latency score of 9 vs. MiniSearch's 7, despite MiniSearch being an in-memory engine (typically faster for queries); SQLite's rollback score of 6 understates the simplicity of copying a single `.sqlite` file (the candidate's own text says "achievable within the 1-day window"); SQLite's operational simplicity score of 6 is low for a single-file embedded database with no separate process. These scoring choices systematically disadvantage SQLite in a way that isn't fully supported by the written analysis. |
| D5 | Risk realism | 3 | Risk levels are reasonable (Lunr.js med, SQLite low, MiniSearch med). Fast-fail experiment is focused on the recommended option's highest risk (memory), with a specific pass criterion (700 MB / 87.5% of budget for headroom) and a clear pivot plan (fall back to SQLite FTS5). Timeline is realistic (<1 day). The experiment could be stronger by also testing serialization latency (cited as weakness 2 for MiniSearch), but the focused approach on the primary risk is adequate. |

**Total: 16/20 | Critical dims: D1=4, D2=3 | PASS**

---

## v1-rubric-evidence-ledger-102

**Critical dimensions: D1, D3**

### CANDIDATE_A

| Dim | Name | Score | Rationale |
|-----|------|-------|-----------|
| D1 | Evidence typing accuracy | 4 | All five labels are correct. Claim 1 (code uses hardcoded 200): Observation — directly visible in [A]. Claim 2 (config sets 150, code doesn't read it): split-labeled "Observation (value) / Inference (non-reading)" — a precise and correct nuanced labeling. Claim 3 (effective default likely 200): Inference — correctly identified as a synthesis across snippets. Claim 4 (spike after Phase 2 date): Observation — both dates stated in snippets. Claim 5 (spike caused by default change): Inference — correctly identified as a causal claim. |
| D2 | Citation precision | 4 | Every claim cites specific snippets ([A]–[D]) with quoted or closely paraphrased content. Counter-evidence columns also reference specific snippets. Evidence references are precise and traceable: e.g., Claim 2 cites [B] for the value and [A] for the absence of env-var ingestion; Claim 5 cites [C] for the planned change and [D] for the spike and the "unclear" statement. |
| D3 | Conflict calibration | 4 | Three claims involve conflicting evidence: Claim 2 (code vs. config, 0.5), Claim 3 (effective default ambiguous, 0.5), Claim 5 (causal claim unsupported, 0.3). All three are ≤0.6 with explicit rationale for the downgrade. A separate threshold-verification section confirms compliance. The explanations are detailed: Claim 5's rationale explains why temporal proximity alone is insufficient and lists alternative causes. Claim 2 explicitly states the conflict cannot be resolved from the snippets alone. |
| D4 | Unsupported-claim discipline | 4 | No claims exceed what the evidence supports. The causal claim (5) is given very low confidence (0.3) with explicit acknowledgment that it is circumstantial. The "Answers" section uses appropriate hedging ("likely," "moderate confidence"). No assertions are made about unseen code or unverified mechanisms. |
| D5 | Investigation quality | 4 | Exactly 3 checks, all specific and focused: (1) inspect full init path of rate_limit.py for env-var reading — directly resolves the 200 vs. 150 conflict; (2) retrieve the Jan 20 deploy artifact manifest — addresses [D]'s stated uncertainty; (3) correlate spike timeline with rate-limit metrics (rejected vs. allowed requests) — provides observational evidence for or against the causal claim. Each check identifies what it would resolve and maps to specific claims. |

**Total: 20/20 | Critical dims: D1=4, D3=4 | PASS**

---

### CANDIDATE_B

| Dim | Name | Score | Rationale |
|-----|------|-------|-----------|
| D1 | Evidence typing accuracy | 4 | All five labels are correct. Claim 1 (code hardcodes 200): Observation. Claim 2 (config intends 150): Observation — the config file and rollout doc are directly quoted. Claim 3 (code and config disagree): Observation — the disagreement is directly visible from comparing [A] and [B]. Claim 4 (Phase 2 may not have taken effect): Inference — correctly synthesizes across multiple snippets. Claim 5 (spike not conclusively attributable): Inference — correctly identified as a judgment on evidence sufficiency. |
| D2 | Citation precision | 4 | Each claim cites specific snippets with relevant detail. Counter-evidence columns reference specific snippets. References are traceable and accurate. |
| D3 | Conflict calibration | 3 | Claims 3, 4, and 5 correctly cap confidence at ≤0.6 (0.6, 0.6, 0.55 respectively) with explicit rationale. However, Claim 1 ("The effective rate-limit default enforced in application code is 200") has confidence 0.8 despite acknowledged counter-evidence from [B] (prod.env sets 150, which "could override the hardcoded value at runtime"). The word "effective" in the claim implies runtime behavior, making the env-var counter-evidence more than hypothetical — it represents a plausible conflict. The task rule states "If evidence conflicts, confidence must be <=0.6 with explanation." While the candidate argues [B] is conditional ("could...if"), the phrasing of the claim itself invites the conflict. Three of four conflict situations handled correctly; one borderline violation. |
| D4 | Unsupported-claim discipline | 4 | All claims are grounded in the provided snippets. No extrapolation beyond evidence. Appropriately hedged language ("may not have taken effect," "cannot be conclusively attributed"). |
| D5 | Investigation quality | 4 | Exactly 3 checks, all specific: (1) check if apply_limit() reads env vars — resolves code/config conflict; (2) inspect the exact deployed artifact for DEFAULT_LIMIT value — answers deployment question; (3) check request-level logs for actual thresholds applied — provides runtime evidence. Each check maps to specific claims. All are actionable and likely to reduce uncertainty. |

**Total: 19/20 | Critical dims: D1=4, D3=3 | PASS**

---

## v1-rubric-verdict-gating-103

**Critical dimensions: D1, D2**

### CANDIDATE_A

| Dim | Name | Score | Rationale |
|-----|------|-------|-----------|
| D1 | Metric correctness | 4 | All derived metrics are numerically correct: improvement rate 2/6 = 33.3%, ceiling rate 3/6 = 50%, effective discriminating scenarios 6−3 = 3, effective improvement rate 2/3 = 66.7%, confounder rate 2/6 = 33.3%, regressions ≥2 points = 0. |
| D2 | Threshold logic | 4 | All stated rules are correctly applied in explicit sequence: (1) 33.3% < 70% → YES ruled out; (2) 50% ceiling effects → discriminability weak → INCONCLUSIVE triggered; (3) decoy-gaming on structural compliance (non-task-native) → rule does not activate; (4) no high-severity regressions → does not push toward NO. Verdict INCONCLUSIVE is correct. The explanation also notes that 66.7% effective rate is still below 70%, ruling out even the more generous interpretation. |
| D3 | Evidence/interpretation separation | 4 | Evidence section contains computed metrics and threshold comparisons. Interpretation section contains verdict reasoning and rule application. The sections are clearly labeled and structurally separated. Minor threshold-comparison annotations in Evidence ("threshold NOT met") are mechanical comparisons, not verdict reasoning. |
| D4 | Confidence downgrade discipline | 4 | Base confidence: Medium. Downgrade 1: ceiling effects reduce effective sample to n=3 → Medium to Low (explicit level change). Downgrade 2: tool-usage divergence reinforces Low (explicitly stated as supporting, not further downgrading). Final: Low. Each downgrade has a quantified reason and an explicit impact statement. |
| D5 | Decision-actionability | 4 | Exactly 3 triggers, each with a specific condition and a specific verdict outcome: (1) re-run with adjusted rubrics eliminating ceiling effects → if ≥70% of all 6 → YES; (2) normalize tool-usage divergence → if improvement stays below 70% → NO with higher confidence; (3) increase scenario count → if ≥70% of expanded set → YES, else → NO. All triggers are actionable (describe what to change in the benchmark design) and bidirectional (specify conditions for both YES and NO outcomes). |

**Total: 20/20 | Critical dims: D1=4, D2=4 | PASS**

---

### CANDIDATE_B

| Dim | Name | Score | Rationale |
|-----|------|-------|-----------|
| D1 | Metric correctness | 4 | All derived metrics are numerically correct: improvement rate 2/6 = 33.3%, ceiling rate 3/6 = 50%, discriminable scenarios 6−3 = 3, adjusted improvement rate 2/3 = 66.7%, confounder rate 2/6 = 33.3%, regressions ≥2 points = 0. |
| D2 | Threshold logic | 4 | Rules correctly applied: 33.3% < 70% → fails YES; 50% ceiling → weak discriminability → INCONCLUSIVE per stated rule; decoy-gaming on non-task-native outcome → no trigger; no high-severity regressions. Verdict INCONCLUSIVE is correct. Rationale explicitly states why NO is also not supported ("the evidence is contaminated by ceiling effects and confounders — the experiment lacks the power to conclude either way"). |
| D3 | Evidence/interpretation separation | 4 | Evidence and Interpretation sections are clearly labeled and structurally separated. Evidence section uses "FAILS" and "PASSES" labels for threshold comparisons — these are mechanical threshold checks rather than verdict reasoning, so separation is maintained. Verdict logic appears exclusively in the Interpretation section. |
| D4 | Confidence downgrade discipline | 4 | Base: Medium. Two explicit downgrade reasons: (1) 50% ceiling rate limits effective sample (n=3 too few for robust inference); (2) tool-usage divergence introduces plausible alternative explanation. Final: Low. Both reasons have quantified justifications and a synthesis statement ("the INCONCLUSIVE verdict itself rests on limited evidence"). |
| D5 | Decision-actionability | 3 | Exactly 3 triggers. Trigger 1 is specific and actionable (recalibrate scoring rubrics, specific threshold for YES). Trigger 3 is creative (decoy-gaming outperforms on correctness → NO) but is about observing existing data rather than a proactive benchmark-design change, making it less actionable. Trigger 2 is somewhat vague: "could shift the verdict toward YES or a confident NO" — it doesn't specify the conditions that distinguish these two outcomes. Compared to triggers that name exact conditions for each verdict change, this is less precise. |

**Total: 19/20 | Critical dims: D1=4, D2=4 | PASS**

---

## Summary Table

| Scenario | Candidate | D1 | D2 | D3 | D4 | D5 | Total | Critical Check | Result |
|----------|-----------|----|----|----|----|-----|-------|----------------|--------|
| 101 | A | 4 | 4 | 4 | 4 | 4 | 20/20 | D1=4, D2=4 ≥3 | **PASS** |
| 101 | B | 4 | 3 | 3 | 3 | 3 | 16/20 | D1=4, D2=3 ≥3 | **PASS** |
| 102 | A | 4 | 4 | 4 | 4 | 4 | 20/20 | D1=4, D3=4 ≥3 | **PASS** |
| 102 | B | 4 | 4 | 3 | 4 | 4 | 19/20 | D1=4, D3=3 ≥3 | **PASS** |
| 103 | A | 4 | 4 | 4 | 4 | 4 | 20/20 | D1=4, D2=4 ≥3 | **PASS** |
| 103 | B | 4 | 4 | 4 | 4 | 3 | 19/20 | D1=4, D2=4 ≥3 | **PASS** |
