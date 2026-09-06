from fpl_agent.analysis.sell_scoring import (
    SellScore,
    calculate_sell_score,
    score_sell_candidate,
)


def test_sell_score_breakdown() -> None:
    result = calculate_sell_score(
        expected_points=6.0,
        overall_risk=0.2,
        availability_risk=0.0,
        sample_confidence=1.0,
        fixture_difficulty=2.0,
    )

    assert isinstance(result, SellScore)
    assert result.risk_penalty == 0.8
    assert result.low_projection_penalty == 0.0
    assert result.difficult_fixture_penalty == 0.0
    assert result.availability_penalty == 0.0
    assert result.low_confidence_penalty == 0.0
    assert result.score == 0.8


def test_higher_risk_increases_score() -> None:
    low_risk = calculate_sell_score(
        expected_points=6.0,
        overall_risk=0.1,
        availability_risk=0.0,
        sample_confidence=1.0,
        fixture_difficulty=2.0,
    )

    high_risk = calculate_sell_score(
        expected_points=6.0,
        overall_risk=0.9,
        availability_risk=0.0,
        sample_confidence=1.0,
        fixture_difficulty=2.0,
    )

    assert high_risk.score > low_risk.score
    assert high_risk.risk_penalty > low_risk.risk_penalty


def test_lower_expected_points_increases_score() -> None:
    strong_projection = calculate_sell_score(
        expected_points=8.0,
        overall_risk=0.2,
        availability_risk=0.0,
        sample_confidence=1.0,
        fixture_difficulty=2.0,
    )

    weak_projection = calculate_sell_score(
        expected_points=1.0,
        overall_risk=0.2,
        availability_risk=0.0,
        sample_confidence=1.0,
        fixture_difficulty=2.0,
    )

    assert weak_projection.score > strong_projection.score
    assert weak_projection.low_projection_penalty > 0.0
    assert strong_projection.low_projection_penalty == 0.0


def test_difficult_fixture_increases_score() -> None:
    easy_fixture = calculate_sell_score(
        expected_points=6.0,
        overall_risk=0.2,
        availability_risk=0.0,
        sample_confidence=1.0,
        fixture_difficulty=2.0,
    )

    hard_fixture = calculate_sell_score(
        expected_points=6.0,
        overall_risk=0.2,
        availability_risk=0.0,
        sample_confidence=1.0,
        fixture_difficulty=5.0,
    )

    assert hard_fixture.score > easy_fixture.score
    assert hard_fixture.difficult_fixture_penalty > 0.0
    assert easy_fixture.difficult_fixture_penalty == 0.0


def test_availability_risk_increases_score() -> None:
    available = calculate_sell_score(
        expected_points=6.0,
        overall_risk=0.2,
        availability_risk=0.0,
        sample_confidence=1.0,
        fixture_difficulty=2.0,
    )

    doubtful = calculate_sell_score(
        expected_points=6.0,
        overall_risk=0.2,
        availability_risk=0.8,
        sample_confidence=1.0,
        fixture_difficulty=2.0,
    )

    assert doubtful.score > available.score
    assert doubtful.availability_penalty > 0.0


def test_low_confidence_increases_score() -> None:
    confident = calculate_sell_score(
        expected_points=6.0,
        overall_risk=0.2,
        availability_risk=0.0,
        sample_confidence=1.0,
        fixture_difficulty=2.0,
    )

    unproven = calculate_sell_score(
        expected_points=6.0,
        overall_risk=0.2,
        availability_risk=0.0,
        sample_confidence=0.0,
        fixture_difficulty=2.0,
    )

    assert unproven.score > confident.score
    assert unproven.low_confidence_penalty > 0.0
    assert confident.low_confidence_penalty == 0.0


def test_negative_inputs_do_not_create_negative_penalties() -> None:
    result = calculate_sell_score(
        expected_points=20.0,
        overall_risk=-1.0,
        availability_risk=-1.0,
        sample_confidence=2.0,
        fixture_difficulty=-5.0,
    )

    assert result.risk_penalty == 0.0
    assert result.low_projection_penalty == 0.0
    assert result.difficult_fixture_penalty == 0.0
    assert result.availability_penalty == 0.0
    assert result.low_confidence_penalty == 0.0
    assert result.score == 0.0


def test_score_sell_candidate_sets_player_id() -> None:
    result = score_sell_candidate(
        player_id=42,
        expected_points=3.0,
        overall_risk=0.6,
        availability_risk=0.5,
        sample_confidence=0.25,
        fixture_difficulty=4.0,
    )

    assert result.player_id == 42
    assert isinstance(result, SellScore)
    assert result.score > 0.0
