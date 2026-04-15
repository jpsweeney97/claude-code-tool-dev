---
title: "Dialogue Turn Contract"
type: reference
authority: production-local
source: packages/plugins/codex-collaboration/skills/dialogue-codex/SKILL.md
extracted_at: 2026-04-14
plan: docs/plans/2026-04-13-t04-v1-production-dialogue-scoping-plan.md
---

# Dialogue Turn Contract

Production-local authoritative turn contract for the per-turn verification loop in codex-collaboration dialogues. Extracted from the `dialogue-codex` skill body at v1 implementation start.

**Authority scope.** This document is normative for: target selection, claim classification, claim registration, status derivation, disposition enum, emission shape (13 fields), terminalization, and budget semantics. The orchestrator cites this document and executes it verbatim.

**Not in scope.** The production synthesis artifact schema (plan §3.2), inline initial scouting (plan §6.2), and `agent_local` mode emission (T5) are owned by the orchestrator body, not this document.

**Extraction discipline.** Sections 1–9 are extracted from the `dialogue-codex` skill body with zero behavioral edits. Shakedown-specific framing (tool MCP names, prohibited artifact names, exemplars) is not included. The following are additions, not modifications to extracted text — each is marked inline:
- T1–T6 adoption table and invariants table (above extracted sections)
- Scope-breach row in §9 "When to Terminate" table *(marked "T1/Risk G addition")*
- Scope-Breach Terminalization subsection in §9 *(marked "T1/Risk G addition")*
- TerminationCode Enum subsection in §9 *(marked "T1")*
- Terminal-turn `<PRODUCTION_SYNTHESIS>` sentinel exception in §8 *(marked "Production addition")*
- Parse-failure exemption for `<PRODUCTION_SYNTHESIS>` in §8
- Sentinel-name note in §8 *(one-line annotation)*

## T1–T6 Semantic Adoption

| Semantic | Contract source | Manifestation in this document |
|---|---|---|
| T1: Structured termination | `t04-t1-structured-termination-contract.md` | TerminationCode enum (§9); `converged` is its mechanical projection |
| T2: Synthetic claim and closure | `t04-t2-synthetic-claim-and-closure-contract.md` | `minimum_fallback` provenance tagging and exclusion rules (§3) |
| T3: Deterministic referential continuity | `t04-t3-deterministic-referential-continuity.md` | Stable claim IDs across turns; merger checks prevent duplication (§3) |
| T4: Scouting position and evidence provenance | `t04-t4-scouting-position-and-evidence-provenance/` | Query coverage requirements, falsification design, query target format (§5) |
| T5: Mode strategy | `t04-t5-mode-strategy.md` | `mode = "agent_local"`, `mode_source = null` — orchestrator-owned, not in this contract |
| T6: Composition review | Closed (review at `t04-t6` composition review) | General design validation; no specific per-turn manifestation |

## Invariants

| Risk | Invariant | Enforcement |
|---|---|---|
| F | Canonical ledger block survives context-window compression | Each emitted state block contains the full `claims` array, not a diff from the prior turn. State blocks are self-contained per turn. |
| G | Scope-breach termination is separate from convergence | Breach count exceeding threshold produces `termination_code = "scope_breach"`, `converged = false`. Breach count is orchestrator-internal state, not an emitted field. See §9. |
| J | Structured per-scout evidence record | Each scouted turn emits `queries`, `citations`, `disposition`. Together these constitute the per-scout evidence record, reconstructable from emitted fields without a separate evidence artifact. |
| K | Cross-turn change tracking | `effective_delta` (per-turn) and `effective_delta_overall` (cumulative, in epilogue) track verification-state changes across turns. |

---

## 1. Per-Turn Loop

Execute steps 1–7 in this exact order every turn after receiving a Codex reply.

| Step | Action |
|------|--------|
| 1 | Extract factual claims from Codex reply |
| 2 | Register claims: Phase 1 (concessions, reinforcements), Phase 1.5 (dead-referent reclassification), Phase 2 (new/revised with merger checks) |
| 3 | Compute counters and per-turn `effective_delta` |
| 4 | Control decision: continue or conclude |
| 5 | Scout (if not skipped — see skip conditions below) |
| 6 | Compose follow-up using current ledger/evidence state |
| 7 | Send follow-up via `codex.dialogue.reply` |

**Skip conditions for step 5 (scouting):**
- Control decision is `conclude`
- Evidence budget exhausted (`evidence_count >= max_evidence`)
- Effort budget exhausted (`scout_budget_spent >= max_scout_rounds`)
- No scoutable targets remain (all claims at priority 4)

When scouting is skipped, also skip steps 6–7 if the control decision is `conclude`. If scouting is skipped due to budget exhaustion but the control decision is NOT conclude, steps 6–7 still execute (subject to the terminalization window — see section 9).

Step 5e (evidence block re-emission) MUST happen BEFORE step 6 (follow-up composition). The state block captures the scouting result; the follow-up uses it.

---

## 2. Claim Classes

Three classes. Determine class at registration time (Phase 2), before creating the verification entry.

### Scoutable

Entity grammar: `<path_or_symbol>` or `<path_or_symbol> <qualifier>`

The claim references a concrete, repo-searchable entity. Standard scouting applies: definition query + falsification query.

**Classification test:** You can identify (1) at least one entity fitting the grammar, (2) a definition query executable via Read/Grep, and (3) a falsification query that would surface contradicting evidence.

### Relational-Scoutable

Entity grammar: `<entity> x <entity>` (the `x` character represents a relationship)

The claim describes a relationship between two concrete entities. The primary entity (left of `x`) determines scouting focus. The definition query targets the primary entity's implementation. The falsification query targets the relationship — e.g., if the claim is "X delegates to Y," the falsification targets "X uses something other than Y."

### Not Scoutable

No entity grammar applies. The claim is an abstract interpretation, meta-property, or cross-system assertion with no repo-searchable entity.

**Classification test:** If ANY of the three criteria (entity, definition query, falsification query) cannot be identified, classify as `not_scoutable`.

Not-scoutable claims enter the ledger at terminal status `not_scoutable` with `scout_attempts: 0`. They appear in counters and the `claims` array. They are never selected for scouting. Do NOT discard them.

---

## 3. Claim Registration (Within-Turn Processing)

Process in this exact order within each turn:

### Phase 1: Concessions and Reinforcements

- **Conceded claims**: Codex withdrew or abandoned the claim. Remove from verification state. Increment `conceded` counter.
- **Reinforced claims**: Codex restated an existing claim. Share the original's ClaimRef. Do NOT create a new verification entry.

### Phase 1.5: Dead-Referent Reclassification

If a claim references another claim (via `[ref:]` annotation or semantic dependency) and ALL occurrences of the referenced claim have been conceded, reclassify the referencing claim as `new`.

### Phase 2: New and Revised Claims

1. **Merger check**: If a new claim has the same `claim_key` AND the same normalized `claim_text` as a live occurrence, merge — do not create a new entry.
2. **Classification**: Apply the three-class test (section 2). Classification happens here, before the verification entry is created.
3. **Entry creation**: Scoutable claims enter at `unverified`, `evidence_indices: []`, `scout_attempts: 0`. Not-scoutable claims enter at `not_scoutable`, `evidence_indices: []`, `scout_attempts: 0` (terminal).

### Zero-Claim Fallback

If turn extraction yields zero distinct raw claims, create exactly one `minimum_fallback` claim from the turn's position text. This preserves the minimum-one-claim invariant.

`minimum_fallback` exclusion rules — these are critical:
- Excluded from counter computation for `new_claims`, `revised`, `conceded`
- Do NOT enter verification state or the scouting pipeline
- Do NOT appear in the emitted `claims` array (the `claims` array represents the verification ledger; `minimum_fallback` claims have no legal emitted status)
- Do NOT count toward `total_claims` in `counters`
- An all-fallback turn produces `quality: SHALLOW`, `effective_delta: STATIC`

A zero-claim turn is transcript-indistinguishable from an omitted fallback (both produce an empty `claims` array and `total_claims: 0`). This branch is verified by source review, not transcript inspection.

---

## 4. Target Selection

Select at most one scout target per round. Use this priority table:

| Priority | Status | Condition | Action |
|----------|--------|-----------|--------|
| 1 | `unverified` | `scout_attempts == 0` | Scout |
| 2 | `conflicted` | `scout_attempts < 2` | Scout |
| 3 | `ambiguous` | `scout_attempts < 2` | Scout |
| 4 (skip) | `supported`, `contradicted`, `not_scoutable` | Terminal | Never scout |
| 4 (skip) | `unverified` | `scout_attempts >= 1` (first scout was `not_found`) | Skip |
| 4 (skip) | `conflicted`, `ambiguous` | `scout_attempts >= 2` | Skip |

**Sort within priority level:** `introduction_turn` ascending, then `claim_key` lexicographic, then `occurrence_index` ascending.

### Graduated Attempt Limits

| After first scout returns... | Max attempts | Rationale |
|-----------------------------|-------------|-----------|
| `not_found` | 1 | Nothing to find. Do NOT retry |
| `ambiguous` | 2 | Evidence real but inconclusive — second attempt may resolve |
| `conflicted` | 2 | Evidence real but mixed — second attempt may resolve |
| `supports` / `contradicts` | 1 | Terminal. Never re-scout |

---

## 5. Scouting Queries

### Coverage Requirements

Each scouting round: 2–5 tool calls total.

| Type | Required | Purpose |
|------|----------|---------|
| `definition` | At least 1 | Locate the entity's implementation |
| `falsification` | At least 1 | Target a specific expected-contradicting condition |
| `supplementary` | Optional | Additional context |

Hard cap: 5 tool calls per round.

### Falsification Design

The falsification query MUST target a specific expected-contradicting condition that is distinct from the definition query. A falsification query that searches for the same entity as the definition query (with no contradicting condition encoded in the pattern) fails the diversity check.

For relational claims: the definition query targets the primary entity (left of `x`). The falsification query targets the relationship. The query set must address both entities.

### Second-Attempt Diversity

When a claim gets a second scout attempt, at least one mandatory-type query (definition or falsification) MUST use query text that does not appear in any first-round query of the same type. The actual search string must change, not just the type label. Supplementary queries do not count toward diversity.

### Query Target Format

The `target` field in emitted `queries` reflects the effective tool input. All file and directory paths in `target` are relative to `scope_root`:

- For Read: `<file>:<lines>` (e.g., `mcp_server.py:115-134`)
- For Grep: `pattern:<search> path:<file_or_dir>` (e.g., `pattern:DialogueController\( path:mcp_server.py`)
- For Glob: `pattern:<glob> path:<dir>` (e.g., `pattern:*.py path:server/`)

Do NOT use absolute paths in `target`. The `scope_root` field provides the absolute base; `target` paths are relative to it.

Every Grep and Glob call MUST include a `path` parameter in the actual tool call. Pathless calls are denied by containment. The `scope_root` field in the state block records where scouting occurred — it does NOT substitute for the `path` parameter in the tool call.

---

## 6. Status Derivation

Single mechanical rule. Used for verification state updates, target selection, and counter computation.

```
effective = set()
for each evidence_index in claim's evidence_indices:
    d = evidence_log[index].disposition
    if d == "conflicted":
        add "supports" and "contradicts" to effective
    elif d in ("supports", "contradicts", "ambiguous"):
        add d to effective
    # "not_found" is EXCLUDED — does not enter effective set

if "contradicts" in effective and "supports" in effective:
    status = "conflicted"
elif "contradicts" in effective:
    status = "contradicted"
elif "supports" in effective:
    status = "supported"
elif "ambiguous" in effective:
    status = "ambiguous"
else:
    status = "unverified"
```

Key rules:
- `not_found` does NOT affect the effective set. It increments `scout_attempts` and appends to `evidence_indices`, but does not change status.
- `conflicted` disposition expands to BOTH `supports` and `contradicts` in the effective set.
- After a `not_found` on first attempt: claim stays `unverified` with `scout_attempts: 1`, which is priority 4 (skip). Do NOT retry.

---

## 7. Disposition Enum

`"supports"` | `"contradicts"` | `"conflicted"` | `"ambiguous"` | `"not_found"` | `null`

- `null` only on non-scouting turns
- `supports`: evidence confirms the claim
- `contradicts`: evidence refutes the claim
- `conflicted`: evidence both supports and contradicts (e.g., mechanism exists but qualifier is wrong)
- `ambiguous`: evidence found but inconclusive
- `not_found`: scouting queries returned no usable evidence

---

## 8. Emission Contract

### Sentinel Format

Every turn emits exactly one state block in this exact format:

```
<SHAKEDOWN_TURN_STATE>
```json
{ ... }
```
</SHAKEDOWN_TURN_STATE>
```

All prose follows the closing sentinel. Do NOT emit any other bare JSON fence in the turn. Do NOT emit more than one state block per turn.

The `SHAKEDOWN_TURN_STATE` sentinel name is inherited from the shakedown emission format. Production runs use the same sentinel for rubric compatibility (plan §8.3). Post-v1 cleanup may rename it.

**Terminal turn exception — production synthesis sentinel.** *(Production addition — not in source.)* On the terminal turn only, after the state block and its prose, the orchestrator MUST also emit the production synthesis artifact wrapped in a `<PRODUCTION_SYNTHESIS>` sentinel. This is the only permitted second JSON fence in any turn. The `<PRODUCTION_SYNTHESIS>` sentinel will be present in the raw transcript JSONL (SubagentStop copies verbatim), but rubric inspection evaluates only `<SHAKEDOWN_TURN_STATE>` sentinels and ignores `<PRODUCTION_SYNTHESIS>` content. The parent `/dialogue` skill extracts the artifact by locating the `<PRODUCTION_SYNTHESIS>` sentinel in the orchestrator's output.

### State Object Fields

Every emitted state block, all 13 fields present:

| Field | Type | Rules |
|-------|------|-------|
| `turn` | int | Monotonically increasing. First emitted state block is `turn: 2` (the first post-reply verification turn). `turn: 1` is the opening send to Codex, which does not emit a state block. |
| `scouted` | bool | `true` if scouting occurred this turn |
| `target_claim_id` | int or null | Claim ID scouted, null if not scouting |
| `target_claim` | string or null | Claim text scouted, null if not scouting |
| `scope_root` | string or null | Absolute path where scouting occurred, null if not scouting |
| `queries` | list | Query objects `{type, tool, target}`. Empty `[]` if not scouting (NOT null) |
| `disposition` | string or null | Disposition enum value. `null` if not scouting |
| `citations` | list | Citation objects `{path, lines, snippet}`. Empty `[]` if not scouting (NOT null) |
| `claims` | list | All verification ledger entries: `{id, text, status, scout_attempts}` |
| `counters` | object | 8 fields (see below) |
| `effective_delta` | object | 8 fields, always PER-TURN delta (not cumulative) |
| `terminal` | bool | `true` only on the final turn |
| `epilogue` | object or null | Required when `terminal: true`, null otherwise |

### Counter Fields (exact set, in both `counters` and `effective_delta`)

`total_claims`, `supported`, `contradicted`, `conflicted`, `ambiguous`, `not_scoutable`, `unverified`, `evidence_count`

### Non-Scouting Turn Empty-Field Rules

When `scouted: false`, set these fields exactly:

| Field | Value |
|-------|-------|
| `target_claim_id` | `null` |
| `target_claim` | `null` |
| `scope_root` | `null` |
| `queries` | `[]` |
| `disposition` | `null` |
| `citations` | `[]` |

`claims`, `counters`, `effective_delta`, `turn`, `terminal`, `epilogue` are still populated normally.

### Parse-Failure Conditions

Any of these makes a turn invalid:

- Missing sentinel (`<SHAKEDOWN_TURN_STATE>` / `</SHAKEDOWN_TURN_STATE>`)
- More than one state block in a single turn
- Invalid JSON inside the sentinel
- Missing required keys (any of the 13 top-level fields)
- Wrong enum value or type (e.g., string where int expected, disposition outside the enum)
- `scouted: true` without required query coverage (missing definition or falsification)
- Terminal turn without `epilogue` (or `epilogue` non-null on a non-terminal turn)
- First emitted state block has `turn` != 2
- Non-monotonic `turn` counter on subsequent emitted turns
- Any bare JSON fence outside the sentinel-wrapped state block (the `<PRODUCTION_SYNTHESIS>` sentinel on the terminal turn is exempt — see Sentinel Format)

A turn that satisfies the positive field table but violates any of these conditions is still invalid.

---

## 9. Terminal Epilogue

### When to Terminate

| Condition | `converged` |
|-----------|-------------|
| Normal completion: no scoutable targets remain (all claims at priority 4 per section 4) AND no budget exhaustion triggered the terminalization path | `true` |
| Budget exhaustion (evidence or effort) — always, even if ledger stabilizes during the terminalization window | `false` |
| Scope-breach count exceeds threshold (Risk G) *(T1/Risk G addition — not in source)* | `false` |
| Dialogue-tool failure (`codex.dialogue.start` or `.reply` error) | `false` |
| Any other controlled early exit | `false` |

**"Stabilized" means:** No scoutable targets remain per the priority table in section 4 — all claims are at priority 4. This includes maxed-out `conflicted`/`ambiguous` at `scout_attempts >= 2`, and `unverified` at `scout_attempts >= 1` (first scout was `not_found`). A stabilized ledger MAY contain non-terminal statuses. `converged: true` means the verification program completed normally, not that all claims resolved.

### Budget Exhaustion Terminalization

Explicit turn accounting:

- **Turn N** (first budget-exhausted turn): Scouting is skipped because budget is exhausted. You may compose and send one follow-up to Codex to seek concessions or closure. This is the ONLY non-terminal follow-up permitted after budget exhaustion.
- **Turn N+1** (terminal): You receive Codex's reply and process claims normally. New scoutable claims enter as `unverified` but cannot be scouted (budget remains exhausted). New `not_scoutable` claims enter at terminal status per section 3. This turn MUST be terminal: set `terminal: true`, emit `epilogue` with `converged: false`, control decision `conclude`. Do NOT compose another follow-up.

There are exactly 2 assistant turns in the terminalization window: turn N (non-terminal, one follow-up) and turn N+1 (terminal, no follow-up). Do NOT emit a non-terminal turn at N+1.

Budget exhaustion always produces `converged: false`. This holds even if the ledger happens to stabilize during the terminalization window, because the run did not complete its verification program normally.

### Scope-Breach Terminalization *(T1/Risk G addition — not in source)*

When the orchestrator's scope-breach count exceeds the threshold defined in the orchestrator body (Risk G), terminate immediately:

- Set `terminal: true`.
- Emit `epilogue` with `converged: false`.
- `ledger_summary` describes the scope-breach condition.
- The breach count is orchestrator-internal state. It does NOT appear as an emitted field in the state block or epilogue.
- `termination_code = "scope_breach"` appears only in the production synthesis artifact (plan §3.2), not in the transcript epilogue.

### Dialogue-Tool Failure

If `codex.dialogue.start` or `codex.dialogue.reply` returns an error, emit a terminal turn immediately: `converged: false`, `ledger_summary` describes the failure (tool name, error message, turn at which failure occurred). Do NOT continue scouting after a dialogue-tool failure.

### Epilogue Schema

```json
{
  "ledger_summary": "Human-readable description of final verification state",
  "converged": true|false,
  "effective_delta_overall": {
    "total_claims": 0,
    "supported": 0,
    "contradicted": 0,
    "conflicted": 0,
    "ambiguous": 0,
    "not_scoutable": 0,
    "unverified": 0,
    "evidence_count": 0
  }
}
```

- `effective_delta_overall`: Cumulative delta across ALL turns
- Top-level `effective_delta`: Always per-turn (this turn's changes only)
- Non-terminal turns: `terminal: false`, `epilogue: null`

### TerminationCode Enum (T1)

The orchestrator computes a `termination_code` at terminalization. The epilogue's `converged: bool` is a mechanical projection of this code.

| Code | Condition | `converged` projection |
|---|---|---|
| `convergence` | Normal completion — no scoutable targets remain, no budget exhaustion | `true` |
| `budget_exhausted` | Evidence or effort budget exhaustion | `false` |
| `scope_breach` | Scope-breach count exceeds threshold | `false` |
| `error` | Dialogue-tool failure or unrecoverable error | `false` |

**Projection rule:** `converged = (termination_code == "convergence")`.

`termination_code` lives in the production synthesis artifact (plan §3.2), not in the transcript epilogue. The transcript epilogue carries only the projected `converged: bool` and the human-readable `ledger_summary`.

Enum values are lowercase string literals. The `convergence` code name is distinct from the `converged` boolean to avoid semantic confusion: `converged` means the verification program completed normally; `convergence` is the specific termination code that produces `converged: true`.
