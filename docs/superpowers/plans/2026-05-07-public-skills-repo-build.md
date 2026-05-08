# Public Claude Code Skills Repo — Build Plan (ready-to-publish, halt before repo creation)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. The plan retains a small number of implementer-judgment caveats (Task 5 prose-only edits, Task 8 README/LICENSE prose specs) on the assumption that the executing Claude has full spec context — `subagent-driven-development` is **not recommended** for this plan because the per-task isolation strips that context. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a verified-ready local artifact at `/Users/jp/Projects/active/claude-code-skills/` — 22 sanitized skills, plugin manifests, repo-level docs, validated against a clean `~/.claude/skills/`, committed locally — **without creating a GitHub repo, pushing, or tagging**.

**Architecture:** Sequential workflow against the spec at `docs/superpowers/specs/2026-05-06-public-skills-repo-design.md` (v5, commit `9ab5a4ad`). Source = dev-monorepo `extensions/skills/`. Target = new standalone git repo at `/Users/jp/Projects/active/claude-code-skills/`. The work is mechanical (file copies + well-specified diffs + automated scans) with explicit user gates at preflight, post-sanitize scans, and clean-machine validation.

**Tech Stack:** `bash` (with `set -euo pipefail`), `git`, `gh` (only for `gh auth status` precondition in this phase), `trash-cli`, `ripgrep` (PCRE mode), `tar`, `claude` CLI (manual user invocations at preflight + validation gates).

**Spec ↔ plan mapping:** Spec Steps 0-8 are in scope (Tasks 1-10 below). Spec Steps 9-11 (`gh repo create`, push, tag, marketplace install verification) are deferred to a follow-up plan.

**Out of scope:** GitHub repo creation, `git push`, tagging `v0.1.0`, `--add-topic`, marketplace install verification, post-publish success-criteria tracking.

---

## File Structure (target repo)

After execution, `/Users/jp/Projects/active/claude-code-skills/` contains:

```
.git/                              # initialized in Task 3
.claude-plugin/
├── plugin.json                    # Task 8
└── marketplace.json               # Task 8
skills/                            # 22 directories, populated in Task 4, sanitized in Task 5
├── adversarial-review/SKILL.md
├── claude-md/{SKILL.md,references/}
├── design-review-team/{SKILL.md,references/}
├── exiting-worktrees/SKILL.md
├── explore-repo/{SKILL.md,references/}
├── format-export/SKILL.md
├── git-hygiene/SKILL.md
├── handbook/{SKILL.md,references/}
├── implementation-review/SKILL.md
├── llm-reference/SKILL.md
├── making-recommendations/SKILL.md
├── merge-branch/SKILL.md
├── next-steps/SKILL.md
├── prompt-generator/SKILL.md
├── readme/{SKILL.md,references/}
├── review-code/SKILL.md
├── review-plan/SKILL.md
├── review-strategy/SKILL.md
├── review-writing/SKILL.md
├── scrutinize/SKILL.md
├── system-design-review/SKILL.md
└── writing-principles/{SKILL.md,writing-principles.md}
README.md                          # Task 8
LICENSE                            # Task 8
CHANGELOG.md                       # Task 8
CONTRIBUTING.md                    # Task 8
.gitignore                         # Task 8
```

After Task 10, this repo holds exactly one commit on `main`. Nothing has been pushed anywhere.

## Conventions for this plan

- **All bash invocations begin with `set -euo pipefail`** if they are multi-command. The spec hardens this at the top of the full workflow; we preserve it per task so each task is independently runnable.
- **No `rm` or `rm -rf`** anywhere. Deletions use `trash`. The dev environment's CLAUDE.md prohibits `rm`; plan inherits that rule.
- **Working directory** for Tasks 3-10 is the target repo (`/Users/jp/Projects/active/claude-code-skills/`), unless otherwise stated.
- **Manual user gates** (preflight, clean-machine validation) are clearly marked `[USER GATE]`. Claude does not run these — the user runs `claude` in a separate session and reports back.
- **Commits**: zero commits in Tasks 3-9. The target repo accumulates uncommitted state until Task 10's single "Initial release" commit, matching the spec's bash workflow. The plan file itself is committed to the dev monorepo separately (after this plan is written), not as a plan task.
- **Shell variable scope:** Some tasks set shell variables in one step that are referenced in later steps — `SCRATCH` in Task 2 (Step 1 → Step 3), `BACKUP` in Task 9 (Step 2 → Step 5), `TMPSKILLS` in Task 9 (Step 3 → Step 4 → trap). Each Bash tool invocation is a **separate shell** — variables do not persist across calls. For each affected task, **execute all variable-dependent steps within a single Bash tool invocation** (one `<bash>` block covering Steps N..M), or save the printed path from the assigning step's output and pass it as a literal value in the dependent step. The plan flags re-derivation paths inline (`# or: trash <path-from-Step-1> if SCRATCH var was lost`) — those are fallbacks, not the primary path.

---

## Task 1: Preconditions verification

**Goal:** Verify the four preconditions in spec lines 253-258 before any filesystem mutation.

**Files:** none modified.

- [ ] **Step 1: Verify `gh auth status`**

```bash
gh auth status
```

Expected: output contains `Logged in to github.com account ...` with no `not logged in` line.

If FAIL: halt. Run `gh auth login` and retry. Spec Steps 9-10 (deferred) need this; later tasks don't, but a failing precondition here predicts a stuck publish phase later.

- [ ] **Step 2: Verify `trash` is on PATH**

```bash
command -v trash
```

Expected: prints a path (e.g., `/opt/homebrew/bin/trash`). Empty output = not installed.

If FAIL: halt. Run `brew install trash` and retry. Tasks 4 (`.DS_Store` strip) and 10 (validation cleanup) require it.

- [ ] **Step 3: Verify `git --version` ≥ 2.28**

```bash
git --version
```

Expected: `git version 2.28.0` or higher (decimal compare on the second component).

If FAIL: halt. Task 3 uses `git init -b main`, which lands in 2.28. Older git would silently create `master` instead.

- [ ] **Step 4: Verify `claude --version` ≥ 2.1.32**

```bash
claude --version
```

Expected: `2.1.32` or higher.

If FAIL: continue with WARNING. Task 9 spot-checks of agent-teams skills (`claude-md`, `design-review-team`, `explore-repo`, `handbook`, `readme`) will hard-stop — the user can either upgrade or skip those 5 skills' invocation tests.

- [ ] **Step 5: Verify `rg` supports PCRE**

```bash
echo "test" | rg --pcre2 -n 'test' >/dev/null && echo "PCRE2 OK"
```

Expected: prints `PCRE2 OK`. Any `error: PCRE2 is not available` (or non-zero exit before the echo) means PCRE2 isn't compiled in.

If FAIL: halt. Task 7's structural scan (regex (a) and (e)) requires `--pcre2`. The Homebrew `rg` ships with it; an older / minimal build may not.

- [ ] **Step 6: Confirm preconditions pass**

Report each result. If all six pass, proceed to Task 2.

---

## Task 2: Step 0 — preflight `marketplace.json source: "./"`

**Goal:** Validate that the running `claude` CLI accepts `source: "./"` in the marketplace manifest, before committing to the spec's flat layout. Docs verification ≠ runtime acceptance.

**Files:** scratch repo at `$(mktemp -d)`, ephemeral.

- [ ] **Step 1: Generate the scratch repo**

```bash
set -euo pipefail
SCRATCH=$(mktemp -d)
( cd "$SCRATCH"
  git init -q
  mkdir -p .claude-plugin skills/test-skill
  cat > .claude-plugin/plugin.json <<'EOF'
{
  "name": "test-skill",
  "description": "Pre-validation of source path."
}
EOF
  cat > .claude-plugin/marketplace.json <<'EOF'
{
  "name": "test-mp",
  "description": "Pre-validation marketplace.",
  "owner": {"name": "x"},
  "plugins": [
    {"name": "test-skill", "source": "./", "description": "Pre-validation."}
  ]
}
EOF
  cat > skills/test-skill/SKILL.md <<'EOF'
---
name: test-skill
description: A test skill for pre-validating source-path acceptance.
---
# Test Skill
Used only for source-path pre-validation.
EOF
  git add .claude-plugin/plugin.json .claude-plugin/marketplace.json skills/test-skill/SKILL.md
  git commit -q -m "test"
)
echo "Scratch repo at: $SCRATCH"
```

Expected: Final line prints `Scratch repo at: /var/folders/.../tmp.XXXXXX`. Save that path.

- [ ] **Step 2: [USER GATE] Validate in a fresh `claude` session**

The user opens a new terminal / claude session and runs:

```
/plugin marketplace add <SCRATCH-path-from-Step-1>
/plugin install test-skill@test-mp
```

PASS condition: install completes without error; `/plugin` shows `test-skill` installed.

FAIL condition: any error mentioning `source`, `path`, or rejected manifest.

User reports back: PASS or FAIL.

- [ ] **Step 3: Branch on result**

**If PASS:** the spec's flat layout is valid. Cleanup and proceed:

```bash
trash "$SCRATCH"   # or: trash <path-from-Step-1> if SCRATCH var was lost
```

**If FAIL:** **halt the entire plan**. Do not proceed to Task 3. Restructure the spec for nested layout (plugin contents in `plugins/claude-code-skills/`, `marketplace.json source: "./plugins/claude-code-skills"`) BEFORE re-running Tasks 1-10. Update the plan to match the restructured spec.

---

## Task 3: Initialize the target repo

**Goal:** Create the empty target repo with `main` as the initial branch.

**Files:**
- Create: `/Users/jp/Projects/active/claude-code-skills/.git/`

- [ ] **Step 1: Create directory and init**

```bash
set -euo pipefail
mkdir /Users/jp/Projects/active/claude-code-skills
cd /Users/jp/Projects/active/claude-code-skills
git init -b main
```

Expected output: `Initialized empty Git repository in /Users/jp/Projects/active/claude-code-skills/.git/`.

If `mkdir` fails with `File exists`, halt and ask the user: stale dir from a prior attempt? Decide whether to `trash` it or pick a different path.

- [ ] **Step 2: Verify**

```bash
cd /Users/jp/Projects/active/claude-code-skills
git status
git branch --show-current
```

Expected: `git status` reports `On branch main` and `No commits yet`. `git branch --show-current` prints `main`.

---

## Task 4: Build directory structure + copy 22 skills via allowlist

**Goal:** Populate `skills/` with 22 directories containing only the sanctioned content (SKILL.md + references/ + examples/ + top-level *.md siblings).

**Files:**
- Create: `.claude-plugin/`
- Create: `skills/<skill-name>/...` × 22

- [ ] **Step 1: Build directory skeleton**

```bash
set -euo pipefail
cd /Users/jp/Projects/active/claude-code-skills
mkdir -p .claude-plugin skills
```

- [ ] **Step 2: Copy the 22 skills via allowlist**

```bash
set -euo pipefail
cd /Users/jp/Projects/active/claude-code-skills
SRC=/Users/jp/Projects/active/claude-code-tool-dev/extensions/skills
for skill in adversarial-review claude-md design-review-team exiting-worktrees explore-repo \
             format-export git-hygiene handbook implementation-review llm-reference \
             making-recommendations merge-branch next-steps prompt-generator readme \
             review-code review-plan review-strategy review-writing scrutinize \
             system-design-review writing-principles; do
  mkdir -p "skills/$skill"
  cp "$SRC/$skill/SKILL.md" "skills/$skill/SKILL.md"
  for sub in references examples; do
    if [ -d "$SRC/$skill/$sub" ]; then
      cp -r "$SRC/$skill/$sub" "skills/$skill/$sub"
    fi
  done
  find "$SRC/$skill" -maxdepth 1 -name '*.md' ! -name 'SKILL.md' -exec cp {} "skills/$skill/" \;
done
```

The allowlist intrinsically excludes `.DS_Store`, `evals/`, `*-workspace/`, `iteration-*/`, `*.local.md`. No denylist sweep is needed (and `rm -rf` is prohibited anyway).

- [ ] **Step 3: Strip `.DS_Store` files (defense-in-depth)**

```bash
set -euo pipefail
cd /Users/jp/Projects/active/claude-code-skills
find skills -name '.DS_Store' -exec trash {} \;
```

`.DS_Store` shouldn't be present (allowlist excludes it), but macOS may have written some during the `cp` traversal — this catches that.

- [ ] **Step 4: Verify**

```bash
set -euo pipefail
cd /Users/jp/Projects/active/claude-code-skills
echo "Skill directories:"; ls -1 skills | wc -l
echo "SKILL.md files:";    find skills -name SKILL.md | wc -l
echo "Forbidden patterns:"
find skills \( -name '.DS_Store' -o -name 'evals' -o -name '*-workspace' -o -name 'iteration-*' \)
echo "writing-principles supplementary file:"
ls skills/writing-principles/writing-principles.md
```

Expected:
- Skill directories: `22`
- SKILL.md files: `22`
- Forbidden patterns: empty (no output, find exits 0)
- writing-principles supplementary file: prints the path (file exists, ~71 KB)

If counts ≠ 22, halt and inspect the loop output for missed copies. If forbidden patterns appear, halt and `trash` them before continuing.

---

## Task 5: Sanitize the 10 SANITIZE skills

**Goal:** Apply the diffs in spec lines 60-71 to remove dangling structural references and internal-vocab leakage. Each substep is one skill. After each, a quick `rg` confirms the change took effect.

**Files (all under `/Users/jp/Projects/active/claude-code-skills/`):**
- Modify: `skills/claude-md/SKILL.md`
- Modify: `skills/git-hygiene/SKILL.md`
- Modify: `skills/next-steps/SKILL.md`
- Modify: `skills/merge-branch/SKILL.md`
- Modify: `skills/making-recommendations/SKILL.md`
- Delete: `skills/making-recommendations/references/codex-delta.md`
- Modify: `skills/writing-principles/SKILL.md`
- Modify: `skills/handbook/SKILL.md`
- Modify: `skills/handbook/references/agent-teams.md`
- Modify: `skills/readme/references/agent-teams.md`
- Modify: `skills/design-review-team/references/agent-teams.md`
- Modify: `skills/explore-repo/references/agent-teams.md`

> Line numbers below reference the source files in `~/.claude/skills/<name>/...` and the spec. Always re-read the file before editing — line numbers may shift between source-of-truth and the just-copied target. Use exact-string matching, not line numbers, when applying edits.

- [ ] **Step 1: `claude-md` SKILL.md (4 changes)**

File: `skills/claude-md/SKILL.md`.

1. **Description trailing sentence** — drop `For quick session-scoped updates, use \`/revise-claude-md\`.` (entire sentence).
2. **Description sibling phrasing** — replace `Distinct from README (introducing the project), handbook (operating the system), and changelog (tracking changes).` with `Distinct from README (introducing the project), handbook (operating the system), and CHANGELOG.md (tracking changes).`
3. **Decision Routing table cell** — replace value cell `Changelog skill` with `Write a CHANGELOG.md`. (If the rephrased cell reads awkwardly out of context, drop the row entirely — implementer's judgment.)
4. **Decision Routing table row** — drop the entire row whose key cell is `'Remember this for next time' / session note` and value cell is `/revise-claude-md`. Verify surrounding rows still cover the surrounding cases.

Verify:

```bash
rg -n 'revise-claude-md|Changelog skill|and changelog' skills/claude-md/SKILL.md || echo "CLEAN"
```

Expected: `CLEAN` (or no output — `rg` exits non-zero on no match, hence `|| echo`).

- [ ] **Step 2: `git-hygiene` SKILL.md (2 lines)**

File: `skills/git-hygiene/SKILL.md`.

Replace `codex/cleanup/YYYY-MM-DD-HHMMSS` with `cleanup/YYYY-MM-DD-HHMMSS` (drops the `codex/` prefix). Two occurrences: spec calls out lines 47 and 330 in the source file. Use `rg` to find current locations in the just-copied file:

```bash
rg -n 'codex/cleanup' skills/git-hygiene/SKILL.md
```

Apply each edit. Verify:

```bash
rg -n 'codex/cleanup' skills/git-hygiene/SKILL.md || echo "CLEAN"
```

Expected: `CLEAN`.

- [ ] **Step 3: `next-steps` SKILL.md (4 changes)**

File: `skills/next-steps/SKILL.md`.

1. **Line 21 (table cell)** — replace `"Use Next Steps protocol instead"` with `"Use session-sized implementation planning instead"`.
2. **Line 26** — replace `Output feeds into Codex dialogue or focused planning sessions` with `Output feeds into deeper planning sessions`.
3. **Line 28** — replace `If the conversation already has a clear implementation path, use the Next Steps protocol from CLAUDE.md instead.` with `If the conversation already has a clear implementation path, use session-sized implementation planning instead.`
4. **Lines 155-157 (entire paragraph)** — replace BOTH sentences

   `Suggest the user take the highest-risk or first-phase tasks into a Codex dialogue for deeper exploration. Use the literal slash command \`/codex-collaboration:dialogue\` so the user can invoke it directly.`

   with one sentence:

   `If you have a follow-up advisor skill, dispatch it here.`

   Do not leave any "Codex dialogue" residue.

Verify:

```bash
rg -i -n 'codex|next steps protocol|/codex-collaboration' skills/next-steps/SKILL.md || echo "CLEAN"
```

Expected: `CLEAN`.

- [ ] **Step 4: `merge-branch` SKILL.md (1 line)**

File: `skills/merge-branch/SKILL.md`.

Replace bullet `User wants a PR — use the commit-push-pr workflow instead` with `User wants a PR — push and open a PR via your normal workflow instead.`

Verify:

```bash
rg -n 'commit-push-pr' skills/merge-branch/SKILL.md || echo "CLEAN"
```

Expected: `CLEAN`.

- [ ] **Step 5: `making-recommendations` (delete file + remove subsection)**

File 1 (delete): `skills/making-recommendations/references/codex-delta.md`

```bash
# `|| true` so a re-run after a partial failure doesn't error if the file is already trashed.
trash skills/making-recommendations/references/codex-delta.md 2>/dev/null || true
[ -e skills/making-recommendations/references/codex-delta.md ] && echo "TRASH FAILED" || echo "GONE"
```

File 2 (modify): `skills/making-recommendations/SKILL.md`

Remove the entire `## Codex Delta` subsection and its content. Spec calls out lines 137-143. Find current location:

```bash
rg -n '## Codex Delta|codex-delta' skills/making-recommendations/SKILL.md
```

Delete the heading and all lines through the next `##` (or end-of-file, whichever comes first). After deletion, scan the surrounding I8-I9 phase text and confirm no dangling reference remains to "Codex Delta".

Verify:

```bash
rg -i -n 'codex' skills/making-recommendations/ || echo "CLEAN"
```

Expected: `CLEAN`.

- [ ] **Step 6: `writing-principles` SKILL.md (remove Composability section)**

File: `skills/writing-principles/SKILL.md`.

Remove the `## Composability` section starting at line 140 and continuing to end-of-file. Spec verifies the section above (`## Failure Mode Index`) ends cleanly at line 138, so deletion is bounded by `## Composability` ... `EOF`.

Method: read the file, locate line containing `^## Composability$`, delete that line and everything after.

Verify:

```bash
rg -n '^## ' skills/writing-principles/SKILL.md
rg -n 'creating-skills|claude-md-improver|Composability' skills/writing-principles/SKILL.md || echo "CLEAN"
```

Expected: the first command lists section headings, with `## Failure Mode Index` as the last entry. The second command outputs `CLEAN`.

Note: do NOT touch `skills/writing-principles/writing-principles.md` (the 71 KB supplementary file). Lines 54 and 1025 are documented false positives for the Step 5 grep (Task 8) — they are common-English usage of "delegated" and "dialogue", not internal vocab. Leave them.

- [ ] **Step 7: `handbook` (3 changes across 2 files)**

File 1: `skills/handbook/SKILL.md`, line 3 (description) — replace `Distinct from READMEs (what it is) and CHANGELOGs (what changed).` with `Distinct from README files (introducing the system to users) and CHANGELOG.md files (tracking history).`

File 2: `skills/handbook/references/agent-teams.md`:
1. Line 3 — remove the line containing `Adapted from \`packages/plugins/superspec/...\`` (entire line).
2. Line 4 — replace `For documentation skills (readme, changelog, handbook).` with `For documentation skills (readme, handbook).`

Verify:

```bash
rg -i -n 'CHANGELOGs|superspec|readme, changelog' skills/handbook/ || echo "CLEAN"
```

Expected: `CLEAN`.

- [ ] **Step 8: `readme` (2 changes in agent-teams.md)**

File: `skills/readme/references/agent-teams.md`:
1. Line 3 — remove the `Adapted from \`packages/plugins/superspec/...\`` line.
2. Line 4 — replace `For documentation skills (readme, changelog, handbook).` with `For documentation skills (readme, handbook).`

Verify:

```bash
rg -i -n 'superspec|readme, changelog' skills/readme/ || echo "CLEAN"
```

Expected: `CLEAN`.

- [ ] **Step 9: `design-review-team` (2 changes in agent-teams.md)**

File: `skills/design-review-team/references/agent-teams.md`:
1. Line 3 — remove the `Adapted from \`packages/plugins/superspec/...\`` line.
2. Line 4 — replace `For documentation skills (readme, changelog, handbook).` with `Used by skills that orchestrate parallel agent teams.` (one rewrite kills both the dangling `changelog` and the misattribution.)

(Spec note: `SKILL.md:243` `docs/audits/` reference is already conditional — no change.)

Verify:

```bash
rg -i -n 'superspec|changelog' skills/design-review-team/ || echo "CLEAN"
```

Expected: `CLEAN`.

- [ ] **Step 10: `explore-repo` (1 change in agent-teams.md)**

File: `skills/explore-repo/references/agent-teams.md`:
1. Line 3 — remove the `Adapted from \`packages/plugins/superspec/...\`` line.

(Line 4 reads `For exploration skills (explore-repo).` — no `changelog` mention, no change needed.)

Verify:

```bash
rg -i -n 'superspec' skills/explore-repo/ || echo "CLEAN"
```

Expected: `CLEAN`.

- [ ] **Step 11: Roll-up verify across all 10 sanitized skills**

```bash
set -euo pipefail
cd /Users/jp/Projects/active/claude-code-skills
echo "--- per-skill residue check ---"
for s in claude-md git-hygiene next-steps merge-branch making-recommendations writing-principles handbook readme design-review-team explore-repo; do
  hits=$(rg -i -c '/revise-claude-md|/codex-collaboration|codex/cleanup|commit-push-pr|next steps protocol|codex delta|superspec|readme, changelog|creating-skills|claude-md-improver' "skills/$s/" 2>/dev/null || true)
  echo "$s: ${hits:-0 hits}"
done
```

Expected: each skill prints `0 hits` (or no count line, since `rg -c` skips files with no match). Any nonzero count means a sanitization edit didn't take — re-apply.

---

## Task 6: Step 4b — structural-reference scan (5 categories)

**Goal:** Confirm no dangling structural references survive Task 5. Lexical residue grep (Task 7) catches different things — it can't see plugin-relative slash commands or named-protocol references that use generic English words.

**Files:** read-only.

- [ ] **Step 1: Category (a) — slash-command refs (PCRE, narrowed)**

```bash
cd /Users/jp/Projects/active/claude-code-skills
rg -nP '\B/[a-z][a-z0-9-]+(?::[a-z0-9-]+)?' skills/
```

Expected: ~40 hits (spec measured this). Eyeball-skip these documented false positives:
- `~/.claude/teams/...`, `~/.claude/tasks/...` — functional Claude Code paths (Risk #6 in spec).
- `{workspace}/exploration/...` — template placeholders in `agent-teams.md`.
- Built-in Claude Code commands: `/resume`, `/rewind`, `/help`, `/export`, `/clear`.
- URL bodies: `https://...`, `code.claude.com/...`.

A real defect looks like a plugin-relative slash command not in the 22-set (e.g., `/revise-claude-md`, `/codex-collaboration:dialogue`). If any appear, return to Task 5 and re-sanitize.

- [ ] **Step 2: Category (b) — named-skill refs in tables/prose**

Read each shipped SKILL.md description and the first ~30 lines for "X skill" / "the X skill" / "and X (...)" / "Distinct from X" patterns. Each X must be in the 22-set OR refer to a file/format (e.g., `CHANGELOG.md` not `Changelog skill`).

Quick scan command:

```bash
cd /Users/jp/Projects/active/claude-code-skills
rg -n 'the [a-z][a-z0-9-]+ skill|and [a-z][a-z0-9-]+ \(|Distinct from' skills/ | head -40
```

Expected: every named X resolves to a 22-set skill or a file/format. Flag any that doesn't.

- [ ] **Step 3: Category (c) — environmental flag deps**

```bash
cd /Users/jp/Projects/active/claude-code-skills
rg -n 'CLAUDE_CODE_EXPERIMENTAL_|CLAUDE_[A-Z_]+' skills/
```

Expected: hits should ONLY appear in skills documented in the README Requirements section (`claude-md`, `design-review-team`, `explore-repo`, `handbook`, `readme`) — and specifically referencing `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. Any other env-flag dependency must either be documented in README Requirements (Task 8, Step 3) or removed.

- [ ] **Step 4: Category (d) — sibling-skill cross-references**

Search for `"Distinct from X, Y, Z"` patterns (most common in description blocks):

```bash
cd /Users/jp/Projects/active/claude-code-skills
rg -nP 'Distinct from [a-z]' skills/
```

Expected: each named sibling must be in the 22-set OR converted to file/format (e.g., `CHANGELOG.md` not `changelog`).

- [ ] **Step 5: Category (e) — named protocols / procedures / workflows**

```bash
cd /Users/jp/Projects/active/claude-code-skills
rg -nP '\b[\w-]+(?:[\s-][\w-]+)*\s+(workflow|protocol|procedure)\b' skills/
```

**Expected hit count:** typically 30-80 matches. The regex is intentionally over-broad — `\b[\w-]+(?:[\s-][\w-]+)*\s+(workflow|protocol|procedure)\b` captures any noun-phrase prefix before the three trigger words, so generic English ("standard build workflow", "review procedure", "internal protocol") shows up alongside the real targets. The verification is a **manual scan**, not a count threshold. Compare to Step 1 (slash commands) where ~40 hits resolve to a 4-item documented FP list.

If hit count is < ~10 or > ~150, treat that as a signal something is off (regex misbehaving, sanitize phase missed, or shipped set wrong) — not a pass/fail gate, but worth pausing to investigate before scrolling through.

Each match must refer to a real entity defined in shipped content OR be reworded to a generic phrase. Specifically watch for:
- `the X workflow` where X is a name not in 22-set (e.g., `the commit-push-pr workflow` from `merge-branch`, fixed in Task 5 Step 4).
- `X protocol from CLAUDE.md` (e.g., the phantom `Next Steps protocol` from `next-steps`, fixed in Task 5 Step 3).
- `X procedure` referring to anything not shipped.

If any real defect appears, return to Task 5 and add a sanitization edit.

- [ ] **Step 6: [USER GATE] Confirm zero dangling refs**

Report each category's findings. User confirms all hits are documented FPs or already-fixed. Proceed to Task 7.

If unresolved dangling refs remain: do NOT proceed. Add the fix as a new Task 5 substep, re-run Task 5 verify roll-up, then re-run Task 6.

---

## Task 7: Step 5 — lexical residue grep (automated)

**Goal:** Confirm no internal-vocab tokens survive in shipped content. This is a complete-within-its-scope mechanical check — the regex enumerates 18+ token categories.

**Files:** read-only.

- [ ] **Step 1: Run the residue grep**

```bash
cd /Users/jp/Projects/active/claude-code-skills
rg -i -n 'codex|cross-model|engram|superpowers|superspec|page[ -]?turner|claude-code-tool-dev|jpsweeney97|sweeney|handoff-archivist|claude-md-improver|creating-skills|cc-docs|openai-docs|claude-code-docs|evaluating-extension-adoption|exploring-claude-repos|delegate|delegation|dialogue|extensions/skills|scripts/promote|docs/learnings|docs/handoffs|docs/tickets|claude_ai_|/Users/jp|T-20[0-9]{6}|packages/plugins|revise-claude-md' skills/
```

Expected output: ONLY these two documented false positives:
- `skills/writing-principles/writing-principles.md:54` (text: "Scoped instructions for delegated tasks")
- `skills/writing-principles/writing-principles.md:1025` (text: "Dynamic dialogue has different constraints")

Any other hit is real residue and must be fixed in Task 5 before continuing.

- [ ] **Step 2: [USER GATE] Confirm only documented FPs remain**

Report the grep output. User confirms exactly the two FPs above and nothing else. Proceed to Task 8.

If real residue appears: return to Task 5, add sanitization for the new finding, re-verify, then re-run this task.

---

## Task 8: Write plugin manifests + repo docs

**Goal:** Create `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `README.md`, `LICENSE`, `CHANGELOG.md`, `CONTRIBUTING.md`, `.gitignore`. Each substep writes exactly one file with full content from the spec.

**Files:**
- Create: `.claude-plugin/plugin.json`
- Create: `.claude-plugin/marketplace.json`
- Create: `README.md`
- Create: `LICENSE`
- Create: `CHANGELOG.md`
- Create: `CONTRIBUTING.md`
- Create: `.gitignore`

- [ ] **Step 1: Write `.claude-plugin/plugin.json`** (spec lines 116-128)

```json
{
  "$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json",
  "name": "claude-code-skills",
  "description": "A curated collection of Claude Code skills for rigorous review, adversarial critique, and grounded documentation.",
  "author": {
    "name": "JP Sweeney",
    "url": "https://github.com/jpsweeney97"
  },
  "homepage": "https://github.com/jpsweeney97/claude-code-skills",
  "repository": "https://github.com/jpsweeney97/claude-code-skills",
  "license": "MIT",
  "keywords": ["claude-code", "skills", "code-review", "documentation", "adversarial-review"]
}
```

Verify:

```bash
rg -n '"version"' /Users/jp/Projects/active/claude-code-skills/.claude-plugin/plugin.json && echo "FAIL: version field present" || echo "CLEAN"
python3 -c 'import json; json.load(open("/Users/jp/Projects/active/claude-code-skills/.claude-plugin/plugin.json"))' && echo "JSON OK"
```

Expected: `CLEAN` (no version field) and `JSON OK` (parses).

- [ ] **Step 2: Write `.claude-plugin/marketplace.json`** (spec lines 136-150)

```json
{
  "name": "jpsweeney97-skills",
  "description": "JP Sweeney's curated Claude Code skills",
  "owner": {
    "name": "JP Sweeney",
    "url": "https://github.com/jpsweeney97"
  },
  "plugins": [
    {
      "name": "claude-code-skills",
      "source": "./",
      "description": "A curated collection of Claude Code skills for rigorous review, adversarial critique, and grounded documentation."
    }
  ]
}
```

Verify:

```bash
python3 -c 'import json; m=json.load(open("/Users/jp/Projects/active/claude-code-skills/.claude-plugin/marketplace.json")); assert m["plugins"][0]["source"] == "./"; print("OK")'
```

Expected: `OK`.

- [ ] **Step 3: Write `README.md`** (spec lines 157-191)

Sections, in order:

1. **Title + one-paragraph hook.** Mention focus areas (review, critique, grounded documentation) and that everything is also installable.
2. **Namespacing note + Trigger-shadow note.** Two short paragraphs, prominent. Use the verbatim text from spec lines 165-167:
   - Manual invocation: `/claude-code-skills:<name>` (e.g., `/claude-code-skills:scrutinize`).
   - Auto-trigger conflicts: lead with [`skillOverrides`](https://code.claude.com/docs/en/skills#override-skill-visibility-from-settings) — settings-level mechanism, no skill-editing required.
3. **Requirements** (prominent). Verbatim from spec lines 168-173:
   - Claude Code v2.1.32+. Check with `claude --version`. Link to official agent-teams docs.
   - `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in `settings.json`. Affects `claude-md`, `design-review-team`, `explore-repo`, `handbook`, `readme` (5 of 22).
   - Note: agent-teams is experimental; rename/deprecation handled via bug reports.
4. **What's in here.** Skill catalog grouped by category (table from spec lines 184-191):
   | Category | Skills |
   |----------|--------|
   | Review & adversarial critique | `adversarial-review`, `scrutinize`, `implementation-review`, `system-design-review`, `design-review-team`, `review-code`, `review-plan`, `review-strategy`, `review-writing` |
   | Grounded documentation generation | `readme`, `handbook`, `claude-md` |
   | Repo exploration & analysis | `explore-repo`, `llm-reference` |
   | Workflow | `git-hygiene`, `merge-branch`, `exiting-worktrees`, `next-steps`, `making-recommendations`, `prompt-generator`, `format-export` |
   | Authoring | `writing-principles` |

   Each entry one-liner-linked to its `SKILL.md`. Optional ↗ footnote on the 5 agent-teams-dependent skills pointing to Requirements.
5. **Install.** Two paths:
   - **Try it (clone + dev flag):** `git clone https://github.com/jpsweeney97/claude-code-skills` then `claude --plugin-dir <path-to-clone>`. NB: clone is permanent; only the plugin load is session-scoped.
   - **Install permanently (marketplace):** `/plugin marketplace add jpsweeney97/claude-code-skills` then `/plugin install claude-code-skills@jpsweeney97-skills`.
6. **Use a skill.** Brief example: `/claude-code-skills:scrutinize` invocation.
7. **Contributing.** Short policy: issues welcome (bug reports, feature requests). PRs reviewed case-by-case. Public repo is canonical. Link to CONTRIBUTING.md.
8. **License.** MIT, link to LICENSE.
9. **Author.** JP Sweeney, https://github.com/jpsweeney97.

Voice: first-person, technical, direct (matches SKILL.md voice).

Verify:

```bash
rg -n 'skillOverrides|v2\.1\.32|CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS|/claude-code-skills:' /Users/jp/Projects/active/claude-code-skills/README.md
```

Expected: hits for all four tokens (every Requirements + namespacing element present).

- [ ] **Step 4: Write `LICENSE`** (MIT, copyright "JP Sweeney", year 2026)

Standard MIT template. Header line:

```
MIT License

Copyright (c) 2026 JP Sweeney

Permission is hereby granted, free of charge, ...
```

(Use the canonical MIT body — `https://opensource.org/license/mit/`.)

Verify:

```bash
rg -n 'MIT License|Copyright \(c\) 2026 JP Sweeney' /Users/jp/Projects/active/claude-code-skills/LICENSE
```

Expected: both lines found.

- [ ] **Step 5: Write `CHANGELOG.md`** (spec lines 219-247)

Format: Keep a Changelog 1.1.0 + Semantic Versioning 2.0.0.

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-MM-DD

> Use the actual publish date when v0.1.0 ships.

### Added

- **Review & adversarial critique** (9 skills): `adversarial-review`, `scrutinize`, `implementation-review`, `system-design-review`, `design-review-team`, `review-code`, `review-plan`, `review-strategy`, `review-writing`.
- **Grounded documentation generation** (3 skills): `readme`, `handbook`, `claude-md`.
- **Repo exploration & analysis** (2 skills): `explore-repo`, `llm-reference`.
- **Workflow** (7 skills): `git-hygiene`, `merge-branch`, `exiting-worktrees`, `next-steps`, `making-recommendations`, `prompt-generator`, `format-export`.
- **Authoring** (1 skill): `writing-principles`.
- Marketplace catalog at `.claude-plugin/marketplace.json` for one-line install.
- README with namespacing + Trigger-shadow + Requirements sections; CONTRIBUTING.md with maintenance flow; MIT license.

### Notes

- Five skills (`claude-md`, `design-review-team`, `explore-repo`, `handbook`, `readme`) require Claude Code v2.1.32+ and `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. See README Requirements section.
```

Note: `2026-MM-DD` is a placeholder — replace with the actual publish date in the follow-up plan (when the spec's Step 9 `gh repo create` runs), NOT in this build phase. The pre-publish state has the placeholder.

Verify:

```bash
rg -n '## \[0\.1\.0\]|Keep a Changelog|22 skills|v2\.1\.32' /Users/jp/Projects/active/claude-code-skills/CHANGELOG.md
```

Expected: hits for the v0.1.0 heading, format reference, and Requirements call-out. (`22 skills` is informational; if not literally present, that's fine — verify the per-category counts add to 22: 9+3+2+7+1=22.)

- [ ] **Step 6: Write `CONTRIBUTING.md`** (spec lines 195-217)

Voice matches README. Three short sections + maintenance-flow paragraph:

```markdown
# Contributing

## Issues

Issues welcome — bug reports, install problems, behavior questions, and feature suggestions. Open one freely; minimal template needed (what you tried, what happened, what you expected).

## Pull requests

Reviewed case-by-case. Small fixes (typos, doc clarifications, broken-link corrections, obvious bugs in skill instructions) are welcome and likely to merge fast. Larger changes — substantive skill rewrites, new skills, structural changes — please open an issue first to align on scope before opening the PR.

## Out of scope

This repo is a curated subset of a larger personal collection of Claude Code skills, many of which are still in-progress experiments. Only skills polished and validated for public use are published here. Requests to publish other skills are welcome as feature requests but treated as low-priority — the curation gap is intentional, not an oversight.

## Maintenance

This public repo is canonical for shipped fixes — bug reports get fixed here. Backports to private dev-staging are at maintainer discretion. Versioning is SHA-driven (no `version` field in `plugin.json`); every commit is a new release for plugin marketplace consumers, so install updates pull the latest published state automatically.
```

Verify:

```bash
rg -n 'canonical for shipped fixes|larger personal collection|SHA-driven' /Users/jp/Projects/active/claude-code-skills/CONTRIBUTING.md
```

Expected: all three phrases found.

- [ ] **Step 7: Write `.gitignore`** (spec line 552, expanded list)

```
# OS / editor noise
.DS_Store
*.swp
.idea/
.vscode/

# Defensive against post-publish drift — these patterns are excluded by the
# initial copy allowlist, but if skills are ever edited directly in this repo
# per the maintenance flow, eval/workspace dirs would otherwise accumulate.
evals/
*-workspace/
iteration-*/
*.local.md
```

Verify:

```bash
rg -n '\.DS_Store|evals/|\*-workspace/|iteration-\*|\*\.local\.md' /Users/jp/Projects/active/claude-code-skills/.gitignore
```

Expected: all five patterns found.

- [ ] **Step 8: Roll-up verify**

```bash
set -euo pipefail
cd /Users/jp/Projects/active/claude-code-skills
echo "Top-level files:"; ls -1 README.md LICENSE CHANGELOG.md CONTRIBUTING.md .gitignore
echo "Plugin manifests:"; ls -1 .claude-plugin/plugin.json .claude-plugin/marketplace.json
```

Expected: every listed file present, no `ls: cannot access`.

---

## Task 9: Step 7 — local clean-machine validation

**Goal:** Verify all 22 skills load via `claude --plugin-dir .` against an EMPTY `~/.claude/skills/` (so globally-promoted skills don't shadow plugin-namespaced versions).

**Files:** ephemeral — tarball backup at `~/claude-skills-backup-<timestamp>.tar.gz`, `mktemp -d` workspace.

**Recovery:** if anything in this task fails (kill -9, terminal close, trap doesn't fire), restore with `tar xzf "$BACKUP" -C ~/.claude`.

- [ ] **Step 1: Verify preconditions for the validation window**

Confirm out-of-band, by asking the user:
1. No other claude session is active (terminal, tmux, IDE, background).
2. No scheduled claude jobs (cron, launchd, hooks) will fire in the next ~5 minutes.
3. User understands: any concurrent claude during validation will see an empty `~/.claude/skills/` and may misbehave until the trap restores state.

If user says "wait, I have a tmux session running": halt. They handle that, then resume.

- [ ] **Step 2: Take tarball backup of `~/.claude/skills/`**

```bash
set -euo pipefail
BACKUP=~/claude-skills-backup-$(date +%Y%m%d-%H%M%S).tar.gz
tar czf "$BACKUP" -C ~/.claude skills
echo "Backup created: $BACKUP"
echo "Manual recovery (if trap fails): tar xzf \"$BACKUP\" -C ~/.claude"
```

Expected: tarball exists at the printed path. With `set -euo pipefail` active, a silent `tar` failure (disk full, permissions) aborts before the destructive `mv` in Step 4 — that's the whole point.

Verify:

```bash
ls -lh "$BACKUP"
tar tzf "$BACKUP" | head -5
```

Expected: file size > 0; `tar tzf` lists at least `skills/` and a few skill directories.

- [ ] **Step 3: Stage `mktemp -d` for the stash**

```bash
TMPSKILLS=$(mktemp -d)
echo "Stash dir: $TMPSKILLS"
```

Save this path; both the trap and the validation block reference `$TMPSKILLS`.

- [ ] **Step 4: Run validation in subshell with restoration trap**

The trap is **subshell-scoped** so the empty-skills window closes when the subshell exits, not when the user's interactive shell exits. (Spec Risk #5 — the v4 design had a full-shell trap that could leave `~/.claude/skills/` empty for the rest of the user's session.)

```bash
set -euo pipefail
cd /Users/jp/Projects/active/claude-code-skills

(
  trap '
    # Step 1: if live skills are still in place (outer mv never ran or was rolled back),
    # stash them so the restoration mv has somewhere to land.
    [ -d ~/.claude/skills ] && mv ~/.claude/skills "$TMPSKILLS/skills.test" 2>/dev/null || true

    # Step 2: restore from the stash. ONLY proceed if skills.bak exists; otherwise emit
    # an explicit recovery instruction so live skills are not silently lost.
    if [ -d "$TMPSKILLS/skills.bak" ]; then
      mv "$TMPSKILLS/skills.bak" ~/.claude/skills
      trash "$TMPSKILLS"
    else
      echo "TRAP: skills.bak missing — outer mv likely failed before validation." >&2
      echo "TRAP: live skills (if any) are at $TMPSKILLS/skills.test — DO NOT trash $TMPSKILLS." >&2
      echo "TRAP: recover via: tar xzf \"$BACKUP\" -C ~/.claude" >&2
    fi
  ' EXIT
  mv ~/.claude/skills "$TMPSKILLS/skills.bak"
  mkdir ~/.claude/skills

  # Validation runs here. Empty ~/.claude/skills/ means plugin-namespaced
  # skills aren't shadowed by globally-promoted ones (Trigger Eval Findings #1).
  claude --plugin-dir . --debug
)
# Subshell exited; trap fired; ~/.claude/skills is restored (or recovery instruction printed).
```

[USER GATE] Inside the `claude` session, verify:
1. All 22 skills register without errors. `--debug` will print skill loads to stderr — look for 22 lines mentioning `claude-code-skills:<name>` or similar.
2. Spot-check invocations: `/claude-code-skills:scrutinize`, `/claude-code-skills:adversarial-review`, and (if `claude --version` ≥ 2.1.32 AND `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`) `/claude-code-skills:claude-md`.
3. No permission prompts for plugin-private MCP tools (none should be present after sanitization).

Exit the claude session normally (Ctrl-D or `/quit`). The subshell exits; the trap fires; `~/.claude/skills/` is restored from `$TMPSKILLS/skills.bak`.

User reports: PASS or FAIL.

- [ ] **Step 5: Verify restoration succeeded**

```bash
ls ~/.claude/skills | wc -l
```

Expected: a number ≥ 1 (the user's normal globally-promoted skills are back).

If 0 or `No such file or directory`: trap didn't fire correctly. Run manual recovery NOW:

```bash
tar xzf "$BACKUP" -C ~/.claude
ls ~/.claude/skills | wc -l   # should now be ≥ 1
```

Then halt and investigate why the trap didn't fire before re-running.

- [ ] **Step 6: Branch on validation result**

**If PASS:** the artifact is verified. Decide on tarball:
- Trash it (validation passed, no need): `trash "$BACKUP"`
- Keep it (defense-in-depth, eats ~few MB): leave alone, manually trash after Task 10.

User chooses. Default: trash.

**If FAIL** (some skills didn't register, or invocation errors): halt.
- Inspect `claude --debug` output for which skills failed and why.
- Likely cause: a sanitize edit (Task 5) corrupted SKILL.md frontmatter, or `cp` missed a file in Task 4.
- Return to the failing skill's Task 5 substep, fix, re-run Tasks 6 and 7, then re-run Task 9 from Step 1.

---

## Task 10: Initial local commit

**Goal:** Capture the verified-ready state as a single "Initial release" commit on `main`. Halt the plan here. **No `git push`. No `gh repo create`. No tag.**

**Files:** all files in target repo staged and committed.

- [ ] **Step 1: Stage explicit paths**

The global CLAUDE.md prohibits `git add -A` and `git add .`. Even in a brand-new repo, stage by path:

```bash
set -euo pipefail
cd /Users/jp/Projects/active/claude-code-skills
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json
git add skills
git add README.md LICENSE CHANGELOG.md CONTRIBUTING.md .gitignore
```

(`git add skills` adds the directory recursively. The `.gitignore` written in Task 8 Step 7 protects against future drift; for the initial commit, the allowlist already excluded forbidden patterns.)

Verify:

```bash
git status -s
git diff --cached --stat | tail -1
```

Expected:
- `git status -s` shows `A` lines for every file in the repo, no `??` (untracked) lines.
- `git diff --cached --stat` final line shows ~25-30 files changed (depending on how many references/* and supplementary md files survive). Specifically: 2 manifests + 22+ SKILL.md + supporting refs + 5 root files.

If any `??` lines appear (untracked): halt, inspect, decide whether to add or trash.

- [ ] **Step 2: Commit**

```bash
git commit -m "Initial release: 22 curated Claude Code skills (v0.1.0)"
```

Expected output: `[main (root-commit) <sha>] Initial release: 22 curated Claude Code skills (v0.1.0)` followed by file-change stats.

- [ ] **Step 3: Verify state**

```bash
git log --oneline
git status
git branch --show-current
```

Expected:
- `git log --oneline` shows exactly one commit on `main`.
- `git status` shows `nothing to commit, working tree clean`.
- `git branch --show-current` prints `main`.

- [ ] **Step 4: HALT — plan complete**

The artifact at `/Users/jp/Projects/active/claude-code-skills/` is now ready-to-publish. Do **not** run any of the following — they belong to the deferred follow-up plan:

- ❌ `gh repo create jpsweeney97/claude-code-skills --public ...`
- ❌ `git remote add origin ...`
- ❌ `git push -u origin main`
- ❌ `git tag v0.1.0`
- ❌ `git push origin v0.1.0`
- ❌ `gh repo edit --add-topic ...`
- ❌ `/plugin marketplace add jpsweeney97/claude-code-skills` (against the public repo)
- ❌ Replacing the `2026-MM-DD` placeholder in CHANGELOG.md (do that at publish time so the date matches the commit/tag)

Report state to user: "Build phase complete. Verified-ready local artifact at `/Users/jp/Projects/active/claude-code-skills/` (commit `<sha>` on `main`). Publish phase deferred."

---

## Acceptance criteria (in-scope subset)

Mapped from spec lines 537-554. Items marked **deferred** belong to the follow-up plan, NOT this one.

- [ ] Preconditions verified (Task 1).
- [ ] Step 0 preflight passes — `marketplace.json source: "./"` accepts at runtime (Task 2).
- [ ] `set -euo pipefail` is the first directive of every multi-command bash block (Tasks 2-10).
- [ ] All 22 skills present in `skills/` with sanctioned content only — no `.DS_Store`, `evals/`, `*-workspace/`, `iteration-*/` (Task 4).
- [ ] 10 sanitization changes applied (Task 5); Step 5 lexical grep returns ONLY the two documented FPs (Task 7).
- [ ] Step 4b structural-reference scan — no dangling refs across categories (a)-(e) (Task 6).
- [ ] `plugin.json` has no `version` field; `marketplace.json` uses `source: "./"` (Task 8 Steps 1-2).
- [ ] Step 7 trap is subshell-scoped (Task 9 Step 4).
- [ ] `claude --plugin-dir . --debug` shows all 22 skills loading without errors (Task 9 Step 4).
- [ ] No `rm` or `rm -rf` in the implementation script — all deletions use `trash` or rely on the copy allowlist.
- [ ] README has all required sections (Task 8 Step 3).
- [ ] CHANGELOG.md exists at repo root with Keep-a-Changelog format and `## [0.1.0]` entry (Task 8 Step 5; date placeholder remains until publish).
- [ ] LICENSE is MIT, current year (2026), copyright "JP Sweeney" (Task 8 Step 4).
- [ ] CONTRIBUTING.md states the public-repo-canonical maintenance flow (Task 8 Step 6).
- [ ] `.gitignore` includes the seven patterns from spec line 552 (Task 8 Step 7).
- **Deferred:** `/plugin marketplace add` succeeds against the public repo, `/plugin install claude-code-skills@jpsweeney97-skills` completes, all 22 skills invokable as `/claude-code-skills:<name>` without permission prompts.
- **Deferred:** GitHub repo public, tagged `v0.1.0`, with five discoverability topics applied.
- **Deferred:** Post-publish success-criteria tracking for first month after release.

## Recovery quick reference

| Failure | Recovery |
|---|---|
| Task 2 preflight fails (`source: "./"` rejected) | Halt entire plan. Restructure spec for nested layout, then resume. |
| Task 4 missing skill in copy | Re-run loop for that skill; verify with `find skills/<name> -type f`. |
| Task 5 sanitize edit broke SKILL.md frontmatter | Re-copy from source (Task 4 step 2 for that one skill), re-apply edit. |
| Task 6 finds dangling ref | Add Task 5 substep, re-run Task 5 + 6. |
| Task 7 finds non-FP residue | Add Task 5 substep, re-run Task 5 + 7. |
| Task 9 trap didn't fire (`~/.claude/skills/` empty) | `tar xzf "$BACKUP" -C ~/.claude` — the snapshot from Task 9 Step 2 is the recovery artifact. |
| Task 9 trap fired but skills missing | Inspect `$TMPSKILLS/skills.bak` (still on disk if `trash "$TMPSKILLS"` didn't run); else use tarball. |
| Task 9 validation FAILs | Halt; re-enter Task 5/6/7 for the failing skill, then re-run Task 9. |
| Task 10 commit aborts (hook failure) | Investigate hook output; never use `--no-verify`. |

## Self-review notes

Cross-checked against spec acceptance criteria (lines 537-554). One non-obvious item to flag at execution time: **the CHANGELOG `2026-MM-DD` placeholder**. The plan explicitly leaves it un-replaced because the publish date isn't known until the follow-up plan runs `gh repo create` + `git tag`. Both the spec's Acceptance criteria and CHANGELOG section name this — the placeholder is intentional in this build phase.

Spec coverage check (per spec section):
- **Curated skill list** → Tasks 4 (copy 22) + 5 (sanitize 10).
- **File layout** → Task 4 + Task 8.
- **Manifest specifications** (`plugin.json`, `marketplace.json`) → Task 8 Steps 1-2; pre-validated in Task 2.
- **README structure** → Task 8 Step 3.
- **CONTRIBUTING.md content** → Task 8 Step 6.
- **CHANGELOG.md content** → Task 8 Step 5.
- **Implementation workflow** → Tasks 1 (preconditions) + 2 (Step 0) + 3 (Step 1) + 4 (Steps 2-3) + 5 (Step 4) + 6 (Step 4b) + 7 (Step 5) + 8 (Step 6) + 9 (Step 7) + 10 (Step 8).
- **Out of scope** → already excluded from this plan.
- **Risks & open questions** → mitigations baked into the relevant tasks (Risk #1 → Tasks 6+7; Risk #3 → Task 9's tarball; Risk #5 → Task 9's subshell trap; Risks #6-8 → README Requirements section in Task 8 Step 3).
- **Acceptance criteria** → mirrored above as in-scope subset.

No placeholders in the plan body except the deliberate CHANGELOG date.
