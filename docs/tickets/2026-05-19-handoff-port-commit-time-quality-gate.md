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
2026-05-19 via interactive grilling + Codex consult `42c10159`).

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

## Proposed Solution (Option B)

Invoke `quality_check` **inside the active-writer commit step**
(`handoff_runtime` active-write commit path) so a handoff failing the quality
contract is **rejected before promotion** to the final path — a true hard gate,
not advisory `additionalContext`.

This is architecturally superior to the hook model: the staged content already
exists and the commit is a single runtime chokepoint, so validation there can
actually refuse the promotion.

## Why Deferred (not done in the port)

- **Scope:** modifies the ported runtime's commit path — beyond the locked
  one-time-port envelope (path + manifest + branding + hooks-retarget).
- **Failure semantics change:** `save`/`quicksave`/`summary` become able to
  *fail* on quality grounds. That is a deliberate behavior change requiring its
  own design + tests + skill-doc updates, not a port side effect.
- **Sequencing:** must land *after* the port (it edits the ported runtime), so
  it cannot be part of the port commit set.

## Acceptance Criteria

1. `quality_check` (or its validation core) is invoked at the active-writer
   commit chokepoint for handoff/checkpoint/summary writes.
2. A write failing the quality contract is **rejected before promotion**; the
   final `.claude/handoffs/` artifact is not created, and the staged content +
   reservation are cleaned up or left in a documented recoverable state.
3. Failure surfaces as a clear, operator-actionable error (consistent with the
   runtime's existing diagnostic-payload conventions), not a silent skip.
4. Skill docs (`save`, `quicksave`, `summary`) document the new
   quality-rejection failure mode and recovery.
5. Tests cover: clean write promotes; hollow/malformed write is rejected
   pre-promotion; reservation/staging cleanup after rejection.
6. The Option-A advisory `PostToolUse:Write → quality_check` hook is either
   retired (superseded by the hard gate) or explicitly retained as a
   complementary early-feedback layer — decided in this ticket, documented.

## Dependencies

- **Blocked by `handoff-codex-port`**: this edits the ported runtime's commit
  path; the port must land first.
