# Context Injection Agent Integration — Architectural Decisions

**Date:** 2026-02-15
**Status:** Decisions locked, ready for implementation planning
**Builds on:** Exploration document at `docs/plans/2026-02-15-context-injection-agent-integration.md`
**Informed by:** Protocol contract at `docs/references/context-injection-contract.md`
**Codex thread:** `019c5ff0-361e-7d12-b72a-381273e45a62` (3 turns, all architectural)

---

## Summary

This session resolved all architectural open questions from the exploration document (Section 7). Five decisions were locked through discussion and two Codex consultations. The remaining open questions (follow-up priority selection, ledger summary design, focus selection ownership) are design details to resolve during implementation planning.

---

## Decision 1: State Recovery — Opaque Checkpoint with Chain Validation

**Question:** What happens when the MCP server restarts mid-conversation? With server-owned ledger state, restart loses the entire conversation history.

**Decision:** Option C — the agent carries an opaque state checkpoint.

**How it works:**
- Server returns a serialized state blob in `TurnPacket` (`state_checkpoint` field)
- Agent passes it back in the next `TurnRequest` as an opaque field
- Server uses in-memory state when running normally; bootstraps from checkpoint on restart
- Mirrors the existing `evidence_history` protocol pattern (agent-transported, server-authoritative)

**Chain validation (from Codex consultation):**
- `checkpoint_id`: unique identifier per checkpoint
- `parent_checkpoint_id`: links to previous checkpoint, enables stale/replay/fork detection
- `format_version`: deserialization safety across server versions
- Size cap: hard limit (8-16 KB), server controls compaction via rolling aggregation

**Recovery error codes:**
- `checkpoint_missing`: no checkpoint provided and no in-memory state
- `checkpoint_invalid`: deserialization failed or payload corrupted
- `checkpoint_stale`: `parent_checkpoint_id` doesn't match server's expected chain

**Deferred:**
- Disk persistence (sqlite/jsonl) — add if checkpoint pattern proves insufficient
- `payload_hash` / HMAC on checkpoint — checkpoint is server-generated, tampering risk is lower than scout tokens
- `request_id` for idempotency — `conversation_id:turn_number` pair already provides uniqueness

**Design-now-implement-later:** Include `state_checkpoint` as an optional field in the 0.2.0 schema. Server can initially use pure in-memory state and ignore checkpoints. Recovery logic added when ready, without schema changes.

**Rationale:** Server restart during a 5-10 minute Codex dialogue is low probability but high impact. Pure in-memory state (the exploration doc's Option A/D) contradicts the robustness motivation for server-owned state. Disk persistence (Option B) adds significant implementation scope for an edge case. The checkpoint pattern provides recovery without operational complexity.

**Codex validation:** Codex recommended a hybrid B-lite + C (disk + checkpoint). We chose pure C for MVP, noting disk as a future enhancement. Codex identified the stale/replay risk and two-call atomicity gap, both addressed by chain validation.

---

## Decision 2: `context_claims` — Server-Managed

**Question:** Should the agent continue assembling cumulative claims from prior turns, or should the server manage them internally?

**Decision:** Server-managed. The agent no longer sends `context_claims`.

**How it works:**
- Server receives `claims` each turn and stores them in the conversation's ledger history
- Server internally computes cumulative claims for entity extraction
- Focus-affinity invariant preserved: `in_focus: true` only when the entity source claim is in the current turn's `focus.claims`, regardless of claim age
- Deterministic ordering maintained when rebuilding cumulative claims (insertion order)

**Rationale:** With server-owned ledger state, the server has the full claim history. Having the agent assemble cumulative claims is redundant bookkeeping that adds context window pressure and introduces a potential inconsistency between what the agent sends and what the server has stored.

**Codex validation:** Codex confirmed the approach. Added implementation notes: store claim_id and raw text for stable entity extraction, preserve deterministic ordering for reproducible template selection.

---

## Decision 3: `evidence_history` — Server-Managed, All Successful Scouts Evidence-Bearing

**Question:** Should the agent continue deciding which scouts appear in `evidence_history`, or should the server manage it? If server-managed, who decides whether a scout is "evidence-bearing"?

**Decision:** Server-managed. All successful scouts (`status: "success"`) are evidence-bearing.

**How it works:**
- Server records every successful scout (including zero-match grep — "absence is data") in the conversation's evidence history
- Agent no longer sends `evidence_history` in `TurnRequest`
- Budget computation uses the server's internal evidence count

**Rejected alternatives:**
- Agent signals usage via third MCP tool (`confirm_evidence`) — adds protocol complexity for marginal gain
- Implicit confirmation via next `process_turn` — creates ambiguity on last turn (conclude)

**Rationale:** The scenario where an agent requests a scout and doesn't use the result is unlikely. The slight over-count is acceptable and eliminates a protocol complication. If strict "cited in final language" provenance is needed later, an optional `used_scout_ids` field can be added without schema changes.

**Codex validation:** Codex confirmed Option 1. Noted edge cases: success with truncation/redaction shouldn't hard-dedup forever (future enhancement: completeness flag for rerun eligibility).

---

## Decision 4: Schema Versioning — Clean Break to 0.2.0

**Question:** How to handle the API evolution from the current schema to the new full-ledger schema?

**Decision:** Clean break to `0.2.0`. No backward compatibility.

**How it works:**
- New schema version `0.2.0` with exact-match requirement (existing 0.x rule)
- Existing 739 tests update their `schema_version` strings
- Scout execution pipeline tests are unchanged — only the TurnRequest/TurnPacket envelope grows
- No optional fields for migration, no schema version gating

**Rationale:** The 0.x exact-match rule was designed for pre-1.0 iteration. The new fields are additive to the protocol envelope; the scout pipeline internals don't change.

---

## Decision 5: Error Handling — Hard/Soft Split with Server-Computed `effective_delta`

**Question:** What happens when the server validates an agent-submitted ledger entry and finds inconsistencies?

**Decision:** Three-tier validation with server-computed mechanical fields.

### Field ownership

| Category | Fields | Owner | Agent sends? |
|----------|--------|-------|-------------|
| Semantic extraction | `position`, `claims`, `unresolved` | Agent | Yes |
| Judgment | `delta`, `tags` | Agent | Yes |
| Derived (mechanical) | `counters`, `quality` | Server | No — server computes from claims |
| Decision input | `effective_delta` | Server | No — server computes from counters |

### `effective_delta` (from Codex consultation)

The server computes its own mechanical progress signal for continue/conclude decisions, independent of the agent's `delta` judgment:

| Condition | `effective_delta` |
|-----------|-------------------|
| `new_claims > 0` | `advancing` |
| `revised > 0` or `conceded > 0` | `shifting` |
| All counters = 0 | `static` |

Plateau detection and continue/conclude decisions use `effective_delta`, not the agent's `delta`. The agent's `delta` is stored for context and advisory purposes.

**Rationale:** If mechanical decisions depend on agent judgment, a bad `delta` can force a wrong continue/conclude decision — reintroducing the drift risk the architecture is designed to eliminate. The "separate language from state" principle requires mechanical decisions to use mechanical inputs.

### Validation tiers

| Tier | Action | Examples |
|------|--------|---------|
| **Hard reject** | Return error, agent must fix | Missing required fields, wrong types, invalid enum values, malformed claim records, turn sequencing errors |
| **Soft warn** | Accept entry, flag in response | Empty position, delta/counter mismatch, suspicious tag combinations |
| **Referential warn** | Accept, flag with context | Claim marked "reinforced" but no similar prior claim found |

### `claim.status` referential validation

`claim.status` (new/reinforced/revised/conceded) is semantic but relative to prior state. The server knows what claims existed in prior turns and can flag mismatches (e.g., "reinforced" with no prior similar claim). This is a soft warning, not a hard reject — the agent may recognize paraphrases as reinforcement that string matching wouldn't catch.

**Codex validation:** Codex identified the `effective_delta` concept as critical. Also recommended the hard/soft split and referential validation for `claim.status`.

---

## Updated TurnRequest Shape (0.2.0)

After all decisions, the agent's per-turn payload is:

```
TurnRequest (0.2.0):
  schema_version: str           # "0.2.0"
  turn_number: int
  conversation_id: str
  posture: str                  # adversarial / collaborative / exploratory / evaluative

  # Semantic extraction (agent's language understanding)
  position: str                 # 1-2 sentence summary of Codex's key point
  claims: list[Claim]           # All claims this turn with status
  unresolved: list[Unresolved]  # Questions opened or left unanswered

  # Judgment (agent's classification)
  delta: str                    # advancing / shifting / static (advisory, not used for decisions)
  tags: list[str]               # challenge, concession, new_reasoning, etc.

  # Scouting context
  focus: Focus                  # text, claims, unresolved (for entity extraction)

  # State recovery (opaque pass-through)
  state_checkpoint: str | null  # Server-generated, agent-opaque
  checkpoint_id: str | null     # Chain validation
  parent_checkpoint_id: str | null

  # Removed from 0.1.0:
  # context_claims — server-managed
  # evidence_history — server-managed
```

## Updated TurnPacket Shape (0.2.0)

```
TurnPacket (0.2.0):
  # Existing (from 0.1.0): entities, path_decisions, template_candidates, budget, deduped
  # (All scout pipeline fields unchanged)

  # New: validated ledger state
  validated_entry: LedgerEntry  # Server-computed counters, quality, effective_delta
  warnings: list[Warning]      # Soft validation warnings (if any)
  cumulative: CumulativeState   # Running totals across all turns

  # New: conversation control
  action: str                   # "continue" / "closing_probe" / "conclude"
  action_reason: str            # Mechanical explanation

  # New: compaction-safe snapshot
  ledger_summary: str           # Compact text summary of conversation state

  # New: state recovery
  state_checkpoint: str         # Opaque blob for agent to pass back next turn
  checkpoint_id: str            # Current checkpoint identifier
```

---

## Open Questions Deferred to Planning

These are design details, not architectural decisions. Resolve during implementation planning.

### Follow-up priority selection

The current agent applies a priority list: unresolved items -> unprobed claims -> weakest claim -> posture probe. Should this move server-side?

Likely hybrid: server ranks follow-up candidates using ledger state, agent selects from the ranked list based on conversational judgment.

### Ledger summary design

How compact while still supporting agent reasoning after compaction? Needs to support follow-up composition, posture adaptation, and synthesis. Estimated 200-400 tokens for 5-8 turns.

### Focus selection ownership

Currently agent-selected. With full ledger state in the server, could move server-side. But has a semantic component — "which unresolved item is most important?" involves judgment.

---

## Next Steps

1. Write an implementation plan on a feature branch — concrete tasks, API schema changes, test strategy, delivery sequencing
2. Implement on the feature branch
3. After completion: proceed to cross-model learning system

---

## References

| What | Where |
|------|-------|
| Exploration document | `docs/plans/2026-02-15-context-injection-agent-integration.md` |
| Protocol contract (0.1.0) | `docs/references/context-injection-contract.md` |
| Context injection design spec | `docs/plans/2026-02-11-conversation-aware-context-injection.md` |
| Cross-model learning spec | `docs/plans/2026-02-10-cross-model-learning-system.md` |
| Codex-dialogue agent | `.claude/agents/codex-dialogue.md` |
| Codex thread (this session) | `019c5ff0-361e-7d12-b72a-381273e45a62` |
