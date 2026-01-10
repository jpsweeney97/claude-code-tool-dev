---
id: hooks-security
topic: Hook Security Considerations
category: hooks
tags: [security, safety, best-practices, disclaimer]
requires: [hooks-overview]
related_to: [hooks-configuration, hooks-exit-codes]
official_docs: https://code.claude.com/en/hooks
---

# Hook Security Considerations

Hooks execute arbitrary shell commands. Understand the risks before configuring hooks.

## Disclaimer

**USE AT YOUR OWN RISK**: Claude Code hooks execute arbitrary shell commands on your system automatically. By using hooks, you acknowledge that:

- You are solely responsible for the commands you configure
- Hooks can modify, delete, or access any files your user account can access
- Malicious or poorly written hooks can cause data loss or system damage
- Anthropic provides no warranty and assumes no liability for any damages resulting from hook usage
- You should thoroughly test hooks in a safe environment before production use

Always review and understand any hook commands before adding them to your configuration.

## Security Best Practices

| Practice | Explanation |
|----------|-------------|
| Validate and sanitize inputs | Never trust input data blindly |
| Always quote shell variables | Use `"$VAR"` not `$VAR` |
| Block path traversal | Check for `..` in file paths |
| Use absolute paths | Specify full paths for scripts |
| Skip sensitive files | Avoid `.env`, `.git/`, keys, etc. |

## Quoting Variables

```bash
# WRONG - vulnerable to injection
if [ $TOOL_INPUT = "test" ]; then

# CORRECT - properly quoted
if [ "$TOOL_INPUT" = "test" ]; then
```

## Path Traversal Protection

```bash
#!/bin/bash
file_path=$(echo "$TOOL_INPUT" | jq -r '.file_path')

# Check for path traversal
if [[ "$file_path" == *".."* ]]; then
  echo "BLOCKED: Path traversal attempt" >&2
  exit 2
fi
```

## Configuration Safety

Claude Code protects against runtime hook modification:

1. **Snapshot at startup**: Hooks are captured when session starts
2. **Snapshot used throughout**: Same hooks apply for entire session
3. **External changes detected**: Claude Code warns if hooks modified externally
4. **Review required**: Changes only apply after review in `/hooks` menu

This prevents malicious hook modifications from affecting your current session.

## Sensitive File Protection

```bash
#!/bin/bash
file_path=$(echo "$TOOL_INPUT" | jq -r '.file_path')

# Block sensitive file access
sensitive_patterns=(".env" ".git/config" "id_rsa" ".ssh/")
for pattern in "${sensitive_patterns[@]}"; do
  if [[ "$file_path" == *"$pattern"* ]]; then
    echo "BLOCKED: Access to sensitive file" >&2
    exit 2
  fi
done
```

## Key Points

- Hooks run with your user permissions
- Always test hooks before production use
- Use `/hooks` menu to review active hooks
- Configuration changes require explicit review
- Quote all variables, validate all inputs
