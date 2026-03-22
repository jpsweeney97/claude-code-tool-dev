# Engram Spec Remediation Plan — Round 1

**Source:** `.review-workspace/synthesis/report.md` (6-reviewer team, 2026-03-21)
**Scope:** 73 canonical findings (3 P0, 44 P1, 26 P2) across 9 spec files
**Spec:** `docs/superpowers/specs/engram/` (10 files, ~1631 lines)
**Dominant pattern:** Underspecified enforcement boundaries (15+ findings across 4 reviewers)

## Strategy

Four commits, ordered by dependency and priority:

1. **P0 critical gaps** + directly coupled P1 findings (same spec surface)
2. **Enforcement boundaries** — trust injection, hook contracts, protected paths
3. **Schema and persistence** — types, serialization, storage contracts
4. **Verification and authority** — delivery.md test additions + authority placement fixes

Rationale: Commit 1 must land first (P0 blocking). Commits 2-3 are independent (enforcement vs. schema surfaces) and could theoretically parallelize, but sequential is safer for cross-file consistency. Commit 4 depends on 2-3 because delivery.md verification items reference enforcement and schema contracts defined in those commits.

---

## Commit 1 — P0: Critical Enforcement and Behavioral Gaps

**Finding count:** 3 P0 + 5 P1 = 8 findings
**Files:** enforcement.md, operations.md, delivery.md, skill-surface.md, foundations.md

### P0 Findings

#### [SY-1] /learn trust enforcement gap — complete blind spot

**Source:** CE-3 + IE-2 + IE-13 (3 reviewers, elevated from P1/P2)
**Files:** enforcement.md, operations.md, skill-surface.md

Fix: Specify that `/learn` routes through the Knowledge engine entrypoint (not a direct Write to `learnings.md`). This means:
1. **enforcement.md** §Trust Injection Step 2: Add `/learn` publish to the mutating entrypoints enumeration ("knowledge publish" → "knowledge publish (both `/learn` direct and `/curate` staged)")
2. **operations.md** §Triage anomaly detection: Define Knowledge-specific provenance anomaly — entries in `learnings.md` lacking valid `lesson-meta` with `producer` field not in `{learn, curate}` (closes SY-3 simultaneously)
3. **skill-surface.md** `/learn` row: Clarify that `/learn` invokes the Knowledge engine entrypoint (not a direct file write)

#### [VR-1] No verification path for core index-not-mutate invariant

**Source:** verification-regression (singleton P0)
**Files:** foundations.md, delivery.md

Fix:
1. **delivery.md** §Step 0a Required Verification: Add three items:
   - Assert `NativeReader` protocol has no `write()` method
   - Assert `query.py` contains no filesystem write calls
   - Integration test: run cross-reader query, assert no files created/modified in subsystem directories
2. **foundations.md** §Shadow Authority Anti-Pattern: Reframe the prose design test as pointing to the runnable tests in delivery.md

#### [VR-2] Promote Branch B1 (already-promoted rejection) has no test

**Source:** verification-regression (singleton P0)
**Files:** delivery.md

Fix: Add to VR-10 in delivery.md: "Branch B1: fixture with `promote-meta` present, `promoted_content_sha256 == current content_sha256`, `target_section` unchanged → assert rejection with 'already promoted' status and existing promotion details."

### Coupled P1 Findings (same surface as P0s)

#### [SY-4] promote-meta without meta_version — unhandled Branch D

**Source:** CE-6 + SP-16
**Files:** operations.md, types.md

Fix: Add Branch D to the promote state machine in operations.md: "promote-meta present, `meta_version` unrecognized or missing → `unknown` status → exclude from candidate list with warning: 'Lesson X has unreadable promote-meta (missing meta_version). Run migration before re-promoting.'" Cross-reference types.md §Legacy Entries.

#### [CC-3] Failure handling table omits Branch B2 and C3

**Source:** completeness-coherence (singleton)
**Files:** operations.md

Fix: Expand failure handling row to "Promote Step 2 failure (Branch A/B2/C1/C2/C3)" — all share the same recovery (CLAUDE.md unchanged, lesson remains eligible). Add note if B2/C3 have distinct partial-write failure modes.

#### [IE-12] hook_injected=False passes trust triple validation

**Source:** integration-enforcement (singleton)
**Files:** enforcement.md

Fix: Rewrite enforcement.md §Step 2 validator description: "`collect_trust_triple_errors()` must check (1) `hook_injected` is present **and equals `True`** (not just non-empty), (2) `hook_request_origin` is present and is a non-empty string, (3) `session_id` is present and is a non-empty string."

#### [CC-6] /learn lesson-meta ambiguity in trigger differentiation

**Source:** completeness-coherence (singleton)
**Files:** skill-surface.md

Fix: Restructure the final sentence of the trigger differentiation entry: "For the distill path, lesson-meta is applied by `/curate` at publication time; `/learn` applies lesson-meta directly on write."

#### [SY-3] Knowledge anomaly detection asymmetric across subsystems

**Source:** CE-10 + CC-10
**Files:** operations.md

Fix: (Addressed jointly with SY-1 above.) Define Knowledge provenance anomaly in operations.md §Triage: entries in `learnings.md` lacking valid `lesson-meta` or with `producer` field not in `{learn, curate}`. Update the misleading "Context/Knowledge" label to separate entries with concrete examples for each. Add VR-19 Knowledge fixture to delivery.md.

---

## Commit 2 — Enforcement Boundaries: Trust, Hooks, Protected Paths

**Finding count:** 9 P1 + 6 P2 = 15 findings
**Files:** enforcement.md (primary), operations.md, foundations.md

### P1 Findings

#### [SY-2] Engine detection pattern is implementation heuristic, not contract

**Source:** CE-1 + IE-8
**Files:** enforcement.md, foundations.md

Fix: Replace filename glob with contract-level detection:
1. **foundations.md** or **enforcement.md**: Define canonical engine filename pattern as normative — "Engine binaries must be named `engine_<subsystem>.py` and reside in the plugin's scripts directory. `engram_guard` matches the full path `<engram_scripts_dir>/engine_*.py`, not just the filename."
2. **enforcement.md** §Step 1: Add failure mode — "If the pattern fails to match a legitimate engine invocation, the trust triple is not injected and the engine rejects via `collect_trust_triple_errors()`. The diagnostic should indicate 'engine invocation not recognized by engram_guard'."

#### [SY-5] Inter-hook runtime state underspecified

**Source:** CE-8 + IE-6
**Files:** enforcement.md

Fix: Change "preferred approach" to a mandate: "engram_guard MUST recompute `worktree_id` independently via `identity.get_worktree_id()`. `session_id` MUST be obtained from Claude Code session context." Remove the "if shared state is unavoidable" paragraph or explicitly scope it: "The shared-state fallback applies only if Claude Code session context becomes unavailable in a future platform change. Until then, recomputation is the sole supported approach."

#### [CE-2] Read-only entrypoint exemption boundary unspecified

**Files:** enforcement.md

Fix: Change "at minimum" to a complete enumeration per subsystem. Add: "Each subsystem engine's module docstring must enumerate all mutating entrypoints. delivery.md Step 3a must include a verification step asserting trust triple validation is present at every documented mutating entrypoint."

#### [CE-5] Phase-scoped idempotency absent from enforcement.md

**Files:** enforcement.md

Fix: Add "Bridge Period Limitations" note to enforcement.md: "During Steps 1–3, envelope-level idempotency keys are not checked (see [operations.md §Phase-Scoped Idempotency](operations.md#envelope-invariants)). Legacy dedup is the active mechanism. Full idempotency enforcement begins at Step 4."

#### [IE-1] Snapshot/checkpoint paths unprotected by engram_guard

**Files:** enforcement.md

Fix: Add rationale note to enforcement.md §Protected-Path Enforcement: "Snapshot and checkpoint paths (`~/.claude/engram/<repo_id>/snapshots/**`, `checkpoints/**`) are intentionally excluded from PreToolUse protection. Context subsystem writes use Write/Edit tools natively (session orchestration), and the Context engine does not gate writes through Bash. Quality validation via `engram_quality` provides advisory checks on these paths."

#### [IE-3] engram_register silent failures invisible

**Files:** enforcement.md

Fix: Add to engram_register hook specification: "Failure modes: (1) Lock timeout → log warning, do not block; (2) Permission denied → log error, do not block; (3) Disk full → log error, do not block. All failures are written to the session diagnostic channel. `/triage` surfaces 'ledger unavailable in session X' rather than 'completion not proven' when the ledger producer has recorded failures."

#### [IE-5] engram/.engram/ directory unprotected

**Files:** enforcement.md

Fix: Add forward-compatible note to §Protected-Path Enforcement: "When content is added to `engram/.engram/`, a corresponding path class entry must be added to this table before implementation. The directory is reserved for future shared metadata."

#### [IE-7] Staging cap batch-exceeds-cap has no recovery path

**Files:** enforcement.md

Fix: Extend the edge case specification: "The rejection response must include: (1) current `batch_size`, (2) current cap, (3) the config change needed (`knowledge_max_stages: N` where N >= batch_size), (4) instruction to re-run the failed distill with the snapshot reference from the recovery manifest."

#### [AA-1] Staging cap behavioral spec misplaced in enforcement.md

**Files:** enforcement.md, operations.md

Fix: Move the behavioral specification (rejection logic, formula, error message format, edge case) to operations.md §Distill. Retain in enforcement.md only the policy statement ("Staging inbox cap is configured via `knowledge_max_stages`") and a cross-reference to operations.md.

### P2 Findings

#### [CE-4] engram_quality does not validate staging writes

**Files:** enforcement.md

Fix: Add rationale note to Quality Validation Scope table: "Staging writes are excluded — the Knowledge engine validates content at write time, making post-write quality hooks redundant for staging."

#### [CE-9] Enforcement exception dual-file update sequencing

**Files:** enforcement.md

Fix: Add: "foundations.md is the authoritative source for new exceptions. A new exception is effective only when present in foundations.md. enforcement.md then references it."

#### [CE-11] knowledge_max_stages: 0 behavior unspecified

**Files:** enforcement.md

Fix: Add minimum value constraint: "Values less than 1 are invalid; the engine rejects the configuration with `'knowledge_max_stages must be >= 1'`."

#### [CE-13] engram_register scope misleadingly aligned with protected paths

**Files:** enforcement.md

Fix: Add clarification to Ledger Multi-Producer Note: "`engram_register` observes only Write/Edit tool calls to protected paths. Staging writes (`knowledge_staging/`) are engine-initiated and not observable by this hook."

#### [IE-10] engram_quality own-failure behavior undocumented

**Files:** enforcement.md

Fix: Add: "If `engram_quality` itself fails (unhandled exception, timeout), the failure is logged as `[engram_quality:error]` (distinct from `[engram_quality:warn]`) but does not block the write."

#### [AA-8] foundations.md permitted exceptions contain behavioral detail

**Files:** foundations.md

Fix: Trim to architectural purpose: "CLAUDE.md is an external sink; the Knowledge engine owns promotion state (promote-meta); the CLAUDE.md write is a skill-level bypass of the engine write path." Remove step-level behavioral detail (drift_hash usage, Step 1/2 sequencing) — replace with cross-reference to the promote state machine in operations.md.

---

## Commit 3 — Schema and Persistence: Types, Serialization, Storage

**Finding count:** 11 P1 + 10 P2 = 21 findings
**Files:** types.md (primary), storage-and-indexing.md, operations.md, foundations.md

### P1 Findings

#### [SY-6] DeferEnvelope idempotency excludes key_file_paths → false dedup

**Source:** CC-7 + SP-1
**Files:** types.md

Fix: Add `key_file_paths: sorted(...)` to `DeferEnvelope` idempotency material. Add rationale note: "`context` is intentionally excluded (supplementary, not identity-defining)."

#### [SP-3] RecordRef has no canonical serialization format

**Files:** types.md

Fix: Define in types.md §RecordRef: "Canonical serialization: `<subsystem>/<record_kind>/<record_id>` (repo_id omitted — implicit from context). Implemented as `RecordRef.to_str()` / `RecordRef.from_str()` in `engram_core/types.py`."

#### [SP-4] Event vocabulary cites RecordRef as Python dataclass in dict payload

**Files:** types.md

Fix: Annotate event vocabulary table: "In payload dicts, `RecordRef` is stored as its canonical serialization string (see §RecordRef). Example: `{\"ref\": \"context/snapshot/2026-03-21-abc123\"}`."

#### [SP-5] RecordMeta fields undefined for native file formats

**Files:** types.md or storage-and-indexing.md

Fix: Add a mapping table defining which frontmatter/comment keys correspond to `RecordMeta` fields per subsystem:

| Subsystem | `schema_version` | `worktree_id` | `session_id` | `visibility` |
|-----------|-------------------|---------------|--------------|-------------|
| Context (snapshot) | `schema_version` in frontmatter | `worktree_id` in frontmatter | `session_id` in frontmatter | `private` (always private root) |
| Work (ticket) | `schema_version` in fenced YAML | `worktree_id` in fenced YAML | `session_id` in fenced YAML | `shared` (always shared root) |
| Knowledge (lesson) | `meta_version` in lesson-meta | N/A (shared root, no worktree scope) | N/A | `shared` |

#### [SP-7] Staging file granularity (per-candidate vs per-batch) unspecified

**Files:** types.md or storage-and-indexing.md

Fix: Specify: "Each `DistillCandidate` gets its own staging file, named `YYYY-MM-DD-<content_sha256[:16]>.md`, where the hash is the candidate's `content_sha256`. This makes `O_CREAT | O_EXCL` coalescing semantics precise."

#### [SP-8] worktree_id hashing function unspecified

**Files:** types.md

Fix: Specify exact derivation in §Identity Resolution: "`worktree_id = sha256(git_dir_path.encode())[:16]` (first 16 hex chars). Implemented solely in `engram_core/identity.py`. All hooks and engines must call `identity.get_worktree_id()` — never re-derive locally."

#### [SP-11] content_sha256 entry content exclusion boundary underspecified

**Files:** types.md

Fix: Define exact byte range: "All text between the blank line following the `lesson-meta` comment and the start of the next `### ` heading (exclusive), after applying `knowledge_normalize`. The heading line itself is included; trailing blank lines before the next heading are excluded."

#### [SP-13] Staging cap count-then-write race (non-atomic)

**Files:** types.md, enforcement.md

Fix: Document as accepted trade-off: Add to enforcement.md §Staging Inbox Cap: "The cap check is non-atomic (TOCTOU). Cross-worktree concurrent distills can briefly overshoot the cap. This is acceptable — the cap is a soft limit protecting against accumulation, not a hard quota. Slight overshoot is bounded by concurrency degree." Add to decisions.md §Named Risks.

#### [CC-1] reader_protocol.py assigned conflicting contents across 3 files

**Files:** storage-and-indexing.md, foundations.md

Fix: Align to delivery.md (most specific — Step 0a deliverable table): `QueryResult` lives in `types.py`. Change storage-and-indexing.md comment to `# NativeReader protocol definition`. Leave foundations.md as-is (already says "NativeReader protocol definition only").

#### [CC-9] Status Vocabulary missing context subsystem entries

**Files:** storage-and-indexing.md

Fix: Add `| context | active, archived |` to the Status Vocabulary table.

#### [CE-7] /curate publish dedup-within-lock race

**Files:** operations.md

Fix: Add to operations.md curate mechanics: "The dedup check against published entries must occur within the same lock scope as the write (after acquiring `fcntl.flock(LOCK_EX)` on `learnings.md.lock`). This ensures no concurrent `/learn` write can interleave between dedup check and append."

### P2 Findings

#### [SP-2] DeferEnvelope idempotency uses bare record_id — cross-subsystem collision

**Files:** types.md

Fix: Use full canonical `RecordRef` serialization in all envelope idempotency materials: `source_ref.to_str()` instead of bare `source_ref.record_id`.

#### [SP-6] work_dedup_fingerprint separator `\|` ambiguous

**Files:** types.md

Fix: Replace markdown-escaped `"\|"` with unambiguous code: `sha256(work_normalize(problem_text) + "|" + ",".join(sorted(key_file_paths)))` in a code fence.

#### [SP-9] EnvelopeHeader.emitted_at has no UTC/timezone requirement

**Files:** types.md

Fix: Add "UTC" qualifier to `emitted_at`, `lesson-meta.created_at`, and all ISO 8601 timestamp fields that lack it. Require suffix `Z` or `+00:00`.

#### [SP-10] VERSION_UNSUPPORTED "expected range" contradicts exact-match

**Files:** operations.md

Fix: Change "expected range" to "expected version" (singular) in operations.md §Envelope Invariants.

#### [SP-12] promote-meta serialization example field order inconsistent

**Files:** types.md

Fix: State explicitly: "`promote-meta` and `lesson-meta` JSON is serialized with `sort_keys=True`." Update serialization example to show alphabetically sorted fields.

#### [SP-14] LedgerEntry major-version comparison algorithm unspecified

**Files:** types.md

Fix: Define in §Compatibility Rules or §Version Evolution Policy: "Parse `schema_version` as `<major>.<minor>`. Compare `major` as integer. Skip entries where `major` differs from the reader's built-in major."

#### [SP-15] Context archived status not derivable from snapshot content

**Files:** storage-and-indexing.md

Fix: Specify derivation: "`context` status is determined by path structure — snapshots in `snapshots/.archive/` have status `archived`; all others have status `active`. The Context reader uses path-based status derivation."

#### [CC-2] canonical.py missing from foundations.md package structure

**Files:** foundations.md

Fix: Add `canonical.py  # Deterministic JSON serialization for idempotency keys` to the `engram_core/` block.

#### [CC-4] Term drift "(Staging)" vs "(Staged)"

**Files:** types.md

Fix: Standardize types.md heading to "(Staged)" to match operations.md (behavior_contract authority).

#### [CC-5] Informal "Step-3-failure case" term undefined

**Files:** types.md

Fix: Replace with: "alongside the promote Step 3 failure case (see [Failure Handling](operations.md#failure-handling))".

---

## Commit 4 — Verification and Authority: Tests + Placement Fixes

**Finding count:** 19 P1 + 10 P2 = 29 findings
**Files:** delivery.md (primary), foundations.md, operations.md, skill-surface.md, types.md, decisions.md

### Authority Placement Fixes (P1)

#### [AA-3 + AA-4] Architecture rules misplaced outside foundation authority (Cluster C)

**Files:** foundations.md, enforcement.md, storage-and-indexing.md

Fix for AA-3: Move "Enforcement Boundary Constraint" from enforcement.md to foundations.md as a named corollary of Pre/Post-Write Validation Layering. Replace in enforcement.md with cross-reference.

Fix for AA-4: Add corollary in foundations.md §Shadow Authority Anti-Pattern: "IndexEntry is discovery-only — no mutation, policy, or lifecycle decisions from IndexEntry alone. See [IndexEntry contract](storage-and-indexing.md#indexentry)." Full interface contract stays in storage-and-indexing.md.

#### [AA-2 + CE-12 + VR-11] /save delegation test under-specification (Cluster A)

**Files:** skill-surface.md, delivery.md

Fix for AA-2: Remove verification specification from skill-surface.md line 40. Replace with cross-reference: "Verified by automated delegation test — see [cross-cutting verification](delivery.md#cross-cutting-verification)."

Fix for CE-12 + VR-11: Extend delivery.md Cross-Cutting Verification: "(1) Spy test: mock the shared entrypoint, invoke `/save`, assert mock called exactly once for defer and once for distill with the same arguments as the standalone call. Same entrypoint = identical Python function object (module + qualified name). (2) Parity test: run `/save` and standalone `/defer` with fixture snapshot, assert identical `IndexEntry` output. (3) Partial-failure parity: `/save` with distill engine disabled → same defer output as standalone `/defer`."

### Verification Additions (Cluster B + all VR-*)

#### [VR-3 + IE-4] SessionStart timing budget (Cluster B)

**Files:** delivery.md, enforcement.md

Fix: Update VR-4 specification: "(1) Specify as median over 5 runs; (2) calibrate fixture to realistic max (200 snapshots for 90-day TTL × 2/day); (3) environment qualifier: 'local filesystem with reasonable I/O latency'; (4) cleanup abort: if per-file-operation exceeds 5ms, abort cleanup with warning rather than blocking."

#### [VR-4] Write concurrency test

**Files:** delivery.md

Fix: Add to Step 2a Required Verification: "Concurrent write test: two threads calling Knowledge publish simultaneously → both entries in `learnings.md` without corruption, lock file absent post-operation. Timeout test: hold lock externally → publish returns error within 5 seconds."

#### [VR-5] PromoteEnvelope idempotency test

**Files:** delivery.md

Fix: Add to Step 2a Required Verification: "PromoteEnvelope idempotency: submit Branch A eligible lesson → promote-meta written. Submit identical PromoteEnvelope again → Branch B1 rejection, no new CLAUDE.md write."

#### [VR-6] canonical_json_bytes() rejection cases untested

**Files:** delivery.md

Fix: Add to Step 0a Required Verification: "(a) `canonical_json_bytes({\"k\": None})` raises ValueError; (b) `canonical_json_bytes({\"k\": 3.14})` raises TypeError; (c) key sorting determinism; (d) byte-identical across two calls."

#### [VR-7] Compatibility harness has no pass threshold

**Files:** delivery.md

Fix: Add to Step 3a: "Harness pass threshold: 100% of ported compatibility-critical fixtures must match on response envelope, on-disk output, and audit side effects. Harness exceptions (intentional behavioral differences) capped at 5, each requiring a comment explaining the divergence."

#### [VR-8] Trust triple partial-triple validation untested

**Files:** delivery.md

Fix: Add to Step 3a Required Verification: "(a) `hook_injected=True` only (missing other two) → rejected; (b) all three present but one empty string → rejected; (c) complete valid triple → accepted. All cases return structured error, not exception."

#### [VR-9] parse_sha256_hex() rejection cases untested

**Files:** delivery.md

Fix: Add to Step 0a Required Verification: "(a) accepts 64-char lowercase hex; (b) accepts `sha256:<hex>` (strips prefix); (c) rejects uppercase hex; (d) rejects `SHA256:<hex>`; (e) rejects `sha384:<hex>`; (f) rejects 63-char hex; (g) round-trip: `parse_sha256_hex(f'sha256:{h}') == h`."

#### [VR-10] Degradation model scenarios untested

**Files:** delivery.md

Fix: Add to Step 0a Required Verification: "(a) private root non-existent → `degraded_roots == ['private']`, shared entries returned; (b) knowledge reader raises RuntimeError → `degraded_subsystems` contains 'knowledge', other entries returned; (c) both roots unavailable → `entries == []`."

#### [VR-12] Archive-before-state-write ordering untested

**Files:** delivery.md

Fix: Add to Step 4a Required Verification: "Simulate archive failure (mock raises OSError mid-write). Assert no chain state file exists. Subsequent `/load` with healthy archive produces valid chain file."

#### [VR-13] Ledger append failure isolation untested

**Files:** delivery.md

Fix: Add to Step 3a Required Verification: "Make shard file read-only. Run `/defer` end-to-end. Assert: ticket created, no exception propagated, subsequent query notes ledger gap."

#### [VR-14] engram_quality Warn-not-Block contract untested

**Files:** delivery.md

Fix: Add to Step 4a Required Verification: "(a) Simulate readback failure → hook returns exit code 0, not 2; (b) missing required frontmatter → hook emits warning, exit code 0; (c) no Block decisions in output path."

### P2 Findings

#### [AA-5] foundations.md promote-meta gating is behavior_contract in architecture_rule file

**Files:** foundations.md

Fix: Reframe as design principle: "promote-meta is classified as authoritative promotion-lifecycle state (not auxiliary), because its presence/absence controls the promote state machine (see [operations.md](operations.md#promote-knowledge-to-claudemd))."

#### [AA-6] decisions.md named risks contain normative behavioral claims

**Files:** decisions.md

Fix: Rewrite named risk rows to contain only: risk name/severity, mitigation approach (pointer to authoritative spec), detection mechanism. Remove normative behavioral statements; replace with cross-references.

#### [AA-7] VERSION_UNSUPPORTED error code introduced without data-contract anchor

**Files:** types.md

Fix: Add subsection to types.md under Envelope Protocol compatibility formally defining the `VERSION_UNSUPPORTED` error: structure, required fields (error code, received version, expected version).

#### [IE-9] CLAUDE.md concurrent promotion concurrency unspecified

**Files:** types.md

Fix: Add CLAUDE.md to write concurrency section: "Cross-worktree concurrent promotions are delegated to git merge (same as learnings.md). Interleaved marker insertions from concurrent promotions of different lessons are safe (distinct `lesson_id` in markers → non-overlapping content)."

#### [IE-11] Promote Step 3 failure detection relies solely on /triage

**Files:** enforcement.md

Fix: Add note to hooks table: "Step 3 promote-meta failures are only detectable via `/triage` (engine Bash writes are not observable by `engram_register`)." Optionally add `promote_meta_written` to event vocabulary for future ledger-based verification.

#### [VR-15] engram init idempotency conflict case undefined

**Files:** delivery.md

Fix: Add to Step 0b Required Verification: "(a) absent → creates valid UUIDv4; (b) present with valid UUID → no-op, exits 0; (c) present with malformed content → error instructing manual repair."

#### [VR-16] Snapshot boolean normalization untested

**Files:** delivery.md

Fix: Add to VR-12: "String boolean normalization: snapshot with `save_expected_defer: \"true\"` (quoted string) → `/triage` interprets as boolean `true`."

#### [VR-17] SessionStart cleanup cap boundary behavior untested

**Files:** delivery.md

Fix: Add to VR-4: "Cap enforcement: 100 expired snapshots → exactly 50 deleted, 50 remain. Run again → 50 more deleted."

#### [VR-18] Migration idempotency new-source-files case

**Files:** delivery.md

Fix: Add to SY-6: "After run 1, add two new source files. Run migration again. Assert original files in `skipped_exists`, new files in `copied`."

#### [VR-19] Text search AND semantics + substring untested

**Files:** delivery.md

Fix: Add to Step 0a Required Verification: "(a) multi-token AND: both tokens must match; (b) single-token miss returns nothing; (c) case-insensitive; (d) substring matching."

#### [VR-20] All-13-skills smoke test deferred to Step 5 only

**Files:** delivery.md

Fix: Change to progressive invariant: "At each step, all skills activated by or before that step must pass their smoke test." Add shared smoke-test runner invoked at each step's exit gate.

#### [VR-21] Namespace status filtering rejection untested

**Files:** delivery.md

Fix: Add to Step 0a Required Verification: "`query(status='open')` without `subsystems` raises ValueError; `query(subsystems=['work'], status='open')` succeeds (auto-prefixed)."

---

## Execution Summary

| Commit | Theme | P0 | P1 | P2 | Total | Primary Files |
|--------|-------|----|----|-----|-------|---------------|
| 1 | Critical gaps + coupled | 3 | 5 | 0 | 8 | enforcement, operations, delivery, skill-surface, foundations |
| 2 | Enforcement boundaries | 0 | 9 | 6 | 15 | enforcement, operations, foundations |
| 3 | Schema & persistence | 0 | 11 | 10 | 21 | types, storage-and-indexing, operations, foundations |
| 4 | Verification & authority | 0 | 19 | 10 | 29 | delivery, foundations, skill-surface, types, decisions |
| **Total** | | **3** | **44** | **26** | **73** | |

## Verification

After all 4 commits, run a targeted re-review focusing on:
1. SY-1 fix closes all three constituent findings (CE-3, IE-2, IE-13)
2. All 6 SY merged findings have coherent cross-file resolutions
3. Authority placement moves preserve claim_precedence (spec.yaml)
4. No new orphaned cross-references introduced by section moves
5. delivery.md Required Verification total count matches the additions

## Decision Gates

- **After Commit 1:** If the `/learn` enforcement path design (route through engine vs. direct write with exception) surfaces new concerns, pause before Commit 2 to reassess.
- **After Commit 3:** If RecordRef serialization format (SP-3) conflicts with any existing code in the bridge adapter design, adjust before Commit 4 adds delivery.md tests that reference it.
