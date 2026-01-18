# Troubleshooting

Common issues during rigorous skill creation and their recovery paths.

## Triage Issues (Phase 0)

| Symptom | Cause | Recovery |
|---------|-------|----------|
| "command not found" | Python not available | Skip triage; proceed to CREATE |
| Non-zero exit | Script error | Log; proceed to CREATE |
| Malformed JSON | Script bug | Ask user: create or specify path |

## Baseline Issues (Phase 3)

| Symptom | Cause | Recovery |
|---------|-------|----------|
| Canary fails | Context leaking | Run baseline in fresh session |
| No failures | Scenarios too weak | Add 3+ combined pressures |
| Agent asks questions | Escape routes | Remove "ask user" option |
| Fails for wrong reason | Confusing scenario | Rewrite with clearer setup |
| Already does right thing | May not need skill | Find harder cases |

## Generation Issues (Phase 4)

| Symptom | Cause | Recovery |
|---------|-------|----------|
| Section fails checklist | Content gaps | Review checklist, regenerate |
| User rejects repeatedly | Requirements mismatch | Return to Phase 2 |
| Exceeds 1000 lines | Scope creep | Split into focused skills |

## Verification Issues (Phase 5)

| Symptom | Cause | Recovery |
|---------|-------|----------|
| Fails despite skill | Skill incomplete | Meta-test, identify gap |
| Hybrid approach | Loopholes not closed | Add explicit negations |
| Argues skill is wrong | Missing principle | Add "letter = spirit" |
| Complies but no citation | Not discoverable | Improve triggers |

## Panel Issues (Phase 7)

| Symptom | Cause | Recovery |
|---------|-------|----------|
| Model error on Opus | Quota | Retry with Sonnet |
| All timeout | Network | Skip panel with warning |
| Contradictory | Genuine ambiguity | Present both; user decides |
| Same issues 3+ times | Design flaw | Return to Phase 2 |

## Context Exhaustion

| Symptom | Cause | Recovery |
|---------|-------|----------|
| Terse responses | Context filling | Save Session State, new session |
| Forgot requirements | Truncated | Re-read metadata.decisions |
| Sections inconsistent | Lost context | Run Semantic Coherence |

## Abort/Rollback

| Trigger | Action |
|---------|--------|
| User requests abort | Confirm; delete skill-dir; clear TodoWrite |
| Unrecoverable error | Preserve Session State; ask user |
| Out of scope | Document why; offer simpler skill or abort |

**Cleanup:**
- Delete partial SKILL.md
- Delete partial supporting files
- Clear TodoWrite
- Notify: "Skill creation aborted. No artifacts remain."
