"""Tests for governance rule content and cross-contract invariant references."""
import re
from pathlib import Path

_REFERENCES_DIR = Path(__file__).resolve().parent.parent / "references"


def test_governance_key_phrases_present() -> None:
    """Each governance rule must contain its distinguishing key phrase."""
    contract = (_REFERENCES_DIR / "consultation-contract.md").read_text()
    section_match = re.search(r"## 15\. Governance.*?(?=\n## \d+\.|\Z)", contract, re.DOTALL)
    assert section_match, "§15 not found"
    section = section_match.group()

    key_phrases = {
        1: "debug-gated",
        2: "fail-closed",
        3: "auto-escalation",
        4: "direct invocation",
        5: "threadId",
        6: "sanitizer_status",
        7: "re-consent",
    }
    for rule_num, phrase in key_phrases.items():
        assert phrase in section, f"Governance rule {rule_num} missing key phrase {phrase!r}"


def test_cross_contract_invariant_refs() -> None:
    """CI-SEC-* references in §15 must exist in context-injection-contract.md."""
    consultation = (_REFERENCES_DIR / "consultation-contract.md").read_text()
    ci_contract = (_REFERENCES_DIR / "context-injection-contract.md").read_text()

    refs = set(re.findall(r"CI-SEC-\d+", consultation))
    assert len(refs) > 0, "No CI-SEC-* references found in consultation contract"
    for ref in refs:
        assert ref in ci_contract, f"{ref} referenced in consultation contract but not found in context-injection contract"
