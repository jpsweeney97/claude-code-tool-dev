# Context Injection Agent Integration

**Date:** 2026-02-15
**Status:** Exploration
**Purpose:** Capture architectural direction for integrating the context injection MCP server into the codex-dialogue agent, including the decision to extend the server into a conversation controller that owns authoritative ledger state.
**Depends on:** Context injection v0b (complete, 739 tests on `main`), codex-dialogue agent v2 (deployed)
**Informed by:** Design spec at `docs/plans/2026-02-11-conversation-aware-context-injection.md`, Section 3 (MVP Scouting Loop)

---

## 1. Current State

### What exists

**Context injection MCP server** (`packages/context-injection/`):
- `process_turn`: receives focus-scoped ledger data (claims, unresolved items), extracts entities, selects scout templates, returns scout options
- `execute_scout`: executes a file read or grep, returns redacted/truncated evidence
- Full pipeline: entity extraction, template selection, redaction, truncation, evidence block building
- 739 tests, merged to `main`

**Codex-dialogue agent** (`.claude/agents/codex-dialogue.md`):
- 3-phase structure: Setup (briefing) → Conversation Loop → Synthesis
- Phase 2 conversation loop: 3 steps per turn (update ledger → choose follow-up → decide continue/conclude)
- Running ledger maintained in the agent's context window as generated text
- Ledger entry schema: position, claims, delta, tags, counters, quality, next, unresolved
- Continue/conclude logic based on delta sequence and unresolved list
- Tool access: `mcp__codex__codex`, `mcp__codex__codex-reply`, Bash, Read, Glob, Grep
- Does NOT have access to `mcp__context-injection__process_turn` or `mcp__context-injection__execute_scout`

### What's missing

The design spec (Section 3) describes a 7-step scouting loop that replaces the 3-step conversation loop:

| Step | Action | Status |
|------|--------|--------|
| 1 | Update ledger | Exists (agent, in-context) |
| 2 | Extract entities from new ledger entry | Exists (server, `process_turn`) |
| 3 | Select focus (priority system) | Exists (agent, in-context) |
| 4 | Select template via decision tree | Exists (server, `process_turn`) |
| 5 | If `requires_repo_fact`, run exactly one scout | Exists (server, `execute_scout`) |
| 6 | Reframe-only planning update | Not implemented |
| 7 | Render + send follow-up | Exists (agent, modified) |

The gap: the agent's conversation loop needs rewriting to call the MCP server tools and use their results. The original design spec assumed the agent would maintain all state in-context and call the MCP tools as helpers. This document proposes a different split.

---

## 2. Problem: State via Context

The codex-dialogue agent maintains its running ledger as text in its own conversation context. This creates three risks:

**Drift.** The agent must follow a structured schema (8 fields per entry, mechanically derived quality, single-label delta) consistently across every turn. If the model fills out an entry incorrectly — miscomputes a counter, assigns quality by judgment instead of derivation, or skips a field — no external system catches it. Reliability depends entirely on instruction-following fidelity.

**Compaction.** Claude Code automatically compresses prior messages as conversations approach context limits. If early ledger entries are compacted, the agent loses detail from early turns. The continue/conclude logic depends on the full delta sequence (two consecutive `static` turns trigger plateau detection), which requires access to recent entries. Cumulative state (total claims, revision count) requires access to all entries.

**No auditability.** When the agent returns its synthesis, the ledger is gone. There's no way to verify after the fact that the agent's decisions (continue/conclude, follow-up selection) were consistent with what it recorded.

---

## 3. Proposed Architecture: Server-Owned Ledger

### Core principle: separate language from state

The agent is an LLM — strong at understanding what Codex said, extracting meaning, composing follow-ups. The MCP server is Python code — strong at validation, computation, and persistent state. The separation:

| Responsibility | Owner | Rationale |
|---------------|-------|-----------|
| Interpret Codex's response | Agent | Requires language understanding |
| Extract claims, position, unresolved | Agent | Semantic extraction from natural language |
| Validate ledger entry structure | Server | Mechanical: counters match claims? Quality correctly derived? |
| Compute derived fields | Server | Counters, quality derivation — deterministic |
| Store cumulative state | Server | Running totals, claim registry across turns — survives compaction |
| Continue/conclude decision | Server | Mechanical: delta sequence + unresolved list + turn budget |
| Entity extraction from claims | Server | Already implemented (regex-based, `process_turn`) |
| Scout template selection | Server | Already implemented (`process_turn`) |
| Compose follow-up question | Agent | Requires posture-aware language generation |

The agent becomes the **language layer**: it translates between natural language (Codex responses, follow-up questions) and structured data (ledger entries, scout results). The server becomes the **state layer**: it validates, stores, computes, and enforces conversation rules mechanically.

### What the server gains

**Structural validation.** The server rejects or corrects malformed entries before they pollute conversation state. If the agent reports `delta: static` alongside `new_claims=3`, the server catches the inconsistency.

**Mechanical continue/conclude.** Plateau detection (two consecutive `static` turns), budget management, and the closing probe requirement become server-side computation. The agent receives `action: "continue"` or `action: "closing_probe"` — it doesn't decide.

**Compaction-safe state.** The server maintains the full claim registry, running totals, and turn history keyed by `conversation_id`. Even if the agent's early context is compacted, it receives a `ledger_summary` from the server that reconstructs essential state.

**Auditability.** The server can log the full ledger history for post-conversation inspection.

### What stays with the agent

**Semantic extraction.** "Codex argued that event sourcing is overkill" is a language understanding task. The agent parses the Codex response and produces structured data (claims, position, delta, tags, unresolved). No Python code can do this.

**Follow-up composition.** The server provides the action (`continue`), scout evidence, and conversation state. The agent decides *how* to phrase the follow-up based on posture, conversational dynamics, and what will be most productive.

**Posture adaptation.** Adversarial vs. collaborative vs. exploratory probing requires language judgment, not mechanical rules.

---

## 4. API Evolution

### Current `process_turn` input

```python
class TurnRequest:
    schema_version: str
    turn_number: int
    conversation_id: str
    focus: Focus               # text, claims, unresolved
    posture: str               # adversarial / collaborative / exploratory / evaluative
    context_claims: list[Claim]
    evidence_history: list[EvidenceRecord]
```

The agent sends a narrow slice: just the current focus with its claims and unresolved items. Cumulative claims go in `context_claims`. Evidence history is passed back each turn.

### Proposed `process_turn` input

```python
class TurnRequest:
    schema_version: str
    turn_number: int
    conversation_id: str
    posture: str

    # Full ledger entry — agent extracts from Codex response, server validates
    position: str                  # 1-2 sentence summary of Codex's key point
    claims: list[Claim]            # All claims this turn with status
    delta: str                     # advancing / shifting / static
    tags: list[str]                # challenge, concession, new_reasoning, etc.
    unresolved: list[Unresolved]   # Questions opened or left unanswered

    # Scouting context (existing)
    focus: Focus
    evidence_history: list[EvidenceRecord]
```

Key changes:
- `position`, `claims`, `delta`, `tags`, `unresolved` are the full ledger entry (previously maintained only in-context)
- `context_claims` removed — the server computes cumulative claims from its stored history
- `evidence_history` may also become server-managed (the server already tracks it per `conversation_id`)

### Current `process_turn` output

```python
class TurnPacket:
    scout_options: list[ScoutOption]
    scout_token: str
    turn_request_ref: str
```

The server returns scout options only.

### Proposed `process_turn` output

```python
class TurnPacket:
    # Existing: scouting
    scout_options: list[ScoutOption]
    scout_token: str
    turn_request_ref: str

    # New: validated ledger state
    validated_entry: LedgerEntry   # Server-computed derived fields (counters, quality)
    cumulative: CumulativeState    # Running totals, claim count, revision count, concession count

    # New: conversation control
    action: str                    # "continue" / "closing_probe" / "conclude"
    action_reason: str             # Mechanical explanation of why

    # New: compaction-safe snapshot
    ledger_summary: str            # Compact text summary of full conversation state
```

The server returns everything the agent needs to proceed: validated state, conversation-level decisions, scout options, and a compaction-safe summary.

---

## 5. Agent Loop Simplification

### Current loop (3 steps, all in-context)

```
1. Get Codex response
2. Parse response, update ledger in context
   - Extract position, claims, delta, tags, unresolved
   - Derive counters and quality (by following rules)
3. Decide continue/conclude (by checking rules against ledger)
4. Select follow-up (priority list: unresolved → unprobed claims → weakest claim → posture probe)
5. Send follow-up to Codex
```

Steps 2-4 are all rule-following tasks where the agent must correctly apply mechanical rules. Drift risk is high.

### Proposed loop (server-assisted)

```
1. Get Codex response
2. Extract structured data from response (semantic work — agent's strength)
   - Position, claims, delta, tags, unresolved
3. Call process_turn with extracted data
4. Receive: validated entry + cumulative state + action + scout options + ledger summary
5. If scout warranted, call execute_scout
6. Compose follow-up based on:
   - action (continue / closing_probe / conclude)
   - scout evidence (if any)
   - posture
   - ledger summary (compaction-safe reference)
7. Send follow-up to Codex
```

Steps 3-4 replace three agent responsibilities (derivation, validation, decision) with a single MCP call that returns authoritative answers. The agent does what it's good at (steps 2 and 6) and delegates what it's unreliable at (steps 3-4).

---

## 6. Relationship to Existing Design Spec

The design spec (Section 3) describes a 7-step loop assuming the agent maintains all state in-context. This proposal changes the ownership model but preserves the same logical steps:

| Design Spec Step | Proposed Owner | Notes |
|-----------------|----------------|-------|
| 1. Update ledger | Agent extracts → Server validates and stores | Split responsibility |
| 2. Extract entities | Server | Already implemented |
| 3. Select focus | Server (part of `process_turn` response) | Could move server-side with full ledger context |
| 4. Select template | Server | Already implemented |
| 5. Execute scout | Server (`execute_scout`) | Already implemented |
| 6. Reframe planning | Agent + Server | Server provides evidence; agent decides reframe |
| 7. Render follow-up | Agent | Language generation stays with agent |

The 7-step structure is preserved. The change is WHERE each step runs, not WHAT each step does.

---

## 7. Open Questions

### Error handling

When the server rejects a ledger entry (structural inconsistency), what happens?

Options:
- **Server auto-corrects and warns:** Server fixes derivation errors (e.g., recomputes counters from claims) and includes a warning in the response. Agent sees corrected state.
- **Server rejects, agent retries:** Server returns an error with details. Agent re-extracts and resubmits. Risk: retry burns a turn.
- **Server accepts with annotations:** Server stores the entry as-is but flags inconsistencies in the response. Agent can self-correct on the next turn.

### Follow-up priority selection

The current agent applies a priority list for follow-up selection: unresolved items → unprobed claims → weakest claim → posture probe. Should this move server-side?

Arguments for: the priority list is mechanical, and the server has full ledger state to evaluate it.
Arguments against: the agent may have conversational judgment about which unresolved item is most productive to pursue.

Possible hybrid: server ranks follow-up candidates, agent selects from the ranked list.

### Backward compatibility

Does `process_turn` need to support both the current narrow API (focus-only) and the proposed full-ledger API?

Options:
- **Clean break:** New API version. Existing tests update to new schema.
- **Schema version gating:** `schema_version: "0.1.0"` uses current API, `"0.2.0"` uses full-ledger API.
- **Additive:** New fields are optional. Server detects which fields are present and adapts.

### Ledger summary design

How compact can the summary be while still letting the agent reason effectively after compaction?

The summary needs to support:
- Follow-up composition (what's the conversation about? what's the current state?)
- Posture adaptation (what's the dynamic? adversarial but converging?)
- Synthesis (when concluding, what are the key outcomes?)

Rough estimate: 200-400 tokens for a summary covering 5-8 turns of conversation.

### Focus selection

Currently the agent selects focus from a priority list. With full ledger state in the server, focus selection could move server-side. But focus selection has a semantic component — "which unresolved item is most important?" involves judgment about the conversation's direction.

### State lifecycle

When does conversation state get cleaned up? Options:
- Server maintains state for the duration of a conversation (keyed by `conversation_id`), cleans up on conclude
- Server persists state to disk for cross-session recovery (overkill for MVP?)
- In-memory only, lost on server restart (acceptable for MVP?)

---

## 8. Implementation Considerations

### Scope of change

This proposal affects:
- **MCP server** (`packages/context-injection/`): New `TurnRequest` fields, new `TurnPacket` fields, ledger validation logic, cumulative state management, continue/conclude computation, ledger summary generation
- **Codex-dialogue agent** (`.claude/agents/codex-dialogue.md`): Rewrite Phase 2 conversation loop, add `mcp__context-injection__process_turn` and `mcp__context-injection__execute_scout` to tool list, simplify rule-following instructions
- **Protocol contract** (`docs/references/context-injection-contract.md`): Updated schemas
- **Tests**: New server-side tests for validation, cumulative state, continue/conclude logic, ledger summary

### Risk

The main risk is that extending the server significantly increases its scope. It goes from "scout executor" to "conversation controller." The 739 existing tests cover the scout execution pipeline; the new responsibilities (ledger validation, cumulative state, conversation control) need their own test coverage.

Mitigation: the new responsibilities are all mechanical (validation, computation, state management) — exactly the kind of logic that's easy to test exhaustively.

### Relationship to cross-model learning

The cross-model learning system (design spec at `docs/plans/2026-02-10-cross-model-learning-system.md`) also integrates with the codex-dialogue agent, injecting learning cards into consultations. If the context injection server evolves into a conversation controller, the learning card injection could go through the same server — cards become another input to `process_turn` alongside ledger data and evidence.

This is speculative and should not drive the current design, but it's worth noting that the architectural direction is compatible.

---

## 9. Next Steps

1. **Review this document** — confirm the architectural direction before planning implementation
2. **Read the protocol contract** (`docs/references/context-injection-contract.md`) to understand the current API surface in detail
3. **Write an implementation plan** for the agent integration, using this document as the architectural foundation
4. **Implement** on a feature branch
