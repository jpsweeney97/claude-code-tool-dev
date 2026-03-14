Concrete rough edges I noticed in the cross-model plugin:

- The default repo-root test command is brittle. `uv run pytest` from `/cross-model` fails collection with 8 import errors, while the scoped commands succeed: `uv run pytest tests` for plugin tests and `uv run pytest` inside `context-injection/`. The likely cause is the duplicated `tests` package name plus manual import-path surgery in plugin tests, e.g. [tests/test_codex_guard.py:10](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/tests/test_codex_guard.py#L10), [tests/test_compute_stats.py:10](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/tests/test_compute_stats.py#L10), and [tests/test_read_events.py:10](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/tests/test_read_events.py#L10). The README already works around this by documenting `uv run pytest tests` at [README.md:339](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/README.md#L339).

- Version metadata is out of sync. The top-level Python package says `1.0.0` in [pyproject.toml:3](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/pyproject.toml#L3), while the plugin manifest says `3.0.0` in [.claude-plugin/plugin.json:3](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/.claude-plugin/plugin.json#L3), and the README also advertises `3.0.0` at [README.md:5](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/README.md#L5). That is the kind of drift that breaks release automation or confuses tooling.

- Root lint is not clean. `ruff check scripts tests` fails on three unused imports in [tests/test_codex_guard.py:5](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/tests/test_codex_guard.py#L5), [tests/test_compute_stats.py:8](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/tests/test_compute_stats.py#L8), and [tests/test_read_events.py:8](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/tests/test_read_events.py#L8). Small issue, but it means the repo is not “all green” at the top level.

- The Python project boundaries are blurry. The top-level [pyproject.toml](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/pyproject.toml#L1) is basically a thin local test config, while [context-injection/pyproject.toml](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/context-injection/pyproject.toml#L1) is a real package with its own dependency set and build backend. Inference: tooling behavior is going to stay surprising until one of those roles is made explicit.

- The behavioral surface is spread across many authoritative-looking places: [README.md](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/README.md), [HANDBOOK.md](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/HANDBOOK.md), the skill files, the agent files, and the two contracts under [references/](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/references). That is not a bug by itself, but it creates a high sync burden when the protocol changes.

---

I would not try to force a single recursive `pytest` run across the whole tree. The repo really contains two Python test worlds, and the nested one intentionally imports its own `tests` package helpers, e.g. [test_redact_json.py:7](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/context-injection/tests/test_redact_json.py#L7), [test_redact_yaml.py:4](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/context-injection/tests/test_redact_yaml.py#L4), [test_redact_toml.py:4](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/context-injection/tests/test_redact_toml.py#L4), and [test_redact_formats.py:12](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/context-injection/tests/test_redact_formats.py#L12). The best fixes are:

- **Root `pytest` import conflict:** Make the separation explicit instead of fighting it. In [pyproject.toml](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/pyproject.toml#L13), set root pytest discovery to only the root suite, e.g. `testpaths = ["tests"]`, and likely `norecursedirs = ["context-injection"]`. Keep `context-injection` as its own test run. If you want one command, add a wrapper script or CI job that runs both commands explicitly. That is more robust than trying to merge two `tests` packages.

- **Version drift:** Pick one canonical version source and enforce it. Since the plugin manifest is the thing Claude installs, I would treat [.claude-plugin/plugin.json](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/.claude-plugin/plugin.json#L3) as canonical, align [pyproject.toml:3](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/pyproject.toml#L3) to it, and remove the hardcoded version from [README.md:5](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/README.md#L5) or check it automatically in CI. Hardcoded version strings in prose are drift magnets.

- **Root lint failures:** Just clean them up and keep them green. Remove the unused imports in [tests/test_codex_guard.py:5](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/tests/test_codex_guard.py#L5), [tests/test_compute_stats.py:8](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/tests/test_compute_stats.py#L8), and [tests/test_read_events.py:8](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/tests/test_read_events.py#L8), then add `ruff check scripts tests` to CI or the repo’s standard check target.

- **Blurry project boundaries:** Codify the repo as “plugin root plus embedded standalone package,” because that is what it already is. The root project is mostly plugin wiring and script tests; the real packaged Python service lives under [context-injection/pyproject.toml](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/context-injection/pyproject.toml#L1). I would reflect that in root tooling and docs rather than pretending it is one uniform Python package.

- **Docs/protocol sprawl:** Reduce duplication and define an authority order. I would make `references/*.md` the normative protocol layer, keep [README.md](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/README.md) as product-level orientation, and keep [HANDBOOK.md](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/HANDBOOK.md) as operations/runbook only. Where the same rule appears in multiple places, delete the duplicate and replace it with a link to the contract. The goal is fewer sources of truth, not more documentation.

---

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
