"""Egress credential scanner vs shared corpus.

The egress scanner runs against testdata/credential_parity_corpus.json.
Tests verify documented expectations match actual behavior.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.credential_scan import scan_text


_CORPUS_PATH = Path(__file__).resolve().parent.parent / "testdata" / "credential_parity_corpus.json"
_CORPUS_CASES = json.loads(_CORPUS_PATH.read_text())["cases"]


class TestEgressCorpus:
    """Egress scanner (credential_scan.scan_text) matches corpus expectations."""

    @pytest.mark.parametrize("case", _CORPUS_CASES, ids=[c["id"] for c in _CORPUS_CASES])
    def test_case(self, case: dict) -> None:
        result = scan_text(case["input"])
        expected = case["egress_action"]
        actual = result.action
        assert actual == expected, (
            f"[{case['id']}] egress expected {expected!r}, got {actual!r}. "
            f"Note: {case.get('note', '')}"
        )
