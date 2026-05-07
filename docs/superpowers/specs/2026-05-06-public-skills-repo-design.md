# Public Claude Code Skills Repo — Design Spec

**Date:** 2026-05-06 (revised after scrutiny pass — see History)
**Author:** JP Sweeney (with Claude collaboration)
**Status:** Draft v3 — minor revisions per scrutiny v2, ready for re-review
**Target artifact:** `/Users/jp/Projects/active/claude-code-skills/` (new public GitHub repo)

## History

- **v1 (committed `30c68a8e`):** initial design based on agent-summary audit. Status was "Approved for implementation" prematurely.
- **v2 (committed `095e2c70`):** rewrote the curated skill breakdown after a direct-file-inspection re-audit. v1 reported 19 PUBLISH + 3 SANITIZE; v2 reported 13 PUBLISH + 9 SANITIZE. Added copy allowlist (replaced `cp -r`), expanded sanitization-residue grep token list, downgraded the `marketplace.json "./"` risk per docs verification, fixed `gh add-topic` syntax, replaced incorrect "session-scoped" framing, added clean-machine validation step, omitted `version` from `plugin.json`, defined public-repo-canonical maintenance flow, added README namespacing + contribution-policy notes.
- **v3 (this revision):** minor precision fixes after scrutiny v2. (1) Drops over-prescribed SANITIZE rows: `system-design-review:374` (already conditional, no remaining sanitization needed — moves to PUBLISH AS-IS) and the `docs/audits/` portion of `design-review-team:243` (already conditional — `design-review-team` stays SANITIZE for the `agent-teams.md:3` attribution fix only). New counts: **14 PUBLISH + 8 SANITIZE = 22**. (2) Fixes Composability section line range: spans `SKILL.md:140-end-of-file` (currently line 168), not `140-165`. (3) Bakes known false positives into Step 5 grep comment. (4) Strengthens Step 7 with tarball snapshot + concurrent-session prohibition. (5) Adds a `## CONTRIBUTING.md content` section with 3-bullet stance and generic curation-gap note (no dev-monorepo link, even though the dev monorepo is public). (6) Notes `~/.claude/teams/`, `~/.claude/tasks/`, `~/.claude/CLAUDE.md` are functional Claude Code paths, not internal-vocab. (7) Fixes `codex-delta.md` line count to 199 (was 191).

## Problem

JP Sweeney maintains ~29 dev-staged Claude Code skills in `claude-code-tool-dev/extensions/skills/`, deployed to `~/.claude/skills/` via `scripts/promote`. He wants to share a curated subset publicly on GitHub as a portfolio-quality showcase that is also installable as a Claude Code plugin.

The new repo at `/Users/jp/Projects/active/claude-code-skills/` will be a fresh, parallel collection — independent of the dev monorepo, hand-picked once from current dev-staging, not synced ongoing.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Source-of-truth model | Parallel | Dev monorepo unchanged; hand-pick once. Lowest risk, accepted drift. |
| Distribution format | Hybrid showcase + installable plugin + marketplace | Browsable on GitHub, installable via `--plugin-dir` *and* one-line `/plugin install`. |
| Curation method | Audit-and-propose, with direct-file-inspection re-audit | v1's agent-summary audit was unsound. v2 uses per-file walkthrough + strict vocab grep. |
| Repo name | `claude-code-skills` | Descriptive, matches product name, SEO-precise. |
| License | MIT | Standard for Claude Code skill repos, frictionless adoption. |
| Voice | First-person, technical, direct | Matches user's existing SKILL.md voice. |
| Marketplace catalog included? | Yes | Enables one-line install for adopters at minimal cost (~10 lines JSON). |
| Versioning strategy | Omit `version` from `plugin.json` | Per docs: SHA drives updates, every commit is a new version. Removes the "remember to bump" anti-mitigation. |
| Maintenance flow | Public repo is canonical for shipped fixes | Bug reports get fixed in the public repo. Dev monorepo's copy may diverge (acceptable). |
| Audience | Both portfolio reader AND plugin adopter, deliberately | README balances catalog (browsability) with first-class install instructions. |
| Vocabulary strictness | Strict | Sanitize ALL internal project vocab regardless of public clarity. Reduces forensic OSINT exposure. |

## Curated skill list (22, recategorized)

### PUBLISH AS-IS (14, after `.DS_Store` filtering)

`adversarial-review`, `claude-md`, `exiting-worktrees`*, `format-export`, `implementation-review`, `llm-reference`, `merge-branch`, `prompt-generator`, `review-code`, `review-plan`, `review-strategy`, `review-writing`, `scrutinize`, `system-design-review`

\* `exiting-worktrees` SKILL.md content is clean, but the directory contains 180 KB of internal eval/benchmark workspace (`evals/`, `exiting-worktrees-workspace/iteration-1/...`, 30+ files). Use copy allowlist (see Implementation workflow) to ship only `SKILL.md`.

### SANITIZE — content changes required (8)

| Skill | Specific changes | Severity |
|-------|------------------|----------|
| `git-hygiene` | `SKILL.md:47` and `SKILL.md:330`: replace `codex/cleanup/YYYY-MM-DD-HHMMSS` branch convention with `cleanup/YYYY-MM-DD-HHMMSS` (drop the `codex/` prefix). | High |
| `next-steps` | `SKILL.md:26`: rephrase "Output feeds into Codex dialogue or focused planning sessions" — drop the Codex reference, keep the comparison ("Output feeds into deeper planning sessions"). `SKILL.md:157`: drop the literal `/codex-collaboration:dialogue` slash command line; replace with generic "If you have a follow-up advisor skill, dispatch it here." | Medium |
| `making-recommendations` | `SKILL.md:137-143`: remove the entire "Codex Delta" subsection. `references/codex-delta.md` (199 lines, 31 case-insensitive `codex` hits): delete the file. Verify the surrounding I8-I9 phase text doesn't dangle a reference to the removed section. | High — structural |
| `writing-principles` | `SKILL.md` "Composability" section: remove. The section starts at line 140 (`## Composability`) and runs to end of file (line 168 in current state — Composability is the last `##` section). Lines 148, 149, 157, 163, 165 reference `creating-skills` and/or `claude-md-improver`. **Removal check:** verify the deletion ends at end-of-file or before the next `##` heading; the `## Failure Mode Index` section above it ends cleanly at line 138. | Medium |
| `design-review-team` | `references/agent-teams.md:3`: remove the "Adapted from `packages/plugins/superspec/...`" attribution line. (`SKILL.md:243` `docs/audits/` reference is already in conditional form — `If the user asks to save or docs/audits/ exists` — no change needed; v2 over-prescribed this row.) | Low |
| `explore-repo` | `references/agent-teams.md:3`: remove the same `packages/plugins/superspec/...` attribution line. | Low |
| `handbook` | `references/agent-teams.md:3`: remove the same `packages/plugins/superspec/...` attribution line. | Low |
| `readme` | `references/agent-teams.md:3`: remove the same `packages/plugins/superspec/...` attribution line. | Low |

### Excluded from v1

| Skill | Reason | Future status |
|-------|--------|---------------|
| `cc-docs`, `claude-code-docs`, `openai-docs` | Hard MCP dependencies on locally-installed servers | Possible secondary release alongside publishing the `claude-code-docs` MCP server |
| `evaluating-extension-adoption` | Hard-depends on `exploring-claude-repos` companion skill (not in this 29-set) and writes to `docs/decisions/` | Future v1.x if companion skill also published |
| `learn`, `promote` | Hardcoded paths to `docs/learnings/learnings.md` and `.claude/CLAUDE.md`; only useful as paired system with documented convention | Future v1.x as documented "learnings workflow" pair |
| `changelog` | Depends on handoff-archivist teammate that references project-specific archive convention | Future v1.x as carved-down 2-teammate variant (git+PRs only) |

## File layout

```
/Users/jp/Projects/active/claude-code-skills/
├── .claude-plugin/
│   ├── plugin.json           # Plugin manifest (no `version` field)
│   └── marketplace.json      # Marketplace catalog (single-plugin self-reference)
├── skills/                   # 22 skill directories at plugin root
│   ├── adversarial-review/
│   │   └── SKILL.md
│   ├── claude-md/
│   │   ├── SKILL.md
│   │   └── references/...    # supporting files travel inside the skill dir
│   ├── design-review-team/
│   │   ├── SKILL.md
│   │   └── references/...    # agent-teams.md sanitized; superspec attribution removed
│   ├── writing-principles/
│   │   ├── SKILL.md
│   │   └── writing-principles.md  # 71 KB supplementary content (legitimate, ships)
│   └── ... (22 directories total)
├── README.md                 # Catalog + install + brief usage + namespacing note + contribution policy
├── LICENSE                   # MIT, copyright "JP Sweeney"
├── CHANGELOG.md              # 0.1.0 initial release entry
├── CONTRIBUTING.md           # 3-bullet stance (issues, PRs, out-of-scope) + curation-gap note + maintenance flow. See "CONTRIBUTING.md content" section.
└── .gitignore                # Includes .DS_Store at minimum
```

Skills live at plugin root (not inside `.claude-plugin/` — common mistake per official docs). Each skill keeps its sanctioned content (SKILL.md, references/, examples/, top-level *.md siblings); internal artifacts (`evals/`, `*-workspace/`, `iteration-*/`, `.DS_Store`) are filtered. Skills get auto-namespaced as `/claude-code-skills:<skill-name>` after install.

## Manifest specifications

### `plugin.json`

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

`version` field deliberately omitted — per Claude Code docs, the git commit SHA drives version resolution and every commit counts as a new release. This eliminates the "remember to bump on every release" failure mode. Email omitted for privacy; `url` points at GitHub profile for attribution. No `skills` field — defaults to `skills/`. `$schema` enables editor autocomplete.

### `marketplace.json`

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

The marketplace uses a self-referential `"./"` source: marketplace and plugin live in the same repo, both manifests in `.claude-plugin/`, skills at repo root. Per the official `plugin-marketplaces#plugin-sources` docs: relative path sources "must start with `./`" and are "resolved relative to the marketplace root, not the `.claude-plugin/` directory." `"./"` literally satisfies this rule. (v1 of this spec over-rated this risk; v2 downgrades it.)

**Validation step (still required):** confirm with `claude --plugin-dir .` that all 22 skills register, and confirm with `/plugin marketplace add` + `/plugin install` flow that the install completes. If the loader rejects `"./"` for any reason, fall back to the nested layout (move plugin contents into `plugins/claude-code-skills/`, update `marketplace.json` source to `"./plugins/claude-code-skills"`).

## README structure

Voice: first-person, technical, direct. Match SKILL.md authoring voice. Audience: portfolio reader AND plugin adopter, balanced.

Sections:

1. **Title + one-paragraph hook** — what this is, who it's for. Mentions the focus areas (review, critique, grounded documentation) and that everything is also installable.
2. **Namespacing note** (one line, prominent) — "All skills are invoked as `/claude-code-skills:<name>` — e.g., `/claude-code-skills:scrutinize`." Pre-empts the most common first-use confusion.
3. **What's in here** — skill catalog grouped by category, each entry one-liner-linked to its `SKILL.md`.
4. **Install** — two paths:
   - **Try it (clone + dev flag):** `git clone` + `claude --plugin-dir`. (NB: this clones the repo to disk; only the *plugin load* is session-scoped, not the clone.)
   - **Install permanently (marketplace):** `/plugin marketplace add jpsweeney97/claude-code-skills` then `/plugin install claude-code-skills@jpsweeney97-skills`.
5. **Use a skill** — brief example showing namespaced invocation.
6. **Contributing** — short policy: issues welcome (bug reports, feature requests). PRs reviewed case-by-case. Public repo is canonical for shipped fixes. Link to CONTRIBUTING.md for details.
7. **License** — MIT with link to LICENSE.
8. **Author** — JP Sweeney, GitHub profile link.

### Skill catalog grouping

| Category | Skills |
|----------|--------|
| Review & adversarial critique | `adversarial-review`, `scrutinize`, `implementation-review`, `system-design-review`, `design-review-team`, `review-code`, `review-plan`, `review-strategy`, `review-writing` |
| Grounded documentation generation | `readme`, `handbook`, `claude-md` |
| Repo exploration & analysis | `explore-repo`, `llm-reference` |
| Workflow | `git-hygiene`, `merge-branch`, `exiting-worktrees`, `next-steps`, `making-recommendations`, `prompt-generator`, `format-export` |
| Authoring | `writing-principles` |

## CONTRIBUTING.md content

Voice matches README: first-person, technical, direct. Three short sections plus a maintenance-flow paragraph.

### Issues

> Issues welcome — bug reports, install problems, behavior questions, and feature suggestions. Open one freely; minimal template needed (what you tried, what happened, what you expected).

### Pull requests

> Reviewed case-by-case. Small fixes (typos, doc clarifications, broken-link corrections, obvious bugs in skill instructions) are welcome and likely to merge fast. Larger changes — substantive skill rewrites, new skills, structural changes — please open an issue first to align on scope before opening the PR.

### Out of scope

> This repo is a curated subset of a larger personal collection of Claude Code skills, many of which are still in-progress experiments. Only skills polished and validated for public use are published here. Requests to publish other skills are welcome as feature requests but treated as low-priority — the curation gap is intentional, not an oversight.

### Maintenance flow

> This public repo is canonical for shipped fixes — bug reports get fixed here. Backports to private dev-staging are at maintainer discretion. Versioning is SHA-driven (no `version` field in `plugin.json`); every commit is a new release for plugin marketplace consumers, so install updates pull the latest published state automatically.

**Decisions encoded in this content:**

- **No link to the dev monorepo.** Even though `claude-code-tool-dev` is public on GitHub, linking it from CONTRIBUTING.md would expose readers to internal-vocab churn (codex, engram, superspec, cross-model, etc.) that the strict-vocab decision deliberately excludes from this repo. The "larger personal collection" wording sets expectations without exposing the monorepo's surface area.
- **No code of conduct file.** Standard professional conduct is implicit; adding `CODE_OF_CONDUCT.md` adds maintenance overhead disproportionate to a skills-only repo. Reconsider if community grows.
- **No security disclosure policy.** Skills are instructional documents, not executable code with attack surface. If a skill instruction has a security implication (e.g., a destructive command), it's a normal bug report.

## Implementation workflow

```bash
# 1. Create + init
mkdir /Users/jp/Projects/active/claude-code-skills
cd /Users/jp/Projects/active/claude-code-skills
git init -b main

# 2. Build structure
mkdir -p .claude-plugin skills

# 3. Copy 22 skills using ALLOWLIST (NOT `cp -r`).
# For each skill, ship: SKILL.md (always), references/* (if present), examples/* (if present),
# top-level *.md siblings (e.g., writing-principles/writing-principles.md).
# DENY anything matching: .DS_Store, evals/, *-workspace/, iteration-*/.
SRC=/Users/jp/Projects/active/claude-code-tool-dev/extensions/skills
for skill in adversarial-review claude-md design-review-team exiting-worktrees explore-repo \
             format-export git-hygiene handbook implementation-review llm-reference \
             making-recommendations merge-branch next-steps prompt-generator readme \
             review-code review-plan review-strategy review-writing scrutinize \
             system-design-review writing-principles; do
  mkdir -p "skills/$skill"
  # Always ship SKILL.md
  cp "$SRC/$skill/SKILL.md" "skills/$skill/SKILL.md"
  # Conditionally ship references/, examples/, and top-level supplementary *.md
  for sub in references examples; do
    if [ -d "$SRC/$skill/$sub" ]; then
      cp -r "$SRC/$skill/$sub" "skills/$skill/$sub"
    fi
  done
  # Top-level *.md siblings (covers writing-principles/writing-principles.md)
  find "$SRC/$skill" -maxdepth 1 -name '*.md' ! -name 'SKILL.md' -exec cp {} "skills/$skill/" \;
done
# Belt-and-braces denylist sweep — remove anything that slipped through
find skills -name '.DS_Store' -delete
find skills -type d \( -name 'evals' -o -name 'iteration-*' -o -name '*-workspace' \) -exec rm -rf {} +

# 4. Sanitize the 8 SANITIZE skills (apply diffs from "Curated skill list / SANITIZE" table)
#    - git-hygiene: replace `codex/cleanup/` with `cleanup/` (2 lines)
#    - next-steps: rephrase 2 lines (drop "Codex" + slash command)
#    - making-recommendations: remove section + delete references/codex-delta.md
#    - writing-principles: remove Composability section (lines 140-end-of-file in SKILL.md)
#    - design-review-team, explore-repo, handbook, readme: remove "Adapted from packages/plugins/superspec/..." line in references/agent-teams.md

# 5. Run sanitization-residue grep across all 22 skills (expanded token list)
rg -i -n 'codex|cross-model|engram|superpowers|superspec|page[ -]?turner|claude-code-tool-dev|jpsweeney97|sweeney|handoff-archivist|claude-md-improver|creating-skills|cc-docs|openai-docs|claude-code-docs|evaluating-extension-adoption|exploring-claude-repos|delegate|delegation|dialogue|extensions/skills|scripts/promote|docs/learnings|docs/handoffs|docs/tickets|claude_ai_|/Users/jp|T-20[0-9]{6}|packages/plugins' skills/
# Known false positives (common-English usage, NOT internal-vocab — leave them):
#   - skills/writing-principles/writing-principles.md:54   ("Scoped instructions for delegated tasks")
#   - skills/writing-principles/writing-principles.md:1025 ("Dynamic dialogue has different constraints")
# Expected output: ONLY the two known false positives above. Any other hit is real residue — sanitize before continuing.

# 6. Write plugin.json, marketplace.json, README.md, LICENSE, CHANGELOG.md, CONTRIBUTING.md, .gitignore
#    LICENSE: MIT template, copyright "JP Sweeney", current year (2026)
#    .gitignore: at minimum, .DS_Store, *.swp, .idea/, .vscode/

# 7. Local validation — clean-machine version
#    Globally-promoted skills in ~/.claude/skills/ shadow the plugin-namespaced versions
#    (per "Trigger Eval Findings #1: globally-promoted skill collision"). To get a true clean
#    validation, temporarily move ~/.claude/skills/ aside.
#
#    PRECONDITIONS — verify ALL of these before running:
#    - No other claude session is active (in any terminal, tmux pane, IDE, or background process).
#    - No scheduled claude jobs (cron, launchd, systemd timer, hooks) will fire during the validation window.
#    - You understand: any concurrent claude invocation during validation will see an empty ~/.claude/skills/
#      and may behave incorrectly until the trap restores state.
#
#    Take a tarball snapshot FIRST — recovery is one command if anything fails (kill -9, system crash,
#    terminal closed without Ctrl-D, accidental shell exit). The trap is a happy-path mechanism only.
BACKUP=~/claude-skills-backup-$(date +%Y%m%d-%H%M%S).tar.gz
tar czf "$BACKUP" -C ~/.claude skills
echo "Backup created: $BACKUP"
echo "Manual recovery (if trap fails): tar xzf \"$BACKUP\" -C ~/.claude"

TMPSKILLS=$(mktemp -d)
mv ~/.claude/skills "$TMPSKILLS/skills.bak"
mkdir ~/.claude/skills
trap "rm -rf ~/.claude/skills && mv \"$TMPSKILLS/skills.bak\" ~/.claude/skills && rmdir \"$TMPSKILLS\"" EXIT

# Now run validation:
claude --plugin-dir . --debug   # verify all 22 skills register on a clean ~/.claude/skills/
# Test a few invocations: /claude-code-skills:scrutinize, /claude-code-skills:adversarial-review
# Restore happens via trap on shell exit; tarball is the fallback if trap doesn't fire.

# 8. Initial commit
git add .
git commit -m "Initial release: 22 curated Claude Code skills (v0.1.0)"

# 9. GitHub repo + push
gh repo create jpsweeney97/claude-code-skills --public \
  --description "Curated Claude Code skills for review, critique, and grounded documentation" \
  --source=. --remote=origin --push

# 10. Tag + topics (note: --add-topic takes one topic per invocation, NOT comma-separated)
git tag v0.1.0 && git push origin v0.1.0
gh repo edit --add-topic claude-code
gh repo edit --add-topic claude-code-skills
gh repo edit --add-topic plugin
gh repo edit --add-topic code-review
gh repo edit --add-topic documentation

# 11. Marketplace install verification (separate test session, also clean ~/.claude/skills/)
# /plugin marketplace add jpsweeney97/claude-code-skills
# /plugin install claude-code-skills@jpsweeney97-skills
# Verify: /claude-code-skills:scrutinize and 21 other skills are invokable; no permission prompts for plugin-private MCP tools.
```

## Out of scope (v1.x or later)

- `changelog` skill (carved-down 2-teammate variant)
- `learn` + `promote` pair as documented learnings workflow
- MCP-dependent skills bundled with publishing the `claude-code-docs` MCP server (separate artifact, possibly own repo)
- Sync mechanism between dev-staging and public repo (parallel model accepts drift)
- Plugin themes, output styles, hooks, subagents, MCP servers
- Translations, localization

## Risks & open questions

1. **Audit completeness (v2 mitigation)** — v1's audit was unsound on 4 of 22 skills. v2 re-audited via direct file inspection + strict vocab grep covering 18+ token categories. The Step-5 grep in the workflow is the same pattern that v2 used for the audit, so any new residue introduced during sanitization will be caught. Residual risk: terms outside the strict vocab list that still leak personal context (e.g. specific person names, company references, internal slang the user hasn't flagged). Acceptance: residual risk treated as below threshold; future findings handled as bug reports against the public repo.

2. **Drift over time** — Parallel model means skills will diverge between dev monorepo and public repo. Maintenance flow: public repo is canonical for shipped fixes (per decision). When the user wants to ship dev improvements to public, it's a deliberate copy-and-sanitize step, not automatic.

3. **Globally-promoted skill collision in local validation** — Per `Trigger Eval Findings #1`, `~/.claude/skills/` already containing all 22 skills means local plugin-namespaced validation is contaminated. Step 7 of the workflow stashes `~/.claude/skills/` to a tmp dir during validation and restores via `trap`. Trap-failure modes (`kill -9`, crash, terminal-close) and concurrent-session exposure are addressed under Risk #5 — Step 7 takes a tarball snapshot before the move, making recovery a one-command `tar xzf` even if the trap fails. Acceptance: documented preconditions + tarball snapshot reduce residual risk to the validation window itself.

4. **Plugin-private MCP tools referenced in supporting `references/*.md`** — `making-recommendations/references/codex-delta.md` references `mcp__plugin_codex-collaboration_*` tools inline. Sanitization step deletes this entire file, removing the issue. Verification: Step 5 grep includes `codex` token, will catch any straggler references.

5. **Stash/restore race condition during validation** — During the Step 7 validation window, ANY concurrent claude invocation (other terminal, tmux pane, IDE, scheduled cron/launchd job, hook, accidental new shell) sees an empty `~/.claude/skills/` until the trap restores it. The trap doesn't fire on `kill -9`, system crash, or "terminal closed without Ctrl-D" in some terminal emulators. Mitigation: Step 7 documents preconditions explicitly AND takes a tarball snapshot before the move, so recovery is one command (`tar xzf "$BACKUP" -C ~/.claude`) even when the trap fails to fire. Acceptance: residual exposure is the validation-window itself; if a precondition-violating session fires anyway, it gets a contaminated read for the duration.

6. **Functional Claude Code path references in shipped skills (not contamination)** — Five skills (`design-review-team`, `explore-repo`, `handbook`, `readme`, `claude-md`) reference `~/.claude/teams/`, `~/.claude/tasks/`, or `~/.claude/CLAUDE.md`. These are functional Claude Code paths — where the harness expects to find teams state, tasks state, and project memory — not internal-project vocabulary. They ship as-is. The Step 5 grep token list deliberately excludes `~/.claude` because it's universal Claude Code surface area, not personal context.

## Acceptance criteria

- All 22 skills present in `skills/` with sanctioned content only (no `.DS_Store`, no `evals/`, no `*-workspace/`, no `iteration-*/`).
- 8 sanitization changes applied per the SANITIZE table; running the Step-5 grep returns ONLY the two documented false positives (`writing-principles.md:54`, `:1025`).
- `plugin.json` has no `version` field. `marketplace.json` uses `source: "./"`.
- `claude --plugin-dir . --debug` (with `~/.claude/skills/` masked per Step 7) shows all 22 skills loading without errors.
- `/plugin marketplace add` (local-path or `gh:`) succeeds; `/plugin install claude-code-skills@jpsweeney97-skills` completes; all 22 skills invokable as `/claude-code-skills:<name>` without plugin-private-MCP permission prompts.
- README has: namespacing note, install instructions for both paths, skill catalog with category groupings, contributing policy, license link.
- LICENSE file is MIT with current year (2026) and copyright "JP Sweeney".
- CONTRIBUTING.md states the public-repo-canonical maintenance flow.
- `.gitignore` includes `.DS_Store` at minimum.
- GitHub repo is public, tagged `v0.1.0`, with five discoverability topics applied (one per `--add-topic` invocation).
