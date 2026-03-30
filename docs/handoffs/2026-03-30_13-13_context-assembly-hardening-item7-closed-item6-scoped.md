---
date: 2026-03-30
time: "13:13"
created_at: "2026-03-30T17:13:31Z"
session_id: 92535c49-d08a-496b-a8a4-715204ee268c
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-03-30_01-54_t1-t2-live-contract-probe-and-recovery-audit-parity.md
project: claude-code-tool-dev
branch: main
commit: 8509789b
title: "Context assembly hardening: item 7 closed, item 6 scoped with implementation contract"
type: handoff
files:
  - packages/plugins/codex-collaboration/server/context_assembly.py
  - packages/plugins/codex-collaboration/tests/test_context_assembly.py
  - docs/tickets/2026-03-30-context-assembly-redaction-hardening.md
  - docs/tickets/2026-03-27-r1-carry-forward-debt.md
---

# Handoff: Context assembly hardening: item 7 closed, item 6 scoped with implementation contract

## Goal

Complete the post-R2 hardening framework tasks T3 (context-assembly trust gaps) and T4 (freeze next work package) from the prior session's 4-task decision framework.

**Trigger:** Prior session closed T1 (live contract probe) and T2-A (audit parity) with 4 commits on main. The remaining tasks were T3 (assess carry-forward debt items 6 and 7 against shared context assembly paths) and T4 (freeze the next work packet). User chose to continue from the handoff rather than starting fresh.

**Stakes:** Items 6 (redaction coverage) and 7 (non-UTF-8 crash) affect the production consult path and the new dialogue path equally — `context_assembly.py` is shared infrastructure. A binary file reference could crash the entire assembly pipeline (item 7), and common credential forms pass through unredacted into Codex prompts (item 6).

**Success criteria:** Assess both items under a "reasonable user expectation" bar, fix or scope each, and freeze the next work packet with clear boundaries.

**Connection to project arc:** Spec compiled (`bf8e69e3`) → T1 (`f53cd6c8`) → R1 (`3490718a`) → Post-R1 amendments (`2ae76ed1`) → R2 implementation + fixes (PR #89) → R2 squash-merge (`f5fc5aab`) → T1-T2 hardening (prior session) → **T3-T4 context assembly hardening (this session)** → item 6 implementation (next session).

## Session Narrative

### Loaded handoff and reframed the remaining work

Loaded the prior session's handoff (`2026-03-30_01-54_t1-t2-live-contract-probe-and-recovery-audit-parity.md`). The post-R2 framework had four tasks: T1 (hardening bar, done), T2 (recovery debt, done/parked), T3 (context-assembly trust gaps), T4 (freeze next work package). User presented a draft plan that renumbered these as their own T1-T3.

I pushed back on three points: (1) the unknown-handle tracking question (user's T1) wasn't a real task — the handoff already documented the parking rationale more thoroughly than most tickets; (2) the ranking question (user's T2) was broader than needed — the carry-forward ticket already narrowed the gate to exactly items 6 and 7; (3) the push gap (7 commits ahead of origin) was real risk, not something to park.

User accepted all three pushbacks and revised to: push main first, assess items 6 and 7, then freeze the packet.

### Assessed items 6 and 7

User presented three ranked hypotheses before proceeding:
1. Item 7 more likely to merit promotion (binary crash aborts the whole pipeline)
2. Item 6 real but may remain backlog (depends on what secrets appear in practice)
3. Neither promoted if both are narrow

We agreed on promotion bar B: "Would a reasonable user expect this to work safely, and be surprised that it doesn't?" — surprise-based severity, not exploit-based.

User performed the assessment and found both items warranted promotion. Item 7: `_read_file_excerpt()` in `context_assembly.py` reads with `read_text(encoding="utf-8")` with no `UnicodeDecodeError` handling. One binary file in `explicit_paths` or `task_local_paths` aborts the entire packet. Item 6: `_SECRET_PATTERNS` has 4 patterns but misses `AKIA*`, `ghp_`/`gho_`/`ghs_`/`ghr_`, `Authorization: Basic`, and URL-embedded credentials. Internal precedent exists in `redact.py` and `secret_taxonomy.py`.

I confirmed both findings against the code and added that item 7's blast radius was wider than stated — one binary file aborts assembly for ALL files in the request, not just the binary file.

### Implemented and landed item 7

User decided item 7 should be a standalone bugfix, not part of the item 6 packet. User: "The poison-pill behavior is broader than I stated: both `_build_explicit_entries()` and `_build_sorted_file_entries()` funnel through `_read_file_excerpt()`, so one non-UTF-8 file in either `explicit_paths` or `task_local_paths` aborts the whole packet."

Created branch `fix/binary-file-assembly-crash`. First implementation caught `UnicodeDecodeError` and checked for null bytes after decoding. A WASM test case (`b"\x00asm\x01\x00\x00\x00"`) exposed that null bytes are valid UTF-8 — the `UnicodeDecodeError` catch alone wasn't sufficient. User identified the fix: sniff bytes first, then decode.

User reviewed the patch and requested three adjustments: (1) make the binary sniff byte-based and bounded before decoding, (2) add a missing-file regression test to lock the hard-error boundary, (3) pull the placeholder into a module constant. All three applied. 216 tests passing, merged to main, pushed.

### Froze the item 6 packet

Created ticket `T-20260330-01` scoping targeted redaction hardening. Updated the carry-forward ticket `T-20260327-01`: item 7 closed, item 6 promoted, T4 decision gate retired.

User reviewed the ticket artifacts and found three documentary issues (stale line anchors, unretired decision gate, inconsistent state model). Fixed in two follow-up commits. Then found two more (historical classification gap, remaining line-number references). Fixed. Then found one more (both tickets said "both promoted" when item 7 was closed directly). Fixed. Final ticket state is internally consistent.

### Ran adversarial reviews to sharpen the item 6 plan

Three rounds of adversarial review exposed that item 6 is not just a "port patterns" task:

1. **First review:** `_redact_text` needs architectural change for group-preserving patterns (URL userinfo, Basic auth). `github_pat_` has no internal precedent. Pattern ordering is not addressed.

2. **Second review:** T1 (false-positive boundary) needs representative prompt content, not just example names. Minimum suffix length is a first-class deliverable, not a tuning parameter. `github_pat_` is misframed — needs external research, not internal validation.

3. **Third review:** The plan collapsed from 4 tasks to 3: T1 (false-positive evidence base), T2 (github_pat_ resolution), T3 (confirm boundary and implementation contract).

### Resolved the two research unknowns

**T2 (github_pat_):** Web search confirmed GitHub Docs document the prefix but NOT the token grammar (length, suffix structure). Community-observed regex (`github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}`) comes from a gist, not official docs. User: "The packet is supposed to be the low-ambiguity hardening pass, and the official evidence only gets us to `github_pat_` as a prefix, not to the full regex." Dropped from scope.

**T1 (false-positive evidence base):** Derived from code structure rather than live assemblies. `assemble_context_packet` shows three content categories: file excerpts (high false-positive risk), explicit snippets (medium), text entries like objectives/constraints/summaries (low). Thresholds derived from internal precedent: `secret_taxonomy.py` uses `AKIA[A-Z0-9]{16}` with word boundaries and `(?:ghp|gho|ghs|ghr)_[A-Za-z0-9]{36,}` with word boundaries — stricter than `redact.py`'s generic `{10,}`.

### Locked the implementation contract

Final adversarial review confirmed the remaining risk is not pattern selection but `_redact_text` architecture: ordering, replacement format, and overlap handling. Defined a bounded local contract: most-specific-first ordering, capture-aware replacement for URL userinfo and Basic auth only, flat `[redacted]` for prefix patterns, taxonomy-derived thresholds. Updated `T-20260330-01` with the full contract.

## Decisions

### Promote both items 6 and 7 from carry-forward debt

**Choice:** Both items assessed and promoted under surprise-based severity bar.

**Driver:** User framed the bar as: "Would a reasonable user expect this to work safely, and be surprised that it doesn't?" A user referencing a `.png` expects graceful handling, not a crash. A user with `AKIA*` keys near referenced code expects redaction to catch them.

**Rejected:**
- **Promote neither** — both gaps exist in the shared production path. The absence of test failures is not evidence of handling: "the current green test suite understates both risks" (user's assessment).
- **Promote item 6 only** — item 7 is a deterministic crash for a foreseeable user action (referencing a binary file).

**Trade-offs accepted:** Two work items instead of one. Mitigated by treating item 7 as an immediate standalone fix and item 6 as a scoped packet.

**Confidence:** High (E2) — both findings confirmed against live code with targeted probes.

**Reversibility:** High — both are additive changes (new patterns, new error handling).

**Change trigger:** None — these correct gaps, not preferences.

### Land item 7 as standalone bugfix, not inside the item 6 packet

**Choice:** Fix the binary-file crash immediately rather than bundling it with redaction hardening.

**Driver:** User: "I would still keep fail-fast semantics for missing or out-of-repo paths, but degrade gracefully only for decode/binary cases. So the right shape is: hard errors stay hard, binary unreadability becomes per-file omission with a clear placeholder."

**Rejected:**
- **Bundle with item 6** — delays a 3-line fix behind pattern-expansion planning. User: "no reason to hold it behind item 6."

**Trade-offs accepted:** Two separate commits/merges instead of one bundled packet. Negligible overhead.

**Confidence:** High (E2) — 216 tests passing, fix is isolated to `_read_file_excerpt`.

**Reversibility:** High — additive change.

**Change trigger:** None.

### Sniff bytes before decoding, not null-check after decode

**Choice:** Read first 8192 bytes and check for `\x00` before attempting `read_text(encoding="utf-8")`.

**Driver:** WASM test case exposed that null bytes (`\x00`) are valid UTF-8 — `read_text` succeeds but produces garbage. Checking after decode means you've already read the entire file. Byte-prefix sniff is cheaper and catches both classes: invalid UTF-8 (caught by exception) and valid-UTF-8-but-binary (caught by null byte check).

**Rejected:**
- **UnicodeDecodeError only** — misses WASM and other null-byte-heavy formats that decode without error.
- **Null-check after full decode** — works but reads and decodes the entire file first. Byte sniff avoids the decode entirely for binary files.

**Trade-offs accepted:** Two I/O operations for binary files (read bytes prefix, then fail fast) vs. one (read text, then check). For text files, the byte sniff is a cheap prefix read that passes through.

**Confidence:** High (E2) — both detection paths tested with representative binary formats (PNG, WASM, mixed valid+binary).

**Reversibility:** High.

**Change trigger:** None — this corrects a detection gap.

### Drop `github_pat_` from T-20260330-01 scope

**Choice:** Remove `github_pat_` from the redaction hardening packet. Defer until GitHub publishes an authoritative format spec.

**Driver:** User: "The packet is supposed to be the low-ambiguity hardening pass, and the official evidence only gets us to `github_pat_` as a prefix, not to the full regex." GitHub Docs confirm the prefix exists but do not publish the token grammar. Community-observed regex (`github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}`) is from a gist, not official documentation.

**Rejected:**
- **Keep with community regex** — violates the packet's evidence bar. The regex may be correct but is not authoritative.
- **Keep with prefix-only pattern** — guessing at suffix structure contradicts the low-ambiguity design constraint.

**Trade-offs accepted:** Fine-grained PATs (`github_pat_`) pass through unredacted. Lower risk than other leaked forms because the 11-character prefix is very distinctive and the full token is 93 characters — unlikely to appear in code as a non-secret.

**Confidence:** High (E2) — evidence bar grounded in GitHub's official docs vs. community gist distinction. User verified the claim independently.

**Reversibility:** High — adding the pattern later is non-breaking.

**Change trigger:** GitHub publishes official token format documentation, or the community regex is validated against a larger sample.

### Prefer taxonomy thresholds over redact.py thresholds

**Choice:** Use `secret_taxonomy.py` per-family thresholds (`AKIA[A-Z0-9]{16}` with `\b`, `gh*_{36,}` with `\b`) instead of `redact.py` generic threshold (`{10,}`).

**Driver:** `redact.py` is tuned for excerpt safety where over-redaction is acceptable (comment above `_JWT_RE`: "ingress over-matching is acceptable for redaction"). `context_assembly.py` feeds the full Codex prompt where over-redaction loses meaningful content. The taxonomy's per-family thresholds reflect actual token structures; the generic `{10,}` is deliberately loose.

**Rejected:**
- **Use `redact.py` thresholds** — `{10,}` would match `ghp_enabled` (11 chars after prefix) as a secret. Real GitHub tokens are 36+ chars.
- **Define new thresholds** — unnecessary when the taxonomy already encodes the right gates.

**Trade-offs accepted:** Tighter gates mean shorter credential fragments (e.g., a truncated `ghp_` token with only 8 suffix chars) pass through unredacted. Acceptable because: (1) truncated tokens are less exploitable, (2) the alternative (false-positiving on variable names) is worse in this path.

**Confidence:** High (E2) — verified both threshold sets against the code. Taxonomy's `AKIA[A-Z0-9]{16}` matches AWS's documented 20-character key format exactly (4-char prefix + 16-char identifier).

**Reversibility:** High — changing thresholds is a regex edit.

**Change trigger:** Discovery of real tokens that are shorter than the taxonomy minimums.

### Use most-specific-first pattern ordering with capture-aware replacement

**Choice:** Refactor `_redact_text` to apply patterns most-specific-first and use per-pattern replacement callables for URL userinfo and Basic auth.

**Driver:** Adversarial review identified two risks in the current flat `pattern.sub("[redacted]", ...)` loop: (1) URL userinfo pattern uses capture groups but flat replacement destroys URL structure (`[redacted]` instead of `://user:[redacted]@host`), (2) adding prefix patterns alongside the existing keyword pattern creates double-match risk.

**Rejected:**
- **Keep flat replacement for all patterns** — destroys URL structure and header formatting, degrading Codex's ability to reason about the code.
- **Full `redact.py`-scale staging** — introduces stats, suppression, and two-stage orchestration. Overkill for this scope.

**Trade-offs accepted:** `_redact_text` grows from 4 lines to ~15-20 lines. Two patterns (URL userinfo, Basic auth) need replacement callables; the rest use flat `[redacted]`. Ordering discipline adds a maintenance obligation.

**Confidence:** High (E2) — `redact.py` demonstrates the pattern and its capture-group callbacks. The local adaptation is bounded.

**Reversibility:** High — the function is self-contained.

**Change trigger:** If a third pattern needs group-preserving replacement, consider extracting a shared replacement dispatcher.

## Changes

### `packages/plugins/codex-collaboration/server/context_assembly.py` — Binary file hardening

**Purpose:** Prevent a single binary or non-UTF-8 file reference from crashing the entire context assembly pipeline.

**Changes:**
- Added `_BINARY_SNIFF_BYTES = 8192` and `_BINARY_PLACEHOLDER` constants at lines 40-41
- `_read_file_excerpt()` at lines 347-353: reads first 8192 bytes and checks for null before attempting `read_text(encoding="utf-8")`. Catches `UnicodeDecodeError` as fallback. Returns `_BINARY_PLACEHOLDER` for both cases.
- Hard errors (out-of-repo path at line 337, missing file at line 342) remain unchanged as `ContextAssemblyError`.

**Key detail:** The byte-prefix sniff avoids decoding obviously binary files at all. The 8192-byte window matches `git`'s own binary detection heuristic. The placeholder `"[binary or non-UTF-8 file — content not shown]"` is not redacted (no user content to leak).

### `packages/plugins/codex-collaboration/tests/test_context_assembly.py` — Binary file and boundary tests

**Purpose:** Cover binary file handling in both path types and lock the hard-error boundary.

**Changes:**
- `test_assembly_handles_binary_file_in_explicit_paths`: PNG magic bytes (`\x89PNG...`) — triggers `UnicodeDecodeError` path
- `test_assembly_preserves_valid_files_alongside_binary`: mixed valid + binary in `explicit_paths` — proves one binary file doesn't poison valid files (the "poison pill" regression)
- `test_assembly_handles_binary_file_in_task_local_paths`: WASM magic bytes (`\x00asm...`) — triggers null-byte sniff path (valid UTF-8 but binary)
- `test_assembly_rejects_missing_file`: asserts `ContextAssemblyError("file reference missing")` — locks the "missing stays hard" boundary

### `docs/tickets/2026-03-30-context-assembly-redaction-hardening.md` — Freeze artifact

**Purpose:** Define the item 6 work packet with explicit scope, implementation contract, and acceptance criteria.

**Key sections:**
- **Scope:** `AKIA*`, `ghp_`, `gho_`, `ghs_`, `ghr_`, Basic auth headers, URL userinfo. `github_pat_` explicitly excluded.
- **Implementation contract:** Taxonomy-derived thresholds, group-preserving replacement for URL userinfo and Basic auth, flat `[redacted]` for prefix patterns, most-specific-first ordering, explicit overlap test.
- **Acceptance criteria:** 11 checkboxes covering positive matches, false-positive boundaries, replacement format, overlap behavior, and regression preservation.

### `docs/tickets/2026-03-27-r1-carry-forward-debt.md` — Parent ticket updates

**Purpose:** Reflect T3/T4 resolution: item 7 closed, item 6 promoted, T4 gate retired.

**Changes:**
- Items 6 and 7 classifications updated to `Promoted` and `Closed` with references
- Classification key updated with `Existing gap (historical)`, `Promoted`, and `Closed` states
- T4 decision gate marked resolved 2026-03-30 with outcome summary
- All acceptance criteria checked
- Resolution log added
- Stale line-number anchors replaced with symbol-based references

## Codebase Knowledge

### Key Code Locations (Verified This Session)

| What | Location | Why verified |
|------|----------|-------------|
| `_read_file_excerpt()` | `context_assembly.py:333-358` | Fixed: byte-prefix sniff + UnicodeDecodeError catch |
| `_BINARY_SNIFF_BYTES` | `context_assembly.py:40` | New: 8192-byte sniff window |
| `_BINARY_PLACEHOLDER` | `context_assembly.py:41` | New: shared placeholder constant |
| `_SECRET_PATTERNS` | `context_assembly.py:42-47` | Starting point for item 6 (4 patterns) |
| `_redact_text()` | `context_assembly.py:360-364` | Current: flat `pattern.sub("[redacted]", ...)` loop. Needs refactor for item 6. |
| `assemble_context_packet()` | `context_assembly.py:61-176` | Maps all `_redact_text` input categories |
| `_build_explicit_entries()` | `context_assembly.py:296-306` | Calls `_read_file_excerpt` per path in `explicit_paths` |
| `_build_sorted_file_entries()` | `context_assembly.py:309-323` | Calls `_read_file_excerpt` per path in `task_local_paths` |
| `_build_text_entries()` | `context_assembly.py:326-330` | Calls `_redact_text` on text values (summaries, constraints) |

### Internal Precedent for Item 6

| Symbol | Location | Threshold | Notes |
|--------|----------|-----------|-------|
| `_API_KEY_PREFIX_RE` | `redact.py:101-103` | `{10,}` generic | Too loose for prompt path — would match `ghp_enabled` |
| `_BASIC_AUTH_RE` | `redact.py:97-98` | `{8,}` base64 | Good pattern but needs explicit header form restriction |
| `_URL_USERINFO_RE` | `redact.py:106-107` | Structural | Group-preserving: `(://[^@/\s:]+:)([^@/\s]+)(@)` |
| `_CREDENTIAL_RE` | `redact.py:110-116` | `{6,}` RHS | 14 keywords — too broad for this scope |
| `aws_access_key_id` | `secret_taxonomy.py:72` | `AKIA[A-Z0-9]{16}` with `\b` | Exact length, word-bounded — preferred threshold |
| `github_pat` (family) | `secret_taxonomy.py:114` | `(?:ghp\|gho\|ghs\|ghr)_[A-Za-z0-9]{36,}` with `\b` | 36+ suffix — preferred threshold |

### Architecture: _redact_text Input Categories

Content flows through `_redact_text` from three sources with different false-positive risk:

| Category | Source | False-positive risk | Why |
|----------|--------|-------------------|-----|
| File excerpts | `_read_file_excerpt` → `_redact_text` | **High** | Source code with variable names, test fixtures, SDK constants |
| Explicit snippets | Inline `_redact_text` at line 90 | Medium | User-provided, unpredictable |
| Text entries | `_build_text_entries` → `_redact_text` | Low | Natural language (objectives, constraints, summaries) |

### Error Handling Hierarchy in _read_file_excerpt

| Check | Behavior | Rationale |
|-------|----------|-----------|
| Path escapes repo root | `ContextAssemblyError` (hard) | Caller bug |
| File missing | `ContextAssemblyError` (hard) | Caller bug |
| Null bytes in first 8KB | `_BINARY_PLACEHOLDER` (graceful) | Binary file — foreseeable user input |
| Invalid UTF-8 | `_BINARY_PLACEHOLDER` (graceful) | Non-text file — foreseeable user input |

## Context

### Mental Model

This session's core problem was "what's the smallest honest path from assessment to implementation readiness for context assembly hardening?" The answer turned out to have three layers:

1. **Assessment layer:** Both items clear the "reasonable user expectation" bar. Item 7 is a deterministic crash. Item 6 is a confidentiality gap in a shared path.

2. **Delivery layer:** Item 7 can ship immediately because it's a scoped bugfix. Item 6 needs a packet because it involves pattern selection, threshold decisions, and architectural adjustment to `_redact_text`.

3. **Contract layer:** Item 6 is not a "port patterns" task. It requires defining a local redaction-behavior contract (ordering, replacement format, overlap handling) before implementation. Three rounds of adversarial review surfaced this.

### Project State

| Milestone | Status | Commit/PR |
|-----------|--------|-----------|
| Spec compiled and merged | Complete | `bf8e69e3` |
| T1: Compatibility baseline | Complete | `f53cd6c8` (PR #87) |
| R1: First runtime milestone | Complete | `3490718a` on main |
| Post-R1 spec amendments | Complete | `078e5a39`..`2ae76ed1` on main |
| R2: Dialogue foundation | Complete | `f5fc5aab` on main (PR #89, squash-merged) |
| T1-T2: Live contract probe + audit parity | Complete | `d65c8d54`..`b0f45f95` |
| **Item 7: Binary file hardening** | **Complete** | `e6792de8` |
| **Item 6: Redaction hardening (scoped)** | **Ready for implementation** | Ticket `T-20260330-01` at `8509789b` |
| T3: Context-assembly trust gaps | **Complete** | Both items assessed and dispositioned |
| T4: Freeze next work package | **Complete** | `T-20260330-01` frozen with implementation contract |

216 tests passing on main. Feature branch `feature/codex-collaboration-r2-dialogue` still exists (tagged at `r2-dialogue-branch-tip` → `d2d0df56`).

## Learnings

### Not all binary files contain invalid UTF-8

**Mechanism:** Some binary formats (WASM: `\x00asm\x01\x00\x00\x00`) consist entirely of null bytes and ASCII characters that are valid UTF-8. `read_text(encoding="utf-8")` succeeds but produces garbage strings with control characters.

**Evidence:** WASM test case in `test_assembly_handles_binary_file_in_task_local_paths` — `read_text` produced `\u0000asm\u0001\u0000\u0000\u0000` without error.

**Implication:** Binary detection requires a null-byte check in addition to `UnicodeDecodeError` catching. The byte-prefix sniff approach (check raw bytes for `\x00` before decoding) is both cheaper and more correct.

### Symbol-based references resist drift better than line numbers in tickets

**Mechanism:** Line numbers shift with every code edit. The item 7 fix added 2 constants that bumped `_SECRET_PATTERNS` from line 40 to 42.

**Evidence:** The freeze ticket's references were stale within minutes of item 7 landing.

**Implication:** Tickets that serve as session re-entry points should use symbol names (`_SECRET_PATTERNS`, `_read_file_excerpt()`) rather than line numbers. Symbols survive code changes as long as the symbol isn't renamed, which is much rarer than line shifts.

### Taxonomy thresholds are safer than generic redaction thresholds for prompt-path redaction

**Mechanism:** `redact.py` uses `{10,}` as a single minimum across all prefix families because it's an ingress redactor where false positives are harmless. `secret_taxonomy.py` encodes per-family minimums that reflect actual token structures: AWS keys are exactly `AKIA` + 16 uppercase chars, GitHub tokens are prefix + 36 alphanumeric chars.

**Evidence:** `redact.py:101-103` uses `[A-Za-z0-9_\-]{10,}`. `secret_taxonomy.py:72` uses `AKIA[A-Z0-9]{16}` with `\b`. `secret_taxonomy.py:114` uses `[A-Za-z0-9]{36,}` with `\b`.

**Implication:** In paths where false positives have real cost (prompt assembly), prefer per-family thresholds from the taxonomy. The `{10,}` gate would match `ghp_enabled` (11 chars) as a secret.

### Official documentation vs community observation is a real evidence-level distinction

**Mechanism:** GitHub Docs confirm `github_pat_` prefix exists. The full token grammar (93 chars, `{22}_...{59}` structure) comes from a community gist, not official documentation.

**Evidence:** Web search of `docs.github.com` and `github.blog` — no official format spec found. Gist at `gist.github.com/magnetikonline/073afe7909ffdd6f10ef06a00bc3bc88` provides the regex.

**Implication:** For a packet whose design constraint is "low-ambiguity families with authoritative basis," community-observed formats don't meet the bar. This distinction matters more in paths where false positives are costly.

## Next Steps

### Implement the item 6 redaction hardening packet

**Dependencies:** None — implementation contract is locked in `T-20260330-01`.

**What to read first:** `T-20260330-01` at `docs/tickets/2026-03-30-context-assembly-redaction-hardening.md` — has the full implementation contract including pattern thresholds, replacement format, application order, and overlap behavior.

**Approach:**
1. Refactor `_redact_text` from flat `pattern.sub` loop to ordered application with per-pattern replacement callables
2. Add taxonomy-derived patterns (AKIA, ghp/gho/ghs/ghr) with word boundaries
3. Add Basic auth header pattern with group-preserving replacement
4. Add URL userinfo pattern with group-preserving replacement
5. Write positive tests, false-positive regression tests, and overlap tests
6. Close item 6 in `T-20260327-01`

**Potential obstacles:** The `_redact_text` refactor is the only non-trivial step. The function is currently 4 lines. It needs to become ~15-20 lines with ordered application and two replacement callables. Keep it local — do not introduce `redact.py`-scale staging.

**Acceptance criteria:** 11 checkboxes in `T-20260330-01`.

### Re-baseline the parent debt ticket

**Dependencies:** Item 6 implementation must land first.

**What to read first:** `T-20260327-01` at `docs/tickets/2026-03-27-r1-carry-forward-debt.md`.

**Approach:** Mark item 6 as closed with commit reference. Verify remaining parked items (1-5) are the only open debt.

### Optional: feature branch cleanup

`feature/codex-collaboration-r2-dialogue` still exists on remote. Tagged at `r2-dialogue-branch-tip` → `d2d0df56`. Can be deleted anytime.

## In Progress

Clean stopping point. Item 7 landed and pushed. Item 6 ticket frozen with implementation contract. No work in flight.

**User's next step:** Implement item 6 using the contract in `T-20260330-01`.

## Open Questions

### Replacement format for existing keyword pattern after overlap

When `api_key = AKIAIOSFODNN7EXAMPLE` is processed, the AKIA pattern matches first (most-specific-first ordering). The keyword pattern then sees `api_key = [redacted]`. The `[redacted]` replacement is 10 characters, which is longer than the keyword pattern's `{6,}` minimum. However, `[redacted]` contains brackets which aren't in the `[^\s"']{6,}` character class, so it won't re-match. This should be verified with an explicit overlap test during implementation.

### MCP consumer retry behavior for CommittedTurnParseError (inherited)

The error message says "Blind retry will create a duplicate follow-up turn." But Claude (the MCP consumer) has no programmatic mechanism to distinguish this error from a generic tool failure. Wire-level retry prevention is out of scope.

### Chronically unreachable unknown handles (parked as T2 Item B)

Startup recovery retries `unknown` handles every restart. Explicitly parked — needs TTL design and usage pattern data. Spec acknowledges at `contracts.md:156`.

### Feature branch cleanup timing

`feature/codex-collaboration-r2-dialogue` exists on remote with tag `r2-dialogue-branch-tip`. Can be deleted anytime. No urgency.

## Risks

### _redact_text refactor could expand scope

The implementation contract specifies a bounded local refactor (~15-20 lines). If the refactor reveals additional complexity (e.g., patterns that need replacement functions beyond URL userinfo and Basic auth), scope could expand. The decision gate in the plan addresses this: "if the agreed contract still fits as a local `context_assembly.py` hardening change, proceed; otherwise re-scope."

### Three independent copies of credential-detection logic

After item 6 lands, `context_assembly.py`, `redact.py`, and `secret_taxonomy.py` will have partially overlapping pattern sets with different thresholds. This is acknowledged duplication, not a bug. The risk is future maintainers updating one and not the others. Parked as explicit debt in the ticket.

### Truncated tokens below threshold minimums pass through

Choosing `{36,}` for GitHub tokens means a truncated token like `ghp_abcdefgh` (8 chars) is not redacted. This is a deliberate trade-off: truncated tokens are less exploitable than the false-positive alternative of redacting variable names.

## References

| Resource | Location | Purpose |
|----------|----------|---------|
| Prior handoff (resumed from) | `docs/handoffs/archive/2026-03-30_01-54_t1-t2-live-contract-probe-and-recovery-audit-parity.md` | T1-T2 context and post-R2 framework |
| Item 6 freeze ticket | `docs/tickets/2026-03-30-context-assembly-redaction-hardening.md` | Implementation contract and acceptance criteria |
| R1 carry-forward ticket | `docs/tickets/2026-03-27-r1-carry-forward-debt.md` | Parent tracking artifact (T4 gate resolved) |
| Item 7 fix | `e6792de8` | Binary file hardening |
| `_SECRET_PATTERNS` | `context_assembly.py:42-47` | Current 4-pattern set (starting point for item 6) |
| `_read_file_excerpt()` | `context_assembly.py:333-358` | Fixed function with binary detection |
| `_redact_text()` | `context_assembly.py:360-364` | Current flat loop (refactor target for item 6) |
| Taxonomy thresholds | `secret_taxonomy.py:72,114` | Per-family minimums for AKIA and GitHub tokens |
| `redact.py` precedent | `context-injection/redact.py:94-116` | Group-preserving patterns to adapt |
| GitHub token format blog | `github.blog/2021-04-05-behind-githubs-new-authentication-token-formats/` | Official prefix documentation |
| Token validation gist | `gist.github.com/magnetikonline/073afe7909ffdd6f10ef06a00bc3bc88` | Community regex (non-authoritative) |

## Gotchas

### _redact_text is not just "add patterns to the tuple"

The current `_redact_text` is a flat 4-line `pattern.sub("[redacted]", ...)` loop. Adding URL userinfo and Basic auth requires capture-group-aware replacement. Adding prefix patterns alongside the existing keyword pattern requires ordering discipline. The implementation contract in `T-20260330-01` specifies the exact approach.

### Existing keyword pattern has a character class that prevents re-matching [redacted]

The existing `_CREDENTIAL_RE` pattern uses `[^\s"']{6,}` for the value portion. The `[redacted]` replacement contains brackets (`[` and `]`) which are not in this character class, so the keyword pattern won't re-match a previously redacted value. This should still be verified with an explicit overlap test.

### Binary file sniff is byte-level, not string-level

`_read_file_excerpt` reads raw bytes (`read_bytes()[:_BINARY_SNIFF_BYTES]`) and checks for `b"\x00"`, not `"\x00"` in a decoded string. This is intentional: it avoids decoding obviously binary files at all. The 8192-byte sniff window is larger than `_MAX_FILE_EXCERPT_BYTES` (4096), so any null byte in the excerpt range will be caught.

### Word boundaries (\b) matter for prefix patterns in the prompt path

The taxonomy uses `\b` anchors that prevent matching inside longer identifiers. Without `\b`, `AKIA` would match inside `MAKIAVELLIANISM`. `redact.py` doesn't use `\b` because it accepts over-matching. For `context_assembly.py`, word boundaries are essential.

## Conversation Highlights

**Pushback on the unknown-handle tracking question:**
User (after my pushback): "You're right that my old `T1` was not a real task. The unknown-handle question is already decided at the right level. The remaining work is just to make sure the freeze artifact explicitly acknowledges that parked debt."

**Promotion bar discussion:**
User: "Promote if it is any meaningful cross-capability trust gap." I added: the bar should mean "would a reasonable user expect this to work safely, and be surprised that it doesn't?" — surprise-based severity, not exploit-based.

**Item 7 as standalone fix:**
User: "I would still keep fail-fast semantics for missing or out-of-repo paths, but degrade gracefully only for decode/binary cases."

**Evidence bar for github_pat_:**
User: "The packet is supposed to be the low-ambiguity hardening pass, and the official evidence only gets us to `github_pat_` as a prefix, not to the full regex."

**Threshold selection:**
User: "The recommended family-level gates from internal precedent are... the safest local rule is to prefer the stricter `secret_taxonomy.py` thresholds over the broader `redact.py` ingress thresholds."

**Adversarial review as a planning tool:**
User ran three rounds of adversarial review via `/adversarial-review` to progressively sharpen the item 6 plan. Each round collapsed unnecessary planning structure and surfaced real unknowns. The final plan went from 4 tasks to 3 (research phase + synthesis gate) by the third round.

## User Preferences

**Evidence-level rigor:** User holds community-observed data to a different standard than official documentation. Applies this distinction to implementation decisions, not just academic correctness. User: "That regex may be correct in practice, but in the material you cited, it comes from the gist, not from GitHub's official docs/blog. For this project, that distinction matters."

**Iterative adversarial review:** User uses `/adversarial-review` as a structural planning tool — not just for final validation but for progressive sharpening. Each round is expected to produce actionable findings that reshape the plan. Three rounds before implementation was the right depth for this scope.

**Production-first ordering (continued from prior session):** Fix production code before updating fakes/tests. Land crash fixes immediately. Don't hold simple fixes behind complex packets.

**Hypothesis-driven exploration (continued):** Present ranked hypotheses with evidence needed and tests to run. Wait for confirmation before proceeding.

**Commit scope discipline (continued):** Each commit is independently justified. Don't bundle unrelated fixes. User: "no reason to hold it behind item 6."

**Grounded pushback (continued):** Push back with file:line references and specific reasoning. User: "Tell me where you would push back."

**Debt classification (continued):** Distinguish correctness debt (fix now) from policy debt (park explicitly with documented rationale).
