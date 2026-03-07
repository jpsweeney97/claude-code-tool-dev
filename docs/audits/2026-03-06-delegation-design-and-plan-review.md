# Delegation Design And Plan Review

**Date:** 2026-03-06
**Targets:** `docs/plans/2026-03-06-delegation-capability-design.md`, `docs/plans/2026-03-06-delegation-implementation-plan.md`
**Related code:** `packages/plugins/cross-model/`
**Thoroughness:** Rigorous

## Entry Gate

**Inputs**
- Target spec: `docs/plans/2026-03-06-delegation-capability-design.md`
- Target plan: `docs/plans/2026-03-06-delegation-implementation-plan.md`
- Current implementation surfaces: `packages/plugins/cross-model/scripts/*.py`, `packages/plugins/cross-model/skills/delegate/SKILL.md`, `packages/plugins/cross-model/.claude-plugin/plugin.json`, `packages/plugins/cross-model/hooks/hooks.json`
- Claude Code plugin docs for plugin structure, packaging, caching, hooks, MCP, and development behavior

**Assumptions**
- The design spec is intended to be the authoritative behavioral contract.
- The implementation plan is intended to be executable without additional design decisions.
- The plugin is expected to work both in local development via `--plugin-dir` and when installed from a marketplace.

**Stakes**
- Reversibility: moderate
- Blast radius: moderate to high
- Cost of error: high
- Uncertainty: moderate

**Stopping criterion**
- Rigorous pass with source coverage across spec, plan, current plugin code, and Claude Code plugin docs.

## Summary Table

| Priority | Count | Description |
|----------|-------|-------------|
| P0 | 1 | Release/install behavior omitted in a way that can make the feature invisible to installed users |
| P1 | 4 | Correctness, safety, or integration issues likely to mislead users or create noisy behavior |
| P2 | 1 | Important polish/documentation drift |

## Findings

### P0-1: The rollout plan omits plugin release mechanics that Claude Code requires for installed plugins

**Why this matters**
- This is a plugin, not just repo-local code. Claude Code caches installed marketplace plugins, and the docs explicitly warn that code changes are not seen by users unless the plugin version is bumped. The spec and plan add a new skill, new scripts, new analytics behavior, and new docs, but they never update the plugin version or release artifacts.

**Evidence**
- Current plugin version is still `2.0.0`: `packages/plugins/cross-model/.claude-plugin/plugin.json:2-4`
- The implementation plan has no task touching `plugin.json`, `CHANGELOG.md`, or release notes.
- Claude Code docs state that installed marketplace plugins are copied to a cache and users will not see updated code unless the plugin version changes: `plugins-reference#plugin-manifest-schema`, `plugins-reference#debugging-and-development-tools`

**Impact**
- Local `claude --plugin-dir` testing can pass while installed users continue running the old plugin.
- This is exactly the class of failure that is hard to notice until after release.

**Recommended fix**
- Add an explicit release task:
  - bump `packages/plugins/cross-model/.claude-plugin/plugin.json`
  - update `packages/plugins/cross-model/CHANGELOG.md`
  - validate install/update behavior from a cached install, not only `--plugin-dir`

### P1-1: The spec contradicts itself on `thread_id`, and the plan follows the unsafe side of the contradiction

**Why this matters**
- The spec says `thread_id` is nullable and only meaningful when Codex actually emitted `thread.started`, but the JSONL parsing section also says to generate a UUID if `thread.started` is missing. The plan then emits that fabricated UUID into analytics and returns it to the skill.

**Evidence**
- Spec says missing `thread.started` should generate a UUID and log a warning: `docs/plans/2026-03-06-delegation-capability-design.md:238-244`
- The same spec later says `thread_id` is nullable and only present when JSONL contained `thread.started`: `docs/plans/2026-03-06-delegation-capability-design.md:414-420`
- Planned implementation generates a UUID when missing: `docs/plans/2026-03-06-delegation-implementation-plan.md:2100-2105`
- Planned analytics emission forwards that value into `delegation_outcome`: `docs/plans/2026-03-06-delegation-implementation-plan.md:2126-2148`
- The skill is supposed to present the thread ID to the user as a diagnostic: `packages/plugins/cross-model/skills/delegate/SKILL.md:139-147`

**Impact**
- Users can be shown a fake `thread_id`.
- Analytics can contain a field that looks resumable but is not tied to a real Codex session.
- This will make future resume support harder because historical data will mix canonical IDs with fabricated placeholders.

**Recommended fix**
- Pick one contract and enforce it consistently.
- Recommended: keep `thread_id` nullable everywhere. If `thread.started` is absent, log a stderr warning and keep `thread_id=None`.
- If an internal correlation ID is still useful, add a separate field such as `local_run_id`; do not overload `thread_id`.

### P1-2: The design underestimates interaction with the existing `PostToolUseFailure` Bash hook

**Why this matters**
- The spec only accounts for `blocked` needing exit `0` to avoid the Bash failure hook. But `/delegate` itself is implemented through Bash calls, and the plugin already has a `PostToolUseFailure` hook that counts Bash failures and nudges Claude toward `/codex`.

**Evidence**
- Existing hook matcher is every Bash failure: `packages/plugins/cross-model/hooks/hooks.json:25-35`
- Existing hook counts Bash failures per session and injects a `/codex` nudge after threshold: `packages/plugins/cross-model/scripts/nudge_codex.py:16-19`, `packages/plugins/cross-model/scripts/nudge_codex.py:50-89`
- The spec only explains exit `0` for blocked adapter results, not adapter errors or review-step Bash failures: `docs/plans/2026-03-06-delegation-capability-design.md:279-286`
- The `/delegate` skill includes multiple Bash steps beyond the adapter itself, including `git rev-parse`, `git status`, and `git diff`: `packages/plugins/cross-model/skills/delegate/SKILL.md:134-147`

**Impact**
- Deterministic adapter errors, environment issues, or review-step command failures can increment the nudge counter.
- The user may get a misleading “consider /codex” prompt while already using a Codex-backed delegation feature.

**Recommended fix**
- Add an explicit integration decision:
  - either exclude the `/delegate` adapter command from the Bash failure hook,
  - or add hook-side filtering using command/tool metadata,
  - or guarantee that known adapter-level failure classes return structured success output without tripping `PostToolUseFailure`.
- The design should mention this integration explicitly because the hook already exists in the plugin.

### P1-3: The clean-tree policy is so strict that it is likely to block normal use, including local dogfooding in this repo

**Why this matters**
- Blocking on any staged, unstaged, or untracked file is clean in theory, but the plan offers no practical escape hatch in Step 1. In active repos, untracked files are normal: scratch notes, local config, generated files, audit docs, or plugin work-in-progress.

**Evidence**
- The spec blocks on any dirty file, including untracked files, and has no Step 1 bypass: `docs/plans/2026-03-06-delegation-capability-design.md:57-71`, `docs/plans/2026-03-06-delegation-capability-design.md:85-87`
- The skill presents dirty-tree blocking as the normal recovery path: `packages/plugins/cross-model/skills/delegate/SKILL.md:161-163`
- In the current workspace, `git status --short` already reports unrelated untracked paths, including the new delegate skill directory and audit artifacts, so the feature would self-block during development.

**Impact**
- The first user experience is likely to be “blocked” instead of “delegated”.
- The feature is harder to test locally than the spec implies.

**Recommended fix**
- Keep the strict default, but add one of:
  - an opt-in worktree mode in Step 1,
  - a local-only override for untracked files outside a generated allowlist,
  - or an explicit deferred-work item marked as required before marketplace release, not merely “future steps”.
- At minimum, call out in the plan that local development of the plugin itself will often hit this gate.

### P1-4: The already-created `/delegate` skill contains destructive revert guidance, and the plan does not include fixing it

**Why this matters**
- The plan says the skill already exists and focuses on adapter implementation, but the current skill text tells Claude to use `git checkout --` to discard changes. That conflicts with the repo’s operating rules and with the general safety posture the delegation design is trying to establish.

**Evidence**
- Current skill troubleshooting recommends `git checkout -- .` and `git checkout -- <file>`: `packages/plugins/cross-model/skills/delegate/SKILL.md:181-183`
- The implementation plan treats `SKILL.md` as already created and does not include a task to audit or correct the destructive guidance.

**Impact**
- The delegation feature can leave users with instructions that are unsafe or inconsistent with the repo’s collaboration rules.
- This is especially awkward because the whole design is framed around safer execution and review.

**Recommended fix**
- Add a task to revise `skills/delegate/SKILL.md` before implementation starts.
- Replace destructive revert advice with safer alternatives, or instruct Claude to ask before discarding changes.

### P1-5: The plan promises “atomic append” for shared analytics logging, but the proposed implementation does not actually add any atomicity guarantees

**Why this matters**
- The spec explicitly elevates `append_log` as an atomic append helper, but the implementation is just `open(..., "a")` followed by `write(...)`. That may be acceptable in practice, but it is weaker than the contract being claimed.

**Evidence**
- Spec export contract says `append_log(entry: dict) -> bool` is an atomic append helper: `docs/plans/2026-03-06-delegation-capability-design.md:146-150`
- Planned implementation is plain append-mode file I/O with no lock or explicit single-write guarantee beyond normal buffered file semantics: `docs/plans/2026-03-06-delegation-implementation-plan.md:603-612`

**Impact**
- The implementation and the contract diverge.
- Future concurrency assumptions may be built on a guarantee the code does not clearly provide.

**Recommended fix**
- Either relax the contract language from “atomic append” to “best-effort append”, or implement a stronger append strategy with one-write semantics and clear concurrency expectations.

### P2-1: The release/docs surface is not treated as a first-class deliverable even though this is a user-facing plugin capability

**Why this matters**
- The spec and plan are very detailed on code paths and tests, but they underspecify how users discover the new capability once installed.

**Evidence**
- The plugin README documents current plugin capabilities and command surfaces, but the plan does not include a README update task despite adding a new public skill and new analytics event behavior.
- Claude Code plugin docs emphasize clear documentation and versioning for shared plugins: `plugins#develop-more-complex-plugins`, `plugins-reference#debugging-and-development-tools`

**Recommended fix**
- Add a small documentation/release task:
  - update `packages/plugins/cross-model/README.md`
  - document `/delegate` in user-facing usage and safety notes
  - note the narrower trust model compared with `/codex` and `/dialogue`

## Exit Gate

- Source coverage completed against spec, plan, current implementation, and plugin docs.
- Main risks are concentrated in plugin release behavior, ID contract consistency, and integration with existing hooks.
- The design is implementable, but it is not release-ready as written.
