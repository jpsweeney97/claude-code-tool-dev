# Synthesis Report: verify skill vs docs-kb

**Date:** 2026-01-06
**Calibration:** Medium
**Sources:**
1. `/Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/verify` (verify skill)
2. `/Users/jp/Projects/active/docs-kb` (docs-kb knowledge base)

---

## Executive Summary

The verify skill and docs-kb are **complementary systems** that can be integrated to improve verification capabilities without replacing either's core purpose.

**Key findings:**
- verify skill: Domain-specific Claude Code fact-checking with algorithmic (Jaccard) matching
- docs-kb: Generic semantic search knowledge base with MCP tools and embedding-based retrieval
- **Integration opportunity:** docs-kb can serve as a knowledge backend while verify skill retains its specialized workflow

**Recommended actions:**
1. ✅ Add Claude Code docs to docs-kb as a source
2. ✅ Add semantic matching option to verify skill
3. ⚠️ Consider docs-kb as offline fallback (optional)
4. ❌ Do NOT merge the two verify skills (different purposes)

---

## Triage Scores

| Source | Relevance | Activity | Quality | Alignment | Total | Rating |
|--------|-----------|----------|---------|-----------|-------|--------|
| verify skill | +2 | +2 | +1 | +2 | **7** | High |
| docs-kb | +1 | +2 | +2 | +1 | **6** | High |

Both passed triage with High ratings.

---

## Architecture Comparison

### verify skill

```
PURPOSE: Fact-check Claude Code claims
WORKFLOW: 7-step process with cache checking + agent verification
MATCHING: Weighted Jaccard with domain term boosting
STORAGE: Markdown tables (known-claims.md, pending-claims.md)
QUERY SOURCE: claude-code-guide agent via Task tool
STRENGTHS: Domain-tuned, deterministic, version-aware staleness
```

### docs-kb

```
PURPOSE: Generic documentation semantic search
WORKFLOW: Ingest → chunk → embed → store → query
MATCHING: Cosine similarity via fastembed + sqlite-vec
STORAGE: SQLite with vector embeddings
QUERY SOURCE: Local database
STRENGTHS: Semantic search, offline capable, MCP integration
```

---

## Value Inventory

| ID | Item | Status | Evidence |
|----|------|--------|----------|
| V1 | Ingest Claude Code docs into docs-kb | ✅ Candidate | Enables semantic search, no conflict |
| V2 | Use docs-kb `ask` as query backend | ⚠️ Conditional | High effort, changes core mechanism |
| V3 | Merge verify skills | ❌ Excluded | Different scopes, would dilute both |
| V4 | Adopt heading-aware chunking | ✅ Candidate | Enhancement, low cost |
| V5 | Add semantic similarity option | ✅ Candidate | Blended matching, best of both |
| V6 | Use docs-kb MCP server | ⚠️ Conditional | Adds deployment dependency |

---

## Conflict Resolutions

### C1: Query Backend (Philosophical)

| Option | Freshness | Latency | Offline |
|--------|-----------|---------|---------|
| claude-code-guide | ✅ Always current | Higher | ❌ No |
| docs-kb | ⚠️ Snapshot | Lower | ✅ Yes |

**Resolution:** Hybrid — Keep agent as primary, add docs-kb as optional fallback
**Confidence:** Probable (PREFERENCE)

### C2: Matching Algorithm (Complementary)

**Resolution:** Blend — Primary Jaccard + optional semantic boost
**Formula:** `0.7 * jaccard + 0.3 * cosine` when `--semantic` enabled
**Confidence:** Probable (EMPIRICAL)

### C3: Skill Scope (Incompatible)

| Skill | Purpose |
|-------|---------|
| tool-dev:verify | Claude Code claims → official docs |
| docs-kb:verify | API usage → any indexed docs |

**Resolution:** Keep separate — Different workflows, different audiences
**Confidence:** Certain (EMPIRICAL)

---

## Integration Plan

### Phase 1: Add Claude Code Source (Recommended)

**Effort:** 30 min
**File:** `docs-kb/docs_kb/sources/configs.py`

```python
WebsiteSource(
    id="claude-code",
    name="Claude Code Documentation",
    base_url="https://code.claude.com/docs/en/",
    link_pattern=r"/docs/en/[a-z-]+\.md",
    content_selector="main",
    exclude_selectors=["nav", "footer", ".sidebar"],
    trigger_patterns=["Claude Code", "hooks", "skills", "MCP"],
)
```

### Phase 2: Semantic Matching Option (Recommended)

**Effort:** 30 min
**Files:** `verify/scripts/match_claim.py`, `verify/scripts/_common.py`

Add `--semantic` flag for blended scoring when Jaccard confidence is low.

### Phase 3: Fallback Integration (Optional)

**Effort:** 1-2 hr
**Trigger:** User needs offline verification
**Change:** Modify SKILL.md Step 3 to check docs-kb when agent unavailable

---

## Rollback Strategy

All integrations are additive. Rollback by:
1. Remove Claude Code source config from docs-kb
2. Remove `--semantic` flag from match_claim.py
3. No SKILL.md changes if Phase 3 not implemented

---

## Lessons Learned

1. **Complementary beats unified:** Different tools for different problems work better than forced mergers
2. **Algorithmic + semantic:** Jaccard (deterministic) and cosine (semantic) complement each other
3. **Keep domain focus:** verify skill's Claude Code specialization is a feature, not a limitation
4. **Infrastructure as option:** docs-kb MCP server is useful but shouldn't be mandatory
