"""Tests for env-tunable runtime configuration in delegation_controller.

Covers ``_read_approval_operator_window_seconds`` — the helper that backs
``_APPROVAL_OPERATOR_WINDOW_SECONDS`` and is read at module load.
"""

from __future__ import annotations

import logging
import os
from unittest.mock import patch

import pytest

from server.delegation_controller import (
    _APPROVAL_OPERATOR_WINDOW_SECONDS_DEFAULT,
    _APPROVAL_OPERATOR_WINDOW_SECONDS_ENV,
    _read_approval_operator_window_seconds,
)


class TestReadApprovalOperatorWindowSeconds:
    def test_default_when_env_unset(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop(_APPROVAL_OPERATOR_WINDOW_SECONDS_ENV, None)
            assert (
                _read_approval_operator_window_seconds()
                == _APPROVAL_OPERATOR_WINDOW_SECONDS_DEFAULT
            )

    def test_custom_integer(self) -> None:
        with patch.dict(
            os.environ, {_APPROVAL_OPERATOR_WINDOW_SECONDS_ENV: "1800"}
        ):
            assert _read_approval_operator_window_seconds() == 1800.0

    def test_custom_float(self) -> None:
        with patch.dict(
            os.environ, {_APPROVAL_OPERATOR_WINDOW_SECONDS_ENV: "1800.5"}
        ):
            assert _read_approval_operator_window_seconds() == 1800.5

    def test_invalid_string_falls_back_with_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        with patch.dict(
            os.environ, {_APPROVAL_OPERATOR_WINDOW_SECONDS_ENV: "abc"}
        ):
            with caplog.at_level(logging.WARNING):
                value = _read_approval_operator_window_seconds()
        assert value == _APPROVAL_OPERATOR_WINDOW_SECONDS_DEFAULT
        assert "not numeric" in caplog.text.lower()

    def test_zero_falls_back_with_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        with patch.dict(
            os.environ, {_APPROVAL_OPERATOR_WINDOW_SECONDS_ENV: "0"}
        ):
            with caplog.at_level(logging.WARNING):
                value = _read_approval_operator_window_seconds()
        assert value == _APPROVAL_OPERATOR_WINDOW_SECONDS_DEFAULT
        assert "must be positive" in caplog.text.lower()

    def test_negative_falls_back_with_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        with patch.dict(
            os.environ, {_APPROVAL_OPERATOR_WINDOW_SECONDS_ENV: "-100"}
        ):
            with caplog.at_level(logging.WARNING):
                value = _read_approval_operator_window_seconds()
        assert value == _APPROVAL_OPERATOR_WINDOW_SECONDS_DEFAULT
        assert "must be positive" in caplog.text.lower()

    def test_empty_string_falls_back_with_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        with patch.dict(os.environ, {_APPROVAL_OPERATOR_WINDOW_SECONDS_ENV: ""}):
            with caplog.at_level(logging.WARNING):
                value = _read_approval_operator_window_seconds()
        assert value == _APPROVAL_OPERATOR_WINDOW_SECONDS_DEFAULT
        assert "not numeric" in caplog.text.lower()
