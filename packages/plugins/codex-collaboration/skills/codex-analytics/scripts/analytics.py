"""Compute analytics views from codex-collaboration outcome and audit streams.

Usage: python3 analytics.py <outcomes.jsonl> <events.jsonl>
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


def _read_jsonl(path: Path) -> tuple[list[dict[str, object]], int]:
    """Read a JSONL file, skipping malformed lines. Returns (records, malformed_count)."""
    if not path.exists():
        return [], 0
    records: list[dict[str, object]] = []
    malformed = 0
    for line in path.read_text().strip().split("\n"):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            malformed += 1
    return records, malformed


def main(outcomes_path: Path, audit_path: Path) -> None:
    by_type: Counter[str] = Counter()
    workflow_counts: Counter[str] = Counter()
    context_sizes: list[int] = []
    fingerprints: Counter[str] = Counter()
    delegation_terminals: list[dict[str, object]] = []
    unknown_types: Counter[str] = Counter()

    outcome_records, outcomes_malformed = _read_jsonl(outcomes_path)
    total_outcome_records = len(outcome_records)

    for r in outcome_records:
        ot = r.get("outcome_type", "")
        if ot in ("consult", "dialogue_turn"):
            by_type[ot] += 1
            cs = r.get("context_size")
            if cs is not None:
                context_sizes.append(cs)
            fp = r.get("policy_fingerprint")
            if fp is not None:
                fingerprints[fp] += 1
            if ot == "consult":
                wf = r.get("workflow", "consult")
                workflow_counts[wf] += 1
        elif ot == "delegation_terminal":
            by_type[ot] += 1
            delegation_terminals.append(r)
        else:
            unknown_types[ot] += 1

    audit_actions: Counter[str] = Counter()
    decisions: Counter[str] = Counter()
    promote_count = 0
    discard_count = 0
    delegate_starts: dict[str, str] = {}

    audit_records, audit_malformed = _read_jsonl(audit_path)
    total_audit_records = len(audit_records)

    for r in audit_records:
        action = r.get("action", "")
        audit_actions[action] += 1
        if action in ("approve", "deny"):
            decisions[r.get("decision", "unknown")] += 1
        elif action == "promote":
            promote_count += 1
        elif action == "discard":
            discard_count += 1
        elif action == "delegate_start":
            jid = r.get("job_id")
            if jid:
                delegate_starts[jid] = r.get("timestamp", "")

    print("## Data Sources")
    outcomes_note = f", {outcomes_malformed} malformed" if outcomes_malformed else ""
    audit_note = f", {audit_malformed} malformed" if audit_malformed else ""
    print(
        f"- Outcomes: `{outcomes_path}` ({total_outcome_records} records{outcomes_note})"
    )
    print(f"- Audit: `{audit_path}` ({total_audit_records} records{audit_note})")

    print("\n## Usage")
    print("| Metric | Count |")
    print("|--------|-------|")
    for t in ("consult", "dialogue_turn", "delegation_terminal"):
        print(f"| {t} | {by_type[t]} |")
    delegate_start_count = audit_actions["delegate_start"]
    print(f"| delegate_start | {delegate_start_count} |")
    review_count = workflow_counts["review"]
    print(f"| reviews | {review_count} |")

    if unknown_types:
        unk_total = sum(unknown_types.values())
        unk_detail = dict(unknown_types)
        print(
            f"\n**Skipped {unk_total} records with unknown outcome_type:** {unk_detail}"
        )

    print("\n## Reliability and Security")
    total_del = len(delegation_terminals)
    completed = sum(
        1 for d in delegation_terminals if d.get("terminal_status") == "completed"
    )
    failed = sum(
        1 for d in delegation_terminals if d.get("terminal_status") == "failed"
    )
    unknown = sum(
        1 for d in delegation_terminals if d.get("terminal_status") == "unknown"
    )
    rate = (
        f"{completed}/{total_del} ({completed * 100 // total_del}%)"
        if total_del
        else "n/a"
    )
    esc_count = audit_actions["escalate"]
    esc_approve = decisions["approve"]
    esc_deny = decisions["deny"]
    print("| Metric | Value |")
    print("|--------|-------|")
    print(f"| Delegation success rate | {rate} |")
    print(f"| Failed | {failed} |")
    print(f"| Unknown | {unknown} |")
    print(f"| Escalations | {esc_count} |")
    print(f"| Escalation approvals | {esc_approve} |")
    print(f"| Escalation denials | {esc_deny} |")
    print("| Credential blocks/shadows | unavailable (not emitted to audit stream) |")
    print("| Promotion rejections | unavailable (not emitted to audit stream) |")

    print("\n## Context and Runtime")
    if context_sizes:
        s = sorted(context_sizes)
        print("| Metric | Value |")
        print("|--------|-------|")
        print(f"| Min context | {s[0]} |")
        print(f"| Max context | {s[-1]} |")
        print(f"| Mean context | {sum(s) // len(s)} |")
        print(f"| p50 context | {s[len(s) // 2]} |")
    else:
        print("No context size data.")

    if fingerprints:
        print("\n### Policy Fingerprints")
        print("| Fingerprint | Count |")
        print("|-------------|-------|")
        for fp, count in fingerprints.most_common():
            print(f"| `{fp}` | {count} |")
    else:
        print("\nNo policy fingerprint data.")

    print("\n## Delegation Lifecycle")
    print("| Status | Count |")
    print("|--------|-------|")
    print(f"| started | {len(delegate_starts)} |")
    print(f"| completed | {completed} |")
    print(f"| failed | {failed} |")
    print(f"| unknown | {unknown} |")
    print(f"| promoted | {promote_count} |")
    print(f"| discarded | {discard_count} |")
    print(f"| escalations | {esc_count} |")

    print("\n## Review")
    consult_count = workflow_counts["consult"]
    ratio = f"{review_count}:{consult_count}" if consult_count else "n/a"
    print("| Metric | Value |")
    print("|--------|-------|")
    print(f"| Review consultations | {review_count} |")
    print(f"| workflow=consult | {consult_count} |")
    print(f"| workflow=review | {review_count} |")
    print(f"| Review:consult ratio | {ratio} |")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <outcomes.jsonl> <events.jsonl>", file=sys.stderr)
        sys.exit(1)
    main(Path(sys.argv[1]), Path(sys.argv[2]))
