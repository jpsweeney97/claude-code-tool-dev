> **Status: CLOSED** — Benchmark-specific. Tier A closed.

# Decision Record: Orchestrator Session Reset Strategy

**Date:** 2026-02-08
**Status:** Decided
**Stakes:** Rigorous
**Decision:** How to recover safely when Codex/orchestrator session resets to zero context

## Context

Both Claude executor sessions and Codex orchestrator sessions can reset and lose in-memory context.
The benchmark must continue deterministically from on-disk state, without relying on prior chat memory.

Key constraints:
- Orchestrator role must remain orchestrator-only.
- Next action must remain deterministic and reproducible.
- Leakage/acceptance gates must remain enforceable after reset.
- Human overhead should stay low during repeated resets.

## Options Evaluated

### Option A — Fully Stateless Orchestrator (Recommended)

Treat every orchestrator turn as if it started from zero memory:
- Run `scripts/benchmark_v0_resume`
- Verify latest run record from disk against acceptance gates
- Update handoffs from disk truth
- Generate exactly one executor prompt from current handoff state

**Pros**
- Highest correctness and reproducibility
- Reset-proof by design
- Minimizes hidden state bugs

**Cons**
- Slightly more repeated verification work each cycle

### Option B — Stateful Orchestrator with Manual Recap

Rely mostly on chat memory and ask user for recap after reset.

**Pros**
- Fast when memory is intact

**Cons**
- Fragile to recap omissions
- Higher drift risk and acceptance mistakes

### Option C — Semi-Stateless with Compact Bootstrap Packet

Keep Option A, plus a tiny reset bootstrap checklist in `handoff_codex.md` (commands + acceptance checks + where to read next action).

**Pros**
- Same safety as Option A
- Lower startup friction on reset

**Cons**
- One extra artifact to maintain

### Option D — External Run State Database

Track orchestration state in a separate database/service.

**Pros**
- Strong auditability at scale

**Cons**
- Unnecessary complexity for current benchmark scope
- More failure modes and maintenance overhead

## Recommendation

Adopt **Option C (Semi-Stateless with Compact Bootstrap Packet)**:
- Operational behavior remains fully stateless (Option A).
- Add a small, explicit reset bootstrap checklist for speed and consistency.

This balances reliability and operator efficiency while preserving deterministic behavior.

## Required Invariants for Reset-Safe Operation

1. **Disk is truth:** suite + run records + scoped git diff checks.
2. **No chat-memory dependence:** every cycle re-derives next step from disk.
3. **Single-run cadence:** one tuple (or one REPAIR tuple) per cycle.
4. **Role isolation:** Codex orchestrates/verifies only; Claude executes/evaluates in separate sessions.
5. **Acceptance-gate authority:** acceptance/repair outcome overrides naive progression signals.

## Implementation Notes

- Keep using:
  - `scripts/benchmark_v0_resume` for candidate next action
  - On-disk run-record verification commands before acceptance
  - `handoff.md` and `handoff_codex.md` as reset bootstrap artifacts
- If `resume` disagrees with acceptance gate outcomes (e.g., rejected leakage run), re-queue REPAIR tuple and do not advance.

## Trade-offs Accepted

- Extra orchestration verification steps on each cycle.
- Slightly slower per-cycle throughput in exchange for significantly stronger integrity.
