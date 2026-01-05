# Monorepo Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the monorepo structure defined in `2026-01-04-monorepo-design.md`, creating scripts for inventory, migration, promotion, and settings sync.

**Architecture:** Python scripts with PEP 723 inline metadata run via `uv run`. No project virtualenv needed. Scripts discover extensions via glob patterns and manage YAML/JSON configs.

**Tech Stack:** Python 3.12, PyYAML, Rich (for terminal output), uv (runtime)

---

## Current State

**Exists:**
- Git repo with `.gitignore`
- `docs/plans/2026-01-04-monorepo-design.md` (approved design)
- `old-repos/` (archived repos, gitignored)

**Needs creation:**
- Directory structure (`.claude/`, `packages/`, `scripts/`, etc.)
- `package.json`, `tsconfig.base.json`
- Four Python scripts: `inventory`, `migrate`, `promote`, `sync-settings`
- Path-specific rules in `.claude/rules/`
- `CLAUDE.md`

**Source inventory:**
- `superserum/plugins/`: 7 plugins (deep-analysis, doc-auditor, docs-kb, ecosystem-builder, persistent-tasks, plugin-dev, session-log)
- `claude-skill-dev/skills/`: 9 skills (architecture-decisions, deep-exploration, deep-retrospective, deep-security-audit, deep-synthesis, markdown-formatter, three-lens-audit, writing-clearly-and-concisely, writing-for-claude)
- `~/.claude/skills/` (orphaned): 6 skills (cli-script-generator, config-optimize, creating-subagents, handoff, persistent-tasks, skillforge)
- `~/.claude/hooks/`: 5 hooks (block-credential-content, block-credential-json-files, block-keychain-extraction, mise-tool-guidance, warn-api-key-helper)

---

## Task 1: Create Directory Structure

**Files:**
- Create: `scripts/.gitkeep`
- Create: `packages/mcp-servers/.gitkeep`
- Create: `packages/plugins/.gitkeep`
- Create: `.claude/commands/.gitkeep`
- Create: `.claude/agents/.gitkeep`
- Create: `.claude/skills/.gitkeep`
- Create: `.claude/hooks/.gitkeep`
- Create: `.claude/rules/.gitkeep`
- Create: `references/.gitkeep`
- Create: `tmp/.gitkeep`

**Step 1: Create all directories with .gitkeep files**

```bash
mkdir -p scripts packages/mcp-servers packages/plugins .claude/commands .claude/agents .claude/skills .claude/hooks .claude/rules references tmp
touch scripts/.gitkeep packages/mcp-servers/.gitkeep packages/plugins/.gitkeep .claude/commands/.gitkeep .claude/agents/.gitkeep .claude/skills/.gitkeep .claude/hooks/.gitkeep .claude/rules/.gitkeep references/.gitkeep tmp/.gitkeep
```

**Step 2: Verify structure exists**

Run: `find . -name ".gitkeep" -not -path "./old-repos/*" | sort`

Expected:
```
./.claude/agents/.gitkeep
./.claude/commands/.gitkeep
./.claude/hooks/.gitkeep
./.claude/rules/.gitkeep
./.claude/skills/.gitkeep
./packages/mcp-servers/.gitkeep
./packages/plugins/.gitkeep
./references/.gitkeep
./scripts/.gitkeep
./tmp/.gitkeep
```

**Step 3: Commit**

```bash
git add .
git commit -m "chore: create directory structure for monorepo"
```

---

## Task 2: Create package.json and tsconfig.base.json

**Files:**
- Create: `package.json`
- Create: `tsconfig.base.json`

**Step 1: Create package.json**

```json
{
  "name": "claude-code-tool-dev",
  "private": true,
  "workspaces": [
    "packages/mcp-servers/*",
    "packages/plugins/*"
  ],
  "scripts": {
    "build": "npm run build --workspaces --if-present"
  }
}
```

**Step 2: Create tsconfig.base.json**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "outDir": "dist"
  }
}
```

**Step 3: Verify files are valid JSON**

Run: `node -e "require('./package.json'); require('./tsconfig.base.json'); console.log('Valid JSON')"`

Expected: `Valid JSON`

**Step 4: Commit**

```bash
git add package.json tsconfig.base.json
git commit -m "chore: add npm workspace config and base tsconfig"
```

---

## Task 3: Write Inventory Script

**Files:**
- Create: `scripts/inventory`
- Create: `migration-inventory.yaml` (output)

**Step 1: Create the inventory script**

```python
#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml", "rich"]
# ///
"""
Scan extension sources and generate migration inventory.

Usage:
    uv run scripts/inventory [--output FILE]

Scans:
    - superserum/plugins/
    - claude-skill-dev/skills/
    - ~/.claude/skills/ (orphaned)
    - ~/.claude/hooks/
"""

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from rich.console import Console
from rich.table import Table

console = Console()

# Source definitions
SOURCES = {
    "superserum": {
        "path": Path.home() / "Projects/active/superserum",
        "extensions": {"plugins": "plugins"},
    },
    "claude-skill-dev": {
        "path": Path.home() / "Projects/active/claude-skill-dev",
        "extensions": {"skills": "skills"},
    },
    "orphaned": {
        "path": Path.home() / ".claude",
        "extensions": {"skills": "skills", "hooks": "hooks"},
    },
}


def scan_directory(base: Path, subdir: str) -> list[dict[str, Any]]:
    """Scan a directory for extensions."""
    path = base / subdir
    if not path.exists():
        return []

    extensions = []
    for item in sorted(path.iterdir()):
        if item.name.startswith("."):
            continue

        # Skip symlinks for orphaned detection
        is_symlink = item.is_symlink()
        if is_symlink:
            target = item.resolve()
            symlink_target = str(target)
        else:
            symlink_target = None

        # Get modification time
        try:
            mtime = datetime.fromtimestamp(item.stat().st_mtime)
        except OSError:
            mtime = None

        # Count files
        if item.is_dir():
            file_count = sum(1 for _ in item.rglob("*") if _.is_file())
        else:
            file_count = 1

        extensions.append({
            "name": item.name,
            "path": str(item),
            "is_symlink": is_symlink,
            "symlink_target": symlink_target,
            "modified": mtime.isoformat() if mtime else None,
            "files": file_count,
        })

    return extensions


def detect_conflicts(extensions_by_type: dict[str, list[dict]]) -> dict[str, list[dict]]:
    """Detect same-named extensions across sources."""
    # Group by name
    by_name: dict[str, list[dict]] = {}
    for ext in extensions_by_type.get("all", []):
        name = ext["name"]
        if name not in by_name:
            by_name[name] = []
        by_name[name].append(ext)

    # Find conflicts
    conflicts = {name: sources for name, sources in by_name.items() if len(sources) > 1}
    return conflicts


def generate_inventory() -> dict[str, Any]:
    """Generate the full migration inventory."""
    inventory: dict[str, Any] = {
        "generated": datetime.now().isoformat(),
        "sources": {},
        "extensions": {"skills": [], "plugins": [], "hooks": []},
    }

    all_skills: list[dict] = []
    all_plugins: list[dict] = []
    all_hooks: list[dict] = []

    for source_name, source_config in SOURCES.items():
        base_path = source_config["path"]
        inventory["sources"][source_name] = {
            "path": str(base_path),
            "status": "pending",
        }

        for ext_type, subdir in source_config["extensions"].items():
            extensions = scan_directory(base_path, subdir)
            for ext in extensions:
                ext["source"] = source_name
                if ext_type == "skills":
                    all_skills.append(ext)
                elif ext_type == "plugins":
                    all_plugins.append(ext)
                elif ext_type == "hooks":
                    all_hooks.append(ext)

    # Process skills - detect conflicts
    skill_conflicts = detect_conflicts({"all": all_skills})
    processed_skills = set()

    for ext in all_skills:
        name = ext["name"]
        if name in processed_skills:
            continue

        if name in skill_conflicts:
            # Conflict case
            sources = skill_conflicts[name]
            inventory["extensions"]["skills"].append({
                "name": name,
                "conflict": True,
                "sources": [
                    {
                        "location": s["source"],
                        "path": s["path"],
                        "modified": s["modified"],
                        "files": s["files"],
                        "is_symlink": s["is_symlink"],
                        "symlink_target": s["symlink_target"],
                    }
                    for s in sources
                ],
                "decision": None,
                "selected_source": None,
                "status": "pending",
                "notes": "",
            })
        else:
            # No conflict
            inventory["extensions"]["skills"].append({
                "name": name,
                "source": ext["source"],
                "path": ext["path"],
                "is_symlink": ext["is_symlink"],
                "symlink_target": ext["symlink_target"],
                "decision": None,
                "status": "pending",
                "notes": "",
            })
        processed_skills.add(name)

    # Process plugins (no conflict detection needed - single source)
    for ext in all_plugins:
        inventory["extensions"]["plugins"].append({
            "name": ext["name"],
            "source": ext["source"],
            "path": ext["path"],
            "decision": None,
            "status": "pending",
            "notes": "",
        })

    # Process hooks (all from orphaned)
    for ext in all_hooks:
        inventory["extensions"]["hooks"].append({
            "name": ext["name"],
            "source": ext["source"],
            "path": ext["path"],
            "decision": None,
            "status": "pending",
            "notes": "",
        })

    return inventory


def print_summary(inventory: dict[str, Any]) -> None:
    """Print a summary table."""
    table = Table(title="Migration Inventory Summary")
    table.add_column("Type", style="cyan")
    table.add_column("Count", style="green")
    table.add_column("Conflicts", style="yellow")

    for ext_type in ["skills", "plugins", "hooks"]:
        extensions = inventory["extensions"][ext_type]
        total = len(extensions)
        conflicts = sum(1 for e in extensions if e.get("conflict", False))
        table.add_row(ext_type.title(), str(total), str(conflicts) if conflicts else "-")

    console.print(table)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate migration inventory")
    parser.add_argument(
        "--output",
        "-o",
        default="migration-inventory.yaml",
        help="Output file path (default: migration-inventory.yaml)",
    )
    args = parser.parse_args()

    console.print("[bold]Scanning extension sources...[/bold]")
    inventory = generate_inventory()

    output_path = Path(args.output)
    with output_path.open("w") as f:
        yaml.dump(inventory, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    console.print(f"\n[green]Inventory written to:[/green] {output_path}")
    print_summary(inventory)

    # Print next steps
    console.print("\n[bold]Next steps:[/bold]")
    console.print("1. Review migration-inventory.yaml")
    console.print("2. Set 'decision' for each extension: migrate | archive | delete")
    console.print("3. For conflicts, also set 'selected_source'")
    console.print("4. Run: uv run scripts/migrate")


if __name__ == "__main__":
    main()
```

**Step 2: Make script executable**

Run: `chmod +x scripts/inventory`

**Step 3: Run inventory script to verify it works**

Run: `uv run scripts/inventory --output /dev/stdout | head -50`

Expected: YAML output showing sources and extensions

**Step 4: Run full inventory and save**

Run: `uv run scripts/inventory`

Expected: `Inventory written to: migration-inventory.yaml` with summary table

**Step 5: Commit**

```bash
git add scripts/inventory
git commit -m "feat: add inventory script for extension discovery"
```

---

## Task 4: Write Migrate Script

**Files:**
- Create: `scripts/migrate`

**Step 1: Create the migrate script**

```python
#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml", "rich"]
# ///
"""
Process migration inventory and copy extensions to monorepo.

Usage:
    uv run scripts/migrate [--dry-run] [--inventory FILE]

Reads migration-inventory.yaml and processes extensions based on their 'decision' field:
    - migrate: Copy to .claude/<type>/ or packages/<type>/
    - archive: Mark as archived (no action, just status update)
    - delete: Skip (manual deletion recommended)
"""

import argparse
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from rich.console import Console
from rich.table import Table

console = Console()

# Destination mappings
DESTINATIONS = {
    "skills": Path(".claude/skills"),
    "plugins": Path("packages/plugins"),
    "hooks": Path(".claude/hooks"),
}


def load_inventory(path: Path) -> dict[str, Any]:
    """Load migration inventory from YAML."""
    with path.open() as f:
        return yaml.safe_load(f)


def save_inventory(inventory: dict[str, Any], path: Path) -> None:
    """Save updated inventory to YAML."""
    with path.open("w") as f:
        yaml.dump(inventory, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def copy_extension(source: Path, dest: Path, dry_run: bool) -> bool:
    """Copy an extension directory or file."""
    if dry_run:
        console.print(f"  [dim]Would copy:[/dim] {source} -> {dest}")
        return True

    try:
        if source.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(source, dest, symlinks=False)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
        return True
    except Exception as e:
        console.print(f"  [red]Error copying {source}: {e}[/red]")
        return False


def resolve_source_path(ext: dict[str, Any]) -> Path | None:
    """Get the actual source path for an extension."""
    if ext.get("conflict"):
        selected = ext.get("selected_source")
        if not selected:
            return None
        for src in ext["sources"]:
            if src["location"] == selected:
                path = Path(src["path"])
                # Follow symlinks
                if src.get("is_symlink") and src.get("symlink_target"):
                    path = Path(src["symlink_target"])
                return path
        return None
    else:
        path = Path(ext["path"])
        # Follow symlinks
        if ext.get("is_symlink") and ext.get("symlink_target"):
            path = Path(ext["symlink_target"])
        return path


def process_extensions(
    inventory: dict[str, Any],
    ext_type: str,
    dry_run: bool,
) -> tuple[int, int, int]:
    """Process all extensions of a given type. Returns (migrated, skipped, errors)."""
    extensions = inventory["extensions"].get(ext_type, [])
    dest_base = DESTINATIONS[ext_type]
    dest_base.mkdir(parents=True, exist_ok=True)

    migrated = 0
    skipped = 0
    errors = 0

    for ext in extensions:
        name = ext["name"]
        decision = ext.get("decision")
        status = ext.get("status", "pending")

        # Skip already processed
        if status in ("migrated", "archived", "deleted"):
            console.print(f"  [dim]Skipping {name} (already {status})[/dim]")
            skipped += 1
            continue

        # Check decision
        if not decision:
            console.print(f"  [yellow]Skipping {name} (no decision set)[/yellow]")
            skipped += 1
            continue

        if decision == "archive":
            ext["status"] = "archived"
            console.print(f"  [blue]Archived:[/blue] {name}")
            skipped += 1
            continue

        if decision == "delete":
            ext["status"] = "deleted"
            console.print(f"  [red]Marked deleted:[/red] {name} (manual cleanup needed)")
            skipped += 1
            continue

        if decision != "migrate":
            console.print(f"  [yellow]Unknown decision '{decision}' for {name}[/yellow]")
            skipped += 1
            continue

        # Validate conflict resolution
        if ext.get("conflict") and not ext.get("selected_source"):
            console.print(f"  [red]Error:[/red] {name} has conflict but no selected_source")
            errors += 1
            continue

        # Get source path
        source = resolve_source_path(ext)
        if not source or not source.exists():
            console.print(f"  [red]Error:[/red] Source not found for {name}: {source}")
            errors += 1
            continue

        # Determine destination
        dest = dest_base / name

        # Copy
        if copy_extension(source, dest, dry_run):
            if not dry_run:
                ext["status"] = "migrated"
                ext["migrated_at"] = datetime.now().isoformat()
            console.print(f"  [green]Migrated:[/green] {name}")
            migrated += 1
        else:
            errors += 1

    return migrated, skipped, errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Process migration inventory")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--inventory",
        "-i",
        default="migration-inventory.yaml",
        help="Inventory file path (default: migration-inventory.yaml)",
    )
    args = parser.parse_args()

    inventory_path = Path(args.inventory)
    if not inventory_path.exists():
        console.print(f"[red]Error:[/red] Inventory file not found: {inventory_path}")
        console.print("Run 'uv run scripts/inventory' first.")
        return

    inventory = load_inventory(inventory_path)

    if args.dry_run:
        console.print("[bold yellow]DRY RUN - no changes will be made[/bold yellow]\n")

    # Process each type
    results = {}
    for ext_type in ["skills", "plugins", "hooks"]:
        console.print(f"\n[bold]Processing {ext_type}...[/bold]")
        migrated, skipped, errors = process_extensions(inventory, ext_type, args.dry_run)
        results[ext_type] = {"migrated": migrated, "skipped": skipped, "errors": errors}

    # Save updated inventory
    if not args.dry_run:
        save_inventory(inventory, inventory_path)
        console.print(f"\n[green]Updated inventory saved to:[/green] {inventory_path}")

    # Print summary
    table = Table(title="Migration Summary")
    table.add_column("Type", style="cyan")
    table.add_column("Migrated", style="green")
    table.add_column("Skipped", style="yellow")
    table.add_column("Errors", style="red")

    for ext_type, counts in results.items():
        table.add_row(
            ext_type.title(),
            str(counts["migrated"]),
            str(counts["skipped"]),
            str(counts["errors"]) if counts["errors"] else "-",
        )

    console.print()
    console.print(table)

    # Next steps
    if not args.dry_run:
        total_migrated = sum(r["migrated"] for r in results.values())
        if total_migrated > 0:
            console.print("\n[bold]Next steps:[/bold]")
            console.print("1. Review migrated extensions in .claude/ and packages/")
            console.print("2. Remove symlinks from ~/.claude/ that point to old repos")
            console.print("3. Use 'uv run scripts/promote' to deploy to ~/.claude/")


if __name__ == "__main__":
    main()
```

**Step 2: Make script executable**

Run: `chmod +x scripts/migrate`

**Step 3: Test with dry-run (after inventory exists)**

Run: `uv run scripts/migrate --dry-run`

Expected: Shows "DRY RUN" and lists what would be done (mostly skipped due to no decisions)

**Step 4: Commit**

```bash
git add scripts/migrate
git commit -m "feat: add migrate script for processing inventory"
```

---

## Task 5: Write Promote Script

**Files:**
- Create: `scripts/promote`

**Step 1: Create the promote script**

```python
#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml", "rich"]
# ///
"""
Promote extensions from sandbox to production (~/.claude/).

Usage:
    uv run scripts/promote <type> <name> [--dry-run] [--force]
    uv run scripts/promote skill my-skill
    uv run scripts/promote hook block-credentials
    uv run scripts/promote command deploy
    uv run scripts/promote agent code-reviewer

Types: skill, command, agent, hook
"""

import argparse
import difflib
import shutil
import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()

# Type mappings
TYPE_CONFIG = {
    "skill": {
        "source": Path(".claude/skills"),
        "dest": Path.home() / ".claude/skills",
        "pattern": "*/SKILL.md",  # Skills are directories with SKILL.md
    },
    "command": {
        "source": Path(".claude/commands"),
        "dest": Path.home() / ".claude/commands",
        "pattern": "*.md",
    },
    "agent": {
        "source": Path(".claude/agents"),
        "dest": Path.home() / ".claude/agents",
        "pattern": "*.md",
    },
    "hook": {
        "source": Path(".claude/hooks"),
        "dest": Path.home() / ".claude/hooks",
        "pattern": "*.py",  # or *.sh
    },
}


def validate_extension(ext_type: str, source_path: Path) -> list[str]:
    """Validate an extension. Returns list of errors."""
    errors = []

    if not source_path.exists():
        errors.append(f"Source does not exist: {source_path}")
        return errors

    if ext_type == "skill":
        # Skills should be directories with SKILL.md
        if source_path.is_dir():
            skill_file = source_path / "SKILL.md"
            if not skill_file.exists():
                errors.append(f"Missing SKILL.md in {source_path}")
        else:
            errors.append(f"Skill should be a directory: {source_path}")

    elif ext_type == "hook":
        # Hooks should be executable
        if not source_path.is_file():
            errors.append(f"Hook should be a file: {source_path}")
        elif not (source_path.stat().st_mode & 0o111):
            errors.append(f"Hook is not executable: {source_path}")

    elif ext_type in ("command", "agent"):
        # Commands and agents should be .md files
        if not source_path.is_file():
            errors.append(f"{ext_type.title()} should be a file: {source_path}")
        elif source_path.suffix != ".md":
            errors.append(f"{ext_type.title()} should have .md extension: {source_path}")

    return errors


def find_extension(ext_type: str, name: str) -> Path | None:
    """Find the source path for an extension."""
    config = TYPE_CONFIG[ext_type]
    source_base = config["source"]

    if ext_type == "skill":
        # Skills are directories
        path = source_base / name
        if path.is_dir():
            return path
    elif ext_type == "hook":
        # Hooks can be .py or .sh
        for ext in [".py", ".sh", ""]:
            path = source_base / f"{name}{ext}"
            if path.is_file():
                return path
    else:
        # Commands and agents are .md files
        path = source_base / f"{name}.md"
        if path.is_file():
            return path
        # Also try without extension
        path = source_base / name
        if path.is_file():
            return path

    return None


def show_diff(source: Path, dest: Path) -> bool:
    """Show diff between source and destination. Returns True if different."""
    if not dest.exists():
        console.print(f"[green]New:[/green] {dest} (does not exist yet)")
        return True

    if source.is_dir():
        # For directories, compare file lists and contents
        source_files = {f.relative_to(source): f for f in source.rglob("*") if f.is_file()}
        dest_files = {f.relative_to(dest): f for f in dest.rglob("*") if f.is_file()}

        all_files = set(source_files.keys()) | set(dest_files.keys())
        has_diff = False

        for rel_path in sorted(all_files):
            src_file = source_files.get(rel_path)
            dst_file = dest_files.get(rel_path)

            if src_file and not dst_file:
                console.print(f"[green]+ {rel_path}[/green] (new file)")
                has_diff = True
            elif dst_file and not src_file:
                console.print(f"[red]- {rel_path}[/red] (will be removed)")
                has_diff = True
            else:
                # Both exist, compare contents
                try:
                    src_content = src_file.read_text().splitlines(keepends=True)
                    dst_content = dst_file.read_text().splitlines(keepends=True)
                    diff = list(difflib.unified_diff(dst_content, src_content, str(dst_file), str(src_file)))
                    if diff:
                        console.print(f"[yellow]~ {rel_path}[/yellow]")
                        console.print(Syntax("".join(diff[:20]), "diff", line_numbers=False))
                        has_diff = True
                except UnicodeDecodeError:
                    console.print(f"[yellow]~ {rel_path}[/yellow] (binary file)")
                    has_diff = True

        return has_diff
    else:
        # Single file
        try:
            src_content = source.read_text().splitlines(keepends=True)
            dst_content = dest.read_text().splitlines(keepends=True)
            diff = list(difflib.unified_diff(dst_content, src_content, str(dest), str(source)))
            if diff:
                console.print(Syntax("".join(diff[:30]), "diff", line_numbers=False))
                return True
            console.print("[dim]No changes[/dim]")
            return False
        except UnicodeDecodeError:
            console.print("[yellow]Binary files differ[/yellow]")
            return True


def copy_extension(source: Path, dest: Path) -> bool:
    """Copy extension to destination."""
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(source, dest)
        else:
            shutil.copy2(source, dest)
        return True
    except Exception as e:
        console.print(f"[red]Error copying: {e}[/red]")
        return False


def prompt_sync_settings() -> bool:
    """Ask if user wants to sync settings after hook promotion."""
    console.print("\n[yellow]Hook promoted. Sync settings.json?[/yellow]")
    response = input("Run sync-settings? [y/N] ").strip().lower()
    return response == "y"


def run_sync_settings() -> None:
    """Run the sync-settings script."""
    script = Path("scripts/sync-settings")
    if script.exists():
        subprocess.run(["uv", "run", str(script)])
    else:
        console.print("[yellow]sync-settings script not found[/yellow]")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Promote extension from sandbox to production",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run scripts/promote skill deep-exploration
  uv run scripts/promote hook block-credentials
  uv run scripts/promote command deploy --dry-run
""",
    )
    parser.add_argument(
        "type",
        choices=["skill", "command", "agent", "hook"],
        help="Extension type",
    )
    parser.add_argument("name", help="Extension name")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show diff without copying",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Skip confirmation prompt",
    )
    args = parser.parse_args()

    # Find source
    source = find_extension(args.type, args.name)
    if not source:
        console.print(f"[red]Error:[/red] {args.type} '{args.name}' not found in sandbox")
        console.print(f"Expected location: {TYPE_CONFIG[args.type]['source']}/{args.name}")
        sys.exit(1)

    # Validate
    errors = validate_extension(args.type, source)
    if errors:
        console.print("[red]Validation errors:[/red]")
        for error in errors:
            console.print(f"  - {error}")
        sys.exit(1)

    # Determine destination
    config = TYPE_CONFIG[args.type]
    if source.is_dir():
        dest = config["dest"] / args.name
    else:
        dest = config["dest"] / source.name

    # Show what we're doing
    console.print(Panel(f"[bold]{args.type.title()}:[/bold] {args.name}\n"
                        f"[dim]From:[/dim] {source}\n"
                        f"[dim]To:[/dim] {dest}"))

    # Show diff
    console.print("\n[bold]Changes:[/bold]")
    has_changes = show_diff(source, dest)

    if not has_changes:
        console.print("\n[green]Already up to date.[/green]")
        return

    if args.dry_run:
        console.print("\n[yellow]Dry run - no changes made[/yellow]")
        return

    # Confirm
    if not args.force:
        response = input("\nProceed with promotion? [y/N] ").strip().lower()
        if response != "y":
            console.print("[yellow]Cancelled[/yellow]")
            return

    # Copy
    if copy_extension(source, dest):
        console.print(f"\n[green]Promoted {args.type} '{args.name}' to {dest}[/green]")

        # For hooks, offer to sync settings
        if args.type == "hook" and not args.force:
            if prompt_sync_settings():
                run_sync_settings()
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Step 2: Make script executable**

Run: `chmod +x scripts/promote`

**Step 3: Test help output**

Run: `uv run scripts/promote --help`

Expected: Shows usage with types and examples

**Step 4: Test with non-existent extension (should fail gracefully)**

Run: `uv run scripts/promote skill nonexistent-skill`

Expected: Error message about skill not found

**Step 5: Commit**

```bash
git add scripts/promote
git commit -m "feat: add promote script for sandbox-to-production deployment"
```

---

## Task 6: Write Sync-Settings Script

**Files:**
- Create: `scripts/sync-settings`

**Step 1: Create the sync-settings script**

```python
#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = ["rich"]
# ///
"""
Rebuild ~/.claude/settings.json hooks section from hook file frontmatter.

Usage:
    uv run scripts/sync-settings [--dry-run] [--force]

Hook frontmatter format (PEP 723 style):
    # /// hook
    # event: PreToolUse
    # matcher: Bash
    # timeout: 60
    # ///

Valid events: PreToolUse, PostToolUse, UserPromptSubmit, Stop, SubagentStop,
              Notification, PermissionRequest, PreCompact, SessionStart, SessionEnd
"""

import argparse
import json
import re
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.syntax import Syntax

console = Console()

SETTINGS_PATH = Path.home() / ".claude/settings.json"
HOOKS_PATH = Path.home() / ".claude/hooks"

VALID_EVENTS = {
    "PreToolUse",
    "PostToolUse",
    "UserPromptSubmit",
    "Stop",
    "SubagentStop",
    "Notification",
    "PermissionRequest",
    "PreCompact",
    "SessionStart",
    "SessionEnd",
}


def parse_hook_frontmatter(path: Path) -> dict[str, Any] | None:
    """Parse hook frontmatter from a script file."""
    try:
        content = path.read_text()
    except Exception as e:
        console.print(f"[yellow]Warning: Could not read {path}: {e}[/yellow]")
        return None

    # Match PEP 723 style: # /// hook ... # ///
    pattern = r"#\s*///\s*hook\s*\n((?:#[^\n]*\n)*?)#\s*///"
    match = re.search(pattern, content)
    if not match:
        return None

    # Parse the frontmatter lines
    frontmatter = {}
    for line in match.group(1).split("\n"):
        line = line.strip()
        if line.startswith("#"):
            line = line[1:].strip()
            if ":" in line:
                key, value = line.split(":", 1)
                frontmatter[key.strip()] = value.strip()

    # Validate required fields
    if "event" not in frontmatter:
        console.print(f"[yellow]Warning: {path.name} missing 'event' in frontmatter[/yellow]")
        return None

    event = frontmatter["event"]
    if event not in VALID_EVENTS:
        console.print(f"[yellow]Warning: {path.name} has invalid event '{event}'[/yellow]")
        return None

    return frontmatter


def build_hooks_config(hooks_dir: Path) -> dict[str, list[dict]]:
    """Build hooks configuration from frontmatter."""
    config: dict[str, list[dict]] = {}

    if not hooks_dir.exists():
        return config

    for hook_file in sorted(hooks_dir.glob("*.py")) + sorted(hooks_dir.glob("*.sh")):
        if hook_file.name.startswith("."):
            continue

        frontmatter = parse_hook_frontmatter(hook_file)
        if not frontmatter:
            continue

        event = frontmatter["event"]
        matcher = frontmatter.get("matcher")
        timeout = int(frontmatter.get("timeout", 60000))

        # Build hook entry
        hook_entry = {
            "type": "command",
            "command": str(hook_file),
        }
        if timeout != 60000:
            hook_entry["timeout"] = timeout

        # Build event entry
        if matcher:
            event_entry = {
                "matcher": matcher,
                "hooks": [hook_entry],
            }
        else:
            event_entry = {"hooks": [hook_entry]}

        if event not in config:
            config[event] = []
        config[event].append(event_entry)

        console.print(f"  [green]Found:[/green] {hook_file.name} -> {event}" +
                      (f" (matcher: {matcher})" if matcher else ""))

    return config


def load_settings() -> dict[str, Any]:
    """Load current settings.json."""
    if SETTINGS_PATH.exists():
        return json.loads(SETTINGS_PATH.read_text())
    return {}


def save_settings(settings: dict[str, Any]) -> None:
    """Save settings.json."""
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2) + "\n")


def show_diff(old: dict, new: dict) -> bool:
    """Show diff between old and new hooks config. Returns True if different."""
    old_json = json.dumps(old, indent=2, sort_keys=True)
    new_json = json.dumps(new, indent=2, sort_keys=True)

    if old_json == new_json:
        console.print("[dim]No changes to hooks section[/dim]")
        return False

    import difflib
    diff = list(difflib.unified_diff(
        old_json.splitlines(keepends=True),
        new_json.splitlines(keepends=True),
        "current hooks",
        "new hooks",
    ))
    console.print(Syntax("".join(diff), "diff", line_numbers=False))
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync settings.json hooks from frontmatter")
    parser.add_argument("--dry-run", action="store_true", help="Show diff without writing")
    parser.add_argument("--force", "-f", action="store_true", help="Skip confirmation")
    parser.add_argument("--quiet", "-q", action="store_true", help="Only output errors")
    args = parser.parse_args()

    if not args.quiet:
        console.print("[bold]Scanning hooks for frontmatter...[/bold]\n")

    # Build new hooks config
    new_hooks = build_hooks_config(HOOKS_PATH)

    if not new_hooks:
        console.print("\n[yellow]No hooks with valid frontmatter found[/yellow]")
        return

    # Load current settings
    settings = load_settings()
    old_hooks = settings.get("hooks", {})

    # Show diff
    if not args.quiet:
        console.print("\n[bold]Changes to hooks section:[/bold]")
    has_changes = show_diff(old_hooks, new_hooks)

    if not has_changes:
        return

    if args.dry_run:
        console.print("\n[yellow]Dry run - no changes made[/yellow]")
        return

    if not args.force:
        response = input("\nApply changes to settings.json? [y/N] ").strip().lower()
        if response != "y":
            console.print("[yellow]Cancelled[/yellow]")
            return

    # Update and save
    settings["hooks"] = new_hooks
    save_settings(settings)
    console.print(f"\n[green]Updated {SETTINGS_PATH}[/green]")


if __name__ == "__main__":
    main()
```

**Step 2: Make script executable**

Run: `chmod +x scripts/sync-settings`

**Step 3: Test help output**

Run: `uv run scripts/sync-settings --help`

Expected: Shows usage and hook frontmatter format

**Step 4: Test dry-run**

Run: `uv run scripts/sync-settings --dry-run`

Expected: Shows found hooks and diff against current settings.json

**Step 5: Commit**

```bash
git add scripts/sync-settings
git commit -m "feat: add sync-settings script for hook configuration"
```

---

## Task 7: Create Path-Specific Rules

**Files:**
- Create: `.claude/rules/skills.md`
- Create: `.claude/rules/hooks.md`
- Create: `.claude/rules/commands.md`
- Create: `.claude/rules/agents.md`
- Create: `.claude/rules/mcp-servers.md`

**Step 1: Create skills.md**

```markdown
---
paths: .claude/skills/**
---

# Skill Development

## Structure

Skills are directories containing `SKILL.md`:
```
.claude/skills/<name>/
├── SKILL.md          # Main skill file (required)
└── ...               # Supporting files (optional)
```

## SKILL.md Format

```markdown
---
name: skill-name
description: One-line description for skill list
allowed-tools: ["Tool1", "Tool2"]  # Optional: auto-approve these tools
---

# Skill Name

Skill content here...
```

## Workflow

1. Create `.claude/skills/<name>/SKILL.md`
2. Test with `/<name>` in this project
3. Promote: `uv run scripts/promote skill <name>`

## Precedence

Personal (`~/.claude/skills/`) overrides project (`.claude/skills/`).

To test changes to an existing skill:
1. Use a dev name: `.claude/skills/<name>-dev/`
2. Test with `/<name>-dev`
3. When ready, promote overwrites production
```

**Step 2: Create hooks.md**

```markdown
---
paths: .claude/hooks/**
---

# Hook Development

## Frontmatter Convention

Hooks use PEP 723-style frontmatter (our convention, not native Claude Code):

```python
#!/usr/bin/env python3
# /// hook
# event: PreToolUse
# matcher: Bash
# timeout: 60000
# ///
```

## Valid Events

- `PreToolUse` - Before tool execution (can block)
- `PostToolUse` - After tool execution
- `UserPromptSubmit` - Before processing user input
- `Stop` - When session ends
- `SubagentStop` - When subagent completes
- `Notification` - On notifications
- `PermissionRequest` - On permission prompts
- `PreCompact` - Before context compaction
- `SessionStart` - When session begins
- `SessionEnd` - When session ends

## Workflow

1. Create `.claude/hooks/<name>.py` with frontmatter
2. Make executable: `chmod +x .claude/hooks/<name>.py`
3. Promote: `uv run scripts/promote hook <name>`
4. Sync: `uv run scripts/sync-settings`

## Important

Claude Code reads hooks from `settings.json`, not from files directly.
The `sync-settings` script generates the config from frontmatter.
```

**Step 3: Create commands.md**

```markdown
---
paths: .claude/commands/**
---

# Command Development

## Structure

Commands are markdown files:
```
.claude/commands/<name>.md
```

## Format

```markdown
---
description: Shown in command list
allowed-tools: ["Tool1"]  # Optional
---

Command template or instructions...

$ARGUMENTS will be replaced with user input after the command.
```

## Workflow

1. Create `.claude/commands/<name>.md`
2. Test with `/<name>` in this project
3. Promote: `uv run scripts/promote command <name>`
```

**Step 4: Create agents.md**

```markdown
---
paths: .claude/agents/**
---

# Agent Development

## Structure

Agents are markdown files:
```
.claude/agents/<name>.md
```

## Format

```markdown
---
description: Agent description for selection
allowed-tools: ["Tool1", "Tool2"]  # Tools this agent can use
---

Agent system prompt and instructions...
```

## Workflow

1. Create `.claude/agents/<name>.md`
2. Test via Task tool with `subagent_type: <name>`
3. Promote: `uv run scripts/promote agent <name>`
```

**Step 5: Create mcp-servers.md**

```markdown
---
paths: packages/mcp-servers/**
---

# MCP Server Development

## Structure

```
packages/mcp-servers/<name>/
├── package.json      # With claudeCode.mcp metadata
├── tsconfig.json     # Extends ../../tsconfig.base.json
├── src/
│   └── index.ts
└── dist/             # Build output (gitignored)
```

## package.json Metadata

```json
{
  "name": "@claude-tools/<name>",
  "claudeCode": {
    "mcp": {
      "transport": "stdio",
      "command": "node dist/index.js",
      "env": ["OPTIONAL_ENV_VAR"]
    }
  }
}
```

## tsconfig.json

```json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "rootDir": "src",
    "outDir": "dist"
  },
  "include": ["src"]
}
```

## Workflow

1. Create package structure
2. Develop and test: `npm run build -w packages/mcp-servers/<name>`
3. Promote: `uv run scripts/promote mcp-server <name>`
   - Builds server
   - Registers via `claude mcp add`
   - Updates `.mcp.json`
```

**Step 6: Remove placeholder .gitkeep from rules/**

Run: `rm .claude/rules/.gitkeep`

**Step 7: Verify all rule files exist**

Run: `ls -la .claude/rules/`

Expected: 5 .md files (skills, hooks, commands, agents, mcp-servers)

**Step 8: Commit**

```bash
git add .claude/rules/
git commit -m "feat: add path-specific rules for extension development"
```

---

## Task 8: Create CLAUDE.md

**Files:**
- Create: `CLAUDE.md`

**Step 1: Create CLAUDE.md**

```markdown
# Claude Code Extension Development

This monorepo is the single source of truth for developing Claude Code extensions.

## Quick Reference

| Extension | Create in | Test with | Promote with |
|-----------|-----------|-----------|--------------|
| Skill | `.claude/skills/<name>/SKILL.md` | `/<name>` | `uv run scripts/promote skill <name>` |
| Command | `.claude/commands/<name>.md` | `/<name>` | `uv run scripts/promote command <name>` |
| Agent | `.claude/agents/<name>.md` | Task tool | `uv run scripts/promote agent <name>` |
| Hook | `.claude/hooks/<name>.py` | After sync-settings | `uv run scripts/promote hook <name>` |
| MCP Server | `packages/mcp-servers/<name>/` | After build | `uv run scripts/promote mcp-server <name>` |

## Workflow

```
CREATE in .claude/  →  TEST locally  →  PROMOTE to ~/.claude/
```

**Why this works:**
- Project-local `.claude/` is auto-discovered by Claude Code
- Sandbox testing requires no setup
- Promotion is explicit with validation

## Scripts

| Script | Purpose |
|--------|---------|
| `uv run scripts/inventory` | Scan sources, generate migration YAML |
| `uv run scripts/migrate` | Process inventory, copy to monorepo |
| `uv run scripts/promote <type> <name>` | Validate and deploy to ~/.claude/ |
| `uv run scripts/sync-settings` | Rebuild settings.json from hook frontmatter |

## Skill Precedence

Personal (`~/.claude/skills/`) overrides project (`.claude/skills/`).

**Testing changes to existing skills:**
1. Create `.claude/skills/<name>-dev/SKILL.md`
2. Test with `/<name>-dev`
3. When ready, promote (overwrites production)

## Hook Frontmatter

Hooks require frontmatter for sync-settings to work:

```python
#!/usr/bin/env python3
# /// hook
# event: PreToolUse
# matcher: Bash
# timeout: 60000
# ///
```

## Directory Structure

```
.claude/
├── commands/     # Slash commands
├── agents/       # Subagents
├── skills/       # Skills
├── hooks/        # Hook scripts
├── rules/        # Path-specific context (auto-discovered)
└── settings.json # Hook wiring + config

packages/
├── mcp-servers/  # TypeScript MCP servers
└── plugins/      # Plugin packages

scripts/          # Python utility scripts (PEP 723)
```
```

**Step 2: Verify file created**

Run: `head -20 CLAUDE.md`

Expected: Shows the header and quick reference table

**Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add CLAUDE.md with workflow documentation"
```

---

## Task 9: Update .gitignore

**Files:**
- Modify: `.gitignore`

**Step 1: Update .gitignore to ensure all patterns are covered**

Current .gitignore already has most patterns. Verify and add if missing:

```gitignore
# Old repos (archived reference, not part of this project)
old-repos/

# macOS
.DS_Store

# Local settings
CLAUDE.local.md
.claude/settings.local.json

# Ephemeral
tmp/

# Node
node_modules/
packages/*/dist/

# Python
__pycache__/
*.pyc
.venv/

# Migration (keep inventory, ignore backup files)
*.backup
```

**Step 2: Commit if changes were made**

```bash
git add .gitignore
git commit -m "chore: update gitignore patterns"
```

---

## Task 10: Final Verification

**Step 1: Run full test cycle**

```bash
# 1. Generate inventory
uv run scripts/inventory

# 2. Check inventory was created
cat migration-inventory.yaml | head -30

# 3. Test promote with dry-run (will fail - no extensions yet)
uv run scripts/promote skill test-skill --dry-run 2>&1 || echo "Expected: no skill found"

# 4. Test sync-settings dry-run
uv run scripts/sync-settings --dry-run
```

**Step 2: Verify all scripts are executable**

Run: `ls -la scripts/`

Expected: All scripts show executable permissions (rwxr-xr-x)

**Step 3: Final commit with all remaining files**

```bash
git add -A
git status
git commit -m "chore: complete monorepo structure setup"
```

**Step 4: Show summary**

```bash
echo "=== Monorepo Structure ==="
find . -type f -not -path "./old-repos/*" -not -path "./.git/*" -not -name ".DS_Store" | sort

echo ""
echo "=== Next Steps ==="
echo "1. Review migration-inventory.yaml"
echo "2. Set decisions (migrate/archive/delete) for each extension"
echo "3. Run: uv run scripts/migrate"
echo "4. Remove old symlinks from ~/.claude/"
echo "5. Archive old repos (update READMEs)"
```

---

## Summary

| Task | Creates |
|------|---------|
| 1 | Directory structure with .gitkeep files |
| 2 | package.json, tsconfig.base.json |
| 3 | scripts/inventory |
| 4 | scripts/migrate |
| 5 | scripts/promote |
| 6 | scripts/sync-settings |
| 7 | .claude/rules/*.md (5 files) |
| 8 | CLAUDE.md |
| 9 | Updated .gitignore |
| 10 | Verification + final commit |

**Post-implementation:** Run inventory, annotate decisions, migrate extensions, remove symlinks, archive old repos.
