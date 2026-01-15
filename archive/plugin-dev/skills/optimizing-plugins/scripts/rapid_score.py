#!/usr/bin/env python3
"""
Rapid scoring for plugin optimization.

Scores a plugin against 6 optimization lenses, producing a structured
assessment for use in the Orientation phase.

Usage:
    python rapid_score.py <plugin-path>
    python rapid_score.py <plugin-path> --json
    python rapid_score.py <plugin-path> --lens trigger_fidelity

Exit Codes:
    0  - Success (all lenses scored)
    1  - General failure
    2  - Invalid arguments
    10 - Plugin structure invalid
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


@dataclass
class LensScore:
    """Score for a single lens."""
    name: str
    score: float
    max_score: float = 10.0
    threshold: float = 7.0
    passing: bool = field(init=False)
    components: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)

    def __post_init__(self):
        self.passing = self.score >= self.threshold


@dataclass
class ScoringResult:
    """Overall scoring result."""
    success: bool
    plugin_path: str
    plugin_name: str
    overall_score: float
    passing: bool
    lens_scores: list
    below_threshold: list
    focus_recommendation: str
    errors: list = field(default_factory=list)


def find_plugin_json(plugin_path: Path) -> Optional[Path]:
    """Locate plugin.json in standard locations."""
    candidates = [
        plugin_path / ".claude-plugin" / "plugin.json",
        plugin_path / "plugin.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def count_files(directory: Path, pattern: str) -> int:
    """Count files matching pattern in directory."""
    if not directory.exists():
        return 0
    return len(list(directory.glob(pattern)))


def read_file_lines(filepath: Path) -> int:
    """Count lines in a file."""
    if not filepath.exists():
        return 0
    try:
        return len(filepath.read_text().splitlines())
    except Exception:
        return 0


def score_trigger_fidelity(plugin_path: Path) -> LensScore:
    """Score Lens 1: Trigger Fidelity."""
    score = LensScore(name="trigger_fidelity", score=5.0)

    skills_dir = plugin_path / "skills"
    if not skills_dir.exists():
        score.notes.append("No skills directory")
        score.score = 0.0
        return score

    skill_files = list(skills_dir.glob("*/SKILL.md"))
    if not skill_files:
        score.notes.append("No SKILL.md files found")
        score.score = 0.0
        return score

    total_score = 0.0
    for skill_file in skill_files:
        content = skill_file.read_text().lower()
        skill_score = 5.0  # Base score

        # Check for trigger phrases
        if "trigger" in content or "use when" in content:
            skill_score += 1.0
            score.components["has_triggers"] = True

        # Check for action verbs
        action_verbs = ["create", "analyze", "debug", "fix", "review", "validate", "generate"]
        verb_count = sum(1 for v in action_verbs if v in content)
        if verb_count >= 3:
            skill_score += 1.0
            score.components["has_action_verbs"] = True

        # Check for context phrases
        context_phrases = ["after", "before", "when", "during", "while"]
        context_count = sum(1 for p in context_phrases if p in content)
        if context_count >= 2:
            skill_score += 1.0
            score.components["has_context"] = True

        # Check description length (50-200 words ideal)
        # Approximate by checking frontmatter
        if "description:" in content:
            skill_score += 1.0
            score.components["has_description"] = True

        # Check for differentiation (NOT for, distinct from)
        if "not for" in content or "instead of" in content or "distinct" in content:
            skill_score += 1.0
            score.components["has_differentiation"] = True

        total_score += min(skill_score, 10.0)

    score.score = round(total_score / len(skill_files), 1)
    score.notes.append(f"Scored {len(skill_files)} skill(s)")
    return score


def score_token_economy(plugin_path: Path) -> LensScore:
    """Score Lens 2: Token Economy."""
    score = LensScore(name="token_economy", score=5.0)

    skills_dir = plugin_path / "skills"
    if not skills_dir.exists():
        score.score = 5.0  # Neutral if no skills
        return score

    skill_files = list(skills_dir.glob("*/SKILL.md"))
    if not skill_files:
        score.score = 5.0
        return score

    total_score = 0.0
    for skill_file in skill_files:
        skill_score = 10.0  # Start high, deduct
        lines = read_file_lines(skill_file)

        # Deduct for excessive length
        if lines > 500:
            skill_score -= 3.0
            score.notes.append(f"{skill_file.parent.name}: {lines} lines (>500)")
        elif lines > 300:
            skill_score -= 1.0

        score.components[f"{skill_file.parent.name}_lines"] = lines

        # Check for references usage
        refs_dir = skill_file.parent / "references"
        if refs_dir.exists() and list(refs_dir.glob("*.md")):
            skill_score += 1.0
            score.components["uses_references"] = True
        elif lines > 200:
            skill_score -= 1.0  # Should use refs if long

        # Check for tables (efficient formatting)
        content = skill_file.read_text()
        if "|" in content and "---" in content:
            skill_score += 0.5
            score.components["uses_tables"] = True

        total_score += max(0.0, min(skill_score, 10.0))

    score.score = round(total_score / len(skill_files), 1)
    return score


def score_structural_clarity(plugin_path: Path) -> LensScore:
    """Score Lens 3: Structural Clarity."""
    score = LensScore(name="structural_clarity", score=5.0)

    skills_dir = plugin_path / "skills"
    if not skills_dir.exists():
        score.score = 5.0
        return score

    skill_files = list(skills_dir.glob("*/SKILL.md"))
    if not skill_files:
        score.score = 5.0
        return score

    total_score = 0.0
    for skill_file in skill_files:
        skill_score = 5.0
        content = skill_file.read_text()

        # Check for headings hierarchy
        h2_count = content.count("\n## ")
        h3_count = content.count("\n### ")
        if h2_count >= 3:
            skill_score += 2.0
            score.components["has_sections"] = True
        if h3_count >= 2:
            skill_score += 1.0
            score.components["has_subsections"] = True

        # Check for TOC (long files should have one)
        lines = len(content.splitlines())
        has_toc = "table of contents" in content.lower() or "## contents" in content.lower()
        if lines > 150 and not has_toc:
            skill_score -= 1.0
            score.notes.append(f"{skill_file.parent.name}: Long file without TOC")
        elif has_toc:
            skill_score += 1.0
            score.components["has_toc"] = True

        # Check for consistent formatting
        if "```" in content:  # Has code blocks
            skill_score += 0.5

        # Check for collapsible sections
        if "<details>" in content:
            skill_score += 1.0
            score.components["uses_details"] = True

        total_score += min(skill_score, 10.0)

    score.score = round(total_score / len(skill_files), 1)
    return score


def score_degrees_of_freedom(plugin_path: Path) -> LensScore:
    """Score Lens 4: Degrees of Freedom."""
    score = LensScore(name="degrees_of_freedom", score=6.0)  # Default moderate

    skills_dir = plugin_path / "skills"
    if not skills_dir.exists():
        return score

    skill_files = list(skills_dir.glob("*/SKILL.md"))
    if not skill_files:
        return score

    total_score = 0.0
    for skill_file in skill_files:
        skill_score = 6.0
        content = skill_file.read_text().lower()

        # Check for explicit steps (rigid when needed)
        step_indicators = ["step 1", "step 2", "1.", "2.", "first,", "then,"]
        has_steps = any(ind in content for ind in step_indicators)
        if has_steps:
            skill_score += 1.0
            score.components["has_explicit_steps"] = True

        # Check for decision points
        decision_indicators = ["if ", "when ", "choose", "decide", "option"]
        decision_count = sum(1 for d in decision_indicators if d in content)
        if decision_count >= 3:
            skill_score += 1.0
            score.components["has_decision_points"] = True

        # Check for flexibility language
        flexibility = ["consider", "may", "could", "depending on", "adapt"]
        flex_count = sum(1 for f in flexibility if f in content)
        if flex_count >= 2:
            skill_score += 1.0
            score.components["has_flexibility"] = True

        # Check for must/required (appropriate rigidity)
        rigidity = ["must", "required", "always", "never", "critical"]
        rigid_count = sum(1 for r in rigidity if r in content)
        if rigid_count >= 2:
            skill_score += 1.0
            score.components["has_rigidity"] = True

        total_score += min(skill_score, 10.0)

    score.score = round(total_score / len(skill_files), 1)
    return score


def score_resilience(plugin_path: Path) -> LensScore:
    """Score Lens 5: Resilience."""
    score = LensScore(name="resilience", score=5.0)

    # Check for hooks with error handling
    hooks_file = plugin_path / "hooks" / "hooks.json"
    if hooks_file.exists():
        try:
            hooks = json.loads(hooks_file.read_text())
            if hooks:
                score.score += 1.0
                score.components["has_hooks"] = True
        except json.JSONDecodeError:
            score.notes.append("Invalid hooks.json")
            score.score -= 1.0

    # Check skills for error handling
    skills_dir = plugin_path / "skills"
    if skills_dir.exists():
        skill_files = list(skills_dir.glob("*/SKILL.md"))
        for skill_file in skill_files:
            content = skill_file.read_text().lower()

            # Check for error handling language
            error_terms = ["error", "fail", "exception", "recovery", "fallback", "graceful"]
            error_count = sum(1 for e in error_terms if e in content)
            if error_count >= 3:
                score.score += 1.5
                score.components["discusses_errors"] = True

            # Check for verification
            if "verif" in content or "check" in content or "validat" in content:
                score.score += 1.0
                score.components["has_verification"] = True

    # Check for scripts (self-verification)
    scripts_dir = plugin_path / "scripts"
    if scripts_dir.exists() and list(scripts_dir.glob("*.py")):
        score.score += 1.5
        score.components["has_scripts"] = True

    score.score = round(min(score.score, 10.0), 1)
    return score


def score_plugin_coherence(plugin_path: Path) -> LensScore:
    """Score Lens 6: Plugin Coherence."""
    score = LensScore(name="plugin_coherence", score=5.0)

    # Check for README
    readme = plugin_path / "README.md"
    if readme.exists():
        score.score += 1.5
        score.components["has_readme"] = True

        content = readme.read_text().lower()
        # Check README completeness
        sections = ["install", "usage", "feature", "command", "skill"]
        section_count = sum(1 for s in sections if s in content)
        if section_count >= 3:
            score.score += 1.0
            score.components["readme_complete"] = True
    else:
        score.notes.append("No README.md")

    # Check for plugin.json
    plugin_json = find_plugin_json(plugin_path)
    if plugin_json:
        score.score += 1.0
        score.components["has_manifest"] = True
        try:
            manifest = json.loads(plugin_json.read_text())
            if manifest.get("description"):
                score.score += 0.5
        except json.JSONDecodeError:
            score.notes.append("Invalid plugin.json")
            score.score -= 1.0

    # Check for consistent structure
    component_dirs = ["skills", "commands", "agents", "hooks"]
    existing_dirs = [d for d in component_dirs if (plugin_path / d).exists()]
    if len(existing_dirs) >= 2:
        score.score += 1.0
        score.components["has_structure"] = True

    # Check for naming consistency (heuristic)
    if (plugin_path / "skills").exists():
        skill_dirs = [d.name for d in (plugin_path / "skills").iterdir() if d.is_dir()]
        # All lowercase with hyphens
        if all("-" in name or name.islower() for name in skill_dirs):
            score.score += 0.5
            score.components["consistent_naming"] = True

    score.score = round(min(score.score, 10.0), 1)
    return score


def score_plugin(plugin_path: Path) -> ScoringResult:
    """Score a plugin against all 6 lenses."""

    # Validate plugin exists
    if not plugin_path.exists():
        return ScoringResult(
            success=False,
            plugin_path=str(plugin_path),
            plugin_name="unknown",
            overall_score=0.0,
            passing=False,
            lens_scores=[],
            below_threshold=[],
            focus_recommendation="",
            errors=[f"Plugin path does not exist: {plugin_path}"]
        )

    # Get plugin name
    plugin_json = find_plugin_json(plugin_path)
    if plugin_json:
        try:
            manifest = json.loads(plugin_json.read_text())
            plugin_name = manifest.get("name", plugin_path.name)
        except json.JSONDecodeError:
            plugin_name = plugin_path.name
    else:
        plugin_name = plugin_path.name

    # Score each lens
    lens_scores = [
        score_trigger_fidelity(plugin_path),
        score_token_economy(plugin_path),
        score_structural_clarity(plugin_path),
        score_degrees_of_freedom(plugin_path),
        score_resilience(plugin_path),
        score_plugin_coherence(plugin_path),
    ]

    # Calculate overall
    overall = sum(ls.score for ls in lens_scores) / len(lens_scores)
    below = [ls.name for ls in lens_scores if not ls.passing]

    # Generate focus recommendation
    if not below:
        recommendation = "All lenses passing. Focus on polish and edge cases."
    elif len(below) == 1:
        recommendation = f"Focus on {below[0]} (below threshold)."
    elif len(below) <= 3:
        recommendation = f"Priority lenses: {', '.join(below[:2])}. Consider Deep mode."
    else:
        recommendation = f"{len(below)} lenses below threshold. Start with highest-priority: {below[0]}."

    return ScoringResult(
        success=True,
        plugin_path=str(plugin_path),
        plugin_name=plugin_name,
        overall_score=round(overall, 1),
        passing=overall >= 7.0,
        lens_scores=[asdict(ls) for ls in lens_scores],
        below_threshold=below,
        focus_recommendation=recommendation,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Score a plugin against 6 optimization lenses",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("plugin_path", type=Path, help="Path to plugin directory")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--lens", type=str, help="Score only specific lens")

    args = parser.parse_args()

    result = score_plugin(args.plugin_path)

    if args.json:
        print(json.dumps(asdict(result), indent=2))
    else:
        # Human-readable output
        if not result.success:
            print(f"ERROR: {result.errors[0]}")
            sys.exit(10)

        print(f"\n{'='*60}")
        print(f"Plugin Optimization Score: {result.plugin_name}")
        print(f"{'='*60}\n")

        print(f"Overall: {result.overall_score}/10", end="")
        print(f" {'✓ PASSING' if result.passing else '✗ BELOW THRESHOLD'}\n")

        print("Lens Scores:")
        print("-" * 40)
        for ls in result.lens_scores:
            status = "✓" if ls["passing"] else "✗"
            print(f"  {status} {ls['name']:20} {ls['score']:4.1f}/10")

        print()
        if result.below_threshold:
            print(f"Below threshold: {', '.join(result.below_threshold)}")
        print(f"\nRecommendation: {result.focus_recommendation}")

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
