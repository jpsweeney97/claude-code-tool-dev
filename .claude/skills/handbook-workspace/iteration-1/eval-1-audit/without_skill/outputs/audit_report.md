# HANDBOOK.md Audit Report

**File audited:** `/Users/jp/Projects/active/claude-code-tool-dev/packages/plugins/cross-model/HANDBOOK.md`
**Audit date:** 2026-03-07
**Auditor:** Claude Sonnet 4.6

---

## Methodology

The handbook was read in full and compared against the following source files:

- `scripts/codex_guard.py` — hook enforcement
- `scripts/credential_scan.py` — credential detector
- `scripts/codex_delegate.py` — delegation adapter
- `scripts/emit_analytics.py` — analytics emitter
- `skills/codex/SKILL.md` — `/codex` skill
- `hooks/hooks.json` — hook registration

Recent commits audited against:
- `fa1531b` — approval-policy default changed from `on-failure` to `on-request`
- `467b653` — JSON epilogue made sole machine contract for analytics
- `cf72278` — `config` added to `content_fields` in `ToolScanPolicy`
- `c724730` — credential scan gaps closed, full-input hook scanning added
- `9737b4c` — certifi CA bundle exempted from secret-file gate

---

## Findings

### 1. STALE — Approval-policy default is underdocumented and references the old behavior

**Location:** HANDBOOK.md line 268, `/codex` Runbook > Inputs and defaults table

**Handbook text:**
```
| `-a <approval-policy>` | approval policy | coupled to sandbox |
```

**Source of truth (`skills/codex/SKILL.md` line 60):**
```
| `-a {untrusted\|on-failure\|on-request\|never}` | `approval-policy` | `never` if read-only, `on-request` if workspace-write or danger-full-access |
```

**Problem:** The HANDBOOK says the default is "coupled to sandbox" without stating the actual values. Before commit `fa1531b`, the workspace-write default was `on-failure`. It is now `on-request`. The HANDBOOK gives operators no way to know what value is actually selected, and the description no longer signals which sandbox-coupling rule applies. Anyone relying on the HANDBOOK to understand the default behavior will not know whether `on-failure` or `on-request` is used for workspace-write.

**Fix:** Replace "coupled to sandbox" with the actual coupling rule: "`never` for `read-only`; `on-request` for `workspace-write`".

---

### 2. STALE — Analytics epilogue priority not documented; fallback behavior misleading

**Location:** HANDBOOK.md lines 574, 362, 710 (various references to "pipeline-data JSON epilogue")

**Source of truth (`scripts/emit_analytics.py` `parse_synthesis()`, lines 354–381):**

The emitter uses a two-path parse. It first attempts to parse the `<!-- pipeline-data -->` JSON epilogue. If the epilogue yields usable data (`_has_usable_epilogue_data()`), markdown parsing is bypassed entirely. Markdown fallback only activates when the epilogue is absent or malformed.

Commit `467b653` made the JSON epilogue the sole authoritative machine contract — the markdown fallback path still exists as a degraded fallback, but the epilogue is now the primary (and intended-only) source of machine-readable analytics fields.

**Problem:** The HANDBOOK describes the epilogue as a production artifact (correct) but does not state:
- That the epilogue supersedes markdown parsing when present and usable
- That markdown parsing is now a degraded fallback only
- That agents must emit the epilogue for analytics to be reliable

The `/dialogue` success criteria (line 362) says "synthesis plus machine-readable epilogue including the final `mode`" — this is correct in spirit but doesn't communicate the primacy of the epilogue over the markdown path, nor that operators should treat missing epilogues as a signal that analytics data will be degraded.

The File-by-File Change Map entry for `codex-dialogue.md` (line 710) says to edit it when changing "pipeline-data epilogue format" but gives no context on what makes the epilogue authoritative versus the fallback.

**Fix:** Add a note under "Event log and analytics" explaining that `dialogue_outcome` events are sourced from the JSON epilogue when present; markdown parsing is a degraded fallback. Note that epilogue absence causes analytics degradation.

---

### 3. MISSING — `ToolScanPolicy` and `config` field scanning not documented

**Location:** HANDBOOK.md lines 198–211, "Credential enforcement" section

**Source of truth (`scripts/codex_guard.py` lines 54–77):**

```python
CODEX_POLICY = ToolScanPolicy(
    expected_fields={"sandbox", "approval-policy", "model", "profile"},
    content_fields={"prompt", "base-instructions", "developer-instructions", "config"},
)
```

Commit `cf72278` added `config` to `content_fields`. This means the `config` field passed to `mcp__plugin_cross-model_codex__codex` (which contains `model_reasoning_effort`) is now scanned for credentials, not treated as a non-content field.

**Problem:** The HANDBOOK describes the scanning behavior as operating on "selected string-bearing fields" but does not document what those fields are. It does not mention the `ToolScanPolicy` structure, nor that `config` is a scanned content field. This matters operationally: if an operator passes structured config data containing anything that resembles a credential pattern, it will be blocked or shadowed.

The HANDBOOK also does not distinguish between `CODEX_POLICY` (for `codex` tool) and `CODEX_REPLY_POLICY` (for `codex-reply` tool), which differ in `expected_fields` (reply includes `threadId` and `conversationId`).

**Fix:** Under "Credential enforcement", list the scanned content fields for each tool. At minimum: note that `prompt`, `base-instructions`, `developer-instructions`, and `config` are all scanned; unexpected root fields are shadow-logged.

---

### 4. MISSING — Certifi CA bundle exemption not documented in secret-file gate limitations

**Location:** HANDBOOK.md lines 454–460, "Secret-file gate limitations" section

**Source of truth (`scripts/codex_delegate.py` lines 81–83):**

```python
_SAFE_ARTIFACT_TAILS: frozenset[tuple[str, ...]] = frozenset({
    ("certifi", "cacert.pem"),  # Python certifi CA bundle — public root certificates only
})
```

Commit `9737b4c` added this exemption. The secret-file gate exempts `certifi/cacert.pem` from the `.pem` glob block because it is a public CA bundle, not a credential. The exemption is applied after template exemptions and before exact-name / glob matching.

**Problem:** The HANDBOOK's limitations section (lines 454–460) describes the gate as matching "filenames and globs" and not tracking symlink targets or arbitrary names. But it makes no mention of known-safe exemptions. An operator troubleshooting why a `.pem` file is not blocked when running `/delegate` in a Python virtualenv would have no handbook reference for this behavior.

More importantly, the limitations section implies the gate is purely restrictive. The existence of a curated exemption list (`_SAFE_ARTIFACT_TAILS`) means the gate has a whitelist dimension that operators should be aware of if they ever need to add or audit exemptions.

**Fix:** Add a bullet to the limitations section: "Known-safe public artifacts (e.g., `certifi/cacert.pem`) are exempted by exact path-tail match. The exemption list lives in `codex_delegate.py`:`_SAFE_ARTIFACT_TAILS`."

---

### 5. MINOR — `stats_common.py` absent from "Core Components" scripts list

**Location:** HANDBOOK.md lines 59–69, "Hooks and scripts" section

**Source of truth:** `scripts/stats_common.py` exists on disk and is referenced in the File-by-File Change Map (line 793) under "Hooks and analytics".

**Problem:** The Core Components listing (lines 59–69) enumerates all scripts individually but omits `stats_common.py`. It appears later in the change map section but not in the canonical component list. A reader inventorying the hook and script surface would miss it.

**Fix:** Add `stats_common.py` to the scripts list in "Core Components" with a brief description (e.g., "shared computation utilities for `compute_stats.py` and `read_events.py`").

---

### 6. MINOR — Verification section test count may be stale

**Location:** HANDBOOK.md line 815

**Handbook text:**
```
- plugin-local suite passed with `160 passed`
```

**Problem:** This count is stamped with a specific date (March 7, 2026) and tied to a specific moment. Four recent commits added behavior to `codex_guard.py`, `codex_delegate.py`, and `emit_analytics.py`. Test counts likely changed with those commits. The count should be re-verified after any batch of functional changes.

**Risk level:** Low — this is a snapshot annotation, not a behavioral claim. But stale test counts erode trust in the verification section.

**Fix:** Re-run `uv run pytest tests` and update the count. Consider noting that the count is a point-in-time snapshot and will drift between updates.

---

## Summary Table

| # | Category | Section | Severity | Affected Commits |
|---|----------|---------|----------|-----------------|
| 1 | Stale | `/codex` Runbook — Inputs and defaults | High | `fa1531b` |
| 2 | Stale/Missing | Event log and analytics; `/dialogue` success criteria | Medium | `467b653` |
| 3 | Missing | Credential enforcement | Medium | `cf72278`, `c724730` |
| 4 | Missing | Secret-file gate limitations | Medium | `9737b4c` |
| 5 | Missing | Core Components — scripts list | Low | — |
| 6 | Stale | Verification — test count | Low | all four commits |

---

## What Is Accurate

The following areas were checked and are correct:

- Hook table (hooks.json matches HANDBOOK lines 128–133): PreToolUse and PostToolUse both use `codex_guard.py`; PostToolUseFailure uses `nudge_codex.py` with `Bash` matcher. Accurate.
- Bring-up prerequisites (Python 3.11, uv, git, POSIX, Codex CLI version ≥ 0.111.0). Accurate.
- Event types and meanings (block, shadow, consultation, consultation_outcome, dialogue_outcome, delegation_outcome). Accurate.
- Adapter pipeline 14-step sequence (lines 414–429). Accurate — matches `codex_delegate.py::run()`.
- Failure and recovery matrix. Accurate for documented failure paths.
- File-by-File Change Map. Accurate for routing. `stats_common.py` appears in the hooks section (line 793) even though it is missing from Core Components.
- `/delegate` mandatory review section. Accurate.
- Context-injection module list. Accurate — all listed modules exist.
- Continuity (`threadId` canonical, `conversationId` alias). Accurate.
- `codex_guard.py` tiered behavior (strict block, contextual block, broad shadow). Accurate.
- `CROSS_MODEL_NUDGE` opt-in behavior. Accurate.
