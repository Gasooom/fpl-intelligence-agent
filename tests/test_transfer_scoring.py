from fpl_agent.analysis.transfer_scoring import (
    TransferCandidateScore,
    calculate_transfer_score,
    score_transfer_candidate,
)


def test_transfer_score() -> None:
    result = calculate_transfer_score(
        expected_points=6.0,
        form=5.0,
        fixture_difficulty=2.0,
        price=6.0,
    )

    assert isinstance(result, TransferCandidateScore)
    assert result.score == 5.7
    assert result.projection_score == 3.0
    assert result.form_score == 1.0
    assert result.fixture_score == 0.8
    assert result.value_score == 0.1


def test_easier_fixture_improves_score() -> None:
    easy = calculate_transfer_score(
        expected_points=6.0,
        form=5.0,
        fixture_difficulty=1.0,
        price=6.0,
    )

    hard = calculate_transfer_score(
        expected_points=6.0,
        form=5.0,
        fixture_difficulty=5.0,
        price=6.0,
    )

    assert easy.score > hard.score


def test_higher_projection_improves_score() -> None:
    high = calculate_transfer_score(
        expected_points=8.0,
        form=5.0,
        fixture_difficulty=3.0,
        price=6.0,
    )

    low = calculate_transfer_score(
        expected_points=4.0,
        form=5.0,
        fixture_difficulty=3.0,
        price=6.0,
    )

    assert high.score > low.score


def test_higher_form_improves_score() -> None:
    high = calculate_transfer_score(
        expected_points=6.0,
        form=8.0,
        fixture_difficulty=3.0,
        price=6.0,
    )

    low = calculate_transfer_score(
        expected_points=6.0,
        form=3.0,
        fixture_difficulty=3.0,
        price=6.0,
    )

    assert high.score > low.score


def test_zero_price_has_zero_value_score() -> None:
    result = calculate_transfer_score(
        expected_points=6.0,
        form=5.0,
        fixture_difficulty=3.0,
        price=0.0,
    )

    assert result.value_score == 0.0


def test_negative_inputs_do_not_create_negative_scores() -> None:
    result = calculate_transfer_score(
        expected_points=-5.0,
        form=-2.0,
        fixture_difficulty=10.0,
        price=6.0,
    )

    assert result.score == 0.0
    assert result.projection_score == 0.0
    assert result.form_score == 0.0
    assert result.fixture_score == 0.0


def test_score_transfer_candidate() -> None:
    result = score_transfer_candidate(
        player_id=123,
        expected_points=7.0,
        form=6.0,
        fixture_difficulty=2.0,
        price=7.0,
    )

    assert result.player_id == 123
    assert isinstance(result, TransferCandidateScore)
    assert result.score > 0.0
