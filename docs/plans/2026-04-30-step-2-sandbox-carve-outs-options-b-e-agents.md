# Step 2: Sandbox Policy Carve-Outs (Options B + E + ~/.agents/)

## Context

T-20260429-01 Phase 1. The T-01 closing live `/delegate` smoke (job
`4586c6c3`, 2026-04-29) required 24 operator escalations for a 1-line
edit. ~11 of those were avoidable sandbox-friction escalations caused by
Codex reading its own data root (`~/.codex/memories`, `~/.codex/plugins/cache`)
and tools traversing the worktree's `.git` cross-pointer to the source
repo's gitdir. A third category (`~/.agents/` — Codex's skills and
plugin metadata) was identified in this session.

The fix widens `readableRoots` in the execution sandbox policy to
include these benign read paths, preserving the credential boundary
(`~/.codex/auth.json`, `~/.codex/config.toml`, `~/.codex/history.jsonl`)
and the existing security envelope (network blocked, sibling-worktree
blocked, sensitive-host-path blocked — all proven by T-01 Candidate A
security probes).

**Acceptance criteria** (from ticket, amended for `~/.agents/`):
1. Comparable smoke run: avoidable sandbox-friction escalations <=2
2. Credential boundary preserved (security probe)
3. `test_runtime.py` regression assertion updated; full test suite passes
4. *(Already satisfied)* Option F documented as upstream limitation

## Scope Amendment: `~/.agents/`

The owning ticket (`T-20260429-01`) defines Phase 1 as Options B and E
only. This plan adds `~/.agents/` as a third read-root category. This
section documents the amendment so the ticket and implementation stay
in sync.

**Evidence basis:** During Step 2 orientation (2026-04-30), the user
identified `~/.agents/` as a source of delegation friction — Codex reads
its own skills and plugin metadata from this directory during execution.
User: "`~/.agents/` — this is where Codex's skills and additional plugin
information live."

**Security boundary:** `~/.agents/` currently contains only
non-secret instruction metadata (skill definitions, agent configs,
`plugins/marketplace.json`). Unlike `~/.codex/`, it has no credential
files (no `auth.*`, `config.*`, `*.sqlite`, or session state). All
contents are world-readable (`drwxr-xr-x`). However, to match the
ticket's narrow carve-out model, grant specific subdirectories rather
than the entire root:

- `~/.agents/skills` — skill definitions and agent configs
- `~/.agents/plugins` — plugin marketplace metadata

**Invariant:** `~/.agents/` is expected to contain only non-secret
instruction metadata. If `~/.agents/` later gains credential files,
session state, generated logs, or private connector state, the
subdirectory-level carve-out prevents silent read-access expansion.

**`~/.agents/plugins` note:** Currently contains only
`marketplace.json`. Granted as a directory (not a file path) for
consistency with all other `readableRoots` entries, which are
directory-level grants. This is acceptable because the local plugin
layout treats that subtree as non-secret install metadata, not runtime
state or credentials. Add `~/.agents/plugins` to the negative-probe
checklist in the smoke/security evidence commit to catch future
content drift.

**Metric treatment:** `~/.agents/` escalations are counted as avoidable
sandbox friction alongside Option B/E escalations in the smoke metric.
They represent the same class of issue: Codex reading its own
configuration data.

**Closeout propagation:** Before the implementation commit, update
`T-20260429-01` to add `~/.agents/skills` and `~/.agents/plugins` as
Friction surface 1b (same section as Option B, same security model,
separate subpaths).

## Files to Modify

| File | Change |
|------|--------|
| `packages/plugins/codex-collaboration/server/runtime.py` | Extend `build_workspace_write_sandbox_policy()` |
| `packages/plugins/codex-collaboration/tests/test_runtime.py` | Update regression assertion; add Option E tests |
| `docs/tickets/2026-04-29-codex-collaboration-delegation-friction-reduction.md` | Add `~/.agents/` as Friction surface 1b |

`delegation_controller.py:1370` passes `worktree_path` through
transparently — no assertion on policy shape. `/delegate` SKILL.md
already narrowed for Option F (D-06).

## Implementation

### 1. `runtime.py:27-61` — `build_workspace_write_sandbox_policy()`

Add three categories of `readableRoots` entries after the existing
`str(resolved)` entry:

**Option B (static):**
```python
str(Path.home() / ".codex" / "memories"),
str(Path.home() / ".codex" / "plugins" / "cache"),
```

**~/.agents/ (static — subdirectory carve-outs):**
```python
str(Path.home() / ".agents" / "skills"),
str(Path.home() / ".agents" / "plugins"),
```

**Option E (dynamic — gitdir resolution):**

Read `worktree_path / ".git"` as a text file. If it exists, is a file
(not a directory), and its content starts with `gitdir: `, parse the
path after the prefix and add the resolved path to `readableRoots`.

Known `.git` file format from live delegation worktrees:
```
gitdir: /Users/jp/Projects/active/claude-code-tool-dev/.git/worktrees/worktree10
```

Graceful degradation: if the `.git` file doesn't exist, isn't a file,
is unreadable, or doesn't match the `gitdir: ` prefix, skip the
carve-out silently. The delegation falls back to current escalation
behavior — no worse than today.

**Extract gitdir resolution into a helper** to keep the policy builder
clean:

```python
def _resolve_worktree_gitdir(worktree_path: Path) -> str | None:
    """Resolve the gitdir target from a worktree's .git pointer file.

    Returns the resolved absolute path as a string, or None if the
    worktree does not have a .git pointer file or the file cannot be
    parsed.
    """
    git_path = worktree_path / ".git"
    try:
        if not git_path.is_file():
            return None
        content = git_path.read_text().strip()
    except OSError:
        return None
    prefix = "gitdir: "
    if not content.startswith(prefix):
        return None
    raw = Path(content[len(prefix):])
    # Resolve relative gitdir pointers against the .git file's parent
    # (the worktree root), not the process cwd.
    if not raw.is_absolute():
        raw = git_path.parent / raw
    return str(raw.resolve())
```

**Policy builder update** — build `readableRoots` list, then construct
the policy dict:

```python
readable_roots = [
    str(resolved),
    str(Path.home() / ".codex" / "memories"),
    str(Path.home() / ".codex" / "plugins" / "cache"),
    str(Path.home() / ".agents" / "skills"),
    str(Path.home() / ".agents" / "plugins"),
]
gitdir = _resolve_worktree_gitdir(worktree_path)
if gitdir is not None:
    readable_roots.append(gitdir)
```

Then use `readable_roots` in the returned dict.

**Docstring update:** Add the three new grant categories to the
enforcement note, referencing this ticket (T-20260429-01).

### 2. `test_runtime.py:171-187` — regression assertion update

The current test (`test_build_workspace_write_sandbox_policy_restricts_reads_and_writes`)
asserts exact dict equality including `readableRoots`. Update the
expected `readableRoots` to include the four static paths (Option B +
`~/.agents/skills` + `~/.agents/plugins`). The test uses
`tmp_path / "worktree"` which is a plain directory — no `.git` file —
so the gitdir entry will be absent (correct behavior: graceful
degradation).

### 3. New tests for Option E

Add tests for the gitdir resolution. Test the helper
`_resolve_worktree_gitdir` directly for edge cases, and test the
full policy builder for the integration path.

**Test: gitdir included when `.git` file present (absolute path).**
Create a fake `.git` text file in the test worktree containing
`gitdir: /some/path/to/gitdir`. Assert the resolved gitdir path appears
in `readableRoots`.

**Test: gitdir resolved correctly for relative `.git` pointer.**
Create a fake `.git` text file containing a relative path
(e.g., `gitdir: ../../.git/worktrees/wk1`). Assert the resolved path
is relative to the `.git` file's parent (the worktree root), not the
process cwd.

**Test: gitdir omitted when `.git` is a directory (real repo root).**
Create a `.git` directory (not file) in the test worktree. Assert
`readableRoots` contains only the static entries — no gitdir.

**Test: gitdir omitted when `.git` file has unexpected format.**
Create a `.git` file with content that does not start with `gitdir: `.
Assert `readableRoots` contains only the static entries.

**Test: gitdir omitted when `.git` file is unreadable.**
Create a `.git` file, then make it unreadable (`chmod 000`). Assert
`readableRoots` contains only the static entries. Skip on platforms
where permission removal is not effective (e.g., root user in CI).

**Test: gitdir omitted when `.git` file does not exist.**
No `.git` file in the worktree directory. Assert `readableRoots`
contains only the static entries. (This is already covered by the
existing regression test, but an explicit helper-level test is clearer.)

### 4. Commit

Single commit: implementation + tests. Message style:

```
fix(codex-collaboration): widen execution sandbox readableRoots for codex data, agents, and worktree gitdir

Option B: add ~/.codex/memories and ~/.codex/plugins/cache (Codex's
own memory store and skill cache). Option E: dynamically resolve
worktree .git pointer to include the gitdir target. Adds
~/.agents/skills and ~/.agents/plugins (Codex skill definitions
and plugin metadata; scope amendment documented in T-20260429-01).

Credential paths (~/.codex/auth.json, ~/.codex/config.toml,
~/.codex/history.jsonl) are not in readableRoots. Live credential
boundary verification deferred to smoke/security probe commit.

Refs: T-20260429-01 Phase 1
```

## What Comes After This Commit

**Not part of this plan — separate follow-up work:**

1. Live `/delegate` smoke (AC #1) — requires App Server access
2. Security probe for credential boundary (AC #2) — must include:
   - `~/.codex/auth.json` and `~/.codex/config.toml` (existing
     credential boundary, same as T-01 sensitive-path probe pattern)
   - `~/.agents/plugins` content audit at probe time (verify subtree
     still contains only non-secret metadata, no credential drift)
3. Ticket/register closeout (AC #3 partially, #4 already done)

These follow the three-commit pattern (implementation → evidence →
closeout) and depend on live App Server availability.

## Verification

1. Run `uv run --package codex-collaboration pytest` — full test suite
   must pass
2. Verify the new tests cover all Option E branches: absolute pointer,
   relative pointer, `.git` is directory, malformed content, unreadable
   file, missing file
3. Verify the existing regression test expects the updated
   `readableRoots` shape (5 static entries, no gitdir)
4. `rg "readableRoots" packages/plugins/codex-collaboration/` — confirm
   no other test or source file asserts the old shape
5. Verify `T-20260429-01` has been updated with the `~/.agents/`
   scope amendment before the implementation commit
