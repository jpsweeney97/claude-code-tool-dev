# Blinded Evaluation Packet — v1 Discriminability Experiment (Scenario 102)

**Run ID:** `2026-02-08_v1-discriminability-102`

**Status:** READY FOR EVALUATION

**Instructions for evaluator:**
- Score each candidate output against the rubric dimensions (0-4 scale per dimension).
- Do NOT attempt to determine which candidate is which condition.
- Score independently: finish all scoring for one replicate before moving to the next.
- All candidate labels (A/B) are randomized and condition-free.
- The rubric and scale anchors are provided below.
- Write scores to `blinded_scores.md` in this directory.

**Scale anchors (all replicates):**

| Score | Meaning |
|---|---|
| 0 | Missing or incorrect; directly violates requirement |
| 1 | Attempt present but substantially flawed/incomplete |
| 2 | Partially correct; material omissions or weak justification |
| 3 | Correct with minor gaps; meets the requirement but room for improvement |
| 4 | Fully correct; thorough, precise, well-justified |

**Pass rule:** Total >= 16/20 AND both critical dimensions >= 3.

---

## Task (authoritative excerpt)

You are given four repository snippets [A]-[D] about rate limiting. Questions: (1) Where is the effective default likely enforced today? (2) Is there enough evidence to claim the Jan 20 spike was caused by a default-limit change?

Output requirements:
1) Claims ledger with exactly 5 rows: Claim | Type (Observation/Inference) | Evidence | Confidence (0.0-1.0) | Counter-evidence
2) If evidence conflicts, confidence must be <=0.6 with explanation.
3) End with "Unknowns & Next Checks" containing exactly 3 concrete checks.
4) No web sources.

## Rubric Dimensions

Critical dimensions: **D1, D3**

| Dim | Name | What is scored |
|---|---|---|
| D1 | Evidence typing accuracy | Observation vs Inference labels are correct for each claim |
| D2 | Citation precision | Evidence references map precisely to provided snippets/paths |
| D3 | Conflict calibration | Conflicting evidence causes explicit confidence downgrades and rationale |
| D4 | Unsupported-claim control | Avoids assertions not grounded in supplied evidence |
| D5 | Investigation quality | Unknowns + next checks are specific and likely to reduce uncertainty |

---

# Replicate 2

---

## replicate-2__CANDIDATE_A

[REDACTED PROCESS PREAMBLE]

## Claims Ledger

| Claim | Type | Evidence | Confidence | Counter-evidence |
|-------|------|----------|------------|------------------|
| The application code defines a hardcoded default rate limit of 200 | Observation | [A]: `DEFAULT_LIMIT = 200` in `services/rate_limit.py` | 0.95 | None from provided snippets; minor residual uncertainty that the snippet may be outdated or from a non-deployed branch |
| The production environment is configured with a default rate limit of 150 | Observation | [B]: `RATE_LIMIT_DEFAULT=150` in `config/prod.env` | 0.9 | [A] shows `apply_limit(user)` uses `DEFAULT_LIMIT` (the hardcoded constant) with no mention of reading environment variables, so the env var may not be consumed by the running application |
| The effective default enforced today is 200 (the code constant), not 150 (the env var) | Inference | [A]: `apply_limit(user)` is described as using `DEFAULT_LIMIT` unless a per-user override exists, with no mention of environment-based config loading. The code and env config disagree (200 vs 150), suggesting the env var is not wired in. | 0.55 | [B] exists in `config/prod.env`, implying some deployment mechanism may inject it. [C] documents an intentional Phase 2 change to 150, suggesting an integration path was planned. Confidence is <=0.6 because the evidence directly conflicts: the code says 200, the env says 150, and we lack visibility into the config-loading layer that would resolve which wins. |
| The Phase 2 rollout (lowering the default to 150) was intended to be active by Jan 20 | Inference | [C]: Phase 2 planned "after Jan 15." [B]: prod.env already reflects 150. Timeline aligns with [D]'s Jan 20 deployment. | 0.6 | [D] explicitly states it is "unclear whether limiter default changed in deployed artifact," meaning the deployment may not have included the config change. [A] shows the code still defines 200, which may mean Phase 2 was only partially applied (env updated, code not updated to read it). Confidence is <=0.6 because the incident summary directly questions whether the change was deployed. |
| The Jan 20 spike was caused by a change in the rate limit default | Inference | [C]: Phase 2 timing (after Jan 15) coincides with [D]'s Jan 20 deployment. [B]: prod.env shows 150, consistent with the Phase 2 target. Temporal correlation exists. | 0.3 | [D]: "Unclear whether limiter default changed in deployed artifact" -- the incident team itself could not confirm causation. [A]: Code still shows `DEFAULT_LIMIT = 200` with no env-var integration visible, so the limit may never have changed in practice. Correlation in timing is not causation. Multiple confounders possible (deployment could have included other changes). Confidence is well below 0.6 because direct counter-evidence exists from the incident summary, and the causal mechanism (env var actually changing runtime behavior) is unverified. |

## Summary of Reasoning

**Question 1 (effective default today):** Most likely the code-level constant of 200, because `apply_limit()` as described references `DEFAULT_LIMIT` directly with no mention of environment variable loading. However, confidence is moderate (0.55) because `prod.env` exists with 150, and there may be a config-loading layer not shown in the snippets.

**Question 2 (causal link to Jan 20 spike):** No, there is not enough evidence to claim causation. The incident summary itself ([D]) flags uncertainty about whether the default changed in the deployed artifact. The code ([A]) still shows 200 with no visible mechanism to read the env var. While the timeline correlates (Phase 2 after Jan 15, spike after Jan 20), at least three unknowns remain unresolved: whether the env var is consumed, whether it was in the deployed artifact, and whether other deployment changes contributed. Confidence in the causal claim is 0.3.

## Unknowns & Next Checks

1. **Check whether `apply_limit()` reads from environment variables at runtime.** Inspect the full implementation of `services/rate_limit.py` (and any config-loading module it imports) to determine whether `RATE_LIMIT_DEFAULT` from `prod.env` overrides the hardcoded `DEFAULT_LIMIT = 200`. This resolves the core conflict between snippets [A] and [B] and determines the effective default.

2. **Check the Jan 20 deployment artifact's actual configuration.** Pull the deployed container image, release tag, or deployment manifest from Jan 20 and inspect the bundled `prod.env` (or equivalent runtime config) to confirm whether `RATE_LIMIT_DEFAULT=150` was present in what was actually deployed -- not just what exists in the repository today.

3. **Check the Jan 20 deployment changelog for other concurrent changes.** Review the full diff or release notes for the Jan 20 deployment to identify whether other changes (new endpoints, changed authentication, traffic routing, upstream dependencies) were included that could explain the spike independently of any rate-limit change.

---

## replicate-2__CANDIDATE_B

[REDACTED PROCESS PREAMBLE]

## Claims Ledger

| # | Claim | Type | Evidence | Confidence | Counter-evidence |
|---|-------|------|----------|------------|------------------|
| 1 | The source code hardcodes the rate-limit default to 200 and uses that value in `apply_limit` unless a per-user override exists. | Observation | [A]: `DEFAULT_LIMIT = 200`; `apply_limit(user)` uses `DEFAULT_LIMIT` unless per-user override exists. | 0.9 | None from the provided snippets. Slight uncertainty (0.9 not 1.0) because we only see a summary of the code, not the full implementation -- there could be env-var reading logic not shown. |
| 2 | The production environment config sets a different rate-limit default of 150, conflicting with the hardcoded source value of 200. | Observation | [B]: `RATE_LIMIT_DEFAULT=150` in `config/prod.env`. [A]: `DEFAULT_LIMIT = 200` in source. | 0.95 | None. Both values are directly observed. The conflict itself is a factual observation, not an inference. |
| 3 | The effective default enforced today is most likely the hardcoded value of 200 from the source code, because `apply_limit` references `DEFAULT_LIMIT` with no shown mechanism to read the environment variable. | Inference | [A]: `apply_limit(user)` uses `DEFAULT_LIMIT` (the hardcoded constant). No code path shown that reads `RATE_LIMIT_DEFAULT` from the environment. | 0.5 | [B]: prod.env sets `RATE_LIMIT_DEFAULT=150`, suggesting the operations team intended 150 to be active. [C]: Phase 2 documentation says the default should be 150 after Jan 15. The code snippet may be incomplete -- a loader or framework could inject the env var at startup. **Confidence is <= 0.6 because the code-vs-config conflict is unresolved: we cannot confirm whether the env var overrides the hardcoded value at runtime.** |
| 4 | The Phase 2 rollout (lowering the default from 200 to 150) was planned for after Jan 15 and aligns with the prod.env value, but there is no evidence it was fully applied to the deployed artifact by Jan 20. | Inference | [C]: "Phase 2 lowers default from 200 to 150 after Jan 15." [B]: prod.env already reflects 150. [D]: incident summary says "unclear whether limiter default changed in deployed artifact." | 0.5 | [A]: source code still shows `DEFAULT_LIMIT = 200`, suggesting the code-level change may not have been made. [D] explicitly flags uncertainty about the deployed state. **Confidence is <= 0.6 because the incident report itself declares the deployed state unclear, and the source code contradicts the intended rollout.** |
| 5 | There is insufficient evidence to conclude the Jan 20 spike was caused by a change in the rate-limit default. | Inference | [D]: "Unclear whether limiter default changed in deployed artifact." [A]: code still shows 200 (no code-level change evident). The causal link between a limit change and the spike is not established in any snippet -- no metrics, no correlation analysis, no deployment manifest confirming the config change was active. | 0.6 | [C]: Phase 2 was scheduled before Jan 20, and [B] shows 150 in prod.env, so a limit change is plausible. [D] does report a spike temporally near deployment. A causal relationship cannot be ruled out. **Confidence is exactly 0.6 because while the evidence leans toward insufficient proof of causation, the temporal coincidence and planned rollout keep the alternative hypothesis alive.** |

**Row count verification:** 1, 2, 3, 4, 5. Exactly 5 rows. Confirmed.

**Confidence threshold verification:**
- Claim 3: 0.5 (affected by code-vs-config conflict, <= 0.6). Confirmed.
- Claim 4: 0.5 (affected by code-vs-config conflict and incident uncertainty, <= 0.6). Confirmed.
- Claim 5: 0.6 (affected by conflicting evidence about whether the change was deployed, <= 0.6). Confirmed.

## Unknowns & Next Checks

1. **Check whether `apply_limit` reads environment variables at runtime.** Inspect the full implementation of `services/rate_limit.py` (beyond the summary) and any framework initialization code to determine if `RATE_LIMIT_DEFAULT` from `prod.env` overrides `DEFAULT_LIMIT` at startup or per-request. This resolves the code-vs-config conflict and determines the effective default (Claims 1, 2, 3).

2. **Check the Jan 20 deployment manifest or release artifact.** Retrieve the exact build/container image deployed on Jan 20 and compare its `rate_limit.py` and bundled environment config against the repository state. This resolves whether Phase 2's config change was present in the deployed artifact (Claims 4, 5) and directly addresses the gap flagged in [D].

3. **Check rate-limit metrics (reject/throttle counts) before and after Jan 20.** Pull observability data (e.g., HTTP 429 response counts, request throughput, per-user limit hits) from the monitoring system for the period Jan 14-21. If the spike correlates with a drop in the effective limit from 200 to 150, causal linkage strengthens; if the spike occurred with the limit still at 200, the root cause lies elsewhere (Claim 5).

**Check count verification:** 1, 2, 3. Exactly 3 checks. Confirmed.

## Summary of Confidence Downgrades (Visibility Requirement)

- **Claim 3 downgraded to 0.5** (from what might otherwise be ~0.8 based on the code alone) because the production environment config [B] contradicts the hardcoded value [A], and we lack evidence about whether a runtime override mechanism exists.
- **Claim 4 downgraded to 0.5** because the incident report [D] explicitly states uncertainty about the deployed state, and the source code [A] contradicts the intended rollout described in [C].
- **Claim 5 held at 0.6** (the threshold ceiling for conflicting evidence) because no snippet provides direct causal evidence linking a limit change to the spike, yet the temporal and configurational circumstantial evidence prevents dismissing the hypothesis entirely.

---

# Replicate 3

---

## replicate-3__CANDIDATE_A

[REDACTED PROCESS PREAMBLE]

## Claims Ledger

| # | Claim | Type | Evidence | Confidence | Counter-evidence |
|---|-------|------|----------|------------|------------------|
| 1 | The code in `services/rate_limit.py` hardcodes `DEFAULT_LIMIT = 200` and `apply_limit(user)` references this value unless a per-user override exists. | Observation | [A]: `DEFAULT_LIMIT = 200`; `apply_limit(user)` uses `DEFAULT_LIMIT` unless per-user override exists. | 0.95 | None from provided snippets. The snippet may be incomplete (module-level env read not shown), which prevents 1.0. |
| 2 | The production environment configuration sets a different default of 150 via `RATE_LIMIT_DEFAULT=150`. | Observation | [B]: `config/prod.env` contains `RATE_LIMIT_DEFAULT=150`. | 0.95 | None directly. The env file exists, but whether the application reads it is unconfirmed. |
| 3 | The effective runtime default is ambiguous: the code hardcodes 200 [A] while prod config specifies 150 [B], and there is no evidence showing which value the application actually uses at runtime. | Inference | [A] states `DEFAULT_LIMIT = 200` used by `apply_limit`. [B] states `RATE_LIMIT_DEFAULT=150`. These conflict. [A] does not mention reading the env var. **Confidence downgraded because evidence directly conflicts: two authoritative sources (code and prod config) specify different values, and no runtime telemetry or initialization logic is provided to resolve which takes precedence.** | 0.5 | [A] suggests the hardcoded value is used (no env read mentioned). [B] suggests prod intended 150. Without seeing the initialization path, neither can be confirmed as the effective value. |
| 4 | The Phase 2 rollout was scheduled to lower the default from 200 to 150 after Jan 15, and a Jan 20 deployment occurred within that window. | Observation | [C]: "Phase 2 lowers default from 200 to 150 after Jan 15." [D]: "Spike observed after Jan 20 deployment." | 0.85 | No evidence that Phase 2 was actually included in the Jan 20 deployment artifact. The schedule existing does not confirm execution. |
| 5 | The Jan 20 traffic spike was caused by a change to the rate-limit default in the deployed artifact. | Inference | [D]: Spike after Jan 20 deployment. [C]: Phase 2 scheduled post-Jan 15 aligns temporally. **Confidence downgraded because: (a) [D] explicitly states "unclear whether limiter default changed in deployed artifact," directly undermining the causal claim; (b) temporal correlation alone (Jan 15 schedule, Jan 20 deploy, spike) does not establish causation; (c) no deployment diff, release manifest, or runtime metric confirms the default changed in that build.** | 0.3 | [D] itself flags uncertainty about whether the default changed. No deployment artifact or diff is provided. Alternative causes for the spike (e.g., organic traffic increase, other config changes, upstream service behavior) are not ruled out. |

**Row count verification:** 1, 2, 3, 4, 5. Exactly 5 rows. Confirmed.

**Confidence threshold verification:**
- Claim 3 (conflicting evidence between [A] and [B]): 0.5 <= 0.6. Confirmed.
- Claim 5 (conflicting/insufficient causal evidence): 0.3 <= 0.6. Confirmed.

## Answers to Questions

**1) Where is the effective default likely enforced today?**

This cannot be determined with confidence from the provided evidence. The code ([A]) hardcodes `DEFAULT_LIMIT = 200` and the snippet shows `apply_limit(user)` using that value directly, with no mention of reading environment variables. The prod config ([B]) sets `RATE_LIMIT_DEFAULT=150`, but nothing in the provided snippets confirms the application reads this variable. If the code does not read the env var, the effective default is 200 (from [A]). If there is an unshown initialization path that loads the env var into `DEFAULT_LIMIT`, it would be 150 (from [B]). The evidence conflicts, so confidence in either answer is at most 0.5.

**2) Is there enough evidence to claim the Jan 20 spike was caused by a default-limit change?**

No. The evidence is insufficient. There is temporal correlation (Phase 2 scheduled after Jan 15, spike after Jan 20 deployment), but the incident summary [D] itself explicitly states it is "unclear whether limiter default changed in deployed artifact." No deployment diff, build manifest, or runtime metric is provided to confirm the default was actually changed. Alternative causes for the spike are not addressed or ruled out. Confidence in a causal claim is 0.3.

## Unknowns & Next Checks

1. **Inspect the initialization path of `DEFAULT_LIMIT` in `services/rate_limit.py`:** Read the full module (not just the snippet) to determine whether `DEFAULT_LIMIT` is overwritten at import time by an environment variable read (e.g., `DEFAULT_LIMIT = int(os.environ.get("RATE_LIMIT_DEFAULT", 200))`). This resolves the conflict between [A] and [B] and answers where the effective default is enforced.

2. **Retrieve the deployment manifest or release diff for the Jan 20 deployment:** Examine the CI/CD artifact, release tag, or deploy log to confirm whether the Jan 20 build included the Phase 2 rate-limit change (i.e., whether `DEFAULT_LIMIT` or the env var value was modified in that release). This is the minimum evidence needed to move Claim 5 above 0.3 confidence.

3. **Pull rate-limit telemetry (enforced limit values) from the monitoring system for Jan 19-21:** Compare the actual rate-limit value applied to requests before and after the Jan 20 deployment. If the enforced limit shifted from 200 to 150 (or vice versa) coinciding with the spike, this provides runtime evidence of a causal link independent of code review or config inspection.

**Check count verification:** 1, 2, 3. Exactly 3 checks. Confirmed.

---

## replicate-3__CANDIDATE_B

[REDACTED PROCESS PREAMBLE]

## Claims Ledger

| Claim | Type | Evidence | Confidence | Counter-evidence |
|-------|------|----------|------------|------------------|
| 1. The code-level default rate limit is 200, as hardcoded in `services/rate_limit.py`. | Observation | [A] `DEFAULT_LIMIT = 200`; `apply_limit(user)` uses this value unless per-user override exists. | 0.9 | None from provided snippets. Minor uncertainty: the snippet may be incomplete or stale relative to deployed code. |
| 2. The production environment config sets the default rate limit to 150, consistent with Phase 2 of the rollout plan. | Observation | [B] `RATE_LIMIT_DEFAULT=150`; [C] Phase 2 lowers default from 200 to 150 after Jan 15. | 0.85 | It is unknown whether the env var is actually consumed by `apply_limit()`. The code snippet [A] does not reference environment variables, so this config value may be inert. |
| 3. The effective default enforced today is likely 200 (from code), not 150 (from env), because `apply_limit()` references only the hardcoded constant. | Inference | [A] describes behavior using `DEFAULT_LIMIT` with no mention of env-var lookup; the code and config disagree (200 vs. 150), and absent evidence of env-var consumption, the code constant governs. | 0.5 | [B] and [C] together suggest intent to operate at 150. The code snippet [A] may be an incomplete representation — the function could read env vars in logic not shown. Confidence is capped at 0.5 because the conflict between [A] and [B] is unresolved: we lack the full implementation of `apply_limit()`. |
| 4. The Jan 20 spike is temporally correlated with the Phase 2 rollout window (post-Jan 15), making a default-limit change a plausible contributing factor. | Inference | [C] Phase 2 targets post-Jan 15; [D] spike observed after Jan 20 deployment — timing aligns. | 0.45 | [D] explicitly states causality is unclear. The code [A] still shows 200, meaning Phase 2 may not have been fully applied. Temporal correlation alone does not establish causation. Multiple deployment changes could coincide. Confidence is capped at 0.45 because direct counter-evidence exists: [D]'s own uncertainty admission, and the code/config mismatch leaves the deployed artifact's actual behavior unknown. |
| 5. There was a rollout/rollback inconsistency: the env config reflects Phase 2 (150) while the code retains the pre-Phase-2 value (200), suggesting either an incomplete rollout or a partial rollback. | Inference | [A] `DEFAULT_LIMIT = 200` vs. [B] `RATE_LIMIT_DEFAULT=150`; [C] documents both the Phase 2 change and rollback procedure. The two sources disagree on the current default, which is consistent with one layer being updated and the other not. | 0.6 | It is possible that the architecture intentionally separates code defaults from env overrides (env takes precedence at runtime), and this is normal operating state rather than an inconsistency. Without understanding the override hierarchy, this claim remains uncertain — hence confidence capped at 0.6 due to the unresolved conflict between [A] and [B]. |

## Summary of Reasoning

**Q1 (Where is the effective default enforced today?):** The evidence conflicts. The code says 200 [A], the env config says 150 [B], and the rollout plan intended 150 [C]. Without knowing whether `apply_limit()` reads the environment variable, the answer is indeterminate. The code-level evidence slightly favors 200 because the described behavior references only the hardcoded constant, but this is low confidence (0.5).

**Q2 (Is there enough evidence to claim the Jan 20 spike was caused by a default-limit change?):** No. The temporal correlation exists (Claims 4), but the incident report itself [D] flags the causal link as unclear. The code/config mismatch means we do not even know what limit was active at deployment time. Confidence for the causal claim is 0.45 — below the threshold for a defensible assertion. The three checks above are necessary before any causal claim can be made.

## Unknowns & Next Checks

1. **Check the full implementation of `apply_limit()`**: Read the complete source of `services/rate_limit.py` to determine whether it reads `RATE_LIMIT_DEFAULT` from environment variables at runtime, which would resolve whether the effective default is 200 (code) or 150 (env). This is the single highest-value check — it resolves Claims 2, 3, and 5.

2. **Check the deployed artifact from the Jan 20 release**: Inspect the deployment manifest, container image, or release tag to confirm which version of `rate_limit.py` and which env config were bundled in the Jan 20 deployment. This directly addresses [D]'s stated uncertainty and would confirm or refute Claim 4.

3. **Check application logs or metrics around Jan 20 for the actual enforced rate-limit value**: Query request logs or rate-limiter metrics (e.g., rejected-request counts, limit headers returned to clients) from Jan 19-21 to observe the limit that was operationally in effect. This provides runtime evidence independent of both code and config, triangulating Claims 3 and 4.
