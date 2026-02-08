# Blinded Evaluation (Full Blindness) — Option 1

This folder implements **Option 1: condition-free alias packet** for fully blinded rubric scoring.

## Files

- `blinded_eval_packet.md`
  - What to share with the blinded evaluator.
  - Contains condition-free candidate IDs and extracted rubric-run `## Output` sections only.
  - Condition words are redacted to `[REDACTED_CONDITION]`.
  - Specific injected-body tokens are redacted to `BENCH_[REDACTED]` / `CONTROL_[REDACTED]` when they appear in the extracted output.

- `blinded_eval_mapping_private.md`
  - **Private.** Do not share with the blinded evaluator.
  - Maps candidate IDs back to the true run-record files for aggregation/deltas.

## How to regenerate (recommended)

Use the script:

```bash
./scripts/blinded_eval_packet.py --run-id 2026-02-06_benchmark-v0_initial
```

This generates a packet that includes:
- per-scenario “Task + Criteria” (authoritative YAML excerpt from the framework doc)
- candidate responses (extracted from each rubric run record’s `## Output` section)

## Verify blinding

```bash
./scripts/blinded_eval_packet.py --run-id 2026-02-06_benchmark-v0_initial --verify-only
```

## Blinding checks (recommended)

Before sharing `blinded_eval_packet.md`, confirm it contains no condition labels:

```bash
rg -n "\\b(baseline|target|placebo|proxy|harmful|control)\\b|__baseline__|__target__|__placebo__|__proxy|__harmful|__control" \
  docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/blinded_eval/blinded_eval_packet.md || true
```

Also confirm no non-redacted injected-body tokens leak through:

```bash
python - <<'PY'
from pathlib import Path
import re
p=Path("docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/blinded_eval/blinded_eval_packet.md")
t=p.read_text()
bench_leak=re.findall(r"\\bBENCH_(?!\\[REDACTED\\]|\\*)\\w+", t)
ctrl_leak=re.findall(r"\\bCONTROL_(?!\\[REDACTED\\])\\w+", t)
print("BENCH leaks:", bench_leak[:10])
print("CONTROL leaks:", ctrl_leak[:10])
PY
```
