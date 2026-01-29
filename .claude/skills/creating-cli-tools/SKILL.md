---
name: creating-cli-tools
description: "Use when asked to create a CLI tool, command-line script, terminal utility, or when user invokes the skill directly."
---

# Creating CLI Tools

## Overview

Turn vague CLI tool ideas into working, production-quality command-line utilities through collaborative dialogue. Follows the brainstorming methodology (one question at a time, converge on design) before generating code.

**Outputs:**
- Working CLI tool at `/Users/jp/dotfiles/bin/.local/bin/<tool-name>` (simple) or `/Users/jp/Projects/tools/<tool-name>/` (complex)
- Installed and runnable by name alone

**Definition of Done:**
- Requirements understood through dialogue
- Understanding converged (two consecutive question rounds that yield nothing new)
- CLI interface designed (commands, options, arguments)
- Tool generated following Python conventions (type hints, Ruff, Google docstrings)
- Tool installed and executable by name
- User prompted to test

## The Process

**Understanding the idea:**

- **YOU MUST ask only one question per message** — break complex topics into multiple questions
- Prefer multiple choice when possible, open-ended when needed
- Focus on understanding: purpose, inputs, outputs, usage patterns, edge cases

**Dimensions to cover:**

| Dimension | Question |
|-----------|----------|
| Purpose | What problem does this tool solve? |
| Inputs | What does the tool take? (files, args, stdin, config) |
| Outputs | What does it produce? (stdout, files, exit codes) |
| Usage patterns | How will it be invoked? (one-off, piped, scripted) |
| Error cases | What can go wrong? How should errors appear? |
| UX expectations | Progress indicators, colors, verbosity levels? |

**Convergence tracking:**

Track whether each question round surfaces new information.

*A round yields if it surfaces:* New requirement, correction, edge case, or priority change.
*A round does NOT yield if it only:* Confirms existing understanding or rephrases what's known.

**Convergence rule:** Understanding has converged when two consecutive question rounds yield nothing new.

**YOU MUST** track each round explicitly: "Round N: [yielded | no yield] — [what was learned or confirmed]"

## Before Generating Code

**This is a mandatory checkpoint, not optional preparation.**

**Summary (present to user):**
- [ ] Purpose — what problem does this solve?
- [ ] Interface — commands, options, arguments
- [ ] Inputs/outputs — what goes in, what comes out
- [ ] Complexity — simple (single file) or complex (package)?

**Adversarial lens:**
- [ ] Could this be simpler? Is every option necessary?
- [ ] What's the main compliance risk? (Claude skipping brainstorming to write quick script)

**Before generating:**
- [ ] Present summary to user
- [ ] Ask: "Does this match your intent?"
- [ ] WAIT for user confirmation — do not generate until user responds

## Code Generation

**Simple tools (single file):**

Location: `/Users/jp/dotfiles/bin/.local/bin/<tool-name>`

Requirements:
- Shebang: `#!/usr/bin/env -S uv run --script`
- PEP 723 inline metadata for dependencies
- No `.py` extension
- Executable permission (`chmod +x`)
- Full type hints
- Google-style docstrings on public functions
- Ruff-compatible formatting

**Example structure:**
```python
#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["click", "rich"]
# ///
"""One-line description of the tool."""

from typing import ...

import click
from rich import print

@click.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output.")
def main(input_file: str, verbose: bool) -> None:
    """Process INPUT_FILE and do something useful."""
    ...

if __name__ == "__main__":
    main()
```

**Complex tools (package):**

Location: `/Users/jp/Projects/tools/<tool-name>/`

Structure:
```
<tool-name>/
├── pyproject.toml
├── src/<tool_name>/
│   ├── __init__.py
│   ├── cli.py
│   └── ...
└── tests/
    └── ...
```

Install: `uv tool install -e /Users/jp/Projects/tools/<tool-name>`

## UX and Quality Standards

**Help text:**
- Every command and option has a help string
- Examples in help where usage isn't obvious
- `--help` works at every level (tool, subcommand)

**Error handling:**
- Fail fast with clear messages
- Include what failed, why, and what to try
- Use appropriate exit codes (0 success, 1 general error, 2 usage error)
- Never silent failures

**Progress and feedback:**
- Long operations show progress (rich.progress, click.progressbar)
- Verbose mode (`-v/--verbose`) for debugging
- Quiet mode (`-q/--quiet`) for scripting when appropriate

**Config files (when needed):**
- XDG Base Directory spec: `~/.config/<tool-name>/config.toml`
- Environment variable overrides
- CLI flags override config

**Colors and formatting:**
- Use rich for colored output
- Respect `NO_COLOR` environment variable
- Tables for structured data, not walls of text

## After Generation

**For simple tools:**
1. Write file to `/Users/jp/dotfiles/bin/.local/bin/<tool-name>`
2. Set executable permission: `chmod +x <path>`
3. Verify it runs: `<tool-name> --help`

**For complex tools:**
1. Create package at `/Users/jp/Projects/tools/<tool-name>/`
2. Install: `uv tool install -e /Users/jp/Projects/tools/<tool-name>`
3. Verify it runs: `<tool-name> --help`

**Prompt user:**
> "The tool is installed. Try running `<tool-name> --help` to verify it works. Let me know if you want to adjust anything."

## Decision Points

**Simple vs complex?**
- Default to simple (single file) unless:
  - Multiple modules that import each other
  - Needs pytest-style tests
  - Building something reusable as a library
- When uncertain, start simple — can always upgrade later

**User's idea is too vague:**
- Start with: "What problem are you trying to solve?"
- If still vague: "Can you describe a specific situation where you'd use this?"

**User changes requirements after checkpoint:**
- Minor change → incorporate and continue
- Major change (different tool entirely) → return to understanding phase

**User wants to skip brainstorming:**
- Acknowledge: "I hear you."
- Complete checkpoint anyway: "Let me confirm my understanding before generating."
- Never skip — this is when misunderstandings surface

## Anti-Patterns

### Skip brainstorming and write code immediately

**Pattern:** User says "make me a CLI tool that does X" → Claude immediately writes the script.

**Why it fails:** Vague requirements lead to rework. The tool doesn't match what the user actually needed.

**Fix:** Ask questions first. One at a time. Converge on design before generating.

### Dump all questions at once

**Pattern:** Asking 5+ questions in one message to "be efficient."

**Why it fails:** User can't process everything; answers are shallow; follow-up questions impossible.

**Fix:** One question per message. Track what you've learned.

### Over-engineer the first version

**Pattern:** Adding config files, plugins, multiple output formats before the user asks.

**Why it fails:** Complexity without need. User wanted something simple.

**Fix:** Start minimal. Add features when requested.

## Rationalizations to Watch For

| Excuse | Reality |
|--------|---------|
| "This is a simple script" | Simple scripts still benefit from clear requirements. |
| "I know what they want" | Assumptions are most dangerous when confident. |
| "I'll just write something and iterate" | Iterating on wrong assumptions costs more than asking. |
| "They seem impatient" | Impatience is when the process matters most. |
| "It's faster to just code it" | Rework from misunderstanding is slower. |

**All of these mean: Complete the brainstorming. No shortcuts.**

## Troubleshooting

**Symptom:** User gives one-word answers
**Cause:** Questions may be too broad
**Fix:** Offer concrete options: "Would this be for [A], [B], or something else?"

**Symptom:** Convergence never reached
**Cause:** Scope keeps expanding
**Fix:** Pause and summarize: "So far I've heard [X, Y, Z]. Is this the core need, or should we scope down?"

**Symptom:** Generated tool doesn't run
**Cause:** Missing shebang, permissions, or dependencies
**Fix:** Verify: correct shebang (`#!/usr/bin/env -S uv run --script`), `chmod +x`, dependencies in PEP 723 block

**Symptom:** Tool runs but behavior is wrong
**Cause:** Requirements weren't fully understood
**Fix:** Return to brainstorming. Ask: "What did you expect to happen? What happened instead?"

## Examples

**Scenario:** User says "Make me a tool to rename files."

### BAD: Skip brainstorming

Claude immediately writes a file renaming script with pattern-based renaming, without asking:
- What kind of files?
- What renaming pattern?
- Batch or interactive?
- What about conflicts?

**Why it's bad:** The tool renames files by adding timestamps. User wanted to rename photos by EXIF date. Complete mismatch.

### GOOD: Understand first

Claude asks one question at a time:
1. "What kind of files are you renaming?"
2. "What should the new names look like?"
3. "Should it preview changes before applying, or just do it?"

After convergence, Claude presents: "A tool that renames JPEG files using their EXIF date, with a `--dry-run` flag to preview. Does this match your intent?"

**Why it's good:** Tool matches actual need. No rework.

---

**Scenario:** User says "I need something to check if my APIs are up."

### BAD: Over-engineer immediately

Claude creates a full monitoring system with config files, database storage, alerting, and a dashboard.

**Why it's bad:** User wanted a quick script to ping three endpoints and print status. Massive overkill.

### GOOD: Start minimal

Claude asks: "How many endpoints? Do you need alerts, or just a quick status check?"

User: "Just 3 URLs, print if they're up or down."

Claude generates a 30-line script. User is happy.

**Why it's good:** Right-sized solution. Can always add complexity later.

## When NOT to Use

- **Modifying existing CLI tool** — just edit it directly
- **Quick one-liner** — if the user explicitly wants a throwaway script, skip the process
- **Non-Python tools** — this skill is for Python/click; bash scripts or other languages are out of scope
- **GUI or web interfaces** — CLI only
- **User provides complete spec** — if requirements are already crystal clear, generate directly
