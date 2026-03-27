"""Minimal JSON-RPC client for `codex app-server`."""

from __future__ import annotations

import json
import subprocess
import threading
from collections import deque
from pathlib import Path
from queue import Empty, Queue
from typing import Any


_EOF = object()


class JsonRpcError(RuntimeError):
    """JSON-RPC request failure."""


class JsonRpcClient:
    """Sequential JSON-RPC client backed by a long-lived subprocess."""

    def __init__(
        self,
        command: list[str],
        *,
        cwd: Path | None = None,
        request_timeout: float = 30.0,
    ) -> None:
        self._command = command
        self._cwd = cwd
        self._request_timeout = request_timeout
        self._process: subprocess.Popen[str] | None = None
        self._message_queue: Queue[object] = Queue()
        self._notification_backlog: deque[dict[str, Any]] = deque()
        self._stderr_lines: deque[str] = deque(maxlen=200)
        self._stdout_thread: threading.Thread | None = None
        self._stderr_thread: threading.Thread | None = None
        self._next_id = 0

    def start(self) -> None:
        """Start the subprocess and background readers."""

        if self._process is not None:
            return
        self._process = subprocess.Popen(
            self._command,
            cwd=str(self._cwd) if self._cwd is not None else None,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self._stdout_thread = threading.Thread(target=self._read_stdout, daemon=True)
        self._stderr_thread = threading.Thread(target=self._read_stderr, daemon=True)
        self._stdout_thread.start()
        self._stderr_thread.start()

    def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        """Send a request and wait for its response, buffering notifications."""

        self.start()
        assert self._process is not None
        assert self._process.stdin is not None
        request_id = self._next_id
        self._next_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }
        try:
            self._process.stdin.write(json.dumps(payload) + "\n")
            self._process.stdin.flush()
        except BrokenPipeError as exc:
            raise RuntimeError(
                f"JSON-RPC request failed: broken stdin pipe. Got: {method!r:.100}"
            ) from exc

        while True:
            message = self._get_message()
            if "method" in message:
                self._notification_backlog.append(message)
                continue
            if message.get("id") != request_id:
                raise RuntimeError(
                    "JSON-RPC request failed: received unexpected response id. "
                    f"Got: {message!r:.100}"
                )
            if "error" in message:
                error = message["error"]
                raise JsonRpcError(
                    f"JSON-RPC request failed: {error!r:.100}. Got: {method!r:.100}"
                )
            result = message.get("result")
            if not isinstance(result, dict):
                raise RuntimeError(
                    "JSON-RPC request failed: response result is not an object. "
                    f"Got: {result!r:.100}"
                )
            return result

    def next_notification(self, timeout: float | None = None) -> dict[str, Any]:
        """Return the next buffered or streamed notification."""

        if self._notification_backlog:
            return self._notification_backlog.popleft()
        return self._get_message(timeout=timeout)

    def close(self) -> None:
        """Terminate the subprocess."""

        if self._process is None:
            return
        process = self._process
        self._process = None
        if process.stdin is not None:
            process.stdin.close()
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

    def stderr_tail(self) -> str:
        """Return recent stderr content for diagnostics."""

        return "".join(self._stderr_lines).strip()

    def _get_message(self, timeout: float | None = None) -> dict[str, Any]:
        effective_timeout = self._request_timeout if timeout is None else timeout
        try:
            message = self._message_queue.get(timeout=effective_timeout)
        except Empty as exc:
            raise TimeoutError("JSON-RPC read failed: timed out waiting for message") from exc
        if message is _EOF:
            raise RuntimeError(
                "JSON-RPC read failed: app-server exited unexpectedly. "
                f"Got: {self.stderr_tail()!r:.100}"
            )
        if not isinstance(message, dict):
            raise RuntimeError(
                "JSON-RPC read failed: malformed queue message. "
                f"Got: {message!r:.100}"
            )
        return message

    def _read_stdout(self) -> None:
        assert self._process is not None
        assert self._process.stdout is not None
        for line in self._process.stdout:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                self._message_queue.put(payload)
        self._message_queue.put(_EOF)

    def _read_stderr(self) -> None:
        assert self._process is not None
        assert self._process.stderr is not None
        for line in self._process.stderr:
            self._stderr_lines.append(line)
