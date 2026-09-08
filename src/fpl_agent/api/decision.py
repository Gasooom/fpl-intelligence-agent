from __future__ import annotations

from fpl_agent.api.schemas import (
    BuyCandidateResponse,
    EvidenceBasisResponse,
    EvidenceResponse,
    GameweekDecisionResponse,
    PlayerDecisionResponse,
    SellCandidateResponse,
    SquadDecisionResponse,
    TransferRecommendationResponse,
)
from fpl_agent.decisions.gameweek_decision import (
    EvidenceBasis,
    GameweekDecision,
    RecommendationEvidence,
)
from fpl_agent.decisions.squad_analysis import (
    SquadDecision,
    SquadPlayerAnalysis,
)
from fpl_agent.decisions.transfer_analysis import (
    BuyCandidate,
    SellCandidate,
    TransferPair,
)


def _player_to_response(
    player: SquadPlayerAnalysis,
    captain_player_id: int,
) -> PlayerDecisionResponse:
    """Convert an internal deterministic analysis to an API response.

    `captain_player_id` is the id of whichever player the deterministic
    engine actually selected as captain for this decision - it is the
    only input that decides whether the FPL 2x multiplier applies to
    `effective_points`. See PlayerDecisionResponse.effective_points for
    the exact rule.
    """
    is_captain = player.player_id == captain_player_id

    return PlayerDecisionResponse(
        player_id=player.player_id,
        web_name=player.web_name,
        position_type=player.position_type,
        team_id=player.team_id,
        price=player.price,
        form=player.form,
        points_per_game=player.points_per_game,
        points_per_90=player.points_per_90,
        xgi_per_90=player.xgi_per_90,
        fixture_difficulty=player.fixture_difficulty,
        expected_points=player.expected_points,
        minutes_risk=player.minutes_risk,
        availability_risk=player.availability_risk,
        overall_risk=player.overall_risk,
        risk_level=player.risk_level,
        captaincy_score=player.captaincy_score,
        effective_points=(
            round(player.expected_points * 2, 2) if is_captain else player.expected_points
        ),
    )


def squad_decision_to_response(
    decision: SquadDecision,
) -> SquadDecisionResponse:
    """Convert a deterministic squad decision to an API response."""
    captain_player_id = decision.captain.player_id

    return SquadDecisionResponse(
        starting_xi=[
            _player_to_response(player, captain_player_id)
            for player in decision.starting_xi
        ],
        bench=[
            _player_to_response(player, captain_player_id)
            for player in decision.bench
        ],
        captain=_player_to_response(decision.captain, captain_player_id),
        vice_captain=_player_to_response(decision.vice_captain, captain_player_id),
        must_play=[
            _player_to_response(player, captain_player_id)
            for player in decision.must_play
        ],
    )


def _sell_candidate_to_response(
    candidate: SellCandidate,
) -> SellCandidateResponse:
    """Convert a deterministic sell candidate to an API response."""
    return SellCandidateResponse(
        player_id=candidate.player_id,
        web_name=candidate.web_name,
        position_type=candidate.position_type,
        team_id=candidate.team_id,
        price=candidate.price,
        expected_points=candidate.expected_points,
        form=candidate.form,
        fixture_difficulty=candidate.fixture_difficulty,
        overall_risk=candidate.overall_risk,
        availability_risk=candidate.availability_risk,
        risk_level=candidate.risk_level,
        sample_confidence=candidate.sample_confidence,
        selection_score=candidate.selection_score,
        score=candidate.sell_score.score,
        rank=candidate.rank,
        reasons=candidate.reasons,
    )


def _buy_candidate_to_response(
    candidate: BuyCandidate,
) -> BuyCandidateResponse:
    """Convert a deterministic buy candidate to an API response."""
    return BuyCandidateResponse(
        player_id=candidate.player_id,
        web_name=candidate.web_name,
        position_type=candidate.position_type,
        team_id=candidate.team_id,
        price=candidate.price,
        expected_points=candidate.expected_points,
        form=candidate.form,
        fixture_difficulty=candidate.fixture_difficulty,
        overall_risk=candidate.overall_risk,
        availability_risk=candidate.availability_risk,
        risk_level=candidate.risk_level,
        sample_confidence=candidate.sample_confidence,
        selection_score=candidate.selection_score,
        value_score=candidate.value_score,
        rank=candidate.rank,
        reasons=candidate.reasons,
    )


def _transfer_pair_to_response(
    pair: TransferPair,
) -> TransferRecommendationResponse:
    """Convert a deterministic transfer pair to an API response."""
    return TransferRecommendationResponse(
        sell=_sell_candidate_to_response(pair.sell),
        buy=_buy_candidate_to_response(pair.buy),
        net_improvement=pair.net_improvement,
        risk_change=pair.risk_change,
        price_change=pair.price_change,
        within_budget=pair.within_budget,
        priority=pair.priority,
        reasons=pair.reasons,
        expected_point_gain=pair.expected_point_gain,
        hit_cost=pair.hit_cost,
        net_value=pair.net_value,
    )


def _evidence_to_response(
    evidence: RecommendationEvidence,
) -> EvidenceResponse:
    """Convert structured decision evidence to an API response."""
    return EvidenceResponse(
        player_id=evidence.player_id,
        decision=evidence.decision,
        score=evidence.score,
        reasons=evidence.reasons,
    )


def _evidence_basis_to_response(basis: EvidenceBasis) -> EvidenceBasisResponse:
    """Copy the confidence basis across field for field.

    Nothing is recomputed, re-rounded, or re-classified here - the
    deterministic engine already decided every one of these values.
    """
    return EvidenceBasisResponse(
        level=basis.level,
        average_sample_confidence=basis.average_sample_confidence,
        medium_threshold=basis.medium_threshold,
        high_threshold=basis.high_threshold,
        players_considered=basis.players_considered,
        limited_sample_players=basis.limited_sample_players,
        partial_sample_players=basis.partial_sample_players,
        full_sample_players=basis.full_sample_players,
        limited_sample_minutes=basis.limited_sample_minutes,
    )


def gameweek_decision_to_response(
    decision: GameweekDecision,
) -> GameweekDecisionResponse:
    """Convert the unified deterministic gameweek decision to an API response."""
    captain_player_id = decision.captain.player_id

    return GameweekDecisionResponse(
        gameweek=decision.gameweek,
        generated_at=decision.generated_at,
        decision_engine_version=decision.decision_engine_version,
        data_source=decision.data_source,
        starting_xi=[
            _player_to_response(player, captain_player_id)
            for player in decision.starting_xi
        ],
        bench=[
            _player_to_response(player, captain_player_id)
            for player in decision.bench
        ],
        captain=_player_to_response(decision.captain, captain_player_id),
        vice_captain=_player_to_response(decision.vice_captain, captain_player_id),
        must_play=[
            _player_to_response(player, captain_player_id)
            for player in decision.must_play
        ],
        sell_candidates=[
            _sell_candidate_to_response(candidate)
            for candidate in decision.sell_candidates
        ],
        buy_candidates=[
            _buy_candidate_to_response(candidate)
            for candidate in decision.buy_candidates
        ],
        transfer_recommendations=[
            _transfer_pair_to_response(pair)
            for pair in decision.transfer_recommendations
        ],
        transfer_count=decision.transfer_count,
        best_transfer=(
            _transfer_pair_to_response(decision.best_transfer)
            if decision.best_transfer is not None
            else None
        ),
        free_transfers_available=decision.free_transfers_available,
        in_the_bank=decision.in_the_bank,
        starting_xi_expected_points=decision.starting_xi_expected_points,
        projected_gameweek_points=decision.projected_gameweek_points,
        confidence=decision.confidence,
        evidence_basis=_evidence_basis_to_response(decision.evidence_basis),
        decision_summary=decision.decision_summary,
        evidence=[
            _evidence_to_response(item)
            for item in decision.evidence
        ],
    )