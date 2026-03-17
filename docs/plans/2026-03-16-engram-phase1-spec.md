# Engram Phase 1: Shared Core Library + Search Plugin

**Date:** 2026-03-16
**Status:** Design (pre-implementation)
**Depends on:** ADR `docs/decisions/2026-03-16-engram-oc2-augmented-path.md`
**Proof of concept:** `docs/plans/2026-03-16-engram-architecture-proof.md`

---

## Overview

Phase 1 delivers the shared-contracts half of the Engram design: a common identity system, typed records, NativeReaders for all three subsystems, and a cross-subsystem search/timeline plugin. The existing plugins (handoff, ticket, learning) remain independent. No plugin is deleted. The ticket engine is untouched.

**What ships:**
1. `engram_core` — shared library (identity, types, reader protocol, query engine)
2. NativeReaders — read-only adapters for handoff, ticket, and learning formats
3. Context identity retrofit — re-key handoff storage from project-name to repo_id
4. `engram-search` plugin — `/search` and `/timeline` skills

**What doesn't ship (deferred to Phase 2):**
- Plugin consolidation (merging handoff + ticket + learning into one plugin)
- Unified hooks (`engram_guard`, `engram_quality`, `engram_register`, `engram_session`)
- `/save` orchestration of defer + distill
- `/curate` skill
- Ledger (`ledger.jsonl`)

---

## Section 1: `engram_core` Library

### Package structure

```
packages/plugins/engram-core/
├── engram_core/
│   ├── __init__.py
│   ├── identity.py          # repo_id + worktree_id resolution
│   ├── types.py             # RecordRef, RecordMeta, RecordStub, RecordPreview
│   ├── reader_protocol.py   # NativeReader protocol definition
│   └── query.py             # Discovery + query engine
├── tests/
│   ├── test_identity.py
│   ├── test_types.py
│   ├── test_reader_protocol.py
│   └── test_query.py
└── pyproject.toml
```

`engram_core` is a **standalone package** in the uv workspace, not nested inside another plugin. This is the approach proven by the architecture proof — any plugin's hooks and scripts can import it via `sys.path.insert(0, engram_core_path)`.

### Import pattern

All consumers (hooks, scripts, tests) use the dual-resolution pattern proven in the architecture proof and established by the ticket guard:

```python
import os
import sys
from pathlib import Path

# Prefer CLAUDE_PLUGIN_ROOT env var, fall back to __file__ resolution
_plugin_root = os.environ.get(
    "CLAUDE_PLUGIN_ROOT",
    str(Path(__file__).parent.parent),
)
# engram_core is a sibling package or installed in the workspace
sys.path.insert(0, _plugin_root)

from engram_core.identity import resolve_identity
from engram_core.types import RecordRef
```

For the `engram-search` plugin, `engram_core` is a workspace dependency declared in `pyproject.toml`. For existing plugins (handoff, ticket), it's imported via `sys.path` pointing at the `engram_core` package location.

### Identity resolution

```python
# identity.py

def resolve_repo_id(repo_root: Path) -> str:
    """Read .engram-id at repo root. Create and commit if missing."""

def resolve_worktree_id() -> str | None:
    """Derive from git rev-parse --git-dir, hashed to 12-char hex."""

def resolve_identity(repo_root: Path) -> RepoIdentity:
    """Full identity: repo_id + worktree_id."""
```

**`.engram-id` creation protocol:**
1. Check if `.engram-id` exists at repo root → read and return
2. Generate UUIDv4, write to `.engram-id`
3. Stage the file: `git add .engram-id`
4. Do **not** auto-commit. The file will be included in the user's next commit.
5. If staging fails (detached HEAD, rebase in progress, pre-commit hook): warn, continue. The file is still usable even unstaged.

**Worktree identity:**
- Derived from `git rev-parse --git-dir` → SHA-256 → first 12 hex chars
- Each worktree has a unique `.git` path, producing a unique worktree_id
- Worktree deletion orphans context data (known, documented trade-off)
- Worktree recreation at same path produces a **new** worktree_id (git-dir-based, not path-based)

### Core types

```python
# types.py

@dataclass(frozen=True)
class RecordRef:
    """Lookup key — immutable after creation."""
    repo_id: str          # UUIDv4 from .engram-id
    subsystem: str        # "context" | "work" | "knowledge"
    record_kind: str      # Subsystem-specific: "snapshot", "checkpoint", "ticket", "lesson"
    record_id: str        # Subsystem-native ID

@dataclass(frozen=True)
class RecordMeta:
    """Provenance — eager on write, optional for read."""
    worktree_id: str | None
    session_id: str | None
    schema_version: str
    visibility: str       # "private" | "shared"

@dataclass(frozen=True)
class RecordStub:
    """Machine-facing record summary. No freeform text fields.
    Used by query engine, triage logic, and cross-subsystem operations."""
    ref: RecordRef
    meta: RecordMeta
    title: str
    created_at: datetime
    updated_at: datetime | None
    status: str | None
    tags: list[str]
    source_path: str

@dataclass(frozen=True)
class RecordPreview:
    """Display-facing record with optional snippet. Never used for
    dedup, triage decisions, or workflow logic."""
    stub: RecordStub
    snippet: str          # Reader-extracted preview, max 200 chars
```

**RecordStub vs RecordPreview (response to review finding F4):**

The original spec's `IndexEntry` combined machine-facing metadata with a freeform `snippet` field, creating shadow authority risk — skills would naturally reason from the snippet text rather than opening native files.

The split enforces a structural boundary:
- `RecordStub` is the default query return. No freeform text to reason from.
- `RecordPreview` wraps a stub with a snippet. Only used for display (search result lists, triage dashboards).
- Query API: `query(..., include_preview=False)` is the default. Skills that need display text opt in explicitly.

### Reader protocol

```python
# reader_protocol.py

class NativeReader(Protocol):
    subsystem: str

    def scan(self, root: Path) -> list[Path]:
        """List all files this reader claims. Reader owns path conventions."""
        ...

    def can_read(self, path: Path) -> bool:
        """Route by directory path, not file content."""
        ...

    def read(self, path: Path) -> RecordStub:
        """Parse native format into RecordStub. Raises ReaderError on failure."""
        ...

    def read_preview(self, path: Path) -> RecordPreview:
        """Parse native format into RecordPreview (stub + snippet)."""
        ...

    # No write(). By design.
```

Readers return `RecordStub` by default. `read_preview()` is a separate method, called only when display text is needed.

### Query engine

```python
# query.py

@dataclass(frozen=True)
class QueryDiagnostics:
    scanned_count: int
    matched_count: int
    skipped_count: int
    warnings: list[str]
    degraded_roots: list[str]    # "private" or "shared" if unavailable

@dataclass(frozen=True)
class QueryResult:
    entries: list[RecordStub]    # RecordStub by default
    diagnostics: QueryDiagnostics

def query(
    readers: list[NativeReader],
    roots: dict[str, Path],      # {"private": Path, "shared": Path}
    *,
    subsystems: list[str] | None = None,
    status: str | None = None,   # "ticket:open", "learning:promoted", etc.
    tags: list[str] | None = None,
    text: str | None = None,     # Searches title + tags
    since: datetime | None = None,
    session_id: str | None = None,
    include_preview: bool = False,
) -> QueryResult:
    """Fresh-scan query across all registered readers."""
```

**No cached index.** Every query does a fresh filesystem scan via `reader.scan()` + `reader.read()`. At MVP scale (~100s of files), this is fast. Instrument latency from Step 0.

**Status filtering:** Uses `subsystem:value` format. Bare status without prefix rejected unless `subsystems` is a single value.

**Text search:** Searches `title` and `tags` only (not snippet). When `include_preview=True`, snippet is populated but still not searched — this prevents snippet content from influencing query results.

**Degradation model:** Same as original spec. Private root unavailable → context queries return empty with `degraded_roots=["private"]`. Reader parse failures → skip file, increment `skipped_count`, add warning.

---

## Section 2: NativeReaders

Three readers, each parsing its subsystem's native format into `RecordStub`. Readers live in their respective plugin packages, not in `engram_core`.

### Context reader (handoff plugin)

```
packages/plugins/handoff/scripts/context_reader.py
```

**Parses:** `---` YAML frontmatter from handoff files.

**Scan roots:**
- Snapshots: `~/.claude/engram/<repo_id>/snapshots/` (post-retrofit)
- Checkpoints: `~/.claude/engram/<repo_id>/checkpoints/` (post-retrofit)
- Legacy: `~/.claude/handoffs/<project>/` (backward-compatible read)

**Field mapping:**

| RecordStub field | Source |
|-----------------|--------|
| `ref.subsystem` | `"context"` |
| `ref.record_kind` | `"snapshot"` or `"checkpoint"` (from filename pattern) |
| `ref.record_id` | Filename stem |
| `title` | Frontmatter `title` |
| `created_at` | Frontmatter `created_at` or `date` + `time` |
| `status` | `None` (context records have no status) |
| `tags` | `[]` (context records have no tags) |
| `source_path` | Absolute path to file |
| `snippet` (preview) | First non-empty section heading + first 200 chars of content |

**Legacy support:** The reader scans both old (`~/.claude/handoffs/<project>/`) and new (`~/.claude/engram/<repo_id>/`) locations. Old files are read-only — no writes to old paths. This provides a backward-compatible read window during and after migration.

### Work reader (ticket plugin)

```
packages/plugins/ticket/scripts/work_reader.py
```

**Parses:** Fenced YAML frontmatter from ticket files.

**Scan roots:**
- Active: `docs/tickets/` (current location — unchanged)
- Archived: `docs/tickets/closed-tickets/`

**Field mapping:**

| RecordStub field | Source |
|-----------------|--------|
| `ref.subsystem` | `"work"` |
| `ref.record_kind` | `"ticket"` |
| `ref.record_id` | Frontmatter `id` (e.g., `T-20260316-01`) |
| `title` | First `# heading` or frontmatter `id` |
| `created_at` | Frontmatter `date` |
| `status` | Frontmatter `status` (e.g., `"open"`, `"closed"`) |
| `tags` | Frontmatter `blocked_by` + `blocks` + `related` (as reference tags) |
| `source_path` | Absolute path to file |
| `snippet` (preview) | First 200 chars of Problem section |

**No changes to ticket storage.** The work reader is read-only. Tickets stay at `docs/tickets/`. The ticket engine is untouched.

### Knowledge reader (learning pipeline)

```
packages/plugins/handoff/scripts/knowledge_reader.py
```

**Parses:** Markdown entries from `docs/learnings/learnings.md`.

**Scan roots:**
- `docs/learnings/learnings.md` (single file)

**Special handling:** Unlike the other readers, the knowledge reader parses a single file containing multiple entries. Each `### YYYY-MM-DD [tags]` heading is one record.

**Field mapping:**

| RecordStub field | Source |
|-----------------|--------|
| `ref.subsystem` | `"knowledge"` |
| `ref.record_kind` | `"lesson"` |
| `ref.record_id` | `YYYY-MM-DD-<tag_hash>` (date + hash of first tag for uniqueness) |
| `title` | Entry heading (date + tags) |
| `created_at` | Parsed from heading date |
| `status` | `"promoted"` if `promote-meta` present, `"published"` otherwise |
| `tags` | Parsed from `[tag1, tag2, ...]` in heading |
| `source_path` | `docs/learnings/learnings.md` (same for all entries) |
| `snippet` (preview) | First 200 chars of entry body |

---

## Section 3: Context Identity Retrofit

Re-key handoff storage from project-name to repo_id. Scoped to 22 non-test references across 5 files (per Gate 3 assessment).

### Changes

**`project_paths.py` → `identity_paths.py`:**

```python
# Before
def get_project_name() -> tuple[str, str]:
    """Get project name from git root directory."""
    ...
    return Path(result.stdout.strip()).name, "git"

def get_handoffs_dir() -> Path:
    return Path.home() / ".claude" / "handoffs" / name

# After
def get_repo_id() -> str:
    """Get repo_id from .engram-id, creating if needed."""
    from engram_core.identity import resolve_repo_id
    repo_root = _find_repo_root()
    return resolve_repo_id(repo_root)

def get_handoffs_dir() -> Path:
    return Path.home() / ".claude" / "engram" / get_repo_id() / "snapshots"

def get_checkpoints_dir() -> Path:
    return Path.home() / ".claude" / "engram" / get_repo_id() / "checkpoints"

def get_chain_dir() -> Path:
    return Path.home() / ".claude" / "engram" / get_repo_id() / "chain"
```

**`cleanup.py`:** Update `get_project_name()` → `get_repo_id()`, update path construction.

**`search.py`:** Update imports and output metadata fields.

**Skill docs (2 files):** Update path references in `save/SKILL.md` and `load/SKILL.md`.

### Legacy data

**No bulk migration.** Old handoff files remain at `~/.claude/handoffs/<project>/`. The context reader scans both old and new locations. New saves write to the new location. Old data is accessible but read-only.

**Chain state:** Old chain state files at `~/.claude/.session-state/handoff-*` remain functional during transition. New chain state writes to `~/.claude/engram/<repo_id>/chain/`. If a session was saved before retrofit but loaded after, the load skill checks both old and new locations.

### Storage layout (post-retrofit)

```
~/.claude/engram/<repo_id>/
├── snapshots/                   # Full session handoffs (was: ~/.claude/handoffs/<project>/)
│   └── YYYY-MM-DD_HH-MM_<slug>.md
├── checkpoints/                 # Lightweight quicksaves
│   └── YYYY-MM-DD_HH-MM_checkpoint-<slug>.md
├── chain/                       # Session lineage state files (24h TTL)
└── knowledge_staging/           # Reserved for Phase 2 /curate
```

---

## Section 4: `engram-search` Plugin

A thin plugin providing cross-subsystem search and timeline.

### Package structure

```
packages/plugins/engram-search/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   ├── search/
│   │   └── SKILL.md            # /search skill
│   └── timeline/
│       └── SKILL.md            # /timeline skill
├── scripts/
│   ├── search.py               # Cross-subsystem search
│   └── timeline.py             # Session timeline reconstruction
└── pyproject.toml              # Depends on engram_core
```

### `/search` skill

```
/search "auth middleware"
    → Load all registered readers
    → query(readers, roots, text="auth middleware")
    → QueryResult with entries grouped by subsystem
    → Display results with RecordPreview (include_preview=True)
    → User selects entry → open native file
```

Results are grouped by subsystem, never interleaved. Display uses `RecordPreview` for snippet context.

### `/timeline` skill

```
/timeline [session_id]
    → query(readers, roots, session_id=<id>)
    → All RecordStubs from that session
    → git log --since=<session_start> for shared-root changes
    → Merge and sort chronologically
    → Events labeled as "file-timestamp" (no ledger in Phase 1)
    → Causal links via source_ref fields where available
    → Legacy artifacts lacking session_id appear under "unattributed"
```

**Phase 1 limitation:** Without a ledger, timeline uses file timestamps only. This is documented, not silent — events are labeled `"file-timestamp"` rather than `"ledger-backed"`. Sub-file-creation granularity is not available.

### Reader registration

In Phase 1, readers are hardcoded in the search plugin:

```python
READERS = [
    ContextReader(),    # From handoff plugin
    WorkReader(),       # From ticket plugin
    KnowledgeReader(),  # From handoff plugin (or learning skill)
]
```

Three readers is fine for Phase 1. Manifest-based discovery is a Phase 2 optimization if more subsystems emerge.

### Root resolution

```python
def resolve_roots(repo_id: str) -> dict[str, Path]:
    return {
        "private": Path.home() / ".claude" / "engram" / repo_id,
        "shared": _find_repo_root(),  # git rev-parse --show-toplevel
    }
```

---

## Section 5: Typed Envelopes

Upgrade the existing `DeferredWorkEnvelope` to use `RecordRef`-based source tracking and idempotency keys. This is lower priority than identity/readers/search (per dialogue ordering) but still Phase 1 scope.

### Envelope header

```python
@dataclass(frozen=True)
class EnvelopeHeader:
    envelope_version: str      # "1.0"
    source_ref: RecordRef      # Pinned at creation. Never "latest."
    idempotency_key: str       # sha256(source_ref.record_id + content_hash)
    emitted_at: str            # ISO 8601
```

### DeferEnvelope (Context → Work)

Replaces the existing `DeferredWorkEnvelope` in `ticket_envelope.py`:

```python
@dataclass(frozen=True)
class DeferEnvelope:
    header: EnvelopeHeader
    title: str
    problem: str
    context: str | None
    key_file_paths: list[str]
```

**Backward compatibility:** The ticket engine's `ingest` subcommand must accept both old (`DeferredWorkEnvelope`) and new (`DeferEnvelope`) formats during transition. Version detection via presence of `header` field.

### Idempotency

The ticket engine's ingest pipeline adds idempotency checking:
- On ingest: compute `idempotency_key` from envelope
- Check against existing tickets (scan `defer-meta` in ticket frontmatter)
- If duplicate: return existing ticket ref, no side effects
- If new: proceed through normal pipeline

This is a targeted change to the ticket engine's ingest path, not a rewrite.

---

## Section 6: Build Sequence

Priority ordering from Codex dialogue: **importability > identity > readers > search > envelopes**.

### Step 0: engram_core package

Create the shared library. Validate the foundation.

| Deliverable | Detail |
|-------------|--------|
| Package | `packages/plugins/engram-core/` with `pyproject.toml`, added to uv workspace |
| `identity.py` | repo_id resolution (read/create `.engram-id`), worktree_id derivation |
| `types.py` | RecordRef, RecordMeta, RecordStub, RecordPreview |
| `reader_protocol.py` | NativeReader protocol, QueryResult, QueryDiagnostics |
| `query.py` | Fresh-scan query engine with degradation model |
| `.engram-id` | Generated and staged at repo root |

**Exit criteria:**
- Identity works across worktrees (test in current repo)
- Query scans empty directories with correct diagnostics
- All types pass construction, equality, and frozen tests
- Import works from a simulated installed-cache path (repeat architecture proof with real package)
- Tests pass: `uv run --package engram-core pytest`

### Step 1: NativeReaders

Build read-only adapters for all three subsystems.

| Deliverable | Detail |
|-------------|--------|
| `context_reader.py` | In handoff plugin. Parses `---` frontmatter. Scans old + new paths. |
| `work_reader.py` | In ticket plugin. Parses fenced YAML. Scans `docs/tickets/`. |
| `knowledge_reader.py` | In handoff plugin. Parses `### date [tags]` entries from learnings.md. |

**Exit criteria:**
- Each reader parses all existing files in its subsystem without errors
- `query(readers, roots)` returns entries from all three subsystems
- Reader parse failures produce warnings in diagnostics, not exceptions
- Context reader finds files in both old and new handoff locations
- Knowledge reader handles entries with and without `promote-meta`/`distill-meta`

### Step 2: Context identity retrofit

Re-key handoff storage from project-name to repo_id.

| Deliverable | Detail |
|-------------|--------|
| `identity_paths.py` | Replaces `project_paths.py`. Uses `engram_core.identity`. |
| `cleanup.py` updates | New path construction, both old + new locations for cleanup |
| `search.py` updates | New imports, updated metadata fields |
| SKILL.md updates | Path references in save/load skills |
| Legacy read path | Context reader scans old location for backward compat |
| Chain state migration | New chain state at `~/.claude/engram/<repo_id>/chain/`, load checks both |

**Exit criteria:**
- `/save` writes to `~/.claude/engram/<repo_id>/snapshots/`
- `/load` reads from new location, falls back to old location
- `/quicksave` writes to `~/.claude/engram/<repo_id>/checkpoints/`
- Cleanup operates on both old and new locations
- All handoff tests pass with updated fixtures
- Legacy handoff files from old location appear in search results

### Step 3: engram-search plugin

Cross-subsystem search and timeline.

| Deliverable | Detail |
|-------------|--------|
| Plugin scaffold | `packages/plugins/engram-search/` with manifest |
| `/search` skill | Cross-subsystem text search with grouped results |
| `/timeline` skill | Session reconstruction from file timestamps + git log |
| Reader registration | Hardcoded three readers |

**Exit criteria:**
- `/search "keyword"` returns results from all three subsystems
- Results grouped by subsystem, displayed with RecordPreview snippets
- `/timeline` reconstructs a session from file timestamps
- Diagnostics report degraded roots when private/shared storage unavailable
- Plugin installable via marketplace

### Step 4: Typed envelopes

Upgrade defer envelope with RecordRef linkage and idempotency.

| Deliverable | Detail |
|-------------|--------|
| `DeferEnvelope` | In `ticket_envelope.py`, replaces `DeferredWorkEnvelope` |
| `EnvelopeHeader` | In `engram_core/types.py` |
| Ingest idempotency | Ticket engine deduplicates by idempotency_key |
| Backward compat | Ingest accepts both old and new envelope formats |

**Exit criteria:**
- `/defer` emits `DeferEnvelope` with `RecordRef` source linkage
- Idempotent: same envelope retried → same ticket ref, no side effects
- Old `DeferredWorkEnvelope` format still accepted during transition
- Ticket created via defer has `source_ref` traceable to originating snapshot
- All existing defer tests pass

---

## Section 7: Testing Strategy

### Per-step testing

Each step has its own test suite. No step depends on a later step's tests passing.

### Reader contract tests

A shared test fixture validates that all three readers conform to the NativeReader protocol:
- `scan()` returns a list of Paths
- `can_read()` returns True for files in its subsystem's directories
- `read()` returns a valid RecordStub with all required fields populated
- `read_preview()` returns a RecordPreview with snippet ≤ 200 chars
- Parse failures raise `ReaderError`, not arbitrary exceptions

### Context retrofit regression tests

The handoff plugin's existing test suite must continue passing with the updated path logic. Test fixtures updated to use repo_id-based paths, but test coverage preserved.

### Integration test: cross-subsystem query

After Step 1, an integration test queries across all three subsystems using fixture data and verifies:
- Results from all three readers present
- Diagnostics accurate (scanned_count, matched_count)
- Status filtering uses namespaced format (`ticket:open`, not bare `open`)
- Text search matches title and tags, not snippet

---

## Section 8: Risks and Open Questions

### Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Fresh-scan latency at scale | Low | Instrument query latency from Step 0. Threshold: 200ms. |
| Reader parse failures on edge-case files | Low | Degradation model: skip + warn. No query-blocking failures. |
| `.engram-id` conflicts across forks | Low | UUIDv4 collision probability negligible. Forks get their own IDs. |
| Static analysis (Pyright) warnings on dynamic imports | Low | Known limitation. Add `# type: ignore[import-not-found]` where needed. |

### Open questions

| Question | When to resolve |
|----------|-----------------|
| Should `engram_core` be a workspace member or a vendored package? | Step 0. Workspace member is the default; vendor only if marketplace constraints require it. |
| How should `/search` handle the handoff plugin being uninstalled? | Step 3. Reader registration should degrade gracefully (skip missing readers). |
| Should the `DistillEnvelope` be added in Phase 1 or deferred? | Step 4. Defer unless the distill pipeline needs idempotency before Phase 2. |

### Success criteria

| Criterion | Measurement |
|-----------|-------------|
| `engram_core` importable from all contexts | Architecture proof repeated with real package |
| All 3 readers parse existing data | Zero parse failures on current repo data |
| Context identity retrofit complete | `/save` + `/load` cycle works with repo_id paths |
| Cross-subsystem search works | `/search` returns from all three subsystems |
| Timeline reconstruction works | `/timeline` shows session events with file-timestamp labels |
| RecordStub has no snippet | Type definition verified, query default is `include_preview=False` |
| Defer idempotency works | Same envelope retried → same result |
| Existing test suites pass | Handoff (354) + ticket (596) tests green |
| No plugin deleted | handoff, ticket, learning pipeline all still functional |
