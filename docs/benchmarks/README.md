# Benchmarks

> **Status: CLOSED** — Behavioral marker measurement project (Tier A) closed 2026-02-08. See [closure document](../plans/2026-02-08-tier-a-closure.md).

This directory contains artifacts from the simulation-based skill assessment benchmark (v0). The project measured whether skills produce detectable behavioral differences in Claude Code subagent output.

## Contents

| Path | Description |
|------|-------------|
| `bench-skill-bodies_*.md` | Skill body variants used as benchmark stimuli |
| `control-bodies_*.md` | Control (no-skill) bodies for baseline runs |
| `target-skills_*.md` | Target skill definitions under test |
| `operations/` | Benchmark operation scripts and runner configuration |
| `runs/` | Raw run output from benchmark executions |
| `scenarios/` | Scenario definitions (queries, rubrics, anchors) |
| `suites/` | Suite configurations grouping scenarios into benchmark runs |
