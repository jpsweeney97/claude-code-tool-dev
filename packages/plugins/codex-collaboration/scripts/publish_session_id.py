#!/usr/bin/env python3
"""SessionStart hook: publish the host session identity for MCP server use.

Reads the Claude Code session_id from the hook's stdin JSON payload and
writes it to ${CLAUDE_PLUGIN_DATA}/session_id. The codex-collaboration MCP
server reads this file on first dialogue tool call to initialize
session-scoped stores (LineageStore, TurnStore, OperationJournal).

Contract:
- Called once per Claude Code session via the SessionStart hook.
- Overwrites any stale session_id from a previous session.
- The MCP server treats the published identity as pinned: it reads the file
  once, caches the value, and refuses mid-process identity changes.
"""

from __future__ import annotations

import json
import os
import sys


def main() -> None:
    plugin_data = os.environ.get("CLAUDE_PLUGIN_DATA")
    if not plugin_data:
        return

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return

    session_id = payload.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        return

    target = os.path.join(plugin_data, "session_id")
    tmp = target + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(session_id)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, target)


if __name__ == "__main__":
    main()
