# T-07 Slice 7d: Context-Injection Removal Plan

## Overview

| Attribute | Value |
|-----------|-------|
| Slice | 7d |
| Branch | `feature/t07-context-injection-removal-7d` |
| Dependency | 7c merged (PR #120 at `c59dbf11`) |
| AC addressed | "Context-injection is removed as part of the cross-model cutover" |
| Authority | T-04 demonstrated-not-scored retirement decision |
| Type | Deletion + reference cleanup |

## Post-7d State

After 7d, the cross-model package is a **deprecated shell awaiting 7e
removal**. Specifically:

- Cross-model `/codex` (consult) and `/delegate` still function — they
  do not depend on context-injection. `/codex`'s delegation branch
  (which previously could launch `codex-dialogue`) is replaced with a
  redirect to codex-collaboration `/dialogue`.
- Cross-model `/dialogue` is **retired**. The skill is marked
  `user-invocable: false` + `disable-model-invocation: true` and
  redirects to codex-collaboration's `/dialogue` (delivered in T-04).
  The `codex-dialogue` agent is also replaced with a retirement stub so
  direct/plugin subagent invocation stops immediately instead of reaching
  stale context-injection instructions. No manual-only rewrite is attempted.
- Cross-model `/consultation-stats` still functions (reads flat event log).
- All of these surfaces are removed in 7e.

This is an intentional, honest degradation: context-injection is retired
(T-04), its replacement is live (codex-collaboration), and the shell is
being removed in the next slice.

## Scope

Remove `packages/plugins/cross-model/context-injection/` and all live
operational references that would cause runtime errors or test failures.

**Explicitly not 7d scope:**
- Removing `packages/plugins/cross-model/` (that is 7e)
- Checking the cross-model removal AC
- Running the live `/delegate` smoke (7e gate)
- Editing the consultation contract's §15 governance section
- Rewriting the cross-model dialogue agent to be manual-only (see
  Post-7d State above)
- Updating `README.md`, `HANDBOOK.md`, or `CHANGELOG.md` — these are
  historical narrative docs being removed entirely in 7e; their
  context-injection references describe past state accurately

## Decisions

### D1: Retain `references/context-injection-contract.md` as historical/validation-only until 7e

The consultation contract §15 (line 408) references CI-SEC-1 through
CI-SEC-6 by name and points to `context-injection-contract.md`. Two
validation paths check this cross-reference:

- `test_governance_content.py:28` — asserts CI-SEC refs resolve
- `validate_consultation_contract.py:202` — same check in CI script

Removing the reference file in 7d would require editing the consultation
contract's §15 governance section — scope creep into a core governance
document. Both the reference file and the two validation paths remain until
7e removes the entire cross-model package.

**Deviation from 7c:** The 7c migration artifact (line 112) lists this
contract as "Retired with context-injection." That describes the contract's
*authority status* — it no longer governs a live subsystem. This plan
retains the *file* for validation purposes only. The contract text is
present-tense governance for a system that no longer runs; it is retained
solely because `CI-SEC-*` cross-references from the consultation contract
would break if it were deleted.

### D2: Remove ingress/parity tests from `test_credential_parity.py`

This test imports `context_injection.redact` to compare ingress/egress
redaction parity. After 7d, the ingress layer no longer exists, so the
parity tests are meaningless. The `TestEgressCorpus` class and egress
scanner (`scripts/credential_scan.py`) are independent and unaffected.

**Alternative considered:** Stub the import. Rejected — the test validates
a property (two-layer parity) that no longer holds. A stub would make a
meaningless test pass silently.

**File naming:** The surviving `test_credential_parity.py` contains only
`TestEgressCorpus` — a misleading name for a one-suite file. Accepted
until 7e, when the file is deleted with the package. Renaming is churn
for a file with a one-slice lifespan.

### D3: Retire dialogue skill with stub; remove all launch paths to codex-dialogue

The `codex-dialogue` agent has two launch paths:

1. `/dialogue` skill (Step 5 delegates to `cross-model:codex-dialogue`)
2. `/codex` skill (Step 2 "Subagent delegation" branch, lines 116-160)

Both must be patched. After 7d, context-injection tools no longer exist,
so any path reaching the agent leads to stale instructions.

**Skill retirement:** Replace the entire dialogue `SKILL.md` with a
retirement stub:

- Set `user-invocable: false` (hides from `/` menu)
- Set `disable-model-invocation: true` (removes from Claude's context)
- Remove `allowed-tools` and `argument-hint`
- Replace body with a short notice: context-injection was removed in
  T-07 7d, use codex-collaboration `/dialogue` instead, do not proceed

This makes the skill invisible to both user and model. If somehow
reached, it stops immediately with a redirect.

**`/codex` delegation branch:** Replace the "Subagent delegation" section
(lines 116-160) in `skills/codex/SKILL.md` with a redirect to
codex-collaboration `/dialogue`. The direct invocation path (Step 3) is
unaffected — `/codex` still functions for single-turn consultations.

**Agent retirement:** Replace `codex-dialogue.md` entirely with a
retirement stub. The agent description is changed to `"[RETIRED] ..."`,
the body is replaced with a stop notice redirecting to codex-collaboration
`/dialogue`, and context-injection tools are removed from the `tools`
frontmatter. This is necessary because Claude Code auto-delegates to
plugin subagents based on the `description` field — a live description
with an active "Use when..." trigger would still route invocations into
stale context-injection instructions even with all skill launch paths
removed.

Per Claude Code docs: `user-invocable: false` controls menu visibility;
`disable-model-invocation: true` "removes the skill from Claude's context
entirely." Both are needed for a full retirement.

### D4: Cross-model dialogue is retired and unreachable after 7d

This is the plan's central behavioral decision. After 7d:

- Cross-model `/dialogue` skill is invisible to both user and model
  (`user-invocable: false` + `disable-model-invocation: true`).
- If somehow reached, the stub body stops immediately and redirects.
- `/codex`'s delegation branch no longer launches `codex-dialogue`;
  it redirects to codex-collaboration `/dialogue`.
- The `codex-dialogue` agent is also a retirement stub — its description
  says `[RETIRED]` and its body stops with a redirect. This is necessary
  because Claude Code auto-delegates to plugin subagents based on the
  description field; a live description would still route invocations
  into dead instructions even with skill launch paths removed.
- codex-collaboration `/dialogue` is the active replacement (T-04).

## Change Set

### Group 1: Package deletion

| # | Path | Action | Mechanics |
|---|------|--------|-----------|
| 1 | `packages/plugins/cross-model/context-injection/` | Delete entire directory | `trash` the directory, then `git add -u` to stage tracked-file removals. Git history preserves all code. Untracked files (`.venv/`, `.pytest_cache/`, `.ruff_cache/`, `.DS_Store`) go to trash with the directory. |

### Group 2: Workspace and registration

| # | File | Line(s) | Action |
|---|------|---------|--------|
| 2 | `pyproject.toml` (root) | 8 | Remove `"packages/plugins/cross-model/context-injection",` workspace member |
| 3 | `uv.lock` (root) | — | Regenerated by `uv lock` after workspace member removal. Expected diff: removal of `context-injection` package metadata and dependency resolution entries. |
| 4 | `packages/plugins/cross-model/.mcp.json` | 11-18 | Remove `context-injection` MCP server entry. Resulting file has only the `codex` server. |

### Group 3: Dialogue surface retirement

| # | File | Change |
|---|------|--------|
| 5 | `cross-model/skills/dialogue/SKILL.md` | **Replace entirely** with a retirement stub. Frontmatter: `name: dialogue`, `description: "[RETIRED] ..."`, `user-invocable: false`, `disable-model-invocation: true`. Body: short notice that context-injection was removed in T-07 7d, redirects to codex-collaboration `/dialogue`, instructs Claude to stop. See D3 for stub specification. |
| 6 | `cross-model/agents/codex-dialogue.md` | **Replace entirely** with a retirement stub. Description: `"[RETIRED] ..."`. Remove context-injection tools from `tools` frontmatter. Body: stop notice redirecting to codex-collaboration `/dialogue`. Agent auto-delegation based on description field requires stubbing, not just frontmatter cleanup (see D3). |
| 7 | `cross-model/skills/codex/SKILL.md` | Replace "Subagent delegation" section (lines 116-160) with a short redirect: for extended multi-turn consultations, use codex-collaboration `/dialogue` instead. Keep the direct invocation path (Step 3) and everything after it unchanged. The `/dialogue` tip on line 123 is now the only multi-turn guidance. |

### Group 4: Test cleanup

| # | File | Action |
|---|------|--------|
| 8 | `tests/test_mcp_surface_contract.py` | Remove `test_context_injection_server_tools_referenced` (lines 80-85). |
| 9 | `tests/test_credential_parity.py` | Remove `TestIngressCorpus` class (lines 37-48), `TestPemParity` class (lines 51-63), `context_injection.redact` import (line 16), and `_PEM_PRIVATE_KEY_RE` import (line 56). Retain `TestEgressCorpus` (lines 23-34) and its `credential_scan` import (line 15). |
| 10 | `tests/test_compute_stats.py` | Fix pre-existing date-dependent test failure: `test_period_filtering_reduces_events` hardcoded `"2026-03-06"` as "recent" with a 30-day window, but `compute()` uses `datetime.now(UTC)` making the test time-bomb. Replace with `(now - 5 days).isoformat()`. |

### Group 5: Not changed (retained until 7e)

| File | Why retained |
|------|-------------|
| `references/context-injection-contract.md` | Historical/validation-only — consultation contract §15 cross-references CI-SEC-* (D1) |
| `test_governance_content.py:28` | Validates CI-SEC cross-references still resolve against retained file (D1) |
| `validate_consultation_contract.py:202` | Same validation in CI script (D1) |
| `README.md`, `HANDBOOK.md`, `CHANGELOG.md` | Historical narrative docs — references describe past state accurately; deleted in 7e |
| All other cross-model skills/agents/hooks/scripts | 7e scope |

## Verification

After all changes, run from the repo root. Each command is self-contained
(no CWD mutation). Positive checks must exit 0; negative checks use
`! grep -rq` which exits 0 when no match is found.

```bash
# 1. Cross-model tests still pass (minus deleted tests)
(cd packages/plugins/cross-model && uv run --package cross-model-plugin pytest)

# 2. uv lock succeeds with workspace member removed
uv lock

# 3. No dangling Python imports of context_injection
# Exits 0 if no match (pass), exits 1 if match found (fail)
! grep -rq 'from context_injection\|import context_injection' \
  packages/plugins/cross-model/ \
  --include='*.py'

# 4. No dangling context-injection tool references in operational surfaces
# Both skill and agent are retirement stubs; check all frontmatter and config
# Exits 0 if no match (pass), exits 1 if match found (fail)
! grep -rq 'context-injection__' \
  packages/plugins/cross-model/skills/ \
  packages/plugins/cross-model/agents/ \
  packages/plugins/cross-model/hooks/ \
  packages/plugins/cross-model/.mcp.json

# 5. No live launch path to codex-dialogue from any skill
# Exits 0 if no match (pass), exits 1 if match found (fail)
! grep -rq 'cross-model:codex-dialogue' \
  packages/plugins/cross-model/skills/ \
  --include='*.md'

# 6. Governance cross-reference tests still pass (D1)
(cd packages/plugins/cross-model && uv run --package cross-model-plugin pytest tests/test_governance_content.py -v)

# 7. Dialogue skill is retired (not user-invocable, not model-invocable)
grep -q 'user-invocable: false' packages/plugins/cross-model/skills/dialogue/SKILL.md && \
grep -q 'disable-model-invocation: true' packages/plugins/cross-model/skills/dialogue/SKILL.md

# 8. codex-dialogue agent is retired (description says RETIRED, body is stub)
grep -q '\[RETIRED\]' packages/plugins/cross-model/agents/codex-dialogue.md && \
grep -q 'Do not proceed' packages/plugins/cross-model/agents/codex-dialogue.md
```

## Build Sequence

1. Create branch (done: `feature/t07-context-injection-removal-7d`)
2. Delete `context-injection/` package via `trash` + `git add -u` (Group 1)
3. Remove workspace member, regenerate lockfile, remove MCP registration
   (Group 2)
4. Retire dialogue skill and agent, patch `/codex` delegation (Group 3)
5. Clean tests (Group 4)
6. Run verification (all 8 checks must pass)
7. Commit, push, PR

Groups 2-5 can be applied in any order after Group 1, but verification
runs last.

## Caveats That Travel With This Removal

Per T-04 closeout and T-07 ticket:

1. `T-20260416-01` (reply-path extraction mismatch) remains open
2. Mechanism losses L1 (scout integrity), L2 (plateau/budget control),
   L3 (per-scout redaction) are accepted trade-offs
3. Capture sequence spans multiple doc commits (audit fact)

## References

| Document | Location | Role |
|----------|----------|------|
| T-07 ticket | `docs/tickets/2026-03-30-codex-collaboration-analytics-reviewer-and-cutover.md` | AC definition |
| T-04 retirement decision | `docs/tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md` | Removal authority |
| 7c migration artifact | `docs/plans/2026-04-22-t07-cross-model-migration-and-parity-7c.md` | §2d removal inventory |
