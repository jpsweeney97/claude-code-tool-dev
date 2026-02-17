# T-003: Context Injection System Review — Post-Merge Findings

```yaml
id: T-003
date: 2026-02-17
status: closed
priority: medium
branch: chore/context-injection-review-fixes
blocked_by: []
blocks: []
related: [T-002]
```

## Summary

Five-reviewer parallel review of the merged context injection system (PR #10, `af8544d`) found **22 unique findings** across architecture coherence, code quality, security, and test coverage. No critical bugs — the system is architecturally sound and well-tested (963 tests). Findings are concentrated in three categories: (1) dead code and DRY violations, (2) documentation drift between contract and implementation, (3) test coverage gaps for specific guard paths.

**Scope:** Code and documentation fixes in `packages/context-injection/` and `docs/`. No architectural changes.

**Reviewers:** architect-reviewer (architecture coherence), quality-reviewer (code quality + deferred PR findings), security-reviewer (trust boundaries + HMAC), test-reviewer-core (pipeline/checkpoint/ledger/conversation coverage), test-reviewer-dispatch (control/templates/execute/types/integration coverage).

## Prerequisites

Before starting fixes:
1. Create branch `chore/context-injection-review-fixes` from `main`
2. No design decisions to resolve (HMAC deferred — see Security section)
3. Run `cd packages/context-injection && uv run pytest` to confirm 963 tests pass

## 1. P1 — Fix Before Next Feature Work

### P1-1: Dead `over_budget` branch + duplicated `compute_budget`

**Found by:** quality-reviewer, security-reviewer

`templates.py:115-127` and `execute.py:183-206` both define `compute_budget()` with identical budget-status logic. In both, `evidence_remaining = max(0, ...)` clamps to `>=0`, making the `over_budget` branch unreachable. The `Budget.budget_status` Literal type includes `"over_budget"` as a valid variant that can never be produced.

**Fix (3 steps):**
1. Remove `"over_budget"` from `Budget.budget_status` Literal type (and any downstream checks)
2. Remove the dead `else: budget_status = "over_budget"` branches from both files
3. Extract shared budget-status computation into a single utility to prevent future drift

**Files:** `base_types.py` or `types.py` (Literal type), `templates.py`, `execute.py`

**Tests:** Update any tests that reference `"over_budget"`. Add a test confirming `budget_status` is `"at_budget"` when `evidence_remaining == 0`.

### P1-2: Pipeline step numbering drift vs contract

**Found by:** architect-reviewer

`pipeline.py` docstring numbers steps 1-17 with sub-steps (1b, 3b). The protocol contract (`docs/references/context-injection-contract.md:939-956`) numbers the same steps differently. The logic matches — only the numbering has drifted.

**Fix:** Re-number the `pipeline.py` docstring to match the contract, or vice versa. Contract is the system of record — prefer updating `pipeline.py`.

**Files:** `pipeline.py` (docstring only)

### P1-3: `ErrorCode` enum incomplete or redundant

**Found by:** architect-reviewer, quality-reviewer

`enums.py:109-116` defines `ErrorCode` with 4 values. `types.py:276-286` defines `ErrorDetail.code` as a Literal with 9 values including 5 checkpoint/ledger/turn-cap codes missing from the enum. The Literal type is the source of truth on the wire.

**Fix (choose one):**
- **Option A (recommended):** Delete the `ErrorCode` enum. The Literal in `types.py` is authoritative. Remove any imports.
- **Option B:** Complete the enum with all 9 values and add a parity test.

**Files:** `enums.py`, any files importing `ErrorCode`

## 2. P2 — Address Soon

### P2-1: Dual-claims channel guard has zero test coverage

**Found by:** test-reviewer-core

`pipeline.py:132-155` has two early-return error paths for mismatched `focus.claims` vs top-level `claims` and `focus.unresolved` vs top-level `unresolved` (CC-PF-3 guard). The test helper `_make_turn_request` auto-syncs these fields, so no test ever triggers either guard.

**Fix:** Add 2 tests using `TurnRequest.model_construct()` or manual construction with mismatched focus/top-level claims. Assert `TurnPacketError(code="ledger_hard_reject")`.

**Files:** `tests/test_pipeline.py`

### P2-2: `checkpoint_stale` and `checkpoint_missing` never tested through pipeline

**Found by:** test-reviewer-core

`pipeline.py:82-88` catches `CheckpointError` and wraps it in `TurnPacketError(code=exc.code)`. Only `checkpoint_invalid` is tested through the pipeline. `checkpoint_stale` and `checkpoint_missing` codes are only tested at the unit level in `test_checkpoint.py`.

**Fix:** Add 2 pipeline-level tests:
1. Turn 2 with mismatched `checkpoint_id` → `checkpoint_stale`
2. Turn 2 with no state and no checkpoint → `checkpoint_missing`

**Files:** `tests/test_pipeline.py`

### P2-3: `_load_git_files` error paths untested + design choice undocumented

**Found by:** architect-reviewer, test-reviewer-dispatch

`server.py:53-68` returns empty `set()` on `TimeoutExpired`, `FileNotFoundError`, and `RuntimeError`. The docstring says "Fail closed on error" (correct — empty set denies all files). But the design spec listed this as an open question without documenting the resolution. Two of three exception paths (`TimeoutExpired`, `RuntimeError`) have no tests.

**Fix:**
1. Add 2 tests for `TimeoutExpired` and `RuntimeError` paths
2. Add a comment documenting the design choice: "Fail closed: empty set means all files denied by git gating"

**Files:** `server.py`, `tests/test_server.py` or `tests/test_integration.py`

### P2-4: `ConversationState` uses `BaseModel` not `ProtocolModel`

**Found by:** quality-reviewer

`conversation.py:17-20` inherits from `BaseModel` with its own `ConfigDict(frozen=True, extra="forbid", strict=True)`. Every other model uses `ProtocolModel` (which provides the same config). The configs are functionally identical but the inconsistency breaks the inheritance pattern.

**Fix (choose one):**
- **Option A:** Inherit from `ProtocolModel`. Verify no behavioral change.
- **Option B:** Add a comment explaining why `ConversationState` is deliberately different (internal type, not protocol type).

**Files:** `conversation.py`

### P2-5: `focus.text` semantic mismatch between agent and design spec

**Found by:** architect-reviewer

Agent file (`codex-dialogue.md:225`) uses `focus.text` as a stable topic. Design spec envisions focus changing per-turn via priority system. Contract is ambiguous. Currently benign — server doesn't use `focus.text` content for any logic.

**Fix:** Document the intended semantics in the protocol contract. Add a note: "`focus.text` is informational. The server does not use it for template ranking or convergence detection."

**Files:** `docs/references/context-injection-contract.md`

### P2-6: `server.py` handlers return `dict`, output schema incorrect

**Found by:** architect-reviewer

Both handlers return `result.model_dump(mode="json")` (a `dict`) to work around FastMCP double-serialization of discriminated unions. Function signatures are typed as `-> dict`, so auto-generated `outputSchema` advertises `dict` instead of `TurnPacket`/`ScoutResult`.

**Fix:** Add a docstring or comment documenting the workaround and the SDK issue. Revisit when FastMCP supports discriminated union serialization.

**Files:** `server.py`

### P2-7: Unused enum classes (12 of 15 never imported outside tests)

**Found by:** quality-reviewer

`enums.py` defines 15 StrEnum classes. Only 3 are imported in production code (`EffectiveDelta`, `QualityLabel`, `ValidationTier`). The other 12 parallel the Literal types in `types.py`.

**Fix (choose one):**
- **Option A:** Add a module docstring explaining the convention: "Literal types are authoritative for wire protocol. StrEnum classes here are for internal use and IDE support only."
- **Option B:** Remove unused enums. Keep only the 3 that are actively imported.

**Files:** `enums.py`

### P2-8: `assert` used for runtime invariants (6 sites)

**Found by:** quality-reviewer

Six `assert` statements guard invariants that preceding logic guarantees. These are stripped with `python -O`.

| File | Line | Assertion |
|------|------|-----------|
| `execute.py` | 122 | `spec.center_line is not None` |
| `execute.py` | 239 | `isinstance(spec, ReadSpec)` |
| `execute.py` | 264 | `realpath is not None` |
| `execute.py` | 312 | `isinstance(redact_outcome, RedactedText)` |
| `execute.py` | 384 | `isinstance(spec, GrepSpec)` |
| `templates.py` | 566 | `pd is not None` |

**Fix:** Replace each `assert X` with `if not X: raise RuntimeError(...)` or a descriptive `ValueError`. Low urgency — MCP servers don't run with `-O` — but defensive.

**Files:** `execute.py`, `templates.py`

## 3. P3 — Low Priority / Nits

| # | Finding | File | Notes |
|---|---------|------|-------|
| P3-1 | Unbounded string fields in TurnRequest | `types.py` | Mitigated by 16KB checkpoint cap. Consider `Field(max_length=...)` for defense-in-depth |
| P3-2 | No list length limits on claims/tags/unresolved | `types.py` | Mitigated by turn cap + checkpoint cap. Consider list length caps (50 claims, 20 tags) |
| P3-3 | `_extract_line_number()` None-return path untested | `tests/test_templates.py` | Defensive path — file_loc entities should always have line anchor |
| P3-4 | Unknown Tier 2 entity type skip branch untested | `tests/test_templates.py` | Silent skip for unrecognized types |
| P3-5 | `LedgerEntry.delta` typed as `str`, not constrained Literal | `ledger.py:33` | Input is already validated via `TurnRequest.delta` Literal |
| P3-6 | `ErrorDetail.details` typed as `dict`, not `dict[str, Any]` | `types.py:288` | Consistency with `ValidationWarning.details` |
| P3-7 | `_make_clarifier` uses `or` chain instead of `_CLARIFIER_FILE_TYPES` frozenset | `templates.py:388` | Frozenset already exists at line 79 |
| P3-8 | Mutable `list[int]` counter pattern | `templates.py:450` | Works correctly, minor readability concern |
| P3-9 | Design spec module layout outdated (9 → 18 modules) | Design spec | Implementation is authoritative |
| P3-10 | `extra="forbid"` not tested for `ConversationState` | `tests/test_conversation.py` | Pydantic enforces reliably |
| P3-11 | Writing principles numbering bug (`#14` → `#13`) | `docs/references/writing-principles.md:135` | `### Outcomes (#14)` should be `### Outcomes (#13)` |
| P3-12 | `app_lifespan` async integration not directly tested | `server.py` | Components tested individually |
| P3-13 | Regex execution bound per-text not per-turn | Entity extraction | No ReDoS risk, but entity count is unbounded per turn |

## 4. Deferred Findings — Status Update

### HMAC Checkpoint Authentication (P1 from PR #10) — DEFER CONFIRMED

**Security reviewer recommendation:** Defer. The checkpoint carries only conversation metadata (claims, evidence history, turn entries) — not execution parameters, file paths, or HMAC keys. Forging a self-consistent checkpoint requires matching the full `ConversationState` Pydantic schema. The worst outcome is biased scout selection or premature conversation end, not data exfiltration or unauthorized file access.

The real security boundary — what files get read and how they're redacted — is enforced independently of checkpoint state via HMAC tokens (per-process key), path safety (5-layer defense-in-depth), and redaction pipeline.

**Revisit if:**
1. Checkpoint starts carrying execution-relevant data (paths, permissions, caps)
2. System moves to multi-agent or multi-tenant deployment
3. A concrete attack vector through claim history manipulation is demonstrated

### Agent Severity C Issues (from PR #10 Codex review)

| Issue | Status | Detail |
|-------|--------|--------|
| Subjective ranking terms | Still present | `codex-dialogue.md:323-324` |
| `turn_count` naming inconsistency | Still present | `codex-dialogue.md:105` |
| Pre-flight checklist edge cases | Partial | Zero-scout/zero-turn scenarios |
| `turn_history` append timing | **Resolved** | Fixed in `637daff` |
| Step 5 unreachable action fallback | **By-design** | Defense-in-depth |

## 5. Positive Security Assessment

The security reviewer confirmed these properties:

- **No shell injection** — all subprocess calls use list-form arguments, grep uses `--fixed-strings`
- **5-layer path defense** — normalization, denylist, git gating, containment, runtime re-check
- **Fail-closed redaction** — unknown formats suppressed, PEM triggers full suppression
- **HMAC token integrity** — per-process 32-byte key, constant-time comparison, replay prevention, spec-bound tokens
- **Bounded resources** — hard caps on turns (15), evidence (5), checkpoint (16KB), grep timeout (5s)
- **Immutable state** — frozen Pydantic models, atomic dict replacement, projection methods

## 6. Execution Plan

### Phase 1: P1 fixes

1. P1-1: Remove dead `over_budget` + deduplicate `compute_budget`
2. P1-2: Re-number pipeline step comments
3. P1-3: Clean up `ErrorCode` enum

### Phase 2: P2 test gaps

4. P2-1: Add dual-claims guard tests (2 tests)
5. P2-2: Add pipeline-level checkpoint error tests (2 tests)
6. P2-3: Add `_load_git_files` error path tests (2 tests) + document design choice

### Phase 3: P2 code/doc cleanup

7. P2-4: Fix `ConversationState` base class
8. P2-5: Document `focus.text` semantics in contract
9. P2-6: Document `server.py` dict return workaround
10. P2-7: Document or clean up unused enums
11. P2-8: Replace `assert` with explicit raises

### Phase 4: P3 nits

12. P3-11: Fix writing principles numbering
13. Remaining P3 items by preference

### Verification

After all fixes:
```bash
cd packages/context-injection && uv run pytest
```
Expected: 963 + ~6 new tests = ~969 tests passing.

## 7. References

### Source Files

| Module | Path |
|--------|------|
| Pipeline | `packages/context-injection/context_injection/pipeline.py` |
| Checkpoint | `packages/context-injection/context_injection/checkpoint.py` |
| Ledger | `packages/context-injection/context_injection/ledger.py` |
| Conversation | `packages/context-injection/context_injection/conversation.py` |
| Control | `packages/context-injection/context_injection/control.py` |
| Templates | `packages/context-injection/context_injection/templates.py` |
| Execute | `packages/context-injection/context_injection/execute.py` |
| Types | `packages/context-injection/context_injection/types.py` |
| Enums | `packages/context-injection/context_injection/enums.py` |
| Base types | `packages/context-injection/context_injection/base_types.py` |
| Server | `packages/context-injection/context_injection/server.py` |

### Documentation

| Document | Path |
|----------|------|
| Protocol contract | `docs/references/context-injection-contract.md` |
| Design spec | `docs/plans/2026-02-11-conversation-aware-context-injection.md` |
| Agent file | `.claude/agents/codex-dialogue.md` |
| Writing principles | `docs/references/writing-principles.md` |

### Related Tickets

| Ticket | Relationship |
|--------|-------------|
| T-002 | Predecessor — T-002 fixed plan document errata. T-003 reviews the implemented code post-merge |
| PR #10 | The merge that T-003 reviews (`af8544d`) |

### Review Session

| Reviewer | Angle | Key Findings |
|----------|-------|-------------|
| architect-reviewer | Architecture coherence | P1-2 (step numbering), P1-3 (enum), P2-5 (focus.text), P2-6 (dict return) |
| quality-reviewer | Code quality + deferred | P1-1 (dead code), P2-4 (base class), P2-7 (enums), P2-8 (asserts) |
| security-reviewer | Trust boundaries | HMAC deferral confirmed, S-1/S-2/S-3 defense-in-depth suggestions |
| test-reviewer-core | Core module coverage | P2-1 (dual-claims), P2-2 (checkpoint errors) |
| test-reviewer-dispatch | Dispatch module coverage | P2-3 (git files), P3-3/P3-4 (minor gaps) |
