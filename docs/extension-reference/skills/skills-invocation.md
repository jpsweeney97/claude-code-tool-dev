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

| Setting | Slash Menu | Skill Tool | Auto-discovery |
|---------|------------|------------|----------------|
| Default | ✓ | ✓ | ✓ |
| `user-invocable: false` | ✗ | ✓ | ✓ |
| `disable-model-invocation: true` | ✓ | ✗ | ✓ |

## Skill Tool Mechanics

- **Lazy loading**: Only name + description loaded at startup
- **Full load**: Complete SKILL.md loaded when skill is activated
- **Character budget**: Default 15,000 chars for metadata (configurable via `SLASH_COMMAND_TOOL_CHAR_BUDGET`)

## Key Points

- Three paths: manual, Skill tool, auto-discovery
- `user-invocable: false` hides from slash menu but allows programmatic use
- `disable-model-invocation: true` shows in menu but prevents Skill tool
- Skills lazy-load for performance
