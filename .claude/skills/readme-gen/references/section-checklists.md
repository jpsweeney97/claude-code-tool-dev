# Section Checklists by Project Type

Phase 2 selects a project type. Phase 3 audits the README against that type's checklist. Phase 5 verifies full coverage.

## Universal Sections

Every README needs these regardless of project type.

| Section | Adequate Depth |
|---------|---------------|
| Title + metadata | Name, version, license, language/runtime, key dependencies |
| Problem statement | Why this exists. What's broken or missing without it. 1-2 paragraphs. |
| Quick Start | Install command + minimal usage to see it work. Copy-paste ready. |
| How It Works | Architecture: components, data flow, design properties. Not just a feature list. |
| Configuration | All user-configurable options with defaults and valid values |
| Tests | Total count, per-file breakdown table, run command |
| Known Limitations | Documented constraints, edge cases, planned-but-not-built items |

## Library / Package

Universal sections plus:

| Section | Adequate Depth |
|---------|---------------|
| API Reference | Key functions/classes with parameters, return types, and one-line descriptions |
| Usage Examples | 2-3 common patterns showing import → usage → expected output |
| Dependencies | Runtime vs dev. Note any unusual or heavy dependencies. |

## CLI Tool

Universal sections plus:

| Section | Adequate Depth |
|---------|---------------|
| Commands | All commands/subcommands with synopsis and description |
| Options / Flags | All flags with types, defaults, and descriptions. Table format. |
| Exit Codes | Numeric codes and their meanings |
| Usage Examples | Common invocations with expected output |

## API / Service

Universal sections plus:

| Section | Adequate Depth |
|---------|---------------|
| Endpoints | All routes with method, path, parameters, and response shape |
| Authentication | Auth mechanism, how to obtain credentials, header format |
| Request / Response | Example request body and response body for key endpoints |
| Error Codes | Status codes, error shapes, and recovery guidance |
| Deployment | How to run in production. Environment variables. |

## Plugin / Extension

Universal sections plus:

| Section | Adequate Depth |
|---------|---------------|
| Skills | Each skill with trigger description and context cost |
| Hooks | Table: event, matcher, script, timeout, behavior |
| Agents | Table: name, model, role, tools |
| Scripts | Table: all scripts with one-line purpose descriptions |
| Reference Files | Table: file and its purpose/authority |
| MCP Servers | Transport, tools provided, auto-configuration details (if applicable) |
| Environment Variables | Variable, default, purpose (if applicable) |

Not every plugin has all components. Only include sections for components that exist.

## MCP Server

Universal sections plus:

| Section | Adequate Depth |
|---------|---------------|
| Tools | Each tool with name, description, parameters, and return shape |
| Resources | Each resource with URI pattern and description |
| Transport | stdio, SSE, or HTTP. Client configuration example. |
| Client Configuration | `.mcp.json` or equivalent snippet ready to paste |

## Framework

Universal sections plus:

| Section | Adequate Depth |
|---------|---------------|
| Getting Started | Step-by-step from zero to working project |
| Project Structure | Directory layout with file/directory purposes |
| Conventions | Naming, file organization, patterns users must follow |
| Extension Points | Where and how to customize behavior |
| Migration Guide | Version upgrade paths (if applicable) |
