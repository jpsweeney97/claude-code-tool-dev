# Rule Reference

Comprehensive reference for all plugin audit validation rules. Each rule includes its ID, severity, what it checks, evidence from official documentation, and how to fix violations.

---

## Severity Levels

| Level | Meaning | Action Required |
|-------|---------|-----------------|
| **CRITICAL** | Plugin will not load or function correctly | Must fix before plugin can work |
| **WARNING** | Plugin works but has quality/reliability issues | Should fix for production use |
| **INFO** | Suggestions for improvement | Consider for better user experience |

---

## Structure Rules (S)

Rules for plugin manifest and overall structure.

### S-MANIFEST-001: Valid plugin.json
- **Severity:** CRITICAL
- **Checks:** Plugin manifest exists and contains valid JSON
- **Evidence:** Plugin manifest is required for Claude Code to recognize the plugin
- **Fix:** Create `.claude-plugin/plugin.json` with valid JSON structure

### S-NAME-001: Plugin name required
- **Severity:** CRITICAL
- **Checks:** `name` field exists in plugin manifest
- **Evidence:** Plugin name is required for identification and logging
- **Fix:** Add `"name": "your-plugin-name"` to plugin.json

### S-NAME-002: Plugin name kebab-case
- **Severity:** WARNING
- **Checks:** Plugin name uses lowercase kebab-case format
- **Pattern:** `^[a-z][a-z0-9]*(-[a-z0-9]+)*$`
- **Evidence:** Kebab-case ensures consistent naming across plugins
- **Fix:** Rename to use lowercase letters, numbers, and hyphens only (e.g., `my-plugin-name`)

### S-VERSION-001: Version field recommended
- **Severity:** INFO
- **Checks:** `version` field exists in plugin manifest
- **Evidence:** Version tracking enables update management
- **Fix:** Add `"version": "1.0.0"` using semantic versioning

---

## Command Rules (C)

Rules for slash commands (`commands/*.md`).

### C-NAME-001: Command name optional
- **Severity:** INFO
- **Checks:** Notes that `name` field in frontmatter is optional
- **Evidence:**
  > "Command name is derived from the filename"
  > *Source: Claude Code Documentation*
- **Derivation:** Documentation explicitly states command names come from filenames. The `name` field in frontmatter is optional and used for display/override only. Flagging missing `name` as error is a FALSE POSITIVE.
- **Fix:** No action needed. If you want a custom display name, add `name:` to frontmatter.

### C-DESC-001: Description recommended
- **Severity:** WARNING
- **Checks:** `description` field exists in command frontmatter
- **Evidence:**
  > "Description is shown in /help output"
  > *Source: Claude Code Documentation*
- **Validation:** 10-200 characters
- **Fix:** Add `description:` field explaining what the command does

### C-TOOLS-001: Allowed tools recommended
- **Severity:** WARNING
- **Checks:** `allowed-tools` field restricts command capabilities
- **Evidence:** Principle of least privilege suggests specifying tools
- **Derivation:** Commands work without this field (full tool access), but explicit restrictions improve security
- **Fix:** Add `allowed-tools: [Read, Write, ...]` listing only needed tools

### C-ARGS-001: Argument hint for $ARGUMENTS
- **Severity:** WARNING (conditional)
- **Checks:** If command body contains `$ARGUMENTS`, `argument-hint` should be present
- **Evidence:**
  > "Shows in /help as usage hint"
  > *Source: Claude Code Documentation*
- **Fix:** Add `argument-hint: "<description of arguments>"` to frontmatter

### C-BODY-001: Instructions written for Claude
- **Severity:** WARNING
- **Checks:** Command body is instructions TO Claude, not documentation ABOUT the command
- **Evidence:** Commands are prompts that Claude executes
- **Detection patterns:**
  - `This command (?:helps|allows|enables)`
  - `Users can`
  - `The user should`
- **Context exemptions:** Within example blocks, within comments
- **Fix:** Rewrite body as direct instructions using imperative form

---

## Skill Rules (SK)

Rules for skills (`skills/*/SKILL.md`).

### SK-NAME-001: Skill name required
- **Severity:** CRITICAL
- **Checks:** `name` field exists in skill frontmatter
- **Evidence:**
  > "Skills require name for identification and logging"
  > *Source: Claude Code Documentation*
- **Derivation:** Unlike commands, skill names are NOT derived from directory. The name field is REQUIRED for skill registration.
- **Validation:** 3-100 characters
- **Fix:** Add `name: "Your Skill Name"` to frontmatter

### SK-DESC-001: Skill description required
- **Severity:** CRITICAL
- **Checks:** `description` field exists in skill frontmatter
- **Evidence:**
  > "Description determines when Claude loads the skill"
  > *Source: Claude Code Documentation*
- **Derivation:** Description is the TRIGGERING MECHANISM for skills. Without it, Claude cannot know when to load the skill.
- **Validation:** 50-1000 characters, should contain trigger phrases
- **Fix:** Add comprehensive `description:` with trigger phrases

### SK-DESC-002: Description has trigger phrases
- **Severity:** WARNING
- **Checks:** Description contains specific quoted trigger phrases
- **Evidence:**
  > "Specific trigger phrases ensure skill loads at right time"
  > *Source: Claude Code triggering mechanism*
- **Detection:** Should contain at least one quoted string pattern: `"[^"]{3,}"`
- **Fix:** Add quoted trigger phrases like: `Use when user asks "create a widget" or "make a new component"`

### SK-DESC-003: Description uses third-person
- **Severity:** WARNING
- **Checks:** Description avoids second-person ("you") language
- **Evidence:** Third-person descriptions work better with Claude's skill loading mechanism
- **Fix:** Rewrite "You should use this when..." as "Use when..."

### SK-BODY-001: Body uses imperative form
- **Severity:** WARNING
- **Checks:** Skill body avoids "you should/need to/can/must" phrasing
- **Evidence:**
  > "Imperative form is clearer for AI consumption"
  > *Source: Claude Code style conventions*
- **Detection patterns:**
  - `\bYou should\b`
  - `\bYou need to\b`
  - `\bYou can\b`
  - `\bYou must\b`
  - `\bClaude should\b`
- **Context exemptions:** Within `<example>` blocks, within quoted user messages
- **Fix:** Rewrite "You should check the file" as "Check the file"

### SK-BODY-002: Body word count limit
- **Severity:** WARNING
- **Checks:** SKILL.md does not exceed 3000 words
- **Evidence:**
  > "Overly long skills bloat context"
  > *Source: Best practice for context efficiency*
- **Recommended:** 1500 words or less
- **Maximum:** 3000 words
- **Fix:** Move detailed content to `references/` subdirectory and link from SKILL.md

---

## Agent Rules (A)

Rules for subagents (`agents/*.md`).

### A-DESC-001: Agent description required
- **Severity:** CRITICAL
- **Checks:** `description` field exists in agent frontmatter
- **Evidence:**
  > "Description is used by Claude to decide when to invoke the agent via Task tool"
  > *Source: Claude Code Documentation*
- **Derivation:** Without description, Claude cannot know when to dispatch the agent
- **Validation:** 20-500 characters
- **Fix:** Add `description:` explaining when to use this agent

### A-TOOLS-001: Agent tools required
- **Severity:** CRITICAL
- **Checks:** `tools` field exists and contains at least one tool
- **Evidence:**
  > "Agents require tools list for execution"
  > *Source: Claude Code Documentation*
- **Derivation:** Agents need explicit tool permissions. Unlike commands, there is no default tool access for agents.
- **Valid values:** Read, Write, Edit, Glob, Grep, Bash, WebFetch, WebSearch, AskUserQuestion, TodoWrite, Task, NotebookEdit, Skill
- **Fix:** Add `tools: [Read, Write, ...]` with needed tools

### A-MODEL-001: Model value valid
- **Severity:** INFO
- **Checks:** If `model` field is present, it has a valid value
- **Valid values:** sonnet, opus, haiku
- **Fix:** Use one of the valid model identifiers

### A-BODY-001: Has example blocks
- **Severity:** WARNING
- **Checks:** Agent body contains `<example>` blocks showing trigger scenarios
- **Evidence:**
  > "Examples help Claude understand exactly when to use the agent"
  > *Source: Claude Code best practices*
- **Fix:** Add example blocks showing when the agent should be invoked:
  ```markdown
  <example>
  User: "I need to refactor the authentication module"
  Action: Invoke this agent for refactoring tasks
  </example>
  ```

### A-BODY-002: Substantive system prompt
- **Severity:** WARNING
- **Checks:** Agent body provides meaningful guidance (minimum 50 words)
- **Evidence:**
  > "The body becomes the agent's system prompt"
  > *Source: Agent design best practices*
- **Fix:** Expand the agent body with clear instructions, constraints, and examples

---

## Hook Rules (H)

Rules for hooks (`hooks/hooks.json`).

### H-EVENT-001: Valid hook events
- **Severity:** CRITICAL
- **Checks:** Hook event names are valid Claude Code events
- **Evidence:**
  > "Valid hook event names"
  > *Source: Claude Code Documentation*
  > Note: Any other event name is silently ignored
- **Valid events:**
  - PreToolUse
  - PostToolUse
  - Stop
  - SubagentStop
  - SessionStart
  - SessionEnd
  - UserPromptSubmit
  - PreCompact
  - Notification
- **Fix:** Use only valid event names from the list above

### H-FIELD-001: Matcher required
- **Severity:** CRITICAL
- **Checks:** Hook has `matcher` field with valid regex pattern
- **Validation:** Regex must compile successfully
- **Fix:** Add `"matcher": "^pattern$"` with valid regex

### H-FIELD-002: Type required
- **Severity:** CRITICAL
- **Checks:** Hook has `type` field
- **Valid values:** command, prompt
- **Fix:** Add `"type": "command"` or `"type": "prompt"`

### H-FIELD-003: Command required for type=command
- **Severity:** CRITICAL (conditional)
- **Checks:** If `type` is "command", `command` field must exist
- **Validation:** Must use `$CLAUDE_PLUGIN_ROOT` for plugin paths
- **Fix:** Add `"command": "$CLAUDE_PLUGIN_ROOT/hooks/your-script.sh"`

### H-FIELD-004: Prompt required for type=prompt
- **Severity:** CRITICAL (conditional)
- **Checks:** If `type` is "prompt", `prompt` field must exist
- **Validation:** Must use `$CLAUDE_PLUGIN_ROOT` for plugin paths
- **Fix:** Add `"prompt": "Your prompt text here"`

### H-TIMEOUT-001: Timeout recommended
- **Severity:** WARNING
- **Checks:** Hook has explicit `timeout` field
- **Evidence:**
  > "Default timeout is 30 seconds"
  > *Source: Claude Code Documentation*
- **Derivation:** Explicit timeout improves reliability and documentation
- **Validation:** 1000-600000ms, recommended 5000-60000ms
- **Fix:** Add `"timeout": 10000` (in milliseconds)

### H-PATH-001: Script paths portable
- **Severity:** WARNING
- **Checks:** Hook command paths use `$CLAUDE_PLUGIN_ROOT`
- **Evidence:** Hardcoded absolute paths break portability
- **Fix:** Replace `/Users/you/plugin/hooks/script.sh` with `$CLAUDE_PLUGIN_ROOT/hooks/script.sh`

---

## MCP Rules (M)

Rules for MCP servers (`.mcp.json`).

### M-FIELD-001: Command required
- **Severity:** CRITICAL
- **Checks:** MCP server has `command` field
- **Evidence:**
  > "Command is required to start the MCP server process"
  > *Source: Claude Code Documentation*
- **Validation:** Command must be accessible/executable
- **Fix:** Add `"command": "node"` or appropriate command

### M-FIELD-002: Args use plugin root
- **Severity:** INFO
- **Checks:** Arguments referencing plugin files use `$CLAUDE_PLUGIN_ROOT`
- **Fix:** Replace hardcoded paths with `$CLAUDE_PLUGIN_ROOT/path/to/file`

### M-FIELD-003: Secrets use substitution
- **Severity:** WARNING
- **Checks:** Environment variables for secrets use `${VAR}` syntax
- **Evidence:** Hardcoded secrets are security risks
- **Fix:** Use `"API_KEY": "${MY_API_KEY}"` instead of literal values

---

## Security Rules (SEC)

Rules for security and credential handling.

### SEC-PATH-001: No hardcoded absolute paths
- **Severity:** CRITICAL
- **Checks:** All paths to plugin files use `$CLAUDE_PLUGIN_ROOT`
- **Evidence:**
  > "Use $CLAUDE_PLUGIN_ROOT for portable plugin paths"
  > *Source: Claude Code Documentation*
- **Detection patterns:**
  - `/Users/`
  - `/home/`
  - `C:\\`
  - `/var/`
  - `/etc/`
- **Files checked:** `*.json`, `*.md`
- **Context exemptions:**
  - Anti-pattern examples (Bad:, DON'T:, etc.)
  - Marked example blocks
  - Security deny blocks (see SEC-EXEMPT-001)
- **Fix:** Replace absolute paths with `$CLAUDE_PLUGIN_ROOT/relative/path`

### SEC-PATH-002: No tilde paths in JSON
- **Severity:** CRITICAL
- **Checks:** JSON files don't use `~/` paths
- **Evidence:**
  > "Tilde expansion is shell-specific"
  > *Source: Shell/JSON behavior*
- **Detection:** `~/` pattern in `*.json` files
- **Fix:** Use `$HOME` environment variable or `$CLAUDE_PLUGIN_ROOT`

### SEC-CRED-001: No hardcoded credentials
- **Severity:** CRITICAL
- **Checks:** No API keys, tokens, or passwords in code
- **Evidence:**
  > "Credentials in code are exposed to anyone with access"
  > *Source: Security best practices*
- **Detection patterns:**
  - `(api[_-]?key|apikey)\s*[:=]\s*["'][^"']{10,}["']`
  - `(token|secret|password|passwd|pwd)\s*[:=]\s*["'][^"']+["']`
  - `AKIA[0-9A-Z]{16}` (AWS access key)
  - `sk-[a-zA-Z0-9]{20,}` (OpenAI-style keys)
- **Files checked:** `*.json`, `*.md`, `*.sh`, `*.py`
- **Context exemptions:**
  - Environment variable substitution `${VAR}`
  - Placeholder tokens `<YOUR_*_HERE>`
  - Intentional placeholders (xxx, REDACTED, placeholder)
- **Fix:** Use environment variables: `"apiKey": "${MY_API_KEY}"`

### SEC-CMD-001: Dangerous commands have safeguards
- **Severity:** WARNING
- **Checks:** Destructive commands have conditional guards or warnings
- **Evidence:** Destructive operations need validation
- **Detection patterns:**
  - `rm\s+-rf?`
  - `DROP\s+(TABLE|DATABASE)`
  - `DELETE\s+FROM.*WHERE`
  - `TRUNCATE`
  - `chmod\s+777`
  - `\bsudo\b`
- **Context exemptions:**
  - Has conditional guard (`if [`, `${...}/`)
  - Has explicit warning comment (`# DANGER`, `# WARNING`, `# CAUTION`)
  - Within sandbox deny configuration
- **Fix:** Add conditional checks and/or warning comments before dangerous operations

### SEC-ENV-001: Sensitive env vars use substitution
- **Severity:** WARNING
- **Checks:** Environment variables for secrets use `${VAR}` syntax
- **Evidence:**
  > "Use ${VAR} for runtime configuration"
  > *Source: Claude Code Documentation*
- **Detection:** Keys containing `key`, `secret`, `token`, `password`, `credential`
- **Fix:** Use `"value": "${ENV_VAR_NAME}"` for sensitive values

#### Security Exemptions

##### SEC-EXEMPT-001: Deny blocks are security features
- **Applies to:** SEC-PATH-001, SEC-PATH-002
- **Description:** Paths appearing in security deny blocks (e.g., `permissionDecision: deny`) are not vulnerabilities - they are security controls.
- **See also:** [context-patterns.md](./context-patterns.md) for detection patterns

---

## Cross-Component Rules (X)

Rules that span multiple component types.

### X-FILE-001: Referenced files exist
- **Severity:** WARNING
- **Checks:** Files referenced in configuration/documentation exist
- **Examples:**
  - Script paths in hooks.json
  - Reference files in SKILL.md
  - Include paths in commands
- **Fix:** Create missing files or correct the path

### X-DOC-001: Components documented
- **Severity:** INFO
- **Checks:** Plugin has README or documentation explaining components
- **Evidence:** Documentation improves discoverability and maintenance
- **Fix:** Add README.md or expand existing documentation

---

## Rule ID Format

Rules follow this naming convention:

```
{PREFIX}-{CATEGORY}-{NUM}
```

| Prefix | Component |
|--------|-----------|
| S | Structure (manifest, directories) |
| C | Command |
| SK | Skill |
| A | Agent |
| H | Hook |
| M | MCP |
| SEC | Security |
| X | Cross-cutting |

| Category | Purpose |
|----------|---------|
| NAME | Naming rules |
| DESC | Description rules |
| BODY | Content/body rules |
| FIELD | Required/optional field rules |
| PATH | Path handling rules |
| CRED | Credential rules |
| CMD | Command safety rules |
| ENV | Environment variable rules |
| FILE | File reference rules |
| DOC | Documentation rules |
| EVENT | Event name rules |
| MANIFEST | Manifest rules |
| TIMEOUT | Timeout rules |
| EXEMPT | Exemption rules |

**Note on audit-spec.yaml mapping:** The specification file uses sequential field numbering (e.g., `H-FIELD-005` for timeout) while this reference uses descriptive IDs (e.g., `H-TIMEOUT-001`). Both refer to the same underlying rule.

---

## See Also

- [context-patterns.md](./context-patterns.md) - How to detect false positives through context analysis
- [audit-spec.yaml](../specification/audit-spec.yaml) - Machine-readable specification
