# Codex MCP Threat Model (Starter)

**Purpose:** Security baseline for operating Codex MCP integrations.  
**Audience:** Security reviewers, platform engineers, and maintainers.

---

## Scope

In scope:

- `codex mcp-server` invocation surface
- tool inputs/outputs (`codex`, `codex-reply`)
- auth/session handling expectations
- logging, telemetry, and operational controls

Out of scope:

- Codex internal model implementation
- third-party systems not connected to this runtime

---

## Assets to Protect

1. Credentials and auth sessions.
2. Sensitive code/data in prompts and responses.
3. Operational integrity of MCP service.
4. Policy settings (sandbox/approval defaults).

---

## Trust Boundaries

| Boundary | Risk Focus |
|---|---|
| Client ↔ MCP server | malformed requests, prompt injection patterns |
| MCP server ↔ Codex runtime | auth errors, upstream outage, config drift |
| Runtime ↔ logs/telemetry | accidental secret leakage |
| Human operators ↔ policy controls | misconfiguration and over-permissioning |

---

## Threat Inventory (STRIDE Starter)

| Category | Example Threat | Mitigation |
|---|---|---|
| Spoofing | unauthorized caller process invokes server | authenticated caller context, host controls |
| Tampering | runtime config altered unsafely | config versioning and review gates |
| Repudiation | unclear who changed policy | audited change logs and ownership |
| Information disclosure | tokens or secrets in logs/prompts | redaction and strict logging policy |
| Denial of service | repeated heavy calls cause timeouts | rate controls, bounded retries, backpressure |
| Elevation of privilege | unsafe sandbox mode in shared env | deny-by-default dangerous modes |

---

## Security Controls Baseline

1. Default sandbox to `read-only`.
2. Restrict `danger-full-access` to explicit break-glass flow.
3. Enforce approval-policy defaults by environment.
4. Redact sensitive fields before logging.
5. Use structured logging with no raw prompt by default.
6. Maintain an incident response path for auth and outage scenarios.

---

## Sensitive Data Handling Policy

Never expose or persist in plain logs:

- `id_token`
- `access_token`
- `refresh_token`
- bearer headers
- API keys (`OPENAI_API_KEY`, `sk-...`)

Required behavior:

1. Detect token-like strings in diagnostic payloads.
2. Replace with redaction marker before storage/display.
3. Keep redaction logic covered by regression tests.

---

## Secure Defaults Checklist

- [ ] Authentication mode documented (interactive vs API key).
- [ ] Secret source managed securely (env/secret store).
- [ ] Runtime policies and overrides documented.
- [ ] Log retention and access controls defined.
- [ ] Incident response contacts and escalation path documented.

---

## Verification Plan

1. Run secret-leakage regression tests.
2. Exercise auth-failure incident path.
3. Validate blocked dangerous modes in shared environments.
4. Confirm redaction in logs, traces, and user-visible errors.
5. Re-review threat model quarterly or after major architecture changes.

