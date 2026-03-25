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
