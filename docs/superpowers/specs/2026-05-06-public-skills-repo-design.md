# Public Claude Code Skills Repo — Design Spec

**Date:** 2026-05-06
**Author:** JP Sweeney (with Claude collaboration)
**Status:** Approved for implementation
**Target artifact:** `/Users/jp/Projects/active/claude-code-skills/` (new public GitHub repo)

## Problem

JP Sweeney maintains ~29 dev-staged Claude Code skills in `claude-code-tool-dev/extensions/skills/`, deployed to `~/.claude/skills/` via `scripts/promote`. He wants to share a curated subset publicly on GitHub as a portfolio-quality showcase that is also installable as a Claude Code plugin.

The new repo at `/Users/jp/Projects/active/claude-code-skills/` will be a fresh, parallel collection — independent of the dev monorepo, hand-picked once from current dev-staging, not synced ongoing.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Source-of-truth model | Parallel | Dev monorepo unchanged; hand-pick once. Lowest risk, accepted drift. |
| Distribution format | Hybrid showcase + installable plugin + marketplace | Browsable on GitHub, installable via `--plugin-dir` *and* one-line `/plugin install`. |
| Curation method | Audit-and-propose | External audit produced 19 PUBLISH + 3 light-sanitize = 22 skills. |
| Repo name | `claude-code-skills` | Descriptive, matches product name, SEO-precise. |
| License | MIT | Standard for Claude Code skill repos, frictionless adoption. |
| Voice | First-person, technical, direct | Matches user's existing SKILL.md voice. |
| Marketplace catalog included? | Yes | Enables one-line install for adopters at minimal cost (~10 lines JSON). |

## Curated skill list (22)

### PUBLISH as-is (19)

`adversarial-review`, `claude-md`, `design-review-team`, `exiting-worktrees`, `explore-repo`, `format-export`, `git-hygiene`, `handbook`, `implementation-review`, `llm-reference`, `merge-branch`, `prompt-generator`, `readme`, `review-code`, `review-plan`, `review-strategy`, `review-writing`, `scrutinize`, `system-design-review`

### Light sanitization (3)

| Skill | Change |
|-------|--------|
| `next-steps` | Drop hardcoded `/codex-collaboration:dialogue` slash command line. Replace with generic phrasing or remove. |
| `making-recommendations` | Remove "Codex Delta" subsection from `SKILL.md`; delete companion `references/codex-delta.md` from copy. |
| `writing-principles` | Genericize "Composability" section that names `claude-md-improver` and `creating-skills`. Either delete the section or rewrite as "any partner skills you may have." |

### Excluded from v1

| Skill | Reason | Future status |
|-------|--------|---------------|
| `cc-docs`, `claude-code-docs`, `openai-docs` | Hard MCP dependencies on locally-installed servers (`claude-code-docs`, `openaiDeveloperDocs`) | Possible secondary release alongside publishing the `claude-code-docs` MCP server |
| `evaluating-extension-adoption` | Hard-depends on `exploring-claude-repos` companion skill (not in this 29-set) and writes to `docs/decisions/` | Future v1.x if companion skill also published |
| `learn`, `promote` | Hardcoded paths to `docs/learnings/learnings.md` and `.claude/CLAUDE.md`; only useful as paired system with documented convention | Future v1.x as documented "learnings workflow" pair |
| `changelog` | Depends on handoff-archivist teammate that references project-specific archive convention | Future v1.x as carved-down 2-teammate variant (git+PRs only) |

## File layout

```
/Users/jp/Projects/active/claude-code-skills/
├── .claude-plugin/
│   ├── plugin.json           # Plugin manifest
│   └── marketplace.json      # Marketplace catalog (single-plugin self-reference)
├── skills/                   # 22 skill directories at plugin root
│   ├── adversarial-review/
│   │   └── SKILL.md
│   ├── claude-md/
│   │   ├── SKILL.md
│   │   └── references/...    # supporting files travel inside the skill dir
│   ├── design-review-team/
│   │   ├── SKILL.md
│   │   └── references/...
│   └── ... (22 directories total)
├── README.md                 # Catalog + install + brief usage
├── LICENSE                   # MIT
├── CHANGELOG.md              # 0.1.0 initial release entry
└── .gitignore                # Standard
```

Skills live at plugin root (not inside `.claude-plugin/` — common mistake per official docs). Each skill keeps its full directory including `references/` and any supporting files. Skills get auto-namespaced as `/claude-code-skills:<skill-name>` after install.

## Manifest specifications

### `plugin.json`

```json
{
  "$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json",
  "name": "claude-code-skills",
  "version": "0.1.0",
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

Email omitted for privacy; `url` points at GitHub profile for attribution. No `skills` field — defaults to `skills/`. `$schema` enables editor autocomplete.

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

The marketplace uses a self-referential `"./"` source: marketplace and plugin live in the same repo, both manifests in `.claude-plugin/`. This pattern keeps skills at the repo root for the best GitHub browsing experience.

**Verification gate (implementation):** validate that `"./"` source works as expected by Claude Code's marketplace loader. Test sequence:
1. Run `claude --plugin-dir .` from the repo root → verify all 22 skills register.
2. From a separate test session, run `/plugin marketplace add /Users/jp/Projects/active/claude-code-skills` (local file path), then `/plugin install claude-code-skills@jpsweeney97-skills` → verify install completes and skills are invokable.

**Fallback (if `"./"` rejected):** restructure to nested layout — move plugin contents into `plugins/claude-code-skills/`, update `marketplace.json` source to `"./plugins/claude-code-skills"`. Skills would then live at `plugins/claude-code-skills/skills/...` (one level deeper, slightly worse browsing UX, otherwise equivalent).

## README structure

Voice: first-person, technical, direct. Match SKILL.md authoring voice.

Sections:

1. **Title + one-paragraph hook** — what's this, who's it for. Mentions the focus areas (review, critique, grounded documentation).
2. **What's in here** — skill catalog grouped by category, each entry linking to its `SKILL.md`.
3. **Install** — two paths:
   - **Try it (session-scoped):** `git clone` + `claude --plugin-dir`
   - **Install permanently (marketplace):** `/plugin marketplace add jpsweeney97/claude-code-skills` then `/plugin install claude-code-skills@jpsweeney97-skills`
4. **Use a skill** — brief example showing namespaced invocation: `/claude-code-skills:scrutinize`, `/claude-code-skills:adversarial-review`, etc.
5. **License** — MIT with link to LICENSE.
6. **Author** — JP Sweeney, GitHub profile link.

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

# 3. Copy 22 skills (full directory contents)
for skill in adversarial-review claude-md design-review-team exiting-worktrees explore-repo \
             format-export git-hygiene handbook implementation-review llm-reference \
             making-recommendations merge-branch next-steps prompt-generator readme \
             review-code review-plan review-strategy review-writing scrutinize \
             system-design-review writing-principles; do
  cp -r /Users/jp/Projects/active/claude-code-tool-dev/extensions/skills/$skill skills/$skill
done

# 4. Sanitize the 3 light-sanitize skills (apply diffs from "Sanitization specifications")

# 5. Write plugin.json, marketplace.json, README.md, LICENSE, CHANGELOG.md, .gitignore

# 6. Run sanitization-residue grep across all 22 skills
rg -i 'codex-collaboration|claude-md-improver|creating-skills|/Users/jp|engram|T-2026' skills/

# 7. Local validation
claude --plugin-dir . --debug   # verify all 22 skills register

# 8. Initial commit
git add .
git commit -m "Initial release: 22 curated Claude Code skills (v0.1.0)"

# 9. GitHub repo + push
gh repo create jpsweeney97/claude-code-skills --public \
  --description "Curated Claude Code skills for review, critique, and grounded documentation" \
  --source=. --remote=origin --push

# 10. Tag + topics
git tag v0.1.0 && git push origin v0.1.0
gh repo edit --add-topic claude-code,skills,plugin,code-review,documentation

# 11. Marketplace install verification (separate test session)
# /plugin marketplace add jpsweeney97/claude-code-skills
# /plugin install claude-code-skills@jpsweeney97-skills
```

## Out of scope (v1.x or later)

- `changelog` skill (carved-down 2-teammate variant)
- `learn` + `promote` pair as documented learnings workflow
- MCP-dependent skills bundled with publishing the `claude-code-docs` MCP server (separate artifact, possibly own repo)
- Sync mechanism between dev-staging and public repo (parallel model accepts drift)
- Plugin themes, output styles, hooks, subagents, MCP servers
- Translations, localization

## Risks & open questions

1. **`marketplace.json` self-reference (`"./"`)** — Documented relative-path rules say sources must start with `./` and must not contain `../`. `"./"` satisfies that literally, but it's a self-referential pattern not explicitly demonstrated in the docs. **Mitigation:** Step 7 of implementation validates locally with `--plugin-dir`; Step 11 validates the marketplace install flow. Fallback layout documented above.

2. **Drift over time** — Parallel model means skills will diverge between dev monorepo and public repo. **Mitigation:** none for v1; accepted tradeoff. Revisit if/when divergence becomes problematic.

3. **Sanitization completeness** — Audit caught obvious internal references but subtle ones in supporting `references/*.md` files may slip through. **Mitigation:** Step 6 grep across all 22 skill directories for tokens (`codex-collaboration`, `claude-md-improver`, `creating-skills`, `~/.claude/`, `/Users/jp/`, `T-2026`, `engram`, etc.) before commit.

4. **Version pinning** — `plugin.json` sets `"version": "0.1.0"`. With `version` set, users only receive updates when the version is bumped. Without it, every commit becomes a new version. Pinning at 0.1.0 is correct for the initial release, but future maintenance requires remembering to bump on each release. **Mitigation:** add a maintenance note in CHANGELOG that says "bump `plugin.json` version + git tag on every release".

## Acceptance criteria

- All 22 skills present in `skills/` with full directory contents (`SKILL.md` + supporting files where applicable).
- 3 sanitization changes applied; sanitization-residue grep returns no internal-only artifact references in any of the 22 skills.
- `plugin.json` and `marketplace.json` present in `.claude-plugin/`.
- `claude --plugin-dir . --debug` shows all 22 skills loading with no errors.
- `/plugin marketplace add jpsweeney97/claude-code-skills` (or local-path equivalent) succeeds.
- `/plugin install claude-code-skills@jpsweeney97-skills` completes and all 22 skills are invokable as `/claude-code-skills:<name>`.
- README has install instructions for both paths, skill catalog with category groupings, and license link.
- LICENSE file is MIT with current year and JP Sweeney attribution.
- GitHub repo is public, tagged `v0.1.0`, with discoverability topics applied.
