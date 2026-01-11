---
id: skills-content-sections
topic: Skill Content Structure
category: skills
tags: [structure, sections, procedure, verification, progressive-disclosure]
requires: [skills-overview]
related_to: [skills-examples, skills-validation]
official_docs: https://code.claude.com/en/skills
---

# Skill Content Structure

Well-structured skills include 8 mandatory sections for clarity and reliability.

## Progressive Disclosure

Skills share Claude's context window with conversation history, other skills, and your request. Use progressive disclosure to keep context focused:

- **SKILL.md**: Essential information, navigation to references
- **Supporting files**: Detailed reference material Claude reads only when needed

**Keep SKILL.md under 500 lines** for optimal performance. If content exceeds this, split detailed reference into separate files.

**Keep references one level deep.** Link directly from SKILL.md to reference files. Deeply nested references (file A → B → C) may result in Claude partially reading files.

### Zero-Context Script Execution

Scripts in your skill directory can be executed without loading their contents into context. Claude runs the script and only the output consumes tokens.

Use for:
- Complex validation logic verbose to describe in prose
- Data processing more reliable as tested code than generated code
- Operations benefiting from consistency across uses

In SKILL.md, tell Claude to run (not read) the script:
```markdown
Run the validation script to check the form:
python scripts/validate_form.py input.pdf
```

See [best practices guide](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices#progressive-disclosure-patterns) for complete structuring guidance.

## Mandatory Sections

### 1. When to Use

Clear triggering conditions:
```markdown
## When to Use
- Applying schema changes to development databases
- Running ORM-generated migrations
```

### 2. When NOT to Use

Explicit exclusions (≥3 non-goals required):
```markdown
## When NOT to Use
- Production databases (require manual approval)
- Migrations involving data loss without backup
```

### 3. Inputs

Required and optional parameters:
```markdown
## Inputs
- Migration files or ORM commands
- Target database connection (from environment)
```

### 4. Outputs

What the skill produces and how to verify success.

```markdown
## Outputs

**Artifacts:**
- Migration status report
- Schema diff summary

**Definition of Done:**
- [ ] Migration applied without errors
- [ ] Schema matches expected state
```

Outputs MUST distinguish:
- **Artifacts**: Files, patches, reports, commands the skill produces
- **Definition of Done**: Objective checks that verify success without reading the agent's mind

#### Objective Definition of Done

Good DoD criteria are observable and deterministic:

| Type | Example |
|------|---------|
| Artifact existence/shape | File exists, contains required keys |
| Deterministic query | `grep` finds/doesn't find pattern |
| Executable check | Command exits 0, output matches pattern |
| Logical condition | All X remain unchanged except Y |

#### Avoid Subjective Criteria

These are too vague to verify:

| Bad | Why |
|-----|-----|
| "Verify it works" | Works how? What's the test? |
| "Ensure quality" | Quality by what measure? |
| "Make sure tests pass" | Which tests? Where? |
| "Check for errors" | Where? What counts as error-free? |

Every DoD item should be checkable by running a command or inspecting a file.

### 5. Procedure

Step-by-step instructions:
```markdown
## Procedure
### 1. Pre-flight Checks
1. Verify database connection
2. Check current migration state
```

### 6. Decision Points

Branching logic that determines skill behavior. Every skill needs ≥2 explicit decision points.

```markdown
## Decision Points
If migration fails:
1. Rollback transaction
2. Report specific error
3. Do NOT retry automatically
```

Decision points use observable signals—things you can check programmatically:
- File/path exists or doesn't
- Command output matches pattern
- Test passes/fails
- Config contains/missing key

#### STOP Patterns

Use STOP when the skill cannot safely proceed:

**Missing required input:**
```
STOP. Ask the user for: <missing input>. Do not proceed until provided.
```

**Ambiguous request:**
```
STOP. The request is ambiguous. Ask: <clarifying question>. Proceed only after user confirms.
```

Example:
```markdown
- If no migration files found in expected paths, STOP and ask user for location
- If multiple databases match the connection pattern, STOP and ask which to target
```

#### Ask-First Patterns

Use ask-first before risky or destructive operations:

```
Ask first: This step may be breaking/destructive (<risk>). Do not proceed without explicit user approval.
```

If the user doesn't approve, skip and provide a safe alternative.

Example:
```markdown
- Before DROP or TRUNCATE operations, ask first: "This will permanently delete data. Confirm?"
- If rollback would lose uncommitted changes, ask first before proceeding
```

### 7. Verification

Objective success criteria:
```markdown
## Verification Criteria
- [ ] Migration applied without errors
- [ ] Schema matches expected state
```

### 8. Troubleshooting

Common issues and fixes:
```markdown
## Troubleshooting
**Connection refused**: Check DATABASE_URL
```

## Risk Tiering

Risk level determines minimum verification requirements.

| Tier | When to Apply | Minimum Requirements |
|------|---------------|---------------------|
| **Low** | Info/docs; trivial/reversible changes | All 8 sections; 1 quick check; 1 troubleshooting entry; 1 STOP/ask for missing inputs |
| **Medium** | Code/config changes; bounded/reversible | Low requirements + STOP/ask for ambiguity; explicit non-goals; SHOULD have 2nd verification mode |
| **High** | Security/ops/data/deps/public contracts; costly to reverse | Medium requirements + ask-first gate; ≥2 STOP/ask gates; ≥2 verification modes; rollback/escape guidance |

**Default**: If a skill has any mutating step (writes, deletes, deploys), treat as High until the procedure explicitly gates those steps.

### Examples by Tier

**Low risk** — `explaining-code` skill:
- Reads files, produces explanations
- No mutations, easily reversible (just re-run)
- Needs: basic verification that explanation was generated

**Medium risk** — `code-reviewer` skill:
- Reads code, may suggest changes
- Bounded impact (suggestions, not direct edits)
- Needs: explicit non-goals (e.g., "not for security audits"), verification of report structure

**High risk** — `database-migration` skill:
- Modifies schema, could cause data loss
- Costly to reverse, affects production
- Needs: ask-first before destructive operations, rollback instructions, multiple verification checks (schema diff + smoke tests)

## Key Points

- Include all 8 sections for completeness
- Risk level determines verification stringency
- Decision points prevent undefined behavior
- Troubleshooting reduces support burden
- See [skills-validation](skills-validation.md) for compliance checklist and quality standards
