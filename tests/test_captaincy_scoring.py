from fpl_agent.analysis.captaincy_scoring import (
    CaptaincyScore,
    calculate_captaincy_score,
    score_captaincy_candidate,
)


def test_captaincy_score() -> None:
    result = calculate_captaincy_score(
        expected_points=8.0,
        form=6.0,
        fixture_difficulty=2.0,
    )

    assert isinstance(result, CaptaincyScore)
    assert result.projection_score == 4.8
    assert result.form_score == 1.2
    assert result.fixture_score == 0.8
    assert result.score == 6.8


def test_easier_fixture_improves_captaincy_score() -> None:
    easy = calculate_captaincy_score(
        expected_points=8.0,
        form=6.0,
        fixture_difficulty=1.0,
    )

    hard = calculate_captaincy_score(
        expected_points=8.0,
        form=6.0,
        fixture_difficulty=5.0,
    )

    assert easy.score > hard.score


def test_higher_projection_improves_captaincy_score() -> None:
    high = calculate_captaincy_score(
        expected_points=10.0,
        form=5.0,
        fixture_difficulty=3.0,
    )

    low = calculate_captaincy_score(
        expected_points=5.0,
        form=5.0,
        fixture_difficulty=3.0,
    )

    assert high.score > low.score


def test_higher_form_improves_captaincy_score() -> None:
    high = calculate_captaincy_score(
        expected_points=8.0,
        form=8.0,
        fixture_difficulty=3.0,
    )

    low = calculate_captaincy_score(
        expected_points=8.0,
        form=3.0,
        fixture_difficulty=3.0,
    )

    assert high.score > low.score


def test_negative_inputs_do_not_create_negative_scores() -> None:
    result = calculate_captaincy_score(
        expected_points=-5.0,
        form=-2.0,
        fixture_difficulty=10.0,
    )

    assert result.score == 0.0
    assert result.projection_score == 0.0
    assert result.form_score == 0.0
    assert result.fixture_score == 0.0


def test_score_captaincy_candidate() -> None:
    result = score_captaincy_candidate(
        player_id=123,
        expected_points=9.0,
        form=7.0,
        fixture_difficulty=2.0,
    )

    assert result.player_id == 123
    assert isinstance(result, CaptaincyScore)
    assert result.score > 0.0