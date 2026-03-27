# Cross-Model Codex App Server Architecture

## 1. Decision

Which architecture should replace the cross-model plugin's current `codex exec` subprocess transport with the Codex App Server JSON-RPC protocol?

Decision type: architectural choice

## 2. Stakes

High.

This change affects every Codex-facing flow in the plugin: `/codex`, `/dialogue`, `codex-reviewer`, and eventually `/delegate`. It is partially reversible, but the wrong shape would either strand the plugin on an event stream it cannot exploit or force a second rewrite shortly after the first. Local evidence also shows a wide verification blast radius: `uv run pytest --collect-only -q` in `packages/plugins/cross-model` currently collects 841 tests.

## 3. Options

### Option A: Stateless App Server bridge per tool call

Spawn `codex app-server` for each consultation or reply, initialize it, run one `thread/start` or `thread/resume` plus one `turn/start`, wait for `turn/completed`, then tear the process down.

### Option B: Raw App Server passthrough MCP server

Expose App Server JSON-RPC primitives almost 1:1 as MCP tools and let skills and agents orchestrate `thread/start`, `turn/start`, `turn/steer`, `thread/fork`, `review/start`, and related methods directly.

### Option C: Stateful advisory App Server broker with isolated delegation runtime

Run one long-lived local `codex app-server` stdio child for advisory flows (`/codex`, `/dialogue`, review), plus a separate isolated App Server runtime for delegation sessions. Build an internal JSON-RPC client, event multiplexer, thread registry, and turn accumulator for the advisory broker. Expose a small, plugin-specific MCP surface for consultation, dialogue, review, steering, and branching while keeping safety, scope, analytics, context injection, and delegation gates in plugin-owned code.

### Option D: Null option, keep `codex exec`

Retain the current subprocess + JSONL parsing design.

## 4. Information gaps

| Gap | Most affects | Can it be resolved before commitment? | Notes |
|-----|--------------|----------------------------------------|-------|
| How stable the installed `codex app-server` surface is across local Codex versions | A, B, C | Yes | Resolve with a short compatibility spike plus startup/version gates. |
| Whether Claude Code's MCP hosting model can surface App Server approval requests interactively enough for delegation UX | C | Partially | Consultation and dialogue can avoid this with restrictive policies; delegation needs explicit design. |
| Whether live tool-stream rendering is available to Claude-facing UX today | A, B, C | Yes | Does not block the architecture, but affects the first rollout shape. |

The architecture decision still has to be made under some uncertainty. The largest unresolved issue is approval handling for autonomous editing flows, not whether App Server is a better substrate than `codex exec`.

## 5. Evaluation

### Criteria

| Criterion | Weight | Definition |
|-----------|--------|------------|
| Capability unlock | 5 | Actually unlocks streaming, steering, forking, review, and structured turn handling rather than merely swapping transports |
| Control-plane fit | 5 | Preserves plugin-owned safety, scope, analytics, and context-injection semantics cleanly |
| Operability | 4 | Fits a local Claude Code plugin process without unnecessary auth, networking, or lifecycle complexity |
| Testability | 4 | Can be exercised with deterministic protocol fixtures instead of brittle stdout scraping |
| Migration risk | 3 | Limits the probability of a near-term second rewrite |

### Option A: Stateless App Server bridge per tool call

Strengths:
- Lowest conceptual change from the current adapter.
- Easy to fit behind the current request/response MCP contract.
- Avoids keeping long-lived in-memory state in the plugin process.

Weaknesses:
- Throws away App Server's main advantages: event streaming, mid-turn steering, thread residency, review delivery modes, and thread lifecycle management.
- Adds JSON-RPC complexity without eliminating batch-mode behavior.
- Recreates startup/teardown cost on every interaction.
- Makes approval/event handling awkward because the process dies immediately after each turn.

Best choice when:
- The host can only tolerate short-lived subprocesses and cannot maintain a long-lived event stream at all.

### Option B: Raw App Server passthrough MCP server

Strengths:
- Maximum feature exposure with minimal abstraction.
- Keeps the bridge implementation thin.
- Makes it easy to add newly documented App Server methods later.

Weaknesses:
- Pushes low-level protocol decisions into prompts, skills, and agents.
- Spreads lifecycle correctness across markdown instructions instead of executable code.
- Makes safety and analytics harder because every tool path has to remember the same preflight rules.
- Exposes too much surface area to Claude, which is likely to increase orchestration drift rather than reduce it.

Best choice when:
- The primary goal is a general-purpose App Server client library, not a focused Claude Code plugin with strong local contracts.

### Option C: Stateful App Server broker with an opinionated plugin control plane

Strengths:
- Matches the App Server lifecycle directly: initialize once, keep a live connection, create/resume/fork threads, start turns, steer active turns, and consume structured item events.
- Keeps plugin-specific rules where they belong: credential scanning, scope envelope checks, analytics emission, consultation profiles, and context injection remain local concerns.
- Preserves the plugin's trust split by keeping delegation in a separate runtime/approval domain instead of sharing session-scoped grants with advisory flows.
- Replaces string scraping with typed turn/item accumulation.
- Supports purpose-built review via `review/start` instead of prompting a generic review turn.
- Makes thread forking a first-class design tool for comparative or adversarial branches.
- Keeps the Claude-facing tool surface compact and semantically meaningful.
- Creates a clean testing seam: replay JSON-RPC transcripts, assert state machines, and pin generated App Server schemas as fixtures.

Weaknesses:
- More implementation work up front than A.
- Requires an internal event loop, request router, and per-thread/per-turn state management.
- Requires two runtime shapes to supervise correctly: a long-lived advisory broker and an isolated delegation runner.
- Fork semantics and recovery semantics must be specified explicitly because the current dialogue/control-plane state is keyed directly to a single `threadId`.

Best choice when:
- The goal is to redesign the plugin around App Server capabilities rather than just replace a subprocess.

### Option D: Null option, keep `codex exec`

Strengths:
- Zero migration cost.
- Existing tests already encode the current contract.

Weaknesses:
- Keeps the plugin in batch mode.
- Forces continued dependence on JSONL parsing and opaque continuation handling.
- Leaves streaming, steering, thread forking, structured turn state, and built-in review unused.
- Makes the transport the limiting factor for future dialogue quality.

Best choice when:
- App Server proves operationally unusable in the plugin environment.

### Scorecard

| Option | Capability unlock | Control-plane fit | Operability | Testability | Migration risk | Total |
|--------|-------------------|------------------|-------------|-------------|----------------|-------|
| C | 5 | 5 | 4 | 5 | 4 | 92 |
| B | 4 | 2 | 3 | 3 | 2 | 61 |
| A | 2 | 3 | 4 | 3 | 3 | 57 |
| D | 1 | 2 | 5 | 2 | 5 | 45 |

### Evidence that drives the ranking

- The current consultation transport is explicitly a subprocess wrapper around `codex exec`, with JSONL parsing, timeout recovery, and a four-state dispatch model, not a live conversation runtime: [`scripts/codex_consult.py`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/scripts/codex_consult.py#L1).
- The current MCP server is intentionally a thin shim over that adapter and owns neither safety nor continuity logic: [`scripts/codex_shim.py`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/scripts/codex_shim.py#L1).
- The plugin's own README still describes the Codex side as a shim translating MCP tool calls to `codex exec` CLI invocations: [`README.md`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/README.md#L147).
- The dialogue agent is already architected around durable conversation state, explicit thread identity, and multi-turn orchestration, which means the current transport is below the abstraction level the agent actually wants: [`agents/codex-dialogue.md`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/agents/codex-dialogue.md#L107).
- OpenAI's App Server protocol is thread/turn/item based, supports `thread/start`, `thread/resume`, `thread/fork`, `turn/start`, `turn/steer`, `turn/interrupt`, `review/start`, and a structured event stream. That is materially closer to the plugin's desired control plane than `codex exec` batch JSONL output. Sources:
  - [Codex App Server protocol](https://developers.openai.com/codex/app-server/#protocol)
  - [Codex App Server lifecycle overview](https://developers.openai.com/codex/app-server/#lifecycle-overview)
  - [Codex App Server threads](https://developers.openai.com/codex/app-server/#threads)
  - [Codex App Server turns](https://developers.openai.com/codex/app-server/#turns)
  - [Codex App Server review](https://developers.openai.com/codex/app-server/#review)
  - [Codex App Server events](https://developers.openai.com/codex/app-server/#events)
  - [Codex App Server approvals](https://developers.openai.com/codex/app-server/#approvals)
- The open-source App Server README confirms the same lifecycle and shows that stdio is the default transport, while websocket carries more rollout and auth complexity than the plugin needs: [openai/codex `codex-rs/app-server/README.md`](https://github.com/openai/codex/blob/main/codex-rs/app-server/README.md).

## 6. Sensitivity analysis

Option C stops being the best choice under only a few realistic flips:

- If the plugin host cannot safely maintain one long-lived child process with a background read loop, Option A becomes the fallback because App Server would still be usable only as a blocking RPC engine.
- If the plugin's real goal changes from "high-quality Claude-facing consultation" to "expose raw App Server to arbitrary clients," Option B becomes better.
- If the plugin cannot reliably supervise both a long-lived advisory broker and isolated delegation runners, the recommendation should narrow to advisory-only migration first and leave delegation on a separate transport until the isolation model is proven.

No realistic change makes Option D preferable unless App Server itself is not operationally viable in the environment.

## 7. Ranked options

1. **Option C: Stateful App Server broker with an opinionated plugin control plane** - Best balance of capability unlock, local-contract fit, and long-term maintainability.
2. **Option B: Raw App Server passthrough MCP server** - Exposes power quickly, but at the cost of pushing protocol complexity into prompts and agents.
3. **Option A: Stateless App Server bridge per tool call** - Safer than raw passthrough, but mostly preserves the current batch ceiling.
4. **Option D: Keep `codex exec`** - Lowest effort and lowest leverage.

## 8. Recommendation

Adopt **Option C**.

The key disagreement with the narrow "replace the transport" framing is this: a transport-only swap is not enough. If the plugin keeps a batch-shaped adapter and only changes the child process from `codex exec` to `codex app-server`, it will incur most of the migration cost while preserving most of the current limitations. The right move is to rebuild the advisory side of the plugin around App Server's native concepts: connection, thread, turn, item, event, and review.

The key correction from the adversarial review is this: **do not put delegation into the same long-lived App Server runtime as advisory flows**. Session-scoped approvals and write grants make runtime boundaries part of the trust boundary. Delegation isolation therefore has to be a first-class architecture decision, not a rollout detail.

### Recommended target architecture

#### 8.1 Process model

- Run **one long-lived `codex app-server` child process over stdio** for advisory flows: `/codex`, `/dialogue`, and review.
- Run **a separate isolated App Server runtime per delegation session**. Never share delegation threads, approvals, writable roots, or session-scoped grants with the advisory broker.
- Do **not** use websocket for the plugin integration. Local stdio avoids extra auth surface and avoids taking on websocket rollout risk that the plugin does not need.
- Initialize the advisory broker once and keep it alive for the life of the MCP server process. Treat delegation runners as short-lived isolated execution domains.

#### 8.2 Internal layers

1. **`AppServerSupervisor`**
   - Spawns the advisory `codex app-server`
   - Performs `initialize` / `initialized`
   - Checks `codex --version`
   - Restarts the child on crash and exposes a fail-fast health state

2. **`JsonRpcClient`**
   - Owns request IDs, pending futures, and the background read loop
   - Routes responses, notifications, and server-initiated requests
   - Serializes writes to stdio

3. **`ThreadRuntime`**
   - Tracks loaded threads, active turns, thread settings, and idle cleanup
   - Uses `thread/start`, `thread/resume`, `thread/fork`, `thread/read`, and `thread/unsubscribe`
   - Treats `{threadId, turnId}` as the canonical continuity model

4. **`TurnAccumulator`**
   - Consumes `turn/*`, `item/*`, `turn/plan/updated`, and `turn/diff/updated`
   - Builds authoritative final state from `item/completed` and `turn/completed`
   - Accumulates agent text, plans, diffs, command output, file changes, errors, and review markers

5. **`CodexControlPlane`**
   - Runs credential scan, redaction, scope-envelope checks, policy resolution, and analytics emission before or after App Server calls
   - Owns consultation profiles and any plugin-specific response shaping

6. **Domain services**
   - `ConsultationService`
   - `DialogueService`
   - `ReviewService`

7. **`DelegationRunner`**
   - Spawns an isolated App Server runtime for one delegation session
   - Applies delegation-only gates before spawn
   - Owns writable sandbox and approval domain for that session only
   - Tears the runtime down after completion or explicit recovery handoff

#### 8.3 Claude-facing tool surface

Do **not** expose raw JSON-RPC as the main MCP surface. Expose a compact, plugin-shaped tool API instead.

Recommended first-class operations:

- `consult` - blocking single-turn consult on a new or existing thread
- `dialogue_turn_start` - start a turn on an existing dialogue thread
- `dialogue_turn_steer` - steer the active turn with additional input
- `dialogue_thread_fork` - branch a thread intentionally
- `review_start` - invoke `review/start`, inline or detached
- `thread_read` - fetch persisted thread state for recovery or synthesis

Slash commands and agents should use these domain tools, not raw `thread/start` or `turn/start` calls.

#### 8.4 Fork semantics

- `thread/fork` is **advisory-only** in the first migration slice. Do not enable implicit mid-loop forking inside `/dialogue` until lineage and synthesis behavior are proven.
- A fork creates a **new** App Server `threadId` and a **new** plugin `conversation_id`. It must not reuse the parent dialogue's context-injection identity.
- No checkpoint state carries forward across a fork: `checkpoint_id = null`, `state_checkpoint = null`, scout tokens invalidated, and `turn_history = []` in the forked branch.
- The fork may inherit an immutable copy of the parent's `scope_envelope` only if the inherited scope remains within the original consent envelope. It must never widen scope by default.
- Persist fork lineage metadata in plugin-owned state and analytics: at minimum `parent_thread_id`, `fork_origin_turn_id`, and `fork_reason`.
- Forked branches synthesize independently. The plugin must not auto-merge forked `turn_history` back into the parent dialogue.

#### 8.5 Recovery semantics

- If the advisory broker crashes with **no active turn**, restart it, re-run `initialize`, and recover threads lazily via `thread/read` or `thread/resume`.
- If the advisory broker crashes during an active **consult** or **review** turn, mark the turn `transport_lost`, attempt `thread/read`, and:
  - relay the result if the turn completed and persisted upstream
  - otherwise return a recoverable interruption that requires explicit retry or resume
- If the advisory broker crashes during an active **dialogue** turn after at least one successful `process_turn`, do not attempt to reconstruct the missing partial turn. Resume only with explicit user action; otherwise synthesize from the existing validated `turn_history` if safe to do so.
- In-flight approval or user-input requests are invalidated on broker crash and must never be auto-replayed.
- Plugin restart is **not** transparent recovery for in-flight turns. Only persisted thread state is recoverable across host restarts.

#### 8.6 What to delete

- `codex_consult.py` as the transport core
- `codex_shim.py` as a two-method compatibility shell
- Opaque `continuation_id` as the plugin's continuity abstraction
- JSONL response scraping as the main source of turn state

#### 8.7 What to keep

- The credential scanner and redaction logic, but move it into the bridge as an executable preflight gate
- Hook-level `PreToolUse` / `PostToolUse` enforcement as the **authoritative outer boundary** for Codex-facing MCP entry points
- Bridge-level scanning and validation as a second line of defense, not a replacement for hooks
- Context injection as a separate plugin-owned subsystem
- Analytics ownership in the plugin
- Consultation profiles and dialogue orchestration concepts
- `/delegate` clean-tree and secret-file gates as mandatory plugin-owned gates regardless of the transport swap

### Flow-specific guidance

#### Direct consult (`/codex`)

- Use `thread/start` + `turn/start`
- Set `outputSchema` for deterministic structured consult outputs where useful
- Default to restrictive read-only settings
- Return the final agent answer plus `threadId`

#### Dialogue (`/dialogue`)

- Keep the existing plugin-owned dialogue logic, but back it with persistent App Server threads
- Use `turn/steer` for mid-turn corrections or newly surfaced evidence when available
- Treat `thread/fork` as an explicit branch operation with fresh `conversation_id`, empty checkpoints, and independent synthesis
- Use `thread/read` for crash recovery and synthesis reconstruction

#### Review

- Replace prompt-based reviewer emulation with `review/start`
- Use `delivery: "detached"` when review should not contaminate the main consultation thread
- Fold `codex-reviewer` into a thin orchestration layer over App Server review mode

#### Delegate

- Delegation must run in an **isolated App Server runtime per session**, not in the long-lived advisory broker.
- Keep the current plugin-owned clean-tree and secret-file gates before spawning the delegation runtime.
- Session-scoped approvals and writable grants from delegation must never be reusable by advisory flows.
- The **first rollout** should still land consult, dialogue, and review first.
- Delegation should follow once approval auto-response behavior is specified for the isolated delegation runner.

### Testing consequences

Replace subprocess/JSONL mocking with protocol-level fixtures.

Recommended test strategy:

- Generate and pin App Server JSON Schema fixtures from the supported Codex version.
- Add transcript-replay tests for:
  - successful turn completion
  - failed turn
  - interrupted turn
  - steer accepted / steer rejected
  - detached review
  - forked thread
  - advisory broker crash with persisted turn recovery
  - advisory broker crash without persisted turn recovery
  - approval request / resolution
  - isolation: delegation session approvals do not affect advisory broker behavior
- Keep hook-path tests authoritative: a Codex-facing tool call must still be blockable by `codex_guard.py` before the broker or delegation runner dispatches.
- Keep plugin-specific contract tests around safety, scope, and analytics.

The current 841-test surface should shrink in transport-specific mocking and grow in protocol-state-machine coverage.

## 9. Readiness

`Best available`

This recommendation is strong, but two conditions should be validated before implementation starts:

1. A short spike confirms that one plugin-local stdio App Server process can be supervised reliably in the Claude Code plugin host.
2. Delegation isolation and approval behavior are specified clearly enough that the isolated delegation runner can answer App Server approval requests without sharing state with advisory flows.

If those two checks pass, this recommendation upgrades to `verifiably best`.

## Short implementation sequence

1. Build the advisory `AppServerSupervisor` + `JsonRpcClient` + transcript fixtures.
2. Keep hook-level enforcement authoritative while adding bridge-level preflight validation.
3. Implement `ConsultationService` on `thread/start` + `turn/start`.
4. Implement `DialogueService` with persistent thread state, explicit fork semantics, `thread/read`, and `turn/steer`.
5. Replace `codex-reviewer` transport with `review/start`.
6. Implement the isolated `DelegationRunner` only after delegation approval semantics and isolation guarantees are nailed down.

## Provenance

- Local plugin architecture:
  - [`scripts/codex_consult.py`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/scripts/codex_consult.py)
  - [`scripts/codex_shim.py`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/scripts/codex_shim.py)
  - [`README.md`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/README.md)
  - [`agents/codex-dialogue.md`](/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/agents/codex-dialogue.md)
- Local verification evidence:
  - `uv run pytest --collect-only -q` in `packages/plugins/cross-model` -> `841 tests collected in 0.47s`
- External protocol sources:
  - [Codex App Server docs](https://developers.openai.com/codex/app-server/)
  - [Codex CLI reference](https://developers.openai.com/codex/cli/reference/)
  - [Open-source App Server README](https://github.com/openai/codex/blob/main/codex-rs/app-server/README.md)
