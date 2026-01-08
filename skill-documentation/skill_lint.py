#!/usr/bin/env python3
"""
skill_lint.py — deterministic linting for SKILL.md bodies.

Design goals:
- Emit STRICT-SPEC fail codes first (PASS/FAIL contract).
- Do not emit semantic quality notes (manual review responsibility).
- Do not emit category/domain notes (routing is out of scope for this linter).
- No third-party deps; portable; deterministic output ordering.

Strict fail codes implemented (from the strict spec):
- FAIL.missing-content-areas
- FAIL.no-objective-dod
- FAIL.no-stop-ask
- FAIL.no-quick-check
- FAIL.too-few-decision-points
- FAIL.undeclared-assumptions
- FAIL.unsafe-default
- FAIL.non-operational-procedure
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

STRICT_FAIL_CODES: Tuple[str, ...] = (
    "FAIL.missing-content-areas",
    "FAIL.no-objective-dod",
    "FAIL.no-stop-ask",
    "FAIL.no-quick-check",
    "FAIL.too-few-decision-points",
    "FAIL.undeclared-assumptions",
    "FAIL.unsafe-default",
    "FAIL.non-operational-procedure",
)

# Required content areas per strict spec (8-section contract).
CONTENT_AREAS: Dict[str, Tuple[str, ...]] = {
    "when_to_use": (
        "when to use", "use when", "intent / typical use cases", "intent", "purpose",
        "triggers", "use cases", "scenarios", "applies when",
    ),
    "when_not_to_use": (
        "when not to use", "do not use", "common misfires", "non-goals", "out of scope",
        "anti-patterns", "avoid", "don't use", "limitations", "not for",
    ),
    "inputs": (
        "inputs", "input contract", "required inputs", "optional inputs",
        "constraints/assumptions", "assumptions", "prerequisites", "requirements",
        "parameters", "arguments", "config", "configuration",
    ),
    "outputs": (
        "outputs", "output contract", "artifacts", "deliverables",
        "results", "produces", "generates", "returns",
    ),
    "procedure": (
        "procedure", "steps", "workflow", "process", "how it works",
        "execution", "algorithm", "method", "approach",
    ),
    "decision_points": (
        "decision points", "decision gates", "branching", "gates",
        "choices", "options", "branches", "conditionals",
    ),
    "verification": (
        "verification", "quick check", "deep checks", "validation",
        "testing", "checks", "how to verify", "confirmation",
    ),
    "troubleshooting": (
        "troubleshooting", "failure modes", "common failure", "debugging",
        "errors", "issues", "problems", "fixes", "recovery",
    ),
}

# Signals that are typically "objective checks" (heuristic).
OBJECTIVE_CHECK_SIGNALS: Tuple[str, ...] = (
    "expected:",
    "exit 0",
    "exit code",
    "file exists",
    "files exist",
    "contains",
    "matches",
    "no remaining occurrences",
    "0 failures",
    "passes",
)

# Dangerous-ish command tokens (heuristic for unsafe default).
DANGEROUS_TOKENS: Tuple[str, ...] = (
    "rm ", "rm\t", "rmdir",
    "delete", "drop ", "truncate",
    "migrate", "migration",
    "deploy", "release",
    "terraform apply", "kubectl delete", "helm upgrade",
    "force", "--force", "-f ",
)

ASK_FIRST_PATTERNS: Tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)\bask\s*[- ]?first\b"),
    re.compile(r"(?i)\bdo not\b.*\bwithout\b.*\bapproval\b"),
    re.compile(r"(?i)\bexplicit\b.*\bapproval\b"),
)

STOP_PATTERNS: Tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)\bstop\b"),
    re.compile(r"(?i)\bstop\.\b"),
    re.compile(r"(?i)\bstop and ask\b"),
)

DECISION_POINT_REGEXES: Tuple[re.Pattern[str], ...] = (
    # Original: if ... then ... otherwise
    re.compile(r"(?i)\bif\b.{0,200}\bthen\b.{0,200}\botherwise\b"),
    re.compile(r"(?i)^\s*[-*]?\s*if\b.*\bthen\b.*\botherwise\b", re.MULTILINE),
    # New: if ... then ... else
    re.compile(r"(?i)\bif\b.{0,200}\bthen\b.{0,200}\belse\b"),
    re.compile(r"(?i)^\s*[-*]?\s*if\b.*\bthen\b.*\belse\b", re.MULTILINE),
    # New: if ... else (without explicit then)
    re.compile(r"(?i)\bif\b.{0,100}\belse\b"),
)

@dataclasses.dataclass(frozen=True)
class FileLintResult:
    path: str
    disposition: str  # PASS | FAIL
    strict_fail_codes: List[str]
    strict_details: List[str]

def _strip_frontmatter(md: str) -> str:
    lines = md.splitlines()
    if len(lines) >= 2 and lines[0].strip() == "---":
        # find closing '---'
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return "\n".join(lines[i + 1 :])
    return md


def _strip_fenced_code_blocks(text: str) -> str:
    """Remove fenced code blocks (```...```) from text.

    These are examples, not actionable instructions.
    """
    # Match ``` optionally with language, then content, then closing ```
    return re.sub(r"```[^\n]*\n.*?```", "", text, flags=re.DOTALL)

@dataclasses.dataclass
class Heading:
    level: int
    text: str
    line_idx: int

def _parse_headings(lines: Sequence[str]) -> List[Heading]:
    headings: List[Heading] = []
    for i, line in enumerate(lines):
        m = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            headings.append(Heading(level=level, text=text, line_idx=i))
    return headings

def _heading_spans(lines: Sequence[str], headings: Sequence[Heading]) -> Dict[int, Tuple[int, int]]:
    """
    Returns mapping: heading_index -> (start_line_inclusive, end_line_exclusive)
    End is next heading with level <= current level, else EOF.
    """
    spans: Dict[int, Tuple[int, int]] = {}
    n = len(lines)
    for idx, h in enumerate(headings):
        start = h.line_idx
        end = n
        for j in range(idx + 1, len(headings)):
            if headings[j].level <= h.level:
                end = headings[j].line_idx
                break
        spans[idx] = (start, end)
    return spans

def _find_section_chunk(
    body_lines: Sequence[str],
    headings: Sequence[Heading],
    spans: Dict[int, Tuple[int, int]],
    keywords: Sequence[str],
) -> Optional[str]:
    kw = tuple(k.lower() for k in keywords)
    for idx, h in enumerate(headings):
        ht = h.text.lower()
        if any(k in ht for k in kw):
            start, end = spans[idx]
            return "\n".join(body_lines[start:end]).strip()
    # Fallback: try "pseudo headings" like "**Inputs**" or "Inputs:"
    body = "\n".join(body_lines)
    for k in kw:
        if re.search(rf"(?im)^\s*(\*\*)?{re.escape(k)}(\*\*)?\s*:?\s*$", body):
            return body  # coarse fallback
    return None

def _contains_any(text: str, needles: Sequence[str]) -> bool:
    t = text.lower()
    return any(n.lower() in t for n in needles)

def _count_decision_points(body: str) -> int:
    count = 0
    for rx in DECISION_POINT_REGEXES:
        count += len(list(rx.finditer(body)))
    # De-dupe crude overlaps
    lines = body.splitlines()
    unique = 0
    for line in lines:
        has_if = re.search(r"(?i)\bif\b", line)
        has_branch = re.search(r"(?i)\b(otherwise|else)\b", line)
        # Count if line has if + (otherwise|else), with or without then
        if has_if and has_branch:
            unique += 1
    return max(unique, count)

def _has_stop(body: str) -> bool:
    return any(rx.search(body) for rx in STOP_PATTERNS)

def _has_ask_first(body: str) -> bool:
    return any(rx.search(body) for rx in ASK_FIRST_PATTERNS)

def _extract_backticked_commands(body: str) -> List[str]:
    # Backtick inline code: `...`
    cmds = re.findall(r"`([^`]+)`", body)
    # Keep only plausible commands: contains a space OR looks like a tool invocation
    cleaned: List[str] = []
    for c in cmds:
        c2 = c.strip()
        if not c2:
            continue
        if " " in c2 or re.match(r"^[a-zA-Z0-9._/-]+$", c2):
            cleaned.append(c2)
    # deterministic order
    return cleaned

def _looks_like_dangerous_command(cmd: str) -> bool:
    c = cmd.lower()
    return any(tok in c for tok in DANGEROUS_TOKENS)

def _has_quick_check_with_expected(verification_chunk: str) -> bool:
    """
    Check if verification section has testable criteria.

    Accepts:
    - "Quick check" + "Expected" (original)
    - "Verification" heading with checkbox items
    - "Verification" heading with bullet criteria
    - Any verifiable criteria patterns
    """
    vc = verification_chunk.lower()

    # Original: Quick check + Expected
    if "quick check" in vc or "quick checks" in vc:
        for m in re.finditer(r"(?i)quick check(s)?", verification_chunk):
            window = verification_chunk[m.start() : m.start() + 400]
            if re.search(r"(?i)\bexpected\b", window):
                return True
        for line in verification_chunk.splitlines():
            if re.search(r"(?i)quick", line) and re.search(r"(?i)\bexpected\b", line):
                return True

    # New: Checkbox items (- [ ] or - [x])
    if re.search(r"^\s*[-*]\s*\[[ x]\]", verification_chunk, re.MULTILINE | re.IGNORECASE):
        return True

    # New: "complete when" or "done when" with criteria
    if re.search(r"(?i)(complete|done|finished|verified)\s+when", vc):
        # Check for bullet points or numbered items following
        if re.search(r"^\s*[-*\d]", verification_chunk, re.MULTILINE):
            return True

    # New: Verification heading with any structured criteria
    if "verification" in vc:
        # Has bullet points or numbered list
        if re.search(r"^\s*[-*]\s+\S", verification_chunk, re.MULTILINE):
            return True
        if re.search(r"^\s*\d+\.\s+\S", verification_chunk, re.MULTILINE):
            return True

    return False

def _has_objective_dod(outputs_chunk: str, body: str) -> bool:
    oc = (outputs_chunk or "").lower()
    bc = body.lower()
    has_dod_marker = ("definition of done" in oc) or ("dod" in oc) or ("definition of done" in bc) or ("dod" in bc)
    if not has_dod_marker:
        return False
    # Look for objective signals nearby (coarse).
    hay = outputs_chunk if outputs_chunk else body
    hl = hay.lower()
    if any(sig in hl for sig in OBJECTIVE_CHECK_SIGNALS):
        return True
    # Or: any backticked command in DoD/outputs area
    if re.search(r"`[^`]+`", hay):
        return True
    return False

def _procedure_is_numbered(procedure_chunk: str) -> bool:
    for line in procedure_chunk.splitlines():
        if re.match(r"^\s*\d+\.\s+\S+", line):
            return True
    return False

def _assumptions_declared(body: str, inputs_chunk: Optional[str]) -> bool:
    hay = (inputs_chunk or body).lower()
    markers = (
        "constraints/assumptions",
        "assumptions",
        "constraints",
        "no network",
        "network",
        "tools",
        "permissions",
        "repo layout",
        "working directory",
        "env var",
        "environment variable",
        "fallback",
        "manual inspection",
        "paste",
    )
    return any(m in hay for m in markers)

def lint_text(md_text: str, *, assumed_annex: Optional[str] = None) -> Tuple[List[str], List[str]]:
    """
    Returns:
      (strict_fail_codes, strict_details)
    """
    body = _strip_frontmatter(md_text)
    lines = body.splitlines()
    headings = _parse_headings(lines)
    spans = _heading_spans(lines, headings)

    missing_areas: List[str] = []
    section_chunks: Dict[str, Optional[str]] = {}

    for area, keys in CONTENT_AREAS.items():
        chunk = _find_section_chunk(lines, headings, spans, keys)
        section_chunks[area] = chunk
        if chunk is None:
            missing_areas.append(area)

    strict_fail_codes: List[str] = []
    strict_details: List[str] = []

    if missing_areas:
        strict_fail_codes.append("FAIL.missing-content-areas")
        strict_details.append(f"Missing content areas: {', '.join(sorted(missing_areas))}")

    outputs_chunk = section_chunks.get("outputs") or ""
    verification_chunk = section_chunks.get("verification") or ""
    procedure_chunk = section_chunks.get("procedure") or ""
    inputs_chunk = section_chunks.get("inputs")

    # FAIL.no-objective-dod
    if not _has_objective_dod(outputs_chunk, body):
        strict_fail_codes.append("FAIL.no-objective-dod")
        strict_details.append("Outputs/DoD: could not detect an objective, checkable DoD (look for 'Definition of Done' + an observable check).")

    # FAIL.no-stop-ask
    if not _has_stop(body):
        strict_fail_codes.append("FAIL.no-stop-ask")
        strict_details.append("No explicit STOP/ask behavior detected (need at least one STOP for missing inputs or ambiguity).")

    # FAIL.no-quick-check
    if not _has_quick_check_with_expected(verification_chunk):
        strict_fail_codes.append("FAIL.no-quick-check")
        strict_details.append("Verification: could not find a 'Quick check' with an 'Expected' result shape.")

    # FAIL.too-few-decision-points
    dp_count = _count_decision_points(body)
    if dp_count < 2:
        strict_fail_codes.append("FAIL.too-few-decision-points")
        strict_details.append(f"Decision points: found {dp_count} explicit 'If ... then ... otherwise ...' decision points (need ≥2 or a justified exception).")

    # FAIL.non-operational-procedure
    if not _procedure_is_numbered(procedure_chunk):
        strict_fail_codes.append("FAIL.non-operational-procedure")
        strict_details.append("Procedure: could not detect a numbered procedure (lines like '1. ...').")

    # FAIL.undeclared-assumptions
    if not _assumptions_declared(body, inputs_chunk):
        strict_fail_codes.append("FAIL.undeclared-assumptions")
        strict_details.append("Assumptions: could not detect constraints/assumptions (tools/network/permissions/repo) or fallbacks.")

    # FAIL.unsafe-default (heuristic)
    # Only check inline backtick commands, not fenced code blocks (examples)
    body_no_fenced = _strip_fenced_code_blocks(body)
    backticked_cmds = _extract_backticked_commands(body_no_fenced)
    dangerous_cmds = [c for c in backticked_cmds if _looks_like_dangerous_command(c)]
    if dangerous_cmds and not _has_ask_first(body):
        strict_fail_codes.append("FAIL.unsafe-default")
        strict_details.append(
            "Unsafe default heuristic: detected potentially destructive commands without an ask-first gate. "
            f"Examples: {', '.join(dangerous_cmds[:3])}"
        )

    # Deterministic ordering / de-dupe
    strict_fail_codes = sorted(set(strict_fail_codes), key=lambda x: STRICT_FAIL_CODES.index(x) if x in STRICT_FAIL_CODES else 999)
    strict_details = list(dict.fromkeys(strict_details))

    # Attach strict_details to semantic? We'll return strict_details separately via wrapper.
    # For API simplicity, we embed strict_details into strict_fail_codes? No — callers keep details separately.
    return strict_fail_codes, strict_details

def lint_path(path: Path, *, annex: Optional[str] = None) -> FileLintResult:
    text = path.read_text(encoding="utf-8")
    strict_fail_codes, strict_details = lint_text(text, assumed_annex=annex)

    if strict_fail_codes:
        disposition = "FAIL"
    else:
        disposition = "PASS"

    return FileLintResult(
        path=str(path),
        disposition=disposition,
        strict_fail_codes=strict_fail_codes,
        strict_details=strict_details,
    )


def lint_text_relaxed(md_text: str, *, assumed_annex: Optional[str] = None) -> Tuple[List[str], List[str]]:
    """
    Relaxed linting: PASS on structural presence, WARN on phrasing.

    Returns:
      (strict_fail_codes, warnings) - fail_codes only for missing structure
    """
    body = _strip_frontmatter(md_text)
    lines = body.splitlines()
    headings = _parse_headings(lines)
    spans = _heading_spans(lines, headings)

    missing_areas: List[str] = []
    section_chunks: Dict[str, Optional[str]] = {}

    for area, keys in CONTENT_AREAS.items():
        chunk = _find_section_chunk(lines, headings, spans, keys)
        section_chunks[area] = chunk
        if chunk is None:
            missing_areas.append(area)

    strict_fail_codes: List[str] = []
    warnings: List[str] = []

    # Only fail on truly missing content areas
    if missing_areas:
        strict_fail_codes.append("FAIL.missing-content-areas")
        warnings.append(f"Missing content areas: {', '.join(sorted(missing_areas))}")

    # Everything else becomes a warning in relaxed mode
    outputs_chunk = section_chunks.get("outputs") or ""
    verification_chunk = section_chunks.get("verification") or ""
    procedure_chunk = section_chunks.get("procedure") or ""
    inputs_chunk = section_chunks.get("inputs")

    if not _has_objective_dod(outputs_chunk, body):
        warnings.append("WARN: No objective DoD detected (consider adding 'Definition of Done' with checkable criteria)")

    if not _has_stop(body):
        warnings.append("WARN: No explicit STOP behavior (consider adding STOP for missing inputs)")

    if not _has_quick_check_with_expected(verification_chunk):
        warnings.append("WARN: Verification could be strengthened with 'Quick check' + 'Expected'")

    dp_count = _count_decision_points(body)
    if dp_count < 2:
        warnings.append(f"WARN: Found {dp_count} decision points (consider adding 'if...then...otherwise' patterns)")

    if not _procedure_is_numbered(procedure_chunk):
        warnings.append("WARN: Procedure not numbered (consider '1. ...' format)")

    if not _assumptions_declared(body, inputs_chunk):
        warnings.append("WARN: No explicit assumptions/constraints declared")

    # Unsafe default check (still important even in relaxed)
    body_no_fenced = _strip_fenced_code_blocks(body)
    backticked_cmds = _extract_backticked_commands(body_no_fenced)
    dangerous_cmds = [c for c in backticked_cmds if _looks_like_dangerous_command(c)]
    if dangerous_cmds and not _has_ask_first(body):
        warnings.append(f"WARN: Potentially destructive commands without ask-first: {', '.join(dangerous_cmds[:3])}")

    return strict_fail_codes, warnings


def lint_path_relaxed(path: Path, *, annex: Optional[str] = None) -> FileLintResult:
    text = path.read_text(encoding="utf-8")
    strict_fail_codes, warnings = lint_text_relaxed(text, assumed_annex=annex)

    if strict_fail_codes:
        disposition = "FAIL"
    else:
        disposition = "PASS"

    return FileLintResult(
        path=str(path),
        disposition=disposition,
        strict_fail_codes=strict_fail_codes,
        strict_details=warnings,  # Reuse field for warnings
    )

def _iter_skill_files(paths: Sequence[Path], recursive: bool) -> List[Path]:
    results: List[Path] = []
    for p in paths:
        if p.is_dir():
            if recursive:
                results.extend(sorted(p.rglob("SKILL.md")))
            else:
                results.extend(sorted(p.glob("SKILL.md")))
        else:
            results.append(p)
    # deterministic unique list
    uniq: Dict[str, Path] = {str(x.resolve()): x for x in results if x.exists()}
    return [uniq[k] for k in sorted(uniq.keys())]

def _print_text(results: Sequence[FileLintResult]) -> None:
    for r in results:
        print(f"== {r.path} ==")
        print(f"Disposition: {r.disposition}")
        if r.strict_fail_codes:
            print("\nStrict-spec FAIL codes:")
            for code in r.strict_fail_codes:
                print(f"- {code}")
            if r.strict_details:
                print("\nStrict-spec details:")
                for d in r.strict_details:
                    print(f"- {d}")
        print()

def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Lint SKILL.md bodies (strict fail codes first; structural compliance + minimum safety gates only).")
    ap.add_argument("paths", nargs="+", help="SKILL.md file(s) or directory(ies) to scan")
    ap.add_argument("--recursive", action="store_true", help="Recurse into directories")
    ap.add_argument("--format", choices=("text", "json"), default="text", help="Output format")
    ap.add_argument("--relaxed", action="store_true", help="Relaxed mode: PASS on structure, WARN on phrasing")
    args = ap.parse_args(list(argv) if argv is not None else None)

    in_paths = [Path(p) for p in args.paths]
    files = _iter_skill_files(in_paths, recursive=args.recursive)
    if not files:
        print("No files found.", file=sys.stderr)
        return 2

    if args.relaxed:
        results = [lint_path_relaxed(p) for p in files]
    else:
        results = [lint_path(p) for p in files]

    if args.format == "json":
        payload = [dataclasses.asdict(r) for r in results]
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _print_text(results)

    any_fail = any(r.disposition == "FAIL" for r in results)

    if any_fail:
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
