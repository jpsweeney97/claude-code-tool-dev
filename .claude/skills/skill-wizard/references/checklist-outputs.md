# Outputs Checklist

## Structural
- [MUST] Artifacts sub-section exists
- [MUST] Definition of Done sub-section exists

## Semantic
- [MUST] At least one artifact defined (files, patches, reports, commands)
- [MUST] At least one objective DoD check that is:
  - Artifact existence/shape, OR
  - Deterministic query/invariant, OR
  - Executable check with expected output, OR
  - Deterministic logical condition
- [MUST] DoD checks are verifiable without "reading the agent's mind"
- [SHOULD] Calibration: outputs distinguish Verified/Inferred/Assumed claims

## Anti-patterns (FAIL-level)
- [SEMANTIC] "Verify it works" - not objective
- [SEMANTIC] "Ensure quality" - not measurable
- [SEMANTIC] "Make sure tests pass" without specifying which tests
- [SEMANTIC] "Check for errors" without specifying where/how
