# Trust & Safety Review Findings

**Reviewer:** trust-safety
**Date:** 2026-03-26
**Plugin:** `packages/plugins/cross-model/` v3.1.3

---

## Summary

5 findings: 0 P0, 2 P1, 3 P2.

The plugin has a well-designed, layered credential protection model (PreToolUse hook + context-injection redaction pipeline + governance locks). The trust boundary between Claude and Codex is explicitly documented, the HMAC token model is sound, and the event log deliberately avoids logging prompt bodies. Two P1 findings relate to documented security gaps that were intentionally accepted — they warrant explicit decision records. Three P2 findings are design gaps that could be addressed without architectural change.

---

## Findings

### [TS-1] Large-prompt credential scan bypass in delegation path (256 KiB cap)

- **priority:** P1
- **lens:** Trust Boundary Integrity
- **decision_state:** explicit decision (accepted risk, documented in HANDBOOK.md guardrails and inline comment)
- **anchor:** `scripts/codex_delegate.py:617-623`; `HANDBOOK.md:845`
- **problem:** When a delegation prompt exceeds 256 KiB, `ToolInputLimitExceeded` is caught and the credential scan is skipped with only a stderr warning and no block. The comment says "allow to preserve parity" with a prior scan path that had no size gate. `codex_guard.py` handles this divergently — it blocks (exit 2) on prompts over 256 KiB. The HANDBOOK explicitly documents this behavioral split.
- **impact:** The blast radius is invocation-path-dependent. For interactive skill use (`/delegate` via Claude Code), the `codex_guard.py` PreToolUse hook fires first on MCP calls — making the delegate bypass moot in practice. However, programmatic direct invocations of `codex_delegate.py` (e.g., in tests, scripts, or future automation) bypass credential scanning on large prompts. This is the only path where egress sanitizer governance lock #6 (normative, non-negotiable) can be bypassed by input size — and it's the path that handles autonomous execution.
- **recommendation:** The two-layer divergence (guard blocks, delegate skips) should be resolved to a single behavior. Preferred: align `codex_delegate.py` to fail-closed on `ToolInputLimitExceeded` (block dispatch, return `status=blocked`), matching the guard's behavior and governance lock #6. Alternatively, scan the first 256 KiB and block if a credential is found — partial coverage is better than none for the programmatic path. If the skip behavior is retained, document it as a named exception in consultation-contract.md §15 governance lock #6 so future readers understand the intended limit.
- **confidence:** high
- **provenance:** independent; confirmed by reliability-operational (CT-4 flag)

---

### [TS-2] Prompt injection via Codex responses can influence scope anchoring (documented, accepted risk)

- **priority:** P1
- **lens:** Trust Boundary Integrity
- **decision_state:** explicit tradeoff (documented in contract §Scope Anchoring)
- **anchor:** `references/context-injection-contract.md` §Scope Anchoring; `agents/codex-dialogue.md:170-178`
- **problem:** The contract explicitly documents that a compromised `codex-dialogue` agent (e.g., via prompt injection through Codex responses) could include entities outside the true user scope in `TurnRequest`. The agent — not the helper — controls scope anchoring (what to send). The helper enforces path-level safety but cannot enforce intent-level scope.
- **impact:** Malicious Codex output crafted to look like claims containing sensitive file paths (e.g., `./auth.json:42` or `.env`) could be extracted as entities and submitted for scouting. The denylist and `git ls-files` gate block the worst cases, but the attack surface includes any file tracked in git. A successful injection could read config or source files and exfiltrate their (post-redaction) content to Codex in subsequent turns.
- **recommendation:** The current mitigations (denylist, git ls-files, redaction, budget caps, evidence wrapper) are sound for MVP. The contract's explicit acknowledgment is good. Recommend adding one improvement: the agent should apply a "Codex-supplied entity" marker to entities extracted from Codex responses (as opposed to the user's original question), and apply stricter scope criteria (e.g., focus-affinity hard gate, no file path entities from Codex turns unless matching the original `scope_envelope`). This would require a change to the context injection protocol. Flag as a v2 hardening item.
- **confidence:** medium
- **provenance:** independent

---

### [TS-3] HMAC key single per-process — no rotation path documented

- **priority:** P2
- **lens:** Blast Radius of Breach
- **decision_state:** explicit decision (documented in §HMAC Token Specification)
- **anchor:** `references/context-injection-contract.md` §HMAC Token Specification:481-483
- **problem:** The HMAC key is a single 32-byte random value generated at server startup (`os.urandom`). The contract explicitly states "no hierarchical key derivation — the attacker model (prompt injection via Codex) never has access to keys, so key compartmentalization adds complexity without security gain." There is no documented procedure for key rotation outside of process restart.
- **impact:** If an attacker obtained the in-process HMAC key (e.g., via a memory disclosure in the MCP server), they could mint valid scout tokens for arbitrary paths, bypassing CI-SEC-3. The contract's threat model excludes this (the attacker is Codex responses, not in-process memory access). Given the system runs locally on the developer's machine, the blast radius of an HMAC key compromise is bounded to the user's own filesystem. The decision is defensible for the stated threat model.
- **recommendation:** No immediate action required given the threat model. Add a note to the contract clarifying what would change the threat model (e.g., multi-user deployment, remote MCP server) and therefore require key compartmentalization. Keep as documentation gap.
- **confidence:** high
- **provenance:** independent

---

### [TS-4] `credential_assignment` (password=/secret=) is broad-tier (shadow only, not blocked)

- **priority:** P2
- **lens:** Data Sensitivity Classification
- **decision_state:** explicit tradeoff (pattern is in `secret_taxonomy.py` with tier="broad")
- **anchor:** `scripts/secret_taxonomy.py:213-223`
- **problem:** The family `credential_assignment` (pattern: `password=`, `passwd=`, `secret=`, `credential=`) is classified as `broad` tier — it logs a shadow event but does NOT block dispatch. This means `password=hunter2` in a Codex prompt is logged but sent to the OpenAI API.
- **impact:** Common credential patterns found in config files, shell output, or error messages (`Error: password=xyz is incorrect`) will not be caught by the egress scanner. The broad-tier families cover the patterns most likely to appear in incidentally included code and output. The gap between `credential_assignment_strong` (contextual, blocking) and `credential_assignment` (broad, shadow) is intentional but may surprise operators reviewing the taxonomy.
- **recommendation:** Document the explicit rationale for broad vs. contextual tier placement in `secret_taxonomy.py` — the current code comments explain tiering at a high level but don't explain why `credential_assignment` is broad rather than contextual. If the pattern generates excessive false positives in practice, the shadow telemetry would show this; consider a review gate that upgrades patterns with low false-positive rates from broad to contextual.
- **confidence:** high
- **provenance:** independent

---

### [TS-5] Audit log is best-effort; audit trail failures on security-relevant blocks not surfaced to user

- **priority:** P2
- **lens:** Auditability
- **decision_state:** explicit decision (documented in `event_log.py` comment, line 6-10)
- **anchor:** `scripts/event_log.py:6-10`; `scripts/codex_guard.py:52-56`
- **problem:** The event log comment explicitly documents: "Best-effort JSONL append is proportionate for a single-developer tool... If the user base grows or audit trail is needed for governance compliance, upgrade to a separate audit log with fail-closed write semantics." When a `block` event (credential detected, dispatch blocked) fails to write to the audit log, `codex_guard.py` prints a warning to stderr but the blocking decision still proceeds. The user sees the block in the conversation but the audit record is silently lost.
- **impact:** Security blocks (credential detected in prompt) may not appear in `~/.claude/.codex-events.jsonl` if the disk is full or the file is unwritable. Post-hoc investigation of "why was this blocked?" becomes harder. For a single-developer internal tool, this is low risk. For a team deployment, missing block events could obscure security incidents.
- **recommendation:** No immediate action required given the "single-developer tool" context. Track the upgrade path noted in the comment — when the user base grows, the audit log for security-enforcement events (block and shadow) should be fail-closed separate from the analytics log. The existing code structure (separate `codex_guard._append_log` wrapper that logs to stderr on failure) makes this upgrade straightforward.
- **confidence:** high
- **provenance:** independent

---

## Coverage Notes

**Least Privilege:** The plugin accesses the user's filesystem via context-injection scouts, but access is gated by (a) `git ls-files` policy (tracked files only), (b) denylist, (c) focus-affinity gate, (d) budget caps. The codex MCP tool is scoped to the `mcp__plugin_cross-model_codex__` namespace. The delegation subprocess inherits the user's full process environment — no privilege reduction — but this is inherent to running `codex exec` locally and the threat model is single-developer. Least privilege is handled appropriately for the stated use case.

**Trust Boundary Integrity (§3 preflight consent):** The egress manifest + consent gate in §3 provides explicit user control over what classes of content leave the machine. The 5 re-consent triggers are deterministic and well-specified. No gaps found beyond TS-1 and TS-2.

**Blast Radius of Breach (Codex API key):** The plugin sends prompts to Codex but does not manage API keys — it delegates to the `codex` CLI which manages its own credentials. If a Codex API key were leaked, the impact would be external to this plugin's control. The credential scanner would catch an API key (`sk-...` is contextual-tier) if it appeared in an outbound prompt. No gap found here.

**`fail_not_run` sanitizer status:** This status is a sentinel for "scan did not run" — it represents an implementation correctness invariant, not a normal code path. The PreToolUse hook enforces the scan on every Codex call; the agent contract instructs fail-closed on scan failure. No reachable path produces `fail_not_run` in a correct implementation. The TS-1 finding covers the one real exception (size cap bypass).
