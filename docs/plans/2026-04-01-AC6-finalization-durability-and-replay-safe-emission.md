# AC6 Dialogue Finalization, Replay Safety, and Error Surfacing

## Summary

- Tighten dialogue phase semantics so `completed` means: the remote turn is confirmed and every local artifact that can be durably recorded for that turn has been finalized.
- Use one shared dialogue finalization path across normal reply, startup recovery, and inline repair, with `completed` always written last.
- Make dialogue audit/outcome replay-safe without changing persisted schemas.
- Keep consult asymmetric: no journal changes, no replay-safe scan, best-effort local append only.

## Key Changes

- In [dialogue.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/dialogue.py), add one internal helper for **confirmed dialogue turns**.
  The helper must do, in order:
  1. `TurnStore.write` only if both `context_size` and `turn_sequence` are present.
  2. dialogue audit append-once only if both `runtime_id` and a usable string `turn_id` are present.
  3. dialogue outcome append-once only if both `runtime_id` and a usable string `turn_id` are present.
  4. `write_phase(completed)` last.
- The finalization boundary explicitly includes `TurnStore.write` through `write_phase(completed)`. Any failure in that boundary means `completed` is not written.
- Dialogue replay-safe append helpers live in [journal.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/journal.py) and are dialogue-only:
  - audit dedupe key: `(action, collaboration_id, turn_id)`
  - outcome dedupe key: `(outcome_type, collaboration_id, turn_id)`
  - if the target JSONL file does not exist yet, treat it as empty and append normally.
- `reply()` success path becomes:
  `intent -> run_turn -> dispatched -> finalization helper -> parse`.
  - `parse` still runs only after `completed` is durable.
  - if any step inside the finalization boundary fails after successful `run_turn()`, the entry remains at `dispatched`, the handle becomes `unknown`, and `CommittedTurnFinalizationError` is raised.
  - if `parse` fails after `completed`, raise `CommittedTurnParseError` exactly as today.
- `reply()` `run_turn()` exception path changes to be result-driven rather than blindly setting `unknown` first.
  `_best_effort_repair_turn()` must never raise and must return one of:
  - `unconfirmed`
  - `confirmed_unfinalized`
  - `confirmed_finalized`
- Inline repair semantics:
  - `unconfirmed`: the journal remains at `intent`, the handle is set to `unknown`, and `reply()` re-raises the original `run_turn()` exception.
  - `confirmed_unfinalized`: the remote turn is confirmed, the journal remains at `intent`, the handle is set to `unknown`, and `reply()` raises `CommittedTurnFinalizationError`.
  - `confirmed_finalized`: inline repair finalizes directly from `intent -> completed` with no intermediate `dispatched` write. `reply()` then tries to inline-resume the thread on the fresh runtime and update runtime/thread IDs. If resume succeeds, keep the handle `active`. If resume fails, log it and leave the handle `unknown`. In both cases, raise `CommittedTurnFinalizationError`, not the original `run_turn()` exception.
- Startup recovery uses the same finalization helper after `thread/read` confirmation.
  - Confirmed entries may finalize from either `intent -> completed` or `dispatched -> completed`, depending on the current terminal phase.
  - If recovery finalization fails, log it, leave the current unresolved phase unchanged, and mark the handle `unknown`. Do not write `completed`.
- Outcome timestamp rules:
  - normal reply outcome timestamp remains append-time via current journal timestamp.
  - recovery/repair outcome timestamp must use `completed_turns[turn_index].get("createdAt")` when that value is a non-empty string; otherwise fall back to `entry.created_at`.
  - audit timestamp stays append-time in all paths. This asymmetry is intentional: audit records when the trust-boundary event was recorded locally, while outcome records the turn completion time for analytics.
- In [control_plane.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/codex-collaboration/server/control_plane.py), keep consult stateless:
  - use raw `append_audit_event` / `append_outcome`, not replay-safe scan helpers;
  - wrap audit and outcome appends in separate best-effort logging blocks so failure in one does not suppress the other or block `ConsultResult`.

## Public API / Type Changes

- Add `CommittedTurnFinalizationError` as the committed-turn, non-parse error surfaced by `reply()`.
- Keep `CommittedTurnParseError` unchanged and parse-only.
- Preserve `AuditEvent`, `OutcomeRecord`, and `OperationJournalEntry` schemas unchanged.
- Preserve the existing phase enum unchanged.

## Test Plan

- Reply success-path finalization failures:
  - `TurnStore.write` failure after successful `run_turn()` leaves terminal phase `dispatched`, sets handle `unknown`, and raises `CommittedTurnFinalizationError`.
  - dialogue audit append failure does the same.
  - dialogue outcome append failure does the same.
  - `write_phase(completed)` failure after audit/outcome were already written does the same, and later recovery writes only the missing `completed` record.
- Dialogue replay safety:
  - if audit already exists and outcome is missing, replay appends only outcome.
  - if outcome already exists and audit is missing, replay appends only audit.
  - missing JSONL files are handled as empty.
  - retry attempts with different UUIDs do not create duplicate logical dialogue audit/outcome rows.
- Inline repair:
  - `_best_effort_repair_turn()` never raises.
  - `unconfirmed` leaves the journal at `intent`, handle `unknown`, and re-raises the original `run_turn()` exception.
  - `confirmed_unfinalized` leaves the journal at `intent`, handle `unknown`, and raises `CommittedTurnFinalizationError`.
  - `confirmed_finalized` writes `completed` directly from `intent`, surfaces `CommittedTurnFinalizationError`, and restores `active` only if inline resume succeeds.
  - confirmed-finalized plus resume failure logs the failure, leaves handle `unknown`, and still raises `CommittedTurnFinalizationError`.
- Startup recovery:
  - confirmed `intent` and confirmed `dispatched` entries both finalize correctly with `completed` last.
  - if recovery finalization fails, the terminal phase remains unchanged and no duplicate dialogue audit/outcome rows are created.
- Timestamp behavior:
  - recovery/repair outcome timestamps use `createdAt` from the confirmed turn when present.
  - fallback is `entry.created_at` when `createdAt` is absent or invalid.
  - audit timestamps remain local append-time.
- Consult:
  - audit append failure is logged and suppressed.
  - outcome append failure is logged and suppressed.
  - one consult append failure does not block the other or `ConsultResult`.
- MCP surface:
  - `CommittedTurnFinalizationError` text includes committed-turn guidance and `codex.dialogue.read`.
  - `CommittedTurnParseError` behavior remains unchanged.

## Assumptions and Defaults

- Full-file scan dedupe is acceptable for dialogue volume; no side index or schema migration is added.
- For legacy recovery entries missing `runtime_id` or usable `turn_id`, dialogue audit/outcome emission is skipped rather than treated as a hard recovery failure; `completed` may still be written after all emit-able local work is done.
- Inline resume failure after confirmed finalization is not fatal to durability; phase-2 startup recovery remains the safety net for reattaching `unknown` handles on the next startup.
- This change updates the relevant docstrings and failure-semantics comments so the code and its documented contracts match.
