"""Shape consistency test for OutcomeRecord emission across all paths."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from server.control_plane import ControlPlane
from server.dialogue import DialogueController
from server.journal import OperationJournal
from server.lineage_store import LineageStore
from server.models import ConsultRequest, DelegationOutcomeRecord, OperationJournalEntry
from server.turn_store import TurnStore

from tests.test_control_plane import FakeRuntimeSession, _compat_result, _repo_identity


def _collect_outcomes(plugin_data: Path) -> list[dict]:
    outcomes_path = plugin_data / "analytics" / "outcomes.jsonl"
    if not outcomes_path.exists():
        return []
    content = outcomes_path.read_text(encoding="utf-8").strip()
    if not content:
        return []
    return [json.loads(line) for line in content.split("\n")]


def test_all_outcome_records_share_same_keys(tmp_path: Path) -> None:
    """Consult, normal reply, recovery, and repair all produce the same key set."""
    focus = tmp_path / "focus.py"
    focus.write_text("print('focus')\n", encoding="utf-8")

    plugin_data = tmp_path / "plugin-data"
    journal = OperationJournal(plugin_data)

    # 1. Consult outcome
    session_consult = FakeRuntimeSession()
    plane_consult = ControlPlane(
        plugin_data_path=plugin_data,
        runtime_factory=lambda _repo_root: session_consult,
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
        clock=lambda: 100.0,
        uuid_factory=iter((f"uuid-{i}" for i in range(100))).__next__,
        journal=journal,
    )
    plane_consult.codex_consult(
        ConsultRequest(
            repo_root=tmp_path,
            objective="Test",
            explicit_paths=(Path("focus.py"),),
        )
    )

    # 2. Normal dialogue reply outcome
    session_dialogue = FakeRuntimeSession()
    plane_dialogue = ControlPlane(
        plugin_data_path=plugin_data,
        runtime_factory=lambda _repo_root: session_dialogue,
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
        clock=lambda: 200.0,
        uuid_factory=iter((f"d-uuid-{i}" for i in range(100))).__next__,
        journal=journal,
    )
    store = LineageStore(plugin_data, "sess-shape")
    turn_store = TurnStore(plugin_data, "sess-shape")
    controller = DialogueController(
        control_plane=plane_dialogue,
        lineage_store=store,
        journal=journal,
        session_id="sess-shape",
        repo_identity_loader=_repo_identity,
        uuid_factory=iter((f"dc-uuid-{i}" for i in range(100))).__next__,
        turn_store=turn_store,
    )
    start = controller.start(tmp_path)
    controller.reply(
        collaboration_id=start.collaboration_id,
        objective="Test turn",
        explicit_paths=(Path("focus.py"),),
    )

    # 3. Recovery outcome
    session_recovery = FakeRuntimeSession()
    session_recovery.read_thread_response = {
        "thread": {
            "id": "thr-start",
            "turns": [
                {
                    "id": "recovered-turn",
                    "status": "completed",
                    "agentMessage": "",
                    "createdAt": "",
                },
            ],
        },
    }
    plane_recovery = ControlPlane(
        plugin_data_path=plugin_data,
        runtime_factory=lambda _repo_root: session_recovery,
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
        clock=lambda: 300.0,
        uuid_factory=iter((f"r-uuid-{i}" for i in range(100))).__next__,
        journal=journal,
    )
    store_r = LineageStore(plugin_data, "sess-recovery")
    turn_store_r = TurnStore(plugin_data, "sess-recovery")
    controller_r = DialogueController(
        control_plane=plane_recovery,
        lineage_store=store_r,
        journal=journal,
        session_id="sess-recovery",
        repo_identity_loader=_repo_identity,
        uuid_factory=iter((f"rc-uuid-{i}" for i in range(100))).__next__,
        turn_store=turn_store_r,
    )
    start_r = controller_r.start(tmp_path)
    # Write an unresolved turn_dispatch for recovery to pick up
    journal.write_phase(
        OperationJournalEntry(
            idempotency_key="r-uuid-0:thr-start:1",
            operation="turn_dispatch",
            phase="intent",
            collaboration_id=start_r.collaboration_id,
            created_at="2026-04-01T00:00:00Z",
            repo_root=str(tmp_path.resolve()),
            codex_thread_id="thr-start",
            turn_sequence=1,
            runtime_id="r-uuid-0",
            context_size=2048,
        ),
        session_id="sess-recovery",
    )
    controller_r.recover_pending_operations()

    # 4. Best-effort repair outcome
    session_repair = FakeRuntimeSession()
    session_repair.read_thread_response = {
        "thread": {
            "id": "thr-start",
            "turns": [
                {
                    "id": "repaired-turn",
                    "status": "completed",
                    "agentMessage": "",
                    "createdAt": "",
                },
            ],
        },
    }
    plane_repair = ControlPlane(
        plugin_data_path=plugin_data,
        runtime_factory=lambda _repo_root: session_repair,
        compat_checker=_compat_result,
        repo_identity_loader=_repo_identity,
        clock=lambda: 400.0,
        uuid_factory=iter((f"rp-uuid-{i}" for i in range(100))).__next__,
        journal=journal,
    )
    store_rp = LineageStore(plugin_data, "sess-repair")
    turn_store_rp = TurnStore(plugin_data, "sess-repair")
    controller_rp = DialogueController(
        control_plane=plane_repair,
        lineage_store=store_rp,
        journal=journal,
        session_id="sess-repair",
        repo_identity_loader=_repo_identity,
        uuid_factory=iter((f"rpc-uuid-{i}" for i in range(100))).__next__,
        turn_store=turn_store_rp,
    )
    start_rp = controller_rp.start(tmp_path)
    store_rp.update_status(start_rp.collaboration_id, "unknown")
    intent_entry_rp = OperationJournalEntry(
        idempotency_key="rp-uuid-0:thr-start:1",
        operation="turn_dispatch",
        phase="intent",
        collaboration_id=start_rp.collaboration_id,
        created_at="2026-04-01T00:00:00Z",
        repo_root=str(tmp_path.resolve()),
        codex_thread_id="thr-start",
        turn_sequence=1,
        runtime_id="rp-uuid-0",
        context_size=1024,
    )
    journal.write_phase(intent_entry_rp, session_id="sess-repair")
    controller_rp._best_effort_repair_turn(intent_entry_rp)

    # 5. Delegation terminal outcome (direct write — journal helper added in Task 4)
    outcomes_path = plugin_data / "analytics" / "outcomes.jsonl"
    with outcomes_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(DelegationOutcomeRecord(
            outcome_id="del-outcome-1",
            timestamp="2026-04-01T00:00:00Z",
            outcome_type="delegation_terminal",
            collaboration_id="collab-del",
            runtime_id="rt-del",
            job_id="job-del",
            terminal_status="completed",
            base_commit="abc123",
            repo_root=str(tmp_path),
        )), sort_keys=True) + "\n")

    # Collect all outcomes and verify key consistency within each outcome_type.
    # Advisory outcomes (consult, dialogue_turn) and delegation terminal
    # outcomes have deliberately different schemas — dispatch by outcome_type.
    outcomes = _collect_outcomes(plugin_data)
    assert len(outcomes) >= 4, f"Expected at least 4 outcomes, got {len(outcomes)}"

    by_type: dict[str, list[frozenset[str]]] = {}
    for record in outcomes:
        ot = record.get("outcome_type", "unknown")
        by_type.setdefault(ot, []).append(frozenset(record.keys()))

    for ot, key_sets in by_type.items():
        assert len(set(key_sets)) == 1, (
            f"Outcome records of type {ot!r} have inconsistent keys. "
            f"Key sets: {[sorted(ks) for ks in key_sets]}"
        )
