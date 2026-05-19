#!/usr/bin/env bash
set -euo pipefail
REPO="${REPO:-/Users/jp/Projects/active/claude-code-tool-dev}"
cd "$REPO"
mkdir -p .claude/handoffs/archive
# Active top-level (depth 1) → .claude/handoffs/
find docs/handoffs -maxdepth 1 -type f -name '*.md' -print0 \
  | while IFS= read -r -d '' f; do mv "$f" ".claude/handoffs/$(basename "$f")"; done
# Archive → .claude/handoffs/archive/
find docs/handoffs/archive -maxdepth 1 -type f -name '*.md' -print0 \
  | while IFS= read -r -d '' f; do mv "$f" ".claude/handoffs/archive/$(basename "$f")"; done
# Promote the 1 pre-1.6.0 residue out of the hidden .archive/
RES=".claude/handoffs/.archive/2026-03-29_21-30_checkpoint-handoff-project-local-storage.md"
[ -f "$RES" ] && mv "$RES" ".claude/handoffs/archive/$(basename "$RES")"
# Remove .DS_Store (NEVER move them); find -delete on .DS_Store only (not rm)
find docs/handoffs .claude/handoffs/.archive -name '.DS_Store' -delete 2>/dev/null || true
echo "M1: move complete"
