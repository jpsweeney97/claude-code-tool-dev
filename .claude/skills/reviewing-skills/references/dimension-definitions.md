# Dimension Definitions

Detailed guidance for checking each dimension. Use this reference when exploring dimensions during the review loop.

## Table of Contents

- [D1: Trigger Clarity (P0)](#d1-trigger-clarity-p0)
- [D2: Process Completeness (P0)](#d2-process-completeness-p0)
- [D3: Structural Conformance (P0)](#d3-structural-conformance-p0)
- [D4: Compliance Strength (P1)](#d4-compliance-strength-p1)
- [D5: Precision (P1)](#d5-precision-p1)
- [D6: Actionability (P1)](#d6-actionability-p1)
- [D7: Internal Consistency (P1)](#d7-internal-consistency-p1)
- [D8: Scope Boundaries (P1)](#d8-scope-boundaries-p1)
- [D9: Reference Validity (P2)](#d9-reference-validity-p2)
- [D10: Edge Cases (P2)](#d10-edge-cases-p2)
- [D11: Feasibility (P2)](#d11-feasibility-p2)
- [D12: Testability (P2)](#d12-testability-p2)
- [D13: Integration Clarity (P1, Conditional)](#d13-integration-clarity-p1-conditional)

---

## D1: Trigger Clarity (P0)

**What it catches:** Vague or overlapping descriptions that cause misfires or missed activations.

**How to check:**

1. Read the `description` field — does it contain ONLY trigger conditions?
2. Check for workflow summaries (BAD: "performs X by doing Y")
3. Check for outcome descriptions (BAD: "helps with X", "improves Y")
4. Compare against other skills — any overlap that could cause conflicts?
5. Are trigger conditions specific enough to be unambiguous?

**Red flags:**

- Verbs describing what skill does (not when to activate)
- "Helps", "improves", "manages", "handles" without trigger context
- Vague contexts: "when needed", "as appropriate", "when relevant"
- Descriptions over 200 characters (likely summarizing workflow)
- Overlap with other skill descriptions in same codebase

**Good patterns:**

- "Use when..." followed by specific condition
- "Use after..." followed by specific event
- "Use before..." followed by specific action
- Error messages or symptoms as triggers
- Explicit user phrases that invoke the skill

**Pass criteria:**

- Description contains only trigger conditions
- No workflow or outcome language
- No overlap with other skills
- Triggers are specific enough that you can tell if they apply

**Example findings:**

| Finding | Priority | Proposed Fix |
|---------|----------|--------------|
| Description says "manages API errors by retrying" | P0 | Rewrite to: "Use when API calls fail with retriable errors (429, 503)" |
| Description overlaps with `handling-errors` skill | P0 | Differentiate: this skill for API errors, that skill for application errors |

---

## D2: Process Completeness (P0)

**What it catches:** Missing steps, undefined decision points, unclear exit criteria.

**How to check:**

1. Trace through the process — can you follow it without guessing?
2. For each decision point — is the condition clear? Is the action specified? Is the alternative defined?
3. Is there an explicit exit/completion criteria?
4. Are there unstated prerequisites?
5. What happens if a step fails?

**Red flags:**

- "Handle appropriately" without specifying how
- Decision points with only one branch defined
- No clear "done" state
- Assumed knowledge not stated
- "Continue until complete" without defining complete
- Steps that reference external knowledge without links

**Good patterns:**

- Condition → Action → Alternative for every decision
- Explicit exit criteria with verification method
- Prerequisites stated at the start
- Failure handling for critical steps
- Numbered steps for sequential processes

**Pass criteria:**

- Every step is actionable without guessing
- Every decision point has condition → action → alternative
- Exit criteria explicit and verifiable
- Prerequisites stated
- Failure modes addressed for P0 steps

**Example findings:**

| Finding | Priority | Proposed Fix |
|---------|----------|--------------|
| "Handle the error appropriately" — how? | P0 | Define specific error handling: retry, escalate, or abort with message |
| Decision point "if complex" has no threshold | P0 | Define: "if >3 files affected" or "if requires architectural change" |
| No exit criteria — when is process done? | P0 | Add: "Done when all tests pass and changes committed" |

---

## D3: Structural Conformance (P0)

**What it catches:** Missing required sections, wrong frontmatter, exceeds size limits.

**How to check:**

1. **Required sections present:**
   - [ ] Overview
   - [ ] Triggers OR When to Use (at least one)
   - [ ] Process
   - [ ] Examples (with BAD/GOOD)
   - [ ] Anti-Patterns
   - [ ] Troubleshooting
   - [ ] Decision Points

2. **Frontmatter valid:**
   - [ ] `name`: kebab-case, ≤64 chars, gerund form
   - [ ] `description`: ≤1024 chars, trigger conditions only

3. **Size limits:**
   - [ ] Body under 500 lines
   - [ ] References one level deep from SKILL.md

4. **Structure:**
   - [ ] Progressive disclosure (overview → details)
   - [ ] Consistent heading levels

**Red flags:**

- Missing required sections
- Name not gerund form ("code-review" vs "reviewing-code")
- Description over 1024 characters
- Body over 500 lines without reference splitting
- Nested references (reference files linking to other reference files)
- Inconsistent heading hierarchy

**Pass criteria:**

- All required sections present
- Frontmatter valid
- Size within limits
- References one level deep

**Example findings:**

| Finding | Priority | Proposed Fix |
|---------|----------|--------------|
| Missing "When NOT to Use" section | P0 | Add section listing exclusions |
| Name is "skill-review" (noun) | P0 | Rename to "reviewing-skills" (gerund) |
| Body is 650 lines | P1 | Split detailed content to references/ |

---

## D4: Compliance Strength (P1)

**What it catches:** Weak language, missing rationalization counters, no red flags.

**How to check:**

1. **Language strength:**
   - Are critical requirements stated with authority? ("YOU MUST", "Never", "Always")
   - Or weak suggestions? ("should", "consider", "try to")

2. **Rationalization defenses:**
   - Is there a rationalization table?
   - Are common excuses addressed?
   - Are red flags listed for self-checking?

3. **Commitment mechanisms:**
   - Does skill require announcements?
   - Are there checkpoints or TodoWrite tracking?
   - Are choices explicit?

4. **Bright-line rules:**
   - Are rules clear and unambiguous?
   - Or do they leave wiggle room? ("use judgment", "as appropriate")

**Red flags:**

- Critical instructions using "should" instead of "must"
- No rationalization table for discipline-enforcing skills
- "Use your judgment" for critical decisions
- No red flags list
- No commitment mechanisms (announcements, checklists)

**Good patterns:**

- "YOU MUST" for non-negotiable requirements
- Rationalization table with excuse → reality pairs
- Red flags section for self-checking
- Explicit "no exceptions" statements
- TodoWrite for multi-step processes

**Pass criteria:**

- Critical requirements use authority language
- Rationalization table present (for discipline skills)
- Red flags listed
- Bright-line rules where compliance matters

**Example findings:**

| Finding | Priority | Proposed Fix |
|---------|----------|--------------|
| "You should run tests" for critical step | P1 | Change to "YOU MUST run tests" |
| No rationalization table | P1 | Add table with common excuses and counters |
| "Use judgment" for security decision | P0 | Define explicit criteria or escalation |

---

## D5: Precision (P1)

**What it catches:** Vague wording, loopholes, wiggle room.

**How to check:**

1. For each instruction, ask: "Could someone interpret this differently?"
2. Look for quantifiers: "some", "many", "appropriate", "reasonable"
3. Look for hedges: "generally", "usually", "often", "might"
4. Check thresholds: Are numbers specific or vague?
5. Check conditions: Are triggers precise or fuzzy?

**Red flags:**

- "Appropriate" without defining criteria
- "Reasonable" without bounds
- "Several" instead of specific count
- "Soon" instead of specific timing
- "Important" without explaining why/when
- Comparative without baseline ("faster", "better", "simpler")

**Good patterns:**

- Specific numbers: "retry 3 times", "wait 5 seconds"
- Explicit criteria: "appropriate means: [list]"
- Bounded ranges: "between 2-5 items"
- Defined thresholds: "if response time > 500ms"

**Pass criteria:**

- Instructions are unambiguous
- Quantifiers are specific or defined
- Thresholds are explicit
- No wiggle room in critical paths

**Example findings:**

| Finding | Priority | Proposed Fix |
|---------|----------|--------------|
| "Wait an appropriate amount of time" | P1 | "Wait 2^n seconds where n = retry count, max 30 seconds" |
| "Handle several edge cases" | P1 | List the specific edge cases |
| "If the task is complex" | P1 | Define: "complex = >3 files OR architectural change OR security-sensitive" |

---

## D6: Actionability (P1)

**What it catches:** Instructions clear in theory but ambiguous in practice.

**How to check:**

1. For each instruction, ask: "Could I do this right now without asking questions?"
2. Are tools/commands specified?
3. Are file paths or locations clear?
4. Is the expected output defined?
5. What does success look like?

**Red flags:**

- "Verify the configuration" — how? what tool?
- "Update the relevant files" — which files?
- "Ensure quality" — what criteria?
- "Follow best practices" — which ones?
- Instructions that require external knowledge not provided

**Good patterns:**

- Specific commands: "Run `npm test`"
- Explicit paths: "Edit `src/config.ts`"
- Clear success criteria: "Tests pass with 0 failures"
- Links to external docs when needed
- Examples showing the action

**Pass criteria:**

- Every instruction is immediately actionable
- Tools and commands specified
- Locations explicit
- Success criteria verifiable

**Example findings:**

| Finding | Priority | Proposed Fix |
|---------|----------|--------------|
| "Verify the service is running" | P1 | "Run `curl localhost:8080/health` — expect 200 OK" |
| "Update relevant documentation" | P1 | List specific files or provide checklist |
| "Follow the style guide" | P2 | Link to style guide or inline key rules |

---

## D7: Internal Consistency (P1)

**What it catches:** Contradictions between sections, terminology drift.

**How to check:**

1. List all key terms — is each defined consistently?
2. Compare Process section with Examples — do they match?
3. Compare Decision Points with Process — are decisions consistent?
4. Check cross-references — do they say the same thing?
5. Look for the same concept described differently in different sections

**Red flags:**

- Term used with different meanings in different sections
- Example shows different steps than Process describes
- Decision Points contradict Process flow
- Numbered steps differ between sections
- References contradict main SKILL.md

**Good patterns:**

- Terminology glossary or consistent "X means Y" definitions
- Examples that exactly follow Process steps
- Decision Points that map to Process decision moments
- Single source of truth for key concepts

**Pass criteria:**

- Terminology consistent throughout
- Examples match Process
- No contradictions between sections
- References align with SKILL.md

**Example findings:**

| Finding | Priority | Proposed Fix |
|---------|----------|--------------|
| "Entry Gate" in Process, "Setup Phase" in Examples | P1 | Standardize to "Entry Gate" throughout |
| Process says 4 steps, Example shows 5 | P1 | Align Example with Process |
| Decision Points says "ask user", Process says "proceed" | P0 | Resolve contradiction — which is correct? |

---

## D8: Scope Boundaries (P1)

**What it catches:** Missing "When NOT to Use", unclear exclusions.

**How to check:**

1. Is there a "When NOT to Use" section?
2. Are exclusions specific and actionable?
3. Does the skill clearly define what's out of scope?
4. Are there handoffs to other skills for excluded cases?
5. Could someone mistakenly use this skill for something it doesn't cover?

**Red flags:**

- No "When NOT to Use" section
- Vague exclusions: "when not appropriate"
- Skill tries to do too much (scope creep)
- No handoff guidance for excluded cases
- Boundary between this skill and related skills unclear

**Good patterns:**

- Explicit "When NOT to Use" with specific scenarios
- Handoffs: "For X, use [other-skill] instead"
- Clear scope statement in Overview
- Non-goals listed explicitly

**Pass criteria:**

- "When NOT to Use" section present
- Exclusions are specific
- Handoffs to related skills defined
- Scope is clear and bounded

**Example findings:**

| Finding | Priority | Proposed Fix |
|---------|----------|--------------|
| No "When NOT to Use" section | P1 | Add section with common misuse cases |
| Exclusion "when it's not needed" is vague | P1 | Specify: "when code is read-only" or "when changes are trivial" |
| Overlap with related skill unclear | P1 | Add: "For [case], use [other-skill] instead" |

---

## D9: Reference Validity (P2)

**What it catches:** Broken links, outdated references, missing assets.

**How to check:**

1. Click/verify every link in SKILL.md
2. Check that referenced files exist
3. Check for orphaned files in references/ (exist but not linked)
4. Look for stale content (old dates, deprecated features, dead links)
5. Verify external links still work

**Red flags:**

- Broken links (404, file not found)
- References to files that don't exist
- Orphaned files not linked from SKILL.md
- Outdated examples (old API versions, deprecated syntax)
- External links that no longer work

**Good patterns:**

- All internal links verified working
- No orphaned files
- External links use stable URLs (documentation, not blog posts)
- Dates/versions noted where relevant

**Pass criteria:**

- All links work
- All references exist
- No orphaned files
- Content is current

**Example findings:**

| Finding | Priority | Proposed Fix |
|---------|----------|--------------|
| Link to `references/examples.md` broken | P2 | Create file or remove link |
| `references/old-api.md` not linked anywhere | P2 | Link it or delete it |
| Example uses deprecated `fs.exists()` | P2 | Update to `fs.existsSync()` |

---

## D10: Edge Cases (P2)

**What it catches:** Boundary situations undefined.

**How to check:**

1. What happens with empty input?
2. What happens with very large input?
3. What happens with invalid input?
4. What happens when dependencies fail?
5. What happens at boundaries (0, 1, max)?

**Red flags:**

- No mention of error handling
- Happy path only — no failure scenarios
- Boundary conditions not addressed
- "Assumes valid input" without validation
- Dependencies assumed always available

**Good patterns:**

- Explicit handling for empty/null cases
- Bounds checking with defined behavior
- Graceful degradation for failures
- Input validation guidance
- Troubleshooting for common edge cases

**Pass criteria:**

- Critical edge cases addressed
- Error handling defined
- Boundary behavior specified
- Failure modes documented

**Example findings:**

| Finding | Priority | Proposed Fix |
|---------|----------|--------------|
| No handling for empty input | P2 | Add: "If no files found, report and exit" |
| What if API is unavailable? | P2 | Add timeout and fallback behavior |
| Boundary: what if 0 items? 1000 items? | P2 | Define limits and behavior at boundaries |

---

## D11: Feasibility (P2)

**What it catches:** Requirements that can't be achieved.

**How to check:**

1. Can each step actually be done with available tools?
2. Are time/resource expectations realistic?
3. Do prerequisites actually exist?
4. Are external dependencies accessible?
5. Is the required knowledge available?

**Red flags:**

- Steps requiring unavailable tools
- Unrealistic expectations ("always perfect")
- Prerequisites that don't exist
- External services without fallback
- Requires information that can't be obtained

**Good patterns:**

- Tool availability checked or alternatives provided
- Realistic expectations with acceptable tolerances
- Prerequisites verified or created
- Fallbacks for external dependencies
- Knowledge requirements stated with sources

**Pass criteria:**

- All steps achievable
- Expectations realistic
- Dependencies accessible
- Alternatives for unavailable resources

**Example findings:**

| Finding | Priority | Proposed Fix |
|---------|----------|--------------|
| Requires `jq` but not installed by default | P2 | Add: "Requires jq, install with `brew install jq`" |
| "Always achieve 100% coverage" — unrealistic | P2 | Change to: "Target 80% coverage, note gaps" |
| References internal wiki that agents can't access | P1 | Inline key content or provide alternative |

---

## D12: Testability (P2)

**What it catches:** Requirements that can't be verified.

**How to check:**

1. For each requirement, ask: "How would I verify this was done?"
2. Are success criteria measurable?
3. Can compliance be checked automatically or manually?
4. Is there a clear pass/fail determination?
5. Can behavioral testing validate this?

**Red flags:**

- "Ensure quality" — how to measure?
- "Be thorough" — what counts as thorough?
- "Handle appropriately" — what's appropriate?
- Requirements without verification method
- Subjective criteria with no rubric

**Good patterns:**

- Measurable criteria: "tests pass", "no errors", "under 500ms"
- Verification commands: "Run X, expect Y"
- Checklists with concrete items
- Rubrics for subjective assessments
- Testing guidance in Verification section

**Pass criteria:**

- Requirements are verifiable
- Success criteria are measurable
- Verification method specified
- Pass/fail determination clear

**Example findings:**

| Finding | Priority | Proposed Fix |
|---------|----------|--------------|
| "Ensure code quality" — untestable | P2 | Define: "No lint errors, all tests pass, no security warnings" |
| "Be thorough" — no verification | P2 | Add checklist of what "thorough" includes |
| No Verification section | P2 | Add section with specific checks |

---

## D13: Integration Clarity (P1, Conditional)

**When to check:** Orchestration-type skills only — skills that coordinate other skills or have complex handoffs.

**What it catches:** Unclear handoffs to/from other skills.

**How to check:**

1. What skills does this orchestrate or call?
2. What triggers the handoff?
3. What state/artifacts are passed?
4. What happens if the downstream skill fails?
5. Are return conditions defined?

**Red flags:**

- "Then use [other-skill]" without handoff details
- State passed implicitly
- No failure handling for orchestrated skills
- Return conditions undefined
- Circular dependencies between skills

**Good patterns:**

- Explicit trigger conditions for handoffs
- Artifacts passed clearly specified
- Failure handling at each handoff point
- Return conditions and continuation logic
- Dependency diagram in Extension Points

**Pass criteria:**

- Handoffs explicitly defined
- State/artifacts specified
- Failure handling at handoffs
- No circular dependencies
- Return conditions clear

**Example findings:**

| Finding | Priority | Proposed Fix |
|---------|----------|--------------|
| "Hand off to testing-skills" — no state passed | P1 | Specify: "Pass draft SKILL.md path and design context location" |
| What if downstream skill fails? | P1 | Add: "If testing fails, return with feedback for revision" |
| Circular dependency with brainstorming-skills | P0 | Define clear entry/exit conditions to break cycle |
