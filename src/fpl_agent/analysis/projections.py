from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlayerProjection:
    """Deterministic expected-points projection for an FPL player."""

    player_id: int
    expected_points: float
    base_points: float
    xgi_component: float
    fixture_component: float


def calculate_expected_points(
    points_per_game: float,
    points_per_90: float,
    xgi_per_90: float,
    fixture_difficulty: float,
) -> float:
    """Calculate a deterministic expected-points projection.

    Lower fixture difficulty represents a more favorable fixture.
    """
    base_points = (
        points_per_game * 0.5
        + points_per_90 * 0.3
    )

    xgi_component = xgi_per_90 * 0.2

    fixture_multiplier = max(
        0.5,
        min(1.5, 1.5 - (fixture_difficulty - 1.0) / 4.0),
    )

    projected_points = (
        base_points + xgi_component
    ) * fixture_multiplier

    return round(projected_points, 2)


def project_player(
    player_id: int,
    points_per_game: float,
    points_per_90: float,
    xgi_per_90: float,
    fixture_difficulty: float,
) -> PlayerProjection:
    """Build a deterministic player projection."""
    base_points = (
        points_per_game * 0.5
        + points_per_90 * 0.3
    )

    xgi_component = xgi_per_90 * 0.2

    fixture_multiplier = max(
        0.5,
        min(1.5, 1.5 - (fixture_difficulty - 1.0) / 4.0),
    )

    expected_points = round(
        (base_points + xgi_component) * fixture_multiplier,
        2,
    )

    return PlayerProjection(
        player_id=player_id,
        expected_points=expected_points,
        base_points=round(base_points, 2),
        xgi_component=round(xgi_component, 2),
        fixture_component=round(fixture_multiplier, 2),
    )
