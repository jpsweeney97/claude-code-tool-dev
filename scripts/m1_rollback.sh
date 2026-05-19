#!/usr/bin/env bash
set -euo pipefail
# Restores every path in the manifest to docs/handoffs/ and removes the
# .gitignore line. Manifest format: "<sha256>  <path>" (shasum -a 256).
MANIFEST="${1:?manifest path required}"
REPO="${REPO:-/Users/jp/Projects/active/claude-code-tool-dev}"
cd "$REPO"
while read -r _sha path; do
  case "$path" in
    docs/handoffs/*) src=".claude/handoffs/${path#docs/handoffs/}";;
    .claude/handoffs/.archive/*) src=".claude/handoffs/archive/$(basename "$path")";;
    *) echo "rollback: unmapped manifest path. Got: ${path:0:100}" >&2; exit 1;;
  esac
  if [ "${DRY_RUN:-0}" = "1" ]; then
    [ -e "$src" ] || { echo "rollback DRY: MISSING $src (for $path)" >&2; exit 1; }
    echo "rollback DRY: $src -> $path"
  else
    mkdir -p "$(dirname "$path")"; mv "$src" "$path"
  fi
done < "$MANIFEST"
if [ "${DRY_RUN:-0}" != "1" ]; then
  perl -ni -e 'print unless m{^\.claude/handoffs/\s*$}' "$REPO/.gitignore"
fi
echo "rollback: ${DRY_RUN:+DRY-}OK"
