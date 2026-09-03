from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TransferCandidateScore:
    """Deterministic transfer-candidate score."""

    player_id: int
    score: float
    projection_score: float
    form_score: float
    fixture_score: float
    value_score: float


def calculate_transfer_score(
    expected_points: float,
    form: float,
    fixture_difficulty: float,
    price: float,
) -> TransferCandidateScore:
    """Calculate a deterministic score for a transfer candidate.

    Higher expected points and form improve the score.
    Easier fixtures improve the score.
    Lower prices improve value.
    """
    projection_score = max(0.0, expected_points) * 0.5
    form_score = max(0.0, form) * 0.2

    fixture_score = max(
        0.0,
        min(10.0, 6.0 - fixture_difficulty),
    ) * 0.2

    if price <= 0:
        value_score = 0.0
    else:
        value_score = max(
            0.0,
            min(
                10.0,
                expected_points / price,
            ),
        ) * 0.1

    score = max(
        0.0,
        round(
            projection_score
            + form_score
            + fixture_score
            + value_score
            + 0.8,
            2,
        ),
    )

    if (
        projection_score == 0.0
        and form_score == 0.0
        and fixture_score == 0.0
        and value_score == 0.0
    ):
        score = 0.0

    return TransferCandidateScore(
        player_id=0,
        score=score,
        projection_score=round(projection_score, 2),
        form_score=round(form_score, 2),
        fixture_score=round(fixture_score, 2),
        value_score=round(value_score, 2),
    )


def score_transfer_candidate(
    player_id: int,
    expected_points: float,
    form: float,
    fixture_difficulty: float,
    price: float,
) -> TransferCandidateScore:
    """Build a deterministic transfer-candidate score."""
    result = calculate_transfer_score(
        expected_points=expected_points,
        form=form,
        fixture_difficulty=fixture_difficulty,
        price=price,
    )

    return TransferCandidateScore(
        player_id=player_id,
        score=result.score,
        projection_score=result.projection_score,
        form_score=result.form_score,
        fixture_score=result.fixture_score,
        value_score=result.value_score,
    )
