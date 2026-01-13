"""Task storage with JSON persistence."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class TaskStatus(str, Enum):
    """Task status values."""
    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    REVIEW = "review"
    DONE = "done"
    DEFERRED = "deferred"
    CANCELLED = "cancelled"


class Priority(str, Enum):
    """Task priority values."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Task:
    """A task with dependencies."""
    id: int
    title: str
    status: TaskStatus = TaskStatus.PENDING
    priority: Priority = Priority.MEDIUM
    dependencies: list[int] = field(default_factory=list)
    description: str = ""

    def __post_init__(self) -> None:
        """Validate task fields after initialization."""
        if not isinstance(self.id, int) or self.id < 1:
            raise ValueError(f"Task id must be a positive integer, got: {self.id!r}")
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError(f"Task title must be a non-empty string, got: {self.title!r}")
        if not isinstance(self.dependencies, list):
            raise ValueError(f"Task dependencies must be a list, got: {type(self.dependencies).__name__}")
        for dep in self.dependencies:
            if not isinstance(dep, int):
                raise ValueError(f"Dependency IDs must be integers, got: {dep!r}")

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status.value,
            "priority": self.priority.value,
            "dependencies": self.dependencies,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        """Create Task from dict."""
        return cls(
            id=data["id"],
            title=data["title"],
            status=TaskStatus(data.get("status", "pending")),
            priority=Priority(data.get("priority", "medium")),
            dependencies=data.get("dependencies", []),
            description=data.get("description", ""),
        )


def get_tasks_file() -> Path:
    """Get the tasks file path for current project.

    Resolution order:
    1. Project-local: .claude/tasks/tasks.json (if exists)
    2. Global: ~/.claude/tasks/tasks.json
    """
    local = Path.cwd() / ".claude" / "tasks" / "tasks.json"
    if local.exists():
        return local
    return Path.home() / ".claude" / "tasks" / "tasks.json"


@dataclass
class TaskStore:
    """Persistent task storage backed by JSON file."""
    path: Path
    tasks: list[Task] = field(default_factory=list)
    meta: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Load or initialize storage."""
        self.path = Path(self.path)
        if self.path.exists():
            self._load()
        else:
            self._initialize()

    def _initialize(self) -> None:
        """Create empty task file."""
        self.meta = {
            "nextId": 1,
            "project": self.path.parent.parent.name,
            "created": datetime.now().isoformat()
        }
        self._save()

    def _load(self) -> None:
        """Load tasks from file.

        Raises:
            RuntimeError: If file cannot be read or contains invalid JSON/data.
        """
        try:
            text = self.path.read_text()
        except OSError as e:
            raise RuntimeError(
                f"Failed to read tasks from {self.path}: {e}. "
                "Check file permissions or delete the file to start fresh."
            ) from e

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Failed to parse tasks from {self.path}: {e}. "
                "Fix the JSON syntax or delete the file to start fresh."
            ) from e

        try:
            self.tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
        except (KeyError, ValueError, TypeError) as e:
            raise RuntimeError(
                f"Invalid task data in {self.path}: {e}. "
                "Fix the task data or delete the file to start fresh."
            ) from e

        self.meta = data.get("meta", {"nextId": 1})

    def _save(self) -> None:
        """Persist tasks to file atomically.

        Writes to a temporary file first, then renames to target.
        This prevents file corruption if the process crashes mid-write.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "tasks": [t.to_dict() for t in self.tasks],
            "meta": self.meta
        }
        # Atomic write: write to temp file, then rename
        temp_path = self.path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(data, indent=2))
        temp_path.replace(self.path)  # atomic on POSIX

    def get_task(self, task_id: int) -> Optional[Task]:
        """Get task by ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def add_task(
        self,
        title: str,
        priority: Priority = Priority.MEDIUM,
        dependencies: Optional[list[int]] = None,
        description: str = "",
    ) -> Task:
        """Add a new task with auto-assigned ID.

        Args:
            title: Task title
            priority: Task priority (default: medium)
            dependencies: List of task IDs this depends on
            description: Optional detailed description

        Returns:
            The created Task

        Raises:
            ValueError: If any dependency ID doesn't exist
        """
        deps = dependencies or []

        # Validate dependencies exist
        if deps:
            existing_ids = {t.id for t in self.tasks}
            for dep_id in deps:
                if dep_id not in existing_ids:
                    raise ValueError(f"Dependency {dep_id} does not exist")

        task = Task(
            id=self.meta["nextId"],
            title=title,
            priority=priority,
            dependencies=deps,
            description=description,
        )
        self.tasks.append(task)
        self.meta["nextId"] += 1
        self._save()
        return task

    def _validate_dependencies(
        self,
        task_id: int,
        dependencies: list[int]
    ) -> None:
        """Validate dependencies for update operation.

        Raises:
            ValueError: If validation fails (self-ref, nonexistent, cycle)
        """
        # Self-reference check
        if task_id in dependencies:
            raise ValueError(f"Task {task_id} cannot have self-reference dependency")

        # Existence check
        existing_ids = {t.id for t in self.tasks}
        for dep_id in dependencies:
            if dep_id not in existing_ids:
                raise ValueError(f"Dependency {dep_id} does not exist")

        # Cycle check: would task_id appear in the dependency chain?
        if self._would_create_cycle(task_id, dependencies):
            raise ValueError("Dependencies would create a cycle")

    def _would_create_cycle(self, task_id: int, new_deps: list[int]) -> bool:
        """Check if setting dependencies would create a cycle.

        A cycle exists if task_id appears anywhere in the transitive
        dependencies of any task in new_deps.
        """
        visited: set[int] = set()

        def has_path_to(from_id: int, to_id: int) -> bool:
            """Check if there's a dependency path from from_id to to_id."""
            if from_id == to_id:
                return True
            if from_id in visited:
                return False
            visited.add(from_id)

            task = self.get_task(from_id)
            if task:
                for dep_id in task.dependencies:
                    if has_path_to(dep_id, to_id):
                        return True
            return False

        # Check if any new dependency has a path back to task_id
        for dep_id in new_deps:
            visited.clear()
            if has_path_to(dep_id, task_id):
                return True
        return False

    def update_task(
        self,
        task_id: int,
        **updates
    ) -> Optional[Task]:
        """Update task fields.

        Args:
            task_id: ID of task to update
            **updates: Fields to update (status, priority, title, description, dependencies)

        Returns:
            Updated task, or None if not found

        Raises:
            ValueError: If dependency validation fails
        """
        task = self.get_task(task_id)
        if not task:
            return None

        if "dependencies" in updates:
            self._validate_dependencies(task_id, updates["dependencies"])
            task.dependencies = updates["dependencies"]

        if "status" in updates:
            status = updates["status"]
            task.status = TaskStatus(status) if isinstance(status, str) else status

        if "priority" in updates:
            priority = updates["priority"]
            task.priority = Priority(priority) if isinstance(priority, str) else priority

        if "title" in updates:
            task.title = updates["title"]

        if "description" in updates:
            task.description = updates["description"]

        self._save()
        return task

    def is_blocked(self, task: Task) -> bool:
        """Check if task is blocked by incomplete dependencies."""
        for dep_id in task.dependencies:
            dep = self.get_task(dep_id)
            if dep and dep.status != TaskStatus.DONE:
                return True
        return False

    def find_next_task(self) -> Optional[Task]:
        """Find the next task to work on.

        Selection algorithm:
        1. Filter to actionable tasks (pending/in-progress, not blocked)
        2. Prioritize in-progress over pending
        3. Sort by priority (high > medium > low)
        4. Then by dependency count (fewer first)
        5. Then by ID (lower first)

        Returns:
            Next task to work on, or None if no actionable tasks
        """
        priority_order = {Priority.HIGH: 3, Priority.MEDIUM: 2, Priority.LOW: 1}

        # Get actionable tasks
        actionable = [
            t for t in self.tasks
            if t.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS)
            and not self.is_blocked(t)
        ]

        if not actionable:
            return None

        # Sort: in-progress first, then priority, then deps, then id
        def sort_key(task: Task) -> tuple:
            in_progress = 0 if task.status == TaskStatus.IN_PROGRESS else 1
            priority = -priority_order[task.priority]  # Negative for descending
            dep_count = len(task.dependencies)
            return (in_progress, priority, dep_count, task.id)

        actionable.sort(key=sort_key)
        return actionable[0]

    def mark_done(self, task_id: int) -> Optional[Task]:
        """Mark a task as done.

        Args:
            task_id: ID of task to mark done

        Returns:
            Updated task, or None if not found
        """
        return self.update_task(task_id, status=TaskStatus.DONE)

    def remove_task(self, task_id: int) -> bool:
        """Remove a task and clean up dependencies.

        Also removes this task from the dependency lists of any
        tasks that depend on it.

        Args:
            task_id: ID of task to remove

        Returns:
            True if removed, False if not found
        """
        task = self.get_task(task_id)
        if not task:
            return False

        # Remove from store
        self.tasks = [t for t in self.tasks if t.id != task_id]

        # Clean up references in other tasks' dependencies
        for t in self.tasks:
            if task_id in t.dependencies:
                t.dependencies = [d for d in t.dependencies if d != task_id]

        self._save()
        return True
