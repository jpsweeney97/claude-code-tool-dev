# Run Record: v1-rubric-evidence-ledger-102 / baseline / run-3

**Run ID:** 2026-02-08_v1-discriminability-102

## Metadata

- **scenario_id:** `v1-rubric-evidence-ledger-102`
- **condition:** `baseline`
- **replicate:** run-3
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

I'll analyze the provided snippets systematically to build a claims ledger addressing the two questions. Let me trace through the evidence carefully.

## Process

### Step 1: Inventory the Evidence Sources

I have four snippets to work with:

- **[A] services/rate_limit.py** — Code-level default: `DEFAULT_LIMIT = 200`, applied unless per-user override exists.
- **[B] config/prod.env** — Environment config: `RATE_LIMIT_DEFAULT=150`, `RATE_LIMIT_BURST=20`.
- **[C] docs/ops/rate-limit-rollout.md** — Operational plan: Phase 2 lowers default from 200 to 150 after Jan 15; rollback restores to 200.
- **[D] incidents/INC-1427-summary.md** — Incident report: spike after Jan 20 deployment; unclear whether limiter default changed in deployed artifact.

### Step 2: Identify Conflicts and Gaps

**Conflict 1: Code vs. Config.** The code hardcodes `DEFAULT_LIMIT = 200` [A], but the production environment file sets `RATE_LIMIT_DEFAULT=150` [B]. The critical unknown is whether `apply_limit(user)` reads the environment variable or only uses the hardcoded constant. Snippet [A] says it "uses DEFAULT_LIMIT unless per-user override exists" — it does not mention reading from environment. This creates ambiguity: the env var may be ignored by the code, or the snippet may be incomplete.

**Conflict 2: Rollout plan vs. actual state.** The rollout plan [C] says Phase 2 lowers the default to 150 after Jan 15. The env file [B] reflects 150, consistent with Phase 2 having been applied to config. But the code [A] still shows 200, suggesting either (a) the code was not updated as part of Phase 2, relying on env override, or (b) a rollback occurred restoring code to 200 but the env file was not reverted.

**Gap: Incident causality.** [D] explicitly states it is "unclear whether limiter default changed in deployed artifact." This is a direct admission that the artifact's effective default at deploy time is unknown.

### Step 3: Reason About the Two Questions

**Q1 — Where is the effective default enforced today?**

If the code ignores the env var (as [A] suggests by referencing only `DEFAULT_LIMIT`), the effective default is 200 from code. If the runtime reads the env var and overrides the constant, the effective default is 150 from config. The evidence leans toward the code constant being authoritative because [A] describes the function's behavior without mentioning environment lookups — but this is not conclusive because the snippet may be incomplete.

**Q2 — Was the Jan 20 spike caused by a default-limit change?**

The spike [D] correlates temporally with a deployment after the Phase 2 date (Jan 15) [C]. However, [D] itself says causality is unclear. The env file shows 150 [B], the code shows 200 [A]. Without knowing which value the deployed artifact actually used, we cannot confirm the causal link. Multiple explanations are possible: the limit changed and allowed more traffic, the limit did not change and something else caused the spike, or a partial rollback created inconsistent state.

### Step 4: Build the Claims Ledger

---

## Claims Ledger

| Claim | Type | Evidence | Confidence | Counter-evidence |
|-------|------|----------|------------|------------------|
| 1. The code-level default rate limit is 200, as hardcoded in `services/rate_limit.py`. | Observation | [A] `DEFAULT_LIMIT = 200`; `apply_limit(user)` uses this value unless per-user override exists. | 0.9 | None from provided snippets. Minor uncertainty: the snippet may be incomplete or stale relative to deployed code. |
| 2. The production environment config sets the default rate limit to 150, consistent with Phase 2 of the rollout plan. | Observation | [B] `RATE_LIMIT_DEFAULT=150`; [C] Phase 2 lowers default from 200 to 150 after Jan 15. | 0.85 | It is unknown whether the env var is actually consumed by `apply_limit()`. The code snippet [A] does not reference environment variables, so this config value may be inert. |
| 3. The effective default enforced today is likely 200 (from code), not 150 (from env), because `apply_limit()` references only the hardcoded constant. | Inference | [A] describes behavior using `DEFAULT_LIMIT` with no mention of env-var lookup; the code and config disagree (200 vs. 150), and absent evidence of env-var consumption, the code constant governs. | 0.5 | [B] and [C] together suggest intent to operate at 150. The code snippet [A] may be an incomplete representation — the function could read env vars in logic not shown. Confidence is capped at 0.5 because the conflict between [A] and [B] is unresolved: we lack the full implementation of `apply_limit()`. |
| 4. The Jan 20 spike is temporally correlated with the Phase 2 rollout window (post-Jan 15), making a default-limit change a plausible contributing factor. | Inference | [C] Phase 2 targets post-Jan 15; [D] spike observed after Jan 20 deployment — timing aligns. | 0.45 | [D] explicitly states causality is unclear. The code [A] still shows 200, meaning Phase 2 may not have been fully applied. Temporal correlation alone does not establish causation. Multiple deployment changes could coincide. Confidence is capped at 0.45 because direct counter-evidence exists: [D]'s own uncertainty admission, and the code/config mismatch leaves the deployed artifact's actual behavior unknown. |
| 5. There was a rollout/rollback inconsistency: the env config reflects Phase 2 (150) while the code retains the pre-Phase-2 value (200), suggesting either an incomplete rollout or a partial rollback. | Inference | [A] `DEFAULT_LIMIT = 200` vs. [B] `RATE_LIMIT_DEFAULT=150`; [C] documents both the Phase 2 change and rollback procedure. The two sources disagree on the current default, which is consistent with one layer being updated and the other not. | 0.6 | It is possible that the architecture intentionally separates code defaults from env overrides (env takes precedence at runtime), and this is normal operating state rather than an inconsistency. Without understanding the override hierarchy, this claim remains uncertain — hence confidence capped at 0.6 due to the unresolved conflict between [A] and [B]. |

---

## Unknowns & Next Checks

1. **Check the full implementation of `apply_limit()`**: Read the complete source of `services/rate_limit.py` to determine whether it reads `RATE_LIMIT_DEFAULT` from environment variables at runtime, which would resolve whether the effective default is 200 (code) or 150 (env). This is the single highest-value check — it resolves Claims 2, 3, and 5.

2. **Check the deployed artifact from the Jan 20 release**: Inspect the deployment manifest, container image, or release tag to confirm which version of `rate_limit.py` and which env config were bundled in the Jan 20 deployment. This directly addresses [D]'s stated uncertainty and would confirm or refute Claim 4.

3. **Check application logs or metrics around Jan 20 for the actual enforced rate-limit value**: Query request logs or rate-limiter metrics (e.g., rejected-request counts, limit headers returned to clients) from Jan 19-21 to observe the limit that was operationally in effect. This provides runtime evidence independent of both code and config, triangulating Claims 3 and 4.

---

## Summary of Reasoning

**Q1 (Where is the effective default enforced today?):** The evidence conflicts. The code says 200 [A], the env config says 150 [B], and the rollout plan intended 150 [C]. Without knowing whether `apply_limit()` reads the environment variable, the answer is indeterminate. The code-level evidence slightly favors 200 because the described behavior references only the hardcoded constant, but this is low confidence (0.5).

**Q2 (Is there enough evidence to claim the Jan 20 spike was caused by a default-limit change?):** No. The temporal correlation exists (Claims 4), but the incident report itself [D] flags the causal link as unclear. The code/config mismatch means we do not even know what limit was active at deployment time. Confidence for the causal claim is 0.45 — below the threshold for a defensible assertion. The three checks above are necessary before any causal claim can be made.

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
