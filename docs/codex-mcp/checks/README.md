# Codex MCP Docs Checks

Run the validator from any location:

```bash
bash docs/codex-mcp/checks/validate-docs.sh
```

The validator loads pinned constants from:

- `./pinned-versions.env`

`MCP_INSPECTOR_VERSION` must be set and equal to `0.20.0`.

## Check IDs

- `DOC001`: forbid absolute local home-directory markdown paths
- `DOC002`: forbid the deprecated Codex MCP server docs URL
- `DOC003`: forbid `Open Decisions` in approved server/client specs
- `DOC004`: forbid outdated MCP key names
- `DOC005`: require exactly one canonical quickstart anchor and one canonical command reference anchor
- `DOC006`: ensure pointerized docs link to canonical master guide anchors
- `DOC007`: require pinned inspector command in canonical command block (`@0.20.0`)
- `DOC008`: ensure parity matrix contains required verified date and parity rows
