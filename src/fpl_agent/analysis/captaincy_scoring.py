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

    Expected points are the primary signal.
    Recent form provides supporting evidence.
    Easier fixtures improve the score.
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