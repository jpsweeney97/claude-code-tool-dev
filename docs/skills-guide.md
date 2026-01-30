# Skills

## Table of Contents

- [Skill Structure](#skill-structure)
- [Skill Design Principles](#skill-design-principles)
- [Common Skill Types](#common-skill-types)
- [Writing Effective Skills](#writing-effective-skills)
- [Patterns and Troubleshooting](#patterns-and-troubleshooting)

## Skill Structure

Each skill is a directory with `SKILL.md` as the entrypoint. The `SKILL.md` contains the main instructions and is required. Other files are optional and can be used to build more powerful skills: templates for Claude to fill in, example outputs showing the expected format, scripts Claude can execute, or detailed reference documentation.

### Directory Structure

```
my-skill/
├── SKILL.md                  # Required - main skill file
├── scripts/                  # Optional - executable code
│    ├── process_data.py      # Example
│    └── validate.sh          # Example
├── references/               # Optional - documentation
│    ├── api-guide.md         # Example
│    └── examples/            # Example
└── assets/                   # Optional - templates, etc.
     └── report-template.md   # Example
```

### The SKILL.md file

Every skill starts with a `SKILL.md` file containing YAML frontmatter and Markdown instructions.

#### YAML frontmatter

The YAML frontmatter is how Claude decides whether to load your skill.

**Minimal Required Format**

```yaml
---
name: your-skill-name
description: What it does + When to use it + Key capabilities
---
```

There are only two required YAML frontmatter fields:

**name**:

- kebab-case only
- No spaces or capitals
- Should match folder name

**description**:

- **MUST include BOTH:**
  - What the skill does
  - When to use it (trigger conditions)
- Under 1024 characters
- No XML tags (`<` or `>`)
- Include specific tasks users might say
- Mention file types if relevant

The remaining available YAML frontmatter fields are optional - use them as needed:

| Field                      | Required | Description                                                                                                                                           |
| :------------------------- | :------- | :---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `argument-hint`            | No       | Hint shown during autocomplete to indicate expected arguments. Example: `[issue-number]` or `[filename] [format]`.                                    |
| `disable-model-invocation` | No       | Set to `true` to prevent Claude from automatically loading this skill. Use for workflows you want to trigger manually with `/name`. Default: `false`. |
| `user-invocable`           | No       | Set to `false` to hide from the `/` menu. Use for background knowledge users shouldn't invoke directly. Default: `true`.                              |
| `allowed-tools`            | No       | Tools Claude can use without asking permission when this skill is active.                                                                             |
| `model`                    | No       | Model to use when this skill is active.                                                                                                               |
| `context`                  | No       | Set to `fork` to run in a forked subagent context.                                                                                                    |
| `agent`                    | No       | Which subagent type to use when `context: fork` is set.                                                                                               |
| `hooks`                    | No       | Hooks scoped to this skill's lifecycle.                                                                                                               |

#### Body content

The Markdown body after the frontmatter contains the skill instructions. There are no strict format restrictions. Write whatever helps agents perform the task effectively.

**Keep `SKILL.md` under 500 lines. Move detailed reference material to supporting files**

### Supporting files

Skills can include multiple files in their directory. This keeps `SKILL.md` focused on the essentials while letting Claude access detailed reference material only when needed. Large reference docs, specifications, or example collections don't need to load into context every time the skill runs.

#### File references

Reference supporting files from `SKILL.md` so Claude knows what each file contains and when to load it.

When referencing supporting files, use relative paths from the skill root:

```markdown
For complete details, read [the reference guide](references/REFERENCE.md)
For usage examples, read [examples.md](examples.md)
```

Keep file references one level deep from `SKILL.md`. Avoid deeply nested reference chains.

## Skill Design Principles

### Progressive disclosure

Skills use a three-level system:

- **First level (YAML frontmatter):** Always loaded in Claude's system prompt. Provides just enough information for Claude to know when each skill should be used without loading all of it into context.
- **Second level (SKILL.md body):** Loaded when Claude thinks the skill is relevant to the current task. Contains the full instructions and guidance.
- **Third level (Supporting files):** Additional files bundled within the skill directory that Claude can choose to navigate and discover only as needed.

This progressive disclosure minimizes token usage while maintaining specialized expertise.

### Composability

Claude can load multiple skills simultaneously. Skills should work well alongside others, not assume it's the only capability available.

### Concise is key

The context window is a public good. Each Skill shares the context window with everything else Claude needs to know, including:

- The system prompt
- Conversation history
- Other Skills' metadata
- User prompts

Not every token in a Skill has an immediate cost. At startup, only the metadata (name and description) from all Skills is pre-loaded. Claude reads SKILL.md only when the Skill becomes relevant, and reads additional files only as needed. However, being concise in SKILL.md still matters: once Claude loads it, every token competes with conversation history and other context.

**Default assumption**: Claude is already very smart

Only add context Claude doesn't already have. Challenge each piece of information:

- "Does Claude really need this explanation?"
- "Can I assume Claude knows this?"
- "Does this paragraph justify its token cost?"

### Set appropriate degrees of freedom

Match the level of specificity to the task's fragility and variability.

**High freedom**

Use when:

- Multiple approaches are valid
- Decisions depend on context
- Heuristics guide the approach

**Medium freedom**

Use when:

- A preferred pattern exists
- Some variation is acceptable
- Configuration affects behavior

**Low freedom**

Use when:

- Operations are fragile and error-prone
- Consistency is critical
- A specific sequence must be followed

### Start with Use Cases

Before writing anything, identify 2-3 concrete use cases your skill should enable.

**Good use case definition:**

```
Use Case: Project Sprint Planning
Trigger: User says "help me plan this sprint" or "create sprint tasks"
Steps:
1. Fetch current project status from Linear (via MCP)
2. Analyze team velocity and capacity
3. Suggest task prioritization
4. Create tasks in Linear with proper labels and estimates
Result: Fully planned sprint with tasks created
```

**Ask yourself:**

- What does the user want to accomplish?
- What multi-step workflows does this require?
- Which tools are needed (built-in or MCP?)
- What domain knowledge or best practices should be embedded?

### Define Success Criteria

**How will you know if a skill is working?**

These are aspirational targets — rough benchmarks rather than precise thresholds. Aim for rigor but accept that there will be an element of vibes-based assessment.

#### Quantitative Metrics

- **Skill triggers on 90% of relevant queries**
  - _How to measure:_ Run 10-20 test queries that should trigger your skill. Track how many times it loads automatically vs. requires explicit invocation.
- **Completes workflow in X tool calls**
  - _How to measure:_ Compare the same task with and without the skill enabled. Count tool calls and total tokens consumed.

#### Qualitative Metrics

- **Users don't need to prompt Claude about next steps**
  - _How to assess:_ During testing, note how often you need to redirect or clarify. Ask beta users for feedback.
- **Workflows complete without user correction**
  - _How to assess:_ Run the same request 3-5 times. Compare outputs for structural consistency and quality.
- **Consistent results across sessions**
  - _How to assess:_ Can a new user accomplish the task on first try with minimal guidance?

## Common Skill Types

Use this table to select the primary skill type before writing:

| If the skill needs to... | Primary type | Key indicator |
|--------------------------|--------------|---------------|
| Prevent Claude from skipping steps | Discipline | Claude tends to shortcut this workflow |
| Teach a structured method | Technique | Activity has learnable approach that beats improvisation |
| Encode reusable structures | Pattern | Task recurs with variations |
| Surface external information | Reference | Info exists but isn't in Claude's training data |

Most skills blend types but lean toward one. Identify the dominant type, then borrow techniques from others as needed.

### Discipline-Enforcing Skills (rules/requirements)

**Used for:** Enforcing methodologies that Claude might otherwise shortcut or skip entirely. These skills address a fundamental challenge: Claude tends to jump directly to solutions, claim completion without verification, or skip intermediate steps that seem unnecessary in the moment but prevent errors. Discipline skills make specific phases mandatory, requiring evidence of completion before proceeding. They're particularly valuable for workflows where skipping steps causes subtle, hard-to-detect problems—like writing tests after code (which produces weaker tests) or claiming "tests pass" without actually running them.

**Key techniques:**

- Rigid phase structure with explicit gates between stages
- Blocking language that makes requirements non-negotiable ("MUST", "before ANY", "NEVER skip")
- Evidence requirements before phase transitions (show output, cite file:line)
- Anti-pattern tables that name and describe common shortcuts
- Explicit "red flag" thoughts that signal rationalization ("this is simple enough to skip")
- Checklists requiring verification of each item, not just acknowledgment
- Failure mode descriptions showing consequences of skipping steps

### Technique Skills (how-to)

**Used for:** Teaching specific methods for accomplishing complex activities that benefit from structure. Unlike discipline skills (which constrain behavior), technique skills provide the how—structured approaches to tasks that would otherwise be ad-hoc. They're valuable when an activity has a learnable method that produces better results than improvisation: brainstorming that actually explores the space, code review that catches real issues, codebase exploration that builds accurate mental models. These skills transfer expertise about how to think about a problem, not just what to do.

**Key techniques:**

- Step-by-step workflows with clear inputs and outputs per stage
- Decision trees for handling variations and edge cases
- Templates that guide execution while allowing adaptation
- Worked examples showing the technique applied to real scenarios
- Heuristics for knowing when to apply which sub-technique
- Quality criteria for evaluating outputs at each stage
- Common failure modes and how to recognize/recover from them
- Iteration patterns showing when and how to loop back
- Perspective prompts that shift thinking ("What would a skeptic say?")
- Time-boxing guidance for stages that could expand indefinitely

### Pattern Skills (mental models)

**Used for:** Encoding reusable patterns for situations that recur with variations. These skills capture domain expertise—the accumulated knowledge of what works—in a form that can be applied repeatedly. They're valuable when a task has a known-good structure that shouldn't be reinvented each time: CLI tools have standard argument parsing patterns, frontend components have established composition patterns, clear writing follows identifiable principles. Pattern skills provide starting points and guardrails, not rigid prescriptions.

**Key techniques:**

- Template structures (file layouts, component hierarchies, document sections)
- Style guides with concrete before/after examples
- Checklists of elements to include and consider
- Anti-patterns showing what to avoid and why
- Variation catalogs showing how the pattern adapts to different contexts
- Decision tables mapping situations to pattern variants
- Composition rules for combining patterns
- Migration paths from one pattern to another
- Naming conventions that encode pattern semantics
- Integration points where patterns connect to larger systems

### Reference Skills (documentation/conventions/knowledge)

**Used for:** Providing lookup capabilities, reference information, or access to authoritative sources. Unlike other skill types that prescribe behavior, reference skills surface information that informs decisions. They're valuable when accurate, current information exists but isn't in Claude's training data or memory: documentation that evolves, configuration options that expand, APIs that change. Reference skills bridge the gap between what Claude knows and what's actually true in the current environment.

**Key techniques:**

- Integration with search tools (MCP servers, grep patterns, API queries)
- Structured query guidance that improves search effectiveness
- Quick-reference tables for common lookups
- Links to authoritative sources with context on when to consult them
- Caching strategies for frequently-accessed information
- Freshness indicators showing when information might be stale
- Cross-reference maps connecting related concepts
- Query reformulation suggestions when initial searches fail
- Disambiguation prompts when queries match multiple concepts
- Summary extraction from verbose sources

**This set of common skill types is not exhaustive. Most real skills blend types but lean toward one.**

## Writing Effective Skills

### The Description Field

The description field provides just enough information for Claude to know when each skill should be used without loading all of it into context. This is the first level of progressive disclosure.

**Structure:**

```
[What it does] + [When to use it] + [Key capabilities]
```

**Examples of good descriptions:**

```yaml
# Good - specific and actionable
description: Analyzes Figma design files and generates developer handoff documentation. Use when user uploads .fig files, asks for "design specs", "component documentation", or "design-to-code handoff".

# Good - includes trigger phrases
description: Manages Linear project workflows including sprint planning, task creation, and status tracking. Use when user mentions "sprint", "Linear tasks", "project planning", or asks to "create tickets".

# Good - clear value proposition
description: End-to-end customer onboarding workflow for PayFlow. Handles account creation, payment setup, and subscription management. Use when user says "onboard new customer", "set up subscription", or "create PayFlow account".
```

**Examples of bad descriptions:**

```yaml
# Too vague
description: Helps with projects.

# Missing triggers
description: Creates sophisticated multi-page documentation systems.

# Too technical, no user triggers
description: Implements the Project entity model with hierarchical relationships.
```

### Writing the Main Instructions

After the frontmatter, write the actual instructions in Markdown.

#### Recommended structure:

Adapt this template for skills. Replace bracketed sections with relevant specific content. Add sections as needed.

````markdown
```yaml
---
name: my-skill
description: [...]
---
```

# Skill Name

## Instructions

### Step 1: [First Major Step]

Clear explanation of what happens.

Example:

```bash
python scripts/fetch_data.py --project-id PROJECT_ID
```

Expected output: [describe what success looks like]

(Add more steps as needed)

## Examples

### Example 1: [common scenario]

**User says:** "Set up a new marketing campaign"

**Actions:**

1. Fetch existing campaigns via MCP
2. Create new campaign with provided parameters

**Result:** Campaign created with confirmation link

(Add more examples as needed)

## Troubleshooting

### Error: [Common error message]

**Cause:** [Why it happens]

**Solution:** [How to fix]

(Add more error cases as needed)
````

### Best Practices for Writing Skills

#### Be Specific and Actionable

✅ **Good:**

```markdown
Run `python scripts/validate.py --input {filename}` to check data format.
If validation fails, common issues include:

- Missing required fields (add them to the CSV)
- Invalid date formats (use YYYY-MM-DD)
```

❌ **Bad:**

```markdown
Validate the data before proceeding.
```

#### Include error handling

```markdown
## Common Issues

### MCP Connection Failed

If you see "Connection refused":

1. Verify MCP server is running: Check Settings > Extensions
2. Confirm API key is valid
3. Try reconnecting: Settings > Extensions > [Your Service] > Reconnect
```

#### Reference bundled resources clearly

```markdown
Before writing queries, read `references/api-patterns.md` for:

- Rate limiting guidance
- Pagination patterns
- Error codes and handling
```

#### Use progressive disclosure

Keep SKILL.md focused on core instructions. Move detailed documentation to `references/` and link to it.

### Bulletproofing Skills Against Rationalization

Skills that enforce discipline need to resist rationalization. Claude is smart and will find loopholes.

#### Use persuasive language

**Authority**

- Imperative language: "YOU MUST", "Never", "Always"
- Non-negotiable framing: "No exceptions"

**Commitment**

- Require announcements: "Announce skill usage"
- Force explicit choices: "Choose A, B, or C"
- Use tracking: TaskCreate/TaskUpdate for checklists and complex workflows

**Scarcity**

- Time-bound requirements: "Before proceeding"
- Sequential dependencies: "Immediately after X"

**Social Proof**

- Universal patterns: "Every time", "Always"
- Failure modes: "X without Y = failure"

Bright-line rules reduce rationalization. "When X, do Y" is more effective than "generally do Y."

#### Close Every Loophole Explicitly

Don't just state rules - specifically forbid workarounds:

❌ **Bad:**

```markdown
Write code before test? Delete it.
```

✅ **Good:**

```markdown
Write code before test? Delete it. Start over.

**No exceptions:**

- Don't keep it as "reference"
- Don't "adapt" it while writing tests
- Don't look at it
- Delete means delete
```

#### Build Rationalization Table

Preempt common excuses Claude could use to skip steps:

```markdown
| Excuse                       | Reality                                        |
| ---------------------------- | ---------------------------------------------- |
| "This case is simple enough" | Simple cases still benefit from the process.   |
| "I'm under time pressure"    | Rushing causes rework. Complete the process.   |
| "I already know the answer"  | Assumptions are most dangerous when confident. |

**All of these mean: Complete the process. No shortcuts.**
```

#### Create Red Flags List

Make it easy for agents to self-check when rationalizing:

```markdown
## Red Flags - STOP and Start Over

- Code before test
- "I already manually tested it"
- "Tests after achieve the same purpose"
- "It's about spirit not ritual"
- "This is different because..."

**All of these mean: Delete code. Start over with TDD.**
```

### Skill Quality Checklist

Before considering a skill complete, verify:

**Structure**
- [ ] `name` is kebab-case and matches folder name
- [ ] `description` includes WHAT + WHEN + trigger phrases
- [ ] `SKILL.md` is under 500 lines
- [ ] Supporting files are referenced, not inlined

**Instructions**
- [ ] Instructions are specific and actionable (not "validate properly")
- [ ] Critical requirements use blocking language ("MUST", "NEVER")
- [ ] Error cases are documented with solutions
- [ ] Examples show expected inputs and outputs

**For Discipline Skills**
- [ ] Phase gates require evidence before proceeding
- [ ] Rationalization table preempts common excuses
- [ ] Red flags list catches shortcut thinking

## Patterns and Troubleshooting

These patterns represent common approaches, not prescriptive templates.

### Choosing Your Approach: Problem-First vs. Tool-First

- **Problem-first:** "I need to set up a project workspace" → Your skill orchestrates the right MCP calls in the right sequence. Users describe outcomes; the skill handles the tools.
- **Tool-first:** "I have Notion MCP connected" → Your skill teaches Claude the optimal workflows and best practices. Users have access; the skill provides expertise.

Most skills lean one direction. Knowing which framing fits your use case helps you choose the right pattern below.

### Pattern 1: Sequential Workflow Orchestration

**Use when:** Your users need multi-step processes in a specific order.

**Example structure:**

```markdown
## Workflow: Onboard New Customer

### Step 1: Create Account

Call MCP tool: `create_customer`
Parameters: name, email, company

### Step 2: Setup Payment

Call MCP tool: `setup_payment_method`
Wait for: payment method verification

### Step 3: Create Subscription

Call MCP tool: `create_subscription`
Parameters: plan_id, customer_id (from Step 1)

### Step 4: Send Welcome Email

Call MCP tool: `send_email`
Template: welcome_email_template
```

**Key techniques:**

- Explicit step ordering
- Dependencies between steps
- Validation at each stage
- Rollback instructions for failures

### Pattern 2: Multi-MCP Coordination

**Use when:** Workflows span multiple services.

**Example: Design-to-development handoff**

```markdown
### Phase 1: Design Export (Figma MCP)

1. Export design assets from Figma
2. Generate design specifications
3. Create asset manifest

### Phase 2: Asset Storage (Drive MCP)

1. Create project folder in Drive
2. Upload all assets
3. Generate shareable links

### Phase 3: Task Creation (Linear MCP)

1. Create development tasks
2. Attach asset links to tasks
3. Assign to engineering team

### Phase 4: Notification (Slack MCP)

1. Post handoff summary to #engineering
2. Include asset links and task references
```

**Key techniques:**

- Clear phase separation
- Data passing between MCPs
- Validation before moving to next phase
- Centralized error handling

### Pattern 3: Iterative Refinement

**Use when:** Output quality improves with iteration.

**Example: Report generation**

```markdown
## Iterative Report Creation

### Initial Draft

1. Fetch data via MCP
2. Generate first draft report
3. Save to temporary file

### Quality Check

1. Run validation script: `scripts/check_report.py`
2. Identify issues:
   - Missing sections
   - Inconsistent formatting
   - Data validation errors

### Refinement Loop

1. Address each identified issue
2. Regenerate affected sections
3. Re-validate
4. Repeat until quality threshold met

### Finalization

1. Apply final formatting
2. Generate summary
3. Save final version
```

**Key techniques:**

- Explicit quality criteria
- Iterative improvement
- Validation scripts
- Know when to stop iterating

### Pattern 4: Context-Aware Tool Selection

**Use when:** Same outcome, different tools depending on context.

**Example: File storage**

```markdown
## Smart File Storage

### Decision Tree

1. Check file type and size
2. Determine best storage location:
   - Large files (>10MB): Use cloud storage MCP
   - Collaborative docs: Use Notion/Docs MCP
   - Code files: Use GitHub MCP
   - Temporary files: Use local storage

### Execute Storage

Based on decision:

- Call appropriate MCP tool
- Apply service-specific metadata
- Generate access link

### Provide Context to User

Explain why that storage was chosen
```

**Key techniques:**

- Clear decision criteria
- Fallback options
- Transparency about choices

### Pattern 5: Domain-Specific Intelligence

**Use when:** Your skill adds specialized knowledge beyond tool access.

**Example: Financial compliance**

```markdown
## Payment Processing with Compliance

### Before Processing (Compliance Check)

1. Fetch transaction details via MCP
2. Apply compliance rules:
   - Check sanctions lists
   - Verify jurisdiction allowances
   - Assess risk level
3. Document compliance decision

### Processing

IF compliance passed:

- Call payment processing MCP tool
- Apply appropriate fraud checks
- Process transaction
  ELSE:
- Flag for review
- Create compliance case

### Audit Trail

- Log all compliance checks
- Record processing decisions
- Generate audit report
```

**Key techniques:**

- Domain expertise embedded in logic
- Compliance before action
- Comprehensive documentation
- Clear governance

### Troubleshooting

#### Skill Doesn't Trigger

**Symptom:** Skill never loads automatically

**Fix:** Revise your description field.

**Quick checklist:**

- Is it too generic? ("Helps with projects" won't work)
- Does it include trigger phrases users would actually say?
- Does it mention relevant file types if applicable?

**Debugging approach:** Ask Claude: "When would you use the [skill name] skill?" Claude will quote the description back. Adjust based on what's missing.

#### Skill Triggers Too Often

**Symptom:** Skill loads for unrelated queries

**Solutions:**

1. **Add negative triggers**

```yaml
description: Advanced data analysis for CSV files. Use for statistical modeling, regression, clustering. Do NOT use for simple data exploration (use data-viz skill instead).
```

2. **Be more specific**

```yaml
# Too broad
description: Processes documents

# More specific
description: Processes PDF legal documents for contract review
```

3. **Clarify scope**

```yaml
description: PayFlow payment processing for e-commerce. Use specifically for online payment workflows, not for general financial queries.
```

#### MCP Connection Issues

**Symptom:** Skill loads but MCP calls fail

**Checklist:**

1. **Verify MCP server is connected**
   - Claude.ai: Settings > Extensions > [Your Service]
   - Should show "Connected" status

2. **Check authentication**
   - API keys valid and not expired
   - Proper permissions/scopes granted
   - OAuth tokens refreshed

3. **Test MCP independently**
   - Ask Claude to call MCP directly (without skill)
   - "Use [Service] MCP to fetch my projects"
   - If this fails, issue is MCP not skill

4. **Verify tool names**
   - Skill references correct MCP tool names
   - Check MCP server documentation
   - Tool names are case-sensitive

#### Instructions Not Followed

**Symptom:** Skill loads but Claude doesn't follow instructions

**Common causes:**

1. **Instructions too verbose**
   - Keep instructions concise
   - Use bullet points and numbered lists
   - Move detailed reference to separate files

2. **Instructions buried**
   - Put critical instructions at the top
   - Use `## Important` or `## Critical` headers
   - Repeat key points if needed

3. **Ambiguous language**

```markdown
# Bad

Make sure to validate things properly

# Good

CRITICAL: Before calling create_project, verify:

- Project name is non-empty
- At least one team member assigned
- Start date is not in the past
```

**Advanced technique:** For critical validations, consider bundling a script that performs the checks programmatically rather than relying on language instructions. Code is deterministic; language interpretation isn't. See the Office skills for examples of this pattern.

4. **Model "laziness"** — Add explicit encouragement:

```markdown
## Performance Notes

- Take your time to do this thoroughly
- Quality is more important than speed
- Do not skip validation steps
```

Note: Adding this to user prompts is more effective than in SKILL.md

#### Large Context Issues

**Symptom:** Skill seems slow or responses degraded

**Causes:**

- Skill content too large
- Too many skills enabled simultaneously
- All content loaded instead of progressive disclosure

**Solutions:**

1. **Optimize SKILL.md size**
   - Move detailed docs to `references/`
   - Link to references instead of inline
   - Keep SKILL.md under 5,000 words

2. **Reduce enabled skills**
   - Evaluate if you have more than 20-50 skills enabled simultaneously
   - Recommend selective enablement
   - Consider skill "packs" for related capabilities
