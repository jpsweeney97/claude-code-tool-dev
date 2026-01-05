# Security Audit Validation Template

**Purpose:** Validate the deep-security-audit skill against the Framework for Rigor with security-specific assessment criteria. This template extends the core validation template with CWE coverage tracking, OWASP mapping, agent cross-validation, and static analysis limitations.

**Reference:** `templates/validation-core.md` (core template), `skills/deep-security-audit/SKILL.md` (skill definition)

---

## Summary

> Security-specific metrics: recall on static-detectable vulnerabilities, precision on confirmed findings, CWE category coverage.

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Recall (static-detectable) | ≥80% | [%] | Pass/Fail/Close |
| Precision (Confirmed FP) | ≤10% | [%] | Pass/Fail/Close |
| CWE Coverage | 15/15 | [n]/15 | Pass/Fail/Close |

**Verdict:** [Validated for X with Y caveats / Not validated due to Z]

---

## Metadata

**Skill:** deep-security-audit @ [version]
**Target:** [test subject / codebase]
**Date:** [YYYY-MM-DD]

### Stakes Assessment

| Factor | Score | Rationale |
|--------|-------|-----------|
| Reversibility | 3 | Security findings affect production decisions |
| Blast radius | [1-3] | [scope of impact if wrong] |
| Precedent | [1-3] | [will this inform future validations?] |
| Visibility | [1-3] | [who sees these results?] |
| **Total** | [6-12] | [Medium (7-9) / Deep (10-12)] |

### Validation Types

- [ ] **Benchmark:** [N challenges from source with known vulnerabilities]
- [ ] **Expert:** [role] assessed [criteria]
- [ ] **Consistency:** [what cross-checked across runs/agents]

### Method

| Element | Value |
|---------|-------|
| Agents | Attacker, Controls, Auditor, Design Review (4) |
| Model | [model identifier] |
| Deployment | parallel |
| Runs | [count] |

---

## Skill Context

| Element | Value |
|---------|-------|
| Purpose | Static code security review using parallel agents with four perspectives |
| Calibration | [Light / Medium / Deep] |
| Success looks like | High recall on static-detectable vulnerabilities, low false positive rate, complete CWE coverage |

---

## Scope

**In:**
- [Code areas examined]
- [Vulnerability categories covered]
- [CWE categories targeted]

**Out:**
- [Runtime-only vulnerabilities]
- [Infrastructure/network security]
- [Dynamic testing requirements]

### Limitations

| Source | Constraint |
|--------|------------|
| Target | [e.g., intentionally vulnerable app, limited categories] |
| Skill | Static analysis only — cannot verify runtime behavior |
| Method | [e.g., single run, specific calibration level] |
| Time | [e.g., time-boxed analysis] |

---

## Assessment

### Validity

> Are conclusions justified by evidence?

#### Evidence Quality

| Principle | Question | Assessment |
|-----------|----------|------------|
| **Adequate Evidence** | Data flows traced for each finding? | [Yes/Partial/No] |
| | CWE classifications correct? | [Yes/Partial/No] |
| | Location citations accurate (file:line)? | [Yes/Partial/No] |
| **Sound Inference** | Severity matches exploitability? | [Yes/Partial/No] |
| | Right findings for right reasons? | [Yes/Partial/No] |

#### Recall by CWE Category

| CWE | Name | Expected | Found | Rate |
|-----|------|----------|-------|------|
| CWE-89 | SQL Injection | [n] | [n] | [%] |
| CWE-79 | Cross-site Scripting (XSS) | [n] | [n] | [%] |
| CWE-94 | Code Injection | [n] | [n] | [%] |
| CWE-22 | Path Traversal | [n] | [n] | [%] |
| CWE-918 | Server-Side Request Forgery (SSRF) | [n] | [n] | [%] |
| CWE-611 | XXE | [n] | [n] | [%] |
| CWE-798 | Hardcoded Credentials | [n] | [n] | [%] |
| CWE-347 | Improper JWT Verification | [n] | [n] | [%] |
| CWE-328 | Weak Hash (Reversible) | [n] | [n] | [%] |
| CWE-639 | Authorization Bypass (IDOR) | [n] | [n] | [%] |
| CWE-862 | Missing Authorization | [n] | [n] | [%] |
| CWE-601 | Open Redirect | [n] | [n] | [%] |
| CWE-943 | NoSQL Injection | [n] | [n] | [%] |
| CWE-1321 | Prototype Pollution | [n] | [n] | [%] |
| CWE-502 | Deserialization of Untrusted Data | [n] | [n] | [%] |
| **TOTAL** | | [n] | [n] | **[%]** |

#### Recall by OWASP Top 10

| OWASP | Category | Expected | Found | Rate |
|-------|----------|----------|-------|------|
| A01:2021 | Broken Access Control | [n] | [n] | [%] |
| A02:2021 | Cryptographic Failures | [n] | [n] | [%] |
| A03:2021 | Injection | [n] | [n] | [%] |
| A04:2021 | Insecure Design | [n] | [n] | [%] |
| A05:2021 | Security Misconfiguration | [n] | [n] | [%] |
| A06:2021 | Vulnerable Components | [n] | [n] | [%] |
| A07:2021 | Auth Failures | [n] | [n] | [%] |
| A08:2021 | Software/Data Integrity | [n] | [n] | [%] |
| A09:2021 | Logging Failures | [n] | [n] | [%] |
| A10:2021 | SSRF | [n] | [n] | [%] |
| **TOTAL** | | [n] | [n] | **[%]** |

#### Precision

| Confidence | Count | False Positives | Rate |
|------------|-------|-----------------|------|
| Confirmed | [n] | [n] | [%] |
| Probable | [n] | [n] | [%] |
| Possible | [n] | [n] | [%] |
| Requires Runtime | [n] | N/A | N/A |

#### Cross-Validation by Agent

| Category | Attacker | Controls | Auditor | Design | Consensus |
|----------|----------|----------|---------|--------|-----------|
| Injection | [finding count] | [finding count] | [finding count] | [finding count] | [%] |
| Auth/AuthZ | [finding count] | [finding count] | [finding count] | [finding count] | [%] |
| Crypto | [finding count] | [finding count] | [finding count] | [finding count] | [%] |
| Data Flow | [finding count] | [finding count] | [finding count] | [finding count] | [%] |

**Conflict Resolution:** [Document any conflicts and how resolved]

**Validity Verdict:** [Strong / Adequate / Weak]

---

### Completeness

> Did the skill examine everything relevant?

#### Scope Appropriateness

| Check | Assessment |
|-------|------------|
| Scope matches stated purpose? | [Yes/No] |
| Hard/complex areas included? | [Yes/No] |
| Exclusions justified? | [Yes/No] |

#### Security Coverage Matrix (10 Dimensions)

| Dimension | [Area 1] | [Area 2] | [Area 3] | [Area 4] | [Area 5] |
|-----------|----------|----------|----------|----------|----------|
| Input Validation | [status] | [status] | [status] | [status] | [status] |
| Authentication | [status] | [status] | [status] | [status] | [status] |
| Authorization | [status] | [status] | [status] | [status] | [status] |
| Session Mgmt | [status] | [status] | [status] | [status] | [status] |
| Cryptography | [status] | [status] | [status] | [status] | [status] |
| Error Handling | [status] | [status] | [status] | [status] | [status] |
| Logging | [status] | [status] | [status] | [status] | [status] |
| Output Encoding | [status] | [status] | [status] | [status] | [status] |
| Configuration | [status] | [status] | [status] | [status] | [status] |
| Dependencies | [status] | [status] | [status] | [status] | [status] |

**Legend:** FINDING = vulnerability found, REVIEWED = examined clean, N/A = not applicable, PARTIAL = incomplete coverage

#### Vulnerable Dependencies

| Package | Version | CVE/Vulnerability | Severity |
|---------|---------|-------------------|----------|
| [package] | [version] | [CVE-XXXX-XXXXX or description] | [Critical/High/Medium/Low] |
| [package] | [version] | [CVE-XXXX-XXXXX or description] | [Critical/High/Medium/Low] |

#### Calibration Fit

| Skill Calibration | Observed Behavior | Match? |
|-------------------|-------------------|--------|
| [Light/Medium/Deep] | [actual depth and thoroughness observed] | [Yes/No] |

**Completeness Verdict:** [Strong / Adequate / Weak]

---

### Transparency

> Can others verify this work?

#### Data Flow Traces

| Finding ID | Source | Propagation | Sink | Verified? |
|------------|--------|-------------|------|-----------|
| [VULN-001] | [input point] | [path through code] | [vulnerable operation] | [Yes/No] |
| [VULN-002] | [input point] | [path through code] | [vulnerable operation] | [Yes/No] |

#### Documentation

| Check | Assessment |
|-------|------------|
| Methodology recorded? | [Yes/Partial/No] |
| Agent perspectives documented? | [Yes/Partial/No] |
| Cross-validation process recorded? | [Yes/Partial/No] |

#### Traceability

| Check | Assessment |
|-------|------------|
| Each finding cites source (file:line)? | [Yes/Partial/No] |
| CWE ID assigned to each finding? | [Yes/Partial/No] |
| Confidence explicitly stated? | [Yes/Partial/No] |

#### Honesty

| Check | Assessment |
|-------|------------|
| Negative findings documented? | [Yes/Partial/No] |
| Static analysis limitations acknowledged? | [Yes/Partial/No] |
| "Requires Runtime" used appropriately (≤20%)? | [Yes/Partial/No] |
| Counter-evidence actively sought? | [Yes/Partial/No] |

**Transparency Verdict:** [Strong / Adequate / Weak]

---

### Reproducibility

> Does the skill produce consistent results across runs?

| Run | Key Findings | CWE Coverage | Variance from Run 1 |
|-----|--------------|--------------|---------------------|
| 1 | [summary of major findings] | [n]/15 | — |
| 2 | [summary of major findings] | [n]/15 | [delta description] |
| 3 | [summary of major findings] | [n]/15 | [delta description] |

**Reproducibility Verdict:** [High / Medium / Low]

---

## Overall Verdict

| Dimension | Verdict |
|-----------|---------|
| Validity | [Strong / Adequate / Weak] |
| Completeness | [Strong / Adequate / Weak] |
| Transparency | [Strong / Adequate / Weak] |
| Reproducibility | [High / Medium / Low] |

**Validation Result:** [Validated / Validated with Caveats / Not Validated]

**Caveats:**
- [Caveat 1 if any]
- [Caveat 2 if any]
- None

---

## Findings

### By CWE

| ID | CWE | Finding | Severity | Confidence | Location |
|----|-----|---------|----------|------------|----------|
| VULN-001 | CWE-[nnn] | [description] | [Critical/High/Medium/Low] | [Confirmed/Probable/Possible/Requires Runtime] | [file:line] |
| VULN-002 | CWE-[nnn] | [description] | [Critical/High/Medium/Low] | [Confirmed/Probable/Possible/Requires Runtime] | [file:line] |

### By Agent

| Agent | Findings | Confirmed | Probable | Possible |
|-------|----------|-----------|----------|----------|
| Attacker | [n] | [n] | [n] | [n] |
| Controls | [n] | [n] | [n] | [n] |
| Auditor | [n] | [n] | [n] | [n] |
| Design Review | [n] | [n] | [n] | [n] |

### Negative Findings

> Document what was sought but not found.

| CWE | Category | What Was Searched | Where | Result |
|-----|----------|-------------------|-------|--------|
| CWE-[nnn] | [category] | [specific pattern sought] | [files/locations] | Not found |
| CWE-[nnn] | [category] | [specific pattern sought] | [files/locations] | Not found |

---

## Conclusions

### Strengths

1. [Strength with supporting evidence]
2. [Strength with supporting evidence]
3. [Strength with supporting evidence]

### Weaknesses

1. [Weakness with supporting evidence]
2. [Weakness with supporting evidence]

### Recommendations

| Priority | Recommendation | Rationale |
|----------|----------------|-----------|
| High | [specific action] | [why this matters] |
| Medium | [specific action] | [why this matters] |
| Low | [specific action] | [why this matters] |

---

## Appendix

### Files Examined

| Directory | Count | Depth |
|-----------|-------|-------|
| [dir] | [n] | [Detailed / Surface] |
| [dir] | [n] | [Detailed / Surface] |
| **Total** | [n] | |

### Static Analysis Limitations

This validation acknowledges inherent limitations of static code analysis:

| Limitation | Impact on Validation |
|------------|---------------------|
| No code execution | Cannot verify runtime behavior, timing attacks |
| No dynamic dispatch resolution | May miss vulnerabilities in dynamically called code |
| No configuration verification | Cannot confirm runtime config values |
| Framework magic | May miss or over-report based on framework auto-protections |
| Seed/test data | Cannot detect default credentials in runtime data |

**Vulnerability classes requiring runtime testing:**
- Race conditions and timing attacks
- Memory corruption (in native code)
- Configuration-dependent vulnerabilities
- Framework-specific runtime protections
- Dynamic code loading/evaluation paths

### References

- `templates/validation-core.md` — Core validation template
- `skills/deep-security-audit/SKILL.md` — Skill definition and methodology
- `skills/deep-security-audit/references/coverage-dimensions.md` — 10 security dimensions
- Framework for Rigor — Assessment dimensions and principles
