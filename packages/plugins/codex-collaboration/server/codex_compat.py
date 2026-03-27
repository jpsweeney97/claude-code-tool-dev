"""Codex App Server compatibility — executable source of truth for version pin and method surface.

This module owns the Codex CLI version pin, required/optional method sets,
and startup compatibility checks. The spec (delivery.md §Compatibility Policy)
describes the policy; this module enforces it.

Fixture regeneration: scripts/regenerate_schema.sh
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory


# ──────────────────────────────────────────
# Version pin
# ──────────────────────────────────────────

TESTED_CODEX_VERSION = "0.117.0"
"""Version of codex-cli that the vendored schema was generated from."""

MINIMUM_CODEX_VERSION = "0.117.0"
"""Startup rejects codex-cli versions below this floor."""


# ──────────────────────────────────────────
# SemVer
# ──────────────────────────────────────────

_SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)")


@dataclass(frozen=True, order=True)
class SemVer:
    """Semantic version with comparison support.

    Uses tuple ordering via @dataclass(order=True) on (major, minor, patch).
    Suffixes (e.g., -beta.1) are parsed but ignored for comparison.
    """

    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, version_string: str) -> SemVer:
        """Parse 'X.Y.Z' or 'X.Y.Z-suffix' into SemVer.

        Raises ValueError if the string doesn't start with three dot-separated integers.
        """
        match = _SEMVER_RE.match(version_string)
        if not match:
            raise ValueError(
                f"Version parse failed: expected X.Y.Z format. Got: {version_string!r:.100}"
            )
        return cls(int(match.group(1)), int(match.group(2)), int(match.group(3)))

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


# ──────────────────────────────────────────
# Method surface
# ──────────────────────────────────────────

REQUIRED_METHODS: frozenset[str] = frozenset({
    "thread/start",
    "thread/resume",
    "thread/fork",
    "thread/read",
    "turn/start",
    "turn/interrupt",
})
"""Methods that must be present for the plugin to start. Missing = fail-closed."""

OPTIONAL_METHODS: frozenset[str] = frozenset({
    "turn/steer",
})
"""Methods checked at startup but not required. Missing = warn, record in status."""


# ──────────────────────────────────────────
# Schema extraction
# ──────────────────────────────────────────

def extract_client_methods(client_request_schema_path: Path) -> frozenset[str]:
    """Extract method names from a ClientRequest.json schema file.

    The schema is a JSON Schema with oneOf variants, each containing a method enum
    with exactly one value.

    Raises ValueError if the schema lacks the expected structure (no oneOf key,
    or oneOf variants present but no methods extracted).
    """
    with open(client_request_schema_path) as f:
        schema = json.load(f)

    variants = schema.get("oneOf")
    if variants is None:
        raise ValueError(
            f"Schema extraction failed: no 'oneOf' key in {client_request_schema_path.name}. "
            f"Top-level keys: {sorted(schema.keys())!r:.200}"
        )

    methods: set[str] = set()
    for variant in variants:
        method_enum = variant.get("properties", {}).get("method", {}).get("enum", [])
        if method_enum:
            methods.add(method_enum[0])

    if not methods:
        raise ValueError(
            f"Schema extraction failed: {len(variants)} oneOf variants but 0 methods extracted "
            f"from {client_request_schema_path.name}. Schema structure may have changed."
        )

    return frozenset(methods)


def check_method_surface(
    available_methods: frozenset[str],
) -> tuple[frozenset[str], frozenset[str]]:
    """Check required and optional methods against available methods.

    Returns (missing_required, missing_optional).
    """
    return (
        REQUIRED_METHODS - available_methods,
        OPTIONAL_METHODS - available_methods,
    )


# ──────────────────────────────────────────
# Live binary checks
# ──────────────────────────────────────────

_CODEX_VERSION_RE = re.compile(r"codex(?:-cli)?\s+(\d+\.\d+\.\d+)")


def get_codex_version() -> SemVer:
    """Get the installed Codex CLI version by running ``codex --version``.

    Raises RuntimeError if the binary is missing, times out, or returns unexpected output.
    """
    try:
        result = subprocess.run(
            ["codex", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        raise RuntimeError("Codex binary not found on PATH")
    except subprocess.TimeoutExpired:
        raise RuntimeError("codex --version timed out after 10s")

    if result.returncode != 0:
        raise RuntimeError(
            f"codex --version failed with exit code {result.returncode}. "
            f"Got: {result.stderr.strip()!r:.100}"
        )

    output = result.stdout.strip()
    match = _CODEX_VERSION_RE.match(output)
    if not match:
        raise RuntimeError(
            f"Unexpected codex version format. Got: {output!r:.100}"
        )
    return SemVer.parse(match.group(1))


# ──────────────────────────────────────────
# Compatibility check result
# ──────────────────────────────────────────

@dataclass(frozen=True)
class CompatCheckResult:
    """Result of startup compatibility checks.

    Cache this for the plugin's lifetime — it is used for feature gating.

    T1 populates this from the version-floor check only. Build step 1 extends
    startup to also populate available_methods from the initialize handshake.
    """

    passed: bool
    codex_version: SemVer | None
    available_methods: frozenset[str]
    errors: tuple[str, ...] = ()

    def has_capability(self, method: str) -> bool:
        """Check if a method is available. Use for runtime feature gating of optional methods."""
        return method in self.available_methods

    @classmethod
    def from_version_check(
        cls,
        codex_version: SemVer,
        available_methods: frozenset[str] | None = None,
    ) -> CompatCheckResult:
        """Create a result from a successful version-floor check.

        If available_methods is not provided, behavior depends on whether the
        installed version exactly matches the tested baseline:
        - Exact match: populate from vendored schema (proven by contract tests).
        - Newer version: leave empty (unverified — build step 1 adds live probing).
        """
        if available_methods is None:
            tested = SemVer.parse(TESTED_CODEX_VERSION)
            if codex_version == tested:
                available_methods = REQUIRED_METHODS | OPTIONAL_METHODS
            else:
                # Newer binary — can't prove methods exist without live probe.
                # has_capability() returns False for everything until build step 1.
                available_methods = frozenset()
        return cls(
            passed=True,
            codex_version=codex_version,
            available_methods=available_methods,
        )


def check_version_floor() -> CompatCheckResult:
    """Run the T1 startup check: binary present + version floor.

    Returns a CompatCheckResult with three possible outcomes:

    - **Below minimum**: passed=False, plugin refuses to start.
    - **Exact tested baseline**: passed=True, available_methods populated from
      vendored schema (contract tests prove these methods exist in this version).
    - **Above tested baseline**: passed=True, available_methods empty (unverified).
      has_capability() returns False for everything until build step 1 adds live
      method-surface probing via the App Server handshake.

    Build step 1 will extend this to also run the initialize handshake and
    populate available_methods from the live binary regardless of version.
    """
    try:
        codex_version = get_codex_version()
    except RuntimeError as e:
        return CompatCheckResult(
            passed=False,
            codex_version=None,
            available_methods=frozenset(),
            errors=(str(e),),
        )

    min_version = SemVer.parse(MINIMUM_CODEX_VERSION)
    if codex_version < min_version:
        return CompatCheckResult(
            passed=False,
            codex_version=codex_version,
            available_methods=frozenset(),
            errors=(
                f"Codex version {codex_version} below minimum {MINIMUM_CODEX_VERSION}",
            ),
        )

    return CompatCheckResult.from_version_check(codex_version)


def probe_live_method_surface() -> frozenset[str]:
    """Probe the installed binary's App Server method surface.

    This uses ``codex app-server generate-json-schema`` against the installed
    binary, then extracts methods from the generated ``ClientRequest.json``.
    """

    try:
        with TemporaryDirectory(prefix="codex-collab-schema-") as temp_dir:
            result = subprocess.run(
                [
                    "codex",
                    "app-server",
                    "generate-json-schema",
                    "--out",
                    temp_dir,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    "Live method probe failed: schema generation returned "
                    f"exit code {result.returncode}. Got: {result.stderr.strip()!r:.100}"
                )
            schema_path = Path(temp_dir) / "ClientRequest.json"
            if not schema_path.exists():
                raise RuntimeError(
                    "Live method probe failed: generated ClientRequest.json missing. "
                    f"Got: {str(schema_path)!r:.100}"
                )
            return extract_client_methods(schema_path)
    except FileNotFoundError as exc:
        raise RuntimeError(
            "Live method probe failed: codex binary not found on PATH"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            "Live method probe failed: schema generation timed out after 30s"
        ) from exc


def check_live_runtime_compatibility() -> CompatCheckResult:
    """Run the R1 compatibility checks against the installed binary.

    R1 extends the T1 version-floor check with a live method-surface probe from
    the installed binary. Required methods fail closed. Optional methods are
    recorded for feature gating.
    """

    version_result = check_version_floor()
    if not version_result.passed:
        return version_result

    assert version_result.codex_version is not None

    try:
        available_methods = probe_live_method_surface()
    except RuntimeError as exc:
        return CompatCheckResult(
            passed=False,
            codex_version=version_result.codex_version,
            available_methods=frozenset(),
            errors=(str(exc),),
        )

    missing_required, missing_optional = check_method_surface(available_methods)
    errors: list[str] = []
    if missing_required:
        errors.append(
            "Live runtime compatibility failed: required methods missing. "
            f"Got: {sorted(missing_required)!r:.200}"
        )
    if missing_optional:
        errors.append(
            "Live runtime compatibility warning: optional methods missing. "
            f"Got: {sorted(missing_optional)!r:.200}"
        )

    return CompatCheckResult(
        passed=not missing_required,
        codex_version=version_result.codex_version,
        available_methods=available_methods,
        errors=tuple(errors),
    )
