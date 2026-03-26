# 0.3.0 Rollout Procedure

**Version:** 0.3.0 (pre-implementation)
**Status:** Approved design — blocks 0.3.0 implementation.
**Purpose:** Deployment procedure for the 0.2.0 → 0.3.0 schema transition, including the bridge server release, checkpoint migration, and cleanup timeline.

**ADR:** `docs/decisions/2026-03-26-entity-injection-accepted-risk-extensions-path.md`
**Related:** `extension-governance.md` (new fields), `capability-negotiation.md` (lifecycle)
**Codex dialogue:** Thread `019d2ba7-2d5e-75e2-9a7c-694ddbc1b4e5` (7 turns, exploratory, converged)

---

## Deployment Constraint

The agent (`codex-dialogue.md`) loads at Claude session start. The server (context-injection MCP process) can restart independently. This asymmetry means:

- A flag-day deploy is impossible — stale Claude sessions send `0.2.0` requests to a `0.3.0`-only server and fail.
- The server must temporarily accept both versions during transition.

---

## Rollout Sequence

### Phase 1: Bridge Server Release

Ship a server release that accepts both `0.2.0` and `0.3.0` requests.

**1a. Bridge ingress model**

Create `TurnRequestBridge` with a widened `schema_version` Literal:

```python
class TurnRequestBridge(ProtocolModel):
    """Bridge ingress model — accepts 0.2.0 and 0.3.0 during rollout.

    Temporary. Removed in Phase 3 (cleanup).
    """

    schema_version: Literal["0.2.0", "0.3.0"]
    # ... all existing TurnRequest fields ...

    # 0.3.0 fields (defaulted for 0.2.0 compatibility)
    extensions: dict[str, JsonValue] = Field(default_factory=dict)
    required_capabilities: list[str] = Field(default_factory=list)
```

**1b. Version-conditioned validation**

After parsing, enforce version surface rules:

| Condition | Rule |
|-----------|------|
| `schema_version == "0.2.0"` AND `extensions` non-empty | Reject: `invalid_extension_value` |
| `schema_version == "0.2.0"` AND `required_capabilities` non-empty | Reject: `invalid_extension_value` |
| `schema_version == "0.3.0"` | Validate per extension governance spec |

The version surface rules prevent accidentally widening the `0.2.0` contract. A `0.2.0` request carrying extensions is a bug in the caller, not a feature.

**1c. Internal dispatch**

After validation, dispatch to version-specific processing:

```
TurnRequestBridge
  ├── schema_version == "0.2.0" → existing pipeline (no capability step)
  └── schema_version == "0.3.0" → pipeline with step 2 (capability negotiation)
```

Do NOT use a single permanent superset `TurnRequest`. The bridge model is temporary and version-specific models preserve closed-model discipline. A permanent superset blurs versioned invariants.

**1d. Response versioning**

`TurnPacketSuccess.schema_version` and `TurnPacketError.schema_version` echo the request's `schema_version`:

| Request version | Response version | `honored_capabilities` |
|----------------|------------------|----------------------|
| `0.2.0` | `0.2.0` | Absent (not in 0.2.0 schema) |
| `0.3.0` | `0.3.0` | Present (may be empty list) |

### Phase 2: Agent Update

Update `codex-dialogue.md` to emit `schema_version: "0.3.0"` with `extensions` and `required_capabilities` fields.

- New Claude sessions use `0.3.0`.
- Existing sessions continue with `0.2.0` until they end naturally.
- No forced migration, no interruption.

### Phase 3: Cleanup

After stale sessions expire (recommended: 2 weeks after Phase 2):

1. Remove `TurnRequestBridge` — revert to a single `TurnRequest` with `SchemaVersionLiteral = Literal["0.3.0"]`.
2. Remove `0.2.0` conditional paths from the pipeline.
3. Update `SCHEMA_VERSION` constant to `"0.3.0"`.
4. Remove `0.2.0` from `SchemaVersionLiteral`.

---

## Checkpoint Migration

### Format Version Bump

`CHECKPOINT_FORMAT_VERSION` bumps from `"1"` to `"2"` when `ConversationState` gains `negotiated_capabilities`.

| Format | Fields | Written by |
|--------|--------|------------|
| `"1"` | Existing (no `negotiated_capabilities`) | 0.2.0 conversations |
| `"2"` | Existing + `negotiated_capabilities` | 0.3.0 conversations |

### Reading Rules

The 0.3.0 server reads both formats:

| Checkpoint format | Behavior |
|-------------------|----------|
| `"1"` | Restore without `negotiated_capabilities` (defaults to `()`) |
| `"2"` | Restore with `negotiated_capabilities` |
| Unknown | Existing `checkpoint_invalid` error handling |

### Writing Rules

| Conversation schema | Checkpoint format written |
|--------------------|--------------------------|
| `0.2.0` | `"1"` (unchanged) |
| `0.3.0` | `"2"` |

### Default Requirement

All new `ConversationState` fields MUST have defaults so newer readers can restore older checkpoints. `negotiated_capabilities: tuple[str, ...] = ()` satisfies this.

---

## Unknown Schema Versions

During the bridge period, schema versions outside the admitted set (`"0.2.0"`, `"0.3.0"`) receive transport-level argument validation failures from Pydantic's `Literal` check, not protocol-level `TurnPacketError`. This is acceptable:

- Transport-level failures produce an MCP error response (not a `TurnPacket`).
- The agent handles both error shapes (existing behavior for malformed input).
- No special error code needed for out-of-range schema versions during bridge.

---

## Rollback

If 0.3.0 must be rolled back after Phase 2:

1. Revert `codex-dialogue.md` to emit `0.2.0`.
2. The bridge server continues accepting both — no server rollback needed.
3. In-progress `0.3.0` conversations fail if the agent sends `0.2.0` on next turn (`required_capabilities_changed`). Acceptable — the agent should not change schema versions mid-conversation.
4. Checkpoint format `"2"` data becomes orphaned but is harmless (`negotiated_capabilities: ()` means no capability contract was established).

---

## Pre-Deployment Checklist

Before shipping Phase 1:

- [ ] Extension governance spec reviewed and finalized
- [ ] Capability negotiation spec reviewed and finalized
- [ ] `TurnRequestBridge` implemented with version-conditioned validation
- [ ] Pipeline step 2 (capability negotiation) implemented
- [ ] `ConversationState.negotiated_capabilities` field added with default
- [ ] `TurnPacketSuccess.honored_capabilities` field added with default
- [ ] Three error codes added to `ErrorDetail.code` Literal
- [ ] `CHECKPOINT_FORMAT_VERSION` bumped to `"2"`
- [ ] Checkpoint reader handles formats `"1"` and `"2"`
- [ ] `ci.phase_id.v1` capability schema implemented
- [ ] Capability validation tests (format, namespace, payload)
- [ ] Negotiation lifecycle tests (Turn 1 establishment, Turn 2+ enforcement)
- [ ] Bridge dispatch tests (0.2.0 ↔ 0.3.0 routing, version surface rules)
- [ ] Checkpoint migration tests (format 1 → 2, format 2 restore, defaults)
- [ ] Contract migration section updated for 0.3.0
