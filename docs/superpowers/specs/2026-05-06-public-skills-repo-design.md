# Public Claude Code Skills Repo — Design Spec

**Date:** 2026-05-06 (revised after scrutiny pass — see History)
**Author:** JP Sweeney (with Claude collaboration)
**Status:** Draft v6 — minor revision after pre-execution audit-miss finding (personal-tool prescription class), ready for re-review
**Target artifact:** `/Users/jp/Projects/active/claude-code-skills/` (new public GitHub repo)

## History

- **v1 (committed `30c68a8e`):** initial design based on agent-summary audit. Status was "Approved for implementation" prematurely.
- **v2 (committed `095e2c70`):** rewrote the curated skill breakdown after a direct-file-inspection re-audit. v1 reported 19 PUBLISH + 3 SANITIZE; v2 reported 13 PUBLISH + 9 SANITIZE. Added copy allowlist (replaced `cp -r`), expanded sanitization-residue grep token list, downgraded the `marketplace.json "./"` risk per docs verification, fixed `gh add-topic` syntax, replaced incorrect "session-scoped" framing, added clean-machine validation step, omitted `version` from `plugin.json`, defined public-repo-canonical maintenance flow, added README namespacing + contribution-policy notes.
- **v3 (committed `66b19a5b`):** minor precision fixes after scrutiny v2. (1) Drops over-prescribed SANITIZE rows: `system-design-review:374` (already conditional — moves to PUBLISH AS-IS) and the `docs/audits/` portion of `design-review-team:243` (already conditional). New counts: **14 PUBLISH + 8 SANITIZE = 22**. (2) Fixes Composability section line range: `SKILL.md:140-end-of-file`. (3) Bakes known false positives into Step 5 grep comment. (4) Strengthens Step 7 with tarball snapshot + concurrent-session prohibition. (5) Adds `## CONTRIBUTING.md content` section. (6) Notes `~/.claude/teams/`, `~/.claude/tasks/`, `~/.claude/CLAUDE.md` are functional Claude Code paths. (7) Fixes `codex-delta.md` line count to 199.
- **v4 (committed `7cd09882`):** major revision per scrutiny v3, which identified the **structural-vs-lexical pattern**: lexical residue grep (Step 5) catches internal-vocab leakage, but a separate failure class — **dangling structural references** (slash commands, named skills, environmental flag dependencies, sibling-skill cross-references) — is invisible to lexical scanning. v4 introduced Step 4b (structural scan), Step 0 (preflight `marketplace.json` validation), README Requirements section, the `trash`-based deletion rule, and moved `claude-md` from PUBLISH AS-IS to SANITIZE.
- **v5 (committed `9ab5a4ad`):** minor revision per scrutiny v4. Scrutiny v4 confirmed the structural-vs-lexical framing was correct but found three concrete misses inside it: (a) Step 4b's slash-command regex `/[a-z]…\b` was so broad (~265 hits across 22 skills) it functioned as noise rather than a gate; (b) Step 4b's category enumeration didn't include **bare-name workflow references** or **named protocols/procedures** (e.g., `merge-branch:17` "the commit-push-pr workflow", `next-steps:21,28` "Next Steps protocol"), so two skills shipped with dangling refs the scan should have caught; (c) the README Requirements section documented the env flag but missed the **Claude Code v2.1.32+** version floor that Anthropic's official docs name. Plus several independent defects: (d) Step 7's `tar` backup had no exit-on-failure check, so a silent backup failure cascaded into destroying live `~/.claude/skills/`; (e) Step 7's trap fired on full shell EXIT, exposing the user's entire shell session — not just the validation command — to the empty `~/.claude/skills/` window; (f) `next-steps:157` SANITIZE diff was ambiguous about whether one or both sentences should be replaced; (g) the README Trigger-shadow note conflated *manual* invocation (slash-command UI) with *auto-trigger* (description-match pathway) and pointed adopters at `disable-model-invocation` even though the typical case is a conflicting skill the adopter doesn't own; (h) `## CHANGELOG.md content` was unspecified despite the file appearing in the layout; (i) `gh auth status` and `git --version` were unstated preconditions; (j) the `.gitignore` was sparse against the allowlist's exclusions; (k) Risk #2 acknowledged drift but didn't say which copy JP uses for ongoing dev work after a public-repo fix. **v5 changes:** (1) `merge-branch` moves from PUBLISH AS-IS → SANITIZE (rephrase line 17 to drop "the commit-push-pr workflow"); new count **12 PUBLISH + 10 SANITIZE = 22**. (2) `next-steps` SANITIZE row expanded to cover lines 21+28 ("Next Steps protocol" phantom → "session-sized implementation planning"); :157 row rewritten to explicit "replace entire paragraph (both sentences)". (3) Adds **Success criteria for v0.1.0** section (post-publish measurable outcomes, distinct from process-level acceptance criteria). (4) README Requirements adds Claude Code v2.1.32+ version floor. (5) README Trigger-shadow note rewritten to split *manual* vs *auto-trigger* and lead with `skillOverrides` (settings-level, no skill-editing required for adopters). (6) Adds new section **`## CHANGELOG.md content`** with Keep-a-Changelog v0.1.0 template. (7) Step 0 gains **Preconditions** sub-block (`gh auth status`, `trash`, `git --version`). (8) `set -euo pipefail` at top of full bash workflow. (9) Step 4b regex narrowed to `\B/[a-z][a-z0-9-]+(?::[a-z0-9-]+)?` (PCRE, ~85% noise reduction); adds explicit FP-exclusion comment block; **adds category (e): named protocols/procedures/workflows**. (10) Step 7 mv+claude+restore wrapped in subshell so trap fires on subshell exit, not full shell exit. (11) `.gitignore` expanded: `evals/`, `*-workspace/`, `iteration-*/`, `*.local.md`. (12) Risk #2 expanded with explicit dev-staging options (a) backport, (b) accept dev-staging falls behind, (c) re-base dev-staging on public — choosing (b) for v1. (13) Risk #7 interrogated: alternative venues considered (split plugins, soft-warn, defer affected skills) and rejected with reasoning; "fail visibly, fix on bug report" is the v0.1.0 stance. (14) Acceptance criteria refreshed: count update (12+10), new criteria for v2.1.32+ check, named-protocol scan, `set -euo pipefail`, CHANGELOG.md presence, `gh auth status` precondition.
- **v6 (this revision):** minor revision after a pre-execution audit miss surfaced during build-plan execution prep. A targeted scan of the 22-skill set for `trash` (a user-machine convention from the author's CLAUDE.md, not part of macOS or universal Claude Code surface) found **8 references in 2 skills** — `git-hygiene` ×7 (foundational; the skill is architecturally about deletion safety) and `writing-principles/writing-principles.md` ×1 (meta example in a prohibition-phrasing table). Both Step 4b structural scan and Step 5 lexical grep missed this category: lexical can't include `trash` (generic English word; FP-prone), structural categorized it as a real-tool reference rather than a personal-prescription. **v6 changes:** (1) `git-hygiene` SANITIZE row extended — replace 7 `trash` references with portable language ("a reversible deletion mechanism") and add a one-paragraph explanation listing concrete tools by OS (macOS `trash` via `brew`; Linux `trash-put` from `trash-cli`; GNOME `gio trash`; fallback inspect-before-`rm`). The skill's safety property (deletion is reversible) is preserved; tool selection delegates to adopter's installed toolchain. (2) `writing-principles` SANITIZE row extended — `writing-principles.md:753` meta-example swapped from `"NEVER run \`rm -rf\`"`/`"Always use \`trash\` or targeted deletion"` to `"NEVER commit secrets"`/`"Always exclude .env from commits"`. The didactic purpose (negative-instruction-is-clearer) is preserved; the local-convention leak is removed. (3) **Step 4b adds category (f): personal-tool prescriptions.** Manual checklist for command-style references in code blocks/backticks where the named tool isn't part of universal toolchain (`git`, `bash`, `rg`, POSIX core). Enumerated targets for v0.1.0: `trash`, `mise`, `stow`, `brew`, `uv`, `ruff`. Each match must be EITHER replaced with portable language OR explicitly documented as a hard requirement in the README. (4) Acceptance criteria updated to add category (f). (5) **Audit-completeness pattern noted in Decisions (item 1):** v4 added Step 4b (structural-vs-lexical), v5 added category (e) (named protocols), v6 adds category (f) (personal tools) — each scrutiny round has surfaced a category the prior framework missed. The audit-completeness premise is asymptotic, not absolute. New categories may continue to surface; future bug reports against the public repo are the catch-all.

## Problem

JP Sweeney maintains ~29 dev-staged Claude Code skills in `claude-code-tool-dev/extensions/skills/`, deployed to `~/.claude/skills/` via `scripts/promote`. He wants to share a curated subset publicly on GitHub as a portfolio-quality showcase that is also installable as a Claude Code plugin.

The new repo at `/Users/jp/Projects/active/claude-code-skills/` will be a fresh, parallel collection — independent of the dev monorepo, hand-picked once from current dev-staging, not synced ongoing.

## Success criteria for v0.1.0

The Acceptance criteria at the bottom of this spec verify *publication mechanics*. These criteria measure *outcome* — what success looks like a few weeks after `v0.1.0` ships. They are post-publish observations, not pre-publish gates; track them after release and use them to inform v1.x triage.

| Criterion | How to measure |
|---|---|
| Discoverable | Repo appears in `gh search repos claude-code-skills` and (when added) the official Claude Code marketplace search. |
| Installable without contacting the author | A first-time adopter can `git clone` + `--plugin-dir` *or* `/plugin marketplace add` + `/plugin install` and reach a working state, using only README + CONTRIBUTING.md. |
| No "missing flag" support traffic | Zero issues filed against the repo in the first month with title or body matching `experimental.*flag` or `agent.*teams.*not.*enabled` — the README Requirements section is prominent enough that adopters set the flag (and check version ≥ 2.1.32) before invoking affected skills. |
| Skill triggering works as described | Manual invocation via `/claude-code-skills:<name>` succeeds for all 22 skills; auto-trigger fires for representative descriptions (verified by spot-checking 3-5 trigger phrases per skill category). |

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
| Audit machinery | Two-layer: lexical residue grep (Step 5) AND structural-reference scan (Step 4b) | Different threat models. Lexical catches internal-vocab leakage in prose. Structural catches dangling references (slash commands, named skills, environmental flags, sibling-skill cross-refs) that lexical can't see — they use generic English words or plugin-relative paths. |

## Curated skill list (22, recategorized)

### PUBLISH AS-IS (12, after `.DS_Store` filtering)

`adversarial-review`, `exiting-worktrees`*, `format-export`, `implementation-review`, `llm-reference`, `prompt-generator`, `review-code`, `review-plan`, `review-strategy`, `review-writing`, `scrutinize`, `system-design-review`

\* `exiting-worktrees` SKILL.md content is clean, but the directory contains 180 KB of internal eval/benchmark workspace (`evals/`, `exiting-worktrees-workspace/iteration-1/...`, 30+ files). Use copy allowlist (see Implementation workflow) to ship only `SKILL.md`.

### SANITIZE — content changes required (10)

| Skill | Specific changes | Severity |
|-------|------------------|----------|
| `claude-md` | **Description (`SKILL.md:3`):** (a) drop the trailing sentence "For quick session-scoped updates, use `/revise-claude-md`." entirely (slash command not in plugin); (b) rephrase "Distinct from README (introducing the project), handbook (operating the system), and changelog (tracking changes)." → "Distinct from README (introducing the project), handbook (operating the system), and CHANGELOG.md (tracking changes)." (sibling-skill ambiguity → file-concept). **Decision Routing table:** (c) `SKILL.md:42` rephrase the value cell "Changelog skill" → "Write a CHANGELOG.md" (or drop the row entirely if the rephrasing reads awkwardly out of context — implementer's judgment); (d) `SKILL.md:43` drop the entire row whose key is `'Remember this for next time' / session note` and value is `/revise-claude-md` (no clean replacement; sibling rows still cover the surrounding cases). | High — structural |
| `git-hygiene` | (a) `SKILL.md:47` and `SKILL.md:330`: replace `codex/cleanup/YYYY-MM-DD-HHMMSS` branch convention with `cleanup/YYYY-MM-DD-HHMMSS` (drop the `codex/` prefix). (b) **Personal-tool prescription cleanup (added v6):** the skill prescribes `trash` as the deletion tool in 7 places — a user-machine convention from the author's CLAUDE.md, not portable. Replace each occurrence with portable language: line 21 `"Use \`trash\` for approved file deletions. Never use \`rm\` or \`git clean -fd\`."` → `"Use a reversible deletion mechanism (move-to-trash semantics) for approved file deletions. Never use \`rm\` or \`git clean -fd\` — they are irreversible."`; line 33 table-cell `"file deletion with \`trash\`"` → `"file deletion via reversible mechanism"`; line 151 `"Files to delete with trash:"` → `"Files to delete (reversible):"`; line 241 `"Delete approved files with \`trash\`."` → `"Delete approved files using a reversible mechanism (e.g., \`trash\` on macOS, \`trash-put\` on Linux, \`gio trash\` on GNOME)."`; line 291 `"Never use \`rm\` or \`git clean -fd\`; use \`trash\` for filesystem deletion."` → `"Never use \`rm\` or \`git clean -fd\`; use a reversible deletion mechanism (e.g., \`trash\`, \`trash-put\`, \`gio trash\`) for filesystem deletion."`; line 335 output-template `"files deleted with trash: 0"` → `"files deleted (reversible): 0"`; line 379 anti-pattern table `"Preview first and use \`trash\` only for explicitly approved files."` → `"Preview first and use a reversible deletion mechanism only for explicitly approved files."`. **Plus:** add a single explanatory paragraph immediately after line 21 (where the rule is first introduced) reading: `"This skill assumes a reversible deletion tool is available. On macOS, install \`trash\` via \`brew install trash\`. On Linux, install \`trash-cli\` (provides \`trash-put\`). On GNOME, \`gio trash\` is built in. If no reversible tool is available, inspect each file before \`rm\` — but a reversible tool is strongly preferred for the recovery property the rest of the skill assumes."` Skill becomes OS-portable; the safety property (recoverable deletion) is preserved. | High — portability |
| `next-steps` | (a) `SKILL.md:21` (table cell): rephrase `"Use Next Steps protocol instead"` → `"Use session-sized implementation planning instead"` (the "Next Steps protocol" referent is a phantom — verified absent from `~/.claude/CLAUDE.md`, `.claude/rules/`, and the entire dev monorepo via `rg`). (b) `SKILL.md:26`: rephrase "Output feeds into Codex dialogue or focused planning sessions" → "Output feeds into deeper planning sessions" (drop "Codex"). (c) `SKILL.md:28`: rephrase "If the conversation already has a clear implementation path, use the Next Steps protocol from CLAUDE.md instead." → "If the conversation already has a clear implementation path, use session-sized implementation planning instead." (d) `SKILL.md:155-157` (entire paragraph under "After producing the plan"): **replace both sentences** — "Suggest the user take the highest-risk or first-phase tasks into a Codex dialogue for deeper exploration. Use the literal slash command `/codex-collaboration:dialogue` so the user can invoke it directly." → "If you have a follow-up advisor skill, dispatch it here." (one sentence replaces two; do not leave a residual "Codex dialogue" mention in sentence 1). | High — structural |
| `merge-branch` | `SKILL.md:17` (When NOT to Use bullet): rephrase `"User wants a PR — use the commit-push-pr workflow instead"` → `"User wants a PR — push and open a PR via your normal workflow instead."` (drops the dangling external-plugin reference; the `commit-push-pr` command lives in the `commit-commands` plugin which is not in the 22-set, and the lexical Step 5 grep cannot catch bare-name workflow refs). | High — structural |
| `making-recommendations` | `SKILL.md:137-143`: remove the entire "Codex Delta" subsection. `references/codex-delta.md` (199 lines, 31 case-insensitive `codex` hits): delete the file. Verify the surrounding I8-I9 phase text doesn't dangle a reference to the removed section. | High — structural |
| `writing-principles` | (a) `SKILL.md` "Composability" section: remove. The section starts at line 140 (`## Composability`) and runs to end of file (line 168 in current state — Composability is the last `##` section). Lines 148, 149, 157, 163, 165 reference `creating-skills` and/or `claude-md-improver`. **Removal check:** verify the deletion ends at end-of-file or before the next `##` heading; the `## Failure Mode Index` section above it ends cleanly at line 138. (b) **Personal-tool prescription cleanup (added v6):** `writing-principles.md:753` (the references file, not SKILL.md) uses `trash` as a meta example in a prohibition-phrasing table. The example pair currently reads `\| "NEVER run \`rm -rf\`" \| "Always use \`trash\` or targeted deletion" \|`. Swap to `\| "NEVER commit secrets" \| "Always exclude .env from commits" \|`. The didactic purpose (negative-instruction-is-clearer-than-affirmative-inverse) is preserved with a universally-relevant security example, while the local-tool-convention leak is removed. | Medium |
| `handbook` | (a) `SKILL.md:3` description: rephrase "Distinct from READMEs (what it is) and CHANGELOGs (what changed)." → "Distinct from README files (introducing the system to users) and CHANGELOG.md files (tracking history)." (consistency with claude-md fix; explicit file-concept framing). (b) `references/agent-teams.md:3`: remove the "Adapted from `packages/plugins/superspec/...`" attribution line. (c) `references/agent-teams.md:4`: rephrase "For documentation skills (readme, changelog, handbook)." → "For documentation skills (readme, handbook)." (drop the dangling "changelog" sibling reference). | Medium |
| `readme` | (a) `references/agent-teams.md:3`: remove the "Adapted from `packages/plugins/superspec/...`" attribution line. (b) `references/agent-teams.md:4`: rephrase "For documentation skills (readme, changelog, handbook)." → "For documentation skills (readme, handbook)." | Low |
| `design-review-team` | (a) `references/agent-teams.md:3`: remove the "Adapted from `packages/plugins/superspec/...`" attribution line. (b) `references/agent-teams.md:4`: rephrase "For documentation skills (readme, changelog, handbook)." → "Used by skills that orchestrate parallel agent teams." (one rewrite kills both the dangling "changelog" and the misattribution — `design-review-team` is a review skill, not a documentation skill). (`SKILL.md:243` `docs/audits/` reference is already conditional — no change.) | Low |
| `explore-repo` | `references/agent-teams.md:3`: remove the "Adapted from `packages/plugins/superspec/...`" attribution line. (Line 4 reads "For exploration skills (explore-repo)." — no `changelog` mention, no change needed.) | Low |

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

The marketplace uses a self-referential `"./"` source: marketplace and plugin live in the same repo, both manifests in `.claude-plugin/`, skills at repo root. Per the official `plugin-marketplaces#plugin-sources` docs: relative path sources "must start with `./`" and are "resolved relative to the marketplace root, not the `.claude-plugin/` directory." `"./"` literally satisfies this rule.

**Pre-validation gate (Step 0 in Implementation workflow):** before committing to this layout, verify `source: "./"` accepts at runtime in a throwaway scratch repo (3 minutes of work). Docs verification is necessary but not sufficient — the version of `claude` the implementer is running may not be the version the docs describe. **If Step 0 confirms acceptance**, the layout above is final. **If Step 0 fails**, restructure the spec for a nested layout (plugin contents in `plugins/claude-code-skills/`, `marketplace.json source: "./plugins/claude-code-skills"`) **before** beginning Steps 1-11. Do not bake a runtime fallback into the implementation order.

## README structure

Voice: first-person, technical, direct. Match SKILL.md authoring voice. Audience: portfolio reader AND plugin adopter, balanced.

Sections:

1. **Title + one-paragraph hook** — what this is, who it's for. Mentions the focus areas (review, critique, grounded documentation) and that everything is also installable.
2. **Namespacing note + Trigger-shadow note** (two short paragraphs, prominent) — covers two distinct mechanisms; conflating them is a real source of adopter confusion:
   > **Manual invocation:** all skills are invoked as `/claude-code-skills:<name>` — e.g., `/claude-code-skills:scrutinize`. The namespaced form ensures you get this plugin's version when you invoke it directly via the slash-command UI.
   >
   > **Auto-trigger conflicts:** if you have a skill with the same name installed elsewhere (e.g., a globally-promoted `scrutinize` from another source), Claude may auto-trigger that one based on natural-language match — the namespaced form does *not* apply, because no slash command is involved in auto-trigger. To force this plugin's version on auto-trigger, set [`skillOverrides`](https://code.claude.com/docs/en/skills#override-skill-visibility-from-settings) in your `settings.json` to hide the conflicting skill (this works for skills you do not own — no file editing required), or rely on description-quality differences between the two skills.
3. **Requirements** (new section, prominent) — covers Claude Code prerequisites:
   > **Claude Code v2.1.32 or later.** Check with `claude --version`. Per the [official agent-teams docs](https://code.claude.com/docs/en/agent-teams), agent teams require this version floor. Earlier versions silently lack the feature; the affected skills will hard-stop with the same "set the flag" guidance *even when the flag is set*, which is the worst-of-both-worlds UX.
   >
   > **Claude Code with the experimental agent-teams feature enabled.** Set `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in your `settings.json` env block. This affects: `claude-md`, `design-review-team`, `explore-repo`, `handbook`, `readme` (5 of 22 skills) — these hard-stop without it. The other 17 skills work without the flag.
   >
   > Note: agent-teams is an experimental Claude Code feature and may change. If Anthropic renames or deprecates the flag, the affected skills will need updates; bug reports against the public repo are welcome if that happens.
4. **What's in here** — skill catalog grouped by category, each entry one-liner-linked to its `SKILL.md`. (Optional: mark the 5 agent-teams-dependent skills with a footnote ↗ pointing back to Requirements.)
5. **Install** — two paths:
   - **Try it (clone + dev flag):** `git clone` + `claude --plugin-dir`. (NB: this clones the repo to disk; only the *plugin load* is session-scoped, not the clone.)
   - **Install permanently (marketplace):** `/plugin marketplace add jpsweeney97/claude-code-skills` then `/plugin install claude-code-skills@jpsweeney97-skills`.
6. **Use a skill** — brief example showing namespaced invocation.
7. **Contributing** — short policy: issues welcome (bug reports, feature requests). PRs reviewed case-by-case. Public repo is canonical for shipped fixes. Link to CONTRIBUTING.md for details.
8. **License** — MIT with link to LICENSE.
9. **Author** — JP Sweeney, GitHub profile link.

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

## CHANGELOG.md content

Format: [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) + [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html). The file lives at the repo root (not inside `.claude-plugin/`) so it is browsable on GitHub.

Standard preamble (3 lines after `# Changelog`):

> All notable changes to this project will be documented in this file.
>
> The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

### `v0.1.0` initial release entry (template)

Heading: `## [0.1.0] - YYYY-MM-DD` (use the actual publish date).

Sections:

- **Added** — list the catalog by category (mirror the README Skill catalog grouping):
  - Review & adversarial critique (9 skills): `adversarial-review`, `scrutinize`, `implementation-review`, `system-design-review`, `design-review-team`, `review-code`, `review-plan`, `review-strategy`, `review-writing`.
  - Grounded documentation generation (3 skills): `readme`, `handbook`, `claude-md`.
  - Repo exploration & analysis (2 skills): `explore-repo`, `llm-reference`.
  - Workflow (7 skills): `git-hygiene`, `merge-branch`, `exiting-worktrees`, `next-steps`, `making-recommendations`, `prompt-generator`, `format-export`.
  - Authoring (1 skill): `writing-principles`.
  - Marketplace catalog at `.claude-plugin/marketplace.json` for one-line install.
  - README with namespacing + Trigger-shadow + Requirements sections; CONTRIBUTING.md with maintenance flow; MIT license.

- **Notes** — surface the version + flag dependency:
  - Five skills (`claude-md`, `design-review-team`, `explore-repo`, `handbook`, `readme`) require Claude Code v2.1.32+ and `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. See README Requirements section.

**Forward-compatibility convention:** every commit is a new release for marketplace consumers (no `version` field in `plugin.json`), but CHANGELOG entries are still tagged at semver milestones — small fixes accumulate under an `## [Unreleased]` section, and a new `## [X.Y.Z] - YYYY-MM-DD` block is added when a meaningful chunk of changes ships. This keeps the human-readable changelog coherent even though the install-time version is SHA-driven.

## Implementation workflow

**Note on `rm` usage:** The dev environment's CLAUDE.md prohibits `rm` and `rm -rf`; deletion uses `trash` (macOS `trash-cli`, available via `brew install trash`). The implementing Claude session inherits this rule. All deletion in this workflow uses `trash`. If running on a system without `trash-cli`, install it first or substitute the local equivalent.

**Preconditions** (verify before starting Step 0):

- `gh auth status` reports authenticated (Steps 9-10 use `gh repo create` and `gh repo edit`).
- `command -v trash` resolves to a binary (per the `rm` note above; deletion in Steps 3 and 7 uses `trash`).
- `git --version` reports `≥ 2.28` (Step 1 uses `git init -b`, which lands in 2.28).
- `claude --version` reports `≥ 2.1.32` if the implementer wants to invoke any of the 5 agent-teams-dependent skills during Step 7 spot-checks.

```bash
set -euo pipefail   # fail fast on unhandled errors; stop at first command that returns non-zero
                    # (essential for Step 7's tar backup — silent backup failure must not cascade
                    # into the destructive mv that follows).

# 0. PRE-FLIGHT — pre-validate `marketplace.json source: "./"` in a throwaway scratch repo.
#    Don't commit to the layout in Steps 1-11 until you confirm "./" accepts at runtime.
#    Docs verification is necessary but not sufficient — the running CLI may differ from docs.
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
  git add . && git commit -q -m "test"
)
echo "Scratch repo at: $SCRATCH"
echo ""
echo "In a fresh claude session, run:"
echo "  /plugin marketplace add $SCRATCH"
echo "  /plugin install test-skill@test-mp"
echo ""
echo "PASS: install completes → source: \"./\" is validated for this CLI version."
echo "      Proceed to Step 1 with the layout in this spec as-is."
echo "FAIL: install rejected → restructure the public repo for nested layout"
echo "      (plugin contents in plugins/claude-code-skills/, marketplace source"
echo "      \"./plugins/claude-code-skills\") BEFORE Step 1. Update this spec accordingly."
echo ""
echo "Cleanup after validation: trash \"$SCRATCH\""

# 1. Create + init
mkdir /Users/jp/Projects/active/claude-code-skills
cd /Users/jp/Projects/active/claude-code-skills
git init -b main

# 2. Build structure
mkdir -p .claude-plugin skills

# 3. Copy 22 skills using ALLOWLIST (NOT `cp -r`).
#    Ship: SKILL.md (always), references/* (if present), examples/* (if present),
#    top-level *.md siblings (e.g., writing-principles/writing-principles.md).
#    Allowlist intrinsically excludes: .DS_Store, evals/, *-workspace/, iteration-*/
#    (the conditional `for sub in references examples` only ships those two subdirs).
#    A belt-and-braces denylist sweep is therefore unnecessary AND would require `rm -rf`
#    which the dev-environment CLAUDE.md prohibits — drop the sweep entirely.
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
# Strip .DS_Store using trash (single-file deletion, recoverable):
find skills -name '.DS_Store' -exec trash {} \;

# 4. Sanitize the 10 SANITIZE skills (apply diffs from "Curated skill list / SANITIZE" table)
#    - claude-md: drop /revise-claude-md description sentence; rephrase "and changelog"
#      → "and CHANGELOG.md"; rephrase Decision Routing "Changelog skill" cell;
#      drop the /revise-claude-md row entirely.
#    - git-hygiene: replace `codex/cleanup/` with `cleanup/` (2 lines).
#    - next-steps: 4 changes — (a) :21 table cell "Use Next Steps protocol instead" →
#      "Use session-sized implementation planning instead"; (b) :26 drop "Codex"; (c) :28
#      rephrase "use the Next Steps protocol from CLAUDE.md instead" → "use session-sized
#      implementation planning instead"; (d) :155-157 ENTIRE PARAGRAPH (both sentences)
#      replaced by single sentence "If you have a follow-up advisor skill, dispatch it here."
#    - merge-branch: rephrase :17 to drop "the commit-push-pr workflow" external-plugin ref.
#    - making-recommendations: remove "Codex Delta" section + delete references/codex-delta.md (use trash).
#    - writing-principles: remove Composability section (SKILL.md:140-end-of-file).
#    - handbook: rephrase SKILL.md:3 description (CHANGELOGs → CHANGELOG.md);
#      drop superspec attribution from agent-teams.md:3; drop "changelog" from agent-teams.md:4.
#    - readme: drop superspec attribution from agent-teams.md:3; drop "changelog" from line 4.
#    - design-review-team: drop superspec attribution from agent-teams.md:3; rewrite line 4
#      ("documentation skills (readme, changelog, handbook)" → "skills that orchestrate parallel agent teams").
#    - explore-repo: drop superspec attribution from agent-teams.md:3 (line 4 is already clean).

# 4b. STRUCTURAL-REFERENCE SCAN — manual checklist gate, complements Step 5 lexical grep.
#     Lexical grep can't see references that use generic English words or plugin-relative paths.
#     Run AFTER sanitization, BEFORE the lexical grep. Resolve any dangling refs before continuing.
#
#     For each shipped skill, verify:
#     (a) Slash-command refs (/<name>): rg -nP '\B/[a-z][a-z0-9-]+(?::[a-z0-9-]+)?' skills/
#         The \B (non-word-boundary) anchor excludes filesystem paths like `path/to/file`
#         and URL bodies like `example.com/path` (both have word|non-word transitions at
#         the slash), while including ` /scrutinize`, `(/scrutinize)`, `` `/scrutinize` ``,
#         and `:/example.com/foo`. Measured: ~265 hits on the unanchored regex
#         `/[a-z][a-z0-9-]*\b`, ~40 hits on the \B form (85% noise reduction). Of the
#         residual ~40 hits, eyeball-skip these known false positives:
#           - `~/.claude/teams/...`, `~/.claude/tasks/...` (functional Claude Code paths)
#           - `{workspace}/exploration/...` (template placeholders in agent-teams.md)
#           - Built-in commands: `/resume`, `/rewind`, `/help`, `/export`, `/clear`
#           - Surviving URLs/markdown links: `https://...`
#         Real defects look like plugin-relative slash commands not in the 22-set
#         (e.g., `/revise-claude-md`, `/codex-collaboration:dialogue`).
#     (b) Named-skill refs in tables/prose: search for "X skill", "the X skill",
#         "and X (...)", "Distinct from X". Each X must be in 22-set OR refer to a
#         file/format (e.g., CHANGELOG.md not "Changelog skill").
#     (c) Environmental flag deps: rg -n 'CLAUDE_CODE_EXPERIMENTAL_|CLAUDE_[A-Z_]+' skills/.
#         Each must be documented in README Requirements OR removed.
#     (d) Sibling-skill cross-references in descriptions: search for "Distinct from X, Y, Z"
#         patterns. Each named skill must be in 22-set OR converted to file/format.
#     (e) NAMED PROTOCOLS / PROCEDURES / WORKFLOWS (added v5):
#         rg -nP '\b[\w-]+(?:[\s-][\w-]+)*\s+(workflow|protocol|procedure)\b' skills/
#         Each match must refer to a real entity defined in shipped content, OR be reworded
#         to a generic phrase. Watch for "the X workflow", "X protocol from Y", "X procedure"
#         where X is a name that won't exist after curation. Two real instances v4 missed:
#         `merge-branch:17` "the commit-push-pr workflow" (lives in `commit-commands` plugin,
#         not in 22-set) and `next-steps:21,28` "Next Steps protocol from CLAUDE.md" (phantom —
#         not in user/project CLAUDE.md or rules; verified via rg).
#     (f) PERSONAL-TOOL PRESCRIPTIONS (added v6):
#         Manual checklist for command-style references in code blocks/backticks where the
#         named tool is NOT part of the universal toolchain (`git`, `bash`/`sh`, `rg`, `grep`,
#         `find`, `cat`, `ls`, `mv`, `cp`, `mkdir`, POSIX core). Enumerated targets for v0.1.0
#         (run case-sensitive, word-boundary, scoped to the 22-set):
#           rg -nw 'trash|trash-cli|brew|mise|stow|uv|ruff' skills/
#         Each match must be EITHER (1) replaced with portable language (e.g., "a reversible
#         deletion mechanism" with concrete-tools paragraph for adopters), OR (2) explicitly
#         documented as a hard requirement in the README's Requirements section.
#         v5 missed this category: `git-hygiene` SKILL.md prescribed `trash` in 7 places, and
#         `writing-principles/writing-principles.md:753` used `trash` in a meta example. Both
#         fixed in the v6 SANITIZE table.
#         **Why this isn't in Step 5 lexical:** these are real English words / real tool names
#         with high false-positive rate ("trash this idea", `mv` is universal POSIX). Lexical
#         can't gate on them without diluting its precision. Category (f) is structural-checklist
#         territory — bounded, manually adjudicated, with documented portable replacements.
#
#     For v1, expected result after Step 4 sanitization: zero dangling structural refs.
#     If a sanitization edit introduced a new dangling ref, fix it before Step 5.

# 5. Run sanitization-residue grep across all 22 skills (expanded token list)
rg -i -n 'codex|cross-model|engram|superpowers|superspec|page[ -]?turner|claude-code-tool-dev|jpsweeney97|sweeney|handoff-archivist|claude-md-improver|creating-skills|cc-docs|openai-docs|claude-code-docs|evaluating-extension-adoption|exploring-claude-repos|delegate|delegation|dialogue|extensions/skills|scripts/promote|docs/learnings|docs/handoffs|docs/tickets|claude_ai_|/Users/jp|T-20[0-9]{6}|packages/plugins|revise-claude-md' skills/
# Known false positives (common-English usage, NOT internal-vocab — leave them):
#   - skills/writing-principles/writing-principles.md:54   ("Scoped instructions for delegated tasks")
#   - skills/writing-principles/writing-principles.md:1025 ("Dynamic dialogue has different constraints")
# Expected output: ONLY the two known false positives above. Any other hit is real residue — sanitize before continuing.

# 6. Write plugin.json, marketplace.json, README.md (with Requirements + Trigger-shadow note),
#    LICENSE, CHANGELOG.md (per "## CHANGELOG.md content" section above), CONTRIBUTING.md,
#    .gitignore.
#    LICENSE: MIT template, copyright "JP Sweeney", current year (2026)
#    .gitignore: at minimum, .DS_Store, *.swp, .idea/, .vscode/. Plus defensive-against-drift
#    entries: evals/, *-workspace/, iteration-*/, *.local.md (these are intrinsically excluded
#    by the Step 3 allowlist for the initial copy, but if JP later edits skills directly in
#    the public repo per the maintenance flow, an inadvertent eval/workspace dir would not
#    be ignored without these patterns).

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

# Wrap the validation block in a subshell so the trap fires on SUBSHELL exit, not on
# the user's full interactive-shell exit. Without subshell scoping, ~/.claude/skills/
# would remain empty for the rest of the user's main-shell lifetime — any concurrent
# claude session, new terminal, or scheduled hook firing during that window would see
# the empty directory and misbehave. The subshell confines the empty-skills window to
# the `claude --plugin-dir` invocation itself.
(
  # Trap uses `trash` (not rm -rf) per the dev-environment CLAUDE.md prohibition.
  # Sequence on subshell exit:
  #   1. Move the empty test dir aside (`|| true` so a missing dir under `set -e`
  #      doesn't abort the trap before step 2 runs).
  #   2. Move the original skills back into place.
  #   3. Trash the entire tmp dir (sends to macOS Trash; recoverable if needed).
  # Single-quoted so $TMPSKILLS expands at trap-fire time, not at trap-set time.
  trap 'mv ~/.claude/skills "$TMPSKILLS/skills.test" 2>/dev/null || true; mv "$TMPSKILLS/skills.bak" ~/.claude/skills; trash "$TMPSKILLS"' EXIT
  mv ~/.claude/skills "$TMPSKILLS/skills.bak"
  mkdir ~/.claude/skills

  # Now run validation:
  claude --plugin-dir . --debug   # verify all 22 skills register on a clean ~/.claude/skills/
  # Test a few invocations: /claude-code-skills:scrutinize, /claude-code-skills:adversarial-review
)
# Subshell exited; trap fired; ~/.claude/skills is restored.
# Tarball at $BACKUP remains as defense-in-depth; trash it after verifying restore.
# Note: with `set -euo pipefail` at the top of the workflow, the tar above already
# fails fast on disk-full / permission / quota errors — no separate exit-on-fail check needed.

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

1. **Audit completeness — multi-category machinery, asymptotic completeness (v4 → v6)** — v1's audit was unsound on 4 of 22 skills. v2 re-audited via direct file inspection + strict vocab grep covering 18+ token categories. v3 baked false-positive expectations into the grep comment. **v4 adds Step 4b: structural-reference scan** — a manual checklist that catches a separate failure class (dangling slash commands, named skills, environmental flag deps, sibling-skill cross-refs) invisible to lexical scanning. Lexical and structural address different threat models: lexical = "internal-vocab leakage in prose"; structural = "references to things not in the published set." **v5 added Step 4b category (e):** named protocols / procedures / workflows (caught two real misses — `merge-branch:17`, `next-steps:21,28`). **v6 added Step 4b category (f):** personal-tool prescriptions (caught 8 real `trash` references in 2 skills that lexical can't gate on without high FP rate). **Pattern observed across v4 → v5 → v6:** each scrutiny round has surfaced a category the prior framework missed; the audit-completeness premise is **asymptotic**, not absolute. New categories may continue to surface in future scrutiny — when discovered, the response is (1) define the category, (2) add a Step 4b sub-scan, (3) update SANITIZE table for known instances. Residual risk after the current six categories: terms, refs, or tool-prescriptions outside the pattern sets (e.g., specific person names, company references, internal slang, niche tools the author hasn't flagged). Acceptance: residual risk treated as below threshold for v0.1.0; future findings handled as bug reports against the public repo.

2. **Drift over time** — Parallel model means skills will diverge between dev monorepo and public repo. Maintenance flow: public repo is canonical for shipped fixes (per decision). When the user wants to ship dev improvements to public, it's a deliberate copy-and-sanitize step, not automatic.

   **Dev-staging reconciliation after a public-repo fix lands (v5)** — three options, each with a different trade-off:
   - (a) **Backport immediately** to dev-staging: keeps both copies in sync. Cost: JP must remember and run `scripts/promote` after every public-repo fix. High discipline overhead.
   - (b) **Accept dev-staging falls behind**: zero ongoing cost, but the dev monorepo carries known bugs the public copy has already fixed. Acceptable when dev-staging usage is low-frequency.
   - (c) **Re-base dev-staging on the public repo** at each new dev cycle (`cp -r claude-code-skills/skills/* extensions/skills/`, then re-add internal-vocab references). Highest one-shot cost; zero ongoing cost.

   **Decision for v0.1.0: option (b).** Reasoning: bug-fix volume is expected to be low (curated subset, polished skills), and JP is the only consumer of dev-staging copies, so divergence is low-stakes. Reconsider for v1.x if drift becomes painful.

3. **Globally-promoted skill collision in local validation** — Per `Trigger Eval Findings #1`, `~/.claude/skills/` already containing all 22 skills means local plugin-namespaced validation is contaminated. Step 7 of the workflow stashes `~/.claude/skills/` to a tmp dir during validation and restores via `trap`. Trap-failure modes (`kill -9`, crash, terminal-close) and concurrent-session exposure are addressed under Risk #5 — Step 7 takes a tarball snapshot before the move, making recovery a one-command `tar xzf` even if the trap fails. Acceptance: documented preconditions + tarball snapshot reduce residual risk to the validation window itself.

4. **Plugin-private MCP tools referenced in supporting `references/*.md`** — `making-recommendations/references/codex-delta.md` references `mcp__plugin_codex-collaboration_*` tools inline. Sanitization step deletes this entire file, removing the issue. Verification: Step 5 grep includes `codex` token, will catch any straggler references.

5. **Stash/restore race condition during validation** — During the Step 7 validation window, ANY concurrent claude invocation (other terminal, tmux pane, IDE, scheduled cron/launchd job, hook, accidental new shell) sees an empty `~/.claude/skills/` until the trap restores it. The trap doesn't fire on `kill -9`, system crash, or "terminal closed without Ctrl-D" in some terminal emulators. Mitigation: Step 7 documents preconditions explicitly AND takes a tarball snapshot before the move, so recovery is one command (`tar xzf "$BACKUP" -C ~/.claude`) even when the trap fails to fire. Acceptance: residual exposure is the validation-window itself; if a precondition-violating session fires anyway, it gets a contaminated read for the duration.

6. **Functional Claude Code path references in shipped skills (not contamination)** — Five skills (`design-review-team`, `explore-repo`, `handbook`, `readme`, `claude-md`) reference `~/.claude/teams/`, `~/.claude/tasks/`, or `~/.claude/CLAUDE.md`. These are functional Claude Code paths — where the harness expects to find teams state, tasks state, and project memory — not internal-project vocabulary. They ship as-is. The Step 5 grep token list deliberately excludes `~/.claude` because it's universal Claude Code surface area, not personal context.

7. **Experimental agent-teams flag dependency (v4 / interrogated v5)** — Five skills (`claude-md`, `design-review-team`, `explore-repo`, `handbook`, `readme`) — 22.7% of the catalog — hard-stop on `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` with no graceful degradation. **Stakes:** an adopter who installs the plugin without the flag set (or on Claude Code < v2.1.32) could hit hard-stops on the first 1-5 skills they try.

   **Venue interrogation (v5):** is a public marketplace plugin the right venue for skills with this brittleness? Three alternatives considered:
   - (1) **Split into two plugins** — `claude-code-skills` (17 stable) + `claude-code-skills-experimental` (5 agent-teams-dependent). Pro: cleaner UX for the stable subset. Con: fragments the portfolio narrative; doubles the maintenance surface; adopters wanting documentation skills *do* need the agent-teams ones.
   - (2) **Downgrade hard-stop to soft-warn** — affected skills detect missing flag and run a degraded single-agent fallback. Pro: better UX on missing flag. Con: substantial code change in 5 skills (each is designed around team coordination); falls outside the v0.1.0 publication scope.
   - (3) **Defer the 5 affected skills to v1.x** — ship only the 17 stable ones for v0.1.0. Pro: zero hard-stop risk. Con: drops three of the most distinctive skills (`claude-md`, `handbook`, `readme`) from the initial catalog, undermining the "grounded documentation generation" category.

   **Decision for v0.1.0: ship as-is — "fail visibly, fix on bug report."** Reasoning: (a) the 17 non-affected skills work without the flag, so adopter value is substantial even with hard-stops on 5; (b) hard-stop is more honest than degraded behavior for skills explicitly designed around team coordination; (c) splitting plugins fragments a portfolio narrative; (d) the README Requirements section (now also documenting Claude Code v2.1.32+) is the primary mitigation. Reconsider for v1.x if bug-report volume indicates the framing isn't clear to adopters.

   **Acceptance:** if the flag is renamed or deprecated, those 5 skills go dark until updated; bug reports against the public repo handle the breakage. The other 17 skills are unaffected. **Open question (v1.x):** should the spec pin a `claude-code` CLI version range (lower bound `2.1.32`, upper bound TBD) to insulate against future changes?

8. **OSINT correlation with the dev monorepo (v4 explicit framing)** — `claude-code-tool-dev` is itself public on GitHub. The strict-vocab decision in this spec reduces *casual-reader* OSINT exposure but does not actually obfuscate from a determined reader who can correlate the two repos via author/commit/style. Acceptance: this spec's threat model is "reduce casual exposure," not "prevent attribution." The CONTRIBUTING.md "larger personal collection" wording sets expectations without exposing the monorepo's surface area; users who go looking will find the dev monorepo, but they have to look.

## Acceptance criteria

- **Preconditions verified** (added v5) — before Step 0: `gh auth status` authenticated; `command -v trash` resolves; `git --version` ≥ 2.28 (for `git init -b`); `claude --version` ≥ 2.1.32 if any agent-teams skill will be invoked during Step 7 spot-checks.
- **Step 0 (preflight) passes** — `marketplace.json source: "./"` accepts in the throwaway scratch repo. If it fails, the spec is restructured to nested layout BEFORE any of Steps 1-11 run.
- **`set -euo pipefail`** is the first directive of the implementation bash block (added v5) — silent failure of the Step 7 `tar` backup must not cascade into the destructive `mv` that follows.
- All 22 skills present in `skills/` with sanctioned content only (no `.DS_Store`, no `evals/`, no `*-workspace/`, no `iteration-*/`).
- **10 sanitization changes** applied per the SANITIZE table; running the **Step 5 lexical grep** returns ONLY the two documented false positives (`writing-principles.md:54`, `:1025`).
- **Step 4b structural-reference scan** returns no dangling references across all six categories: (a) slash commands via `\B/[a-z]…` PCRE (eyeball-skip the documented FP list); (b) named-skill refs in tables/prose; (c) environmental flag deps; (d) "Distinct from X, Y, Z" sibling refs; (e) **named protocols / procedures / workflows** (added v5; catches refs like "the X workflow" / "Y protocol from Z"); (f) **personal-tool prescriptions** (added v6; enumerated targets `trash`, `trash-cli`, `brew`, `mise`, `stow`, `uv`, `ruff` — each match either replaced with portable language or documented as a hard README requirement).
- `plugin.json` has no `version` field. `marketplace.json` uses `source: "./"` (validated in Step 0).
- **Step 7 trap is subshell-scoped** (added v5) — verify by inspecting the source: the `trap → mv → claude` sequence lives inside `( ... )` so the empty-skills window closes when validation exits, not when the user's interactive shell exits.
- `claude --plugin-dir . --debug` (with `~/.claude/skills/` masked per Step 7's subshell-scoped trap) shows all 22 skills loading without errors.
- `/plugin marketplace add` (local-path or `gh:`) succeeds; `/plugin install claude-code-skills@jpsweeney97-skills` completes; all 22 skills invokable as `/claude-code-skills:<name>` without plugin-private-MCP permission prompts.
- **No `rm` or `rm -rf` in the implementation script.** All deletions use `trash` or rely on the copy allowlist (which never includes denylisted content in the first place).
- README has: namespacing note + **Trigger-shadow note split into manual-invocation vs auto-trigger sub-points** (added v5), with [`skillOverrides`](https://code.claude.com/docs/en/skills#override-skill-visibility-from-settings) as the primary auto-trigger remediation; **Requirements section** documenting **Claude Code v2.1.32+** (added v5) AND `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` AND the 5 affected skills; install instructions for both paths; skill catalog with category groupings; contributing policy; license link.
- **CHANGELOG.md** exists at repo root with Keep-a-Changelog 1.1.0 format and a `## [0.1.0] - YYYY-MM-DD` entry listing the 22 skills by category (added v5).
- LICENSE file is MIT with current year (2026) and copyright "JP Sweeney".
- CONTRIBUTING.md states the public-repo-canonical maintenance flow.
- `.gitignore` includes `.DS_Store, *.swp, .idea/, .vscode/` AND `evals/, *-workspace/, iteration-*/, *.local.md` (added v5; defensive against post-publish drift).
- GitHub repo is public, tagged `v0.1.0`, with five discoverability topics applied (one per `--add-topic` invocation).
- **Post-publish (added v5):** track [Success criteria for v0.1.0](#success-criteria-for-v010) (top of spec) for the first month after release; observations inform v1.x triage.
