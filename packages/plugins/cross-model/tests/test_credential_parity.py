"""Parity tests: egress and ingress credential scanners vs shared corpus.

Both scanners run against testdata/credential_parity_corpus.json.
Divergences are documented in the corpus — tests verify documented
expectations match actual behavior.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.credential_scan import scan_text

# Import ingress scanner from context-injection package
from context_injection.redact import redact_known_secrets


@pytest.fixture(scope="module")
def corpus() -> list[dict]:
    corpus_path = Path(__file__).resolve().parent.parent / "testdata" / "credential_parity_corpus.json"
    data = json.loads(corpus_path.read_text())
    return data["cases"]


class TestEgressCorpus:
    """Egress scanner (credential_scan.scan_text) matches corpus expectations."""

    def test_all_cases(self, corpus: list[dict]) -> None:
        for case in corpus:
            result = scan_text(case["input"])
            expected = case["egress_action"]
            actual = result.action
            assert actual == expected, (
                f"[{case['id']}] egress expected {expected!r}, got {actual!r}. "
                f"Note: {case.get('note', '')}"
            )


class TestIngressCorpus:
    """Ingress scanner (redact.redact_known_secrets) matches corpus expectations."""

    def test_all_cases(self, corpus: list[dict]) -> None:
        for case in corpus:
            _, count = redact_known_secrets(case["input"])
            expected_redacts = case["ingress_redacts"]
            actual_redacts = count > 0
            assert actual_redacts == expected_redacts, (
                f"[{case['id']}] ingress expected redacts={expected_redacts!r}, "
                f"got count={count}. Note: {case.get('note', '')}"
            )


class TestPemParity:
    """PEM regex must be identical across scanners."""

    def test_pem_regex_identical(self) -> None:
        from scripts.secret_taxonomy import FAMILIES
        from context_injection.redact import _PEM_PRIVATE_KEY_RE

        pem_family = next(f for f in FAMILIES if f.name == "pem_private_key")
        assert pem_family.pattern.pattern == _PEM_PRIVATE_KEY_RE.pattern, (
            f"PEM regex divergence:\n"
            f"  egress:  {pem_family.pattern.pattern!r}\n"
            f"  ingress: {_PEM_PRIVATE_KEY_RE.pattern!r}"
        )
