# Engram Spec Remediation Plan — Round 3

**Source:** `.review-workspace/synthesis/report.md` (6-reviewer team + CE late delivery, 2026-03-22)
**Scope:** 59 canonical findings (5 P0, 30 P1, 24 P2) across 8 normative files
**Spec:** `docs/superpowers/specs/engram/` (10 files, ~1709 lines)
**Dominant pattern:** Missing verification paths (5 P0) + underspecified enforcement boundaries (14 P1 across enforcement.md)

## Design Decisions (Resolved via Codex Dialogue)

Two findings required design decisions. Both resolved via Codex dialogue (thread `019d13f2-3b47-7d90-b16e-59df0c05f1e1`, 4 turns, converged).

### DD-1: Context Trust Model (SY-7/CE-7) → Remove from trust triple scope

**Decision:** Option A — remove Context from Step 2 mutating entrypoints list.

**Rationale:** The structural argument is airtight (Write/Edit cannot participate in Bash-mediated trust injection). The spec already establishes three consistent clauses: enforcement.md:41 (intentional exclusion from path blocking), enforcement.md:72 (PostToolUse must not become enforcement boundary), enforcement.md:148 (Context autonomy = None). The Step 2 list was simply inconsistent. Codex initially proposed a "separate enforcement model" framing, then conceded after pressure-testing that path classification without blocking is not authorization. Context integrity relies on provenance fields in snapshot frontmatter + advisory quality hooks + detective controls via `/triage`.

**Spec changes:**
- enforcement.md: Remove Context from §Step 2 mutating entrypoints, scope to Work and Knowledge
- enforcement.md: Expand §Intentional Exclusions to cover trust injection exclusion
- operations.md: Narrow Core Rules trust triple requirement to Work/Knowledge only
- delivery.md: Add verification step (grep Context scripts for `collect_trust_triple_errors`, assert zero)

### DD-2: Version Compatibility (SY-12/CE-14) → Same-major + Minor Bump Safety Contract

**Decision:** Option A with safety constraint — make `lesson-meta.meta_version` same-major tolerant for query, addressability, dedup, and rewrites. `promote-meta` retains exact-match for state-machine interpretation.

**Rationale:** The field-preservation rule at types.md:447 implicitly assumes same-major reads are possible (you cannot preserve unknown fields in a record you never read). What makes this safe: a **Minor Bump Safety Contract** constraining minor bumps — "an older reader ignoring a new field must produce identical results for every operation it supports." This was a genuinely collaborative product of the dialogue (emerged at T3, agreed T4). Content_sha256 dedup is safe under same-major because changing hash semantics is a breaking change (major bump).

**Spec changes:**
- types.md: Change Knowledge entry metadata compatibility row from exact-match to same-major tolerance
- types.md: Tighten minor bump trigger to require semantics-preservation
- types.md: Add new `### Minor Bump Safety Contract` subsection
- types.md: Clarify promote-meta retains exact-match for state-machine interpretation specifically
- storage-and-indexing.md: Clarify same-major lesson-meta versions are indexed; different-major skipped

---

## Strategy

Three commits, ordered by dependency and priority:

1. **P0 critical gaps + security-boundary P1s** — all P0 verification paths + trust/security fixes
2. **P1 enforcement + operations underspecification** — hook contracts, missing definitions, authority fixes + design decision results
3. **Remaining P1 + all P2** — schema gaps, VR additions, cross-refs, cosmetic

Rationale: Commit 1 must land first (P0s are "build the wrong system" severity). Commit 2 depends on design decisions DD-1 and DD-2. Commit 3 is independent of design decisions but benefits from commit 2's enforcement definitions for cross-referencing.

---

## Commit 1 — P0: Critical Verification Gaps + Security-Boundary P1

**Finding count:** 5 P0 + 5 P1 = 10 findings
**Files:** enforcement.md, delivery.md, operations.md, types.md, skill-surface.md

### P0 Findings

#### [SY-1] Contradictory activation step for idempotency enforcement

**Files:** enforcement.md
**Fix:** enforcement.md line 118: change "Step 4" → "Step 3a". Per `claim_precedence` for `behavior_contract`, operations.md wins. delivery.md VR-11 placement confirms Step 3a.

#### [SY-2] No verification for `work_dedup_fingerprint` formula

**Files:** delivery.md
**Fix:** Add formula contract test to delivery.md Step 1 or 3a:
- Assert formula: `sha256(work_normalize(text) + "|" + ",".join(sorted(paths)))`
- Test separator character is `"|"` (not `"/"` or `","`)
- Test path sort order is lexicographic
- Test `work_normalize()` is applied before hashing

#### [SY-3] No verification for fence-aware `knowledge_normalize`

**Files:** delivery.md
**Fix:** Add fence-aware test cases to delivery.md Step 0a:
- Test normalization rules 3-6 are suspended inside fenced code blocks
- Test nested fences (triple-backtick inside quadruple-backtick)
- Test unclosed fence at end-of-file
- Test fence with info string (e.g., ` ```python `)

#### [SY-4] No verification for multi-producer concurrent writes

**Files:** delivery.md
**Fix:** Add concurrent write test to delivery.md Step 4a:
- Two producers (engine + `engram_register` hook) write to same JSONL shard simultaneously
- Assert no data loss, no corrupted lines
- Test fcntl/lockf contention under concurrent append

#### [SY-5] All-mutating-entrypoints trust triple coverage test absent

**Files:** delivery.md
**Fix:** Add coverage assertion to delivery.md Step 3a (scope depends on DD-1 resolution):
- Static analysis or spy test asserting `collect_trust_triple_errors()` is invoked at every documented mutating entrypoint
- Cross-reference enforcement.md §Step 2 entrypoint list for the complete set

### Coupled P1 Findings (security boundary)

#### [SY-7/CE-7] Context trust injection structurally unreachable — DD-1 RESOLVED

**Files:** enforcement.md, operations.md
**Fix:** Remove "Context: snapshot write, checkpoint write" from enforcement.md §Step 2 mutating entrypoints list. Scope trust triple validation to "Work and Knowledge subsystem engines" only. Expand §Intentional Exclusions to cover trust injection exclusion. Narrow operations.md Core Rules from "every mutating engine entrypoint" to "every mutating Work or Knowledge engine entrypoint." Add clarifying note: "Context write integrity relies on provenance fields in snapshot frontmatter + advisory quality hooks + detective controls via `/triage`."

#### [SY-51/CE-2] Trust injection order relative to idempotency check

**Files:** enforcement.md
**Fix:** Add to enforcement.md §Step 2: "Trust validation precedes all other processing, including idempotency key lookups and dedup reads. The trust triple is verified as the first operation in any engine entrypoint call."

#### [SY-53/CE-4] `DistillEnvelope.durability` in idempotency material

**Files:** types.md
**Fix:** Remove `durability` from DistillEnvelope idempotency material table. Material becomes: `{source_ref.to_str(), candidates: sorted([{content_sha256, source_section}, ...], key=lambda c: c["content_sha256"])}`. Update rationale to clarify durability is advisory metadata, not semantic identity.

#### [SY-54/CE-6] `/learn` "direct publish" contradicts engine-routed trust injection

**Files:** skill-surface.md
**Fix:** Update trigger differentiation: "/learn ... capture one insight manually (publishes to learnings.md via Knowledge engine entrypoint with lesson-meta; not a direct Write tool call)." Remove "direct publish" language.

#### [SY-56/CE-12] Trust triple fields have no canonical Python type

**Files:** types.md
**Fix:** Add `TrustPayload` TypedDict to types.md §Core Types:
```python
class TrustPayload(TypedDict):
    hook_injected: bool
    hook_request_origin: str
    session_id: str
```
Reference from enforcement.md §Step 1 as the canonical type for payload file contents.

---

## Commit 2 — P1: Enforcement Boundaries + Operations Gaps

**Finding count:** 14 P1 findings
**Files:** enforcement.md, foundations.md, operations.md, types.md, delivery.md, storage-and-indexing.md
**Dependency:** DD-1 and DD-2 must be resolved before SY-10 and SY-12.

### Enforcement Underspecification (enforcement.md)

#### [SY-13] `engram_guard` On-Failure conflates Write/Edit blocking with Bash best-effort

**Fix:** Split hook table or add footnote: "Block (Write/Edit: reliable; Bash: best-effort — see §Enforcement Scope)."

#### [SY-14] Trust injection "payload file" undefined

**Fix:** Add §Payload File Convention under §Trust Injection:
- Path convention: how hook communicates path to engine (e.g., `--payload-file <path>` CLI argument)
- Creator: skill creates file before engine invocation
- Missing-file behavior: fail-closed (Block with diagnostic)

#### [SY-15] `engram_scripts_dir` never defined

**Fix:** Define derivation: `engram_scripts_dir = Path(__file__).parent` (resolved from `engram_core/` package location). Specify failure mode if path resolution fails.

#### [SY-16] `work_max_creates` session cap has no enforcement owner

**Fix:** Specify Work engine as enforcer. Add to enforcement.md §Configuration or §Enforcement Scope.

#### [SY-17] "Session diagnostic channel" undefined

**Fix:** Define in enforcement.md: storage path (e.g., `~/.claude/engram/<repo_id>/ledger/diagnostics.jsonl`), entry format (`session_id`, `ts`, `failure_type`, `error_message`), lifetime (session-scoped or TTL). Cross-reference from operations.md §Triage.

#### [SY-18] `engram_register` worktree_id resolution unspecified

**Fix:** Extend worktree_id recomputation requirement from `engram_guard` to all hooks that use `worktree_id` (including `engram_register`).

#### [SY-19] `knowledge_staging` protected path uses unexpanded tilde

**Fix:** Add tilde expansion to canonicalization spec. All path matching must expand `~` before comparison.

#### [SY-20] `.engram-id` unprotected

**Fix:** Add `.engram-id` to protected-path table in enforcement.md. Direct Write/Edit blocked by `engram_guard`.

#### [SY-21/CE-5] Enforcement exception sequencing rule misplaced

**Files:** enforcement.md, foundations.md
**Fix:** Move sequencing rule ("foundations.md is the authoritative source for new exceptions") from enforcement.md §Enforcement Exceptions to foundations.md §Permitted Exceptions as a new "Adding New Exceptions" subsection. enforcement.md references foundations.md instead of declaring the rule.

### Operations + Skill Surface Gaps

#### [SY-52/CE-3] Branch B2 promote Step 3 trigger undefined

**Files:** operations.md
**Fix:** Add explicit sub-sequence for Branch B2 in Step 3: after user confirms placement and skill wraps in markers (end of Step 2), the engine retrieves text between markers and recomputes `drift_hash()`, then writes promote-meta. Clarify this occurs within the same `/promote` invocation.

#### [SY-55/CE-11] `work_dedup_fingerprint` 24-hour window absent from Defer pseudocode

**Files:** operations.md
**Fix:** Add dedup sequence to operations.md §Defer: "(1) Envelope-level: check `idempotency_key` against existing tickets. (2) Content-level: check `work_dedup_fingerprint(problem, key_file_paths)` against tickets within past 24 hours. If match, return existing ticket_ref." Cross-reference types.md §work_dedup_fingerprint.

#### [SY-10/CE-13] `snapshot_written` orchestrated_by — expand value set

**Files:** operations.md, types.md
**Fix:** Add emit specifications to operations.md per producer:
- `/save`: emit with `orchestrated_by: "save"`
- `/quicksave`: emit with `orchestrated_by: "quicksave"`
- `/load` (archive path): emit with `orchestrated_by: "load"`
Update types.md event vocabulary to document full value set.

#### [SY-12/CE-14] Version compatibility reconciliation — DD-2 RESOLVED

**Files:** types.md, storage-and-indexing.md
**Fix:** Change Knowledge entry metadata compatibility from exact-match to same-major tolerance for query, addressability, dedup, and rewrites. Add `### Minor Bump Safety Contract` subsection: "an older reader ignoring a new field must produce identical results for every operation it supports." Tighten minor bump trigger definition. Clarify promote-meta retains exact-match for state-machine interpretation. Update storage-and-indexing.md RecordMeta field mapping note.

### VR ID Disambiguation (delivery.md prerequisite)

#### [SY-6] Duplicate VR identifiers — 11+ IDs reused

**Files:** delivery.md
**Fix:** Assign globally unique VR IDs using step-scoped prefixes (e.g., `VR-0a-1`, `VR-3a-8`) or monotonic continuation. Update all cross-references (VR-18 → VR-13 disambiguation). This is a large mechanical change touching ~50 VR items.

---

## Commit 3 — Remaining P1 + All P2

**Finding count:** 11 P1 + 24 P2 = 35 findings
**Files:** types.md, delivery.md, enforcement.md, operations.md, foundations.md, README.md, storage-and-indexing.md

### P1: Schema Gaps (types.md)

| SY-ID | Finding | Fix |
|-------|---------|-----|
| SY-8 | `content_sha256` byte range undefined for last entry | Specify end-of-file terminator rule |
| SY-9 | `DeferEnvelope.context` nullable + no None-exclusion rule | Add explicit construction rule for `canonical_json_bytes` |
| SY-11 | Staging file serialization format unspecified | Add staging file format subsection |

### P1: Cross-References + Structure (types.md, delivery.md)

| SY-ID | Finding | Fix |
|-------|---------|-----|
| SY-22 | Broken anchor: `#recordref--lookup-key` (double-hyphen) | `#recordref-lookup-key` |
| SY-23 | Broken anchors: `#legacy-entries-missing-meta_version` (2x) | `#legacy-entries-missing-metaversion` |
| SY-24 | VR-12/VR-16 co-located in single bullet | Extract as separate bullet |

### P1: Missing Verification (delivery.md, skill-surface.md)

| SY-ID | Finding | Fix |
|-------|---------|-----|
| SY-25 | `engram init --force` undocumented | Document in skill-surface.md or remove delivery.md reference |
| SY-26 | SessionStart timing test median vs worst-case | Align test to P95/P99 budget semantics |
| SY-27 | No `RecordRef.from_str()` round-trip test | Add to Step 0a |
| SY-28 | `DeferEnvelope.context` exclusion from idempotency key untested | Add negative test |
| SY-29 | `IndexEntry.snippet` 200-char cap untested | Add per-reader cap test |

### P2: All 24 Findings

| SY-ID | File | Finding | Fix |
|-------|------|---------|-----|
| SY-30 | enforcement.md | Delivery-scoped milestone claim in §Bridge Period | Move to delivery.md |
| SY-31 | enforcement.md | Wrong anchor for Phase-Scoped Idempotency | Fix anchor |
| SY-32 | README.md | `supporting` authority description incomplete | Add "reference material" |
| SY-33 | delivery.md | Step 0a VR items non-sequential | Reorder (secondary to SY-6) |
| SY-34 | delivery.md | Bridge test scope "Steps 1-4" vs "Steps 1-3" | Align |
| SY-35 | delivery.md | Missing cross-ref to enforcement.md trust triple | Add cross-ref |
| SY-36 | types.md | `DistillEnvelope` content exclusion rationale missing | Add rationale |
| SY-37 | types.md | Staging filename date source undefined | Specify date source |
| SY-38 | types.md | `RecordRef` field constraints deferred | Confirmed deferred — add cross-ref to decisions.md |
| SY-39 | types.md | `LedgerEntry.payload` untyped dict | Add payload schema note |
| SY-40 | types.md | `promote-meta` parse-time behavior for missing fields | Specify defaults |
| SY-41 | enforcement.md | `engram_session` abort condition delivery-only | Add to enforcement spec |
| SY-42 | enforcement.md | `engram_quality` no Block guard | Add implementation note |
| SY-43 | enforcement.md | Bridge period guard gap undocumented | Document expected gap |
| SY-44 | enforcement.md | `collect_trust_triple_errors()` return type unspecified | Specify return type |
| SY-45 | delivery.md | No `knowledge_normalize` tilde fence test | Add test case |
| SY-46 | delivery.md | Compatibility harness cap (5) unenforced | Add automated check |
| SY-47 | delivery.md | No `RecordMeta` N/A field test | Add per-subsystem test |
| SY-48 | delivery.md | `degraded_subsystems` counter untested | Add counter test |
| SY-49 | delivery.md | Branch D promote exclusion untested | Add test |
| SY-50 | delivery.md | `worktree_id` derivation identity untested | Add identity test |
| SY-57 | types.md | `DeferEnvelope.context` rationale in wrong authority | Move rationale to operations.md or decisions.md |
| SY-58 | enforcement.md | Config read semantics inconsistent | Add config read-time statement |
| SY-59 | enforcement.md | `engram_quality` Edit readback missing-file behavior | Specify warning + exit 0 |

---

## Dependency Map

```
DD-1 (RESOLVED: remove Context) ──┐
                                   ├──► Commit 1 (SY-5, SY-7 unblocked)
                                   │
DD-2 (RESOLVED: same-major) ──────┼──► Commit 2 (SY-12 unblocked)
                                   │
Commit 1 ─────────────────────────┼──► Commit 2 (P0 must land first)
                                   │
Commit 2 ─────────────────────────┴──► Commit 3 (enforcement definitions available for cross-refs)
```

All design decisions resolved. No blockers remain.

## Verification

After each commit:
1. All spec files parse as valid markdown
2. All cross-references resolve (anchors, VR IDs, section references)
3. No new authority violations per spec.yaml `claim_precedence`
4. `wc -l` delta reported for each file
