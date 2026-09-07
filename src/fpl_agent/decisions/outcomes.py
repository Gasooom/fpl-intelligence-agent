from __future__ import annotations

from dataclasses import dataclass

from fpl_agent.data.models import EventLiveResponse


@dataclass(frozen=True)
class PlayerActualOutcome:
    """One player's real, already-played FPL points for one gameweek.

    The only source of this data is the official FPL `event/{event}/live/`
    endpoint - nothing here is ever estimated, simulated, or carried
    over from a projection.
    """

    player_id: int
    gameweek: int
    actual_points: int


def build_actual_outcomes(
    gameweek: int,
    live: EventLiveResponse,
) -> list[PlayerActualOutcome]:
    """Convert a raw event-live response into actual per-player outcomes."""
    return [
        PlayerActualOutcome(
            player_id=element.id,
            gameweek=gameweek,
            actual_points=element.stats.total_points,
        )
        for element in live.elements
    ]


def index_actual_outcomes(
    outcomes: list[PlayerActualOutcome],
) -> dict[int, PlayerActualOutcome]:
    """Index outcomes by player_id for O(1) lookup during evaluation."""
    return {outcome.player_id: outcome for outcome in outcomes}
