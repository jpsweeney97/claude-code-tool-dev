# Public Claude Code Skills Repo — Design Spec

**Date:** 2026-05-06 (revised after scrutiny pass — see History)
**Author:** JP Sweeney (with Claude collaboration)
**Status:** Draft v2 — re-audit complete, ready for re-review
**Target artifact:** `/Users/jp/Projects/active/claude-code-skills/` (new public GitHub repo)

## History

- **v1 (committed `30c68a8e`):** initial design based on agent-summary audit. Status was "Approved for implementation" prematurely.
- **v2 (this revision):** rewrites the curated skill breakdown after a direct-file-inspection re-audit. v1 reported 19 PUBLISH + 3 SANITIZE; reality is 13 PUBLISH + 9 SANITIZE. Adds copy allowlist (replaces `cp -r`), expands sanitization-residue grep token list, downgrades the `marketplace.json "./"` risk per docs verification, fixes `gh add-topic` syntax, replaces incorrect "session-scoped" framing, adds clean-machine validation step, omits `version` from `plugin.json`, defines public-repo-canonical maintenance flow, and adds README namespacing + contribution-policy notes.

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

### PUBLISH AS-IS (13, after `.DS_Store` filtering)

`adversarial-review`, `claude-md`, `exiting-worktrees`*, `format-export`, `implementation-review`, `llm-reference`, `merge-branch`, `prompt-generator`, `review-code`, `review-plan`, `review-strategy`, `review-writing`, `scrutinize`

\* `exiting-worktrees` SKILL.md content is clean, but the directory contains 180 KB of internal eval/benchmark workspace (`evals/`, `exiting-worktrees-workspace/iteration-1/...`, 30+ files). Use copy allowlist (see Implementation workflow) to ship only `SKILL.md`.

### SANITIZE — content changes required (9)

| Skill | Specific changes | Severity |
|-------|------------------|----------|
| `git-hygiene` | `SKILL.md:47` and `SKILL.md:330`: replace `codex/cleanup/YYYY-MM-DD-HHMMSS` branch convention with `cleanup/YYYY-MM-DD-HHMMSS` (drop the `codex/` prefix). | High |
| `next-steps` | `SKILL.md:26`: rephrase "Output feeds into Codex dialogue or focused planning sessions" — drop the Codex reference, keep the comparison ("Output feeds into deeper planning sessions"). `SKILL.md:157`: drop the literal `/codex-collaboration:dialogue` slash command line; replace with generic "If you have a follow-up advisor skill, dispatch it here." | Medium |
| `making-recommendations` | `SKILL.md:137-143`: remove the entire "Codex Delta" subsection. `references/codex-delta.md` (191 lines, 35+ codex hits): delete the file. Verify the surrounding I8-I9 phase text doesn't dangle a reference to the removed section. | High — structural |
| `writing-principles` | `SKILL.md:140-165` "Composability" section: remove or rewrite. Specific lines: 148, 149, 157, 163, 165 all name `creating-skills` and/or `claude-md-improver`. Cleanest fix: remove the entire Composability section (the principles below it stand alone). | Medium |
| `design-review-team` | `SKILL.md:243`: rewrite `docs/audits/` references as conditional ("if a `docs/audits/` directory exists in your workspace") or generic ("a reviews/audit directory you maintain"). `references/agent-teams.md:3`: remove the "Adapted from `packages/plugins/superspec/...`" attribution line. | Medium |
| `explore-repo` | `references/agent-teams.md:3`: remove the same `packages/plugins/superspec/...` attribution line. | Low |
| `handbook` | `references/agent-teams.md:3`: remove the same `packages/plugins/superspec/...` attribution line. | Low |
| `readme` | `references/agent-teams.md:3`: remove the same `packages/plugins/superspec/...` attribution line. | Low |
| `system-design-review` | `SKILL.md:374`: rewrite `docs/audits/` reference as conditional or generic. | Low |

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
├── CONTRIBUTING.md           # short stance: issues welcome, PRs case-by-case (matches "public canonical" decision)
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

# 4. Sanitize the 9 SANITIZE skills (apply diffs from "Curated skill list / SANITIZE" table)
#    - git-hygiene: replace `codex/cleanup/` with `cleanup/` (2 lines)
#    - next-steps: rephrase 2 lines (drop "Codex" + slash command)
#    - making-recommendations: remove section + delete references/codex-delta.md
#    - writing-principles: remove Composability section (~25 lines)
#    - design-review-team, explore-repo, handbook, readme: remove "Adapted from packages/plugins/superspec/..." line in references/agent-teams.md
#    - system-design-review: rewrite docs/audits/ reference

# 5. Run sanitization-residue grep across all 22 skills (expanded token list)
rg -i -n 'codex|cross-model|engram|superpowers|superspec|page[ -]?turner|claude-code-tool-dev|jpsweeney97|sweeney|handoff-archivist|claude-md-improver|creating-skills|cc-docs|openai-docs|claude-code-docs|evaluating-extension-adoption|exploring-claude-repos|delegate|delegation|dialogue|extensions/skills|scripts/promote|docs/learnings|docs/handoffs|docs/tickets|claude_ai_|/Users/jp|T-20[0-9]{6}|packages/plugins' skills/
# Expected output: empty (or only false positives that are clearly not internal-vocab leaks).
# If any hit is a real residue, sanitize before continuing.

# 6. Write plugin.json, marketplace.json, README.md, LICENSE, CHANGELOG.md, CONTRIBUTING.md, .gitignore
#    LICENSE: MIT template, copyright "JP Sweeney", current year (2026)
#    .gitignore: at minimum, .DS_Store, *.swp, .idea/, .vscode/

# 7. Local validation — clean-machine version
#    Globally-promoted skills in ~/.claude/skills/ shadow the plugin-namespaced versions
#    (per "Trigger Eval Findings #1: globally-promoted skill collision"). To get a true clean
#    validation, temporarily move ~/.claude/skills/ aside:
TMPSKILLS=$(mktemp -d)
mv ~/.claude/skills "$TMPSKILLS/skills.bak"
mkdir ~/.claude/skills
trap "rm -rf ~/.claude/skills && mv \"$TMPSKILLS/skills.bak\" ~/.claude/skills && rmdir \"$TMPSKILLS\"" EXIT
# Now run validation:
claude --plugin-dir . --debug   # verify all 22 skills register on a clean ~/.claude/skills/
# Test a few invocations: /claude-code-skills:scrutinize, /claude-code-skills:adversarial-review
# Restore happens via trap on shell exit

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

3. **Globally-promoted skill collision in local validation** — Per `Trigger Eval Findings #1`, `~/.claude/skills/` already containing all 22 skills means local plugin-namespaced validation is contaminated. Step 7 of the workflow stashes `~/.claude/skills/` to a tmp dir during validation and restores via `trap`. Risk: trap doesn't fire on `kill -9` or system crash; user would need to manually restore. Acceptance: rare failure mode, user can re-run from tmp dir.

4. **Plugin-private MCP tools referenced in supporting `references/*.md`** — `making-recommendations/references/codex-delta.md` references `mcp__plugin_codex-collaboration_*` tools inline. Sanitization step deletes this entire file, removing the issue. Verification: Step 5 grep includes `codex` token, will catch any straggler references.

5. **Stash/restore race condition during validation** — If the user's `claude` session is already running, `mv ~/.claude/skills` could affect the running session. Mitigation: run Step 7 in a fresh terminal, not in an active Claude Code session. Document this constraint.

## Acceptance criteria

- All 22 skills present in `skills/` with sanctioned content only (no `.DS_Store`, no `evals/`, no `*-workspace/`, no `iteration-*/`).
- 9 sanitization changes applied per the SANITIZE table; running the Step-5 grep returns no internal-vocab residue.
- `plugin.json` has no `version` field. `marketplace.json` uses `source: "./"`.
- `claude --plugin-dir . --debug` (with `~/.claude/skills/` masked per Step 7) shows all 22 skills loading without errors.
- `/plugin marketplace add` (local-path or `gh:`) succeeds; `/plugin install claude-code-skills@jpsweeney97-skills` completes; all 22 skills invokable as `/claude-code-skills:<name>` without plugin-private-MCP permission prompts.
- README has: namespacing note, install instructions for both paths, skill catalog with category groupings, contributing policy, license link.
- LICENSE file is MIT with current year (2026) and copyright "JP Sweeney".
- CONTRIBUTING.md states the public-repo-canonical maintenance flow.
- `.gitignore` includes `.DS_Store` at minimum.
- GitHub repo is public, tagged `v0.1.0`, with five discoverability topics applied (one per `--add-topic` invocation).
