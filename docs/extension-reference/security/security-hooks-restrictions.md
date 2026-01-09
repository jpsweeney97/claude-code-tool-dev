---
id: security-hooks-restrictions
topic: Hook Restrictions
category: security
tags: [hooks, restrictions, managed, disable]
requires: [security-managed]
related_to: [hooks-overview]
official_docs: https://code.claude.com/en/iam
---

# Hook Restrictions

Control which hooks can run.

## allowManagedHooksOnly

In `managed-settings.json`:

```json
{
  "allowManagedHooksOnly": true
}
```

When enabled:
- Managed hooks run
- SDK hooks run
- User hooks blocked
- Project hooks blocked
- Plugin hooks blocked

## disableAllHooks

Completely disable hooks:

```json
{
  "disableAllHooks": true
}
```

All hooks are blocked, including managed hooks.

## Comparison

| Setting | Managed | SDK | User/Project/Plugin |
|---------|---------|-----|---------------------|
| Default | ✓ | ✓ | ✓ |
| `allowManagedHooksOnly: true` | ✓ | ✓ | ✗ |
| `disableAllHooks: true` | ✗ | ✗ | ✗ |

## Disable Bypass Mode

Prevent users from bypassing permissions:

```json
{
  "permissions": {
    "disableBypassPermissionsMode": "disable"
  }
}
```

Prevents `--dangerously-skip-permissions` flag.

## Key Points

- allowManagedHooksOnly: only IT-deployed hooks
- disableAllHooks: no hooks at all
- disableBypassPermissionsMode: block permission bypass
- Use for security-sensitive environments
