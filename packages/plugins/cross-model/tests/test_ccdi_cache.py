"""Tests for CCDI session-local cache."""

from __future__ import annotations

from scripts.ccdi.cache import CCDICache


# ---------------------------------------------------------------------------
# Result cache
# ---------------------------------------------------------------------------


class TestResultCacheHitAvoidsResearch:
    """Same fingerprint returns cached results without re-search."""

    def test_put_then_get_returns_same_results(self) -> None:
        cache = CCDICache()
        results = [{"chunk_id": "c1", "score": 0.9}]
        cache.put_results("some query", "v2", results)
        assert cache.get_results("some query", "v2") is results

    def test_miss_returns_none(self) -> None:
        cache = CCDICache()
        assert cache.get_results("unknown query", "v1") is None

    def test_normalized_whitespace_is_cache_hit(self) -> None:
        cache = CCDICache()
        results = [{"chunk_id": "c1"}]
        cache.put_results("  some   query  ", "v1", results)
        assert cache.get_results("some query", "v1") is results

    def test_normalized_case_is_cache_hit(self) -> None:
        cache = CCDICache()
        results = [{"chunk_id": "c1"}]
        cache.put_results("Some Query", "v1", results)
        assert cache.get_results("some query", "v1") is results


# ---------------------------------------------------------------------------
# Negative cache
# ---------------------------------------------------------------------------


class TestNegativeCachePreventsRetry:
    """Weak results are flagged so the query is not re-searched."""

    def test_mark_negative_then_check(self) -> None:
        cache = CCDICache()
        cache.mark_negative("bad query", "v1")
        assert cache.is_negative("bad query", "v1") is True

    def test_unmarked_query_is_not_negative(self) -> None:
        cache = CCDICache()
        assert cache.is_negative("good query", "v1") is False

    def test_negative_uses_normalized_fingerprint(self) -> None:
        cache = CCDICache()
        cache.mark_negative("  Bad  Query ", "v1")
        assert cache.is_negative("bad query", "v1") is True


# ---------------------------------------------------------------------------
# Packet cache
# ---------------------------------------------------------------------------


class TestPacketCacheServesExisting:
    """Same (topic_key, facet) returns cached packet."""

    def test_put_then_get_returns_same_packet(self) -> None:
        cache = CCDICache()
        packet = {"facts": ["fact1"], "token_count": 42}
        cache.put_packet("topic/a", "overview", packet)
        assert cache.get_packet("topic/a", "overview") is packet

    def test_miss_returns_none(self) -> None:
        cache = CCDICache()
        assert cache.get_packet("topic/a", "overview") is None

    def test_different_facet_is_miss(self) -> None:
        cache = CCDICache()
        packet = {"facts": ["fact1"]}
        cache.put_packet("topic/a", "overview", packet)
        assert cache.get_packet("topic/a", "configuration") is None

    def test_different_topic_is_miss(self) -> None:
        cache = CCDICache()
        packet = {"facts": ["fact1"]}
        cache.put_packet("topic/a", "overview", packet)
        assert cache.get_packet("topic/b", "overview") is None


# ---------------------------------------------------------------------------
# docs_epoch in cache keys
# ---------------------------------------------------------------------------


class TestCacheKeysIncludeDocsEpoch:
    """Same query with different docs_epoch is a cache miss."""

    def test_different_epoch_is_result_miss(self) -> None:
        cache = CCDICache()
        results = [{"chunk_id": "c1"}]
        cache.put_results("query", "v1", results)
        assert cache.get_results("query", "v2") is None

    def test_none_epoch_vs_string_epoch_is_miss(self) -> None:
        cache = CCDICache()
        results = [{"chunk_id": "c1"}]
        cache.put_results("query", None, results)
        assert cache.get_results("query", "v1") is None

    def test_none_epoch_is_self_consistent(self) -> None:
        cache = CCDICache()
        results = [{"chunk_id": "c1"}]
        cache.put_results("query", None, results)
        assert cache.get_results("query", None) is results

    def test_different_epoch_is_negative_miss(self) -> None:
        cache = CCDICache()
        cache.mark_negative("query", "v1")
        assert cache.is_negative("query", "v2") is False

    def test_none_epoch_vs_string_epoch_is_negative_miss(self) -> None:
        cache = CCDICache()
        cache.mark_negative("query", None)
        assert cache.is_negative("query", "v1") is False


# ---------------------------------------------------------------------------
# Per-session isolation
# ---------------------------------------------------------------------------


class TestCacheIsPerSessionOnly:
    """New cache instance has no carryover from another instance."""

    def test_new_instance_has_no_results(self) -> None:
        cache1 = CCDICache()
        cache1.put_results("query", "v1", [{"chunk_id": "c1"}])

        cache2 = CCDICache()
        assert cache2.get_results("query", "v1") is None

    def test_new_instance_has_no_negatives(self) -> None:
        cache1 = CCDICache()
        cache1.mark_negative("query", "v1")

        cache2 = CCDICache()
        assert cache2.is_negative("query", "v1") is False

    def test_new_instance_has_no_packets(self) -> None:
        cache1 = CCDICache()
        cache1.put_packet("topic/a", "overview", {"facts": []})

        cache2 = CCDICache()
        assert cache2.get_packet("topic/a", "overview") is None
