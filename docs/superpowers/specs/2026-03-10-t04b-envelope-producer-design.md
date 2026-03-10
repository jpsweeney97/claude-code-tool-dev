# T-04b: Handoff-Side Envelope Producer

**Date:** 2026-03-10
**Status:** Draft
**Ticket:** T-20260302-04 (sub-ticket T-04b)
**Branch:** TBD (feature or fix branch)
**Dependencies:** T-04a (envelope consumer) — merged in PR #69

## Problem

The handoff plugin's `/defer` skill creates tickets by piping JSON to `defer.py`, which allocates IDs, renders markdown, and writes files directly to `docs/tickets/`. This bypasses the ticket engine's pipeline (dedup, autonomy enforcement, audit trail, validation, preflight). T-04a built the envelope consumer — a validated schema and ingestion pipeline. T-04b converts `/defer` to emit envelopes that the ticket engine consumes through its full pipeline.

## Architecture

```
BEFORE (direct write):
  /defer SKILL.md → defer.py → write markdown → docs/tickets/*.md

AFTER (envelope pipeline):
  /defer SKILL.md → defer.py → write envelope JSON → docs/tickets/.envelopes/*.json
                  → ticket_engine_user.py ingest <payload> → plan → preflight → execute
                  → move envelope to .processed/
```

**Cross-plugin boundary:** The SKILL.md orchestrates the handoff. `defer.py` (handoff plugin) writes the envelope. `ticket_engine_user.py ingest` (ticket plugin) consumes it. No Python imports cross the plugin boundary — the interface is a JSON file on disk plus a CLI subprocess call.

**Trust model:** The `/defer` SKILL.md invokes `ticket_engine_user.py ingest` via Bash. The `ticket_engine_guard.py` PreToolUse hook matches this against the allowlist pattern (`ticket_engine_(user|agent)\.py\s+(\w+)\s+(.+)$`), injects trust fields (`hook_injected`, `hook_request_origin`, `session_id`) into the payload file, and allows the command. The `ingest` subcommand internally runs the plan→preflight→execute pipeline with the injected trust triple.

**Guard modification required:** The guard's `VALID_SUBCOMMANDS` frozenset (`ticket_engine_guard.py:29`) must be updated to include `"ingest"`. Without this, the guard rejects the subcommand before the runner sees it.

## Schema Change

Add one optional field to the DeferredWorkEnvelope schema:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `effort` | string | `"S"` | Effort estimate (freeform string, not enum) |

The ticket engine does not validate `effort` as an enum — `ticket_validate.py` has no effort check, and tests preserve freeform values. Adding `effort` to `_OPTIONAL_FIELDS` is required so the closed-schema validator (`validate_envelope`) does not reject it as an unknown field. `map_envelope_to_fields()` must also be updated to pass it through to `fields["effort"]` — neither exists today.

**Fields NOT added to the envelope:**

| Field | Disposition | Rationale |
|-------|------------|-----------|
| `branch` | Composed into `context` by SKILL.md | Capture context, not origin identity. `source` stays `{type, ref, session}`. |
| `source_text` | Composed into `context` by SKILL.md | Evidence anchor has no engine equivalent (`## Source` section doesn't exist in `ticket_render.py`). |

## Components

### 1. Envelope Schema Update

**File:** `packages/plugins/ticket/scripts/ticket_envelope.py`

Add `"effort"` to `_OPTIONAL_FIELDS`. Update `map_envelope_to_fields()` to pass `effort` through. Also fix the module docstring (line 3 says `/save` but should reference `/defer` or both skills):

```python
if "effort" in envelope:
    fields["effort"] = envelope["effort"]
```

**File:** `packages/plugins/ticket/references/ticket-contract.md` (§11)

Add `effort` row to the Optional Fields table.

### 2. Guard Update

**File:** `packages/plugins/ticket/hooks/ticket_engine_guard.py`

Add `"ingest"` to `VALID_SUBCOMMANDS`:

```python
VALID_SUBCOMMANDS = frozenset({"classify", "plan", "preflight", "execute", "ingest"})
```

The guard's existing trust injection logic applies unchanged — it reads the payload file, injects `hook_injected`, `hook_request_origin`, and `session_id`, then writes it back before allowing the command.

### 3. Ingest Subcommand

**File:** `packages/plugins/ticket/scripts/ticket_engine_runner.py`

Add `"ingest"` to `_dispatch()`. The ingest handler:

1. Reads `envelope_path` from the payload
2. Calls `read_envelope(envelope_path)` — validates JSON and schema
3. Calls `map_envelope_to_fields(envelope)` — maps to engine vocabulary
4. Runs the engine pipeline: `engine_plan()` → `engine_preflight()` → `engine_execute()`
5. On success: calls `move_to_processed(envelope_path)`
6. Returns `EngineResponse` (same format as other subcommands)

**Payload schema for ingest:**

```json
{
  "envelope_path": "/absolute/path/to/envelope.json",
  "session_id": "(injected by guard)",
  "hook_injected": true,
  "hook_request_origin": "user"
}
```

The ingest handler hardcodes `action="create"` and `classify_confidence=1.0` (the intent is known — no classification ambiguity). `classify_intent="create"` to satisfy preflight's intent-match check.

**Trust triple:** The guard injects `hook_injected`, `hook_request_origin`, and `session_id` into the payload file before the command runs. The runner's `run()` function validates the trust triple for `execute` subcommands. Extend this check to also cover `ingest`: change the condition from `if subcommand == "execute":` to `if subcommand in ("execute", "ingest"):`. The ingest handler then receives the validated trust fields and passes them through to `engine_execute()` internally.

### 4. Ingest Stage Model

**File:** `packages/plugins/ticket/scripts/ticket_stage_models.py`

Add `IngestInput` dataclass:

```python
@dataclass
class IngestInput:
    envelope_path: str
    session_id: str
    hook_injected: bool = False
    hook_request_origin: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "IngestInput": ...
```

### 5. defer.py Rewrite

**File:** `packages/plugins/handoff/scripts/defer.py`

Replace the current `render_ticket()` / `write_ticket()` / `allocate_id()` / `filename_slug()` flow with `emit_envelope()`:

```python
def emit_envelope(candidate: dict[str, Any], envelopes_dir: Path) -> Path:
    """Write a DeferredWorkEnvelope JSON file. Returns the path."""
```

**Field mapping (candidate → envelope):**

| Candidate field | Envelope field |
|----------------|---------------|
| `summary` | `title` |
| `problem` | `problem` |
| `proposed_approach` | `approach` |
| `acceptance_criteria` | `acceptance_criteria` |
| `priority` | `suggested_priority` |
| `effort` | `effort` |
| `files` | `key_file_paths` |
| `source_type` | `source.type` |
| `source_ref` | `source.ref` |
| `session_id` | `source.session` |
| — | `envelope_version` = `"1.0"` |
| — | `emitted_at` = ISO 8601 UTC now |

**Context composition** (deterministic, in `emit_envelope`):

```python
context_parts = []
if candidate.get("branch"):
    context_parts.append(f"Captured on branch `{candidate['branch']}`.")
if candidate.get("source_text"):
    context_parts.append(f"Evidence anchor:\n> \"{candidate['source_text']}\"")
if context_parts:
    envelope["context"] = "\n\n".join(context_parts)
```

**Envelope filename:** `<ISO-timestamp>-<slug>.json` where slug is derived from the title (lowercase, alphanumeric + hyphens, max 50 chars). Uses the current `filename_slug` logic adapted for JSON extension and timestamp prefix instead of ticket ID.

**CLI interface change:**

```
BEFORE: echo '<json>' | python defer.py --date YYYY-MM-DD --tickets-dir docs/tickets
AFTER:  echo '<json>' | python defer.py --tickets-dir docs/tickets
```

`--date` is no longer needed — `emitted_at` uses the current UTC timestamp. The script no longer allocates ticket IDs (the engine does that).

**Output format change:**

```json
BEFORE: {"status": "ok", "created": [{"id": "T-...", "path": "docs/tickets/..."}]}
AFTER:  {"status": "ok", "envelopes": [{"path": "docs/tickets/.envelopes/..."}]}
```

The response no longer includes ticket IDs — those are allocated by the engine during ingestion. The SKILL.md gets ticket IDs from the engine's response in a subsequent step.

### 6. SKILL.md Update

**File:** `packages/plugins/handoff/skills/defer/SKILL.md`

**Step 4 changes** (create tickets via defer.py):

Replace the single `defer.py` call with a two-phase flow:

```
Phase 1 — Emit envelopes:
  echo '<candidates_json>' | python "${CLAUDE_PLUGIN_ROOT}/scripts/defer.py" \
    --tickets-dir "<project_root>/docs/tickets"

Phase 2 — Ingest each envelope:
  For each envelope path in the response:
    Write ingest payload to temp file:
      {"envelope_path": "<path>"}
    Call:
      python3 "<ticket_plugin_root>/scripts/ticket_engine_user.py" ingest <payload_file>
    Parse EngineResponse from stdout
```

**Step 5 changes** (commit):

Stage both the created ticket files AND the `.processed/` envelope files:

```bash
git add docs/tickets/<ticket>.md docs/tickets/.envelopes/.processed/<envelope>.json
git commit -m "chore(tickets): defer N items from <source_type>"
```

**Step 6 changes** (report):

Report both envelope paths and created ticket IDs from the engine responses.

**Ticket plugin root discovery:** The SKILL.md needs the ticket plugin's script path. Two options:
- Convention: `${CLAUDE_PLUGIN_ROOT}/../ticket/scripts/ticket_engine_user.py` (relative from handoff plugin)
- Discovery: `find $(git rev-parse --show-toplevel)/packages/plugins/ticket -name ticket_engine_user.py`

Convention is deterministic; use it with a fallback.

### 7. Dead Code Removal

**File:** `packages/plugins/handoff/scripts/defer.py`

Remove after cutover:
- `render_ticket()` — markdown rendering (replaced by engine's `ticket_render.py`)
- `allocate_id()` — ID allocation (replaced by engine's `_execute_create`)
- `filename_slug()` — ticket filename generation (replaced by engine)
- `_quote()` — YAML string quoting helper (no longer rendering YAML)
- `write_ticket()` — file writer (replaced by `emit_envelope()`)
- `_VALID_PRIORITIES`, `_VALID_EFFORTS` — validation constants (envelope validator handles this)
- `_YAML_IMPLICIT_SCALARS`, `_YAML_NUMERIC_RE` — YAML safety constants (no longer rendering YAML)
- `_DATE_ID_RE` — ticket ID regex (no longer allocating IDs)
- Imports: `re`, `warnings` (no longer needed)
- Imports: `parse_ticket`, `render_defer_meta` (no longer needed)

**Retained:**
- `main()` — rewritten to call `emit_envelope()` instead of `write_ticket()`
- `emit_envelope()` — new function

### 8. provenance.py

**File:** `packages/plugins/handoff/scripts/provenance.py`

Check if `render_defer_meta()` is used elsewhere. If only used by `defer.py`'s `render_ticket()`, it becomes dead code after cutover. Leave for a separate cleanup pass.

## Cutover Strategy

**Atomic cutover.** No feature flag, no dual-path.

The SKILL.md change and `defer.py` rewrite ship together. After the change:
- `/defer` emits envelopes and immediately ingests them
- Users see the same end result (tickets created, committed)
- The envelope in `.processed/` is additional provenance

**Rollback:** Revert the commits. The old `defer.py` and SKILL.md are in git history.

## Testing Strategy

### Ticket plugin tests (envelope schema + ingest)

| Test | What it verifies |
|------|-----------------|
| `test_validate_envelope_with_effort` | `effort` field accepted as optional string |
| `test_validate_envelope_effort_non_string_rejected` | Non-string effort rejected |
| `test_map_envelope_to_fields_with_effort` | Effort passed through to fields dict |
| `test_ingest_subcommand_happy_path` | Full ingest pipeline: read → validate → map → plan → preflight → execute → move |
| `test_ingest_subcommand_invalid_envelope` | Returns error response for invalid schema |
| `test_ingest_subcommand_missing_envelope` | Returns error response for missing file |
| `test_ingest_subcommand_dedup_detected` | Dedup fires during plan stage |

### Handoff plugin tests (emit_envelope)

| Test | What it verifies |
|------|-----------------|
| `test_emit_envelope_minimal` | Minimal candidate produces valid envelope JSON |
| `test_emit_envelope_full` | All candidate fields mapped correctly |
| `test_emit_envelope_context_composition` | Branch and source_text composed into context |
| `test_emit_envelope_no_status` | Envelope never contains `status` field |
| `test_emit_envelope_timestamp` | `emitted_at` is valid ISO 8601 |
| `test_main_emits_envelopes` | CLI writes envelopes to `.envelopes/` dir |
| `test_main_output_format` | JSON response has `envelopes` key, not `created` |

## Non-Goals

- **T-04c (agent infrastructure):** Agent-side ingestion (`ticket_engine_agent.py ingest`) is a separate ticket.
- **`/save` envelope emission:** Only `/defer` is converted. `/save`'s integration is future work.
- **Envelope batch processing:** No batch ingestion command. Each envelope is ingested immediately after emission.
- **Schema v1.1:** No new structured fields beyond `effort`. `branch` and `source_text` are composed into `context`.

## Open Questions (Resolved)

| Question | Resolution | Source |
|----------|-----------|--------|
| Write-then-consume vs batch? | Write-then-consume | Codex consultation turn 1 |
| Who orchestrates ingestion? | SKILL.md calls ticket-owned CLI | Codex consultation turn 1 |
| Cross-plugin call style? | Subprocess via Bash | Codex consultation turn 1 |
| Feature flag needed? | No — atomic cutover | Codex consultation turn 1 |
| `effort` type? | String, not enum | Codex consultation turn 2 |
| `branch` placement? | `context` composition, not `source.branch` | Codex consultation turn 2 |
| `source_text` placement? | `context` composition | Codex consultation turn 2 |
| Guard update? | Yes — add `"ingest"` to `VALID_SUBCOMMANDS` in `ticket_engine_guard.py` | Spec review (Critical-1) |

## References

| Resource | Location |
|----------|----------|
| Envelope consumer | `packages/plugins/ticket/scripts/ticket_envelope.py` |
| Engine runner | `packages/plugins/ticket/scripts/ticket_engine_runner.py` |
| Engine guard | `packages/plugins/ticket/hooks/ticket_engine_guard.py` |
| Contract §11 | `packages/plugins/ticket/references/ticket-contract.md` |
| Current defer.py | `packages/plugins/handoff/scripts/defer.py` |
| Current /defer SKILL.md | `packages/plugins/handoff/skills/defer/SKILL.md` |
| T-04a PR | PR #69 (merged) |
| Codex thread | `019cd957-e641-7a13-a2d6-628c81d0021f` |
