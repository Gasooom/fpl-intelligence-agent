from fpl_agent.analysis.form_trends import (
    FormTrend,
    calculate_form_average,
    calculate_form_trend,
)


def test_improving_form() -> None:
    result = calculate_form_trend(6.5, 5.0)

    assert isinstance(result, FormTrend)
    assert result.current_form == 6.5
    assert result.previous_form == 5.0
    assert result.change == 1.5
    assert result.direction == "improving"


def test_declining_form() -> None:
    result = calculate_form_trend(3.5, 5.0)

    assert result.change == -1.5
    assert result.direction == "declining"


def test_stable_form() -> None:
    result = calculate_form_trend(5.0, 5.0)

    assert result.change == 0.0
    assert result.direction == "stable"


def test_form_average() -> None:
    result = calculate_form_average([4.0, 5.0, 6.0])

    assert result == 5.0


def test_empty_form_average() -> None:
    assert calculate_form_average([]) == 0.0