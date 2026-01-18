---
id: skills-troubleshooting
topic: Skill Troubleshooting
category: skills
tags: [troubleshooting, debugging, errors, diagnostics]
requires: [skills-overview, skills-frontmatter]
related_to: [skills-invocation, skills-examples]
official_docs: https://code.claude.com/en/skills
---

# Skill Troubleshooting

Common issues and solutions when working with skills.

## View and Test Skills

Ask Claude: "What Skills are available?"

Claude loads all skill names and descriptions at startup, so it can list available skills.

To test a skill, ask Claude to do a task matching the skill's description. Claude automatically uses matching skills.

## Skill Not Triggering

The `description` field determines when Claude uses a skill. Vague descriptions don't give Claude enough context.

**Good description answers:**
1. What does this Skill do? (specific capabilities)
2. When should Claude use it? (trigger terms users would say)

```yaml
# Bad - too vague
description: Helps with documents

# Good - specific actions and keywords
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
```

## Skill Doesn't Load

### Check File Path

Skills must be in the correct directory with exact filename `SKILL.md` (case-sensitive):

| Type | Path |
|------|------|
| Personal | `~/.claude/skills/my-skill/SKILL.md` |
| Project | `.claude/skills/my-skill/SKILL.md` |
| Enterprise | See [managed settings](/en/iam#managed-settings) for platform-specific paths |
| Plugin | `skills/my-skill/SKILL.md` inside plugin directory |

### Check YAML Syntax

Invalid YAML prevents loading:
- Frontmatter must start with `---` on line 1 (no blank lines before)
- End with `---` before markdown content
- Use spaces for indentation (not tabs)

### Run Debug Mode

```bash
claude --debug
```

Shows skill loading errors in console output.

## Skill Has Errors

### Dependencies Not Installed

If your skill uses external packages, they must be installed before Claude can use them:

```bash
pip install pypdf pdfplumber
```

List required packages in your skill's description.

### Script Permissions

Scripts need execute permissions:

```bash
chmod +x scripts/*.py
```

### File Paths

Use forward slashes (Unix style) in all paths:

```markdown
# Correct
scripts/helper.py

# Wrong - will fail on non-Windows
scripts\helper.py
```

## Multiple Skills Conflict

If Claude uses the wrong skill or seems confused, descriptions are too similar.

Make each description distinct with specific trigger terms:

```yaml
# Instead of both having "data analysis"...

# Skill 1
description: Analyze sales data in Excel files and CRM exports

# Skill 2
description: Analyze log files and system metrics
```

## Plugin Skills Not Appearing

**Symptom**: Plugin installed but skills don't appear when asking "What Skills are available?"

**Solution**: Clear the plugin cache and reinstall:

```bash
rm -rf ~/.claude/plugins/cache
```

Restart Claude Code, then reinstall:

```
/plugin install plugin-name@marketplace-name
```

**If still not appearing**, verify plugin directory structure:

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json
└── skills/
    └── my-skill/
        └── SKILL.md
```

## Key Points

- Use `claude --debug` to see loading errors
- Description quality determines skill activation
- Check file paths, YAML syntax, permissions
- Clear plugin cache when skills don't appear
