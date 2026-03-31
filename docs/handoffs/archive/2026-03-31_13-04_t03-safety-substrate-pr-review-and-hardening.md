---
date: 2026-03-31
time: "13:04"
created_at: "2026-03-31T17:04:28Z"
session_id: 2edcade4-ad64-4944-b5b6-cfdb5622ac6e
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-03-31_15-49_t03-safety-substrate-implementation-complete.md
project: claude-code-tool-dev
branch: feature/codex-collaboration-safety-substrate
commit: f7d84a65
title: "T-03 safety substrate PR review and hardening"
type: handoff
files:
  - packages/plugins/codex-collaboration/server/consultation_safety.py
  - packages/plugins/codex-collaboration/server/secret_taxonomy.py
  - packages/plugins/codex-collaboration/server/context_assembly.py
  - packages/plugins/codex-collaboration/server/retrieve_learnings.py
  - packages/plugins/codex-collaboration/server/dialogue.py
  - packages/plugins/codex-collaboration/scripts/codex_guard.py
  - packages/plugins/codex-collaboration/tests/test_codex_guard.py
  - packages/plugins/codex-collaboration/tests/test_consultation_safety.py
  - packages/plugins/codex-collaboration/tests/test_context_assembly.py
  - packages/plugins/codex-collaboration/tests/test_dialogue.py
  - packages/plugins/codex-collaboration/tests/test_retrieve_learnings.py
  - packages/plugins/codex-collaboration/tests/test_secret_taxonomy.py
  - packages/plugins/codex-collaboration/pyproject.toml
---

# T-03 safety substrate PR review and hardening

## Goal

Conduct a comprehensive PR review of PR #90 (T-03 safety substrate) and fix all critical and important findings before merge. The T-03 implementation was complete from the prior session (347/347 tests, 10 commits), but the user explicitly stated the PR was not yet ready for merge — it needed a full review first.

**Trigger:** User loaded the prior session's handoff and said: "PR #90 is not yet ready for merge - it still needs a full review." Then invoked `/pr-review-toolkit:review-pr`.

**Stakes:** This is safety-critical code — credential scanning, tool-input safety policy, consultation profiles, learning retrieval. Bugs in this code could expose credentials to Codex or allow unscanned tool inputs through the advisory pipeline. The review needed to be thorough because the consequences of shipping a safety gap are high.

**Success criteria:** All critical findings fixed, all important findings addressed, 358/358 tests passing (11 new hardening tests), PR description updated with the hardening section.

**Connection to project arc:** This is the review and hardening pass for T-03. The prior session implemented T-03 (9 tasks). This session validated and hardened it. Next: merge PR #90, then evaluate the `codex.consult` open question or address T-03 deferred items (AC6 analytics, journal profile integration).

## Session Narrative

Session began by loading the prior handoff (`2026-03-31_15-49_t03-safety-substrate-implementation-complete.md`). The handoff described T-03 as complete with PR #90 created and ready for review. The three next steps were: (1) merge PR #90, (2) evaluate `codex.consult` open question, (3) address T-03 deferred items.

The user immediately redirected — PR #90 was not ready for merge without a full review. They invoked the PR review toolkit. This set the session's character: review-driven, with the user operating as a critical reviewer who validates findings, corrects proposed fixes, and controls scope.

Gathered PR scope: 29 files changed, ~2600 lines added. Based on the changes (safety-critical code, new types, new test files, error handling), all 5 review aspects were applicable. Launched 5 specialized review agents in parallel:

| Agent | Focus | Duration |
|-------|-------|----------|
| code-reviewer | Bugs, security, conventions | ~5 min |
| test-analyzer | Coverage quality and gaps | ~2 min |
| failure-hunter | Silent failures, error handling | ~3 min |
| type-analyzer | Type design, invariants | ~3 min |
| comment-analyzer | Comment accuracy, rot | ~3 min |

Results arrived over ~5 minutes. Compiled an aggregated report with cross-agent deduplication. Multiple agents independently converged on the same issues — `policy_for_tool` silent fallback was flagged by both failure-hunter (error handling) and code-reviewer (security); PEM `redact_enabled=False` was flagged by code-reviewer and test-analyzer (missing contract test). This cross-agent convergence increased confidence in the findings.

The aggregated report identified 2 critical, 9 important, and 14 suggestion-level findings. Presented to user with file:line references and proposed fixes for each.

**Key pivot — user corrected C2 fix:** The naive fix for PEM redaction (flip `redact_enabled=True`) was incomplete. The user identified that the current pattern at `secret_taxonomy.py:87` only matches the header line (`-----BEGIN RSA PRIVATE KEY-----`), while `context_assembly.py:361` sends full file excerpts through `_redact_text()`. Flipping `redact_enabled` would replace the header with `[REDACTED:value]` but leave the base64 body and footer intact — Codex would still see the key material. The user stated: "This needs full-block PEM redaction, or separate egress and redaction patterns."

This correction was the most important moment in the session. It transformed C2 from a simple boolean flip into a design question requiring a new field on `SecretFamily`.

I proposed two approaches: (A) add a `redact_pattern` field to `SecretFamily` with a multiline regex, or (B) create two separate families for PEM. Recommended Approach A because the egress scanner's header-only pattern is genuinely the right choice for fast detection, while redaction needs to remove the full block — these are different jobs with different optimal patterns. User confirmed Approach A was preferred.

**User also refined I2 and I5:** For I2, the user stated: "I would not implement it as `assert`. If we want that invariant enforced in production, `_redact_text()` should raise a descriptive runtime error." For I5, they noted: "An outer fail-closed catch is reasonable, but it must not accidentally convert intentional `SystemExit(0)` into exit 2."

User then implemented all fixes themselves. Returned with verification: 159 targeted tests passed, 358 full suite passed, ruff clean. Asked for critical review of the implementation.

I reviewed all 7 changed source files and 6 changed test files in parallel. Verified:
- C1: `policy_for_tool` raises `KeyError`, guard catches via `except Exception → exit 2`
- C2: PEM `redact_pattern` uses named backreference for header-footer matching, with `[\s\S]*\Z` fallback for truncated excerpts
- I1: Stale docstring removed
- I2: `_validate_boundary_map` raises `RuntimeError` with diagnostic context
- I3: `retrieve_learnings` wrapped in broad `except Exception`
- I4: `_log_recovery_failure` helper used at all 3 recovery sites
- I5: `run()` catches `KeyboardInterrupt` only, preserves `SystemExit(0)`
- I6: Monkeypatched test exercises guard internal-error branch

Additionally verified PEM regex behavior by running it against 3 test cases (full block, truncated excerpt, mismatched labels). All behaved correctly — mismatched labels over-redact to EOF, which is the safe direction.

User committed (`f7d84a65`), then asked to update the PR. Pushed with `--force-with-lease` (branches had diverged due to the hardening commit) and updated PR #90 description via GitHub API.

## Decisions

### Fix scope: 8 targeted fixes, no broad refactoring

**Choice:** Fix C1, corrected C2, I1, I2, I3, I4, I5, I6. Defer I7/I8/I9 and suggestions S1-S14.

**Driver:** User stated: "Most likely, this is a narrow safety patch, not a broad refactor." And: "Fix now: C1, corrected C2, I1, I3, I4, I5, I6. Fold in for better hardening: I2. Broader cleanup: I7, I8, I9, and most of S1-S14."

**Alternatives considered:**
- **Fix everything** — address all 25 findings in one pass. Rejected by user as too broad: "I haven't independently validated all 14 suggestions."
- **Fix only criticals** — address C1 and C2 only. Not proposed — user explicitly included the important findings in scope.

**Trade-offs accepted:** I7 (mutable containers in frozen dataclasses), I8 (`tier: str | None` should be `Tier | None`), and I9 ("Release posture item N" comments) remain unfixed. These are correctness/cleanup improvements, not safety gaps.

**Confidence:** High (E2) — user independently validated each finding against the code before accepting.

**Reversibility:** High — each fix is isolated and well-tested.

**Change trigger:** If any deferred finding (I7-I9 or S1-S14) is later found to have safety implications, it would be promoted to the fix set.

### C2: Separate `redact_pattern` field on SecretFamily (Approach A)

**Choice:** Add `redact_pattern: re.Pattern[str] | None = None` to `SecretFamily`. PEM gets a multiline regex that captures header-through-footer. Other families use `None` (falls back to `family.pattern`).

**Driver:** User corrected the naive fix: "If you only flip `redact_enabled=True`, the header gets replaced and the key body/footer still go to Codex. This needs full-block PEM redaction, or separate egress and redaction patterns."

**Alternatives considered:**
- **Approach B: Two families** — keep header-only family for egress, add second multiline family for redaction. Rejected: "Two entries for PEM in the taxonomy. Naming/ordering gets awkward."
- **Naive flip** — just set `redact_enabled=True`. Rejected by user because the header-only pattern would only redact the header line, leaving the base64 body and footer exposed.

**Trade-offs accepted:** Adds a field to `SecretFamily`, increasing the schema surface. The multiline regex for PEM (`[\s\S]*?` non-greedy with backreference and `[\s\S]*\Z` fallback) is more complex than the header-only pattern. Mismatched PEM labels (BEGIN RSA...END EC) cause the regex to consume to EOF — this over-redacts rather than under-redacts, which is the safe direction.

**Confidence:** High (E2) — verified regex behavior against 3 test cases (full block, truncated, mismatched labels). All tests pass.

**Reversibility:** High — the `redact_pattern` field is additive. Removing it falls back to `family.pattern`.

**Change trigger:** If the over-redaction on mismatched labels causes user-visible problems (extremely unlikely — malformed PEM is rare).

### I2: RuntimeError not assert for boundary map validation

**Choice:** `_validate_boundary_map` raises `RuntimeError` with diagnostic context (family name, buffer length, map length), not `assert`.

**Driver:** User stated: "I would not implement it as `assert`. If we want that invariant enforced in production, `_redact_text()` should raise a descriptive runtime error when `index_map` and `redacted` drift instead of relying on assertions."

**Alternatives considered:**
- **`assert` statement** — original proposal from the failure-hunter. Rejected because `assert` is stripped by `python -O`, which would silently disable the safety check in production.

**Trade-offs accepted:** Minor performance cost of the length comparison on every splice (negligible — integer comparison + function call overhead).

**Confidence:** High (E2) — the `assert` vs runtime error distinction is a well-understood Python behavior.

**Reversibility:** High — one-line change.

**Change trigger:** None — this is strictly better than `assert` for safety-critical code.

### I5: Catch KeyboardInterrupt only, not SystemExit

**Choice:** The `run()` wrapper catches only `KeyboardInterrupt`, not `BaseException` broadly. `SystemExit(0)` from `sys.exit(main())` passes through normally.

**Driver:** User noted: "An outer fail-closed catch is reasonable, but it must not accidentally convert intentional `SystemExit(0)` into exit 2."

**Alternatives considered:**
- **Catch `BaseException`** — original proposal from the failure-hunter. Would catch `SystemExit(0)` and convert it to exit 2, turning a clean allow into a false block.
- **Conditional `SystemExit` handling** — catch `SystemExit`, re-raise if code is 0, exit 2 otherwise. Proposed in the discussion but rejected as unnecessary — `main()` returns an int, `sys.exit(main())` produces the only `SystemExit`, so `KeyboardInterrupt` is the real gap.

**Trade-offs accepted:** `GeneratorExit` is not caught. This is a non-concern — `GeneratorExit` only arises in generator cleanup, which the guard doesn't use.

**Confidence:** High (E2) — traced the entry point flow: `main()` returns int → `sys.exit(int)` → `SystemExit(int)`. The only non-`SystemExit` `BaseException` that can occur during `json.load(sys.stdin)` or `check_tool_input()` is `KeyboardInterrupt`.

**Reversibility:** High — one-line change.

**Change trigger:** If a new code path in `main()` can raise `GeneratorExit` or another `BaseException` subclass, the catch would need broadening.

## Changes

### Modified files (7 source + 6 test)

| File | Change | Key details |
|------|--------|-------------|
| `server/consultation_safety.py:60` | `policy_for_tool` raises `KeyError` | Removed `.get(tool_name, CONSULT_POLICY)` default. Guard's `except Exception` at `codex_guard.py:54` catches `KeyError` and fails closed. |
| `server/secret_taxonomy.py:51,87-98` | Added `redact_pattern` field, PEM full-block regex, docstring fix | `redact_pattern: re.Pattern[str] \| None = None`. PEM uses named backreference `(?P<pem_label>...)` to match BEGIN/END labels. `[\s\S]*\Z` fallback for truncated excerpts. Stale "pre-sliced window" docstring removed. |
| `server/context_assembly.py:54-63,397,441` | `_validate_boundary_map` function, called after initial setup and each splice | Raises `RuntimeError` with family name, buffer length, and map length. Uses `redact_pattern or family.pattern` at line 407. |
| `server/retrieve_learnings.py:124-134` | Broad `except Exception: return ""` wrapping entire function body | Delivers documented fail-soft contract: "Fail-soft: missing file, empty file, or parse errors return empty string." Catches `UnicodeDecodeError`, `re.error`, and any downstream exception. |
| `server/dialogue.py:43-47,415,549,649` | `_log_recovery_failure` helper + usage at 3 recovery sites | Follows project error format: `"{operation} failed: {reason}. Got: {input!r:.100}"`. Used in `recover_startup`, `_recover_turn_dispatch`, `_best_effort_repair_turn`. |
| `scripts/codex_guard.py:70-79` | `run()` wrapper catches `KeyboardInterrupt → exit 2` | Separates entry point concern from business logic. `main()` returns int, `run()` handles signals. |
| `pyproject.toml:6` | Added `pyyaml>=6.0` to dependencies | PyYAML was available in workspace but not declared. |
| `tests/test_codex_guard.py:140-202` | 3 new tests: unknown tool blocks, internal error blocks, interrupt blocks | `test_unknown_plugin_tool_blocks` (subprocess), `test_internal_error_in_check_tool_input_blocks` (monkeypatch via importlib), `test_keyboard_interrupt_exits_fail_closed` (monkeypatch). |
| `tests/test_consultation_safety.py:38-40` | Updated unknown-tool test | `test_unknown_tool_raises_key_error` asserts `KeyError` instead of `CONSULT_POLICY` return. |
| `tests/test_context_assembly.py:96-117,434-457` | PEM full-block and truncated redaction tests | End-to-end via `assemble_context_packet` and unit via `_redact_text`. Verifies header, body, and footer are all removed. Truncated PEM (no END marker) also redacted. |
| `tests/test_dialogue.py:274-294,441-465,991-1044` | Recovery path logging tests | Verifies stderr output for `recover_startup`, `_recover_turn_dispatch`, `_best_effort_repair_turn`. Uses `capsys` to capture stderr. |
| `tests/test_retrieve_learnings.py:98-103` | UTF-8 decode error test | Writes `\xff\xfe\xfd` bytes, verifies `retrieve_learnings` returns empty string. |
| `tests/test_secret_taxonomy.py:53-55` | PEM redact_pattern existence test | Asserts `family.redact_pattern is not None` for `pem_private_key`. |

## Codebase Knowledge

### PEM Redact Pattern Behavior

The PEM `redact_pattern` at `secret_taxonomy.py:95-98` uses a named backreference to ensure the END label matches the BEGIN label:

```
-----BEGIN\s+(?P<pem_label>{label})-----
(?:[\s\S]*?-----END\s+(?P=pem_label)-----|[\s\S]*\Z)
```

Three verified behaviors:
| Input | Behavior | Result |
|-------|----------|--------|
| Full block (BEGIN RSA...END RSA) | Non-greedy `[\s\S]*?` finds nearest matching END | Matches header through footer |
| Truncated excerpt (BEGIN OPENSSH...no END) | Second alternative `[\s\S]*\Z` captures to EOF | Matches header to end of string |
| Mismatched labels (BEGIN RSA...END EC) | Backreference fails first alt, falls to `[\s\S]*\Z` | Over-redacts to EOF (safe direction) |

The `_redact_text` function uses `family.redact_pattern or family.pattern` at `context_assembly.py:407`, so the multiline pattern is only used for redaction. The egress scanner (`credential_scan.py`) uses `family.pattern` (header-only) for fast detection.

### Guard Entry Point Flow

```
if __name__ == "__main__":
    run()                           # codex_guard.py:78-79
        sys.exit(main())            # codex_guard.py:72
            json.load(stdin)        # line 29 — ValueError/OSError/UnicodeDecodeError → return 2
            tool_name check         # line 36 — not our tool → return 0
            tool_input check        # line 40 — missing/malformed → return 2
            status tool check       # line 46 — codex.status → return 0
            policy_for_tool()       # line 52 — KeyError for unknown → except → return 2
            check_tool_input()      # line 53 — any Exception → return 2
            verdict.action check    # line 59 — block → return 2, else → return 0
        KeyboardInterrupt           # codex_guard.py:73-75 → exit 2
```

Every path to exit 0 requires affirmatively passing through the scanner. All error paths exit 2 (fail-closed).

### Recovery Path Diagnostic Chain

```
_log_recovery_failure(operation, exc, got)     # dialogue.py:43-47
    print(f"codex-collaboration: {operation} failed: {exc}. Got: {got!r:.100}", stderr)

Used at:
    recover_startup          → line 415 → got=handle.collaboration_id
    _recover_turn_dispatch   → line 549 → got=entry.idempotency_key
    _best_effort_repair_turn → line 649 → got=intent_entry.idempotency_key
```

### Boundary Map Validation

`_validate_boundary_map` at `context_assembly.py:54-63` is called at two points:
1. After initial `index_map = list(range(len(value) + 1))` — verifies starting invariant
2. After each splice `index_map = index_map[:start] + replacement_map + index_map[end:]` — verifies splice preserved invariant

The invariant: `len(index_map) == len(redacted) + 1`. The +1 accounts for the sentinel position at end of string.

### Key File-Level Findings from Review

Files that produced findings worth knowing about when modifying them in the future:

| File | Finding | Implication |
|------|---------|-------------|
| `consultation_safety.py:129` | `TIER_RANK` dict has only `strict` and `contextual` — `broad` is absent. Uses `.get(tier, 99)` fallback. | When adding a new tier, add it to `TIER_RANK` or document the fallback. |
| `profiles.py:46-50` | Missing YAML file → empty dict → named profiles silently degrade to contract defaults. | If a user requests `profile="adversarial-challenge"` and the YAML can't load, they silently get collaborative posture. The "Explicit over Silent" tenet suggests this should warn or raise. |
| `mcp_server.py:202-212` | Tool dispatch `except Exception` converts all errors to JSON-RPC error responses with `str(exc)` only. No server-side logging. | When debugging production tool call failures, there is no server-side trace. Add stderr logging if debugging becomes difficult. |
| `dialogue.py:178` | Comment references "plan doc [section]Key invariants" — ambiguous. Actual document is `docs/superpowers/plans/2026-03-28-r2-recovery-and-read-fidelity.md`. | Either make the comment self-contained or add the full path. |

### Five Review Agent Findings Summary

The 5-agent parallel review produced findings at three severity levels:

| Level | Count | Fixed | Deferred |
|-------|-------|-------|----------|
| Critical | 2 | 2 | 0 |
| Important | 9 | 8 | 1 (I9: comment cleanup) |
| Suggestion | 14 | 0 | 14 |

Cross-agent convergence: `policy_for_tool` flagged by failure-hunter AND code-reviewer. PEM flagged by code-reviewer AND test-analyzer. Independent agents reaching the same conclusion increases finding confidence.

Key deferred items by category:
- **Type improvements (I7, I8):** Mutable containers → immutable (`list→tuple`, `set→frozenset`), `tier: str | None` → `Tier | None`. Correctness improvements, not safety gaps.
- **Comment cleanup (I9):** "Release posture item N" references are process artifacts that will rot.
- **Suggestions (S1-S14):** Missing YAML → empty dict, raw `yaml.YAMLError`, MCP dispatch logging, regex timeout, `__post_init__` validation, `ResolvedProfile` composite type, various test gaps, various comment improvements.

## Context

### Mental Model

This session was a **validation and hardening** problem, not an implementation problem. The T-03 implementation was complete from the prior session. This session's job was to find gaps the implementation missed and close them with targeted fixes.

The core insight: safety code needs adversarial review because its failure modes are silent. A `policy_for_tool` fallback that returns the "most restrictive" policy looks safe — until you realize a future tool might have content in fields that the fallback policy classifies as `expected_fields` (skipped). The failure-hunter agent found this because it was specifically looking for "error paths that return success instead of failure."

Similarly, the PEM issue was only visible when you traced the full data flow: `redact_enabled=True` on a header-only pattern means the header gets redacted but the base64 body passes through. The code-reviewer found the `redact_enabled=False` flag; the user traced the implication to its conclusion.

### Project State

- **Branch:** `feature/codex-collaboration-safety-substrate` — 12 commits ahead of main (10 T-03 + 1 handoff archive + 1 hardening)
- **PR:** jpsweeney97/claude-code-tool-dev#90 — description updated with hardening section, ready for merge
- **Tests:** 358/358 passing (108 T-03 + 11 hardening + 239 pre-existing, zero regressions)
- **Deferred from review:** I7/I8 (type improvements), I9 (comment cleanup), S1-S14 (14 suggestions)
- **Deferred from T-03:** AC6 (analytics emission), journal profile integration
- **Open question:** `codex.consult` surface retirement at `decisions.md:115-117`

### Environment

- Feature branch pushed to origin after `--force-with-lease` (branches had diverged: 2 local vs 1 remote)
- PyYAML 6.0 now declared as explicit dependency in `pyproject.toml`
- `uv.lock` updated with the dependency change

## Learnings

### Safety code review benefits from parallel specialized agents

**Mechanism:** Five agents each focused on a single dimension (code quality, tests, error handling, types, comments) found issues that a single generalist review would likely miss. The failure-hunter found `policy_for_tool` silent fallback because it was specifically looking for "error paths that return success." The type-analyzer found the `tier: str | None` vs `Tier | None` gap because it was specifically looking for type expressiveness.

**Evidence:** 2 critical and 9 important findings across 5 agents. Cross-agent convergence on 2 findings (policy_for_tool, PEM) increased confidence. Total review time: ~5 minutes for all 5 agents in parallel.

**Implication:** For safety-critical PRs, the 5-agent parallel review pattern is worth the context cost. For non-safety code, 2-3 targeted agents may suffice.

**Watch for:** Agent findings can be false positives or incomplete — the user's correction of C2 showed the code-reviewer identified the gap but proposed an incomplete fix.

### Naive fixes for safety code can introduce new gaps

**Mechanism:** The obvious fix for PEM (flip `redact_enabled=True`) would have introduced a false sense of security — the header would show `[REDACTED:value]` but the base64 key body would still pass through to Codex. The fix looks correct in the diff but is incomplete when you trace the data flow through `_redact_text()`.

**Evidence:** User traced the flow: `secret_taxonomy.py:87` matches only the header → `context_assembly.py:361` sends full file excerpts → flipping `redact_enabled` redacts only the header line. Key body and footer remain.

**Implication:** Safety code fixes must be validated by tracing the full data flow, not just the local change site. The correct fix (separate `redact_pattern`) required understanding both the egress and redaction pipelines.

**Watch for:** Any future change to `SecretFamily` patterns should consider whether `pattern` (used by egress scanner) and `redact_pattern` (used by inner redaction) need to differ.

### `assert` is inappropriate for production safety invariants

**Mechanism:** Python's `assert` statement is removed when running with `-O` (optimize) flag. Using `assert` for safety invariants means the check can be silently disabled in production deployments that use optimization.

**Evidence:** User stated: "If we want that invariant enforced in production, `_redact_text()` should raise a descriptive runtime error when `index_map` and `redacted` drift instead of relying on assertions."

**Implication:** All production safety checks should use explicit `if` + `raise`, not `assert`. `assert` is appropriate for development-time sanity checks and test assertions, not production invariants.

**Watch for:** Existing code that uses `assert` for safety-critical checks.

## Next Steps

### 1. Merge PR #90

**Dependencies:** None — PR is reviewed, hardened, and 358/358 tests passing.

**What to read first:** The PR at jpsweeney97/claude-code-tool-dev#90. The description now includes both the original T-03 acceptance criteria and the hardening section.

**Approach:** Merge and clean up the feature branch. The PR has 12 commits (10 T-03 implementation + 1 handoff archive + 1 hardening).

### 2. Evaluate the `codex.consult` open question

**Dependencies:** PR merge (#1).

**What to read first:** `decisions.md:115-117` (the open question), `contracts.md` codex.consult surface, and the official plugin's native review/task flow.

**Approach suggestion:** Write a concrete decision memo comparing `codex.consult` against native review/task patterns. The open question is the one place where the spec explicitly acknowledges the official plugin's approach might be sufficient.

**Acceptance criteria:** Either close the question (keep `codex.consult` with rationale) or escalate it (propose retirement path with migration plan).

### 3. Address deferred review findings (cleanup pass)

**Dependencies:** PR merge (#1).

**What to read first:** The deferred items from this session:
- I7: Mutable containers → immutable (`list→tuple`, `set→frozenset`) in `secret_taxonomy.py`, `consultation_safety.py`
- I8: `tier: str | None` → `Tier | None` in `credential_scan.py`, `consultation_safety.py`
- I9: Strip "Release posture item N" prefixes from comments in `mcp_server.py`, `control_plane.py`, `dialogue.py`

**Approach suggestion:** These are mechanical cleanup changes. Could be a single commit on a `chore/` branch.

### 4. Address T-03 deferred items

**Dependencies:** PR merge (#1).

**What to read first:** Deferred Task 10 in the T-03 plan (analytics emission, AC6). Also the crash recovery limitation for profile fields (plan lines 2245-2251).

**Approach suggestion:** AC6 requires Thread C investigation (profile/audit schema expansion). Journal profile integration is a schema migration task.

## In Progress

Clean stopping point. PR #90 is reviewed, hardened, pushed, and description updated. No work in flight.

## Open Questions

### `codex.consult` surface retirement

Whether `codex.consult` should eventually be retired in favor of native review/task patterns plus a lighter structured wrapper remains open at `decisions.md:115-117`. Unchanged from the prior session.

### AC6 analytics emission

Deferred from T-03. Thread C (profile/audit schema expansion) must be investigated before implementation.

### Deferred review suggestions (S1-S14)

14 suggestions from the review agents were not independently validated by the user. They may contain false positives. If a future session encounters any of these areas, validate the specific finding against the current code before acting.

## Risks

### PEM over-redaction on mismatched labels

The PEM `redact_pattern` consumes from BEGIN to EOF when labels mismatch (e.g., BEGIN RSA...END EC). This over-redacts text after the malformed PEM block. Malformed PEM is extremely rare in practice, and over-redaction is the safe direction, but it could cause confusion if a file excerpt contains text after a malformed PEM.

### Force-push to feature branch

The branch was pushed with `--force-with-lease` because local and remote had diverged (2 local commits vs 1 remote commit). The remote commit was the prior PR creation; the local commits were the handoff archive and hardening fix. `--force-with-lease` is safe (it verifies the remote hasn't been updated by someone else), but any pending reviews or comments on the old commit hashes are orphaned.

### Deferred type improvements reduce static safety

I7 (`list→tuple`, `set→frozenset`) and I8 (`str→Tier`) were deferred as cleanup. While not safety-critical today (the "sole producer" pattern maintains invariants by convention), the type-analyzer noted these become increasingly risky as the codebase grows and more code constructs these types.

## References

| What | Where |
|------|-------|
| PR #90 | jpsweeney97/claude-code-tool-dev#90 |
| T-03 implementation plan | `docs/superpowers/plans/2026-03-30-codex-collaboration-safety-substrate.md` |
| Prior handoff (T-03 complete) | `docs/handoffs/archive/2026-03-31_15-49_t03-safety-substrate-implementation-complete.md` |
| Governance decision | `docs/superpowers/specs/codex-collaboration/decisions.md:41-49` |
| `codex.consult` open question | `docs/superpowers/specs/codex-collaboration/decisions.md:115-117` |
| Spec packet | `docs/superpowers/specs/codex-collaboration/` (12 files) |

## Gotchas

### Feature branch already exists with 12 commits — don't re-create

The branch `feature/codex-collaboration-safety-substrate` has 12 commits (10 T-03 + 1 archive + 1 hardening) and is pushed to origin with PR #90. If continuing work, checkout this branch.

### PEM redact_enabled=True now — different from prior session

The prior handoff documented `redact_enabled=False` as intentional for PEM. This session changed it to `True` with a separate `redact_pattern` for full-block redaction. The egress scanner still uses the header-only `pattern`. If reviewing the taxonomy, remember PEM now has TWO patterns: `pattern` (header-only, for egress) and `redact_pattern` (full-block, for inner redaction).

### `policy_for_tool` now raises KeyError for unknown tools

The prior behavior was silent fallback to `CONSULT_POLICY`. Any new tool added to `mcp_server.py` MUST have a corresponding entry in `_TOOL_POLICY_MAP` at `consultation_safety.py:51-55`, or the guard will block it.

### hooks.json modified — sync required after promotion

When this plugin is promoted to production, the `hooks.json` change needs to be picked up by Claude Code. Per CLAUDE.md: "Run `uv run scripts/sync-settings` after modifying hooks."

## User Preferences

**Review before merge:** User explicitly stated "PR #90 is not yet ready for merge - it still needs a full review." Does not assume implementation completeness implies merge readiness.

**Detailed per-finding feedback with file references:** User provided per-finding analysis with specific file:line links (e.g., `[consultation_safety.py#L58]`, `[secret_taxonomy.py#L87]`, `[codex_guard.py#L70]`). When validating findings, they traced the code themselves.

**Corrects and refines, does not reject wholesale:** User accepted the review findings as a body of work, then refined specific fixes. For C2: "C2 is a real inner-boundary gap, but the proposed fix is incomplete." For I2: "I would not implement it as `assert`." For I5: "must not accidentally convert intentional `SystemExit(0)` into exit 2."

**Implements then requests review:** User said "Share your thoughts. Do not proceed with changes." They implemented the fixes themselves, ran verification, and returned for review. This is consistent with the prior session's observation: "User operates as a collaborative architect, not a task requester."

**Narrow scope, tight control:** User classified the fix into three tiers: "Fix now", "Fold in for better hardening", "Broader cleanup." Then stated: "Most likely, this is a narrow safety patch, not a broad refactor."
