## Adversarial Review: Engram Design Spec

**Target:** `docs/superpowers/specs/2026-03-16-engram-design.md`
**Reviewed:** 2026-03-16
**Depth calibration:** High — This is an architecture decision that consolidates three production plugins with combined 950 tests, introduces new abstractions (NativeReader, typed envelopes, identity system), migrates data to new locations, and deletes old code. Irreversible once committed past Step 3.

---

### 1. Steel-Man

The strongest argument for Engram is **identity resolution via `repo_id`**. The three existing systems all struggle with the same unsolved problem: Claude Code sessions have no stable way to reference "this project" across clones, renames, forks, and worktrees. Handoff keys by directory name (breaks on rename). Tickets live at `docs/tickets/` (no worktree isolation). Learnings have no provenance linking back to the session that produced them. A committed UUIDv4 at `.engram-id` solves all three simultaneously, and this identity foundation cannot be meaningfully added to each plugin independently — it needs a shared layer. The `RecordRef` type that builds on this identity is the load-bearing abstraction that makes cross-subsystem query, dedup, and timeline possible.

---

### 2. Assumptions Audit

**A1. Three plugins solving "the same underlying problem" is the right framing.**
The spec's core insight is that handoff, ticket, and learning all solve "Claude Code has no persistent state." But handoff solves *session continuity*, tickets solve *work tracking*, and learnings solve *knowledge curation*. These overlap on "persistence" the way email, Slack, and documentation overlap on "communication" — the shared substrate doesn't imply they should be one system. **What breaks:** If the subsystems' concerns diverge (e.g., tickets gain dependency graphs, knowledge needs vector search), the shared layer becomes a constraint rather than an enabler. **Early detection:** During Step 3/4, notice whether subsystem engines need to work around `engram_core` abstractions rather than benefit from them.

**A2. MVP scale (~100s of files) holds for the fresh-scan indexing model.**
The spec assumes "no cached index" is viable because file counts are small. But ticket audit trails are JSONL files that grow per-session, handoff archives accumulate at 30/90-day retention, and the knowledge staging inbox has *no TTL*. **What breaks:** If a busy project accumulates 500+ tickets over months (the spec mentions this threshold for NativeReader latency), every `/search` and `/triage` call does a full filesystem scan with YAML/frontmatter parsing. **Early detection:** Instrument query latency from Step 1. Track file counts per subsystem.

**A3. `engram_core/` living inside the plugin won't create import path issues.**
The spec puts the shared library inside `packages/plugins/engram/engram_core/`. Tests, scripts, and hooks all need to import from it. Claude Code plugins have specific execution contexts — hook scripts run as standalone processes, skill-invoked scripts run via `uv run`. **What breaks:** If hook scripts can't resolve `engram_core` imports without `sys.path` manipulation, every hook becomes fragile. The current ticket plugin avoids this by having self-contained scripts. **Early detection:** Step 0 must prove that `engram_guard` hook can `import engram_core.identity` without path hacks.

**A4. The ticket plugin's 15 machine states and 4-stage pipeline can be transplanted without behavioral regression.**
The spec's compatibility harness compares "response envelope, on-disk output, audit side effects, hook allow/deny, dedup/TOCTOU/trust outcomes." But the ticket pipeline's behavior depends on execution context: hook-injected trust triples, temporary payload files in `.claude/ticket-tmp/`, and re-reading live policy at execute time. **What breaks:** If the new Work engine changes any of these execution-context details — different temp paths, different hook injection points, different policy file location — tests pass but production behavior drifts. **Early detection:** The compatibility harness must replay real ticket creation sequences (not just fixture comparisons), including the hook injection path.

**A5. No external users means no migration compatibility burden.**
The spec says "We can break old plugins freely during development." But the user has promoted plugins to `~/.claude/` and uses them daily. Old handoff data at `~/.claude/handoffs/<project>/` contains session history. **What breaks:** If migration doesn't cover all existing handoff files (edge cases: handoffs with missing frontmatter, checkpoints vs full saves, chain state files mid-session), the user loses access to prior session context. **Early detection:** Inventory all files in `~/.claude/handoffs/` before migration. Count how many parse cleanly with the new Context reader.

**A6. The `engram_guard` hook can reliably detect and block Bash file writes to protected paths.**
The spec explicitly acknowledges this is "best-effort" for Bash interception. But it still lists Bash protection as a feature and includes it in success criteria ("Direct Write/Edit/Bash to `engram/work/` blocked"). **What breaks:** If the guard reliably catches Write/Edit but inconsistently catches Bash, users develop false confidence that protected-path enforcement is comprehensive when it has a known bypass. **Early detection:** This is already known. The question is whether the spec should remove Bash from the success criteria or explicitly document the gap in the skill surface.

---

### 3. Failure Modes

#### Most likely failures

**F1. Compatibility harness false confidence (high likelihood)**
The spec plans to triage 669 ticket tests into three buckets: ~100-150 compatibility-critical, ~200-250 fixture-port, ~200-300 don't-port. The triage itself is a judgment call with no objective criteria. Tests that seem "implementation-local" may actually encode behavioral invariants the spec author doesn't recognize because they were written by a different conversation session. **Trigger:** Step 3, during test triage. **Blast radius:** Work subsystem behavioral regressions that surface only when real tickets are created in production use. **Loud or silent:** Silent. Tickets get created with slightly wrong metadata, wrong dedup behavior, or wrong autonomy enforcement, and the errors aren't surfaced until much later.

**F2. `/save` orchestration partial failure UX (medium likelihood)**
The spec returns per-step results: `{snapshot: ok, defer: ok, distill: failed}`. But the user invoked `/save` — a single action with the expectation of a single outcome. A partial success is cognitively expensive: the user must understand which step failed, why, and whether to retry. **Trigger:** Any error in the distill or defer sub-operations. **Blast radius:** Localized to the save operation, but degrades trust in the system. **Loud or silent:** Loud, but confusingly so. The user sees "distill failed" but their snapshot was saved — is the session state safe? The answer is yes, but the UX doesn't make this obvious.

**F3. Staged knowledge candidate accumulation (medium likelihood)**
Knowledge staging has no TTL. The spec says "accumulate until curated" and relies on `/triage` to report pending counts. But `/triage` is user-initiated. If the user doesn't run `/triage` or `/curate`, staging candidates grow indefinitely in the private root. Each `/save` with distill enabled can add candidates. **Trigger:** Normal usage over weeks/months without running `/curate`. **Blast radius:** Disk growth in `~/.claude/engram/<repo_id>/knowledge_staging/`. When the user eventually runs `/curate`, they face a backlog of potentially hundreds of candidates, making curation impractical. **Loud or silent:** Silent until the user runs `/curate` and gets overwhelmed.

#### Highest-severity failure

**F4. Shadow authority via `snippet` field in `IndexEntry` (low likelihood, high severity)**
The spec says "`snippet` is not `summary`" and is "display-only, never used for dedup, triage decisions, or workflow logic." But `/triage` needs to cross-reference tickets, snapshots, and staged knowledge. If the triage skill uses `snippet` to make reasoning decisions (e.g., "this ticket looks related to that snapshot based on snippets"), it violates the "no decisions from IndexEntry alone" invariant. The risk is that the prohibition against using `snippet` for decisions is a spec-level rule that the skill implementation won't enforce because it's natural for the skill prompt to use whatever text is available. **Trigger:** Any skill that receives `IndexEntry` objects and reasons about them rather than opening native files. **Blast radius:** Cross-subsystem reasoning becomes based on lossy 200-char previews instead of full records. Decisions degrade silently. **Loud or silent:** Silent. Triage reports look plausible but are based on incomplete data.

---

### 4. Underspecification

**U1. How `engram_core` is importable from hooks, scripts, and tests (Accidentally omitted)**
The spec defines the package structure but never specifies how hooks (which run as standalone Python scripts via Claude Code) import `engram_core`. The current ticket plugin's hooks are self-contained scripts that don't import shared libraries. The `pyproject.toml` is mentioned but its `[project.scripts]` or entry points are not specified.

**U2. How `.engram-id` is committed on first use (Accidentally omitted)**
The spec says "generate UUIDv4, write to `.engram-id` at repo root, commit it." But committing requires staging and a commit message. Does Engram auto-commit? Does it stage and expect the user to commit? Does it add to `.gitignore` if uncommitted? What happens if the user is on a detached HEAD or in a rebase? What if the repo has a pre-commit hook that rejects the file?

**U3. What happens to existing handoff chain state during migration (Accidentally omitted)**
Chain state files have 24-hour TTL and live at `~/.claude/.session-state/handoff-<UUID>`. The spec migrates handoffs to `~/.claude/engram/<repo_id>/chain/` but doesn't specify what happens to active chain state from a session that was saved before migration and loaded after. A user who runs `/save` on the old system and `/load` on the new system will have a broken chain.

**U4. The `curate` interaction model (Intentional deferral with consequences)**
The spec describes `/curate` mechanics (sort by durability, show snippet/source/classification, user selects, publish) but doesn't specify the interaction flow. Is it a single prompt showing all candidates? Paginated? Does it show diffs against existing published knowledge? For a backlog of 50 candidates, the UX matters enormously.

**U5. How `worktree_id` derivation handles worktree creation/deletion (Accidentally omitted)**
The spec says worktree_id is "derived from `git rev-parse --git-dir`" and "hashed to a short stable ID." But when a worktree is created, used for work, deleted, and recreated at the same path, does the worktree_id stay stable (path-based) or change (git-dir-based)? If path-based, worktree reuse inherits old context. If git-dir-based, context is orphaned when the worktree is recreated.

**U6. Ledger event schema (Intentional deferral with consequences)**
The ledger is described as "architecturally optional, operationally default-on" and records "events for debugging and diagnostics." But the event schema is never defined. What events are logged? What fields? Without a schema, the ledger becomes an unstructured append log that's hard to query and easy to break.

**U7. How `engram_guard` determines "engine entrypoints only" (Accidentally omitted)**
The guard allows mutations from "engine entrypoints only" but doesn't specify how it identifies engine-originated writes versus direct writes. The ticket plugin's guard detects `ticket_engine_*.py` script invocations in Bash commands. Does the Engram guard do the same pattern matching? What about Write/Edit tool calls from within skills that are supposed to go through engines?

---

### 5. Opportunity Cost

**What we're ruling out:**

1. **Incremental improvement of existing plugins.** Adding `repo_id` to handoff, adding cross-plugin search as a standalone skill, and adding staging to the learning pipeline would capture ~70% of Engram's value without the migration risk. This path becomes impractical once Engram consolidation begins (you can't improve old code while building its replacement).

2. **Independent evolution speed.** Today, modifying tickets is a self-contained change to `packages/plugins/ticket/`. After Engram, every ticket change potentially touches `engram_core`, `engram_guard`, and cross-subsystem tests. The ticket plugin's 596 tests run in isolation today; post-Engram, they're part of a larger test suite with shared dependencies.

3. **Plugin composition.** The three-plugin model lets users install what they need. A team that wants tickets but not handoffs can use just the ticket plugin. Engram bundles all three — you get everything or nothing.

**Alternative dismissed too quickly:**

**Shared identity library + thin integration layer.** Instead of one plugin, ship `engram_core` as a shared library and add `RecordRef`-based cross-references to the existing plugins. Each plugin registers a NativeReader. A new "engram-search" plugin provides `/search` and `/timeline` by querying readers across installed plugins. This preserves independent deployment, independent testing, and independent evolution while still providing the identity and cross-subsystem query that the spec rightly identifies as valuable. Its strongest advantage: zero data migration, because the storage locations don't change.

---

### 6. Second-Order Effects

**Dependencies created:**
- All three subsystems now depend on `engram_core` (identity, types, reader protocol). A bug in `identity.py` breaks all three.
- The `engram_guard` hook becomes a single point of enforcement for all subsystem writes. If the guard has a bug, all protection fails simultaneously.
- Every skill must be tested with the full Engram infrastructure, not just its own subsystem.

**Maintenance burden:**
- One plugin with 12 skills, 4 hooks, 3 engines, 3 readers, a core library, and a migration harness is significantly more complex to maintain than three focused plugins. The spec's success criteria require 20 verification items.
- The compatibility harness for the Work subsystem is itself a significant artifact that must be maintained during migration and can be deleted after — but "after" is undefined if behavioral equivalence questions arise months later.
- Envelope versioning (`envelope_version: "1.0"`) implies future versions. The version negotiation protocol (reject unknown versions with `VERSION_UNSUPPORTED`) means that upgrading envelope formats requires coordinating across all subsystems simultaneously.

**Behavioral effects:**
- **Coupling incentive:** With all subsystems in one plugin, the path of least resistance is to add cross-subsystem features (e.g., "auto-defer on save," "auto-distill on save") that the spec explicitly defers but the architecture makes trivial. The spec says "no reactive pipelines" but `/save` already orchestrates defer + distill — the line between "orchestration" and "reactive pipeline" will blur.
- **Testing gravity:** The 950+ combined tests will exert pressure toward integration testing over unit testing, because it's easier to test the whole system than to mock the boundaries between subsystems. This makes tests slower and more brittle.
- **Ownership ambiguity:** When a bug appears in `/triage` (cross-subsystem), is it a Context issue, a Work issue, or an Engram issue? With three plugins, ownership was clear. With one plugin, every cross-subsystem bug requires understanding the full system.

---

### 7. Severity Ranking

| ID | Issue | Source | Severity |
|----|-------|--------|----------|
| A1 | "Same underlying problem" framing may not hold as subsystems diverge | §2 Assumptions | [moderate] |
| A2 | Fresh-scan indexing won't scale beyond MVP file counts | §2 Assumptions | [moderate] |
| A3 | `engram_core` import path from hooks unspecified and potentially fragile | §2 Assumptions | [serious] |
| A4 | Ticket pipeline behavioral transplant risk due to execution context differences | §2 Assumptions | [serious] |
| A5 | Existing handoff data migration has unaddressed edge cases | §2 Assumptions | [moderate] |
| A6 | Bash protection in success criteria despite acknowledged best-effort limitation | §2 Assumptions | [minor] |
| F1 | Compatibility harness test triage based on subjective judgment | §3 Failure Modes | [serious] |
| F2 | `/save` partial failure UX is confusing | §3 Failure Modes | [minor] |
| F3 | Knowledge staging accumulation without TTL or size cap | §3 Failure Modes | [moderate] |
| F4 | Shadow authority via `snippet` in skill reasoning | §3 Failure Modes | [serious] |
| U1 | `engram_core` importability from all execution contexts | §4 Underspec | [serious] — Blocks Step 0 if wrong |
| U2 | `.engram-id` first-use commit mechanics | §4 Underspec | [moderate] |
| U3 | Active chain state during migration | §4 Underspec | [moderate] |
| U4 | `/curate` interaction model at scale | §4 Underspec | [minor] |
| U5 | `worktree_id` stability across worktree lifecycle | §4 Underspec | [moderate] |
| U6 | Ledger event schema undefined | §4 Underspec | [minor] |
| U7 | Guard "engine entrypoints only" detection mechanism | §4 Underspec | [serious] — Enforcement is hollow without this |
| OC1 | Incremental improvement path foreclosed | §5 Opportunity Cost | [moderate] |
| OC2 | Shared library alternative dismissed without evaluation | §5 Opportunity Cost | [serious] — Achieves ~70% of value without migration risk; several [serious] issues (A4, F1, U3) become avoidable under this alternative |
| SE1 | Single point of failure in `engram_core` and `engram_guard` | §6 Second-Order | [moderate] |
| SE2 | Coupling incentive toward reactive pipelines | §6 Second-Order | [minor] |
| SE3 | Testing gravity toward integration over unit testing | §6 Second-Order | [minor] |
| SE4 | Ownership ambiguity for cross-subsystem bugs | §6 Second-Order | [minor] |

**Summary:** No `[fatal]` issues — the approach is fundamentally sound and the spec is unusually thorough. Six `[serious]` issues cluster around three themes: (1) the importability and enforcement mechanisms of the shared infrastructure (A3, U1, U7) are underspecified in ways that could block implementation, (2) the ticket pipeline transplant (A4, F1) carries silent regression risk that the compatibility harness may not fully catch, and (3) a viable alternative (shared identity library + thin integration layer, OC2) that avoids several migration-related [serious] issues hasn't been explicitly evaluated and rejected. Themes 1 and 2 should be resolved before implementation begins. Theme 3 deserves a design decision with documented rationale — the spec should either adopt the alternative or explain why full consolidation is worth the migration cost that the lighter approach avoids.
