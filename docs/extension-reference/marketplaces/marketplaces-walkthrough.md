---
id: marketplaces-walkthrough
topic: Marketplace Walkthrough
category: marketplaces
tags: [tutorial, walkthrough, quickstart, example]
requires: [marketplaces-overview]
related_to: [marketplaces-schema, marketplaces-examples, marketplaces-troubleshooting, plugins-overview]
official_docs: https://code.claude.com/en/plugin-marketplaces
---

# Marketplace Walkthrough

Create a local marketplace with one plugin: a `/review` command for code reviews.

## Step 1: Create Directory Structure

```bash
mkdir -p my-marketplace/.claude-plugin
mkdir -p my-marketplace/plugins/review-plugin/.claude-plugin
mkdir -p my-marketplace/plugins/review-plugin/commands
```

**Structure:**

```
my-marketplace/
├── .claude-plugin/
│   └── marketplace.json      # Step 4
└── plugins/
    └── review-plugin/
        ├── .claude-plugin/
        │   └── plugin.json   # Step 3
        └── commands/
            └── review.md     # Step 2
```

## Step 2: Create the Plugin Command

Create the `/review` command that defines what it does:

**File:** `my-marketplace/plugins/review-plugin/commands/review.md`

```markdown
Review the code I've selected or the recent changes for:
- Potential bugs or edge cases
- Security concerns
- Performance issues
- Readability improvements

Be concise and actionable.
```

## Step 3: Create the Plugin Manifest

**File:** `my-marketplace/plugins/review-plugin/.claude-plugin/plugin.json`

```json
{
  "name": "review-plugin",
  "description": "Adds a /review command for quick code reviews",
  "version": "1.0.0"
}
```

## Step 4: Create the Marketplace File

**File:** `my-marketplace/.claude-plugin/marketplace.json`

```json
{
  "name": "my-plugins",
  "owner": {
    "name": "Your Name"
  },
  "plugins": [
    {
      "name": "review-plugin",
      "source": "./plugins/review-plugin",
      "description": "Adds a /review command for quick code reviews"
    }
  ]
}
```

## Step 5: Add and Install

Add the marketplace and install the plugin:

```bash
/plugin marketplace add ./my-marketplace
/plugin install review-plugin@my-plugins
```

> **Note:** Plugins are copied to a cache directory when installed. Files outside the plugin directory (like `../shared-utils`) won't be copied. Use symlinks or restructure shared files inside the plugin. See [marketplaces-troubleshooting](marketplaces-troubleshooting.md#files-not-found-after-installation).

## Step 6: Test It

Select some code in your editor and run your new command:

```bash
/review
```

## Validation Workflow

Before distributing your marketplace:

1. **Validate JSON syntax:**
   ```bash
   claude plugin validate .
   ```

2. **Add and test locally:**
   ```bash
   /plugin marketplace add ./my-marketplace
   /plugin install review-plugin@my-plugins
   ```

3. **Verify plugin works:**
   ```bash
   /review
   ```

See [marketplaces-troubleshooting](marketplaces-troubleshooting.md) for common validation errors.

## Related Topics

- [marketplaces-examples](marketplaces-examples.md) — More complex configurations
- [marketplaces-publishing](marketplaces-publishing.md) — Publish to GitHub
- [plugins-overview](../plugins/plugins-overview.md) — Creating plugins with commands, hooks, agents

## Key Points

- Marketplace file goes in `.claude-plugin/marketplace.json`
- Each plugin needs its own `.claude-plugin/plugin.json`
- Use relative paths like `./plugins/my-plugin` for bundled plugins
- Test locally before distributing to team
