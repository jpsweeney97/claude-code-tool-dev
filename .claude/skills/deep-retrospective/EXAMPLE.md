# Worked Example: Key Transitions

Condensed example showing critical transitions. Drawn from credential exposure incident (2025-12-16).

---

## Stage 2 → Stage 3: Surface Cause → Pattern Test

**Stage 2 output (surface causes):**

| Cause | How it contributed |
|-------|-------------------|
| Wrong mental model | Assumed auth was monolithic — one credential to move between environments |
| Conflated token types | Treated OAuth tokens and API keys as interchangeable |
| No threat modeling | Didn't consider that command output goes to conversation transcript |
| Didn't verify preconditions | Never asked "Have you tried claude /login?" |

**Stage 3 test:** Can I generate variants?

- **Variant 1:** SSH key extraction for remote server setup → same pattern (extract from secure storage to bridge environments)
- **Variant 2:** API key written to .env file for Docker → same pattern (write credentials to file to share across boundary)
- **Variant 3:** Token displayed in output for debugging → same pattern (expose credentials in visible channel)

**Gate decision:** Surface fix ("don't extract OAuth tokens from Keychain") would NOT prevent variants 2 and 3. **CONTINUE.**

---

## Stage 4 → Stage 5: Pattern Identified → Challenge Framing

**Stage 4 output:**

```
Obvious explanation: "I didn't know Linux Claude Code had its own auth"
Why insufficient: I did know. The information was available but unused.
                  This doesn't explain variants 2 and 3 either.
Proposed pattern: "Capability-first thinking — I pattern-matched to tools 
                  I knew (Keychain extraction, apiKeyHelper) without 
                  checking if the target environment had its own solution."
```

**Stage 5 challenge:** Is this framing precise?

**First attempt:** "I solved before understanding"
- Problem: Too abstract. Doesn't predict what I'd do differently.

**Refined:** "I work forward from capabilities rather than backward from goals"
- Test: Does this predict the variants? Yes — all three involve reaching for a known tool before checking if it's needed.
- Test: What would I do differently? Check "does the target have native solution?" before proposing bridging.

**Result:** Framing accepted. Actionable and predicts other failures.

---

## Stage 8: Encoding Validation

**Initial encoding:** "When asked about container auth, ALWAYS check if `claude /login` inside the container works before suggesting alternatives."

**Validation:**

| Variant | Prevents? | How? |
|---------|-----------|------|
| SSH key extraction | ⚠️ Partially | Only if framed as "auth problem" — too narrow |
| API key to .env | ✗ No | Doesn't trigger on file-writing |
| Token display | ✗ No | Doesn't trigger on display |

**Result:** FAIL. Encoding is incident-specific.

---

**Revised encoding:** "NEVER extract credentials from secure storage to plaintext. NEVER write credentials to files. When auth doesn't work in an environment, first check if that environment has its own native auth mechanism."

**Re-validation:**

| Variant | Prevents? | How? |
|---------|-----------|------|
| SSH key extraction | ✓ Yes | "Extract from secure storage" blocked |
| API key to .env | ✓ Yes | "Write credentials to files" blocked |
| Token display | ✓ Yes | Covered by "never display credentials" addition |

**Result:** PASS. Encoding addresses pattern.

---

## Full Reference

For the complete conversation showing all stages and deeper exploration of *why* capability-first thinking occurs, see:

`deep-retrospective-credential-incident.md`

Location: `examples/deep-retrospective-credential-incident.md`

The condensed example above is sufficient to apply the methodology. The full transcript covers:
- Pushing past "capability-first" to "optimizing for demonstrating competence"
- The structural gap between "goal-shaped output" and "achieving goals"
- How rules and hooks function as encoded feedback across sessions
