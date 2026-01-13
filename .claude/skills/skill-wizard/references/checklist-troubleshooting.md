# Troubleshooting Checklist

## Structural
- [MUST] At least one failure mode documented
- [MUST] Each failure mode has: symptoms, likely causes, next steps

## Semantic
- [MUST] Symptoms describe what user observes (error message, behavior)
- [MUST] Causes are specific (not "something went wrong")
- [MUST] Next steps are actionable (specific commands, inspections)
- [SHOULD] At least one anti-pattern phrased as temptation to avoid
  (e.g., "Don't just disable the test")
- [HIGH-MUST] Includes rollback/escape hatch guidance for partial success

## Anti-patterns
- [SEMANTIC] Generic causes: "configuration issue", "environment problem"
- [SEMANTIC] Vague next steps: "investigate further", "check the logs"
