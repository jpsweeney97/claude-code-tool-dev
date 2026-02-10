# Codex MCP Operations Runbook

**Purpose:** Day-2 operations guide for running Codex MCP reliably and safely.  
**Audience:** On-call engineers, platform owners, and maintainers.

---

## Service Definition

- **Service:** Codex MCP server process (`codex mcp-server`)
- **Critical capabilities:** tool availability, request success, thread continuity
- **Primary tools exposed:** `codex`, `codex-reply`

---

## Ownership

- **Service owner:** [team/role]
- **Primary on-call:** [rotation]
- **Secondary on-call:** [rotation]
- **Escalation path:** [pager/channel]

Replace bracketed fields with your real ownership mapping before production use.

---

## SLO / SLI Starter Set

### Suggested SLIs

1. Tool invocation success rate.
2. p95 invocation latency.
3. Timeout rate.
4. Authentication failure rate.

### Suggested initial SLOs

1. Success rate ≥ 99.0% (rolling 30 days).
2. p95 latency ≤ 15s for standard calls.
3. Timeout rate ≤ 1.0%.

Tune these after baseline observations.

---

## Startup Checklist

1. Verify CLI and version:
   - `codex --version`
2. Verify auth state:
   - `codex login status`
3. Verify server command:
   - `codex mcp-server --help`
4. Start server process with approved config profile.
5. Confirm tool discovery (`codex`, `codex-reply`).
6. Run one synthetic request.

---

## Health Checks

### Level 1: Process health

- Is server process running?
- Are stdio pipes healthy?

### Level 2: Functional health

- Can client list available tools?
- Does `codex` return a valid response?

### Level 3: Continuity health

- Does `codex-reply` succeed on known-good `threadId` flow?

---

## Incident Playbooks

### Incident A: Auth outage

**Symptoms:** sudden auth failures across requests.  
**Actions:**

1. Check `codex login status`.
2. Re-authenticate according to policy.
3. Re-run synthetic request.
4. Confirm recovery and close incident notes.

### Incident B: Upstream degradation/timeouts

**Symptoms:** rising latency/timeout/error rates.  
**Actions:**

1. Verify network and upstream status.
2. Apply bounded retries.
3. Switch to degraded-mode guidance if needed.
4. Communicate ETA and current impact.

### Incident C: Thread continuity failures

**Symptoms:** repeated invalid/unknown `threadId`.  
**Actions:**

1. Validate caller persistence of `threadId`.
2. Start fresh `codex` turn with full context.
3. Confirm follow-up success.
4. Capture root cause and prevent recurrence.

### Incident D: Policy misconfiguration

**Symptoms:** blocked calls due to sandbox/approval mismatch.  
**Actions:**

1. Compare runtime settings to approved policy baseline.
2. Roll back to last known-good policy profile.
3. Validate with synthetic test.

---

## Change Management

Before changing runtime defaults:

1. Document proposed change and reason.
2. Assess security impact.
3. Test in non-production environment.
4. Roll out gradually with monitoring.
5. Keep rollback command/profile ready.

---

## Communication Templates

### Incident start

“Investigating Codex MCP degradation affecting [scope]. Current impact: [brief]. Next update in [X] minutes.”

### Incident resolved

“Codex MCP service restored at [time]. Root cause: [brief]. Follow-up actions: [items].”

---

## Post-Incident Review Checklist

1. Timeline with key events.
2. Trigger and root cause.
3. Detection and response effectiveness.
4. Corrective and preventive actions.
5. Owner + target dates for each action.

