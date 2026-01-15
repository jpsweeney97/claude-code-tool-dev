"""Single-threaded orchestrator for ecosystem-builder runs."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable

from lib.agents import AgentPanel
from lib.builder import SkillBuilder
from lib.logging import EventLogger
from lib.staging import StagingManager
from lib.state import RunManifest
from lib.validator import ValidationPanel


class Orchestrator:
    """Orchestrates a single ecosystem-builder run."""

    def __init__(
        self,
        manifest: RunManifest,
        staging_dir: Path | None = None,
        user_skills_dir: Path | None = None,
        plugins_dir: Path | None = None,
        subagent_callable: Callable[[str], str] | None = None,
    ) -> None:
        self.manifest = manifest
        self.logger = EventLogger(manifest.run_dir / "log.jsonl")
        self.staging = StagingManager(staging_dir=staging_dir)
        self.build_queue: list[dict[str, Any]] = []

        # Ecosystem paths
        if user_skills_dir is None:
            user_skills_dir = Path.home() / ".claude" / "skills"
        if plugins_dir is None:
            plugins_dir = Path.home() / ".claude" / "plugins"

        self.agent_panel = AgentPanel(
            user_skills_dir=user_skills_dir,
            plugins_dir=plugins_dir,
        )
        self.builder = SkillBuilder(subagent_callable=subagent_callable)
        self.validator = ValidationPanel(existing_skills_dir=user_skills_dir)

        if subagent_callable is None:
            logging.warning(
                "No subagent_callable configured - complex skill generation will fail. "
                "Use --mock flag or configure Claude Code callable for full functionality."
            )

    def run(self) -> None:
        """Execute the main control loop."""
        self.logger.log("run_started", {
            "run_id": self.manifest.run_id,
            "budget": {
                "artifacts": self.manifest.budget.artifacts.limit,
                "hours": self.manifest.budget.hours.limit,
            },
        })

        try:
            # Phase 1: Analyze
            gaps = self._analyze()
            self.manifest.progress.analyzed = len(gaps)
            self.manifest.save()

            self.logger.log("gap_analyzed", {"count": len(gaps)})

            # Phase 2: Propose (populate build queue)
            self.build_queue = self._prioritize(gaps)

            # Phase 3-5: Build -> Validate -> Stage loop
            while self.build_queue and not self.manifest.budget.any_exhausted:
                gap = self.build_queue.pop(0)

                # Build
                artifact = self._build(gap)
                if artifact is None:
                    continue

                self.manifest.progress.built += 1
                self.logger.log("artifact_built", {
                    "name": artifact["name"],
                    "gap_id": gap.get("gap_id"),
                })

                # Validate
                passed = self._validate(artifact)

                if passed:
                    # Stage
                    self.staging.stage_skill(
                        name=artifact["name"],
                        content=artifact["content"],
                        run_id=self.manifest.run_id,
                        gap_id=gap.get("gap_id", "unknown"),
                    )
                    self.manifest.progress.passed += 1
                    self.logger.log("artifact_staged", {"name": artifact["name"]})
                else:
                    self.manifest.progress.failed += 1
                    self.logger.log("artifact_rejected", {"name": artifact["name"]})

                # Update budget
                self.manifest.budget.artifacts.used += 1
                self.manifest.save()

            # Complete
            self.manifest.status = "complete"
            if self.manifest.budget.any_exhausted:
                self.manifest.completion_reason = "budget_exhausted"
            else:
                self.manifest.completion_reason = "queue_empty"

        except Exception as e:
            self.manifest.status = "failed"
            self.manifest.completion_reason = f"{type(e).__name__}: {e}"
            self.logger.log("run_failed", {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "run_id": self.manifest.run_id,
                "progress": asdict(self.manifest.progress),
            })
            raise

        finally:
            self.manifest.save()
            self.logger.log("run_complete", {
                "status": self.manifest.status,
                "reason": self.manifest.completion_reason,
                "progress": {
                    "analyzed": self.manifest.progress.analyzed,
                    "built": self.manifest.progress.built,
                    "passed": self.manifest.progress.passed,
                    "failed": self.manifest.progress.failed,
                },
            })

    def _analyze(self) -> list[dict[str, Any]]:
        """Analyze ecosystem for gaps using agent panel."""
        results = self.agent_panel.run_all_agents()
        gaps = self.agent_panel.merge_gaps(results)

        # Convert to dicts and save
        gap_dicts = [g.to_dict() for g in gaps]

        opportunities_file = self.manifest.run_dir / "opportunities.json"
        opportunities_file.write_text(json.dumps(gap_dicts, indent=2))

        return gap_dicts

    def _prioritize(self, gaps: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Prioritize gaps for building. Override in subclass or mock."""
        # Already sorted by priority in merge_gaps
        return gaps

    def _build(self, gap: dict[str, Any]) -> dict[str, Any] | None:
        """Build an artifact for a gap using SkillBuilder."""
        result = self.builder.build(gap)

        if not result.success:
            self.logger.log("build_failed", {
                "gap_id": gap.get("gap_id"),
                "error": result.error,
            })
            return None

        return {
            "name": result.name,
            "content": result.content,
            "method": result.method,
        }

    def _validate(self, artifact: dict[str, Any]) -> bool:
        """Validate an artifact using ValidationPanel."""
        result = self.validator.validate(
            name=artifact["name"],
            content=artifact["content"],
        )

        if not result.passed:
            for check in result.failed_checks:
                self.logger.log("validation_failed", {
                    "artifact": artifact["name"],
                    "check": check.name,
                    "issues": check.issues,
                })

        return result.passed
