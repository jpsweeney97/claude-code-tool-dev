# T-01 Delegate Execution Diagnostic Run Record

Date: 2026-04-28

Status: draft first-run record, not yet executed

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
| Candidate B | Narrow `readableRoots` additions only — see Candidate B Matrix below | Same approval policy as baseline unless explicitly changed | Conditional. Run only if Candidate A works but grants wider read access than desired. |

### Candidate B Matrix

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
        `build_workspace_write_sandbox_policy`.** `runtime.py` does not
        import `sys` or `logging` at module top, so the patch must add an
        import. Insert immediately before the `return` statement:

        ```python
        # variant instrumentation (remove after diagnostic)
        import sys
        print(
            f"[VARIANT-LABEL] sandboxPolicy={policy!r}",
            file=sys.stderr,
            flush=True,
        )
        ```

        Replace `policy` with whichever local variable name the function
        uses for its return value (read the patched function before
        copying — current source assigns the dict literal directly to
        `return`, so the patch must also extract it to a local variable
        first).

        **Site 2: call site, `delegation_controller.py:1327`.**
        `delegation_controller.py` already imports `logging` at module
        top (verified at the file's import block). Patch the call site
        to extract the policy to a local, log it, then pass it through:

        ```python
        # variant instrumentation (remove after diagnostic)
        import logging
        _variant_logger = logging.getLogger(__name__)
        _variant_policy = build_workspace_write_sandbox_policy(worktree_path)
        _variant_logger.warning(
            "[VARIANT-LABEL] sandboxPolicy=%r", _variant_policy
        )
        # then in the kwarg list, pass _variant_policy instead of the
        # build_workspace_write_sandbox_policy(worktree_path) inline call:
        # sandbox_policy=_variant_policy,
        ```

        Capture stderr/stdout (build-site emit) or the configured logging
        sink (call-site emit) for the variant's run and paste the emitted
        payload into the per-variant evidence block.
      - **App Server access log** if the operator's App Server build emits
        one and the path is known. Record the log path and grep for
        `turn/start` against the variant's job id timestamp.
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
  Precedence #1) and rerun.
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
| Plugin process start timestamp | Required. ISO-8601 UTC of the post-restart process start. `ps -o lstart -p <PID>` emits a non-ISO format like `Tue Apr 28 04:56:25 2026` — record either the raw output as-emitted **or** normalize to ISO-8601 UTC (e.g., `date -u -j -f "%a %b %d %H:%M:%S %Y" "<lstart-output>" +"%Y-%m-%dT%H:%M:%SZ"` on macOS, or `date -u -d "<lstart-output>" +"%Y-%m-%dT%H:%M:%SZ"` on Linux). State which form was used. Must be **later than** `Patch applied at` above; if it is earlier or equal, the running process predates the patch and the variant is invalid (rerun after a fresh restart). For Baseline (where `Patch applied at` is N/A), the timestamp still anchors the run identity but no inequality applies. | TBD |
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
     fired a non-ratio branch (S1, S6, S7), keep the classification.

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
