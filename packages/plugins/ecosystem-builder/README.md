# Ecosystem Builder

Autonomous workflow that expands the skill ecosystem by finding gaps, building artifacts, and staging for review.

## Quick Start

```bash
cd plugins/ecosystem-builder
uv sync --extra dev

# Run with mock (for testing)
uv run bin/ecosystem-builder run --artifacts 5 --mock

# Check status
uv run bin/ecosystem-builder status

# Review and accept/reject
uv run bin/ecosystem-builder review
uv run bin/ecosystem-builder review --accept skill-name
uv run bin/ecosystem-builder review --reject skill-name --reason "Why"
```

## CLI Flags

| Flag | Description |
|------|-------------|
| `--artifacts N` | Number of skills to generate (required) |
| `--hours N` | Maximum hours (default: 4.0) |
| `--cost N` | Maximum cost in USD (default: 50.0) |
| `--dry-run` | Create run without executing |
| `--mock` | Use mock callable for testing |

## Production Wiring

The CLI accepts a `subagent_callable` for complex gap generation. Currently:

- `--mock` uses a dynamic mock (works without Claude Code)
- Without `--mock`, complex gaps fail (no Claude Code callable available)

### Architecture

```
Orchestrator(subagent_callable=...)
    └── SkillBuilder(subagent_callable=...)
        └── SkillGeneratorAgent(llm_callable=...)
            └── callable(prompt) -> skill_content
```

The callable interface is `Callable[[str], str]` - takes a prompt, returns skill content.

## Testing

```bash
uv run python -m pytest tests/ -v   # Unit tests
./scripts/e2e-test.sh               # End-to-end test
```
