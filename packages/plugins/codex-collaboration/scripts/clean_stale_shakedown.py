#!/usr/bin/env python3
"""Remove stale shakedown state files older than 24 hours.

CLI wrapper for ``clean_stale_files()`` from ``server/containment.py``.
Invoked by the shakedown-b1 harness before seed creation.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "server"))

from containment import clean_stale_files, shakedown_dir

data_dir = Path(os.environ.get("CLAUDE_PLUGIN_DATA", ""))
if not data_dir.is_dir():
    print(f"CLAUDE_PLUGIN_DATA not set or not a directory: {data_dir!r}", file=sys.stderr)
    sys.exit(1)

clean_stale_files(shakedown_dir(data_dir))
