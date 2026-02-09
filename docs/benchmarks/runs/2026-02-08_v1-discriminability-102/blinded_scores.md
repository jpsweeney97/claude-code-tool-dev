# Blinded Scores — v1 Discriminability Experiment (Scenario 102)

**Run ID:** `2026-02-08_v1-discriminability-102`

**Evaluator notes:** Each candidate was scored independently against the rubric dimensions (D1-D5) on the 0-4 scale. Scoring for Replicate 2 was completed before Replicate 3.

---

## Replicate 2

### replicate-2__CANDIDATE_A

| Dim | Score | Rationale |
|-----|-------|-----------|
| D1  | 4     | All 5 Observation/Inference labels are correct. Claims 1-2 (directly readable from snippets) labeled Observation; Claims 3-5 (require reasoning about precedence, intent, causation) labeled Inference. No misclassifications. |
| D2  | 4     | Every claim cites specific snippets ([A]-[D]) with exact variable names, file paths, and quoted phrases. Cross-references between snippets are precise and traceable. |
| D3  | 4     | All three conflicting-evidence claims are properly downgraded: Claim 3 at 0.55 (code-vs-config conflict), Claim 4 at 0.6 (incident uncertainty), Claim 5 at 0.3 (unverified causal mechanism). Each includes explicit rationale tied to specific evidence conflicts. |
| D4  | 4     | All assertions are grounded in provided snippets. No web sources. Appropriate hedging throughout ("most likely," "may not have included"). Summary avoids overreach. |
| D5  | 4     | Three concrete checks: (1) inspect `apply_limit()` for env-var reading, (2) pull Jan 20 deployment artifact, (3) review deployment changelog for concurrent changes. All actionable and target specific uncertainties that would resolve open claims. |

**Total: 20/20 | Pass: Yes** (D1=4 >= 3, D3=4 >= 3, Total=20 >= 16)

---

### replicate-2__CANDIDATE_B

| Dim | Score | Rationale |
|-----|-------|-----------|
| D1  | 4     | All 5 labels correct. Claims 1-2 as Observation (code value and config value are directly readable), Claim 2's framing of the conflict as factual observation is defensible. Claims 3-5 as Inference (effective default, deployment status, causal insufficiency). |
| D2  | 4     | Precise references to snippets with specific variable names, file paths, and content. All evidence columns map accurately to provided material. |
| D3  | 4     | Claim 3 at 0.5, Claim 4 at 0.5, Claim 5 at 0.6 — all at or below 0.6 threshold with explicit rationale. Includes a dedicated "Summary of Confidence Downgrades" section explaining each downgrade with reference to specific conflicting evidence. |
| D4  | 4     | All claims grounded in snippets. Includes row-count and confidence-threshold verification. No unsupported assertions or web sources. |
| D5  | 4     | Three checks: (1) env-var consumption in `apply_limit`, (2) deployment manifest/artifact inspection, (3) rate-limit metrics (HTTP 429 counts, throughput). Cross-references which claims each check resolves. All specific and uncertainty-reducing. |

**Total: 20/20 | Pass: Yes** (D1=4 >= 3, D3=4 >= 3, Total=20 >= 16)

---

## Replicate 3

### replicate-3__CANDIDATE_A

| Dim | Score | Rationale |
|-----|-------|-----------|
| D1  | 4     | All labels defensible. Claims 1-2 as Observation (direct snippet content). Claim 3 as Inference (reasoning about ambiguous effective value). Claim 4 as Observation — defensible since both the schedule ([C]) and deployment ([D]) are directly stated, and "within that window" is calendar arithmetic. Claim 5 as Inference (causal claim). |
| D2  | 4     | All citations precise with specific snippet references, variable names (`DEFAULT_LIMIT`, `RATE_LIMIT_DEFAULT`), file paths, and quoted phrases. |
| D3  | 4     | Claim 3 at 0.5 (code-vs-config conflict) and Claim 5 at 0.3 (causal claim undermined by [D]'s stated uncertainty) — both properly downgraded with thorough rationale. Claim 4 at 0.85 is appropriate because that claim only asserts observable schedule/deployment facts, not that Phase 2 was actually deployed. |
| D4  | 4     | No ungrounded claims. Careful hedging ("cannot be determined with confidence," "evidence is insufficient"). Separate answers section stays within evidence bounds. |
| D5  | 4     | Three checks: (1) initialization path of `DEFAULT_LIMIT` in full module, (2) deployment manifest/release diff for Jan 20, (3) rate-limit telemetry from Jan 19-21. All specific, actionable, and targeted at resolving key uncertainties. |

**Total: 20/20 | Pass: Yes** (D1=4 >= 3, D3=4 >= 3, Total=20 >= 16)

---

### replicate-3__CANDIDATE_B

| Dim | Score | Rationale |
|-----|-------|-----------|
| D1  | 4     | All labels correct. Claims 1-2 as Observation (Claim 2's "consistent with Phase 2" notes alignment between [B] and [C], which is a factual observation of matching values). Claims 3-5 as Inference (effective default, temporal correlation, rollout inconsistency). |
| D2  | 4     | All citations map precisely to snippets with specific values, paths, and content. Evidence columns are traceable and accurate. |
| D3  | 4     | Claim 3 at 0.5, Claim 4 at 0.45, Claim 5 at 0.6 — all at or below 0.6 threshold. Each includes explicit "confidence is capped" rationale tied to specific evidence conflicts. Proper calibration throughout. |
| D4  | 4     | Claim 5 (rollout/rollback inconsistency) is a reasonable inference from the code/env mismatch, properly hedged with counter-evidence acknowledging alternative interpretation. No unsupported assertions or web sources. |
| D5  | 4     | Three checks: (1) full `apply_limit()` implementation review, (2) deployed artifact from Jan 20, (3) application logs/metrics for enforced limit values Jan 19-21. Cross-references resolved claims. All specific and uncertainty-reducing. |

**Total: 20/20 | Pass: Yes** (D1=4 >= 3, D3=4 >= 3, Total=20 >= 16)

---

## Summary Table

| Candidate | D1 | D2 | D3 | D4 | D5 | Total | Pass |
|-----------|----|----|----|----|-----|-------|------|
| replicate-2__CANDIDATE_A | 4 | 4 | 4 | 4 | 4 | 20/20 | Yes |
| replicate-2__CANDIDATE_B | 4 | 4 | 4 | 4 | 4 | 20/20 | Yes |
| replicate-3__CANDIDATE_A | 4 | 4 | 4 | 4 | 4 | 20/20 | Yes |
| replicate-3__CANDIDATE_B | 4 | 4 | 4 | 4 | 4 | 20/20 | Yes |
