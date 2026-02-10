# Codex MCP Skill Maturity Model

**Purpose:** Assess learner/team capability from novice to expert.  
**Audience:** Team leads, platform owners, and learners tracking progression.

---

## Dimensions

Score each dimension independently:

1. Conceptual understanding
2. Integration execution
3. Failure diagnosis and recovery
4. Security and policy discipline
5. Operations and observability
6. Coaching and reuse (ability to teach others)

---

## Maturity Levels

| Level | Name | Profile |
|---|---|---|
| 0 | Unaware | No working mental model or setup |
| 1 | Beginner | Can run basic setup with guidance |
| 2 | Practitioner | Can run/continue consultations independently |
| 3 | Advanced Practitioner | Handles common failures and applies guardrails |
| 4 | Operator | Owns reliable team deployment with runbooks |
| 5 | Expert | Improves system design, mentors others, drives standards |

---

## Level Criteria by Dimension

### Level 1 → 2 gate

- Demonstrates successful `codex` + `codex-reply` flow.
- Correctly manages `threadId` continuity.

### Level 2 → 3 gate

- Diagnoses and recovers from at least three common failure modes.
- Applies secure defaults without prompting.

### Level 3 → 4 gate

- Operates runbook procedures during simulated incident.
- Uses structured telemetry to support diagnosis.

### Level 4 → 5 gate

- Creates reusable integration pattern for team.
- Reviews and improves threat model/runbook quality.

---

## Scoring Rubric

Use 0–4 for each dimension:

- 0 = no evidence
- 1 = assisted performance only
- 2 = independent basic execution
- 3 = reliable under common variance
- 4 = teaches, improves, and institutionalizes

**Overall maturity suggestion:**

- Average < 1.5: Level 1
- 1.5–2.4: Level 2
- 2.5–3.1: Level 3
- 3.2–3.7: Level 4
- 3.8+: Level 5

---

## Evidence Requirements

Minimum evidence bundle:

1. Setup transcript and successful tool calls.
2. Failure-lab records with diagnosis/recovery.
3. Security checklist completion.
4. Runbook exercise notes.
5. One artifact contributed back (guide, recipe, checklist, or improvement proposal).

---

## 30/60/90 Day Development Plan Template

### First 30 days

- Complete learning path modules 01–03.
- Demonstrate first independent integration.

### 60 days

- Handle failure drills and produce recovery notes.
- Contribute one cookbook adaptation for local team context.

### 90 days

- Participate in operational simulation.
- Co-own one improvement in security or observability posture.

