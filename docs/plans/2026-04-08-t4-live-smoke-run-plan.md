# T4 Live Smoke Run Plan

## Prerequisites

| Item | Value | How to verify |
|------|-------|---------------|
| Pre-smoke fixes | All applied and tests green (47 passing) | `uv run --directory packages/plugins/codex-collaboration pytest tests/test_containment*.py` |
| Worktree | `/Users/jp/Projects/active/claude-code-tool-dev-t8-impl` on `feature/t8-shakedown-implementation` | `git branch --show-current` |
| Plugin data dir | `~/.claude/plugins/data/codex-collaboration-inline/` | `ls` the directory |
| Telemetry clean slate | No prior telemetry from test runs | See reset step below |
| Session launch | `cd /Users/jp/Projects/active/claude-code-tool-dev-t8-impl && claude --plugin-dir packages/plugins/codex-collaboration` | `/hooks` shows SubagentStart + SubagentStop + PreToolUse `^(Read\|Grep\|Glob)$`; `/agents` shows `shakedown-dialogue` |
| Session ID published | SessionStart hook writes `session_id` to data dir | `cat $DATA_DIR/session_id` |

Reset telemetry before starting:

```bash
DATA_DIR=~/.claude/plugins/data/codex-collaboration-inline
trash "$DATA_DIR/shakedown/poll-telemetry.jsonl" 2>/dev/null || true
```

### Constants

```bash
DATA_DIR=~/.claude/plugins/data/codex-collaboration-inline
REPO_ROOT=/Users/jp/Projects/active/claude-code-tool-dev-t8-impl
SETUP="python3 $REPO_ROOT/packages/plugins/codex-collaboration/scripts/containment_smoke_setup.py --data-dir $DATA_DIR --repo-root $REPO_ROOT"
```

### Evidence Helper

Every telemetry-producing scenario uses `run_id`-filtered evidence checks instead of `tail -1`. This binds each observation to exactly the scenario that produced it.

```bash
# Check telemetry for a specific run (use after each telemetry-producing scenario)
telem_check() {
  python3 -c "
import json, sys
rows = [json.loads(l) for l in open('$DATA_DIR/shakedown/poll-telemetry.jsonl') if json.loads(l).get('run_id') == '$1']
for r in rows: print(json.dumps(r, indent=2))
print(f'--- {len(rows)} row(s) for run_id=$1')
" 2>/dev/null || echo "--- 0 rows (no telemetry file)"
}

# Check absence of telemetry for a specific run (use after passthrough scenarios)
# Exits 0 only on confirmed zero rows. Exits 1 on unexpected telemetry.
telem_absent() {
  python3 -c "
import json, os, sys
path = '$DATA_DIR/shakedown/poll-telemetry.jsonl'
if not os.path.exists(path):
    print('PASS: no telemetry file exists')
    sys.exit(0)
rows = [json.loads(l) for l in open(path) if json.loads(l).get('run_id') == '$1']
if rows:
    for r in rows: print(json.dumps(r, indent=2))
    print(f'FAIL: expected 0 rows for run_id=$1, got {len(rows)}')
    sys.exit(1)
print('PASS: 0 rows for run_id=$1')
"
}
```

### Execution Model

Two terminals:

- **Terminal A** — the Claude Code session (interactive, `--plugin-dir`)
- **Terminal B** — the operator terminal (runs `prepare` and `cleanup`, reads recipes)

Each scenario follows this cycle:

1. **Terminal B**: `$SETUP prepare <scenario_id>` — read the JSON recipe (capture `run_id`)
2. **Terminal A**: execute the recipe (spawn agent with the printed prompt, or execute main-thread tool, or check post-run state)
3. **Terminal B**: observe evidence using `run_id`-filtered checks
4. Record the result in `t8-t4-live-smoke-log.md`
5. **Terminal B**: `$SETUP cleanup <run_id>`

## Scenario Sequence

Three ordered groups. Within each group, run scenarios in listed order.

### Group 1: Lifecycle pair

These two scenarios share a single `run_id` and must run in this order. `scope_file_remove` verifies the state left behind by `scope_file_create`. Do not run cleanup between them.

| # | Scenario | Execution | Key observation |
|---|----------|-----------|-----------------|
| 1 | `scope_file_create` | Spawn agent, prompt in-scope Read | Telemetry row with matching `run_id` proves guard saw scope; `transcript-<run_id>.done` proves lifecycle completed |
| 2 | `scope_file_remove` | Post-run check only (no agent spawn) | scope file absent after stop (SubagentStop removed it), `transcript-<run_id>.done` present |

**Why the scope file itself is not checked directly:** SubagentStop removes the scope file as part of normal lifecycle. By the time the operator can check, it is already gone. The durable evidence that the scope file existed is the telemetry row — the guard can only produce a `read_allow_*` decision if the scope file was present when the Read fired.

```bash
# Step 1: scope_file_create
$SETUP prepare scope_file_create
# Note the run_id from the JSON output: RUN_ID=<...>

# Terminal A: spawn shakedown-dialogue with the recipe's prompt
# Wait for agent to complete

# Terminal B: verify durable evidence
telem_check $RUN_ID
# Expected: 1 row with branch_id=read_allow_anchor, decision=allow, run_id=$RUN_ID
ls $DATA_DIR/shakedown/transcript-$RUN_ID.done
# Expected: exists (proves SubagentStop lifecycle completed)

# Step 2: scope_file_remove (same run_id, no cleanup between)
$SETUP prepare scope_file_remove --run-id $RUN_ID
# execution_kind is post_run_check, no agent spawn

# Verify:
ls $DATA_DIR/shakedown/scope-$RUN_ID.json 2>/dev/null && echo "FAIL: scope file still exists" || echo "PASS: scope file removed by SubagentStop"
ls $DATA_DIR/shakedown/transcript-$RUN_ID.done
# Expected: exists

# Cleanup both
$SETUP cleanup $RUN_ID
```

### Group 2: Independent containment scenarios

Any order. Each gets a fresh `run_id`.

| # | Scenario | Execution | Key observation |
|---|----------|-----------|-----------------|
| 3 | `read_allow_anchor` | Spawn agent, Read a file anchor | Read succeeds, telemetry: `read_allow_anchor` |
| 4 | `read_allow_scope_directory` | Spawn agent, Read in-scope non-anchor | Read succeeds, telemetry: `read_allow_scope_directory` |
| 5 | `read_deny_out_of_scope` | Spawn agent, Read out-of-scope file | Agent reports denial, telemetry: `read_deny_out_of_scope` |
| 6 | `grep_rewrite_path_targeted` | Spawn agent, Grep with in-scope path | Grep executes (rewritten), telemetry: `grep_rewrite_path_targeted` |
| 7 | `glob_rewrite_path_targeted` | Spawn agent, Glob with in-scope path | Glob executes (rewritten), telemetry: `glob_rewrite_path_targeted` |
| 8 | `grep_pathless_deny` | Spawn agent, Grep without path | Agent reports denial, telemetry: `grep_pathless_deny` |
| 9 | `glob_pathless_deny` | Spawn agent, Glob without path | Agent reports denial, telemetry: `glob_pathless_deny` |
| 10 | `main_thread_passthrough` | Main-thread Read of out-of-scope file | Read succeeds, **no** telemetry row for this `run_id` |
| 11 | `no_active_run_passthrough` | Spawn agent, Read out-of-scope file | Read succeeds (no containment), **no** telemetry for this `run_id` |
| 12 | `agent_id_mismatch_passthrough` | Spawn agent, Read out-of-scope file | Read succeeds (agent_id mismatch), **no** telemetry for this `run_id` |

Per-scenario operator script (telemetry-producing scenarios #3–#9):

```bash
$SETUP prepare <scenario_id>
# Note the run_id: RUN_ID=<...>

# Terminal A: spawn shakedown-dialogue with the recipe's prompt

# Terminal B: check evidence filtered by run_id
telem_check $RUN_ID
# Expected: 1 row with the scenario's branch_id

$SETUP cleanup $RUN_ID
```

Per-scenario operator script (passthrough scenarios #10–#12):

```bash
$SETUP prepare <scenario_id>
# Note the run_id: RUN_ID=<...>

# Terminal A: execute per scenario type:
#   main_thread_passthrough: Read the file directly (not via agent)
#   no_active_run_passthrough / agent_id_mismatch_passthrough: spawn shakedown-dialogue

# Terminal B: verify no telemetry was emitted for this run
telem_absent $RUN_ID
# Expected: 0 rows

$SETUP cleanup $RUN_ID
```

### Group 3: Timing-sensitive scenarios

Run last. Each involves a real delay (1.7s for poll_success, 2s timeout for poll_timeout_deny).

| # | Scenario | Execution | Key observation |
|---|----------|-----------|-----------------|
| 13 | `poll_success` | Spawn agent, Read with delayed scope promotion | Read succeeds after poll, telemetry: `poll_success` |
| 14 | `poll_timeout_deny` | Spawn agent, Read with disabled scope promotion | Agent reports denial after ~2s, telemetry: `poll_timeout_deny` |

#### `poll_success` timing calibration

The `--delay-ms` value must satisfy two constraints simultaneously:

- **Above** the subagent startup time (Phase 0 median: 1524ms) so the guard fires before scope promotion
- **Below** 2000ms (poll timeout) so promotion lands before the guard gives up

Default: **1700ms** — provides ~176ms margin above startup and ~300ms below timeout.

```bash
$SETUP prepare poll_success --delay-ms 1700
# Note the run_id: RUN_ID=<...>
```

If the scenario fails, diagnose and adjust:

| Symptom | Diagnosis | Adjustment |
|---------|-----------|------------|
| Telemetry shows `read_allow_anchor` instead of `poll_success` | Scope was promoted before the guard fired — delay too short | Increase by 100ms |
| Agent reports denial, telemetry shows `poll_timeout_deny` | Scope was not promoted in time — delay too long | Decrease by 100ms |
| Telemetry shows `poll_success` | Correct | None |

**Retry procedure:** If calibration requires a retry, clean up and re-prepare. The retry adds extra telemetry rows for the retried `run_id`, but Phase 2 verification uses distinct branch IDs, not row count, so retries do not invalidate the exit gate. Document the final working `--delay-ms` value in the smoke log.

```bash
# On retry: cleanup the failed attempt, re-prepare with adjusted delay
$SETUP cleanup $RUN_ID
$SETUP prepare poll_success --delay-ms <adjusted_value>
# New RUN_ID from output
```

## Post-Run Verification

After all 14 scenarios:

### 1. Branch coverage (primary gate)

```bash
python3 -c "
import json, sys
branches = {json.loads(line)['branch_id'] for line in open('$DATA_DIR/shakedown/poll-telemetry.jsonl')}
expected = {
    'glob_pathless_deny',
    'glob_rewrite_path_targeted',
    'grep_pathless_deny',
    'grep_rewrite_path_targeted',
    'poll_success',
    'poll_timeout_deny',
    'read_allow_anchor',
    'read_allow_scope_directory',
    'read_deny_out_of_scope',
}
missing = expected - branches
extra = branches - expected
for b in sorted(branches): print(f'  {b}')
print(f'\n{len(branches)} distinct branches')
if missing: print(f'MISSING: {sorted(missing)}')
if extra: print(f'UNEXPECTED: {sorted(extra)}')
ok = not missing and not extra
print('PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
"
```

Expected: exactly the 9 branch IDs listed, no more, no fewer. Retries produce duplicate rows for existing branch IDs — they do not create new distinct IDs. Any unexpected branch ID is evidence of branch drift or a telemetry bug and must fail the gate.

### 2. Row sanity check

```bash
wc -l $DATA_DIR/shakedown/poll-telemetry.jsonl
```

Expected: **at least 10** rows. The 10 telemetry-producing scenarios are: `scope_file_create` (emits `read_allow_anchor`), scenarios #3–#9, and scenarios #13–#14. More than 10 is acceptable if `poll_success` required calibration retries. Fewer than 10 means a scenario did not emit telemetry.

### 3. Fill the smoke log

Transfer observed results into `docs/plans/t8-t4-live-smoke-log.md`.

### 4. Archive telemetry

Copy the telemetry file into the worktree as evidence:

```bash
cp $DATA_DIR/shakedown/poll-telemetry.jsonl $REPO_ROOT/docs/plans/t8-t4-poll-telemetry.jsonl
```

### 5. T4 exit gate

All 14 rows filled. All `pass_fail` = pass. Branch coverage = 9/9.

## Post-Smoke Cleanup

```bash
# Remove the runtime telemetry file (evidence is archived in step 4)
trash "$DATA_DIR/shakedown/poll-telemetry.jsonl"
```

Verify residual state:

```bash
ls $DATA_DIR/shakedown/
```

Expected residual files:
- `ordering-marker-*.json` and `ordering-result-*.json` from T3
- `transcript-<run_id>.jsonl` — copied transcript for each scenario that spawned an agent (preserved by `cleanup_scenario` as evidence)
- `transcript-<run_id>.done` — success marker for each completed agent run
- `transcript-<run_id>.error` — failure marker if transcript copy failed (presence indicates a problem during the run; investigate before marking the scenario as pass)

All transcript artifacts are deliberately preserved by `cleanup_scenario`. `clean_stale_files` only removes files older than 24 hours, so fresh artifacts will persist across subsequent `prepare` calls within the same day. Remove manually with `trash` after evidence is archived if a clean data directory is needed.

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| `poll_success` timing mismatch | Use 1700ms default. Adjust per the calibration table. Document final value |
| Stale state from a failed scenario bleeds into the next | Always `cleanup <run_id>` between scenarios. Before retrying, inspect `ls $DATA_DIR/shakedown/` for leftover `active-run-*`, `seed-*`, `scope-*` files |
| Agent ignores the prompt and retries after denial | The `shakedown-dialogue.md` instructions prohibit retry. If it happens, the first tool call still produces the correct telemetry — extra rows are filtered by `run_id` so they don't contaminate other scenarios |
| `CLAUDE_PLUGIN_DATA` differs from expected | Verify with `cat $DATA_DIR/session_id` before starting. If empty, the SessionStart hook did not fire — restart the Claude session |

## Origin

Phase 0 pre-smoke fixes (branch-ID isolation, Glob field-preservation test, delay parameterization) were completed during the T4 hardening session and are subsumed by the broader 7-fix hardening pass. See the prior handoff for details.

This plan was first produced during the T4 implementation review session (2026-04-08), then revised after two adversarial reviews:

1. **First review** (prior session, 5 findings): branch-ID exception coupling, timing margin, Glob coverage gap, lifecycle ordering, telemetry growth — all addressed in Phase 0 fixes.
2. **Second review** (this session, 5 findings + 1 systemic): scope_file_create unobservable post-run, retry/row-count conflict, weak passthrough verification via `tail -1`, cleanup/harness contradiction, `rm -f` policy violation, and the systemic pattern of weak-signal evidence. All addressed in this revision.
