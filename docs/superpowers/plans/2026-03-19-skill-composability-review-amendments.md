# Skill Composability Second-Pass Review Amendments

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply 4 pre-implementation amendments and 2 low-cost fixes from the second-pass system design review + Codex evaluative dialogue (thread `019d0728-c61a-7c03-b67c-f13512cd3d85`) to the skill composability design spec and implementation plan.

**Architecture:** All amendments target markdown documents — the design spec (authoritative), the implementation plan (derived), and the first-round amendments plan (disposition update). The material-delta tiering (Task 4) is the most complex edit. All spec amendments are independent and can be applied in any order.

**Tech Stack:** Markdown documents only. No code changes.

**Spec:** `docs/superpowers/specs/2026-03-18-skill-composability-design.md`
**Implementation plan:** `docs/superpowers/plans/2026-03-18-skill-composability.md`
**First-round amendments:** `docs/superpowers/plans/2026-03-19-skill-composability-amendments.md`
**Source:** Second-pass design review (this session) + Codex evaluative dialogue thread `019d0728-c61a-7c03-b67c-f13512cd3d85`

---

## Context: Second-Pass Review Outcomes

| Finding | Disposition | Amendment |
|---------|------------|-----------|
| F1 (silent advisory/tolerant fallback) | REOPENED — prior counter-evidence invalid (SS2 doesn't cover pipeline stages) | Add diagnostic + remove SS2 claim (Task 2) |
| F2 (dual identity keys) | Acceptable v1 — fix label | Update topic_key "Used by" column (Task 5) |
| F3 (timestamp precision) | Design change | Specify canonical millisecond precision (Task 3) |
| F4 (mixed material-delta criteria) | Upgraded to HIGH — design change | Tier into ordered evaluation (Task 4) |
| F5 (multi-surface routing) | Acceptable v1 | No spec change — v2 backlog item |
| F6 (schema evolution) | Can safely wait | No spec change |
| F7 (composition contract location) | Acceptable v1 — fix discoverability | Add stub→contract reference (Task 5) |
| D1 (thin structural overlay) | Reframe | Rename to "standalone-first, protocol-rich composition" (Task 1) |

Emerged concepts from Codex dialogue: `ar_input_mode` degradation field (optional, included in Task 2), `materiality_source: rule | model` (included in Task 4), v1 scope confirmed as full implementation.

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `docs/superpowers/specs/2026-03-18-skill-composability-design.md` | Modify | Tasks 1-6: all spec amendments |
| `docs/superpowers/plans/2026-03-18-skill-composability.md` | Modify | Task 7: propagate spec changes to implementation plan |
| `docs/superpowers/plans/2026-03-19-skill-composability-amendments.md` | Modify | Task 8: update F1 disposition |

---

### Task 0: Create working branch

- [ ] **Step 1: Create feature branch**

```bash
git checkout -b feature/skill-composability-review-amendments main
```

- [ ] **Step 2: Verify branch**

```bash
git branch --show-current
```

Expected: `feature/skill-composability-review-amendments`

---

### Task 1: Reframe D1 heading

**Files:**
- Modify: `docs/superpowers/specs/2026-03-18-skill-composability-design.md:35`

- [ ] **Step 1: Replace D1 heading**

Replace:
```markdown
### D1: Composability model is thin structural overlay
```

With:
```markdown
### D1: Composability model is standalone-first, protocol-rich composition
```

- [ ] **Step 2: Verify**

Read lines 35-42. Confirm:
- Heading says "standalone-first, protocol-rich composition"
- Body text still says "Each skill remains fully standalone and human-usable" (unchanged — body already matches the new framing)
- Alternatives considered section is untouched

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/2026-03-18-skill-composability-design.md
git commit -m "feat(spec): reframe D1 — standalone-first, protocol-rich composition"
```

---

### Task 2: Reopen F1 — add advisory/tolerant diagnostic and remove SS2 claim

**Files:**
- Modify: `docs/superpowers/specs/2026-03-18-skill-composability-design.md:48` (D2 consumer class table)
- Modify: `docs/superpowers/specs/2026-03-18-skill-composability-design.md:212` (boundary clarification)

This is the highest-value amendment. The prior review's F1 counter-evidence was invalidated by Codex — SS2 at `consultation-contract.md:33` covers 4 specific normative sections, not pipeline stage names.

- [ ] **Step 1: Add diagnostic requirement to advisory/tolerant consumer class**

Replace the advisory/tolerant row in the D2 table (line 48):
```markdown
| Advisory/tolerant | Validate if capsule present; fall back to prose parsing if absent or invalid | NS consuming AR capsule |
```

With:
```markdown
| Advisory/tolerant | Validate if capsule present; fall back to prose parsing if absent or invalid. Emit a one-line prose diagnostic when falling back (e.g., "AR capsule not detected; lineage tracking unavailable for this run.") | NS consuming AR capsule |
```

- [ ] **Step 2: Remove SS2 governance claim from boundary clarification**

Replace the boundary clarification at line 212:
```markdown
**Boundary clarification:** The pipeline stages referenced above (Pre-Step 0, Step 0, Step 2, Step 3, Step 3c) are part of the dialogue skill's public contract, as codified in its SKILL.md and governed by the consultation contract's normative precedence (SS2). The NS handoff is designed to these published stages — this is correct boundary coupling to a public interface, not internal implementation coupling.
```

With:
```markdown
**Boundary clarification:** The NS handoff intentionally couples to pipeline stages documented in the dialogue skill's SKILL.md. This is documented interface coupling, not hidden internal coupling.
```

The change: (a) removes the invalid SS2 governance claim (SS2 covers SS5, SS7, SS10, SS11 only), (b) softens "public contract" to "documented interface coupling" — the SKILL.md documents these stages but doesn't explicitly promise their stability as a contract surface.

- [ ] **Step 3: Verify**

Read lines 44-51 and line 212. Confirm:
- Advisory/tolerant row includes diagnostic emission requirement
- Strict/deterministic row is unchanged
- Boundary clarification no longer references SS2
- Boundary clarification still asserts pipeline stages are public contract (this part is valid)

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/2026-03-18-skill-composability-design.md
git commit -m "feat(spec): reopen F1 — add advisory fallback diagnostic, remove invalid SS2 claim"
```

---

### Task 3: Specify canonical millisecond precision for timestamps

**Files:**
- Modify: `docs/superpowers/specs/2026-03-18-skill-composability-design.md:96` (Contract 1 created_at)
- Modify: `docs/superpowers/specs/2026-03-18-skill-composability-design.md:169` (Contract 2 created_at)
- Modify: `docs/superpowers/specs/2026-03-18-skill-composability-design.md:255` (Contract 3 created_at)
- Modify: `docs/superpowers/specs/2026-03-18-skill-composability-design.md:455` (Artifact ID format)

- [ ] **Step 1: Update all three capsule schema `created_at` fields**

In all three locations (lines 96, 169, 255), replace:
```yaml
created_at: <ISO 8601 full timestamp with fractional seconds, UTC>
```

With:
```yaml
created_at: <ISO 8601, UTC, millisecond precision: YYYY-MM-DDTHH:MM:SS.sssZ>
```

Use `replace_all` for this edit — the old string appears exactly 3 times.

- [ ] **Step 2: Update the Artifact ID format section**

Replace line 455:
```markdown
Where `created_at_compact` is the `created_at` ISO 8601 value with separators removed: `YYYYMMDDTHHMMSS` at minimum, with fractional seconds appended when the `created_at` field includes them (e.g., `YYYYMMDDTHHMMSS.fff`). The timestamp component MUST preserve the full precision of the `created_at` field — do not truncate fractional seconds. All three skills MUST use the same precision.
```

With:
```markdown
Where `created_at_compact` is the `created_at` value with separators removed: `YYYYMMDDTHHMMSS.sss` (always 3 fractional digits). All three skills MUST use millisecond precision. Pad `.000` if only second-level precision is available from the runtime; truncate to milliseconds if higher precision is provided.
```

- [ ] **Step 3: Verify**

Search the spec for `created_at`. Confirm:
- All 3 capsule schemas say `millisecond precision: YYYY-MM-DDTHH:MM:SS.sssZ`
- Artifact ID format says `YYYYMMDDTHHMMSS.sss` (always 3 digits)
- Examples still show `.123`, `.456`, `.789` (already 3 digits — no change needed)
- No remaining references to "full precision" or "same precision" without specifying milliseconds

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/2026-03-18-skill-composability-design.md
git commit -m "feat(spec): specify canonical millisecond precision for timestamps"
```

---

### Task 4: Tier material-delta criteria into ordered evaluation

**Files:**
- Modify: `docs/superpowers/specs/2026-03-18-skill-composability-design.md:355-367` (Material-Delta Gating section)

This is the most complex amendment. The flat mixed list becomes three ordered tiers mirroring the routing classification's deterministic-first pattern.

- [ ] **Step 1: Replace the Material-Delta Gating section**

Replace lines 355-367:
```markdown
### Material-Delta Gating

An item is **material** if any of:
- Introduces a new non-duplicate risk, assumption challenge, or alternative that changes AR's diagnostic surface
- Introduces a new dependency, blocker, gate change, or critical-path shift that changes NS's planning surface
- Reopens or contradicts something previously RESOLVED
- Crosses an action threshold: assumption status → `wishful`, finding severity → `blocking`/`high`, task → on/off critical path, decision gate → changed branch outcome

An item is **not material** if only:
- A restatement or example of an existing item
- An implementation detail below the current abstraction level
- A low-support idea with no affected upstream refs
- An open question already present in the source snapshot
```

With:
```markdown
### Material-Delta Gating

Evaluate materiality in tier order. Stop at the first tier that produces a definitive match.

**Tier 1 — Pre-screening exclusions (check first):**

An item is **not material** if any of:
- A restatement or example of an existing item
- An implementation detail below the current abstraction level
- A low-support idea with no affected upstream refs
- An open question already present in the source snapshot

Some Tier 1 criteria (e.g., "implementation detail") involve lightweight judgment. Set `materiality_source: rule` when the exclusion is clear-cut; set `materiality_source: model` with a one-line reason when it required interpretation. Either way, if Tier 1 matches, the item is not material. Skip Tiers 2-3.

**Tier 2 — Rule-based inclusions (deterministic):**

An item is **material** if any of:
- Reopens or contradicts something previously RESOLVED
- Crosses an action threshold: assumption status → `wishful`, finding severity → `blocking`/`high`, task → on/off critical path, decision gate → changed branch outcome

If Tier 2 matches, the item is material. Set `material: true`, `materiality_source: rule`. Skip Tier 3.

**Tier 3 — Semantic evaluation (model fallback):**

If neither Tier 1 nor Tier 2 matched, evaluate using judgment:
- Does the item introduce a new non-duplicate risk, assumption challenge, or alternative that changes AR's diagnostic surface?
- Does it introduce a new dependency, blocker, gate change, or critical-path shift that changes NS's planning surface?

Set `materiality_source: model`. Provide a one-line `materiality_reason`.

**Note:** `materiality_source` is a separate dimension from `classifier_source`. `classifier_source` describes the routing classification method (for `suggested_arc`). `materiality_source` describes the materiality evaluation method. Do not conflate them.
```

- [ ] **Step 2: Add `materiality_source` to feedback_candidates schema**

In the Contract 3 feedback_candidates schema (spec line ~289), after the existing `classifier_source` line:
```yaml
    classifier_source: rule | model
```

Add:
```yaml
    materiality_source: rule | model
```

This separates routing provenance (`classifier_source` — how `suggested_arc` was determined) from materiality provenance (`materiality_source` — how `material` was determined). Both are per-item fields in `feedback_candidates`.

- [ ] **Step 3: Verify**

Read the replaced material-delta section and the updated feedback_candidates schema. Confirm:
- Three tiers in order: pre-screening exclusions → deterministic inclusions → model fallback
- All original criteria are preserved (nothing lost, just reordered)
- Each tier specifies what `materiality_source` to set
- Tier evaluation is stop-at-first-match (explicitly stated)
- `feedback_candidates` schema now has both `classifier_source` (routing) and `materiality_source` (materiality)
- `classifier_source` is NOT referenced in the material-delta tiers

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/2026-03-18-skill-composability-design.md
git commit -m "feat(spec): tier material-delta criteria, add materiality_source to feedback schema"
```

---

### Task 5: Low-cost fixes — F2 topic_key label and F7 stub discoverability

**Files:**
- Modify: `docs/superpowers/specs/2026-03-18-skill-composability-design.md:414` (topic_key "Used by" column)
- Modify: `docs/superpowers/specs/2026-03-18-skill-composability-design.md:512-515` (composition stub spec)

- [ ] **Step 1: Update topic_key "Used by" column**

Replace line 414:
```markdown
| `topic_key` | Coarse grouping (soft iteration budget) | kebab-case, broader than subject_key | `redaction-pipeline` | Loop guardrails only |
```

With:
```markdown
| `topic_key` | Coarse grouping (soft iteration budget) | kebab-case, broader than subject_key | `redaction-pipeline` | Loop guardrails; propagated via inheritance by all downstream skills |
```

- [ ] **Step 2: Add stub→contract reference requirement**

Replace lines 512-515:
```markdown
Each skill inlines a self-contained composition stub that is fully operational without reading the contract. The stub specifies:
- What upstream capsule it can consume
- What downstream capsule it emits
- When to suggest the next hop
```

With:
```markdown
Each skill inlines a self-contained composition stub that is fully operational without reading the contract. The stub specifies:
- What upstream capsule it can consume
- What downstream capsule it emits
- When to suggest the next hop
- A reference to the authoritative contract path (`packages/plugins/cross-model/references/composition-contract.md`) for skill authors who need the full protocol
```

- [ ] **Step 3: Verify**

Read lines 411-414 and 512-516. Confirm:
- topic_key "Used by" mentions both loop guardrails and inheritance propagation
- Stub spec includes 4 items, with the contract path reference as the last one
- The contract path matches the file location in the "File location" paragraph below

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/2026-03-18-skill-composability-design.md
git commit -m "feat(spec): low-cost fixes — topic_key label, stub-to-contract reference"
```

---

### Task 6: Add second-pass review cross-model validation note

**Files:**
- Modify: `docs/superpowers/specs/2026-03-18-skill-composability-design.md:543` (after existing Cross-Model Validation)

- [ ] **Step 1: Amend F1 closure in existing validation note**

In the existing validation note at line 543, replace:
```markdown
F1 closed by counter-evidence (pipeline steps are the public contract).
```

With:
```markdown
~~F1 closed by counter-evidence (pipeline steps are the public contract)~~ F1 reopened by second-pass review — see below.
```

This prevents contradictory F1 dispositions in the same section.

- [ ] **Step 2: Append second-pass review note**

After line 543 (the existing "Design review amendments (2026-03-19)" paragraph), append:

```markdown

**Second-pass review amendments (2026-03-19):** Second-pass system design review surfaced 7 findings (F1-F7) and 1 tension (T1). Codex evaluative dialogue (thread `019d0728-c61a-7c03-b67c-f13512cd3d85`, 6 turns) resolved all findings. Key amendments: F1 reopened — advisory fallback diagnostic added, invalid SS2 claim removed; F3 canonical millisecond precision; F4 material-delta tiered into ordered evaluation; D1 reframed to "standalone-first, protocol-rich composition." F2/F7 accepted with low-cost fixes. F5/F6 deferred. Emerged: `ar_input_mode` degradation field (deferred), `materiality_source` field (integrated into tiered material-delta), v1 scope narrowing option (declined — full v1 confirmed).
```

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/2026-03-18-skill-composability-design.md
git commit -m "feat(spec): add second-pass review validation note, amend F1 closure"
```

---

### Task 7: Propagate amendments to implementation plan

**Files:**
- Modify: `docs/superpowers/plans/2026-03-18-skill-composability.md`

This task propagates all spec amendments into the corresponding implementation plan sections. Changes are mechanical — each plan section must match the amended spec.

- [ ] **Step 1: Update the plan header Architecture description**

Replace line 7:
```markdown
**Architecture:** Each skill remains standalone. Composition is additive — structured capsules/sentinels are appended to existing prose output. A shared composition contract governs artifact schemas, consumer classes, routing rules, and staleness detection. The dialogue skill consumes upstream handoffs through its existing pipeline stages.
```

With:
```markdown
**Architecture:** Each skill remains standalone-first with protocol-rich composition. Structured capsules/sentinels are appended to existing prose output. A shared composition contract governs artifact schemas, consumer classes, routing rules, and staleness detection. The dialogue skill consumes upstream handoffs through its existing pipeline stages. Advisory/tolerant consumers emit a diagnostic when falling back to prose parsing.
```

- [ ] **Step 2: Update Task 1 consumer class table**

In the composition contract content (line 78-81), replace the advisory/tolerant row:
```markdown
| Advisory/tolerant | Validate if present; enhance processing | Fall back to prose parsing | Fall back to prose parsing |
```

With:
```markdown
| Advisory/tolerant | Validate if present; enhance processing. Emit diagnostic on fallback. | Fall back to prose parsing; emit diagnostic | Fall back to prose parsing; emit diagnostic |
```

- [ ] **Step 3: Update Task 1 material-delta section**

In the composition contract content (lines 104-112), replace:
```markdown
## Material-Delta Gating

An item is **material** if any of:
- New non-duplicate risk, assumption challenge, or alternative changing diagnostic surface
- New dependency, blocker, gate change, or critical-path shift changing planning surface
- Reopens or contradicts a previously RESOLVED item
- Crosses action threshold: assumption → `wishful`, finding → `blocking`/`high`, task on/off critical path

**Not material:** restatement, implementation detail, low-support idea with no upstream refs, existing open question.
```

With:
```markdown
## Material-Delta Gating

Evaluate in tier order. Stop at first match.

**Tier 1 — Pre-screening exclusions:** Not material if: restatement, implementation detail, low-support idea with no upstream refs, existing open question. Set `materiality_source: rule` (or `model` when criterion required interpretation).

**Tier 2 — Inclusions (rule):** Material if: reopens/contradicts RESOLVED, or crosses action threshold (assumption → `wishful`, finding → `blocking`/`high`, task on/off critical path). Set `materiality_source: rule`.

**Tier 3 — Semantic (model):** If no tier matched: evaluate whether item introduces new risk/alternative changing diagnostic surface, or new dependency/blocker changing planning surface. Set `materiality_source: model`.
```

- [ ] **Step 4: Update Task 1 timestamp precision**

In the composition contract's Artifact Metadata table, replace:
```markdown
| `created_at` | ISO 8601 | When this artifact was produced |
```

With:
```markdown
| `created_at` | ISO 8601, UTC, millisecond precision (`YYYY-MM-DDTHH:MM:SS.sssZ`) | When this artifact was produced |
```

- [ ] **Step 5: Update Task 1 topic_key description**

In the composition contract's "Two identity keys" paragraph (plan line 60), replace:
```markdown
`topic_key` for coarse grouping (soft iteration budget).
```

With:
```markdown
`topic_key` for coarse grouping (soft iteration budget); also propagated via inheritance by all downstream skills.
```

- [ ] **Step 6: Update timestamp fields in Task 2, Task 3, Task 7 capsule schemas**

In Task 2 (AR capsule, line 184):
```yaml
created_at: <ISO 8601 timestamp>
```
→
```yaml
created_at: <ISO 8601, UTC, millisecond precision: YYYY-MM-DDTHH:MM:SS.sssZ>
```

In Task 3 (NS handoff, line 289):
```yaml
created_at: <ISO 8601 timestamp>
```
→
```yaml
created_at: <ISO 8601, UTC, millisecond precision: YYYY-MM-DDTHH:MM:SS.sssZ>
```

In Task 7 (feedback capsule, line 601):
```yaml
created_at: <ISO 8601>
```
→
```yaml
created_at: <ISO 8601, UTC, millisecond precision: YYYY-MM-DDTHH:MM:SS.sssZ>
```

- [ ] **Step 7: Update Task 8 material-delta reference**

In Task 8 (line 688), replace:
```markdown
**Material-delta gating:** Apply the material-delta rules from the composition contract (`packages/plugins/cross-model/references/composition-contract.md`). Set `material = true | false` based on whether the item meets any materiality criterion.
```

With:
```markdown
**Material-delta gating:** Apply the tiered material-delta rules from the composition contract (`packages/plugins/cross-model/references/composition-contract.md`): Tier 1 exclusions (rule) → Tier 2 inclusions (rule) → Tier 3 semantic (model). Set `material = true | false` and `materiality_source = rule | model`.
```

- [ ] **Step 8: Add `materiality_source` to feedback capsule schema in implementation plan**

In the implementation plan's Task 7 feedback capsule schema (plan line ~633), after:
```yaml
    classifier_source: <rule | model>
```

Add:
```yaml
    materiality_source: <rule | model>
```

- [ ] **Step 10: Add diagnostic to NS prose-fallback instruction**

In Task 3 (NS handoff), find the prose-fallback instruction (plan line ~263):
```markdown
**If the AR capsule is absent or invalid:** Fall back to reading the conversation prose for findings. This is the default behavior today — the capsule enhances but does not replace it.
```

Replace with:
```markdown
**If the AR capsule is absent or invalid:** Fall back to reading the conversation prose for findings. Emit a one-line diagnostic: "AR capsule not detected; lineage tracking unavailable for this run." This is the default behavior today — the capsule enhances but does not replace it.
```

- [ ] **Step 11: Add contract path to composition contract references in skill tasks**

In each skill task's composition contract reference (plan lines ~211, ~322, ~637), append the contract path. For example, in Task 2 (line 211):
```markdown
**Composition contract:** This capsule follows the artifact metadata schema inlined as minimal operational subset in this skill. NS consumes it as advisory/tolerant — the capsule enhances but is not required.
```

Append after each such reference:
```markdown
Full protocol: `packages/plugins/cross-model/references/composition-contract.md`.
```

Apply this to all three locations (Task 2 line ~211, Task 3 line ~322, Task 7 line ~637).

- [ ] **Step 12: Add second-pass verification items to the Verification Checklist**

Append to the Verification Checklist at the end of the file:
```markdown
- [ ] Advisory/tolerant consumer class includes diagnostic emission requirement
- [ ] No reference to SS2 governance in boundary clarification
- [ ] All `created_at` fields specify millisecond precision (`YYYY-MM-DDTHH:MM:SS.sssZ`)
- [ ] Material-delta section uses tiered evaluation (exclusions → inclusions → model)
- [ ] D1 heading says "standalone-first, protocol-rich composition"
- [ ] topic_key "Used by" mentions inheritance propagation
- [ ] Composition stubs include contract path reference
```

- [ ] **Step 13: Verify cross-file consistency**

Read both spec and plan. Check:
- Consumer class definitions match between spec and plan contract (including diagnostic requirement)
- Material-delta structure matches (tiered in both, using `materiality_source` not `classifier_source`)
- Timestamp precision matches (milliseconds in both)
- All capsule `created_at` fields in the plan use the new format
- `feedback_candidates` schema has both `classifier_source` and `materiality_source` in both spec and plan
- NS prose-fallback includes diagnostic
- All three composition contract references include the full protocol path

- [ ] **Step 14: Commit**

```bash
git add docs/superpowers/plans/2026-03-18-skill-composability.md
git commit -m "feat(plan): propagate second-pass review amendments to implementation plan"
```

---

### Task 8: Update first-round amendments plan — F1 disposition and historical banner

**Files:**
- Modify: `docs/superpowers/plans/2026-03-19-skill-composability-amendments.md:1-2,21`

- [ ] **Step 1: Add historical status banner**

After line 2 (the "For agentic workers" callout), insert:

```markdown

> **Status: Historical / Partially Superseded.** All 7 tasks in this plan have been executed (commits on main). The second-pass design review (`2026-03-19-skill-composability-review-amendments.md`) reopened F1 and amended F3, F4, D1. This file is retained as historical record of the first-round amendments.
```

- [ ] **Step 2: Update F1 row in the Context table**

Replace line 21:
```markdown
| F1 (pipeline coupling) | Closed by counter-evidence | Note only — pipeline steps are the public contract |
```

With:
```markdown
| F1 (pipeline coupling) | ~~Closed by counter-evidence~~ → Reopened by second-pass review | SS2 doesn't cover pipeline stages; advisory fallback diagnostic added (see `2026-03-19-skill-composability-review-amendments.md` Task 2) |
```

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/plans/2026-03-19-skill-composability-amendments.md
git commit -m "docs: mark first-round amendments as historical, update F1 disposition"
```

---

## Task Dependencies

```
Task 0 (branch) ──► Tasks 1-5 (parallel spec amendments) ──► Task 6 (validation note)
                                                            ──► Task 7 (plan propagation)
                     Task 8 (amendments plan update — independent)
```

**Parallel tracks after Task 0:**
- Track A: Tasks 1-5 (all edit spec, but different sections — apply in any order)
- Track B: Task 8 (independent, edits a different file)
- Track C: Task 6 → Task 7 (after all spec amendments)

**Critical path:** Task 0 → Tasks 1-5 → Task 7

**Highest-risk task:** Task 4 (material-delta tiering). Restructuring from a flat list to three ordered tiers must preserve all original criteria without loss or duplication.

---

## Verification Checklist

After all tasks are complete:

- [ ] D1 heading says "standalone-first, protocol-rich composition" — not "thin structural overlay"
- [ ] Advisory/tolerant consumer class includes diagnostic emission requirement
- [ ] Boundary clarification does not reference SS2 governance
- [ ] All 3 capsule schemas specify `created_at` with millisecond precision
- [ ] Artifact ID format says `YYYYMMDDTHHMMSS.sss` (always 3 fractional digits)
- [ ] Material-delta uses 3 ordered tiers: exclusions → inclusions → model fallback
- [ ] Material-delta tiers use `materiality_source` (NOT `classifier_source` — separate dimension)
- [ ] All original material-delta criteria are present (no criteria lost in restructuring)
- [ ] topic_key "Used by" mentions inheritance propagation alongside loop guardrails
- [ ] Composition stubs include contract path reference as 4th item
- [ ] Cross-model validation includes second-pass review note
- [ ] Implementation plan consumer class, material-delta, and timestamp fields match spec
- [ ] NS prose-fallback in implementation plan includes diagnostic emission
- [ ] All three skill task composition contract references include full protocol path
- [ ] First-round amendments plan F1 disposition updated to "Reopened"
- [ ] Existing validation note F1 clause has strikethrough with "reopened" forward reference
- [ ] No remaining references to "thin structural overlay" in spec or plan
- [ ] No remaining references to "SS2" in the boundary clarification
- [ ] `feedback_candidates` schema has both `classifier_source` (routing) and `materiality_source` (materiality) in spec and plan
- [ ] No use of `classifier_source` for materiality evaluation (only for routing classification)
