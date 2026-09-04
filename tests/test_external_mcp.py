from __future__ import annotations

import pytest

from fpl_agent.mcp.external_server import mcp


def test_external_mcp_server_name() -> None:
    assert mcp.name == "FPL External Data"


@pytest.mark.asyncio
async def test_external_mcp_server_lists_tools() -> None:
    tools = await mcp.list_tools()

    tool_names = {tool.name for tool in tools}

    assert tool_names == {
        "get_external_data",
    }


@pytest.mark.asyncio
async def test_external_mcp_server_calls_external_data() -> None:
    result = await mcp.call_tool(
        "get_external_data",
        {"query": "Premier League"},
    )

    assert result