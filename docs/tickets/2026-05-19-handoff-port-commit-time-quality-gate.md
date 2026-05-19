# Handoff: commit-time quality gate (hard pre-promotion enforcement)

```yaml
id: handoff-port-commit-time-quality-gate
date: 2026-05-19
status: open
priority: medium
blocked_by: [handoff-codex-port]
blocks: []
related: []
plugin: packages/plugins/handoff/
```

## Context

This ticket is the deferred "Option B" extracted from the handoff-plugin port
decision (one-time Claude Code port of the Codex `handoff` plugin, decided
2026-05-19 via interactive grilling + Codex consult `42c10159`; revised
2026-05-19 post `/scrutinize` + `/grill-me`).

During that port the quality-enforcement decision was made as **Option A**:
re-wire the existing hooks retargeted to the Claude host —
`SessionStart → cleanup` and `PostToolUse:Write → quality_check` — restoring
the *advisory* safety net the current Claude plugin already has. Option A was
chosen because it restores existing user-facing behavior without expanding the
port's locked envelope (path + manifest + branding + hooks-retarget) and does
not change `save` failure semantics.

**Option B was explicitly deferred to this ticket** rather than smuggled into
the port.

## Problem

`PostToolUse:Write → quality_check` is structurally **advisory only**:

- PostToolUse hooks cannot block — the file (staging content) is already written.
- In the ported architecture, the runtime commits the staged `$CONTENT_FILE`
  to the final `.claude/handoffs/` path in a *separate, later* Bash step that
  Claude controls. The hook can emit `additionalContext` Claude sees before it
  runs the commit, but nothing *enforces* that a hollow or malformed handoff is
  not promoted.

Result: a hollow/malformed handoff can still land if the advisory feedback is
ignored or the commit step proceeds anyway. The current Claude plugin has the
same advisory-only weakness; the port preserves parity but does not fix it.

## Verified Integration Points

The original draft asserted "a single runtime chokepoint" without locating it.
Verified 2026-05-19 against the Codex source (the port adopts this runtime
verbatim, renamed `handoff_runtime`):

- **Chokepoint:** `active_writes.py:564 write_active_handoff(...)` (durable
  write at `_write_content_to_active_path:507`, wrapped in
  reservation/lock/snapshot/transaction machinery). Reached identically by
  save/quicksave/summary: skill stages body → `$CONTENT_FILE`, computes
  `$CONTENT_SHA256`, then "commit through the active writer" → `session_state`
  facade → `write_active_handoff`. It is genuinely the single commit
  entrypoint.
- **Validation core:** `quality_check.py:297 validate(content) -> list[Issue]`
  is a pure, I/O-free function — the injectable core (AC #1's "or its
  validation core" is satisfiable as-is).
- **Failure/recovery already exists:** `ActiveWriteError` +
  `_recovery_commands:453` + reservation/snapshot rollback already provide most
  of AC #2's "cleaned up or documented recoverable state." This ticket hooks
  validation in and classifies blocking issues; it does not build rollback from
  scratch.

(Post-port, all symbols above live under `handoff_runtime/` — same code, renamed
namespace per the port's Decision 4.)

## Proposed Solution (Option B)

Invoke the `quality_check` validation core **inside `write_active_handoff`**
(before `_write_content_to_active_path` performs the durable write) so a handoff
failing the **integrity tier** of the quality contract is **rejected before
promotion** — a true hard gate, raising `ActiveWriteError` (the existing failure
type, with its existing recovery-command surface), not advisory
`additionalContext`.

**Two-tier severity model** (decided 2026-05-19; `validate()` currently returns
a flat `list[Issue]` spanning all checks):

- **Integrity tier — HARD-BLOCKS at the chokepoint.** Invalid/missing required
  frontmatter (`validate_frontmatter`) and absent required sections
  (`validate_sections`). These are the "hollow/malformed → unloadable or
  untriageable" cases this ticket exists to stop.
- **Advisory tier — does NOT block.** Line-count and section-depth
  (`validate_line_count` / `count_body_lines`). These stay on the **retained**
  Option-A `PostToolUse:Write → quality_check` hook as early feedback.
  Rationale: `/save` exists to capture state under context pressure; a hard
  *length* gate would make `/save` refuse to checkpoint exactly when a terse
  handoff is legitimate — turning the safety net into a failure mode.

Implementation requires `quality_check.Issue` to carry a blocking/severity flag
(or an explicit integrity-issue predicate) so the chokepoint can filter the
blocking subset. This is in-scope (the ticket already edits `quality_check.py`).

This is architecturally superior to the hook model: the staged content already
exists and the commit is a single runtime chokepoint, so validation there can
actually refuse the promotion.

## Why Deferred (not done in the port)

- **Scope:** modifies the ported runtime's commit path — beyond the locked
  one-time-port envelope (path + manifest + branding + hooks-retarget).
- **Failure semantics change:** `save`/`quicksave`/`summary` become able to
  *fail* on integrity grounds. That is a deliberate behavior change requiring
  its own design + tests + skill-doc updates, not a port side effect.
- **Sequencing:** must land *after* the port (it edits the ported runtime), so
  it cannot be part of the port commit set.

## Acceptance Criteria

1. The `quality_check` validation core (`validate()`) is invoked inside
   `write_active_handoff` (post-port: `handoff_runtime/active_writes.py`),
   before the durable `_write_content_to_active_path`, for
   handoff/checkpoint/summary writes.
2. A write whose **integrity-tier** issues are non-empty is **rejected before
   promotion** via `ActiveWriteError`; the final `.claude/handoffs/` artifact
   is not created, and the staged content + reservation are cleaned up or left
   in the runtime's existing documented recoverable state.
3. Failure surfaces as a clear, operator-actionable error reusing the runtime's
   existing diagnostic/recovery-command conventions (`_recovery_commands`), not
   a silent skip.
4. Skill docs (`save`, `quicksave`, `summary`) document the new
   integrity-rejection failure mode and recovery, and explicitly state that
   length/depth remain advisory (do not block).
5. Tests cover: clean write promotes; integrity-tier failure
   (missing-frontmatter and missing-required-section) is rejected
   pre-promotion; advisory-tier-only issue (too short) still promotes;
   reservation/staging cleanup after rejection.
6. **AC #6 resolved:** the Option-A advisory `PostToolUse:Write → quality_check`
   hook is **retained** as the advisory-tier early-feedback layer (it carries
   line-count/section-depth feedback the chokepoint deliberately does not
   block). The chokepoint enforces the integrity tier only. Documented in the
   skill docs and the plugin CHANGELOG.

## Dependencies

- **Blocked by `handoff-codex-port`**: this edits the ported runtime's commit
  path; the port must land first. (Chokepoint/validation-core symbols verified
  to exist in the port source — see Verified Integration Points — so this is a
  sequencing dependency, not an open feasibility question.)
