# Engram Architecture Proof — Step 0A Results

**Date:** 2026-03-16
**Status:** Complete
**Branch:** docs/engram-design
**Decision rule outcome:** Branch 1 — proceed with OC2-augmented, single phase

---

## Purpose

Before committing to the OC2-augmented path (shared `engram_core` library + search plugin + Context identity retrofit), test two empirical gates:

1. **Gate 1:** Can `engram_core` be imported from hooks, scripts, and tests in an installed-cache plugin runtime?
2. **Gate 3:** How large is the Context identity retrofit (handoff path references that change from project-name to repo_id)?

These gates come from the Codex dialogue's 4-branch decision rule:

| Gate 1 (import) | Gate 3 (retrofit) | Path |
|---|---|---|
| Pass | Small | OC2-augmented, single phase |
| Pass | Large | Split Phase 1A/1B |
| Fail (vendored works) | — | OC2 with vendored core |
| All fail | — | Fall back to consolidation |

---

## Gate 1: Import Proof

### Method

Created minimal `engram_core` package with `identity.py` (repo_id/worktree_id resolution) and `types.py` (RecordRef, RecordMeta, RecordStub). Tested imports from 5 execution contexts:

| Context | Location | Import mechanism | Result |
|---------|----------|-----------------|--------|
| A. Script (local) | `/tmp/engram-proof/scripts/` | `sys.path.insert(0, parent.parent)` | **PASS** |
| B. Hook (local) | `/tmp/engram-proof/hooks/` | `sys.path.insert(0, parent.parent)` | **PASS** |
| B'. Hook (simulated cache) | `/tmp/engram-cache-test/engram/0.1.0/hooks/` | `sys.path.insert(0, parent.parent)` | **PASS** |
| B''. Hook (env var) | Same, with `CLAUDE_PLUGIN_ROOT` set | `sys.path.insert(0, env_var)` | **PASS** |
| C. pytest | `/tmp/engram-proof/` | `sys.path.insert(0, parent)` | **PASS** (7/7 tests) |

### Key findings

1. **The `sys.path.insert` pattern is proven in installed-cache.** The directory tree is preserved when plugins are copied to `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`. Hook scripts can resolve the plugin root via `Path(__file__).parent.parent` and add it to `sys.path`.

2. **The existing ticket guard already uses dual resolution:** `os.environ.get("CLAUDE_PLUGIN_ROOT", str(Path(__file__).parent.parent))`. Engram hooks should follow the same pattern.

3. **No novel mechanism required.** Scripts already use `sys.path.insert` for intra-plugin imports. Hooks extending this to `engram_core` is a minor generalization, not a new pattern.

4. **Static analysis (Pyright) cannot follow dynamic `sys.path`.** This is a known limitation — `reportMissingImports` fires on all `engram_core` imports. Not a runtime issue.

### Gate 1 verdict: **PASS**

---

## Gate 3: Context Identity Retrofit Scope

### Method

Searched all files in `packages/plugins/handoff/` for references to project-name-based paths, `get_project_name()` calls, and `.session-state/handoff-` chain state patterns.

### Results

| Category | References | Files |
|----------|-----------|-------|
| Non-test code | 22 | 5 (`project_paths.py`, `cleanup.py`, `search.py`, 2 SKILL.md files) |
| Test code | 16 | 4 (`test_project_paths.py`, `test_cleanup.py`, `test_search.py`) |
| **Total** | **38** | **9** |

### Breakdown

- `get_project_name()` → `get_repo_id()`: 12 call sites
- `~/.claude/handoffs/<project>/` hardcoded paths: 11 references
- `.session-state/handoff-` chain state: 6 references
- SKILL/doc path documentation: 9 references

### Assessment

**SMALL** — well under the 50-reference/10-file threshold. Changes are localized substitutions (`project_name` → `repo_id`), not architectural refactors. No dependency cascades to other plugins.

### Gate 3 verdict: **SMALL**

---

## Decision Rule Evaluation

| Gate | Result | Evidence |
|------|--------|----------|
| Gate 1 | PASS | 5/5 import contexts succeed, including simulated installed-cache |
| Gate 3 | SMALL | 22 non-test references across 5 files |

**→ Branch 1: Proceed with OC2-augmented, single phase.**

No phasing split needed (Gate 3 is small). No vendored core needed (Gate 1 passes cleanly). Full consolidation not required (OC2 is viable).

---

## Proof Artifacts

Test scripts at `/tmp/engram-proof/` (ephemeral):
- `engram_core/` — minimal stubs (identity.py, types.py)
- `scripts/test_script_import.py` — Context A
- `hooks/test_hook_import.py` — Context B
- `test_pytest_import.py` — Context C (7 tests)

---

## Next Actions

1. **Write ADR** — document OC2-augmented decision with review finding dispositions
2. **Write Phase 1 spec** — shared core library, NativeReaders, search plugin, Context identity retrofit (single phase)
3. **Add deferred banner** to current Engram design spec
