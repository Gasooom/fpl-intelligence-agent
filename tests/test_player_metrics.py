from fpl_agent.analysis.player_metrics import (
    PlayerMetrics,
    calculate_player_metrics,
)
from fpl_agent.data.models import Player


def make_player() -> Player:
    return Player(
        id=1,
        first_name="Test",
        second_name="Player",
        web_name="Test Player",
        team=1,
        element_type=3,
        now_cost=55,
        total_points=100,
        minutes=1000,
        goals_scored=10,
        assists=5,
        clean_sheets=8,
        goals_conceded=10,
        own_goals=0,
        penalties_saved=0,
        penalties_missed=0,
        yellow_cards=1,
        red_cards=0,
        saves=0,
        bonus=10,
        form="5.0",
        points_per_game="5.0",
        selected_by_percent="10.0",
        transfers_in=100,
        transfers_out=50,
        expected_goals="5.0",
        expected_assists="3.0",
        expected_goal_involvements="8.0",
        expected_goals_conceded="10.0",
        influence="100.0",
        creativity="100.0",
        threat="100.0",
        ict_index="100.0",
    )


def test_calculate_player_metrics() -> None:
    metrics = calculate_player_metrics(make_player())

    assert isinstance(metrics, PlayerMetrics)
    assert metrics.player_id == 1
    assert metrics.web_name == "Test Player"
    assert metrics.price == 5.5
    assert metrics.total_points == 100
    assert metrics.minutes == 1000
    assert metrics.points_per_game == 5.0
    assert metrics.points_per_90 == 9.0
    assert metrics.goals_per_90 == 0.9
    assert metrics.assists_per_90 == 0.45
    assert metrics.xgi_per_90 == 0.72
    assert metrics.form == 5.0
    assert metrics.ownership_percent == 10.0