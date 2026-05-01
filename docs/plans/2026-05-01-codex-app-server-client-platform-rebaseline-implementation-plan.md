# Codex App Server Client-Platform Rebaseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This is an implementation control plan with hard stop gates; do not convert it into a broad "0.128 compatibility" migration.

**Goal:** Turn the current client-platform rebaseline evidence into narrow, testable `codex-collaboration` compatibility work without overclaiming unobserved Codex App Server behavior.

**Architecture:** Treat launcher provenance, runtime evidence, parser support, fixture-backed handling, and live response semantics as separate evidence classes. Land the evidence/capability record first, harden server-request and `thread/read` boundaries second, and keep the v128 permission migration behind the existing branch-decision packet.

**Tech Stack:** Python, pytest, Markdown diagnostics, JSON evidence records, Codex App Server JSON-RPC, existing `codex-collaboration` runtime, approval router, delegation controller, and compatibility checks.

---

## Boundary

This plan implements:

- A durable capability/evidence record for the selected `codex app-server` 0.128.0 target.
- Regression coverage that pins the live-observed command-approval envelope and exposes current structured-decision loss.
- Method-by-method classification for schema-visible server-request methods, with explicit evidence basis.
- Tests and docs that preserve `thread/read` as advisory recovery, not terminal-status authority.
- A launcher-target posture that keeps `codex app-server` selected and standalone `codex-app-server` unclaimed.
- A stop-gated handoff to the v128 permission branch decision packet.

This plan does not:

- Claim complete Codex App Server 0.128.0 compatibility.
- Close `T-20260429-02` from the command-approval envelope alone.
- Implement a v128 execution sandbox or permission payload before the branch decision is recorded.
- Raise `TESTED_CODEX_VERSION` or `MINIMUM_CODEX_VERSION`.
- Adopt standalone `codex-app-server`, non-stdio transport, config/trust APIs, fs APIs, plugins/apps/MCP/realtime APIs, or `thread/shellCommand`.
- Run live probes that copy, read, print, hash, or serialize operator-home credentials.

## Evidence Classes

Use these terms consistently in code comments, diagnostics, tickets, and commit messages:

| Class | Meaning | Can justify |
|---|---|---|
| `live_runtime_evidence` | A real client request, response, or notification path was observed from the selected launcher | Live runtime behavior for that exact surface and scenario |
| `live_envelope_evidence` | A real server-initiated JSON-RPC request was observed from the selected launcher | Live reachability for that method only |
| `live_response_evidence` | The client sent a response and observed the resulting runtime path | Live response semantics for that method and decision only |
| `parser_support` | Local code parses the envelope into a known `PendingRequestKind` | Parser behavior and fixture-backed handling, not live reachability |
| `fixture_terminalization` | Tests prove the plugin intentionally terminalizes or rejects a synthetic shape | Safe local handling, not live reachability |
| `documented_non_relevance` | The method is schema-visible but documented as outside current collaboration flows | Ticket classification, not runtime support |
| `unobserved_risk` | Schema-visible method with no live evidence and no final non-relevance proof | Must remain visible in docs and tickets |

## Current Evidence Frame

All inputs in this worktree are untracked until staged and committed. Do not describe them as committed `HEAD` truth.

Active worktree:

```text
/Users/jp/Projects/active/claude-code-tool-dev/.worktrees/feature/codex-app-server-client-platform-exploration
```

Read first:

- `docs/architecture/2026-05-01-codex-app-server-current-client-platform-rebaseline.md`
- `docs/architecture/2026-05-01-codex-app-server-v128-permission-architecture-implications.md`
- `docs/diagnostics/2026-05-01-codex-app-server-client-platform-exploration.md`
- `docs/diagnostics/codex-app-server-client-platform-exploration.json`
- `docs/diagnostics/2026-05-01-codex-app-server-scratch-home-runtime-probes.md`
- `docs/diagnostics/codex-app-server-scratch-home-runtime-probes.json`
- `docs/diagnostics/2026-05-01-codex-app-server-materialized-thread-and-server-request-probes.md`
- `docs/diagnostics/codex-app-server-materialized-thread-and-server-request-probes.json`
- `docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md`
- `docs/diagnostics/codex-app-server-server-request-envelope-probes.json`
- `docs/plans/2026-05-01-codex-app-server-v128-execution-sandbox-migration-plan.md`
- `docs/tickets/2026-04-29-codex-collaboration-unsupported-server-request-reachability.md`
- `packages/plugins/codex-collaboration/server/approval_router.py`
- `packages/plugins/codex-collaboration/server/runtime.py`
- `packages/plugins/codex-collaboration/server/delegation_controller.py`
- `packages/plugins/codex-collaboration/server/codex_compat.py`

## Files And Responsibilities

Create:

- `docs/diagnostics/2026-05-01-codex-app-server-client-platform-rebaseline-capabilities.md`
  - Human-readable capability/evidence matrix for the selected launcher.
- `docs/diagnostics/codex-app-server-client-platform-rebaseline-capabilities.json`
  - Structured capability/evidence matrix consumed by reviewers and future compatibility work.
- `docs/diagnostics/2026-05-01-codex-app-server-server-request-method-classification.md`
  - Method-by-method server-request classification.
- `docs/diagnostics/codex-app-server-server-request-method-classification.json`
  - Structured method classification record.

Modify:

- `packages/plugins/codex-collaboration/tests/test_approval_router.py`
  - Add 0.128 observed-envelope parser regression and schema-visible unsupported-method parser tests.
- `packages/plugins/codex-collaboration/tests/test_handler_branches_integration.py`
  - Add lifecycle tests only for gaps not already covered by unknown-kind parse-failure and parseable-unknown tests.
- `packages/plugins/codex-collaboration/tests/test_runtime.py`
  - Add regression coverage that live `turn/completed` status remains authoritative over historical `thread/read` status/error fields.
- `docs/tickets/2026-04-29-codex-collaboration-unsupported-server-request-reachability.md`
  - Narrow the ticket after the classification artifact and tests exist.

Do not modify in this plan unless the v128 decision packet selects a branch:

- `packages/plugins/codex-collaboration/server/runtime.py`
- `packages/plugins/codex-collaboration/server/control_plane.py`
- `packages/plugins/codex-collaboration/server/codex_compat.py`
- `packages/plugins/codex-collaboration/tests/fixtures/codex-app-server/`

## Stop Conditions

Stop and save a blocked note instead of continuing if any condition occurs:

- The architecture note is missing or no longer contains the patched live-support boundary.
- Any diagnostic JSON contradicts the markdown packet it accompanies.
- A proposed change would describe untracked artifacts as committed `HEAD` truth.
- A proposed test would require live network, live auth, or a non-scratch `CODEX_HOME`.
- A live probe is needed but the exact scratch home, auth handling, model turn, response policy, and redaction rules are not written first.
- A server-request method is treated as live-supported without `live_envelope_evidence`, lossless parser preservation of shape-critical fields, and a response-compatibility contract.
- Response semantics are treated as live-supported without `live_response_evidence` or an explicit narrower non-response contract.
- The v128 permission branch is still undecided and an implementation step would change execution sandbox or permission payloads.
- Any durable artifact contains an unredacted token-looking value, email address, auth URL, login ID, user code, account identifier, cookie, bearer header, or operator-home credential path outside explicit negated safety prose.

## Commit Boundaries

Use these commit groups when executing this plan:

1. Evidence and capability records.
2. Server-request parser/lifecycle tests plus method-classification artifacts.
3. `thread/read` recovery-boundary tests and docs.
4. Ticket narrowing and current-state references.
5. v128 decision-packet result or blocked handoff to a branch-specific implementation plan.

Do not mix branch-specific v128 sandbox implementation with commits 1-4.

Before commit group 1, make one source-evidence commit that includes the architecture notes, probe diagnostics, probe plans, and this implementation plan. Derived capability/classification artifacts must not cite uncommitted source evidence.

## Task 0: Preflight And Evidence Consistency

**Files:**

- Read: `docs/architecture/2026-05-01-codex-app-server-current-client-platform-rebaseline.md`
- Read: all four `docs/diagnostics/codex-app-server-*.json` files listed above
- Read: `docs/tickets/2026-04-29-codex-collaboration-unsupported-server-request-reachability.md`

- [ ] Confirm worktree state.

Run:

```bash
git status --short --branch
```

Expected:

- Branch is `feature/codex-app-server-client-platform-exploration`.
- Existing evidence files are untracked.
- No unrelated tracked modifications are mixed into this worktree.

- [ ] Run redaction validation over source evidence before staging it.

Run:

```bash
rg -n --pcre2 "(gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{10,}|Bearer\s+[A-Za-z0-9._~+/=-]{20,}|(?i)(authorization|set-cookie|cookie):\s*[^\s]+|https?://[^\s\"]*(auth|oauth|login|token)[^\s\"]*|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|/Users/[^\s\"]+/(\.codex|\.config|\.ssh|Library/Application Support)[^\s\"]*)" docs/architecture/2026-05-01-codex-app-server-current-client-platform-rebaseline.md docs/architecture/2026-05-01-codex-app-server-v128-permission-architecture-implications.md docs/diagnostics/2026-05-01-codex-app-server-client-platform-exploration.md docs/diagnostics/codex-app-server-client-platform-exploration.json docs/diagnostics/2026-05-01-codex-app-server-scratch-home-runtime-probes.md docs/diagnostics/codex-app-server-scratch-home-runtime-probes.json docs/diagnostics/2026-05-01-codex-app-server-materialized-thread-and-server-request-probes.md docs/diagnostics/codex-app-server-materialized-thread-and-server-request-probes.json docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md docs/diagnostics/codex-app-server-server-request-envelope-probes.json docs/plans/2026-05-01-codex-app-server-client-platform-exploration-plan.md docs/plans/2026-05-01-codex-app-server-scratch-home-runtime-probe-plan.md docs/plans/2026-05-01-codex-app-server-materialized-thread-and-server-request-probe-plan.md docs/plans/2026-05-01-codex-app-server-server-request-envelope-probe-plan.md docs/plans/2026-05-01-codex-app-server-v128-execution-sandbox-migration-plan.md docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md
```

Expected:

- Review every match from this command before staging. Matches are allowed only when they are source-plan safety boundaries, redaction detector patterns, or explicit negated evidence saying operator-home credential material was not used, copied, or referenced.
- The currently allowed source-evidence match categories are:
  - the scratch-home runtime packet line that forbids referencing the operator Codex home;
  - the server-request envelope packet line that forbids copying operator-home credentials;
  - the scratch-home runtime JSON note that says no operator Codex home evidence was referenced;
  - probe-plan safety, stop-condition, or checklist lines that name the operator Codex home only as a forbidden or negated path;
  - probe-plan redaction-command lines that contain literal detector patterns for bearer headers, access-token names, or auth URLs.
- If any match contains an actual token, auth URL, cookie/header value, email address, account identifier, or non-negated operator-home credential path, stop and redact or classify it before the source-evidence commit. Do not commit source evidence before this redaction gate passes.

- [ ] Commit the source evidence bundle before deriving new artifacts.

Run:

```bash
git add docs/architecture/2026-05-01-codex-app-server-current-client-platform-rebaseline.md docs/architecture/2026-05-01-codex-app-server-v128-permission-architecture-implications.md docs/diagnostics/2026-05-01-codex-app-server-client-platform-exploration.md docs/diagnostics/codex-app-server-client-platform-exploration.json docs/diagnostics/2026-05-01-codex-app-server-scratch-home-runtime-probes.md docs/diagnostics/codex-app-server-scratch-home-runtime-probes.json docs/diagnostics/2026-05-01-codex-app-server-materialized-thread-and-server-request-probes.md docs/diagnostics/codex-app-server-materialized-thread-and-server-request-probes.json docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md docs/diagnostics/codex-app-server-server-request-envelope-probes.json docs/plans/2026-05-01-codex-app-server-client-platform-exploration-plan.md docs/plans/2026-05-01-codex-app-server-scratch-home-runtime-probe-plan.md docs/plans/2026-05-01-codex-app-server-materialized-thread-and-server-request-probe-plan.md docs/plans/2026-05-01-codex-app-server-server-request-envelope-probe-plan.md docs/plans/2026-05-01-codex-app-server-v128-execution-sandbox-migration-plan.md docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md
git commit -m "docs: record app-server rebaseline source evidence"
```

Expected:

- The commit includes every architecture, diagnostic, and probe-plan artifact cited by this implementation plan.
- A later checkout of the branch can reproduce the evidence basis for derived capability/classification artifacts.
- No derived capability/classification artifact has been created before this commit.

- [ ] Confirm the architecture note contains the patched server-request boundary.

Run:

```bash
rg -n "live support|live response semantics|fixture-backed tests|not live reachability" docs/architecture/2026-05-01-codex-app-server-current-client-platform-rebaseline.md
```

Expected:

- The note says live support requires live envelope evidence.
- The note says fixture-backed tests do not prove live reachability.

- [ ] Verify JSON evidence values that drive the plan.

Run:

```bash
jq '.observed_server_requests[0] | {method, has_id, threadId_present, turnId_present, itemId_present, schema_visible, local_compatibility}' docs/diagnostics/codex-app-server-server-request-envelope-probes.json
jq '.architecture_spec_readiness_delta' docs/diagnostics/codex-app-server-server-request-envelope-probes.json
jq '.materialized_thread_read.message_shape' docs/diagnostics/codex-app-server-materialized-thread-and-server-request-probes.json
```

Expected:

- Observed method is `item/commandExecution/requestApproval`.
- `has_id`, `threadId_present`, `turnId_present`, `itemId_present`, and `schema_visible` are true.
- `local_compatibility` is `supported` in the probe summary, but this plan must refine that label to decision-shape-lossy because the raw envelope has structured `availableDecisions`.
- Server-request architecture readiness is true only with observed-method scoping.
- Materialized-thread `message_shape` has no recoverable agent output shape.

- [ ] Stop if the expected evidence does not match.

Blocked output path on evidence mismatch:

```text
docs/diagnostics/2026-05-01-codex-app-server-client-platform-rebaseline-blocked.md
```

## Task 1: Add Capability And Evidence Records

**Files:**

- Create: `docs/diagnostics/2026-05-01-codex-app-server-client-platform-rebaseline-capabilities.md`
- Create: `docs/diagnostics/codex-app-server-client-platform-rebaseline-capabilities.json`
- Read: `docs/architecture/2026-05-01-codex-app-server-current-client-platform-rebaseline.md`

- [ ] Create the structured capability JSON.

Write `docs/diagnostics/codex-app-server-client-platform-rebaseline-capabilities.json` with this complete top-level shape:

```json
{
  "artifact_version": 1,
  "created_for": "codex-app-server-client-platform-rebaseline-capabilities",
  "repo_worktree": "/Users/jp/Projects/active/claude-code-tool-dev/.worktrees/feature/codex-app-server-client-platform-exploration",
  "source_architecture_note": "docs/architecture/2026-05-01-codex-app-server-current-client-platform-rebaseline.md",
  "selected_launcher": {
    "kind": "codex app-server",
    "path": "/opt/homebrew/bin/codex",
    "version_output": "codex-cli 0.128.0",
    "binary_sha256": "ff803d4b5c595af19b99c18db6def26539fdf4da23a035ab30809835631e8e4b",
    "standalone_equivalence": "not_proven"
  },
  "launcher_posture": {
    "production_default": "codex app-server",
    "runtime_command_override": "supported_for_tests_and_future_probes",
    "standalone_codex_app_server_equivalence": "not_proven",
    "dual_target_support": "not_claimed",
    "required_before_dual_target_support": [
      "controlled standalone codex-app-server install or download",
      "standalone binary sha256 capture",
      "schema comparison against the selected launcher",
      "runtime handshake comparison against the selected launcher",
      "server-request probe comparison against the selected launcher"
    ]
  },
  "evidence_state": {
    "committed_head_truth": false,
    "scratch_home_isolation_proven": true,
    "server_request_live_envelope_scope": [
      "item/commandExecution/requestApproval"
    ],
    "server_request_live_support_scope": [],
    "server_request_lossy_parser_scope": [
      "item/commandExecution/requestApproval"
    ],
    "server_request_live_response_scope": [],
    "thread_read_materialization": "proven_after_user_message_turn",
    "thread_read_reply_recovery": "not_proven",
    "v128_permission_branch": "undecided"
  },
  "surfaces": [
    {
      "surface": "initialize / initialized",
      "posture": "required",
      "evidence_class": "live_runtime_evidence",
      "status": "live_proven",
      "notes": "Handshake was proven under scratch CODEX_HOME."
    },
    {
      "surface": "item/commandExecution/requestApproval",
      "posture": "live_envelope_observed_parser_kind_supported_decision_shape_lossy",
      "evidence_class": "live_envelope_evidence",
      "status": "live_envelope_observed_decision_shape_lossy_response_unproven",
      "notes": "Reachability and kind mapping are proven. Current parser drops the structured availableDecisions shape and falls back to default string decisions, including decline, while the live envelope offered cancel but not decline. Response semantics are not proven."
    },
    {
      "surface": "item/fileChange/requestApproval",
      "posture": "parser_supported_server_request",
      "evidence_class": "parser_support",
      "status": "live_unobserved",
      "notes": "Local parser maps this method, but this evidence set observed no live envelope."
    },
    {
      "surface": "item/tool/requestUserInput",
      "posture": "parser_supported_server_request",
      "evidence_class": "parser_support",
      "status": "live_unobserved",
      "notes": "Local parser maps this method, but this evidence set observed no live envelope."
    },
    {
      "surface": "thread/read(includeTurns=true)",
      "posture": "required_supplemental_projection",
      "evidence_class": "live_runtime_evidence",
      "status": "materialization_proven_reply_recovery_unproven",
      "notes": "Historical status/error fields must not override live turn/completed notifications."
    }
  ]
}
```

- [ ] Add the human-readable capability packet.

Write `docs/diagnostics/2026-05-01-codex-app-server-client-platform-rebaseline-capabilities.md` with these sections:

```markdown
# Codex App Server Client-Platform Rebaseline Capabilities

**Date:** 2026-05-01
**Status:** current evidence record; not committed HEAD truth until staged and committed
**Selected launcher:** `codex app-server`
**Selected version:** `codex-cli 0.128.0`

## Scope

This packet records the capability and evidence boundaries that implementation tasks must preserve.

## Evidence Classes

| Class | Meaning | Can justify |
|---|---|---|
| `live_runtime_evidence` | A real client request, response, or notification path was observed from the selected launcher | Live runtime behavior for that exact surface and scenario |
| `live_envelope_evidence` | A real server-initiated JSON-RPC request was observed from the selected launcher | Live reachability for that method only |
| `live_response_evidence` | The client sent a response and observed the resulting runtime path | Live response semantics for that method and decision only |
| `parser_support` | Local code parses the envelope into a known `PendingRequestKind` | Parser behavior and fixture-backed handling, not live reachability |
| `fixture_terminalization` | Tests prove the plugin intentionally terminalizes or rejects a synthetic shape | Safe local handling, not live reachability |
| `documented_non_relevance` | The method is schema-visible but documented as outside current collaboration flows | Ticket classification, not runtime support |
| `unobserved_risk` | Schema-visible method with no live evidence and no final non-relevance proof | Must remain visible in docs and tickets |

## Current Capability Matrix

| Surface | Posture | Evidence class | Status |
|---|---|---|---|
| `initialize / initialized` | required | `live_runtime_evidence` | live-proven under scratch `CODEX_HOME` |
| `item/commandExecution/requestApproval` | live envelope observed; parser kind supported; decision shape lossy | `live_envelope_evidence` | live envelope observed; structured `availableDecisions` not preserved; no response sent |
| `item/fileChange/requestApproval` | parser-supported server request | `parser_support` | live-unobserved |
| `item/tool/requestUserInput` | parser-supported server request | `parser_support` | live-unobserved |
| `thread/read(includeTurns=true)` | required supplemental projection | `live_runtime_evidence` | materialization proven; reply recovery unproven |

## Launcher Abstraction Posture

`AppServerRuntimeSession` already accepts an explicit command override for tests or future probes. Production remains scoped to `codex app-server` by default. Standalone `codex-app-server` equivalence requires a separate controlled install/download and schema/runtime comparison before dual-target support is claimed.

## Non-Claims

- Complete Codex App Server 0.128.0 compatibility is not claimed.
- Standalone `codex-app-server` equivalence is not claimed.
- Live response semantics for command approval are not claimed.
- Lossless command-approval parser compatibility is not claimed.
- `thread/read` reply recovery is not claimed.
- The v128 permission branch is not selected.
```

- [ ] Validate the JSON.

Run:

```bash
jq '.' docs/diagnostics/codex-app-server-client-platform-rebaseline-capabilities.json >/dev/null
```

Expected: exit code 0.

- [ ] Scan for overclaims.

Run:

```bash
rg -n "fully compatible|complete 0\\.128|standalone.*equivalent|response semantics.*proven|fallback recovery.*proven|lossless.*command.*supported|command.*supported server request" docs/diagnostics/2026-05-01-codex-app-server-client-platform-rebaseline-capabilities.md docs/diagnostics/codex-app-server-client-platform-rebaseline-capabilities.json
```

Expected: no matches except in explicit non-claim wording.

- [ ] Commit boundary.

Commit message:

```bash
git add docs/diagnostics/2026-05-01-codex-app-server-client-platform-rebaseline-capabilities.md docs/diagnostics/codex-app-server-client-platform-rebaseline-capabilities.json
git commit -m "docs: record app-server rebaseline capabilities"
```

## Task 2: Convert Observed Command Approval Into Parser Regression Coverage

**Files:**

- Modify: `packages/plugins/codex-collaboration/tests/test_approval_router.py`
- Read: `docs/diagnostics/codex-app-server-server-request-envelope-probes.json`

- [ ] Re-read the captured live command-approval envelope before writing the test.

Run:

```bash
jq '.. | objects | select(.method? == "item/commandExecution/requestApproval") | select(.params? and .id? != null) | {id, method, params}' docs/diagnostics/codex-app-server-server-request-envelope-probes.json
```

Expected:

- `id` is an integer.
- `params.availableDecisions` is a mixed list containing `"accept"`, an object with `acceptWithExecpolicyAmendment`, and `"cancel"`.
- `params.commandActions` is a non-empty list with a `type: "unknown"` command action.
- `params.availableDecisions` does not contain `"decline"`.

- [ ] Add a parser regression for the observed 0.128 command-approval envelope.

Normalize ephemeral scratch path values and redacted correlation ids, but keep the shape-critical fields from the observed envelope exact: integer `id`, method, context keys, payload field names, `commandActions` shape, and mixed `availableDecisions` entries. Do not rewrite structured decisions into string enum names.

Append this test to `packages/plugins/codex-collaboration/tests/test_approval_router.py`:

```python
def test_parse_live_0128_command_approval_envelope_documents_lossy_decisions() -> None:
    message = {
        "id": 0,
        "method": "item/commandExecution/requestApproval",
        "params": {
            "availableDecisions": [
                "accept",
                {
                    "acceptWithExecpolicyAmendment": {
                        "execpolicy_amendment": ["touch"],
                    }
                },
                "cancel",
            ],
            "command": "/bin/zsh -lc 'touch server-request-probe.txt'",
            "commandActions": [
                {
                    "command": "touch server-request-probe.txt",
                    "type": "unknown",
                }
            ],
            "cwd": "/private/tmp/codex-app-server-server-request-envelope-probes/workspace",
            "itemId": "item-live-1",
            "proposedExecpolicyAmendment": ["touch"],
            "reason": (
                "Do you want to allow creating server-request-probe.txt in the "
                "current workspace?"
            ),
            "threadId": "thread-live-1",
            "turnId": "turn-live-1",
        },
    }

    request = parse_pending_server_request(
        message,
        runtime_id="runtime-live",
        collaboration_id="collab-live",
    )

    assert request.request_id == "0"
    assert request.raw_request_id == 0
    assert request.wire_request_id == 0
    assert request.kind == "command_approval"
    assert request.codex_thread_id == "thread-live-1"
    assert request.codex_turn_id == "turn-live-1"
    assert request.item_id == "item-live-1"

    live_decisions = message["params"]["availableDecisions"]
    assert "decline" not in live_decisions
    assert request.available_decisions != tuple(live_decisions)
    assert request.available_decisions == (
        "accept",
        "acceptForSession",
        "acceptWithExecpolicyAmendment",
        "applyNetworkPolicyAmendment",
        "decline",
        "cancel",
    )
    assert request.requested_scope == {
        "command": "/bin/zsh -lc 'touch server-request-probe.txt'",
        "commandActions": [
            {
                "command": "touch server-request-probe.txt",
                "type": "unknown",
            }
        ],
        "cwd": "/private/tmp/codex-app-server-server-request-envelope-probes/workspace",
        "proposedExecpolicyAmendment": ["touch"],
        "reason": (
            "Do you want to allow creating server-request-probe.txt in the "
            "current workspace?"
        ),
    }
    assert "availableDecisions" not in request.requested_scope
```

This test intentionally documents current lossy behavior: the parser maps the live method to `kind="command_approval"`, but it does not preserve the structured `availableDecisions` object and instead falls back to the default string decision set. If a worker chooses to make the parser lossless instead, update the parser/model, response mapping, capability classification, and this test together; do not leave the artifact claiming both lossless support and lossy behavior.

- [ ] Run the targeted test and verify it passes.

Run:

```bash
uv run pytest packages/plugins/codex-collaboration/tests/test_approval_router.py::test_parse_live_0128_command_approval_envelope_documents_lossy_decisions -q
```

Expected: one passing test.

- [ ] Run the full approval router test module.

Run:

```bash
uv run pytest packages/plugins/codex-collaboration/tests/test_approval_router.py -q
```

Expected: all tests in the module pass.

## Task 3: Classify Remaining Server-Request Methods Without Claiming Live Support

**Files:**

- Modify: `packages/plugins/codex-collaboration/tests/test_approval_router.py`
- Create: `docs/diagnostics/2026-05-01-codex-app-server-server-request-method-classification.md`
- Create: `docs/diagnostics/codex-app-server-server-request-method-classification.json`
- Read: `docs/tickets/2026-04-29-codex-collaboration-unsupported-server-request-reachability.md`

- [ ] Add parser classification tests for schema-visible methods that are not live-supported.

Do not use malformed synthetic params for negative classifications. Each negative test must start from a minimal fixture-schema-conformant request shape, then assert the local parser boundary: `parse_pending_server_request()` requires repo-owned request context (`itemId`, `threadId`, and a string `turnId`) even when the app-server schema for that method does not.

Add these imports near the top of `packages/plugins/codex-collaboration/tests/test_approval_router.py` if they are not already present:

```python
import json
from pathlib import Path
from typing import Any
```

Append these helper fixtures and tests to `packages/plugins/codex-collaboration/tests/test_approval_router.py`:

```python
def _schema_shaped_unobserved_server_requests() -> dict[str, dict[str, Any]]:
    return {
        "mcpServer/elicitation/request": {
            "id": "req-mcp",
            "method": "mcpServer/elicitation/request",
            "params": {
                "serverName": "example-mcp",
                "threadId": "thread-mcp",
                "message": "Need input",
                "mode": "form",
                "requestedSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
        },
        "item/tool/call": {
            "id": "req-tool-call",
            "method": "item/tool/call",
            "params": {
                "arguments": {},
                "callId": "call-tool",
                "threadId": "thread-tool",
                "tool": "example",
                "turnId": "turn-tool",
            },
        },
        "account/chatgptAuthTokens/refresh": {
            "id": "req-auth-refresh",
            "method": "account/chatgptAuthTokens/refresh",
            "params": {
                "reason": "unauthorized",
            },
        },
        "applyPatchApproval": {
            "id": "req-apply-patch",
            "method": "applyPatchApproval",
            "params": {
                "callId": "call-patch",
                "conversationId": "thread-legacy",
                "fileChanges": {
                    "example.txt": {
                        "type": "add",
                        "content": "example",
                    }
                },
            },
        },
        "execCommandApproval": {
            "id": "req-exec-command",
            "method": "execCommandApproval",
            "params": {
                "callId": "call-exec",
                "command": ["echo", "hello"],
                "conversationId": "thread-legacy",
                "cwd": "/repo/worktree",
                "parsedCmd": [
                    {
                        "cmd": "echo hello",
                        "type": "unknown",
                    }
                ],
            },
        },
    }


def _server_request_params_schema(method: str) -> dict[str, Any]:
    schema_path = (
        Path(__file__).parent
        / "fixtures/codex-app-server/0.117.0/ServerRequest.json"
    )
    schema = json.loads(schema_path.read_text())
    for variant in schema["oneOf"]:
        methods = variant["properties"]["method"]["enum"]
        if method not in methods:
            continue
        ref = variant["properties"]["params"]["$ref"]
        return schema["definitions"][ref.rsplit("/", 1)[-1]]
    raise AssertionError(f"missing schema for method {method!r}")


def _required_keys_for_selected_schema_branch(
    params_schema: dict[str, Any], params: dict[str, Any]
) -> set[str]:
    required = set(params_schema.get("required", ()))
    for branch in params_schema.get("oneOf", ()):
        branch_required = set(branch.get("required", ()))
        if branch_required <= set(params):
            return required | branch_required
    return required


def test_unobserved_negative_fixtures_match_schema_required_keys() -> None:
    for method, message in _schema_shaped_unobserved_server_requests().items():
        params = message["params"]
        params_schema = _server_request_params_schema(method)
        required = _required_keys_for_selected_schema_branch(params_schema, params)

        assert required <= set(params), method


def test_parse_request_user_input_is_parser_supported_but_not_live_proven() -> None:
    message = {
        "id": "req-user-input",
        "method": "item/tool/requestUserInput",
        "params": {
            "itemId": "item-input",
            "threadId": "thread-input",
            "turnId": "turn-input",
            "questions": [],
        },
    }

    request = parse_pending_server_request(
        message,
        runtime_id="runtime-input",
        collaboration_id="collab-input",
    )

    assert request.kind == "request_user_input"
    assert request.available_decisions == ()
    assert request.requested_scope == {"questions": []}


def test_parse_mcp_elicitation_schema_shape_is_unparseable_by_local_parser() -> None:
    message = _schema_shaped_unobserved_server_requests()[
        "mcpServer/elicitation/request"
    ]

    try:
        parse_pending_server_request(
            message,
            runtime_id="runtime-mcp",
            collaboration_id="collab-mcp",
        )
    except RuntimeError as exc:
        assert "missing itemId" in str(exc)
    else:
        raise AssertionError("schema-shaped MCP elicitation should be unparseable")


def test_parse_tool_call_schema_shape_is_unparseable_by_local_parser() -> None:
    message = _schema_shaped_unobserved_server_requests()["item/tool/call"]

    try:
        parse_pending_server_request(
            message,
            runtime_id="runtime-tool",
            collaboration_id="collab-tool",
        )
    except RuntimeError as exc:
        assert "missing itemId" in str(exc)
    else:
        raise AssertionError("schema-shaped tool call should be unparseable")


def test_parse_auth_refresh_schema_shape_is_unparseable_by_local_parser() -> None:
    message = _schema_shaped_unobserved_server_requests()[
        "account/chatgptAuthTokens/refresh"
    ]

    try:
        parse_pending_server_request(
            message,
            runtime_id="runtime-auth-refresh",
            collaboration_id="collab-auth-refresh",
        )
    except RuntimeError as exc:
        assert "missing itemId" in str(exc)
    else:
        raise AssertionError("schema-shaped auth refresh should be unparseable")


def test_parse_legacy_approval_schema_shapes_are_unparseable_by_local_parser() -> None:
    cases = _schema_shaped_unobserved_server_requests()

    for method in ("applyPatchApproval", "execCommandApproval"):
        message = cases[method]

        try:
            parse_pending_server_request(
                message,
                runtime_id="runtime-legacy",
                collaboration_id="collab-legacy",
            )
        except RuntimeError as exc:
            assert "missing itemId" in str(exc)
        else:
            raise AssertionError(f"schema-shaped {method} should be unparseable")
```

- [ ] Run the parser classification tests.

Run:

```bash
uv run pytest packages/plugins/codex-collaboration/tests/test_approval_router.py -q
```

Expected: all tests pass.

- [ ] Verify existing lifecycle tests already cover parse-failure and parseable-unknown terminalization.

Run:

```bash
uv run pytest packages/plugins/codex-collaboration/tests/test_handler_branches_integration.py::test_unknown_kind_parse_failure_terminalizes_unknown packages/plugins/codex-collaboration/tests/test_handler_branches_integration.py::test_unknown_kind_unrecognized_method_lineage_status_is_unknown -q
```

Expected: both tests pass.

- [ ] If either lifecycle test is missing or fails for a reason unrelated to baseline setup, stop and fix lifecycle coverage before writing the classification artifact.

Required lifecycle coverage:

- Parse failure persists a minimal `PendingServerRequest(kind="unknown")`.
- Parse failure terminalizes the job as `unknown`.
- Parseable unknown persists full context where available.
- Parseable unknown terminalizes the job as `unknown` and does not project a parked escalation.

- [ ] Create structured method classification JSON.

Write `docs/diagnostics/codex-app-server-server-request-method-classification.json`:

```json
{
  "artifact_version": 1,
  "created_for": "codex-app-server-server-request-method-classification",
  "source_live_packet": "docs/diagnostics/codex-app-server-server-request-envelope-probes.json",
  "ticket": "docs/tickets/2026-04-29-codex-collaboration-unsupported-server-request-reachability.md",
  "methods": [
    {
      "method": "item/commandExecution/requestApproval",
      "classification": "live_envelope_observed_parser_kind_supported_decision_shape_lossy_response_unproven",
      "evidence_basis": ["live emitted request", "lossy parser behavior test", "code-path analysis"],
      "parser_boundary": "current parser maps the method to command_approval but drops the structured availableDecisions object and falls back to default string decisions, including decline even though the observed live request offered cancel and not decline",
      "ticket_effect": "narrows broad no-live-envelope blocker but does not establish lossless parser compatibility or response compatibility"
    },
    {
      "method": "item/fileChange/requestApproval",
      "classification": "parser_supported_live_unobserved",
      "evidence_basis": ["parser test", "code-path analysis"],
      "ticket_effect": "remains open for live reachability or non-relevance proof"
    },
    {
      "method": "item/tool/requestUserInput",
      "classification": "parser_supported_live_unobserved",
      "evidence_basis": ["parser test", "code-path analysis"],
      "ticket_effect": "remains open for live reachability or non-relevance proof"
    },
    {
      "method": "item/permissions/requestApproval",
      "classification": "parseable_unknown_live_unobserved",
      "evidence_basis": ["parser test", "lifecycle terminalization test", "schema/code-path analysis"],
      "ticket_effect": "remains open for reachability and intended support-vs-terminalization decision"
    },
    {
      "method": "mcpServer/elicitation/request",
      "classification": "schema_conformant_parser_context_mismatch_live_unobserved",
      "evidence_basis": ["parser test", "schema/code-path analysis"],
      "parser_boundary": "fixture schema requires serverName and threadId and permits absent/null turnId; local parser rejects because itemId is absent and support would also need a string turnId strategy",
      "ticket_effect": "remains open for reachability or documented non-relevance proof"
    },
    {
      "method": "item/tool/call",
      "classification": "schema_conformant_parser_context_mismatch_live_unobserved",
      "evidence_basis": ["parser test", "schema/code-path analysis"],
      "parser_boundary": "fixture schema requires arguments, callId, threadId, tool, and turnId; local parser rejects because itemId is absent",
      "ticket_effect": "remains open for reachability or documented non-relevance proof"
    },
    {
      "method": "account/chatgptAuthTokens/refresh",
      "classification": "auth_runtime_surface_live_unobserved",
      "evidence_basis": ["parser test", "schema/code-path analysis"],
      "parser_boundary": "fixture schema requires reason and does not carry itemId, threadId, or turnId; local parser rejects because itemId is absent before auth-refresh semantics can be evaluated",
      "ticket_effect": "remains open unless documented as outside collaboration execution"
    },
    {
      "method": "applyPatchApproval",
      "classification": "legacy_alternate_approval_surface_parser_context_mismatch_live_unobserved",
      "evidence_basis": ["parser test", "schema/code-path analysis"],
      "parser_boundary": "fixture schema uses callId, conversationId, and fileChanges; local parser rejects because itemId is absent before it can map thread or turn context",
      "ticket_effect": "remains open for alternate-surface reachability or non-relevance proof"
    },
    {
      "method": "execCommandApproval",
      "classification": "legacy_alternate_approval_surface_parser_context_mismatch_live_unobserved",
      "evidence_basis": ["parser test", "schema/code-path analysis"],
      "parser_boundary": "fixture schema uses callId, command, conversationId, cwd, and parsedCmd; local parser rejects because itemId is absent before it can map thread or turn context",
      "ticket_effect": "remains open for alternate-surface reachability or non-relevance proof"
    }
  ],
  "global_conclusion": {
    "ready_to_close_ticket": false,
    "ready_to_narrow_ticket": true,
    "live_envelope_methods": ["item/commandExecution/requestApproval"],
    "live_support_methods": [],
    "lossy_parser_methods": ["item/commandExecution/requestApproval"],
    "live_response_methods": []
  }
}
```

- [ ] Create the human-readable method classification packet.

Write `docs/diagnostics/2026-05-01-codex-app-server-server-request-method-classification.md` with:

```markdown
# Codex App Server Server-Request Method Classification

**Date:** 2026-05-01
**Status:** classification packet; not ticket closure

## Scope

This packet narrows `T-20260429-02` after one live command-approval envelope was observed.

## Classification Rules

- Live support requires live envelope evidence, lossless parser preservation of shape-critical fields, and a response-compatibility contract.
- Live response semantics require a live response path or an explicit non-response contract.
- A method with live envelope evidence is not "supported" if the parser drops shape-critical request semantics.
- Parser tests prove parser behavior only.
- Fixture-backed lifecycle tests prove intentional local handling only.

## Method Table

| Method | Classification | Evidence basis | Ticket effect |
|---|---|---|---|
| `item/commandExecution/requestApproval` | live envelope observed; parser kind supported; structured decision shape lossy; response unproven | live emitted request, lossy parser behavior test, code-path analysis | narrows broad no-live-envelope blocker but does not establish lossless parser compatibility or response compatibility |
| `item/fileChange/requestApproval` | parser-supported; live-unobserved | parser test, code-path analysis | remains open for live reachability or non-relevance proof |
| `item/tool/requestUserInput` | parser-supported; live-unobserved | parser test, code-path analysis | remains open for live reachability or non-relevance proof |
| `item/permissions/requestApproval` | parseable unknown; live-unobserved | parser test, lifecycle terminalization test, schema/code-path analysis | remains open for reachability and intended support-vs-terminalization decision |
| `mcpServer/elicitation/request` | schema-conformant request rejected by local parser context requirements; live-unobserved | parser test, schema/code-path analysis | remains open for reachability or documented non-relevance proof |
| `item/tool/call` | schema-conformant request rejected by local parser context requirements; live-unobserved | parser test, schema/code-path analysis | remains open for reachability or documented non-relevance proof |
| `account/chatgptAuthTokens/refresh` | auth/runtime surface; schema-conformant request rejected by local parser context requirements; live-unobserved | parser test, schema/code-path analysis | remains open unless documented as outside collaboration execution |
| `applyPatchApproval` | legacy alternate approval surface; schema-conformant request rejected by local parser context requirements; live-unobserved | parser test, schema/code-path analysis | remains open for alternate-surface reachability or non-relevance proof |
| `execCommandApproval` | legacy alternate approval surface; schema-conformant request rejected by local parser context requirements; live-unobserved | parser test, schema/code-path analysis | remains open for alternate-surface reachability or non-relevance proof |

## Parser-Context Mismatch Rows

The `mcpServer/elicitation/request`, `item/tool/call`, `applyPatchApproval`, and `execCommandApproval` parser tests must not be summarized as generic malformed-message rejection. They use minimal fixture-schema-conformant params and prove only the local parser boundary:

- `mcpServer/elicitation/request`: fixture params include `serverName`, `threadId`, `message`, `mode`, and `requestedSchema`; local parsing rejects first on missing plugin `itemId`, and any future support also needs an explicit strategy for optional or nullable `turnId`.
- `item/tool/call`: fixture params include `arguments`, `callId`, `threadId`, `tool`, and `turnId`; local parsing rejects on missing plugin `itemId`.
- `account/chatgptAuthTokens/refresh`: fixture params include `reason`; local parsing rejects on missing plugin `itemId` before auth-refresh semantics can be evaluated.
- `applyPatchApproval`: fixture params include `callId`, `conversationId`, and `fileChanges`; local parsing rejects on missing plugin `itemId` before it can map thread or turn context.
- `execCommandApproval`: fixture params include `callId`, `command`, `conversationId`, `cwd`, and `parsedCmd`; local parsing rejects on missing plugin `itemId` before it can map thread or turn context.

## Command Approval Decision-Shape Boundary

The observed `item/commandExecution/requestApproval` envelope offered these decisions:

```json
[
  "accept",
  {
    "acceptWithExecpolicyAmendment": {
      "execpolicy_amendment": ["touch"]
    }
  },
  "cancel"
]
```

Current `approval_router.py` only preserves `availableDecisions` when every entry is a string. For the observed mixed list, it falls back to the default command decision tuple, which includes `decline`. Current `delegation_controller.py` maps deny to `{"decision": "decline"}` for command approval. Because the live request offered `cancel` but not `decline`, response compatibility is not established and command approval must remain classified as lossy until a lossless parser/response branch is implemented and exercised.

## Ticket Effect

`T-20260429-02` should remain open. It should narrow from "no live server-request evidence" to "only command approval has live envelope evidence, and current command-approval handling is parser-kind compatible but decision-shape lossy; remaining schema-visible methods require method-by-method reachability, terminalization, response semantics, or non-relevance proof."
```

- [ ] Validate JSON and scan for overclaims.

Run:

```bash
jq '.' docs/diagnostics/codex-app-server-server-request-method-classification.json >/dev/null
rg -n "ready_to_close_ticket\": true|fully compatible|live support.*fileChange|live support.*requestUserInput|response semantics.*proven|lossless.*command.*supported|command.*supported server request" docs/diagnostics/2026-05-01-codex-app-server-server-request-method-classification.md docs/diagnostics/codex-app-server-server-request-method-classification.json
```

Expected:

- `jq` succeeds.
- No overclaim matches.

- [ ] Commit boundary.

Commit message:

```bash
git add packages/plugins/codex-collaboration/tests/test_approval_router.py packages/plugins/codex-collaboration/tests/test_handler_branches_integration.py docs/diagnostics/2026-05-01-codex-app-server-server-request-method-classification.md docs/diagnostics/codex-app-server-server-request-method-classification.json
git commit -m "test: classify app-server server requests"
```

If `test_handler_branches_integration.py` was not modified because existing lifecycle tests were sufficient, omit it from `git add`.

## Task 4: Preserve The `thread/read` Recovery Boundary

**Files:**

- Modify: `packages/plugins/codex-collaboration/tests/test_runtime.py`
- Read: `packages/plugins/codex-collaboration/server/runtime.py`
- Read: `packages/plugins/codex-collaboration/server/turn_extraction.py`

- [ ] Add a regression that execution turns do not use `thread/read` fallback on failed terminal status.

Append this test near the existing `run_execution_turn` and fallback tests in `packages/plugins/codex-collaboration/tests/test_runtime.py`:

```python
def test_execution_failed_turn_does_not_use_thread_read_fallback(
    fake_server_process: FakeServerProcess,
) -> None:
    fake_server_process.queue_response(
        "turn/start",
        {"turn": {"id": "t1", "status": "inProgress", "items": []}},
    )
    fake_server_process.queue_response(
        "thread/read",
        {
            "thread": {
                "id": "thr-1",
                "turns": [
                    {
                        "id": "t1",
                        "status": "completed",
                        "error": None,
                        "agentMessage": "historical projection should not be used",
                    }
                ],
            }
        },
    )
    fake_server_process.queue_notification(
        "turn/completed",
        {
            "threadId": "thr-1",
            "turnId": "t1",
            "turn": {
                "id": "t1",
                "status": "failed",
                "error": {"message": "backend auth failed"},
                "items": [],
            },
        },
    )
    session = AppServerRuntimeSession(repo_root=Path("/repo"))
    session._client = fake_server_process.client  # type: ignore[assignment]

    result = session.run_execution_turn(
        thread_id="thr-1",
        prompt_text="do work",
        sandbox_policy={"type": "workspaceWrite"},
        approval_policy="on-request",
    )

    assert result.status == "failed"
    assert result.agent_message == ""
    assert ("thread/read", {"threadId": "thr-1", "includeTurns": True}) not in fake_server_process.requests
```

- [ ] Add a regression that advisory fallback does not overwrite live terminal status.

Append:

```python
def test_advisory_fallback_does_not_replace_live_terminal_status(
    fake_server_process: FakeServerProcess,
) -> None:
    session = _setup_advisory_session_no_item_completed(fake_server_process)
    fake_server_process.queue_response(
        "thread/read",
        {
            "thread": {
                "id": "thr-1",
                "turns": [
                    {
                        "id": "t1",
                        "status": "failed",
                        "error": {"message": "historical status disagrees"},
                        "agentMessage": FALLBACK_AGENT_TEXT,
                    }
                ],
            }
        },
    )

    result = session.run_advisory_turn(
        thread_id="thr-1",
        prompt_text="test",
        output_schema={},
    )

    assert result.status == "completed"
    assert result.agent_message == FALLBACK_AGENT_TEXT
```

- [ ] Run targeted runtime tests.

Run:

```bash
uv run pytest packages/plugins/codex-collaboration/tests/test_runtime.py::test_execution_failed_turn_does_not_use_thread_read_fallback packages/plugins/codex-collaboration/tests/test_runtime.py::test_advisory_fallback_does_not_replace_live_terminal_status -q
```

Expected: both tests pass.

- [ ] Run all runtime tests.

Run:

```bash
uv run pytest packages/plugins/codex-collaboration/tests/test_runtime.py -q
```

Expected: all runtime tests pass.

- [ ] Commit boundary.

Commit message:

```bash
git add packages/plugins/codex-collaboration/tests/test_runtime.py
git commit -m "test: preserve thread read recovery boundary"
```

## Task 5: Narrow `T-20260429-02` Without Closing It

**Files:**

- Modify: `docs/tickets/2026-04-29-codex-collaboration-unsupported-server-request-reachability.md`
- Read: `docs/diagnostics/2026-05-01-codex-app-server-server-request-method-classification.md`
- Read: `docs/diagnostics/codex-app-server-server-request-method-classification.json`

- [ ] Read the ticket frontmatter directly.

Run:

```bash
sed -n '1,120p' docs/tickets/2026-04-29-codex-collaboration-unsupported-server-request-reachability.md
```

Expected:

- `status: open`
- `priority: high`

- [ ] Add a current evidence update after the existing Context section.

Add this subsection:

```markdown
## Current Evidence Update: 2026-05-01

The 2026-05-01 server-request envelope probe observed one live schema-visible server request:

- `item/commandExecution/requestApproval`

That observed envelope included JSON-RPC `id`, `itemId`, `threadId`, `turnId`, and a mixed `availableDecisions` list with a structured `acceptWithExecpolicyAmendment` object. `approval_router.py` maps the method to `kind="command_approval"`, but current parsing is decision-shape lossy: it does not preserve the structured decision object and falls back to default string decisions.

This narrows the original blocker from "no live server-request evidence" to "only command approval has live envelope evidence, with lossy local decision handling." It does not close this ticket because:

- no live response path was exercised for command approval;
- the observed command-approval request offered `cancel` but not `decline`, while current denial response mapping emits `{"decision": "decline"}`;
- `item/fileChange/requestApproval` remains parser-supported but live-unobserved;
- `item/tool/requestUserInput` remains parser-supported but live-unobserved;
- `item/permissions/requestApproval` remains parseable as `unknown` unless future work supports it intentionally;
- `mcpServer/elicitation/request`, `item/tool/call`, `account/chatgptAuthTokens/refresh`, `applyPatchApproval`, and `execCommandApproval` still require reachability, terminalization, or non-relevance proof.

Evidence:

- `docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md`
- `docs/diagnostics/codex-app-server-server-request-envelope-probes.json`
- `docs/diagnostics/2026-05-01-codex-app-server-server-request-method-classification.md`
- `docs/diagnostics/codex-app-server-server-request-method-classification.json`
```

- [ ] Update the acceptance criteria only if the wording still implies zero live evidence for every method.

Preserve:

- `status: open`
- method-by-method classification requirement
- observed-envelope regression coverage requirement
- evidence-basis requirement

- [ ] Verify the ticket is narrowed, not closed.

Run:

```bash
sed -n '1,180p' docs/tickets/2026-04-29-codex-collaboration-unsupported-server-request-reachability.md
rg -n "status: open|ready to close|closed|command approval has live envelope evidence|decision-shape lossy|does not close" docs/tickets/2026-04-29-codex-collaboration-unsupported-server-request-reachability.md
```

Expected:

- Frontmatter still says `status: open`.
- New prose says command approval has live envelope evidence.
- New prose says command-approval decision handling is lossy.
- New prose says the ticket is not closed.

- [ ] Commit boundary.

Commit message:

```bash
git add docs/tickets/2026-04-29-codex-collaboration-unsupported-server-request-reachability.md
git commit -m "docs: narrow unsupported server request ticket"
```

## Task 6: Keep Launcher Abstraction Narrow

**Files:**

- Read: `packages/plugins/codex-collaboration/server/runtime.py`
- Read: `docs/diagnostics/2026-05-01-codex-app-server-client-platform-exploration.md`
- Verify or modify the Task 1 launcher posture text: `docs/diagnostics/2026-05-01-codex-app-server-client-platform-rebaseline-capabilities.md`
- Verify or modify the Task 1 `launcher_posture` JSON object: `docs/diagnostics/codex-app-server-client-platform-rebaseline-capabilities.json`

- [ ] Verify current runtime already accepts a command override.

Run:

```bash
rg -n "def __init__\\(|command: list\\[str\\]|command or \\[\"codex\", \"app-server\"\\]" packages/plugins/codex-collaboration/server/runtime.py
```

Expected:

- `AppServerRuntimeSession.__init__` has `command: list[str] | None = None`.
- It defaults to `["codex", "app-server"]`.

- [ ] Do not add standalone launcher support in this plan.

Verify this Markdown section from Task 1 is present in the capability packet:

```markdown
## Launcher Abstraction Posture

`AppServerRuntimeSession` already accepts an explicit command override for tests or future probes. Production remains scoped to `codex app-server` by default. Standalone `codex-app-server` equivalence requires a separate controlled install/download and schema/runtime comparison before dual-target support is claimed.
```

Ensure the capability JSON still contains exactly this top-level launcher posture object from Task 1. Do not invent a second JSON field in Task 6.

```json
"launcher_posture": {
  "production_default": "codex app-server",
  "runtime_command_override": "supported_for_tests_and_future_probes",
  "standalone_codex_app_server_equivalence": "not_proven",
  "dual_target_support": "not_claimed",
  "required_before_dual_target_support": [
    "controlled standalone codex-app-server install or download",
    "standalone binary sha256 capture",
    "schema comparison against the selected launcher",
    "runtime handshake comparison against the selected launcher",
    "server-request probe comparison against the selected launcher"
  ]
}
```

- [ ] Verify no production default changed.

Run:

```bash
git diff -- packages/plugins/codex-collaboration/server/runtime.py
```

Expected: no diff from this task.

- [ ] Commit boundary.

Commit message if capability files changed:

```bash
git add docs/diagnostics/2026-05-01-codex-app-server-client-platform-rebaseline-capabilities.md docs/diagnostics/codex-app-server-client-platform-rebaseline-capabilities.json
git commit -m "docs: keep app-server launcher target bounded"
```

If no files changed, record "Task 6 verified no code change" in the execution notes.

## Task 7: Consume Or Block On The v128 Permission Branch Decision

**Files:**

- Read: `docs/plans/2026-05-01-codex-app-server-v128-execution-sandbox-migration-plan.md`
- Read: `docs/architecture/2026-05-01-codex-app-server-v128-permission-architecture-implications.md`
- Consume if already present: `docs/diagnostics/codex-app-server-v128-schema-runtime-decision.json`
- Create if decision packet is absent: `docs/diagnostics/2026-05-01-codex-app-server-v128-permission-decision-required.md`
- Create only if the decision packet already exists and selects a branch: branch-specific implementation plan path named by the decision result

- [ ] Confirm prior rebaseline tasks are committed before entering this gate.

Run:

```bash
git status --short -- docs/diagnostics/2026-05-01-codex-app-server-client-platform-rebaseline-capabilities.md docs/diagnostics/codex-app-server-client-platform-rebaseline-capabilities.json docs/diagnostics/2026-05-01-codex-app-server-server-request-method-classification.md docs/diagnostics/codex-app-server-server-request-method-classification.json packages/plugins/codex-collaboration/tests/test_approval_router.py packages/plugins/codex-collaboration/tests/test_runtime.py docs/tickets/2026-04-29-codex-collaboration-unsupported-server-request-reachability.md
```

Expected: no output.

If this command prints any file, stop Task 7 and commit or deliberately block the prior work first. Do not context-switch into v128 permission planning with uncommitted rebaseline artifacts.

- [ ] Check whether the decision packet already exists.

Run:

```bash
if test -f docs/diagnostics/codex-app-server-v128-schema-runtime-decision.json; then
  jq '.decision // .selected_branch // .branch' docs/diagnostics/codex-app-server-v128-schema-runtime-decision.json
else
  printf '%s\n' 'decision_packet_absent'
fi
```

Expected:

- If the file exists, it names a selected branch or a blocked outcome.
- If the file does not exist, the command prints `decision_packet_absent` and exits 0; this task then creates a blocked handoff instead of executing another plan inline.
- Any nonzero exit from this command means the decision packet exists but could not be read or parsed, or the shell command itself failed. Stop and classify that as an execution blocker before continuing.

- [ ] If the decision packet does not exist, create a blocked handoff and stop.

Write `docs/diagnostics/2026-05-01-codex-app-server-v128-permission-decision-required.md`:

```markdown
# Codex App Server v128 Permission Decision Required

**Date:** 2026-05-01
**Status:** blocked handoff; do not implement permission migration from this plan

## Blocker

`docs/diagnostics/codex-app-server-v128-schema-runtime-decision.json` does not exist, so this rebaseline implementation plan cannot choose a v128 permission implementation branch.

## Why It Blocks Progress

The rebaseline work intentionally separates current live-envelope/parser evidence from v128 permission migration. Implementing sandbox or permission payload changes without the decision packet would collapse branch selection, runtime isolation, and config/trust provenance into this plan.

## Required Next Work

Execute `docs/plans/2026-05-01-codex-app-server-v128-execution-sandbox-migration-plan.md` in a separate clean step, then resume this plan only after the decision packet exists and prior rebaseline artifacts remain committed.
```

- [ ] Commit the blocked handoff if created.

Run:

```bash
git add docs/diagnostics/2026-05-01-codex-app-server-v128-permission-decision-required.md
git commit -m "docs: block v128 permission branch pending decision"
```

Expected: the commit contains only the blocked handoff file.

- [ ] If the decision packet exists, consume it under these hard rules:

- Use scratch `CODEX_HOME` or an explicit non-durable trust/config strategy.
- Record stable and experimental schema provenance from the same launcher used for runtime probes.
- Record `experimentalApi` negotiation if experimental fields are used.
- Record active/effective permission provenance from thread-level responses or a documented alternate source.
- Do not copy, read, hash, or serialize operator credential material.

- [ ] If the decision packet selects Branch A3, write a child implementation plan for stable `sandboxPolicy`.

Suggested path:

```text
docs/plans/2026-05-01-codex-app-server-v128-stable-sandbox-policy-implementation-plan.md
```

Required scope:

- update `build_workspace_write_sandbox_policy()`;
- update `packages/plugins/codex-collaboration/tests/test_runtime.py`;
- preserve PR #127 / T-20260429-01 support-root and denial invariants;
- prove current smoke and credential-boundary behavior.

- [ ] If the decision packet selects Branch A1, write a child implementation plan for experimental request-level `permissions`.

Suggested path:

```text
docs/plans/2026-05-01-codex-app-server-v128-experimental-permissions-implementation-plan.md
```

Required scope:

- add `experimentalApi` initialization support;
- decide whether permission selection belongs on execution `thread/start`, `turn/start`, or both;
- expose permission mode in runtime APIs without overloading `sandbox_policy`;
- test profile provenance and fallback behavior.

- [ ] If the decision packet selects Branch A2, write a child implementation plan for config-level default permissions.

Suggested path:

```text
docs/plans/2026-05-01-codex-app-server-v128-config-permissions-implementation-plan.md
```

Required scope:

- define config/Codex-home isolation;
- define user-defined profile generation or operator setup;
- preserve support-root read-only behavior without making support roots writable;
- document failure modes and operator guidance.

- [ ] If the decision packet selects Branch B, C, or D, stop normal implementation.

Required output:

```text
docs/diagnostics/2026-05-01-codex-app-server-v128-permission-branch-blocked.md
```

The blocked artifact must name:

- selected branch or blocked outcome;
- reason normal implementation cannot proceed;
- exact decision-packet evidence;
- whether `/delegate` should remain enabled, gated, or disabled for 0.128.

## Task 8: Verification Sweep

**Files:**

- All files changed by Tasks 1-7.

- [ ] Run targeted unit tests.

Run:

```bash
uv run pytest packages/plugins/codex-collaboration/tests/test_approval_router.py packages/plugins/codex-collaboration/tests/test_runtime.py -q
```

Expected: all selected tests pass.

- [ ] Run lifecycle tests touched by server-request classification.

Run:

```bash
uv run pytest packages/plugins/codex-collaboration/tests/test_handler_branches_integration.py::test_unknown_kind_parse_failure_terminalizes_unknown packages/plugins/codex-collaboration/tests/test_handler_branches_integration.py::test_unknown_kind_unrecognized_method_lineage_status_is_unknown packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py::test_e2e_command_approval_produces_escalation packages/plugins/codex-collaboration/tests/test_delegate_start_integration.py::test_e2e_unknown_request_kind_interrupts_and_escalates -q
```

Expected: all selected tests pass.

- [ ] Run docs/data validation.

Scope the overclaim scan to artifacts this plan creates or edits. Do not scan all of `docs/architecture` or all of `docs/diagnostics`; older diagnostics and bounded architecture language can contain intentionally skeptical or non-claim matches.

Run:

```bash
jq '.' docs/diagnostics/codex-app-server-client-platform-rebaseline-capabilities.json >/dev/null
jq '.' docs/diagnostics/codex-app-server-server-request-method-classification.json >/dev/null
rg -n "fully compatible|complete 0\\.128|ready_to_close_ticket\": true|standalone.*equivalent|fallback recovery.*proven|response semantics.*proven|lossless.*command.*supported|command.*supported server request" docs/diagnostics/2026-05-01-codex-app-server-client-platform-rebaseline-capabilities.md docs/diagnostics/codex-app-server-client-platform-rebaseline-capabilities.json docs/diagnostics/2026-05-01-codex-app-server-server-request-method-classification.md docs/diagnostics/codex-app-server-server-request-method-classification.json docs/tickets/2026-04-29-codex-collaboration-unsupported-server-request-reachability.md
```

Expected:

- Both JSON files parse.
- Overclaim scan has no matches except explicit non-claims or "not ready" language in the files this plan created or edited.

- [ ] Run redaction validation over created or modified documentation artifacts.

Run:

```bash
rg -n --pcre2 "(gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{10,}|Bearer\\s+[A-Za-z0-9._~+/=-]{20,}|(?i)(authorization|set-cookie|cookie):\\s*[^\\s]+|https?://[^\\s\\\"]*(auth|oauth|login|token)[^\\s\\\"]*|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}|/Users/[^\\s\\\"]+/(\\.codex|\\.config|\\.ssh|Library/Application Support)[^\\s\\\"]*)" docs/architecture/2026-05-01-codex-app-server-current-client-platform-rebaseline.md docs/architecture/2026-05-01-codex-app-server-v128-permission-architecture-implications.md docs/diagnostics/2026-05-01-codex-app-server-client-platform-exploration.md docs/diagnostics/codex-app-server-client-platform-exploration.json docs/diagnostics/2026-05-01-codex-app-server-scratch-home-runtime-probes.md docs/diagnostics/codex-app-server-scratch-home-runtime-probes.json docs/diagnostics/2026-05-01-codex-app-server-materialized-thread-and-server-request-probes.md docs/diagnostics/codex-app-server-materialized-thread-and-server-request-probes.json docs/diagnostics/2026-05-01-codex-app-server-server-request-envelope-probes.md docs/diagnostics/codex-app-server-server-request-envelope-probes.json docs/diagnostics/2026-05-01-codex-app-server-client-platform-rebaseline-capabilities.md docs/diagnostics/codex-app-server-client-platform-rebaseline-capabilities.json docs/diagnostics/2026-05-01-codex-app-server-server-request-method-classification.md docs/diagnostics/codex-app-server-server-request-method-classification.json docs/plans/2026-05-01-codex-app-server-client-platform-rebaseline-implementation-plan.md docs/tickets/2026-04-29-codex-collaboration-unsupported-server-request-reachability.md
```

Expected:

- No matches except explicit negated safety prose that says operator-home credential material was not used, copied, or referenced.
- The currently allowed negated matches are:
  - the scratch-home runtime packet line that forbids referencing the operator Codex home;
  - the server-request envelope packet line that forbids copying operator-home credentials;
  - the scratch-home runtime JSON note that says no operator Codex home evidence was referenced.
- If there are any other matches, stop and redact or classify them before committing.

- [ ] Run formatting or lint only if Python files changed beyond tests.

Run:

```bash
ruff check packages/plugins/codex-collaboration/server packages/plugins/codex-collaboration/tests
```

Expected: no new lint failures.

- [ ] Record baseline-vs-branch truth in final notes.

Required final summary wording:

- "The branch adds evidence records and regression coverage."
- "It does not claim complete 0.128 compatibility."
- "It does not close `T-20260429-02`."
- "It does not implement v128 permission migration unless the decision packet selected a branch and a child plan was executed."

- [ ] Verify final git status after all required commits.

Run:

```bash
git status --short --branch
```

Expected:

- No untracked source evidence, derived diagnostics, implementation plan, or modified test/ticket files remain.
- Any remaining output is unrelated pre-existing work explicitly listed in the final notes.

## Final Acceptance

This plan is complete only when:

- source architecture, probe diagnostics, probe plans, and this implementation plan are committed before derived artifacts;
- capability/evidence artifacts exist and parse;
- server-request parser tests pass;
- lifecycle tests prove parse-failure and parseable-unknown terminalization remain intentional;
- `thread/read` tests prove live terminal status remains authoritative;
- `T-20260429-02` is narrowed but still open;
- standalone launcher equivalence remains unclaimed;
- v128 permission migration is either blocked in a committed handoff because the decision packet is absent or handed to a branch-specific implementation plan because the decision packet already existed;
- every changed file is staged and committed in the relevant commit boundary.
