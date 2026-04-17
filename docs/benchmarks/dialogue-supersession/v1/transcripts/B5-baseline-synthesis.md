# B5 Baseline — codex-dialogue Synthesis

**Thread ID:** `019d9811-b052-7163-b5e2-e91b9db26ffb`
**Question:** Is the advisory runtime rotation model specified strongly enough for privilege widening and narrowing, or where are the weak points?
**Posture:** evaluative
**Turns:** 5 of 6 budget
**Mode:** `server_assisted`
**Scope envelope:** `docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md`, `packages/plugins/codex-collaboration/server/control_plane.py`, `packages/plugins/codex-collaboration/server/runtime.py` (read-only)

This is the verbatim synthesis returned by the `cross-model:codex-dialogue` subagent after Phase 3 (synthesis assembly from `turn_history`). It is the canonical dialogue output — narrative synthesis + Synthesis Checkpoint block + pipeline-data epilogue.

---

All 5 original unresolved items are now closed. 27 claims, all advancing. I have budget for 1 more turn. Since every question has been substantively answered with a final priority ranking and the server returns `continue_dialogue`, the last turn should be a consolidation/closing probe asking Codex to state its final position concisely. But the synthesis already happened in T5's "Sharpest Summary". Rather than waste a turn with no new signal, I'll proceed to Phase 3 synthesis — continuing would be `static` or `restatement` and the ledger is clean.

Now synthesizing the findings.

# Evaluative Dialogue Synthesis: Advisory Runtime Rotation Model

## Bottom Line (high confidence)

**The spec is strong enough for the safety posture but not strong enough to implement widening/narrowing without inventing policy semantics.** The freeze-and-rotate invariant and "no mid-turn rotation" prohibition are well-defined. Everything that describes *what the runtime transitions between* and *how it transitions safely under concurrency* is underspecified.

## Weak Points — Ranked by Fix Priority

### 1. Authoritative Policy Model — FIX FIRST (high confidence)
This is the root cause. All other weak points are machinery for moving between policy states that the spec doesn't precisely define.

- No single typed `EffectiveAdvisoryPolicy` object. The fingerprint claims to cover 5 dimensions (transport, sandbox, network, approval, connectors), but the only referenced defaults are prose tables in `foundations.md` whose terms don't align one-to-one (e.g., "Network approvals" vs "Network access").
- Direct evidence of the gap: `build_policy_fingerprint()` at `packages/plugins/codex-collaboration/server/control_plane.py:432` returns hardcoded literals — the implementation had no typed source to derive from, so it invented constants.
- **Recommendation:** promote the advisory policy into its own `policy-model.md` contract file containing a typed `EffectiveAdvisoryPolicy` dataclass. Fingerprint derives from exactly that object. The request contract materializes a full `target_policy` per turn; decision procedure becomes mechanical (`if current == target: reuse else: rotate`). "Widen" vs "narrow" becomes a post-hoc label, not the core decision.

### 2. Request Contract for Capability Changes (high confidence)
- `codex.consult` has no capability fields; `ConsultRequest` carries only `network_access: bool` plus an opaque `profile`. Insufficient to represent sandbox, approval mode, or connectors.
- **Recommendation:** flat capability struct (`sandbox_policy`, `network_access`, `approval_mode`, `connector_allowlist` as set), canonicalized into a full `target_policy` object server-side. Named enums fail on matrix explosion. Delta-against-base fails on ambiguous omission.
- **Profile vs capability rule:** capabilities are authoritative for privilege; profiles are prompt/context only (posture, effort, budget, source selection). Current `profiles.py` includes `sandbox` and `approval_policy` — this creates two competing policy channels and must be cut. If both are supplied, explicit capabilities win; profile with policy fields must match exactly or the request is invalid. Never silent override.

### 3. Narrowing Semantics — Philosophically Unsound (high confidence)
- The phrase "narrowest sufficient policy" implies the control plane can predict turn needs. It cannot — only the caller's declared target is knowable.
- **Recommended wording fix:** replace "each turn runs under the narrowest sufficient policy" with "each turn is admitted under the narrowest requested target policy for that turn."
- **Interpretation question resolved:** lazy narrowing is correct (narrow only when turn N+1 signals a smaller target). Speculative narrowing (always narrow after a widened turn) is wrong — it guarantees widen → turn → narrow → widen thrash on oscillating dialogues, multiplies rotation overhead, and amounts to guessing.
- **Recovery contract:** if a turn needs more than declared, it fails under the declared policy; Claude retries as a new turn with broader target. No auto-continuation. No mid-turn rotation.
- **Five-part repair:** (1) lazy narrowing only, (2) explicitly reject speculative narrowing, (3) replace "narrowest sufficient" wording, (4) define fail-and-retry recovery, (5) make narrowing observable via explicit rotate events.

### 4. Concurrency Gap — Unstated Coupling (high confidence)
- The "next turn boundary" concept requires total order over turn admissions in a shared advisory runtime. Today that total order is supplied externally by MCP dispatch serialization (see `delivery.md`). The rotation spec itself defines no concurrency model.
- This is **unstated coupling**, not a benign external invariant — if dispatch stops being serialized, the spec breaks immediately.
- **Six concrete race hazards** if serialization drops: (1) stale admission after freeze, (2) double rotation from same source runtime, (3) conflicting widen/narrow direction at same boundary, (4) partial handle remap, (5) premature reap of frozen runtime, (6) duplicate turn sequencing.
- **Contention unit is `(claude_session_id, repo_root)`, not conversation.** Per-`collaboration_id` locks are structurally insufficient (multiple dialogues and consults share the same runtime; consults lack durable handles).
- **Load-bearing minimum contract:** (1) define concurrency unit as advisory domain, (2) linearize `policy-eval + freeze/rotate + registry replace + handle remap + turn bind` in one critical section per domain, (3) frozen runtimes accept no new admissions, (4) reap requires both replacement success AND no turns bound to frozen.
- **Not sufficient on their own:** per-`collaboration_id` lock, CAS only on handle mapping, registry-only mutex.
- Concrete evidence: `lineage_store.py:169` updates are append-only last-wins with no CAS — split-brain rotation today would produce orphaned lineage.

### 5. Rotation Observability Asymmetry (high confidence)
- Widening has a caller-initiated signal; narrowing is server-internal with no signal. The `rotate` audit event's typed schema today carries only `runtime_id` and `policy_fingerprint` — old/new linkage relies on implementation-defined `extra` payload.
- **Required minimum audit schema** for every rotation: `old_runtime_id`, `new_runtime_id`, `old_policy_fingerprint`, `new_policy_fingerprint`, `reason_code`, `trigger_source`.
- **Valid narrowing reason codes** stay narrow: `request_target_policy_lower_than_current`, `request_target_policy_equals_base`. Do NOT add "idle base-policy reclamation" (would endorse speculative narrowing, which the model correctly rejects).

### 6. Base-Policy Authority (medium-high confidence)
- Base policy should be resolved at control-plane startup, then fixed for the lifetime of the Claude session.
- **Not per-repo** (creates hidden trust-tier variance; makes audit/comparison harder).
- **Not hot-changeable** during a session (would allow silent trust-posture mutation without caller request; complicates recovery).
- **Not env vars directly.** Use a typed `AdvisoryPolicyConfig` object sourced from settings file or startup parameter. Env vars are an implementation input, a poor normative interface for a trust boundary.
- Deployment config change is **not** a live rotation trigger; applies only to new sessions.

### 7. Generation/Epoch — Conditionally Load-Bearing (medium-high confidence)
- **Today (R1, live-process state only):** hardening, not required, *if* the spec guarantees atomic bind under the per-domain lock.
- **Strictly load-bearing** if any split between remap and bind is permitted.
- **Strictly load-bearing for R2/R3** if journal-based replay of advisory rotation/binding state is added — fingerprint alone is insufficient because `base → wide → base` repeats fingerprints, and `runtime_id` is identity not ordering.
- **Recommendation:** add `policy_generation: int` to advisory domain state now; persist on handle remaps, rotation journal entries, and rotate audit events. Cheap to add; avoids a later protocol-level migration.

## Implementation-vs-Spec Gaps (confirmation, high confidence)

Current R1 code confirms the spec gaps are contract-level, not merely unimplemented:
- Widening is hard-rejected (`packages/plugins/codex-collaboration/server/control_plane.py:147`).
- `build_policy_fingerprint` is hardcoded (`control_plane.py:432`), structurally incapable of distinguishing policy levels.
- Narrowing has no code path: neither `codex_consult`, `_bootstrap_runtime`, nor `_probe_runtime` contains a narrowing decision, rotation call, or base-policy comparison.
- Runtime startup literals `approvalPolicy: never` and `readOnly: true` in `runtime.py`.
- Some is deliberate R1 scoping; some exists because the spec lacks an executable target-policy contract to implement against.

## Dialogue Metadata
- Conversation ID: `019d9811-b052-7163-b5e2-e91b9db26ffb`
- Turns: 5 of 6 budget (closing without 6th turn — all 5 unresolved items closed, trajectory static would be the next delta).
- Ledger: 27 claims, 0 reinforced, 0 revised, 0 conceded, 5 unresolved closed, 0 open.
- Trajectory: advancing → advancing → advancing → advancing → advancing (no plateau).
- Posture: evaluative throughout.
- Evidence scouts: 0 (template_candidates remained empty across all turns — server did not resolve file entities to code candidates, so Codex's own file inspections inside its tool-calling loop provided the in-session evidence; the dialogue is grounded in spec excerpts and code line references Codex quoted directly).

## Pipeline Data
```json
{
  "dialogue_id": "019d9811-b052-7163-b5e2-e91b9db26ffb",
  "turns_completed": 5,
  "turn_budget": 6,
  "posture": "evaluative",
  "seed_confidence": "low",
  "reasoning_effort": "high",
  "total_claims": 27,
  "reinforced": 0,
  "revised": 0,
  "conceded": 0,
  "unresolved_open": 0,
  "unresolved_closed": 5,
  "delta_sequence": ["advancing", "advancing", "advancing", "advancing", "advancing"],
  "converged": true,
  "convergence_reason_code": "all_unresolved_closed_before_budget",
  "termination_reason": "clean_exit",
  "evidence_count": 0,
  "scope_breach_count": 0,
  "closing_probe_fired": false,
  "mode": "server_assisted",
  "ccdi": {"status": "removed"}
}
```

## Key Spec/Code Paths Referenced
- `/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/advisory-runtime-policy.md` (rotation semantics, narrowing rule, reap conditions, mid-turn prohibition)
- `/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/foundations.md` (advisory domain, prose policy defaults)
- `/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/delivery.md` (MCP serialization assumption)
- `/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/contracts.md` (audit schema, handle mapping)
- `/Users/jp/Projects/active/claude-code-tool-dev/docs/superpowers/specs/codex-collaboration/recovery-and-journal.md` (journal fields, crash recovery path)
- `/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/control_plane.py` (widening rejection, hardcoded fingerprint)
- `/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/runtime.py` (runtime startup literals)
- `/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/profiles.py` (profile-carried sandbox/approval fields — the two-channel ambiguity)
- `/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/lineage_store.py` (append-only last-wins, no CAS)
- `/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/mcp_server.py` (thin tool schema, serialized dispatch)
- `/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/models.py` (ConsultRequest surface)
- `/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/dialogue.py` (turn-sequencing dependency on serialized admission)
