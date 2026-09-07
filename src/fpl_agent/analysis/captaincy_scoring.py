from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CaptaincyScore:
    """Deterministic captaincy score."""

    player_id: int
    score: float
    projection_score: float
    form_score: float
    fixture_score: float


def calculate_captaincy_score(
    expected_points: float,
    form: float,
    fixture_difficulty: float,
) -> CaptaincyScore:
    """Calculate a deterministic captaincy score.

    Policy: maximum expected doubled value. The FPL captain multiplier
    (2x) is applied to whichever player is chosen - it does not change
    *who* that should be, since doubling every candidate's expected
    output equally is a monotonic transform that never changes their
    relative order. So this score ranks candidates by projected
    output (expected_points, weighted 0.6) as the dominant signal, with
    recent form (0.2) and fixture ease (0.2) as supporting evidence for
    how reliable that projection is over the coming gameweek.

    This is deliberately NOT risk-adjusted or variance-controlled: it
    has no overall_risk, sample_confidence, or minutes_risk term. A
    captaincy pick that also needs to weigh those against projection
    would be a different, explicitly risk-adjusted policy - this one
    is not that, and should not be read as one.
    """
    projection_score = max(0.0, expected_points) * 0.6
    form_score = max(0.0, form) * 0.2

    fixture_score = max(
        0.0,
        min(10.0, 6.0 - fixture_difficulty),
    ) * 0.2

    score = max(
        0.0,
        round(
            projection_score
            + form_score
            + fixture_score,
            2,
        ),
    )

    return CaptaincyScore(
        player_id=0,
        score=score,
        projection_score=round(projection_score, 2),
        form_score=round(form_score, 2),
        fixture_score=round(fixture_score, 2),
    )


def score_captaincy_candidate(
    player_id: int,
    expected_points: float,
    form: float,
    fixture_difficulty: float,
) -> CaptaincyScore:
    """Build a deterministic captaincy score for a player."""
    result = calculate_captaincy_score(
        expected_points=expected_points,
        form=form,
        fixture_difficulty=fixture_difficulty,
    )

    return CaptaincyScore(
        player_id=player_id,
        score=result.score,
        projection_score=result.projection_score,
        form_score=result.form_score,
        fixture_score=result.fixture_score,
    )