# Run Record: v1-rubric-evidence-ledger-102 / target / run-1

**Run ID:** 2026-02-08_benchmark-v1_pilot-01

## Metadata

- **scenario_id:** `v1-rubric-evidence-ledger-102`
- **condition:** `target`
- **replicate:** run-1
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
```

## Output

I'll work through this evidence analysis task systematically, following the loaded skill instructions. Let me begin by analyzing each snippet carefully before constructing the claims ledger.

---

## Process

### Step 1: Inventory the evidence sources

I have four snippets:

- **[A]** `services/rate_limit.py` — Code-level default of 200, with per-user override logic.
- **[B]** `config/prod.env` — Environment config sets `RATE_LIMIT_DEFAULT=150` and `RATE_LIMIT_BURST=20`.
- **[C]** `docs/ops/rate-limit-rollout.md` — Rollout plan: Phase 2 lowers default from 200 to 150 after Jan 15; rollback restores 200.
- **[D]** `incidents/INC-1427-summary.md` — Spike after Jan 20 deployment; unclear whether the limiter default changed in the deployed artifact.

### Step 2: Identify conflicts and tensions

**Conflict 1:** The code in [A] hardcodes `DEFAULT_LIMIT = 200`. The prod environment config in [B] sets `RATE_LIMIT_DEFAULT=150`. These are different values. The effective default depends on whether `apply_limit(user)` reads the environment variable or uses the hardcoded constant. [A] says it "uses DEFAULT_LIMIT unless per-user override exists" — it does *not* say it reads from the environment. This is a direct conflict: the code says 200, the config says 150.

**Conflict 2:** The rollout doc [C] says Phase 2 lowers the default to 150 after Jan 15. The incident [D] is dated Jan 20 and states it is "unclear whether limiter default changed in deployed artifact." So even after Phase 2's target date, there is uncertainty about what was actually deployed.

### Step 3: Assess each prospective claim

**Claim 1 (Question 1 — code-level default):** The code in [A] enforces a default of 200 via `DEFAULT_LIMIT`. This is a direct observation from the snippet.

**Claim 2 (Question 1 — config-level default):** The prod config in [B] specifies 150. This is also a direct observation. But whether this value is *read* by the code is not established — the code description in [A] references `DEFAULT_LIMIT` (the hardcoded constant), not an environment variable.

**Claim 3 (Question 1 — which one wins):** The effective default today is *likely* 200 from the code, because [A] describes `apply_limit` as using `DEFAULT_LIMIT` (the hardcoded value), with no mention of reading the environment config. However, this is an inference — the snippet is partial, and there could be initialization logic not shown that loads `RATE_LIMIT_DEFAULT` from the environment into `DEFAULT_LIMIT`. The conflict between [A] (200) and [B] (150) forces confidence down.

**Claim 4 (Question 2 — spike timing):** The spike occurred after the Jan 20 deployment [D], which is after the Phase 2 target date of Jan 15 [C]. This is an observation linking two timestamps.

**Claim 5 (Question 2 — causation):** Whether the spike was *caused* by a default-limit change is an inference. [D] explicitly states it is "unclear whether limiter default changed in deployed artifact." This is a direct counter-evidence statement against claiming causation. Confidence must be low.

### Step 4: Construct the ledger

I need exactly 5 rows. Let me count: Claims 1 through 5 above. That is 5. Verified.

I need to check the confidence threshold rule: "If evidence conflicts, confidence for affected claims must be <= 0.6." The conflicting evidence affects Claims 2, 3, and 5. I will set each of those at or below 0.6.

### Step 5: Construct the "Unknowns & Next Checks" section

I need exactly 3 checks. I will draft them and count before finalizing.

---

## Claims Ledger

| # | Claim | Type | Evidence | Confidence | Counter-evidence |
|---|-------|------|----------|------------|------------------|
| 1 | `apply_limit(user)` uses the hardcoded constant `DEFAULT_LIMIT = 200` as the baseline when no per-user override exists. | Observation | [A]: `DEFAULT_LIMIT = 200`; `apply_limit(user)` uses `DEFAULT_LIMIT` unless per-user override exists. | 0.85 | None from provided snippets. However, only a partial view of the code is available; initialization logic that overrides the constant at startup is not shown. |
| 2 | The production environment config sets a different default of 150, but there is no evidence the code reads this value. | Observation (value) / Inference (non-reading) | [B]: `RATE_LIMIT_DEFAULT=150`. [A]: describes `apply_limit` as using the hardcoded `DEFAULT_LIMIT`, with no mention of environment variable ingestion. | 0.5 | **Confidence downgraded to 0.5 because evidence conflicts.** [B] exists as a prod config presumably intended to be consumed, yet [A] shows no mechanism for reading it. The snippet of [A] may be incomplete — there could be an `__init__` or config-loader module not shown that sets `DEFAULT_LIMIT` from the environment. The conflict between a config file that *sets* a value and code that *appears not to read it* cannot be resolved from these snippets alone. |
| 3 | The effective default enforced today is likely 200 (the hardcoded value), not 150 (the config value). | Inference | [A]: code uses `DEFAULT_LIMIT = 200`. [B]: config says 150 but no linkage to code is shown. [C]: Phase 2 *planned* to lower to 150, implying it was not yet reflected in code at the time the plan was written. | 0.5 | **Confidence downgraded to 0.5 because evidence conflicts.** [B] sets 150 in prod config, and [C] describes a deliberate rollout to 150. If Phase 2 completed successfully, the effective default could be 150 via a mechanism not visible in [A]'s snippet. [D] adds further uncertainty: "unclear whether limiter default changed in deployed artifact." |
| 4 | The Jan 20 spike occurred after the Phase 2 target date (Jan 15) for lowering the default to 150. | Observation | [C]: Phase 2 lowers default after Jan 15. [D]: Spike observed after Jan 20 deployment. | 0.90 | None. Both dates are directly stated in the snippets. Minor caveat: "after Jan 15" in [C] is a planned date, not a confirmed execution date. |
| 5 | The Jan 20 spike was caused by a change in the rate-limit default. | Inference | Circumstantial only: [C] planned a default change around this period; [D] reports a spike after deployment in the same timeframe. | 0.3 | **Confidence downgraded to 0.3 because evidence conflicts and is insufficient.** [D] explicitly states: "Unclear whether limiter default changed in deployed artifact." This directly undermines a causal claim. No artifact diff, deploy log, or metric correlation is provided. The spike could have other causes (traffic pattern, code bug, upstream dependency). Temporal proximity alone does not establish causation. |

**Row count verification:** 1, 2, 3, 4, 5. Exactly 5 rows. Confirmed.

**Threshold verification for conflicting evidence:**
- Claim 2: 0.5 (<= 0.6). Confirmed.
- Claim 3: 0.5 (<= 0.6). Confirmed.
- Claim 5: 0.3 (<= 0.6). Confirmed.

---

## Answers to the Questions

**1) Where is the effective default likely enforced today?**

Based on the available evidence, the effective default is **likely enforced in `services/rate_limit.py` at the hardcoded value of 200**. The code in [A] explicitly sets `DEFAULT_LIMIT = 200` and uses it in `apply_limit(user)`. While `config/prod.env` [B] specifies 150, no evidence links the environment variable to the code path. However, confidence is moderate (0.5) because the code snippet is partial and a config-loading mechanism may exist outside the visible scope.

**2) Is there enough evidence to claim the Jan 20 spike was caused by a default-limit change?**

**No.** The evidence is insufficient to support a causal claim. The incident summary [D] itself states the relationship is "unclear." The only supporting evidence is temporal proximity between the Phase 2 rollout window [C] and the spike date [D], which is circumstantial. No deploy artifact diff, metric correlation, or rollback-confirms-fix evidence is provided. Confidence in the causal claim is 0.3.

---

## Unknowns & Next Checks

1. **Inspect the full initialization path of `services/rate_limit.py`:** Determine whether `DEFAULT_LIMIT` is reassigned at module load or application startup from `os.environ["RATE_LIMIT_DEFAULT"]` or a config loader. This resolves the conflict between [A] (200) and [B] (150) and answers definitively which value is enforced at runtime.

2. **Retrieve the Jan 20 deploy artifact manifest or diff:** Compare the deployed artifact's rate-limit configuration against the prior deployment. This directly addresses [D]'s stated uncertainty ("unclear whether limiter default changed in deployed artifact") and is required before any causal claim about the spike.

3. **Correlate the spike timeline with the rate-limit metric (requests rejected vs. requests allowed):** If the spike corresponds to a sudden increase in *allowed* requests (consistent with a higher or missing limit), that supports the default-change hypothesis. If the spike is in a different metric (latency, errors), the cause is likely unrelated to the rate limiter. This check provides the observational evidence needed to move Claim 5 above 0.3.

**Check count verification:** 1, 2, 3. Exactly 3 checks. Confirmed.

## Tool Trace

- No tools used (pure reasoning task)
- Runner self-reported its step-by-step analysis process
- Runner performed explicit count verification steps (row count, check count, threshold checks)

## Oracle Results

Rubric scoring deferred to blinded evaluation per `rubric_blinded` oracle type.

DO NOT self-score. Scores will be assigned by a separate evaluator in a blinded session.

## Confounders

- No tool usage observed (no web searches, no file reads beyond the skill prompt) — same as baseline
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
- Runner produced exactly 5 claims and exactly 3 next checks as requested.
- Runner performed explicit count verification ("Row count verification: 1, 2, 3, 4, 5. Exactly 5 rows. Confirmed.") — evidence of cardinality enforcement from the injected skill.
- Runner performed explicit threshold verification for conflicting-evidence claims (0.5, 0.5, 0.3 — all <= 0.6).
- Confidence values: 0.85, 0.5, 0.5, 0.90, 0.3 — three claims below 0.6 for conflicting evidence.
- Injected body matches canonical definition at `docs/benchmarks/bench-skill-bodies_v1.0.0.md` lines 47-65.
