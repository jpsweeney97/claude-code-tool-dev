# Dialogue Synthesis Format

Read this document when entering Phase 3 of the `codex-dialogue` agent. Defines the assembly process, output format, and pipeline data epilogue.

## Assembly Process

Assemble synthesis from `turn_history`. Do not recall the full conversation — walk the `turn_history` (server-validated `validated_entry` records and cumulative snapshots).

These 7 items are independent output sections. Assemble all 7 from `turn_history`.

1. **Convergence → Areas of Agreement:** Claims where both sides arrived at the same position, especially through independent reasoning or survived challenges. High confidence.
2. **Concessions → Key Outcomes:** Claims where one side changed position. Note which side, what triggered the change, and the final position.
3. **Novel emergent ideas:** Ideas that appeared mid-conversation that neither side started with. Flag as "emerged from dialogue."
4. **Unresolved → Open Questions:** Claims still tagged `new` or items remaining in the unresolved column.
5. **Evidence trajectory:** For each turn in `turn_history` where `scout_outcomes` is non-empty, note: what entity was scouted, what was found (or not found), and its impact on the conversation (premise falsified, claim supported, or ambiguous).
6. **Claim trajectory:** Using the accumulated `validated_entry` records in `turn_history`, trace how each significant claim evolved across turns (new → reinforced/revised/conceded).
7. **Contested claims:** For each claim where the two sides held different positions at any point, classify the final state: `agreement` (both converged), `resolved_disagreement` (one side conceded with reasoning), or `unresolved_disagreement` (positions remain apart). Include: `claim_text`, `state`, `final_positions` (both sides' ending positions), `resolution_basis` (what triggered the resolution, if any), and `confidence`.

## Confidence Annotations

Each finding gets a confidence level derived from ledger data:

| Confidence | Criteria |
|------------|----------|
| **High** | Both sides independently argued for it, OR one side challenged and the other defended with evidence |
| **Medium** | One side proposed, the other agreed with reasoning (at least one turn where delta was `advancing` or `shifting`) |
| **Low** | Single turn, no probing — or agreement without reasoning |

## Your Assessment

Add independent judgment:
- Where you agree with Codex and why
- Where you disagree and why
- What emerged from the back-and-forth that neither side started with

## Pre-Flight Checklist

Before writing output, verify every item:

- [ ] Trajectory line computed from ledger (one `delta(tags)` entry per turn)
- [ ] Each Key Outcome has **Confidence** (High/Medium/Low) and **Basis**
- [ ] Areas of Agreement include confidence levels
- [ ] Open Questions reference which turn(s) raised them
- [ ] Continuation section includes unresolved items and recommended posture (if warranted)
- [ ] Contested claims classified with state (agreement/resolved_disagreement/unresolved_disagreement) and resolution basis
- [ ] Evidence statistics: scouts executed, entities scouted, impacts on conversation. If `evidence_count == 0`, state "Evidence: none (no scouts executed)" and omit evidence trajectory
- [ ] Phase trajectory: which phases entered, turns consumed per phase, phases skipped by convergence (multi-phase only)

If any item is missing, fix it before returning output.

## Synthesis Checkpoint

After the narrative synthesis and pre-flight checklist, emit a structured checkpoint block:

```
## Synthesis Checkpoint
RESOLVED: <claim> [confidence: High|Medium|Low] [basis: convergence|concession|evidence]
UNRESOLVED: <item> [raised: turn N]
EMERGED: <idea> [source: dialogue-born]
```

**Tags:**
- `RESOLVED` — claims where both sides reached agreement. Include confidence level and the basis for resolution.
- `UNRESOLVED` — items still open at dialogue end. Include the turn number where first raised.
- `EMERGED` — ideas that neither side started with; born from the dialogue itself. Flag as `dialogue-born`.

**Consistency rules:** The checkpoint and narrative synthesis are generated from the same `turn_history` state. Precedence: checkpoint is canonical for structured status, narrative is canonical for explanatory detail.

Cross-reference requirements:
- Every `UNRESOLVED` in the checkpoint **must** appear in the narrative's Open Questions section.
- Every `RESOLVED` in the checkpoint **must** appear in the narrative's Areas of Agreement or Contested Claims section.
- Every `EMERGED` in the checkpoint **must** appear in the narrative's Key Outcomes section.

If any cross-reference is missing, add it before returning output.

## Output Format

### Conversation Summary
- **Topic:** [what was discussed]
- **Goal:** [what outcome was sought]
- **Posture:** [posture used]
- **Turns:** [X of Y budget]
- **Converged:** [yes — reason / no — hit turn limit or error]
- **Trajectory:** `T1:delta(tags) → T2:delta(tags) → ...` (one entry per turn)
- **Evidence:** [X scouts / Y turns, entities: ..., impacts: ...]
- **Mode:** `server_assisted` or `manual_legacy` — the actual mode used for this conversation. Set once at conversation start (server_assisted if context injection tools available, manual_legacy otherwise). Do not change mid-conversation.

### Key Outcomes

For each finding, adapt structure to the goal:
- **Ideation** → ideas with assessments
- **Plan review** → concerns and suggestions
- **Decision-making** → options with trade-offs
- **Doc review** → findings by severity
- **Research** → findings and knowledge map

Annotate each finding:
- **Confidence:** High / Medium / Low
- **Basis:** How this emerged — convergence, concession, single-turn proposal, or emerged from dialogue

### Areas of Agreement

Points both sides converged on. Include confidence level.

### Contested Claims

For each claim with divergent positions during the dialogue:
- **Claim:** [claim text]
- **State:** Agreement / Resolved disagreement / Unresolved disagreement
- **Final positions:** [both sides' ending positions]
- **Resolution basis:** [what triggered resolution, if resolved]
- **Confidence:** High / Medium / Low

### Open Questions

Unresolved points worth further investigation. Include which turn(s) raised them.

### Continuation
- **Thread ID:** {persisted threadId value} | none
- **Continuation warranted:** yes — [reason] / no
- **Unresolved items carried forward:** [list from ledger, if continuation warranted]
- **Recommended posture for continuation:** [posture suggestion based on conversation dynamics]
- **Evidence trajectory:** [which turns had evidence, what entities, what impacts — or "none (no scouts executed)" if evidence_count == 0]

### Synthesis Checkpoint

Structured summary of dialogue outcomes. Emitted after the narrative sections:

```
## Synthesis Checkpoint
RESOLVED: <claim> [confidence: High|Medium|Low] [basis: convergence|concession|evidence]
UNRESOLVED: <item> [raised: turn N]
EMERGED: <idea> [source: dialogue-born]
```

Include all items from the narrative — this block must be consistent with the narrative sections per the consistency rules above.

### Pipeline Data (JSON epilogue)

After the markdown synthesis, emit a fenced JSON block with structured fields for downstream consumers. This block is machine-parsed by the `/dialogue` skill — do not omit fields.

| Field | Type | Description |
|-------|------|-------------|
| `mode` | string | `"server_assisted"` or `"manual_legacy"` |
| `thread_id` | string or null | Codex thread ID. Emit whenever available, including `manual_legacy`. |
| `turn_count` | int | Actual Codex turns used |
| `converged` | bool | Whether dialogue converged |
| `convergence_reason_code` | string or null | One of: `"all_resolved"`, `"natural_convergence"`, `"budget_exhausted"`, `"error"`, `"scope_breach"`. Set to `null` if dialogue did not converge. Do NOT use `termination_reason` values here — the two fields have different enums. |
| `termination_reason` | string | `"convergence"`, `"budget"`, `"scope_breach"`, or `"error"` (dialogue only — `/codex` also uses `"complete"`) |
| `scout_count` | int | `evidence_count` from state |
| `resolved_count` | int | From synthesis checkpoint |
| `unresolved_count` | int | From synthesis checkpoint |
| `emerged_count` | int | From synthesis checkpoint |
| `scope_breach_count` | int | 0 unless scope breach occurred |
| `ccdi` | object | CCDI diagnostics. Schema varies by `ccdi.status` — see [ccdi-dialogue-protocol.md](ccdi-dialogue-protocol.md) or emit `{"status": "unavailable", "phase": "initial_only"}` when CCDI is unavailable. |
| `ccdi_trace` | list or null | Per-turn CCDI trace entries. Present only when `ccdi_debug` is `true`. `null` otherwise. |

```json
<!-- pipeline-data -->
{
  "mode": "server_assisted",
  "thread_id": "codex-thread-id",
  "turn_count": 0,
  "converged": false,
  "convergence_reason_code": null,
  "termination_reason": "convergence",
  "scout_count": 0,
  "resolved_count": 0,
  "unresolved_count": 0,
  "emerged_count": 0,
  "scope_breach_count": 0,
  "ccdi": {"status": "unavailable", "phase": "initial_only"},
  "ccdi_trace": null
}
```

The `<!-- pipeline-data -->` sentinel marks this block for machine parsing. The `/dialogue` skill extracts fields from this block. Substitute actual values from conversation state — the template above shows types and placeholders.

### Example

Complete example showing all required fields:

```
### Conversation Summary
- **Topic:** Whether to use event sourcing vs. state-based persistence for the audit log
- **Goal:** Choose a persistence strategy with clear trade-offs
- **Posture:** Adversarial
- **Turns:** 4 of 6 budget
- **Converged:** Yes — both sides agreed on hybrid approach after T3 challenge
- **Trajectory:** `T1:advancing(new_reasoning) → T2:advancing(challenge) → T3:shifting(concession, expansion) → T4:static(restatement)`
- **Evidence:** 2 scouts / 4 turns (T2: `src/audit/store.py` — confirmed append-only pattern; T3: `config/schema.yaml` — found versioned envelope type)

### Key Outcomes

**Hybrid persistence: event sourcing for audit trail, state-based for read models**
- **Confidence:** High
- **Basis:** Convergence — both sides independently argued for separation of write and read concerns (T1, T2). Survived adversarial challenge on operational complexity (T2-T3).

**Event schema should use a single envelope type with versioned payloads**
- **Confidence:** Medium
- **Basis:** Codex proposed (T1), Claude agreed with reasoning about schema evolution (T3). Not independently derived.

**Skip CQRS framework; use simple event log table + materialized views**
- **Confidence:** Low
- **Basis:** Single-turn proposal (T3). Not probed or challenged.

### Areas of Agreement

- Audit requirements demand append-only semantics (High — independently argued T1-T2)
- Read-heavy queries shouldn't hit the event store (High — converged T2-T3)

### Contested Claims

**Use CQRS framework for read model projections**
- **State:** Resolved disagreement
- **Final positions:** Both agreed to skip — use simple materialized views
- **Resolution basis:** Codex proposed CQRS (T1), challenged on operational complexity (T2), conceded in favor of simplicity (T3)
- **Confidence:** Medium

### Open Questions

- Retention policy for raw events vs. snapshots (raised T3, not probed)
- Whether to use database triggers or application-level projection (raised T1, partially explored T2)

### Continuation
- **Thread ID:** thread_abc123
- **Continuation warranted:** yes — retention policy and projection strategy unresolved
- **Unresolved items carried forward:** event retention policy, trigger vs. application projection
- **Recommended posture for continuation:** Exploratory — key decisions made, remaining items need research not debate
- **Evidence trajectory:** T2 — `src/audit/store.py` read, confirmed append-only writes (claim supported); T3 — `config/schema.yaml` read, found envelope type with version field (claim supported)
```

---

**Do not include:**
- Raw conversation transcript or full Codex responses
- Raw ledger entries (keep internal — only the trajectory line appears in output)
- Filler, pleasantries, or praise
- Implementation of recommendations (report them, don't do them)
