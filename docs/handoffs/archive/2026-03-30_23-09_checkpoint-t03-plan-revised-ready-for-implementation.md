---
date: 2026-03-30
time: "23:09"
created_at: "2026-03-31T03:09:12Z"
session_id: 194fbf9f-4dce-4b09-8f28-855498df3b0e
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-03-30_21-52_t03-safety-substrate-plan-and-architecture-investigation.md
project: claude-code-tool-dev
branch: feature/codex-collaboration-safety-substrate
commit: fbe52554
title: "Checkpoint: T-03 plan revised — ready for implementation"
type: checkpoint
files:
  - docs/superpowers/plans/2026-03-30-codex-collaboration-safety-substrate.md
---

# Checkpoint: T-03 plan revised — ready for implementation

## Current Task

Revising the T-03 safety substrate implementation plan based on user code review. The plan had 7 findings (5 P1, 2 P2) covering wrong hook protocol, schema mismatches, missing wiring, and semantic bugs. All findings have been addressed through 3 review rounds — no P1 blockers remain.

## In Progress

Plan revision is complete. Three review rounds applied to `docs/superpowers/plans/2026-03-30-codex-collaboration-safety-substrate.md`:

**Round 1 (7 findings):** Exit 2 + stderr hook protocol, matcher-group schema with escaped dots, per-match redaction bypass via `match.expand()`, required `repo_root` on learning retrieval wired through `_build_text_entries()`, conditional profile resolution (only when explicitly provided), phased profile explicit rejection, fail-closed on all hook error paths.

**Round 2 (4 findings):** Learnings routed through `_build_text_entries()` not raw `_ContextEntry` (redaction boundary), crash recovery documented as known limitation (None profile state), `LineageStore.get()` not `.load()`, contracts.md + test_models_r2.py updated for 13-field handle.

**Round 3 (2 findings):** `profile` moved to `content_fields` (was in `expected_fields` — bypassed scanning), `DIALOGUE_REPLY_POLICY` aligned to actual schema (removed `repo_root`, `message`, `supplementary_context`), profile-scanning tests added to both Task 4 and Task 5, `FakeRuntimeSession.run_turn()` updated to accept `effort` with `last_effort` capture.

Plan is 2580 lines, 9 tasks + deferred Task 10. No code written yet — all changes are to the plan document.

## Active Files

- `docs/superpowers/plans/2026-03-30-codex-collaboration-safety-substrate.md` — The implementation plan (revised)
- `packages/plugins/codex-collaboration/server/mcp_server.py` — Read for schema verification
- `packages/plugins/codex-collaboration/server/dialogue.py` — Read for shared packet path verification
- `packages/plugins/codex-collaboration/server/context_assembly.py` — Read for redaction boundary analysis
- `packages/plugins/codex-collaboration/tests/test_control_plane.py` — Read for FakeRuntimeSession shape
- `packages/plugins/cross-model/scripts/secret_taxonomy.py` — Read for `check_placeholder_bypass` and `PLACEHOLDER_BYPASS_WINDOW`

## Next Action

Execute the T-03 plan. User's prior preference was subagent-driven execution (dispatch a fresh agent per task with review between tasks). Begin with Task 1 (secret taxonomy port).

## Verification Snapshot

No code changes — plan revision only. Last verification: `wc -l` on plan file = 2580 lines, all task headings and step numbering confirmed sequential via grep.

## Decisions

**Hook protocol: exit 2 + stderr** — Simpler, matches cross-model pattern, fail-closed on every error path. Structured JSON (`hookSpecificOutput.permissionDecision`) rejected because Claude Code ignores JSON on exit 2 and the security boundary benefits from simplicity over structured feedback.

**Conditional profile resolution** — Only resolve and store profile state when `profile_name is not None`. Preserves pre-T-03 behavior for calls without explicit profile. Consult and dialogue follow the same contract: None profile → None stored fields → no effort/posture override.

**Phased profiles explicitly rejected** — `debugging` profile (the only phased profile) raises `ProfileValidationError` instead of silently collapsing to default posture. AC4 covers 8 of 9 profiles; `debugging` available when phase-progression support lands.

**Crash recovery loses profile state (accepted)** — `OperationJournalEntry` has no profile fields. Crash-recovered handles get None for all profile fields. Acceptable: narrow window, same as pre-T-03 baseline, `reply()` handles None gracefully.
