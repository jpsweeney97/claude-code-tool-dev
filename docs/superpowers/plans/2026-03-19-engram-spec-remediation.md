# Engram Spec Remediation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate 6 findings from the system design review + Codex dialogue before Step 0a implementation begins.

**Architecture:** Edit 4 spec files in `docs/superpowers/specs/engram/` to add a versioning policy, normalization verification gates, chain file reclassification, and NativeReader scope clarification. All changes are spec-level (markdown), no code.

**Tech Stack:** Markdown spec files with YAML frontmatter. Verification via grep for cross-reference consistency.

**Source:** System design review (2026-03-19) + Codex dialogue thread `019d068a-5649-7132-b151-2bf107cfad8e` (initial 5 turns + plan review turn). Findings: F1 (NativeReader clarification), F3 (normalization verification), F5 (versioning policy), M1a (chain file reclassification), plus emerged insights.

---

## File Map

| File | Changes | Finding |
|------|---------|---------|
| `docs/superpowers/specs/engram/types.md` | Add Version Evolution Policy section (~90 lines); add `meta_version` field to lesson-meta and promote-meta | F5 |
| `docs/superpowers/specs/engram/foundations.md` | Reclassify chain files as auxiliary coordination | M1a |
| `docs/superpowers/specs/engram/storage-and-indexing.md` | Add NativeReader scope clarification; add reader crash behavior to degradation model | F1, Emerged |
| `docs/superpowers/specs/engram/delivery.md` | Add VR-14 to Step 0a; add VR-15 to Step 2a | F3 |

---

### Task 1: Add Version Evolution Policy to types.md

The largest remediation item. Adds a new top-level section after "LedgerEntry — Event Record" defining 5 independent version spaces, compatibility rules, bump triggers, field-preservation requirement, `RecordMeta.schema_version` semantics, and legacy `meta_version` handling.

**Files:**
- Modify: `docs/superpowers/specs/engram/types.md:367` (insert after LedgerEntry Write Semantics)

- [ ] **Step 1: Verify the gap exists**

Run: `grep -c "Version Evolution" docs/superpowers/specs/engram/types.md`
Expected: `0`

- [ ] **Step 2: Insert the Version Evolution Policy section**

Add the following after line 367 (end of LedgerEntry section) in `types.md`:

```markdown
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
| Envelope protocol | **Exact-match.** Target engine rejects envelopes with unrecognized `envelope_version` via `VERSION_UNSUPPORTED` error. No forward compatibility. | Writers emit the version they were built for. |
| Record provenance | **Same-major tolerance with field preservation.** Readers accept records with the same major version (e.g., a v1.0 reader reads v1.1). Unknown fields must be preserved verbatim on rewrite — see [Field Preservation Requirement](#field-preservation-requirement). Records with a different major version are skipped with a warning via `QueryDiagnostics.warnings`. | Writers emit the version they were built for. |
| Ledger format | **Same-major tolerance.** Readers skip entries with unrecognized major versions. Unknown fields are ignored (ledger entries are append-only, never rewritten). | Writers emit the version they were built for. |
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
```

- [ ] **Step 3: Verify the section was added**

Run: `grep -c "Version Evolution" docs/superpowers/specs/engram/types.md`
Expected: `1` (the new section heading)

Run: `grep -c "Field Preservation Requirement" docs/superpowers/specs/engram/types.md`
Expected: `1`

Run: `grep -c "Legacy Entries" docs/superpowers/specs/engram/types.md`
Expected: `1`

Run: `grep -c "RecordMeta.schema_version Semantics" docs/superpowers/specs/engram/types.md`
Expected: `1`

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/engram/types.md
git commit -m "feat(engram-spec): add Version Evolution Policy to types.md

Defines 5 independent version spaces, compatibility rules (exact-match
for envelopes, same-major tolerance for stored records, entry-level
exact-match for lesson-meta/promote-meta), bump triggers, field
preservation requirement, RecordMeta.schema_version semantics, and
legacy meta_version handling.

Addresses F5 from system design review + Codex dialogue."
```

---

### Task 2: Add meta_version to lesson-meta and promote-meta

Adds the `meta_version` field to both metadata comment formats and updates their documentation. Note: `lesson-meta` is a JSON comment format (not a Python dataclass); `promote-meta` has both a dataclass definition and a JSON comment serialization.

**Files:**
- Modify: `docs/superpowers/specs/engram/types.md:270` (lesson-meta format example and fields)
- Modify: `docs/superpowers/specs/engram/types.md:107-122` (PromoteMeta dataclass and serialization)

- [ ] **Step 1: Update lesson-meta format example**

In `types.md`, replace the lesson-meta example block (around line 268-273):

Old:
~~~markdown
```markdown
### YYYY-MM-DD Entry title
<!-- lesson-meta {"lesson_id": "<UUIDv4>", "content_sha256": "<hex>", "created_at": "<ISO8601>", "producer": "learn|curate"} -->

Entry content...
```
~~~

New:
~~~markdown
```markdown
### YYYY-MM-DD Entry title
<!-- lesson-meta {"meta_version": "1.0", "lesson_id": "<UUIDv4>", "content_sha256": "<hex>", "created_at": "<ISO8601>", "producer": "learn|curate"} -->

Entry content...
```
~~~

- [ ] **Step 2: Add meta_version to lesson-meta Fields list**

In `types.md`, in the **Fields:** list under lesson-meta (around line 275), add a new bullet (position in the list is not normative):

```markdown
- **`meta_version`**: Version of the lesson-meta format. Currently `"1.0"`. Entries lacking this field are treated as `legacy` — see [Legacy Entries](#legacy-entries-missing-meta_version). See [Version Evolution Policy](#version-evolution-policy) for compatibility rules.
```

- [ ] **Step 3: Add meta_version to PromoteMeta dataclass**

In `types.md`, in the `PromoteMeta` dataclass (around line 108), add `meta_version`. Field order in JSON comments is not normative — showing it first in examples is for visibility only:

Old:
```python
@dataclass(frozen=True)
class PromoteMeta:
    target_section: str           # Advisory: last requested destination / insertion hint
```

New:
```python
@dataclass(frozen=True)
class PromoteMeta:
    meta_version: str             # "1.0" — see Version Evolution Policy
    target_section: str           # Advisory: last requested destination / insertion hint
```

- [ ] **Step 4: Add meta_version field description for promote-meta**

In `types.md`, after the `PromoteMeta` dataclass fields (around line 114), in the field documentation, add:

```markdown
**`meta_version`**: Version of the promote-meta format. Currently `"1.0"`. Entries lacking this field are treated as `legacy`. See [Version Evolution Policy](#version-evolution-policy) for entry-level exact-match semantics and field preservation requirements.
```

- [ ] **Step 5: Update promote-meta serialization example**

In `types.md`, update the promote-meta serialization example (around line 119):

Old:
```markdown
<!-- promote-meta {"lesson_id": "550e8400-...", "target_section": "## Code Style", ...} -->
```

New:
```markdown
<!-- promote-meta {"meta_version": "1.0", "lesson_id": "550e8400-...", "target_section": "## Code Style", ...} -->
```

- [ ] **Step 6: Verify both formats include meta_version**

Run: `grep "meta_version" docs/superpowers/specs/engram/types.md`
Expected: At least 5 matches (lesson-meta example, lesson-meta field doc, PromoteMeta dataclass, promote-meta field doc, promote-meta serialization example) plus references from the Version Evolution Policy section.

- [ ] **Step 7: Commit**

```bash
git add docs/superpowers/specs/engram/types.md
git commit -m "feat(engram-spec): add meta_version to lesson-meta and promote-meta

Both metadata comment formats now carry a meta_version field ('1.0')
with entry-level exact-match semantics per the Version Evolution Policy.
Entries lacking the field are treated as legacy. Enables future format
evolution without file-wide denial of service."
```

---

### Task 3: Reclassify chain files in foundations.md

Reclassify chain state files from "Primary records" to ephemeral coordination artifacts in the Auxiliary State Authority section.

**Files:**
- Modify: `docs/superpowers/specs/engram/foundations.md:70` (Auxiliary State Authority)

- [ ] **Step 1: Reclassify chain files**

In `foundations.md`, the Auxiliary State Authority section (line 70) currently reads:

```
Recovery manifests (`save_recovery.json`, `migration_report.json`) are operational aids only. Primary records — snapshots, tickets, learnings, chain state files — remain authoritative.
```

Replace with:

```
Recovery manifests (`save_recovery.json`, `migration_report.json`) and chain state files (`chain/<worktree_id>-<session_id>`) are operational aids only. Primary records — snapshots, tickets, learnings — remain authoritative. Chain state files are ephemeral coordination artifacts with 24-hour TTL; their loss degrades `resumed_from` lineage tracking but does not invalidate any primary record. See [chain protocol](skill-surface.md#chain-protocol-session-lineage-tracking) for TTL and cleanup rules.
```

- [ ] **Step 2: Verify the change**

Run: `grep "ephemeral coordination" docs/superpowers/specs/engram/foundations.md`
Expected: 1 match

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/engram/foundations.md
git commit -m "feat(engram-spec): reclassify chain files as auxiliary coordination

Chain state files are ephemeral coordination artifacts (24h TTL), not
primary records. Their loss degrades lineage tracking but does not
invalidate any primary record.

Addresses M1a from system design review + Codex dialogue."
```

---

### Task 4: NativeReader clarification and reader crash behavior in storage-and-indexing.md

Three changes in `storage-and-indexing.md` (authority: `data-contract`):
1. Add NativeReader Protocol scope clarification near the protocol definition (F1).
2. Add `degraded_subsystems` field to `QueryDiagnostics` for structured reader-crash reporting.
3. Add reader crash behavior to the degradation model (Emerged).

**Files:**
- Modify: `docs/superpowers/specs/engram/storage-and-indexing.md:96-115` (NativeReader Protocol section)
- Modify: `docs/superpowers/specs/engram/storage-and-indexing.md:147-153` (QueryDiagnostics dataclass)
- Modify: `docs/superpowers/specs/engram/storage-and-indexing.md:227-233` (Degradation Model table)

- [ ] **Step 1: Add NativeReader scope clarification**

In `storage-and-indexing.md`, after the NativeReader Protocol definition and the `# No write(). By design.` comment (around line 114), before the "### Readers" subsection, add:

```markdown
**Reader wiring:** `query.py` instantiates a fixed set of NativeReaders (context, work, knowledge). The `NativeReader` Protocol is a typing contract only — it provides structural subtyping for reader implementations but does not provide registration, discovery, or enforcement. Adding a new reader requires a code change in `query.py`, not a plugin mechanism.
```

- [ ] **Step 2: Add degraded_subsystems to QueryDiagnostics**

In `storage-and-indexing.md`, in the `QueryDiagnostics` dataclass (around line 147-153), add a new field after `degraded_roots`:

```python
    degraded_subsystems: list[str]  # Subsystems where reader scan()/read() raised an exception
```

This provides structured reporting for reader crashes, complementing `degraded_roots` (storage unavailability) and `warnings` (human-readable detail). Callers can check `degraded_subsystems` without parsing warning strings.

- [ ] **Step 3: Add reader crash row to degradation model**

In `storage-and-indexing.md`, after the "Reader fails to parse a file" row in the Degradation Model table (around line 231), add a new row:

```markdown
| Reader `scan()` or `read()` raises unhandled exception | Catch, skip that reader's entire subsystem, add to `degraded_subsystems` and `warnings` | `diagnostics.degraded_subsystems` includes subsystem name. `diagnostics.warnings` includes subsystem name and error message. `diagnostics.skipped_count` is not incremented (file-level metric). Other subsystems' results are unaffected. |
```

- [ ] **Step 4: Verify all three changes**

Run: `grep "Reader wiring" docs/superpowers/specs/engram/storage-and-indexing.md`
Expected: 1 match

Run: `grep "degraded_subsystems" docs/superpowers/specs/engram/storage-and-indexing.md`
Expected: At least 2 matches (dataclass field + degradation table)

Run: `grep "raises unhandled exception" docs/superpowers/specs/engram/storage-and-indexing.md`
Expected: 1 match

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/engram/storage-and-indexing.md
git commit -m "feat(engram-spec): add NativeReader scope, degraded_subsystems, reader crash

NativeReader Protocol is typing only — query.py wires a fixed reader
set. New degraded_subsystems field in QueryDiagnostics for structured
reader-crash reporting. Reader crashes skip entire subsystem; other
subsystems unaffected.

Addresses F1 and emerged insight from Codex dialogue."
```

---

### Task 5: Add normalization verification to delivery.md

Two verification requirements split across steps per Codex feedback:
- VR-14 (normalization boundary) in Step 0a — validates the hash helpers exist and diverge.
- VR-15 (promote-path wiring) in Step 2a — validates the promote pipeline uses the correct normalizer. Cannot be tested until the promote pipeline exists.

**Files:**
- Modify: `docs/superpowers/specs/engram/delivery.md:47-50` (Step 0a Required Verification)
- Modify: `docs/superpowers/specs/engram/delivery.md:121` (Step 2a exit criteria)

- [ ] **Step 1: Locate Step 0a and Step 2a Required Verification sections**

Run: `grep -n "Required Verification\|Exit criteria" docs/superpowers/specs/engram/delivery.md | head -10`
Expected: Shows Step 0a Required Verification (line ~47) and Step 2a exit criteria (line ~121)

- [ ] **Step 2: Add VR-14 to Step 0a**

In `delivery.md`, after the existing Step 0a Required Verification items (after line 50, the VR-7 entry), add:

```markdown
- Normalization boundary test (VR-14): construct a string where `knowledge_normalize` and `drift_hash`-level normalization (NFC+LF only) produce different outputs (e.g., trailing whitespace). Assert `content_hash(input) != drift_hash(input)`. Separately, assert `content_hash(input) != work_dedup_fingerprint(input, [])` for a mixed-case input. This proves the three pipelines diverge — using the wrong one would produce a different hash.
```

- [ ] **Step 3: Add VR-15 to Step 2a**

In `delivery.md`, after the Step 2a exit criteria line (around line 121, `**Exit criteria (2a):**`), add a new Required Verification subsection:

```markdown
#### Required Verification
- Promote-path wiring check (VR-15): `PromoteMeta.transformed_text_sha256` must be produced by `drift_hash()`, not `content_hash()`. Construct promoted text with trailing whitespace. Assert `drift_hash(text)` detects the whitespace (different hash from stripped version) while `content_hash(text)` does not (same hash). This verifies the promote pipeline uses the correct — stricter — normalizer for drift detection.
```

- [ ] **Step 4: Verify both VRs are present in correct steps**

Run: `grep -B5 "VR-14" docs/superpowers/specs/engram/delivery.md | head -8`
Expected: VR-14 appears under Step 0a

Run: `grep -B5 "VR-15" docs/superpowers/specs/engram/delivery.md | head -8`
Expected: VR-15 appears under Step 2a

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/engram/delivery.md
git commit -m "feat(engram-spec): add normalization verification gates

VR-14 (Step 0a) proves the three normalization pipelines diverge.
VR-15 (Step 2a) proves the promote pipeline uses drift_hash for
transformed_text_sha256, not content_hash.

VR-15 placed in Step 2a (not 0a) because the promote pipeline
does not exist until the knowledge cutover step.

Addresses F3 from system design review."
```

---

### Task 6: Cross-reference verification

Verify all new content is properly cross-referenced and no broken links were introduced.

**Files:**
- Read: all 4 modified spec files

- [ ] **Step 1: Verify types.md internal anchors**

Run: `grep -o '\[.*\](#[a-z-]*)' docs/superpowers/specs/engram/types.md | sort -u`

Check that every `#anchor` reference in types.md points to a heading that exists in the same file. Specifically verify:
- `#version-evolution-policy` exists as `## Version Evolution Policy`
- `#field-preservation-requirement` exists as `### Field Preservation Requirement`
- `#legacy-entries-missing-meta_version` exists as `### Legacy Entries (Missing meta_version)`
- `#per-entry-degradation-guarantee` exists as `### Per-Entry Degradation Guarantee`

- [ ] **Step 2: Verify cross-file references from foundations.md**

Run: `grep -o '\[.*\](skill-surface.md#[a-z-]*)' docs/superpowers/specs/engram/foundations.md`

Verify the chain protocol link `(skill-surface.md#chain-protocol-session-lineage-tracking)` matches an existing heading in skill-surface.md.

- [ ] **Step 3: Verify VR numbering in delivery.md**

Run: `grep -o 'VR-[0-9]*' docs/superpowers/specs/engram/delivery.md | sort -t- -k2 -n`

Expected: VR-4 through VR-15, no collisions. VR-14 under Step 0a, VR-15 under Step 2a. (VR-1 through VR-3 do not exist — the numbering started at VR-4 in the original spec.)

- [ ] **Step 4: Verify spec.yaml authority boundaries**

Check that each file was modified within its authority:
- `types.md` → authority: `data-contract` (versioning is a data contract concern) ✓
- `foundations.md` → authority: `foundation` (auxiliary state authority is a foundation concern) ✓
- `storage-and-indexing.md` → authority: `data-contract` (NativeReader protocol and degradation model are data-contract concerns) ✓
- `delivery.md` → authority: `delivery` (verification requirements are delivery-owned) ✓

Run: `grep "^authority:" docs/superpowers/specs/engram/{types,foundations,storage-and-indexing,delivery}.md`

- [ ] **Step 5: Final commit (if any fixups needed)**

If any cross-reference issues were found in Steps 1-4, fix them and commit:

```bash
git add docs/superpowers/specs/engram/
git commit -m "fix(engram-spec): fix cross-references in spec remediation"
```

If no issues, skip this step.
