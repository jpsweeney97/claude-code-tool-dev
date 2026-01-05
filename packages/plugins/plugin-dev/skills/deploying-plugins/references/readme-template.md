# {PLUGIN_NAME}

> {ONE_LINE_DESCRIPTION}

**Version:** {VERSION}
**License:** {LICENSE}

## Description

{DESCRIPTION_PARAGRAPH}

## Installation

### Via Marketplace

```bash
/plugin marketplace add {GIT_URL}
/plugin install {PLUGIN_NAME}@{MARKETPLACE_NAME}
```

### Manual Installation

```bash
git clone {GIT_URL}
claude --plugin-dir ./{PLUGIN_NAME}
```

Or add to your settings:

```json
{
  "plugins": [
    { "type": "local", "path": "/path/to/{PLUGIN_NAME}" }
  ]
}
```

## Quick Start

{QUICK_START_EXAMPLE}

## Features

{FEATURES_LIST}

## Commands

| Command | Description |
|---------|-------------|
{COMMANDS_TABLE}

## Skills

| Skill | Description |
|-------|-------------|
{SKILLS_TABLE}

## Configuration

{CONFIGURATION_SECTION}

## Requirements

- Claude Code CLI
{ADDITIONAL_REQUIREMENTS}

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

{LICENSE_TEXT}

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.
