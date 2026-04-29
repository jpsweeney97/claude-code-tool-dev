# T-20260416-01: codex.dialogue.reply extraction mismatch on items-array response shape

```yaml
id: T-20260416-01
date: 2026-04-16
status: open
priority: medium
tags: [codex-collaboration, dialogue, bug, post-benchmark, mcp-dispatch]
blocked_by: []
blocks: []
effort: medium
```

## Dual record

This ticket captures two independent facts. Do not conflate them when revisiting.

**Benchmark status.** The B3 candidate run (`B3-candidate`, thread `019d979c-f50c-7213-9729-be04ad765642`, commit `fa75111b`) is preserved as captured — transcript, synthesis, and metadata exported to staging. The extraction-path failure this ticket tracks does not on its own meet any invalidation trigger at `docs/benchmarks/dialogue-supersession/v1/operator-procedure.md:660-666`, and the non-convergence is accurately recorded in metadata (`converged_within_budget: false`, `termination_code: error`). **Final scored-validity classification for this row belongs to the parent benchmark track `T-20260330`** — including how the commit-reconciliation question in §"Why the B3 run stays valid" is resolved. This bug ticket does not assert a scored-validity verdict; it preserves the artifact and its finding. **Do not reclassify the run as invalid + superseded from this ticket's side** — that would erase the finding the benchmark was designed to surface and preempt a decision that is not this ticket's to make.

**Product defect.** Independently, there is a real parse-path bug in `codex.dialogue.reply`: replies delivered via the `items[] -> agentMessage` shape are extracted as empty string, producing a `Consult result parse failed: expected JSON object` error that hard-terminates the dialogue. This is the bug this ticket tracks and will eventually fix.

## Symptom

`codex.dialogue.reply` terminates a dialogue with `CommittedTurnParseError` and error text `"Reply turn committed but response parsing failed: Consult result parse failed: expected JSON object. Got: ''"` when the Codex runtime delivers the agent message via `items[] -> agentMessage` instead of the top-level `agentMessage` field.

Observable outcomes:
- Dialogue terminates mid-turn
- The turn IS committed to durable state (per the commit-before-parse design at `dialogue.py:498-499`) and can be retrieved via `codex.dialogue.read`, but the in-dialogue caller sees only the error
- Metadata fields: `converged_within_budget: false`, `termination_code: error`, `termination_reason` populated with the parse error message

## Reproduction context

First observed in B3 candidate benchmark run on 2026-04-16.

| Field | Value |
|---|---|
| Thread ID | `019d979c-f50c-7213-9729-be04ad765642` |
| Run ID | `a39c2738-1af9-4e45-931e-833d6828c6d6` |
| Commit | `fa75111b` |
| Posture | adversarial |
| Turn budget | 6 (3 completed before termination) |
| Triggering turn | T3 (adversarial pressure-test round) |
| Codex reply (rollout) | Substantive ~4000-character JSON reply with `position`, `evidence[5]`, `uncertainties[3]`, `follow_up_branches[3]` — verified present in session rollout |
| Codex reply (parse step) | Empty string |
| Rollout path | `/Users/jp/.codex/sessions/2026/04/16/rollout-2026-04-16T14-45-39-019d979c-*.jsonl` |

Conditions that appear to correlate (not confirmed as causal):
- Longer Codex replies (~4000 chars in observed case)
- Adversarial posture (likely via longer/more complex prompts producing longer replies)
- Complex turns emitting the full schema (`position`, `evidence[]`, `uncertainties[]`, `follow_up_branches[]`)

## Root cause

The live runtime and historical read path use different data sources for
agent message extraction:

| Path | Location | Data source | Handles missing agent message? |
|---|---|---|---|
| `reply()` dispatch | `runtime.py:268-273` → `dialogue.py:498-502` | Live `item/completed` notifications | **No** — if no `item/completed` with `type: "agentMessage"` fires during the turn, `agent_message` stays `""` |
| `read()` extraction | `dialogue.py:984-1001` (`_read_turn_agent_message`) | Historical `thread/read` turn projections | **Yes** — tries top-level `agentMessage` field, falls back to `items[]` |

The runtime's notification loop (`runtime.py:249-292`) captures agent
messages via `item/completed` at `runtime.py:268-273`. When this
notification fires with `item.type == "agentMessage"`, the text is
captured correctly. The bug triggers when the `item/completed`
notification path fails to deliver the agent message — `agent_message`
stays `""`, and `parse_consult_response("")` raises
`json.JSONDecodeError` from `prompt_builder.py:58-63`, which `reply()`
wraps as `CommittedTurnParseError` at `dialogue.py:504-509`.

The `_read_turn_agent_message` helper cannot be shared directly to the
runtime notification loop because it parses `thread/read` projection
shapes (top-level `agentMessage` or nested `items[]` on turn dicts),
not live notification shapes (`item/completed`,
`item/agentMessage/delta`). These are fundamentally different data
sources with different JSON structures.

## Why the B3 run stays valid

Per `docs/benchmarks/dialogue-supersession/v1/operator-procedure.md:660-666`, a benchmark run is invalid only if ONE of:

1. Scope violation (scouting outside `allowed_roots`)
2. Evidence-budget overflow (`evidence_count > max_evidence`)
3. Run condition breach (wrong commit, non-clean tree, session reuse)
4. Missing artifacts (transcript or synthesis not saved)

None apply to B3 candidate:

1. All 12 Codex `exec_command` scouts stayed within `allowed_roots`; all final-claim citations resolve to the three allowed files
2. `evidence_count: 2 ≤ max_evidence: 15`
3. Fresh session, clean tree, canonical session_id (commit story in the note below)
4. All three artifacts exported to staging

The procedure treats `converged_within_budget` as a **diagnostic metric** (`operator-procedure.md:519`), not a validity condition. A non-converged run is still valid evidence — it evidences something specific about the system under test.

### Commit reconciliation (benchmark-track concern, not B3-specific)

The B3 candidate ran on `fa75111b` (current HEAD at run time). The manifest records `run_commit: 693551cc`, which is `fa75111b`'s ancestor by two commits: `f0fde082` (manifest update) and `fa75111b` (operator-procedure `evidence_count` amendment). Both intervening commits are documentation-only — no system-under-test behavior change.

The same mismatch applies uniformly to B1 candidate and B3 baseline (all three ran on `fa75111b` as well). Only B1 baseline ran on an earlier commit (`693551cc` era).

Under a strict reading of `operator-procedure.md:66` ("all runs must use the same commit"), this is a benchmark-track reconciliation concern that belongs to the parent ticket `T-20260330`, not to this bug ticket. Reconciliation options (to be decided at parent-ticket level, not here):

- Update `manifest.run_commit` to `fa75111b` and accept B1 baseline as a pre-amendment artifact recorded under its actual run commit
- Rerun B1 baseline on `fa75111b` so all four post-amendment runs share the same commit
- Document the doc-only drift as a benchmark-procedural exception

This ticket does not resolve that reconciliation. It preserves the B3 candidate artifact for whatever resolution the parent track chooses. The commit mismatch is not a B3-specific signal; it does not change the extraction-bug findings captured here.

### Contract-integrity constraint on mid-track patching

Per `operator-procedure.md:66`, all runs must use the same commit. Patching this bug mid-benchmark and rerunning B3 candidate on a new commit would violate the `run_commit` invariant and render aggregate metrics across B1/B3/B5/B8 incoherent. This applies independently of the commit-reconciliation question above.

## Proposed fix

### Protocol analysis (updated 2026-04-29)

The Codex App Server delivers agent message content through three
notification methods during a live turn:

| Notification | Schema fixture | Shape | Runtime captures? |
|---|---|---|---|
| `item/completed` | `ItemCompletedNotification.json` | `{item: ThreadItem, threadId, turnId}` — full item with `type`, `text`, `id` | **Yes** (`runtime.py:268-273`) |
| `item/agentMessage/delta` | `AgentMessageDeltaNotification.json` | `{delta: string, itemId, threadId, turnId}` — streaming text chunk | **No** — unhandled |
| `turn/completed` | `TurnCompletedNotification.json` | `{turn: Turn, threadId}` — terminal signal | Yes (terminal, returns `TurnExecutionResult`) |

**Critical schema constraint on `Turn.items`** (from
`TurnCompletedNotification.json:1285`, replicated in
`ThreadReadResponse.json` and `ItemCompletedNotification.json`):

> "Only populated on a `thread/resume` or `thread/fork` response. For
> all other responses and notifications returning a Turn, the items
> field will be an empty list."

Since `turn/completed` is a notification (not `thread/resume` or
`thread/fork`), **`turn_payload["items"]` is always `[]`**. A fallback
targeting `turn/completed.turn.items[]` would parse an empty list and
return `""` — no improvement over the current behavior.

**The previous ticket revision (2026-04-29) proposed a
`turn/completed.turn.items[]` fallback; it is withdrawn based on the
schema evidence above.**

Additionally, the `Turn` schema defines only `{id, items, status,
error}` — no top-level `agentMessage` field. The `agentMessage` field
that `_read_turn_agent_message` reads from `thread/read` turn dicts is
a server-side projection extension not captured in the typed schema,
further confirming that notification shapes and `thread/read` projection
shapes are distinct.

### Candidate fix mechanisms

Three viable approaches, ordered by implementation simplicity:

**A: Post-completion `thread/read` fallback.** When `agent_message == ""`
after `turn/completed`, call `read_thread(thread_id)` and extract from
the last completed turn's projection using the existing
`_read_turn_agent_message` logic. The B3 evidence proves the text is
in the session log — `thread/read` is a guaranteed recovery path.

- Pro: Guaranteed to have the data (B3 proves the session log had the
  text)
- Pro: Simple — one conditional `read_thread()` call on the failure path
- Pro: Reuses the proven `_read_turn_agent_message` extraction (it
  parses `thread/read` projections, which is exactly this data source)
- Con: Extra round-trip latency on the failure path
- Con: Requires `thread_id` access in the notification loop (available
  from `turn/completed` params at `runtime.py:275`)

**B: Delta assembly.** Add `item/agentMessage/delta` handling to the
notification loop. Accumulate deltas keyed by `itemId`, and when
`turn/completed` arrives with `agent_message` still empty, assemble
from the accumulated deltas.

- Pro: Captures a notification path the runtime currently ignores
  entirely
- Pro: No extra API call; stays within the notification loop
- Con: Need to verify deltas are always delivered when `item/completed`
  is not (the B3 failure mode is unconfirmed — deltas may also be
  absent)
- Con: Assembly complexity (ordering, multi-item dedup)
- Con: Cannot prove correctness without confirming the B3 failure mode
  involved missing `item/completed` but present deltas

**C: Investigate `item/completed` failure mode first.** Before building
fallbacks, examine the B3 rollout to determine why `item/completed` with
`type: "agentMessage"` did not fire. Possible causes: `turnId` filtering
mismatch (`runtime.py:260`), item not emitted for this turn pattern,
notification dropped. `TurnExecutionResult.notifications` preserves the
full notification stream from the B3 turn.

- Pro: Might reveal the bug is simpler (e.g., a `turnId` filter issue
  fixable in one line)
- Pro: Understanding the failure mode improves confidence in any
  fallback
- Con: Requires access to the B3 rollout file; reproduction is uncertain
- Con: Even if found, a fallback is still prudent for robustness

**Recommended approach:** Start with C (investigate the B3 notification
stream if available) to understand the failure mode, then implement A
(`thread/read` fallback) as the guaranteed-correct recovery. B (delta
assembly) is a future enhancement if the delivery pattern warrants it.

### Shared helper (still applicable)

Extract `_read_turn_agent_message` from `dialogue.py:984-1001` into
`turn_extraction.py` as:

```python
def extract_agent_message(raw_turn: Mapping[str, object]) -> str:
    ...
```

This is response-shape normalization for `thread/read` projection shapes,
not version-compatibility logic — `codex_compat.py` is not the right
home.

Wire into two sites:

1. **`dialogue.py` read path** (`dialogue.py:947`): replace
   `self._read_turn_agent_message(raw_turn)` with
   `extract_agent_message(raw_turn)`.
2. **`runtime.py` fallback path**: if mechanism A is chosen, the
   `thread/read` fallback calls `extract_agent_message` on the turn dict
   returned by `read_thread()` — same projection shape.

Do not modify `TurnExecutionResult` (4 fields, no `items`). Do not
modify `dialogue.reply()` except imports if needed. The fix canonicalizes
`agent_message` at the runtime layer, so all downstream consumers
(`reply`, `consult`, any future `TurnExecutionResult` consumer) are
fixed.

### Implementation tests

1. Unit: shared extractor handles top-level `agentMessage`.
2. Unit: shared extractor handles `items[]` with `type: "agentMessage"`.
3. Unit: shared extractor returns `""` when neither shape exists, and
   ignores malformed/non-dict items.
4. Runtime integration (load-bearing regression): test the chosen
   fallback mechanism. For mechanism A: fake JSON-RPC emits only
   `turn/completed` (no preceding `item/completed` notification);
   `_run_turn()` returns `TurnExecutionResult.agent_message` populated
   from the `thread/read` fallback. For mechanism B: fake emits
   `item/agentMessage/delta` notifications without `item/completed`;
   verify delta assembly.
5. Downstream regression: a reply flow backed by the runtime projection
   succeeds when the runtime result came from the fallback path —
   verify `parse_consult_response` receives valid canonical text.

### Out of scope

- Retry logic for genuinely empty Codex completions (separate concern)
- In-dialogue recovery via `codex.dialogue.read` fallback after parse
  failure
- Refactoring the commit-before-parse design at `dialogue.py:498-499`
  (the design is sound; the bug is upstream)
- Changing `TurnExecutionResult` shape
- Delta assembly (mechanism B) unless investigation (C) confirms it
  would have helped in B3

## Benchmark status (current truth as of 2026-04-29)

The benchmark track is complete. Tiers A and B concluded; parent ticket
`T-20260330`
(`docs/tickets/closed-tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md`)
is closed.

**Reproduction results:**

- The bug reproduced on B3 candidate and B5 candidate (both terminated
  with the same `CommittedTurnParseError` / items-array extraction
  mismatch). Evidence: `docs/benchmarks/dialogue-supersession/v1/summary.md`
  and `docs/benchmarks/dialogue-supersession/v1/runs.json`.
- The bug did not reproduce on B8 candidate (converged normally).
  Evidence: same sources.

The contract-integrity constraint on mid-track patching (§"Why the B3
run stays valid") is now historical — the benchmark track is complete.
The fix is no longer deferred.

**Next step:** Land the fix with tests and run one post-patch
verification.

**Closure criteria:**

- Patch landed on main with unit tests for both extraction shapes
  (tests #1-#3)
- Runtime integration test proving the chosen fallback mechanism
  populates `TurnExecutionResult.agent_message` when `item/completed`
  does not fire (test #4 — load-bearing regression)
- Downstream regression test proving `reply()` →
  `parse_consult_response` succeeds on fallback-produced text (test #5)
- One-run verification: rerun the B3 adversarial prompt on the patched
  commit in a fresh session, confirm convergence or natural termination
  without parse error
- Update this ticket with final commit SHA and mark `status: closed`

## References

| Reference | Location |
|---|---|
| Direct parse path (bug site) | `packages/plugins/codex-collaboration/server/dialogue.py:498-509` |
| Robust extractor (fix reuses) | `packages/plugins/codex-collaboration/server/dialogue.py:984-1001` |
| Runtime notification loop | `packages/plugins/codex-collaboration/server/runtime.py:249-292` |
| `item/completed` streaming capture | `packages/plugins/codex-collaboration/server/runtime.py:268-273` |
| Parse error source | `packages/plugins/codex-collaboration/server/prompt_builder.py:58-63` |
| MCP tool dispatch | `packages/plugins/codex-collaboration/server/mcp_server.py:263-272` |
| Turn.items schema constraint | `tests/fixtures/codex-app-server/0.117.0/v2/TurnCompletedNotification.json:1284-1290` (Turn definition) |
| AgentMessageDelta notification schema | `tests/fixtures/codex-app-server/0.117.0/v2/AgentMessageDeltaNotification.json` |
| ItemCompleted notification schema | `tests/fixtures/codex-app-server/0.117.0/v2/ItemCompletedNotification.json` |
| Benchmark contract — invalidation triggers | `docs/benchmarks/dialogue-supersession/v1/operator-procedure.md:660-666` |
| Benchmark contract — run_commit rule | `docs/benchmarks/dialogue-supersession/v1/operator-procedure.md:66` |
| Benchmark contract — diagnostic metrics | `docs/benchmarks/dialogue-supersession/v1/operator-procedure.md:519` |
| B3 candidate metadata | `/private/tmp/benchmark-v1-staging-20260415/B3-candidate-metadata.json` |
| B3 candidate synthesis | `/private/tmp/benchmark-v1-staging-20260415/B3-candidate-synthesis.md` |
| B3 candidate transcript | `/private/tmp/benchmark-v1-staging-20260415/B3-candidate-transcript.md` |
| Codex session rollout (B3 candidate) | `/Users/jp/.codex/sessions/2026/04/16/rollout-2026-04-16T14-45-39-019d979c-*.jsonl` |
| Parent ticket (supersession benchmark) | `docs/tickets/closed-tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md` |
