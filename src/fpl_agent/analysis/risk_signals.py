from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskSignal:
    """Deterministic risk and uncertainty signals for an FPL decision."""

    minutes_risk: float
    form_uncertainty: float
    fixture_risk: float
    availability_risk: float
    overall_risk: float
    risk_level: str


def _calculate_availability_risk(
    status: str | None,
    chance_of_playing: int | None,
    can_select: bool,
    removed: bool,
) -> float:
    """Calculate deterministic player availability risk."""

    if removed or not can_select:
        return 1.0

    if status in {"i", "s", "u"}:
        return 1.0

    if status == "d":
        if chance_of_playing is None:
            return 0.8
        if chance_of_playing <= 25:
            return 1.0
        if chance_of_playing <= 50:
            return 0.8
        if chance_of_playing <= 75:
            return 0.5
        return 0.25

    if chance_of_playing is None:
        return 0.0

    if chance_of_playing <= 0:
        return 1.0
    if chance_of_playing <= 25:
        return 0.8
    if chance_of_playing <= 50:
        return 0.6
    if chance_of_playing <= 75:
        return 0.4
    if chance_of_playing < 90:
        return 0.2

    return 0.0


def calculate_risk_signals(
    minutes: int,
    form: float,
    fixture_difficulty: float,
    status: str | None = None,
    chance_of_playing: int | None = None,
    can_select: bool = True,
    removed: bool = False,
) -> RiskSignal:
    """Calculate deterministic risk and uncertainty signals.

    Lower expected minutes increase minutes risk.
    Lower form increases form uncertainty.
    Harder fixtures increase fixture risk.
    Player availability contributes an independent availability risk.

    Missing availability data does not imply that a player is unavailable.
    """
    if minutes <= 0:
        minutes_risk = 1.0
    elif minutes < 450:
        minutes_risk = 0.8
    elif minutes < 900:
        minutes_risk = 0.4
    else:
        minutes_risk = 0.0

    if form < 2.0:
        form_uncertainty = 1.0
    elif form < 4.0:
        form_uncertainty = 0.6
    elif form < 6.0:
        form_uncertainty = 0.3
    else:
        form_uncertainty = 0.0

    if fixture_difficulty >= 5.0:
        fixture_risk = 1.0
    elif fixture_difficulty >= 4.0:
        fixture_risk = 0.7
    elif fixture_difficulty >= 3.0:
        fixture_risk = 0.4
    else:
        fixture_risk = 0.0

    availability_risk = _calculate_availability_risk(
        status=status,
        chance_of_playing=chance_of_playing,
        can_select=can_select,
        removed=removed,
    )

    base_risk = (
        minutes_risk * 0.5
        + form_uncertainty * 0.1
        + fixture_risk * 0.3
    )

    availability_penalty = availability_risk * 0.3

    overall_risk = round(
        min(1.0, base_risk + availability_penalty),
        2,
    )

    if overall_risk >= 0.7:
        risk_level = "high"
    elif overall_risk >= 0.4:
        risk_level = "medium"
    else:
        risk_level = "low"

    return RiskSignal(
        minutes_risk=minutes_risk,
        form_uncertainty=form_uncertainty,
        fixture_risk=fixture_risk,
        availability_risk=availability_risk,
        overall_risk=overall_risk,
        risk_level=risk_level,
    )