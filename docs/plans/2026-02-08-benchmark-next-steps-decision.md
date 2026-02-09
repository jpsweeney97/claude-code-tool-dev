# How to proceed after Benchmark v1 pilot FAIL

## Context
- Protocol: decision-making.framework@1.0.0
- Stakes level: adequate
- Decision trigger: Benchmark v1 pilot failed (0/3 improvement signals, 1 regression). Two benchmark cycles (v0 + v1 pilot) have yielded no clear positive signal. Need to decide whether to iterate, pivot, or stop.
- Time pressure: no constraint

## Entry Gate
- Stakes level: adequate
- Rationale: Reversibility is easy (can always run another pilot), blast radius is localized (benchmark project only), cost of error is medium (wasted sessions), uncertainty is moderate. Two factors in "rigorous" but blast radius firmly in "adequate" — this is an internal research project, not production code.
- Time budget: no constraint
- Iteration cap: 2
- Evidence bar: clear rationale for why the chosen path addresses the identified root causes (dimension coupling, ceiling effects, weak discriminability) and doesn't repeat the same mistakes
- Allowed skips: deep stakeholder analysis (sole stakeholder is the user); sensitivity analysis (skip, options are qualitatively different enough)
- Escalation trigger: if I can't distinguish between "skills don't work" and "measurement can't detect skill effects" — this is a critical uncertainty
- Initial frame: What should we do next with the benchmark project?
- Known constraints: each benchmark cycle costs 6+ sessions; pilot gate rules are deterministic
- Known stakeholders: the user (wants to know if skills improve Claude's output quality)

## Frame

### Decision Statement
Given two benchmark cycles with no clear positive signal, what is the most efficient next step to determine whether skills produce measurable output quality improvements?

### Constraints
- C1: Each full benchmark cycle costs ~6 sessions of execution + 1 evaluation session
- C2: Pilot gate rules require delta >= 2 AND critical dimension lift (can't be loosened without losing rigor)
- C3: N=1 pilot is inherently noisy — a single run can be dominated by one architectural choice (as 101 showed)
- C4: Must preserve blinding discipline in any evaluation

### Criteria
| Criterion | Weight | Definition |
|-----------|--------|------------|
| Diagnostic yield | 5 | Does this approach answer the fundamental question: "can rubric scoring detect skill effects?" |
| Effort efficiency | 4 | Learning gained per session invested |
| Root cause coverage | 4 | Addresses identified problems (coupling, ceilings, discriminability) |
| Risk of same outcome | 3 | How likely to produce another FAIL/INCONCLUSIVE |

### Assumptions
- A1: Skills do produce behavioral differences (verified — target in 102 showed explicit counting, 103 showed structured confidence downgrades)
- A2: Behavioral differences should translate to rubric score differences if rubrics are well-designed (unverified — this is the key question)
- A3: N=1 noise was the primary driver of the 101 regression, not skill harmfulness (unverified but likely — option selection cascaded through coupled dimensions)

### Scope
- In bounds: benchmark methodology, scenario design, rubric design, measurement approach
- Out of bounds: skill content redesign (skills are fixed for benchmarking purposes), execution architecture (already validated)
- Related decisions: whether to continue investing in quantitative skill evaluation at all

### Reversibility
Easy. Any option can be abandoned or redirected without lasting cost beyond time spent.

### Dependencies
- Depends on: pilot failure diagnosis (completed — dimension coupling + ceiling effects identified)
- Blocks: full v1 replication (gated behind pilot pass)

### Downstream Impact
- Enables: either a revised pilot or a principled decision to stop benchmarking
- Precludes: nothing permanently

## Options Considered

### Option 1: Redesign 101 rubric + harden 102/103, re-pilot
- Description: Decouple 101's rubric dimensions (score option diversity independently from recommendation quality). Increase difficulty on 102/103 to push scores below ceiling. Re-run full 6-run pilot.
- Trade-offs: Directly addresses identified problems (coupling + ceilings); costs another full pilot cycle (~7 sessions). Doesn't test whether rubric scoring CAN detect skill effects even when dimensions are well-designed.

### Option 2: Targeted discriminability experiment
- Description: Skip the full pilot infrastructure. Pick scenario 102 (where we already observed behavioral differences — explicit counting in target). Run N=3 baseline + N=3 target with the CURRENT rubric. See if the behavioral difference consistently produces rubric score separation.
- Trade-offs: Directly tests assumption A2 ("behavioral differences translate to score differences") with minimal effort. Doesn't fix 101 or the full suite, but answers the most important question first. If rubric can't detect differences even when behavioral change is obvious, redesigning scenarios is pointless.

### Option 3: Pivot to behavioral (non-rubric) measurement
- Description: Instead of rubric scoring, measure skill effects via behavioral markers: does the target produce verification steps? Does it count explicitly? Does it structure confidence as base-then-downgrade? These are binary/countable, not rubric-scored.
- Trade-offs: Measures what skills actually change (process) rather than what they might not change (output quality). Easier to detect. But measures a different thing — "does the skill change behavior?" not "does the skill improve quality." The user presumably cares about quality, not just behavioral compliance.

### Option 4: Null (stop benchmarking)
- Description: Accept that two benchmark cycles showed no clear quality improvement. Use skills based on qualitative assessment ("they seem to help with structure and process") without quantitative proof. Redirect effort to building better skills rather than proving existing ones work.
- Trade-offs: Saves significant effort. Honest about current evidence. Loses the possibility of quantitative validation. Risks abandoning a measurement approach that might work with better rubrics.

## Evaluation

### Criteria Scores (0-5, weighted)
| Option | Diagnostic yield (5) | Effort efficiency (4) | Root cause coverage (4) | Risk of same outcome (3) | Total |
|--------|---------------------|----------------------|------------------------|-------------------------|-------|
| 1: Redesign + re-pilot | 3 | 2 | 4 | 2 | 15+8+16+6 = 45 |
| 2: Targeted experiment | 5 | 5 | 2 | 3 | 25+20+8+9 = 62 |
| 3: Behavioral markers | 4 | 4 | 3 | 4 | 20+16+12+12 = 60 |
| 4: Null (stop) | 2 | 5 | 0 | 5 | 10+20+0+15 = 45 |

Score rationale:
- **Option 1** scores low on diagnostic yield (3) because it tests "can a better rubric detect differences" but not the more fundamental "can rubric scoring detect skill effects at all." Low efficiency (2) — another 7-session cycle. High root cause coverage (4) since it fixes the identified issues. But high risk of same outcome (2) — ceiling effects may persist even with harder scenarios, and N=1 noise remains.
- **Option 2** scores highest on diagnostic yield (5) because it directly tests the key assumption (A2) with minimal confounds. Highest efficiency (5) — 6 runs + 1 scoring session, but scoped to one scenario with a known behavioral difference. Low root cause coverage (2) — doesn't fix 101 or ceilings, but deliberately defers that. Moderate risk of same outcome (3) — N=3 helps with noise, but rubric resolution might still be too coarse.
- **Option 3** scores well on diagnostic yield (4) — would conclusively show skill behavioral effects, but pivots the question away from quality measurement. Good efficiency (4). Moderate root cause coverage (3) — addresses ceiling effects by changing the measurement type. Low risk of same outcome (4) — binary/count measures avoid rubric ceiling issues.
- **Option 4** scores low on diagnostic yield (2) — we learn nothing new. Highest efficiency (5) — zero cost. No root cause coverage (0). No risk of failure (5).

### Information Gaps
- **Critical:** We don't know if rubric scoring can detect skill effects EVEN WHEN behavioral differences are obvious. Option 2 fills this gap directly.
- **Moderate:** We don't know if 101's regression was noise or systematic. N=3 on 101 would answer this, but it's less important than the rubric-detection question.

### Bias Check
- **Sunk cost risk:** HIGH. Two benchmark cycles invested. Natural pull toward "iterate harder" (Options 1). Check: scoring as if starting fresh. If someone showed me this evidence and asked "should you spend 7 more sessions on rubric redesign?" — I'd say "not until you've tested whether rubric scoring works at all."
- **Familiarity bias:** Moderate pull toward rubric-based approaches since that's what's been built. Option 3 challenges this.
- **Action bias:** Moderate. Options 1-3 all involve doing something. The null option is genuinely worth considering — the qualitative evidence that skills change behavior may be sufficient.

## Pressure Test

### Arguments Against Frontrunner (Option 2)

1. **Objection:** "It only tests one scenario. Even if 102 shows rubric-detectable differences, 101 and 103 might not."
   - Response: True, but the question isn't "do all scenarios work?" — it's "CAN rubric scoring detect skill effects at all?" One positive example answers that. If it can't detect differences even where behavioral change is most obvious, no amount of scenario redesign will help.

2. **Objection:** "N=3 might still be too low. You could get a +1 average and still not clear the +2 threshold."
   - Response: The goal of this experiment isn't to pass the pilot gate. It's to measure the distribution of score deltas. If 3 runs show deltas of +1, +1, +0, that's diagnostic ("rubric can't detect behavioral differences"). If they show +3, +1, +2, that's also diagnostic ("rubric CAN detect, 101's regression was noise, proceed with redesign").

3. **Objection:** "You're cherry-picking the best scenario."
   - Response: Deliberately. This is a diagnostic experiment, not a benchmark. We pick the scenario most likely to show a difference. If the best case fails, the general case certainly does.

### Disconfirmation Attempt
- Sought: reasons Option 2 would be a waste of time
- Found: If the answer is "rubric can detect with N=3 on 102" we still need to fix 101 and 103 before a real pilot → Option 2 doesn't REPLACE Option 1, it just gates whether Option 1 is worth doing. This is a feature, not a bug — it's the cheapest possible gate.

## Decision

**Choice:** Option 2 — Targeted discriminability experiment on scenario 102, N=3 per condition.

**Trade-offs Accepted:**
- Doesn't fix scenario 101 or the full suite (deferred until we know if rubric detection works)
- Doesn't address the question of overall skill quality improvement (only tests detection capability)
- Cherry-picks the best-case scenario (intentionally — diagnostic, not benchmark)

**Confidence:** Medium-High. The logic is sound (test the key assumption first), the effort is low (~7 sessions), and the outcome is diagnostic regardless of direction.

**Caveats:**
- If result is "rubric detects differences" → proceed to Option 1 (redesign 101 + harden 102/103)
- If result is "rubric cannot detect differences even on 102" → pivot to Option 3 (behavioral markers) or Option 4 (stop benchmarking)
- If result is ambiguous (mixed deltas, e.g., +2, 0, +1) → add N=3 more runs before deciding

## Iteration Log
| Pass | Frame Changes | Frontrunner | Key Findings |
|------|---------------|-------------|--------------|
| 1 | None | Option 2 | Sunk cost bias toward Option 1 identified; Option 2 is cheapest gate for the critical assumption |

## Exit Gate
- [x] All outer loop activities complete (O1-O9 at adequate depth)
- [x] All inner loop activities complete (I1-I9 at adequate depth; I10 light; I11-I13 skipped per allowed skips)
- [x] Convergence indicators met (frontrunner stable for 1 pass; trade-offs stated; criteria defined)
- [x] Trade-offs explicitly documented
- [x] Decision defensible under scrutiny
