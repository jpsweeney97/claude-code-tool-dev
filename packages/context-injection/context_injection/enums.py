"""Protocol enum types for the context injection contract.

All values match the contract at docs/references/context-injection-contract.md.
"""

from enum import StrEnum


class EntityType(StrEnum):
    """Entity types extracted from dialogue text. Contract: EntityType enum."""

    # Tier 1 — MVP (scoutable, have matching templates)
    FILE_LOC = "file_loc"
    FILE_PATH = "file_path"
    FILE_NAME = "file_name"
    SYMBOL = "symbol"
    # Tier 1 — Post-MVP (extracted but not scoutable)
    DIR_PATH = "dir_path"
    ENV_VAR = "env_var"
    CONFIG_KEY = "config_key"
    CLI_FLAG = "cli_flag"
    COMMAND = "command"
    PACKAGE_NAME = "package_name"
    # Tier 2 (clarifier-routing only)
    FILE_HINT = "file_hint"
    SYMBOL_HINT = "symbol_hint"
    CONFIG_HINT = "config_hint"


class Confidence(StrEnum):
    """Extraction confidence. Only high/medium are scout-eligible."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ClaimStatus(StrEnum):
    """Ledger status of a claim."""

    NEW = "new"
    REINFORCED = "reinforced"
    REVISED = "revised"
    CONCEDED = "conceded"


class Posture(StrEnum):
    """Conversation posture. Reserved for template ranking adjustments."""

    ADVERSARIAL = "adversarial"
    COLLABORATIVE = "collaborative"
    EXPLORATORY = "exploratory"
    EVALUATIVE = "evaluative"


class PathStatus(StrEnum):
    """Result of path checking (canonicalization + denylist + git ls-files)."""

    ALLOWED = "allowed"
    DENIED = "denied"
    NOT_TRACKED = "not_tracked"
    UNRESOLVED = "unresolved"


class UnresolvedReason(StrEnum):
    """Why a file_name entity could not be resolved to a file_path."""

    ZERO_CANDIDATES = "zero_candidates"
    MULTIPLE_CANDIDATES = "multiple_candidates"
    TIMEOUT = "timeout"


class TemplateId(StrEnum):
    """MVP template identifiers."""

    CLARIFY_FILE_PATH = "clarify.file_path"
    CLARIFY_SYMBOL = "clarify.symbol"
    PROBE_FILE_REPO_FACT = "probe.file_repo_fact"
    PROBE_SYMBOL_REPO_FACT = "probe.symbol_repo_fact"


class ScoutAction(StrEnum):
    """Scout execution action."""

    READ = "read"
    GREP = "grep"


class ExcerptStrategy(StrEnum):
    """Excerpt selection strategy."""

    CENTERED = "centered"
    FIRST_N = "first_n"
    MATCH_CONTEXT = "match_context"


class ScoutStatus(StrEnum):
    """Scout result status."""

    SUCCESS = "success"
    NOT_FOUND = "not_found"
    DENIED = "denied"
    BINARY = "binary"
    DECODE_ERROR = "decode_error"
    TIMEOUT = "timeout"
    INVALID_REQUEST = "invalid_request"


class ErrorCode(StrEnum):
    """TurnPacket error codes."""

    INVALID_SCHEMA_VERSION = "invalid_schema_version"
    MISSING_REQUIRED_FIELD = "missing_required_field"
    MALFORMED_JSON = "malformed_json"
    INTERNAL_ERROR = "internal_error"


class TruncationReason(StrEnum):
    """Which cap triggered excerpt truncation."""

    MAX_LINES = "max_lines"
    MAX_CHARS = "max_chars"
    MAX_RANGES = "max_ranges"


class EffectiveDelta(StrEnum):
    """Server-computed effective delta for a ledger entry."""

    ADVANCING = "advancing"
    SHIFTING = "shifting"
    STATIC = "static"


class QualityLabel(StrEnum):
    """Server-computed quality label for a ledger entry."""

    SUBSTANTIVE = "substantive"
    SHALLOW = "shallow"


class ValidationTier(StrEnum):
    """Validation warning severity tier."""

    HARD_REJECT = "hard_reject"
    SOFT_WARN = "soft_warn"
    REFERENTIAL_WARN = "referential_warn"
