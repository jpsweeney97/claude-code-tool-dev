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
| 2 | Working tree clean (no unstaged changes) | `worktree_dirty` | No invisible local edits that could interact with the applied diff |
| 3 | Index clean (no staged changes) | `index_dirty` | No pending staged work that could be disrupted |
| 4 | Artifact hash matches reviewed artifact | `artifact_hash_mismatch` | The exact artifact Claude reviewed is what gets applied |
| 5 | Job status is `completed` | `job_not_completed` | Only completed jobs can be promoted |

### HEAD Match

The primary workspace's `HEAD` must exactly equal the `base_commit` recorded when the delegation job was created. Any divergence — local commits, pulls, rebases — invalidates the delegation's assumptions about the codebase state.

v1 does not support three-way merge. If HEAD has drifted, the user must either reset to `base_commit`, re-delegate from the current HEAD, or manually apply the diff.

### Clean Workspace

Both the working tree and the index must be clean. Staged changes are just as invisible to the promotion diff as unstaged ones — either can interact badly with applied changes.

### Artifact Hash Integrity

The artifact hash is the load-bearing integrity guarantee for the entire delegation flow.

- **At review time:** When Claude reviews delegation results via `codex.delegate.poll`, the control plane computes a hash of the complete artifact set (diff, changed files, test results).
- **At promotion time:** The control plane recomputes the hash and compares it to the reviewed hash stored in the [DelegationJob](contracts.md#delegationjob).
- **On mismatch:** Promotion is rejected with `artifact_hash_mismatch`.

This makes the delegation flow tamper-evident: any modification to the artifact set between review and promotion is detected.

## Promotion State Machine

```
pending ──→ prechecks_passed ──→ applied ──→ verified
  │              │                  │
  │              │                  └──→ rollback_needed ──→ rolled_back
  │              │
  │              └──→ prechecks_failed ──→ pending (retry)
  │
  └──→ discarded
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
| `prechecks_passed` | `applied` | `git apply` succeeds | Diff applied; journal entry written |
| `applied` | `verified` | Post-apply verification passes | Audit event emitted; worktree cleanup scheduled |
| `applied` | `rollback_needed` | Post-apply verification fails | — |
| `rollback_needed` | `rolled_back` | Workspace restored | Audit event emitted; worktree retained for inspection |
| `prechecks_failed` | `pending` | User resolves blocking condition and retries | — |

### Re-Entry

A `prechecks_failed` promotion can be retried. The user resolves the blocking condition (e.g., stashes staged changes, resets HEAD to match `base_commit`) and calls `codex.delegate.promote` again. The state machine re-enters at `pending` and re-evaluates all preconditions.

## Rollback Semantics

If post-application verification fails:

1. Applied changes are reverted (`git checkout -- .` for tracked files; untracked files produced by the diff are removed).
2. The worktree and artifacts are retained for inspection (retention governed by [recovery-and-journal.md §Retention Defaults](recovery-and-journal.md#retention-defaults)).
3. An [audit event](contracts.md#auditevent) is emitted with `action: promote` and `decision: deny`.
4. Claude receives the verification failure details and can re-delegate, manually apply, or discard.

## Workspace Effects

A successful promotion changes HEAD in the primary workspace. This has implications beyond the promotion itself:

- The [advisory runtime](advisory-runtime-policy.md) may hold stale context that predates the new HEAD. See [recovery-and-journal.md §Advisory-Delegation Race](recovery-and-journal.md#advisory-delegation-race) for the coherence implications and recommended signaling approach.
