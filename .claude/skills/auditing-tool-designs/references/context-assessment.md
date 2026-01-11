# Context Assessment Framework

This framework calibrates audit severity based on deployment context. Applied before lenses execute.

## Interactive Assessment Questions

Three questions determine calibration level:

### Q1: Deployment Scope
> "Who will use this {{ARTIFACT_TYPE}}?"

| Answer | Score | Meaning |
|--------|-------|---------|
| Personal (just me) | +1 | No external users; mistakes affect only developer |
| Team (internal users) | +2 | Trusted users; mistakes affect productivity |
| Public (external consumers) | +3 | Untrusted users; mistakes affect security/reputation |

### Q2: Input Trust Level
> "Who controls the inputs this tool will process?"

| Answer | Score | Meaning |
|--------|-------|---------|
| Developer-controlled | +1 | Config files, env vars, version-controlled data |
| Internal users | +2 | Team members, authenticated users |
| External/untrusted | +3 | User uploads, public API, external data |

### Q3: Failure Impact
> "What happens if this tool has a bug or security issue?"

| Answer | Score | Meaning |
|--------|-------|---------|
| Learning/experiment | +1 | No real impact; safe to fail |
| Internal tool | +2 | Team inconvenience; recoverable |
| Production system | +3 | Data loss, security breach, outage |

## Calibration Levels

Sum the scores (range: 3-9):

| Score | Level | Behavior |
|-------|-------|----------|
| 3-5 | Light | Focus on correctness; skip theoretical security risks |
| 6-7 | Standard | Full methodology; normal thresholds |
| 8-9 | Deep | Strict thresholds; adversarial mindset |

## Severity Calibration Matrix

Severity thresholds vary by context:

| Context | Critical | Major | Minor |
|---------|----------|-------|-------|
| **Light** (trusted inputs, personal) | N/A—no external attack surface | Design flaw that breaks functionality | Style/convention deviation |
| **Standard** (mixed trust, team) | Privilege escalation within trust boundary | Feature doesn't work as designed | Non-compliance with standards |
| **Deep** (untrusted inputs, public) | Exploitable by external actors | Requires elevated access to exploit | Theoretical with no plausible path |

## Exploitability Standards

Security findings require exploitability assessment based on input trust level.

| Input Source | Standard |
|--------------|----------|
| Developer-controlled (env vars, config) | Admin already has access; not externally exploitable |
| Version-controlled files | Attacker needs commit access; not externally exploitable |
| User input (forms, API) | Externally exploitable; full security review required |
| External data (APIs, uploads) | High risk; assume hostile input |

**Anti-pattern:** Flagging developer-controlled configuration as "path traversal" or "injection" without demonstrating an external attack path.

## Template Variables

After assessment, populate these for lens injection:

### {{CONTEXT_ASSESSMENT}}
```
Deployment scope: [Personal/Team/Public]
Input trust level: [Trusted/Partial/Untrusted]
Failure impact: [Low/Medium/High]
Calibration: [Light/Standard/Deep] (score: X)
```

### {{SEVERITY_CALIBRATION}}
```
For this [Light/Standard/Deep] audit:
- Critical: [context-specific definition from matrix]
- Major: [context-specific definition from matrix]
- Minor: [context-specific definition from matrix]
```
