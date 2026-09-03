from __future__ import annotations

from typing import Any

import httpx

from fpl_agent.data.models import BootstrapData, Fixture


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