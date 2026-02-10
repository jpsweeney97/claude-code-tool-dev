---
name: llm-reference
description: Transform any content into an LLM-optimized reference document. Converts human-oriented prose, guides, tutorials, meeting notes, or unstructured braindumps into structured documents optimized for LLM consumption, preserving intentional nuance while removing human-reader scaffolding. Use when user says "make this LLM-readable", "optimize for LLM", "transform this into a reference", "rewrite for LLM consumption", or "create an LLM reference from this".
---

# LLM Reference

Transform any content into a structured reference document optimized for LLM consumption.

The hard part is not knowing what to change — it's knowing what to leave alone.

## Before You Start

Read [transformation-principles.md](transformation-principles.md) before performing any transformation. It contains the authoritative reference for why human documents and LLM documents differ, and what drives each transformation decision.

## The Core Discipline

Claude's default failure mode when transforming documents is **over-transformation**: flattening nuance, replacing intentional phrasing with generic alternatives, breaking purposeful structure, and converting flexible guidance into rigid rules.

Every transformation decision is a judgment call between removing noise and destroying signal. When uncertain, preserve.

### Identifying Load-Bearing Content

Before removing or rewriting anything, determine whether it's scaffolding (removable) or signal (preserve).

**A hedge word is signal when:**

- Removing it changes the truth value ("usually" — because exceptions exist)
- The author had a simpler phrasing available and chose this one instead
- Other content depends on the qualification

**A hedge word is scaffolding when:**

- It softens without changing meaning ("I would suggest that perhaps...")
- It's defensive rather than precise ("It might be worth considering...")
- Removing it makes the statement more accurate, not less

**Structure is signal when:**

- The ordering reflects dependencies, priority, or progression
- Groupings create meaningful categories
- The hierarchy encodes relationships between ideas

**Structure is scaffolding when:**

- It follows a generic template without adapting to the content
- Reordering wouldn't change comprehension
- Groupings are arbitrary or cosmetic

**Phrasing is signal when:**

- A simpler synonym would lose a distinction the author was drawing
- The word choice carries domain-specific meaning
- The tone is calibrated (e.g., deliberately casual to signal flexibility)

**Phrasing is scaffolding when:**

- It's verbose where concise would be equivalent
- It's generic where the author likely didn't choose deliberately
- It exists for human engagement rather than information content

## Workflow

### Step 1: Acquire the Source

Accept input in any form:

| Input | Action |
|-------|--------|
| File path | Read the file |
| URL | Fetch and extract content |
| Pasted content | Work with what's provided |
| Topic (no source) | Research via web search for current information; use training knowledge for established domains. Note when knowledge may be stale. Synthesize into a draft, then apply the same transformation workflow to your own draft. |

If the source is unstructured (meeting notes, braindumps, scattered bullets), the transformation includes an organization phase: group related content, establish a logical sequence, and surface implicit structure before optimizing.

### Step 2: Analyze and Checkpoint

Before writing anything, present an analysis to the user:

1. **Content type:** What kind of source this is (guide, tutorial, notes, reference, mixed)
2. **Preserve:** Specific elements to keep and why — name the intentional phrasing, the deliberate structure, the calibrated flexibility. Be concrete: quote the specific words or describe the specific structural choice.
3. **Transform:** What human-reader scaffolding to remove or restructure — motivational framing, authority citations, persuasion, redundancy. Again, be specific.
4. **Organize** (if needed): How unstructured content will be grouped and sequenced
5. **Target context** (optional): Ask if the user has a specific deployment context (system prompt, RAG, skill file, general-purpose)

Wait for confirmation before proceeding.

**For long documents:** Offer iterative mode — transform section by section with checkpoints after each. Let the user decide what counts as "long enough" to warrant this; don't impose a threshold.

### Step 3: Transform

Apply transformation operations selectively. Each operation is a tool, not a rule — use it when it serves the content.

| Operation | When to apply | When to skip |
|-----------|---------------|--------------|
| Advisory voice → imperative | Content is instructional and the guidance is unconditional | Guidance is genuinely conditional, or the source is descriptive/explanatory |
| Prose logic → decision tables | Content contains conditional rules readers need to look up | Logic is sequential narrative that reads naturally as prose |
| Linear structure → lookup sections | Readers will search for specific answers | Content is a procedure where order matters |
| Illustrative examples → input/output pairs | Source shows "bad → good" transformations | Examples are case studies or narratives that lose meaning when compressed |
| Multiple representations → single statement | Redundancy exists for human retention, not for distinct purposes | Each representation adds distinct information |
| Remove motivational scaffolding | Content exists to persuade human readers to keep reading | Framing provides necessary context for understanding what follows |

### Step 4: Verify

After transformation, check:

- [ ] **No information loss** — all content from the source that would be valuable to an LLM consumer is present (actionable instructions, context, rationale)
- [ ] **No over-rigidification** — flexible guidance in the source remains flexible in the output. "Usually" didn't become "always." "Consider" didn't become "must."
- [ ] **No nuance loss** — hedge words identified as signal in Step 2 survived the transformation. Intentional phrasing wasn't replaced with generic equivalents.
- [ ] **No invented content** — nothing added that wasn't in the source or directly implied by it
- [ ] **Structurally parseable** — tables, lists, and headers create clear boundaries for LLM consumption
- [ ] **Self-contained sections** — each section is comprehensible without requiring cross-references to other sections

## Anti-Patterns

### Uniform Transformation

Applying the same operations to all content regardless of type. A tutorial, an API reference, and meeting notes each need different treatment. A tutorial's sequential structure is intentional; flattening it into lookup sections destroys the learning progression.

### Synonym Smoothing

Replacing the author's specific word choices with "cleaner" generic alternatives. "Credible, specific, low-drama" becoming "professional and concise" loses the author's precise characterization. If a phrase is unusual, check whether it's unusual *on purpose* before replacing it.

### Table Everything

Converting all content into tables. Tables work for conditional logic and parameter lookups. They don't work for procedures, narratives, or content where relationships between ideas matter more than individual items. A paragraph that builds an argument across sentences shouldn't become a table of disconnected rows.

### Strip All Hedges

Treating every qualifier as fluff. "In most cases" became "Always." "Consider" became "Must." "Often effective" became "Effective." The source author used hedges because the guidance IS conditional — removing them creates false absolutes.

### Template Imposition

Forcing content into a familiar structure (Overview → Rules → Examples → Anti-patterns) regardless of whether that structure fits. Let the content's natural organization drive the output structure. A reference for cooking techniques doesn't need the same sections as a reference for API error codes.

## Examples

### Preservation in Practice

**Source text:**
> Cover letters still matter most when they function as a writing sample + context layer (not a resume rehash). Harvard's career guidance frames it explicitly as part of the screening process and a writing-skill signal.

**Over-transformed (bad):**
> A cover letter is a writing sample. It must not repeat the resume.

**Why it's bad:** "still matter most when" was load-bearing — it scoped when cover letters are valuable. The transformation collapsed a conditional statement into an absolute. The Harvard citation was correctly removed (authority scaffolding), but the qualifying condition was removed with it.

**Correctly transformed:**
> A cover letter is a writing sample, not a resume rehash. It adds the most value when the role treats it as part of the screening process or as a writing-skill signal.

### Conditional Logic Extraction

**Source text:**
> "Tailoring" isn't flattery. It's showing you understand the role's priorities, the team's environment (scale, tooling, customer type, risk), and what success likely means in the first 3-6 months.

**Correctly transformed:**
> Tailoring means demonstrating understanding of:
> - The role's priorities
> - The team's environment: scale, tooling, customer type, risk profile
> - What success looks like in the first 3-6 months
>
> Generic mission praise is not tailoring.

**Why:** The prose structure was scaffolding — the "isn't... It's..." rhetorical device is for human engagement. But "3-6 months" and the specific environment dimensions were signal. The transformation extracted the list without losing the specifics.

### When to Keep Prose

**Source text:**
> In 2025, recruiters increasingly complain that AI-heavy materials feel polished but empty — "grammatically correct and emotionally vacant." The differentiator is specificity + honest voice + accurate detail.

**Correctly transformed:**
> AI-generated content fails when it's polished but generic. The differentiator is specificity, honest voice, and accurate detail — not surface-level fluency.

**Why:** The year reference and recruiter attribution were scaffolding. But "grammatically correct and emotionally vacant" was a precise characterization worth preserving in spirit (captured as "polished but generic"). The core insight was kept; the human-reader framing was removed.
