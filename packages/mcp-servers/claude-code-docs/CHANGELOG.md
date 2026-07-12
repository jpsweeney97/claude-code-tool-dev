# Changelog

All notable changes to this package are documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 1.1.0 - 2026-07-12

### Added

- `gateways` category (29 categories total) with ~30 new URL slug mappings, accepted by the `search_docs` `category` filter alongside a new `gateway` alias.
- `resolveSegmentCategory`: longest hyphen-bounded prefix resolution, so new sub-pages of known doc families (e.g. `llm-gateway-*`, `mcp-*`, `desktop-*`) categorize correctly without a mapping-table edit.
- Warn-only `fallback_ratio_high` canary: fires when ≥ 10% of sections fall back to `uncategorized` (official trust mode only; excluded from baseline advancement). Surfaced in `get_status` warnings.
- Live golden-query suite (`tests/golden-queries.live.test.ts`): all 44 shared queries run against the real cached corpus through the production transform (`sectionToMarkdownFile`, extracted from the loader). The shared query table (35 mocked + 9 live-only) is pinned by a cardinality contract test.

### Changed

- `llm-gateway` docs recategorized from `providers` to the new `gateways` category.
- `getUnmappedSegments` now shares `resolveSegmentCategory` with `deriveCategory`, so fallback diagnostics always agree with actual chunk categorization.
- `INGESTION_VERSION` 6 → 7 and `CANARY_VERSION` 2 → 3: existing index caches rebuild automatically on first load.
- README and CLAUDE.md document the gateways category, prefix resolver, and ratio canary.

## 1.0.0 - 2026-01-26

Initial release: BM25-indexed Claude Code documentation search over MCP stdio, exposing `search_docs`, `reload_docs`, `dump_index_metadata`, and `get_status`.
