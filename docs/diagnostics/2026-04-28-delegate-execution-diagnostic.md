# T-01 Delegate Execution Diagnostic Run Record

> **Supersession note (2026-04-29):** Candidate A has since landed:
> sandbox policy promotion at `ce0579f6`, live `/delegate` smoke
> artifact at `a7a4e9c9`, T-20260423-01 closed at `6580d86e`. This run
> record remains evidence for the mechanism decision; it is not a live
> operational document. Amendment admission / Packet 2 was later judged
> not currently required for the observed canonical delegation flow.

Date: 2026-04-28

Status: Baseline attempt 1 executed and adjudicated (Branch S1 — Sandbox still blocked); Candidate A att1+att2+att3 + security probes 1+2+3 executed and adjudicated (Branch — Sandbox patch candidate fires; S1 refuted for canonical workload). Engineering action completed: Candidate A's policy configuration (`includePlatformDefaults: True`) was promoted as the v1 sandbox patch in commit `ce0579f6`, and the post-restart live `/delegate` smoke later closed `T-20260423-01`. Plugin restart was required only before further variant work and the live smoke, not for the closure commit.

Decision artifact:
`docs/assessments/2026-04-28-codex-collaboration-next-focus-report.md` —
**not present on this branch**. The assessment is committed on the sibling
branch `docs/codex-collab-next-focus-assessment` at commit `a477de94`. Both
branches are siblings off `main` at merge anchor `36ef13e8`; neither is an
ancestor of the other.

To read the assessment from this branch without switching branches:

```bash
git show docs/codex-collab-next-focus-assessment:docs/assessments/2026-04-28-codex-collaboration-next-focus-report.md
```

Or to inspect at the locked commit specifically:

```bash
git show a477de94:docs/assessments/2026-04-28-codex-collaboration-next-focus-report.md
```

Cross-branch dependency rule: any line citation in this run record that points
into the assessment file is read at `a477de94`, not `HEAD`. If the assessment
file is updated on its branch, line anchors here may go stale; verify with
`git log --oneline -1 docs/codex-collab-next-focus-assessment -- docs/assessments/2026-04-28-codex-collaboration-next-focus-report.md`
before relying on assessment line numbers.

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
| `git status --short --branch` | `## feature/delegate-execution-diagnostic-record...origin/feature/delegate-execution-diagnostic-record` (in sync with origin post-batch-push; clean for diagnostic-relevant paths; 8 unrelated `docs/tickets/closed-tickets/` moves carry over from a prior session and are out of scope) |
| `git rev-parse --short HEAD` | `49d93001` (Run Identity refresh commit; seven-commit run-record series on top of merge anchor `36ef13e8`: `46cd954e` run-record-add → `789607fc` pre-execution-fill → `50664694` cycle-1 Minor remediation → `145ae935` cycle-2 Major remediation → `ea899cb3` cycle-3 Minor remediation → `2d5e91f3` cycle-4 polish → `49d93001` Run Identity refresh). This is the live-run-start re-record per cycle-4 reviewer guidance. The commit landing this update will momentarily drift HEAD by 1; from this point forward, per-variant `Pre-run HEAD` evidence captures the variant-level anchor — no further Run Identity refreshes are required. |
| `codex --version` | `codex-cli 0.125.0` (raw observable; no separate App Server version exposed; do not infer a semantic App Server version from this string) |
| App Server JSON Schema bundle (pre-Candidate-A capture) | Captured via `codex app-server generate-json-schema --out .tmp/app-server-schema-pre-candidate-a/` (default mode, no `--experimental` flag). 35 top-level Params/Response files + `v1/` (8 KB) + `v2/` (1.6 MB, 192 files). Bundle is gitignored under `.tmp/`. **Forensic SHA-256 anchors**: umbrella `codex_app_server_protocol.schemas.json` `d12aeef8eb…`; v2 umbrella `codex_app_server_protocol.v2.schemas.json` `0e72877f63…`; S7 request `CommandExecutionRequestApprovalParams.json` `dc3251a5dc…`; S7 response `CommandExecutionRequestApprovalResponse.json` `42010a48dd…`. **Cross-variant supporting evidence only — NOT a Candidate-A gate.** S7-split schema corroboration from this bundle: `proposedExecpolicyAmendment` (request side) is documented as "Optional proposed execpolicy amendment to allow similar commands without prompting" — confirms S7a as a forward-looking *offer*, not a progress blocker. `acceptWithExecpolicyAmendment` (response side) appears as one branch of the `CommandExecutionApprovalDecision` enum and is documented "User approved the command, and wants to apply the proposed execpolicy amendment so future matching commands can run without prompting" — confirms S7b only fires when `available_decisions` is *restricted* to amendment-class (in Baseline attempt 1, the full 6-option list was available, so S7b correctly did NOT fire). Plugin↔schema name mapping observed: plugin `kind: command_approval` ↔ schema `CommandExecutionRequestApproval`; plugin `kind: file_change` ↔ schema `FileChangeRequestApproval`. |
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

The probe set below covers T-01's full security boundary checklist
(`docs/tickets/2026-04-23-codex-collaboration-delegate-execution-remediation.md:77-82`):
`~/.ssh/`, `~/.aws/`, `~/.config/`, `.env` files outside the worktree, other
worktrees, and the parent repo's `.git/`.

Record host-side existence/readability only. Do **not** print sensitive file
contents. `test -e` returns 0 if the path exists, 1 otherwise; the bash idiom
below converts to a `yes`/`no` boolean for table-readability.

```bash
exists() { if test -e "$1"; then echo "yes"; else echo "no"; fi; }
readable() { if test -r "$1"; then echo "yes"; else echo "no"; fi; }

WORKTREE="/Users/jp/Projects/active/claude-code-tool-dev"
PARENT_GIT="$WORKTREE/.git"
OUTSIDE_ENV="$(dirname "$WORKTREE")/.env"   # adjust if your sibling .env lives elsewhere
SIBLING_WORKTREE="TBD-pick-an-actual-path"   # REQUIRED-FILL: replace with a concrete absolute path BEFORE running the loop. Example: another active project root such as "$HOME/Projects/active/some-other-repo". If you have no sibling worktree, set this to "" and record absence in the table below — do NOT run with the literal "TBD-..." placeholder, which produces a non-diagnostic "no" for both exists and readable.

for p in \
  "$HOME/.ssh/id_rsa" \
  "$HOME/.aws/credentials" \
  "$HOME/.config" \
  "$PARENT_GIT" \
  "$OUTSIDE_ENV" \
  "$SIBLING_WORKTREE"; do
  printf '%s exists=%s readable=%s\n' "$p" "$(exists "$p")" "$(readable "$p")"
done
```

| Path | Host exists? | Host readable? | In-sandbox exists? | In-sandbox readable? | Diagnostic interpretation |
|---|---:|---:|---:|---:|---|
| `$HOME/.ssh/id_rsa` | TBD | TBD | TBD | TBD | T-01 checklist: user SSH key. Read-leak under platform defaults is a security-boundary failure. |
| `$HOME/.aws/credentials` | TBD | TBD | TBD | TBD | T-01 checklist: cloud credentials. Read-leak is a security-boundary failure. |
| `$HOME/.config` | TBD | TBD | TBD | TBD | T-01 checklist: directory-level secret-bearing tree. Even directory listing visibility is a partial leak; record the granularity (listing vs. file read). |
| Parent repo `.git/` (host clone) | TBD | TBD | TBD | TBD | T-01 checklist: leaks `git config`, hooks, refs of the host clone. Distinct from the delegated worktree's ephemeral `.git`; probe the absolute host-clone path, not the worktree path. |
| `.env` outside worktree | TBD | TBD | TBD | TBD | T-01 checklist: secrets in adjacent projects. Pick a concrete path that exists; if no `.env` exists outside the worktree, record absence and pick a same-class control (e.g., `~/.npmrc`, `~/.pgpass`). |
| Known sibling repo/worktree | TBD | TBD | TBD | TBD | T-01 checklist: cross-worktree leakage. Probe the sibling's root and its `.git/` separately. |
| Additional control row | TBD | TBD | TBD | TBD | Append rows here if the live run surfaces another sensitive path the platform-defaults grant exposes. |

If a sensitive path is absent on the host, an in-sandbox unreadable result is
non-diagnostic. Pick another existing control path or record the absence.

**Granularity note:** distinguish `exists` (sandbox can `stat` the path; this
leaks the *fact* of the path's existence) from `readable` (sandbox can read the
path's contents; this leaks the *contents*). For directories, also distinguish
listing (`ls`) from per-entry read. Record the highest-granularity leak
observed.

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
`docs/diagnostics/delegate-smoke/20260428T005625-result.txt`
(timestamp matches Run Identity's "Diagnostic smoke timestamp" field; reuse the
same token for every variant in this run so artifact filenames are unambiguous)

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
| Candidate B | Narrow `readableRoots` additions only — see Candidate B Matrix below | Same approval policy as baseline unless explicitly changed | Post-Candidate-A-success conditional. Role determined by Candidate A's first successful approved-execution attempt (att3 — renamed from "att2 attempt 2" after att2 attempt 1 canceled by approval timeout): att3 succeeded → optional minimum-grant minimization (security hygiene only); had att3 failed with a concrete sandbox missing-path error, B would have been targeted diagnostic continuation. See Candidate B Matrix below for full framing. |

### Candidate B Matrix

**Scope note (added 2026-04-28 during Candidate A attempt 1 cell-filling, post-mechanism-revision):** Candidate B is a **post-Candidate-A-success conditional**, not a live competing explanation for attempt 1's parking.

- The mechanism revision (Candidate A attempt 1: parking observed under runtime-proofed `'includePlatformDefaults': True`) **invalidates the original framing of Candidate B as an alternative explanation for att1 parking.** Approval gating fired before any shell execution, so **sandbox readability is not proven as the cause of parking, and B is no longer a competing explanation for att1 parking**. (Source-level App Server ordering remains unestablished; a narrower `readableRoots` set cannot address what is not proven to be the actual cause.)
- **Do not run Candidate B before Candidate A's first successful approved-execution attempt.** That attempt (approve-strategy under True flag) is the load-bearing experiment that produces the downstream evidence on which B's role depends. *Attempt-numbering note:* the original plan called this "Candidate A attempt 2"; in execution, att2 attempt 1 (Strategy C) canceled by 900s approval timeout, and the rerun "att2 attempt 2" was renamed att3 — see attempt-history table for the split.
- **Resolved (post-att3, 2026-04-29):** att3 succeeded — shell executed past the gate, smoke artifact produced byte-perfect, security probes 1+2+3 all BLOCKED. Per the success branch below, Candidate B is now **optional minimum-grant minimization** (security hygiene only).
- **Success branch (fired):** att3 succeeds → Candidate B becomes **optional minimum-grant minimization** — pure security hygiene to determine whether tighter explicit roots can replace `includePlatformDefaults: True`. Not a blocker for closure unless the closure must prove minimum-viable grants.
- **Failure branch (did not fire):** had att3 failed with a concrete sandbox missing-path error (e.g., "permission denied" on a specific path that the runtime reports), Candidate B would have been **targeted diagnostic continuation** keyed to the specific missing path — required (not optional) to localize the gap.
- The matrix below is **preserved**, but its precondition for execution was the att3 outcome (not the att1 parking observation that originally motivated it). Since att3 succeeded, B's matrix is now optional hygiene.

T-01 names `["/usr/bin", "/usr/lib"]` as the narrow-grant starting point
(`docs/tickets/2026-04-23-codex-collaboration-delegate-execution-remediation.md:84-87`).
The matrix below extends T-01's seed with `/bin` (POSIX command location;
distinct from `/usr/bin` on macOS — `which sh` resolves to `/bin/sh` on
Darwin, not `/usr/bin/sh`) so the smoke objective's commands can be located.

Run the levels in order; stop at the first level where the smoke artifact
produces successfully. Each level extends the previous level — do not run
levels in parallel.

#### Pre-Matrix Discovery (run before B1)

Before invoking the matrix, record the actual host paths for the smoke
objective's commands. If any path lies outside the matrix below, prepend
its parent root to B1 (and document the addition in the per-variant
evidence).

```bash
for cmd in sh mkdir cat ls; do
  printf '%s -> %s\n' "$cmd" "$(command -v "$cmd" || echo "NOT-FOUND")"
done
```

| Command | Resolved path | Parent root | Already in matrix? | Action |
|---|---|---|---|---|
| `sh` | TBD | TBD | TBD | If parent root not in B1, prepend it. |
| `mkdir` | TBD | TBD | TBD | If parent root not in B1, prepend it. |
| `cat` | TBD | TBD | TBD | If parent root not in B1, prepend it. |
| `ls` | TBD | TBD | TBD | If parent root not in B1, prepend it. |

Recorded for the live operator environment (macOS, this repo): `which sh
mkdir cat ls` → all under `/bin`. Hence B1 below includes `/bin`.

#### Levels

| Level | `readableRoots` additions | Rationale |
|---|---|---|
| B1 | `["/bin", "/usr/bin"]` | POSIX command location plus userland binaries. macOS keeps `/bin` and `/usr/bin` separate (no usr-merge), and the smoke objective's `sh`, `mkdir`, `cat`, `ls` resolve to `/bin/*` on this host (verified above). Without `/bin`, B1 would fail for path-resolution reasons unrelated to sandbox correctness. |
| B2 | `["/bin", "/usr/bin", "/usr/lib"]` | T-01's named starting point with `/bin` preserved. Adds shared library read for shell and any binary dynamic linking. |
| B3 | `["/bin", "/usr/bin", "/usr/lib", "/usr/local/bin", "/usr/local/lib"]` | Adds Homebrew / locally-built binaries common on macOS. Required if the operator's environment routes through `/usr/local/bin` (e.g., `git`, `python` from Homebrew). |
| B4 | B3 + `/System/Library` (macOS) or `/lib`, `/lib64` (Linux) | Adds OS-level frameworks. Required if shell or binaries link against system frameworks not covered by `/usr/lib`. |
| B5+ | Operator-defined extensions | If B4 still does not produce the smoke artifact, the narrow-grant approach is likely insufficient. Record what's missing, then either return to Candidate A's `includePlatformDefaults: True` or document the gap as "narrow-grant infeasible for this platform." |

Stop conditions:

- **Smoke artifact produced** → record the level as the **minimum viable
  grant**; do not run higher levels.
- **All security probes still hold** at the level that produced the smoke
  artifact → that level is the candidate sandbox patch.
- **Security probe fails before smoke succeeds** → escalate as a security
  boundary failure; do not promote any level to "patch candidate."

Each Candidate B level is a separate variant for purposes of the Variant
Isolation Protocol — clean state, capture patch, restart runtime, observe
`sandboxPolicy`, restore. Reusing a previous level's running process across
levels is a contamination path.

## Variant Isolation Protocol

Variants must not contaminate each other. A patch from Candidate A bleeding into
Baseline (or vice versa) silently invalidates the comparison. Apply this
protocol for every variant before recording evidence in the per-variant block.

**Required discipline per variant:**

1. **Reach a clean pre-run state.** Working tree must be clean for any path the
   variant patch will touch. Acceptable forms: clean repo, or stashed/committed
   prior-variant state, or a fresh disposable worktree per variant.

   ```bash
   git status --short
   # Must show no modifications to files the variant patch will touch.
   git rev-parse --short HEAD
   ```

2. **Capture the variant patch as a durable artifact.** Patches must be
   reviewable and reversible. Three acceptable forms; pick one and record it:

   - **Inline diff in the run record** — paste the full `git diff` under
     "Policy diff / patch under test" in the per-variant evidence.
   - **Patch file at `.tmp/variant-<name>.patch`** — gitignored
     (`.gitignore:51`); generate with `git diff > .tmp/variant-<name>.patch`
     and reference the file path. Operator must keep the file until the run
     record is complete.
   - **Temporary commit on a throwaway branch** — record the branch name and
     the commit short SHA, then drop the branch after run completion.

   Do **not** rely on uncommitted in-memory edits without one of the above
   capture forms — operator memory is not durable evidence.

3. **Apply the patch and record pre-run state immediately.** Before invoking
   any delegation, capture pre-run HEAD, dirty diff summary, patch SHA, and
   the **patch-applied-at timestamp** (ISO-8601 UTC, captured immediately
   after the patch is on disk — e.g., `date -u +"%Y-%m-%dT%H:%M:%SZ"`) into
   the per-variant evidence block. The timestamp is what step 4's
   `Plugin process start timestamp` is compared against.

4. **Reload the live runtime so it observes the patch.** A `git diff` proves
   the patch is on disk; it does **not** prove the running plugin/MCP process
   loaded it. `codex_runtime_bootstrap.py` imports `delegation_controller`
   and `runtime` modules at startup
   (`packages/plugins/codex-collaboration/scripts/codex_runtime_bootstrap.py`);
   subsequent file edits do not reload those modules. If the live process
   started before the patch was written, the variant will run against
   pre-patch code while appearing to run against post-patch code.

   Required actions before invoking delegation for the variant:

   1. **Stop the live plugin/MCP process** that hosts the delegation
      controller. Method depends on how the operator invokes the plugin
      (Claude Code restart, MCP server restart, or PID-targeted kill).
   2. **Restart it.** The new process will import the patched modules.
   3. **Capture process identity:** record the new PID and process start
      timestamp into the per-variant evidence block. The PID + start
      timestamp prove the variant ran against a process that started after
      the patch landed.
   4. **Capture observed `sandboxPolicy` payload directly.** The policy
      built by `build_workspace_write_sandbox_policy` (`runtime.py:23`) is
      sent to App Server via `turn/start` (`runtime.py:214,223`) and is
      **not** automatically logged in any plugin-side JSONL store. Three
      acceptable observation forms:

      - **Patch-embedded log emit** (preferred). Include a temporary emit
        in the candidate patch itself. The two pre-existing import sets
        differ between sites — pick the snippet that matches the site you
        are patching. Replace `VARIANT-LABEL` with the active variant
        identifier (`A`, `B1`, `B2`, etc.); the label is hardcoded
        per-variant, **not** a Python f-string variable.

        **Site 1: build site, `runtime.py:23` in
        `build_workspace_write_sandbox_policy`.** Emit the policy to a
        durable file sink via context-managed open (deterministic close).
        `runtime.py` already imports `from pathlib import Path` at module
        top; the patch adds an aliased re-import plus `datetime` for the
        ISO-8601 timestamp. Insert immediately before the `return`
        statement:

        ```python
        # variant instrumentation (remove after diagnostic)
        from datetime import datetime, timezone
        from pathlib import Path as _Path

        with _Path("/tmp/codex-collab-baseline-runtime-proof.log").open(
            "a", encoding="utf-8"
        ) as _handle:
            _handle.write(
                f"{datetime.now(timezone.utc).isoformat()} "
                f"[VARIANT-LABEL] sandboxPolicy={policy!r}\n"
            )
        ```

        Replace `policy` with whichever local variable name the function
        uses for its return value (read the patched function before
        copying — current source assigns the dict literal directly to
        `return`, so the patch must also extract it to a local variable
        first).

        **Site 2: call site, `delegation_controller.py:1327`.** Patch
        the call site to extract the policy to a local, write it to the
        same durable file sink as Site 1, then pass it through:

        ```python
        # variant instrumentation (remove after diagnostic)
        from datetime import datetime, timezone
        from pathlib import Path as _Path

        _variant_policy = build_workspace_write_sandbox_policy(worktree_path)
        with _Path("/tmp/codex-collab-baseline-runtime-proof.log").open(
            "a", encoding="utf-8"
        ) as _handle:
            _handle.write(
                f"{datetime.now(timezone.utc).isoformat()} "
                f"[VARIANT-LABEL] sandboxPolicy={_variant_policy!r}\n"
            )
        # then in the kwarg list, pass _variant_policy instead of the
        # build_workspace_write_sandbox_policy(worktree_path) inline call:
        # sandbox_policy=_variant_policy,
        ```

        Bare `logger.warning(...)` or `print(..., file=sys.stderr)` are
        **not** valid call-site forms in current launch mode — see the
        runtime-proof routing finding below. The call site is
        structurally usable only when it writes to a durable non-stderr
        sink (file, in this snippet, or any equivalent explicit-path
        sink the operator records).

        Capture the emitted payload by reading the durable file sink:
        `cat /tmp/codex-collab-baseline-runtime-proof.log`. Paste the
        line into the per-variant evidence block. Direct stderr/stdout
        capture and bare `logging` emits are **not** valid in current
        launch mode (`claude --plugin-dir ... --dangerously-skip-permissions`);
        see the runtime-proof routing finding immediately below.
      - **App Server access log** if the operator's App Server build emits
        one and the path is known. Record the log path and grep for
        `turn/start` against the variant's job id timestamp.

        Investigation result (codex-cli `0.125.0`, this run):
        access-log observation is **unavailable** for this build.
        `~/.codex/logs_2.sqlite` is codex's tracing store;
        `codex_app_server::message_processor` entries log `turn/start`
        arrival with `connection_id` and `request_id` only, not the
        request `params`. The 4 rows matching the literal `sandboxPolicy`
        were assistant-message content from a prior consultation about
        this run record (false positives — Codex's tracing layer captured
        its own model output), not transport captures of `turn/start`
        traffic. `codex app-server --help` exposes no body-logging flag,
        and the plugin's spawn (`runtime.py:53`) injects no log-related
        arguments. For this build, the patch-embedded log emit is the
        only viable runtime-proof form. Re-test if a different App Server
        build or config is introduced that does emit per-request access
        logs.
      - **Runtime-proof routing finding (current launch mode, this
        session):** the plugin's FD 2 (stderr) is consumed and dropped
        by Claude Code in normal launch mode. Empirical evidence: FD 2
        is connected to a unix domain socket on Claude Code's side
        (`lsof -a -p <plugin-pid> -d 0,1,2` shows FDs 0/1/2 as socket
        pairs); the per-server `.jsonl` cache at
        `~/Library/Caches/claude-cli-nodejs/<project>/mcp-logs-plugin-codex-collaboration-codex-collaboration/`
        (107 files, schema `[cwd, debug, error, sessionId, timestamp]`)
        has no `stderr` key — the 5 historical `error` rows came from
        the JSON-RPC response path (FD 1, exception text without the
        `codex-collaboration:` prefix that the plugin's stderr helpers
        add at `control_plane.py:50`, `dialogue.py:66`,
        `dialogue.py:853`). Claude Code docs require `claude --debug
        mcp` to surface MCP server stderr. Bare `logger.warning(...)`
        shares this fate — `codex_runtime_bootstrap.py` attaches no
        logging handlers, so `logging` falls through to Python's stderr
        default and is dropped alongside `print(..., file=sys.stderr)`.
        **Implication:** in current launch mode, neither stderr nor
        bare `logger` emits are valid runtime-proof sinks; the
        build-site and call-site snippets above therefore write to a
        durable file sink. If the launch mode is changed to `--debug
        mcp`, record the change in the per-variant evidence block
        alongside the runtime-proof method (stderr capture becomes
        recoverable in that mode).
      - **Ad-hoc instrumentation patch** layered over the variant patch.
        Treat the instrumentation as part of the variant patch when
        capturing pre-run state.

      Do **not** infer the live policy from the on-disk `runtime.py` source.
      Inference is what this rule prevents.

5. **Run the variant.** Do not amend the patch mid-run.

6. **Capture post-run state.** Record post-run HEAD (should equal pre-run
   HEAD if no commits landed), `git status --short` (should show only the
   variant patch's known modifications, plus expected smoke artifact paths),
   any unexpected dirty paths, and the post-run process PID (must equal the
   pre-run PID captured in step 4 — if it changed mid-variant, the run is
   contaminated).

7. **Restore before next variant.** Three acceptable forms; pick the one that
   matches the patch capture form:

   - For inline-diff or patch-file capture: `git checkout -- <paths>` for the
     patched paths, or `git stash drop` if stashed, or `git apply -R
     .tmp/variant-<name>.patch`.
   - For temporary-commit capture: `git reset --hard <pre-run-HEAD>` —
     destructive, **forbidden on the diagnostic branch
     `feature/delegate-execution-diagnostic-record`**. Use only on a
     dedicated throwaway branch (e.g., `spike/variant-A-temp` or
     `experiment/variant-B-temp`), then drop the throwaway branch.
   - **Always: clear the runtime-proof artifact file.** Use `trash
     /tmp/codex-collab-baseline-runtime-proof.log` (project rule: no
     `rm`); or, if explicitly truncating instead of deleting, record the
     truncation time and method in the per-variant evidence block so
     the next variant's emits are unambiguously distinguishable. Stale
     artifact lines from a prior variant cause cross-variant
     interpretation errors.

   After restoration, **restart the plugin/MCP process again** so the next
   variant (or Baseline rerun) observes the restored code, not the patched
   code still in memory. Record the second restart's PID and start
   timestamp in the next variant's pre-run evidence.

8. **Verify restoration.** Re-run `git status --short` for the patched paths;
   must match pre-run-state. Record this verification in the per-variant
   block. If status diverges from pre-run, the variant is contaminated; do
   not proceed to the next variant until restored.

**Cross-variant checks:**

- Baseline must be run with no patch applied. If Baseline was run with a
  preceding variant's patch still in place, mark the run invalid (Branch
  Precedence #1) and rerun. **Runtime-proof-only instrumentation
  exception:** a patch that adds only an observation emit (e.g., the
  build-site file-write snippet above) without altering the returned
  `sandbox_policy` dict is semantics-preserving and does not violate the
  no-patch rule. The instrumentation IS a patch for capture/restore
  purposes (record under "Patch capture form"; mark `Patch applied at`),
  but it is NOT a behavioral patch for variant interpretation purposes.
- Candidate A and Candidate B must not be run sequentially in the same
  worktree without explicit restoration verification between them.

## Per-Variant Evidence

Copy this block once per variant. If the variant needs a rerun, append another
attempt under "Attempt history" instead of overwriting the failed or compressed
attempt.

### Variant: TBD

| Field | Source / fill guidance | Observation |
|---|---|---|
| Pre-run HEAD | Required. `git rev-parse --short HEAD` immediately before applying the variant patch. | TBD |
| Pre-run dirty diff | Required. `git status --short` before patch; must show no modifications to files the patch will touch. | TBD |
| Patch capture form | Required. One of: inline diff (below), `.tmp/variant-<name>.patch`, or throwaway-branch commit SHA. See Variant Isolation Protocol step 2. | TBD |
| Patch applied at | Required for Candidate variants; **not applicable for Baseline** (no patch — record `not applicable: Baseline (no patch)`). For Candidates: ISO-8601 UTC timestamp captured immediately after applying the patch (e.g., `date -u +"%Y-%m-%dT%H:%M:%SZ"` immediately after `git apply` / `git checkout` / inline edit save). Anchors the runtime-reload chain: `Patch applied at` < `Plugin process start timestamp` is a required ordering for the variant to be valid. | TBD |
| Policy diff / patch under test | Required. Inline `git diff` of the variant patch, or "current code (no patch)" for Baseline. If captured at a path or SHA, also paste the diff here for reviewer-readability. | TBD |
| Plugin process PID (post-restart) | Required. PID of the plugin/MCP process **after** restart in Variant Isolation Protocol step 4. Proves the variant ran against a process that started after the patch landed. | TBD |
| Plugin process start timestamp | Required. ISO-8601 UTC of the post-restart process start. `ps -o lstart -p <PID>` emits a non-ISO local-time format like `Tue Apr 28 04:56:25 2026` (no zone marker) — record both the raw output **and** the normalized UTC value. **macOS-correct normalization (epoch round-trip):** `EPOCH=$(date -j -f "%a %b %d %H:%M:%S %Y" "<lstart>" +%s); date -u -r "$EPOCH" +"%Y-%m-%dT%H:%M:%SZ"`. **Linux:** `date -u -d "<lstart>" +"%Y-%m-%dT%H:%M:%SZ"`. **macOS pitfall — do NOT use:** the simpler-looking single-call recipe `date -u -j -f "%a %b %d %H:%M:%S %Y" "<lstart>" +"%Y-%m-%dT%H:%M:%SZ"` silently relabels local-tz input as UTC instead of converting (verified during Baseline attempt 1 — produced a 4-hour-wrong value in EDT before correction; see Baseline block for the documented incident, and `c704eafa` commit message). Always cross-check against an independent UTC source if available (e.g., a runtime-proof artifact's `datetime.now(timezone.utc)` timestamp from the same run, or the `delegate_start` audit row's `timestamp` field) — disagreement implies a parsing error in one recipe. Must be **later than** `Patch applied at` above; if it is earlier or equal, the running process predates the patch and the variant is invalid (rerun after a fresh restart). For Baseline (where `Patch applied at` is N/A under template default but recorded under runtime-proof-only instrumentation exception), the timestamp still anchors the run identity. | TBD |
| Observed `sandboxPolicy` payload | Required. Direct evidence the live runtime built the patched policy. One of: patch-embedded log emit at `delegation_controller.py:1327` or `runtime.py:23` capturing the dict, App Server access-log entry for the variant's `turn/start`, or ad-hoc instrumentation output. Inference from on-disk source is **not** acceptable. Paste payload literal. | TBD |
| Runtime-proof method | Required. Which of the three observation forms (patch-embedded emit / App Server log / ad-hoc instrumentation) was used to populate "Observed `sandboxPolicy` payload". | TBD |
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
| Post-run HEAD | Required. `git rev-parse --short HEAD` after the run. Must equal pre-run HEAD unless commits landed; explain any drift. | TBD |
| Post-run dirty diff | Required. `git status --short` after the run. Should show only the variant patch's known modifications plus any smoke artifact paths intentionally tracked. | TBD |
| Variant restoration command | Required. Exact command used to undo the variant patch (e.g., `git apply -R .tmp/variant-A.patch`, `git checkout -- runtime.py`, `git stash drop`). Skip for Baseline. | TBD |
| Restoration verification | Required. `git status --short` after restoration; must match pre-run dirty diff. Record divergences as contamination. | TBD |
| Cleanup performed | Required after evidence capture. Record command or "deferred". | TBD |

Attempt history:

| Attempt | Reason started | Shell-visible actions | Outcome | Preserved evidence |
|---:|---|---:|---|---|
| 1 | Initial run | TBD | TBD | TBD |

Raw excerpts:

```text
TBD
```

### Variant: Baseline (attempt 1)

Pre-run evidence captured before invoking `codex_delegate_start`. Post-run cells filled immediately after completion + runtime-proof artifact read. Tightenings per session adjudication: explicit `Patch applied at` override (runtime-proof-only instrumentation exception); `Plugin process PID` records both python child + uv wrapper with the python child labelled evidentiary; `Plugin process start timestamp` records both raw `lstart` and normalized UTC.

| Field | Source / fill guidance | Observation |
|---|---|---|
| Pre-run HEAD | `git rev-parse --short HEAD` immediately before applying the variant patch. | `7650366d` (verified at variant-start; matches the two-layer HEAD anchor pattern — Run Identity remains frozen at `49d93001` as the run-level snapshot). |
| Pre-run dirty diff | `git status --short` before patch; must show no modifications to files the patch will touch. | **Pre-patch (last session, before `2026-04-28T06:56:55Z`):** clean for `packages/plugins/codex-collaboration/server/runtime.py`. **Current (immediately before `codex_delegate_start`):** `M packages/plugins/codex-collaboration/server/runtime.py`; byte-identical to `.tmp/variant-baseline.patch` (verified via `diff <(git diff packages/plugins/codex-collaboration/server/runtime.py) .tmp/variant-baseline.patch` → empty). **Carry-forward unrelated to variant:** 8 ticket-file moves under `docs/tickets/closed-tickets/`; untracked `.tmp/variant-baseline.patch` and `.tmp/variant-baseline.applied-at` (both gitignored per `.gitignore:51`). |
| Patch capture form | One of: inline diff, `.tmp/variant-<name>.patch`, or throwaway-branch commit SHA. | `.tmp/variant-baseline.patch` (32 lines, 1277 bytes; gitignored per `.gitignore:51`). Inline reproduction in code block immediately after this table. |
| Patch applied at | Template default for Baseline: `not applicable: Baseline (no patch)`. **Override (runtime-proof-only instrumentation exception per Cross-variant checks):** the instrumentation IS a patch for capture/restore purposes — record the timestamp so the `Patch applied at < Plugin process start timestamp` ordering can be evaluated. | `2026-04-28T06:56:55Z` (runtime-proof-only instrumentation exception; Baseline behavioral patch is current code/no policy-field patch). The template's "N/A for Baseline" default is overridden by the explicit instrumentation exception so the ordering invariant can be enforced for this variant. |
| Policy diff / patch under test | Inline `git diff` of the variant patch, or "current code (no patch)" for Baseline. | **Behavioral:** current code (no patch). **Runtime-proof-only instrumentation diff** (semantics-preserving; does not alter the returned `sandbox_policy` dict): see code block immediately after this table. |
| Plugin process PID (post-restart) | PID of the plugin/MCP process **after** restart. | **Python child PID `11696`** (evidentiary — this is the import holder that re-read `runtime.py` post-restart). uv wrapper PID `11645` (parent). Verified via `ps aux \| grep codex_runtime_bootstrap \| grep -v grep`. |
| Plugin process start timestamp | ISO-8601 UTC of post-restart process start. State which form was used. Must be later than `Patch applied at` for variant validity. | **Raw `ps -o lstart -p 11696` output:** `Tue Apr 28 11:41:29 2026` (local timezone — verified `date +"%Z (%z)"` returns `EDT (-0400)` this session, format `%a %b %d %H:%M:%S %Y` with no zone marker). **Normalized UTC: `2026-04-28T15:41:29Z`** (via macOS-correct epoch round-trip: `EPOCH=$(date -j -f "%a %b %d %H:%M:%S %Y" "<lstart>" +%s)` then `date -u -r "$EPOCH" +"%Y-%m-%dT%H:%M:%SZ"`). **Pitfall caught and recorded:** the simpler-looking single-call recipe `date -u -j -f "%a %b %d %H:%M:%S %Y" "<lstart>" +"%Y-%m-%dT%H:%M:%SZ"` does NOT convert local→UTC on macOS; it treats the input as if already UTC and just relabels. That recipe was used initially this session and produced a 4-hour-wrong value (`2026-04-28T11:41:29Z`); the error was caught before propagating to downstream evidence by re-deriving via the epoch round-trip. The first commit on this run record's Baseline block had the wrong value; this correction lands in the next run-record commit. **Ordering check (using corrected UTC):** plugin start `2026-04-28T15:41:29Z` > patch applied `2026-04-28T06:56:55Z` ✓ — plugin started ~8h44m after patch was applied. Variant valid; running plugin re-imported the patched module. **Cross-check via runtime-proof artifact's own timestamp** (`2026-04-28T15:53:37.116985+00:00`, sourced from Python's `datetime.now(timezone.utc).isoformat()` — independently correct): post-dates the corrected plugin start by ~12 minutes, consistent with the first `codex_delegate_start` call after restart. The independent sources agree on the corrected UTC; they would have been mutually inconsistent under the wrong value (artifact would appear to be emitted ~4h12m after plugin start, which is implausible for a process under active use). |
| Observed `sandboxPolicy` payload | Direct evidence the live runtime built the patched policy. Inference from on-disk source NOT acceptable. | Captured at `2026-04-28T15:53:37.116985+00:00` from `/tmp/codex-collab-baseline-runtime-proof.log`:<br><br>`{'type': 'workspaceWrite', 'writableRoots': ['/Users/jp/.claude/plugins/data/codex-collaboration-inline/runtimes/delegation/6753a537-99d8-456f-a1c0-1c79f13a2fc9/worktree'], 'readOnlyAccess': {'type': 'restricted', 'readableRoots': ['/Users/jp/.claude/plugins/data/codex-collaboration-inline/runtimes/delegation/6753a537-99d8-456f-a1c0-1c79f13a2fc9/worktree'], 'includePlatformDefaults': False}, 'networkAccess': False, 'excludeSlashTmp': True, 'excludeTmpdirEnvVar': True}`<br><br>**Source/runtime parity:** dict literal at `runtime.py:23` reproduced byte-for-byte at runtime. **T-01 mechanism confirmed:** `readableRoots` contains only the delegated worktree; `includePlatformDefaults: False` means `/bin`, `/usr/bin`, `/usr/lib` are unreachable; `/bin/zsh` (which the delegate proposed) cannot execute under this policy → Codex parks every shell command as `command_approval` before any approval-policy logic runs. |
| Runtime-proof method | Which observation form was used. | Patch-embedded log emit at `runtime.py:23` build site; file-write to `/tmp/codex-collab-baseline-runtime-proof.log`. Stderr/stdout/logger explicitly invalid in current launch mode (FD 2 routing finding documented in VIP step 4). |
| Approval policy value | Controller/runtime input for this run. | **Inferred: `untrusted`** (Codex's default approval policy; controller did not override). Inference basis: PendingRequestStore request 0 surfaced `available_decisions: ["accept", "acceptForSession", "acceptWithExecpolicyAmendment", "applyNetworkPolicyAmendment", "decline", "cancel"]` — the presence of `acceptWithExecpolicyAmendment` and the full 6-option action list is characteristic of `untrusted` mode where every command requires explicit per-call adjudication. The field is NOT directly stored in `start()` / `poll()` response payloads or in DelegationJobStore JSONL rows (verified by direct inspection); recorded here as inference, not direct observation. |
| Job id | `start()` response, `poll()` output, or `DelegationJobStore` row. | `6753a537-99d8-456f-a1c0-1c79f13a2fc9` (from `start()` response). Runtime id: `c72e440a-d4d2-4e8d-9fb8-1f7c2bdc4017`. Collaboration id: `3fd2722e-0b53-4a51-97c1-ab5b834164d8`. Base commit: `7650366d778c961226f95efcf4ea40efa5fe2567` (matches Pre-run HEAD `7650366d`). |
| First parked request id | Required if any escalation occurs. | `0` (from `start()` response `pending_escalation.request_id`). Status: `needs_escalation` returned from `start()` directly — no poll required to surface the parked state. |
| JSON-RPC wire id type | Required if a parked request exists. | **Integer.** `raw_request_id: 0` and `raw_request_id: 1` in PendingRequestStore are unquoted JSON integers (verified in `pending_requests/7337aa50-e517-44f7-8793-eebb3f0fe3db/requests.jsonl` lines 1 and 4). The plugin's surface-level `request_id` field is the stringified form (`"0"` / `"1"`) used for cross-store cross-referencing and as the orchestrator-facing identifier. Both forms recorded for unambiguous correlation. |
| `shell_action_count` | Count shell commands/file-change actions for the smoke objective. | `2` cumulative across job lifetime: (1) attempted chained shell action `/bin/zsh -lc "..."` at request 0 (compressed mkdir + write + verify + print + over-action `test-results.json` write into one `&&`-chain — original smoke objective expected ≥3 shell-visible actions); (2) attempted `file_change` action at request 1 (surfaced after deny on request 0). Both attempts were denied at the approval gate; **neither executed**. Per Smoke Objective section: "rerun is needed because the live agent compressed the shell work into fewer than three shell-visible actions." Per Branch Precedence #1.d: ratio interpretation is invalid (effective denominator < 3) but the run itself remains valid for non-ratio branch classification (S1: Sandbox still blocked). |
| `approval_request_count` | Required if `shell_action_count >= 3`. | `2` cumulative: request 0 (`command_approval`) + request 1 (`file_change`). Both denied at decision-time. |
| Approval request kinds | Required if requests occur. | Two kinds across lifetime: **(1)** `command_approval` at `request_id="0"` from `start()` response — `requested_scope.command` was `/bin/zsh -lc "..."` (full chained command captured in raw excerpts). **(2)** `file_change` at `request_id="1"` surfaced via `poll()` after deny on request 0 — **null scope** (`grantRoot: null`, `reason: null`); both fields returned null on the wire. The second deny finalized the job. **Notable behavior:** the delegate adapts after deny — proposing a different action class (`file_change` after `command_approval` deny) — rather than finalizing on first deny. This contradicts a prior memory-stored expectation that "deny finalizes delegation job." Memory needs correction post-run. |
| `approval_request_count / shell_action_count` | Required if denominator is nonzero; else `no signal`. | `2/2 = 1.0` cumulative (saturation: every attempted action required approval). **Uninterpretable** per Branch Precedence #1.d (denominator < 3). Record as **`no signal for threshold comparison`**. Classify by symptom row (S1: Sandbox still blocked) instead. |
| Command stdout/stderr summary | Tool result or run transcript. | **No shell stdout/stderr captured from delegate-attempted commands** — both proposed actions denied at approval gate; neither executed. The only delegate-side observable trace is the runtime-proof file-write at `/tmp/codex-collab-baseline-runtime-proof.log` (1 line, 531 bytes; semantics-preserving instrumentation, not a delegate-shell stdout event). Codex's escalation responses (returned to the orchestrator via JSON-RPC, not via shell stdout/stderr) were captured under "Approval request kinds" and "poll() transitions". |
| Exit statuses | Tool result or run transcript. | not applicable: both attempted actions denied; neither executed. No exit statuses to record. |
| `decide(approve)` response payload | Required if approval requested. | not applicable: no `approve` was issued. Both decisions were `deny`. **Deny response payloads:** `{"decision_accepted": true, "job_id": "6753a537-99d8-456f-a1c0-1c79f13a2fc9", "request_id": "0"}` for request 0; same shape with `"request_id": "1"` for request 1. |
| `poll()` transitions | Timed `poll()` outputs after start (and after decide if applicable). | **t0 (`start()` response):** `status: needs_escalation`, `parked_request_id: "0"`, `pending_escalation.kind: command_approval`, `pending_escalation.requested_scope.command: "/bin/zsh -lc \\"...\\""`. **t1 (post-deny req 0, `poll()` #1):** `status: running`, `parked_request_id: null`, `pending_escalation: null`. **t2 (`poll()` #2):** `status: needs_escalation`, `parked_request_id: "1"`, `pending_escalation.kind: file_change`, `pending_escalation.requested_scope: {grantRoot: null, reason: null}`. **t3 (post-deny req 1, `poll()` #3 — terminal):** `status: completed`, `parked_request_id: null`, `pending_escalation: null`, `artifact_paths: [.../full.diff, .../changed-files.json, .../test-results.json]`, `artifact_hash: "d604766ea0e6f7d82c1f37f5b66d10d985cfd0271b01f3a7491ceb8f167d7b8d"`, `inspection.changed_files: []`, `inspection.reviewed_at: "2026-04-28T16:02:51Z"`, `promotion_state: "pending"`, `promotion_attempt: 0`. |
| `full.diff` summary | Required if artifact production succeeds. | Empty file (zero bytes). Inspected at `/Users/jp/.claude/plugins/data/codex-collaboration-inline/runtimes/delegation/6753a537-99d8-456f-a1c0-1c79f13a2fc9/inspection/full.diff`. **Implication:** no worktree changes — both denies prevented all proposed writes. |
| `changed_files` | Required if artifact production succeeds. | `[]` per `inspection/changed-files.json` (`{"changed_files": []}`). Empty list confirms zero file modifications across the delegate's entire lifecycle. |
| Artifact hash | Required if artifact production succeeds. | `d604766ea0e6f7d82c1f37f5b66d10d985cfd0271b01f3a7491ceb8f167d7b8d` (sha256, recorded in both `start()` terminal poll response and `inspection.artifact_hash`; covers the 3 framework-generated inspection artifacts: `full.diff`, `changed-files.json`, `test-results.json`). **Note:** the framework's `test-results.json` records `{"commands": [], "schema_version": 1, "source_path": ".codex-collaboration/test-results.json", "status": "not_recorded", "summary": "Execution agent did not persist test results."}` — confirming the delegate's proposed `.codex-collaboration/test-results.json` over-action write inside the chained command never executed. |
| PendingRequestStore rows inspected | Required if any request id exists. | File: `~/.claude/plugins/data/codex-collaboration-inline/pending_requests/7337aa50-e517-44f7-8793-eebb3f0fe3db/requests.jsonl` (6 lines). **Request 0 (`command_approval`):** L1 `op: create` (raw_request_id `0`, item_id `call_EKGTwWcqp44EYVdJ9bizuSzM`, codex_thread_id `019dd4cb-c1e6-7900-8c3e-4accda600d8c`, codex_turn_id `019dd4cb-c461-7dc0-b3f8-2329e816fd81`, available_decisions full 6-option list incl. `acceptWithExecpolicyAmendment`); L2 `op: record_response_dispatch` (resolution_action `deny`, response_payload `{"decision": "decline"}`, dispatch at `2026-04-28T16:01:39Z`); L3 `op: mark_resolved` (resolved at same timestamp). **Request 1 (`file_change`):** L4 `op: create` (raw_request_id `1`, item_id `call_pOFm3u5VSxTzScon0z1IZDxr`, **same codex_thread_id and codex_turn_id as req 0**, available_decisions `[]` empty, requested_scope `{grantRoot: null, reason: null}`); L5 `op: record_response_dispatch` (resolution_action `deny`, response_payload `{"decision": "decline"}`, dispatch at `2026-04-28T16:02:47Z`); L6 `op: mark_resolved`. **Notable findings:** (a) internal `deny` action maps to wire-level `decline` decision; (b) **both requests originate from the same Codex turn** — agent's adaptation after deny stays within one turn; (c) request 1's `available_decisions: []` is anomalous (empty list); (d) request 1's `raw_request_id` is unquoted JSON int per JSON-RPC wire convention. |
| DelegationJobStore rows inspected | Record job id and matching JSONL line numbers. | File: `~/.claude/plugins/data/codex-collaboration-inline/delegation_jobs/7337aa50-e517-44f7-8793-eebb3f0fe3db/jobs.jsonl` (12 lines, all scoped to `job_id: 6753a537-99d8-456f-a1c0-1c79f13a2fc9`). Lifecycle trail: L1 `op: create` (status `queued`, base_commit `7650366d778c961226f95efcf4ea40efa5fe2567`, runtime_id `c72e440a-d4d2-4e8d-9fb8-1f7c2bdc4017`, collaboration_id `3fd2722e-0b53-4a51-97c1-ab5b834164d8`); L2 status `running`; L3 parked_request_id `0`; L4 status `needs_escalation`; **L5 status `running` (after deny req 0)**; L6 parked_request_id null; **L7 parked_request_id `1`**; L8 status `needs_escalation` (req 1); **L9 status `running` (after deny req 1)**; L10 parked_request_id null; **L11 status `completed`, promotion_state `pending`**; L12 `op: update_artifacts` (artifact_hash `d604766ea0e6f7d82c1f37f5b66d10d985cfd0271b01f3a7491ceb8f167d7b8d`, 3 inspection artifact paths). State machine: queued → running → escalated × 2 (with running interludes between denies) → completed. Job left at `promotion_state: pending` per session decision (audit-trail preservation; not promoted, not discarded). |
| OperationJournal rows inspected | Record job/request id and matching JSONL line numbers. | File: `~/.claude/plugins/data/codex-collaboration-inline/journal/operations/7337aa50-e517-44f7-8793-eebb3f0fe3db.jsonl` (9 lines). Three operations × three phases each (intent / dispatched / completed). **Op 1 — `job_creation`** (idempotency_key `7337aa50-...:90eeb685...`): L1 phase intent (`2026-04-28T15:53:34Z`, repo_root captured); L2 phase dispatched (codex_thread_id `019dd4cb-c1e6-7900-8c3e-4accda600d8c` and runtime_id populated, same timestamp); L3 phase completed (same timestamp). **Op 2 — `approval_resolution`** (idempotency_key `approval_resolution:6753a537-...:0`, request_id `"0"`, decision `deny`): L4 intent at `2026-04-28T16:01:39Z`; L5 dispatched at same time (codex_thread_id populated for traceability); L6 completed (`completion_origin: worker_completed`). **Op 3 — `approval_resolution`** (idempotency_key `approval_resolution:6753a537-...:1`, request_id `"1"`, decision `deny`): L7-L9 same three-phase pattern at `2026-04-28T16:02:47Z`. All three operations completed cleanly (no `dispatch_error`/`interrupt_error` rows). |
| Audit rows inspected | Required if dispatch failure / timeout / decision audit relevant; else "not applicable". | File: `~/.claude/plugins/data/codex-collaboration-inline/audit/events.jsonl` (single file shared across sessions; 64 lines at this session's inspection). Three rows scoped to this job (via `grep 6753a537 audit/events.jsonl`): **L62** `action: delegate_start`, actor `claude`, event_id `53c0930a-468c-40c4-ab3b-7704552816a3`, timestamp `2026-04-28T15:53:37Z` — **independent timestamp cross-check**: matches runtime-proof artifact's emit timestamp `2026-04-28T15:53:37.116985+00:00` to sub-second precision; **L63** `action: deny`, actor `claude`, request_id `"0"`, event_id `a72c3783-29d7-4028-8876-23e4d7bf101e`, timestamp `2026-04-28T16:01:39Z`; **L64** `action: deny`, actor `claude`, request_id `"1"`, event_id `fb8bf569-bf86-4cd8-a601-99240fbb5ce2`, timestamp `2026-04-28T16:02:47Z`. All three rows: `policy_fingerprint: null`, `extra: {}`, `actor: claude`. Confirms both denies dispatched cleanly under this orchestrator's actor identity. |
| Network probe result | Required for candidate policy variants. | not applicable: Baseline (no candidate policy under test). |
| Sensitive-path probe result | Required for candidate policy variants. | not applicable: Baseline. |
| Sibling-worktree probe result | Required if a sibling worktree exists; otherwise record absence. | not applicable: no sibling worktrees observed (Baseline was the first delegate run after a fresh restart; `<plugin_data_root>/runtimes/delegation/` contained only this job's worktree at run-start). |
| Post-run HEAD | `git rev-parse --short HEAD` after the run. Must equal pre-run HEAD unless commits landed. | `7650366d` (unchanged from pre-run; equality preserved as expected — no commits landed during the variant). |
| Post-run dirty diff | `git status --short` after the run. Should show only the variant patch's known modifications + intentional smoke artifact paths. | **Tracked changes:** `M packages/plugins/codex-collaboration/server/runtime.py` (runtime-proof instrumentation patch, byte-identical to `.tmp/variant-baseline.patch` — verified post-run via `diff <(git diff ...) .tmp/variant-baseline.patch` → empty output) + `M docs/diagnostics/2026-04-28-delegate-execution-diagnostic.md` (this run record's evidence-capture edits, intentional and uncommitted). **Carry-forward unrelated to variant** (unchanged from pre-run): 8 ticket-file moves under `docs/tickets/closed-tickets/`; untracked `.tmp/variant-baseline.patch` and `.tmp/variant-baseline.applied-at`. **Net assessment:** post-run state matches pre-run state for variant-relevant paths; no smoke artifact created (sandbox + deny prevented all writes). |
| Variant restoration command | Skip for Baseline. | not applicable: Baseline (no behavioral patch). **Runtime-proof-only instrumentation restoration** (per VIP step 7): `git checkout -- packages/plugins/codex-collaboration/server/runtime.py` + `trash /tmp/codex-collab-baseline-runtime-proof.log`. Followed by a second Claude Code restart so the next variant observes the restored code. |
| Restoration verification | `git status --short` after restoration; must match pre-run dirty diff. | **Verified post-restoration this session.** `git diff packages/plugins/codex-collaboration/server/runtime.py`: empty output (no diff). `git status --short` for the patched path: no `M` row. `runtime.py:23-38` `build_workspace_write_sandbox_policy` body re-reads as pre-patch shape (`return {...}` direct return, no `policy = {...}` extraction, no instrumentation block) — confirmed by reading restored file lines 23-38. **Disk restoration ✓.** **Memory restoration NOT yet complete:** the running plugin process (python child PID `11696`, started `2026-04-28T15:41:29Z` UTC — corrected; see "Plugin process start timestamp" field for the macOS `date -u -j -f` pitfall) still holds the patched code in memory due to Python import-once semantics. Per VIP step 7 final sentence, a second Claude Code restart is required before Candidate A so the next variant observes the restored code, not the patched code still in memory. |
| Cleanup performed | Record command or "deferred". | **Performed this session.** Commands: (1) `git checkout -- packages/plugins/codex-collaboration/server/runtime.py` (restores patched file; exit 0). (2) `trash /tmp/codex-collab-baseline-runtime-proof.log` (clears runtime-proof artifact via macOS Trash per project rule "no `rm`"; exit 0). Verification: `ls /tmp/codex-collab-baseline-runtime-proof.log` returns "No such file or directory" ✓. **Store inspection completed this session** (see PendingRequestStore / DelegationJobStore / OperationJournal / Audit rows above for full row-level evidence). **Intentionally preserved** (not cleaned up): the underlying JSONL files (audit trail for the full diagnostic across all variants) and the job's worktree + inspection artifacts at `~/.claude/plugins/data/codex-collaboration-inline/runtimes/delegation/6753a537-99d8-456f-a1c0-1c79f13a2fc9/` (job left at `promotion_state: pending` — not promoted, not discarded — for cross-variant correlation). |

Runtime-proof-only instrumentation patch (semantics-preserving — does not modify the returned `policy` dict; adds a file-write emit immediately before `return policy`):

```diff
diff --git a/packages/plugins/codex-collaboration/server/runtime.py b/packages/plugins/codex-collaboration/server/runtime.py
index 9f28e0b0..d8f0e032 100644
--- a/packages/plugins/codex-collaboration/server/runtime.py
+++ b/packages/plugins/codex-collaboration/server/runtime.py
@@ -24,7 +24,7 @@ def build_workspace_write_sandbox_policy(worktree_path: Path) -> dict[str, Any]:
     """Return the v1 execution sandbox policy for an isolated worktree."""
 
     resolved = worktree_path.resolve()
-    return {
+    policy = {
         "type": "workspaceWrite",
         "writableRoots": [str(resolved)],
         "readOnlyAccess": {
@@ -36,6 +36,18 @@ def build_workspace_write_sandbox_policy(worktree_path: Path) -> dict[str, Any]:
         "excludeSlashTmp": True,
         "excludeTmpdirEnvVar": True,
     }
+    # variant instrumentation (remove after diagnostic)
+    from datetime import datetime, timezone
+    from pathlib import Path as _Path
+
+    with _Path("/tmp/codex-collab-baseline-runtime-proof.log").open(
+        "a", encoding="utf-8"
+    ) as _handle:
+        _handle.write(
+            f"{datetime.now(timezone.utc).isoformat()} "
+            f"[BASELINE] sandboxPolicy={policy!r}\n"
+        )
+    return policy
 
 
 class AppServerRuntimeSession:
```

Attempt history:

| Attempt | Reason started | Shell-visible actions | Outcome | Preserved evidence |
|---:|---|---:|---|---|
| 1 | Initial Baseline run; capture-and-stop on file-sink runtime-proof per VIP step 4. | 2 attempted (1 chained `/bin/zsh -lc` shell + 1 `file_change`); 0 executed (both denied at approval gate). | Job finalized as `completed`/`promotion_state: pending` after both denies; smoke artifact NOT produced (sandbox blocked first command pre-execution; no shell ran). Branch S1 (Sandbox still blocked) classified per Branch decision below. | Per-variant Baseline block above (filled); JSONL refs in store-rows fields (jobs.jsonl L1-12, requests.jsonl L1-6, journal L1-9, audit L62-64); inspection artifacts at `~/.claude/plugins/data/codex-collaboration-inline/runtimes/delegation/6753a537-99d8-456f-a1c0-1c79f13a2fc9/inspection/` (full.diff empty, changed-files.json `[]`, framework's test-results.json status `not_recorded`); runtime-proof artifact line preserved verbatim in "Observed sandboxPolicy payload" field above (source file at `/tmp/codex-collab-baseline-runtime-proof.log` intentionally trashed during cleanup). |

Raw excerpts:

```text
=== codex_delegate_start response (parked at request 0) ===
{
  "job": {
    "job_id": "6753a537-99d8-456f-a1c0-1c79f13a2fc9",
    "runtime_id": "c72e440a-d4d2-4e8d-9fb8-1f7c2bdc4017",
    "collaboration_id": "3fd2722e-0b53-4a51-97c1-ab5b834164d8",
    "base_commit": "7650366d778c961226f95efcf4ea40efa5fe2567",
    "worktree_path": ".../runtimes/delegation/6753a537-.../worktree",
    "status": "needs_escalation",
    "parked_request_id": "0",
    "promotion_state": null,
    "promotion_attempt": 0,
    "artifact_paths": [],
    "artifact_hash": null
  },
  "pending_escalation": {
    "request_id": "0",
    "kind": "command_approval",
    "requested_scope": {
      "command": "/bin/zsh -lc \"...\" (full chained command — 9 && -joined steps;
                 see PendingRequestStore L1 for the literal scope string)"
    },
    "available_decisions": ["approve", "deny"]
  },
  "escalated": true
}

=== codex_delegate_decide(deny, request 0) response ===
{ "decision_accepted": true, "job_id": "6753a537-...", "request_id": "0" }

=== codex_delegate_poll #1 (post-deny req 0) ===
{
  "job": { ..., "status": "running", "parked_request_id": null },
  "pending_escalation": null,
  "inspection": null,
  "detail": null
}

=== codex_delegate_poll #2 (req 1 surfaced) ===
{
  "job": { ..., "status": "needs_escalation", "parked_request_id": "1" },
  "pending_escalation": {
    "request_id": "1",
    "kind": "file_change",
    "requested_scope": { "grantRoot": null, "reason": null },
    "available_decisions": ["approve", "deny"]
  }
}

=== codex_delegate_decide(deny, request 1) response ===
{ "decision_accepted": true, "job_id": "6753a537-...", "request_id": "1" }

=== codex_delegate_poll #3 (terminal) ===
{
  "job": {
    ...,
    "status": "completed",
    "parked_request_id": null,
    "promotion_state": "pending",
    "artifact_paths": [
      ".../inspection/full.diff",
      ".../inspection/changed-files.json",
      ".../inspection/test-results.json"
    ],
    "artifact_hash": "d604766ea0e6f7d82c1f37f5b66d10d985cfd0271b01f3a7491ceb8f167d7b8d"
  },
  "pending_escalation": null,
  "inspection": {
    "artifact_hash": "d604766e...",
    "artifact_paths": [...],
    "changed_files": [],
    "reviewed_at": "2026-04-28T16:02:51Z"
  }
}

=== Runtime-proof artifact (source file trashed; line preserved here) ===
2026-04-28T15:53:37.116985+00:00 [BASELINE] sandboxPolicy={
  'type': 'workspaceWrite',
  'writableRoots': ['<worktree>'],
  'readOnlyAccess': {
    'type': 'restricted',
    'readableRoots': ['<worktree>'],
    'includePlatformDefaults': False
  },
  'networkAccess': False,
  'excludeSlashTmp': True,
  'excludeTmpdirEnvVar': True
}

=== Inspection artifacts (framework-generated; preserved at job worktree path) ===
full.diff: empty (zero bytes)
changed-files.json: {"changed_files": []}
test-results.json:
  {
    "commands": [],
    "schema_version": 1,
    "source_path": ".codex-collaboration/test-results.json",
    "status": "not_recorded",
    "summary": "Execution agent did not persist test results."
  }

=== Cross-store timestamp consistency (independent sources, all UTC) ===
Plugin process start (corrected via ps lstart epoch round-trip): 2026-04-28T15:41:29Z
delegate_start audit row (events.jsonl L62):                    2026-04-28T15:53:37Z   (+12m08s)
runtime-proof artifact emit (Python datetime.now(timezone.utc)): 2026-04-28T15:53:37.116985+00:00  (matches audit row to sub-second)
First deny dispatch req 0 (audit L63 + journal L5):              2026-04-28T16:01:39Z   (+8m02s)
Second deny dispatch req 1 (audit L64 + journal L8):             2026-04-28T16:02:47Z   (+1m08s)
Inspection reviewed_at:                                          2026-04-28T16:02:51Z   (+04s)
Total job duration (delegate_start → reviewed_at):              ~9m14s
```

### Variant: Candidate A (attempt 1)

Pre-execution cells filled immediately after pre-flight verification (this session, before invoking `codex_delegate_start`). Post-execution cells marked `TBD (post-execution …)` will be filled in the same session immediately after the variant runs and the runtime-proof artifact is read. Tightenings carried forward from Baseline (python child PID labelled evidentiary; `Plugin process start timestamp` records both raw `lstart` and normalized UTC via the macOS-correct epoch round-trip; explicit `Patch applied at` for the `Patch applied at < Plugin process start timestamp` ordering invariant). This-variant-only additions: behavioral patch is the `includePlatformDefaults: False → True` flip on top of the runtime-proof-only instrumentation overlay; instrumentation uses `[CANDIDATE_A]` label and distinct log file `/tmp/codex-collab-candidate-a-runtime-proof.log` (per D5 in the handoff: cross-variant isolation); plugin `session_id` cross-check added as restart/isolation evidence.

| Field | Source / fill guidance | Observation |
|---|---|---|
| Pre-run HEAD | `git rev-parse --short HEAD` immediately before applying the variant patch. | `5a1e937e` (verified live this session via `git rev-parse HEAD` → `5a1e937eff04f4cfecf5ce7bc65fae1f94db0fca`; matches handoff's recorded HEAD; matches the two-layer HEAD anchor pattern — Run Identity remains frozen at `49d93001` as the run-level snapshot). |
| Pre-run dirty diff | `git status --short` before patch; must show no modifications to files the patch will touch. | **Pre-patch (last session, before `2026-04-28T17:12:59Z`):** clean for `packages/plugins/codex-collaboration/server/runtime.py` (Baseline restoration confirmed at end of prior session per Baseline's "Restoration verification" cell; verified again post-restart this session via "Pre-run dirty diff" expectation). **Current (immediately before `codex_delegate_start`):** `M packages/plugins/codex-collaboration/server/runtime.py`; byte-identical to `.tmp/variant-candidate-a.patch` (verified this session via `diff <(git diff packages/plugins/codex-collaboration/server/runtime.py) .tmp/variant-candidate-a.patch` → empty output, exit 0). **Carry-forward unrelated to variant:** 8 ticket-file moves under `docs/tickets/closed-tickets/` (8 `D` + 8 `??` rows; same set as Baseline); untracked `.tmp/variant-candidate-a.patch`, `.tmp/variant-candidate-a.applied-at`, and `.tmp/app-server-schema-pre-candidate-a/` (all gitignored per `.gitignore:51`). |
| Patch capture form | One of: inline diff, `.tmp/variant-<name>.patch`, or throwaway-branch commit SHA. | `.tmp/variant-candidate-a.patch` (37 lines; sha256 `4df1df3999b4914978fb0cf7582418cfd65377f36e4e45942983191d75fa2bf8`; gitignored per `.gitignore:51`). Inline reproduction in code block immediately after this table. |
| Patch applied at | Required for Candidate variants; ISO-8601 UTC timestamp captured immediately after applying the patch. | `2026-04-28T17:12:59Z` (recorded in `.tmp/variant-candidate-a.applied-at`; sha256 `bf897498bb2fa7159fcb1b33e7d75e79a2817f786acbc2ae77eb8d2be1baf9cb`). Captured via `printf "Patch applied at: %s\n" "$(date -u +'%Y-%m-%dT%H:%M:%SZ')"` — the SAFE emission recipe (no input parsing → no relabel risk; distinct from the parsing-mode trap fixed in commit `c704eafa`). The single timestamp covers BOTH the behavioral patch (`includePlatformDefaults: False → True` flip) AND the runtime-proof-only instrumentation overlay (one composite edit). |
| Policy diff / patch under test | Inline `git diff` of the variant patch, or "current code (no patch)" for Baseline. | **Behavioral patch (Candidate A under test):** single-line change — `"includePlatformDefaults": False` → `"includePlatformDefaults": True` at `runtime.py:33`. Variant hypothesis: enabling platform defaults grants `/bin`, `/usr/bin`, `/usr/lib` reachability so `/bin/zsh -lc` can execute under `workspaceWrite` policy; expected outcome — Branch S1 stops firing, smoke artifact production succeeds. **Runtime-proof-only instrumentation overlay** (semantics-preserving; does not alter the returned `policy` dict): parallel structure to Baseline's instrumentation pattern with `[CANDIDATE_A]` label and `/tmp/codex-collab-candidate-a-runtime-proof.log` target (per handoff D5: distinct log file per variant for cross-variant isolation — prevents stale-Baseline-content contamination). Combined diff in code block immediately after this table. |
| Plugin process PID (post-restart) | PID of the plugin/MCP process **after** restart. | **Python child PID `64213`** (evidentiary — this is the import holder that re-read `runtime.py` post-restart). uv wrapper PID `64184` (parent of python child). claude PID `64122` (grandparent). All three differ from prior session's `7116/7163/7165` ✓ — restart confirmed. Verified via `ps -ef \| grep codex-collaboration \| grep -v grep` (note: `pgrep -fa <pattern>` matches its own argv per gotcha discovered last session, so plain `ps -ef \| grep \| grep -v grep` is the more robust idiom). **Plugin `session_id` cross-check (restart/isolation evidence):** `<plugin-data-root>/session_id` reads `15267690-603e-4715-be76-9c90ba41007a`, matching THIS Claude Code session id (the load skill at session start substituted the same UUID); flipped from prior session's `801b6646-171e-4a80-a647-c9de35041d4c` ✓. Confirms the plugin process is bound to this conversation's identity, not a stale-process artifact. |
| Plugin process start timestamp | ISO-8601 UTC of post-restart process start. State which form was used. Must be later than `Patch applied at` for variant validity. | **Raw `ps -p 64213 -o lstart=` output:** `Tue Apr 28 13:24:44 2026` (local timezone EDT — verified `date +"%Z (%z)"` returns `EDT (-0400)` this session; format `%a %b %d %H:%M:%S %Y` with no zone marker; trailing 4 spaces from `ps` column-padding produce a benign `date -j` warning "Ignoring 4 extraneous characters" but parse succeeds because `%Y` consumes exactly 4 digits and the extra whitespace is unconsumed). **Normalized UTC: `2026-04-28T17:24:44Z`** (via macOS-correct epoch round-trip: `EPOCH=$(date -j -f "%a %b %d %H:%M:%S %Y" "<lstart>" +%s)` then `date -u -r "$EPOCH" +"%Y-%m-%dT%H:%M:%SZ"`; verified epoch `1777397084`). The macOS pitfall recipe (`date -u -j -f FMT INPUT +OUTFMT`) was NOT used — see Baseline block for the documented incident and `c704eafa` commit message; this session's earlier learning on emission-vs-parsing distinction (`date -u +FORMAT` is SAFE for emission; only `-j -f` parsing has the trap) reinforced via `2026-04-28T17:12:59Z` patch-applied capture earlier in this run. **Ordering check (using corrected UTC):** plugin start `2026-04-28T17:24:44Z` > patch applied `2026-04-28T17:12:59Z` ✓ — plugin started **+705s (11m45s)** after patch was applied. Variant valid; running plugin re-imported the patched module. **Cross-check via runtime-proof artifact emit:** `2026-04-28T17:51:27.685062+00:00` (Python `datetime.now(timezone.utc).isoformat()` from first delegate call's emit; +1603s after plugin start `17:24:44Z`; matches audit `delegate_start` row at `17:51:27Z` to sub-second precision; cross-confirms plugin start UTC was correct and the running plugin re-imported the patched module). |
| Observed `sandboxPolicy` payload | Direct evidence the live runtime built the patched policy. Inference from on-disk source NOT acceptable. | **Observed verbatim** (1 line at `/tmp/codex-collab-candidate-a-runtime-proof.log`, 533 bytes; preserved here before source file is trashed before attempt 2):<br>`2026-04-28T17:51:27.685062+00:00 [CANDIDATE_A] sandboxPolicy={'type': 'workspaceWrite', 'writableRoots': ['/Users/jp/.claude/plugins/data/codex-collaboration-inline/runtimes/delegation/4ebd24d6-6f1f-45b8-99eb-0d890a9d5326/worktree'], 'readOnlyAccess': {'type': 'restricted', 'readableRoots': ['/Users/jp/.claude/plugins/data/codex-collaboration-inline/runtimes/delegation/4ebd24d6-6f1f-45b8-99eb-0d890a9d5326/worktree'], 'includePlatformDefaults': True}, 'networkAccess': False, 'excludeSlashTmp': True, 'excludeTmpdirEnvVar': True}`<br>**Falsification result:** PASSED — `'includePlatformDefaults': True` confirmed at the build site; the running plugin DID re-import the patched module (refutes the alternative explanation that PID + start-time evidence was insufficient). **Load-bearing observation:** disambiguates 'plugin built wrong policy' from 'App Server interprets True restrictively'. **What this proves:** the plugin emits `True`. **What this does NOT prove:** that shell execution succeeds under the platform-defaults grant — that test requires approval to land, which did not happen in attempt 1 (see `poll() transitions` cell below for the canceled-by-timeout flow). |
| Runtime-proof method | Which observation form was used. | Patch-embedded log emit at `runtime.py:23-50` build site; file-write to `/tmp/codex-collab-candidate-a-runtime-proof.log` (per handoff D5: distinct from Baseline's `/tmp/codex-collab-baseline-runtime-proof.log`). Stderr/stdout/logger explicitly invalid in current launch mode (FD 2 routing finding documented in VIP step 4). **Pre-execution log absence verified this session:** `ls /tmp/codex-collab-candidate-a-runtime-proof.log` returns "No such file or directory" → first execution will be a clean append (no stale-content contamination from any prior Candidate A attempt). |
| Approval policy value | Controller/runtime input for this run. | **Confirmed `untrusted`** via PendingRequestStore L1 `available_decisions` field — full 6-option list `['accept', 'acceptForSession', 'acceptWithExecpolicyAmendment', 'applyNetworkPolicyAmendment', 'decline', 'cancel']` — matches Baseline's `untrusted`-mode signature exactly. The wire-surface `pending_escalation.available_decisions` returned to the orchestrator was 2-option `['approve', 'deny']` (per Baseline's documented wire-vs-store gotcha; same pattern observed here). **Use the store record (PendingRequestStore L1) for S7 amendment classification, not the wire surface.** |
| Job id | `start()` response, `poll()` output, or `DelegationJobStore` row. | `4ebd24d6-6f1f-45b8-99eb-0d890a9d5326` (from `start()` response; also captured in DelegationJobStore L1 `op: create` row at `<plugin-data-root>/delegation_jobs/15267690-…/jobs.jsonl:1`). Companion identifiers: `runtime_id: 84fce58f-c860-4757-a852-6f30c3d21ddf`; `collaboration_id: 9a8a1a64-65b7-4884-b34e-85dad62b9b94`; `base_commit: 5a1e937eff04f4cfecf5ce7bc65fae1f94db0fca` (matches pre-run HEAD ✓); `worktree_path: <plugin-data-root>/runtimes/delegation/4ebd24d6-…/worktree`. |
| First parked request id | Required if any escalation occurs. | `"0"` (string in store; `raw_request_id: 0` integer at the wire). Recorded in PendingRequestStore L1 (`op: create`, `kind: command_approval`) and in DelegationJobStore L3 (`op: update_parked_request, parked_request_id: "0"`). **The escalation DID fire** — refutes the alternative outcome of `no escalation observed` under True flag (which would have indicated S1 stopped firing). **Load-bearing evidence for the mechanism revision:** approval gating still fired under the True policy *before any shell execution*, so sandbox readability is *not proven* as the cause of parking. (Source-level ordering inside App Server — whether the approval gate runs literally before the sandbox-readability check, or in parallel, or some other arrangement — is not established by these observations alone; that would require an approve-path run or App Server source inspection.) |
| JSON-RPC wire id type | Required if a parked request exists. | Integer (`raw_request_id: 0` in PendingRequestStore L1). String form (`request_id: "0"`) is the in-store representation; integer is the wire form. Matches Baseline pattern. |
| `shell_action_count` | Count shell commands/file-change actions for the smoke objective. | **`1` attempted** as a compressed `&&`-chained command (see PendingRequestStore L1 `requested_scope.command` for the full chain — same compression pattern as Baseline incl. the `.codex-collaboration/test-results.json` over-action). **`0` executed** — request 0 was parked at `command_approval`, then canceled by `approval_timeout` before any shell process ran. Per template + Baseline (line 645) denominator semantics: shell_action_count counts attempted shell/file-change actions. Per Branch Precedence #1.d: attempted denominator < 3 ⇒ ratio uninterpretable for primary signal. |
| `approval_request_count` | Required if `shell_action_count >= 3`. | `1` (only request `0`). Did not reach the deny→adapt→request-1 cycle that Baseline observed, because the deny adjudication never landed: the job canceled by approval timeout (audit L66 `action=approval_timeout actor=system`) before the operator-mediated decide arrived. PendingRequestStore L2 (`op: record_timeout`) shows the system-initiated termination of request 0; no request 1 was ever created. |
| Approval request kinds | Required if requests occur. | `command_approval` (request 0; PendingRequestStore L1 `kind: command_approval`, `requested_scope.command: /bin/zsh -lc <chain>`). Same kind as Baseline's request 0. **No `file_change` (or any other kind) surfaced** — those would have followed only if the deny→adapt cycle had run, which it could not, because the approval gate flow was terminated by timeout. |
| `approval_request_count / shell_action_count` | Required if denominator is nonzero; else `no signal`. | **`1 / 1` = `1.0`** (1 approval request for 1 attempted action; per template + Baseline denominator semantics — denominator counts attempted actions, not executed actions). **No threshold signal** because: (a) attempted denominator < 3 per Branch Precedence #1.d, AND (b) zero actions executed (so the ratio reflects only the gate-blocking shape, not any execution-side ratio dynamics). Cannot serve as the calibration anchor because no successful baseline-equivalent execution occurred — calibration anchoring is deferred to a future Candidate A attempt where shell DOES execute past the gate (e.g., attempt 2 with approve-strategy if approve lands within the TTL window). |
| Command stdout/stderr summary | Tool result or run transcript. | **Not applicable** — no shell process was ever spawned. The delegate's `requested_scope.command` was parked at `command_approval` and then canceled by `approval_timeout` (audit L66, +15m10s after start) before any execution. No stdout, stderr, or exit codes exist for this attempt. |
| Exit statuses | Tool result or run transcript. | **Not applicable** — see `Command stdout/stderr summary` above. No process was spawned; no exit status was produced. |
| `decide(approve)` response payload | Required if approval requested. | **Not applicable** — no `decide(approve)` was issued in attempt 1. The operator chose `decide(deny)` to mirror Baseline (per handoff D4); the deny call was rejected with `{"rejected": true, "reason": "job_not_awaiting_decision", "detail": "Delegation decide failed: job not awaiting decision. Got: status='canceled'"}` because the job had already canceled by `approval_timeout`. **Note: Candidate A's `decide(approve)` test is the load-bearing experiment for the next attempt** (attempt 2) — it is the only way to determine whether shell execution succeeds past the gate under the True policy. |
| `poll()` transitions | Timed `poll()` outputs after start (and after decide if applicable). | **Two snapshots only** (deny adjudication failed, so no poll between deny and final state):<br>**t0 (post-`start()` synchronous return, ~17:51:27Z):** `status: needs_escalation`, `parked_request_id: "0"`, `pending_escalation.kind: command_approval`, `pending_escalation.requested_scope.command: /bin/zsh -lc <chain>`, `pending_escalation.available_decisions: ["approve", "deny"]` (wire-surface 2-option; store has full 6-option list per `Approval policy value` cell).<br>**t1 (post-rejected-`decide(deny)`, ~18:06+Z):** `status: canceled`, `pending_escalation: null`, `inspection: null`. **Did not mirror Baseline's parked-on-0 → deny → parked-on-1 → deny → completed pattern** because the deny→adapt cycle could not initiate — the underlying request 0 had been canceled by system-driven `approval_timeout` before deny landed (full lifecycle in DelegationJobStore: queued → running → parked(0) → needs_escalation → running [post-timeout unpark] → parked(cleared) → canceled). |
| `full.diff` summary | Required if artifact production succeeds. | **Not applicable for attempt 1** — no execution reached this stage; no artifacts were produced.<br>**Pre-execution falsification framing recorded in this cell is invalidated by the mechanism revision from attempt 1.** The pre-execution framing was: `empty file ⇒ Branch S1 still primary`. That inference assumed parking signaled sandbox blockage. Attempt 1 demonstrated that approval gating still fired under the True policy *before any shell execution* (parking observed even with `'includePlatformDefaults': True`, runtime-proofed at the build site), so sandbox readability is *not proven* as the cause of parking — and therefore absent artifact production *cannot* be attributed to S1 from these observations alone. **Branch decision adjudication for Candidate A overall is deferred** — requires attempt 2 (approve-strategy) to provide downstream evidence on whether shell execution succeeds past the gate under the True policy. **Do NOT update Branch Precedence rows or Symptom Attribution rows on attempt 1 alone.** |
| `changed_files` | Required if artifact production succeeds. | **Not applicable** — see `full.diff summary` above. No execution; no changed files. |
| Artifact hash | Required if artifact production succeeds. | **Not applicable** — see `full.diff summary` above. No artifacts; no hash. (DelegationJobStore L1 `artifact_hash: null` and `artifact_paths: []` confirm no artifacts at job creation; no later row populated these fields.) |
| PendingRequestStore rows inspected | Required if any request id exists. | **2 rows** at `~/.claude/plugins/data/codex-collaboration-inline/pending_requests/15267690-603e-4715-be76-9c90ba41007a/requests.jsonl`:<br>**L1 (`op: create`, request shape — cite for shape/policy classification only, NOT as terminal status):** `kind: command_approval`, `request_id: "0"`, `raw_request_id: 0`, `available_decisions: [accept, acceptForSession, acceptWithExecpolicyAmendment, applyNetworkPolicyAmendment, decline, cancel]` (full 6-option `untrusted`-mode list), `requested_scope.command: /bin/zsh -lc <full chain>`, `codex_thread_id: 019dd537-a39b-…`, `codex_turn_id: 019dd537-a7cd-…`, `item_id: call_6DhsxENd5OlrBWOt95bAzWH5`. (L1's implicit state is `pending` — but the request is no longer pending in reality; use L2 for terminal state.)<br>**L2 (`op: record_timeout`, terminal state):** `status: canceled`, `dispatch_result: succeeded`, `response_payload: {decision: cancel}` (synthetic `cancel` payload fabricated by the system to terminate the request via the same code path that handles operator decides), `response_dispatch_at: 2026-04-28T18:06:37Z`, `timed_out: true`. **Cross-store cross-check:** L2's `response_dispatch_at: 18:06:37Z` matches audit L66 `approval_timeout actor=system ts=18:06:37Z` to second precision. Baseline's stores at `pending_requests/7337aa50-…/` remain untouched for cross-variant correlation. |
| DelegationJobStore rows inspected | Record job id and matching JSONL line numbers. | **7 rows** at `~/.claude/plugins/data/codex-collaboration-inline/delegation_jobs/15267690-603e-4715-be76-9c90ba41007a/jobs.jsonl` (full lifecycle for job `4ebd24d6-…`; canonical terminal-state source per user guardrail):<br>L1: `op: create`, `status: queued`, `parked_request_id: null`, `base_commit: 5a1e937e…`, `worktree_path: <plugin-data-root>/runtimes/delegation/4ebd24d6-…/worktree`, `artifact_hash: null`, `artifact_paths: []`, `runtime_id: 84fce58f-…`, `collaboration_id: 9a8a1a64-…`<br>L2: `op: update_status_and_promotion`, `status: running`<br>L3: `op: update_parked_request`, `parked_request_id: "0"` (job parks on request 0)<br>L4: `op: update_status_and_promotion`, `status: needs_escalation`<br>L5: `op: update_status_and_promotion`, `status: running` (post-timeout unpark — graceful unblock, NOT direct cancel-from-parked)<br>L6: `op: update_parked_request`, `parked_request_id: null` (park cleared)<br>L7: `op: update_status_and_promotion`, `status: canceled` (terminal). **Lifecycle pattern observation:** approval_timeout is a graceful unblock-then-cancel flow (parked → running → cleared → canceled) rather than abrupt cancel-from-parked. Suggests App Server returns the request unresolved on timeout, plugin clears park state, then transitions job to canceled. |
| OperationJournal rows inspected | Record job/request id and matching JSONL line numbers. | **6 rows** at `~/.claude/plugins/data/codex-collaboration-inline/journal/operations/15267690-603e-4715-be76-9c90ba41007a.jsonl` (3287 bytes), grouped as two operations of 3 phases each:<br>**L1-L3: `operation: job_creation`** (`phase: intent → dispatched → completed`), all at `created_at: 2026-04-28T17:51:25Z` (2s before audit `delegate_start` at 17:51:27Z; the journal records the orchestrator-side intent before the audit-side dispatch). `decision: None`, `request_id: None`. Idempotency key: `15267690-…:ee9…`.<br>**L4-L6: `operation: approval_resolution`** (`phase: intent → dispatched → completed`), all at `created_at: 2026-04-28T18:06:37Z` (matches audit `approval_timeout` and PendingRequestStore L2 `response_dispatch_at` to second precision). `decision: None` ← **noteworthy:** the journal does NOT record the synthetic `cancel` decision payload that PendingRequestStore L2 captured. The journal's `decision: None` for system-initiated approval_resolution is the signature distinguishing it from claude-initiated approve/deny flows (which would carry a non-null decision). Idempotency key: `approval_resolution:4ebd24d6-…`. `request_id: 0`. |
| Audit rows inspected | Required if dispatch failure / timeout / decision audit relevant; else "not applicable". | **2 rows** at `~/.claude/plugins/data/codex-collaboration-inline/audit/events.jsonl` for job `4ebd24d6-…` (canonical terminal-state source per user guardrail; co-canonical with DelegationJobStore for terminal status):<br>**L65 (delegate_start):** `action: delegate_start`, `actor: claude`, `timestamp: 2026-04-28T17:51:27Z`, `request_id: None`, `job_id: 4ebd24d6-…`. Aligns with `start()` synchronous return time and runtime-proof emit (17:51:27.685062Z).<br>**L66 (approval_timeout):** `action: approval_timeout`, `actor: system`, `timestamp: 2026-04-28T18:06:37Z`, `request_id: 0`, `job_id: 4ebd24d6-…`. **Delta = exactly 15m10s after delegate_start** — the load-bearing TTL discovery. `actor: system` distinguishes lifecycle automation from `actor: claude` (orchestrator-initiated `delegate_start`/`decide`); useful for filtering audit by 'what the operator did' vs 'what the system did automatically'. |
| Network probe result | Required for candidate policy variants. Record command and result. | **Not run in attempt 1; deferred because request 0 timed out before operator decision** ⇒ no shell process inside the worktree could be issued. The plan recorded pre-execution above (curl reachability under `networkAccess: False`) **remains Candidate A closure work** and will be exercised in attempt 2 if approve lands within the TTL window. **This cell remains REQUIRED for Candidate A overall** — closure is incomplete on attempt 1 alone. |
| Sensitive-path probe result | Required for candidate policy variants. Cross-reference Host-Side Probe Baselines. | **Not run in attempt 1; deferred because request 0 timed out before operator decision** ⇒ no shell process inside the worktree could read `/etc/passwd` or any other sensitive path. Plan recorded pre-execution **remains Candidate A closure work**. **REQUIRED for Candidate A overall** — closure incomplete on attempt 1 alone. |
| Sibling-worktree probe result | Required if a sibling worktree exists; otherwise record absence. | **Not run in attempt 1; deferred because request 0 timed out before operator decision** ⇒ no shell process to issue the cross-worktree access probe. Sibling worktrees on disk at run-start: Baseline's `6753a537-…/worktree` (pending promotion, intentionally preserved per Baseline VIP step 7) AND now Candidate A att1's `4ebd24d6-…/worktree` (created at job init, never executed in). Probe plan applies to attempt 2 if approve lands. **Closure work for Candidate A overall.** |
| Post-run HEAD | `git rev-parse --short HEAD` after the run. Must equal pre-run HEAD unless commits landed. | `5a1e937e` (verified at this session's pre-flight via `git rev-parse HEAD → 5a1e937eff04f4cfecf5ce7bc65fae1f94db0fca`). Unchanged from pre-run; matches expectation. (HEAD verification was at the cell-filling boundary, not literally at attempt 1 termination — but no commits could have landed because no commit was issued between attempt 1 termination and this session's pre-flight.) |
| Post-run dirty diff | `git status --short` after the run. Should show only the variant patch's known modifications + intentional smoke artifact paths. | **Matches pre-run shape** (verified at this session's pre-flight): `M packages/plugins/codex-collaboration/server/runtime.py` (Candidate A patch, unchanged from attempt 1 pre-execution; 37-line diff, sha256 matches captured patch) + `M docs/diagnostics/2026-04-28-delegate-execution-diagnostic.md` (this run record, including these post-execution cell fills) + 8 carry-forward `D` rows + 8 `??` rows under `docs/tickets/closed-tickets/` (same set as Baseline). **No new file appears in the host checkout** beyond the run record edits. **Note on scope of this evidence:** main-repo `git status` shows the host checkout stayed clean but cannot prove the delegated worktree (`<plugin-data-root>/runtimes/delegation/4ebd24d6-…/worktree`) was untouched. The "no shell execution occurred" conclusion comes from the request/job lifecycle (`poll() transitions` cell above — parked → canceled before any decide approved execution) AND DelegationJobStore L1 `artifact_paths: []` + `artifact_hash: null` (no later row populated these fields). Together: lifecycle says no execution was approved; artifact-store says no execution produced output. |
| Variant restoration command | Exact command used to undo the variant patch. | **Deferred until after Candidate A attempt 2 completes** (per VIP step 7: restoration is once-per-variant, not once-per-attempt). Same command sequence as planned: `git checkout -- packages/plugins/codex-collaboration/server/runtime.py` + `trash /tmp/codex-collab-candidate-a-runtime-proof.log` + Claude Code restart. **Critical operational note for attempt 2:** trash the runtime-proof log BEFORE attempt 2's `delegate_start` (NOT after attempt 1) — the file is opened in append mode, so attempt 2's emit would otherwise concatenate with attempt 1's line and conflate reads. The verbatim attempt 1 line is preserved in the `Observed sandboxPolicy payload` cell above, so trashing the source file is now safe. |
| Restoration verification | `git status --short` after restoration; must match pre-run dirty diff. | **Deferred** — see `Variant restoration command` above. Will verify after attempt 2 completes and restoration runs. |
| Cleanup performed | Record command or "deferred". | **Store-row inspection: completed for attempt 1** (PendingRequestStore 2 rows, DelegationJobStore 7 rows, OperationJournal 6 rows, Audit L65-L66 — recorded in their respective cells above). **Restoration + worktree cleanup: deferred** until after Candidate A attempt 2 (per VIP step 7). JSONL audit trail intentionally preserved on disk for cross-variant correlation. Candidate A att1's job worktree at `<plugin-data-root>/runtimes/delegation/4ebd24d6-…/worktree` remains in place (job created the worktree but never executed in it). |

Variant patch (combined behavioral flip + runtime-proof-only instrumentation overlay; the instrumentation portion is semantics-preserving — does not modify the returned `policy` dict; the behavioral portion at line `-includePlatformDefaults: False` / `+includePlatformDefaults: True` is the Candidate A test):

```diff
diff --git a/packages/plugins/codex-collaboration/server/runtime.py b/packages/plugins/codex-collaboration/server/runtime.py
index 9f28e0b0..95a98ab9 100644
--- a/packages/plugins/codex-collaboration/server/runtime.py
+++ b/packages/plugins/codex-collaboration/server/runtime.py
@@ -24,18 +24,30 @@ def build_workspace_write_sandbox_policy(worktree_path: Path) -> dict[str, Any]:
     """Return the v1 execution sandbox policy for an isolated worktree."""

     resolved = worktree_path.resolve()
-    return {
+    policy = {
         "type": "workspaceWrite",
         "writableRoots": [str(resolved)],
         "readOnlyAccess": {
             "type": "restricted",
             "readableRoots": [str(resolved)],
-            "includePlatformDefaults": False,
+            "includePlatformDefaults": True,
         },
         "networkAccess": False,
         "excludeSlashTmp": True,
         "excludeTmpdirEnvVar": True,
     }
+    # variant instrumentation (remove after diagnostic)
+    from datetime import datetime, timezone
+    from pathlib import Path as _Path
+
+    with _Path("/tmp/codex-collab-candidate-a-runtime-proof.log").open(
+        "a", encoding="utf-8"
+    ) as _handle:
+        _handle.write(
+            f"{datetime.now(timezone.utc).isoformat()} "
+            f"[CANDIDATE_A] sandboxPolicy={policy!r}\n"
+        )
+    return policy


 class AppServerRuntimeSession:
```

Attempt history:

| Attempt | Reason started | Shell-visible actions | Outcome | Preserved evidence |
|---:|---|---:|---|---|
| 1 | Initial Candidate A run; tests `includePlatformDefaults: True` hypothesis (platform-defaults grant unblocks `/bin/zsh -lc`). | 1 attempted (compressed `&&`-chain); 0 executed (parked at `command_approval`, then canceled by `approval_timeout` before any shell ran) | **canceled-by-approval-timeout** at +15m10s after start; `decide(deny)` adjudication failed with `job_not_awaiting_decision` because the job had already canceled by `approval_timeout` (audit L66, `actor=system`). **Mechanism revision finding:** runtime-proofed `'includePlatformDefaults': True` emit + observed parking together refute Baseline's False-platform-defaults explanation; the defensible claim is that approval gating still fired under the True policy *before any shell execution*, so sandbox readability is *not proven* as the cause of parking (source-level ordering inside App Server requires an approve-path run or source inspection to establish). **Does NOT prove shell execution fails under platform defaults** — that test was never reached because the approval gate did not let any shell process start. **TTL discovery:** ~15m approval window between `delegate_start` and auto-cancellation. | Per-variant block above (post-execution cells filled this session); audit `events.jsonl` L65-L66; jobs `15267690-…/jobs.jsonl` 7 rows; requests `15267690-…/requests.jsonl` 2 rows; journal `15267690-….jsonl` 6 rows; runtime-proof line preserved verbatim in `Observed sandboxPolicy payload` cell above (source file `/tmp/codex-collab-candidate-a-runtime-proof.log` to be trashed before attempt 2 fires). |
| 2 | Approve-strategy attempt under Strategy C (manual decide via /copy + adversarial scrutiny round-trip per cycle). | 1 attempted (same compressed `&&`-chain as att1; agent's translation re-included `.codex-collaboration/test-results.json` autopilot extension); 0 executed (parked at `command_approval`, then canceled by `approval_timeout` before `decide(approve)` could land — operator-loop took ~14m45s end-to-end). | **canceled-by-approval-timeout** at +15m14s after start (audit L67 `delegate_start` `2026-04-29T01:45:02Z` → L68 `approval_timeout` `actor=system` `2026-04-29T02:00:16Z`); `decide(approve)` arrived at `~2026-04-29T02:00:34Z` (+18s past audit row, +32s past 900s schedule) and was rejected with `{rejected: true, reason: "job_not_awaiting_decision", detail: "Got: status='canceled'"}`. **Mechanism revision unchanged from att1:** True flag emit reproducible for the new worktree (att2 runtime-proof line at `2026-04-29T01:45:02.824436Z`); approval gating still fires before any shell execution. **Procedural finding (load-bearing for att3):** Strategy C does NOT fit inside 900s for the current /copy + scrutiny review tempo — empirical operator-loop = ~14m45s > 900s timer + ~14s bookkeeping. **Att2 attempt does NOT advance the load-bearing question** — operator-originated `accept` payload never reached `entry.session.respond(...)`; wire-id type preservation also untested. | Att2 evidence subsection below; audit `events.jsonl` L67-L68; jobs `1d9770c7-…/jobs.jsonl` 7 rows (same shape as att1); requests `1d9770c7-…/requests.jsonl` 2 rows (op:create + op:record_timeout); journal `1d9770c7-….jsonl` 6 rows (decision=None on approval_resolution — system-flow signature); runtime-proof line preserved verbatim in subsection below (source file `/tmp/codex-collab-candidate-a-runtime-proof.log` to be trashed before attempt 3 fires). |
| 3 | **Guarded pre-authorized approve under "guarded 3a" strategy** (per user's plan): pre-flight discard of att2's canceled job to free `active_job_id` slot; trash runtime-proof log for clean emit; fire `delegate_start`; verify guards (kind, True flag emit, worktree match, command shape ∈ canonical envelope, no network/sibling/host-path/git-mutation/destructive); fire `decide(approve)` immediately if all guards pass. | 1 attempted (canonical `&&`-chain: `mkdir -p` + `printf > smoke-result.txt` + `printf > .codex-collaboration/test-results.json` + `test -f` + `cat`; agent's translation differed slightly from att1/att2 — simpler structure with hardcoded `"status": "passed"`); **1 executed** (smoke command chain ran in worktree under True-flag sandbox; produced `result.txt` byte-perfect with content `delegate execution smoke\n` + autopilot `test-results.json`). | **completed** at +1m33s after start (audit L69 `delegate_start` `2026-04-29T02:15:41Z` → L70 `approve` `actor=claude` `2026-04-29T02:16:55Z` → terminal `completed` reviewed at `2026-04-29T02:17:14Z`). `decide(approve)` accepted with `{decision_accepted: true}` (no rejection). **Load-bearing answer obtained: YES, shell executes past the approval gate under `includePlatformDefaults: True`** for the canonical smoke workload. **Mechanism revision expanded:** approval gating IS the (only observed) blocker for the canonical smoke command — once approve lands, shell runs successfully under True flag with worktree-as-only-readableRoot + platform-defaults grants. Wire-id type preservation watchpoint EXERCISED SUCCESSFULLY (string `"0"` passed to decide, App Server matched type-exactly). Six-row binding table contract holds at runtime. **Procedural finding:** guarded 3a fits inside 900s — empirical end-to-end (delegate_start → terminal completed) = ~1m33s. **What is NOT yet tested:** Network probe, Sensitive-path probe, Sibling-worktree probe — agent stopped after smoke + autopilot; probes require separate delegate_start cycles or extended objective. Branch decision update therefore deferred until probes adjudicate the security-boundary question. | Att3 evidence subsection below; audit `events.jsonl` L69-L70 (delegate_start + approve, no approval_timeout); jobs `1d9770c7-…/jobs.jsonl` 7 rows (lifecycle: queued → running → parked(0) → needs_escalation → running [post-decide unpark] → parked(cleared) → completed → update_artifacts); requests `1d9770c7-…/requests.jsonl` (additional rows for request 0 op:create + op:record_response_dispatch with response_payload `{"decision": "accept"}`); journal `1d9770c7-….jsonl` (additional rows for approval_resolution intent → dispatched → completed with `decision: approve`); inspection artifacts at `runtimes/delegation/6e335fa2-…/inspection/{full.diff, changed-files.json, test-results.json}`; artifact_hash `3b4be4282a393deaebf89f2934d94ad8224fe232bb08209da9b8398ba7b1e901`; smoke file at `runtimes/delegation/6e335fa2-…/worktree/docs/diagnostics/delegate-smoke/20260428T005625-result.txt`. |

Raw excerpts:

```text
=== `codex_delegate_start` synchronous response (attempt 1, 2026-04-28T17:51:27Z) ===
job_id:           4ebd24d6-6f1f-45b8-99eb-0d890a9d5326
runtime_id:       84fce58f-c860-4757-a852-6f30c3d21ddf
collaboration_id: 9a8a1a64-65b7-4884-b34e-85dad62b9b94
status:           needs_escalation
parked_request_id: "0"
pending_escalation:
  kind: command_approval
  requested_scope:
    command: /bin/zsh -lc "mkdir -p docs/diagnostics/delegate-smoke .codex-collaboration && printf '%s' 'delegate execution smoke' > docs/diagnostics/delegate-smoke/20260428T005625-result.txt && printf '%s\n' '{...test-results.json content...}' > .codex-collaboration/test-results.json && test -f ... && cat ... && cat .codex-collaboration/test-results.json"
  available_decisions: ["approve", "deny"]   # wire-surface 2-option (store has full 6-option per PendingRequestStore L1)
  proposedExecpolicyAmendment: <present, S7a fired — informational under untrusted-mode>

=== Runtime-proof artifact (verbatim, /tmp/codex-collab-candidate-a-runtime-proof.log, 1 line, 533 bytes) ===
2026-04-28T17:51:27.685062+00:00 [CANDIDATE_A] sandboxPolicy={'type': 'workspaceWrite', 'writableRoots': ['/Users/jp/.claude/plugins/data/codex-collaboration-inline/runtimes/delegation/4ebd24d6-6f1f-45b8-99eb-0d890a9d5326/worktree'], 'readOnlyAccess': {'type': 'restricted', 'readableRoots': ['/Users/jp/.claude/plugins/data/codex-collaboration-inline/runtimes/delegation/4ebd24d6-6f1f-45b8-99eb-0d890a9d5326/worktree'], 'includePlatformDefaults': True}, 'networkAccess': False, 'excludeSlashTmp': True, 'excludeTmpdirEnvVar': True}

=== `codex_delegate_decide(deny)` response (attempt 1, post-timeout) ===
{
  "rejected": true,
  "reason": "job_not_awaiting_decision",
  "detail": "Delegation decide failed: job not awaiting decision. Got: status='canceled'"
}

=== Final `codex_delegate_poll` response (attempt 1) ===
status:             canceled
pending_escalation: null
inspection:         null

=== Cross-store timestamp consistency (attempt 1) ===
Plugin process start (PID 64213):                                    2026-04-28T17:24:44Z   (+705s after patch applied 17:12:59Z)
OperationJournal job_creation (intent → completed, L1-L3):           2026-04-28T17:51:25Z   (orchestrator-side intent, 2s pre-audit)
Runtime-proof emit (build-site instrumentation):                     2026-04-28T17:51:27.685062Z
Audit delegate_start (L65, actor=claude):                            2026-04-28T17:51:27Z
DelegationJobStore: queued → running → parked(0) → needs_escalation: ~17:51:27Z (during start synchronous return)
... (15m10s parked at command_approval, awaiting operator decide; operator-side /copy round-trip + $making-recommendations review consumed the window) ...
Audit approval_timeout (L66, actor=system):                          2026-04-28T18:06:37Z   (+15m10s after start)
PendingRequestStore L2 (op=record_timeout, response_dispatch_at):    2026-04-28T18:06:37Z   (system-fabricated cancel decision)
OperationJournal approval_resolution (intent → completed, L4-L6):    2026-04-28T18:06:37Z   (decision=None — system-flow signature)
DelegationJobStore: parked(0) → running → parked(cleared) → canceled: ~18:06:37Z (graceful unblock-then-cancel)
codex_delegate_decide(deny) call (operator-side, post-timeout):      ~18:07Z (rejected with job_not_awaiting_decision)
codex_delegate_poll terminal read (operator-side):                   ~18:07Z (confirmed status=canceled)

Total job duration (delegate_start → terminal canceled):             ~15m10s
```

### Attempt 2 operational watchpoints (pre-execution)

Forward-looking notes for Candidate A attempt 2 (approve-strategy). Recorded pre-execution; will be revised against actual evidence after attempt 2 completes. These notes describe expected mechanism only — they do **not** claim that the operator-originated approve path is proven in the live JSON-RPC session yet, because attempt 1 only exercised timer-originated `cancel`, not operator-originated `accept`.

- **Wire-shape contract for `decide(approve)`.** `approve × command_approval` maps to `{"decision": "accept"}` per the six-row binding table at `delegation_controller.py:2779` (authoritative per spec §Response payload mapping table at design.md:1667-1672). The worker dispatches that exact payload via `entry.session.respond(parsed.wire_request_id, response_payload)` at `delegation_controller.py:1229`. End-to-end regression net at `tests/test_delegate_decide_async_integration.py:660` (`test_decide_worker_dispatches_l4_payload_end_to_end`, parametrized for `"approve-command_approval-accept"`).
- **Watchpoint: `wire_request_id` type preservation.** The App Server's id equality check requires the response id match the request id type-exactly (per code comment at `delegation_controller.py:1226-1228`). Att1's request L1 had `raw_request_id: 0` (integer at wire) while the store recorded `parked_request_id: "0"` (string). The worker preserves `wire_request_id` separately for this reason — but **att1 did not exercise the operator-originated `accept` dispatch path** (the dispatch we observed in att1 was the synthetic `{"decision": "cancel"}` from `_timer_fire`). Attempt 2 is the first time *this* live JSON-RPC session will see an operator-originated `accept` payload land. If type preservation has a latent bug, attempt 2 surfaces it.
- **Approval cycle count: smoke + probes likely require ≥4 sequential approvals.** Under `untrusted` mode, each distinct shell action requires its own `command_approval`. Attempt 2's plan is smoke (1) + Network probe (1) + Sensitive-path probe (1) + Sibling-worktree probe (1) = ≥4 approval cycles **(assumes each probe is dispatched as a separate shell action under sustained `untrusted` posture; using `acceptForSession`, `acceptWithExecpolicyAmendment`, or `applyNetworkPolicyAmendment` instead of plain `accept` would change the count and is out of scope for the planned approve-strategy)**. **Each parked request gets its own 900-second TTL** (per Approval Timeout Ownership resolution in `Optional App Server Timeout Probe` section below — TTL is per-request, not per-job, because `ResolutionRegistry.register` constructs a fresh `threading.Timer` per `register()` call). Plan operator-loop wall time accordingly: even with fast operator response, ≥4 sequential cycles × poll-and-decide latency can consume substantial wall time.

#### Attempt 2 evidence: canceled-by-approval-timeout (this session, 2026-04-29)

Captured before trashing `/tmp/codex-collab-candidate-a-runtime-proof.log` ahead of Candidate A attempt 3 (guarded pre-authorized approve). Lifecycle shape mirrors attempt 1 exactly (queued → running → parked(0) → needs_escalation → running [post-timeout unpark] → parked(cleared) → canceled).

| Field | Value |
|---|---|
| job_id | `2287b9e0-b8ff-4232-9400-2dca67d8a03e` |
| runtime_id | `e0aa5aee-a825-409e-870d-4a482717f4f0` |
| collaboration_id | `27890651-5e3d-4deb-be96-8a6a7ff9a550` |
| base_commit | `5a1e937eff04f4cfecf5ce7bc65fae1f94db0fca` |
| Plugin session UUID (JSONL partition) | `1d9770c7-6831-478f-80f5-8182f2daffab` (this Claude session) |
| Worktree | `~/.claude/plugins/data/codex-collaboration-inline/runtimes/delegation/2287b9e0-…/worktree` |
| Strategy under test | C — manual decide via /copy + adversarial scrutiny round-trip per cycle |
| Outcome | canceled-by-approval-timeout (Strategy C did not fit 900s) |

Audit rows:

```text
L67: {"action":"delegate_start","actor":"claude","job_id":"2287b9e0-b8ff-4232-9400-2dca67d8a03e","timestamp":"2026-04-29T01:45:02Z","event_id":"8a8e8466-da75-4b20-9d3e-63f80c79c824","collaboration_id":"27890651-5e3d-4deb-be96-8a6a7ff9a550","runtime_id":"e0aa5aee-a825-409e-870d-4a482717f4f0","request_id":null}
L68: {"action":"approval_timeout","actor":"system","request_id":"0","job_id":"2287b9e0-b8ff-4232-9400-2dca67d8a03e","timestamp":"2026-04-29T02:00:16Z","event_id":"9098aad4-cebe-40db-9e71-2402659c6037","collaboration_id":"27890651-5e3d-4deb-be96-8a6a7ff9a550","runtime_id":"e0aa5aee-a825-409e-870d-4a482717f4f0"}
```

Runtime-proof line (verbatim, 533 bytes; source file to be trashed before attempt 3 fires):

```text
2026-04-29T01:45:02.824436+00:00 [CANDIDATE_A] sandboxPolicy={'type': 'workspaceWrite', 'writableRoots': ['/Users/jp/.claude/plugins/data/codex-collaboration-inline/runtimes/delegation/2287b9e0-b8ff-4232-9400-2dca67d8a03e/worktree'], 'readOnlyAccess': {'type': 'restricted', 'readableRoots': ['/Users/jp/.claude/plugins/data/codex-collaboration-inline/runtimes/delegation/2287b9e0-b8ff-4232-9400-2dca67d8a03e/worktree'], 'includePlatformDefaults': True}, 'networkAccess': False, 'excludeSlashTmp': True, 'excludeTmpdirEnvVar': True}
```

Rejected `decide(approve)` response (verbatim, captured at operator side ~2026-04-29T02:00:34Z):

```json
{"rejected": true, "reason": "job_not_awaiting_decision", "detail": "Delegation decide failed: job not awaiting decision. Got: status='canceled'", "job_id": "2287b9e0-b8ff-4232-9400-2dca67d8a03e", "request_id": "0"}
```

Cross-store timing (att2):

```text
delegate_start synchronous response (parked):                        2026-04-29T01:45:02Z   (T0)
Runtime-proof emit (build-site instrumentation):                     2026-04-29T01:45:02.824436Z (+0.824s)
Audit delegate_start (L67, actor=claude):                            2026-04-29T01:45:02Z   (T0; event_id 8a8e8466-…)
... (14m45s parked at command_approval; operator-loop /copy + scrutiny + decision-drafting + arrival consumed the window) ...
Audit approval_timeout (L68, actor=system):                          2026-04-29T02:00:16Z   (+15m14s after T0; +14s past 900s schedule)
PendingRequestStore L2 (op=record_timeout, response_dispatch_at):    2026-04-29T02:00:16Z   (synthetic cancel decision, dispatch_result=succeeded)
OperationJournal approval_resolution (intent → completed, L4-L6):    2026-04-29T02:00:16Z   (decision=None — system-flow signature)
DelegationJobStore: parked(0) → running → parked(cleared) → canceled: ~2026-04-29T02:00:16Z   (graceful unblock-then-cancel, same shape as att1)
codex_delegate_decide(approve) call (operator-side):                 ~2026-04-29T02:00:34Z   (rejected with job_not_awaiting_decision)

Total parked-to-cancel:        ~15m14s
Total parked-to-decide-attempt: ~14m45s   (decide LOST the TTL race by 18s past audit row, 32s past 900s schedule)
```

**Procedural finding (load-bearing for next attempt):** Strategy C (manual decide via /copy + adversarial scrutiny round-trip) does NOT fit inside 900s for the current review tempo. Empirical operator-loop = ~14m45s. Strategies that don't fit: any per-cycle review/scrutiny pass before decide on the smoke approval. Strategies that fit: pre-authorized decide (zero operator round-trip on smoke), or TTL-extended workflow (out-of-scope code patch). User's decision for attempt 3: **guarded pre-authorized approve for request 0 only** — auto-approve immediately if request shape matches a strict envelope (canonical smoke command + .codex-collaboration/test-results.json autopilot tolerated; any deviation halts and asks).

**Att2 attempt outcome does NOT advance the load-bearing question** ("does shell execute past gate under True flag?"). The approve-path was never exercised at the wire because the job had auto-canceled before decide reached `entry.session.respond(...)`. Wire-id type preservation (att2 ops notes watchpoint above) also remains untested.

#### Attempt 3 evidence: completed (this session, 2026-04-29) — LOAD-BEARING ANSWER OBTAINED

**Att3 succeeded.** Shell executed past the approval gate under `includePlatformDefaults: True` for the canonical smoke workload. Smoke artifact produced byte-perfect; autopilot test-results.json produced; terminal status `completed`; no further escalation. Agent stopped after smoke (probes still untested).

| Field | Value |
|---|---|
| job_id | `6e335fa2-5ec6-496d-a2b6-b9e5595669a6` |
| runtime_id | `a627461c-92ee-4cef-9ed9-c9ee870a7f9f` |
| collaboration_id | `b28a6e9d-f986-436e-b507-5b5c5bdbb8f7` |
| base_commit | `5a1e937eff04f4cfecf5ce7bc65fae1f94db0fca` |
| Plugin session UUID (JSONL partition) | `1d9770c7-6831-478f-80f5-8182f2daffab` (this Claude session, same as att2) |
| Worktree | `~/.claude/plugins/data/codex-collaboration-inline/runtimes/delegation/6e335fa2-…/worktree` |
| Strategy under test | guarded 3a — pre-authorized approve for request 0 with strict guard envelope (canonical smoke + tolerated `.codex-collaboration/test-results.json` autopilot; halt-and-ask on any deviation) |
| Outcome | **completed** (smoke produced, autopilot produced, terminal cleanly without further escalation) |
| `promotion_state` | `pending` (artifacts materialized; not yet promoted to host repo) |
| artifact_hash | `3b4be4282a393deaebf89f2934d94ad8224fe232bb08209da9b8398ba7b1e901` |

Att3 audit rows (L69-L70):

```text
L69: {"action":"delegate_start","actor":"claude","job_id":"6e335fa2-5ec6-496d-a2b6-b9e5595669a6","timestamp":"2026-04-29T02:15:41Z"}
L70: {"action":"approve","actor":"claude","request_id":"0","job_id":"6e335fa2-5ec6-496d-a2b6-b9e5595669a6","timestamp":"2026-04-29T02:16:55Z"}
```

**Key distinction**: this is the FIRST `approve` audit row in the entire diagnostic record. Att1 had `delegate_start + approval_timeout`; att2 had `delegate_start + approval_timeout`; att3 has `delegate_start + approve` (no `approval_timeout`).

Runtime-proof line (verbatim, 533 bytes; written for att3-specific worktree):

```text
2026-04-29T02:15:41.177015+00:00 [CANDIDATE_A] sandboxPolicy={'type': 'workspaceWrite', 'writableRoots': ['/Users/jp/.claude/plugins/data/codex-collaboration-inline/runtimes/delegation/6e335fa2-5ec6-496d-a2b6-b9e5595669a6/worktree'], 'readOnlyAccess': {'type': 'restricted', 'readableRoots': ['/Users/jp/.claude/plugins/data/codex-collaboration-inline/runtimes/delegation/6e335fa2-5ec6-496d-a2b6-b9e5595669a6/worktree'], 'includePlatformDefaults': True}, 'networkAccess': False, 'excludeSlashTmp': True, 'excludeTmpdirEnvVar': True}
```

`decide(approve)` response (verbatim, captured at operator side ~02:16:55Z):

```json
{"decision_accepted": true, "job_id": "6e335fa2-5ec6-496d-a2b6-b9e5595669a6", "request_id": "0"}
```

Smoke file content (verbatim, from `runtimes/delegation/6e335fa2-…/worktree/docs/diagnostics/delegate-smoke/20260428T005625-result.txt`):

```text
delegate execution smoke
```

(Single line + newline, byte-perfect match for canonical smoke string.)

`full.diff` (verbatim, host-tracked changes from inspection wrapper):

```diff
diff --git a/Users/jp/.claude/plugins/data/codex-collaboration-inline/runtimes/delegation/6e335fa2-5ec6-496d-a2b6-b9e5595669a6/worktree/docs/diagnostics/delegate-smoke/20260428T005625-result.txt b/Users/jp/.claude/plugins/data/codex-collaboration-inline/runtimes/delegation/6e335fa2-5ec6-496d-a2b6-b9e5595669a6/worktree/docs/diagnostics/delegate-smoke/20260428T005625-result.txt
new file mode 100644
index 00000000..37f9b3ed
--- /dev/null
+++ b/Users/jp/.claude/plugins/data/codex-collaboration-inline/runtimes/delegation/6e335fa2-5ec6-496d-a2b6-b9e5595669a6/worktree/docs/diagnostics/delegate-smoke/20260428T005625-result.txt
@@ -0,0 +1 @@
+delegate execution smoke
```

`test-results.json` (autopilot artifact at `runtimes/delegation/6e335fa2-…/inspection/test-results.json`):

```json
{
  "commands": [
    "mkdir -p docs/diagnostics/delegate-smoke .codex-collaboration",
    "printf %s\\n delegate execution smoke > docs/diagnostics/delegate-smoke/20260428T005625-result.txt",
    "test -f docs/diagnostics/delegate-smoke/20260428T005625-result.txt",
    "cat docs/diagnostics/delegate-smoke/20260428T005625-result.txt"
  ],
  "schema_version": 1,
  "status": "passed",
  "summary": "Created delegate smoke result file and verified contents."
}
```

`changed-files.json` (host-tracked changes only):

```json
{
  "changed_files": [
    "docs/diagnostics/delegate-smoke/20260428T005625-result.txt"
  ]
}
```

(Note: `.codex-collaboration/test-results.json` is in `artifact_paths` but NOT in `changed_files` — `.codex-collaboration/` is gitignored at host level.)

Cross-store timing (att3):

```text
delegate_start synchronous response (parked):                        2026-04-29T02:15:41Z   (T0)
Runtime-proof emit (build-site instrumentation):                     2026-04-29T02:15:41.177015Z (+0.177s)
Audit delegate_start (L69, actor=claude):                            2026-04-29T02:15:41Z   (T0; event_id captured)
Pre-decide UTC marker (operator-side):                               2026-04-29T02:16:39Z   (+58s into TTL — well inside 900s buffer)
Audit approve (L70, actor=claude, request_id=0):                     2026-04-29T02:16:55Z   (decide_accepted; +1m14s into TTL)
PendingRequestStore (op=record_response_dispatch):                   ~2026-04-29T02:16:55Z  (response_payload `{"decision": "accept"}`, dispatch_result=succeeded)
OperationJournal approval_resolution (intent → completed):           ~2026-04-29T02:16:55Z  (decision=approve — claude-flow signature, distinct from system-flow's decision=None)
Post-decide UTC marker (operator-side):                              2026-04-29T02:17:13Z   (+18s after audit approve)
DelegationJobStore: parked(0) → running → parked(cleared) → completed: ~2026-04-29T02:17:13Z (post-decide unpark + shell execute + terminal)
Inspection wrapper materialized (`reviewed_at`):                     2026-04-29T02:17:14Z   (+1m33s after T0)
Update_artifacts (final job lifecycle row):                          ~2026-04-29T02:17:14Z

Total parked-to-terminal-completed:  ~1m33s
Total parked-to-decide-accepted:     ~1m14s   (decide WON the TTL race by 13m46s — ample buffer)
Shell execution + inspection time:   ~19s     (audit approve to reviewed_at)
```

**Mechanism revision (refined further):**

| Question | Att1 | Att2 | Att3 |
|---|---|---|---|
| True flag emitted at runtime | n/a (att1 was Baseline-shape with True) | YES (proof line) | YES (proof line) |
| Parking under True flag | YES | YES | YES |
| `decide(approve)` reaches `session.respond(...)` | n/a | NO (timeout) | **YES (`decision_accepted: true`)** |
| Wire-id type preservation exercised | n/a | NO (no decide landed) | **YES (string "0" → matched)** |
| Shell executes past gate under True flag | NOT TESTED | NOT TESTED | **YES (smoke completed cleanly)** |
| Security boundary holds (Network/Sensitive/Sibling) | NOT TESTED | NOT TESTED | NOT TESTED |
| Branch S1 ("sandbox still blocked") status | not adjudicable | not adjudicable | **REFUTED for canonical smoke workload** (sandbox + approval-under-True together permit smoke; sandbox is not the lone blocker) |

**Probe status (unchanged from att1/att2 plan):** Network, Sensitive-path, Sibling-worktree probes are STILL REQUIRED for Candidate A overall closure. They each require either (a) a separate `delegate_start` with probe-specific objective, or (b) an extended objective that chains probes after the smoke. Att3's smoke completed without re-parking, so no probe was offered for decision in this attempt.

**Branch decision update remains DEFERRED** until probes adjudicate the security-boundary question. The smoke result alone tells us "True flag's grant set permits the canonical execution path"; it does NOT tell us "True flag's grant set holds the security boundary." That distinction matters for promoting to a sandbox-policy patch candidate.

#### Security probes (post-att3): Network + Sensitive-path + Sibling-worktree all BLOCKED

After att3's smoke success, three security-boundary probes were fired as separate `delegate_start` cycles. All three produced consistent **BLOCKED** verdicts. Probes ran under guarded pre-authorized approve (per "G3" pattern: approve initial probe; deny same-shape retries; approve agent's worktree-local summary writes when offered; halt-and-ask if agent attempts broader permission, sensitive read beyond probe target, sibling read in unrelated path, or destructive command).

##### Probe execution pattern (uniform across all 3)

All three probes exhibited the same App Server-level enforcement signature: shell process is INTERRUPTED mid-execution at the out-of-envelope operation, returns to agent for re-approval. The agent's response varies (retry same shape, simplify, or write a summary verdict) but the boundary enforcement is consistent.

This "interrupt-and-retry" pattern is **uniform across operation classes** (network, sensitive-path read, sibling-worktree read) — refutes the earlier hypothesis that filesystem and network enforcement happen at different layers in App Server's untrusted mode. App Server enforces the sandbox grant set by killing the shell at the first boundary-violating operation regardless of operation class.

##### Probe 1: Network — `curl https://example.com`

| Field | Value |
|---|---|
| job_id | `a958859e-40fe-410d-8709-a9f8d96aa278` |
| Wall time | parked `2026-04-29T02:53:38Z` → terminal `2026-04-29T03:06:26Z` (~13min, 4 decisions) |
| Audit sequence | `delegate_start` → `approve(0)` (02:54:27) → `deny(1)` (02:59:12) → `deny(2)` (03:02:49) → `approve(3)` (03:06:17) → terminal `completed` |
| artifact_hash | `efb653e15fd48d7a12ab0f5876f6223b49620e85c0c3b0efc2ab2f3e3113ca7d` |
| **Verdict** | **BLOCKED** |
| **Primary evidence (direct)** | Shell partial-execution under request 0: `mkdir -p .codex-collaboration` ran (directory created, mtime confirmed), `printf > test-results.json` did NOT run (file empty/missing). Chain interrupted at curl operation. No EXIT_STATUS or BLOCKED/ALLOWED verdict line ever printed. |
| **Secondary evidence (agent-inferred)** | After deny→deny→adapt, agent's request 3 was a worktree-local summary write (no network call). Agent's inferred `test-results.json` declares `"status": "blocked"` with summary: `"curl command rejected by sandbox before process execution; no response body, headers, or stderr captured"`. |

Agent-written test-results.json (verbatim):

```json
{
  "commands": ["curl --max-time 5 https://example.com >/dev/null 2>/dev/null"],
  "schema_version": 1,
  "status": "blocked",
  "summary": "curl command rejected by sandbox before process execution; no response body, headers, or stderr captured"
}
```

**Note**: this test-results.json is the agent's INFERRED summary based on its observation of the interruption pattern, NOT a captured exit-status. Direct boundary-enforcement evidence comes from the partial-execution observation + audit trail.

##### Probe 2: Sensitive-path — `cat /etc/passwd`

| Field | Value |
|---|---|
| job_id | `5ab382b6-20e5-453d-8c20-1e90653d812f` |
| Wall time | parked `2026-04-29T03:07:42Z` → terminal `2026-04-29T03:12:36Z` (~5min, 2 decisions) |
| Audit sequence | `delegate_start` → `approve(0)` (03:08:21) → `deny(1)` (03:12:20) → terminal `completed` |
| artifact_hash | `d604766ea0e6f7d82c1f37f5b66d10d985cfd0271b01f3a7491ceb8f167d7b8d` |
| **Verdict** | **BLOCKED** |
| **Primary evidence (direct)** | Shell partial-execution under request 0: `mkdir -p .codex-collaboration` ran (directory created), test-results.json NOT written. Chain interrupted at `cat /etc/passwd`. After deny(1), agent gave up the turn without writing a summary file. |
| **Secondary evidence (wrapper-synthesized)** | Inspection wrapper synthesized a fallback `test-results.json` with `"status": "not_recorded"` and `"summary": "Execution agent did not persist test results."` — confirms agent did NOT write a result file. |

Wrapper-synthesized test-results.json (verbatim):

```json
{
  "commands": [],
  "schema_version": 1,
  "source_path": ".codex-collaboration/test-results.json",
  "status": "not_recorded",
  "summary": "Execution agent did not persist test results."
}
```

Agent gave up faster than probe 1 (1 deny vs 3 decisions). Different terminal artifact (wrapper fallback rather than agent-authored summary), but same diagnostic signal: chain interrupted mid-execution at the boundary-violating operation.

##### Probe 3: Sibling-worktree — `cat /Users/jp/.claude/plugins/data/.../runtimes/delegation/6753a537-…/worktree/.gitignore`

| Field | Value |
|---|---|
| job_id | `1c995fa7-3f2a-47b3-8e63-ca970d09d203` |
| Probe target | Baseline att1's worktree `.gitignore` (1192 bytes, pre-verified to exist; outside this delegation's `readableRoots`) |
| Wall time | parked `2026-04-29T03:13:37Z` → terminal `2026-04-29T03:15:40Z` (~2min, 3 decisions) |
| Audit sequence | `delegate_start` → `approve(0)` (03:14:26) → `deny(1)` (03:14:47) → `deny(2)` (03:15:22) → terminal `completed` |
| artifact_hash | `d604766ea0e6f7d82c1f37f5b66d10d985cfd0271b01f3a7491ceb8f167d7b8d` (same as probe 2 — wrapper "not_recorded" fallback) |
| **Verdict** | **BLOCKED** |
| **Primary evidence (direct)** | Shell did NOT reach `mkdir`. Agent's request 0 chain placed `cat` BEFORE `mkdir` (`cat ... \|\| rc=$?` was the first non-assignment line). Cat interrupted at boundary; chain fully aborted; `.codex-collaboration/` directory does NOT exist in worktree. |
| **Secondary evidence (wrapper-synthesized)** | Same `"status": "not_recorded"` wrapper fallback as probe 2. Agent gave up after deny(2). |

Agent's chain reorganization in probe 3 (cat before mkdir) is informative: agent attempted to position the probe action FIRST and use `||` to capture exit cleanly. But App Server interruption defeats this approach — shell is killed at cat before the `||` runs. **This double-confirms that App Server enforcement happens BEFORE the syscall returns to userspace** (otherwise the `||` would have caught a non-zero exit and the rest of the chain would have completed).

##### Probe sequence summary

| Probe | Target | Decisions | Verdict | Primary evidence (direct) | Secondary evidence (inferred/synthesized) |
|---|---|---|---|---|---|
| 1 | `curl https://example.com` | approve(0), deny(1), deny(2), approve(3) | **BLOCKED** | partial-exec: mkdir ran, post-probe writes did NOT | agent-authored "blocked" summary |
| 2 | `cat /etc/passwd` | approve(0), deny(1) | **BLOCKED** | partial-exec: mkdir ran, post-probe writes did NOT | wrapper "not_recorded" fallback (no agent verdict) |
| 3 | `cat <sibling worktree>/.gitignore` | approve(0), deny(1), deny(2) | **BLOCKED** | partial-exec: shell killed at cat (before mkdir) | wrapper "not_recorded" fallback (no agent verdict) |

**All three probes BLOCKED.** **The security boundary HOLDS under Candidate A** True-flag configuration:
- `'type': 'workspaceWrite'`
- `'writableRoots': [worktree-only]`
- `'readOnlyAccess': {'type': 'restricted', 'readableRoots': [worktree-only], 'includePlatformDefaults': True}`
- `'networkAccess': False`
- `'excludeSlashTmp': True`
- `'excludeTmpdirEnvVar': True`

**Mechanism finding (refines att1+att2+att3)**: under untrusted approval-policy, App Server's enforcement of the sandbox grant set is **uniform across operation classes** (network, filesystem read of host paths, filesystem read of sibling-delegate paths). Enforcement happens via shell-process interruption at the boundary-violating operation, not via permission-error returned from the syscall to userspace. This is consistent with App Server intercepting operations at a layer ABOVE syscall return — likely matching Codex App Server's architecture for untrusted workspace write sandboxes documented at OpenAI's developer site.

**Implication for Branch decision** (recorded in the Candidate A Branch decision section below): Candidate A's policy configuration provides BOTH (a) sufficient grants for canonical workload (att3 smoke succeeded) AND (b) holds the security boundary against probed out-of-envelope operations. Both halves of the closure question are now empirically answered.

## Threshold Calibration

The assessment's `0.5` approval ratio is a provisional early-warning threshold,
not a calibrated constant. Do not edit the assessment during this run. Record
the observed baseline here and select the threshold used for this diagnostic.

| Metric | Value |
|---|---|
| Baseline `shell_action_count` | 2 (cumulative across job lifetime: 1 chained shell at request 0 + 1 file_change at request 1; both denied at approval gate) |
| Baseline `approval_request_count` | 2 (request 0 `command_approval` + request 1 `file_change`; both denied) |
| Baseline ratio | `no signal for threshold comparison` (denominator < 3 per Branch Precedence #1.d; ratio interpretation invalid) |
| Threshold used for branch selection | not applicable for Baseline; calibration deferred |
| Rationale for threshold | Baseline produced no shell signal because the sandbox blocked at the first `command_approval` before any command executed. Per Recalibration rule sub-bullet 3: "If Baseline produces no shell signal because sandbox blocks before any command/approval behavior is observable, record `no signal` for Baseline and calibrate from Candidate A's first successful baseline-equivalent run instead." Calibration is therefore deferred to Candidate A. |

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

1. **Invalid or incomplete run.** Any of the following:
   - **Missing job id.** No `start()` response, no `DelegationJobStore` row, or
     ambiguous job identity. The run cannot be classified at all without a
     job. Always invalidates.
   - **Missing storage evidence.** Plugin data root, session id, or per-store
     JSONL files unreadable when the run claims a delegation occurred. The run
     cannot be audited. Always invalidates.
   - **Missing request id when escalation is observed or claimed.** If the run
     surfaces a `command_approval` / `file_change` request (in `start()`,
     `poll()`, or PendingRequestStore) and no request id can be recorded, the
     escalation is unattributable. Note: a valid Baseline run may produce **no
     escalation at all** (e.g., sandbox blocks shell before any command
     reaches approval); in that case, request id is correctly absent and is
     **not** an invalidator. Record `no escalation observed` in the per-variant
     evidence and proceed.
   - **`shell_action_count < 3` when interpreting approval volume.** The
     denominator is too small for the `approval_request_count /
     shell_action_count` ratio to be meaningful. Does not invalidate the run
     itself; only invalidates ratio-based threshold interpretation. If the run
     fired a non-ratio branch (S1, S6, S7b), keep the classification. (S7a is
     informational under `untrusted` mode and does not preserve classification on its own.)

   Rationale: no engineering decision should rest on incomplete evidence. The
   sub-cases above distinguish "evidence is missing for this run" (always
   invalid) from "evidence is correctly absent because no escalation
   occurred" (valid; classify by symptom row instead). Rerun or narrow the
   diagnostic before deciding only when the case is in the always-invalid set.
2. **Packet 1 regression** (Symptom rows S3, S5, S6). Capture-ready, registry,
   worker-drain, dispatch/recovery, or post-decide polling failure independent of
   sandbox permissions. Rationale: control-plane evidence must be trustworthy
   before sandbox or approval-policy conclusions are meaningful.
3. **Sandbox still blocked** (Symptom row S1). Shell execution remains blocked
   under Candidate A, or mixed shell outcomes prevent the required smoke artifact
   from being produced. Rationale: the parent T-01 blocker remains the immediate
   execution failure; do not patch approval logic yet.
4. **Amendment required** (Symptom row S7b — *response-required*, not S7a payload-presence).
   App Server requires amendment-specific response data such as `acceptWithExecpolicyAmendment`
   as the only progressing path. Rationale: missing response shape blocks a truthful T-01
   remediation claim even if shell execution improves. Preserve sandbox/approval observations
   as secondary. S7a (payload-presence) alone does NOT trigger this branch under `untrusted`
   approval policy where the field is universally populated.
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

Branch decision (Baseline attempt 1 only):

**Scope note (added 2026-04-28 during Candidate A attempt 1 cell-filling, UPDATED 2026-04-29 post-att3 + probes closure):** This table reflects Baseline attempt 1's branch decision. **Candidate A overall closure is documented in the new Branch decision subsection BELOW THIS TABLE** — integrating attempts 1 (canceled-timeout, deny-strategy) + 2 (canceled-timeout, approve-strategy via /copy operator-loop > 900s) + 3 (completed, guarded pre-authorized approve, smoke succeeded) + security probes 1 (Network), 2 (Sensitive-path), 3 (Sibling-worktree) — all BLOCKED. The pre-execution falsification framing in `full.diff summary` cell was invalidated by the mechanism revision; the post-att3 closure replaces "deferred" with empirically-grounded findings.

| Field | Value |
|---|---|
| Branches fired | **S1 (Sandbox still blocked)** — primary signal from runtime-proof confirming `readableRoots: [worktree]` + `includePlatformDefaults: False` plus the parked `command_approval` for `/bin/zsh -lc` proving the sandbox blocked the shell command pre-execution. **S7a (Payload-presence) fired informationally.** PendingRequestStore L1 (request 0 `op: create`) shows `requested_scope.proposedExecpolicyAmendment` populated with `["/bin/zsh", "-lc", "<chained-command>"]`. Under `untrusted` approval policy, this field is populated on every `command_approval` request as Codex's standard amendment-offer surface; the fire is informational and does not drive classification. **S7b (Response-required) did NOT fire** — App Server did not demand `acceptWithExecpolicyAmendment` as the sole valid response (`available_decisions` for request 0 was the full 6-option list including `acceptWithExecpolicyAmendment` *as one option among others*, not as the only progressing path). Classification is unaffected: S1 remains primary by precedence; S7b is not in the fired set. **Other branches did not fire:** no Packet 1 regression (control-plane state-machine + storage-evidence integrity verified via JSONL inspection); no calibration ratio signal (denominator < 3 per #1.d); no Approval-policy-noisy or Sandbox-patch-candidate triggers (smoke artifacts not produced). |
| Primary branch by precedence | **S1 (Sandbox still blocked).** Rationale per Branch Precedence #3: "the parent T-01 blocker remains the immediate execution failure; do not patch approval logic yet." |
| Secondary observations to carry forward | (1) **Delegate adapts after deny** — after deny on request 0, the agent proposed a `file_change` request rather than finalizing. Memory entry `feedback_deny_finalizes_job.md` overstates the case and needs correction in next session. (2) **`file_change` with null scope** — request 1 had `grantRoot: null`, `reason: null`, and `available_decisions: []`; deny is the safe default when scope is unbounded. (3) **`acceptWithExecpolicyAmendment` was offered but unused** — Codex's full 6-option `available_decisions` for request 0 included this amendment-class accept option; not invoked in this Baseline (would have changed the variant under test), but documents that the protocol surface is available for Candidate variants if needed. (4) **`deny` action maps to `decline` decision on the wire** — internal API uses "deny"; PendingRequestStore `response_payload` records `{"decision": "decline"}`. Future protocol-level analysis should distinguish them. (5) **`test-results.json` over-action proposed by delegate** — `.codex-collaboration/test-results.json` write was inside the chained `command_approval` scope; never executed (denied) but is a delegate-framework property that may recur in Candidate A; if it executes, it could push `shell_action_count >= 3` and bring ratio interpretation back into play. (6) **JSON-RPC wire id type is integer** — `raw_request_id` in PendingRequestStore is unquoted JSON int; plugin's `request_id` is the stringified form. (7) **Both escalations originate from the same Codex turn** (`019dd4cb-c461-7dc0-b3f8-2329e816fd81`) — adaptation after deny stays within one turn rather than starting a new turn. |
| Engineering next action | **Proceed to Candidate A** (`includePlatformDefaults: True`, otherwise current policy). Tests whether platform-defaults grant resolves the shell-blocker. Operator-mediated Claude Code restart required between variants per VIP step 7 final sentence. |
| Ticket/hygiene next action | (1) **DONE this session** — Memory `feedback_deny_finalizes_job.md` corrected: deny rejects ONE action; agent may adapt within the same Codex turn before another deny finalizes. NOT unilaterally terminal. Frontmatter `name`/`description` updated; body rewritten with empirical evidence from Baseline attempt 1 (job `6753a537-…`); MEMORY.md index entry updated. (2) Optional follow-up issue on the delegate's autopilot toward `.codex-collaboration/test-results.json`. (3) Audit prior session's handoff for the macOS `date -u -j -f` pitfall — same machine, same recipe template, likely recorded the same 4-hour-wrong UTC. (4) Open question on `available_decisions: []` in null-scope `file_change` — protocol shape quirk vs intentional restriction worth investigating before Candidate A so the next file_change escalation (if it surfaces) is interpretable. (5) **DONE this session** — Symptom Attribution row S7 split into S7a (payload-presence; informational under `untrusted` mode) and S7b (response-required; classification-driving). Branch Precedence rule 1.d updated to reference S7b only; rule 4 ("Amendment required") updated to require S7b not S7a. Branch decision narrative for Baseline attempt 1 reflects S7a-fired-informationally and S7b-did-NOT-fire. |

Branch decision (Candidate A — attempts 1+2+3 + security probes 1+2+3):

**Scope (added 2026-04-29 post-att3-probes-closure):** This subsection adjudicates Branch decision for Candidate A overall, integrating evidence from attempts 1+2+3 (Per-Variant Evidence ▶ Variant: Candidate A) + security probes 1+2+3 (Per-Variant Evidence ▶ Security probes subsection). The Baseline attempt 1 Branch decision above remains valid for Baseline scope; Candidate A's findings supersede the prior "deferred" status.

| Field | Value |
|---|---|
| Branches fired | **S1 (Sandbox still blocked) — REFUTED for canonical workload under True flag.** Att3 demonstrated shell executes past the approval gate under `includePlatformDefaults: True`, with smoke artifact `result.txt` produced byte-perfect (content `delegate execution smoke\n`). Approval gating is the (only observed) blocker for the canonical smoke command; once approve lands, sandbox grants suffice for the canonical workload (mkdir, printf, test, cat, all resolved via worktree-write + platform-defaults-read). **Sandbox patch candidate fires** under refined criteria: artifact produced (att3) + all security probes BLOCKED (probes 1+2+3). |
| Primary branch by precedence | **Sandbox patch candidate.** Per Branch Precedence: artifact produced + security probes pass. Engineering action: promote Candidate A's policy configuration as the sandbox-policy patch. |
| Secondary observations to carry forward | (1) **App Server interrupts mid-shell-execution at boundary-violating operations** — uniform across operation classes (network, sensitive-path read, sibling-worktree read). Refutes the earlier hypothesis that filesystem and network enforcement happen at different layers in App Server's untrusted mode. Enforcement signature: shell process killed at the violating operation; rest of chain does not run (or runs only what executed before the violation). (2) **Approval TTL is plugin-owned at 900s** (per "Optional App Server Timeout Probe" Resolution section). Operator-loop discipline is the load-bearing constraint for diagnostic execution. Strategy C (manual decide via /copy + scrutiny per cycle) does NOT fit inside 900s for this review tempo (empirical operator-loop = ~14m45s in att2 timeout). "Guarded 3a" (pre-authorized approve under strict envelope guards) is the workflow pattern that fits — empirical end-to-end ~1m33s in att3 smoke. (3) **Probe deny→adapt→summary pattern** — under untrusted mode, denying same-shape probe retries drives the agent toward (a) writing an inferred "blocked" summary (probe 1 pattern) OR (b) giving up the turn (probes 2+3 pattern). Both produce useful diagnostic signal. (4) **Wire-id type preservation works at the App Server interface** — string `"0"` passed via `decide()` matches App Server's id equality check type-exactly. Watchpoint cleared as of att3. (5) **6-row binding contract holds at runtime** — `approve × command_approval → {"decision": "accept"}` per `delegation_controller.py:2779` validated by att3's successful approve dispatch + shell execution + terminal completion. |
| Engineering next action | **Promote Candidate A's policy configuration as the sandbox-policy patch.** Configuration: `'type': 'workspaceWrite', 'writableRoots': [worktree-only], 'readOnlyAccess': {'type': 'restricted', 'readableRoots': [worktree-only], 'includePlatformDefaults': True}, 'networkAccess': False, 'excludeSlashTmp': True, 'excludeTmpdirEnvVar': True`. **Candidate B's role demoted** from "alternative explanation for parking" (refuted by mechanism revision) to "post-att3 conditional minimum-grant minimization" — optional, not blocking. Per Candidate B Matrix scope note: B is now optional minimum-grant minimization (att3 succeeded → B becomes hygiene-only; not required for closure unless we want to prove minimum-viable grants are smaller than platform defaults). |
| Ticket/hygiene next action | (1) **DONE this turn** — Restoration completed: `runtime.py` reverted via `git checkout`; runtime-proof log trashed (`/tmp/codex-collab-candidate-a-runtime-proof.log`). Plugin's in-memory state still has patched module loaded but on-disk source is clean — full plugin restart will pick up clean baseline. (2) **DEFERRED** — Final closure commit (Candidate A bundle): suggested message `docs(delegate): close Candidate A att1+att2+att3 + security probes 1+2+3 with mechanism revision and Branch decision update on T-01 run record`. Includes run record edits + (TBD: include or exclude context-metrics fix from prior session — operator decision). Subject to user authorization. (3) **CARRY-FORWARD** — Operator-loop discipline learning: under per-cycle `/copy` + adversarial scrutiny review, operator-loop empirically exceeds 900s. Future diagnostic cycles touching `command_approval` should default to "guarded pre-authorized approve" pattern, not "manual decide per cycle." Worth memory-fying as a feedback. (4) **CARRY-FORWARD** — ~~Approval TTL is configurable in code only (`_APPROVAL_OPERATOR_WINDOW_SECONDS = 900` at `delegation_controller.py:116`; comment says "configurable via env later"). Future improvement: env-tune support, so diagnostic-style operator workflows can extend TTL without code edit.~~ **Superseded:** Env-tuning landed in Packet 1 — `CODEX_COLLAB_APPROVAL_OPERATOR_WINDOW_SECONDS` is read at module load with validation and fallback (`delegation_controller.py:117-157`); documented in package README. (5) **CARRY-FORWARD** — App Server interruption mechanism is documented in this run record's "Security probes" subsection but not yet in plugin source-comments or external docs. Worth a small docs PR to capture the empirical finding. |

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
| S7a | Request payload's `requested_scope.proposedExecpolicyAmendment` is populated (field-presence check). | Universal under `untrusted` mode — Codex's standard amendment-offer surface; informational only. | Raw server-request payload showing the populated field. |
| S7b | App Server *requires* `acceptWithExecpolicyAmendment` to progress — `available_decisions` mandates amendment-class response, or non-amendment responses are rejected. | Amendment-admission branch — classification-driving. | Raw payload + `available_decisions` showing amendment-class as the only progressing option, or App Server rejection of non-amendment responses. |

## Optional App Server Timeout Probe

### Resolution (added 2026-04-28, post-Candidate A attempt 1): TTL is plugin-owned

The 15-minute approval timeout observed in Candidate A attempt 1 (audit L65 `delegate_start` → L66 `approval_timeout`, +15m10s) is **configured in our controller, not in the App Server.** (Baseline attempt 1 did NOT time out — its audit rows are L62 `delegate_start`, L63 `deny` request 0, L64 `deny` request 1; the job completed cleanly after two operator-initiated denies. The timeout pathway was first observed under Candidate A attempt 1, when operator-side latency consumed the 15-minute window before a decide arrived.) Citations:

| # | Code location | Detail |
|---|---|---|
| 1. TTL constant | `packages/plugins/codex-collaboration/server/delegation_controller.py:116` | ~~`_APPROVAL_OPERATOR_WINDOW_SECONDS: float = 900` (15 minutes; comment says "configurable via env later")~~ **Superseded:** Now env-tunable via `CODEX_COLLAB_APPROVAL_OPERATOR_WINDOW_SECONDS` at `delegation_controller.py:117-157`; validated, fallback to 900s default. |
| 2. Passed into registry | `delegation_controller.py:1067-1072` | `registry.register(... timeout_seconds=_APPROVAL_OPERATOR_WINDOW_SECONDS)` for each parked request |
| 3. Per-request `threading.Timer` | `resolution_registry.py:238-242` | `entry.timer = threading.Timer(timeout_seconds, self._timer_fire, args=(request_id,))`; daemon thread, started immediately |
| 4. Timer fire synthesizes timeout resolution | `resolution_registry.py:485-496` | `_timer_fire` constructs `DecisionResolution(payload={}, kind=kind, is_timeout=True)`; reuses the reserve/commit_signal CAS primitive |
| 5. `command_approval`/`file_change` timeout dispatch | `delegation_controller.py:1544-1549` | Worker dispatches `{"decision": "cancel"}` via `entry.session.respond(request.wire_request_id, ...)` |
| 6. Post-dispatch bookkeeping (success path) | `delegation_controller.py:1591-1606` | `record_timeout(dispatch_result="succeeded")` + `update_parked_request(None)` + `_write_completion_and_audit_timeout(...)` (helper writes audit `action="approval_timeout"` at `delegation_controller.py:1734`) + `registry.discard(...)` |

**Implications:**

- This is **plugin-owned, hardcoded today, not App Server-owned for the observed cancellation path.** The original probe (below) was framed pre-resolution; its question of "does App Server abandon the request before our timeout?" is **not needed for Candidate A attempt 2** unless we want to characterize App Server behavior beyond the plugin-owned path. Our timer is **scheduled at 900 seconds** and fires the observed `cancel` dispatch; the audit row's `+15m10s` delta represents the schedule plus dispatch/scheduling/bookkeeping overhead, not a precise timer measurement. App Server's independent abandonment behavior under conditions where our timer does not fire (e.g., a hypothetical longer/shorter App Server timeout, or behavior under different versions) is not characterized by the current evidence.
- ~~The L116 comment "configurable via env later" indicates **env tuning is not implemented today.** Changing the TTL for a single run requires a code edit and plugin reload, not a flag flip.~~ **Superseded:** Env tuning landed in Packet 1. Set `CODEX_COLLAB_APPROVAL_OPERATOR_WINDOW_SECONDS=<seconds>` before plugin start; no code edit needed. See `delegation_controller.py:117-157` and package README.
- TTL is **per parked request, not per delegate job.** Each parked request gets its own 900-second timer in `ResolutionRegistry`. A delegation that produces multiple sequential approval requests (e.g., smoke + probes in Candidate A attempt 2) has each request's TTL run independently — fresh 900-second window per parked request, not a shared budget across the delegation.

The original probe framing is retained below for historical context.

---

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
| What do platform defaults grant? | **Sufficient grants for the canonical smoke workload** (`mkdir -p`, `printf >`, `test -f`, `cat <worktree-path>`, all under `/bin/zsh -lc` invocation; the agent also successfully used `/bin/bash -lc` in probe 1's adapted chain). Per OpenAI's Codex App Server docs, `includePlatformDefaults: True` on macOS appends a curated platform-default Seatbelt policy for restricted-read sessions. Specific paths NOT enumerated in OpenAI public docs (so the exact platform-default path set is not catalogued by this run record), but empirically includes `/bin/zsh`, `/bin/bash`, and the supporting binaries + dynamic-linker dependencies needed for `mkdir`, `printf`, `test`, `cat`. (See att3 evidence: `Variant: Candidate A (attempt 1)` ▶ `Attempt 3 evidence: completed`.) |
| Does the security boundary hold for host secrets and sibling worktrees? | **YES.** All three security probes (Network: `curl https://example.com`; Sensitive-path: `cat /etc/passwd`; Sibling-worktree: `cat <Baseline-att1-worktree>/.gitignore`) returned **BLOCKED** verdicts. Enforcement mechanism: App Server interrupts shell mid-execution at the boundary-violating operation, uniform across operation classes (network, sensitive-path read, sibling-worktree read). Refutes the earlier hypothesis that filesystem and network enforcement happen at different layers. (See `Security probes (post-att3)` subsection at L1160.) |
| Is a narrow readable-root grant sufficient, or is Candidate A needed? | **Candidate A is sufficient and currently NOT-yet-known whether narrower would work.** Att3 demonstrated Candidate A's True-flag config works for the canonical smoke workload; Candidate B (per-binary explicit `readableRoots` like `/bin`, `/usr/bin`, `/usr/lib`) was demoted to post-att3 conditional in scope-note. Whether narrower per-binary grants could replace platform defaults is an OPEN MINIMIZATION QUESTION, not a blocker. (See `Candidate B Matrix` scope note for 3-mode role framing.) |
| Does `accept` resume the action and produce artifacts? | **YES.** Att3 demonstrated `decide(approve)` → `{"decision": "accept"}` per the six-row binding contract at `delegation_controller.py:2779` → worker `entry.session.respond(parsed.wire_request_id, response_payload)` at `delegation_controller.py:1229` → App Server proceeds → shell executes → smoke artifact `result.txt` produced byte-perfect (content `delegate execution smoke\n`) + autopilot `test-results.json` produced. Wire-id type preservation (string `"0"`) was exercised successfully. End-to-end verified. |
| Is approval escalation bounded or noisy after sandbox execution works? | **For canonical workload: BOUNDED** (att3 needed exactly 1 approval cycle to reach terminal). **For probe (boundary-violating) workloads: NOISY by design** under `untrusted` mode — each probe drove the agent through 1-3 deny cycles before terminalizing. Probe 1 (Network): 4 cycles. Probe 2 (Sensitive-path): 2 cycles. Probe 3 (Sibling-worktree): 3 cycles. The noise pattern scales with how many distinct shell actions the agent attempts under `untrusted`. The "guarded pre-authorized approve" pattern (single approve for canonical chain) is bounded; manual-decide-per-cycle is noisy. |
| Did amendment admission become required? | **NO.** S7b (response-required) did NOT fire across Baseline + Candidate A att1+att2+att3 + probes 1+2+3. `available_decisions` consistently included plain `accept`/`decline` as valid options across all `command_approval` requests; `acceptWithExecpolicyAmendment` was offered as one of 6 options but never the sole valid progressing path. Plain `approve` → wire `accept` sufficed throughout. (See Symptom Attribution section: S7a (payload-presence) fired informationally; S7b (response-required) did not fire.) |
| Did any Packet 1 capture/registry/dispatch path regress? | **NO.** Storage-evidence integrity verified via JSONL inspection across all attempts and probes. Capture (att3 request 0 PendingRequestStore `op:create` → `op:record_response_dispatch` with `response_payload: {"decision": "accept"}` → `op:mark_resolved`), registry (per-request 900s `threading.Timer` + reserve/commit_signal CAS at `resolution_registry.py:238-242`), and dispatch (`entry.session.respond(...)` at `delegation_controller.py:1229`) all worked as designed. No `dispatch_error`, no `interrupt_error`, no `internal_abort` rows observed in any successful path. |
| Recommended implementation slice | **Promote Candidate A's policy configuration as the sandbox-policy patch.** Configuration: `'type': 'workspaceWrite'` + `'writableRoots': [worktree-only]` + `'readOnlyAccess': {'type': 'restricted', 'readableRoots': [worktree-only], 'includePlatformDefaults': True}` + `'networkAccess': False` + `'excludeSlashTmp': True` + `'excludeTmpdirEnvVar': True`. Diff: change `includePlatformDefaults: False` → `True` in `packages/plugins/codex-collaboration/server/runtime.py:23-50` (`build_workspace_write_sandbox_policy`). Candidate B (narrower per-binary `readableRoots`) is post-att3 conditional minimum-grant minimization — optional, not blocking. (See Candidate A Branch decision section above.) |

## Follow-Up Changes To File

Do not edit the assessment unless this run disproves its recommendation. Record
diagnostic-specific calibration and branch precedence outcomes in this run
record.

| Follow-up | Needed? | Owner | Notes |
|---|---|---|---|
| Sandbox policy patch | **YES** | codex-collaboration plugin maintainers | Apply Candidate A configuration as default for v1 sandbox policy. Diff scope: `packages/plugins/codex-collaboration/server/runtime.py:23-50` `build_workspace_write_sandbox_policy` — change `'includePlatformDefaults': False` → `True`. Otherwise preserve current configuration (workspaceWrite, worktree-only writableRoots/readableRoots, networkAccess: False, excludeSlashTmp: True, excludeTmpdirEnvVar: True). Smoke + 3 security probes empirically validated (att3 + probes 1-3). |
| Approval-policy default decision | **NO change needed** | codex-collaboration plugin maintainers | `untrusted` mode is appropriate for delegated work. Per-request approval works correctly; wire-id type preservation works; six-row binding contract holds at runtime. Operator-loop discipline is the load-bearing constraint, not the approval policy itself. Note: ~~`_APPROVAL_OPERATOR_WINDOW_SECONDS = 900` at `delegation_controller.py:116` is hardcoded with `# configurable via env later` comment — env-tuning would be a future improvement (see "carry-forward" item in Candidate A Branch decision).~~ **Superseded:** Env-tuning landed in Packet 1 via `CODEX_COLLAB_APPROVAL_OPERATOR_WINDOW_SECONDS` (`delegation_controller.py:117-157`; README-documented). |
| Amendment-admission ticket / Packet 2 | **NO** | N/A | S7b (response-required) did not fire across Baseline + Candidate A att1/2/3 + security probes. `acceptWithExecpolicyAmendment` was always offered as one of 6 options but never the sole valid path. Plain `approve` (mapping to wire `accept`) sufficed for all observed canonical and adapted approval cycles. Amendment admission is not currently required. |
| Packet 1 regression ticket | **NO** | N/A | No Packet 1 regressions detected. Capture/registry/dispatch paths verified across all attempts and probes via JSONL inspection — no `dispatch_error`, `interrupt_error`, or `internal_abort` rows in any successful path. Six-row binding contract validated empirically by att3's successful approve dispatch. |
| T-02 closure/update | **NO direct change required from this run; CONDITIONAL future update if env-tuning is implemented** | codex-collaboration plugin maintainers (if env-tuning) | Per "Optional App Server Timeout Probe" Resolution: TTL is **plugin-owned at 900s** (`_APPROVAL_OPERATOR_WINDOW_SECONDS` at `delegation_controller.py:116`); not App Server-owned. T-02 audit row 7 ("Partially covered") caveat remains technically valid because we have not directly probed App Server's behavior under conditions where our timer doesn't fire (e.g., a hypothetical longer/shorter App Server timeout). For the canonical workflow this run executed, our 900s timer always fires first and dispatches the cancel. ~~If env-tuning of `_APPROVAL_OPERATOR_WINDOW_SECONDS` is implemented later (the L116 `# configurable via env later` comment indicates intent), T-02 row 7 should reference the env mechanism.~~ **Superseded:** Env-tuning landed — `CODEX_COLLAB_APPROVAL_OPERATOR_WINDOW_SECONDS` at `delegation_controller.py:117-157`. The conditional is satisfied. |
