# Reliability + Operational Findings

Reviewer: reliability-operational
System: `packages/plugins/cross-model/` — cross-model consultation plugin v3.1.3
Stakes: Medium (internal developer tool; egresses code/prompts to external API; fail-closed safety controls)

---

## Summary

4 findings. Primary concerns are in **Operational** (configuration clarity, observability, resource proportionality). Reliability concerns are minor given the system's explicit best-effort positioning — the design decisions are conscious and proportionate for a single-developer tool.

| Finding | Priority | Lens | Decision State |
|---------|----------|------|----------------|
| RO-1 | P1 | Configuration Clarity | underspecified |
| RO-2 | P2 | Resource Proportionality | default likely inherited |
| RO-3 | P2 | Observability | explicit tradeoff |
| RO-4 | P2 | Recoverability | explicit decision |

---

### [RO-1] REPO_ROOT silently misconfigures the entire dialogue subsystem

- **priority:** P1
- **lens:** Configuration Clarity
- **decision_state:** underspecified
- **anchor:** `.mcp.json:16`, `context-injection/context_injection/server.py:47`
- **problem:** The `context-injection` MCP server captures `REPO_ROOT=${PWD}` at startup time. If Claude Code is launched from a directory other than the target repository (e.g., from `~`, `/tmp`, or a parent monorepo), the server silently operates with the wrong git root for the entire session. The fail-closed git_files behavior (`_load_git_files` returns empty set on error) only fires on a git command failure — not on a directory that is a valid git repo but is the wrong one.
- **impact:** All evidence gathering in `/dialogue` sessions will either return no results (empty git_files for a non-repo `PWD`) or gather evidence from the wrong codebase (if `PWD` is a different valid git repo). The failure is silent: `codex-dialogue` gets `scout_available=false` or receives irrelevant evidence, and the session continues without surfacing the root cause. The operator has no signal that the misconfiguration occurred.
- **recommendation:** Add a startup warning (logged to stderr) when `REPO_ROOT` is the default `${PWD}` and the resolved path differs from what is visible in the session context, or at minimum document in the HANDBOOK fast health check (step 3) that the working directory check is critical for `/dialogue` correctness — not just a nice-to-have. Consider emitting `REPO_ROOT` value as a startup log line so it's visible in Claude Code's MCP server output.
- **confidence:** high
- **provenance:** independent

---

### [RO-2] Codex version check runs on every MCP call, adding subprocess overhead to each turn

- **priority:** P2
- **lens:** Resource Proportionality
- **decision_state:** default likely inherited
- **anchor:** `scripts/codex_consult.py:138-162` (`_check_codex_version`)
- **problem:** `_check_codex_version()` spawns a `codex --version` subprocess inside every `consult()` call — including every `codex-reply` turn in a multi-turn dialogue. A `/dialogue` session with an 8-turn budget triggers 9 or more version checks (initial call plus replies), each with a 10-second timeout. This was likely added as a correctness check and never reviewed as a per-call cost.
- **impact:** For the typical `/dialogue` budget (8 turns), this adds 8+ sequential subprocesses per session. On a fast machine the `codex --version` call is nearly instant, but it adds latency and a potential stall point (timeout=10s each) on every turn. More significantly, the retry/continuation logic in the HANDBOOK says "do not auto-retry after timeout" — if `_check_codex_version` stalls, it can appear as a mysterious pre-dispatch hang that the operator would need to debug.
- **recommendation:** Cache the version check result for the process lifetime (module-level flag after first successful check), or move it to a startup gate rather than a per-call check. The risk of a Codex CLI downgrade mid-session is negligible compared to the per-call overhead. Alternatively, document this as a known cost so operators don't mistake the pre-dispatch latency for a network issue.
- **confidence:** high
- **provenance:** independent

---

### [RO-3] JSONL event log has no size management — unbounded growth with no documented lifecycle

- **priority:** P2
- **lens:** Observability
- **decision_state:** explicit tradeoff
- **anchor:** `scripts/event_log.py:8-11` (design note), `~/.claude/.codex-events.jsonl`
- **problem:** The event log at `~/.claude/.codex-events.jsonl` grows without bound. There is no rotation, archival, size cap, or documented retention policy. The `event_log.py` module comment explicitly acknowledges this is best-effort and proportionate for single-developer use, but does not address the lifecycle question. The `/consultation-stats` skill reads the entire file on every invocation with a time-window filter applied in Python (not at read time).
- **impact:** Over time, the JSONL file will grow large enough that `/consultation-stats` reads slow down measurably. More practically, operators have no answer to "how do I clean this up" — if the file is manually truncated or deleted, `read_events.py` may behave unexpectedly on partial lines at the beginning. The HANDBOOK's "stats: malformed log lines" recovery path covers corruption but not size-based degradation.
- **recommendation:** Document the expected file growth rate (approximate bytes per consultation event), add a one-liner to the HANDBOOK for how to safely truncate or archive the file (e.g., `cp ~/.claude/.codex-events.jsonl ~/archive.jsonl && echo "" > ~/.claude/.codex-events.jsonl`), and note the effect on historical stats. This is a documentation gap, not a code change.
- **confidence:** high
- **provenance:** independent

---

### [RO-4] Context-injection HMAC key regeneration on restart invalidates mid-dialogue scouts with no operator signal

- **priority:** P2
- **lens:** Recoverability
- **decision_state:** explicit decision
- **anchor:** `context-injection/context_injection/state.py:102-106` (`AppContext.create`), `HANDBOOK.md:650-651`
- **problem:** The `AppContext` generates a fresh 32-byte HMAC key on every process start. A server restart mid-dialogue (crash, OOM, Claude Code restart) means all in-flight HMAC tokens are immediately invalid. The HANDBOOK documents the recovery path ("scout request can fail with `invalid_request`; agent continues without that scout"), but the failure signal to the agent is a generic `ScoutResultInvalid` response — indistinguishable from a token replay attack or a legitimate tamper attempt.
- **impact:** After a mid-dialogue restart, the `codex-dialogue` agent receives `invalid_request` scout failures and either proceeds without evidence or falls back to `manual_legacy`. There is no logged event and no operator-visible indication that a restart caused the failure (vs. a security event). This makes post-hoc diagnosis harder: a security audit of `shadow` events cannot distinguish "server restarted" from "attempted token replay." The distinction matters for CT-6 (consistency/availability tradeoff): state coordination (HMAC tokens) blocks progress after failures.
- **recommendation:** Emit a distinguishable server-side log event at startup (e.g., to stderr) so the restart event is visible in Claude Code's MCP server output alongside the subsequent `invalid_request` errors. Alternatively, consider passing a server generation/epoch counter in `TurnPacket` responses so agents can detect that a restart occurred and respond with a cleaner fallback signal. This is a medium-stakes improvement — the current recovery behavior is safe, just opaque.
- **confidence:** medium
- **provenance:** independent

---

## Coverage Notes

**Reliability (background emphasis):**

- **Service Guarantees:** No SLOs defined; this is appropriate and proportionate for a single-developer internal tool. Explicitly documented as best-effort in `event_log.py`. No finding.
- **Durability:** Analytics log is best-effort; explicitly acknowledged in HANDBOOK and `event_log.py`. Security enforcement (credential blocking) does not depend on log availability. No finding beyond RO-3's lifecycle gap.
- **Availability Model:** Single-process tools; no HA expectation. Context-injection can fall back to `manual_legacy`. Proportionate for the use case. No finding.
- **Degradation Strategy:** Explicit degradation paths documented in HANDBOOK failure matrix. `/dialogue` falls back to `manual_legacy`, analytics emit best-effort, stats skip malformed lines. Degradation is well-defined. No finding.

**Operational (primary emphasis):**

- **Deployability:** Single install command (`claude plugin install cross-model@turbo-mode`), auto-registers MCP servers and hooks, no manual post-install steps. README prerequisites are clear. Minor gap: no documented rollback path if a version introduces breaking behavior (no `@previous` tag mechanism noted). Low risk for single-developer tool. No separate finding.
- **Operational Ownership:** Single-developer tool; implicit ownership. The HANDBOOK's File-by-File Change Map is an unusually strong artifact for a tool of this size — it effectively acts as a component ownership map. No finding.

---

## Cross-Cutting Tension Notes

**CT-4 (Security ↔ Operability) [high attention]:** The credential scanning controls (fail-closed PreToolUse hook, 256 KiB threshold behavior divergence noted in HANDBOOK) create a known operational friction point: legitimate prompts can be blocked, and the only recovery is prompt rephrasing. This is a documented, conscious tradeoff. The 256 KiB threshold divergence between `codex_guard.py` (blocks) and `codex_delegate.py` (skips scan with stderr warning) for programmatic invocations is a security-operability gap worth surfacing to `trust-safety`. Messaging that reviewer.

**CT-6 (Consistency ↔ Availability) [high attention]:** Finding RO-4 directly instantiates this tension. HMAC state coordination blocks scout progress after server restart. The current resolution (agent continues without the scout) favors availability over consistency of the evidence-gathering path. The gap is that the failure signal is indistinguishable from a security event. Messaging `behavioral` reviewer.
