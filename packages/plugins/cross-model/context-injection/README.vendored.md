# Vendored Copy — Do Not Edit

This directory is a vendored copy of `packages/context-injection/`.
Edits here will be overwritten by `scripts/build-cross-model-plugin`.

To make changes:
1. Edit the source at `packages/context-injection/`
2. Run tests: `cd packages/context-injection && uv run pytest`
3. Sync: `scripts/build-cross-model-plugin`

## Tests

Tests for the context injection system live in the source package at `packages/context-injection/tests/`. They are intentionally excluded from this vendored copy. Run them from the source package:

```bash
cd packages/context-injection && uv run pytest
```
