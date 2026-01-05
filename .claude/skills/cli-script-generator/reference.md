# CLI Script Reference

Comprehensive patterns for generating Python CLI scripts.

## Self-Bootstrapping Scripts

Scripts use uv's script runner for automatic dependency management:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["click"]
# ///
```

**How it works:**
- First run: uv reads PEP 723 metadata, installs deps to cache, executes script
- Subsequent runs: deps cached, near-instant startup
- No manual `pip install` or virtual environment needed

Add dependencies as needed:

```python
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click",
#     "httpx",
#     "rich",
# ]
# ///
```

## Version Flag

Every script must include a version flag.

```python
__version__ = "0.1.0"


@click.command()
@click.version_option(__version__, "--version", "-V")
def main() -> None:
    ...
```

For command groups:

```python
__version__ = "0.1.0"


@click.group()
@click.version_option(__version__, "--version", "-V")
def main() -> None:
    ...
```

**Version bumping:**
- Patch (0.1.0 → 0.1.1): Bug fixes, minor tweaks
- Minor (0.1.0 → 0.2.0): New features, new subcommands
- Major (0.1.0 → 1.0.0): Breaking changes to arguments/options

## Click Patterns

### Basic Command

```python
@click.command()
def main() -> None:
    """One-line description shown in --help."""
    click.echo("Hello")


if __name__ == "__main__":
    main()
```

### Arguments

Required positional inputs.

```python
@click.command()
@click.argument("name")
def main(name: str) -> None:
    """Greet NAME."""
    click.echo(f"Hello, {name}")
```

Multiple arguments:

```python
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.argument("dst", type=click.Path(path_type=Path))
```

Variadic arguments:

```python
@click.argument("files", nargs=-1, required=True)  # One or more
@click.argument("files", nargs=-1)  # Zero or more
```

### Options

Optional flags and values.

```python
@click.command()
@click.option("--count", "-c", default=1, help="Number of times.")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output.")
@click.option("--name", "-n", required=True, help="Your name.")
@click.option("--format", "fmt", type=click.Choice(["json", "text"]), default="text")
def main(count: int, verbose: bool, name: str, fmt: str) -> None:
    ...
```

### Environment Variable Options

For sensitive values or config that shouldn't appear in shell history:

```python
@click.command()
@click.option(
    "--api-key",
    envvar="MY_TOOL_API_KEY",
    required=True,
    help="API key. [env: MY_TOOL_API_KEY]",
)
def main(api_key: str) -> None:
    """Tool that needs an API key."""
    ...
```

Multiple environment variables (first found wins):

```python
@click.option(
    "--token",
    envvar=["MY_TOOL_TOKEN", "GITHUB_TOKEN"],
    help="Auth token. [env: MY_TOOL_TOKEN, GITHUB_TOKEN]",
)
```

**Convention:** Include `[env: VAR_NAME]` in help text so users know the option exists.

### Command Groups (Subcommands)

```python
@click.group()
def main() -> None:
    """Tool description."""
    pass


@main.command()
def subcommand() -> None:
    """Subcommand description."""
    ...


@main.command(name="other-name")  # Custom command name
def other_subcommand() -> None:
    ...
```

Nested groups:

```python
@click.group()
def main() -> None:
    """Top level."""
    pass


@main.group()
def sub() -> None:
    """Nested group."""
    pass


@sub.command()
def leaf() -> None:
    """Nested subcommand."""
    ...
```

### Shared Options (Group Context)

Pass data between group and subcommands:

```python
@click.group()
@click.option("--verbose", "-v", is_flag=True)
@click.pass_context
def main(ctx: click.Context, verbose: bool) -> None:
    """Tool with shared options."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


@main.command()
@click.pass_context
def sub(ctx: click.Context) -> None:
    """Subcommand accessing shared state."""
    if ctx.obj["verbose"]:
        click.echo("Verbose mode")
```

### Type Conversion

```python
# Built-in types
@click.option("--count", type=int)
@click.option("--ratio", type=float)
@click.option("--flag", type=bool)

# Path handling
@click.option("--file", type=click.Path(exists=True, path_type=Path))
@click.option("--dir", type=click.Path(file_okay=False, path_type=Path))
@click.option("--output", type=click.Path(dir_okay=False, writable=True, path_type=Path))

# File handling (opens file automatically)
@click.option("--input", type=click.File("r"))
@click.option("--output", type=click.File("w"), default="-")  # Default to stdout

# Constrained choices
@click.option("--level", type=click.Choice(["debug", "info", "warn", "error"]))

# Integer ranges
@click.option("--port", type=click.IntRange(1, 65535))
```

### Validation

Custom validation via callbacks:

```python
def validate_positive(ctx: click.Context, param: click.Parameter, value: int) -> int:
    if value <= 0:
        raise click.BadParameter("must be positive")
    return value


@click.option("--count", type=int, callback=validate_positive)
```

### Prompting

```python
# Prompt if not provided
@click.option("--name", prompt=True)

# Prompt with custom text
@click.option("--name", prompt="Your name")

# Password (hidden input)
@click.option("--password", prompt=True, hide_input=True)

# Confirmation prompt
if click.confirm("Proceed?"):
    ...

# Abort on no
if not click.confirm("Proceed?", abort=True):
    ...  # Never reached if user says no
```

### Output

```python
# Basic output
click.echo("Message")

# Styled output
click.secho("Success", fg="green")
click.secho("Warning", fg="yellow")
click.secho("Error", fg="red", err=True)  # Write to stderr
click.secho("Bold", bold=True)

# Colors: black, red, green, yellow, blue, magenta, cyan, white
# Styles: bold, dim, underline, blink, reverse

# Paging long output
click.echo_via_pager(long_text)

# Progress bar
with click.progressbar(items, label="Processing") as bar:
    for item in bar:
        process(item)
```

### Error Handling

```python
import sys

# User error (bad input, missing resource)
click.secho("Error: File not found: config.yml", fg="red", err=True)
sys.exit(1)

# System/runtime error (permissions, network, corruption)
click.secho("Error: Permission denied: /etc/hosts", fg="red", err=True)
sys.exit(2)

# Using click's exception (auto-exits with code 1)
raise click.ClickException("Something went wrong")

# Abort with message
raise click.Abort()

# In callbacks, signal bad parameter
raise click.BadParameter("must be positive")
```

### Stdin/Stdout Conventions

```python
# Accept stdin with "-"
@click.argument("input", type=click.File("r"), default="-")

# Pipe-friendly output (no decoration when piped)
if sys.stdout.isatty():
    click.secho("Pretty output", fg="green")
else:
    click.echo("Plain output")
```

## Shell Completions

Click has built-in shell completion support. Users enable it by adding a line to their shell config.

### Zsh (recommended)

Add to `~/.zshrc`:

```bash
eval "$(_<SCRIPT_NAME>_COMPLETE=zsh_source <script-name>)"
```

Example for a script named `bookmarks`:

```bash
eval "$(_BOOKMARKS_COMPLETE=zsh_source bookmarks)"
```

### Bash

Add to `~/.bashrc`:

```bash
eval "$(_<SCRIPT_NAME>_COMPLETE=bash_source <script-name>)"
```

### Fish

Add to `~/.config/fish/completions/<script-name>.fish`:

```fish
_<SCRIPT_NAME>_COMPLETE=fish_source <script-name> | source
```

### How It Works

- The environment variable format is `_<UPPERCASED_SCRIPT_NAME>_COMPLETE`
- Hyphens in script names become underscores: `my-tool` → `_MY_TOOL_COMPLETE`
- Click automatically completes:
  - Subcommand names
  - Option names (`--verbose`, `-v`)
  - Option values for `click.Choice`
  - File paths for `click.Path` and `click.File`

### Custom Completions

For dynamic completion values:

```python
def get_bookmark_names(ctx: click.Context, param: click.Parameter, incomplete: str) -> list[str]:
    """Return bookmark names matching the incomplete string."""
    bookmarks = load_bookmarks()
    return [name for name in bookmarks if name.startswith(incomplete)]


@main.command()
@click.argument("name", shell_complete=get_bookmark_names)
def get(name: str) -> None:
    ...
```

## Wrapper Scripts

Simple scripts that wrap other commands with preset arguments:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Quick git checkout shorthand."""

import subprocess
import sys

import click

__version__ = "0.1.0"


@click.command()
@click.version_option(__version__, "--version", "-V")
@click.argument("branch")
def main(branch: str) -> None:
    """Checkout BRANCH (shorthand for git checkout)."""
    result = subprocess.run(["git", "checkout", branch])
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
```

Note: Wrapper scripts that don't need click can omit it from dependencies entirely and use `sys.argv` directly for minimal overhead.

## Common Patterns

### Config File Loading

```python
from pathlib import Path
import json

CONFIG_PATH = Path.home() / ".config" / "tool" / "config.json"


def load_config() -> dict:
    """Load config, creating default if missing."""
    if not CONFIG_PATH.exists():
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text("{}")
        return {}
    return json.loads(CONFIG_PATH.read_text())
```

### XDG Base Directory

```python
from pathlib import Path
import os

def get_config_dir() -> Path:
    """Get XDG-compliant config directory."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "tool-name"


def get_data_dir() -> Path:
    """Get XDG-compliant data directory."""
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return base / "tool-name"
```

### Logging Setup

```python
import logging

def setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
    )
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | User error (bad input, invalid arguments, resource not found) |
| 2 | System error (permissions, network, corrupted state) |

## Testing Scripts

Scripts can be tested by invoking the command directly:

```python
from click.testing import CliRunner

def test_basic():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output


def test_version():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output
```

## Troubleshooting

### Script won't run: "command not found"

1. Check `~/.scripts` is in PATH:
   ```bash
   echo $PATH | tr ':' '\n' | grep scripts
   ```
2. If missing, add to `~/.zshrc`:
   ```bash
   export PATH="$HOME/.scripts:$PATH"
   ```
3. Reload: `source ~/.zshrc`

### Script won't run: "permission denied"

```bash
chmod +x ~/.scripts/<script-name>
```

### Script fails: "uv: command not found"

The self-bootstrapping shebang requires uv. Install it:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Script fails: dependency errors

Force uv to refresh the cache:
```bash
uv cache clean
```
Then run the script again.

### Script runs slowly on first execution

Normal. First run installs dependencies to uv's cache. Subsequent runs are fast.

### Click completion not working

1. Verify the eval line is in your shell config
2. Hyphens become underscores: `my-tool` → `_MY_TOOL_COMPLETE`
3. Restart your shell or run `source ~/.zshrc`
4. Test with: `_<SCRIPT_NAME>_COMPLETE=zsh_source <script-name>`
