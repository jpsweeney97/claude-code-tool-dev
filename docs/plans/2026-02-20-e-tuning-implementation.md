# E-TUNING Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add provenance tags and assembler validation to the `/dialogue` pipeline to reduce overlap between the two context-gathering agents.

**Architecture:** Every CLAIM line carries a line-semantic `[SRC:code]` or `[SRC:docs]` tag based on the actual source file cited. The assembler validates tags after dedup (Step 3h-bis), a reason collector (Step 4b) composes `seed_confidence` from all metrics sources, and `provenance_unknown_count` flows through analytics. The falsifier's no-assumptions fallback is constrained to rationale surfaces only.

**Tech Stack:** Markdown instruction files (agents, skill, grammar reference), Python (emit_analytics.py + pytest)

**Reference:** `docs/plans/2026-02-19-cross-model-plugin-enhancements.md` §2

**Branch:** Create `feature/e-tuning` from `main`.

**Test command:** `uv run pytest tests/test_emit_analytics.py -v`

**All paths relative to:** `packages/plugins/cross-model/`

**Dependencies between tasks:**
- Task 1 (tag-grammar.md): independent — defines the SRC field grammar all other files reference
- Task 2 (context-gatherer-code.md): depends on Task 1 (references updated grammar)
- Task 3 (context-gatherer-falsifier.md): depends on Task 1 (references updated grammar)
- Task 4 (SKILL.md): depends on Tasks 2-3 — **runtime dependency** (rollout ordering: if 3h-bis ships before gatherer updates, every CLAIM gets `[SRC:unknown]`, triggering universal `seed_confidence: low`)
- Task 5 (codex-dialogue.md): depends on Task 4 (references `[SRC:unknown]` in briefing, which 3h-bis assigns)
- Task 6 (emit_analytics.py + tests): depends on Task 4 (needs to know the reason enum values and pipeline field names)

**Strict ordering:** Task 1 → (Task 2 + Task 3 in parallel) → Task 4 → Task 5 → Task 6

---

## Task List

### Task 1: Extend tag grammar with SRC field
- **Modify:** `skills/dialogue/references/tag-grammar.md`
- **Rationale:** Foundation — defines the `[SRC:<source>]` field that all other files reference. Changes the grammar line, adds to tag table, adds parse rules, updates assembly processing order (insert provenance validation between Dedup and Group), adds examples.

### Task 2: Add SRC tags to code explorer
- **Modify:** `agents/context-gatherer-code.md`
- **Rationale:** Gatherer A — must ship with or before 3h-bis (rollout ordering constraint). Adds `[SRC:code]` to all CLAIM output format and examples.

### Task 3: Constrain falsifier fallback + add SRC tags
- **Modify:** `agents/context-gatherer-falsifier.md`
- **Rationale:** Gatherer B — must ship with or before 3h-bis. Two changes: (1) constrain no-assumptions fallback to rationale surfaces only, (2) add line-semantic SRC tags to all CLAIM output.

### Task 4: Add 3h-bis, Step 4b, and pipeline updates to SKILL.md
- **Modify:** `skills/dialogue/SKILL.md`
- **Rationale:** Core pipeline changes. Adds 3h-bis provenance validation (between 3g and 3h), Step 4b reason collector, SRC tags in retry prompt (3b), updates 3c skip list to include 3h-bis, adds `provenance_unknown_count` to Step 7 pipeline table, updates `low_seed_confidence_reasons` source to "Step 4b".

### Task 5: Add unknown-claims-priority to codex-dialogue
- **Modify:** `agents/codex-dialogue.md`
- **Rationale:** Briefing passthrough — `[SRC:unknown]` lines pass through to the dialogue agent, which must prioritize verifying them via scouting. Small, targeted addition.

### Task 6: Harden emit_analytics.py + add provenance_unknown_count plumbing
- **Modify:** `scripts/emit_analytics.py`
- **Test:** `tests/test_emit_analytics.py`
- **Rationale:** Two changes: (1) add enum enforcement for `low_seed_confidence_reasons` values, (2) make `provenance_unknown_count` a real pipeline input (currently hard-coded to `None`). Schema version auto-bumps to `0.2.0` when `provenance_unknown_count` is non-null.

---

## Summary of Deliverables

| File | Change | Spec Section |
|------|--------|--------------|
| `references/tag-grammar.md` | Add `[SRC:<source>]` to grammar, tag table, parse rules, assembly order, examples | §2.5 |
| `agents/context-gatherer-code.md` | Add `[SRC:code]` to CLAIM output format and examples | §2.3 |
| `agents/context-gatherer-falsifier.md` | Constrain no-assumptions fallback + add line-semantic SRC tags | §2.2, §2.3 |
| `skills/dialogue/SKILL.md` | Add 3h-bis, Step 4b, retry SRC prompt, 3c skip list, Step 7 provenance field | §2.4, §2.4a |
| `agents/codex-dialogue.md` | Add unknown-claims-priority scouting instruction | §2.4 (briefing passthrough) |
| `scripts/emit_analytics.py` | Enum enforcement + provenance_unknown_count plumbing + schema version bump | §2.6, §4.4 |
| `tests/test_emit_analytics.py` | Tests for enum enforcement + provenance_unknown_count | — |

---

## Detailed Tasks

### Task 1: Extend tag grammar with SRC field

**Modify:** `packages/plugins/cross-model/skills/dialogue/references/tag-grammar.md`

**Step 1: Update grammar line**

Change line 8 from:

```
TAG: <content> [@ <path>:<line>] [AID:<id>] [TYPE:<type>]
```

To:

```
TAG: <content> [@ <path>:<line>] [AID:<id>] [TYPE:<type>] [SRC:<source>]
```

**Step 2: Add SRC field description**

After the `TYPE:` field description (line 16), add:

```
- `SRC:<source>` — provenance tag. Gatherer-emitted values: `code`, `docs`. Assembler-assigned only: `unknown` (indicates gatherer did not follow output format — never valid in gatherer output). Required on CLAIM lines. Optional on OPEN lines. Not used on COUNTER/CONFIRM (AID provides traceability).
```

**Step 3: Add SRC column to tag table**

Replace the tag table (lines 20-26):

```markdown
| Tag | Purpose | Citation | AID | TYPE | SRC |
|-----|---------|----------|-----|------|-----|
| `CLAIM` | Factual observation about the codebase | Required | Optional | No | Required |
| `COUNTER` | Evidence contradicting a stated assumption | Required | Required | Required | No |
| `CONFIRM` | Evidence supporting a stated assumption | Required | Required | No | No |
| `OPEN` | Unresolved question or ambiguity | Optional | Optional | No | Optional |
```

**Step 4: Add SRC parse rules**

After existing parse rule 7 (line 44), add:

```
8. `SRC:` values must be one of `code`, `docs`. `unknown` is assembler-assigned only — if a gatherer emits `SRC:unknown`, treat it as a missing SRC tag (the assembler will assign `[SRC:unknown]` in step 8).
```

**Step 5: Insert provenance validation step in assembly processing order**

Renumber current step 8 (Group) to step 9. Insert new step 8 between Dedup (7) and Group:

```
8. **Validate provenance** — for each `CLAIM` line in the retained set, check for `[SRC:code]` or `[SRC:docs]`. If missing, assign `[SRC:unknown]` and increment `provenance_unknown_count`. Does not drop lines.
9. **Group** — deterministic order (Gatherer A first, then B within each section):
```

Also update the zero-output fallback reference: "skip steps 4-8" → "skip steps 4-9".

**Step 6: Add SRC to examples**

Update Gatherer A examples:

```
CLAIM: Redaction pipeline has 3 layers (generic, format-specific, token) @ redact.py:45 [SRC:code]
CLAIM: Format-specific redaction handles YAML, JSON, TOML independently @ redact_formats.py:11 [SRC:code]
CLAIM: Generic token redaction runs unconditionally after format-specific @ redact.py:78 [SRC:code]
CLAIM: Denylist covers 14 directory patterns and 12 file patterns @ paths.py:22 [SRC:code]
OPEN: Whether format-specific redaction adds value given generic runs unconditionally
```

Update Gatherer B examples:

```
CONFIRM: Denylist covers OWASP secret categories (AWS, PEM, JWT, GitHub PAT) @ paths.py:22 AID:A1
COUNTER: Format-specific layer has zero matches in 847/969 test cases @ test_redact.py:203 AID:A2 TYPE:interface mismatch
COUNTER: Generic redaction catches all patterns format-specific targets @ redact.py:78 AID:A2 TYPE:control-flow mismatch
OPEN: Whether test fixture coverage reflects production workload distribution AID:A2
```

(No SRC on COUNTER/CONFIRM/OPEN — unchanged.)

Add a new edge case example:

```
CLAIM: Architecture uses event sourcing for audit log @ docs/decisions/ADR-003.md:12 [SRC:docs]
```
Valid — citation present, SRC is `docs` because the cited file is in `docs/`.

```
CLAIM: Pipeline has 3 layers @ redact.py:45
```
Missing SRC — assembler assigns `[SRC:unknown]` in step 8.

**Step 7: Commit**

```bash
git add packages/plugins/cross-model/skills/dialogue/references/tag-grammar.md
git commit -m "feat(cross-model): add [SRC:<source>] provenance tag to tag grammar

Adds provenance field to grammar, tag table, parse rules, assembly
processing order (new step 8: validate provenance), and examples.
Spec: §2.5 of cross-model-plugin-enhancements."
```

---

### Task 2: Add SRC tags to code explorer

**Modify:** `packages/plugins/cross-model/agents/context-gatherer-code.md`

**Step 1: Update grammar line**

Change the grammar block (line 55) from:

```
TAG: <content> [@ <path>:<line>]
```

To:

```
TAG: <content> [@ <path>:<line>] [SRC:<source>]
```

**Step 2: Add SRC column to tag table**

Replace the tag table (lines 62-66):

```markdown
| Tag | When to use | Citation required? | SRC required? |
|-----|-------------|-------------------|---------------|
| `CLAIM` | Factual observation about the codebase | Yes — `@ path:line` | Yes — `[SRC:code]` |
| `OPEN` | Unresolved question or ambiguity you discovered | No (but preferred) | No |
```

**Step 3: Update examples**

Replace examples (lines 73-80):

```
CLAIM: Redaction pipeline has 3 layers (generic, format-specific, token) @ redact.py:45 [SRC:code]
CLAIM: Format-specific redaction handles YAML, JSON, TOML independently @ redact_formats.py:11 [SRC:code]
CLAIM: Generic token redaction runs unconditionally after format-specific @ redact.py:78 [SRC:code]
CLAIM: 969 tests across 23 test files cover the context injection system @ tests/conftest.py:1 [SRC:code]
CLAIM: Checkpoint serialization uses HMAC-signed tokens @ checkpoint.py:89 [SRC:code]
OPEN: Whether format-specific redaction adds value given generic runs unconditionally
```

**Step 4: Update citation rule**

Replace line 82:

```
Every `CLAIM` must include a citation (`@ path:line`). Lines without citations are discarded by the assembler.
```

With:

```
Every `CLAIM` must include a citation (`@ path:line`) and a provenance tag (`[SRC:code]`). Lines without citations are discarded by the assembler. Lines without provenance tags are assigned `[SRC:unknown]` by the assembler.
```

**Step 5: Commit**

```bash
git add packages/plugins/cross-model/agents/context-gatherer-code.md
git commit -m "feat(cross-model): add [SRC:code] provenance tag to code explorer

Every CLAIM line now carries [SRC:code]. This agent only explores code,
test, and config files, so all CLAIMs are SRC:code.
Spec: §2.3 of cross-model-plugin-enhancements."
```

---

### Task 3: Constrain falsifier fallback + add SRC tags

**Modify:** `packages/plugins/cross-model/agents/context-gatherer-falsifier.md`

**Step 1: Replace the no-assumptions fallback section**

Replace lines 48-54 (the current "No-Assumptions Fallback" section):

```markdown
## No-Assumptions Fallback

When the `assumptions` list is empty (the question contains no testable assumptions):

1. Explore **rationale surfaces only**: `docs/decisions/`, `docs/plans/`, `docs/learnings/`, `CLAUDE.md`, `README.md`, and architectural files at repository root.
2. Do NOT explore code files, test files, or config files — those are the code explorer's domain.
3. Emit `CLAIM` and `OPEN` items about design rationale, architectural decisions, and documented constraints relevant to the question.
4. Tag every `CLAIM` line with the appropriate provenance tag (see Provenance Tags below).
5. Do **not** emit `COUNTER` or `CONFIRM` — these require assumption IDs.
```

**Step 2: Update grammar line in output format**

Change the grammar block (line 61) from:

```
TAG: <content> [@ <path>:<line>] [AID:<id>] [TYPE:<type>]
```

To:

```
TAG: <content> [@ <path>:<line>] [AID:<id>] [TYPE:<type>] [SRC:<source>]
```

**Step 3: Add SRC column to tag table**

Replace the tag table (lines 66-72):

```markdown
| Tag | When to use | Citation | AID | TYPE | SRC |
|-----|-------------|----------|-----|------|-----|
| `COUNTER` | Evidence contradicting an assumption | Required | Required | Required | No |
| `CONFIRM` | Evidence supporting an assumption | Required | Required | No | No |
| `OPEN` | Unresolved question or ambiguity | Optional | Optional | No | No |
| `CLAIM` | Factual observation (no-assumptions fallback only) | Required | No | No | Required |
```

**Step 4: Add provenance tags section**

After the CONFIRM behavior section (after line 101), add:

```markdown
### Provenance tags

Every `CLAIM` line must include a provenance tag based on the actual source file cited:

| Tag | When to use |
|-----|-------------|
| `[SRC:code]` | CLAIM cites a code, test, or config file |
| `[SRC:docs]` | CLAIM cites a docs, plans, decisions, README, or CLAUDE.md file |

`COUNTER`, `CONFIRM`, and `OPEN` lines do not require provenance tags.

In the no-assumptions fallback (rationale surfaces only), all CLAIMs will carry `[SRC:docs]` because only documentation files are explored.
```

**Step 5: Update no-assumptions fallback examples**

Replace the fallback examples (lines 105-110):

```
CLAIM: Authentication module chosen over JWT per ADR-003 @ docs/decisions/ADR-003.md:12 [SRC:docs]
CLAIM: Caching strategy documented as "defer until profiled" @ docs/plans/architecture.md:45 [SRC:docs]
OPEN: Whether the caching deferral decision still holds given new requirements
```

**Step 6: Commit**

```bash
git add packages/plugins/cross-model/agents/context-gatherer-falsifier.md
git commit -m "feat(cross-model): constrain falsifier fallback + add SRC tags

No-assumptions fallback now restricted to rationale surfaces only
(docs/decisions/, docs/plans/, docs/learnings/, CLAUDE.md, README.md).
Line-semantic [SRC:code]/[SRC:docs] provenance tags added to all CLAIMs.
Spec: §2.2, §2.3 of cross-model-plugin-enhancements."
```

---

### Task 4: Add 3h-bis, Step 4b, and pipeline updates to SKILL.md

**Modify:** `packages/plugins/cross-model/skills/dialogue/SKILL.md`

This is the largest task — 6 edits to the pipeline.

**Step 1: Add SRC to retry prompt (3b)**

Replace the 3b paragraph (line 98):

Old:
```
**3b. Low-output retry:** After parsing, if a gatherer produced fewer than 4 parseable tagged lines, re-launch that gatherer once with a prompt reinforcing the output format: "Emit findings as prefix-tagged lines per the output format. Each CLAIM must include `@ path:line` citation. Each COUNTER must include `@ path:line` citation, `AID:<id>`, and `TYPE:<type>`." Parse the retry output (3a) and combine with the original lines. If still below 4 after retry, proceed with available output.
```

New:
```
**3b. Low-output retry:** After parsing, if a gatherer produced fewer than 4 parseable tagged lines, re-launch that gatherer once with a prompt reinforcing the output format: "Emit findings as prefix-tagged lines per the output format. Each CLAIM must include `@ path:line` citation and `[SRC:code]` or `[SRC:docs]` provenance tag. Each COUNTER must include `@ path:line` citation, `AID:<id>`, and `TYPE:<type>`." Parse the retry output (3a) and merge with the original lines: non-duplicate lines are combined (both kept). For duplicate claim keys (same tag type + normalized citation): retry-wins — prefer the SRC-tagged version from retry output over the untagged original. Tie-break: if both original and retry have valid SRC tags (`code` or `docs`), keep the retry version. If still below 4 after retry, proceed with available output.
```

**Step 2: Update 3c skip list and seed_confidence handling**

In the 3c section (around line 114), change:

Old:
```
Set `seed_confidence` to `low`. Skip steps 3d-3h.
```

New:
```
Set `seed_confidence` to `low` with `low_seed_confidence_reasons: ["zero_output"]`. Skip steps 3d through 3h (including 3h-bis), Step 4, and Step 4b.

**3c as terminal exception:** Step 3c is a terminal early-exit that bypasses the normal pipeline entirely. Step 4b is the "sole authority" for `seed_confidence` within its jurisdiction (the normal path where Steps 3d-3h, 4, and 4b all run). When 3c fires, it sets both `seed_confidence` and `low_seed_confidence_reasons` directly because the composition step (4b) is skipped. The `zero_output` row in Step 4b's reason table documents the reason's semantics, not its runtime origin — in the 3c path, the reason is set by 3c itself, not collected by 4b.
```

**Step 3: Insert 3h-bis between 3g and 3h**

After the 3g (Dedup) paragraph (line 126), before 3h (Group), insert:

```markdown
**3h-bis. Validate provenance:** For each `CLAIM` line in the final retained set, check for `[SRC:code]` or `[SRC:docs]`. If a CLAIM line lacks a provenance tag:
- Assign `[SRC:unknown]`. Emitters never produce `unknown`; its presence means the gatherer did not follow its output format.
- Increment `provenance_unknown_count`.

3h-bis produces `provenance_unknown_count` as a metric only. It does **not** set `seed_confidence` — that happens in Step 4b.

Do **not** implement path inference (guessing SRC from the citation path). This is an explicit prohibition — `[SRC:unknown]` preserves data and marks uncertainty for downstream recovery via scouting.

`[SRC:unknown]` lines are preserved in the assembled briefing — not stripped before delegation.

**Pipeline state:** Initialize `provenance_unknown_count` as a pipeline variable with these semantics:
- `null` — Step 3c fired (3h-bis never ran). Signals to `emit_analytics.py` that provenance validation was skipped; schema stays at `0.1.0`.
- `0` — 3h-bis ran and all CLAIMs have valid SRC tags. Signals provenance validation ran successfully; schema bumps to `0.2.0`.
- Positive `int` — count of CLAIMs where `[SRC:unknown]` was assigned. If `>= 2`, Step 4b adds `provenance_violations` to `low_seed_confidence_reasons`.

Store this value for use by Step 4b (reason evaluation) and Step 7 (analytics emission).
```

**Step 4: Restructure Step 4 (metrics only, no confidence setting)**

Replace the Step 4 section (lines 146-157):

Old:
```markdown
### Step 4: Health check

Count citations and unique files in the assembled briefing:

| Metric | Threshold | On failure |
|--------|-----------|-----------|
| Total lines with `@ path:line` | >= 8 | Set `seed_confidence` to `low` |
| Unique file paths cited | >= 5 | Set `seed_confidence` to `low` |

If either threshold fails, `seed_confidence` is `low`. Both must pass for `normal`.

`seed_confidence: low` does **not** block the dialogue. It tells the dialogue agent to prioritize early scouting to compensate for thin initial context.
```

New:
```markdown
### Step 4: Health check

Count citations and unique files in the assembled briefing. Step 4 computes metrics only — it does **not** set `seed_confidence`. That happens in Step 4b.

| Metric | Threshold | Reason code on failure |
|--------|-----------|----------------------|
| Total lines with `@ path:line` | >= 8 | `thin_citations` |
| Unique file paths cited | >= 5 | `few_files` |

Store triggered reason codes for Step 4b.

### Step 4b: Compose seed_confidence

Collect reasons from all pipeline stages into `low_seed_confidence_reasons`:

| Reason | Source | Trigger |
|--------|--------|---------|
| `zero_output` | Step 3c (terminal) | Total parseable lines = 0 after retries. Set directly by 3c — 4b is skipped. |
| `thin_citations` | Step 4 | Total lines with `@ path:line` < 8 |
| `few_files` | Step 4 | Unique file paths cited < 5 |
| `provenance_violations` | Step 3h-bis | `provenance_unknown_count` >= 2 |

`seed_confidence` = `low` if `low_seed_confidence_reasons` is non-empty; `normal` otherwise. Step 4b is the sole authority for `seed_confidence` in the normal pipeline path (Steps 3d through 4b all run). Exception: Step 3c is a terminal early-exit that sets `seed_confidence` directly and skips 4b entirely (see Step 2 above). No short-circuit masking between reasons — all triggered reasons are collected.

`seed_confidence: low` does **not** block the dialogue. It tells the dialogue agent to prioritize early scouting to compensate for thin initial context.
```

**Step 5: Update Step 7 pipeline table**

In the Step 7 pipeline field table (lines 206-232), make three changes:

1. Change `seed_confidence` source from `Step 4` to `Step 4b`
2. Change `low_seed_confidence_reasons` source from `Step 4` to `Step 4b`, and update the type description
3. Add `provenance_unknown_count` row

Updated rows:

```
| `seed_confidence` | Step 4b | `"normal"` or `"low"` |
| `low_seed_confidence_reasons` | Step 4b | list of enum: `thin_citations`, `few_files`, `zero_output`, `provenance_violations` |
```

New row (add after `claim_count`):

```
| `provenance_unknown_count` | Step 3h-bis | int or null |
```

**Step 6: Verify edits**

Verify no stale references:
- Search for "3d-3h" — should now say "3d through 3h (including 3h-bis)" or similar
- Search for "Step 4" in seed_confidence context — should reference Step 4b
- Confirm 3h-bis appears between 3g and 3h in the processing order

**Step 7: Commit**

```bash
git add packages/plugins/cross-model/skills/dialogue/SKILL.md
git commit -m "feat(cross-model): add 3h-bis provenance validation + Step 4b reason collector

Pipeline additions:
- 3b: SRC tags in retry prompt, retry-wins supersession for duplicate keys
- 3c: explicit zero_output reason, updated skip list
- 3h-bis: validate provenance tags, assign [SRC:unknown], count violations
- Step 4: metrics only (no longer sets seed_confidence)
- Step 4b: sole authority for seed_confidence via reason collector
- Step 7: provenance_unknown_count in pipeline table
Spec: §2.4, §2.4a of cross-model-plugin-enhancements."
```

---

### Task 5: Add unknown-claims-priority to codex-dialogue

**Modify:** `packages/plugins/cross-model/agents/codex-dialogue.md`

**Step 1: Add unknown-provenance claims section**

After the "Low seed confidence behavior" section (after line 134), add:

```markdown
### Unknown-provenance claims

When the assembled briefing is received (via the `<!-- dialogue-orchestrated-briefing -->` sentinel), extract `unknown_claim_paths` — the set of citation paths (`@ path:line`) from any briefing line containing `[SRC:unknown]`.

If `unknown_claim_paths` is non-empty, prioritize verifying those claims via mid-dialogue scouting:

- **Briefing parse (Phase 1):** After detecting the sentinel, scan the briefing `## Material` section for lines containing `[SRC:unknown]`. Extract each cited `path:line` into the `unknown_claim_paths` set. Store this set in conversation state.
- **Step 4 (Scout):** When selecting among `template_candidates`, prefer candidates whose `entity_key` matches a path in `unknown_claim_paths`. If multiple candidates match, prefer the highest-ranked (lowest `rank` value).
- **Step 6 (Compose follow-up):** Treat unknown-provenance claims as higher priority than unprobed `new` claims — insert between priority items 2 (Unresolved items) and 3 (Unprobed claims) in the existing follow-up composition list.

`[SRC:unknown]` is an assembler-assigned tag indicating the gatherer did not follow its output format. Scouting converts this quality signal into dialogue-level recovery — the agent verifies the claim's evidence surface directly rather than relying on incorrect metadata.
```

**Step 2: Commit**

```bash
git add packages/plugins/cross-model/agents/codex-dialogue.md
git commit -m "feat(cross-model): add unknown-claims-priority scouting instruction

codex-dialogue agent now prioritizes [SRC:unknown] claims for
mid-dialogue scouting, converting assembler quality signals into
dialogue-level recovery.
Spec: §2.4 (briefing passthrough) of cross-model-plugin-enhancements."
```

---

### Task 6: Harden emit_analytics.py + add provenance_unknown_count plumbing

**Modify:** `packages/plugins/cross-model/scripts/emit_analytics.py`
**Test:** `tests/test_emit_analytics.py`

**Step 1: Add valid reasons enum set**

After `_VALID_MODES` (line 49), add:

```python
_VALID_LOW_SEED_CONFIDENCE_REASONS = {
    "thin_citations",
    "few_files",
    "zero_output",
    "provenance_violations",
}
```

**Step 2: Add provenance_unknown_count to _COUNT_FIELDS**

Add `"provenance_unknown_count"` to the `_COUNT_FIELDS` set (line 78). It's nullable — the existing count validator already skips None values.

**Step 3: Make provenance_unknown_count a real pipeline input**

In `build_dialogue_outcome()`, change line 348:

Old:
```python
        "provenance_unknown_count": None,
```

New:
```python
        "provenance_unknown_count": pipeline.get("provenance_unknown_count"),
```

**Step 4: Add schema version auto-bump**

In `build_dialogue_outcome()`, change from returning the dict directly to assigning it, then conditionally bumping:

After the dict construction (before the function ends), assign to `event` variable and add:

```python
    event = {
        # ... existing dict content ...
    }

    # Schema version auto-bump (§4.4): non-null provenance → 0.2.0
    if event.get("provenance_unknown_count") is not None:
        event["schema_version"] = "0.2.0"

    return event
```

**Step 5: Add enum enforcement to validate()**

After the existing `low_reasons` type and string-items checks (lines 470-475), add:

```python
        invalid = set(low_reasons) - _VALID_LOW_SEED_CONFIDENCE_REASONS
        if invalid:
            raise ValueError(
                f"invalid low_seed_confidence_reasons values: {sorted(invalid)}"
            )
```

**Step 6: Update existing test for enum enforcement**

In `tests/test_emit_analytics.py`, update `test_low_seed_confidence_reasons_valid` (line 641) — it currently uses arbitrary strings that would fail enum validation:

Old:
```python
    def test_low_seed_confidence_reasons_valid(self) -> None:
        """Valid list of strings passes."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["low_seed_confidence_reasons"] = ["narrow scope", "few files"]
        MODULE.validate(event, "dialogue_outcome")  # no exception
```

New:
```python
    def test_low_seed_confidence_reasons_valid(self) -> None:
        """Valid list of enum strings passes."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["low_seed_confidence_reasons"] = ["thin_citations", "few_files"]
        MODULE.validate(event, "dialogue_outcome")  # no exception
```

**Step 7: Write new tests**

Add these tests to `tests/test_emit_analytics.py`:

In `TestValidate`:

```python
    def test_invalid_low_seed_confidence_reason_rejected(self) -> None:
        """Only enum values from §2.4a are accepted."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["low_seed_confidence_reasons"] = ["narrow_scope"]
        with pytest.raises(ValueError, match="invalid low_seed_confidence_reasons"):
            MODULE.validate(event, "dialogue_outcome")

    def test_all_low_seed_confidence_reasons_accepted(self) -> None:
        """All four enum values pass validation together."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["low_seed_confidence_reasons"] = [
            "thin_citations", "few_files", "zero_output", "provenance_violations"
        ]
        MODULE.validate(event, "dialogue_outcome")  # no exception

    def test_provenance_unknown_count_negative_rejected(self) -> None:
        """provenance_unknown_count must be non-negative (via _COUNT_FIELDS)."""
        pipeline = {**SAMPLE_PIPELINE, "provenance_unknown_count": 3}
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        event["provenance_unknown_count"] = -1
        with pytest.raises(ValueError, match="non-negative int"):
            MODULE.validate(event, "dialogue_outcome")

    def test_provenance_unknown_count_bool_rejected(self) -> None:
        """provenance_unknown_count bool must be rejected (via _COUNT_FIELDS)."""
        pipeline = {**SAMPLE_PIPELINE, "provenance_unknown_count": 3}
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        event["provenance_unknown_count"] = True
        with pytest.raises(ValueError, match="non-negative int"):
            MODULE.validate(event, "dialogue_outcome")
```

In `TestBuildDialogueOutcome`:

```python
    def test_provenance_unknown_count_from_pipeline(self) -> None:
        """provenance_unknown_count flows from pipeline when provided."""
        pipeline = {**SAMPLE_PIPELINE, "provenance_unknown_count": 3}
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        assert event["provenance_unknown_count"] == 3

    def test_provenance_unknown_count_none_when_absent(self) -> None:
        """provenance_unknown_count defaults to None when not in pipeline."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        assert event["provenance_unknown_count"] is None

    def test_schema_version_bumps_with_provenance(self) -> None:
        """schema_version auto-bumps to 0.2.0 when provenance_unknown_count is non-null."""
        pipeline = {**SAMPLE_PIPELINE, "provenance_unknown_count": 0}
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        assert event["schema_version"] == "0.2.0"

    def test_schema_version_stays_without_provenance(self) -> None:
        """schema_version stays 0.1.0 when provenance_unknown_count is None."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        assert event["schema_version"] == "0.1.0"
```

**Step 8: Run tests**

Run: `uv run pytest tests/test_emit_analytics.py -v`

Expected: All tests pass (84 existing + 8 new = 92 total). The one modified test (`test_low_seed_confidence_reasons_valid`) also passes with enum values.

**Step 9: Commit**

```bash
git add packages/plugins/cross-model/scripts/emit_analytics.py tests/test_emit_analytics.py
git commit -m "feat(cross-model): enum enforcement + provenance_unknown_count plumbing

- Add _VALID_LOW_SEED_CONFIDENCE_REASONS enum enforcement in validate()
- Make provenance_unknown_count a real pipeline input (was hard-coded None)
- Auto-bump schema_version to 0.2.0 when provenance_unknown_count is non-null
- Add provenance_unknown_count to _COUNT_FIELDS for non-negative int validation
- 8 new tests, 1 updated test (92 total)
Spec: §2.6, §4.4 of cross-model-plugin-enhancements."
```

---

## Final Verification

Run: `uv run pytest tests/test_emit_analytics.py -v`
Expected: All 92 tests pass

Verify no stale references across all modified files:
- `rg "3d-3h[^-]" packages/plugins/cross-model/` — should find zero matches (all updated to include 3h-bis)
- `rg "3a-bis" packages/plugins/cross-model/` — should find zero matches (spec renamed to 3h-bis)
- `rg "Step 4\b" packages/plugins/cross-model/skills/dialogue/SKILL.md` — verify references to Step 4 vs Step 4b are correct

## Summary of Deliverables

| Module | New/Modified | What This Plan Adds |
|--------|-------------|---------------------|
| `references/tag-grammar.md` | Modified | `[SRC:<source>]` grammar, parse rules, assembly step 8 |
| `agents/context-gatherer-code.md` | Modified | `[SRC:code]` on all CLAIM output |
| `agents/context-gatherer-falsifier.md` | Modified | Rationale-only fallback + line-semantic SRC tags |
| `skills/dialogue/SKILL.md` | Modified | 3h-bis, Step 4b, retry SRC prompt, pipeline table |
| `agents/codex-dialogue.md` | Modified | Unknown-claims-priority scouting |
| `scripts/emit_analytics.py` | Modified | Enum enforcement, provenance plumbing, schema bump |
| `tests/test_emit_analytics.py` | Modified | 8 new tests (92 total) |
