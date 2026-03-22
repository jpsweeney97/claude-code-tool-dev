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

    def to_str(self) -> str: ...    # "<subsystem>/<record_kind>/<record_id>"
    def from_str(s: str) -> RecordRef: ...  # Inverse of to_str
```

**Canonical serialization:** `<subsystem>/<record_kind>/<record_id>` (`repo_id` omitted — implicit from context). Used in `LedgerEntry.record_ref`, event vocabulary payloads, idempotency material, and recovery manifests. Implemented as `RecordRef.to_str()` / `RecordRef.from_str()` in `engram_core/types.py`.

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
- Hashed: `sha256(git_dir_path.encode())[:16]` (first 16 hex chars). Implemented solely in `engram_core/identity.py` via `identity.get_worktree_id()`. All hooks and engines must call this function — never re-derive locally.
- Context records are isolated per worktree by default

## Envelope Types

All cross-subsystem writes use typed envelopes with a common header. See [envelope invariants](operations.md#envelope-invariants) for behavioral rules.

### EnvelopeHeader

```python
@dataclass(frozen=True)
class EnvelopeHeader:
    envelope_version: str          # "1.0" — target rejects unknown versions explicitly
    source_ref: RecordRef          # Pinned at creation. Never "latest."
    idempotency_key: Sha256Hex     # sha256(canonical_json_bytes(material)) — see Hash Types and Helpers
    emitted_at: str                # ISO 8601 UTC (suffix Z or +00:00)
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

### DistillEnvelope — Context to Knowledge (Staged)

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
    content_sha256: Sha256Hex      # content_hash(content) — for dedup
```

### PromoteEnvelope — Knowledge to CLAUDE.md (Intent Record)

```python
@dataclass(frozen=True)
class PromoteEnvelope:
    header: EnvelopeHeader
    target_section: str            # Advisory: insertion hint for CLAUDE.md section
    transformed_text: str          # Prescriptive prose, ready to insert
    content_sha256: Sha256Hex      # content_hash(lesson_content) at envelope creation time
```

## promote-meta — Promotion State Record

Written by the Knowledge engine after a successful CLAUDE.md write. Stored as a `<!-- promote-meta {...} -->` HTML comment in the knowledge entry, immediately after the `lesson-meta` comment.

```python
@dataclass(frozen=True)
class PromoteMeta:
    meta_version: str             # "1.0" — see Version Evolution Policy
    target_section: str           # Advisory: last requested destination / insertion hint
    promoted_at: str              # ISO 8601
    promoted_content_sha256: Sha256Hex  # content_hash(lesson_content) at promotion time
    transformed_text_sha256: Sha256Hex  # drift_hash(text_between_markers) — drift sentinel
    lesson_id: str                # Matches lesson-meta lesson_id — used for marker pair identification
```

**`meta_version`**: Version of the promote-meta format. Currently `"1.0"`. Entries lacking this field are treated as `legacy`. See [Version Evolution Policy](#version-evolution-policy) for entry-level exact-match semantics and field preservation requirements.

**Serialization:** All fields are required. `promote-meta` (and `lesson-meta`) JSON is serialized with `sort_keys=True`. Stored as an HTML comment in learnings.md immediately after the entry's `lesson-meta` comment:

```markdown
<!-- promote-meta {"lesson_id": "550e8400-e29b-41d4-a716-446655440000", "meta_version": "1.0", "promoted_at": "2026-03-17T14:30:00Z", "promoted_content_sha256": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2", "target_section": "## Code Style", "transformed_text_sha256": "d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5"} -->
```

Field names match the Python dataclass exactly (alphabetically sorted in serialized form). All string values. `promoted_at` uses ISO 8601 UTC.

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
- `transformed_text_sha256` is computed by [`drift_hash()`](#hash-producing-functions) on the text **between** markers (excluding markers themselves). Used for [drift detection in Branch C](operations.md#promote-knowledge-to-claudemd), not location.

**Marker validity rules:**
- One `start` + one `end` with the same `lesson_id`, properly ordered
- Non-nested (no marker pair inside another marker pair)
- Unique per `lesson_id` in the file (at most one pair per lesson)
- Violation of any rule: treat as "markers not found" and fall through to manual reconcile

**Marker loss is expected.** Users edit CLAUDE.md freely. The promote state machine treats marker absence as degraded automation, not an error state. See [Branch C location strategy](operations.md#promote-knowledge-to-claudemd).

**Re-promotion detection:** If a lesson's `content_sha256` changes after promotion, the `PromoteEnvelope` idempotency key changes (because `content_sha256` is part of the material). The engine detects this as a stale promotion: existing `promote-meta.promoted_content_sha256` != current `content_sha256`. `/promote` surfaces stale promotions for user review. `/triage` reports them as a mismatch class alongside the promote Step 3 failure case (see [Failure Handling](operations.md#failure-handling)).

**`target_section` is advisory.** It records the last requested destination for the promoted text. It is used as an insertion hint for new promotions (Branch A) and as context in the manual reconcile flow. It is **not** the primary locator — marker search is. If the user moves a managed block to a different section, `target_section` becomes stale; `/promote` updates it on the next successful promotion.

## Hash Types and Helpers

### Scalar Types

| Type | Pattern | Usage |
|---|---|---|
| `Sha256Hex` | `^[0-9a-f]{64}$` | All `*_sha256` fields — bare lowercase hex, no algorithm prefix |
| `HashId` | `sha256:` + `Sha256Hex` | Algorithm-tagged identifiers (e.g., `source_uid`). Not used for `*_sha256` fields. |

**Rationale:** The algorithm is encoded in the field name (`content_sha256`, `promoted_content_sha256`), making a `sha256:` prefix redundant. `HashId` is reserved for identifier fields where the algorithm is not implied by the name. **Exception:** `idempotency_key` is typed `Sha256Hex` despite lacking the `_sha256` suffix — its computation formula (`sha256(canonical_json_bytes(...))`) is documented at the point of use in [Idempotency](#idempotency-same-operation-retried).

**`parse_sha256_hex(value: str) -> Sha256Hex`:** Strict parser. Accepts bare lowercase hex (`^[0-9a-f]{64}$`) or exact lowercase `sha256:` prefix (strips prefix, returns bare hex). Rejects uppercase hex, uppercase prefix, and non-`sha256` algorithm prefixes. During the bridge period ([Step 1](delivery.md#step-1-bridge-cutover) through [Step 3](delivery.md#step-3-work-cutover)), readers accept both formats; writers always emit bare hex.

### Normalization Functions

Two normalization families serve different content types. Using the wrong normalizer produces different hashes — the distinction is intentional.

| Function | Purpose | When to Use |
|---|---|---|
| `knowledge_normalize(text) -> str` | Light normalization for multi-paragraph markdown content | Knowledge entry content, distill candidates |
| `work_normalize(text) -> str` | Aggressive normalization for short problem descriptions | Work engine dedup fingerprints |

**`knowledge_normalize` rules (v1):**

1. Unicode NFC normalization
2. Line endings to `\n` (LF)
3. Strip trailing whitespace per line
4. Whitespace-only lines become blank lines (empty `\n`)
5. Collapse 2+ consecutive blank lines to exactly 1
6. Strip leading and trailing blank lines from the document
7. Preserve intra-line spaces (no collapse)
8. No lowercasing
9. No punctuation removal
10. Fence-aware: content inside fenced code blocks (backtick or tilde) is subject only to rules 1–2 (NFC + LF). Rules 3–6 do not apply inside fences.

**Fence detection (CommonMark-aligned):**
- Opening fence: 3+ identical characters (`` ` `` or `~`), preceded by 0–3 spaces of indentation
- Closing fence: same character, same or greater length, preceded by 0–3 spaces of indentation
- No nested fences — the first valid closing fence ends the block
- Indented code blocks (4+ spaces) are not treated as fences in v1

**`work_normalize` rules:** The existing 5-step pipeline from `ticket_dedup.py`:

1. Strip leading/trailing whitespace
2. Collapse internal whitespace runs to single space
3. Lowercase
4. Remove punctuation (keep alphanumeric, spaces, hyphens, underscores)
5. Unicode NFC normalization

### Hash-Producing Functions

Named producer functions that compose normalization with hashing. Each `*_sha256` field in this spec cites its producer.

| Function | Signature | Normalization | Purpose |
|---|---|---|---|
| `content_hash` | `(markdown_content: str) -> Sha256Hex` | `knowledge_normalize` | Knowledge entry content hashing — dedup, promote drift detection. Used by: `lesson-meta.content_sha256`, `DistillCandidate.content_sha256`, `PromoteEnvelope.content_sha256`, `PromoteMeta.promoted_content_sha256` |
| `drift_hash` | `(text: str) -> Sha256Hex` | NFC + LF only (no further whitespace or content normalization) | Detect user edits to promoted text in CLAUDE.md. Intentionally stricter than `content_hash` so formatting changes count as drift. Empty string is valid input (produces a deterministic hash; will not match any stored `transformed_text_sha256` from non-empty promoted text). Used by: `PromoteMeta.transformed_text_sha256` |
| `work_dedup_fingerprint` | `(problem_text: str, key_file_paths: list[str]) -> Sha256Hex` | `work_normalize` on `problem_text` | Work engine 24-hour dedup window. Formula: `sha256(work_normalize(problem_text) + "|" + ",".join(sorted(key_file_paths)))` (single pipe character as separator) |

**Why three normalization levels?**

| Level | Function | Preserves | Discards | Rationale |
|---|---|---|---|---|
| Strictest | `drift_hash` | All whitespace, punctuation, case | Nothing beyond NFC+LF | CLAUDE.md is user-owned. Formatting edits to promoted blocks must count as drift. |
| Medium | `content_hash` | Intra-line spaces, punctuation, case, code fences | Trailing whitespace, excessive blank lines | Lesson content has meaningful punctuation and code examples (`` Use `json.dumps(sort_keys=True)` ``). Whitespace normalization prevents false mismatches from editor settings. |
| Lightest | `work_dedup_fingerprint` | Hyphens, underscores | Case, punctuation, extra whitespace | Short problem descriptions. Aggressive normalization catches near-duplicate tickets that differ only in formatting or capitalization. |

### Canonical JSON

**`canonical_json_bytes(value: dict | list | str | int | bool) -> bytes`**

Deterministic JSON serialization for idempotency key computation. Defined in `engram_core/canonical.py`.

Rules:
- `json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")`
- **Rejects `None`** anywhere in the input tree (raises `ValueError`). Callers must omit absent keys before calling — do not pass `None` values and expect silent exclusion.
- **Rejects `float`** (raises `TypeError`). All Engram idempotency material uses `str`, `int`, `bool`, `dict`, or `list`.
- NFC Unicode normalization is enforced upstream (at dataclass construction), not inside this function.
- No external standard referenced (not RFC 8785). This is internal canonicalization for same-codebase determinism, not cross-language interchange.

**Idempotency key computation:** `sha256(canonical_json_bytes(idempotency_material)).hexdigest()` — the two-step pattern (canonicalize, then hash) matches the existing `compute_source_uid()` pattern in `distill.py`.

## Idempotency and Dedup

Two distinct mechanisms serving different purposes.

### Idempotency — Same Operation Retried

The `idempotency_key` in `EnvelopeHeader` is computed as `sha256(canonical_json_bytes(idempotency_material)).hexdigest()` where the material is envelope-type-specific:

| Envelope | Idempotency Material |
|---|---|
| `DeferEnvelope` | `{source_ref.to_str(), title, problem, key_file_paths: sorted(...)}` |
| `DistillEnvelope` | `{source_ref.to_str(), candidates: sorted([{content_sha256, source_section, durability}, ...], key=lambda c: c["content_sha256"])}` |
| `PromoteEnvelope` | `{source_ref.to_str(), target_section, content_sha256}` |

**Field inclusion rationale:** `DeferEnvelope.key_file_paths` is included (sorted) because two defers with the same title/problem but different file paths are semantically distinct work items. `DeferEnvelope.context` is intentionally excluded — it is supplementary (same intent regardless of context snippet). All envelopes use `source_ref.to_str()` (full canonical serialization) instead of bare `source_ref.record_id` to prevent theoretical cross-subsystem collision.

[`canonical_json_bytes()`](#canonical-json) produces deterministic byte output. Same material produces the same key — target engine returns existing result without side effects.

The `DistillEnvelope` idempotency material includes per-candidate fingerprints to ensure that re-running extraction with improved logic on the same snapshot produces a distinct key when candidate content changes.

### Dedup — Semantically Identical Content

Uses content fingerprints at the record level:
- `DistillCandidate.content_sha256` — [`content_hash()`](#hash-producing-functions) deduplicates staged/published knowledge entries by content
- Work engine's existing duplicate detection — [`work_dedup_fingerprint()`](#hash-producing-functions) within a 24-hour window. The fingerprint uses problem content and file paths, not titles.

These mechanisms are independent in purpose and enforcement stage: an idempotent retry (same `idempotency_key`) is caught at the envelope level before dedup is ever checked. A genuinely new operation with coincidentally identical content is caught by dedup, not idempotency.

### Engine Hash Verification

The Knowledge engine **must** recompute [`content_hash(content)`](#hash-producing-functions) for every `DistillCandidate` and verify it matches the caller-provided `content_sha256`. Reject any candidate where the computed hash does not match. This prevents hash drift from corrupting the dedup invariant. Caller provides the hash (self-describing envelopes); engine verifies (trust-but-verify).

### Promote Hash Verification

The Knowledge engine **must** recompute [`drift_hash()`](#hash-producing-functions) on the exact text written to CLAUDE.md in [Step 2](operations.md#promote-knowledge-to-claudemd) and use that value for `PromoteMeta.transformed_text_sha256` in Step 3. The hash input is the final post-confirmation text between markers — not the `PromoteEnvelope.transformed_text` from Step 1.

**Rationale:** The Approve/modify/skip confirmation in Step 2 (Branches C1, C2) allows the user to modify the transformed text before writing. If Step 3 uses the pre-confirmation hash from the envelope, `transformed_text_sha256` would not match the actual CLAUDE.md content, causing spurious drift detection on the next `/promote` run.

**If the exact post-write text is unavailable** (e.g., Step 2 wrote to CLAUDE.md but the skill cannot retrieve the final text between markers), Step 3 **must** reject the promote-meta write rather than persist a hash computed from pre-confirmation text. The lesson remains eligible for the next `/promote` run (same recovery as [Step 2 failure](operations.md#failure-handling)).

## Knowledge Entry Format — lesson-meta Contract

All published knowledge entries in `engram/knowledge/learnings.md` use a uniform format regardless of producer (`/learn` or `/curate`):

```markdown
### YYYY-MM-DD Entry title
<!-- lesson-meta {"meta_version": "1.0", "lesson_id": "<UUIDv4>", "content_sha256": "<hex>", "created_at": "<ISO8601>", "producer": "learn|curate"} -->

Entry content...
```

**Fields:**
- **`meta_version`**: Version of the lesson-meta format. Currently `"1.0"`. Entries lacking this field are treated as `legacy` — see [Legacy Entries](#legacy-entries-missing-meta_version). See [Version Evolution Policy](#version-evolution-policy) for compatibility rules.
- **`lesson_id`**: UUIDv4 generated at creation. Serves as `RecordRef.record_id` for knowledge entries. Stable across edits (content changes update `content_sha256`, not `lesson_id`).
- **`content_sha256`**: [`Sha256Hex`](#scalar-types) produced by [`content_hash()`](#hash-producing-functions) on entry content (excluding the `lesson-meta` comment itself). The exact byte range: all text between the blank line following the `lesson-meta` comment and the start of the next `### ` heading (exclusive), after applying `knowledge_normalize`. The heading line itself is included; trailing blank lines before the next heading are excluded. Used for cross-producer dedup: both `/learn` and `/curate` check `content_sha256` against all existing published entries before writing.
- **`created_at`**: ISO 8601 UTC timestamp of initial creation (suffix `Z` or `+00:00`).
- **`producer`**: Which skill created the entry. Informational — does not affect lifecycle.

The [Knowledge reader](storage-and-indexing.md#readers) parses `### ` headings as entry delimiters and extracts `lesson-meta` JSON from the immediately following HTML comment. Entries lacking `lesson-meta` (legacy or hand-edited) are assigned `record_kind: "legacy"` and are discoverable via query but not addressable by `lesson_id`.

### Format Preservation

Each subsystem keeps its native format. Tickets keep fenced YAML. Snapshots keep `---` frontmatter. Learnings use heading-delimited blocks with `lesson-meta` comments. [NativeReaders](storage-and-indexing.md#nativereader-protocol) parse each format without requiring unification.

## Write Concurrency

Two failure modes for `learnings.md`, two mitigations:

**Same-worktree (local process race):** Two concurrent operations (e.g., `/learn` and `/curate` publish) in the same worktree perform read-modify-write on `learnings.md`. The Knowledge engine's publish path acquires an advisory file lock (`fcntl.flock(LOCK_EX)`) on a lockfile (`learnings.md.lock`, same directory) before reading. Lock held through read, append, write-to-temp, `fsync`, `os.replace`. Lock released after replace completes. Timeout: 5 seconds. On timeout: fail the operation with `"learnings.md is locked by another operation"` — do not queue or retry.

**Cross-worktree (git merge territory):** Each worktree has its own filesystem view. Concurrent appends from different worktrees produce divergent file states resolved by git merge on the shared branch. The Knowledge engine does not attempt cross-worktree coordination — git's line-based merge handles append-only files well. Conflicting appends (rare — requires overlapping content at the same file position) surface as git merge conflicts for the user to resolve.

**Staging files are not affected** — staging uses content-addressed filenames (`content_sha256`-based) with atomic file creation (`O_CREAT | O_EXCL` via `os.open` or equivalent). Identical candidates from concurrent operations coalesce; non-identical candidates get distinct files.

**CLAUDE.md:** Cross-worktree concurrent promotions are delegated to git merge (same model as `learnings.md` cross-worktree). Interleaved marker insertions from concurrent promotions of different lessons are safe — distinct `lesson_id` values in markers means non-overlapping content regions. Same-worktree concurrent promotion is not expected (single user, single session).

## Snapshot Orchestration Intent

When `/save` creates a snapshot, it embeds orchestration intent as flat scalar fields in the snapshot frontmatter:

```yaml
orchestrated_by: save
save_expected_defer: true
save_expected_distill: true
```

**Fields:**
- **`orchestrated_by`**: `"save"` when created by `/save` orchestrator. Absent when created by `/quicksave` or standalone `/load`. Presence indicates the snapshot was part of an orchestrated flow with expected sub-operations.
- **`save_expected_defer`**: `true` if `/save` was invoked without `--no-defer`. `false` if `--no-defer` was passed. Absent when `orchestrated_by` is absent.
- **`save_expected_distill`**: `true` if `/save` was invoked without `--no-distill`. `false` if `--no-distill` was passed. Absent when `orchestrated_by` is absent.

**Immutability:** Snapshots are immutable after creation. These fields record the intent at creation time. If a user later retries a failed sub-operation standalone (e.g., `/defer --snapshot-ref`), the snapshot's intent fields are not updated — the downstream record's existence is the proof of completion.

**Parse normalization:** Frontmatter parsers must normalize string `"true"`/`"false"` to boolean. YAML native booleans (`true`/`false` without quotes) are preferred but string representations must be accepted.

**Relationship to /triage:** These fields enable `/triage` to distinguish "intentionally skipped" from "crashed before running." See [/triage inference matrix](operations.md#triage-read-work-and-context).

## LedgerEntry — Event Record

Each line in a ledger shard (`ledger/<worktree_id>/<session_id>.jsonl`) is a single JSON object conforming to this schema:

```python
@dataclass(frozen=True)
class LedgerEntry:
    schema_version: str           # "1.0"
    ts: str                       # ISO 8601 UTC — primary sort key
    event_type: str               # From event vocabulary below
    producer: str                 # "engine" | "orchestrator" | "hook"
    session_id: str               # Claude session UUID
    worktree_id: str              # Derived from git rev-parse --git-dir
    record_ref: str | None        # RecordRef canonical serialization, if applicable
    operation_id: str | None      # Groups related events (e.g., all events from one /save)
    payload: dict                 # Event-type-specific data
```

### Event Vocabulary (v1)

| Event Type | Producer | Payload Fields | Purpose |
|---|---|---|---|
| `snapshot_written` | orchestrator | `{ref: str, orchestrated_by: str}` | Timeline fidelity — records snapshot creation |
| `defer_completed` | engine | `{source_ref: str, emitted_count: int}` | Completion evidence for /triage inference |
| `distill_completed` | engine | `{source_ref: str, emitted_count: int}` | Completion evidence for /triage inference |

In payload dicts, `RecordRef` values are stored as their [canonical serialization string](#recordref--lookup-key) (`RecordRef.to_str()`). Example: `{"ref": "context/snapshot/2026-03-21-abc123"}`.

**Completion events are success-only.** Their presence proves the operation ran to completion. Their absence means "not proven completed" — not "failed." Failure events are [deferred](decisions.md#deferred-decisions) to a future recovery-phase extension.

### Producer Classes

- **`engine` / `orchestrator`**: Events from subsystem engines and skill orchestrators (e.g., `/save`). These are authoritative completion signals. Only engine/orchestrator events qualify for the "ledger-backed" label in [/timeline](operations.md#session-timeline).
- **`hook`**: Events from `engram_register` PostToolUse hook. Observational only. `engram_register` does not observe engine Bash writes — it fires on Write/Edit tool calls to protected paths. Hook events provide supplementary timeline data but do not qualify as "ledger-backed."

### Timeline Label Semantics

- **"ledger-backed"**: A defined event from an `engine` or `orchestrator` producer exists for this record/operation.
- **"inferred"**: Reconstructed from `created_at` timestamps in `IndexEntry`, `source_ref` field scanning, or `git log` history.

### Ordering

- Primary sort: `ts` (ISO 8601 string comparison)
- Tie-break: file order (append-order within the JSONL shard)
- Grouping: `operation_id` links related events from the same orchestrated flow

### Write Semantics

All ledger producers use a shared locked append primitive in `engram_core/`. Advisory lock (`fcntl.flock`) on the shard file. Lock scope: read-append-fsync. Multi-producer integrity replaces the previous "single writer by sharding" assumption (which broke when engines became ledger producers).

**Ledger append failure never invalidates a successful write.** If a `defer_completed` event fails to append after a successful ticket creation, the ticket exists — the ledger gap is a diagnostic degradation, not data loss.

## Version Evolution Policy

Five independent version spaces govern Engram's data contracts. Each evolves independently — a bump in one does not require a bump in any other.

### Version Spaces

| Space | Field | Location | Starting Value |
|---|---|---|---|
| Envelope protocol | `EnvelopeHeader.envelope_version` | Cross-subsystem envelopes | `"1.0"` |
| Record provenance | `RecordMeta.schema_version` | All stored records via `IndexEntry` | `"1.0"` |
| Ledger format | `LedgerEntry.schema_version` | Event ledger entries | `"1.0"` |
| Knowledge entry metadata | `lesson-meta.meta_version` | `learnings.md` entries | `"1.0"` |
| Promotion state metadata | `promote-meta.meta_version` | `learnings.md` promotion records | `"1.0"` |

### RecordMeta.schema_version Semantics

`RecordMeta.schema_version` versions the Engram per-record provenance contract as surfaced through `RecordMeta` and `IndexEntry.meta`. It does **not** version envelope wire format (`envelope_version`), ledger event schema (`LedgerEntry.schema_version`), or native subsystem body layout (subsystem-specific). Each of those has its own version space.

### Compatibility Rules

| Version Space | Read Behavior | Write Behavior |
|---|---|---|
| Envelope protocol | **Exact-match.** Target engine rejects envelopes with unrecognized `envelope_version` via `VERSION_UNSUPPORTED` error (see below). No forward compatibility. | Writers emit the version they were built for. |

**`VERSION_UNSUPPORTED` error:** Returned by target engines when `envelope_version` does not match the engine's built-in version. Structure: `{"error_code": "VERSION_UNSUPPORTED", "received_version": "<received>", "expected_version": "<engine_version>"}`. Note: `expected_version` is singular (exact-match — there is only one valid version per engine build).
| Record provenance | **Same-major tolerance with field preservation.** Readers accept records with the same major version (e.g., a v1.0 reader reads v1.1). Unknown fields must be preserved verbatim on rewrite — see [Field Preservation Requirement](#field-preservation-requirement). Records with a different major version are skipped with a warning via `QueryDiagnostics.warnings`. | Writers emit the version they were built for. |
| Ledger format | **Same-major tolerance.** Parse `schema_version` as `<major>.<minor>`. Compare `major` as integer. Readers skip entries where `major` differs from the reader's built-in major. Unknown fields are ignored (ledger entries are append-only, never rewritten). | Writers emit the version they were built for. |
| Knowledge entry metadata | **Entry-level exact-match for interpretation; verbatim preservation for unrelated writes.** When interpreting a `lesson-meta` comment (dedup, promote eligibility), the Knowledge engine requires exact major.minor match. Entries with unrecognized `meta_version` are skipped with a per-entry warning — they do not block operations on other entries in the same file. When appending a new entry, existing entries with unrecognized `meta_version` are preserved verbatim. | Writers emit the version they were built for. |
| Promotion state metadata | **Entry-level exact-match.** Same rules as knowledge entry metadata. Entries with unrecognized `promote-meta.meta_version` are skipped per-entry. Unrelated entries are preserved verbatim on rewrite. | Writers emit the version they were built for. |

### Legacy Entries (Missing meta_version)

Existing `lesson-meta` and `promote-meta` comments written before the `meta_version` field was introduced will lack the field entirely. These are **not** treated as implicit `"1.0"`:

- **Discovery:** Entries with structured `lesson-meta` but missing `meta_version` remain discoverable via `query()` and addressable by `lesson_id`. They retain their original `record_kind` (not overloaded to `"legacy"` — that label is reserved for entries lacking `lesson-meta` entirely, per the [Knowledge Entry Format](#knowledge-entry-format-lesson-meta-contract)). A per-entry compatibility warning is added to `QueryDiagnostics.warnings`.
- **Interpretation:** Operations that interpret metadata (dedup via `content_sha256`, promote eligibility via `promote-meta`) skip entries with missing `meta_version` with a per-entry warning. They do not block operations on other entries.
- **Rewrite:** Rewrite paths (e.g., appending `promote-meta` to an entry) must not touch metadata blocks with missing `meta_version`. To upgrade, the user runs a migration that adds `meta_version: "1.0"` explicitly.
- **Promote-meta without meta_version:** Promotion status for entries with pre-version `promote-meta` degrades to `unknown` (not interpretable for Branch A/B/C decisions). The lesson itself remains valid.

**Rationale:** Treating missing `meta_version` as implicit `"1.0"` makes the field meaningless for existing entries and prevents distinguishing "written before versioning existed" from "written with v1.0 format."

### Per-Entry Degradation Guarantee

Mixed-version `learnings.md` files degrade per entry, never per file. A single entry with an unsupported `meta_version` (or missing `meta_version`) does not make other entries in the same file unreadable, unqueryable, or unwritable. This guarantee applies to both `lesson-meta` and `promote-meta` version mismatches.

### Bump Triggers

| Change Type | Version Impact | Examples |
|---|---|---|
| **Major** (breaking) | Increment major, reset minor to 0 | Removing or renaming a required field, changing field semantics, changing serialization format |
| **Minor** (additive) | Increment minor | Adding an optional field, adding a new enum value to an existing field |

No patch version. Documentation-only changes do not affect version numbers.

### Field Preservation Requirement

When a reader encounters a record with same-major, different-minor version and subsequently rewrites that record (e.g., appending `promote-meta` to a `lesson-meta` entry), it **must** preserve all fields from the original record verbatim — including fields the reader does not recognize. If an operation cannot preserve unknown fields, it must reject the rewrite rather than silently drop them.

**Non-normative implementation note:** One acceptable strategy is to parse the JSON comment as a `dict`, update known keys, and serialize the merged object with `sort_keys=True`. Other implementations that satisfy the preservation invariant are equally valid.

**Rationale:** Without field preservation, same-major tolerance is a data-loss trap. A v1.0 Knowledge engine that reparses and reserializes a v1.1 `lesson-meta` would silently drop the v1.1 field, corrupting the record for v1.1 consumers.
