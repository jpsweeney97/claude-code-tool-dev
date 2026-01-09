---
id: skills-content-sections
topic: Skill Content Structure
category: skills
tags: [structure, sections, procedure, verification]
requires: [skills-overview]
related_to: [skills-examples]
official_docs: https://code.claude.com/en/skills
---

# Skill Content Structure

Well-structured skills include 8 mandatory sections for clarity and reliability.

## Mandatory Sections

### 1. When to Use

Clear triggering conditions:
```markdown
## When to Use
- Applying schema changes to development databases
- Running ORM-generated migrations
```

### 2. When NOT to Use

Explicit exclusions:
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

What the skill produces:
```markdown
## Outputs
- Migration status report
- Schema diff summary
```

### 5. Procedure

Step-by-step instructions:
```markdown
## Procedure
### 1. Pre-flight Checks
1. Verify database connection
2. Check current migration state
```

### 6. Decision Points

Branching logic:
```markdown
## Decision Points
If migration fails:
1. Rollback transaction
2. Report specific error
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

| Risk Level | Requirements | Examples |
|------------|--------------|----------|
| **Low** | Basic verification | Code formatting, documentation |
| **Medium** | Multiple checks, rollback plan | Refactoring, migrations |
| **High** | Mandatory confirmation, dry-run | Deployments, data changes |

## Key Points

- Include all 8 sections for completeness
- Risk level determines verification stringency
- Decision points prevent undefined behavior
- Troubleshooting reduces support burden
