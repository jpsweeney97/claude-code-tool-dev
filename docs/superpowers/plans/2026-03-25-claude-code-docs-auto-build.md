# claude-code-docs Auto-Build Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ensure the claude-code-docs MCP server's compiled `dist/` always reflects the TypeScript source, eliminating silent source/output divergence across Claude Code session restarts.

**Architecture:** Replace the direct `node dist/index.js` MCP registration with a package-local wrapper script that runs `tsc` (with incremental compilation enabled in tsconfig) before `exec`-ing into node. This couples build and start atomically — every server start gets fresh compiled output. Redirect build output to stderr to protect the MCP stdio JSON-RPC transport.

**Tech Stack:** TypeScript, bash, Claude Code MCP CLI (`claude mcp`)

**Context:** This design was validated via Codex dialogue (thread `019d27e0-8274-7b21-94fb-c44492409e2c`, 6 turns, converged). The wrapper approach won over SessionStart hooks (undocumented ordering, wrong failure semantics), npm lifecycle hooks (Claude Code invokes `node` directly, not `npm start`), and tsx (skips typecheck gate). One simplification from the dialogue: using plain `tsc` with `"incremental": true` in tsconfig instead of `tsc -b --incremental`, since the project has no composite/reference setup and `tsc` with incremental config is sufficient.

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `packages/mcp-servers/claude-code-docs/tsconfig.json` | Modify | Add incremental compilation + tsBuildInfoFile |
| `packages/mcp-servers/claude-code-docs/scripts/run-mcp.sh` | Create | Wrapper: compile then exec into node |
| `packages/mcp-servers/claude-code-docs/CLAUDE.md` | Modify | Document the auto-build mechanism |

No changes to `package.json` — the `"build": "tsc"` script stays as-is since tsconfig now drives incremental behavior.

MCP server re-registration is a CLI command, not a file change.

---

### Task 1: Enable incremental TypeScript compilation

**Files:**
- Modify: `packages/mcp-servers/claude-code-docs/tsconfig.json`

- [ ] **Step 1: Add incremental and tsBuildInfoFile to tsconfig.json**

```json
{
  "extends": "../../../tsconfig.base.json",
  "compilerOptions": {
    "rootDir": "src",
    "outDir": "dist",
    "incremental": true,
    "tsBuildInfoFile": "dist/.tsbuildinfo"
  },
  "include": ["src"]
}
```

`tsBuildInfoFile` goes inside `dist/` so that `rm -rf dist/` also clears the incremental cache — no stale build-info outliving the output files it describes. No `.gitignore` change needed since `dist/` is already ignored.

- [ ] **Step 2: Verify incremental compilation works**

Run from `packages/mcp-servers/claude-code-docs/`:

```bash
# Clean slate
rm -rf dist/

# First build (cold — should take 3-8s, creates .tsbuildinfo)
time npx tsc

# Verify .tsbuildinfo was created
ls -la dist/.tsbuildinfo

# Second build (incremental — should be noticeably faster)
time npx tsc
```

Expected:
- `dist/.tsbuildinfo` exists after first build
- Second build completes faster than first (incremental reuse)
- `dist/index.js` and other compiled files present

- [ ] **Step 3: Run existing tests to confirm nothing broke**

```bash
npm test
```

Expected: All 561 tests pass (count may vary if tests were added since the handoff snapshot).

- [ ] **Step 4: Typecheck**

```bash
npx tsc --noEmit
```

Expected: Clean (no errors).

- [ ] **Step 5: Commit**

```bash
git add packages/mcp-servers/claude-code-docs/tsconfig.json
git commit -m "feat(claude-code-docs): enable incremental TypeScript compilation

Add incremental: true and tsBuildInfoFile to tsconfig.json.
Places .tsbuildinfo inside dist/ so rm -rf dist/ also clears
the incremental cache. Prepares for auto-build wrapper."
```

---

### Task 2: Create the wrapper script

**Files:**
- Create: `packages/mcp-servers/claude-code-docs/scripts/run-mcp.sh`

- [ ] **Step 1: Create the scripts directory**

```bash
mkdir -p packages/mcp-servers/claude-code-docs/scripts
```

- [ ] **Step 2: Write the wrapper script**

Create `packages/mcp-servers/claude-code-docs/scripts/run-mcp.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
tsc 1>&2
exec node dist/index.js
```

Design notes:
- `set -euo pipefail`: fail-hard on any error. If `tsc` fails, the server doesn't start (correct — stale code is worse than no server).
- `cd "$(dirname "$0")/.."`: resolves to the package root relative to the script location. Works regardless of where Claude Code starts the process.
- `tsc 1>&2`: redirects all build output (progress, warnings) to stderr. **Critical** — MCP stdio transport uses stdout for JSON-RPC. Any stdout pollution from tsc corrupts the protocol stream.
- `exec node dist/index.js`: replaces bash with node. Claude Code's signal handling reaches the node process directly (no zombie bash parent).

- [ ] **Step 3: Make it executable**

```bash
chmod +x packages/mcp-servers/claude-code-docs/scripts/run-mcp.sh
```

- [ ] **Step 4: Verify the wrapper starts the server**

Run from any directory:

```bash
/Users/jp/Projects/active/claude-code-tool-dev/packages/mcp-servers/claude-code-docs/scripts/run-mcp.sh &
SERVER_PID=$!
sleep 3

# Verify server process is running
ps -p $SERVER_PID -o command=
# Expected: node dist/index.js (the exec replaced bash with node)

# Clean up
kill $SERVER_PID 2>/dev/null
```

Expected: The process shows `node dist/index.js` (not `bash scripts/run-mcp.sh`), confirming `exec` correctly replaced the shell.

- [ ] **Step 5: Verify build output goes to stderr, not stdout**

```bash
# Capture stdout and stderr separately
/Users/jp/Projects/active/claude-code-tool-dev/packages/mcp-servers/claude-code-docs/scripts/run-mcp.sh \
  1>/tmp/mcp-stdout.log 2>/tmp/mcp-stderr.log &
SERVER_PID=$!
sleep 3
kill $SERVER_PID 2>/dev/null

# stdout should be empty (or contain only MCP JSON-RPC init)
echo "=== stdout ==="
cat /tmp/mcp-stdout.log | head -5

# stderr should contain any tsc output (or be empty on clean incremental)
echo "=== stderr ==="
cat /tmp/mcp-stderr.log | head -5
```

Expected: No tsc output in stdout. Any tsc progress/warnings appear only in stderr.

- [ ] **Step 6: Commit**

```bash
git add packages/mcp-servers/claude-code-docs/scripts/run-mcp.sh
git commit -m "feat(claude-code-docs): add auto-build wrapper script

Wrapper runs tsc before exec-ing into node dist/index.js.
Build output redirected to stderr to protect MCP stdio transport.
Uses relative path resolution so it works from any working directory."
```

---

### Task 3: Re-register the MCP server

This task uses Claude Code CLI commands. Run these from the terminal (not in a test).

- [ ] **Step 1: Verify current registration**

```bash
claude mcp get claude-code-docs
```

Expected: Shows current registration with `Command: node`, `Args: .../dist/index.js`, `Environment: DOCS_PATH=...`.

Note the exact `DOCS_PATH` value for re-registration.

- [ ] **Step 2: Remove the old registration**

```bash
claude mcp remove claude-code-docs -s user
```

Expected: Server removed.

- [ ] **Step 3: Add the new registration with wrapper**

```bash
claude mcp add --transport stdio --scope user \
  --env DOCS_PATH=/Users/jp/Projects/active/claude-code-tool-dev/docs/extension-reference \
  claude-code-docs \
  -- /Users/jp/Projects/active/claude-code-tool-dev/packages/mcp-servers/claude-code-docs/scripts/run-mcp.sh
```

- [ ] **Step 4: Verify the new registration**

```bash
claude mcp get claude-code-docs
```

Expected output includes:
```
Command: /Users/jp/.../scripts/run-mcp.sh
```
(Not `node` — the wrapper is now the command.)

Environment should still show `DOCS_PATH=...`.

---

### Task 4: Document the auto-build mechanism

**Files:**
- Modify: `packages/mcp-servers/claude-code-docs/CLAUDE.md`

- [ ] **Step 1: Add auto-build documentation to CLAUDE.md**

Add a new section after the "Gotchas" section in `packages/mcp-servers/claude-code-docs/CLAUDE.md`:

```markdown
## Auto-Build

The MCP server is registered to start via `scripts/run-mcp.sh`, a wrapper that runs `tsc` before `exec node dist/index.js`. This ensures `dist/` always reflects the TypeScript source on every session restart.

**How it works:**
- Wrapper redirects tsc output to stderr (stdout is reserved for MCP JSON-RPC)
- `exec` replaces bash with node so signals reach the server process directly
- Incremental compilation (`incremental: true` in tsconfig) makes no-op builds fast
- `.tsbuildinfo` lives in `dist/` — `rm -rf dist/` also clears the incremental cache

**If tsc fails:** The server does not start. This is intentional — running stale compiled code is worse than no server. Fix the TypeScript error and restart the session.

**Registration:** `claude mcp get claude-code-docs` shows the current config. To re-register after moving the repo, run:
```bash
claude mcp remove claude-code-docs -s user
claude mcp add --transport stdio --scope user \
  --env DOCS_PATH=<repo>/docs/extension-reference \
  claude-code-docs \
  -- <repo>/packages/mcp-servers/claude-code-docs/scripts/run-mcp.sh
```
```

- [ ] **Step 2: Commit**

```bash
git add packages/mcp-servers/claude-code-docs/CLAUDE.md
git commit -m "docs(claude-code-docs): document auto-build mechanism"
```

---

### Task 5: End-to-end verification (next session)

This task requires a Claude Code session restart. Document the checks here; execute them after restarting.

- [ ] **Step 1: Restart Claude Code session**

Exit the current session and start a new one in the same project directory.

- [ ] **Step 2: Check server status**

```
/mcp
```

Expected: `claude-code-docs` shows "Connected".

- [ ] **Step 3: Verify taxonomy_drift is gone**

Use the `get_status` MCP tool.

Expected:
- `taxonomy_drift` is **absent** from `warning_codes`
- `source_kind` is `fetched` or `cached`
- No `last_load_error`

This confirms: (1) the wrapper ran `tsc` before starting, (2) the new code with INGESTION_VERSION=4 loaded, (3) the stale index cache was invalidated and rebuilt with the `fallbackOverviewCount` fix.

- [ ] **Step 4: Verify incremental builds are working**

After the session is running, check that `.tsbuildinfo` exists:

```bash
ls -la packages/mcp-servers/claude-code-docs/dist/.tsbuildinfo
```

Expected: File exists with recent timestamp matching session start.

- [ ] **Step 5: Clean up stale server processes from previous sessions**

```bash
# Check for orphaned server processes
ps aux | grep "claude-code-docs/dist/index.js" | grep -v grep

# Kill any from previous sessions (keep only the current one)
# The current session's server will have the most recent start time
```
