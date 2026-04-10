# T-20260410-01: dialogue-codex turn-semantics clarification

```yaml
id: T-20260410-01
date: 2026-04-10
status: open
priority: medium
tags: [codex-collaboration, b4, shakedown, dialogue-codex, contract]
blocked_by: []
blocks: []
effort: small
```

## Context

The live B4 `/shakedown-b1` dry run passed and staged artifacts successfully on
commit `7f4eed41`. The inspection checklist cleared, but transcript inspection
surfaced a remaining contract inconsistency in `dialogue-codex`.

The emitted state blocks in
`/Users/jp/.claude/plugins/data/codex-collaboration-inline/shakedown/transcript-9f5da415-0a90-4863-a611-407d29e512f7.jsonl`
use `turn` values `2, 3, 4, 5, 6`.

The current skill contract says:

- `turn` is monotonically increasing, starting at `1`
- non-scouting turns use explicit empty-field values

The current runtime behavior and the current prose are therefore not aligned.

## Problem

`dialogue-codex` does not currently define a single unambiguous meaning of
"turn."

Two plausible interpretations exist:

1. **Logical dialogue turn:** the opening send is `turn: 1`, even though no
   scouting happens yet, so the first emitted state block should be
   `scouted: false`.
2. **Post-reply verification turn:** the first emitted state block follows
   Codex's first reply, so numbering starts at `2`.

Right now the skill mixes these models:

- the field table implies model 1
- the observed transcript and skill exemplars imply model 2
- the non-scouting-turn rules imply there are legitimate emitted turns with
  `scouted: false`, but do not say whether the opening send is one of them

This ambiguity does not block B4 runtime correctness, but it does weaken the
emission contract and future inspection clarity.

## Scope

**In scope:**

- Decide what `turn` means in `dialogue-codex`
- Align the contract prose, exemplars, and checklist expectations to that
  chosen meaning
- Preserve the currently validated B4 runtime behavior unless there is a
  concrete reason to change it

**Out of scope:**

- Re-opening the B4 runtime gate
- Changing containment, harness sequencing, or dialogue transport behavior
- Broad redesign of the scouting loop beyond turn semantics

## Decision needed

Choose one of these contract models:

1. **Start at 1 with an emitted non-scouting opening turn**
   - Update the skill behavior so the opening send emits a state block with
     `scouted: false`
   - Keep the current "starting at 1" rule
   - Clarify that the opening-send turn is part of the emitted protocol

2. **Start at 2 for the first post-reply verification turn**
   - Update the field rule and any affected checklist language
   - Clarify that emitted state blocks begin only after a Codex reply exists
   - Reassess whether the non-scouting-turn rules should remain as written

## Acceptance criteria

1. `dialogue-codex/SKILL.md` defines `turn` semantics without contradiction
2. The skill exemplars match the chosen semantics
3. The inspection checklist can adjudicate the first emitted turn without
   interpretation drift
4. Future shakedown runs do not require operator judgment to decide whether the
   first emitted turn number is correct

## References

- Skill contract:
  `packages/plugins/codex-collaboration/skills/dialogue-codex/SKILL.md`
- B4 dry-run transcript:
  `/Users/jp/.claude/plugins/data/codex-collaboration-inline/shakedown/transcript-9f5da415-0a90-4863-a611-407d29e512f7.jsonl`
- B4 inspection template:
  `/Users/jp/.claude/plugins/data/codex-collaboration-inline/shakedown/inspection-9f5da415-0a90-4863-a611-407d29e512f7.md`
