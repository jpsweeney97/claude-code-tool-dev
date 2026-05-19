# External-Consumer Survey — `docs/handoffs` References

**Date:** 2026-05-19
**Context:** One-time Codex→Claude port of the `handoff` plugin (Task 9 of 11). Task 6 hard-migrated
the live corpus from `docs/handoffs/` → `.claude/handoffs/` (161 files). `docs/handoffs/` is now
an empty gitignored dir. The plugin itself is AC2-clean and was NOT surveyed here.

**AC2 clause satisfied:** "Every `docs/handoffs` hit OUTSIDE the plugin … is remediated to
`.claude/handoffs/` OR explicitly recorded as intentionally legacy-pointing."

**Survey command:**
```
rg -n 'docs/handoffs' . --glob '!docs/handoffs/**' --glob '!packages/plugins/handoff/**' --glob '!.git/**'
```
Plus: `rg -n 'docs/handoffs' ~/.claude/projects/.../memory/` (user auto-memory, reported only).

---

## Classification Rubric

- **(a) Live operational pointer** — actively prescribes `docs/handoffs/` for CURRENT use. Retargeted to `.claude/handoffs/`.
- **(b) Historical record / intentionally legacy-pointing** — describes past state, narrates the migration, or is immutable evidence. Left verbatim; recorded here.
- **(c) Ambiguous / closed-artifact** — no operational force, cannot cleanly decide. Left verbatim; noted.

---

## Survey Results — 30 Files, 361 Hits

*(29 repo files + 1 user auto-memory file outside the repo)*

---

### Class (a) — Live Operational Pointer → RETARGETED (2 files)

| File | Line(s) | Before | After | Rationale |
|------|---------|--------|-------|-----------|
| `extensions/skills/changelog/SKILL.md` | 174 | `<project_root>/docs/handoffs/archive/` | `<project_root>/.claude/handoffs/archive/` | Inline Handoff Archivist agent prompt instructs a Claude subagent to open that directory NOW during changelog generation. With corpus in `.claude/handoffs/archive/`, the live agent would find nothing if this stays `docs/handoffs/`. |
| `extensions/skills/changelog/references/entry-writing.md` | 55 | `$(git rev-parse --show-toplevel)/docs/handoffs/archive` | `$(git rev-parse --show-toplevel)/.claude/handoffs/archive` | Shell variable `ARCHIVE_DIR` executed in live changelog skill context — directly read by `ls` and `grep -l` in the code block immediately below. Would silently return empty results post-migration. |

---

### Class (b) — Historical Record / Intentionally Legacy-Pointing → LEFT VERBATIM (27 files)

| File | Hit count | Rationale |
|------|-----------|-----------|
| `scripts/m1_migrate.sh` | 3 | The M1 migration script itself. Operates on `docs/handoffs/` as source — that's its entire purpose. A rollback/replay artifact for a one-shot move that already ran. Changing it would break rollback fidelity. |
| `scripts/m1_rollback.sh` | 2 | The M1 rollback script. Reverse-maps `.claude/handoffs/` → `docs/handoffs/` from the manifest. Same reasoning — migration infrastructure, must stay verbatim. |
| `packages/plugins/handoff-port-manifests/M1-premove-manifest.txt` | ~161 | Pre-move SHA256 checksums with literal `docs/handoffs/` paths from the corpus snapshot. Immutable integrity evidence; altering it would corrupt rollback verification. |
| `docs/superpowers/plans/2026-05-19-handoff-codex-port.md` | ~35 | The port master plan itself. Describes the migration architecture, Decision 5/6, and the very move that is being surveyed here. Intentionally narrates the `docs/handoffs/` → `.claude/handoffs/` transition. |
| `docs/tickets/2026-05-19-handoff-codex-port.md` | ~15 | Port ticket describing AC2 scope, Decision 5/6 rationale, and survey requirements. Narrates the migration. |
| `docs/superpowers/plans/2026-03-29-handoff-docs-storage-migration.md` | ~75 | Implementation plan for the 2026-03-29 `.claude/handoffs/` → `docs/handoffs/` migration (the previous storage move, now fully superseded). Historical record; fully executed and complete. |
| `docs/superpowers/specs/2026-03-29-handoff-docs-storage-design.md` | ~35 | Design spec for the 2026-03-29 migration. Historical. |
| `docs/superpowers/plans/2026-04-10-handoff-no-commit.md` | ~55 | Implementation plan for the 2026-04-10 gitignore + auto-commit removal. Historical; executed. |
| `docs/superpowers/specs/2026-04-10-handoff-no-commit-design.md` | ~30 | Design spec for the no-commit refactor. Historical. |
| `docs/superpowers/plans/2026-05-01-handoff-summary-type.md` | ~10 | Implementation plan for the summary handoff type, written when `docs/handoffs/` was the active path. Historical; feature already implemented with the old path and now superseded by the port. |
| `docs/superpowers/specs/2026-05-01-handoff-summary-type-design.md` | 3 | Design spec for the summary type. Same reasoning. |
| `docs/superpowers/specs/2026-03-31-persistence-hardening-and-type-narrowing-design.md` | 1 | Single reference to an archived handoff file path as an example. Historical. |
| `docs/superpowers/plans/2026-05-07-public-skills-repo-build.md` | 1 | Single hit inside a `rg` decontamination grep pattern used to scan for private paths. The pattern `docs/handoffs` appears as a string in an inline shell command designed to detect accidental private-path leakage in a public repo. Historical plan artifact; the grep pattern is not operational in this repo. |
| `docs/superpowers/specs/2026-05-06-public-skills-repo-design.md` | 1 | Same `rg` decontamination pattern as above. Historical spec. |
| `docs/plans/2026-04-23-t07-cross-model-removal-7e.md` | 3 | T07 cross-model removal plan. References `docs/handoffs/archive/` as a path description in a scope table and an rg exclusion glob. Historical; T07 is closed. |
| `docs/plans/04-29-2026-reconcile-active-stale-codex-collaboration-artifacts-to-current-repo-truth.md` | 2 | Plan for reconciling codex-collaboration artifacts; lists `docs/handoffs/**` in a scope exclusion table. Historical; executed plan. |
| `docs/benchmarks/dialogue-supersession/v1/transcripts/B1-baseline-transcript.md` | 1 | Benchmark transcript — immutable scored evidence. Contains model output from when `docs/handoffs/` was the active path. Do not modify. |
| `docs/benchmarks/dialogue-supersession/v1/transcripts/B1-candidate-transcript.md` | 1 | Same; benchmark transcript. |
| `docs/benchmarks/dialogue-supersession/v1/transcripts/B3-baseline-transcript.md` | 1 | Same; benchmark transcript. |
| `docs/benchmarks/dialogue-supersession/v1/transcripts/B3-candidate-transcript.md` | 1 | Same; benchmark transcript. |
| `docs/benchmarks/dialogue-supersession/v1/transcripts/B5-baseline-transcript.md` | 2 | Same; benchmark transcript. |
| `docs/benchmarks/dialogue-supersession/v1/transcripts/B5-candidate-transcript.md` | 2 | Same; benchmark transcript. |
| `docs/benchmarks/dialogue-supersession/v1/transcripts/B8-baseline-transcript.md` | 2 | Same; benchmark transcript. |
| `docs/benchmarks/dialogue-supersession/v1/transcripts/B8-candidate-transcript.md` | 2 | Same; benchmark transcript. |
| `docs/discussions/simulation-based-assessment-framework-discussion-part-01-turns-01-10.md` | 2 | Discussion transcript from a prior benchmarking session. Immutable evidence record. |
| `docs/frameworks/simulation-based-skill-assessment_v0.2.0.md` | 1 | Framework doc referencing an archived handoff by path as an example. The path was accurate when written; the framework is not operationally driven by the handoff location. Historical. |
| `docs/tickets/closed-tickets/2026-03-27-r1-carry-forward-debt.md` | 1 | Closed ticket with a parenthetical noting the R1 handoff was archived at `docs/handoffs/archive/`. Historical closure note. |

#### User Auto-Memory (outside repo — NOT edited, user-owned)

| File | Line | Rationale |
|------|------|-----------|
| `~/.claude/projects/.../memory/feedback_no_midtrack_doc_commits.md` | 21 | Auto-memory entry noting that handoff saves write to `docs/handoffs/` (describing the then-current behavior at time of writing). User-owned file outside the repo; per task rules, classified here and recorded only. |

---

### Class (c) — Ambiguous / Closed-Artifact → NONE

No files required (c) classification. All hits were cleanly decidable as (a) or (b).

---

## Summary

| Class | Count | Action |
|-------|-------|--------|
| (a) Live operational pointer | 2 files | Retargeted to `.claude/handoffs/` |
| (b) Historical / intentionally legacy-pointing | 27 files + 1 auto-memory | Left verbatim; recorded above |
| (c) Ambiguous | 0 | — |
| **Total** | **30 files** | |

**Controller-review flags:** None. All classifications were cleanly decidable by the prescribes-now vs describes-past hinge.

**Plugin untouched:** `packages/plugins/handoff/**` was excluded per task scope (already AC2-clean).
