# Design Review: Cross-Model Plugin

**Target:** `packages/plugins/cross-model/` v3.1.3
**Scope:** subsystem | **Stakes:** medium | **Date:** 2026-03-26
**Archetypes:** Internal tool (primary), Event-driven (secondary)

---

## 1. Review Snapshot

| Metric | Value |
|--------|-------|
| Raw findings | 27 |
| Canonical findings (after consolidation) | 24 |
| Presented findings (hard cap) | 16 |
| Duplicate clusters merged | 3 |
| Corroborated findings | 3 |
| Contradictions | 0 |
| Normalization rewrites | 0 |
| Reviewers failed | 0 |
| Tensions mapped | 3 |

**Priority distribution (presented):** 6 P1, 10 P2
**Team:** 6/6 reviewers completed (structural-cognitive, behavioral, data, reliability-operational, change, trust-safety)

---

## 2. Focus and Coverage

### Emphasis Map

| Reviewer | Categories | Emphasis | Status |
|----------|-----------|----------|--------|
| structural-cognitive | Structural, Cognitive | background, primary | deep (4 findings) |
| behavioral | Behavioral | primary | deep (6 findings) |
| data | Data | background | screened (3 findings) |
| reliability-operational | Reliability, Operational | background, primary | deep (4 findings) |
| change | Change | primary | deep (5 findings) |
| trust-safety | Trust & Safety | background | deep — promoted (5 findings) |

### Category Coverage

| Category | Status | Notes |
|----------|--------|-------|
| Structural | screened | Clean — 5-layer model holds for 3/4 skills; deliberate boundaries |
| Cognitive | deep | 4 findings on legibility, discoverability, coherence, minimal surprise |
| Behavioral | deep | 6 findings — correctness and failure containment dominant |
| Data | screened | 3 findings; data flow clarity, source of truth, locality all clean |
| Reliability | screened | Proportionate for single-dev tool; best-effort explicitly acknowledged |
| Operational | deep | Configuration clarity gap (P1), resource proportionality, observability |
| Change | deep | Versioning and migration dominant — schema evolution path is constrained |
| Trust & Safety | deep (promoted) | Security surface warranted promotion; 5 findings including 2 P1 |

---

## 3. Findings

### F1. [P1] Credential scan bypass for oversized prompts in delegation path

- **source_findings:** BH-1, TS-1
- **support_type:** independent_convergence
- **contributors:** behavioral, trust-safety
- **merge_rationale:** Both independently identified the 256 KiB credential scan bypass at `codex_delegate.py:617-623`. BH-1 framed it as a correctness violation of governance lock #6; TS-1 framed it as a trust boundary integrity gap. Same defect, different analytical lenses.
- **lens:** Correctness / Trust Boundary Integrity
- **decision_state:** explicit decision
- **anchor:** `scripts/codex_delegate.py:617-623`; `HANDBOOK.md:845`
- **problem:** When a delegation prompt exceeds 256 KiB, `ToolInputLimitExceeded` is caught and the credential scan is skipped with a stderr warning. The `codex_guard.py` PreToolUse hook handles this divergently — it blocks (exit 2). The HANDBOOK documents the split but the consultation contract's governance lock #6 (non-negotiable egress sanitization) has no named exception for this case.
- **impact:** Programmatic invocations of `codex_delegate.py` (tests, scripts, future automation) bypass credential scanning on large prompts. This is the plugin's lowest-trust capability (autonomous Codex execution) on the path with the weakest safety guarantee. Interactive use is protected by the PreToolUse hook firing first.
- **recommendation:** Align `codex_delegate.py` to fail-closed on `ToolInputLimitExceeded`, matching the guard's behavior and governance lock #6. Alternatively, scan the first 256 KiB (partial coverage > none). If the skip is retained, add a named exception in consultation-contract.md #15.
- **confidence:** high

---

### F2. [P1] Concurrency race on HMAC token used-bit under concurrent transport

- **source_findings:** BH-2
- **support_type:** singleton
- **lens:** Concurrency Safety
- **decision_state:** explicit tradeoff
- **anchor:** `context-injection/context_injection/state.py:72-78`, `state.py:149-162`
- **problem:** The one-shot used-bit on `TurnRequestRecord` is set without an `asyncio.Lock`. The code comment acknowledges this relies on single-flight client behavior, which is not an MCP protocol guarantee. FastMCP's `Server.run()` dispatches via `tg.start_soon()`, making concurrent dispatch structurally possible.
- **impact:** If a client pipelines two `execute_scout` calls for the same `turn_request_ref` (possible under SSE/WebSocket transport), both could pass the used-bit check, violating CI-SEC-3 (one-shot replay prevention). Current stdio transport makes this unlikely but not impossible.
- **recommendation:** Add `asyncio.Lock` guarding the read-check-write on `record.used`. Low-overhead fix (microseconds of lock hold time). Alternatively, document the transport constraint as a deployment gate.
- **confidence:** high

---

### F3. [P1] REPO_ROOT silently misconfigures the entire dialogue subsystem

- **source_findings:** RO-1
- **support_type:** singleton
- **lens:** Configuration Clarity
- **decision_state:** underspecified
- **anchor:** `.mcp.json:16`, `context-injection/context_injection/server.py:47`
- **problem:** The context-injection MCP server captures `REPO_ROOT=${PWD}` at startup. If Claude Code is launched from a different directory, the server silently operates with the wrong git root for the entire session. The fail-closed `_load_git_files` behavior only fires on git command failure, not on a directory that is a valid-but-wrong git repo.
- **impact:** All `/dialogue` evidence gathering returns irrelevant results or no results. The failure is silent — the operator has no signal that misconfiguration occurred.
- **recommendation:** Emit `REPO_ROOT` value to stderr at startup. Add a HANDBOOK note that working directory is critical for `/dialogue` correctness.
- **confidence:** high

---

### F4. [P1] Prompt injection via Codex responses can influence scope anchoring

- **source_findings:** TS-2
- **support_type:** singleton
- **lens:** Trust Boundary Integrity
- **decision_state:** explicit tradeoff
- **anchor:** `references/context-injection-contract.md` #Scope Anchoring; `agents/codex-dialogue.md:170-178`
- **problem:** The agent (not the helper) controls scope anchoring. A compromised agent (via Codex prompt injection) could include entities outside the user's intended scope in TurnRequests. The contract explicitly documents this as accepted MVP risk with mitigations (denylist, git ls-files, redaction, budget caps).
- **impact:** Malicious Codex output could cause scouting of any git-tracked file. Post-redaction content would be exfiltrated to Codex in subsequent turns. Mitigations limit but don't eliminate the risk.
- **recommendation:** v2 hardening: mark entities extracted from Codex responses as `codex_supplied` and apply stricter scope criteria (e.g., focus-affinity hard gate on Codex-sourced entities). Document as a hardening item.
- **confidence:** medium

---

### F5. [P1] Context-injection `0.x exact-match` versioning makes every field addition a breaking deploy

- **source_findings:** CH-1
- **support_type:** singleton
- **lens:** Versioning & Migration
- **decision_state:** explicit decision
- **anchor:** `references/context-injection-contract.md#schema-versioning`; `context-injection/context_injection/types.py:26-29`
- **problem:** Any schema version mismatch returns `invalid_schema_version` with no backward-compatibility window. Adding a single optional field (e.g., the deferred `phase_id`) requires simultaneous agent and server deploy. For an LLM-executed agent, "atomic deploy" is not guaranteed — session state may cross versions.
- **impact:** Every schema change is a hard-coordination deploy. In-flight conversations fail at the version boundary. The rollout procedure is undocumented.
- **recommendation:** Document the rollout procedure: which updates first, what happens to in-flight conversations, and conditions for unlocking semver compatibility at 1.0.
- **confidence:** high

---

### F6. [P1] Governance drift CI checks are partially fictional

- **source_findings:** CH-2
- **support_type:** singleton
- **lens:** Versioning & Migration
- **decision_state:** underspecified
- **anchor:** `references/consultation-contract.md:409`; `references/composition-contract.md:723-727`
- **problem:** The consultation-contract check (`validate_consultation_contract.py`) exists but is not wired into CI — only into a repo-root test suite. The composition-contract #12.3 CI requirements (4 "MUST fail" rules) are entirely aspirational: no script exists. No participating skill declares the required `implements_composition_contract: v1` marker.
- **impact:** Contract drift goes undetected. A skill author could add a local variant of routing semantics (violating #2 execution ownership) with no automated gate.
- **recommendation:** Wire `validate_consultation_contract.py` into CI path-scoped to the plugin. Create a minimal composition-contract #12.3 check. Add the `implements_composition_contract: v1` marker to participating skills.
- **confidence:** high

---

### F7. [P2] `git_files` set is stale after server startup

- **source_findings:** BH-3
- **support_type:** singleton
- **lens:** Correctness
- **decision_state:** default likely inherited
- **anchor:** `context-injection/context_injection/server.py:47-71`
- **problem:** The set of git-tracked files is loaded once at startup and never refreshed. Files untracked after startup retain scout access; newly tracked files are blocked. The security-relevant direction: a file removed from the index after startup (`git rm --cached sensitive.key`) would remain scoutable.
- **impact:** For long-running server processes in active repos, the staleness window is unbounded. CI-SEC-2 is technically enforced but against a snapshot.
- **recommendation:** Add a TTL-based cache (e.g., refresh every 60 seconds) or document as a known limitation.
- **confidence:** high

---

### F8. [P2] HMAC `invalid_request` conflates security violations and operational restarts

- **source_findings:** RO-4, BH-6
- **support_type:** cross_lens_followup_confirmation
- **contributors:** reliability-operational, behavioral
- **merge_rationale:** RO-4 identified the operator signal gap (recoverability lens); BH-6 analyzed the protocol-level conflation and added the `failure_source` field recommendation (failure containment lens).
- **lens:** Recoverability / Failure Containment
- **decision_state:** explicit decision
- **anchor:** `context-injection/context_injection/state.py:102-106`; `execute.py:515-522`
- **problem:** `ScoutResultInvalid` with `status: "invalid_request"` is returned for both genuine HMAC token violations (CI-SEC-3) and operational state loss (server restart). No field distinguishes them.
- **impact:** Monitoring cannot distinguish attack attempts from operational restarts. Post-hoc security audit of `invalid_request` events is ambiguous.
- **recommendation:** Add an optional `failure_source` field (`"token_invalid"` vs `"state_lost"`) to `ScoutResultInvalid`. Non-breaking additive change.
- **confidence:** high

---

### F9. [P2] JSONL event log has no retention policy, rotation, or size bound

- **source_findings:** DA-3, RO-3
- **support_type:** independent_convergence
- **contributors:** data, reliability-operational
- **merge_rationale:** DA-3 identified the lifecycle gap (retention lens); RO-3 identified the same issue from observability and operational perspectives. Both independently flagged the full-file read in `compute_stats.py`.
- **lens:** Retention & Lifecycle / Observability
- **decision_state:** underspecified
- **anchor:** `scripts/event_log.py:8-16`; `~/.claude/.codex-events.jsonl`
- **problem:** The event log grows indefinitely. `/consultation-stats` reads the entire file on every invocation. No documented retention or cleanup procedure.
- **impact:** Stats computation slows linearly with file growth. Operators have no guidance on cleanup.
- **recommendation:** Document expected growth rate and safe truncation procedure in HANDBOOK. No code change required.
- **confidence:** high

---

### F10. [P2] `contract-agent-extract.md` can silently drift from normative sections

- **source_findings:** SC-4
- **support_type:** singleton
- **lens:** Legibility
- **decision_state:** explicit decision
- **anchor:** `references/contract-agent-extract.md:1-5`; `agents/codex-dialogue.md:89-94`
- **problem:** The agent extract is a manually maintained copy of 7 consultation contract sections (including normative #5, #7, #10). The governance drift CI check validates governance lock count only, not extract sync. If normative safety pipeline sections change, the extract drifts silently.
- **impact:** The codex-dialogue agent would execute stale safety rules while contract-level CI passes.
- **recommendation:** Add a `<!-- extract-version: <hash> -->` marker or prose warning in the consultation contract: "If you update #5, #7, #8, #9, #10, or #15, also update `contract-agent-extract.md`."
- **confidence:** medium

---

### F11. [P2] Phase boundary detection couples posture values into TurnRequest schema

- **source_findings:** CH-5
- **support_type:** singleton
- **lens:** Extensibility
- **decision_state:** explicit tradeoff
- **anchor:** `references/consultation-contract.md:392`; `context-injection/context_injection/types.py:26-29`
- **problem:** Phase boundaries are detected by posture change. Same-posture consecutive phases silently merge. The documented fix (`phase_id` in TurnRequest) requires a schema version bump under the `0.x exact-match` policy.
- **impact:** Profile authors cannot define multi-phase conversations with adjacent same-posture phases. Workaround (enforce distinct adjacent postures) constrains the profile system.
- **recommendation:** Assess whether deferring past current version is worth the friction. Document the Release C milestone that gates this fix.
- **confidence:** medium

---

### F12. [P2] Codex version check runs on every MCP call

- **source_findings:** RO-2
- **support_type:** singleton
- **lens:** Resource Proportionality
- **decision_state:** default likely inherited
- **anchor:** `scripts/codex_consult.py:138-162`
- **problem:** `_check_codex_version()` spawns a `codex --version` subprocess on every `consult()` call. An 8-turn dialogue triggers 9+ version checks, each with a 10-second timeout.
- **impact:** Adds sequential subprocess overhead per turn. A stalling version check appears as a mysterious pre-dispatch hang.
- **recommendation:** Cache the version check result for the process lifetime.
- **confidence:** high

---

### F13. [P2] `VALID_CONSULTATION_SOURCES` defined but never enforced

- **source_findings:** DA-1
- **support_type:** singleton
- **lens:** Schema Governance
- **decision_state:** default likely inherited
- **anchor:** `scripts/event_schema.py:165-171`
- **problem:** The enum is defined but never imported or validated. An arbitrary string passes silently; `compute_stats.py` falls through to `"unknown"`.
- **impact:** Stats skew silently on bad data. The enum gives false assurance of governance.
- **recommendation:** Wire the validation into `emit_analytics.py`'s existing `validate()` path.
- **confidence:** high

---

### F14. [P2] ~4000 lines of legacy test files with no removal plan

- **source_findings:** CH-4
- **support_type:** singleton
- **lens:** Testability
- **decision_state:** default likely inherited
- **anchor:** `tests/test_emit_analytics_legacy.py` (1771 lines) + 6 other `*_legacy.py` files
- **problem:** Seven legacy test files duplicate current coverage using an older class-based structure. No plan to replace or remove.
- **impact:** Module refactors require updating two test sets. Failing tests exist in both files, making triage harder.
- **recommendation:** Audit coverage overlap. Migrate unique cases, schedule removal.
- **confidence:** medium

---

### F15. [P2] `/dialogue` skill implements orchestration-layer logic beyond its stated layer

- **source_findings:** SC-2
- **support_type:** singleton
- **lens:** Coherence
- **decision_state:** explicit decision
- **anchor:** `README.md` (5-layer model); `skills/dialogue/SKILL.md` (~520 lines)
- **problem:** The README defines skills as "entrypoints" and agents as "orchestration." The `/dialogue` SKILL.md implements full briefing assembly (Steps 0-4b), including retry logic, health checks, seed_confidence composition, and analytics. Other skills follow the model; `/dialogue` is the exception.
- **impact:** Cognitive overhead when navigating the codebase or deciding where to modify dialogue orchestration.
- **recommendation:** Update the README's layer description to acknowledge `/dialogue` as a documented exception with rationale.
- **confidence:** high

---

### F16. [P2] `conversationId` deprecation has no removal path

- **source_findings:** CH-3
- **support_type:** singleton
- **lens:** Reversibility
- **decision_state:** explicit tradeoff
- **anchor:** `references/consultation-contract.md:75`; governance lock #5
- **problem:** `conversationId` is labeled "deprecated alias for `threadId`" with no version for removal, no migration guide, and no test asserting eventual failure.
- **impact:** Open deprecations accumulate permanence. New consumers inherit the alias without knowing it's deprecated.
- **recommendation:** Add an explicit removal condition (e.g., "removed when no skill or agent sends `conversationId`"). Add a test.
- **confidence:** high

---

### Additional findings below cap (8 P2, screened)

| ID | Summary | Reviewer |
|----|---------|----------|
| BH-4 | `RgNotFoundError` mapped to `"timeout"` status — semantic mismatch deferred to v0c | behavioral |
| BH-5 | `assert isinstance(...)` in `grep.py:313` production path — silently stripped under `-O` | behavioral |
| DA-2 | Schema version auto-bump heuristic won't scale past 3 feature flags | data |
| SC-1 | `tag-grammar.md` located outside canonical `references/` tree | structural-cognitive |
| SC-3 | Composition contract governs skills absent from this plugin (misleading README) | structural-cognitive |
| TS-3 | HMAC key has no rotation path — acceptable for current threat model | trust-safety |
| TS-4 | `credential_assignment` broad tier rationale undocumented | trust-safety |
| TS-5 | Audit log best-effort — block events can be silently lost on disk-full | trust-safety |

---

## 4. Tension Map

### T1. Performance ↔ Correctness (CT-1)

- **tension_id:** CT-1
- **kind:** canonical
- **sides:** Performance ↔ Correctness
- **what_is_traded:** The context-injection server loads the git-tracked file set once at startup for performance (avoiding per-request subprocess calls). This trades correctness of the CI-SEC-2 security gate — the gate evaluates against a stale snapshot that may not reflect the current index state.
- **why_it_hid:** The startup-load pattern is the natural default for initialization-time state. The staleness window only matters for long-running processes in actively-changing repositories — a condition that wasn't the primary design scenario but is the actual deployment scenario (MCP servers persist across the session).
- **likely_failure_story:** Developer removes a sensitive file from git tracking mid-session (`git rm --cached .secrets.yaml`). The context-injection server still considers it tracked and scoutable. The file's post-redaction contents are sent to Codex.
- **linked_findings:** F7
- **anchors:** side_a: `server.py:47-71` (startup load), side_b: `context-injection-contract.md` CI-SEC-2
- **reviewers_involved:** behavioral

---

### T2. Completeness ↔ Changeability (CT-3)

- **tension_id:** CT-3
- **kind:** canonical
- **sides:** Completeness ↔ Changeability
- **what_is_traded:** The context-injection contract specifies a 17-step pipeline, full field inventories, HMAC token spec, and exact-match versioning — a highly complete protocol definition. This completeness makes the protocol resistant to change: every field addition requires a version bump, coordinated deploy, and full regression. The governance drift CI checks intended to manage this tension are themselves partially unimplemented.
- **why_it_hid:** The completeness was built incrementally (v0.1.0 → v0.2.0) and each addition was justified. The accumulated changeability cost is visible only when you try to evolve the whole system — adding `phase_id`, for example, requires touching 4 artifacts in a coordinated change.
- **likely_failure_story:** A schema change is needed (e.g., `phase_id` for multi-phase support). The developer updates the server but forgets the agent extract. The governance CI check doesn't catch it because the composition-contract CI rules aren't wired. Mid-conversation, the agent hits `invalid_schema_version` with no graceful degradation.
- **linked_findings:** F5, F6, F10, F11
- **anchors:** side_a: `context-injection-contract.md` (full protocol spec), side_b: `types.py:26-29` (exact-match gate)
- **reviewers_involved:** change, structural-cognitive

---

### T3. Security ↔ Operability (CT-4)

- **tension_id:** CT-4
- **kind:** canonical
- **sides:** Security ↔ Operability
- **what_is_traded:** The credential scanning pipeline (fail-closed by design) creates a security guarantee at the cost of operational friction. The tension manifests in two concrete ways: (1) the delegation path trades security for operability on large prompts (skip scan > 256 KiB), and (2) the HMAC key regeneration on restart trades security signal for operational availability (restart failures look like attacks).
- **why_it_hid:** The delegation bypass was inherited from a prior implementation and preserved for "parity." The HMAC restart conflation was an acceptable simplification when the system was new — it becomes a diagnostic problem only after enough operational history accumulates to care about distinguishing events.
- **likely_failure_story:** An automated workflow generates a >256 KiB delegation prompt containing credentials from a config dump. The guard hook fires on the MCP layer (blocks for interactive use), but a direct programmatic call to `codex_delegate.py` bypasses the scan. Meanwhile, a server restart mid-session generates `invalid_request` events that a security audit later flags as potential attacks.
- **linked_findings:** F1, F8
- **anchors:** side_a: `codex_guard.py` (blocks >256 KiB), side_b: `codex_delegate.py:617-623` (skips scan)
- **reviewers_involved:** behavioral, trust-safety, reliability-operational

---

## 5. Questions / Next Probes

1. **Is the `codex_delegate.py` programmatic path a real invocation surface beyond tests?** If yes, F1 is a hard P0. If only the interactive `/delegate` path exists (protected by the PreToolUse hook), the bypass is defense-in-depth rather than a live gap. The answer determines whether the governance lock exception needs formal treatment.

2. **What's the path to context-injection 1.0 and semver compatibility?** F5 and F11 both trace to the `0.x exact-match` policy. If 1.0 is near, the cost of the current approach is bounded. If it's distant, the coordinated-deploy friction compounds with each schema change. What conditions gate the 1.0 milestone?

3. **Should the composition contract live in this plugin?** SC-3 (below cap) and CH-2 both note that the composition contract governs skills outside this plugin's boundary. If the composition contract is forward-looking infrastructure, does it belong at a higher level in the monorepo rather than inside `packages/plugins/cross-model/references/`?

4. **What is the actual threat model for context-injection scope anchoring (F4)?** The contract documents prompt injection as "accepted MVP risk." Has there been any adversarial testing of this path? The mitigations are sound but the attack is constructible — a Codex response containing backticked file paths (high confidence in entity extraction) that target interesting files would be extracted and scouted. Understanding the practical exploitability would help prioritize the v2 hardening recommendation.
