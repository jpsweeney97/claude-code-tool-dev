# Run Record: v1-rubric-evidence-ledger-102 / target / run-3

**Run ID:** 2026-02-08_v1-discriminability-102

## Metadata

- **scenario_id:** `v1-rubric-evidence-ledger-102`
- **condition:** `target`
- **replicate:** run-3
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

I'll work through this evidence analysis task systematically, following the loaded skill instructions. Let me first examine the scenario carefully, then build the claims ledger.

---

## Process

### Step 1: Identify all evidence sources and their contents

I have four snippets:

- **[A] services/rate_limit.py** — Code sets `DEFAULT_LIMIT = 200`; `apply_limit(user)` uses this unless a per-user override exists.
- **[B] config/prod.env** — Environment config sets `RATE_LIMIT_DEFAULT=150` and `RATE_LIMIT_BURST=20`.
- **[C] docs/ops/rate-limit-rollout.md** — Operational doc states Phase 2 lowers default from 200 to 150 after Jan 15; rollback restores to 200.
- **[D] incidents/INC-1427-summary.md** — Incident report notes a spike after Jan 20 deployment; states it is unclear whether the limiter default changed in the deployed artifact.

### Step 2: Analyze Question 1 — Where is the effective default likely enforced today?

**Observations:**
- The code hardcodes `DEFAULT_LIMIT = 200` [A].
- The prod environment sets `RATE_LIMIT_DEFAULT=150` [B].
- These two values conflict: 200 vs 150.

**Key unknown:** Does `apply_limit(user)` read the environment variable `RATE_LIMIT_DEFAULT` at runtime, or does it only use the hardcoded `DEFAULT_LIMIT = 200`? Snippet [A] says it "uses DEFAULT_LIMIT unless per-user override exists" — it does not mention reading from environment. This suggests the code may ignore the env var entirely, making the effective default 200 despite prod.env saying 150.

However, it is also possible that `DEFAULT_LIMIT` is initialized from the environment variable elsewhere (e.g., at module load time) and the snippet only shows the fallback. This is uncertain.

### Step 3: Analyze Question 2 — Is there enough evidence to claim the Jan 20 spike was caused by a default-limit change?

**Observations:**
- A spike was observed after Jan 20 deployment [D].
- The incident summary itself states it is "unclear whether limiter default changed in deployed artifact" [D].
- Phase 2 was scheduled to lower the default after Jan 15 [C], so a Jan 20 deployment could plausibly include that change.
- But we have no deployment manifest, no diff, and no confirmation the Phase 2 change was included in the Jan 20 deploy.

**Assessment:** There is a temporal correlation (post-Jan 15 schedule, Jan 20 deployment, spike) but no direct causal evidence. The incident report explicitly flags this as unclear. Evidence is insufficient to assert causation.

### Step 4: Build the claims ledger with exactly 5 rows

I need to verify I produce exactly 5 rows. Let me draft them and count.

### Step 5: Check for evidence conflicts and apply confidence thresholds

The conflict between [A] (DEFAULT_LIMIT = 200) and [B] (RATE_LIMIT_DEFAULT=150) directly affects claims about the effective default. Any claim touching the effective runtime value must have confidence <= 0.6 per the skill instructions.

The causal claim about the Jan 20 spike also has conflicting/insufficient evidence: [D] explicitly states uncertainty, and no deployment artifact confirms the change. Confidence must be <= 0.6.

### Step 6: Verify counts

- Claims ledger rows: I will count explicitly after drafting.
- Unknowns & Next Checks: Must be exactly 3.

---

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

---

## Answers to Questions

**1) Where is the effective default likely enforced today?**

This cannot be determined with confidence from the provided evidence. The code ([A]) hardcodes `DEFAULT_LIMIT = 200` and the snippet shows `apply_limit(user)` using that value directly, with no mention of reading environment variables. The prod config ([B]) sets `RATE_LIMIT_DEFAULT=150`, but nothing in the provided snippets confirms the application reads this variable. If the code does not read the env var, the effective default is 200 (from [A]). If there is an unshown initialization path that loads the env var into `DEFAULT_LIMIT`, it would be 150 (from [B]). The evidence conflicts, so confidence in either answer is at most 0.5.

**2) Is there enough evidence to claim the Jan 20 spike was caused by a default-limit change?**

No. The evidence is insufficient. There is temporal correlation (Phase 2 scheduled after Jan 15, spike after Jan 20 deployment), but the incident summary [D] itself explicitly states it is "unclear whether limiter default changed in deployed artifact." No deployment diff, build manifest, or runtime metric is provided to confirm the default was actually changed. Alternative causes for the spike are not addressed or ruled out. Confidence in a causal claim is 0.3.

---

## Unknowns & Next Checks

1. **Inspect the initialization path of `DEFAULT_LIMIT` in `services/rate_limit.py`:** Read the full module (not just the snippet) to determine whether `DEFAULT_LIMIT` is overwritten at import time by an environment variable read (e.g., `DEFAULT_LIMIT = int(os.environ.get("RATE_LIMIT_DEFAULT", 200))`). This resolves the conflict between [A] and [B] and answers where the effective default is enforced.

2. **Retrieve the deployment manifest or release diff for the Jan 20 deployment:** Examine the CI/CD artifact, release tag, or deploy log to confirm whether the Jan 20 build included the Phase 2 rate-limit change (i.e., whether `DEFAULT_LIMIT` or the env var value was modified in that release). This is the minimum evidence needed to move Claim 5 above 0.3 confidence.

3. **Pull rate-limit telemetry (enforced limit values) from the monitoring system for Jan 19-21:** Compare the actual rate-limit value applied to requests before and after the Jan 20 deployment. If the enforced limit shifted from 200 to 150 (or vice versa) coinciding with the spike, this provides runtime evidence of a causal link independent of code review or config inspection.

**Check count verification:** 1, 2, 3. Exactly 3 checks. Confirmed.

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
- Runner produced explicit verification steps: row count verification ("1, 2, 3, 4, 5. Exactly 5 rows. Confirmed."), confidence threshold verification (checked conflicted claims against <=0.6 rule), check count verification ("1, 2, 3. Exactly 3 checks. Confirmed.").
- Runner included explicit "Step 6: Verify counts" in process, showing anticipatory count checking before drafting.
- Target run-3 framed Claim 3 differently from target run-2: used "ambiguous" framing rather than "most likely 200" — a more epistemically humble claim given the conflict.
- Injected body matches canonical definition at `docs/benchmarks/bench-skill-bodies_v1.0.0.md`.
