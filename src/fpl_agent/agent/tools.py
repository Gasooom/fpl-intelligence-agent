from __future__ import annotations

from agents import RunContextWrapper, function_tool

from fpl_agent.agent.context import FPLAgentContext
from fpl_agent.analysis.captaincy_scoring import (
    score_captaincy_candidate,
)
from fpl_agent.analysis.fixture_analysis import (
    average_fixture_difficulty,
)
from fpl_agent.analysis.player_metrics import (
    calculate_player_metrics,
)
from fpl_agent.analysis.projections import project_player
from fpl_agent.analysis.risk_signals import calculate_risk_signals
from fpl_agent.analysis.transfer_scoring import score_transfer_candidate
from fpl_agent.data.models import Fixture, Player


@function_tool
def get_agent_capabilities() -> str:
    """Describe the capabilities currently available to the FPL agent."""
    return (
        "The FPL agent can work with FPL decision intelligence data, "
        "including player performance, fixture difficulty, form, projections, "
        "transfer scoring, captaincy scoring, and risk signals."
    )


@function_tool
def get_agent_context(
    context: RunContextWrapper[FPLAgentContext],
) -> str:
    """Return the runtime context available to the FPL agent."""
    return context.context.describe()


@function_tool
def get_player_performance(
    player: Player,
) -> dict[str, float | int | str]:
    """Calculate deterministic performance metrics for an FPL player."""
    metrics = calculate_player_metrics(player)

    return {
        "player_id": metrics.player_id,
        "web_name": metrics.web_name,
        "price": metrics.price,
        "total_points": metrics.total_points,
        "minutes": metrics.minutes,
        "points_per_game": metrics.points_per_game,
        "points_per_90": metrics.points_per_90,
        "goals_per_90": metrics.goals_per_90,
        "assists_per_90": metrics.assists_per_90,
        "xgi_per_90": metrics.xgi_per_90,
        "form": metrics.form,
        "ownership_percent": metrics.ownership_percent,
    }


@function_tool
def get_fixture_difficulty(
    fixtures: list[Fixture],
    team_id: int,
    limit: int | None = None,
) -> float:
    """Calculate the average upcoming fixture difficulty for a team."""
    return average_fixture_difficulty(
        fixtures=fixtures,
        team_id=team_id,
        limit=limit,
    )


@function_tool
def get_player_projection(
    player_id: int,
    points_per_game: float,
    points_per_90: float,
    xgi_per_90: float,
    fixture_difficulty: float,
) -> dict[str, float | int]:
    """Calculate a deterministic expected-points projection."""
    projection = project_player(
        player_id=player_id,
        points_per_game=points_per_game,
        points_per_90=points_per_90,
        xgi_per_90=xgi_per_90,
        fixture_difficulty=fixture_difficulty,
    )

    return {
        "player_id": projection.player_id,
        "expected_points": projection.expected_points,
        "base_points": projection.base_points,
        "xgi_component": projection.xgi_component,
        "fixture_component": projection.fixture_component,
    }


@function_tool
def get_transfer_candidate_score(
    player_id: int,
    expected_points: float,
    form: float,
    fixture_difficulty: float,
    price: float,
) -> dict[str, float | int]:
    """Calculate a deterministic transfer-candidate score."""
    result = score_transfer_candidate(
        player_id=player_id,
        expected_points=expected_points,
        form=form,
        fixture_difficulty=fixture_difficulty,
        price=price,
    )

    return {
        "player_id": result.player_id,
        "score": result.score,
        "projection_score": result.projection_score,
        "form_score": result.form_score,
        "fixture_score": result.fixture_score,
        "value_score": result.value_score,
    }


@function_tool
def get_captaincy_score(
    player_id: int,
    expected_points: float,
    form: float,
    fixture_difficulty: float,
) -> dict[str, float | int]:
    """Calculate a deterministic captaincy score."""
    result = score_captaincy_candidate(
        player_id=player_id,
        expected_points=expected_points,
        form=form,
        fixture_difficulty=fixture_difficulty,
    )

    return {
        "player_id": result.player_id,
        "score": result.score,
        "projection_score": result.projection_score,
        "form_score": result.form_score,
        "fixture_score": result.fixture_score,
    }


@function_tool
def get_risk_signals(
    minutes: int,
    form: float,
    fixture_difficulty: float,
) -> dict[str, float | str]:
    """Calculate deterministic risk and uncertainty signals."""
    result = calculate_risk_signals(
        minutes=minutes,
        form=form,
        fixture_difficulty=fixture_difficulty,
    )

    return {
        "minutes_risk": result.minutes_risk,
        "form_uncertainty": result.form_uncertainty,
        "fixture_risk": result.fixture_risk,
        "overall_risk": result.overall_risk,
        "risk_level": result.risk_level,
    }