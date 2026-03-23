---
module: storage-and-indexing
status: active
normative: true
authority: data-contract
---

# Storage and Indexing

## Dual-Root Storage Layout

Two physical locations, one logical namespace.

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
│   ├── YYYY-MM-DD_HH-MM_<slug>.md
│   └── .archive/                    # Archived snapshots (moved by /load chain protocol)
├── checkpoints/                     # Lightweight quicksaves
│   └── YYYY-MM-DD_HH-MM_checkpoint-<slug>.md
├── chain/                           # Session lineage state files (24h TTL)
├── knowledge_staging/               # Distill candidates awaiting review
│   └── YYYY-MM-DD-<hash>.md
├── ledger/                          # Event ledger (default-on, optional)
│   └── <worktree_id>/
│       ├── <session_id>.jsonl       # Per-session, per-worktree sharding
│       └── <session_id>.diag        # Per-session hook failure diagnostics (JSONL)
├── save_recovery.json               # /save recovery manifest (overwritten each invocation)
└── migration_report.json            # Step 4a migration output (overwritten on re-run)
```

`.engram-id` lives at the repo root alongside the `engram/` directory.

## Key Storage Decisions

1. **Learnings remain a single file** (`engram/knowledge/learnings.md`) for MVP. Entries are delimited by `### ` headings and individually addressable via `lesson_id` in [lesson-meta](types.md#knowledge-entry-format--lesson-meta-contract) comments. Individual files are a [deferred optimization](decisions.md#deferred-decisions).

2. **Tickets move from `docs/tickets/` to `engram/work/`**. Git history preserved via `git mv`.

3. **Handoffs move from `~/.claude/handoffs/<project>/` to `~/.claude/engram/<repo_id>/`**. Keyed by `repo_id` instead of project directory name — solves rename and worktree identity collisions. Forks that share `.engram-id` share the same private root; see [fork collision risk](decisions.md#named-risks).

4. **Knowledge staging is private** (`knowledge_staging/` in the private root). Staged candidates are not repo-visible until explicitly published via `/curate`. Each `DistillCandidate` gets its own staging file, named `YYYY-MM-DD-<content_sha256[:16]>.md` (first 16 hex chars of the candidate's `content_sha256`). The `YYYY-MM-DD` prefix is the staging date (UTC, from `staged_at` in the [staging file format](types.md#staging-file-format)) — it aids human readability and chronological sorting but is not part of the dedup key (the `content_sha256` suffix is). This makes `O_CREAT | O_EXCL` coalescing semantics precise — identical candidates from concurrent operations coalesce to the same filename. When `O_CREAT | O_EXCL` fails (file already exists), the engine compares the full `content_sha256` of the existing staging file with the new candidate's `content_sha256`. If they match, this is a genuine duplicate — coalesce (no action). If they differ, this is a hash-prefix collision — write the new candidate with a disambiguating suffix (`-1`, `-2`, etc.) and log a diagnostic. Collision probability with 16 hex chars (64-bit space) is negligible for expected staging volumes (<1000 candidates).

## TTL and Lifecycle

| Artifact | TTL | Location |
|---|---|---|
| Snapshots/checkpoints | 90-day TTL from creation (filename timestamp). [SessionStart](enforcement.md#sessionstart-hook) deletes files older than 90 days. Archived snapshots (`.archive/`) follow the same 90-day TTL. | Private root |
| Chain state files | 24h | Private root |
| Knowledge staging candidates | No TTL (accumulate until curated) | Private root |
| Work items | Permanent until closed | Shared root |
| Published knowledge | Permanent (marked with [promote-meta](types.md#promote-meta--promotion-state-record) when graduated) | Shared root |
| Ledger shards | Append-only, no TTL ([compaction deferred](decisions.md#deferred-decisions)). Sharded per worktree/session. | Private root `ledger/` |

## Visibility Rule

Publication intent, not access control:
- **Private root** = "this is my session state, not project state"
- **Shared root** = "this is project state that belongs in version control"
- The boundary is about what gets committed, not about security

## IndexEntry

The slim discovery type returned by [NativeReaders](#nativereader-protocol). Helps you *find* records — to *use* them, open the native file.

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

**Timezone normalization:** All `datetime` fields in `IndexEntry` are UTC-normalized (`datetime.timezone.utc`). NativeReaders **must** parse ISO 8601 timestamps from source formats and convert to UTC-aware datetime before populating `IndexEntry`. This ensures consistent ordering in `/search`, `/timeline`, and `query(since=...)` across subsystems.

### RecordMeta Field Mapping per Subsystem

| Subsystem | `schema_version` source | `worktree_id` source | `session_id` source | `visibility` |
|---|---|---|---|---|
| Context (snapshot) | `schema_version` in `---` frontmatter | `worktree_id` in `---` frontmatter | `session_id` in `---` frontmatter | `"private"` (always private root) |
| Work (ticket) | `schema_version` in fenced YAML | `worktree_id` in fenced YAML | `session_id` in fenced YAML | `"shared"` (always shared root) |
| Knowledge (lesson) | `meta_version` in `lesson-meta` | N/A (shared root, no worktree scope) | N/A | `"shared"` |

Work ticket YAML schema is inherited from the ticket plugin format — field requirements (`schema_version`, `worktree_id`, `session_id`, `status`) are specified in the RecordMeta field mapping table above.

When `lesson-meta` is present but `meta_version` is absent, populate `RecordMeta.schema_version` with `"0.0"` (pre-versioned sentinel). See [types.md §Legacy Entries](types.md#legacy-entries-missing-meta-version).

Fields marked N/A populate as `None` in `RecordMeta`. The Knowledge reader derives `schema_version` from `lesson-meta.meta_version` (not a separate field). Same-major `lesson-meta` versions (e.g., v1.1 read by a v1.0 reader) are indexed normally — the entry appears in query results and is addressable. Entries with a different major version are skipped with a warning in `QueryDiagnostics.warnings`. See [types.md §Compatibility Rules](types.md#compatibility-rules) for the governing contract.

**Hard rule: No mutation, policy, or lifecycle decisions from `IndexEntry` alone.** IndexEntry is display-only. Any operation that changes state must open the native file through the subsystem engine.

**`snippet` is not `summary`.** It's a preview for display in search results and triage lists. Capped at 200 characters. Reader-extracted (not first-N-chars). Never used for dedup, triage decisions, or workflow logic.

## NativeReader Protocol

Read-only adapters that parse each subsystem's native format into `IndexEntry` for discovery. Readers own both enumeration and parsing.

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

**Reader wiring:** `query.py` instantiates a fixed set of NativeReaders (context, work, knowledge). The `NativeReader` Protocol is a typing contract only — it provides structural subtyping for reader implementations but does not provide registration, discovery, or enforcement. Adding a new reader requires a code change in `query.py`, not a plugin mechanism.

### Readers

Readers live with their subsystems:

```
packages/plugins/engram/
├── engram_core/
│   ├── reader_protocol.py    # NativeReader protocol definition
│   └── query.py              # Discovery + query engine
├── scripts/
│   ├── context/
│   │   └── context_reader.py # Parses --- frontmatter (handoff format)
│   ├── work/
│   │   └── work_reader.py    # Parses fenced yaml (ticket format)
│   └── knowledge/
│       └── knowledge_reader.py # Parses heading-delimited blocks + lesson-meta
```

When the ticket format changes, `work_reader.py` changes with it — in the same subsystem directory.

### Scan Mechanics

The query engine calls `scan()` twice per reader: once with `root_type="shared"`, once with `root_type="private"`. Readers return `[]` for root types they don't handle (e.g., the Work reader returns `[]` for `root_type="private"`). The `root_type` parameter makes this explicit without requiring readers to inspect path structure. The Knowledge reader returns published entries from the shared root and staged entries from the private root, using `record_kind` to distinguish them.

## Query API

### QueryResult

```python
@dataclass(frozen=True)
class QueryDiagnostics:
    scanned_count: int            # Total files found by readers
    matched_count: int            # Files matching filters
    skipped_count: int            # Files that failed to parse
    warnings: list[str]           # Parse errors, reader failures
    degraded_roots: list[str]     # "private" or "shared" if unavailable
    degraded_subsystems: list[str]  # Subsystems where reader scan()/read() raised an exception

@dataclass(frozen=True)
class QueryResult:
    entries: list[IndexEntry]
    diagnostics: QueryDiagnostics
```

Callers can distinguish "no matches" from "17 files failed to parse" from "private root unavailable."

### Query Signature

```python
def query(
    subsystems: list[str] | None = None,
    status: str | None = None,        # "work:open", "knowledge:published", etc.
    tags: list[str] | None = None,
    text: str | None = None,          # Searches title + snippet + tags
    since: datetime | None = None,
    session_id: str | None = None,
) -> QueryResult: ...
```

### Namespaced Status Filtering

Status filters use `subsystem:value` format (e.g., `"work:open"`, `"knowledge:published"`). `IndexEntry.status` stores subsystem-native bare values (e.g., `"open"`, `"published"`). The query engine splits the prefix, routes to the correct reader, and matches against bare status.

When `subsystems` is set to a single value, bare status is auto-prefixed as a convenience (e.g., `query(subsystems=["work"], status="open")` is equivalent to `status="work:open"`). Bare status with multiple or no subsystems is rejected — no implicit cross-subsystem status normalization.

### Status Vocabulary

| Subsystem | Bare Values |
|---|---|
| `work` | `open`, `in_progress`, `closed`, `blocked` |
| `knowledge` | `staged`, `published` |
| `context` | `active`, `archived` |

Bare values are subsystem-native. The query engine prefixes with `subsystem:` for cross-subsystem filtering. Context status is determined by path structure: snapshots in `snapshots/.archive/` have status `archived`; all others have status `active`. The Context reader uses path-based status derivation (not a frontmatter field).

### Text Search Semantics

The `query()` `text` parameter searches `title`, `snippet`, and `tags` fields of each `IndexEntry`:

- **Case-insensitive:** All comparisons use Unicode case-folded values.
- **Tokenization:** Split on whitespace and punctuation boundaries. `"auth middleware"` produces tokens `["auth", "middleware"]`.
- **Multi-token behavior:** AND — all tokens must match somewhere across the searched fields. A token matching in `title` and another in `tags` satisfies the query.
- **Matching:** Substring within tokens. `"auth"` matches `"authentication"`. Exact-match is not required.
- **Ordering within subsystem groups:** `created_at` descending (newest first). Deterministic — no relevance ranking in v1.

Ranking (BM25, TF-IDF, recency-weighted scoring) is [deferred](decisions.md#deferred-decisions). The current ordering is simple and predictable.

## Fresh Scan — No Cached Index

Every query does a fresh filesystem scan via `reader.scan()` + `reader.read()`. No `index.json`, no cache invalidation, no read-after-write races. At MVP scale (~100s of files), this is fast. [Incremental indexing is deferred](decisions.md#deferred-decisions).

`git log` is **not** part of the `query()` hot path. The [/timeline](operations.md#session-timeline) operation calls `git log` separately, bounded by session time window.

## Ledger

Architecturally optional, operationally default-on. Sharded as `ledger/<worktree_id>/<session_id>.jsonl` in private root. Each line is a [LedgerEntry](types.md#ledgerentry--event-record) JSON object.

**Producers:** Engines and orchestrators append completion events post-commit. The `engram_register` hook appends observational events for Write/Edit tool calls. See [producer classes](types.md#producer-classes) for the distinction and its impact on timeline labels.

**Sharding:** Per worktree and session. Multi-producer writes to the same shard are coordinated via a [shared locked append primitive](types.md#write-semantics).

Session timeline reconstructs from:
1. `created_at` timestamps from `IndexEntry` (parsed during scan)
2. `session_id` in `RecordMeta` to group records by session
3. Ledger events matching `session_id` (engine/orchestrator events are "ledger-backed")
4. `git log` for shared-root change attribution (called once per timeline request, not per query)

No ledger means timeline still works but at lower fidelity (no completion evidence, no sub-file-creation event granularity). This is a documented trade-off, not a silent degradation.

## Degradation Model

| Condition | Behavior | User Visibility |
|---|---|---|
| Private root unavailable | Context queries return empty | `diagnostics.degraded_roots = ["private"]` |
| Shared root unavailable | Work + Knowledge return empty | `diagnostics.degraded_roots = ["shared"]` |
| Reader fails to parse a file | Skip file, add to warnings | `diagnostics.skipped_count > 0` |
| Reader `scan()` or `read()` raises unhandled exception | Catch, skip that reader's entire subsystem, add to `degraded_subsystems` and `warnings` | `diagnostics.degraded_subsystems` includes subsystem name. `diagnostics.warnings` includes subsystem name and error message. `diagnostics.skipped_count` is not incremented (file-level metric). Other subsystems' results are unaffected. |
| Both roots unavailable | All queries return empty | Skills report "Engram storage unavailable" |
| No ledger | Timeline uses file timestamps only. `/triage` inference cases (3) and (4) [collapse](operations.md#triage-read-work-and-context): zero-output success becomes indistinguishable from incomplete execution. All collapsed cases carry `reason=ledger_disabled` qualifier. | Lower fidelity timeline. `/triage` reports `completion not proven (ledger unavailable)` instead of distinguishing zero-output success. Policy: `ledger.enabled=false` is supported for storage and basic query, but unsupported for production-grade `/triage` completion inference. |
