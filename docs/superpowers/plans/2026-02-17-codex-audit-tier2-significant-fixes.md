# T-005: Codex Audit Tier 2 — Significant Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 14 Severity B findings from the Codex integration audit — ambiguous instructions, missing examples, calibration gaps, and hook hardening.

**Architecture:** Each of 4 target files gets one task. Findings are grouped by file. Tasks 1-4 are independent (no cross-task dependencies except B6's marker alignment, resolved by a plan-level decision). Task 5 is final verification.

**Reference:** `docs/tickets/2026-02-17-codex-audit-tier2-significant-fixes.md`

**Branch:** Create `chore/codex-audit-tier2` from `main`.

**Test command:** `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/context-injection && uv run pytest -q` (expect 969 passed)

**Plan-level decisions:**

- **B6 marker alignment:** Standardize on `[REDACTED: credential material]` (shorter, more consistent with typical redaction markers). Update SKILL.md line 132 to match codex-reviewer line 86.
- **B3 rename:** Use `current_turn` (clearer than keeping `turn_count` with a changed description). Rename in all locations using `replace_all`.
- **B8 default:** Add a note below the prompt table for unscoped prompts that describe content but not a diff range.
- **B12 matcher defense:** Add in-code `tool_name` filtering regardless of whether `matcher` works for PostToolUseFailure. The hooks docs don't list PostToolUseFailure as supporting matchers.

**Dependencies between tasks:**
- Task 1 (codex-dialogue): independent
- Task 2 (codex-reviewer): independent
- Task 3 (codex skill): independent (B6 marker decision made at plan level)
- Task 4 (hook): independent
- Task 5 (verification): depends on Tasks 1-4

---

## Task 1: Fix codex-dialogue agent (B1, B2, B3, B4)

**Files:**
- Modify: `.claude/agents/codex-dialogue.md`

**Findings addressed:**
- B1: Remove contradictory `focus.claims` scoping instruction (line 223)
- B2: Replace undefined "importance" in weakest-claim derivation (line 323)
- B3: Rename `turn_count` → `current_turn` at all locations
- B4: Add document-wide default behavior statement near top

**Edit order:** Bottom-to-top within file to avoid line-number drift: B2 → B1 → B4 → B3 (replace_all, position-independent).

**Step 1: Read the rules file (blocking requirement)**

Read `.claude/rules/subagents.md` — required before editing any agent file.

**Step 2: Read the full agent file**

Read `.claude/agents/codex-dialogue.md` to confirm current content matches plan expectations.

**Step 3: Fix B2 — Remove undefined "importance"**

Edit `.claude/agents/codex-dialogue.md`:

Old:
```
the weakest claim is the one with fewest `reinforced` statuses relative to its importance, not a value derived from aggregate counters in `cumulative`
```

New:
```
the weakest claim is the one with the fewest `reinforced` statuses across all turns in `turn_history`, not a value derived from aggregate counters in `cumulative`
```

Rationale: Drops undefined "importance" modifier. Simplifies to a concrete, deterministic metric: count `reinforced` statuses, pick the lowest.

**Step 4: Fix B1 — Remove contradictory claims scoping**

Edit `.claude/agents/codex-dialogue.md`:

Old:
```
- Build `claims` list once from ledger extraction. Assign to BOTH `focus.claims` and top-level `claims` fields. On subsequent turns, `focus.claims` contains claims relevant to the current focus scope (not the full conversation history — the server accumulates history internally).
```

New:
```
- Build `claims` list from ledger extraction each turn. Assign the identical list to BOTH `focus.claims` and top-level `claims` fields — the server requires both channels to carry identical lists (dual-claims guard CC-PF-3; mismatched lists trigger `ledger_hard_reject`). The server accumulates history internally; send only the current turn's extracted claims.
```

Rationale: The contract at `docs/references/context-injection-contract.md:65` explicitly requires `focus.claims == claims`. The old text's second sentence ("On subsequent turns, focus.claims contains claims relevant to the current focus scope") contradicted both the first sentence and the server's validation.

**Step 5: Fix B4 — Add document-wide default**

Edit `.claude/agents/codex-dialogue.md`. Insert after the `## Preconditions` section (after the turn-1 failure precedence bullet), before `## Task`:

Old:
```
## Task
```

New:
```
## Defaults

When no instruction covers the current situation: log a warning describing the unexpected state and proceed to the next step. If the current step cannot be skipped (it produces state required by subsequent steps), proceed directly to Phase 3 synthesis using whatever `turn_history` is available. Do not retry failed steps unless the error table in Step 3 explicitly permits retry.

## Task
```

**Step 6: Fix B3 — Rename turn_count → current_turn**

Edit `.claude/agents/codex-dialogue.md` using `replace_all: true`:

Old: `turn_count`
New: `current_turn`

Then fix the description at the state initialization table. Edit:

Old: `| `current_turn` | `1` | Turns completed |`
New: `| `current_turn` | `1` | Current turn number (1-indexed) |`

**Step 7: Verify all 4 fixes**

Run these checks:
- `grep "turn_count" .claude/agents/codex-dialogue.md` → expect 0 matches
- `grep "relative to its importance" .claude/agents/codex-dialogue.md` → expect 0 matches
- `grep "current focus scope" .claude/agents/codex-dialogue.md` → expect 0 matches
- `grep "## Defaults" .claude/agents/codex-dialogue.md` → expect 1 match
- `grep "dual-claims guard" .claude/agents/codex-dialogue.md` → expect 1 match
- `grep "current_turn" .claude/agents/codex-dialogue.md` → count matches (should be ≥5)

**Step 8: Commit**

```bash
git add .claude/agents/codex-dialogue.md
git commit -m "fix(codex-dialogue): resolve B1-B4 — claims contradiction, undefined importance, turn_count rename, defaults

B1: Fix contradictory focus.claims scoping (dual-claims guard requires identical lists)
B2: Replace undefined 'importance' with concrete 'fewest reinforced statuses'
B3: Rename turn_count → current_turn with clear description
B4: Add document-wide Defaults section for uncovered situations

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 2: Fix codex-reviewer agent (B5, B6, B7, B8)

**Files:**
- Modify: `.claude/agents/codex-reviewer.md`

**Findings addressed:**
- B5: Add severity calibration table
- B6: Verify marker (already correct — `[REDACTED: credential material]`)
- B7: Replace vague "surrounding context" with concrete guidance
- B8: Add note for unscoped content-describing prompts

**Step 1: Read the rules file (blocking requirement)**

Read `.claude/rules/subagents.md` — already read in Task 1, but confirm awareness.

**Step 2: Read the full agent file**

Read `.claude/agents/codex-reviewer.md` to confirm current content.

**Step 3: Fix B7 — Concrete surrounding-context guidance**

Edit `.claude/agents/codex-reviewer.md`:

Old:
```
- Read modified files for surrounding context (not just changed lines)
```

New:
```
- Read modified files for surrounding context: for files under 300 lines, read the full file; for larger files, read the modified functions/classes plus 20 lines above and below each change
```

Also edit the briefing template:

Old:
```
### Surrounding Code
[Key modified functions/classes with enough context to understand the change]
```

New:
```
### Surrounding Code
[Modified functions/classes with ≥20 lines of surrounding context. For files <300 lines, include the full file.]
```

**Step 4: Fix B8 — Add guidance for unscoped content prompts**

Edit `.claude/agents/codex-reviewer.md`. After the prompt table row `| No specific scope | \`git diff HEAD\` |`, add a note:

Old:
```
| No specific scope | `git diff HEAD` |

**Detecting the base branch:**
```

New:
```
| No specific scope | `git diff HEAD` |

**Prompt describes content but not scope** (e.g., "review the authentication module"): Treat as a branch review — use `git diff <base>...HEAD` (see base detection below). If on the default branch with no feature branch, fall back to `git diff HEAD`.

**Detecting the base branch:**
```

**Step 5: Fix B5 — Add severity calibration table**

Edit `.claude/agents/codex-reviewer.md`. After the severity ordering line, add a calibration table:

Old:
```
For each issue, ordered by severity (Critical > High > Medium > Low):

#### [Severity] Issue title
```

New:
```
For each issue, ordered by severity:

| Severity | Criteria | Example |
|----------|----------|---------|
| Critical | Exploitable security vulnerability or data loss risk. Would block a production deploy. | SQL injection, auth bypass, unencrypted secrets in code |
| High | Bug causing incorrect behavior under normal conditions. Likely to cause incidents. | Off-by-one in pagination, race condition in writes, missing null check on required field |
| Medium | Code smell or edge case that could cause problems under unusual conditions. | Missing error handling for unlikely failure, overly broad exception catch |
| Low | Minor inconsistency that indicates potential confusion but no immediate risk. | Misleading comment, inconsistent naming, unused import chain |

#### [Severity] Issue title
```

**Step 6: Verify B6 — Redaction marker**

Run: `grep "REDACTED" .claude/agents/codex-reviewer.md`

Expected: `[REDACTED: credential material]` — already matches plan decision. No change needed.

**Step 7: Verify all fixes**

- `grep "surrounding context" .claude/agents/codex-reviewer.md` → should show the new concrete guidance
- `grep "Prompt describes content" .claude/agents/codex-reviewer.md` → expect 1 match
- `grep "Criteria" .claude/agents/codex-reviewer.md` → expect 1 match (calibration table header)

**Step 8: Commit**

```bash
git add .claude/agents/codex-reviewer.md
git commit -m "fix(codex-reviewer): resolve B5, B7, B8 — severity calibration, context guidance, prompt default

B5: Add severity calibration table (Critical/High/Medium/Low with criteria and examples)
B7: Replace vague 'surrounding context' with concrete 300-line/20-line thresholds
B8: Add guidance for prompts that describe content but not a diff scope
B6: Verified — redaction marker already matches canonical format

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 3: Fix codex skill SKILL.md (B9, B10, B11, B14, B6)

**Files:**
- Modify: `.claude/skills/codex/SKILL.md`

**Findings addressed:**
- B6: Align redaction marker to `[REDACTED: credential material]`
- B9: Add delegation example
- B10: Add case-sensitivity note for `-t` flag
- B11: Add diagnostics cross-reference in Step 4
- B14: Define `$ARGUMENTS` at first use

**Step 1: Read the rules file (blocking requirement)**

Read `.claude/rules/skills.md` — required before editing any skill file.

**Step 2: Read the full skill file**

Read `.claude/skills/codex/SKILL.md` to confirm current content.

**Step 3: Fix B14 — Define $ARGUMENTS**

Edit `.claude/skills/codex/SKILL.md`:

Old:
```
Parse optional flags from `$ARGUMENTS`. Remaining text after flags = PROMPT.
```

New:
```
Parse optional flags from `$ARGUMENTS` — the raw text following `/codex` in the user's command (e.g., for `/codex -t high review this PR`, `$ARGUMENTS` is `-t high review this PR`). Remaining text after extracting flags = PROMPT.
```

**Step 4: Fix B10 — Case-sensitivity note**

Edit `.claude/skills/codex/SKILL.md`. After the flags table (after the `-t` row), add a note:

Old:
```
Only `prompt` is required by the MCP tool schema
```

New:
```
Flag values are case-insensitive: `high`, `HIGH`, and `High` are all accepted for `-t` and other enum flags.

Only `prompt` is required by the MCP tool schema
```

**Step 5: Fix B6 — Align redaction marker**

Edit `.claude/skills/codex/SKILL.md`:

Old:
```
replace with `[REDACTED: sensitive credential material]`
```

New:
```
replace with `[REDACTED: credential material]`
```

**Step 6: Fix B11 — Add diagnostics cross-reference in Step 4**

Edit `.claude/skills/codex/SKILL.md`:

Old:
```
Do not just parrot Codex's response. Add value as the primary agent.

## Failure Handling
```

New:
```
Do not just parrot Codex's response. Add value as the primary agent.

**After relaying:** Capture diagnostics for this consultation (see [Diagnostics](#diagnostics) section below — timestamp, strategy, flags, success/failure).

## Failure Handling
```

**Step 7: Fix B9 — Add delegation example**

Edit `.claude/skills/codex/SKILL.md`. After the delegation instructions (line 122, "4. To continue later..."), add:

Old:
```
4. To continue later, resume the subagent via its `agentId` (preserves richer context than raw `threadId`)

## Step 3: Invoke Codex
```

New:
```
4. To continue later, resume the subagent via its `agentId` (preserves richer context than raw `threadId`)

**Delegation example:**

User asks: `/codex I need a deep review of our caching strategy — challenge my assumptions`

This likely needs 3+ adversarial turns — delegate to codex-dialogue:

```
Task(
  subagent_type: "codex-dialogue",
  prompt: """
    Goal: Challenge the caching strategy assumptions.
    Posture: adversarial
    Budget: 5

    ## Context
    [Current caching approach, decisions made, trade-offs considered]

    ## Material
    [Key cache implementation files, config, performance data]

    ## Question
    What are the weakest assumptions in this caching strategy?
  """
)
```

The subagent returns a confidence-annotated synthesis with convergence points, divergence points, and the Codex `threadId`. Present this synthesis to the user with your own assessment.

## Step 3: Invoke Codex
```

**Step 8: Verify all fixes**

- `grep "\\$ARGUMENTS" .claude/skills/codex/SKILL.md` → should show the definition
- `grep "case-insensitive" .claude/skills/codex/SKILL.md` → expect 1 match
- `grep "sensitive credential" .claude/skills/codex/SKILL.md` → expect 0 matches
- `grep "credential material" .claude/skills/codex/SKILL.md` → expect 1 match
- `grep "Delegation example" .claude/skills/codex/SKILL.md` → expect 1 match
- `grep "After relaying" .claude/skills/codex/SKILL.md` → expect 1 match
- Count total lines: should still be under 500 (skills rule)

**Step 9: Commit**

```bash
git add .claude/skills/codex/SKILL.md
git commit -m "fix(codex-skill): resolve B6, B9, B10, B11, B14 — marker, examples, flags, diagnostics, args

B6: Align redaction marker to [REDACTED: credential material]
B9: Add delegation example showing codex-dialogue subagent usage
B10: Document case-insensitivity of flag values
B11: Add diagnostics cross-reference in Step 4
B14: Define \$ARGUMENTS at first use

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 4: Harden hook (B12, B13)

**Files:**
- Modify: `.claude/hooks/nudge-codex-consultation.py`

**Findings addressed:**
- B12: Add explicit `tool_name == "Bash"` filtering in code
- B13: Add `fcntl.flock` file locking for atomic counter updates

**Step 1: Read the rules file (blocking requirement)**

Read `.claude/rules/hooks.md` — required before editing any hook file.

**Step 2: Read the full hook file**

Read `.claude/hooks/nudge-codex-consultation.py` to confirm current content.

**Step 3: Fix B12 — Add tool_name filtering**

Edit `.claude/hooks/nudge-codex-consultation.py`. Add tool_name check immediately after parsing stdin:

Old:
```python
    session_id = event.get("session_id", "unknown")
```

New:
```python
    # B12: Defensive tool_name filtering — PostToolUseFailure matcher support
    # is undocumented, so filter in code to ensure only Bash failures count.
    tool_name = event.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    session_id = event.get("session_id", "unknown")
```

**Step 4: Fix B13 — Add file locking**

Edit `.claude/hooks/nudge-codex-consultation.py`. Add `fcntl` import and replace the read/write functions with locked versions:

Old:
```python
import json
import sys
import tempfile
from pathlib import Path
```

New:
```python
import fcntl
import json
import sys
import tempfile
from pathlib import Path
```

Replace `read_count` and `write_count`:

Old:
```python
def read_count(path: Path) -> int:
    try:
        return int(path.read_text().strip())
    except (FileNotFoundError, ValueError):
        return 0


def write_count(path: Path, count: int) -> None:
    path.write_text(str(count))
```

New:
```python
def read_and_update_count(path: Path, new_count: int) -> int:
    """Atomically read the current count and write a new value.

    Uses fcntl.flock for exclusive access. Returns the old count.
    """
    try:
        fd = os.open(str(path), os.O_RDWR | os.O_CREAT)
        with os.fdopen(fd, "r+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            content = f.read().strip()
            old_count = int(content) if content else 0
            f.seek(0)
            f.truncate()
            f.write(str(new_count))
        return old_count
    except (ValueError, OSError):
        return 0
```

Also add `import os` to the imports:

Old:
```python
import fcntl
import json
```

New:
```python
import fcntl
import json
import os
```

Then update `main()` to use the new function:

Old:
```python
    session_id = event.get("session_id", "unknown")
    path = state_path(session_id)
    count = read_count(path) + 1

    if count >= THRESHOLD:
        write_count(path, 0)
```

New (after B12's tool_name check):
```python
    session_id = event.get("session_id", "unknown")
    path = state_path(session_id)
    old_count = read_and_update_count(path, 0)  # Tentatively reset; see below
    count = old_count + 1

    if count >= THRESHOLD:
        # Counter already reset to 0 by read_and_update_count
```

Wait — this doesn't work cleanly because we need to either write `count` (if below threshold) or `0` (if at threshold). Let me restructure `main()` instead:

Old `main()` body (after stdin parsing and B12 tool_name check):
```python
    session_id = event.get("session_id", "unknown")
    path = state_path(session_id)
    count = read_count(path) + 1

    if count >= THRESHOLD:
        write_count(path, 0)
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUseFailure",
                "additionalContext": (
                    "You've hit several consecutive failures. "
                    "Consider running /codex to get a second opinion from another model. "
                    "It can help spot assumptions you might be stuck on."
                ),
            }
        }
        print(json.dumps(output))
    else:
        write_count(path, count)
```

New `main()` body (after stdin parsing and B12 tool_name check):
```python
    session_id = event.get("session_id", "unknown")
    path = state_path(session_id)

    # B13: Atomic read-increment-write with file locking
    try:
        fd = os.open(str(path), os.O_RDWR | os.O_CREAT)
        with os.fdopen(fd, "r+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            content = f.read().strip()
            count = (int(content) if content else 0) + 1

            if count >= THRESHOLD:
                f.seek(0)
                f.truncate()
                f.write("0")
            else:
                f.seek(0)
                f.truncate()
                f.write(str(count))
    except (ValueError, OSError):
        count = 1  # On any file error, assume first failure

    if count >= THRESHOLD:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUseFailure",
                "additionalContext": (
                    "You've hit several consecutive failures. "
                    "Consider running /codex to get a second opinion from another model. "
                    "It can help spot assumptions you might be stuck on."
                ),
            }
        }
        print(json.dumps(output))
```

This replaces `read_count`, `write_count`, and the conditional logic in `main()` with a single atomic block. The old helper functions (`read_count`, `write_count`) can be removed.

**Step 5: Verify the hook runs correctly**

Test with mock input:

```bash
echo '{"tool_name": "Bash", "session_id": "test-b12"}' | python3 .claude/hooks/nudge-codex-consultation.py
echo $?
# Expected: 0, no output (count = 1, below threshold)
```

```bash
echo '{"tool_name": "Read", "session_id": "test-b12"}' | python3 .claude/hooks/nudge-codex-consultation.py
echo $?
# Expected: 0, no output (non-Bash tool, exits early)
```

Run 3 Bash failures to trigger the nudge:
```bash
for i in 1 2 3; do echo '{"tool_name": "Bash", "session_id": "test-b12-threshold"}' | python3 .claude/hooks/nudge-codex-consultation.py; done
# Expected: 3rd invocation prints JSON with additionalContext
```

Clean up test state:
```bash
rm -f /tmp/claude-nudge-test-b12 /tmp/claude-nudge-test-b12-threshold
```

**Step 6: Lint check**

```bash
ruff check /Users/jp/Projects/active/claude-code-tool-dev/.claude/hooks/nudge-codex-consultation.py
```

Expected: Clean (no errors).

**Step 7: Commit**

```bash
git add .claude/hooks/nudge-codex-consultation.py
git commit -m "fix(hook): resolve B12, B13 — tool_name filtering and atomic file locking

B12: Add explicit tool_name == 'Bash' check (PostToolUseFailure matcher undocumented)
B13: Replace non-atomic read/write with fcntl.flock-guarded block

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 5: Final verification

**Dependencies:** Tasks 1-4 complete.

**Step 1: Run tests**

```bash
cd /Users/jp/Projects/active/claude-code-tool-dev/packages/context-injection && uv run pytest -q
```

Expected: 969 passed.

**Step 2: Cross-file grep checks**

```bash
# B1: No contradictory claims text
grep "current focus scope" .claude/agents/codex-dialogue.md
# Expected: 0 matches

# B2: No undefined importance
grep "relative to its importance" .claude/agents/codex-dialogue.md
# Expected: 0 matches

# B3: No old turn_count
grep "turn_count" .claude/agents/codex-dialogue.md
# Expected: 0 matches

# B6: Consistent redaction markers
grep "REDACTED" .claude/agents/codex-reviewer.md .claude/skills/codex/SKILL.md
# Expected: Both show [REDACTED: credential material] (no "sensitive")

# B12: tool_name filtering present
grep "tool_name" .claude/hooks/nudge-codex-consultation.py
# Expected: ≥1 match

# B13: fcntl present
grep "fcntl" .claude/hooks/nudge-codex-consultation.py
# Expected: ≥1 match
```

**Step 3: Update ticket status**

Edit `docs/tickets/2026-02-17-codex-audit-tier2-significant-fixes.md`:
- Change `status: open` → `status: complete`
- Change `branch: null` → `branch: chore/codex-audit-tier2`

**Step 4: Commit ticket update**

```bash
git add docs/tickets/2026-02-17-codex-audit-tier2-significant-fixes.md docs/plans/2026-02-17-codex-audit-tier2-significant-fixes.md
git commit -m "chore: mark T-005 complete, update plan

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Final Verification

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/packages/context-injection && uv run pytest -q`
Expected: 969 passed

Run: `ruff check /Users/jp/Projects/active/claude-code-tool-dev/.claude/hooks/nudge-codex-consultation.py`
Expected: No errors

## Summary of Deliverables

| File | Modified | What This Plan Fixes |
|------|----------|---------------------|
| `.claude/agents/codex-dialogue.md` | Modified | B1 claims contradiction, B2 undefined importance, B3 turn_count rename, B4 defaults section |
| `.claude/agents/codex-reviewer.md` | Modified | B5 severity calibration, B7 context guidance, B8 unscoped prompt handling |
| `.claude/skills/codex/SKILL.md` | Modified | B6 redaction marker, B9 delegation example, B10 case-sensitivity, B11 diagnostics xref, B14 $ARGUMENTS definition |
| `.claude/hooks/nudge-codex-consultation.py` | Modified | B12 tool_name filtering, B13 atomic file locking |
| `docs/tickets/...tier2...md` | Modified | Status update |
