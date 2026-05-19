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
2026-05-19 post `/scrutinize` + `/grill-me`). **Second 2026-05-19 revision**
(cross-model verification loop): the prior "satisfiable as-is" feasibility
framing was falsified — `quality_check.Issue` carries only `severity` +
`message` and `validate()` returns one flat list, so the two-tier split is not
extractable from the existing model without an issue-provenance refactor. This
revision repairs the design spec (mechanism, tier definitions, AC #5) so the
ticket is executable once the port lands; no runtime code is changed here.

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

- **Chokepoint:** `active_writes.write_active_handoff` (durable write at
  `_write_content_to_active_path`, wrapped in
  reservation/lock/snapshot/transaction machinery). Reached identically by
  save/quicksave/summary: skill stages body → `$CONTENT_FILE`, computes
  `$CONTENT_SHA256`, then "commit through the active writer" → `session_state`
  facade → `write_active_handoff`. It is genuinely the single commit
  entrypoint. (Symbols only, no line numbers: Decision 4's rename and this
  ticket's own `Issue` refactor both shift offsets.)
- **Validation core — invocable as-is, NOT tier-filterable as-is.**
  `quality_check.validate(content) -> list[Issue]` is pure and I/O-free, so it
  can be *called* at the chokepoint unchanged. But its *output* cannot be
  partitioned into tiers as-is: `Issue` carries only `severity`
  ("error"/"warning") + `message` with no per-issue provenance, and
  `validate()` returns one flat list (and `validate_line_count` emits
  `severity="error"`, so severity does not separate the tiers). AC #1's "or its
  validation core" is therefore **not** satisfiable without the `Issue`
  tier/provenance refactor in Proposed Solution — an open design requirement,
  not a closed one.
- **Failure/recovery already exists:** `ActiveWriteError` +
  `_recovery_commands` + reservation/snapshot rollback already provide most
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

**Two-tier model — partitioned by issue source, NOT by `severity`** (decided
2026-05-19): `validate()` returns a flat `list[Issue]` and `validate_line_count`
emits `severity="error"` for under-minimum bodies, so a severity-keyed gate is
provably wrong — it would hard-block legitimate terse handoffs.

- **Integrity tier — HARD-BLOCKS at the chokepoint.** Defined by source and
  behavior, covering *every* integrity failure path in `validate()`:
  1. **no-frontmatter early return** — `validate()` returns before any
     sub-validator runs when frontmatter is absent;
  2. **invalid-`type` early return** — `validate()` returns before
     sub-validators when `type` is outside the allowlist;
  3. invalid/missing required frontmatter fields (`validate_frontmatter`);
  4. absent required sections (`validate_sections`);
  5. hollow-document guardrail (`validate_sections`: required content sections
     present but empty).
  These are the "hollow/malformed → unloadable or untriageable" cases this
  ticket exists to stop. (1) and (2) are the maximally-hollow cases and live
  *outside* `validate_frontmatter`/`validate_sections` — a predicate scoped to
  only those two validators silently misses the worst inputs.
- **Advisory tier — does NOT block, regardless of `severity`.** **Every**
  `validate_line_count` issue is advisory and never gates promotion — both
  under-minimum and over-maximum body length, for handoff/summary/checkpoint,
  **including the ones `validate_line_count` emits at `severity="error"`**.
  These stay on the **retained** Option-A `PostToolUse:Write → quality_check`
  hook as early feedback. Rationale: `/save` exists to capture state under
  context pressure; a hard *length* gate would make `/save` refuse to
  checkpoint exactly when a terse handoff is legitimate — turning the safety
  net into a failure mode. (There is no "section-depth" validator;
  `count_body_lines` is a line-count helper consumed by `validate_line_count`.)

**Mechanism — required `quality_check` refactor (not an incidental edit).**
Because `Issue` today is only `severity` + `message` and `validate()` returns
one flat, untagged list, the tier split is **not** extractable from the
existing model. This ticket must add per-issue provenance to `quality_check`: a
`tier` (or `blocking`) discriminator set at **every** `Issue` construction
site — explicitly including the two `validate()` early returns and the hollow
guardrail — and the chokepoint filters on the integrity discriminator, **never
on `severity`**. This is a deliberate cross-cutting refactor with its own test
surface, not a one-line filter, and it is the load-bearing design work this
ticket exists to specify.

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
5. Tests cover: (a) clean write promotes; (b) each integrity-tier path is
   rejected pre-promotion — **no-frontmatter**, **invalid-`type`**, missing
   required frontmatter field, missing required section, and hollow-document
   (content sections present but empty); (c) a **valid-frontmatter +
   valid-sections doc under the line-count minimum still promotes** (proves
   `validate_line_count` `severity="error"` issues do NOT gate — the AC #5
   case the prior draft got backwards); (d) an over-maximum-length doc still
   promotes; (e) reservation/staging cleanup after a rejection.
6. **AC #6 resolved:** the Option-A advisory `PostToolUse:Write → quality_check`
   hook is **retained** as the advisory-tier early-feedback layer (it carries
   the `validate_line_count` feedback the chokepoint deliberately does not
   block). The chokepoint enforces the integrity tier only. Documented in the
   skill docs and the plugin CHANGELOG.

## Dependencies

- **Blocked by `handoff-codex-port`**: this edits the ported runtime's commit
  path; the port must land first. The *chokepoint* and *invocation point* are
  verified to exist (see Verified Integration Points), so the integration is a
  sequencing dependency. The *tier mechanism* is an **open design requirement**
  resolved in Proposed Solution (the `Issue` provenance refactor) — it is
  designed and tested as part of this ticket, not assumed free.
