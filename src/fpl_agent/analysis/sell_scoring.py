from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SellScore:
    """Deterministic sell-candidate score.

    Higher scores indicate stronger sell candidates. Each component is
    an independent, transparent penalty so the total score can always
    be explained in terms of the metrics that produced it.
    """

    player_id: int
    score: float
    risk_penalty: float
    low_projection_penalty: float
    difficult_fixture_penalty: float
    availability_penalty: float
    low_confidence_penalty: float


def calculate_sell_score(
    expected_points: float,
    overall_risk: float,
    availability_risk: float,
    sample_confidence: float,
    fixture_difficulty: float,
) -> SellScore:
    """Calculate a deterministic sell-candidate score.

    Mirrors the additive, weighted-component style used by
    ``captaincy_scoring`` and ``transfer_scoring``: each signal
    contributes an independent, non-negative penalty, and higher
    penalties push a player higher up the sell list.

    High overall risk, poor projected output, difficult fixtures,
    availability doubts, and low sample confidence each increase the
    score on their own; none of them substitute for one another.
    """
    risk_penalty = round(max(0.0, overall_risk) * 4.0, 2)

    low_projection_penalty = round(
        max(0.0, 6.0 - expected_points) * 0.5,
        2,
    )

    difficult_fixture_penalty = round(
        max(0.0, fixture_difficulty - 3.0) * 0.5,
        2,
    )

    availability_penalty = round(
        max(0.0, availability_risk) * 3.0,
        2,
    )

    low_confidence_penalty = round(
        max(0.0, 0.5 - sample_confidence) * 2.0,
        2,
    )

    score = round(
        risk_penalty
        + low_projection_penalty
        + difficult_fixture_penalty
        + availability_penalty
        + low_confidence_penalty,
        2,
    )

    return SellScore(
        player_id=0,
        score=score,
        risk_penalty=risk_penalty,
        low_projection_penalty=low_projection_penalty,
        difficult_fixture_penalty=difficult_fixture_penalty,
        availability_penalty=availability_penalty,
        low_confidence_penalty=low_confidence_penalty,
    )


def score_sell_candidate(
    player_id: int,
    expected_points: float,
    overall_risk: float,
    availability_risk: float,
    sample_confidence: float,
    fixture_difficulty: float,
) -> SellScore:
    """Build a deterministic sell-candidate score for one player."""
    result = calculate_sell_score(
        expected_points=expected_points,
        overall_risk=overall_risk,
        availability_risk=availability_risk,
        sample_confidence=sample_confidence,
        fixture_difficulty=fixture_difficulty,
    )

    return SellScore(
        player_id=player_id,
        score=result.score,
        risk_penalty=result.risk_penalty,
        low_projection_penalty=result.low_projection_penalty,
        difficult_fixture_penalty=result.difficult_fixture_penalty,
        availability_penalty=result.availability_penalty,
        low_confidence_penalty=result.low_confidence_penalty,
    )
