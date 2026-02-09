# Control Calibration Evaluation Packet — making-recommendations (Phase 4)

## Orchestrator Instructions (DELETE before sending to evaluator)

> **This entire section is for the orchestrator only. Delete it before sending the packet to the evaluator session.**

### Building the Packet

1. Delete this "Orchestrator Instructions" section
2. For each task, replace every `{INSERT OUTPUT #N}` with the actual anonymized output
3. Each task must include **9 outputs** total:
   - 3 baseline
   - 3 harmful control
   - 3 placebo control
4. For any output: if the run created a Decision Record file, **paste the full Decision Record contents below the output** under a `Decision Record contents:` sub-header (the skill's in-chat output is often just a summary + link — the evaluator needs the file contents to score D1–D6)
5. Strip metadata that reveals condition: condition labels (`baseline`, `test`, `placebo`, `harmful`, `control`), skill file paths (`.claude/skills/scenario-*/SKILL.md`), run-record paths. **Do not redact** Decision Record references, Entry Gate sections, scoring tables, or other structural content inside the output
6. Assign a random 4-character alphanumeric ID to each output (e.g., `7k3m`, `p2x9`) and ensure IDs are unique within the packet
7. Shuffle the output presentation order within each task

### Output File

Evaluator writes results to: `docs/assessments/evaluator-scores-calibration.md`

### After Scoring (Orchestrator-only)

Unmask output IDs to condition + replication and compute task-level outcomes using majority vote over the 3 run-pairs:
- **Baseline vs Harmful:** for i in 1..3, compare baseline_run_i total vs harmful_run_i total → winner_i; majority vote → task outcome
- **Placebo vs Baseline:** for i in 1..3, compare placebo_run_i total vs baseline_run_i total → winner_i; majority vote → task outcome

Apply gates (from the pilot plan Phase 4):
- **Sensitivity gate:** harmful must be worse than baseline on ≥1 of the 2 calibration tasks
- **Instruction-sensitivity check:** if placebo beats baseline on either calibration task → mark evaluation as instruction-sensitive and include placebo in the full suite

---

## Instructions for Evaluator

You are scoring outputs from a control calibration experiment. Each task below shows a prompt and 9 candidate outputs, each identified by a random ID. You do not know which condition produced which output.

**Your job:** Score each output against the rubric below using the scoring table provided for that task.

**What to produce:** For each task, fill in the scoring table and write 1–2 sentences of evidence for D0 and D7 per output. After scoring all outputs for a task, optionally record your condition guess (which outputs you think share a condition) and confidence. Write all results to `docs/assessments/evaluator-scores-calibration.md`.

**Rules:**
- Score each output independently — do not adjust scores relative to other outputs
- Do not try to "balance" scores across outputs
- If an output mentions creating or referencing a file, and file contents are shown below the output, use those contents for scoring D1–D6

---

## Rubric

### D0 — Appropriate activation (0-4)

For **full-activation tasks:**
- 0: No framework engagement at all
- 1: Minimal framework engagement (some structure but key elements missing)
- 2: Partial — identifies this as a recommendation task, applies some framework
- 3: Appropriate — full framework engagement proportional to task complexity
- 4: Calibrated — framework engagement explicitly matched to stakes level

### D1 — Decision Record file (0-2)

- 0: No file created
- 1: File created but missing major sections (e.g., no evaluation, no iteration log)
- 2: Complete Decision Record with all sections for stakes level

### D2 — Entry Gate documented (0-2)

- 0: No stakes calibration or iteration cap mentioned
- 1: Stakes level mentioned but incomplete (missing rationale or iteration cap)
- 2: Full Entry Gate: stakes level + rationale + iteration cap + evidence bar

### D3 — Options include null (0-2)

- 0: Fewer than 3 options, no null
- 1: 3+ options but no null/do-nothing option
- 2: 3+ options including explicit null/defer/do-nothing

### D4 — Weighted scoring table (0-2)

- 0: No scoring or only prose comparison
- 1: Informal comparison (pros/cons lists, unweighted)
- 2: Formal weighted scoring table with numerical criteria weights and scores

### D5 — Adversarial pressure test (0-3)

- 0: No adversarial challenge
- 1: Token objections ("one concern is...")
- 2: Genuine pressure with specific lenses (pre-mortem OR steelman OR kill-it)
- 3: Multiple lenses applied, objections that would cause discomfort if true

### D6 — Iteration log (0-2)

- 0: No iteration log or mention of multiple passes
- 1: Mentions iteration but no pass-by-pass detail
- 2: Multi-pass log with what changed each pass and convergence justification

### D7 — Task completion (0-3)

- 0: Does not address the question
- 1: Partially addresses (misses key constraints or aspects)
- 2: Adequately addresses the question
- 3: Exceptionally thorough and well-reasoned for the domain

---

## Calibration Tasks (Phase 4)

### C1 — Full activation | Max: 20

**Prompt:** "Should we use MongoDB or PostgreSQL for our e-commerce platform?"

| output_id | D0 | D1 | D2 | D3 | D4 | D5 | D6 | D7 | total |
|-----------|----|----|----|----|----|----|----|----|-------|
| {id-1} | | | | | | | | | |
| {id-2} | | | | | | | | | |
| {id-3} | | | | | | | | | |
| {id-4} | | | | | | | | | |
| {id-5} | | | | | | | | | |
| {id-6} | | | | | | | | | |
| {id-7} | | | | | | | | | |
| {id-8} | | | | | | | | | |
| {id-9} | | | | | | | | | |

**Evidence:**
- **{id-1}** D0: … D7: …
- **{id-2}** D0: … D7: …
- **{id-3}** D0: … D7: …
- **{id-4}** D0: … D7: …
- **{id-5}** D0: … D7: …
- **{id-6}** D0: … D7: …
- **{id-7}** D0: … D7: …
- **{id-8}** D0: … D7: …
- **{id-9}** D0: … D7: …

**Condition guess (optional):** {evaluator: which IDs share a condition? confidence: low/medium/high}

#### Outputs

**{id-1}:**
{INSERT OUTPUT #1}

**{id-2}:**
{INSERT OUTPUT #2}

**{id-3}:**
{INSERT OUTPUT #3}

**{id-4}:**
{INSERT OUTPUT #4}

**{id-5}:**
{INSERT OUTPUT #5}

**{id-6}:**
{INSERT OUTPUT #6}

**{id-7}:**
{INSERT OUTPUT #7}

**{id-8}:**
{INSERT OUTPUT #8}

**{id-9}:**
{INSERT OUTPUT #9}

---

### C2 — Full activation | Max: 20

**Prompt:** "What logging library should I use for a Node.js microservice?"

| output_id | D0 | D1 | D2 | D3 | D4 | D5 | D6 | D7 | total |
|-----------|----|----|----|----|----|----|----|----|-------|
| {id-1} | | | | | | | | | |
| {id-2} | | | | | | | | | |
| {id-3} | | | | | | | | | |
| {id-4} | | | | | | | | | |
| {id-5} | | | | | | | | | |
| {id-6} | | | | | | | | | |
| {id-7} | | | | | | | | | |
| {id-8} | | | | | | | | | |
| {id-9} | | | | | | | | | |

**Evidence:**
- **{id-1}** D0: … D7: …
- **{id-2}** D0: … D7: …
- **{id-3}** D0: … D7: …
- **{id-4}** D0: … D7: …
- **{id-5}** D0: … D7: …
- **{id-6}** D0: … D7: …
- **{id-7}** D0: … D7: …
- **{id-8}** D0: … D7: …
- **{id-9}** D0: … D7: …

**Condition guess (optional):** {evaluator: which IDs share a condition? confidence: low/medium/high}

#### Outputs

**{id-1}:**
{INSERT OUTPUT #1}

**{id-2}:**
{INSERT OUTPUT #2}

**{id-3}:**
{INSERT OUTPUT #3}

**{id-4}:**
{INSERT OUTPUT #4}

**{id-5}:**
{INSERT OUTPUT #5}

**{id-6}:**
{INSERT OUTPUT #6}

**{id-7}:**
{INSERT OUTPUT #7}

**{id-8}:**
{INSERT OUTPUT #8}

**{id-9}:**
{INSERT OUTPUT #9}

