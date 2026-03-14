# Cross-Model Repo Cleanup Plan

## Summary
- Goal: make repo verification predictable, align metadata, restore clean root lint, and reduce documentation drift without changing plugin runtime behavior.
- Non-goal: no changes to `/codex`, `/dialogue`, `/delegate`, MCP wiring, hook behavior, or either normative contract.
- Priority order: verification boundary first, then metadata consistency, then hygiene, then doc authority cleanup.

## Interface Changes
- No public runtime APIs, MCP schemas, or contract types change.
- Developer workflow changes:
  - `uv run pytest` from the plugin root becomes intentionally scoped to the root `tests/` suite.
  - Full verification remains an explicit two-surface sequence: root suite plus the nested `context-injection` package suite.

## Ordered Changes
1. **Stabilize the root verification boundary**
- Update [pyproject.toml](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/pyproject.toml#L1) so root pytest only discovers the plugin-root `tests/` suite and does not recurse into `context-injection/`.
- Keep the nested `context-injection` pytest setup unchanged; do not attempt to unify both test trees under one recursive root run.
- Add `ruff` to the root dev dependency group so `uv run ruff check scripts tests` is reproducible from the project itself, not dependent on a globally installed binary.
- Update root docs to define two verification modes:
  - plugin-root checks: `uv run pytest` and `uv run ruff check scripts tests`
  - full repo checks: plugin-root checks plus `cd context-injection && uv run pytest && uv run ruff check context_injection tests`
- Acceptance:
  - `uv run pytest` passes from the plugin root.
  - The nested suite still passes unchanged from `context-injection/`.
  - The docs stop relying on `pytest tests` as a workaround.

2. **Align metadata and remove drift-prone duplication**
- Set the root package version in [pyproject.toml](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/pyproject.toml#L1) to `3.0.0` so it matches [.claude-plugin/plugin.json](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/.claude-plugin/plugin.json#L1).
- Remove the hardcoded version banner from [README.md](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/README.md#L1), or replace it with non-versioned wording, so prose is not a third source of truth.
- Add one root consistency test that asserts version parity between the machine-readable metadata files that are supposed to stay aligned.
- Acceptance:
  - There are only two machine-readable version surfaces, and they match.
  - A future version mismatch fails tests immediately.

3. **Clear the root hygiene debt**
- Remove the three unused imports in the root test suite.
- Leave the current root test import strategy in place for this pass; do not refactor import style unless the verification-boundary fix proves insufficient.
- Acceptance:
  - `uv run ruff check scripts tests` passes cleanly.
  - Root tests continue to pass with no behavioral changes.

4. **Codify document authority and trim duplication**
- Add a short “source of truth” section near the top of [README.md](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/README.md#L1) and [HANDBOOK.md](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/HANDBOOK.md#L1):
  - `references/` is normative for protocol/behavior
  - skills/agents are executable instructions that must conform to those contracts
  - README is overview and setup
  - HANDBOOK is operations and maintenance
- Replace duplicated protocol-detail prose in README/HANDBOOK with links to the relevant contract sections where the current duplication creates drift risk.
- Keep operator-specific content in place: commands, topology, troubleshooting, and file ownership guidance.
- Acceptance:
  - A maintainer can identify the correct edit location without guessing.
  - Version and protocol facts are no longer restated in multiple drift-prone places.

## Test Plan
- Root: `uv run pytest`
- Root: `uv run ruff check scripts tests`
- Nested package: `cd context-injection && uv run pytest`
- Nested package: `cd context-injection && uv run ruff check context_injection tests`
- New consistency coverage: root metadata/version parity test passes

## Assumptions
- `context-injection` remains a separate package and separate test surface.
- The repo should optimize for explicit multi-step verification rather than forcing a single recursive pytest run across both Python subprojects.
- No repo-local CI config exists here; any external automation should later follow the documented two-surface verification sequence.
- This cleanup pass is intentionally low-risk and avoids runtime or contract behavior changes.
