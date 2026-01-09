# How to author + review `SKILL.md` bodies (one-pager)

This is a **single, repeatable workflow** that unifies:

- **Strict structure + safety** (the pass/fail contract and fail codes).
- **Semantic quality** (avoid “compliant but useless”).
- **Category guidance** (what to emphasize for the dominant failure mode).
- **Domain annexes** (local-repo invariants for meta/audit/pipeline).

---

## Author workflow (10–20 minutes, deterministic)

### 1) Route the skill

1. Pick a **category** by dominant failure mode (use the categories guide decision tree).
2. Pick a **risk tier** (low / medium / high). If uncertain, **round up**.
3. If you’re in a **local repo** context and category is:
   - `category=meta-skills` / `category=auditing-assessment` / `category=agentic-pipelines`
     then **apply the local-repo domain annex** for canonical invariants + verification menus.

**Output of this step:**

- `Category: category=<id>`
- `Risk posture: <low|medium|high> (why)`
- `Domain: local-repo (if applicable)`

### 2) Draft using the strict skeleton (do not improvise structure)

Write the body so a reviewer can find these **8 content areas** quickly:

1. When to use
2. When NOT to use
3. Inputs
4. Outputs (Artifacts + Definition of Done)
5. Procedure (numbered)
6. Decision points (≥2 “If … then … otherwise …”)
7. Verification (≥1 quick check with expected result shape)
8. Troubleshooting (≥1 failure mode: symptoms/causes/next step)

### 3) Add semantic precision (minimum viable semantics)

Add a small “semantic contract” block near the top:

```text
Semantic contract:
- Primary goal: <1 sentence>
- Non-goals: <3–6 bullets>
- Hard constraints: <e.g., no network, no new deps, no breaking changes>
- Acceptance signals: <2–4 observable success signals>
- Risk posture: <low/medium/high> and why
```

This prevents scope creep + verification theater.

### 4) Encode safety gates explicitly

- Include at least one **STOP** step for missing inputs/ambiguity.
- Add **ask-first** gates before any breaking/destructive/irreversible step.
- Any mentioned command must include **Expected result shape** and (when feasible) a **fallback** path if it can’t be run.

### 5) Write verification like you mean it

- **Quick check** measures the **primary success property**, not just “it compiles”.
- If checks can’t be run here, use: `Not run (reason): … Run: <cmd>. Expected: <pattern>.`

### 6) Run the linter (then fix strict FAILs first)

Run:

```bash
python skill_lint.py path/to/SKILL.md
```

Fix in this order:

1. Strict-spec FAIL codes (must-fix)
2. Manually apply semantic + category/domain guidance (quality + risk alignment)

---

## Reviewer workflow (5–10 minutes)

### 1) Run the linter

- If **any strict FAIL codes** → disposition is **FAIL** (must-fix).

### 2) Manual quick scan (only the deltas the linter can’t prove)

Check:

- The Definition of Done is _actually_ objective for the stated goal.
- Decision points are triggered by **observable signals**, not “judgment”.
- Risk tier is appropriate (if uncertain, require stricter gates).

### 3) Choose disposition (required)

- **PASS**: no strict FAIL codes; no meaningful manual review notes.
- **PASS-WITH-NOTES**: no strict FAIL codes; has fixable semantic/category issues (manual review; not emitted by the linter).
- **FAIL**: any strict FAIL code or safety gap.

### 4) Review comment format (copy/paste)

```text
Disposition: <PASS | PASS-WITH-NOTES | FAIL>

Strict-spec:
- FAIL.<code>: <what’s missing / where to look>

Notes (semantic/category/domain; manual review only):
- <note bullets>
```

---

## CI recommendation (minimal + reversible)

- Default CI: **fail only on strict FAIL codes**.
- Optional stricter mode: fail on notes too (for high-risk categories).
