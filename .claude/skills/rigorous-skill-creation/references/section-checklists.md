# Section Checklists

Consolidated validation checklists for each of the 11 skill sections plus frontmatter and session state.

## Frontmatter Checklist

### Required Fields

- [MUST] `name` exists, is kebab-case, <=64 chars
- [MUST] `description` exists, <=1024 chars, single line

### Tool Declaration

- [MUST] `allowed-tools` lists all tools actually used by skill (if skill uses tools)
- [MUST] No placeholder values like `<tool1>` or `<tool2>` in final output
- [SHOULD] `allowed-tools` omitted entirely if skill uses no tools (not empty array)

### Invocation Control

- [SHOULD] `user-invocable` explicitly set if skill should appear in slash menu
- [SHOULD] `user-invocable: false` for skills only invoked programmatically

### Optional Metadata

- [SHOULD] `license` declared for redistributable skills
- [SHOULD] `metadata.version` follows semver (e.g., "1.0.0")

### Anti-patterns

- [SEMANTIC] `allowed-tools: []` (empty array) when skill clearly uses tools in Procedure
- [SEMANTIC] Placeholder values in any field (`<skill-name>`, `<brief description>`)
- [SEMANTIC] `description` that doesn't explain when to use the skill
- [SEMANTIC] Mismatch between `allowed-tools` and tools referenced in Procedure

## Triggers Checklist

### [MUST] - Structural Requirements

- [ ] Section exists with `## Triggers` heading
- [ ] Contains >=3 trigger phrases
- [ ] Each phrase <=50 characters
- [ ] No duplicate phrases
- [ ] No overlap with "When to use" content (triggers are literal phrases, not conditions)

### [SHOULD] - Quality Requirements

- [ ] Includes both verb phrases ("create a", "build a") and noun phrases ("new skill", "skill for")
- [ ] Covers common synonyms (create/build/make, skill/workflow/automation)
- [ ] Avoids overly generic triggers that match unrelated intents
- [ ] Phrases represent how users actually speak

### [SEMANTIC] - Anti-Pattern Detection

| Pattern | Issue |
|---------|-------|
| Trigger >30 chars | Too specific - won't match variations |
| Single-word trigger | Too broad - false positives |
| Trigger matches common Claude commands | Conflict with built-in functionality |
| All triggers start same way | Limited discoverability |

## When to Use Checklist

### Structural
- [MUST] Section exists with clear heading or equivalent
- [MUST] Contains activation triggers (when this skill applies)

### Semantic
- [MUST] Primary goal stated in 1-2 sentences
- [MUST] Triggers are specific enough to avoid over-broad activation
- [SHOULD] Includes example scenarios or user phrases that trigger activation

### Anti-patterns
- [SEMANTIC] Vague triggers: "when you need to do X" without specifics
- [SEMANTIC] Overlapping scope with other skills without differentiation

## When NOT to Use Checklist

### Structural
- [MUST] Section exists with clear heading or equivalent
- [MUST] Contains at least 3 explicit non-goals or out-of-scope items

### Semantic
- [MUST] Non-goals prevent common scope failures
- [MUST] Includes STOP conditions (explicit triggers to halt and route elsewhere)
- [SHOULD] Default non-goals stated if applicable:
  - No dependency upgrades (unless skill's purpose)
  - No public API changes (unless skill's purpose)
  - No destructive actions (unless skill's purpose)
  - No schema/data migrations (unless skill's purpose)

### Anti-patterns
- [SEMANTIC] Non-goals are just routing suggestions without STOP language
- [SEMANTIC] Missing boundaries that would surprise reviewers

## Inputs Checklist

### Structural
- [MUST] Required inputs sub-section exists
- [MUST] Optional inputs sub-section exists (or explicit "None")
- [MUST] Constraints/Assumptions sub-section exists

### Semantic
- [MUST] At least one required input defined
- [MUST] Each input is specific and actionable (not "the inputs needed")
- [MUST] Constraints declare non-universal assumptions:
  - Tools (specific CLIs, versions)
  - Network (API access, downloads)
  - Permissions (file write, env vars, secrets)
  - Repo layout (specific paths, conventions)
- [MUST] Fallback provided when assumptions not met (or STOP/ask)

### Anti-patterns
- [SEMANTIC] Placeholder language: "whatever is needed", "appropriate inputs"
- [SEMANTIC] Implicit tool assumptions without declaration
- [SEMANTIC] No fallback for network-dependent operations

## Outputs Checklist

### Structural
- [MUST] Artifacts sub-section exists
- [MUST] Definition of Done sub-section exists

### Semantic
- [MUST] At least one artifact defined (files, patches, reports, commands)
- [MUST] At least one objective DoD check that is:
  - Artifact existence/shape, OR
  - Deterministic query/invariant, OR
  - Executable check with expected output, OR
  - Deterministic logical condition
- [MUST] DoD checks are verifiable without "reading the agent's mind"
- [SHOULD] Calibration: outputs distinguish Verified/Inferred/Assumed claims

### Anti-patterns (FAIL-level)
- [SEMANTIC] "Verify it works" - not objective
- [SEMANTIC] "Ensure quality" - not measurable
- [SEMANTIC] "Make sure tests pass" without specifying which tests
- [SEMANTIC] "Check for errors" without specifying where/how

## Procedure Checklist

### Structural
- [MUST] Steps are numbered (not bullets or prose)
- [MUST] Steps are executable actions (not generic advice)

### Semantic
- [MUST] At least one explicit STOP/ask step for missing inputs
- [MUST] At least one explicit STOP/ask step for ambiguity (Medium+ risk)
- [HIGH-MUST] Ask-first gate before any breaking/destructive/irreversible action
- [SHOULD] Order follows: inspect -> decide -> act -> verify
- [SHOULD] Prefers smallest correct change

### Command Mention Rule
- [MUST] Every command specifies expected result shape
- [MUST] Every command specifies preconditions (if non-obvious)
- [MUST] Every command has fallback for when it cannot run

### Mutating Action Gating
- [HIGH-MUST] Every mutating step has explicit ask-first gate
- [HIGH-MUST] Each ask-first gate names the specific risk
- [HIGH-MUST] Safe alternative offered (dry-run, read-only, or skip)
- [MEDIUM-MUST] Mutating steps are bounded by scope fence
- [MEDIUM-SHOULD] Rollback/undo steps provided for mutating actions

### Anti-patterns
- [SEMANTIC] "Use judgment" without observable decision criteria
- [SEMANTIC] Commands without expected outputs
- [SEMANTIC] Mutating steps without ask-first gates (High risk)

## Decision Points Checklist

### Structural
- [MUST] At least 2 explicit decision points exist
- [MUST] Each uses "If... then... otherwise..." structure (or equivalent)

### Semantic
- [MUST] Each decision point names an observable trigger:
  - File/path exists or doesn't
  - Command output matches pattern
  - Test passes/fails
  - Grep finds/doesn't find pattern
  - Config contains/missing key
- [MUST] Triggers are not subjective ("if it seems", "when appropriate")
- [SHOULD] Covers common operational branches:
  - Tests exist vs not
  - Network available vs restricted
  - Breaking change allowed vs prohibited
  - Output format preference

### Exception Handling
- [MUST] If fewer than 2 decision points, justification is provided
- [MUST] Even with exception, at least one STOP/ask condition exists

### Anti-patterns
- [SEMANTIC] "Use judgment" as the decision criterion
- [SEMANTIC] Subjective triggers: "if it seems risky", "when appropriate"

## Verification Checklist

### Structural
- [MUST] Quick check sub-section exists
- [SHOULD] Deep check sub-section exists (required for High risk)

### Semantic
- [MUST] Quick check is concrete and executable/observable
- [MUST] Quick check measures the primary success property (not just proxy)
- [MUST] Quick check specifies expected result shape
- [MUST] Failure interpretation: what to do if check fails
- [HIGH-MUST] At least two verification modes (quick + deep)
- [SHOULD] No-network fallback for verification when feasible

### Calibration
- [MUST] Skill instructs "Not run (reason)" reporting for skipped checks
- [SHOULD] Verification ladder (quick -> narrow -> broad) for Medium+ risk

### Anti-patterns
- [SEMANTIC] "Tests pass" without specifying which tests or showing output
- [SEMANTIC] Proxy-only verification (compiles but behavior unchecked)
- [SEMANTIC] No failure handling ("if check fails, continue anyway")

### Command Robustness
- [MUST] Use literal paths in verification commands, not glob patterns
  - Bad: `test -f docs/plans/*-review.md` (glob may match 0, 1, or N files)
  - Good: `test -f "$REPORT_PATH"` with note to substitute actual path
- [MUST] Quote variables in shell commands to handle spaces
  - Bad: `grep -q "pattern" $FILE`
  - Good: `grep -q "pattern" "$FILE"`
- [SHOULD] Verification commands should be deterministic (same input = same result)
- [SHOULD] Deep check criteria must be objectively verifiable (not "looks correct")

## Troubleshooting Checklist

### Structural
- [MUST] At least one failure mode documented
- [MUST] Each failure mode has: symptoms, likely causes, next steps

### Semantic
- [MUST] Symptoms describe what user observes (error message, behavior)
- [MUST] Causes are specific (not "something went wrong")
- [MUST] Next steps are actionable (specific commands, inspections)
- [SHOULD] At least one anti-pattern phrased as temptation to avoid
  (e.g., "Don't just disable the test")
- [HIGH-MUST] Includes rollback/escape hatch guidance for partial success

### Anti-patterns
- [SEMANTIC] Generic causes: "configuration issue", "environment problem"
- [SEMANTIC] Vague next steps: "investigate further", "check the logs"

## Anti-Patterns Checklist

### [MUST] - Structural Requirements

- [ ] Section exists with `## Anti-Patterns` heading
- [ ] Contains >=1 anti-pattern entry
- [ ] Each entry has pattern description
- [ ] Each entry has consequence (why it's problematic)
- [ ] Not duplicates of "When NOT to use" entries

### [SHOULD] - Quality Requirements

- [ ] Minimum entries matches risk tier: Low >=1, Medium >=2, High >=2
- [ ] Each explains *why* the pattern is problematic (not just "don't do this")
- [ ] Entries are distinct from "When NOT to use" (anti-patterns = bad practices during use; when-not-to-use = wrong context for skill)
- [ ] Patterns are specific enough to recognize
- [ ] Consequences describe observable negative outcomes

### [SEMANTIC] - Anti-Pattern Detection

| Pattern | Issue |
|---------|-------|
| Entry without consequence | No motivation to avoid |
| Vague pattern ("don't do bad things") | Not actionable |
| Duplicates When NOT to use | Wrong section |
| Only 1 entry for High risk skill | Insufficient coverage |

## Extension Points Checklist

### [MUST] - Structural Requirements

- [ ] Section exists with `## Extension Points` heading
- [ ] Contains >=2 extension point entries
- [ ] Each entry is actionable (verb + object)
- [ ] No vague entries ("improve", "enhance" without specifics)

### [SHOULD] - Quality Requirements

- [ ] Entries span different extension types (scope expansion, integration, optimization)
- [ ] Each entry is independently actionable
- [ ] Entries don't require major redesign (natural evolution paths)
- [ ] At least one entry addresses integration with other tools/skills
- [ ] Entries are forward-looking but realistic

### [SEMANTIC] - Anti-Pattern Detection

| Pattern | Issue |
|---------|-------|
| Entry starts with "improve", "enhance", "optimize" without specifics | Not actionable direction |
| Entry requires fundamental redesign | Not an extension, it's a rewrite |
| All entries are scope expansion | Missing integration/optimization paths |
| Entry duplicates existing functionality | Not actually an extension |

## Session State Checklist

### [MUST] - Structural Requirements

- [ ] Section exists with `## Session State` heading (during creation)
- [ ] Contains `phase` field with value 0-4
- [ ] Contains `progress` field in format "N/11" (body sections completed, not phases)
- [ ] Removed after Phase 4 approval (not present in final skill)

### [SHOULD] - Quality Requirements

- [ ] `dialogue_context` captures user preferences discovered during session
- [ ] `next_steps` is specific (not just "continue" or "proceed")
- [ ] Updated after each section approval in Phase 3
- [ ] `last_action` describes what happened before any interruption

### [SEMANTIC] - Anti-Pattern Detection

| Pattern | Issue |
|---------|-------|
| `next_steps` contains only "continue" or "proceed" | Not specific enough for recovery |
| `progress` doesn't match actual sections present | State out of sync |
| `phase` value doesn't match progress | Inconsistent state |
| Session State present in "final" skill | Not cleaned up after approval |

### Lifecycle

| Phase | Session State |
|-------|---------------|
| Phase 0 (Triage) | Not yet created |
| Phase 1 (Analysis) | Created at end with initial state |
| Phase 2 (Checkpoint) | Updated with validated decisions |
| Phase 3 (Generation) | Updated after each section approval |
| Phase 4 (Panel) | Present during review |
| After approval | **Removed** |

## Frontmatter Decisions Checklist

### [MUST] - Structural Requirements

- [ ] `metadata.decisions` field present and parses as valid YAML
- [ ] Contains `requirements` object with at least one `explicit` entry
- [ ] Contains `approach.chosen` describing selected approach
- [ ] Contains `risk_tier` with value (Low/Medium/High)

### [SHOULD] - Quality Requirements

- [ ] `requirements.implicit` non-empty (user expectations not stated)
- [ ] `requirements.discovered` non-empty for non-trivial skills
- [ ] `approach.alternatives` includes >=2 rejected approaches with rationale
- [ ] `risk_tier` includes rationale (not just "Medium")
- [ ] `key_tradeoffs` documents significant trade-offs made
- [ ] `methodology_insights` traces lens findings to sections
- [ ] `category` matches one of 21 defined categories

### [SEMANTIC] - Anti-Pattern Detection

| Pattern | Issue |
|---------|-------|
| Empty `alternatives` | Alternatives weren't explored |
| `risk_tier` without rationale | Classification not justified |
| `methodology_insights` with <5 entries | Methodology likely superficial |
| All insights say "no findings" | Analysis wasn't rigorous |
| `discovered` empty for complex skill | Analysis incomplete |
