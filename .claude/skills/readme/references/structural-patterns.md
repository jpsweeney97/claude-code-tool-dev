# README Structural Patterns

Select the pattern that matches the project type identified during exploration. Each pattern lists required sections (always include) and optional sections (include when the exploration team found relevant content).

## Pattern Selection

| Project Type | Signals | Pattern |
|---|---|---|
| Library/package | Exports functions/classes, published to registry, consumed via import | [Library](#library) |
| CLI tool | Has bin scripts, parses arguments, runs from terminal | [CLI](#cli) |
| Plugin/extension | Extends another system, has hooks/handlers, installs into a host | [Plugin](#plugin) |
| Monorepo | Multiple packages, workspace config, shared tooling | [Monorepo](#monorepo) |

When a project fits multiple types (e.g., a monorepo containing CLI tools), use the outermost type for the root README and nest inner READMEs with their own patterns.

---

## Library

### Required Sections

**Title & Description** — One-line purpose statement. What does this library do and why does it exist? Name the problem it solves.

**Installation** — Package manager commands for all supported registries. Include peer dependencies if any.

**Quick Start** — Minimal working example. Import, configure, use. Copy-paste-runnable.

**API Reference** — Every public export documented: function signatures, parameter types, return types, thrown errors. Group by module or domain. For large APIs, link to generated docs and cover the top 5-10 most-used exports inline.

**Configuration** — All configuration options with types, defaults, and examples. Environment variables, config files, constructor options.

**Usage Examples** — 3-5 real-world scenarios showing common patterns. Progress from simple to advanced. Each example should be self-contained.

### Optional Sections

**Architecture** — Include when the library has meaningful internal structure (>5 modules, plugin system, middleware pipeline). Show how components connect. Useful for contributors and agents extending the system.

**Migration Guide** — Include when breaking changes exist between versions.

**Troubleshooting** — Include when the exploration team found common error patterns in tests or issues.

**Performance** — Include when the library has benchmarks, known hot paths, or scaling considerations.

**Contributing** — Include when the project accepts external contributions. Link to CONTRIBUTING.md if it exists; otherwise inline: how to set up dev environment, run tests, submit changes.

---

## CLI

### Required Sections

**Title & Description** — One-line purpose statement. What does this CLI do?

**Installation** — How to install globally and locally. Include version managers, Docker, or platform-specific methods if applicable.

**Quick Start** — The single most common command. Show input and output.

**Commands** — Every command and subcommand documented: syntax, required/optional arguments, flags with types and defaults. Use consistent formatting. For CLIs with many commands, group by category.

**Configuration** — Config file locations, formats, and all options. Environment variables that affect behavior. Precedence order (CLI flags > env vars > config file > defaults).

**Usage Examples** — Common workflows end-to-end. Show pipelines, scripting integration, and composition with other tools where relevant.

### Optional Sections

**Output Formats** — Include when the CLI supports multiple output formats (JSON, table, CSV, etc.).

**Shell Completion** — Include when completions are available.

**Scripting & Automation** — Include when the CLI is designed for non-interactive use. Document exit codes, stdout/stderr contracts, and machine-readable output.

**Architecture** — Include for CLIs with plugin systems, middleware, or complex internal structure.

**Contributing** — Same criteria as Library.

---

## Plugin

### Required Sections

**Title & Description** — One-line purpose statement. What does this plugin add to the host system? Name the host system.

**Installation** — How to install and enable the plugin in the host system. Include any host version requirements.

**What It Does** — Concrete list of capabilities the plugin adds. Not marketing — observable behaviors.

**Components** — Every component the plugin provides (hooks, commands, handlers, middleware, etc.), what each does, and how they interact. This is the section agents need most: it maps the plugin's surface area.

**Configuration** — All configuration options with types, defaults, and examples. Where config lives (host config file, plugin config file, environment variables).

**Usage Patterns** — 3-5 common usage scenarios showing the plugin in action within the host system.

**Extension Points** — How other plugins or user code can extend this plugin. What interfaces are stable, what hooks are available, what's internal.

### Optional Sections

**Architecture** — Include when the plugin has multiple interacting components, internal state, or non-obvious data flow.

**Compatibility** — Include when the plugin has version constraints, conflicts with other plugins, or platform limitations.

**Troubleshooting** — Include when the plugin can fail in non-obvious ways (host version mismatches, config conflicts, load order issues).

**Contributing** — Same criteria as Library.

---

## Monorepo

### Required Sections

**Title & Description** — One-line purpose statement for the monorepo as a whole. What is this collection of packages for?

**Package Map** — Table or tree showing every package with: name, one-line description, current status (stable/beta/experimental), and link to its own README. This is the navigation hub — agents and humans both use it to find what they need.

**Getting Started** — How to clone, install dependencies across all packages, and run the development environment. Cover the workspace tool (npm workspaces, pnpm, turborepo, uv workspace, cargo workspace, etc.).

**Common Workflows** — Cross-package operations: how to run all tests, how to build everything, how to add a new package, how to manage cross-package dependencies.

**Contributing** — How the monorepo is organized, branching conventions, where new code goes, how CI works across packages.

### Optional Sections

**Architecture** — Include when packages have meaningful dependency relationships. Show the dependency graph. Explain which packages are foundational vs. which are leaf nodes.

**Release Process** — Include when the monorepo has coordinated releases, versioning strategies, or changelogs.

**Scripts & Tooling** — Include when the monorepo has shared scripts, custom tooling, or automation that contributors need to know about.

---

## Cross-Pattern Guidance

### Dual-Audience Writing

Every section serves two audiences. Apply these principles throughout:

**For human readers:**
- Lead with the most common use case
- Use concrete examples over abstract descriptions
- Keep the quick start under 30 seconds to copy-paste-run
- Use headings that match what they'd search for

**For agent readers:**
- Use consistent, parseable structure (tables for options, code blocks for commands)
- Include type information for all parameters and options
- State constraints explicitly ("requires Node 18+", "must be called after init()")
- Document error conditions and edge cases — agents encounter these without human intuition
- Name files and paths precisely — agents navigate by path, not by "the config file"

### Sections to Never Include

- **Badges** unless the user requests them. They add visual noise and provide information available elsewhere.
- **Table of Contents** for READMEs under 200 lines. Headings serve as navigation.
- **License section body** — a one-line "See LICENSE" suffices. The full text belongs in the LICENSE file.
- **Changelog in README** — belongs in CHANGELOG.md. At most, link to it.
