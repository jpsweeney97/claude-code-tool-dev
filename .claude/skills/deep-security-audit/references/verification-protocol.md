# Verification Protocol

Methods for verifying security findings through static analysis. Every finding must document how it was verified.

---

## Static Analysis Methods

### 1. Data Flow Tracing

The primary method for verifying injection vulnerabilities.

**Process:**
1. **Identify Source:** Where untrusted data enters
   - User input (request params, forms, headers, cookies)
   - File contents
   - Database values (if populated from untrusted source)
   - Environment variables (if externally configurable)
   - Network responses

2. **Trace Propagation:** How data moves through code
   - Variable assignments
   - Function parameters and returns
   - Object properties
   - String operations (concatenation, formatting)
   - Data structure operations (list append, dict update)

3. **Identify Sink:** Where data reaches security-sensitive operation
   - SQL queries (CWE-89)
   - OS commands (CWE-78)
   - File operations (CWE-22)
   - HTML output (CWE-79)
   - LDAP queries (CWE-90)
   - XML parsers (CWE-611)

4. **Check for Sanitization:** On the path from source to sink
   - Input validation functions
   - Encoding/escaping functions
   - Parameterization
   - Type conversion

**Documentation Format:**
```
Source: request.form['username'] at auth/login.py:12
  ↓ Assigned to 'username' variable (line 12)
  ↓ Passed to build_query(username) (line 15)
  ↓ Concatenated into query string (line 23)
Sink: cursor.execute(query) at auth/login.py:24
Sanitization: None found on path
```

---

### 2. Taint Analysis

Track "tainted" (untrusted) data through the codebase.

**Taint Sources (mark as untrusted):**
- All user input
- File reads from user-specified paths
- Network responses
- Database values from user-controlled queries

**Taint Propagation Rules:**
- Assignment: `y = x` → if x is tainted, y is tainted
- Concatenation: `z = x + y` → if x OR y is tainted, z is tainted
- Function return: if tainted data passed to function and returned, return is tainted
- Object property: `obj.prop = x` → if x is tainted, obj.prop is tainted

**Taint Sinks (security-sensitive operations):**
- Query execution
- Command execution
- File operations
- Response rendering

**Sanitizers (remove taint):**
- Parameterized queries (for SQL)
- Encoding functions (for XSS)
- Validation that rejects invalid input
- Type conversion that enforces format

---

### 3. Control Flow Analysis

Verify that vulnerable code is reachable.

**Questions to Answer:**
- Is the vulnerable function called?
- Can the vulnerable code path be reached with attacker-controlled input?
- Are there conditions that prevent exploitation?
- Can security controls be bypassed?

**Process:**
1. Start from entry points (routes, handlers, public methods)
2. Trace call graph to vulnerable code
3. Identify all conditions on the path
4. Determine if conditions can be satisfied with malicious input

**Example Question:**
```
If vulnerable code is guarded by `if admin_mode:`
Can an attacker control the `admin_mode` variable?
```

---

### 4. Pattern Matching

Identify known vulnerable patterns.

**High-Confidence Patterns:**
- String concatenation into SQL/command strings
- Hardcoded credentials (API keys, passwords)
- Weak cryptographic algorithms (MD5, SHA1 for security)
- Missing authentication decorators on sensitive routes
- Disabled security features (CSRF exempt, no-verify SSL)

**Lower-Confidence Patterns (need context):**
- Use of certain functions (may be safe depending on input)
- Missing security headers (may be set elsewhere)
- Deprecated functions (may still be secure)

---

## False Positive Reduction Checklist

Before marking a finding as "Confirmed," verify:

### Framework Protections
- [ ] Does the framework auto-escape/sanitize by default?
  - Django: Templates auto-escape unless |safe used
  - Rails: ERB auto-escapes unless raw/html_safe used
  - React: JSX auto-escapes unless specific props used
- [ ] Is the framework's protection being bypassed in this case?

### Sanitization Check
- [ ] Is there a sanitization function called on this path?
- [ ] Is the sanitization appropriate for the context?
- [ ] Can the sanitization be bypassed?

### Reachability Check
- [ ] Is this code path reachable from an entry point?
- [ ] Can an attacker control the relevant input?
- [ ] Are there conditions that prevent exploitation?

### Dead Code Check
- [ ] Is this function ever called?
- [ ] Is this code path reachable (no always-false conditions)?
- [ ] Is this test/example code, not production?

### Context Check
- [ ] Is the "sink" actually security-sensitive in this context?
- [ ] Does the application context reduce impact?

---

## Confidence Level Criteria

### Confirmed
All of the following must be true:
- Complete data flow from source to sink documented
- No sanitization found on the path
- Code path is reachable (control flow verified)
- Framework protections do not apply or are bypassed
- Not dead code or test-only code

### Probable
Most of the following are true:
- Data flow is mostly traced (minor gaps)
- Sanitization exists but appears bypassable
- Code path is likely reachable
- High-confidence vulnerable pattern

### Possible
Some of the following are true:
- Vulnerable pattern detected
- Data flow partially traced
- Context needed to confirm (framework behavior, configuration)
- May require runtime verification

### Requires Runtime
Static analysis cannot determine:
- Dynamic dispatch (method called depends on runtime type)
- Configuration-dependent behavior (security depends on config value)
- Timing-dependent vulnerabilities (race conditions)
- External service behavior

---

## "Requires Runtime" Guidelines

**Acceptable uses:**
- Control flow depends on database values loaded at runtime
- Security configuration is externalized (environment variables)
- Dynamic method invocation makes call graph unclear
- Race condition between check and use

**NOT acceptable (investigate further):**
- "I didn't trace it completely" → Trace it
- "It might be sanitized somewhere" → Find where or document absence
- "The framework might protect this" → Check framework documentation
- "I'm not sure about this pattern" → Research the pattern

**Cap at 20%:** If more than 20% of findings are "Requires Runtime," the analysis is incomplete. Investigate further.

---

## Verification Documentation

Every finding must include verification method:

```markdown
### Verification Method

**Data Flow:**
- Traced from [source] at [location] to [sink] at [location]
- Passed through functions: [list]
- No sanitization observed at: [checked locations]

**Framework Check:**
- Framework: [name/version]
- Default protection: [yes/no/partial]
- Protection applies here: [yes/no - reason]

**Reachability:**
- Entry point: [route/function]
- Call path: [A → B → C → vulnerable code]
- Conditions satisfied: [how attacker can reach this]

**False Positive Checks:**
- [ ] Not dead code
- [ ] Not test-only code
- [ ] Sanitization not present
- [ ] Framework protection not active
```

---

## Evidence Quality Standards

### Strong Evidence (supports Confirmed)
- Complete source→sink trace with code locations
- Explicit check that no sanitization exists
- Proof that code is reachable
- Documentation of why framework protections don't apply

### Moderate Evidence (supports Probable)
- Partial data flow trace
- Known vulnerable pattern
- Likely reachable based on code structure
- Framework behavior documented but not verified for this case

### Weak Evidence (supports Possible only)
- Pattern match without data flow
- Assumption about reachability
- Unknown framework behavior
- General suspicion without specifics
