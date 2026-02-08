# Run Record: v1-rubric-evidence-ledger-102 / baseline / run-1

**Run ID:** 2026-02-08_benchmark-v1_pilot-01

## Metadata

- **scenario_id:** `v1-rubric-evidence-ledger-102`
- **condition:** `baseline`
- **replicate:** run-1
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
```

## Output

I'll analyze the provided snippets systematically to build a claims ledger. Let me trace through the evidence carefully.

## Process

### Step 1: Inventory the evidence sources

I have four snippets labeled [A] through [D]. I need to cross-reference them to answer the two questions and build a claims ledger.

### Step 2: Analyze each snippet

**[A] services/rate_limit.py** — Code-level evidence. `DEFAULT_LIMIT = 200` is hardcoded. `apply_limit(user)` uses this unless a per-user override exists. This is the enforcement point in the application code.

**[B] config/prod.env** — Environment configuration. `RATE_LIMIT_DEFAULT=150` and `RATE_LIMIT_BURST=20`. This suggests the production environment is configured to use 150, not 200. However, there is no evidence that `rate_limit.py` actually reads this environment variable. The code in [A] shows a hardcoded constant, not an `os.getenv()` call.

**[C] docs/ops/rate-limit-rollout.md** — Operational documentation. Phase 2 was planned to lower the default from 200 to 150 after Jan 15. Rollback restores to 200. This tells us intent, not necessarily what was deployed.

**[D] incidents/INC-1427-summary.md** — Incident report. Spike after Jan 20 deployment. Unclear whether the limiter default changed in the deployed artifact. This is a symptom report with an explicitly stated uncertainty.

### Step 3: Identify conflicts and gaps

**Key conflict:** The code [A] says `DEFAULT_LIMIT = 200`, but prod.env [B] says `RATE_LIMIT_DEFAULT=150`. If the code does not read the environment variable, the effective default is 200 regardless of what prod.env says. The rollout doc [C] says Phase 2 was supposed to lower it to 150, but if the code was never updated to read the env var, that change never took effect.

**Key gap:** We do not know whether `apply_limit()` reads `RATE_LIMIT_DEFAULT` from the environment at runtime. The snippet only shows a hardcoded constant. This is the critical unknown.

### Step 4: Answer the questions

**Q1: Where is the effective default likely enforced today?**

The code in [A] hardcodes `DEFAULT_LIMIT = 200`. Unless `apply_limit()` has logic (not shown in the snippet) that reads the environment variable from [B], the effective default is enforced by the hardcoded value in `services/rate_limit.py`. The env var in prod.env may be dead configuration.

**Q2: Is there enough evidence to claim the Jan 20 spike was caused by a default-limit change?**

No. The incident summary [D] itself states "Unclear whether limiter default changed in deployed artifact." The code [A] still shows 200, which is the pre-Phase-2 value. If the default never actually changed (because the code does not read the env var), then the spike cannot be attributed to a default-limit change. Even if it did change, correlation (spike after deployment) is not causation without further investigation.

---

## Claims Ledger

| # | Claim | Type | Evidence | Confidence | Counter-evidence |
|---|-------|------|----------|------------|------------------|
| 1 | The effective rate-limit default enforced in application code is 200 | Observation | [A] `DEFAULT_LIMIT = 200` is hardcoded in `services/rate_limit.py`; `apply_limit(user)` uses it unless per-user override exists | 0.8 | [B] `prod.env` sets `RATE_LIMIT_DEFAULT=150`, which could override the hardcoded value at runtime if the code reads env vars in logic not shown in the snippet |
| 2 | The prod environment configuration intends a default of 150 | Observation | [B] `RATE_LIMIT_DEFAULT=150` in `config/prod.env`; [C] Phase 2 plan to lower default from 200 to 150 after Jan 15 | 0.85 | No direct counter-evidence for the intent; the config file and rollout doc agree |
| 3 | The code and the environment config disagree on the effective default (200 vs 150) | Observation | [A] hardcodes 200; [B] configures 150; no evidence in the snippet that the code reads the env var | 0.6 | It is possible that `apply_limit()` contains env-var reading logic not shown in the snippet, which would resolve the conflict in favor of 150. Confidence capped at 0.6 because the evidence conflicts and we lack visibility into the full function body. |
| 4 | The Phase 2 rollout (lowering default to 150) may not have taken effect in the deployed artifact | Inference | [A] still shows `DEFAULT_LIMIT = 200` (not 150); [D] states "Unclear whether limiter default changed in deployed artifact"; the code-level evidence does not reflect the intended change from [C] | 0.6 | [B] shows the env var is set to 150, so if the runtime reads it, the rollout did take effect. Confidence capped at 0.6 because the code and config evidence point in opposite directions. |
| 5 | The Jan 20 spike cannot be conclusively attributed to a default-limit change | Inference | [D] explicitly flags uncertainty about whether the default changed; [A] still shows 200 (pre-change value); temporal correlation alone (spike after deployment) is insufficient for causation | 0.55 | [C] confirms a planned change around that timeframe; [B] shows prod config at 150; if the change did deploy and raised or lowered the effective limit unexpectedly, it could explain the spike. Confidence capped at 0.55 because the causal link is plausible but unverified in either direction. |

---

## Unknowns & Next Checks

1. **Check whether `apply_limit()` reads environment variables at runtime.** Inspect the full function body in `services/rate_limit.py` for any `os.getenv("RATE_LIMIT_DEFAULT")` or framework-level config injection that would override the hardcoded `DEFAULT_LIMIT = 200`. This resolves the code-vs-config conflict (Claims 1, 3, 4).

2. **Check the exact artifact deployed on Jan 20 for the value of `DEFAULT_LIMIT`.** Pull the deployed container image or build artifact from the Jan 20 release and inspect the frozen value in `services/rate_limit.py`. Compare it against the current repository HEAD. This directly answers whether the rollout changed the deployed default (Claims 4, 5).

3. **Check request-level logs or metrics around Jan 20 for actual rate-limit thresholds applied.** Query application logs or observability dashboards for the effective limit value used per-request before and after the Jan 20 deployment. This provides runtime evidence of what limit was actually enforced, independent of code or config (Claims 1, 5).

## Tool Trace

- No tools used (pure reasoning task)
- Runner self-reported its step-by-step analysis process

## Oracle Results

Rubric scoring deferred to blinded evaluation per `rubric_blinded` oracle type.

DO NOT self-score. Scores will be assigned by a separate evaluator in a blinded session.

## Confounders

- No tool usage observed (no web searches, no file reads beyond the skill prompt)
- No differential confounders identified for this run

## Cleanup

```
$ trash /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/scenario-evidence-ledger
(success — directory removed)

$ git checkout -- packages/mcp-servers/claude-code-docs/
(success)

$ git diff -- packages/mcp-servers/claude-code-docs/
(empty — clean)
```

**Confirmation:** Did NOT run `git checkout -- .`.

## Notes

- **Run status:** COMPLETED
- Scaffolded by Codex from pilot matrix.
- Runner produced exactly 5 claims as requested.
- Confidence values: 0.8, 0.85, 0.6, 0.6, 0.55 — two claims at or below 0.6 threshold where evidence conflicts.
- Runner included numbered process steps showing evidence cross-referencing.
