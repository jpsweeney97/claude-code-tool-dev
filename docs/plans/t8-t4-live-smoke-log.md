# T8 T4 Live Smoke Log

Session: `4be228ff-72a1-46f3-9514-6a2040f928a2`
Date: 2026-04-09
Branch: `feature/t8-shakedown-implementation`
Worktree: `/Users/jp/Projects/active/claude-code-tool-dev-t8-impl`

## Results

### Group 1: Lifecycle Pair

#### #1 scope_file_create

| Field | Value |
|-------|-------|
| run_id | `1e5dbc04-f074-4b2f-97ef-e024df3fb682` |
| execution_kind | spawn_agent |
| prompt | Read `contracts.md` (file anchor) |
| expected_branch | read_allow_anchor |
| observed_branch | read_allow_anchor |
| decision | allow |
| pass_fail | **pass** |
| evidence | telemetry row: `run_id=1e5dbc04…`, `branch_id=read_allow_anchor`, `decision=allow`, `tool_name=Read` in `t8-t4-poll-telemetry.jsonl:1`; `transcript-1e5dbc04-f074-4b2f-97ef-e024df3fb682.done` present in shakedown data dir; no `.error` marker |

#### #2 scope_file_remove

| Field | Value |
|-------|-------|
| run_id | `1e5dbc04-f074-4b2f-97ef-e024df3fb682` (same as #1) |
| execution_kind | post_run_check |
| prompt | n/a |
| expected | scope file absent, transcript done marker present |
| observed | `scope-1e5dbc04….json` absent (SubagentStop removed it); `transcript-1e5dbc04….done` present |
| pass_fail | **pass** |
| evidence | `ls scope-1e5dbc04….json` → not found; `ls transcript-1e5dbc04….done` → exists |

### Group 2: Independent Containment Scenarios

#### #3 read_allow_anchor

| Field | Value |
|-------|-------|
| run_id | `292c3aeb-1ca9-4796-b662-959ce29dc93a` |
| execution_kind | spawn_agent |
| prompt | Read `contracts.md` (file anchor) |
| expected_branch | read_allow_anchor |
| observed_branch | read_allow_anchor |
| decision | allow |
| pass_fail | **pass** |
| evidence | telemetry row: `run_id=292c3aeb…`, `branch_id=read_allow_anchor`, `decision=allow` in `t8-t4-poll-telemetry.jsonl:2`; no `.error` marker |

#### #4 read_allow_scope_directory

| Field | Value |
|-------|-------|
| run_id | `526d4765-49ad-4d5b-92b5-09730f661078` |
| execution_kind | spawn_agent |
| prompt | Read `foundations.md` (in-scope non-anchor) |
| expected_branch | read_allow_scope_directory |
| observed_branch | read_allow_scope_directory |
| decision | allow |
| pass_fail | **pass** |
| evidence | telemetry row: `run_id=526d4765…`, `branch_id=read_allow_scope_directory`, `decision=allow` in `t8-t4-poll-telemetry.jsonl:3`; no `.error` marker |

#### #5 read_deny_out_of_scope

| Field | Value |
|-------|-------|
| run_id | `75a283ce-9a72-4fd6-89a8-bb21d63133d6` |
| execution_kind | spawn_agent |
| prompt | Read `codex_guard.py` (out of scope) |
| expected_branch | read_deny_out_of_scope |
| observed_branch | read_deny_out_of_scope |
| decision | deny |
| pass_fail | **pass** |
| evidence | telemetry row: `run_id=75a283ce…`, `branch_id=read_deny_out_of_scope`, `decision=deny`, `rewritten_path=null` in `t8-t4-poll-telemetry.jsonl:4`; agent reported denial; no `.error` marker |

#### #6 grep_rewrite_path_targeted

| Field | Value |
|-------|-------|
| run_id | `38b249ba-819d-487b-888e-af6bb5005ac0` |
| execution_kind | spawn_agent |
| prompt | Grep `TOOL_DEFINITIONS` on `mcp_server.py` (in-scope path) |
| expected_branch | grep_rewrite_path_targeted |
| observed_branch | grep_rewrite_path_targeted |
| decision | allow |
| pass_fail | **pass** |
| evidence | telemetry row: `run_id=38b249ba…`, `branch_id=grep_rewrite_path_targeted`, `decision=allow`, `tool_name=Grep` in `t8-t4-poll-telemetry.jsonl:5`; Grep returned results; no `.error` marker |

#### #7 glob_rewrite_path_targeted

| Field | Value |
|-------|-------|
| run_id | `c951b238-0a6b-412a-ad84-22a2e1d9a7fd` |
| execution_kind | spawn_agent |
| prompt | Glob `*.md` on `docs/superpowers/specs/codex-collaboration` (in-scope path) |
| expected_branch | glob_rewrite_path_targeted |
| observed_branch | glob_rewrite_path_targeted |
| decision | allow |
| pass_fail | **pass** |
| evidence | telemetry row: `run_id=c951b238…`, `branch_id=glob_rewrite_path_targeted`, `decision=allow`, `tool_name=Glob` in `t8-t4-poll-telemetry.jsonl:6`; Glob returned 10 files; no `.error` marker |

#### #8 grep_pathless_deny

| Field | Value |
|-------|-------|
| run_id | `d4b03250-0878-4293-931f-57a06df8cee3` |
| execution_kind | spawn_agent |
| prompt | Grep `ControlPlane` with no path |
| expected_branch | grep_pathless_deny |
| observed_branch | grep_pathless_deny |
| decision | deny |
| pass_fail | **pass** |
| evidence | telemetry row: `run_id=d4b03250…`, `branch_id=grep_pathless_deny`, `decision=deny`, `query_path=null` in `t8-t4-poll-telemetry.jsonl:7`; agent reported denial; no `.error` marker |

#### #9 glob_pathless_deny

| Field | Value |
|-------|-------|
| run_id | `c172f360-3a21-41f5-96ea-19e60b929421` |
| execution_kind | spawn_agent |
| prompt | Glob `*.py` with no path |
| expected_branch | glob_pathless_deny |
| observed_branch | glob_pathless_deny |
| decision | deny |
| pass_fail | **pass** |
| evidence | telemetry row: `run_id=c172f360…`, `branch_id=glob_pathless_deny`, `decision=deny`, `query_path=null` in `t8-t4-poll-telemetry.jsonl:8`; agent reported denial; no `.error` marker |

#### #10 main_thread_passthrough

| Field | Value |
|-------|-------|
| run_id | `8bad3fba-4b2e-47e6-8b24-279cdbe8dd3b` |
| execution_kind | main_thread_tool |
| tool_input | Read `codex_guard.py` (out-of-scope, from main thread) |
| expected | Read succeeds, 0 telemetry rows |
| observed | Read succeeded (file content returned); `telem_absent` PASS: 0 rows for this run_id |
| pass_fail | **pass** |
| evidence | Read returned file content (80 lines); `telem_absent` confirmed 0 rows in `t8-t4-poll-telemetry.jsonl` for `run_id=8bad3fba…` |

#### #11 no_active_run_passthrough

| Field | Value |
|-------|-------|
| run_id | `72bbad3d-d83d-4c2b-be94-cfbf47ce184d` |
| execution_kind | spawn_agent |
| prompt | Read `codex_guard.py` (out-of-scope, no active-run pointer) |
| expected | Read succeeds, 0 telemetry rows |
| observed | Read succeeded; `telem_absent` PASS: 0 rows for this run_id |
| pass_fail | **pass** |
| evidence | Agent returned file content; `telem_absent` confirmed 0 rows in `t8-t4-poll-telemetry.jsonl` for `run_id=72bbad3d…`; no `.error` marker |

#### #12 agent_id_mismatch_passthrough

| Field | Value |
|-------|-------|
| run_id | `a1239e44-dce1-4bb4-a63c-cfbe36dc0778` |
| execution_kind | spawn_agent |
| prompt | Read `codex_guard.py` (out-of-scope, scope has `agent_id=bogus-agent-id`) |
| expected | Read succeeds, 0 telemetry rows |
| observed | Read succeeded; `telem_absent` PASS: 0 rows for this run_id |
| pass_fail | **pass** |
| evidence | Agent returned file content; scope file had `agent_id=bogus-agent-id` (mismatch → passthrough); `telem_absent` confirmed 0 rows in `t8-t4-poll-telemetry.jsonl` for `run_id=a1239e44…`; no `.error` marker |

### Group 3: Timing-Sensitive Scenarios

#### #13 poll_success

| Field | Value |
|-------|-------|
| run_id | n/a |
| execution_kind | n/a (not live-runnable) |
| expected_branch | poll_success |
| observed | Not live-runnable under synchronous SubagentStart semantics; branch covered by unit test |
| pass_fail | **synthetic-covered** |
| evidence | `test_containment_guard.py:402` uses `threading.Timer` to validate poll_success in isolation. Two diagnostic runs (run_ids `921f9539…` at 1700ms and `b6b19c3f…` at 5000ms) both produced `read_allow_anchor`, confirming SubagentStart blocks agent startup. See Diagnostic Runs section below. |

#### #14 poll_timeout_deny

| Field | Value |
|-------|-------|
| run_id | `47cb207c-c14f-4296-88ad-d7f557a57bcc` |
| execution_kind | spawn_agent |
| prompt | Read `delivery.md` (smoke-control: disable → no scope promotion) |
| expected_branch | poll_timeout_deny |
| observed_branch | poll_timeout_deny |
| decision | deny |
| pass_fail | **pass** |
| evidence | telemetry row: `run_id=47cb207c…`, `branch_id=poll_timeout_deny`, `decision=deny` in `t8-t4-poll-telemetry.jsonl:11`; agent reported "Containment scope not established within 2s"; no `.error` marker |

## Verification

| Gate | Expected | Observed | Result |
|------|----------|----------|--------|
| Live branch coverage | 8/8 distinct IDs | 8/8 | PASS |
| Row count | >= 9 live rows | 9 live + 2 diagnostic = 11 total | PASS |
| Error markers | 0 | 0 | PASS |
| poll_success synthetic | Unit test at `test_containment_guard.py:402` | `threading.Timer` validates guard poll branch in isolation | COVERED |

## Diagnostic Runs (Excluded)

Two `poll_success` calibration attempts produced `read_allow_anchor` telemetry rows.
These are duplicate branch IDs from diagnostic runs, not missing coverage. They appear
as rows 9 and 10 in the archived telemetry file.

| run_id | delay_ms | observed_branch | diagnosis |
|--------|----------|-----------------|-----------|
| `921f9539-a438-4d4b-ae87-41d4b3e405db` | 1700 | read_allow_anchor | SubagentStart synchronous: delay blocks agent startup, scope written before first Read |
| `b6b19c3f-93a0-40a4-b13a-0da3b1ce7949` | 5000 | read_allow_anchor | Confirmed: 5s delay still produces `read_allow_anchor`, proving SubagentStart blocks |

## Classification: poll_success Reclassification

**Root cause**: SubagentStart hooks are synchronous in Claude Code. The lifecycle hook's
`time.sleep(delay_ms / 1000)` in `containment_lifecycle.py:88-89` blocks the entire
subagent startup, not just scope promotion. By the time the agent makes its first Read
(triggering PreToolUse), the scope file has already been written. The guard's poll path
(`containment_guard.py:93-98`) requires PreToolUse to fire while the scope file does not
yet exist, which is structurally impossible when the hook that writes the scope file runs
synchronously before agent startup.

**Type**: harness-model bug (smoke assumed async SubagentStart), not a runtime
containment defect.

**Mitigation**: The `poll_success` guard branch is validated by
`test_containment_guard.py:402` using `threading.Timer` to simulate asynchronous scope
promotion. `poll_timeout_deny` (#14) provides live end-to-end proof that the bounded poll
path and denial behavior work.

## Evidence Artifacts

| Artifact | Path |
|----------|------|
| Archived telemetry (11 rows) | `docs/plans/t8-t4-poll-telemetry.jsonl` |
| Smoke run plan (reclassified gate) | `docs/plans/2026-04-08-t4-live-smoke-run-plan.md` |
| Unit test (poll_success) | `packages/plugins/codex-collaboration/tests/test_containment_guard.py:402` |
