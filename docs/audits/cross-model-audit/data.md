# Data Review Findings

**Reviewer:** data
**Date:** 2026-03-26
**Target:** `packages/plugins/cross-model/`

---

## Sentinel Questions Run

1. **Data Flow Clarity** — Can you trace a datum from entry to storage to exit? YES — traced `dialogue_outcome` event from agent synthesis text → `parse_synthesis()` → `build_dialogue_outcome()` → `append_log()` → `~/.claude/.codex-events.jsonl` → `read_events.py` → `compute_stats.py`. Path is legible. One concern raised (DA-2).
2. **Schema Governance** — Are schemas versioned and validated at boundaries? PARTIAL — structured event types have strong validation via `emit_analytics.py` + `event_schema.py`. Finding raised (DA-1): `VALID_CONSULTATION_SOURCES` is defined but never enforced. Schema version bumping is implicit (feature-flag heuristic).
3. **Source of Truth** — Is authority unambiguous for each fact? YES — `event_schema.py` is designated single source of truth for field definitions; `consultation-contract.md` is authoritative for briefing structure. No ambiguity found.
4. **Data Locality** — Does data live close to where it's consumed? YES — JSONL log is written locally at `~/.claude/.codex-events.jsonl`, consumed by the same host. Context-injection state is in-process memory. No unnecessary cross-boundary hops.
5. **Retention & Lifecycle** — Is there a defined policy for creation, archival, deletion? NO — finding raised (DA-3).

---

### [DA-1] `VALID_CONSULTATION_SOURCES` defined but never enforced

- **priority:** P2
- **lens:** Schema Governance
- **decision_state:** default likely inherited
- **anchor:** `scripts/event_schema.py:165-171`
- **problem:** `VALID_CONSULTATION_SOURCES` (enum: `codex`, `dialogue`, `reviewer`) is defined in `event_schema.py` with a comment saying it is optional "to preserve backward compatibility." It is never imported or validated in `emit_analytics.py` or `read_events.py`. A caller supplying an arbitrary string (e.g., `"unknown"`) passes validation silently.
- **impact:** `compute_stats.py` groups by `consultation_source` and falls through to `"unknown"` for unrecognized values (`scripts/compute_stats.py:565-567`). Stats skew silently rather than alerting on bad data. The enum in `event_schema.py` gives false assurance that the field is governed.
- **recommendation:** Either (a) import and apply `VALID_CONSULTATION_SOURCES` in the existing `validate()` function for `consultation_outcome` events (as an optional-but-typed check), or (b) remove the frozenset and document the field as unvalidated. Option (a) is preferred — the enum exists, the validation path exists, the wiring is just missing.
- **confidence:** high
- **provenance:** independent

---

### [DA-2] Schema version auto-bump is implicit and forward-read ambiguous

- **priority:** P2
- **lens:** Schema Governance
- **decision_state:** explicit tradeoff
- **anchor:** `scripts/event_schema.py:37-46`, `scripts/emit_analytics.py:491-492`
- **problem:** `resolve_schema_version()` determines `schema_version` by heuristic inspection of which feature-flag fields are present (`question_shaped` → 0.3.0, `provenance_unknown_count` as int → 0.2.0, else 0.1.0). This means two events can have the same `schema_version` with different field sets, and a future reader cannot distinguish "field absent because 0.1.0" from "field present but null in 0.2.0."
- **impact:** Acceptable as documented tradeoff for a pre-1.0 single-developer tool. The risk materializes when a third event type or new feature-flag field is added: the precedence chain (`0.3.0 > 0.2.0 > 0.1.0`) must be updated in `resolve_schema_version()` and is easy to miss. Existing logic is not wrong, but the pattern does not scale cleanly beyond 2-3 version flags.
- **recommendation:** Document the feature-flag precedence chain exhaustively in `event_schema.py` (current comment says only "Precedence: planning (0.3.0) > provenance (0.2.0) > base (0.1.0)"). When a 4th feature flag is added, consider switching to an explicit `schema_version` field in the input pipeline rather than heuristic inference. No immediate action required.
- **confidence:** high
- **provenance:** independent

---

### [DA-3] JSONL event log has no retention policy or size bound

- **priority:** P2
- **lens:** Retention & Lifecycle
- **decision_state:** underspecified
- **anchor:** `scripts/event_log.py:8-16`, `scripts/event_log.py:27`
- **problem:** `~/.claude/.codex-events.jsonl` grows indefinitely. There is no rotation, size cap, archival, or purge mechanism anywhere in the plugin codebase or HANDBOOK. The docstring in `event_log.py` explicitly marks this as best-effort and notes "if the user base grows or audit trail is needed for governance compliance, upgrade" — but the growth path is not bounded for a long-lived single-developer installation either.
- **impact:** Low for light use; at typical single-session consultation rates, growth is negligible. However, `compute_stats.py` reads the entire file on every `/consultation-stats` invocation (`read_events.py:66-100`). As the file grows, stats computation time grows linearly. No explicit acknowledgment that this is an acceptable tradeoff.
- **recommendation:** Add a HANDBOOK note stating the expected growth rate and when manual cleanup is warranted (e.g., "trim to last N events with `tail -n 10000 > temp && mv temp .codex-events.jsonl`"). Optionally cap `compute_stats.py` to the most recent N days (already partially present via `period_days` window in `compute_stats.py:826`). No code change required unless the user encounters performance issues.
- **confidence:** high
- **provenance:** independent

---

## Coverage Notes

**Data Flow Clarity:** Clean. The critical datum path (synthesis text → JSONL event → stats) is fully traceable. The dual-path fallback in `parse_synthesis()` (epilogue JSON → markdown regex) is well-documented. No data teleportation via side channels found.

**Source of Truth:** Clean. `event_schema.py` is the declared single source of truth for field definitions (module docstring explicitly states this). `consultation-contract.md` is authoritative for consultation protocol fields. No authority ambiguity found.

**Data Locality:** Clean. All state (JSONL log, in-process conversation state, profile YAML) is co-located with consumers. Context-injection in-process state is by design ephemeral with checkpoint recovery.
