#!/usr/bin/env python3
"""
run_audit.py - Pipeline orchestration for three-lens-audit

Part of the three-lens-audit skill.

Orchestrates the full audit workflow:
1. Generate agent prompts from templates
2. Estimate cost before running
3. Validate agent outputs
4. Synthesize findings (only if validation passes)

Usage:
    python run_audit.py prepare <target_file> [--preset default|design|quick]
    python run_audit.py finalize <output1.md> <output2.md> [output3.md] --target <name>
    python run_audit.py status <output_dir>

Exit Codes:
    0  - Success
    1  - General failure
    2  - Invalid arguments
    10 - Validation failed
    11 - Synthesis failed
"""

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Import sibling modules
try:
    from validate_output import validate_output, LENS_REQUIREMENTS
    from synthesize import synthesize, generate_synthesis_markdown, generate_implementation_spec_markdown, detect_lens_from_content
except ImportError:
    # Handle running from different directory
    import importlib.util
    script_dir = Path(__file__).parent

    spec = importlib.util.spec_from_file_location("validate_output", script_dir / "validate_output.py")
    validate_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validate_module)
    validate_output = validate_module.validate_output
    LENS_REQUIREMENTS = validate_module.LENS_REQUIREMENTS

    spec = importlib.util.spec_from_file_location("synthesize", script_dir / "synthesize.py")
    synthesize_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(synthesize_module)
    synthesize = synthesize_module.synthesize
    generate_synthesis_markdown = synthesize_module.generate_synthesis_markdown
    generate_implementation_spec_markdown = synthesize_module.generate_implementation_spec_markdown
    detect_lens_from_content = synthesize_module.detect_lens_from_content


# ===========================================================================
# CONSTANTS
# ===========================================================================

PRESETS = {
    "default": {
        "lenses": ["adversarial", "pragmatic", "cost-benefit"],
        "description": "General stress-testing (Adversarial + Pragmatic + Cost/Benefit)"
    },
    "design": {
        "lenses": ["robustness", "minimalist", "capability"],
        "description": "Design documents (Robustness + Minimalist + Capability)"
    },
    "quick": {
        "lenses": ["adversarial", "pragmatic"],
        "description": "Fast review, skip ROI analysis (Adversarial + Pragmatic)"
    },
    "claude-code": {
        "lenses": ["implementation", "adversarial", "cost-benefit"],
        "description": "Claude Code artifacts (Implementation + Adversarial + Cost/Benefit)"
    }
}

# Cost estimation (approximate tokens per agent)
COST_ESTIMATES = {
    "default": {"input": 12000, "output": 6000, "agents": 3},
    "design": {"input": 15000, "output": 8000, "agents": 3},
    "quick": {"input": 8000, "output": 4000, "agents": 2},
    "claude-code": {"input": 12000, "output": 6000, "agents": 3}
}

# Opus pricing (last updated: 2025-01)
# Check https://www.anthropic.com/pricing for current rates
OPUS_PRICE_INPUT = 15.0 / 1_000_000   # $15 per 1M input tokens
OPUS_PRICE_OUTPUT = 75.0 / 1_000_000  # $75 per 1M output tokens


# ===========================================================================
# PROMPT TEMPLATES
# ===========================================================================

def load_prompts_from_reference() -> Dict[str, str]:
    """Load prompts from references/agent-prompts.md using markers.

    Extracts content between <!-- BEGIN:lens_name --> and <!-- END:lens_name -->
    markers. The prompts are inside markdown code blocks, so we strip those.

    Returns:
        Dict mapping lens name to prompt template with {target} placeholder.

    Raises:
        FileNotFoundError: If the reference file doesn't exist.
    """
    script_dir = Path(__file__).parent
    ref_file = script_dir.parent / "references" / "agent-prompts.md"

    if not ref_file.exists():
        raise FileNotFoundError(f"Reference file not found: {ref_file}")

    content = ref_file.read_text()
    prompts = {}

    # Pattern matches: <!-- BEGIN:lens_name -->\n```\ncontent\n```\n<!-- END:lens_name -->
    # We capture the lens name and the content inside the code block
    pattern = r'<!-- BEGIN:([\w-]+) -->\n```\n(.*?)\n```\n<!-- END:\1 -->'
    for match in re.finditer(pattern, content, re.DOTALL):
        lens_name = match.group(1)
        prompt_content = match.group(2).strip()
        # Convert [TARGET_FILE] placeholder to {target} for Python format strings
        prompt_content = prompt_content.replace('[TARGET_FILE]', '{target}')
        prompts[lens_name] = prompt_content

    return prompts


# Load prompts at module import time
PROMPT_TEMPLATES = load_prompts_from_reference()


# ===========================================================================
# RESULT TYPES
# ===========================================================================

@dataclass
class PrepareResult:
    """Result of prepare command."""
    target: str
    preset: str
    lenses: List[str]
    prompts: Dict[str, str]  # lens -> prompt text
    cost_estimate: Dict[str, float]
    task_template: str


@dataclass
class ValidationSummary:
    """Summary of validation for multiple outputs."""
    results: Dict[str, Tuple[bool, str]]  # lens -> (passed, summary)
    all_passed: bool
    passed_count: int
    total_count: int


@dataclass
class FinalizeResult:
    """Result of finalize command."""
    validation: ValidationSummary
    synthesis_result: Optional["SynthesisResult"]  # Store raw result, defer formatting to CLI
    warnings: List[str] = field(default_factory=list)


# ===========================================================================
# CORE FUNCTIONS
# ===========================================================================

def estimate_cost(preset: str, target_tokens: int = 2000) -> Dict[str, float]:
    """Estimate cost for running the audit."""
    estimates = COST_ESTIMATES.get(preset, COST_ESTIMATES["default"])

    # Add target file tokens to input
    total_input = (estimates["input"] + target_tokens) * estimates["agents"]
    total_output = estimates["output"] * estimates["agents"]

    input_cost = total_input * OPUS_PRICE_INPUT
    output_cost = total_output * OPUS_PRICE_OUTPUT

    return {
        "input_tokens": total_input,
        "output_tokens": total_output,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": input_cost + output_cost,
        "agents": estimates["agents"]
    }


def generate_prompts(target: str, preset: str) -> Dict[str, str]:
    """Generate agent prompts for each lens."""
    lenses = PRESETS[preset]["lenses"]
    prompts = {}

    for lens in lenses:
        template = PROMPT_TEMPLATES.get(lens)
        if template:
            prompts[lens] = template.format(target=target)
        else:
            prompts[lens] = f"[Prompt template not found for lens: {lens}]"

    return prompts


def generate_task_template(target: str, preset: str) -> str:
    """Generate Task tool invocation template for Claude."""
    lenses = PRESETS[preset]["lenses"]

    lines = [
        "## Task Tool Invocations",
        "",
        "Launch these agents in a SINGLE message with multiple Task tool calls:",
        ""
    ]

    for i, lens in enumerate(lenses, 1):
        lines.extend([
            f"### Agent {i}: {lens.title().replace('-', '/')}",
            "```",
            "Tool: Task",
            "  name: general-purpose",
            "  model: opus",
            f"  description: {lens} lens audit of {target}",
            f"  prompt: [Contents of {lens}_prompt.md]",
            "```",
            ""
        ])

    lines.extend([
        "**Critical:** All agents MUST be launched in a single message for true parallelism.",
        "",
        "Save each agent's output to a separate file, then run:",
        f"```",
        f"python scripts/run_audit.py finalize {' '.join(f'{l}.md' for l in lenses)} --target \"{target}\"",
        "```"
    ])

    return "\n".join(lines)


def prepare(target: str, preset: str = "default", output_dir: Optional[Path] = None) -> PrepareResult:
    """Prepare prompts and cost estimate for an audit."""
    if preset not in PRESETS:
        raise ValueError(f"Unknown preset: {preset}. Valid: {', '.join(PRESETS.keys())}")

    # Estimate target file size
    target_path = Path(target)
    if target_path.exists():
        target_tokens = len(target_path.read_text()) // 4  # Rough estimate
    else:
        target_tokens = 2000  # Default estimate

    prompts = generate_prompts(target, preset)
    cost = estimate_cost(preset, target_tokens)
    task_template = generate_task_template(target, preset)

    # Write prompt files if output_dir specified
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        for lens, prompt in prompts.items():
            (output_dir / f"{lens}_prompt.md").write_text(prompt)

    return PrepareResult(
        target=target,
        preset=preset,
        lenses=PRESETS[preset]["lenses"],
        prompts=prompts,
        cost_estimate=cost,
        task_template=task_template
    )


def validate_outputs(files: Dict[str, Path]) -> ValidationSummary:
    """Validate multiple lens outputs."""
    results = {}
    passed_count = 0

    for lens, path in files.items():
        if not path.exists():
            results[lens] = (False, f"File not found: {path}")
            continue

        content = path.read_text()
        result = validate_output(lens, content)

        results[lens] = (result.is_valid, result.summary)
        if result.is_valid:
            passed_count += 1

    return ValidationSummary(
        results=results,
        all_passed=passed_count == len(files),
        passed_count=passed_count,
        total_count=len(files)
    )


def finalize(
    output_files: List[Path],
    target: str = "[Audit Target]",
    preset: str = "default",
    auto_detect: bool = False,
    threshold: float = 0.3
) -> FinalizeResult:
    """Validate outputs and synthesize findings."""
    warnings = []

    # Determine lens mapping
    if auto_detect:
        lens_files = {}
        for path in output_files:
            if not path.exists():
                warnings.append(f"File not found: {path}")
                continue
            content = path.read_text()
            lens = detect_lens_from_content(content)
            if lens:
                lens_files[lens] = path
            else:
                warnings.append(f"Could not detect lens type for: {path}")
    else:
        lenses = PRESETS[preset]["lenses"]
        if len(output_files) != len(lenses):
            warnings.append(f"Expected {len(lenses)} files for {preset} preset, got {len(output_files)}")
        lens_files = dict(zip(lenses, output_files))

    # Validate
    validation = validate_outputs(lens_files)

    if not validation.all_passed:
        failed = [l for l, (p, _) in validation.results.items() if not p]
        warnings.append(f"Validation failed for: {', '.join(failed)}")

        # Still attempt synthesis if at least 2 passed
        if validation.passed_count < 2:
            return FinalizeResult(
                validation=validation,
                synthesis_result=None,
                warnings=warnings + ["Insufficient valid outputs for synthesis (need ≥2)"]
            )

    # Filter to valid outputs only
    valid_lens_files = {l: p for l, p in lens_files.items()
                        if validation.results.get(l, (False, ""))[0]}

    # Synthesize
    result = synthesize(valid_lens_files, target, threshold=threshold)

    if result.warnings:
        warnings.extend(result.warnings)

    return FinalizeResult(
        validation=validation,
        synthesis_result=result,
        warnings=warnings
    )


def check_status(output_dir: Path, preset: str = "default") -> Dict[str, Dict]:
    """Check status of audit outputs in a directory."""
    lenses = PRESETS[preset]["lenses"]
    status = {}

    for lens in lenses:
        expected_file = output_dir / f"{lens}.md"

        if not expected_file.exists():
            status[lens] = {
                "exists": False,
                "validated": False,
                "file": str(expected_file)
            }
        else:
            content = expected_file.read_text()
            result = validate_output(lens, content)
            status[lens] = {
                "exists": True,
                "validated": result.is_valid,
                "summary": result.summary,
                "file": str(expected_file)
            }

    return status


# ===========================================================================
# CLI INTERFACE
# ===========================================================================

def cmd_prepare(args):
    """Handle prepare subcommand."""
    result = prepare(
        args.target,
        preset=args.preset,
        output_dir=Path(args.output_dir) if args.output_dir else None
    )

    print(f"# Three-Lens Audit: Preparation")
    print(f"")
    print(f"**Target:** `{result.target}`")
    print(f"**Preset:** {result.preset} — {PRESETS[result.preset]['description']}")
    print(f"**Lenses:** {', '.join(result.lenses)}")
    print(f"")
    print(f"## Cost Estimate")
    print(f"")
    print(f"| Metric | Value |")
    print(f"|--------|-------|")
    print(f"| Agents | {result.cost_estimate['agents']} |")
    print(f"| Input tokens | ~{result.cost_estimate['input_tokens']:,} |")
    print(f"| Output tokens | ~{result.cost_estimate['output_tokens']:,} |")
    print(f"| Estimated cost | ${result.cost_estimate['total_cost']:.2f} |")
    print(f"")

    if args.output_dir:
        print(f"## Generated Files")
        print(f"")
        for lens in result.lenses:
            print(f"- `{args.output_dir}/{lens}_prompt.md`")
        print(f"")

    print(result.task_template)


def cmd_finalize(args):
    """Handle finalize subcommand."""
    output_files = [Path(f) for f in args.files]

    result = finalize(
        output_files,
        target=args.target,
        preset=args.preset,
        auto_detect=args.auto_detect,
        threshold=args.threshold
    )

    # Print validation summary
    print("## Validation Summary", file=sys.stderr)
    print("", file=sys.stderr)
    print(f"| Lens | Status | Details |", file=sys.stderr)
    print(f"|------|--------|---------|", file=sys.stderr)
    for lens, (passed, summary) in result.validation.results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"| {lens} | {status} | {summary} |", file=sys.stderr)
    print("", file=sys.stderr)
    print(f"**Result:** {result.validation.passed_count}/{result.validation.total_count} passed", file=sys.stderr)
    print("", file=sys.stderr)

    if result.warnings:
        print("**Warnings:**", file=sys.stderr)
        for w in result.warnings:
            print(f"- {w}", file=sys.stderr)
        print("", file=sys.stderr)

    # Print synthesis if available
    if result.synthesis_result:
        if args.impl_spec:
            print(generate_implementation_spec_markdown(result.synthesis_result))
        else:
            print(generate_synthesis_markdown(result.synthesis_result))
        sys.exit(0)
    else:
        print("Synthesis not generated due to validation failures.", file=sys.stderr)
        sys.exit(10)


def cmd_status(args):
    """Handle status subcommand."""
    status = check_status(Path(args.output_dir), preset=args.preset)

    print(f"## Audit Status: {args.output_dir}")
    print(f"")
    print(f"| Lens | Exists | Valid | File |")
    print(f"|------|--------|-------|------|")

    all_ready = True
    for lens, info in status.items():
        exists = "✓" if info["exists"] else "✗"
        valid = "✓" if info["validated"] else "✗" if info["exists"] else "-"
        print(f"| {lens} | {exists} | {valid} | `{info['file']}` |")
        if not info.get("validated", False):
            all_ready = False

    print(f"")
    if all_ready:
        print(f"**Ready for finalize!**")
        lenses = PRESETS[args.preset]["lenses"]
        files = " ".join(f"{args.output_dir}/{l}.md" for l in lenses)
        print(f"```")
        print(f"python scripts/run_audit.py finalize {files} --target \"[Target Name]\"")
        print(f"```")
    else:
        print(f"**Not ready:** Some outputs missing or invalid.")


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline orchestration for three-lens-audit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Subcommands:
  prepare   Generate agent prompts and cost estimate
  finalize  Validate outputs and synthesize findings
  status    Check status of outputs in a directory

Examples:
  # Prepare for audit
  %(prog)s prepare path/to/target.md --output-dir ./audit_outputs

  # Finalize after agents complete
  %(prog)s finalize adversarial.md pragmatic.md cost-benefit.md --target "CLAUDE.md"

  # Check status
  %(prog)s status ./audit_outputs
        """
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Prepare subcommand
    prepare_parser = subparsers.add_parser("prepare", help="Generate prompts and cost estimate")
    prepare_parser.add_argument("target", help="Target file to audit")
    prepare_parser.add_argument(
        "--preset", "-p",
        choices=list(PRESETS.keys()),
        default="default",
        help="Lens preset (default: default)"
    )
    prepare_parser.add_argument(
        "--output-dir", "-o",
        help="Directory to write prompt files"
    )
    prepare_parser.set_defaults(func=cmd_prepare)

    # Finalize subcommand
    finalize_parser = subparsers.add_parser("finalize", help="Validate and synthesize")
    finalize_parser.add_argument(
        "files",
        nargs="+",
        help="Agent output files (in lens order, or use --auto-detect)"
    )
    finalize_parser.add_argument(
        "--target", "-t",
        default="[Audit Target]",
        help="Name of the audit target"
    )
    finalize_parser.add_argument(
        "--preset", "-p",
        choices=list(PRESETS.keys()),
        default="default",
        help="Lens preset for file ordering (default: default)"
    )
    finalize_parser.add_argument(
        "--auto-detect",
        action="store_true",
        help="Auto-detect lens type from file content"
    )
    finalize_parser.add_argument(
        "--threshold",
        type=float,
        default=0.3,
        help="Keyword overlap threshold for convergence (default: 0.3)"
    )
    finalize_parser.add_argument(
        "--impl-spec",
        action="store_true",
        help="Generate implementation spec format (prioritized tasks for execution)"
    )
    finalize_parser.set_defaults(func=cmd_finalize)

    # Status subcommand
    status_parser = subparsers.add_parser("status", help="Check output status")
    status_parser.add_argument("output_dir", help="Directory containing outputs")
    status_parser.add_argument(
        "--preset", "-p",
        choices=list(PRESETS.keys()),
        default="default",
        help="Lens preset (default: default)"
    )
    status_parser.set_defaults(func=cmd_status)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
