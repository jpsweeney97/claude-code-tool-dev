# Scripts Reference

Automation tools for validation and synthesis.

## validate_output.py

Validates agent outputs before synthesis to catch malformed responses.

```bash
# Validate a single lens output
python scripts/validate_output.py adversarial agent1.md
python scripts/validate_output.py pragmatic agent2.md
python scripts/validate_output.py cost-benefit agent3.md

# Validate with JSON output
python scripts/validate_output.py adversarial agent1.md --json

# Quiet mode (errors only)
python scripts/validate_output.py pragmatic agent2.md -q
```

**Exit codes:** 0 = valid, 10 = validation failed

**What it checks:**

| Lens           | Required Structure                                          |
| -------------- | ----------------------------------------------------------- |
| adversarial    | Table: Vulnerability/Evidence/Attack Scenario/Severity      |
| pragmatic      | Sections: What Works/What's Missing/Friction Points/Verdict |
| cost-benefit   | Table: Element/Effort/Benefit/Verdict + ROI sections        |
| robustness     | Table: Gap/Evidence/Risk Scenario/Severity                  |
| minimalist     | Table: Element/Keep-Cut-Simplify/Rationale/Effort Saved     |
| capability     | Assumption/Reality/Evidence/Mitigation pairs                |
| implementation | Table: Capability Gaps + Works Today/Behavioral Risks/Verdict sections |
| arbiter        | Critical Path/Quick Wins/Defer tables + Verdict             |

## synthesize.py

Automates synthesis from 3 lens outputs, detecting convergent findings.

```bash
# Synthesize from 3 files (in lens order)
python scripts/synthesize.py adversarial.md pragmatic.md cost-benefit.md

# Specify target name for report header
python scripts/synthesize.py --target "CLAUDE.md" adv.md prag.md cb.md

# Design lens preset
python scripts/synthesize.py --design robustness.md minimalist.md capability.md

# Auto-detect lens types from content
python scripts/synthesize.py outputs/*.md --auto-detect

# Save to file
python scripts/synthesize.py *.md > synthesis.md

# JSON output for programmatic use
python scripts/synthesize.py *.md --json
```

**What it does:**

1. Extracts findings from each lens output (tables, sections)
2. Identifies convergent findings via keyword overlap
3. Separates lens-specific unique insights
4. Generates prioritized synthesis report

**Convergence detection:** Uses keyword overlap (Jaccard similarity >= 0.3 by default). Adjust with `--threshold 0.4` for stricter matching.

**Output:** Markdown synthesis report with:

- Convergent Findings (All 3 Lenses) table
- Convergent Findings (2 Lenses) table
- Lens-Specific Insights per lens
- Prioritized Recommendations with `[TODO]` placeholders

**Note:** Automated synthesis is a starting point. Review and refine the convergence detection manually for nuanced findings that keyword matching misses.

### Convergence Detection Limitations

The automated synthesis uses keyword overlap (Jaccard similarity) to detect convergent findings. This approach:

| Catches                          | Misses                                           |
| -------------------------------- | ------------------------------------------------ |
| Findings with shared terminology | Semantically similar findings stated differently |
| Explicit keyword matches         | Conceptually related issues using synonyms       |
| Direct overlaps                  | Higher-level pattern convergence                 |

**Recommendation:** Always review the synthesis output manually. If you see 0 convergent findings but the individual lens outputs seem related, the algorithm may have missed semantic overlap. Use the `--threshold` flag (default 0.3) to adjust sensitivity, or enable `--semantic-review` for LLM-assisted matching.

### Semantic Review

Keyword-based convergence detection (Jaccard similarity ≥0.3) misses semantically equivalent findings that use different vocabulary. The `--semantic-review` flag enables LLM-assisted matching.

```bash
# Enable semantic review (uses Haiku by default, ~$0.002-0.01 per synthesis)
python scripts/run_audit.py finalize *.md --target "X" --semantic-review

# Use Sonnet for higher accuracy (more expensive)
python scripts/run_audit.py finalize *.md --target "X" --semantic-review --semantic-model sonnet

# Limit pairs reviewed (cost control)
python scripts/run_audit.py finalize *.md --target "X" --semantic-review --max-pairs 10
```

**How it works:**

1. Generates candidate pairs from findings that failed keyword matching
2. Filters to pairs with shared file/element references
3. Sends pairs to Claude for semantic comparison
4. Merges confirmed matches into convergent findings

**When to use:**

- When no 3-lens convergence is detected automatically
- When findings describe the same element using different terms
- When vocabulary differs across lenses (e.g., "exploitable" vs "confusing")

**Cost:** ~$0.002-0.01 per synthesis using Haiku (default).

## run_audit.py

Pipeline orchestration script that combines preparation, validation, and synthesis into a complete workflow.

```bash
# Prepare: Generate prompts and cost estimate
python scripts/run_audit.py prepare path/to/target.md
python scripts/run_audit.py prepare target.md --preset design
python scripts/run_audit.py prepare target.md --output-dir ./audit_outputs

# Finalize: Validate outputs and synthesize
python scripts/run_audit.py finalize adversarial.md pragmatic.md cost-benefit.md --target "CLAUDE.md"
python scripts/run_audit.py finalize outputs/*.md --auto-detect --target "My Skill"

# Finalize with implementation spec output (for TodoWrite workflow)
python scripts/run_audit.py finalize outputs/*.md --target "Name" --impl-spec

# Finalize with semantic review (LLM-assisted matching)
python scripts/run_audit.py finalize outputs/*.md --target "Name" --semantic-review
python scripts/run_audit.py finalize outputs/*.md --target "Name" --semantic-review --semantic-model sonnet
python scripts/run_audit.py finalize outputs/*.md --target "Name" --semantic-review --max-pairs 10

# Status: Check audit progress
python scripts/run_audit.py status ./audit_outputs
```

**Subcommands:**

| Command                      | Action                                                           |
| ---------------------------- | ---------------------------------------------------------------- |
| `prepare <target>`           | Generate agent prompts, estimate cost, output Task tool template |
| `finalize <files>`           | Validate all outputs, synthesize if valid                        |
| `finalize <files> --impl-spec` | Output implementation spec instead of synthesis (for TodoWrite) |
| `finalize <files> --semantic-review` | Enable LLM-assisted semantic matching (finds keyword misses) |
| `status <dir>`               | Check which outputs exist and their validation status            |

**Prepare output includes:**

- Cost estimate (tokens, USD)
- Ready-to-use Task tool invocation template
- Prompt files (if `--output-dir` specified)

**Finalize workflow:**

1. Validates each lens output using `validate_output.py`
2. Reports validation summary to stderr
3. If >= 2 outputs pass, generates synthesis
4. Exits with code 10 if synthesis blocked by validation

**Exit codes:** 0 = success, 10 = validation failed, 11 = synthesis failed
