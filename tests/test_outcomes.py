from __future__ import annotations

from fpl_agent.data.models import EventLiveElement, EventLiveElementStats, EventLiveResponse
from fpl_agent.decisions.outcomes import (
    PlayerActualOutcome,
    build_actual_outcomes,
    index_actual_outcomes,
)


def make_live(*points: tuple[int, int]) -> EventLiveResponse:
    """Build an EventLiveResponse from (player_id, total_points) pairs."""
    return EventLiveResponse(
        elements=[
            EventLiveElement(id=player_id, stats=EventLiveElementStats(total_points=total))
            for player_id, total in points
        ],
    )


def test_build_actual_outcomes_maps_every_element_to_the_requested_gameweek() -> None:
    live = make_live((1, 10), (2, 0), (3, 6))

    outcomes = build_actual_outcomes(gameweek=3, live=live)

    assert outcomes == [
        PlayerActualOutcome(player_id=1, gameweek=3, actual_points=10),
        PlayerActualOutcome(player_id=2, gameweek=3, actual_points=0),
        PlayerActualOutcome(player_id=3, gameweek=3, actual_points=6),
    ]


def test_build_actual_outcomes_preserves_a_zero_score_for_a_player_who_did_not_play() -> None:
    live = make_live((1, 0))

    outcomes = build_actual_outcomes(gameweek=3, live=live)

    assert outcomes[0].actual_points == 0


def test_index_actual_outcomes_allows_o1_lookup_by_player_id() -> None:
    live = make_live((1, 10), (2, 0))
    outcomes = build_actual_outcomes(gameweek=3, live=live)

    indexed = index_actual_outcomes(outcomes)

    assert indexed[1].actual_points == 10
    assert indexed[2].actual_points == 0
    assert 3 not in indexed
