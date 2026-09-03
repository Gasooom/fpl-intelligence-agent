from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskSignal:
    """Deterministic risk and uncertainty signals for an FPL decision."""

    minutes_risk: float
    form_uncertainty: float
    fixture_risk: float
    overall_risk: float
    risk_level: str


def calculate_risk_signals(
    minutes: int,
    form: float,
    fixture_difficulty: float,
) -> RiskSignal:
    """Calculate deterministic risk and uncertainty signals.

    Lower expected minutes increase minutes risk.
    Lower form increases form uncertainty.
    Harder fixtures increase fixture risk.
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

    overall_risk = round(
        (
            minutes_risk * 0.5
            + form_uncertainty * 0.1
            + fixture_risk * 0.3
        ),
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
        overall_risk=overall_risk,
        risk_level=risk_level,
    )