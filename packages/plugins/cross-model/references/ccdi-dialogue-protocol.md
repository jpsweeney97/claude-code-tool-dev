# CCDI Mid-Dialogue Protocol

Governs CCDI (Claude Code Documentation Integration) behavior within the `codex-dialogue` agent. Read this document only when `ccdi_seed` is present in the delegation envelope.

## CCDI State Variables

Add these to conversation state alongside the core variables:

| State | Initial value | Purpose |
|-------|--------------|---------|
| `ccdi_mode` | `"unavailable"` | One of `"active"`, `"shadow"`, or `"unavailable"`. Set by the shadow mode gate at dialogue start. |
| `ccdi_seed_path` | `null` | File path from `ccdi_seed` delegation field. Registry file — mutated in-place. |
| `ccdi_snapshot_path` | `null` | File path from `ccdi_inventory_snapshot` delegation field. Pinned inventory snapshot. |
| `ccdi_debug` | `false` | From delegation envelope. Controls ccdi_trace emission. |
| `ccdi_trace` | `[]` | Accumulated trace entries (emitted only when `ccdi_debug` is true). |
| `ccdi_diagnostics_emitter` | `null` | DiagnosticsEmitter instance. Initialized after shadow mode gate. |

## Shadow Mode Gate

At dialogue start, after initializing conversation state and before the per-turn loop, determine whether CCDI mid-dialogue injection is available and in which mode:

1. **Check `ccdi_seed` in delegation envelope.** If absent, set `ccdi_mode = "unavailable"`. Skip steps 2-4 below. Mid-dialogue CCDI is disabled for this conversation.
2. **Check `ccdi_inventory_snapshot` in delegation envelope.** If absent while `ccdi_seed` is present, log warning: `"ccdi_inventory_snapshot absent with ccdi_seed present — disabling mid-dialogue CCDI"`. Set `ccdi_mode = "unavailable"`. Skip steps 3-4.
3. **Validate `ccdi_seed` is a file path, not inline JSON.** If the value starts with `{` (after stripping whitespace), treat as absent: log warning `"ccdi_seed appears to be inline JSON, not a file path — disabling mid-dialogue CCDI"`. Set `ccdi_mode = "unavailable"`. Skip step 4.
4. **Read `data/ccdi_shadow/graduation.json`** (relative to the cross-model plugin root).
   - If the file is absent: set `ccdi_mode = "shadow"`.
   - If the file contains `"status": "approved"`: set `ccdi_mode = "active"`.
   - If `status` is any other value (including `"rejected"`, malformed, or unreadable): set `ccdi_mode = "shadow"`.

Store `ccdi_seed` as `ccdi_seed_path`, `ccdi_inventory_snapshot` as `ccdi_snapshot_path`, and `ccdi_debug` (default `false`) in conversation state.

**Phase A carve-out:** This gate governs Phase B mid-dialogue mutations only. Phase A initial injection (pre-delegation, in `/dialogue`) is unconditional — initial CCDI commits fire regardless of `graduation.json` status.

**Initialize diagnostics emitter** after the gate resolves:
- If `ccdi_mode` is `"active"`: create `DiagnosticsEmitter(status="active", phase="full", ...)`.
- If `ccdi_mode` is `"shadow"`: create `DiagnosticsEmitter(status="shadow", phase="full", ...)`.
- If `ccdi_mode` is `"unavailable"`: set `ccdi_diagnostics_emitter = null`. Diagnostics will use `DiagnosticsEmitter.unavailable()` at emission time.

## Step 6.5: CCDI PREPARE (mid-dialogue injection)

**Skip this step** if `ccdi_mode` is `"unavailable"`.

After composing the follow-up (Step 6) and before sending (Step 7), run the CCDI prepare cycle:

**6.5a. Write Codex's response to a temp file:**

Write the Codex response text (from Step 1 extraction) to `/tmp/ccdi_turn_<id>.txt`. Use the `threadId` as `<id>`.

**6.5b. Optionally extract semantic hints:**

If the Codex response contains topic-relevant terminology, key phrases, or named entities that would improve topic classification, write them as a JSON array to `/tmp/ccdi_hints_<id>.json`. Each hint is a string. If no hints are extractable, skip this step (do not create the file).

**6.5c. Run `dialogue-turn`:**

```bash
uv run python -m scripts.topic_inventory dialogue-turn \
  --registry-file <ccdi_seed_path> \
  --text-file /tmp/ccdi_turn_<id>.txt \
  --source codex \
  --inventory-snapshot <ccdi_snapshot_path> \
  --turn <current_turn> \
  [--semantic-hints-file /tmp/ccdi_hints_<id>.json] \
  [--shadow-mode]
```

Pass `--shadow-mode` when `ccdi_mode` is `"shadow"`. Omit when `"active"`.

Read the JSON candidates from stdout. Record timing for diagnostics: `ccdi_diagnostics_emitter.record_turn(latency_ms=<elapsed>)`.

**6.5d. Process candidates:**

IF no candidates returned: no CCDI this turn. Record trace entry with `action: "none"`. Continue to Step 7.

IF candidates returned AND a scout target exists for this turn (Step 4 produced an `execute_scout` candidate):

For each candidate, defer with `scout_priority` reason:

```bash
uv run python -m scripts.topic_inventory build-packet \
  --results-file /dev/null \
  --registry-file <ccdi_seed_path> \
  --inventory-snapshot <ccdi_snapshot_path> \
  --mode mid_turn \
  --topic-key <candidate.topic_key> \
  --facet <candidate.facet> \
  --mark-deferred scout_priority \
  --skip-build \
  [--shadow-mode]
```

Pass `--shadow-mode` when `ccdi_mode` is `"shadow"`. Record `ccdi_diagnostics_emitter.record_packet_deferred_scout()` and `record_topic_deferred(candidate.topic_key)` for each candidate.

IF candidates returned AND no scout target:

For each candidate (in scheduling priority order):

1. **Search:** Use `mcp__claude-code-docs__search_docs` (or equivalent) with the candidate's query plan to find relevant content. Write results to `/tmp/ccdi_results_<id>.json`.

2. **Build packet (prepare only — no commit):**

```bash
uv run python -m scripts.topic_inventory build-packet \
  --results-file /tmp/ccdi_results_<id>.json \
  --registry-file <ccdi_seed_path> \
  --inventory-snapshot <ccdi_snapshot_path> \
  --mode mid_turn \
  --topic-key <candidate.topic_key> \
  --facet <candidate.facet> \
  --coverage-target <candidate.coverage_target>
```

Do NOT pass `--mark-injected` at this stage.

3. **Empty packet check:** If `build-packet` returned empty output, the topic was auto-suppressed (weak results). Record `ccdi_diagnostics_emitter.record_topic_suppressed(candidate.topic_key)`. Skip target-match for this candidate.

4. **Target-match check:** Verify the staged packet supports the composed follow-up target.
   - **(a)** Check if any of the packet's topics appear as a substring (case-insensitive) in the composed follow-up text.
   - **(b)** If (a) fails, run `classify` on the composed follow-up text and check for topic overlap:
     ```bash
     uv run python -m scripts.topic_inventory classify \
       --text-file /tmp/ccdi_followup_<id>.txt \
       --inventory <ccdi_snapshot_path>
     ```
   - If target-relevant (either check passes) AND `ccdi_mode` is `"active"`: stage the packet for prepending to the follow-up. Record `ccdi_diagnostics_emitter.record_packet_prepared()` and `record_topic_detected(candidate.topic_key)`.
   - If target-relevant AND `ccdi_mode` is `"shadow"`: record the packet in diagnostics (`record_packet_prepared()`, `record_topic_detected(candidate.topic_key)`) but do NOT stage for prepending.
   - If NOT target-relevant: defer with `target_mismatch`:
     ```bash
     uv run python -m scripts.topic_inventory build-packet \
       --results-file /tmp/ccdi_results_<id>.json \
       --registry-file <ccdi_seed_path> \
       --inventory-snapshot <ccdi_snapshot_path> \
       --mode mid_turn \
       --topic-key <candidate.topic_key> \
       --facet <candidate.facet> \
       --mark-deferred target_mismatch \
       --skip-build \
       [--shadow-mode]
     ```
     Pass `--shadow-mode` when `ccdi_mode` is `"shadow"`. Record `ccdi_diagnostics_emitter.record_topic_deferred(candidate.topic_key)`.

**6.5e. Record trace entry** (when `ccdi_debug` is `true`):

Append a trace entry to `ccdi_trace` with all 9 required keys:

```json
{
  "turn": <current_turn>,
  "action": "<classify|schedule|search|build_packet|prepare|inject|defer|suppress|skip_cooldown|skip_scout|shadow_defer_intent|replay_turn|none>",
  "topics_detected": ["<topic_key>", ...],
  "candidates": ["<topic_key>", ...],
  "packet_staged": <true|false>,
  "scout_conflict": <true|false>,
  "commit": false,
  "shadow_suppressed": <true|false>,
  "semantic_hints": ["<hint>", ...] or []
}
```

- `action`: the primary action taken this turn (use the most specific applicable value)
- `topics_detected`: topic keys from the classifier result within `dialogue-turn`
- `candidates`: topic keys from the scheduling result
- `packet_staged`: whether a packet was prepared for injection
- `scout_conflict`: whether a scout target prevented CCDI processing
- `commit`: always `false` at PREPARE time — updated to `true` in Step 7.5 if committed
- `shadow_suppressed`: `true` when `ccdi_mode` is `"shadow"` and a packet was staged but not delivered

When `ccdi_mode` is `"shadow"` and a packet was staged, also append a `shadow_defer_intent` trace entry to record the counterfactual deferral.

**Multi-candidate turns:** When `dialogue-turn` emits multiple candidates, process in scheduling priority order. The per-turn cooldown applies only to `candidate_type: "new"` entries. `pending_facet` and `facet_expansion` candidates are exempt and may be processed in the same turn.

## Step 7 CCDI Integration

Before sending the follow-up via `codex-reply`:

- IF `ccdi_mode` is `"active"` AND a CCDI packet was staged in Step 6.5: prepend the packet to the follow-up text.
- IF `ccdi_mode` is `"shadow"`: send the follow-up WITHOUT the packet. Diagnostics record what would have been injected.

## Step 7.5: CCDI COMMIT (after send confirmed)

**Skip this step** if `ccdi_mode` is `"unavailable"`.

After Step 7 send is confirmed successful:

IF `ccdi_mode` is `"active"` AND a packet was sent (staged in Step 6.5 and prepended in Step 7):

For each candidate that was staged and sent, commit the injection:

```bash
uv run python -m scripts.topic_inventory build-packet \
  --results-file /tmp/ccdi_results_<id>.json \
  --registry-file <ccdi_seed_path> \
  --inventory-snapshot <ccdi_snapshot_path> \
  --mode mid_turn \
  --topic-key <candidate.topic_key> \
  --facet <candidate.facet> \
  --coverage-target <candidate.coverage_target> \
  --mark-injected
```

Record `ccdi_diagnostics_emitter.record_packet_injected(tokens=<packet_tokens>)` and `record_topic_injected(candidate.topic_key)`.

Update the trace entry for this turn: set `commit` to `true`.

IF `ccdi_mode` is `"shadow"`: no commit. The packet was staged but not delivered. Registry remains unchanged (except for auto-suppressions from empty build-packet output).

IF the send failed (Step 7 error): no commit. Do NOT call `--mark-injected`. The packet was staged but not delivered.

**Key invariant:** `--mark-injected` is called only after the packet-containing prompt has been confirmed sent to Codex. This prevents the registry from recording injection for packets that were staged but never delivered.

## Phase 3: CCDI Trace Emission

**Skip this section** if `ccdi_debug` is `false` or absent.

When `ccdi_debug` is `true` in the delegation envelope, include the accumulated `ccdi_trace` in the output. The trace is a JSON array of per-turn entries, each with all 9 required keys:

| Key | Type | Description |
|-----|------|-------------|
| `turn` | int | Turn number |
| `action` | string | Primary action: `classify`, `schedule`, `search`, `build_packet`, `prepare`, `inject`, `defer`, `suppress`, `skip_cooldown`, `skip_scout`, `shadow_defer_intent`, `replay_turn`, `none` |
| `topics_detected` | list[string] | Topic keys from the classifier result |
| `candidates` | list[string] | Topic keys from scheduling |
| `packet_staged` | bool | Whether a packet was prepared |
| `scout_conflict` | bool | Whether a scout target conflicted with CCDI |
| `commit` | bool | Whether injection was committed (true only after Step 7.5 success) |
| `shadow_suppressed` | bool | Whether this was a shadow-mode turn where a packet was staged but not delivered |
| `semantic_hints` | list[string] or [] | Hints processed this turn, or empty |

Every entry in `ccdi_trace` MUST have all 9 keys. Emit the trace in a fenced JSON block after the synthesis checkpoint:

```json
<!-- ccdi-trace -->
[
  {"turn": 1, "action": "prepare", "topics_detected": [...], "candidates": [...], "packet_staged": true, "scout_conflict": false, "commit": true, "shadow_suppressed": false, "semantic_hints": []},
  ...
]
```

The `<!-- ccdi-trace -->` sentinel marks this block for machine parsing.

## Phase 3: CCDI Diagnostics Emission

At dialogue end, emit CCDI diagnostics in the Pipeline Data JSON epilogue. The format depends on `ccdi_mode`:

**Active mode** (`ccdi_mode` = `"active"`):

Call `ccdi_diagnostics_emitter.emit()` and include the result as the `ccdi` field in the pipeline data JSON. Active mode includes standard fields only (no shadow-only fields):

- `status`, `phase`, `topics_detected`, `topics_injected`, `topics_deferred`, `topics_suppressed`
- `packets_prepared`, `packets_injected`, `packets_deferred_scout`, `total_tokens_injected`
- `semantic_hints_received`, `search_failures`, `inventory_epoch`, `config_source`, `per_turn_latency_ms`

**Shadow mode** (`ccdi_mode` = `"shadow"`):

Call `ccdi_diagnostics_emitter.emit()` and include the result. Shadow mode includes all active fields PLUS shadow-only fields:

- `packets_target_relevant` — packets that passed the target-match check
- `packets_surviving_precedence` — packets not deferred by scout priority or cooldown
- `false_positive_topic_detections` — topics detected but never producing a viable packet
- `shadow_adjusted_yield` — yield metric accounting for shadow-mode suppression

**Unavailable** (`ccdi_mode` = `"unavailable"`):

Emit minimal diagnostics:

```json
"ccdi": {
  "status": "unavailable",
  "phase": "initial_only"
}
```

No count or array fields are present when status is `"unavailable"`.
