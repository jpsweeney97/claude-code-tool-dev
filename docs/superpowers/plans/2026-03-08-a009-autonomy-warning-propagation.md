# A-009: Autonomy Warning Propagation Implementation Plan

**Goal:** Surface `AutonomyConfig` degradation warnings in the two `engine_execute` responses where a live config re-read materially affects the outcome.

**Architecture:** Two targeted enrichments to `engine_execute` in `ticket_engine_core.py`. No new logic — only serialization of warnings that already exist in `config.warnings` when the config was malformed. Two new integration tests in `test_autonomy_integration.py`. Pre-existing Ruff violation in the test file fixed in Task 0.

**Tech Stack:** Python 3.12, pytest, uv (`uv run pytest`), ruff (`uv run ruff check`)

---

## Background

`AutonomyConfig` self-heals invalid values to safe defaults and records why in `.warnings`. In `engine_execute`, two paths re-read the live config and use it to block execution:

1. **Policy-changed check** (L1049–1059): if live config's `(mode, max_creates)` fingerprint differs from the preflight snapshot, returns `policy_blocked`. Currently includes `live_mode` in `data` but not the degradation reason.
2. **Defense-in-depth mode block** (L1178–1183): if live config's mode is not `"auto_audit"`, returns `policy_blocked`. Currently has no `data` at all.

`_autonomy_policy_fingerprint` returns `(config.mode, config.max_creates)` — warnings are **excluded**. This is intentional and must not change.

The fix: in each of these two responses, add `live_mode` (already present in path 1, missing in path 2) and conditionally add `live_warnings: list[str]` when `config.warnings` is non-empty.

---

## Task 0: Create branch and fix pre-existing Ruff violation

**Files:**
- Modify: `packages/plugins/ticket/tests/test_autonomy_integration.py:8`

**Step 1: Create the working branch**

```bash
cd /Users/jp/Projects/active/claude-code-tool-dev
git checkout main && git pull
git checkout -b fix/a009-autonomy-warning-propagation
```

**Step 2: Fix the unused import on line 8**

Current line 8:
```python
from scripts.ticket_dedup import dedup_fingerprint as compute_dedup_fp, target_fingerprint as compute_target_fp
```

Replace with:
```python
from scripts.ticket_dedup import dedup_fingerprint as compute_dedup_fp
```

`compute_target_fp` is imported but never used in this file. This is a pre-existing F401 Ruff violation noted in the prior handoff.

**Step 3: Verify the fix**

```bash
cd packages/plugins/ticket
uv run ruff check tests/test_autonomy_integration.py
```

Expected: no output (clean).

**Step 4: Run the existing integration tests to confirm nothing broke**

```bash
uv run pytest tests/test_autonomy_integration.py -v
```

Expected: all 5 existing tests pass.

**Step 5: Commit**

```bash
git add packages/plugins/ticket/tests/test_autonomy_integration.py
git commit -m "fix(ticket): remove unused compute_target_fp import in test_autonomy_integration.py"
```

---

## Task 1: Propagate warnings in policy-changed-since-preflight response

**Files:**
- Modify: `packages/plugins/ticket/scripts/ticket_engine_core.py:1054–1059`
- Test: `packages/plugins/ticket/tests/test_autonomy_integration.py`

### Scenario

Preflight runs with a valid `auto_audit` config (fingerprint: `("auto_audit", 5)`). Between preflight and execute, the config becomes malformed — say `autonomy_mode: BOGUS_MODE`. On execute, the live re-read self-heals to `mode="suggest"` and populates `config.warnings`. Fingerprint is now `("suggest", 5)` ≠ `("auto_audit", 5)` → policy-changed fires. The response should explain that the mode degraded because the config was malformed.

**Step 1: Write the failing test**

Add to `TestAutonomyIntegration` in `test_autonomy_integration.py`:

```python
def test_policy_changed_with_malformed_live_config_includes_warnings(self, integration_env):
    """Policy-changed response includes live_warnings when config is malformed."""
    tickets_dir, config_path = integration_env
    config_path.write_text("---\nautonomy_mode: auto_audit\nmax_creates_per_session: 5\n---\n")

    pf_resp = engine_preflight(
        ticket_id=None, action="create", session_id="warn-session",
        request_origin="agent", classify_confidence=0.95, classify_intent="create",
        dedup_fingerprint="fp1", target_fingerprint=None,
        tickets_dir=tickets_dir, hook_injected=True,
    )
    assert pf_resp.state == "ok"
    snapshot = AutonomyConfig.from_dict(pf_resp.data["autonomy_config"])
    assert snapshot.mode == "auto_audit"

    # Config becomes malformed between preflight and execute.
    config_path.write_text("---\nautonomy_mode: BOGUS_MODE\n---\n")

    ex_resp = engine_execute(
        action="create", ticket_id=None,
        fields={"title": "Warning test", "problem": "Config degraded"},
        session_id="warn-session", request_origin="agent",
        dedup_override=False, dependency_override=False,
        tickets_dir=tickets_dir, autonomy_config=snapshot, hook_injected=True,
        hook_request_origin="agent",
        classify_intent="create",
        classify_confidence=0.95,
        dedup_fingerprint=compute_dedup_fp("Config degraded", []),
    )
    assert ex_resp.state == "policy_blocked"
    assert "changed since preflight" in ex_resp.message.lower()
    assert ex_resp.data["live_mode"] == "suggest"
    assert "live_warnings" in ex_resp.data
    assert any("BOGUS_MODE" in w for w in ex_resp.data["live_warnings"])
```

**Step 2: Run the test to verify it fails**

```bash
cd packages/plugins/ticket
uv run pytest tests/test_autonomy_integration.py::TestAutonomyIntegration::test_policy_changed_with_malformed_live_config_includes_warnings -v
```

Expected: FAIL — `KeyError: 'live_warnings'` or `AssertionError` on the `live_warnings` assertion.

**Step 3: Implement the fix**

In `ticket_engine_core.py`, replace the policy-changed return (L1054–1059):

Current:
```python
            return EngineResponse(
                state="policy_blocked",
                message="Autonomy policy changed since preflight. Rerun from preflight.",
                error_code="policy_blocked",
                data={"live_mode": config.mode},
            )
```

Replace with:
```python
            policy_changed_data: dict[str, Any] = {"live_mode": config.mode}
            if config.warnings:
                policy_changed_data["live_warnings"] = list(config.warnings)
            return EngineResponse(
                state="policy_blocked",
                message="Autonomy policy changed since preflight. Rerun from preflight.",
                error_code="policy_blocked",
                data=policy_changed_data,
            )
```

**Step 4: Run the new test to verify it passes**

```bash
uv run pytest tests/test_autonomy_integration.py::TestAutonomyIntegration::test_policy_changed_with_malformed_live_config_includes_warnings -v
```

Expected: PASS.

**Step 5: Run the full integration test suite**

```bash
uv run pytest tests/test_autonomy_integration.py -v
```

Expected: all 6 tests pass (5 existing + 1 new).

**Step 6: Commit**

```bash
git add packages/plugins/ticket/scripts/ticket_engine_core.py \
        packages/plugins/ticket/tests/test_autonomy_integration.py
git commit -m "feat(ticket): propagate live_warnings in policy-changed-since-preflight response (A-009)"
```

---

## Task 2: Propagate warnings in defense-in-depth mode block response

**Files:**
- Modify: `packages/plugins/ticket/scripts/ticket_engine_core.py:1178–1183`
- Test: `packages/plugins/ticket/tests/test_autonomy_integration.py`

### Scenario

The config is malformed (`BOGUS_MODE`) — self-heals to `mode="suggest"`, `max_creates=5`. A snapshot is constructed with `mode="suggest"` (matching effective policy, so fingerprints match: `("suggest", 5) == ("suggest", 5)`). The policy-changed check passes. The mode block fires: `"suggest" != "auto_audit"`. The response currently has no `data`. After the fix it should include `live_mode` and `live_warnings`.

Note: in the standard pipeline, preflight blocks agents in `suggest` mode before they reach execute, so this is defense-in-depth for bypass scenarios. The snapshot is constructed directly in the test to reach this code path.

**Step 1: Write the failing test**

Add to `TestAutonomyIntegration` in `test_autonomy_integration.py`:

```python
def test_defense_in_depth_mode_block_with_malformed_config_includes_warnings(self, integration_env):
    """Defense-in-depth mode block includes live_mode and live_warnings when config is malformed."""
    tickets_dir, config_path = integration_env
    # Malformed config: self-heals to mode="suggest", max_creates=5.
    config_path.write_text("---\nautonomy_mode: BOGUS_MODE\n---\n")

    # Snapshot matches effective policy (suggest, 5) — fingerprints match,
    # policy-changed check passes, mode block fires.
    snapshot = AutonomyConfig(mode="suggest")

    ex_resp = engine_execute(
        action="create", ticket_id=None,
        fields={"title": "Mode block test", "problem": "Degraded config mode block"},
        session_id="dind-session", request_origin="agent",
        dedup_override=False, dependency_override=False,
        tickets_dir=tickets_dir, autonomy_config=snapshot, hook_injected=True,
        hook_request_origin="agent",
        classify_intent="create",
        classify_confidence=0.95,
        dedup_fingerprint=compute_dedup_fp("Degraded config mode block", []),
    )
    assert ex_resp.state == "policy_blocked"
    assert "defense-in-depth" in ex_resp.message.lower()
    assert ex_resp.data["live_mode"] == "suggest"
    assert "live_warnings" in ex_resp.data
    assert any("BOGUS_MODE" in w for w in ex_resp.data["live_warnings"])
```

**Step 2: Run the test to verify it fails**

```bash
uv run pytest tests/test_autonomy_integration.py::TestAutonomyIntegration::test_defense_in_depth_mode_block_with_malformed_config_includes_warnings -v
```

Expected: FAIL — `AttributeError: 'NoneType' has no attribute '__getitem__'` (no `data`) or `KeyError`.

**Step 3: Implement the fix**

In `ticket_engine_core.py`, replace the mode block return (L1178–1183):

Current:
```python
        if config.mode != "auto_audit":
            return EngineResponse(
                state="policy_blocked",
                message=f"Defense-in-depth: autonomy mode {config.mode!r} blocks agent mutations",
                error_code="policy_blocked",
            )
```

Replace with:
```python
        if config.mode != "auto_audit":
            dind_data: dict[str, Any] = {"live_mode": config.mode}
            if config.warnings:
                dind_data["live_warnings"] = list(config.warnings)
            return EngineResponse(
                state="policy_blocked",
                message=f"Defense-in-depth: autonomy mode {config.mode!r} blocks agent mutations",
                error_code="policy_blocked",
                data=dind_data,
            )
```

**Step 4: Run the new test to verify it passes**

```bash
uv run pytest tests/test_autonomy_integration.py::TestAutonomyIntegration::test_defense_in_depth_mode_block_with_malformed_config_includes_warnings -v
```

Expected: PASS.

**Step 5: Run the full integration test suite**

```bash
uv run pytest tests/test_autonomy_integration.py -v
```

Expected: all 7 tests pass.

**Step 6: Commit**

```bash
git add packages/plugins/ticket/scripts/ticket_engine_core.py \
        packages/plugins/ticket/tests/test_autonomy_integration.py
git commit -m "feat(ticket): add live_mode and live_warnings to defense-in-depth mode block response (A-009)"
```

---

## Task 3: Full test suite and PR

**Step 1: Run the full test suite**

```bash
cd packages/plugins/ticket
uv run pytest -v
```

Expected: 568 tests pass (566 existing + 2 new).

**Step 2: Run Ruff on all touched files**

```bash
uv run ruff check scripts/ticket_engine_core.py tests/test_autonomy_integration.py
```

Expected: no output.

**Step 3: Open the PR**

```bash
cd /Users/jp/Projects/active/claude-code-tool-dev
gh pr create \
  --title "feat(ticket): propagate autonomy config warnings in execute responses (A-009)" \
  --body "$(cat <<'EOF'
## Summary

- Enriches the `policy_changed_since_preflight` response in `engine_execute` with `live_warnings` when the live config was malformed (A-009)
- Enriches the defense-in-depth mode block response in `engine_execute` with `live_mode` and `live_warnings` when the live config was malformed (A-009)
- Fixes pre-existing Ruff F401 (unused `compute_target_fp` import in `test_autonomy_integration.py`)

## Motivation

When `ticket.local.md` is malformed, `AutonomyConfig` self-heals to safe defaults and records why in `.warnings`. Previously those warnings evaporated when execute blocked due to a degraded live config — the caller couldn't tell whether the block was from an intentional policy change or a malformed config. Now both blocking responses surface `live_warnings` when the config was degraded.

## Test plan

- [ ] `test_policy_changed_with_malformed_live_config_includes_warnings` — asserts `live_warnings` in policy-changed response
- [ ] `test_defense_in_depth_mode_block_with_malformed_config_includes_warnings` — asserts `live_mode` and `live_warnings` in mode block response
- [ ] All 568 tests pass (`uv run pytest`)
- [ ] Ruff clean on touched files

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Reference

| What | Where |
|------|-------|
| Policy-changed return | `ticket_engine_core.py:1054–1059` |
| Mode block return | `ticket_engine_core.py:1178–1183` |
| Policy fingerprint | `ticket_engine_core.py:885–887` (`(mode, max_creates)` — warnings excluded) |
| Integration test file | `packages/plugins/ticket/tests/test_autonomy_integration.py` |
| Architectural review | `docs/prompts/ticket-plugin-architectural-review.md` |
