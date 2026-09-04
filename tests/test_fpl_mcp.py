from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from fpl_agent.data.models import Fixture
from fpl_agent.mcp.fpl_server import mcp


def test_fpl_mcp_server_name() -> None:
    assert mcp.name == "FPL Decision Intelligence"


@pytest.mark.asyncio
async def test_fpl_mcp_server_lists_tools() -> None:
    tools = await mcp.list_tools()

    tool_names = {tool.name for tool in tools}

    assert tool_names == {
        "get_bootstrap_static",
        "get_fixtures",
    }


@pytest.mark.asyncio
async def test_fpl_mcp_server_calls_get_fixtures() -> None:
    fixtures = [
        Fixture(
            id=1,
            event=1,
            team_h=1,
            team_a=2,
            finished=False,
            team_h_difficulty=3,
            team_a_difficulty=4,
        )
    ]

    with patch(
        "fpl_agent.mcp.fpl_server.FPLClient.get_fixtures",
        new=AsyncMock(return_value=fixtures),
    ):
        result = await mcp.call_tool(
            "get_fixtures",
            {},
        )

    assert result