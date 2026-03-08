"""Tests for protocol enums."""

from context_injection.enums import (
    ClaimStatus,
    Confidence,
    EntityType,
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
        assert Posture.COMPARATIVE == "comparative"


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



class TestTruncationReason:
    def test_values(self) -> None:
        assert TruncationReason.MAX_LINES == "max_lines"
        assert TruncationReason.MAX_CHARS == "max_chars"
        assert TruncationReason.MAX_RANGES == "max_ranges"


def test_all_enums_are_str_subclass() -> None:
    """Every enum member must serialize to its string value."""
    for enum_cls in [
        EntityType,
        Confidence,
        ClaimStatus,
        Posture,
        PathStatus,
        UnresolvedReason,
        TemplateId,
        ScoutAction,
        ExcerptStrategy,
        ScoutStatus,
        TruncationReason,
    ]:
        for member in enum_cls:
            assert isinstance(member, str)
            assert str(member) == member.value
