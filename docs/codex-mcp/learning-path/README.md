# Codex MCP Learning Path (Clueless → Expert)

**Purpose:** A structured progression from zero familiarity to production-ready proficiency with Codex MCP.  
**Audience:** Engineers, technical PMs, platform owners, and AI tool builders.

> **Navigation note:** Start with `/Users/jp/Projects/active/claude-code-tool-dev/docs/codex-mcp/codex-mcp-master-guide.md` if you want a single-document path. Use this learning path when you prefer staged modules, checkpoints, and guided progression.

---

## Outcomes

By the end of this path, a learner can:

1. Explain Codex MCP architecture and tool contracts.
2. Launch and validate `codex mcp-server` end to end.
3. Diagnose and recover common failure modes.
4. Build high-quality consultation briefs and follow-ups.
5. Operate a secure, observable, policy-compliant deployment.

---

## Prerequisites

- Basic terminal comfort.
- Ability to edit JSON/YAML configs.
- Familiarity with API keys and environment variables.

---

## Learning Stages

| Stage | Target Skill Level | Required Module(s) | Time Estimate |
|---|---|---|---|
| 0 | Conceptual orientation | `01-codex-mcp-concepts.md` | 45–60 min |
| 1 | First working integration | `02-first-success-30-min.md` | 30–45 min |
| 2 | Failure recovery confidence | `03-common-failures-lab.md` | 60–90 min |
| 3 | Applied implementation patterns | `../cookbooks/client-integration-recipes.md`, `../cookbooks/prompt-briefing-patterns.md` | 90–150 min |
| 4 | Operations + security readiness | `../runbooks/codex-mcp-operations.md`, `../security/codex-mcp-threat-model.md` | 90–120 min |
| 5 | Capability benchmarking | `../assessments/codex-mcp-skill-maturity-model.md`, `../faq/codex-mcp-faq.md` | 60–90 min |

---

## Suggested Sequence

1. Read concepts doc once without taking notes.
2. Complete first-success tutorial exactly as written.
3. Run all failure labs and record evidence.
4. Implement one cookbook recipe in your own environment.
5. Review runbook + threat model before broader rollout.
6. Score yourself with maturity model and set next targets.

---

## Evidence Checklist (Required for “Expert” Claim)

- Successful `codex` and `codex-reply` calls with preserved `threadId`.
- At least three failure-mode recoveries demonstrated.
- Documented sandbox/approval policy defaults.
- Secret-safe logs and troubleshooting process validated.
- Mature score target reached in the skill maturity model.

---

## Related Docs

- `../references/codex-mcp-server-beginner-to-expert.md`
- `../specs/2026-02-09-codex-consultation-skill-implementation-spec.md`
- `../specs/2026-02-09-codex-mcp-server-build-spec.md`
