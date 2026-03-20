# Checklist: Consolidate the `cross-model` Plugin

## Summary
- Make [`packages/plugins/cross-model/context-injection`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/context-injection) a full self-contained plugin with no dependency on any specific repo.
- Make [`packages/plugins/cross-model/context-injection`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/context-injection) the only `context-injection` package.
- Keep it as a nested Python package with its own [`pyproject.toml`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/context-injection/pyproject.toml).
- Keep the canonical protocol contract at [`packages/plugins/cross-model/references/context-injection-contract.md`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/references/context-injection-contract.md).
- Remove the legacy package at [`packages/context-injection`](/Users/jp/Projects/active/claude-code-tool-dev/packages/context-injection), the vendoring script at [`scripts/build-cross-model-plugin`](/Users/jp/Projects/active/claude-code-tool-dev/scripts/build-cross-model-plugin), and the symlink at [`docs/references/context-injection-contract.md`](/Users/jp/Projects/active/claude-code-tool-dev/docs/references/context-injection-contract.md).
- No runtime behavior changes: tool names, import path `context_injection`, schema `0.2.0`, and [`packages/plugins/cross-model/.mcp.json`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/.mcp.json) stay functionally unchanged.

## Preflight
**Goal**
- Confirm the environment can run `uv`-backed verification.
- Confirm the contract file in `docs/references` is a symlink.
- Confirm the root workspace uses explicit members, not globs.

**Commands**
```bash
cd /Users/jp/Projects/active/claude-code-tool-dev
ls -l docs/references/context-injection-contract.md
sed -n '1,20p' pyproject.toml
cd packages/plugins/cross-model/context-injection && uv sync --locked
cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model && uv sync --locked
cd /Users/jp/Projects/active/claude-code-tool-dev && uv sync --locked
```

**Rules**
- If any `uv sync --locked` fails because dependencies cannot be fetched, stop before editing anything.
- The symlink check should show `docs/references/context-injection-contract.md -> ../../packages/plugins/cross-model/references/context-injection-contract.md`.
- The workspace check should show explicit `members = [...]`; no extra collision guard is needed once the nested plugin path becomes the only member.

**Baseline verification**
```bash
cd /Users/jp/Projects/active/claude-code-tool-dev/packages/context-injection && uv run pytest
cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model && uv run pytest tests
cd /Users/jp/Projects/active/claude-code-tool-dev && uv run pytest tests
```

## Commit 1 — `test: move context-injection suite into plugin package`
**Files**
- Add [`packages/plugins/cross-model/context-injection/tests/`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/context-injection/tests) as a full copy of [`packages/context-injection/tests/`](/Users/jp/Projects/active/claude-code-tool-dev/packages/context-injection/tests).
- Edit [`packages/plugins/cross-model/context-injection/tests/test_server.py`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/context-injection/tests/test_server.py).

**Exact edits**
- Copy the entire helper test tree into the plugin package, preserving filenames and contents.
- In `test_server.py`, replace the hardcoded four-parent repo-root calculation with `Path(__file__).resolve()` parent scanning for the first parent containing `.git`.
- Keep test behavior identical: `_load_git_files(repo_root)` must still return a non-empty set.
- Leave the old source-package tests in place for now.

**Commands**
```bash
cd /Users/jp/Projects/active/claude-code-tool-dev
rsync -a --exclude='__pycache__/' packages/context-injection/tests/ packages/plugins/cross-model/context-injection/tests/
```

**Verify**
```bash
cd /Users/jp/Projects/active/claude-code-tool-dev
diff -rq packages/context-injection/tests packages/plugins/cross-model/context-injection/tests -x '__pycache__' -x 'test_server.py'
cd packages/plugins/cross-model/context-injection && uv run pytest
cd packages/plugins/cross-model/context-injection && uv run ruff check context_injection/ tests/
```

**Stage and commit**
```bash
cd /Users/jp/Projects/active/claude-code-tool-dev
git add packages/plugins/cross-model/context-injection/tests
git commit -m "test: move context-injection suite into plugin package"
```

## Commit 2 — `build: repoint workspace to plugin context-injection package`
**Files**
- Edit [`pyproject.toml`](/Users/jp/Projects/active/claude-code-tool-dev/pyproject.toml).
- Refresh [`uv.lock`](/Users/jp/Projects/active/claude-code-tool-dev/uv.lock).
- Edit [`packages/plugins/cross-model/tests/test_codex_delegate.py`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/tests/test_codex_delegate.py).

**Exact edits**
- In root `pyproject.toml`, replace `"packages/context-injection"` with `"packages/plugins/cross-model/context-injection"` in `[tool.uv.workspace].members`.
- Remove the `exclude = [...]` block that existed only to suppress the vendored-copy collision.
- Regenerate `uv.lock` so the editable source for `context-injection` points at the nested plugin package.
- In `test_codex_delegate.py`, change the mocked nested certifi path from `packages/context-injection/.venv/.../cacert.pem` to `packages/plugins/cross-model/context-injection/.venv/.../cacert.pem`, and update the test docstring to match.

**Commands**
```bash
cd /Users/jp/Projects/active/claude-code-tool-dev
uv lock
```

**Verify**
```bash
cd /Users/jp/Projects/active/claude-code-tool-dev
rg -n 'packages/plugins/cross-model/context-injection' pyproject.toml uv.lock
rg -n 'packages/context-injection' pyproject.toml uv.lock
cd packages/plugins/cross-model && uv run pytest tests
cd /Users/jp/Projects/active/claude-code-tool-dev && uv run pytest tests
```

**Stage and commit**
```bash
cd /Users/jp/Projects/active/claude-code-tool-dev
git add pyproject.toml uv.lock packages/plugins/cross-model/tests/test_codex_delegate.py
git commit -m "build: repoint workspace to plugin context-injection package"
```

## Commit 3 — `chore: canonicalize plugin context-injection and remove legacy package`
**Files**
- Edit [`packages/plugins/cross-model/context-injection/CLAUDE.md`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/context-injection/CLAUDE.md).
- Add [`packages/plugins/cross-model/context-injection/README.md`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/context-injection/README.md).
- Edit [`packages/plugins/cross-model/README.md`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/README.md).
- Edit [`packages/plugins/cross-model/HANDBOOK.md`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/HANDBOOK.md).
- Edit [`packages/plugins/cross-model/CHANGELOG.md`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/CHANGELOG.md).
- Edit [`.claude/CLAUDE.md`](/Users/jp/Projects/active/claude-code-tool-dev/.claude/CLAUDE.md).
- Edit [`docs/references/README.md`](/Users/jp/Projects/active/claude-code-tool-dev/docs/references/README.md).
- Edit the helper docstring/comment references in:
  - [`packages/plugins/cross-model/context-injection/context_injection/pipeline.py`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/context-injection/context_injection/pipeline.py)
  - [`packages/plugins/cross-model/context-injection/context_injection/types.py`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/context-injection/context_injection/types.py)
  - [`packages/plugins/cross-model/context-injection/context_injection/templates.py`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/context-injection/context_injection/templates.py)
  - [`packages/plugins/cross-model/context-injection/context_injection/enums.py`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/context-injection/context_injection/enums.py)
- Trash:
  - [`scripts/build-cross-model-plugin`](/Users/jp/Projects/active/claude-code-tool-dev/scripts/build-cross-model-plugin)
  - [`packages/plugins/cross-model/context-injection/README.vendored.md`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/context-injection/README.vendored.md)
  - [`docs/references/context-injection-contract.md`](/Users/jp/Projects/active/claude-code-tool-dev/docs/references/context-injection-contract.md)
  - [`packages/context-injection`](/Users/jp/Projects/active/claude-code-tool-dev/packages/context-injection)

**Exact edits**
- In helper `CLAUDE.md`, remove all “vendored copy” and “source package only” wording. Point commands at `packages/plugins/cross-model/context-injection`.
- Add a short normal helper `README.md` describing what the package does, how to run tests, and that the canonical contract lives in `packages/plugins/cross-model/references/context-injection-contract.md`.
- In plugin `README.md` and `HANDBOOK.md`, remove all instructions to edit `packages/context-injection` and sync into the plugin.
- In `.claude/CLAUDE.md`, change the helper location and contract path to the canonical plugin locations.
- In `docs/references/README.md`, replace the `./context-injection-contract.md` entry with a pointer to `packages/plugins/cross-model/references/context-injection-contract.md`.
- In `CHANGELOG.md`, add an `Unreleased` note stating that `context-injection` now lives only under the plugin, the vendoring script was removed, and the docs symlink was removed.
- In the four helper Python files, update the contract path string from `docs/references/context-injection-contract.md` to `packages/plugins/cross-model/references/context-injection-contract.md`. These are documentation strings/comments, not runtime lookups.
- Trash the vendoring script, vendored marker file, contract symlink, and legacy package.

**Commands**
```bash
cd /Users/jp/Projects/active/claude-code-tool-dev
trash scripts/build-cross-model-plugin
trash packages/plugins/cross-model/context-injection/README.vendored.md
trash docs/references/context-injection-contract.md
trash packages/context-injection
```

**Verify**
```bash
cd /Users/jp/Projects/active/claude-code-tool-dev
rg -n 'packages/context-injection|build-cross-model-plugin|README\.vendored|docs/references/context-injection-contract\.md' \
  .claude/CLAUDE.md \
  docs/references/README.md \
  packages/plugins/cross-model/README.md \
  packages/plugins/cross-model/HANDBOOK.md \
  packages/plugins/cross-model/CHANGELOG.md \
  packages/plugins/cross-model/context-injection \
  packages/plugins/cross-model/tests \
  tests \
  scripts
test ! -e /Users/jp/Projects/active/claude-code-tool-dev/docs/references/context-injection-contract.md
test ! -e /Users/jp/Projects/active/claude-code-tool-dev/packages/context-injection
cd packages/plugins/cross-model/context-injection && uv run pytest
cd packages/plugins/cross-model/context-injection && uv run ruff check context_injection/ tests/
cd packages/plugins/cross-model && uv run pytest tests
cd /Users/jp/Projects/active/claude-code-tool-dev && uv run pytest tests
cd packages/plugins/cross-model/context-injection && uv run python -c "from context_injection.server import create_server; print(create_server().name)"
```

**Stage and commit**
```bash
cd /Users/jp/Projects/active/claude-code-tool-dev
git add .claude/CLAUDE.md \
  docs/references/README.md \
  packages/plugins/cross-model/README.md \
  packages/plugins/cross-model/HANDBOOK.md \
  packages/plugins/cross-model/CHANGELOG.md \
  packages/plugins/cross-model/context-injection/CLAUDE.md \
  packages/plugins/cross-model/context-injection/README.md \
  packages/plugins/cross-model/context-injection/context_injection/pipeline.py \
  packages/plugins/cross-model/context-injection/context_injection/types.py \
  packages/plugins/cross-model/context-injection/context_injection/templates.py \
  packages/plugins/cross-model/context-injection/context_injection/enums.py
git add -u scripts/build-cross-model-plugin \
  packages/plugins/cross-model/context-injection/README.vendored.md \
  docs/references/context-injection-contract.md \
  packages/context-injection
git commit -m "chore: canonicalize plugin context-injection and remove legacy package"
```

## Final Verification
```bash
cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/context-injection && uv run pytest
cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/context-injection && uv run ruff check context_injection/ tests/
cd /Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model && uv run pytest tests
cd /Users/jp/Projects/active/claude-code-tool-dev && uv run pytest tests
cd /Users/jp/Projects/active/claude-code-tool-dev && git status --short
```

## Assumptions and Defaults
- The root workspace uses explicit member paths, not globs, so removing the exclude block in Commit 2 is safe even while the old package still exists.
- [`docs/references/context-injection-contract.md`](/Users/jp/Projects/active/claude-code-tool-dev/docs/references/context-injection-contract.md) is a symlink today; Commit 3 removes that symlink, not a second real contract copy.
- The contract-path edits in helper Python files are doc/comment cleanup only; they are not runtime behavior changes.
- No edits to historical records under [`docs/plans`](/Users/jp/Projects/active/claude-code-tool-dev/docs/plans), [`docs/tickets`](/Users/jp/Projects/active/claude-code-tool-dev/docs/tickets), or [`docs/audits`](/Users/jp/Projects/active/claude-code-tool-dev/docs/audits).
- All deletions use `trash`, never `rm`.
