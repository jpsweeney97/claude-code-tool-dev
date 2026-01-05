# CWE Reference

Common Weakness Enumeration (CWE) reference for static code security audit.

**Scope:** This document provides detection patterns for high-priority CWEs most amenable to static analysis. The mapping table covers 17 common CWEs; detailed patterns are provided for 12 that are most detectable through code review.

**Complete reference:** For the full CWE Top 25 (updated annually), see https://cwe.mitre.org/top25/

**Last reviewed:** 2024 CWE Top 25

---

## Quick Reference: CWE to OWASP Mapping

| CWE | Name | OWASP 2021 |
|-----|------|------------|
| CWE-79 | Cross-site Scripting (XSS) | A03: Injection |
| CWE-89 | SQL Injection | A03: Injection |
| CWE-78 | OS Command Injection | A03: Injection |
| CWE-20 | Improper Input Validation | A03: Injection |
| CWE-22 | Path Traversal | A01: Broken Access Control |
| CWE-352 | Cross-Site Request Forgery | A01: Broken Access Control |
| CWE-434 | Unrestricted File Upload | A04: Insecure Design |
| CWE-287 | Improper Authentication | A07: Identification & Auth Failures |
| CWE-798 | Hardcoded Credentials | A07: Identification & Auth Failures |
| CWE-862 | Missing Authorization | A01: Broken Access Control |
| CWE-863 | Incorrect Authorization | A01: Broken Access Control |
| CWE-502 | Deserialization of Untrusted Data | A08: Software & Data Integrity |
| CWE-611 | XXE | A05: Security Misconfiguration |
| CWE-918 | Server-Side Request Forgery | A10: SSRF |
| CWE-327 | Broken Crypto Algorithm | A02: Cryptographic Failures |
| CWE-330 | Insufficient Randomness | A02: Cryptographic Failures |
| CWE-532 | Sensitive Info in Log Files | A09: Security Logging Failures |

---

## CWE-79: Cross-site Scripting (XSS)

**Description:** Improper neutralization of user input during web page generation.

**Types:**
- Reflected: Input immediately returned in response
- Stored: Input saved and displayed to other users
- DOM-based: Client-side JavaScript vulnerability

**Static Detection Patterns:**
- User input rendered in HTML without encoding
- Template safe filters (|safe, raw, html_safe)
- innerHTML assignments with user data
- String concatenation into HTML responses

**Remediation:**
- Use framework auto-escaping (don't disable it)
- Apply context-appropriate encoding
- Use Content-Security-Policy headers

---

## CWE-89: SQL Injection

**Description:** Improper neutralization of special elements used in SQL commands.

**Static Detection Patterns:**
- String concatenation/formatting into SQL queries
- User input in query without parameterization
- Dynamic table/column names from user input
- ORM raw query methods with user input

**Remediation:**
- Use parameterized queries (prepared statements)
- Use ORM methods that parameterize automatically
- Validate input type/format before use

---

## CWE-78: OS Command Injection

**Description:** Improper neutralization of special elements used in OS commands.

**Static Detection Patterns:**
- Shell execution functions with user input in arguments
- subprocess with shell=True and user input
- String concatenation into command strings
- Backtick execution in scripts

**Remediation:**
- Avoid shell commands when possible (use libraries)
- Use subprocess with shell=False and argument list
- Validate/sanitize input against allowlist
- Use proper escaping if shell is necessary

---

## CWE-22: Path Traversal

**Description:** Improper limitation of pathname to restricted directory.

**Static Detection Patterns:**
- User input in file paths without validation
- Direct use of user input in file open/read/write
- Path construction without checking result stays in allowed directory
- Missing check for ".." sequences

**Remediation:**
- Use realpath() and verify within allowed directory
- Reject paths containing ".."
- Use allowlist of permitted files
- Chroot or containerize file access

---

## CWE-352: Cross-Site Request Forgery (CSRF)

**Description:** Web application does not verify request was intentionally made by user.

**Static Detection Patterns:**
- State-changing operations on GET requests
- Missing CSRF token validation
- CSRF protection disabled (@csrf_exempt, etc.)
- SameSite cookie attribute not set

**Remediation:**
- Enable framework CSRF protection
- Use anti-CSRF tokens
- Set SameSite=Strict on session cookies
- Verify Origin/Referer headers

---

## CWE-287: Improper Authentication

**Description:** System does not properly verify claimed identity.

**Static Detection Patterns:**
- Authentication bypass conditions
- Weak password comparison
- Missing authentication on protected endpoints
- Predictable session/token generation

**Remediation:**
- Require authentication on all protected routes
- Use framework authentication mechanisms
- Implement proper session management
- Use timing-safe comparison for credentials

---

## CWE-798: Hardcoded Credentials

**Description:** Credentials embedded in source code.

**Static Detection Patterns:**
- Variables named password, secret, key, token with string literals
- API keys in code (AWS, Stripe patterns like AKIA...)
- Database connection strings with passwords
- JWT secrets as string literals

**Remediation:**
- Use environment variables
- Use secret management services
- Use configuration files excluded from version control
- Rotate any exposed credentials immediately

---

## CWE-862: Missing Authorization

**Description:** Software does not perform authorization check.

**Static Detection Patterns:**
- Missing @require_role or similar decorators
- Direct object access without ownership check
- Admin functions without admin check
- API endpoints without permission validation

**Remediation:**
- Check authorization on every protected resource
- Verify ownership for user-specific resources
- Use role-based access control
- Centralize authorization logic

---

## CWE-502: Deserialization of Untrusted Data

**Description:** Deserializing data from untrusted sources without verification.

**Static Detection Patterns:**
- Unsafe deserialization functions with user input (pickle, yaml.load, unserialize)
- No signature verification before deserialization
- Direct deserialization of request body

**Remediation:**
- Avoid deserializing untrusted data
- Use safe serialization formats (JSON with schema validation)
- If unsafe formats needed, use cryptographic signing
- Use safe loaders (yaml.safe_load)

---

## CWE-611: XML External Entity (XXE)

**Description:** XML parser processes external entity references in untrusted XML.

**Static Detection Patterns:**
- XML parsing without disabling external entities
- etree.parse() without secure configuration
- SOAP/XML-RPC services accepting user XML

**Remediation:**
- Disable external entity processing
- Use defusedxml or similar secure parsers
- Configure parser with resolve_entities=False
- Consider using JSON instead of XML

---

## CWE-918: Server-Side Request Forgery (SSRF)

**Description:** Server makes requests to URLs specified by attacker.

**Static Detection Patterns:**
- User input in URL for HTTP requests
- Redirect following with user-controlled URLs
- URL construction from user input
- Webhooks with user-specified endpoints

**Remediation:**
- Validate URLs against allowlist
- Block internal IP ranges (127.x, 10.x, 192.168.x, etc.)
- Use URL parsing to validate scheme and host
- Don't follow redirects or validate redirect targets

---

## CWE-327: Broken Cryptographic Algorithm

**Description:** Use of cryptographic algorithm not appropriate for security context.

**Static Detection Patterns:**
- MD5, SHA1 used for security purposes (passwords, signatures)
- DES, 3DES, RC4 encryption
- ECB mode encryption
- Custom cryptographic implementations

**Remediation:**
- Use bcrypt, Argon2, or scrypt for passwords
- Use AES-GCM or ChaCha20-Poly1305 for encryption
- Use SHA-256 or SHA-3 for hashing
- Use established cryptographic libraries

---

## Using This Reference

### During Analysis
1. For each CWE, search for the detection patterns in code
2. Trace data flow when pattern is found
3. Verify vulnerability using [verification-protocol.md](verification-protocol.md)
4. Assign severity using [severity-scoring.md](severity-scoring.md)
5. Document using [vulnerability-format.md](vulnerability-format.md)

### Coverage Tracking
Track which CWEs were checked in the Auditor agent's coverage matrix.

### External References
- CWE Top 25: https://cwe.mitre.org/top25/
- OWASP Top 10: https://owasp.org/Top10/
- CWE Full List: https://cwe.mitre.org/data/definitions/
