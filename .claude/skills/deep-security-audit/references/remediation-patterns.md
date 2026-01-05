# Remediation Patterns

Common security fixes organized by vulnerability category. Each pattern shows the principle and secure implementation approach.

---

## Injection Vulnerabilities

### SQL Injection (CWE-89)

**Principle:** Never construct queries with string concatenation. Use parameterized queries.

**Pattern: Parameterized Query**
```
INSTEAD OF: query = "SELECT * FROM users WHERE id = " + user_id
USE: query = "SELECT * FROM users WHERE id = ?"
     execute(query, [user_id])
```

**Framework Examples:**
- Python/SQLAlchemy: Use `session.query().filter()` or bound parameters
- Python/psycopg2: Use `cursor.execute(query, params)`
- Node/pg: Use parameterized queries with `$1, $2` placeholders
- Java/JDBC: Use `PreparedStatement`

### Command Injection (CWE-78)

**Principle:** Avoid shell commands. If necessary, use argument arrays, not shell strings.

**Pattern: Argument Array**
```
INSTEAD OF: shell("cat " + filename)
USE: execute(["cat", filename])  # With shell=False

BETTER: Use language-native file reading instead of shell commands
```

**Additional Controls:**
- Validate input against allowlist of permitted values
- Use libraries instead of shell commands when possible
- If shell required, use proper escaping functions

### XSS (CWE-79)

**Principle:** Encode output for the correct context. Don't disable auto-escaping.

**Pattern: Context-Appropriate Encoding**
```
HTML Context: Use HTML entity encoding (&lt; &gt; &amp; etc.)
JavaScript Context: Use JavaScript string encoding
URL Context: Use URL encoding (%20, %3C, etc.)
CSS Context: Use CSS encoding
```

**Framework Controls:**
- Keep template auto-escaping enabled
- Don't use |safe, raw, html_safe unless content is trusted AND sanitized
- Use Content-Security-Policy headers

---

## Authentication & Session

### Weak Password Storage (CWE-916)

**Principle:** Use adaptive hashing with unique salt per password.

**Pattern: Adaptive Hashing**
```
INSTEAD OF: hash = md5(password)
USE: hash = bcrypt(password, cost=12)
     # Or: argon2, scrypt with appropriate parameters
```

**Parameters:**
- bcrypt: cost factor 10-12 minimum
- Argon2: memory 64MB+, iterations 3+, parallelism 1
- scrypt: N=2^14, r=8, p=1 minimum

### Session Fixation (CWE-384)

**Principle:** Regenerate session ID after authentication state changes.

**Pattern: Session Regeneration**
```
After successful login:
1. Invalidate old session
2. Create new session with new ID
3. Copy only necessary data to new session
```

### Missing Authentication (CWE-287)

**Principle:** Protect all sensitive endpoints with authentication middleware.

**Pattern: Authentication Middleware**
```
Apply authentication decorator/middleware to all protected routes:
- @login_required (Django)
- before_action :authenticate_user! (Rails)
- app.use(authenticate) (Express)
```

---

## Authorization

### Missing Authorization (CWE-862)

**Principle:** Check authorization on every request to protected resources.

**Pattern: Ownership Check**
```
def get_resource(resource_id, current_user):
    resource = Resource.get(resource_id)
    if resource.owner_id != current_user.id:
        if not current_user.is_admin:
            raise Forbidden()
    return resource
```

### IDOR (CWE-639)

**Principle:** Verify the requester has access to the specific resource.

**Pattern: Access Control Check**
```
INSTEAD OF: return Resource.get(user_provided_id)
USE: return Resource.get(id=user_provided_id, owner=current_user)
     # Or explicit ownership/permission check
```

---

## Cryptography

### Weak Algorithm (CWE-327)

**Principle:** Use modern, vetted cryptographic algorithms.

**Recommended Algorithms:**
| Purpose | Use | Avoid |
|---------|-----|-------|
| Password hashing | bcrypt, Argon2, scrypt | MD5, SHA1, SHA256 (without salt) |
| Symmetric encryption | AES-256-GCM, ChaCha20-Poly1305 | DES, 3DES, RC4, AES-ECB |
| Asymmetric encryption | RSA-2048+, Ed25519 | RSA-1024, DSA |
| Hashing | SHA-256, SHA-3 | MD5, SHA1 |

### Hardcoded Credentials (CWE-798)

**Principle:** Store secrets outside code in secure configuration.

**Pattern: Environment Variables**
```
INSTEAD OF: API_KEY = "sk_live_..."
USE: API_KEY = get_env("API_KEY")
     # Fail if not set in production
```

**Better:** Use secret management service (Vault, AWS Secrets Manager, etc.)

---

## Data Exposure

### Information Leak in Errors (CWE-209)

**Principle:** Show generic errors to users, log details server-side.

**Pattern: Error Handling**
```
try:
    process_request()
except Exception as e:
    log.error(f"Processing failed: {e}", exc_info=True)  # Full details to log
    return error_response("An error occurred")  # Generic to user
```

### Sensitive Data in Logs (CWE-532)

**Principle:** Never log credentials, tokens, or PII.

**Pattern: Log Sanitization**
```
INSTEAD OF: log(f"Login: user={u}, password={p}")
USE: log(f"Login attempt: user={u}")

INSTEAD OF: log(f"Request: {full_request}")
USE: log(f"Request: {sanitize_request(request)}")
```

---

## Configuration

### Debug Mode in Production (CWE-489)

**Principle:** Disable debug features in production via environment configuration.

**Pattern: Environment-Based Config**
```
DEBUG = (get_env("ENVIRONMENT") != "production")
# Or: DEBUG = get_env("DEBUG", "false").lower() == "true"
```

### Insecure Defaults (CWE-1188)

**Principle:** Default to secure configuration; require explicit opt-out.

**Pattern: Secure Defaults**
```
CSRF_ENABLED = True  # Secure by default
HTTPS_REQUIRED = True  # Secure by default
DEBUG = False  # Secure by default
```

---

## CSRF

### Missing CSRF Protection (CWE-352)

**Principle:** Require CSRF token for all state-changing requests.

**Pattern: CSRF Token**
```
1. Generate unique token per session
2. Include token in forms (hidden field) or headers (X-CSRF-Token)
3. Validate token on all POST/PUT/DELETE requests
4. Use SameSite=Strict cookies as defense in depth
```

---

## File Handling

### Path Traversal (CWE-22)

**Principle:** Validate paths stay within allowed directory.

**Pattern: Path Validation**
```
def safe_join(base_dir, user_path):
    # Resolve to absolute path
    full_path = realpath(join(base_dir, user_path))
    # Verify it's still within base_dir
    if not full_path.startswith(realpath(base_dir)):
        raise SecurityError("Path traversal detected")
    return full_path
```

### Unrestricted File Upload (CWE-434)

**Principle:** Validate file type, size, and store safely.

**Pattern: Safe File Upload**
```
1. Validate file extension against allowlist
2. Validate content type (don't trust Content-Type header alone)
3. Check magic bytes for file type
4. Limit file size
5. Generate new filename (don't use user-provided name)
6. Store outside web root or use signed URLs
7. Scan for malware if accepting executables
```

---

## Applying Remediations

### In Vulnerability Reports

Include remediation in each finding:

```markdown
### Remediation

**Principle:** [The security principle being violated]

**Fix Pattern:** [Reference to pattern from this document]

**Specific Fix:**
[Code or configuration change specific to this finding]

**Additional Recommendations:**
- [Defense-in-depth measures]
- [Related hardening]
```

### Prioritization

Fix in this order:
1. **Critical/High + Easy Fix** — Biggest risk reduction per effort
2. **Critical/High + Hard Fix** — Requires more effort but necessary
3. **Medium + Easy Fix** — Quick wins
4. **Medium + Hard Fix** — Plan for next sprint
5. **Low/Informational** — Backlog for hardening

### Testing Fixes

After applying remediation:
1. Verify the specific vulnerability is fixed
2. Regression test to ensure functionality preserved
3. Consider if fix introduces new issues
4. Add automated test to prevent regression
