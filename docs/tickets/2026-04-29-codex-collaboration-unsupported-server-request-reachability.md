# T-20260429-02: Classify unsupported App Server request reachability

```yaml
id: T-20260429-02
date: 2026-04-29
status: open
priority: high
tags: [codex-collaboration, delegation, app-server, compatibility, runtime]
blocked_by: []
blocks: []
effort: medium
```

## Context

The codex-collaboration runtime handles server-initiated JSON-RPC requests
during delegated execution. The current parser accepts only requests whose
params contain string `itemId`, `threadId`, and `turnId`, then maps only three
methods to parkable operator decisions:

- `item/commandExecution/requestApproval`
- `item/fileChange/requestApproval`
- `item/tool/requestUserInput`

Other App Server `ServerRequest` methods exist in the current vendored
`0.117.0` schema and remain present in the generated `0.125.0` schema. Some of
these methods do not have the context fields the parser currently requires.

The selected `0.117.0` to `0.125.0` schema delta evidence map records this as
latent current-runtime debt, not only future pin-update work:

- `docs/superpowers/specs/codex-collaboration/2026-04-29-codex-app-server-0.125.0-schema-delta.md`

## Current Runtime Behavior

During `_run_turn()`, method-bearing messages with object params are collected
as notifications. Messages whose `turnId` is present and different from the
current turn are skipped. If the message has an `id` and a
`server_request_handler` is installed, the handler is invoked.

`approval_router.parse_pending_server_request()` hard-requires context fields
and maps only the three parkable methods above. In delegation execution,
server-request parse failures or parsed-but-unknown methods can create minimal
`unknown` pending records, interrupt the running turn, and terminalize the job
as `unknown`.

That behavior can be safe as an intentional terminal state, but it is not yet
classified method by method.

## Methods To Classify

The delegation controller has two distinct code paths for unsupported
server requests. Both terminalize the job as `unknown`, but the
diagnostic quality differs:

| Path | Code location | Trigger | Diagnostic quality |
|---|---|---|---|
| Parse-failure | `delegation_controller.py:984` catch | `_require_string` raises for missing `itemId`, `threadId`, or `turnId` | Minimal: empty context fields, only `raw_method` in `requested_scope` |
| Known-parsed non-parkable | `delegation_controller.py:1072` | Parse succeeds but `kind` is not in the parkable set | Full: real context fields preserved, full `requested_scope` |

Note: `availableDecisions` is also in `_REQUEST_CONTEXT_KEYS`
(`approval_router.py:13`) and is stripped from `requested_scope` by the
context-key filter, but it is not a required string field for parser
acceptance. Methods that carry `availableDecisions` will have those
values silently excluded from the preserved `requested_scope`.

| Method | Current parser result | Failure path | Classification needed |
|---|---|---|---|
| `item/commandExecution/requestApproval` | Supported as `command_approval` | Supported (parked) | Current-flow regression coverage |
| `item/fileChange/requestApproval` | Supported as `file_change` | Supported (parked) | Current-flow regression coverage |
| `item/tool/requestUserInput` | Supported as `request_user_input` | Supported (parked) | Current-flow regression coverage |
| `item/permissions/requestApproval` | Parsed successfully as `unknown` (has `itemId`, `threadId`, `turnId` per schema) | Known-parsed non-parkable | Reachability and intended terminal/support behavior |
| `mcpServer/elicitation/request` | Parse failure: `turnId` is nullable/non-required | Parse-failure | Reachability in current advisory/delegation flows |
| `item/tool/call` | Parse failure: missing `itemId` | Parse-failure | Reachability in current advisory/delegation flows |
| `account/chatgptAuthTokens/refresh` | Parse failure: missing `itemId`, `threadId`, `turnId` | Parse-failure | Runtime/auth reachability and intended handling |
| `applyPatchApproval` | Parse failure: missing `itemId`, `threadId`, `turnId` | Parse-failure | Whether alternate approval surface can appear in delegated execution |
| `execCommandApproval` | Parse failure: missing `itemId`, `threadId`, `turnId` | Parse-failure | Whether alternate approval surface can appear in delegated execution |

## Acceptance Criteria

- [ ] Each unsupported `ServerRequest` method is classified as one of:
      current delegated/advisory flow, theoretically possible but unobserved,
      auth/runtime support only, alternate approval surface, or unrelated to
      codex-collaboration execution.
- [ ] Each current-flow or plausibly reachable method has either:
      supported handling, a regression test proving intentional safe terminal
      behavior, or a documented runtime non-reachability proof.
- [ ] Supported methods retain regression coverage for capture, operator
      projection, decision dispatch, and response payload shape.
- [ ] Evidence names the source used for classification: live emitted request,
      fixture-backed synthetic test, App Server schema, or code-path analysis.
- [ ] If this work is used as part of a tested-version pin update, the
      compatibility-update artifact links this ticket and records its final
      disposition.

## Investigation Notes

This ticket is deliberately narrower than a `0.125.0` adoption plan. It tracks
the current runtime question: what happens if an existing unsupported
server-initiated request is emitted while codex-collaboration owns a turn.

