## Adversarial Review: 2026-03-31 Persistence Hardening and Type Narrowing Implementation Plan

### 1. Assumptions Audit
- **Task 0 can be committed before branch creation without breaking workflow** - `wishful`. If this is wrong, the worker either commits on the wrong branch, hits branch protection on `main`, or starts the fix branch from a base that does not actually contain the spec update.
- **Pytest is a sufficient ship gate for both branches** - `wishful`. If this is wrong, the plan can complete all scripted steps and still fail late on `ruff` or formatting after the expensive work is already done.
- **Task 5’s YAML ingress tests cover the actual configuration ingress surface** - `wishful`. If this is wrong, the loader’s `consultation-profiles.local.yaml` merge path remains untested even though the plan claims realistic ingress coverage.
- **Rejecting unknown lineage literals is an acceptable compatibility tradeoff** - `plausible`. If this is wrong, a partial rollout or newer writer causes handles to be silently skipped on older readers.
- **Full-file replacement instructions are safe in this repo’s live workspace** - `plausible`. If this is wrong, a worker following the plan literally can clobber unrelated edits or copy stale file context back into the tree.

### 2. Pre-Mortem
1. **Most likely failure:** the worker follows Task 0 literally, makes the design-spec commit, then runs `git checkout main && git checkout -b fix/persistence-replay-hardening`. The spec commit is now either stranded on the wrong branch or was attempted on `main` and blocked by branch policy. Implementation proceeds anyway, recreating the plan/spec drift the task was supposed to prevent.
2. **Most damaging quiet failure:** lineage literal tightening ships before every writer is updated. Older readers replay logs containing a new `status` or `capability_class`, classify those rows as `schema_violation`, and quietly skip affected handles. Nothing crashes; dialogue state simply appears to disappear, which is much harder to diagnose.

### 3. Dimensional Critique
#### Correctness
The branch choreography is internally inconsistent. Task 0 tells the worker to commit the spec update before any implementation branch exists, but Branch 1 then starts with `git checkout main && git checkout -b fix/persistence-replay-hardening`. In this repo, work is supposed to happen on feature branches, and this sequence can leave the spec update off the actual implementation branch entirely.

The plan still contains one stale internal claim: the verification checklist says YAML ingress is tested “via monkeypatched `load_profiles`,” but Task 5 actually patches `_REFERENCES_DIR` and reads real YAML. That is small, but it is direct evidence that the document is still drifting while trying to prevent drift elsewhere.

The lineage literal rejection rule is now a hard correctness choice, not just test coverage. The inline rationale is good, but the plan still assumes rollout order discipline instead of enforcing it.

#### Completeness
The YAML ingress section does not actually test the local override merge path, even though `load_profiles()` supports `consultation-profiles.local.yaml` and the stated goal was to cover ingress more realistically. The tests only create `consultation-profiles.yaml`.

The execution gates are incomplete. The package declares `ruff` in its dev dependencies, but every task gates only on pytest. That leaves a predictable late failure path for import ordering, unused imports, formatting, and style cleanup.

Task 0 is explicit about its commit, but not about how that commit is carried forward. There is no stated branch name, merge step, or cherry-pick step that ties the spec update to the implementation branch that follows.

#### Security / Trust Boundaries
No material new security boundary is introduced by this plan beyond normal local file parsing and test execution. Skipping further review here.

#### Operational
The branch/commit choreography is the highest operational risk. A worker can follow the plan exactly and still end up on the wrong base or blocked by branch policy.

The full-file replacement instructions for `turn_store.py`, `lineage_store.py`, and `journal.py` are operationally brittle in a shared repo. They maximize copy-paste fidelity, but they also maximize the chance of overwriting unrelated local edits or reintroducing stale context from the draft.

Running the full suite after nearly every task is good for safety, but without a companion lint/format gate it still does not prove the branch is actually shippable.

#### Maintainability
The plan is large and code-heavy enough that it is already drifting from its own updated intent. The stale YAML verification line is evidence. The more full file bodies, exact counts, and commit text it embeds, the faster it will rot as the codebase moves.

The prescriptive “replace the full file with” instructions couple the plan to exact current file contents rather than to behavioral changes and invariants. That makes the plan fragile to unrelated edits and harder to reuse or partially execute.

#### Alternatives Foregone
A smaller delta-oriented plan was not chosen. Instead of full file replacements and per-step commit scripts, the plan could specify invariants, touched functions, and verification gates only. That would be less convenient to implement mechanically, but much safer in a repo where unrelated edits may exist.

A dedicated docs branch or an initial `chore/...` branch for Task 0 was not chosen. That alternative would remove the current branch-sequencing ambiguity entirely.

### 4. Severity Summary
1. **[blocking] Task 0 can strand or invalidate the spec update before implementation starts**  
   Suggested mitigation or investigation: make Task 0 happen on an explicit branch that the fix branch is based on, or move Task 0 into the start of `fix/persistence-replay-hardening` so the spec change and code change share one coherent branch lineage.
2. **[high] Lineage literal tightening creates a quiet rollout-order failure mode**  
   Suggested mitigation or investigation: add an explicit rollout precondition stating that readers must be updated before any writer emits new `status` or `capability_class` values, and verify that no current writer can emit future literals during this branch.
3. **[moderate] YAML ingress coverage still misses the local override merge path**  
   Suggested mitigation or investigation: add one real test that writes both `consultation-profiles.yaml` and `consultation-profiles.local.yaml` under the patched `_REFERENCES_DIR` and proves the merge plus validation path works.
4. **[moderate] Pytest-only gates leave a likely late CI failure path**  
   Suggested mitigation or investigation: add `uv run ruff check .` and, if the repo expects it, `uv run ruff format --check .` after each task or at least before each commit.
5. **[low] Full-file replacement steps are more brittle than the behavioral changes require**  
   Suggested mitigation or investigation: rewrite the implementation steps in terms of function-level edits and invariants, especially for `lineage_store.py` and `journal.py`, so workers do not overwrite unrelated changes while following the plan.

### 5. Confidence Check
**3** - The plan is workable and technically detailed, but the branch choreography and compatibility edges are still brittle enough that I would not execute it unchanged.

Raise this to 4 by fixing Task 0 branch sequencing, adding one real local-override YAML test, and adding a lint/format gate alongside pytest.
