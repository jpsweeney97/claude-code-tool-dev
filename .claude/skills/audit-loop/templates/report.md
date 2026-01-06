# Report Template

> **Note:** Report generation is now handled by `scripts/generate_report.py`.
>
> The Handlebars template has been replaced with Python string formatting
> for reliable, dependency-free report generation.

## Usage

```bash
# Generate to stdout
python scripts/generate_report.py <artifact>

# Save to dated file
python scripts/generate_report.py <artifact> --save
```

## Report Sections

1. **Header** — Artifact name, date, calibration, cycles
2. **Summary** — Finding counts by priority
3. **Scope** — Examined and excluded areas
4. **Findings** — Table and details
5. **Limitations** — Known blind spots
6. **Counter-Conclusion** — Best argument artifact is fine
7. **Audit Trail** — Recent history events
