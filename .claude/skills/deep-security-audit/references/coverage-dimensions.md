# Coverage Dimensions

The 10 security dimensions that must be examined in every audit. Each dimension includes what to review and key patterns to look for.

---

## Coverage Matrix Template

Use this matrix to track examination status:

|  | Auth Module | API Handlers | Data Layer | Config | Dependencies |
|--|-------------|--------------|------------|--------|--------------|
| **Input Validation** | | | | | |
| **Authentication** | | | | | |
| **Authorization** | | | | | |
| **Session Management** | | | | | |
| **Cryptography** | | | | | |
| **Error Handling** | | | | | |
| **Logging** | | | | | |
| **Output Encoding** | | | | | |
| **Configuration** | | | | | |
| **Dependencies** | | | | | |

**Status values:**
- ✓ Examined, no issues
- ⚠ Examined, issues found (list VULN-IDs)
- ✗ Not examined (explain why)
- N/A Not applicable to this area

**Customize columns** for your codebase's structure (e.g., frontend, backend, services).

---

## Dimension 1: Input Validation

### What to Review
- Type checking before use
- Length/size limits enforced
- Format validation (regex, parsers)
- Allowlists vs blocklists
- Client-side vs server-side validation

### Key Patterns to Look For

**Vulnerable:**
- Direct use of user input without validation
- Client-only validation (server trusts client)
- String concatenation into queries/commands

**Secure:**
- Type conversion with error handling
- Server-side validation regardless of client
- Parameterized queries

### Common CWEs
- CWE-20: Improper Input Validation
- CWE-79: XSS (input not sanitized for output)
- CWE-89: SQL Injection
- CWE-78: Command Injection

---

## Dimension 2: Authentication

### What to Review
- Credential storage (hashing algorithm, salt)
- Password policies enforced
- Multi-factor authentication
- Brute force protection (rate limiting, lockout)
- Password reset flow
- Session creation after authentication

### Key Patterns to Look For

**Vulnerable:**
- Plaintext password storage
- Weak hashing (MD5, SHA1 without salt)
- No rate limiting on login attempts
- Predictable password reset tokens

**Secure:**
- Strong adaptive hashing (bcrypt, Argon2, scrypt)
- Rate limiting with exponential backoff
- Cryptographically random reset tokens
- Session regeneration after login

### Common CWEs
- CWE-287: Improper Authentication
- CWE-798: Hardcoded Credentials
- CWE-307: Brute Force
- CWE-521: Weak Password Requirements

---

## Dimension 3: Authorization

### What to Review
- RBAC/ABAC enforcement
- Privilege checks on every protected resource
- Resource ownership validation
- Horizontal privilege escalation (accessing other users' data)
- Vertical privilege escalation (gaining admin access)

### Key Patterns to Look For

**Vulnerable:**
- Missing authorization checks on endpoints
- Role check without ownership validation
- Direct object references without access control
- Admin functions accessible to regular users

**Secure:**
- Authorization check on every protected resource
- Both role AND ownership validation
- Indirect references or access control lists
- Consistent enforcement via middleware/decorators

### Common CWEs
- CWE-862: Missing Authorization
- CWE-863: Incorrect Authorization
- CWE-639: Authorization Bypass Through User-Controlled Key (IDOR)

---

## Dimension 4: Session Management

### What to Review
- Token generation (randomness, entropy)
- Session expiration (idle timeout, absolute timeout)
- Session invalidation (logout, password change)
- Cookie flags (HttpOnly, Secure, SameSite)
- Token storage (cookies vs localStorage)

### Key Patterns to Look For

**Vulnerable:**
- Predictable session IDs (sequential, timestamp-based)
- Missing cookie security flags
- Sessions persist after logout/password change
- Tokens in localStorage (XSS accessible)

**Secure:**
- Cryptographically random tokens (32+ bytes)
- HttpOnly, Secure, SameSite flags set
- Session invalidation on security events
- Tokens in HttpOnly cookies

### Common CWEs
- CWE-384: Session Fixation
- CWE-613: Insufficient Session Expiration
- CWE-614: Sensitive Cookie Without 'Secure' Flag

---

## Dimension 5: Cryptography

### What to Review
- Algorithm choice (no MD5, SHA1 for security purposes)
- Key management (generation, storage, rotation)
- IV/nonce handling (no reuse)
- Hardcoded secrets (keys, passwords in code)
- TLS configuration (min version, cipher suites)

### Key Patterns to Look For

**Vulnerable:**
- Weak algorithms (MD5, SHA1, DES, RC4)
- Hardcoded keys or secrets in source code
- ECB mode (patterns visible in ciphertext)
- Reused IVs or nonces
- Custom cryptography implementations

**Secure:**
- Strong algorithms (SHA-256+, AES-GCM, ChaCha20)
- Keys from environment or secret manager
- Authenticated encryption modes (GCM, CCM)
- Random IVs/nonces per operation
- Well-tested cryptographic libraries

### Common CWEs
- CWE-327: Broken Crypto Algorithm
- CWE-798: Hardcoded Credentials
- CWE-329: Not Using Random IV

---

## Dimension 6: Error Handling

### What to Review
- Stack traces not exposed to users
- Sensitive data not in error messages
- Error handling doesn't create vulnerabilities
- Fail-secure (deny on error, not allow)

### Key Patterns to Look For

**Vulnerable:**
- Full stack traces returned to client
- Database errors exposed (table names, queries)
- Fail-open on exceptions (allow access on error)
- Different error messages reveal information (user enumeration)

**Secure:**
- Generic error messages to users
- Detailed errors logged server-side only
- Fail-secure on all exceptions
- Consistent error responses regardless of cause

### Common CWEs
- CWE-209: Error Message Information Leak
- CWE-755: Improper Exception Handling

---

## Dimension 7: Logging & Auditing

### What to Review
- Security events logged (auth, authz, data access)
- No credentials/PII in logs
- Log injection prevention
- Audit trail completeness
- Log integrity protection

### Key Patterns to Look For

**Vulnerable:**
- Passwords, tokens, or API keys in logs
- User input directly in log messages (injection)
- Missing logs for security-critical operations
- No audit trail for admin actions

**Secure:**
- Sensitive data masked or excluded from logs
- Log input sanitized (newlines, control chars removed)
- All auth/authz events logged with context
- Tamper-evident or append-only logs

### Common CWEs
- CWE-532: Sensitive Info in Log Files
- CWE-117: Log Injection
- CWE-778: Insufficient Logging

---

## Dimension 8: Output Encoding

### What to Review
- Context-appropriate encoding (HTML, JS, URL, CSS)
- Framework auto-escaping enabled
- Bypass of auto-escaping (safe filters, raw output)
- Content-Type headers set correctly

### Key Patterns to Look For

**Vulnerable:**
- User input rendered without encoding
- Auto-escape disabled (|safe filter, raw output, innerHTML)
- Wrong encoding for context (HTML encoding in JS context)
- Missing Content-Type headers

**Secure:**
- Framework auto-escaping enabled and not bypassed
- Context-appropriate encoding functions used
- Content-Security-Policy headers set
- User content rendered as text, not HTML

### Framework-Specific Safe Filters to Watch
- Django: `|safe`, `mark_safe()`
- Rails: `raw`, `html_safe`
- React: `dangerously...` props (innerHTML patterns)
- Vue: `v-html` directive
- Angular: `bypassSecurityTrust...` methods

### Common CWEs
- CWE-79: Cross-site Scripting (XSS)
- CWE-116: Improper Encoding

---

## Dimension 9: Configuration

### What to Review
- Secure defaults (debug off, HTTPS required)
- Environment separation (dev vs prod configs)
- Secrets not in code/config files
- Unnecessary features disabled
- Admin interfaces protected

### Key Patterns to Look For

**Vulnerable:**
- DEBUG=True in production
- ALLOWED_HOSTS=['*'] or similar wildcards
- Secrets committed to version control
- Default credentials unchanged
- Admin panel publicly accessible

**Secure:**
- Environment-specific configuration
- Secrets from environment variables or secret manager
- Debug features disabled in production
- Admin interfaces IP-restricted or VPN-only
- Unnecessary endpoints/features removed

### Common CWEs
- CWE-1188: Insecure Default Initialization
- CWE-489: Active Debug Code
- CWE-798: Hardcoded Credentials

---

## Dimension 10: Dependencies

### What to Review
- Known CVEs in dependencies
- Outdated packages
- Lock file matches manifest
- Unnecessary dependencies
- Supply chain risks (typosquatting, compromised packages)

### Key Patterns to Look For

**Vulnerable:**
- Dependencies with known CVEs
- No lock file (non-deterministic builds)
- Unpinned version ranges
- Dependencies from untrusted sources
- Abandoned/unmaintained packages

**Secure:**
- All dependencies pinned to exact versions
- Lock file present and committed
- Regular dependency audits
- Dependencies from official registries
- Automated vulnerability scanning in CI

### Audit Commands by Ecosystem
- Python: `pip-audit`, `safety check`
- Node.js: `npm audit`, `yarn audit`
- Ruby: `bundle audit`
- Go: `govulncheck`
- Java: OWASP Dependency-Check

### Common CWEs
- CWE-1104: Use of Unmaintained Third-Party Components
- CWE-829: Inclusion of Untrusted Functionality
