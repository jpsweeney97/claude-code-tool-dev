# B5 Candidate — Production Synthesis

**Objective:** Is the advisory runtime rotation model specified strongly enough for privilege widening and narrowing, or where are the weak points?

**Posture:** evaluative | **Turn budget:** 6 | **Termination:** `error` (dialogue-tool failure on turn 5) | **Converged:** false

---

**`error`** | converged: `false` | turns: `5/6` | mode: `agent_local` | mode_source: `null`

## Synthesis

The advisory runtime rotation model is directionally correct but **NOT specified strongly enough** for safe, deterministic privilege widening and narrowing.

The **severe weakness** is the narrowing trigger contract: `policy.md:71-73` references a comparison against "base policy defaults" without defining the capability-request shape, the comparator, or an ambiguity fallback. The implementation confirms this — `ConsultRequest` carries only a boolean `network_access` flag used as a widening-rejection gate (`control_plane.py:153`), and `build_policy_fingerprint` takes no parameters at all (`control_plane.py:432-446`), so policies cannot be compared across rotation boundaries even if a narrowing decision were made.

A **real-but-bounded secondary weakness** is protocol-level silence on post-reap fork continuity: the spec never states whether the replacement's forked history must remain independently usable after the frozen runtime is reaped, and the implementation hardcodes `fork_thread` with `ephemeral=True` (`runtime.py:102`), with all durability rules delegated to the out-of-scope `recovery-and-journal.md`.

Two additional weaknesses are **theoretical within the three allowed files but are genuine contract holes**:
1. The spec does not define the concurrency model for incoming turns during the freeze-start-fork-repoint interval — the implementation uses an unsynchronized dict (`control_plane.py:78`) with no locks or queues.
2. The reap table gives both a primary "first successful turn" trigger and a TTL fallback with no precedence rule when TTL expires during the in-flight first replacement turn, contradicting the table's own rationale that the frozen runtime must survive until the replacement proves healthy.

**Minimum spec amendment set** (two sections):
- **(A)** A canonical capability-request schema and widen/hold/narrow decision table with conservative defaults for missing or ambiguous capability declarations.
- **(B)** A compact rotation state-machine section defining fork-continuity-after-reap requirements, handle-promotion atomicity, incoming-turn disposition during rotation, and explicit precedence that TTL cannot reap while the replacement's first proving turn is in flight.

Amendment (A) is required because Claim 1 is otherwise unexecutable as written. Amendment (B) closes the three remaining protocol gaps in one structural addition.

## Claims

| Claim | Status | Citation |
|---|---|---|
| SEVERE: narrowing trigger under-specified — no canonical capability-request shape, no ambiguity fallback, no deterministic pre-turn decision rule; `ConsultRequest.network_access` is widening-rejection only, `build_policy_fingerprint` takes no runtime params | supported | `docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md:71-73` |
| BOUNDED AMBIGUITY: spec silent on post-reap continuity semantics of forked history; `fork_thread` is hardcoded `ephemeral=True` and durability rules delegated out-of-scope | supported | `packages/plugins/codex-collaboration/server/runtime.py:97-109` |
| THEORETICAL GAP: rotation contract does not define concurrency model for incoming turns during freeze-start-fork-repoint interval; `_advisory_runtimes` is an unsynchronized dict with no Lock/Queue | supported | `packages/plugins/codex-collaboration/server/control_plane.py:78` |
| THEORETICAL GAP: reap table gives primary "first successful turn" and fallback TTL triggers with no precedence rule when TTL expires during in-flight proving turn | supported | `docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md:102-110` |
| Minimum spec amendment set: (A) capability-request schema + widen/hold/narrow decision table; (B) rotation state-machine covering fork continuity, promotion atomicity, in-flight turn disposition, and TTL precedence | not_scoutable | — |

## Citations

- `docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md:63-74` — "## Privilege Narrowing... Narrowing is triggered when Claude initiates a turn that does not require the current runtime's elevated capabilities. The control plane compares the requested capabilities against the [base policy defaults] and rotates down if the turn can be served at a lower privilege level." `[dialogue]`
- `docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md:79-98` — "## Freeze-and-Rotate Semantics... A frozen runtime: Accepts no new turns. Remains available for thread history reads... Rotation creates a new runtime: 1. Freeze. 2. Start new runtime. 3. Fork thread history. 4. Update handle mappings. 5. Emit rotate audit event." `[dialogue]`
- `docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md:102-110` — "Reap conditions: primary = replacement completes first successful turn; fallback = TTL from freeze timestamp expires; terminal = Claude session ends. No precedence rule when TTL and first-turn-in-flight conflict." `[dialogue]`
- `docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md:138-146` — "## Recovery and Journal Interactions... Crash recovery for advisory runtimes follows the path defined in recovery-and-journal.md. Reap timing follows retention defaults for the TTL fallback condition." `[dialogue]`
- `packages/plugins/codex-collaboration/server/runtime.py:97-109` — "def fork_thread(self, thread_id): result = self._client.request('thread/fork', {'threadId': thread_id, 'ephemeral': True})" `[dialogue]`
- `packages/plugins/codex-collaboration/server/runtime.py:78-130` — "start_thread and run_turn hardcode approvalPolicy='never' and sandboxPolicy={'type':'readOnly'} as static literals; no parameter surface for a widened/narrowed policy." `[dialogue]`
- `packages/plugins/codex-collaboration/server/control_plane.py:78` — "self._advisory_runtimes: dict[str, AdvisoryRuntimeState] = {}  [unsynchronized dict, no Lock/Queue/serialization]" `[dialogue]`
- `packages/plugins/codex-collaboration/server/control_plane.py:147-157` — "def codex_consult(self, request): if request.network_access: raise RuntimeError('Consult failed: advisory widening is not implemented in R1.')" `[dialogue]`
- `packages/plugins/codex-collaboration/server/control_plane.py:424-446` — "_invalidate_runtime is pop-and-close (no freeze, fork, or audit event). build_policy_fingerprint takes no runtime parameters — hardcoded SHA256 of fixed literals." `[dialogue]`

## Ledger Summary

Dialogue terminated early on turn 5 due to dialogue-tool failure: `codex.dialogue.reply` returned empty content (parse error) on the final closure prompt. Thread durably recorded at turn_count=3. Codex's turn-3 position already delivered the final severity ranking and minimum-amendment set before the failure — only a restated yes/no closing verdict was lost. Synthesis draws from that final Codex position plus dialogue scout evidence. Four factual weakness claims supported (1, 2, 3 via direct scout; 4 via Codex's direct citation to `policy.md:100-110`, not independently scouted). Claim 5 is a prescriptive synthesis (not_scoutable). Verdict: rotation model is directionally correct but not specified strongly enough — the narrowing trigger contract is the single severe gap.

## Canonical Artifact

```json
{
  "objective": "Is the advisory runtime rotation model specified strongly enough for privilege widening and narrowing, or where are the weak points?",
  "mode": "agent_local",
  "mode_source": null,
  "termination_code": "error",
  "converged": false,
  "turn_count": 5,
  "turn_budget": 6,
  "final_claims": [
    {
      "text": "SEVERE: The narrowing trigger is under-specified at the contract level. Policy.md:71-73 says the control plane 'compares the requested capabilities against the base policy defaults,' but no canonical capability-request shape, no ambiguity fallback, and no deterministic pre-turn decision rule exists. The only capability signal in the code is a boolean network_access in ConsultRequest, which is a widening-rejection gate (control_plane.py:153), not a narrowing comparator. build_policy_fingerprint takes no runtime parameters (control_plane.py:432-446) so it cannot even represent a widened/narrowed policy for comparison across rotation boundaries.",
      "final_status": "supported",
      "representative_citation": {"path": "docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md", "lines": "71-73", "snippet": "Narrowing is triggered when Claude initiates a turn that does not require the current runtime's elevated capabilities. The control plane compares the requested capabilities against the [base policy defaults] and rotates down if the turn can be served at a lower privilege level."}
    },
    {
      "text": "BOUNDED AMBIGUITY: The spec is silent on post-reap continuity semantics of forked history. Rotation step 3 (policy.md:96) requires forking thread history from the frozen runtime, and the Reap table (policy.md:102-110) says the frozen runtime is reaped after the replacement's first successful turn. But no normative text in the allowed files specifies whether the forked history must remain independently usable after reap. The implementation hardcodes fork_thread with ephemeral=True (runtime.py:102), and policy.md:138-146 delegates all recovery/durability rules to out-of-scope recovery-and-journal.md. Not a proved single-rotation defect but a real continuity gap for later rotations and crash recovery.",
      "final_status": "supported",
      "representative_citation": {"path": "packages/plugins/codex-collaboration/server/runtime.py", "lines": "97-109", "snippet": "def fork_thread(self, thread_id: str) -> str: result = self._client.request('thread/fork', {'threadId': thread_id, 'ephemeral': True})"}
    },
    {
      "text": "THEORETICAL GAP: The rotation contract does not define a concurrency model for incoming turns during the freeze-start-fork-repoint interval. Freeze (policy.md:83-89) says the frozen runtime 'accepts no new turns,' and turn-boundary invariants (policy.md:112-117) say no rotation occurs mid-turn, but the spec never defines whether a second codex.consult may race in during rotation, or how incoming turns are queued, rejected, or bound to temporary state. The implementation's self._advisory_runtimes dict (control_plane.py:78) is an unsynchronized cache with no Lock, Queue, or serialization primitive anywhere in ControlPlane. Latent contract hole, but not demonstrable as a real race within the allowed files.",
      "final_status": "supported",
      "representative_citation": {"path": "packages/plugins/codex-collaboration/server/control_plane.py", "lines": "78", "snippet": "self._advisory_runtimes: dict[str, AdvisoryRuntimeState] = {}"}
    },
    {
      "text": "THEORETICAL GAP: The reap table (policy.md:102-110) provides two triggers — primary 'first successful turn' and fallback 'TTL from freeze timestamp expires' — but no precedence rule when TTL expires during the in-flight first replacement turn. The prose rationale says the primary trigger is conservative because the frozen runtime survives until the replacement proves it works, but without an explicit tie-break, TTL can fire before that proof completes, contradicting the rationale. Policy.md:112-117 turn-boundary invariants do not defer reaping. Severity is bounded because TTL magnitude is delegated to recovery-and-journal.md:146 (out of scope); within the allowed files there is no evidence TTL is short enough for the race to be realistic.",
      "final_status": "supported",
      "representative_citation": {"path": "docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md", "lines": "102-110", "snippet": "| Replacement runtime completes its first successful turn | Primary | Proves the fork worked and the new runtime is healthy | | TTL from freeze timestamp expires | Fallback | Prevents accumulation if the replacement never becomes healthy |"}
    },
    {
      "text": "Minimum spec amendment set to close the severe gap: (A) add a canonical capability-request schema and decision table covering widen/hold/narrow with omitted, unknown, and partial capability declarations, plus a conservative default; (B) add a compact rotation state-machine section defining post-reap fork continuity requirements, handle-promotion atomicity, incoming-turn disposition during rotation, and explicit TTL-cannot-preempt-proving-turn precedence.",
      "final_status": "not_scoutable",
      "representative_citation": null
    }
  ],
  "synthesis_citations": [
    {"path": "docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md", "line_range": "63-74", "snippet": "## Privilege Narrowing... Narrowing is triggered when Claude initiates a turn that does not require the current runtime's elevated capabilities. The control plane compares the requested capabilities against the [base policy defaults] and rotates down if the turn can be served at a lower privilege level.", "citation_tier": "dialogue"},
    {"path": "docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md", "line_range": "79-98", "snippet": "## Freeze-and-Rotate Semantics... A frozen runtime: Accepts no new turns. Remains available for thread history reads... Rotation creates a new runtime: 1. Freeze the current runtime. 2. Start a new App Server runtime with the target policy. 3. Fork the thread history from the frozen runtime into the new runtime. 4. Update the control plane's handle mappings. 5. Emit an audit event with action: rotate.", "citation_tier": "dialogue"},
    {"path": "docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md", "line_range": "102-110", "snippet": "Reap conditions table: primary = replacement completes first successful turn; fallback = TTL from freeze timestamp expires; terminal = Claude session ends. No precedence rule when TTL and first-turn-in-flight conflict.", "citation_tier": "dialogue"},
    {"path": "docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md", "line_range": "138-146", "snippet": "## Recovery and Journal Interactions... Crash recovery for advisory runtimes follows the path defined in recovery-and-journal.md. Reap timing follows retention defaults for the TTL fallback condition. [All durability/retention rules delegated out of scope.]", "citation_tier": "dialogue"},
    {"path": "packages/plugins/codex-collaboration/server/runtime.py", "line_range": "97-109", "snippet": "def fork_thread(self, thread_id: str) -> str: result = self._client.request('thread/fork', {'threadId': thread_id, 'ephemeral': True})", "citation_tier": "dialogue"},
    {"path": "packages/plugins/codex-collaboration/server/runtime.py", "line_range": "78-130", "snippet": "start_thread and run_turn hardcode approvalPolicy='never' and sandboxPolicy={'type':'readOnly'} as static literals; no parameter surface for a widened/narrowed policy to flow through either call site.", "citation_tier": "dialogue"},
    {"path": "packages/plugins/codex-collaboration/server/control_plane.py", "line_range": "78", "snippet": "self._advisory_runtimes: dict[str, AdvisoryRuntimeState] = {}  [unsynchronized dict, no Lock/Queue/serialization anywhere in ControlPlane class lines 53-145]", "citation_tier": "dialogue"},
    {"path": "packages/plugins/codex-collaboration/server/control_plane.py", "line_range": "147-157", "snippet": "def codex_consult(self, request): if request.network_access: raise RuntimeError('Consult failed: advisory widening is not implemented in R1.')  [The only capability signal in ConsultRequest is a widening-rejection gate, not a narrowing comparator.]", "citation_tier": "dialogue"},
    {"path": "packages/plugins/codex-collaboration/server/control_plane.py", "line_range": "424-446", "snippet": "_invalidate_runtime is pop-and-close (no freeze, fork, or audit event). build_policy_fingerprint takes no runtime parameters — hardcoded SHA256 of fixed literals; cannot represent a widened or narrowed policy.", "citation_tier": "dialogue"}
  ],
  "final_synthesis": "The advisory runtime rotation model is directionally correct but NOT specified strongly enough for safe, deterministic privilege widening and narrowing. The severe weakness is the narrowing trigger contract: policy.md:71-73 references a comparison against 'base policy defaults' without defining the capability-request shape, the comparator, or an ambiguity fallback, and the implementation surface confirms this — ConsultRequest carries only a boolean network_access flag used as a widening-rejection gate (control_plane.py:153), and build_policy_fingerprint takes no parameters at all (control_plane.py:432-446), so policies cannot be compared across rotation boundaries even if a narrowing decision were made. A real-but-bounded secondary weakness is protocol-level silence on post-reap fork continuity: the spec never states whether the replacement's forked history must remain independently usable after the frozen runtime is reaped, and the implementation hardcodes fork_thread with ephemeral=True (runtime.py:102), with all durability rules delegated to the out-of-scope recovery-and-journal.md. Two additional weaknesses are theoretical within the three allowed files but are genuine contract holes: (1) the spec does not define the concurrency model for incoming turns during the freeze-start-fork-repoint interval — the implementation uses an unsynchronized dict (control_plane.py:78) with no locks or queues — and (2) the reap table gives both a primary 'first successful turn' trigger and a TTL fallback with no precedence rule when TTL expires during the in-flight first replacement turn, contradicting the table's own rationale that the frozen runtime must survive until the replacement proves healthy. The minimum spec amendment set is two sections: (A) a canonical capability-request schema and widen/hold/narrow decision table with conservative defaults for missing or ambiguous capability declarations, and (B) a compact rotation state-machine section defining fork-continuity-after-reap requirements, handle-promotion atomicity, incoming-turn disposition during rotation, and explicit precedence that TTL cannot reap while the replacement's first proving turn is in flight. Amendment (A) is required because Claim 1 is otherwise unexecutable as written. Amendment (B) closes the three remaining protocol gaps in one structural addition.",
  "ledger_summary": "Dialogue terminated early on turn 5 due to dialogue-tool failure: codex.dialogue.reply returned empty content (parse error) on the final closure prompt. Thread durably recorded at turn_count=3. Codex's turn-3 position already delivered the final severity ranking and minimum-amendment set before the failure — only a restated yes/no closing verdict was lost. Synthesis draws from that final Codex position plus dialogue scout evidence. Four factual weakness claims supported (1, 2, 3 via direct scout; 4 via Codex's direct citation to policy.md:100-110, not independently scouted). Claim 5 is a prescriptive synthesis (not_scoutable). Verdict: rotation model is directionally correct but not specified strongly enough — the narrowing trigger contract is the single severe gap."
}
```
