from fpl_agent.data.transform import (
    player_assists_per_90,
    player_goals_per_90,
    player_points_per_90,
    player_price,
    player_xgi_per_90,
)


def test_player_price() -> None:
    assert player_price(55) == 5.5


def test_player_points_per_90() -> None:
    assert player_points_per_90(100, 1000) == 9.0


def test_player_points_per_90_zero_minutes() -> None:
    assert player_points_per_90(100, 0) == 0.0


def test_player_goals_per_90() -> None:
    assert player_goals_per_90(10, 1000) == 0.9


def test_player_goals_per_90_zero_minutes() -> None:
    assert player_goals_per_90(10, 0) == 0.0


def test_player_assists_per_90() -> None:
    assert player_assists_per_90(5, 1000) == 0.45


def test_player_assists_per_90_zero_minutes() -> None:
    assert player_assists_per_90(5, 0) == 0.0


def test_player_xgi_per_90() -> None:
    assert player_xgi_per_90("5.0", "3.0", 1000) == 0.72


def test_player_xgi_per_90_zero_minutes() -> None:
    assert player_xgi_per_90("5.0", "3.0", 0) == 0.0