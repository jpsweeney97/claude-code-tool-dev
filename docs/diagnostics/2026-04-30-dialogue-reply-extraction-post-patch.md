# Post-Patch Verification: T-20260416-01 Reply Extraction Fallback

## Identity

| Field | Value |
|---|---|
| Ticket | T-20260416-01 |
| Implementation commit | `00ec0054` (`feature/t16-01-reply-extraction-fallback`) |
| Codex CLI version | `0.125.0` |
| App Server user agent | `codex_collaboration/0.125.0 (Mac OS 26.4.1; arm64) kitty (codex_collaboration; 0.1.0)` |
| Verification date | 2026-04-30 |
| Repository | `claude-code-tool-dev` at `00ec0054` |

## Verification Design

The verification instruments `_fallback_extract_agent_message` on the live
`AppServerRuntimeSession` to detect whether the `thread/read` fallback fires.
Each run starts a fresh App Server session, creates an advisory thread, runs
one or more adversarial advisory turns with `CONSULT_OUTPUT_SCHEMA`, and
records:

- Whether `item/completed` delivered the agent message (normal path)
- Whether the fallback fired (failure recovery path)
- Whether `parse_consult_response` succeeded on the result
- Turn identifiers, message lengths, notification counts

The adversarial prompt requests thorough analysis with many evidence items
and is calibrated to produce responses at or above the scale of the original
B3 failure (~4K chars). All runs used `effort: "high"`.

## Runs

### Run 1: Single adversarial turn

| Field | Value |
|---|---|
| Thread ID | `019ddfa5-639b-7471-a8fd-9db608bc8c19` |
| Turn ID | `019ddfa5-65b6-7892-a0db-6417af1eda45` |
| Agent message length | 15,726 chars |
| Notification count | 3,762 |
| item/completed delivered | Yes |
| Fallback fired | No |
| parse_consult_response | Success (position: 1305 chars, evidence: 19, uncertainties: 7, branches: 8) |

### Run 2: Single adversarial turn (fresh session)

| Field | Value |
|---|---|
| Thread ID | `019ddfa7-9031-7ad0-a09d-4a9808b73511` |
| Turn ID | `019ddfa7-9298-7981-92f4-ef09e36376f9` |
| Agent message length | 14,679 chars |
| Notification count | 3,334 |
| item/completed delivered | Yes |
| Fallback fired | No |
| parse_consult_response | Success (position: 1248 chars, evidence: 20, uncertainties: 8, branches: 8) |

### Runs 3-5: Multi-turn dialogue (3 consecutive turns, fresh session)

| Turn | Turn ID | Message length | Notifications | Evidence | Fallback |
|---|---|---|---|---|---|
| 1 | `019ddfa9-9b8e-7c80-9029-34299dbef9b0` | 17,398 | 3,944 | 29 | No |
| 2 | `019ddfab-ff4a-78c1-b105-c04fe2fe3897` | 20,067 | 4,201 | 37 | No |
| 3 | `019ddfac-e998-7341-bd46-e2da3ae93a71` | 26,047 | 5,365 | 44 | No |

Thread ID: `019ddfa9-9986-7ea2-8591-c5881066daa3`

## Aggregate Results

| Metric | Value |
|---|---|
| Total advisory turns | 5 |
| Sessions | 3 |
| Total agent message bytes | 93,917 chars |
| Total notifications processed | 20,606 |
| item/completed delivered | 5/5 (100%) |
| Fallback fired | 0/5 (0%) |
| parse_consult_response success | 5/5 (100%) |
| CommittedTurnParseError | 0 |
| Runtime invalidation | 0 |
| Dispatch failure | 0 |

## Whether Fallback Fired

**No.** In all 5 runs, `item/completed` delivered the agent message through
the normal notification path. The `thread/read` fallback was instrumented but
never invoked.

## Observed Result

All 5 advisory turns completed without error. Agent messages ranged from
14,679 to 26,047 characters — all significantly larger than the original B3
failure case (~4,000 chars). `parse_consult_response` succeeded on all
results. No `CommittedTurnParseError`, no runtime invalidation, no
dispatch-failure semantics.

## Residual Uncertainty

The original B3/B5 failure mode (missing `item/completed` notification for
agent message) did not reproduce in these 5 runs. This means:

1. **The fallback recovery path itself is not proven by live evidence.** The
   implementation is covered by unit test #4 (load-bearing regression) and
   failure tests #6-#8, but the live `thread/read` projection shape for the
   failure class has not been exercised against the real App Server.

2. **The failure mode may be intermittent and version-dependent.** The
   original B3/B5 runs were on Codex `0.117.0`; this verification uses
   `0.125.0`. The `item/completed` delivery behavior may have changed between
   versions. The missing notification could also be a timing/load artifact
   that does not reproduce under single-session verification conditions.

3. **Non-regression is established.** The patched code does not introduce
   regressions: the normal notification path works correctly, the fallback
   does not interfere with successful turns, and the implementation passes
   1082 tests including 12 new fallback-specific tests.

## Closure Recommendation

**Do not close T-20260416-01 based solely on this evidence.**

The live verification establishes non-regression but does not prove the
fallback recovery path works against the real App Server. Per the ticket's
decision rule:

> If fallback did not fire but the dialogue completed normally:
> implementation remains test-covered, live non-regression passes, but the
> original failure-class recovery is not proven.

The implementation commit (`00ec0054`) is ready for merge. The ticket should
remain open with this evidence recorded until either:

1. A future run naturally triggers the fallback (the failure mode reproduces
   and recovery succeeds), or
2. The team accepts the unit-test coverage as sufficient closure evidence
   given that the App Server version has advanced and the failure mode may
   no longer be reproducible.

## Tool/Command Path

Verification was driven by a Python script (`verify_fallback_live.py`)
that directly called `AppServerRuntimeSession.run_advisory_turn()` with
an instrumented `_fallback_extract_agent_message`. The script was removed
after capturing evidence. The structured output and run identifiers above
are the durable record.
