# Compatibility Checklist

Verification checklist for "complementary" items in Phase 4. Prevents combining items that seem independent but conflict at runtime.

---

## When to Use

Before combining any items classified as "Complementary" in conflict detection.

---

## The Five Checks

### 1. Dependency Compatibility

```markdown
[ ] List dependencies of Item A: ____
[ ] List dependencies of Item B: ____
[ ] Check for version conflicts: ____
[ ] Check for mutually exclusive dependencies: ____
```

| Result | Action |
|--------|--------|
| No conflicts | Pass ✅ |
| Version mismatch | Attempt resolution, else Fail ❌ |
| Mutually exclusive | Fail ❌ — reclassify as Incompatible |

---

### 2. File Modification Overlap

```markdown
[ ] Files modified by Item A: ____
[ ] Files modified by Item B: ____
[ ] Overlapping files: ____
[ ] Nature of overlap: [additive / conflicting]
```

| Result | Action |
|--------|--------|
| No overlap | Pass ✅ |
| Additive overlap | Pass ✅ (both add to same file without conflict) |
| Conflicting overlap | Fail ❌ — reclassify as Direct conflict |

---

### 3. Convention Alignment

```markdown
[ ] Naming conventions in A: ____
[ ] Naming conventions in B: ____
[ ] Compatible? ____

[ ] File structure assumptions in A: ____
[ ] File structure assumptions in B: ____
[ ] Compatible? ____

[ ] Configuration format in A: ____
[ ] Configuration format in B: ____
[ ] Compatible? ____
```

| Result | Action |
|--------|--------|
| Conventions align | Pass ✅ |
| Conventions independent | Pass ✅ |
| Conventions conflict | Fail ❌ — reclassify as Philosophical conflict |

---

### 4. Runtime Interaction

```markdown
[ ] Does A assume exclusive access to any resource? ____
[ ] Does B assume exclusive access to any resource? ____
[ ] Could A's behavior affect B's behavior? ____
[ ] Could B's behavior affect A's behavior? ____
[ ] Potential interference identified: ____
```

| Result | Action |
|--------|--------|
| Independent execution | Pass ✅ |
| Potential interference | Investigate further |
| Confirmed interference | Fail ❌ — reclassify as Incompatible |

---

### 5. Dry-Run Test (Deep calibration only)

```markdown
[ ] Install A alone: works? ____
[ ] Install B alone: works? ____
[ ] Install A + B together: works? ____
[ ] Test interaction scenarios: ____
[ ] Issues found: ____
```

| Result | Action |
|--------|--------|
| All tests pass | Pass ✅ |
| Combined installation fails | Fail ❌ |
| Interaction issues | Document and assess severity |

---

## Outcome Summary

| All Checks | Verdict | Next Step |
|------------|---------|-----------|
| All pass | **Compatible** | Proceed with combination |
| Any fail | **Incompatible** | Reclassify, resolve via conflict protocol |
| Unable to verify | **Uncertain** | Mark confidence as Possible, note in Limitations |

---

## Output Format

```markdown
### Compatibility Verification: [Item A] + [Item B]

| Check | Result | Notes |
|-------|--------|-------|
| Dependencies | ✅/❌ | [details] |
| File overlap | ✅/❌ | [details] |
| Conventions | ✅/❌ | [details] |
| Runtime | ✅/❌ | [details] |
| Dry-run | ✅/❌/N/A | [details] |

**Verdict:** [Compatible / Incompatible / Uncertain]
**Confidence:** [Certain / Probable / Possible]
**Notes:** [any additional context]
```
