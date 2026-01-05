"""Tests for task storage module."""

import json
from pathlib import Path

import pytest

from persistent_tasks.storage import Task, TaskStore, TaskStatus, Priority


class TestTaskStoreInit:
    """Tests for TaskStore initialization."""

    def test_creates_file_if_not_exists(self, tmp_path: Path) -> None:
        """Store creates tasks.json if missing."""
        tasks_file = tmp_path / "tasks.json"
        store = TaskStore(tasks_file)

        assert tasks_file.exists()
        data = json.loads(tasks_file.read_text())
        assert data["tasks"] == []
        assert "meta" in data

    def test_loads_existing_file(self, tmp_path: Path) -> None:
        """Store loads existing tasks from file."""
        tasks_file = tmp_path / "tasks.json"
        tasks_file.write_text(json.dumps({
            "tasks": [{"id": 1, "title": "Test", "status": "pending", "priority": "medium", "dependencies": [], "description": ""}],
            "meta": {"nextId": 2, "project": "test"}
        }))

        store = TaskStore(tasks_file)
        assert len(store.tasks) == 1
        assert store.tasks[0].title == "Test"


class TestAddTask:
    """Tests for adding tasks."""

    def test_add_task_assigns_id(self, tmp_path: Path) -> None:
        """Adding a task auto-assigns sequential ID."""
        store = TaskStore(tmp_path / "tasks.json")

        task = store.add_task("First task")
        assert task.id == 1

        task2 = store.add_task("Second task")
        assert task2.id == 2

    def test_add_task_persists(self, tmp_path: Path) -> None:
        """Added tasks persist to file."""
        tasks_file = tmp_path / "tasks.json"
        store = TaskStore(tasks_file)
        store.add_task("Persisted task")

        # Reload from file
        store2 = TaskStore(tasks_file)
        assert len(store2.tasks) == 1
        assert store2.tasks[0].title == "Persisted task"

    def test_add_task_with_options(self, tmp_path: Path) -> None:
        """Can specify priority, dependencies, description."""
        store = TaskStore(tmp_path / "tasks.json")
        task = store.add_task(
            "Complex task",
            priority=Priority.HIGH,
            dependencies=[],
            description="Detailed description"
        )

        assert task.priority == Priority.HIGH
        assert task.description == "Detailed description"

    def test_add_task_rejects_nonexistent_dependency(self, tmp_path: Path) -> None:
        """Cannot depend on task that doesn't exist."""
        store = TaskStore(tmp_path / "tasks.json")

        with pytest.raises(ValueError, match="does not exist"):
            store.add_task("Task 1", dependencies=[99])

    def test_add_task_accepts_valid_dependencies(self, tmp_path: Path) -> None:
        """Valid dependency chains are allowed."""
        store = TaskStore(tmp_path / "tasks.json")
        t1 = store.add_task("Task 1")
        t2 = store.add_task("Task 2", dependencies=[t1.id])
        t3 = store.add_task("Task 3", dependencies=[t1.id, t2.id])

        assert t3.dependencies == [1, 2]


class TestUpdateTask:
    """Tests for updating tasks."""

    def test_update_status(self, tmp_path: Path) -> None:
        """Can update task status."""
        store = TaskStore(tmp_path / "tasks.json")
        t = store.add_task("Task")

        store.update_task(t.id, status=TaskStatus.IN_PROGRESS)
        assert store.get_task(t.id).status == TaskStatus.IN_PROGRESS

    def test_update_priority(self, tmp_path: Path) -> None:
        """Can update task priority."""
        store = TaskStore(tmp_path / "tasks.json")
        t = store.add_task("Task")

        store.update_task(t.id, priority=Priority.HIGH)
        assert store.get_task(t.id).priority == Priority.HIGH

    def test_update_title(self, tmp_path: Path) -> None:
        """Can update task title."""
        store = TaskStore(tmp_path / "tasks.json")
        t = store.add_task("Old title")

        store.update_task(t.id, title="New title")
        assert store.get_task(t.id).title == "New title"

    def test_update_persists(self, tmp_path: Path) -> None:
        """Updates persist to file."""
        tasks_file = tmp_path / "tasks.json"
        store = TaskStore(tasks_file)
        t = store.add_task("Task")
        store.update_task(t.id, status=TaskStatus.DONE)

        # Reload
        store2 = TaskStore(tasks_file)
        assert store2.get_task(t.id).status == TaskStatus.DONE

    def test_update_nonexistent_returns_none(self, tmp_path: Path) -> None:
        """Updating nonexistent task returns None."""
        store = TaskStore(tmp_path / "tasks.json")
        assert store.update_task(999, status=TaskStatus.DONE) is None

    def test_update_dependencies_validates_existence(self, tmp_path: Path) -> None:
        """Cannot update dependencies to include nonexistent task."""
        store = TaskStore(tmp_path / "tasks.json")
        t = store.add_task("Task")

        with pytest.raises(ValueError, match="does not exist"):
            store.update_task(t.id, dependencies=[99])

    def test_update_dependencies_rejects_self_reference(self, tmp_path: Path) -> None:
        """Cannot add self as dependency."""
        store = TaskStore(tmp_path / "tasks.json")
        t = store.add_task("Task")

        with pytest.raises(ValueError, match="self-reference"):
            store.update_task(t.id, dependencies=[t.id])

    def test_update_dependencies_rejects_cycle(self, tmp_path: Path) -> None:
        """Cannot create circular dependencies."""
        store = TaskStore(tmp_path / "tasks.json")
        t1 = store.add_task("Task 1")
        t2 = store.add_task("Task 2", dependencies=[t1.id])

        # Try to make t1 depend on t2 (creates cycle: t1 -> t2 -> t1)
        with pytest.raises(ValueError, match="cycle"):
            store.update_task(t1.id, dependencies=[t2.id])

    def test_update_dependencies_rejects_indirect_cycle(self, tmp_path: Path) -> None:
        """Cannot create indirect circular dependencies."""
        store = TaskStore(tmp_path / "tasks.json")
        t1 = store.add_task("Task 1")
        t2 = store.add_task("Task 2", dependencies=[t1.id])
        t3 = store.add_task("Task 3", dependencies=[t2.id])

        # Try to make t1 depend on t3 (creates cycle: t1 -> t3 -> t2 -> t1)
        with pytest.raises(ValueError, match="cycle"):
            store.update_task(t1.id, dependencies=[t3.id])


class TestFindNextTask:
    """Tests for intelligent next task selection."""

    def test_returns_none_when_empty(self, tmp_path: Path) -> None:
        """Returns None when no tasks exist."""
        store = TaskStore(tmp_path / "tasks.json")
        assert store.find_next_task() is None

    def test_returns_none_when_all_done(self, tmp_path: Path) -> None:
        """Returns None when all tasks are done."""
        store = TaskStore(tmp_path / "tasks.json")
        t = store.add_task("Done task")
        store.update_task(t.id, status=TaskStatus.DONE)

        assert store.find_next_task() is None

    def test_prioritizes_high_over_medium(self, tmp_path: Path) -> None:
        """High priority tasks come first."""
        store = TaskStore(tmp_path / "tasks.json")
        store.add_task("Medium task", priority=Priority.MEDIUM)
        store.add_task("High task", priority=Priority.HIGH)
        store.add_task("Low task", priority=Priority.LOW)

        next_task = store.find_next_task()
        assert next_task.title == "High task"

    def test_fewer_deps_wins_at_same_priority(self, tmp_path: Path) -> None:
        """Among same priority, fewer dependencies wins."""
        store = TaskStore(tmp_path / "tasks.json")
        t1 = store.add_task("Base task")
        store.update_task(t1.id, status=TaskStatus.DONE)

        store.add_task("One dep", priority=Priority.MEDIUM, dependencies=[t1.id])
        store.add_task("No deps", priority=Priority.MEDIUM)

        next_task = store.find_next_task()
        assert next_task.title == "No deps"

    def test_blocked_tasks_excluded(self, tmp_path: Path) -> None:
        """Tasks with incomplete dependencies are skipped."""
        store = TaskStore(tmp_path / "tasks.json")
        t1 = store.add_task("Blocker", priority=Priority.LOW)
        store.add_task("Blocked", priority=Priority.HIGH, dependencies=[t1.id])

        # Even though "Blocked" is high priority, it's blocked by t1
        next_task = store.find_next_task()
        assert next_task.title == "Blocker"

    def test_in_progress_tasks_returned_first(self, tmp_path: Path) -> None:
        """In-progress tasks have priority over pending."""
        store = TaskStore(tmp_path / "tasks.json")
        store.add_task("Pending high", priority=Priority.HIGH)
        t2 = store.add_task("In progress low", priority=Priority.LOW)
        store.update_task(t2.id, status=TaskStatus.IN_PROGRESS)

        next_task = store.find_next_task()
        assert next_task.title == "In progress low"

    def test_lower_id_breaks_tie(self, tmp_path: Path) -> None:
        """Lower ID wins when priority and deps are equal."""
        store = TaskStore(tmp_path / "tasks.json")
        store.add_task("First")
        store.add_task("Second")

        next_task = store.find_next_task()
        assert next_task.title == "First"


class TestMarkDone:
    """Tests for marking tasks complete."""

    def test_mark_done_changes_status(self, tmp_path: Path) -> None:
        """Marking done updates status to done."""
        store = TaskStore(tmp_path / "tasks.json")
        t = store.add_task("Task to complete")

        store.mark_done(t.id)
        assert store.get_task(t.id).status == TaskStatus.DONE

    def test_mark_done_unblocks_dependents(self, tmp_path: Path) -> None:
        """Completing a task unblocks its dependents."""
        store = TaskStore(tmp_path / "tasks.json")
        t1 = store.add_task("Blocker")
        t2 = store.add_task("Dependent", dependencies=[t1.id])

        # Before: t2 is blocked
        assert store.is_blocked(t2)

        store.mark_done(t1.id)

        # After: t2 is unblocked
        assert not store.is_blocked(store.get_task(t2.id))

    def test_mark_done_returns_task(self, tmp_path: Path) -> None:
        """mark_done returns the updated task."""
        store = TaskStore(tmp_path / "tasks.json")
        t = store.add_task("Task")

        result = store.mark_done(t.id)
        assert result.id == t.id
        assert result.status == TaskStatus.DONE

    def test_mark_done_nonexistent_returns_none(self, tmp_path: Path) -> None:
        """Marking nonexistent task returns None."""
        store = TaskStore(tmp_path / "tasks.json")
        assert store.mark_done(999) is None


class TestRemoveTask:
    """Tests for removing tasks."""

    def test_remove_task_deletes(self, tmp_path: Path) -> None:
        """Removing a task deletes it from store."""
        store = TaskStore(tmp_path / "tasks.json")
        t = store.add_task("To delete")

        result = store.remove_task(t.id)
        assert result is True
        assert store.get_task(t.id) is None

    def test_remove_task_persists(self, tmp_path: Path) -> None:
        """Removal persists to file."""
        tasks_file = tmp_path / "tasks.json"
        store = TaskStore(tasks_file)
        t = store.add_task("To delete")
        store.remove_task(t.id)

        # Reload
        store2 = TaskStore(tasks_file)
        assert store2.get_task(t.id) is None

    def test_remove_nonexistent_returns_false(self, tmp_path: Path) -> None:
        """Removing nonexistent task returns False."""
        store = TaskStore(tmp_path / "tasks.json")
        assert store.remove_task(999) is False

    def test_remove_clears_from_dependents(self, tmp_path: Path) -> None:
        """Removing a task clears it from dependents' dependency lists."""
        store = TaskStore(tmp_path / "tasks.json")
        t1 = store.add_task("Will be removed")
        t2 = store.add_task("Depends on t1", dependencies=[t1.id])

        store.remove_task(t1.id)

        # t2 should no longer list t1 as dependency
        assert t1.id not in store.get_task(t2.id).dependencies

    def test_remove_with_multiple_dependents(self, tmp_path: Path) -> None:
        """Removing task clears from all dependents."""
        store = TaskStore(tmp_path / "tasks.json")
        t1 = store.add_task("Base")
        t2 = store.add_task("Will be removed", dependencies=[t1.id])
        t3 = store.add_task("Depends on t2", dependencies=[t2.id])
        t4 = store.add_task("Also depends on t2", dependencies=[t1.id, t2.id])

        store.remove_task(t2.id)

        assert t2.id not in store.get_task(t3.id).dependencies
        assert t2.id not in store.get_task(t4.id).dependencies
        assert t1.id in store.get_task(t4.id).dependencies  # t1 still there


class TestTaskValidation:
    """Tests for Task dataclass validation."""

    def test_rejects_negative_id(self) -> None:
        """Task ID must be positive."""
        with pytest.raises(ValueError, match="positive integer"):
            Task(id=-1, title="Test")

    def test_rejects_zero_id(self) -> None:
        """Task ID must be positive (not zero)."""
        with pytest.raises(ValueError, match="positive integer"):
            Task(id=0, title="Test")

    def test_rejects_empty_title(self) -> None:
        """Task title must be non-empty."""
        with pytest.raises(ValueError, match="non-empty string"):
            Task(id=1, title="")

    def test_rejects_whitespace_only_title(self) -> None:
        """Task title must have non-whitespace content."""
        with pytest.raises(ValueError, match="non-empty string"):
            Task(id=1, title="   ")

    def test_rejects_non_list_dependencies(self) -> None:
        """Dependencies must be a list."""
        with pytest.raises(ValueError, match="must be a list"):
            Task(id=1, title="Test", dependencies="not a list")  # type: ignore

    def test_rejects_non_int_dependency(self) -> None:
        """Dependency IDs must be integers."""
        with pytest.raises(ValueError, match="must be integers"):
            Task(id=1, title="Test", dependencies=["not", "ints"])  # type: ignore


class TestCorruptFileHandling:
    """Tests for handling corrupt or invalid task files."""

    def test_corrupt_json_raises_runtime_error(self, tmp_path: Path) -> None:
        """Corrupt JSON file raises RuntimeError with clear message."""
        tasks_file = tmp_path / "tasks.json"
        tasks_file.write_text("{ invalid json }")

        with pytest.raises(RuntimeError, match="Failed to parse"):
            TaskStore(tasks_file)

    def test_invalid_task_data_raises_runtime_error(self, tmp_path: Path) -> None:
        """Invalid task data raises RuntimeError with clear message."""
        tasks_file = tmp_path / "tasks.json"
        # Missing required 'id' field
        tasks_file.write_text(json.dumps({
            "tasks": [{"title": "Missing ID"}],
            "meta": {"nextId": 1}
        }))

        with pytest.raises(RuntimeError, match="Invalid task data"):
            TaskStore(tasks_file)

    def test_invalid_status_enum_raises_runtime_error(self, tmp_path: Path) -> None:
        """Invalid status enum value raises RuntimeError."""
        tasks_file = tmp_path / "tasks.json"
        tasks_file.write_text(json.dumps({
            "tasks": [{"id": 1, "title": "Test", "status": "invalid-status"}],
            "meta": {"nextId": 2}
        }))

        with pytest.raises(RuntimeError, match="Invalid task data"):
            TaskStore(tasks_file)

    def test_atomic_write_leaves_no_temp_file(self, tmp_path: Path) -> None:
        """Atomic write cleans up temp file after success."""
        tasks_file = tmp_path / "tasks.json"
        temp_file = tmp_path / "tasks.tmp"

        store = TaskStore(tasks_file)
        store.add_task("Test task")

        assert tasks_file.exists()
        assert not temp_file.exists()
