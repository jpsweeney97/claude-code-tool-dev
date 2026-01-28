# Type Example: Capability Skills

**Load this reference when:** brainstorming-skills identifies the skill type as Capability.

## Core Question

**Can Claude do the thing?**

Capability skills enable Claude to do something it couldn't do before (or couldn't do well). The failure mode is no improvement over baseline — the skill adds information but doesn't enable new abilities.

## Type Indicators

Your skill is Capability if it:
- Teaches domain knowledge (Kubernetes, tax law, specific frameworks)
- Enables tool usage patterns Claude doesn't know
- Fills a knowledge gap that prevents task completion
- Would let Claude succeed where it previously failed

## The Capability Test

A Capability skill must pass this test:
1. **Without the skill:** Claude fails or produces poor results
2. **With the skill:** Claude succeeds or produces good results

If Claude could already do it, the skill is unnecessary. If Claude still can't do it with the skill, the skill is ineffective.

## Section Guidance

### Process Section

**Use domain knowledge structure.** Organize the capability around:
- Core concepts needed
- Common patterns/solutions
- Edge cases and gotchas

**Example (Kubernetes troubleshooting):**

```markdown
## Process

When troubleshooting Kubernetes issues, follow this diagnostic sequence:

**1. Pod Status Check**
```bash
kubectl get pods -n <namespace>
kubectl describe pod <pod-name> -n <namespace>
```
Look for: CrashLoopBackOff, ImagePullBackOff, Pending, Error

**2. Log Analysis**
```bash
kubectl logs <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace> --previous  # if crashed
```

**3. Event Timeline**
```bash
kubectl get events -n <namespace> --sort-by='.lastTimestamp'
```

**4. Resource Verification**
- Service exists and selects correct pods?
- ConfigMaps/Secrets mounted correctly?
- Resource limits causing OOM?

**5. Network Debugging**
- DNS resolution working? (`kubectl exec -it <pod> -- nslookup <service>`)
- NetworkPolicy blocking traffic?
- Service endpoints populated? (`kubectl get endpoints <service>`)
```

**Anti-pattern:** Just listing commands without explaining when to use each or how to interpret output.

### Decision Points Section

Focus on **diagnostic branching** — what to check based on what you find:

**Example:**

```markdown
## Decision Points

**Based on pod status:**
- CrashLoopBackOff → Check logs for application error, then check resource limits
- ImagePullBackOff → Check image name, registry credentials, network access
- Pending → Check node resources, node selectors, taints/tolerations
- Running but not working → Check service configuration, network policies

**Based on log output:**
- "Connection refused" → Target service not running or wrong port
- "Permission denied" → RBAC issue or filesystem permissions
- "OOMKilled" → Increase memory limits or fix memory leak
- No useful logs → Check if app logs to stdout, try `--previous` flag

**When stuck:**
- If standard checks reveal nothing → Compare working vs broken deployment YAMLs
- If intermittent → Check resource contention, look for patterns in timing
```

### Examples Section

Show **task success/failure comparison**:
- Before: Claude attempts task, fails or produces poor result
- After: Claude with skill succeeds

**Example:**

```markdown
## Examples

**Scenario:** Pod stuck in CrashLoopBackOff, logs show "connection refused to database:5432"

**Before** (without skill):
Claude suggests: "The database connection is failing. Check if the database is running and the connection string is correct."

This is vague and doesn't leverage Kubernetes-specific diagnostic approaches. User still doesn't know what to do.

**After** (with skill):
Claude follows the diagnostic sequence:

1. Check database pod: `kubectl get pods -l app=database`
   → Database pod is Running

2. Check database service: `kubectl get svc database`
   → Service exists, port 5432

3. Check endpoints: `kubectl get endpoints database`
   → **No endpoints!** Service selector doesn't match pod labels

4. Compare service selector with pod labels:
   - Service: `app: database`
   - Pod: `app: postgres`  ← Mismatch!

Root cause identified: Service selector doesn't match pod labels.
Fix: Update service selector or pod labels to match.
```

### Anti-Patterns Section

Focus on **incomplete knowledge application**:

**Example:**

```markdown
## Anti-Patterns

**Pattern:** Listing commands without interpretation
**Why it fails:** User can run commands but doesn't know what output means or what to do next.
**Fix:** For each command, explain what to look for in output and what different results mean.

**Pattern:** Covering happy path only
**Why it fails:** Real issues are edge cases. Skill that only works when everything is normal isn't useful.
**Fix:** Include the weird cases — intermittent failures, misleading symptoms, multiple simultaneous issues.

**Pattern:** Domain knowledge without prioritization
**Why it fails:** User drowns in information. "Here are 20 things that could be wrong" isn't helpful.
**Fix:** Structure as diagnostic tree — start with most common causes, branch based on findings.
```

### Troubleshooting Section

Address **capability gaps**:

**Example:**

```markdown
## Troubleshooting

**Symptom:** Claude follows the skill but still can't solve the problem
**Cause:** The specific issue isn't covered by the skill's knowledge
**Next steps:** Skill may need expansion. Document the gap and add coverage.

**Symptom:** Claude has the knowledge but doesn't apply it
**Cause:** Skill isn't triggered, or Claude doesn't recognize when to use it
**Next steps:** Check triggers/when-to-use. Add more specific activation conditions.

**Symptom:** Claude applies knowledge incorrectly
**Cause:** Skill knowledge is ambiguous or context-dependent rules aren't clear
**Next steps:** Add more Decision Points to clarify when each piece of knowledge applies.
```

## Testing This Type

Capability skills need **baseline failure demonstration**:

1. **Baseline test:** Give Claude the task without the skill — document the failure
2. **Capability test:** Same task with skill — verify success
3. **Edge case test:** Unusual scenarios — does the capability extend?
4. **Metrics:** Task success rate with vs without skill

See `type-specific-testing.md` → Type 3: Capability Skills for scenario templates.

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Skill for something Claude already knows | No value added | Test baseline first — only build skill if Claude fails |
| Knowledge dump without structure | Information overload | Organize as diagnostic tree or decision framework |
| No edge cases | Fails on real problems | Include gotchas, weird cases, common misdiagnoses |
| Commands without interpretation | User can't act on output | Explain what each result means and what to do next |
