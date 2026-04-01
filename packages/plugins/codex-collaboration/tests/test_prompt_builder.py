from __future__ import annotations

import pytest

from server.prompt_builder import parse_consult_response


def test_parse_consult_response_rejects_malformed_json() -> None:
    with pytest.raises(ValueError, match="expected JSON object"):
        parse_consult_response("not-json")


def test_parse_consult_response_rejects_missing_required_fields() -> None:
    with pytest.raises(ValueError, match="missing string position"):
        parse_consult_response(
            '{"evidence": [], "uncertainties": [], "follow_up_branches": []}'
        )
