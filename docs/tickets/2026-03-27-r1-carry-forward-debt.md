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
| 6 | Redaction pattern coverage | `context_assembly.py:40-45` — 4 patterns (OpenAI `sk-*`, Bearer, PEM, `password=`). Missing: AWS `AKIA*`, GitHub `ghp_`/`gho_`/`github_pat_`, base64 credentials. | Medium | Existing gap | Same assembly path for dialogue and consultation. Not dialogue-specific, but a token in context assembly leaks regardless of capability. |
| 7 | Non-UTF-8 file read hardening | `context_assembly.py:345` — `read_text(encoding="utf-8")` without `try/except UnicodeDecodeError`. Binary file reference crashes the entire assembly pipeline. | Medium | Existing gap | Same assembly path for dialogue and consultation. A user referencing a binary file (image, compiled asset) crashes assembly for any capability. |

## Classification Key

| Classification | Meaning | Action |
|---|---|---|
| **Parked** | Not a pre-dialogue blocker. Revisit when the relevant capability enters scope or the risk profile changes. | No action before R2. |
| **Existing gap** | Affects all context assembly equally (dialogue and consultation). Not dialogue-specific, but the risk exists today. | Fix opportunistically or add to R2 scope at T4 decision gate. |

## Decision Gate (T4 input)

Before freezing R2 scope in T4, review items classified as **existing gap** (items 6 and 7):

- If the team judges that either gap undermines trustworthy context assembly enough to warrant pre-dialogue fixing, promote it to R2 scope.
- If neither is promoted, they remain here as open backlog items with no milestone assignment.

## Acceptance Criteria

- [ ] All 7 items have a classification (parked or existing gap)
- [ ] Any items promoted to pre-dialogue blockers are noted for T4 scope inclusion
- [ ] This ticket replaces handoff-only tracking — the handoff is archived
