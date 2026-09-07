from __future__ import annotations

from typing import Any

import httpx

from fpl_agent.data.models import (
    BootstrapData,
    EventLiveResponse,
    Fixture,
    FPLEntry,
    SquadPicksResponse,
)


class FPLClient:
    """HTTP client for the official Fantasy Premier League API."""

    BASE_URL = "https://fantasy.premierleague.com/api"

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    async def get_bootstrap_static(self) -> BootstrapData:
        """Fetch and validate the main FPL dataset."""
        url = f"{self.BASE_URL}/bootstrap-static/"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()

            data: dict[str, Any] = response.json()

        return BootstrapData.model_validate(data)

    async def get_fixtures(self) -> list[Fixture]:
        """Fetch and validate all FPL fixtures."""
        url = f"{self.BASE_URL}/fixtures/"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()

            data: list[dict[str, Any]] = response.json()

        return [Fixture.model_validate(fixture) for fixture in data]

    async def get_entry(self, entry_id: int) -> FPLEntry:
        """Fetch an FPL manager entry."""
        url = f"{self.BASE_URL}/entry/{entry_id}/"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()

            data: dict[str, Any] = response.json()

        return FPLEntry.model_validate(data)

    async def get_entry_picks(
        self,
        entry_id: int,
        gameweek: int,
    ) -> SquadPicksResponse:
        """Fetch an FPL manager's squad for a gameweek."""
        url = f"{self.BASE_URL}/entry/{entry_id}/event/{gameweek}/picks/"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()

            data: dict[str, Any] = response.json()

        return SquadPicksResponse.model_validate(data)

    async def get_event_live(self, gameweek: int) -> EventLiveResponse:
        """Fetch actual per-player points for a gameweek.

        Only meaningful once the gameweek has kicked off; FPL reports
        `total_points: 0` for players who have not yet played rather
        than omitting them, and the same for a gameweek that has not
        started at all - callers that need to know whether a gameweek
        is actually finished should check `Gameweek.finished` from
        `get_bootstrap_static`, not infer it from this response.
        """
        url = f"{self.BASE_URL}/event/{gameweek}/live/"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()

            data: dict[str, Any] = response.json()

        return EventLiveResponse.model_validate(data)