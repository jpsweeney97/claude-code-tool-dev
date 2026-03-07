---
name: delegate
description: >-
  Delegate coding tasks to Codex CLI for autonomous execution in a sandboxed
  environment. Use when the user wants Codex to DO something — write code, fix
  bugs, refactor files, implement features, write tests, generate migrations,
  scaffold components, add endpoints, resolve TODOs, or run commands — rather
  than give opinions. Trigger on "delegate this to codex", "have codex do",
  "let codex handle", "codex exec", "run this with codex", "send this to
  codex", or any request for Codex to autonomously execute coding work. Do NOT
  use for consultation or second opinions — use /codex or /dialogue instead.
argument-hint: "[-m <model>] [-s {read-only|workspace-write}] [-t {minimal|low|medium|high|xhigh}] [--full-auto] PROMPT"
user-invocable: true
---

# Delegate — Autonomous Codex Execution

Delegate a coding task to Codex CLI (`codex exec`) for autonomous execution. Codex reads files, runs commands, and writes code within a sandbox. Claude reviews all changes afterward.

**This is delegation, not consultation.** Codex acts as a worker, not an advisor. For second opinions, use `/codex`. For multi-turn discussions, use `/dialogue`.

## Preconditions

- Codex CLI installed (`npm install -g @openai/codex`) and authenticated (`codex login` or `OPENAI_API_KEY` set)
- Codex CLI version >= 0.111.0
- Clean git working tree (no staged, unstaged, or untracked changes)

The adapter verifies all preconditions and returns specific error messages if any are unmet.

## Arguments

Parse flags from `$ARGUMENTS` — the raw text following `/delegate` in the user's command. Remaining text after extracting flags = PROMPT.

| Flag | Input Field | Default | Values |
|------|-------------|---------|--------|
| `-m <model>` | `model` | Codex default | any valid model name |
| `-s <sandbox>` | `sandbox` | `workspace-write` | `read-only`, `workspace-write` |
| `-t <effort>` | `reasoning_effort` | `high` | `minimal`, `low`, `medium`, `high`, `xhigh` |
| `--full-auto` | `full_auto` | `false` | boolean flag |

Flag values are case-sensitive lowercase (e.g., `workspace-write`, not `Workspace-Write`).

**Validation (deterministic, before calling adapter):**

1. Reject unknown flags.
2. Reject missing values after flags that require values.
3. Reject invalid enum values.
4. `-s danger-full-access` → error: `"not supported in this version"`
5. `--full-auto` with `-s read-only` → error: `"--full-auto and read-only are mutually exclusive"`
6. Empty prompt after flag extraction → ask user: "What task should Codex handle?"

Error format: `argument parsing failed: {reason}`

**Security note:** Error messages must NOT echo user input — the credential scan runs in the adapter (Step 4), not in the skill. Echoing prompt content in a pre-adapter error could leak credentials.

Examples:
- `/delegate fix the flaky test in tests/auth_test.py` → all defaults, PROMPT = "fix the flaky test..."
- `/delegate -t xhigh refactor the auth middleware` → reasoning xhigh, rest defaults
- `/delegate -s read-only analyze the codebase for dead code` → read-only sandbox
- `/delegate --full-auto implement the retry logic from the design doc` → full-auto mode

## Procedure

### Step 1: Parse and validate

Parse `$ARGUMENTS` per the Arguments section. Extract flags and prompt. Run all validation checks. Stop on any error.

### Step 2: Write input JSON

Write a temp file at `$TMPDIR/codex_delegate_input_{random}.json`:

```json
{
  "prompt": "the user's task description",
  "sandbox": "workspace-write",
  "reasoning_effort": "high",
  "full_auto": false
}
```

Include only fields the user explicitly set, plus `prompt` (always required). Omit `model` unless `-m` was passed — letting the adapter use Codex's default is correct.

### Step 3: Run adapter

The adapter script is at `scripts/codex_delegate.py` within this plugin. Construct the path by navigating up two levels from this skill's base directory (up from `skills/delegate/` to the plugin root), then appending `scripts/codex_delegate.py`:

```
{skill_base_dir}/../../scripts/codex_delegate.py
```

```bash
python3 "{plugin_root}/scripts/codex_delegate.py" "$TMPDIR/codex_delegate_input_{random}.json"
```

The adapter handles: credential scanning, CLI version check, clean-tree gate, readable-secret-file gate, `codex exec` subprocess invocation, JSONL parsing, analytics emission, and temp file cleanup.

**Exit codes:**
- `0`: Check the `status` field in JSON output — may be `ok`, `blocked`, or `ok` with degraded data
- `1`: Adapter error (bad input, internal failure, version mismatch)

Exit 0 for `blocked` is intentional — it prevents triggering the PostToolUseFailure Bash hook.

### Step 4: Interpret output

Parse the JSON from stdout:

```json
{
  "status": "ok|error|blocked",
  "dispatched": true,
  "thread_id": "...",
  "summary": "...",
  "commands_run": [{"command": "...", "exit_code": 0}],
  "exit_code": 0,
  "token_usage": {"input_tokens": 0, "output_tokens": 0},
  "runtime_failures": [],
  "blocked_paths": [],
  "error": null
}
```

Branch on `status` and `dispatched`:

| Status | `dispatched` | Meaning | Action |
|--------|-------------|---------|--------|
| `blocked` | `false` | Pre-dispatch gate failed | Report block reason + `blocked_paths` (if non-empty) to user, stop |
| `error` | `false` | Adapter failure before dispatch | Report `error` field to user, stop |
| `error` | `true` | Codex ran then failed (timeout, parse error) | Proceed to Step 5 — Codex may have modified files |
| `ok` | `true` | Codex completed (exit code may be non-zero) | Proceed to Step 5 |

On `blocked`, do not attempt review — there are no changes to inspect. If `blocked_paths` is non-empty, list the specific files that caused the block. On `error` with `dispatched=true`, **always review** — Codex ran and may have written partial changes before the failure. Treat as a partial run: present changes with a warning that the run did not complete successfully.

### Step 4b: Clean up input temp file

Delete the input JSON file created in Step 2: `trash "$TMPDIR/codex_delegate_input_{random}.json"`. The adapter does not clean it (F6 creation-ownership: each creator cleans its own file). Run this regardless of adapter outcome (success, blocked, or error).

### Step 5: Review changes

This step is mandatory. Never skip it, even if Codex reports success. If any review command fails, warn the user that changes exist but could not be reviewed. Never report success without completed review (R7-15).

1. Resolve repo root: `repo_root=$(git rev-parse --show-toplevel)`
2. From repo root, run (use `git -C "$repo_root"` for all commands — do not rely on CWD) (R7-12):
   - `git status --short` — all changes including new files
   - `git diff` — modifications to tracked files (unstaged)
   - `git diff --cached` — staged changes (R6-B4: Codex may stage files)
   - For new untracked files shown by `git status`: read their contents to review

3. Present to the user:
   - **Codex summary:** the `summary` field (may be null if Codex errored mid-run)
   - **Exit code:** the `exit_code` field. If non-zero with `status=ok`, warn the user prominently: "Codex exited abnormally (code {N}) — changes may be incomplete or corrupt. Review with extra caution and verify file completeness." Signal-specific guidance: 137=OOM-killed, 139=segfault (R6-B2, R7-2)
   - **Commands run:** the `commands_run` array with command + exit code for each
   - **Files changed:** output of `git status --short`
   - **Diff:** relevant portions of `git diff` and `git diff --cached` (for large diffs, summarize and show key sections)
   - **Claude's assessment:** your independent evaluation of quality, correctness, completeness, and potential issues
   - **Runtime failures:** if `runtime_failures` is non-empty, highlight them prominently
   - **Thread ID:** from adapter output (diagnostic — for manual `codex exec resume` if needed)
   - **Token usage:** if `token_usage` is present, report input/output token counts

## Safety

The adapter enforces all safety gates before Codex runs. The skill trusts the adapter's structured output.

**Non-negotiable rules:**

1. **`danger-full-access` is blocked.** Reject at argument parsing, before the adapter runs.
2. **`--full-auto` is opt-in only.** Requires the user to explicitly pass the flag. Never auto-enable. Never suggest it.
3. **Claude reviews all changes.** Step 5 is not optional. Present your assessment even for small changes.

## Troubleshooting

### Blocked: dirty working tree

Commit, stash, or discard changes before delegating. The clean-tree gate ensures reliable diff attribution — without it, Codex's changes are indistinguishable from pre-existing modifications.

### Blocked: credential in prompt

Rephrase without API keys, tokens, or passwords. The credential scan is fail-closed — if uncertain, it blocks.

### Blocked: readable secret file

Files like `.env`, `*.pem`, `*.key` in the repo are readable by Codex within the sandbox. Move or rename them before delegating. Template files (`.env.example`, `.env.sample`) are exempt.

**Limitations:** The secret-file gate checks filenames, not symlink targets. A symlink like `creds -> ~/.aws/credentials` would not be detected. The gate also only catches files matching a fixed pathspec — arbitrarily-named secret files in `.gitignore` are not detected (R7-17). All tracked files in the repo are readable by Codex during autonomous execution — delegation is appropriate for repos whose tracked contents the user is willing to expose (R7-25).

### Error: codex not found

Install: `npm install -g @openai/codex`

### Error: version too old

Upgrade: `npm update -g @openai/codex`. Minimum version: 0.111.0.

### Changes look wrong

All changes are uncommitted. Ask the user whether to keep, modify, or revert them. If the user confirms revert: `git restore <file>` for specific files, or `git restore .` for all changes (R6-B14: `git restore` replaces deprecated `git checkout --`).

## Example

**User:** `/delegate -t xhigh fix the flaky test in tests/auth_test.py`

1. **Parse:** prompt = "fix the flaky test in tests/auth_test.py", reasoning_effort = xhigh, sandbox = workspace-write (default)
2. **Write JSON:** `{"prompt": "fix the flaky test in tests/auth_test.py", "reasoning_effort": "xhigh"}`
3. **Run adapter** → Codex reads the test, identifies a race condition, fixes it
4. **Interpret:** status = ok, dispatched = true, exit_code = 0, summary = "Fixed race condition in auth token refresh test"
5. **Review:**
   ```
   M tests/auth_test.py
   ```
   Claude: "The fix adds proper async/await handling for the token refresh mock. Correctly addresses the race condition. Change is minimal and focused."
6. **Report:** Codex summary + diff + Claude's assessment + thread ID
