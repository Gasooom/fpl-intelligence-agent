from __future__ import annotations

from typing import Any

import httpx

from fpl_agent.data.errors import (
    FPLRateLimitedError,
    FPLResourceNotFoundError,
    FPLUpstreamError,
    FPLUpstreamTimeoutError,
)
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

    def __init__(
        self,
        timeout: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.timeout = timeout
        # Injectable purely so tests can drive controlled upstream
        # responses through httpx.MockTransport instead of calling the
        # live FPL API. Left as None in production, which keeps httpx's
        # default transport and its normal connection behaviour.
        self._transport = transport

    async def _get_json(self, url: str, resource: str) -> Any:
        """GET `url`, returning parsed JSON or raising an `FPLDataError`.

        Every request funnels through here so that upstream failures
        are translated in exactly one place. `resource` is a short
        human-readable description of what was being fetched and is
        the *only* caller-varying text that reaches the message, so a
        raw httpx exception, the request URL, or an upstream response
        body can never leak into an API response.

        Only the statuses this project can act on meaningfully are
        singled out. Everything else - including all 5xx and any
        unrecognised 4xx - stays a generic upstream failure, because
        reporting it as "not found" would tell the caller something
        untrue about their request.
        """
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                transport=self._transport,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()

                return response.json()
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code

            if status_code == httpx.codes.NOT_FOUND:
                raise FPLResourceNotFoundError(
                    f"{resource} was not found in the official FPL API.",
                ) from exc

            if status_code == httpx.codes.TOO_MANY_REQUESTS:
                raise FPLRateLimitedError(
                    "The official FPL API is rate limiting this service. "
                    "Please try again shortly.",
                ) from exc

            raise FPLUpstreamError(
                f"The official FPL API could not return {resource.lower()}.",
            ) from exc
        except httpx.TimeoutException as exc:
            # Deliberately distinct from the not-found case: a slow or
            # unreachable upstream says nothing about whether the
            # requested resource exists.
            raise FPLUpstreamTimeoutError(
                f"Timed out fetching {resource.lower()} from the official FPL API.",
            ) from exc
        except httpx.RequestError as exc:
            raise FPLUpstreamError(
                f"Could not reach the official FPL API to fetch {resource.lower()}.",
            ) from exc

    async def get_bootstrap_static(self) -> BootstrapData:
        """Fetch and validate the main FPL dataset."""
        url = f"{self.BASE_URL}/bootstrap-static/"

        data: dict[str, Any] = await self._get_json(url, "The FPL bootstrap dataset")

        return BootstrapData.model_validate(data)

    async def get_fixtures(self) -> list[Fixture]:
        """Fetch and validate all FPL fixtures."""
        url = f"{self.BASE_URL}/fixtures/"

        data: list[dict[str, Any]] = await self._get_json(url, "The FPL fixture list")

        return [Fixture.model_validate(fixture) for fixture in data]

    async def get_entry(self, entry_id: int) -> FPLEntry:
        """Fetch an FPL manager entry."""
        url = f"{self.BASE_URL}/entry/{entry_id}/"

        data: dict[str, Any] = await self._get_json(url, f"FPL entry {entry_id}")

        return FPLEntry.model_validate(data)

    async def get_entry_picks(
        self,
        entry_id: int,
        gameweek: int,
    ) -> SquadPicksResponse:
        """Fetch an FPL manager's squad for a gameweek.

        FPL answers 404 both for an entry that does not exist and for a
        gameweek whose squad has not been picked yet (any gameweek
        before its deadline), so this is the call that most often
        surfaces `FPLResourceNotFoundError` in practice.
        """
        url = f"{self.BASE_URL}/entry/{entry_id}/event/{gameweek}/picks/"

        data: dict[str, Any] = await self._get_json(
            url,
            f"The squad for FPL entry {entry_id} in gameweek {gameweek}",
        )

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

        data: dict[str, Any] = await self._get_json(
            url,
            f"Live data for gameweek {gameweek}",
        )

        return EventLiveResponse.model_validate(data)
