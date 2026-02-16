"""Tests for template matching, ranking, and scout option synthesis.

Tests cover:
1. Budget computation
2. Focus-affinity gate (only in_focus=True entities pass for probe templates)
3. Anchor type ranking (file_loc > file_path > file_name > symbol)
4. Clarifier templates bypass hard gate
5. Dedupe: already-scouted entity_key filtered out
6. Scout option synthesis (ReadOption/GrepOption created correctly)
7. Codex-review gaps:
   - Resolved-key dedupe (file_name resolving to file_path)
   - Risk-signal cap halving (max_lines=20, max_chars=1000)
   - Budget floor invariant (evidence_history length is floor)
"""

import re

from context_injection.canonical import ScoutTokenPayload
from context_injection.state import AppContext, verify_token
from context_injection.types import (
    Entity,
    EvidenceRecord,
    Focus,
    GrepOption,
    PathDecision,
    ReadOption,
    ReadSpec,
    SCHEMA_VERSION,
    TurnRequest,
)


# --- Helpers ---


def _make_ctx() -> AppContext:
    return AppContext.create(
        repo_root="/tmp/repo", git_files={"src/app.py", "config.yaml"}
    )


def _make_turn_request(
    conversation_id: str = "conv_1",
    turn_number: int = 1,
) -> TurnRequest:
    """Convenience TurnRequest constructor with sensible 0.2.0 defaults."""
    return TurnRequest(
        schema_version=SCHEMA_VERSION,
        turn_number=turn_number,
        conversation_id=conversation_id,
        focus=Focus(text="test", claims=[], unresolved=[]),
        posture="exploratory",
        position="Test position",
        claims=[],
        delta="static",
        tags=["test"],
        unresolved=[],
    )


def _make_entity(
    id: str = "e_001",
    type: str = "file_path",
    tier: int = 1,
    raw: str = "src/app.py",
    canonical: str = "src/app.py",
    confidence: str = "high",
    source_type: str = "claim",
    in_focus: bool = True,
    resolved_to: str | None = None,
) -> Entity:
    return Entity(
        id=id,
        type=type,
        tier=tier,
        raw=raw,
        canonical=canonical,
        confidence=confidence,
        source_type=source_type,
        in_focus=in_focus,
        resolved_to=resolved_to,
    )


def _make_path_decision(
    entity_id: str = "e_001",
    status: str = "allowed",
    user_rel: str = "src/app.py",
    resolved_rel: str | None = "src/app.py",
    risk_signal: bool = False,
    deny_reason: str | None = None,
    candidates: list[str] | None = None,
    unresolved_reason: str | None = None,
) -> PathDecision:
    return PathDecision(
        entity_id=entity_id,
        status=status,
        user_rel=user_rel,
        resolved_rel=resolved_rel,
        risk_signal=risk_signal,
        deny_reason=deny_reason,
        candidates=candidates,
        unresolved_reason=unresolved_reason,
    )


# ============================================================
# Budget computation
# ============================================================


class TestComputeBudget:
    def test_empty_history(self) -> None:
        from context_injection.templates import compute_budget

        budget = compute_budget([])
        assert budget.evidence_count == 0
        assert budget.evidence_remaining == 5
        assert budget.scout_available is True

    def test_partial_history(self) -> None:
        from context_injection.templates import compute_budget

        history = [
            EvidenceRecord(
                entity_key="file_path:src/app.py",
                template_id="probe.file_repo_fact",
                turn=1,
            ),
            EvidenceRecord(
                entity_key="symbol:os.path.join",
                template_id="probe.symbol_repo_fact",
                turn=1,
            ),
        ]
        budget = compute_budget(history)
        assert budget.evidence_count == 2
        assert budget.evidence_remaining == 3
        assert budget.scout_available is True

    def test_full_history_disables_scouting(self) -> None:
        from context_injection.templates import compute_budget

        history = [
            EvidenceRecord(
                entity_key=f"file_path:file_{i}.py",
                template_id="probe.file_repo_fact",
                turn=i,
            )
            for i in range(5)
        ]
        budget = compute_budget(history)
        assert budget.evidence_count == 5
        assert budget.evidence_remaining == 0
        assert budget.scout_available is False

    def test_over_capacity_clamps_remaining(self) -> None:
        """If somehow more than max evidence items exist, remaining is 0."""
        from context_injection.templates import compute_budget

        history = [
            EvidenceRecord(
                entity_key=f"file_path:file_{i}.py",
                template_id="probe.file_repo_fact",
                turn=i,
            )
            for i in range(7)
        ]
        budget = compute_budget(history)
        assert budget.evidence_count == 7
        assert budget.evidence_remaining == 0
        assert budget.scout_available is False

    def test_budget_floor_invariant(self) -> None:
        """evidence_history.length is the floor for evidence_count
        even if evidence items have been evicted from store.

        This means: compute_budget takes the history list as-is.
        The count equals len(history). No store lookup needed."""
        from context_injection.templates import compute_budget

        # 3 items in history — budget must reflect 3, not fewer
        history = [
            EvidenceRecord(
                entity_key=f"file_path:file_{i}.py",
                template_id="probe.file_repo_fact",
                turn=i,
            )
            for i in range(3)
        ]
        budget = compute_budget(history)
        assert budget.evidence_count == 3
        assert budget.evidence_remaining == 2


# ============================================================
# Focus-affinity hard gate
# ============================================================


class TestFocusAffinityGate:
    """Probe templates require in_focus=True. Entities with in_focus=False
    are excluded from probe template matching (Step A hard gate)."""

    def test_in_focus_entity_gets_probe_template(self) -> None:
        from context_injection.templates import match_templates

        ctx = _make_ctx()
        entity = _make_entity(in_focus=True, type="file_path", canonical="src/app.py")
        pd = _make_path_decision(
            entity_id="e_001", status="allowed", resolved_rel="src/app.py"
        )
        req = _make_turn_request()

        candidates, deduped, _ = match_templates([entity], [pd], [], req, ctx)
        probe_candidates = [
            c for c in candidates if c.template_id == "probe.file_repo_fact"
        ]
        assert len(probe_candidates) == 1
        assert probe_candidates[0].focus_affinity is True

    def test_out_of_focus_entity_no_probe_template(self) -> None:
        from context_injection.templates import match_templates

        ctx = _make_ctx()
        entity = _make_entity(in_focus=False, type="file_path", canonical="src/app.py")
        pd = _make_path_decision(
            entity_id="e_001", status="allowed", resolved_rel="src/app.py"
        )
        req = _make_turn_request()

        candidates, deduped, _ = match_templates([entity], [pd], [], req, ctx)
        probe_candidates = [
            c for c in candidates if c.template_id == "probe.file_repo_fact"
        ]
        assert len(probe_candidates) == 0

    def test_low_confidence_entity_no_probe_template(self) -> None:
        """Only high/medium confidence entities pass the hard gate."""
        from context_injection.templates import match_templates

        ctx = _make_ctx()
        entity = _make_entity(
            in_focus=True,
            type="file_path",
            canonical="src/app.py",
            confidence="low",
        )
        pd = _make_path_decision(
            entity_id="e_001", status="allowed", resolved_rel="src/app.py"
        )
        req = _make_turn_request()

        candidates, deduped, _ = match_templates([entity], [pd], [], req, ctx)
        probe_candidates = [c for c in candidates if c.template_id.startswith("probe.")]
        assert len(probe_candidates) == 0

    def test_post_mvp_tier1_entity_no_probe(self) -> None:
        """Post-MVP Tier 1 entities (dir_path, env_var, etc.) do not satisfy the gate."""
        from context_injection.templates import match_templates

        ctx = _make_ctx()
        entity = _make_entity(
            in_focus=True,
            type="dir_path",
            tier=1,
            raw="src/config/",
            canonical="src/config",
            confidence="high",
        )
        # dir_path won't have a path decision normally, but even with one it shouldn't match
        pd = _make_path_decision(entity_id="e_001", status="allowed")
        req = _make_turn_request()

        candidates, deduped, _ = match_templates([entity], [pd], [], req, ctx)
        assert len(candidates) == 0


# ============================================================
# Anchor type ranking
# ============================================================


class TestAnchorTypeRanking:
    """Ranking order: file_loc > file_path > file_name > symbol."""

    def test_file_loc_ranks_higher_than_file_path(self) -> None:
        from context_injection.templates import match_templates

        ctx = _make_ctx()
        e_loc = _make_entity(
            id="e_001",
            type="file_loc",
            raw="src/app.py:42",
            canonical="src/app.py",
        )
        e_path = _make_entity(
            id="e_002",
            type="file_path",
            raw="config.yaml",
            canonical="config.yaml",
        )
        pd_loc = _make_path_decision(
            entity_id="e_001", status="allowed", resolved_rel="src/app.py"
        )
        pd_path = _make_path_decision(
            entity_id="e_002",
            status="allowed",
            user_rel="config.yaml",
            resolved_rel="config.yaml",
        )
        req = _make_turn_request()

        candidates, _, _ = match_templates(
            [e_loc, e_path], [pd_loc, pd_path], [], req, ctx
        )
        probe_candidates = [c for c in candidates if c.template_id.startswith("probe.")]
        assert len(probe_candidates) == 2
        # file_loc should have rank 1, file_path should have rank 2
        loc_candidate = next(c for c in probe_candidates if c.entity_id == "e_001")
        path_candidate = next(c for c in probe_candidates if c.entity_id == "e_002")
        assert loc_candidate.rank < path_candidate.rank

    def test_symbol_ranks_lower_than_file_path(self) -> None:
        from context_injection.templates import match_templates

        ctx = _make_ctx()
        e_path = _make_entity(
            id="e_001",
            type="file_path",
            raw="src/app.py",
            canonical="src/app.py",
        )
        e_sym = _make_entity(
            id="e_002",
            type="symbol",
            raw="os.path.join",
            canonical="os.path.join",
        )
        pd_path = _make_path_decision(
            entity_id="e_001", status="allowed", resolved_rel="src/app.py"
        )
        # symbol doesn't need a path decision for matching, but we provide one for completeness
        req = _make_turn_request()

        candidates, _, _ = match_templates([e_path, e_sym], [pd_path], [], req, ctx)
        probe_candidates = [c for c in candidates if c.template_id.startswith("probe.")]
        assert len(probe_candidates) == 2
        path_candidate = next(c for c in probe_candidates if c.entity_id == "e_001")
        sym_candidate = next(c for c in probe_candidates if c.entity_id == "e_002")
        assert path_candidate.rank < sym_candidate.rank

    def test_file_name_ranks_between_file_path_and_symbol(self) -> None:
        from context_injection.templates import match_templates

        ctx = _make_ctx()
        e_path = _make_entity(
            id="e_001",
            type="file_path",
            raw="src/app.py",
            canonical="src/app.py",
        )
        e_name = _make_entity(
            id="e_002",
            type="file_name",
            raw="config.yaml",
            canonical="config.yaml",
            resolved_to="e_003",
        )
        e_resolved = _make_entity(
            id="e_003",
            type="file_path",
            raw="config.yaml",
            canonical="config.yaml",
        )
        e_sym = _make_entity(
            id="e_004",
            type="symbol",
            raw="os.path.join",
            canonical="os.path.join",
        )
        pd_path = _make_path_decision(
            entity_id="e_001", status="allowed", resolved_rel="src/app.py"
        )
        pd_name = _make_path_decision(
            entity_id="e_002",
            status="allowed",
            user_rel="config.yaml",
            resolved_rel="config.yaml",
        )
        req = _make_turn_request()

        candidates, _, _ = match_templates(
            [e_path, e_name, e_resolved, e_sym],
            [pd_path, pd_name],
            [],
            req,
            ctx,
        )
        probe_candidates = [c for c in candidates if c.template_id.startswith("probe.")]
        assert len(probe_candidates) >= 3
        path_c = next(c for c in probe_candidates if c.entity_id == "e_001")
        name_c = next(c for c in probe_candidates if c.entity_id == "e_002")
        sym_c = next(c for c in probe_candidates if c.entity_id == "e_004")
        assert path_c.rank < name_c.rank < sym_c.rank


# ============================================================
# Clarifier templates bypass hard gate
# ============================================================


class TestClarifierTemplates:
    """Clarifier templates bypass the hard gate and route from Tier 2 entities."""

    def test_file_hint_gets_clarify_file_path(self) -> None:
        from context_injection.templates import match_templates

        ctx = _make_ctx()
        entity = _make_entity(
            id="e_001",
            type="file_hint",
            tier=2,
            raw="the config file",
            canonical="the config file",
            confidence="low",
            in_focus=True,
        )
        req = _make_turn_request()

        candidates, _, _ = match_templates([entity], [], [], req, ctx)
        assert len(candidates) == 1
        assert candidates[0].template_id == "clarify.file_path"
        assert candidates[0].clarifier is not None
        assert candidates[0].scout_options == []

    def test_symbol_hint_gets_clarify_symbol(self) -> None:
        from context_injection.templates import match_templates

        ctx = _make_ctx()
        entity = _make_entity(
            id="e_001",
            type="symbol_hint",
            tier=2,
            raw="that function",
            canonical="that function",
            confidence="low",
            in_focus=True,
        )
        req = _make_turn_request()

        candidates, _, _ = match_templates([entity], [], [], req, ctx)
        assert len(candidates) == 1
        assert candidates[0].template_id == "clarify.symbol"
        assert candidates[0].clarifier is not None
        assert candidates[0].scout_options == []

    def test_clarifier_focus_affinity_false_still_works(self) -> None:
        """Clarifier templates do NOT require in_focus=True."""
        from context_injection.templates import match_templates

        ctx = _make_ctx()
        entity = _make_entity(
            id="e_001",
            type="file_hint",
            tier=2,
            raw="some file",
            canonical="some file",
            confidence="low",
            in_focus=False,
        )
        req = _make_turn_request()

        candidates, _, _ = match_templates([entity], [], [], req, ctx)
        assert len(candidates) == 1
        assert candidates[0].template_id == "clarify.file_path"
        assert candidates[0].focus_affinity is False

    def test_unresolved_file_name_gets_clarifier(self) -> None:
        """Unresolved file_name entities get clarify.file_path instead of probe."""
        from context_injection.templates import match_templates

        ctx = _make_ctx()
        entity = _make_entity(
            id="e_001",
            type="file_name",
            raw="config.yaml",
            canonical="config.yaml",
            in_focus=True,
            resolved_to=None,
        )
        pd = _make_path_decision(
            entity_id="e_001",
            status="unresolved",
            user_rel="config.yaml",
            resolved_rel=None,
            unresolved_reason="multiple_candidates",
            candidates=["src/config.yaml", "test/config.yaml"],
        )
        req = _make_turn_request()

        candidates, _, _ = match_templates([entity], [pd], [], req, ctx)
        assert len(candidates) == 1
        assert candidates[0].template_id == "clarify.file_path"
        assert candidates[0].clarifier is not None
        # Choices should include the candidates
        assert candidates[0].clarifier.choices is not None
        assert "src/config.yaml" in candidates[0].clarifier.choices


# ============================================================
# Dedupe
# ============================================================


class TestDedupe:
    """Entities already in evidence_history are filtered out."""

    def test_entity_already_scouted(self) -> None:
        from context_injection.templates import match_templates

        ctx = _make_ctx()
        entity = _make_entity(
            id="e_001",
            type="file_path",
            canonical="src/app.py",
            in_focus=True,
        )
        pd = _make_path_decision(
            entity_id="e_001", status="allowed", resolved_rel="src/app.py"
        )
        # Use a different template_id in history to trigger entity_already_scouted
        # (not template_already_used). This simulates a future scenario where the
        # same entity was previously scouted via a different template.
        history = [
            EvidenceRecord(
                entity_key="file_path:src/app.py",
                template_id="clarify.file_path",
                turn=1,
            ),
        ]
        req = _make_turn_request()

        candidates, deduped, _ = match_templates([entity], [pd], history, req, ctx)
        # No probe candidates for this entity
        probe_candidates = [
            c
            for c in candidates
            if c.entity_id == "e_001" and c.template_id.startswith("probe.")
        ]
        assert len(probe_candidates) == 0
        # DedupRecord created with entity_already_scouted (different template)
        assert len(deduped) >= 1
        d = deduped[0]
        assert d.entity_key == "file_path:src/app.py"
        assert d.reason == "entity_already_scouted"
        assert d.template_id is None
        assert d.prior_turn == 1

    def test_resolved_key_dedupe(self) -> None:
        """Codex-review gap #1: file_name:config.yaml resolves to file_path:src/config.yaml.
        If file_path:src/config.yaml was already scouted, the file_name entity is deduped
        using the resolved key, not the original entity_key."""
        from context_injection.templates import match_templates

        ctx = _make_ctx()
        # file_name entity that resolves to a file_path entity
        e_name = _make_entity(
            id="e_001",
            type="file_name",
            raw="config.yaml",
            canonical="config.yaml",
            in_focus=True,
            resolved_to="e_002",
        )
        e_resolved = _make_entity(
            id="e_002",
            type="file_path",
            raw="config.yaml",
            canonical="src/config.yaml",
            in_focus=True,
        )
        pd = _make_path_decision(
            entity_id="e_001",
            status="allowed",
            user_rel="config.yaml",
            resolved_rel="src/config.yaml",
        )
        # Evidence history has the resolved path already scouted
        history = [
            EvidenceRecord(
                entity_key="file_path:src/config.yaml",
                template_id="probe.file_repo_fact",
                turn=1,
            ),
        ]
        req = _make_turn_request()

        candidates, deduped, _ = match_templates(
            [e_name, e_resolved], [pd], history, req, ctx
        )
        # The file_name entity should be deduped via resolved key
        name_probes = [
            c
            for c in candidates
            if c.entity_id == "e_001" and c.template_id.startswith("probe.")
        ]
        assert len(name_probes) == 0
        # DedupRecord should reference the resolved key
        name_dedups = [
            d for d in deduped if d.entity_key == "file_path:src/config.yaml"
        ]
        assert len(name_dedups) >= 1

    def test_template_already_used(self) -> None:
        """Same (entity_key + template_id) combination produces template_already_used."""
        from context_injection.templates import match_templates

        ctx = _make_ctx()
        entity = _make_entity(
            id="e_001",
            type="symbol",
            raw="os.path.join",
            canonical="os.path.join",
            in_focus=True,
        )
        # Same entity_key AND same template_id → template_already_used
        history = [
            EvidenceRecord(
                entity_key="symbol:os.path.join",
                template_id="probe.symbol_repo_fact",
                turn=1,
            ),
        ]
        req = _make_turn_request()

        candidates, deduped, _ = match_templates([entity], [], history, req, ctx)
        sym_probes = [
            c
            for c in candidates
            if c.entity_id == "e_001" and c.template_id == "probe.symbol_repo_fact"
        ]
        assert len(sym_probes) == 0
        assert len(deduped) >= 1
        d = deduped[0]
        assert d.reason == "template_already_used"
        assert d.entity_key == "symbol:os.path.join"
        assert d.template_id == "probe.symbol_repo_fact"
        assert d.prior_turn == 1


# ============================================================
# Scout option synthesis
# ============================================================


class TestScoutOptionSynthesis:
    """Scout options are created correctly for each template type."""

    def test_file_path_creates_read_option_first_n(self) -> None:
        from context_injection.templates import match_templates

        ctx = _make_ctx()
        entity = _make_entity(
            id="e_001",
            type="file_path",
            raw="src/app.py",
            canonical="src/app.py",
        )
        pd = _make_path_decision(
            entity_id="e_001", status="allowed", resolved_rel="src/app.py"
        )
        req = _make_turn_request()

        candidates, _, _ = match_templates([entity], [pd], [], req, ctx)
        probe = next(c for c in candidates if c.template_id == "probe.file_repo_fact")
        assert len(probe.scout_options) == 1
        opt = probe.scout_options[0]
        assert isinstance(opt, ReadOption)
        assert opt.action == "read"
        assert opt.strategy == "first_n"
        assert opt.max_lines == 40
        assert opt.max_chars == 2000
        assert opt.center_line is None
        assert opt.risk_signal is False
        assert opt.target_display == "src/app.py"

    def test_file_loc_creates_read_option_centered(self) -> None:
        from context_injection.templates import match_templates

        ctx = _make_ctx()
        entity = _make_entity(
            id="e_001",
            type="file_loc",
            raw="src/app.py:42",
            canonical="src/app.py",
        )
        pd = _make_path_decision(
            entity_id="e_001", status="allowed", resolved_rel="src/app.py"
        )
        req = _make_turn_request()

        candidates, _, _ = match_templates([entity], [pd], [], req, ctx)
        probe = next(c for c in candidates if c.template_id == "probe.file_repo_fact")
        assert len(probe.scout_options) == 1
        opt = probe.scout_options[0]
        assert isinstance(opt, ReadOption)
        assert opt.strategy == "centered"
        assert opt.center_line == 42
        assert opt.max_lines == 40
        assert opt.max_chars == 2000

    def test_file_loc_github_anchor_extracts_line(self) -> None:
        from context_injection.templates import match_templates

        ctx = _make_ctx()
        entity = _make_entity(
            id="e_001",
            type="file_loc",
            raw="src/app.py#L99",
            canonical="src/app.py",
        )
        pd = _make_path_decision(
            entity_id="e_001", status="allowed", resolved_rel="src/app.py"
        )
        req = _make_turn_request()

        candidates, _, _ = match_templates([entity], [pd], [], req, ctx)
        probe = next(c for c in candidates if c.template_id == "probe.file_repo_fact")
        opt = probe.scout_options[0]
        assert opt.center_line == 99

    def test_symbol_creates_grep_option(self) -> None:
        from context_injection.templates import match_templates

        ctx = _make_ctx()
        entity = _make_entity(
            id="e_001",
            type="symbol",
            raw="os.path.join",
            canonical="os.path.join",
        )
        req = _make_turn_request()

        candidates, _, _ = match_templates([entity], [], [], req, ctx)
        probe = next(c for c in candidates if c.template_id == "probe.symbol_repo_fact")
        assert len(probe.scout_options) == 1
        opt = probe.scout_options[0]
        assert isinstance(opt, GrepOption)
        assert opt.action == "grep"
        assert opt.strategy == "match_context"
        assert opt.max_lines == 40
        assert opt.max_chars == 2000
        assert opt.context_lines == 2
        assert opt.max_ranges == 5

    def test_scout_option_has_valid_hmac_token(self) -> None:
        """Scout tokens must be verifiable HMAC tokens."""
        from context_injection.templates import match_templates

        ctx = _make_ctx()
        entity = _make_entity(
            id="e_001",
            type="file_path",
            raw="src/app.py",
            canonical="src/app.py",
        )
        pd = _make_path_decision(
            entity_id="e_001", status="allowed", resolved_rel="src/app.py"
        )
        req = _make_turn_request()

        candidates, _, _ = match_templates([entity], [pd], [], req, ctx)
        probe = next(c for c in candidates if c.template_id == "probe.file_repo_fact")
        opt = probe.scout_options[0]

        # Reconstruct the spec and payload to verify the token
        spec = ReadSpec(
            action="read",
            resolved_path="src/app.py",
            strategy="first_n",
            max_lines=40,
            max_chars=2000,
        )
        payload = ScoutTokenPayload(
            v=1,
            conversation_id="conv_1",
            turn_number=1,
            scout_option_id=opt.id,
            spec=spec,
        )
        assert verify_token(ctx.hmac_key, payload, opt.scout_token)

    def test_scout_option_id_format(self) -> None:
        from context_injection.templates import match_templates

        ctx = _make_ctx()
        entity = _make_entity(
            id="e_001",
            type="file_path",
            raw="src/app.py",
            canonical="src/app.py",
        )
        pd = _make_path_decision(
            entity_id="e_001", status="allowed", resolved_rel="src/app.py"
        )
        req = _make_turn_request()

        candidates, _, _ = match_templates([entity], [pd], [], req, ctx)
        probe = next(c for c in candidates if c.template_id == "probe.file_repo_fact")
        opt = probe.scout_options[0]
        assert re.match(r"so_\d{3}", opt.id)

    def test_template_candidate_id_format(self) -> None:
        from context_injection.templates import match_templates

        ctx = _make_ctx()
        entity = _make_entity(
            id="e_001",
            type="file_path",
            raw="src/app.py",
            canonical="src/app.py",
        )
        pd = _make_path_decision(
            entity_id="e_001", status="allowed", resolved_rel="src/app.py"
        )
        req = _make_turn_request()

        candidates, _, _ = match_templates([entity], [pd], [], req, ctx)
        assert len(candidates) >= 1
        assert re.match(r"tc_\d{3}", candidates[0].id)

    def test_file_name_resolved_uses_resolved_path(self) -> None:
        """file_name entity with resolved_to should use the resolved entity's
        canonical form for the scout target."""
        from context_injection.templates import match_templates

        ctx = _make_ctx()
        e_name = _make_entity(
            id="e_001",
            type="file_name",
            raw="config.yaml",
            canonical="config.yaml",
            in_focus=True,
            resolved_to="e_002",
        )
        e_resolved = _make_entity(
            id="e_002",
            type="file_path",
            raw="config.yaml",
            canonical="src/config.yaml",
            in_focus=True,
        )
        pd = _make_path_decision(
            entity_id="e_001",
            status="allowed",
            user_rel="config.yaml",
            resolved_rel="src/config.yaml",
        )
        req = _make_turn_request()

        candidates, _, _ = match_templates([e_name, e_resolved], [pd], [], req, ctx)
        name_probes = [
            c
            for c in candidates
            if c.entity_id == "e_001" and c.template_id == "probe.file_repo_fact"
        ]
        assert len(name_probes) == 1
        opt = name_probes[0].scout_options[0]
        assert isinstance(opt, ReadOption)
        # Scout target should be the resolved path, not the bare filename
        assert opt.target_display == "src/config.yaml"


# ============================================================
# Risk-signal cap halving (Codex-review gap #2)
# ============================================================


class TestRiskSignalCapHalving:
    """risk_signal=True in PathDecision produces half the budget caps."""

    def test_risk_signal_halves_read_caps(self) -> None:
        from context_injection.templates import match_templates

        ctx = _make_ctx()
        entity = _make_entity(
            id="e_001",
            type="file_path",
            raw="src/secret_config.py",
            canonical="src/secret_config.py",
        )
        pd = _make_path_decision(
            entity_id="e_001",
            status="allowed",
            user_rel="src/secret_config.py",
            resolved_rel="src/secret_config.py",
            risk_signal=True,
        )
        req = _make_turn_request()

        candidates, _, _ = match_templates([entity], [pd], [], req, ctx)
        probe = next(c for c in candidates if c.template_id == "probe.file_repo_fact")
        opt = probe.scout_options[0]
        assert isinstance(opt, ReadOption)
        assert opt.max_lines == 20
        assert opt.max_chars == 1000
        assert opt.risk_signal is True

    def test_no_risk_signal_full_caps(self) -> None:
        from context_injection.templates import match_templates

        ctx = _make_ctx()
        entity = _make_entity(
            id="e_001",
            type="file_path",
            raw="src/app.py",
            canonical="src/app.py",
        )
        pd = _make_path_decision(
            entity_id="e_001",
            status="allowed",
            resolved_rel="src/app.py",
            risk_signal=False,
        )
        req = _make_turn_request()

        candidates, _, _ = match_templates([entity], [pd], [], req, ctx)
        probe = next(c for c in candidates if c.template_id == "probe.file_repo_fact")
        opt = probe.scout_options[0]
        assert isinstance(opt, ReadOption)
        assert opt.max_lines == 40
        assert opt.max_chars == 2000
        assert opt.risk_signal is False


# ============================================================
# Scout not available when budget exhausted
# ============================================================


class TestBudgetExhausted:
    """When budget is exhausted, no probe templates should be produced."""

    def test_no_probe_when_budget_exhausted(self) -> None:
        from context_injection.templates import match_templates

        ctx = _make_ctx()
        entity = _make_entity(
            id="e_001",
            type="file_path",
            raw="src/app.py",
            canonical="src/app.py",
            in_focus=True,
        )
        pd = _make_path_decision(
            entity_id="e_001", status="allowed", resolved_rel="src/app.py"
        )
        # 5 items in evidence = budget exhausted
        history = [
            EvidenceRecord(
                entity_key=f"file_path:file_{i}.py",
                template_id="probe.file_repo_fact",
                turn=i,
            )
            for i in range(5)
        ]
        req = _make_turn_request()

        candidates, _, _ = match_templates([entity], [pd], history, req, ctx)
        probe_candidates = [c for c in candidates if c.template_id.startswith("probe.")]
        assert len(probe_candidates) == 0

    def test_clarifiers_still_work_when_budget_exhausted(self) -> None:
        from context_injection.templates import match_templates

        ctx = _make_ctx()
        entity = _make_entity(
            id="e_001",
            type="file_hint",
            tier=2,
            raw="some file",
            canonical="some file",
            confidence="low",
            in_focus=True,
        )
        history = [
            EvidenceRecord(
                entity_key=f"file_path:file_{i}.py",
                template_id="probe.file_repo_fact",
                turn=i,
            )
            for i in range(5)
        ]
        req = _make_turn_request()

        candidates, _, _ = match_templates([entity], [], history, req, ctx)
        assert len(candidates) == 1
        assert candidates[0].template_id == "clarify.file_path"


# ============================================================
# Path decision gating
# ============================================================


class TestPathDecisionGating:
    """Only entities with status=allowed get probe templates."""

    def test_denied_entity_no_probe(self) -> None:
        from context_injection.templates import match_templates

        ctx = _make_ctx()
        entity = _make_entity(
            id="e_001",
            type="file_path",
            raw=".env",
            canonical=".env",
            in_focus=True,
        )
        pd = _make_path_decision(
            entity_id="e_001",
            status="denied",
            user_rel=".env",
            deny_reason="file matches denylist",
        )
        req = _make_turn_request()

        candidates, _, _ = match_templates([entity], [pd], [], req, ctx)
        probe_candidates = [c for c in candidates if c.template_id.startswith("probe.")]
        assert len(probe_candidates) == 0

    def test_not_tracked_entity_no_probe(self) -> None:
        from context_injection.templates import match_templates

        ctx = _make_ctx()
        entity = _make_entity(
            id="e_001",
            type="file_path",
            raw="build/output.js",
            canonical="build/output.js",
            in_focus=True,
        )
        pd = _make_path_decision(
            entity_id="e_001", status="not_tracked", user_rel="build/output.js"
        )
        req = _make_turn_request()

        candidates, _, _ = match_templates([entity], [pd], [], req, ctx)
        probe_candidates = [c for c in candidates if c.template_id.startswith("probe.")]
        assert len(probe_candidates) == 0


# ============================================================
# Edge cases
# ============================================================


class TestEdgeCases:
    def test_empty_entities_returns_empty(self) -> None:
        from context_injection.templates import match_templates

        ctx = _make_ctx()
        req = _make_turn_request()
        candidates, deduped, _ = match_templates([], [], [], req, ctx)
        assert candidates == []
        assert deduped == []

    def test_multiple_scout_options_different_ids(self) -> None:
        """Multiple candidates should have unique IDs."""
        from context_injection.templates import match_templates

        ctx = _make_ctx()
        e1 = _make_entity(
            id="e_001", type="file_path", raw="src/app.py", canonical="src/app.py"
        )
        e2 = _make_entity(
            id="e_002", type="symbol", raw="os.path.join", canonical="os.path.join"
        )
        pd1 = _make_path_decision(
            entity_id="e_001", status="allowed", resolved_rel="src/app.py"
        )
        req = _make_turn_request()

        candidates, _, _ = match_templates([e1, e2], [pd1], [], req, ctx)
        tc_ids = [c.id for c in candidates]
        assert len(tc_ids) == len(set(tc_ids)), "Template candidate IDs must be unique"

        so_ids = []
        for c in candidates:
            for opt in c.scout_options:
                so_ids.append(opt.id)
        assert len(so_ids) == len(set(so_ids)), "Scout option IDs must be unique"

    def test_rank_factors_is_human_readable(self) -> None:
        from context_injection.templates import match_templates

        ctx = _make_ctx()
        entity = _make_entity(
            id="e_001",
            type="file_path",
            raw="src/app.py",
            canonical="src/app.py",
        )
        pd = _make_path_decision(
            entity_id="e_001", status="allowed", resolved_rel="src/app.py"
        )
        req = _make_turn_request()

        candidates, _, _ = match_templates([entity], [pd], [], req, ctx)
        assert len(candidates) >= 1
        # rank_factors should be a non-empty string
        assert isinstance(candidates[0].rank_factors, str)
        assert len(candidates[0].rank_factors) > 0
