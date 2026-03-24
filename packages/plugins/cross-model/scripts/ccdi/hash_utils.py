"""Deterministic hashing utilities for CCDI classify results.

Used by the registry and shadow-mode tracing to fingerprint classify
outputs for deduplication and change detection.
"""

from __future__ import annotations

import hashlib
import json


def classify_result_hash(
    topic_key: str,
    confidence: str,
    facet: str,
    matched_aliases: list[dict],
) -> str:
    """Deterministic hash of a per-topic classify result.

    Includes confidence, facet, and matched_aliases (not just topic_key).
    Same payload always produces the same hash (stability invariant).

    Args:
        topic_key: The topic key.
        confidence: Confidence level ("high", "medium", "low").
        facet: The resolved facet.
        matched_aliases: List of dicts with "text" and "weight" keys.

    Returns:
        First 16 hex characters of the SHA-256 hash.
    """
    payload = {
        "topic_key": topic_key,
        "confidence": confidence,
        "facet": facet,
        "matched_aliases": sorted(
            [{"text": m["text"], "weight": m["weight"]} for m in matched_aliases],
            key=lambda m: m["text"],
        ),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]
