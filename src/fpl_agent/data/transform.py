from __future__ import annotations

from fpl_agent.data.models import BootstrapData


def player_price(player_cost: int) -> float:
    """Convert FPL's tenths-of-a-million price into millions."""
    return player_cost / 10


def player_points_per_90(total_points: int, minutes: int) -> float:
    """Calculate points scored per 90 minutes."""
    if minutes <= 0:
        return 0.0

    return total_points / minutes * 90


def player_goals_per_90(goals_scored: int, minutes: int) -> float:
    """Calculate goals scored per 90 minutes."""
    if minutes <= 0:
        return 0.0

    return goals_scored / minutes * 90


def player_assists_per_90(assists: int, minutes: int) -> float:
    """Calculate assists per 90 minutes."""
    if minutes <= 0:
        return 0.0

    return assists / minutes * 90


def player_xgi_per_90(
    expected_goals: str,
    expected_assists: str,
    minutes: int,
) -> float:
    """Calculate expected goal involvements per 90 minutes."""
    if minutes <= 0:
        return 0.0

    xg = float(expected_goals)
    xa = float(expected_assists)

    return (xg + xa) / minutes * 90


def team_lookup(data: BootstrapData) -> dict[int, str]:
    """Create a team ID to team name lookup."""
    return {team.id: team.name for team in data.teams}


def player_team_name(
    data: BootstrapData,
    player_team_id: int,
) -> str:
    """Return the team name for a player."""
    teams = team_lookup(data)

    try:
        return teams[player_team_id]
    except KeyError as exc:
        raise ValueError(
            f"Unknown team ID: {player_team_id}"
        ) from exc