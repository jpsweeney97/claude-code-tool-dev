#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Migration script for renaming extension-docs to claude-code-docs.

Usage:
    uv run scripts/migrate-extension-docs.py          # dry-run (default)
    uv run scripts/migrate-extension-docs.py --apply  # execute changes
"""

import argparse
import json
import shutil
import sys
from pathlib import Path


def log(msg: str, prefix: str = "") -> None:
    """Print a log message with optional prefix."""
    print(f"{prefix}{msg}")


def dry_log(msg: str) -> None:
    """Print a dry-run log message."""
    log(msg, "[DRY-RUN] ")


def apply_log(msg: str) -> None:
    """Print an apply log message."""
    log(msg, "[APPLY] ")


def read_file(path: Path) -> str | None:
    """Read a file, returning None if it doesn't exist."""
    try:
        return path.read_text()
    except FileNotFoundError:
        return None


def write_file(path: Path, content: str) -> None:
    """Write content to a file atomically."""
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(content)
    temp_path.rename(path)


def update_json_file(
    path: Path,
    updates: dict,
    dry_run: bool,
) -> bool:
    """Update specific keys in a JSON file."""
    content = read_file(path)
    if content is None:
        log(f"Skipping (not found): {path}")
        return False

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        log(f"Skipping (invalid JSON): {path} - {e}")
        return False

    changed = False
    for key_path, transform in updates.items():
        keys = key_path.split(".")
        obj = data
        for key in keys[:-1]:
            if key not in obj:
                break
            obj = obj[key]
        else:
            final_key = keys[-1]
            if final_key in obj:
                old_val = obj[final_key]
                new_val = transform(old_val) if callable(transform) else transform
                if old_val != new_val:
                    if dry_run:
                        dry_log(f"Would update {path}")
                        dry_log(f"  - {key_path}: {old_val!r} → {new_val!r}")
                    else:
                        obj[final_key] = new_val
                    changed = True

    if changed and not dry_run:
        write_file(path, json.dumps(data, indent=2) + "\n")
        apply_log(f"Updated: {path}")

    return changed


def update_text_file(
    path: Path,
    replacements: list[tuple[str, str]],
    dry_run: bool,
) -> bool:
    """Apply text replacements to a file."""
    content = read_file(path)
    if content is None:
        log(f"Skipping (not found): {path}")
        return False

    new_content = content
    changes = []
    for old, new in replacements:
        if old in new_content:
            changes.append((old, new))
            new_content = new_content.replace(old, new)

    if not changes:
        return False

    if dry_run:
        dry_log(f"Would update: {path}")
        for old, new in changes:
            dry_log(f"  - {old!r} → {new!r}")
    else:
        write_file(path, new_content)
        apply_log(f"Updated: {path}")

    return True


def rename_path(old_path: Path, new_path: Path, dry_run: bool) -> bool:
    """Rename a file or directory."""
    if not old_path.exists():
        log(f"Skipping (not found): {old_path}")
        return False

    if new_path.exists():
        log(f"Skipping (target exists): {new_path}")
        return False

    if dry_run:
        dry_log(f"Would rename: {old_path} → {new_path}")
    else:
        new_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(old_path), str(new_path))
        apply_log(f"Renamed: {old_path} → {new_path}")

    return True


def migrate(dry_run: bool) -> int:
    """Run the migration."""
    repo_root = Path(__file__).parent.parent
    home = Path.home()

    changes = 0

    # 1. Rename MCP server directory
    old_server = repo_root / "packages/mcp-servers/extension-docs"
    new_server = repo_root / "packages/mcp-servers/claude-code-docs"
    if rename_path(old_server, new_server, dry_run):
        changes += 1

    # 2. Rename agent file
    old_agent = repo_root / ".claude/agents/extension-docs-researcher.md"
    new_agent = repo_root / ".claude/agents/claude-code-docs-researcher.md"
    if rename_path(old_agent, new_agent, dry_run):
        changes += 1

    # Update agent content
    agent_path = new_agent if new_agent.exists() else old_agent
    if update_text_file(
        agent_path,
        [
            ("extension-docs-researcher", "claude-code-docs-researcher"),
            ("mcp__extension-docs__search_extension_docs", "mcp__claude-code-docs__search_docs"),
            ("mcp__extension-docs__reload_extension_docs", "mcp__claude-code-docs__reload_docs"),
            ("extension-docs MCP server", "claude-code-docs MCP server"),
        ],
        dry_run,
    ):
        changes += 1

    # 3. Rename skill directory
    old_skill = repo_root / ".claude/skills/extension-docs"
    new_skill = repo_root / ".claude/skills/claude-code-docs"
    if rename_path(old_skill, new_skill, dry_run):
        changes += 1

    # Update skill content
    skill_path = (new_skill if new_skill.exists() else old_skill) / "SKILL.md"
    if update_text_file(
        skill_path,
        [
            ("name: extension-docs", "name: claude-code-docs"),
            ("mcp__extension-docs__search_extension_docs", "mcp__claude-code-docs__search_docs"),
            ("mcp__extension-docs__reload_extension_docs", "mcp__claude-code-docs__reload_docs"),
            ("extension-docs MCP server", "claude-code-docs MCP server"),
            ("search_extension_docs", "search_docs"),
            ("reload_extension_docs", "reload_docs"),
        ],
        dry_run,
    ):
        changes += 1

    # 4. Update .claude/settings.local.json
    if update_text_file(
        repo_root / ".claude/settings.local.json",
        [
            ("mcp__extension-docs__search_extension_docs", "mcp__claude-code-docs__search_docs"),
        ],
        dry_run,
    ):
        changes += 1

    # 5. Update ~/.claude.json (MCP server config)
    claude_json = home / ".claude.json"
    content = read_file(claude_json)
    if content:
        try:
            data = json.loads(content)
            # Idempotency: skip if already migrated
            if "mcpServers" in data and "claude-code-docs" in data["mcpServers"]:
                log(f"Skipping (already migrated): {claude_json}")
            elif "mcpServers" in data and "extension-docs" in data["mcpServers"]:
                if dry_run:
                    dry_log(f"Would update: {claude_json}")
                    dry_log("  - mcpServers.extension-docs → mcpServers.claude-code-docs")
                else:
                    # Backup before modifying
                    backup_path = claude_json.with_suffix(".json.bak")
                    backup_path.write_text(content)
                    apply_log(f"Backed up: {claude_json} → {backup_path}")
                    data["mcpServers"]["claude-code-docs"] = data["mcpServers"].pop("extension-docs")
                    write_file(claude_json, json.dumps(data, indent=2) + "\n")
                    apply_log(f"Updated: {claude_json}")
                changes += 1
        except json.JSONDecodeError:
            log(f"Skipping (invalid JSON): {claude_json}")

    # 6. Update ~/.claude/skills/extension-docs if it exists
    home_old_skill = home / ".claude/skills/extension-docs"
    home_new_skill = home / ".claude/skills/claude-code-docs"
    if home_old_skill.exists():
        if rename_path(home_old_skill, home_new_skill, dry_run):
            changes += 1
        skill_md = (home_new_skill if home_new_skill.exists() else home_old_skill) / "SKILL.md"
        if skill_md.exists():
            if update_text_file(
                skill_md,
                [
                    ("name: extension-docs", "name: claude-code-docs"),
                    ("mcp__extension-docs__", "mcp__claude-code-docs__"),
                    ("search_extension_docs", "search_docs"),
                    ("reload_extension_docs", "reload_docs"),
                ],
                dry_run,
            ):
                changes += 1

    # 7. Update ~/.claude/hooks/extension-docs-reminder.sh if it exists
    old_hook = home / ".claude/hooks/extension-docs-reminder.sh"
    new_hook = home / ".claude/hooks/claude-code-docs-reminder.sh"
    if old_hook.exists():
        if rename_path(old_hook, new_hook, dry_run):
            changes += 1
        hook_path = new_hook if new_hook.exists() else old_hook
        if update_text_file(
            hook_path,
            [
                ("search_extension_docs", "search_docs"),
                ("reload_extension_docs", "reload_docs"),
                ("extension-docs MCP", "claude-code-docs MCP"),
            ],
            dry_run,
        ):
            changes += 1

    # 8. Update ~/.claude/settings.json hook references
    settings_json = home / ".claude/settings.json"
    if update_text_file(
        settings_json,
        [
            ("extension-docs-reminder.sh", "claude-code-docs-reminder.sh"),
        ],
        dry_run,
    ):
        changes += 1

    # Summary
    print()
    if dry_run:
        print(f"Summary: {changes} change(s) would be made")
        print("\nTo apply changes, run: uv run scripts/migrate-extension-docs.py --apply")
    else:
        print(f"Summary: {changes} change(s) made")
        print("\nNext steps:")
        print("1. Rebuild MCP server: cd packages/mcp-servers/claude-code-docs && npm run build")
        print("2. Restart Claude Code to pick up new MCP server config")
        print("3. Delete orphaned cache: rm -rf ~/.cache/extension-docs/")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate extension-docs to claude-code-docs"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Execute changes (default is dry-run)",
    )
    args = parser.parse_args()

    dry_run = not args.apply
    if dry_run:
        print("Running in dry-run mode. Use --apply to execute changes.\n")

    return migrate(dry_run)


if __name__ == "__main__":
    sys.exit(main())
