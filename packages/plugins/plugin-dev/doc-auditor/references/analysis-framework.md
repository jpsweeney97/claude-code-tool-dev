# Analysis Framework

This reference describes the five dimensions of documentation coherence analysis. These are aspects of a single comprehensive read, NOT sequential passes.

## Overview

Coherence analysis synthesizes what documentation **actually describes** when read holistically — the "forest view" rather than individual trees.

The goal is to reconstruct the implied design from the documentation, identifying where that picture is incomplete, contradictory, or confusing.

## The Five Dimensions

### Dimension 1: Structure

**What to observe:**
- Document types (ADR, spec, guide, reference, runbook)
- Heading hierarchies and section organization
- Tables, code blocks, diagrams (note presence, don't parse)
- Metadata (titles, dates, versions, authors)

**What to report:**
- Document inventory with types
- Structural anomalies (heading skips, missing sections)
- Patterns in organization across docs

**Questions to answer:**
- What kinds of documents exist?
- Is there a consistent organizational pattern?
- Are documents structured appropriately for their type?

### Dimension 2: Connections

**What to observe:**
- Explicit links between documents
- Implicit references ("as described in...", "see the...")
- Definition sites vs. usage sites for terms
- Document clusters (what links to what)

**What to report:**
- Orphaned documents (nothing links to them)
- Hub documents (everything links to them)
- Broken or stale references
- Disconnected clusters

**Questions to answer:**
- Can a reader navigate logically through the docs?
- Are there isolated documents that might be stale?
- Which documents are most central?

### Dimension 3: Terminology

**What to observe:**
- Terms that are defined (glossary entries, inline definitions)
- Terms used but never defined
- Synonyms (same concept, different names)
- Potential homonyms (same name, different meanings)

**What to report:**
- Terminology map (key terms and where defined)
- Undefined jargon
- Naming inconsistencies

**Questions to answer:**
- Can a newcomer understand the vocabulary?
- Is terminology consistent across documents?
- Are there confusing overlaps or gaps?

### Dimension 4: Assertions

**What to observe:**
- Factual claims about the system (counts, behaviors, constraints)
- Claims about the same entity from different documents
- Potential contradictions or tensions

**What to report:**
- Key assertions per component/concept
- Contradictions with evidence from both sources
- Confidence level per assertion

**Questions to answer:**
- What does the documentation claim the system does?
- Where do documents disagree?
- Which claims seem authoritative vs. tentative?

### Dimension 5: Completeness

**What to observe:**
- Expected content that's missing (error handling, edge cases, rationale)
- Sections that are stubs or TODOs
- Asymmetries (detailed in one area, sparse in another)

**What to report:**
- Gap inventory by type
- Coverage assessment per major component

**Questions to answer:**
- What would a reader expect to find but won't?
- Where is documentation thorough vs. thin?
- What critical information is absent?

## Synthesis Process

After observing across all five dimensions, synthesize findings into a coherent picture:

1. **Executive Summary**: Write what the documentation describes as if explaining the system to someone new. This IS the "forest view" — the reconstructed design.

2. **Document Inventory**: List all documents with their types, modification dates, and connectivity (links in/out).

3. **Terminology Map**: Catalog key terms, where they're defined, and any inconsistencies.

4. **Key Assertions**: Table contradictions and tensions, with evidence from each source.

5. **Gaps Identified**: Catalog missing content by type and impact.

6. **Recommendations**: Prioritized list of improvements.

## Output Quality

A good coherence report:

- **Synthesizes** rather than just lists (the forest, not just trees)
- **Provides evidence** for every claim (file:line references)
- **Prioritizes** issues by impact
- **Is actionable** — readers know what to do next

A poor coherence report:

- Mechanically lists issues without context
- Makes claims without evidence
- Treats all issues as equally important
- Leaves readers unsure how to proceed

## Handling Suppressions

When encountering inline `doc-auditor:ignore` comments:

- **DO** include suppressed content in your analysis (you need the full picture)
- **DO NOT** flag suppressed items as issues
- **DO** mention suppressed items in a separate "Suppressed Content" section

This provides visibility without creating noise.

## Practical Guidance

**Start with structure**: Understanding document types and organization provides context for everything else.

**Track terminology early**: As you read, note unfamiliar terms. Check if they get defined later.

**Build the link graph mentally**: Notice which docs reference which. This reveals orphans and hubs.

**Look for tensions**: When two docs discuss the same thing, ask if they agree.

**Note what's missing**: Expected sections that aren't there are as important as what IS there.

**Synthesize continuously**: Don't wait until the end. Form and refine your mental model as you read.
