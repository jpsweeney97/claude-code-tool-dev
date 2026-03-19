# Skill Composability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add structural contracts, explicit handoffs, and a feedback loop between the adversarial-review, next-steps, and cross-model:dialogue skills.

**Architecture:** Each skill remains standalone-first with protocol-rich composition. Structured capsules/sentinels are appended to existing prose output. A shared composition contract governs artifact schemas, consumer classes, routing rules, and staleness detection. The dialogue skill consumes upstream handoffs through its existing pipeline stages. Advisory/tolerant consumers emit a diagnostic when falling back to prose parsing.

**Tech Stack:** Markdown instruction documents (SKILL.md files), YAML-in-markdown capsule schemas. No code changes.

**Spec:** `docs/superpowers/specs/2026-03-18-skill-composability-design.md`

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `packages/plugins/cross-model/references/composition-contract.md` | Create | Shared artifact schemas, consumer classes, routing rules, material-delta, staleness, guardrails |
| `.claude/skills/adversarial-review/SKILL.md` | Modify | Add capsule emission, `/next-steps` suggestion, composition stub |
| `.claude/skills/next-steps/SKILL.md` | Modify | Add AR capsule consumption, NS handoff block emission, composition stub |
| `packages/plugins/cross-model/skills/dialogue/SKILL.md` | Modify | Add handoff detection, enriched decomposition, feedback capsule, routing classification |

---

### Task 1: Create the shared composition contract

**Files:**
- Create: `packages/plugins/cross-model/references/composition-contract.md`

This is the foundation — all other tasks reference it. Target ~60-80 lines. Must be self-contained per the standalone-layers principle.

- [ ] **Step 1: Write the composition contract**

```markdown
# Composition Contract

**Version:** 1.0.0
**Purpose:** Shared protocol for inter-skill composition between adversarial-review, next-steps, and cross-model:dialogue. Governs artifact identity, capsule formats, consumer behavior, routing rules, and loop guardrails.

---

## Artifact Metadata

Every capsule includes these fields:

| Field | Type | Purpose |
|-------|------|---------|
| `artifact_id` | `<prefix>:<subject_key>:<created_at_compact>` | Unique identity for this skill-run snapshot |
| `artifact_kind` | `adversarial_review \| next_steps_plan \| dialogue_feedback` | Artifact type |
| `subject_key` | kebab-case string | What is being analyzed — shared across reruns |
| `topic_key` | kebab-case string | Coarse grouping for iteration budget |
| `created_at` | ISO 8601, UTC, millisecond precision (`YYYY-MM-DDTHH:MM:SS.sssZ`) | When this artifact was produced |
| `supersedes` | artifact_id or null | Prior artifact of same kind and subject_key |
| `source_artifacts` | list of `{artifact_id, artifact_kind, role}` | Cross-skill provenance |
| `record_path` | path or null | Optional durable file location |

**Artifact ID prefixes:** `ar:` (adversarial_review), `ns:` (next_steps_plan), `dialogue:` (dialogue_feedback).

**Two identity keys:** `subject_key` for exact lineage matching (staleness, supersession). `topic_key` for coarse grouping (soft iteration budget); also propagated via inheritance by all downstream skills. Generic inheritance rule: if a skill directly consumes an upstream capsule, it inherits both keys; if no upstream capsule is consumed, the skill mints both keys from its basis field. This applies in all directions, including the feedback loop (dialogue → AR re-review). Finding IDs, task IDs, and gate IDs are snapshot-scoped — they are valid only within their artifact.

---

## Capsule Sentinels

| Sentinel | Producer | Purpose |
|----------|----------|---------|
| `<!-- ar-capsule:v1 -->` | adversarial-review | Diagnosis findings for NS consumption |
| `<!-- next-steps-dialogue-handoff:v1 -->` | next-steps | Task context for dialogue pipeline |
| `<!-- dialogue-feedback-capsule:v1 -->` | dialogue | Synthesis outcomes for AR/NS feedback |

**Version handling:** If a consumer encounters an unknown sentinel version (e.g., `v2` when it knows `v1`), reject the capsule but continue the skill's normal pipeline. "Reject block, not session."

---

## Consumer Classes

| Class | Behavior | When capsule absent | When capsule invalid |
|-------|----------|--------------------|--------------------|
| Advisory/tolerant | Validate if present; enhance processing. Emit diagnostic on fallback. | Fall back to prose parsing; emit diagnostic | Fall back to prose parsing; emit diagnostic |
| Strict/deterministic | Validate; reject invalid but continue pipeline | Continue normal pipeline | Log warning; continue normal pipeline |

**AR capsule → NS:** advisory/tolerant.
**NS handoff → Dialogue:** strict/deterministic.
**Dialogue feedback → AR/NS:** advisory/tolerant.

---

## Routing Classification

When dialogue produces feedback_candidates, classify each item:

| Signal | Suggested arc | Precedence |
|--------|--------------|------------|
| References upstream `finding_id` or `assumption_id` | `adversarial-review` | 1 (highest) |
| References upstream `task_id`, `gate_id`, or critical path | `next-steps` | 2 |
| References neither; evidence/framing question | `dialogue_continue` | 3 |
| Hits both AR and NS surfaces | `adversarial-review` | 1 (diagnosis before planning) |

For items without explicit upstream ID references: constrained LLM classification. Output: one of `ar | ns | dialogue_continue | ambiguous`, affected surface, one-line reason, `classifier_source: model`.

---

## Material-Delta Gating

Evaluate in tier order. Stop at first match.

**Tier 1 — Pre-screening exclusions:** Not material if: restatement, implementation detail, low-support idea with no upstream refs, existing open question. Set `materiality_source: rule` (or `model` when criterion required interpretation).

**Tier 2 — Inclusions (rule):** Material if: reopens/contradicts RESOLVED, or crosses action threshold (assumption → `wishful`, finding → `blocking`/`high`, task on/off critical path). Set `materiality_source: rule`.

**Tier 3 — Semantic (model):** If no tier matched: evaluate whether item introduces new risk/alternative changing diagnostic surface, or new dependency/blocker changing planning surface. Set `materiality_source: model`.

---

## Staleness Detection

| Status | Condition | Consumer behavior |
|--------|-----------|------------------|
| `current` | No superseder; all source_artifacts current | Proceed normally |
| `superseded` | Newer same-kind same-subject artifact exists | Prefer newer artifact |
| `stale_inputs` | Source artifact has been superseded | Warn user; suggest rebase |
| `unknown` | Insufficient lineage metadata | Do not block; continue |

---

## Loop Guardrails

1. **No auto-chaining.** Skills suggest the next arc; the user confirms.
2. **Material-delta gating.** Do not recommend a hop unless something changed.
3. **Soft iteration budget.** After 2 targeted loops in the same topic (same `topic_key`), stop suggesting further hops. Report remaining open items.

---

## Capsule Emission Rule

Skills emit capsules when invoked explicitly. Global CLAUDE.md protocols (Adversarial Self-Review, Next Steps Planning) do NOT auto-emit capsules. Same schema when externalized via skill invocation; no schema obligation when used as internal reasoning scaffolding.
```

- [ ] **Step 2: Verify the contract is self-contained**

Read the file. Check:
- All sentinel names are defined
- All consumer classes are specified
- Routing rules cover all cases (including ambiguous)
- Material-delta has both positive and negative criteria
- No forward references to skill files for definitions

- [ ] **Step 3: Commit**

```bash
git add packages/plugins/cross-model/references/composition-contract.md
git commit -m "feat: add shared composition contract for skill composability"
```

---

### Task 2: Add AR capsule emission to adversarial-review

**Files:**
- Modify: `.claude/skills/adversarial-review/SKILL.md:97-131` (after output format, before durable record)

- [ ] **Step 1: Add capsule emission section after the output format section**

Insert after the output format section (line 123, after the closing `` ``` `` of the format template) and before "Durable record":

```markdown
## Capsule emission

After producing the review output, always append a machine-readable capsule for downstream skill consumption. The capsule is enclosed in sentinel comments and uses YAML format.

Emit the capsule after the Confidence Check section, separated by a blank line. Do NOT omit the capsule even if the review found no material flaws — downstream skills use the `overall_confidence` and empty `findings` list as positive signals.

**Sentinel:** `<!-- ar-capsule:v1 -->`

**Schema:**

```yaml
<!-- ar-capsule:v1 -->
artifact_id: ar:<subject_key>:<created_at_compact>
artifact_kind: adversarial_review
subject_key: <kebab-case target identifier derived from the review target>
topic_key: <coarse grouping key — same as subject_key unless reviewing a facet of a broader topic>
created_at: <ISO 8601, UTC, millisecond precision: YYYY-MM-DDTHH:MM:SS.sssZ>
supersedes: <artifact_id of the prior review of this same subject, or null if first review>
source_artifacts: []
record_path: <path to docs/reviews/ file if written, or null>

review_target: <one-line description matching the "Adversarial Review: [target]" heading>
overall_confidence: <1-5 score from the Confidence Check>
findings:
  - finding_id: F1
    severity: <blocking | high | moderate | low>
    summary: <one-line from Severity Summary>
assumptions:
  - assumption_id: A1
    text: <assumption text from Assumptions Audit>
    status: <validated | plausible | wishful>
    if_wrong: <what breaks — from the Assumptions Audit>
open_questions:
  - <any unresolved questions surfaced during the review>
<!-- /ar-capsule:v1 -->
```

**Field mapping:**
- `findings` mirrors the Severity Summary section. Use the same finding order and severity tags.
- `assumptions` mirrors the Assumptions Audit. `if_wrong` is the "what breaks" clause already present in the audit.
- `open_questions` captures questions that arose during the review but were not answered.
- Timestamp in artifact_id provides collision resistance. No sequence counter needed.

**Composition contract:** This capsule follows the artifact metadata schema inlined as minimal operational subset in this skill. NS consumes it as advisory/tolerant — the capsule enhances but is not required. Full protocol: `packages/plugins/cross-model/references/composition-contract.md`.
```

- [ ] **Step 2: Add "After the review" section before Anti-patterns**

Insert after the "Durable record" section and before "Anti-patterns":

```markdown
## After the review

If this review surfaced multiple findings that need coordinated action, suggest the user invoke `/next-steps` to sequence the work into a dependency-aware action plan.

If a dialogue feedback capsule (`<!-- dialogue-feedback-capsule:v1 -->`) is present in the conversation, check whether any EMERGED or UNRESOLVED items triggered this re-review. If so, reference the specific items and their `item_id` values in your review to maintain lineage.
```

- [ ] **Step 3: Cross-reference check**

Read the modified file. Verify:
- Sentinel name matches composition contract: `<!-- ar-capsule:v1 -->`
- All field names in the capsule match the spec schema exactly
- Finding severity enum matches existing output format: `blocking | high | moderate | low`
- Assumption status enum matches existing output: `validated | plausible | wishful`
- The capsule section does not introduce implementation planning (preserves "separate diagnosis from remediation")

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/adversarial-review/SKILL.md
git commit -m "feat(adversarial-review): add AR capsule emission and next-steps suggestion"
```

---

### Task 3: Add AR capsule consumption and NS handoff to next-steps

**Files:**
- Modify: `.claude/skills/next-steps/SKILL.md:46-157` (workflow and after-plan sections)

- [ ] **Step 1: Add AR capsule consumption to the workflow**

Insert a new section after "## Workflow" and before "### 1. Summarize the current state":

```markdown
### 0. Check for upstream capsules

Before starting the workflow, scan the conversation for structured capsules from upstream skills.

**AR capsule (`<!-- ar-capsule:v1 -->`):** If present, extract `findings`, `assumptions`, `overall_confidence`, and `artifact_id`. Use these as the primary input for the dependency map:
- Each finding with severity `blocking` or `high` should map to at least one strategic task.
- Assumptions tagged `wishful` are candidate risks that may need their own resolution task.
- Record the AR `artifact_id` for lineage — it becomes a `source_artifacts` entry in the NS handoff.

**If the AR capsule is absent or invalid:** Fall back to reading the conversation prose for findings. Emit a one-line diagnostic: "AR capsule not detected; lineage tracking unavailable for this run." This is the default behavior today — the capsule enhances but does not replace it.

**Dialogue feedback capsule (`<!-- dialogue-feedback-capsule:v1 -->`):** If present, extract `unresolved` and `emerged` items. Treat EMERGED items as new findings to incorporate into the plan. Treat UNRESOLVED items as open questions that may need their own task or decision gate.
```

- [ ] **Step 2: Replace the "After producing the plan" section**

Replace the existing section at line 155-157 with:

```markdown
## After producing the plan

Suggest the user take the highest-risk or first-phase tasks into a Codex dialogue for deeper exploration. Use the literal slash command `/cross-model:dialogue` so the user can invoke it directly.

For the recommended task, emit a handoff block that gives `/dialogue` structured context:

**Sentinel:** `<!-- next-steps-dialogue-handoff:v1 -->`

This sentinel is distinct from `<!-- dialogue-orchestrated-briefing -->`. The NS handoff is input to dialogue's pipeline, not a replacement for it.

```yaml
<!-- next-steps-dialogue-handoff:v1 -->
artifact_id: ns:<subject_key>:<created_at_compact>
artifact_kind: next_steps_plan
subject_key: <kebab-case subject identifier matching the plan topic — inherited from AR capsule if consumed, otherwise derived from plan topic>
topic_key: <inherited from AR capsule if consumed, otherwise derived from plan topic>
created_at: <ISO 8601, UTC, millisecond precision: YYYY-MM-DDTHH:MM:SS.sssZ>
supersedes: <prior NS artifact_id for this subject, or null>
source_artifacts:
  - artifact_id: <AR artifact_id if AR capsule was consumed, omit entry if not>
    artifact_kind: adversarial_review
    role: diagnosis
record_path: null

focus_question: <what this dialogue should resolve — derived from the recommended task>
recommended_posture: <adversarial | collaborative | exploratory — based on the task's nature>
selected_tasks:
  - task_id: <T-ID from the plan>
    task: <task description>
    why_now: <why this task is the recommended starting point>
    depends_on: [<dependency T-IDs>]
    done_when: <strategic completion condition from the plan>
decision_gates:
  - gate_id: <G-ID>
    after: <T-ID>
    condition: <the decision gate condition from the plan>
source_findings:
  - finding_id: <F-ID from AR capsule>
    severity: <severity>
    summary: <finding summary>
out_of_scope:
  - <parked items from section 6>
<!-- /next-steps-dialogue-handoff:v1 -->
```

**Posture precedence:** The `recommended_posture` is a hint — the lowest priority in dialogue's resolution chain. Explicit `--posture` and `--profile` flags override it.

**Provenance fallback:** If AR capsule was not structurally consumed (prose fallback), omit the AR entry from source_artifacts entirely.

**Composition contract:** This handoff follows the artifact metadata schema inlined as minimal operational subset in this skill. Dialogue consumes it as strict/deterministic. Full protocol: `packages/plugins/cross-model/references/composition-contract.md`.
```

- [ ] **Step 3: Cross-reference check**

Read the modified file. Verify:
- Sentinel name matches: `<!-- next-steps-dialogue-handoff:v1 -->`
- All field names match the spec schema: `focus_question`, `recommended_posture`, `selected_tasks`, `decision_gates` (with `gate_id`), `source_findings`, `out_of_scope`
- `source_artifacts` correctly references AR capsule `artifact_id`
- Consumer class language matches contract: "strict/deterministic"
- The handoff block does not include plan prose — only structured data

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/next-steps/SKILL.md
git commit -m "feat(next-steps): add AR capsule consumption and NS dialogue handoff"
```

---

### Task 4: Add NS handoff detection to dialogue (pre-Step 0)

**Files:**
- Modify: `packages/plugins/cross-model/skills/dialogue/SKILL.md:49-53` (before Step 0)

- [ ] **Step 1: Add pre-Step 0 handoff detection section**

Insert after the "## Pipeline" heading (line 49) and before "### Step 0":

```markdown
### Pre-Step 0: Detect upstream handoff

Before any pipeline processing, scan the conversation for `<!-- next-steps-dialogue-handoff:v1 -->`.

**If found:**
1. Parse the YAML content between the opening and closing sentinel comments.
2. Validate required fields: `artifact_id`, `focus_question`, `selected_tasks` (non-empty list).
3. If valid: store as `upstream_handoff` pipeline state. Set `handoff_detected: true`.
4. If invalid (missing required fields, malformed YAML): log a warning. Set `handoff_detected: false`. Continue normal pipeline — do not block.

**If not found:** Set `handoff_detected: false`. Continue normal pipeline.

**Unknown version handling:** If the sentinel version is not `v1` (e.g., `<!-- next-steps-dialogue-handoff:v2 -->`), reject the block. Set `handoff_detected: false`. Continue normal pipeline. "Reject block, not session."

**Pipeline state initialization:** Add these fields alongside the existing planning pipeline fields:

| Field | Initial value | Set by |
|-------|--------------|--------|
| `handoff_detected` | false | Pre-Step 0 |
| `handoff_source_artifact` | null | Pre-Step 0 (from `artifact_id` in handoff) |
| `handoff_enriched` | false | Step 0 (true when `--plan` AND `handoff_detected`) |

**Posture resolution update:** When `handoff_detected` is true and `upstream_handoff` contains `recommended_posture`, add it to the resolution chain:

```
explicit --posture > --profile > upstream_handoff.recommended_posture > default collaborative
```
```

- [ ] **Step 2: Verify no collision with existing pipeline state fields**

Read the dialogue SKILL.md's existing pipeline state fields (Step 0 initialization). Confirm:
- `handoff_detected`, `handoff_source_artifact`, `handoff_enriched` do not collide with existing field names
- The posture resolution chain addition is consistent with existing precedence documentation

- [ ] **Step 3: Commit**

```bash
git add packages/plugins/cross-model/skills/dialogue/SKILL.md
git commit -m "feat(dialogue): add NS handoff detection in pre-Step 0"
```

---

### Task 5: Add handoff_enriched decomposition to dialogue Step 0

**Files:**
- Modify: `packages/plugins/cross-model/skills/dialogue/SKILL.md:51-140` (Step 0 section)

- [ ] **Step 1: Add handoff_enriched mode to Step 0**

Insert after the existing `--plan` skip check ("Skip this step if `--plan` is not set") and before the debug gate:

```markdown
**Mode selection:** When `--plan` is set, determine which decomposition mode to use:
- If `handoff_detected` is true: use `handoff_enriched` mode.
- If `handoff_detected` is false: use `raw_input` mode (current behavior).

Set `handoff_enriched` pipeline field to `true` or `false` accordingly.
```

Insert after the existing decomposition template (the ```````` block) and before validation:

```markdown
**Handoff-enriched decomposition:** When in `handoff_enriched` mode, replace the decomposition template with:

````
Given this problem statement: "{raw_input}"

Upstream context from a strategic action plan:
- Focus question: {upstream_handoff.focus_question}
- Selected task: {upstream_handoff.selected_tasks[0].task}
- Done when: {upstream_handoff.selected_tasks[0].done_when}
- Source findings: {upstream_handoff.source_findings, formatted as "F-ID: severity - summary"}
- Decision gates: {upstream_handoff.decision_gates, formatted as "after T-ID: condition"}

Decompose into:
1. A focused, answerable question (one sentence) — grounded in the focus question and the user's raw input
2. 2-5 testable assumptions — derived from the source findings but NOT restating them verbatim
3. 3-8 search terms — include entity names from the task context, findings, and decision gates
4. Your confidence that this decomposition captures the user's intent (high/medium/low)
5. 0-3 ambiguities — seed from decision gate conditions

IMPORTANT — Three-tier tautology filter:
- Do NOT restate the focus_question or the user's raw question as an assumption
- Do NOT parrot task descriptions, done_when conditions, or dependency statements as assumptions
- Source findings can INSPIRE derived assumptions but must NOT be restated verbatim — a derived assumption must operationalize the finding (make it testable against the codebase), not merely reword it

Format:
planning_question: ...
assumptions:
- A1: "..."
- A2: "..."
key_terms: [term1, term2, ...]
shape_confidence: high|medium|low
ambiguities:
- ...
````

The validation, normalization, and confidence downgrade rules from `raw_input` mode apply identically to `handoff_enriched` output.
```

- [ ] **Step 2: Cross-reference check**

Verify:
- The enriched template references `upstream_handoff` fields that match the NS handoff schema exactly: `focus_question`, `selected_tasks[].task`, `selected_tasks[].done_when`, `source_findings`, `decision_gates`
- The tautology filter instruction matches the spec's three tiers
- Validation/normalization rules are not duplicated — the existing rules are referenced by "apply identically"

- [ ] **Step 3: Commit**

```bash
git add packages/plugins/cross-model/skills/dialogue/SKILL.md
git commit -m "feat(dialogue): add handoff_enriched decomposition mode to Step 0"
```

---

### Task 6: Thread handoff through dialogue Steps 2-3

**Files:**
- Modify: `packages/plugins/cross-model/skills/dialogue/SKILL.md` (Steps 2, 3h, 3c)

- [ ] **Step 1: Add enriched gatherer seeds to Step 2**

Insert after the existing Gatherer A prompt description ("derive terms from the question as usual"):

```markdown
When `handoff_detected` is true (regardless of whether `--plan` is set), enrich the gatherer prompts:

**Gatherer A enrichment:** Append to the key terms: entity names from `upstream_handoff.selected_tasks[].task`, file paths or concepts from `upstream_handoff.source_findings[].summary`, and condition terms from `upstream_handoff.decision_gates[].condition`.

**Gatherer B enrichment:** If `upstream_handoff.source_findings` is non-empty, include the source findings as additional context alongside the assumptions: "The following findings from a prior review are relevant: {source_findings, formatted as F-ID: severity - summary}. Consider whether these findings are supported, contradicted, or complicated by codebase evidence."
```

- [ ] **Step 2: Add upstream context to briefing assembly (Step 3h)**

Insert in the Step 3h grouping section, after the `## Context` assembly and before `## Prior Learnings`:

```markdown
**Upstream handoff projection:** When `handoff_detected` is true, insert a subsection in the briefing's `## Context` after the CONFIRM items and before `## Prior Learnings`:

```
## Upstream Plan Context
Task: {upstream_handoff.selected_tasks[0].task_id}: {upstream_handoff.selected_tasks[0].task}
Done when: {upstream_handoff.selected_tasks[0].done_when}
Source findings: {upstream_handoff.source_findings, one per line as "F-ID [severity]: summary"}
Decision gates: {upstream_handoff.decision_gates, one per line as "After T-ID: condition"}
Source artifact: {upstream_handoff.artifact_id}
```

This is a deterministic projection — no LLM processing. The section is included verbatim in the briefing sent to codex-dialogue.
```

- [ ] **Step 3: Add upstream context to zero-output fallback (Step 3c)**

Insert in the Step 3c zero-output fallback briefing template, after `## Context` and before `## Prior Learnings`:

```markdown
When `handoff_detected` is true and Step 3c fires, include the upstream handoff projection in the fallback briefing:

```
<!-- dialogue-orchestrated-briefing -->
## Context
(Context gathering produced insufficient results. Rely on mid-dialogue scouting for evidence.)

## Upstream Plan Context
Task: {upstream_handoff.selected_tasks[0].task_id}: {upstream_handoff.selected_tasks[0].task}
Done when: {upstream_handoff.selected_tasks[0].done_when}
Source findings: {upstream_handoff.source_findings}
Decision gates: {upstream_handoff.decision_gates}
Source artifact: {upstream_handoff.artifact_id}

## Prior Learnings
{learning_entries from retrieval step, if non-empty}

## Material
(none)

## Question
{user's question, verbatim}
```

In the zero-output case, the upstream plan context may be the primary grounding alongside learnings.
```

- [ ] **Step 4: Cross-reference check**

Verify:
- The `## Upstream Plan Context` section uses field names from the NS handoff schema
- The zero-output fallback still includes the `<!-- dialogue-orchestrated-briefing -->` sentinel
- The upstream projection is deterministic (no LLM processing) — consistent with Step 3's non-LLM assembly constraint

- [ ] **Step 5: Commit**

```bash
git add packages/plugins/cross-model/skills/dialogue/SKILL.md
git commit -m "feat(dialogue): thread NS handoff through Steps 2, 3h, 3c"
```

---

### Task 7: Add feedback capsule emission to dialogue

**Files:**
- Modify: `packages/plugins/cross-model/skills/dialogue/SKILL.md` (after Step 6)

- [ ] **Step 1: Add Step 6b: Emit feedback capsule**

Insert after Step 6 ("Present synthesis") and before Step 7 ("Emit analytics"):

```markdown
### Step 6b: Emit feedback capsule

After presenting the synthesis to the user, append a dialogue feedback capsule. This capsule is derived from the codex-dialogue agent's Synthesis Checkpoint output — it is a machine-readable projection, not a new synthesis.

**Sentinel:** `<!-- dialogue-feedback-capsule:v1 -->`

**Derivation from agent output:**

| Capsule field | Source in agent output |
|---------------|----------------------|
| `resolved[]` | Lines starting with `RESOLVED:` in the Synthesis Checkpoint |
| `unresolved[]` | Lines starting with `UNRESOLVED:` in the Synthesis Checkpoint |
| `emerged[]` | Lines starting with `EMERGED:` in the Synthesis Checkpoint |
| `converged` | Parse from `**Converged:**` in the Conversation Summary |
| `turn_count` | Parse from `**Turns:**` in the Conversation Summary |
| `thread_id` | From the `### Continuation` section |
| `continuation_warranted` | From the `### Continuation` section |
| `recommended_posture` | From `**Recommended posture for continuation:**` or null |

**Artifact metadata:**
- `artifact_id`: `dialogue:<subject_key>:<created_at_compact>`. Derive `subject_key` from the goal/question topic.
- `supersedes`: If this is a fresh dialogue, null. If continuing after a prior dialogue on the same subject, reference the prior `artifact_id`.
- `source_artifacts`: Include the NS handoff as the only direct-edge upstream source (if `handoff_detected`). Dialogue does not directly consume AR — it only consumes NS.

**Item IDs:** Assign sequential IDs: `R1`, `R2`... for resolved; `U1`, `U2`... for unresolved; `E1`, `E2`... for emerged.

**`feedback_candidates[]`:** For each UNRESOLVED and EMERGED item, classify the suggested feedback arc. See Task 8 for the classification procedure.

**Emit format:**

```yaml
<!-- dialogue-feedback-capsule:v1 -->
artifact_id: dialogue:<subject_key>:<created_at_compact>
artifact_kind: dialogue_feedback
subject_key: <derived from goal>
topic_key: <inherited from NS handoff if consumed, otherwise derived from goal topic>
created_at: <ISO 8601, UTC, millisecond precision: YYYY-MM-DDTHH:MM:SS.sssZ>
supersedes: <prior dialogue artifact_id or null>
source_artifacts:
  - artifact_id: <NS artifact_id if handoff consumed>
    artifact_kind: next_steps_plan
    role: plan

thread_id: <Codex thread ID>
converged: <true | false>
turn_count: <int>

resolved:
  - item_id: R1
    text: <resolved item text>
    confidence: <high | medium | low>
unresolved:
  - item_id: U1
    text: <unresolved item text>
emerged:
  - item_id: E1
    text: <emerged item text>

continuation_warranted: <true | false>
recommended_posture: <posture or null>

feedback_candidates:
  - item_id: <U or E item ID>
    suggested_arc: <adversarial-review | next-steps | dialogue_continue | ambiguous>
    affected_surface: <diagnosis | planning | evidence-only>
    affected_refs: [<upstream artifact/finding/task IDs if applicable>]
    material: <true | false>
    materiality_reason: <one-line explanation>
    classifier_source: <rule | model>
    materiality_source: <rule | model>
<!-- /dialogue-feedback-capsule:v1 -->
```

**Composition contract:** This capsule follows the artifact metadata schema inlined as minimal operational subset in this skill. AR and NS consume it as advisory/tolerant. Full protocol: `packages/plugins/cross-model/references/composition-contract.md`.
```

- [ ] **Step 2: Cross-reference check**

Verify:
- Sentinel name matches: `<!-- dialogue-feedback-capsule:v1 -->`
- All fields match the spec schema in Contract 3
- Derivation sources reference actual codex-dialogue output markers (`RESOLVED:`, `UNRESOLVED:`, `EMERGED:`, `**Converged:**`)
- `source_artifacts` correctly references upstream capsules consumed in this run
- feedback_candidates references Task 8's classification procedure

- [ ] **Step 3: Commit**

```bash
git add packages/plugins/cross-model/skills/dialogue/SKILL.md
git commit -m "feat(dialogue): add feedback capsule emission after synthesis"
```

---

### Task 8: Add routing classification and feedback presentation to dialogue

**Files:**
- Modify: `packages/plugins/cross-model/skills/dialogue/SKILL.md` (within Step 6b, after capsule emission)

- [ ] **Step 1: Add classification procedure to Step 6b**

Insert after the capsule emission format and before the composition contract reference:

```markdown
**Classification procedure for `feedback_candidates`:**

For each UNRESOLVED and EMERGED item, determine the suggested feedback arc:

**Step A — Reference-based classification (deterministic):**
1. Scan the item text for upstream artifact references: `finding_id` (F1, F2...), `assumption_id` (A1, A2...), `task_id` (T1, T2...), `gate_id` (G1, G2...).
2. If the item references `finding_id` or `assumption_id`: `suggested_arc = adversarial-review`, `affected_surface = diagnosis`.
3. If the item references `task_id` or `gate_id`: `suggested_arc = next-steps`, `affected_surface = planning`.
4. If both: `suggested_arc = adversarial-review` (diagnosis before planning precedence).
5. Set `classifier_source = rule`.

**Step B — Constrained LLM classification (fallback for items without explicit ID references):**
1. If Step A found no upstream references, classify using judgment.
2. Output MUST be one of: `ar | ns | dialogue_continue | ambiguous`.
3. Name the `affected_surface`: `diagnosis | planning | evidence-only`.
4. Provide a one-line `materiality_reason`.
5. Set `classifier_source = model`.

**Dimension independence:** `classifier_source` and `suggested_arc` are independent dimensions. `classifier_source` describes the classification *method* (deterministic rule vs. LLM judgment). `suggested_arc` describes the routing *outcome* (where the item should go). `ambiguous` is a valid outcome (`suggested_arc = ambiguous`) but not a valid method — every classification is performed by either a rule or the model.

**Material-delta gating:** Apply the tiered material-delta rules from the composition contract (`packages/plugins/cross-model/references/composition-contract.md`): Tier 1 exclusions (rule) → Tier 2 inclusions (rule) → Tier 3 semantic (model). Set `material = true | false` and `materiality_source = rule | model`.

**Loop guardrails:** After classifying all items, check the soft iteration budget:
- Count how many AR or NS capsules in the conversation share the same `topic_key` as this dialogue's topic.
- If the count is >= 2 (meaning 2 prior targeted loops on this subject): do NOT suggest further hops. Instead, after the capsule, state: "This subject has been through multiple review cycles. Remaining open items: [list]. Further iteration is at your discretion."
- If the count is < 2: present the feedback candidates with material items highlighted.

**Feedback presentation:** After the capsule, present a human-readable summary:

```markdown
### Suggested next steps

Based on the dialogue outcomes:
- [item_id]: [suggested arc] — [materiality_reason]
- ...

To follow up: `/adversarial-review [target]` or `/next-steps` as suggested above.
```

Do NOT auto-invoke any skill. The user decides which arc to follow.
```

- [ ] **Step 2: Add thread continuation rules**

Insert after the feedback presentation:

```markdown
### Thread continuation rules

**Hard rule: new artifact → new thread.**

If the user follows a feedback arc (invokes AR or NS) and then returns to `/dialogue`:
- If new AR or NS capsules exist since this dialogue: start a fresh `/dialogue` with new briefing. Do NOT continue this thread.
- If no new capsules exist and the user wants to continue exploring the same unresolved items: thread continuation is permitted using the `thread_id` from this capsule.

**When continuation is permitted:** Same goal, same upstream snapshot set, operational interruption (budget exhaustion, scope breach resolved), or narrow follow-up on unresolved evidence questions.
```

- [ ] **Step 3: Cross-reference check**

Verify:
- Classification references match composition contract routing table
- Material-delta references match composition contract section
- Loop guardrail count of 2 matches composition contract
- Thread continuation rules match spec's "new artifact → new thread" hard rule

- [ ] **Step 4: Commit**

```bash
git add packages/plugins/cross-model/skills/dialogue/SKILL.md
git commit -m "feat(dialogue): add routing classification, material-delta, and loop guardrails"
```

---

## Task Dependencies

```
Task 1 (contract) ──┬──► Task 2 (AR capsule)
                    ├──► Task 3 (NS handoff) ──► Task 4 (dialogue handoff detection)
                    │                              └──► Task 5 (enriched decomposition)
                    │                                    └──► Task 6 (thread through pipeline)
                    └──► Task 7 (feedback capsule) ──► Task 8 (routing classification)
```

**Parallel tracks after Task 1:**
- Track A: Tasks 2 → (independent after commit)
- Track B: Tasks 3 → 4 → 5 → 6
- Track C: Tasks 7 → 8

Track B depends on Task 3's sentinel format being committed. Tasks 7-8 can start after Task 1 (they don't consume NS handoff output, only emit capsules).

## Verification Checklist

After all tasks are complete, run these cross-file consistency checks:

- [ ] All sentinel names match across all 4 files (contract, AR, NS, dialogue)
- [ ] All field names in capsule schemas match between producer and consumer
- [ ] AR capsule fields in adversarial-review match what next-steps consumes in Step 0
- [ ] NS handoff fields in next-steps match what dialogue consumes in pre-Step 0
- [ ] Dialogue feedback capsule fields match what AR and NS consume
- [ ] Consumer class labels are consistent: AR→NS is advisory/tolerant, NS→Dialogue is strict/deterministic
- [ ] Each skill works standalone without upstream capsules (graceful degradation verified)
- [ ] Composition contract is referenced from all three skills with correct file path
- [ ] No skill file exceeds ~600 lines after modifications
- [ ] All capsule schemas use `<prefix>:<subject_key>:<created_at_compact>` format (no sequence numbers)
- [ ] All schemas include both `subject_key` and `topic_key`
- [ ] Inheritance rules documented: generic rule (consume upstream → inherit; no upstream → mint) with feedback loop examples
- [ ] Loop guardrails use `topic_key`, staleness uses `subject_key`
- [ ] Contract 3 source_artifacts is direct-edge only (NS, not AR)
- [ ] `classifier_source = rule | model` — `ambiguous` removed from method, retained in `suggested_arc`
- [ ] Composition contract stubs are self-contained (not "see the contract")
- [ ] Advisory/tolerant consumer class includes diagnostic emission requirement
- [ ] No reference to SS2 governance in boundary clarification
- [ ] All `created_at` fields specify millisecond precision (`YYYY-MM-DDTHH:MM:SS.sssZ`)
- [ ] Material-delta section uses tiered evaluation (exclusions → inclusions → model)
- [ ] D1 heading says "standalone-first, protocol-rich composition"
- [ ] topic_key "Used by" mentions inheritance propagation
- [ ] Composition stubs include contract path reference
