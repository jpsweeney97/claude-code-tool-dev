---
date: 2026-03-30
time: "14:59"
created_at: "2026-03-30T18:59:20Z"
session_id: b204de02-e095-46e0-baee-fe92672ad8c3
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-03-30_13-13_context-assembly-hardening-item7-closed-item6-scoped.md
project: claude-code-tool-dev
branch: main
commit: dbc91d8f
title: "Item 6 landed, release posture accepted, supersession roadmap frozen"
type: handoff
files:
  - packages/plugins/codex-collaboration/server/context_assembly.py
  - packages/plugins/codex-collaboration/tests/test_context_assembly.py
  - packages/plugins/codex-collaboration/server/control_plane.py
  - packages/plugins/codex-collaboration/server/dialogue.py
  - packages/plugins/codex-collaboration/server/jsonrpc_client.py
  - packages/plugins/codex-collaboration/server/mcp_server.py
  - docs/tickets/2026-03-27-r1-carry-forward-debt.md
  - docs/tickets/2026-03-30-context-assembly-redaction-hardening.md
  - docs/superpowers/specs/codex-collaboration/decisions.md
  - docs/superpowers/specs/codex-collaboration/delivery.md
  - docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md
  - docs/tickets/2026-03-30-codex-collaboration-plugin-shell-and-consult-parity.md
  - docs/tickets/2026-03-30-codex-collaboration-safety-substrate-and-benchmark-contract.md
  - docs/tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md
  - docs/tickets/2026-03-30-codex-collaboration-execution-domain-foundation.md
  - docs/tickets/2026-03-30-codex-collaboration-promotion-flow-and-delegate-ux.md
  - docs/tickets/2026-03-30-codex-collaboration-analytics-reviewer-and-cutover.md
---

# Handoff: Item 6 landed, release posture accepted, supersession roadmap frozen

## Goal

Continue the post-R2 hardening arc by implementing item 6 (redaction coverage), closing the R1/R2 debt posture, and defining the complete supersession roadmap from current state to full cross-model replacement.

**Trigger:** Prior session closed T1-T4 of the post-R2 hardening framework: item 7 fixed (binary file crash at `e6792de8`), item 6 scoped with implementation contract in `T-20260330-01`, items 1-5 still parked. User wanted to implement item 6, review it adversarially, and determine the next strategic direction.

**Stakes:** Item 6 (redaction coverage) affects the shared context assembly path used by both consultation and dialogue. Common credential forms (AKIA keys, GitHub tokens, Basic auth headers, URL-embedded credentials) were passing through unredacted into Codex prompts. Beyond that, the broader question of what comes after R2 hardening needed resolution before further implementation work could begin.

**Success criteria:** Item 6 implemented and closed per the `T-20260330-01` contract; remaining R1/R2 debt (items 1-5) explicitly accepted or rejected for the current rollout target; full supersession roadmap from current state to cross-model replacement defined with executable tickets.

**Connection to project arc:** Spec compiled (`bf8e69e3`) -> T1 (`f53cd6c8`) -> R1 (`3490718a`) -> Post-R1 amendments (`2ae76ed1`) -> R2 (PR #89, `f5fc5aab`) -> T1-T2 hardening -> T3-T4 context assembly hardening (prior session) -> **Item 6 implementation + release posture + supersession roadmap (this session)** -> Plugin shell and consult parity (next session, `T-20260330-02`).

## Session Narrative

### Loaded prior handoff and reviewed item 6 implementation

Loaded the handoff from the prior session (`2026-03-30_13-13_context-assembly-hardening-item7-closed-item6-scoped.md`). The user had already implemented item 6 between sessions: `_redact_text()` refactored from a flat `pattern.sub("[redacted]", ...)` loop to ordered application with per-pattern replacement callables, taxonomy-derived patterns (AKIA, ghp/gho/ghs/ghr) added with word boundaries, Basic auth and URL userinfo with group-preserving replacement, and keyword assignments preserving the label (`api_key = [redacted]` instead of losing the key name).

Conducted an adversarial implementation review against the `T-20260330-01` contract. Verified all 11 acceptance criteria met. Verified pattern ordering matches contract exactly (8 rules, most-specific-first). Verified taxonomy thresholds match `secret_taxonomy.py` exactly for AKIA (`\bAKIA[A-Z0-9]{16}\b`) and GitHub tokens (`\b(?:ghp|gho|ghs|ghr)_[A-Za-z0-9]{36,}\b`). Verified URL userinfo matches `redact.py:106-107` exactly.

Found three findings:
1. Basic auth regex deviated from contract: implementation had `[A-Za-z0-9+/=]{8,}` (equals inside character class) vs contract's `[A-Za-z0-9+/]{8,}=*` (equals as trailing padding). Minor — no practical impact.
2. Keyword pattern value class intentionally tightened from `[^'\"\n]{6,}` to `[^\s\"']{6,}` — necessary for label-preserving behavior.
3. Off-by-one AKIA boundary test missing — `{16}` exact-length constraint not tested at boundaries.

User addressed findings 1 and 3: aligned Basic auth regex to match contract exactly, added `test_assembly_does_not_redact_off_by_one_akia_lengths` with both the 15-char (too short) and 17-char (too long, blocked by `\b` word boundary) cases.

### Committed, merged, and pushed the redaction hardening

Created branch `fix/context-assembly-redaction-hardening`, committed at `1f3305a8` (4 files, 176 insertions, 25 deletions), ran tests (220 passed), merged to main via fast-forward, deleted branch, pushed. Test count in `T-20260330-01` resolution section updated from 219 to 220 at `802863ab`.

### Defined the release posture for items 1-5

The post-item-6 state raised a strategic question: what comes next? User presented a sequenced triage plan (T1-T4 for choosing the next capability lane). I pushed back that T1 as written was a "ceremony without a trigger" — a decision to keep all remaining debt parked while pretending that decision was an active workflow. The real activation mechanism should be code-local annotations at the sites where capability changes would invalidate the park rationale.

User agreed but refined: annotations are the right activation mechanism, but they don't replace the need for one explicit product decision (what counts as "internal rollout") and one central release artifact (what was accepted for this release). We converged on a two-output model: a release posture table in the carry-forward ticket plus targeted invalidation annotations at real chokepoints.

I identified that 3 of the 5 originally proposed annotation sites were wrong — they were at implementation sites rather than caller chokepoints. Item 3 (concurrent safety) should be at `mcp_server.py` dispatch entry, not `control_plane.py`. Item 4 (audit schema) should be at the audit emission sites in `control_plane.py` and `dialogue.py`, not just `models.py`. Item 5 (policy fingerprint) needed annotations at both the admission gate and the fingerprint function. User verified each site against the code and agreed.

Resolved the rollout target as "dev-repo internal use" — matches the implemented R1/R2 slice, keeps packaging out of the critical path. Committed the release posture table and 7 invalidation annotations at `2994b138`.

### Mapped the full supersession roadmap

User's stated goal: "complete building the codex-collaboration system/plugin in full" to completely supersede the cross-model plugin. Launched two parallel exploration agents to map (1) everything cross-model provides and (2) the gap between the codex-collaboration spec and its current implementation.

Key finding: cross-model is a 3-layer stack (MCP transport -> safety/scouting middleware -> user surface). Codex-collaboration has rebuilt the transport layer (direct JSON-RPC, architecturally better than the CLI shim) but hasn't built the middleware or user surface yet. The context-injection subsystem (~1000 tests, ~15 modules) may not need porting because codex-collaboration's architecture allows Claude-side agents to scout using standard tools and pass results via the MCP tool parameters.

User refined my initial milestone sequence with several corrections: split Phase 2 into 2a (plugin shell) and 2b (safety substrate); split delegation into foundation (infrastructure) and promotion (product UX); defined a concrete benchmark contract for the context-injection retirement decision rather than relying on judgment calls; and identified that Phases 3 (dialogue) and 4 (execution domain) can run in parallel after 2b.

### Froze the benchmark contract and ticket chain

User wrote the dialogue supersession benchmark contract at `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md` with: fixed 8-task corpus, run conditions (same commit, same model, no manual hints), required artifacts (manifest, runs, adjudication, summary), adjudication rules (supported/unsupported/false claim labels), 4-gate pass rule (zero safety violations, false claims <= baseline, supported claim rate within 10%, convergence within 1 session), and change control.

User also wrote 6 execution tickets (T-20260330-02 through T-20260330-07) covering the full supersession path. Anchored the supersession direction in `decisions.md`, added the post-R2 packet sequence to `delivery.md`, and updated the spec reading order.

I reviewed and flagged two notes: (1) all 8 benchmark corpus tasks are about the codex-collaboration repo itself — fair for comparison but doesn't test unfamiliar-repo performance, and (2) T-03's framing said "add the benchmark contract" when the file already existed. User incorporated both: added a known-limitations section to the benchmark contract and fixed T-03's framing to reference the contract as an existing governed artifact.

Committed at `dbc91d8f` (10 files, 861 insertions), merged to main, pushed.

## Decisions

### Align Basic auth regex to contract specification exactly

**Choice:** Changed implementation from `[A-Za-z0-9+/=]{8,}` to `[A-Za-z0-9+/]{8,}=*` to match the contract.

**Driver:** The contract in `T-20260330-01` specifies `[A-Za-z0-9+/]{8,}=*` sourced from `redact.py:97-98`. The implementation allowed `=` inside the character class, counting padding toward the 8-char minimum.

**Rejected:** Keep the implementation as-is — no practical impact since real base64 auth tokens always exceed 8 non-padding characters. Rejected because: if the contract says something specific, the implementation should match it rather than arguing the deviation doesn't matter in practice.

**Trade-offs accepted:** None — the change is pure alignment.

**Confidence:** High (E2) — verified against both the contract and `redact.py` source.

**Reversibility:** High — single regex edit.

**Change trigger:** None.

### Dev-repo internal use as the R1/R2 rollout target

**Choice:** The current R1/R2 slice targets internal use from the dev repo, not packaged-plugin deployment or broader production.

**Driver:** Matches the implemented slice: no plugin.json, no .mcp.json, no skills/hooks. The runtime works but isn't packaged. User: "Dev-repo internal use. Your recommendation matches where this actually is."

**Rejected:**
- **Packaged plugin for the team** — requires plugin artifact structure that doesn't exist. Would add packaging work to the critical path before the runtime debt posture is even decided.
- **Broader production** — requires hook-guard integration, audit-consumer interface, and re-assessment of all parked items under production expectations. Premature.

**Trade-offs accepted:** Users can't install codex-collaboration as a plugin yet. They must run the MCP server from the repo checkout. This is acceptable for internal development.

**Confidence:** High (E2) — the packaging artifacts literally don't exist.

**Reversibility:** High — this is a classification decision, not a technical choice. Upgrading the target is additive.

**Change trigger:** Team requests plugin installation capability, or an external user needs access.

### Replace triage ceremony with code-local invalidation annotations plus release posture table

**Choice:** Instead of a multi-phase triage plan (T1-T4), embed invalidation triggers directly in code at chokepoints and record the release-risk acceptance in the carry-forward ticket.

**Driver:** User agreed with my critique: "T1 as ceremony without a trigger" was a decision to keep all remaining debt parked while pretending it was an active workflow. Annotations at invalidation sites are higher-reliability than periodic triage because they surface the debt when the activating change actually happens.

**Rejected:**
- **Periodic triage ceremony (T1-T4)** — medium risk of becoming a recurring no-op. User: "You're right that my old T1 was not a real task."
- **Annotations only without central release artifact** — I initially proposed this. User pushed back: "I would not fully eliminate the strategic layer in favor of only code annotations." Annotations tell you when to reconsider, but not whether the risk was already accepted for this release.

**Trade-offs accepted:** 7 code comments added across 4 files. Minor maintenance burden. Each comment links to a specific release posture item.

**Confidence:** High (E2) — both the annotation placement and the release posture table were adversarially reviewed.

**Reversibility:** High — comments can be removed or updated.

**Change trigger:** If annotations prove insufficient (a capability change lands without anyone seeing the annotation), add automated checks instead.

### Codex-collaboration as sole successor to cross-model

**Choice:** Record in `decisions.md` that codex-collaboration is the sole planned successor. Cross-model remains a migration inventory and failure-mode reference, not a co-equal long-term surface.

**Driver:** The user's stated goal: "complete building the codex-collaboration system/plugin in full" to "completely supersede the cross-model plugin." Codex-collaboration's architecture (direct JSON-RPC, session-scoped runtime, lineage persistence) is fundamentally better than cross-model's CLI shim.

**Rejected:** Maintaining both plugins as parallel surfaces. Rejected because: two competing plugin surfaces with overlapping scope creates confusion about which to use and splits maintenance effort.

**Trade-offs accepted:** Cross-model continues to be the only usable plugin until codex-collaboration reaches plugin shell + consult parity (T-20260330-02). During the transition, cross-model is the production surface.

**Confidence:** High (E2) — architectural comparison confirmed codex-collaboration's approach is superior on transport, lifecycle, and persistence dimensions.

**Reversibility:** Medium — the decision is recorded but reversing would require significant scope change to cross-model.

**Change trigger:** Discovery that codex-collaboration's architecture has a fundamental limitation that cross-model's doesn't share.

### Retire context-injection by default, pending benchmark

**Choice:** Context-injection is not ported to codex-collaboration. Claude-side scouting (agents using Glob/Grep/Read) replaces plugin-side scouting (process_turn/execute_scout). This is the default posture; the benchmark contract governs reversal.

**Driver:** Cross-model needed plugin-side scouting because the codex CLI shim couldn't access Claude's tools. Codex-collaboration's MCP architecture allows Claude-side agents to scout and pass results via `explicit_paths`/`explicit_snippets` on consult and dialogue calls. Simpler architecture, fewer moving parts.

**Rejected:**
- **Port context-injection** — ~1000 tests, ~15 modules, designed for a different transport layer. High cost, uncertain benefit when Claude-side scouting may suffice.
- **Retire without benchmark** — user insisted on a defensible evidence base: "It felt fine is not sufficient."

**Trade-offs accepted:** If Claude-side scouting proves insufficient, a focused follow-up subsystem will be needed. The benchmark contract defines exactly when this happens and what evidence triggers it.

**Confidence:** Medium (E1) — architectural argument is sound but the benchmark hasn't been executed. The 4-gate pass rule will convert this to E2 or trigger a focused follow-up.

**Reversibility:** High — retirement is the default; the benchmark can reverse it.

**Change trigger:** Benchmark failure on any of the 4 gates.

### Split Phase 2 into plugin shell (2a) and safety substrate (2b)

**Choice:** Separate packaging work from substrate porting into distinct tickets.

**Driver:** I identified that "plugin shell plus consult parity" bundled mechanical packaging work with design-judgment substrate porting. User agreed: "Phase 2 scope might benefit from splitting."

**Rejected:** Single combined Phase 2 — hides the substrate porting design decisions behind mechanical packaging work. Different risk profiles deserve separate tracking.

**Trade-offs accepted:** Two tickets instead of one. Minimal overhead given the scope difference.

**Confidence:** High (E2) — scope boundaries are clean.

**Reversibility:** High — tickets can be combined if the split proves unnecessary.

**Change trigger:** None — the split is organizational, not architectural.

### Split delegation into foundation (T-05) and promotion/UX (T-06)

**Choice:** Execution-domain infrastructure (worktree, runtime, job state, approval routing) in one ticket; promotion protocol, artifact hashes, rollback, and `/delegate` skill in a separate ticket.

**Driver:** User: "I would split delegation into two phases: execution-domain foundation first, promotion/delegate UX second. That matches the existing delivery split in delivery.md, and it prevents '/delegate' from becoming another oversized milestone that hides the hard parts."

**Rejected:** Single delegation ticket — obscures the infrastructure/product boundary.

**Trade-offs accepted:** T-06 depends on T-05, adding a sequential dependency in the execution-domain lane.

**Confidence:** High (E2) — matches the delivery.md staging.

**Reversibility:** High.

**Change trigger:** None.

### Benchmark contract with fixed 8-task corpus and 4-gate pass rule

**Choice:** Define the context-injection retirement decision through a fixed-corpus benchmark with quantitative pass/fail gates, not narrative judgment.

**Driver:** User: "Define the context-injection retirement benchmark before Phase 3 starts, not during it." User specified: fixed corpus, fixed rubric, zero-tolerance on safety, relative quality gates.

**Rejected:** Ad hoc evaluation ("it felt fine") — user explicitly stated this is not sufficient for a retirement decision.

**Trade-offs accepted:** The 8-task corpus is drawn entirely from the codex-collaboration repo. Both systems face the same familiarity bias, so the comparison is fair, but it doesn't test unfamiliar-repo performance. The benchmark contract includes a known-limitations section acknowledging this.

**Confidence:** High (E2) — pass rule has 4 independent gates with concrete thresholds.

**Reversibility:** Medium — the benchmark contract has change control (edits require explanation and rerun).

**Change trigger:** Discovery that the self-referential corpus produces misleading results. Follow-up: corpus expansion under a new contract revision.

## Changes

### `packages/plugins/codex-collaboration/server/context_assembly.py` — Redaction hardening

**Purpose:** Implement item 6 from the carry-forward debt: add low-ambiguity credential patterns with taxonomy-derived thresholds and ordered application.

**Changes:**
- Added `_REDACTED = "[redacted]"` constant at line 43
- Added `_replace_prefixed_secret()` at line 46 and `_replace_url_userinfo()` at line 50 — per-pattern replacement callables for structure-preserving redaction
- Refactored `_SECRET_PATTERNS` from a flat tuple of patterns to a tuple of `(pattern, replacement)` pairs with full type annotation at lines 54-80
- Pattern ordering: PEM -> URL userinfo -> Basic auth -> AKIA -> GitHub gh*_ -> sk-* -> Bearer -> keyword assignment (most-specific-first per contract)
- `_redact_text()` at line 393: changed from `pattern.sub("[redacted]", ...)` to `pattern.sub(replacement, ...)` where replacement is either a string or callable

**Key details:** Basic auth regex `(?i)(authorization\s*:\s*basic\s+)[A-Za-z0-9+/]{8,}=*` matches contract exactly — `=` padding is trailing, not inside the character class. AKIA uses exact length `{16}` not minimum. GitHub tokens use `{36,}` minimum. Both have `\b` word boundaries per `secret_taxonomy.py`.

### `packages/plugins/codex-collaboration/tests/test_context_assembly.py` — Redaction tests

**Purpose:** Cover all 11 acceptance criteria from `T-20260330-01`.

**New tests:**
- `test_assembly_redacts_low_ambiguity_credential_forms` (line 87): all 5 new pattern families + structural preservation assertions
- `test_assembly_does_not_redact_code_like_false_positives` (line 125): `ghp_enabled`, `akia_prefix`, `basic_auth_setup`, `basic_config`
- `test_assembly_does_not_redact_off_by_one_akia_lengths` (line 152): 15-char suffix (too short for `{16}`) and 17-char suffix (blocked by `\b` word boundary)
- `test_assembly_preserves_assignment_label_for_overlapping_redaction_rules` (line 166): `api_key = AKIAIOSFODNN7EXAMPLE` -> exactly one `[redacted]`, label survives

### `docs/tickets/2026-03-27-r1-carry-forward-debt.md` — Release posture table

**Purpose:** Convert items 1-5 from generic "parked" debt to explicit accepted risks for the dev-repo internal use rollout target.

**Changes:**
- Added "Release Posture — R1/R2 Dev-Repo Internal Use" section with 5-row table
- Each row has: accepted risk, blast radius if undetected, invalidation trigger, re-review condition, owner
- Preamble distinguishes backlog classification ("Parked") from release acceptance
- Item 6 updated from "Promoted" to "Closed" with reference to `T-20260330-01`
- Resolution log extended with item 6 closure entry

### `docs/tickets/2026-03-30-context-assembly-redaction-hardening.md` — Item 6 closed

**Purpose:** Close the item 6 packet.

**Changes:** Status changed from `open` to `closed`. All 11 acceptance criteria checked. Resolution section added with test count (220 passed) and lint confirmation. Replacement format section updated to document keyword assignment label preservation.

### Code annotations — 7 invalidation annotations across 4 files

**Purpose:** Embed release-posture invalidation triggers at the code sites where capability changes would invalidate the park rationale for items 1-5.

| File | Line | Item | Trigger |
|------|------|------|---------|
| `control_plane.py` | 133 | 5 | Advisory widening at the admission gate |
| `control_plane.py` | 181 | 4 | Consult audit emission site |
| `control_plane.py` | 264 | 1 | Bootstrap handshake site |
| `control_plane.py` | 371 | 5 | Policy fingerprint material |
| `jsonrpc_client.py` | 122 | 2 | Process lifecycle boundary |
| `mcp_server.py` | 186 | 3 | Serialized dispatch chokepoint |
| `dialogue.py` | 192 | 3 | Turn-sequence serialization dependence |
| `dialogue.py` | 279 | 4 | Dialogue audit emission site |

### `docs/superpowers/specs/codex-collaboration/delivery.md` — R1/R2 profile + supersession packets

**Purpose:** Anchor the current deployment state and the post-R2 roadmap.

**Changes:**
- Added "R1/R2 Deployment Profile" section: implemented surface, deployment shape, operational assumptions, out-of-scope, risk acceptance cross-reference
- Added "Post-R2 Supersession Packets" section: 6-row table mapping packets to tickets, parallelization note for 3||4 after 2b

### `docs/superpowers/specs/codex-collaboration/decisions.md` — Supersession direction

**Purpose:** Record the three Phase 1 decisions as committed postures.

**Changes:** Added "Supersession Direction" section: codex-collaboration is the sole planned successor, context-injection retired by default pending benchmark, analytics rebuilt on the new audit model.

### `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md` — Benchmark contract

**Purpose:** Define the fixed evaluation protocol for the context-injection retirement decision.

**Key sections:** 8-task fixed corpus, run conditions (same commit, same model), required artifacts (manifest, runs, adjudication, summary), adjudication rules (supported/unsupported/false labels), 4-gate pass rule, decision consequences, known limitations, change control.

### 6 execution tickets — T-20260330-02 through T-20260330-07

**Purpose:** Decompose the full supersession roadmap into executable packets.

| Ticket | Purpose | Blocked by | Blocks |
|--------|---------|------------|--------|
| T-02 | Plugin shell + minimal consult flow | None | T-03 |
| T-03 | Safety substrate + benchmark contract | T-02 | T-04, T-05 |
| T-04 | Dialogue parity + scouting retirement | T-03 | T-07 |
| T-05 | Execution-domain foundation | T-03 | T-06 |
| T-06 | Promotion flow + delegate UX | T-05 | T-07 |
| T-07 | Analytics, reviewer, cutover | T-04, T-06 | None |

## Codebase Knowledge

### Key Code Locations (Verified This Session)

| What | Location | Why verified |
|------|----------|-------------|
| `_SECRET_PATTERNS` | `context_assembly.py:54-80` | Refactored: 8-rule ordered tuple with replacement callables |
| `_redact_text()` | `context_assembly.py:393-397` | Changed: tuple unpacking with per-pattern replacement |
| `_replace_prefixed_secret()` | `context_assembly.py:46-47` | New: preserves group(1) prefix |
| `_replace_url_userinfo()` | `context_assembly.py:50-51` | New: preserves groups 1 and 3 |
| `_read_file_excerpt()` | `context_assembly.py:366-390` | Unchanged from prior session (binary sniff + decode) |
| `_BINARY_SNIFF_BYTES` | `context_assembly.py:41` | Unchanged: 8192-byte window |
| Serialized dispatch | `mcp_server.py:183-186` | Annotated: item 3 invalidation trigger |
| Advisory admission gate | `control_plane.py:130-133` | Annotated: item 5 invalidation trigger |
| Bootstrap handshake | `control_plane.py:264` | Annotated: item 1 invalidation trigger |
| Process lifecycle | `jsonrpc_client.py:119-122` | Annotated: item 2 invalidation trigger |
| Policy fingerprint | `control_plane.py:371` | Annotated: item 5 second anchor |
| Consult audit emission | `control_plane.py:181` | Annotated: item 4 trigger |
| Dialogue audit emission | `dialogue.py:279` | Annotated: item 4 trigger |
| Turn-sequence derivation | `dialogue.py:192` | Annotated: item 3 dependence on serialization |

### Architecture: Redaction Pipeline in context_assembly.py

| Pattern Rule | Regex | Replacement | Source |
|---|---|---|---|
| 1. PEM blocks | `-----BEGIN.*PRIVATE KEY-----` (DOTALL) | `[redacted]` | Existing |
| 2. URL userinfo | `(://[^@/\s:]+:)([^@/\s]+)(@)` | Group-preserving | `redact.py:106-107` |
| 3. Basic auth | `(?i)(authorization\s*:\s*basic\s+)[A-Za-z0-9+/]{8,}=*` | Group-preserving | `redact.py:97-98` (narrowed) |
| 4. AKIA | `\bAKIA[A-Z0-9]{16}\b` | `[redacted]` | `secret_taxonomy.py:72` |
| 5. GitHub | `\b(?:ghp\|gho\|ghs\|ghr)_[A-Za-z0-9]{36,}\b` | `[redacted]` | `secret_taxonomy.py:114` |
| 6. sk-* | `sk-[A-Za-z0-9]{12,}` | `[redacted]` | Existing |
| 7. Bearer | `Bearer\s+[A-Za-z0-9._-]{12,}` | `[redacted]` | Existing |
| 8. Keyword | `(?i)((?:password\|token\|secret\|api[_-]?key)\s*[:=]\s*)[\"']?([^\s\"']{6,})[\"']?` | Group-preserving | Existing (refactored) |

**Overlap behavior:** When AKIA pattern fires on `api_key = AKIAIOSFODNN7EXAMPLE`, the keyword pattern re-matches the residue `api_key = [redacted]` but replacement is idempotent (group(1) + `[redacted]` = same output). Count stays at 1.

### Cross-Model Plugin Capability Inventory

| Capability | Cross-model | Codex-collaboration | Gap |
|---|---|---|---|
| Transport | `codex exec` CLI shim | Direct JSON-RPC to App Server | **Done** (better) |
| Consultation | `/codex` skill | `codex.consult` MCP tool | Runtime done, skill not built |
| Dialogue | `/dialogue` + context-injection | `codex.dialogue.*` tools | Runtime done, agents not built |
| Delegation | `/delegate` via `codex exec` wrapper | Not implemented | Foundation + promotion needed |
| Analytics | `/consultation-stats` + event log | Audit journal (partial) | Dashboard not built |
| Safety | PreToolUse credential scanning | Not implemented | Hook guard needed |
| Profiles | 9 consultation presets | Not implemented | Port semantics |
| Learning retrieval | Briefing injection | Not implemented | Port semantics |
| Context-injection | Plugin-side scouting (~1000 tests) | Retired by default | Benchmark in T-04 |

## Context

### Mental Model

This session's arc was "closing the implementation gap, then lifting the strategic horizon." The first half was concrete implementation work (review, commit, merge). The second half was progressively zooming out: from "what item do we fix next" to "what's the release posture for remaining debt" to "what's the full roadmap to supersede cross-model."

The key insight from the strategic half: **there are two critical paths that don't need to be serialized.** Dialogue parity drives user adoption (nobody can switch from cross-model until `/dialogue` works). Execution-domain foundation drives spec completion (the hardest/longest remaining work). After the shared substrate (2b) is stable, these two tracks can run in parallel because they touch different server modules.

### Project State

| Milestone | Status | Commit/PR |
|-----------|--------|-----------|
| Spec compiled and merged | Complete | `bf8e69e3` |
| T1: Compatibility baseline | Complete | `f53cd6c8` (PR #87) |
| R1: First runtime milestone | Complete | `3490718a` on main |
| Post-R1 spec amendments | Complete | `078e5a39`..`2ae76ed1` on main |
| R2: Dialogue foundation | Complete | `f5fc5aab` on main (PR #89) |
| T1-T2: Live contract probe + audit parity | Complete | `d65c8d54`..`b0f45f95` |
| Item 7: Binary file hardening | Complete | `e6792de8` |
| **Item 6: Redaction hardening** | **Complete** | `1f3305a8` |
| **Release posture + invalidation annotations** | **Complete** | `2994b138` |
| **Supersession roadmap + benchmark + tickets** | **Complete** | `dbc91d8f` |

220 tests passing on main. `main` is even with `origin/main` at `dbc91d8f`.

### Supersession Roadmap

```
T-02 (plugin shell) -> T-03 (substrate) -> T-04 (dialogue) ---------> T-07 (cutover)
                                         -> T-05 (execution) -> T-06 (promotion) -> T-07
```

Parallelization: T-04 and T-05 can run concurrently after T-03 is stable.

## Learnings

### The keyword pattern re-matches `[redacted]` but is idempotent

**Mechanism:** After a prefix pattern (e.g., AKIA) replaces a value with `[redacted]`, the keyword pattern matches `api_key = [redacted]` because `[redacted]` (10 chars) passes `[^\s\"']{6,}`. But `_replace_prefixed_secret` returns `group(1) + _REDACTED` = `api_key = [redacted]` — same as input.

**Evidence:** Verified by tracing through all 8 pattern rules manually. The overlap test (`test_assembly_preserves_assignment_label_for_overlapping_redaction_rules`) confirms `payload.count("[redacted]") == 1`.

**Implication:** If logging or counters are ever added to `_redact_text`, this double-match would inflate counts. Not actionable now but worth knowing.

### Annotations at implementation sites vs caller chokepoints matter

**Mechanism:** A code annotation "revisit X if Y changes" only works if the triggering change must pass through the annotated code. For 3 of 5 items, the triggering change could happen at a *caller* site rather than the annotated *implementation* site.

**Evidence:** Item 3 (concurrent safety) — serialization is enforced at `mcp_server.py` dispatch, not inside `control_plane.py`. A change to dispatch model could bypass a `control_plane.py` annotation entirely.

**Implication:** Always verify that the annotation site is a chokepoint, not just a related code location.

### Benchmark contracts with self-referential corpora are fair but limited

**Mechanism:** All 8 benchmark tasks ask questions about the codex-collaboration repo itself. Both baseline and candidate face the same familiarity, so the comparison is fair. But it doesn't test performance on unfamiliar codebases where scouting strategy matters more.

**Evidence:** Identified during review. Added to the benchmark contract as a known limitation with the follow-up path: corpus expansion under a new contract revision.

**Implication:** If the benchmark passes but real-world dialogue quality seems lower, the self-referential corpus may be masking the gap. The follow-up path is already documented.

## Next Steps

### Implement the plugin shell and minimal consult flow (T-20260330-02)

**Dependencies:** None — first in the chain.

**What to read first:** `T-20260330-02` at `docs/tickets/2026-03-30-codex-collaboration-plugin-shell-and-consult-parity.md`. Also read `packages/plugins/cross-model/.claude-plugin/plugin.json` and `.mcp.json` as packaging precedent.

**Approach:**
1. Create `.claude-plugin/plugin.json` and `.mcp.json` in the codex-collaboration package
2. Create a bootstrap entry point that starts the existing stdio MCP server
3. Add a minimal `/codex` skill mapping to `codex.consult`
4. Add a minimal `/status` skill mapping to `codex.status`
5. Wire `codex.status` as preflight in the consult skill

**Acceptance criteria:** 8 checkboxes in T-02. Key: installed plugin can run a consult flow end-to-end without manual wiring.

**Potential obstacles:** The MCP server currently starts via direct Python invocation. The plugin entry point needs to match whatever the Claude Code plugin system expects. Check cross-model's `.mcp.json` for the launch pattern.

### Implement the shared safety substrate (T-20260330-03)

**Dependencies:** T-02 (plugin shell must exist first).

**What to read first:** `T-20260330-03` at `docs/tickets/2026-03-30-codex-collaboration-safety-substrate-and-benchmark-contract.md`. Key cross-model sources: `credential_scan.py`, `secret_taxonomy.py`, `consultation_safety.py`, `consultation-profiles.yaml`, `retrieve_learnings.py`, `emit_analytics.py`.

**Approach:** Port semantics, not code blindly. The new runtime and audit model are architecturally different from cross-model's shim transport.

**Potential obstacles:** Design decisions about which cross-model semantics survive, which are adapted, and which are dropped. This is where the "port semantics, not code" judgment calls live.

## In Progress

Clean stopping point. All implementation work committed and pushed. The post-R2 hardening arc is fully closed. The supersession roadmap is frozen with executable tickets. No work in flight.

**User's next step:** Begin T-20260330-02 (plugin shell and minimal consult flow).

## Open Questions

### Whether Claude-side scouting suffices for dialogue evidence gathering

The benchmark contract governs this decision. It will be executed during T-04 (dialogue parity). Until then, the default posture is "context-injection retired." If the benchmark fails, a focused follow-up packet addresses the measured shortfall.

### Feature branch cleanup timing (inherited from prior session)

`feature/codex-collaboration-r2-dialogue` still exists on remote. Tagged at `r2-dialogue-branch-tip` -> `d2d0df56`. Can be deleted anytime. No urgency.

### MCP consumer retry behavior for CommittedTurnParseError (inherited)

The error message says "Blind retry will create a duplicate follow-up turn." But Claude (the MCP consumer) has no programmatic mechanism to distinguish this error from a generic tool failure. Wire-level retry prevention is out of scope.

### Chronically unreachable unknown handles (inherited, parked as T2 Item B)

Startup recovery retries `unknown` handles every restart. Explicitly parked — needs TTL design and usage pattern data. Spec acknowledges at `contracts.md:156`.

## Risks

### T-03 is the most overloaded ticket in the chain

T-03 includes credential scanning, secret taxonomy, safety policy, profiles, learning retrieval, analytics emission, AND the benchmark contract adoption. 7 distinct deliverables. The ticket acknowledges "large" effort. If any substrate porting decision proves contentious, T-03 becomes the bottleneck for both the dialogue (T-04) and execution-domain (T-05) lanes.

### Three independent copies of credential-detection logic after substrate port

After T-03 lands, `context_assembly.py`, `redact.py`, and the new codex-collaboration safety substrate will have partially overlapping pattern sets with different thresholds. This is acknowledged duplication. The risk is future maintainers updating one and not the others.

### Benchmark corpus familiarity bias

All 8 tasks are about the codex-collaboration repo. Both systems face the same bias, making the comparison fair. But if Claude-side scouting performs well on familiar code but poorly on unfamiliar repos, the benchmark won't catch it. Follow-up path: corpus expansion under a new contract revision.

## References

| Resource | Location | Purpose |
|----------|----------|---------|
| Prior handoff (resumed from) | `docs/handoffs/archive/2026-03-30_13-13_context-assembly-hardening-item7-closed-item6-scoped.md` | T3-T4 context and item 6 contract |
| Item 6 freeze ticket | `docs/tickets/2026-03-30-context-assembly-redaction-hardening.md` | Implementation contract and acceptance criteria (closed) |
| R1 carry-forward ticket | `docs/tickets/2026-03-27-r1-carry-forward-debt.md` | Release posture table and parked debt |
| Benchmark contract | `docs/superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md` | Context-injection retirement authority |
| Supersession direction | `docs/superpowers/specs/codex-collaboration/decisions.md` | Committed strategic posture |
| Post-R2 packet sequence | `docs/superpowers/specs/codex-collaboration/delivery.md` | Roadmap and parallelization |
| T-02: Plugin shell | `docs/tickets/2026-03-30-codex-collaboration-plugin-shell-and-consult-parity.md` | Next executable packet |
| T-03: Safety substrate | `docs/tickets/2026-03-30-codex-collaboration-safety-substrate-and-benchmark-contract.md` | Substrate porting |
| T-04: Dialogue parity | `docs/tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md` | Adoption gate |
| T-05: Execution domain | `docs/tickets/2026-03-30-codex-collaboration-execution-domain-foundation.md` | Completion gate (infrastructure) |
| T-06: Promotion + delegate | `docs/tickets/2026-03-30-codex-collaboration-promotion-flow-and-delegate-ux.md` | Completion gate (product) |
| T-07: Cutover | `docs/tickets/2026-03-30-codex-collaboration-analytics-reviewer-and-cutover.md` | Final removal |
| Taxonomy thresholds | `secret_taxonomy.py:72,114` | AKIA and GitHub token patterns |
| `redact.py` precedent | `context-injection/context_injection/redact.py:94-116` | Group-preserving patterns |
| Item 7 fix | `e6792de8` | Binary file hardening (closed prior session) |

## Gotchas

### `_redact_text` overlap is idempotent but not zero-cost

The keyword pattern re-matches `[redacted]` tokens produced by prefix patterns. The replacement is idempotent (same output), so it doesn't affect correctness. But if counters or telemetry are ever added, they'll overcount.

### Annotation sites must be chokepoints, not just related code

3 of the original 5 proposed annotation sites were at implementation locations rather than caller chokepoints where the triggering change would actually happen. The corrected sites are documented in the Changes section and verified against the codebase.

### The `\b` word boundary on AKIA prevents matching the 17-char case

`AKIAIOSFODNN7EXAMPLE1` (17 chars after AKIA) is not matched because `\b` requires a boundary between the last word character and the next. Since both `E` and `1` are word characters, there's no boundary. The test `test_assembly_does_not_redact_off_by_one_akia_lengths` locks this.

### Benchmark contract has change control

The corpus, adjudication labels, metrics, and pass rule are frozen for this contract version. Any change requires editing the contract, explaining why the previous version was insufficient, and rerunning any comparison that relied on the changed rule. Don't edit mid-run.

## Conversation Highlights

**On T1 as ceremony:**
User (after my critique): "You're right that my old T1 was not a real task."

**On annotations vs central artifact:**
User: "I would not fully eliminate the strategic layer in favor of only code annotations. The annotations are the right activation mechanism for items 1-5, but they do not replace the need for one explicit product decision."

**On the benchmark contract:**
User: "Define the context-injection retirement benchmark before Phase 3 starts, not during it." User specified the exact pass rule: "zero safety_violations; false_claim_count no worse than cross-model; supported_claim_rate within 10%; convergence no worse by more than 1 session out of 8. That is defensible. 'It felt fine' is not."

**On Phase 2 split:**
User: "Phase 2's scope is two things pretending to be one."

**On delegation split:**
User: "That matches the existing delivery split in delivery.md, and it prevents '/delegate' from becoming another oversized milestone that hides the hard parts."

**On the rollout target:**
User: "Dev-repo internal use. Your recommendation matches where this actually is."

**On the stated goal:**
User: "The goal is to complete building the codex-collaboration system/plugin in full. What's the roadmap from where we are right now, and a completed implementation that completely supersedes the cross-model plugin?"

## User Preferences

**Evidence-level rigor (continued from prior sessions):** User holds all decisions to defensible evidence standards. "It felt fine is not sufficient" for a retirement decision. Benchmark contracts need fixed corpora and quantitative pass rules.

**Iterative adversarial refinement (continued):** User uses adversarial review as a structural tool for progressive sharpening, not just final validation. Three rounds of adversarial exchange refined the triage plan from T1-T4 ceremony into annotations + release posture.

**Hypothesis-driven exploration (continued):** Present ranked hypotheses with evidence. Wait for confirmation.

**Production-first ordering (continued):** Fix production code before updating fakes/tests. Land crash fixes immediately.

**Commit scope discipline (continued):** Each commit independently justified. Don't bundle unrelated fixes.

**Grounded pushback (continued):** Push back with file:line references and specific reasoning.

**Scope splitting by risk profile:** User splits work by risk profile, not just size. "Packaging work has different risk profiles from substrate porting decisions" — they deserve separate tickets even if they could fit in one.

**Annotations should state acceptance conditions, not just triggers:** User: "The annotations should not just say 'revisit if X changes'; they should say 'current release accepts this only while X remains true.' That makes them operationally useful instead of merely informative."
