"""CCDI PostToolUse hook: trigger inventory rebuild on docs_epoch change.

Reads PostToolUse payload from stdin. If ``tool_response.docs_epoch`` is
present, invokes ``build_inventory.py`` to regenerate the compiled inventory.

Resilience principle: **never blocks tool use** -- always exits 0.  If the
build fails, a warning is logged and execution continues.

The ``process_event`` function is injectable for testing -- pass a custom
``build_fn`` to avoid requiring an MCP connection.

CLI usage (from hooks.json / PostToolUse):
    python -m hooks.ccdi_inventory_refresh < payload.json
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from typing import Any, Callable

logger = logging.getLogger(__name__)

# Type for the build function: takes epoch string, returns success bool
BuildFn = Callable[[str], bool]


def _default_build_fn(epoch: str) -> bool:
    """Default build function: invoke build_inventory.py via subprocess."""
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "scripts.ccdi.build_inventory", "--force"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if proc.returncode != 0:
            logger.warning(
                "build_inventory failed (exit %d): %s",
                proc.returncode,
                proc.stderr.strip(),
            )
            return False
        return True
    except subprocess.TimeoutExpired:
        logger.warning("build_inventory timed out after 60s")
        return False
    except Exception as exc:
        logger.warning("build_inventory subprocess error: %s", exc)
        return False


def process_event(
    payload: dict[str, Any],
    build_fn: BuildFn | None = None,
) -> bool:
    """Process a PostToolUse event. Returns True if build was triggered successfully.

    Args:
        payload: PostToolUse JSON payload.
        build_fn: Callable that takes an epoch string and returns True on success.
                  Defaults to invoking build_inventory.py via subprocess.

    Returns:
        True if the build was triggered and succeeded, False otherwise.
    """
    if build_fn is None:
        build_fn = _default_build_fn

    # Extract docs_epoch ONLY from tool_response (not tool_result, not root)
    tool_response = payload.get("tool_response")
    if not isinstance(tool_response, dict):
        return False

    epoch = tool_response.get("docs_epoch")
    if epoch is None:
        return False

    # Epoch found -- trigger build
    logger.info("docs_epoch detected: %s -- triggering inventory rebuild", epoch)
    try:
        result = build_fn(epoch)
        if not result:
            logger.warning("Inventory rebuild returned failure for epoch %s", epoch)
            return False
        return True
    except Exception as exc:
        logger.warning("Inventory rebuild failed for epoch %s: %s", epoch, exc)
        return False


# ---------------------------------------------------------------------------
# CLI entry point -- reads PostToolUse payload from stdin
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Failed to parse PostToolUse payload: %s", exc)
        sys.exit(0)  # Fail-open: never block tool use

    process_event(payload)
    sys.exit(0)  # Always exit 0 -- fail-open
