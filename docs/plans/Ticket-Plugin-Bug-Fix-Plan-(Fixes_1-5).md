# Ticket Plugin Bug-Fix Plan (Revised)

## Summary

This revision resolves the five issues in the prior plan.

- Tests ship with their corresponding code fix. Fix 4 is reduced to cross-cutting regression updates, command coverage, and test cleanup that spans multiple fixes.
- Fix 1 uses `error_code`, not `code`, if a machine-readable error is added. To minimize blast radius, the preferred implementation is still `state="escalate"` with a clear message and no new enum unless the existing error-code set already has a suitable value.
- Fix 2 now calls out the exact autonomy tests that must be rewritten versus the ones that only need cleanup.
- Fix 2 includes both divergence directions as explicit tested behavior.
- Fix 3 preserves the existing `resolution != "wontfix"` exemption outside the new blocker-classification helper at both close sites.

## Fix 1: Stop `update` from corrupting section fields into YAML

### Changes

Modify [`packages/plugins/ticket/scripts/ticket_engine_core.py`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/scripts/ticket_engine_core.py#L819) in two places.

1. Add explicit update-field classification near `_CANONICAL_FIELD_ORDER`.
   - Add `_UPDATE_FRONTMATTER_KEYS = set(_CANONICAL_FIELD_ORDER) | {"defer"}`
   - Add `_UPDATE_SECTION_FIELDS = {"problem", "context", "prior_investigation", "approach", "decisions_made", "acceptance_criteria", "verification", "key_files", "related"}`
   - Add `_UPDATE_IGNORED_FIELDS = {"ticket_id"}`
   - Add helper `_classify_update_fields(fields: dict[str, Any], ticket_id: str) -> tuple[dict[str, Any], list[str], list[str], bool]` returning:
     - `frontmatter_updates`
     - `section_fields_present`
     - `unknown_fields_present`
     - `ticket_id_mismatch`

2. Replace the blind write loop in `_execute_update` at [`ticket_engine_core.py`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/scripts/ticket_engine_core.py#L1244).
   - Remove the current lines 1295-1299 behavior that writes every `fields` key into `data`.
   - New flow:
     - Parse/classify fields before mutating `data`.
     - If `ticket_id_mismatch`, reject.
     - If any section-backed fields are present, reject the whole request.
     - If any unknown fields are present, reject the whole request.
     - If both valid and invalid fields are present, reject atomically; do not partially apply valid keys.
     - If `fields.ticket_id` matches top-level `ticket_id`, drop it silently.
     - Only write `frontmatter_updates` into `data`.

Preferred response shape:

```python
if ticket_id_mismatch:
    return EngineResponse(
        state="escalate",
        message=f"Update failed: fields.ticket_id must match top-level ticket_id. Got: {fields.get('ticket_id')!r:.100}",
    )

if section_fields or unknown_fields:
    parts = []
    if section_fields:
        parts.append(f"section fields not supported by update: {', '.join(section_fields)}")
    if unknown_fields:
        parts.append(f"unknown fields: {', '.join(unknown_fields)}")
    return EngineResponse(
        state="escalate",
        message=f"Update failed: {'; '.join(parts)}",
    )
```

If the implementation decides a machine-readable error is necessary, use `error_code=...`, not `code=...`.

Do not change `_render_canonical_frontmatter` at lines 844-850. The catch-all remains for preserving unknown keys already present in an existing ticket file, not for accepting arbitrary update payload keys.

### Edge Cases

1. `fields={"ticket_id": "<same id>"}` only.
   - Ignore `ticket_id`, no-op update, return `ok_update`, do not persist `ticket_id` in YAML.
2. `fields={"ticket_id": "<different id>"}`.
   - Reject with `escalate`; file unchanged.
3. `fields={"priority": "high", "problem": "..."}`.
   - Reject entire update; `priority` must not change.
4. `fields={"priority": "high", "custom": 1}`.
   - Reject entire update; `priority` must not change.
5. `fields={"approach": "..."}` only.
   - Reject with explicit unsupported-section message.
6. Existing ticket file already contains unknown frontmatter.
   - Preserve it on read/write.
7. Frontmatter-only updates for canonical/defer fields.
   - Continue to work exactly as before.

### New Tests

Ship these tests with Fix 1 in [`packages/plugins/ticket/tests/test_engine.py`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_engine.py).

- `test_update_rejects_section_field_problem_and_leaves_file_unchanged`
- `test_update_rejects_mixed_frontmatter_and_section_fields_atomically`
- `test_update_rejects_unknown_field_and_leaves_file_unchanged`
- `test_update_ignores_matching_fields_ticket_id`
- `test_update_rejects_mismatched_fields_ticket_id`

Each test should assert both the response and on-disk file contents.

### Regression Tests

Verify existing frontmatter-only update coverage still passes, especially [`test_engine.py`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_engine.py#L704) through [`test_engine.py`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_engine.py#L890).

Update:
- [`test_update_handles_yaml_serialization_failure`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_engine.py#L1204)
  - After Fix 1, unsupported custom fields should fail validation before YAML serialization. Update the expected failure mode accordingly.

### Doc Updates

Update:
- [`packages/plugins/ticket/skills/ticket/references/pipeline-guide.md`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/skills/ticket/references/pipeline-guide.md#L61)
  - Remove `fields.ticket_id` from the recommended update payload.
  - State explicitly that `update` supports frontmatter fields only.
- [`packages/plugins/ticket/skills/ticket/SKILL.md`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/skills/ticket/SKILL.md#L87)
  - Stop mapping “change problem/approach” requests onto `update`.
- [`packages/plugins/ticket/README.md`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/README.md)
  - Add one concise note that `update` is metadata/frontmatter-only in the current architecture.

### Forward Compatibility with Fix 6

Keep field classification in a standalone helper/constants block. Fix 6 can reuse that logic when the single mutation command decides whether a request is metadata-only or needs a future section-edit path.

## Fix 2: Re-read live autonomy config in agent `execute`

### Changes

Modify [`packages/plugins/ticket/scripts/ticket_engine_core.py`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/scripts/ticket_engine_core.py#L993).

1. Keep the `engine_execute(... autonomy_config: AutonomyConfig | None = None, ...)` signature unchanged.
   - This avoids coupling the security fix to the later CLI refactor.
   - The payload snapshot remains accepted as input but is no longer authoritative for agent policy.

2. Replace line 1012 logic with origin-aware policy loading.
   - For `request_origin == "agent"`:
     - Read `live_config = read_autonomy_config(tickets_dir)`.
     - Use `live_config` for policy enforcement.
     - If `autonomy_config` is present, compare policy-relevant fields against `live_config`.
     - If they differ, return `policy_blocked` with a rerun-from-preflight message.
   - For `request_origin == "user"`:
     - Keep current behavior: `config = autonomy_config or AutonomyConfig()`.

3. Add a narrow comparison helper, e.g. `_autonomy_policy_fingerprint(config: AutonomyConfig) -> tuple[str, int]`.
   - Compare only fields that affect execute admission in the current code:
     - `mode`
     - `max_creates`

Recommended logic:

```python
snapshot_config = autonomy_config

if request_origin == "agent":
    live_config = read_autonomy_config(tickets_dir)
    config = live_config
    if snapshot_config is not None:
        if _autonomy_policy_fingerprint(snapshot_config) != _autonomy_policy_fingerprint(live_config):
            return EngineResponse(
                state="policy_blocked",
                message="Autonomy policy changed since preflight. Rerun from preflight.",
                error_code="policy_blocked",
                data={"live_mode": live_config.mode},
            )
else:
    config = snapshot_config or AutonomyConfig()
```

Do not move this logic into the entrypoints. The security boundary belongs in `engine_execute`, because direct stage invocation is the actual risk.

### Edge Cases

1. Direct agent `execute` with forged payload snapshot `auto_audit`, live config `suggest`.
   - Return `policy_blocked`.
2. Agent preflight under `auto_audit`, config flips to `suggest` before execute.
   - Return `policy_blocked`.
3. Agent preflight under `suggest`, config flips to `auto_audit` before execute.
   - Also return `policy_blocked`; require rerun so execute is never based on a stale snapshot in either direction.
4. Agent execute with no snapshot, live config `auto_audit`.
   - Proceed if all other checks pass.
5. Agent execute with malformed/unreadable config file.
   - Preserve fail-closed behavior: effective mode becomes `suggest`, so mutation is blocked.
6. User-origin execute.
   - No behavior change.

### New Tests

Ship these tests with Fix 2.

Add to [`packages/plugins/ticket/tests/test_autonomy.py`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_autonomy.py):
- `test_agent_execute_uses_live_config_not_payload_snapshot`
  - Live config `suggest`, payload snapshot `auto_audit` -> `policy_blocked`
- `test_agent_execute_blocks_when_snapshot_and_live_config_diverge_to_more_restrictive`
  - Snapshot `auto_audit`, live `suggest` -> `policy_blocked`
- `test_agent_execute_blocks_when_snapshot_and_live_config_diverge_to_less_restrictive`
  - Snapshot `suggest`, live `auto_audit` -> `policy_blocked`
- `test_agent_execute_allows_when_live_config_auto_audit_and_no_snapshot`
  - No snapshot, live `auto_audit` -> succeeds
- `test_agent_execute_fail_closed_on_malformed_live_config`
  - Malformed config file -> blocked

Update/add integration coverage in [`packages/plugins/ticket/tests/test_autonomy_integration.py`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_autonomy_integration.py):
- Rename [`test_config_snapshot_prevents_toctou`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_autonomy_integration.py#L116) to something like `test_execute_blocks_when_autonomy_policy_changes_after_preflight`
- Invert expectation from `ok_create` to `policy_blocked`

### Regression Tests

These existing tests need explicit migration guidance.

Tests to rewrite for mechanism accuracy, even if the old assertions would still pass accidentally:
- [`test_execute_agent_suggest_blocked`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_autonomy.py#L316)
  - Remove the passed `AutonomyConfig(mode="suggest")`
  - Rely on missing config file -> default `suggest`
- [`test_execute_agent_none_config_blocked`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_autonomy.py#L342)
  - Same cleanup: no snapshot, no config file -> blocked
- [`test_execute_agent_unknown_mode_self_heals_to_suggest`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_autonomy.py#L327)
  - Rewrite to write invalid mode into `.claude/ticket.local.md`
  - Assert `read_autonomy_config()` self-heals to `suggest`
  - Then assert agent execute blocks because live config resolves to `suggest`

Tests that must be reconfigured to write a live config file because they currently depend on payload snapshot admission:
- [`test_execute_agent_reopen_blocked`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_autonomy.py#L352)
- [`test_execute_agent_dedup_override_blocked`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_autonomy.py#L364)
- [`test_execute_agent_auto_audit_allowed`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_autonomy.py#L375)
- [`test_execute_agent_auto_audit_cap_reached`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_autonomy.py#L386)
- [`test_post_init_heals_invalid_max_creates`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_autonomy.py#L409)
- [`test_execute_agent_update_auto_audit_allowed`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_autonomy.py#L427)
- [`test_execute_agent_close_auto_audit_allowed`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_autonomy.py#L441)
- [`test_execute_agent_audit_write_failure_blocks`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_autonomy.py#L455)

For those tests, create/write `.claude/ticket.local.md` in the temporary project root backing `tmp_tickets` before invoking `engine_execute`.

### Doc Updates

Update:
- [`packages/plugins/ticket/references/ticket-contract.md`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/references/ticket-contract.md#L107)
  - Replace snapshot-based defense-in-depth wording with live reread wording for agent execute.
- [`packages/plugins/ticket/README.md`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/README.md#L137)
  - Remove claims that immutable snapshots prevent TOCTOU.
- [`packages/plugins/ticket/README.md`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/README.md#L183)
  - State that agent execute re-reads live autonomy policy and blocks if it changed since preflight.

No `/ticket` skill change is required for this fix.

### Forward Compatibility with Fix 6

This preserves the current API while moving policy authority into the engine. Fix 6 can later remove the payload snapshot entirely once one public mutation command owns the full flow.

## Fix 3: Distinguish missing blockers from unresolved blockers

### Changes

Modify [`packages/plugins/ticket/scripts/ticket_engine_core.py`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/scripts/ticket_engine_core.py) at all blocker-validation sites.

1. Add a pure classification helper near the dependency logic:

```python
def _classify_blockers(blocked_by: list[str], ticket_map: dict[str, TicketData]) -> tuple[list[str], list[str]]:
    missing = []
    unresolved = []
    for bid in blocked_by:
        if bid not in ticket_map:
            missing.append(bid)
        elif ticket_map[bid].status not in _TERMINAL_STATUSES:
            unresolved.append(bid)
    return missing, unresolved
```

2. Preserve the existing `wontfix` exemption outside the helper.
   - Do not move `resolution != "wontfix"` into `_classify_blockers`.
   - Keep the current outer gating pattern at both close sites:
     - preflight close path around [`ticket_engine_core.py`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/scripts/ticket_engine_core.py#L664)
     - execute close path around [`ticket_engine_core.py`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/scripts/ticket_engine_core.py#L1355)

3. Patch preflight close dependency validation at [`ticket_engine_core.py`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/scripts/ticket_engine_core.py#L667).
   - If `resolution != "wontfix"` and blockers exist:
     - call `_classify_blockers`
     - if `missing_blockers` or `unresolved_blockers` and `dependency_override` is false:
       - return `dependency_blocked`
       - include both lists in `data`
       - message distinguishes missing references from open blockers
     - if `dependency_override` is true:
       - allow preflight to continue
       - keep current override semantics

4. Patch transition precondition validation at [`ticket_engine_core.py`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/scripts/ticket_engine_core.py#L901).
   - For blocked -> open / in_progress:
     - call `_classify_blockers`
     - if either list is non-empty:
       - return `invalid_transition`
       - message tells the caller to resolve open blockers and remove stale/missing references first
   - Do not add override support here.

5. Patch execute close defense-in-depth at [`ticket_engine_core.py`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/scripts/ticket_engine_core.py#L1355).
   - Mirror preflight close exactly, including:
     - outer `resolution != "wontfix"` gate
     - `dependency_override` handling
     - separate reporting of `missing_blockers` and `unresolved_blockers`

### Edge Cases

1. `blocked_by=[]`
   - Proceed normally.
2. All blockers exist and are terminal.
   - Proceed normally.
3. Open blockers only.
   - Existing blocked behavior remains.
4. Missing blockers only.
   - Close/reopen blocked unless close uses `dependency_override=True`.
5. Missing + unresolved blockers.
   - Surface both lists.
6. Close with `resolution="wontfix"` and missing blockers.
   - Preserve current exemption; do not block on blockers in this path.
7. Duplicate blocker IDs.
   - Preserve order; no dedup in this patch.

### New Tests

Ship these tests with Fix 3 in [`packages/plugins/ticket/tests/test_engine.py`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_engine.py).

- `test_preflight_close_reports_missing_blockers`
- `test_execute_close_reports_missing_blockers`
- `test_close_reports_missing_and_unresolved_blockers_together`
- `test_execute_close_allows_missing_blockers_with_dependency_override`
- `test_blocked_ticket_cannot_reopen_with_missing_blocker_reference`
- `test_close_wontfix_ignores_missing_blockers`
  - Explicitly protects the existing exemption at both preflight and execute close

### Regression Tests

Verify these existing tests still pass:
- [`test_close_blocked_ticket_requires_override`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_engine.py#L962)
- [`test_execute_close_blocks_on_open_dependencies_without_override`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_engine.py#L1009)

Also verify triage coverage stays coherent with the new semantics:
- [`packages/plugins/ticket/tests/test_triage.py`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_triage.py#L88)

### Doc Updates

Update:
- [`packages/plugins/ticket/references/ticket-contract.md`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/references/ticket-contract.md#L127)
  - Clarify that missing blocker references are validation failures, not resolved blockers.
- [`packages/plugins/ticket/skills/ticket/references/pipeline-guide.md`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/skills/ticket/references/pipeline-guide.md)
  - Mention that close can be blocked by open blockers or missing blocker references unless override is used.
- [`packages/plugins/ticket/README.md`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/README.md)
  - Add a short note that stale `blocked_by` references must be cleaned up for normal close/reopen flow.

### Forward Compatibility with Fix 6

The helper should stay purely classificatory. Future orchestration can reuse it without inheriting close-specific exemptions or override semantics.

## Fix 4: Cross-cutting regression updates and test cleanup

### Changes

Fixes 1-3 each ship with their own new tests. Fix 4 is limited to cross-cutting cleanup that is not naturally owned by a single code fix.

Modify:
- [`packages/plugins/ticket/tests/test_autonomy_integration.py`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_autonomy_integration.py)
- [`packages/plugins/ticket/tests/test_entrypoints.py`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_entrypoints.py) if any assertions need realignment
- Test names/docstrings in [`test_autonomy.py`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_autonomy.py) that would otherwise describe the wrong mechanism after Fix 2

This fix should:
- rename tests whose old names assert obsolete snapshot semantics
- normalize fixtures/helpers where multiple tests now need a live config file
- update any comments/docstrings that still describe section updates as supported or snapshot-based execute policy as authoritative

### Edge Cases

1. A test still passes for the wrong reason after a behavior change.
   - Rewrite it so setup proves the intended mechanism, not just the outcome.
2. A comment/docstring contradicts the new security behavior.
   - Update it in the same PR as the test change.

### New Tests

None required in Fix 4 itself unless a cross-cutting helper warrants a dedicated test. All bug-specific new tests land with Fixes 1-3.

### Regression Tests

Run and verify at minimum:
- `uv run pytest packages/plugins/ticket/tests/test_engine.py`
- `uv run pytest packages/plugins/ticket/tests/test_autonomy.py`
- `uv run pytest packages/plugins/ticket/tests/test_autonomy_integration.py`
- `uv run pytest packages/plugins/ticket/tests/test_entrypoints.py`
- `uv run pytest packages/plugins/ticket/tests/test_triage.py`

### Doc Updates

None beyond the code-test comments/docstrings updated in the touched test files.

### Forward Compatibility with Fix 6

Keep tests behavior-focused so the future CLI collapse only requires setup rewrites, not expectation rewrites.

## Fix 5: Correct close-resolution docs to match the engine

### Changes

This remains a docs-only patch.

Update [`packages/plugins/ticket/skills/ticket/references/pipeline-guide.md`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/skills/ticket/references/pipeline-guide.md#L96).

Replace the current resolution guidance with:

- `resolution` is optional
- valid values are `done` and `wontfix`
- omitting `resolution` defaults to `done`

Do not extend the code to support `duplicate` or `fixed` in this patch. The contract already matches the engine; the guide is the drift point.

### Edge Cases

1. `resolution` omitted.
   - Docs must say this defaults to `done`.
2. `resolution="duplicate"` or `resolution="fixed"`.
   - Docs must say these are invalid and will be rejected.
3. Existing tickets with `done` / `wontfix`.
   - No behavior change.

### New Tests

No new code tests are required for the documentation fix itself.

### Regression Tests

Verify existing close-resolution tests still pass in [`packages/plugins/ticket/tests/test_engine.py`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/tests/test_engine.py).

### Doc Updates

Update:
- [`packages/plugins/ticket/skills/ticket/references/pipeline-guide.md`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/ticket/skills/ticket/references/pipeline-guide.md#L96)

No contract update is needed. No README update is needed unless the invalid values appear there.

### Forward Compatibility with Fix 6

Keeping the close payload vocabulary aligned now prevents more prompt/code drift from leaking into the future single-command mutation interface.

## Assumptions and Defaults

- Tests land with the fix they verify. Fix 4 is only cross-cutting cleanup and regression maintenance.
- Section-backed field updates remain unsupported in this patch set.
- `fields.ticket_id` is a compatibility shim only:
  - ignored if it matches
  - rejected if it conflicts
- Agent execute uses live autonomy policy as the sole authority for admission.
- Snapshot/live policy divergence blocks in both directions and requires rerun from preflight.
- Missing blockers are reported separately from unresolved blockers, but existing response states are preserved.
- The `wontfix` dependency exemption remains exactly where it is today: in the close paths, outside the blocker-classification helper.
