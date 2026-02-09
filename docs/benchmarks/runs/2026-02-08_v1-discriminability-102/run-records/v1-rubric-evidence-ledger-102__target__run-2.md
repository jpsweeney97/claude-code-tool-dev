# Run Record: v1-rubric-evidence-ledger-102 / target / run-2

**Run ID:** 2026-02-08_v1-discriminability-102

## Metadata

- **scenario_id:** `v1-rubric-evidence-ledger-102`
- **condition:** `target`
- **replicate:** run-2
- **injected_body:** BENCH_REFERENCE_EVIDENCE_CALIBRATION_v1.0.0
- **oracle_type:** `rubric_blinded`
- **oracle_commands:** N/A (rubric scoring)
- **blinding_required:** yes
- **observability_mode:** Mode A (self-report)
- **allowed_tools_expectation:** no_web
- **skill_file:** `.claude/skills/scenario-evidence-ledger/SKILL.md`
- **invocation_method:** Skill tool (`Skill(skill: "scenario-evidence-ledger")`)

## Preflight

```
$ git diff -- packages/mcp-servers/claude-code-docs/
(empty — clean)

$ ls .claude/skills/
claude-md-improver  creating-skills  format-export  improving-skills  writing-principles
(no leftover scenario dirs)
```

## Output

I'll work through this evidence analysis task systematically, following the loaded skill instructions. Let me begin by examining each snippet, labeling claims, and building the ledger.

---

## Process

### Step 1: Identify all claims I can extract from the evidence

**From Snippet [A] (services/rate_limit.py):**
- Observation: `DEFAULT_LIMIT` is hardcoded to 200 in the source code.
- Observation: `apply_limit(user)` uses `DEFAULT_LIMIT` unless a per-user override exists.

**From Snippet [B] (config/prod.env):**
- Observation: The production environment variable `RATE_LIMIT_DEFAULT` is set to 150.
- Observation: `RATE_LIMIT_BURST` is set to 20 in the prod environment config.

**From Snippet [C] (docs/ops/rate-limit-rollout.md):**
- Observation: Documentation states Phase 2 lowers the default from 200 to 150 after Jan 15.
- Observation: Documentation states rollback restores the default to 200.

**From Snippet [D] (incidents/INC-1427-summary.md):**
- Observation: A spike was observed after the Jan 20 deployment.
- Observation: The incident summary states it is "unclear whether limiter default changed in deployed artifact."

### Step 2: Identify conflicts

**Critical conflict:** Snippet [A] hardcodes `DEFAULT_LIMIT = 200`, but Snippet [B] sets the environment variable `RATE_LIMIT_DEFAULT=150`. The code in [A] shows `apply_limit(user)` uses `DEFAULT_LIMIT` -- there is no evidence it reads from the environment variable. This means the prod.env value of 150 may or may not be consumed by the running application. The two values (200 vs. 150) are in direct tension, and we lack evidence about whether the code reads the env var at runtime to override the hardcoded value.

**Second conflict:** The rollout doc [C] says Phase 2 lowers the default to 150 after Jan 15, which aligns with [B]'s env config of 150. But the code [A] still shows 200. This suggests either: (a) the code was not updated to reflect Phase 2, (b) the env var is meant to override the code at runtime via a mechanism not shown, or (c) the rollout was incomplete.

**Relevance to incident [D]:** The Jan 20 spike occurred after Phase 2's Jan 15 cutover date. The incident summary itself says it is "unclear" whether the limiter default changed. If the hardcoded 200 was still effective (env var not consumed), then the rate limit was never lowered, meaning the spike has a different cause. If the env var was consumed, the limit dropped from 200 to 150, which could cause rejected requests to spike -- or could reduce load spikes depending on interpretation.

### Step 3: Determine which question the conflict affects and apply confidence thresholds

**Question 1 (Where is the effective default enforced today?):** The conflict between [A] (200 hardcoded) and [B] (150 in env) directly affects this. Confidence for any claim about the effective value must be <= 0.6.

**Question 2 (Was the Jan 20 spike caused by a default-limit change?):** The incident summary [D] itself says "unclear." Combined with the code-vs-config conflict, confidence must be <= 0.6.

### Step 4: Build the claims ledger with exactly 5 rows

I need to select 5 claims that address both questions meaningfully. Let me draft them and then count to verify.

### Step 5: Build the "Unknowns & Next Checks" section with exactly 3 checks

---

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

---

## Unknowns & Next Checks

1. **Check whether `apply_limit` reads environment variables at runtime.** Inspect the full implementation of `services/rate_limit.py` (beyond the summary) and any framework initialization code to determine if `RATE_LIMIT_DEFAULT` from `prod.env` overrides `DEFAULT_LIMIT` at startup or per-request. This resolves the code-vs-config conflict and determines the effective default (Claims 1, 2, 3).

2. **Check the Jan 20 deployment manifest or release artifact.** Retrieve the exact build/container image deployed on Jan 20 and compare its `rate_limit.py` and bundled environment config against the repository state. This resolves whether Phase 2's config change was present in the deployed artifact (Claims 4, 5) and directly addresses the gap flagged in [D].

3. **Check rate-limit metrics (reject/throttle counts) before and after Jan 20.** Pull observability data (e.g., HTTP 429 response counts, request throughput, per-user limit hits) from the monitoring system for the period Jan 14-21. If the spike correlates with a drop in the effective limit from 200 to 150, causal linkage strengthens; if the spike occurred with the limit still at 200, the root cause lies elsewhere (Claim 5).

**Check count verification:** 1, 2, 3. Exactly 3 checks. Confirmed.

---

## Summary of Confidence Downgrades (Visibility Requirement)

- **Claim 3 downgraded to 0.5** (from what might otherwise be ~0.8 based on the code alone) because the production environment config [B] contradicts the hardcoded value [A], and we lack evidence about whether a runtime override mechanism exists.
- **Claim 4 downgraded to 0.5** because the incident report [D] explicitly states uncertainty about the deployed state, and the source code [A] contradicts the intended rollout described in [C].
- **Claim 5 held at 0.6** (the threshold ceiling for conflicting evidence) because no snippet provides direct causal evidence linking a limit change to the spike, yet the temporal and configurational circumstantial evidence prevents dismissing the hypothesis entirely.

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
$ trash .claude/skills/scenario-evidence-ledger
(success — directory removed)

$ ls .claude/skills/
claude-md-improver  creating-skills  format-export  improving-skills  writing-principles
(clean)
```

**Confirmation:** Did NOT run `git checkout -- .`.

## Notes

- **Run status:** COMPLETED
- Part of discriminability experiment (not pilot); tests whether rubric scoring can detect skill effects at N=3.
- Runner produced explicit verification steps: row count verification ("1, 2, 3, 4, 5. Exactly 5 rows. Confirmed."), confidence threshold verification (checked each conflicted claim against <=0.6 rule), check count verification ("1, 2, 3. Exactly 3 checks. Confirmed.").
- Runner added a "Summary of Confidence Downgrades (Visibility Requirement)" section not present in baseline runs — direct behavioral signature of injected skill's "make the downgrade visible" instruction.
- Injected body matches canonical definition at `docs/benchmarks/bench-skill-bodies_v1.0.0.md`.
