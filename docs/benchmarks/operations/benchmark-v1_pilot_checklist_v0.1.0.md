# Benchmark v1 Pilot — Executable Run Matrix & Checklist v0.1.0

This checklist operationalizes the v1 draft spec into a concrete pilot run you can execute now.

Primary reference:
- `docs/benchmarks/suites/benchmark-v1-draft_v0.1.0.md`

Pilot scope:
- 3 rubric scenarios
- 2 conditions (`baseline`, `target`)
- 1 replicate each (`run-1`)
- Total runs: **6**

Pilot policy decision (2026-02-08):
- This pilot is intentionally rubric-only.
- Objective anchor scenarios are deferred until after pilot gate outcome.

---

## 1) Pilot Configuration

Set:

```bash
RUN_ID=2026-02-08_benchmark-v1_pilot-01
RUN_ROOT=docs/benchmarks/runs/$RUN_ID
```

Create dirs:

```bash
mkdir -p "$RUN_ROOT/run-records" "$RUN_ROOT/blinded_eval"
```

---

## 2) Run Matrix (authoritative)

| # | scenario_id | condition | replicate | run record path |
|---:|---|---|---|---|
| 1 | `v1-rubric-constraint-ledger-101` | `baseline` | `run-1` | `docs/benchmarks/runs/$RUN_ID/run-records/v1-rubric-constraint-ledger-101__baseline__run-1.md` |
| 2 | `v1-rubric-constraint-ledger-101` | `target` | `run-1` | `docs/benchmarks/runs/$RUN_ID/run-records/v1-rubric-constraint-ledger-101__target__run-1.md` |
| 3 | `v1-rubric-evidence-ledger-102` | `baseline` | `run-1` | `docs/benchmarks/runs/$RUN_ID/run-records/v1-rubric-evidence-ledger-102__baseline__run-1.md` |
| 4 | `v1-rubric-evidence-ledger-102` | `target` | `run-1` | `docs/benchmarks/runs/$RUN_ID/run-records/v1-rubric-evidence-ledger-102__target__run-1.md` |
| 5 | `v1-rubric-verdict-gating-103` | `baseline` | `run-1` | `docs/benchmarks/runs/$RUN_ID/run-records/v1-rubric-verdict-gating-103__baseline__run-1.md` |
| 6 | `v1-rubric-verdict-gating-103` | `target` | `run-1` | `docs/benchmarks/runs/$RUN_ID/run-records/v1-rubric-verdict-gating-103__target__run-1.md` |

---

## 3) Target Injection Mapping (pilot draft)

Use these target bodies for `condition=target`:

| scenario_id | injected body token |
|---|---|
| `v1-rubric-constraint-ledger-101` | `BENCH_DISCIPLINE_CONSTRAINT_LEDGER_v1.0.0` |
| `v1-rubric-evidence-ledger-102` | `BENCH_REFERENCE_EVIDENCE_CALIBRATION_v1.0.0` |
| `v1-rubric-verdict-gating-103` | `BENCH_PATTERN_VERDICT_GATING_v1.0.0` |

For `condition=baseline`, use no injected benchmark body.

If canonical v1 body definitions do not yet exist, use the temporary definitions in Appendix A.

---

## 4) Per-Run Execution Checklist (repeat for each row)

For each run tuple:

1. Identify tuple variables:
   - `SCENARIO_ID`
   - `CONDITION`
   - `REPLICATE=run-1`
   - `RUN_RECORD_PATH`

2. Preflight cleanliness:

```bash
git diff -- packages/mcp-servers/claude-code-docs/
```

Expected: empty.

3. Execute scenario with correct condition:
   - `baseline`: scenario prompt only.
   - `target`: scenario prompt + mapped injected body.

4. Ensure run record is fully written to `RUN_RECORD_PATH` with:
   - metadata (`scenario_id`, `condition`, `replicate`, `oracle_type`, etc.)
   - output section (full produced output)
   - tool trace / file-read summary
   - confounders
   - cleanup evidence

5. Cleanup safety (required):

```bash
trash /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/<neutral_name>
git checkout -- packages/mcp-servers/claude-code-docs/
git diff -- packages/mcp-servers/claude-code-docs/
```

Expected final diff: empty.

6. Explicitly confirm:
   - Did **not** run `git checkout -- .`

---

## 5) Hard Invariants (pilot acceptance)

Per run, all must pass:

- Correct tuple (`scenario_id`, `condition`, `replicate`) in filename and metadata.
- `oracle_type` is `rubric_blinded`.
- No self-scoring table in run records (scoring deferred).
- Cleanup evidence present; package diff returns empty after run.
- No destructive cleanup (`rm`, `rm -rf`, broad checkout).

---

## 6) Blinded Scoring Checklist (pilot)

Use a separate evaluator session from the executor session.

1. Build blinded packet manually:
   - For each scenario, copy both outputs (baseline + target) into condition-free IDs:
     - `A` and `B`, randomized.
   - Do not include run-record filenames, condition labels, or injected-body tokens.
   - Save to:
     - `docs/benchmarks/runs/$RUN_ID/blinded_eval/blinded_eval_packet.md`

2. Keep private mapping (orchestrator-only):
   - `A/B` -> run-record file path
   - Save to:
     - `docs/benchmarks/runs/$RUN_ID/blinded_eval/blinded_eval_mapping_private.md`

3. Evaluator scores each candidate on 5 dimensions (0-4) using scenario-specific rubric in:
   - `docs/benchmarks/suites/benchmark-v1-draft_v0.1.0.md`
   - Save to:
     - `docs/benchmarks/runs/$RUN_ID/blinded_scores.md`

4. Blinding contamination checks:

```bash
rg -n "baseline|target|placebo|proxy|harmful|control|BENCH_|CONTROL_" docs/benchmarks/runs/$RUN_ID/blinded_scores.md
```

Expected: no matches.

---

## 7) Pilot Gate Computation (go / no-go)

For each scenario:

- `total = D1 + D2 + D3 + D4 + D5` (0-20)
- `PASS` iff `total >= 16` and both critical dimensions >=3
- Improvement signal iff all true:
  1. `target_total - baseline_total >= 2`
  2. target is `PASS`
  3. at least one critical dimension improved by >=1

Global pilot gate (from v1 suite draft):
- At least 2/3 scenarios show improvement signal.
- No scenario has target regression >=2 points.
- Blinding contamination checks clean.

If all true: proceed to full v1 replication (`N=3` baseline + `N=3` target).  
Else: revise scenarios/rubric before full execution.

---

## 8) Pilot Deliverables (required)

- `docs/benchmarks/runs/$RUN_ID/run-records/*.md` (6 files)
- `docs/benchmarks/runs/$RUN_ID/blinded_eval/blinded_eval_packet.md`
- `docs/benchmarks/runs/$RUN_ID/blinded_eval/blinded_eval_mapping_private.md`
- `docs/benchmarks/runs/$RUN_ID/blinded_scores.md`
- `docs/benchmarks/runs/$RUN_ID/scores.md` (pilot summary)
- `docs/benchmarks/runs/$RUN_ID/report.md` (pilot verdict + next action)

---

## Appendix A — Temporary v1 Target Bodies (if canonical bodies are not yet authored)

These temporary bodies are only for pilot execution and should be replaced by canonical v1 body definitions before full v1.

### `BENCH_DISCIPLINE_CONSTRAINT_LEDGER_v1.0.0` (temporary)

```md
---
Follow output constraints exactly.

You must provide exactly 3 options, each with:
- 2 strengths
- 2 weaknesses
- risk level (low/med/high)

Then provide a weighted score table whose weights sum to 100, followed by one recommendation that is consistent with the table.
Do not include extra options or honorable mentions.
---
```

### `BENCH_REFERENCE_EVIDENCE_CALIBRATION_v1.0.0` (temporary)

```md
---
When evidence is mixed, separate Observation vs Inference explicitly.
Every claim must cite provided evidence.
If evidence conflicts, downgrade confidence and explain why.
Do not make unsupported assertions.
---
```

### `BENCH_PATTERN_VERDICT_GATING_v1.0.0` (temporary)

```md
---
When producing benchmark verdicts:
1) Compute metrics explicitly.
2) Apply threshold logic before concluding.
3) Separate Evidence and Interpretation structurally.
4) If confounders exist, downgrade confidence explicitly.
5) State concrete decision triggers for changing verdict.
---
```
