# B4 `dialogue-codex` Conformance Checklist

**Date:** 2026-04-09
**Purpose:** Verification checklist for the `dialogue-codex` skill against the B1-load-bearing subset of the T4 scouting contract. Used during drafting and after completion to confirm conformance before the B4 dry run.
**Branch:** `feature/b4-agent-skill-harness-assembly`

## Authorities

| Authority | What it governs | Path |
|-----------|-----------------|------|
| T4-SB-01 through T4-SB-05 | Behavioral loop, target selection, query coverage, claim classification | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/scouting-behavior.md` |
| T4-SM-01 through T4-SM-10 | Data structures, claim lifecycle, verification state, budgets | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/state-model.md` |
| T4-CT-01 through T4-CT-05 | Containment enforcement | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/containment.md` |
| V3 execution plan | Emission contract, gate definitions, acceptance thresholds | `docs/plans/2026-04-08-t8-shakedown-execution-plan-v3.md` |
| T8 implementation packet | Concrete implementation surfaces, file inventory | `docs/plans/2026-04-07-t8-minimum-runnable-shakedown-packet.md` |
| T7 executable slice | Behavioral surface, acceptance criteria, inspection protocol | `docs/plans/2026-04-07-t7-executable-slice-definition.md` |
| T2 synthetic-claim contract | Zero-claim fallback, `minimum_fallback` provenance, counter exclusion | `docs/plans/2026-04-02-t04-t2-synthetic-claim-and-closure-contract.md` |

## Authority Precedence

V3 is later than T7 and authoritative for the full emission-contract field set. Where V3 and T7 specify overlapping fields differently, V3 governs. Specifically:

- **`effective_delta` (top-level):** V3 defines this as the per-turn delta. T7:268 describes terminal-turn `effective_delta` as "overall delta." V3's separate `epilogue.effective_delta_overall` field carries the cumulative delta. Follow V3: top-level `effective_delta` is always per-turn, `epilogue.effective_delta_overall` is cumulative.

---

## 1. Loop Shape

Source: T4-SB-01 (scouting-behavior.md:13-32)

The skill must encode the per-turn loop in this exact order:

| Step | Action | Authority |
|------|--------|-----------|
| 1 | Extract semantic data from Codex reply (factual claims) | T4-SB-01 step 1 |
| 2 | Validate, normalize, register occurrences: Phase 1 (concessions, reinforcements), Phase 1.5 (dead-referent reclassification), Phase 2 (new/revised with merger checks) | T4-SM-01, T4-SM-02 |
| 3 | Compute counters and `effective_delta` | T4-SM-07, T4-SB-01 step 3 |
| 4 | Control decision (continue or conclude) | T4-SB-01 step 4 |
| 5 | Scout (if not skipped per T4-SB-02): select target, execute queries, assess disposition, create evidence record, re-emit evidence block | T4-SB-01 step 5 |
| 6 | Compose follow-up using current ledger/evidence state | T4-SB-01 step 6 |
| 7 | Send follow-up | T4-SB-01 step 7 |

**B4 checks:**
- [ ] Steps 1-7 appear in this order
- [ ] Steps 5-7 are skipped when `action == "conclude"` (T4-SB-02)
- [ ] Step 5 is skipped when scout skip conditions hold (T4-SB-02): conclude, evidence budget exhausted, effort budget exhausted, no scoutable targets
- [ ] Step 5e (evidence block re-emission) happens BEFORE step 6 (follow-up composition) — "atomic round commit"

---

## 2. Claim Classes and Lifecycle Rules

Source: T4-SB-05 (scouting-behavior.md:176-336), T4-SM-06 (state-model.md:311-403), T4-SM-02 (state-model.md:67-139)

### Zero-Claim Fallback (T2 Contract)

Source: T2 synthetic-claim contract (t2-synthetic-claim-and-closure-contract.md:88, §5.1)

If turn extraction yields zero distinct raw claims, the skill MUST create exactly one `minimum_fallback` claim from the turn's position text. This preserves the minimum-one-claim invariant.

| Condition | Action |
|-----------|--------|
| Raw claims extracted | Tag each as `claim_source: "extracted"`, proceed normally |
| Zero raw claims | Create one claim: `claim_source: "minimum_fallback"`, `status: "new"` |

**`minimum_fallback` exclusion rules:**
- `minimum_fallback` claims are excluded from counter computation for `new_claims`, `revised`, `conceded` (T2 §5.3)
- An all-fallback turn produces `quality: SHALLOW`, `effective_delta: STATIC` — no inflation
- `minimum_fallback` claims do NOT enter the scouting pipeline — they never become verification entries
- `minimum_fallback` claims are excluded from the emitted `claims` array in the V3 emission contract. The `claims` array represents the verification ledger (V3:116 — statuses are verification statuses: `unverified|supported|contradicted|conflicted|ambiguous|not_scoutable`). Since `minimum_fallback` claims have T2 status `"new"` and never enter `verification_state`, they have no legal emitted status and cannot appear in the array. They satisfy the T2 minimum-one-claim invariant at the processing layer; the emission surface shows only verification entries
- `minimum_fallback` claims do NOT count toward `total_claims` in `counters`

### Three Claim Classes

T4-SB-05 defines three classes. All three are in scope for B1.

| Class | Entity grammar | Scouting behavior | B1 likelihood |
|-------|---------------|-------------------|---------------|
| **Scoutable** | `<path_or_symbol>` or `<path_or_symbol> <qualifier>` | Standard scouting: definition + falsification queries | High — most claims about specific components |
| **Relational-scoutable** | `<entity> × <entity>` | Primary entity (left of `×`) determines scouting focus. Queries target the relationship | High — architecture questions produce "X calls Y", "X delegates to Y" claims |
| **Not scoutable** | N/A | No scouting. Terminal status: `not_scoutable` | Moderate — abstract interpretation, meta-property, cross-system claims |

### Classification Criteria (T4-SB-05:212-221)

A claim is scoutable if and only if the agent can identify:
1. At least one entity fitting the `<path_or_symbol>` grammar (including relational `×` form)
2. A definition query that could be executed via Grep/Read
3. A falsification query that would surface contradicting evidence

If ANY criterion cannot be identified, classify as `not_scoutable`.

For relational claims: the primary entity (left of `×`) determines scouting focus. The definition query targets the primary entity's implementation. The falsification query targets the relationship (e.g., "X calls Y" → falsification targets "X calls something other than Y").

### Within-Turn Processing Order (T4-SM-02)

Phase 1 and Phase 1.5 are runtime behaviors, not audit surfaces. They must be encoded in the skill.

| Phase | What it processes | Key rule |
|-------|-------------------|----------|
| Phase 1 | `conceded` and `reinforced` claims | Conceded: remove from verification state. Reinforced: share referent's ClaimRef |
| Phase 1.5 | Referential claims with dead referents | Reclassify to `new` if all referent occurrences are conceded |
| Phase 2 | `new` and `revised` claims | Merger check against live occurrences; classify scoutable vs not |

### Verification State Lifecycle (T4-SM-06:383-403)

| Event | Transition |
|-------|-----------|
| New scoutable claim | Add: `unverified`, `evidence_indices=[]`, `scout_attempts=0` |
| New not-scoutable claim | Add: `not_scoutable`, `evidence_indices=[]`, `scout_attempts=0`. Terminal |
| Evidence stored | Append index, recompute status, `scout_attempts += 1` |
| `not_found` stored | Append index (no effect on effective set), `scout_attempts += 1` |
| Conceded | Remove from verification state |

**B4 checks:**
- [ ] Zero-claim fallback branch exists: zero raw claims → one `minimum_fallback` claim
- [ ] `minimum_fallback` claims excluded from counter computation
- [ ] `minimum_fallback` claims do NOT enter verification state or scouting pipeline
- [ ] Three claim classes recognized (scoutable, relational-scoutable, not-scoutable)
- [ ] Relational claims use `entity × entity` grammar with primary entity determining scout focus
- [ ] Scoutable claims enter at `unverified`, `scout_attempts: 0`
- [ ] `not_scoutable` claims enter at terminal status, never selected for scouting
- [ ] `not_scoutable` claims still appear in the claim ledger and counters — NOT discarded
- [ ] Classification happens at registration time (Phase 2), before entry creation
- [ ] Phase 1 (concession/reinforcement) is handled before Phase 2 (new/revised registration)
- [ ] Phase 1.5 (dead-referent reclassification to `new`) is handled between Phase 1 and Phase 2
- [ ] Merger check: same `claim_key` + same normalized `claim_text` as a live occurrence -> merge, do not create new entry

**B4-deferred (audit-side only, not runtime behavior):**
- `ClassificationTrace` struct (adjudicator audit surface for scored runs)
- Decomposition analysis recording before `not_scoutable` (T4-SB-05:226-244)
- `claim_provenance_index` emission
- `[ref:]` annotation surfaces

---

## 3. Target Selection Priority

Source: T4-SB-03 (scouting-behavior.md:43-76)

| Priority | Status | Condition | Action |
|----------|--------|-----------|--------|
| 1 | `unverified` | `scout_attempts == 0` | Scout |
| 2 | `conflicted` | `scout_attempts < 2` | Scout |
| 3 | `ambiguous` | `scout_attempts < 2` | Scout |
| 4 (skip) | `supported`, `contradicted`, `not_scoutable` | Terminal | Never scout |
| 4 (skip) | `unverified` | `scout_attempts >= 1` (first scout was `not_found`) | Skip |
| 4 (skip) | `conflicted`, `ambiguous` | `scout_attempts >= 2` | Skip |

Secondary sort: `introduction_turn` ascending. Tertiary: `claim_key` lexicographic. Quaternary: `occurrence_index` ascending.

### Graduated Attempt Limits (T4-SB-03:57-66)

| After first scout returns... | Max attempts | Rationale |
|-----------------------------|-------------|-----------|
| `not_found` | 1 | Nothing to find. Retrying wastes budget |
| `ambiguous` | 2 | Evidence real but inconclusive |
| `conflicted` | 2 | Evidence real but mixed |
| `supports` / `contradicts` | 1 | Terminal |

**B4 checks:**
- [ ] At most one scout target per round
- [ ] Priority ordering correct: unverified(0) > conflicted(<2) > ambiguous(<2)
- [ ] `not_found` on first attempt -> `unverified` with `scout_attempts=1` -> priority 4 (skip)
- [ ] `supported` and `contradicted` are terminal — never re-scouted
- [ ] Second attempts allowed only for `conflicted` and `ambiguous` (max 2)

---

## 4. Query Coverage and Second-Attempt Diversity

Source: T4-SB-04 (scouting-behavior.md:77-174)

### Per Scouting Round

- 2-5 tool calls total
- Minimum: 1 `definition` + 1 `falsification` (mandatory)
- Optional: `supplementary` queries
- Hard cap: 5 tool calls

### Falsification Query Design (T4-SB-04:98-111)

- Must target a specific expected-contradicting condition
- Must be distinct from the definition query target
- A falsification query that searches for the same entity as the definition query (with no contradicting condition) fails the diversity check

### Second-Attempt Diversity (T4-SB-04:155-174)

When a claim gets a second scout attempt:
- At least one mandatory-type query (definition or falsification) MUST have query text that does not appear in any first-round query of the same type
- The actual search string must change, not just the type reclassification
- Supplementary queries do not count toward diversity

### Relational Query Coverage

For relational-scoutable claims (`entity × entity`):
- Definition query targets the primary entity (left of `×`)
- Falsification query targets the relationship
- Query set must address both entities, not just the primary

**B4 checks:**
- [ ] Each scouting round has 2-5 tool calls
- [ ] Each round has >=1 definition AND >=1 falsification
- [ ] Falsification query targets a condition distinct from the definition query
- [ ] Relational claims: query set addresses both entities
- [ ] Second attempts use at least one query with different text than first-round queries of the same mandatory type

---

## 5. Per-Turn Emission Contract

Source: V3 execution-plan-v3.md:84-199

### Sentinel Format (exact)

```
<SHAKEDOWN_TURN_STATE>
```json
{ ... }
```
</SHAKEDOWN_TURN_STATE>
```

All prose follows the closing sentinel. No other JSON fence permitted in the turn.

### State Object Required Fields

| Field | Type | Every turn |
|-------|------|------------|
| `turn` | int | Monotonically increasing, starting at 1 |
| `scouted` | bool | Yes |
| `target_claim_id` | int \| null | Yes |
| `target_claim` | string \| null | Yes |
| `scope_root` | string \| null | Yes |
| `queries` | list[{type, tool, target}] | Yes |
| `disposition` | string \| null | Yes |
| `citations` | list[{path, lines, snippet}] | Yes |
| `claims` | list[{id, text, status, scout_attempts}] | Yes |
| `counters` | object (8 fields) | Yes |
| `effective_delta` | object (8 fields) | Yes — always per-turn delta |
| `terminal` | bool | Yes |
| `epilogue` | object \| null | Yes |

### Counter Fields (exact set, in both `counters` and `effective_delta`)

`total_claims`, `supported`, `contradicted`, `conflicted`, `ambiguous`, `not_scoutable`, `unverified`, `evidence_count`

### Disposition Enum

`"supports"` | `"contradicts"` | `"conflicted"` | `"ambiguous"` | `"not_found"` | `null`

(`null` only on non-scouting turns)

### Parse Failure Conditions (V3:183-193)

Any of these is a parse failure:
- Missing sentinel
- More than one state block in a single turn
- Invalid JSON
- Missing required keys
- Wrong enum or type
- `scouted: true` without required query coverage
- Terminal turn without `epilogue`
- Non-monotonic `turn`

**B4 checks:**
- [ ] Exactly one state block per turn
- [ ] Opening sentinel is literal `<SHAKEDOWN_TURN_STATE>`
- [ ] Closing sentinel is literal `</SHAKEDOWN_TURN_STATE>`
- [ ] JSON is in a fenced `json` block between sentinels
- [ ] No other JSON fence in the turn
- [ ] `turn` is monotonically increasing (1, 2, 3, ...)
- [ ] All 14 top-level fields present on every turn
- [ ] `counters` has all 8 subfields
- [ ] `effective_delta` has all 8 subfields (per-turn delta, not cumulative)
- [ ] `scouted: true` turns have non-null `target_claim_id`, `target_claim`, `scope_root`, `queries`, `disposition`, `citations`
- [ ] Scouting turns have >=1 `definition` and >=1 `falsification` in `queries`
- [ ] `queries` entries: `type`, `tool`, `target`
- [ ] `citations` entries: `path`, `lines`, `snippet`
- [ ] `claims` entries: `id`, `text`, `status`, `scout_attempts`

---

## 6. Non-Scouting Turn Empty-Field Rules

Source: V3 execution-plan-v3.md:152-159

When `scouted: false`, these fields MUST be set exactly:

| Field | Value |
|-------|-------|
| `scouted` | `false` |
| `target_claim_id` | `null` |
| `target_claim` | `null` |
| `scope_root` | `null` |
| `queries` | `[]` (empty array, NOT null) |
| `disposition` | `null` |
| `citations` | `[]` (empty array, NOT null) |

**B4 checks:**
- [ ] Non-scouting turns set all 7 fields exactly as specified
- [ ] `queries` is `[]`, not `null`
- [ ] `citations` is `[]`, not `null`
- [ ] `claims`, `counters`, `effective_delta`, `turn`, `terminal`, `epilogue` are still populated normally

---

## 7. Terminal Epilogue Schema and `converged` Derivation

Source: V3 execution-plan-v3.md:162-179

### Terminal Turn Requirements

- `terminal: true`
- `epilogue` object (not null) with all 3 fields

### Epilogue Schema

```json
{
  "ledger_summary": "string",
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

### `converged` Derivation (V3:162, strict)

| Condition | `converged` |
|-----------|-------------|
| Dialogue completed normally AND verification ledger stabilized (no more scoutable unverified targets) | `true` |
| Dialogue-tool failure (`codex.dialogue.start` or `.reply` error) | `false` |
| Budget exhaustion (evidence or effort) | `false` |
| Other non-convergence (any controlled early exit) | `false` |

Budget exhaustion is a controlled early exit, not convergence. Only normal completion with a stabilized ledger yields `converged: true`.

### Top-Level vs Epilogue Delta

- `effective_delta` (top-level): always per-turn delta (changes since previous turn)
- `epilogue.effective_delta_overall`: cumulative delta across all turns

This follows V3's field definitions. T7:268 describes terminal-turn `effective_delta` as "overall," but V3 is later and authoritative for the emission contract.

**B4 checks:**
- [ ] Terminal turn has `terminal: true`
- [ ] Terminal turn has non-null `epilogue` with all 3 fields
- [ ] `epilogue.effective_delta_overall` has all 8 counter subfields
- [ ] `converged: true` ONLY when dialogue completed normally AND ledger stabilized
- [ ] Budget exhaustion -> `converged: false`
- [ ] Dialogue-tool failure -> `converged: false`
- [ ] `ledger_summary` is human-readable, describes final verification ledger state
- [ ] Non-terminal turns have `terminal: false` and `epilogue: null`

---

## 8. Explicit Prohibitions and Stop Conditions

### Prohibitions

- [ ] Do NOT emit `manifest.json`, `runs.json`, `adjudication.json`, or `summary.md` (T7:356-364 — benchmark artifact names reserved)
- [ ] Do NOT use Bash, Write, Edit, or Agent tools (T8 Phase 2a — containment-safe surface)
- [ ] Do NOT continue scouting after dialogue-tool failure (V3 behavior 7, T7:242)
- [ ] Do NOT emit more than one state block per turn (V3:186)
- [ ] Do NOT emit any JSON fence outside the sentinel-wrapped state block (V3:91)

### Stop Conditions

| Condition | Action |
|-----------|--------|
| `action == "conclude"` from control decision | Emit terminal turn with epilogue |
| `codex.dialogue.start` or `.reply` error | Emit terminal turn: `converged: false`, epilogue describes failure (tool name, error message, turn at failure) |
| Evidence budget exhausted (`evidence_count >= max_evidence`) | Scout skip; may still compose follow-up |
| Effort budget exhausted (`scout_budget_spent >= max_scout_rounds`) | Scout skip |
| No scoutable targets remaining | Scout skip |

### `not_found` Disposition (V3:161)

- When scouting queries return no usable evidence: `disposition: "not_found"`
- Distinct from `"ambiguous"` (evidence found but mixed)
- Signals retry with different queries may be productive
- `not_found` does NOT affect the status derivation effective set (excluded from the derivation rule)

### Status Derivation Rule (T4-SM-06:346-368)

Used everywhere: verification state updates, target selection, counter computation.

```
effective = set()
for each evidence_index:
    d = evidence_log[index].disposition
    if d == "conflicted": add "supports" and "contradicts"
    elif d in ("supports", "contradicts", "ambiguous"): add d
    # "not_found" is excluded — does not enter effective set

if "contradicts" in effective and "supports" in effective -> "conflicted"
elif "contradicts" in effective -> "contradicted"
elif "supports" in effective -> "supported"
elif "ambiguous" in effective -> "ambiguous"
else -> "unverified"
```

**B4 checks:**
- [ ] This exact rule governs all status derivation
- [ ] `not_found` excluded from the effective set
- [ ] `conflicted` disposition expands to both `supports` and `contradicts` in the effective set

---

## Golden Exemplar: Scouting Turn

Turn 2: after receiving Codex's architecture reply, the agent extracted 4 claims. One is relational-scoutable. One is not scoutable. The agent scouts claim 1.

Claims extracted:
1. "DialogueController uses OperationJournal to record intent before dispatching thread creation" — relational-scoutable (`DialogueController × OperationJournal`)
2. "LineageStore persists CollaborationHandle records as append-only JSONL" — scoutable
3. "McpServer lazily initializes DialogueController via a factory callback" — scoutable
4. "The plugin follows a microservices architecture for horizontal scaling" — not scoutable (abstract interpretation, no repo-searchable entity)

Scouting claim 1 (relational, primary entity `DialogueController`):

```
<SHAKEDOWN_TURN_STATE>
```json
{
  "turn": 2,
  "scouted": true,
  "target_claim_id": 1,
  "target_claim": "DialogueController uses OperationJournal to record intent before dispatching thread creation",
  "scope_root": "/Users/jp/Projects/active/claude-code-tool-dev-t8-impl/packages/plugins/codex-collaboration/server/",
  "queries": [
    {
      "type": "definition",
      "tool": "Read",
      "target": "dialogue.py:115-138"
    },
    {
      "type": "falsification",
      "tool": "Grep",
      "target": "start_thread"
    },
    {
      "type": "supplementary",
      "tool": "Grep",
      "target": "write_phase.*intent"
    }
  ],
  "disposition": "supports",
  "citations": [
    {
      "path": "/Users/jp/Projects/active/claude-code-tool-dev-t8-impl/packages/plugins/codex-collaboration/server/dialogue.py",
      "lines": "118-130",
      "snippet": "# Phase 1: intent — journal before dispatch ... self._journal.write_phase(OperationJournalEntry(... phase=\"intent\" ...))"
    },
    {
      "path": "/Users/jp/Projects/active/claude-code-tool-dev-t8-impl/packages/plugins/codex-collaboration/server/dialogue.py",
      "lines": "132-134",
      "snippet": "try: thread_id = runtime.session.start_thread() runtime.thread_count += 1"
    }
  ],
  "claims": [
    {
      "id": 1,
      "text": "DialogueController uses OperationJournal to record intent before dispatching thread creation",
      "status": "supported",
      "scout_attempts": 1
    },
    {
      "id": 2,
      "text": "LineageStore persists CollaborationHandle records as append-only JSONL",
      "status": "unverified",
      "scout_attempts": 0
    },
    {
      "id": 3,
      "text": "McpServer lazily initializes DialogueController via a factory callback",
      "status": "unverified",
      "scout_attempts": 0
    },
    {
      "id": 4,
      "text": "The plugin follows a microservices architecture for horizontal scaling",
      "status": "not_scoutable",
      "scout_attempts": 0
    }
  ],
  "counters": {
    "total_claims": 4,
    "supported": 1,
    "contradicted": 0,
    "conflicted": 0,
    "ambiguous": 0,
    "not_scoutable": 1,
    "unverified": 2,
    "evidence_count": 1
  },
  "effective_delta": {
    "total_claims": 4,
    "supported": 1,
    "contradicted": 0,
    "conflicted": 0,
    "ambiguous": 0,
    "not_scoutable": 1,
    "unverified": 2,
    "evidence_count": 1
  },
  "terminal": false,
  "epilogue": null
}
```
</SHAKEDOWN_TURN_STATE>

[Follow-up composition to Codex follows here, using updated ledger state]
```

### What this exemplar demonstrates

- Correct sentinel wrapping with fenced JSON block
- All 14 top-level fields present
- Relational-scoutable claim (claim 1): entity `DialogueController × OperationJournal`, primary entity determines scout focus
- 3 tool calls (within 2-5 range): 1 definition + 1 falsification + 1 supplementary
- Definition query reads the primary entity's implementation (`dialogue.py:115-138`)
- Falsification query targets what would contradict the ordering claim — if `start_thread` appeared before `write_phase(phase="intent")`, the journal-before-dispatch claim would be false
- Disposition `supports` with confirming citations: `write_phase` at lines 118-130 precedes `start_thread()` at lines 132-134
- `not_scoutable` claim (claim 4) present in ledger but never selected for scouting
- `effective_delta` equals `counters` because this is the first turn with claims (turn 1 was non-scouting)
- All paths reference the active B4 worktree (`claude-code-tool-dev-t8-impl`)

### Grounding verification

| Claim | Source file | Line(s) | Verifiable? |
|-------|-----------|---------|-------------|
| Claim 1: DialogueController uses OperationJournal to record intent before dispatching thread creation | `dialogue.py` | 118-134 | Yes — `write_phase(phase="intent")` at L118-130, `start_thread()` at L132-134. Journal precedes dispatch |
| Claim 2: LineageStore persists CollaborationHandle as append-only JSONL | `lineage_store.py` | 124-125 | Yes — docstring: "All mutations append a new record" |
| Claim 3: McpServer lazy initialization via factory | `mcp_server.py` | 115-134 | Yes — `_ensure_dialogue_controller()` with one-way pin pattern |
| Claim 4: Microservices architecture | N/A | N/A | No — abstract interpretation, no repo entity |

---

## Golden Exemplar: Terminal Epilogue

Turn 6: dialogue complete, ledger stabilized, no unverified targets remaining. Budget was NOT exhausted — this is normal convergence.

```
<SHAKEDOWN_TURN_STATE>
```json
{
  "turn": 6,
  "scouted": false,
  "target_claim_id": null,
  "target_claim": null,
  "scope_root": null,
  "queries": [],
  "disposition": null,
  "citations": [],
  "claims": [
    {
      "id": 1,
      "text": "DialogueController uses OperationJournal to record intent before dispatching thread creation",
      "status": "supported",
      "scout_attempts": 1
    },
    {
      "id": 2,
      "text": "LineageStore persists CollaborationHandle records as append-only JSONL",
      "status": "supported",
      "scout_attempts": 1
    },
    {
      "id": 3,
      "text": "McpServer lazily initializes DialogueController via a factory callback",
      "status": "supported",
      "scout_attempts": 1
    },
    {
      "id": 4,
      "text": "The plugin follows a microservices architecture for horizontal scaling",
      "status": "not_scoutable",
      "scout_attempts": 0
    },
    {
      "id": 5,
      "text": "TurnStore persists per-turn context_size as append-only JSONL",
      "status": "supported",
      "scout_attempts": 1
    },
    {
      "id": 6,
      "text": "ContextAssembly enforces a hard token budget per assembled packet",
      "status": "ambiguous",
      "scout_attempts": 2
    }
  ],
  "counters": {
    "total_claims": 6,
    "supported": 4,
    "contradicted": 0,
    "conflicted": 0,
    "ambiguous": 1,
    "not_scoutable": 1,
    "unverified": 0,
    "evidence_count": 5
  },
  "effective_delta": {
    "total_claims": 0,
    "supported": 0,
    "contradicted": 0,
    "conflicted": 0,
    "ambiguous": 0,
    "not_scoutable": 0,
    "unverified": 0,
    "evidence_count": 0
  },
  "terminal": true,
  "epilogue": {
    "ledger_summary": "6 claims extracted across 5 Codex turns. 4 supported by code evidence (DialogueController-OperationJournal intent-before-dispatch, LineageStore append-only JSONL, McpServer lazy factory initialization, TurnStore append-only context_size). 1 ambiguous after 2 scout attempts (ContextAssembly enforces a hard budget but it is byte-based via len(packet.encode('utf-8')), not token-based as claimed). 1 not scoutable (abstract microservices scaling claim). Verification ledger stabilized: 0 unverified claims remain.",
    "converged": true,
    "effective_delta_overall": {
      "total_claims": 6,
      "supported": 4,
      "contradicted": 0,
      "conflicted": 0,
      "ambiguous": 1,
      "not_scoutable": 1,
      "unverified": 0,
      "evidence_count": 5
    }
  }
}
```
</SHAKEDOWN_TURN_STATE>
```

### What this exemplar demonstrates

- Terminal turn with `terminal: true` and non-null `epilogue`
- Non-scouting terminal turn: all 7 empty-field rules applied (null/empty arrays)
- `converged: true` — ledger stabilized normally (0 unverified, no budget exhaustion)
- `effective_delta` is zero on this turn (no state changes — conclusion)
- `epilogue.effective_delta_overall` is cumulative across all turns (top-level `effective_delta` is per-turn per V3)
- `ledger_summary` describes final state in human-readable form, including the ambiguous claim's specific finding
- Counter arithmetic consistent: 4+0+0+1+1+0 = 6 = `total_claims`
- `evidence_count` (5) matches: claims 1-3, 5 scouted once each; claim 6 scouted twice (ambiguous → second attempt → still ambiguous)
- `ambiguous` claim 6 has `scout_attempts: 2` (max per T4-SB-03 graduated limit)

### Grounding verification

| Claim | Source file | Line(s) | Verifiable? |
|-------|-----------|---------|-------------|
| Claim 5: TurnStore persists context_size as append-only JSONL | `turn_store.py` | 32-56 | Yes — class docstring: "Append-only JSONL store for per-turn context_size", `write()` appends JSONL records |
| Claim 6: ContextAssembly enforces a hard token budget | `context_assembly.py` | 12-17, 187-191 | Genuinely ambiguous — `_HARD_CAPS` exists and `ContextAssemblyError` is raised when exceeded, confirming a hard budget. But the budget is byte-based (`len(packet.encode("utf-8"))`), not token-based. Evidence confirms enforcement, contradicts "token" specificity → `ambiguous` |
