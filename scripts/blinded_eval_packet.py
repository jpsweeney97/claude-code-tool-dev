#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


CONDITION_WORDS_RE = re.compile(
    r"\b(baseline|target|placebo|proxy|harmful|control)\b", re.I
)
FILENAME_CONDITION_TOKENS_RE = re.compile(
    r"__baseline__|__target__|__placebo__|__proxy|__harmful|__control"
)

# Redact injected-body tokens if they appear inside extracted content.
# Include lowercase, dots, and hyphens because versioned tokens often use suffixes like `_v0.1.0`.
BENCH_TOKEN_RE = re.compile(r"\bBENCH_[A-Za-z0-9_.-]+\b")
CONTROL_TOKEN_RE = re.compile(r"\bCONTROL_[A-Za-z0-9_.-]+\b")

# Disallow scenario-doc and ADR references anywhere in run records, per invariant.
FORBIDDEN_PATHS_RE = re.compile(r"docs/adrs|docs/benchmarks/scenarios")


@dataclass(frozen=True)
class Candidate:
    scenario_id: str
    run_record_name: str
    output: str


@dataclass(frozen=True)
class ScenarioContext:
    scenario_id: str
    task_and_criteria: str


def _extract_scenario_id(text: str) -> str:
    match = re.search(r"^- \*\*scenario_id:\*\* `([^`]+)`", text, flags=re.M)
    if not match:
        raise ValueError("extract_scenario_id failed: missing scenario_id")
    return match.group(1)


def _extract_section(text: str, header: str) -> str:
    pattern = rf"^## {re.escape(header)}\s*\n(.*?)(?=^##\s|\Z)"
    match = re.search(pattern, text, flags=re.M | re.S)
    return match.group(1).strip() if match else ""


def _is_stub(output: str) -> bool:
    if not output.strip():
        return True
    lower = output.lower()
    return (
        ("empty stub" in lower)
        or ("not executed" in lower)
        or ("raw output or pointer to artifact" in lower)
    )


def _candidate_id(scenario_id: str, run_record_name: str) -> str:
    digest = hashlib.sha256(run_record_name.encode("utf-8")).hexdigest()[:8]
    return f"{scenario_id}__C{digest}"


def _redact_for_blinding(text: str) -> str:
    redacted = CONDITION_WORDS_RE.sub("[REDACTED_CONDITION]", text)
    redacted = BENCH_TOKEN_RE.sub("BENCH_[REDACTED]", redacted)
    redacted = CONTROL_TOKEN_RE.sub("CONTROL_[REDACTED]", redacted)
    return redacted


def _iter_rubric_run_records(run_records_dir: Path) -> Iterable[Path]:
    yield from sorted(run_records_dir.glob("v0-rubric-*.md"))


def _extract_framework_rubric_yaml_blocks(framework_text: str) -> dict[str, str]:
    # Extract rubric scenario YAML blocks that contain `id: v0-rubric-...` as a stable, evaluator-facing source of
    # task prompt + criteria. We include the full YAML block so the evaluator can see task + success criteria.
    blocks = re.findall(r"```yaml\n(.*?)\n```", framework_text, flags=re.S)
    by_id: dict[str, str] = {}
    for block in blocks:
        match = re.search(r"^id:\s*(v0-rubric-[\w-]+)\s*$", block, flags=re.M)
        if not match:
            continue
        scenario_id = match.group(1)
        by_id[scenario_id] = block.strip()
    return by_id


def build_scenario_contexts(repo_root: Path) -> dict[str, ScenarioContext]:
    framework_path = (
        repo_root / "docs/frameworks/simulation-effectiveness-benchmark_v0.1.0.md"
    )
    if not framework_path.exists():
        raise SystemExit(
            f"context build failed: framework doc missing. Got: {str(framework_path)!r}"
        )
    framework_text = framework_path.read_text()
    yaml_by_id = _extract_framework_rubric_yaml_blocks(framework_text)

    contexts: dict[str, ScenarioContext] = {}
    for scenario_id, yaml_block in yaml_by_id.items():
        # Redact any injected-body tokens that might appear in notes/elsewhere.
        redacted = _redact_for_blinding(yaml_block)
        contexts[scenario_id] = ScenarioContext(
            scenario_id=scenario_id, task_and_criteria=redacted
        )
    return contexts


def build_candidates(run_records_dir: Path, include_stubs: bool) -> list[Candidate]:
    candidates: list[Candidate] = []
    for path in _iter_rubric_run_records(run_records_dir):
        text = path.read_text()
        scenario_id = _extract_scenario_id(text)
        output = _extract_section(text, "Output")
        output = _redact_for_blinding(output)
        if not include_stubs and _is_stub(output):
            continue
        candidates.append(
            Candidate(scenario_id=scenario_id, run_record_name=path.name, output=output)
        )
    candidates.sort(key=lambda c: (c.scenario_id, c.run_record_name))
    return candidates


def write_packet(
    run_id: str,
    out_path: Path,
    candidates: list[Candidate],
    scenario_contexts: dict[str, ScenarioContext],
) -> None:
    lines: list[str] = []
    lines.append("# Blinded Evaluation Packet — Benchmark v0")
    lines.append("")
    lines.append(f"**Run ID:** `{run_id}`")
    lines.append("")
    lines.append("This packet is designed for a fully blinded evaluator.")
    lines.append("- Candidate IDs are condition-free.")
    lines.append("- Content includes only extracted rubric-run `## Output` sections.")
    lines.append("- Condition words are redacted to `[REDACTED_CONDITION]`.")
    lines.append(
        "- Injected-body tokens are redacted to `BENCH_[REDACTED]` / `CONTROL_[REDACTED]` when they appear in extracted output."
    )
    lines.append("")

    current_scenario: str | None = None
    for candidate in candidates:
        if candidate.scenario_id != current_scenario:
            current_scenario = candidate.scenario_id
            lines.append("---")
            lines.append("")
            lines.append(f"## {current_scenario}")
            lines.append("")
            context = scenario_contexts.get(current_scenario)
            if context:
                lines.append("### Task + Criteria (authoritative excerpt)")
                lines.append("")
                lines.append("```yaml")
                lines.append(context.task_and_criteria)
                lines.append("```")
                lines.append("")
            else:
                lines.append("### Task + Criteria (authoritative excerpt)")
                lines.append("")
                lines.append(
                    "_Missing: scenario context not found in framework doc YAML blocks._"
                )
                lines.append("")

        cid = _candidate_id(candidate.scenario_id, candidate.run_record_name)
        lines.append(f"### {cid}")
        lines.append("")
        lines.append(candidate.output.rstrip() or "<NO OUTPUT>")
        lines.append("")

    out_path.write_text("\n".join(lines).rstrip() + "\n")


def write_mapping(run_id: str, out_path: Path, candidates: list[Candidate]) -> None:
    lines: list[str] = []
    lines.append("# Blinded Evaluation Mapping (PRIVATE)")
    lines.append("")
    lines.append(f"**Run ID:** `{run_id}`")
    lines.append("")
    lines.append(
        "This file maps condition-free candidate IDs to run-record files. Do not share with the blinded evaluator."
    )
    lines.append("")
    for candidate in candidates:
        cid = _candidate_id(candidate.scenario_id, candidate.run_record_name)
        lines.append(
            f"- `{cid}` -> `docs/benchmarks/runs/{run_id}/run-records/{candidate.run_record_name}`"
        )
    out_path.write_text("\n".join(lines).rstrip() + "\n")


def verify_packet(packet_path: Path) -> None:
    text = packet_path.read_text()

    forbidden_tokens = FILENAME_CONDITION_TOKENS_RE.findall(text)
    if forbidden_tokens:
        raise SystemExit(
            f"verify_packet failed: forbidden filename condition tokens present. Got: {sorted(set(forbidden_tokens))!r}"
        )

    if CONDITION_WORDS_RE.search(text):
        raise SystemExit(
            "verify_packet failed: condition words present after redaction."
        )

    # Allow BENCH_[REDACTED], CONTROL_[REDACTED], and BENCH_* (literal phrase).
    bench_leaks = re.findall(r"\bBENCH_(?!\[REDACTED\]|\*)[A-Za-z0-9_.-]+\b", text)
    ctrl_leaks = re.findall(r"\bCONTROL_(?!\[REDACTED\])[A-Za-z0-9_.-]+\b", text)
    if bench_leaks or ctrl_leaks:
        raise SystemExit(
            f"verify_packet failed: injected-body token leaks. Got: BENCH={bench_leaks[:10]!r} CONTROL={ctrl_leaks[:10]!r}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build fully blinded rubric evaluation packet + private mapping."
    )
    parser.add_argument(
        "--run-id",
        required=True,
        help="Benchmark run id, e.g. 2026-02-06_benchmark-v0_initial",
    )
    parser.add_argument("--repo-root", default=".", help="Repo root (default: .)")
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Output dir (default: docs/benchmarks/runs/<run-id>/blinded_eval/)",
    )
    parser.add_argument(
        "--include-stubs",
        action="store_true",
        help="Include empty stubs as <NO OUTPUT> entries",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Verify an existing packet (no writes)",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    run_id = args.run_id

    base_dir = repo_root / "docs/benchmarks/runs" / run_id
    run_records_dir = base_dir / "run-records"
    out_dir = (
        Path(args.out_dir).resolve() if args.out_dir else (base_dir / "blinded_eval")
    )

    packet_path = out_dir / "blinded_eval_packet.md"
    mapping_path = out_dir / "blinded_eval_mapping_private.md"

    if args.verify_only:
        verify_packet(packet_path)
        print(f"OK: {packet_path}")
        return

    if not run_records_dir.exists():
        raise SystemExit(
            f"build failed: run-records dir missing. Got: {str(run_records_dir)!r}"
        )

    out_dir.mkdir(parents=True, exist_ok=True)

    candidates = build_candidates(run_records_dir, include_stubs=args.include_stubs)
    scenario_contexts = build_scenario_contexts(repo_root)
    write_packet(run_id, packet_path, candidates, scenario_contexts)
    write_mapping(run_id, mapping_path, candidates)

    verify_packet(packet_path)

    print(f"Wrote: {packet_path}")
    print(f"Wrote: {mapping_path}")
    print(f"Candidates: {len(candidates)}")


if __name__ == "__main__":
    main()
