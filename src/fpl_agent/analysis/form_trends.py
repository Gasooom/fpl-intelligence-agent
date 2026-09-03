from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FormTrend:
    """Deterministic form and trend signal."""

    current_form: float
    previous_form: float
    change: float
    direction: str


def calculate_form_trend(
    current_form: float,
    previous_form: float,
) -> FormTrend:
    """Calculate the change and direction between two form values."""
    change = current_form - previous_form

    if change > 0:
        direction = "improving"
    elif change < 0:
        direction = "declining"
    else:
        direction = "stable"

    return FormTrend(
        current_form=current_form,
        previous_form=previous_form,
        change=change,
        direction=direction,
    )


def calculate_form_average(forms: list[float]) -> float:
    """Calculate the average form over a sequence of values."""
    if not forms:
        return 0.0

    return sum(forms) / len(forms)