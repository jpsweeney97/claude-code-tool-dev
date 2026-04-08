# T8 Implementation Plan: Minimum Runnable Shakedown Packet

## Context

T7 (PR #98, merged) defines the minimum runnable packet for one pre-benchmark integration shakedown on B1. T8 implements it: builds containment hooks, a dialogue agent with the T4 behavioral loop, and an orchestration harness, then runs the shakedown against the 12-item inspection checklist.

**Authority:** `docs/plans/2026-04-07-t7-executable-slice-definition.md` (444 lines, 9 scrutiny rounds)

**Delivery sequence:** `docs/plans/2026-04-08-t8-shakedown-execution-plan-v3.md` — workstream ordering, gate logic, emission contract, acceptance thresholds.

**What this proves:** One contained dialogue with usable local loop state. NOT benchmark readiness, scored-run validity, or full T4 coverage.

**What exists (Layer 1 — reuse):** Dialogue infrastructure at `packages/plugins/codex-collaboration/` with 460 tests: `DialogueController`, `ControlPlane`, `LineageStore`, `OperationJournal`, `ContextAssembly`, plus `codex_guard.py` (PreToolUse credential scanning) and `publish_session_id.py` (SessionStart).

**What's missing (Layer 2 — build):** `dialogue-codex` skill, T4 behavioral loop, containment hooks, scope wiring, transcript capture, metadata, inspection notes.

**Plugin data:** All shakedown runtime state uses `${CLAUDE_PLUGIN_DATA}` — a persistent directory for plugin state that survives plugin updates, resolved to `~/.claude/plugins/data/{id}/` (ref: [plugins-reference#environment-variables](https://code.claude.com/docs/en/plugins-reference#environment-variables)). Created automatically on first reference. Deleted when the plugin is uninstalled from all scopes (unless `--keep-data`).

## Architecture

```
Operator invokes /shakedown-b1

  shakedown-b1 skill (orchestrator):
    1. Reads session_id from ${CLAUDE_PLUGIN_DATA}/session_id
    2. Writes seed file → ${CLAUDE_PLUGIN_DATA}/shakedown/seed-<run_id>.json
       Writes active-run pointer → ${CLAUDE_PLUGIN_DATA}/shakedown/active-run-<session_id>
    3. Spawns Agent(subagent_type="shakedown-dialogue", prompt=<B1 task>)
                        │
                   SubagentStart hook fires (matched on "shakedown-dialogue")
                   → reads seed + agent_id from input
                   → writes scope file (seed + agent_id)
                   → removes seed
                        │
                   Agent runs dialogue (PreToolUse guard active)
                   → Read: check file_path within scope (file anchors + scope directories), deny if not
                   → Grep: rewrite path to file anchor or scope directory via updatedInput
                   → Glob: rewrite path to scope directory via updatedInput
                        │
                   SubagentStop hook fires
                   → removes scope file
                        │
    4. Captures transcript, writes metadata, generates inspection template
```

**Three components:**
- `shakedown-b1` skill — operator-facing harness (seed, spawn, capture)
- `shakedown-dialogue` agent — execution context, loads `dialogue-codex` skill via `skills` frontmatter
- `dialogue-codex` skill — 6 T4 behavioral instructions (claim extraction, registration, scouting, emission)

## Interface Contracts

| Interface | Schema | Writer | Reader |
|-----------|--------|--------|--------|
| Seed file (`seed-<run_id>.json`) | `{session_id, run_id, file_anchors: [...], scope_directories: [...], created_at}` | shakedown-b1 skill | containment_lifecycle.py (SubagentStart) |
| Scope file (`scope-<run_id>.json`) | seed fields + `{agent_id}` | containment_lifecycle.py (SubagentStart) | containment_guard.py (PreToolUse), containment_lifecycle.py (SubagentStop — reads `run_id` for transcript naming) |
| Active run pointer (`active-run-<sid>`) | Contains `run_id` (plain text) | shakedown-b1 skill | containment_guard.py (looks up current run_id from session_id to find scope file) |
| PreToolUse deny | `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "..."}}` | containment_guard.py | Claude Code |
| PreToolUse rewrite | `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow", "updatedInput": {<all fields>}}}` | containment_guard.py | Claude Code |
| Agent name match | `"shakedown-dialogue"` | agent frontmatter `name` | hooks.json SubagentStart/SubagentStop `matcher` |
| Session ID | plain text file | publish_session_id.py | shakedown-b1 skill reads `${CLAUDE_PLUGIN_DATA}/session_id` |

## Phases

### Phase 0: SubagentStart Ordering Validation

**Goal:** Measure the timing gap between SubagentStart completion and the subagent's first PreToolUse. Produces empirical `delta_ms` to evaluate whether the provisional 2-second bootstrap poll window is sufficient for this environment.
**Blocking:** No — the PreToolUse guard includes a bootstrap poll (provisional 2-second window) that bridges timing gaps within that window and fails closed on timeout. Phase 0 is a timing measurement, not a gate.

**Approach:**
1. Create `scripts/ordering_test_start.py`: SubagentStart hook reads `run_id` from `active-run-<session_id>`, writes marker file at `${CLAUDE_PLUGIN_DATA}/shakedown/ordering-marker-<run_id>.json` containing `{"written_at": <monotonic timestamp>}` (use `time.monotonic_ns()` for sub-ms precision)
2. Create `agents/ordering-test.md`: minimal agent (tools: Read only) that reads a known file
3. Create `scripts/ordering_test_check.py`: PreToolUse hook (matched on Read, only for agent_id present) reads `run_id` from `active-run-<session_id>`, records its own `checked_at` timestamp, checks whether marker file exists, and writes result to `${CLAUDE_PLUGIN_DATA}/shakedown/ordering-result-<run_id>.json` containing `{"marker_found": bool, "checked_at": <monotonic timestamp>, "marker_written_at": <from marker file or null>, "delta_ms": <checked_at - marker_written_at or null>}`. The `delta_ms` is the measured SubagentStart-to-PreToolUse gap — the empirical basis for evaluating the provisional 2-second bootstrap poll window
4. Add temporary hook entries to `hooks/hooks.json` for `SubagentStart` (matcher: `ordering-test`) and `PreToolUse` (matcher: `Read`)
5. **Reload:** Plugin components are discovered at session load time. After creating or modifying plugin agents, hooks, or skills mid-session, run `/reload-plugins` to reload the plugin's full component tree (ref: [plugins#develop-more-complex-plugins](https://code.claude.com/docs/en/plugins#develop-more-complex-plugins)). Alternatively, use the `--agents` CLI flag to define the ordering-test agent inline for the test session (avoids file creation and reload entirely). If using `--agents`, skip step 2.
6. Run test: spawn ordering-test agent, check result file

**Outcome:**
- `marker_found: true`, `delta_ms` small (e.g., <100ms) → SubagentStart completes well before PreToolUse. The bootstrap poll is unlikely to be exercised. Proceed to Phase 1.
- `marker_found: true`, `delta_ms` large (e.g., >500ms) → SubagentStart completes before PreToolUse but with less margin than expected. The bootstrap poll may be exercised under load. The 2-second window is sufficient for this environment but note the reduced margin.
- `marker_found: false` → SubagentStart had not completed when PreToolUse fired. The bootstrap poll is load-bearing. If the shakedown's Phase 1 guard successfully bridges the gap during actual runs, the poll window is sufficient. If Phase 1 guard poll timeouts occur, increase the window beyond 2 seconds.

**Files created:**
- `scripts/ordering_test_start.py` (~35 lines — includes monotonic timestamp in marker)
- `scripts/ordering_test_check.py` (~50 lines — captures own timestamp, computes delta_ms)
- `agents/ordering-test.md` (~10 lines)

**Cleanup (explicit — executed before leaving Phase 0):**
1. Remove `agents/ordering-test.md` (if created; not needed if `--agents` CLI was used)
2. Remove temporary `SubagentStart` and `PreToolUse` hook entries from `hooks/hooks.json` — restore to pre-Phase-0 state. Diff `hooks/hooks.json` against its git HEAD to verify only the temporary entries are removed.
3. Remove marker and result files from `${CLAUDE_PLUGIN_DATA}/shakedown/`
4. Keep test scripts (`ordering_test_start.py`, `ordering_test_check.py`) as regression evidence — they have no effect without hook registration.

**Verification:** `git diff hooks/hooks.json` shows no Phase 0 entries. `ls agents/` shows no `ordering-test.md`.

**Verification gate:** Result file exists with `marker_found` and `delta_ms` fields. If `marker_found: true`: `delta_ms` is the measured SubagentStart-to-PreToolUse gap in milliseconds — compare against the provisional 2-second bootstrap poll window. If `marker_found: false`: `delta_ms` is null (SubagentStart had not completed when PreToolUse fired) — the bootstrap poll is load-bearing for this environment; consider whether the 2-second window needs adjustment. Either way, the guard is fail-closed on poll timeout.

---

### Phase 1: Containment Infrastructure

**Goal:** Seed-file/scope-file lifecycle + PreToolUse enforcement.
**Dependencies:** Phase 0 complete (ordering behavior recorded). Guard includes bootstrap poll and is fail-closed on poll timeout regardless of Phase 0 outcome.

#### Phase 1a: Shared Containment Module

**Create:** `server/containment.py` (~80 lines)

Pure-function module imported by both hook scripts:
- `scope_file_path(plugin_data: str, run_id: str) -> Path`
- `seed_file_path(plugin_data: str, run_id: str) -> Path`
- `active_run_path(plugin_data: str, session_id: str) -> Path`
- `read_active_run_id(plugin_data: str, session_id: str) -> str | None` (reads active-run pointer, returns run_id or None)
- `read_json_file(path: Path) -> dict | None` (returns None if missing/corrupt)
- `write_json_file(path: Path, data: dict) -> None` (atomic write via tmp+replace, following `publish_session_id.py` pattern)
- `build_scope_from_seed(seed: dict, agent_id: str) -> dict`
- `is_path_within_scope(file_path: str, file_anchors: list[str], scope_directories: list[str]) -> bool` (canonical paths via `os.path.realpath` — checks if path is a file anchor or within a scope directory)
- `select_scope_root(file_anchors: list[str], scope_directories: list[str], query_path: str | None, tool_name: str) -> str | None` (per-query scope_root selection per T4-CT-02 and T7 Scope Directory Derivation amendment. If `query_path` names or implies a specific file: returns the shallowest file anchor whose subtree contains it (for Grep), or the shallowest scope directory (for Glob, which requires a directory). If `query_path` is None: returns None. **B1-specific pathless-query rule:** when the function returns None, the guard denies the call with `permissionDecisionReason` listing both scope directories and instructing the agent to reissue with an explicit `path` targeting one of them. This is a hard deny, not a fallback: T4 does not define a deterministic selection rule for conceptual queries (containment.md:57-65), so the shakedown requires the agent to make the scope choice explicit rather than the guard making it silently. The `dialogue-codex` skill instructs path-targeted queries, so this deny path should be rare. Scored runs are blocked on this until T4-BR-07 is resolved.)
- `derive_scope_directories(file_anchors: list[str]) -> list[str]` (deduplicated parent directories of file anchors — used by harness to populate seed file)
- `clean_stale_files(shakedown_dir: Path, max_age_hours: int = 24) -> None` (removes seed, scope, active-run, marker, and completion-marker files older than `max_age_hours`)

**Pattern:** Follow `publish_session_id.py` for atomic writes, `codex_guard.py` for `sys.path` manipulation to import from `server/`.

**Tests:** `tests/test_containment.py` (~200 lines) — file anchor membership, scope_root selection (path-targeted → file anchor or scope directory, pathless → None/deny, Glob → scope directory only), scope directory derivation from file anchors, atomic I/O, stale cleanup.

#### Phase 1b: Lifecycle Hooks

**Create:** `scripts/containment_lifecycle.py` (~100 lines)

Single script dispatching on `hook_event_name`:
- **SubagentStart:** Read `session_id`, `agent_id` from stdin JSON. Read `run_id` from `active-run-<session_id>`. Find seed file (`seed-<run_id>.json`). If found: write scope file (`scope-<run_id>.json` = seed + agent_id), remove seed. If an existing scope file already exists for the same run_id: log error to stderr (unexpected — the harness's single-active-run check should have prevented this), exit 0 without modifying the existing scope. Clean stale seeds >24h. Exit 0.
- **SubagentStop:** Read `session_id`, `agent_id`, `agent_transcript_path` from stdin JSON. Find scope file. If `agent_id` matches: copy `agent_transcript_path` to `${CLAUDE_PLUGIN_DATA}/shakedown/transcript-<run_id>.jsonl` (where `run_id` comes from the scope file; `.jsonl` matches Claude Code's transcript format per docs: `subagents/agent-<id>.jsonl`), then write a completion marker at `${CLAUDE_PLUGIN_DATA}/shakedown/transcript-<run_id>.done` (empty file), then remove scope file. Exit 0.
- **Error handling:** Transcript copy failure → write error to `${CLAUDE_PLUGIN_DATA}/shakedown/transcript-<run_id>.error` with reason, then remove scope file, exit 0. The harness checks for `.done` or `.error` to determine outcome. Other errors → stderr diagnostics, exit 0 (lifecycle hooks cannot block).

**Tests:** `tests/test_containment_lifecycle.py` (~150 lines) — subprocess tests following `codex_guard.py` test pattern.

#### Phase 1c: PreToolUse Containment Guard

**Create:** `scripts/containment_guard.py` (~150 lines)

PreToolUse hook for `Read|Grep|Glob`:

**Fast exit (exit 0, no output):**
- No `agent_id` in hook input → main-thread call, pass through
- No `active-run-<session_id>` pointer → no shakedown active, containment inactive
- Active-run pointer exists → read `run_id`, check for `scope-<run_id>.json`. If scope file's `agent_id` ≠ hook input's `agent_id` → wrong agent, pass through.

**Seed-present bootstrap poll (poll, then deny on timeout):**
- `agent_id` present + active-run pointer exists + no scope file + seed file exists for `run_id` → a shakedown is bootstrapping but SubagentStart hasn't promoted the seed yet. The guard polls for the scope file (up to 2 seconds, checking every 100ms). If the scope file appears during the poll, proceed to containment enforcement (read scope, verify `agent_id` match, enforce as normal). If the poll times out, deny with reason: "Containment scope not established within 2s — SubagentStart may have failed or ordering gap exceeds poll window." This provides deterministic safety (poll timeout = fail-closed deny) and a bounded startup bridge (timing gaps up to 2 seconds are bridged without depending on Claude's retry behavior after a denial). If the poll times out, the failure is deterministic and diagnosable — not a silent pass-through. The 2-second window is a provisional operational threshold, not a documented platform guarantee; Phase 0 measures whether it is sufficient. The seed file proves a shakedown was requested, so a poll timeout means the guard MUST deny rather than pass through. The guard's behavior is unconditional.

**Same-session retry safety:** The harness rejects a second launch if the active-run pointer exists with either a live seed or scope file (step 5 of the harness procedure). There is no overwrite path — the operator must wait for the prior run to complete or manually clean up stale state before retrying. This eliminates the pointer-flip race entirely: the active-run pointer is never overwritten while a prior run's state files exist.

**Containment active (all 3 conditions hold):**
- **Read:** Canonicalize `tool_input.file_path`, check `is_path_within_scope(file_path, file_anchors, scope_directories)`. Out-of-scope → deny. Read allows access to any file within a scope directory, not just named file anchors. This ensures discovery-then-inspect consistency: if Glob surfaces a sibling file in a scope directory, the agent can Read it. For scored runs, Read restriction to file anchors only is a post-execution filtering concern (T4-CT-01, deferred).
- **Grep:** Call `select_scope_root(file_anchors, scope_directories, tool_input.get("path"), "Grep")`. If path is present: rewrite `path` to the selected scope_root, echo all original `tool_input` fields + rewritten `path` → `updatedInput` with `permissionDecision: "allow"`. The agent receives post-confinement results transparently (T4 containment.md:37-39). Grep's `path` accepts both files and directories, so both file anchors and scope directories are valid. If `path` is absent: deny with `permissionDecisionReason` listing scope directories and instructing the agent to reissue with explicit `path` (B1-specific pathless-query rule — see `select_scope_root`).
- **Glob:** Call `select_scope_root(file_anchors, scope_directories, tool_input.get("path"), "Glob")`. If path is present: rewrite to the matching scope directory (Glob requires a directory, so the function always returns a scope directory member). Echo all original `tool_input` fields + rewritten `path` → `updatedInput` with `permissionDecision: "allow"`. Glob results may include non-anchor files — acceptable for shakedown (inspector checks via checklist items 10-12); scored runs require post-execution filtering (T4-CT-01, deferred). If `path` is absent: deny with `permissionDecisionReason` listing scope directories (same pathless-query rule as Grep).

**Critical:** `updatedInput` replaces the entire input object. Must include ALL original fields (pattern, output_mode, etc.) alongside the modified `path`.

**Note on ordering:** Phase 0 validates whether SubagentStart completes before the first PreToolUse. If ordering holds (expected), the guard's bootstrap poll is never exercised. If ordering does NOT hold, the poll bridges the timing gap: the guard waits up to 2 seconds for the scope file, then proceeds with containment if found or denies on timeout. Either way, containment is fail-closed. If the poll succeeds, the run proceeds normally. If the poll times out, the failure is deterministic and diagnosable — Phase 0 measures whether the provisional 2-second window is sufficient and whether calibration is needed.

**Output format:** `hookSpecificOutput` wrapper per Claude Code docs (NOT the legacy exit-code-2 pattern).

**Tests:** `tests/test_containment_guard.py` (~250 lines) — Read deny (out-of-scope file), Read allow (file anchor), Read allow (non-anchor file within scope directory), Grep rewrite to file anchor (path-targeted), Grep deny (no path — pathless-query rule), Glob rewrite to scope directory (path present), Glob deny (no path), main-thread passthrough, agent_id mismatch, seed-present poll timeout → deny, seed-present poll success → containment.

#### Phase 1d: Hook Registration

**Modify:** `hooks/hooks.json`

Add to existing config (keeping SessionStart + PreToolUse codex_guard entries):

```json
"SubagentStart": [
  {
    "matcher": "shakedown-dialogue",
    "hooks": [{
      "type": "command",
      "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/containment_lifecycle.py\""
    }]
  }
],
"SubagentStop": [
  {
    "matcher": "shakedown-dialogue",
    "hooks": [{
      "type": "command",
      "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/containment_lifecycle.py\""
    }]
  }
],
"PreToolUse": [
  ...<existing codex_guard entry>,
  {
    "matcher": "Read|Grep|Glob",
    "hooks": [{
      "type": "command",
      "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/containment_guard.py\""
    }]
  }
]
```

No matcher conflict: `codex_guard.py` matches MCP tool names, `containment_guard.py` matches native tool names (`Read|Grep|Glob`).

**Verification gate:** All containment tests pass. `/hooks` shows the new entries.

---

### Phase 2: Agent + Behavioral Skill

**Goal:** Custom agent with T4 behavioral instructions.
**Dependencies:** Phase 1 (hooks registered for agent_type matching).

#### Phase 2a: Agent Definition

**Create:** `agents/shakedown-dialogue.md` (~15 lines frontmatter + minimal body)

```yaml
---
name: shakedown-dialogue
description: Contained pre-benchmark shakedown agent for B1 dialogue. Invoked by the shakedown-b1 skill. Do not use directly.
model: opus
maxTurns: 30
tools:
  - Read
  - Grep
  - Glob
  - mcp__plugin_codex-collaboration_codex-collaboration__codex.dialogue.start
  - mcp__plugin_codex-collaboration_codex-collaboration__codex.dialogue.reply
  - mcp__plugin_codex-collaboration_codex-collaboration__codex.dialogue.read
skills:
  - dialogue-codex
---

Execute the dialogue-codex skill procedure. Your Read, Grep, and Glob calls are constrained to the B1 scope by the containment guard — you can access any file within the scope directories. You do not need to manage containment — the harness handles it transparently.
```

Key constraints:
- NO Bash, Write, Edit, Agent (containment-safe surface)
- `skills: [dialogue-codex]` preloads the behavioral skill at agent start
- `name: shakedown-dialogue` MUST match hooks.json SubagentStart/SubagentStop matchers exactly
- Plugin agents cannot have `hooks` in frontmatter (ignored per docs)

#### Phase 2b: Behavioral Skill

**Create:** `skills/dialogue-codex/SKILL.md` (~300 lines)

NOT user-invocable (preloaded into agent). The 6 behaviors:

1. **Claim extraction:** After each Codex reply, identify factual claims. Classify as scoutable (mechanically verifiable against source code via path/symbol) or `not_scoutable`.

2. **Claim registration:** Maintain structured claim ledger in working context. New claims: register with ID, status `unverified`, `scout_attempts: 0`. Revised: update text, preserve ID. `not_scoutable`: set status immediately.

3. **Scout target selection:** Per T4-SB-03 priority: unverified(attempts=0) → conflicted → ambiguous. At most 1 target per round. Skip conditions: action=="conclude", evidence budget, effort budget, no scoutable targets.

4. **Query coverage:** ≥1 definition query + ≥1 falsification query per scouting round. 2-5 tool calls total (T4-SB-04). Second-attempt diversity: at least one mandatory query type must differ from first-round queries.

5. **Per-turn state emission:** After each round, emit evidence block + verification-state summary using the Machine-Readable Emission Contract in the execution plan v3 (§ "Machine-Readable Emission Contract" is authoritative for field names, types, and sentinel format):

   Evidence block: `{target_claim, target_claim_id, scope_root, queries: [{type, tool, target}], disposition, citations: [{path, lines, snippet}]}`

   Verification-state summary: `{turn, claims: [{id, text, status, scout_attempts}], counters: {total_claims, supported, contradicted, conflicted, ambiguous, not_scoutable, unverified, evidence_count}, effective_delta: {total_claims, supported, contradicted, conflicted, ambiguous, not_scoutable, unverified, evidence_count}}`

6. **Follow-up composition:** Produce follow-up using current ledger/evidence state. Terminal turn: epilogue with `effective_delta` (overall), `ledger_summary`, `converged` derivation.

7. **Dialogue-tool failure termination:** If `codex.dialogue.start` or `codex.dialogue.reply` returns an error, terminate the run on the next turn with `terminal: true`, `converged: false`, and an epilogue `ledger_summary` that describes the failure (tool name, error message, turn number at failure). Do not continue scouting after dialogue-tool failure — without Codex replies, scouting has no claims to verify.

Must also include:
- Loop shape (extract → register → compute → control → scout → update → compose → send per T4-SB-01)
- Verification state derivation rule (T4-SM-06:346-368)
- Prohibition on benchmark artifact names (`manifest.json`, `runs.json`, etc.)

**Reference documents to inline into skill:** Key contracts from `scouting-behavior.md` (T4-SB-01 through T4-SB-05) and `state-model.md` (T4-SM-06 derivation rule). The skill must be self-contained — the agent cannot read reference docs during execution.

**Verification gate:** Run `/reload-plugins` after creating agent + skill. Agent spawnable. Skill preloads. `/agents` shows `codex-collaboration:shakedown-dialogue`.

---

### Phase 3: Orchestration Harness

**Goal:** User-invocable skill that drives the shakedown.
**Dependencies:** Phases 1 + 2.

**Create:** `skills/shakedown-b1/SKILL.md` (~120 lines)

```yaml
---
name: shakedown-b1
description: Run the B1 pre-benchmark integration shakedown. Writes containment seed, spawns the shakedown agent, captures artifacts.
user-invocable: true
allowed-tools: Bash, Read, Write, Agent, mcp__plugin_codex-collaboration_codex-collaboration__codex.status
---
```

**Procedure:**

1. **Repo root:** `git rev-parse --show-toplevel`
2. **Preflight:** Call `codex.status` → verify runtime health
3. **Read session_id:** from `${CLAUDE_PLUGIN_DATA}/session_id` (written by `publish_session_id.py`)
4. **Stale cleanup:** Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/clean_stale_shakedown.py"` via Bash to remove stale scope, seed, active-run, and completion-marker files older than 24h from prior runs (T7:212 — required on both fresh and resumed sessions). This script imports `clean_stale_files()` from `server/containment.py` and passes `${CLAUDE_PLUGIN_DATA}/shakedown/`. Runs before seed creation to ensure no stale containment state from a crashed prior run.
5. **Single-active-run check:** Read `active-run-<session_id>`. If it exists, read the `run_id` it contains and check for BOTH `scope-<run_id>.json` and `seed-<run_id>.json`. If either file exists, a prior shakedown is still active (seed-only means SubagentStart has not yet promoted; scope means SubagentStop has not yet cleaned up). **Abort with error:** "A shakedown run is already active in this session (run_id: <run_id>, state: seed|scope). Wait for it to complete or manually remove the state files." This closes the bootstrap window: a second launch cannot flip the active-run pointer while a prior run's seed or scope is in flight.
6. **Generate run_id:** UUID4
7. **Write seed file + active-run pointer:** Create `${CLAUDE_PLUGIN_DATA}/shakedown/` dir if needed. Write `active-run-<session_id>` containing the `run_id` (plain text — allows the containment guard to look up the current run from session_id). Write `seed-<run_id>.json`:
   ```json
   {
     "session_id": "<session_id>",
     "run_id": "<run_id>",
     "file_anchors": [
       "<repo_root>/docs/superpowers/specs/codex-collaboration/contracts.md",
       "<repo_root>/docs/superpowers/specs/codex-collaboration/delivery.md",
       "<repo_root>/packages/plugins/codex-collaboration/server/mcp_server.py"
     ],
     "scope_directories": [
       "<repo_root>/docs/superpowers/specs/codex-collaboration/",
       "<repo_root>/packages/plugins/codex-collaboration/server/"
     ],
     "created_at": "<ISO timestamp>"
   }
   ```
   `scope_directories` are deduplicated parent directories of the `file_anchors` (per T7 Scope Directory Derivation amendment). All three tools use the same scope boundary: a file is in scope if it is a file anchor or within a scope directory. `Read` checks membership; `Grep`/`Glob` rewrite `path` to the matching member.
8. **Spawn agent:**

   ```python
   Agent(
     subagent_type="shakedown-dialogue",
     prompt=f"""You are running a pre-benchmark integration shakedown on task B1.

   **Task:** Conduct a structured dialogue with Codex about the codex-collaboration
   package, then scout Codex's factual claims against the source code.

   **Opening question for Codex:** "Describe the architecture of the
   codex-collaboration server: its major components, their responsibilities,
   and how they interact during a dialogue session."

   **Repository root:** {repo_root}
   **Scope directories:** {json.dumps(scope_directories)}

   Your Read, Grep, and Glob calls are constrained to the scope directories
   by the containment guard. You can access any file within those directories.

   **Begin by calling `codex.dialogue.start` with the opening question above.**
   After receiving the reply, follow the dialogue-codex skill procedure."""
   )
   ```

   Required template fields: task framing, opening Codex question, `repo_root`, `scope_directories`, instruction to begin with `codex.dialogue.start`. The opening question targets B1's file anchors (contracts, delivery, mcp_server) to maximize scoutable-claim yield.
9. **Verify transcript capture:** Check for `${CLAUDE_PLUGIN_DATA}/shakedown/transcript-<run_id>.done` (completion marker written by SubagentStop lifecycle hook). If `.done` exists: transcript at `transcript-<run_id>.jsonl` is the primary inspection artifact. If `.error` exists: report the error and fail the run. If neither exists: fail the run with "Transcript capture did not complete — SubagentStop hook may have failed silently." The harness checks for completion markers immediately after the Agent tool returns. The expectation is that SubagentStop fires before result delivery (inferred from the lifecycle diagram — see T7 Hook State Transport — not an explicit doc guarantee). If neither `.done` nor `.error` exists on first check, retry once after 1 second as a heuristic to accommodate undocumented lag between SubagentStop execution and file visibility. If still absent after retry, fail the run with: "Transcript capture did not complete — undocumented timing gap may have exceeded the provisional 1-second retry window, or SubagentStop hook failed silently." The 1-second retry is a provisional operational threshold, not closure of the timing question. Phase 0 measures SubagentStart-to-PreToolUse gap, not SubagentStop marker visibility; the 1-second transcript retry can only be calibrated empirically during actual shakedown runs (Phase 4).
10. **Capture remaining artifacts:**
   - Transcript: already written by SubagentStop (Phase 1b) to `${CLAUDE_PLUGIN_DATA}/shakedown/transcript-<run_id>.jsonl`. Format is JSONL (matching Claude Code's transcript format per docs: `subagents/agent-<id>.jsonl`). The parent-facing agent result (summary returned to the operator) is NOT the transcript — it lacks per-turn evidence blocks, verification summaries, and follow-up text required by checklist items 1-12.
   - Metadata: write JSON to `${CLAUDE_PLUGIN_DATA}/shakedown/metadata-<run_id>.json`
     ```json
     {"run_id", "session_id", "task_id": "B1", "classification": "pre_benchmark_integration_shakedown", "commit_sha", "timestamp", "file_anchors", "scope_directories", "result": null}
     ```
   - Inspection template: write to `${CLAUDE_PLUGIN_DATA}/shakedown/inspection-<run_id>.md` with 12-item checklist (per-turn 1-6, terminal 7-9, containment 10-12)

**Verification gate:** Full lifecycle works: seed created → SubagentStart fires → scope created → agent runs contained → SubagentStop fires → scope removed → artifacts written.

---

### Phase 4: Dry Run

**Goal:** Execute the shakedown on B1, apply inspection checklist.
**Dependencies:** All above.

No new files. This is execution:

1. Invoke `/shakedown-b1`
2. Monitor seed → scope lifecycle via filesystem
3. Verify containment: agent's Read/Grep/Glob constrained to scope (file anchors + scope directories)
4. Verify per-turn emission matches schema
5. Fill in inspection template (12 items)
6. Determine result: pass / fail (routed to specific component) / inconclusive (>50% not_scoutable)

## File Inventory

All paths relative to `packages/plugins/codex-collaboration/`.

### New Files (10 production + 4 test)

| File | Phase | Lines (est.) | Purpose |
|------|-------|-------------|---------|
| `server/containment.py` | 1a | 80 | Shared pure functions for scope/seed file ops |
| `scripts/containment_lifecycle.py` | 1b | 100 | SubagentStart + SubagentStop hook handler |
| `scripts/containment_guard.py` | 1c | 150 | PreToolUse containment enforcement |
| `agents/shakedown-dialogue.md` | 2a | 20 | Agent definition (tools allowlist, skills ref) |
| `skills/dialogue-codex/SKILL.md` | 2b | 300 | T4 behavioral instructions (6 behaviors) |
| `skills/shakedown-b1/SKILL.md` | 3 | 120 | Orchestration harness |
| `scripts/clean_stale_shakedown.py` | 3 | 15 | CLI wrapper for `clean_stale_files()` — invoked by harness via Bash |
| `scripts/ordering_test_start.py` | 0 | 35 | Ordering validation: SubagentStart marker with monotonic timestamp |
| `scripts/ordering_test_check.py` | 0 | 50 | Ordering validation: PreToolUse checker with delta_ms measurement |
| `agents/ordering-test.md` | 0 | 10 | Ordering validation: minimal test agent (optional — prefer `--agents` CLI flag) |
| `tests/test_containment.py` | 1a | 200 | Unit tests for containment module |
| `tests/test_containment_lifecycle.py` | 1b | 150 | Subprocess tests for lifecycle hooks |
| `tests/test_containment_guard.py` | 1c | 250 | Subprocess tests for PreToolUse guard |
| `agents/` directory | 2a | — | New directory (create) |

### Modified Files (1)

| File | Phase | Change |
|------|-------|--------|
| `hooks/hooks.json` | 0, 1d | Add SubagentStart, SubagentStop, PreToolUse (Read\|Grep\|Glob) entries |

### Reference Files (read during implementation, not modified)

| File | What it provides |
|------|-----------------|
| `docs/plans/2026-04-07-t7-executable-slice-definition.md` | Authority — all requirements |
| `docs/plans/t04-t4-scouting-position-and-evidence-provenance/scouting-behavior.md` | Per-turn loop (T4-SB-01), target selection (T4-SB-03), query coverage (T4-SB-04) |
| `docs/plans/t04-t4-scouting-position-and-evidence-provenance/state-model.md` | Verification state derivation (T4-SM-06:346-368), data structures |
| `docs/plans/t04-t4-scouting-position-and-evidence-provenance/containment.md` | Scope confinement spec (T4-CT-02) |
| `scripts/codex_guard.py` | Hook script pattern (stdin JSON, sys.path, exit codes) |
| `scripts/publish_session_id.py` | Atomic write pattern, session_id publication mechanism |
| `skills/consult-codex/SKILL.md` | Skill frontmatter pattern |

## Risks

| Risk | Mitigation | Phase |
|------|-----------|-------|
| SubagentStart ordering not guaranteed by docs | Guard includes bootstrap poll (provisional 2s window, every 100ms) when seed-present + no-scope. Bounded startup bridge: timing gaps within the window are bridged; poll timeout = fail-closed deny with diagnosable error. Phase 0 measures whether the window is sufficient; calibrate if needed | 0 |
| Plugin agents ignore `hooks` frontmatter | All hooks in `hooks.json` (verified from docs) | 1 |
| `updatedInput` replaces entire input | Guard echoes ALL original fields alongside modified `path` | 1c |
| File anchors are files, Glob needs directories | T7 Scope Directory Derivation amendment: `allowed_roots` includes both file anchors and scope directories. All three tools use the same scope boundary. `scope_root ∈ allowed_roots` preserved | 1a, 1c |
| Conceptual queries — scope directory selection unresolved in T4 | B1 pathless-query rule: guard denies with scope directory list, agent must reissue with explicit `path`. Skill instructs path-targeted queries. Scored runs blocked until T4-BR-07 | 1c |
| Glob results may include non-anchor files | Acceptable for shakedown (manual inspection). Read allows any file within scope directories for discovery-then-inspect consistency. Scored runs restrict Read to file anchors via post-execution filtering (T4-CT-01, deferred) | 1c |
| Same-session shakedown retry while prior run active | Harness rejects second launch if active-run pointer has live seed or scope. No overwrite path — operator waits or cleans up manually | 3 |
| Transcript capture failure silent | SubagentStop writes `.done` or `.error` marker; harness verifies before proceeding | 1b, 3 |
| Plugin components not discovered mid-session | Phase 0 uses `--agents` CLI flag or `/reload-plugins`. Phase 2 requires `/reload-plugins` after creating agent + skill. All verification gates include reload step | 0, 2 |
| Claude doesn't follow behavioral instructions perfectly | Shakedown is manual-inspection grade; failures route to specific checklist items | 4 |
| Stale scope/seed from crashed run | `clean_stale_files()` at harness startup (>24h); single-active-run check prevents relaunch while stale state exists; agent_id mismatch prevents accidental activation in new sessions | 1b, 3 |
| codex-collaboration may lack plugin.json / not be deployed | Test with `--plugin-dir` during development | all |

## Verification

### Per-Phase Gates

| Phase | Gate |
|-------|------|
| 0 | Ordering result file exists with `marker_found` and `delta_ms` fields. Evaluate `delta_ms` against provisional 2-second bootstrap poll window |
| 1 | `uv run --package codex-collaboration pytest tests/test_containment*.py` passes |
| 2 | `/reload-plugins` run; agent spawnable; `/agents` lists `codex-collaboration:shakedown-dialogue` |
| 3 | Full lifecycle: seed → scope → containment → cleanup → artifacts |
| 4 | 12-item inspection checklist completed; result determined |

### End-to-End

1. Invoke `/shakedown-b1`
2. Verify seed file created then removed (SubagentStart promoted it)
3. Verify active-run pointer written and points to correct run_id
4. Verify scope file exists during agent execution, removed after
5. Verify agent Read calls to files outside scope directories are denied; Read calls within scope directories are allowed
6. Verify agent Grep paths are rewritten to file anchors or scope directories
7. Verify agent Glob paths are rewritten to scope directories
8. Verify `.done` marker exists after agent returns; transcript at `.jsonl` path
9. Verify per-turn emission matches T7 schema
10. Verify metadata JSON has all required fields
11. Apply 12-item inspection checklist
12. Result: pass / fail (routed) / inconclusive

### Acceptance Criteria (from T7)

1. `dialogue-codex` skill implements all 6 behaviors, invocable through dialogue infrastructure
2. Containment hooks registered and functional (SubagentStart/Stop + PreToolUse for Read/Grep/Glob)
3. B1 seed file has non-empty `file_anchors` and `scope_directories`; SubagentStart promotes to scope with `agent_id`
4. Transcript capture writes to stable path
5. Metadata records commit SHA, timestamp, task ID `B1`, classification `pre_benchmark_integration_shakedown`

## References

| Document | Role | Path |
|----------|------|------|
| T7 executable slice definition | Authority (what to build) | `docs/plans/2026-04-07-t7-executable-slice-definition.md` |
| T8 execution plan v3 | Delivery sequence (build order, gates, emission contract) | `docs/plans/2026-04-08-t8-shakedown-execution-plan-v3.md` |
| T4 containment spec | Scope membership rules | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/containment.md` |
| T4 scouting behavior | Per-turn behavioral loop | `docs/plans/t04-t4-scouting-position-and-evidence-provenance/scouting-behavior.md` |
