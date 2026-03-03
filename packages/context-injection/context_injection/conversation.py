"""Conversation state management.

Immutable projection pattern: ConversationState is never mutated.
Projection methods return new instances via model_copy(update={...}).
Pipeline commits atomically by replacing the dict entry:
ctx.conversations[id] = projected.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from context_injection.ledger import CumulativeState, LedgerEntry
from context_injection.types import Claim, EvidenceRecord


class ConversationState(BaseModel):
    """Per-conversation state. Frozen — projection methods return new instances.

    Server-side state — not protocol-facing. Uses BaseModel directly with
    identical config to ProtocolModel (frozen, extra=forbid, strict).
    """

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    conversation_id: str
    entries: tuple[LedgerEntry, ...] = ()
    claim_registry: tuple[Claim, ...] = ()
    evidence_history: tuple[EvidenceRecord, ...] = ()
    closing_probe_fired: bool = False
    last_checkpoint_id: str | None = None
    # Phase tracking (Release B)
    last_posture: str | None = None
    phase_start_index: int = 0

    def with_turn(self, entry: LedgerEntry) -> ConversationState:
        """New state with entry appended and claim_registry extended."""
        return self.model_copy(
            update={
                "entries": (*self.entries, entry),
                "claim_registry": (*self.claim_registry, *entry.claims),
            }
        )

    def with_evidence(self, record: EvidenceRecord) -> ConversationState:
        """New state with evidence record appended."""
        return self.model_copy(
            update={
                "evidence_history": (*self.evidence_history, record),
            }
        )

    def with_closing_probe_fired(self) -> ConversationState:
        """New state with closing_probe_fired set."""
        return self.model_copy(update={"closing_probe_fired": True})

    def with_checkpoint_id(self, checkpoint_id: str) -> ConversationState:
        """New state with last_checkpoint_id updated."""
        return self.model_copy(update={"last_checkpoint_id": checkpoint_id})

    def with_posture_change(
        self, posture: str, phase_start_index: int
    ) -> ConversationState:
        """New state reflecting a posture change at phase boundary."""
        return self.model_copy(
            update={
                "last_posture": posture,
                "phase_start_index": phase_start_index,
                "closing_probe_fired": False,
            }
        )

    def get_phase_entries(self) -> tuple[LedgerEntry, ...]:
        """Entries from the current phase (since last posture change)."""
        return self.entries[self.phase_start_index :]

    def get_cumulative_claims(self) -> list[Claim]:
        """All claims from all turns (insertion-ordered). Returns mutable copy."""
        return list(self.claim_registry)

    def get_evidence_history(self) -> list[EvidenceRecord]:
        """All evidence records (insertion-ordered). Returns mutable copy."""
        return list(self.evidence_history)

    def compute_cumulative_state(self) -> CumulativeState:
        """Aggregate state across all validated ledger entries.

        Correct only when compaction has not triggered. See DD-2 invariant:
        MAX_CONVERSATION_TURNS < MAX_ENTRIES_BEFORE_COMPACT ensures compaction
        is unreachable under normal operation. If compaction has occurred,
        totals reflect only the retained window, not full conversation history.

        total_claims: all claims across all entries (including reinforced).
        reinforced: scanned from claims (not tracked in counters).
        revised/conceded: from entry counters.
        unresolved_open: from latest entry's unresolved list.
        unresolved_closed: summed from entry counters.
        """
        total_claims = sum(len(e.claims) for e in self.entries)
        reinforced = sum(
            sum(1 for c in e.claims if c.status == "reinforced") for e in self.entries
        )
        revised = sum(e.counters.revised for e in self.entries)
        conceded = sum(e.counters.conceded for e in self.entries)
        unresolved_open = len(self.entries[-1].unresolved) if self.entries else 0
        unresolved_closed = sum(e.counters.unresolved_closed for e in self.entries)
        turns_completed = len(self.entries)
        effective_delta_sequence = [e.effective_delta for e in self.entries]

        return CumulativeState(
            total_claims=total_claims,
            reinforced=reinforced,
            revised=revised,
            conceded=conceded,
            unresolved_open=unresolved_open,
            unresolved_closed=unresolved_closed,
            turns_completed=turns_completed,
            effective_delta_sequence=effective_delta_sequence,
        )
