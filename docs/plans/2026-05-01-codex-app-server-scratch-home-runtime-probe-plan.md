# Codex App Server Scratch-Home Runtime Probe Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to execute this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This is a runtime evidence plan, not the client-platform architecture spec and not the v128 permission-branch decision packet.

**Goal:** Produce a scratch-home runtime probe packet that proves or blocks the selected `codex app-server` launcher's basic handshake, `thread/read` projection, server-request evidence path, and config/trust mutation behavior without touching the operator's real Codex home.

**Architecture:** Launch the selected app-server with an isolated `CODEX_HOME` under `/private/tmp`, use a raw JSON-RPC harness that preserves full responses/errors/notifications, and write durable markdown plus JSON diagnostics. Treat no-auth protocol probes, auth/model-gated probes, and v128 permission probes as separate evidence classes.

**Tech Stack:** Python 3 standard library, Codex App Server JSON-RPC over stdio, isolated `CODEX_HOME`, existing exploration packet, generated schema artifacts under `/private/tmp/codex-app-server-exploration`.

---

## Boundary

This plan answers:

- Does the selected launcher enforce the `initialize` / `initialized` lifecycle as documented?
- What does `initialize` return for `codexHome`, `platformFamily`, `platformOs`, and `userAgent` when `CODEX_HOME` is isolated?
- What files does `thread/start` create or mutate under an isolated Codex home?
- What is the live `thread/read(includeTurns=true)` projection shape for a scratch thread?
- Which server-request facts can be proven without a model turn, and which are blocked on safe auth/model-turn execution?

This plan does not:

- Select v128 Branch A1/A2/A3/B/C/D.
- Probe stable `sandboxPolicy` acceptance or experimental `permissions` acceptance.
- Run delegated `/delegate` execution.
- Install or download standalone `codex-app-server`.
- Read, copy, print, hash, or serialize auth tokens from the operator's real Codex home.
- Draft `docs/architecture/2026-05-01-codex-app-server-current-client-platform-rebaseline.md`.

## Inputs

Read first:

- `docs/diagnostics/2026-05-01-codex-app-server-client-platform-exploration.md`
- `docs/diagnostics/codex-app-server-client-platform-exploration.json`
- `docs/plans/2026-05-01-codex-app-server-client-platform-exploration-plan.md`
- `docs/plans/2026-05-01-codex-app-server-v128-execution-sandbox-migration-plan.md`
- `docs/architecture/2026-05-01-codex-app-server-v128-permission-architecture-implications.md`

Use these scratch inputs when present:

- `/private/tmp/codex-app-server-exploration/schemas/codex-cli-app-server/stable`
- `/private/tmp/codex-app-server-exploration/schemas/codex-cli-app-server/experimental`
- `/private/tmp/codex-app-server-exploration/openai-codex-ff27d016`

## Outputs

Create:

- `docs/diagnostics/2026-05-01-codex-app-server-scratch-home-runtime-probes.md`
- `docs/diagnostics/codex-app-server-scratch-home-runtime-probes.json`
- `/private/tmp/codex-app-server-runtime-probes/`

The scratch directory may contain:

- `probe_app_server_runtime.py`
- raw JSONL transcripts
- redacted stderr logs
- pre/post scratch-home manifests
- command output snippets

Do not commit scratch files.

## Probe JSON Schema

The durable JSON artifact must use this top-level shape:

```json
{
  "artifact_version": 1,
  "created_for": "codex-app-server-scratch-home-runtime-probes",
  "repo_worktree": "/Users/jp/Projects/active/claude-code-tool-dev/.worktrees/feature/codex-app-server-client-platform-exploration",
  "selected_launcher": {
    "kind": "codex app-server",
    "path": "/opt/homebrew/bin/codex",
    "version_output": "codex-cli 0.128.0",
    "binary_sha256": "sha256"
  },
  "scratch_environment": {
    "scratch_root": "/private/tmp/codex-app-server-runtime-probes",
    "codex_home": "/private/tmp/codex-app-server-runtime-probes/codex-home",
    "probe_workspace": "/private/tmp/codex-app-server-runtime-probes/workspace",
    "env_overrides": {
      "CODEX_HOME": "/private/tmp/codex-app-server-runtime-probes/codex-home",
      "CODEX_APP_SERVER_DISABLE_MANAGED_CONFIG": "1"
    },
    "operator_codex_home_used": false,
    "auth_values_serialized": false
  },
  "probes": [],
  "codex_home_mutations": {
    "before": [],
    "after": [],
    "created_paths": [],
    "modified_paths": [],
    "deleted_paths": []
  },
  "architecture_spec_readiness_delta": {
    "ready": false,
    "newly_satisfied_items": [],
    "still_missing_items": []
  }
}
```

Each probe entry must include:

```json
{
  "name": "initialize_then_initialized",
  "status": "passed|failed|blocked|partial",
  "requires_auth": false,
  "requires_model_turn": false,
  "request_sequence": [],
  "responses": [],
  "notifications": [],
  "errors": [],
  "classification": "protocol_confirmed|runtime_rejected|blocked_no_safe_auth|blocked_requires_user_approval|unexpected",
  "evidence": []
}
```

Do not store credential values, auth headers, session contents from the operator's real home, or complete stderr when it may include secrets. Redact emails and token-looking strings before writing durable artifacts.

## Task 0: Preflight And Scope Lock

**Files:**
- Read: `docs/diagnostics/2026-05-01-codex-app-server-client-platform-exploration.md`
- Read: `docs/diagnostics/codex-app-server-client-platform-exploration.json`
- Create later: `docs/diagnostics/2026-05-01-codex-app-server-scratch-home-runtime-probes.md`
- Create later: `docs/diagnostics/codex-app-server-scratch-home-runtime-probes.json`

- [ ] Confirm worktree state.

Run:

```bash
git status --short --branch
```

Expected:

```text
## feature/codex-app-server-client-platform-exploration
```

Additional untracked copied input docs and diagnostic artifacts are acceptable. Record the full status in the runtime probe markdown.

- [ ] Confirm selected launcher is still the installed `codex` subcommand.

Run:

```bash
which codex
codex --version
shasum -a 256 "$(which codex)"
command -v codex-app-server || true
```

Expected:
- `codex --version` is `codex-cli 0.128.0`.
- `codex-app-server` may be absent; absence is recorded, not fixed.
- Stop if `codex --version` is not `codex-cli 0.128.0`.

- [ ] Confirm this plan will not run v128 permission-branch probes.

Record this sentence in the markdown output:

```markdown
This packet intentionally does not adjudicate v128 Branch A1/A2/A3/B/C/D. Permission-branch probes remain owned by `docs/plans/2026-05-01-codex-app-server-v128-execution-sandbox-migration-plan.md`.
```

## Task 1: Create Isolated Scratch Environment

**Files:**
- Scratch create: `/private/tmp/codex-app-server-runtime-probes/`
- Scratch create: `/private/tmp/codex-app-server-runtime-probes/codex-home/`
- Scratch create: `/private/tmp/codex-app-server-runtime-probes/workspace/`

- [ ] Create the scratch root and workspace.

Run:

```bash
mkdir -p /private/tmp/codex-app-server-runtime-probes/codex-home
mkdir -p /private/tmp/codex-app-server-runtime-probes/workspace
printf '%s\n' 'scratch probe workspace' > /private/tmp/codex-app-server-runtime-probes/workspace/README.txt
```

Expected:
- Scratch `CODEX_HOME` exists.
- Scratch workspace exists.
- No files under `~/.codex` are touched by this setup.

- [ ] Capture initial scratch-home manifest.

Run:

```bash
find /private/tmp/codex-app-server-runtime-probes/codex-home -mindepth 1 -print | sort > /private/tmp/codex-app-server-runtime-probes/codex-home-before.txt
```

Expected:
- File exists. It may be empty.

## Task 2: Create Raw JSON-RPC Probe Harness

**Files:**
- Create: `/private/tmp/codex-app-server-runtime-probes/probe_app_server_runtime.py`

- [ ] Write a raw JSON-RPC harness that can send requests, send notifications, preserve raw errors, and record notifications.

Use `apply_patch` to create `/private/tmp/codex-app-server-runtime-probes/probe_app_server_runtime.py` with this content:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import queue
import re
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any


TOKEN_PATTERNS = [
    re.compile(r"\\bgh[pousr]_[A-Za-z0-9]{20,}\\b"),
    re.compile(r"\\bsk-[A-Za-z0-9]{20,}\\b"),
    re.compile(r"\\b[A-Za-z0-9_=-]{32,}\\.[A-Za-z0-9_=-]{8,}\\.[A-Za-z0-9_=-]{8,}\\b"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}"),
]


def redact_text(text: str) -> str:
    redacted = text
    for pattern in TOKEN_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not root.exists():
        return rows
    for path in sorted(root.rglob("*")):
        rel = str(path.relative_to(root))
        stat = path.lstat()
        row: dict[str, Any] = {
            "path": rel,
            "kind": "dir" if path.is_dir() else "file",
            "size": stat.st_size,
        }
        if path.is_file():
            row["sha256"] = sha256_path(path)
        rows.append(row)
    return rows


class RawJsonRpc:
    def __init__(self, command: list[str], cwd: Path, env: dict[str, str], timeout: float = 10.0) -> None:
        self.command = command
        self.cwd = cwd
        self.env = env
        self.timeout = timeout
        self.next_id = 0
        self.messages: "queue.Queue[object]" = queue.Queue()
        self.stderr_lines: list[str] = []
        self.process = subprocess.Popen(
            command,
            cwd=str(cwd),
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        threading.Thread(target=self._read_stdout, daemon=True).start()
        threading.Thread(target=self._read_stderr, daemon=True).start()

    def _read_stdout(self) -> None:
        assert self.process.stdout is not None
        for line in self.process.stdout:
            try:
                self.messages.put(json.loads(line))
            except json.JSONDecodeError:
                self.messages.put({"_malformed_stdout": redact_text(line.rstrip("\\n"))})
        self.messages.put({"_eof": True})

    def _read_stderr(self) -> None:
        assert self.process.stderr is not None
        for line in self.process.stderr:
            self.stderr_lines.append(redact_text(line.rstrip("\\n")))

    def request(self, method: str, params: dict[str, Any]) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
        request_id = self.next_id
        self.next_id += 1
        payload = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
        self._write(payload)
        notifications: list[dict[str, Any]] = []
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            message = self._get(deadline - time.time())
            if message is None:
                break
            if message.get("id") == request_id and "method" not in message:
                return message, notifications
            notifications.append(message)
        return {"id": request_id, "error": {"code": "timeout", "message": "timed out waiting for response"}}, notifications

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        payload: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        self._write(payload)

    def drain(self, seconds: float = 0.5) -> list[dict[str, Any]]:
        deadline = time.time() + seconds
        rows: list[dict[str, Any]] = []
        while time.time() < deadline:
            message = self._get(max(0.0, deadline - time.time()))
            if message is None:
                break
            rows.append(message)
        return rows

    def _write(self, payload: dict[str, Any]) -> None:
        assert self.process.stdin is not None
        self.process.stdin.write(json.dumps(payload) + "\\n")
        self.process.stdin.flush()

    def _get(self, timeout: float) -> dict[str, Any] | None:
        try:
            message = self.messages.get(timeout=max(0.0, timeout))
        except queue.Empty:
            return None
        if not isinstance(message, dict):
            return {"_malformed_queue": repr(message)}
        return message

    def close(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=3)


def classify_response(response: dict[str, Any] | None) -> str:
    if response is None:
        return "no_response"
    if "error" in response:
        message = stable_json(response["error"])
        if "Not initialized" in message:
            return "not_initialized_error"
        if "Already initialized" in message:
            return "already_initialized_error"
        return "jsonrpc_error"
    return "ok"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--codex-home", required=True)
    parser.add_argument("--workspace", required=True)
    args = parser.parse_args()

    out = Path(args.out)
    codex_home = Path(args.codex_home)
    workspace = Path(args.workspace)
    codex_home.mkdir(parents=True, exist_ok=True)
    workspace.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["CODEX_HOME"] = str(codex_home)
    env["CODEX_APP_SERVER_DISABLE_MANAGED_CONFIG"] = "1"

    result: dict[str, Any] = {
        "artifact_version": 1,
        "selected_launcher": {
            "kind": "codex app-server",
            "path": subprocess.check_output(["which", "codex"], text=True).strip(),
            "version_output": subprocess.check_output(["codex", "--version"], text=True).strip(),
        },
        "scratch_environment": {
            "codex_home": str(codex_home),
            "probe_workspace": str(workspace),
            "env_overrides": {
                "CODEX_HOME": str(codex_home),
                "CODEX_APP_SERVER_DISABLE_MANAGED_CONFIG": "1",
            },
            "operator_codex_home_used": False,
            "auth_values_serialized": False,
        },
        "codex_home_mutations": {"before": manifest(codex_home), "after": [], "created_paths": [], "modified_paths": [], "deleted_paths": []},
        "probes": [],
    }

    client = RawJsonRpc(["codex", "app-server"], cwd=workspace, env=env)
    try:
        response, notifications = client.request("account/read", {"refreshToken": False})
        result["probes"].append({
            "name": "request_before_initialize_rejection",
            "status": "passed" if classify_response(response) == "not_initialized_error" else "failed",
            "requires_auth": False,
            "requires_model_turn": False,
            "responses": [response],
            "notifications": notifications,
            "errors": [],
            "classification": classify_response(response),
            "evidence": ["Sent account/read before initialize."],
        })
    finally:
        client.close()

    client = RawJsonRpc(["codex", "app-server"], cwd=workspace, env=env)
    try:
        init_response, init_notifications = client.request("initialize", {
            "clientInfo": {
                "name": "codex_collaboration_probe",
                "title": "Codex Collaboration Runtime Probe",
                "version": "0.1.0",
            }
        })
        client.notify("initialized", {})
        post_init_notifications = client.drain(0.25)
        account_response, account_notifications = client.request("account/read", {"refreshToken": False})
        thread_response, thread_notifications = client.request("thread/start", {
            "cwd": str(workspace),
            "approvalPolicy": "never",
            "personality": "pragmatic",
            "serviceName": "codex_collaboration_probe",
        })
        thread_id = None
        if thread_response and isinstance(thread_response.get("result"), dict):
            thread = thread_response["result"].get("thread")
            if isinstance(thread, dict):
                thread_id = thread.get("id")
        read_response = None
        read_notifications: list[dict[str, Any]] = []
        if isinstance(thread_id, str):
            read_response, read_notifications = client.request("thread/read", {"threadId": thread_id, "includeTurns": True})
        result["probes"].append({
            "name": "initialize_then_initialized",
            "status": "passed" if classify_response(init_response) == "ok" else "failed",
            "requires_auth": False,
            "requires_model_turn": False,
            "responses": [init_response],
            "notifications": init_notifications + post_init_notifications,
            "errors": [],
            "classification": classify_response(init_response),
            "evidence": ["Sent initialize then initialized notification."],
        })
        result["probes"].append({
            "name": "account_read_after_initialize",
            "status": "passed" if classify_response(account_response) == "ok" else "failed",
            "requires_auth": False,
            "requires_model_turn": False,
            "responses": [account_response],
            "notifications": account_notifications,
            "errors": [],
            "classification": classify_response(account_response),
            "evidence": ["Sent account/read after initialize."],
        })
        result["probes"].append({
            "name": "thread_start_and_read_projection",
            "status": "passed" if classify_response(thread_response) == "ok" and classify_response(read_response) == "ok" else "failed",
            "requires_auth": False,
            "requires_model_turn": False,
            "responses": [thread_response, read_response],
            "notifications": thread_notifications + read_notifications,
            "errors": [],
            "classification": f"thread_start={classify_response(thread_response)};thread_read={classify_response(read_response)}",
            "evidence": ["Started a scratch thread and read it back with includeTurns=true."],
        })
    finally:
        client.close()

    after = manifest(codex_home)
    before_by_path = {row["path"]: row for row in result["codex_home_mutations"]["before"]}
    after_by_path = {row["path"]: row for row in after}
    result["codex_home_mutations"]["after"] = after
    result["codex_home_mutations"]["created_paths"] = sorted(set(after_by_path) - set(before_by_path))
    result["codex_home_mutations"]["deleted_paths"] = sorted(set(before_by_path) - set(after_by_path))
    result["codex_home_mutations"]["modified_paths"] = sorted(
        path for path in set(before_by_path) & set(after_by_path)
        if before_by_path[path] != after_by_path[path]
    )

    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] Make the harness executable.

Run:

```bash
chmod +x /private/tmp/codex-app-server-runtime-probes/probe_app_server_runtime.py
```

Expected:
- The script is executable.

## Task 3: Run No-Auth Protocol Probes

**Files:**
- Create: `/private/tmp/codex-app-server-runtime-probes/raw-runtime-probes.json`

- [ ] Run the probe harness with scratch `CODEX_HOME`.

Run:

```bash
/private/tmp/codex-app-server-runtime-probes/probe_app_server_runtime.py \
  --codex-home /private/tmp/codex-app-server-runtime-probes/codex-home \
  --workspace /private/tmp/codex-app-server-runtime-probes/workspace \
  --out /private/tmp/codex-app-server-runtime-probes/raw-runtime-probes.json
```

Expected:
- The command exits `0`.
- `raw-runtime-probes.json` exists.
- The JSON contains probes named:
  - `request_before_initialize_rejection`
  - `initialize_then_initialized`
  - `account_read_after_initialize`
  - `thread_start_and_read_projection`

- [ ] Validate the raw probe JSON.

Run:

```bash
jq '.probes[].name' /private/tmp/codex-app-server-runtime-probes/raw-runtime-probes.json
jq '.scratch_environment.operator_codex_home_used, .scratch_environment.auth_values_serialized' /private/tmp/codex-app-server-runtime-probes/raw-runtime-probes.json
```

Expected:
- Probe names print.
- The two booleans are `false` and `false`.

- [ ] Inspect probe status.

Run:

```bash
jq '.probes[] | {name, status, classification}' /private/tmp/codex-app-server-runtime-probes/raw-runtime-probes.json
```

Expected:
- `request_before_initialize_rejection` should be `passed` with `not_initialized_error`.
- `initialize_then_initialized` should be `passed` with `ok`.
- `thread_start_and_read_projection` may pass or fail. If it fails, preserve the raw error and classify it; do not retry by using the operator's real Codex home.

## Task 4: Classify Thread/Read Projection Shape

**Files:**
- Read: `/private/tmp/codex-app-server-runtime-probes/raw-runtime-probes.json`
- Write later: `docs/diagnostics/codex-app-server-scratch-home-runtime-probes.json`

- [ ] Extract thread-start and thread-read response keys.

Run:

```bash
jq '
  .probes[]
  | select(.name == "thread_start_and_read_projection")
  | {
      thread_start_response_keys: (.responses[0].result | keys_unsorted?),
      thread_start_thread_keys: (.responses[0].result.thread | keys_unsorted?),
      thread_read_response_keys: (.responses[1].result | keys_unsorted?),
      thread_read_thread_keys: (.responses[1].result.thread | keys_unsorted?),
      thread_read_turn_count: (.responses[1].result.thread.turns | length?)
    }
' /private/tmp/codex-app-server-runtime-probes/raw-runtime-probes.json
```

Expected:
- The extracted shape is recorded in the durable JSON.
- If `thread/read` failed, record the error shape and mark projection evidence as `blocked` or `failed`.

- [ ] Decide whether projection evidence satisfies the architecture blocker.

Use this rule:

- `satisfied` only if `thread/read` succeeds and returns a `thread` object with a documented path to turns or an explicit empty-turns shape for a new thread.
- `partial` if `thread/read` succeeds but the projection is too shallow to say how completed turns expose agent messages.
- `blocked` if thread creation or readback requires auth or fails under scratch home.

## Task 5: Classify Config/Trust Mutation Under Scratch Home

**Files:**
- Read: `/private/tmp/codex-app-server-runtime-probes/raw-runtime-probes.json`
- Write later: `docs/diagnostics/codex-app-server-scratch-home-runtime-probes.json`

- [ ] Extract created, modified, and deleted scratch-home paths.

Run:

```bash
jq '.codex_home_mutations | {created_paths, modified_paths, deleted_paths}' /private/tmp/codex-app-server-runtime-probes/raw-runtime-probes.json
```

Expected:
- Paths are relative to scratch `CODEX_HOME`.
- No path should reference `/Users/jp/.codex`.

- [ ] Classify trust/config mutation.

Use this rule:

- `no_mutation`: no created, modified, or deleted paths.
- `scratch_only_mutation`: mutations are present but only under `/private/tmp/codex-app-server-runtime-probes/codex-home`.
- `unsafe_operator_home_mutation`: any evidence references the operator's real Codex home. Stop and report this as a blocker.

Record whether `config.toml`, `sessions/`, `log/`, sqlite files, or trust/project-state files were created.

## Task 6: Classify Server-Request Evidence Without Forcing A Model Turn

**Files:**
- Read: `/private/tmp/codex-app-server-runtime-probes/raw-runtime-probes.json`
- Read: `/private/tmp/codex-app-server-exploration/schemas/codex-cli-app-server/experimental/ServerRequest.json`
- Write later: `docs/diagnostics/codex-app-server-scratch-home-runtime-probes.json`

- [ ] Extract server-request schema names.

Run:

```bash
jq . /private/tmp/codex-app-server-exploration/schemas/codex-cli-app-server/experimental/ServerRequest.json
```

Expected:
- The durable markdown summarizes the schema-visible server-request variants.

- [ ] Extract server-initiated requests observed during no-auth probes.

Run:

```bash
jq '
  [.probes[].notifications[]? | select(has("id") and has("method"))]
' /private/tmp/codex-app-server-runtime-probes/raw-runtime-probes.json
```

Expected:
- Usually an empty array for no-auth protocol probes.
- Empty array does not prove execution server-request behavior; record it as "none observed in no-auth handshake/thread probes."

- [ ] Decide whether a model-turn server-request probe is needed.

Use this rule:

- If no server requests appear in no-auth probes, mark `server_request_runtime_evidence.status = "partial"`.
- If `account/read` reports missing auth, mark model-turn server-request probing as `blocked_no_safe_auth`.
- If `account/read` reports authenticated without exposing credentials, stop and ask the user before running any model-mediated turn. Do not run it automatically from this plan.

## Task 7: Write Durable Runtime Probe Packet

**Files:**
- Create: `docs/diagnostics/2026-05-01-codex-app-server-scratch-home-runtime-probes.md`
- Create: `docs/diagnostics/codex-app-server-scratch-home-runtime-probes.json`

- [ ] Write the structured JSON artifact.

Use `/private/tmp/codex-app-server-runtime-probes/raw-runtime-probes.json` as the source and add:

- `created_for`
- `repo_worktree`
- `selected_launcher.binary_sha256`
- `architecture_spec_readiness_delta`
- `server_request_runtime_evidence`
- `thread_read_projection_classification`
- `trust_config_mutation_classification`

Expected:
- The durable JSON parses with `jq`.
- It records `operator_codex_home_used: false`.
- It records `auth_values_serialized: false`.

- [ ] Write the markdown artifact with these sections:

```markdown
# Codex App Server Scratch-Home Runtime Probes

**Date:** 2026-05-01
**Status:** Runtime probe packet complete; not an architecture spec
**Selected launcher:** `codex app-server`
**Scratch CODEX_HOME:** `/private/tmp/codex-app-server-runtime-probes/codex-home`

## Scope

## Launcher And Scratch Environment

## Probe Results

## Thread Read Projection Shape

## Server-Request Evidence

## Config And Trust Mutation

## Architecture Spec Readiness Delta

## Remaining Blockers
```

Expected:
- The markdown clearly distinguishes passed, partial, failed, and blocked probes.
- It does not claim v128 Branch A1/A2/A3/B/C/D is decided.

## Task 8: Verify Artifacts

**Files:**
- Verify: `docs/diagnostics/2026-05-01-codex-app-server-scratch-home-runtime-probes.md`
- Verify: `docs/diagnostics/codex-app-server-scratch-home-runtime-probes.json`

- [ ] Parse the durable JSON.

Run:

```bash
jq . docs/diagnostics/codex-app-server-scratch-home-runtime-probes.json >/dev/null
```

Expected:
- Exit code `0`.

- [ ] Verify no durable artifact contains obvious secrets.

Run:

```bash
rg -n "sk-[A-Za-z0-9]|gh[pousr]_|Authorization: Bearer|refresh_token|access_token" \
  docs/diagnostics/2026-05-01-codex-app-server-scratch-home-runtime-probes.md \
  docs/diagnostics/codex-app-server-scratch-home-runtime-probes.json
```

Expected:
- No matches.

- [ ] Verify no durable artifact claims architecture readiness without blockers resolved.

Run:

```bash
rg -n "Ready to draft architecture spec|Branch A1|Branch A2|Branch A3|implementation selected" \
  docs/diagnostics/2026-05-01-codex-app-server-scratch-home-runtime-probes.md \
  docs/diagnostics/codex-app-server-scratch-home-runtime-probes.json
```

Expected:
- No matches unless the phrase appears in a negated readiness statement.

- [ ] Capture final worktree status.

Run:

```bash
git status --short --branch
```

Expected:
- New untracked runtime probe plan and diagnostics are visible.
- Do not stage or commit unless explicitly asked.

## Acceptance Criteria

The scratch-home runtime probe packet is complete when:

- The selected launcher path, version, and binary hash are recorded.
- Every app-server subprocess is launched with scratch `CODEX_HOME`.
- The durable artifacts record `operator_codex_home_used: false`.
- The durable artifacts record `auth_values_serialized: false`.
- Request-before-initialize behavior is captured with the raw JSON-RPC error.
- `initialize` then `initialized` behavior is captured with raw response metadata.
- `thread/start` and `thread/read(includeTurns=true)` are captured or explicitly blocked.
- Scratch-home created/modified/deleted paths are recorded and classified.
- Server-request schema taxonomy is summarized.
- Server requests observed during no-auth probes are recorded, even if none are observed.
- Model-mediated server-request probing is either not run, or is run only after explicit user approval in a later turn.
- Architecture readiness delta states exactly which previous blockers are satisfied, partial, or still blocked.

## Stop Conditions

Stop and ask the user before proceeding if:

- `codex --version` is not `codex-cli 0.128.0`.
- The app-server touches or reports the operator's real `/Users/jp/.codex` while `CODEX_HOME` is set to scratch.
- A probe requires reading, copying, printing, hashing, or serializing credentials.
- A model-mediated turn appears necessary to produce server-request evidence.
- The standalone `codex-app-server` artifact is needed for equivalence testing.
- Any command would mutate Homebrew, mise, npm, dotfiles, or the parent workspace.

## Final Fresh-Session Response Shape

Use:

- `What changed`
- `Why it changed`
- `Verification performed`
- `Remaining risks`

Name the durable artifacts:

- `docs/diagnostics/2026-05-01-codex-app-server-scratch-home-runtime-probes.md`
- `docs/diagnostics/codex-app-server-scratch-home-runtime-probes.json`

Do not say the architecture spec is complete. If all non-auth probes pass but model-turn server-request evidence is still blocked, say that the packet reduces the blocker set but does not close it.
