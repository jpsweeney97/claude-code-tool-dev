"""Tests for _common module."""
import json
import sys
from pathlib import Path

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_result_success():
    """Result.success() creates success result."""
    from _common import Result

    result = Result.success("Operation completed", data={"key": "value"})
    assert result.ok is True
    assert result.message == "Operation completed"
    assert result.data == {"key": "value"}
    assert result.errors == []


def test_result_failure():
    """Result.failure() creates failure result."""
    from _common import Result

    result = Result.failure("Something failed", errors=["Error 1"])
    assert result.ok is False
    assert result.message == "Something failed"
    assert result.errors == ["Error 1"]


def test_result_to_json():
    """Result.to_json() produces valid JSON."""
    from _common import Result

    result = Result.success("Done", data={"count": 5})
    output = result.to_json()
    parsed = json.loads(output)
    assert parsed["ok"] is True
    assert parsed["data"]["count"] == 5


def test_atomic_write_creates_file(tmp_path):
    """atomic_write creates file with content."""
    from _common import atomic_write

    target = tmp_path / "test.json"
    content = '{"key": "value"}'

    atomic_write(target, content)

    assert target.exists()
    assert target.read_text() == content


def test_atomic_write_overwrites_existing(tmp_path):
    """atomic_write replaces existing file atomically."""
    from _common import atomic_write

    target = tmp_path / "test.json"
    target.write_text("old content")

    atomic_write(target, "new content")

    assert target.read_text() == "new content"


def test_get_state_path():
    """get_state_path returns adjacent .audit.json path."""
    from _common import get_state_path

    result = get_state_path(Path("docs/plans/feature.md"))
    assert result == Path("docs/plans/feature.audit.json")


def test_get_archive_path():
    """get_archive_path includes date in filename."""
    from _common import get_archive_path

    result = get_archive_path(Path("docs/plans/feature.md"), "2026-01-06")
    assert result == Path("docs/plans/feature.audit.2026-01-06.json")


def test_get_report_path():
    """get_report_path generates dated report path."""
    from _common import get_report_path

    result = get_report_path(Path("docs/plans/feature.md"), "2026-01-06")
    assert result == Path("docs/plans/feature.audit-report.2026-01-06.md")
