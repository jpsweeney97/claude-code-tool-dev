# T-01 Delegate Execution Diagnostic Run Record

Date: 2026-04-28

Status: draft first-run record, not yet executed

Decision artifact:
`docs/assessments/2026-04-28-codex-collaboration-next-focus-report.md`

Primary ticket: `T-20260423-01`

Related hygiene ticket: `T-20260423-02`

Merge-commit anchor for the assessment: `36ef13e8`

## Quick Reference

1. Work from a feature branch or disposable worktree, not `main`.
2. Run citation-freshness checks before relying on assessment line anchors.
3. Resolve runtime storage paths for this session.
4. Capture preflight metadata and the cleanup decision before starting.
5. Run the same tiny artifact-producing objective under each required policy variant.
6. Record shell action count, approval request count, artifacts, storage rows,
   and branch decision per variant.
7. Apply the branch precedence rule before choosing the next engineering action.
8. Record threshold recalibration here, not in the assessment.
9. Preserve only the run evidence needed for review; remove ignored probe output
   with `trash <path>`.

## Run Identity

| Field | Value |
|---|---|
| Operator | jpsweeney97 |
| Date/time started | 2026-04-28T04:56:25Z |
| Branch/worktree | `feature/delegate-execution-diagnostic-record` at `/Users/jp/Projects/active/claude-code-tool-dev` |
| `git status --short --branch` | `## feature/delegate-execution-diagnostic-record...origin/feature/delegate-execution-diagnostic-record` (clean for diagnostic-relevant paths; 8 unrelated `docs/tickets/closed-tickets/` moves carry over from a prior session and are out of scope) |
| `git rev-parse --short HEAD` | `46cd954e` (run-record commit on top of merge anchor `36ef13e8`) |
| `codex --version` | `codex-cli 0.125.0` (raw observable; no separate App Server version exposed; do not infer a semantic App Server version from this string) |
| Raw App Server identity / `RuntimeHandshake.user_agent` | Pending live bootstrap; record the literal value emitted by the App Server during the first handshake of this run |
| Fixture directory | `packages/plugins/codex-collaboration/tests/fixtures/codex-app-server/0.117.0/` |
| Target workspace/worktree | `/Users/jp/Projects/active/claude-code-tool-dev` (this repository; the delegated job will create its own worktree under the plugin data root — see Runtime Storage Reference) |
| Diagnostic smoke timestamp | `20260428T005625` (UTC, derived from session-start time; reuse this token for `docs/diagnostics/delegate-smoke/<timestamp>-result.txt`) |

If `codex --version` does not expose an App Server version separately, record the
raw observable value and do not infer a semantic version from it.

**Version-delta note:** Live `codex-cli` reports `0.125.0`, but the only fixture
present under `tests/fixtures/codex-app-server/` is `0.117.0/`. This is a known
mismatch, not yet a defect. If the live App Server's request/response shapes
diverge from the `0.117.0` fixture during the run, record the divergence rather
than treating the fixture as authoritative.

## Citation Freshness

Run before using line citations from the assessment as current evidence:

```bash
git log --oneline -1 -- packages/plugins/codex-collaboration/server/delegation_controller.py
git log --oneline -1 -- packages/plugins/codex-collaboration/server/runtime.py
git log --oneline -1 -- docs/tickets/2026-04-23-codex-collaboration-delegate-execution-remediation.md
git log --oneline -1 -- docs/tickets/2026-04-23-deferred-same-turn-approval-response.md
```

Ancestry rule: a citation is fresh if its last-touch commit is an ancestor of
`36ef13e8`. Verify with
`git merge-base --is-ancestor <last-touch-commit> 36ef13e8`.

| File | Last-touch commit | Re-anchor needed? | Notes |
|---|---:|---|---|
| `packages/plugins/codex-collaboration/server/delegation_controller.py` | `702499b0` | No | Ancestor of `36ef13e8` (PR #126 commit). Assessment line citations into this file remain valid. |
| `packages/plugins/codex-collaboration/server/runtime.py` | `667ed20e` | No | Ancestor of `36ef13e8` (T-20260423-02 Task 16 rewrite). Method-layering line anchors at `:23-38`, `:140-217`, `:166`, `:202` confirmed against this commit's tree. |
| `docs/tickets/2026-04-23-codex-collaboration-delegate-execution-remediation.md` | `82121adf` | No | Ancestor of `36ef13e8`. Ticket file unchanged since creation. |
| `docs/tickets/2026-04-23-deferred-same-turn-approval-response.md` | `41b4c1aa` | No | Ancestor of `36ef13e8`. Ticket file unchanged since creation. |
| Other cited file used during execution | TBD | TBD | Append rows here for any additional file cited during the live run (e.g., `journal.py`, `pending_request_store.py`); rerun the ancestry check before relying on the citation. |

All four primary citations resolved fresh against the merge anchor; no
re-anchoring required for the assessment's existing line ranges.

If a cited file changed after `36ef13e8`, re-anchor by symbol search and
line-number print before relying on the citation:

```bash
rg -n "<symbol-or-heading>" <file>
nl -ba <file> | sed -n '<start>,<end>p'
```

## Runtime Storage Reference

The plugin data root is `CLAUDE_PLUGIN_DATA` when set; otherwise the code falls
back to `/tmp/codex-collaboration` (`server/journal.py:23-33`). The session id is
read from `<plugin_data>/session_id` by
`packages/plugins/codex-collaboration/scripts/codex_runtime_bootstrap.py`.

```bash
PLUGIN_DATA="${CLAUDE_PLUGIN_DATA:-/tmp/codex-collaboration}"
SESSION_ID="$(cat "$PLUGIN_DATA/session_id")"
printf 'plugin_data=%s\nsession_id=%s\n' "$PLUGIN_DATA" "$SESSION_ID"
```

Record the paths used for this run. `CLAUDE_PLUGIN_DATA` is unset in the operator
environment, so the resolved root is the fallback `/tmp/codex-collaboration`.
Pre-execution, the root does not yet exist on disk — it is created by the App
Server bootstrap during the first delegated session. `<SESSION_ID>` and
`<JOB_ID>` placeholders are filled once the live session and a delegation job
are observable.

| Artifact | Path |
|---|---|
| Plugin data root | `/tmp/codex-collaboration` (fallback; `CLAUDE_PLUGIN_DATA` unset) |
| Session id file | `/tmp/codex-collaboration/session_id` (does not yet exist; written by `scripts/codex_runtime_bootstrap.py:48` on first bootstrap) |
| PendingRequestStore | `/tmp/codex-collaboration/pending_requests/<SESSION_ID>/requests.jsonl` |
| DelegationJobStore | `/tmp/codex-collaboration/delegation_jobs/<SESSION_ID>/jobs.jsonl` |
| OperationJournal | `/tmp/codex-collaboration/journal/operations/<SESSION_ID>.jsonl` |
| Audit events | `/tmp/codex-collaboration/audit/events.jsonl` (global, not session-scoped) |
| Delegation worktree root | `/tmp/codex-collaboration/runtimes/delegation/<JOB_ID>/worktree` |
| Delegation inspection artifacts | `/tmp/codex-collaboration/runtimes/delegation/<JOB_ID>/inspection` |

Once the App Server bootstraps the session, replay this lookup to capture the
live `<SESSION_ID>`:

```bash
PLUGIN_DATA="${CLAUDE_PLUGIN_DATA:-/tmp/codex-collaboration}"
SESSION_ID="$(cat "$PLUGIN_DATA/session_id")"
printf 'plugin_data=%s\nsession_id=%s\n' "$PLUGIN_DATA" "$SESSION_ID"
```

Then add the resolved literal `<SESSION_ID>` and (per variant) `<JOB_ID>` to a
follow-up table inside each variant's evidence block, and update Attempt
history's Preserved evidence column with the matching JSONL line numbers.

Use these read-only lookup commands after a job id and request id are known:

```bash
tail -n 80 "$PLUGIN_DATA/pending_requests/$SESSION_ID/requests.jsonl"
tail -n 80 "$PLUGIN_DATA/delegation_jobs/$SESSION_ID/jobs.jsonl"
tail -n 120 "$PLUGIN_DATA/journal/operations/$SESSION_ID.jsonl"
tail -n 80 "$PLUGIN_DATA/audit/events.jsonl"
```

For long sessions, prefer job/request scoped lookup over `tail`:

```bash
grep -n "<job_id>" "$PLUGIN_DATA/delegation_jobs/$SESSION_ID/jobs.jsonl"
grep -n "<job_id>" "$PLUGIN_DATA/journal/operations/$SESSION_ID.jsonl"
grep -n "<request_id>" "$PLUGIN_DATA/pending_requests/$SESSION_ID/requests.jsonl"
grep -n "<request_id>" "$PLUGIN_DATA/audit/events.jsonl"
```

Stable forensic fields to look for:

| Question | Storage evidence |
|---|---|
| Did dispatch to App Server fail after `decide()`? | Pending request row with `dispatch_result="failed"` and non-null `dispatch_error`; audit row with `action="dispatch_failed"` if present. |
| Did a repeat manual decide lose the race? | Direct tool response with `reason="request_already_decided"`. |
| Did the worker clear the parked request? | Delegation job row where `parked_request_id` becomes `null`. |
| Did recovery close an unresolved approval operation? | Operation journal `approval_resolution` row with `phase="completed"` and `completion_origin="recovered_unresolved"`. |

## Host-Side Probe Baselines

Record host-side existence/readability only. Do not print sensitive file
contents.

```bash
for p in "$HOME/.ssh/id_rsa" "$HOME/.aws/credentials" "$HOME/.config"; do
  test -e "$p"; echo "$p exists=$?"
  test -r "$p"; echo "$p readable=$?"
done
```

| Path | Host exists? | Host readable? | In-sandbox exists? | In-sandbox readable? | Diagnostic interpretation |
|---|---:|---:|---:|---:|---|
| `$HOME/.ssh/id_rsa` | TBD | TBD | TBD | TBD | TBD |
| `$HOME/.aws/credentials` | TBD | TBD | TBD | TBD | TBD |
| `$HOME/.config` | TBD | TBD | TBD | TBD | TBD |
| Known sibling repo/worktree | TBD | TBD | TBD | TBD | TBD |

If a sensitive path is absent on the host, an in-sandbox unreadable result is
non-diagnostic. Pick another existing control path or record the absence.

## Smoke Objective

Use this objective for every variant unless a rerun is needed because the live
agent compressed the shell work into fewer than three shell-visible actions.

> Create `docs/diagnostics/delegate-smoke/<timestamp>-result.txt` in the
> delegated worktree using shell commands, write the exact string
> `delegate execution smoke`, verify the file exists, print its contents, then
> stop.

Expected minimum shell-visible actions:

1. Create parent directory.
2. Write fixed string.
3. Verify/read the file.

Chosen smoke path:
`docs/diagnostics/delegate-smoke/TBD-result.txt`

Capture all required evidence into this run record before cleanup. Cleanup can
remove smoke files and ignored probes, so treat cleanup commands as destructive.

Cleanup decision:

| Artifact | Keep in commit? | Cleanup action | Evidence preserved in this run record |
|---|---|---|---|
| Tracked smoke output | TBD | TBD | TBD |
| Ignored `.tmp` probe output | No | `trash <path>` after evidence capture | TBD |

## Policy Variants

| Variant | Sandbox policy | Approval policy | Expected use |
|---|---|---|---|
| Baseline | Current code: `includePlatformDefaults: False`, worktree-only readable root, `networkAccess: False` | Controller default, expected `untrusted` | Required. Preserve known shell failure and measure approval-request baseline if possible. |
| Candidate A | `includePlatformDefaults: True`, otherwise current policy | Same approval policy as baseline unless explicitly changed | Required unless Baseline unexpectedly produces complete artifact evidence. Tests whether platform defaults unblock shell while preserving security boundary. |
| Candidate B | Narrow readable-root additions only | Same approval policy as baseline unless explicitly changed | Conditional. Run only if Candidate A works but grants wider read access than desired. |

## Per-Variant Evidence

Copy this block once per variant. If the variant needs a rerun, append another
attempt under "Attempt history" instead of overwriting the failed or compressed
attempt.

### Variant: TBD

| Field | Source / fill guidance | Observation |
|---|---|---|
| Policy diff / patch under test | Required. Local code/config diff or explicit "current code". | TBD |
| Approval policy value | Required. Controller/runtime input for this run. | TBD |
| Job id | Required. `start()` response, `poll()` output, or `DelegationJobStore` row. | TBD |
| First parked request id | Required if any escalation occurs. `start()` pending escalation, `poll()` pending escalation, or PendingRequestStore row. | TBD |
| JSON-RPC wire id type | Required if a parked request exists. PendingRequestStore `raw_request_id` type or raw server-request payload `id` type. | TBD |
| `shell_action_count` | Required. Count shell commands/file-change actions attempted for the smoke objective; attach action list in raw excerpts. | TBD |
| `approval_request_count` | Required if `shell_action_count >= 3`. Count `command_approval` plus `file_change` server requests for this variant. | TBD |
| Approval request kinds | Required if requests occur. Raw server-request payloads or PendingRequestStore `kind`. | TBD |
| `approval_request_count / shell_action_count` | Required if denominator is nonzero; otherwise record `no signal`. | TBD |
| Command stdout/stderr summary | Required. Tool result or run transcript. | TBD |
| Exit statuses | Required. Tool result or run transcript. | TBD |
| `decide(approve)` response payload | Required if approval requested. Tool response from `decide`. | TBD |
| `poll()` transitions | Required. Timed `poll()` outputs after start and after decide if applicable. | TBD |
| `full.diff` summary | Required if artifact production succeeds. `poll()` or inspection output. | TBD |
| `changed_files` | Required if artifact production succeeds. `poll()` or inspection output. | TBD |
| Artifact hash | Required if artifact production succeeds. Hash of smoke file or artifact metadata. | TBD |
| PendingRequestStore rows inspected | Required if any request id exists. Record request id and matching JSONL line numbers. | TBD |
| DelegationJobStore rows inspected | Required. Record job id and matching JSONL line numbers. | TBD |
| OperationJournal rows inspected | Required. Record job/request id and matching JSONL line numbers. | TBD |
| Audit rows inspected | Required if dispatch failure, timeout, or decision audit is relevant; otherwise record "not applicable". | TBD |
| Network probe result | Required for candidate policy variants. Record command and result. | TBD |
| Sensitive-path probe result | Required for candidate policy variants. Cross-reference Host-Side Probe Baselines. | TBD |
| Sibling-worktree probe result | Required if a sibling worktree exists; otherwise record absence. | TBD |
| Cleanup performed | Required after evidence capture. Record command or "deferred". | TBD |

Attempt history:

| Attempt | Reason started | Shell-visible actions | Outcome | Preserved evidence |
|---:|---|---:|---|---|
| 1 | Initial run | TBD | TBD | TBD |

Raw excerpts:

```text
TBD
```

## Threshold Calibration

The assessment's `0.5` approval ratio is a provisional early-warning threshold,
not a calibrated constant. Do not edit the assessment during this run. Record
the observed baseline here and select the threshold used for this diagnostic.

| Metric | Value |
|---|---:|
| Baseline `shell_action_count` | TBD |
| Baseline `approval_request_count` | TBD |
| Baseline ratio | TBD |
| Threshold used for branch selection | TBD |
| Rationale for threshold | TBD |

Recalibration rule for this run:

- If baseline ratio is near one approval request per shell action, treat noisy
  approval behavior as expected under `approval_policy="untrusted"` and use a
  higher threshold for repeated comparisons.
- If baseline ratio is materially below one, keep the lower early-warning
  threshold and record why it still separates bounded from noisy escalation.
- If Baseline produces no shell signal because sandbox blocks before any
  command/approval behavior is observable, record `no signal` for Baseline and
  calibrate from Candidate A's first successful baseline-equivalent run instead.
- Always record the actual action list; do not compare ratios across runs unless
  the action counts and command grouping are comparable.

## Branch Precedence

Multiple observations may fire in one run. Record all fired branches, then choose
the primary branch using this precedence. Symptom row references point to the
numbered rows in the Symptom Attribution table below.

1. **Invalid or incomplete run.** Missing storage evidence, missing job/request
   ids, or `shell_action_count < 3` for approval-volume interpretation.
   Rationale: no engineering decision should rest on incomplete evidence. Rerun
   or narrow the diagnostic before deciding.
2. **Packet 1 regression** (Symptom rows S3, S5, S6). Capture-ready, registry,
   worker-drain, dispatch/recovery, or post-decide polling failure independent of
   sandbox permissions. Rationale: control-plane evidence must be trustworthy
   before sandbox or approval-policy conclusions are meaningful.
3. **Sandbox still blocked** (Symptom row S1). Shell execution remains blocked
   under Candidate A, or mixed shell outcomes prevent the required smoke artifact
   from being produced. Rationale: the parent T-01 blocker remains the immediate
   execution failure; do not patch approval logic yet.
4. **Amendment required** (Symptom row S7). App Server requires
   amendment-specific response data such as `acceptWithExecpolicyAmendment`.
   Rationale: missing response shape blocks a truthful T-01 remediation claim
   even if shell execution improves. Preserve sandbox/approval observations as
   secondary.
5. **Approval policy noisy.** Artifacts are produced, but approval requests exceed
   the calibrated threshold or an approved same action immediately re-escalates.
   Rationale: once artifacts exist, the next usability blocker may be controller
   policy rather than sandbox readability.
6. **Sandbox patch candidate.** Artifacts are produced, escalation is bounded,
   security probes hold, and no higher-precedence branch fired. Rationale: this
   is the first point where a narrow sandbox policy patch has enough evidence.

Mixed shell outcomes: if some shell actions succeed and others fail, classify by
the required smoke result first. If the smoke artifact is not produced, use
"Sandbox still blocked." If the artifact is produced but security probes fail,
do not use "Sandbox patch candidate"; record a security-boundary failure and
continue sandbox design.

Branch decision:

| Field | Value |
|---|---|
| Branches fired | TBD |
| Primary branch by precedence | TBD |
| Secondary observations to carry forward | TBD |
| Engineering next action | TBD |
| Ticket/hygiene next action | TBD |

## Symptom Attribution

Use this table while assigning fired branches.

| Row | Symptom | Likely attribution | Evidence to attach |
|---|---|---|---|
| S1 | Shell command result shows sandbox/read failure, missing platform binary access, or exit `-1`, with no successful approval dispatch. | T-01 sandbox blocker. | Command result, server-request payload if any, policy variant. |
| S2 | `start()` waits roughly `START_OUTCOME_WAIT_SECONDS` and returns a running job, then later `poll()` surfaces escalation/completion. | Slow-but-valid worker. | `start()` response timestamp and later `poll()` excerpt. |
| S3 | `start()` returns `StartWaitElapsed` / running, raw server-request evidence exists, and later `poll()` never surfaces the parked request. | Capture-ready / registry signaling regression. | Raw request, `poll()` sequence, job store rows. |
| S4 | `decide()` returns `decision_accepted=True`, immediate `poll()` briefly shows the same pending request, and later poll advances. | Expected consuming window. | Timed `decide()` and `poll()` excerpts. |
| S5 | Same request remains pending after bounded post-decide polling, or manual-MCP repeat decide returns `request_already_decided` while worker state does not advance. | Registry / worker-drain issue. | Tool response, registry-facing request id, job store rows. |
| S6 | Job terminalizes `unknown` after `session.respond(...)`. | Packet 1 dispatch/recovery path. | Pending request `dispatch_result="failed"` and `dispatch_error`, or audit `action="dispatch_failed"`. |
| S7 | Request payload contains `proposedExecpolicyAmendment` or requires `acceptWithExecpolicyAmendment`. | Amendment-admission branch. | Raw server-request payload. |

## Optional App Server Timeout Probe

Default: do not run. This probe can take more than 15 minutes and should be run
only if promoting T-02 audit row 7 from "Partially covered" to "Covered" is worth
the time.

Procedure, if selected:

1. Start a controlled run that parks on one approval request.
2. Do not decide before the 900-second operator window.
3. Poll at roughly 900 seconds, 930 seconds, and before 1200 seconds if still
   active.
4. Record whether App Server abandons the request before the plugin/runtime
   timeout defaults.

| Timeout probe field | Observation |
|---|---|
| Selected? | No |
| Reason selected or skipped | TBD |
| Park timestamp | TBD |
| 900s poll | Status, pending request id still present?, job status, storage line refs. |
| 930s poll | Status, pending request id still present?, job status, storage line refs. |
| Pre-1200s poll | Status, pending request id still present?, job status, storage line refs. |
| App Server behavior observed | TBD |
| Row-7 audit implication | TBD |

## Final Diagnostic Summary

| Question | Answer |
|---|---|
| What do platform defaults grant? | TBD |
| Does the security boundary hold for host secrets and sibling worktrees? | TBD |
| Is a narrow readable-root grant sufficient, or is Candidate A needed? | TBD |
| Does `accept` resume the action and produce artifacts? | TBD |
| Is approval escalation bounded or noisy after sandbox execution works? | TBD |
| Did amendment admission become required? | TBD |
| Did any Packet 1 capture/registry/dispatch path regress? | TBD |
| Recommended implementation slice | TBD |

## Follow-Up Changes To File

Do not edit the assessment unless this run disproves its recommendation. Record
diagnostic-specific calibration and branch precedence outcomes in this run
record.

| Follow-up | Needed? | Owner | Notes |
|---|---|---|---|
| Sandbox policy patch | TBD | TBD | TBD |
| Approval-policy default decision | TBD | TBD | TBD |
| Amendment-admission ticket / Packet 2 | TBD | TBD | TBD |
| Packet 1 regression ticket | TBD | TBD | TBD |
| T-02 closure/update | TBD | TBD | Preserve row-7 caveat unless timeout probe proves otherwise. |
