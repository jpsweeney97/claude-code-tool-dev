# Rolling Handoff Packet — Codex Orchestrator (Benchmark v0)

This file is a standardized resume packet for starting a *fresh Codex session* (the orchestrator/verifier).
It complements `handoff.md`, which is optimized for starting a fresh Claude executor session.

## Repo

- `/Users/jp/Projects/active/claude-code-tool-dev`

## Role Split

- **Claude (Executor session)**: executes one run (scenario × condition × replicate) and writes the run record.
- **Claude (Evaluator session, separate from executor)**: performs blinded rubric scoring only.
- **Codex (this session)**: orchestrator/verifier only — decides next run, drafts Claude prompt, reads run record from disk, verifies invariants + drift, updates both handoff files.
- **Codex never does:** no run execution, no skill invocation, no blinded scoring.

## Interaction pattern (must follow)

This session must follow a strict loop:

1) You (assistant) determine the next step(s) for Benchmark v0 based on the canonical docs and the latest run records.
2) You give the user:
   - (a) the next steps in plain language
   - (b) a single paste-ready prompt to Claude telling it exactly what to do next (including file paths, run id, scenario id, condition, replicate, oracle commands, which run-record stub/file to fill, cleanup rules, and what to paste back). **The prompt must be provided inside a Markdown code block** for easy copy/paste.
3) The user pastes your prompt to Claude and then pastes Claude’s response back to you.
4) You evaluate Claude’s response against the prompt + benchmark invariants (correctness, compliance, drift, confounders).
5) You decide the next steps and repeat (back to step 1).

**Critical:** Codex must read the run record **from disk** (the specified `docs/benchmarks/runs/.../run-records/...` file) and verify invariants based on the on-disk contents. Claude’s chat summary is not authoritative.

**Also required:** After each accepted run (and after any repair), Codex must update both rolling handoff files:
- `docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/handoff.md`
- `docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/handoff_codex.md`

## Reset Bootstrap (Codex-run, not user-run)

When a new Codex/orchestrator session starts with zero memory, Codex must run this cycle autonomously:

1) Resume candidate state:
   - `scripts/benchmark_v0_resume`
2) Verify from disk against acceptance gates:
   - read the candidate run record from disk
   - apply strict invariants (including strict leakage rule)
   - if acceptance and `resume` disagree, acceptance gate is authoritative
3) Update both handoffs to match on-disk truth:
   - `docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/handoff.md`
   - `docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/handoff_codex.md`
4) Generate exactly one paste-ready Claude prompt for the user.

User responsibility is only:
- paste Codex’s prompt into Claude,
- return Claude’s response to Codex.

## Acceptance vs Repair (run-record policy)

- **Accepted run records are append-only.** Do not change an accepted run record unless you are repairing a hard invariant violation (e.g., wrong replicate format, forbidden-path mentions, self-scoring in rubric_blinded).
- **Strict leakage policy (effective 2026-02-08):** Any disallowed read of `scores.md`, `report.md`, or peer run-records during execution makes the run **REPAIR required** (do not accept as executed even if other invariants pass).
- **REPAIR runs:** If a run record was lost/corrupted or a run must be re-executed, label it explicitly as a REPAIR in the run record and explain: (1) what failed, (2) why re-execution was necessary, (3) what changed relative to the original (if known).
- **Do not overwrite:** Never overwrite an accepted run record with a new output unless explicitly performing a REPAIR and documenting it.

## Audience Note

- `handoff.md` is for the Claude executor and should stay focused on “do exactly one run + fill one run record”.
- `handoff_codex.md` is for Codex orchestration/verification policy, checklists, and handoff maintenance.

## Codex Preflight (before prompting Claude)

1) Confirm clean start (required invariant):
   - `git diff -- packages/mcp-servers/claude-code-docs/` (expect empty)
2) Confirm the next scheduled run from the suite matrix (source of truth):
   - `docs/benchmarks/suites/benchmark-v0_v0.1.0.md` is authoritative if any handoff text/stub expectations disagree.
3) Confirm the run-record stub exists for the next run (path in handoff).
4) Confirm the prior accepted run record passes the strict zero-mention rule:
   - No occurrences of `docs/adrs` or `docs/benchmarks/scenarios`.
5) Ensure the Claude prompt is explicitly “one run only” and includes:
   - run id / scenario id / condition / replicate
   - oracle commands (or explicit `N/A` for rubric_blinded)
   - exact run-record filepath to fill
   - cleanup commands (trash + scoped revert, not broad checkout)
6) Enforce leakage avoidance:
   - Claude must not open `scores.md` / `report.md` or other run records.
   - If disallowed reads occur, the run must be marked REPAIR_REQUIRED and not accepted.

## Codex Post-run Verification (after user pastes Claude response)

1) Read the run record **from disk** (do not trust chat summary).
2) Verify strict invariants in the on-disk run record:
   - correct run id / scenario id / condition / replicate string
   - rubric_blinded: no rubric score table; no self-scoring
   - strict zero-mention rule: no `docs/adrs` and no `docs/benchmarks/scenarios`
   - leakage rule: no disallowed reads of `scores.md`, `report.md`, or peer run records
   - clean-start and cleanup evidence blocks included (commands + raw outputs)
3) Verify repository state:
   - `git diff -- packages/mcp-servers/claude-code-docs/` empty after cleanup
4) Enforce acceptance/repair decision:
   - if any disallowed read occurred, classify run as REPAIR_REQUIRED and schedule re-execution of same scenario/condition/replicate.
5) Record confounders and drift:
   - tool usage differences across conditions
   - anchoring (e.g., reading `docs/benchmarks/control-bodies_v0.1.0.md`)
   - constraint violations (e.g., brevity control exceeded)
6) Update both handoff files and advance exactly one run.

## Fully Blinded Rubric Scoring (Option 1: alias packet)

When scoring `rubric_blinded` scenarios, do NOT give the evaluator the `run-records/` directory directly (filenames and metadata leak condition labels).

Use the fully blinded alias packet workflow:

```bash
./scripts/blinded_eval_packet.py --run-id 2026-02-06_benchmark-v0_initial
./scripts/blinded_eval_packet.py --run-id 2026-02-06_benchmark-v0_initial --verify-only
```

Share ONLY with evaluator:
- `docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/blinded_eval/blinded_eval_packet.md`

Keep PRIVATE (orchestrator-only mapping):
- `docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/blinded_eval/blinded_eval_mapping_private.md`

Evaluator writes (blinded artifact):
- `docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/blinded_scores.md`

Orchestrator then updates:
- `docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/scores.md`
- `docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/report.md`

## Handoff Alignment Protocol (keep `handoff.md` + `handoff_codex.md` 100% current)

Treat the on-disk repo as the source of truth. These handoff files are summaries; they must never “drift” into a narrative that contradicts run records or the suite matrix.

### Source of truth (in priority order)

1) Suite execution spec (what should be run next):
   - `docs/benchmarks/suites/benchmark-v0_v0.1.0.md`
2) On-disk run records (what has actually been executed/accepted):
   - `docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/run-records/`
3) Current repo state invariants (clean start / cleanup):
   - `git diff -- packages/mcp-servers/claude-code-docs/`

### Update rules (apply every accepted run and every repair)

After a run is accepted (or after a repair to make it acceptable), update BOTH handoffs in the same edit session:

- `handoff.md` must always reflect the executor-facing “next action”:
  - Progress Snapshot: status for each scenario touched so far + the currently active scenario.
  - Most Recent Run Record Touched: point at the most recently modified/accepted run record on disk (not a historical example).
  - Immediate Next Action: MUST match the next scheduled run from the suite matrix that is not yet executed.
  - Next Claude Prompt: MUST be a single-run prompt that matches Immediate Next Action exactly (scenario/condition/replicate/path).
    - No stale “scoring/report update” instructions if the next action is a run execution.

- `handoff_codex.md` must always reflect verifier/orchestrator “next run” state:
  - Current State Summary: scenario completion counts must match the suite matrix AND the presence of run records on disk.
  - Immediate Next Run: MUST match `handoff.md`’s Immediate Next Action.
  - Next Codex Actions: MUST point to the same next run and the correct run-record file path to verify.

### Drift checks (required before declaring “up to date”)

Run these checks and reconcile any mismatch immediately:

```bash
# 1) Suite-driven expectation for next run (human check)
cat docs/benchmarks/suites/benchmark-v0_v0.1.0.md

# 2) Confirm the intended stub exists
ls -la docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/run-records/

# 3) Confirm the most recent accepted run record is invariant-clean
rg -n "docs/adrs|docs/benchmarks/scenarios" docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/run-records/<LATEST_ACCEPTED>.md || true

# 4) Confirm the repo package diff is clean after cleanup
git diff -- packages/mcp-servers/claude-code-docs/
```

If either handoff contradicts (a) the suite matrix, or (b) the on-disk run-record directory contents, treat it as a handoff bug and fix it before proceeding to the next run.

## Verifier Commands (paste-ready)

Use these commands every cycle (replace `<RUN_RECORD_PATH>`):

```bash
cat <RUN_RECORD_PATH>
rg -n "docs/adrs|docs/benchmarks/scenarios" <RUN_RECORD_PATH> || true
rg -n "Read.*(report\\.md|scores\\.md|run-records/)|disallowed read|REPAIR_REQUIRED" <RUN_RECORD_PATH> || true
git diff -- packages/mcp-servers/claude-code-docs/
```

## Confounders (what must be recorded if present)

- Read of prior run records (can cause anchoring / leakage)
- Read of `docs/benchmarks/control-bodies_v0.1.0.md` (anchoring risk, often HIGH)
- Tool usage differs between conditions (differential confounder)
- Constraint violations (e.g., exact-count violated, brevity constraint exceeded)
- Any fallback/blocked behavior (especially any attempted Task-tool substitute)

## Oracle Commands (rule of thumb)

- **Anchor scenarios:** run record must include the objective oracle command(s) output and `task_completion_verdict: PASS/FAIL` (empty diff => FAIL).
- **Rubric_blinded scenarios:** `oracle_commands: N/A` and no rubric score table; scoring deferred to a separate evaluator.

## Common Failure Modes (and immediate fix)

- **Task tool used instead of Skill tool:** Invalid run → re-execute via Skill tool invocation chain.
- **Forbidden-path string appears in run record:** Invariant violation → repair the run record to remove it.
- **Disallowed leakage read (`scores.md`/`report.md`/peer run records):** Mark REPAIR_REQUIRED and re-execute same scenario/condition/replicate.
- **Over-broad cleanup (`git checkout -- .`) reverts run records:** Treat as incident → REPAIR re-execution for lost records; update prompts to require scoped revert only.

## Canonical Docs (Authoritative)

Use these as the only authoritative sources for mappings/citations in prompts/run records:

1) `docs/simulation-assessment-context-official.md`
2) `docs/frameworks/simulation-effectiveness-benchmark_v0.1.0.md`
3) `docs/benchmarks/suites/benchmark-v0_v0.1.0.md`
4) `docs/benchmarks/target-skills_v0.1.0.md`
5) `docs/benchmarks/control-bodies_v0.1.0.md`
6) `docs/benchmarks/bench-skill-bodies_v0.1.0.md`

## Hard Invariants (Must Enforce)

- Never use `rm`; use `trash`.
- Skills hot-reload; do not rely on subagents.
- Valid invocation chain only:
  - Create skill at `.claude/skills/<name>/SKILL.md` with `context: fork` + `agent: assessment-runner`
  - Invoke via `Skill(skill: "<name>")` (do not use Task tool as a substitute)
- Neutral skill metadata naming (no baseline/test/control/placebo labels in description).
- Runner run is pre-check only; main session is oracle of record.
- Verify clean start before each run:
  - `git diff -- packages/mcp-servers/claude-code-docs/` must be empty.
- Cleanup after each run:
  - `trash` temp skill dir + revert code changes + verify diff empty.
  - **Do not use** `git checkout -- .` as cleanup; it can revert run records (this occurred during `v0-rubric-exact-three-options-007` baseline run-2 and required REPAIR re-executions). Prefer scoped reverts (e.g., `git checkout -- packages/mcp-servers/claude-code-docs/`) plus the canonical diff verification.
- Baseline integrity: for each scenario, run baseline before any injected-skill condition (avoid anchoring/scenario leakage).
- Anchor rule:
  - include `task_completion_verdict` PASS/FAIL
  - empty diff => FAIL even if tests pass.
- Rubric scenarios are `rubric_blinded`:
  - Claude must not self-score; run record should defer scoring.
- Replicate naming:
  - must be `run-1`/`run-2`/`run-3` string (not numeric).
- Citations rule:
  - run records should cite only the canonical docs above.
  - **Zero-mention rule (strict):** run records must contain **zero occurrences** of:
    - `docs/adrs` (any ADR path prefix)
    - `docs/benchmarks/scenarios` (any scenario-doc path prefix)
    Any appearance (even as “context” or “confounder”) is an invariant violation requiring repair.

## Benchmark Run ID

- `2026-02-06_benchmark-v0_initial`

## Current State Summary (status only; not required for procedure)

Completed (anchors):
- `v0-anchor-vitest-001`: COMPLETE (9/9)
- `v0-anchor-frontmatter-002`: COMPLETE (7/7)
- `v0-anchor-golden-queries-003`: COMPLETE (6/6)

Reporting artifacts:
- `docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/scores.md` currently reflects anchor scoring; rubric scoring remains deferred to blinded evaluation.
- `docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/report.md` exists as a working artifact and should be refreshed after blinded rubric scoring.

Rubric run execution status:
- Scenario `v0-rubric-scenario-spec-004`: COMPLETE (6/6)
  - baseline run-1/run-2/run-3 COMPLETE
  - placebo run-1 COMPLETE
  - proxy_gaming run-1 COMPLETE (run record repaired to remove non-canonical scenario-doc dependency)
  - harmful_brevity_60w run-1 COMPLETE

- Scenario `v0-rubric-report-005`: COMPLETE (7/7)
  - baseline run-1/run-2/run-3 COMPLETE (run-3 accepted via REPAIR re-execution)
  - target run-1/run-2/run-3 COMPLETE
  - proxy_gaming run-1 COMPLETE

- Scenario `v0-rubric-controls-006`: COMPLETE (4/4)
  - baseline run-1/run-2/run-3 COMPLETE
  - harmful_brevity_60w run-1 COMPLETE

- Scenario `v0-rubric-exact-three-options-007`: COMPLETE (6/6)
  - baseline run-1/run-2/run-3 COMPLETE
  - target run-1/run-2/run-3 COMPLETE

- Scenario `v0-rubric-reference-008`: COMPLETE
  - baseline run-1/run-2/run-3 COMPLETE
  - target run-1/run-2/run-3 COMPLETE

Run records directory:
- `docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/run-records/`

## Verification Checklist (Codex) — Final Closeout

Final checks (all must hold):

1) Execution completeness:
   - `scripts/benchmark_v0_resume` shows `planned_runs=51`, `executed_runs=51`, `remaining_runs=0`.
2) Blinding integrity:
   - `./scripts/blinded_eval_packet.py --run-id 2026-02-06_benchmark-v0_initial --verify-only` => `OK`
   - `rg -n "\\b(baseline|target|placebo|proxy|harmful|control)\\b" docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/blinded_scores.md || true` => empty
   - `rg -n "__baseline__|__target__|__placebo__|__proxy|__harmful|__control" docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/blinded_scores.md || true` => empty
   - `rg -n "\\bBENCH_|\\bCONTROL_" docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/blinded_scores.md || true` => empty
3) Reporting refresh:
   - `scores.md` and `report.md` reflect full execution + blinded scoring results.
   - no stale pre-scoring claims (`not executed`, `empty stubs`, etc.).
4) Repo package cleanliness:
   - `git diff -- packages/mcp-servers/claude-code-docs/` is empty.

## Immediate Next Phase (Complete)

- `phase`: `benchmark_v0_complete`
- `run_id`: `2026-02-06_benchmark-v0_initial`
- Final artifacts:
  - `docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/blinded_eval/blinded_eval_packet.md`
  - `docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/blinded_eval/blinded_eval_mapping_private.md`
  - `docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/blinded_scores.md`
  - `docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/scores.md`
  - `docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/report.md`

Next Claude prompt:
- None required for this `run_id`.

## Next Codex Actions (Copy/Paste)

```text
You are Codex acting as the orchestrator/verifier for Benchmark v0.

Closeout state:
- Benchmark v0 is complete for run_id 2026-02-06_benchmark-v0_initial.
- No further executor/evaluator prompts are required for this run.

If the user asks for follow-up:
1) Provide final artifact pointers (scores/report/blinded outputs).
2) Summarize key findings and final verdict from report.md.
3) Offer optional next step: start a new run_id / benchmark-v1 planning.
```
