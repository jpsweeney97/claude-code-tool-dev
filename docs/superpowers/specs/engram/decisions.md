---
module: decisions
status: active
normative: true
authority: decisions
---

# Decisions

## Named Risks

| Risk | Severity | Mitigation | Detection |
|---|---|---|---|
| **Shadow authority** | High | Engram indexes but never owns. No decisions from [IndexEntry](storage-and-indexing.md#indexentry). | Does any feature give a different answer via Engram vs. subsystem? |
| **God Skill on /save** | Medium | Thin orchestrator, no unique logic, same code paths. See [/save orchestration rules](skill-surface.md#save-orchestration-rules). | Does `/save` contain logic `/defer` or `/distill` don't share? |
| **Fingerprint drift** | Medium | `repo_id` is stored UUIDv4. Dedup uses content hashes, not paths. | Rename repo, clone elsewhere — dedup still works? |
| **Bash enforcement gap** | High | Bounded guarantee: Write/Edit direct mutations to protected paths are reliably blocked. Authorized engine Bash invocations are supported via [trust injection](enforcement.md#trust-injection). Arbitrary Bash writes may bypass the guard. Records created via Bash bypass have no trust triple, no audit trail, and no provenance guarantee. | Bash write to `engram/work/` bypasses guard? Created ticket has no `.audit/` entry? |
| **Fork-on-same-machine collision** | Low | Two forks sharing `.engram-id` use the same private root. `worktree_id` differentiates Context queries. Knowledge staging and ledger shards commingle but are operationally harmless at single-developer scale. Deliberate v1 trade-off. | Clone a fork locally, run `/curate` — see candidates from both? |
| **Staging accumulation** | Low | `/triage` reports pending. Cumulative [staging inbox cap](enforcement.md#staging-inbox-cap). `/curate` shows queue. Knowledge engine rejects whole batch when cap exceeded. | Staging directory file count over time. |
| **NativeReader latency** | Low | Fresh scan at MVP scale is fast. `git log` off hot path. | Query latency on repos with 500+ files. |
| **Concurrent worktree staging** | Medium | Staging files use content-addressed filenames with `O_CREAT | O_EXCL` atomic creation. Published learnings guarded by `fcntl.flock` on lockfile. Cross-worktree concurrency delegated to git merge. See [write concurrency](types.md#write-concurrency). | Two worktrees distill same snapshot concurrently — duplicate staging files? Same-worktree `/learn` + `/curate` concurrent — lost append? |
| **Chain protocol limitations** | Low | Three inherited limitations (resume-crash gap, archive-failure poisoning, state-file TTL race). Archive-failure resolved in v1 by archive-before-state-write ordering. See [known limitations](skill-surface.md#chain-protocol-known-limitations). | Session spans >24h, save has no `resumed_from`? |

## Open Questions

| Question | When to Resolve |
|---|---|
| What additional fields does IndexEntry need? | Step 0a implementation. Extend based on real query needs. |
| How many of 669 ticket tests are compatibility-critical? | Step 3. Triage before building harness. |

## Deferred Decisions

Explicitly not in v1. Each entry records what was deferred and why.

| Decision | Rationale |
|---|---|
| Three-tier storage (repo-local `.claude/engram/`) | Current two-root model sufficient. Add if multi-worktree pain materializes. |
| Individual knowledge files | Single `learnings.md` for MVP. Split when count warrants. |
| Manifest-based reader discovery | Three hardcoded readers is fine. YAGNI. |
| Incremental indexing | Fresh scan fast enough. Add if >200ms. |
| `auto_silent` autonomy mode | Deferred from ticket v1.1. Carry forward. |
| Reactive pipelines (auto-defer, auto-distill) | User-initiated for v1. Consider after usage patterns emerge. |
| Ledger compaction | Append-only grows indefinitely. Add when file size matters. |
| Cross-user timeline | Session-local only. Multi-user via `git log` is out of scope. |
| Bounded protected-path drift scan | PostToolUse Bash trigger comparing protected-root manifest before/after Bash execution. Would close the Bash enforcement gap for git-tracked paths. Not achievable without pre/post state comparison mechanism. |
| RecordRef subsystem/record_kind constraints | Validated at construction time in implementation, not schema-level Literal types. See SP-8. |
