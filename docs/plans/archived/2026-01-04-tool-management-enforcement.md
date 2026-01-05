# Design: Tool Management Enforcement

## Goal

Enforce mise/uv/brew tool management patterns through automated validation with educational feedback.

**Reference:** `~/Documents/mise-tool-management.md`

---

## Design Decisions

### Documentation Verification

This design was verified against official Claude Code documentation (2026-01-04):

| Claim | Source | Status |
|-------|--------|--------|
| Exit code 2 + stderr blocks tool calls | [hooks.md](https://code.claude.com/docs/en/hooks) | ✅ Verified |
| `hookSpecificOutput.permissionDecision: "deny"` alternative | [hooks.md](https://code.claude.com/docs/en/hooks) | ✅ Verified |
| JSON in stdout ignored for exit code 2 | [hooks.md](https://code.claude.com/docs/en/hooks) | ✅ Verified |
| `Bash(pattern:*)` prefix matching | [iam.md](https://code.claude.com/docs/en/iam) | ✅ Verified |
| Permissions deny bypasses documented | [iam.md](https://code.claude.com/docs/en/iam) | ✅ Verified |

**Key finding:** The original `{"decision": "block"}` format was non-standard. Corrected to use exit code 2 + stderr.

### Defense in Depth

Two layers protect against tool management violations:

| Layer | System | Role |
|-------|--------|------|
| Primary | PreToolUse hook | Catches patterns, provides educational messages, handles exceptions |
| Backup | Permissions deny | Silent fallback if hook fails |

Hooks run before permissions, so the hook handles all logic. Permissions are redundant but safe.

### What Gets Blocked

| Pattern | Why |
|---------|-----|
| `pip install` | Pollutes global Python |
| `pip3 install` | Same |
| `python -m pip install` | Same (workaround) |
| `python3 -m pip install` | Same (workaround) |
| `uv pip install` | Bypasses lockfile management |
| `brew install <dev-tool>` | Dev tools need version management via mise |

**Exception:** `pip install -e` and `pip install --editable` (editable install of current project) are allowed.

### DEV_TOOLS Set

Core tools where `brew install` is always wrong:

```python
DEV_TOOLS = {
    # Python linters/formatters/type checkers
    "ruff", "black", "mypy", "flake8", "pylint", "isort",
    # Testing
    "pytest",
    # Node tools
    "prettier", "eslint", "pyright", "typescript",
}
```

Intentionally minimal to reduce false positives. Expand based on real-world usage.

### Educational Messages

Messages explain WHY the pattern is wrong and WHAT to do instead:

**`pip install <pkg>` / `pip3 install <pkg>`:**
```
pip install pollutes global Python.

For project dependencies:
  uv add <pkg>              # adds to pyproject.toml and installs

For global dev tools:
  Add to ~/.config/mise/config.toml:
    [tools]
    "pipx:<pkg>" = "latest"
  Then: mise install

Reference: ~/Documents/mise-tool-management.md
```

**`uv pip install <pkg>`:**
```
uv pip install bypasses lockfile management.

Use instead:
  uv add <pkg>              # adds to pyproject.toml
  uv add --group dev <pkg>  # for dev dependencies
  uv sync                   # install from lockfile

This ensures reproducible environments and proper dependency tracking.

Reference: ~/Documents/mise-tool-management.md
```

**`brew install <dev-tool>`:**
```
Dev tools like {tool} need version management via mise, not brew.

If already in mise config:
  mise install

To add to mise (~/.config/mise/config.toml):
  [tools]
  "pipx:{tool}" = "latest"    # for Python tools
  "npm:{tool}" = "latest"     # for Node tools

Then: mise install

Reference: ~/Documents/mise-tool-management.md
```

### Documentation

Minimal section in CLAUDE.md (hook enforces, docs orient):

```markdown
## Tool Management

Keep global Python pristine. The hook blocks violations automatically.

| Do this | Not this |
|---------|----------|
| `uv add <pkg>` | `pip install` |
| `uv add --group dev <tool>` | `uv pip install` |
| `mise install` | `brew install <dev-tool>` |

Reference: `~/Documents/mise-tool-management.md`
```

---

## Implementation

### Files to Create/Modify

| File | Action |
|------|--------|
| `.claude/hooks/validate-tool-patterns.py` | Create hook script |
| `.claude/settings.json` | Add permissions deny rules |
| `CLAUDE.md` | Add minimal Tool Management section |

### Hook: `.claude/hooks/validate-tool-patterns.py`

```python
#!/usr/bin/env python3
# /// hook
# event: PreToolUse
# matcher: Bash
# timeout: 60000
# ///
"""
Enforce tool management patterns.

Output format: Exit code 2 + stderr message (per Claude Code hooks documentation).
JSON output is NOT used because stdout is ignored for exit code 2.

Blocks:
- pip install / pip3 install (except -e/--editable for editable installs)
- python -m pip install variants
- uv pip install
- brew install <dev-tool>

Provides educational messages explaining the correct approach.
Reference: ~/Documents/mise-tool-management.md
"""

import json
import sys

DEV_TOOLS = {
    "ruff", "black", "mypy", "flake8", "pylint", "isort",
    "pytest",
    "prettier", "eslint", "pyright", "typescript",
}

MSG_PIP = """pip install pollutes global Python.

For project dependencies:
  uv add <pkg>              # adds to pyproject.toml and installs

For global dev tools:
  Add to ~/.config/mise/config.toml:
    [tools]
    "pipx:<pkg>" = "latest"
  Then: mise install

Reference: ~/Documents/mise-tool-management.md"""

MSG_UV_PIP = """uv pip install bypasses lockfile management.

Use instead:
  uv add <pkg>              # adds to pyproject.toml
  uv add --group dev <pkg>  # for dev dependencies
  uv sync                   # install from lockfile

This ensures reproducible environments and proper dependency tracking.

Reference: ~/Documents/mise-tool-management.md"""

MSG_BREW = """Dev tools like {tool} need version management via mise, not brew.

If already in mise config:
  mise install

To add to mise (~/.config/mise/config.toml):
  [tools]
  "pipx:{tool}" = "latest"    # for Python tools
  "npm:{tool}" = "latest"     # for Node tools

Then: mise install

Reference: ~/Documents/mise-tool-management.md"""


def check_command(command: str) -> tuple[bool, str]:
    """Check if command violates tool management patterns.

    Returns (should_block, reason).
    """
    cmd_lower = command.lower()

    # Check for pip install patterns (but allow -e for editable installs)
    pip_patterns = ["pip install", "pip3 install"]
    for pattern in pip_patterns:
        if pattern in cmd_lower:
            # Allow editable installs (both short and long form)
            editable_patterns = ["install -e", "install --editable"]
            if any(p in cmd_lower for p in editable_patterns):
                return False, ""
            return True, MSG_PIP

    # Check for uv pip install
    if "uv pip install" in cmd_lower:
        return True, MSG_UV_PIP

    # Check for brew install <dev-tool>
    if "brew install" in cmd_lower:
        for tool in DEV_TOOLS:
            if f"brew install {tool}" in cmd_lower:
                return True, MSG_BREW.format(tool=tool)

    return False, ""


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # Allow if we can't parse input

    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")

    if not command:
        sys.exit(0)  # Allow if no command

    should_block, reason = check_command(command)

    if should_block:
        # Exit code 2 = block, stderr = message shown to Claude
        print(reason, file=sys.stderr)
        sys.exit(2)

    sys.exit(0)  # Allow


if __name__ == "__main__":
    main()
```

### Permissions: `.claude/settings.json`

Add to existing settings (backup layer):

```json
{
  "permissions": {
    "deny": [
      "Bash(pip install:*)",
      "Bash(pip3 install:*)",
      "Bash(uv pip install:*)",
      "Bash(brew install ruff:*)",
      "Bash(brew install black:*)",
      "Bash(brew install mypy:*)",
      "Bash(brew install flake8:*)",
      "Bash(brew install pylint:*)",
      "Bash(brew install isort:*)",
      "Bash(brew install pytest:*)",
      "Bash(brew install prettier:*)",
      "Bash(brew install eslint:*)",
      "Bash(brew install pyright:*)",
      "Bash(brew install typescript:*)"
    ]
  }
}
```

Note: `pip install -e` is NOT in permissions deny because prefix matching would block it. The hook handles the exception; permissions are backup for non-exception cases.

### CLAUDE.md Addition

Append to end of file:

```markdown
## Tool Management

Keep global Python pristine. The hook blocks violations automatically.

| Do this | Not this |
|---------|----------|
| `uv add <pkg>` | `pip install` |
| `uv add --group dev <tool>` | `uv pip install` |
| `mise install` | `brew install <dev-tool>` |

Reference: `~/Documents/mise-tool-management.md`
```

---

## Verification

After implementation, test these commands:

| Command | Expected |
|---------|----------|
| `pip install requests` | BLOCK with educational message |
| `pip3 install requests` | BLOCK with educational message |
| `python -m pip install requests` | BLOCK with educational message |
| `uv pip install requests` | BLOCK with educational message |
| `brew install ruff` | BLOCK with educational message |
| `brew install pytest` | BLOCK with educational message |
| `pip install -e .` | ALLOW (editable install exception) |
| `pip install --editable .` | ALLOW (editable install exception) |
| `uv add requests` | ALLOW |
| `uv run scripts/inventory` | ALLOW |
| `mise install` | ALLOW |
| `brew install ripgrep` | ALLOW (not a dev tool) |

---

## Post-Implementation

1. Run `uv run scripts/sync-settings` to wire up hook (if using sync-settings workflow)
2. Delete `~/.claude/plans/vivid-prancing-steele.md` (superseded by this design)
