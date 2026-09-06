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
    assert result.availability_risk == 0.0
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
    assert result.availability_risk == 0.0
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
    assert result.availability_risk == 0.0
    assert result.overall_risk == 0.35
    assert result.risk_level == "low"


def test_zero_minutes_are_high_minutes_risk() -> None:
    result = calculate_risk_signals(
        minutes=0,
        form=6.0,
        fixture_difficulty=2.0,
    )

    assert result.minutes_risk == 1.0
    assert result.availability_risk == 0.0
    assert result.overall_risk == 0.5
    assert result.risk_level == "medium"


def test_missing_availability_data_is_not_a_penalty() -> None:
    result = calculate_risk_signals(
        minutes=1000,
        form=7.0,
        fixture_difficulty=2.0,
        status="a",
        chance_of_playing=None,
    )

    assert result.availability_risk == 0.0
    assert result.overall_risk == 0.0
    assert result.risk_level == "low"


def test_high_chance_of_playing_has_no_availability_penalty() -> None:
    result = calculate_risk_signals(
        minutes=1000,
        form=7.0,
        fixture_difficulty=2.0,
        status="a",
        chance_of_playing=90,
    )

    assert result.availability_risk == 0.0
    assert result.overall_risk == 0.0


def test_doubtful_player_with_75_percent_chance_has_moderate_risk() -> None:
    result = calculate_risk_signals(
        minutes=1000,
        form=7.0,
        fixture_difficulty=2.0,
        status="d",
        chance_of_playing=75,
    )

    assert result.availability_risk == 0.5
    assert result.overall_risk == 0.15
    assert result.risk_level == "low"


def test_doubtful_player_with_50_percent_chance_has_high_availability_risk() -> None:
    result = calculate_risk_signals(
        minutes=1000,
        form=7.0,
        fixture_difficulty=2.0,
        status="d",
        chance_of_playing=50,
    )

    assert result.availability_risk == 0.8
    assert result.overall_risk == 0.24
    assert result.risk_level == "low"


def test_zero_chance_of_playing_is_unavailable() -> None:
    result = calculate_risk_signals(
        minutes=1000,
        form=7.0,
        fixture_difficulty=2.0,
        status="a",
        chance_of_playing=0,
    )

    assert result.availability_risk == 1.0
    assert result.overall_risk == 0.3


def test_injured_player_is_high_availability_risk() -> None:
    result = calculate_risk_signals(
        minutes=1000,
        form=7.0,
        fixture_difficulty=2.0,
        status="i",
        chance_of_playing=None,
    )

    assert result.availability_risk == 1.0
    assert result.overall_risk == 0.3


def test_suspended_player_is_high_availability_risk() -> None:
    result = calculate_risk_signals(
        minutes=1000,
        form=7.0,
        fixture_difficulty=2.0,
        status="s",
        chance_of_playing=None,
    )

    assert result.availability_risk == 1.0
    assert result.overall_risk == 0.3


def test_unavailable_status_is_high_availability_risk() -> None:
    result = calculate_risk_signals(
        minutes=1000,
        form=7.0,
        fixture_difficulty=2.0,
        status="u",
        chance_of_playing=None,
    )

    assert result.availability_risk == 1.0
    assert result.overall_risk == 0.3


def test_player_who_cannot_be_selected_is_unavailable() -> None:
    result = calculate_risk_signals(
        minutes=1000,
        form=7.0,
        fixture_difficulty=2.0,
        status="a",
        chance_of_playing=None,
        can_select=False,
    )

    assert result.availability_risk == 1.0
    assert result.overall_risk == 0.3


def test_removed_player_is_unavailable() -> None:
    result = calculate_risk_signals(
        minutes=1000,
        form=7.0,
        fixture_difficulty=2.0,
        status="a",
        chance_of_playing=None,
        removed=True,
    )

    assert result.availability_risk == 1.0
    assert result.overall_risk == 0.3