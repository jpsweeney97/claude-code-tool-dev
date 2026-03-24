"""CCDI session-local cache — avoids redundant searches and packet builds.

Three caches, all in-memory only (no persistence across sessions):

- Result cache: normalized query fingerprint → search results
- Negative cache: normalized query fingerprint → weak flag
- Packet cache: (topic_key, facet) → built FactPacket

Cache keys for result and negative caches include docs_epoch to ensure
a docs refresh invalidates stale entries. Key format matches the registry
fingerprint: ``normalize(query) + '|' + str(docs_epoch)`` where null
becomes the literal string ``'null'``.

Import pattern:
    from scripts.ccdi.cache import CCDICache
"""

from __future__ import annotations

from scripts.ccdi.registry import normalize_fingerprint


class CCDICache:
    """Session-local cache for CCDI search results, packets, and negative flags."""

    def __init__(self) -> None:
        self._result_cache: dict[str, list[dict]] = {}
        self._packet_cache: dict[tuple[str, str], object] = {}  # (topic_key, facet)
        self._negative_cache: set[str] = set()  # fingerprints with weak results

    # -- Result cache -------------------------------------------------------

    def get_results(self, query: str, docs_epoch: str | None) -> list[dict] | None:
        """Return cached results for query+epoch, or None on miss."""
        key = normalize_fingerprint(query, docs_epoch)
        return self._result_cache.get(key)

    def put_results(
        self, query: str, docs_epoch: str | None, results: list[dict]
    ) -> None:
        """Store search results under the normalized fingerprint."""
        key = normalize_fingerprint(query, docs_epoch)
        self._result_cache[key] = results

    # -- Negative cache -----------------------------------------------------

    def is_negative(self, query: str, docs_epoch: str | None) -> bool:
        """Return True if this query+epoch was flagged as weak."""
        key = normalize_fingerprint(query, docs_epoch)
        return key in self._negative_cache

    def mark_negative(self, query: str, docs_epoch: str | None) -> None:
        """Flag a query+epoch as producing weak results (no retry)."""
        key = normalize_fingerprint(query, docs_epoch)
        self._negative_cache.add(key)

    # -- Packet cache -------------------------------------------------------

    def get_packet(self, topic_key: str, facet: str) -> object | None:
        """Return cached packet for (topic_key, facet), or None on miss."""
        return self._packet_cache.get((topic_key, facet))

    def put_packet(self, topic_key: str, facet: str, packet: object) -> None:
        """Store a built packet under (topic_key, facet)."""
        self._packet_cache[(topic_key, facet)] = packet
