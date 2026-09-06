from __future__ import annotations

import pytest

from fpl_agent.analysis.confidence import (
    SampleConfidence,
    calculate_sample_confidence,
)


@pytest.mark.parametrize(
    ("minutes", "expected_score", "expected_level"),
    [
        (0, 0.0, "low"),
        (1, 0.25, "low"),
        (449, 0.25, "low"),
        (450, 0.5, "medium"),
        (899, 0.5, "medium"),
        (900, 0.75, "high"),
        (1499, 0.75, "high"),
        (1500, 1.0, "high"),
        (3000, 1.0, "high"),
    ],
)
def test_sample_confidence_boundaries(
    minutes: int,
    expected_score: float,
    expected_level: str,
) -> None:
    result = calculate_sample_confidence(minutes)

    assert isinstance(result, SampleConfidence)
    assert result.minutes == minutes
    assert result.score == expected_score
    assert result.level == expected_level


def test_negative_minutes_have_zero_confidence() -> None:
    result = calculate_sample_confidence(-1)

    assert result.score == 0.0
    assert result.level == "low"


def test_more_minutes_do_not_reduce_confidence() -> None:
    minute_samples = [0, 100, 450, 900, 1500, 2500]

    scores = [
        calculate_sample_confidence(minutes).score
        for minutes in minute_samples
    ]

    assert scores == sorted(scores)