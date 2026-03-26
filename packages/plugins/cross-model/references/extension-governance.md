# Extension Governance

**Version:** 0.3.0 (pre-implementation)
**Status:** Approved design — blocks 0.3.0 implementation.
**Authority:** Governs namespace ownership, validation rules, and versioning for `TurnRequest.extensions` and `TurnRequest.required_capabilities`. The context-injection contract remains authoritative for the overall protocol; this spec extends it for the extensions mechanism.

**ADR:** `docs/decisions/2026-03-26-entity-injection-accepted-risk-extensions-path.md`
**Related:** `capability-negotiation.md` (lifecycle and error handling), `rollout-0.3.0.md` (deployment procedure)
**Codex dialogue:** Thread `019d2ba7-2d5e-75e2-9a7c-694ddbc1b4e5` (7 turns, exploratory, converged)

---

## Field Definitions

### `TurnRequest.extensions`

```python
extensions: dict[str, JsonValue] = Field(default_factory=dict)
```

Capability-keyed dictionary. Keys are capability IDs (§Capability ID Format). Values are non-null JSON values.

| Constraint | Rule |
|-----------|------|
| Default | Empty dict via `default_factory` |
| Nullability | Not nullable — `dict`, not `dict \| None` |
| Top-level null value | Rejected (`invalid_extension_value`) |
| Unknown namespace key | Rejected in 0.x (`invalid_extension_value`) |
| Value type | `JsonValue` — any non-null JSON value |

**Semantics:**

| Key state | Meaning |
|-----------|---------|
| Present | Caller provides payload for that capability |
| Absent | No payload for that capability |
| Empty dict | No extensions (default) |

### `TurnRequest.required_capabilities`

```python
required_capabilities: list[str] = Field(default_factory=list)
```

List of capability IDs the server MUST support for this request.

| Constraint | Rule |
|-----------|------|
| Default | Empty list via `default_factory` |
| Nullability | Not nullable — `list`, not `list \| None` |
| Normalization | Pipeline sorts to unique (model stores as-sent) |
| Element format | Must match §Capability ID Format |

### The Required/Optional Split

| Placement | Semantics |
|-----------|-----------|
| In `required_capabilities` AND `extensions` | Mandatory capability with payload |
| In `required_capabilities` only | Mandatory flag capability (no payload needed) |
| In `extensions` only | Optional capability with payload — server may warn and ignore |

---

## Capability ID Format

Capability IDs are ASCII strings with dot-separated segments.

| Rule | Constraint |
|------|------------|
| Character set | Lowercase ASCII letters, digits, underscores |
| Segment separator | `.` (dot) |
| Minimum segments | 3: `<namespace>.<name>.v<N>` |
| Version suffix | Final segment: `v` followed by positive integer |
| Case | Lowercase only — uppercase rejected at validation |

**Regex:** `^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*\.v[1-9][0-9]*$`

**Examples:**

| ID | Valid | Reason |
|----|-------|--------|
| `ci.phase_id.v1` | ✓ | First-party, versioned |
| `ci.scope.v1` | ✓ | First-party, versioned |
| `ext.acme.audit_log.v2` | ✓ | Third-party format (deferred) |
| `phase_id` | ✗ | No namespace, no version |
| `CI.PHASE_ID.V1` | ✗ | Uppercase |
| `ci.phase_id` | ✗ | No version suffix |
| `ci..phase_id.v1` | ✗ | Empty segment |

---

## Namespace Ownership

### `ci.*` — First-Party (0.3.0)

Reserved for protocol capabilities defined in this repository. All `ci.*` capability IDs and their schemas are defined in this spec or its amendments.

**Current capabilities:**

| ID | Purpose | Payload type | Ships with |
|----|---------|-------------|------------|
| `ci.phase_id.v1` | Phase boundary detection | `str` (non-empty) | 0.3.0 |

### Third-Party — Deferred

Third-party extensions use ownership-bearing namespaces: `ext.<owner>.<name>.v<N>`. Not recognized in 0.3.0 — any non-`ci.*` key is rejected with `invalid_extension_value`. A governance amendment is required before accepting non-`ci.*` namespaces.

**Rationale:** Reverse-DNS namespace governance is over-engineering for a single-repo, single-consumer system. Deferred until third-party extensions materialize.

---

## Validation Rules

### Validation Owner

The **server pipeline** is the authoritative validator. The Pydantic model validates structural shape (types, required fields). The pipeline validates semantic rules (supported capabilities, namespace membership, capability ID format, payload type per capability).

### Pipeline Validation Order

Validation runs as pipeline step 2 (after version gate, before dual-claims guard):

1. **Normalize** `required_capabilities` to sorted unique list.
2. **Validate capability ID format** for all keys in `extensions` and all entries in `required_capabilities`. Reject on first invalid ID.
3. **Validate namespace** — all IDs must start with a recognized namespace prefix (0.3.0: `ci.` only).
4. **Check server support** — for each ID in `required_capabilities`, verify the server recognizes the capability. Reject on first unsupported required capability.
5. **Validate extension payloads** — for each recognized capability with a key in `extensions`, validate the payload against the capability's typed schema (§Capability Schemas). Reject on first invalid value.
6. **Warn on optional unknowns** — for each key in `extensions` not in `required_capabilities` that the server doesn't recognize, emit a `ValidationWarning`.

### Invalid-Value Behavior

**Hard reject.** No best-effort parsing, no silent coercion, no partial acceptance.

Invalid values produce `TurnPacketError` with the appropriate error code. This matches the system's existing strictness bias: `extra="forbid"` rejects unknown fields, exact-match version rejects mismatched schemas.

### Error Codes

Added to `ErrorDetail.code` Literal:

| Code | Trigger | Details payload |
|------|---------|-----------------|
| `unsupported_required_capability` | Required capability not supported by server | `{"unsupported": ["ci.scope.v1"], "request_schema_version": "0.3.0"}` |
| `invalid_extension_value` | Payload fails capability schema, null value, invalid namespace, or invalid ID format | `{"capability": "ci.phase_id.v1", "reason": "expected string, got int"}` |
| `required_capabilities_changed` | `required_capabilities` set differs from Turn 1 | `{"expected": ["ci.phase_id.v1"], "received": ["ci.phase_id.v1", "ci.scope.v1"]}` |

---

## Capability Schemas

Each `ci.*` capability has a typed schema defining valid payload values.

### `ci.phase_id.v1`

| Property | Value |
|----------|-------|
| **Purpose** | Agent-declared phase boundary detection |
| **Payload type** | `str` (non-empty) |
| **Semantics** | Unique identifier for the current dialogue phase |
| **Behavior** | When active, supersedes posture-based phase boundary inference in `ConversationState` |
| **Complementary** | `phase_id` answers "same phase?"; `posture` answers "what mode?" |
| **Warning** | If posture changes while `phase_id` stays the same, emit a `ValidationWarning` |
| **Without capability** | Current posture-based boundary detection unchanged |

---

## Versioning

### Per-Capability Versioning

Major version is embedded in the capability ID: `ci.<name>.v<N>`.

| Rule | Detail |
|------|--------|
| Breaking change | New capability ID (e.g., `ci.phase_id.v2`) |
| Non-breaking change | Backwards-compatible within the same `v<N>` |
| Stability | Within one major version, semantics MUST stay stable |
| Coexistence | Multiple versions may coexist (both `v1` and `v2` recognized) |

### Schema Version Relationship

`extensions` and `required_capabilities` are protocol fields introduced in schema version `0.3.0`. The schema version governs field presence; the capability version governs payload semantics. These are independent versioning axes.

---

## Response Rules

### Echo

`TurnPacketSuccess` gains one field:

```python
honored_capabilities: list[str] = Field(default_factory=list)
```

Contains the sorted list of capability IDs the server accepted and will honor for this turn. Subset of `required_capabilities` ∪ recognized keys from `extensions`.

**No `effective_extensions` field.** The caller knows what it sent; it only needs to know what the server accepted. Normalization warnings (e.g., duplicate `required_capabilities` entries) go in `warnings[]`.

### Normalization

`required_capabilities` is normalized to sorted unique in the pipeline. The original as-sent list is not preserved. Duplicates trigger a `ValidationWarning`.

---

## `JsonValue` Type

Extension value type — union of JSON-representable non-null types:

```python
JsonValue = str | int | float | bool | list[Any] | dict[str, Any]
```

Top-level `None` is explicitly excluded. Absence of a key means "no payload"; `None` as a value is ambiguous and rejected.

**`strict=True` implications:** Pydantic's strict mode blocks implicit coercions (e.g., `int` to `float`, `list` to `tuple`). Extension payloads arriving as JSON from the MCP SDK are already in their natural Python types after `json.loads` — no coercion expected.

---

## Security Notes

- `extensions` is a controlled opening in the `extra="forbid"` surface. The opening is bounded: keys must match recognized namespaces, values must pass per-capability validation. Unknown namespace keys are rejected, not ignored.
- `required_capabilities` provides **downgrade protection**, not **authenticity protection**. It prevents old servers from silently dropping new capability requirements. It does NOT prevent a compromised agent from sending `required_capabilities: []`.
- Extension payloads are not bound into HMAC tokens unless a capability specifically alters Call 2 execution semantics independently of the signed scout spec.
