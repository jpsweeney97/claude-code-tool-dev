from __future__ import annotations

from pathlib import Path

PLUGIN_ROOT = Path(__file__).parent.parent
COMMAND_SKILLS = [
    PLUGIN_ROOT / "skills" / "search" / "SKILL.md",
    PLUGIN_ROOT / "skills" / "distill" / "SKILL.md",
    PLUGIN_ROOT / "skills" / "triage" / "SKILL.md",
    PLUGIN_ROOT / "skills" / "defer" / "SKILL.md",
]
STATE_SKILLS = [
    PLUGIN_ROOT / "skills" / "load" / "SKILL.md",
    PLUGIN_ROOT / "skills" / "save" / "SKILL.md",
    PLUGIN_ROOT / "skills" / "quicksave" / "SKILL.md",
    PLUGIN_ROOT / "skills" / "summary" / "SKILL.md",
]
LOAD_SKILL = PLUGIN_ROOT / "skills" / "load" / "SKILL.md"
CHAIN_STATE_SKILLS = [
    PLUGIN_ROOT / "skills" / "save" / "SKILL.md",
    PLUGIN_ROOT / "skills" / "quicksave" / "SKILL.md",
    PLUGIN_ROOT / "skills" / "summary" / "SKILL.md",
]


def test_no_skill_doc_uses_relative_script_paths() -> None:
    for path in COMMAND_SKILLS + STATE_SKILLS:
        text = path.read_text(encoding="utf-8")
        assert "../../scripts/" not in text


def test_skill_docs_do_not_request_tool_permissions_up_front() -> None:
    for path in COMMAND_SKILLS + STATE_SKILLS:
        text = path.read_text(encoding="utf-8")
        assert "allowed-tools" not in text


def test_command_skills_define_plugin_root_setup() -> None:
    for path in COMMAND_SKILLS:
        text = path.read_text(encoding="utf-8")
        assert "Resolve plugin root" in text
        assert "three levels above this `SKILL.md`" in text
        assert "not the `skills/` directory" in text
        assert 'PLUGIN_ROOT="/absolute/path/to/handoff"' in text
        assert "two levels above" not in text
        assert 'UV_PROJECT_ENVIRONMENT="$PROJECT_ROOT/.claude/plugin-runtimes/handoff"' in text
        assert "PYTHONDONTWRITEBYTECODE=1" in text


def test_state_skills_use_session_state_module() -> None:
    for path in CHAIN_STATE_SKILLS:
        text = path.read_text(encoding="utf-8")
        assert "Resolve plugin root" in text
        assert "three levels above this `SKILL.md`" in text
        assert "not the `skills/` directory" in text
        assert 'PLUGIN_ROOT="/absolute/path/to/handoff"' in text
        assert "session_state.py" in text
        assert 'python "$PLUGIN_ROOT/scripts/session_state.py"' in text
        assert "begin-active-write" in text
        assert "write-active-handoff" in text
        assert "operation_state_path" in text
        assert "allocated_active_path" in text
        assert "resumed_from_path" in text
        assert "<project_root>/.claude/handoffs/" in text
        assert "read-state" not in text
        assert "clear-state" not in text
        assert "$PROJECT_ROOT/docs/handoffs/.session-state" not in text
        assert "legacy plain-text state file" not in text
        assert "The literal `python` command must resolve to Python >=3.11." in text
        assert "PYTHONDONTWRITEBYTECODE=1" in text
        assert "UV_PROJECT_ENVIRONMENT" not in text
        assert "uv run --project" not in text


def test_load_skill_uses_load_transaction_and_listing_scripts() -> None:
    text = LOAD_SKILL.read_text(encoding="utf-8")
    assert "Resolve plugin root" in text
    assert "three levels above this `SKILL.md`" in text
    assert "not the `skills/` directory" in text
    assert 'PLUGIN_ROOT="/absolute/path/to/handoff"' in text
    assert 'python "$PLUGIN_ROOT/scripts/load_transactions.py"' in text
    assert 'python "$PLUGIN_ROOT/scripts/list_handoffs.py"' in text
    assert "<project_root>/.claude/handoffs/archive/<filename>" in text
    assert (
        "<project_root>/.claude/handoffs/.session-state/handoff-<project>-<resume_token>.json"
        in text
    )
    assert 'load_transactions.py" \\' in text
    assert "session_state.py" not in text
    assert 'ls "$(git rev-parse --show-toplevel)/docs/handoffs"' not in text
    assert '--archive-dir "$PROJECT_ROOT/docs/handoffs/archive"' not in text


def test_load_skill_documents_fail_closed_operator_recovery_boundaries() -> None:
    text = LOAD_SKILL.read_text(encoding="utf-8")

    assert "Readable pending load transactions are recovered before a new load is selected" in text
    assert "Unreadable or corrupt transaction records block `/load`" in text
    assert "global fail-closed" in text
    assert "recovery claim file present" in text
    assert "stale lock from another host" in text
    assert "operator review" in text
    assert "Pending interrupted loads are recovered before a new load is selected" not in text
    assert "Re-run `/load`; pending transactions are recovered before new selection" not in text


def test_session_id_sourced_from_claude_session_id_not_write_time_uuid() -> None:
    for name in ("save", "summary", "quicksave", "load"):
        text = (PLUGIN_ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
        assert "${CLAUDE_SESSION_ID}" in text, name
        assert "Generate a fresh UUID for `session_id`" not in text, name
        assert "Generate a fresh UUID for this checkpoint" not in text, name


def test_resume_token_spine_unchanged() -> None:
    contract = (PLUGIN_ROOT / "references" / "handoff-contract.md").read_text("utf-8")
    assert "handoff-<project>-<resume_token>.json" in contract  # Codex spine kept verbatim


def test_defer_skill_uses_plugin_siblings_plain_field() -> None:
    text = (PLUGIN_ROOT / "skills" / "defer" / "SKILL.md").read_text(encoding="utf-8")
    assert (
        'plugin_siblings.py" --plugin-root "$PLUGIN_ROOT" --sibling ticket --field plugin_root'
    ) in text
    assert (
        'python "$PLUGIN_ROOT/scripts/defer.py" --tickets-dir "$PROJECT_ROOT/docs/tickets"'
    ) in text
    assert (
        "python3 /absolute/ticket/root/scripts/ticket_engine_user.py ingest "
        '"$PROJECT_ROOT/.claude/ticket-tmp/payload-' in text
    )
    assert "relative payload path" in text
    assert "$TICKET_PLUGIN_ROOT" not in text
    assert "/tmp/ingest_payload.json" not in text
    assert "../../../../ticket/" not in text
    assert "ticket/1.4.0/scripts" not in text
