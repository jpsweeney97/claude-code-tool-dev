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
├── skills/                   # User-facing skills (12 total)
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
    record_id: str        # Subsystem-native ID (handoff filename, T-YYYYMMDD-NN, lesson date+tag)
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

### Idempotency vs dedup — two distinct mechanisms

**Idempotency** answers: "is this the same operation being retried?" The `idempotency_key` in `EnvelopeHeader` is computed from `canonical_json(idempotency_material)` where the material is envelope-type-specific:

| Envelope | `idempotency_material` |
|----------|----------------------|
| `DeferEnvelope` | `{source_ref.record_id, title, problem}` |
| `DistillEnvelope` | `{source_ref.record_id, len(candidates)}` |
| `PromoteEnvelope` | `{source_ref.record_id, target_section}` |

`canonical_json()` sorts keys and normalizes whitespace. Same material → same key → target engine returns existing result without side effects.

**Dedup** answers: "is this content semantically identical to existing content?" Uses content fingerprints at the record level:
- `DistillCandidate.content_sha256` — deduplicates staged/published knowledge entries by content
- Work engine's existing duplicate detection — matches by title similarity and source overlap

These are independent: an idempotent retry of a distill operation (same `idempotency_key`) is caught at the envelope level before dedup is ever checked. A genuinely new operation with coincidentally identical content is caught by dedup, not idempotency.

**Format preservation:** Each subsystem keeps its native format. Tickets keep fenced YAML. Handoffs keep `---` frontmatter. Learnings keep their current markdown format. NativeReaders parse each format without requiring unification.

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

1. **Learnings remain a single file** (`engram/knowledge/learnings.md`) for MVP. Individual files are a deferred optimization when entry count warrants addressability over single-file browsability.

2. **Tickets move from `docs/tickets/` to `engram/work/`**. Git history preserved via `git mv`.

3. **Handoffs move from `~/.claude/handoffs/<project>/` to `~/.claude/engram/<repo_id>/`**. Keyed by `repo_id` instead of project directory name — solves rename and worktree identity collisions. Forks that share `.engram-id` share the same private root; see Section 8 for the named risk and v1 trade-off rationale.

4. **Knowledge staging is private** (`knowledge_staging/` in the private root). Staged candidates are not repo-visible until explicitly published via `/curate`.

### TTL and lifecycle

| Artifact | TTL | Location |
|----------|-----|----------|
| Snapshots/checkpoints | 30-day active, 90-day archive | Private root |
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

    def scan(self, root: Path) -> list[Path]:
        """List all files this reader claims. Reader decides what files
        exist and where — Engram never hardcodes subsystem path conventions."""
        ...

    def read(self, path: Path) -> IndexEntry:
        """Parse native format into IndexEntry. Raises ReaderError on failure."""
        ...

    # No write(). By design.
```

Engram calls `reader.scan(root)` to discover files — it never globs subsystem directories directly. The query engine calls `scan()` twice per reader: once with the shared root, once with the private root. Readers return `[]` for roots they don't own (e.g., the Work reader returns `[]` for the private root). The Knowledge reader returns published entries from the shared root and staged entries from the private root, using `record_kind` to distinguish them.

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

**4. Promote: Knowledge → CLAUDE.md (two-step)**

```
/promote
    → query(subsystems=["knowledge"], status="knowledge:published")
    → Rank by maturity signals (age, breadth, reuse evidence)
    → User selects
    → Step 1 (engine): Knowledge engine validates promotability, returns promotion plan
    → Step 2 (skill): Skill writes transformed text to CLAUDE.md
    → Step 3 (engine): Knowledge engine writes promote-meta to mark completion
```

CLAUDE.md is an external sink, not an Engram-managed record. The Knowledge engine owns the promotion *state*. The CLAUDE.md edit is a skill-level operation. Deliberate, documented exception to the "target engine validates and writes" rule.

**Promote recovery (reconciliation-based):** Step 1 validates but does not record durable state — it returns a promotion plan. Step 3 writes `promote-meta` only after the CLAUDE.md write succeeds. If Step 2 fails, no `promote-meta` exists, so the lesson remains eligible for future `/promote` runs. If Step 3 fails (promote-meta write), `/triage` detects the mismatch: CLAUDE.md contains the text but the knowledge record lacks `promote-meta`. `/triage` surfaces this for the user to resolve (attach metadata, re-draft, or skip).

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

`/save` is a thin orchestrator. No unique business logic. Same code paths as standalone skills. Each sub-operation independently retryable. `/quicksave` remains lightweight (5 sections, no orchestration).

### Failure handling

| Failure | Behavior | Recovery |
|---------|----------|----------|
| Envelope version mismatch | `VERSION_UNSUPPORTED` error | User upgrades Engram |
| Target engine rejects envelope | Specific error (duplicate, validation) | User fixes and retries |
| Idempotent duplicate detected | Returns existing ref, no side effects | Automatic (transparent) |
| `/save` partial success | Per-step results show which failed | Retry failed steps standalone |
| Crash after envelope write | Envelope orphaned in staging | `/triage` flags stale staging files; moved to `.failed/` after 24h TTL |
| Crash before envelope write | No envelope exists; downstream record missing expected upstream link | `/triage` infers unlinked records by scanning native content and cross-checking `source_ref` fields against upstream records |
| Promote Step 2 failure | CLAUDE.md unchanged, no promote-meta written | Lesson remains eligible for next `/promote` run (no durable state recorded until Step 3) |
| Promote Step 3 failure | CLAUDE.md written but promote-meta absent | `/triage` detects mismatch; surfaces for user resolution |
| Legacy artifact lacks session_id | Appears in timeline as "unattributed" | Not silently omitted |

---

## Section 6: Skill Surface and Hooks

### Skills (12 total)

| Skill | Subsystem | Change from today |
|-------|-----------|-------------------|
| `/save` | Context (orchestrator) | Orchestrates defer + distill. Per-step results. `--no-defer`, `--no-distill`. |
| `/load` | Context | Chain protocol uses `repo_id` + `worktree_id`. |
| `/quicksave` | Context | Lightweight: 5 sections, no defer, no distill. |
| `/defer` | Context → Work | DeferEnvelope + idempotency. |
| `/search` | Cross-subsystem | Queries all subsystems. Results grouped by subsystem. |
| `/ticket` | Work | Unchanged API. Storage at `engram/work/`. |
| `/triage` | Cross-subsystem | Merged from ticket-triage + handoff triage. Reports staged candidates + orphans. |
| `/learn` | Knowledge | Appends to `engram/knowledge/learnings.md`. |
| `/distill` | Context → Knowledge | Writes to staging inbox. Idempotent per snapshot. |
| `/curate` | Knowledge | **New.** Reviews staged candidates, publishes to `engram/knowledge/`. |
| `/promote` | Knowledge → CLAUDE.md | Three-step: engine validates promotability, skill writes CLAUDE.md, engine writes promote-meta. |
| `/timeline` | Cross-subsystem | **New.** Session reconstruction with ledger-backed/inferred labels. |

**Consolidated:** `/ticket-triage` + handoff `/triage` → merged `/triage`.

**`/curate` naming rationale:** "Publish" collides with too many concepts. "Curate" is distinctive, implies review/selection, and pairs with the knowledge lifecycle: learn → distill → curate → promote.

### `/save` orchestration rules

1. **No unique business logic.** Same code paths as standalone skills.
2. **No hidden behaviors.** Every sub-operation visible in per-step results.
3. **Independently retryable.** Failed steps retry via standalone skills.

### Hooks

| Hook | Event | Order | Purpose | On failure |
|------|-------|-------|---------|------------|
| `engram_guard` | PreToolUse | 1st | Protected-path enforcement + trust injection | **Block** |
| `engram_quality` | PostToolUse (Write) | 2nd | Snapshot quality checks + protected-path integrity validation | **Warn** |
| `engram_register` | PostToolUse (Write) | 3rd | Ledger append | **Silent** (best-effort) |
| `engram_session` | SessionStart | — | TTL cleanup, worktree_id init | See below |

### Protected-path enforcement (`engram_guard`)

Policy-based, not tool-specific. Protects subsystem-owned paths from direct mutation regardless of which tool is used.

| Path class | Protected paths | Allowed mutators |
|------------|-----------------|------------------|
| `work` | `engram/work/**` | Engine entrypoints only |
| `knowledge_published` | `engram/knowledge/**` | Engine entrypoints only |
| `knowledge_staging` | `~/.claude/engram/<repo_id>/knowledge_staging/**` | Engine entrypoints only |

**Enforcement scope:** Write and Edit mutations are reliably blocked. Bash interception is best-effort — detecting arbitrary shell commands that write to protected paths (`echo >`, `cp`, `tee`, etc.) is unreliable via PreToolUse input parsing. The guard catches direct `python3 engine_*.py` patterns reliably; other Bash writes are caught on a best-effort basis. See Section 8 for the named risk.

**Defense-in-depth:** `engram_quality` (PostToolUse) validates protected-path integrity after writes complete — if a Bash command bypasses `engram_guard` and mutates a protected path, `engram_quality` detects the unauthorized change and warns. This does not prevent the write but ensures it is never silent.

Paths canonicalized before matching (resolve symlinks, collapse `..`, normalize to absolute).

### SessionStart hook (`engram_session`)

Bounded and idempotent. <500ms startup budget.

| Operation | Budget | On failure |
|-----------|--------|------------|
| Resolve `worktree_id` | 1 call | Fail-closed: session needs identity |
| Clean expired snapshots (>30d/90d) | Max 50 files | Fail-open: retry next session |
| Clean expired chain state (>24h) | Max 20 files | Fail-open |
| Clean `.failed/` envelopes (>7d) | Max 20 files | Fail-open |
| Verify `.engram-id` exists | 1 read | Warn if missing (diagnostic only — does not create) |

**Bootstrap:** SessionStart does not create `.engram-id` — it requires a git commit, which is inappropriate during session initialization. Bootstrap occurs via Step 0 (migration for this repo) or a dedicated `engram init` command (for new repos post-v1). Until `.engram-id` exists, all mutating Engram operations (save, defer, distill, ticket create) fail closed with error: `"Engram not initialized: run 'engram init' to bootstrap."` Read-only operations (search, triage) degrade gracefully via the existing degradation model.

### Autonomy model

| Subsystem | Model | Rationale |
|-----------|-------|-----------|
| Work | `suggest` / `auto_audit` | Trust boundary: agents propose, users approve |
| Context | None | Agents save their own session state |
| Knowledge staging | Session cap + idempotency | Dedup prevents repeated staging; cap limits volume |

Configuration in `.claude/engram.local.md` (YAML frontmatter in markdown, parsed by `engram_core` using the same fenced-YAML extraction as the ticket plugin's `extract_fenced_yaml()`):

```yaml
autonomy:
  work_mode: suggest          # suggest | auto_audit
  work_max_creates: 5
  knowledge_max_stages: 10
ledger:
  enabled: true               # Default on. Opt-out here.
```

### Trigger differentiation

| Collision pair | Differentiation |
|----------------|-----------------|
| `/save` vs `/quicksave` | Full session wrap-up vs. quick checkpoint |
| `/triage` vs `/ticket list` | Cross-subsystem health dashboard vs. list my tickets |
| `/search` vs `/ticket query` | Find across everything vs. find ticket by ID prefix |
| `/distill` vs `/learn` | Bulk extraction from snapshot vs. capture one insight manually |
| `/curate` vs `/promote` | Review staged candidates vs. graduate published knowledge to CLAUDE.md |

---

## Section 7: Migration Strategy

**Context:** All three plugins live in this repo. No external users, no production deployments. We can break old plugins freely during development.

**Approach:** Build Engram, move data, delete old code. No coexistence period.

### Build sequence

```
Step 0: Engram shell (plugin + core library)
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

### Step 0: Engram shell

Create plugin and core library. Validate the foundation.

| Deliverable | Detail |
|-------------|--------|
| Plugin manifest | `packages/plugins/engram/.claude-plugin/plugin.json` |
| `engram_core/identity.py` | repo_id generation/resolution, worktree_id derivation |
| `engram_core/types.py` | RecordRef, RecordMeta, IndexEntry, QueryResult, envelope types |
| `engram_core/reader_protocol.py` | NativeReader protocol |
| `engram_core/query.py` | Fresh-scan query engine |
| `.engram-id` | Generated and committed |

**Exit criteria:** Identity works across worktrees. Query scans empty directories with correct diagnostics. All types pass construction and equality tests.

### Step 1: Bridge cutover (defer/ingest)

The only existing cross-subsystem path with trusted writes on both ends. Proves Engram's value.

| Deliverable | Detail |
|-------------|--------|
| `DeferEnvelope` with `EnvelopeHeader` | New envelope type |
| Bridge adapter | Converts `DeferEnvelope` → old `DeferredWorkEnvelope` JSON → temp file → old ticket engine ingest |
| Context reader | Parses handoff `---` frontmatter |
| Work reader | Parses ticket fenced YAML |
| `/defer` skill | Emits `DeferEnvelope`, adapter calls old ticket engine |

Readers point at current data locations. Data doesn't move yet. The bridge adapter is temporary scaffolding — it allows Step 1 to prove envelope contracts without requiring the new Work engine (a Step 3 deliverable). The adapter preserves the old engine's existing dedup behavior.

**Exit criteria:** `/defer` produces envelope with RecordRef linkage. Bridge adapter successfully routes to old ticket engine. Cross-subsystem query returns results from both readers.

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

**Exit criteria (4a):** Save/load cycle works. Worktree isolation verified. `/save` orchestration with per-step results. `/search` spans all subsystems. `/timeline` reconstructs sessions. All hooks operational. SessionStart <500ms.

**Step 4b — Retire:**

- Remove `packages/plugins/handoff/` package
- Remove deployed handoff plugin from `~/.claude/plugins/` (use `trash`)
- Remove deployed handoff skills from `~/.claude/skills/{save,load,quicksave,search,defer,distill,triage}/` (use `trash`)

**Exit criteria (4b):** No old handoff code present in repo or deployed locations.

**Cross-step dependency:** Steps 2a and 3a depend on the old handoff format remaining readable (Context reader parses `---` frontmatter from existing handoff files). Do not modify the handoff format until Step 4a is complete.

### Step 5: Cleanup

- Remove bridge adapter from Step 1 (temporary scaffolding must not survive as permanent code)
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

**Rollback:** Each step is a branch. Revert the branch if a step fails. The activate/retire split ensures old code is still in the repo during validation (substep a) and only removed after validation passes (substep b). Reverting substep b restores old code; reverting substep a restores the pre-step state entirely.

---

## Section 8: Risks, Open Questions, and Deferred Decisions

### Named risks

| Risk | Severity | Mitigation | Detection |
|------|----------|------------|-----------|
| **Shadow authority** | High | Engram indexes but never owns. No decisions from IndexEntry. | Does any feature give a different answer via Engram vs. subsystem? |
| **God Skill on /save** | Medium | Thin orchestrator, no unique logic, same code paths. | Does /save contain logic /defer or /distill don't share? |
| **Fingerprint drift** | Medium | repo_id is stored UUIDv4. Dedup uses content hashes, not paths. | Rename repo, clone elsewhere — dedup still works? |
| **Bash enforcement gap** | Medium | `engram_guard` reliably blocks Write/Edit but Bash interception is best-effort. `engram_quality` PostToolUse provides defense-in-depth by detecting unauthorized changes after the fact. | Bash write to `engram/work/` bypasses guard? `engram_quality` warns? |
| **Fork-on-same-machine collision** | Low | Two forks sharing `.engram-id` use the same private root. Worktree_id differentiates Context queries. Knowledge staging and ledger shards commingle but are operationally harmless at single-developer scale. Deliberate v1 trade-off — engineering fix (worktree_id in private root path) deferred because it changes private root semantics from repo-scoped to worktree-scoped. | Clone a fork locally, run `/curate` — see candidates from both? |
| **Staging accumulation** | Low | /triage reports pending. Session cap. /curate shows queue. | Staging directory file count over time. |
| **NativeReader latency** | Low | Fresh scan at MVP scale is fast. git log off hot path. | Query latency on repos with 500+ files. |

### Open questions

| Question | When to resolve |
|----------|-----------------|
| What additional fields does IndexEntry need? | Step 0 implementation. Extend based on real query needs. |
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

### Success criteria

| Criterion | Measurement |
|-----------|-------------|
| All 12 skills functional | Manual walkthrough of each primary flow |
| Cross-subsystem query works | `/search` returns from all three subsystems |
| Session timeline reconstructs | `/timeline` with ledger-backed/inferred labels |
| Defer → ticket linkage | Ticket's source_ref traces to originating snapshot |
| Distill → staging → curate pipeline | Full lifecycle works |
| Protected-path enforcement | Direct Write/Edit to `engram/work/` blocked; Bash best-effort; `engram_quality` warns on unauthorized changes |
| Worktree isolation | Two worktrees don't cross-contaminate Context |
| Compatibility harness passes | Work subsystem behavioral equivalence |
| Old plugins removed | No code in `packages/plugins/handoff/` or `packages/plugins/ticket/` |
| SessionStart < 500ms | Cleanup bounded and idempotent |
