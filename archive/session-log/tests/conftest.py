"""Pytest configuration for session-log tests."""

import sys
from pathlib import Path

# Add plugin root to path for imports
plugin_root = Path(__file__).parent.parent
sys.path.insert(0, str(plugin_root))
