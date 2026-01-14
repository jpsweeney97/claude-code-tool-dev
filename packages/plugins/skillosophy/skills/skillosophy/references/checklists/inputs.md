# Inputs Checklist

## Structural
- [MUST] Required inputs sub-section exists
- [MUST] Optional inputs sub-section exists (or explicit "None")
- [MUST] Constraints/Assumptions sub-section exists

## Semantic
- [MUST] At least one required input defined
- [MUST] Each input is specific and actionable (not "the inputs needed")
- [MUST] Constraints declare non-universal assumptions:
  - Tools (specific CLIs, versions)
  - Network (API access, downloads)
  - Permissions (file write, env vars, secrets)
  - Repo layout (specific paths, conventions)
- [MUST] Fallback provided when assumptions not met (or STOP/ask)

## Anti-patterns
- [SEMANTIC] Placeholder language: "whatever is needed", "appropriate inputs"
- [SEMANTIC] Implicit tool assumptions without declaration
- [SEMANTIC] No fallback for network-dependent operations
