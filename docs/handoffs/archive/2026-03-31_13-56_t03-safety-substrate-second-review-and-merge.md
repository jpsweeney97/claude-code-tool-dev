---
date: 2026-03-31
time: "13:56"
created_at: "2026-03-31T17:56:37Z"
session_id: 7dc5e002-5a24-4aa1-931e-ce6c34df03ef
resumed_from: /Users/jp/Projects/active/claude-code-tool-dev/docs/handoffs/archive/2026-03-31_13-04_t03-safety-substrate-pr-review-and-hardening.md
project: claude-code-tool-dev
branch: main
commit: 43fa3ba5
title: "T-03 safety substrate second review and merge"
type: handoff
files:
  - packages/plugins/codex-collaboration/server/dialogue.py
  - packages/plugins/codex-collaboration/server/profiles.py
  - packages/plugins/codex-collaboration/server/consultation_safety.py
  - packages/plugins/codex-collaboration/server/credential_scan.py
  - packages/plugins/codex-collaboration/server/secret_taxonomy.py
  - packages/plugins/codex-collaboration/server/mcp_server.py
  - packages/plugins/codex-collaboration/server/control_plane.py
  - packages/plugins/codex-collaboration/server/jsonrpc_client.py
  - packages/plugins/codex-collaboration/server/context_assembly.py
  - packages/plugins/codex-collaboration/scripts/codex_guard.py
  - packages/plugins/codex-collaboration/references/consultation-profiles.yaml
  - packages/plugins/codex-collaboration/tests/test_dialogue.py
  - packages/plugins/codex-collaboration/tests/test_profiles.py
  - packages/plugins/codex-collaboration/tests/test_consultation_safety.py
  - packages/plugins/codex-collaboration/tests/test_secret_taxonomy.py
---

# T-03 safety substrate second review and merge

## Goal

Conduct a second comprehensive PR review of PR #90 (T-03 safety substrate), fix all critical and important findings, and land the PR on main via squash merge. The prior session completed a first review pass and 8 hardening fixes. The user stated PR #90 was not yet ready for merge and required a second review before landing.

**Trigger:** User loaded the prior session's handoff and requested a second review pass: "PR #90 needs a second review pass /pr-review-toolkit:review-pr".

**Stakes:** Safety-critical code — credential scanning, tool-input safety policy, consultation profiles, learning retrieval. The first review found 2C/9I/14S; the user's instinct was that a second pass would find more, particularly in code paths the first pass didn't scrutinize deeply.

**Success criteria:** All new critical findings fixed, type-hardening cluster landed, docs/comments cleanup complete, PR squash-merged to main with clean branch reconciliation.

**Connection to project arc:** This session closes T-03 entirely. The prior session implemented T-03 (10 commits). The session before that reviewed and hardened it (8 fixes). This session performed the second review, fixed 3 more slices, and landed the squash merge. Next: evaluate the `codex.consult` open question or address T-03 deferred items (AC6 analytics, persistence replay hardening).

## Session Narrative

Session began by loading the prior handoff (`2026-03-31_13-04_t03-safety-substrate-pr-review-and-hardening.md`). The handoff described the first review pass as complete with 8 hardening fixes and PR #90 pushed. Next steps listed: (1) merge PR #90, (2) evaluate `codex.consult` open question, (3) address deferred review findings.

The user immediately redirected: "PR #90 needs a second review pass" and invoked the PR review toolkit. This set the session's character: a second adversarial review of already-reviewed code, followed by structured fix-and-merge execution.

Gathered PR scope: 33 files changed, +3342/-97 lines. All 5 review aspects applicable due to safety-critical nature. Launched all 5 specialized review agents in parallel:

| Agent | Focus | Duration | Findings |
|-------|-------|----------|----------|
| test-analyzer | Coverage quality | ~2.5 min | 0C, 4I, 5S |
| type-analyzer | Type design, invariants | ~2.5 min | 0C, 6I, 5S |
| failure-hunter | Silent failures, error handling | ~3.5 min | 2C, 5I, 3S |
| comment-analyzer | Comment accuracy, rot | ~3.5 min | 2C, 4I, 3S |
| code-reviewer | Bugs, security, conventions | ~5.5 min | 0C, 2I, 0S |

Results arrived over ~5 minutes. The aggregated report identified 4 critical, 14 important, and 16 suggestion-level findings — more than the first pass (2C/9I/14S) despite running on already-reviewed code. This validated the user's instinct that a second pass was needed.

**Key new finding — CRITICAL-1:** The failure-hunter found a data integrity hole in `_recover_thread_creation` at `dialogue.py:467-510`. A dispatched `thread_creation` entry with `codex_thread_id is None` was silently marked "completed", leaving an orphaned Codex thread and a handle pointing at a null thread ID. This was in pre-existing recovery code that the first pass didn't scrutinize deeply because the focus was on new T-03 additions.

**User corrected I1:** The failure-hunter reported that `mcp_server.py:202` catches `KeyboardInterrupt/SystemExit` via `except Exception`. The user correctly identified this as wrong: "`mcp_server.py` catches `Exception`, so it does not swallow `KeyboardInterrupt` or `SystemExit`; I1 should be dropped." In Python 3, `except Exception` does not catch `BaseException` subclasses.

The user then provided structured triage with ranked hypotheses, evidence requirements, and tests. They proposed three options:
- A: Fix C1 and C2 first, then re-evaluate
- B: Broader "runtime integrity" pass including persistence replay
- C: Fast cleanup sweep first

User recommended A: "Fix C1 and C2 first, then re-evaluate the remaining list." They grouped the remaining findings into coherent clusters: type-hardening (I6/I7/D1/I8), docs/comments (C3/C4/I12/I13/I14), and persistence replay (I2/I3/I4 — deferred).

The user implemented C1 and C2 fixes themselves, ran verification (targeted tests + full suite at 359 passed + ruff clean), then returned for review. I reviewed the fixes by reading the changed code:
- C1: `_recover_thread_creation` now raises `RuntimeError` when `codex_thread_id is None` in dispatched phase, leaving the journal entry unresolved
- C2: `resolve_profile` raises `ProfileValidationError` for unknown names instead of silent fallback

User approved with "No findings" and specified the next slice: type-hardening cluster.

I implemented the type-hardening cluster: `set` → `frozenset` on `ToolScanPolicy` fields, `list` → `tuple` on `SafetyVerdict.unexpected_fields` and `SecretFamily.placeholder_bypass`, `str` → `Tier` on `SafetyVerdict.tier` and `ScanResult.tier`. Updated test assertions. 359/359 passing.

User reviewed with "No findings" and confirmed the changes were behavior-preserving with the mutability hole closed.

I implemented the docs/comments cleanup: "Shadow telemetry only" → "Telemetry not yet wired", dead design doc reference removed, 6 "Release posture item N" comments replaced with self-contained `INVARIANT:` annotations, backslash escaping fixed, process artifact trimmed, codex_guard docstring clarified.

User reviewed with "No findings."

User specified three separate commits with explicit messages and ordering rationale:
1. `fix(codex-collaboration): harden thread recovery and reject unknown profiles` — behavioral changes get their own rollback boundary
2. `refactor(codex-collaboration): freeze safety policy and tier types` — behavior-preserving, easier to validate separately
3. `docs(codex-collaboration): replace posture references and clean stale comments` — pure clarity changes, zero runtime effect

I committed in that order, grouping overlapping files by their dominant slice. User then specified the squash-merge landing strategy with detailed rationale: 16 commits ahead of main, squash is the clean landing because the branch shape (many small task commits) isn't optimal for main's readability. Recommended sequence: `gh pr merge 90 --squash`, `git fetch origin`, `git branch -f main origin/main`, `git switch main`, `git branch -d feature/...`.

I executed the full merge and cleanup sequence. PR #90 squash-merged at `43fa3ba5`, local main reconciled, feature branch deleted.

## Decisions

### Fix C1 and C2 first, then re-evaluate (Option A)

**Choice:** Address the two new critical findings first as a standalone slice, then decide on the remaining clusters.

**Driver:** User stated: "I would not treat this as a single patch. The findings split into one real integrity bug, one clear configuration bug, one type-hardening cluster, and a docs/comment cleanup cluster." And: "Fix C1 and C2 first, then re-evaluate the remaining list."

**Alternatives considered:**
- **Option B: Broader runtime integrity pass** — include C1, C2, I2, I3, I4, I5 (persistence replay issues). Rejected by user: "I2, I3, and I4 expand scope into storage repair semantics" and "I5 is a design decision, not an automatic fix."
- **Option C: Fast cleanup sweep first** — land docs/comments/types before touching recovery behavior. Not proposed by user.

**Trade-offs accepted:** I2/I3/I4 (JSONL replay hardening) deferred. These are real reliability concerns but predate T-03 and would expand scope.

**Confidence:** High (E2) — user independently validated each finding against the code before accepting or rejecting.

**Reversibility:** High — each fix is isolated and well-tested.

**Change trigger:** If persistence replay issues (I2/I3/I4) cause production incidents, they'd be promoted from deferred to a dedicated `fix/persistence-replay-hardening` branch.

### Three separate commits by slice type

**Choice:** Three commits in order: fix (runtime behavior), refactor (type hardening), docs (comment cleanup).

**Driver:** User stated: "That gives the cleanest history for this second pass because the slices are actually independent in risk and intent." And: "The first pass being a single hardening commit is not a good reason to collapse this one. This pass already has clearer slice boundaries."

**Alternatives considered:**
- **Single combined commit** — like the first review pass. Rejected by user because "separate commits improve review, bisecting, and revert safety."

**Trade-offs accepted:** Minor file overlap — some files have changes from multiple slices (dialogue.py has C1 fix + INVARIANT comment; consultation_safety.py has type changes + comment trim). Grouped by dominant change since interactive staging wasn't available.

**Confidence:** High (E2) — standard git hygiene practice, well-understood tradeoffs.

**Reversibility:** N/A — commit organization, not functional decision.

**Change trigger:** None — this is a process preference, not a technical tradeoff.

### Squash merge for PR landing

**Choice:** Squash-merge PR #90's 16 commits into one commit on main, rather than merge commit or rebase.

**Driver:** User stated: "Main should optimize for readability and revertability, not preserve every task checkpoint." And: "If you wanted preserved history on main, the right version of that would have been rebasing into a very small set of logical commits first. Given the branch shape now, squash is the clean landing."

**Alternatives considered:**
- **Regular merge** — preserves all commits. Rejected: "One thing not to do: regular-merge this branch as-is."
- **Rebase then merge** — clean history but requires rewriting 16 commits into logical groups. Not proposed — user considered squash sufficient.

**Trade-offs accepted:** Individual commit history lost on main. The feature branch commits are preserved in the GitHub PR for archaeology.

**Confidence:** High (E2) — this repo has already used squash merges for similar long-lived feature branches.

**Reversibility:** Low — squash merge is a one-way operation. But reverting the squash commit is a single `git revert`.

**Change trigger:** If the team adopts trunk-based development or requires per-commit CI, squash merges would need to be reconsidered.

### Drop I1 (MCP catches BaseException)

**Choice:** Drop the failure-hunter's finding that `mcp_server.py:202` catches `KeyboardInterrupt/SystemExit`.

**Driver:** User stated: "`mcp_server.py` catches `Exception`, so it does not swallow `KeyboardInterrupt` or `SystemExit`; I1 should be dropped." In Python 3, `except Exception` does not catch `BaseException` subclasses (`KeyboardInterrupt`, `SystemExit`, `GeneratorExit`).

**Alternatives considered:**
- **Fix as reported** — change to `except (KeyboardInterrupt, SystemExit): raise` before the catch. Rejected because unnecessary — `except Exception` already excludes these.

**Trade-offs accepted:** None — the finding was factually incorrect.

**Confidence:** High (E3) — Python language specification. `BaseException` hierarchy is well-documented: `Exception` is a subclass of `BaseException`, and `KeyboardInterrupt`/`SystemExit` are direct `BaseException` subclasses, not `Exception` subclasses.

**Reversibility:** N/A — no change made.

**Change trigger:** None — this is a language fact, not a design decision.

## Changes

### Modified files (10 source + 5 test, landed as squash commit `43fa3ba5`)

| File | Change | Key details |
|------|--------|-------------|
| `server/dialogue.py:469-473` | C1: Recovery integrity — raises `RuntimeError` for dispatched thread_creation with null thread ID | Replaces silent "completed" marking. Leaves journal entry unresolved. Error format: `"Recovery integrity failure: no codex_thread_id in thread_creation entry. Got: idempotency_key={...!r:.100}"` |
| `server/dialogue.py:304-306` | I12: INVARIANT comment replaces "Release posture item 4" | Self-contained constraint: "minimal audit schema covers consult/dialogue_turn only" |
| `server/profiles.py:80-84` | C2: Unknown profile name raises `ProfileValidationError` | `profile_name not in profiles` → raise. Error format matches project convention. |
| `references/consultation-profiles.yaml:10` | C2+C4: Updated contract comment + removed dead design doc reference | "Unknown profile names are rejected during resolution." Dead ref: `docs/plans/2026-03-03-posture-taxonomy-and-composition.md` |
| `server/consultation_safety.py:23-24` | I6: `ToolScanPolicy` fields `set` → `frozenset` | Prevents `.add()` mutation on module-scope policy singletons |
| `server/consultation_safety.py:139-140` | I7+D1: `SafetyVerdict` — `list` → `tuple`, `str` → `Tier` | `unexpected_fields: tuple[str, ...] = ()`, `tier: Tier \| None = None` |
| `server/consultation_safety.py:32-50` | I6: Policy singletons use `frozenset({...})` | CONSULT_POLICY, DIALOGUE_START_POLICY, DIALOGUE_REPLY_POLICY |
| `server/consultation_safety.py:46-47` | I14: Process artifact trimmed from DIALOGUE_REPLY_POLICY comment | "forward-looking fields removed to match the real tool surface" → removed |
| `server/credential_scan.py:25-26,30` | D1: `ScanResult.tier` → `Tier \| None`, `_families_for_tier` fully typed | Import `Tier` and `SecretFamily` from `secret_taxonomy` |
| `server/credential_scan.py:6` | C3: "Shadow telemetry only" → "Telemetry not yet wired" | Matches actual behavior — shadow verdicts are never consumed |
| `server/secret_taxonomy.py:47` | I7: `SecretFamily.placeholder_bypass` → `tuple[str, ...]` | All `list(PLACEHOLDER_BYPASS_WORDS)` → `tuple(...)`, all `[]` → `()` |
| `server/secret_taxonomy.py:9` | C3: "Shadow telemetry only" → "Telemetry not yet wired" | Same as credential_scan.py |
| `server/mcp_server.py:217-219` | I12: INVARIANT comment replaces "Release posture item 3" | "safe only while this is the sole serialized dispatch chokepoint" |
| `server/control_plane.py:133,189,272` | I12: Three INVARIANT comments replace "Release posture item" 1, 4, 5 | Each states its architectural constraint directly |
| `server/jsonrpc_client.py:122-124` | I12: INVARIANT comment replaces "Release posture item 2" | "explicit close is the lifecycle boundary" |
| `server/context_assembly.py:389` | I13: Fixed backslash escaping in `_redact_text` docstring | `r"\\1[REDACTED:value]\\3"` → `r"\1[REDACTED:value]\3"` |
| `scripts/codex_guard.py:4` | I13: Clarified stdin payload description | "Reads JSON from stdin with {tool_name, tool_input}" → "Reads JSON from stdin (PreToolUse hook payload). Uses tool_name and tool_input fields." |
| `tests/test_dialogue.py:362-389` | C1 regression test | Seeds dispatched thread_creation with no thread ID, asserts RuntimeError, verifies entry stays unresolved |
| `tests/test_profiles.py:44-46` | C2 test update | `test_unknown_profile_returns_defaults` → `test_unknown_profile_raises` |
| `tests/test_consultation_safety.py` | I6: All `set()` → `frozenset()`, `== []` → `== ()` | Policy constructors and assertions updated |
| `tests/test_secret_taxonomy.py:35` | I7: `placeholder_bypass == []` → `== ()` | Strict family bypass assertion |

## Codebase Knowledge

### Second Review Pass: Agent Cross-Convergence

Multiple agents independently converged on the same issues, increasing confidence:

| Finding | Agents converging | Convergence signal |
|---------|-------------------|--------------------|
| Unknown profile → silent defaults | failure-hunter (Critical), type-analyzer (F4) | Error handling vs type constraints — different angles |
| Mutable containers on frozen safety types | type-analyzer (F2/F3), first-pass deferred I7 | F2 elevated: policy singletons specifically |
| `retrieve_learnings` broad except | failure-hunter, test-analyzer, comment-analyzer | Three agents from three perspectives |

### Recovery Flow Architecture

```
recover_pending_operations()                     # dialogue.py:430
    for entry in journal.list_unresolved():
        if entry.operation == "thread_creation":
            _recover_thread_creation(entry)      # dialogue.py:446
                if phase == "intent":
                    → write "completed" (no-op)
                if phase == "dispatched":
                    if codex_thread_id is None:
                        → raise RuntimeError     # NEW (C1 fix)
                    else:
                        → reattach via read/resume
                        → persist or update handle
        elif entry.operation == "turn_dispatch":
            _recover_turn_dispatch(entry)        # dialogue.py:519
```

### Profile Resolution Flow

```
resolve_profile(profile_name="deep-review")      # profiles.py:67
    load_profiles()                               # profiles.py:39
        → YAML load from consultation-profiles.yaml
        → optional local override merge
    if profile_name not in profiles:
        → raise ProfileValidationError            # NEW (C2 fix)
    profile = profiles[profile_name]
    → validate no phased profiles
    → validate no sandbox widening
    → validate no approval widening
    → apply explicit overrides
    → return ResolvedProfile(frozen=True)
```

### Frozen Dataclass Mutability Hierarchy

After type hardening, the safety types have this immutability profile:

| Type | `frozen=True` | Fields immutable | Truly immutable |
|------|---------------|------------------|-----------------|
| `ToolScanPolicy` | Yes | `frozenset` fields | Yes |
| `SafetyVerdict` | Yes | `tuple`, `Tier` | Yes |
| `SecretFamily` | Yes | `tuple` (bypass) | Yes |
| `ScanResult` | Yes | `Tier` | Yes |
| `AdvisoryRuntimeState` | **No** | Mixed mutable | No (by design) |
| `ResolvedProfile` | Yes | `str` fields | Shallow only (stringly-typed) |

### Key File-Level Findings from Second Review

Files that produced findings worth knowing about when modifying them in the future:

| File | Finding | Implication |
|------|---------|-------------|
| `profiles.py:46-50` | YAML `safe_load` can return non-dict types | `data.get("profiles", {})` assumes dict. Malformed YAML crashes with `AttributeError`. |
| `dialogue.py:322-332` | Parse error wrapping catches `(ValueError, AttributeError)` but not `TypeError` | `json.loads(None)` raises `TypeError`, escaping the catch block |
| `lineage_store.py:110-127` | `_apply_record` silently drops unknown operations | Future operation types from newer server version lost during rollback |
| `turn_store.py:70-71` | Missing key in one JSONL record crashes entire replay | `record['collaboration_id']` KeyError propagates, taking down all reads |
| `retrieve_learnings.py:133-134` | Broad `except Exception` covers both I/O errors (expected) and processing bugs (unexpected) | Coding bugs in `parse_learnings`/`filter_by_relevance` silently return empty string |

### Full Review Agent Findings Summary (Second Pass)

| Level | Count | Fixed | Deferred |
|-------|-------|-------|----------|
| Critical | 4 | 4 (C1, C2, C3, C4) | 0 |
| Important | 14 | 10 (I6-I14, D1) | 4 (I2-I5: persistence replay) |
| Suggestion | 16 | 0 | 16 |

## Context

### Mental Model

This session was a **validation-and-merge** problem. The core insight: a second review pass found *more* findings (4C/14I/16S) than the first pass (2C/9I/14S) despite running on already-reviewed code. Two factors explain this: (1) the hardening commit introduced new code that itself needed review, and (2) the first pass was scoped to "find the worst things" while the second pass had the luxury of deeper scrutiny.

The most important new finding (C1: recovery data integrity) was in pre-existing recovery code that the first pass didn't examine deeply because the focus was on the new T-03 additions. This validates the user's instinct that safety code benefits from repeated adversarial review — each pass explores different corners of the same codebase.

### Project State

- **Branch:** `main` — T-03 landed at squash commit `43fa3ba5`
- **PR:** jpsweeney97/claude-code-tool-dev#90 — MERGED (squash) at 2026-03-31T17:53:33Z
- **Tests:** 359/359 passing (108 T-03 + 12 hardening + 239 pre-existing, zero regressions)
- **Feature branch:** `feature/codex-collaboration-safety-substrate` deleted (local and remote)

### Deferred Items

| Category | Items | Rationale |
|----------|-------|-----------|
| Persistence replay | I2 (turn_store KeyError), I3 (JSONL corrupt mid-file), I4 (lineage unknown ops) | Expands scope into storage repair semantics; better as dedicated `fix/persistence-replay-hardening` branch |
| Design decision | I5 (retrieve_learnings narrow except) | Changes documented fail-soft contract; needs deliberate design choice |
| Test gaps | T1-T4 from test-analyzer | Lower priority: extract_strings TypeError, unsupported value traversal, guard non-dict tool_input, bypass window boundary |
| Type improvements | F4 (stringly-typed ResolvedProfile), F6 (AdvisoryRuntimeState session: Any) | Moderate effort, not safety-critical |
| Suggestions | 16 across all agents | Not independently validated by user |
| AC6 | Analytics emission | Thread C checkpoint required |
| Open question | `codex.consult` surface retirement | `decisions.md:115-117` |

## Learnings

### Second review passes find different bugs than first passes

**Mechanism:** The first review pass optimizes for "find the worst things" — agents focus on the most obviously problematic patterns. The second pass, with the worst issues already fixed, goes deeper into less-obvious code paths. The recovery flow at `dialogue.py:467-510` was present in the first pass's diff but wasn't flagged because the agents focused on the new T-03 additions rather than pre-existing recovery logic.

**Evidence:** First pass: 2C/9I/14S. Second pass: 4C/14I/16S. The new C1 (recovery data integrity) was in code untouched by T-03 — it was reachable from T-03's recovery path but the agents had to follow the call chain deeper to find it.

**Implication:** For safety-critical PRs, budget for at least two review passes. The first pass catches obvious issues; the second catches the subtle ones that the first pass's fixes make visible.

**Watch for:** Diminishing returns on third+ passes. Two passes hit the sweet spot for this codebase size.

### `except Exception` does NOT catch `KeyboardInterrupt` or `SystemExit` in Python 3

**Mechanism:** Python 3's exception hierarchy: `BaseException` is the root. `Exception` and `KeyboardInterrupt`/`SystemExit` are direct subclasses of `BaseException`. `except Exception` only catches `Exception` and its subclasses — it explicitly excludes `KeyboardInterrupt`, `SystemExit`, and `GeneratorExit`.

**Evidence:** User corrected the failure-hunter's finding: "`mcp_server.py` catches `Exception`, so it does not swallow `KeyboardInterrupt` or `SystemExit`; I1 should be dropped."

**Implication:** When reviewing error handling, verify the catch type before flagging. `except Exception` is a reasonable catch-all for application errors that need to be converted to error responses, as long as you don't need to catch `BaseException` subclasses.

**Watch for:** Python 2 code or references — Python 2's `except Exception` behavior was different (before the `BaseException` hierarchy was introduced).

### Post-squash-merge reconciliation requires `git branch -f`, not `git pull --rebase`

**Mechanism:** After a squash merge, the squash commit's tree matches the feature branch tip, but its parent is the old main HEAD. The feature branch commits have no ancestor relationship to the squash commit. Running `git pull --rebase` would try to replay those commits on top of the squash — producing duplicate changes and conflicts. `git branch -f main origin/main` directly moves the ref pointer without replaying anything.

**Evidence:** User specified the reconciliation sequence: "Do not use `git pull --rebase`. Do not use `git reset --hard`. From any branch other than main, move the local main ref directly: `git branch -f main origin/main`."

**Implication:** For this repo (which uses squash merges), post-merge reconciliation should always use `git branch -f` rather than `git pull`.

**Watch for:** The `git branch -d` after reconciliation warns "not yet merged to HEAD" because git can't see the squash as a merge. This warning is expected and safe to ignore — the content is on main, just not via a merge commit.

## Next Steps

### 1. Evaluate the `codex.consult` open question

**Dependencies:** None — T-03 is complete.

**What to read first:** `decisions.md:115-117` (the open question), `contracts.md` codex.consult surface, and the official plugin's native review/task flow.

**Approach suggestion:** Write a concrete decision memo comparing `codex.consult` against native review/task patterns. The open question is the one place where the spec explicitly acknowledges the official plugin's approach might be sufficient.

**Acceptance criteria:** Either close the question (keep `codex.consult` with rationale) or escalate it (propose retirement path with migration plan).

### 2. Address deferred persistence replay hardening

**Dependencies:** None — independent of `codex.consult` evaluation.

**What to read first:** The deferred items from this session:
- I2: `turn_store.py:70-71` — one bad JSONL record crashes entire TurnStore replay
- I3: `journal.py:142`, `lineage_store.py:99`, `turn_store.py:68` — JSONL replay silently discards corrupt mid-file records
- I4: `lineage_store.py:110-127` — unknown operations silently dropped

**Approach suggestion:** Dedicated `fix/persistence-replay-hardening` branch. Add logging for corrupt/unknown records, add KeyError resilience to turn_store replay. Keep the trailing-record tolerance (crash-safe append-only semantics) but log when non-trailing records are corrupt.

### 3. Address remaining type improvements

**Dependencies:** None.

**What to read first:**
- F4: `profiles.py:22-29` — `ResolvedProfile` stringly-typed fields (posture, effort should be Literal types)
- F6: `models.py:111-127` — `AdvisoryRuntimeState.session: Any` should be typed

**Approach suggestion:** `chore/` branch. Define `Posture = Literal[...]` and `Effort = Literal[...]`, use in `ResolvedProfile`. Type `session` as `AppServerRuntimeSession`.

## In Progress

Clean stopping point. PR #90 squash-merged to main at `43fa3ba5`. Feature branch deleted. Working tree clean on main. No work in flight.

## Open Questions

### `codex.consult` surface retirement

Whether `codex.consult` should eventually be retired in favor of native review/task patterns plus a lighter structured wrapper remains open at `decisions.md:115-117`. Unchanged from prior sessions.

### AC6 analytics emission

Deferred from T-03. Thread C (profile/audit schema expansion) must be investigated before implementation.

### Deferred review suggestions (S1-S16, second pass)

16 suggestions from the second review agents were not independently validated by the user. They may contain false positives. If a future session encounters any of these areas, validate the specific finding against the current code before acting.

## Risks

### Deferred persistence replay issues (I2/I3/I4)

Three replay hardening issues were deferred: turn_store crashes on malformed records, JSONL replay silently drops corrupt mid-file records, lineage_store silently drops unknown operations. These predate T-03 and haven't caused known issues, but they represent reliability gaps in crash recovery.

### Stringly-typed ResolvedProfile

`ResolvedProfile.posture` and `.effort` accept arbitrary strings. A typo in a profile YAML (e.g., `posture: adversrial`) silently propagates to the prompt builder. The profile validation gate catches sandbox/approval widening but not posture/effort typos.

## References

| What | Where |
|------|-------|
| Squash merge commit | `43fa3ba5` on main |
| PR #90 (merged) | jpsweeney97/claude-code-tool-dev#90 |
| T-03 implementation plan | `docs/superpowers/plans/2026-03-30-codex-collaboration-safety-substrate.md` |
| Prior handoff (first review) | `docs/handoffs/archive/2026-03-31_13-04_t03-safety-substrate-pr-review-and-hardening.md` |
| Prior handoff (T-03 complete) | `docs/handoffs/archive/2026-03-31_15-49_t03-safety-substrate-implementation-complete.md` |
| Governance decision | `docs/superpowers/specs/codex-collaboration/decisions.md:41-49` |
| `codex.consult` open question | `docs/superpowers/specs/codex-collaboration/decisions.md:115-117` |
| Spec packet | `docs/superpowers/specs/codex-collaboration/` (12 files) |

## Gotchas

### T-03 is now on main — no feature branch exists

The branch `feature/codex-collaboration-safety-substrate` has been deleted (local and remote). The 16 individual commits are preserved in PR #90's GitHub history but not on any branch. All work is in the squash commit `43fa3ba5` on main.

### Post-squash reconciliation requires `git branch -f`, not pull/rebase

After squash merge, `git pull --rebase` on main would try to replay the feature branch commits on top of the squash — producing duplicate changes. Use `git branch -f main origin/main` instead. The `git branch -d` warns "not yet merged to HEAD" — this is expected because git can't see the squash as an ancestor merge.

### `policy_for_tool` now raises KeyError for unknown tools (unchanged from first pass)

Any new tool added to `mcp_server.py` MUST have a corresponding entry in `_TOOL_POLICY_MAP` at `consultation_safety.py:51-55`, or the guard will block it.

### Frozen safety types are now truly immutable

`ToolScanPolicy.expected_fields` and `.content_fields` are `frozenset`. `SafetyVerdict.unexpected_fields` is `tuple`. `SecretFamily.placeholder_bypass` is `tuple`. Code that previously relied on mutating these fields (e.g., `.add()`, `.append()`) will get `AttributeError` at runtime.

### hooks.json modified — sync required after promotion

When this plugin is promoted to production, the `hooks.json` change needs to be picked up by Claude Code. Per CLAUDE.md: "Run `uv run scripts/sync-settings` after modifying hooks."

## User Preferences

**Reviews before merge:** User explicitly requested a second review pass before merge: "PR #90 needs a second review pass." Does not assume prior review completeness implies merge readiness.

**Structured triage with hypotheses:** User provided ranked hypotheses, evidence requirements, and tests before diving into fixes. Format: (1) hypothesis ranked by likelihood, (2) evidence needed, (3) tests to run. This matches the root cause analysis pattern in global CLAUDE.md.

**Corrects agent findings:** User identified the I1 finding as factually incorrect and stated it should be dropped. Demonstrates deep Python knowledge and critical evaluation of automated findings.

**Implements fixes themselves:** User said they would implement C1 and C2 and return for review. This is consistent with the prior session's observation: "User operates as a collaborative architect, not a task requester."

**Precise commit strategy:** User specified three separate commits with exact messages and ordering rationale. Ordering: behavioral fix first (rollback boundary), behavior-preserving refactor second (easier to validate), docs last (zero runtime effect).

**Squash merge preference for long feature branches:** User stated: "Main should optimize for readability and revertability, not preserve every task checkpoint." Squash is the default landing strategy for branches with many small commits.

**Post-squash reconciliation via `git branch -f`:** User provided the exact reconciliation sequence and explicitly prohibited `git pull --rebase` and `git reset --hard`. Rule: "ancestry is gone, content is preserved."
