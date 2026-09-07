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


def test_captaincy_score_ranking_matches_ranking_by_doubled_expected_points() -> None:
    """Documents and locks in the chosen policy: captaincy_score
    optimizes for maximum expected doubled value. Doubling every
    candidate's expected_points equally (the FPL captain multiplier)
    is a monotonic transform, so ranking candidates by captaincy_score
    must always agree with ranking them by their would-be doubled
    points, for any pair that differs only in expected_points."""
    higher_projection = score_captaincy_candidate(
        player_id=1,
        expected_points=10.0,
        form=5.0,
        fixture_difficulty=3.0,
    )
    lower_projection = score_captaincy_candidate(
        player_id=2,
        expected_points=6.0,
        form=5.0,
        fixture_difficulty=3.0,
    )

    ranked_by_captaincy_score = higher_projection.score > lower_projection.score
    ranked_by_doubled_points = (10.0 * 2) > (6.0 * 2)

    assert ranked_by_captaincy_score == ranked_by_doubled_points is True
