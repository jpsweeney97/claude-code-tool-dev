# Context Injection v0a Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the v0a context injection MCP server — full Call 1 pipeline (TurnRequest → TurnPacket) with entity extraction, path checking, template matching, scout option synthesis, and HMAC token generation. No file I/O (Call 2 is v0b).

**Architecture:** Python MCP server using the `mcp` SDK's `MCPServer` class (stdio transport). Pydantic v2 models with strict validation, discriminated unions, and frozen immutability. HMAC tokens bind scout options to stored execution specs. All state is in-memory (per-process lifetime).

**Tech Stack:** Python 3.11+, `mcp` SDK (includes Pydantic >= 2.12.0), `uv` for package management, `pytest` for testing, `ruff` for linting.

**SDK note:** The handoff references `FastMCP` — the SDK has since renamed this to `MCPServer`. Import: `from mcp.server.mcpserver import MCPServer, Context`. Lifespan context access: `ctx.request_context.lifespan_context`.

**Codex Review Amendments (2026-02-12):** This plan was reviewed by Codex (5-turn adversarial dialogue). Three blocking issues and five non-blocking concerns were incorporated inline. Key changes:
- **B1:** Added SDK smoke-test step in Task 12 (before wiring the full server)
- **B2:** Changed `tuple[int, int]` → `Annotated[list[int], Field(min_length=2, max_length=2)]` in ReadResult/GrepMatch (strict mode blocks list→tuple coercion)
- **B3:** Replaced multi-tag ScoutResult union with callable discriminator (3 tags instead of 7)
- **NB1:** Fixed dependency graph — Task 9 depends on Task 7 (entities.py imports AppContext from state.py)
- **NB2:** Bumped `requires-python` to `>=3.11` (StrEnum requires 3.11+)
- **NB5:** Added `model_validator` to DedupRecord for conditional `template_id` enforcement
- Added test coverage items for resolved-key dedupe, risk-signal cap halving, budget floor invariant

**Reference documents:**
- Contract: `docs/references/context-injection-contract.md` (925 lines)
- Design plan: `docs/plans/2026-02-11-conversation-aware-context-injection.md` (867 lines)
- Python MCP SDK source: `python-sdk-git/` (local clone)
- Handoff: `.archive/2026-02-12_00-18_pydantic-architecture-and-sdk-integration-resolved.md`

---

## Task 1: Project Scaffolding

**Files:**
- Create: `packages/context-injection/pyproject.toml`
- Create: `packages/context-injection/context_injection/__init__.py`
- Create: `packages/context-injection/context_injection/__main__.py`
- Create: `packages/context-injection/tests/__init__.py`
- Create: `packages/context-injection/tests/conftest.py`

**Step 1: Create package directory structure**

```bash
mkdir -p packages/context-injection/context_injection
mkdir -p packages/context-injection/tests
```

**Step 2: Write pyproject.toml**

```toml
[project]
name = "context-injection"
version = "0.1.0"
description = "Context injection MCP server for the codex-dialogue agent"
requires-python = ">=3.11"
dependencies = [
    "mcp>=1.9.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "ruff>=0.8",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**Step 3: Write `__init__.py`**

```python
"""Context injection MCP server for the codex-dialogue agent."""
```

**Step 4: Write `__main__.py`**

```python
"""Entry point: python -m context_injection.server"""

from context_injection.server import main

main()
```

Note: `server.py` doesn't exist yet. This file will error until Task 10. That's fine — scaffolding is ahead of implementation.

**Step 5: Write `tests/__init__.py`** (empty) and `tests/conftest.py`**

```python
"""Shared test fixtures for context-injection tests."""
```

**Step 6: Install the package in dev mode**

Run: `cd packages/context-injection && uv sync --dev`

**Step 7: Verify import works**

Run: `cd packages/context-injection && uv run python -c "import context_injection; print('OK')"`
Expected: `OK`

**Step 8: Commit**

```bash
git add packages/context-injection/
git commit -m "feat(context-injection): scaffold Python MCP server package"
```

---

## Task 2: Enums (`enums.py`)

**Files:**
- Create: `packages/context-injection/context_injection/enums.py`
- Create: `packages/context-injection/tests/test_enums.py`

**Context:** The contract defines 13 enum types. Use `StrEnum` (Python 3.11+ or `enum.StrEnum` backport via `__str__`). Each enum has specific values from the contract's Enums section.

**Step 1: Write the failing test**

```python
"""Tests for protocol enums."""

import pytest

from context_injection.enums import (
    ClaimStatus,
    Confidence,
    EntityType,
    ErrorCode,
    ExcerptStrategy,
    PathStatus,
    Posture,
    ScoutAction,
    ScoutStatus,
    TemplateId,
    TruncationReason,
    UnresolvedReason,
)


class TestEntityType:
    def test_mvp_tier1_types(self) -> None:
        assert EntityType.FILE_LOC == "file_loc"
        assert EntityType.FILE_PATH == "file_path"
        assert EntityType.FILE_NAME == "file_name"
        assert EntityType.SYMBOL == "symbol"

    def test_post_mvp_tier1_types(self) -> None:
        assert EntityType.DIR_PATH == "dir_path"
        assert EntityType.ENV_VAR == "env_var"
        assert EntityType.CONFIG_KEY == "config_key"
        assert EntityType.CLI_FLAG == "cli_flag"
        assert EntityType.COMMAND == "command"
        assert EntityType.PACKAGE_NAME == "package_name"

    def test_tier2_types(self) -> None:
        assert EntityType.FILE_HINT == "file_hint"
        assert EntityType.SYMBOL_HINT == "symbol_hint"
        assert EntityType.CONFIG_HINT == "config_hint"


class TestConfidence:
    def test_values(self) -> None:
        assert Confidence.HIGH == "high"
        assert Confidence.MEDIUM == "medium"
        assert Confidence.LOW == "low"


class TestClaimStatus:
    def test_values(self) -> None:
        assert ClaimStatus.NEW == "new"
        assert ClaimStatus.REINFORCED == "reinforced"
        assert ClaimStatus.REVISED == "revised"
        assert ClaimStatus.CONCEDED == "conceded"


class TestPosture:
    def test_values(self) -> None:
        assert Posture.ADVERSARIAL == "adversarial"
        assert Posture.COLLABORATIVE == "collaborative"
        assert Posture.EXPLORATORY == "exploratory"
        assert Posture.EVALUATIVE == "evaluative"


class TestPathStatus:
    def test_values(self) -> None:
        assert PathStatus.ALLOWED == "allowed"
        assert PathStatus.DENIED == "denied"
        assert PathStatus.NOT_TRACKED == "not_tracked"
        assert PathStatus.UNRESOLVED == "unresolved"


class TestUnresolvedReason:
    def test_values(self) -> None:
        assert UnresolvedReason.ZERO_CANDIDATES == "zero_candidates"
        assert UnresolvedReason.MULTIPLE_CANDIDATES == "multiple_candidates"
        assert UnresolvedReason.TIMEOUT == "timeout"


class TestTemplateId:
    def test_values(self) -> None:
        assert TemplateId.CLARIFY_FILE_PATH == "clarify.file_path"
        assert TemplateId.CLARIFY_SYMBOL == "clarify.symbol"
        assert TemplateId.PROBE_FILE_REPO_FACT == "probe.file_repo_fact"
        assert TemplateId.PROBE_SYMBOL_REPO_FACT == "probe.symbol_repo_fact"


class TestScoutAction:
    def test_values(self) -> None:
        assert ScoutAction.READ == "read"
        assert ScoutAction.GREP == "grep"


class TestExcerptStrategy:
    def test_values(self) -> None:
        assert ExcerptStrategy.CENTERED == "centered"
        assert ExcerptStrategy.FIRST_N == "first_n"
        assert ExcerptStrategy.MATCH_CONTEXT == "match_context"


class TestScoutStatus:
    def test_values(self) -> None:
        assert ScoutStatus.SUCCESS == "success"
        assert ScoutStatus.NOT_FOUND == "not_found"
        assert ScoutStatus.DENIED == "denied"
        assert ScoutStatus.BINARY == "binary"
        assert ScoutStatus.DECODE_ERROR == "decode_error"
        assert ScoutStatus.TIMEOUT == "timeout"
        assert ScoutStatus.INVALID_REQUEST == "invalid_request"


class TestErrorCode:
    def test_values(self) -> None:
        assert ErrorCode.INVALID_SCHEMA_VERSION == "invalid_schema_version"
        assert ErrorCode.MISSING_REQUIRED_FIELD == "missing_required_field"
        assert ErrorCode.MALFORMED_JSON == "malformed_json"
        assert ErrorCode.INTERNAL_ERROR == "internal_error"


class TestTruncationReason:
    def test_values(self) -> None:
        assert TruncationReason.MAX_LINES == "max_lines"
        assert TruncationReason.MAX_CHARS == "max_chars"
        assert TruncationReason.MAX_RANGES == "max_ranges"


def test_all_enums_are_str_subclass() -> None:
    """Every enum member must serialize to its string value."""
    for enum_cls in [
        EntityType, Confidence, ClaimStatus, Posture, PathStatus,
        UnresolvedReason, TemplateId, ScoutAction, ExcerptStrategy,
        ScoutStatus, ErrorCode, TruncationReason,
    ]:
        for member in enum_cls:
            assert isinstance(member, str)
            assert str(member) == member.value
```

**Step 2: Run test to verify it fails**

Run: `cd packages/context-injection && uv run pytest tests/test_enums.py -v`
Expected: FAIL (ImportError — module doesn't exist)

**Step 3: Write the implementation**

```python
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
```

Note: `StrEnum` requires Python 3.11+. The `requires-python` is set to `>=3.11` so this is safe.

**Step 4: Run test to verify it passes**

Run: `cd packages/context-injection && uv run pytest tests/test_enums.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add packages/context-injection/context_injection/enums.py packages/context-injection/tests/test_enums.py
git commit -m "feat(context-injection): add protocol enum types"
```

---

## Task 3: ProtocolModel Base + Input Models (`types.py` part 1)

**Files:**
- Create: `packages/context-injection/context_injection/types.py`
- Create: `packages/context-injection/tests/test_types.py`

**Context:** All protocol types inherit from `ProtocolModel` with `extra="forbid"`, `strict=True`, `frozen=True`. This task covers the base class and the TurnRequest input models (Claim, Unresolved, Focus, EvidenceRecord, TurnRequest). These are the simplest models — no discriminated unions.

The contract defines `SCHEMA_VERSION = "0.1.0"` with exact-match semantics for 0.x.

**Step 1: Write the failing test**

```python
"""Tests for protocol Pydantic models."""

import pytest
from pydantic import ValidationError

from context_injection.types import (
    SCHEMA_VERSION,
    Claim,
    EvidenceRecord,
    Focus,
    ProtocolModel,
    TurnRequest,
    Unresolved,
)


class TestProtocolModel:
    """ProtocolModel base enforces extra=forbid, strict=True, frozen=True."""

    def test_rejects_extra_fields(self) -> None:
        with pytest.raises(ValidationError, match="extra_forbidden"):
            Claim(text="test", status="new", turn=1, bogus="field")

    def test_rejects_type_coercion(self) -> None:
        """strict=True means string '1' is not coerced to int."""
        with pytest.raises(ValidationError):
            Claim(text="test", status="new", turn="1")  # type: ignore[arg-type]

    def test_frozen_immutability(self) -> None:
        claim = Claim(text="test", status="new", turn=1)
        with pytest.raises(ValidationError):
            claim.text = "modified"  # type: ignore[misc]


class TestClaim:
    def test_valid_claim(self) -> None:
        c = Claim(text="The project uses YAML", status="new", turn=3)
        assert c.text == "The project uses YAML"
        assert c.status == "new"
        assert c.turn == 3

    def test_all_statuses(self) -> None:
        for status in ("new", "reinforced", "revised", "conceded"):
            c = Claim(text="claim", status=status, turn=1)
            assert c.status == status


class TestFocus:
    def test_valid_focus(self) -> None:
        f = Focus(
            text="Config format question",
            claims=[Claim(text="Uses YAML", status="new", turn=1)],
            unresolved=[Unresolved(text="Are there overrides?", turn=1)],
        )
        assert len(f.claims) == 1
        assert len(f.unresolved) == 1

    def test_empty_claims_and_unresolved(self) -> None:
        f = Focus(text="Empty focus", claims=[], unresolved=[])
        assert f.claims == []
        assert f.unresolved == []


class TestTurnRequest:
    def test_parse_contract_example(self) -> None:
        """Parse the exact JSON from the contract's Call 1 example."""
        data = {
            "schema_version": SCHEMA_VERSION,
            "turn_number": 3,
            "conversation_id": "conv_abc123",
            "focus": {
                "text": "Whether the project uses YAML or TOML for configuration",
                "claims": [
                    {
                        "text": "The project uses `src/config/settings.yaml` for all configuration",
                        "status": "new",
                        "turn": 3,
                    },
                    {
                        "text": "YAML was chosen over TOML for readability",
                        "status": "new",
                        "turn": 3,
                    },
                ],
                "unresolved": [
                    {
                        "text": "Whether `config.yaml` is the only config file or if there are environment overrides",
                        "turn": 3,
                    }
                ],
            },
            "context_claims": [
                {
                    "text": "The project follows a monorepo structure with `packages/` subdirectories",
                    "status": "reinforced",
                    "turn": 1,
                }
            ],
            "evidence_history": [
                {
                    "entity_key": "file_path:src/config/loader.py",
                    "template_id": "probe.file_repo_fact",
                    "turn": 1,
                }
            ],
            "posture": "evaluative",
        }
        req = TurnRequest.model_validate(data)
        assert req.turn_number == 3
        assert req.conversation_id == "conv_abc123"
        assert len(req.focus.claims) == 2
        assert len(req.evidence_history) == 1
        assert req.posture == "evaluative"

    def test_wrong_schema_version_rejected(self) -> None:
        """Pydantic strict Literal rejects wrong version."""
        data = {
            "schema_version": "0.2.0",
            "turn_number": 1,
            "conversation_id": "conv_1",
            "focus": {"text": "test", "claims": [], "unresolved": []},
            "evidence_history": [],
            "posture": "exploratory",
        }
        with pytest.raises(ValidationError):
            TurnRequest.model_validate(data)

    def test_optional_context_claims(self) -> None:
        """context_claims is optional and defaults to empty."""
        data = {
            "schema_version": SCHEMA_VERSION,
            "turn_number": 1,
            "conversation_id": "conv_1",
            "focus": {"text": "test", "claims": [], "unresolved": []},
            "evidence_history": [],
            "posture": "exploratory",
        }
        req = TurnRequest.model_validate(data)
        assert req.context_claims == []
```

**Step 2: Run test to verify it fails**

Run: `cd packages/context-injection && uv run pytest tests/test_types.py -v`
Expected: FAIL (ImportError)

**Step 3: Write the implementation**

```python
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
```

Design note: Use `Literal[...]` for discriminator-like fields (status, posture, template_id) rather than StrEnum, per the D7 decision. StrEnum types in `enums.py` are for non-discriminator contexts (iteration, validation logic, documentation).

**Step 4: Run test to verify it passes**

Run: `cd packages/context-injection && uv run pytest tests/test_types.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add packages/context-injection/context_injection/types.py packages/context-injection/tests/test_types.py
git commit -m "feat(context-injection): add ProtocolModel base and TurnRequest input models"
```

---

## Task 4: Output Models — Entity, PathDecision, Budget, Dedup, Clarifier, TemplateCandidate (`types.py` part 2)

**Files:**
- Modify: `packages/context-injection/context_injection/types.py`
- Modify: `packages/context-injection/tests/test_types.py`

**Context:** These are the TurnPacket's nested output models. Still no discriminated unions — those come in Task 5.

**Step 1: Add failing tests for output models**

Add to `tests/test_types.py`:

```python
from context_injection.types import (
    Budget,
    Clarifier,
    DedupRecord,
    Entity,
    PathDecision,
    TemplateCandidate,
)


class TestEntity:
    def test_parse_file_path_entity(self) -> None:
        e = Entity(
            id="e_005",
            type="file_path",
            tier=1,
            raw="src/config/settings.yaml",
            canonical="src/config/settings.yaml",
            confidence="high",
            source_type="claim",
            in_focus=True,
            resolved_to=None,
        )
        assert e.type == "file_path"
        assert e.in_focus is True
        assert e.resolved_to is None

    def test_parse_file_name_with_resolution(self) -> None:
        e = Entity(
            id="e_006",
            type="file_name",
            tier=1,
            raw="config.yaml",
            canonical="config.yaml",
            confidence="high",
            source_type="unresolved",
            in_focus=True,
            resolved_to="e_008",
        )
        assert e.resolved_to == "e_008"


class TestPathDecision:
    def test_allowed_path(self) -> None:
        pd = PathDecision(
            entity_id="e_005",
            status="allowed",
            user_rel="src/config/settings.yaml",
            resolved_rel="src/config/settings.yaml",
            risk_signal=False,
            deny_reason=None,
            candidates=None,
            unresolved_reason=None,
        )
        assert pd.status == "allowed"
        assert pd.resolved_rel == "src/config/settings.yaml"

    def test_unresolved_with_candidates(self) -> None:
        pd = PathDecision(
            entity_id="e_010",
            status="unresolved",
            user_rel="config.yaml",
            resolved_rel=None,
            risk_signal=False,
            deny_reason=None,
            candidates=["src/config.yaml", "lib/config.yaml"],
            unresolved_reason="multiple_candidates",
        )
        assert pd.candidates == ["src/config.yaml", "lib/config.yaml"]
        assert pd.unresolved_reason == "multiple_candidates"


class TestBudget:
    def test_budget(self) -> None:
        b = Budget(evidence_count=1, evidence_remaining=4, scout_available=True)
        assert b.evidence_remaining == 4


class TestTemplateCandidate:
    def test_probe_candidate_with_scout_option(self) -> None:
        tc = TemplateCandidate(
            id="tc_001",
            template_id="probe.file_repo_fact",
            entity_id="e_005",
            focus_affinity=True,
            rank=1,
            rank_factors="file_path > file_name; high confidence",
            scout_options=[],  # Scout options tested separately in Task 5
            clarifier=None,
        )
        assert tc.rank == 1

    def test_clarifier_candidate(self) -> None:
        tc = TemplateCandidate(
            id="tc_003",
            template_id="clarify.file_path",
            entity_id="e_007",
            focus_affinity=False,
            rank=3,
            rank_factors="Tier 2 entity",
            scout_options=[],
            clarifier=Clarifier(
                question="Which file is 'the auth module'?",
                choices=["src/auth/middleware.py", "src/auth/handler.py"],
            ),
        )
        assert tc.clarifier is not None
        assert len(tc.clarifier.choices) == 2
```

**Step 2: Run test to verify it fails**

Run: `cd packages/context-injection && uv run pytest tests/test_types.py -v -k "TestEntity or TestPathDecision or TestBudget or TestTemplateCandidate"`
Expected: FAIL (ImportError — classes don't exist yet)

**Step 3: Add the models to `types.py`**

Append to `types.py`:

```python
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
```

**Step 4: Run test to verify it passes**

Run: `cd packages/context-injection && uv run pytest tests/test_types.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add packages/context-injection/context_injection/types.py packages/context-injection/tests/test_types.py
git commit -m "feat(context-injection): add Entity, PathDecision, Budget, TemplateCandidate models"
```

---

## Task 5: Discriminated Unions — ScoutSpec, ScoutOption, TurnPacket, ScoutResult (`types.py` part 3)

**Files:**
- Modify: `packages/context-injection/context_injection/types.py`
- Modify: `packages/context-injection/tests/test_types.py`

**Context:** This is the most architecturally significant task. Four discriminated unions per the D7/D10 architecture decisions. Uses `Literal["..."]` discriminator fields (not StrEnum) to avoid Pydantic v2 "conflicting reports" issues. ScoutResultSuccess uses a `@model_validator(mode="after")` for the read/grep result split.

Discriminated union table:
- `ScoutSpec = ReadSpec | GrepSpec` (on `action`)
- `ScoutOption = ReadOption | GrepOption` (on `action`)
- `TurnPacket = TurnPacketSuccess | TurnPacketError` (on `status`)
- `ScoutResult = ScoutResultSuccess | ScoutResultFailure | ScoutResultInvalid` (on `status`)

**Step 1: Write the failing tests**

Add to `tests/test_types.py`:

```python
from typing import Annotated, Union

from context_injection.types import (
    GrepOption,
    GrepSpec,
    ReadOption,
    ReadSpec,
    ReadResult,
    GrepResult,
    GrepMatch,
    ScoutOption,
    ScoutRequest,
    ScoutResult,
    ScoutResultFailure,
    ScoutResultInvalid,
    ScoutResultSuccess,
    ScoutSpec,
    TurnPacket,
    TurnPacketError,
    TurnPacketSuccess,
    ErrorDetail,
)


class TestScoutSpec:
    def test_read_spec_first_n(self) -> None:
        spec = ReadSpec(
            action="read",
            resolved_path="src/config/settings.yaml",
            strategy="first_n",
            max_lines=40,
            max_chars=2000,
        )
        assert spec.action == "read"
        assert spec.strategy == "first_n"
        assert spec.center_line is None

    def test_read_spec_centered(self) -> None:
        spec = ReadSpec(
            action="read",
            resolved_path="src/config/settings.yaml",
            strategy="centered",
            max_lines=40,
            max_chars=2000,
            center_line=42,
        )
        assert spec.center_line == 42

    def test_grep_spec(self) -> None:
        spec = GrepSpec(
            action="grep",
            pattern="load_config",
            strategy="match_context",
            max_lines=40,
            max_chars=2000,
            context_lines=2,
            max_ranges=5,
        )
        assert spec.action == "grep"
        assert spec.context_lines == 2

    def test_discriminated_union_parses_read(self) -> None:
        data = {
            "action": "read",
            "resolved_path": "src/app.py",
            "strategy": "first_n",
            "max_lines": 40,
            "max_chars": 2000,
        }
        from pydantic import TypeAdapter
        adapter = TypeAdapter(ScoutSpec)
        spec = adapter.validate_python(data)
        assert isinstance(spec, ReadSpec)

    def test_discriminated_union_parses_grep(self) -> None:
        data = {
            "action": "grep",
            "pattern": "main",
            "strategy": "match_context",
            "max_lines": 40,
            "max_chars": 2000,
            "context_lines": 2,
            "max_ranges": 5,
        }
        from pydantic import TypeAdapter
        adapter = TypeAdapter(ScoutSpec)
        spec = adapter.validate_python(data)
        assert isinstance(spec, GrepSpec)


class TestScoutOption:
    def test_read_option(self) -> None:
        opt = ReadOption(
            id="so_005",
            scout_token="hmac_a1b2c3d4e5f6",
            action="read",
            target_display="src/config/settings.yaml",
            strategy="first_n",
            max_lines=40,
            max_chars=2000,
            risk_signal=False,
        )
        assert opt.action == "read"
        assert opt.center_line is None

    def test_grep_option(self) -> None:
        opt = GrepOption(
            id="so_006",
            scout_token="hmac_f6e5d4c3b2a1",
            action="grep",
            target_display="load_config",
            strategy="match_context",
            max_lines=40,
            max_chars=2000,
            context_lines=2,
            max_ranges=5,
        )
        assert opt.action == "grep"
        assert opt.context_lines == 2


class TestTurnPacket:
    def test_success_packet(self) -> None:
        data = {
            "schema_version": "0.1.0",
            "status": "success",
            "entities": [],
            "path_decisions": [],
            "template_candidates": [],
            "budget": {"evidence_count": 0, "evidence_remaining": 5, "scout_available": True},
            "deduped": [],
        }
        from pydantic import TypeAdapter
        adapter = TypeAdapter(TurnPacket)
        packet = adapter.validate_python(data)
        assert isinstance(packet, TurnPacketSuccess)

    def test_error_packet(self) -> None:
        data = {
            "schema_version": "0.1.0",
            "status": "error",
            "error": {
                "code": "invalid_schema_version",
                "message": "Unsupported schema version",
                "details": None,
            },
        }
        from pydantic import TypeAdapter
        adapter = TypeAdapter(TurnPacket)
        packet = adapter.validate_python(data)
        assert isinstance(packet, TurnPacketError)


class TestScoutResult:
    def test_success_read_result(self) -> None:
        data = {
            "schema_version": "0.1.0",
            "scout_option_id": "so_005",
            "status": "success",
            "template_id": "probe.file_repo_fact",
            "entity_id": "e_005",
            "entity_key": "file_path:src/config/settings.yaml",
            "action": "read",
            "read_result": {
                "path_display": "src/config/settings.yaml",
                "excerpt": "port: 8080\nhost: 0.0.0.0",
                "excerpt_range": [1, 7],
                "total_lines": 42,
            },
            "grep_result": None,
            "truncated": False,
            "truncation_reason": None,
            "redactions_applied": 0,
            "risk_signal": False,
            "evidence_wrapper": "From `src/config/settings.yaml:1-7`",
            "budget": {"evidence_count": 2, "evidence_remaining": 3, "scout_available": False},
        }
        from pydantic import TypeAdapter
        adapter = TypeAdapter(ScoutResult)
        result = adapter.validate_python(data)
        assert isinstance(result, ScoutResultSuccess)
        assert result.read_result is not None
        assert result.grep_result is None

    def test_failure_not_found(self) -> None:
        data = {
            "schema_version": "0.1.0",
            "scout_option_id": "so_005",
            "status": "not_found",
            "template_id": "probe.file_repo_fact",
            "entity_id": "e_005",
            "entity_key": "file_path:src/config/settings.yaml",
            "action": "read",
            "error_message": "File not found",
            "budget": {"evidence_count": 1, "evidence_remaining": 4, "scout_available": False},
        }
        from pydantic import TypeAdapter
        adapter = TypeAdapter(ScoutResult)
        result = adapter.validate_python(data)
        assert isinstance(result, ScoutResultFailure)

    def test_invalid_request(self) -> None:
        data = {
            "schema_version": "0.1.0",
            "scout_option_id": "so_005",
            "status": "invalid_request",
            "error_message": "Scout token invalid",
            "budget": None,
        }
        from pydantic import TypeAdapter
        adapter = TypeAdapter(ScoutResult)
        result = adapter.validate_python(data)
        assert isinstance(result, ScoutResultInvalid)
        assert result.budget is None
```

**Step 2: Run test to verify it fails**

Run: `cd packages/context-injection && uv run pytest tests/test_types.py -v -k "TestScoutSpec or TestScoutOption or TestTurnPacket or TestScoutResult"`
Expected: FAIL (ImportError)

**Step 3: Write the discriminated union models**

Append to `types.py`:

```python
from typing import Any, Annotated, Union
from pydantic import Discriminator, Field, Tag, model_validator


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


ScoutSpec = Annotated[Union[
    Annotated[ReadSpec, Tag("read")],
    Annotated[GrepSpec, Tag("grep")],
], Discriminator("action")]


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


ScoutOption = Annotated[Union[
    Annotated[ReadOption, Tag("read")],
    Annotated[GrepOption, Tag("grep")],
], Discriminator("action")]


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
        "invalid_schema_version", "missing_required_field",
        "malformed_json", "internal_error",
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


class TurnPacketError(ProtocolModel):
    """Error TurnPacket response."""

    schema_version: SchemaVersionLiteral
    status: Literal["error"]
    error: ErrorDetail


TurnPacket = Annotated[Union[
    Annotated[TurnPacketSuccess, Tag("success")],
    Annotated[TurnPacketError, Tag("error")],
], Discriminator("status")]


# --- ScoutResult: Call 2 response (Success | Failure | Invalid) ---


class ReadResult(ProtocolModel):
    """Read-specific result fields."""

    path_display: str
    excerpt: str
    excerpt_range: Annotated[list[int], Field(min_length=2, max_length=2)]
    """[start_line, end_line]. Uses list (not tuple) because strict=True blocks list→tuple coercion from JSON arrays."""
    total_lines: int


class GrepMatch(ProtocolModel):
    """Per-file match details in a grep result."""

    path_display: str
    total_lines: int
    ranges: list[Annotated[list[int], Field(min_length=2, max_length=2)]]
    """Each range is [start_line, end_line]. Uses list (not tuple) — same strict coercion reason."""


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
        "clarify.file_path", "clarify.symbol",
        "probe.file_repo_fact", "probe.symbol_repo_fact",
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


class ScoutResultFailure(ProtocolModel):
    """Non-evidence failure (not_found, denied, binary, decode_error, timeout)."""

    schema_version: SchemaVersionLiteral
    scout_option_id: str
    status: Literal["not_found", "denied", "binary", "decode_error", "timeout"]
    template_id: Literal[
        "clarify.file_path", "clarify.symbol",
        "probe.file_repo_fact", "probe.symbol_repo_fact",
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


ScoutResult = Annotated[Union[
    Annotated[ScoutResultSuccess, Tag("success")],
    Annotated[ScoutResultFailure, Tag("failure")],
    Annotated[ScoutResultInvalid, Tag("invalid_request")],
], Discriminator(_scout_result_discriminator)]
```

Then update `TemplateCandidate.scout_options` from `list[Any]` to the proper union type:
```python
# In TemplateCandidate, change:
scout_options: list[ReadOption | GrepOption]
```

Also uncomment the `DedupRecord._check_template_id_consistency` model_validator (stubbed in Task 4) and add tests:
```python
# In DedupRecord, uncomment and activate:
@model_validator(mode="after")
def _check_template_id_consistency(self) -> "DedupRecord":
    if self.reason == "template_already_used" and self.template_id is None:
        raise ValueError("template_already_used requires template_id")
    if self.reason == "entity_already_scouted" and self.template_id is not None:
        raise ValueError("entity_already_scouted must not have template_id")
    return self
```

Add tests for the DedupRecord invariant:
```python
class TestDedupRecordInvariant:
    def test_template_already_used_requires_template_id(self) -> None:
        with pytest.raises(ValidationError, match="template_already_used requires template_id"):
            DedupRecord(
                entity_key="file_path:src/app.py",
                template_id=None,
                reason="template_already_used",
                prior_turn=1,
            )

    def test_entity_already_scouted_forbids_template_id(self) -> None:
        with pytest.raises(ValidationError, match="entity_already_scouted must not have template_id"):
            DedupRecord(
                entity_key="file_path:src/app.py",
                template_id="probe.file_repo_fact",
                reason="entity_already_scouted",
                prior_turn=1,
            )

    def test_valid_entity_already_scouted(self) -> None:
        d = DedupRecord(
            entity_key="file_path:src/app.py",
            template_id=None,
            reason="entity_already_scouted",
            prior_turn=1,
        )
        assert d.reason == "entity_already_scouted"

    def test_valid_template_already_used(self) -> None:
        d = DedupRecord(
            entity_key="file_path:src/app.py",
            template_id="probe.file_repo_fact",
            reason="template_already_used",
            prior_turn=1,
        )
        assert d.template_id == "probe.file_repo_fact"
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/context-injection && uv run pytest tests/test_types.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add packages/context-injection/
git commit -m "feat(context-injection): add discriminated unions — ScoutSpec, ScoutOption, TurnPacket, ScoutResult"
```

---

## Task 6: Canonical Serialization and Entity Keys (`canonical.py`)

**Files:**
- Create: `packages/context-injection/context_injection/canonical.py`
- Create: `packages/context-injection/tests/test_canonical.py`

**Context:** Two serialization functions with opposite `exclude_none` behavior. `canonical_json_bytes()` is the fail-closed HMAC payload serializer. `wire_dump()` is the protocol output serializer. Plus `make_entity_key()`/`parse_entity_key()` functions and the `ScoutTokenPayload` model.

**Step 1: Write failing tests**

```python
"""Tests for canonical serialization and entity key functions."""

import json

import pytest

from context_injection.canonical import (
    ScoutTokenPayload,
    canonical_json_bytes,
    make_entity_key,
    parse_entity_key,
    wire_dump,
)
from context_injection.types import ReadSpec, GrepSpec, Budget


class TestCanonicalJsonBytes:
    def test_read_spec_golden_vector(self) -> None:
        """Golden vector: ReadSpec with first_n strategy."""
        spec = ReadSpec(
            action="read",
            resolved_path="src/config/settings.yaml",
            strategy="first_n",
            max_lines=40,
            max_chars=2000,
        )
        payload = ScoutTokenPayload(
            v=1,
            conversation_id="conv_abc123",
            turn_number=3,
            scout_option_id="so_005",
            spec=spec,
        )
        result = canonical_json_bytes(payload)
        parsed = json.loads(result)
        # Verify deterministic key ordering
        assert list(parsed.keys()) == sorted(parsed.keys())
        # Verify no None values (center_line is None, should be excluded)
        assert "center_line" not in json.dumps(parsed)
        # Verify no whitespace
        assert b" " not in result
        assert b"\n" not in result

    def test_grep_spec_golden_vector(self) -> None:
        spec = GrepSpec(
            action="grep",
            pattern="load_config",
            strategy="match_context",
            max_lines=40,
            max_chars=2000,
            context_lines=2,
            max_ranges=5,
        )
        payload = ScoutTokenPayload(
            v=1,
            conversation_id="conv_1",
            turn_number=1,
            scout_option_id="so_001",
            spec=spec,
        )
        result = canonical_json_bytes(payload)
        parsed = json.loads(result)
        assert parsed["spec"]["action"] == "grep"
        assert parsed["spec"]["pattern"] == "load_config"

    def test_unicode_nfc_path(self) -> None:
        """Paths must be NFC-normalized before entering models."""
        # This test verifies the bytes are valid UTF-8
        spec = ReadSpec(
            action="read",
            resolved_path="src/caf\u00e9.py",  # NFC form
            strategy="first_n",
            max_lines=40,
            max_chars=2000,
        )
        payload = ScoutTokenPayload(
            v=1, conversation_id="c", turn_number=1,
            scout_option_id="so", spec=spec,
        )
        result = canonical_json_bytes(payload)
        assert "caf\u00e9".encode("utf-8") in result

    def test_deterministic_output(self) -> None:
        """Same input produces identical bytes."""
        spec = ReadSpec(
            action="read", resolved_path="a.py", strategy="first_n",
            max_lines=40, max_chars=2000,
        )
        payload = ScoutTokenPayload(
            v=1, conversation_id="c", turn_number=1,
            scout_option_id="so", spec=spec,
        )
        assert canonical_json_bytes(payload) == canonical_json_bytes(payload)


class TestWireDump:
    def test_includes_null_for_none(self) -> None:
        """Wire format includes explicit null for None values."""
        from context_injection.types import Entity
        e = Entity(
            id="e_001", type="file_path", tier=1, raw="a.py",
            canonical="a.py", confidence="high", source_type="claim",
            in_focus=True, resolved_to=None,
        )
        dumped = wire_dump(e)
        assert dumped["resolved_to"] is None
        assert "resolved_to" in dumped

    def test_budget_wire_dump(self) -> None:
        b = Budget(evidence_count=1, evidence_remaining=4, scout_available=True)
        dumped = wire_dump(b)
        assert dumped == {"evidence_count": 1, "evidence_remaining": 4, "scout_available": True}


class TestEntityKey:
    def test_roundtrip(self) -> None:
        key = make_entity_key("file_path", "src/config/settings.yaml")
        assert key == "file_path:src/config/settings.yaml"
        entity_type, canonical = parse_entity_key(key)
        assert entity_type == "file_path"
        assert canonical == "src/config/settings.yaml"

    def test_symbol_with_parens(self) -> None:
        key = make_entity_key("symbol", "load_config")
        assert key == "symbol:load_config"

    def test_parse_with_colon_in_value(self) -> None:
        """file_loc values contain colons (e.g., config.py:42)."""
        key = "file_loc:config.py:42"
        entity_type, canonical = parse_entity_key(key)
        assert entity_type == "file_loc"
        assert canonical == "config.py:42"
```

**Step 2: Run test to verify it fails**

Run: `cd packages/context-injection && uv run pytest tests/test_canonical.py -v`
Expected: FAIL (ImportError)

**Step 3: Write the implementation**

```python
"""Canonical serialization and entity key functions.

Two serialization policies:
- canonical_json_bytes(): HMAC payload — exclude None, sorted keys, compact
- wire_dump(): Protocol output — include null, for JSON serialization

Never call model_dump() ad hoc. Use these functions.

Contract reference: HMAC Token Specification section.
"""

import json
from typing import Any

from pydantic import BaseModel

from context_injection.types import ProtocolModel, ReadSpec, GrepSpec, ScoutSpec


class ScoutTokenPayload(ProtocolModel):
    """HMAC signing payload. Binds turn identity to execution spec.

    Not sent over the wire — used only for canonical_json_bytes() → HMAC signing.
    """

    v: int
    conversation_id: str
    turn_number: int
    scout_option_id: str
    spec: ReadSpec | GrepSpec


def canonical_json_bytes(payload: ScoutTokenPayload) -> bytes:
    """Serialize payload to canonical JSON bytes for HMAC signing.

    Rules (from contract):
    - json.dumps(separators=(",", ":"), sort_keys=True, ensure_ascii=False)
    - Encode as UTF-8
    - No None values (exclude_none=True)
    - No floats (ints only)
    - NFC-normalized Unicode (enforced before model construction, not here)
    """
    data = payload.model_dump(exclude_none=True)
    return json.dumps(
        data,
        separators=(",", ":"),
        sort_keys=True,
        ensure_ascii=False,
    ).encode("utf-8")


def wire_dump(model: BaseModel) -> dict[str, Any]:
    """Serialize a protocol model for wire output.

    Includes None as null (exclude_none=False, the Pydantic default).
    Used for TurnPacket and ScoutResult JSON responses.
    """
    return model.model_dump()


def make_entity_key(entity_type: str, canonical_form: str) -> str:
    """Build deterministic entity key: '{entity_type}:{canonical_form}'.

    Used for dedupe and evidence_history cross-turn identification.
    """
    return f"{entity_type}:{canonical_form}"


def parse_entity_key(key: str) -> tuple[str, str]:
    """Parse entity key back to (entity_type, canonical_form).

    Handles values containing colons (e.g., file_loc:config.py:42).
    """
    entity_type, _, canonical_form = key.partition(":")
    return entity_type, canonical_form
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/context-injection && uv run pytest tests/test_canonical.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add packages/context-injection/context_injection/canonical.py packages/context-injection/tests/test_canonical.py
git commit -m "feat(context-injection): add canonical serialization and entity key functions"
```

---

## Task 7: State Management — HMAC, Store, AppContext (`state.py`)

**Files:**
- Create: `packages/context-injection/context_injection/state.py`
- Create: `packages/context-injection/tests/test_state.py`

**Context:** The state module manages per-process server state: HMAC key, TurnRequest store (bounded OrderedDict), token generation/verification, and the AppContext dataclass for the MCPServer lifespan.

Key design decisions from D8/D10:
- Single per-process 32-byte random key
- `MAX_TURN_RECORDS = 200` with oldest-eviction
- Duplicate turn_request_ref rejection
- Used-bit not set on verification failure
- Stored token comparison is security check; recompute is diagnostic

**Step 1: Write failing tests**

```python
"""Tests for server state management, HMAC tokens, and TurnRequest store."""

import pytest

from context_injection.canonical import ScoutTokenPayload
from context_injection.state import (
    MAX_TURN_RECORDS,
    AppContext,
    TurnRequestRecord,
    generate_token,
    make_turn_request_ref,
    verify_token,
)
from context_injection.types import ReadSpec, TurnRequest, SCHEMA_VERSION


def _make_read_spec(**overrides) -> ReadSpec:
    defaults = dict(
        action="read", resolved_path="src/app.py", strategy="first_n",
        max_lines=40, max_chars=2000,
    )
    defaults.update(overrides)
    return ReadSpec(**defaults)


def _make_turn_request(conversation_id: str = "conv_1", turn_number: int = 1) -> TurnRequest:
    return TurnRequest(
        schema_version=SCHEMA_VERSION,
        turn_number=turn_number,
        conversation_id=conversation_id,
        focus={"text": "test", "claims": [], "unresolved": []},
        evidence_history=[],
        posture="exploratory",
    )


class TestAppContext:
    def test_creates_hmac_key(self) -> None:
        ctx = AppContext.create(repo_root="/tmp/repo")
        assert len(ctx.hmac_key) == 32

    def test_different_instances_different_keys(self) -> None:
        ctx1 = AppContext.create(repo_root="/tmp/repo")
        ctx2 = AppContext.create(repo_root="/tmp/repo")
        assert ctx1.hmac_key != ctx2.hmac_key


class TestTokenGeneration:
    def test_roundtrip(self) -> None:
        """Generate a token and verify it."""
        ctx = AppContext.create(repo_root="/tmp/repo")
        spec = _make_read_spec()
        payload = ScoutTokenPayload(
            v=1, conversation_id="conv_1", turn_number=1,
            scout_option_id="so_001", spec=spec,
        )
        token = generate_token(ctx.hmac_key, payload)
        assert isinstance(token, str)
        assert verify_token(ctx.hmac_key, payload, token)

    def test_wrong_key_fails(self) -> None:
        ctx1 = AppContext.create(repo_root="/tmp/repo")
        ctx2 = AppContext.create(repo_root="/tmp/repo")
        spec = _make_read_spec()
        payload = ScoutTokenPayload(
            v=1, conversation_id="conv_1", turn_number=1,
            scout_option_id="so_001", spec=spec,
        )
        token = generate_token(ctx1.hmac_key, payload)
        assert not verify_token(ctx2.hmac_key, payload, token)

    def test_modified_payload_fails(self) -> None:
        ctx = AppContext.create(repo_root="/tmp/repo")
        spec = _make_read_spec()
        payload = ScoutTokenPayload(
            v=1, conversation_id="conv_1", turn_number=1,
            scout_option_id="so_001", spec=spec,
        )
        token = generate_token(ctx.hmac_key, payload)
        # Different spec
        modified_spec = _make_read_spec(resolved_path="src/evil.py")
        modified_payload = ScoutTokenPayload(
            v=1, conversation_id="conv_1", turn_number=1,
            scout_option_id="so_001", spec=modified_spec,
        )
        assert not verify_token(ctx.hmac_key, modified_payload, token)


class TestTurnRequestStore:
    def test_store_and_retrieve(self) -> None:
        ctx = AppContext.create(repo_root="/tmp/repo")
        req = _make_turn_request()
        ref = make_turn_request_ref(req)
        spec = _make_read_spec()
        token = "token_123"
        record = TurnRequestRecord(
            turn_request=req,
            scout_options={"so_001": (spec, token)},
        )
        ctx.store[ref] = record
        assert ref in ctx.store
        assert ctx.store[ref].scout_options["so_001"] == (spec, token)

    def test_duplicate_ref_detected(self) -> None:
        ctx = AppContext.create(repo_root="/tmp/repo")
        req = _make_turn_request()
        ref = make_turn_request_ref(req)
        record = TurnRequestRecord(turn_request=req, scout_options={})
        ctx.store[ref] = record
        assert ref in ctx.store
        # Second store with same ref should be detectable
        assert ref in ctx.store

    def test_bounded_capacity_evicts_oldest(self) -> None:
        ctx = AppContext.create(repo_root="/tmp/repo")
        # Fill store to capacity
        for i in range(MAX_TURN_RECORDS + 5):
            req = _make_turn_request(turn_number=i + 1)
            ref = make_turn_request_ref(req)
            record = TurnRequestRecord(turn_request=req, scout_options={})
            ctx.store_record(ref, record)
        assert len(ctx.store) == MAX_TURN_RECORDS
        # Oldest should be evicted
        oldest_ref = make_turn_request_ref(_make_turn_request(turn_number=1))
        assert oldest_ref not in ctx.store

    def test_used_bit_lifecycle(self) -> None:
        ctx = AppContext.create(repo_root="/tmp/repo")
        req = _make_turn_request()
        ref = make_turn_request_ref(req)
        record = TurnRequestRecord(turn_request=req, scout_options={})
        ctx.store[ref] = record
        assert record.used is False
        record.used = True
        assert ctx.store[ref].used is True


class TestMakeTurnRequestRef:
    def test_format(self) -> None:
        req = _make_turn_request(conversation_id="conv_abc", turn_number=3)
        assert make_turn_request_ref(req) == "conv_abc:3"
```

**Step 2: Run test to verify it fails**

Run: `cd packages/context-injection && uv run pytest tests/test_state.py -v`
Expected: FAIL (ImportError)

**Step 3: Write the implementation**

```python
"""Server state management: HMAC tokens, TurnRequest store, AppContext.

Per-process state with bounded capacity. Helper restart invalidates all tokens.

Design decisions:
- Single per-process 32-byte random key (D6/D8)
- MAX_TURN_RECORDS=200 with oldest-eviction (D8)
- Duplicate turn_request_ref rejection (D8)
- Used-bit not set on verification failure (D10)
- Stored token comparison is security; recompute is diagnostic (D10)
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
from collections import OrderedDict
from dataclasses import dataclass, field

from context_injection.canonical import ScoutTokenPayload, canonical_json_bytes
from context_injection.types import ReadSpec, GrepSpec, TurnRequest

MAX_TURN_RECORDS: int = 200
"""Bounded store capacity. Oldest-eviction when exceeded."""

TAG_LEN: int = 16
"""HMAC tag length in bytes (128 bits). Truncated from SHA-256 output."""


@dataclass
class TurnRequestRecord:
    """Stored record for Call 2 validation."""

    turn_request: TurnRequest
    scout_options: dict[str, tuple[ReadSpec | GrepSpec, str]]
    """scout_option_id → (frozen ScoutSpec, HMAC token) — atomic pairs."""
    used: bool = False
    """One-shot used-bit. Set only after successful verification, before execution."""


@dataclass
class AppContext:
    """Per-process server state, yielded by MCPServer lifespan."""

    hmac_key: bytes
    repo_root: str
    store: OrderedDict[str, TurnRequestRecord] = field(default_factory=OrderedDict)
    git_files: set[str] = field(default_factory=set)
    """Tracked file paths from git ls-files (repo-relative, populated at startup)."""
    entity_counter: int = 0
    """Monotonic counter for entity IDs within this process."""

    @classmethod
    def create(cls, repo_root: str, git_files: set[str] | None = None) -> AppContext:
        """Create a new AppContext with a fresh HMAC key."""
        return cls(
            hmac_key=os.urandom(32),
            repo_root=repo_root,
            git_files=git_files or set(),
        )

    def next_entity_id(self) -> str:
        """Generate the next entity ID (e_NNN format)."""
        self.entity_counter += 1
        return f"e_{self.entity_counter:03d}"

    def store_record(self, ref: str, record: TurnRequestRecord) -> None:
        """Store a TurnRequestRecord with bounded eviction.

        Raises ValueError if ref already exists (duplicate rejection).
        """
        if ref in self.store:
            raise ValueError(f"Duplicate turn_request_ref: {ref}")
        # Evict oldest if at capacity
        while len(self.store) >= MAX_TURN_RECORDS:
            self.store.popitem(last=False)
        self.store[ref] = record


def make_turn_request_ref(req: TurnRequest) -> str:
    """Build turn_request_ref: '{conversation_id}:{turn_number}'."""
    return f"{req.conversation_id}:{req.turn_number}"


def generate_token(key: bytes, payload: ScoutTokenPayload) -> str:
    """Generate base64url-encoded HMAC-SHA256 token, truncated to TAG_LEN bytes.

    Contract: base64url(HMAC-SHA256(K, canonical_bytes))[:TAG_LEN]

    Padding convention: standard base64url with '=' padding (Python default).
    Both generate and verify use the same function, so padding is consistent.
    Stripping padding would save 1-2 chars but adds decode complexity.
    """
    canonical = canonical_json_bytes(payload)
    mac = hmac.new(key, canonical, hashlib.sha256).digest()
    truncated = mac[:TAG_LEN]
    return base64.urlsafe_b64encode(truncated).decode("ascii")


def verify_token(key: bytes, payload: ScoutTokenPayload, token: str) -> bool:
    """Verify an HMAC token via constant-time comparison.

    Returns True if the token matches the expected HMAC for the payload.
    """
    expected = generate_token(key, payload)
    return hmac.compare_digest(expected.encode("ascii"), token.encode("ascii"))
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/context-injection && uv run pytest tests/test_state.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add packages/context-injection/context_injection/state.py packages/context-injection/tests/test_state.py
git commit -m "feat(context-injection): add HMAC tokens, TurnRequest store, AppContext"
```

---

## Task 8: Path Checking (`paths.py`)

**Files:**
- Create: `packages/context-injection/context_injection/paths.py`
- Create: `packages/context-injection/tests/test_paths.py`

**Context:** Path safety is the primary enforcement boundary. Two exported functions: `check_path_compile_time()` (Call 1: full pipeline) and `check_path_runtime()` (Call 2: lightweight re-check). Implements: input normalization, realpath containment, denylist, git ls-files gating, NFC normalization.

The denylist is glob-based, targeting where secrets live. Risk-signal detection for `*secret*`, `*token*`, `*credential*` paths.

**Step 1: Write failing tests**

```python
"""Tests for path canonicalization, denylist, and safety checks."""

import pytest

from context_injection.paths import (
    CompileTimeResult,
    check_path_compile_time,
    is_risk_signal_path,
    normalize_input_path,
)


class TestNormalizeInputPath:
    def test_strips_backticks(self) -> None:
        assert normalize_input_path("`src/app.py`") == "src/app.py"

    def test_strips_quotes(self) -> None:
        assert normalize_input_path('"src/app.py"') == "src/app.py"
        assert normalize_input_path("'src/app.py'") == "src/app.py"

    def test_splits_line_number(self) -> None:
        path, line = normalize_input_path("src/app.py:42", split_anchor=True)
        assert path == "src/app.py"
        assert line == 42

    def test_splits_github_anchor(self) -> None:
        path, line = normalize_input_path("src/app.py#L42", split_anchor=True)
        assert path == "src/app.py"
        assert line == 42

    def test_backslash_to_forward(self) -> None:
        assert normalize_input_path("src\\api\\auth.py") == "src/api/auth.py"

    def test_rejects_nul_bytes(self) -> None:
        with pytest.raises(ValueError, match="NUL"):
            normalize_input_path("src/app\x00.py")

    def test_rejects_dotdot_traversal(self) -> None:
        with pytest.raises(ValueError, match="traversal"):
            normalize_input_path("../etc/passwd")

    def test_rejects_absolute_path(self) -> None:
        with pytest.raises(ValueError, match="absolute"):
            normalize_input_path("/etc/passwd")

    def test_nfc_normalization(self) -> None:
        # NFD: e + combining acute
        nfd = "caf\u0065\u0301.py"
        # NFC: precomposed é
        nfc = "caf\u00e9.py"
        assert normalize_input_path(nfd) == nfc


class TestDenylist:
    def test_git_dir_denied(self) -> None:
        result = check_path_compile_time(
            ".git/config", repo_root="/tmp/repo", git_files={"src/app.py"},
        )
        assert result.status == "denied"

    def test_env_file_denied(self) -> None:
        result = check_path_compile_time(
            ".env", repo_root="/tmp/repo", git_files={".env", "src/app.py"},
        )
        assert result.status == "denied"

    def test_env_local_denied(self) -> None:
        result = check_path_compile_time(
            ".env.local", repo_root="/tmp/repo", git_files={".env.local"},
        )
        assert result.status == "denied"

    def test_env_example_allowed(self) -> None:
        result = check_path_compile_time(
            ".env.example", repo_root="/tmp/repo", git_files={".env.example"},
        )
        assert result.status == "allowed"

    def test_pem_file_denied(self) -> None:
        result = check_path_compile_time(
            "certs/server.pem", repo_root="/tmp/repo", git_files={"certs/server.pem"},
        )
        assert result.status == "denied"

    def test_ssh_dir_denied(self) -> None:
        result = check_path_compile_time(
            ".ssh/id_rsa", repo_root="/tmp/repo", git_files=set(),
        )
        assert result.status == "denied"


class TestGitLsFilesGating:
    def test_tracked_file_allowed(self) -> None:
        result = check_path_compile_time(
            "src/app.py", repo_root="/tmp/repo", git_files={"src/app.py"},
        )
        assert result.status == "allowed"

    def test_untracked_file_blocked(self) -> None:
        result = check_path_compile_time(
            "src/app.py", repo_root="/tmp/repo", git_files={"src/other.py"},
        )
        assert result.status == "not_tracked"


class TestRiskSignal:
    def test_secret_in_path(self) -> None:
        assert is_risk_signal_path("config/secrets.yaml") is True

    def test_token_in_path(self) -> None:
        assert is_risk_signal_path("auth/token_store.py") is True

    def test_credential_in_path(self) -> None:
        assert is_risk_signal_path("credentials/aws.json") is True

    def test_normal_path(self) -> None:
        assert is_risk_signal_path("src/app.py") is False


class TestCompileTimeResult:
    def test_allowed_result(self) -> None:
        result = check_path_compile_time(
            "src/app.py", repo_root="/tmp/repo", git_files={"src/app.py"},
        )
        assert result.status == "allowed"
        assert result.user_rel == "src/app.py"
        assert result.resolved_rel is not None
        assert result.risk_signal is False
```

**Step 2: Run test, verify failure, implement, verify pass, commit**

The implementation should include:
- `normalize_input_path()`: strip quotes/backticks, split anchors, NFC normalize, reject NUL/traversal/absolute
- `DENYLIST_DIRS` and `DENYLIST_FILES` as glob patterns
- `ENV_EXCEPTIONS`: `.env.example`, `.env.sample`, `.env.template`
- `check_path_compile_time()`: normalize → realpath → containment → denylist → git ls-files → CompileTimeResult
- `check_path_runtime()`: realpath → containment → regular file check
- `is_risk_signal_path()`: matches `*secret*`, `*token*`, `*credential*`
- `CompileTimeResult` as a dataclass with status, user_rel, resolved_rel, risk_signal, deny_reason, candidates, unresolved_reason

**Step 5: Commit**

```bash
git add packages/context-injection/context_injection/paths.py packages/context-injection/tests/test_paths.py
git commit -m "feat(context-injection): add path canonicalization, denylist, and safety checks"
```

---

## Task 9: Entity Extraction (`entities.py`)

**Files:**
- Create: `packages/context-injection/context_injection/entities.py`
- Create: `packages/context-injection/tests/test_entities.py`

**Context:** Regex-based entity extraction from claim/unresolved text. Implements: ordered extractor pipeline, entity type disambiguation (file_loc > file_path > file_name > file_hint), confidence assignment, normalization (`canon()`), and entity registry with global interning.

This is the most implementation-heavy module. Entity extraction regex patterns are not yet fully authored (noted as an open question in the plan). Start with well-defined patterns for MVP Tier 1 types; iterate based on testing.

**Step 1: Write failing tests for disambiguation rules and basic extraction**

Test cases based on the contract's Entity Type Disambiguation Rules:
- `config.py:42` → `file_loc`
- `src/api/auth.py` → `file_path`
- `config.yaml` → `file_name`
- `authenticate()` → `symbol`
- Backticked entities → `high` confidence
- Unquoted path-like → `medium` confidence

**Step 2-5: Implement, test, commit**

The implementation should include:
- `extract_entities(text: str, source_type: str, in_focus: bool, ctx: AppContext) -> list[Entity]`
- Ordered extractor list: `file_loc` → `file_path` → `file_name` → `symbol` → Tier 2 hints
- `canon()` function per entity type
- Span tracking to prevent overlapping extractions

**Commit message:**
```
feat(context-injection): add entity extraction with disambiguation and normalization
```

---

## Task 10: Template Matching and Scout Option Synthesis (`templates.py`)

**Files:**
- Create: `packages/context-injection/context_injection/templates.py`
- Create: `packages/context-injection/tests/test_templates.py`

**Context:** The template system implements the 3-step decision tree from Section 4 of the plan: (A) hard gates (MVP Tier 1 at high/medium confidence + focus-affinity), (B) prefer closers, (C) best anchor. Plus scout option synthesis (creating ReadOption/GrepOption with HMAC tokens) and dedupe filtering.

**Step 1: Write failing tests**

Test cases:
- Focus-affinity gate: only `in_focus=True` entities pass for probe templates
- Anchor type ranking: `file_loc > file_path > file_name > symbol`
- Clarifier templates bypass hard gate
- Dedupe: already-scouted entity_key filtered out
- Scout option synthesis: ReadSpec/GrepSpec created correctly from entities

**Step 2-5: Implement, test, commit**

The implementation should include:
- `match_templates(entities, path_decisions, evidence_history, budget, ctx) -> (list[TemplateCandidate], list[DedupRecord])`
- Template matching logic per TemplateId
- Ranking by anchor type, confidence, ambiguity risk
- Scout option synthesis with HMAC token generation
- Dedupe via entity_key and template_id from evidence_history

**Commit message:**
```
feat(context-injection): add template matching, ranking, and scout option synthesis
```

---

## Task 11: Pipeline Composition (`pipeline.py`)

**Files:**
- Create: `packages/context-injection/context_injection/pipeline.py`
- Create: `packages/context-injection/tests/test_pipeline.py`

**Context:** Composes the full Call 1 pipeline: TurnRequest → validate → extract entities → check paths → match templates → synthesize scout options → build TurnPacket. This is the "wiring" module — orchestrates the other modules.

**Step 1: Write failing test with full contract example**

Test: Parse the contract's Call 1 example TurnRequest, pipe through the pipeline, verify the TurnPacket contains expected entities, path decisions, template candidates, and budget.

**Step 2-5: Implement, test, commit**

The implementation should include:
- `process_turn(request: TurnRequest, ctx: AppContext) -> TurnPacketSuccess | TurnPacketError`
- Schema version validation (returns TurnPacketError on mismatch)
- Entity extraction from focus.claims, focus.unresolved, context_claims
- Path checking for all Tier 1 entities with paths
- Template matching and ranking
- Budget computation from evidence_history
- Store the TurnRequest for Call 2 validation
- Error handling: catch all exceptions, return TurnPacketError with internal_error

**Commit message:**
```
feat(context-injection): add process_turn pipeline composing all v0a modules
```

---

## Task 12: MCP Server (`server.py`)

**Files:**
- Create: `packages/context-injection/context_injection/server.py`
- Modify: `.mcp.json` (add context-injection server registration)
- Create: `packages/context-injection/tests/test_server.py`

**Context:** Wire the pipeline into an MCPServer with lifespan context, tool registration, and stdio entry point. Uses the SDK's `MCPServer` class (formerly `FastMCP`).

**Step 0: SDK smoke test (Codex review B1)**

Before wiring the full server, verify the SDK API assumptions with a minimal server. This catches constructor signature, lifespan plumbing, and tool decorator issues before they compound with pipeline logic.

```python
"""SDK smoke test — verify MCPServer API assumptions.

Run this as a standalone script, not as a pytest test (avoids async complexity).
Delete after Task 12 passes.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp.server.mcpserver import MCPServer, Context


@dataclass
class TestCtx:
    value: str = "hello"


@asynccontextmanager
async def test_lifespan(server: MCPServer) -> AsyncIterator[TestCtx]:
    yield TestCtx()


mcp = MCPServer("smoke-test", version="0.1.0", lifespan=test_lifespan)


@mcp.tool()
def echo(message: str, ctx: Context[TestCtx]) -> str:
    """Echo a message, verifying lifespan context access."""
    app_ctx = ctx.request_context.lifespan_context
    return f"{app_ctx.value}: {message}"


if __name__ == "__main__":
    print("MCPServer constructor: OK")
    print("Tool registered: OK")
    print("Lifespan pattern: OK (verified by constructor acceptance)")
    # Do NOT call mcp.run() — just verify the setup compiles
```

Run: `cd packages/context-injection && uv run python -c "from mcp.server.mcpserver import MCPServer, Context; print('Import OK')"`

If this fails, the SDK API has changed and the plan needs updating before proceeding.

**Step 1: Write failing test**

```python
"""Tests for the MCP server setup."""

from context_injection.server import create_server


def test_server_has_process_turn_tool() -> None:
    server = create_server(repo_root="/tmp/repo")
    # Verify the server has the expected tools registered
    # (exact assertion depends on SDK internals — may need async test)
    assert server.name == "context-injection"
```

**Step 2: Write the implementation**

```python
"""Context injection MCP server.

Entry point: python -m context_injection.server
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import os
import subprocess

from mcp.server.mcpserver import MCPServer, Context

from context_injection.pipeline import process_turn
from context_injection.state import AppContext
from context_injection.types import TurnRequest, TurnPacketSuccess, TurnPacketError


@asynccontextmanager
async def app_lifespan(server: MCPServer) -> AsyncIterator[AppContext]:
    """Initialize per-process state: HMAC key, git file list, store."""
    repo_root = os.environ.get("REPO_ROOT", os.getcwd())
    git_files = _load_git_files(repo_root)
    ctx = AppContext.create(repo_root=repo_root, git_files=git_files)
    yield ctx


def _load_git_files(repo_root: str) -> set[str]:
    """Load tracked file list from git ls-files. Fail closed on error."""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            capture_output=True, text=True, timeout=10,
            cwd=repo_root,
        )
        if result.returncode != 0:
            raise RuntimeError(f"git ls-files failed: {result.stderr}")
        return set(result.stdout.splitlines())
    except (subprocess.TimeoutExpired, FileNotFoundError, RuntimeError):
        # Fail closed: empty set means all files are "not tracked"
        return set()


def create_server(repo_root: str | None = None) -> MCPServer:
    """Create the MCPServer instance (useful for testing without running)."""
    mcp = MCPServer(
        "context-injection",
        version="0.1.0",
        lifespan=app_lifespan,
    )

    @mcp.tool()
    def process_turn_tool(
        request: TurnRequest,
        ctx: Context[AppContext],
    ) -> TurnPacketSuccess | TurnPacketError:
        """Process a TurnRequest (Call 1) and return a TurnPacket."""
        app_ctx = ctx.request_context.lifespan_context
        return process_turn(request, app_ctx)

    return mcp


def main() -> None:
    """Entry point for python -m context_injection.server."""
    server = create_server()
    server.run()
```

**Step 3: Update `.mcp.json`**

Add the context-injection server alongside the existing codex entry:

```json
{
  "mcpServers": {
    "codex": { ... },
    "context-injection": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--directory", "packages/context-injection", "python", "-m", "context_injection.server"],
      "env": {
        "REPO_ROOT": "${PWD}"
      }
    }
  }
}
```

**Step 4: Run tests, verify**

Run: `cd packages/context-injection && uv run pytest tests/test_server.py -v`

**Step 5: Commit**

```bash
git add packages/context-injection/context_injection/server.py packages/context-injection/tests/test_server.py .mcp.json
git commit -m "feat(context-injection): add MCPServer with process_turn tool and lifespan"
```

---

## Task 13: Integration Test — Full Call 1 Pipeline

**Files:**
- Create: `packages/context-injection/tests/test_integration.py`

**Context:** End-to-end test using the full contract example. Verifies that a TurnRequest flows through the entire pipeline and produces a valid TurnPacket with entities, path decisions, template candidates, and budget. Uses injected git_files (no subprocess) and a known repo root.

**Step 1: Write the integration test**

```python
"""Integration test: full Call 1 pipeline with contract example input."""

from context_injection.pipeline import process_turn
from context_injection.state import AppContext
from context_injection.types import SCHEMA_VERSION, TurnRequest, TurnPacketSuccess


def test_contract_example_produces_valid_turn_packet() -> None:
    """The contract's Call 1 example input produces a valid TurnPacket."""
    git_files = {
        "src/config/settings.yaml",
        "src/config/loader.py",
        "config.yaml",
    }
    ctx = AppContext.create(repo_root="/tmp/repo", git_files=git_files)

    request = TurnRequest.model_validate({
        "schema_version": SCHEMA_VERSION,
        "turn_number": 3,
        "conversation_id": "conv_abc123",
        "focus": {
            "text": "Whether the project uses YAML or TOML for configuration",
            "claims": [
                {"text": "The project uses `src/config/settings.yaml` for all configuration", "status": "new", "turn": 3},
                {"text": "YAML was chosen over TOML for readability", "status": "new", "turn": 3},
            ],
            "unresolved": [
                {"text": "Whether `config.yaml` is the only config file or if there are environment overrides", "turn": 3}
            ],
        },
        "context_claims": [
            {"text": "The project follows a monorepo structure with `packages/` subdirectories", "status": "reinforced", "turn": 1}
        ],
        "evidence_history": [
            {"entity_key": "file_path:src/config/loader.py", "template_id": "probe.file_repo_fact", "turn": 1}
        ],
        "posture": "evaluative",
    })

    result = process_turn(request, ctx)
    assert isinstance(result, TurnPacketSuccess)
    assert result.schema_version == SCHEMA_VERSION
    assert result.status == "success"

    # Should have extracted entities from backticked paths
    entity_types = {e.type for e in result.entities}
    assert "file_path" in entity_types or "file_name" in entity_types

    # Budget should reflect 1 prior evidence item
    assert result.budget.evidence_count == 1
    assert result.budget.evidence_remaining == 4

    # Deduped should include the already-scouted loader.py
    deduped_keys = {d.entity_key for d in result.deduped}
    assert "file_path:src/config/loader.py" in deduped_keys

    # Should have template candidates (at least one probe for settings.yaml)
    assert len(result.template_candidates) > 0

    # TurnRequest should be stored for Call 2
    ref = "conv_abc123:3"
    assert ref in ctx.store
```

**Step 2: Run and iterate**

Run: `cd packages/context-injection && uv run pytest tests/test_integration.py -v`

This test will likely require iteration as entity extraction patterns are refined. The test serves as the acceptance criteria for v0a completion.

**Step 3: Commit**

```bash
git add packages/context-injection/tests/test_integration.py
git commit -m "test(context-injection): add integration test for full Call 1 pipeline"
```

---

## Task 14: Lint, Type-Check, Final Cleanup

**Files:**
- Modify: various (fix lint and type errors)

**Step 1: Run ruff**

Run: `cd packages/context-injection && uv run ruff check . && uv run ruff format --check .`

**Step 2: Fix any issues**

**Step 3: Run full test suite**

Run: `cd packages/context-injection && uv run pytest tests/ -v --tb=short`
Expected: All tests PASS

**Step 4: Commit**

```bash
git add packages/context-injection/
git commit -m "chore(context-injection): lint and type-check cleanup"
```

---

## Dependency Graph

```
Task 1: Scaffolding
  └─ Task 2: enums.py
       └─ Task 3: types.py (base + input models)
            └─ Task 4: types.py (output models)
                 └─ Task 5: types.py (discriminated unions)
                      ├─ Task 6: canonical.py
                      │    └─ Task 7: state.py
                      │         └─ Task 9: entities.py (imports AppContext from state.py)
                      ├─ Task 8: paths.py
                      └─ Task 10: templates.py (depends on 6, 7, 8, 9)
                           └─ Task 11: pipeline.py
                                └─ Task 12: server.py (Step 0: SDK smoke test)
                                     └─ Task 13: Integration test
                                          └─ Task 14: Final cleanup
```

Tasks 6 and 8 can be parallelized after Task 5 completes. Task 9 depends on Task 7 (entities.py imports AppContext for the entity counter). Task 10 depends on all four (6, 7, 8, 9).

## Open Questions to Resolve During Implementation

These should be decided as encountered, not upfront:

| Question | Default | Decide when |
|----------|---------|-------------|
| Entity extraction regex specifics | Start conservative, iterate | Task 9 |
| `file_name` resolution (subprocess) | Mock in tests, real in server | Task 8/12 |
| Symlink policy | Resolve-and-contain (realpath handles it) | Task 8 |
| `git ls-files` failure at startup | Fail closed (empty set) | Task 12 |
| Callable discriminator JSON schema quality | Verify schema output works with MCP SDK clients | Task 5, after implementation |

## Test Coverage Gaps to Address (Codex Review)

These test cases were identified as missing during Codex review. Add them to the relevant task's test file:

| Gap | Task | What to test |
|-----|------|-------------|
| Resolved-key dedupe semantics | Task 10 (templates.py) | Dedupe operates on effective probed target (resolved_key), not entity identity key. Two mentions of the same file (one via filename, one via path) must not produce duplicate scouts. |
| Risk-signal cap halving | Task 8 (paths.py) or Task 10 (templates.py) | Risk-signal paths get halved `max_lines`/`max_chars` in scout options. Test that `risk_signal=True` produces half the budget caps. |
| Budget floor invariant | Task 10 (templates.py) or Task 11 (pipeline.py) | `evidence_history.length` is treated as a floor — even if some evidence was evicted from the store, the budget reflects the full history count. |
