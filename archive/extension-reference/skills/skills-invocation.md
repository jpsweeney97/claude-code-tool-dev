---
id: skills-invocation
topic: Skill Invocation Paths
category: skills
tags: [invocation, slash-menu, skill-tool, auto-discovery]
requires: [skills-overview]
related_to: [skills-frontmatter, skills-context-fork]
official_docs: https://code.claude.com/en/skills
---

# Skill Invocation Paths

Skills can be invoked through three different paths.

## Core Concept

Skills are **model-invoked**: Claude decides which skills to use based on your request. You don't need to explicitly call a skill. Claude automatically applies relevant skills when your request matches their description.

## Invocation Methods

### 1. Manual (Slash Command)

User explicitly types the skill name:

```
/skill-name
/skill-name arguments here
```

### 2. Skill Tool

Claude programmatically invokes via the Skill tool:

```typescript
Skill(skill: "skill-name", args: "optional arguments")
```

### 3. Auto-Discovery

Claude matches user's task to skill description and invokes automatically. Requires:
- Good `description` field that matches task patterns
- `disable-model-invocation: false` (default)

## Visibility Matrix

| Setting | Slash Menu | Skill Tool | Auto-discovery | Use Case |
|---------|------------|------------|----------------|----------|
| Default | Visible | Allowed | Yes | Skills you want users to invoke directly |
| `user-invocable: false` | Hidden | Allowed | Yes | Skills that Claude can use but users shouldn't invoke manually |
| `disable-model-invocation: true` | Visible | Blocked | Yes | Skills you want users to invoke but not Claude programmatically |

## Example: Model-Only Skill

Set `user-invocable: false` to hide a skill from the slash menu while allowing Claude to invoke it programmatically:

```yaml
---
name: internal-review-standards
description: Apply internal code review standards when reviewing pull requests
user-invocable: false
---
```

With this setting, users won't see the skill in the `/` menu, but Claude can still invoke it via the Skill tool or discover it automatically based on context.

## Skill Lifecycle

When you send a request, Claude follows these steps:

1. **Discovery**: At startup, loads only name + description of each skill (keeps startup fast)
2. **Activation**: When request matches a skill's description, Claude asks to use it. You see a confirmation prompt before full SKILL.md loads into context.
3. **Execution**: Claude follows the skill's instructions, loading referenced files or running bundled scripts as needed.

## Skill Tool Mechanics

- **Lazy loading**: Only name + description loaded at startup
- **Full load**: Complete SKILL.md loaded after user confirms activation
- **Character budget**: Default 15,000 chars for metadata (configurable via `SLASH_COMMAND_TOOL_CHAR_BUDGET`)

## Key Points

- Three paths: manual, Skill tool, auto-discovery
- `user-invocable: false` hides from slash menu but allows programmatic use
- `disable-model-invocation: true` shows in menu but prevents Skill tool
- Skills lazy-load for performance
