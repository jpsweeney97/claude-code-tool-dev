# Cross-Model Plugin Architectural Remediation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Address 5 validated findings from the cross-model plugin design review: asymmetric credential scanning, MCP tool name fragility, analytics subsystem gravity, orphaned comment codes, and missing governance guardrails.

**Architecture:** Three changes in dependency order: (P3) drift-hardening governance tests that catch renames and unauthorized bypass, (P1) boundary canonicalization that routes `codex_delegate.py` through the shared `consultation_safety.check_tool_input` wrapper, (P2) analytics slimming that makes the markdown regex fallback lazy and adds observability. All changes are within `packages/plugins/cross-model/`.

**Tech Stack:** Python 3.14, pytest, ripgrep patterns for file scanning tests

**Source:** Design review + two Codex dialogues (threads `019d2303-7c69-7140-945f-519d469b5617` evaluative, `019d2324-69c1-7971-a311-8f4b95213896` exploratory).

---

## File Map

### New Files
| File | Responsibility |
|------|---------------|
| `tests/test_mcp_surface_contract.py` | Governance: MCP tool name consistency across 7 surfaces + raw exec guardrail |

### Modified Files
| File | Change |
|------|--------|
| `scripts/consultation_safety.py` | Add `DELEGATION_POLICY`, promote `_TIER_RANK` to `TIER_RANK` |
| `scripts/codex_delegate.py` | Replace `scan_text(prompt)` at step 4 with `check_tool_input` via `DELEGATION_POLICY` |
| `scripts/codex_guard.py` | Delete local `_TIER_RANK`, import `TIER_RANK` from consultation_safety |
| `scripts/emit_analytics.py` | Make `_parse_markdown_synthesis` lazy (call only on epilogue failure), add `parse_fallback_used` |
| `tests/test_consultation_safety.py` | Add tests for `DELEGATION_POLICY` and `TIER_RANK` export |
| `tests/test_codex_delegate.py` | Add test verifying `check_tool_input` path |
| `tests/test_emit_analytics.py` | Add tests for lazy fallback behavior and `parse_fallback_used` |

All paths relative to `packages/plugins/cross-model/`.

---

## Task 1: P3 — MCP Tool Name Drift Detection

**Files:**
- Create: `packages/plugins/cross-model/tests/test_mcp_surface_contract.py`

These are governance tests that validate the current codebase is consistent. They should PASS immediately. Their value is catching future drift.

- [ ] **Step 1: Write the tool name consistency test**

Create `tests/test_mcp_surface_contract.py`:

```python
"""MCP tool name surface contract tests.

Validates that MCP tool names derived from .mcp.json are consistent
across all surfaces that reference them: hooks.json, consultation_safety.py,
skills, agents, contracts, and documentation.
"""

import json
import re
from pathlib import Path

import pytest

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_MCP_JSON = _PLUGIN_ROOT / ".mcp.json"
_PLUGIN_JSON = _PLUGIN_ROOT / ".claude-plugin" / "plugin.json"


def _derive_tool_names() -> dict[str, str]:
    """Derive expected MCP tool name prefixes from .mcp.json + plugin.json.

    Claude Code plugin tool naming: mcp__plugin_{plugin}_{server}__{tool}
    Returns dict mapping server key to expected prefix string.
    """
    with open(_PLUGIN_JSON) as f:
        plugin = json.load(f)
    plugin_name = plugin["name"]

    with open(_MCP_JSON) as f:
        mcp = json.load(f)

    return {
        server_key: f"mcp__plugin_{plugin_name}_{server_key}__"
        for server_key in mcp["mcpServers"]
    }


# Surfaces that must reference MCP tool names consistently
_SURFACES = [
    _PLUGIN_ROOT / "hooks" / "hooks.json",
    _PLUGIN_ROOT / "scripts" / "consultation_safety.py",
    _PLUGIN_ROOT / "skills" / "codex" / "SKILL.md",
    _PLUGIN_ROOT / "skills" / "dialogue" / "SKILL.md",
    _PLUGIN_ROOT / "agents" / "codex-dialogue.md",
    _PLUGIN_ROOT / "agents" / "codex-reviewer.md",
    _PLUGIN_ROOT / "references" / "consultation-contract.md",
]


class TestToolNameConsistency:
    """All surfaces must use tool names derived from .mcp.json + plugin.json."""

    def test_all_surfaces_exist(self):
        for surface in _SURFACES:
            assert surface.exists(), f"Missing surface: {surface.relative_to(_PLUGIN_ROOT)}"

    def test_tool_names_match_derived_prefixes(self):
        """Every mcp__plugin_cross-model_ reference must start with a derived prefix."""
        prefixes = _derive_tool_names()
        all_valid_prefixes = list(prefixes.values())
        pattern = re.compile(r"mcp__plugin_cross-model_\w+__\w[\w-]*")

        for surface in _SURFACES:
            if not surface.exists():
                continue
            content = surface.read_text()
            for tool_name in pattern.findall(content):
                assert any(
                    tool_name.startswith(p) for p in all_valid_prefixes
                ), (
                    f"Tool name {tool_name!r} in {surface.name} "
                    f"does not match any derived prefix: {all_valid_prefixes}"
                )

    def test_codex_server_tools_referenced(self):
        """At least one surface references the codex server tools."""
        prefix = _derive_tool_names()["codex"]
        assert any(
            prefix in s.read_text() for s in _SURFACES if s.exists()
        ), f"No surface references codex tools with prefix {prefix}"

    def test_context_injection_server_tools_referenced(self):
        """At least one surface references the context-injection server tools."""
        prefix = _derive_tool_names()["context-injection"]
        assert any(
            prefix in s.read_text() for s in _SURFACES if s.exists()
        ), f"No surface references context-injection tools with prefix {prefix}"
```

- [ ] **Step 2: Run to verify tests pass**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_mcp_surface_contract.py::TestToolNameConsistency -v`
Expected: All 4 tests PASS (current code is consistent)

- [ ] **Step 3: Write the raw exec guardrail test**

Append to `tests/test_mcp_surface_contract.py`:

```python
class TestRawCodexExecGuardrail:
    """Surfaces that discuss Codex must not instruct raw 'codex exec' usage,
    except the delegate skill which legitimately calls the adapter."""

    _DENY_LIST = [
        _PLUGIN_ROOT / "skills" / "codex" / "SKILL.md",
        _PLUGIN_ROOT / "skills" / "dialogue" / "SKILL.md",
        _PLUGIN_ROOT / "agents" / "codex-dialogue.md",
        _PLUGIN_ROOT / "agents" / "codex-reviewer.md",
        _PLUGIN_ROOT / "references" / "consultation-contract.md",
        _PLUGIN_ROOT / "references" / "contract-agent-extract.md",
    ]

    # Matches "codex exec" as a command to run (not adapter discussion)
    _EXEC_PATTERN = re.compile(r'(?:^|\s)(?:`)?codex\s+exec(?:`)?(?:\s|$)', re.MULTILINE)
    _ADAPTER_DISCUSSION = re.compile(r'codex[\s_]exec.*(?:adapter|subprocess|pipeline|JSONL)', re.IGNORECASE)

    def test_deny_list_files_exist(self):
        for path in self._DENY_LIST:
            assert path.exists(), f"Missing: {path.relative_to(_PLUGIN_ROOT)}"

    def test_no_raw_exec_instructions(self):
        """Deny-listed files must not instruct raw codex exec usage."""
        violations = []
        for path in self._DENY_LIST:
            if not path.exists():
                continue
            content = path.read_text()
            for match in self._EXEC_PATTERN.finditer(content):
                line_start = content.rfind("\n", 0, match.start()) + 1
                line_end = content.find("\n", match.end())
                line = content[line_start:line_end if line_end != -1 else len(content)]
                if not self._ADAPTER_DISCUSSION.search(line):
                    violations.append(f"{path.relative_to(_PLUGIN_ROOT)}: {line.strip()!r:.120}")
        assert not violations, (
            f"Raw 'codex exec' instructions found in deny-listed files:\n"
            + "\n".join(f"  - {v}" for v in violations)
        )
```

- [ ] **Step 4: Run full test file**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_mcp_surface_contract.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add packages/plugins/cross-model/tests/test_mcp_surface_contract.py
git commit -m "test(cross-model): add MCP tool name drift detection and exec guardrail

Governance tests validate MCP tool name consistency across 7 surfaces
and prevent raw codex exec instructions in consultation-path files.
Tool names derived from .mcp.json + plugin.json.

Part of cross-model architectural remediation P3 (drift hardening)."
```

---

## Task 2: P1a — Add DELEGATION_POLICY and Promote TIER_RANK

**Files:**
- Modify: `packages/plugins/cross-model/scripts/consultation_safety.py:45-68`
- Modify: `packages/plugins/cross-model/tests/test_consultation_safety.py`

- [ ] **Step 1: Write failing tests for DELEGATION_POLICY**

Add to `tests/test_consultation_safety.py`:

```python
class TestDelegationPolicy:
    """DELEGATION_POLICY scans only the prompt field for credential egress."""

    def test_delegation_policy_exists(self):
        from scripts.consultation_safety import DELEGATION_POLICY
        assert DELEGATION_POLICY is not None

    def test_delegation_policy_content_fields(self):
        from scripts.consultation_safety import DELEGATION_POLICY
        assert DELEGATION_POLICY.content_fields == {"prompt"}

    def test_delegation_policy_expected_fields(self):
        from scripts.consultation_safety import DELEGATION_POLICY
        assert "model" in DELEGATION_POLICY.expected_fields
        assert "sandbox" in DELEGATION_POLICY.expected_fields
        assert "reasoning_effort" in DELEGATION_POLICY.expected_fields
        assert "full_auto" in DELEGATION_POLICY.expected_fields

    def test_delegation_policy_does_not_scan_unknown_fields(self):
        """Unknown fields are rejected by validation, not dispatched to Codex.
        Scanning them conflates 'unexpected input' with 'egress risk'."""
        from scripts.consultation_safety import DELEGATION_POLICY
        assert DELEGATION_POLICY.scan_unknown_fields is False

    def test_delegation_policy_blocks_credential_in_prompt(self):
        from scripts.consultation_safety import DELEGATION_POLICY, check_tool_input
        result = check_tool_input(
            {"prompt": "AKIAIOSFODNN7EXAMPLE", "model": "o3-pro", "sandbox": "read-only"},
            DELEGATION_POLICY,
        )
        assert result.action == "block"

    def test_delegation_policy_allows_clean_prompt(self):
        from scripts.consultation_safety import DELEGATION_POLICY, check_tool_input
        result = check_tool_input(
            {"prompt": "safe prompt", "model": "o3-pro", "sandbox": "read-only"},
            DELEGATION_POLICY,
        )
        assert result.action == "allow"


class TestTierRankExport:
    """TIER_RANK is a public constant for use by codex_guard.py."""

    def test_tier_rank_exported(self):
        from scripts.consultation_safety import TIER_RANK
        assert isinstance(TIER_RANK, dict)

    def test_tier_rank_ordering(self):
        from scripts.consultation_safety import TIER_RANK
        assert TIER_RANK["strict"] < TIER_RANK["contextual"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_consultation_safety.py -k "TestDelegationPolicy or TestTierRankExport" -v`
Expected: FAIL with ImportError (DELEGATION_POLICY and TIER_RANK not defined)

- [ ] **Step 3: Implement DELEGATION_POLICY and promote TIER_RANK**

In `scripts/consultation_safety.py`, add after `REPLY_POLICY` (after line 60):

```python
DELEGATION_POLICY = ToolScanPolicy(
    expected_fields={"model", "sandbox", "reasoning_effort", "full_auto"},
    content_fields={"prompt"},
    scan_unknown_fields=False,
)
```

Rename `_TIER_RANK` (line 143) to `TIER_RANK` and update its reference in `check_tool_input` (line 175).

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_consultation_safety.py -k "TestDelegationPolicy or TestTierRankExport" -v`
Expected: All 8 tests PASS

- [ ] **Step 5: Run full safety test suite**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_consultation_safety.py -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add packages/plugins/cross-model/scripts/consultation_safety.py packages/plugins/cross-model/tests/test_consultation_safety.py
git commit -m "feat(cross-model): add DELEGATION_POLICY and promote TIER_RANK

DELEGATION_POLICY scans only the prompt field with scan_unknown_fields=False.
TIER_RANK promoted from private to public for import by codex_guard.py.

Part of cross-model architectural remediation P1 (boundary canonicalization)."
```

---

## Task 3: P1b — Wire codex_delegate.py Through check_tool_input

**Files:**
- Modify: `packages/plugins/cross-model/scripts/codex_delegate.py:37-51,600-614`
- Modify: `packages/plugins/cross-model/tests/test_codex_delegate.py`

- [ ] **Step 1: Write test verifying new scan path**

Add to `tests/test_codex_delegate.py`:

```python
def test_credential_scan_uses_check_tool_input(monkeypatch, tmp_path):
    """Step 4 credential scan routes through consultation_safety.check_tool_input."""
    from unittest.mock import MagicMock
    from scripts.consultation_safety import SafetyVerdict

    mock_check = MagicMock(return_value=SafetyVerdict(action="allow", reason=None, tier=None))
    # NOTE: monkeypatch target must match the import alias in codex_delegate.py.
    # If the alias changes from _check_tool_input, this patch breaks silently.
    monkeypatch.setattr("scripts.codex_delegate._check_tool_input", mock_check)
    monkeypatch.setattr("scripts.codex_delegate._check_codex_version", lambda: None)
    monkeypatch.setattr("scripts.codex_delegate._check_clean_tree", lambda: None)
    monkeypatch.setattr("scripts.codex_delegate._check_secret_files", lambda: None)
    monkeypatch.setattr("scripts.codex_delegate._resolve_repo_root", lambda: tmp_path)

    input_file = tmp_path / "input.json"
    input_file.write_text('{"prompt": "test prompt", "sandbox": "read-only"}')

    # Will fail at subprocess stage but credential scan should have fired
    import scripts.codex_delegate as delegate
    delegate.run(input_file)

    mock_check.assert_called_once()
    payload = mock_check.call_args[0][0]
    assert "prompt" in payload
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_codex_delegate.py::test_credential_scan_uses_check_tool_input -v`
Expected: FAIL (codex_delegate doesn't import _check_tool_input yet)

- [ ] **Step 3: Wire codex_delegate.py imports and step 4**

Update the import blocks in `scripts/codex_delegate.py`. In the `if __package__` block, add:

```python
    from scripts.consultation_safety import (
        check_tool_input as _check_tool_input,
        DELEGATION_POLICY as _DELEGATION_POLICY,
    )
```

In the `else` block, add:

```python
    from consultation_safety import (
        check_tool_input as _check_tool_input,
        DELEGATION_POLICY as _DELEGATION_POLICY,
    )
```

Replace step 4 credential scan (around lines 600-614). Change:

```python
        if prompt and isinstance(prompt, str):
            try:
                scan_result = scan_text(prompt)
            except Exception as scan_exc:
                raise CredentialBlockError(
                    f"credential scan failed: {scan_exc}"
                ) from scan_exc
            if scan_result.action == "block":
                raise CredentialBlockError(scan_result.reason or "credential detected")
```

To:

```python
        if prompt and isinstance(prompt, str):
            try:
                verdict = _check_tool_input({"prompt": prompt}, _DELEGATION_POLICY)
            except Exception as scan_exc:
                raise CredentialBlockError(
                    f"credential scan failed: {scan_exc}"
                ) from scan_exc
            if verdict.action == "block":
                raise CredentialBlockError(verdict.reason or "credential detected")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_codex_delegate.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add packages/plugins/cross-model/scripts/codex_delegate.py packages/plugins/cross-model/tests/test_codex_delegate.py
git commit -m "refactor(cross-model): route delegate credential scan through check_tool_input

codex_delegate.py step 4 now uses consultation_safety.check_tool_input with
DELEGATION_POLICY instead of calling credential_scan.scan_text directly.
Closes the asymmetric scanning gap between consultation and delegation paths.

Part of cross-model architectural remediation P1 (boundary canonicalization)."
```

---

## Task 4: P1c — Deduplicate TIER_RANK in codex_guard.py

**Files:**
- Modify: `packages/plugins/cross-model/scripts/codex_guard.py:59-75,121`

- [ ] **Step 1: Update codex_guard.py imports and delete local constant**

Add `TIER_RANK` to the consultation_safety import in `scripts/codex_guard.py` (line 59 block). Delete the local `_TIER_RANK = {"strict": 0, "contextual": 1}` at line 121. Replace `_TIER_RANK` usage with `TIER_RANK` at line 126.

- [ ] **Step 2: Run tests**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_codex_guard.py tests/test_codex_guard_legacy.py -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add packages/plugins/cross-model/scripts/codex_guard.py
git commit -m "refactor(cross-model): deduplicate TIER_RANK in codex_guard.py

Import TIER_RANK from consultation_safety instead of defining locally.

Part of cross-model architectural remediation P1 (boundary canonicalization)."
```

---

## Task 5: P2 — Make Markdown Fallback Lazy in emit_analytics.py

**Files:**
- Modify: `packages/plugins/cross-model/scripts/emit_analytics.py:197-317`
- Modify: `packages/plugins/cross-model/tests/test_emit_analytics.py`

- [ ] **Step 1: Write failing tests for lazy fallback**

Add to `tests/test_emit_analytics.py`:

```python
class TestLazyMarkdownFallback:
    """Markdown fallback should only run when epilogue fails."""

    def test_epilogue_present_skips_markdown_parse(self, monkeypatch):
        from unittest.mock import MagicMock
        import scripts.emit_analytics as ea

        mock_md = MagicMock(return_value=({"parse_truncated": False}, True))
        monkeypatch.setattr(ea, "_parse_markdown_synthesis", mock_md)

        text = ('### Summary\n\n'
                '```json\n<!-- pipeline-data -->\n'
                '{"mode":"server_assisted","turn_count":3,"converged":true,'
                '"resolved_count":2,"unresolved_count":0,"emerged_count":1,'
                '"scout_count":0,"scope_breach_count":0,'
                '"termination_reason":"convergence"}\n```')
        ea.parse_synthesis(text)
        mock_md.assert_not_called()

    def test_epilogue_missing_triggers_markdown_parse(self, monkeypatch):
        from unittest.mock import MagicMock
        import scripts.emit_analytics as ea

        original = ea._parse_markdown_synthesis
        mock_md = MagicMock(side_effect=original)
        monkeypatch.setattr(ea, "_parse_markdown_synthesis", mock_md)

        text = '### Conversation Summary\n- **Turns:** 4\n- **Converged:** Yes\n'
        ea.parse_synthesis(text)
        mock_md.assert_called_once()

    def test_parse_fallback_used_true_when_markdown(self):
        from scripts.emit_analytics import parse_synthesis
        text = '### Conversation Summary\n- **Turns:** 4\n- **Converged:** Yes\n'
        result = parse_synthesis(text)
        assert result.get("parse_fallback_used") is True

    def test_parse_fallback_used_false_when_epilogue(self):
        from scripts.emit_analytics import parse_synthesis
        text = ('### Summary\n\n'
                '```json\n<!-- pipeline-data -->\n'
                '{"mode":"server_assisted","turn_count":3,"converged":true,'
                '"resolved_count":2,"unresolved_count":0,"emerged_count":1,'
                '"scout_count":0,"scope_breach_count":0,'
                '"termination_reason":"convergence"}\n```')
        result = parse_synthesis(text)
        assert result.get("parse_fallback_used") is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_emit_analytics.py::TestLazyMarkdownFallback -v`
Expected: FAIL (current code calls markdown unconditionally, no parse_fallback_used field)

- [ ] **Step 3: Extract truncation detection**

Add before `_parse_markdown_synthesis` in `scripts/emit_analytics.py`:

```python
def _detect_truncation(text: str) -> bool:
    """Detect whether synthesis text appears truncated.

    Checks for unclosed fenced code blocks (odd number of triple backticks).
    """
    return text.count("```") % 2 != 0
```

> **Reviewer note:** Verify this matches `_split_sections`'s actual truncation logic before implementing. If `_split_sections` uses a subtler definition of truncation (e.g., counting only top-level fences, or handling nested fences), this heuristic silently changes behavior. Check `_split_sections` and confirm equivalence.

- [ ] **Step 4: Make parse_synthesis lazy**

Replace the `parse_synthesis` function body. Change:

```python
    payload, warnings = _parse_epilogue(text)
    markdown_data, markdown_usable = _parse_markdown_synthesis(text)

    if _has_usable_epilogue_data(payload):
        return {
            ...
            "parse_truncated": markdown_data["parse_truncated"],
            "parse_failed": False,
        }

    if warnings:
        print(...)

    markdown_data["parse_failed"] = not markdown_usable
    return markdown_data
```

To:

```python
    payload, warnings = _parse_epilogue(text)

    if _has_usable_epilogue_data(payload):
        return {
            "resolved_count": payload.get("resolved_count", 0),
            "unresolved_count": payload.get("unresolved_count", 0),
            "emerged_count": payload.get("emerged_count", 0),
            "converged": payload.get("converged", False),
            "turn_count": payload.get("turn_count", 0),
            "thread_id": payload.get("thread_id"),
            "scout_count": payload.get("scout_count", 0),
            "mode": payload.get("mode"),
            "convergence_reason_code": payload.get("convergence_reason_code"),
            "scope_breach_count": payload.get("scope_breach_count", 0),
            "termination_reason": payload.get("termination_reason"),
            "parse_truncated": _detect_truncation(text),
            "parse_failed": False,
            "parse_fallback_used": False,
        }

    # Lazy fallback — only parse markdown when epilogue failed
    if warnings:
        print(
            "epilogue missing or malformed, falling back to markdown parsing",
            file=sys.stderr,
        )

    markdown_data, markdown_usable = _parse_markdown_synthesis(text)
    markdown_data["parse_failed"] = not markdown_usable
    markdown_data["parse_fallback_used"] = True
    return markdown_data
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_emit_analytics.py::TestLazyMarkdownFallback -v`
Expected: All 4 tests PASS

- [ ] **Step 6: Run full analytics test suite**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_emit_analytics.py tests/test_emit_analytics_legacy.py -v`
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add packages/plugins/cross-model/scripts/emit_analytics.py packages/plugins/cross-model/tests/test_emit_analytics.py
git commit -m "refactor(cross-model): make markdown synthesis fallback lazy

_parse_markdown_synthesis now only runs when epilogue is absent or unusable.
Adds parse_fallback_used signal and extracts _detect_truncation helper.

Part of cross-model architectural remediation P2 (analytics slimming)."
```

---

## Task 6: Final Validation

- [ ] **Step 1: Run full plugin test suite**

Run: `cd packages/plugins/cross-model && uv run pytest tests/ -v --tb=short`
Expected: All tests PASS, no regressions

- [ ] **Step 2: Run context-injection tests (separate package, should be unaffected)**

Run: `cd packages/plugins/cross-model/context-injection && uv run pytest -v --tb=short`
Expected: All tests PASS

- [ ] **Step 3: Verify governance tests catch simulated drift**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_mcp_surface_contract.py -v`
Expected: All 6 governance tests PASS

- [ ] **Step 4: Verify credential scan path end-to-end**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_codex_delegate.py -k credential -v`
Expected: All credential tests PASS through check_tool_input path

---

## Out of Scope (Deferred)

- **F6 (orphaned comment codes):** Resolving 62 tag references in codex_delegate.py requires finding or reconstructing review documents. Separate task.
- **Wire VALID_CONSULTATION_SOURCES into validate():** Low priority, no functional impact. Bundle with next analytics change.
- **scan_tool_input_detailed API for codex_guard.py:** Enhancement emerged from dialogue. Not needed for minimum scope.
- **compute_stats surfacing of parse_fallback_used:** Follow-on to P2 once the signal is proven useful.
- **parse_degraded documentation audit:** Pre-existing tech debt in compute_stats. Out of scope.
