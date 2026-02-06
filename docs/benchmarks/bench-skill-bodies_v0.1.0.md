# Synthetic Benchmark Skill Bodies v0.1.0 (BENCH_*)

This file defines canonical instruction bodies for **synthetic benchmark skills** referenced by:
- `docs/benchmarks/target-skills_v0.1.0.md`

These are intended to be injected into the scenario skill file’s standardized slot:
- Heading: `## Loaded Skill`
- Wrap in delimiters: `---` … `---`

**Safety:** These benchmark bodies must never instruct destructive actions (e.g., `rm`). They may change process and tool usage expectations, but should remain safe and repo-contained.

---

## BENCH_DISCIPLINE_EXACT_THREE_OPTIONS_v0.1.0

**Intent:** Enforce a strictly countable output structure. This is a “discipline” benchmark: it tests whether the evaluation can correctly score structural compliance without confusing it for correctness.

```md
---
You MUST structure your answer as exactly 3 options (no more, no less).

For each option:
- Name it (short title)
- Give at least 1 strength
- Give at least 1 weakness

After the 3 options, provide a single recommended option and explain why in 2–4 sentences.

Do not add “honorable mentions” or a 4th option.
---
```

Expected effect:
- Improves structure scores where the rubric values structure.
- Should not necessarily improve task correctness; evaluators must not over-credit it.

---

## BENCH_TECHNIQUE_RUN_TESTS_AND_MIN_DIFF_v0.1.0

**Intent:** Improve objective success on code-change anchor scenarios by requiring verification and minimal diffs.

```md
---
When making code changes, follow this process:

1) Identify the smallest change that could satisfy the task.
2) Prefer localized edits. Do not refactor unrelated code.
3) Verify with the scenario’s stated oracle commands (tests/build). If you cannot run them, state that explicitly and downgrade confidence.
4) If tests fail, iterate until they pass or you can explain the blocker.

Constraints:
- Avoid unrelated formatting-only changes.
- Avoid introducing new dependencies.
- Keep the diff minimal while still correct.
---
```

Expected effect:
- Higher pass rate on objective test/build oracles vs baseline.
- Fewer regressions/unrelated edits.

---

## BENCH_PATTERN_BLINDED_EVAL_DISCIPLINE_v0.1.0

**Intent:** Improve reporting integrity for rubric scenarios by enforcing evidence/interpretation separation and blinding discipline.

```md
---
For any benchmark report or scoring output you produce:

1) Separate **Evidence** from **Interpretation**.
   - Evidence = directly observable facts (outputs, oracle results, scores).
   - Interpretation = conclusions or hypotheses.

2) If the scenario requires blinded evaluation:
   - Do not label outputs as baseline/test in the scoring view.
   - Use Output A / Output B only.
   - Record the randomization method.
   - Only unmask baseline/test after scoring is complete.

3) If a confounder occurred (e.g., tool usage changed between conditions), you MUST flag it and downgrade confidence in conclusions.
---
```

Expected effect:
- Better benchmark reports; fewer overclaims.
- More consistent confounder tracking.

---

## BENCH_TOOL_SENSITIVITY_WEB_SEARCH_PUSH_v0.1.0

**Intent:** Deliberately induce tool-use confounding to test whether the benchmark process catches and records confounders. This is not expected to improve correctness.

```md
---
Before answering, you SHOULD use web search or external sources to confirm details, even if you think you already know them.

If you cannot access the web, state that and proceed anyway.

Note: This instruction is intentionally included to test tool-confounding detection in the benchmark process.
---
```

Expected effect:
- Increased likelihood of web/tool usage.
- Benchmark run records should flag this as a confounder rather than crediting it as “skill effectiveness.”

---

## BENCH_REFERENCE_LOCAL_CITATIONS_ONLY_v0.1.0

**Intent:** Improve “reference skill” behavior: ground claims in local repo sources with exact path citations; clearly separate observation vs inference; no web.

```md
---
When you make claims about this repository:

1) Use only local files as sources (no web).
2) Cite exact file paths for each key claim.
3) Clearly label:
   - Observation: directly supported by a cited file
   - Inference: conclusion drawn from observations
4) If you cannot find support in local files, say so explicitly.

Do not invent file paths or project facts.
---
```

Expected effect:
- Fewer hallucinated repo claims.
- More precise citations.
- Better evaluator confidence on “reference” tasks.
