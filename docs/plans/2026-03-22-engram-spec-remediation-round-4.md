# Engram Spec Remediation Plan — Round 4

**Source:** `.review-workspace/synthesis/report.md` (6-reviewer team, 2026-03-22)
**Scope:** 59 canonical findings (4 P0, ~28 P1, ~27 P2) across 8 normative files
**Spec:** `docs/superpowers/specs/engram/` (10 files, ~160KB)
**Dominant pattern:** enforcement.md self-contradictions and underspecified hook decision logic (3/4 P0, most P1 findings originate in enforcement.md)

## Design Decisions

Three findings require judgment calls. All are resolvable from existing spec structure — no Codex consultation needed.

### DD-1: RecordMeta.schema_version for Legacy Entries (SP-1)

**Decision:** Use `"0.0"` as sentinel value for legacy Knowledge entries missing `meta_version`.

**Rationale:** `RecordMeta.schema_version` is typed `str` (not nullable). The `"0.0"` value follows semver convention, is distinct from any real version (which start at `"1.0"`), and avoids the string `"legacy"` which CC-5 already flags as an overloaded term. The reader can trivially detect `"0.0"` as pre-versioned without special-casing `None`.

**Spec changes:**
- storage-and-indexing.md: Add footnote to RecordMeta field mapping table — "When `lesson-meta` is present but `meta_version` is absent, populate `schema_version` with `'0.0'`."
- types.md §Legacy Entries: Add — "`RecordMeta.schema_version` for these entries is `'0.0'`."

### DD-2: Context Path Identity Verification (IE-3)

**Decision:** Option A — document as intentional design decision, not a gap.

**Rationale:** The autonomy model explicitly sets Context autonomy to `None`. The spec already establishes three consistent clauses: (1) Context paths excluded from protected-path enforcement, (2) `collect_trust_triple_errors()` not invoked for direct-write paths, (3) `/triage` anomaly detection is the detective control. Adding identity verification to `engram_guard` for Context would contradict the autonomy model and add enforcement to a subsystem designed for advisory-only controls.

**Spec changes:**
- enforcement.md §Direct-Write Path Authorization: Add explicit note — "Context paths allow Write/Edit from any source. Identity verification is intentionally omitted — `/triage` anomaly detection (not `engram_guard`) is the enforcement layer for Context path integrity. See foundations.md §Autonomy Model."

### DD-3: Branch D vs Legacy Entry Promote Eligibility (CE-5)

**Decision:** Operations.md Branch D exclusion is authoritative. Update types.md to align.

**Rationale:** Per `spec.yaml` claim_precedence, `behavior_contract` authority order is `[operations, skill-contract, foundation, decisions]`. Operations.md wins for behavioral decisions about promote eligibility. Types.md's "lesson itself remains valid" is true (the lesson IS valid), but "valid" does not mean "eligible for promotion" — Branch D explicitly excludes it from the candidate list pending migration.

**Spec changes:**
- types.md §Legacy Entries: Clarify — "The lesson remains valid for query and display. However, promotion eligibility requires interpretable promote-meta — entries with unrecognized or missing `meta_version` are excluded from the promote candidate list per operations.md §Promote Branch D."

---

## Strategy

Three commits, ordered by dependency and priority:

1. **P0 critical fixes + security-boundary P1s** — all contradictions that cause wrong implementations + trust/security enforcement gaps
2. **Corroborated P1 clusters + enforcement/schema underspecification** — merged findings with multi-reviewer support + remaining enforcement and data-contract gaps
3. **Remaining P1 (verification gaps) + all P2** — missing VR codes, broken anchors, schema imprecision, cosmetic

**Rationale:** Commit 1 must land first — P0 findings cause implementers to build the wrong system. Commit 2 depends on commit 1's capability name split (SY-2) being in place before authority placement fixes reference the new names. Commit 3 is largely independent but benefits from commits 1–2's structural fixes for correct cross-referencing.

---

## Commit 1 — P0: Critical Contradictions + Security-Boundary P1

**Finding count:** 4 P0 + 7 P1 = 11 findings
**Files:** enforcement.md, delivery.md, types.md, skill-surface.md

### P0 Findings

#### [SY-1] engram_guard deployment timing self-contradiction

**Files:** enforcement.md
**Fix:** Rewrite enforcement.md §Bridge Period Limitations. Replace "engram_guard is not deployed until Step 3a" with: "engram_guard ships at Step 2a (engine_trust_injection capability only — Knowledge engine mutating entrypoints). Step 3a extends the guard with protected-path enforcement for Work paths. Step 4a adds direct-write path authorization for Context paths. During Steps 0a–1, no guard capabilities are active."

Delete or correct any statement claiming the guard is absent before Step 3a.

**Dependency:** Resolves IE-12 (P2, staging cap timing) — once guard is confirmed at 2a, the staging cap concern becomes moot.

#### [SY-2] write_path_authorization capability step conflict

**Files:** enforcement.md, delivery.md
**Fix — enforcement.md:** Split `write_path_authorization` in the guard capability rollout table into two rows:

| Capability | Step | Scope |
|---|---|---|
| `work_path_enforcement` | Step 3a | Protected-path block for Write/Edit to Work and Knowledge paths |
| `context_direct_write_authorization` | Step 4a | Direct-write path authorization for Context snapshot/checkpoint paths |

**Fix — delivery.md:** In Step 3a deliverables table, replace "direct-write path authorization for Work paths" with "protected-path enforcement for Work paths." In Step 4a deliverables, reference `context_direct_write_authorization` by name.

#### [SY-6] write_path_authorization has no verification path

**Files:** delivery.md
**Fix:** Add VR-4A tests for context direct-write path authorization:
- VR-4A-19: (a) Write to `~/.claude/engram/<different_repo_id>/snapshots/test.md` → assert blocked by `engram_guard`; (b) Write to correct repo's `snapshots/test.md` → assert allowed; (c) Write with path traversal (`snapshots/../other_file.md`) → assert blocked after canonicalization.

#### [SY-8] Step 5 cleanup has no Required Verification section

**Files:** delivery.md
**Fix:** Add `### Required Verification` to Step 5 with:
- VR-5-1: `grep -r "bridge_adapter\|SourceResolver\|DeferredWorkEnvelope" packages/plugins/engram/` returns zero results
- VR-5-2: Old plugin directories (`packages/plugins/handoff/`, `packages/plugins/ticket/`) absent
- VR-5-3: `grep -r "handoffs/\|plugins/ticket\|plugins/handoff" .claude/skills/ .claude/hooks/ .claude/agents/` returns zero results
- VR-5-4: Old data directories (`docs/tickets/`, `docs/learnings/`) absent
- VR-5-5: All 13 skill smoke tests pass (final progressive gate)

### Coupled P1 Findings

#### [SY-7] engram_guard Write/Edit decision algorithm missing 3-branch logic

**Files:** enforcement.md
**Fix:** Add explicit decision algorithm to §Trust Injection (or new §Guard Decision Algorithm subsection):

```
engram_guard decision algorithm:
  1. If tool_name == Bash AND matches engine_*.py pattern:
     → Engine trust injection (write TrustPayload, allow)
  2. If tool_name in {Write, Edit} AND path within Context private root:
     → Direct-write path authorization (allow + post-write quality)
  3. If tool_name in {Write, Edit} AND path in protected-path table:
     → Block with path-class diagnostic
  4. Otherwise:
     → Allow unconditionally (engram_guard does not restrict general writes)
Branches evaluated in this order. Step 2 failing (not Context-owned) routes to step 3.
```

**Depends on:** SY-2 (uses new capability names `work_path_enforcement` and `context_direct_write_authorization`).

#### [SY-4 + CC-4] TrustPayload type too permissive + validator signature mismatch

**Files:** types.md, enforcement.md
**Root cause:** Three separate findings (AA-1, CE-16, SP-2 → merged as SY-4, plus CC-4) all identify the same gap: `TrustPayload.hook_request_origin` is typed `str` but the validator constrains to `{"user", "agent"}`, and the validator signature accepts `str | None` while the wire format requires `str`.

**Fix — types.md:** Change `TrustPayload` definition:
```python
class TrustPayload(TypedDict):
    hook_injected: bool          # Must be True
    hook_request_origin: str     # Must be "user" | "agent" — validated by collect_trust_triple_errors()
    session_id: str              # Claude session UUID, non-empty
```

Add note below: "The `hook_request_origin` field accepts only `'user'` or `'agent'`. See enforcement.md §collect_trust_triple_errors() Contract for the closed set validation. Adding a new origin value (e.g., `'mcp'`) requires updating the validator."

**Fix — enforcement.md:** Add note to `collect_trust_triple_errors()` signature explaining that `str | None` parameters are intentional — "The validator accepts `None` to provide specific error messages when a hook omits a required field. Callers constructing a well-formed `TrustPayload` always pass `str`."

#### [CC-2] Duplicate VR-0A-10 test ID

**Files:** delivery.md
**Fix:** Renumber the second test (IndexEntry.snippet contract test) from VR-0A-10 to VR-0A-13 (next available sequential ID after VR-0A-12). Leave the first VR-0A-10 (fence-aware `knowledge_normalize` tests) in place.

#### [CC-3] skill-surface.md references non-existent VR-15

**Files:** skill-surface.md
**Fix:** Replace "delivery.md VR-15" with "delivery.md VR-0B-1" in the `engram init` `--force` cross-reference.

#### [IE-8] Payload file containment check failure mode unspecified

**Files:** enforcement.md
**Fix:** Add to §Payload File Contract after the containment row: "If the containment check fails (payload path resolves outside `.claude/engram-tmp/`), `engram_guard` blocks the Bash tool call (exit code 2) with diagnostic: `'engram_guard: payload path outside containment boundary: {path}'`. This is a security-critical check and must fail-closed."

#### [IE-9] Payload file atomic write failure mode unspecified

**Files:** enforcement.md
**Fix:** Add failure mode paragraph after §Step 1: Injection: "If the atomic write fails (fsync error, disk full, permission denied), `engram_guard` blocks the Bash tool call (exit code 2) with diagnostic: `'engram_guard: payload write failed: {error}'`. Do not allow the engine invocation to proceed with a missing payload — the resulting trust triple rejection produces a misleading error."

---

## Commit 2 — P1: Corroborated Clusters + Enforcement/Schema Underspecification

**Finding count:** ~21 P1 findings
**Files:** enforcement.md, types.md, operations.md, storage-and-indexing.md, delivery.md

### Corroborated P1 Clusters (multi-reviewer support)

#### [SY-3] engram_session "stores error state" contradicts no-shared-state

**Files:** enforcement.md
**Fix:** In §SessionStart Hook table, replace the `worktree_id` resolution failure row's "stores error state" language with: "If `worktree_id` resolution fails, `engram_session` logs a warning to the session diagnostic channel (`.diag`). `engram_guard` independently calls `identity.get_worktree_id()` at each invocation — if git state is broken, the hook fails-closed with the specific git error. No error state is stored between hooks."

Remove any implication of state passing between `engram_session` and `engram_guard`.

#### [SY-5] collect_trust_triple_errors() contract in wrong authority file

**Files:** types.md, enforcement.md
**Fix — types.md:** Add new section `### Trust Validation — collect_trust_triple_errors()` after §TrustPayload. Move the full function contract from enforcement.md: Python signature, parameter types (`str | None` with rationale), 3 validation rules (ordered), stable error string templates, return type (`list[str]`), caller obligation, and origin-matching delegation statement.

**Fix — enforcement.md:** Replace the full contract with a cross-reference: "The `collect_trust_triple_errors()` function contract (signature, validation rules, stable error strings) is specified in types.md §Trust Validation — that is the canonical source. This section specifies the enforcement mandate: every mutating Work or Knowledge engine entrypoint must invoke `collect_trust_triple_errors()` before making state changes."

**Fix — enforcement.md:** Remove stale "Module location: `engram_core/trust.py`. Add to package structure." directive (AA-3 — already listed in foundations.md).

#### [SY-9] content_sha256 byte range ambiguity

**Files:** types.md, delivery.md
**Fix — types.md:** Replace "The heading line itself is included" with explicit statement: "The current entry's `### ` heading line is NOT included in the hash input. The byte range starts at the first character after the blank line following the `lesson-meta` comment and ends at (but excludes) the next `### ` heading line. Trailing blank lines before the next heading are excluded."

**Fix — delivery.md:** Add golden-value VR to Step 0a: "VR-0A-14: Construct a two-entry `learnings.md` fixture with known content. Compute `content_hash()` on the specified byte range. Assert result equals a golden hex value embedded in the test. This locks the byte-range interpretation."

#### [SY-10] Session diagnostic channel (.diag) incomplete spec + unverified

**Files:** enforcement.md, operations.md, delivery.md
**Fix — enforcement.md §Session Diagnostic Channel:** Add directory creation requirement (IE-2): "`engram_register` must create the diagnostic directory path (`ledger/<worktree_id>/`) if absent before writing the `.diag` file. If directory creation itself fails, log to stderr (no triage impact)."

**Fix — operations.md §Triage:** Add `.diag` check step before inference matrix: "For each session being evaluated, check for `<session_id>.diag` file. If present and non-empty: cases (3) and (4) for that session surface `'ledger unavailable in session <session_id>'` rather than `'zero-output success'` or `'completion not proven'`. This is session-scoped hook-failure degradation, distinct from config-scoped `ledger.enabled=false`."

**Fix — delivery.md:** Add VR-4A-20: (a) Force `engram_register` to fail (make shard file unwritable). Assert `.diag` created with JSONL entry containing `hook`, `failure_type`, `ts` fields. (b) Run `/triage` for that session. Assert output surfaces `"ledger unavailable in session <session_id>"`. (c) Assert other sessions unaffected.

### Enforcement Underspecification

#### [CE-3] .engram-id pre-check ordering absent from operations.md

**Files:** operations.md
**Fix:** Add to §Core Rules: "Before trust triple validation, each engine entrypoint must verify `.engram-id` exists in the Engram root; if absent, return the initialization error immediately without invoking `collect_trust_triple_errors()`."

#### [CE-5] Branch D exclusion vs Legacy Entry "lesson remains valid" — DD-3 RESOLVED

**Files:** types.md
**Fix:** Per DD-3 above. Add clarifying statement to §Legacy Entries — promote-meta without meta_version.

#### [CE-7] Context skills and write_path_authorization intra-step ordering at 4a

**Files:** delivery.md
**Fix:** Add intra-step ordering note to §Step 4a: "Within Step 4a, hooks are deployed and validated before skills are activated. The `context_direct_write_authorization` guard capability must pass its VR-4A-19 tests before Context skills (`/save`, `/quicksave`, `/load`) are enabled."

#### [CE-8] /learn trust injection entrypoint enumeration ambiguous

**Files:** enforcement.md
**Fix:** Replace parenthetical in §Mutating Entrypoints with explicit enumeration:
```
Knowledge:
  (a) publish entrypoint — called by both /learn and /curate staged-publish paths
  (b) staging write entrypoint — called by /distill
  (c) promote-meta write entrypoint — called by /promote Step 3
```
Confirm that /learn and /curate call the same publish function.

#### [CE-14] promote-meta in-place replacement vs field preservation

**Files:** types.md
**Fix:** Add explicit statement to §Promotion State Record or §Compatibility Rules: "Because promote-meta uses exact-match version semantics, a Knowledge engine at v1.0 never attempts to rewrite a promote-meta entry with a different version (Branch D excludes it from all operations). Field preservation does not apply to promote-meta version mismatches — they are fully excluded, not rewritten."

#### [IE-3] Context direct-write no identity verification — DD-2 RESOLVED

**Files:** enforcement.md
**Fix:** Per DD-2 above.

#### [IE-4] Protected-path ** glob coverage of .audit/ hidden directory

**Files:** enforcement.md
**Fix:** Add note to §Protected-Path Enforcement: "Path canonicalization and `**` glob matching cover all subdirectories including `.`-prefixed ones (e.g., `.audit/`). The `engram/work/**` path class protects `engram/work/.audit/**` — all audit trail entries are engine-only."

#### [IE-5] Checkpoint frontmatter schema undefined

**Files:** enforcement.md (or types.md)
**Fix:** Define required checkpoint frontmatter fields for `engram_quality` validation:
```
Required checkpoint frontmatter fields:
  session_id: str      # From RecordMeta
  worktree_id: str     # From RecordMeta
  timestamp: str       # ISO 8601 UTC
  source_skill: str    # "quicksave"
```
Add to enforcement.md §Quality Validation scope table's "Frontmatter completeness" description, or add a new checkpoint schema to types.md and cross-reference.

#### [IE-6] Origin-matching per-entrypoint delegation has no enumeration

**Files:** enforcement.md
**Fix:** Add table to §collect_trust_triple_errors() Contract (or new §Origin-Matching):

| Entrypoint Category | Expected Origin | Examples |
|---|---|---|
| User-initiated commands | `"user"` | ticket create/update/close, promote Step 3 |
| Agent/engine-initiated operations | `"agent"` | staging write (distill), publish (learn/curate) |

Note: "The `_user.py` / `_agent.py` naming convention reflects but does not define the expected origin. This table is the normative source."

#### [CC-5] "legacy" label ambiguity in promote-meta

**Files:** types.md
**Fix:** Rewrite line 145 from "Entries lacking this field are treated as `legacy`" to: "Entries lacking this field are treated as pre-versioned entries — see [Legacy Entries](#legacy-entries-missing-metaversion) for discovery, interpretation, and rewrite rules." Remove backtick formatting around "legacy."

#### [SP-1] RecordMeta.schema_version for legacy entries — DD-1 RESOLVED

**Files:** storage-and-indexing.md, types.md
**Fix:** Per DD-1 above.

#### [SP-5] Staging file complete schema not defined

**Files:** types.md
**Fix:** Add staging file schema section or extend §DistillCandidate to include all fields present in staging files. Cross-reference the staging-meta fields that are present in staging files but not in DistillCandidate, specifying where each originates and what it represents.

#### [SP-7] promote-meta exact-match creates forward-incompatibility

**Files:** types.md
**Fix:** Add rationale note to §Compatibility Rules for promote-meta: "Exact-match is intentional. promote-meta governs a state machine (Branch A/B/C/D) where minor version changes can alter transition logic. Unlike lesson-meta (where minor bumps add optional metadata), promote-meta minor bumps can change state-machine semantics. Forward-incompatibility is the desired safety property — unknown versions are excluded, not misinterpreted."

---

## Commit 3 — P1 Verification Gaps + All P2

**Finding count:** ~7 P1 + 27 P2 = ~34 findings
**Files:** delivery.md (VR additions), enforcement.md, types.md, operations.md, storage-and-indexing.md, foundations.md, README.md, decisions.md, skill-surface.md

### P1 Verification Gaps

#### [VR-2] knowledge_max_stages < 1 rejection no VR

**Files:** delivery.md
**Fix:** Add VR-3A test: Set `knowledge_max_stages: 0` and invoke distill — assert rejection with `"knowledge_max_stages must be >= 1"` before any staging I/O. Repeat with `-1`. Test string form `"0"` for type coercion.

#### [VR-4] promote-meta exact-match on minor version bump no VR

**Files:** delivery.md
**Fix:** Add VR-4A test: Fixture with `promote-meta` having `meta_version: "1.1"` (same major, different minor). Run `/promote`. Assert: lesson excluded from candidate list. Assert: warning containing lesson_id.

#### [VR-5] LedgerEntry major-version mismatch skip no VR

**Files:** delivery.md
**Fix:** Add VR-4A test: JSONL shard with three entries — `schema_version: "1.0"`, `"2.0"` (future major), `"1.1"` (same-major minor). Assert: reader returns entries 1 and 3; entry 2 skipped; no exception.

#### [VR-6] Archived snapshot TTL cleanup no VR

**Files:** delivery.md
**Fix:** Extend VR-4A-3: Add (a) 10 archived snapshots in `.archive/` older than 90 days and (b) 3 younger than 90 days. Assert old deleted, young retained, combined cleanup respects 50-file cap.

#### [VR-7] Chain state migration valid_fresh conjunction underspecified

**Files:** delivery.md
**Fix:** Extend VR-4A-1: Add case (e) fresh-age-but-dangling fixture (age < 24h, target snapshot absent) — assert NOT migrated, classified as dangling.

#### [VR-8] SourceResolver failure path unspecified and unverified

**Files:** delivery.md
**Fix:** (1) Specify in §Bridge Field Mapping: when `session_id` is absent from frontmatter, SourceResolver returns empty string (or raises with explicit error referencing source snapshot path). (2) Add to VR-1-2: fixture with snapshot missing `session_id` — assert failure handled explicitly.

#### [VR-10] Smoke test progressive activation manifest unspecified

**Files:** delivery.md
**Fix:** Add skill activation table to §Cross-Cutting Verification:

| After Step | Active Skills |
|---|---|
| 0b | `engram init` |
| 1 | `engram init`, `/defer` |
| 2a | adds `/learn`, `/distill`, `/curate`, `/promote` |
| 3a | adds `/ticket`, `/triage` |
| 4a | adds `/save`, `/load`, `/quicksave`, `/search`, `/timeline` |

Specify this table is the canonical runner parameterization.

### Remaining P1 Schema

#### [SP-4] worktree_id hash truncation collision undetected

**Files:** types.md or decisions.md
**Fix:** Add note to §Identity Resolution: "If a collision is detected at runtime (two worktrees yielding the same `worktree_id`), the system should surface a diagnostic. The 64-bit hash space (16 hex chars) makes collision negligible for practical worktree counts but is not cryptographically guaranteed."

### P2 Findings — Broken Anchors

#### [CC-6] Broken anchor: enforcement-boundary-constraint

**Files:** enforcement.md
**Fix:** Update link from `foundations.md#enforcement-boundary-constraint` to `foundations.md#enforcement-boundary-constraint-invariant`.

#### [CC-7] Em-dash anchor pattern: 5+ sections with wrong double-hyphen

**Files:** Multiple files
**Fix:** Audit all cross-reference anchors containing em-dashes. GFM strips em-dashes entirely (not converted to hyphens). Fix each broken anchor to match the actual generated GFM anchor. The reviewer identifies 9+ affected references.

#### [CC-9] Broken anchor: legacy-entries underscore

**Files:** types.md or referencing file
**Fix:** Fix the underscore-vs-hyphen mismatch in the legacy entries anchor.

#### [CC-8] Archive-failure "resolved" vs "active limitation"

**Files:** operations.md or decisions.md
**Fix:** Clarify whether the archive-failure limitation is resolved or still active. Align description.

### P2 Findings — Minor Specification Gaps

#### [CE-4] /triage emitted_count field dependency not cross-referenced

**Files:** operations.md
**Fix:** Add explicit cross-reference in triage inference matrix case (3) to `types.md §Event Vocabulary`. Specify: if `emitted_count` absent, treat as "completion not proven."

#### [CE-6] Direct-write path authorization error format unspecified

**Files:** enforcement.md
**Fix:** Add: "If the path is not Context-owned and not in the protected-path table, allow the write unconditionally (engram_guard does not restrict general filesystem writes)."

#### [CE-9] DeferEnvelope.context nullable exclusion not in operations.md

**Files:** operations.md
**Fix:** Add note to §Defer: "The idempotency_key in EnvelopeHeader is computed by the caller at envelope construction time (see types.md §Idempotency). The engine uses the provided key — it does not recompute from fields."

#### [CE-11] /quicksave quality validation cross-reference missing

**Files:** skill-surface.md
**Fix:** Add to /quicksave row: "Checkpoint writes trigger `engram_quality` advisory validation (see enforcement.md §Quality Validation)."

#### [CE-12] orchestrated_by field name collision (frontmatter vs ledger)

**Files:** types.md
**Fix:** Add clarifying note to §Snapshot Orchestration Intent: "The ledger event `snapshot_written` also contains an `orchestrated_by` payload field — this is a distinct field in the LedgerEntry payload, not the snapshot frontmatter field. The frontmatter field is absent for /quicksave; the ledger event payload field contains `'quicksave'`."

#### [CE-13] engram_quality timing contract gap

**Files:** enforcement.md
**Fix:** Add: "For Edit tool calls, the hook reads the final file state from disk at PostToolUse invocation time. Concurrent writes between Edit completion and hook invocation are not detectable — the hook validates whatever is on disk. This is acceptable for advisory warnings."

#### [CE-15] Guard behavior during bridge for unrecognized paths

**Files:** enforcement.md
**Fix:** Add to §Bridge Period Limitations: "During Step 3a, `engram_guard` has `engine_trust_injection` and `work_path_enforcement` active but not `context_direct_write_authorization`. Write/Edit to unrecognized paths (including future Context paths) are allowed through — the guard only blocks Write/Edit to currently-protected paths."

#### [IE-10] Guard path overlap precedence unspecified

**Files:** enforcement.md
**Fix:** Covered by SY-7 decision algorithm (commit 1). Add cross-reference if needed: "See §Guard Decision Algorithm for the evaluation order that resolves overlapping path classifications."

#### [IE-11] engram_register protected-path trigger not connected to table

**Files:** enforcement.md
**Fix:** Add cross-reference to hook table: "`engram_register` fires on the exact paths defined in the [protected-path enforcement table](#protected-path-enforcement) and no others. A change to that table automatically applies to both `engram_guard` and `engram_register`."

#### [IE-12] Staging inbox cap unenforced if guard delayed

**Files:** enforcement.md
**Fix:** N/A after SY-1 resolution (guard confirmed at 2a). Optionally add note: "The staging inbox cap is enforced by the Knowledge engine at entrypoint validation time. With `engram_guard` active from Step 2a, unauthorized callers are rejected before reaching cap enforcement."

#### [SP-3] save_recovery.json version space omission

**Files:** operations.md or types.md
**Fix:** Remove `schema_version` from `save_recovery.json` schema. The file is overwritten on every `/save` and classified as "operational aid" — no cross-version reader tolerance is needed.

#### [SP-12] UTC timestamp write-time enforcement

**Files:** types.md
**Fix:** Add note specifying UTC timestamp enforcement: all timestamp fields are written in ISO 8601 UTC format. Readers encountering non-UTC timestamps should normalize to UTC.

### P2 Findings — Schema Underspecification

#### [SP-8] RecordRef free-form strings (documented deferral)

**Files:** types.md
**Fix:** Add cross-reference to decisions.md §Deferred Decisions confirming this is intentional. Note: "RecordRef string fields (`repo_id`, `record_id`) are validated at construction time in implementation, not at the schema level. See decisions.md."

#### [SP-9] LedgerEntry.payload untyped dict

**Files:** types.md
**Fix:** Add note: "LedgerEntry.payload is an untyped dict (`dict[str, Any]`). The event vocabulary (§Event Vocabulary) defines the expected payload shape for each event_type. Runtime validation is event-type-specific."

#### [SP-10] RecordMeta.schema_version semantics ambiguity

**Files:** types.md
**Fix:** Clarify: "`RecordMeta.schema_version` reflects the version of the subsystem-specific metadata schema (e.g., `lesson-meta.meta_version` for Knowledge). It is NOT the version of RecordMeta itself."

#### [SP-11] Session diagnostic file schema unversioned

**Files:** enforcement.md
**Fix:** Add `schema_version: "1.0"` to the `.diag` JSONL entry format. Add note: "If a reader encounters a `.diag` entry with an unrecognized `schema_version`, it should treat the entry as opaque (log but do not interpret fields)."

#### [AA-7] operations.md re-specifies ledger degradation from storage-and-indexing.md

**Files:** operations.md
**Fix:** Add cross-reference: "The ledger-disabled inference collapse rule is specified authoritatively in storage-and-indexing.md §Degradation Model. This section summarizes it for triage context."

### P2 Findings — Authority/Description Imprecision

#### [AA-5] Bidirectional normative dependency on exception creation

**Files:** enforcement.md
**Fix:** Replace "New exceptions require an entry in both this table and foundations.md" with: "This table lists all exceptions defined in foundations.md §Permitted Exceptions. The canonical source is foundations.md — an exception not present there is not effective, regardless of its presence in this table."

#### [AA-6] README authority description understates data-contract scope

**Files:** README.md
**Fix:** Update `data-contract` concern column to match spec.yaml: "Core types (RecordRef, RecordMeta, envelopes, lesson-meta), storage layout, NativeReader protocol, query API, and degradation model."

### P2 Findings — Unverified Low-Risk Claims

#### [VR-12] Staging filename hash-prefix collision no VR

**Files:** delivery.md
**Fix:** Add VR-0A test: Mock `O_CREAT | O_EXCL` to raise FileExistsError; mock existing file to return different `content_sha256`. Assert: engine writes with `-1` suffix; diagnostic logged; original unchanged.

#### [VR-13] RecordRef construction-time validation no VR

**Files:** delivery.md
**Fix:** Add VR-0A test: `RecordRef(subsystem="invalid")` → assert `ValueError`. Repeat with empty string.

#### [VR-14] worktree_id truncation uniqueness no VR

**Files:** delivery.md
**Fix:** Add VR-0B test: Two known distinct `git_dir` paths → assert `worktree_id` values differ. Assert format: exactly 16 lowercase hex chars.

#### [VR-15] Config live-reload no-caching no VR

**Files:** delivery.md
**Fix:** Add VR-3A test: Run distill with `knowledge_max_stages: 5`; update config to 15 without restart; run second distill — assert new cap applies.

---

## File Edit Summary

| File | Commit 1 | Commit 2 | Commit 3 | Total Edits |
|---|---|---|---|---|
| enforcement.md | SY-1, SY-2, SY-7, SY-4, IE-8, IE-9 | SY-3, SY-5, SY-10, CE-8, IE-3, IE-4, IE-5, IE-6, AA-3 | CE-6, CE-13, CE-15, IE-10, IE-11, IE-12, AA-5, SP-11 | 23 |
| delivery.md | SY-2, SY-6, SY-8, CC-2 | SY-9, SY-10, CE-7 | VR-2, VR-4, VR-5, VR-6, VR-7, VR-8, VR-10, VR-12, VR-13, VR-14, VR-15 | 18 |
| types.md | SY-4 | SY-5, SY-9, CE-5, CE-14, CC-5, SP-1, SP-5, SP-7 | CE-12, SP-8, SP-9, SP-10 | 14 |
| operations.md | — | SY-10, CE-3 | CE-4, CE-9, AA-7, SP-3 | 6 |
| storage-and-indexing.md | — | SP-1 | — | 1 |
| skill-surface.md | CC-3 | — | CE-11 | 2 |
| foundations.md | — | — | CC-6 (if heading change) | 0–1 |
| README.md | — | — | AA-6 | 1 |
| decisions.md | — | — | CC-8, SP-8 | 1–2 |

---

## Dependency Graph

```
SY-1 (guard timing) ──────────> IE-12 (staging cap, P2 — becomes N/A)
SY-2 (capability split) ──────> SY-7 (decision algorithm — uses new names)
                         ──────> SY-6 (VR uses correct capability name)
                         ──────> CE-7 (intra-step ordering uses new names)
SY-4 (TrustPayload type) ─────> SY-5 (authority move — references fixed type)
CC-2 (duplicate VR ID) ───────> all new VR codes (must not collide)
SY-10 (.diag spec) ───────────> IE-2 (.diag dir creation, part of SY-10 fix)
                   ───────────> VR-3/VR-11 (VR codes, part of SY-10 fix)
                   ───────────> CE-18 (operations.md triage read, part of SY-10 fix)
SY-7 (decision algorithm) ────> IE-10 (path overlap, P2 — covered by SY-7)
CE-5 (Branch D) ──────────────> CC-5 (legacy label — use consistent term)
SP-1 (schema_version) ────────> SP-10 (semantics, P2 — clarified by SP-1)
```

## Verification

After each commit:
1. Grep for all finding IDs in the plan to confirm each was addressed
2. Run cross-reference check: all new VR codes have unique IDs
3. Verify boundary rules: changes to data-contract files → review operations + enforcement for consistency
4. Confirm no new contradictions introduced by checking: (a) guard capability table matches delivery.md step descriptions, (b) types.md TypedDict definitions match enforcement.md validation rules, (c) operations.md behavioral claims align with enforcement.md mechanisms
