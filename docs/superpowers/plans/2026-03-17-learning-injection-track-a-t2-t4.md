# Learning Injection Track A T2–T4 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire `retrieve_learnings.py` (Track A T1, already built and tested) into both consultation skills and update the consultation contract to reflect the active implementation.

**Architecture:** Three instruction-document edits — `/codex` SKILL.md gets a new retrieval subsection before Step 1, `/dialogue` SKILL.md gets retrieval instructions before Step 3 and an updated Step 3h template, and contract §17 drops its "Deferred" status. All edits follow the existing `${CLAUDE_PLUGIN_ROOT}` invocation pattern established by `consultation-stats/SKILL.md`.

**Tech Stack:** Markdown (SKILL.md instruction documents), Python (existing `retrieve_learnings.py`), Bash (verification commands)

**Prerequisites completed:**
- `retrieve_learnings.py` exists at `packages/plugins/cross-model/scripts/retrieve_learnings.py` (22 tests, all passing)
- Test coverage audit: 12/12 scripts covered, plugin is self-contained (0 external imports)
- Branch: `feature/learning-injection` (5 commits ahead of main)

---

### Task 1: Update `/codex` SKILL.md — Learning Retrieval Before Briefing

**Files:**
- Modify: `packages/plugins/cross-model/skills/codex/SKILL.md:84` (replace single-line stub)

**Context:** Line 84 is between "Argument validation" (ends line 82) and "Step 1: Build Context Briefing" (starts line 86). The stub is a single bold paragraph. Replace it with a subsection that tells Claude to call the retrieval script and inject output into the briefing's `## Context` section per §17.2.

**Invocation pattern:** Follows the precedent set by `consultation-stats/SKILL.md:33`:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/compute_stats.py" --period 30 --type all --json
```

**§17.2 spec for `/codex` path:** "Inject selected entries into the briefing's `## Context` section before the question."

- [ ] **Step 1: Replace the stub at line 84**

Replace this single line:
```
**Learning retrieval (§17):** Before building the briefing, attempt to read learning cards per consultation contract §17. Fail-soft: missing store does not block consultation.
```

With this subsection:
```markdown
### Learning retrieval (§17)

Before building the briefing, retrieve relevant learnings for context injection.

1. Run the retrieval script:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/retrieve_learnings.py" --query "{question}" --max-entries 5
   ```
   Where `{question}` is the user's consultation question (the prompt text after flag processing).

2. **If stdout is non-empty:** Prepend the output to the `## Context` section of the briefing, before your contextual framing. The output is pre-formatted markdown — include it verbatim. Do not strip or reformat the `### YYYY-MM-DD [tags]` headers.

3. **If stdout is empty or the command fails (non-zero exit):** Proceed without learnings. Do not block the consultation. Do not report the absence of learnings to the user.

The `<!-- learnings-injected: N -->` comment in the output is an observability marker. Preserve it in the briefing — `emit_analytics.py` uses it for injection tracking.
```

- [ ] **Step 2: Verify the edit preserves document structure**

Visually confirm:
- The new subsection sits between "Argument validation" (line 82) and "## Step 1: Build Context Briefing" (previously line 86)
- The `###` heading level is consistent with other subsections in the skill (Argument validation is `###`)
- No orphaned blank lines or broken markdown links

- [ ] **Step 3: Verify the retrieval script runs from the expected path**

Run:
```bash
python3 packages/plugins/cross-model/scripts/retrieve_learnings.py --query "credential scan security" --max-entries 3
```
Expected: 1-3 formatted learning entries with `<!-- learnings-injected: N -->` marker. This confirms the script works and the command pattern is correct.

- [ ] **Step 4: Commit**

```bash
git add packages/plugins/cross-model/skills/codex/SKILL.md
git commit -m "feat: wire learning retrieval into /codex SKILL.md (Track A T2)

Replace §17 stub with full retrieval instructions. Claude calls
retrieve_learnings.py before building the briefing and injects
output into the ## Context section per §17.2.

Follows ${CLAUDE_PLUGIN_ROOT} invocation pattern from
consultation-stats/SKILL.md."
```

---

### Task 2: Update `/dialogue` SKILL.md — Learning Retrieval + Step 3h Template

**Files:**
- Modify: `packages/plugins/cross-model/skills/dialogue/SKILL.md:187` (replace single-line stub)
- Modify: `packages/plugins/cross-model/skills/dialogue/SKILL.md:262-276` (update Step 3h template)

**Context:** The `/dialogue` path is more involved than `/codex` because it uses a deterministic assembly pipeline (Step 3). Two edits:
1. Replace the stub at line 187 (between Step 2 and Step 3) with retrieval instructions
2. Update the Step 3h grouping template (lines 264-276) to include `## Prior Learnings` between `## Context` and `## Material`

**§17.2 spec for `/dialogue` path:** "Inject selected entries into the assembled briefing (Step 3h) as a `## Prior Learnings` section between `## Context` and `## Material`. This section appears only in the outbound briefing to Codex — it is not expected in the agent's synthesis output."

**Constraint:** Step 3 is described as "deterministic, non-LLM assembly" (line 189). The retrieval script is deterministic (keyword scoring), so it fits this constraint.

- [ ] **Step 1: Replace the stub at line 187**

Replace this single line:
```
**Learning retrieval (§17):** Before briefing assembly, attempt to read learning cards per consultation contract §17. Fail-soft: missing store does not block consultation.
```

With this subsection:
```markdown
### Learning retrieval (§17)

Before briefing assembly, retrieve relevant learnings for injection into the outbound briefing.

1. Run the retrieval script:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/retrieve_learnings.py" --query "{question}" --max-entries 5
   ```
   Where `{question}` is the user's dialogue question.

2. **If stdout is non-empty:** Store the output as a pipeline variable `learning_entries` for injection in Step 3h. The output is pre-formatted markdown — do not modify it.

3. **If stdout is empty or the command fails (non-zero exit):** Set `learning_entries` to empty string. Proceed without learnings. Do not block the consultation. Do not report the absence.

The retrieval script is deterministic (keyword/tag scoring) — consistent with Step 3's non-LLM assembly constraint.
```

- [ ] **Step 2: Update the Step 3h grouping template (lines 264-276)**

Replace the current template:
```
**3h. Group:** Assemble into three sections with deterministic ordering (Gatherer A items first, then Gatherer B within each section):

```
<!-- dialogue-orchestrated-briefing -->
## Context
{OPEN items}
{COUNTER items}
{CONFIRM items}

## Material
{CLAIM items}

## Question
{user's question, verbatim}
```
```

With (adds `## Prior Learnings` conditionally):
```
**3h. Group:** Assemble into sections with deterministic ordering (Gatherer A items first, then Gatherer B within each section):

```
<!-- dialogue-orchestrated-briefing -->
## Context
{OPEN items}
{COUNTER items}
{CONFIRM items}

## Prior Learnings
{learning_entries from retrieval step, if non-empty}

## Material
{CLAIM items}

## Question
{user's question, verbatim}
```

**`## Prior Learnings` rules:**
- Include this section only if `learning_entries` (from the retrieval step) is non-empty. If empty, omit the section header entirely — do not emit an empty `## Prior Learnings` section.
- The section appears only in the outbound briefing to Codex. It is NOT expected in the `codex-dialogue` agent's synthesis output.
- The `<!-- learnings-injected: N -->` comment within the learning entries is an observability marker. Preserve it.
```

- [ ] **Step 3: Update the "three sections" count**

The description at line 262 says "three sections" — it is now four (Context, Prior Learnings, Material, Question). However, Prior Learnings is conditional. Update the wording from "three sections" to "sections" (already done in the replacement above — the word "three" is dropped).

- [ ] **Step 4: Verify the sentinel marker is undisturbed**

Confirm line 278 still reads:
```
The sentinel `<!-- dialogue-orchestrated-briefing -->` must appear in the briefing. The `codex-dialogue` agent uses it to detect an external briefing.
```
The sentinel is at the top of the template, before `## Context`. The `## Prior Learnings` insertion is below it — no conflict.

- [ ] **Step 5: Commit**

```bash
git add packages/plugins/cross-model/skills/dialogue/SKILL.md
git commit -m "feat: wire learning retrieval into /dialogue SKILL.md (Track A T3)

Replace §17 stub with retrieval instructions. Add ## Prior Learnings
section to Step 3h template between ## Context and ## Material per
§17.2. Section is conditional — omitted when no learnings match."
```

---

### Task 3: Update Contract §17 — Remove Deferred Status

**Files:**
- Modify: `packages/plugins/cross-model/references/consultation-contract.md:440-443` (checklist)
- Modify: `packages/plugins/cross-model/references/consultation-contract.md:447-479` (§17 body)
- Modify: `scripts/validate_consultation_contract.py:163-172` (remove §17 deferred check)
- Modify: `tests/test_consultation_contract_sync.py:291-297,321-334` (update/remove deferred tests)

**Context:** §17 is marked "Deferred" because the card model it originally referenced was removed by the learning system redesign. Now that `retrieve_learnings.py` implements the retrieval protocol and T2/T3 wire it into both skills, the section should reflect the active implementation.

**Validation script impact:** `scripts/validate_consultation_contract.py:163-172` has a `check_deferred_annotations` function that enforces §16 contains "deferred" near §17 references. Removing "deferred" from §16 will trigger a NEW test failure in `test_deferred_sections_annotated` unless the validation script is updated. The test `test_missing_deferred_annotation_is_caught` tests the stale heuristic and must also be updated.

**What changes:**
- Title: remove "(Deferred)"
- Status blockquote: replace "Deferred" with "Active" and note the implementation
- §17.1: add reference to `retrieve_learnings.py` as the implementation
- §17.4: keep non-goals as still deferred (they genuinely are)
- Checklist: update to reflect completed items
- Add migration note for Engram (future path change)
- Validation script: remove §17-specific deferred check (§17 is now active)
- Validation test: remove stale `test_missing_deferred_annotation_is_caught`

**What does NOT change:**
- §17.2 injection points (already correct — T2/T3 implement exactly this)
- §17.3 entry format (already correct)

- [ ] **Step 1: Update the checklist (lines 440-443)**

Replace:
```markdown
**Learning Retrieval (§17)** *(deferred — card model removed by learning system redesign. See `docs/plans/2026-03-11-learning-system-redesign.md`)*
- [x] Fail-soft stub in place *(returns empty — no cards to inject)*
- [ ] ~~Cards capped at 5 per consultation~~ *(deferred — no card model in v1)*
- [ ] ~~Cards injected at correct point (§17.2)~~ *(deferred)*
```

With:
```markdown
**Learning Retrieval (§17)**
- [x] Retrieval script implemented (`scripts/retrieve_learnings.py`, 22 tests)
- [x] Entries capped at 5 per consultation (`--max-entries 5`)
- [x] Entries injected at correct point per §17.2 (`/codex` in `## Context`, `/dialogue` in `## Prior Learnings`)
- [x] Fail-soft on missing/empty learning store
```

- [ ] **Step 2: Update §17 title and status (lines 447-449)**

Replace:
```markdown
## 17. Learning Retrieval and Injection (Deferred)

> **Status: Deferred.** The learning system redesign (`docs/plans/2026-03-11-learning-system-redesign.md`) removed the card model this section depends on. The redesign uses a funnel (capture → stage → graduate to CLAUDE.md) instead of card-based injection. This section is retained as reference for a potential v2 feature: deterministic query-scoped retrieval of unpromoted learnings for Codex briefings.
```

With:
```markdown
## 17. Learning Retrieval and Injection

> **Status: Active.** Implemented via `scripts/retrieve_learnings.py` — keyword/tag-based retrieval from `docs/learnings/learnings.md`. Both `/codex` and `/dialogue` skills call the script before briefing assembly. Future migration: when Engram Step 2a lands, update the default path from `docs/learnings/learnings.md` to `engram/knowledge/learnings.md` (configurable via `--path`).
```

- [ ] **Step 3: Update §17.1 to reference the script**

Replace line 455 (first item in the numbered list):
```markdown
1. **Read learning store:** Read from `docs/learnings/learnings.md` (or the configured learning store path).
```

With:
```markdown
1. **Read learning store:** `scripts/retrieve_learnings.py` reads from `docs/learnings/learnings.md` by default. Override with `--path` for alternate locations (e.g., Engram migration).
```

- [ ] **Step 4: Update §17.4 title to clarify scope**

Replace:
```markdown
### 17.4 Non-Goals (Deferred)
```

With:
```markdown
### 17.4 Non-Goals (v2)
```

The items beneath are unchanged — mid-dialogue adaptive injection, ML scoring, and promote-meta filtering are genuinely future work.

- [ ] **Step 5: Update validation script — remove §17 deferred check**

In `scripts/validate_consultation_contract.py`, replace the `check_deferred_annotations` function body (lines 163-172):

```python
def check_deferred_annotations(contract_text: str) -> list[str]:
    """Verify that unimplemented sections are annotated as deferred in §16."""
    section = extract_section_text(contract_text, "## 16.")
    if section is None:
        return ["contract: §16 Conformance Checklist not found"]
    errors: list[str] = []
    # Heuristic: checks "deferred" appears near §17 refs. May need refinement if §16 grows.
    if "§17" in section and "deferred" not in section.lower():
        errors.append("contract §16: §17 items present but not annotated as deferred")
    return errors
```

With:

```python
def check_deferred_annotations(contract_text: str) -> list[str]:
    """Verify that unimplemented sections are annotated as deferred in §16.

    §17 (Learning Retrieval) is now active — no deferred check needed.
    Retained as scaffolding for future deferred sections.
    """
    section = extract_section_text(contract_text, "## 16.")
    if section is None:
        return ["contract: §16 Conformance Checklist not found"]
    return []
```

Also update the script's docstring (line 15) from:
```
5. §16 Conformance Checklist annotates §17 items as deferred.
```
To:
```
5. §16 Conformance Checklist structure is valid.
```

- [ ] **Step 6: Update validation test — remove stale deferred assertion**

In `tests/test_consultation_contract_sync.py`, remove the `test_missing_deferred_annotation_is_caught` test (lines 321-334):

```python
def test_missing_deferred_annotation_is_caught() -> None:
    """§16 referencing §17 without 'deferred' annotation is flagged."""
    contract_text = "\n".join(
        [
            "## 16. Conformance Checklist",
            "",
            "- [ ] §17 Cross-Model Learning items implemented",
            "",
            "## 17. Next Section",
        ]
    )
    errors = MODULE.check_deferred_annotations(contract_text)
    assert len(errors) >= 1
    assert any("deferred" in e.lower() for e in errors)
```

Delete this entire function. The test verified the §17-specific heuristic which no longer exists.

`test_deferred_sections_annotated` (lines 291-297) does NOT need changes — it calls `check_deferred_annotations` on the real contract and asserts `errors == []`. Since the function now returns `[]` unconditionally (no deferred sections to check), this test still passes.

- [ ] **Step 7: Run the contract sync test**

Run:
```bash
uv run pytest tests/test_consultation_contract_sync.py -v
```

Expected: `test_termination_reasons_match_contract` fails (pre-existing, unrelated to our changes). `test_missing_deferred_annotation_is_caught` no longer exists. All remaining tests pass — specifically `test_deferred_sections_annotated` should PASS.

**Note:** The pre-existing failure is in `test_termination_reasons_match_contract` — it tests termination reason sync between contract and code. It is NOT related to §17.

- [ ] **Step 8: Commit**

```bash
git add packages/plugins/cross-model/references/consultation-contract.md scripts/validate_consultation_contract.py tests/test_consultation_contract_sync.py
git commit -m "feat: activate contract §17 — learning retrieval implemented (Track A T4)

Remove Deferred status from §17. Update §16 checklist to reflect
completed implementation. Reference retrieve_learnings.py in §17.1.
Remove §17-specific deferred check from validation script (§17 is
now active). Add Engram migration note in status block."
```

---

### Task 4: Run Full Test Suite and Verify

**Files:** None (verification only)

- [ ] **Step 1: Run cross-model package tests**

Run:
```bash
uv run --package cross-model-plugin pytest packages/plugins/cross-model/tests/ -v --tb=short
```

Expected: 604 tests pass, 0 failures. The SKILL.md and contract edits are markdown — they don't affect test outcomes. This step confirms no accidental file corruption.

- [ ] **Step 2: Run retrieval script end-to-end**

Run:
```bash
python3 packages/plugins/cross-model/scripts/retrieve_learnings.py --query "credential scan security" --max-entries 3
```

Expected: 1-3 entries with security-related tags, followed by `<!-- learnings-injected: N -->`.

Run:
```bash
python3 packages/plugins/cross-model/scripts/retrieve_learnings.py --query "parallel agents codex dialogue" --max-entries 3
```

Expected: 1-3 entries with codex/workflow tags, followed by `<!-- learnings-injected: N -->`.

- [ ] **Step 3: Verify branch state**

Run:
```bash
git log --oneline feature/learning-injection...main
```

Expected: 8 commits (5 existing + 3 new from Tasks 1-3). All commits on `feature/learning-injection`.

---

### Task 5: Create PR

**Files:** None (git operations only)

**Decision point:** The branch mixes infrastructure work (test migration, import guards) with feature work (Track A). The handoff flagged this as an open question. Two options:

- **(A) Single PR** — simpler, all changes are on the same branch and already committed. Review is heavier but the work is coherent (all cross-model plugin improvements).
- **(B) Split PRs** — cherry-pick infrastructure commits to a separate branch/PR, keep Track A on its own PR. Cleaner history but more git surgery.

**Recommendation:** Option A (single PR). The infrastructure work was triggered by Track A development (test failures surfaced during Track A T1), so they form a coherent narrative. Note the two themes in the PR description.

- [ ] **Step 1: Push branch**

```bash
git push -u origin feature/learning-injection
```

- [ ] **Step 2: Create PR**

```bash
gh pr create \
  --title "feat: learning injection (Track A) + test migration" \
  --body "$(cat <<'EOF'
## Summary

- Wire `retrieve_learnings.py` into `/codex` and `/dialogue` skills for §17 learning injection
- Activate contract §17 (remove Deferred status, update checklist)
- Migrate 370 cross-model tests from repo root into package (`_legacy` suffix)
- Fix module-identity bug with `if __package__:` import guards across 6 scripts

## Track A: Learning Injection (T1–T4)

- **T1:** `retrieve_learnings.py` — keyword/tag-based retrieval (22 tests)
- **T2:** `/codex` SKILL.md — retrieval + injection into `## Context`
- **T3:** `/dialogue` SKILL.md — retrieval + injection as `## Prior Learnings` in Step 3h
- **T4:** Contract §17 — activated, checklist updated

## Infrastructure

- Test migration: 370 tests from `tests/` root into `packages/plugins/cross-model/tests/` using Codex-advised `import scripts.X as MODULE` alias pattern
- Import fix: `if __package__:` guard in 6 scripts to eliminate non-deterministic `try/except ModuleNotFoundError` pattern (10 ordering-sensitive failures fixed)

## Test plan

- [ ] 604 cross-model package tests pass (`uv run --package cross-model-plugin pytest`)
- [ ] `retrieve_learnings.py` returns relevant entries for test queries
- [ ] Contract sync test has no NEW failures (pre-existing `test_termination_reasons_match_contract` failure is known)
- [ ] SKILL.md edits render correctly (no broken markdown)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 3: Verify PR created**

Expected: PR URL returned. Branch tracking set.
