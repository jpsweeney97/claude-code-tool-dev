# T-20260327-01: R1 carry-forward debt triage

```yaml
id: T-20260327-01
date: 2026-03-27
status: closed
priority: medium
tags: [codex-collaboration, r1, hardening]
blocked_by: []
blocks: []
effort: medium
closed_date: '2026-04-12'
closed_reason: >-
  Umbrella triage complete. Items 6-7 resolved (T-20260330-01, e6792de8).
  Items 1-5 intentionally parked pending R2/delegation/advisory-widening
  triggers. Re-enter scope via new targeted tickets when triggers fire.
```

## Context

R1 runtime milestone merged to main at `3490718a` (2026-03-27). The following items were identified during spec-grounded R1 code review and explicitly deferred. This ticket converts them from handoff-only notes into durable backlog artifacts.

Source: R1 handoff document, review findings #1-10, downstream risks A-E.

## Items

| # | Item | Code Location | Severity | Classification | Rationale |
|---|---|---|---|---|---|
| 1 | Bootstrap-required method assertions | `runtime.py:29-33,52`; `control_plane.py:243,260` — calls `initialize`/`account/read` without asserting in `REQUIRED_METHODS` | Medium | Parked | Dialogue doesn't change the bootstrap path. These methods are called before any capability-specific code. |
| 2 | Process orphan cleanup | `jsonrpc_client.py` — no `__del__`, no `__enter__`/`__exit__`, no `atexit.register()`. Relies on explicit `close()`. | Low | Parked | Invalidation-on-failure from R1 reduces practical orphan damage. Same risk profile for dialogue. |
| 3 | Concurrent consult safety | `control_plane.py:65` — `_advisory_runtimes` dict has no `threading.Lock`. Multiple `.get()`, `[]`, `.pop()` without synchronization. | Low | Parked | R2 MCP server uses serialized dispatch (one tool call at a time). Concurrent safety is not needed while serialization invariant holds. Revisit only if serialization is relaxed. |
| 4 | `AuditEvent` schema expansion | `models.py:149-151` — missing `job_id`, `request_id`, `artifact_hash`, `decision`, `causal_parent`. Currently uses `extra: dict[str, Any]`. | Deferred | Parked | Dialogue events only need existing fields (`collaboration_id`, `runtime_id`, `turn_id`). Add delegation-specific fields before delegation events land. |
| 5 | Policy fingerprint parameterization | `control_plane.py:346-357` — `build_policy_fingerprint()` uses hardcoded material dict (`transport_mode`, `sandbox_level`, etc.). | Deferred | Parked | Blocks advisory widening, not dialogue. No change needed for R2. |
| 6 | Redaction pattern coverage | `context_assembly.py` `_redact_text()` — ordered redaction now covers AWS `AKIA*`, GitHub `ghp_`/`gho_`/`ghs_`/`ghr_`, Basic auth headers, and URL userinfo with false-positive regressions. | Medium | **Closed** → `T-20260330-01` | Shared assembly path for dialogue and consultation hardened and verified in the dedicated ticket. |
| 7 | Non-UTF-8 file read hardening | `context_assembly.py` `_read_file_excerpt()` — `read_text(encoding="utf-8")` without decode error handling. Binary file reference crashed the entire assembly pipeline. | Medium | **Closed** → `e6792de8` | Fixed: byte-prefix sniff + UnicodeDecodeError catch returns `_BINARY_PLACEHOLDER`. 216 tests passing. |

## Classification Key

| Classification | Meaning | Action |
|---|---|---|
| **Parked** | Not a pre-dialogue blocker. Revisit when the relevant capability enters scope or the risk profile changes. | No action before R2. |
| **Existing gap** (historical) | Affects all context assembly equally (dialogue and consultation). Pre-resolution classification for items 6 and 7 that triggered the T4 decision gate. | Superseded — items 6 and 7 resolved to Promoted or Closed on 2026-03-30. |
| **Promoted** | Assessed at T3/T4 decision gate and moved to a dedicated ticket. | Track in the referenced ticket. |
| **Closed** | Fixed and verified in the repository state. | No further action. |

## Decision Gate (T4 input) — Resolved 2026-03-30

Both items classified as **existing gap** (items 6 and 7) were assessed against shared context assembly paths and selected for action:

- **Item 7** closed immediately as standalone bugfix (`e6792de8`). Binary/non-UTF-8 references now return a placeholder instead of crashing the packet.
- **Item 6** was promoted to `T-20260330-01` and is now closed there after the targeted redaction hardening was implemented and verified.

## Release Posture — R1/R2 Dev-Repo Internal Use

`Parked` remains the backlog classification for items 1-5. The table below is the
explicit release acceptance for the current rollout target: R1/R2 internal use
from the dev repo, not packaged-plugin rollout. If an invalidation trigger fires,
re-review the item before shipping the triggering change.

| Item | Accepted risk | Blast radius if undetected | Invalidation trigger | Re-review condition | Owner |
|------|---------------|----------------------------|----------------------|---------------------|-------|
| 1 | Missing explicit bootstrap assertions are accepted while advisory runtime bootstrap still depends only on `initialize` and `account/read`, both of which already fail closed via live checks. | Startup can fail later or with less precise diagnostics if a new bootstrap-critical method is added without tightening the bootstrap contract. | Any new App Server method becomes required before the advisory runtime is considered usable. | Any change to the bootstrap sequence in `ControlPlane._probe_runtime()` or equivalent startup flow. | Author of the bootstrap-surface change |
| 2 | Explicit `close()` plus invalidation-on-failure is accepted for short-lived internal sessions. | Orphaned local app-server processes can survive until process exit or manual cleanup. | Process ownership, shutdown semantics, or recovery assumptions change. | Any change to `JsonRpcClient` lifecycle management or to how runtimes are retained across sessions. | Author of the lifecycle change |
| 3 | No locking is required while MCP dispatch remains serialized and dialogue turn sequencing relies on that invariant. | Advisory runtime cache access and turn sequencing can race, producing duplicate or misordered turns. | Tool dispatch stops being single-threaded or concurrent advisory turns become possible. | Any change to MCP dispatch serialization or dialogue turn-sequence derivation assumptions. | Author of the dispatch-model change |
| 4 | The minimal `AuditEvent` shape is accepted while only `consult` and `dialogue_turn` events are first-class. | New audit event families can ship with under-specified structure and become hard to query or export consistently. | A new audit action needs typed fields beyond `extra`, or an external consumer depends on richer schema. | The first non-`consult`/`dialogue_turn` audit producer or audit-consumer feature. | Author of the audit-surface change |
| 5 | Hardcoded policy fingerprint inputs are accepted while advisory runtime policy remains read-only, no-network, approval=`never`, and reuse semantics stay unchanged. | Advisory runtime reuse can become unsound if the effective policy widens without invalidating the cached fingerprint. | Advisory widening or any change to the policy input surface or reuse semantics. | Any change to `request.network_access` handling, runtime approval/sandbox settings, or `build_policy_fingerprint()` material. | Author of the policy-surface change |

## Acceptance Criteria

- [x] All 7 items have a classification (parked, promoted, or closed)
- [x] Any items promoted to pre-dialogue blockers are noted for T4 scope inclusion
- [x] This ticket replaces handoff-only tracking — the handoff is archived (R1 handoff archived at `docs/handoffs/archive/`)

## Resolution Log

| Date | Item | Action | Reference |
|------|------|--------|-----------|
| 2026-03-30 | Item 7 | Closed — binary file hardening landed | `e6792de8` |
| 2026-03-30 | Item 6 | Promoted to `T-20260330-01` | Targeted redaction hardening |
| 2026-03-30 | Item 6 | Closed via `T-20260330-01` | Ordered redaction, structural replacements, and false-positive regressions implemented |
| 2026-03-30 | Items 1-5 | Remain parked | No change in risk profile |
