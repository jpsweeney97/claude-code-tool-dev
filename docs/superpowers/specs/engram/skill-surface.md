---
module: skill-surface
status: active
normative: true
authority: skill-contract
---

# Skill Surface

## Skills (13 Total)

| Skill | Subsystem | Change from Today |
|---|---|---|
| `/save` | Context (orchestrator) | Orchestrates [defer + distill](operations.md#save-as-session-orchestrator). Embeds [orchestration intent](types.md#snapshot-orchestration-intent) in snapshot frontmatter. Per-step results. `--no-defer`, `--no-distill`. |
| `/load` | Context | Chain protocol uses `repo_id` + `worktree_id`. |
| `/quicksave` | Context | Lightweight: 5 sections, no defer, no distill. Writes checkpoint directly via Write tool (not through engine Bash) — see [direct-write path authorization](enforcement.md#direct-write-path-authorization). Checkpoint writes trigger `engram_quality` advisory validation (see [enforcement.md §Quality Validation](enforcement.md#quality-validation)). |
| `/defer` | Context -> Work | [DeferEnvelope](types.md#deferenvelope--context-to-work) + idempotency. Accepts `--snapshot-ref <ref>` for retry (required when called standalone after `/save` failure). |
| `/search` | Cross-subsystem | Queries all subsystems via [unified search](operations.md#unified-search). Results grouped by subsystem. |
| `/ticket` | Work | Unchanged API. Storage at `engram/work/`. |
| `/triage` | Cross-subsystem | Merged from ticket-triage + handoff triage. Reports staged candidates + orphans. |
| `/learn` | Knowledge | Invokes the Knowledge engine publish entrypoint to append to `engram/knowledge/learnings.md` with [lesson-meta](types.md#knowledge-entry-format--lesson-meta-contract). Routes through `engram_guard` trust injection (not a direct Write tool call). Dedup via `content_sha256` against published entries. |
| `/distill` | Context -> Knowledge | Writes to staging inbox. Idempotent per snapshot. Accepts `--snapshot-ref <ref>` for retry (required when called standalone after `/save` failure). |
| `/curate` | Knowledge | **New.** Reviews staged candidates, publishes to `engram/knowledge/`. See [curate mechanics](operations.md#distill-context-to-knowledge-staged). |
| `/promote` | Knowledge -> CLAUDE.md | [Three-step state machine](operations.md#promote-knowledge-to-claudemd): engine validates promotability, skill writes CLAUDE.md, engine writes promote-meta. |
| `/timeline` | Cross-subsystem | **New.** [Session reconstruction](operations.md#session-timeline) with ledger-backed/inferred labels. |
| `engram init` | System | **New.** Bootstrap: generates `.engram-id` (UUIDv4), writes to repo root, stages for commit. Prints exact `git commit` command for user to run. Idempotent — no-ops if `.engram-id` already exists. Supports `--force` to overwrite a malformed `.engram-id` (see [delivery.md VR-0B-1](delivery.md#step-0b-bootstrap-and-identity)). |

**Consolidated:** `/ticket-triage` + handoff `/triage` merged into `/triage`.

**`/curate` naming rationale:** "Publish" collides with too many concepts. "Curate" is distinctive, implies review/selection, and pairs with the knowledge lifecycle: learn -> distill -> curate -> promote.

## /save Orchestration Rules

Three rules constrain `/save` to prevent [God Skill](decisions.md#named-risks) drift:

1. **Shared entrypoint delegation.** Each `/save` sub-operation must delegate to the same public entrypoint function as its standalone counterpart (`/defer`, `/distill`). The entrypoint is the shared programmatic seam — `/save` is a thin wrapper that calls it, not a reimplementation.
2. **No hidden behaviors.** Every sub-operation visible in per-step results.
3. **Independently retryable.** Failed steps retry via standalone skills with explicit `--snapshot-ref` from [recovery manifest](operations.md#recovery-manifest). "Latest" is permitted for discovery UI only, never as the semantic source of a write.

**Structural verification:** `/save` sub-operations **must** call the same public entrypoint functions as their standalone counterparts. Verified by automated delegation test — see [cross-cutting verification](delivery.md#cross-cutting-verification) for test specification.

## Chain Protocol — Session Lineage Tracking

Enables `resumed_from` tracking across sessions. Carried forward from the existing handoff contract with identity changes.

### Resume (/load) — Writes Chain State

1. Archive the snapshot to `~/.claude/engram/<repo_id>/snapshots/.archive/<filename>`
2. Write archive path to `~/.claude/engram/<repo_id>/chain/<worktree_id>-<session_id>`

**Precondition:** Chain state file creation requires a non-None `session_id`. If `session_id` cannot be resolved at `/load` time, the chain file is not written and `resumed_from` is omitted from the next snapshot. A diagnostic warning is logged.

### Save/Quicksave — Reads and Cleans Chain State

1. **Read:** Check `chain/<worktree_id>-<session_id>` — if exists, include path as `resumed_from` in snapshot frontmatter
2. **Write:** Write the new snapshot/checkpoint file
3. **Cleanup:** Use `trash` to remove the state file. If `trash` fails, warn but do not block — 24-hour TTL handles cleanup.

### Identity Change from Handoff

Chain state files are scoped by `repo_id` (directory) and `worktree_id` (filename prefix) instead of project name and `session_id` alone. This provides worktree isolation — two worktrees cannot pollute each other's chain.

**Invariant:** Chain state files are created by `/load`; the next `/save` or `/quicksave` reads them to populate `resumed_from`, then attempts cleanup. A state file that persists beyond 24 hours is stale.

### Chain Protocol Known Limitations

Three inherited limitations, carried forward with documentation:

1. **Resume-crash gap:** If a session resumes a snapshot but crashes before saving a new one, the chain has a gap. The archived file is intact and can be manually re-loaded. The orphaned state file is pruned by TTL.

2. **Archive-failure chain poisoning:** If archive fails but the state file is written, `resumed_from` points to a non-existent file. Skills treat `resumed_from` as informational — do not fail on missing target. **v1 mitigation:** Archive-before-state-write ordering eliminates this failure mode for new Engram sessions. Legacy chain files (pre-migration) may still exhibit this issue.

3. **State-file TTL race:** If a session spans >24 hours, the state file may be pruned before `/save` reads it. Result: missing `resumed_from`. Not data loss — the chain link is skipped.

## Trigger Differentiation

| Collision Pair | Differentiation |
|---|---|
| `/save` vs `/quicksave` | Full session wrap-up vs. quick checkpoint |
| `/triage` vs `/ticket list` | Cross-subsystem health dashboard vs. list my tickets |
| `/search` vs `/ticket query` | Find across everything vs. find ticket by ID prefix |
| `/distill` vs `/learn` | Bulk extraction from snapshot (staged as `DistillCandidate` files) vs. capture one insight manually (publishes to `learnings.md` via the Knowledge engine entrypoint with [lesson-meta](types.md#knowledge-entry-format--lesson-meta-contract); not a direct Write tool call — routes through `engram_guard` trust injection). Both dedup via `content_sha256`. `/learn` applies lesson-meta directly on write; for the distill path, lesson-meta is applied by `/curate` at publication time. |
| `/curate` vs `/promote` | Review staged candidates vs. graduate published knowledge to CLAUDE.md |
