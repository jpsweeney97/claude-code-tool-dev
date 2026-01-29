# Identity and Access Management

> Learn how to configure user authentication, authorization, and access controls for Claude Code in your organization.

### Configuring permissions

You can view & manage Claude Code's tool permissions with `/permissions`. This UI lists all permission rules and the settings.json file they are sourced from.

* **Allow** rules let Claude Code use the specified tool without manual approval.
* **Ask** rules prompt for confirmation whenever Claude Code tries to use the specified tool.
* **Deny** rules prevent Claude Code from using the specified tool.

Rules are evaluated in order: **deny → ask → allow**. The first matching rule wins, so deny rules always take precedence.

* **Additional directories** extend Claude's file access to directories beyond the initial working directory.
* **Default mode** controls Claude's permission behavior when encountering new requests.

Permission rules use the format: `Tool` or `Tool(optional-specifier)`

A rule that is just the tool name matches any use of that tool. For example, adding `Bash` to the allow list allows Claude Code to use the Bash tool without requiring user approval. `Bash(*)` is equivalent to `Bash` and can be used interchangeably.

<Note>
  For a quick reference on permission rule syntax including wildcards, see [Permission rule syntax](settings.md) in the settings documentation.
</Note>

#### Permission modes

Claude Code supports several permission modes that can be set as the `defaultMode` in [settings files](settings.md):

| Mode                | Description                                                                                                               |
| :------------------ | :------------------------------------------------------------------------------------------------------------------------ |
| `default`           | Standard behavior - prompts for permission on first use of each tool                                                      |
| `acceptEdits`       | Automatically accepts file edit permissions for the session                                                               |
| `plan`              | Plan Mode - Claude can analyze but not modify files or execute commands                                                   |
| `dontAsk`           | Auto-denies tools unless pre-approved via `/permissions` or [`permissions.allow`](settings.md) rules |
| `bypassPermissions` | Skips all permission prompts (requires safe environment - see warning below)                                              |

#### Working directories

By default, Claude has access to files in the directory where it was launched. You can extend this access:

* **During startup**: Use `--add-dir <path>` CLI argument
* **During session**: Use `/add-dir` command
* **Persistent configuration**: Add to `additionalDirectories` in [settings files](settings.md)

Files in additional directories follow the same permission rules as the original working directory - they become readable without prompts, and file editing permissions follow the current permission mode.

#### Tool-specific permission rules

Some tools support more fine-grained permission controls:

**Bash**

Bash permission rules support wildcard matching with `*`. Wildcards can appear at any position in the command, including at the beginning, middle, or end:

* `Bash(npm run build)` Matches the exact Bash command `npm run build`
* `Bash(npm run test *)` Matches Bash commands starting with `npm run test`
* `Bash(npm *)` Matches any command starting with `npm ` (e.g., `npm install`, `npm run build`)
* `Bash(* install)` Matches any command ending with ` install` (e.g., `npm install`, `yarn install`)
* `Bash(git * main)` Matches commands like `git checkout main`, `git merge main`
* `Bash(* --help *)` Matches any command with `--help` followed by additional arguments

When `*` appears at the end with a space before it (like `Bash(ls *)`), it enforces a word boundary, requiring the prefix to be followed by a space or end-of-string. For example, `Bash(ls *)` matches `ls -la` but not `lsof`. In contrast, `Bash(ls*)` without a space matches both `ls -la` and `lsof` because there's no word boundary constraint. The legacy `:*` suffix syntax is equivalent to ` *` but is deprecated.

<Tip>
  Claude Code is aware of shell operators (like `&&`) so a prefix match rule like `Bash(safe-cmd *)` won't give it permission to run the command `safe-cmd && other-cmd`
</Tip>

<Warning>
  Important limitations of Bash permission patterns:

  1. The space before `*` matters: `Bash(ls *)` matches `ls -la` but not `lsof`, while `Bash(ls*)` matches both
  2. The `*` wildcard can appear at any position and matches any sequence of characters
  3. Patterns like `Bash(curl http://github.com/ *)` can be bypassed in many ways:
     * Options before URL: `curl -X GET http://github.com/...` won't match
     * Different protocol: `curl https://github.com/...` won't match
     * Redirects: `curl -L http://bit.ly/xyz` (redirects to github)
     * Variables: `URL=http://github.com && curl $URL` won't match
     * Extra spaces: `curl  http://github.com` won't match

  For more reliable URL filtering, consider:

  * **Restrict Bash network tools**: Use deny rules to block `curl`, `wget`, and similar commands, then use the WebFetch tool with `WebFetch(domain:github.com)` permission for allowed domains
  * **Use PreToolUse hooks**: Implement a hook that validates URLs in Bash commands and blocks disallowed domains
  * Instructing Claude Code about your allowed curl patterns via CLAUDE.md

  Note that using WebFetch alone does not prevent network access. If Bash is allowed, Claude can still use `curl`, `wget`, or other tools to reach any URL.
</Warning>

**Read & Edit**

`Edit` rules apply to all built-in tools that edit files. Claude will make a best-effort attempt to apply `Read` rules to all built-in tools that read files like Grep and Glob.

Read & Edit rules both follow the [gitignore](https://git-scm.com/docs/gitignore) specification with four distinct pattern types:

| Pattern            | Meaning                                | Example                          | Matches                            |
| ------------------ | -------------------------------------- | -------------------------------- | ---------------------------------- |
| `//path`           | **Absolute** path from filesystem root | `Read(//Users/alice/secrets/**)` | `/Users/alice/secrets/**`          |
| `~/path`           | Path from **home** directory           | `Read(~/Documents/*.pdf)`        | `/Users/alice/Documents/*.pdf`     |
| `/path`            | Path **relative to settings file**     | `Edit(/src/**/*.ts)`             | `<settings file path>/src/**/*.ts` |
| `path` or `./path` | Path **relative to current directory** | `Read(*.env)`                    | `<cwd>/*.env`                      |

<Warning>
  A pattern like `/Users/alice/file` is NOT an absolute path - it's relative to your settings file! Use `//Users/alice/file` for absolute paths.
</Warning>

* `Edit(/docs/**)` - Edits in `<project>/docs/` (NOT `/docs/`!)
* `Read(~/.zshrc)` - Reads your home directory's `.zshrc`
* `Edit(//tmp/scratch.txt)` - Edits the absolute path `/tmp/scratch.txt`
* `Read(src/**)` - Reads from `<current-directory>/src/`

<Note>
  In gitignore patterns, `*` matches files in a single directory while `**` matches recursively across directories. To allow all file access, use just the tool name without parentheses: `Read`, `Edit`, or `Write`.
</Note>

**WebFetch**

* `WebFetch(domain:example.com)` Matches fetch requests to example.com

**MCP**

* `mcp__puppeteer` Matches any tool provided by the `puppeteer` server (name configured in Claude Code)
* `mcp__puppeteer__*` Wildcard syntax that also matches all tools from the `puppeteer` server
* `mcp__puppeteer__puppeteer_navigate` Matches the `puppeteer_navigate` tool provided by the `puppeteer` server

**Task (Subagents)**

Use `Task(AgentName)` rules to control which [subagents](subagents.md) Claude can use:

* `Task(Explore)` Matches the Explore subagent
* `Task(Plan)` Matches the Plan subagent
* `Task(Verify)` Matches the Verify subagent

Add these rules to the `deny` array in your [settings](settings.md) or use the `--disallowedTools` CLI flag to disable specific agents. For example, to disable the Explore agent:

```json  theme={null}
{
  "permissions": {
    "deny": ["Task(Explore)"]
  }
}
```

### Additional permission control with hooks

[Claude Code hooks](hooks-guide.md) provide a way to register custom shell commands to perform permission evaluation at runtime. When Claude Code makes a tool call, PreToolUse hooks run before the permission system runs, and the hook output can determine whether to approve or deny the tool call in place of the permission system.

### Managed settings

For organizations that need centralized control over Claude Code configuration, administrators can deploy `managed-settings.json` files to [system directories](settings.md). These policy files follow the same format as regular settings files and cannot be overridden by user or project settings.

### Settings precedence

When multiple settings sources exist, they are applied in the following order (highest to lowest precedence):

1. Managed settings (`managed-settings.json`)
2. Command line arguments
3. Local project settings (`.claude/settings.local.json`)
4. Shared project settings (`.claude/settings.json`)
5. User settings (`~/.claude/settings.json`)

This hierarchy ensures that organizational policies are always enforced while still allowing flexibility at the project and user levels where appropriate.

## Credential management

Claude Code securely manages your authentication credentials:

* **Storage location**: On macOS, API keys, OAuth tokens, and other credentials are stored in the encrypted macOS Keychain.
* **Supported authentication types**: Claude.ai credentials, Claude API credentials, Azure Auth, Bedrock Auth, and Vertex Auth.
* **Custom credential scripts**: The [`apiKeyHelper`](settings.md) setting can be configured to run a shell script that returns an API key.
* **Refresh intervals**: By default, `apiKeyHelper` is called after 5 minutes or on HTTP 401 response. Set `CLAUDE_CODE_API_KEY_HELPER_TTL_MS` environment variable for custom refresh intervals.
