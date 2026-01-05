---
name: cli-script-generator
description: Generate Python CLI scripts using click with PEP 723 inline metadata. Use when asked to create, update, or modify a terminal command, CLI tool, shell script, or executable script that should be runnable from anywhere.
---

# CLI Script Generator

Create and update self-contained Python CLI scripts that install to `~/.scripts` and run from anywhere.

## Trigger Conditions

Activate when the user asks to:
- Create a command-line tool or CLI
- Make a script runnable from anywhere
- Build a terminal command
- Create an executable script with arguments/options
- Update, modify, or add features to an existing script in `~/.scripts`

## Output Location

All scripts go to `~/.scripts/<script-name>` (no `.py` extension for executables).

## Workflow

### Creating a New Script

1. **Validate the script name** (see [Name Validation](#name-validation))

2. **Check for existing script:**
   ```bash
   ls -la ~/.scripts/<script-name> 2>/dev/null
   ```
   If exists: show the user the existing script and ask whether to replace, update, or abort.

3. **Clarify requirements** if ambiguous:
   - What inputs does the command need?
   - What should it output?
   - Single command or command group?

4. **Generate the script** following patterns in [reference.md](reference.md)

5. **Install the script:**
   ```bash
   mkdir -p ~/.scripts && \
   cat > ~/.scripts/<script-name> << 'SCRIPT_EOF'
   <script content>
   SCRIPT_EOF
   chmod +x ~/.scripts/<script-name>
   ```
   
   **Verify installation succeeded:**
   ```bash
   test -x ~/.scripts/<script-name> && echo "Installed successfully" || echo "Installation failed"
   ```

6. **Confirm** with usage example:
   ```
   Created ~/.scripts/<script-name>
   
   Usage: <script-name> [OPTIONS] <ARGS>
   
   Enable completions (optional):
     eval "$(_<SCRIPT_NAME>_COMPLETE=zsh_source <script-name>)"
   ```

### Updating an Existing Script

1. **Read the existing script first:**
   ```bash
   cat ~/.scripts/<script-name>
   ```

2. **Understand current structure** before modifying

3. **Apply the requested changes** while preserving:
   - Existing functionality not being changed
   - Version number (increment it)
   - Existing options/arguments (unless explicitly removing)

4. **Show diff or summary** of what changed

5. **Confirm before overwriting**

## Script Requirements

Every generated script MUST include:

1. **Self-bootstrapping shebang**: `#!/usr/bin/env -S uv run --script`
2. **PEP 723 metadata block** with dependencies
3. **Click decorators** for CLI interface
4. **Version flag**: `--version` / `-V`
5. **Docstring** explaining what the script does
6. **Error handling** with informative messages (fail fast, fail loud)
7. **`if __name__ == "__main__"` guard**

## Name Validation

Before creating a script, validate the name:

**Requirements:**
- Lowercase letters, numbers, and hyphens only
- Must start with a letter
- No spaces or special characters
- 2-50 characters long

**Reject with explanation if:**
- Name contains invalid characters
- Name collides with common shell builtins: `cd`, `pwd`, `echo`, `test`, `read`, `export`, `source`, `alias`, `type`, `which`, `true`, `false`, `exit`, `return`, `shift`, `wait`, `exec`, `eval`, `set`, `unset`, `trap`, `kill`
- Name collides with standard Unix commands: `ls`, `cat`, `rm`, `cp`, `mv`, `grep`, `find`, `sed`, `awk`, `sort`, `head`, `tail`, `less`, `more`, `man`, `git`, `python`, `pip`, `uv`

**Warn but allow if:**
- Name shadows a command in PATH (check with `which <name>`)

## Conventions

- No `.py` extension on installed scripts (they're commands, not modules)
- Use `click.echo()` for output, not `print()`
- Use `click.secho()` for colored/styled output
- Exit codes: 0 = success, 1 = user error, 2 = system/runtime error
- Options use `--kebab-case`, arguments use `UPPER_CASE` in help
- Version format: `MAJOR.MINOR.PATCH` starting at `0.1.0`

## Examples

### Request: "Create a command that counts lines in files"

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["click"]
# ///
"""Count lines in one or more files."""

import sys
from pathlib import Path

import click

__version__ = "0.1.0"


@click.command()
@click.version_option(__version__, "--version", "-V")
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--total", "-t", is_flag=True, help="Show only the total count.")
def main(files: tuple[Path, ...], total: bool) -> None:
    """Count lines in FILES."""
    counts: list[tuple[Path, int]] = []
    
    for file_path in files:
        try:
            count = len(file_path.read_text().splitlines())
            counts.append((file_path, count))
        except PermissionError:
            click.secho(f"Error: Permission denied: {file_path}", fg="red", err=True)
            sys.exit(2)
    
    if total:
        click.echo(sum(c for _, c in counts))
    else:
        for path, count in counts:
            click.echo(f"{count:>8}  {path}")
        if len(counts) > 1:
            click.echo(f"{sum(c for _, c in counts):>8}  total")


if __name__ == "__main__":
    main()
```

### Request: "Create a command with subcommands for managing bookmarks"

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["click"]
# ///
"""Manage URL bookmarks from the command line."""

import json
import sys
from pathlib import Path

import click

__version__ = "0.1.0"

BOOKMARKS_FILE = Path.home() / ".bookmarks.json"


def load_bookmarks() -> dict[str, str]:
    """Load bookmarks from disk."""
    if not BOOKMARKS_FILE.exists():
        return {}
    try:
        return json.loads(BOOKMARKS_FILE.read_text())
    except json.JSONDecodeError as e:
        click.secho(f"Error: Corrupted bookmarks file: {e}", fg="red", err=True)
        sys.exit(2)


def save_bookmarks(bookmarks: dict[str, str]) -> None:
    """Save bookmarks to disk."""
    BOOKMARKS_FILE.write_text(json.dumps(bookmarks, indent=2))


@click.group()
@click.version_option(__version__, "--version", "-V")
def main() -> None:
    """Manage URL bookmarks."""
    pass


@main.command()
@click.argument("name")
@click.argument("url")
def add(name: str, url: str) -> None:
    """Add a bookmark."""
    bookmarks = load_bookmarks()
    if name in bookmarks:
        click.secho(f"Error: Bookmark '{name}' already exists.", fg="red", err=True)
        sys.exit(1)
    bookmarks[name] = url
    save_bookmarks(bookmarks)
    click.secho(f"Added: {name} -> {url}", fg="green")


@main.command()
@click.argument("name")
def get(name: str) -> None:
    """Get a bookmark URL."""
    bookmarks = load_bookmarks()
    if name not in bookmarks:
        click.secho(f"Error: Bookmark '{name}' not found.", fg="red", err=True)
        sys.exit(1)
    click.echo(bookmarks[name])


@main.command(name="list")
def list_bookmarks() -> None:
    """List all bookmarks."""
    bookmarks = load_bookmarks()
    if not bookmarks:
        click.echo("No bookmarks saved.")
        return
    for name, url in sorted(bookmarks.items()):
        click.echo(f"{name}: {url}")


@main.command()
@click.argument("name")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation.")
def remove(name: str, force: bool) -> None:
    """Remove a bookmark."""
    bookmarks = load_bookmarks()
    if name not in bookmarks:
        click.secho(f"Error: Bookmark '{name}' not found.", fg="red", err=True)
        sys.exit(1)
    if not force and not click.confirm(f"Remove '{name}'?"):
        click.echo("Aborted.")
        return
    del bookmarks[name]
    save_bookmarks(bookmarks)
    click.secho(f"Removed: {name}", fg="yellow")


if __name__ == "__main__":
    main()
```

See [reference.md](reference.md) for complete click patterns and conventions.
