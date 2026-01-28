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
- [D14: Example Quality (P1)](#d14-example-quality-p1)
- [D15: Cognitive Manageability (P2)](#d15-cognitive-manageability-p2)

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

3. **Size guidance:**
   - [ ] Body reasonably sized (~500 lines is a guideline, not a hard cap; consider splitting to references/ if significantly larger)
   - [ ] References one level deep from SKILL.md

4. **Structure:**
   - [ ] Progressive disclosure (overview → details)
   - [ ] Consistent heading levels

**Red flags:**

- Missing required sections
- Name not gerund form ("code-review" vs "reviewing-code")
- Description over 1024 characters
- Body significantly exceeds ~500 lines with content that could be split to references/
- Nested references (reference files linking to other reference files)
- Inconsistent heading hierarchy

**Pass criteria:**

- All required sections present
- Frontmatter valid
- Size reasonable (lengthy skills have content appropriately split to references/)
- References one level deep

**Example findings:**

| Finding | Priority | Proposed Fix |
|---------|----------|--------------|
| Name is "skill-review" (noun) | P0 | Rename to "reviewing-skills" (gerund) |
| Body is 650 lines | P1 | Split detailed content to references/ |
| Missing required "Examples" section | P0 | Add Examples section with BAD/GOOD patterns |

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

**What it catches:** Vague wording that allows multiple interpretations (language quality).

**Distinction from D6:** D5 checks if language is *unambiguous* — only one valid interpretation. D6 checks if instructions are *executable* — reader has what they need to act. A statement can be precise but not actionable ("Run the validation script" — unambiguous but which script?). A statement can fail both ("Handle appropriately" — vague AND unexecutable).

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

- Instructions have only one valid interpretation
- Quantifiers are specific or defined
- Thresholds are explicit
- No wiggle room in critical paths

**Example findings:**

| Finding | Priority | Proposed Fix |
|---------|----------|--------------|
| "Wait an appropriate amount of time" | P1 | "Wait 2^n seconds where n = retry count, max 30 seconds" |
| "Handle several edge cases" | P1 | List the specific edge cases |
| "If the task is complex" | P1 | Define: "complex = >3 files OR architectural change OR security-sensitive" |

**D5 vs D6 examples:**

| Statement | D5 (Precision) | D6 (Actionability) |
|-----------|----------------|-------------------|
| "Handle errors appropriately" | FAIL — "appropriately" is vague | FAIL — no method specified |
| "Run the validation script" | PASS — unambiguous | FAIL — which script? where? |
| "Retry 3 times" | PASS — specific | FAIL — how to retry? what delay? |
| "Run `./validate.py`, expect 'OK'" | PASS | PASS |

---

## D6: Actionability (P1)

**What it catches:** Instructions that lack execution details — tools, paths, methods unspecified (execution readiness).

**Distinction from D5:** D5 checks if language is *unambiguous*. D6 checks if the reader can *immediately execute* without asking questions or looking things up. An instruction can be unambiguous but still require the reader to figure out HOW to do it.

**How to check:**

1. For each instruction, ask: "Could I do this right now without asking questions?"
2. Are tools/commands specified?
3. Are file paths or locations clear?
4. Is the expected output defined?
5. What does success look like?
6. Is assumed knowledge actually provided or linked?

**Red flags:**

- "Verify the configuration" — how? what tool?
- "Update the relevant files" — which files?
- "Ensure quality" — what criteria?
- "Follow best practices" — which ones?
- "Run the script" — which script? where?
- Instructions that require external knowledge not provided or linked

**Good patterns:**

- Specific commands: "Run `npm test`"
- Explicit paths: "Edit `src/config.ts`"
- Clear success criteria: "Tests pass with 0 failures"
- Links to external docs when needed
- Examples showing the action
- Expected output specified

**Pass criteria:**

- Every instruction is immediately executable
- Tools and commands specified
- Locations explicit
- Success criteria verifiable
- Required knowledge provided or linked

**Example findings:**

| Finding | Priority | Proposed Fix |
|---------|----------|--------------|
| "Verify the service is running" | P1 | "Run `curl localhost:8080/health` — expect 200 OK" |
| "Update relevant documentation" | P1 | List specific files or provide checklist |
| "Follow the style guide" | P2 | Link to style guide or inline key rules |
| "Run the validation script" | P1 | "Run `./scripts/validate.py` — expect exit code 0" |

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

**What it catches:** Requirements that can't be achieved given available resources, tools, knowledge, or constraints.

**Distinction from D12:** D11 asks "CAN this be done?" — are the resources available? D12 asks "Can we VERIFY it was done?" — is there a way to check? A requirement can be feasible but untestable ("think carefully" — doable but unverifiable). A requirement can be testable but infeasible ("run on 1000 servers" — verifiable but you don't have 1000 servers).

**How to check:**

1. **Tool availability:**
   - Does each step specify what tool to use?
   - Are tools available by default, or do they need installation?
   - Are there platform-specific tools that won't work everywhere?

2. **Knowledge requirements:**
   - What does the reader need to know to follow this?
   - Is that knowledge provided, linked, or assumed?
   - Can an agent actually obtain this knowledge?

3. **Resource constraints:**
   - What compute/memory/time does this require?
   - Are there API limits, rate limits, or quotas?
   - Does this require credentials or permissions the agent might not have?

4. **Environmental assumptions:**
   - What does the skill assume about the environment?
   - Git repo? Specific language runtime? Network access?
   - Are these assumptions stated or silent?

5. **Dependency accessibility:**
   - Are external services always available?
   - What happens if a dependency is down or changed?
   - Are there fallbacks?

**Red flags:**

- Steps requiring unavailable tools without install instructions
- Unrealistic expectations ("always perfect", "100% accuracy", "zero errors")
- Prerequisites that don't exist or aren't provided
- External services without fallback or error handling
- Requires information that agents cannot obtain (internal wikis, private docs)
- Assumes credentials/permissions without noting them
- Platform-specific instructions without alternatives
- "Use [tool]" without specifying version or installation
- Requires human judgment that agents can't provide
- Time-dependent instructions ("wait until the market opens")

**Good patterns:**

- Tool availability noted: "Requires X, install with [command]"
- Realistic expectations: "Target 80% coverage" not "100% coverage"
- Prerequisites listed explicitly with verification commands
- Fallbacks for external dependencies: "If X unavailable, use Y"
- Knowledge requirements stated with sources or inlined
- Environment assumptions documented in Prerequisites section
- Platform alternatives: "On Mac use X, on Linux use Y"
- Graceful degradation: "If full analysis not possible, provide partial"

**Pass criteria:**

- All steps achievable with stated resources
- Expectations realistic and toleranced
- Dependencies accessible or fallbacks provided
- Knowledge requirements stated and obtainable
- Environmental assumptions explicit
- No hidden resource requirements

**Example findings:**

| Finding | Priority | Proposed Fix |
|---------|----------|--------------|
| Requires `jq` but not installed by default | P2 | Add: "Requires jq, install with `brew install jq`" |
| "Always achieve 100% coverage" — unrealistic | P2 | Change to: "Target 80% coverage, document gaps" |
| References internal wiki that agents can't access | P1 | Inline key content or provide alternative source |
| "Run the enterprise linter" — what linter? | P1 | Specify tool name, version, and installation |
| Assumes AWS credentials exist | P2 | Add: "Requires AWS credentials in environment or ~/.aws/credentials" |
| "Wait for approval" — agent can't wait for humans | P1 | Restructure: "Pause and request approval, then resume" or remove |
| Requires 16GB RAM for analysis | P2 | Note requirement; provide lightweight alternative if possible |

**Questions to ask:**

- "If I tried to follow this skill right now, what would stop me?"
- "What does this assume I have that I might not have?"
- "What could change externally that would break this?"

---

## D12: Testability (P2)

**What it catches:** Requirements that can't be verified — no way to check if the skill was followed or if it produced the right outcome.

**Distinction from D11:** D11 asks "CAN this be done?" D12 asks "Can we VERIFY it was done?" A requirement can be feasible but untestable ("think carefully" — doable but how do you check?). This dimension matters because untestable requirements can't be validated by testing-skills.

**Connection to testing-skills:** This dimension checks if requirements are *structured for testing*. The actual behavioral testing happens in testing-skills. If requirements fail D12, testing-skills won't be able to validate them.

**How to check:**

1. **Measurability:**
   - For each requirement, ask: "How would I verify this was done?"
   - Can success be measured objectively?
   - Is there a number, state, or artifact that indicates success?

2. **Observability:**
   - Can compliance be observed from outside?
   - Are there outputs, logs, or artifacts that show the skill was followed?
   - Or does it rely on internal state that can't be checked?

3. **Reproducibility:**
   - Would two reviewers agree on whether this was done?
   - Is there enough specificity to avoid subjective judgment?

4. **Automation potential:**
   - Can verification be automated (script, test, linter)?
   - Or does it require human judgment?

5. **Pass/fail clarity:**
   - Is there a clear threshold between pass and fail?
   - Or is it a gradient with no defined cutoff?

**Red flags:**

- "Ensure quality" — quality of what? By what measure?
- "Be thorough" — what counts as thorough? Checklist?
- "Handle appropriately" — what's appropriate? Defined where?
- "Think carefully" — unobservable internal state
- "Use good judgment" — subjective, varies by person
- "Make it better" — better than what? By what metric?
- Requirements without verification method
- Subjective criteria with no rubric or examples
- "Consider" or "take into account" — no observable output
- Success defined as absence: "no issues" — how to confirm none exist?
- Process requirements with no artifacts: "review the code" — what proves review happened?

**Good patterns:**

- Measurable criteria: "tests pass", "no lint errors", "response under 500ms"
- Verification commands: "Run `npm test`, expect 0 failures"
- Observable artifacts: "Create review report at [path]"
- Checklists with concrete items (each item is verifiable)
- Rubrics for subjective assessments with specific criteria
- Verification section with explicit checks
- Examples of pass vs fail cases
- Thresholds defined: "coverage > 80%", "complexity < 10"

**Pass criteria:**

- Requirements are verifiable by observation or measurement
- Success criteria have clear pass/fail thresholds
- Verification method specified for critical requirements
- Subjective criteria have rubrics or examples
- Process requirements produce observable artifacts

**Example findings:**

| Finding | Priority | Proposed Fix |
|---------|----------|--------------|
| "Ensure code quality" — untestable | P2 | Define: "No lint errors, all tests pass, no security warnings" |
| "Be thorough" — no verification | P2 | Add checklist of what "thorough" includes |
| No Verification section | P2 | Add section with specific checks |
| "Review the code carefully" — no artifact | P1 | Add: "Document findings in review report" |
| "Consider edge cases" — unobservable | P2 | Change to: "List edge cases considered in [section]" |
| "Use appropriate error handling" — vague | P1 | Define: "All P0 errors have try/catch with logging" |
| "Make it readable" — subjective | P2 | Add rubric: "Functions < 50 lines, names descriptive, comments for non-obvious logic" |

**Testability spectrum:**

| Level | Example | Testable? |
|-------|---------|-----------|
| Objective + automated | "Tests pass" | Yes — run tests |
| Objective + manual | "All links work" | Yes — click each link |
| Rubric-based | "Code is readable per style guide" | Partially — apply rubric |
| Subjective | "Code is elegant" | No — no shared definition |
| Internal state | "Think carefully" | No — unobservable |

**Questions to ask:**

- "If I claimed this was done, how would you check?"
- "Could two reviewers disagree on whether this was satisfied?"
- "What artifact or observation proves this happened?"

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

---

## D14: Example Quality (P1)

**What it catches:** Examples that exist but are unrealistic, lack diversity, don't show graduated complexity, or fail to demonstrate the skill's value.

**Distinction from D3:** D3 checks that an Examples section exists with BAD/GOOD patterns. D14 checks whether those examples are *effective* — realistic enough to transfer to real situations, diverse enough to cover the skill's scope, and graduated to build understanding.

**How to check:**

1. **Realism:**
   - Are examples based on plausible scenarios an agent would encounter?
   - Or are they contrived/toy examples that don't reflect real complexity?
   - Would an agent recognize "I'm in this situation" from the example?

2. **Diversity:**
   - Do examples cover the skill's full scope, or just one narrow case?
   - Are different contexts represented (different file types, project sizes, error types)?
   - Do BAD examples show *different kinds* of failures, not just one failure repeated?

3. **Graduated complexity:**
   - Is there a simple example that shows the core pattern?
   - Are there progressively complex examples that show edge cases and nuance?
   - Can a reader understand the simple case before tackling the complex one?

4. **Failure mode coverage:**
   - Do BAD examples show the *common* ways agents fail, not just strawmen?
   - Are BAD examples ones an agent might actually produce under pressure?
   - Is the distinction between BAD and GOOD clear and instructive?

5. **Transferability:**
   - After reading examples, could an agent handle a *different* situation correctly?
   - Or do examples only show how to handle the exact cases shown?

**Red flags:**

- Single example claimed to represent the whole skill
- BAD examples that are obviously wrong (no agent would actually do that)
- Examples all from one domain (all web, all CLI, all Python)
- No simple "base case" example — jumps straight to complex scenarios
- Examples that are too short to show the skill's full process
- GOOD examples that are actually mediocre (just "less bad")
- Toy examples: "Imagine a function called `doThing()`..."
- Examples that skip the hard parts: "...then handle the edge cases appropriately"

**Good patterns:**

- 2-3 examples showing simple → moderate → complex cases
- BAD examples that show realistic mistakes (the kind agents actually make)
- Examples from different contexts (different languages, project types, scenarios)
- Full worked examples showing complete skill execution, not just snippets
- Clear annotations explaining *why* BAD is bad and GOOD is good
- Examples that highlight decision points and show how to navigate them
- "What would happen if..." variations that show consequences

**Pass criteria:**

- Examples are realistic — agents would recognize the situations
- Examples are diverse — cover skill's scope, not just one narrow case
- Complexity is graduated — simple case first, then progressively harder
- BAD examples show realistic failures, not strawmen
- Examples are instructive — reader learns principles, not just specific cases
- Hard parts are shown, not skipped

**Example findings:**

| Finding | Priority | Proposed Fix |
|---------|----------|--------------|
| Only one example, covers narrow case | P1 | Add 2-3 examples covering different contexts |
| BAD example is strawman ("forgot to save file") | P1 | Replace with realistic failure an agent would make under pressure |
| All examples are Python web apps | P2 | Add examples from different domains (CLI, library, config) |
| GOOD example skips the hard decision | P1 | Expand to show how decision was made, not just the outcome |
| No simple base case — first example is complex | P1 | Add minimal example showing core pattern before complex ones |
| Examples show what to do, not why | P2 | Add annotations explaining the reasoning |

**Questions to ask:**

- "If I only saw these examples, would I understand what to do in a *different* situation?"
- "Would an agent under pressure actually make the mistake shown in the BAD example?"
- "Is there a simple case that teaches the core pattern before the complex cases?"

---

## D15: Cognitive Manageability (P2)

**What it catches:** Skills that are structurally correct and precisely worded but unusable in practice because they overwhelm working memory or require holding too much context simultaneously.

**Why this matters:** Agents have limited context windows and attention. A skill can pass all other dimensions yet fail because following it requires tracking too many things at once, or because the structure doesn't match how agents process information. Claude Code provides tools to externalize memory — skills should guide agents to use them.

**How to check:**

1. **Step count and depth:**
   - How many steps must be held in memory simultaneously?
   - Are there deeply nested conditionals (if → if → if)?
   - Can each step be completed before needing to think about the next?
   - Does the skill use TaskCreate to externalize multi-step tracking?

2. **Decision complexity:**
   - How many factors must be weighed for each decision?
   - Are decision criteria independent or do they interact?
   - Can decisions be made sequentially, or must multiple be held pending?

3. **Cross-referencing burden:**
   - How often must the agent jump between sections?
   - Are related concepts co-located or scattered?
   - Can a section be understood without flipping back to previous sections?

4. **Chunking support:**
   - Is information grouped into meaningful chunks?
   - Are there natural "save points" where partial progress is stable?
   - Can the skill be applied in phases without losing state?

5. **Progressive disclosure:**
   - Does the skill front-load what matters most?
   - Can simple cases be handled without reading the full skill?
   - Is complexity introduced gradually or all at once?

6. **Parallel vs sequential load:**
   - How many things must be tracked simultaneously?
   - Or can items be processed one at a time?

7. **Tool usage for memory externalization:**
   - Does the skill guide use of TaskCreate for complex checklists?
   - Does it delegate sub-work to Task (subagents) where appropriate?
   - Does it instruct agents to re-read files rather than rely on memory?

**Red flags:**

- More than 7 top-level steps without TaskCreate tracking
- Nested conditionals more than 2 levels deep
- Decision tables with more than 4 factors to weigh simultaneously
- Frequent forward/backward references between sections
- No clear phases or checkpoints — one long undifferentiated process
- Important details buried in walls of text
- Multiple processes interleaved rather than sequential
- "Remember to also check X" scattered throughout (should be in a checklist)
- Critical information only in footnotes or references
- Steps that require output from multiple prior non-adjacent steps
- Assumes agent remembers file contents from earlier in conversation
- Complex sub-tasks inline instead of delegated to Task tool

**Good patterns:**

- Clear phases with distinct purposes (Entry → Process → Exit)
- Each section self-contained where possible
- Key information surfaced early, details available when needed
- Decision tables with ≤4 factors
- "Quick path" for simple cases separate from full complexity
- **TaskCreate for multi-step processes** — externalize the checklist
- **Task tool for complex sub-work** — delegate to subagent, receive summary
- **Explicit "re-read X before Y" instructions** — don't assume agent remembers
- Natural checkpoints where state is stable
- Related concepts co-located, not scattered
- Visual hierarchy that guides attention
- Summary tables before detailed explanations

**Tools that reduce cognitive load:**

Claude Code provides tools that externalize memory and offload complexity. Skills should guide agents to use these:

| Tool | How It Helps | Use When |
|------|--------------|----------|
| **TaskCreate / TaskUpdate** | Externalizes checklists to persistent storage — agent doesn't need to hold all steps in working memory | Multi-step processes, complex workflows |
| **TaskList / TaskGet** | Retrieves current state without relying on memory | Resuming after context compaction, checking progress |
| **Task** (subagents) | Offloads complex sub-tasks to separate context window — main agent receives summary, not raw data | Independent sub-tasks, parallel work streams, exploration |
| **Read** | Re-reads files instead of trying to remember contents | Any time file contents are needed — don't memorize |

**When cognitive load is high, use tools:**

If a skill has inherent complexity that can't be simplified, it should explicitly guide agents to use memory-externalizing tools:

| High Complexity Pattern | Mitigation | Skill Should Say |
|-------------------------|------------|------------------|
| Many steps to track | TaskCreate | "Create tasks for each phase before starting" |
| Need to remember findings | TaskUpdate with notes | "Record findings in task metadata as you go" |
| Complex sub-problem | Task (subagent) | "Delegate X to a subagent; receive summary" |
| File contents needed later | Read again | "Re-read the file before proceeding" |
| Parallel workstreams | Multiple Task calls | "Launch subagents in parallel for independent items" |

**Pass criteria:**

- Skill can be applied without exceeding working memory
- Decisions can be made with information that's locally available
- Clear phases allow partial completion with stable state
- Progressive disclosure — simple cases don't require full complexity
- Cross-referencing burden is minimal
- Complexity is structured, not dumped
- Tool-based externalization used where appropriate for complex skills

**Severity calibration:**

| Pattern | Impact | Priority |
|---------|--------|----------|
| >10 steps with no phases or task tracking | High — agents lose track | P1 |
| 3+ level nested conditionals | High — decision path unclear | P1 |
| Assumes memory of file contents | Medium — leads to errors | P1 |
| Constant cross-referencing required | Medium — slows execution | P2 |
| No quick path for simple cases | Medium — overhead on easy tasks | P2 |
| Dense text without visual hierarchy | Low — harder to scan | P2 |
| Complex sub-work not delegated to subagents | Medium — context pollution | P2 |

**Example findings:**

| Finding | Priority | Proposed Fix |
|---------|----------|--------------|
| 12 steps with no phase structure or task tracking | P1 | Group into 3-4 phases; add "Use TaskCreate to track progress" |
| Decision requires weighing 6 factors simultaneously | P1 | Restructure as sequential filters or use decision tree |
| Must refer to 3 prior sections to understand current step | P2 | Co-locate required context or add summary |
| No quick path — trivial cases require full process | P2 | Add "Fast Path" section for simple cases |
| Nested if → if → if → then structure | P1 | Flatten to decision table or sequential checks |
| "Also remember X" scattered in 5 different places | P2 | Consolidate into TaskCreate checklist |
| 500-line skill with no phases or headers | P1 | Add structure with clear sections and phases |
| "Using the findings from earlier..." without re-read | P1 | Add: "Re-read [file] before this step" |
| Complex exploration inline in main process | P2 | Add: "Delegate exploration to Explore subagent" |

**Example of tool-guided process in a skill:**

```markdown
## Process

### Phase 1: Setup

1. **Create tracking tasks:**
   Use TaskCreate to create one task per dimension. This externalizes your
   checklist so you don't need to hold all dimensions in memory.

2. **Inventory inputs:**
   Read all relevant files. Do not try to memorize — you will re-read as needed.

### Phase 2: Analysis (per dimension)

For each dimension:
1. TaskUpdate to mark in_progress
2. Re-read the relevant section of the skill being reviewed
3. Check the dimension using the guidance in references/
4. TaskUpdate to mark completed with findings in notes

### Phase 3: Synthesis

1. TaskList to see all findings
2. ...
```

**Questions to ask:**

- "How many things must I hold in my head to complete step N?"
- "If I paused mid-skill, could I resume without re-reading everything?"
- "Can I handle a simple case without engaging with all the complexity?"
- "Where are the natural 'save points' in this process?"
- "Does this skill tell me to use TaskCreate, or does it expect me to track everything mentally?"
- "When I need file contents, does the skill tell me to re-read or assume I remember?"

**Interaction with other dimensions:**

- **D2 (Process Completeness):** A process can be complete but unmanageable. D2 checks if steps exist; D15 checks if they can be followed without overload.
- **D3 (Structural Conformance):** D3 checks required sections exist; D15 checks if the structure *supports* cognitive processing.
- **D6 (Actionability):** D6 checks if instructions are executable; D15 checks if they're executable *given attention limits*.
- **D11 (Feasibility):** D11 checks if requirements can be achieved; D15 checks if they can be achieved *without exceeding cognitive capacity*.
