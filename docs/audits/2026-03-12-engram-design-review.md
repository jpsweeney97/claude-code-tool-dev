# Engram Design Review

**Date:** 2026-03-12
**Reviewer:** Claude (reviewing-designs skill, Framework for Thoroughness v1.0.0)
**Target:** `docs/plans/2026-03-12-engram-plugin-design.md` (705 lines, commit `2645b0f`)
**Stakes:** Rigorous (default)
**Convergence:** 3 passes. Yield%: 100% → 11.1% → 8.3% (threshold: <10%)
**Prior reviews:** 2 automated, 1 deep (evaluative), 1 adversarial — this is the 4th review pass

## Summary

| Priority | Count | Description |
|----------|-------|-------------|
| P0 | 0 | Issues that break correctness or execution |
| P1 | 9 | Issues that degrade quality |
| P2 | 6 | Polish items |

**Assessment:** The spec is implementation-ready. No P0 issues. The 3 prior review sessions caught the structural issues (P4 dependency gap, mode boundary dispatch, three-bucket codemod). This review found documentation accuracy issues (F1-F3), specification gaps (F6-F9, F16-F17), and traceability gaps (F11).

---

## Delta Card #1: Early Gate

### Entry Gate

**Inputs:**
- Target: `docs/plans/2026-03-12-engram-plugin-design.md` (705 lines)
- Sources: Learning system redesign spec, existing ticket plugin (669 tests), existing handoff plugin (340 tests)
- User concerns: None beyond "review the spec"

**Assumptions:**
1. Spec is current (commit `2645b0f`, 5th revision)
2. Source plugins' code is ground truth for migration targets
3. Prior reviews (2 automated, 1 deep, 1 adversarial) were genuine

**Stakes:** Rigorous — wide blast radius (all knowledge lifecycle components), high cost of error (migration of ~1000 tests), low time pressure.

**Stopping criteria:** Yield% < 10%. Yield% scope: D-codes and F-codes only. H-codes are bridge scaffolding.

### AHG-5

| # | Question | Finding |
|---|---------|---------|
| Q1 | Wrong problem? | Strongest counter: 5 specific crossover points could be fixed with targeted changes, not full consolidation. But learning system needs a package home. → H1 |
| Q2 | Rejected alternatives? | "Targeted fix" (3 PRs, ~3 days) delivers ~60% of value at ~5% of cost. Not documented in spec. → ALT1, ALT2 |
| Q3 | What would fail? | (1) sys.path ambiguity during P3-P6 dual-importable modules, (2) guard plugin_root derivation change, (3) marketplace.json stale paths → H2 |
| Q4 | Hidden complexity? | Codemod: no tool specified, no per-phase configuration, no completeness verification. Test allocation: no criteria for which tests go to which phase. → H3 |
| Q5 | Load-bearing assumption? | `${CLAUDE_PLUGIN_ROOT}` reliability across all invocation contexts. Single point of failure — every shim depends on it. → merged into H3 |

### Bridge Table (Initial)

| ID | Hypothesis | Target Dimensions | Anchor | Status |
|----|-----------|-------------------|--------|--------|
| H1 | Scope mismatch: full consolidation for targeted coupling problems | D15, D4, D14 | Problem Statement (lines 8-17) | open |
| H2 | sys.path ambiguity during P3-P6 causes silent behavioral divergence | D5, D6, D7 | Test Strategy (lines 636-656) | open |
| H3 | Codemod complexity underestimated: no tool, no per-phase config, no completeness metric | D7, D9, D15 | Codemod Details (lines 555-618) | open |
| ALT1 | Targeted fix: address only the 5 cross-package issues without consolidation | — | Problem Statement (lines 8-17) | open |
| ALT2 | Phased extraction: learning system first, defer ticket/handoff consolidation | — | Phase 2 (lines 432-446) | open |

---

## Delta Card #2: Loop Convergence

### Bridge Dispositions (Post-Loop)

| ID | Status | Disposition |
|----|--------|-------------|
| H1 | open | Deferred to adversarial pass A7 |
| H2 | open | Risk reduced by guard analysis (Branch 4 pass-through) and YAML serialization boundary |
| H3 | tested | F5 (P2: codemod tool deferred) + F6 (P1: test allocation absent). Design-level adequate. |
| ALT1 | evaluated | Not dominant — consolidation enables learning system + unified search |
| ALT2 | evaluated | Not dominant — design already incorporates phased extraction as P2 |

### Findings After Loop

| Finding | Dim | Pri | Description | Evidence |
|---------|-----|-----|-------------|----------|
| F1 | D12 | P1 | Module count "15 modules" at line 67 but 17 listed in tree | Tree includes read.py and dedup.py (added in adversarial review). Comment not updated. |
| F2 | D12 | P1 | Handoff module count "10 modules" at line 86 but 9 listed in tree | ticket_parsing.py counted in source (10) but deleted, not migrated (9 in target). |
| F3 | D12 | P1 | Redundant `scripts/cleanup.py` and `scripts/quality_check.py` | Both also in `hooks/`. hooks.json references hooks/ versions. No skill invokes these. |
| F4 | D5 | P2 | Rollback strategy absent | "Independently reviewable and revertible PR" is design-adequate. Implementation concern. |
| F5 | D15 | P2 | Codemod tool not specified | Scope and strategy described. Tool selection deferred to implementation plan. |
| F6 | D9 | P1 | Test allocation criteria absent | 669 actual ticket tests vs ~659 in spec (10 unaccounted). No rules for assigning test files to phases. |
| F7 | D5 | P1 | P5/P6 have no cross-dependency | P5 (handoff) imports `engram.ticket.parse` (P3). P6 (triage, audit) imports only ticket modules (P3-P4). Independent — could run in parallel. |
| F8 | D5 | P2 | Hook migration window | Verified benign: old guard's Branch 4 passes through commands targeting new root. No conflict. |
| F9 | D15 | P1 | Skills migration timing not systematic | Spec mentions learn/promote in P2, handoff skills in P5, ticket skills in P6, but lacks a complete skill-to-phase mapping for all 11 skills. |
| F10 | D5 | P2 | Hook coexistence during P4-P6 | Verified benign: each guard recognizes only its own plugin root. Old guard's allowlist is irrelevant for new shim paths. |
| F11 | D1 | P1 | Learning system behavioral spec not referenced | Spec describes learning module structure but doesn't reference `docs/plans/2026-03-11-learning-system-redesign.md` as the behavioral specification for /promote maturity signals, ranking, placement. |
| F12 | D6 | P2 | Guard fail-open risk | Inherited from existing system (guard line 17: "Exit code always 0 — accepted v1.0 limitation"). Migration doesn't increase risk if guard stays stdlib-only. |
| F13 | D14 | P2 | Runtime import count imprecise | Spec lists "8+" at 8 specific lines. Actual: 13 runtime imports of ticket_read/ticket_dedup. "8+" is technically correct but undercounts by 5. |

### Running Totals (Post-Loop)

| Priority | Count |
|----------|-------|
| P0 | 0 |
| P1 | 7 |
| P2 | 6 |

### Convergence

| Pass | U | Y | Yield% | Action |
|------|---|---|--------|--------|
| 1 | — | — | 100% | Special case |
| 2 | 27 | 3 (F4, F5, F12 downgraded) | 11.1% | Continue |
| 3 | 24 | 2 (F8, F10 downgraded) | 8.3% | Exit (<10%) |

---

## Delta Card #3: Adversarial Pass

### Bridge Table (Final)

| ID | Status | Disposition | Audit |
|----|--------|-------------|-------|
| H1 | tested | Scope justified by learning system + unified search. Problem framing overstates ("overlapping boundaries" vs "5 specific crossover points"). Alternative not documented → F17. | Checkpoint 3, adversarial A7. Prior: open. |
| H2 | disconfirmed | Guard Branch 4 pass-through makes dual-firing benign. YAML serialization prevents in-memory type confusion. No concrete namespace ambiguity scenario found. | Checkpoint 3, adversarial A4 + VERIFY cross-check. Prior: open. Counter-evidence: guard code lines 35-60, YAML-file data flow. |
| H3 | tested | F5 (P2: codemod tool deferred) + F6 (P1: test allocation absent). Design-level specification adequate; implementation plan must address. | Checkpoint 2, EXPLORE D7+D9. Prior: open. |
| ALT1 | evaluated | Not dominant. Learning system needs package home. Consolidation delivers permanent crossover fix + unified search. ALT1 can't provide either. | Checkpoint 2. Decision tree: not dominant (design wins). |
| ALT2 | evaluated | Not dominant. Design already incorporates phased extraction (P2 = core + learning first). | Checkpoint 2. Decision tree: not dominant (design wins). |

### Adversarial Lenses

| Lens | Objection | Response | Residual Risk |
|------|-----------|----------|---------------|
| A1 Assumption Hunting | One-way compatibility rule relies on developer discipline, not tooling | Rule is temporary (P3-P6), developer has deep context | Low |
| A2 Scale Stress | Search degrades linearly with handoff archive size | 30/90-day retention bounds data; v2 defers persistent index | Very low |
| A3 Competing Perspectives | Guard fail-open + shim import chain broadens crash surface | Guard is stdlib-only (verified: lines 19-27). No transitive deps. | Near zero if guard stays stdlib-only |
| A4 Kill the Design | **P4 exit gate tests don't verify deny path through shim** | → **NET-NEW F16** | Medium |
| A5 Pre-mortem | v2 features may never ship, reducing consolidation ROI | v1-only benefits sufficient: 5 crossover fixes + learning backing + single deployment | Low |
| A6 Steelman Alternatives | **ALT1 delivers ~60% value at ~5% cost** | Learning system needs package home; consolidation is permanent fix | Medium → **NET-NEW F17** |
| A7 Challenge the Framing | Problem framing overstates ("overlapping boundaries" vs "5 crossover points") | Learning system tips balance toward consolidation | Low |
| A8 Hidden Complexity | hooks.json may not capture all existing hooks | Implementation plan would audit existing hooks | Low |
| A9 Motivated Reasoning | Success criteria are positive-only ("X works"), no negative regression checks | Criterion #4 IS a regression check ("preserve legacy handoff behavior") | Low |

### NET-NEW Adversarial Findings

| Finding | Dim | Pri | Description | Why Early Gate Missed |
|---------|-----|-----|-------------|----------------------|
| F16 | D9 | P1 | P4 exit gate missing deny-path test. The 4 subprocess categories (engine, readonly, audit, no-env-var) are positive tests. No test verifies the guard DENIES unauthorized commands through the new shim. | Q3 focused on namespace/guard resolution, not exit gate coverage. |
| F17 | D15 | P1 | Spec's Design Decisions table documents HOW to consolidate (D1-D10) but not WHETHER. The targeted-fix alternative (3 PRs to fix /defer, duplicate parser, shared paths) is not documented as a rejected approach with rationale. | Q2 tracked as ALT1 dominance check, not spec completeness. |

### Final Totals

| Priority | Count | Findings |
|----------|-------|----------|
| **P0** | **0** | — |
| **P1** | **9** | F1, F2, F3, F6, F7, F9, F11, F16, F17 |
| **P2** | **6** | F4, F5, F8, F10, F12, F13 |

---

## Coverage Tracker

### Dimensions

| ID | Dimension | Status | Pri | Evidence | Confidence | Notes |
|----|-----------|--------|-----|----------|------------|-------|
| D1 | Learning spec coverage | [~] | P1 | E1 | Medium | Requirements mentioned but source spec not referenced → F11 |
| D2 | Ticket plugin coverage | [x] | P0 | E2 | High | All 16 script modules + guard accounted for. Count annotation stale → F1. Completeness basis: ls verification + mapping table cross-check. |
| D3 | Handoff plugin coverage | [x] | P0 | E2 | High | All 10 script modules listed (9 migrated + 1 deleted). Count annotation stale → F2. Completeness basis: ls verification + mapping table cross-check. |
| D4 | Normal path completeness | [x] | P1 | E1 | Medium | Shim, hook, search, migration flows documented. Completeness basis: all invocation patterns described. |
| D5 | Edge case specification | [~] | P0 | E2 | Medium | Rollback (F4/P2), hook coexistence (F8,F10/P2 — verified benign), phase parallelism (F7/P1). |
| D6 | Failure mode specification | [~] | P1 | E1 | Medium | Guard fail-open inherited (F12/P2). Spec doesn't add new failure modes. |
| D7 | Error handling strategy | [~] | P1 | E0 | Low | Not addressed at design level. Appropriate deferral. |
| D8 | Phase dependency correctness | [x] | P0 | E2 | High | Verified by import graph analysis. P3 reshaping (adversarial review) closes dependency gap. P5/P6 independent → F7. Completeness basis: traced all cross-phase imports. |
| D9 | Test strategy completeness | [~] | P1 | E2 | Medium | Principles clear, allocation criteria absent → F6. Exit gate missing deny test → F16. |
| D10 | Performance considerations | [-] | P2 | — | — | Deferred to v2 (design choice, not omission). Open Question #1. |
| D11 | Security considerations | [-] | P2 | — | — | Inherited from existing plugins. Guard stays stdlib-only (verified). |
| D12 | Internal cross-validation | [~] | P0 | E2 | High | Module counts stale → F1, F2. Redundant shims → F3. Import count verified exact (285). Test count verified (669+340). |
| D13 | Clarity | [x] | P1 | E1 | Medium | Implementable — architecture, API, migration described at sufficient detail. Completeness basis: a competent implementer could start from this spec. |
| D14 | Precision | [~] | P1 | E1 | Medium | Module counts imprecise (F1, F2). Runtime import lines imprecise (F13). Import total exact. |
| D15 | Completeness | [~] | P0 | E2 | Medium | Codemod tool deferred (F5/P2). Skill migration timing incomplete (F9/P1). "Whether to consolidate" not documented (F17/P1). |
| D16 | Terminology consistency | [x] | P2 | E1 | High | Consistent throughout. Completeness basis: checked shim/provider/module/subsystem terms. |
| D17 | Structure/organization | [x] | P2 | E1 | High | Logical flow: Problem → Decisions → Architecture → Migration → Risks. Completeness basis: sections build on predecessors. |
| D18 | Traceability | [x] | P1 | E2 | High | Decisions linked to Codex consultations with thread IDs, line numbers, sessions. Completeness basis: D1-D10 all have source attribution. |
| D19 | Actionability | [~] | P1 | E1 | Medium | Architecture and search API are actionable. Migration phases need test allocation criteria (F6) and skill-to-phase mapping (F9). |

Summary: 7 `[x]`, 8 `[~]`, 2 `[-]`, 0 `[ ]`, 0 `[?]`

### Findings Summary

| Finding | Dim | Pri | Description | Disconfirmation |
|---------|-----|-----|-------------|-----------------|
| F1 | D12 | P1 | Module count "15 modules" at line 67 but 17 in tree | Checked if intentional — no, comment predates adversarial review's read/dedup addition |
| F2 | D12 | P1 | Handoff module count "10 modules" at line 86 but 9 in tree | ticket_parsing.py counted in source but deleted. Comment should say 9. |
| F3 | D12 | P1 | Redundant `scripts/cleanup.py` and `scripts/quality_check.py` | Checked if any skill invokes these — no skill does. hooks.json uses hooks/ versions. |
| F4 | D5 | P2 | Rollback strategy absent | "Revertible PR" is design-adequate. Implementation concern. |
| F5 | D15 | P2 | Codemod tool not specified | Scope and strategy clear. Tool selection is implementation concern. |
| F6 | D9 | P1 | Test allocation criteria absent (669 actual vs ~659 in spec) | Checked if derivable from module mapping — partially, but integration tests cross phases. |
| F7 | D5 | P1 | P5/P6 have no cross-dependency — could run in parallel | Verified: P5 imports engram.ticket.parse (P3). P6 imports only P3-P4 ticket modules. Independent. |
| F8 | D5 | P2 | Hook migration window | Verified benign: guard Branch 4 passes through commands targeting other root. |
| F9 | D15 | P1 | Skills migration timing not systematic for all 11 skills | Some skills mentioned with phases, no complete mapping. |
| F10 | D5 | P2 | Hook coexistence P4-P6 | Verified benign: each guard recognizes only its own plugin root's scripts. |
| F11 | D1 | P1 | Learning system redesign spec not referenced | Spec describes structure but doesn't link to behavioral specification for /promote. |
| F12 | D6 | P2 | Guard fail-open risk | Inherited from existing system (guard line 17). Not introduced by migration. |
| F13 | D14 | P2 | Runtime import count: 13 actual vs 8 listed lines | "8+" is technically correct. Codemod AST walker finds all regardless of listing. |
| F16 | D9 | P1 | P4 exit gate missing deny-path test (NET-NEW, adversarial A4) | — (adversarial finding) |
| F17 | D15 | P1 | "Whether to consolidate" decision not documented (NET-NEW, adversarial A6) | — (adversarial finding) |

### Iteration Log

| Pass | Changes | Yield% |
|------|---------|--------|
| 1 | 15 D-codes + 12 F-codes established | 100% (special case) |
| 2 | F4 P1→P2, F5 P1→P2, F12 P1→P2 (all evidence-based downgrades) | 11.1% |
| 3 | F8 P1→P2 (guard Branch 4 verification), F10 P1→P2 (same) | 8.3% → converged |

### Verified Claims

| Claim in spec | Actual | Status |
|---------------|--------|--------|
| 285 `from scripts.` imports (157+122+6) | 157+122+6 = 285 | Exact match ✓ |
| ~659 ticket tests | 669 | 10 over (approximate OK) |
| ~340 handoff tests (315+25) | 340 | Exact match ✓ |
| 8+ runtime imports of read/dedup | 13 | "8+" is correct but imprecise |
| Guard uses `__file__`-based resolution | Uses `CLAUDE_PLUGIN_ROOT` with `__file__` fallback (line 37) | Spec's description of current behavior is imprecise |
| Exit code always 0 (fail-open) | Confirmed (guard line 17) | Match ✓ |

## Exit Gate

| Criterion | Status |
|-----------|--------|
| Coverage complete | ✓ — 7 `[x]`, 8 `[~]`, 2 `[-]`, 0 `[ ]`, 0 `[?]` |
| Evidence requirements met | ✓ — P0 dimensions have E2 evidence |
| Disconfirmation attempted | ✓ — 2+ techniques per P0 dimension (Rigorous) |
| Assumptions resolved | ✓ — all 3 verified |
| Convergence reached | ✓ — Yield% 8.3% < 10% |
| Connections mapped | ✓ — all P1 findings linked to dimensions |
| Adversarial pass complete | ✓ — all 9 lenses applied with objections and responses |
| Bridge complete | ✓ — no open rows, disposition invariant satisfied |

## Recommendations

### For the design spec (before implementation planning):

1. **F1, F2:** Fix module count annotations: `ticket/` → "17 modules", `handoff/` → "9 modules (10 source, 1 deleted)"
2. **F3:** Remove `scripts/cleanup.py` and `scripts/quality_check.py` from architecture tree (hook-only scripts)
3. **F17:** Add a "D0: Whether to consolidate" decision documenting the targeted-fix alternative and why consolidation was chosen
4. **F11:** Add a reference to `docs/plans/2026-03-11-learning-system-redesign.md` as the behavioral specification for the learning module

### For the implementation plan:

5. **F6:** Compute exact test counts per phase. Specify allocation criteria for integration tests that cross phase boundaries.
6. **F16:** Add deny-path test to P4 exit gate: "At least one subprocess test verifying the guard DENIES an unauthorized command through the new shim boundary"
7. **F7:** Consider parallelizing P5 (handoff) and P6 (rest of ticket) — verified independent
8. **F9:** Create complete skill-to-phase mapping for all 11 skills

### Constraints to preserve:

9. Guard module (`engram/ticket/guard.py`) MUST remain stdlib-only (no imports from other `engram.*` modules) — prevents transitive dependency failures that would silently disable the guard
10. One-way compatibility rule enforcement: consider a lint check during P3-P6 to prevent accidental `from scripts.*` imports in engram/ code

## Supplementary Verification (Background Agents)

Two verification agents independently confirmed findings against the codebase. Key results:

### Confirmed Claims

| Claim | Agent Result |
|-------|-------------|
| 285 `from scripts.` imports | Confirmed: 157 + 122 + 6 alias = 285 |
| ~659 ticket tests | Confirmed: 659 test functions (669 via pytest --co due to parametrized expansion) |
| ~340 handoff tests | Confirmed: 340 test functions |
| Guard uses CLAUDE_PLUGIN_ROOT | Confirmed: lines 35-37 |
| /defer cross-plugin path hack | Confirmed: SKILL.md line 145 |
| Duplicate parsers diverging | Confirmed: both use fenced YAML regex |
| 8 test files with __file__ paths | Confirmed: 7 ticket + 1 handoff |
| 3 handoff scaffolding files | Confirmed: triage.py, search.py, distill.py |
| marketplace.json hardcoded paths | Confirmed: ticket + handoff source paths |
| Hook count: 3 total | Confirmed: 1 ticket + 2 handoff |
| /search --regex documented flag | Confirmed: SKILL.md lines 4, 23 |
| Cross-model scripts/ unrelated | Confirmed: local namespace (94+13 refs) |

### New Finding

**Ticket's `scripts/__init__.py` exists** — making `scripts/` a Python package, not just a directory. Handoff's `scripts/` does NOT have `__init__.py`. The spec doesn't mention this asymmetry. Impact: during migration, the old `scripts` package persists on sys.path alongside `engram`. Per-package pytest isolation and subprocess hook execution prevent namespace collision, but P7 cleanup must delete this `__init__.py`. (P2 — does not change review conclusions.)

### Clarifications

- **Skill count:** 9 existing (2 ticket + 7 handoff) + 2 new (learn, promote from `.claude/skills/`) = 11 target. Spec is correct.
- **Test count:** 659 test functions vs 669 pytest-collected (parametrized expansion). Spec's "~659" aligns with function count.
- **/triage `python` vs `python3`:** Already acknowledged in spec (line 569: "python → python3 invocation normalization"). Not a finding.
- **pipeline-guide.md paths:** 6 actual vs 5 claimed. Minor counting difference (P2).
