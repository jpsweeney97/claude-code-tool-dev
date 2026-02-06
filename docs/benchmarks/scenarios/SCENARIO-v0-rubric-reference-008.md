# v0-rubric-reference-008: Answer using only local sources and cite exact file paths

```yaml
id: v0-rubric-reference-008
title: Answer using only local sources and cite exact file paths
skill_target: Demonstrate reference-skill behavior (source lookup + constrained claims) without web access
skill_type: reference
task_type: research
oracle_type: rubric_blinded
allowed_tools_expectation: no_web
success_criteria:
  - Claims about repo content cite the exact file paths used (no invented sources)
  - Distinguishes "observed in files" vs "inference"
  - Does not use web browsing
failure_modes_to_watch:
  - Hallucinated repo facts
  - Vague citations ("the docs say…") without paths
inputs:
  prompt: |
    Using only local repository files (no web), answer:

    1) What are the two canonical files that define benchmark control bodies and synthetic benchmark skill bodies?
    2) Where is the standardized injection slot heading for injected skills defined, and what is the exact heading text?

    Requirements:
    - Cite exact file paths for each answer.
    - If you infer anything not explicitly stated, label it as inference.
notes:
  - This is a reference-skill benchmark: it tests retrieval discipline and citation specificity, not "writing quality."
```
