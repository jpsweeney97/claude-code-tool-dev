# Verification Checklist

## Structural
- [MUST] Quick check sub-section exists
- [SHOULD] Deep check sub-section exists (required for High risk)

## Semantic
- [MUST] Quick check is concrete and executable/observable
- [MUST] Quick check measures the primary success property (not just proxy)
- [MUST] Quick check specifies expected result shape
- [MUST] Failure interpretation: what to do if check fails
- [HIGH-MUST] At least two verification modes (quick + deep)
- [SHOULD] No-network fallback for verification when feasible

## Calibration
- [MUST] Skill instructs "Not run (reason)" reporting for skipped checks
- [SHOULD] Verification ladder (quick -> narrow -> broad) for Medium+ risk

## Anti-patterns
- [SEMANTIC] "Tests pass" without specifying which tests or showing output
- [SEMANTIC] Proxy-only verification (compiles but behavior unchecked)
- [SEMANTIC] No failure handling ("if check fails, continue anyway")

## Command Robustness
- [MUST] Use literal paths in verification commands, not glob patterns
  - Bad: `test -f docs/plans/*-review.md` (glob may match 0, 1, or N files)
  - Good: `test -f "$REPORT_PATH"` with note to substitute actual path
- [MUST] Quote variables in shell commands to handle spaces
  - Bad: `grep -q "pattern" $FILE`
  - Good: `grep -q "pattern" "$FILE"`
- [SHOULD] Verification commands should be deterministic (same input = same result)
- [SHOULD] Deep check criteria must be objectively verifiable (not "looks correct")
