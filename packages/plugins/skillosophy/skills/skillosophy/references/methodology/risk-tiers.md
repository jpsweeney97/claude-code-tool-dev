# Risk Tier Guide

## Tier Selection Criteria

| Tier | Characteristics | Examples |
|------|-----------------|----------|
| **Low** | Read-only, no external deps, trivial/reversible | Documentation, exploration, analysis |
| **Medium** | Writes files/config, bounded and reversible | Code generation, config changes, test writing |
| **High** | Security, ops, data, deps, public contracts, costly to reverse | Deployments, migrations, auth changes, API changes |

## Auto-Escalation Rule

**If ANY mutating action detected -> treat as High until gating verified**

Mutating actions include:
- File writes, deletes
- Deployments
- Database changes
- Force operations (git push --force)
- External API calls with side effects

## Gating Validation for Downgrade

A skill with mutating actions MAY be treated as Medium ONLY IF ALL of:

1. **Ask-first gates exist** for every mutating step in Procedure
2. **Scope is bounded and reversible** (explicit scope fence)
3. **Category justifies Medium** (typical risk is Medium or lower)

## Validation Matrix

| Condition | Gating Required | Allowed Tiers |
|-----------|-----------------|---------------|
| No mutating actions | None | Low, Medium, High |
| Mutating + all gates + bounded | Full gating | Medium, High |
| Mutating + missing any gate | Incomplete | High only |
| Touches security/data/ops | Domain risk | High only |

## Tier-Specific Minimum Requirements

| Requirement | Low | Medium | High |
|-------------|-----|--------|------|
| All 8 sections | Y | Y | Y |
| 1 quick check | Y | Y | Y |
| 1 troubleshooting entry | Y | Y | Y |
| 1 STOP/ask (missing inputs) | Y | Y | Y |
| STOP/ask (ambiguity) | - | Y | Y |
| Explicit non-goals (>=3) | - | Y | Y |
| 2nd verification mode | - | SHOULD | Y |
| Ask-first gates | - | - | Y |
| >=2 STOP/ask gates | - | - | Y |
| Rollback/escape guidance | - | - | Y |

## User Override Handling

**If user requests downgrade from High to Medium:**

1. Check gating validation (all 3 criteria above)
2. If passes: Allow, log "Downgraded to Medium - gating validated"
3. If fails: Block, show "Cannot downgrade: [specific missing gate]"
4. User may NOT downgrade to Low if any mutating actions exist
