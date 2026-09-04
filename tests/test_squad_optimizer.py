from __future__ import annotations

from fpl_agent.decisions.squad_analysis import (
    SquadPlayerAnalysis,
    select_starting_xi,
)


def make_player(
    player_id: int,
    position_type: int,
    team_id: int,
    expected_points: float,
) -> SquadPlayerAnalysis:
    return SquadPlayerAnalysis(
        player_id=player_id,
        web_name=f"Player {player_id}",
        position_type=position_type,
        team_id=team_id,
        price=10.0,
        form=5.0,
        points_per_game=5.0,
        points_per_90=6.0,
        xgi_per_90=0.5,
        fixture_difficulty=3.0,
        expected_points=expected_points,
        minutes_risk=0.0,
        overall_risk=0.0,
        risk_level="low",
        captaincy_score=expected_points,
    )


def test_optimizer_respects_three_player_team_limit() -> None:
    players = [
        make_player(1, 1, 1, 8.0),
        make_player(2, 1, 2, 5.0),
        make_player(3, 2, 1, 9.0),
        make_player(4, 2, 1, 8.0),
        make_player(5, 2, 4, 7.0),
        make_player(6, 2, 2, 6.0),
        make_player(7, 2, 3, 5.0),
        make_player(8, 3, 1, 9.0),
        make_player(9, 3, 1, 8.0),
        make_player(10, 3, 4, 7.0),
        make_player(11, 3, 2, 6.0),
        make_player(12, 3, 3, 5.0),
        make_player(13, 4, 1, 8.0),
        make_player(14, 4, 2, 7.0),
        make_player(15, 4, 3, 6.0),
    ]

    starting_xi = select_starting_xi(players)

    assert len(starting_xi) == 11

    team_counts: dict[int, int] = {}

    for player in starting_xi:
        team_counts[player.team_id] = (
            team_counts.get(player.team_id, 0) + 1
        )

    assert max(team_counts.values()) <= 3


def test_optimizer_returns_valid_formation() -> None:
    players = [
        make_player(1, 1, 1, 8.0),
        make_player(2, 1, 2, 5.0),
        make_player(3, 2, 1, 9.0),
        make_player(4, 2, 2, 8.0),
        make_player(5, 2, 3, 7.0),
        make_player(6, 2, 4, 6.0),
        make_player(7, 3, 1, 9.0),
        make_player(8, 3, 2, 8.0),
        make_player(9, 3, 3, 7.0),
        make_player(10, 3, 4, 6.0),
        make_player(11, 3, 5, 5.0),
        make_player(12, 4, 1, 8.0),
        make_player(13, 4, 2, 7.0),
        make_player(14, 4, 3, 6.0),
        make_player(15, 4, 4, 5.0),
    ]

    starting_xi = select_starting_xi(players)

    assert len(starting_xi) == 11

    assert sum(p.position_type == 1 for p in starting_xi) == 1
    assert sum(p.position_type == 2 for p in starting_xi) >= 3
    assert sum(p.position_type == 3 for p in starting_xi) >= 2
    assert sum(p.position_type == 4 for p in starting_xi) >= 1