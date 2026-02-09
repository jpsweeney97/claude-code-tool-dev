# Run Record: v1-rubric-evidence-ledger-102 / baseline / run-2

**Run ID:** 2026-02-08_v1-discriminability-102

## Metadata

- **scenario_id:** `v1-rubric-evidence-ledger-102`
- **condition:** `baseline`
- **replicate:** run-2
- **injected_body:** none (baseline)
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

I'll work through this systematically, analyzing the provided snippets to build a claims ledger about the rate limit configuration and the Jan 20 incident.

## Process

### Step 1: Inventory the Evidence

Let me catalog what each snippet provides:

**Snippet [A] - services/rate_limit.py:**
- Code-level default: `DEFAULT_LIMIT = 200`
- Logic: `apply_limit(user)` uses `DEFAULT_LIMIT` unless a per-user override exists
- This is the application code, the "hardcoded" fallback.

**Snippet [B] - config/prod.env:**
- Environment config: `RATE_LIMIT_DEFAULT=150`
- Environment config: `RATE_LIMIT_BURST=20`
- This is the production environment configuration, which presumably could override the code default.

**Snippet [C] - docs/ops/rate-limit-rollout.md:**
- Operational plan: Phase 2 lowers default from 200 to 150 after Jan 15
- Rollback procedure: restores default to 200
- This documents intent, not necessarily what was deployed.

**Snippet [D] - incidents/INC-1427-summary.md:**
- A spike was observed after Jan 20 deployment
- It is unclear whether the limiter default changed in the deployed artifact
- This is an incident record acknowledging uncertainty about root cause.

### Step 2: Analyze Key Questions

**Question 1: Where is the effective default likely enforced today?**

There is a conflict between [A] (code says 200) and [B] (prod.env says 150). The critical unknown is whether `apply_limit(user)` reads from the environment variable `RATE_LIMIT_DEFAULT` or only uses the hardcoded `DEFAULT_LIMIT = 200`. Snippet [A] states the function "uses DEFAULT_LIMIT unless per-user override exists" -- it does not mention reading from environment. This suggests the env var in [B] may not be consumed by the code, or that there is a separate config-loading layer not shown.

**Question 2: Is there enough evidence to claim the Jan 20 spike was caused by a default-limit change?**

The timeline is suggestive: Phase 2 planned for after Jan 15 [C], spike observed after Jan 20 [D]. But [D] explicitly states it is "unclear whether limiter default changed in deployed artifact." We also have a conflict between the code default (200) and the env config (150) -- if the env var is not wired into the code, the Phase 2 change may never have taken effect, meaning the spike has a different cause. There is correlation in timing but no confirmed causal mechanism.

### Step 3: Build the Claims Ledger

---

## Claims Ledger

| Claim | Type | Evidence | Confidence | Counter-evidence |
|-------|------|----------|------------|------------------|
| The application code defines a hardcoded default rate limit of 200 | Observation | [A]: `DEFAULT_LIMIT = 200` in `services/rate_limit.py` | 0.95 | None from provided snippets; minor residual uncertainty that the snippet may be outdated or from a non-deployed branch |
| The production environment is configured with a default rate limit of 150 | Observation | [B]: `RATE_LIMIT_DEFAULT=150` in `config/prod.env` | 0.9 | [A] shows `apply_limit(user)` uses `DEFAULT_LIMIT` (the hardcoded constant) with no mention of reading environment variables, so the env var may not be consumed by the running application |
| The effective default enforced today is 200 (the code constant), not 150 (the env var) | Inference | [A]: `apply_limit(user)` is described as using `DEFAULT_LIMIT` unless a per-user override exists, with no mention of environment-based config loading. The code and env config disagree (200 vs 150), suggesting the env var is not wired in. | 0.55 | [B] exists in `config/prod.env`, implying some deployment mechanism may inject it. [C] documents an intentional Phase 2 change to 150, suggesting an integration path was planned. Confidence is <=0.6 because the evidence directly conflicts: the code says 200, the env says 150, and we lack visibility into the config-loading layer that would resolve which wins. |
| The Phase 2 rollout (lowering the default to 150) was intended to be active by Jan 20 | Inference | [C]: Phase 2 planned "after Jan 15." [B]: prod.env already reflects 150. Timeline aligns with [D]'s Jan 20 deployment. | 0.6 | [D] explicitly states it is "unclear whether limiter default changed in deployed artifact," meaning the deployment may not have included the config change. [A] shows the code still defines 200, which may mean Phase 2 was only partially applied (env updated, code not updated to read it). Confidence is <=0.6 because the incident summary directly questions whether the change was deployed. |
| The Jan 20 spike was caused by a change in the rate limit default | Inference | [C]: Phase 2 timing (after Jan 15) coincides with [D]'s Jan 20 deployment. [B]: prod.env shows 150, consistent with the Phase 2 target. Temporal correlation exists. | 0.3 | [D]: "Unclear whether limiter default changed in deployed artifact" -- the incident team itself could not confirm causation. [A]: Code still shows `DEFAULT_LIMIT = 200` with no env-var integration visible, so the limit may never have changed in practice. Correlation in timing is not causation. Multiple confounders possible (deployment could have included other changes). Confidence is well below 0.6 because direct counter-evidence exists from the incident summary, and the causal mechanism (env var actually changing runtime behavior) is unverified. |

---

## Unknowns & Next Checks

1. **Check whether `apply_limit()` reads from environment variables at runtime.** Inspect the full implementation of `services/rate_limit.py` (and any config-loading module it imports) to determine whether `RATE_LIMIT_DEFAULT` from `prod.env` overrides the hardcoded `DEFAULT_LIMIT = 200`. This resolves the core conflict between snippets [A] and [B] and determines the effective default.

2. **Check the Jan 20 deployment artifact's actual configuration.** Pull the deployed container image, release tag, or deployment manifest from Jan 20 and inspect the bundled `prod.env` (or equivalent runtime config) to confirm whether `RATE_LIMIT_DEFAULT=150` was present in what was actually deployed -- not just what exists in the repository today.

3. **Check the Jan 20 deployment changelog for other concurrent changes.** Review the full diff or release notes for the Jan 20 deployment to identify whether other changes (new endpoints, changed authentication, traffic routing, upstream dependencies) were included that could explain the spike independently of any rate-limit change.

---

## Summary of Reasoning

**Question 1 (effective default today):** Most likely the code-level constant of 200, because `apply_limit()` as described references `DEFAULT_LIMIT` directly with no mention of environment variable loading. However, confidence is moderate (0.55) because `prod.env` exists with 150, and there may be a config-loading layer not shown in the snippets.

**Question 2 (causal link to Jan 20 spike):** No, there is not enough evidence to claim causation. The incident summary itself ([D]) flags uncertainty about whether the default changed in the deployed artifact. The code ([A]) still shows 200 with no visible mechanism to read the env var. While the timeline correlates (Phase 2 after Jan 15, spike after Jan 20), at least three unknowns remain unresolved: whether the env var is consumed, whether it was in the deployed artifact, and whether other deployment changes contributed. Confidence in the causal claim is 0.3.

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
- Runner produced complete claims ledger with all required structure (5 claims, type labels, confidence scores, counter-evidence, 3 next checks).
