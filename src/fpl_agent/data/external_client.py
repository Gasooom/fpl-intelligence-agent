from __future__ import annotations

from typing import Any

import httpx


class ExternalDataClient:
    """HTTP client for external football data."""

    BASE_URL = "https://www.thesportsdb.com/api/v1/json/123"

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    async def search_team(self, team_name: str) -> list[dict[str, Any]]:
        """Search for a football team using an external sports API."""
        url = f"{self.BASE_URL}/searchteams.php"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                url,
                params={"t": team_name},
            )
            response.raise_for_status()

            data: dict[str, Any] = response.json()

        teams = data.get("teams")

        if not isinstance(teams, list):
            return []

        return [
            team
            for team in teams
            if isinstance(team, dict)
        ]