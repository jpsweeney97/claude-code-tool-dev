# Architecture Note: Codex App Server Current Client-Platform Rebaseline

**Date:** 2026-05-01
**Status:** Evidence-bounded architecture note; not an implementation plan
**Selected runtime target:** installed `codex app-server`
**Selected runtime version:** `codex-cli 0.128.0`
**Related exploration packet:** `docs/diagnostics/2026-05-01-codex-app-server-client-platform-exploration.md`
**Related runtime packets:**

- `docs/diagnostics/2026-05-01-codex-app-server-scratch-home-runtime-probes.md`
- `docs/diagnostics/2026-05-01-codex-app-server-materialized-thread-and-server-request-probes.md`
- `docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md`

## Conclusion

The `codex-collaboration` client-platform rebaseline can now proceed as an
evidence-bounded architecture, but it must stay narrower than "Codex App Server
0.128.0 is fully compatible."

The current credible target is the locally installed `codex app-server` launcher,
not standalone `codex-app-server` equivalence. Live scratch-home probes now prove
the selected launcher can initialize, start threads, materialize
`thread/read(includeTurns=true)` after a user-message turn, and emit a live
schema-visible server-request envelope for
`item/commandExecution/requestApproval`.

That closes the broad "no live server-request envelope observed" blocker for the
observed command-approval method only. It does not prove live reachability,
parser cleanliness, response semantics, or lifecycle quality for the other
schema-visible server-request methods.

The implementation rebaseline should therefore proceed in two tracks:

1. Preserve the current client contract for the surfaces already required by
   `codex-collaboration`.
2. Add explicit capability and evidence boundaries for app-server 0.128 behavior
   that is only partially proven, especially permissions, unobserved server
   requests, and `thread/read` recovery semantics.

## Evidence Frame

This note is based on untracked worktree artifacts in:

`/Users/jp/Projects/active/claude-code-tool-dev/.worktrees/feature/codex-app-server-client-platform-exploration`

Do not describe this evidence as committed `HEAD` truth until the branch stages
and commits the diagnostic and architecture artifacts.

The evidence ladder is:

| Evidence packet | What it proves | What it does not prove |
|---|---|---|
| `2026-05-01-codex-app-server-client-platform-exploration.md` | source, release, schema, launcher, and surface map for the selected local target | live runtime behavior |
| `2026-05-01-codex-app-server-scratch-home-runtime-probes.md` | selected launcher handshake, pre-initialize rejection, scratch `thread/start`, scratch-home isolation, and unmaterialized `thread/read` lifecycle precondition | materialized turn projection or server-request reachability |
| `2026-05-01-codex-app-server-materialized-thread-and-server-request-probes.md` | materialized `thread/read(includeTurns=true)` exists after one user-message turn | recoverable agent output shape, reliable historical status/error fields, or server-request reachability |
| `2026-05-01-codex-app-server-server-request-envelope-probes.md` | scratch `chatgptDeviceCode` auth and one live `item/commandExecution/requestApproval` envelope with local `supported` classification | other server-request methods, response semantics, unsupported-method lifecycle cleanliness, or standalone launcher equivalence |

## Current Runtime Target

The rebaseline should target `codex app-server` first.

Facts now captured:

- selected launcher: `/opt/homebrew/bin/codex`
- version: `codex-cli 0.128.0`
- binary SHA-256:
  `ff803d4b5c595af19b99c18db6def26539fdf4da23a035ab30809835631e8e4b`
- standalone `codex-app-server`: release-visible but not installed locally in
  this evidence set
- transport: stdio remains the current runtime model

Implication:

`codex-collaboration` should not claim equivalence between `codex app-server`
and standalone `codex-app-server` until the standalone artifact is installed or
downloaded in a controlled probe and its schema/runtime behavior is compared
against the selected launcher.

## Required Surface Posture

| Surface | Rebaseline posture | Evidence status |
|---|---|---|
| `initialize` / `initialized` | required | live-proven under scratch `CODEX_HOME` |
| request-before-initialize rejection | required invariant | live-proven |
| stdio transport | required | selected launcher and probes use it |
| `account/read` | required diagnostic/auth-state read | live-proven before and after scratch auth; `requiresOpenaiAuth` alone is not a sufficient unauthenticated-state proof |
| `thread/start` | required | live-proven under scratch `CODEX_HOME` |
| `thread/read(includeTurns=false)` | required diagnostic/projection surface | live-proven immediately after `thread/start` |
| `thread/read(includeTurns=true)` | required but supplemental | live-proven only after materialization; unmaterialized threads reject it with a lifecycle error |
| `turn/start` | required | live-proven for constrained model-mediated probes |
| `turn/interrupt` | required for cleanup and unknown-request handling | used by local code; not separately live-proven in this packet set |
| `thread/resume` / `thread/fork` | required by current recovery and dialogue behavior | source/code-visible; not separately live-proven in this packet set |
| `item/commandExecution/requestApproval` | supported server-request method | live-proven and locally classified as `supported` |
| `item/fileChange/requestApproval` | supported by parser shape, still needs live coverage | local parser maps it, but no live envelope observed here |
| `item/tool/requestUserInput` | supported by parser shape, still needs live coverage | local parser maps it, but no live envelope observed here |
| `item/permissions/requestApproval` | unobserved risk | schema-visible; currently expected to parse as `unknown` if required correlation fields are present |
| `mcpServer/elicitation/request` | unobserved risk | schema-visible; current parser may fail if correlation fields are absent or nullable |
| `item/tool/call` | unobserved risk | schema-visible; current parser may fail because the parser requires `itemId` |
| `account/chatgptAuthTokens/refresh` | unobserved risk | schema-visible auth/runtime method; not a current collaboration execution capability |
| `applyPatchApproval` / `execCommandApproval` | unobserved alternate approval surfaces | schema-visible; no live evidence in current collaboration flows |
| `command/exec` | diagnostic only | useful for probes, not a replacement for delegated turn execution |
| `thread/shellCommand` | dangerous / do not adopt by default | separate security design required |
| config, trust, and fs APIs | dangerous / do not adopt by default | can mutate config, trust, or filesystem outside current plugin guardrails |
| skills, plugins, apps, MCP, realtime, external-agent import | future scope | out of immediate delegate-execution rebaseline |

## Runtime Design Implications

### 1. Treat live notifications as primary turn truth

`runtime.py` already uses live notifications to collect `item/completed` agent
messages and waits for `turn/completed` before returning a `TurnExecutionResult`.
That remains the correct primary path.

`thread/read` should remain supplemental for recovery and diagnostics, not the
primary terminal-status authority. The materialized-thread packet observed a
real discrepancy: live `turn/completed` reported a failed auth turn, while
historical `thread/read(includeTurns=true)` projected the same turn as completed
with `error: null` and only the user message.

Implementation rule:

- use live `turn/completed` for terminal status/error when it is available;
- use `thread/read` as best-effort historical projection and advisory fallback;
- do not use `thread/read` status/error to overwrite a stronger live
  notification result.

### 2. Keep reply recovery advisory until successful agent output is captured

The current runtime only enables `thread/read` fallback on advisory turns
through `fallback_on_empty_message=True`. Execution turns do not use that
fallback.

The new runtime probes do not justify widening that behavior. They prove that a
materialized projection exists, but the captured projection contains no
top-level `agentMessage`, no legacy `items[]` `agentMessage`, and no other
recoverable agent-output shape.

Implementation rule:

- keep fallback reply extraction advisory-only;
- keep `_fallback_extract_agent_message()` best-effort and non-raising;
- do not claim fallback recovery is live-proven until a successful
  reply-bearing turn exposes a recoverable shape.

### 3. Scope server-request support to observed and parser-owned methods

The live envelope packet upgrades the server-request posture from
"unproven reachability" to "proven reachability for one supported method."

Observed live method:

- `item/commandExecution/requestApproval`

Observed compatibility facts:

- JSON-RPC `id` was present;
- `itemId`, `threadId`, and `turnId` were present;
- `availableDecisions` was present in the params keys;
- local classification was `supported`;
- no approval response was sent during the probe.

Local parser facts:

- `approval_router.py` maps `item/commandExecution/requestApproval` to
  `command_approval`;
- it also maps `item/fileChange/requestApproval` to `file_change`;
- it maps `item/tool/requestUserInput` to `request_user_input`;
- all other methods become `unknown` if parsing succeeds;
- parsing fails if `params`, JSON-RPC `id`, `itemId`, `threadId`, or `turnId`
  are absent or not shaped as required.

Implementation rule:

- advertise or rely on live support only for methods with live envelope evidence;
- claim live response semantics only after a live response path is exercised or
  a narrower non-response contract is explicitly documented;
- use fixture-backed tests to prove parser behavior, intentional handling,
  terminalization, or documented non-support, not live reachability;
- keep file-change and request-user-input as parser-supported but
  live-unobserved until coverage exists;
- keep permissions, MCP elicitation, tool call, auth refresh, and legacy
  approval methods as explicit risks, not silent compatibility.

### 4. Do not collapse fail-closed behavior into lifecycle cleanliness

The current delegation controller has two broad unknown/unsupported paths:

- parse failures create a minimal `unknown` causal record and terminalize the job
  as `unknown`;
- parseable non-parkable methods preserve more context but still interrupt and
  terminalize rather than park for operator decision.

That can be a safe stop behavior, but it is not the same thing as clean support
or complete lifecycle semantics.

Implementation rule:

- keep parse failure, parseable unknown, parked escalation, response dispatch,
  timeout, internal abort, and dispatch failure as separate evidence buckets;
- do not mark `T-20260429-02` closed solely because one command-approval
  envelope was observed;
- close or narrow that ticket only after each schema-visible method is
  classified by live evidence, fixture-backed test, or documented non-relevance.

### 5. Preserve scratch-home isolation for probes

The probes established that the selected launcher respects scratch `CODEX_HOME`
and can complete scratch `chatgptDeviceCode` auth without copying operator-home
credentials.

That proves a safe probe strategy. It does not decide production Codex-home
ownership.

Implementation rule:

- every future runtime probe should keep using scratch `CODEX_HOME` or an
  explicit non-durable trust/config strategy;
- durable artifacts must not serialize auth URLs, user codes, login IDs,
  account identifiers, tokens, cookies, or operator-home credential material;
- production use of the operator's real Codex home remains a separate design
  decision.

### 6. Keep v128 permission-branch work separate

This rebaseline does not decide Branch A1/A2/A3/B/C/D from:

`docs/plans/2026-05-01-codex-app-server-v128-execution-sandbox-migration-plan.md`

The existing v128 architecture note still controls the permission-model fork:

`docs/architecture/2026-05-01-codex-app-server-v128-permission-architecture-implications.md`

Implementation rule:

- do not treat server-request reachability as permission-branch proof;
- do not treat stable `sandboxPolicy` acceptance, experimental `permissions`,
  built-in profiles, user-defined profiles, or thread-level
  `activePermissionProfile` provenance as decided by this note;
- keep execution sandbox migration behind the v128 decision packet.

### 7. Add explicit capability records before widening client ownership

The current client code has been operating against a narrow runtime contract.
The 0.128 evidence shows a broader client platform with transport choices,
config/trust APIs, filesystem APIs, plugin/app/MCP surfaces, realtime APIs, and
standalone packaging.

Implementation rule:

- add a versioned capability/evidence record before depending on any broadened
  surface;
- distinguish stable schema, experimental schema, static source evidence, live
  runtime evidence, and local parser/runtime support;
- record selected launcher kind, launcher path, launcher version, schema
  provenance, and whether experimental API was negotiated.

## Recommended Implementation Plan Shape

The follow-up implementation plan should not be a single "update to 0.128" task.
It should be split into narrow slices:

1. **Evidence and compatibility record:** introduce a local capability matrix for
   launcher, version, stable schema, experimental schema, and runtime probe
   status.
2. **Server-request hardening:** convert the command-approval live evidence into
   regression coverage, then classify the remaining schema-visible methods by
   live evidence, fixture-backed synthetic tests, or documented non-relevance.
3. **`thread/read` recovery boundary:** preserve advisory-only fallback and add
   tests or docs that prevent historical status/error fields from overriding live
   turn notifications.
4. **Launcher abstraction:** keep `codex app-server` as the selected target, but
   add a future path for standalone `codex-app-server` equivalence probes before
   dual-target support.
5. **v128 permission branch:** execute the separate permission migration plan and
   wire the selected permission mode without overloading `sandbox_policy` if the
   winning branch is profile/config based.

## Architecture Readiness

Ready to draft an implementation plan:

- yes, if the plan is scoped to the selected `codex app-server` launcher and
  carries the limits above.

Ready to claim complete 0.128 compatibility:

- no.

Ready to close the broad live-envelope blocker:

- yes, for observed command-approval reachability.

Ready to close the unsupported-method reachability and lifecycle ticket:

- no. The ticket should narrow from "no live server-request evidence" to
  "remaining schema-visible methods need method-by-method classification and
  regression/terminalization proof."

Ready to claim `thread/read` fallback recovery:

- no. Materialization is proven; successful agent-output recovery is not.

## Non-Decisions

This note does not decide:

- whether production should use a scratch Codex home;
- whether production should use standalone `codex-app-server`;
- which v128 permission branch wins;
- whether `codex-collaboration` should adopt config, trust, fs, plugin, app,
  MCP, realtime, or external-agent APIs;
- whether unobserved server-request methods should be supported, terminalized,
  or proven unreachable;
- whether reply-bearing `thread/read` projections expose a recoverable
  `agentMessage` shape on successful authenticated turns.
