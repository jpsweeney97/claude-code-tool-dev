# Spec Writing System Plan Review

**Target:** `docs/superpowers/plans/2026-03-16-spec-writing-system.md` (~1340 lines)
**Sources:** `docs/superpowers/specs/spec-writing-system/` — 6 files (README.md, foundations.md, shared-contract.md, spec-writer.md, review-team-updates.md, hook.md)
**Reviewer:** reviewing-designs skill
**Date:** 2026-03-16
**Stakes:** Rigorous

## Summary (Post-Codex Dialogue)

| Priority | Count | Description |
|----------|-------|-------------|
| P0 | 0 | — |
| P1 | 5 | spec.yaml structural validation gap (NEW), duplication sync (F2), classification guidance (F3), degraded-mode claim_family (F7), "When NOT to Use" contradiction (NEW) |
| P2 | 4 | Renumbering instruction (F1, downgraded), placeholder wording (F4), parallelization (F5), dropped example (F6), edge semantics (NEW), hook scope (NEW) |

**Overall:** Plan is well-constructed and faithfully translates all 6 spec files into actionable implementation steps. Ready to execute with amendments. No P0 issues. Codex dialogue (5 turns, collaborative, converged) confirmed original findings, identified 2 new P1 issues, and produced a concrete claim_family decision tree.

**Codex dialogue thread:** `019cf535-606d-7953-9a55-d919b9b23e87` (5/8 turns, all resolved)

---

## Delta Card #1: Early Gate

### Entry Gate

- **Inputs:** Implementation plan (target) derived from 6-file modular spec (source)
- **Assumptions:** (1) Source spec complete and authoritative, (2) Existing skill files match plan expectations, (3) Plan intended for agentic workers, (4) Spec decisions are approved
- **Stakes:** Rigorous — moderate reversibility, moderate blast radius, medium error cost, moderate uncertainty, low time pressure
- **Yield% scope:** D-codes and F-codes only. H-codes are bridge scaffolding.

### AHG-5 Results

| Q | Finding |
|---|---------|
| Q1 (Wrong problem?) | Shared contract machinery may be over-complex for "hard to reference in conversations" → **H1** |
| Q2 (Alternatives?) | Spec-modulator extension and deferred review-team integration unexplored → **ALT1, ALT2** |
| Q3 (Failure mechanisms?) | Inline/reference content divergence with no sync → **H2**. Also: section-replacement fragility, renumbering brittleness. |
| Q4 (Hidden complexity?) | claim_family classification lacks guidance; "ambiguous" escape hatch may dominate → **H3** |
| Q5 (Load-bearing assumption?) | 8-claim vocabulary sufficiency. Merged → H1. |

### Bridge Table (Initial)

| ID | Hypothesis | Target Dims | Status |
|----|-----------|-------------|--------|
| H1 | Shared contract machinery over-complex for stated problem | D4, D5, D13, D19 | open |
| H2 | Inline contract content in SKILL.md will diverge from shared-contract.md — no sync | D6, D9, D12 | open |
| H3 | claim_family classification lacks reviewer guidance — high ambiguity risk | D5, D8, D15 | open |
| ALT1 | Extend spec-modulator instead of new spec-writer | D4, D19 | open |
| ALT2 | Defer review-team integration; ship spec-writer standalone first | D7, D10 | open |

---

## Delta Card #2: Loop Convergence

### Loop Metrics

| Pass | U | Y | Yield% |
|------|---|---|--------|
| 1 | — | — | 100% (seed) |
| 2 | 18 | 2 | 11.1% |
| 3 | 18 | 0 | 0% |

Converged at Pass 3.

### Bridge Dispositions

| ID | Status | Disposition |
|----|--------|-------------|
| H1 | disconfirmed | Plan adds no complexity beyond spec requirements. D4, D13, D19 clean. Over-complexity is a spec design concern, not a plan issue. Counter-evidence: systematic comparison shows plan faithfully translates all spec content without embellishment. |
| H2 | tested → F2 | Confirmed. SKILL.md inlines claims enum, derivation table, spec.yaml schema, failure model. docs/references/shared-contract.md has the same content as the authoritative source. No sync mechanism, validation script, or divergence warning. |
| H3 | tested → F3 | Confirmed. claim_family added to finding schema with "ambiguous" escape hatch. Zero classification guidance: no decision tree, no examples-per-claim, no rubric. Extended by F7 in adversarial pass. |
| ALT1 | evaluated: not dominant | Spec-modulator outputs plans; spec-writer outputs files. Different purposes. Extending spec-modulator would conflate planning and compilation semantics. |
| ALT2 | evaluated: not dominant | Shared contract validated by both consumers from day 1 is preferable. Degraded mode provides safe partial implementation regardless. |

### Findings After Loop

| ID | Priority | Dimensions | Summary |
|----|----------|-----------|---------|
| F1 | P1 | D7 | synthesis-guidance.md "Audit Metric Notes" heading (line 216) has no "Section N:" prefix. Plan says "renumber" but should say "add Section 8: prefix." |
| F2 | P1 | D9, D12 | No sync mechanism between inline contract content in spec-writer SKILL.md and docs/references/shared-contract.md. Claims enum, derivation table, spec.yaml schema, and failure model are duplicated with no validation or divergence detection. |
| F3 | P1 | D5, D15 | claim_family classification lacks reviewer guidance. No decision tree, no examples-per-claim. "ambiguous" escape hatch exists but may dominate without guidance, undermining mechanical precedence resolution. |
| F4 | P2 | D9 | Minor spec.yaml template placeholder wording: Task 1 says "in this spec's domain", Task 2 says "what this authority covers." |
| F5 | P2 | D7 | Chunks 2-4 can execute in parallel after Chunk 1. Plan doesn't state this for agentic workers. |
| F6 | P2 | D3 | boundary_edges worked example ("2 boundary rules produce 5 edges (3+2)") from spec dropped in plan's ROUTING replacement. |

---

## Delta Card #3: Adversarial Pass

### Adversarial Findings

| Lens | Objection | Response | Residual | Bridge/NET-NEW |
|------|-----------|----------|----------|----------------|
| A1 Assumptions | Existing files may have changed since plan authoring; replacement instructions break silently | Plan has grep validation steps that catch structural mismatches | No explicit "file doesn't match" handling | H1 (extends) |
| A2 Scale | At 10x+ specs, 8-claim vocabulary may need extension. No migration path v1→v2. | shared_contract_version field exists. Extension is future concern. | No migration story defined | — |
| A3 Perspectives | Three copies of claims/derivation content → drift risk. Promote+sync pipeline adds deployment step. | Shared contract declares itself authoritative. | F2 stands | H2 (confirms) |
| A4 Kill | Mechanical precedence only fires on contradictions. If rare (<5%), entire claims machinery is carried cost. | Other benefits: deterministic spawning, boundary analysis, structural scoring. | Cost-benefit uncertain until real usage | H1 (reconfirms disconfirmation for plan) |
| A5 Pre-mortem | 8-claim vocabulary too restrictive → force-fit → wrong routing → teams revert to spec-modulator, leaving dead metadata | Degraded mode and spec-modulator remain available. Damage is wasted effort, not broken specs. | No early feedback loop for claim quality | — |
| A6 Steelman | ALT1 better if claims prove unnecessary. ALT2 better if classification too ambiguous. | Neither alternative dominates given current information. | — | ALT1, ALT2 (reconfirms) |
| A7 Framing | Real problem may be "ad-hoc review routing" not "big files." Spec-modulator already splits files. | Solution fits either framing. Shared contract formalizes ad-hoc decisions. | Plan inherits spec's framing | — |
| A8 Hidden complexity | claim_family is REQUIRED in all modes but meaningless in degraded mode. Every degraded-mode finding forced to `ambiguous`. | Not addressed in plan or spec. | **F7 (NET-NEW P1)** | H3 (extends) |
| A9 Motivated reasoning | Plan positions spec-modulator as legacy without evaluation. | Framing comes from spec, not plan. Plan's job is faithful translation. | None | — |

### NET-NEW Finding

| ID | Priority | Dimensions | Summary |
|----|----------|-----------|---------|
| F7 | P1 | D5, D6 | claim_family added as "required" field to finding schema but has no useful semantics in degraded mode (no spec.yaml → no claims vocabulary). Every degraded-mode finding would have `claim_family: ambiguous`, diluting the signal. Plan should specify: make field conditional on full contract mode, or default to "N/A" in degraded mode. |

**NET-NEW justification:** Early gate Q3/Q4 focused on classification *difficulty* in full contract mode. A8's hidden-complexity lens exposed the orthogonal issue of modal *applicability* — a required field that's meaningless in one of two operating modes.

### Final Bridge Table

| ID | Status | Disposition | Audit |
|----|--------|-------------|-------|
| H1 | disconfirmed | Plan adds no complexity beyond spec. Counter-evidence: systematic spec-to-plan comparison at D1, D2, D19. | Card #2 / Pass 2. A4 reconfirmed disconfirmation. |
| H2 | tested | F2 (P1). Three content copies, no sync. | Card #2 / Pass 1. A3 confirmed. |
| H3 | tested | F3 (P1) + F7 (P1). Classification guidance missing AND field meaningless in degraded mode. | Card #2 / Pass 1. A8 extended with F7. |
| ALT1 | evaluated | Not dominant. Different tool purposes (plans vs files). | Card #2 / Pass 1. A6 reconfirmed. |
| ALT2 | evaluated | Not dominant. Dual-consumer validation preferred. | Card #2 / Pass 1. A6 reconfirmed. |

---

## Coverage Tracker

### Source Coverage

| ID | Dimension | Status | Priority | Evidence | Confidence | Notes |
|----|-----------|--------|----------|----------|------------|-------|
| D1 | Requirements coverage | [x] | P0 | E2 | High | All 6 spec files mapped to plan tasks. Section-by-section comparison. Completeness basis: every spec section has a corresponding plan step. |
| D2 | Source fidelity | [x] | P0 | E2 | High | Content blocks compared against spec originals. Claims enum, derivation table, schema, failure model — all match. One placeholder wording difference (F4, P2). Completeness basis: systematic data structure comparison. |
| D3 | Source completeness | [x] | P1 | E2 | High | All sections accounted for. One worked example dropped (F6, P2). Completeness basis: section-by-section sweep. |

### Behavioral Completeness

| ID | Dimension | Status | Priority | Evidence | Confidence | Notes |
|----|-----------|--------|----------|----------|------------|-------|
| D4 | Functional completeness | [x] | P1 | E1 | Medium | All functional components present. Claims/derivation/precedence machinery fully specified. |
| D5 | Edge case coverage | [~] | P1 | E2 | Medium | Failure models cover hard failures. Gap: claim_family in degraded mode (F7), classification guidance (F3). |
| D6 | Error handling | [x] | P1 | E2 | Medium | Producer (hard fail) and consumer (graceful degrade) models complete. Dual-mode fallback specified. |

### Implementation Readiness

| ID | Dimension | Status | Priority | Evidence | Confidence | Notes |
|----|-----------|--------|----------|----------|------------|-------|
| D7 | Actionability | [~] | P1 | E2 | High | Exact content provided for new files. Edit instructions mostly precise. Gap: renumbering instruction precision (F1), parallelization unstated (F5). |
| D8 | Dependencies | [x] | P1 | E2 | High | Correct ordering: Chunk 1 foundational, Chunks 2-4 depend on it. Individual commits provide rollback. Degraded mode ensures safe partial implementation. |
| D9 | Internal consistency | [~] | P1 | E2 | High | Claims, derivation, failure model consistent across tasks. Gap: three copies with no sync mechanism (F2). Minor placeholder wording variance (F4). |
| D10 | Risk identification | [~] | P1 | E1 | Medium | No explicit risk section. Implicit risks identified via bridge table. Degraded mode mitigates partial implementation risk. |
| D11 | Testability | [x] | P1 | E2 | High | Each task has validation steps. Hook has 3 test scenarios. SKILL.md has grep-based checks. |

### Consistency

| ID | Dimension | Status | Priority | Evidence | Confidence | Notes |
|----|-----------|--------|----------|----------|------------|-------|
| D12 | Cross-validation | [x] | P0 | E2 | High | Plan vs spec: consistent. Plan internal: consistent. Plan vs existing files: verified (synthesis-guidance.md checked directly). |

### Document Quality

| ID | Dimension | Status | Priority | Evidence | Confidence | Notes |
|----|-----------|--------|----------|----------|------------|-------|
| D13 | Clarity | [x] | P2 | E1 | High | Well-structured with clear chunk/task/step hierarchy. Replacement content in code blocks. |
| D14 | Structure | [x] | P2 | E1 | High | 4 chunks, 5 tasks, logical ordering. Validation and commit steps per task. |
| D15 | Instruction completeness | [~] | P1 | E1 | Medium | Most steps actionable. Gaps: claim_family classification guidance (F3), degraded-mode behavior (F7). |
| D16 | Terminology | [x] | P2 | E1 | High | Consistent: "full contract mode" vs "degraded mode", claims/authorities/roles. |
| D17 | Cross-references | [x] | P1 | E2 | High | All file paths verified. Links to shared contract, existing skills, and spec files correct. |
| D18 | Detail level | [x] | P2 | E1 | High | Appropriate — exact content for new files, exact edits for modifications, validation commands with expected outputs. |
| D19 | Complexity | [x] | P1 | E1 | Medium | Plan doesn't add unnecessary complexity beyond spec. Content duplication is spec-designed, not plan-introduced. |

### Verified PostToolUse Hook Format

PostToolUse input confirmed per Claude Code docs (2026-03-16):
- Input includes both `tool_input` (write arguments) and `tool_response` (result)
- Hook correctly reads `.tool_input.file_path` and `.tool_input.content`
- Output format `hookSpecificOutput.additionalContext` matches docs

---

## Iteration Log

| Pass | Action | Entities Changed |
|------|--------|-----------------|
| 1 | Seed — all dimensions and findings established | All D1-D19, F1-F6 |
| 2 | Verified: "Audit Metric Notes" exists (line 216, no section prefix). Verified: PostToolUse hook format correct per docs. | F1 revised P0→P1 (section exists but unnumbered). D7 revised P0→P1 (phantom concern resolved). |
| 3 | Convergence check — no new findings, no revisions | None |
| Adversarial | A1-A9 applied. A8 produced NET-NEW F7. | F7 added (P1). |

---

## Recommendations

### Must-fix before execution (P1) — Revised after Codex dialogue

1. **NEW: spec.yaml structural validation gap** — Add failure conditions for parseable-but-structurally-invalid spec.yaml: missing required top-level keys (`authorities`, `precedence`, `fallback_authority_order`), wrong types (e.g., `boundary_rules: {}` instead of list). Add to both producer and consumer failure models. The `shared_contract_version` hard stop is a related but distinct operational path within this same gap.

2. **F2 — Validator script + sync comments** (Task 2): Create `scripts/validate_spec_writing_contract.py` following the repo precedent of `validate_consultation_contract.py`. Block-extraction diff between SKILL.md inline content and `docs/references/shared-contract.md`. Add sync comment markers (`<!-- SYNC: docs/references/shared-contract.md#claims-enum -->`) in the SKILL.md. Invoke from Task 2's validation step.

3. **F3 — claim_family decision tree in shared scaffold** (Task 4 Step 2): Add an 8-step numbered-priority classifier to the shared scaffold in `role-rubrics.md`, ordered from most specific claims (`persistence_schema`, `enforcement_mechanism`) to most general (`architecture_rule`, `decision_record`), with 3 tie-breakers for confusable pairs. Include a guarded fast-path: "If the file has exactly one effective claim, use that claim" (guard: not for multi-claim files). SKILL.md gets a pointer-level rule only. Domain briefs remain defect-class-based per spec's design intent.

4. **F7 — Conditional claim_family** (Task 3 Step 7): Make claim_family conditional: required in full contract mode, omitted in degraded mode. Do not use `ambiguous` as a proxy for "no spec.yaml" — it conflates genuinely uncertain classification with structurally meaningless context. Follows existing `prompted_by` precedent (field already conditional in the schema).

5. **NEW: "When NOT to Use" contradiction** — Replace SKILL.md line 38 ("Do NOT use for specs without frontmatter metadata") with: "Best for spec corpora with frontmatter metadata. Specs without frontmatter are supported in degraded mode; authority-based features are unavailable."

### Address before first use (P2)

6. **F1 — Renumbering instruction** (Task 4 Step 3, downgraded from P1): Split into two explicit operations: (a) rename `## Section 5: Exemplar Ledger Entry` to `## Section 7: Exemplar Ledger Entry`, (b) rename `## Audit Metric Notes` to `## Section 8: Audit Metric Notes`.

7. **F5 — State parallelization**: Add to plan header: "Chunks 2, 3, and 4 have no mutual dependencies and can execute in parallel after Chunk 1 completes."

8. **F4 — Normalize placeholder wording**: Use consistent "what this authority covers in this spec's domain" in both Task 1 and Task 2 spec.yaml schema templates.

9. **F6 — Restore boundary_edges example**: Add "Example: 2 boundary rules in the CLI spec produce 5 edges (3 + 2)" to the ROUTING replacement content in Task 3 Step 3.

10. **NEW: Edge semantics** — Add coverage for `claims: []`, duplicate claims, and claim ordering to the validator script.

11. **NEW: Hook scope** — The `docs/` path filter catches plans, audits, benchmarks — broader than spec-like documents. Usability concern.

---

## Codex Dialogue Results

**Thread:** `019cf535-606d-7953-9a55-d919b9b23e87`
**Posture:** Collaborative | **Turns:** 5/8 | **Converged:** Yes | **Mode:** server_assisted

### New Findings from Dialogue

| ID | Priority | Source | Summary |
|----|----------|--------|---------|
| NEW-1 | P1 | T3 (Codex proposed, T4 agreed) | spec.yaml structural validation gap — parseable-but-invalid manifests have undefined behavior |
| NEW-2 | P1 | T5 (convergence) | "When NOT to Use" prohibition contradicts degraded mode backward compatibility |
| NEW-3 | P2 | T5 (emerged) | Edge semantics: `claims: []`, duplicate claims, claim ordering not covered |
| NEW-4 | P2 | T5 (emerged) | Hook scope broader than spec-like documents |

### Priority Changes

| Finding | Before | After | Rationale |
|---------|--------|-------|-----------|
| F1 | P1 | P2 | Failure mode is messy edit, not broken system. Both models agreed T1. |

### Emerged Artifacts

- **8-step claim_family classifier** with 3 tie-breakers — ready for shared scaffold in `role-rubrics.md`
- **Guarded fast-path** for single-claim files — "if exactly one effective claim, use it"
- **Conditional claim_family schema** — omit in degraded mode, following `prompted_by` precedent
