"""Path canonicalization, denylist, and safety checks.

Two exported check functions:
- check_path_compile_time(): Call 1 full pipeline (normalize → containment → denylist → git ls-files)
- check_path_runtime(): Call 2 lightweight re-check (realpath → containment → regular file)

Security boundary: prevents reading sensitive files (.env, .pem, .ssh/, .git/),
traversal attacks (../), NUL injection, and untracked files.
"""

import os
import re
import unicodedata
from dataclasses import dataclass
from fnmatch import fnmatch
from typing import Literal, overload


# --- Denylist configuration ---

DENYLIST_DIRS: tuple[str, ...] = (
    ".git",
    ".git/*",
    ".ssh",
    ".ssh/*",
    "__pycache__",
    "__pycache__/*",
    "node_modules",
    "node_modules/*",
    ".svn",
    ".svn/*",
    ".hg",
    ".hg/*",
)
"""Glob patterns for denied directory prefixes.

Each directory has two entries: bare name (denies the directory itself) and
name/* (denies any file within it). Both are needed because fnmatch matches
against individual path components, not the full path.
"""

DENYLIST_FILES: tuple[str, ...] = (
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "*.jks",
    "*.keystore",
    "id_rsa",
    "id_rsa.*",
    "id_ed25519",
    "id_ed25519.*",
    "id_dsa",
    "id_ecdsa",
)
"""Glob patterns for denied file basenames."""

ENV_EXCEPTIONS: frozenset[str] = frozenset(
    {
        ".env.example",
        ".env.sample",
        ".env.template",
    }
)
"""Env-like files that are safe to read (no secrets)."""

_RISK_SIGNAL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"secret"),
    re.compile(r"token"),
    re.compile(r"credential"),
)
"""Substrings in path that indicate potential secret content."""


# --- Result types ---


@dataclass(frozen=True, slots=True)
class CompileTimeResult:
    """Result of check_path_compile_time().

    Maps to PathDecision (types.py) in the pipeline via field-by-field copy
    in pipeline.py:145-156. Both types use the same status values.

    status values align with PathStatus enum:
    - "allowed": safe to scout
    - "denied": blocked by denylist
    - "not_tracked": not in git ls-files
    - "unresolved": could not resolve path
    """

    status: Literal["allowed", "denied", "not_tracked", "unresolved"]
    user_rel: str
    resolved_rel: str | None = None
    risk_signal: bool = False
    deny_reason: str | None = None
    candidates: list[str] | None = None
    unresolved_reason: (
        Literal["zero_candidates", "multiple_candidates", "timeout"] | None
    ) = None


@dataclass(frozen=True, slots=True)
class RuntimeResult:
    """Result of check_path_runtime().

    status values:
    - "allowed": file exists, is regular, within repo root
    - "denied": containment check failed
    - "not_found": file does not exist or is not a regular file
    """

    status: Literal["allowed", "denied", "not_found"]
    resolved_abs: str | None = None
    deny_reason: str | None = None


# --- Input normalization ---


@overload
def normalize_input_path(raw: str) -> str: ...


@overload
def normalize_input_path(
    raw: str, *, split_anchor: Literal[True]
) -> tuple[str, int | None]: ...


def normalize_input_path(
    raw: str, *, split_anchor: bool = False
) -> str | tuple[str, int | None]:
    """Normalize a user-supplied path string.

    Steps:
    1. Strip surrounding backticks, single quotes, double quotes
    2. Reject NUL bytes
    3. Replace backslashes with forward slashes
    4. NFC-normalize Unicode
    5. Reject absolute paths
    6. Reject directory traversal (..)
    7. Optionally split line-number anchor (:N or #LN)

    Raises:
        ValueError: On NUL bytes, absolute paths, or traversal attempts.
    """
    # Strip surrounding quotes/backticks
    path = raw.strip()
    if len(path) >= 2:
        if path[0] == "`" and path[-1] == "`":
            path = path[1:-1]
        elif path[0] == '"' and path[-1] == '"':
            path = path[1:-1]
        elif path[0] == "'" and path[-1] == "'":
            path = path[1:-1]

    # Reject NUL bytes
    if "\x00" in path:
        raise ValueError(
            f"normalize_input_path failed: NUL byte in path. Got: {raw!r:.100}"
        )

    # Backslash to forward slash
    path = path.replace("\\", "/")

    # NFC normalize
    path = unicodedata.normalize("NFC", path)

    # Reject absolute paths
    if path.startswith("/"):
        raise ValueError(
            f"normalize_input_path failed: absolute path not allowed. Got: {raw!r:.100}"
        )

    # Reject traversal
    parts = path.split("/")
    if ".." in parts:
        raise ValueError(
            f"normalize_input_path failed: directory traversal not allowed. Got: {raw!r:.100}"
        )

    # Split anchor if requested
    line: int | None = None
    if split_anchor:
        path, line = _split_anchor(path)

    if split_anchor:
        return path, line
    return path


def _split_anchor(path: str) -> tuple[str, int | None]:
    """Split a line-number anchor from a path.

    Supports:
    - Colon anchor: src/app.py:42
    - GitHub anchor: src/app.py#L42
    """
    # GitHub anchor: #L<number>
    match = re.search(r"#L(\d+)$", path)
    if match:
        return path[: match.start()], int(match.group(1))

    # Colon anchor: :<number> at end (but not Windows drive like C:)
    match = re.search(r":(\d+)$", path)
    if match:
        prefix = path[: match.start()]
        # Don't split if it looks like a Windows drive letter (single char before colon)
        if len(prefix) > 1 or not prefix.isalpha():
            return prefix, int(match.group(1))

    return path, None


# --- Denylist checking ---


def _is_denied_dir(path: str) -> str | None:
    """Check if any path component matches a denied directory pattern.

    For simple patterns (no /): fnmatch against individual components.
    For patterns with / (e.g., ".git/*"): fnmatch against accumulated path prefix.

    Returns deny reason or None.
    """
    parts = path.split("/")
    # Check each prefix segment against dir patterns
    for i, part in enumerate(parts):
        for pattern in DENYLIST_DIRS:
            # For patterns without /, match against individual component
            if "/" not in pattern:
                if fnmatch(part, pattern):
                    return f"directory matches denylist pattern: {pattern}"
            else:
                # For patterns with /, match against the relative path from start
                rel_prefix = "/".join(parts[: i + 2]) if i + 1 < len(parts) else None
                if rel_prefix and fnmatch(rel_prefix, pattern):
                    return f"path matches denylist pattern: {pattern}"
    return None


def _is_denied_file(path: str) -> str | None:
    """Check if the file basename matches a denied file pattern.

    Respects ENV_EXCEPTIONS for safe .env variants.
    Returns deny reason or None.
    """
    basename = os.path.basename(path)

    # Check env exceptions first — these override the denylist
    if basename in ENV_EXCEPTIONS:
        return None

    for pattern in DENYLIST_FILES:
        if fnmatch(basename, pattern):
            return f"file matches denylist pattern: {pattern}"
    return None


def _check_denylist(normalized_path: str) -> str | None:
    """Run full denylist check (dirs then files).

    Returns deny reason string, or None if allowed.
    """
    reason = _is_denied_dir(normalized_path)
    if reason:
        return reason
    return _is_denied_file(normalized_path)


# --- Risk signal detection ---


def is_risk_signal_path(path: str) -> bool:
    """Check if path contains risk-signal substrings (secret, token, credential).

    Risk signals don't block access — they flag the scout option for the agent.
    """
    path_lower = path.lower()
    return any(pattern.search(path_lower) for pattern in _RISK_SIGNAL_PATTERNS)


# --- Compile-time check (Call 1: full pipeline) ---


def check_path_compile_time(
    raw_path: str,
    *,
    repo_root: str,
    git_files: set[str],
) -> CompileTimeResult:
    """Full path safety check for Call 1 (TurnPacket generation).

    Pipeline:
    1. Normalize input path
    2. Resolve to absolute via repo_root (logical join if file doesn't exist)
    3. Containment check (resolved path must be under repo_root)
    4. Denylist check (dirs + files)
    5. Git ls-files gating (must be in tracked set)
    6. Risk signal detection

    Returns CompileTimeResult with status and metadata.
    """
    # Step 1: Normalize
    try:
        normalized = normalize_input_path(raw_path)
    except ValueError as exc:
        return CompileTimeResult(
            status="denied",
            user_rel=raw_path,
            deny_reason=str(exc),
        )

    # Step 2: Resolve path
    # Use logical join for unit-testability (file may not exist on disk)
    logical_abs = os.path.normpath(os.path.join(repo_root, normalized))

    # If the file exists on disk, use realpath for symlink resolution
    if os.path.exists(logical_abs):
        resolved_abs = os.path.realpath(logical_abs)
    else:
        resolved_abs = logical_abs

    # Step 3: Containment check
    repo_root_normalized = os.path.normpath(repo_root)
    # Ensure resolved path is under repo root
    # Use os.path.commonpath to avoid prefix false positives
    # (e.g., /tmp/repo-evil shouldn't match /tmp/repo)
    if not (
        resolved_abs == repo_root_normalized
        or resolved_abs.startswith(repo_root_normalized + os.sep)
    ):
        return CompileTimeResult(
            status="denied",
            user_rel=normalized,
            deny_reason="path escapes repository root",
        )

    # Compute resolved relative path
    resolved_rel = os.path.relpath(resolved_abs, repo_root_normalized)
    # Normalize separators to forward slash for cross-platform consistency
    resolved_rel = resolved_rel.replace(os.sep, "/")

    # Step 4: Denylist check
    deny_reason = _check_denylist(normalized)
    if deny_reason:
        return CompileTimeResult(
            status="denied",
            user_rel=normalized,
            resolved_rel=resolved_rel,
            deny_reason=deny_reason,
            risk_signal=is_risk_signal_path(normalized),
        )

    # Step 5: Git ls-files gating
    if normalized not in git_files:
        return CompileTimeResult(
            status="not_tracked",
            user_rel=normalized,
            resolved_rel=resolved_rel,
            risk_signal=is_risk_signal_path(normalized),
        )

    # Step 6: Allowed — compute risk signal
    return CompileTimeResult(
        status="allowed",
        user_rel=normalized,
        resolved_rel=resolved_rel,
        risk_signal=is_risk_signal_path(normalized),
    )


# --- Runtime check (Call 2: lightweight re-check) ---


def check_path_runtime(
    resolved_path: str,
    *,
    repo_root: str,
) -> RuntimeResult:
    """Lightweight runtime path check for Call 2 (ScoutResult execution).

    Checks:
    1. Realpath resolution (follows symlinks)
    2. Containment under repo_root
    3. Regular file existence

    This re-validates at execution time. The compile-time check already
    verified denylist and git tracking; runtime re-checks containment
    and file existence (which may have changed between Call 1 and Call 2).

    TOCTOU note: A symlink could be swapped between this check and the
    subsequent file read. Accepted for v0a — the agent is the consumer,
    and the denylist re-check at Call 2 time provides defense in depth.
    """
    # Resolve realpath
    real = os.path.realpath(resolved_path)

    # Containment check
    repo_root_normalized = os.path.normpath(repo_root)
    if not (
        real == repo_root_normalized or real.startswith(repo_root_normalized + os.sep)
    ):
        return RuntimeResult(
            status="denied",
            deny_reason="resolved path escapes repository root",
        )

    # Regular file check
    if not os.path.isfile(real):
        return RuntimeResult(
            status="not_found",
            resolved_abs=real,
        )

    return RuntimeResult(
        status="allowed",
        resolved_abs=real,
    )
