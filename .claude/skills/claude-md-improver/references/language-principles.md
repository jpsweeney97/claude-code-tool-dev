# Language Principles for CLAUDE.md

The audience for CLAUDE.md is Claude. Optimize language accordingly.

## Principles

### 1. Economy (Signal-to-Noise)

Omit needless words. If a word does not advance meaning, remove it.

| Before | After |
|--------|-------|
| "It is important to note that tests should be run" | "Run tests" |
| "Please make sure to always use" | "Use" |
| "completely finished" | "finished" |

Delete: "please," "actually," "it is important to," "make sure to," "note that"

### 2. Affirmative Direction

State what *is*, not what *is not*. Use active voice.

| Before | After |
|--------|-------|
| "Do not fail to include tests" | "Include tests" |
| "Errors should be logged by the handler" | "The handler logs errors" |
| "It is not uncommon for builds to fail" | "Builds often fail" |

**Exception:** Prohibitions for dangerous operations are clearest as negatives. "NEVER run `rm -rf`" is more memorable than its affirmative inverse.

### 3. Concrete Specificity

Ambiguity is failure. Prefer specific nouns and verbs to abstract generalizations.

| Before | After |
|--------|-------|
| "Update the config file" | "Update `.claude/settings.json`" |
| "Run the tests" | "Run `uv run pytest tests/`" |
| "It processes the data" | "The parser extracts timestamps from log lines" |

Replace vague pronouns ("it," "this," "that") with their antecedents.

### 4. Logical Proximity

Physical distance on the page reflects logical distance in thought.

| Before | After |
|--------|-------|
| "Run tests. (See Environment section for prerequisites.)" | Prerequisites in Environment section, then "Run tests" |
| "Y applies. (When X is true.)" | "When X is true, Y applies." |

Keep modifiers next to words they modify. Keep conditions next to their consequences. Group related instructions with bullets or tables.

### 5. Contextual Priming

Structure for rapid parsing.

- Place reference data *before* instructions that use it
- Start sections with topic sentences
- Front-load important information
- Use headers to signal scope boundaries

| Before | After |
|--------|-------|
| "Use these commands: [...]. This section covers testing." | "## Testing\n\nCommands: [...]" |
| "The API returns errors in a specific format. When handling errors, parse the `code` field." | "Error format: `{code, message}`. Parse the `code` field." |

### 6. Pattern Consistency

Use parallel structure across similar sections.

| Before | After |
|--------|-------|
| "Run tests", "You should lint the code", "Formatting is done with ruff" | "Run tests", "Lint code", "Format with ruff" |
| Mixed bullet styles and numbering | Consistent format throughout |

If one rule is imperative ("Run tests"), peer rules should be imperative. If one table uses "Avoid/Prefer" headers, similar tables should match.

## Grading Scale

Language quality is scored separately from content quality.

| Grade | Criteria |
|-------|----------|
| A | All 6 principles followed consistently |
| B | Minor violations in 1-2 principles |
| C | Noticeable issues in 2-3 principles |
| D | Significant issues in 4+ principles |
| F | Pervasive language problems throughout |

Report format: `Content: 78/100 (B), Language: B+`

Specific violations go in the Issues section with principle name and location:
- "Economy: filler phrases in How to Work section ('it is important to note')"
- "Specificity: vague 'the config file' reference at line 45"

## Common Violations

| Violation | Principle | Fix |
|-----------|-----------|-----|
| "Please remember to..." | Economy | Delete filler |
| "It should not be forgotten that..." | Economy + Affirmative | State directly |
| Passive voice throughout | Affirmative | Rewrite in active voice |
| "this," "it" without antecedent | Specificity | Name the referent |
| Condition buried after instruction | Proximity | Move condition first |
| Mixed imperative/declarative style | Consistency | Pick one, apply throughout |
| Important info at end of paragraph | Priming | Front-load |

## Integration with Content Rubric

Language quality is orthogonal to content quality:

- **Content** = "Does this include the right information?"
- **Language** = "Is that information well-expressed?"

A file can score high on content (all sections present) but low on language (poorly expressed). Both dimensions appear in the quality report.

During Phase 5 (Targeted Updates), apply these principles when drafting improvements. Show before/after in diffs to demonstrate the transformation.
