# codex-collaboration Current State

Last updated: 2026-04-29

## Start Here

Start here for current state.

This document is the canonical reader entry point for the current
`codex-collaboration` project state in this repo.

This document is **not** a behavioral tie-breaker. If a claim here conflicts
with the underlying owner documents or current code/tests, the underlying owner
artifacts win.

## Reader Routing

- **Current state / project orientation:** this document
- **Open or unreconciled work:** [codex-collaboration reconciliation register](./codex-collaboration-reconciliation-register.md)
- **Behavioral truth / contract ownership:** the owner documents under
  `docs/superpowers/specs/codex-collaboration/`, per the authority map in
  [`spec.yaml`](../superpowers/specs/codex-collaboration/spec.yaml)
- **Implementation truth:** `packages/plugins/codex-collaboration/` code and tests
- **Supporting audit evidence:** diagnostics, closed-ticket closeout evidence, and
  assessment-layer documents

Do not infer open/closed truth from directory placement under `docs/tickets/`
alone. Use ticket front matter, the reconciliation register, closeout notes, and
current code together.

## Authority Owners

Behavioral claim ownership comes from
[`docs/superpowers/specs/codex-collaboration/spec.yaml`](../superpowers/specs/codex-collaboration/spec.yaml).

| Authority owner | Owns | Primary artifact(s) |
|---|---|---|
| `foundation` | Architecture rules, domains, trust model, terminology | `foundations.md` |
| `contracts` | MCP surface, data models, typed responses, audit schema | `contracts.md` |
| `promotion-contract` | Promotion preconditions, state machine, rollback semantics | `promotion-protocol.md` |
| `advisory-policy` | Advisory lifecycle, widening/narrowing/rotation policy | `advisory-runtime-policy.md` |
| `recovery-contract` | Journal, audit-log behavior, crash recovery, concurrency | `recovery-and-journal.md` |
| `delivery` | Build sequence, deployment profile, compatibility, test strategy | `delivery.md` |
| `decisions` | Locked design decisions and open design questions | `decisions.md` |
| `supporting` | Overview and supporting evidence only | `README.md`, evidence maps, rewrite maps |

`docs/status/` is a synthesis/routing layer. It can summarize current truth and
reader guidance, but it does not outrank the owner documents above.

## Implemented Now

The live implementation surface currently includes:

- `codex.status`
- `codex.consult`
- `codex.dialogue.start`
- `codex.dialogue.reply`
- `codex.dialogue.read`
- `codex.delegate.start`
- `codex.delegate.poll`
- `codex.delegate.decide`
- `codex.delegate.promote`
- `codex.delegate.discard`

Related shipped operator surfaces include:

- `/consult-codex`
- `/delegate`
- `/codex-status`
- `/codex-review`
- `/codex-analytics`

At a high level:

- advisory consultation and dialogue are live,
- dialogue is durable but **does not** currently expose `codex.dialogue.fork`,
- delegation runs in an isolated worktree with promotion-gated apply,
- analytics and review surfaces are present,
- execution sandbox default uses `includePlatformDefaults: True`.

For implementation details, start from:

- `packages/plugins/codex-collaboration/server/mcp_server.py`
- `packages/plugins/codex-collaboration/server/dialogue.py`
- `packages/plugins/codex-collaboration/server/delegation_controller.py`
- `packages/plugins/codex-collaboration/server/runtime.py`

## Intentionally Deferred Or Not Yet Implemented

The following remain intentionally deferred or not yet implemented:

- dialogue branching via `seed_from` on `codex.dialogue.start` (copy-and-diverge; `codex.dialogue.fork` as a standalone tool is permanently replaced — see [decisions.md §Dialogue Fork Scope](../superpowers/specs/codex-collaboration/decisions.md#dialogue-fork-scope))
- advisory widening / narrowing / rotation behavior as live implementation
- phased consultation profiles
- broader structured MCP error reasons for certain delegation failures
- fully classified support or intentional handling for currently unsupported App
  Server request kinds

Use the reconciliation register for the current list of active unresolved work
and exit conditions.

## Active Current-State Watchpoints

The main current watchpoints are:

- delegation friction reduction (`T-20260429-01`)
- unsupported App Server request reachability / handling (`T-20260429-02`)
- Packet 1 carry-forward debt (`TT.1`, `RT.1`, `P1-MINOR-SWEEP`)
- benchmark-carried follow-on work (`BMARK-L1-L3`)
- open spec question `AUDIT-CONSUMER-INTERFACE`

This document names the categories only. Use the reconciliation register for the
current-truth summaries, owning artifacts, and exit conditions.

## Status-Layer Conventions

If a future status or drift artifact records findings, separate:

- `authority_owner`: one of the owner classes from `spec.yaml`
- `drift_type`: what kind of mismatch or debt exists
- `repair_target`: the exact file or artifact class that should change
- `evidence_basis`: recommended (`code`, `tests`, `live-diagnostic`,
  `normative-doc`, `supporting-doc`, or `mixed`)

Do not collapse owner and drift type into one field.
