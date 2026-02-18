# Codex Plugin PR #13 Review Fixes

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix all P1-P3 issues found in the PR #13 code review before merge.

**Architecture:** Three independent fix groups: (1) harden credential detection logic in `codex_guard.py`, (2) fix PATH portability in plugin `.mcp.json`, (3) update MCP tool names across skill/agent frontmatter and body text. All changes stay on the existing `feature/codex-plugin` branch.

**Reference:** PR #13 review findings — 2 P1s, 2 P2s, 2 P3s across 9 files.

**Branch:** Continue on `feature/codex-plugin` (already exists).

**Test command:** `uv run pytest tests/test_codex_guard.py -v`

**Dependencies between tasks:**
- Task 1: independent (codex_guard.py security hardening)
- Task 2: independent (.mcp.json PATH fix)
- Task 3: independent (tool name updates across 6 files)

---

## Task 1: Harden credential detection logic

**Addresses:** P1 #1 (`_check_contextual` single-match bypass), P1 #2 (`<`/`>` in placeholder words), P3 #5 (`"like"` placeholder word)

**Files:**
- Modify: `packages/plugins/codex/scripts/codex_guard.py:42-99` (patterns + detection)
- Modify: `packages/plugins/codex/scripts/codex_guard.py:144-149` (`_check_contextual`)
- Modify: `tests/test_codex_guard.py`

### Step 1: Write 4 failing tests

Add a new test class `TestSecurityHardening` after `TestPlaceholderSuppression` in `tests/test_codex_guard.py`:

```python
# ---------------------------------------------------------------------------
# Security hardening: regression tests for review findings
# ---------------------------------------------------------------------------


class TestSecurityHardening:
    def test_contextual_second_match_blocks_when_first_suppressed(self) -> None:
        """P1: _check_contextual must check ALL matches, not just the first."""
        token1 = "ghp_" + "A" * 36
        token2 = "ghp_" + "B" * 36
        # Padding pushes "example" >100 chars from second token
        padding = "x" * 80
        prompt = f"An example GitHub PAT: {token1} {padding} real: {token2}"
        assert MODULE.handle_pre(_pre(prompt)) == 2

    def test_html_context_does_not_suppress_real_key(self) -> None:
        """P1: angle brackets must not suppress contextual detection."""
        key = "sk-" + "a" * 40
        prompt = f"<div>{key}</div>"
        assert MODULE.handle_pre(_pre(prompt)) == 2

    def test_angle_bracket_comparison_does_not_suppress(self) -> None:
        """P1: comparison operators near tokens must not suppress."""
        token = "ghp_" + "A" * 36
        prompt = f"if count > 0; export TOKEN={token}"
        assert MODULE.handle_pre(_pre(prompt)) == 2

    def test_like_without_looks_does_not_suppress(self) -> None:
        """P3: standalone 'like' must not suppress contextual detection."""
        token = "ghp_" + "A" * 36
        prompt = f"I would like to use my token: {token}"
        assert MODULE.handle_pre(_pre(prompt)) == 2
```

### Step 2: Run tests to verify they fail

Run: `uv run pytest tests/test_codex_guard.py::TestSecurityHardening -v`
Expected: 4 FAILED (first three fail due to current bugs, fourth may also fail due to `"like"`)

### Step 3: Fix `_check_contextual` to use `finditer`

In `packages/plugins/codex/scripts/codex_guard.py`, replace the `_check_contextual` function (lines 144-149):

**Old:**
```python
def _check_contextual(prompt: str) -> str | None:
    """Return a reason string if a contextual-tier pattern matches without suppression."""
    for pat in _CONTEXTUAL:
        m = pat.search(prompt)
        if m and not _has_placeholder_context(prompt, m.start(), m.end()):
            return f"contextual:{pat.pattern[:60]}"
    return None
```

**New:**
```python
def _check_contextual(prompt: str) -> str | None:
    """Return a reason string if any contextual-tier match lacks placeholder context."""
    for pat in _CONTEXTUAL:
        for m in pat.finditer(prompt):
            if not _has_placeholder_context(prompt, m.start(), m.end()):
                return f"contextual:{pat.pattern[:60]}"
    return None
```

### Step 4: Remove `<`, `>`, and `like` from `_PLACEHOLDER_WORDS`

In `packages/plugins/codex/scripts/codex_guard.py`, replace the `_PLACEHOLDER_WORDS` frozenset (lines 72-91):

**Old:**
```python
_PLACEHOLDER_WORDS: frozenset[str] = frozenset(
    [
        "format",
        "example",
        "looks",
        "like",
        "placeholder",
        "dummy",
        "sample",
        "suppose",
        "hypothetical",
        "redact",
        "redacted",
        "your-",
        "my-",
        "<",
        ">",
        "[redacted",
    ]
)
```

**New:**
```python
_PLACEHOLDER_WORDS: frozenset[str] = frozenset(
    [
        "format",
        "example",
        "looks",
        "placeholder",
        "dummy",
        "sample",
        "suppose",
        "hypothetical",
        "redact",
        "redacted",
        "your-",
        "my-",
        "[redacted",
    ]
)
```

Removed: `"like"` (too common in English — "I would like to use my token..."), `"<"` and `">"` (match any XML/HTML/template/comparison context). The existing `"your-"` and `"my-"` already catch `<your-token-here>` patterns via the hyphenated prefix.

### Step 5: Run new tests to verify they pass

Run: `uv run pytest tests/test_codex_guard.py::TestSecurityHardening -v`
Expected: 4 PASSED

### Step 6: Run full test suite

Run: `uv run pytest tests/test_codex_guard.py -v`
Expected: 24 PASSED (20 existing + 4 new)

Verify existing placeholder suppression tests still pass — they test single matches with nearby placeholder words, which `finditer` handles identically to `search` for single-match cases.

### Step 7: Lint

Run: `ruff check packages/plugins/codex/scripts/codex_guard.py tests/test_codex_guard.py`
Expected: No errors

### Step 8: Commit

```bash
git add packages/plugins/codex/scripts/codex_guard.py tests/test_codex_guard.py
git commit -m "fix(codex-plugin): harden credential detection — check all matches, remove broad placeholders

- _check_contextual now uses finditer to check ALL matches per regex,
  not just the first. Prevents bypass where a leading example-context
  match masks a real credential later in the same prompt.
- Remove '<' and '>' from placeholder words — single-char entries
  created broad false negatives in XML/HTML/template contexts.
- Remove 'like' from placeholder words — too common in English,
  'looks' alone catches the intended 'looks like sk-...' pattern.
- 4 new regression tests for all three fixes.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Fix PATH inheritance in plugin `.mcp.json`

**Addresses:** P2 #3 (hardcoded PATH replaces caller environment)

**Files:**
- Modify: `packages/plugins/codex/.mcp.json`

### Step 1: Remove PATH from env

In `packages/plugins/codex/.mcp.json`, replace the entire file:

**Old:**
```json
{
  "mcpServers": {
    "codex": {
      "type": "stdio",
      "command": "codex",
      "args": ["mcp-server"],
      "env": {
        "CODEX_SANDBOX": "seatbelt",
        "PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin"
      }
    }
  }
}
```

**New:**
```json
{
  "mcpServers": {
    "codex": {
      "type": "stdio",
      "command": "codex",
      "args": ["mcp-server"],
      "env": {
        "CODEX_SANDBOX": "seatbelt"
      }
    }
  }
}
```

The `env` field in MCP server config merges with the parent process environment — it doesn't replace it. Removing `PATH` lets the `stdio` subprocess inherit the user's actual PATH, which already contains `codex` (required for installation).

### Step 2: Reinstall plugin and verify MCP connects

Run: `claude plugin marketplace update cross-model && claude plugin install codex@cross-model`

Then start a new Claude Code session and verify the codex MCP server connects. Check that `/codex test` or a simple Codex call works.

**If codex not found (fallback):** The parent PATH isn't inherited. In that case, use the fallback approach — test whether simple `${PATH}` expansion (without `:-` default syntax) works:

```json
"env": {
  "CODEX_SANDBOX": "seatbelt",
  "PATH": "${PATH}:/opt/homebrew/bin"
}
```

If simple `${PATH}` also doesn't expand, revert to the hardcoded PATH but add common user-managed directories:

```json
"PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:/opt/homebrew/sbin"
```

Document whichever approach works in the CHANGELOG.

### Step 3: Commit

```bash
git add packages/plugins/codex/.mcp.json
git commit -m "fix(codex-plugin): inherit PATH from parent env instead of hardcoding

Remove hardcoded PATH from plugin .mcp.json env field. The stdio MCP
process inherits the parent environment; the env field merges additional
vars rather than replacing the entire environment. This fixes
installations where codex is in user-managed locations (nvm, fnm, asdf,
volta, mise) that weren't in the hardcoded PATH.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Update MCP tool names in skill and agent files

**Addresses:** P2 #4 (agent `tools` frontmatter — confirmed P1), P3 #6 (inline body references)

**Files:**
- Modify: `packages/plugins/codex/skills/codex/SKILL.md` (frontmatter + body)
- Modify: `packages/plugins/codex/agents/codex-dialogue.md` (frontmatter + body)
- Modify: `.claude/skills/codex/SKILL.md` (frontmatter + body)
- Modify: `.claude/agents/codex-dialogue.md` (frontmatter + body)
- Modify: `packages/plugins/codex/references/consultation-contract.md`
- Modify: `docs/references/consultation-contract.md`

**Rename mapping (single operation per file):**

Since `mcp__codex__codex` is a prefix of `mcp__codex__codex-reply`, a single `replace_all` with `old="mcp__codex__codex"` → `new="mcp__plugin_codex_codex__codex"` correctly transforms both:
- `mcp__codex__codex` → `mcp__plugin_codex_codex__codex`
- `mcp__codex__codex-reply` → `mcp__plugin_codex_codex__codex-reply`

### Step 1: Update plugin-bundled skill

In `packages/plugins/codex/skills/codex/SKILL.md`, replace all occurrences of `mcp__codex__codex` with `mcp__plugin_codex_codex__codex`.

**Affected locations (8 occurrences):**
- Line 6: `allowed-tools: mcp__codex__codex, mcp__codex__codex-reply` (frontmatter)
- Line 37: `- \`mcp__codex__codex\`` (body)
- Line 38: `- \`mcp__codex__codex-reply\`` (body)
- Line 65: `Only \`prompt\` is required by the MCP tool schema for \`mcp__codex__codex\`.` (body)
- Line 156: `Call \`mcp__codex__codex\` with parameters` (body)
- Line 160: `Call \`mcp__codex__codex-reply\` per` (body)

### Step 2: Update plugin-bundled agent

In `packages/plugins/codex/agents/codex-dialogue.md`, replace all occurrences of `mcp__codex__codex` with `mcp__plugin_codex_codex__codex`.

**Affected locations (14 occurrences):**
- Line 4: `tools:` frontmatter
- Lines 14, 81, 347, 359: body references

### Step 3: Update project-level skill

In `.claude/skills/codex/SKILL.md`, replace all occurrences of `mcp__codex__codex` with `mcp__plugin_codex_codex__codex`.

Same locations as Step 1.

### Step 4: Update project-level agent

In `.claude/agents/codex-dialogue.md`, replace all occurrences of `mcp__codex__codex` with `mcp__plugin_codex_codex__codex`.

Same locations as Step 2.

### Step 5: Update plugin-bundled consultation contract

In `packages/plugins/codex/references/consultation-contract.md`, replace all occurrences of `mcp__codex__codex` with `mcp__plugin_codex_codex__codex`.

### Step 6: Update source consultation contract

In `docs/references/consultation-contract.md`, replace all occurrences of `mcp__codex__codex` with `mcp__plugin_codex_codex__codex`.

### Step 7: Verify no old names remain

Run:
```bash
rg "mcp__codex__codex" packages/plugins/codex/ .claude/skills/codex/ .claude/agents/codex-dialogue.md docs/references/consultation-contract.md
```

Expected: No matches. Every instance should now be `mcp__plugin_codex_codex__codex` (with or without `-reply` suffix).

**Exceptions (these should NOT be renamed — verify they are untouched):**
- `packages/plugins/codex/scripts/codex_guard.py` line 3: docstring says "for mcp__codex__codex" — this is a comment describing the original design intent. Update to match: `mcp__plugin_codex_codex__codex`.
- `packages/plugins/codex/hooks/hooks.json`: already uses `mcp__plugin_codex_codex__codex` (fixed in commit `f79d192`). Verify unchanged.
- `tests/test_codex_guard.py` line 31: uses `mcp__codex__codex` as the default tool name in the `_pre` helper. This is fine — the guard logic doesn't branch on tool name, it only uses it for logging. Tests still pass regardless of tool name string.

### Step 8: Update codex_guard.py docstring

In `packages/plugins/codex/scripts/codex_guard.py` line 3, update the docstring:

**Old:** `codex_guard.py — PreToolUse/PostToolUse enforcement hook for mcp__codex__codex.`
**New:** `codex_guard.py — PreToolUse/PostToolUse enforcement hook for mcp__plugin_codex_codex__codex.`

### Step 9: Commit

```bash
git add packages/plugins/codex/skills/codex/SKILL.md \
       packages/plugins/codex/agents/codex-dialogue.md \
       packages/plugins/codex/references/consultation-contract.md \
       packages/plugins/codex/scripts/codex_guard.py \
       .claude/skills/codex/SKILL.md \
       .claude/agents/codex-dialogue.md \
       docs/references/consultation-contract.md
git commit -m "fix(codex-plugin): update MCP tool names to plugin-namespaced convention

Plugin-provided MCP tools use mcp__plugin_<plugin>_<server>__<tool>
naming, not mcp__<server>__<tool>. The hook matcher was already fixed
(f79d192) but skill allowed-tools, agent tools frontmatter, and all
inline body references still used the old naming.

- Skill allowed-tools: auto-approval now targets the correct tool names
- Agent tools: subagent can now actually call Codex MCP tools (was a
  hard restriction with wrong names — confirmed blocker)
- Body text: instructions reference correct tool names
- Both plugin-bundled and project-level copies updated
- Both consultation contract copies updated

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Final Verification

Run: `uv run pytest tests/test_codex_guard.py -v`
Expected: All tests pass (20 existing + 4 new = 24)

Run: `ruff check packages/plugins/codex/scripts/codex_guard.py tests/test_codex_guard.py`
Expected: No errors

Verify no old tool names remain:
```bash
rg "mcp__codex__codex[^_]" packages/plugins/codex/ .claude/skills/codex/ .claude/agents/codex-dialogue.md docs/references/consultation-contract.md
```
Expected: No matches (all renamed to `mcp__plugin_codex_codex__codex`)

Verify hooks.json unchanged (already correct):
```bash
rg "mcp__plugin_codex_codex__codex" packages/plugins/codex/hooks/hooks.json
```
Expected: Matches on both PreToolUse and PostToolUse matchers

## Summary of Deliverables

| File | Status | What This Plan Changes |
|------|--------|----------------------|
| `packages/plugins/codex/scripts/codex_guard.py` | Modified | `finditer` for all-match check, remove `<`, `>`, `like` from placeholders, update docstring |
| `tests/test_codex_guard.py` | Modified | 4 new security regression tests |
| `packages/plugins/codex/.mcp.json` | Modified | Remove hardcoded PATH, keep CODEX_SANDBOX only |
| `packages/plugins/codex/skills/codex/SKILL.md` | Modified | Plugin MCP tool names in frontmatter + body |
| `packages/plugins/codex/agents/codex-dialogue.md` | Modified | Plugin MCP tool names in frontmatter + body |
| `.claude/skills/codex/SKILL.md` | Modified | Plugin MCP tool names in frontmatter + body |
| `.claude/agents/codex-dialogue.md` | Modified | Plugin MCP tool names in frontmatter + body |
| `packages/plugins/codex/references/consultation-contract.md` | Modified | Plugin MCP tool names |
| `docs/references/consultation-contract.md` | Modified | Plugin MCP tool names |
