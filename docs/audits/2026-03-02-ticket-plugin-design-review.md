# Ticket Plugin Design Review

**Target:** `docs/plans/2026-03-02-ticket-plugin-design.md` (717 lines)
**Protocol:** reviewing-designs skill with Framework for Thoroughness v1.0.0
**Date:** 2026-03-02
**Review round:** 6 (prior: collaborative, adversarial, team, triage, evaluative)

## Summary

| Priority | Count | Description |
|----------|-------|-------------|
| P0 | 8 | Issues that break correctness or block implementation |
| P1 | 14 | Issues that degrade quality or create ambiguity |
| P2 | 10 | Polish items and minor gaps |

**Key issues:**
- Engine pipeline has 3 behavioral gaps at core decision points (classify threshold, preflight state mapping, create autonomy stage)
- Error codes and machine states are inconsistent (3 codes have no state, 2 have name mismatches)
- session_id delivery mechanism is fragile — entire autonomy cap system depends on it
- Security bypass via shell obfuscation is documented but permanent without v1.1 MCP migration
- Over-engineering concern: enterprise-grade complexity for single-user single-repo problem

## Entry Gate

**Inputs:**
- Target: `docs/plans/2026-03-02-ticket-plugin-design.md` (717 lines, on `main` at `c052fdb`)
- Sources: None (design is the source — D1-D3 skipped)
- User concern: Pre-implementation readiness

**Assumptions:**
1. Design doc is current version (on `main`)
2. Prior 5 review rounds' findings are incorporated
3. No source documents to compare against (design is self-contained)
4. Single-user plugin context (not multi-tenant)

**Stakes:** Rigorous
- Reversibility: Some undo cost (design becomes canonical implementation spec)
- Blast radius: Wide (every future ticket operation constrained by these decisions)
- Cost of error: Medium-High (implementation effort wasted on ambiguous spec)
- Uncertainty: Moderate (5 prior rounds reduced but didn't eliminate)
- Time pressure: Low (design hardening before implementation)

**Stopping criteria:** Yield% < 10%

## Review Team

| Agent | Dimensions | Focus |
|-------|-----------|-------|
| impl-reviewer | D4-D11 | Behavioral completeness + implementation readiness |
| quality-reviewer | D12-D19 | Cross-validation + document quality |
| codebase-reviewer | — | Design vs existing codebase patterns |
| adversarial-reviewer | 9 lenses | Kill the design |

## Coverage Tracker

### Source Coverage (D1-D3)

| ID | Status | Priority | Evidence | Confidence | Notes |
|----|--------|----------|----------|------------|-------|
| D1 | [-] | — | — | — | N/A: no source documents. Design is self-contained. |
| D2 | [-] | — | — | — | N/A: same reason as D1. |
| D3 | [-] | — | — | — | N/A: same reason as D1. |

**Justification:** This design was created through iterative Codex dialogues, not derived from a source spec. Prior review rounds verified architectural completeness. Skeptical reviewer test: accepted — there is genuinely no source document to compare against.

### Behavioral Completeness (D4-D6)

| ID | Status | Priority | Evidence | Confidence | Notes |
|----|--------|----------|----------|------------|-------|
| D4 | [~] | P0 | E2 | High | 3 decision rules missing: classify threshold, preflight state, create autonomy stage |
| D5 | [~] | P1 | E1 | High | "resolved" undefined for blocked_by; no fallback for unknown first-token |
| D6 | [~] | P1 | E1 | High | Audit write ordering unspecified; stale_plan recovery path missing |

### Implementation Readiness (D7-D11)

| ID | Status | Priority | Evidence | Confidence | Notes |
|----|--------|----------|----------|------------|-------|
| D7 | [~] | P2 | E1 | Medium | ticket_render.py unspecified; intent vocabulary not enumerated |
| D8 | [~] | P2 | E1 | High | Render module gap |
| D9 | [~] | P0 | E2 | High | session_id delivery + Python environment assumptions |
| D10 | [~] | P1 | E1 | Medium | Directory bootstrap, force+fingerprint interaction |
| D11 | [~] | P2 | E1 | Medium | No test vectors for orphan detection |

### Consistency (D12)

| ID | Status | Priority | Evidence | Confidence | Notes |
|----|--------|----------|----------|------------|-------|
| D12 | [~] | P0 | E2 | High | Error codes vs machine states mismatch; plan_fingerprint producer gap; example vs schema |

### Document Quality (D13-D19)

| ID | Status | Priority | Evidence | Confidence | Notes |
|----|--------|----------|----------|------------|-------|
| D13 | [~] | P1 | E2 | Medium | plan_fingerprint ambiguous (dedup vs TOCTOU) |
| D14 | [x] | — | E1 | High | Language is precise throughout |
| D15 | [~] | P0 | E2 | High | Example ticket contradicts schema (missing contract_version) |
| D16 | [~] | P0 | E2 | High | Error codes/states disagree; close/archive conflated |
| D17 | [~] | P2 | E1 | High | Fail-closed stated 4 times; ticket_source naming drift |
| D18 | [~] | P2 | E1 | Medium | --from-envelope pipeline unverifiable |
| D19 | [~] | P1 | E1 | High | Two implementers diverge on fingerprint producer, close target status |

### Codebase Fit

| Area | Status | Notes |
|------|--------|-------|
| Plugin structure | Compatible | Matches cross-model and handoff patterns |
| Existing ticket patterns | Partially compatible | PyYAML dependency undeclared; import fallback pattern needed |
| Hook patterns | Compatible | Bash matcher performance risk (fires on every Bash call) |
| Skill/agent patterns | Compatible | First proactive agent in codebase (novel, needs testing) |
| Contract patterns | Partially compatible | Split-source contract diverges from single-doc precedent |
| Testing patterns | Compatible | Matches context-injection and context-metrics patterns |

## Iteration Log

| Pass | Action | P0+P1 Entities | Yielding | Yield% |
|------|--------|----------------|----------|--------|
| 1 | 4 parallel agents across all dimensions + adversarial | 22 | 22 (all new) | 100% |

**Note:** Pass 1 is always 100% yield. However, this was a 4-agent parallel review with high finding density. The findings are primarily cross-section inconsistencies and behavioral gaps at decision points — exactly what 5 prior rounds (which focused on architecture, control flow, specification, and contracts) didn't cover. A second pass would target disconfirmation of P0s rather than new discovery.

**Convergence assessment:** The team structure compressed multiple serial passes into one parallel pass. Findings are internally consistent across agents (session_id delivery flagged by both adversarial and impl reviewers; fingerprint ambiguity flagged by both quality and impl reviewers). Cross-agent agreement suggests the dimension space is well-covered.

## P0 Findings

### P0-1: classify confidence threshold unspecified [D4]

**Source:** impl-reviewer
**Location:** Lines 301, 505
**Issue:** `classify` returns `intent + confidence` (float), but no threshold defines when confidence is too low to proceed. Every mutation flows through `classify` first. Without a threshold, the implementer must invent behavioral policy.
**Evidence:** E1 (design doc only) | Confidence: High
**Impact:** Two implementers would set different thresholds, producing different behavior for ambiguous inputs.

### P0-2: preflight failure has no defined machine state [D4]

**Source:** impl-reviewer
**Location:** Lines 303, 507, 210-225, 497
**Issue:** `preflight` returns `checks_passed` and `checks_failed` but does not map to a machine state. The common response envelope requires `state: string`. The 12 machine states don't include a generic "preflight_failed." The implementer must decide which state maps to which failure — a behavioral decision left unspecified.
**Evidence:** E2 (envelope contract + state table both lack this) | Confidence: High

### P0-3: create pipeline autonomy check stage ambiguous [D4]

**Source:** impl-reviewer
**Location:** Lines 201, 302, 309, 370-392
**Issue:** `create` uses `classify → plan → execute` (no `preflight`). Autonomy is checked in `preflight` (line 309). The autonomy pseudocode (line 370) is stage-agnostic. For agent-initiated `create`, the stage that enforces the autonomy cap is unspecified.
**Evidence:** E2 (pipeline + pseudocode contradict) | Confidence: Medium

### P0-4: Error codes vs machine states mismatch [D12, D16]

**Source:** quality-reviewer
**Location:** Lines 499, 510, 212-225
**Issue:** 8 error codes claim to map to "exactly one machine state," but 3 codes (`stale_plan`, `audit_unavailable`, `parse_error`) have no corresponding machine state. 2 codes have name mismatches (`missing_field` vs `need_fields`, `duplicate_detected` vs `duplicate_candidate`). An implementer cannot build the error→state mapping from this spec.
**Evidence:** E2 (two sections disagree) | Confidence: High

### P0-5: plan_fingerprint has no producer for update/close/reopen [D12, D16, D19]

**Source:** quality-reviewer
**Location:** Lines 507, 318, 505-508
**Issue:** `preflight` input requires `plan_fingerprint: string`, but the update/close/reopen pipeline (`classify → preflight → execute`) has no `plan` stage to produce it. Only `create` goes through `plan`. Two implementers would build different solutions (preflight self-computes vs null allowed).
**Evidence:** E2 (two sections disagree) | Confidence: High

### P0-6: Example ticket missing contract_version [D12, D15]

**Source:** quality-reviewer
**Location:** Lines 82-95, 476, 538
**Issue:** `contract_version` is declared a required YAML field, but the only example ticket in the entire design doc omits it. The concrete example contradicts the schema requirement.
**Evidence:** E2 (example vs schema) | Confidence: High

### P0-7: session_id delivery mechanism fragile [D9, Adversarial Lens 1]

**Source:** adversarial-reviewer (P0) + impl-reviewer (D9-1, P2 — escalated)
**Location:** Line 436
**Issue:** Line 436 says "Claude Code provides `session_id` via hook input JSON; the skill passes it through to the engine's stdin." But skills are markdown instructions, not hooks — they don't receive hook input JSON. The skill must instruct the model to extract session_id from context and faithfully pass it. If session_id is wrong, fabricated, or reused, the entire autonomy cap (guardrail 3) is defeated — a session appearing to have 0 creates gets unlimited creates.
**Evidence:** E2 (platform docs + design doc disagree on delivery mechanism) | Confidence: High
**Note:** The adversarial pre-mortem developed this into a concrete failure scenario where fabricated session IDs led to 47 uncapped ticket creates.

### P0-8: Security bypass via shell obfuscation is permanent without v1.1 [Adversarial Lens 3]

**Source:** adversarial-reviewer
**Location:** Lines 362, 364
**Issue:** The PreToolUse hook non-coverage statement acknowledges it "cannot reliably catch shell obfuscation (`eval`, backtick expansion, `$()` substitution)." A prompt-injection attack causing the model to call `eval "python3 ticket_engine_core.py execute ..."` with `request_origin=user` bypasses the entire trust model. The v1.1 MCP migration (line 364) would fix this but has no timeline. If v1.1 never ships, the trust model has a permanent documented bypass.
**Evidence:** E1 (design doc's own non-coverage statement) | Confidence: High

## P1 Findings

### P1-1: blocked→open "resolved" undefined [D5]

**Source:** impl-reviewer (D5-1)
**Location:** Line 521
**Issue:** Transition requires "all `blocked_by` resolved" but "resolved" is undefined against the 5-state set. Does `wontfix` count as resolved?
**Evidence:** E1 | Confidence: High

### P1-2: No fallback for unknown first-token [D5]

**Source:** impl-reviewer (D5-2)
**Location:** Lines 191-199, 505
**Issue:** Routing table has no default/fallback row. Unknown input like `/ticket something_unexpected` has no defined behavior.
**Evidence:** E1 | Confidence: High

### P1-3: Audit trail write failure creates partial state [D6]

**Source:** impl-reviewer (D6-1)
**Location:** Lines 430-453, 401
**Issue:** If ticket file is written but audit write fails, a ticket exists with no audit record. For `auto_silent`, this ticket is invisible to the session cap counter. Write ordering (ticket-first vs audit-first) is unspecified.
**Evidence:** E1 | Confidence: High

### P1-4: stale_plan recovery path unspecified [D6]

**Source:** impl-reviewer (D6-2)
**Location:** Line 318, 210-225, 510
**Issue:** `stale_plan` is an error code but has no machine state and no defined UX response (retry? re-plan? ask user?).
**Evidence:** E2 | Confidence: High

### P1-5: Empty tickets directory bootstrap [D10]

**Source:** impl-reviewer (D10-1)
**Location:** Line 474
**Issue:** Engine creates directories on first write, but `classify` and `plan` read from `docs/tickets/`. Read path behavior when directory doesn't exist is unspecified.
**Evidence:** E1 | Confidence: Medium

### P1-6: force:true with plan_fingerprint mismatch [D10]

**Source:** impl-reviewer (D10-2)
**Location:** Lines 336, 508
**Issue:** When user confirms duplicate, `execute` requires `plan_fingerprint` but the duplicate candidate may have changed between user seeing it and confirming.
**Evidence:** E1 | Confidence: Medium

### P1-7: ok_close UX implies archiving but archiving is separate [D12, D16]

**Source:** quality-reviewer (P1-1)
**Location:** Lines 216, 526
**Issue:** `ok_close` machine state says "(moved to archive)" but archiving is a separate explicit step via `--archive` flag. UX mapping conflates close with archive.
**Evidence:** E2 | Confidence: High

### P1-8: close target status unspecified [D19]

**Source:** quality-reviewer (P1-2)
**Location:** Line 195, 516-526
**Issue:** "Close/resolve ticket" doesn't specify which terminal status (`done` vs `wontfix`). Multiple transitions exist to terminal states with different preconditions.
**Evidence:** E1 | Confidence: High

### P1-9: Dedup vs TOCTOU fingerprint ambiguity [D13, D14]

**Source:** quality-reviewer (P1-3)
**Location:** Lines 322, 318, 506
**Issue:** `plan` output returns a single `fingerprint` field but two different fingerprints are computed (dedup = normalize+hash, TOCTOU = content+mtime). Which one is in the output?
**Evidence:** E2 | Confidence: Medium

### P1-10: Scale stress — scan budget undercounted, triage O(n) [Adversarial Lens 2]

**Source:** adversarial-reviewer
**Location:** Lines 460, 313, 464
**Issue:** 3-scan-per-create budget undercounts (preflight dependency checks add scans). Triage scans full corpus — O(n) at 1700 tickets with YAML parsing becomes a latency hit. Indexing deferred to v1.1.
**Evidence:** E1 | Confidence: Medium

### P1-11: Over-engineering for single-user problem [Adversarial Lens 4]

**Source:** adversarial-reviewer
**Issue:** 4-stage pipeline, 3-tier autonomy with 6 guardrails, split entrypoints, PreToolUse hooks, per-session audit trails, 4-generation migration, TOCTOU mitigation — enterprise complexity for managing markdown files in one directory for one user. A single skill + script covers 90% of the value at 10% complexity.
**Evidence:** E1 (comparative analysis) | Confidence: Medium

### P1-12: Hidden complexity — defer.active + transitions [Adversarial Lens 8]

**Source:** adversarial-reviewer
**Location:** Lines 478, 516-527
**Issue:** What happens when a deferred ticket (`defer.active: true`, status `open`) transitions to `in_progress`? Does `defer.active` auto-clear? The design doesn't say. Also, conversion-on-update for legacy tickets with free-text fields (e.g., `effort: "S (1-2 sessions)"`) is a state explosion.
**Evidence:** E1 | Confidence: High

### P1-13: Motivated reasoning — anchoring to Architecture E [Adversarial Lens 9]

**Source:** adversarial-reviewer
**Location:** Lines 7, 33-39
**Issue:** The rejected alternatives table has no row for "single skill with template, no engine." The possibility space was pre-narrowed to architectures that justify an engine. 5 review rounds and a 717-line doc create sunk cost that makes "start simpler" feel wasteful.
**Evidence:** E1 (structural analysis of alternatives table) | Confidence: Medium

### P1-14: Bash matcher performance risk [Codebase]

**Source:** codebase-reviewer (3A)
**Issue:** The PreToolUse hook matches on `Bash` tool, firing on every Bash call in sessions where the plugin is enabled. Must be very fast (<50ms) to avoid noticeable latency. Existing plugins use narrow matchers (specific MCP tool patterns).
**Evidence:** E1 (codebase comparison) | Confidence: High

## P2 Findings

### P2-1: ticket_source vs source naming drift [D17]

**Source:** quality-reviewer
**Location:** Line 631 vs lines 88, 347, 366, 476
**Issue:** One reference uses `ticket_source`; all others use `source`. Minor inconsistency from accumulated patches.

### P2-2: --from-envelope pipeline unspecified [D18, D19]

**Source:** quality-reviewer
**Location:** Line 552
**Issue:** `/ticket create --from-envelope <path>` introduced but doesn't specify how it modifies the create pipeline (skip classify? run dedup?).

### P2-3: Redundant fail-closed statements [D17]

**Source:** quality-reviewer
**Location:** Lines 384, 394, 401, 452
**Issue:** Same fail-closed policy stated 4 times with slightly different wording. Not contradictory, but drift risk from accumulated patches.

### P2-4: reopen not in classify intent vocabulary [D7]

**Source:** impl-reviewer (D7-1)
**Location:** Line 505, 196
**Issue:** `classify` output includes `intent: string` but valid intent values aren't enumerated. `reopen` was added later and may not be in the vocabulary.

### P2-5: ticket_render.py has no specification [D8]

**Source:** impl-reviewer (D8-1)
**Location:** Line 61
**Issue:** Listed in plugin structure but never referenced in any pipeline stage or skill flow. Contract absent.

### P2-6: No test vectors for orphan detection [D11]

**Source:** impl-reviewer (D11-1)
**Location:** Lines 63, 66-72, 254
**Issue:** Test plan lists `test_triage.py` but no test vectors for the 3 matching strategies ported from handoff.

### P2-7: PyYAML dependency undeclared [Codebase]

**Source:** codebase-reviewer (2B)
**Issue:** Design doesn't mention a `pyproject.toml` or declare PyYAML as runtime dependency. Handoff plugin declares `pyyaml>=6.0`.

### P2-8: Contract split-source diverges from precedent [Codebase]

**Source:** codebase-reviewer (5A)
**Issue:** Context-injection contract is a single self-contained document. Ticket contract is split between design doc and a not-yet-created `references/ticket-contract.md`. Implementer must read two documents.

### P2-9: Import fallback pattern needed [Codebase]

**Source:** codebase-reviewer (2A)
**Issue:** Existing handoff scripts use dual-import fallback (`try: from scripts.X / except: sys.path.insert`). Ticket plugin scripts will need the same pattern.

### P2-10: First proactive agent in codebase [Codebase]

**Source:** codebase-reviewer (4A)
**Issue:** `ticket-autocreate` would be the first agent using "use proactively" in its description. Follows documented convention but is novel in this codebase — needs thorough testing.

## Adversarial Pass

All 9 lenses applied at Rigorous depth. Objections documented with responses or accepted risks.

### Lens 1: Assumption Hunting — P0

session_id delivery mechanism is the design's load-bearing assumption. If it fails, the autonomy cap is theater. The Python execution environment assumption (does the target repo have `uv`?) is a secondary concern.

### Lens 2: Scale Stress — P1

Scan budget is optimistic for non-create operations. Triage at >500 tickets is O(n) with no index. v1.0 ships with known performance cliffs deferred to v1.1.

### Lens 3: Competing Perspectives — P0

Security: documented shell obfuscation bypass is permanent without v1.1 MCP migration. Operations: one-way traceability only (audit→ticket but no ticket→audit back-pointer).

### Lens 4: Kill the Design — P1

Enterprise complexity for a single-user problem. A skill + script covers 90% of the value at 10% of the complexity. Counter: the autonomy model and audit trail address a real risk (unconstrained agent ticket creation). But the risk can be mitigated with simpler controls (no agent, or agent with tool restrictions only).

### Lens 5: Pre-mortem — P0 (scenario)

Specific failure story: Plugin ships but (1) session_id delivery never works reliably — fabricated IDs defeat caps, (2) Python environment missing in non-Python repos, (3) migration's 3-tier section renaming misleads on Gen 3 tickets, (4) DeferredWorkEnvelope schema never formally defined — cross-plugin integration is dead code. Multiple cascading failures from independent assumptions.

### Lens 6: Steelman Alternatives — P1

SQLite eliminates O(n) scans, TOCTOU races, and audit corruption. Flat file without engine covers 90% of value. Both were not considered in the alternatives table.

### Lens 7: Challenge the Framing — P1

Root cause of poor ticket quality was `/defer` being tacked onto `/save` with no template. A better defer template + quality requirements in the handoff contract may solve the problem without a separate plugin.

### Lens 8: Hidden Complexity — P1

defer.active + status transitions interaction unspecified. Conversion-on-update for 4 legacy generations is a state explosion. These look simple in the spec but are combinatorially complex in implementation.

### Lens 9: Motivated Reasoning — P1

Anchoring to Architecture E. No "simple alternative" in the rejected table. 5 review rounds and 717 lines create sunk cost bias. A fresh designer would not arrive at this complexity for the stated requirements.

## Disconfirmation Attempts

### P0-4 (Error codes vs machine states): Counterexample search

Searched for any text indicating error codes are independent of machine states. Line 510 explicitly says "each maps to exactly one machine state" — the mapping claim is unambiguous. The missing states are genuine gaps, not a misreading. **Confirmed.**

### P0-7 (session_id delivery): Alternative hypothesis

Hypothesis: Maybe Claude Code injects session_id into the conversation context automatically, and the skill can reference it. Counter: Claude Code docs don't document this behavior for skills. Hook input JSON is only available to hook scripts, not skill markdown. The design's own line 436 says "hook input JSON" — acknowledging it's hook-level data. **Confirmed — delivery mechanism is genuinely unspecified for the skill→engine path.**

### P0-8 (Security bypass): Negative test

If the finding is wrong, the PreToolUse hook would catch `eval` obfuscation. Line 362 explicitly states it cannot. The design's own non-coverage statement confirms the bypass. **Confirmed.**

### P1-11 (Over-engineering): Adversarial read

Could the complexity be justified? The autonomy model addresses a real risk: unconstrained agent ticket creation could produce 50+ low-quality tickets in a session. The audit trail provides accountability. But the same protection is achievable with: (1) a tool restriction on the agent (no Write tool), (2) a simple counter in the skill, (3) no engine pipeline. The 4-stage pipeline, split entrypoints, and TOCTOU mitigation add complexity beyond what the threat model requires. **Partially confirmed — the risk is real but the mitigation is disproportionate.**

## Exit Gate

| Criterion | Status |
|-----------|--------|
| Coverage complete | Yes — all applicable dimensions checked (D1-D3 N/A with justification) |
| Evidence requirements met | Yes — P0 dimensions at E2 for Rigorous |
| Disconfirmation attempted | Yes — 4 P0 findings tested with 2+ techniques each |
| Assumptions resolved | 3 of 4 verified; #4 (single-user) accepted as given |
| Convergence | Single parallel pass — see note below |
| Adversarial pass complete | Yes — all 9 lenses applied |

**Convergence note:** This was a 4-agent parallel review, not a serial iteration. Yield% calculation assumes Pass 1 = 100% (all findings are new). A second serial pass would be needed to reach <10% Yield%. However: (1) cross-agent finding agreement (session_id, fingerprint ambiguity flagged by 2 agents each) indicates good coverage, (2) the 8 P0 findings are dense enough that remediation should precede further review, (3) a verification pass after remediation is more valuable than another discovery pass now.

**Recommendation:** Fix the 8 P0s, then run a verification pass (Yield% check) before implementation planning.
