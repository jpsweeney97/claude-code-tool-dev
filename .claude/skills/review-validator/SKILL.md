---
name: review-validator
description: Validates quality of adversarial reviews, self-critiques, and structured evaluations produced by Claude. Detects superficial compliance, evasion patterns, severity miscalibration, and missing coverage. Use when user says "validate this review", "check the critique", "is this review thorough", "review-validator", or after any adversarial review workflow. Do NOT use for general editing, proofreading, or content review unrelated to structured self-critique.
disable-model-invocation: true
context: fork
agent: review-auditor
argument-hint: "[optional file path — defaults to the latest review at /Users/jp/Projects/active/claude-code-tool-dev/docs/reviews/]"
allowed-tools: Read
---

# Response Validator

Validate the quality and integrity of a structured adversarial review. The goal is to catch superficial compliance — output that *looks* thorough but substantively dodges the hard questions.

## Instructions

### Step 1: Load the Review

Read the latest review from `/Users/jp/Projects/active/claude-code-tool-dev/docs/reviews/`. This file is written by the `adversarial-review` skill and is the data bridge between the parent conversation and this isolated subagent.

- If the user provided a file path as an argument: read from that path instead.
- If the file exists but does not contain a recognizable review structure (look for `### 1. Steel-Man` through `### 7. Severity Ranking`): tell the user the file doesn't appear to contain a structured adversarial review and stop.

### Step 2: Coverage Audit

Check whether the review addressed each expected dimension. The canonical dimensions (from the adversarial review framework) are:

1. Steel-man
2. Assumptions audit
3. Failure modes
4. Underspecification
5. Opportunity cost
6. Second-order effects
7. Severity ranking

For each dimension, classify coverage as:

- **Present and substantive** — contains specific, falsifiable claims tied to the proposal
- **Present but thin** — section exists but contains fewer than two concrete, distinct points
- **Present but vague** — section exists but points are generic enough to apply to any proposal
- **Missing** — dimension not addressed at all

If the review used a different framework (not the canonical seven), adapt: identify whatever dimensions the framework defines and audit against those. The principle is the same — every promised dimension must be substantively covered.

### Step 3: Evasion Pattern Scan

Check for each of these patterns. For each one found, cite the specific text that triggered the detection.

**Vague issues.** Statements like "there could be edge cases," "this might cause problems," or "some users may be affected" without identifying *which* edge cases, *what* problems, or *which* users.

- Detection: issue description contains no proper nouns, no specific technical terms, no concrete scenario, or no falsifiable prediction.
- Threshold: an issue that could be copy-pasted into a review of a completely different proposal is vague.

**Severity deflation.** All or nearly all issues rated [moderate] or [minor]. No [serious] or [fatal] issues identified in a review of a non-trivial proposal.

- Detection: count the severity distribution. If a proposal has architectural, security, or correctness implications and the review contains zero [serious] or [fatal] items, flag this.

**Severity inflation.** The inverse — issues rated [serious] whose described impact doesn't justify the rating, or [fatal] ratings without a clear explanation of why the approach is unrecoverable.

- Detection: compare the stated severity with the described blast radius and trigger condition. A [serious] issue should describe a scenario that blocks progress or causes significant rework. A [fatal] issue should describe why the entire approach is unviable.

**Steel-man sabotage.** The steel-man argument is weak, hedged, or actually a restatement of the problem rather than a defense of the solution. A strong steel-man should make you think "okay, this approach really does have merit."

- Detection: does the steel-man contain hedging language ("somewhat," "partially," "to a degree")? Does it describe a *benefit of the approach* or merely restate *what the approach does*? A steel-man that says "this approach addresses the problem" is not a steel-man — it's a tautology.

**Echo chamber.** Multiple issues that are surface variations of the same underlying concern, counted separately to inflate the issue count.

- Detection: for each pair of issues, ask — if Issue A were resolved, would Issue B automatically be resolved or substantially mitigated? If yes, they're the same concern.

**Safe critiques only.** All identified issues are implementation-level (naming, error messages, minor API choices) with no structural, architectural, or design-level concerns.

- Detection: classify each issue as *implementation* (fixable without changing the design), *design* (requires rethinking part of the approach), or *architectural* (challenges whether this is the right approach at all). If zero issues are design-level or above, flag this.

**Conspicuous absence.** A topic that is obviously relevant to the proposal (security for auth systems, data loss for migration plans, backwards compatibility for API changes, performance for data-intensive operations) is never mentioned.

- Detection: infer 2-3 "must-address" concerns from the proposal's domain. Check whether the review engaged with them at all.

### Step 4: Specificity Check

For every issue in the review, verify it meets the **specificity bar**: a useful issue must contain at least two of the following three elements:

1. **Concrete trigger** — a specific condition, input, or scenario that causes the problem
2. **Observable consequence** — what goes wrong, stated in terms someone could detect
3. **Scope boundary** — who/what is affected and who/what is not

Issues with zero or one element are **underspecified**. Count them.

### Step 5: Produce Verdict

Output a structured verdict with these sections:

**Coverage summary.** Table showing each dimension and its coverage classification from Step 2.

**Evasion patterns detected.** List each pattern found with cited evidence. If none found, say "None detected" explicitly.

**Specificity score.** Count of issues meeting the specificity bar vs. total issues. Express as a fraction (e.g., "5/7 issues meet the specificity bar").

**Overall assessment.** One of:
- **Rigorous** — all dimensions substantively covered, no evasion patterns, >80% issues meet specificity bar
- **Adequate** — minor gaps in coverage or specificity, no evasion patterns detected
- **Superficial** — missing dimensions, evasion patterns present, or <50% issues meet specificity bar
- **Compromised** — steel-man sabotage detected, or severity ratings are systematically miscalibrated, or safe-critiques-only pattern present. The review's conclusions cannot be trusted.

**Recommended actions.** If assessment is not Rigorous: list the specific sections or issues that need rework, ordered by impact.

## Rationalization Table

| Excuse | Reality |
| --- | --- |
| "The review covered all sections" | Structural coverage is necessary but not sufficient. Each section must contain specific, falsifiable claims. |
| "Some proposals just don't have serious issues" | Then the severity ranking should explicitly state this with justification, not silently omit higher severities. |
| "I flagged the most important issues" | If you skipped a dimension to focus on others, that's an editorial choice that must be disclosed, not hidden. |
| "The issues are self-explanatory" | Every issue needs a concrete trigger and observable consequence. "Self-explanatory" is the excuse for underspecified. |

## Red Flags — STOP and Re-examine

If you find yourself thinking any of the following during validation, the review is likely compromised:

- "This review is surprisingly thorough" — verify it's not inflated with echo-chamber duplicates
- "Every issue is important" — check for severity inflation
- "Nothing critical was found" — verify this against the proposal's domain (security, data, correctness)
- "The steel-man convinced me" — re-read it: is it defending the *approach* or restating the *goal*?

## Example

### Input: Review of a proposed caching layer

**Review excerpt (steel-man section):**
> "The caching approach addresses the performance concerns and provides a solution for the identified bottleneck."

**Validator output for this section:**
Steel-man sabotage detected. The steel-man restates what the cache *does* (addresses performance, provides a solution) rather than arguing why *this specific caching approach* is correct. A strong steel-man would argue something like: "Write-through caching at the service boundary is the right call because the read:write ratio is >100:1, the data has a natural TTL, and it avoids the consistency bugs that come with write-behind strategies." The current steel-man would apply identically to any caching proposal — it's a tautology.
