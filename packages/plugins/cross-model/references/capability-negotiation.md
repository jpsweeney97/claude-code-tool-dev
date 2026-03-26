# Capability Negotiation

**Version:** 0.3.0 (pre-implementation)
**Status:** Approved design — blocks 0.3.0 implementation.
**Authority:** Governs the lifecycle of capability negotiation between agent and server within a conversation. The extension governance spec (`extension-governance.md`) defines field shapes, namespaces, and validation rules. This spec defines when and how those fields are processed across turns.

**ADR:** `docs/decisions/2026-03-26-entity-injection-accepted-risk-extensions-path.md`
**Related:** `extension-governance.md` (field definitions, error codes), `rollout-0.3.0.md` (deployment)
**Codex dialogue:** Thread `019d2ba7-2d5e-75e2-9a7c-694ddbc1b4e5` (7 turns, exploratory, converged)

---

## Lifecycle

### Turn 1: Contract Establishment

The first `TurnRequest` in a conversation establishes the capability contract.

1. Server validates `extensions` and `required_capabilities` per the governance spec (§Validation Rules).
2. If validation passes, server persists `required_capabilities` (normalized to sorted unique) as `negotiated_capabilities` in `ConversationState`.
3. Server processes the turn normally (pipeline steps 3-17).
4. `TurnPacketSuccess.honored_capabilities` echoes the accepted capabilities.

### Turns 2-N: Contract Enforcement

Subsequent turns must present the **same `required_capabilities` set** (after normalization to sorted unique).

| Condition | Behavior |
|-----------|----------|
| Matches `negotiated_capabilities` | Proceed |
| Differs from `negotiated_capabilities` | Hard reject: `required_capabilities_changed` |
| Both empty | Proceed (no capabilities in this conversation) |

**Exact-match for 0.x.** Not monotonic-subset, not superset-allowed. This matches the system's existing exactness bias (exact schema version, `extra="forbid"`).

### Extension Payloads: Per-Turn Variation

The capability set is conversation-stable. Extension payloads vary per-turn.

| Aspect | Stability |
|--------|-----------|
| `required_capabilities` set | Immutable after Turn 1 |
| `extensions` keys (which capabilities have payloads) | May vary per-turn |
| `extensions` values (payload content) | May vary per-turn |

This enables `ci.phase_id.v1` to carry `"exploration"` on one turn and `"synthesis"` on the next without renegotiating the capability contract.

---

## Pipeline Integration

### Position: Step 2

Capability checking is **pipeline step 2**, after the version gate (step 1) and before the dual-claims guard (step 3).

```
Step 1: Schema version gate      → TurnPacketError(invalid_schema_version)
Step 2: Capability negotiation   → TurnPacketError(unsupported_required_capability |
                                                    invalid_extension_value |
                                                    required_capabilities_changed)
Step 3: Dual-claims guard        → ...
...
Step 17: Checkpoint serialization
```

### Admission Control vs. Processing Errors

The contract principle "errors in the helper never block the conversation" applies to **processing errors** — entity extraction failures, template matching bugs, checkpoint corruption. It does NOT apply to **admission control** — wrong schema version, unsupported capabilities, turn cap exceeded.

Admission control failures produce `TurnPacketError`. The agent cannot proceed with an incompatible server. This is identical to the existing `invalid_schema_version` and `turn_cap_exceeded` behavior.

---

## Error Handling

### Error Response Format

Error details are machine-readable JSON. See `extension-governance.md` §Error Codes for the complete list.

```json
{
  "code": "unsupported_required_capability",
  "message": "Server does not support required capability: ci.scope.v1",
  "details": {
    "unsupported": ["ci.scope.v1"],
    "request_schema_version": "0.3.0"
  }
}
```

### Agent Response to Errors

| Error code | Agent action |
|------------|-------------|
| `unsupported_required_capability` | Report to user; cannot downgrade mid-conversation |
| `invalid_extension_value` | Fix payload and retry the turn |
| `required_capabilities_changed` | Bug — capabilities must not change mid-conversation |

---

## ConversationState Changes

`ConversationState` gains one field:

```python
negotiated_capabilities: tuple[str, ...] = ()
```

| Property | Value |
|----------|-------|
| Default | Empty tuple (backwards-compatible with existing conversations) |
| Set by | Pipeline step 2 on Turn 1 |
| Immutable after | Turn 1 |
| Checkpoint impact | Format bumps to `"2"` (see `rollout-0.3.0.md`) |

**Projection method:**

```python
def with_negotiated_capabilities(self, caps: tuple[str, ...]) -> ConversationState:
    """New state with negotiated capabilities set. Called once on Turn 1."""
    return self.model_copy(update={"negotiated_capabilities": caps})
```

---

## HMAC Implications

`negotiated_capabilities` is NOT bound into `ScoutTokenPayload`. Capabilities govern which pipeline features are active, not which files can be read. Scout authorization (path, template, budget) is determined by entities, templates, and budget — all already HMAC-bound.

**Exception:** If a future capability alters Call 2 execution semantics independently of the existing signed spec (e.g., restricting scout scope to a path set), that capability MUST add its own field to `ScoutTokenPayload` and document the HMAC binding.

---

## `ci.phase_id.v1` Behavior

### When Active

When `ci.phase_id.v1` is in `negotiated_capabilities`:

1. Server reads `extensions["ci.phase_id.v1"]` — string payload is the current phase ID.
2. Phase boundary detection uses `phase_id` change instead of `posture` change.
3. `ConversationState.phase_start_index` resets on `phase_id` change.
4. If `posture` changes while `phase_id` stays the same, server emits `ValidationWarning`: `"posture changed without phase_id change"`.

### When Inactive

Without `ci.phase_id.v1` in `negotiated_capabilities`:

- Current posture-based boundary detection unchanged.
- `extensions["ci.phase_id.v1"]` is ignored even if present (capability not negotiated as required).

---

## 1.x Compatibility Rules

### Locked Now (Shapes 0.3.0)

| Rule | Rationale |
|------|-----------|
| `required_capabilities` means all-or-fail | Downgrade protection requires hard reject on unsupported |
| Unknown optional extensions are ignorable | Forward compatibility for callers probing new capabilities |
| Breaking capability changes require new IDs | Per-capability versioning via `v<N>` suffix |
| New checkpoint fields require format bump | Checkpoint reader must know which fields to expect |
| New `ConversationState` fields must have defaults | Newer readers must restore older checkpoints |

### Deferred to 1.0 Cut

| Decision | Why deferred |
|----------|-------------|
| Exact 1.x version matching policy | Requires deciding semver range vs. exact minor |
| Server capabilities introspection endpoint | Lock the principle; defer tool name and shape |
| Historical multi-version server support | Depends on deployment model maturity |
| External namespace governance (`ext.*`) | No third-party consumers exist |
