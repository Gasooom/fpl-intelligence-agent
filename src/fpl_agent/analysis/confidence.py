from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SampleConfidence:
    """Confidence derived from the available player-minute sample."""

    minutes: int
    score: float
    level: str


def calculate_sample_confidence(minutes: int) -> SampleConfidence:
    """Calculate deterministic confidence from observed minutes.

    Confidence measures how much playing-time evidence is available.
    It does not represent player availability or injury risk.
    """
    if minutes <= 0:
        score = 0.0
    elif minutes < 450:
        score = 0.25
    elif minutes < 900:
        score = 0.5
    elif minutes < 1500:
        score = 0.75
    else:
        score = 1.0

    if score >= 0.75:
        level = "high"
    elif score >= 0.5:
        level = "medium"
    else:
        level = "low"

    return SampleConfidence(
        minutes=minutes,
        score=score,
        level=level,
    )