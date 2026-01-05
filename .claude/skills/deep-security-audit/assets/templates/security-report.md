# Security Audit Report: [PROJECT_NAME]

**Version:** 1.0
**Date:** [DATE]
**Auditor:** Claude Code (deep-security-audit skill)
**Scope:** [BRIEF_SCOPE_DESCRIPTION]

---

## Executive Summary

### Overview

[1-2 paragraph summary of what was audited and key findings]

### Risk Summary

| Severity | Count | Status |
|----------|-------|--------|
| Critical | 0 | - |
| High | 0 | - |
| Medium | 0 | - |
| Low | 0 | - |
| Informational | 0 | - |

### Key Findings

1. **[FINDING_TITLE]** (Critical/High) — [One-line summary]
2. **[FINDING_TITLE]** (Critical/High) — [One-line summary]
3. **[FINDING_TITLE]** (Medium) — [One-line summary]

### Recommendations Priority

| Priority | Action | Findings |
|----------|--------|----------|
| Immediate | [Action description] | VULN-001, VULN-002 |
| Short-term | [Action description] | VULN-003 |
| Long-term | [Action description] | VULN-004, VULN-005 |

---

## Audit Scope

### Included

- **Codebase:** [repository/path]
- **Languages:** [e.g., Python, JavaScript, Go]
- **Frameworks:** [e.g., Django, React, Express]
- **Components:** [List of modules/services audited]

### Excluded

- [What was explicitly out of scope]
- [Dependencies not reviewed in depth]
- [Runtime/infrastructure concerns]

### Methodology

This audit used static code analysis with four security perspectives:

1. **Attacker** — Data flow from untrusted input to sensitive sinks
2. **Controls** — Validation, sanitization, encoding, access checks
3. **Auditor** — Systematic CWE coverage across 10 security dimensions
4. **Design Review** — Trust boundaries, separation of concerns, secure defaults

### Limitations

This is a static code audit. The following require runtime verification:
- Dynamic dispatch behavior
- Configuration-dependent security controls
- Race condition exploitability
- External service interactions

---

## Coverage Matrix

|  | [Area 1] | [Area 2] | [Area 3] | [Area 4] |
|--|----------|----------|----------|----------|
| **Input Validation** | | | | |
| **Authentication** | | | | |
| **Authorization** | | | | |
| **Session Management** | | | | |
| **Cryptography** | | | | |
| **Error Handling** | | | | |
| **Logging** | | | | |
| **Output Encoding** | | | | |
| **Configuration** | | | | |
| **Dependencies** | | | | |

**Legend:** Check = Examined, no issues | Warning = Issues found (see findings) | X = Not examined | N/A = Not applicable

---

## Findings

### Critical Severity

#### VULN-001: [Title]

| Field | Value |
|-------|-------|
| **CWE** | CWE-XXX |
| **OWASP** | A0X: Category |
| **Confidence** | Confirmed/Probable/Possible |
| **Location** | `path/to/file.py:123` |

**Description:**
[What the vulnerability is]

**Data Flow:**
```
Source: [where untrusted data enters]
  -> [propagation step]
  -> [propagation step]
Sink: [where it reaches sensitive operation]
```

**Impact:**
[What an attacker could achieve]

**Remediation:**
[How to fix it with code example if applicable]

**Verification Method:**
[How this was confirmed - data flow trace, pattern match, etc.]

---

### High Severity

[Same format as Critical]

---

### Medium Severity

[Same format as Critical]

---

### Low Severity

[Same format as Critical, may be abbreviated]

---

### Informational

[Brief notes on best practice deviations without security impact]

---

## Agent Perspectives Summary

### Attacker Perspective

**Attack Vectors Identified:**
- [Vector 1]: [Brief description]
- [Vector 2]: [Brief description]

**Data Flow Chains:**
[Summary of source-to-sink traces found]

### Controls Perspective

**Controls Present:**
- [Control 1]: [Where and how implemented]
- [Control 2]: [Where and how implemented]

**Controls Missing:**
- [Missing control 1]: [Where it should be]
- [Missing control 2]: [Where it should be]

### Auditor Perspective

**CWE Coverage:**
- CWEs checked: [count]
- CWEs with findings: [list]
- CWEs clear: [list]

**Systematic Gaps:**
[Any areas that couldn't be fully examined and why]

### Design Review Perspective

**Trust Boundaries:**
[Assessment of trust boundary definition and enforcement]

**Architecture Concerns:**
[Any design-level security issues]

---

## Cross-Validation Results

### Finding Correlation

| Finding | Attacker | Controls | Auditor | Design | Confidence |
|---------|----------|----------|---------|--------|------------|
| VULN-001 | Source found | No sanitization | CWE-89 match | Trust boundary crossed | Confirmed |
| VULN-002 | Path traced | Weak control | CWE-79 match | Output context wrong | Probable |

### Disputed Findings

[Any findings where agents disagreed, with resolution]

### False Positive Analysis

[Findings initially flagged but determined to be false positives, with reasoning]

---

## Remediation Roadmap

### Phase 1: Immediate (Critical/High)

| Finding | Remediation | Effort | Owner |
|---------|-------------|--------|-------|
| VULN-001 | [Action] | [Est.] | [TBD] |
| VULN-002 | [Action] | [Est.] | [TBD] |

### Phase 2: Short-term (Medium)

| Finding | Remediation | Effort | Owner |
|---------|-------------|--------|-------|
| VULN-003 | [Action] | [Est.] | [TBD] |

### Phase 3: Hardening (Low/Informational)

| Finding | Remediation | Effort | Owner |
|---------|-------------|--------|-------|
| VULN-004 | [Action] | [Est.] | [TBD] |

---

## Appendices

### A. Files Reviewed

```
[List of files examined, possibly with line counts]
```

### B. Tools and References

- CWE Top 25 (2024): https://cwe.mitre.org/top25/
- OWASP Top 10 (2021): https://owasp.org/Top10/
- [Framework-specific security guides referenced]

### C. Glossary

| Term | Definition |
|------|------------|
| CWE | Common Weakness Enumeration - standardized vulnerability taxonomy |
| OWASP | Open Web Application Security Project |
| IDOR | Insecure Direct Object Reference |
| SSRF | Server-Side Request Forgery |
| XSS | Cross-Site Scripting |

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | [DATE] | Initial audit |

---

*Report generated using deep-security-audit skill*
