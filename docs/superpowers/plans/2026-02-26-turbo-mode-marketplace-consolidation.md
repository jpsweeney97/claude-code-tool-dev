# Turbo-Mode Marketplace Consolidation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Consolidate the `cross-model` and `handoff-dev` directory-sourced marketplaces into a single GitHub-sourced marketplace called `turbo-mode`, fixing the autocomplete namespacing bug for plugin skills.

**Architecture:** Rename the root marketplace from `cross-model` to `turbo-mode` and add the `handoff` plugin to it. Switch the marketplace source type from `directory` to `github` (repo: `jpsweeney97/claude-code-tool-dev`). Update all config files that reference the old marketplace names, then reinstall both plugins from the new marketplace.

**Tech Stack:** Claude Code plugin system, git, GitHub

**Root cause:** Directory-sourced marketplaces (`source: "directory"` in `known_marketplaces.json`) don't apply the `plugin-name:` namespace prefix in the autocomplete UI. GitHub-sourced marketplaces do. Both self-published plugins (`cross-model`, `handoff`) were directory-sourced; all official plugins are GitHub-sourced. Switching to GitHub source fixes the autocomplete.

---

## Pre-flight

Before starting, verify:
- Current branch: `chore/turbo-mode-marketplace-consolidation` (already created)
- Remote: `https://github.com/jpsweeney97/claude-code-tool-dev.git`
- No uncommitted changes beyond this plan

---

### Task 1: Update Root Marketplace Definition

**Files:**
- Modify: `.claude-plugin/marketplace.json`

**Step 1: Edit marketplace.json**

Change the marketplace name from `cross-model` to `turbo-mode` and add the `handoff` plugin entry:

```json
{
  "name": "turbo-mode",
  "owner": { "name": "JP" },
  "plugins": [
    { "name": "cross-model", "source": "./packages/plugins/cross-model" },
    { "name": "handoff", "source": "./packages/plugins/handoff" }
  ]
}
```

**Step 2: Remove the handoff-dev marketplace definition**

The file `packages/plugins/handoff/.claude-plugin/marketplace.json` defined the old `handoff-dev` marketplace. It's no longer needed since handoff is now referenced from the root marketplace. Remove it:

```bash
trash packages/plugins/handoff/.claude-plugin/marketplace.json
```

Verify `packages/plugins/handoff/.claude-plugin/plugin.json` still exists (it defines the plugin identity and must stay).

**Step 3: Commit**

```bash
git add .claude-plugin/marketplace.json
git add packages/plugins/handoff/.claude-plugin/marketplace.json
git commit -m "chore: rename marketplace to turbo-mode, consolidate handoff plugin"
```

---

### Task 2: Push to GitHub

The marketplace must be available on the remote before we can register it as a GitHub source.

**Step 1: Push the branch**

```bash
git push -u origin chore/turbo-mode-marketplace-consolidation
```

**Step 2: Verify the marketplace.json is accessible on GitHub**

```bash
gh api repos/jpsweeney97/claude-code-tool-dev/contents/.claude-plugin/marketplace.json?ref=chore/turbo-mode-marketplace-consolidation --jq '.name'
```

Expected: `marketplace.json`

---

### Task 3: Update `~/.claude/plugins/known_marketplaces.json`

**Files:**
- Modify: `~/.claude/plugins/known_marketplaces.json`

**Step 1: Replace old marketplace entries with new one**

Remove the `"cross-model"` and `"handoff-dev"` entries. Add `"turbo-mode"` with GitHub source:

Current entries to remove:
```json
"handoff-dev": {
    "source": { "source": "directory", "path": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/handoff" },
    "installLocation": "/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/handoff",
    "lastUpdated": "2026-02-26T03:37:52.416Z"
},
"cross-model": {
    "source": { "source": "directory", "path": "/Users/jp/Projects/active/claude-code-tool-dev" },
    "installLocation": "/Users/jp/Projects/active/claude-code-tool-dev",
    "lastUpdated": "2026-02-25T03:30:56.108Z"
}
```

New entry to add:
```json
"turbo-mode": {
    "source": { "source": "github", "repo": "jpsweeney97/claude-code-tool-dev" },
    "installLocation": "/Users/jp/.claude/plugins/marketplaces/turbo-mode",
    "lastUpdated": "<current ISO timestamp>"
}
```

**Step 2: Validate JSON**

```bash
python3 -c "import json; json.load(open('/Users/jp/.claude/plugins/known_marketplaces.json')); print('Valid JSON')"
```

Expected: `Valid JSON`

---

### Task 4: Update `~/.claude/plugins/installed_plugins.json`

**Files:**
- Modify: `~/.claude/plugins/installed_plugins.json`

**Step 1: Remove old plugin entries**

Remove these keys from the `plugins` object:
- `"cross-model@cross-model"` (already removed `"codex@cross-model"` earlier in this session)
- `"handoff@handoff-dev"`

**Step 2: Validate JSON**

```bash
python3 -c "import json; json.load(open('/Users/jp/.claude/plugins/installed_plugins.json')); print('Valid JSON')"
```

Expected: `Valid JSON`

> **Note:** New entries for `cross-model@turbo-mode` and `handoff@turbo-mode` will be created automatically by `claude plugin install` in Task 6. Do NOT add them manually.

---

### Task 5: Update `~/.claude/settings.json` `enabledPlugins`

**Files:**
- Modify: `~/.claude/settings.json`

**Step 1: Replace old plugin keys with new ones**

In the `enabledPlugins` object:
- Remove: `"codex@cross-model": true`
- Remove: `"cross-model@cross-model": true`
- Remove: `"handoff@handoff-dev": true`
- Add: `"cross-model@turbo-mode": true`
- Add: `"handoff@turbo-mode": true`

**Step 2: Validate JSON**

```bash
python3 -c "import json; json.load(open('/Users/jp/.claude/settings.json')); print('Valid JSON')"
```

Expected: `Valid JSON`

---

### Task 6: Register New Marketplace and Install Plugins

This task requires user interaction with Claude Code CLI. The implementer should present these commands to the user for manual execution, since `claude plugin` commands may require interactive confirmation.

**Step 1: Fetch/clone the marketplace**

```bash
claude plugin marketplace update turbo-mode
```

This should clone the repo to `~/.claude/plugins/marketplaces/turbo-mode/` and recognize the `.claude-plugin/marketplace.json`.

If `marketplace update` doesn't work because the marketplace isn't registered yet:
```bash
claude plugin marketplace add turbo-mode
```
Then select GitHub source and provide repo `jpsweeney97/claude-code-tool-dev`.

> **Fallback:** If neither command works with the current branch, the marketplace may need the changes on `main`. In that case, merge the branch to `main` first (Task 2 alternate), then retry.

**Step 2: Install both plugins**

```bash
claude plugin install cross-model@turbo-mode
claude plugin install handoff@turbo-mode
```

**Step 3: Verify installed_plugins.json has new entries**

```bash
python3 -c "
import json
data = json.load(open('/Users/jp/.claude/plugins/installed_plugins.json'))
for key in ['cross-model@turbo-mode', 'handoff@turbo-mode']:
    assert key in data['plugins'], f'Missing: {key}'
    print(f'OK: {key}')
"
```

Expected:
```
OK: cross-model@turbo-mode
OK: handoff@turbo-mode
```

---

### Task 7: Verify Autocomplete Fix

**Step 1: Restart Claude Code**

Exit and relaunch Claude Code in the project directory.

**Step 2: Test autocomplete**

Type `/` and check:
- `/cross-model:codex` appears (not bare `/codex`)
- `/cross-model:dialogue` appears (not bare `/dialogue`)
- `/handoff:creating-handoffs` appears (not bare `/creating-handoffs`)
- `/handoff:checkpointing` appears
- `/handoff:resuming-handoffs` appears

**Step 3: Test invocation**

Try invoking `/cross-model:codex` — confirm the skill loads correctly.

If autocomplete still shows un-namespaced forms: the bug may not be source-type-related. File a GitHub issue at `https://github.com/anthropics/claude-code/issues` with the evidence from this investigation.

---

### Task 8: Clean Up Old Cache

**Step 1: Remove old cache directories**

```bash
trash ~/.claude/plugins/cache/cross-model
trash ~/.claude/plugins/cache/handoff-dev
```

**Step 2: Verify new cache exists**

```bash
ls ~/.claude/plugins/cache/turbo-mode/
```

Expected: directories for `cross-model` and `handoff` plugins.

---

### Task 9: Merge Branch

**Step 1: Merge to main**

```bash
git checkout main
git merge chore/turbo-mode-marketplace-consolidation
git push origin main
```

**Step 2: Clean up branch**

```bash
git branch -d chore/turbo-mode-marketplace-consolidation
git push origin --delete chore/turbo-mode-marketplace-consolidation
```

---

## Rollback Plan

If things break after migration:

1. Restore old `known_marketplaces.json` entries (directory sources)
2. Restore old `installed_plugins.json` entries
3. Restore old `settings.json` `enabledPlugins` keys
4. Revert `.claude-plugin/marketplace.json` to `cross-model` name
5. Run `claude plugin marketplace update cross-model` and `claude plugin install cross-model@cross-model`

The old cache directories (if not yet deleted) still contain working plugin installations.
