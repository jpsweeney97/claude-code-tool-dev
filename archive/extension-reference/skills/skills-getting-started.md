---
id: skills-getting-started
topic: Creating Your First Skill
category: skills
tags: [tutorial, getting-started, example]
related_to: [skills-overview, skills-frontmatter, skills-examples]
official_docs: https://code.claude.com/en/skills
---

# Creating Your First Skill

This tutorial creates a personal skill that teaches Claude to explain code using visual diagrams and analogies.

## Prerequisites

- Claude Code installed and configured
- A working directory with code to explain

## Step 1: Check Available Skills

Before creating a skill, see what skills Claude already has access to:

```
What Skills are available?
```

Claude lists any currently loaded skills. You may see none, or skills from plugins or your organization.

## Step 2: Create the Skill Directory

Create a directory for the skill in your personal skills folder. Personal skills are available across all your projects.

```bash
mkdir -p ~/.claude/skills/explaining-code
```

For project-specific skills shared with your team, use `.claude/skills/` instead.

## Step 3: Write SKILL.md

Every skill needs a `SKILL.md` file. The file starts with YAML metadata between `---` markers and must include `name` and `description`, followed by markdown instructions.

The `description` is especially important because Claude uses it to decide when to apply the skill.

Create `~/.claude/skills/explaining-code/SKILL.md`:

```yaml
---
name: explaining-code
description: Explains code with visual diagrams and analogies. Use when explaining how code works, teaching about a codebase, or when the user asks "how does this work?"
---

When explaining code, always include:

1. **Start with an analogy**: Compare the code to something from everyday life
2. **Draw a diagram**: Use ASCII art to show the flow, structure, or relationships
3. **Walk through the code**: Explain step-by-step what happens
4. **Highlight a gotcha**: What's a common mistake or misconception?

Keep explanations conversational. For complex concepts, use multiple analogies.
```

## Step 4: Load and Verify

Skills are automatically loaded when created or modified. Verify the skill appears:

```
What Skills are available?
```

You should see `explaining-code` in the list with its description.

## Step 5: Test the Skill

Open any file in your project and ask Claude a question that matches the skill's description:

```
How does this code work?
```

Claude should ask to use the `explaining-code` skill, then include an analogy and ASCII diagram in its explanation.

If the skill doesn't trigger, try rephrasing to include keywords from the description like "explain how this works."

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Skill not listed | Check path: `~/.claude/skills/explaining-code/SKILL.md` |
| Skill doesn't trigger | Make description more specific with trigger keywords |
| YAML errors | Ensure frontmatter starts on line 1, uses spaces not tabs |

See [skills-troubleshooting](skills-troubleshooting.md) for detailed diagnostics.

## Next Steps

- [skills-frontmatter](skills-frontmatter.md) — Configure visibility, tools, hooks
- [skills-examples](skills-examples.md) — More complete skill patterns
- [skills-content-sections](skills-content-sections.md) — Structure complex skills

## Key Points

- Skills live in `~/.claude/skills/<name>/SKILL.md` (personal) or `.claude/skills/<name>/SKILL.md` (project)
- `name` and `description` are required frontmatter fields
- Description quality determines when Claude uses the skill
- Changes take effect immediately, no restart needed
