# Benchmark v0 Operations Manual v0.1.0

This document is the **canonical operating manual** for running and scoring Benchmark v0.
It defines the roles, invariants, file layout, and the end-to-end loop for:

1) **Orchestrator/Verifier** (Codex)
2) **Executor** (Claude)
3) **Blind Evaluator** (Claude in a separate session)

If any handoff text conflicts with this manual, this manual wins.

Ownership/usage:
- This document is **orchestrator-owned**. Do not provide it to Executor or Blind Evaluator sessions.
- Orchestrator prompts must embed the relevant constraints and file paths inline.

---

## Repo + Run ID

- Repo root: `/Users/jp/Projects/active/claude-code-tool-dev`
- Run artifacts: `docs/benchmarks/runs/<RUN_ID>/`
- Run records: `docs/benchmarks/runs/<RUN_ID>/run-records/`

---

## Canonical Docs (Authoritative)

Run records must cite ONLY these documents as evidentiary authority:

1. `docs/simulation-assessment-context-official.md`
2. `docs/frameworks/simulation-effectiveness-benchmark_v0.1.0.md`
3. `docs/benchmarks/suites/benchmark-v0_v0.1.0.md`
4. `docs/benchmarks/target-skills_v0.1.0.md`
5. `docs/benchmarks/control-bodies_v0.1.0.md`
6. `docs/benchmarks/bench-skill-bodies_v0.1.0.md`

Source-of-truth priority:
1) Suite matrix (`docs/benchmarks/suites/benchmark-v0_v0.1.0.md`) — what SHOULD be run
2) On-disk run records (`docs/benchmarks/runs/<RUN_ID>/run-records/`) — what DID happen
3) Repo state (`git diff -- packages/mcp-servers/claude-code-docs/`) — clean-start/cleanup invariants

Run records must also comply with the suite’s Citation Policy (including `.claude/` path rules):
- `docs/benchmarks/suites/benchmark-v0_v0.1.0.md` → “Citation Policy (required for run records)”

---

## Hard Invariants (All Roles)

- **Deletion safety:** never run `rm`; use `trash`.
- **Role boundary (strict):**
  - Codex is orchestrator/verifier only; Codex must not execute benchmark runs or blinded scoring.
  - Claude may serve as Executor or Blind Evaluator, but evaluator work must be in a separate Claude session from the executor session.
- **Invocation chain (required):**
  - Create `.claude/skills/<neutral_name>/SKILL.md` with:
    - `context: fork`
    - `agent: assessment-runner`
  - Invoke via `Skill(skill: "<neutral_name>")`
  - Do not use Task tool as a substitute.
- **Neutral naming:** skill name/description must not include baseline/target/control/placebo labels.
- **Clean start (required before each run):**
  - `git diff -- packages/mcp-servers/claude-code-docs/` must be empty.
- **Cleanup (required after each run):**
  - `trash .claude/skills/<neutral_name>`
  - `git checkout -- packages/mcp-servers/claude-code-docs/`
  - Verify `git diff -- packages/mcp-servers/claude-code-docs/` is empty.
  - Do NOT run `git checkout -- .` (it can revert run artifacts).
- **Replicate naming:** must be `run-1` / `run-2` / `run-3` (string).
- **Strict zero-mention rule (run records):** run records must contain zero occurrences of:
  - `docs/adrs`
  - `docs/benchmarks/scenarios`
- **Rubric scenarios are `rubric_blinded`:**
  - no self-scoring
  - no rubric score table scaffold (even empty/em-dash “Dimension | Score” tables)

---

## Lessons Learned (Rolling, Non-Normative)

Benchmark execution often surfaces practical “gotchas” and drift patterns. Capture these without changing canonical procedure in:

- `docs/benchmarks/operations/benchmark-v0_ops_lessons_learned.md`

### When to add an entry

Add an entry when any of the following occurs:
- A run record required a REPAIR (invariant violation, accidental leakage, rubric-table scaffold, forbidden path mention).
- A recurring prompt failure mode appears (e.g., copy/paste trap, repeated rubric-table scaffolds, repeated stale “next run” guidance).
- A consistent confounder emerges across runs (e.g., environment derivative sources in reference scenarios).
- You adopt a new mitigation in prompts/hand-offs (even if the canonical procedure stays the same).

### What *not* to do

- Do not modify `benchmark-v0_ops_v0.1.0.md` for one-off incidents.
- Do not change suite/framework semantics via lessons learned.
- If a lesson implies a change to invariants, acceptance gates, or blinding method, bump ops version instead of editing this ops manual in-place.

---

## Orchestrator/Verifier (Codex) Workflow

Codex is the orchestrator/verifier. Codex decides the next run, drafts the Executor prompt, reads run records from disk, verifies invariants, and maintains handoffs.

### Next-run selection (deterministic)

Use the suite matrix as the source of truth:
- `docs/benchmarks/suites/benchmark-v0_v0.1.0.md`

Rules:
- Execute exactly one run per cycle (one scenario × one condition × one replicate).
- For a given scenario, complete **baseline N=3** before starting any injected condition for that scenario (avoids anchoring/leakage).
- For scenarios with “TARGET: none” per the suite matrix, treat any target stubs as invalid and do not execute them.
- Treat “stub exists on disk” as non-authoritative; only “run record contains real output + invariant compliance” counts as executed.
- Prefer completing a scenario’s planned matrix before moving to the next scenario in the roster (reduces drift and confusion).

### Codex loop (every execution cycle)

1) Determine the next scheduled run from the suite matrix:
   - `docs/benchmarks/suites/benchmark-v0_v0.1.0.md`
2) Preflight:
   - `git diff -- packages/mcp-servers/claude-code-docs/` must be empty.
3) Confirm the run-record stub exists for the next run:
   - `docs/benchmarks/runs/<RUN_ID>/run-records/<scenario>__<condition>__<replicate>.md`
4) Provide the user:
   - the next step in plain language
   - a single paste-ready Executor prompt (one run only)
5) After the user returns Claude’s response:
   - Read the run record from disk (Claude summary is not authoritative)
   - Verify invariants and repo state
6) Accept vs repair:
   - Accepted run records are append-only.
   - Only edit an accepted run record to repair a hard invariant violation.
7) Update both rolling handoffs:
   - `docs/benchmarks/runs/<RUN_ID>/handoff.md`
   - `docs/benchmarks/runs/<RUN_ID>/handoff_codex.md`
8) Repeat.

### Codex acceptance gate (machine-checkable)

Before marking a run accepted, verify from disk:

```bash
cat <RUN_RECORD_PATH>
rg -n "docs/adrs|docs/benchmarks/scenarios" <RUN_RECORD_PATH> || true
rg -n "\\| Dimension \\| Score \\(0-2\\)" <RUN_RECORD_PATH> || true
rg -n "\\.claude/(rules|agents)/" <RUN_RECORD_PATH> || true
git diff -- packages/mcp-servers/claude-code-docs/
```

Acceptance rules:
- Any match for `docs/adrs` or `docs/benchmarks/scenarios` in the run record is an invariant violation → REPAIR required.
- Any rubric score table scaffold (e.g., “Dimension | Score (0-2)”) in a `rubric_blinded` run record is an invariant violation → REPAIR required.
- Any `.claude/rules/` or `.claude/agents/` path in a run record is a Citation Policy violation (see suite spec) → REPAIR required.
- `git diff -- packages/mcp-servers/claude-code-docs/` must be empty after cleanup.

### Codex verifier commands (paste-ready)

```bash
cat <RUN_RECORD_PATH>
rg -n "docs/adrs|docs/benchmarks/scenarios" <RUN_RECORD_PATH> || true
rg -n "\\| Dimension \\| Score \\(0-2\\)" <RUN_RECORD_PATH> || true
git diff -- packages/mcp-servers/claude-code-docs/
```

---

## Executor (Claude) Workflow (Run Execution)

Claude Executor runs **exactly one** scenario × condition × replicate per prompt and fills **exactly one** run record stub.

### Executor preflight (must record raw output in run record)

1) `git diff -- packages/mcp-servers/claude-code-docs/`
2) If non-empty: return `BLOCKED: dirty start`.

### Executor leakage avoidance (required)

Unless the scenario explicitly requires it, the Executor must NOT open/read:
- `docs/benchmarks/runs/<RUN_ID>/scores.md`
- `docs/benchmarks/runs/<RUN_ID>/report.md`
- other run records in `docs/benchmarks/runs/<RUN_ID>/run-records/`

If any of these are opened/read, it must be recorded as a confounder in the run record.

### Executor execution steps (one run only)

1) Create `.claude/skills/<neutral_name>/SKILL.md` with `context: fork` + `agent: assessment-runner`.
2) Inject the specified body (or none for baseline).
3) Invoke `Skill(skill: "<neutral_name>")`.
4) Produce the task output under scenario constraints.
5) Fill the specified on-disk run-record stub (no placeholders).
6) For `rubric_blinded`: do not self-score; do not include rubric score tables; defer scoring.

### Executor cleanup (must record raw output)

1) `trash .claude/skills/<neutral_name>`
2) `git checkout -- packages/mcp-servers/claude-code-docs/`
3) `git diff -- packages/mcp-servers/claude-code-docs/` must be empty.
4) Explicitly confirm in chat: did NOT run `git checkout -- .`

### Executor chat response format

- First line: `COMPLETED` or `BLOCKED: <reason>`
- Then 5–10 concise bullets (no full file paste)
- Include: run-record filepath written + cleanup diff status

---

## Blind Evaluator (Claude) Workflow (Fully Blinded Rubric Scoring)

Evaluator must be a **separate Claude session** from the Executor.

### Fully blinded mechanism: Option 1 (alias packet)

Do NOT give the evaluator `run-records/` directly (filenames and metadata leak condition labels).

Orchestrator generates the packet:

```bash
./scripts/blinded_eval_packet.py --run-id <RUN_ID>
./scripts/blinded_eval_packet.py --run-id <RUN_ID> --verify-only
```

The evaluator packet includes:
- per-scenario “Task + Criteria” (authoritative YAML excerpt from the framework doc)
- condition-free candidate IDs and extracted rubric-run `## Output` sections
- redaction of condition words and injected-body tokens inside extracted output

Share with evaluator ONLY:
- `docs/benchmarks/runs/<RUN_ID>/blinded_eval/blinded_eval_packet.md`

Keep private (orchestrator-only):
- `docs/benchmarks/runs/<RUN_ID>/blinded_eval/blinded_eval_mapping_private.md`

### Evaluator rules

Evaluator MUST:
- Read only the packet.
- Score using the packet’s per-scenario “Task + Criteria” and candidate outputs.
- Write results to:
  - `docs/benchmarks/runs/<RUN_ID>/blinded_scores.md`
- Avoid condition words, injected-body tokens, and run-record filenames in `blinded_scores.md`.

---

## Orchestrator scoring/report update workflow

After `blinded_scores.md` exists:

1) Sanity-check it is blinded (no condition labels).
2) Update:
   - `docs/benchmarks/runs/<RUN_ID>/scores.md`
   - `docs/benchmarks/runs/<RUN_ID>/report.md`
   using `blinded_scores.md` as the rubric scoring source of truth.
3) Do not edit run records during this phase.

---

## Paste-Ready Prompts (Evaluator + Orchestrator)

These prompts are provided to reduce drift and enforce consistent blinding.

### Prompt A: Blind Evaluator (fresh Claude session)

```md
You are a BLINDED EVALUATOR for Benchmark v0.

Goal
- Score rubric_blinded scenarios for run_id `<RUN_ID>`.
- You must NOT execute runs, modify code, or edit any run-record files.
- You must NOT infer or use condition labels (“baseline/target/placebo/proxy/harmful/control”) while scoring.

Repo
- /Users/jp/Projects/active/claude-code-tool-dev

Allowed input (the only file you should read for scoring)
- `docs/benchmarks/runs/<RUN_ID>/blinded_eval/blinded_eval_packet.md`

Disallowed (do not open)
- `docs/benchmarks/runs/<RUN_ID>/run-records/` (filenames + metadata leak conditions)
- `docs/benchmarks/runs/<RUN_ID>/handoff.md`
- `docs/benchmarks/runs/<RUN_ID>/handoff_codex.md`

Scoring rules
- For each scenario section in the packet:
  - Use the packet’s “Task + Criteria” block as the source of truth.
  - Score each candidate output independently.
- Do not rewrite responses; only score.

Output artifact
- Create: `docs/benchmarks/runs/<RUN_ID>/blinded_scores.md`

Format requirements for blinded_scores.md
- Section per `scenario_id`.
- One row per candidate ID (do not include run-record filenames).
- Include per-dimension scores, total, brief justification, and confidence (low/med/high).
- Do not include condition words or injected-body tokens (`BENCH_` / `CONTROL_`) anywhere.

When finished
- Reply with the filepath you wrote and a short list of top-ranked candidate IDs per scenario.
```

### Prompt B: Orchestrator (Codex) post-eval update

```md
You are Codex acting as the orchestrator for Benchmark v0.

Goal
- Use the blinded evaluator artifact to update:
  - `docs/benchmarks/runs/<RUN_ID>/scores.md`
  - `docs/benchmarks/runs/<RUN_ID>/report.md`
- Do not modify any run-record files.
- Do not edit `blinded_scores.md` unless it is purely formatting and does not affect blinding.

Repo
- /Users/jp/Projects/active/claude-code-tool-dev

Inputs
- `docs/benchmarks/runs/<RUN_ID>/blinded_scores.md`
- Private mapping (do not share with evaluator):
  - `docs/benchmarks/runs/<RUN_ID>/blinded_eval/blinded_eval_mapping_private.md`

Blinding verification (must run before using blinded_scores.md)
```bash
rg -n "\\b(baseline|target|placebo|proxy|harmful|control)\\b" docs/benchmarks/runs/<RUN_ID>/blinded_scores.md || true
rg -n "__baseline__|__target__|__placebo__|__proxy|__harmful|__control" docs/benchmarks/runs/<RUN_ID>/blinded_scores.md || true
rg -n "\\bBENCH_|\\bCONTROL_" docs/benchmarks/runs/<RUN_ID>/blinded_scores.md || true
```
If any matches occur, treat the evaluator artifact as contaminated and re-run evaluation.

Update steps
1) Update `scores.md` rubric sections to reflect executed-counts and scoring summaries (derived from blinded_scores.md).
2) Update `report.md` to cite blinded scoring provenance and summarize findings + limitations/confounders.
3) Confirm `git diff -- packages/mcp-servers/claude-code-docs/` remains empty.

Response
- List which files changed + concise summary.
```

---

## Paste-Ready Prompt Template: Executor (Claude) one-run execution

Use this template whenever running a single scenario × condition × replicate. Replace all `<...>` placeholders.
Orchestrator note: copy/paste this prompt to a Claude Executor session; do not execute these run steps in Codex.

```md
You are Claude (executor) running exactly ONE Benchmark v0 run.

Run identity
- run_id: <RUN_ID>
- scenario_id: <SCENARIO_ID>
- condition: <CONDITION>   # e.g., baseline / target / placebo / irrelevant / harmful_* / proxy_gaming
- replicate: <REPLICATE>   # run-1 / run-2 / run-3
- oracle_type: <ORACLE_TYPE>   # objective_tests or rubric_blinded
- oracle_commands: <ORACLE_COMMANDS or N/A>

Run record (authoritative; fill this exact on-disk stub)
- <RUN_RECORD_PATH>

Preflight (must record raw output in the run record)
1) In repo: /Users/jp/Projects/active/claude-code-tool-dev
2) Run: git diff -- packages/mcp-servers/claude-code-docs/
   - Expect: empty. If not empty, STOP and return BLOCKED.

Invocation chain (required)
1) Create a temp skill at: .claude/skills/<neutral_name>/SKILL.md
   - Must include: context: fork
   - Must include: agent: assessment-runner
   - Neutral naming/description (no baseline/target/control/placebo labels).
2) Injected body:
   - If baseline: none
   - Otherwise: <INJECTED_BODY_ID> (verbatim)
3) Invoke via: Skill(skill: "<neutral_name>")

Task requirements
- Follow the scenario prompt and constraints as specified in the framework/suite.
- For rubric_blinded:
  - DO NOT self-score
  - DO NOT include any rubric score table scaffold
  - Defer scoring to blinded evaluator

Leakage avoidance
- Do NOT open/read:
  - docs/benchmarks/runs/<RUN_ID>/scores.md
  - docs/benchmarks/runs/<RUN_ID>/report.md
  - other run records
If you read anything extra anyway, record it explicitly as a confounder.

Run record invariants
- Cite ONLY the six canonical docs listed in the suite spec.
- Strict zero-mention rule: the run record must contain ZERO occurrences of:
  - \"docs/adrs\"
  - \"docs/benchmarks/scenarios\"

Cleanup (must record raw outputs)
1) trash .claude/skills/<neutral_name>   # never rm
2) git checkout -- packages/mcp-servers/claude-code-docs/   # DO NOT git checkout -- .
3) git diff -- packages/mcp-servers/claude-code-docs/       # must be empty

Response back (chat)
- First line: COMPLETED or BLOCKED: <reason>
- Then 5–10 concise bullets summarizing what happened (no full-file paste)
- Confirm you did NOT run `git checkout -- .`
```
