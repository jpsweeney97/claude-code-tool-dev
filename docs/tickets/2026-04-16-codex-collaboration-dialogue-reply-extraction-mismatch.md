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

Extraction mismatch between `codex.dialogue.reply` and `codex.dialogue.read`:

| Path | Location | Extraction logic | Handles items-array shape? |
|---|---|---|---|
| `reply()` parse step | `packages/plugins/codex-collaboration/server/dialogue.py:498-502` | `parse_consult_response(turn_result.agent_message)` — direct field read | **No** |
| `read()` extraction | `packages/plugins/codex-collaboration/server/dialogue.py:973-990` (`_read_turn_agent_message`) | Tries `raw_turn["agentMessage"]`; falls back to `raw_turn["items"][type="agentMessage"].text` | **Yes** |

The Codex runtime can deliver an agent message in two shapes:

1. Top-level `agentMessage` field (short or simple replies)
2. `items` array with `{type: "agentMessage", text: "..."}` entries (streamed or complex replies)

`_read_turn_agent_message` handles both. `reply()` relies on `turn_result.agent_message` having already been populated by the dispatch layer, but that population only covers shape (1). When shape (2) is delivered, `turn_result.agent_message` arrives as empty string, and `parse_consult_response("")` raises `json.JSONDecodeError` from `prompt_builder.py:58-63`, which `reply()` wraps as `CommittedTurnParseError` at `dialogue.py:504-509`.

The underlying extractor for shape (2) already exists, is already tested in the read-path, and is already factored as a static method on the controller. The bug is that the reply-path doesn't use it.

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

**Fix boundary:** wire the existing `_read_turn_agent_message` extractor into the `reply()` parse step. Do **not** broaden runtime-layer semantics.

Preferred boundary because:

- The robust extraction is already written and tested in the read-path — it's static, dependency-free, and designed to handle both response shapes
- Broadening the dispatch/runtime layer to canonicalize `turn_result.agent_message` would touch a wider surface and risks affecting other consumers (`consult`, `start`, future tool calls)
- The bug is local to the controller's parse projection; the fix should be local too

**Correction to the initial draft:** an earlier version of this ticket proposed "obtain the raw_turn dict from the dispatch layer" in `reply()`. That framing is wrong. `TurnExecutionResult` (defined at `packages/plugins/codex-collaboration/server/models.py:106-111`) carries only three fields: `turn_id`, `agent_message`, `notifications`. The raw turn dict is not exposed at the `reply()` site. Implementing the fix requires either enriching the runtime projection, canonicalizing at dispatch, or doing a post-commit journal read — each with different trade-offs.

**Fix options (ordered by scope increase):**

*Option A — Canonicalize `agent_message` at dispatch.* The bug's true site is `runtime.py:173-177`, where `agent_message` is populated from the Codex `turn/start` response. If that extraction is given the same items-array fallback that `_read_turn_agent_message` implements, all downstream consumers (`reply`, `consult`, any future tool using `TurnExecutionResult`) are fixed. Implementation: move `_read_turn_agent_message` from the controller (`dialogue.py:973-990`) to a shared helper (e.g., `codex_compat.py` or a new `turn_extraction.py`), call it from runtime's `agent_message` extraction path. Scope: runtime + helper module + tests; `dialogue.reply()` unchanged.

*Option B — Enrich `TurnExecutionResult`.* Add a narrow projection field to `TurnExecutionResult` (e.g., `items: tuple[dict[str, Any], ...] = ()`) populated at dispatch. In `reply()`, fall back to `self._read_turn_agent_message({"items": turn_result.items})` if `turn_result.agent_message` is empty. Scope: models + runtime + controller + tests. Adds items-array visibility to TurnExecutionResult consumers.

*Option C — Post-commit journal read in `reply()`.* Since the turn is committed to durable state before the parse step (`dialogue.py:498-499`), `reply()` could retrieve the committed turn via the turn store and extract the agent message via `_read_turn_agent_message`. Scope: controller-only, but couples `reply()` to persistence-layer retrieval and adds a storage round-trip on every reply.

**Recommended:** Option A. Fixes the root cause at its source. Narrowest long-term surface because `TurnExecutionResult` stays unchanged, and consult-path robustness improves for free. The static extractor's existing unit tests transfer with the move.

**Estimated effort (Option A):** 1 helper module (or addition to `codex_compat.py`) + ~3-5 lines in `runtime.py` + updates to existing `_read_turn_agent_message` tests + 1 new test for the runtime integration path. Roughly ~15-25 production lines + ~30-50 test lines. `effort: medium` in the frontmatter reflects this.

**Implementation tests required:**

1. Unit test for the shared extractor: items-array shape with well-formed text
2. Unit test: top-level `agentMessage` shape (regression)
3. Unit test: absent `agentMessage` AND absent `items[type=agentMessage]` — extractor returns `""`
4. Integration test: runtime's `agent_message` extraction path handles items-array shape end-to-end (mock `turn/start` response)
5. Integration test: `dialogue.reply()` against a mock runtime that returns items-array-shaped turns — successful parse + `DialogueReplyResult` construction

**Out of scope for this patch:**

- Retry logic for genuinely empty Codex completions (separate concern — extraction mismatch ≠ empty-response handling)
- Migrating `consult`'s parse path separately (Option A fixes it incidentally; no separate work)
- In-dialogue recovery via `codex.dialogue.read` fallback after parse failure
- Refactoring the commit-before-parse design at `dialogue.py:498-499` (the design is sound; the bug is upstream)

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

- Patch landed on main with unit test for items-array shape
- Regression test for top-level `agentMessage` shape
- One-run verification: rerun the B3 adversarial prompt on the patched
  commit in a fresh session, confirm convergence or natural termination
  without parse error
- Update this ticket with final commit SHA and mark `status: closed`

## References

| Reference | Location |
|---|---|
| Direct parse path (bug site) | `packages/plugins/codex-collaboration/server/dialogue.py:498-509` |
| Robust extractor (fix reuses) | `packages/plugins/codex-collaboration/server/dialogue.py:973-990` |
| Parse error source | `packages/plugins/codex-collaboration/server/prompt_builder.py:58-63` |
| MCP tool dispatch | `packages/plugins/codex-collaboration/server/mcp_server.py:263-272` |
| Benchmark contract — invalidation triggers | `docs/benchmarks/dialogue-supersession/v1/operator-procedure.md:660-666` |
| Benchmark contract — run_commit rule | `docs/benchmarks/dialogue-supersession/v1/operator-procedure.md:66` |
| Benchmark contract — diagnostic metrics | `docs/benchmarks/dialogue-supersession/v1/operator-procedure.md:519` |
| B3 candidate metadata | `/private/tmp/benchmark-v1-staging-20260415/B3-candidate-metadata.json` |
| B3 candidate synthesis | `/private/tmp/benchmark-v1-staging-20260415/B3-candidate-synthesis.md` |
| B3 candidate transcript | `/private/tmp/benchmark-v1-staging-20260415/B3-candidate-transcript.md` |
| Codex session rollout (B3 candidate) | `/Users/jp/.codex/sessions/2026/04/16/rollout-2026-04-16T14-45-39-019d979c-*.jsonl` |
| Parent ticket (supersession benchmark) | `docs/tickets/closed-tickets/2026-03-30-codex-collaboration-dialogue-parity-and-scouting-retirement.md` |
