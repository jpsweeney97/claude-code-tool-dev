---
date: 2026-04-01
time: "00:00"
created_at: "2026-04-01T04:00:04Z"
session_id: 31328517-9aa1-4813-8257-fa749b2f43a3
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-03-31_23-22_plan-review-and-revision-persistence-hardening.md
project: claude-code-tool-dev
branch: main
commit: 80ae21f5
title: "plan revision round 4 — persistence hardening"
type: handoff
files:
  - docs/superpowers/plans/2026-03-31-persistence-hardening-and-type-narrowing.md
  - docs/reviews/2026-03-31-persistence-hardening-and-type-narrowing-adversarial-review.md
  - docs/learnings/learnings.md
---

# plan revision round 4 — persistence hardening

## Goal

Incorporate Round 4 adversarial review findings into the persistence hardening implementation plan, then merge the fully-revised plan to main for execution.

**Trigger:** The user had performed a structured adversarial review of the 2017-line implementation plan (`docs/superpowers/plans/2026-03-31-persistence-hardening-and-type-narrowing.md`), saved as `docs/reviews/2026-03-31-persistence-hardening-and-type-narrowing-adversarial-review.md`. The review surfaced 5 findings with a confidence score of 3/5 — "workable but brittle enough that I would not execute it unchanged."

**Stakes:** The plan is the direct input for subagent-driven implementation. Unresolved operational ambiguities (like the branch sequencing issue) would cause a worker to strand commits on the wrong branch or skip spec updates entirely. The Round 4 findings were about execution mechanics, not technical design — the most likely failure mode if unaddressed was a worker following the plan literally and producing a stranded commit.

**Success criteria:** (1) All accepted findings incorporated into the plan. (2) Test counts updated to reflect new tests. (3) Plan merged to main. (4) Clean stopping point for implementation session.

**Connection to project arc:** Fourth session in the persistence hardening chain: design (session 1) → plan (session 2) → review rounds 1-3 (session 3) → **review round 4 + merge** (session 4) → execute (session 5). The plan at `docs/superpowers/plans/2026-03-31-persistence-hardening-and-type-narrowing.md` is now on `main` and ready for execution.

## Session Narrative

Session began by loading the prior handoff (`2026-03-31_23-22_plan-review-and-revision-persistence-hardening.md`), which described the plan review session with 3 rounds of findings (10 findings total). The handoff's next steps were: (1) commit and merge the plan revision, (2) execute the implementation plan.

The user overrode the handoff's suggested next step — instead of committing and executing, they provided a Round 4 adversarial review with 5 new findings. The review was structured as: assumptions audit (5 items), pre-mortem (2 scenarios), dimensional critique (6 dimensions), severity summary (5 findings), and confidence check.

Analysis of each finding required cross-referencing the plan against the codebase. Key verification reads:

- **Plan lines 42-95:** Task 0 commits a design spec update with no branch specified. Branch 1 then starts with `git checkout main && git checkout -b fix/persistence-replay-hardening`. A worker following the plan literally would commit Task 0 on whatever branch they're on (the `chore/plan-revision-persistence-hardening` branch), then `git checkout main` would leave that commit behind. The branch sequencing ambiguity was real and blocking.

- **`profiles.py:54-63`:** The local override merge path reads `consultation-profiles.local.yaml` and merges with base profiles via `{**profiles[name], **overrides}`. The plan's YAML ingress tests (lines 1739-1790) only wrote `consultation-profiles.yaml`, leaving the local override path uncovered. The reviewer's claim that "the `consultation-profiles.local.yaml` merge path stays untested" was verified.

- **`pyproject.toml:11`:** `ruff>=0.8` is a dev dependency. Every task in the plan gated only on `uv run pytest`. The reviewer's claim that "pytest is a sufficient ship gate" was classified as "wishful" — ruff failures would surface late.

- **Plan line 2015:** The stale checklist line said "YAML ingress path tested via monkeypatched `load_profiles`" but Task 5 actually patches `_REFERENCES_DIR`. This was evidence of plan-level drift — the plan was revised in Round 3 to use `_REFERENCES_DIR`, but the checklist at line 2015 wasn't updated.

- **Plan line 71:** The lineage literal rollout text already existed: "New enum values require coordinated rollout: update the `Literal` type first, then start writing the new value." The reviewer wanted this strengthened. I partially accepted — added a WARNING callout but argued the severity is lower than "high" in a single-codebase context where `HandleStatus` and the frozenset validation update in the same commit.

After presenting my analysis of all 5 findings, the user confirmed my proposed changes with one refinement: update the task-level and cumulative test counts when adding the local override test. The user explicitly confirmed: "Your proposed changes are the right ones."

Applied 14 targeted edits to the plan:
1. Added design spec to Branch 1 file map (new row)
2. Relocated Task 0 into Branch 1 scope — moved it after `git checkout -b fix/persistence-replay-hardening`. Added rollout-order WARNING to the lineage literal validation section.
3-9. Added `uv run ruff check . && uv run ruff format --check .` before each of 7 Python commit steps
10. Added `_write_local_override_yaml` helper to `TestYamlIngressValidation`
11. Added `test_local_override_bad_posture_rejected` test
12. Updated Task 5 test count: 13→14 new tests, 22→23 total
13. Updated Step 2 to include `TestYamlIngressValidation` in "verify they fail" run
14. Fixed stale checklist: `load_profiles` → `_REFERENCES_DIR` patch with real YAML

After applying all edits, spot-checked the restructured sections: Task 0 now appears under Branch 1 after the branch creation step, the YAML test section has the local override test and helper, all 7 commit steps have ruff gates, and the checklist is updated.

User requested commit and merge. Committed on `chore/plan-revision-persistence-hardening` with message documenting Round 4 changes. Merged to `main` with `--no-ff`. Deleted branch. User then requested handoff save.

## Decisions

### Fold Task 0 into Branch 1 scope

**Choice:** Move Task 0 (design spec update) from a standalone pre-branch position into Branch 1, executing after `git checkout -b fix/persistence-replay-hardening`.

**Driver:** Round 4 adversarial review finding #1 (blocking): "Task 0 can strand or invalidate the spec update before implementation starts." Verified by reading plan lines 42-95 — Task 0 had no branch specified, so it would commit on whatever branch the worker happens to be on. The subsequent `git checkout main` would leave the commit behind.

**Alternatives considered:**
- **Merge chore branch first, then create fix branch** — would work but requires an undocumented two-merge dance. The plan never said "merge chore branch to main before starting." Rejected because it adds a dependency the plan doesn't encode.
- **Create a dedicated docs branch for Task 0** — over-engineered. The design spec update is logically coupled to the code that implements it. Rejected because it splits related changes across branches.

**Trade-offs accepted:** The fix branch now contains a docs-only commit (Task 0) alongside code commits. Minor overhead — one extra commit that contains no code.

**Confidence:** High (E2) — verified by reading both the plan structure and the branch protection hook behavior. The hook blocks edits on `main`, so a worker on `main` would be blocked from making the Task 0 commit.

**Reversibility:** High — Task 0 can be moved back to a standalone position if needed. Plan-only change.

**Change trigger:** If the project adopts a workflow where spec updates are committed separately from implementation (e.g., on a `docs/*` branch).

### Partially accept lineage literal rollout-order finding

**Choice:** Strengthen the existing rollout text to a WARNING callout in the design spec update. Do not add runtime rollout gates.

**Driver:** Round 4 finding #2 (high): "Lineage literal tightening creates a quiet rollout-order failure mode." The concern is that a newer version writing new `status` values, followed by a downgrade, would cause older readers to silently skip handles.

**Alternatives considered:**
- **Accept at full severity and add runtime gates** — would detect version mismatch at replay time. Rejected because this is a single-codebase plugin, not a distributed system. The `Literal` type and `frozenset(get_args(...))` validation update in the same commit. The "partial rollout" scenario requires a version downgrade, which is inherently lossy.
- **Reject the finding entirely** — the rollout text already existed at plan line 71. Rejected because the WARNING callout makes the constraint more prominent and harder to miss during implementation.

**Trade-offs accepted:** The WARNING adds documentation overhead but no runtime cost. A future developer reading the design spec will see the explicit rollout constraint rather than having to infer it from the validation code.

**Confidence:** High (E2) — verified that `HandleStatus` and `CapabilityProfile` are `Literal` types at `models.py:10-12`, and the frozenset is derived via `get_args()` which updates automatically when the type changes.

**Reversibility:** High — text-only change. Can be strengthened to runtime gates later if the deployment model changes.

**Change trigger:** If the plugin is deployed across multiple versions simultaneously (e.g., rolling update across machines), runtime rollout gates become necessary.

### Add local override YAML merge path test

**Choice:** Add one test (`test_local_override_bad_posture_rejected`) that writes both `consultation-profiles.yaml` (valid) and `consultation-profiles.local.yaml` (bad posture override), verifies the merged result is caught by validation.

**Driver:** Round 4 finding #3 (moderate): "YAML ingress coverage still misses the local override merge path." Verified by reading `profiles.py:54-63` — the local override merge logic exists and was uncovered by the plan's tests.

**Alternatives considered:**
- **Monkeypatch `load_profiles()` instead of `_REFERENCES_DIR`** — was explicitly rejected in Round 3 review (prior session). User said: "Monkeypatching `load_profiles()` is still weaker than true ingress coverage."
- **Skip the test** — rejected because `profiles.py:54-63` has real merge logic (`{**profiles[name], **overrides}`) that should be exercised.

**Trade-offs accepted:** Adds a `_write_local_override_yaml` helper (~7 lines) and one test (~14 lines). Minimal overhead.

**Confidence:** High (E1) — standard test pattern. The merge path at `profiles.py:54-63` is straightforward.

**Reversibility:** High — test-only change.

**Change trigger:** If the local override mechanism is removed or redesigned.

### Add ruff check/format gates to all commit steps

**Choice:** Add `uv run ruff check . && uv run ruff format --check .` before each Python `git commit` step. 7 gates total across Tasks 1-6 and the controller test commit. Task 0 is docs-only, no ruff gate.

**Driver:** Round 4 finding #4 (moderate): "Pytest-only gates leave a likely late CI failure path." Verified `ruff>=0.8` at `pyproject.toml:11`.

**Alternatives considered:**
- **Add ruff only to final commit steps (per branch)** — catches issues eventually but doesn't pinpoint which task introduced them. Rejected because fixing ruff issues at the end of a branch is harder than fixing them per-commit.
- **Skip ruff gates** — rejected because a plan that claims completion with failing lint is incomplete.

**Trade-offs accepted:** Each commit step is slightly longer (2 extra lines of bash). The `cd` pattern requires navigating to the package directory for ruff, then back to repo root for git.

**Confidence:** High (E1) — standard lint gate pattern.

**Reversibility:** High — removing ruff gates just means removing 2 lines from each commit step.

**Change trigger:** If the package drops ruff from dev dependencies.

### Defer full-file replacement rewrite

**Choice:** Do not rewrite the plan's implementation steps from full-file replacements to function-level edits. The TDD structure and branch isolation provide sufficient safety.

**Driver:** Round 4 finding #5 (low): "Full-file replacement steps are more brittle than the behavioral changes require." The reviewer's suggested mitigation — rewriting as function-level edits — is a significant plan rework for a low-severity finding.

**Alternatives considered:**
- **Rewrite all larger implementation steps as function-level edits** — more resilient in a shared repo but significant effort. The plan is already 2062 lines. Rejected as disproportionate.

**Trade-offs accepted:** A worker following the plan's full-file replacement steps on a branch where other changes have been made could clobber those changes. Mitigated by: (1) each task runs on a feature branch, (2) TDD catches correctness issues, (3) the plan specifies exact files to `git add` (not `git add .`).

**Confidence:** Medium (E1) — branch isolation is a structural mitigation but doesn't prevent all clobber scenarios (e.g., if a worker switches to the branch after making changes on it).

**Reversibility:** High — can rewrite specific steps as function-level edits during execution if a clobber occurs.

**Change trigger:** If a concrete clobber occurs during execution, rewrite the affected step as function-level edits before proceeding.

## Changes

### Modified files

| File | Lines changed | Purpose |
|------|--------------|---------|
| `docs/superpowers/plans/2026-03-31-persistence-hardening-and-type-narrowing.md` | 2017 → 2062 (+45) | 14 targeted edits incorporating Round 4 review findings |

### New files

| File | Lines | Purpose |
|------|-------|---------|
| `docs/reviews/2026-03-31-persistence-hardening-and-type-narrowing-adversarial-review.md` | ~64 | User's Round 4 adversarial review (assumptions audit, pre-mortem, dimensional critique, severity summary) |

### Plan revision details

**Structural change (Task 0 relocation):**
- Task 0 moved from standalone position (before Branch 1) to inside Branch 1 (after `git checkout -b`). It is now `### Task 0:` under `## Branch 1:`, executing on `fix/persistence-replay-hardening`.
- Design spec added to Branch 1 file map with `(repo root)` annotation (since other files in the map are relative to `packages/plugins/codex-collaboration/`).
- Rollout-order WARNING added to the lineage literal validation section in the design spec update text.

**YAML test additions:**
- `_write_local_override_yaml` helper added to `TestYamlIngressValidation` class
- `test_local_override_bad_posture_rejected` test added — writes valid base profile, injects bad posture via local override, verifies merged result caught by validation
- Step 2 updated to run `TestYamlIngressValidation` alongside `TestTypeNarrowing` in "verify they fail" step

**Ruff gates (7 commit steps):**
- Each Python commit step now has `uv run ruff check . && uv run ruff format --check .` before `git commit`
- Pattern: `cd` to package dir for ruff, then `cd` back to repo root for `git add/commit`
- Task 0 has no ruff gate (docs-only commit)

**Test count updates:**
- Task 5: 13 → 14 new tests, 22 → 23 total at task level
- Cumulative: 66 → 67 new tests across all tasks

**Checklist fix:**
- Line 2060 (was 2015): `"monkeypatched load_profiles"` → `"_REFERENCES_DIR patch with real YAML, including local override merge path"`

## Codebase Knowledge

### profiles.py Local Override Merge Path

`profiles.py:40-64` — `load_profiles()` has two file reads:
1. Base: `base / "consultation-profiles.yaml"` (line 45-52)
2. Local: `base / "consultation-profiles.local.yaml"` (line 54-63)

The merge at line 58-62:
```python
for name, overrides in local_data.get("profiles", {}).items():
    if name in profiles:
        profiles[name] = {**profiles[name], **overrides}
    else:
        profiles[name] = overrides
```

This means local overrides do a shallow merge (not deep). A local file that overrides `posture` but not `turn_budget` will produce a profile with the local `posture` and the base `turn_budget`. The plan's new test exercises this: valid base profile with `posture: "collaborative"`, local override with `posture: "adversrial"` (typo), merged result caught by validation.

`_REFERENCES_DIR` at `profiles.py:37` is a module-level `Path` — the monkeypatch target for YAML ingress tests. `load_profiles()` accepts `base_path` parameter (line 41-44) that falls back to `_REFERENCES_DIR`, but the plan patches `_REFERENCES_DIR` directly to exercise the default path.

### Existing Local Override Test

`test_validate_profiles.py:145` — `test_local_override_validated_if_exists` already tests that local overrides are validated. The plan's new test is distinct: it tests that a bad value *in the local override* is caught by the type-narrowing validation that doesn't exist yet (added in Task 5 Step 3). The existing test validates that the local override file is loaded and parsed; the new test validates that invalid values flowing through the merge path are caught by the runtime validation gate.

### ruff in Package Dev Dependencies

`packages/plugins/codex-collaboration/pyproject.toml:11` — `"ruff>=0.8"` in dev dependencies. This is a range pin (library-style), not exact (app-style). The ruff gate runs from the package directory (`cd packages/plugins/codex-collaboration`), which picks up the package's `pyproject.toml` for ruff configuration.

### Branch Protection Hook Interaction with Task 0

The project's `PreToolUse` hook (documented in `.claude/rules/workflow/git.md`) blocks edits on protected branches (`main`, `master`). This is why the Round 4 finding was classified as "blocking" — a worker on `main` attempting Task 0's design spec edit would be blocked by the hook. The worker would then need to create a branch (which the plan didn't instruct), introducing an unscripted decision point. By placing Task 0 after `git checkout -b fix/persistence-replay-hardening`, the worker is always on a valid working branch.

### Plan Edit Approach: Targeted Replacements via Edit Tool

All 14 plan edits were made using the Edit tool's exact string replacement, not full-file rewrites. Each edit targeted a specific string in the plan and replaced it with the revised version. This was important because the plan is 2062 lines — a full-file rewrite would have been error-prone and hard to verify. The targeted approach meant each edit could be independently verified by reading the surrounding context.

### Plan Structure Post-Revision

The plan has 7 tasks across 2 branches:

| Branch | Tasks | Tests |
|--------|-------|-------|
| `fix/persistence-replay-hardening` | Task 0 (spec update), Task 1 (replay helper, 22 tests), Task 2 (TurnStore, 5 tests), Task 3 (LineageStore, 13 tests), Task 4 (Journal, 10 tests + 2 controller tests) | 52 new |
| `chore/type-narrowing` | Task 5 (profiles, 14 tests), Task 6 (models, 1 test) | 15 new |
| **Total** | 7 tasks | **67 new tests** |

Running total per task:
- Task 1: 359 + 22 = 381
- Task 2: 381 + 5 = 386
- Task 3: 386 + 13 = 399
- Task 4: 399 + 10 = 409
- Task 4b (controller): 409 + 2 = 411
- Task 5: 9 existing + 14 new = 23 (task-level), full suite "all tests pass"
- Task 6: 8 existing + 1 new = 9 (task-level), full suite "all tests pass"

## Context

### Mental Model

This session was an **execution-mechanics review** — the Round 4 findings were about plan execution risks (branch choreography, lint gates, test coverage gaps), not about the technical design of the persistence hardening itself. The highest-value finding (#1, blocking) was entirely about git workflow, not about JSONL replay or store validation.

This pattern — operationally-focused review after technically-focused review — is natural for large plans. Rounds 1-3 caught protocol-layer invariants (recovery code field dependencies, conditional requirements). Round 4 caught the plan's internal consistency and the execution environment (which branch, which lint tools, which test paths).

The review layers form a taxonomy:
- **Schema layer** (original plan) — field presence and type correctness
- **Protocol layer** (Rounds 1-3) — per-operation+phase conditional requirements derived from consumer code
- **Integration layer** (Rounds 1-3) — controller-level composition of store behavior with recovery/read paths
- **Execution layer** (Round 4) — branch choreography, lint gates, test coverage completeness, internal consistency

Each layer catches issues that the others miss. The plan is now reviewed at all four layers.

### Project State

- **Branch:** `main` at `80ae21f5` (merge commit)
- **Plan:** Revised through 4 review rounds, merged to main, ready for execution
- **Design spec:** Needs updating (Task 0 in the plan — executes on `fix/persistence-replay-hardening`)
- **Tests:** 359/359 passing (unchanged — no code changes in sessions 2-4)
- **No implementation branches exist yet**

### Review Statistics (Cumulative Across All Rounds)

| Metric | Value |
|--------|-------|
| Review rounds | 4 |
| Total findings | 15 (2 P1, 5 P2, 4 P3, 1 blocking, 2 moderate, 1 low) |
| Accepted | 12 (1 partially) |
| Deferred | 1 (full-file replacement rewrite) |
| Rejected | 0 |
| New tests added to plan | +17 (50 → 67) |
| Plan line growth | +571 (1491 → 2062) |
| Decisions documented | 10 total (5 prior + 5 this session) |

### Handoff Chain

| Session | Date | Purpose | Handoff |
|---------|------|---------|---------|
| 1 | 2026-03-31 | Design spec | `archive/2026-03-31_17-04_codex-consult-resolution-and-persistence-hardening-design.md` |
| 2 | 2026-03-31 | Implementation plan | `archive/2026-03-31_21-22_persistence-hardening-implementation-plan.md` |
| 3 | 2026-03-31 | Review rounds 1-3 | `archive/2026-03-31_23-22_plan-review-and-revision-persistence-hardening.md` |
| **4** | **2026-04-01** | **Review round 4 + merge** | **This handoff** |
| 5 | Next | Execute plan | Not started |

## Learnings

### Plan-level drift is a real maintenance problem

**Mechanism:** Large plans (2000+ lines) act like codebases — changes in one section can leave stale references elsewhere. The plan was revised in Round 3 to use `_REFERENCES_DIR` patching, but the verification checklist at line 2015 still referenced the old `load_profiles` approach. The stale line was only caught by the Round 4 adversarial review.

**Evidence:** Plan line 2015 (pre-fix): "YAML ingress path tested via monkeypatched `load_profiles` (F4)". Plan lines 1764/1776/1787 (actual code): `monkeypatch.setattr("server.profiles._REFERENCES_DIR", tmp_path)`.

**Implication:** After editing a plan, grep for references to the changed concept. Plans with verification checklists should be checked for consistency with the implementation steps they summarize. The same DRY principle that applies to code applies to plans.

**Watch for:** Any plan revision that changes an approach (e.g., "we now test via X instead of Y") — search the entire plan for mentions of the old approach.

### Adversarial reviews at different layers catch different classes of issues

**Mechanism:** Technically-focused reviews (Rounds 1-3) caught protocol-layer invariants — field dependencies, conditional requirements, recovery code access patterns. Operationally-focused review (Round 4) caught execution mechanics — branch choreography, lint gates, test coverage completeness, internal consistency.

**Evidence:** Round 1 P1 finding (technical): "Journal validates wrong layer — flat type checks miss per-operation+phase requirements that recovery depends on." Round 4 blocking finding (operational): "Task 0 can strand or invalidate the spec update before implementation starts."

**Implication:** Plan reviews benefit from at least two passes with different lenses: (1) technical correctness of the code design, (2) operational correctness of the execution sequence. Neither subsumes the other.

**Watch for:** Plans that pass technical review but have undocumented execution prerequisites or ambiguous task ordering.

## Next Steps

### 1. Execute the implementation plan

**Dependencies:** None — plan is merged to main at `80ae21f5`.

**What to read first:** The plan itself at `docs/superpowers/plans/2026-03-31-persistence-hardening-and-type-narrowing.md`. It contains all code, test cases, commands, and gates. No other files need to be read before starting.

**Approach suggestion:** Invoke `superpowers:subagent-driven-development` skill. The plan has 7 tasks (Task 0 → Task 6). Task 0 updates the design spec (docs only, on the fix branch). Tasks 1-4 + controller tests execute on `fix/persistence-replay-hardening`. After merging Branch 1, Tasks 5-6 execute on `chore/type-narrowing`.

**Acceptance criteria:** All 359 existing tests pass. 67 new tests added and passing. `check_health()` available on all three stores. Malformed records diagnosed (not crashed). Type narrowing catches typo postures/efforts. Per-operation+phase conditional requirements enforced. Compatibility decisions documented inline. `uv run ruff check . && uv run ruff format --check .` passes before each commit.

**Potential obstacles:** Full-file replacement steps may need adjustment if the codebase has changed since the plan was written. The TDD structure (write tests first, verify they fail, then implement) mitigates this — test failures will surface any drift.

### 2. (After Branch 1 merged) AC6 analytics emission

**Dependencies:** Branch 1 merged. Ticket T-20260330-03. Delivery roadmap at `delivery.md:255` (packet 2b).

**What to read first:** `delivery.md` for packet 2b acceptance criteria. `contracts.md` §Analytics for the event schema.

**Approach suggestion:** This is actual roadmap work (not debt/cleanup). Scope and plan separately.

## In Progress

Clean stopping point. The implementation plan is revised, merged to main (`80ae21f5`), and ready for execution. No code changes in flight. No uncommitted files. Branch `chore/plan-revision-persistence-hardening` has been deleted.

## Open Questions

### AC6 analytics emission

Deferred from T-03. Actual roadmap work in packet 2b (`delivery.md:255`). Not addressed in sessions 1-4. Ticket T-20260330-03 tracks it.

### Diagnostics consumer architecture

The design spec defers wiring `check_health()` to a production surface. The store ownership split (control plane owns journal; dialogue owns lineage/turn stores) means no single component can call all three without refactoring. The journal `check_health` outlier (takes `session_id`) adds complexity to a uniform consumer.

### Deferred review suggestions (S1-S16)

16 suggestions from the T-03 second review agents were not independently validated. Unchanged from prior handoffs. May contain false positives.

## Risks

### Plan code may need adjustment during implementation

The plan contains 2062 lines including ~1800 lines of code written from reading, not execution. The TDD structure mitigates this — each step verifies before proceeding. Four review rounds (15 findings) have reduced the risk of unverified assumptions, but the code hasn't been run.

### Branch merge ordering matters

Branch 2 (`chore/type-narrowing`) must be created after Branch 1 is merged. If created in parallel, the type narrowing tests may interact with the replay migration in unexpected ways. The plan documents this dependency explicitly.

### Full-file replacement steps are brittle (deferred)

Round 4 finding #5 (low) noted that full-file replacement steps could clobber unrelated edits. Deferred because TDD + branch isolation provide sufficient safety. If a concrete clobber occurs during execution, rewrite the affected step as function-level edits.

## References

| What | Where |
|------|-------|
| Implementation plan (final) | `docs/superpowers/plans/2026-03-31-persistence-hardening-and-type-narrowing.md` |
| Round 4 adversarial review | `docs/reviews/2026-03-31-persistence-hardening-and-type-narrowing-adversarial-review.md` |
| Design spec | `docs/superpowers/specs/2026-03-31-persistence-hardening-and-type-narrowing-design.md` |
| Recovery coordinator | `packages/plugins/codex-collaboration/server/dialogue.py:435-601` |
| Profile resolver | `packages/plugins/codex-collaboration/server/profiles.py` |
| Local override merge | `packages/plugins/codex-collaboration/server/profiles.py:54-63` |
| HandleStatus/CapabilityProfile | `packages/plugins/codex-collaboration/server/models.py:10-12` |
| Prior handoff (round 3) | `docs/handoffs/archive/2026-03-31_23-22_plan-review-and-revision-persistence-hardening.md` |
| Prior handoff (plan writing) | `docs/handoffs/archive/2026-03-31_21-22_persistence-hardening-implementation-plan.md` |
| Prior handoff (design) | `docs/handoffs/archive/2026-03-31_17-04_codex-consult-resolution-and-persistence-hardening-design.md` |

## Gotchas

### Task 0 executes on the fix branch, not on main

After Round 4 revision, Task 0 (design spec update) runs on `fix/persistence-replay-hardening` after `git checkout -b`. The design spec update travels with the implementation. Previous plan versions had Task 0 floating before any branch creation, which would have stranded the commit.

### Ruff gates use a two-cd pattern

Each ruff gate navigates to the package directory (`cd packages/plugins/codex-collaboration`) for `uv run ruff check/format`, then back to the repo root (`cd /Users/jp/Projects/active/claude-code-tool-dev`) for `git add/commit`. This avoids hardcoding long paths into the ruff command and ensures ruff scans from the right root.

### Local override merge is shallow, not deep

`profiles.py:58-62` uses `{**profiles[name], **overrides}` — a shallow dict merge. A local override that specifies only `posture` will replace `posture` but keep other fields from the base profile. This is correct for flat profile dicts but would be wrong if profiles ever become nested.

### Plan test count is 67, not 66

The prior handoff documented 66 tests. The Round 4 revision added 1 local override test, bringing the total to 67. The cumulative count in the plan is: 22 (replay) + 5 (turn) + 13 (lineage) + 10 (journal) + 2 (controller) + 14 (profiles) + 1 (models) = 67.

## User Preferences

**Review style:** Structured adversarial reviews with assumptions audit, pre-mortem, dimensional critique, severity levels, and confidence score. The Round 4 review format was consistent with prior rounds.

**Bookkeeping matters:** User explicitly added a refinement: "once you add the local-override YAML test, update the task-level and cumulative test counts." Attention to plan-internal consistency, not just correctness.

**Deferral is acceptable when justified:** User agreed that deferring the full-file replacement rewrite was "reasonable" and classified it as "a plan quality issue, not a blocker."

**Phase-boundary workflow:** Consistent across all 4 sessions. User separates design → plan → review → execute into distinct sessions with handoff saves at each boundary. This is the fourth consecutive session following this pattern.

**Merge without PR for docs-only changes:** User instructed "commit and merge" without requesting a PR, consistent with the prior session's handoff suggestion that "a direct merge to main is appropriate" for documentation-only changes.
