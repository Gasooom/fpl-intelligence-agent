from __future__ import annotations

from fpl_agent.api.schemas import (
    PlayerDecisionResponse,
    SquadDecisionResponse,
)
from fpl_agent.decisions.squad_analysis import (
    SquadDecision,
    SquadPlayerAnalysis,
)


def _player_to_response(
    player: SquadPlayerAnalysis,
) -> PlayerDecisionResponse:
    """Convert an internal deterministic analysis to an API response."""
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
    )


def squad_decision_to_response(
    decision: SquadDecision,
) -> SquadDecisionResponse:
    """Convert a deterministic squad decision to an API response."""
    return SquadDecisionResponse(
        starting_xi=[
            _player_to_response(player)
            for player in decision.starting_xi
        ],
        bench=[
            _player_to_response(player)
            for player in decision.bench
        ],
        captain=_player_to_response(decision.captain),
        vice_captain=_player_to_response(decision.vice_captain),
        must_play=[
            _player_to_response(player)
            for player in decision.must_play
        ],
    )