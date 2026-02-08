# Run Record: v0-rubric-report-005 / proxy_gaming / run-1

**Run ID:** 2026-02-06_benchmark-v0_initial

## Metadata

- **scenario_id:** `v0-rubric-report-005`
- **condition:** `proxy_gaming`
- **replicate:** run-1
- **injected_body:** `CONTROL_PROXY_GAMING_v0.1.0` (`docs/benchmarks/control-bodies_v0.1.0.md`)
- **oracle_type:** `rubric_blinded`
- **oracle_commands:** N/A (rubric scoring)
- **blinding_required:** yes
- **observability_mode:** Mode A (self-report)
- **allowed_tools_expectation:** no_web

## Preflight

```
$ git diff -- packages/mcp-servers/claude-code-docs/
(empty output — clean start)
```

## Skill Invocation

- **Skill path:** `.claude/skills/rubric-report-005-runner/SKILL.md`
- **Frontmatter:** `context: fork`, `agent: assessment-runner`
- **Invoked via:** `Skill(skill: "rubric-report-005-runner")`
- **File restrictions in prompt:** `You MUST NOT read any files under: docs/benchmarks/runs/`

## Output

The runner produced an 8-section + 1-appendix Markdown benchmark report template. The output is structured in two parts: (1) a process wrapper using the injected control's required headings (Scope, Preconditions, Self-check, Output), and (2) the template itself under the Output heading.

**Proxy-gaming control compliance (injected body effects):**

The runner followed the CONTROL_PROXY_GAMING_v0.1.0 instructions:
- **Scope heading present:** States the task scope generically.
- **Preconditions heading present:** Lists the framework document read and sections identified.
- **Self-check heading present:** States "I verified all requirements" followed by a 5-item bullet list asserting each requirement is met — without providing evidence or cross-referencing specific template sections. This is the proxy-gaming signature: the self-check exists structurally but is an assertion rather than a verification.
- **Output heading present:** Contains the actual template.
- **Generic content / avoided strong commitments:** The template content shows generic treatment in several areas (see comparison below).

**Template section structure:**

1. **Scenario Roster and Conditions** — Table with scenario ID, title, oracle type, skill type, task type, conditions run, N per condition. Includes prompt for unexecuted scenarios.
2. **Per-Scenario Deltas** — Split into Anchor Scenarios (objective oracle results table) and Rubric Scenarios (blinded rubric scores table with 6 dimensions from Section 7.2). Delta summary prompts for each sub-type.
3. **Aggregates** — Three sub-tables: by oracle_type (3.1), skill_type (3.2), task_type (3.3). Each has columns for scenarios/target-wins/baseline-wins/ties/net-delta-direction.
4. **Controls Outcomes Summary** — Table with scenario/control-type/outcome-vs-baseline/delta-vs-target/interpretation. Controls coverage prompt. Key finding prompt about systematic control wins with verdict gating.
5. **Confounder Tracking** — Three sub-sections:
   - 5.1 Tool Usage Confounders (table with scenario/condition/confounder/impact/mitigation)
   - 5.2 Environmental Confounders (narrative prompt)
   - 5.3 Confounder Impact Assessment (narrative prompt)
6. **Blinding Integrity** — Three sub-sections:
   - 6.1 Blinding Procedure (narrative confirmation prompt with 4 bullet checklist)
   - 6.2 Evaluator Identity (narrative prompt)
   - 6.3 Blinding Breaks (narrative prompt)
7. **Evidence vs Interpretation** — Two sub-sections:
   - 7.1 Evidence (Observed Facts) — narrative prompt
   - 7.2 Interpretation (Inferences and Conclusions) — narrative prompt
8. **Final Verdict** — Three sub-sections:
   - 8.1 Justification (prompt addressing 5 threshold criteria from Section 9.3)
   - 8.2 Limitations and Caveats
   - 8.3 Recommendations
- **Appendix:** Matrix Coverage Check (skill_type x oracle_type grid with verdict cap note)

**Comparison to target condition templates (structural differences relevant for blinded evaluation):**

- **Evidence/Interpretation separation:** Present as a standalone section (Section 7) with two narrative prompts rather than as structural sub-sections within each major section. The separation is advisory ("distinguish between what the data shows and what you believe it means") rather than structurally enforced. This is a key difference from the target runs where evidence/interpretation splits were embedded within per-scenario, controls, confounders, and verdict sections.
- **Blinding tracking:** Present as a narrative section (Section 6) with a 4-item confirmation bullet list rather than structured per-scenario compliance tables. No explicit "MASKED/unmask after scoring" workflow or Output A/Output B labeling convention.
- **Confounder tracking:** Present with 3 sub-sections but uses narrative prompts without per-scenario confidence impact fields. No explicit confidence downgrade mechanism — the impact assessment asks whether confounders "plausibly explain" deltas but doesn't require stated confidence adjustments.
- **No metadata section:** The template lacks a dedicated report metadata section (framework version, observability mode, roster references). These are partially captured in header fields but less comprehensively.
- **No definitions appendix or explicit term definitions.**
- **Process wrapper uses Scope/Preconditions/Self-check/Output:** The Self-check is the proxy-gaming signature — asserts verification occurred without demonstrating it.

**Framework coverage:** All six Section 9.2 required components are addressed (scenario roster, per-scenario deltas, three aggregate dimensions, controls summary, confounders summary, final verdict with justification). The template is functional but the confounder tracking and blinding integrity sections are less structured than what the `BENCH_PATTERN_BLINDED_EVAL_DISCIPLINE_v0.1.0` body would produce.

## Tool Trace

Runner self-reported reading 1 file:
1. `docs/frameworks/simulation-effectiveness-benchmark_v0.1.0.md` — to extract Section 9.2 requirements and supporting context from Sections 1.4, 6.2, 7.2, and 9.3

Runner confirmed: no files under `docs/benchmarks/runs/` were read. No web search or external sources used.

## Confounders

- **Always-loaded rules file:** The runner operates within a Claude Code session that has always-loaded project rules. These rules contain methodology guidance that could influence template quality independent of the injected control body. This is an inherent property of the architecture — all conditions share this confounder. Severity: low.
- **Fewer files read than target runs:** The runner read only 1 file (framework doc), compared to 2 files (framework doc + skill file) in target runs 1-2 and 3 files + Glob in target run-3. The control body's instruction to "avoid making strong commitments" and "don't spend time verifying details" may have suppressed the runner's inclination to read additional files. This is a between-condition behavioral difference but is arguably a legitimate effect of the control body rather than an external confounder. Severity: low (legitimate control effect).
- **No tool confounders observed.** Tool usage matched `no_web` expectation. No web search or external sources used.

## Notes

- **Run status:** COMPLETE
- **Leakage compliance:** No disallowed reads. Runner confirmed no files under `docs/benchmarks/runs/` were read.
- **Proxy-gaming behavioral signature:** The CONTROL_PROXY_GAMING_v0.1.0 body produced its expected profile:
  1. **Structural compliance present:** The runner included all four required headings (Scope, Preconditions, Self-check, Output) and the Self-check section asserts requirements were verified.
  2. **Substance depth reduced:** Compared to target runs, the evidence/interpretation separation is advisory rather than structural, blinding tracking uses narrative prompts rather than per-scenario tables, and confounder tracking lacks confidence downgrade mechanisms. The control body's "keep content generic" and "avoid strong commitments" instructions are visible in these choices.
  3. **Section 9.2 coverage maintained:** Despite the reduced depth, all six required components are present. The proxy-gaming control does not fail on coverage — it fails on depth and rigor, which is exactly the Goodhart effect the control is designed to test.
- **Template derivation:** Runner read only the framework document. Template structure was derived from Section 9.2 requirements shaped by the control body's four constraints (required headings, self-check assertion, generic content, avoid deep analysis).

## Cleanup

```
$ trash .claude/skills/rubric-report-005-runner
(no output — directory moved to trash)

$ git checkout -- packages/mcp-servers/claude-code-docs/
(no output — clean restore)

$ git diff -- packages/mcp-servers/claude-code-docs/
(empty output — confirmed clean)
```

**Confirmation:** Did NOT run `git checkout -- .` (scoped checkout to `packages/mcp-servers/claude-code-docs/` only).
