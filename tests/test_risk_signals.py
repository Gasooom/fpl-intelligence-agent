from fpl_agent.analysis.risk_signals import (
    RiskSignal,
    calculate_risk_signals,
)


def test_low_risk_player() -> None:
    result = calculate_risk_signals(
        minutes=1000,
        form=7.0,
        fixture_difficulty=2.0,
    )

    assert isinstance(result, RiskSignal)
    assert result.minutes_risk == 0.0
    assert result.form_uncertainty == 0.0
    assert result.fixture_risk == 0.0
    assert result.overall_risk == 0.0
    assert result.risk_level == "low"


def test_minutes_risk_increases_for_low_minutes() -> None:
    established = calculate_risk_signals(
        minutes=1000,
        form=6.0,
        fixture_difficulty=2.0,
    )

    limited = calculate_risk_signals(
        minutes=300,
        form=6.0,
        fixture_difficulty=2.0,
    )

    assert limited.minutes_risk > established.minutes_risk
    assert limited.overall_risk > established.overall_risk


def test_form_uncertainty_increases_for_poor_form() -> None:
    good = calculate_risk_signals(
        minutes=1000,
        form=7.0,
        fixture_difficulty=2.0,
    )

    poor = calculate_risk_signals(
        minutes=1000,
        form=1.0,
        fixture_difficulty=2.0,
    )

    assert poor.form_uncertainty > good.form_uncertainty
    assert poor.overall_risk > good.overall_risk


def test_fixture_risk_increases_for_harder_fixture() -> None:
    easy = calculate_risk_signals(
        minutes=1000,
        form=6.0,
        fixture_difficulty=2.0,
    )

    hard = calculate_risk_signals(
        minutes=1000,
        form=6.0,
        fixture_difficulty=5.0,
    )

    assert hard.fixture_risk > easy.fixture_risk
    assert hard.overall_risk > easy.overall_risk


def test_high_risk_player() -> None:
    result = calculate_risk_signals(
        minutes=200,
        form=1.0,
        fixture_difficulty=5.0,
    )

    assert result.minutes_risk == 0.8
    assert result.form_uncertainty == 1.0
    assert result.fixture_risk == 1.0
    assert result.overall_risk == 0.8
    assert result.risk_level == "high"


def test_medium_risk_player() -> None:
    result = calculate_risk_signals(
        minutes=700,
        form=5.0,
        fixture_difficulty=3.0,
    )

    assert result.minutes_risk == 0.4
    assert result.form_uncertainty == 0.3
    assert result.fixture_risk == 0.4
    assert result.overall_risk == 0.35
    assert result.risk_level == "low"


def test_zero_minutes_are_high_minutes_risk() -> None:
    result = calculate_risk_signals(
        minutes=0,
        form=6.0,
        fixture_difficulty=2.0,
    )

    assert result.minutes_risk == 1.0
    assert result.overall_risk == 0.5
    assert result.risk_level == "medium"