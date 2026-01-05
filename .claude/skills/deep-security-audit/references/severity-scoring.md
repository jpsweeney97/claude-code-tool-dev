# Severity Scoring

Criteria for assigning severity levels to security findings. Severity should reflect exploitability and impact, not just the presence of a vulnerability.

---

## Severity Levels

| Severity | Definition |
|----------|------------|
| **Critical** | Immediate, severe impact with easy exploitation |
| **High** | Significant impact or easy exploitation (not both Critical) |
| **Medium** | Moderate impact requiring specific conditions |
| **Low** | Limited impact or difficult exploitation |
| **Informational** | Best practice deviation with no direct security impact |

---

## Critical Severity

### Criteria (ANY of these)
- Remote Code Execution (RCE)
- Authentication bypass (unauthenticated access to protected resources)
- Full database compromise (arbitrary read/write)
- Complete system takeover
- Hardcoded credentials in public repository
- Unauthenticated admin access

### Examples

**SQL Injection with admin access:**
- Attacker can read/modify any data
- No authentication required
- Severity: **Critical**

**Hardcoded API key in public GitHub repo:**
- Key provides access to production systems
- Anyone can find and use it
- Severity: **Critical**

**Authentication bypass via parameter manipulation:**
- Adding `?admin=true` grants admin access
- No credentials needed
- Severity: **Critical**

### NOT Critical (common mistakes)
- SQL injection in authenticated admin-only endpoint → High (requires auth)
- XSS that only affects the attacker's own session → Low
- Hardcoded test credentials in non-production code → Informational

---

## High Severity

### Criteria (ANY of these)
- Privilege escalation (user to admin, or user to other user)
- Significant data exposure (PII, financial data, credentials)
- Account takeover (via password reset, session hijacking)
- Stored XSS affecting other users
- Server-Side Request Forgery (SSRF) with internal network access
- Insecure Direct Object Reference (IDOR) accessing sensitive data

### Examples

**IDOR accessing other users' data:**
- Changing user_id parameter shows other users' profiles
- Requires authentication but not authorization
- Severity: **High**

**JWT with weak/guessable secret:**
- Attacker can forge tokens
- Requires knowledge of the weak secret
- Severity: **High**

**Password reset token prediction:**
- Tokens are based on timestamp + user ID
- Attacker can generate valid reset links
- Severity: **High**

### NOT High (common mistakes)
- Self-XSS (only affects the user who triggers it) → Low
- IDOR exposing non-sensitive data (usernames) → Medium
- Theoretical SQL injection with no proof of concept → Medium/Possible

---

## Medium Severity

### Criteria (ANY of these)
- Limited impact requiring specific conditions
- User interaction required for exploitation
- Data exposure of limited sensitivity
- CSRF on sensitive but non-critical actions
- Reflected XSS (requires victim to click link)
- Information disclosure of internal paths/versions

### Examples

**Stored XSS visible only to admin users:**
- Requires admin to view attacker content
- Limited audience reduces impact
- Severity: **Medium**

**CSRF on profile update:**
- Attacker can change victim's profile info
- Requires victim to visit attacker page while authenticated
- Severity: **Medium**

**Path traversal limited to non-sensitive files:**
- Can read application source code but not credentials
- Limited to specific directory
- Severity: **Medium**

### NOT Medium (common mistakes)
- Reflected XSS in error messages that are also logged → May be High if log injection possible
- CSRF on logout → Low (limited impact)
- Information disclosure of public information → Informational

---

## Low Severity

### Criteria (ANY of these)
- Information disclosure with no direct security impact
- Missing security headers (without demonstrated exploit)
- Hardening recommendations
- Defense-in-depth gaps
- Verbose error messages (without sensitive data)
- Clickjacking on non-sensitive pages

### Examples

**Server version disclosure:**
- Response headers reveal Apache 2.4.41
- Helps attacker identify potential CVEs
- Severity: **Low**

**Missing security headers (X-Frame-Options, CSP):**
- Reduces defense-in-depth
- No immediate exploitable vulnerability
- Severity: **Low**

**Session cookies without SameSite attribute:**
- Modern browsers default to Lax
- Reduces CSRF protection but not immediate vulnerability
- Severity: **Low**

### NOT Low (common mistakes)
- Missing rate limiting on login → Medium/High (enables brute force)
- Missing HTTPS (if handling sensitive data) → Medium/High
- Debug mode enabled → Medium/High (may expose sensitive info)

---

## Informational

### Criteria
- Best practice deviation with no security impact
- Cosmetic issues
- Suggestions for improvement
- Deprecated but not vulnerable code
- Code quality issues that don't affect security

### Examples

**Using SHA-256 instead of SHA-3:**
- SHA-256 is still secure
- SHA-3 is newer but not required
- Severity: **Informational**

**Comments containing TODO: fix security:**
- May indicate awareness of issue
- Comment itself is not a vulnerability
- Severity: **Informational**

**Deprecated API usage (still functional and secure):**
- Should be updated but not vulnerable
- No immediate security impact
- Severity: **Informational**

---

## Severity Decision Matrix

| Factor | Increases Severity | Decreases Severity |
|--------|-------------------|-------------------|
| **Authentication** | None required | Requires valid credentials |
| **Authorization** | Any user can exploit | Requires specific role |
| **User interaction** | None required | Requires victim action |
| **Data sensitivity** | PII, credentials, financial | Public or internal-only |
| **Scope** | Affects all users | Affects only attacker |
| **Reversibility** | Permanent damage possible | Easily reversible |
| **Detectability** | Hard to detect | Obvious in logs |

---

## Severity Adjustment Guidelines

### Upgrade severity when:
- Vulnerability is part of a chain that increases impact
- Multiple instances of same vulnerability exist
- Vulnerability affects critical business function
- No compensating controls exist

### Downgrade severity when:
- Compensating controls significantly reduce risk
- Vulnerability only affects non-production systems
- Exploitation requires unlikely conditions
- Impact is limited by application design

### Document adjustments
Always explain severity adjustments:
```markdown
**Severity:** High (upgraded from Medium)
**Adjustment Reason:** This XSS vulnerability, combined with VULN-003 (CSRF),
allows account takeover without user interaction beyond visiting a page.
```

---

## Common Severity Mistakes

| Finding | Common Mistake | Correct Severity | Reason |
|---------|---------------|------------------|--------|
| SQL injection (authenticated) | Critical | High | Requires authentication |
| Self-XSS | Medium | Low | Only affects attacker |
| Missing HTTPS | Low | Medium/High | Depends on data handled |
| Debug mode | Low | Medium | Often exposes sensitive info |
| Outdated dependency (no CVE) | Medium | Informational | No known vulnerability |
| Hardcoded test credentials | Critical | Varies | Depends on what they access |
