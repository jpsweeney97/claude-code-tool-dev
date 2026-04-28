# Codex-Collaboration Next Focus Assessment

Date: 2026-04-28

Repo state investigated: `main` at merge commit `36ef13e8`

Citation scope: repo line citations reflect `main` at `36ef13e8`. If line
numbers drift, resolve them against that commit. Operational handoff citations
under `/Users/jp/.codex/handoffs/...` are machine-local evidence only and are not
reproducible for future readers on a different machine.

## Executive Finding

Recommended next focus:

**Execute T-20260423-01 Phase 1 / Phase 2 diagnostics for live delegated
execution.**

T-20260423-01 already specifies the diagnostic-first plan. This report is not a
replacement plan. Its contribution is a delta layer:

- separate engineering work from ticket hygiene;
- add operational detail for the sandbox probes and diagnostic run record;
- add the missing `approval_policy="untrusted"` interpretation branch;
- audit whether T-20260423-02 can be closed as parallel hygiene after PR #126;
- make external evidence limits explicit.

Parallel hygiene recommendation:

**Close or update T-20260423-02 with a resolution note for PR #126 only after
recording the scope audit below.**

That ticket-file update is not an operational precondition for T-01. T-02's
`blocks: [T-20260423-01]` field is useful ticket-graph metadata, but nothing in
the repo or runtime prevents starting T-01 diagnostics today. T-01 itself has
`blocked_by: []` and is open (`docs/tickets/2026-04-23-codex-collaboration-delegate-execution-remediation.md:3-11`).

## Premise Boundaries

PR #126 is merged. `gh pr view 126` reports state `MERGED`, merged at
`2026-04-28T03:07:17Z`, with merge commit
`36ef13e823f8c684f78d08787c7498bcbf5c332b`.

T-01 remains the parent live delegate remediation ticket. It says the T-07 smoke
proved the infrastructure path but actual artifact-producing execution is still
blocked by shell execution and approval behavior
(`docs/tickets/2026-04-23-codex-collaboration-delegate-execution-remediation.md:14-25`).
T-02 also says it does not resolve T-01 on its own
(`docs/tickets/2026-04-23-deferred-same-turn-approval-response.md:35-46`).

T-01 already says diagnostics precede implementation. Its sandbox diagnostic
gate asks what `includePlatformDefaults: True` grants, whether the security
boundary holds, and whether a narrower readable-root grant is sufficient
(`docs/tickets/2026-04-23-codex-collaboration-delegate-execution-remediation.md:65-90`).
Its implementation sequence already splits Phase 1 sandbox diagnostics and
Phase 2 approval diagnostics, and says they can run in parallel
(`docs/tickets/2026-04-23-codex-collaboration-delegate-execution-remediation.md:226-238`).

T-01 also already flags the approval-policy interaction: even if the sandbox can
execute shell commands, execution turns currently default to
`approval_policy="untrusted"`, so App Server may still emit
`command_approval` / `file_change` requests regardless of sandbox readability
(`docs/tickets/2026-04-23-codex-collaboration-delegate-execution-remediation.md:179-205`).
Current code still has that default at
`packages/plugins/codex-collaboration/server/delegation_controller.py:361-390`.

## Ranked Candidates

1. **Engineering: execute T-01 diagnostic Phase 1 / Phase 2.**
   This is the strongest next focus because the sandbox blocker still exists in
   live code and artifact-producing delegated execution is still the current
   product gap.

2. **Parallel hygiene: close or update T-02 after scope audit.**
   PR #126 appears to cover T-02's in-scope Packet 1 obligations, but this is a
   bookkeeping action. It should not be phrased as "unblocking" T-01 in an
   operational sense.

3. **Conditional follow-up: controller approval-policy decision.**
   If sandbox execution works but every shell command still escalates under
   `approval_policy="untrusted"`, the next decision is a controller policy
   change or an explicit reason to keep untrusted behavior.

4. **Conditional follow-up: amendment admission / Packet 2.**
   T-02 explicitly leaves exec-policy amendment admission out of scope. This
   becomes immediate only if live App Server behavior requires an amendment
   response such as `acceptWithExecpolicyAmendment`.

5. **Deferred polish: RT.1 and TT.1 typing cleanup.**
   Useful cleanup, but not the live delegated-execution blocker.

6. **Separate older product defect: T-20260416-01 dialogue reply extraction.**
   Real and still open, but not the current `/delegate` execution blocker.

## What This Adds To T-01

T-01 already owns the diagnostic plan. The deltas below are the only additions
this assessment recommends carrying into the next run record or implementation
plan.

| Delta | Why it matters |
|---|---|
| Pair every sensitive-path sandbox probe with an out-of-sandbox baseline. | `test -r ~/.ssh/id_rsa` returning 1 is ambiguous unless the file is known to exist. |
| Record exact policy variant and approval-policy value per run. | Sandbox readability and approval escalation are independent mechanisms. |
| Add an interpretation branch for "artifacts produced, but every shell command escalates." | That outcome points at `approval_policy`, not sandbox or amendment admission. |
| Treat capture-ready / registry failures as Packet 1 regressions, not sandbox evidence. | PR #126 specifically changed the capture-ready handshake; failures there should not be misattributed. |
| Make amendment-admission tracking concrete. | "Preserve the trail" is not actionable without a ticket or explicit closure note. |

## Recommended Sequence

### A. Engineering Path

1. Create or switch to a feature branch first, for example
   `feature/delegate-execution-remediation`, from `main` at `36ef13e8` or a
   later synced commit. The repo's PreToolUse branch-protection hook blocks
   edits on `main`, so diagnostic run records must not be written on `main`
   (`.claude/rules/workflow/git.md:1-24`).
2. If running from a later commit, refresh the line anchors in this assessment
   before using them as executable evidence. Start with:

   ```bash
   git log --oneline -1 -- packages/plugins/codex-collaboration/server/delegation_controller.py
   git log --oneline -1 -- packages/plugins/codex-collaboration/server/runtime.py
   git log --oneline -1 -- docs/tickets/2026-04-23-codex-collaboration-delegate-execution-remediation.md
   git log --oneline -1 -- docs/tickets/2026-04-23-deferred-same-turn-approval-response.md
   ```

   If any cited file changed after `36ef13e8`, re-anchor by symbol search
   (`rg -n "<symbol-or-heading>" <file>`) and line-number print
   (`nl -ba <file> | sed -n '<start>,<end>p'`) before treating the citation as
   current. Repeat the same check for any other cited file behind a claim the
   operator intends to rely on.
3. Run T-01 Phase 1 / Phase 2 diagnostics and record observations before
   changing production code.
4. Do not commit a sandbox policy patch until the
   diagnostic record answers T-01's three sandbox questions and the approval API
   observation questions.
5. Convert the diagnostic result into a scoped implementation plan only after
   the live observations are known.

### B. Parallel Hygiene Path

1. Close or update T-20260423-02 with a PR #126 resolution note only after
   preserving the audit result in this report or in the ticket.
2. Do not describe the T-02 edit as a prerequisite to starting T-01.
3. If no successor ticket exists for amendment admission, file one explicitly:
   `T-YYYYMMDD-NN: Amendment admission for delegated execution`, with
   `blocked_by: []`, and reference T-02's out-of-scope clause
   (`docs/tickets/2026-04-23-deferred-same-turn-approval-response.md:68-73`).
4. If the owner wants amendment admission to remain conditional rather than a
   live ticket, close T-02 with that condition stated plainly.

## Diagnostic Run Contract

### Preconditions

- Working live `codex` CLI available to the operator.
- Local repo synced to `main` at `36ef13e8` or later.
- Dedicated feature branch or disposable worktree selected before any run
  record is written.
- Run-record artifact target selected, preferably
  `docs/diagnostics/2026-MM-DD-delegate-execution-diagnostic.md`.
- Smoke output path selected deliberately:
  - use `docs/diagnostics/delegate-smoke/<timestamp>-result.txt` when the goal
    is a tracked artifact-production proof;
  - use `.tmp/delegate-smoke/<timestamp>/probe.txt` only for ignored write probes
    that should not appear in `full.diff`.
- Cleanup policy recorded. `scratch/` is not ignored by the current `.gitignore`;
  do not use it unless the smoke output is intentionally tracked. After copying
  necessary evidence into the run record, remove ignored probe output with
  `trash <path>`. For tracked smoke output, either retain it as evidence or
  trash it before final commit and preserve the relevant diff / poll excerpt in
  the run record.

### Preflight Metadata

Record:

- `git status --short --branch`
- `git rev-parse --short HEAD`
- `codex --version`
- raw App Server identity from the `initialize()` handshake if available; the
  wrapper stores the implementation-defined value as `RuntimeHandshake.user_agent`
  (`packages/plugins/codex-collaboration/server/runtime.py:58-76`)
- vendored fixture directory:
  `packages/plugins/codex-collaboration/tests/fixtures/codex-app-server/0.117.0/`
- sandbox policy variant under test
- approval policy under test
- target workspace/worktree and branch

If `codex --version` does not expose the App Server version separately, record
that limitation and preserve the raw runtime `user_agent` or CLI log line that
was actually observable. Do not treat `user_agent` as a semantic version unless
its raw value clearly carries one.

### Policy Variants

Run the same tiny artifact-producing objective under each relevant policy
variant. This is T-01's plan, with the observation grid made explicit.

| Variant | Purpose |
|---|---|
| Baseline | Current policy: `includePlatformDefaults: False`. Expected to preserve the known shell failure. |
| Candidate A | `includePlatformDefaults: True`. Tests whether App Server's platform defaults are safe and sufficient. |
| Candidate B | Narrow readable-root additions only, if Candidate A works but grants a wider boundary than desired. |

Current code still serializes the baseline policy with `readableRoots` limited
to the worktree, `includePlatformDefaults: False`, `networkAccess: False`, and
tmp exclusions enabled
(`packages/plugins/codex-collaboration/server/runtime.py:23-38`).

### Probe Baselines

For every sensitive-path probe, first record a host-side baseline that does not
read file contents.

Example host-side baseline:

```bash
for p in "$HOME/.ssh/id_rsa" "$HOME/.aws/credentials" "$HOME/.config"; do
  test -e "$p"; echo "$p exists=$?"
  test -r "$p"; echo "$p readable=$?"
done
```

Then run equivalent `test -e` / `test -r` checks inside the delegated turn. If a
path is absent on the host, an in-sandbox `test -r` failure is non-diagnostic;
select another existing local control path or record the absence.

Minimum probe set:

- shell/runtime availability: `test -x /bin/sh`, `test -x /usr/bin/env`;
- expected scoped write: create the smoke file under the delegated worktree;
- host secrets not readable: existing paths under `~/.ssh/`, `~/.aws/`, and
  `~/.config/` without reading contents;
- unrelated repo/worktree not readable, using a known sibling worktree path if
  one exists;
- network unavailable with `networkAccess: False`, for example:

```bash
curl --max-time 2 --silent --show-error https://example.com >/dev/null
```

If `curl` itself is unavailable under the candidate policy, record that as a
tool-availability result rather than a network-policy result.

### Smoke Objective

Use one objective that is simple enough to inspect:

> Create `docs/diagnostics/delegate-smoke/<timestamp>-result.txt` in the
> delegated worktree using shell commands, write a short fixed string, verify
> the file exists, print its contents, then stop.

The objective must cause at least three shell-visible actions (`mkdir`, write,
verify/read) before branches 2 or 3 below can be selected. If the live agent
compresses the objective into fewer observed shell actions, rerun with a more
explicit objective before interpreting approval-request volume. Because the
agent may choose different command grouping across runs, record the observed
action list and do not compare approval ratios across runs without comparing
the action count too.

For each run, capture:

- shell action count;
- command stdout/stderr and exit status;
- raw server-request payloads;
- JSON-RPC wire ID type for the first parked request;
- response payload sent by `decide(approve)`;
- job status transitions;
- `full.diff`, `changed_files`, artifact hash, and `poll()` output;
- number and kinds of approval requests produced.

## Approval Observation Branches

Interpret live results with these branches.

Before choosing branch 2 or branch 3, compute:

- `shell_action_count`: shell commands or file-change actions attempted by the
  agent for the smoke objective;
- `approval_request_count`: `command_approval` plus `file_change` server requests
  emitted for that objective.

Use the ratio only after `shell_action_count >= 3`.

The `0.5` ratio below is a provisional early-warning threshold, not a calibrated
constant. Recalibrate it after the first baseline run records
`approval_request_count` for known-failing shell actions. If the baseline ratio
is typically near one approval request per shell action under
`approval_policy="untrusted"`, tighten the threshold before using it for
repeated branch selection, for example by raising it from `0.5` to `0.8`.

| Observation | Next decision |
|---|---|
| Shell execution remains blocked even under Candidate A. | Continue App Server sandbox investigation; do not patch approval logic yet. |
| `accept` resumes the action, artifacts are produced, and `approval_request_count <= 1` with no same-action re-escalation. | Implement the narrow sandbox policy patch plus regression tests. |
| `accept` resumes the action and artifacts are produced, but `approval_request_count > shell_action_count * 0.5`, or an approved same action immediately re-escalates. | Decide whether execution turns should continue defaulting to `approval_policy="untrusted"`; this is distinct from sandbox readability and amendment admission. |
| App Server requests or requires amendment-specific response data. | Open or activate Packet 2 / amendment admission before claiming T-01 remediated. |
| Capture-ready, worker, registry, or post-decide polling fails independently of sandbox permissions. | Triage as a Packet 1 regression, starting with the capture-ready path changed in PR #126. |

The third branch is required because the controller still defaults execution
turns to `approval_policy="untrusted"`
(`packages/plugins/codex-collaboration/server/delegation_controller.py:361-390`)
and passes that policy into App Server turn execution
(`packages/plugins/codex-collaboration/server/delegation_controller.py:1323-1329`,
`packages/plugins/codex-collaboration/server/runtime.py:209-217`). A successful
sandbox change may therefore still leave delegated execution noisy or unusable
until the approval policy decision is made.

Layer split: `AppServerRuntimeSession.run_execution_turn()` has a wrapper
default of `"on-request"` (`packages/plugins/codex-collaboration/server/runtime.py:160-183`),
and lower-level `_run_turn()` defaults to `"never"`
(`packages/plugins/codex-collaboration/server/runtime.py:194-217`). Advisory
turns explicitly pass `"never"`
(`packages/plugins/codex-collaboration/server/runtime.py:140-158`). Production
delegated execution is different: it passes the controller's `_approval_policy`,
whose default is `"untrusted"`
(`packages/plugins/codex-collaboration/server/delegation_controller.py:1323-1329`,
`packages/plugins/codex-collaboration/server/delegation_controller.py:361-390`).
If a debugger sees `"never"` or `"on-request"` in `runtime.py`, treat that as a
runtime-layer default; the live delegated-execution default comes from the
controller. The advisory-side `"never"` path is intentionally separate from
this T-01 delegated-execution diagnostic, but it is the same kind of layer split
to keep in mind when debugging consult/dialogue flows.

### Symptom Attribution Rules

Use these recognition rules before assigning a smoke result to one branch:

| Symptom | Likely attribution |
|---|---|
| Shell command result shows sandbox/read failure, missing platform binary access, or exit `-1`, and no successful approval dispatch occurs. | T-01 sandbox blocker. Continue policy-variant diagnostics. |
| `start()` waits roughly `START_OUTCOME_WAIT_SECONDS` and returns a running job, then a later `poll()` surfaces the escalation/completion. | Slow-but-valid worker; not a Packet 1 regression by itself. |
| `start()` returns `StartWaitElapsed` / running, raw server-request evidence exists, and later `poll()` never surfaces the parked request. | Suspect capture-ready / registry signaling regression. Inspect `open_capture_channel`, `announce_parked`, and `wait_for_parked` paths. |
| `decide()` returns `decision_accepted=True`, an immediate `poll()` briefly shows the same pending request, and a later poll advances. | Expected consuming window; not a failure and not evidence of sandbox trouble. |
| The same request remains pending after the delegate skill's bounded post-decide polling window, or a manual-MCP repeat decide returns `request_already_decided` while worker state does not advance. | Suspect registry / worker-drain issue. Search direct debug output for `request_already_decided`, then inspect registry reservation and worker wake/drain paths. |
| Job terminalizes `unknown` after `session.respond(...)` and the persisted request shows `dispatch_result="failed"` with non-null `dispatch_error`, or audit contains `action="dispatch_failed"`. | Packet 1 dispatch/recovery path, not sandbox readability. The stable recognition surface is the pending-request store / audit record, not a human log string. |
| Request payload contains `proposedExecpolicyAmendment` or requires `acceptWithExecpolicyAmendment` to proceed. | Amendment-admission branch. |

## T-02 Closure Audit

T-02's in-scope list is at
`docs/tickets/2026-04-23-deferred-same-turn-approval-response.md:48-66`.
The merged Packet 1 implementation covers most in-scope items and leaves a
timeout-coordination caveat that should be preserved if T-02 is closed or
updated as hygiene. This audit is not proof that T-01 is remediated.

This is an authorial audit in a recommendation document. Before a durable T-02
closure commit, a second reviewer should re-read the eight T-02 in-scope items
against the cited code/doc regions, with special attention to rows 5 and 7.
If no second reviewer is available, do a delayed self-review after a 24-hour
cooling-off period and record the self-review timestamp in the closure note.
Checklist for each row: verify every cited file/range still exists, verify the
prose claim is directly supported by the cited code or doc text, and downgrade
the row if either check fails.

| T-02 in-scope item | Audit result after PR #126 |
|---|---|
| 1. `codex.delegate.start` lifecycle while original turn is live | Covered. `start()` now pre-opens the capture channel, spawns a worker, waits for capture-ready outcome, then dispatches the start return shape (`packages/plugins/codex-collaboration/server/delegation_controller.py:735-774`). |
| 2. Background / live-turn ownership | Covered. Packet 1 architecture assigns each deferred-approval turn to a worker thread with exclusive session ownership (`docs/plans/2026-04-24-packet-1-deferred-approval-response.md:9-19`). |
| 3. Capture cardinality model | Covered. The handler now records every parkable server request and tracks the most recent request for finalizer mapping (`packages/plugins/codex-collaboration/server/delegation_controller.py:1048-1076`). |
| 4. Blocking resolution registry | Covered. `ResolutionRegistry` owns per-request wait/decide channels and per-job capture-ready channels (`packages/plugins/codex-collaboration/server/resolution_registry.py:1-15`), while `decide()` reserves and commits the request signal (`packages/plugins/codex-collaboration/server/delegation_controller.py:2678-2728`). |
| 5. Persisted request / job mutation model | Covered. New durable fields land in `PendingServerRequest` and `DelegationJob`; mutators are `PendingRequestStore.mark_resolved`, `record_response_dispatch`, `record_protocol_echo`, `record_timeout`, `record_dispatch_failure`, and `record_internal_abort`; parked-request selection is `DelegationJobStore.update_parked_request()`. Citations: `packages/plugins/codex-collaboration/server/models.py:285-330`, `:415-436`; `packages/plugins/codex-collaboration/server/pending_request_store.py:71-211`; `packages/plugins/codex-collaboration/server/delegation_job_store.py:187-202`; park path `packages/plugins/codex-collaboration/server/delegation_controller.py:1059-1076`; recovery `packages/plugins/codex-collaboration/server/delegation_controller.py:2881-2910`. |
| 6. Public contract updates | Covered. `contracts.md` documents post-Packet-1 async `decide()`, pending escalation projection, `canceled` status, and discard admissibility (`docs/superpowers/specs/codex-collaboration/contracts.md:269-273`, `:327-337`, `:352-354`, `:401-407`). |
| 7. Timeout alignment | Partially covered. Repo code sets the operator window to 900 seconds and the synchronous start-outcome wait to 30 seconds (`packages/plugins/codex-collaboration/server/delegation_controller.py:116-117`), while runtime request / notification defaults are 1200 seconds (`packages/plugins/codex-collaboration/server/runtime.py:49`, `:233`). However, the design spec explicitly says the true server-request timeout is external and unknown, and that the 900s default is conservative product policy rather than repo-authoritative transport derivation (`docs/superpowers/specs/2026-04-23-deferred-approval-response-design.md:2226-2241`, `:2426-2428`). Closure should preserve that caveat instead of claiming fully encoded timeout coordination. |
| 8. Recovery semantics for blocked approval paths | Covered. Startup recovery closes unresolved approval-resolution records and marks orphaned running / needs-escalation jobs unknown; terminal catch-up includes `canceled` and repairs active canceled handles (`packages/plugins/codex-collaboration/server/delegation_controller.py:2814-2910`, `:3051-3107`). |

Recommended ticket-hygiene wording:

> Close T-20260423-02 as the PR #126 Packet 1 control-plane rewrite, conditional
> on accepting the timeout-alignment caveat recorded in the closure audit. Scope
> audit covers rows 1-6 and 8 as repo-covered; row 7 is numerically consistent
> in repo code but depends on an external App Server server-request timeout that
> the repo cannot prove. This closure does not claim T-20260423-01 is remediated:
> sandbox execution and approval-policy behavior remain live diagnostic work
> under T-20260423-01. Exec-policy amendment admission remains out of scope and
> conditional on live App Server behavior. Audit cross-check: <second reviewer
> and date, or delayed self-review timestamp>.

Do not rely on the machine-local handoff archive as the only closure proof. If
gate counts from the final PR review are useful, paste them into the ticket
resolution or PR closeout text; a future agent on another machine cannot verify
`/Users/jp/.codex/handoffs/...` paths.

## Current Code Evidence

The sandbox blocker is still live. `build_workspace_write_sandbox_policy()`
still sets:

- `readOnlyAccess.type = "restricted"`;
- `readableRoots = [worktree]`;
- `includePlatformDefaults = False`;
- `networkAccess = False`;
- `/tmp` exclusions enabled.

Evidence: `packages/plugins/codex-collaboration/server/runtime.py:23-38`.

Packet 1 changed the old approval-loop mechanism. The post-PR126 shape is:

- `start()` pre-registers a capture-ready channel before `spawn_worker(...)`
  (`packages/plugins/codex-collaboration/server/delegation_controller.py:735-774`);
- parkable requests are durably recorded and block on the registry
  (`packages/plugins/codex-collaboration/server/delegation_controller.py:1048-1076`);
- `decide()` builds a bare App Server payload, writes durable intent, commits
  the registry signal, and returns accepted-for-dispatch
  (`packages/plugins/codex-collaboration/server/delegation_controller.py:2656-2765`);
- approve on `command_approval` / `file_change` maps to
  `{"decision": "accept"}`, deny maps to `{"decision": "decline"}`
  (`packages/plugins/codex-collaboration/server/delegation_controller.py:2767-2809`);
- the worker responds through `session.respond(parsed.wire_request_id,
  response_payload)`, preserving the original JSON-RPC wire ID type
  (`packages/plugins/codex-collaboration/server/delegation_controller.py:1193-1230`).

So the old static "cancel then prompt a new turn" approval defect is no longer
the current design shape. The remaining question is live App Server behavior
once shell execution is possible and while `approval_policy="untrusted"` remains
the default.

## Not Recommended As The Next Main Focus

Do not start by rebuilding analytics/review/cutover. T-07 is closed and the
cutover happened.

Do not start with RT.1/TT.1 unless the selected goal is pure typing polish. They
are useful cleanup but do not unblock live delegated artifact production.

Do not implement amendment admission before the sandbox/approval diagnostic
unless the project owner explicitly chooses that lane. Packet 1 supplies the
delayed response mechanism; the next evidence needed is what live App Server
requires once shell execution is possible.

Do not reopen the benchmark aggregate-scoring path. T-04 closed as
demonstrated-not-scored, and the remaining extraction mismatch is tracked
separately.

## Decision Needed

Engineering decision:

Proceed with **T-01 Phase 1 / Phase 2 diagnostics**, using the delta contract
above.

Independent hygiene action:

Close or update T-02 when convenient, after the audit is second-checked and the
timeout / amendment-admission caveats are included. If no second reviewer is
available, use the delayed self-review checklist above and record the timestamp.

No ticket edit is required before the engineering diagnostic can begin.
