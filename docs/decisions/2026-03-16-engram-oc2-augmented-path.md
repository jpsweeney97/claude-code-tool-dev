# Engram: OC2-Augmented Path over Full Consolidation

## Context

- **Decision trigger:** Adversarial review of the Engram design spec surfaced 6 [serious] issues, including a viable alternative (OC2) that was never formally evaluated.
- **Stakes level:** Rigorous — architectural decision affecting three production plugins (handoff, ticket, learning pipeline) with 950+ combined tests.
- **Decision process:** Adversarial review → review validation → Codex dialogue (6 turns, collaborative, converged) → architecture proof (Step 0A).

## Decision

**Adopt the OC2-augmented path: shared `engram_core` library + search plugin + Context identity retrofit.** Defer full consolidation to Phase 2, contingent on multi-plugin composition pain materializing.

### What OC2-augmented means

| Component | Action |
|-----------|--------|
| `engram_core` library | New shared package: identity (repo_id, worktree_id), types (RecordRef, RecordMeta, RecordStub), reader protocol, query engine |
| `engram-search` plugin | New thin plugin: `/search` and `/timeline` across installed plugins via NativeReaders |
| Context identity retrofit | Re-key handoff storage from project-name to repo_id (22 non-test references, 5 files) |
| Work subsystem | **Untouched.** Ticket engine stays in its own plugin. No transplant. |
| Knowledge subsystem | Adopt RecordRef for learnings. No structural changes to storage. |

### What is deferred to Phase 2

Full consolidation into a single Engram plugin — merging handoff, ticket, and learning into one package with unified hooks and storage. Phase 2 only proceeds if multi-plugin composition creates measurable friction.

## Rationale

### Core insight: the spec collapses two separable decisions

The Engram design spec bundles (1) shared identity/query contracts with (2) physical consolidation of plugins/storage/hooks. The adversarial review and Codex dialogue independently identified that codebase evidence supports the first but not the second.

Most [serious] review findings cluster around consolidation — ticket pipeline transplant risk (A4), test triage subjectivity (F1), chain state migration (U3). The shared-contracts decision carries none of these risks.

### Architecture proof confirmed feasibility

Step 0A tested `engram_core` imports from 5 execution contexts including simulated installed-cache runtime. All passed. The `sys.path.insert(0, plugin_root)` pattern used by existing scripts extends cleanly to hooks. The Context identity retrofit is small (22 non-test references, 5 files).

Full proof: `docs/plans/2026-03-16-engram-architecture-proof.md`

### Decision rule outcome

| Gate | Result | Evidence |
|------|--------|----------|
| Gate 1 (installed-cache import) | PASS | 5/5 contexts pass |
| Gate 3 (Context retrofit scope) | SMALL | 22 refs, 5 files |

→ **Branch 1:** OC2-augmented, single phase.

## Review Finding Dispositions

| ID | Finding | Severity | Disposition |
|----|---------|----------|-------------|
| A3 | `engram_core` import path from hooks | [serious] | **Resolved** — architecture proof demonstrates `sys.path.insert(0, plugin_root)` works in all contexts including installed-cache. Follow ticket guard's dual-resolution pattern: `os.environ.get("CLAUDE_PLUGIN_ROOT", str(Path(__file__).parent.parent))`. |
| A4 | Ticket pipeline transplant risk | [serious] | **Avoided** — Work subsystem stays untouched under OC2-augmented. No ticket engine transplant needed. |
| F1 | Compatibility harness test triage subjectivity | [serious] | **Deferred to Phase 2** with anti-subjectivity rules locked in (see below). No harness needed for OC2-augmented. |
| F4 | Shadow authority via `snippet` in skill reasoning | [serious] | **Addressed in Phase 1** — split IndexEntry into RecordStub (machine-facing, no freeform text) and RecordPreview (display-only snippet, optional). Query API defaults to `include_preview=False`. |
| U1 | `engram_core` importability from all execution contexts | [serious] | **Resolved** — same as A3. |
| U7 | Guard "engine entrypoints only" detection mechanism | [serious] | **Resolved by design** — each subsystem keeps its own guard (ticket guard stays, handoff gets one if needed). No unified `engram_guard` needed. Single point of failure avoided. |
| OC2 | Shared library alternative not evaluated | [serious] | **Adopted** as primary path. This ADR is the formal evaluation. |

### Remaining findings (not [serious])

| ID | Severity | Status |
|----|----------|--------|
| A1 | [moderate] | Mitigated — OC2 preserves independent evolution; subsystems can diverge without constraint |
| A2 | [moderate] | Accepted — fresh-scan indexing at MVP scale; instrument query latency from Step 1 |
| A5 | [moderate] | Mitigated — Context retrofit is small and well-scoped; legacy read path for old handoffs |
| A6 | [minor] | Accepted — Bash protection remains best-effort; documented, not in success criteria |
| F2 | [minor] | Accepted — `/save` partial failure UX is inherent to orchestration |
| F3 | [moderate] | Mitigated — `/triage` reports staging backlog; session cap limits accumulation |
| U2 | [moderate] | Deferred — `.engram-id` commit mechanics specified in Phase 1 spec |
| U3 | [moderate] | Avoided — no bulk migration; backward-compatible read for legacy handoffs |
| U4 | [minor] | Deferred — `/curate` interaction model designed during implementation |
| U5 | [moderate] | Deferred — worktree_id lifecycle specified in Phase 1 spec |
| U6 | [minor] | Deferred — ledger event schema designed when `/timeline` is implemented |
| OC1 | [moderate] | Accepted — incremental improvement path remains open under OC2 |
| SE1-4 | [minor] | Mitigated — independent plugins avoid single point of failure and coupling incentives |

## Anti-Subjectivity Rules for Phase 2 Test Triage

If Phase 2 proceeds (full consolidation), the ticket engine transplant will require triaging ~596 tests. These rules prevent subjective judgment from creating silent behavioral regressions:

### Automatic compatibility-critical classification

Any test touching these areas is **automatically** compatibility-critical. No further justification needed:

- Hook behavior (allow/deny decisions, trust injection)
- Entrypoint validation (payload parsing, schema checks)
- Trust triple mechanics (`session_id`, `hook_injected`, `hook_request_origin`)
- Audit trail side effects (JSONL append, session grouping)
- Autonomy policy re-reads at execute time
- Dedup behavior (fingerprint generation, window enforcement, TOCTOU)
- Envelope ingest (version validation, idempotency)

### Exclusion requires written reason

A test can only be classified as "implementation-local" (don't port) with a written reason from this allowed set:

1. Tests internal data structure layout that has no behavioral contract
2. Tests a code path that will be deleted (not replaced) in the new engine
3. Tests Python-version-specific behavior irrelevant to the new implementation

"Implementation-local" is **not** a valid exclusion reason by itself. The default is compatibility-critical.

## Evidence

| Artifact | Path |
|----------|------|
| Adversarial review | `docs/reviews/adversarial-review-engram-design.md` |
| Engram design spec | `docs/superpowers/specs/2026-03-16-engram-design.md` |
| Architecture proof | `docs/plans/2026-03-16-engram-architecture-proof.md` |
| Codex dialogue | Thread `019cf963-4a83-7f40-b71f-8c0eeb8f1a0a` (6 turns, converged) |

## Status

**Accepted.** Proceed with Phase 1 spec.
