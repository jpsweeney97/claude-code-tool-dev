# Skill Composability Design Amendments

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply 5 amendments from the system design review + Codex dialogue to the skill composability design spec and implementation plan, before the main implementation plan can be executed.

**Architecture:** All amendments target two markdown documents — the design spec (authoritative) and the implementation plan (derived). The identity model change (Task 1) is the critical path because it touches every capsule schema. All other spec amendments are parallel. Plan propagation (Task 6) depends on all spec amendments completing first.

**Tech Stack:** Markdown documents only. No code changes.

**Spec:** `docs/superpowers/specs/2026-03-18-skill-composability-design.md`
**Implementation plan:** `docs/superpowers/plans/2026-03-18-skill-composability.md`
**Source:** System design review (2026-03-19) + Codex dialogue thread `019d0682-3f52-70a1-b7ed-e536ad2b8652`

---

## Context: Design Review Outcomes

| Finding | Disposition | Amendment |
|---------|------------|-----------|
| F1 (pipeline coupling) | Closed by counter-evidence | Note only — pipeline steps are the public contract |
| F2 (provenance corruption) | Design change | Direct-edge provenance only (Task 2) |
| F3 (artifact identity) | Design change | Split-field identity + timestamp IDs + inheritance (Task 1) |
| F4 (classifier schema) | Design change | Narrow `classifier_source` to `rule \| model` (Task 4) |
| F5 (tautology filter) | Acceptable for v1 | Add examples (Task 5, lower priority) |
| F6 (deployment path) | Design change | Authoritative contract + inline stubs (Task 3) |
| F7 (contract versioning) | Acceptable tradeoff | Sentinel versioning is sufficient (no change) |

Emerged concepts from dialogue: split-field identity, inheritance-first propagation, timestamp-based artifact IDs.

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `docs/superpowers/specs/2026-03-18-skill-composability-design.md` | Modify | All 5 spec amendments |
| `docs/superpowers/plans/2026-03-18-skill-composability.md` | Modify | Propagate spec changes to implementation plan |

---

### Task 1: Amend identity model (F3 — critical path)

**Files:**
- Modify: `docs/superpowers/specs/2026-03-18-skill-composability-design.md:376-427` (Lineage Model section)
- Modify: `docs/superpowers/specs/2026-03-18-skill-composability-design.md:89-114` (Contract 1 schema)
- Modify: `docs/superpowers/specs/2026-03-18-skill-composability-design.md:161-194` (Contract 2 schema)
- Modify: `docs/superpowers/specs/2026-03-18-skill-composability-design.md:244-285` (Contract 3 schema)
- Modify: `docs/superpowers/specs/2026-03-18-skill-composability-design.md:350-354` (Loop guardrails)

This is the highest-risk amendment. It defines the new artifact identity scheme that all capsule schemas use.

- [ ] **Step 1: Replace the Lineage Model > Artifact identity and Artifact ID format sections (lines 378-399)**

Replace the content between `### Artifact identity` and `### DAG structure` with:

```markdown
### Artifact identity

An artifact is one skill-run snapshot. The capsule is the machine-readable projection of that artifact — not a separate entity.

| Skill run | Artifact kind |
|-----------|--------------|
| One adversarial-review run | `adversarial_review` |
| One next-steps run | `next_steps_plan` |
| One /dialogue run | `dialogue_feedback` |

### Two identity keys

Each artifact carries two identity keys serving different purposes:

| Key | Purpose | Format | Example | Used by |
|-----|---------|--------|---------|---------|
| `subject_key` | Exact lineage matching (staleness, supersession) | kebab-case, deterministic from target | `redaction-pipeline` | Staleness detection, `supersedes` links |
| `topic_key` | Coarse grouping (soft iteration budget) | kebab-case, broader than subject_key | `redaction-pipeline` | Loop guardrails only |

For simple targets, `subject_key` and `topic_key` may be identical. They diverge when a subject is a specific facet of a broader topic (e.g., subject_key `redaction-format-layer` under topic_key `redaction-pipeline`).

**Normalization rules for `subject_key` (exact key — minimally lossy):**
- Lowercase, replace spaces/underscores with hyphens
- Remove leading/trailing whitespace
- No character limit — preserve full target specificity for exact lineage matching
- Derived from the skill's basis field when minting, or inherited from upstream capsule

**Normalization rules for `topic_key` (coarse key — grouping):**
- Same base normalization as `subject_key`
- Additionally: strip articles (a, an, the), trailing qualifiers, and implementation-specific suffixes
- Limit to 50 characters, truncate at word boundary
- Represents the broadest topic this analysis belongs to

**Inheritance-first propagation:**
- If a skill directly consumes an upstream capsule (any kind), it inherits both `subject_key` and `topic_key` from that capsule.
- If no upstream capsule is directly consumed, the skill mints both keys from its own basis field (see table below).
- **Rule:** Only the root of a composition chain mints keys. All downstream skills inherit. This eliminates cross-skill key drift.

**Basis fields for key minting (when no upstream capsule is consumed):**

| Skill | Basis field | Example |
|-------|-------------|---------|
| adversarial-review | `review_target` | "the redaction pipeline" → `redaction-pipeline` |
| next-steps | Primary topic of the plan | "redaction pipeline remediation" → `redaction-pipeline-remediation` |
| dialogue | Goal/question topic | "redaction pipeline architecture" → `redaction-pipeline-architecture` |

**Examples of inheritance in the feedback loop:**
- AR (standalone) → mints `redaction-pipeline`
- NS (consumes AR capsule) → inherits `redaction-pipeline`
- Dialogue (consumes NS handoff) → inherits `redaction-pipeline`
- AR (re-review consuming dialogue feedback capsule) → inherits `redaction-pipeline`

### Artifact ID format

```
<kind-prefix>:<subject_key>:<created_at_compact>
```

Where `created_at_compact` is the `created_at` ISO 8601 value with separators removed: `YYYYMMDDTHHMMSS` at minimum, with fractional seconds appended when the `created_at` field includes them (e.g., `YYYYMMDDTHHMMSS.fff`). The timestamp component MUST preserve the full precision of the `created_at` field — do not truncate fractional seconds. All three skills MUST use the same precision.

Examples:
- `ar:redaction-pipeline:20260318T143052.123`
- `ns:redaction-pipeline:20260318T144215.456`
- `dialogue:redaction-pipeline:20260318T151033.789`

**Artifact ID prefixes:** `ar:` (adversarial_review), `ns:` (next_steps_plan), `dialogue:` (dialogue_feedback).

The timestamp component provides collision resistance derived from the full `created_at` precision. Two runs on the same subject at different times produce different artifact IDs. The sequence-based format (`:<01>`) is removed — timestamps are strictly more unique.
```

- [ ] **Step 2: Update Contract 1 (AR capsule) schema (lines 89-114)**

Replace the schema block with:

```yaml
artifact_id: ar:<subject_key>:<created_at_compact>
artifact_kind: adversarial_review
subject_key: <kebab-case derived from review_target, or inherited from upstream feedback capsule>
topic_key: <coarse grouping key — same as subject_key unless reviewing a facet of a broader topic>
created_at: <ISO 8601 full timestamp with fractional seconds, UTC>
supersedes: <prior artifact_id of same kind and subject_key, or null>
source_artifacts: <[] if standalone; include upstream feedback capsule if re-review triggered by dialogue feedback>
record_path: <path to docs/reviews/ file or null>

review_target: <one-line description of what was reviewed>
overall_confidence: <1-5>
findings:
  - finding_id: F1
    severity: blocking | high | moderate | low
    summary: <one-line description>
  - finding_id: F2
    severity: high
    summary: ...
assumptions:
  - assumption_id: A1
    text: <assumption text>
    status: validated | plausible | wishful
    if_wrong: <one-sentence consequence>
open_questions:
  - <question text>
```

- [ ] **Step 3: Update Contract 2 (NS handoff) schema (lines 161-194)**

Replace the schema block with:

```yaml
artifact_id: ns:<subject_key>:<created_at_compact>
artifact_kind: next_steps_plan
subject_key: <inherited from AR capsule if consumed, otherwise derived from plan topic>
topic_key: <inherited from AR capsule if consumed, otherwise derived from plan topic>
created_at: <ISO 8601 full timestamp with fractional seconds, UTC>
supersedes: <prior NS artifact_id for this subject_key, or null>
source_artifacts:
  - artifact_id: <AR artifact_id if AR capsule was consumed, omit entry if not>
    artifact_kind: adversarial_review
    role: diagnosis
record_path: null

focus_question: <what this dialogue should resolve>
recommended_posture: <adversarial | collaborative | exploratory | evaluative | comparative>
selected_tasks:
  - task_id: T2
    task: <task description>
    why_now: <why this task is recommended for dialogue>
    depends_on: [T1]
    done_when: <strategic completion condition>
decision_gates:
  - gate_id: G1
    after: T2
    condition: <if X then path A; otherwise path B>
source_findings:
  - finding_id: F1
    severity: blocking
    summary: <from AR capsule>
  - finding_id: F3
    severity: high
    summary: ...
out_of_scope:
  - <parked item>
```

- [ ] **Step 4: Update Contract 3 (Dialogue feedback) schema (lines 244-285)**

Replace the schema block with:

```yaml
artifact_id: dialogue:<subject_key>:<created_at_compact>
artifact_kind: dialogue_feedback
subject_key: <inherited from NS handoff if consumed, otherwise derived from goal topic>
topic_key: <inherited from NS handoff if consumed, otherwise derived from goal topic>
created_at: <ISO 8601 full timestamp with fractional seconds, UTC>
supersedes: <prior dialogue artifact_id for this subject_key, or null>
source_artifacts:
  - artifact_id: <NS artifact_id if handoff was consumed>
    artifact_kind: next_steps_plan
    role: plan
record_path: null

thread_id: <Codex thread ID>
converged: <true | false>
turn_count: <int>

resolved:
  - item_id: R1
    text: <what was resolved>
    confidence: high | medium | low
unresolved:
  - item_id: U1
    text: <what remains open>
emerged:
  - item_id: E1
    text: <new concept or risk that emerged>

continuation_warranted: <true | false>
recommended_posture: <posture or null>

feedback_candidates:
  - item_id: E1
    suggested_arc: adversarial-review | next-steps | dialogue_continue | ambiguous
    affected_surface: diagnosis | planning | evidence-only
    affected_refs: [<upstream artifact_id/finding_id references>]
    material: true | false
    materiality_reason: <one-line explanation>
    classifier_source: rule | model
```

Note: `classifier_source` narrowed to `rule | model` (Task 4 makes this explicit).

- [ ] **Step 5: Update loop guardrails to use `topic_key` (line 354)**

Replace:
```
3. **Soft iteration budget.** After 2 targeted loops in the same lineage (same `subject_key`), stop suggesting further hops automatically. Report remaining open items. User can override.
```

With:
```
3. **Soft iteration budget.** After 2 targeted loops in the same topic (same `topic_key`), stop suggesting further hops automatically. Report remaining open items. User can override. The budget uses `topic_key` (coarse grouping), not `subject_key` (exact lineage), so related reviews on different facets of the same topic share a budget.
```

- [ ] **Step 6: Update the Lineage Model examples (lines 394-397)**

Replace the old examples with the new format:
```
- `ar:redaction-pipeline:20260318T143052.123`
- `ns:redaction-pipeline:20260318T144215.456`
- `dialogue:redaction-pipeline:20260318T151033.789`
```

This is already done in Step 1's replacement text, but verify the examples appear only once.

- [ ] **Step 7: Verify cross-section consistency**

Read the full spec. Check:
- All three capsule schemas use `<prefix>:<subject_key>:<created_at_compact>` format
- All three schemas include both `subject_key` and `topic_key`
- Inheritance rules are consistent: consume upstream → inherit; no upstream → mint from basis field
- Staleness detection still references `subject_key` (exact match), not `topic_key`
- Loop guardrails reference `topic_key` (coarse match)
- No leftover references to `<sequence>` numbering anywhere in the spec

- [ ] **Step 8: Commit**

```bash
git add docs/superpowers/specs/2026-03-18-skill-composability-design.md
git commit -m "feat(spec): amend identity model — split-field keys, timestamp IDs, inheritance propagation"
```

---

### Task 2: Amend provenance semantics (F2 — depends on Task 1)

**Files:**
- Modify: `docs/superpowers/specs/2026-03-18-skill-composability-design.md:244-257` (Contract 3 source_artifacts)
- Modify: `docs/superpowers/specs/2026-03-18-skill-composability-design.md:401-410` (DAG structure)
- Modify: `docs/superpowers/specs/2026-03-18-skill-composability-design.md:74-76` (Advisory fallback)

- [ ] **Step 1: Fix Contract 3 source_artifacts to direct-edge only**

In the Contract 3 schema (already updated in Task 1 Step 4), verify that `source_artifacts` lists ONLY the NS handoff — NOT the AR artifact. The rule:

> `source_artifacts[]` means "cross-kind artifacts that this run directly parsed and validated." Dialogue does not directly consume the AR capsule (only NS does). Transitive provenance is recovered by following the DAG: dialogue → NS → AR.

If the schema from Task 1 Step 4 already has only the NS entry, this step is a verification pass. If it still includes AR, remove the AR entry.

- [ ] **Step 2: Add direct-edge provenance rule to DAG structure (lines 401-410)**

After the existing DAG structure table, add:

```markdown
**Provenance rule:** `source_artifacts[]` records direct edges only — artifacts that this run directly parsed and validated. Transitive provenance is recovered by traversing upstream `source_artifacts[]` references. Example: dialogue's feedback capsule lists NS (direct consumer) but not AR (transitive — reached via NS's own `source_artifacts[]`).
```

- [ ] **Step 3: Add `consumed_via` annotation to advisory fallback description (line 75)**

After "Advisory/tolerant. NS validates the capsule if present; falls back to prose parsing if absent or invalid." add:

```markdown
**Provenance in fallback:** When NS falls back to prose parsing (capsule absent or invalid), the NS handoff MUST omit `source_artifacts` entries for the absent capsule. Do not reference an AR `artifact_id` that was not structurally consumed. This preserves lineage integrity — downstream consumers can trust that `source_artifacts` entries represent structurally validated provenance, not prose-derived references.
```

- [ ] **Step 4: Verify**

Read the modified sections. Check:
- Contract 3 schema has only NS in source_artifacts (no AR)
- DAG structure section has the direct-edge rule
- Contract 1 advisory fallback has the provenance-in-fallback clause
- No contradictions with D4 (snapshot-based state with lineage)

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/2026-03-18-skill-composability-design.md
git commit -m "feat(spec): amend provenance to direct-edge only, add fallback lineage rule"
```

---

### Task 3: Amend contract authority wording (F6 — parallel to Task 1)

**Files:**
- Modify: `docs/superpowers/specs/2026-03-18-skill-composability-design.md:431-448` (Shared Composition Contract)
- Modify: `docs/superpowers/specs/2026-03-18-skill-composability-design.md:452-459` (Skill Text Summary)

- [ ] **Step 1: Update the Shared Composition Contract section (lines 431-448)**

Replace:
```markdown
A thin reference document (~50-80 lines) loaded by all participating skills. Governs:
```

With:
```markdown
A thin reference document (~50-80 lines). The authoritative source for cross-skill composition semantics. Each participating skill inlines the minimal operational subset it needs as a self-contained stub. The full contract is additive context, not a required dependency — every skill must function correctly with only its inline stub.

Governs:
```

Replace:
```markdown
Each skill gets a short self-contained stub referencing the contract:
```

With:
```markdown
Each skill inlines a self-contained composition stub that is fully operational without reading the contract. The stub specifies:
```

- [ ] **Step 2: Update the Skill Text Summary table (lines 452-459)**

Replace "Add composition contract stub" in each row with "Inline self-contained composition stub (upstream/downstream capsules, consumer class, hop suggestion)".

- [ ] **Step 3: Add F1 boundary clarification note**

After the Pipeline threading table (line 206), add:

```markdown
**Boundary clarification:** The pipeline stages referenced above (Pre-Step 0, Step 0, Step 2, Step 3, Step 3c) are part of the dialogue skill's public contract, as codified in its SKILL.md and governed by the consultation contract's normative precedence (SS2). The NS handoff is designed to these published stages — this is correct boundary coupling to a public interface, not internal implementation coupling.
```

- [ ] **Step 4: Verify**

Read the modified sections. Check:
- "loaded by all" is replaced with "inlined as minimal operational subset"
- Standalone principle is preserved: stubs are self-contained, contract is additive
- Consistent with the standalone-layers learning (2026-02-17)
- F1 boundary note is present after Pipeline threading

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/2026-03-18-skill-composability-design.md
git commit -m "feat(spec): amend contract authority — inline stubs, additive contract, F1 boundary note"
```

---

### Task 4: Clean up classifier schema (F4 — parallel to Task 1)

**Files:**
- Modify: `docs/superpowers/specs/2026-03-18-skill-composability-design.md:277-284` (feedback_candidates in Contract 3)
- Modify: `docs/superpowers/specs/2026-03-18-skill-composability-design.md:323-334` (Routing Classification)

- [ ] **Step 1: Narrow `classifier_source` in Contract 3 schema**

Note: If Task 1 has already been applied, the full Contract 3 schema replacement already includes `classifier_source: rule | model`. In that case, verify the value is correct rather than replacing.

In the `feedback_candidates` schema (line 284), change:
```yaml
    classifier_source: rule | model | ambiguous
```
To:
```yaml
    classifier_source: rule | model
```

- [ ] **Step 2: Add independence note to Routing Classification section**

After the constrained LLM classification paragraph (line 334), add:

```markdown
**Dimension independence:** `classifier_source` and `suggested_arc` are independent dimensions. `classifier_source` describes the classification *method* (deterministic rule vs. LLM judgment). `suggested_arc` describes the routing *outcome* (where the item should go). `ambiguous` is a valid outcome (`suggested_arc = ambiguous` means the router could not determine a clear destination) but not a valid method — every classification is performed by either a rule or the model.
```

- [ ] **Step 3: Verify**

Read the modified sections. Check:
- `classifier_source` has exactly two values: `rule`, `model`
- `suggested_arc` still has `ambiguous` as a valid value
- The independence note is clear about method vs. outcome
- No `user` or `ambiguous` values in `classifier_source`

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/2026-03-18-skill-composability-design.md
git commit -m "feat(spec): clean up classifier schema — method vs outcome dimensions"
```

---

### Task 5: Add soft-echo filter examples (F5 — independent, lower priority)

**Files:**
- Modify: `docs/superpowers/specs/2026-03-18-skill-composability-design.md:311-318` (Three-tier tautology filter)
- Modify: `docs/superpowers/specs/2026-03-18-skill-composability-design.md:463-468` (Open Items)

- [ ] **Step 1: Add examples to tier 3**

After the tier 3 description (line 317), add:

```markdown
**Tier 3 examples:**

Given source finding `F1: "NS handoff deeply couples to dialogue's internal pipeline stages"`:

| Derived assumption | Valid? | Reason |
|--------------------|--------|--------|
| "The NS handoff references dialogue's internal pipeline stages" | No — restatement | Restates the finding in assumption form without operationalizing it |
| "Dialogue's pipeline stages could be refactored without breaking the NS handoff contract" | Yes — operationalizable | Makes the finding testable against the codebase: check whether pipeline stages are referenced in the NS schema |
| "The pipeline stages referenced by the NS handoff are documented as public interface" | Yes — operationalizable | Tests whether the coupling is to a public or internal surface — a factual codebase question |
| "The NS handoff couples to dialogue's pipeline" | No — restatement | Removes specificity ("internal pipeline stages") without adding testability |
```

- [ ] **Step 2: Close Open Item 1**

In the Open Items section (line 465), change:
```
1. **Soft echo filter specification**: Exact validation rule distinguishing "source-finding parrot" from legitimate source-finding-derived assumption in the tautology filter.
```
To:
```
1. ~~**Soft echo filter specification**~~: Resolved — examples added to tier 3 (2026-03-19). The existing dialogue SKILL.md tautology filter (line 93) provides the baseline rule; tier 3 examples extend it for `handoff_enriched` mode.
```

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/2026-03-18-skill-composability-design.md
git commit -m "feat(spec): add soft-echo filter tier 3 examples, close open item 1"
```

---

### Task 6: Propagate amendments to implementation plan

**Files:**
- Modify: `docs/superpowers/plans/2026-03-18-skill-composability.md`

This task propagates all spec amendments into the corresponding implementation plan tasks. Changes are mechanical — each plan task's code blocks and instructions must match the amended spec.

- [ ] **Step 1: Update Task 1 (composition contract) — identity model and authority wording**

In the plan's Task 1 Step 1 (the composition contract content):

1. Replace the artifact_id format in the Artifact Metadata table:
   - Old: `<prefix>:<date>:<subject-key>:<sequence>`
   - New: `<prefix>:<subject_key>:<created_at_compact>`

2. Add `topic_key` row to the Artifact Metadata table:
   ```
   | `topic_key` | kebab-case string | Coarse grouping for iteration budget |
   ```

3. Add after the `subject_key` description:
   ```
   **Two identity keys:** `subject_key` for exact lineage matching (staleness, supersession). `topic_key` for coarse grouping (soft iteration budget). Generic inheritance rule: if a skill directly consumes an upstream capsule, it inherits both keys; if no upstream capsule is consumed, the skill mints both keys from its basis field. This applies in all directions, including the feedback loop (dialogue → AR re-review).
   ```

4. Update the Loop Guardrails section: change `same subject_key` to `same topic_key`.

5. Update the opening paragraph: change "loaded by all participating skills" to "Each participating skill inlines the minimal operational subset it needs. The full contract is additive context, not a required dependency."

- [ ] **Step 2: Update Task 2 (AR capsule) — new artifact_id format**

In the plan's Task 2 Step 1 (AR capsule schema):

1. Replace `artifact_id: ar:<YYYY-MM-DD>:<subject-key>:<sequence>` with `artifact_id: ar:<subject_key>:<created_at_compact>`
2. Add `topic_key: <coarse grouping key — same as subject_key unless reviewing a facet>` after `subject_key`
3. Replace the `sequence` field note with: "Timestamp in artifact_id provides collision resistance. No sequence counter needed."
4. Update the Composition contract reference: change "loaded by" to "inlined as minimal operational subset in this skill"

- [ ] **Step 3: Update Task 3 (NS handoff) — new format and provenance**

In the plan's Task 3:

1. Replace `artifact_id: ns:<YYYY-MM-DD>:<subject-key>:<sequence>` with `artifact_id: ns:<subject_key>:<created_at_compact>`
2. Add `topic_key` field with inheritance note
3. Add `subject_key` inheritance note: "Inherited from AR capsule if consumed, otherwise derived from plan topic"
4. In the `source_artifacts` section, add the provenance-in-fallback clause: "If AR capsule was not structurally consumed (prose fallback), omit the AR entry from source_artifacts entirely"

- [ ] **Step 4: Update Task 7 (feedback capsule) — direct-edge provenance and classifier**

In the plan's Task 7 Step 1 (feedback capsule schema):

1. Replace `artifact_id: dialogue:<date>:<subject-key>:<sequence>` with `artifact_id: dialogue:<subject_key>:<created_at_compact>`
2. Add `topic_key` field with inheritance note
3. Fix `source_artifacts` to direct-edge only — list NS handoff as the only entry. Remove the comment about "AR capsule (if consumed via NS handoff's source_findings)"
4. Change `classifier_source: rule | model | ambiguous` to `classifier_source: rule | model`

- [ ] **Step 5: Update Task 8 (routing classification) — classifier cleanup**

In the plan's Task 8 Step 1 (classification procedure):

1. Add the dimension independence note after Step B
2. Update the loop guardrails: change `same subject_key` to `same topic_key`

- [ ] **Step 6: Update the plan's Verification Checklist**

Add these items to the checklist at the end of the plan:

```markdown
- [ ] All capsule schemas use `<prefix>:<subject_key>:<created_at_compact>` format (no sequence numbers)
- [ ] All schemas include both `subject_key` and `topic_key`
- [ ] Inheritance rules documented: generic rule (consume upstream → inherit; no upstream → mint) with feedback loop examples
- [ ] Loop guardrails use `topic_key`, staleness uses `subject_key`
- [ ] Contract 3 source_artifacts is direct-edge only (NS, not AR)
- [ ] `classifier_source = rule | model` — `ambiguous` removed from method, retained in `suggested_arc`
- [ ] Composition contract stubs are self-contained (not "see the contract")
```

- [ ] **Step 7: Verify cross-file consistency**

Read both the spec and the plan. Check:
- Every capsule schema in the plan matches the corresponding schema in the spec
- Every sentinel name in the plan matches the spec
- All field names are identical between spec and plan
- The composition contract content in the plan matches the spec's Shared Composition Contract section

- [ ] **Step 8: Commit**

```bash
git add docs/superpowers/plans/2026-03-18-skill-composability.md
git commit -m "feat(plan): propagate design amendments — identity, provenance, classifier, authority"
```

---

### Task 7: Update Open Items and add cross-model validation note

**Files:**
- Modify: `docs/superpowers/specs/2026-03-18-skill-composability-design.md:462-473` (Open Items and Cross-Model Validation)

- [ ] **Step 1: Update Open Items section**

Replace the Open Items section with:

```markdown
## Open Items

1. ~~**Soft echo filter specification**~~: Resolved — examples added to tier 3 (2026-03-19).
2. **Composition contract file location**: Resolved — `packages/plugins/cross-model/references/composition-contract.md`, alongside consultation contract. Authority model: authoritative source, skills inline minimal stubs.
3. **upstream_handoff version field**: Deferred — sentinel versioning (`v1`) provides forward-compatibility. Version field adds no value until v2 exists.
4. **codex-dialogue synthesis format**: Resolved — no changes needed. `/dialogue` projects feedback capsule from existing Synthesis Checkpoint output.
```

- [ ] **Step 2: Add design review validation note**

After the existing Cross-Model Validation section, append:

```markdown
**Design review amendments (2026-03-19):** System design review surfaced 7 findings (F1-F7) and 2 tensions (T1-T2). Codex collaborative dialogue (thread `019d0682-3f52-70a1-b7ed-e536ad2b8652`, 5 turns) resolved all findings. Key amendments: split-field identity model (F3 emerged concept), direct-edge provenance (F2), classifier dimension separation (F4), inline-stub authority model (F6). F1 closed by counter-evidence (pipeline steps are the public contract). F5/F7 accepted as v1 tradeoffs.
```

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/2026-03-18-skill-composability-design.md
git commit -m "feat(spec): update open items and add design review validation note"
```

---

## Task Dependencies

```
Task 1 (identity model) ──► Task 2 (provenance) ──► Task 6 (plan propagation)
Task 3 (authority)       ──────────────────────────► Task 6
Task 4 (classifier)      ──────────────────────────► Task 6
Task 5 (tautology)       ──────────────────────────► Task 6
                                                      └──► Task 7 (open items)
```

**Parallel tracks:**
- Track A: Task 1 → Task 2 (sequential — provenance depends on new schema)
- Track B: Task 3 (independent)
- Track C: Task 4 (independent)
- Track D: Task 5 (independent, lower priority)
- Track E: Task 6 → Task 7 (after all spec amendments)

**Critical path:** Task 1 → Task 2 → Task 6 → Task 7

**Highest-risk task:** Task 1 (identity model). The split-field design, inheritance rules, and timestamp format affect every capsule schema. If wrong, staleness detection, supersession, and loop budgeting all need rework.

---

## Verification Checklist

After all tasks are complete:

- [ ] All three capsule schemas use `<prefix>:<subject_key>:<created_at_compact>` — no sequence numbers remain
- [ ] All schemas include both `subject_key` and `topic_key`
- [ ] Inheritance documented: generic rule (consume upstream → inherit; no upstream → mint) with feedback loop examples
- [ ] Loop guardrails use `topic_key`, staleness uses `subject_key`
- [ ] Contract 3 `source_artifacts` is direct-edge only (NS, not AR)
- [ ] `classifier_source = rule | model` — `ambiguous` removed from method, retained in `suggested_arc`
- [ ] Contract authority: "inlined as minimal operational subset" — not "loaded by all"
- [ ] F1 boundary clarification note present after Pipeline threading
- [ ] Tier 3 tautology examples present with positive/negative cases
- [ ] Open Items updated (1 resolved, 2-4 resolved/deferred)
- [ ] Plan schemas match spec schemas exactly
- [ ] No leftover references to sequence-based artifact IDs in either document
