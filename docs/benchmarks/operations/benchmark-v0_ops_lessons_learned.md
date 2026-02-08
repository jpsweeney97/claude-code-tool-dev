# Benchmark v0 — Lessons Learned (Rolling)

This document is a **rolling log** of practical lessons learned while executing Benchmark v0.

It is intentionally **non-normative**:
- It does **not** change the benchmark procedure.
- It does **not** override the suite/framework/ops manual.
- It records operational gotchas, drift patterns, common failure modes, and mitigations.

Canonical procedure lives in:
- `docs/benchmarks/operations/benchmark-v0_ops_v0.1.0.md`

---

## 2026-02-08 — Escalate leakage reads to REPAIR-required

**Context:** `v0-rubric-report-005` baseline replicates (`run-1`, `run-2`) during execution phase.
**Symptom:** Executor read disallowed same-run artifacts (`report.md`, `scores.md`) while generating rubric-run output.
**Impact:** Increased anchoring risk and reduced replicate independence; observed output can drift toward existing artifact structure.
**Root cause (best guess):** Prompt language treated leakage reads as “record confounder” but not as an acceptance blocker.
**Mitigation:** In orchestrator handoffs/prompts, hard-fail leakage policy: any disallowed read => mark run `REPAIR_REQUIRED`, do not accept, re-run same scenario/condition/replicate.
**Decision:** Canonical ops manual unchanged; stricter enforcement applied at orchestration layer effective immediately.
**Links:** `docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/run-records/v0-rubric-report-005__baseline__run-1.md`, `docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/run-records/v0-rubric-report-005__baseline__run-2.md`, `docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/handoff.md`, `docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/handoff_codex.md`

---

## Entry Template

Add new entries at the top (reverse-chronological):

```md
## YYYY-MM-DD — <short title>

**Context:** <scenario(s) / phase / what was happening>
**Symptom:** <what went wrong or was surprising>
**Impact:** <why it matters to measurement integrity or ops reliability>
**Root cause (best guess):** <brief>
**Mitigation:** <what to do next time>
**Decision:** <did we change procedure? if no, why not>
**Links:** <run record(s) / handoff / commits if relevant>
```
