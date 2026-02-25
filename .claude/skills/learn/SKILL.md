---
name: learn
description: >-
  Capture project insights. Two modes: `/learn log` creates a structured,
  machine-validated episode (cross-model learning system). `/learn` (no
  subcommand) appends an unstructured insight to the learnings file (Phase 0).
  Use when user says "/learn", "capture this insight", "log this learning".
argument-hint: "[log [hint] | hint]"
---

# Learn

Capture project insights for re-injection in future sessions.

## Routing

Extract the first token from `$ARGUMENTS` (case-insensitive, split on whitespace):

| First token | Route | Remaining tokens |
|-------------|-------|------------------|
| `log` | Episode Logging (below) | Passed as hint context |
| `promote` | Reject: "Not yet available. `/learn promote` is Phase 1b." | — |
| *(anything else)* | Unstructured Capture (below) | Full `$ARGUMENTS` used as hint |
| *(empty)* | Unstructured Capture (below) | No hint |

**Routing rules:** Exact first-token match only. No prefix matching. Case-insensitive comparison (`Log`, `LOG`, `log` all route to Episode Logging).

---

## Episode Logging (`/learn log`)

Create a structured, machine-validated episode file in `docs/learnings/episodes/`.

**Reference:** `.claude/skills/learn/references/episode-schema.md` is authoritative for field definitions, enum tables, inference rules, and bias documentation. Read it before generating an episode.

### Procedure

#### 1. Determine next episode ID

- Glob `docs/learnings/episodes/EP-*.md`
- Parse the highest existing number (0 if none exist)
- Next ID = highest + 1, zero-padded to 4 digits (`EP-0001`, `EP-0002`, ...)

#### 2. Determine `source_type`

Review the conversation for Codex involvement:

- If the insight came from a **Codex disagreement, cross-model resolution, or contested claim** → suggest `dialogue`
- If the insight is from **solo work with no Codex contribution** → suggest `solo`

**Bias watch (B5):** The presence of any `/codex` tool usage does NOT automatically mean `dialogue`. Only use `dialogue` when the *insight itself* came from the cross-model interaction, not just because Codex was consulted during the session.

Present the suggested value and confirm with the user via AskUserQuestion:
- Options: `dialogue`, `solo`
- Default: the suggested value

#### 3. Infer `task_type` and `decision`

For each field, scan the conversation for relevant signals. Consult the signal table and inference rules in the schema reference.

**Inference rules (from schema reference — authoritative):**

1. Signals are suggestive, not deterministic. Never auto-assign.
2. Suggest when ≥1 strong signal OR ≥2 weak signals from different families.
3. Sparse, conflicting, or split signals → mark low confidence, ask user.
4. Explicit user statement overrides inference.

**For `decision`, apply negative-space guards:**
- `applied`: requires positive evidence AND no postponement language
- `rejected`: requires no "do later" markers
- `deferred`: requires explicit postpone/revisit marker
- Inconclusive → AskUserQuestion with all three options

**Bias watch:**
- B1 (label compression): If the session spans multiple task types, present the top 2-3 candidates and let the user choose.
- B2 (outcome optimism): Do not default to `applied`. Check for postponement language before suggesting it.
- B6 (deferred underproduction): Explicitly include `deferred` as an option — do not omit it.

Present each inferred value with a brief rationale. Confirm via AskUserQuestion:
- For `task_type`: show the suggested value and 1-2 alternatives
- For `decision`: show the suggested value with the signal rationale

#### 4. Collect remaining fields

- `title`: Draft a 1-line summary (~80 chars). Present for confirmation.
- `domain`: Infer from conversation topic. Present for confirmation.
- `keywords`: Suggest 1-5 tags. Present for confirmation. Reuse tags from existing episodes and learnings where possible.
- `languages` / `frameworks`: Scan conversation for languages and frameworks mentioned in context. Default to `[]` if none relevant.
- `safety`: Set to `true` if the episode touches auth, credentials, or secrets. Default `false`.

**Bias watch (B4):** For `languages`/`frameworks`, scan the full conversation, not just recent context. The last file touched is not necessarily representative of the session scope.

#### 5. Two-step confirmation

**Step A — Compact metadata summary:**

Present all frontmatter fields as a compact block:

```
Episode draft:

  id: EP-0003
  date: 2026-02-23
  title: Atomic cutover replaces dual-version transition windows
  source_type: dialogue
  domain: architecture
  task_type: design
  languages: [python]
  frameworks: []
  keywords: [schema-migration, scale]
  decision: applied
  decided_by: user
  safety: false
  schema_version: 1

Confirm, edit, or cancel?
```

**Step B — Handle response:**

- **Confirm:** proceed to draft body sections
- **Edit:** Accept `field=value` directives (e.g., `task_type=planning, keywords=[a,b,c]`). Any frontmatter field accepted. Invalid enum/field → show error with valid options. Multiple edits comma-separated. Re-display summary after edits.
- **Cancel:** abort episode creation

#### 6. Draft body sections

Based on `source_type` and `decision`, draft the appropriate sections:

- **Summary:** One sentence summarizing the episode. Self-contained — a future session should understand without the original conversation.
- **Claude Position** (dialogue only): Claude's argument or recommendation.
- **Codex Position** (dialogue only): Codex's counter-argument or alternative.
- **Resolution** (required when decision is `applied` or `rejected`): What was decided and why.
- **Evidence:** Supporting data — test results, patterns, code references.

If the user provided a hint (e.g., `/learn log the thing about scale`), focus the body content on that topic.

#### 7. Validate and write

1. Assemble the full episode file (frontmatter + body)
2. Write to a temp file
3. Run: `uv run scripts/validate_episode.py <temp-file>`
4. **On success (exit 0):** Move to `docs/learnings/episodes/EP-NNNN.md`
5. **On failure (exit 1):** Show validation errors. Fix the issue and retry from step 2. Do not write an invalid episode.

#### 8. Confirm

One-line summary: the EP ID, title, and file path.

```
Logged EP-0003: "Atomic cutover replaces dual-version transition windows" → docs/learnings/episodes/EP-0003.md
```

### Phase 0 hint

When running in Unstructured Capture mode (below), if the conversation shows signs of a Codex dialogue — cross-model disagreement, contested claims, position convergence — add a one-line suggestion after the capture:

> Tip: This insight came from a Codex dialogue. Consider `/learn log` for a structured episode.

This is a suggestion only. Do not block or redirect the Phase 0 flow.

---

## Unstructured Capture (`/learn`)

Extract an insight from the current conversation and append it to the project's learnings file for re-injection in future sessions. This is the Phase 0 path — quick, low-ceremony, append-only.

### Procedure

1. **Identify the insight.** Review the current conversation and extract the most notable insight.

   - If the user provided a hint (e.g., `/learn the thing about Codex infrastructure`), focus on that topic.
   - If no hint, identify the insight that would be most valuable in a future session — patterns discovered, mistakes caught, techniques that worked, architectural decisions and their reasoning.
   - Prefer specific, actionable insights over general observations.

2. **Select tags** from the table below. Pick 1-3 tags that fit. Create a new tag if none fit.

3. **Draft the entry** and present it to the user for confirmation:

   ```
   Draft learning:

   ### YYYY-MM-DD [tag1, tag2]

   One paragraph capturing the insight — specific enough to be actionable
   when re-read in a future session without the original context.

   Append to docs/learnings/learnings.md?
   ```

   Write the insight as a single paragraph. It should be self-contained — a future Claude session reading this entry should understand the insight without access to the original conversation.

4. **On confirmation, append the entry** to `docs/learnings/learnings.md`.

   If the file does not exist, create it with this header first:

   ```markdown
   # Learnings

   Project insights captured from consultations. Curate manually: delete stale entries, merge duplicates.
   ```

   Append using this exact format (preserve the blank line before the heading):

   ```markdown

   ### YYYY-MM-DD [tag1, tag2]

   The insight paragraph.
   ```

5. **Confirm** with a one-line summary: the date, tags, and first ~10 words of the insight.

### Example Tags

| Tag | Use for |
|-----|---------|
| `codex` | Insights from Codex dialogues |
| `architecture` | Architectural decisions and patterns |
| `debugging` | Debugging techniques and root causes |
| `workflow` | Process and workflow improvements |
| `testing` | Testing strategies and patterns |
| `security` | Security considerations |
| `pattern` | Reusable code or design patterns |
| `performance` | Performance optimization |
| `skill-design` | Skill authoring insights |
| `review` | Code review and feedback patterns |

These are examples, not a closed set. Create new tags when none fit.
