# D5: Agent Rewrite — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Delivery:** D5 of 6 (D1, D2, D3, D4a, D4b, D5)
**Objective:** Rewrite the codex-dialogue agent's Phase 2 conversation loop from the current 3-step in-context process to the 7-step server-assisted scouting loop.
**Execution order position:** 6 of 6 (D1 → D3 → D2 → D4a → D4b → D5)
**Branch:** `feature/context-injection-agent-integration`
**Package directory:** `packages/context-injection/`
**Test command:** `cd packages/context-injection && uv run pytest tests/ -v`

## Prerequisite Contract

**Requires:**
- D4b complete — 0.2.0 protocol fully functional with all tests passing
- The MCP server must be running with `process_turn` and `execute_scout` tools accepting/returning 0.2.0 schemas
- Source of truth: `context_injection/types.py` (0.2.0 schemas), `context_injection/pipeline.py` (pipeline behavior)

**Requires MCP tools:** `mcp__context-injection__process_turn`, `mcp__context-injection__execute_scout` (in addition to existing `mcp__codex__codex`, `mcp__codex__codex-reply`)

**Critical invariant:** The agent rewrite changes `.claude/agents/codex-dialogue.md` — this is a subagent definition (markdown instruction file), not Python code. The rewrite replaces the Phase 2 conversation loop while preserving Phase 1 (setup) and Phase 3 (synthesis) with targeted additions.

**Adaptation:** If the 0.2.0 protocol schema field names differ from this plan, adapt the agent instructions and note the mapping.

## Files in Scope

**Create:** None.

**Modify:**
- `.claude/agents/codex-dialogue.md` — Phase 2 conversation loop rewrite (7-step scouting loop)

**Out of scope:** All files not listed above. In particular, do NOT modify any Python code in `packages/context-injection/`.

## Done Criteria

- Agent rewrite complete
- Phase 2 loop uses `process_turn` and `execute_scout` MCP tools
- Phase 1 (setup) and Phase 3 (synthesis) preserved
- Agent instructions are clear and follow existing codex-dialogue patterns

## Scope Boundary

This document covers D5 only. After completing all tasks in this delivery, stop.

---

Rewrites `.claude/agents/codex-dialogue.md` Phase 2 conversation loop from 3-step manual ledger management to 7-step server-assisted scouting loop.

**Depends on:** D4 complete (server returns `action`, `ledger_summary`, `state_checkpoint`, `checkpoint_id`, `template_candidates`)
**Risk:** Medium — instruction design (not code), single file, but high-stakes (governs all future Codex conversations)

### Task 15: Phase 2 conversation loop rewrite

**Files:**
- Modify: `.claude/agents/codex-dialogue.md`

**Step 1: Read the current agent file**

Read `.claude/agents/codex-dialogue.md`. Verify:
- Frontmatter `tools:` line contains `mcp__codex__codex` and `mcp__codex__codex-reply`
- Phase 1 (Setup): lines 17-66
- Phase 2 (Conversation Loop): lines 68-185
- Phase 3 (Synthesis): lines 187-225
- Constraints: lines 227-234
- Output Format: lines 237-315

**Step 2: Update the YAML frontmatter**

Add context injection MCP tools to the `tools:` line.

Old (line 4):
```yaml
tools: Bash, Read, Glob, Grep, mcp__codex__codex, mcp__codex__codex-reply
```

New:
```yaml
tools: Bash, Read, Glob, Grep, mcp__codex__codex, mcp__codex__codex-reply, mcp__context-injection__process_turn, mcp__context-injection__execute_scout
```

**Step 3: Add context injection precondition**

Add after the existing MCP tools precondition (after line 15):

```markdown
- Context injection MCP tools `mcp__context-injection__process_turn` and `mcp__context-injection__execute_scout` should be available (see mode gating below)
- **Mode gating:** Start in `server_assisted` mode. If context injection tools are unavailable at conversation start (first call to `mcp__context-injection__process_turn` returns an error or times out), switch to `manual_legacy` mode for the remainder of the conversation. Do not switch modes mid-conversation after a successful `process_turn`.
```

**Step 4: Replace Phase 2 conversation loop**

Replace the entire Phase 2 section (lines 68-185 of the current file) with the text below.
Keep Phase 1 (lines 17-66) and everything after Phase 2 (line 186+) intact.

The complete replacement text for Phase 2:

````markdown
## Phase 2: Conversation Loop

### Start the conversation

Call `mcp__codex__codex` with:

| Parameter | Value |
|-----------|-------|
| `prompt` | Assembled briefing |
| `model` | `"gpt-5.3-codex"` |
| `sandbox` | `read-only` |
| `approval-policy` | `never` |
| `config` | `{"model_reasoning_effort": "xhigh"}` |

Persist `threadId` from the response (prefer `structuredContent.threadId`, fall back to top-level `threadId`).

Use `threadId` as `conversation_id` for `process_turn` calls.

### Conversation state

Initialize after starting the conversation:

| State | Initial value | Purpose |
|-------|--------------|---------|
| `threadId` | From Codex response | For `codex-reply` calls |
| `conversation_id` | Same as `threadId` | For `process_turn` calls |
| `state_checkpoint` | `null` | Opaque string; store from `process_turn` response, pass back next turn |
| `checkpoint_id` | `null` | Opaque string; store from `process_turn` response, pass back next turn |
| `turn_count` | `1` | Turns completed |
| `evidence_count` | `0` | Scouts executed (for synthesis statistics) |
| `turn_history` | `[]` | Per-turn list of `{validated_entry, cumulative, scout_outcomes}` — append after each successful `process_turn` response |

**Per-turn state retention:** After each successful `process_turn` response, append to `turn_history`:
- `validated_entry` — the server-validated ledger entry for this turn
- `cumulative` — the cumulative snapshot returned by the server
- `scout_outcomes` — list of scout results from Step 4 (empty if no scouts executed)

This accumulated history is required for Phase 3 synthesis (especially claim trajectory and "weakest claim" derivation) and for fallback synthesis if later turns error.

### Running ledger

The context injection server maintains the conversation ledger, computes counters, derives quality, detects convergence, and decides when to continue or conclude. The agent's role per turn:

1. **Extract** semantic data from the Codex response
2. **Send** to server via `process_turn`
3. **Act** on the server's `action` directive
4. **Pass through** checkpoints between turns

The server tracks: cumulative claim counts, plateau detection, closing probe state, evidence budget, and conversation state snapshots. The agent does not replicate this logic.

### Fallback Mode: Legacy Manual Loop

The 7-step per-turn loop is bypassed entirely in `manual_legacy` mode. Instead, use the original 3-step conversation loop:

1. **Extract** semantic data from the Codex response (same as Step 1 above)
2. **Evaluate** continue/conclude manually: count turns, detect repetition, apply closing probe if plateau detected (2+ consecutive `static` delta turns)
3. **Compose** follow-up using the posture patterns table and send via `codex-reply`

The agent manages its own ledger state, convergence detection, and turn budget. Synthesis (Phase 3) proceeds without `ledger_summary` or evidence data — reconstruct trajectory from the manually tracked extraction history.

### Per-turn loop (7 steps)

After each Codex response, execute steps 1-7 in order.

#### Step 1: Extract semantic data

Read the Codex response and extract:

| Field | Type | How to extract |
|-------|------|---------------|
| `position` | `string` | 1-2 sentence summary of Codex's key point this turn |
| `claims` | `list[{text, status, turn}]` | Each distinct claim with status (see table below) |
| `delta` | `string` | Single label: `advancing`, `shifting`, or `static` (see table below) |
| `tags` | `list[string]` | 0-2 tags from the tag table below |
| `unresolved` | `list[{text, turn}]` | Questions this turn opened or left unanswered |

**Claim status:**

| Status | When to assign |
|--------|---------------|
| `new` | Claim appears for the first time in this conversation |
| `reinforced` | Previously stated claim repeated with new evidence or reasoning |
| `revised` | Codex changed position on a previously stated claim |
| `conceded` | Codex abandoned a previously stated claim |

**Delta** (required, single-label — the decision-relevant signal):

| Delta | Meaning |
|-------|---------|
| `advancing` | New reasoning, evidence, or genuine pushback introduced |
| `shifting` | Position changed (concession) or topic moved to a different thread |
| `static` | Previous points restated without new substance |

Classify honestly: different phrasing of the same point is `static`, not `advancing`.

**Tags** (optional, multi-label):

| Tag | Signal |
|-----|--------|
| `challenge` | Pushed back on a claim with evidence or reasoning |
| `concession` | Changed position based on the argument |
| `tangent` | Shifted to a weakly-related topic |
| `new_reasoning` | Introduced a novel argument or framework |
| `expansion` | Built on an existing thread, added depth |
| `restatement` | Repeated a previous point without new substance |

#### Step 2: Call `process_turn`

Call `mcp__context-injection__process_turn` with:

```json
{
  "request": {
    "schema_version": "0.2.0",
    "turn_number": <turn_count>,
    "conversation_id": "<conversation_id>",
    "focus": {
      "text": "<the overarching topic under discussion>",
      "claims": [{"text": "<claim>", "status": "<status>", "turn": <n>}, ...],
      "unresolved": [{"text": "<question>", "turn": <n>}, ...]
    },
    "posture": "<current posture>",
    "position": "<position from Step 1>",
    "claims": [{"text": "<claim>", "status": "<status>", "turn": <n>}, ...],
    "delta": "<delta from Step 1>",
    "tags": ["<tag1>", "<tag2>"],
    "unresolved": [{"text": "<question>", "turn": <n>}, ...],
    "state_checkpoint": "<from previous turn's response, or null>",
    "checkpoint_id": "<from previous turn's response, or null>"
  }
}
```

**Field mapping:**
- Build `claims` list once from ledger extraction. Assign to BOTH `focus.claims` and top-level `claims` fields. On subsequent turns, `focus.claims` contains claims relevant to the current focus scope (not the full conversation history — the server accumulates history internally).
- Build `unresolved` list once. Assign to BOTH `focus.unresolved` and top-level `unresolved` fields.
- `focus.text` is the overarching topic (stable across turns), not the per-turn `position`.

**First turn:** Set `state_checkpoint` and `checkpoint_id` to `null`.

**Subsequent turns:** Pass `state_checkpoint` and `checkpoint_id` from the previous turn's `process_turn` response.

#### Step 3: Process the response

**On success** (`status: "success"`):

| Field | What to do |
|-------|-----------|
| `validated_entry` | Server-validated ledger entry. Use for follow-up composition — authoritative over your extraction. |
| `warnings` | Log internally. No action needed. |
| `cumulative` | Running totals: `total_claims`, `reinforced`, `revised`, `conceded`, `unresolved_open`. Use for conversation awareness. |
| `action` | **Directive:** `continue_dialogue`, `closing_probe`, or `conclude`. See Step 5. |
| `action_reason` | Human-readable explanation. Include in your internal reasoning. |
| `template_candidates` | Available scout options for evidence gathering. See Step 4. Fields per candidate: `rank`, `template_id`, `entity_key`, `scout_options` (each with `id`, `scout_token`). Note: `turn_request_ref` is NOT part of `template_candidates` — it is agent-derived in Step 4. |
| `budget` | `scout_available` (bool), `evidence_count`, `evidence_remaining`. |
| `ledger_summary` | Compact trajectory summary. Use in follow-up composition. |
| `state_checkpoint` | **Store** — pass in next turn's request. |
| `checkpoint_id` | **Store** — pass in next turn's request. |

**On error** (`status: "error"`):

| Code | Recovery |
|------|----------|
| `checkpoint_stale` | Retry once with `state_checkpoint=null` and `checkpoint_id=null`. If the retry also fails, synthesize from `turn_history` (proceed to Phase 3). |
| `checkpoint_missing` | Retry once only if a non-null checkpoint is available. If checkpoint is already null, synthesize from `turn_history` (proceed to Phase 3). |
| `checkpoint_invalid` | Do not retry. Synthesize from `turn_history` (proceed to Phase 3). |
| `ledger_hard_reject` | Re-examine the Codex response, correct your extraction, retry `process_turn`. Maximum one retry per turn. |
| `turn_cap_exceeded` | Do not retry. Proceed to Phase 3 (Synthesis). |
| Other codes | Do not retry. Synthesize from `turn_history` (proceed to Phase 3). |
| Transport/tool failure (after prior success) | Do not switch to `manual_legacy`. Proceed to Phase 3 (Synthesis) using `turn_history`. |

**Checkpoint retry cap:** Maximum 1 checkpoint retry per turn regardless of error code. If the retry also fails, synthesize from `turn_history`.

#### Step 4: Scout (optional)

**Skip this step** if `template_candidates` is empty.

If `template_candidates` is non-empty:

1. Select the highest-ranked candidate (lowest `rank` value)
2. **Clarifier check:** If the top candidate has `scout_options: []` (empty list), this is a clarifier — skip scouting for this turn. Instead, use the clarifier's question text in Step 6 follow-up composition (treat it as a high-priority unresolved item). Continue to Step 5. (Clarifiers do not consume evidence budget, so this check runs even when `budget.scout_available` is `false`.)
3. **Budget gate:** If `budget.scout_available` is `false`, skip scout execution (steps 4-6 below). Continue to Step 5.
4. Select its first `scout_option`
5. Call `mcp__context-injection__execute_scout`:

```json
{
  "request": {
    "schema_version": "0.2.0",
    "scout_option_id": "<from scout_option.id>",
    "scout_token": "<from scout_option.scout_token>",
    "turn_request_ref": "<conversation_id>:<turn_number>"
  }
}
```

6. On success:
   - Store `evidence_wrapper` (human-readable summary — include in follow-up)
   - Store `read_result` or `grep_result` if you need raw evidence data
   - Increment `evidence_count`
   - Note updated `budget`
7. On error: continue without evidence. Do not retry.

#### Step 5: Act on action

| Action | Do this |
|--------|---------|
| `continue_dialogue` | Compose follow-up (Step 6) and send (Step 7). |
| `closing_probe` | Compose closing probe (see fallback chain below). Send (Step 7). |
| `conclude` | Exit the loop. Proceed to Phase 3 (Synthesis). |
| Unknown action | Treat as `conclude` and log a warning: `"Unknown action '<action>' from process_turn — treating as conclude."` |

**Closing probe target fallback chain** (use the first available):
1. Highest-priority unresolved item from `validated_entry.unresolved`: "Given our discussion, what's your final position on [unresolved item]?"
2. If `validated_entry.unresolved` is empty, target the highest-impact claim from `turn_history` claim records: "Given our discussion, what's your strongest evidence for [claim]?"
3. If no claims available, use core thesis summary: "Given our discussion, what's your final position on [focus.text]?"

The server handles plateau detection, budget exhaustion, and closing probe sequencing internally. Trust the `action` — do not override it with your own continue/conclude logic.

**Budget precedence:** The agent's turn budget cap takes priority over the server's `action`. If `turn_count >= effective_budget` (see Turn management), treat any server action — including `continue_dialogue` — as `conclude`. This prevents runaway conversations when the server's budget tracking diverges from the agent's.

#### Step 6: Compose follow-up

Build the follow-up from these inputs. Priority order for choosing what to ask:

1. **Scout evidence** (if Step 4 produced results): Frame a question around `evidence_wrapper` using the evidence shape below
2. **Unresolved items** from `validated_entry.unresolved`
3. **Unprobed claims** tagged `new` in `validated_entry.claims`
4. **Weakest claim** derived from accumulated `turn_history` claim records (least-supported, highest-impact). Scan `validated_entry.claims` across all turns in `turn_history` — the weakest claim is the one with fewest `reinforced` statuses relative to its importance, not a value derived from aggregate counters in `cumulative`
5. **Posture-driven probe** from the patterns table

**When scout evidence is available**, use this shape:

```
[repo facts — inline snippet with provenance (path:line)]
[disposition — what this means for the claim under discussion]
[one question — derived from the evidence, not from the original follow-up]
```

This forces Codex to engage with evidence by making it the premise of the question.

**Target-lock guardrail:** When scout evidence is available, the follow-up question MUST target the claim or unresolved item that triggered the scout. Other observations from the evidence MAY be noted in the disposition field but MUST NOT change the question's target. This prevents enrichment hijack — tangential evidence drifting the conversation away from the claim under scrutiny.

**Known tradeoff:** Occasional one-turn delay on important side findings from scout evidence. Acceptable because side findings are captured in the disposition field and surface as new unresolved items for later prioritization.

**De-scoped: Reframe model.** The design spec (Section 12) flags reframe outcome detection as an unsolved problem at medium priority. Unreliable classification (focus answered / premise falsified / enrichment) in dense agent instructions creates more harm than benefit. The target-lock guardrail above provides the necessary constraint without classification. **Future path:** Server-side `reframe_outcome` field (deterministic classification with cross-turn state) if explicit outcome routing proves necessary.

Use `ledger_summary` for conversation awareness — knowing which claims are settled, what's still open, and the conversation trajectory.

#### Patterns by posture

| Posture | Patterns |
|---------|----------|
| **Adversarial** | "I disagree because...", "What about failure mode X?", "This assumes Y — what if Y is false?" |
| **Collaborative** | "Building on that, what if...", "How would X combine with Y?", "What's the strongest version of this?" |
| **Exploratory** | "What other approaches exist?", "What am I not considering?", "How does this relate to X?" |
| **Evaluative** | "Is that claim accurate?", "What about coverage of X?", "Where are the gaps?" |

#### Step 7: Send follow-up

Send via `mcp__codex__codex-reply` with the persisted `threadId`.

Increment `turn_count`. Return to Step 1 for the next Codex response.

### Turn management

- **Agent-side budget override (defense-in-depth, interim):** `effective_budget = min(max(1, user_budget), MAX_CONVERSATION_TURNS)` where `MAX_CONVERSATION_TURNS = 15`. This clamps the user-provided budget to `[1, 15]`. The server enforces its own turn cap, but this agent-side clamp provides defense-in-depth against server bugs or misconfiguration. Long-term: pass user budget through TurnRequest so the server can enforce it directly (separate ticket).
- Track turns used vs. `effective_budget`.
- **Budget 1:** No follow-ups. Extract semantic data, call `process_turn` once, synthesize from the single response.
- **Budget 2:** Run both turns through the loop. The server's `action` guides whether to continue after turn 1.
- **Budget 3+:** The server handles convergence detection and closing probes via `action`. Trust the directive.
- **Budget exceeded:** If `turn_count >= effective_budget`, treat any server action as `conclude` regardless of what the server returns. See Step 5 budget precedence.
- If `mcp__codex__codex-reply` fails mid-conversation, proceed directly to Phase 3 synthesis using `turn_history`. Use the most recent `cumulative` snapshot and `validated_entry` records from `turn_history` in place of the missing `ledger_summary`. Do not attempt to call `process_turn` again — there is no new Codex response to extract from.
````

**Step 5: Update Phase 3 synthesis**

Update the Phase 3 intro text: replace any reference to "walk the ledger entries" with "walk the `turn_history` (server-validated `validated_entry` records and cumulative snapshots)".

Add the following to the **Assembly process** section in Phase 3 (after the existing item 4 "Unresolved → Open Questions"):

```markdown
5. **Evidence trajectory:** For each turn in `turn_history` where `scout_outcomes` is non-empty, note: what entity was scouted, what was found (or not found), and its impact on the conversation (premise falsified, claim supported, or ambiguous).
6. **Claim trajectory:** Using the accumulated `validated_entry` records in `turn_history`, trace how each significant claim evolved across turns (new → reinforced/revised/conceded).
```

Add the following to the **Pre-flight checklist** (after the last existing checklist item):

```markdown
- [ ] Evidence statistics: scouts executed, entities scouted, impacts on conversation
```

**Step 6: Update output format**

Add to the **Conversation Summary** section (after the `Trajectory` line):

```markdown
- **Evidence:** [X scouts / Y turns, entities: ..., impacts: ...]
```

Add to the **Continuation** section (after "Recommended posture for continuation"):

```markdown
- **Evidence trajectory:** [which turns had evidence, what entities, what impacts]
```

Update the **Example** Conversation Summary to include evidence:

```markdown
- **Evidence:** 2 scouts / 4 turns (T2: `src/audit/store.py` — confirmed append-only pattern; T3: `config/schema.yaml` — found versioned envelope type)
```

Update the example Continuation section to include:

```markdown
- **Evidence trajectory:** T2 — `src/audit/store.py` read, confirmed append-only writes (claim supported); T3 — `config/schema.yaml` read, found envelope type with version field (claim supported)
```

**Step 7: Manual testing**

Run the codex-dialogue agent with a test topic that exercises the new loop:

1. **Start a test conversation:**

```
Use the Task tool to invoke the codex-dialogue agent:
  Topic: "Review the context injection pipeline architecture"
  Context: packages/context-injection/
  Goal: Evaluate the pipeline design
  Posture: evaluative
  Turn budget: 3
```

2. **Verify each per-turn loop iteration:**

- [ ] Agent extracts semantic data from Codex response (position, claims, delta, tags, unresolved)
- [ ] `process_turn` called with extracted data and correct schema version (`0.2.0`)
- [ ] Server response received with `action`, `ledger_summary`, `state_checkpoint`, `checkpoint_id`
- [ ] `state_checkpoint` and `checkpoint_id` from response passed to next turn's request
- [ ] Agent follows `action` directive (continue_dialogue → follow-up, closing_probe → closing probe question, conclude → exit to synthesis)

3. **Verify scout integration (if template_candidates returned):**

- [ ] Scout evaluated when `budget.scout_available` is true
- [ ] `execute_scout` called with correct `scout_option_id`, `scout_token`, and `turn_request_ref`
- [ ] `evidence_wrapper` from scout included in follow-up composition
- [ ] Follow-up uses the evidence shape (repo facts → disposition → question)

4. **Verify synthesis:**

- [ ] Synthesis uses `ledger_summary` for trajectory (not manually reconstructed)
- [ ] Evidence trajectory included if scouts were executed
- [ ] Output format includes evidence statistics line
- [ ] Continuation section includes evidence trajectory

5. **Verify error recovery:**

- [ ] If `process_turn` returns `checkpoint_stale`, agent retries with `state_checkpoint=null` and `checkpoint_id=null`
- [ ] If `execute_scout` fails, agent continues without evidence (no retry)
- [ ] If Codex reply fails mid-conversation, agent proceeds directly to Phase 3 synthesis using `turn_history`
- [ ] If `process_turn` returns `checkpoint_missing`, agent retries once only if a non-null checkpoint is available; otherwise synthesizes from `turn_history`
- [ ] If `process_turn` returns `checkpoint_invalid`, agent does not retry and synthesizes from `turn_history`
- [ ] If `process_turn` returns `ledger_hard_reject`, agent re-examines extraction and retries once (maximum one retry per turn)
- [ ] If `process_turn` returns `turn_cap_exceeded`, agent does not retry and proceeds to Phase 3
- [ ] If `process_turn` returns an unknown action, agent treats it as `conclude` and logs a warning
- [ ] Agent's turn budget cap takes priority over server `action` (budget-precedence override)
- [ ] Transport/tool failure after initial success: agent does not switch to `manual_legacy`, proceeds to Phase 3 using `turn_history`
- [ ] Clarifier handling when `budget.scout_available=false`: clarifier check still runs, clarifier question used in follow-up
- [ ] `turn_history` is appended after each successful `process_turn` response (append semantics verified)

6. **Verify fallback (context injection unavailable — `manual_legacy` mode):**

- [ ] If context injection MCP tools are not available at conversation start, agent switches to `manual_legacy` mode
- [ ] In `manual_legacy` mode, conversation loop uses the Legacy Manual Loop (3-step) instead of the 7-step server-assisted loop
- [ ] Mode is not switched mid-conversation after a successful `process_turn`
- [ ] Synthesis still produces valid output without evidence data or `ledger_summary`

**Step 8: Commit**

```bash
git add .claude/agents/codex-dialogue.md
git commit -m "$(cat <<'EOF'
feat(agent): rewrite codex-dialogue Phase 2 to 7-step server-assisted loop

Replace manual ledger management with context injection server integration.
Agent extracts semantic data, server validates entries, tracks conversation
state, detects convergence, and controls closing probes via action directive.

Adds: process_turn calls, scout execution, checkpoint pass-through,
evidence-aware follow-ups, action-driven convergence detection.

Removes: manual counter computation, quality derivation, continue/conclude
rule evaluation, closing probe tracking.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```
