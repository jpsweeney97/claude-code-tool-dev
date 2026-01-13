"""State management for ecosystem-builder runs."""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Literal


def normalize_skill_name(title: str) -> str:
    """Convert a gap title to a valid skill name.

    Examples:
        "Missing testing skill" -> "testing"
        "TDD or testing workflow" -> "tdd-or-testing-workflow"
    """
    name = title.lower().strip()
    name = re.sub(r"^missing\s+", "", name)
    name = re.sub(r"\s+skill$", "", name)
    name = re.sub(r"[^a-z0-9]+", "-", name)
    return name.strip("-")


class GapType(Enum):
    """Types of ecosystem gaps."""

    MISSING_SKILL = "missing_skill"
    INCOMPLETE_ARTIFACT = "incomplete_artifact"
    WORKFLOW_HOLE = "workflow_hole"
    QUALITY_ISSUE = "quality_issue"


@dataclass
class Gap:
    """A detected gap in the ecosystem."""

    gap_id: str
    gap_type: GapType
    title: str
    description: str
    source_agent: str
    confidence: float  # 0.0 to 1.0
    priority: int  # 1 = highest

    def __post_init__(self) -> None:
        if not self.gap_id:
            raise ValueError("Gap.gap_id cannot be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Gap.confidence must be in [0.0, 1.0]. Got: {self.confidence!r}")
        if self.priority < 1:
            raise ValueError(f"Gap.priority must be >= 1. Got: {self.priority!r}")

    def to_dict(self) -> dict:
        """Serialize to dict for JSON storage."""
        return {
            "gap_id": self.gap_id,
            "gap_type": self.gap_type.value,
            "title": self.title,
            "description": self.description,
            "source_agent": self.source_agent,
            "confidence": self.confidence,
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Gap":
        """Deserialize from dict."""
        return cls(
            gap_id=data["gap_id"],
            gap_type=GapType(data["gap_type"]),
            title=data["title"],
            description=data["description"],
            source_agent=data["source_agent"],
            confidence=data["confidence"],
            priority=data["priority"],
        )


@dataclass
class BuildResult:
    """Result of building an artifact."""

    name: str
    gap_id: str
    content: str | None = None
    error: str | None = None
    method: Literal["direct", "subagent"] = "direct"

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("BuildResult.name cannot be empty")
        if self.content is not None and self.error is not None:
            raise ValueError("BuildResult cannot have both content and error set")

    @property
    def success(self) -> bool:
        return self.content is not None and self.error is None

    def to_dict(self) -> dict:
        """Serialize to dict."""
        return {
            "name": self.name,
            "gap_id": self.gap_id,
            "content": self.content,
            "error": self.error,
            "method": self.method,
        }


@dataclass
class ValidationCheck:
    """Result of a single validation check."""

    name: str
    passed: bool
    issues: list[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Result of validation panel."""

    artifact_name: str
    checks: list[ValidationCheck]

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def failed_checks(self) -> list[ValidationCheck]:
        return [c for c in self.checks if not c.passed]


@dataclass
class BudgetItem:
    """A single budget constraint."""

    limit: int | float
    used: int | float = 0

    def __post_init__(self) -> None:
        if self.limit < 0:
            raise ValueError(f"BudgetItem.limit must be non-negative. Got: {self.limit!r}")
        if self.used < 0:
            raise ValueError(f"BudgetItem.used must be non-negative. Got: {self.used!r}")

    @property
    def remaining(self) -> int | float:
        return self.limit - self.used

    @property
    def exhausted(self) -> bool:
        return self.used >= self.limit


@dataclass
class Budget:
    """All budget constraints for a run."""

    artifacts: BudgetItem
    hours: BudgetItem = field(default_factory=lambda: BudgetItem(limit=4.0))
    tokens: BudgetItem = field(default_factory=lambda: BudgetItem(limit=5_000_000))
    cost_usd: BudgetItem = field(default_factory=lambda: BudgetItem(limit=50.0))

    @property
    def any_exhausted(self) -> bool:
        return any([
            self.artifacts.exhausted,
            self.hours.exhausted,
            self.tokens.exhausted,
            self.cost_usd.exhausted,
        ])


@dataclass
class Progress:
    """Progress counters for a run."""

    analyzed: int = 0
    built: int = 0
    passed: int = 0
    failed: int = 0


@dataclass
class RunManifest:
    """Manifest for a single ecosystem-builder run."""

    run_id: str
    started: str
    budget: Budget
    progress: Progress = field(default_factory=Progress)
    status: Literal["running", "complete", "failed"] = "running"
    completion_reason: str | None = None

    _state_dir: Path | None = field(default=None, repr=False, compare=False)

    @property
    def run_dir(self) -> Path:
        if self._state_dir is None:
            raise ValueError("RunManifest not associated with state directory")
        return self._state_dir / self.run_id

    def save(self) -> None:
        """Persist manifest to disk.

        Uses atomic write pattern: write to temp file, then rename.
        Raises RuntimeError on failure with context.
        """
        manifest_path = self.run_dir / "manifest.json"
        temp_path = manifest_path.with_suffix(".tmp")

        data = {
            "run_id": self.run_id,
            "started": self.started,
            "budget": {
                "artifacts": {"limit": self.budget.artifacts.limit, "used": self.budget.artifacts.used},
                "hours": {"limit": self.budget.hours.limit, "used": self.budget.hours.used},
                "tokens": {"limit": self.budget.tokens.limit, "used": self.budget.tokens.used},
                "cost_usd": {"limit": self.budget.cost_usd.limit, "used": self.budget.cost_usd.used},
            },
            "progress": asdict(self.progress),
            "status": self.status,
            "completion_reason": self.completion_reason,
        }

        try:
            temp_path.write_text(json.dumps(data, indent=2))
            temp_path.replace(manifest_path)  # Atomic on POSIX
        except OSError as e:
            # Clean up temp file if it exists
            temp_path.unlink(missing_ok=True)
            raise RuntimeError(
                f"Failed to save manifest to {manifest_path}: {e}"
            ) from e

    @classmethod
    def load(cls, run_dir: Path) -> RunManifest:
        """Load manifest from disk."""
        manifest_path = run_dir / "manifest.json"
        try:
            data = json.loads(manifest_path.read_text())
        except FileNotFoundError:
            raise FileNotFoundError(f"Manifest not found for run at {run_dir}") from None
        except json.JSONDecodeError as e:
            raise ValueError(f"Corrupted manifest at {manifest_path}: {e}") from e
        except OSError as e:
            raise RuntimeError(f"Failed to read manifest from {manifest_path}: {e}") from e

        budget = Budget(
            artifacts=BudgetItem(**data["budget"]["artifacts"]),
            hours=BudgetItem(**data["budget"]["hours"]),
            tokens=BudgetItem(**data["budget"]["tokens"]),
            cost_usd=BudgetItem(**data["budget"]["cost_usd"]),
        )
        progress = Progress(**data["progress"])

        manifest = cls(
            run_id=data["run_id"],
            started=data["started"],
            budget=budget,
            progress=progress,
            status=data["status"],
            completion_reason=data.get("completion_reason"),
        )
        manifest._state_dir = run_dir.parent
        return manifest


class StateManager:
    """Manages ecosystem-builder state directory."""

    def __init__(self, state_dir: Path | None = None) -> None:
        if state_dir is None:
            state_dir = Path.home() / ".claude" / "ecosystem-builder" / "state"
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def create_run(
        self,
        artifact_limit: int,
        hour_limit: float = 4.0,
        token_limit: int = 5_000_000,
        cost_limit: float = 50.0,
    ) -> RunManifest:
        """Create a new run with the given budget."""
        now = datetime.now(timezone.utc)
        run_id = f"run-{now.strftime('%Y-%m-%d')}-{uuid.uuid4().hex[:6]}"

        budget = Budget(
            artifacts=BudgetItem(limit=artifact_limit),
            hours=BudgetItem(limit=hour_limit),
            tokens=BudgetItem(limit=token_limit),
            cost_usd=BudgetItem(limit=cost_limit),
        )

        manifest = RunManifest(
            run_id=run_id,
            started=now.isoformat(),
            budget=budget,
        )
        manifest._state_dir = self.state_dir

        # Create run directory
        run_dir = self.state_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # Create empty files
        (run_dir / "opportunities.json").write_text("[]")
        (run_dir / "build-queue.json").write_text("[]")
        (run_dir / "log.jsonl").write_text("")

        # Save manifest
        manifest.save()

        # Update current symlink
        current = self.state_dir / "current"
        if current.is_symlink():
            current.unlink()
        current.symlink_to(run_id)

        return manifest

    def load_run(self, run_id: str) -> RunManifest:
        """Load an existing run."""
        run_dir = self.state_dir / run_id
        if not run_dir.exists():
            raise FileNotFoundError(f"Run not found: {run_id}")
        return RunManifest.load(run_dir)

    def load_current(self) -> RunManifest | None:
        """Load the current active run, if any."""
        current = self.state_dir / "current"
        if not current.exists():
            return None
        return self.load_run(current.resolve().name)
