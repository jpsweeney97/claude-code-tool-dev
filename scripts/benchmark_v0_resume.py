#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


RUN_ID_RE = re.compile(r"^(?P<date>\d{4}-\d{2}-\d{2})_benchmark-v0_(?P<slug>.+)$")
RUBRIC_RUN_RECORD_RE = re.compile(
    r"^(?P<scenario>v0-[\w-]+)__(?P<condition>[\w-]+)__(?P<replicate>run-\d)\.md$"
)


@dataclass(frozen=True)
class PlannedRun:
    scenario_id: str
    condition: str
    replicate: str

    @property
    def filename(self) -> str:
        return f"{self.scenario_id}__{self.condition}__{self.replicate}.md"


def _iter_run_dirs(runs_root: Path) -> Iterable[Path]:
    for child in runs_root.iterdir():
        if not child.is_dir():
            continue
        if RUN_ID_RE.match(child.name):
            yield child


def _latest_run_dir(runs_root: Path) -> Path:
    run_dirs = sorted(_iter_run_dirs(runs_root), key=lambda p: p.name)
    if not run_dirs:
        raise SystemExit(
            f"resume failed: no benchmark-v0 run dirs found. Got: {str(runs_root)!r}"
        )
    return run_dirs[-1]


def _extract_planned_runs_from_suite(suite_text: str) -> list[PlannedRun]:
    # Minimal deterministic parsing for Benchmark v0 v0.1.0:
    # We use the “Scenario-by-scenario matrix” table with N=3/N=1 markers.
    scenario_rows = re.findall(
        r"^\|\s*`(?P<scenario>v0-[^`]+)`\s*\|\s*(?P<row>.+)\|$", suite_text, flags=re.M
    )
    if not scenario_rows:
        raise SystemExit(
            "resume failed: could not locate scenario-by-scenario matrix rows in suite spec."
        )

    # Header order from suite spec table:
    # | scenario_id | baseline | target | placebo | irrelevant | harmful (no tools) | harmful (brevity) | proxy-gaming |
    # Rows are like: | `id` | N=3 | N=3 | — | — | N=1 | — | — |
    def parse_cell(cell: str) -> int:
        cell = cell.strip()
        if cell.startswith("N="):
            return int(cell.split("=", 1)[1])
        return 0

    planned: list[PlannedRun] = []
    for scenario_id, row in scenario_rows:
        cells = [c.strip() for c in row.split("|")]
        if len(cells) < 7:
            continue
        baseline_n = parse_cell(cells[0])
        target_n = parse_cell(cells[1])
        placebo_n = parse_cell(cells[2])
        irrelevant_n = parse_cell(cells[3])
        harmful_no_tools_n = parse_cell(cells[4])
        harmful_brevity_n = parse_cell(cells[5])
        proxy_gaming_n = parse_cell(cells[6])

        def add_runs(condition: str, n: int) -> None:
            for i in range(1, n + 1):
                planned.append(
                    PlannedRun(
                        scenario_id=scenario_id,
                        condition=condition,
                        replicate=f"run-{i}",
                    )
                )

        add_runs("baseline", baseline_n)
        add_runs("target", target_n)
        add_runs("placebo", placebo_n)
        add_runs("irrelevant", irrelevant_n)
        add_runs("harmful_no_tools", harmful_no_tools_n)
        add_runs("harmful_brevity_60w", harmful_brevity_n)
        add_runs("proxy_gaming", proxy_gaming_n)

    return planned


def _extract_output_section(text: str) -> str:
    match = re.search(r"^## Output\s*\n(.*?)(?=^##\s|\Z)", text, flags=re.M | re.S)
    return match.group(1).strip() if match else ""


def _is_executed_run_record(run_record_path: Path) -> bool:
    text = run_record_path.read_text()
    output = _extract_output_section(text)
    if not output:
        return False
    lower = output.lower()
    if (
        "empty stub" in lower
        or "not executed" in lower
        or "raw output or pointer to artifact" in lower
    ):
        return False
    # Heuristic: at least some substantial content
    return len(output.split()) > 30


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Resume helper for Benchmark v0 orchestration."
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help=(
            "Repo root. If omitted, auto-detect by walking upward from CWD, then from this script's directory, "
            "until a known suite marker is found."
        ),
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Explicit run id. If omitted, picks most recent docs/benchmarks/runs/YYYY-MM-DD_benchmark-v0_*/.",
    )
    args = parser.parse_args()

    def autodetect_repo_root(start: Path, script_dir: Path) -> Path:
        suite_markers = [
            Path("docs/benchmarks/suites/benchmark-v0_v0.1.0.md"),
            Path("docs/benchmarks/suites/benchmark-v0.md"),
        ]

        # Prefer the script location first so invoking the wrapper by absolute path works from any CWD.
        search_starts = [script_dir, start]

        visited: set[Path] = set()
        for root_start in search_starts:
            for candidate in [root_start, *root_start.parents]:
                if candidate in visited:
                    continue
                visited.add(candidate)
                for marker in suite_markers:
                    suite_candidate = candidate / marker
                    if suite_candidate.exists():
                        return candidate
        raise SystemExit(
            "resume failed: could not auto-detect repo root. "
            f"Started at: {str(start)!r}. "
            f"Script dir: {str(script_dir)!r}. "
            "Expected to find: one of the known benchmark suite markers in a parent directory."
        )

    repo_root = (
        Path(args.repo_root).resolve()
        if args.repo_root
        else autodetect_repo_root(Path.cwd().resolve(), Path(__file__).resolve().parent)
    )
    suite_candidates = [
        repo_root / "docs/benchmarks/suites/benchmark-v0_v0.1.0.md",
        repo_root / "docs/benchmarks/suites/benchmark-v0.md",
    ]
    suite_path = next(
        (candidate for candidate in suite_candidates if candidate.exists()), None
    )
    runs_root = repo_root / "docs/benchmarks/runs"

    if suite_path is None:
        raise SystemExit(
            "resume failed: suite spec missing. "
            f"Checked: {[str(path) for path in suite_candidates]!r}"
        )

    if not runs_root.exists():
        raise SystemExit(f"resume failed: runs root missing. Got: {str(runs_root)!r}")

    run_dir = (runs_root / args.run_id) if args.run_id else _latest_run_dir(runs_root)
    run_id = run_dir.name
    run_records_dir = run_dir / "run-records"
    if not run_records_dir.exists():
        raise SystemExit(
            f"resume failed: run-records dir missing. Got: {str(run_records_dir)!r}"
        )

    suite_text = suite_path.read_text()
    planned = _extract_planned_runs_from_suite(suite_text)

    executed: set[str] = set()
    for planned_run in planned:
        path = run_records_dir / planned_run.filename
        if path.exists() and _is_executed_run_record(path):
            executed.add(planned_run.filename)

    remaining = [r for r in planned if r.filename not in executed]

    print(f"repo_root: {repo_root}")
    print(f"run_id: {run_id}")
    print(f"run_records_dir: {run_records_dir}")
    print(f"planned_runs: {len(planned)}")
    print(f"executed_runs: {len(executed)}")
    print(f"remaining_runs: {len(remaining)}")
    print("")

    if remaining:
        next_run = remaining[0]
        print("next_action: execute_one_run")
        print(f"scenario_id: {next_run.scenario_id}")
        print(f"condition: {next_run.condition}")
        print(f"replicate: {next_run.replicate}")
        print(
            f"run_record_stub: docs/benchmarks/runs/{run_id}/run-records/{next_run.filename}"
        )
    else:
        print("next_action: blinded_scoring_and_report_updates")
        print(f"blinded_packet_cmd: ./scripts/blinded_eval_packet.py --run-id {run_id}")
        print(
            f"blinded_packet_verify_cmd: ./scripts/blinded_eval_packet.py --run-id {run_id} --verify-only"
        )
        print(
            f"blinded_packet_share: docs/benchmarks/runs/{run_id}/blinded_eval/blinded_eval_packet.md"
        )
        print(f"blinded_scores_out: docs/benchmarks/runs/{run_id}/blinded_scores.md")
        print(f"scores_md: docs/benchmarks/runs/{run_id}/scores.md")
        print(f"report_md: docs/benchmarks/runs/{run_id}/report.md")

    print("")
    print("preflight_cmd: git diff -- packages/mcp-servers/claude-code-docs/")


if __name__ == "__main__":
    main()
