# T-20260416-01: codex.dialogue.reply returns empty agent_message despite Codex session log containing reply

```yaml
id: T-20260416-01
date: 2026-04-16
status: closed
priority: medium
tags: [codex-collaboration, dialogue, bug, post-benchmark, mcp-dispatch]
blocked_by: []
blocks: []
effort: medium
```

## Dual record

This ticket captures two independent facts. Do not conflate them when revisiting.

**Benchmark status.** The B3 candidate run (`B3-candidate`, thread `019d979c-f50c-7213-9729-be04ad765642`, commit `fa75111b`) is preserved as captured — transcript, synthesis, and metadata exported to staging. The extraction-path failure this ticket tracks does not on its own meet any invalidation trigger at `docs/benchmarks/dialogue-supersession/v1/operator-procedure.md:660-666`, and the non-convergence is accurately recorded in metadata (`converged_within_budget: false`, `termination_code: error`). **Final scored-validity classification for this row belongs to the parent benchmark track `T-20260330`** — including how the commit-reconciliation question in §"Why the B3 run stays valid" is resolved. This bug ticket does not assert a scored-validity verdict; it preserves the artifact and its finding. **Do not reclassify the run as invalid + superseded from this ticket's side** — that would erase the finding the benchmark was designed to surface and preempt a decision that is not this ticket's to make.

**Product defect.** Independently, there is a real parse-path bug in `codex.dialogue.reply`: the live notification stream can fail to deliver an `item/completed` notification for the agent message, leaving `TurnExecutionResult.agent_message` as empty string and producing a `Consult result parse failed: expected JSON object` error that hard-terminates the dialogue. The Codex session log contains the agent message text (verified in B3 rollout), and `thread/read` projection recovery is the implementation hypothesis — but the exact projection behavior for this failure class has not been directly captured. This is the bug this ticket tracks and will eventually fix.

## Symptom

`codex.dialogue.reply` terminates a dialogue with `CommittedTurnParseError` and error text `"Reply turn committed but response parsing failed: Consult result parse failed: expected JSON object. Got: ''"` when the live notification stream fails to populate `TurnExecutionResult.agent_message` — even though the Codex session log contains the full agent message text.

Observable outcomes:
- Dialogue terminates mid-turn
- The turn IS committed to durable state (per the commit-before-parse design at `dialogue.py:498-499`) and the agent message text is present in the Codex session log, but the in-dialogue caller sees only the error. Whether `codex.dialogue.read` (which calls `thread/read`) can retrieve the text for this failure class is the implementation hypothesis to prove
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
after `turn/completed` with `status == "completed"`, call
`read_thread(thread_id)` and extract from the turn matching `turn_id`
in the returned turns list. The B3 evidence proves the text existed
in the Codex session log — `thread/read` is a plausible recovery path,
but its projection shape for this failure class has not been directly
captured. The post-patch live reproduction is the proof point.

**Turn selection:** Look up by `raw_turn["id"] == turn_id`, not by
position ("last completed turn"). Position-based selection is unsafe:
`thread/read` ordering may differ from notification order, overlapping
advisory turns could exist in future, and recovery/fork state can change
ordering. A wrong but schema-valid stale turn would pass
`parse_consult_response` and corrupt the dialogue semantics. If no
turn matching `turn_id` is found, or the matching turn has no
extractable message, fall through to the existing empty-string behavior
(see failure semantics below).

**Scope constraint:** The fallback MUST be scoped to advisory turns
only. `_run_turn()` is shared between `run_advisory_turn()` (advisory
path — `allowed_terminal_statuses=("completed",)`) and
`run_execution_turn()` (delegation path —
`allowed_terminal_statuses=("completed", "interrupted", "failed")`).
Execution turns legitimately complete with empty `agent_message` on
`interrupted` or `failed` status. An unconditional fallback would add
`thread/read` calls to delegation paths where empty is correct, and
could introduce new failure modes. Implementation options: (a) add a
`fallback_on_empty_message: bool` parameter to `_run_turn()`, set `True`
only in `run_advisory_turn()`; (b) apply the fallback as post-processing
in `run_advisory_turn()` rather than in the shared `_run_turn()`.

**Failure semantics:** The fallback is best-effort. If `read_thread()`
raises, returns no matching turn, or the matching turn has no extractable
message, the fallback MUST NOT raise — it falls through and returns the
original `TurnExecutionResult` with `agent_message == ""`. The caller
(`dialogue.reply()`) then hits the existing `CommittedTurnParseError`
path, preserving today's committed-turn parse-failure semantics. An
unguarded exception from the fallback would escalate to dispatch-failure
semantics, potentially invalidating the runtime and quarantining the
handle — a worse outcome than the parse error it was trying to prevent.

- Pro: Plausible recovery path (B3 proves the text existed in session
  state)
- Pro: Simple — one conditional `read_thread()` call on the failure path
- Pro: Reuses the proven `_read_turn_agent_message` extraction (it
  parses `thread/read` projections, which is exactly this data source)
- Con: Extra round-trip latency on the failure path
- Con: `thread/read` projection shape for this failure class is unproven
  — post-patch reproduction is the proof point
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

**C: Investigate `item/completed` failure mode.** Reproduce the B3
scenario with instrumentation to determine why `item/completed` with
`type: "agentMessage"` did not fire. Possible causes: `turnId` filtering
mismatch (`runtime.py:260`), item not emitted for this turn pattern,
notification dropped.

Note: `TurnExecutionResult.notifications` preserves the notification
stream in memory, but `dialogue.reply()` does not persist it when
parsing fails — the tuple is lost with the `TurnExecutionResult` object.
The B3 rollout file (`/Users/jp/.codex/sessions/.../rollout-*.jsonl`) is
the Codex Desktop session log, not the App Server JSON-RPC notification
stream. This mechanism therefore requires fresh reproduction with
notification-stream logging, not examination of existing B3 artifacts.

- Pro: Might reveal the bug is simpler (e.g., a `turnId` filter issue
  fixable in one line)
- Pro: Understanding the failure mode improves confidence in any
  fallback
- Con: Requires fresh reproduction; the B3 notification stream was not
  persisted
- Con: Even if found, a fallback is still prudent for robustness

**Recommended approach:** Implement A (`thread/read` fallback) as the
primary fix — it is the only mechanism that can be tested without
reproducing the exact B3 failure mode. C (notification-stream
investigation) is optional confidence-building diagnostic work: useful
for understanding the root cause but not a gate for landing the fix.
B (delta assembly) is a future enhancement if the delivery pattern
warrants it.

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
4. Runtime integration (load-bearing regression): fake JSON-RPC emits
   only `turn/completed` (no preceding `item/completed` notification);
   `run_advisory_turn()` returns `TurnExecutionResult.agent_message`
   populated from the `thread/read` fallback via turn-ID lookup.
5. Downstream regression: a reply flow backed by the runtime projection
   succeeds when the runtime result came from the fallback path —
   verify `parse_consult_response` receives valid canonical text.
6. Fallback failure — `read_thread` raises: verify
   `run_advisory_turn()` returns the original `TurnExecutionResult`
   with `agent_message == ""` (does not escalate to dispatch failure).
7. Fallback failure — no matching turn ID: `thread/read` returns turns
   but none match `turn_id`; verify same fall-through behavior as #6.
8. Fallback failure — matching turn, no extractable message: matching
   turn exists but `extract_agent_message` returns `""`; verify same
   fall-through behavior as #6.
9. Execution turn not affected: `run_execution_turn()` with empty
   `agent_message` on `interrupted` status does NOT trigger the
   `thread/read` fallback.

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
  with `CommittedTurnParseError` — empty `agent_message` despite
  Codex session log containing the reply text). Evidence:
  `docs/benchmarks/dialogue-supersession/v1/summary.md` and
  `docs/benchmarks/dialogue-supersession/v1/runs.json`.
- The bug did not reproduce on B8 candidate (converged normally).
  Evidence: same sources.

The contract-integrity constraint on mid-track patching (§"Why the B3
run stays valid") is now historical — the benchmark track is complete.
The fix is no longer deferred.

**Closed (2026-04-30) by accepted engineering sufficiency standard.**

Implementation and tests landed in `00ec0054`. Live post-patch
non-regression evidence landed in `c5807d84` (5 adversarial turns across
3 sessions on Codex `0.125.0`, all completed without error). The fallback
did not fire in any live run — `item/completed` delivered agent messages
on the normal path every time. The original failure-class recovery
(missing `item/completed` → fallback via `thread/read`) remains unproven
by live evidence. See [Closure](#closure) for the evidence standard
applied.

**Closure criteria:**

- [x] Patch landed on main with unit tests for both extraction shapes
  (tests #1-#3)
- [x] Runtime integration test proving the fallback populates
  `TurnExecutionResult.agent_message` via turn-ID lookup when
  `item/completed` does not fire (test #4 — load-bearing regression)
- [x] Downstream regression test proving `reply()` →
  `parse_consult_response` succeeds on fallback-produced text (test #5)
- [x] Fallback failure tests proving best-effort semantics: read failure,
  no matching turn, and empty extraction all fall through without
  escalating to dispatch failure (tests #6-#8)
- [x] Execution-turn isolation test proving `run_execution_turn()` does not
  trigger the fallback (test #9)
- [x] One-run verification: rerun the B3 adversarial prompt on the patched
  commit in a fresh session, confirm convergence or natural termination
  without parse error
- [x] Record implementation commit SHA (`00ec0054`) and mark `status: closed`

## Closure

**Evidence standard applied: engineering sufficiency with explicit
evidence downgrade.** This ticket is closed based on test-covered
fallback implementation plus App Server version drift and current
non-regression evidence. It is **not** closed based on a live fallback
firing.

What was proven:

- The `thread/read` fallback implementation is test-covered by 12
  targeted tests: 5 extraction-shape tests, 1 load-bearing regression
  test (#4: fallback populates `agent_message` when `item/completed`
  does not fire), 1 downstream parse parity test (#5), 3 failure-mode
  tests (#6-#8), and 1 execution-turn isolation test (#9).
- Live non-regression is established: 5 adversarial turns on Codex
  `0.125.0` completed without error. The patched code does not interfere
  with normal `item/completed` delivery.
- 1082 existing tests pass with the fallback in place.

What was **not** proven:

- The fallback recovery path has never been exercised against the real
  App Server. No live run produced the original failure condition
  (missing `item/completed` notification), so the `thread/read`
  projection shape for that failure class is untested against production
  infrastructure.
- The original failure was observed on Codex `0.117.0`. Verification ran
  on `0.125.0`. Current runtime is `0.128.0`. The `item/completed`
  delivery behavior may have been fixed server-side between versions.
  The failure mode may no longer be reproducible.

Why this standard is accepted:

- The fallback code path is covered by unit and integration tests that
  simulate the exact failure condition (empty `agent_message` on a
  completed advisory turn). The test-to-production gap is limited to
  the `thread/read` response shape, which uses the same
  `extract_agent_message` helper already exercised by the dialogue read
  path in production.
- Waiting for natural live proof requires a server-side regression on
  current App Server versions. There is no monitoring mechanism for this
  and no indication the failure will recur. Holding the ticket open
  indefinitely for evidence that requires external infrastructure failure
  is not operationally useful.
- The fallback's best-effort semantics mean failure is safe: if the
  `thread/read` shape differs from expectations, the fallback returns
  `""` and the original `CommittedTurnParseError` occurs — no worse than
  the unfixed state.

Evidence artifacts:

- Implementation commit: `00ec0054`
- Live verification: `docs/diagnostics/2026-04-30-dialogue-reply-extraction-post-patch.md`
- Diagnostic recommendation at time of verification was "Do not close
  based solely on this evidence" — this closure overrides that
  recommendation by explicitly accepting the reduced standard described
  above.

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
| B3 candidate metadata | `docs/benchmarks/dialogue-supersession/v1/runs.json` (B3-candidate entry) |
| B3 candidate synthesis | `docs/benchmarks/dialogue-supersession/v1/transcripts/B3-candidate-synthesis.md` |
| B3 candidate transcript | `docs/benchmarks/dialogue-supersession/v1/transcripts/B3-candidate-transcript.md` |
| Codex session rollout (B3 candidate) | `/Users/jp/.codex/sessions/2026/04/16/rollout-2026-04-16T14-45-39-019d979c-*.jsonl` |
| Parent ticket (supersession benchmark) | `docs/tickets/closed-tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md` |
