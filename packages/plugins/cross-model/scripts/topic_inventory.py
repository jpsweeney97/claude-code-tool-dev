#!/usr/bin/env python3
"""CCDI topic inventory CLI.

Two subcommands:
- classify: classify text against inventory, emit ClassifierResult JSON
- build-packet: build injection packet from search results, emit markdown

Flag name enforcement:
- classify uses --inventory (NOT --inventory-snapshot)
- build-packet uses --inventory-snapshot (NOT --inventory)

Exit codes: 0 on success, non-zero on error. JSON on stdout, errors on stderr.

Usage:
    scripts/topic_inventory.py classify --text-file <path> --inventory <path>
    scripts/topic_inventory.py build-packet --results-file <path> --mode initial|mid_turn [...]
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from scripts.ccdi.classifier import classify
from scripts.ccdi.config import CCDIConfigLoader, BUILTIN_DEFAULTS
from scripts.ccdi.inventory import load_inventory
from scripts.ccdi.packets import build_packet, render_initial, render_mid_turn
from scripts.ccdi.registry import load_registry, mark_injected, write_suppressed
from scripts.ccdi.types import ClassifierResult, MatchedAlias, ResolvedTopic

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Agent gate — hardcoded thresholds, NOT configurable
# ---------------------------------------------------------------------------

_AGENT_HIGH_COUNT = 1
_AGENT_MEDIUM_SAME_FAMILY = 2


def check_agent_gate(result: ClassifierResult) -> bool:
    """Agent-side pre-dispatch gate. Uses HARDCODED thresholds, NOT config.

    Dispatch if:
    - At least _AGENT_HIGH_COUNT high-confidence topics, OR
    - At least _AGENT_MEDIUM_SAME_FAMILY medium-confidence topics in same family
    """
    high_count = sum(
        1 for t in result.resolved_topics if t.confidence == "high"
    )
    if high_count >= _AGENT_HIGH_COUNT:
        return True

    # Count medium-confidence per family
    family_medium: dict[str, int] = {}
    for t in result.resolved_topics:
        if t.confidence == "medium":
            family_medium[t.family_key] = family_medium.get(t.family_key, 0) + 1

    for count in family_medium.values():
        if count >= _AGENT_MEDIUM_SAME_FAMILY:
            return True

    return False


# ---------------------------------------------------------------------------
# ClassifierResult serialization
# ---------------------------------------------------------------------------


def _serialize_classifier_result(result: ClassifierResult) -> dict:
    """Serialize ClassifierResult to JSON-compatible dict."""
    return {
        "resolved_topics": [
            {
                "topic_key": t.topic_key,
                "family_key": t.family_key,
                "coverage_target": t.coverage_target,
                "confidence": t.confidence,
                "facet": t.facet,
                "matched_aliases": [
                    {
                        "text": ma.text,
                        "span": list(ma.span),
                        "weight": ma.weight,
                    }
                    for ma in t.matched_aliases
                ],
                "reason": t.reason,
            }
            for t in result.resolved_topics
        ],
        "suppressed_candidates": [
            {
                "topic_key": s.topic_key,
                "reason": s.reason,
            }
            for s in result.suppressed_candidates
        ],
    }


# ---------------------------------------------------------------------------
# classify subcommand
# ---------------------------------------------------------------------------


def _cmd_classify(args: argparse.Namespace) -> int:
    """Execute classify subcommand."""
    # Load input text
    text_path = Path(args.text_file)
    if not text_path.exists():
        print(f"Error: text file not found: {text_path}", file=sys.stderr)
        return 1

    try:
        text = text_path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, ValueError) as exc:
        print(f"Error: cannot read text file: {exc}", file=sys.stderr)
        return 1

    # Validate text is not binary garbage
    if "\x00" in text:
        print("Error: text file appears to be binary", file=sys.stderr)
        return 1

    # Load inventory
    inv_path = Path(args.inventory)
    if not inv_path.exists():
        print(f"Error: inventory file not found: {inv_path}", file=sys.stderr)
        return 1

    try:
        inventory = load_inventory(inv_path)
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        print(f"Error: failed to load inventory: {exc}", file=sys.stderr)
        return 1

    # Build config from defaults (CLI does not accept config path for classify)
    config = CCDIConfigLoader("/dev/null").load()

    # Run classifier
    result = classify(text, inventory, config)

    # Write JSON to stdout
    json.dump(_serialize_classifier_result(result), sys.stdout, indent=2)
    print(file=sys.stdout)  # trailing newline
    return 0


# ---------------------------------------------------------------------------
# build-packet subcommand
# ---------------------------------------------------------------------------


def _validate_build_packet_flags(args: argparse.Namespace) -> str | None:
    """Validate flag dependencies. Returns error message or None."""
    # --registry-file requires --inventory-snapshot
    if args.registry_file and not args.inventory_snapshot:
        return "--registry-file requires --inventory-snapshot"

    # --registry-file requires --topic-key
    if args.registry_file and not args.topic_key:
        return "--registry-file requires --topic-key"

    # --mark-injected requires --coverage-target, --topic-key, --facet
    if args.mark_injected:
        if not args.coverage_target:
            return "--mark-injected requires --coverage-target"
        if not args.topic_key:
            return "--mark-injected requires --topic-key"
        if not args.facet:
            return "--mark-injected requires --facet"

    return None


def _cmd_build_packet(args: argparse.Namespace) -> int:
    """Execute build-packet subcommand."""
    # Validate flag dependencies
    err = _validate_build_packet_flags(args)
    if err:
        print(f"Error: {err}", file=sys.stderr)
        return 1

    # Load search results
    results_path = Path(args.results_file)
    if not results_path.exists():
        print(f"Error: results file not found: {results_path}", file=sys.stderr)
        return 1

    try:
        results = json.loads(results_path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Error: failed to load results file: {exc}", file=sys.stderr)
        return 1

    # Build config from defaults
    config = CCDIConfigLoader("/dev/null").load()

    # Load registry entry if registry-file provided
    registry_entry = None
    if args.registry_file:
        seed = load_registry(args.registry_file)
        for entry in seed.entries:
            if entry.topic_key == args.topic_key:
                registry_entry = entry
                break

    # Build packet
    facet = args.facet or "overview"
    packet = build_packet(
        results,
        args.mode,
        config,
        registry_entry=registry_entry,
        facet=facet,
    )

    # Handle empty output
    if packet is None:
        # Automatic suppression: only when --registry-file is present
        if args.registry_file and args.topic_key:
            # Determine suppression reason
            docs_epoch = None
            if args.inventory_snapshot:
                try:
                    inv = load_inventory(args.inventory_snapshot)
                    docs_epoch = inv.docs_epoch
                except Exception:
                    pass

            # Check if redundant (all chunks already injected)
            if registry_entry is not None:
                injected_ids = set(registry_entry.coverage_injected_chunk_ids)
                all_chunk_ids = {r["chunk_id"] for r in results}
                if all_chunk_ids and all_chunk_ids.issubset(injected_ids):
                    reason = "redundant"
                else:
                    reason = "weak_results"
            else:
                reason = "weak_results"

            write_suppressed(
                args.registry_file,
                args.topic_key,
                reason,
                docs_epoch,
            )

        # Empty stdout, exit 0
        return 0

    # Render markdown
    if args.mode == "mid_turn":
        output = render_mid_turn(packet)
    else:
        output = render_initial(packet)

    # --mark-injected: commit injection to registry
    if args.mark_injected and args.registry_file:
        chunk_ids = []
        for fact in packet.facts:
            for ref in fact.refs:
                if ref.chunk_id not in chunk_ids:
                    chunk_ids.append(ref.chunk_id)

        mark_injected(
            args.registry_file,
            args.topic_key,
            facet,
            args.coverage_target,
            chunk_ids,
            query_fingerprint=f"cli:{args.topic_key}:{facet}",
            turn=0,
        )

    # Write markdown to stdout
    print(output, end="")
    return 0


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    """Build argparse parser with classify and build-packet subcommands."""
    parser = argparse.ArgumentParser(
        prog="topic_inventory",
        description="CCDI topic inventory CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- classify ---
    classify_parser = subparsers.add_parser(
        "classify",
        help="Classify text against topic inventory",
    )
    classify_parser.add_argument(
        "--text-file", required=True,
        help="Path to text file to classify",
    )
    classify_parser.add_argument(
        "--inventory", required=True,
        help="Path to compiled inventory JSON",
    )

    # --- build-packet ---
    bp_parser = subparsers.add_parser(
        "build-packet",
        help="Build injection packet from search results",
    )
    bp_parser.add_argument(
        "--results-file", required=True,
        help="Path to search results JSON",
    )
    bp_parser.add_argument(
        "--mode", required=True, choices=["initial", "mid_turn"],
        help="Packet mode: initial or mid_turn",
    )
    bp_parser.add_argument(
        "--registry-file",
        help="Path to session registry JSON",
    )
    bp_parser.add_argument(
        "--topic-key",
        help="Topic key for registry operations",
    )
    bp_parser.add_argument(
        "--facet",
        help="Facet for packet building",
    )
    bp_parser.add_argument(
        "--coverage-target", choices=["family", "leaf"],
        help="Coverage target: family or leaf",
    )
    bp_parser.add_argument(
        "--inventory-snapshot",
        help="Path to inventory snapshot for epoch lookup",
    )
    bp_parser.add_argument(
        "--mark-injected", action="store_true",
        help="Commit injection to registry after building packet",
    )

    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    # Configure logging to stderr only
    logging.basicConfig(
        level=logging.WARNING,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )

    parser = _build_parser()

    # Flag name enforcement: reject wrong flag names before argparse sees them
    raw_args = argv if argv is not None else sys.argv[1:]

    # Detect subcommand from raw args
    subcommand = None
    for arg in raw_args:
        if arg in ("classify", "build-packet"):
            subcommand = arg
            break

    if subcommand == "classify" and "--inventory-snapshot" in raw_args:
        print(
            "Error: classify uses --inventory, not --inventory-snapshot",
            file=sys.stderr,
        )
        return 1

    if subcommand == "build-packet" and "--inventory" in raw_args:
        print(
            "Error: build-packet uses --inventory-snapshot, not --inventory",
            file=sys.stderr,
        )
        return 1

    try:
        args = parser.parse_args(raw_args)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 1

    if args.command == "classify":
        return _cmd_classify(args)
    elif args.command == "build-packet":
        return _cmd_build_packet(args)
    else:
        parser.print_help(sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
