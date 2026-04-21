---
module: promotion-protocol
status: active
normative: true
authority: promotion-contract
---

# Promotion Protocol

The promotion protocol governs how delegation results move from an isolated worktree back to the user's primary workspace. Promotion is the highest-risk boundary in the system — the point where isolated safety must translate into workspace-level correctness.

## Preconditions

All preconditions must pass before promotion begins. Each has a specific [typed rejection](contracts.md#promotion-rejection) returned on failure.

| # | Precondition | Rejection Reason | Rationale |
|---|---|---|---|
| 1 | `HEAD == base_commit` | `head_mismatch` | Primary workspace has not diverged since delegation started |
| 2 | Working tree clean (`git status --porcelain` empty, including untracked files) | `worktree_dirty` | No invisible local edits or untracked files that could interact with the applied diff |
| 3 | Index clean (no staged changes) | `index_dirty` | No pending staged work that could be disrupted |
| 4 | Job status is `completed` | `job_not_completed` | Only completed jobs can be promoted |
| 5 | Reviewed artifact hash exists | `job_not_reviewed` | Job must have been reviewed via `codex.delegate.poll` before promotion |
| 6 | Artifact hash matches reviewed artifact | `artifact_hash_mismatch` | The exact artifact Claude reviewed is what gets applied |

### HEAD Match

The primary workspace's `HEAD` must exactly equal the `base_commit` recorded when the delegation job was created. Any divergence — local commits, pulls, rebases — invalidates the delegation's assumptions about the codebase state.

v1 does not support three-way merge. If HEAD has drifted, the user must either reset to `base_commit`, re-delegate from the current HEAD, or manually apply the diff.

### Clean Workspace

Both the working tree and the index must be clean. v1 treats **any** non-empty `git status --porcelain` output as blocking, including `??` untracked files. Staged changes are just as invisible to the promotion diff as unstaged ones, and pre-existing untracked files make apply/rollback semantics ambiguous.

### Artifact Hash Integrity

The artifact hash is the load-bearing integrity guarantee for the entire delegation flow.

#### Materialization

On first `codex.delegate.poll` for a `completed` job with no reviewed snapshot, the control plane materializes the [Artifact Inspection Snapshot](contracts.md#artifact-inspection-snapshot):

1. Computes the canonical review set from the job's `base_commit` and `worktree_path`.
2. Persists the inspection artifacts to durable storage and records `artifact_paths` on the [DelegationJob](contracts.md#delegationjob).
3. Computes the `artifact_hash` and records it on the job.
4. Returns the snapshot with `artifact_hash` populated.

Subsequent polls return the persisted snapshot and do not recompute it. This makes the operation lazy and idempotent — retries are harmless, and there are no caller-visible "first reviewer" semantics.

#### Canonical Review Set

The review set must include at least:

- Full diff against `base_commit`
- Changed-files manifest
- Test-results record

Additional artifacts (e.g., unresolved-risks summary) are allowed. If included in the review snapshot, they must also participate in promote-time recomputation.

#### Hash Recipe

The hash is computed over the persisted artifact files listed in `artifact_paths`, sorted by relative path. For each file: `relative_path + NUL + file_bytes`. The concatenation is hashed with SHA-256. Without a canonical ordering and separator rule, the integrity promise is underspecified.

#### Promotion Verification

- **At promotion time:** `codex.delegate.promote` regenerates the canonical review set from the current worktree state (same `base_commit` + `worktree_path` inputs as poll-time materialization), applies the same hash recipe to that regenerated set, and compares the result to the stored reviewed hash on the [DelegationJob](contracts.md#delegationjob). Promote does not hash the persisted snapshot files — it independently regenerates and hashes, so any post-review worktree modification is detected.
- **On missing hash:** Promotion is rejected with `job_not_reviewed`. The caller must poll the job to trigger materialization before retrying.
- **On mismatch:** Promotion is rejected with `artifact_hash_mismatch`. Any modification to the worktree or artifact set between review and promotion is detected.

This makes the delegation flow tamper-evident across the review-to-promotion boundary.

#### Post-Apply Verification

After `git apply` succeeds in the primary workspace, promote verifies the applyable subset of the reviewed artifact set:

1. Recompute `git diff --binary` against `base_commit` in the primary workspace and compare it byte-for-byte to the reviewed `full.diff`.
2. Recompute the changed-file set in the primary workspace and compare it to the reviewed `changed-files.json`.
3. Confirm `git status --porcelain` shows only the expected tracked modifications from the reviewed artifact set and no unexpected entries.

Promote does **not** recompute the full reviewed artifact hash in the primary workspace. The canonical review set includes execution-side inspection data such as the test-results record, which is not applied into the primary workspace.

## Promotion State Machine

```
pending ──→ prechecks_passed ──→ applied ──→ verified
  │              │                  │
  │              │                  └──→ rollback_needed ──→ rolled_back
  │              │
  │              └──→ prechecks_failed ──→ pending (retry)
  │                                   │
  └───────────────────────────────────┴──→ discarded
```

### States

| State | Meaning |
|---|---|
| `pending` | Job completed; awaiting promotion decision |
| `prechecks_passed` | All [preconditions](#preconditions) verified |
| `applied` | Diff applied to primary workspace |
| `verified` | Post-application verification succeeded |
| `prechecks_failed` | One or more preconditions failed; [typed rejection](contracts.md#promotion-rejection) returned |
| `rollback_needed` | Post-application verification failed |
| `rolled_back` | Applied changes reverted; workspace restored to pre-promotion state |
| `discarded` | User/Claude chose not to promote; job artifacts retained per [retention policy](recovery-and-journal.md#retention-defaults) |

### Transitions

| From | To | Trigger | Side Effects |
|---|---|---|---|
| `pending` | `prechecks_passed` | All preconditions pass | [Journal entry](recovery-and-journal.md#operation-journal) written |
| `pending` | `prechecks_failed` | Any precondition fails | Typed rejection returned; journal entry written |
| `pending` | `discarded` | User/Claude chooses to discard | [Audit event](contracts.md#auditevent) emitted |
| `prechecks_failed` | `discarded` | User/Claude chooses not to retry while no workspace mutation has occurred | [Audit event](contracts.md#auditevent) emitted |
| `prechecks_passed` | `applied` | `git apply` succeeds | Diff applied; journal entry written |
| `applied` | `verified` | Post-apply verification passes | Audit event emitted; worktree cleanup scheduled; advisory coherence callback may mark stale context |
| `applied` | `rollback_needed` | Post-apply verification fails | — |
| `rollback_needed` | `rolled_back` | Workspace restored | Audit event emitted; worktree retained for inspection |
| `prechecks_failed` | `pending` | User resolves blocking condition and retries | — |

### Re-Entry

A `prechecks_failed` promotion can be retried. The user resolves the blocking condition (e.g., stashes staged changes, resets HEAD to match `base_commit`) and calls `codex.delegate.promote` again. The state machine re-enters at `pending` and re-evaluates all preconditions.

`prechecks_passed` is not a caller-facing steady state. It exists to support crash recovery between precheck success and apply. If recovery finds `prechecks_passed` with no matching promotion journal `dispatched` phase, the state normalizes back to `pending` before any retry or discard.

## Rollback Semantics

If post-application verification fails:

1. Applied changes are reverted (`git checkout -- .` for tracked files; untracked files produced by the diff are removed).
2. The worktree and artifacts are retained for inspection (retention governed by [recovery-and-journal.md §Retention Defaults](recovery-and-journal.md#retention-defaults)).
3. An [audit event](contracts.md#auditevent) is emitted with `action: promote` and `decision: deny`.
4. Claude receives the verification failure details and can re-delegate, manually apply, or discard.

## Discard Semantics

`codex.delegate.discard` is a separate low-risk operation from promotion.

- **Allowed states:** `promotion_state in {pending, prechecks_failed}`, or `status in {failed, unknown}` with `promotion_state is None` (pre-mutation)
- **Rejected states:** `prechecks_passed`, `applied`, `verified`, `rollback_needed`, `rolled_back`, and `discarded`
- **Rationale:** discard is only valid before any primary-workspace mutation has occurred. Failed/unknown jobs with null promotion state are pre-mutation by definition and must be discardable to prevent permanently blocking new delegations via the widened busy gate.

Discard emits an [audit event](contracts.md#auditevent) with `action: discard`, transitions the job to `promotion_state="discarded"`, and schedules the execution worktree for normal discard-time cleanup.

## Workspace Effects

A successful promotion changes primary-workspace content without creating a commit. This has implications beyond the promotion itself:

- The [advisory runtime](advisory-runtime-policy.md) may hold stale context that predates the newly applied workspace content. See [recovery-and-journal.md §Advisory-Delegation Race](recovery-and-journal.md#advisory-delegation-race) for the coherence implications and recommended signaling approach.
