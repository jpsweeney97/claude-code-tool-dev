# Engram Design Review Amendments

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Amend the Engram design spec (`docs/superpowers/specs/2026-03-16-engram-design.md`) to address 12 review findings (D1–D12) and 3 emerged design principles from the Codex-reviewed analysis.

**Architecture:** Pure document editing — all changes modify the existing spec. No new files. Changes grouped by spec section to minimize merge conflicts. Each task produces one commit.

**Tech Stack:** Markdown

**Source documents:**
- Spec: `docs/superpowers/specs/2026-03-16-engram-design.md`
- Handoff chain protocol: `packages/plugins/handoff/references/handoff-contract.md`
- Ticket dedup: `packages/plugins/ticket/scripts/ticket_dedup.py`

---

## File Structure

### Files Modified

| File | Change |
|------|--------|
| `docs/superpowers/specs/2026-03-16-engram-design.md` | All amendments — Sections 1, 2, 3, 5, 6, 7, 8 |

### Files Created

None.

### Files Removed

None.

---

## Chunk 1: Core Contract Amendments (D3, D5, D8)

### Task 1: Fix skill count and dedup description

Fixes D8 (skill count discrepancy) and D5 partial (dedup description mischaracterizes actual implementation).

**Files:**
- Modify: `docs/superpowers/specs/2026-03-16-engram-design.md:43` (Section 1 package structure)
- Modify: `docs/superpowers/specs/2026-03-16-engram-design.md:145` (Section 2 dedup description)

- [ ] **Step 1: Fix skill count in Section 1 package structure**

In Section 1, line 43, change:
```
├── skills/                   # User-facing skills (12 total)
```
to:
```
├── skills/                   # User-facing skills (13 total, including engram init)
```

- [ ] **Step 2: Correct dedup description in Section 2**

In Section 2 "Idempotency vs dedup" (line 145), replace:
```
- Work engine's existing duplicate detection — matches by title similarity and source overlap
```
with:
```
- Work engine's existing duplicate detection — `sha256(normalize(problem_text) + sorted(key_file_paths))` fingerprint within a 24-hour window. The fingerprint uses problem content and file paths, not titles. See `packages/plugins/ticket/scripts/ticket_dedup.py` for the canonical implementation.
```

- [ ] **Step 3: Verify consistency**

Search the spec for any other references to "title similarity" — ensure none remain that contradict the corrected description.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/2026-03-16-engram-design.md
git commit -m "docs: fix skill count and dedup description (D5, D8)"
```

---

### Task 2: Add content_sha256 to PromoteEnvelope idempotency and specify promote-meta fields

Fixes D3 (promote idempotency key prevents re-promotion after content edit).

**Files:**
- Modify: `docs/superpowers/specs/2026-03-16-engram-design.md:139` (Section 2 idempotency table)
- Modify: `docs/superpowers/specs/2026-03-16-engram-design.md:221` (Section 3 TTL table, promote-meta row)

- [ ] **Step 1: Update PromoteEnvelope idempotency material**

In Section 2 idempotency table (line 139), replace:
```
| `PromoteEnvelope` | `{source_ref.record_id, target_section}` |
```
with:
```
| `PromoteEnvelope` | `{source_ref.record_id, target_section, content_sha256}` |
```

- [ ] **Step 2: Add promote-meta field specification**

After the `PromoteEnvelope` dataclass definition (around line 129), add a new subsection:

```markdown
### promote-meta — promotion state record

Written by the Knowledge engine in Promote Step 3. Stored as a `<!-- promote-meta {...} -->` HTML comment in the knowledge entry, immediately after the `lesson-meta` comment.

```python
@dataclass(frozen=True)
class PromoteMeta:
    target_section: str           # Where in CLAUDE.md
    promoted_at: str              # ISO 8601
    promoted_content_sha256: str  # Hash of lesson content at promotion time
    transformed_text_sha256: str  # Hash of the text written to CLAUDE.md
```

**Re-promotion:** If a lesson's `content_sha256` changes after promotion, the `PromoteEnvelope` idempotency key changes (because `content_sha256` is now part of the material). The engine detects this as a stale promotion: existing `promote-meta.promoted_content_sha256` ≠ current `content_sha256`. `/promote` surfaces stale promotions for user review. `/triage` reports them as a second mismatch class alongside the Step-3-failure case.
```

- [ ] **Step 3: Verify consistency**

Confirm that the Section 5 promote operation description and the Section 3 TTL table's promote-meta row are consistent with the new field spec. The TTL table row at line 221 already says "marked with promote-meta when graduated" — this remains accurate.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/2026-03-16-engram-design.md
git commit -m "docs: add content_sha256 to promote idempotency, specify promote-meta fields (D3)"
```

---

## Chunk 2: Storage and Lifecycle (D7)

### Task 3: Clarify TTL semantics for snapshots

Fixes D7 (ambiguous "30-day active, 90-day archive" lifecycle).

**Files:**
- Modify: `docs/superpowers/specs/2026-03-16-engram-design.md:214-222` (Section 3 TTL table)

- [ ] **Step 1: Replace ambiguous TTL row**

In the Section 3 TTL table (line 216), replace:
```
| Snapshots/checkpoints | 30-day active, 90-day archive | Private root |
```
with:
```
| Snapshots/checkpoints | 90-day TTL from creation (filename timestamp). SessionStart deletes files older than 90 days. No intermediate "archive" tier — files stay in place until deletion. | Private root |
```

- [ ] **Step 2: Update SessionStart hook description to match**

In Section 6 SessionStart table (line 572), replace:
```
| Clean expired snapshots (>30d/90d) | Max 50 files | Fail-open: retry next session |
```
with:
```
| Clean expired snapshots (>90d by filename timestamp) | Max 50 files | Fail-open: retry next session |
```

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/2026-03-16-engram-design.md
git commit -m "docs: clarify snapshot TTL semantics — 90-day from creation, no archive tier (D7)"
```

---

## Chunk 3: Concurrency and Retryability (D1, D2, D5)

### Task 4: Add learnings.md write concurrency contract

Fixes D1 (concurrent append to learnings.md is not atomic for multiple writers).

**Files:**
- Modify: `docs/superpowers/specs/2026-03-16-engram-design.md:804` (Section 8 concurrent worktree staging risk)
- Modify: `docs/superpowers/specs/2026-03-16-engram-design.md:153` (Section 2, after lesson-meta contract)

- [ ] **Step 1: Add write concurrency contract after lesson-meta in Section 2**

After the paragraph ending "Entries lacking `lesson-meta` (legacy or hand-edited) are assigned `record_kind: "legacy"`..." (line 167), add:

```markdown
### learnings.md write concurrency

Two failure modes, two mitigations:

**Same-worktree (local process race):** Two concurrent operations (e.g., `/learn` and `/curate` publish) in the same worktree perform read-modify-write on `learnings.md`. The Knowledge engine's publish path acquires an advisory file lock (`fcntl.flock(LOCK_EX)`) on a lockfile (`learnings.md.lock`, same directory) before reading. Lock held through read → append → write-to-temp → `fsync` → `os.replace`. Lock released after replace completes. Timeout: 5 seconds. On timeout: fail the operation with `"learnings.md is locked by another operation"` — do not queue or retry.

**Cross-worktree (git merge territory):** Each worktree has its own filesystem view. Concurrent appends from different worktrees produce divergent file states resolved by git merge on the shared branch. The Knowledge engine does not attempt cross-worktree coordination — git's line-based merge handles append-only files well. Conflicting appends (rare — requires overlapping content at the same file position) surface as git merge conflicts for the user to resolve.

**Staging files are not affected** — staging uses content-addressed filenames (`content_sha256`-based) with atomic file creation (`O_CREAT | O_EXCL` via `os.open` or equivalent). Identical candidates from concurrent operations coalesce; non-identical candidates get distinct files.
```

- [ ] **Step 2: Update Section 8 concurrent worktree staging risk**

In Section 8 named risks table (line 804), replace the concurrent worktree staging entry:
```
| **Concurrent worktree staging** | Low | Two worktrees running `/distill` concurrently write to the same `knowledge_staging/` directory. Staging is content-addressed: identical candidates from different worktrees coalesce into a single artifact (engine uses atomic create-or-read-existing semantics via `content_sha256`-based filenames). `/curate` reviews content, not source multiplicity. `learnings.md` appends use atomic write-then-rename. Deliberate v1 trade-off — worktree sharding of staging deferred because coalescing is the correct semantic at single-developer scale. | Two worktrees distill same snapshot concurrently — duplicate staging files? |
```
with:
```
| **Concurrent worktree staging** | Medium | **Staging files:** Content-addressed filenames (`content_sha256`-based) with `O_CREAT | O_EXCL` atomic creation. Concurrent identical candidates coalesce. **Published learnings (`learnings.md`):** Same-worktree concurrency guarded by `fcntl.flock` on lockfile (see Section 2). Cross-worktree concurrency delegated to git merge. | Two worktrees distill same snapshot concurrently — duplicate staging files? Same-worktree `/learn` + `/curate` concurrent — lost append? |
```

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/2026-03-16-engram-design.md
git commit -m "docs: add learnings.md write concurrency contract with flock guard (D1)"
```

---

### Task 5: Add snapshot_ref arguments and recovery manifest

Fixes D2 (standalone skill retryability vs "never latest") and D5 (recovery manifest for /save retry).

**Files:**
- Modify: `docs/superpowers/specs/2026-03-16-engram-design.md:467-496` (Section 5, /save orchestrator + failure handling)
- Modify: `docs/superpowers/specs/2026-03-16-engram-design.md:509-514` (Section 6, skill table /defer and /distill rows)

- [ ] **Step 1: Add recovery manifest to /save orchestration in Section 5**

After the `/save` result JSON block (after line 479), add:

```markdown
**Recovery manifest:** On completion (success or partial failure), `/save` writes `save_recovery.json` to `~/.claude/engram/<repo_id>/`:

```json
{
    "snapshot_ref": "<RecordRef canonical serialization>",
    "emitted_at": "<ISO 8601>",
    "results": {
        "snapshot": {"status": "ok", "ref": "..."},
        "defer": {"status": "error", "error": "..."},
        "distill": {"status": "ok", "staged": 3}
    }
}
```

The manifest is an **operational aid, not authoritative state**. Primary records (snapshots, tickets, learnings) remain authoritative. Manifest failure degrades retry convenience but does not break standalone operations. Overwritten on each `/save` invocation (only the most recent is useful for retry). Not part of the Engram storage contract.

**Retry path:** On partial failure, retry the failed sub-operation standalone with the `snapshot_ref` from the manifest:
```
/defer --snapshot-ref <ref_from_manifest>
/distill --snapshot-ref <ref_from_manifest>
```
```

- [ ] **Step 2: Update /save failure handling table**

In the Section 5 failure handling table (line 491), replace:
```
| `/save` partial success | Per-step results show which failed | Retry failed steps standalone |
```
with:
```
| `/save` partial success | Per-step results show which failed. Recovery manifest written to `save_recovery.json`. | Retry failed steps standalone with `--snapshot-ref` from manifest. |
```

- [ ] **Step 3: Update /save orchestration rule 3**

In Section 6 `/save` orchestration rules (line 528), replace:
```
3. **Independently retryable.** Failed steps retry via standalone skills.
```
with:
```
3. **Independently retryable.** Failed steps retry via standalone skills with explicit `--snapshot-ref` from recovery manifest. "Latest" is permitted for discovery UI only, never as the semantic source of a write.
```

- [ ] **Step 4: Update /defer and /distill in skill table**

In Section 6 skill table:

Replace `/defer` row (line 509):
```
| `/defer` | Context → Work | DeferEnvelope + idempotency. |
```
with:
```
| `/defer` | Context → Work | DeferEnvelope + idempotency. Accepts `--snapshot-ref <ref>` for retry (required when called standalone after `/save` failure). |
```

Replace `/distill` row (line 514):
```
| `/distill` | Context → Knowledge | Writes to staging inbox. Idempotent per snapshot. |
```
with:
```
| `/distill` | Context → Knowledge | Writes to staging inbox. Idempotent per snapshot. Accepts `--snapshot-ref <ref>` for retry (required when called standalone after `/save` failure). |
```

- [ ] **Step 5: Add phase-scoped idempotency note**

After the Section 5 envelope invariants list (after line 465), add:

```markdown
**Phase-scoped idempotency (migration):** During Step 1 (bridge adapter), only the legacy dedup mechanism (`sha256(problem_text + key_file_paths)`) is active — envelope-level idempotency keys are not checked by the old ticket engine. Full envelope idempotency (where the Work engine checks `idempotency_key` before processing) activates in Step 3 when the new Work engine replaces the bridge. Section 5 core rules describe the Step 3+ steady state. The bridge adapter preserves legacy dedup behavior only.
```

- [ ] **Step 6: Commit**

```bash
git add docs/superpowers/specs/2026-03-16-engram-design.md
git commit -m "docs: add snapshot_ref arguments, recovery manifest, phase-scoped idempotency (D2, D5)"
```

---

## Chunk 4: Promote State Machine (D3 completion)

### Task 6: Rewrite promote operation with 3-branch validation

Completes D3 by adding the promote state machine to Section 5.

**Files:**
- Modify: `docs/superpowers/specs/2026-03-16-engram-design.md:421-437` (Section 5, promote operation)

- [ ] **Step 1: Rewrite the promote flow**

Replace the promote operation block (lines 421–437), from `**4. Promote: Knowledge → CLAUDE.md (two-step)**` through the promote recovery paragraph, with:

```markdown
**4. Promote: Knowledge → CLAUDE.md (three-step with state machine)**

```
/promote
    → query(subsystems=["knowledge"], status="knowledge:published")
    → Rank by maturity signals (age, breadth, reuse evidence) — advisory ordering only
    → User selects
    → Step 1 (engine): Knowledge engine validates promotability via 3-branch state machine:
        Branch A (no promote-meta): Eligible. Returns promotion plan.
        Branch B (promote-meta exists, promoted_content_sha256 == current content_sha256):
            Reject — already promoted. Return existing promotion details.
        Branch C (promote-meta exists, promoted_content_sha256 ≠ current content_sha256):
            Stale promotion. Return reconciliation plan: old target_section,
            old transformed_text_sha256 (for locating text in CLAUDE.md), new content.
    → Step 2 (skill): Skill writes transformed text to CLAUDE.md
        For Branch C: attempts to locate and replace old text using transformed_text_sha256
        If old text not found: surfaces manual reconcile flow to user
    → Step 3 (engine): Knowledge engine writes/updates promote-meta with current hashes
```

CLAUDE.md is an external sink, not an Engram-managed record. The Knowledge engine owns the promotion *state*. The CLAUDE.md edit is a skill-level operation. Deliberate, documented exception to the "target engine validates and writes" rule.

**Ranking is advisory, not contractual.** Maturity signals (age, breadth, reuse evidence) determine display ordering only — they are not part of the storage contract. Engine promotability validation must not depend on undocumented maturity scores.

**Promote recovery (reconciliation-based):** Step 1 validates but does not record durable state — it returns a promotion plan. Step 3 writes `promote-meta` only after the CLAUDE.md write succeeds. If Step 2 fails, no `promote-meta` exists (Branch A) or stale `promote-meta` persists (Branch C), so the lesson remains eligible for future `/promote` runs. If Step 3 fails (promote-meta write), `/triage` detects the mismatch: CLAUDE.md contains the text but the knowledge record lacks current `promote-meta`. `/triage` surfaces two mismatch classes:
- **Missing promote-meta:** CLAUDE.md has text, no promote-meta at all (Step 3 never ran)
- **Stale promote-meta:** CLAUDE.md has updated text, promote-meta has old hashes (Step 3 failed on re-promotion)
```

- [ ] **Step 2: Verify Section 6 /promote skill row is consistent**

The skill table row (line 516) says "Three-step: engine validates promotability, skill writes CLAUDE.md, engine writes promote-meta." This remains accurate with the 3-branch addition. No change needed, but verify.

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/2026-03-16-engram-design.md
git commit -m "docs: add 3-branch promote state machine with stale promotion handling (D3)"
```

---

## Chunk 5: Chain Protocol (D4)

### Task 7: Add chain protocol specification and carry forward known limitations

Fixes D4 (chain protocol unspecified but load-bearing for /load).

**Files:**
- Modify: `docs/superpowers/specs/2026-03-16-engram-design.md:507` (Section 6, after skill table)
- Modify: `docs/superpowers/specs/2026-03-16-engram-design.md:736-753` (Section 7, Step 4a)
- Modify: `docs/superpowers/specs/2026-03-16-engram-design.md:791-825` (Section 8, risks + deferred)

- [ ] **Step 1: Add chain protocol subsection to Section 6**

After the `/save` orchestration rules block (after line 528), add a new subsection:

```markdown
### Chain protocol — session lineage tracking

The chain protocol enables `resumed_from` tracking across sessions. Carried forward from the existing handoff contract (`packages/plugins/handoff/references/handoff-contract.md`) with identity changes.

**Resume (/load) — writes chain state:**
1. Archive the snapshot to `~/.claude/engram/<repo_id>/snapshots/.archive/<filename>`
2. Write archive path to `~/.claude/engram/<repo_id>/chain/<worktree_id>-<session_id>`

**Save/Quicksave (/save, /quicksave) — reads and cleans chain state:**
1. **Read:** Check `chain/<worktree_id>-<session_id>` — if exists, include path as `resumed_from` in snapshot frontmatter
2. **Write:** Write the new snapshot/checkpoint file
3. **Cleanup:** Use `trash` to remove the state file. If `trash` fails, warn but do not block — 24-hour TTL handles cleanup.

**Identity change from handoff:** Chain state files are scoped by `repo_id` (directory) and `worktree_id` (filename prefix) instead of project name and session_id alone. This provides worktree isolation — two worktrees cannot pollute each other's chain.

**Invariant:** Chain state files are created by `/load`; the next `/save` or `/quicksave` reads them to populate `resumed_from`, then attempts cleanup. A state file that persists beyond 24 hours is stale.

**Known limitations (carried forward):**

1. **Resume-crash gap:** If a session resumes a snapshot but crashes before saving a new one, the chain has a gap. The archived file is intact and can be manually re-loaded. The orphaned state file is pruned by TTL.

2. **Archive-failure chain poisoning:** If archive fails but the state file is written, `resumed_from` points to a non-existent file. Skills treat `resumed_from` as informational — do not fail on missing target. **v1 mitigation:** Archive-before-state-write ordering. The state file is only written after archive succeeds, eliminating this failure mode for new Engram sessions. Legacy chain files (pre-migration) may still exhibit this issue.

3. **State-file TTL race:** If a session spans >24 hours, the state file may be pruned before `/save` reads it. Result: missing `resumed_from`. Not data loss — the chain link is skipped.
```

- [ ] **Step 2: Add chain integrity check to Step 4a migration**

In Section 7 Step 4a (around line 741), after the data migration line, add:

```markdown
**Chain state migration:** Before copying chain state files, classify each:
- **Valid fresh** (age < 24h, target snapshot exists): Migrate to new `chain/` directory
- **Stale** (age > 24h): Skip — TTL would have pruned these
- **Dangling** (target snapshot missing): Skip — archive-failure poisoning
- **Corrupt** (unparseable): Skip and log

Only migrate valid fresh state. Do not reimport defects from the old system.
```

- [ ] **Step 3: Add chain limitations to Section 8**

In Section 8 named risks table, add a new row:

```
| **Chain protocol limitations** | Low | Three inherited limitations (resume-crash gap, archive-failure poisoning, state-file TTL race). Archive-failure resolved in v1 by archive-before-state-write ordering. Other two carried as named limitations. See Section 6 chain protocol. | Session spans >24h, save has no `resumed_from`? |
```

- [ ] **Step 4: Update Step 4a exit criteria**

In Step 4a exit criteria (line 743), add: "Chain state migration classifies and filters old state files."

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/2026-03-16-engram-design.md
git commit -m "docs: add chain protocol spec, carry forward known limitations (D4)"
```

---

## Chunk 6: Hooks and Autonomy (D6, D9)

### Task 8: Fix staging cap naming and enforcement, extend quality hook

Fixes D6 (session cap enforcement unspecified) and D9 (engram_quality excludes Edit).

**Files:**
- Modify: `docs/superpowers/specs/2026-03-16-engram-design.md:579-596` (Section 6, autonomy model)
- Modify: `docs/superpowers/specs/2026-03-16-engram-design.md:535` (Section 6, hooks table)
- Modify: `docs/superpowers/specs/2026-03-16-engram-design.md:551` (Section 6, quality validation)

- [ ] **Step 1: Rename and specify staging cap in autonomy model**

In Section 6 autonomy model table (line 585), replace:
```
| Knowledge staging | Session cap + idempotency | Dedup prevents repeated staging; cap limits volume |
```
with:
```
| Knowledge staging | Staging inbox cap + idempotency | Dedup prevents repeated staging; cumulative cap limits volume |
```

- [ ] **Step 2: Add enforcement specification**

After the config YAML block (after line 596), add:

```markdown
**Staging inbox cap enforcement:** The Knowledge engine checks the cumulative count of files in `knowledge_staging/` **before** writing new staged candidates. If `count + batch_size > knowledge_max_stages`, the entire batch is rejected (whole-batch reject for determinism — no partial staging). The rejection response includes current count, cap, and a suggestion to run `/curate` to clear the inbox.

Scope is cumulative (total files in directory), not per-session. This matches the stated risk (staging accumulation over time), not per-session agent autonomy. The engine reads `knowledge_max_stages` from `.claude/engram.local.md` at invocation time — no caching.
```

- [ ] **Step 3: Rename in config YAML**

In the config YAML (line 593), change the comment:
```yaml
  knowledge_max_stages: 10
```
to:
```yaml
  knowledge_max_stages: 10    # Cumulative files in staging inbox, not per-session
```

- [ ] **Step 4: Update staging accumulation risk in Section 8**

In Section 8 named risks (line 802), replace:
```
| **Staging accumulation** | Low | /triage reports pending. Session cap. /curate shows queue. | Staging directory file count over time. |
```
with:
```
| **Staging accumulation** | Low | /triage reports pending. Cumulative staging inbox cap (default 10). /curate shows queue. Knowledge engine rejects whole batch when cap exceeded. | Staging directory file count over time. |
```

- [ ] **Step 5: Extend engram_quality to cover Edit tool**

In Section 6 hooks table (line 535), replace:
```
| `engram_quality` | PostToolUse (Write) | 2nd | Snapshot quality checks (payload-based, Write tool only) | **Warn** |
```
with:
```
| `engram_quality` | PostToolUse (Write, Edit) | 2nd | Snapshot quality checks — Write: reads `tool_input.content` from payload. Edit: reads file from disk after edit. Both: only for snapshot-owned paths. | **Warn** |
```

- [ ] **Step 6: Update quality validation description**

In Section 6 quality validation paragraph (line 551), replace:
```
**Quality validation:** `engram_quality` (PostToolUse) validates snapshot content quality for Write tool calls only — it reads `tool_input.content` from the write payload, not from disk. It does **not** detect Bash-mediated writes to protected paths. Bash bypass of `engram_guard` remains an admitted gap with best-effort pre-blocking only (see Section 8).
```
with:
```
**Quality validation:** `engram_quality` (PostToolUse) validates snapshot content quality for Write and Edit tool calls on snapshot-owned paths. For Write: reads `tool_input.content` from the payload. For Edit: reads the file from disk after the edit completes (post-state validation). This is advisory quality lint, not trust enforcement — the small race between write completion and readback is acceptable for warnings. It does **not** detect Bash-mediated writes to protected paths. Bash bypass of `engram_guard` remains an admitted gap with best-effort pre-blocking only (see Section 8).
```

- [ ] **Step 7: Commit**

```bash
git add docs/superpowers/specs/2026-03-16-engram-design.md
git commit -m "docs: specify staging inbox cap enforcement, extend quality hook to Edit (D6, D9)"
```

---

## Chunk 7: Migration Amendments (D10, D11)

### Task 9: Add bridge contract test and migration manifest

Fixes D10 (bridge adapter type dependency) and D11 (private root migration partial failure).

**Files:**
- Modify: `docs/superpowers/specs/2026-03-16-engram-design.md:659-685` (Section 7, Step 1)
- Modify: `docs/superpowers/specs/2026-03-16-engram-design.md:736-753` (Section 7, Step 4a)

- [ ] **Step 1: Add bridge contract test to Step 1**

After the Step 1 cross-step dependency warning (line 683), add:

```markdown
**Bridge compatibility test:** A behavioral contract test must accompany the bridge adapter. The test:
1. Constructs a representative `DeferEnvelope` with full `EnvelopeHeader`
2. Runs it through the bridge adapter's conversion logic
3. Asserts the output is valid legacy `DeferredWorkEnvelope` JSON
4. Verifies `SourceResolver` field mapping (`source.type`, `source.ref`, `source.session`)

This test runs in CI across Steps 1–3. If type changes to `DeferEnvelope` or `EnvelopeHeader` break the bridge, this test fails fast — replacing the process-level "do not modify" warning with a structural guard. The test is deleted in Step 5 cleanup alongside the bridge adapter.
```

- [ ] **Step 2: Update Step 1 exit criteria**

In Step 1 exit criteria (line 685), append: "Bridge compatibility test passes."

- [ ] **Step 3: Add migration manifest to Step 4a**

After the Step 4a data migration line (line 741), add:

```markdown
**Migration manifest:** The migration script writes `migration_report.json` to `~/.claude/engram/<repo_id>/`:

```json
{
    "migrated_at": "<ISO 8601>",
    "source_root": "~/.claude/handoffs/<project>/",
    "target_root": "~/.claude/engram/<repo_id>/snapshots/",
    "results": {
        "copied": ["file1.md", "file2.md"],
        "skipped_exists": ["file3.md"],
        "skipped_corrupt": ["file4.md"],
        "skipped_unreadable": ["file5.md"],
        "needs_manual_mapping": ["ambiguous-project/"],
        "conflicts": [{"file": "file6.md", "reason": "content mismatch at destination"}]
    }
}
```

**Fail-closed, non-interactive:**
- Ambiguous project name → repo_id mappings: skip, record as `needs_manual_mapping`
- Unreadable source files: skip, record as `skipped_unreadable`
- Existing destination with non-matching content: skip, record as `conflicts`
- Successful copy: verify destination parses through Context reader before recording as `copied`

The manifest is an **operational aid** (see design principle in Section 8). Re-running the migration is idempotent: `skipped_exists` entries are files that already exist with matching content. Non-interactive design enables deterministic reruns without human attention.
```

- [ ] **Step 4: Update Step 4a exit criteria**

In Step 4a exit criteria (line 743), add: "All copied handoffs parse successfully through the Context reader. Migration manifest written with no `skipped_corrupt` entries for newly copied files."

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/2026-03-16-engram-design.md
git commit -m "docs: add bridge contract test and migration manifest (D10, D11)"
```

---

## Chunk 8: Risks and Design Principles (D12, emerged)

### Task 10: Elevate Bash enforcement risk, add design principles

Fixes D12 (Bash enforcement gap severity and invariant language) and adds 3 emerged design principles from the Codex dialogue.

**Files:**
- Modify: `docs/superpowers/specs/2026-03-16-engram-design.md:800` (Section 8, Bash enforcement risk row)
- Modify: `docs/superpowers/specs/2026-03-16-engram-design.md:549` (Section 6, enforcement scope)
- Add new subsection to Section 8

- [ ] **Step 1: Elevate Bash enforcement risk to High**

In Section 8 named risks table (line 800), replace:
```
| **Bash enforcement gap** | Medium | `engram_guard` reliably blocks Write/Edit but Bash interception is best-effort. No post-hoc detection — `engram_quality` validates Write payloads only, not disk state. | Bash write to `engram/work/` bypasses guard? |
```
with:
```
| **Bash enforcement gap** | High | **Bounded guarantee:** Write/Edit direct mutations to protected paths are reliably blocked. Authorized engine Bash invocations are supported via trust injection. Arbitrary Bash writes to protected paths may bypass the guard and are not guaranteed detectable. Records created via Bash bypass have no trust triple, no audit trail, and no provenance guarantee. Post-hoc drift scan deferred (see Deferred decisions). | Bash write to `engram/work/` bypasses guard? Created ticket has no `.audit/` entry? |
```

- [ ] **Step 2: Weaken invariant language in Section 6**

In Section 6 enforcement scope (line 549), replace:
```
**Enforcement scope:** Write and Edit mutations are reliably blocked. Bash interception is best-effort — detecting arbitrary shell commands that write to protected paths (`echo >`, `cp`, `tee`, etc.) is unreliable via PreToolUse input parsing. The guard catches direct `python3 engine_*.py` patterns reliably; other Bash writes are caught on a best-effort basis. See Section 8 for the named risk.
```
with:
```
**Enforcement scope (bounded guarantee):** Write and Edit mutations to protected paths are reliably blocked. Authorized engine Bash invocations (`python3 engine_*.py` patterns) are detected and supported with trust injection. Arbitrary Bash writes (`echo >`, `cp`, `tee`, etc.) are caught on a best-effort basis only — PreToolUse input parsing cannot reliably detect all shell write patterns. This is an honest boundary, not a gap to close: the design provides reliable enforcement for the tools Claude uses natively (Write, Edit) and for the authorized engine invocation pattern, but does not claim to prevent all possible filesystem mutations. See Section 8 for severity assessment and detection strategy.
```

- [ ] **Step 3: Add design principles subsection to Section 8**

Before the "Success criteria" subsection (before line 827), add:

```markdown
### Design principles

Three cross-cutting principles emerged from the design review process. These are not invariants (they have no enforcement mechanism) but guide implementation decisions across subsystems.

**1. Auxiliary state authority:** Recovery manifests (`save_recovery.json`, `migration_report.json`) and reconciliation metadata (`promote-meta`) are operational aids only. Primary records — snapshots, tickets, learnings, chain state files — remain authoritative. Manifest failure degrades convenience (retry requires manual snapshot_ref lookup) but does not break standalone operations. Use distinct naming for each manifest to prevent shadow-authority confusion.

**2. Pre/post-write validation layering:** Pre-write or pre-dispatch validation for hard invariants (trust triples, idempotency keys, promotion state machine). Post-write validation for advisory quality checks only (`engram_quality`). PostToolUse hooks must not become enforcement boundaries — the race between write completion and validation readback is acceptable for warnings, not for trust authorization.

**3. Chain integrity at migration boundaries:** When migrating state from an old system (chain files, staging candidates), classify each artifact's health before copying. Only migrate valid, fresh state. Do not reimport known defects (stale chain files, poisoned references) from the predecessor system.
```

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/2026-03-16-engram-design.md
git commit -m "docs: elevate Bash enforcement to High, add design principles (D12, emerged)"
```

---

## Verification

### Task 11: Full-document consistency check

- [ ] **Step 1: Verify all D-findings addressed**

Check each finding has corresponding spec text:

| Finding | Section(s) modified | Task |
|---------|---------------------|------|
| D1 | Section 2 (write concurrency), Section 8 (risk row) | Task 4 |
| D2 | Section 5 (recovery manifest, snapshot_ref), Section 6 (skill table, orchestration rules) | Task 5 |
| D3 | Section 2 (idempotency table, promote-meta), Section 5 (promote operation) | Tasks 2, 6 |
| D4 | Section 6 (chain protocol), Section 7 (chain integrity), Section 8 (risk row) | Task 7 |
| D5 | Section 2 (dedup description), Section 5 (recovery manifest, phase-scoped note) | Tasks 1, 5 |
| D6 | Section 6 (autonomy model, config), Section 8 (staging risk) | Task 8 |
| D7 | Section 3 (TTL table), Section 6 (SessionStart) | Task 3 |
| D8 | Section 1 (skill count) | Task 1 |
| D9 | Section 6 (hooks table, quality description) | Task 8 |
| D10 | Section 7 (Step 1 bridge test) | Task 9 |
| D11 | Section 7 (Step 4a migration manifest) | Task 9 |
| D12 | Section 6 (enforcement scope), Section 8 (risk row, design principles) | Task 10 |

- [ ] **Step 2: Search for internal contradictions**

Grep the amended spec for:
- "12 total" (should be gone — replaced by "13 total")
- "title similarity" (should be gone — replaced by sha256 description)
- "30-day active" (should be gone — replaced by 90-day TTL)
- "atomic write-then-rename" in the concurrent worktree risk (should be replaced by flock description)
- "Session cap" in autonomy table (should be "Staging inbox cap")
- "Write tool only" in quality hook (should be "Write, Edit")

- [ ] **Step 3: Commit any fixups**

```bash
git add docs/superpowers/specs/2026-03-16-engram-design.md
git commit -m "docs: consistency fixups from design review verification"
```

(Skip this commit if no fixups needed.)
