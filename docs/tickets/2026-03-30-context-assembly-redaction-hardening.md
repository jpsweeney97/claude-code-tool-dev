# T-20260330-01: Context assembly redaction hardening

```yaml
id: T-20260330-01
date: 2026-03-30
status: open
priority: medium
tags: [codex-collaboration, hardening, context-assembly, redaction]
blocked_by: []
blocks: []
effort: small
```

## Context

T3/T4 decision gate from the post-R2 hardening framework. Items 6 and 7 from the R1 carry-forward debt ticket (`T-20260327-01`) were assessed against shared context assembly paths.

Item 7 (non-UTF-8 file crash) was closed immediately as a standalone bugfix at `e6792de8`. Item 6 (redaction coverage) was promoted into this ticket as the next work packet.

## Problem

`_SECRET_PATTERNS` in `context_assembly.py` covers 4 pattern families: `sk-*`, `Bearer`, PEM blocks, and `key=value` assignments with 4 keywords. Common credential forms pass through unredacted into Codex prompts:

| Leaked form | Example | Risk |
|-------------|---------|------|
| AWS access keys | `AKIAIOSFODNN7EXAMPLE` | Bare prefix, no `key=` wrapper needed |
| GitHub tokens | `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` | Bare prefix |
| GitHub app tokens | `gho_*`, `github_pat_*` | Bare prefix |
| Basic auth headers | `Authorization: Basic dXNlcjpwYXNz` | Header form, not caught by `Bearer` pattern |
| URL-embedded credentials | `https://user:pass@host.com/path` | Userinfo in URL |

These affect the production consult path and the dialogue path equally — `context_assembly.py` is shared infrastructure.

## Scope

**In scope:**
- Port low-ambiguity prefix patterns to `_SECRET_PATTERNS`: `AKIA*`, `ghp_`, `gho_`, `ghs_`, `ghr_`, `github_pat_`
- Add `Authorization: Basic` header pattern (explicit header form only, not free-floating `basic` text)
- Add URL userinfo pattern (`://user:pass@`)
- Add false-positive regression tests against code-like content
- Close item 6 in carry-forward ticket `T-20260327-01`

**Explicitly out of scope:**
- Blind parity with `context-injection/redact.py` — that module is tuned for excerpt safety where over-redaction is acceptable. This path feeds the full Codex prompt where over-redaction loses meaningful content.
- Broader `_CREDENTIAL_RE` keyword expansion (14 keywords in `redact.py`) — evaluate only after prefix patterns land and false-positive impact is assessed.
- JWT detection — high false-positive risk in code content (base64-heavy strings).
- Shared redaction module extraction — acknowledged duplication, not worth the cross-package dependency for this scope.

## Internal precedent

`context-injection/redact.py` (`_JWT_RE` through `_CREDENTIAL_RE`) has battle-tested patterns for all of the above. Adapt, don't copy — the false-positive tolerance differs.

Key differences from `redact.py` context:
- `redact.py` operates on scout evidence snippets (small, targeted reads) — over-redaction is explicitly acceptable (see comment above `_JWT_RE`)
- `context_assembly.py` operates on the full Codex prompt — over-redaction means Codex can't see the code it needs to reason about
- Patterns must be tuned for code content: variable names, comments, documentation examples

## Acceptance criteria

- [ ] `AKIA*` bare keys redacted in assembled packets
- [ ] `ghp_`, `gho_`, `ghs_`, `ghr_`, `github_pat_` tokens redacted
- [ ] `Authorization: Basic` headers redacted
- [ ] URL userinfo (`://user:pass@host`) redacted
- [ ] False-positive regression: code containing `basic_auth_setup`, `basic_config`, and similar patterns NOT redacted
- [ ] False-positive regression: variable names like `ghp_enabled` or `akia_prefix` NOT redacted (short suffixes below token-length minimum)
- [ ] Existing 4-pattern coverage preserved (no regression in current tests)
- [ ] Item 6 marked closed in `T-20260327-01`

## Parked debt (not in scope)

**Unknown-handle policy (T2 Item B):** Chronically unreachable `unknown` handles retry every startup. Policy debt, not a correctness gap — retry is idempotent, handle namespace is small, spec acknowledges at `contracts.md:156`. No action until usage data shows meaningful accumulation or startup impact.

## References

| Resource | Location | Purpose |
|----------|----------|---------|
| Current patterns | `context_assembly.py` `_SECRET_PATTERNS` | Starting point |
| Internal precedent | `context-injection/redact.py` `_API_KEY_PREFIX_RE` through `_CREDENTIAL_RE` | Pattern reference (adapt, don't copy) |
| Secret taxonomy | `cross-model/scripts/secret_taxonomy.py` | Broader classification reference |
| R1 carry-forward ticket | `docs/tickets/2026-03-27-r1-carry-forward-debt.md` | Parent tracking artifact |
| Item 7 fix | `e6792de8` | Binary file hardening (closed) |
