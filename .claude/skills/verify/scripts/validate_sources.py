#!/usr/bin/env python3
"""
Validate source URLs in known-claims.md.

Checks that documentation URLs are accessible and reports broken links
that may indicate stale or invalid claims.

Exit codes:
    0 - All URLs valid
    1 - Input error
    2 - One or more URLs invalid
"""

from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple


class URLResult(NamedTuple):
    """Result of URL validation."""
    url: str
    section: str
    status: int | None  # HTTP status code or None if unreachable
    error: str | None   # Error message if failed


@dataclass
class ValidationResult:
    """Overall validation result."""
    valid: list[URLResult] = field(default_factory=list)
    invalid: list[URLResult] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def extract_source_urls(content: str) -> dict[str, str]:
    """Extract section -> source URL mapping from known-claims.md."""
    urls: dict[str, str] = {}
    current_section = None

    for line in content.splitlines():
        # Match section headers like "## Skills"
        section_match = re.match(r"^## (\w+)", line)
        if section_match:
            current_section = section_match.group(1)
            continue

        # Match source lines like "**Source:** https://..."
        source_match = re.match(r"\*\*Source:\*\*\s+(https?://\S+)", line)
        if source_match and current_section:
            urls[current_section] = source_match.group(1)

    return urls


def validate_url(url: str, section: str, timeout: int = 10) -> URLResult:
    """Check if URL is accessible using HEAD request."""
    try:
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", "verify-skill-validator/1.0")

        with urllib.request.urlopen(req, timeout=timeout) as response:
            return URLResult(url=url, section=section, status=response.status, error=None)

    except urllib.error.HTTPError as e:
        return URLResult(url=url, section=section, status=e.code, error=str(e.reason))
    except urllib.error.URLError as e:
        return URLResult(url=url, section=section, status=None, error=str(e.reason))
    except TimeoutError:
        return URLResult(url=url, section=section, status=None, error="Timeout")
    except Exception as e:
        return URLResult(url=url, section=section, status=None, error=str(e))


def validate_sources(
    known_path: Path,
    timeout: int = 10,
    rate_limit: float = 1.0,
    section_filter: str | None = None,
) -> ValidationResult:
    """Validate all source URLs in known-claims.md."""
    result = ValidationResult()

    if not known_path.exists():
        return result

    content = known_path.read_text(encoding="utf-8")
    urls = extract_source_urls(content)

    # Filter to specific section if requested
    if section_filter:
        section_lower = section_filter.lower()
        urls = {k: v for k, v in urls.items() if k.lower() == section_lower}

    for i, (section, url) in enumerate(urls.items()):
        # Rate limiting between requests
        if i > 0 and rate_limit > 0:
            time.sleep(rate_limit)

        # Skip placeholder URLs
        if "(pending" in url.lower():
            result.skipped.append(f"{section}: {url}")
            continue

        url_result = validate_url(url, section, timeout)

        if url_result.error is None and url_result.status and 200 <= url_result.status < 400:
            result.valid.append(url_result)
        else:
            result.invalid.append(url_result)

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate source URLs in known-claims.md")
    parser.add_argument(
        "--known-claims",
        type=Path,
        default=Path(__file__).parent.parent / "references" / "known-claims.md",
        help="Path to known-claims.md",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Timeout in seconds per URL (default: 10)",
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=1.0,
        help="Seconds between requests to avoid rate limiting (default: 1.0)",
    )
    parser.add_argument(
        "--section",
        type=str,
        default=None,
        help="Only validate URLs for this section",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    args = parser.parse_args()

    if not args.known_claims.exists():
        print(f"Error: {args.known_claims} not found", file=sys.stderr)
        return 1

    result = validate_sources(
        args.known_claims,
        timeout=args.timeout,
        rate_limit=args.rate_limit,
        section_filter=args.section,
    )

    if args.json:
        import json
        output = {
            "valid": [{"url": r.url, "section": r.section, "status": r.status} for r in result.valid],
            "invalid": [{"url": r.url, "section": r.section, "status": r.status, "error": r.error} for r in result.invalid],
            "skipped": result.skipped,
        }
        print(json.dumps(output, indent=2))
    else:
        print("Source URL Validation Report\n")

        if result.valid:
            print(f"Valid ({len(result.valid)}):")
            for r in result.valid:
                print(f"  [ok] {r.section}: {r.url} [{r.status}]")

        if result.invalid:
            print(f"\nInvalid ({len(result.invalid)}):")
            for r in result.invalid:
                status = r.status or "unreachable"
                print(f"  [!] {r.section}: {r.url} [{status}] - {r.error}")

        if result.skipped:
            print(f"\nSkipped ({len(result.skipped)}):")
            for s in result.skipped:
                print(f"  - {s}")

        print(f"\nSummary: {len(result.valid)} valid, {len(result.invalid)} invalid, {len(result.skipped)} skipped")

    return 2 if result.invalid else 0


if __name__ == "__main__":
    sys.exit(main())
