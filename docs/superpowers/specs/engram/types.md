---
module: types
status: active
normative: true
authority: data-contract
---

# Core Types

## RecordRef — Lookup Key

Immutable after creation. The universal addressing scheme across all subsystems.

```python
@dataclass(frozen=True)
class RecordRef:
    repo_id: str          # UUIDv4, stored in .engram-id at repo root
    subsystem: str        # "context" | "work" | "knowledge"
    record_kind: str      # Subsystem-specific: "snapshot", "checkpoint", "ticket", "lesson", etc.
    record_id: str        # Subsystem-native ID (snapshot filename, T-YYYYMMDD-NN, lesson_id)
```

## RecordMeta — Provenance

Eager on write, optional for read.

```python
@dataclass(frozen=True)
class RecordMeta:
    worktree_id: str | None    # Disambiguates concurrent worktrees
    session_id: str | None     # Claude session UUID
    schema_version: str        # Contract version (e.g., "1.0")
    visibility: str            # "private" (user-home) | "shared" (repo-local)
```

## Identity Resolution

**`repo_id`:**
- On first use: generate UUIDv4, write to `.engram-id` at repo root, commit it
- On subsequent use: read from `.engram-id`
- Stable across clones and renames (because it's committed). Forks inherit the same `repo_id` — see [fork collision risk](decisions.md#named-risks)

**`worktree_id`:**
- Derived from `git rev-parse --git-dir` — each worktree has a unique `.git` path
- Hashed to a short stable ID for filesystem use
- Context records are isolated per worktree by default

## Envelope Types

All cross-subsystem writes use typed envelopes with a common header. See [envelope invariants](operations.md#envelope-invariants) for behavioral rules.

### EnvelopeHeader

```python
@dataclass(frozen=True)
class EnvelopeHeader:
    envelope_version: str          # "1.0" — target rejects unknown versions explicitly
    source_ref: RecordRef          # Pinned at creation. Never "latest."
    idempotency_key: str           # sha256(canonical_json(idempotency_material)) — see below
    emitted_at: str                # ISO 8601
```

### DeferEnvelope — Context to Work

```python
@dataclass(frozen=True)
class DeferEnvelope:
    header: EnvelopeHeader
    title: str
    problem: str
    context: str | None
    key_file_paths: list[str]
```

### DistillEnvelope — Context to Knowledge (Staging)

```python
@dataclass(frozen=True)
class DistillEnvelope:
    header: EnvelopeHeader
    candidates: list[DistillCandidate]

@dataclass(frozen=True)
class DistillCandidate:
    content: str
    durability: str                # "likely_durable" | "likely_ephemeral" | "unknown"
    source_section: str            # Which snapshot section it came from
    content_sha256: str            # For dedup
```

### PromoteEnvelope — Knowledge to CLAUDE.md (Intent Record)

```python
@dataclass(frozen=True)
class PromoteEnvelope:
    header: EnvelopeHeader
    target_section: str            # Advisory: insertion hint for CLAUDE.md section
    transformed_text: str          # Prescriptive prose, ready to insert
    content_sha256: str            # Hash of source lesson content at envelope creation time
```

## promote-meta — Promotion State Record

Written by the Knowledge engine after a successful CLAUDE.md write. Stored as a `<!-- promote-meta {...} -->` HTML comment in the knowledge entry, immediately after the `lesson-meta` comment.

```python
@dataclass(frozen=True)
class PromoteMeta:
    target_section: str           # Advisory: last requested destination / insertion hint
    promoted_at: str              # ISO 8601
    promoted_content_sha256: str  # Hash of lesson content at promotion time
    transformed_text_sha256: str  # Hash of text between markers (excluding markers themselves)
    lesson_id: str                # Matches lesson-meta lesson_id — used for marker pair identification
```

**Serialization:** All fields are required. Stored as an HTML comment in learnings.md immediately after the entry's `lesson-meta` comment:

```markdown
<!-- promote-meta {"target_section": "## Code Style", "promoted_at": "2026-03-17T14:30:00Z", "promoted_content_sha256": "a1b2c3...", "transformed_text_sha256": "d4e5f6..."} -->
```

Field names match the Python dataclass exactly. All string values. `promoted_at` uses ISO 8601 UTC.

### Promotion Markers in CLAUDE.md

When `/promote` writes transformed text to CLAUDE.md, it wraps the text in paired HTML comment markers:

~~~markdown
<!-- engram:lesson:start:<lesson_id> -->
Promoted text here...
<!-- engram:lesson:end:<lesson_id> -->
~~~

**Marker semantics:**
- Markers are **locator hints**, not authoritative state. `promote-meta` in `learnings.md` remains the authority for Branch A/B/C decisions.
- `lesson_id` in markers matches `lesson-meta.lesson_id` — stable for the life of the lesson.
- User can delete markers. Consequence: reduced automation (degradation to manual reconcile), not invalid system state.
- `transformed_text_sha256` hashes the text **between** markers (excluding markers themselves). Used for drift detection, not location.

**Marker validity rules:**
- One `start` + one `end` with the same `lesson_id`, properly ordered
- Non-nested (no marker pair inside another marker pair)
- Unique per `lesson_id` in the file (at most one pair per lesson)
- Violation of any rule: treat as "markers not found" and fall through to manual reconcile

**Marker loss is expected.** Users edit CLAUDE.md freely. The promote state machine treats marker absence as degraded automation, not an error state. See [Branch C location strategy](operations.md#promote-knowledge-to-claudemd).

**Re-promotion detection:** If a lesson's `content_sha256` changes after promotion, the `PromoteEnvelope` idempotency key changes (because `content_sha256` is part of the material). The engine detects this as a stale promotion: existing `promote-meta.promoted_content_sha256` != current `content_sha256`. `/promote` surfaces stale promotions for user review. `/triage` reports them as a mismatch class alongside the Step-3-failure case.

**`target_section` is advisory.** It records the last requested destination for the promoted text. It is used as an insertion hint for new promotions (Branch A) and as context in the manual reconcile flow. It is **not** the primary locator — marker search is. If the user moves a managed block to a different section, `target_section` becomes stale; `/promote` updates it on the next successful promotion.

## Idempotency and Dedup

Two distinct mechanisms serving different purposes.

### Idempotency — Same Operation Retried

The `idempotency_key` in `EnvelopeHeader` is computed from `canonical_json(idempotency_material)` where the material is envelope-type-specific:

| Envelope | Idempotency Material |
|---|---|
| `DeferEnvelope` | `{source_ref.record_id, title, problem}` |
| `DistillEnvelope` | `{source_ref.record_id, sorted([canonical_json({content_sha256, source_section, durability}), ...], key=lambda c: c["content_sha256"])}` |
| `PromoteEnvelope` | `{source_ref.record_id, target_section, content_sha256}` |

`canonical_json()` sorts keys and normalizes whitespace. Same material produces the same key — target engine returns existing result without side effects.

The `DistillEnvelope` idempotency material includes per-candidate fingerprints to ensure that re-running extraction with improved logic on the same snapshot produces a distinct key when candidate content changes.

### Dedup — Semantically Identical Content

Uses content fingerprints at the record level:
- `DistillCandidate.content_sha256` — deduplicates staged/published knowledge entries by content
- Work engine's existing duplicate detection — `sha256(normalize(problem_text) + sorted(key_file_paths))` fingerprint within a 24-hour window. The fingerprint uses problem content and file paths, not titles.

These mechanisms are independent in purpose and enforcement stage: an idempotent retry (same `idempotency_key`) is caught at the envelope level before dedup is ever checked. A genuinely new operation with coincidentally identical content is caught by dedup, not idempotency.

### Engine Hash Verification

The Knowledge engine **must** recompute `sha256(normalize(content))` for every `DistillCandidate` and verify it matches the caller-provided `content_sha256`. Reject any candidate where the computed hash does not match. This prevents hash drift from corrupting the dedup invariant. Caller provides the hash (self-describing envelopes); engine verifies (trust-but-verify).

## Knowledge Entry Format — lesson-meta Contract

All published knowledge entries in `engram/knowledge/learnings.md` use a uniform format regardless of producer (`/learn` or `/curate`):

```markdown
### YYYY-MM-DD Entry title
<!-- lesson-meta {"lesson_id": "<UUIDv4>", "content_sha256": "<hex>", "created_at": "<ISO8601>", "producer": "learn|curate"} -->

Entry content...
```

**Fields:**
- **`lesson_id`**: UUIDv4 generated at creation. Serves as `RecordRef.record_id` for knowledge entries. Stable across edits (content changes update `content_sha256`, not `lesson_id`).
- **`content_sha256`**: Hash of normalized entry content (excluding the `lesson-meta` comment itself). Used for cross-producer dedup: both `/learn` and `/curate` check `content_sha256` against all existing published entries before writing.
- **`created_at`**: ISO 8601 timestamp of initial creation.
- **`producer`**: Which skill created the entry. Informational — does not affect lifecycle.

The [Knowledge reader](storage-and-indexing.md#readers) parses `### ` headings as entry delimiters and extracts `lesson-meta` JSON from the immediately following HTML comment. Entries lacking `lesson-meta` (legacy or hand-edited) are assigned `record_kind: "legacy"` and are discoverable via query but not addressable by `lesson_id`.

### Format Preservation

Each subsystem keeps its native format. Tickets keep fenced YAML. Snapshots keep `---` frontmatter. Learnings use heading-delimited blocks with `lesson-meta` comments. [NativeReaders](storage-and-indexing.md#nativereader-protocol) parse each format without requiring unification.

## Write Concurrency

Two failure modes for `learnings.md`, two mitigations:

**Same-worktree (local process race):** Two concurrent operations (e.g., `/learn` and `/curate` publish) in the same worktree perform read-modify-write on `learnings.md`. The Knowledge engine's publish path acquires an advisory file lock (`fcntl.flock(LOCK_EX)`) on a lockfile (`learnings.md.lock`, same directory) before reading. Lock held through read, append, write-to-temp, `fsync`, `os.replace`. Lock released after replace completes. Timeout: 5 seconds. On timeout: fail the operation with `"learnings.md is locked by another operation"` — do not queue or retry.

**Cross-worktree (git merge territory):** Each worktree has its own filesystem view. Concurrent appends from different worktrees produce divergent file states resolved by git merge on the shared branch. The Knowledge engine does not attempt cross-worktree coordination — git's line-based merge handles append-only files well. Conflicting appends (rare — requires overlapping content at the same file position) surface as git merge conflicts for the user to resolve.

**Staging files are not affected** — staging uses content-addressed filenames (`content_sha256`-based) with atomic file creation (`O_CREAT | O_EXCL` via `os.open` or equivalent). Identical candidates from concurrent operations coalesce; non-identical candidates get distinct files.
