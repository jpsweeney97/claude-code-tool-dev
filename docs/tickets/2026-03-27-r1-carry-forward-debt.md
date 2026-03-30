# T-20260327-01: R1 carry-forward debt triage

```yaml
id: T-20260327-01
date: 2026-03-27
status: open
priority: medium
tags: [codex-collaboration, r1, hardening]
blocked_by: []
blocks: []
effort: medium
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
