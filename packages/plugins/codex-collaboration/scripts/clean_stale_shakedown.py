#!/usr/bin/env python3
"""Remove stale shakedown state files older than 24 hours.

CLI wrapper for ``clean_stale_files()`` from ``server/containment.py``.
Invoked by the shakedown-b1 harness before seed creation.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add package root to sys.path for server imports.
_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
if str(_PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(_PACKAGE_ROOT))

def main() -> int:
    plugin_data = os.environ.get("CLAUDE_PLUGIN_DATA", "")
    if not plugin_data:
        print(
            "clean_stale_shakedown failed: CLAUDE_PLUGIN_DATA not set. "
            f"Got: {plugin_data!r:.100}",
            file=sys.stderr,
        )
        return 1

    data_dir = Path(plugin_data).expanduser().resolve()
    if not data_dir.is_dir():
        print(
            "clean_stale_shakedown failed: CLAUDE_PLUGIN_DATA is not a directory. "
            f"Got: {plugin_data!r:.100}",
            file=sys.stderr,
        )
        return 1

    from server.containment import clean_stale_files, shakedown_dir

    result = clean_stale_files(shakedown_dir(data_dir))
    if result.had_errors:
        print(result.report(), file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(
            f"clean_stale_shakedown failed: unexpected error. Got: {exc!r:.100}",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc
