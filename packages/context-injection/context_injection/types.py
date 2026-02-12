"""Pydantic protocol models for the context injection contract.

All models inherit from ProtocolModel:
- extra="forbid" — rejects unknown fields (catches contract drift)
- strict=True — no type coercion (MCP SDK handles JSON parsing)
- frozen=True — immutable after construction (security-critical for HMAC)

Contract reference: docs/references/context-injection-contract.md
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict

from context_injection.enums import ClaimStatus, Posture, TemplateId

SCHEMA_VERSION: str = "0.1.0"
"""Single-point version control. 0.x uses exact-match semantics."""

SchemaVersionLiteral = Literal["0.1.0"]


class ProtocolModel(BaseModel):
    """Base for all protocol types. Frozen, strict, forbids extra fields."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


# --- TurnRequest input models (Call 1 input) ---


class Claim(ProtocolModel):
    """A claim from the ledger."""

    text: str
    status: Literal["new", "reinforced", "revised", "conceded"]
    turn: int


class Unresolved(ProtocolModel):
    """An unresolved question from the ledger."""

    text: str
    turn: int


class Focus(ProtocolModel):
    """The current focus the agent is probing."""

    text: str
    claims: list[Claim]
    unresolved: list[Unresolved]


class EvidenceRecord(ProtocolModel):
    """A prior evidence-bearing scout, for dedupe and budget tracking."""

    entity_key: str
    template_id: Literal[
        "clarify.file_path",
        "clarify.symbol",
        "probe.file_repo_fact",
        "probe.symbol_repo_fact",
    ]
    turn: int


class TurnRequest(ProtocolModel):
    """Call 1 input: agent sends focus-scoped ledger data."""

    schema_version: SchemaVersionLiteral
    turn_number: int
    conversation_id: str
    focus: Focus
    context_claims: list[Claim] = []
    evidence_history: list[EvidenceRecord] = []
    posture: Literal["adversarial", "collaborative", "exploratory", "evaluative"]
