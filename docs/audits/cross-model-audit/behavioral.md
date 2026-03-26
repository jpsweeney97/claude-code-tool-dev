# Behavioral Review Findings

**Reviewer:** behavioral
**Date:** 2026-03-26
**Plugin:** `packages/plugins/cross-model/` v3.1.3

---

## Lens Coverage

All 8 Behavioral sentinel questions were run. Deep-lens analysis applied to: Correctness, Concurrency Safety, Failure Containment, Idempotency & Safety (4 lenses — cap honored).

**Zero-finding categories:**
- **Consistency Model:** No shared distributed state. Single-process in-memory state with checkpoint pass-through. Consistency model is implicit but appropriate for this archetype — single writer, no replication.
- **Performance Envelope:** No latency SLOs defined, which is appropriate for an internal developer tool. Subprocess timeouts (300s for consult, 600s for delegate) are the only performance bounds and are proportionate.
- **Scalability:** Single-developer tool — single process, single concurrent user. No scalability concerns in this context.
- **Backpressure & Load Shedding:** Not applicable at current scale. No queue, no fan-out.

---

## Findings

### [BH-1] Credential scan bypass for oversized prompts in delegation pipeline

- **priority:** P1
- **lens:** Correctness
- **decision_state:** explicit decision
- **anchor:** `scripts/codex_delegate.py:617-624`
- **problem:** When `ToolInputLimitExceeded` is raised (prompt > 256 KiB), the delegation pipeline logs a warning and continues without scanning the prompt for credentials. The comment cites "parity with the prior scan_text path" — but a bypass that was acceptable in a prior implementation is explicitly preserved here.
- **impact:** A prompt exceeding 256 KiB can reach the Codex subprocess with no credential scan. The governance rule (§4: fail-closed credential scanning on all outbound payloads) is violated for this input class. Since `codex delegate` prompts are agent-generated and can include code context, this threshold is reachable in practice.
- **recommendation:** Either (a) fail-closed on `ToolInputLimitExceeded` with a `CredentialBlockError` (safest, preserves governance guarantee), or (b) scan a truncated leading/trailing slice instead of skipping entirely. Document the chosen tradeoff explicitly in the consultation contract §4.
- **confidence:** high
- **provenance:** independent

---

### [BH-2] Concurrency race on used-bit in `consume_scout` under concurrent transport

- **priority:** P1
- **lens:** Concurrency Safety
- **decision_state:** explicit tradeoff
- **anchor:** `context-injection/context_injection/state.py:72-78`, `state.py:149-162`
- **problem:** The one-shot used-bit on `TurnRequestRecord` is set without an `asyncio.Lock`. The code comment at line 149-162 explicitly acknowledges this: "safe without asyncio.Lock under stdio transport with a single-flight client." FastMCP's `Server.run()` dispatches messages via `tg.start_soon()`, making concurrent dispatch structurally possible. The safety guarantee is entirely behavioral — it depends on the MCP client (Claude Code) not pipelining requests, which is not a protocol guarantee.
- **impact:** If a client sends two `execute_scout` calls for the same `turn_request_ref` concurrently (possible under SSE/WebSocket transports or if Claude Code ever pipelines), both calls could pass the `record.used` check before either sets it to `True`. This allows the same scout token to be consumed twice, violating the one-shot replay prevention guarantee (CI-SEC-3).
- **recommendation:** Add `asyncio.Lock` guarding the read-check-write on `record.used` in `consume_scout`. This is low-overhead (the lock is held for microseconds), and the comment already identifies exactly where it's needed. Alternatively, document the transport constraint as a deployment gate (e.g., "SSE transport requires lock addition before use").
- **confidence:** high
- **provenance:** independent

---

### [BH-3] `git_files` set is stale after server startup

- **priority:** P2
- **lens:** Correctness
- **decision_state:** default likely inherited
- **anchor:** `context-injection/context_injection/server.py:47-71`, `grep.py:206-213`
- **problem:** The set of git-tracked files (`git_files`) is loaded once at server startup via `git ls-files` and never refreshed. Files added to git tracking (via `git add`) or removed between startup and a scout call will be evaluated against stale state. The CI-SEC-2 invariant ("git ls-files policy gate blocks untracked files") is technically enforced, but against a snapshot that may not reflect the current repo state.
- **impact:** Two failure modes: (1) Newly untracked files (added to .gitignore after startup, or deleted from index) retain their tracked status — they pass the git gate they should fail. (2) Files newly tracked after startup are incorrectly blocked as "not tracked." Failure mode 1 is the security-relevant direction: a file that was tracked at startup but was subsequently removed from the index (e.g., `git rm --cached sensitive.key`) would still be scoutable. For a long-running server process in an active repo, this gap can grow.
- **recommendation:** Add an optional per-request refresh of `git_files` (e.g., re-run `git ls-files` before each Call 1) or document the startup-snapshot behavior explicitly as a known limitation in the contract. If refresh is too expensive on hot paths, a TTL-based cache (e.g., refresh every 60 seconds) would bound the staleness window.
- **confidence:** high
- **provenance:** independent

---

### [BH-4] `RgNotFoundError` mapped to `"timeout"` status in grep scout

- **priority:** P2
- **lens:** Correctness
- **decision_state:** explicit decision
- **anchor:** `context-injection/context_injection/execute.py:399-401`
- **problem:** When `ripgrep` is not found on PATH, `execute_grep` returns a `ScoutResultFailure` with `status="timeout"` and `error_message="ripgrep (rg) not found on PATH"`. The code comment acknowledges this is a semantic mismatch: "A missing binary is permanent, not transient." The agent's retry logic is cited as the justification for accepting this.
- **impact:** A misconfigured deployment (ripgrep not installed) is indistinguishable from a transient timeout to any monitoring, logging, or analytics layer that only reads `status`. The comment acknowledges a protocol change is deferred to v0c, but there is no tracking ticket or timeline. An operator encountering repeated `status=timeout` for grep scouts has no signal that the real failure is a missing binary.
- **recommendation:** Either add a `"dependency_error"` status to the protocol (the contract already has an extension point), or surface the distinction via `error_message` parsing. At minimum, add a `RgNotFoundError` test case to the integration test suite to prevent regression. Flag as tech debt in the contract migration notes.
- **confidence:** high
- **provenance:** independent

---

### [BH-5] `assert` in production code path — `grep.py` suppression branch

- **priority:** P2
- **lens:** Failure Containment
- **decision_state:** default likely inherited
- **anchor:** `context-injection/context_injection/grep.py:313`
- **problem:** `build_evidence_blocks` uses `assert isinstance(redact_outcome, RedactedText)` after checking for `SuppressedText`. In a Python environment where assertions are disabled (`python -O`), this assert is silently stripped — a `redact_outcome` of an unexpected type would proceed through the `redact_outcome.stats` attribute access and raise `AttributeError` rather than a controlled error.
- **impact:** If the `redact_text` function ever returns a third type (e.g., during a refactor or protocol extension), the failure mode under `-O` is an uncontrolled `AttributeError` rather than a clean `RuntimeError`. This affects all grep scouts in an optimized runtime. The impact is bounded to a single scout failure, but the error is harder to diagnose.
- **recommendation:** Replace with an explicit `if not isinstance(redact_outcome, RedactedText): raise RuntimeError(...)` check, consistent with the analogous check in `execute.py:302-303`.
- **confidence:** high
- **provenance:** independent

---

### [BH-6] `invalid_request` conflates security violations and operational restarts

- **priority:** P2
- **lens:** Failure Containment
- **decision_state:** explicit tradeoff
- **anchor:** `context-injection/context_injection/state.py:102-106`, `context-injection/context_injection/execute.py:515-522`
- **problem:** The `ScoutResultInvalid` response with `status: "invalid_request"` is returned for two structurally different conditions: (1) a genuine security event — invalid or replayed HMAC token (CI-SEC-3), and (2) an operational event — helper process restarted, in-memory state lost, all tokens invalidated. The agent protocol correctly treats both identically (proceed without evidence), but the response carries no discriminating field.
- **impact:** Any monitoring or alerting on `invalid_request` rates cannot distinguish attack attempts from deploys/restarts. A deployment that restarts the context-injection server mid-session generates the same signal as a token replay attack. This suppresses useful security signal during normal operations, or alternatively creates false-positive noise if alerting thresholds are set to catch attacks. The failure mode is documented (contract §Error Handling, HANDBOOK), but no structured distinction is provided.
- **recommendation:** Add an optional `failure_source` field (e.g., `"token_invalid"` vs `"state_lost"`) to `ScoutResultInvalid`. The helper can distinguish these: a missing `turn_request_ref` in the store after a verified healthy token would indicate state loss; a failed HMAC verify indicates tamper. Alternatively, surface the distinction via a structured `error_code` enum. This is a non-breaking additive change at the protocol level.
- **confidence:** high
- **provenance:** followup
- **prompted_by:** CT-6 flag from reliability-operational (finding RO-4)

---

## Cross-Cutting Tension Notes

**CT-1 (Performance ↔ Correctness):** The `git_files` startup-snapshot (BH-3) is a performance tradeoff — refreshing per-request would be correct but adds I/O on every Call 1. The current design inherits a default (load once) without explicitly bounding the staleness window. Message to `data`: this affects the correctness of the git-tracking gate, which is a data flow decision.

**CT-6 (Consistency ↔ Availability):** Context injection's checkpoint pass-through correctly resolves this: on server restart, Call 1 is recoverable (via checkpoint), and Call 2 fails gracefully with `invalid_request`. No blocking coordination required. No finding here — the design is conscious and correct.
