"""Tests for file type classification."""

import pytest

from context_injection.classify import FileKind, classify_path


class TestFileKind:
    def test_is_config_true_for_all_config_variants(self) -> None:
        for kind in FileKind:
            if kind.value.startswith("config_"):
                assert kind.is_config is True, f"{kind} should be config"

    def test_is_config_false_for_non_config(self) -> None:
        assert FileKind.CODE.is_config is False
        assert FileKind.UNKNOWN.is_config is False

    def test_all_values_are_lowercase(self) -> None:
        for kind in FileKind:
            assert kind.value == kind.value.lower()


class TestClassifyPath:
    # --- Dotenv files (basename-based detection) ---

    @pytest.mark.parametrize(
        "path",
        [".env", ".env.local", ".env.production", "src/.env", "/repo/.env.staging"],
    )
    def test_dotenv_by_basename(self, path: str) -> None:
        assert classify_path(path) == FileKind.CONFIG_ENV

    def test_dotenv_by_extension(self) -> None:
        """Files like config.env use extension-based detection."""
        assert classify_path("config.env") == FileKind.CONFIG_ENV

    # --- Config formats (extension-based) ---

    @pytest.mark.parametrize(
        "path, expected",
        [
            ("settings.json", FileKind.CONFIG_JSON),
            ("tsconfig.jsonc", FileKind.CONFIG_JSON),
            ("config.yaml", FileKind.CONFIG_YAML),
            ("docker-compose.yml", FileKind.CONFIG_YAML),
            ("pyproject.toml", FileKind.CONFIG_TOML),
            ("config.ini", FileKind.CONFIG_INI),
            ("setup.cfg", FileKind.CONFIG_INI),
            ("app.properties", FileKind.CONFIG_INI),
        ],
    )
    def test_config_by_extension(self, path: str, expected: FileKind) -> None:
        assert classify_path(path) == expected

    # --- Code files ---

    @pytest.mark.parametrize(
        "path",
        ["app.py", "index.ts", "main.go", "lib.rs", "App.java", "script.sh"],
    )
    def test_code_classification(self, path: str) -> None:
        assert classify_path(path) == FileKind.CODE

    # --- Unknown ---

    @pytest.mark.parametrize(
        "path",
        ["Makefile", "Dockerfile", "LICENSE", "file.xyz", ".gitignore"],
    )
    def test_unknown_classification(self, path: str) -> None:
        assert classify_path(path) == FileKind.UNKNOWN

    # --- Case insensitivity ---

    def test_case_insensitive_extension(self) -> None:
        assert classify_path("Config.JSON") == FileKind.CONFIG_JSON
        assert classify_path("APP.PY") == FileKind.CODE

    # --- Full paths ---

    def test_full_path_uses_basename_extension(self) -> None:
        assert classify_path("/repo/src/config/settings.yaml") == FileKind.CONFIG_YAML
        assert classify_path("/repo/.env") == FileKind.CONFIG_ENV
        assert classify_path("/repo/src/main.py") == FileKind.CODE

    # --- is_config routing ---

    def test_all_config_kinds_are_config(self) -> None:
        """Every CONFIG_* member returns is_config=True."""
        config_kinds = {FileKind.CONFIG_ENV, FileKind.CONFIG_INI, FileKind.CONFIG_JSON,
                        FileKind.CONFIG_YAML, FileKind.CONFIG_TOML}
        for kind in config_kinds:
            assert kind.is_config is True
