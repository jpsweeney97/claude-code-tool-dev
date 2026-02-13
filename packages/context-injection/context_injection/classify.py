"""File type classification by extension.

Maps file paths to FileKind for redaction routing. Config files get
format-specific redaction; code and unknown files get generic token
redaction only.

Extension mapping from v0b master plan.
"""

from __future__ import annotations

import os
from enum import StrEnum


class FileKind(StrEnum):
    """File type classification for redaction routing."""

    CODE = "code"
    CONFIG_ENV = "config_env"
    CONFIG_INI = "config_ini"
    CONFIG_JSON = "config_json"
    CONFIG_YAML = "config_yaml"
    CONFIG_TOML = "config_toml"
    UNKNOWN = "unknown"

    @property
    def is_config(self) -> bool:
        """True for all CONFIG_* variants."""
        return self.value.startswith("config_")


_CONFIG_MAP: dict[str, FileKind] = {
    ".env": FileKind.CONFIG_ENV,
    ".json": FileKind.CONFIG_JSON,
    ".jsonc": FileKind.CONFIG_JSON,
    ".yaml": FileKind.CONFIG_YAML,
    ".yml": FileKind.CONFIG_YAML,
    ".toml": FileKind.CONFIG_TOML,
    ".ini": FileKind.CONFIG_INI,
    ".cfg": FileKind.CONFIG_INI,
    ".properties": FileKind.CONFIG_INI,
}

_CODE_EXTENSIONS: frozenset[str] = frozenset({
    ".py", ".pyi", ".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs",
    ".go", ".rs", ".rb", ".java", ".kt", ".scala",
    ".c", ".cpp", ".cc", ".h", ".hpp", ".cs",
    ".swift", ".sh", ".bash", ".zsh",
    ".pl", ".php", ".lua", ".r",
    ".ex", ".exs", ".erl", ".hs",
    ".sql", ".html", ".htm", ".css", ".scss",
    ".vue", ".svelte", ".md", ".rst", ".txt", ".xml",
})


def classify_path(path: str) -> FileKind:
    """Classify file by extension. Returns UNKNOWN for unrecognized extensions.

    Handles dotenv files (.env, .env.local) by basename check since
    os.path.splitext(".env") returns no extension.
    """
    name = os.path.basename(path).lower()
    _, ext = os.path.splitext(name)

    # Dotenv files: .env, .env.local, .env.production, etc.
    if name == ".env" or name.startswith(".env."):
        return FileKind.CONFIG_ENV

    # Extension-based config classification
    if ext in _CONFIG_MAP:
        return _CONFIG_MAP[ext]

    # Known code extensions
    if ext in _CODE_EXTENSIONS:
        return FileKind.CODE

    return FileKind.UNKNOWN
