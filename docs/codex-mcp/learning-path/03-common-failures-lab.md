# 03 — Common Failures Lab

**Stage:** Reliability competence  
**Goal:** Build confidence handling realistic integration failures.

---

## Lab Rules

1. Run failures one at a time.
2. Capture symptom, diagnosis, recovery action, and verification.
3. Do not skip post-recovery verification.
4. Redact secrets in any captured logs.

---

## Lab Setup

- Start from a working setup validated in `02-first-success-30-min.md`.
- Keep a recovery log in a separate notes file.
- Use stable network where possible to isolate intentional failures.

---

## Failure Drills

### Drill 1: Authentication missing or expired

- **Inject:** Logout or use expired session.
- **Expected symptom:** Auth-related failure on `codex` call.
- **Diagnosis check:** `codex login status`.
- **Recovery:** `codex login` (or API-key login flow).
- **Verification:** Repeat successful `codex` call.

### Drill 2: Invalid `threadId`

- **Inject:** Use malformed or old thread ID with `codex-reply`.
- **Expected symptom:** Thread-not-found/invalid thread error.
- **Diagnosis check:** Confirm exact `threadId` provenance.
- **Recovery:** Start new `codex` call with full context; capture new `threadId`.
- **Verification:** Successful `codex-reply` on new thread.

### Drill 3: Timeout / transient upstream failure

- **Inject:** Simulate constrained network or set aggressive timeout in wrapper.
- **Expected symptom:** Timeout or upstream-unavailable behavior.
- **Diagnosis check:** Look for retry attempts and timeout class.
- **Recovery:** Restore network/timeout budget; retry with same request intent.
- **Verification:** Stable successful response under normal settings.

### Drill 4: Sandbox/policy mismatch

- **Inject:** Request mode disallowed by environment policy.
- **Expected symptom:** Policy/permission failure before normal execution.
- **Diagnosis check:** Compare requested sandbox/approval vs team defaults.
- **Recovery:** Use allowed policy profile; document why.
- **Verification:** Successful call under approved settings.

### Drill 5: Server lifecycle interruption

- **Inject:** Stop server process mid-session.
- **Expected symptom:** Tool unavailable / broken pipe / disconnect.
- **Diagnosis check:** Confirm server process exit.
- **Recovery:** Restart `codex mcp-server`; reconnect client.
- **Verification:** New successful `codex` call and restored workflow.

---

## Scoring Rubric

| Dimension | 0 | 1 | 2 |
|---|---|---|---|
| Detection speed | Could not identify issue | Identified issue slowly | Identified quickly and correctly |
| Root-cause clarity | Vague explanation | Partial cause | Clear causal explanation |
| Recovery quality | Unreliable workaround | Works once | Repeatable and documented |
| Verification discipline | No verification | Partial verification | Full before/after verification |

**Pass threshold:** 7/8 or higher on first four drills, plus successful completion of Drill 5.

---

## Debrief Questions

1. Which failures were hardest to diagnose and why?
2. Which runbook steps should be codified for your team?
3. What monitoring would have detected each failure earlier?
4. Which defaults should be tightened before broad adoption?

