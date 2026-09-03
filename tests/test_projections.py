from fpl_agent.analysis.projections import (
    PlayerProjection,
    calculate_expected_points,
    project_player,
)


def test_expected_points_projection() -> None:
    result = calculate_expected_points(
        points_per_game=6.0,
        points_per_90=6.0,
        xgi_per_90=0.5,
        fixture_difficulty=3.0,
    )

    assert result == 4.9


def test_easy_fixture_increases_projection() -> None:
    easy = calculate_expected_points(
        points_per_game=5.0,
        points_per_90=5.0,
        xgi_per_90=0.5,
        fixture_difficulty=1.0,
    )

    hard = calculate_expected_points(
        points_per_game=5.0,
        points_per_90=5.0,
        xgi_per_90=0.5,
        fixture_difficulty=5.0,
    )

    assert easy > hard


def test_projection_is_deterministic() -> None:
    first = calculate_expected_points(
        points_per_game=5.5,
        points_per_90=5.8,
        xgi_per_90=0.7,
        fixture_difficulty=2.0,
    )

    second = calculate_expected_points(
        points_per_game=5.5,
        points_per_90=5.8,
        xgi_per_90=0.7,
        fixture_difficulty=2.0,
    )

    assert first == second


def test_project_player() -> None:
    result = project_player(
        player_id=10,
        points_per_game=6.0,
        points_per_90=6.0,
        xgi_per_90=0.5,
        fixture_difficulty=3.0,
    )

    assert isinstance(result, PlayerProjection)
    assert result.player_id == 10
    assert result.expected_points == 4.9
    assert result.base_points == 4.8
    assert result.xgi_component == 0.1
    assert result.fixture_component == 1.0


def test_zero_inputs() -> None:
    result = calculate_expected_points(
        points_per_game=0.0,
        points_per_90=0.0,
        xgi_per_90=0.0,
        fixture_difficulty=3.0,
    )

    assert result == 0.0


def test_fixture_multiplier_has_lower_bound() -> None:
    result = calculate_expected_points(
        points_per_game=10.0,
        points_per_90=10.0,
        xgi_per_90=1.0,
        fixture_difficulty=100.0,
    )

    assert result == 4.1


def test_fixture_multiplier_has_upper_bound() -> None:
    result = calculate_expected_points(
        points_per_game=10.0,
        points_per_90=10.0,
        xgi_per_90=1.0,
        fixture_difficulty=-100.0,
    )

    assert result == 12.3
