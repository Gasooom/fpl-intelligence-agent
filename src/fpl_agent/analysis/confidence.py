from __future__ import annotations

from dataclasses import dataclass

# Minute thresholds separating the four sample bands. Named rather than
# inlined so the one place that decides "how much playing-time evidence
# is there?" can also be quoted verbatim by anything that needs to
# explain that decision, instead of a second copy drifting out of sync.
PARTIAL_SAMPLE_MINUTES = 450
ADEQUATE_SAMPLE_MINUTES = 900
FULL_SAMPLE_MINUTES = 1500

# Score thresholds separating the three level labels.
HIGH_SAMPLE_SCORE = 0.75
MEDIUM_SAMPLE_SCORE = 0.5

# Below this many observed minutes a player's own sample level is
# "low" - i.e. PARTIAL_SAMPLE_MINUTES restated as the boundary callers
# actually care about when describing a thin sample. Kept as a derived
# alias so the two can never disagree.
LIMITED_SAMPLE_MINUTES = PARTIAL_SAMPLE_MINUTES


@dataclass(frozen=True)
class SampleConfidence:
    """Confidence derived from the available player-minute sample."""

    minutes: int
    score: float
    level: str


def sample_confidence_level(score: float) -> str:
    """Map a sample-confidence score to its deterministic level label.

    Split out of `calculate_sample_confidence` so a caller holding an
    already-computed score (for example when summarising a whole
    starting XI) classifies it with exactly these thresholds rather
    than re-implementing them. Behaviour is unchanged.
    """
    if score >= HIGH_SAMPLE_SCORE:
        return "high"

    if score >= MEDIUM_SAMPLE_SCORE:
        return "medium"

    return "low"


def calculate_sample_confidence(minutes: int) -> SampleConfidence:
    """Calculate deterministic confidence from observed minutes.

    Confidence measures how much playing-time evidence is available.
    It does not represent player availability or injury risk.
    """
    if minutes <= 0:
        score = 0.0
    elif minutes < PARTIAL_SAMPLE_MINUTES:
        score = 0.25
    elif minutes < ADEQUATE_SAMPLE_MINUTES:
        score = 0.5
    elif minutes < FULL_SAMPLE_MINUTES:
        score = 0.75
    else:
        score = 1.0

    return SampleConfidence(
        minutes=minutes,
        score=score,
        level=sample_confidence_level(score),
    )
