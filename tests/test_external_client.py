from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from fpl_agent.data.external_client import ExternalDataClient


@pytest.mark.asyncio
async def test_search_team_returns_external_data() -> None:
    response = httpx.Response(
        200,
        json={
            "teams": [
                {
                    "idTeam": "133604",
                    "strTeam": "Arsenal",
                    "strLeague": "English Premier League",
                }
            ]
        },
        request=httpx.Request(
            "GET",
            "https://www.thesportsdb.com/api/v1/json/123/searchteams.php",
        ),
    )

    with patch(
        "httpx.AsyncClient.get",
        new=AsyncMock(return_value=response),
    ):
        client = ExternalDataClient()

        result = await client.search_team("Arsenal")

    assert len(result) == 1
    assert result[0]["strTeam"] == "Arsenal"


@pytest.mark.asyncio
async def test_search_team_returns_empty_list_when_no_results() -> None:
    response = httpx.Response(
        200,
        json={"teams": None},
        request=httpx.Request(
            "GET",
            "https://www.thesportsdb.com/api/v1/json/123/searchteams.php",
        ),
    )

    with patch(
        "httpx.AsyncClient.get",
        new=AsyncMock(return_value=response),
    ):
        client = ExternalDataClient()

        result = await client.search_team("Unknown Team")

    assert result == []


@pytest.mark.asyncio
async def test_search_team_raises_for_http_error() -> None:
    response = httpx.Response(
        500,
        request=httpx.Request(
            "GET",
            "https://www.thesportsdb.com/api/v1/json/123/searchteams.php",
        ),
    )

    with patch(
        "httpx.AsyncClient.get",
        new=AsyncMock(return_value=response),
    ):
        client = ExternalDataClient()

        with pytest.raises(httpx.HTTPStatusError):
            await client.search_team("Arsenal")