# Issue Categories Reference

This reference defines all 15 issue categories, subcategories, detection patterns, and severity guidelines for doc-auditor.

## Category Overview

| # | Category | Key | What It Catches |
|---|----------|-----|-----------------|
| 1 | Contradictions | `contradictions` | Same thing described differently |
| 2 | Dangling References | `dangling-references` | Links to nonexistent targets |
| 3 | Undefined Terms | `undefined-terms` | Jargon never explained |
| 4 | Orphaned Content | `orphaned-content` | Docs nothing links to |
| 5 | Scope Creep | `scope-creep` | Over-engineering, speculation |
| 6 | Coverage Gaps | `coverage-gaps` | Missing error handling, rationale |
| 7 | Stale Content | `stale-content` | Outdated information |
| 8 | Structural | `structural` | Formatting, heading issues |
| 9 | Ambiguity | `ambiguity` | Vague language, unclear referents |
| 10 | Code-Doc Drift | `code-doc-drift` | Docs don't match code |
| 11 | Security | `security` | Credentials, insecure patterns |
| 12 | Readability | `readability` | Complex sentences, jargon density |
| 13 | Duplication | `duplication` | Copy-pasted content |
| 14 | Navigation | `navigation` | Missing TOCs, poor discoverability |
| 15 | Template Compliance | `template-compliance` | Missing required sections |

---

## 1. Contradictions

**Definition:** Same concept described differently in different locations.

### Subcategories

| Subcategory | Description |
|-------------|-------------|
| `numeric-contradiction` | Numbers don't match ("10 states" vs "12 states") |
| `behavioral-contradiction` | Different behaviors described ("sync" vs "async") |
| `temporal-contradiction` | Conflicting sequences (Step 3 before Step 2) |
| `definitional-contradiction` | Same term defined differently |
| `constraint-contradiction` | Conflicting limits ("max 100" vs "max 500") |

### Detection Patterns

- Same noun/entity with different attributes across docs
- Numeric values for same metric that don't match
- Process descriptions with different step counts
- Terminology definitions that conflict

### Severity

| CRITICAL | Core architecture/design contradictions |
| HIGH | Behavioral contradictions affecting implementation |
| MEDIUM | Numeric mismatches in non-critical values |
| LOW | Minor wording differences with same meaning |

---

## 2. Dangling References

**Definition:** Links pointing to targets that don't exist.

### Subcategories

| Subcategory | Description |
|-------------|-------------|
| `broken-file-link` | Link to nonexistent file |
| `broken-anchor-link` | Link to nonexistent section |
| `broken-image` | Image reference that doesn't resolve |
| `implicit-reference` | "See the X document" where X not found |

### Detection Patterns

- Markdown links `[text](path)` where path doesn't exist
- Anchor links `#section` where heading not found
- Image references `![alt](path)` where path missing
- Phrases "see the", "refer to" followed by document names

### Severity

| CRITICAL | Broken link to critical docs (getting started, API) |
| HIGH | Broken link in main navigation or index |
| MEDIUM | Broken link in body content |
| LOW | Broken anchor within same document |

---

## 3. Undefined Terms

**Definition:** Domain terminology used without definition.

### Subcategories

| Subcategory | Description |
|-------------|-------------|
| `undefined-acronym` | Acronym never expanded |
| `domain-jargon` | Technical term assumed known |
| `project-specific` | Internal term unique to project |
| `ambiguous-pronoun` | "It", "this" with unclear referent |

### Detection Patterns

- Capitalized terms/acronyms with no definition
- Terms in backticks used repeatedly without explanation
- Technical terms not in common vocabulary
- First use without inline definition or glossary link

### Severity

| CRITICAL | Undefined term in onboarding docs |
| HIGH | Core concept undefined, >5 uses |
| MEDIUM | Domain term undefined, 2-5 uses |
| LOW | Acronym undefined but guessable |

---

## 4. Orphaned Content

**Definition:** Documents nothing links to.

### Subcategories

| Subcategory | Description |
|-------------|-------------|
| `unreachable-document` | No inbound links from reachable docs |
| `disconnected-section` | Section not in ToC/navigation |
| `orphaned-example` | Example file with no doc reference |

### Detection

Uses transitive closure from entry points. Documents not reachable are orphaned.

### Severity

| HIGH | Orphaned doc that appears authoritative |
| MEDIUM | Orphaned doc with recent modification |
| LOW | Orphaned doc marked as draft/WIP |

**Note:** Skipped if no entry points found.

---

## 5. Scope Creep

**Definition:** Documentation beyond what's implemented or needed.

### Subcategories

| Subcategory | Description |
|-------------|-------------|
| `speculative-feature` | Documents unimplemented functionality |
| `over-abstraction` | Excessive generalization |
| `premature-optimization` | Performance docs before profiling |
| `scope-beyond-implementation` | Docs describe more than code does |

### Detection Patterns

- Future tense ("will support", "planned")
- Abstract patterns with single implementation
- References to components that don't exist

### Severity

| HIGH | Documents nonexistent features as real |
| MEDIUM | Speculative mixed with factual |
| LOW | Clearly marked future sections |

---

## 6. Coverage Gaps

**Definition:** Expected content that's missing.

### Subcategories

| Subcategory | Description |
|-------------|-------------|
| `missing-error-handling` | No failure modes documented |
| `missing-edge-cases` | Happy path only |
| `missing-rationale` | Decision without "why" |
| `missing-examples` | Concept without illustration |
| `stub-section` | Empty or TODO section |
| `missing-prerequisites` | No setup/requirements listed |

### Detection Patterns

- API docs without error sections
- ADRs without Context/Decision
- Guides without prerequisites
- Sections with only "TODO", "TBD"

### Severity

| CRITICAL | Missing error handling for critical paths |
| HIGH | Stub in published documentation |
| MEDIUM | Missing examples for complex concepts |
| LOW | Missing rationale in internal docs |

---

## 7. Stale Content

**Definition:** Information now outdated.

### Subcategories

| Subcategory | Description |
|-------------|-------------|
| `outdated-version` | References old version |
| `deprecated-feature` | Documents removed functionality |
| `old-screenshot` | UI doesn't match current |
| `stale-timeline` | Past dates as future |
| `renamed-concept` | Old terminology still used |

### Detection Patterns

- Version numbers below current
- Dates beyond `staleness_days` in past
- References to deprecated APIs
- Renamed terminology

### Severity

| CRITICAL | Stale security/auth docs |
| HIGH | Outdated getting started guide |
| MEDIUM | Old version numbers in examples |
| LOW | Stale dates in changelog |

---

## 8. Structural

**Definition:** Formatting and organization issues.

### Subcategories

| Subcategory | Description |
|-------------|-------------|
| `heading-skip` | Heading levels skip (h1→h3) |
| `inconsistent-formatting` | Different styles for same element |
| `missing-title` | No h1 heading |
| `duplicate-heading` | Same heading text twice |
| `deep-nesting` | >4 heading levels |
| `inconsistent-list-style` | Mixed bullet styles |

### Detection Patterns

- Heading level jumps
- Documents without h1
- Duplicate headings
- Excessive nesting

### Severity

| HIGH | Missing document title |
| MEDIUM | Heading level skips |
| LOW | Style inconsistencies |

---

## 9. Ambiguity

**Definition:** Vague language leaving readers uncertain.

### Subcategories

| Subcategory | Description |
|-------------|-------------|
| `vague-quantity` | "several", "many", "few" |
| `hedge-words` | "should", "might", "probably" |
| `unclear-referent` | Ambiguous "this", "it" |
| `passive-voice-agent` | Unknown actor |
| `weasel-words` | Unattributed claims |

### Detection Patterns

- Words: "several", "many", "few", "various", "etc."
- Hedges: "should", "might", "may", "probably"
- "This" or "it" at sentence start without clear antecedent

### Severity

| HIGH | Ambiguity in requirements |
| MEDIUM | Hedge words in behavior descriptions |
| LOW | Vague language in asides |

---

## 10. Code-Doc Drift

**Definition:** Documentation doesn't match implementation.

### Subcategories

| Subcategory | Description |
|-------------|-------------|
| `api-mismatch` | Documented API differs from code |
| `example-broken` | Code example won't run |
| `signature-drift` | Function signature doesn't match |
| `return-type-mismatch` | Documented return differs |
| `config-mismatch` | Config options don't exist |

### Detection Patterns

- Cross-reference function names with source
- Parse code blocks, validate imports
- Compare documented params with signatures
- Validate CLI flags exist

### Severity

| CRITICAL | Core API documented incorrectly |
| HIGH | Function signature mismatch |
| MEDIUM | Example code won't compile |
| LOW | Minor parameter name differences |

**Note:** Requires `code_paths` configuration.

---

## 11. Security

**Definition:** Content leading to vulnerabilities.

### Subcategories

| Subcategory | Description |
|-------------|-------------|
| `credentials-exposed` | Secrets in examples |
| `insecure-pattern` | Unsafe practice shown as valid |
| `missing-auth-warning` | Auth requirements not mentioned |
| `http-not-https` | Non-secure URLs |
| `unsafe-defaults` | Insecure defaults documented |

### Detection Patterns

- Regex for API keys, tokens (`sk-`, `ghp_`, `password=`)
- Known insecure functions: `eval`, string SQL
- HTTP URLs in production examples
- Disabled security flags: `verify=False`

### Severity

| CRITICAL | Real credentials exposed |
| HIGH | Insecure pattern without warning |
| MEDIUM | HTTP URLs, missing auth docs |
| LOW | Disabled security in test examples |

---

## 12. Readability

**Definition:** Unnecessarily difficult to understand.

### Subcategories

| Subcategory | Description |
|-------------|-------------|
| `sentence-complexity` | 50+ word sentences |
| `jargon-density` | >5 technical terms per 100 words |
| `wall-of-text` | 10+ sentences without breaks |
| `inconsistent-terminology` | Same thing, different names |
| `passive-overuse` | Excessive passive voice |

### Detection Patterns

- Sentence length >40 words
- Technical terms per paragraph
- Text density (sentences per break)
- Term consistency tracking

### Severity

| HIGH | Jargon-heavy getting started |
| MEDIUM | Complex sentences in API reference |
| LOW | Passive voice in internal docs |

---

## 13. Duplication

**Definition:** Content repeated across documents.

### Subcategories

| Subcategory | Description |
|-------------|-------------|
| `copy-paste-content` | Identical paragraphs |
| `redundant-definitions` | Same term defined multiple times |
| `parallel-docs` | Multiple docs on same topic |
| `inline-duplication` | Content repeated in same doc |
| `version-forks` | Multiple versions without hierarchy |

### Detection Patterns

- Content similarity (fuzzy matching)
- Term definitions across docs
- Files with similar names/paths
- Repeated blocks within docs

### Severity

| HIGH | Identical content in 3+ locations |
| MEDIUM | Same term defined differently in multiple places |
| LOW | Minor duplication within single doc |

---

## 14. Navigation

**Definition:** Hard to find or navigate documentation.

### Subcategories

| Subcategory | Description |
|-------------|-------------|
| `missing-toc` | Long doc without table of contents |
| `missing-index` | No main landing page |
| `deep-nesting` | Content 4+ clicks from entry |
| `unclear-hierarchy` | Organization doesn't reflect importance |
| `missing-breadcrumbs` | No location context |
| `dead-end-docs` | No outbound links |

### Detection Patterns

- Document length vs ToC presence
- Index files in doc directories
- Click depth from entry points
- Outbound links per document

### Severity

| HIGH | No index in docs root |
| MEDIUM | Long doc without ToC |
| LOW | Missing "See also" links |

---

## 15. Template Compliance

**Definition:** Documents don't follow canonical structure.

### Subcategories

| Subcategory | Description |
|-------------|-------------|
| `missing-required-section` | Required section absent |
| `wrong-section-order` | Non-standard section order |
| `invalid-section-content` | Wrong content for section |
| `missing-type-marker` | Can't determine doc type |
| `incomplete-template` | Started but not finished |
| `non-standard-structure` | Custom sections where standard expected |

### Detection Patterns

- Infer doc type from filename/content
- Load template for detected type
- Check required sections present
- Validate section order

### Severity

| CRITICAL | Missing required section in README/API |
| HIGH | Wrong section order |
| MEDIUM | Missing recommended sections |
| LOW | Non-standard section names |

---

## Cross-Category Rules

### Overlap Precedence

When issue fits multiple categories, use:

1. **Security** → `security`
2. **Code mismatch** → `code-doc-drift`
3. **Factual conflict** → `contradictions`
4. **Template wrong** → `template-compliance`
5. **Missing content** → `coverage-gaps`
6. **Outdated** → `stale-content`
7. **Repeated** → `duplication`
8. **Hard to find** → `navigation`
9. **Hard to read** → `readability`
10. **Unclear** → `ambiguity`

### Confidence Assignment

| HIGH | Exact pattern match, no interpretation |
| MEDIUM | Strong indicators, some inference |
| LOW | Possible issue, needs verification |

When uncertain, prefer lower confidence.

### Naming Convention

All identifiers use **kebab-case**:
- Categories: `contradictions`, `code-doc-drift`, `template-compliance`
- Subcategories: `numeric-contradiction`, `api-mismatch`, `missing-required-section`
