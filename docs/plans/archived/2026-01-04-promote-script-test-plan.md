# Promote Script Test Plan

> **Status:** ✅ EXECUTED 2026-01-05 — 15/17 tasks passed, 2 blocked (placeholders)

> **For Claude:** Execute tasks sequentially. Check preconditions before each task.

**Goal:** Verify `scripts/promote` correctly validates, diffs, and deploys extensions from sandbox to production.

**Architecture:** The promote script copies from `.claude/<type>/<name>` (sandbox) to `~/.claude/<type>/<name>` (production). Skills are directories; commands/agents are `.md` files; hooks can be `.py`, `.sh`, or no extension. Production currently uses symlinks to monorepo.

**Scope:** This plan tests `skill` and `hook` types. Command and agent types are placeholders (`.claude/commands/` and `.claude/agents/` contain only `.gitkeep`). See Tasks 15-16 for TODO markers.

**Tech Stack:** Python 3.12, uv, shutil, rich

---

## Critical Context

**Current state:** `~/.claude/skills/*` are symlinks → monorepo

**Promote behavior:** `shutil.rmtree(dest)` + `copytree()` replaces symlink with directory copy

**Test impact:** Promoting converts symlink to standalone copy. Cleanup restores symlinks.

**State tracking:** Actual state changes observed during execution:

| Resource | Initial State | After Task 2 | After Task 8 | After Task 14 |
|----------|---------------|--------------|--------------|---------------|
| `~/.claude/skills/config-optimize` | symlink | directory | directory | symlink ✓ |
| `~/.claude/hooks/block-keychain-extraction.py` | file* | file | file | file |

*Note: Hook was already a regular file, not a symlink as plan assumed.

---

## Analysis Notes

*Added 2026-01-04 after code review of `scripts/promote`*

**sync-settings behavior (Q1):**
- `--force` skips sync-settings prompt entirely (line 294: `if args.type == "hook" and not args.force`)
- `--dry-run` exits before reaching prompt code
- Interactive mode (no flags) prompts "Run sync-settings? [y/N]"
- Gap: No task tests the interactive sync-settings prompt → see Task 17

**Broken symlink handling (Q2):**
- `dest.exists()` returns `False` for broken symlinks (Python follows the link)
- Code skips `shutil.rmtree(dest)` when `dest.exists()` is false
- `shutil.copytree()` likely fails with `OSError` when symlink entry exists
- Caught by line 192, prints "OS error: ..."
- Task 13 will confirm empirically

**Commands/agents structure (Q3):**
- Both are single `.md` files, not directories
- Validation: must be file + `.md` extension
- Plan already correct

---

## Task 0: Pre-flight Verification

**Precondition:** None — this is the first task

**Files:**
- Test: `scripts/promote`
- Test: `scripts/sync-settings`

**Step 0: Ensure symlink state for testing**

```bash
# Check current state and restore symlink if needed
if [ -L ~/.claude/skills/config-optimize ]; then
  echo "STATE: symlink - ready for testing"
elif [ -d ~/.claude/skills/config-optimize ]; then
  echo "STATE: directory - converting to symlink"
  rm -r ~/.claude/skills/config-optimize
  ln -s ~/Projects/active/claude-code-tool-dev/.claude/skills/config-optimize ~/.claude/skills/
fi
```

Expected: Either "STATE: symlink" or "STATE: directory" with conversion

**Step 1: Verify promote script runs**

```bash
uv run scripts/promote --help
```

Expected: Usage text with `skill`, `command`, `agent`, `hook` types

**Step 2: Verify sync-settings exists**

```bash
ls -la scripts/sync-settings
```

Expected: File exists

**Step 3: Confirm symlink state**

```bash
file ~/.claude/skills/config-optimize
```

Expected: `symbolic link to ...`

**Checkpoint:** All steps pass → proceed to Task 1

---

## Task 1: Dry Run (Non-Destructive)

**Precondition:** Task 0 completed successfully

**Files:**
- Test: `scripts/promote`
- Observe: `~/.claude/skills/config-optimize`

**Step 1: Run dry-run promotion**

```bash
uv run scripts/promote skill config-optimize --dry-run
```

Expected: Shows diff panel, prints "Dry run - no changes made"

**Step 2: Verify diff shows expected content**

Expected in diff output:
- Source path: `.claude/skills/config-optimize`
- Dest path: `~/.claude/skills/config-optimize`
- File listing including `SKILL.md`

**Step 3: Verify exit code**

```bash
echo $?
```

Expected: `0`

**Step 4: Verify destination unchanged**

```bash
file ~/.claude/skills/config-optimize
```

Expected: `symbolic link` (not `directory`)

---

## Task 2: Actual Skill Promotion

**Precondition:** `file ~/.claude/skills/config-optimize` shows `symbolic link`

**Files:**
- Test: `scripts/promote`
- Modify: `~/.claude/skills/config-optimize` (symlink → directory)

**Step 0: Verify precondition**

```bash
file ~/.claude/skills/config-optimize
```

Expected: `symbolic link` — if `directory`, run Task 0 Step 0 first

**Step 1: Promote with force (skip prompt)**

```bash
uv run scripts/promote skill config-optimize --force
```

Expected: Shows diff, prints "Promoted skill 'config-optimize'"

**Step 2: Verify exit code**

```bash
echo $?
```

Expected: `0`

**Step 3: Verify symlink replaced with directory**

```bash
file ~/.claude/skills/config-optimize
```

Expected: `directory`

**Step 4: Verify contents copied**

```bash
ls ~/.claude/skills/config-optimize/SKILL.md
```

Expected: File exists

**State change:** `config-optimize` is now a directory (not symlink)

---

## Task 3: Idempotence (Already Up To Date)

**Precondition:** `file ~/.claude/skills/config-optimize` shows `directory` (Task 2 completed)

**Files:**
- Test: `scripts/promote`

**Step 0: Verify precondition**

```bash
file ~/.claude/skills/config-optimize
```

Expected: `directory` — if `symbolic link`, Task 2 didn't run

**Step 1: Promote same skill again**

```bash
uv run scripts/promote skill config-optimize
```

Expected: Prints "Already up to date." (no prompt, no diff)

**Step 2: Verify immediate exit (no user interaction)**

Expected: Command exits within 1 second without waiting for input

---

## Task 4: Missing Extension (Error Case)

**Precondition:** None — independent test

**Files:**
- Test: `scripts/promote`

**Step 1: Try to promote nonexistent skill**

```bash
uv run scripts/promote skill nonexistent-skill-12345
```

Expected:
- `Error: skill 'nonexistent-skill-12345' not found in sandbox`
- `Expected location: .claude/skills/nonexistent-skill-12345`

**Step 2: Verify exit code**

```bash
echo $?
```

Expected: `1`

---

## Task 5: Validation Failure (Missing SKILL.md)

**Precondition:** None — creates own test fixtures

**Files:**
- Create: `.claude/skills/broken-test/` (empty directory)
- Test: `scripts/promote`

**Step 1: Create invalid skill directory**

```bash
mkdir -p .claude/skills/broken-test
```

**Step 2: Try to promote**

```bash
uv run scripts/promote skill broken-test
```

Expected: `Validation errors:` followed by `Missing SKILL.md in .claude/skills/broken-test`

**Step 3: Verify exit code**

```bash
echo $?
```

Expected: `1`

**Step 4: Cleanup**

```bash
rm -r .claude/skills/broken-test
```

---

## Task 6: Hook Promotion (Dry Run)

**Precondition:** None — independent test

**Files:**
- Test: `scripts/promote`
- Observe: `.claude/hooks/block-keychain-extraction.py`

**Step 1: Run dry-run hook promotion**

```bash
uv run scripts/promote hook block-keychain-extraction --dry-run
```

Expected: Shows diff, prints "Dry run - no changes made"

**Step 2: Verify NO sync-settings prompt**

Expected: Output should NOT contain "Run sync-settings?" or similar prompt

---

## Task 7: Hook Validation (Non-Executable)

**Precondition:** None — creates own test fixtures

**Files:**
- Create: `.claude/hooks/broken-hook.py` (non-executable)
- Test: `scripts/promote`

**Step 1: Create non-executable hook**

```bash
touch .claude/hooks/broken-hook.py
```

**Step 2: Try to promote**

```bash
uv run scripts/promote hook broken-hook
```

Expected: "Validation errors:" with "not executable"

**Step 3: Verify exit code**

```bash
echo $?
```

Expected: `1`

**Step 4: Cleanup**

```bash
rm .claude/hooks/broken-hook.py
```

---

## Task 8: Hook Actual Promotion (with --force)

**Precondition:** None — uses separate hook, includes own cleanup

**Files:**
- Test: `scripts/promote`
- Modify: `~/.claude/hooks/block-keychain-extraction.py` (symlink → file)

**Step 1: Verify current state**

```bash
file ~/.claude/hooks/block-keychain-extraction.py
```

Expected: `symbolic link` or `Python script` — note current state for cleanup

**Step 2: Promote with --force**

```bash
uv run scripts/promote hook block-keychain-extraction --force
```

Expected: Shows diff, prints `Promoted hook 'block-keychain-extraction'`, NO sync-settings prompt

**Step 3: Verify file copied (not symlink)**

```bash
file ~/.claude/hooks/block-keychain-extraction.py
```

Expected: `Python script text executable` (not `symbolic link`)

**Step 4: Cleanup - restore symlink**

```bash
rm ~/.claude/hooks/block-keychain-extraction.py
ln -s ~/Projects/active/claude-code-tool-dev/.claude/hooks/block-keychain-extraction.py ~/.claude/hooks/
```

**Step 5: Verify cleanup**

```bash
file ~/.claude/hooks/block-keychain-extraction.py
```

Expected: `symbolic link`

---

## Task 9: New Destination (First-Time Promotion)

**Precondition:** None — creates own test fixtures

**Files:**
- Create: `.claude/skills/test-new-dest/SKILL.md`
- Create: `~/.claude/skills/test-new-dest/`

**Step 1: Create test skill**

```bash
mkdir -p .claude/skills/test-new-dest
cat > .claude/skills/test-new-dest/SKILL.md << 'EOF'
---
name: test-new-dest
description: Test skill for new destination
---

Test content
EOF
```

**Step 2: Verify destination doesn't exist**

```bash
ls ~/.claude/skills/test-new-dest 2>&1
```

Expected: `No such file or directory`

**Step 3: Promote**

```bash
uv run scripts/promote skill test-new-dest --force
```

Expected: Shows `New: ~/.claude/skills/test-new-dest (does not exist yet)`, promotes successfully

**Step 4: Verify created**

```bash
ls ~/.claude/skills/test-new-dest/SKILL.md
```

Expected: File exists

**Step 5: Cleanup**

```bash
rm -r .claude/skills/test-new-dest ~/.claude/skills/test-new-dest
```

---

## Task 10: User Cancellation (Interactive)

**Precondition:** `file ~/.claude/skills/config-optimize` shows `directory` (Task 2 completed)

**Files:**
- Test: `scripts/promote`

**Step 0: Modify source to create diff**

```bash
# Add a temporary marker to force a diff
echo "# test-marker-$(date +%s)" >> .claude/skills/config-optimize/SKILL.md
```

**Step 1: Run promotion, manually enter 'n' when prompted**

```bash
uv run scripts/promote skill config-optimize
```

When prompted `Proceed with promotion? [y/N]`, type `n` and press Enter.

Expected: Shows diff, prompts for confirmation, prints `Cancelled` after 'n'

**Step 2: Verify exit code**

```bash
echo $?
```

Expected: `0` (cancellation is not an error)

**Step 3: Verify no changes made**

```bash
grep "test-marker" ~/.claude/skills/config-optimize/SKILL.md
```

Expected: No match (marker not in destination)

**Step 4: Cleanup - remove marker from source**

```bash
# Remove the test marker line
sed -i '' '/^# test-marker-/d' .claude/skills/config-optimize/SKILL.md
```

---

## Task 11: Shell Hook Validation

**Precondition:** None — creates own test fixtures

**Files:**
- Create: `.claude/hooks/test-hook.sh`
- Test: `scripts/promote`

**Step 1: Create shell hook**

```bash
cat > .claude/hooks/test-hook.sh << 'EOF'
#!/bin/bash
# /// hook
# event: PreToolUse
# matcher: Bash
# ///
echo "test"
EOF
chmod +x .claude/hooks/test-hook.sh
```

**Step 2: Dry-run promote**

```bash
uv run scripts/promote hook test-hook --dry-run
```

Expected: Shows diff, validates successfully (no "Validation errors")

**Step 3: Cleanup**

```bash
rm .claude/hooks/test-hook.sh
```

---

## Task 12: Permission Error (Unwritable Destination)

**Precondition:** None — creates own test fixtures

**Files:**
- Create: `.claude/skills/perm-test/SKILL.md`
- Test: `scripts/promote`

**Step 1: Create test skill and destination**

```bash
mkdir -p .claude/skills/perm-test
echo -e "---\nname: perm-test\n---\nTest" > .claude/skills/perm-test/SKILL.md
mkdir -p ~/.claude/skills/perm-test
```

**Step 2: Make destination unwritable**

```bash
chmod 000 ~/.claude/skills/perm-test
```

**Step 3: Attempt promotion**

```bash
uv run scripts/promote skill perm-test --force
```

Expected: Error message containing `Permission denied`

**Step 4: Verify exit code**

```bash
echo $?
```

Expected: `1`

**Step 5: Cleanup**

```bash
chmod 755 ~/.claude/skills/perm-test
rm -r ~/.claude/skills/perm-test .claude/skills/perm-test
```

---

## Task 13: Broken Symlink in Destination

**Precondition:** None — creates own test fixtures

**Purpose:** Determine how `shutil.rmtree()` handles broken symlinks

**Prediction (from code review):** Fails with "OS error" because `dest.exists()` returns `False` for broken symlinks, skipping `rmtree()`, then `copytree()` fails when symlink entry exists. Update this section after execution.

**Files:**
- Create: `.claude/skills/broken-link-test/SKILL.md`
- Test: `scripts/promote`

**Step 1: Create test skill**

```bash
mkdir -p .claude/skills/broken-link-test
echo -e "---\nname: broken-link-test\n---\nTest" > .claude/skills/broken-link-test/SKILL.md
```

**Step 2: Create broken symlink at destination**

```bash
ln -s /nonexistent/path ~/.claude/skills/broken-link-test
```

**Step 3: Verify symlink is broken**

```bash
file ~/.claude/skills/broken-link-test
```

Expected: `broken symbolic link`

**Step 4: Attempt promotion**

```bash
uv run scripts/promote skill broken-link-test --force 2>&1
```

**Step 5: Record actual behavior**

**Observed behavior (2026-01-05):**
- Script shows: `New: /Users/jp/.claude/skills/broken-link-test (does not exist yet)`
- Then fails with: `OS error: [Errno 17] File exists: '/Users/jp/.claude/skills/broken-link-test'`
- Exit code: 1

This confirms the prediction: `dest.exists()` returns `False` for broken symlinks, so script thinks destination is new. But `copytree()` fails because the symlink entry exists on disk.

**Recommended fix:** Check `dest.is_symlink()` before `dest.exists()` and remove symlink first.

**Step 6: Cleanup**

```bash
rm ~/.claude/skills/broken-link-test && rm -r .claude/skills/broken-link-test
```

---

## Task 14: Cleanup (Restore Symlinks)

**Precondition:** Test session complete

**Purpose:** Restore production to symlink state

**Files:**
- Modify: `~/.claude/skills/config-optimize` (directory → symlink)

**Step 1: Check if cleanup needed**

```bash
file ~/.claude/skills/config-optimize
```

- If `symbolic link`: Skip to Step 5
- If `directory`: Continue with Steps 2-4

**Step 2: Remove promoted directory**

```bash
rm -r ~/.claude/skills/config-optimize
```

**Step 3: Restore symlink**

```bash
ln -s ~/Projects/active/claude-code-tool-dev/.claude/skills/config-optimize ~/.claude/skills/
```

**Step 4: Verify symlink restored**

```bash
file ~/.claude/skills/config-optimize
```

Expected: `symbolic link to ...`

**Step 5: Verify hook symlink intact**

```bash
file ~/.claude/hooks/block-keychain-extraction.py
```

Expected: `symbolic link` (Task 8 cleanup should have restored this)

---

## Task 15: Command Promotion (TODO)

**Status:** Blocked — `.claude/commands/` contains only `.gitkeep`

**Unblock:** Create a test command file (e.g., `.claude/commands/test-cmd.md`)

**When unblocked, test:**
1. Dry-run shows diff
2. Promotion copies `.md` file (not directory)
3. Missing file error handled
4. Validation (if any) works

---

## Task 16: Agent Promotion (TODO)

**Status:** Blocked — `.claude/agents/` contains only `.gitkeep`

**Unblock:** Create a test agent file (e.g., `.claude/agents/test-agent.md`)

**When unblocked, test:**
1. Dry-run shows diff
2. Promotion copies `.md` file (not directory)
3. Missing file error handled
4. Validation (if any) works

---

## Task 17: Interactive sync-settings Prompt

**Precondition:** None — creates own test fixtures

**Purpose:** Test the sync-settings prompt path (not covered by `--force` or `--dry-run` tests)

**Execution order:** Run before Task 14 (cleanup)

**Files:**
- Create: `.claude/hooks/sync-test-hook.py`
- Test: `scripts/promote`

**Step 1: Create executable test hook**

```bash
cat > .claude/hooks/sync-test-hook.py << 'EOF'
#!/usr/bin/env python3
# /// hook
# event: PreToolUse
# matcher: Bash
# ///
print("test")
EOF
chmod +x .claude/hooks/sync-test-hook.py
```

**Step 2: Promote without --force, answer 'y' to promotion**

```bash
uv run scripts/promote hook sync-test-hook
```

When prompted `Proceed with promotion? [y/N]`, type `y` and press Enter.

Expected: Shows sync-settings prompt: `Run sync-settings? [y/N]`

**Step 3: Answer 'n' to sync-settings**

Type `n` and press Enter.

Expected: Completes without running sync-settings

**Step 4: Verify hook was promoted**

```bash
file ~/.claude/hooks/sync-test-hook.py
```

Expected: `Python script text executable`

**Step 5: Cleanup**

```bash
rm .claude/hooks/sync-test-hook.py ~/.claude/hooks/sync-test-hook.py
```

---

## Success Criteria

| # | Criterion | Task | Status |
|---|-----------|------|--------|
| 1 | `--help` shows usage | Task 0 | ✅ PASS |
| 2 | Dry-run shows diff without changes | Task 1 | ✅ PASS* |
| 3 | Dry-run diff contains expected paths | Task 1 | ✅ PASS |
| 4 | Promotion replaces symlink with directory | Task 2 | ✅ PASS |
| 5 | "Already up to date" when no changes | Task 3 | ✅ PASS |
| 6 | Exit 1 for missing extension | Task 4 | ✅ PASS |
| 7 | Exit 1 for validation failure | Task 5 | ✅ PASS |
| 8 | Hook dry-run skips sync-settings prompt | Task 6 | ✅ PASS |
| 9 | Exit 1 for non-executable hook | Task 7 | ✅ PASS |
| 10 | Hook promotion with --force skips sync-settings | Task 8 | ✅ PASS |
| 11 | New destination shows "does not exist yet" message | Task 9 | ✅ PASS |
| 12 | User cancellation prints "Cancelled" with exit 0 | Task 10 | ✅ PASS |
| 13 | Shell hooks (.sh) validate correctly | Task 11 | ✅ PASS |
| 14 | Permission error handled gracefully with exit 1 | Task 12 | ✅ PASS |
| 15 | Broken symlinks behavior documented | Task 13 | ✅ PASS |
| 16 | Interactive sync-settings prompt appears after hook promotion | Task 17 | ✅ PASS |

*Task 1 showed "Already up to date" instead of diff because symlink→source means identical content. Verified path display and no-change behavior.

---

## Rollback

If any test corrupts production:

```bash
# Restore specific skill symlink
rm -r ~/.claude/skills/<name>
ln -s ~/Projects/active/claude-code-tool-dev/.claude/skills/<name> ~/.claude/skills/

# Restore specific hook symlink
rm ~/.claude/hooks/<name>.py
ln -s ~/Projects/active/claude-code-tool-dev/.claude/hooks/<name>.py ~/.claude/hooks/
```

---

## Files Involved

| File | Role |
|------|------|
| `scripts/promote` | Script under test |
| `scripts/sync-settings` | Called after hook promotion |
| `.claude/skills/` | Source (sandbox) |
| `~/.claude/skills/` | Destination (production, currently symlinks) |

---

## Execution Summary (2026-01-05)

### Results

- **15/17 tasks passed**
- **2 tasks blocked** (Tasks 15-16: commands/agents are placeholders)
- **2 issues discovered** (see below)

### Issues Discovered

| Issue | Severity | Description | Suggested Fix |
|-------|----------|-------------|---------------|
| Symlink-to-source detection | Low | When destination is a symlink pointing to source, script reports "Already up to date" instead of converting to standalone copy. | Add `--force-copy` flag to ignore content comparison |
| Broken symlink handling | Medium | Script fails with "OS error: File exists" on broken symlinks. `dest.exists()` returns `False` but symlink entry exists. | Check `dest.is_symlink()` before `dest.exists()` |

### Plan Deviations

| Deviation | Impact |
|-----------|--------|
| `file` command follows symlinks by default | Minor — use `ls -la` to verify symlink status |
| Hook was already a file, not symlink | None — adjusted Task 8 cleanup accordingly |

### Conclusion

The promote script handles the happy path and common error cases correctly. The broken symlink edge case should be fixed for robustness. The symlink-to-source behavior is acceptable for normal workflows.
