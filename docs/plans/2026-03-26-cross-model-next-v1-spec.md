# Cross-Model Next V1 Implementation Spec

**Status:** Proposed implementation spec
**Date:** 2026-03-26
**Audience:** Claude Code plugin implementers working in `claude-code-tool-dev`
**Scope:** New sibling plugin at `packages/plugins/cross-model-next/`

## 1. Decision

Build a new **Claude Code plugin** named `cross-model-next` that replaces the legacy
`codex exec` consultation transport with a supervised `codex app-server` child
process over stdio.

V1 is **advisory-only**:

- include quick consultation
- include orchestrated multi-turn dialogue
- include review
- include analytics
- exclude delegation from the shared runtime

Delegation is intentionally out of scope for V1 because App Server approval state
and write permissions are part of the trust boundary. Advisory and delegation
must not share a runtime in the first release.

## 2. Why This Shape

### Recommended option

Use a **plugin-owned advisory broker** on top of `codex app-server`, exposed to
Claude through a compact plugin MCP surface.

Why:

- It unlocks native App Server lifecycle features: initialize once, thread start,
  resume, fork, steer, review, and structured item streaming.
- It keeps plugin-specific control where it belongs: credential scanning, scope
  rules, analytics, and dialogue orchestration stay in plugin code.
- It matches Claude Code plugin constraints cleanly: root-level `skills/`,
  `agents/`, `hooks/`, and `.mcp.json`, with only `plugin.json` inside
  `.claude-plugin/`.

### Rejected alternatives

1. Stateless App Server bridge per request
   - Too little gain for the migration cost.
   - Preserves batch-mode behavior.

2. Raw App Server passthrough MCP server
   - Pushes JSON-RPC lifecycle details into prompts and agent markdown.
   - Bloats the Claude-facing tool surface.

3. Full advisory + delegation rewrite in one pass
   - Collapses the trust boundary too early.
   - Increases failure modes before the advisory broker is proven.

## 3. Claude Code Constraints That This Spec Must Respect

These constraints are normative for the plugin structure and runtime wiring:

- The plugin uses the standard Claude Code layout with `.claude-plugin/plugin.json`
  at the root metadata directory, and `skills/`, `agents/`, `hooks/`, `.mcp.json`,
  and `settings.json` at the plugin root.
- Only `plugin.json` belongs inside `.claude-plugin/`.
- Plugin MCP servers can be declared in `.mcp.json` and start automatically when
  the plugin is enabled.
- Hook matchers for `PreToolUse` and `PostToolUse` run against the tool name and
  can target plugin MCP tools by regex.
- Plugin-shipped agents do **not** support `hooks`, `mcpServers`, or
  `permissionMode` frontmatter, so those controls must live at the plugin root
  or in skill instructions, not in the agent files themselves.
- Plugin paths in manifest config must be relative and start with `./` when
  custom paths are used.
- `${CLAUDE_PLUGIN_ROOT}` is the correct reference for bundled files.
- `${CLAUDE_PLUGIN_DATA}` is the correct location for persistent plugin-owned
  state that must survive plugin updates.

## 4. Plugin Identity

### Package path

`packages/plugins/cross-model-next/`

### Manifest

`packages/plugins/cross-model-next/.claude-plugin/plugin.json`

```json
{
  "name": "cross-model-next",
  "version": "0.1.0",
  "description": "Codex App Server-backed advisory collaboration for Claude Code",
  "author": {
    "name": "JP"
  },
  "license": "MIT",
  "keywords": [
    "codex",
    "app-server",
    "consultation",
    "dialogue",
    "review",
    "cross-model"
  ]
}
```

### Naming rationale

Use `cross-model-next` instead of `cross-model` so both plugins can be loaded
side-by-side during development and migration. If V1 fully replaces the legacy
plugin later, renaming back to `cross-model` is a separate cutover task.

## 5. Package Layout

```text
packages/plugins/cross-model-next/
├── .claude-plugin/
│   └── plugin.json
├── .mcp.json
├── CHANGELOG.md
├── README.md
├── HANDBOOK.md
├── pyproject.toml
├── hooks/
│   └── hooks.json
├── agents/
│   ├── codex-dialogue.md
│   ├── codex-reviewer.md
│   ├── context-gatherer-code.md
│   └── context-gatherer-falsifier.md
├── skills/
│   ├── consult/
│   │   └── SKILL.md
│   ├── dialogue/
│   │   └── SKILL.md
│   └── consultation-stats/
│       └── SKILL.md
├── references/
│   ├── consultation-contract.md
│   ├── dialogue-contract.md
│   └── app-server-adapter.md
├── scripts/
│   ├── codex_broker_server.py
│   ├── codex_guard.py
│   ├── emit_analytics.py
│   ├── read_events.py
│   ├── compute_stats.py
│   ├── retrieve_learnings.py
│   └── broker/
│       ├── __init__.py
│       ├── jsonrpc.py
│       ├── app_server_client.py
│       ├── protocol_views.py
│       ├── supervisor.py
│       ├── thread_runtime.py
│       ├── turn_accumulator.py
│       ├── server_requests.py
│       ├── consultation_service.py
│       ├── dialogue_service.py
│       ├── review_service.py
│       └── errors.py
├── context-injection/
│   └── ...
├── tests/
│   ├── fixtures/
│   │   ├── app_server/
│   │   ├── schema/
│   │   └── events/
│   ├── test_mcp_wiring.py
│   ├── test_hook_wiring.py
│   ├── test_jsonrpc_client.py
│   ├── test_turn_accumulator.py
│   ├── test_thread_runtime.py
│   ├── test_consultation_service.py
│   ├── test_dialogue_service.py
│   ├── test_review_service.py
│   ├── test_codex_guard.py
│   ├── test_event_log.py
│   └── test_compute_stats.py
└── uv.lock
```

## 6. V1 User-Facing Capability Set

### In scope

1. `/cross-model-next:consult`
   - quick advisory Codex consultation
   - new thread or resume existing thread
   - blocking call that waits for `turn/completed`

2. `/cross-model-next:dialogue`
   - structured multi-turn consultation
   - retains proactive codebase gathering and the transitional `context-injection`
     adapter
   - supports explicit steering and explicit fork

3. `codex-reviewer` agent
   - uses native `review/start`
   - supports inline or detached review delivery

4. `/cross-model-next:consultation-stats`
   - reads plugin-owned event log
   - reports consult/dialogue/review activity

### Out of scope

- autonomous delegation
- shared write-capable App Server runtime
- plugin channels
- LSP integration
- raw App Server passthrough tools

## 7. Runtime Architecture

### Process model

The plugin runs two MCP servers:

1. `codex-advisory`
   - local FastMCP server implemented by `scripts/codex_broker_server.py`
   - exposes the plugin-owned advisory MCP tools
   - supervises one long-lived `codex app-server` stdio child

2. `context-injection`
   - Python MCP server retained from the current cross-model package as a
     **transitional compatibility adapter**
   - used only by the dialogue workflow in V1
   - must not become a second general-purpose advisory control plane

### Transitional adapter rule

`context-injection` is transitional, not permanent.

Exit condition:

- retire `context-injection` after the advisory broker can produce the same
  scope-checked, redacted dialogue seed context directly and parity tests cover
  the current gatherer behavior

Until that exit condition is met:

- no new non-dialogue feature may depend on `context-injection`
- dialogue remains the only workflow allowed to call it

### Advisory child lifecycle

The `codex-advisory` server owns one child process:

```text
codex app-server --listen stdio://
```

Startup sequence:

1. spawn child
2. send `initialize`
3. send `initialized`
4. mark broker healthy

Shutdown sequence:

1. stop accepting new tool requests
2. allow active advisory turns to finish if possible
3. terminate child
4. clear in-memory thread runtime

### Startup compatibility gate

Before the broker is marked healthy, it must prove that the installed local
Codex binary is inside the plugin's supported compatibility envelope.

Required checks:

1. capture `codex --version`
2. complete `initialize` / `initialized`
3. verify that the server advertises and successfully supports the V1-required
   method subset:
   - `thread/start`
   - `thread/resume`
   - `thread/read`
   - `thread/fork`
   - `turn/start`
   - `turn/steer`
   - `turn/interrupt`
   - `review/start`
4. verify that the notification subset used by `protocol_views.py` and
   `turn_accumulator.py` is present and parseable
5. verify that advisory flows do not require unsupported server-initiated
   requests

If any check fails:

- the broker remains unhealthy
- all advisory tools fail fast with a structured startup compatibility error
- schema fixtures generated from the installed local binary are treated as test
  inputs, not as automatic proof of support

### Advisory execution policy

All advisory tools run under a broker-enforced execution policy:

- sandbox is fixed to restrictive advisory mode in V1
- interactive write approvals are disallowed
- callers may not widen sandbox or approval scope through tool inputs

V1 implication:

- `approvalPolicy` and `sandbox` are not caller-controlled fields on the public
  tool surface
- service- or profile-level routing may affect model and reasoning settings, but
  never the advisory trust boundary

### Admission control, queueing, and cancellation

V1 uses bounded admission on top of the singleton advisory child:

- at most 1 active advisory turn across `consult`, `dialogue-turn-start`, and
  `review-start` per broker process
- up to 8 queued turn-start requests in FIFO order
- queue overflow returns structured `overloaded`
- `dialogue-turn-steer` is accepted only for the currently active turn and
  bypasses the start queue
- `thread-read` may run while the queue is non-empty
- `thread-fork` is rejected for a thread with an active turn

Cancellation rules:

- if the caller disconnects or cancels while a turn is active, the broker must
  attempt `turn/interrupt`
- if interruption succeeds, the terminal tool result is `interrupted`
- if interruption cannot be confirmed before transport loss, the broker returns
  `transport lost` and clears the active-turn slot during recovery

### Broker principles

- one child process per plugin MCP server process
- one JSON-RPC reader task
- one serialized writer
- one broker-owned advisory execution policy
- one bounded global admission queue for turn-start requests
- request/response correlation by numeric request id
- item and turn state built from streamed notifications, not string scraping
- fail fast on unexpected server requests in V1
- fail closed on unsupported App Server versions or capabilities
- no advisory call may silently downgrade to `codex exec`

## 8. `.mcp.json`

```json
{
  "mcpServers": {
    "codex-advisory": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "${CLAUDE_PLUGIN_ROOT}",
        "python",
        "${CLAUDE_PLUGIN_ROOT}/scripts/codex_broker_server.py"
      ],
      "env": {
        "CODEX_SANDBOX": "seatbelt",
        "CROSS_MODEL_EVENT_LOG": "${CLAUDE_PLUGIN_DATA}/events.jsonl",
        "CROSS_MODEL_LINEAGE_LOG": "${CLAUDE_PLUGIN_DATA}/thread_lineage.jsonl"
      }
    },
    "context-injection": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "${CLAUDE_PLUGIN_ROOT}/context-injection",
        "python",
        "-m",
        "context_injection"
      ],
      "env": {
        "REPO_ROOT": "${PWD}"
      }
    }
  }
}
```

## 9. Exact MCP Tool Surface

The new plugin does **not** expose raw App Server methods. It exposes the
following compact tool surface from the `codex-advisory` server.

Execution policy for all advisory tools:

- broker-enforced restrictive sandbox
- broker-enforced non-interactive advisory approval mode
- no caller-provided field may widen execution permissions

### Tool 1: `consult`

Purpose:
- one blocking advisory turn on a new or existing thread

Inputs:
- `prompt: str`
- `threadId: str | null`
- `model: str | null`
- `cwd: str | null`
- `reasoningEffort: str | null`
- `serviceName: str | null`

Outputs:
- `threadId: str`
- `turnId: str`
- `status: "completed" | "failed" | "interrupted"`
- `responseText: str`
- `items: list`
- `usage: object | null`
- `reviewMode: false`

### Tool 2: `dialogue-turn-start`

Purpose:
- start a managed dialogue turn on a new or existing thread

Inputs:
- `prompt: str`
- `threadId: str | null`
- `model: str | null`
- `cwd: str | null`
- `reasoningEffort: str | null`
- `profileName: str | null`
- `scopeEnvelope: object | null`

Outputs:
- `threadId: str`
- `turnId: str`
- `status: "completed" | "failed" | "interrupted"`
- `items: list`
- `responseText: str`
- `usage: object | null`

### Tool 3: `dialogue-turn-steer`

Purpose:
- append user input to an already in-flight advisory turn

Inputs:
- `threadId: str`
- `turnId: str`
- `prompt: str`

Outputs:
- `threadId: str`
- `turnId: str`
- `accepted: bool`

### Tool 4: `thread-read`

Purpose:
- read persisted thread state plus broker-owned lineage metadata for recovery,
  continuity, or synthesis

Inputs:
- `threadId: str`
- `includeTurns: bool = false`

Outputs:
- `thread: object`

### Tool 5: `thread-fork`

Purpose:
- explicitly fork an advisory thread

Inputs:
- `threadId: str`
- `reason: str`
- `ephemeral: bool = false`

Outputs:
- `thread: object`
- `parentThreadId: str`
- `forkReason: str`

Success rule:

- the broker does not return success from `thread-fork` until the lineage record
  is durably appended to `${CROSS_MODEL_LINEAGE_LOG}`

### Tool 6: `review-start`

Purpose:
- invoke native Codex review on a thread

Inputs:
- `threadId: str`
- `target: object`
- `delivery: "inline" | "detached" = "inline"`

Outputs:
- `threadId: str`
- `reviewThreadId: str | null`
- `turnId: str`
- `status: "completed" | "failed" | "interrupted"`
- `reviewText: str`
- `items: list`

## 10. Exact Python Module Responsibilities

### Server entrypoint

`scripts/codex_broker_server.py`

- creates the FastMCP server
- registers the 6 advisory tools
- translates tool inputs to broker service calls
- performs no business logic beyond validation and translation

### JSON-RPC layer

`scripts/broker/jsonrpc.py`

- request id allocation
- raw JSON encode/decode
- response correlation
- transport-level error normalization

### App Server child client

`scripts/broker/app_server_client.py`

- spawn and supervise `codex app-server`
- perform initialize handshake
- own reader and writer tasks
- send requests and await responses
- expose notification stream to higher layers
- surface capability and version metadata needed by the startup compatibility
  gate

### Protocol views

`scripts/broker/protocol_views.py`

- typed Python views over the subset of App Server payloads that V1 uses
- no full-schema reimplementation
- stable parsed views for:
  - thread start/resume/fork result
  - turn start/complete
  - item started/completed
  - agent message delta
  - entered/exited review mode

### Supervisor

`scripts/broker/supervisor.py`

- owns the singleton child client
- capture `codex --version`
- enforce the startup compatibility gate
- health state
- own bounded admission state for advisory turn starts
- route interruption on caller cancellation or shutdown
- restart policy
- graceful shutdown

### Thread runtime

`scripts/broker/thread_runtime.py`

- per-thread in-memory state
- active turn bookkeeping
- loaded thread registry
- merge App Server thread state with durable lineage metadata from
  `${CROSS_MODEL_LINEAGE_LOG}`
- rehydrate lineage cache on broker restart
- advisory-only fork lineage metadata:
  - `parent_thread_id`
  - `fork_origin_turn_id`
  - `fork_reason`

### Turn accumulator

`scripts/broker/turn_accumulator.py`

- consume streamed App Server notifications
- accumulate authoritative terminal turn state
- preserve:
  - final `agentMessage`
  - `plan`
  - `reasoning`
  - `commandExecution`
  - `fileChange`
  - `mcpToolCall`
  - `dynamicToolCall`
  - `enteredReviewMode`
  - `exitedReviewMode`
- treat `item/completed` and `turn/completed` as authoritative

### Server request handling

`scripts/broker/server_requests.py`

- classify and reject unexpected server-initiated requests in V1
- allow an explicit future extension point for:
  - `tool/requestUserInput`
  - permission requests
  - MCP elicitations

V1 rule:

- advisory broker runs with restrictive policies and must not expect interactive
  write approvals
- any unexpected server request becomes a structured broker error, not a hang

### Domain services

`scripts/broker/consultation_service.py`

- implement `consult`
- own new-vs-resume thread logic for single-turn advisory use

`scripts/broker/dialogue_service.py`

- implement `dialogue-turn-start`, `dialogue-turn-steer`, `thread-read`, and
  `thread-fork`
- own dialogue-specific continuity rules
- integrate with the transitional `context-injection` adapter
- reject forks on active turns and persist lineage before returning success

`scripts/broker/review_service.py`

- implement `review-start`
- normalize inline vs detached review delivery

### Shared errors

`scripts/broker/errors.py`

- transport lost
- child startup failure
- initialize failure
- startup compatibility failure
- overloaded
- unsupported server request
- invalid thread
- invalid turn
- unexpected protocol payload

### Hooks and analytics

`scripts/codex_guard.py`

- `PreToolUse` outbound secret scan for advisory MCP tools
- `PostToolUse` event-log emission
- authoritative outer gate for advisory egress

`scripts/emit_analytics.py`

- build `consultation_outcome`, `dialogue_outcome`, and `review_outcome`
  records in schema version 1
- redact or omit all raw prompt, response, item, plan, reasoning, command, file
  change, and gathered-evidence content before persistence
- enforce event-log retention pruning after append

`scripts/read_events.py`

- read plugin-owned event log from `${CROSS_MODEL_EVENT_LOG}`
- validate event schema version and ignore malformed records

`scripts/compute_stats.py`

- compute usage and quality stats for consult, dialogue, and review

`scripts/retrieve_learnings.py`

- pull relevant entries from repo learnings for advisory briefings

## 11. Hooks

`hooks/hooks.json` must define:

1. `PreToolUse`
   - matcher:
     `mcp__plugin_cross-model-next_codex-advisory__consult|mcp__plugin_cross-model-next_codex-advisory__dialogue-turn-start|mcp__plugin_cross-model-next_codex-advisory__dialogue-turn-steer|mcp__plugin_cross-model-next_codex-advisory__review-start`
   - command:
     `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/codex_guard.py`

2. `PostToolUse`
   - same matcher
   - same command
   - emitted records must follow the redacted event schema defined in Section 13

There is **no** V1 hook for context-injection tools.

## 12. Skills And Agents

### Skills

`skills/consult/SKILL.md`

- explicit quick advisory consultation skill
- default path for single-turn second opinions
- uses `consult`

`skills/dialogue/SKILL.md`

- orchestrated multi-turn consultation
- retains parallel gatherers and the transitional `context-injection` adapter
- uses `dialogue-turn-start`, `dialogue-turn-steer`, `thread-fork`, and
  `thread-read`

`skills/consultation-stats/SKILL.md`

- reads plugin-owned analytics
- no Codex network interaction

### Agents

`agents/codex-dialogue.md`

- owns multi-turn Codex conversation management
- must not define `hooks`, `mcpServers`, or `permissionMode`
- may declare only supported plugin-agent frontmatter

`agents/codex-reviewer.md`

- advisory review specialist
- uses `review-start`

`agents/context-gatherer-code.md`

- read-only code explorer for dialogue seed context

`agents/context-gatherer-falsifier.md`

- read-only assumption challenger for dialogue seed context

## 13. Persistent State

Use `${CLAUDE_PLUGIN_DATA}` for plugin-owned durable state:

- `${CLAUDE_PLUGIN_DATA}/events.jsonl`
- `${CLAUDE_PLUGIN_DATA}/thread_lineage.jsonl`
- `${CLAUDE_PLUGIN_DATA}/fixtures/` for generated schema snapshots if needed

Do **not** create a second durable thread database in V1.

Codex thread persistence remains owned by `codex app-server` and is accessed
through `thread/read` and `thread/resume`.

`thread_lineage.jsonl` is allowed because it stores only the minimum broker-owned
metadata needed for restart-safe advisory continuity. It is not a second copy of
thread content.

### Event-log policy

`${CLAUDE_PLUGIN_DATA}/events.jsonl` is append-only JSONL with schema version 1.

Allowed event types:

- `consultation_outcome`
- `dialogue_outcome`
- `review_outcome`
- `block_event`

Required fields on every record:

- `schemaVersion`
- `eventType`
- `timestamp`
- `pluginVersion`
- `toolName`
- `status`

Optional fields, when present:

- `durationMs`
- `model`
- `serviceName`
- `profileName`
- `reviewDelivery`
- `usage`
- `reasonCode`
- `threadRefHash`

Persisted event records must never contain:

- raw prompts
- raw response text
- streamed items
- plans or reasoning text
- command output
- file diffs or file contents
- gathered context or scout output
- unredacted secrets
- raw thread identifiers

Retention policy:

- keep at most 30 days of events or 10,000 records, whichever limit is reached
  first
- prune oldest records after append

## 14. First Test Fixture Set

All schema fixtures are generated from the **installed local** Codex binary, not
copied from GitHub source.

### Schema fixtures

- `tests/fixtures/schema/app_server_stable.json`
- `tests/fixtures/schema/app_server_experimental.json`

Generation command:

```bash
codex app-server generate-json-schema --out tests/fixtures/schema/stable
codex app-server generate-json-schema --out tests/fixtures/schema/experimental --experimental
```

The committed fixtures are then normalized to:

- `tests/fixtures/schema/app_server_stable.json`
- `tests/fixtures/schema/app_server_experimental.json`

### Transcript fixtures

These are line-oriented JSON-RPC transcripts used by replay tests:

- `tests/fixtures/app_server/initialize_ok.jsonl`
- `tests/fixtures/app_server/initialize_incompatible.jsonl`
- `tests/fixtures/app_server/consult_new_ok.jsonl`
- `tests/fixtures/app_server/consult_resume_ok.jsonl`
- `tests/fixtures/app_server/dialogue_steer_ok.jsonl`
- `tests/fixtures/app_server/thread_fork_ok.jsonl`
- `tests/fixtures/app_server/review_detached_ok.jsonl`
- `tests/fixtures/app_server/server_request_user_input.jsonl`
- `tests/fixtures/app_server/turn_interrupt_ok.jsonl`
- `tests/fixtures/app_server/overloaded_error.jsonl`

### Event-log fixtures

- `tests/fixtures/events/consultation_outcome_minimal.jsonl`
- `tests/fixtures/events/consultation_outcome_redacted.jsonl`
- `tests/fixtures/events/dialogue_outcome_server_assisted.jsonl`
- `tests/fixtures/events/event_log_pruned.jsonl`
- `tests/fixtures/events/review_outcome_minimal.jsonl`
- `tests/fixtures/events/block_event.jsonl`

## 15. First Test Module Set

### Wiring and layout

- `tests/test_mcp_wiring.py`
  - `.mcp.json` points at `codex_broker_server.py`
  - `context-injection` remains wired as a transitional adapter

- `tests/test_hook_wiring.py`
  - hook matcher targets the advisory MCP tools only

### Broker runtime

- `tests/test_jsonrpc_client.py`
  - initialize handshake
  - startup compatibility rejection
  - response correlation
  - overload error handling
  - child death handling
  - interrupt-on-cancel path

- `tests/test_turn_accumulator.py`
  - agent message delta accumulation
  - item-completed authority
  - review mode extraction

- `tests/test_thread_runtime.py`
  - lineage persistence
  - restart rehydration
  - `thread-read` lineage merge

### Domain services

- `tests/test_consultation_service.py`
  - new thread consult
  - resumed consult
  - broker-enforced advisory policy
  - queue overflow
  - transport lost

- `tests/test_dialogue_service.py`
  - dialogue turn start
  - steer
  - explicit fork lineage
  - reject fork on active turn
  - transitional `context-injection` contract wiring

- `tests/test_review_service.py`
  - inline review
  - detached review

### Safety and analytics

- `tests/test_codex_guard.py`
  - advisory tool matcher coverage
  - thread id extraction from tool input/output

- `tests/test_event_log.py`
  - append and read plugin-owned event log
  - redaction enforcement
  - retention pruning

- `tests/test_compute_stats.py`
  - consult/dialogue/review counts

## 16. Implementation Order

1. Create plugin skeleton and manifest.
2. Wire `.mcp.json` to `codex_broker_server.py`.
3. Implement `jsonrpc.py`, `app_server_client.py`, and `supervisor.py`.
4. Add startup compatibility gate using `codex --version` plus initialize
   capability checks.
5. Add transcript replay tests for initialize, incompatible startup, consult,
   interrupt, and overload paths.
6. Implement `turn_accumulator.py` and `thread_runtime.py` with durable lineage
   persistence.
7. Implement `consultation_service.py` with broker-enforced advisory policy and
   bounded admission.
8. Add hook guard and redacted event log with retention pruning.
9. Port dialogue path and keep `context-injection` as a transitional adapter
   only.
10. Implement `review_service.py`.
11. Add analytics and stats skill.
12. Validate plugin with `claude plugin validate`.
13. Test locally with `claude --plugin-dir ./packages/plugins/cross-model-next`.

## 17. Exit Criteria For V1

V1 is done when all of the following are true:

- `claude plugin validate` passes for the new plugin
- broker rejects unsupported local Codex/App Server versions before accepting
  advisory work
- `consult` works on a new thread and resumed thread under broker-owned
  advisory policy
- singleton-child queueing, overload, and cancellation semantics behave as
  specified
- `dialogue` works with the transitional `context-injection` adapter and
  explicit steer
- `thread-read` and `thread-fork` remain restart-safe through persisted lineage
- `review-start` works in detached mode
- hook-level advisory secret scanning blocks outbound secrets before dispatch
- event log writes redacted schema-versioned records under
  `${CLAUDE_PLUGIN_DATA}`
- event-log retention pruning is enforced
- transcript replay tests pass against committed fixtures
- no code path falls back to `codex exec`

## 18. Explicit Non-Goals For V1.1+

These are deferred follow-ups, not V1 deliverables:

- isolated delegation runtime
- session-scoped approval mediation
- background advisory threads
- raw App Server tool exposure
- thread archival UI
- retiring `context-injection` after advisory dialogue-seed parity is proven
- prompt-compatible migration shim for legacy `/cross-model:codex`
