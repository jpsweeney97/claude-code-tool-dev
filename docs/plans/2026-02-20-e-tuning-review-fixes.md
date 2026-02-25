# E-TUNING Review Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 10 review findings from PR #19 (E-TUNING) — 2 critical, 3 important, 4 suggestions, 1 emerged.

**Architecture:** All fixes are within the `feature/e-tuning` branch. C1 is a targeted rewrite of the unknown-provenance scouting section in `codex-dialogue.md` — replacing broken `entity_key` references with `entity_id → Entity` resolution and tiered path matching. C2-S4 are surgical edits (1-10 lines each) in markdown instruction files and Python analytics code/tests. Task 10 is an emerged doc fix.

**Reference:**
- PR review summary from 2026-02-20 session
- Codex dialogue `019c7dc1-4f8f-7b90-83b0-f088ca636721` (exploratory, 6 turns — fix approaches)
- Codex dialogue `019c7ddf-5b34-7352-b01c-e091f39e0e98` (adversarial, 5 turns — plan review)
- Codex dialogue `019c7df4-f4ef-7981-81fa-bb158bb5fe0a` (collaborative, 5 turns — open questions)

**Branch:** Continue on `feature/e-tuning` (already exists, PR #19 open).

**Test command:** `cd packages/plugins/cross-model && uv run pytest ../../../tests/test_emit_analytics.py -v`

**Dependencies between tasks:**
- Tasks 1, 6, 7: independent (each modifies a unique file)
- Task 2: independent
- Task 3: independent
- Task 4: blocked by Task 2 (both modify SKILL.md)
- Task 5: blocked by Tasks 3 and 4 (modifies both tag-grammar.md and SKILL.md)
- Task 8: independent (test only)
- Task 9: blocked by Tasks 6 and 8 (tests the `_is_non_negative_int` helper + both modify test_emit_analytics.py)
- Task 10: blocked by Task 5 (both modify SKILL.md)

**Parallel execution graph:**
- Batch 1 (parallel): Tasks 1, 2, 3, 6, 7, 8
- Batch 2 (after 2): Task 4
- Batch 3 (after 3, 4): Task 5
- Batch 4 (after 5): Task 10
- Batch 5 (after 6, 8): Task 9

---

## Task 1: Fix unknown-provenance scouting in codex-dialogue.md (C1)

**Files:**
- Modify: `packages/plugins/cross-model/agents/codex-dialogue.md:67` (Phase 1 pointer)
- Modify: `packages/plugins/cross-model/agents/codex-dialogue.md:105-114` (state table)
- Modify: `packages/plugins/cross-model/agents/codex-dialogue.md:136-146` (section rewrite)
- Modify: `packages/plugins/cross-model/agents/codex-dialogue.md:270-276` (response table + field list)
- Modify: `packages/plugins/cross-model/agents/codex-dialogue.md:348-354` (Step 6 priority)

**Context:** The "Unknown-provenance claims" section (lines 136-146) is dead code — it references `entity_key` on `TemplateCandidate` (which has `entity_id`), and compares bare `path:line` citation strings against typed `{entity_type}:{canonical_form}` entity keys. Three Codex dialogues converged on: pre-execution entity resolution with tiered matching, case-insensitive normalization, causal clearing mechanism, and standalone mode initialization.

**Key data model facts:**
- `TemplateCandidate` (types.py:240-256): has `entity_id: str`, `rank: int` (unique, assigned via enumerate), `template_id`, `scout_options`
- `Entity` (types.py:78-103): has `id: str`, `type` (file_loc, file_path, file_name, symbol, ...), `canonical: str`, `resolved_to: str | None`
- `Entity.canonical` strips line numbers for `file_loc` entities
- `make_entity_key(entity_type, canonical_form)` → `"{entity_type}:{canonical_form}"` (canonical.py:61-66)
- `TurnPacketSuccess.entities` is `list[Entity]` — available in the `process_turn` response but not documented in codex-dialogue.md's Step 3 response table

**Step 1: Add Phase 1 pointer**

In the External briefing detection section, after the final paragraph ending "The sentinel `<!-- dialogue-orchestrated-briefing -->` is injected by the `/dialogue` skill and never appears in standalone invocations." (~line 78), before the "Token safety" section, add a pointer:

```
For orchestrated briefings with `[SRC:unknown]` lines, see "Unknown-provenance claims" in Phase 2 below — extraction runs once before the per-turn loop begins.
```

**Step 2: Add `unknown_claim_paths` to conversation state table**

In `packages/plugins/cross-model/agents/codex-dialogue.md`, find the conversation state table (lines 105-114). Add a new row after `seed_confidence` (line 114):

Replace:
```
| `seed_confidence` | `normal` | From delegation envelope. Values: `normal`, `low`. Controls early-turn scouting bias. |
```

With:
```
| `seed_confidence` | `normal` | From delegation envelope. Values: `normal`, `low`. Controls early-turn scouting bias. |
| `unknown_claim_paths` | `∅` | Set of file paths (without line numbers) from `[SRC:unknown]` briefing lines. Populated once at briefing parse (before Step 1 of per-turn loop). Cleared per-path after successful scout verification. |
```

**Step 3: Add `entities` to Step 3 response data capture table**

At line 276, the `template_candidates` row in the `process_turn` response table says:
```
| `template_candidates` | Available scout options for evidence gathering. See Step 4. Fields per candidate: `rank`, `template_id`, `entity_key`, `scout_options` (each with `id`, `scout_token`). Note: `turn_request_ref` is NOT part of `template_candidates` — it is agent-derived in Step 4. |
```

Replace with:
```
| `entities` | List of extracted entities from focus and claims. Each has `id`, `type` (file_loc, file_path, file_name, symbol, ...), `canonical` (normalized form), `resolved_to` (alias target or null). Used by unknown-provenance scouting to resolve `entity_id` → entity path. |
| `template_candidates` | Available scout options for evidence gathering. See Step 4. Fields per candidate: `rank`, `template_id`, `entity_id`, `scout_options` (each with `id`, `scout_token`). Note: `turn_request_ref` is NOT part of `template_candidates` — it is agent-derived in Step 4. |
```

This both adds the missing `entities` row AND fixes `entity_key` → `entity_id` in the `template_candidates` row.

**Step 4: Rewrite "Unknown-provenance claims" section**

Replace lines 136-146 (the entire `### Unknown-provenance claims` section, from the heading through the final paragraph ending "...relying on incorrect metadata.") with:

```markdown
### Unknown-provenance claims

When the assembled briefing is received (via the `<!-- dialogue-orchestrated-briefing -->` sentinel), extract `unknown_claim_paths` from any briefing line containing `[SRC:unknown]`. This extraction runs once before Step 1 of the per-turn loop, after the briefing is available.

**Extraction:** Scan the briefing `## Material` section for lines containing `[SRC:unknown]`. For each such line, parse the citation from the `@ path:line` annotation and extract the path component only (strip the `:line` suffix). Normalize: strip leading `./`, collapse `//` to `/`. Store the resulting set in `unknown_claim_paths` in conversation state.

**Standalone mode:** If no sentinel is detected (standalone invocation, not from `/dialogue`), initialize `unknown_claim_paths = ∅`. No unknown claims can exist because non-orchestrated briefings have no `[SRC:unknown]` tags (no gatherer pipeline runs in standalone mode).

If `unknown_claim_paths` is non-empty, prioritize verifying those claims via mid-dialogue scouting:

- **Step 4 (Scout — entity resolution):** When selecting among `template_candidates`, build an entity lookup from the `entities` array in the current `process_turn` response (`entity.id` → `Entity` object). For each candidate, resolve `candidate.entity_id` to its `Entity`. Compare the entity's `canonical` path against paths in `unknown_claim_paths` using tiered matching:

  1. **Exact path:** `Entity.canonical` equals an `unknown_claim_paths` entry (case-insensitive)
  2. **Component-boundary suffix:** `Entity.canonical` ends with an `unknown_claim_paths` entry at a `/` boundary (e.g., canonical `src/config/types.py` matches entry `config/types.py`)
  3. **Basename:** `Entity.canonical` basename equals the basename of an `unknown_claim_paths` entry

  **Normalization (both sides):** Strip leading `./`, collapse `//` to `/`, compare case-insensitively.

  **Tie-break:** Match tier (lower = stronger) → `rank` (lowest wins).

  **No match:** If no candidates match any `unknown_claim_paths` entry, fall back to normal priority ranking.

  **Selection tracking:** When a candidate is selected via unknown-provenance priority, persist `matched_unknown_path` (the specific `unknown_claim_paths` entry that caused the priority boost) in per-turn state.

- **Step 4 (Scout — clearing):** After a successful scout execution (Step 4f success path), if `matched_unknown_path` is set for this turn, remove that specific entry from `unknown_claim_paths`. Only clear the entry that caused the priority boost — do not clear based on coincidental entity path matches from normal-ranked scouts. Note: `unknown_claim_paths` stores paths, not individual claims. Multiple `[SRC:unknown]` claims citing the same file are coalesced at path level — one successful scout retires priority for that file. This is intentional; claim-level granularity is deferred.

- **Step 6 (Compose follow-up):** See unknown-provenance sub-item in Step 6 priority list below.

`[SRC:unknown]` is an assembler-assigned tag indicating the gatherer did not follow its output format. Scouting converts this quality signal into dialogue-level recovery — the agent verifies the claim's evidence surface directly rather than relying on incorrect metadata.
```

**Step 5: Insert unknown-provenance priority in Step 6**

At lines 350-354, find the full numbered priority list in Step 6:
```
1. **Scout evidence** (if Step 4 produced results): Frame a question around `evidence_wrapper` using the evidence shape below
2. **Unresolved items** from `validated_entry.unresolved`
3. **Unprobed claims** tagged `new` in `validated_entry.claims`
4. **Weakest claim** derived from accumulated `turn_history` claim records (least-supported, highest-impact). Scan `validated_entry.claims` across all turns in `turn_history` — the weakest claim is the one with the fewest `reinforced` statuses across all turns in `turn_history`, not a value derived from aggregate counters in `cumulative`
5. **Posture-driven probe** from the patterns table
```

Replace with:
```
1. **Scout evidence** (if Step 4 produced results): Frame a question around `evidence_wrapper` using the evidence shape below
2. **Unresolved items** from `validated_entry.unresolved`
   - **Unknown-provenance claims** (if `unknown_claim_paths` is non-empty): Challenge the specific `[SRC:unknown]` claim text from the briefing. Frame the question to probe the claim's evidence surface — the goal is to verify or refute the untagged claim, not to ask a general question. When scout evidence comes from an unknown-provenance-triggered scout, the follow-up must target that specific claim. Note: unknown-provenance claims are sourced from the briefing (`unknown_claim_paths`), not from `validated_entry.unresolved`.
3. **Unprobed claims** tagged `new` in `validated_entry.claims`
4. **Weakest claim** derived from accumulated `turn_history` claim records (least-supported, highest-impact). Scan `validated_entry.claims` across all turns in `turn_history` — the weakest claim is the one with the fewest `reinforced` statuses across all turns in `turn_history`, not a value derived from aggregate counters in `cumulative`
5. **Posture-driven probe** from the patterns table
```

**Step 6: Verify all edits**

Read the full file and verify:
- [ ] Phase 1 pointer references "Unknown-provenance claims" section
- [ ] State table has `unknown_claim_paths` row with "before Step 1" sequencing
- [ ] `entities` row added to Step 3 response table
- [ ] `template_candidates` field list says `entity_id` (not `entity_key`)
- [ ] "Unknown-provenance claims" section uses `entity_id` resolution via `entities` array
- [ ] Tiered matching with normalization is specified (no entity type precedence)
- [ ] Causal clearing with `matched_unknown_path` (not opportunistic)
- [ ] Standalone mode initialization present
- [ ] No-match fallback present
- [ ] Step 6 has unknown-provenance sub-bullet under item 2 (not "2b.")
- [ ] Items 4 (weakest claim) and 5 (posture-driven probe) preserved
- [ ] No remaining references to `entity_key` on `TemplateCandidate` in the file

**Step 7: Commit**

```bash
git add packages/plugins/cross-model/agents/codex-dialogue.md
git commit -m "fix(cross-model): rewrite unknown-provenance scouting with entity resolution

Replace broken entity_key references (field doesn't exist on
TemplateCandidate) with entity_id → Entity resolution using tiered
path matching. Add entities row to response table, normalization rules,
causal clearing mechanism, standalone mode initialization, Phase 1
pointer, and Step 6 unknown-provenance sub-item."
```

---

## Task 2: Fix 3c null initialization in SKILL.md (C2)

**Files:**
- Modify: `packages/plugins/cross-model/skills/dialogue/SKILL.md:114`

**Context:** Step 3c sets `seed_confidence` and `low_seed_confidence_reasons` but never explicitly sets `provenance_unknown_count = null`. The pipeline state docs (lines 140-144) define null semantics, but the 3c instruction text doesn't state it. An implementing agent could default to `0` instead of `null`, causing the schema auto-bump to fire incorrectly.

**Step 1: Add explicit null assignment**

At line 114, find:
```
Set `seed_confidence` to `low` with `low_seed_confidence_reasons: ["zero_output"]`. Skip steps 3d through 3h (including 3h-bis), Step 4, and Step 4b.
```

Replace with:
```
Set `seed_confidence` to `low` with `low_seed_confidence_reasons: ["zero_output"]`. Set `provenance_unknown_count` to `null` (3h-bis is skipped, so provenance validation never ran). Skip steps 3d through 3h (including 3h-bis), Step 4, and Step 4b.
```

**Step 2: Verify**

Read line 114 and confirm `provenance_unknown_count` is explicitly set to `null`.

**Step 3: Commit**

```bash
git add packages/plugins/cross-model/skills/dialogue/SKILL.md
git commit -m "fix(cross-model): explicitly set provenance_unknown_count null in 3c

Step 3c is a terminal early-exit that skips 3h-bis. The null assignment
was implied by pipeline state docs but not stated in the instruction
text, risking a 0-vs-null confusion that would corrupt the schema
version auto-bump."
```

---

## Task 3: Add SRC to metadata fields in tag-grammar.md (I1)

**Files:**
- Modify: `packages/plugins/cross-model/skills/dialogue/references/tag-grammar.md:13` (content field terminator)
- Modify: `packages/plugins/cross-model/skills/dialogue/references/tag-grammar.md:44` (parse rule 6)
- Modify: `packages/plugins/cross-model/skills/dialogue/references/tag-grammar.md:46` (parse rule 8)

**Context:** The content field description (line 13) lists terminators as `(@, AID:, TYPE:)` but omits `SRC:`. The Codex collaborative dialogue resolved: use bracketed `[SRC:<source>]` form (matching live syntax in tagged lines) and unify terminology to "metadata field" throughout. The existing bare terminators (`@`, `AID:`, `TYPE:`) match their live syntax; SRC's live syntax is bracketed (`[SRC:code]`), so its terminator form should be bracketed too.

**Step 1: Update content field terminator**

At line 13, find:
```
- `<content>` — required. The finding text. Everything between the tag colon and the first metadata marker (`@`, `AID:`, `TYPE:`), or end of line.
```

Replace with:
```
- `<content>` — required. The finding text. Everything between the tag colon and the first metadata field (`@`, `AID:`, `TYPE:`, `[SRC:`), or end of line.
```

**Step 2: Update parse rule 6 terminology**

At line 44, find:
```
6. Multiple metadata markers on one line: parse left-to-right, first match wins for each field type.
```

Replace with:
```
6. Multiple metadata fields on one line: parse left-to-right, first match wins for each field type.
```

**Step 3: Update parse rule 8 SRC form**

At line 46, find:
```
8. `SRC:` values must be one of `code`, `docs`. `unknown` is assembler-assigned only — if a gatherer emits `SRC:unknown`, treat it as a missing SRC tag (the assembler will assign `[SRC:unknown]` in step 8).
```

Replace with:
```
8. `[SRC:<source>]` values must be one of `code`, `docs`. `unknown` is assembler-assigned only — if a gatherer emits `[SRC:unknown]`, treat it as a missing SRC tag (the assembler will assign `[SRC:unknown]` in step 8).
```

**Step 4: Commit**

```bash
git add packages/plugins/cross-model/skills/dialogue/references/tag-grammar.md
git commit -m "fix(cross-model): add [SRC:] to content field metadata fields list

Use bracketed [SRC:] form matching live syntax in tagged lines.
Unify terminology from 'metadata marker' to 'metadata field'
throughout parse rules."
```

---

## Task 4: Add content_conflict_count metric in SKILL.md (I2)

**Files:**
- Modify: `packages/plugins/cross-model/skills/dialogue/SKILL.md:98`

**Context:** Step 3b's retry-wins tie-break silently drops content-different duplicates (same tag type + citation, different content text). The Codex dialogue converged on adding a pipeline-local diagnostic counter (not an OPEN line, which would contaminate the briefing). Analytics schema promotion is deferred.

**Step 1: Add content_conflict_count instruction**

At line 98, find the last sentence of Step 3b:
```
If still below 4 after retry, proceed with available output.
```

Replace with:
```
If still below 4 after retry, proceed with available output.

**Content conflict tracking:** When the retry-wins rule resolves a duplicate (same tag type + normalized citation, different content text), increment `content_conflict_count` (pipeline-local diagnostic counter, initialized to `0`). This counter is not emitted to analytics in the current schema — it exists for pipeline observability only.
```

**Step 2: Commit**

```bash
git add packages/plugins/cross-model/skills/dialogue/SKILL.md
git commit -m "fix(cross-model): add content_conflict_count for retry tie-break auditing

When 3b retry-wins resolves content-different duplicates, track the
count as a pipeline diagnostic. Does not emit to analytics schema —
deferred to future PR."
```

---

## Task 5: Add step numbering crosswalk (I3)

**Files:**
- Modify: `packages/plugins/cross-model/skills/dialogue/SKILL.md` (after line 92)
- Modify: `packages/plugins/cross-model/skills/dialogue/references/tag-grammar.md` (after line 48)

**Context:** SKILL.md uses step IDs `3a`-`3h-bis`, `Step 4`, `Step 4b`. tag-grammar.md uses assembly processing order numbers 1-9. No cross-reference exists. The Codex dialogue converged on a crosswalk table (not renumbering, which would break existing references).

**Step 1: Add crosswalk table to SKILL.md**

After line 92 (the line reading `Perform **deterministic, non-LLM assembly** of gatherer outputs. Reference: `references/tag-grammar.md` for full grammar and edge cases.`), insert:

```markdown

**Step ID crosswalk** (SKILL.md ↔ tag-grammar.md assembly processing order):

| SKILL.md | tag-grammar.md | Operation |
|----------|---------------|-----------|
| 3a | 1 | Parse |
| 3b | 2 | Retry |
| 3c | 3 | Zero-output fallback |
| 3d | 4 | Discard |
| 3e | 5 | Cap |
| 3f | 6 | Sanitize |
| 3g | 7 | Dedup |
| 3h-bis | 8 | Validate provenance |
| 3h | 9 | Group |

```

**Step 2: Add pointer in tag-grammar.md**

After line 48 (the `## Assembly Processing Order` heading), find:
```
When the `/dialogue` skill assembles gatherer outputs:
```

Replace with:
```
When the `/dialogue` skill assembles gatherer outputs (SKILL.md steps 3a-3h map to steps 1-9 below; see SKILL.md Step 3 for the full crosswalk table):
```

**Step 3: Commit**

```bash
git add packages/plugins/cross-model/skills/dialogue/SKILL.md packages/plugins/cross-model/skills/dialogue/references/tag-grammar.md
git commit -m "fix(cross-model): add step numbering crosswalk between SKILL.md and tag-grammar.md"
```

---

## Task 6: Extract _is_non_negative_int helper in emit_analytics.py (S1)

**Files:**
- Modify: `packages/plugins/cross-model/scripts/emit_analytics.py`
- Test: `tests/test_emit_analytics.py` (existing 93 tests must pass)

**Context:** The schema auto-bump (`is not None` on line 361) accepts bools, strings, and other non-int types. The `_COUNT_FIELDS` validation loop (lines 444-450) already has the correct bool/int/negative check but only runs during `validate()`, not at build time. The Codex dialogue converged on extracting a shared helper used in both locations. **Note:** This is a behavior change for the auto-bump (tightens the predicate to reject non-int types), not a pure refactor. The validation loop replacement is a pure refactor.

**Step 1: Add helper function**

After the `_VALID_TERMINATION_REASONS` set (around line 62), add:

```python

def _is_non_negative_int(value: object) -> bool:
    """Check value is a non-negative int, excluding bool."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0

```

**Step 2: Update auto-bump predicate**

At line 361, find:
```python
    # Schema version auto-bump (§4.4): non-null provenance → 0.2.0
    if event.get("provenance_unknown_count") is not None:
        event["schema_version"] = "0.2.0"
```

Replace with:
```python
    # Schema version auto-bump (§4.4): valid provenance count → 0.2.0
    if _is_non_negative_int(event.get("provenance_unknown_count")):
        event["schema_version"] = "0.2.0"
```

**Step 3: Update _COUNT_FIELDS validation loop**

At lines 444-450, find:
```python
    # Count fields >= 0
    for field in _COUNT_FIELDS:
        value = event.get(field)
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value < 0
        ):
            raise ValueError(f"{field} must be non-negative int, got {value!r}")
```

Replace with:
```python
    # Count fields >= 0
    for field in _COUNT_FIELDS:
        value = event.get(field)
        if value is not None and not _is_non_negative_int(value):
            raise ValueError(f"{field} must be non-negative int, got {value!r}")
```

**Step 4: Run tests**

Run: `cd packages/plugins/cross-model && uv run pytest ../../../tests/test_emit_analytics.py -v`
Expected: All 93 tests pass. The validation loop change is a pure refactor. The auto-bump change tightens the predicate (previously `is not None`, now `_is_non_negative_int`) — no existing test exercises bool/string values in the auto-bump path, so all 93 pass.

**Step 5: Commit**

```bash
git add packages/plugins/cross-model/scripts/emit_analytics.py
git commit -m "fix(cross-model): extract _is_non_negative_int helper for type-safe auto-bump

The schema auto-bump previously used 'is not None' which accepted
bools, strings, and other non-int types. Now uses shared helper that
rejects non-int types at build time. The validation loop replacement
is a pure refactor; the auto-bump change is a behavior tightening."
```

---

## Task 7: Add OPEN template to falsifier no-assumptions fallback (S2)

**Files:**
- Modify: `packages/plugins/cross-model/agents/context-gatherer-falsifier.md:50-56`

**Context:** When the falsifier's no-assumptions fallback activates, it restricts exploration to rationale surfaces only (docs, plans, decisions). There's no signal to downstream consumers that code exploration was blocked. The Codex dialogue converged on a required deterministic OPEN line.

**Step 1: Add OPEN emission rule**

At lines 50-56, find:
```
1. Explore **rationale surfaces only**: `docs/decisions/`, `docs/plans/`, `docs/learnings/`, `CLAUDE.md`, `README.md`, and architectural files at repository root.
2. Do NOT explore code files, test files, or config files — those are the code explorer's domain.
3. Emit `CLAIM` and `OPEN` items about design rationale, architectural decisions, and documented constraints relevant to the question.
4. Tag every `CLAIM` line with `[SRC:docs]` — all CLAIMs in the fallback path are documentation-sourced because only rationale surfaces are explored.
5. Do **not** emit `COUNTER` or `CONFIRM` — these require assumption IDs.
```

Replace with:
```
1. Explore **rationale surfaces only**: `docs/decisions/`, `docs/plans/`, `docs/learnings/`, `CLAUDE.md`, `README.md`, and architectural files at repository root.
2. Do NOT explore code files, test files, or config files — those are the code explorer's domain.
3. **Always** emit this OPEN line first: `OPEN: No-assumptions fallback active — scoped to rationale surfaces only; code/test/config exploration skipped`
4. Emit `CLAIM` and `OPEN` items about design rationale, architectural decisions, and documented constraints relevant to the question.
5. Tag every `CLAIM` line with `[SRC:docs]` — all CLAIMs in the fallback path are documentation-sourced because only rationale surfaces are explored.
6. Do **not** emit `COUNTER` or `CONFIRM` — these require assumption IDs.
```

**Step 2: Commit**

```bash
git add packages/plugins/cross-model/agents/context-gatherer-falsifier.md
git commit -m "fix(cross-model): add required OPEN signal for falsifier fallback restriction

When the no-assumptions fallback activates, emit a deterministic OPEN
line signaling that code exploration was skipped. Downstream consumers
can now distinguish 'found nothing in code' from 'was prohibited from
looking at code'."
```

---

## Task 8: Add mixed enum validation test (S3)

**Files:**
- Modify: `tests/test_emit_analytics.py` (after line 689)

**Context:** No test for mixed valid/invalid `low_seed_confidence_reasons` (e.g., `["few_files", "bad_reason"]`). The set-subtraction implementation handles it correctly, but a test prevents regressions from refactors.

**Step 1: Add parameterized test**

After `test_all_low_seed_confidence_reasons_accepted` (inside `TestValidate`), insert:

```python

    @pytest.mark.parametrize("reasons", [
        ["few_files", "bad_reason"],
        ["thin_citations", "provenance_violations", "oops"],
        ["bad_reason", "few_files"],
    ])
    def test_mixed_valid_invalid_low_seed_confidence_reasons_rejected(
        self, reasons: list[str]
    ) -> None:
        """Mixed valid and invalid low_seed_confidence_reasons are rejected."""
        event = MODULE.build_dialogue_outcome(_dialogue_input())
        event["low_seed_confidence_reasons"] = reasons
        with pytest.raises(ValueError, match="invalid low_seed_confidence_reasons"):
            MODULE.validate(event, "dialogue_outcome")
```

**Step 2: Run tests**

Run: `cd packages/plugins/cross-model && uv run pytest ../../../tests/test_emit_analytics.py::TestValidate::test_mixed_valid_invalid_low_seed_confidence_reasons_rejected -v`
Expected: 3 parameterized cases PASS.

Run: `cd packages/plugins/cross-model && uv run pytest ../../../tests/test_emit_analytics.py -v`
Expected: 96 tests pass (93 existing + 3 new parameterized).

**Step 3: Commit**

```bash
git add tests/test_emit_analytics.py
git commit -m "test(cross-model): add mixed valid/invalid enum regression tests

Parameterized test for low_seed_confidence_reasons with partial valid
and partial invalid values. Prevents regressions if set-subtraction
validation is refactored."
```

---

## Task 9: Add non-int pipeline type regression test (S4)

**Files:**
- Modify: `tests/test_emit_analytics.py` (after line 420)
- **Depends on:** Task 6 (tests the `_is_non_negative_int` helper behavior)

**Context:** After Task 6's helper fix, bool `pipeline.provenance_unknown_count` should NOT trigger the schema auto-bump. Previously, `True` (a bool, which is an int subclass) would pass the `is not None` check and bump the schema. The helper rejects bools. This is a behavior change test, not a regression test for existing behavior.

**Step 1: Add pipeline type tests**

After `test_provenance_unknown_count_explicit_none_schema_stays` (inside `TestBuildDialogueOutcome`, before `TestBuildConsultationOutcome`), insert:

```python

    def test_provenance_unknown_count_bool_pipeline_no_schema_bump(self) -> None:
        """Bool pipeline.provenance_unknown_count does NOT trigger schema bump."""
        pipeline = {**SAMPLE_PIPELINE, "provenance_unknown_count": True}
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        # Helper rejects bool — schema stays at base version
        assert event["schema_version"] == "0.1.0"

    def test_provenance_unknown_count_string_pipeline_no_schema_bump(self) -> None:
        """String pipeline.provenance_unknown_count does NOT trigger schema bump."""
        pipeline = {**SAMPLE_PIPELINE, "provenance_unknown_count": "3"}
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        # Helper rejects string — schema stays at base version
        assert event["schema_version"] == "0.1.0"

    def test_provenance_unknown_count_float_pipeline_no_schema_bump(self) -> None:
        """Float pipeline.provenance_unknown_count does NOT trigger schema bump."""
        pipeline = {**SAMPLE_PIPELINE, "provenance_unknown_count": 0.0}
        event = MODULE.build_dialogue_outcome(_dialogue_input(pipeline=pipeline))
        # Helper rejects float — schema stays at base version
        assert event["schema_version"] == "0.1.0"
```

**Step 2: Run tests**

Run: `cd packages/plugins/cross-model && uv run pytest ../../../tests/test_emit_analytics.py::TestBuildDialogueOutcome::test_provenance_unknown_count_bool_pipeline_no_schema_bump ../../../tests/test_emit_analytics.py::TestBuildDialogueOutcome::test_provenance_unknown_count_string_pipeline_no_schema_bump ../../../tests/test_emit_analytics.py::TestBuildDialogueOutcome::test_provenance_unknown_count_float_pipeline_no_schema_bump -v`
Expected: 3 tests PASS.

Run: `cd packages/plugins/cross-model && uv run pytest ../../../tests/test_emit_analytics.py -v`
Expected: 99 tests pass (93 existing + 3 from Task 8 + 3 from Task 9).

**Step 3: Commit**

```bash
git add tests/test_emit_analytics.py
git commit -m "test(cross-model): add non-int pipeline type tests for auto-bump behavior

Verify bool, string, and float pipeline.provenance_unknown_count do not trigger
schema version auto-bump after _is_non_negative_int helper extraction.
These test a behavior change (not a regression) — the old 'is not None'
predicate would have bumped for these types."
```

---

## Task 10: Fix degraded exit code documentation (emerged)

**Files:**
- Modify: `packages/plugins/cross-model/skills/dialogue/SKILL.md` (Step 7c)

**Context:** The original emit-analytics implementation plan specified `exit_code == 0` for degraded, but the implementation uses `exit_code == 2`. The test (`test_degraded_on_write_failure`) correctly asserts `exit_code == 2`, matching the implementation. The SKILL.md Step 7c section may have stale language about degraded status.

**Step 1: Verify SKILL.md Step 7c accuracy**

Read the Step 7c section in SKILL.md and check whether the degraded description matches the implementation:
- Implementation: `_process` returns exit code `2` on degraded (emit_analytics.py:545)
- SKILL.md should say: degraded means input was valid but log write failed — warn user, do not retry

If the SKILL.md text is already accurate (it describes degraded semantics, not exit codes), no edit is needed — just verify and note.

**Step 2: Verify no stale exit code references in SKILL.md**

Search for `exit` or `exit_code` or `return 0` in SKILL.md's Step 7 section. The skill describes the script's stdout JSON status, not its exit code — so stale references are unlikely. If found, update them.

**Step 3: Commit (if changes made)**

```bash
git add packages/plugins/cross-model/skills/dialogue/SKILL.md
git commit -m "fix(cross-model): correct degraded status documentation in Step 7c"
```

If no changes needed, skip this commit.

---

## Final Verification

Run: `cd packages/plugins/cross-model && uv run pytest ../../../tests/test_emit_analytics.py -v`
Expected: 99 tests pass (93 existing + 3 from Task 8 + 3 from Task 9)

Run: `cd packages/plugins/cross-model && uv run ruff check scripts/ ../../../tests/test_emit_analytics.py`
Expected: No errors

Verify no stale `entity_key` references on `TemplateCandidate`:
Run: `grep -r "entity_key" packages/plugins/cross-model/agents/codex-dialogue.md`
Expected: Zero matches (all replaced with `entity_id` resolution)

## Summary of Deliverables

| File | New/Modified | What This Plan Adds |
|------|-------------|---------------------|
| `agents/codex-dialogue.md` | Modified | C1: entity resolution via entities[], tiered matching, causal clearing, standalone mode, Step 6 unknown-provenance sub-item, state table row, field list fix, entities row, Phase 1 pointer |
| `skills/dialogue/SKILL.md` | Modified | C2: explicit null in 3c. I2: content_conflict_count metric. I3: crosswalk table. T10: degraded doc check |
| `skills/dialogue/references/tag-grammar.md` | Modified | I1: [SRC:] in metadata fields + terminology. I3: crosswalk pointer |
| `agents/context-gatherer-falsifier.md` | Modified | S2: required OPEN template in fallback |
| `scripts/emit_analytics.py` | Modified | S1: `_is_non_negative_int` helper (behavior change for auto-bump, refactor for validation) |
| `tests/test_emit_analytics.py` | Modified | S3: 3 parameterized mixed-enum tests. S4: 3 non-int pipeline behavior tests |

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| v1 | 2026-02-20 | Initial plan (9 tasks) |
| v2 | 2026-02-20 | Revised after adversarial review (2 blockers, 3 high, 4 medium) and open questions dialogue (3 resolved, 2 emerged). 14 changes applied. Now 10 tasks. |
| v3 | 2026-02-20 | Final adversarial review fixes: test paths (../../ →../../../), standalone mode wording, Step 5 source clarifier, path-level coalescing note, float auto-bump test (+1 test → 99 total), text anchors for Tasks 8/9. 6 changes applied. Post-review: file-level parallel execution dependencies, Step 1 anchor precision, Step 5 line range correction. 4 changes applied. |
