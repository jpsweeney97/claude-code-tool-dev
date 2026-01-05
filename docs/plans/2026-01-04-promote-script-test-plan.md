# Promote Script Test Plan

> **For Claude:** Execute tasks sequentially. Each task is independent and includes cleanup.

**Goal:** Verify `scripts/promote` correctly validates, diffs, and deploys extensions from sandbox to production.

**Architecture:** The promote script copies from `.claude/<type>/<name>` (sandbox) to `~/.claude/<type>/<name>` (production). Skills are directories; hooks/commands/agents are files. Production currently uses symlinks to monorepo.

**Tech Stack:** Python 3.12, uv, shutil, rich

---

## ⚠️ Critical Context

**Current state:** `~/.claude/skills/*` are symlinks → monorepo

**Promote behavior:** `shutil.rmtree(dest)` + `copytree()` replaces symlink with directory copy

**Test impact:** Promoting converts symlink to standalone copy. Cleanup restores symlinks.

---

### Task 0: Pre-flight Verification

**Files:**
- Test: `scripts/promote`
- Test: `scripts/sync-settings`

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

**Step 3: Check current symlink state**

```bash
ls -la ~/.claude/skills/config-optimize
```

Expected: Symlink → `/Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/config-optimize`

---

### Task 1: Dry Run (Non-Destructive)

**Files:**
- Test: `scripts/promote`
- Observe: `~/.claude/skills/config-optimize`

**Step 1: Run dry-run promotion**

```bash
uv run scripts/promote skill config-optimize --dry-run
```

Expected: Shows diff panel, prints "Dry run - no changes made"

**Step 2: Verify exit code**

```bash
echo $?
```

Expected: `0`

**Step 3: Verify destination unchanged**

```bash
ls -la ~/.claude/skills/config-optimize
```

Expected: Still a symlink (not a directory)

---

### Task 2: Actual Skill Promotion

**Files:**
- Test: `scripts/promote`
- Modify: `~/.claude/skills/config-optimize` (symlink → directory)

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

---

### Task 3: Idempotence (Already Up To Date)

**Files:**
- Test: `scripts/promote`

**Step 1: Promote same skill again**

```bash
uv run scripts/promote skill config-optimize
```

Expected: Prints "Already up to date." (no prompt)

**Step 2: Verify no user interaction required**

Expected: Command exits without waiting for input

---

### Task 4: Missing Extension (Error Case)

**Files:**
- Test: `scripts/promote`

**Step 1: Try to promote nonexistent skill**

```bash
uv run scripts/promote skill nonexistent-skill-12345
```

Expected: "Error: skill 'nonexistent-skill-12345' not found in sandbox"

**Step 2: Verify exit code**

```bash
echo $?
```

Expected: `1`

---

### Task 5: Validation Failure (Missing SKILL.md)

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

Expected: "Validation errors:" with "Missing SKILL.md"

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

### Task 6: Hook Promotion (Dry Run)

**Files:**
- Test: `scripts/promote`
- Observe: `.claude/hooks/block-keychain-extraction.py`

**Step 1: Run dry-run hook promotion**

```bash
uv run scripts/promote hook block-keychain-extraction --dry-run
```

Expected: Shows diff, prints "Dry run - no changes made"

**Step 2: Verify NO sync-settings prompt**

Expected: Dry run should not prompt for sync-settings

---

### Task 7: Hook Validation (Non-Executable)

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

### Task 8: Cleanup (Restore Symlink)

**Files:**
- Modify: `~/.claude/skills/config-optimize` (directory → symlink)

**Step 1: Remove promoted directory**

```bash
rm -r ~/.claude/skills/config-optimize
```

**Step 2: Restore symlink**

```bash
ln -s ~/Projects/active/claude-code-tool-dev/.claude/skills/config-optimize ~/.claude/skills/
```

**Step 3: Verify symlink restored**

```bash
ls -la ~/.claude/skills/config-optimize
```

Expected: Symlink → monorepo path

---

## Success Criteria

| # | Criterion | Task |
|---|-----------|------|
| 1 | `--help` shows usage | Task 0 |
| 2 | Dry-run shows diff without changes | Task 1 |
| 3 | Promotion replaces symlink with directory | Task 2 |
| 4 | "Already up to date" when no changes | Task 3 |
| 5 | Exit 1 for missing extension | Task 4 |
| 6 | Exit 1 for validation failure | Task 5 |
| 7 | Hook dry-run skips sync-settings prompt | Task 6 |
| 8 | Exit 1 for non-executable hook | Task 7 |

---

## Rollback

If any test corrupts production:

```bash
# Restore specific skill symlink
rm -r ~/.claude/skills/<name>
ln -s ~/Projects/active/claude-code-tool-dev/.claude/skills/<name> ~/.claude/skills/

# Restore specific plugin symlink
rm -r ~/.claude/plugins/<name>
ln -s ~/Projects/active/claude-code-tool-dev/packages/plugins/<name> ~/.claude/plugins/
```

---

## Files Involved

| File | Role |
|------|------|
| `scripts/promote` | Script under test |
| `scripts/sync-settings` | Called after hook promotion |
| `.claude/skills/` | Source (sandbox) |
| `~/.claude/skills/` | Destination (production, currently symlinks) |
