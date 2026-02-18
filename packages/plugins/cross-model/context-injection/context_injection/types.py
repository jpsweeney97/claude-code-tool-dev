"""Pydantic protocol models for the context injection contract.

All models inherit from ProtocolModel:
- extra="forbid" — rejects unknown fields (catches contract drift)
- strict=True — no type coercion (MCP SDK handles JSON parsing)
- frozen=True — immutable after construction (security-critical for HMAC)

Contract reference: docs/references/context-injection-contract.md
"""

from typing import Annotated, Any, Literal, Union

from pydantic import Discriminator, Field, Tag, model_validator

from context_injection.base_types import Claim, ProtocolModel, Unresolved
from context_injection.ledger import (
    CumulativeState,
    LedgerEntry,
    LedgerEntryCounters,  # re-exported for test convenience
    ValidationWarning,
)


SchemaVersionLiteral = Literal["0.2.0"]

SCHEMA_VERSION: SchemaVersionLiteral = "0.2.0"
"""Single-point version control. 0.x uses exact-match semantics."""


# --- TurnRequest input models (Call 1 input) ---


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
    posture: Literal["adversarial", "collaborative", "exploratory", "evaluative"]

    # --- 0.2.0: Ledger fields (top-level for validation) ---
    position: str
    claims: list[Claim]
    delta: Literal["advancing", "shifting", "static"]
    tags: list[str]
    unresolved: list[Unresolved]

    # --- 0.2.0: Checkpoint fields (optional — absent on turn 1) ---
    state_checkpoint: str | None = None
    checkpoint_id: str | None = None


# --- TurnPacket output models (Call 1 response nested types) ---


class Entity(ProtocolModel):
    """An extracted entity from focus or context text."""

    id: str
    type: Literal[
        "file_loc",
        "file_path",
        "file_name",
        "symbol",
        "dir_path",
        "env_var",
        "config_key",
        "cli_flag",
        "command",
        "package_name",
        "file_hint",
        "symbol_hint",
        "config_hint",
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
    unresolved_reason: (
        Literal["zero_candidates", "multiple_candidates", "timeout"] | None
    )


class Budget(ProtocolModel):
    """Current budget state."""

    evidence_count: int
    evidence_remaining: int
    scout_available: bool
    budget_status: Literal["under_budget", "at_budget"]


class DedupRecord(ProtocolModel):
    """Record of a deduped entity/template combination.

    Invariant: template_already_used requires template_id; entity_already_scouted forbids it.
    """

    entity_key: str
    template_id: (
        Literal[
            "clarify.file_path",
            "clarify.symbol",
            "probe.file_repo_fact",
            "probe.symbol_repo_fact",
        ]
        | None
    ) = None
    reason: Literal["entity_already_scouted", "template_already_used"]
    prior_turn: int

    @model_validator(mode="after")
    def _check_template_id_consistency(self) -> "DedupRecord":
        if self.reason == "template_already_used" and self.template_id is None:
            raise ValueError("template_already_used requires template_id")
        if self.reason == "entity_already_scouted" and self.template_id is not None:
            raise ValueError("entity_already_scouted must not have template_id")
        return self


class Clarifier(ProtocolModel):
    """Pre-built clarification question for clarifier templates."""

    question: str
    choices: list[str] | None


# --- ScoutSpec: HMAC-signed execution spec (ReadSpec | GrepSpec) ---


class ReadSpec(ProtocolModel):
    """Execution spec for a file read scout."""

    action: Literal["read"]
    resolved_path: str
    strategy: Literal["first_n", "centered"]
    max_lines: int
    max_chars: int
    center_line: int | None = None


class GrepSpec(ProtocolModel):
    """Execution spec for a grep scout."""

    action: Literal["grep"]
    pattern: str
    strategy: Literal["match_context"]
    max_lines: int
    max_chars: int
    context_lines: int
    max_ranges: int


ScoutSpec = Annotated[
    Union[
        Annotated[ReadSpec, Tag("read")],
        Annotated[GrepSpec, Tag("grep")],
    ],
    Discriminator("action"),
]


# --- ScoutOption: what the agent sees (ReadOption | GrepOption) ---


class ReadOption(ProtocolModel):
    """Scout option for a file read."""

    id: str
    scout_token: str
    action: Literal["read"]
    target_display: str
    strategy: Literal["first_n", "centered"]
    max_lines: int
    max_chars: int
    risk_signal: bool
    center_line: int | None = None


class GrepOption(ProtocolModel):
    """Scout option for a grep."""

    id: str
    scout_token: str
    action: Literal["grep"]
    target_display: str
    strategy: Literal["match_context"]
    max_lines: int
    max_chars: int
    context_lines: int
    max_ranges: int


ScoutOption = Annotated[
    Union[
        Annotated[ReadOption, Tag("read")],
        Annotated[GrepOption, Tag("grep")],
    ],
    Discriminator("action"),
]


class TemplateCandidate(ProtocolModel):
    """A ranked template candidate in the TurnPacket response."""

    id: str
    template_id: Literal[
        "clarify.file_path",
        "clarify.symbol",
        "probe.file_repo_fact",
        "probe.symbol_repo_fact",
    ]
    entity_id: str
    focus_affinity: bool
    rank: int
    rank_factors: str
    scout_options: list[ReadOption | GrepOption]
    clarifier: Clarifier | None


# --- ScoutRequest (Call 2 input) ---


class ScoutRequest(ProtocolModel):
    """Call 2 input: agent sends scout_option_id + scout_token."""

    schema_version: SchemaVersionLiteral
    scout_option_id: str
    scout_token: str
    turn_request_ref: str


# --- TurnPacket: Call 1 response (Success | Error) ---


class ErrorDetail(ProtocolModel):
    """Error details in a TurnPacket error response."""

    code: Literal[
        "invalid_schema_version",
        "missing_required_field",
        "malformed_json",
        "internal_error",
        "ledger_hard_reject",
        "checkpoint_missing",
        "checkpoint_invalid",
        "checkpoint_stale",
        "turn_cap_exceeded",
    ]
    message: str
    details: dict | None = None


class TurnPacketSuccess(ProtocolModel):
    """Successful TurnPacket response."""

    schema_version: SchemaVersionLiteral
    status: Literal["success"]
    entities: list[Entity]
    path_decisions: list[PathDecision]
    template_candidates: list[TemplateCandidate]
    budget: Budget
    deduped: list[DedupRecord]

    # --- 0.2.0: Ledger validation results ---
    validated_entry: LedgerEntry
    warnings: list[ValidationWarning]
    cumulative: CumulativeState

    # --- 0.2.0: Conversation control ---
    action: Literal["continue_dialogue", "closing_probe", "conclude"]
    action_reason: str
    ledger_summary: str

    # --- 0.2.0: Checkpoint ---
    state_checkpoint: str
    checkpoint_id: str


class TurnPacketError(ProtocolModel):
    """Error TurnPacket response."""

    schema_version: SchemaVersionLiteral
    status: Literal["error"]
    error: ErrorDetail


TurnPacket = Annotated[
    Union[
        Annotated[TurnPacketSuccess, Tag("success")],
        Annotated[TurnPacketError, Tag("error")],
    ],
    Discriminator("status"),
]


# --- ScoutResult: Call 2 response (Success | Failure | Invalid) ---


class ReadResult(ProtocolModel):
    """Read-specific result fields."""

    path_display: str
    excerpt: str
    excerpt_range: Annotated[list[int], Field(min_length=2, max_length=2)] | None
    """[start_line, end_line] or None for PEM suppression / zero-content. Uses list (not tuple) because strict=True blocks list->tuple coercion from JSON arrays."""
    total_lines: int


class GrepMatch(ProtocolModel):
    """Per-file match details in a grep result."""

    path_display: str
    total_lines: int
    ranges: list[Annotated[list[int], Field(min_length=2, max_length=2)]]
    """Each range is [start_line, end_line]. Uses list (not tuple) for the same strict coercion reason."""


class GrepResult(ProtocolModel):
    """Grep-specific result fields."""

    excerpt: str
    match_count: int
    matches: list[GrepMatch]


class ScoutResultSuccess(ProtocolModel):
    """Successful scout result. Exactly one of read_result/grep_result is non-None."""

    schema_version: SchemaVersionLiteral
    scout_option_id: str
    status: Literal["success"]
    template_id: Literal[
        "clarify.file_path",
        "clarify.symbol",
        "probe.file_repo_fact",
        "probe.symbol_repo_fact",
    ]
    entity_id: str
    entity_key: str
    action: Literal["read", "grep"]
    read_result: ReadResult | None = None
    grep_result: GrepResult | None = None
    truncated: bool
    truncation_reason: Literal["max_lines", "max_chars", "max_ranges"] | None
    redactions_applied: int
    risk_signal: bool
    evidence_wrapper: str
    budget: Budget

    @model_validator(mode="after")
    def _check_result_matches_action(self) -> "ScoutResultSuccess":
        if self.action == "read" and self.read_result is None:
            raise ValueError("read action requires read_result")
        if self.action == "grep" and self.grep_result is None:
            raise ValueError("grep action requires grep_result")
        if self.action == "read" and self.grep_result is not None:
            raise ValueError("read action must not have grep_result")
        if self.action == "grep" and self.read_result is not None:
            raise ValueError("grep action must not have read_result")
        return self


ScoutFailureStatus = Literal["not_found", "denied", "binary", "decode_error", "timeout"]
"""Valid status values for ScoutResultFailure."""


class ScoutResultFailure(ProtocolModel):
    """Non-evidence failure (not_found, denied, binary, decode_error, timeout)."""

    schema_version: SchemaVersionLiteral
    scout_option_id: str
    status: ScoutFailureStatus
    template_id: Literal[
        "clarify.file_path",
        "clarify.symbol",
        "probe.file_repo_fact",
        "probe.symbol_repo_fact",
    ]
    entity_id: str
    entity_key: str
    action: Literal["read", "grep"]
    error_message: str
    budget: Budget


class ScoutResultInvalid(ProtocolModel):
    """Invalid request (token invalid, state lost)."""

    schema_version: SchemaVersionLiteral
    scout_option_id: str
    status: Literal["invalid_request"]
    error_message: str
    budget: None


def _scout_result_discriminator(v: Any) -> str:
    """Map multi-value failure statuses to a single 'failure' tag.

    Avoids fragile multi-tag-same-type pattern. Codex review B3.
    """
    status = v.get("status") if isinstance(v, dict) else v.status
    if status == "success":
        return "success"
    elif status == "invalid_request":
        return "invalid_request"
    else:
        return "failure"


ScoutResult = Annotated[
    Union[
        Annotated[ScoutResultSuccess, Tag("success")],
        Annotated[ScoutResultFailure, Tag("failure")],
        Annotated[ScoutResultInvalid, Tag("invalid_request")],
    ],
    Discriminator(_scout_result_discriminator),
]
