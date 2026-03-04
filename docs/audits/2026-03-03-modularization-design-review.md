# Modularization Design Review (Round 5)

## Context

- **Protocol:** thoroughness.framework@1.0.0
- **Audience:** Project author (reviewer/executor of modular plan execution)
- **Scope:** Verify the modularization design (`docs/plans/2026-03-02-ticket-plugin-plan-modularization.md`, 186 lines) captures all requirements from source documents and is implementable without ambiguity.
- **Constraints:** Design has been through 4 adversarial Codex reviews (structural, fix-translation, fix-interaction, mechanism-interaction defect classes) + 2 collaborative triages. This review uses a different methodology (Framework for Thoroughness) to check requirements coverage and implementation readiness — a complementary lens to the prior internal-consistency reviews.

## Summary

| Priority | Count | Description |
|----------|-------|-------------|
| P0       | 0     | No correctness or execution issues found |
| P1       | 0     | No quality degradation issues found |
| P2       | 5     | Wording, clarity, and polish items |

**Verdict:** Design is ready for implementation. All P2 findings are cosmetic — no changes required before proceeding to module execution plans.

## Entry Gate

### Assumptions

- **A1:** Source documents (Phase 1 plan ~4870 lines, design doc 912 lines) are complete and authoritative. **Verified** — plan has been through 2 adversarial reviews, design doc stable at 912 lines.
- **A2:** The 186-line modularization design is the current version (post-R4 fixes at commit `ac91fbf`). **Verified** — read from `main` after merge.
- **A3:** Prior reviews focused on internal consistency — this review checks requirements coverage and implementation readiness. **Verified** — prior review threads are adversarial Codex dialogues, not source-comparison reviews.
- **A4:** The executing agent will have both the modularization design and the relevant plan section in context. **Verified** — Gate 0 check #2 confirms the sub-skill can accept ~1924 lines (M4's size).
- **A5:** The conftest helpers (`make_gen1/2/3/4_ticket`) are defined in the plan's Task 1. **Verified** — lines 193-284 of the plan define all 4 helpers as plain functions in `tests/conftest.py`.

### Stakes / Thoroughness Level

- **Level:** Rigorous
- **Rationale:** Blast radius is wide (defects propagate to all 5 module executions) and cost of error is high (mid-execution defect discovery is expensive). However, 4 prior adversarial reviews + 2 collaborative triages provide compensating control against structural defects. The value of this review is the different lens (requirements coverage), not adding depth to an already-deep internal-consistency review. Time pressure is low.

### Stopping Criteria

- **Selected:** Risk-based (all P0 dimensions `[x]` with ≥E2 evidence) + Discovery-based (two consecutive loops with no new P0/P1 findings)

### Initial Dimensions + Priorities

**P0:** D2 (semantic fidelity), D3 (procedural completeness), D4 (decision rules), D5 (exit criteria), D6 (safety defaults)

**P1:** D1 (structural coverage), D7 (clarity), D8 (completeness), D9 (feasibility), D10 (edge cases), D11 (testability), D12 (cross-validation), D13 (implicit concepts), D14 (precision), D16 (internal consistency), D18 (verifiability), D19 (actionability)

**P2:** D15 (examples), D17 (redundancy)

### Coverage Structure

- **Chosen:** Backlog (dimensions as entries, findings linked to dimensions)
- **Rationale:** 19 dimensions with few expected findings — sparse tracking is more efficient than a matrix.
- **Overrides:** None. Standard Yield% scope (P0+P1 entities).

### DISCOVER Techniques Applied

1. **External taxonomy check:** Compared against CI/CD gated pipeline patterns (entry criteria, exit criteria, failure handling, artifact management, timeout/staleness). The design covers all standard gate elements.
2. **Pre-mortem inversion:** 5 completions — "This review would be worthless if the design doesn't match the plan's actual task dependencies," "if gate types are misassigned," "if an executor needs information not in the design," "if failure recovery is ambiguous for co-occurring failures," "if the design assumes capabilities the executor doesn't have."
3. **Perspective multiplication:** 3 stakeholders — executing agent ("Do I know what to do?"), reviewer ("Do I have clear PASS/FAIL criteria?"), plan author ("Does this faithfully partition my plan?").

## Coverage Tracker

| ID | Status | Priority | Evidence | Confidence | Notes |
|----|--------|----------|----------|------------|-------|
| D1 | [x] | P1 | E2 | High | Completeness basis: All 15 tasks mapped to 5 modules. Line counts verified (M1=500, M2=784, M3=975, M4=1924, M5=617). Test counts verified (0+25+42+49+9=125 ≈ plan's ~128). Test file mapping verified (7 files). |
| D2 | [x] | P0 | E2 | High | Completeness basis: Import dependency graph verified against plan source code. M2→M3 sentinels match plan's actual imports (Task 4: extract_fenced_yaml, parse_yaml_block; Task 6: ParsedTicket, parse_ticket). M3→M4 import subset verified (5 modules × specific symbols). Tasks 5, 7 confirmed no ticket_parse imports. |
| D3 | [x] | P0 | E2 | High | Completeness basis: All 3 gate types (Standard, Standard+, Critical) have concrete steps. Each boundary has assigned gate type. M1→M2 has custom conftest smoke test. M4→M5 has 4-vector round-trip probe. |
| D4 | [x] | P0 | E2 | High | Completeness basis: Gate verdict mechanically derived [T]. Failure classification (transient/deterministic) has clear criteria. 3-branch attribution has exhaustive branches. Boundary fault has decision record requirement. |
| D5 | [x] | P0 | E2 | High | Completeness basis: Each gate has PASS/FAIL verdict. Gate 0 has explicit 4-check pass/fail. Module completion = evaluated_sha commit. |
| D6 | [x] | P0 | E2 | High | Completeness basis: 4-step Failure Recovery with escalation chain. Gate 0 failure blocks M1 start. Cross-boundary edits disallowed unless remediation cycle. Warnings are non-blocking. |
| D7 | [x] | P1 | E1 | Medium | Completeness basis: Executing agent knows which tasks, which plan sections, gate card format, checkpoint format, failure handling. Minor gap: "handoff prompt" referenced but not defined (see F2). |
| D8 | [x] | P1 | E2 | High | Completeness basis: Module structure, gate card format, two-SHA model, boundary risk classification, gate types, enforcement tags, probe vectors, failure recovery, M4 checkpoints, M2 phased execution — all specified. |
| D9 | [x] | P1 | E1 | Medium | Completeness basis: Gate 0 verifies executing-plans sub-skill. Test files created by plan tasks. Conftest helpers defined in Task 1. All referenced dependencies have creation points. |
| D10 | [x] | P1 | E2 | High | Completeness basis: M1 (0 tests) → custom conftest smoke test. M4 (~1924 lines) → internal checkpoints. M2 (non-sequential) → Gate 0 check #3 + phased execution. M5 (final) → Task 15 cleanup. |
| D11 | [x] | P1 | E1 | Medium | Completeness basis: Gate verdicts mechanically derivable [T]. Monotonicity enforceable [M]. Probe vectors have specific assertions. Gate 0 has specific pass/fail. |
| D12 | [x] | P1 | E2 | High | Completeness basis: Terminology scan — evaluated_sha/handoff_sha, must_pass_files, gate types, gate card, remediation cycle all used consistently. Minor: "sentinel" has two scopes (see F1). |
| D13 | [x] | P1 | E1 | Medium | Completeness basis: Key terms defined (gate card, two-SHA, enforcement tags, remediation cycle, invariant ledger, monotonicity). Minor: "handoff prompt" undefined in this document (see F2). |
| D14 | [x] | P1 | E1 | Medium | Completeness basis: Gate card format precise. Probe vectors precise. Module table precise. Minor: "brief invariant summary" vague (see F5). |
| D15 | [-] | P2 | — | — | N/A rationale: Gate card template, probe vectors, invariant ledger schema, and slice table provide sufficient concrete examples. Missing examples (decision record format, remediation cycle walkthrough) are P2 polish, not structural gaps. |
| D16 | [x] | P1 | E2 | High | Completeness basis: Test counts sum to 125 (consistent with plan's ~128 approximation). Gate types match boundary risk. Module → test file mapping matches plan. Enforcement tags consistent with gate definitions. |
| D17 | [-] | P2 | — | — | N/A rationale: 186-line document with no significant redundancy found. Lines 68 and 72 both discuss warnings/gate commits but address different aspects (visibility vs. commit scope). |
| D18 | [x] | P1 | E1 | Medium | Completeness basis: Most constraints are verifiable — [T] for gate verdicts and probes, [M] for monotonicity and two-SHA diff, cumulative must_pass_files derivable from mapping table. |
| D19 | [x] | P1 | E1 | Medium | Completeness basis: Executing agent, reviewer, and Gate 0 runner all have clear action items. Decision record fields listed. Minor: artifact format for decision record unspecified (see F3). |

## Iteration Log

| Pass | New | Reopened | Revised | Escalated | Yield% | Notes |
|------|-----|----------|---------|-----------|--------|-------|
| 1 | 22 (17 dims + 5 findings) | 0 | 0 | 0 | 100% | Special case. All dimensions explored. 5 findings, all P2. |
| 2 | 0 | 0 | 0 | 0 | 0% | Re-examined all findings for under-prioritization. F2 considered for P1 upgrade but kept at P2 (handoff prompt is created by reviewer, not defined by sub-skill). Temporal expansion and boundary perturbation applied — no new dimensions. |

Convergence: 0% < 10% (Rigorous threshold). Reached after Pass 2.

## Findings

### F1: "Sentinel" terminology overloaded
- **Priority:** P2 | **Evidence:** E2 | **Confidence:** High
- **Linked dimensions:** D12 (cross-validation), D14 (precision)
- **Claim:** The term "sentinel" has two scopes: (1) "forward-dependency sentinels" in gate types = import-only smoke tests for the next module, (2) "sentinel commands" in Failure Recovery = previous gate's `commands_to_run` + smoke checks. The Failure Recovery scope is broader.
- **Artifacts:** Design lines 100-101 (gate type sentinels), line 123 (Failure Recovery sentinels)
- **Impact:** Low — the Failure Recovery text explicitly defines what "sentinel commands" means in context (`commands_to_run and any smoke checks`). An executor would follow the inline definition, not infer from the gate type usage.
- **Recommendation:** Could add a parenthetical "(note: broader than gate-type forward-dependency sentinels)" at line 123, but not required.

### F2: "Handoff prompt" referenced but not defined
- **Priority:** P2 | **Evidence:** E1 | **Confidence:** Medium
- **Linked dimensions:** D13 (implicit concepts), D7 (clarity)
- **Claim:** Line 51 says the gate card is "included in the handoff prompt for the next module" and line 21 says "The M1 handoff prompt includes this Gate 0 preflight card." The term "handoff prompt" is not defined in the modularization design.
- **Artifacts:** Design lines 21, 51
- **Impact:** Low — "handoff prompt" is the prompt given to the next agent session. The reviewer/user creates this prompt by including the gate card, relevant plan section, and design reference. The concept is intuitive for the intended audience (who will also have the executing-plans sub-skill loaded). Gate 0 check #1 verifies the sub-skill exists.
- **Recommendation:** Could add a one-line definition: "The handoff prompt is the input prompt given to the fresh agent session that executes the next module." Not blocking.

### F3: Decision record format unspecified for boundary faults
- **Priority:** P2 | **Evidence:** E1 | **Confidence:** Medium
- **Linked dimensions:** D7 (clarity), D15 (examples)
- **Claim:** Line 126 requires the reviewer to produce "a decision record (owner_module, evidence, scope_of_edits, rerun_commands)" for boundary faults, but doesn't specify the artifact format (file? commit message? gate card section?).
- **Artifacts:** Design line 126
- **Impact:** Low — the required fields are listed, and the reviewer would naturally include this in the gate card's warnings or a commit message. For a 5-module process with at most 4 gate boundaries, format inconsistency between reviewers is unlikely (likely one reviewer for all gates).
- **Recommendation:** Could add: "recorded as a subsection in the gate card or as a standalone committed document." Not blocking.

### F4: M4→M5 Critical gate omits Standard+ sentinel specification
- **Priority:** P2 | **Evidence:** E2 | **Confidence:** High
- **Linked dimensions:** D3 (procedural completeness)
- **Claim:** The Critical gate definition (line 101) includes Standard+ checks (forward-dependency sentinels). At M3→M4, these are specified as M4's import subset. At M4→M5, only the round-trip probe is specified — no explicit Standard+ sentinels for M5.
- **Artifacts:** Design line 101 (Critical definition), Task 12 in plan (entrypoints use subprocess invocation, not Python imports)
- **Impact:** Low — M5's entrypoints use subprocess invocation of engine scripts, not Python imports. Import-only sentinel checks don't apply in the same way. The round-trip probe (4 vectors) covers the most critical M4→M5 contract (write→parse fidelity). Additionally, the Critical gate includes "re-run all upstream module test files" which covers regression.
- **Disconfirmation:** If M5 had Python imports from engine_core, this would be P1. Verified Task 12 uses `subprocess.run()` (plan line 4080-4085), not direct imports. Sentinel checks for subprocess invocability would be redundant with the test suite.
- **Recommendation:** Could add: "At M4→M5: Standard+ sentinel checks are subsumed by the round-trip probe (which exercises the write→parse contract M5 integration tests depend on)." Not blocking.

### F5: "Brief invariant summary" vague for M2 internal execution
- **Priority:** P2 | **Evidence:** E1 | **Confidence:** Medium
- **Linked dimensions:** D14 (precision)
- **Claim:** Line 170 says M2 phased execution includes "Brief invariant summary of parse API surface" between Task 3 and Task 14. "Brief" is unquantified — no format, required content, or minimum coverage specified.
- **Artifacts:** Design line 170
- **Impact:** Low — this is an internal M2 checkpoint (between Task 3 and Task 14 within the same agent session), not a gate artifact. The executing agent would naturally summarize the parse API after implementing it. The M2→M3 gate card captures the formal API surface check.
- **Recommendation:** Could replace with: "Enumerate parse API exports (function names + return types) as a checkpoint before proceeding to Task 14." Not blocking.

## Disconfirmation Attempts

### P0 Dimensions

**D2 (Semantic fidelity) — 2 techniques:**
1. **Cross-check:** Verified import dependency graph against source plan by grepping for all `from scripts.ticket_* import` statements (6 distinct import lines across tasks 4, 6, 9, 10, 11, 14). All imports match the design's claims.
   - Result: Confirmed. No discrepancies found.
2. **Counterexample search:** Searched for imports the design might have missed — checked Tasks 5 and 7 for any ticket_parse imports. Also checked Task 8 range for unexpected imports.
   - Result: Confirmed. No unexpected imports found in any task range.

**D3 (Procedural completeness) — 2 techniques:**
1. **Adversarial read:** Traced each gate type through its definition, checking for unstated preconditions or missing steps. Standard gate: clear (run tests, check imports, derive verdict). Standard+: clear (Standard + sentinel imports). Critical: clear (Standard+ + upstream re-run + downstream preflight).
   - Result: Confirmed complete. M4→M5 sentinel omission is P2 (subprocess, not imports).
2. **Cross-check:** Compared gate steps to CI/CD pipeline patterns (build → test → verify → promote). The design's Standard gate maps to test+verify; Standard+ adds integration-level smoke; Critical adds regression + downstream.
   - Result: Confirmed. Gate types are a well-structured escalation.

**D4 (Decision rules) — 2 techniques:**
1. **Counterexample search:** What if failure classification is ambiguous (flaky test that sometimes passes)? Design says "After 2 retries of a transient failure, escalate." This handles ambiguity by defaulting to escalation after retry budget exhausted.
   - Result: Confirmed adequate. The retry budget provides a bounded resolution path.
2. **Adversarial read:** What if 3-branch attribution misclassifies (treats boundary fault as local)? The executor would attempt a local fix, fail, and naturally re-evaluate. The design doesn't explicitly say "re-evaluate attribution on local fix failure," but the 4-step process restarts at the failure point.
   - Result: Confirmed adequate with minor gap — no explicit re-evaluation loop, but the implicit restart is sufficient for a 5-module process.

**D5 (Exit criteria) — 2 techniques:**
1. **Cross-check:** Each gate has `verdict: PASS | FAIL`. Standard gate defines PASS as "all commands exit 0 and all expected symbols import successfully [T]." Standard+/Critical inherit and extend.
   - Result: Confirmed complete.
2. **Negative test:** What if verdict is PASS but the module has undetected defects? The next gate's cumulative `must_pass_files` provides multi-gate defense-in-depth. The M4→M5 round-trip probe specifically targets the highest-risk undetected defect (write→parse fidelity).
   - Result: Confirmed. Defense-in-depth provides catch-net for false PASS.

**D6 (Safety defaults) — 2 techniques:**
1. **Cross-check:** Failure Recovery has 4 steps with escalation. Gate 0 blocks M1 on failure. Cross-boundary edits disallowed. Warnings non-blocking.
   - Result: Confirmed complete.
2. **Counterexample search:** Are the 3 attribution branches exhaustive? Upstream (sentinels fail), local (sentinels pass + current module file), boundary (sentinels pass + cross-module interaction). Any failure must be in one of: prior module code (upstream), current module code (local), or the interaction between them (boundary). These are exhaustive.
   - Result: Confirmed. The 3 branches partition the failure space completely.

## Adversarial Pass

All 9 lenses applied (Rigorous requirement).

| Lens | Objection | Response | Residual Risk |
|------|-----------|----------|---------------|
| A1: Assumption Hunting | Design assumes complete import dependency graph. If plan is modified or agent adds unexpected imports, sentinel checks miss them. | Plan is read-only during execution (line 43). Only exception is remediation cycle, which requires reviewer authorization. | Low — read-only constraint prevents import graph drift. |
| A2: Scale Stress | At 10x modules (50), cumulative must_pass_files grows linearly. At 10x remediation cycles, no "give up" condition exists. | The design is scoped to 5 modules. Remediation cycles are bounded by the sequential nature — at worst, re-enter one upstream module. | Low — bounded by module count. |
| A3: Competing Perspectives | Performance: running 7 cumulative test files + probe at M4→M5 gate could be slow. | ~128 tests total, expected <30s. Acceptable for gate review cadence. | Negligible. |
| A4: Kill the Design | Process overhead (gate cards, two-SHA, invariant ledgers, probes) slows execution significantly vs. running 15 tasks straight. | Gate overhead (~30 min per boundary × 4 = 2 hours) is far cheaper than reworking 3 modules after a late-discovered M2 parser defect. The 4870-line plan exceeds agent context for single-shot execution. | Accepted trade-off: 2 hours overhead for defect-early-detection. |
| A5: Pre-mortem | 6 months later, failure cause: (1) executing-plans sub-skill lacks handoff prompt concept — Gate 0 passes but gate cards have nowhere to go, (2) M4 monotonicity check is syntactically monotonic but semantically degraded (trivial tests replace real ones). | (1) Gate 0 check #1 verifies skill existence; if it lacks handoff prompts, execution would fail immediately at M1. (2) [M] enforcement catches count regression; semantic degradation requires reviewer judgment, which is the design intent. | Medium — Gate 0 adequacy is the highest residual risk. If the sub-skill doesn't support module-level handoffs, the entire design is blocked (which is fail-safe). |
| A6: Steelman Alternatives | (1) No modularization: single-shot execution. (2) 15 modules (one per task). (3) Branch-based isolation without contract-aware gates. | (1) ~4870 lines exceeds agent context. (2) 14 gate reviews is excessive for mostly-safe boundaries. (3) Branches don't verify API contracts or import surfaces. | None — 5-module gated approach is well-justified. |
| A7: Challenge the Framing | Maybe the plan is too detailed (4870 lines). A less detailed plan would fit without modularization. | Plan detail was deliberately calibrated through 2 adversarial reviews (32+13 defects). Reducing detail re-introduces ambiguities those reviews caught. | None — the plan's detail level is justified. |
| A8: Hidden Complexity | Two-SHA model adds 4 reviewer commits + 4 diff verifications. M4's 6 full checkpoints + 3 commit-only snapshots = 9 internal commits. | Reviewer commits are lightweight (gate card + evidence). Internal commits are standard TDD snapshots. Total additional commits: ~13 (4 gate + 9 M4 internal). Manageable. | Low — commit count is bounded and manageable. |
| A9: Motivated Reasoning | 5-module split established in round 1 collaborative dialogue, never challenged in 4 adversarial rounds. Could be anchored to initial idea. | Justifications are technical: dependency chain (M1→M5 sequential), shared files (Tasks 8-11 modify same file), context load (M4 at 1924 lines within capacity). No adversarial review proposed an alternative because the split is sound. | Low — technical rationale is defensible. |

**Most impactful objection:** A5 (Pre-mortem) — Gate 0's adequacy as a guard against executing-plans sub-skill incompatibility. If the sub-skill doesn't support module-level handoff prompts, execution is blocked. This is **fail-safe** (blocked, not silently broken), which is the correct failure mode.

## Decidable vs. Undecidable

**Decide now:**
- Design is ready for implementation. No P0/P1 findings block execution.
- All 5 P2 findings are cosmetic — none require changes before proceeding.

**Can't decide yet:**
- Whether Gate 0 will pass (requires running the 4 verification commands against the actual sub-skill).
- Whether M4's 1924 lines will cause context issues in practice (theoretical concern, well within 200k token capacity).
- Whether the round-trip probe's 4 vectors are sufficient (coverage question that can only be answered by execution).

**What would change the decision:**
- A P0 finding (none found).
- Gate 0 failure (blocks execution, forces sub-skill modification).
- Discovery that the import dependency graph is wrong (verified E2 — unlikely).

## Exit Gate

| Criterion | Status |
|-----------|--------|
| Coverage complete | PASS — All 19 dimensions are `[x]` or `[-]` (with rationale). No `[ ]` or `[?]` remaining. |
| Evidence requirements met | PASS — All 5 P0 dimensions have E2 evidence. All P1 dimensions have E1+. |
| Disconfirmation attempted | PASS — 2 techniques per P0 dimension (10 total). All confirmed, no disconfirmation succeeded. |
| Assumptions resolved | PASS — A1-A5 all verified against source material. |
| Convergence reached | PASS — Yield% = 0% (Pass 2) < 10% Rigorous threshold. |
| Connections mapped | PASS — No P0/P1 findings to map. P2 findings linked to dimensions with low propagation impact. |
| Adversarial pass complete | PASS — All 9 lenses applied with objections, responses, and residual risks documented. |
| Stopping criteria met | PASS — Risk-based: all P0 dimensions `[x]` with ≥E2. Discovery-based: Pass 2 had zero new P0/P1 findings. |

## Post-Completion Self-Check

- [x] Entry Gate: inputs, assumptions, stakes, stopping criteria all recorded
- [x] DISCOVER: 3 techniques applied (external taxonomy, pre-mortem, perspective multiplication); D12-D19 not skipped; D15/D17 marked `[-]` with skeptical-reviewer justification
- [x] EXPLORE: each dimension has Cell Schema fields; findings linked to dimensions
- [x] VERIFY: disconfirmation techniques documented with technique names AND results
- [x] REFINE: Yield% calculated per pass (100% → 0%); iteration log shows pass-by-pass changes
- [x] Adversarial: all 9 lenses applied; A5 pre-mortem produced specific plausible failure story (Gate 0 / handoff prompt gap)
- [x] If a P0 existed, would the user definitely see it in the summary? — Yes (summary table at top)
- [x] If the design had hidden flaws, did I genuinely try to find them? — Yes (verified import graph against source, traced gate types, applied 9 adversarial lenses, wrote specific failure stories)

## Appendix

### Source Verification Evidence

| Claim | Design Line | Plan Evidence | Status |
|-------|-------------|---------------|--------|
| Task 4 imports extract_fenced_yaml, parse_yaml_block from ticket_parse | 100 | Plan line 1286 | Confirmed |
| Task 6 imports ParsedTicket, parse_ticket from ticket_parse | 100 | Plan line 1840 | Confirmed |
| Task 5 does not import from ticket_parse | 100 | No hits in plan lines 1399-1663 | Confirmed |
| Task 7 does not import from ticket_parse | 100 | No hits in plan lines 1938-2124 | Confirmed |
| Task 9 imports ParsedTicket from ticket_parse | 101 (via M4 import subset) | Plan line 2484 | Confirmed |
| Task 9 imports dedup_fingerprint, normalize, target_fingerprint from ticket_dedup | 101 | Plan line 2482 | Confirmed |
| Task 9 imports list_tickets from ticket_read | 101 | Plan line 2483 | Confirmed |
| Task 10 imports find_ticket_by_id, list_tickets from ticket_read (function-local) | 101 | Plan lines 3029, 3044 | Confirmed |
| Task 10 imports target_fingerprint from ticket_dedup (function-local) | 101 | Plan line 3068 | Confirmed |
| Task 11 imports parse_ticket, extract_fenced_yaml, parse_yaml_block from ticket_parse | 101 | Plan line 3518 | Confirmed |
| Task 11 imports allocate_id, build_filename from ticket_id | 101 | Plan line 3516 | Confirmed |
| Task 11 imports render_ticket from ticket_render | 101 | Plan line 3517 | Confirmed |
| Task 14 imports parse_ticket from ticket_parse | 37 | Plan line 4656 | Confirmed |
| Task 14 imports make_gen1/2/3/4_ticket from conftest | 37 | Plan lines 4661-4736 | Confirmed |
| conftest helpers are plain functions (not fixtures) | Handoff gotcha | Plan lines 193-284 (no @pytest.fixture) | Confirmed |
| Task 12 uses subprocess invocation (not Python imports) | F4 analysis | Plan lines 4080-4085 (subprocess.run) | Confirmed |
| M1 test count = 0 | Module table | Tasks 1-2 have no test files | Confirmed |
| M2 test count ≈ 25 | Module table | Tasks 3 (~20) + 14 (~5) = 25 | Confirmed |
| M3 test count ≈ 42 | Module table | Tasks 4 (~10) + 5 (~5) + 6 (~15) + 7 (~12) = 42 | Confirmed |
| M4 test count ≈ 49 | Module table | Tasks 8 (~8) + 9 (~5) + 10 (~15) + 11 (~21) = 49 | Confirmed |
| M5 test count ≈ 9 | Module table | Tasks 12 (~5) + 13 (~4) + 15 (0) = 9 | Confirmed |
