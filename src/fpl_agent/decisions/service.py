from __future__ import annotations

from fpl_agent.data.client import FPLClient
from fpl_agent.data.models import Gameweek
from fpl_agent.decisions.gameweek_decision import (
    GameweekDecision,
    build_gameweek_decision,
)
from fpl_agent.decisions.squad_analysis import (
    SquadDecision,
    build_squad_decision,
)


class FPLDecisionService:
    """Application service for deterministic FPL squad decisions."""

    def __init__(self, client: FPLClient | None = None) -> None:
        self.client = client or FPLClient()

    async def analyze_squad(
        self,
        entry_id: int,
        gameweek: int | None = None,
    ) -> SquadDecision:
        """Fetch FPL data and produce a deterministic squad decision.

        Kept for callers that only need starting XI/bench/captaincy.
        Prefer analyze_gameweek for the full gameweek action plan,
        including transfer intelligence.
        """
        bootstrap = await self.client.get_bootstrap_static()

        target_gameweek = self._resolve_gameweek(
            bootstrap.events,
            gameweek,
        )

        entry = await self.client.get_entry(entry_id)

        picks_response = await self.client.get_entry_picks(
            entry_id=entry.id,
            gameweek=target_gameweek,
        )

        fixtures = await self.client.get_fixtures()

        return build_squad_decision(
            players=bootstrap.elements,
            teams=bootstrap.teams,
            fixtures=fixtures,
            picks=picks_response.picks,
        )

    async def analyze_gameweek(
        self,
        entry_id: int,
        gameweek: int | None = None,
    ) -> GameweekDecision:
        """Fetch FPL data and produce the unified deterministic gameweek decision.

        Combines the squad decision (starting XI, bench, captaincy,
        must-play) with deterministic sell/buy transfer intelligence.
        """
        bootstrap = await self.client.get_bootstrap_static()

        target_gameweek = self._resolve_gameweek(
            bootstrap.events,
            gameweek,
        )

        entry = await self.client.get_entry(entry_id)

        picks_response = await self.client.get_entry_picks(
            entry_id=entry.id,
            gameweek=target_gameweek,
        )

        fixtures = await self.client.get_fixtures()

        return build_gameweek_decision(
            players=bootstrap.elements,
            teams=bootstrap.teams,
            fixtures=fixtures,
            picks=picks_response.picks,
            gameweek=target_gameweek,
            entry_history=picks_response.entry_history,
        )

    @staticmethod
    def _resolve_gameweek(
        events: list[Gameweek],
        requested_gameweek: int | None,
    ) -> int:
        """Resolve the requested gameweek or the current FPL gameweek."""
        if requested_gameweek is not None:
            if requested_gameweek < 1:
                raise ValueError(
                    "Gameweek must be greater than zero.",
                )

            if not any(
                event.id == requested_gameweek
                for event in events
            ):
                raise ValueError(
                    f"Gameweek {requested_gameweek} was not found.",
                )

            return requested_gameweek

        current_events = [
            event
            for event in events
            if event.is_current
        ]

        if current_events:
            return current_events[0].id

        next_events = [
            event
            for event in events
            if event.is_next
        ]

        if next_events:
            return next_events[0].id

        raise ValueError(
            "Unable to determine the current or next gameweek.",
        )