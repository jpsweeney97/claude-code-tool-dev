# Evidence Hierarchy

Evidence levels for synthesis decisions. Shared reference for all phases.

---

## Three Levels

| Level | Source | Trust | Use For |
|-------|--------|-------|---------|
| **Primary** | Direct observation | High | Final decisions |
| **Secondary** | Documentation, claims | Verify if possible | Supporting evidence |
| **Tertiary** | Inference, reputation | Contextual only | Tiebreakers |

---

## Primary Evidence

Evidence gathered by direct observation:

| Evidence | Example |
|----------|---------|
| Ran code, observed behavior | "Tested hook, caught 3 errors" |
| Inspected source directly | "Lines 45-67 implement validation" |
| Measured performance | "Response time: 50ms vs 120ms" |
| Verified test results | "All 47 tests pass" |

**Rule:** Primary evidence required for Certain confidence.

---

## Secondary Evidence

Evidence from documentation or claims:

| Evidence | Example |
|----------|---------|
| README states capability | "README claims 99% accuracy" |
| Comments describe intent | "Comment says 'handles edge case X'" |
| Changelog lists features | "v2.0 added error recovery" |
| Issue tracker discussions | "Issue #45 confirms this works" |

**Rule:** Verify against primary when possible. Secondary alone caps confidence at Probable.

---

## Tertiary Evidence

Evidence from inference or reputation:

| Evidence | Example |
|----------|---------|
| Star count | "12,000 GitHub stars" |
| Author reputation | "Created by well-known developer" |
| Community sentiment | "Highly recommended in forums" |
| Age/stability | "Stable for 3 years" |

**Rule:** Never use alone for decisions. Useful as tiebreaker when primary/secondary evidence is equal.

---

## Mapping to Confidence

| Evidence Basis | Maximum Confidence |
|----------------|-------------------|
| Primary + cross-reference | Certain |
| Primary alone | Probable |
| Secondary only | Probable (prefer Possible) |
| Tertiary only | Possible (consider excluding) |

---

## Documentation Format

When citing evidence:

```markdown
**Claim:** [what you're asserting]
**Evidence:** [what you observed]
**Level:** [Primary / Secondary / Tertiary]
**Source:** [file:line or specific reference]
```

---

## Usage

This hierarchy is used in:
- **Phase 3:** Value Identification (assessing quality evidence)
- **Phase 4:** Conflict Resolution (weighing competing approaches)
- **Deliverable:** Confidence labels for recommendations
