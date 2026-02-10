#!/usr/bin/env bash

set -u
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCS_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

PINNED_VERSIONS_FILE="${SCRIPT_DIR}/pinned-versions.env"
MASTER_GUIDE_FILE="${DOCS_ROOT}/codex-mcp-master-guide.md"
PARITY_MATRIX_FILE="${DOCS_ROOT}/references/official-parity-matrix.md"
SERVER_SPEC_FILE="${DOCS_ROOT}/specs/2026-02-09-codex-mcp-server-build-spec.md"
CLIENT_SPEC_FILE="${DOCS_ROOT}/specs/2026-02-09-codex-consultation-skill-implementation-spec.md"
PLAN_FILE="${DOCS_ROOT}/specs/2026-02-10-codex-mcp-docs-refactor-plan-v2.2.md"

DOCS_PARITY_VERIFIED_DATE="2026-02-10"

if [[ ! -f "${PINNED_VERSIONS_FILE}" ]]; then
  echo "validate-docs failed: missing pinned versions file. Got: ${PINNED_VERSIONS_FILE}"
  exit 1
fi

# shellcheck disable=SC1090
source "${PINNED_VERSIONS_FILE}"

if [[ -z "${MCP_INSPECTOR_VERSION:-}" ]]; then
  echo "validate-docs failed: MCP_INSPECTOR_VERSION is unset/empty. Got: ${MCP_INSPECTOR_VERSION-}"
  exit 1
fi

if [[ "${MCP_INSPECTOR_VERSION}" != "0.20.0" ]]; then
  echo "validate-docs failed: MCP_INSPECTOR_VERSION must equal 0.20.0. Got: ${MCP_INSPECTOR_VERSION}"
  exit 1
fi

MARKDOWN_FILES=()
while IFS= read -r markdown_file; do
  if [[ "${markdown_file}" == "${PLAN_FILE}" ]]; then
    continue
  fi
  MARKDOWN_FILES+=("${markdown_file}")
done < <(find "${DOCS_ROOT}" -type f -name "*.md" | sort)

FAILURES=0

fail_check() {
  local check_id="$1"
  local reason="$2"
  local details="${3:-}"
  FAILURES=1
  echo "[${check_id}] FAIL: ${reason}"
  if [[ -n "${details}" ]]; then
    echo "${details}"
  fi
}

check_no_matches() {
  local check_id="$1"
  local pattern="$2"
  local reason="$3"
  local details
  details="$(rg -n "${pattern}" "${MARKDOWN_FILES[@]}" || true)"
  if [[ -n "${details}" ]]; then
    fail_check "${check_id}" "${reason}" "${details}"
  fi
}

check_no_matches "DOC001" "/Users/jp/" "forbidden absolute local markdown path found"

check_no_matches "DOC002" "https://developers.openai.com/codex/mcp-server" "forbidden dead official link found"

doc003_details="$(rg -n "Open Decisions" "${SERVER_SPEC_FILE}" "${CLIENT_SPEC_FILE}" || true)"
if [[ -n "${doc003_details}" ]]; then
  fail_check "DOC003" "forbidden Open Decisions heading/content found in approved specs" "${doc003_details}"
fi

check_no_matches "DOC004" "mcp_server_startup_timeout_sec|mcp_tool_timeout_sec|mcp_oauth_client_store" "forbidden outdated MCP key name found"

quick_anchor_count="$(rg -n '<a id="canonical-quickstart"></a>' "${MARKDOWN_FILES[@]}" | wc -l | tr -d '[:space:]')"
command_anchor_count="$(rg -n '<a id="canonical-command-reference"></a>' "${MARKDOWN_FILES[@]}" | wc -l | tr -d '[:space:]')"

if [[ "${quick_anchor_count}" != "1" ]]; then
  fail_check "DOC005" "expected exactly one canonical-quickstart anchor, found ${quick_anchor_count}" "$(rg -n '<a id="canonical-quickstart"></a>' "${MARKDOWN_FILES[@]}" || true)"
fi

if [[ "${command_anchor_count}" != "1" ]]; then
  fail_check "DOC005" "expected exactly one canonical-command-reference anchor, found ${command_anchor_count}" "$(rg -n '<a id="canonical-command-reference"></a>' "${MARKDOWN_FILES[@]}" || true)"
fi

POINTER_FILES=(
  "${DOCS_ROOT}/learning-path/02-first-success-30-min.md"
  "${DOCS_ROOT}/references/codex-mcp-server-beginner-to-expert.md"
  "${DOCS_ROOT}/faq/codex-mcp-faq.md"
  "${DOCS_ROOT}/learning-path/README.md"
  "${DOCS_ROOT}/README.md"
)

doc006_missing=""
for pointer_file in "${POINTER_FILES[@]}"; do
  if ! rg -q "codex-mcp-master-guide\\.md#canonical-quickstart" "${pointer_file}"; then
    doc006_missing+="${pointer_file}: missing pointer to #canonical-quickstart"$'\n'
  fi
  if ! rg -q "codex-mcp-master-guide\\.md#canonical-command-reference" "${pointer_file}"; then
    doc006_missing+="${pointer_file}: missing pointer to #canonical-command-reference"$'\n'
  fi
done

if [[ -n "${doc006_missing}" ]]; then
  fail_check "DOC006" "pointer link(s) missing for canonical anchors" "${doc006_missing}"
fi

pinned_command="npx @modelcontextprotocol/inspector@${MCP_INSPECTOR_VERSION} codex mcp-server"

doc007_count="$(rg -n "${pinned_command}" "${MASTER_GUIDE_FILE}" | wc -l | tr -d '[:space:]')"
if [[ "${doc007_count}" != "1" ]]; then
  fail_check "DOC007" "canonical inspector command must appear exactly once in master guide, found ${doc007_count}" "$(rg -n "@modelcontextprotocol/inspector" "${MASTER_GUIDE_FILE}" || true)"
fi

doc007_unpinned="$(rg -n "npx @modelcontextprotocol/inspector codex mcp-server" "${MARKDOWN_FILES[@]}" || true)"
if [[ -n "${doc007_unpinned}" ]]; then
  fail_check "DOC007" "found unpinned inspector command usage" "${doc007_unpinned}"
fi

if [[ ! -f "${PARITY_MATRIX_FILE}" ]]; then
  fail_check "DOC008" "parity matrix file missing" "${PARITY_MATRIX_FILE}"
else
  doc008_missing=""
  REQUIRED_PARITY_PATTERNS=(
    "\\*\\*Verified date:\\*\\* ${DOCS_PARITY_VERIFIED_DATE}"
    "conversationId"
    "structuredContent.threadId"
    "mcp_servers.<id>.startup_timeout_sec"
    "mcp_servers.<id>.tool_timeout_sec"
    "mcp_oauth_credentials_store"
  )
  for required_pattern in "${REQUIRED_PARITY_PATTERNS[@]}"; do
    if ! rg -q "${required_pattern}" "${PARITY_MATRIX_FILE}"; then
      doc008_missing+="${PARITY_MATRIX_FILE}: missing required parity row/pattern -> ${required_pattern}"$'\n'
    fi
  done
  if [[ -n "${doc008_missing}" ]]; then
    fail_check "DOC008" "parity matrix missing required rows/patterns" "${doc008_missing}"
  fi
fi

if [[ "${FAILURES}" -ne 0 ]]; then
  echo "validate-docs: one or more checks failed (DOC001-DOC008)."
  exit 1
fi

echo "validate-docs: all checks passed (DOC001-DOC008)."
exit 0
