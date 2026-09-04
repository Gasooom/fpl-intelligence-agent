from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from fpl_agent.agent.errors import (
    ExternalMCPError,
    FPLMCPError,
)
from fpl_agent.mcp.external_server import get_external_data
from fpl_agent.mcp.fpl_server import (
    get_bootstrap_static,
    get_fixtures,
)


@pytest.mark.asyncio
async def test_fpl_bootstrap_failure_is_wrapped() -> None:
    with patch(
        "fpl_agent.mcp.fpl_server.FPLClient.get_bootstrap_static",
        new=AsyncMock(
            side_effect=httpx.ConnectError("connection failed"),
        ),
    ), pytest.raises(FPLMCPError) as exc_info:
        await get_bootstrap_static()

    assert str(exc_info.value) == (
        "The FPL bootstrap data could not be retrieved."
    )
    assert isinstance(exc_info.value.__cause__, httpx.ConnectError)


@pytest.mark.asyncio
async def test_fpl_fixture_failure_is_wrapped() -> None:
    with patch(
        "fpl_agent.mcp.fpl_server.FPLClient.get_fixtures",
        new=AsyncMock(
            side_effect=httpx.ConnectError("connection failed"),
        ),
    ), pytest.raises(FPLMCPError) as exc_info:
        await get_fixtures()

    assert str(exc_info.value) == (
        "The FPL fixture data could not be retrieved."
    )
    assert isinstance(exc_info.value.__cause__, httpx.ConnectError)


@pytest.mark.asyncio
async def test_external_data_failure_is_wrapped() -> None:
    with patch(
        "fpl_agent.mcp.external_server.ExternalDataClient.search_team",
        new=AsyncMock(
            side_effect=httpx.ConnectError("connection failed"),
        ),
    ), pytest.raises(ExternalMCPError) as exc_info:
        await get_external_data("Arsenal")

    assert str(exc_info.value) == (
        "The external football data could not be retrieved."
    )
    assert isinstance(exc_info.value.__cause__, httpx.ConnectError)