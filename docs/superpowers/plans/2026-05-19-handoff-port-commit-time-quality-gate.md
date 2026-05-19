# Handoff: Commit-Time Quality Gate (Hard Pre-Promotion Enforcement) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make a hollow/malformed handoff impossible to promote by invoking the `quality_check` validation core *inside* the runtime commit chokepoint and rejecting integrity-tier failures before the durable write — a true hard gate, not advisory feedback.

**Architecture:** Add a per-issue `tier` discriminator to `quality_check.Issue` (set at every one of the 14 construction sites), then call `validate()` inside `write_active_handoff` after the content-hash check but before the first operation-state mutation; if any `tier == "integrity"` issue exists, raise `ActiveWriteError` (the existing failure type) so the reservation stays in its existing documented-recoverable `begun` state and `_recovery_commands` already enumerates the operator's options. Length/depth stays advisory on the retained Option-A `PostToolUse` hook.

**Tech Stack:** Python 3.11+ (stdlib + pyyaml), pytest. Edits the *ported* runtime — namespace is `handoff_runtime` (post Plan A Decision 4).

**Authoritative spec:** `docs/tickets/2026-05-19-handoff-port-commit-time-quality-gate.md` (Problem, Verified Integration Points, Proposed Solution, AC 1–6). The ticket's two-tier model is authority; where this plan and the ticket disagree, the ticket wins.

**HARD DEPENDENCY:** Blocked by `handoff-codex-port` (Plan A). This plan edits the **ported** runtime; Plan A must be landed on `main` first. Execute on a *new* branch `feature/handoff-port-commit-time-quality-gate` cut from `main` after Plan A merges. Do not start until `rg '\.codex' packages/plugins/handoff` returns zero on `main`.

---

## Verified Integration Points (measured 2026-05-19 against Codex source; symbols only — Plan A rename + this refactor shift line offsets)

| Symbol | Role | Verified shape |
|--------|------|----------------|
| `handoff_runtime/quality_check.py` `Issue` | issue model | `@dataclass` with **only** `severity: str`, `message: str` — no provenance. Tier split is NOT extractable as-is. |
| `quality_check.validate(content) -> list[Issue]` | validation core | Pure, I/O-free. Two early returns (no-frontmatter; invalid-type) + `validate_frontmatter` + `validate_sections` + `validate_line_count`. |
| `validate_line_count` | length checks | Emits `severity="error"` for **under-minimum** handoff/summary/checkpoint bodies → a severity-keyed gate is provably wrong (would block legitimate terse `/save`). |
| `handoff_runtime/active_writes.py` `write_active_handoff(project_root, *, operation_state_path, content, content_sha256)` | **the** commit chokepoint | After lock + freshness/snapshot/watermark checks, validates `expected_hash == content_sha256`, then (if status != committed) does the **first operation-state mutation** to `content-generated`, then `_write_content_to_active_path` performs the durable temp-file+`os.replace`. |
| `active_writes.ActiveWriteError(RuntimeError)` | failure type | Trivial subclass; reused everywhere with the global `"{op} failed: {reason}. Got: {input!r:.100}"` message format. |
| `active_writes._recovery_commands(project_root, operation_state_path)` | recovery surface | Returns `{continue, retry_write, abandon}` command dict — already the documented operator-actionable convention. |

**The seam (decisive):** insert the gate **between the `content_sha256` hash check and the first `_persist_operation_and_transaction` (the `content-generated` transition)**. At that point the reservation is still `begun` — the existing documented recoverable state — so raising `ActiveWriteError` needs **no new status literal** and triggers **no** `test_active_write_status_partition` churn. The lock's `finally` releases; `_recovery_commands` already enumerates continue/retry/abandon for a reservation in this state. (Rejected alternative: a new `integrity_rejected` operation-state terminal — out of scope, perturbs the status-partition invariant for zero AC benefit.)

**The 14 `Issue(...)` construction sites and their tier (from verified source):**

| # | Site (function / condition) | Current `severity` | **Tier** |
|---|------------------------------|--------------------|----------|
| 1 | `validate()` no-frontmatter early return | error | **integrity** |
| 2 | `validate()` invalid-`type` early return | error | **integrity** |
| 3 | `validate_frontmatter` missing required fields | error | **integrity** |
| 4 | `validate_frontmatter` blank required fields | error | **integrity** |
| 5 | `validate_frontmatter` checkpoint-title prefix | warning | advisory |
| 6 | `validate_frontmatter` summary-title prefix | warning | advisory |
| 7 | `validate_sections` missing required sections | error | **integrity** |
| 8 | `validate_sections` empty section | warning | advisory |
| 9 | `validate_sections` hollow-document guardrail | error | **integrity** |
| 10 | `validate_line_count` handoff `< min` | error | advisory |
| 11 | `validate_line_count` summary `< min` | error | advisory |
| 12 | `validate_line_count` summary `> max` | warning | advisory |
| 13 | `validate_line_count` checkpoint `< min` | error | advisory |
| 14 | `validate_line_count` checkpoint `> max` | warning | advisory |

Integrity = {1,2,3,4,7,9}; everything `validate_line_count` emits (10–14) is advisory **including its `severity="error"` ones**.

---

## File Structure Map

- **Modify:** `packages/plugins/handoff/handoff_runtime/quality_check.py` — add `Issue.tier`, tag all 14 sites. `format_output` display logic unchanged (still groups by `severity`).
- **Modify:** `packages/plugins/handoff/handoff_runtime/active_writes.py` — import `validate`; insert the integrity gate in `write_active_handoff` at the verified seam.
- **Modify:** `packages/plugins/handoff/skills/save/SKILL.md`, `skills/quicksave/SKILL.md`, `skills/summary/SKILL.md` — document the new integrity-rejection failure mode + recovery; state length/depth stay advisory.
- **Modify:** `packages/plugins/handoff/CHANGELOG.md` — new entry; AC#6 retained-hook note.
- **Test:** `tests/test_quality_check.py` (tier tagging), `tests/test_active_writes.py` (gate matrix), `tests/test_skill_docs.py` (doc assertions).
- **Untouched (AC#6):** `hooks/hooks.json` — the Option-A `PostToolUse:Write → quality_check` advisory hook is **retained** as the advisory-tier early-feedback layer.

---

## Task 0: Pre-Flight (dependency gate)

- [ ] **Step 1: Confirm Plan A landed on main**

Run: `git checkout main && git pull --ff-only && rg '\.codex' packages/plugins/handoff | wc -l`
Expected: `0`. If non-zero, STOP — Plan A is not landed; this plan is blocked.

- [ ] **Step 2: Cut the dependent branch**

Run: `git checkout -b feature/handoff-port-commit-time-quality-gate && git branch --show-current`
Expected: `feature/handoff-port-commit-time-quality-gate`.

- [ ] **Step 3: Green baseline**

Run: `uv run --package handoff pytest packages/plugins/handoff/tests -q 2>&1 | tail -1`
Expected: all pass (Plan A's final state). Record the count.

---

## Task 1: Add the `tier` Discriminator to `Issue` (cross-cutting refactor)

**Files:**
- Modify: `packages/plugins/handoff/handoff_runtime/quality_check.py`
- Test: `packages/plugins/handoff/tests/test_quality_check.py`

> Ticket Mechanism: "add per-issue provenance … a `tier` discriminator set at **every** `Issue` construction site — explicitly including the two `validate()` early returns and the hollow guardrail — and the chokepoint filters on the integrity discriminator, **never on `severity`**."

- [ ] **Step 1: Write the failing tier-tagging test**

Add to `packages/plugins/handoff/tests/test_quality_check.py`:
```python
from handoff_runtime.quality_check import validate

def _tiers(content):
    return {(i.tier, i.severity, i.message[:30]) for i in validate(content)}

def test_no_frontmatter_is_integrity():
    issues = validate("no frontmatter at all\njust body\n")
    assert issues and all(i.tier == "integrity" for i in issues)

def test_invalid_type_is_integrity():
    c = "---\ndate: 2026-01-01\ntime: \"00:00\"\ncreated_at: x\nsession_id: s\nproject: p\ntitle: t\ntype: bogus\n---\nbody\n"
    assert any(i.tier == "integrity" and "Invalid type" in i.message for i in validate(c))

def test_line_count_under_min_is_advisory_even_though_error_severity():
    # valid frontmatter + all required handoff sections, but short body
    fm = ("---\ndate: 2026-01-01\ntime: \"00:00\"\ncreated_at: x\n"
          "session_id: s\nproject: p\ntitle: t\ntype: handoff\n---\n")
    body = "".join(f"## {s}\nx\n" for s in (
        "Goal","Session Narrative","Decisions","Changes","Codebase Knowledge",
        "Context","Learnings","Next Steps","In Progress","Open Questions",
        "Risks","References","Gotchas"))
    issues = validate(fm + body)
    lc = [i for i in issues if "lines" in i.message and "minimum" in i.message]
    assert lc, "expected an under-minimum line-count issue"
    assert all(i.tier == "advisory" for i in lc)
    assert any(i.severity == "error" for i in lc)  # severity stays error; tier overrides gating

def test_hollow_guardrail_is_integrity():
    fm = ("---\ndate: 2026-01-01\ntime: \"00:00\"\ncreated_at: x\n"
          "session_id: s\nproject: p\ntitle: t\ntype: handoff\n---\n")
    body = "".join(f"## {s}\n\n" for s in (
        "Goal","Session Narrative","Decisions","Changes","Codebase Knowledge",
        "Context","Learnings","Next Steps","In Progress","Open Questions",
        "Risks","References","Gotchas"))
    assert any(i.tier == "integrity" and "Hollow" in i.message for i in validate(fm + body))
```

- [ ] **Step 2: Run it — expect FAIL** (`Issue` has no `tier`)

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev && uv run --package handoff pytest packages/plugins/handoff/tests/test_quality_check.py -k "tier or integrity or advisory or hollow" -q`
Expected: FAIL — `AttributeError: 'Issue' object has no attribute 'tier'` (or `TypeError` once the field is added but a site is missed — that is the desired tripwire).

- [ ] **Step 3: Add the required `tier` field to `Issue`**

In `handoff_runtime/quality_check.py`, the `Issue` dataclass:
```python
@dataclass
class Issue:
    """A quality issue found during validation.

    `tier` partitions gating, NOT `severity`: the commit-time quality gate
    (handoff-port-commit-time-quality-gate) hard-blocks promotion on
    tier == "integrity" only. Every Issue MUST declare its tier — there is
    no default, so a missed construction site is a TypeError caught by tests.
    """

    severity: str  # "error" or "warning" (display grouping only)
    message: str
    tier: str  # "integrity" (hard-blocks at commit) | "advisory" (never blocks)
```

- [ ] **Step 4: Tag all 14 construction sites (no default → every site must be edited)**

Apply `tier=` (keyword, for readability) to each. Exact mapping:
- **integrity** — site 1 (`validate()` no-frontmatter `Issue("error", "No frontmatter found. …")` → add `, tier="integrity"`); site 2 (`validate()` invalid-type `Issue("error", f"Invalid type '{doc_type}'. …")` → `tier="integrity"`); site 3 (`validate_frontmatter` `Issue("error", f"Missing required frontmatter: …")` → `tier="integrity"`); site 4 (`Issue("error", f"Blank required frontmatter: …")` → `tier="integrity"`); site 7 (`validate_sections` `Issue("error", f"Missing required sections: …")` → `tier="integrity"`); site 9 (hollow `Issue("error", "Hollow document: …")` → `tier="integrity"`).
- **advisory** — site 5 (`Issue("warning", f"Checkpoint title should start …")` → `tier="advisory"`); site 6 (`Issue("warning", f"Summary title should start …")` → `tier="advisory"`); site 8 (`Issue("warning", f"Empty section: …")` → `tier="advisory"`); sites 10–14 — **every** `validate_line_count` `Issue(...)` (handoff `<min` error, summary `<min` error, summary `>max` warning, checkpoint `<min` error, checkpoint `>max` warning) → `tier="advisory"`.

- [ ] **Step 5: Run it — expect PASS**

Run: same as Step 2.
Expected: PASS (all four tier tests green; the under-min test proves severity stays `error` while tier is `advisory`).

- [ ] **Step 6: Regression — existing quality tests still pass; `format_output` unchanged**

Run: `uv run --package handoff pytest packages/plugins/handoff/tests/test_quality_check.py -q`
Expected: PASS. Any existing test that constructs `Issue("error","msg")` positionally now fails with `TypeError` — update those *test* constructions to pass `tier=` (test-fixture retarget, the intended cross-cutting consequence; not a defect mask). `format_output` filters by `severity` for display — leave it; the gate (Task 2) filters by `tier`.

- [ ] **Step 7: Commit**

```bash
git add packages/plugins/handoff/handoff_runtime/quality_check.py packages/plugins/handoff/tests/test_quality_check.py
git commit -m "feat(handoff-gate): add required Issue.tier; tag all 14 sites

integrity = {no-frontmatter, invalid-type, missing/blank frontmatter,
missing sections, hollow}; everything validate_line_count emits is
advisory (incl. severity=error under-minimum). No default on tier so a
missed site is a construction-time TypeError.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Insert the Integrity Gate in `write_active_handoff`

**Files:**
- Modify: `packages/plugins/handoff/handoff_runtime/active_writes.py`
- Test: `packages/plugins/handoff/tests/test_active_writes.py`

> AC#1: `validate()` invoked inside `write_active_handoff` before the durable `_write_content_to_active_path`, for handoff/checkpoint/summary writes. AC#2: integrity-tier non-empty → rejected before promotion via `ActiveWriteError`; final artifact not created; reservation left in the existing documented recoverable state.

- [ ] **Step 1: Write the failing pre-promotion rejection test**

Add to `packages/plugins/handoff/tests/test_active_writes.py` (reuse the module's existing reservation/begin-active-write helpers — locate the existing happy-path test and mirror its setup):
```python
def test_integrity_failure_rejected_before_promotion(tmp_path):
    # Arrange: begin a reservation (mirror the existing happy-path helper).
    from handoff_runtime import active_writes
    # ... begin_active_write -> operation_state_path, allocated_active_path ...
    hollow = (  # valid frontmatter, all sections present but empty -> hollow (integrity)
        "---\ndate: 2026-01-01\ntime: \"00:00\"\ncreated_at: x\n"
        "session_id: s\nproject: p\ntitle: t\ntype: handoff\n---\n"
        + "".join(f"## {s}\n\n" for s in (
            "Goal","Session Narrative","Decisions","Changes","Codebase Knowledge",
            "Context","Learnings","Next Steps","In Progress","Open Questions",
            "Risks","References","Gotchas")))
    import hashlib
    sha = hashlib.sha256(hollow.encode()).hexdigest()
    with pytest.raises(active_writes.ActiveWriteError) as ei:
        active_writes.write_active_handoff(
            tmp_path, operation_state_path=operation_state_path,
            content=hollow, content_sha256=sha)
    assert "integrity" in str(ei.value).lower()
    assert not allocated_active_path.exists()  # NOT promoted
```

- [ ] **Step 2: Run it — expect FAIL** (hollow doc currently promotes)

Run: `uv run --package handoff pytest packages/plugins/handoff/tests/test_active_writes.py -k integrity -q`
Expected: FAIL — no exception; `allocated_active_path` exists.

- [ ] **Step 3: Insert the gate at the verified seam**

In `handoff_runtime/active_writes.py`: add `from handoff_runtime.quality_check import validate` to the imports. In `write_active_handoff`, **immediately after** the `expected_hash != content_sha256` check raises/passes and **before** the `if state.get("status") != "committed":` content-generated transition (the first `_persist_operation_and_transaction`), insert:
```python
        # Commit-time integrity gate (handoff-port-commit-time-quality-gate).
        # Hollow/malformed handoffs are rejected BEFORE any operation-state
        # mutation or durable write. The reservation stays in its existing
        # `begun` state — the documented recoverable state — so the lock
        # `finally` releases and _recovery_commands already enumerates
        # continue/retry/abandon. Length/depth (advisory tier) never gate
        # here; that stays on the PostToolUse advisory hook.
        integrity = [i for i in validate(content) if i.tier == "integrity"]
        if integrity:
            raise ActiveWriteError(
                "write-active-handoff failed: handoff failed integrity validation. "
                f"Got: {'; '.join(i.message for i in integrity)!r:.100}"
            )
```

- [ ] **Step 4: Run it — expect PASS**

Run: same as Step 2.
Expected: PASS — `ActiveWriteError` raised, message contains "integrity", `allocated_active_path` absent.

- [ ] **Step 5: Reservation-recoverability assertion (AC#2 / AC#3)**

Add a test asserting that after the rejection the `operation_state_path` still exists and `_recovery_commands(project_root, operation_state_path)` returns the `{continue, retry_write, abandon}` dict (the reservation is in the documented recoverable state — nothing to clean up beyond what the existing lock `finally` + reservation TTL already do). No new status literal; assert `test_active_write_status_partition` still passes unchanged.

Run: `uv run --package handoff pytest packages/plugins/handoff/tests/test_active_writes.py packages/plugins/handoff/tests/test_active_write_status_partition.py -q`
Expected: PASS (status-partition invariant untouched).

- [ ] **Step 6: Commit**

```bash
git add packages/plugins/handoff/handoff_runtime/active_writes.py packages/plugins/handoff/tests/test_active_writes.py
git commit -m "feat(handoff-gate): hard integrity gate in write_active_handoff

validate() called at the verified seam (post hash-check, pre first
operation-state mutation); tier==integrity -> ActiveWriteError before
promotion. Reservation stays in begun/recoverable state; no new status
literal; status-partition invariant untouched.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: AC#5 Test Matrix (each integrity path + the backwards advisory case)

**Files:** `packages/plugins/handoff/tests/test_active_writes.py`

> AC#5: (a) clean write promotes; (b) each integrity path rejected pre-promotion — **no-frontmatter, invalid-`type`**, missing required frontmatter field, missing required section, hollow-document; (c) **valid-frontmatter+valid-sections doc under the line-count minimum still promotes** (proves `validate_line_count` `severity="error"` does NOT gate — the case the prior draft got backwards); (d) over-maximum-length doc still promotes; (e) reservation/staging cleanup after a rejection.

- [ ] **Step 1: Write the full matrix (one test per case, parametrized where natural)**

Cases, each driving `write_active_handoff` through a fresh reservation:
- **(a) clean** — full valid handoff (≥400 body lines, all sections substantive) → promotes; `allocated_active_path` exists; `validate()` integrity-empty.
- **(b1) no-frontmatter** → `ActiveWriteError`, not promoted.
- **(b2) invalid-`type`** (`type: bogus`) → rejected, not promoted.
- **(b3) missing required frontmatter field** (drop `session_id`) → rejected.
- **(b4) missing required section** (omit `Decisions`) → rejected.
- **(b5) hollow** (all `CONTENT_REQUIRED_SECTIONS` present but empty) → rejected.
- **(c) under-minimum** — valid frontmatter + all required sections, body `< HANDOFF_MIN_LINES` → **promotes** (the linchpin: `validate_line_count` error severity, advisory tier, must NOT gate).
- **(d) over-maximum** — valid summary, body `> SUMMARY_MAX_LINES` → **promotes**.
- **(e)** — after any (b) rejection, `operation_state_path` still present, no partial `.md` at `allocated_active_path`, no `.tmp` sibling left behind.

- [ ] **Step 2: Run — expect PASS (all cases)**

Run: `uv run --package handoff pytest packages/plugins/handoff/tests/test_active_writes.py -q`
Expected: PASS. If (c) fails (doc rejected), the gate is wrongly keying on `severity`/line-count — fix the gate filter to `i.tier == "integrity"`, never severity.

- [ ] **Step 3: Commit**

```bash
git add packages/plugins/handoff/tests/test_active_writes.py
git commit -m "test(handoff-gate): AC#5 matrix incl. under-min promotes (severity!=gate)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Skill Docs + CHANGELOG + AC#6 Retained-Hook Note

**Files:**
- Modify: `skills/save/SKILL.md`, `skills/quicksave/SKILL.md`, `skills/summary/SKILL.md`
- Modify: `packages/plugins/handoff/CHANGELOG.md`
- Test: `tests/test_skill_docs.py`

> AC#4: skill docs document the integrity-rejection failure mode + recovery, and explicitly state length/depth remain advisory. AC#6: the Option-A advisory `PostToolUse:Write → quality_check` hook is **retained** and documented.

- [ ] **Step 1: Write the failing skill-docs assertion**

Add to `tests/test_skill_docs.py`:
```python
def test_skills_document_integrity_rejection_and_advisory_length():
    import pathlib
    skills = pathlib.Path(__file__).resolve().parents[1] / "skills"
    for name in ("save", "quicksave", "summary"):
        t = (skills / name / "SKILL.md").read_text("utf-8")
        assert "integrity" in t.lower()
        assert "ActiveWriteError" in t or "integrity validation" in t
        assert "advisory" in t.lower()  # length/depth remain advisory
```

- [ ] **Step 2: Run — expect FAIL**

Run: `uv run --package handoff pytest packages/plugins/handoff/tests/test_skill_docs.py -k integrity -q`
Expected: FAIL.

- [ ] **Step 3: Add a "Failure modes" note to each of save/quicksave/summary SKILL.md**

Add (near the active-writer step, mirroring the existing "If active-writer reservation or write fails, report the helper error and STOP" line):
```markdown
**Integrity rejection (hard gate):** The active writer rejects a handoff
that fails the integrity tier of the quality contract — no frontmatter,
invalid `type`, missing/blank required frontmatter, a missing required
section, or a hollow document (required content sections present but
empty). It fails with an `ActiveWriteError` ("… failed integrity
validation …") and the handoff is NOT written. Recovery: fix the flagged
content and retry, or abandon the reservation (see `_recovery_commands`:
`retry_write` / `abandon`). Length and section depth remain **advisory
only** — a terse `/save` under the line-count minimum still saves; that
feedback comes from the `PostToolUse` quality hook, not the gate.
```

- [ ] **Step 4: Run — expect PASS**

Run: same as Step 2.
Expected: PASS.

- [ ] **Step 5: CHANGELOG entry + AC#6 note**

Prepend to `packages/plugins/handoff/CHANGELOG.md` (above the `[2.0.0]` port entry):
```markdown
## [2.1.0] - <date>

### Added
- **Commit-time integrity gate:** `write_active_handoff` now invokes the
  `quality_check` validation core before the durable write and rejects
  integrity-tier failures (no-frontmatter, invalid `type`, missing/blank
  required frontmatter, missing required section, hollow document) via
  `ActiveWriteError` — a hard pre-promotion gate. `save`/`quicksave`/
  `summary` can now fail on integrity grounds (deliberate behavior change).
- `Issue.tier` ("integrity" | "advisory") partitions gating; the gate
  keys on tier, never on `severity`.

### Changed
- Length/depth checks remain **advisory only** and stay on the retained
  Option-A `PostToolUse:Write → quality_check` hook (AC#6) — a terse
  handoff under the line-count minimum still promotes.
```
(Set `<date>` to the execution date; bump matches a minor feature on top of the `2.0.0` port.)

- [ ] **Step 6: Commit**

```bash
git add packages/plugins/handoff/skills packages/plugins/handoff/CHANGELOG.md packages/plugins/handoff/tests/test_skill_docs.py
git commit -m "docs(handoff-gate): document integrity-rejection + advisory-length; CHANGELOG (AC#4/#6)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Full Suite Green + AC Verification

- [ ] **Step 1: Whole ported suite**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev && uv run --package handoff pytest packages/plugins/handoff/tests -q 2>&1 | tail -8`
Expected: **all pass** (Task 0 baseline count + the new tests; any positional-`Issue` test fixtures already retargeted in Task 1 Step 6).

- [ ] **Step 2: AC checklist (evidence, not assertion)**

- AC#1 — `rg -n 'from handoff_runtime.quality_check import validate' packages/plugins/handoff/handoff_runtime/active_writes.py` present; the `validate(content)` call is lexically before `_write_content_to_active_path`.
- AC#2 — Task 3 (b*) cases: `ActiveWriteError`, artifact absent.
- AC#3 — error message matches `"{op} failed: {reason}. Got: {input!r:.100}"`; skill docs cite `_recovery_commands` (`retry_write`/`abandon`).
- AC#4 — `test_skills_document_integrity_rejection_and_advisory_length` green.
- AC#5 — Task 3 matrix green incl. (c) under-min **promotes**.
- AC#6 — `hooks/hooks.json` still wires `PostToolUse:Write → quality_check`; CHANGELOG documents retention.

- [ ] **Step 3: Final commit + land**

```bash
git add -A && git commit -m "chore(handoff-gate): full suite green; AC#1-#6 verified

Plan: docs/superpowers/plans/2026-05-19-handoff-port-commit-time-quality-gate.md

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```
Then merge to `main` per superpowers:finishing-a-development-branch.

---

## Remaining Risks / Open Uncertainties

1. **Existing positional `Issue(...)` test fixtures** — adding a no-default `tier` is a deliberate tripwire; Task 1 Step 6 retargets them. If the count is large, that is expected cross-cutting fallout, not scope creep (the ticket calls this "a deliberate cross-cutting refactor with its own test surface").
2. **`write_active_handoff` setup in `test_active_writes.py`** — Task 2/3 reuse the module's existing reservation/begin-active-write helper. If no reusable fixture exists, build a minimal `begin_active_write` → `write_active_handoff` harness mirroring the happy-path test; do not stub the chokepoint.
3. **Seam exactness** — the gate must sit after the `content_sha256` check and before the *first* `_persist_operation_and_transaction`. If Plan A's rename/edits shifted that block, re-locate by symbol (the `if state.get("status") != "committed":` content-generated transition), not by line number. The ticket explicitly warns offsets shift.
4. **`format_output`** — left keying on `severity` for display by design (operators still see error/warning grouping); only the *gate* keys on `tier`. Not a defect.

## Self-Review

- **Spec coverage:** AC#1→T2; AC#2→T2/T3; AC#3→T2S5/T4; AC#4→T4; AC#5→T3 (all of a–e, incl. the backwards case); AC#6→T4/T5. Mechanism (`Issue` provenance refactor)→T1 (all 14 sites). Dependency→T0.
- **Placeholder scan:** the only non-literal is the `test_active_writes.py` reservation setup (Risk 2) — bounded by "mirror the existing happy-path helper", with an explicit fallback; acceptable because the exact helper name is in the ported source, not inventable here without re-reading post-Plan-A.
- **Type/name consistency:** `Issue(severity, message, tier)`; gate filter `i.tier == "integrity"` (never `severity`); namespace `handoff_runtime` throughout (post Plan A).
