"""Pydantic protocol models for the context injection contract.

All models inherit from ProtocolModel:
- extra="forbid" — rejects unknown fields (catches contract drift)
- strict=True — no type coercion (MCP SDK handles JSON parsing)
- frozen=True — immutable after construction (security-critical for HMAC)

Contract reference: docs/references/context-injection-contract.md
"""

from typing import Any, Literal

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


# --- TurnPacket output models (Call 1 response nested types) ---


class Entity(ProtocolModel):
    """An extracted entity from focus or context text."""

    id: str
    type: Literal[
        "file_loc", "file_path", "file_name", "symbol",
        "dir_path", "env_var", "config_key", "cli_flag", "command", "package_name",
        "file_hint", "symbol_hint", "config_hint",
    ]
    tier: Literal[1, 2]
    raw: str
    canonical: str
    confidence: Literal["high", "medium", "low"]
    source_type: Literal["claim", "unresolved"]
    in_focus: bool
    resolved_to: str | None


class PathDecision(ProtocolModel):
    """Result of path checking for a Tier 1 entity."""

    entity_id: str
    status: Literal["allowed", "denied", "not_tracked", "unresolved"]
    user_rel: str
    resolved_rel: str | None
    risk_signal: bool
    deny_reason: str | None
    candidates: list[str] | None
    unresolved_reason: Literal["zero_candidates", "multiple_candidates", "timeout"] | None


class Budget(ProtocolModel):
    """Current budget state."""

    evidence_count: int
    evidence_remaining: int
    scout_available: bool


class DedupRecord(ProtocolModel):
    """Record of a deduped entity/template combination.

    Invariant: template_already_used requires template_id; entity_already_scouted forbids it.
    Note: model_validator import is added in Task 5; this validator is added then.
    """

    entity_key: str
    template_id: Literal[
        "clarify.file_path", "clarify.symbol",
        "probe.file_repo_fact", "probe.symbol_repo_fact",
    ] | None = None
    reason: Literal["entity_already_scouted", "template_already_used"]
    prior_turn: int

    # Added in Task 5 (when model_validator is imported):
    # @model_validator(mode="after")
    # def _check_template_id_consistency(self) -> "DedupRecord":
    #     if self.reason == "template_already_used" and self.template_id is None:
    #         raise ValueError("template_already_used requires template_id")
    #     if self.reason == "entity_already_scouted" and self.template_id is not None:
    #         raise ValueError("entity_already_scouted must not have template_id")
    #     return self


class Clarifier(ProtocolModel):
    """Pre-built clarification question for clarifier templates."""

    question: str
    choices: list[str] | None


class TemplateCandidate(ProtocolModel):
    """A ranked template candidate in the TurnPacket response.

    scout_options uses a forward reference resolved in Task 5.
    For now, typed as list[dict] — will be updated to list[ScoutOption].
    """

    id: str
    template_id: Literal[
        "clarify.file_path", "clarify.symbol",
        "probe.file_repo_fact", "probe.symbol_repo_fact",
    ]
    entity_id: str
    focus_affinity: bool
    rank: int
    rank_factors: str
    scout_options: list[Any]  # Placeholder — updated to list[ReadOption | GrepOption] in Task 5. Uses Any to avoid strict-mode test fragility.
    clarifier: Clarifier | None
