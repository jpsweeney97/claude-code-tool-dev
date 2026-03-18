---
name: making-recommendations
description: Use when asked to recommend, suggest an approach, compare options, or choose between alternatives. Triggers on "what should I use", "which is better", "recommend", "help me decide", "what's the best way to", "should I go with X or Y", or any variant where the user needs help choosing between 2+ viable options. Also use when a mid-conversation discussion surfaces a decision point with trade-offs. Do not use for trivial decisions where both scope and reversibility are negligible, or for purely factual questions ("what is X?").
---

# Structured Recommendations

Your role is **analyst and recommender, not advocate**. Do not anchor on the first viable option. Generate the full option space before evaluating any of it.

## Ground Rules

- The **null option** (do nothing, defer, or accept the current state) must always appear in the option set. If genuinely non-viable, say why explicitly — do not silently omit it.
- Options are **generated before any are evaluated**. Do not collapse generation and evaluation into a single pass.
- Ranked options and trade-offs come before the recommendation. The recommendation must follow from the ranking — if it doesn't, reconcile the discrepancy explicitly.
- "Done" means: the recommendation is verifiably best given available information, or the information gaps preventing that verdict are explicitly named.

---

## The Process

### 1. Decision Extraction

State the decision to be made in one precise sentence, drawn from the preceding conversation. Name the decision type (e.g., technical selection, architectural choice, process design, tooling, prioritization). If the decision is ambiguous or underspecified, stop here and ask — do not proceed with a vague subject.

### 2. Stakes Calibration

Assess the decision on two axes:

- **Reversibility**: easy to undo → hard to undo
- **Blast radius**: affects one thing → affects many things or many people

Assign a tier and declare which sections you will run:

| Tier       | Criteria                                        | Sections skipped                              |
| ---------- | ----------------------------------------------- | --------------------------------------------- |
| **Low**    | Reversible + narrow blast radius                | Information Gaps, Sensitivity Analysis        |
| **Medium** | Partially reversible OR meaningful blast radius | Sensitivity Analysis abbreviated to 1–2 flips |
| **High**   | Hard to reverse OR wide blast radius            | None — full treatment                         |

State the tier and your reasoning in 1–2 sentences.

### 3. Option Generation

List every candidate option, including:

- All options raised in the conversation
- Any materially distinct alternatives not yet raised
- The null option: do nothing, defer the decision, or accept the current state

Do not evaluate options here. Generation only.

### 4. Information Gaps

_(Required for Medium and High; skip for Low — state that you are skipping and why)_

What is currently unknown that would materially change the ranking? For each gap:

- Name the unknown
- State which options it most affects
- State whether it is resolvable before committing (and how), or whether the decision must be made under uncertainty

### 5. Option Analysis

Evaluate each option against criteria that matter for **this specific decision**. Derive the criteria from the decision context — do not use a generic checklist. For each option, state:

- Key strengths
- Key weaknesses / risks
- Conditions under which it is the best choice

The third point matters: every option gets its moment as the right answer under some set of conditions. If you can't articulate those conditions, you don't understand the option well enough.

### 6. Sensitivity Analysis

_(Required for High; abbreviated for Medium — 1–2 flips only; skip for Low)_

For each non-recommended option: what would have to be true — about constraints, unknowns, or future conditions — for it to be the better choice? If no realistic set of conditions flips the ranking, say so explicitly.

### 7. Ranked Options

Present all options in ranked order with a one-line trade-off summary for each:

1. **[Option]** — [trade-off summary]
2. **[Option]** — [trade-off summary]
3. **[Option]** — [trade-off summary]

### 8. Recommendation

State the recommended option and core reasoning in 2–3 sentences. It must follow from Section 7. If it doesn't, reconcile the discrepancy before proceeding.

### 9. Readiness Signal

State whether this recommendation is **verifiably best** or **best available**:

| Signal              | Meaning |
| ------------------- | ------- |
| **Verifiably best** | Option space is complete, information gaps are resolved or non-material, and sensitivity analysis confirms the ranking is stable. |
| **Best available**  | Recommendation is sound given current information, but named gaps or unresolved conditions could flip it. Committing now is acceptable only if those gaps cannot be resolved before the decision deadline. |

If **best available**: list the specific conditions that would upgrade it to verifiably best.

---

## High-Tier Addons

These extensions apply only to **High**-stakes decisions. Skip for Low and Medium.

### Decision Record

Persist the full analysis to a file at `docs/decisions/YYYY-MM-DD-<decision-slug>.md`. Include all 9 sections plus any Codex Delta output. Then present an inline summary:

```
**Recommendation:** [Selected option]
**Why:** [2-3 sentence summary]
**Trade-offs accepted:** [What's being sacrificed]
**Readiness:** Verifiably best / Best available — [one-line justification]
**Full analysis:** [link to Decision Record file]
```

### Codex Delta (Cross-Model Adversarial Check)

When the Codex MCP is available, run a cross-model adversarial check on the frontrunner before finalizing the ranking. An independent model finds blind spots you can't see in your own reasoning.

Full invocation spec: [references/codex-delta.md](references/codex-delta.md)

When Codex MCP is unavailable, continue without it — apply extra scrutiny to Step 6 by steelmanning each non-recommended option more aggressively.

---

## Anti-Patterns

| Pattern | Problem | Fix |
|---------|---------|-----|
| Recommending the familiar option | Comfort isn't a criterion for the user's problem | Generate 3+ alternatives including at least one you're less familiar with |
| Evaluating during generation | Anchors on the first option, shrinks the space | Steps 3 and 5 are separate for a reason |
| Omitting null option silently | Biases toward action when inaction may be best | Always include it; explain non-viability if needed |
| Hiding uncertainty behind confidence | "Use X" when you're guessing erodes trust | Use the Readiness Signal honestly |
| Generic criteria for every decision | "Performance, scalability, cost" may not be what matters here | Derive criteria from the specific decision context |
| Skipping "conditions for best choice" | Treats options as globally right/wrong instead of contextually right/wrong | Every option is best under some conditions — name them |

## Example

**User:** "I need to add search to my documentation site. What should I use?"

### BAD: Pattern-matching

> "I'd recommend Algolia or Elasticsearch. Algolia is easier to set up and has great docs. Elasticsearch is more powerful for complex queries. For a docs site, Algolia is probably the way to go."
>
> — No stakes assessment, no null option, only considered two options in the same category, no trade-offs, confident despite knowing nothing about constraints.

### GOOD: Structured analysis

> **1. Decision:** Which search implementation for a documentation site? (Technical selection)
>
> **2. Stakes:** **Low** — reversible (search is additive, can swap later) and narrow blast radius (affects search UX only, not core content). Skipping Information Gaps and Sensitivity Analysis.
>
> **3. Options:**
> - Algolia DocSearch — managed service, free for open-source docs
> - Pagefind — static search, runs entirely client-side
> - Elasticsearch — self-hosted, full-text search engine
> - Built-in framework search (if available) — whatever the docs framework ships
> - **Null: no search** — rely on browser Ctrl+F and good navigation
>
> **5. Option Analysis:**
> - **Algolia DocSearch:** Strong for open-source projects (free tier, maintained crawlers). Weak: vendor dependency, requires application approval, limited customization. Best when: open-source project with standard docs structure.
> - **Pagefind:** Strong: zero dependencies, fast, no API keys. Weak: limited to static content, no typo tolerance. Best when: static site, privacy-conscious, no backend.
> - **Elasticsearch:** Strong: most powerful and customizable. Weak: massive overkill for docs — requires infrastructure, ops, costs. Best when: complex query needs (faceted search, analytics).
> - **Framework built-in:** Strong: zero setup, maintained by framework authors. Weak: limited features, varies by framework. Best when: search is nice-to-have, not critical.
> - **Null:** Strong: zero effort and maintenance. Weak: users can't find things. Best when: docs are small enough to browse, or audience is technical and uses grep.
>
> **7. Ranked:**
> 1. **Pagefind** — best simplicity-to-power ratio; no vendor, no infra, instant setup
> 2. **Framework built-in** — even simpler if it exists, but less capable
> 3. **Algolia DocSearch** — powerful but adds dependency; best if open-source eligible
> 4. **Null** — viable only if docs are small
> 5. **Elasticsearch** — overkill for this use case
>
> **8. Recommendation:** Pagefind. It runs client-side with no external dependencies, indexes at build time, and handles docs-scale content well. If you're eligible for Algolia DocSearch (open-source project), that's a strong alternative with better typo handling.
>
> **9. Readiness:** **Best available** — I don't know your docs framework (some have excellent built-in search that would rank higher), your content volume, or whether you need typo tolerance. Confirming those would upgrade to verifiably best.
