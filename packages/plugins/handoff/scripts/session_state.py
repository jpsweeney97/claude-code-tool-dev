#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))

from handoff_runtime.session_state import main  # noqa: E402  -- sys.path bootstrap above

if __name__ == "__main__":
    raise SystemExit(main())
