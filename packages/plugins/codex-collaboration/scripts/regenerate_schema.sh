#!/usr/bin/env bash
# Regenerate vendored Codex App Server schema fixtures.
#
# This is a build-time maintenance step, not a runtime dependency.
# The generate-json-schema command is marked [experimental] in the CLI,
# but its output (JSON Schema files) is the canonical schema representation.
#
# Usage:
#   ./scripts/regenerate_schema.sh           # Use version from codex_compat.py
#   ./scripts/regenerate_schema.sh 0.118.0   # Override version

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Get version from argument or from code constant
if [[ $# -ge 1 ]]; then
    VERSION="$1"
else
    VERSION=$(python3 -c "
import re, sys
with open('${PLUGIN_DIR}/server/codex_compat.py') as f:
    for line in f:
        m = re.match(r'TESTED_CODEX_VERSION\s*=\s*\"(.+?)\"', line)
        if m:
            print(m.group(1))
            sys.exit(0)
print('ERROR: TESTED_CODEX_VERSION not found', file=sys.stderr)
sys.exit(1)
")
fi

if [[ -z "$VERSION" ]]; then
    echo "ERROR: Could not determine version" >&2
    exit 1
fi

# Verify codex is installed
if ! command -v codex &>/dev/null; then
    echo "ERROR: codex binary not found on PATH" >&2
    exit 1
fi

INSTALLED_VERSION=$(codex --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
echo "Installed codex-cli: $INSTALLED_VERSION"
echo "Target version:      $VERSION"

if [[ "$INSTALLED_VERSION" != "$VERSION" ]]; then
    echo "" >&2
    echo "ERROR: Installed version ($INSTALLED_VERSION) != target ($VERSION)" >&2
    echo "Install codex-cli $VERSION first, or pass the installed version as argument." >&2
    echo "The vendored directory name must match the binary that generated it." >&2
    exit 1
fi

# Generate into a temp directory first, then swap atomically.
# This prevents stale files from surviving across regenerations.
TARGET_DIR="${PLUGIN_DIR}/tests/fixtures/codex-app-server/${VERSION}"
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

echo ""
echo "Generating schema to temp directory ..."
codex app-server generate-json-schema --out "$TEMP_DIR"

FILE_COUNT=$(find "$TEMP_DIR" -type f -name '*.json' | wc -l | tr -d ' ')
echo "Generated ${FILE_COUNT} schema files"

# Replace target directory atomically
if [[ -d "$TARGET_DIR" ]]; then
    BACKUP_DIR=$(mktemp -d)
    mv "$TARGET_DIR" "$BACKUP_DIR/old"
    mv "$TEMP_DIR" "$TARGET_DIR"
    rm -rf "$BACKUP_DIR"
else
    mkdir -p "$(dirname "$TARGET_DIR")"
    mv "$TEMP_DIR" "$TARGET_DIR"
fi
# Disarm the trap — temp dir has been moved
trap - EXIT

# Generate derived required-methods.json
echo ""
echo "Generating required-methods.json ..."
python3 -c "
import json, sys
sys.path.insert(0, '${PLUGIN_DIR}')
from server.codex_compat import REQUIRED_METHODS, OPTIONAL_METHODS, TESTED_CODEX_VERSION, extract_client_methods
from pathlib import Path

schema_path = Path('${TARGET_DIR}/ClientRequest.json')
if not schema_path.exists():
    print('ERROR: ClientRequest.json not found in generated output', file=sys.stderr)
    sys.exit(1)

available = extract_client_methods(schema_path)

# Verify required methods are present
missing = REQUIRED_METHODS - available
if missing:
    print(f'ERROR: Generated schema is missing required methods: {sorted(missing)}', file=sys.stderr)
    sys.exit(1)

manifest = {
    'codex_version': '${VERSION}',
    'required': sorted(REQUIRED_METHODS),
    'optional': sorted(OPTIONAL_METHODS),
    'all_available': sorted(available),
}

out_path = schema_path.parent / 'required-methods.json'
with open(out_path, 'w') as f:
    json.dump(manifest, f, indent=2)
    f.write('\n')

print(f'Generated {out_path}')
missing_opt = OPTIONAL_METHODS - available
if missing_opt:
    print(f'  Optional: {sorted(missing_opt)} NOT present')
else:
    print(f'  Optional: {len(OPTIONAL_METHODS)} methods (all present)')
print(f'  Total available: {len(available)} methods')
"

echo ""
echo "Done. Vendored schema for codex-cli ${VERSION}."
echo ""
echo "Next steps:"
echo "  1. Update TESTED_CODEX_VERSION in server/codex_compat.py if version changed"
echo "  2. Run: uv run pytest tests/test_codex_compat.py -v"
echo "  3. Run: uv run pytest tests/test_codex_compat_live.py -v"
echo "  4. Commit vendored schema and code changes together"
