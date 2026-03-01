# Design Review: Context Metrics Plugin

**Date:** 2026-02-28
**Target:** `docs/plans/2026-02-28-context-metrics-design.md` (1047 lines, 4 amendments)
**Stakes:** Rigorous
**Stopping criterion:** Yield% < 10%
**Reviewer:** Claude (pre-implementation-planning review)

## Summary

| Priority | Count | Description |
|----------|-------|-------------|
| P0 | 2 | Contradictions that could cause incorrect implementation |
| P1 | 18 | Stale/ambiguous content that slows implementation planning |
| P2 | 7 | Polish and edge cases |

**Verdict:** Design is architecturally sound after 3 Codex reviews. The primary issue is NOT design quality — it's **document readability**. The append-only amendment pattern has created 6 superseded sections that contradict current design truth. An implementation plan writer must mentally compile 4 amendment layers to extract the v1 specification.

**Recommendation:** Add a supersession index to the top of the document before implementation planning. Alternatively, create a consolidated v1 specification as a separate section that synthesizes all amendments into a single coherent view.

## Entry Gate

**Inputs:**
- Target: `docs/plans/2026-02-28-context-metrics-design.md`
- Sources: research doc, plugin rules, hook rules, 3 Codex review threads
- Concern: implementation readiness after 4 amendment layers

**Assumptions:**
1. Amendment 4 (latest) is authoritative where conflicts exist ✓ Validated
2. v1 scope table in Amendment 4 Finding 10 is the definitive scope ✓ Validated
3. Design has been thoroughly reviewed for correctness (3 Codex reviews) ✓ Validated
4. Research document is complete — Assumed (not re-verified)

**Stakes:** Rigorous (implementation follows; errors waste implementation effort)
**Stopping:** Yield% < 10%

## Iteration Log

| Pass | New P0+P1 | Total P0+P1 | Yield% | Focus |
|------|-----------|-------------|--------|-------|
| 1 | 17 | 17 | 100% | Cross-amendment consistency, stale content |
| 2 | 5 | 22 | 22.7% | Behavioral completeness, decision rules |
| 3 | 5 | 27 | 18.5% | Document quality, terminology, defaults |
| 4 | 1 | 28 | 3.6% | Adversarial lenses |

Converged at Pass 4 (3.6% < 10%).

## Coverage Tracker

| ID | Dimension | Status | Priority | Evidence | Confidence |
|----|-----------|--------|----------|----------|------------|
| D4 | Decision rules at branch points | [~] | P0 | E2 | Medium |
| D5 | Error/failure modes defined | [~] | P1 | E2 | Medium |
| D6 | Exit criteria / success metrics | [~] | P1 | E1 | Low |
| D7 | Sufficient implementation detail | [~] | P1 | E2 | Medium |
| D8 | Component dependencies clear | [x] | P1 | E2 | High |
| D9 | External dependencies documented | [x] | P1 | E2 | High |
| D10 | Testing strategy | [~] | P1 | E1 | Low |
| D11 | Rollback/migration path | [x] | P2 | E1 | Medium |
| D12 | Cross-amendment consistency | [~] | P0 | E2 | High |
| D13 | Terminology consistent | [~] | P2 | E1 | Medium |
| D14 | No ambiguous language | [~] | P1 | E2 | Medium |
| D15 | No missing defaults | [~] | P1 | E1 | Medium |
| D16 | No unstated assumptions | [~] | P1 | E1 | Medium |
| D18 | No dead/superseded content unmarked | [~] | P1 | E2 | High |
| D19 | Actionable (implementable from doc alone) | [~] | P1 | E2 | Medium |

## P0 Findings

### F1. Start/stop sidecar lifecycle contradicts across amendments (D4, D12)

**Evidence:**
- Original (line 209): `start_sidecar.py`: "Check PID file → **kill stale process** if exists → start server.py as daemon"
- Original (line 210): `stop_sidecar.py`: "Read PID file → **send SIGTERM** → remove PID file"
- Amendment 3 Finding 3 (line 702): "start_sidecar.py must **NOT kill-and-restart** when sidecar is running — it must register and exit"
- Amendment 3 Finding 3 (line 711): "stop_sidecar.py **deregisters** the session instead of killing the process"

These are directly contradictory specifications with no supersession marker. The original says kill-restart; the amendment says register-only.

**Impact:** An implementer could build either lifecycle. The correct behavior (register, deregister, conditional shutdown) requires reading Amendment 3 at line 700+.

**Disconfirmation:** Could the original and amendment coexist? No — "kill stale process" and "must NOT kill-and-restart" are mutually exclusive behaviors for the same script.

**Recommendation:** Mark original startup/shutdown section (lines 207-211) as superseded. Add cross-reference to Amendment 3 Finding 3.

### F2. fail-open vs fail-closed philosophical contradiction (D4, D12)

**Evidence:**
- Original (line 222): "**Fail-open at every layer.**"
- Amendment 4 Finding 1 (line 860): "The sidecar's JSONL parser must be **fail-closed**, not fail-open. [...] This is a philosophical inversion from the original design's fail-open approach for the data layer"

Amendment 4 Finding 1 acknowledges the contradiction ("philosophical inversion") but the original statement at line 222 remains unqualified. The correct policy is a **two-layer model**: fail-open for injection (missing metrics is better than blocking prompts), fail-closed for data parsing (wrong metrics is worse than missing metrics). This is never stated as a unified policy.

**Impact:** An implementer reading "fail-open at every layer" might implement fail-open JSONL parsing, which Amendment 4 explicitly prohibits.

**Disconfirmation:** Could "fail-open at every layer" be read as compatible with fail-closed parsing? No — "every layer" is unambiguous.

**Recommendation:** Replace line 222 with the two-layer model. Or add a supersession note.

## P1 Findings — Stale Content (6 superseded sections)

### F3-F8. Superseded sections not marked (D12, D18)

The append-only amendment pattern has created 6 sections where original content contradicts later amendments:

| # | Section | Lines | Superseded by | What changed |
|---|---------|-------|---------------|--------------|
| F3 | Architecture diagram | 22-56 | Amendment 2 (509-552) | Data source: devtools → JSONL |
| F4 | Hook configuration | 99-151 | Amendment 3 F4 (718-738) | UserPromptSubmit: HTTP → command |
| F5 | "Why HTTP hooks" rationale | 58-64 | Amendment 3 F4 | v1 uses command hooks, not HTTP |
| F6 | Requirements | 14-15 | Amendments 2, 3 | Devtools optional, delta-gated |
| F7 | Sidecar State table | 200-205 | Amendments 2, 4 | TTL cache removed, devtools cache irrelevant |
| F8 | "Decisions Made" table | 310-321 | Amendments 2, 3, 4 | 5 of 7 entries superseded |

**Impact:** An implementer reading top-to-bottom gets a stale mental model for the first 300 lines.

**Recommendation:** Either (a) add strikethrough + cross-references to superseded sections, or (b) add a supersession index at the top of the document mapping original sections to their current-truth amendments.

## P1 Findings — Ambiguity and Gaps

### F9. Return/injection format described 4 different ways (D14, D12)

| Location | Format |
|----------|--------|
| Line 186 | `{ hookSpecificOutput: { hookEventName, additionalContext } }` |
| Line 541 | `{ additionalContext: "..." }` |
| Line 774 | `{ hookSpecificOutput: null }` or `{ hookSpecificOutput: { hookEventName, additionalContext } }` |
| Amendment 4 F5 | stdout → system-reminder (v1) |

The v1 format is stdout (Amendment 4), but the sidecar also needs a response format for `context_summary.py`'s HTTP request. What does the sidecar return to `context_summary.py`, and how does `context_summary.py` translate that to stdout?

### F10. context_summary.py stdout format never specified (D7)

Amendment 3 F4 establishes `context_summary.py` as the injection script for both UserPromptSubmit and compact hooks. Amendment 4 F5 says v1 uses stdout injection. But the actual stdout format is never specified:
- Does it print plain text? (`Context: 142k/200k tokens (71%) | ...`)
- Does it print JSON? (`{ "hookSpecificOutput": { ... } }`)
- Does it print just the summary line with no wrapper?

The hooks documentation says stdout "is added as context to the conversation" — but the format matters for how Claude sees it.

### F11. Heartbeat cadence not specific (D15)

- Normal heartbeat: "8-10 prompts" — is it 8? 9? 10? Random?
- Critical heartbeat: "3-4 prompts" — same ambiguity.

**Recommendation:** Pick exact values (e.g., 8 and 3) and note they can be tuned empirically.

### F12. +2% delta threshold direction ambiguous (D14)

Identified in Codex Review 3 as OPEN but not resolved in Amendment 4. At 150k/200k: 2% of window = 4k tokens, 2% of last value = 3k tokens. Different injection frequencies.

### F13. JSONL format assumptions unstated (D16)

The design assumes but never states:
1. JSONL uses newline-delimited JSON (one record per line)
2. Records are append-only (not modified in place)
3. `transcript_path` is always present in hook input
4. The file exists by the time UserPromptSubmit fires

### F14. First-prompt behavior undefined (D5)

On the first `UserPromptSubmit`, no assistant messages exist in the JSONL yet (only the user's prompt). The sidecar finds no matching records. What does `context_summary.py` output? Empty string? "Context: 0/200k (0%)"? Nothing?

### F15. Session ID bridge needs v1 update (D18)

Lines 189-197 describe parsing `transcript_path` to construct devtools API URLs. In v1, `transcript_path` is used to READ the JSONL file directly. The bridge section's purpose has changed.

### F16. Amendment 2 diagram cost step contradicts v1 scope (D12)

Line 534: "6. Estimate cost from token counts × model pricing." Amendments 3 and 4 both say v1 omits self-computed cost. The diagram step is stale.

### F17. context_summary.py scope not updated in plugin structure (D18)

Line 77 describes `context_summary.py` as "SessionStart(compact) — queries sidecar, prints JSON." Amendment 3 F4 (line 738) says it's "the sole injection script for both UserPromptSubmit and SessionStart(compact)." The plugin structure section wasn't updated.

### F18. "Why a config file (not auto-detection)" contradicts Amendment 2 (D12)

Lines 242-244 explain why auto-detection is impossible. Amendment 2 (lines 565-580) implements auto-detection. The original section is now misleading.

### F19. No testing strategy beyond fixture mention (D10)

Amendment 4 F10 says "fixture-based JSONL regression tests" but specifies no:
- Test framework (pytest?)
- Test categories (unit, integration, e2e?)
- How to obtain JSONL fixtures
- How to run tests

### F20. Registration/deregistration protocol unspecified (D7)

Amendment 3 F3 (line 711) says "Add `GET /sessions/register` and `GET /sessions/deregister` endpoints." But: What parameters? How does `start_sidecar.py` know the session_id? How does `stop_sidecar.py` know it? Is session_id passed via environment variable, hook input, or transcript_path parsing?

## P2 Findings

| # | Finding | Dimension |
|---|---------|-----------|
| F21 | No HTTP error response format for sidecar endpoints | D7 |
| F22 | Stdlib-only constraint buried in Amendment 1 F4, not in plugin structure | D18 |
| F23 | Dashboard skill v1 scope ("simplified JSONL-only or deferred") not specified | D7 |
| F24 | Port 7432 conflict with non-sidecar process: behavior unspecified | D5 |
| F25 | Sidecar request for unregistered session: behavior unspecified | D5 |
| F26 | No smoke test or v1 shippability criteria | D6 |
| F27 | "sidecar" vs "server" terminology used interchangeably | D13 |

## Adversarial Pass

All 9 lenses applied (Rigorous requirement):

| Lens | Objection | Response |
|------|-----------|----------|
| Assumption Hunting | Assumes JSONL format is stable enough for a production tool | Mitigated by fixture tests + fail-closed parsing (Amendment 4 F1). Residual risk: format could change silently between Claude Code versions. |
| Scale Stress | 100+ concurrent sessions on single sidecar | Acceptable — in-memory session registry + file seeks per request. Python async HTTP handles this. |
| Competing Perspectives (Security) | JSONL contains conversation content; sidecar reads it | Sidecar only reads `usage` fields, not message content. No exfiltration path. |
| Competing Perspectives (Perf) | Command hook latency (~150-300ms) on every prompt | Acceptable for v1. Upgrade path to HTTP hooks (1-5ms) in v1.1. |
| Kill the Design | What if the JSONL format changes? | Fixtures break on CI. Fail-closed means no injection, not wrong injection. |
| Pre-mortem | "6 months later, context-metrics failed because..." | ...the 200k→1M auto-detection gave wrong percentages for 100+ prompts and users lost trust. Mitigated by config override. Low residual risk. |
| Steelman Alternatives | Could devtools be modified upstream? | Yes, but external dependency. JSONL-primary is architecturally independent. Right call. |
| Challenge Framing | Is passive context awareness the right problem? | Yes — Claude makes better decisions about verbosity, tool use, and file reading when it knows context state. |
| Hidden Complexity | The append-only amendment pattern | THIS is the hidden complexity. Not in the design, but in the document. See F3-F8. |
| Motivated Reasoning | Is JSONL-primary anchored to the sunk-cost of investigating it? | No — the devtools investigation genuinely showed cumulative-not-occupancy. JSONL is the right data source. |

**Adversarial findings:** The strongest objection is F3-F8 (document readability). The design itself is sound. The document is the risk — an implementation plan writer working from stale original sections would produce an incorrect plan.

## Disconfirmation Log

| P0 Finding | Technique | Result |
|------------|-----------|--------|
| F1 (lifecycle contradiction) | Counterexample: could both behaviors coexist? | No — "kill stale" and "must NOT kill" are mutually exclusive |
| F1 | Alternative hypothesis: original means "kill stale from previous session crash" | Partial — but Amendment 3 explicitly says "must NOT kill-and-restart when sidecar is running," which covers the crash case too |
| F2 (fail-open/closed) | Counterexample: could "every layer" exclude data parsing? | No — "every" is unqualified |
| F2 | Alternative hypothesis: fail-open for the hook layer, which is what line 222 is in context of | Possible — line 222 follows the Error Handling table. But Amendment 4 F1 explicitly calls it a "philosophical inversion," confirming the contradiction |

## Exit Gate

| Criterion | Status |
|-----------|--------|
| Coverage complete | ✓ All dimensions checked (no `[ ]` or `[?]`) |
| Evidence requirements met | ✓ P0 dimensions at E2 |
| Disconfirmation attempted | ✓ 2 techniques per P0 |
| Assumptions resolved | ✓ 3 verified, 1 assumed (research doc) |
| Convergence reached | ✓ Pass 4: 3.6% < 10% |
| Adversarial pass complete | ✓ All 9 lenses applied |
