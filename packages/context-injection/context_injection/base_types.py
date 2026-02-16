"""Base protocol types extracted from types.py to break import cycle.

Canonical rule: all code imports from `types.py` (which re-exports these).
Only `ledger.py` imports directly from `base_types.py`.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class ProtocolModel(BaseModel):
    """Base model for all protocol types."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class Claim(ProtocolModel):
    """A claim from the ledger."""

    text: str
    status: Literal["new", "reinforced", "revised", "conceded"]
    turn: int


class Unresolved(ProtocolModel):
    """An unresolved question from the ledger."""

    text: str
    turn: int
