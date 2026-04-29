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

| Method | Current parser result | Classification needed |
|---|---|---|
| `item/commandExecution/requestApproval` | Supported as `command_approval` | Current-flow regression coverage |
| `item/fileChange/requestApproval` | Supported as `file_change` | Current-flow regression coverage |
| `item/tool/requestUserInput` | Supported as `request_user_input` | Current-flow regression coverage |
| `mcpServer/elicitation/request` | Parse failure with current required-field contract | Reachability in current advisory/delegation flows |
| `item/permissions/requestApproval` | Parsed as `unknown` when context fields are present | Reachability and intended terminal/support behavior |
| `item/tool/call` | Parse failure with current required-field contract | Reachability in current advisory/delegation flows |
| `account/chatgptAuthTokens/refresh` | Parse failure with current required-field contract | Runtime/auth reachability and intended handling |
| `applyPatchApproval` | Parse failure with current required-field contract | Whether alternate approval surface can appear in delegated execution |
| `execCommandApproval` | Parse failure with current required-field contract | Whether alternate approval surface can appear in delegated execution |

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

