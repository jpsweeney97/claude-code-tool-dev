---
date: 2026-03-30
time: "01:54"
created_at: "2026-03-30T05:54:17Z"
session_id: dba37b64-3fcd-4b56-a126-f83f20e175c5
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-03-29_07-16_review-fix-merge-pr89-to-main.md
project: claude-code-tool-dev
branch: main
commit: b0f45f95
title: "T1-T2: live contract probe, read() parser fix, recovery audit parity"
type: handoff
files:
  - packages/plugins/codex-collaboration/server/runtime.py
  - packages/plugins/codex-collaboration/server/dialogue.py
  - packages/plugins/codex-collaboration/tests/test_runtime.py
  - packages/plugins/codex-collaboration/tests/test_dialogue.py
  - packages/plugins/codex-collaboration/tests/test_dialogue_integration.py
  - packages/plugins/codex-collaboration/tests/test_recovery_coordinator.py
  - packages/plugins/codex-collaboration/tests/test_control_plane.py
---

# Handoff: T1-T2: live contract probe, read() parser fix, recovery audit parity

## Goal

Resolve the post-R2 hardening tasks T1 (set the hardening bar) and T2 (decide on residual recovery debt) from the prior session's 4-task framework.

**Trigger:** Prior session squash-merged PR #89 (R2 dialogue foundation, 210 tests) to main at `f5fc5aab` and outlined a 4-task decision framework: T1 (hardening bar), T2 (recovery debt), T3 (context-assembly trust gaps), T4 (freeze next work package). This session picked up T1 first while recovery control flow was fresh.

**Stakes:** The R2 implementation had 210 tests but all used FakeRuntimeSession — no live runtime validation. The contract between the wrapper (`runtime.py`) and the actual Codex app-server had never been verified. A mismatch in response shapes would cause silent failures in recovery, sequence numbering, and dialogue history reading.

**Success criteria:** Verify the runtime boundary against live data, fix any mismatches found, close the recovery audit parity gap, and explicitly disposition all T2 debt items.

**Connection to project arc:** Spec compiled (`bf8e69e3`) → T1 (`f53cd6c8`) → R1 (`3490718a`) → Post-R1 amendments (`2ae76ed1`) → R2 implementation + fixes (PR #89) → R2 squash-merge (`f5fc5aab`) → **T1-T2 hardening (this session)** → T3 (context-assembly trust gaps) → T4 (freeze next work package).

## Session Narrative

### Loaded handoff and framed T1

Loaded the prior session's handoff (`2026-03-29_07-16_review-fix-merge-pr89-to-main.md`). The post-R2 next-steps framework had four decision tasks: T1 (hardening bar), T2 (recovery debt), T3 (context-assembly trust gaps), T4 (freeze next work package). User chose T1 first because it was closest to the recovery code just validated.

### Hypothesis framing and pushback

User presented three ranked hypotheses for T1:

1. **Most likely:** fake coverage is good enough, but a single live crash/restart drill validates the runtime boundary.
2. **Less likely:** current tests are sufficient; live drill would duplicate confidence.
3. **Riskier:** fake hides real integration mismatch; expect the drill to uncover at least one edge.

I explored the codebase to compare `FakeRuntimeSession` (test fixture at `test_control_plane.py:21-125`) against `AppServerRuntimeSession` (real wrapper at `runtime.py:12-191`). Found several divergences: `resume_thread` is a pure string transform in the fake vs. actual JSON-RPC in production, `read_thread` returns synthetic data vs. raw server response, no formal Protocol/ABC for the interface.

I agreed with H1's ranking but challenged the test plan: a full crash/restart drill is the most expensive validation, not the most informative first step. Recommended a phased approach — verify `read_thread` and `resume_thread` response shapes first (cheap, minutes), then decide on a drill based on the results.

### User identified a concrete contract violation

User pointed out something stronger than my exploration found: **the repo already contained protocol fixtures proving the mismatch**. `ThreadReadParams.json:4-6` documents `includeTurns` defaulting to `false`. `runtime.py:177` was sending only `{"threadId": thread_id}` — no `includeTurns: true`. The test at `test_runtime.py:75` encoded the wrong params as correct.

This reframed T1 from "build a drill" to "align and verify the runtime contract." The user scoped four steps: (1) fix the live wrapper, (2) fix the test, (3) probe a live server, (4) decide if a drill is still needed.

User: "The main thing you overlooked is stronger than 'the fake may differ from live': this repo already contains protocol fixtures showing that `thread/read` only includes turns when `includeTurns` is true, and the live wrapper currently does not send that flag."

### Commit 1: includeTurns fix (d65c8d54)

User manually patched `runtime.py:177-179` to send `{"threadId": thread_id, "includeTurns": True}` and updated `test_runtime.py:75-77` to assert the correct params. 210 tests passed. Committed as a standalone fix grounded in repo-local protocol fixtures.

### Live contract probe

User ran a focused live probe against a real Codex app-server (not a crash/restart drill — a targeted contract shape verification). Results:

- `thread/read` without `includeTurns` returned `turns: []` — confirmed the fixture contract.
- `thread/read` with `includeTurns: true` returned one completed turn — confirmed the fix.
- `thread/resume` returned a parseable `thread.id` — same ID as the original, not a new one.

Recovery-related parsing was safe (only uses `status` and `id` from each turn). But `read()` had a live-shape problem: real turns had keys `{error, id, items, status}` — no top-level `agentMessage` or `createdAt`. The agent message content lived in `turn.items[type=agentMessage].text`.

### Commit 2: read() parser fix (343535f6)

User implemented dual-path parsing: `_read_turn_agent_message()` checks legacy top-level `agentMessage` first, falls back to `items[type=agentMessage].text`. `_read_turn_timestamp()` follows the same pattern. Added a regression test using live-style nested `items` payload. 211 tests passed.

### Commit 3: resume_thread test alignment (a3978000)

`FakeRuntimeSession.resume_thread()` was returning `f"{thread_id}-resumed"` — live probe showed it returns the same ID. Updated the fake to return `thread_id` unchanged, added `resumed_threads` tracking list for test observability. Updated assertions in 5 test files to use `session.resumed_threads` instead of inferring resume from ID mutation. 211 tests passed.

### T2: recovery audit parity

Moved to T2. Two sub-items from the prior handoff:

**Item A: `_recover_turn_dispatch` audit gap.** When `_recover_turn_dispatch` confirms a turn, it writes TurnStore metadata but doesn't emit a `dialogue_turn` audit event. `_best_effort_repair_turn` does emit one. The normal `reply()` path always emits one. User and I agreed to close this now — it's a small, well-patterned change that eliminates a known gap.

User: "The timestamp objection is not a reason to park it. That exact temporal mismatch already exists in the inline repair path, and the contract explicitly describes audit as best-effort append for human reconstruction."

**Item B: Chronically unreachable unknown handles.** No TTL or escalation for handles stuck in `unknown` status. User and I agreed to explicitly park this — it's architectural policy debt, not a correctness gap. The retry is idempotent, the handle namespace is small, and the spec frames this as future work.

User: "This is not the same class of problem. The unknown-handle retry loop is policy debt, not a correctness gap."

### Commit 4: audit parity fix (b0f45f95)

User implemented the audit parity fix: `_recover_turn_dispatch` now keeps the `completed_turns` list (instead of collapsing to `completed_count`), recovers `turn_id` from the confirmed turn index, and emits `dialogue_turn` when `turn_id` and `entry.runtime_id` are available. Added a regression test. 212 tests passed.

## Decisions

### Reframe T1 as "align and verify the runtime contract" instead of "crash/restart drill"

**Choice:** Start with contract alignment (fix `includeTurns`, fix parser), then probe live, then decide on a drill.

**Driver:** User identified a concrete contract violation already documented in repo-local protocol fixtures — `ThreadReadParams.json:4-6` shows `includeTurns` defaults to `false`, but the wrapper didn't send the flag. This made the mismatch a known bug, not a hypothesis to test via drill.

**Rejected:**
- **Crash/restart drill first** — most expensive validation, not the most informative first step. A shape mismatch would cause the drill to fail for parsing reasons, not recovery reasons, and you'd debug the wrong thing.
- **Code inspection only** — user correctly noted that wrapper thinness doesn't prove response-shape fidelity. The shapes come from the server, not the wrapper.

**Trade-offs accepted:** No crash/restart drill was done. The recovery sequencing is validated only by unit tests (212 passing), not by live recovery. The controller logic is deterministic and journal-based, so the unit test coverage is strong, but live restart behavior of `thread/resume` is still assumed-correct.

**Confidence:** High (E2) — live probe confirmed the documented shapes; unit tests cover the controller logic exhaustively.

**Reversibility:** High — all changes are small, test-covered patches.

**Change trigger:** If a live crash/restart reveals behavioral differences in `thread/resume` (e.g., server returns different thread state after restart), the recovery code may need adjustment. But this is now an integration concern, not a contract concern.

### Always send includeTurns: true (not parameterized)

**Choice:** `read_thread` in the wrapper always sends `{"threadId": thread_id, "includeTurns": True}`. No parameter to opt out.

**Driver:** 5 of 6 call sites in the controller parse turns. The one that doesn't (`_recover_thread_creation` at `dialogue.py:442`) discards the response entirely. Adding a parameter for one call site that doesn't care is unnecessary complexity.

**Rejected:**
- **Parameterized `include_turns: bool = True`** — adds interface complexity for a code path that doesn't use the response.
- **Two methods (`read_thread` / `read_thread_with_turns`)** — over-engineering for the same reason.

**Trade-offs accepted:** Slightly larger response when turns aren't needed (one call site). Negligible cost.

**Confidence:** High (E2) — all 6 call sites inspected; only one doesn't parse turns, and it discards the response.

**Reversibility:** High — adding the parameter later is a non-breaking change.

**Change trigger:** If a future call site needs `read_thread` without turns for performance reasons (very large turn history), parameterize then.

### Dual-path parser for read() (legacy + live shapes)

**Choice:** `_read_turn_agent_message` checks legacy top-level `agentMessage` first, falls back to `items[type=agentMessage].text`. Same pattern for `_read_turn_timestamp`.

**Driver:** Live probe showed turns have `{error, id, items, status}` with agent message in nested items, while the fake returns `{id, status, agentMessage, createdAt}`. Supporting both shapes avoids breaking existing tests while handling live data correctly.

**Rejected:**
- **Update the fake to match live shape** — would require rewriting all existing tests that use the legacy shape. The dual-path approach is cheaper and the legacy shape may still appear in older server versions.
- **Only support live shape** — breaks existing test infrastructure for no correctness gain.

**Trade-offs accepted:** Two code paths to maintain. Mitigated by extracting into static methods with clear fallback chains.

**Confidence:** High (E2) — live probe confirmed the live shape; existing tests confirm the legacy shape; both paths tested.

**Reversibility:** High — if the fake is later updated to match live shape, the legacy path becomes dead code and can be removed.

**Change trigger:** If a third response shape appears, the fallback chain grows. Consider a response-shape normalizer at that point.

### Close audit parity now, park unreachable handles

**Choice:** Fix the `_recover_turn_dispatch` audit gap immediately. Park chronically unreachable `unknown` handles as explicit debt.

**Driver:** Audit parity is a small, well-patterned change — `_best_effort_repair_turn` already demonstrates the exact pattern. The spec says audit is for "human reconstruction and diagnostics" (contracts.md:166). Unreachable handles are architectural policy debt — needs TTL design, eviction policy, and usage pattern data that doesn't exist yet.

**Rejected:**
- **Park both** — leaves a known inconsistency in the audit trail when the fix is trivial and the pattern exists.
- **Fix both** — unreachable handle eviction is a scope expansion beyond the "close the gap while the code is warm" framing.
- **Fix audit with timestamp caveat** — the same temporal mismatch already exists in `_best_effort_repair_turn` (recovery-time vs. dispatch-time). Not a reason to skip.

**Trade-offs accepted:** Unreachable handles remain as documented debt. The retry is idempotent and the spec acknowledges this at contracts.md:156.

**Confidence:** High (E2) — audit fix mirrors proven pattern; parking decision grounded in spec language and architectural analysis.

**Reversibility:** High — audit fix is additive (new audit events, no changed events). Parking is reversible by design.

**Change trigger:** For audit: none — this corrects a gap, not a preference. For unreachable handles: if production usage shows significant handle accumulation or startup slowdown from retries.

## Changes

### `packages/plugins/codex-collaboration/server/runtime.py` — Send includeTurns on thread/read

**Purpose:** Fix contract mismatch where the wrapper didn't request turn history from `thread/read`.

**Change:** `read_thread()` at line 177-180 now sends `{"threadId": thread_id, "includeTurns": True}` instead of `{"threadId": thread_id}`. One-line semantic change.

**Key detail:** `ThreadReadParams.json:4-6` documents `includeTurns` defaulting to `false`. Without the flag, the server returns `turns: []` — confirmed by live probe.

### `packages/plugins/codex-collaboration/server/dialogue.py` — Dual-path parser + audit parity

**Purpose:** (1) Support live turn shapes in `read()`, (2) emit `dialogue_turn` audit on confirmed `turn_dispatch` recovery.

**Changes:**
- `read()` at line 665 now calls `self._read_turn_agent_message(raw_turn)` instead of `raw_turn.get("agentMessage", "")`.
- `read()` at line 690 now calls `self._read_turn_timestamp(raw_turn)` instead of `str(raw_turn.get("createdAt", ""))`.
- New `_read_turn_agent_message()` at lines 703-719: legacy `agentMessage` → `items[type=agentMessage].text` → `""`.
- New `_read_turn_timestamp()` at lines 722-736: legacy `createdAt` → `items[].createdAt` → `""`.
- `_recover_turn_dispatch()` at lines 502-560: now keeps `completed_turns` list (not just `completed_count`), recovers `turn_id` from `completed_turns[turn_sequence - 1]`, emits `dialogue_turn` audit when both `turn_id` and `entry.runtime_id` are present.

### `packages/plugins/codex-collaboration/tests/test_runtime.py` — Corrected params assertion + resume rename

**Purpose:** Assert the correct JSON-RPC params for `thread/read` and remove "new ID" assumption from `resume_thread`.

**Changes:**
- `test_read_thread_returns_turns` at line 75-77: asserts `("thread/read", {"threadId": "thr-1", "includeTurns": True})`.
- `test_resume_thread_returns_thread_id_from_response` (renamed from `test_resume_thread_returns_new_thread_id`): stub response uses same ID (`"thr-1"`), variable renamed to `resumed_thread_id`.

### `packages/plugins/codex-collaboration/tests/test_control_plane.py` — FakeRuntimeSession alignment

**Purpose:** Align fake with live `resume_thread` behavior (same ID returned).

**Changes:**
- Added `self.resumed_threads: list[str] = []` at line 49 for tracking.
- `resume_thread()` at lines 123-124 now appends to `resumed_threads` and returns `thread_id` unchanged (was `f"{thread_id}-resumed"`).

### `packages/plugins/codex-collaboration/tests/test_dialogue.py` — Live-shape regression + audit regression

**Purpose:** Cover the dual-path parser and audit parity fix.

**Changes:**
- `test_read_extracts_position_from_nested_agent_message_item` at line 591: uses live-style `items` payload, asserts position extracted from `agentMessage.text`, timestamp empty.
- `test_recover_dispatched_turn_dispatch_confirmed_emits_audit` at line 534: writes `turn_dispatch dispatched` entry with `runtime_id`, calls `recover_pending_operations`, asserts audit event with correct `collaboration_id`, `runtime_id`, `turn_id`, `context_size`.
- Updated recovery test at line 334: asserts `codex_thread_id == "thr-orphan"` and `session.resumed_threads == ["thr-orphan"]`.

### `packages/plugins/codex-collaboration/tests/test_dialogue_integration.py` — Resume ID alignment

**Purpose:** Remove dependence on synthetic `-resumed` suffix.

**Changes:**
- Line 152: now captures `session` from `_full_stack`.
- Line 188-189: asserts `codex_thread_id == "thr-orphan"` and `session.resumed_threads == ["thr-orphan"]`.

### `packages/plugins/codex-collaboration/tests/test_recovery_coordinator.py` — Resume ID alignment

**Purpose:** Remove dependence on synthetic `-resumed` suffix across 6 recovery tests.

**Changes:** All tests updated to assert `codex_thread_id == "thr-start"` (not `"thr-start-resumed"`) and verify resume via `session.resumed_threads`. `test_journal_reconciled_before_reattach` uses `.count("thr-start") == 2` for the two-handle case.

**Note:** `test_does_not_double_resume_handles_from_phase_1` was NOT changed — it already uses its own `tracking_resume` wrapper (lines 202-209) rather than relying on the thread ID suffix. Could be simplified to use `session.resumed_threads` in a future cleanup.

## Codebase Knowledge

### Key Code Locations (Verified This Session)

| What | Location | Why verified |
|------|----------|-------------|
| `read_thread()` wrapper | `runtime.py:175-180` | Fixed to send `includeTurns: True` |
| `ThreadReadParams.json` | `tests/fixtures/codex-app-server/0.117.0/v2/ThreadReadParams.json:4-6` | Documents `includeTurns` defaulting to `false` |
| `ThreadReadResponse.json` turns doc | `tests/fixtures/codex-app-server/0.117.0/v2/ThreadReadResponse.json:855-861` | Documents when `turns` is populated |
| `_read_turn_agent_message()` | `dialogue.py:703-719` | New: dual-path agent message extraction |
| `_read_turn_timestamp()` | `dialogue.py:722-736` | New: dual-path timestamp extraction |
| `_recover_turn_dispatch()` | `dialogue.py:479-560` | Updated: audit event emission on confirmed recovery |
| `_best_effort_repair_turn()` | `dialogue.py:559-631` | Pattern source for audit event in recovery |
| `FakeRuntimeSession` | `test_control_plane.py:21-125` | Updated: `resumed_threads` tracking, same-ID return |
| `_recovery_stack` | `test_recovery_coordinator.py:18-48` | Unchanged but frequently used in updated tests |
| Phase 2 recovery loop | `dialogue.py:350-389` | Calls `read_thread` and `resume_thread` — affected by `includeTurns` fix |

### Architecture: read_thread Response Shapes

```
Legacy shape (FakeRuntimeSession default):
  {"thread": {"id": "...", "turns": [{"id": "t1", "status": "completed", "agentMessage": "...", "createdAt": "..."}]}}

Live shape (Codex app-server 0.117.0):
  {"thread": {"id": "...", "turns": [{"id": "t1", "status": "completed", "error": null, "items": [
    {"id": "item-1", "type": "userMessage", "content": [{"type": "text", "text": "..."}]},
    {"id": "item-2", "type": "agentMessage", "text": "{\"position\":\"...\"}"}
  ]}]}}

Key differences:
  - Agent message: top-level `agentMessage` (legacy) vs `items[type=agentMessage].text` (live)
  - Timestamp: top-level `createdAt` (legacy) vs not present in live probe
  - Additional fields: live has `error` and `items`; legacy has `agentMessage` and `createdAt`
```

### Architecture: Audit Event Emission Paths (Now Complete)

| Path | Emits `dialogue_turn`? | Conditions | Location |
|------|------------------------|------------|----------|
| Normal `reply()` | Always | — | `dialogue.py:278-290` |
| `_best_effort_repair_turn()` | When `turn_id` recoverable AND `runtime_id` available | Best-effort, exception-swallowed | `dialogue.py:619-631` |
| `_recover_turn_dispatch()` | When `turn_id` recoverable AND `entry.runtime_id` available | After journal resolution | `dialogue.py:549-560` |

### Protocol Fixture Layout

Versioned protocol fixtures at `tests/fixtures/codex-app-server/0.117.0/v2/`:

| File | Purpose | Key detail for this session |
|------|---------|---------------------------|
| `ThreadReadParams.json` | Params schema for `thread/read` | `includeTurns` defaults to `false` |
| `ThreadReadResponse.json` | Response schema for `thread/read` | `turns` only populated when `includeTurns: true` or on `thread/resume`, `thread/fork`, `thread/rollback` |

### Test Observability Patterns

| Pattern | Used by | How it works |
|---------|---------|-------------|
| `session.resumed_threads` | Most recovery tests | List of thread IDs passed to `resume_thread()`. Verify resume happened without depending on return value. |
| `tracking_resume` wrapper | `test_does_not_double_resume_handles_from_phase_1` | Monkey-patches `resume_thread` to count calls. Pre-dates `resumed_threads` tracking. |
| `session.read_thread_response` override | Parser and recovery tests | Overrides synthetic turn generation with specific response shapes. |

## Context

### Mental Model

This session's core problem was "fake fidelity" — the gap between what the test infrastructure assumes about the runtime and what the runtime actually does. Three distinct mismatches were found and fixed:

1. **Contract mismatch (includeTurns):** The wrapper asked for less data than the controller needed. Found via repo-local protocol fixtures before touching a live server.
2. **Shape mismatch (turn items):** The controller parsed fields that exist in the fake but not in live responses. Found via live probe.
3. **Behavioral mismatch (resume_thread ID):** The fake assumed resume always returns a new ID. Live probe showed it returns the same ID. The controller handles both correctly, but tests asserted fake-specific behavior.

The pattern: each mismatch was discovered, fixed, and tested independently. The user drove the sequencing: contract correction first (grounded in fixtures), then live probe (validates the fix), then parser fix (addresses what the probe found), then test alignment (removes fake-specific assumptions).

### Project State

| Milestone | Status | Commit/PR |
|-----------|--------|-----------|
| Spec compiled and merged | Complete | `bf8e69e3` |
| T1: Compatibility baseline | Complete | `f53cd6c8` (PR #87) |
| R1: First runtime milestone | Complete | `3490718a` on main |
| Post-R1 spec amendments | Complete | `078e5a39`..`2ae76ed1` on main |
| R2: Dialogue foundation | Complete | `f5fc5aab` on main (PR #89, squash-merged) |
| **T1: Live contract probe** | **Complete** | `d65c8d54`, `343535f6`, `a3978000` |
| **T2 Item A: Audit parity** | **Complete** | `b0f45f95` |
| **T2 Item B: Unreachable handles** | **Parked** | Architectural debt, spec acknowledges |
| T3: Context-assembly trust gaps | **Next** | Not started |
| T4: Freeze next work package | Pending T3 | Not started |

212 tests passing on main. Branch `feature/codex-collaboration-r2-dialogue` still exists (tagged at `r2-dialogue-branch-tip` → `d2d0df56`).

## Learnings

### Protocol fixtures are the first place to check for contract mismatches

**Mechanism:** Versioned fixtures at `tests/fixtures/codex-app-server/<version>/v2/` document the server's JSON-RPC param schemas with defaults. If production code omits a parameter that defaults to a restrictive value (like `includeTurns: false`), the fixture documents the mismatch before any live testing.

**Evidence:** `ThreadReadParams.json:4-6` showed `includeTurns` defaults to `false`. The wrapper at `runtime.py:177` didn't send it. The test at `test_runtime.py:75` encoded the wrong params as correct. All three artifacts were in the repo — no live server needed to find the bug.

**Implication:** When adding or modifying runtime wrapper methods, cross-check params against the versioned fixture schemas. The fixture is the contract; the wrapper must satisfy it.

### Tests can encode the wrong expectation as correct

**Mechanism:** `test_read_thread_returns_turns` verified the wrapper could *parse* a response with turns, but asserted params (`{"threadId": "thr-1"}`) that would *never produce* turns against a real server. The test name promised something the test didn't verify.

**Evidence:** Line 75 of the original test: `assert client.requests[0] == ("thread/read", {"threadId": "thr-1"})`. This passed because the stub returned turns regardless of params, but the real server respects the `includeTurns` flag.

**Implication:** Runtime wrapper tests should assert both the request params sent to the server AND the response parsing. Asserting only parsing creates a false sense of coverage.

### Live resume_thread returns the same thread ID

**Mechanism:** `thread/resume` on the live Codex app-server (0.117.0) returns the same `thread.id` as the input, not a new one. The controller persists whatever string it gets back, so this doesn't affect correctness.

**Evidence:** Live probe: `thread/resume(thread_id="thr-X")` → response `thread.id == "thr-X"`. FakeRuntimeSession was returning `f"{thread_id}-resumed"` — a synthetic convention not grounded in live behavior.

**Implication:** Tests should not assert that `resume_thread` changes the ID. Use `session.resumed_threads` to verify resume was called. The `test_does_not_double_resume_handles_from_phase_1` test's hand-rolled tracking wrapper (`tracking_resume` at `test_recovery_coordinator.py:202-209`) is now redundant — `session.resumed_threads` provides the same observability built into the fake.

### Live turn shapes use nested items, not top-level fields

**Mechanism:** Live `thread/read` returns turns with `{error, id, items, status}`. Agent message text is at `items[type=agentMessage].text`. No top-level `agentMessage` or `createdAt` on the turn object. Timestamp was absent from both turn and items in the live probe.

**Evidence:** Live probe against Codex app-server 0.117.0. The `ThreadReadResponse.json` fixture schema lists `turns` as an array of Turn objects — the Turn schema includes `items` but the controller was reading `agentMessage` and `createdAt` directly off the turn.

**Implication:** Any new code that parses turn data from `read_thread` should use `_read_turn_agent_message()` and `_read_turn_timestamp()` rather than direct field access. The dual-path helpers handle both legacy and live shapes.

## Next Steps

### T3: Decide on context-assembly trust gaps

**Dependencies:** None — parallel with T2 (now closed).

**What to read first:** [T-20260327-01](docs/tickets/2026-03-27-r1-carry-forward-debt.md) — the R1 carry-forward debt ticket tracking redaction coverage and non-UTF-8 handling gaps.

**Approach:** Decide whether these trust-boundary gaps should be promoted ahead of new feature work. These affect the existing production consult path, not just the new dialogue path. Key areas: redaction coverage (what gets redacted and what doesn't), non-UTF-8 content handling (binary files in context assembly).

**Potential obstacles:** The trust gaps may be broader than the ticket captures. A fresh read of the context assembly code may surface additional issues.

### T4: Freeze the next work package

**Dependencies:** T3.

**What to read first:** Outcomes of T3.

**Approach:** Select one next work item, agree on scope boundary, create the starting artifact for the next session.

### Feature branch cleanup (low priority)

`feature/codex-collaboration-r2-dialogue` still exists on remote. The branch tip is tagged as `r2-dialogue-branch-tip` → `d2d0df56`. Can be deleted once confirmed the tag is pushed (it was pushed in the prior session).

### Optional: simplify test_does_not_double_resume_handles_from_phase_1

The hand-rolled `tracking_resume` wrapper at `test_recovery_coordinator.py:202-209` is now redundant — `session.resumed_threads` provides the same observability. Could be simplified to use the built-in tracking in a future cleanup pass. Not urgent — the test is correct as-is.

## In Progress

Clean stopping point. All four commits merged to main. T1 and T2 Item A are closed. T2 Item B is explicitly parked. No work in flight.

**User's next step:** T3 (context-assembly trust gaps), then T4 (freeze next work package).

## Open Questions

### MCP consumer retry behavior for CommittedTurnParseError (inherited)

The error message says "Blind retry will create a duplicate follow-up turn." But Claude (the MCP consumer) has no programmatic mechanism to distinguish this error from a generic tool failure. Will it retry? Task 6's test verifies the guidance is in the error text, but wire-level retry prevention is out of scope.

### Chronically unreachable unknown handles (parked as T2 Item B)

Startup recovery will retry `unknown` handles every restart. If the underlying infrastructure is permanently broken, the handle never recovers and never gets evicted. Explicitly parked — needs TTL design and usage pattern data. Spec acknowledges at contracts.md:156.

### Feature branch cleanup timing

`feature/codex-collaboration-r2-dialogue` exists on remote with tag `r2-dialogue-branch-tip`. Can be deleted anytime. No urgency.

### Live timestamp availability

Live `thread/read` and `thread/resume` did not include `createdAt` on turns or items. `_read_turn_timestamp` currently returns `""` on live data. If the server adds timestamps in a future version, the dual-path parser will pick them up automatically. No action needed now.

## Risks

### No live crash/restart drill performed

The contract probe confirmed response shapes match, but live crash/restart sequencing (process kill → runtime restart → recovery → reply) was not tested. The controller logic is deterministic and journal-based (212 unit tests), and the response shapes are now verified against live data, so the residual risk is integration timing — e.g., does `thread/resume` behave the same after a process restart as after a fresh start? This is low-risk given the controller's design but remains unverified.

### Dual-path parser maintenance

`_read_turn_agent_message` and `_read_turn_timestamp` support two response shapes. If a third shape appears (future server version), the fallback chain grows. Consider a response normalizer if this happens.

### T2 Item B remains unaddressed

Unreachable `unknown` handles retry every startup. Low risk today (small handle namespace, fast retry, idempotent), but could become noticeable if handle count grows or startup time matters.

## References

| Resource | Location | Purpose |
|----------|----------|---------|
| Prior handoff (resumed from) | `docs/handoffs/archive/2026-03-29_07-16_review-fix-merge-pr89-to-main.md` | Full R2 merge context and post-R2 framework |
| ThreadReadParams fixture | `tests/fixtures/codex-app-server/0.117.0/v2/ThreadReadParams.json` | Documents `includeTurns` default |
| ThreadReadResponse fixture | `tests/fixtures/codex-app-server/0.117.0/v2/ThreadReadResponse.json` | Documents when `turns` is populated |
| Crash Recovery Contract | `docs/superpowers/specs/codex-collaboration/contracts.md:141-156` | Option C eligibility, unknown handle provenance |
| R1 carry-forward debt | `docs/tickets/2026-03-27-r1-carry-forward-debt.md` | T3 input: context-assembly trust gaps |
| Modular spec | `docs/superpowers/specs/codex-collaboration/` | Normative v1 contract (9 files) |
| R2 branch tag | `r2-dialogue-branch-tip` → `d2d0df56` | Per-task commit archaeology |

## Gotchas

### includeTurns defaults to false on thread/read

`ThreadReadParams.json:4-6` documents `includeTurns` with `"default": false`. If you add another `thread/read` call site, it will silently return empty turns unless `includeTurns: True` is sent. The wrapper now always sends it, but if someone bypasses the wrapper or adds a new RPC method, remember the default.

### Live turns use nested items, not top-level fields

Live `thread/read` returns `{error, id, items, status}` per turn. Agent message is in `items[type=agentMessage].text`, not top-level `agentMessage`. `createdAt` was absent in the 0.117.0 probe. Use `_read_turn_agent_message()` and `_read_turn_timestamp()` — don't access turn fields directly.

### resume_thread returns the same thread ID

Live `thread/resume` does not generate a new thread ID. The controller handles this correctly (persists whatever it gets), but if you write tests that assert the ID changed, they'll fail against a live server. Use `session.resumed_threads` for observability instead.

### FakeRuntimeSession.read_thread default vs override

The default synthetic `read_thread` response generates turns from `completed_turn_count` with legacy shape (`agentMessage`, `createdAt`). Override via `session.read_thread_response` to test live shapes. The override is global — both phase 1 and phase 2 see the same response. For tests that need per-call responses, the current fake doesn't support it.

### test_does_not_double_resume has redundant tracking

`test_recovery_coordinator.py:202-209` uses a hand-rolled `tracking_resume` wrapper. `session.resumed_threads` now provides the same tracking built into the fake. The hand-rolled version works but is redundant. If you modify this test, consider simplifying to use the built-in tracking.

## Conversation Highlights

**User's contract-violation finding:**
User: "The main thing you overlooked is stronger than 'the fake may differ from live': this repo already contains protocol fixtures showing that `thread/read` only includes turns when `includeTurns` is true, and the live wrapper currently does not send that flag."
— This reframed T1 from hypothesis-testing to contract-fixing. The fixtures were the evidence; the live probe was confirmation.

**Commit boundary discipline:**
User: "It's an independently justified fix grounded in repo-local protocol fixtures, and it already has a clean verification story. The live probe is a different kind of work... If the probe finds something, it should land as a second change, not get muddled into this one."
— Each commit addresses one concern. Probe findings land separately from contract fixes.

**Production-first fix ordering:**
User: "The one place I'd push back hardest is 'if shapes don't match, fix the fake first.' No. Fix the production wrapper and parser contract first, then make the fake follow that contract. The fake is a mirror, not the source of truth."
— Clear principle: production code is the source of truth, fake mirrors it.

**Debt classification:**
User: "This is not the same class of problem. The unknown-handle retry loop is policy debt, not a correctness gap. The current contract already frames future unknown producers as needing stronger provenance."
— Distinguishes between correctness debt (fix now) and policy debt (park explicitly).

**T1-T2 sequencing rationale:**
User: "The most sensible move now is to decide the remaining recovery-specific debt while the control flow is still fresh."
— Context locality drives task ordering. Recovery-adjacent decisions belong together.

## User Preferences

**Commit scope discipline:** Each commit is independently justified with its own verification story. Don't bundle probe findings into a contract fix. User: "If the probe finds something, it should land as a second change, not get muddled into this one."

**Production-first ordering:** Fix production code before updating fakes/tests. User: "Fix the production wrapper and parser contract first, then make the fake follow that contract. The fake is a mirror, not the source of truth."

**Hypothesis-driven exploration:** Present ranked hypotheses with evidence needed and tests to run. User frames decisions the same way and expects the same rigor in pushback.

**Grounded pushback:** User: "I want you to challenge me, but don't be contrarian just for the sake of it — defend every pushback with grounded evidence and clear reasoning." Push back with file:line references and specific reasoning, not general concerns.

**Debt classification:** Distinguish correctness debt (fix now while context is warm) from policy debt (park explicitly, document why). User: "A counter without policy is just observability garnish."

**Context locality in sequencing:** Work on related decisions together while control flow is fresh. User chose T2 after T1 because "the most sensible move now is to decide the remaining recovery-specific debt while the control flow is still fresh."
