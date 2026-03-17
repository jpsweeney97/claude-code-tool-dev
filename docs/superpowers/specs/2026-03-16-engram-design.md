# Engram: A Federated Persistence Layer for Claude Code

**Date:** 2026-03-16
**Authors:** JP + Claude + Codex (7-turn collaborative dialogue)

---

## Overview

Engram is a federated persistence and observability layer for Claude Code. It consolidates three existing plugins — handoff (session state), ticket (work tracking), and the learning pipeline (knowledge capture) — into a single marketplace plugin with shared identity, indexing, and cross-subsystem coordination.

**The core insight:** Three independently-built systems solve the same underlying problem — Claude Code has no persistent state. Each session starts from zero. The solution isn't three plugins; it's one stateful layer with three concerns.

**Three subsystems, one system:**

| Subsystem | Concern | Unit | Formerly |
|-----------|---------|------|----------|
| **Context** | Session state at boundaries | Snapshot | Handoff plugin |
| **Work** | Task lifecycle and project tracking | Ticket | Ticket plugin |
| **Knowledge** | Durable insights and patterns | Lesson | Learning pipeline |

---

## Section 1: System Identity and Core Invariant

**Engram** provides shared identity, indexing, and cross-subsystem coordination — but it **never owns domain data**. Each subsystem (Context, Work, Knowledge) remains authoritative for its own records.

**The load-bearing invariant:** Engram indexes but does not mutate. All writes flow through subsystem engines. Engram reads the results.

**Anti-pattern (Shadow Authority):** Any feature that makes Engram a second source of truth for data that a subsystem already owns is a design violation. Test every new capability against: "could a user get a different answer by querying the subsystem directly vs. querying Engram?"

**Package structure:**

```
packages/plugins/engram/
├── .claude-plugin/
│   └── plugin.json          # Marketplace manifest
├── engram_core/              # Shared library (identity, types, indexing)
│   ├── identity.py           # repo_id, worktree_id resolution
│   ├── types.py              # RecordRef, RecordMeta, contracts
│   ├── reader_protocol.py    # NativeReader protocol definition only
│   └── query.py              # Discovery + query engine
├── skills/                   # User-facing skills (13 total, including engram init)
├── hooks/                    # PreToolUse/PostToolUse/SessionStart hooks
├── scripts/                  # Subsystem engines
│   ├── context/              # Context engine + context_reader.py
│   ├── work/                 # Work engine + work_reader.py
│   └── knowledge/            # Knowledge engine + knowledge_reader.py
└── pyproject.toml
```

`engram_core/` lives inside the plugin, not as a separate package. One plugin install gets everything. Extract later if external consumers emerge.

---

## Section 2: Core Types

### RecordRef — lookup key (immutable after creation)

```python
@dataclass(frozen=True)
class RecordRef:
    repo_id: str          # UUIDv4, stored in .engram-id at repo root
    subsystem: str        # "context" | "work" | "knowledge"
    record_kind: str      # Subsystem-specific: "snapshot", "checkpoint", "ticket", "lesson", etc.
    record_id: str        # Subsystem-native ID (handoff filename, T-YYYYMMDD-NN, lesson_id)
```

### RecordMeta — provenance and observability (eager on write, optional for read)

```python
@dataclass(frozen=True)
class RecordMeta:
    worktree_id: str | None    # Disambiguates concurrent worktrees
    session_id: str | None     # Claude session UUID
    schema_version: str        # Contract version (e.g., "1.0")
    visibility: str            # "private" (user-home) | "shared" (repo-local)
```

### Identity resolution

**repo_id:**
- On first use: generate UUIDv4, write to `.engram-id` at repo root, commit it
- On subsequent use: read from `.engram-id`
- Stable across clones and renames (because it's committed). Forks inherit the same `repo_id` — see Section 8 for the fork-on-same-machine risk

**worktree_id:**
- Derived from `git rev-parse --git-dir` — each worktree has a unique `.git` path
- Hashed to a short stable ID for filesystem use
- Context records are isolated per worktree by default

### Cross-subsystem contracts — typed envelopes

All cross-subsystem writes use typed envelopes with a common header:

```python
@dataclass(frozen=True)
class EnvelopeHeader:
    envelope_version: str          # "1.0" — target rejects unknown versions explicitly
    source_ref: RecordRef          # Pinned at creation. Never "latest."
    idempotency_key: str           # sha256(canonical_json(idempotency_material)) — see below
    emitted_at: str                # ISO 8601

@dataclass(frozen=True)
class DeferEnvelope:               # Context → Work
    header: EnvelopeHeader
    title: str
    problem: str
    context: str | None
    key_file_paths: list[str]

@dataclass(frozen=True)
class DistillEnvelope:             # Context → Knowledge (staging)
    header: EnvelopeHeader
    candidates: list[DistillCandidate]

@dataclass(frozen=True)
class DistillCandidate:
    content: str
    durability: str                # "likely_durable" | "likely_ephemeral" | "unknown"
    source_section: str            # Which snapshot section it came from
    content_sha256: str            # For dedup

@dataclass(frozen=True)
class PromoteEnvelope:             # Knowledge → CLAUDE.md (intent record)
    header: EnvelopeHeader
    target_section: str            # Where in CLAUDE.md
    transformed_text: str          # Prescriptive prose, ready to insert
```

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

### Idempotency vs dedup — two distinct mechanisms

**Idempotency** answers: "is this the same operation being retried?" The `idempotency_key` in `EnvelopeHeader` is computed from `canonical_json(idempotency_material)` where the material is envelope-type-specific:

| Envelope | `idempotency_material` |
|----------|----------------------|
| `DeferEnvelope` | `{source_ref.record_id, title, problem}` |
| `DistillEnvelope` | `{source_ref.record_id, sorted([{content_sha256, source_section, durability}, ...])}` |
| `PromoteEnvelope` | `{source_ref.record_id, target_section, content_sha256}` |

`canonical_json()` sorts keys and normalizes whitespace. Same material → same key → target engine returns existing result without side effects.

**Dedup** answers: "is this content semantically identical to existing content?" Uses content fingerprints at the record level:
- `DistillCandidate.content_sha256` — deduplicates staged/published knowledge entries by content
- Work engine's existing duplicate detection — `sha256(normalize(problem_text) + sorted(key_file_paths))` fingerprint within a 24-hour window. The fingerprint uses problem content and file paths, not titles. See `packages/plugins/ticket/scripts/ticket_dedup.py` for the canonical implementation.

These are independent in purpose and enforcement stage, though not necessarily disjoint in fields: an idempotent retry of a distill operation (same `idempotency_key`) is caught at the envelope level before dedup is ever checked. A genuinely new operation with coincidentally identical content is caught by dedup, not idempotency. The `DistillEnvelope` idempotency material includes per-candidate fingerprints to ensure that re-running extraction with improved logic on the same snapshot produces a distinct key when candidate content changes.

**Format preservation:** Each subsystem keeps its native format. Tickets keep fenced YAML. Handoffs keep `---` frontmatter. Learnings use heading-delimited blocks with `lesson-meta` comments (see below). NativeReaders parse each format without requiring unification.

### Knowledge entry format — `lesson-meta` contract

All published knowledge entries in `engram/knowledge/learnings.md` use a uniform format regardless of producer (`/learn` or `/curate`):

```markdown
### YYYY-MM-DD Entry title
<!-- lesson-meta {"lesson_id": "<UUIDv4>", "content_sha256": "<hex>", "created_at": "<ISO8601>", "producer": "learn|curate"} -->

Entry content...
```

- **`lesson_id`**: UUIDv4 generated at creation. Serves as `RecordRef.record_id` for knowledge entries. Stable across edits (content changes update `content_sha256`, not `lesson_id`).
- **`content_sha256`**: Hash of normalized entry content (excluding the `lesson-meta` comment itself). Used for cross-producer dedup: both `/learn` and `/curate` check `content_sha256` against all existing published entries before writing.
- **`created_at`**: ISO 8601 timestamp of initial creation.
- **`producer`**: Which skill created the entry. Informational — does not affect lifecycle.

The Knowledge reader parses `### ` headings as entry delimiters and extracts `lesson-meta` JSON from the immediately following HTML comment. Entries lacking `lesson-meta` (legacy or hand-edited) are assigned `record_kind: "legacy"` and are discoverable via query but not addressable by `lesson_id`.

### learnings.md write concurrency

Two failure modes, two mitigations:

**Same-worktree (local process race):** Two concurrent operations (e.g., `/learn` and `/curate` publish) in the same worktree perform read-modify-write on `learnings.md`. The Knowledge engine's publish path acquires an advisory file lock (`fcntl.flock(LOCK_EX)`) on a lockfile (`learnings.md.lock`, same directory) before reading. Lock held through read → append → write-to-temp → `fsync` → `os.replace`. Lock released after replace completes. Timeout: 5 seconds. On timeout: fail the operation with `"learnings.md is locked by another operation"` — do not queue or retry.

**Cross-worktree (git merge territory):** Each worktree has its own filesystem view. Concurrent appends from different worktrees produce divergent file states resolved by git merge on the shared branch. The Knowledge engine does not attempt cross-worktree coordination — git's line-based merge handles append-only files well. Conflicting appends (rare — requires overlapping content at the same file position) surface as git merge conflicts for the user to resolve.

**Staging files are not affected** — staging uses content-addressed filenames (`content_sha256`-based) with atomic file creation (`O_CREAT | O_EXCL` via `os.open` or equivalent). Identical candidates from concurrent operations coalesce; non-identical candidates get distinct files.

---

## Section 3: Storage Model

**Dual-root, unified logically.** Two physical locations, one logical namespace.

```
engram/                              # Shared root (repo-local, git-tracked)
├── work/                            # Tickets
│   ├── T-YYYYMMDD-NN-<slug>.md
│   ├── closed/
│   └── .audit/                      # JSONL audit trail (stays authoritative)
├── knowledge/                       # Learnings
│   └── learnings.md                 # Single file for MVP
└── .engram/                         # Shared metadata
    └── (reserved for future use)

~/.claude/engram/<repo_id>/          # Private root (user-home, not git-tracked)
├── snapshots/                       # Full session handoffs
│   └── YYYY-MM-DD_HH-MM_<slug>.md
├── checkpoints/                     # Lightweight quicksaves
│   └── YYYY-MM-DD_HH-MM_checkpoint-<slug>.md
├── chain/                           # Session lineage state files (24h TTL)
├── knowledge_staging/               # Distill candidates awaiting review
│   └── YYYY-MM-DD-<hash>.md
├── ledger/                          # Event ledger (default-on, optional)
│   └── <worktree_id>/
│       └── <session_id>.jsonl       # Per-session, per-worktree sharding
└── .failed/                         # Orphaned envelopes for inspection
```

`.engram-id` lives at the repo root alongside the `engram/` directory.

### Key design decisions

1. **Learnings remain a single file** (`engram/knowledge/learnings.md`) for MVP. Entries are delimited by `### ` headings and individually addressable via `lesson_id` in `lesson-meta` comments (see Section 2). Individual files are a deferred optimization when entry count warrants file-level addressability over single-file browsability.

2. **Tickets move from `docs/tickets/` to `engram/work/`**. Git history preserved via `git mv`.

3. **Handoffs move from `~/.claude/handoffs/<project>/` to `~/.claude/engram/<repo_id>/`**. Keyed by `repo_id` instead of project directory name — solves rename and worktree identity collisions. Forks that share `.engram-id` share the same private root; see Section 8 for the named risk and v1 trade-off rationale.

4. **Knowledge staging is private** (`knowledge_staging/` in the private root). Staged candidates are not repo-visible until explicitly published via `/curate`.

### TTL and lifecycle

| Artifact | TTL | Location |
|----------|-----|----------|
| Snapshots/checkpoints | 90-day TTL from creation (filename timestamp). SessionStart deletes files older than 90 days. No intermediate "archive" tier — files stay in place until deletion. | Private root |
| Chain state files | 24h | Private root |
| Knowledge staging candidates | No TTL (accumulate until curated) | Private root |
| Failed envelopes | 7 days → flagged by `/triage` | Private root `.failed/` |
| Work items | Permanent until closed | Shared root |
| Published knowledge | Permanent (marked with promote-meta when graduated) | Shared root |
| Ledger shards | Append-only, no TTL (compaction deferred). Sharded per worktree/session. | Private root `ledger/` |

### Visibility rule

Publication intent, not access control:
- **Private root** = "this is my session state, not project state"
- **Shared root** = "this is project state that belongs in version control"
- The boundary is about what gets committed, not about security

---

## Section 4: NativeReader Codecs and Indexing

**NativeReaders** are read-only adapters that parse each subsystem's native format into a slim `IndexEntry` for discovery. The index helps you *find* records — to *use* them, open the native file.

**Hard rule: No mutation, policy, or lifecycle decisions from `IndexEntry` alone.** IndexEntry is display-only. Any operation that changes state must open the native file through the subsystem engine.

### IndexEntry

```python
@dataclass(frozen=True)
class IndexEntry:
    ref: RecordRef                # Lookup key
    meta: RecordMeta              # Provenance
    title: str                    # Human-readable title
    created_at: datetime          # Creation timestamp
    updated_at: datetime | None   # Last modification
    status: str | None            # Subsystem-native status string
    tags: list[str]               # Subsystem-native tags
    snippet: str                  # Reader-extracted preview, max 200 chars. Display-only.
    source_path: str              # Absolute path to native file
```

**`snippet` is not `summary`.** It's a preview for display in search results and triage lists. Capped at 200 characters. Reader-extracted (not first-N-chars). Never used for dedup, triage decisions, or workflow logic.

### Readers live with their subsystems

```
packages/plugins/engram/
├── engram_core/
│   ├── reader_protocol.py    # NativeReader protocol + QueryResult types
│   └── query.py              # Discovery + query engine
├── scripts/
│   ├── context/
│   │   └── context_reader.py # Parses --- frontmatter (handoff format)
│   ├── work/
│   │   └── work_reader.py    # Parses fenced yaml (ticket format)
│   └── knowledge/
│       └── knowledge_reader.py # Parses --- frontmatter (learning format)
```

When the ticket format changes, `work_reader.py` changes with it — in the same subsystem directory.

### Reader protocol — readers own both enumeration and parsing

```python
class NativeReader(Protocol):
    subsystem: str

    def scan(self, root: Path, root_type: Literal["shared", "private"]) -> list[Path]:
        """List all files this reader claims. Reader decides what files
        exist and where — Engram never hardcodes subsystem path conventions.
        root_type tells the reader which storage root is being scanned,
        so it can return [] for root types it doesn't handle without
        inspecting path structure."""
        ...

    def read(self, path: Path) -> IndexEntry:
        """Parse native format into IndexEntry. Raises ReaderError on failure."""
        ...

    # No write(). By design.
```

Engram calls `reader.scan(root, root_type)` to discover files — it never globs subsystem directories directly. The query engine calls `scan()` twice per reader: once with `root_type="shared"`, once with `root_type="private"`. Readers return `[]` for root types they don't handle (e.g., the Work reader returns `[]` for `root_type="private"`) — the `root_type` parameter makes this explicit without requiring readers to inspect path structure. The Knowledge reader returns published entries from the shared root and staged entries from the private root, using `record_kind` to distinguish them.

### Query returns entries + diagnostics

```python
@dataclass(frozen=True)
class QueryDiagnostics:
    scanned_count: int            # Total files found by readers
    matched_count: int            # Files matching filters
    skipped_count: int            # Files that failed to parse
    warnings: list[str]           # Parse errors, reader failures
    degraded_roots: list[str]     # "private" or "shared" if unavailable

@dataclass(frozen=True)
class QueryResult:
    entries: list[IndexEntry]
    diagnostics: QueryDiagnostics
```

Callers can distinguish "no matches" from "17 files failed to parse" from "private root unavailable."

### Namespaced status filtering

```python
def query(
    subsystems: list[str] | None = None,
    status: str | None = None,        # "work:open", "knowledge:promoted", etc.
    tags: list[str] | None = None,
    text: str | None = None,          # Searches title + snippet + tags
    since: datetime | None = None,
    session_id: str | None = None,
) -> QueryResult: ...
```

Status filters use `subsystem:value` format (e.g., `"work:open"`, `"knowledge:promoted"`). `IndexEntry.status` stores subsystem-native bare values (e.g., `"open"`, `"promoted"`). The query engine splits the prefix, routes to the correct reader, and matches against bare status. When `subsystems` is set to a single value, bare status is auto-prefixed as a convenience (e.g., `query(subsystems=["work"], status="open")` is equivalent to `status="work:open"`). Bare status with multiple or no subsystems is rejected — no implicit cross-subsystem status normalization.

### No cached index. Fresh metadata scan on query.

Every query does a fresh filesystem scan via `reader.scan()` + `reader.read()`. No `index.json`, no cache invalidation, no read-after-write races. At MVP scale (~100s of files), this is fast.

Git log is **not** part of the `query()` hot path. The `/timeline` operation calls `git log` separately, bounded by session time window.

### Ledger: architecturally optional, operationally default-on

The ledger (sharded as `ledger/<worktree_id>/<session_id>.jsonl` in private root) records events for debugging and diagnostics. Sharding per worktree and session eliminates concurrent-append corruption — each session writes to its own file, following the same pattern as the Work subsystem's per-session audit trail.

Session timeline reconstructs from:
1. `created_at` timestamps from `IndexEntry` (parsed during scan)
2. `session_id` in `RecordMeta` to group records by session
3. `git log` for shared-root change attribution (called once per timeline request, not per query)

No ledger → timeline still works but at lower fidelity (no sub-file-creation event granularity). This is a documented trade-off, not a silent degradation.

### Degradation model

| Condition | Behavior | User visibility |
|-----------|----------|-----------------|
| Private root unavailable | Context queries return empty | `diagnostics.degraded_roots = ["private"]` |
| Shared root unavailable | Work + Knowledge return empty | `diagnostics.degraded_roots = ["shared"]` |
| Reader fails to parse a file | Skip file, add to warnings | `diagnostics.skipped_count > 0` |
| Both roots unavailable | All queries return empty | Skills report "Engram storage unavailable" |
| No ledger | Timeline uses file timestamps only | Lower fidelity, documented |

---

## Section 5: Cross-Subsystem Operations

Six operations justify Engram's plugin scope. Three exist today as cross-plugin calls; three are new capabilities. All cross-subsystem writes use typed envelope contracts with idempotent retry semantics.

### Core rules

- Target subsystem engine validates and writes. Envelopes are requests, not commands.
- Every envelope carries a `source_ref: RecordRef` pinned at creation time. Downstream operations target this ref, never "latest file at path."
- Every envelope carries an `idempotency_key`. Target engines deduplicate retried operations.
- `/save` orchestrates cross-subsystem flows but each sub-operation is independently callable and retryable.
- No reactive pipelines. No cross-subsystem transactions.

### Existing operations (migrate and improve)

**1. Defer: Context → Work**

```
/save (or /defer standalone)
    → Context engine writes snapshot, returns snapshot_ref
    → Skill extracts deferred items
    → DeferEnvelope per item (with idempotency_key)
    → Work engine ingests via 4-stage pipeline
    → Duplicate check: idempotency_key against existing tickets
    → If duplicate: returns existing ticket_ref (no new ticket)
    → If new: creates ticket, returns ticket_ref
```

**2. Distill: Context → Knowledge (staged, not published)**

```
/save (or /distill standalone)
    → Context reader parses snapshot
    → distill engine extracts candidates (parse → subsections → classify durability → dedup)
    → DistillEnvelope per candidate batch (with idempotency_key)
    → Knowledge engine writes to staging inbox (private, not repo-visible)
    → Duplicate check: idempotency_key against staged + published entries
    → If duplicate: skip
    → If new: creates staged candidate
```

**Trust boundary: staged ≠ published.** Distill writes to a private staging area (`knowledge_staging/`), not to `engram/knowledge/`. Staged candidates are reviewed before publication via `/curate`.

**`/curate` mechanics:** `/curate` lists staged candidates sorted by `durability` (likely_durable first), then by `created_at`. It shows snippet, source section, and durability classification. The user reviews and selects candidates to publish. `likely_ephemeral` candidates are surfaced with a warning but not filtered — the user decides. On publish, the knowledge engine deduplicates via `content_sha256` against existing published entries, writes to `engram/knowledge/learnings.md`, and removes the staged file.

**3. Triage: Read Work + Context**

```
/triage
    → query(subsystems=["work"]) → IndexEntries for tickets
    → query(subsystems=["context"]) → IndexEntries for snapshots
    → Open native ticket files for subsystem-specific reasoning
    → Cross-reference: orphaned items, stale tickets, blocked chains, failed envelopes
    → Report pending staged knowledge candidates
    → Return structured triage report with per-subsystem sections
```

Uses the index for *discovery*, opens native files for *reasoning*.

### New operations (Engram-only)

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

**5. Unified Search**

```
/search "auth middleware"
    → query(text="auth middleware") across all subsystems
    → QueryResult with entries grouped by subsystem (never interleaved)
    → User selects entry → open native file
```

**6. Session Timeline**

```
/timeline [session_id]
    → query(session_id=<id>) → all IndexEntries from that session
    → git log --since=<session_start> for shared-root changes
    → Merge and sort chronologically
    → Events labeled as "ledger-backed" or "inferred"
    → Causal links resolved by scanning target records' source_ref fields (O(n), scoped by session_id)
    → Legacy artifacts lacking session_id appear under "unattributed" group
```

### Envelope invariants

- Target engine validates and writes (envelope is a request, not a command)
- Target engine can reject any envelope (duplicate, version mismatch, validation failure)
- Unknown `envelope_version` → explicit `VERSION_UNSUPPORTED` error with expected range
- Idempotent: same `idempotency_key` → same result, no side effects on retry

**Phase-scoped idempotency (migration):** During Step 1 (bridge adapter), only the legacy dedup mechanism (`sha256(problem_text + key_file_paths)`) is active — envelope-level idempotency keys are not checked by the old ticket engine. Full envelope idempotency (where the Work engine checks `idempotency_key` before processing) activates in Step 3 when the new Work engine replaces the bridge. Section 5 core rules describe the Step 3+ steady state. The bridge adapter preserves legacy dedup behavior only.

### `/save` as session orchestrator

```
/save [title] [--no-defer] [--no-distill]
    → Context engine writes snapshot → snapshot_ref
    → If not --no-defer: defer sub-operation
    → If not --no-distill: distill sub-operation
    → Return per-step results:
        {
            snapshot: {status: "ok", ref: snapshot_ref},
            defer: {status: "ok", created: 2, skipped: 1} | {status: "skipped"},
            distill: {status: "ok", staged: 3, skipped: 0} | {status: "skipped"},
        }
```

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

`/save` is a thin orchestrator. No unique business logic. Same code paths as standalone skills. Each sub-operation independently retryable. `/quicksave` remains lightweight (5 sections, no orchestration).

### Failure handling

| Failure | Behavior | Recovery |
|---------|----------|----------|
| Envelope version mismatch | `VERSION_UNSUPPORTED` error | User upgrades Engram |
| Target engine rejects envelope | Specific error (duplicate, validation) | User fixes and retries |
| Idempotent duplicate detected | Returns existing ref, no side effects | Automatic (transparent) |
| `/save` partial success | Per-step results show which failed. Recovery manifest written to `save_recovery.json`. | Retry failed steps standalone with `--snapshot-ref` from manifest. |
| Crash after envelope write | Envelope orphaned in staging | `/triage` flags stale staging files; moved to `.failed/` after 24h TTL |
| Crash before envelope write | No envelope exists; downstream record missing expected upstream link | `/triage` infers unlinked records by scanning native content and cross-checking `source_ref` fields against upstream records |
| Promote Step 2 failure | CLAUDE.md unchanged, no promote-meta written | Lesson remains eligible for next `/promote` run (no durable state recorded until Step 3) |
| Promote Step 3 failure | CLAUDE.md written but promote-meta absent | `/triage` detects mismatch; surfaces for user resolution |
| Legacy artifact lacks session_id | Appears in timeline as "unattributed" | Not silently omitted |

---

## Section 6: Skill Surface and Hooks

### Skills (13 total)

| Skill | Subsystem | Change from today |
|-------|-----------|-------------------|
| `/save` | Context (orchestrator) | Orchestrates defer + distill. Per-step results. `--no-defer`, `--no-distill`. |
| `/load` | Context | Chain protocol uses `repo_id` + `worktree_id`. |
| `/quicksave` | Context | Lightweight: 5 sections, no defer, no distill. |
| `/defer` | Context → Work | DeferEnvelope + idempotency. Accepts `--snapshot-ref <ref>` for retry (required when called standalone after `/save` failure). |
| `/search` | Cross-subsystem | Queries all subsystems. Results grouped by subsystem. |
| `/ticket` | Work | Unchanged API. Storage at `engram/work/`. |
| `/triage` | Cross-subsystem | Merged from ticket-triage + handoff triage. Reports staged candidates + orphans. |
| `/learn` | Knowledge | Appends to `engram/knowledge/learnings.md` with `lesson-meta` contract. Dedup via `content_sha256` against published entries. |
| `/distill` | Context → Knowledge | Writes to staging inbox. Idempotent per snapshot. Accepts `--snapshot-ref <ref>` for retry (required when called standalone after `/save` failure). |
| `/curate` | Knowledge | **New.** Reviews staged candidates, publishes to `engram/knowledge/`. |
| `/promote` | Knowledge → CLAUDE.md | Three-step: engine validates promotability, skill writes CLAUDE.md, engine writes promote-meta. |
| `/timeline` | Cross-subsystem | **New.** Session reconstruction with ledger-backed/inferred labels. |
| `engram init` | System | **New.** Bootstrap: generates `.engram-id` (UUIDv4), writes to repo root, stages for commit. Prints exact `git commit` command for user to run. Idempotent — no-ops if `.engram-id` already exists. |

**Consolidated:** `/ticket-triage` + handoff `/triage` → merged `/triage`.

**`/curate` naming rationale:** "Publish" collides with too many concepts. "Curate" is distinctive, implies review/selection, and pairs with the knowledge lifecycle: learn → distill → curate → promote.

### `/save` orchestration rules

1. **No unique business logic.** Same code paths as standalone skills.
2. **No hidden behaviors.** Every sub-operation visible in per-step results.
3. **Independently retryable.** Failed steps retry via standalone skills with explicit `--snapshot-ref` from recovery manifest. "Latest" is permitted for discovery UI only, never as the semantic source of a write.

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

### Hooks

| Hook | Event | Order | Purpose | On failure |
|------|-------|-------|---------|------------|
| `engram_guard` | PreToolUse | 1st | Protected-path enforcement + trust injection | **Block** |
| `engram_quality` | PostToolUse (Write, Edit) | 2nd | Snapshot quality checks — Write: reads `tool_input.content` from payload. Edit: reads file from disk after edit. Both: only for snapshot-owned paths. | **Warn** |
| `engram_register` | PostToolUse (Write) | 3rd | Ledger append | **Silent** (best-effort) |
| `engram_session` | SessionStart | — | TTL cleanup, worktree_id init | See below |

### Protected-path enforcement (`engram_guard`)

Policy-based, not tool-specific. Protects subsystem-owned paths from direct mutation regardless of which tool is used.

| Path class | Protected paths | Allowed mutators |
|------------|-----------------|------------------|
| `work` | `engram/work/**` | Engine entrypoints only |
| `knowledge_published` | `engram/knowledge/**` | Engine entrypoints only |
| `knowledge_staging` | `~/.claude/engram/<repo_id>/knowledge_staging/**` | Engine entrypoints only |

**Enforcement scope (bounded guarantee):** Write and Edit mutations to protected paths are reliably blocked. Authorized engine Bash invocations (`python3 engine_*.py` patterns) are detected and supported with trust injection. Arbitrary Bash writes (`echo >`, `cp`, `tee`, etc.) are caught on a best-effort basis only — PreToolUse input parsing cannot reliably detect all shell write patterns. This is an honest boundary, not a gap to close: the design provides reliable enforcement for the tools Claude uses natively (Write, Edit) and for the authorized engine invocation pattern, but does not claim to prevent all possible filesystem mutations. See Section 8 for severity assessment and detection strategy.

**Quality validation:** `engram_quality` (PostToolUse) validates snapshot content quality for Write and Edit tool calls on snapshot-owned paths. For Write: reads `tool_input.content` from the payload. For Edit: reads the file from disk after the edit completes (post-state validation). This is advisory quality lint, not trust enforcement — the small race between write completion and validation readback is acceptable for warnings. It does **not** detect Bash-mediated writes to protected paths. Bash bypass of `engram_guard` remains an admitted gap with best-effort pre-blocking only (see Section 8).

Paths canonicalized before matching (resolve symlinks, collapse `..`, normalize to absolute).

### Trust injection mechanism

`engram_guard` injects a trust triple into the engine payload for every authorized Bash invocation of a subsystem engine:

1. **Injection (PreToolUse):** When `engram_guard` detects an authorized engine invocation pattern (`python3 engine_*.py`), it writes `hook_injected=True`, `hook_request_origin`, and `session_id` to the engine's payload file atomically (temp file → `fsync` → `os.replace`). This carries forward the ticket plugin's proven trust injection pattern.

2. **Validation (engine entrypoint):** Every **mutating** entrypoint in each subsystem engine must invoke a shared trust validator (`collect_trust_triple_errors()`) before making state changes. The validator checks that all three fields are present and non-empty. Missing or incomplete triples reject the operation. Read-only entrypoints are exempt.

3. **Per-subsystem enforcement:** Each subsystem engine owns its trust boundary. The shared validator lives in `engram_core/` but enforcement is at the engine level — Engram's indexing layer never sees or checks trust triples.

### SessionStart hook (`engram_session`)

Bounded and idempotent. <500ms startup budget.

| Operation | Budget | On failure |
|-----------|--------|------------|
| Resolve `worktree_id` | 1 call | Fail-closed: session needs identity |
| Clean expired snapshots (>90d by filename timestamp) | Max 50 files | Fail-open: retry next session |
| Clean expired chain state (>24h) | Max 20 files | Fail-open |
| Clean `.failed/` envelopes (>7d) | Max 20 files | Fail-open |
| Verify `.engram-id` exists | 1 read | Warn if missing (diagnostic only — does not create) |

**Bootstrap:** SessionStart does not create `.engram-id` — it requires a git commit, which is inappropriate during session initialization. Bootstrap occurs via `engram init` (see Skills table). Until `.engram-id` exists, all mutating Engram operations (save, defer, distill, ticket create) fail closed with error: `"Engram not initialized: run 'engram init' to bootstrap."` Read-only operations (search, triage) degrade gracefully via the existing degradation model.

### Autonomy model

| Subsystem | Model | Rationale |
|-----------|-------|-----------|
| Work | `suggest` / `auto_audit` | Trust boundary: agents propose, users approve |
| Context | None | Agents save their own session state |
| Knowledge staging | Staging inbox cap + idempotency | Dedup prevents repeated staging; cumulative cap limits volume |

Configuration in `.claude/engram.local.md` (YAML frontmatter in markdown, parsed by `engram_core` using the same fenced-YAML extraction as the ticket plugin's `extract_fenced_yaml()`):

```yaml
autonomy:
  work_mode: suggest          # suggest | auto_audit
  work_max_creates: 5
  knowledge_max_stages: 10    # Cumulative files in staging inbox, not per-session
ledger:
  enabled: true               # Default on. Opt-out here.
```

**Staging inbox cap enforcement:** The Knowledge engine checks the cumulative count of files in `knowledge_staging/` **before** writing new staged candidates. If `count + batch_size > knowledge_max_stages`, the entire batch is rejected (whole-batch reject for determinism — no partial staging). The rejection response includes current count, cap, and a suggestion to run `/curate` to clear the inbox.

Scope is cumulative (total files in directory), not per-session. This matches the stated risk (staging accumulation over time), not per-session agent autonomy. The engine reads `knowledge_max_stages` from `.claude/engram.local.md` at invocation time — no caching.

### Trigger differentiation

| Collision pair | Differentiation |
|----------------|-----------------|
| `/save` vs `/quicksave` | Full session wrap-up vs. quick checkpoint |
| `/triage` vs `/ticket list` | Cross-subsystem health dashboard vs. list my tickets |
| `/search` vs `/ticket query` | Find across everything vs. find ticket by ID prefix |
| `/distill` vs `/learn` | Bulk extraction from snapshot (staged) vs. capture one insight manually (direct publish). Both write `lesson-meta`; both dedup via `content_sha256`. |
| `/curate` vs `/promote` | Review staged candidates vs. graduate published knowledge to CLAUDE.md |

---

## Section 7: Migration Strategy

**Context:** All three plugins live in this repo. No external users, no production deployments. We can break old plugins freely during development.

**Approach:** Build Engram, move data, delete old code. No coexistence period.

### Build sequence

```
Step 0a: Foundation contracts (plugin + core library + type contracts)
    ↓
Step 0b: Bootstrap and identity (engram init + .engram-id)
    ↓
Step 1: Bridge cutover (defer/ingest)
    ↓
Step 2: Knowledge cutover
    ↓
Step 3: Work cutover
    ↓
Step 4: Context cutover
    ↓
Step 5: Cleanup
```

### Step 0a: Foundation contracts

Create plugin, core library, and type contracts. Validate the foundation before bootstrap.

| Deliverable | Detail |
|-------------|--------|
| Plugin manifest | `packages/plugins/engram/.claude-plugin/plugin.json` |
| `engram_core/types.py` | RecordRef, RecordMeta, IndexEntry, QueryResult, envelope types (including `lesson-meta` contract for knowledge entries and per-candidate fingerprints in `DistillEnvelope` idempotency material) |
| `engram_core/reader_protocol.py` | NativeReader protocol with `root_type: Literal["shared", "private"]` parameter on `scan()` |
| `engram_core/query.py` | Fresh-scan query engine |

**Exit criteria:** All types pass construction and equality tests. Query scans empty directories with correct diagnostics. NativeReader protocol compiles with `root_type` parameter.

### Step 0b: Bootstrap and identity

Create identity resolution and bootstrap command. Depends on 0a types being stable.

| Deliverable | Detail |
|-------------|--------|
| `engram_core/identity.py` | repo_id generation/resolution, worktree_id derivation |
| `engram init` command | Generates `.engram-id` (UUIDv4), writes to repo root, stages for commit |
| `.engram-id` | Generated and committed (for this repo) |

**Exit criteria:** Identity works across worktrees. `engram init` is idempotent. SessionStart warns when `.engram-id` missing and points to `engram init`.

### Step 1: Bridge cutover (defer/ingest)

The only existing cross-subsystem path with trusted writes on both ends. Proves Engram's value.

| Deliverable | Detail |
|-------------|--------|
| `DeferEnvelope` with `EnvelopeHeader` | New envelope type |
| Bridge adapter + SourceResolver | Converts `DeferEnvelope` → old `DeferredWorkEnvelope` JSON → temp file → old ticket engine ingest. SourceResolver reads source snapshot frontmatter to recover `session_id` for bridge mapping (see below). |
| Context reader | Parses handoff `---` frontmatter |
| Work reader | Parses ticket fenced YAML |
| `/defer` skill | Emits `DeferEnvelope`, adapter calls old ticket engine |

Readers point at current data locations. Data doesn't move yet. The bridge adapter is temporary scaffolding — it allows Step 1 to prove envelope contracts without requiring the new Work engine (a Step 3 deliverable). The adapter preserves the old engine's existing dedup behavior.

**Bridge field mapping via SourceResolver:** The old `DeferredWorkEnvelope` requires `source.type`, `source.ref`, and `source.session` as string fields. The new `EnvelopeHeader.source_ref` is a `RecordRef` with no `session` field. The bridge adapter uses an adapter-local `SourceResolver` to bridge this structural mismatch:

| Old field | Mapped from |
|-----------|-------------|
| `source.type` | `f"engram:{source_ref.subsystem}:{source_ref.record_kind}"` |
| `source.ref` | Canonical `RecordRef` serialization |
| `source.session` | `SourceResolver` reads `session_id` from the source snapshot's frontmatter |

The `SourceResolver` is adapter-local scaffolding — it dies with the bridge adapter in Step 5 cleanup. Do not add `session_id` to `EnvelopeHeader` or `RecordRef` to serve this temporary need.

**Cross-step dependency:** Do not modify the `DeferEnvelope` or `EnvelopeHeader` types between Steps 1 and 3 without updating the bridge adapter. The adapter depends on both the new envelope format and the old ticket engine's ingest JSON schema.

**Bridge compatibility test:** A behavioral contract test must accompany the bridge adapter. The test:
1. Constructs a representative `DeferEnvelope` with full `EnvelopeHeader`
2. Runs it through the bridge adapter's conversion logic
3. Asserts the output is valid legacy `DeferredWorkEnvelope` JSON
4. Verifies `SourceResolver` field mapping (`source.type`, `source.ref`, `source.session`)

This test runs in CI across Steps 1–3. If type changes to `DeferEnvelope` or `EnvelopeHeader` break the bridge, this test fails fast — replacing the process-level "do not modify" warning with a structural guard. The test is deleted in Step 5 cleanup alongside the bridge adapter.

**Exit criteria:** `/defer` produces envelope with RecordRef linkage. Bridge adapter successfully routes to old ticket engine. Cross-subsystem query returns results from both readers. Bridge compatibility test passes.

### Step 2: Knowledge cutover

**Step 2a — Activate:**

| Deliverable | Detail |
|-------------|--------|
| `engram/knowledge/learnings.md` | `git mv docs/learnings/learnings.md` |
| Knowledge reader, engine | Staging writes, dedup, publication, promote-meta |
| Staging inbox | `~/.claude/engram/<repo_id>/knowledge_staging/` |
| `/learn`, `/distill`, `/curate`, `/promote` | All knowledge skills |

**Exit criteria (2a):** Full learn → distill → curate → promote lifecycle. Staging dedup. Session cap.

**Step 2b — Retire:**

- Remove old learn/distill/promote skills from repo `.claude/skills/`
- Remove deployed copies from `~/.claude/skills/{learn,distill,promote}/` (use `trash`)
- Remove knowledge-related code from handoff plugin

**Exit criteria (2b):** No old knowledge skills present in repo or deployed locations. New Engram skills are the sole providers.

### Step 3: Work cutover

**Step 3a — Activate:**

| Deliverable | Detail |
|-------------|--------|
| `engram/work/` | `git mv docs/tickets/*` |
| Work engine | 4-stage pipeline, trust model, dedup, autonomy — all preserved |
| `engram_guard` hook | Protected-path enforcement + trust injection |
| `/ticket`, `/triage` | Work skills |
| Config | `.claude/engram.local.md` |
| Bridge adapter update | `/defer` switches from bridge adapter (Step 1) to new Work engine |

**Exit criteria (3a):** All ticket operations work. Protected-path enforcement blocks Write/Edit (Bash best-effort). Trust triple works. Compatibility harness passes. `/defer` routes through new Work engine.

**Step 3b — Retire:**

- Remove `packages/plugins/ticket/` package
- Remove deployed ticket plugin from `~/.claude/plugins/` (use `trash`)

**Exit criteria (3b):** No old ticket code present in repo or deployed locations.

### Step 4: Context cutover

**Step 4a — Activate:**

| Deliverable | Detail |
|-------------|--------|
| `~/.claude/engram/<repo_id>/` storage | Keyed by repo_id + worktree_id |
| Context engine | Chain protocol updated |
| `engram_quality`, `engram_session`, `engram_register` hooks | Quality, SessionStart, ledger |
| `/save`, `/load`, `/quicksave`, `/search`, `/timeline` | All Context + cross-subsystem skills |

**Data migration:** Copy handoffs to new location. Map project name → repo_id.

**Chain state migration:** Before copying chain state files, classify each:
- **Valid fresh** (age < 24h, target snapshot exists): Migrate to new `chain/` directory
- **Stale** (age > 24h): Skip — TTL would have pruned these
- **Dangling** (target snapshot missing): Skip — archive-failure poisoning
- **Corrupt** (unparseable): Skip and log

Only migrate valid fresh state. Do not reimport defects from the old system.

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

**Exit criteria (4a):** Save/load cycle works. Worktree isolation verified. `/save` orchestration with per-step results. `/search` spans all subsystems. `/timeline` reconstructs sessions. All hooks operational. SessionStart <500ms. Chain state migration classifies and filters old state files. All copied handoffs parse successfully through the Context reader. Migration manifest written with no `skipped_corrupt` entries for newly copied files.

**Step 4b — Retire:**

- Remove `packages/plugins/handoff/` package
- Remove deployed handoff plugin from `~/.claude/plugins/` (use `trash`)
- Remove deployed handoff skills from `~/.claude/skills/{save,load,quicksave,search,defer,distill,triage}/` (use `trash`)

**Exit criteria (4b):** No old handoff code present in repo or deployed locations.

**Cross-step dependency:** Steps 2a and 3a depend on the old handoff format remaining readable (Context reader parses `---` frontmatter from existing handoff files). Do not modify the handoff format until Step 4a is complete.

### Step 5: Cleanup

- Remove bridge adapter and SourceResolver from Step 1 (temporary scaffolding must not survive as permanent code)
- Remove old marketplace entries for retired plugins
- Clean old data locations (`docs/tickets/`, `docs/learnings/`)
- Update CLAUDE.md, references, and documentation
- Verify no stale references to old plugin paths in skills, hooks, or agents

### Testing strategy

**Compatibility harness for Work subsystem (Step 3):**

Feed identical fixtures into old ticket engine and new Engram Work engine. Compare:
- Response envelope (state, message, error_code)
- On-disk ticket output
- Audit side effects
- Hook allow/deny behavior
- Dedup/TOCTOU/trust outcomes

**Triage old tests into three buckets:**

| Bucket | Treatment |
|--------|-----------|
| Compatibility-critical (~100-150) | Must pass harness. Behavioral equivalence gates migration. |
| Fixture/golden (~200-250) | Port fixtures, write fresh assertions. |
| Implementation-local (~200-300) | Don't port. Write what's needed for new engine. |

**All migration scripts are idempotent.** Running twice produces the same result.

**Rollback:** Each step is a branch. Revert the branch if a step fails.

- **Shared root (git-tracked):** Branch revert fully restores the pre-step state. The activate/retire split ensures old code is still in the repo during validation (substep a) and only removed after validation passes (substep b). Reverting substep b restores old code; reverting substep a restores the pre-step state entirely.
- **Private root (`~/.claude/engram/`):** Migration steps that write to the private root (Steps 2a, 4a) are **forward-only and additive** — they copy data but never delete originals. Branch revert does not undo private-root writes. Orphaned private-root data after a branch revert is expected and safe — SessionStart cleanup handles TTL expiration, and re-running the migration step is idempotent (copy skips files that already exist at the destination). Deletion of original private-root data (e.g., `~/.claude/handoffs/`) occurs only in Step 5 (cleanup), after all validation passes.

---

## Section 8: Risks, Open Questions, and Deferred Decisions

### Named risks

| Risk | Severity | Mitigation | Detection |
|------|----------|------------|-----------|
| **Shadow authority** | High | Engram indexes but never owns. No decisions from IndexEntry. | Does any feature give a different answer via Engram vs. subsystem? |
| **God Skill on /save** | Medium | Thin orchestrator, no unique logic, same code paths. | Does /save contain logic /defer or /distill don't share? |
| **Fingerprint drift** | Medium | repo_id is stored UUIDv4. Dedup uses content hashes, not paths. | Rename repo, clone elsewhere — dedup still works? |
| **Bash enforcement gap** | High | **Bounded guarantee:** Write/Edit direct mutations to protected paths are reliably blocked. Authorized engine Bash invocations are supported via trust injection. Arbitrary Bash writes to protected paths may bypass the guard and are not guaranteed detectable. Records created via Bash bypass have no trust triple, no audit trail, and no provenance guarantee. Post-hoc drift scan deferred (see Deferred decisions). | Bash write to `engram/work/` bypasses guard? Created ticket has no `.audit/` entry? |
| **Fork-on-same-machine collision** | Low | Two forks sharing `.engram-id` use the same private root. Worktree_id differentiates Context queries. Knowledge staging and ledger shards commingle but are operationally harmless at single-developer scale. Deliberate v1 trade-off — engineering fix (worktree_id in private root path) deferred because it changes private root semantics from repo-scoped to worktree-scoped. | Clone a fork locally, run `/curate` — see candidates from both? |
| **Staging accumulation** | Low | /triage reports pending. Cumulative staging inbox cap (default 10). /curate shows queue. Knowledge engine rejects whole batch when cap exceeded. | Staging directory file count over time. |
| **NativeReader latency** | Low | Fresh scan at MVP scale is fast. git log off hot path. | Query latency on repos with 500+ files. |
| **Concurrent worktree staging** | Medium | **Staging files:** Content-addressed filenames (`content_sha256`-based) with `O_CREAT | O_EXCL` atomic creation. Concurrent identical candidates coalesce. **Published learnings (`learnings.md`):** Same-worktree concurrency guarded by `fcntl.flock` on lockfile (see Section 2). Cross-worktree concurrency delegated to git merge. | Two worktrees distill same snapshot concurrently — duplicate staging files? Same-worktree `/learn` + `/curate` concurrent — lost append? |
| **Chain protocol limitations** | Low | Three inherited limitations (resume-crash gap, archive-failure poisoning, state-file TTL race). Archive-failure resolved in v1 by archive-before-state-write ordering. Other two carried as named limitations. See Section 6 chain protocol. | Session spans >24h, save has no `resumed_from`? |

### Open questions

| Question | When to resolve |
|----------|-----------------|
| What additional fields does IndexEntry need? | Step 0a implementation. Extend based on real query needs. |
| How many of 669 ticket tests are compatibility-critical? | Step 3. Triage before building harness. |

### Deferred decisions (explicitly not in v1)

| Decision | Rationale |
|----------|-----------|
| Three-tier storage (repo-local `.claude/engram/`) | Current two-root model sufficient. Add if multi-worktree pain materializes. |
| Individual knowledge files | Single learnings.md for MVP. Split when count warrants. |
| Manifest-based reader discovery | Three hardcoded readers is fine. YAGNI. |
| Incremental indexing | Fresh scan fast enough. Add if >200ms. |
| `auto_silent` autonomy mode | Deferred from ticket v1.1. Carry forward. |
| Reactive pipelines (auto-defer, auto-distill) | User-initiated for v1. Consider after usage patterns emerge. |
| Ledger compaction | Append-only grows indefinitely. Add when file size matters. |
| Cross-user timeline | Session-local only. Multi-user via git log is out of scope. |
| Bounded protected-path drift scan | PostToolUse Bash trigger that compares protected-root manifest (mtime, size) before/after Bash execution. Would close the Bash enforcement gap for git-tracked paths. Not achievable without pre/post state comparison mechanism. |

### Design principles

Three cross-cutting principles emerged from the design review process. These are not invariants (they have no enforcement mechanism) but guide implementation decisions across subsystems.

**1. Auxiliary state authority:** Recovery manifests (`save_recovery.json`, `migration_report.json`) and reconciliation metadata (`promote-meta`) are operational aids only. Primary records — snapshots, tickets, learnings, chain state files — remain authoritative. Manifest failure degrades convenience (retry requires manual snapshot_ref lookup) but does not break standalone operations. Use distinct naming for each manifest to prevent shadow-authority confusion.

**2. Pre/post-write validation layering:** Pre-write or pre-dispatch validation for hard invariants (trust triples, idempotency keys, promotion state machine). Post-write validation for advisory quality checks only (`engram_quality`). PostToolUse hooks must not become enforcement boundaries — the race between write completion and validation readback is acceptable for warnings, not for trust authorization.

**3. Chain integrity at migration boundaries:** When migrating state from an old system (chain files, staging candidates), classify each artifact's health before copying. Only migrate valid, fresh state. Do not reimport known defects (stale chain files, poisoned references) from the predecessor system.

### Success criteria

| Criterion | Measurement |
|-----------|-------------|
| All 13 skills functional | Manual walkthrough of each primary flow (including `engram init`) |
| Cross-subsystem query works | `/search` returns from all three subsystems |
| Session timeline reconstructs | `/timeline` with ledger-backed/inferred labels |
| Defer → ticket linkage | Ticket's source_ref traces to originating snapshot |
| Distill → staging → curate pipeline | Full lifecycle works |
| Protected-path enforcement | Direct Write/Edit to `engram/work/` blocked; Bash best-effort |
| Worktree isolation | Two worktrees don't cross-contaminate Context |
| Compatibility harness passes | Work subsystem behavioral equivalence |
| Old plugins removed | No code in `packages/plugins/handoff/` or `packages/plugins/ticket/` |
| SessionStart < 500ms | Cleanup bounded and idempotent |
