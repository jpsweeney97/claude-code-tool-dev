## v1.1 Hardening Patch Set

### Summary
Implement four bounded changes in order: fix origin enforcement to use hook metadata, enforce workspace containment for read-only scripts, add ticket titles to structured outputs, and make skill-generated payload filenames truly unique. Do not change concurrency behavior or non-create stale checks in this patch set; document concurrency as a known limitation instead.

### Public Interface Changes
- Hook trust semantics change: `hook_request_origin` is derived from `agent_id` presence in `PreToolUse` input, not from which entrypoint path appears in the Bash command.
- Read-only CLI error convention becomes explicit: path containment failures return structured JSON with `state: "policy_blocked"` and exit code `1`.
- Structured ticket objects from read paths gain `title: str`.
- Triage dashboard items that identify specific tickets gain `title: str` where applicable.

### 1. Origin Enforcement Via Hook Metadata
Files:
- [ticket_engine_guard.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/hooks/ticket_engine_guard.py)
- [ticket_engine_user.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/scripts/ticket_engine_user.py)
- [ticket_engine_agent.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/scripts/ticket_engine_agent.py)
- [README.md](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/README.md)
- [ticket-contract.md](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/references/ticket-contract.md)
- [test_hook.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_hook.py)
- [test_hook_integration.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_hook_integration.py)
- [test_entrypoints.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_entrypoints.py)

Change:
- In the hook, compute `effective_origin = "agent"` only when `event["agent_id"]` is present and non-empty; otherwise use `"user"`.
- Keep command-path parsing only for allowlisting and injection eligibility. Do not use entrypoint path to infer trust origin.
- Inject `hook_request_origin=effective_origin`.
- Keep entrypoint hardcoded `REQUEST_ORIGIN` values and mismatch checks unchanged; the behavior change comes from correct hook injection.
- Rewrite docs so the user/agent entrypoint split is described as routing convenience and explicit intent, not a security boundary.
- Remove the false README claim that “agent calling user entrypoint is blocked because the hook injects agent origin based on that call.”

Edge cases:
- `agent_type` alone must not affect origin. Top-level `claude --agent Explore` remains user-origin unless `agent_id` is present.
- Empty-string or malformed `agent_id` is treated as absent.
- Direct CLI execution outside Claude Code still depends on explicit entrypoint choice and will have no hook metadata; that remains acceptable for manual local use.

Tests:
- Add a hook unit test: `agent_id` present + command targets `ticket_engine_user.py` => payload gets `hook_request_origin="agent"`.
- Add a hook unit test: `agent_type` present but no `agent_id` + command targets `ticket_engine_user.py` => payload gets `hook_request_origin="user"`.
- Add a hook unit test: no `agent_id` + command targets `ticket_engine_agent.py` => payload gets `hook_request_origin="user"`.
- Add integration coverage that a payload injected as agent causes `ticket_engine_user.py` to return `origin_mismatch`.
- Add integration coverage that a payload injected as user causes `ticket_engine_agent.py` to return `origin_mismatch`.
- Explicitly update [test_entrypoints.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_entrypoints.py) to reflect that “wrong entrypoint” mismatch detection now really fires based on hook metadata, not script-path inference.

Docs:
- Update the hook/security section in the README.
- Update the autonomy/trust section of the contract to state that `agent_id` is the authoritative hook signal for subagent origin.
- Add a note that entrypoint mismatch is now enforced as documented.

### 2. Read-Path Workspace Containment
Files:
- Add [ticket_paths.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/scripts/ticket_paths.py)
- Update [ticket_engine_core.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/scripts/ticket_engine_core.py)
- Update [ticket_read.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/scripts/ticket_read.py)
- Update [ticket_triage.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/scripts/ticket_triage.py)
- Update [README.md](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/README.md)
- Update [ticket-contract.md](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/references/ticket-contract.md)
- Update [test_read.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_read.py)
- Update [test_triage.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_triage.py)
- Optionally add or update a small CLI-focused test file if existing read/triage tests are too function-level.

Change:
- Extract `resolve_tickets_dir()` into a small shared helper module so mutations and read-only scripts use the same containment logic against `Path.cwd()`.
- Update engine core to import the shared helper rather than owning the function.
- In `ticket_read.py`, resolve the CLI `tickets_dir` before running list/query. On failure, print JSON like `{"state":"policy_blocked","message":"...","error_code":"policy_blocked"}` and exit `1`.
- In `ticket_triage.py`, do the same for `tickets_dir`. If `triage_orphan_detection()` remains callable from code with a `handoffs_dir`, leave it unchanged unless you expose it via CLI in this patch.
- Keep “missing `docs/tickets`” behavior as empty-success after a valid in-root path resolution.

Edge cases:
- Absolute paths inside the current project root remain valid.
- Relative paths are resolved from `Path.cwd()`, matching mutation behavior.
- A symlinked `tickets_dir` resolving outside root must be rejected.
- Exit code for containment errors is explicitly `1`, matching engine error convention; do not invent a new code.

Tests:
- Add CLI tests for `ticket_read.py list/query` rejecting paths outside the project root with exit code `1` and structured JSON.
- Add CLI tests for `ticket_read.py` accepting absolute and relative in-root paths.
- Add CLI tests for `ticket_triage.py dashboard/audit` rejecting outside-root paths with exit code `1`.
- Keep existing empty-directory read behavior covered.

Docs:
- Update path-constraints text in README and contract to state containment is enforced for read and triage scripts, not only mutation entrypoints.

### 3. Title In Structured API
Files:
- [ticket_parse.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/scripts/ticket_parse.py)
- [ticket_read.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/scripts/ticket_read.py)
- [ticket_triage.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/scripts/ticket_triage.py)
- [pipeline-guide.md](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/skills/ticket/references/pipeline-guide.md)
- [SKILL.md](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/skills/ticket/SKILL.md)
- [test_parse.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_parse.py)
- [test_read.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_read.py)
- [test_triage.py](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_triage.py)

Change:
- Add a title extraction helper in `ticket_parse.py` that reads the first Markdown H1.
- Support both `# T-YYYYMMDD-NN: Title` and `# Title`.
- Add `title: str` to `ParsedTicket`.
- Only strip the `"<id>:"` prefix when it matches the parsed YAML `id`; otherwise preserve the full heading text.
- Return `title` from read/list/query JSON objects.
- Add `title` to triage dashboard objects that identify a specific ticket:
  `stale[]`, `blocked_chains[]`, and `size_warnings[]`.
- Leave audit report output unchanged; it is audit-entry-based, not ticket-object-based.
- Update skill/docs so duplicate-candidate UX uses structured `title` from query output rather than implying a separate raw markdown parse.

Edge cases:
- Missing or malformed H1 should not make the ticket unparseable; use `title=""`.
- Legacy tickets with unusual headings should preserve whatever title text is present after `#`.
- Do not derive title from filename; heading is the source of truth.

Tests:
- Add parse tests for standard v1.0 heading extraction.
- Add parse tests for title-only heading and missing-heading fallback.
- Update read tests to assert `title` appears in list/query results.
- Update triage tests to assert `title` appears in stale/blocked/size-warning items.
- Add a duplicate-candidate regression test path showing the query response now contains title for user-facing messaging.

Docs:
- Remove any note claiming title is omitted from structured output.
- Update the pipeline guide duplicate loop example to rely on returned `title`.

### 4. Payload Filename Uniqueness
Files:
- [SKILL.md](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/skills/ticket/SKILL.md)
- [pipeline-guide.md](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/skills/ticket/references/pipeline-guide.md) if any fixed payload-name example should be aligned
- Optionally [README.md](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/README.md) if it mentions payload temp naming

Change:
- Replace the date-only guidance with a truly unique payload path format:
  `.claude/ticket-tmp/payload-<action>-<YYYYMMDDTHHMMSSffffff>-<8hex>.json`.
- State that the chosen filename must stay constant across all four stages of the same operation.
- Keep the path relative to project root so the hook containment rule still accepts it.

Edge cases:
- Uniqueness must not rely on second-level timestamps only.
- Avoid shell-heavy generation guidance; the skill should simply choose a unique literal suffix and reuse it.
- Do not use `/tmp`; keep payloads in `.claude/ticket-tmp/`.

Tests:
- No runtime tests required because this is instruction-only.
- Update any skill-facing examples or eval fixtures that assume `payload-<action>-<YYYYMMDD>.json`.

Docs:
- Update setup step 3 in SKILL.md.
- Update any pipeline examples that hardcode `.claude/ticket-tmp/payload.json` if consistency matters.

### Known Limitation Documentation
Files:
- [README.md](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/README.md)
- [ticket-contract.md](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/references/ticket-contract.md)

Change:
- Add an explicit v1.1 known limitation: concurrent autonomous creates are not serialized.
- Name the two concrete gaps: session create cap enforcement and ID allocation are not lock-based.
- State that this is acceptable for sequential single-session usage but not a hard guarantee under parallel subagent execution.

### Test Plan
- Run targeted suites first:
  `uv run pytest packages/plugins/ticket/tests/test_hook.py packages/plugins/ticket/tests/test_hook_integration.py packages/plugins/ticket/tests/test_entrypoints.py`
- Then run read/title suites:
  `uv run pytest packages/plugins/ticket/tests/test_read.py packages/plugins/ticket/tests/test_triage.py packages/plugins/ticket/tests/test_parse.py`
- Then run the full plugin suite:
  `uv run pytest packages/plugins/ticket/tests`

### Assumptions And Defaults
- `agent_id` is the sole authoritative signal for subagent-origin hook events.
- Top-level `claude --agent ...` sessions without `agent_id` remain user-origin.
- Path containment failures in read-only CLIs use exit code `1`.
- Non-create stale-plan protection remains out of scope for this patch set.
- Concurrency hardening is documentation-only in v1.1, not implemented.
