# Tool Management Enforcement Updates Implementation Plan

> **Status:** ✅ Completed 2026-01-04
>
> Commits: `8ef85ac`, `31cd909`, `9a4057d`, `a9a2bf4`

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Update the tool-management-enforcement design document to align with official Claude Code documentation findings.

**Architecture:** The design document at `docs/plans/2026-01-04-tool-management-enforcement.md` contains three issues discovered during verification against official docs. We'll update the hook implementation, add missing pattern checks, and add a verification section documenting compliance.

**Tech Stack:** Python hooks, Claude Code settings.json, Markdown documentation

---

### Task 1: Fix Hook Output Format

**Files:**
- Modify: `docs/plans/2026-01-04-tool-management-enforcement.md:234-257` (main() function)

**Context:** The official Claude Code documentation states:
- Exit code 2 + stderr = blocking (JSON in stdout is IGNORED)
- Exit code 0 + JSON with `hookSpecificOutput.permissionDecision: "deny"` = blocking
- The current format `{"decision": "block", "reason": "..."}` is non-standard and won't work

**Step 1: Locate the incorrect main() function**

Find lines 234-257 containing:
```python
def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return  # Allow if we can't parse input
    ...
    if should_block:
        print(json.dumps({
            "decision": "block",
            "reason": reason
        }))
```

**Step 2: Replace with correct exit code implementation**

Replace the entire `main()` function (lines 234-256) with:

```python
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
```

**Step 3: Verify the edit**

Read lines 234-260 of the file to confirm the change is correct.

**Step 4: Commit**

```bash
git add docs/plans/2026-01-04-tool-management-enforcement.md
git commit -m "fix(hook): use exit code 2 + stderr for blocking per official docs"
```

---

### Task 2: Add --editable Long Form Pattern Check

**Files:**
- Modify: `docs/plans/2026-01-04-tool-management-enforcement.md:213-219` (pip pattern check)

**Context:** The current check only handles `-e` short form:
```python
if "install -e" in cmd_lower or "install -e." in cmd_lower.replace(" ", ""):
```

The official `pip` documentation also supports `--editable` as the long form flag.

**Step 1: Locate the editable install check**

Find lines 213-219 containing the pip pattern check.

**Step 2: Update the exception to include --editable**

Replace:
```python
            # Allow editable installs
            if "install -e" in cmd_lower or "install -e." in cmd_lower.replace(" ", ""):
                return False, ""
```

With:
```python
            # Allow editable installs (both short and long form)
            editable_patterns = ["install -e", "install --editable"]
            if any(p in cmd_lower for p in editable_patterns):
                return False, ""
```

**Step 3: Update the "Exception" section in documentation**

Find line 35 containing:
```markdown
**Exception:** `pip install -e` (editable install of current project) is allowed.
```

Replace with:
```markdown
**Exception:** `pip install -e` and `pip install --editable` (editable install of current project) are allowed.
```

**Step 4: Update verification table**

Find line 320 containing:
```markdown
| `pip install -e .` | ALLOW (editable install exception) |
```

Add a new row after it:
```markdown
| `pip install --editable .` | ALLOW (editable install exception) |
```

**Step 5: Verify the edits**

Read lines 35, 213-220, and 320-325 to confirm all changes are correct.

**Step 6: Commit**

```bash
git add docs/plans/2026-01-04-tool-management-enforcement.md
git commit -m "fix(hook): add --editable long form to exception patterns"
```

---

### Task 3: Add Documentation Verification Section

**Files:**
- Modify: `docs/plans/2026-01-04-tool-management-enforcement.md` (add section after line 11)

**Context:** Document that this design was verified against official Claude Code documentation, adding credibility and traceability.

**Step 1: Add verification section after Design Decisions header**

After line 11 (`## Design Decisions`), insert:

```markdown

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

```

**Step 2: Verify the edit**

Read lines 11-28 to confirm the section was added correctly.

**Step 3: Commit**

```bash
git add docs/plans/2026-01-04-tool-management-enforcement.md
git commit -m "docs: add documentation verification section"
```

---

### Task 4: Update Hook Docstring

**Files:**
- Modify: `docs/plans/2026-01-04-tool-management-enforcement.md:144-155` (hook docstring)

**Context:** Add information about the output format to the docstring for future maintainers.

**Step 1: Locate the hook docstring**

Find lines 144-155 containing:
```python
"""
Enforce tool management patterns.

Blocks:
- pip install / pip3 install (except -e for editable installs)
...
"""
```

**Step 2: Update docstring with output format info**

Replace with:
```python
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
```

**Step 3: Verify the edit**

Read lines 144-160 to confirm the docstring was updated.

**Step 4: Commit**

```bash
git add docs/plans/2026-01-04-tool-management-enforcement.md
git commit -m "docs: clarify hook output format in docstring"
```

---

### Task 5: Final Verification

**Files:**
- Read: `docs/plans/2026-01-04-tool-management-enforcement.md` (full file)

**Step 1: Read and verify all changes**

Read the complete file and verify:
- [ ] main() uses `sys.exit(2)` + stderr for blocking
- [ ] main() uses `sys.exit(0)` for allow/errors
- [ ] editable_patterns includes both `-e` and `--editable`
- [ ] Documentation Verification section present
- [ ] Exception text mentions `--editable`
- [ ] Verification table includes `--editable` test case
- [ ] Docstring mentions exit code 2 format

**Step 2: Run syntax check on embedded Python**

Verify the Python code in the design document is syntactically valid by extracting and checking:

```bash
# Extract hook code to temp file and check syntax
python3 -c "
import ast
code = '''
# Paste the full hook code here to verify
'''
ast.parse(code)
print('Syntax OK')
"
```

**Step 3: Final commit (if any fixes needed)**

```bash
git add docs/plans/2026-01-04-tool-management-enforcement.md
git commit -m "chore: final verification pass"
```

---

## Summary of Changes

| Location | Change |
|----------|--------|
| Lines 234-256 | Replace JSON output with exit code 2 + stderr |
| Lines 217-218 | Add `--editable` to exception patterns |
| Line 35 | Update exception description |
| Line 320 | Add `--editable` test case |
| After line 11 | Add Documentation Verification section |
| Lines 144-155 | Update docstring with format info |

**Total tasks:** 5
**Estimated time:** 15-20 minutes
