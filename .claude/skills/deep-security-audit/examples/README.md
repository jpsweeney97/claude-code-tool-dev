# Deep Security Audit Examples

Worked examples demonstrating the deep-security-audit methodology.

## Available Examples

### OWASP Juice Shop Audit (2025-12-31)

A comprehensive security audit of OWASP Juice Shop v19.1.1, an intentionally vulnerable application with 110 documented security challenges.

**Methodology Applied:**
- 4 agents deployed in parallel (Attacker, Controls, Auditor, Design Review)
- Medium calibration (full cross-validation)
- CWE primary taxonomy with OWASP mapping

**Results:**
- 76% recall on static-detectable vulnerabilities
- 0% false positive rate
- Vulnerabilities found across 10+ CWE categories
- SQL Injection, NoSQL Injection, XSS, XXE, Code Injection, SSRF, Path Traversal confirmed

**Key Findings:**
1. All 5 trust boundaries inadequate
2. 15 of 25 security controls flawed
3. 6 expected controls missing entirely
4. Complete coverage matrix achieved

**Full Report:** [validation-results-juice-shop.md](validation-results-juice-shop.md)

---

## Using These Examples

Each example demonstrates:
1. Pre-flight phase (scope definition, threat model)
2. Agent deployment (4 security perspectives in parallel)
3. Cross-validation (reconciling findings, eliminating false positives)
4. Synthesis (vulnerability report with remediation)

Reference the full methodology in [../SKILL.md](../SKILL.md).
