# Agent Skills

> Create, manage, and share Skills to extend Claude's capabilities in Claude Code.

A Skill is a markdown file that teaches Claude how to do something specific: reviewing PRs using your team's standards, generating commit messages in your preferred format, or querying your company's database schema. When you ask Claude something that matches a Skill's purpose, Claude automatically applies it.

The rest of this guide covers how Skills work, configuration options, and troubleshooting.

## How Skills work

Skills are **model-invoked**: Claude decides which Skills to use based on your request. You don't need to explicitly call a Skill. Claude automatically applies relevant Skills when your request matches their description.

When you send a request, Claude follows these steps to find and use relevant Skills:

<Steps>
  <Step title="Discovery">
    At startup, Claude loads only the name and description of each available Skill. This keeps startup fast while giving Claude enough context to know when each Skill might be relevant.
  </Step>

  <Step title="Activation">
    When your request matches a Skill's description, Claude asks to use the Skill. You'll see a confirmation prompt before the full `SKILL.md` is loaded into context. Since Claude reads these descriptions to find relevant Skills, [write descriptions](#skill-not-triggering) that include keywords users would naturally say.
  </Step>

  <Step title="Execution">
    Claude follows the Skill's instructions, loading referenced files or running bundled scripts as needed.
  </Step>
</Steps>

## Configure Skills

This section covers Skill file structure, supporting files, tool restrictions, and distribution options.

### Write SKILL.md

The `SKILL.md` file is the only required file in a Skill. It has two parts: YAML metadata (the section between `---` markers) at the top, and Markdown instructions that tell Claude how to use the Skill:

```yaml
---
name: your-skill-name
description: Brief description of what this Skill does and when to use it
---

# Your Skill Name

## Instructions
Provide clear, step-by-step guidance for Claude.

## Examples
Show concrete examples of using this Skill.
```

#### Available metadata fields

You can use the following fields in the YAML frontmatter:

| Field            | Required | Description                                                                                                                                                                                                                                                    |
| :--------------- | :------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`           | Yes      | Skill name. Must use lowercase letters, numbers, and hyphens only (max 64 characters). Should match the directory name.                                                                                                                                        |
| `description`    | Yes      | What the Skill does and when to use it (max 1024 characters). Claude uses this to decide when to apply the Skill.                                                                                                                                              |
| `allowed-tools`  | No       | Tools Claude can use without asking permission when this Skill is active. Supports comma-separated values or YAML-style lists.                                                                                                                                 |
| `model`          | No       | [Model] to use when this Skill is active (e.g., `claude-sonnet-4-20250514`). Defaults to the conversation's model.                                                                                                                                             |
| `context`        | No       | Set to `fork` to run the Skill in a forked sub-agent context with its own conversation history.                                                                                                                                                                |
| `agent`          | No       | Specify which [agent type] to use when `context: fork` is set (e.g., `Explore`, `Plan`, `general-purpose`, or a custom agent name from `.claude/agents/`). Defaults to `general-purpose` if not specified. Only applicable when combined with `context: fork`. |
| `hooks`          | No       | Define hooks scoped to this Skill's lifecycle. Supports `PreToolUse`, `PostToolUse`, and `Stop` events.                                                                                                                                                        |
| `user-invocable` | No       | Controls whether the Skill appears in the slash command menu. Does not affect the [`Skill` tool] or automatic discovery. Defaults to `true`. See [Control Skill visibility](#control-skill-visibility).                                                        |

#### Available string substitutions

Skills support string substitution for dynamic values in the Skill content:

| Variable               | Description                                                                                                                                  |
| :--------------------- | :------------------------------------------------------------------------------------------------------------------------------------------- |
| `$ARGUMENTS`           | All arguments passed when invoking the Skill. If `$ARGUMENTS` is not present in the content, arguments are appended as `ARGUMENTS: <value>`. |
| `${CLAUDE_SESSION_ID}` | The current session ID. Useful for logging, creating session-specific files, or correlating Skill output with sessions.                      |

**Example using substitutions:**

```yaml
---
name: session-logger
description: Log activity for this session
---

Log the following to logs/${CLAUDE_SESSION_ID}.log:

$ARGUMENTS
```

### Update or delete a Skill

To update a Skill, edit its `SKILL.md` file directly. To remove a Skill, delete its directory. Changes take effect immediately.

### Add supporting files with progressive disclosure

Skills share Claude's context window with conversation history, other Skills, and your request. To keep context focused, use **progressive disclosure**: put essential information in `SKILL.md` and detailed reference material in separate files that Claude reads only when needed.

This approach lets you bundle comprehensive documentation, examples, and scripts without consuming context upfront. Claude loads additional files only when the task requires them.

<Tip>Keep `SKILL.md` under 500 lines for optimal performance. If your content exceeds this, split detailed reference material into separate files.</Tip>

#### Example: multi-file Skill structure

Claude discovers supporting files through links in your `SKILL.md`. The following example shows a Skill with detailed documentation in separate files and utility scripts that Claude can execute without reading:

```
my-skill/
├── SKILL.md (required - overview and navigation)
├── reference.md (detailed API docs - loaded when needed)
├── examples.md (usage examples - loaded when needed)
└── scripts/
    └── helper.py (utility script - executed, not loaded)
```

The `SKILL.md` file references these supporting files so Claude knows they exist:

````markdown
## Overview

[Essential instructions here]

## Additional resources

- For complete API details, see [reference.md](reference.md)
- For usage examples, see [examples.md](examples.md)

## Utility scripts

To validate input files, run the helper script. It checks for required fields and returns any validation errors:

```bash
python scripts/helper.py input.txt
```
````

<Tip>Keep references one level deep. Link directly from `SKILL.md` to reference files. Deeply nested references (file A links to file B which links to file C) may result in Claude partially reading files.</Tip>

**Bundle utility scripts for zero-context execution.** Scripts in your Skill directory can be executed without loading their contents into context. Claude runs the script and only the output consumes tokens. This is useful for:

- Complex validation logic that would be verbose to describe in prose
- Data processing that's more reliable as tested code than generated code
- Operations that benefit from consistency across uses

In `SKILL.md`, tell Claude to run the script rather than read it:

```markdown
Run the validation script to check the form:
python scripts/validate_form.py input.pdf
```

### Restrict tool access with allowed-tools

Use the `allowed-tools` frontmatter field to limit which tools Claude can use when a Skill is active. You can specify tools as a comma-separated string or a YAML list:

```yaml
---
name: reading-files-safely
description: Read files without making changes. Use when you need read-only file access.
allowed-tools: Read, Grep, Glob
---
```

Or use YAML-style lists for better readability:

```yaml
---
name: reading-files-safely
description: Read files without making changes. Use when you need read-only file access.
allowed-tools:
  - Read
  - Grep
  - Glob
---
```

When this Skill is active, Claude can only use the specified tools (Read, Grep, Glob) without needing to ask for permission. This is useful for:

- Read-only Skills that shouldn't modify files
- Skills with limited scope: for example, only data analysis, no file writing
- Security-sensitive workflows where you want to restrict capabilities

If `allowed-tools` is omitted, the Skill doesn't restrict tools. Claude uses its standard permission model and may ask you to approve tool usage.

### Run Skills in a forked context

Use `context: fork` to run a Skill in an isolated sub-agent context with its own conversation history. This is useful for Skills that perform complex multi-step operations without cluttering the main conversation:

```yaml
---
name: code-analysis
description: Analyze code quality and generate detailed reports
context: fork
---
```

### Define hooks for Skills

Skills can define hooks that run during the Skill's lifecycle. Use the `hooks` field to specify `PreToolUse`, `PostToolUse`, or `Stop` handlers:

```yaml
---
name: secure-operations
description: Perform operations with additional security checks
hooks:
  PreToolUse:
    - matcher: 'Bash'
      hooks:
        - type: command
          command: './scripts/security-check.sh $TOOL_INPUT'
          once: true
---
```

The `once: true` option runs the hook only once per session. After the first successful execution, the hook is removed.

Hooks defined in a Skill are scoped to that Skill's execution and are automatically cleaned up when the Skill finishes.

### Control Skill visibility

Skills can be invoked in three ways:

1. **Manual invocation**: You type `/skill-name` in the prompt
2. **Programmatic invocation**: Claude calls it via the [`Skill` tool]
3. **Automatic discovery**: Claude reads the Skill's description and loads it when relevant to the conversation

The `user-invocable` field controls only manual invocation. When set to `false`, the Skill is hidden from the slash command menu but Claude can still invoke it programmatically or discover it automatically.

To block programmatic invocation via the `Skill` tool, use `disable-model-invocation: true` instead.

#### When to use each setting

| Setting                          | Slash menu | `Skill` tool | Auto-discovery | Use case                                                        |
| :------------------------------- | :--------- | :----------- | :------------- | :-------------------------------------------------------------- |
| `user-invocable: true` (default) | Visible    | Allowed      | Yes            | Skills you want users to invoke directly                        |
| `user-invocable: false`          | Hidden     | Allowed      | Yes            | Skills that Claude can use but users shouldn't invoke manually  |
| `disable-model-invocation: true` | Visible    | Blocked      | Yes            | Skills you want users to invoke but not Claude programmatically |

#### Example: model-only Skill

Set `user-invocable: false` to hide a Skill from the slash menu while still allowing Claude to invoke it programmatically:

```yaml
---
name: internal-review-standards
description: Apply internal code review standards when reviewing pull requests
user-invocable: false
---
```

With this setting, users won't see the Skill in the `/` menu, but Claude can still invoke it via the `Skill` tool or discover it automatically based on context.

### Skills and subagents

There are two ways Skills and subagents can work together:

#### Give a subagent access to Skills

Subagents do not automatically inherit Skills from the main conversation. To give a custom subagent access to specific Skills, list them in the subagent's `skills` field:

```yaml
# .claude/agents/code-reviewer.md
---
name: code-reviewer
description: Review code for quality and best practices
skills: pr-review, security-check
---
```

The full content of each listed Skill is injected into the subagent's context at startup, not just made available for invocation. If the `skills` field is omitted, no Skills are loaded for that subagent.

<Note>
  Built-in agents (Explore, Plan, general-purpose) do not have access to your Skills. Only custom subagents you define in `.claude/agents/` with an explicit `skills` field can use Skills.
</Note>

#### Run a Skill in a subagent context

Use `context: fork` and `agent` to run a Skill in a forked subagent with its own separate context. See [Run Skills in a forked context](#run-skills-in-a-forked-context) for details.

### Distribute Skills

You can share Skills in several ways:

- **Project Skills**: Commit `.claude/skills/` to version control. Anyone who clones the repository gets the Skills.
- **Plugins**: To share Skills across multiple repositories, create a `skills/` directory in your [plugin](/en/plugins) with Skill folders containing `SKILL.md` files. Distribute through a [plugin marketplace](/en/plugin-marketplaces).
- **Managed**: Administrators can deploy Skills organization-wide through [managed settings](/en/iam#managed-settings). See [Where Skills live](#where-skills-live) for managed Skill paths.

## Examples

These examples show common Skill patterns, from minimal single-file Skills to multi-file Skills with supporting documentation and scripts.

### Simple Skill (single file)

A minimal Skill needs only a `SKILL.md` file with frontmatter and instructions. This example helps Claude generate commit messages by examining staged changes:

```
commit-helper/
└── SKILL.md
```

```yaml
---
name: generating-commit-messages
description: Generates clear commit messages from git diffs. Use when writing commit messages or reviewing staged changes.
---

# Generating Commit Messages

## Instructions

1. Run `git diff --staged` to see changes
2. I'll suggest a commit message with:
   - Summary under 50 characters
   - Detailed description
   - Affected components

## Best practices

- Use present tense
- Explain what and why, not how
```

### Use multiple files

For complex Skills, use progressive disclosure to keep the main `SKILL.md` focused while providing detailed documentation in supporting files. This PDF processing Skill includes reference docs, utility scripts, and uses `allowed-tools` to restrict Claude to specific tools:

```
pdf-processing/
├── SKILL.md              # Overview and quick start
├── FORMS.md              # Form field mappings and filling instructions
├── REFERENCE.md          # API details for pypdf and pdfplumber
└── scripts/
    ├── fill_form.py      # Utility to populate form fields
    └── validate.py       # Checks PDFs for required fields
```

**`SKILL.md`**:

````yaml
---
name: pdf-processing
description: Extract text, fill forms, merge PDFs. Use when working with PDF files, forms, or document extraction. Requires pypdf and pdfplumber packages.
allowed-tools: Read, Bash(python:*)
---

# PDF Processing

## Quick start

Extract text:
```python
import pdfplumber
with pdfplumber.open("doc.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```

For form filling, see [FORMS.md](FORMS.md).
For detailed API reference, see [REFERENCE.md](REFERENCE.md).

## Requirements

Packages must be installed in your environment:
```bash
pip install pypdf pdfplumber
```
````

<Note>
  If your Skill requires external packages, list them in the description. Packages must be installed in your environment before Claude can use them.
</Note>

## Troubleshooting

### View and test Skills

To see which Skills Claude has access to, ask Claude a question like "What Skills are available?" Claude loads all available Skill names and descriptions into the context window when a conversation starts, so it can list the Skills it currently has access to.

To test a specific Skill, ask Claude to do a task that matches the Skill's description. For example, if your Skill has the description "Reviews pull requests for code quality", ask Claude to "Review the changes in my current branch." Claude automatically uses the Skill when the request matches its description.

### Skill not triggering

The description field is how Claude decides whether to use your Skill. Vague descriptions like "Helps with documents" don't give Claude enough information to match your Skill to relevant requests.

A good description answers two questions:

1. **What does this Skill do?** List the specific capabilities.
2. **When should Claude use it?** Include trigger terms users would mention.

```yaml
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
```

This description works because it names specific actions (extract, fill, merge) and includes keywords users would say (PDF, forms, document extraction).

### Skill doesn't load

**Check the file path.** Skills must be in the correct directory with the exact filename `SKILL.md` (case-sensitive):

| Type       | Path                                                                    |
| :--------- | :---------------------------------------------------------------------- |
| Personal   | `~/.claude/skills/my-skill/SKILL.md`                                    |
| Project    | `.claude/skills/my-skill/SKILL.md`                                      |
| Enterprise | See [Where Skills live](#where-skills-live) for platform-specific paths |
| Plugin     | `skills/my-skill/SKILL.md` inside the plugin directory                  |

**Check the YAML syntax.** Invalid YAML in the frontmatter prevents the Skill from loading. The frontmatter must start with `---` on line 1 (no blank lines before it), end with `---` before the Markdown content, and use spaces for indentation (not tabs).

**Run debug mode.** Use `claude --debug` to see Skill loading errors.

### Skill has errors

**Check dependencies are installed.** If your Skill uses external packages, they must be installed in your environment before Claude can use them.

**Check script permissions.** Scripts need execute permissions: `chmod +x scripts/*.py`

**Check file paths.** Use forward slashes (Unix style) in all paths. Use `scripts/helper.py`, not `scripts\helper.py`.

### Multiple Skills conflict

If Claude uses the wrong Skill or seems confused between similar Skills, the descriptions are probably too similar. Make each description distinct by using specific trigger terms.

For example, instead of two Skills with "data analysis" in both descriptions, differentiate them: one for "sales data in Excel files and CRM exports" and another for "log files and system metrics". The more specific your trigger terms, the easier it is for Claude to match the right Skill to your request.
