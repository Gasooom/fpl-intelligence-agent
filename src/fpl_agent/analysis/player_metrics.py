from __future__ import annotations

from dataclasses import dataclass

from fpl_agent.data.models import Player
from fpl_agent.data.transform import (
    player_assists_per_90,
    player_goals_per_90,
    player_points_per_90,
    player_price,
    player_xgi_per_90,
)


@dataclass(frozen=True)
class PlayerMetrics:
    """Deterministic performance metrics for an FPL player."""

    player_id: int
    web_name: str
    price: float

    total_points: int
    minutes: int
    points_per_game: float

    points_per_90: float
    goals_per_90: float
    assists_per_90: float
    xgi_per_90: float

    form: float
    ownership_percent: float


def calculate_player_metrics(player: Player) -> PlayerMetrics:
    """Calculate deterministic performance metrics from FPL player data."""
    return PlayerMetrics(
        player_id=player.id,
        web_name=player.web_name,
        price=player_price(player.now_cost),
        total_points=player.total_points,
        minutes=player.minutes,
        points_per_game=float(player.points_per_game),
        points_per_90=player_points_per_90(
            player.total_points,
            player.minutes,
        ),
        goals_per_90=player_goals_per_90(
            player.goals_scored,
            player.minutes,
        ),
        assists_per_90=player_assists_per_90(
            player.assists,
            player.minutes,
        ),
        xgi_per_90=player_xgi_per_90(
            player.expected_goals,
            player.expected_assists,
            player.minutes,
        ),
        form=float(player.form),
        ownership_percent=float(player.selected_by_percent),
    )