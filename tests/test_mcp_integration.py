from __future__ import annotations

import pytest

from fpl_agent.mcp.server import (
    get_external_mcp_server,
    get_fpl_mcp_server,
)


@pytest.mark.asyncio
async def test_fpl_mcp_stdio_connection_and_tool_discovery() -> None:
    server = get_fpl_mcp_server()

    async with server:
        tools = await server.list_tools()

    assert {tool.name for tool in tools} == {
        "get_bootstrap_static",
        "get_fixtures",
    }


@pytest.mark.asyncio
async def test_external_mcp_stdio_connection_and_tool_discovery() -> None:
    server = get_external_mcp_server()

    async with server:
        tools = await server.list_tools()

    assert {tool.name for tool in tools} == {
        "get_external_data",
    }


@pytest.mark.asyncio
async def test_external_mcp_stdio_tool_call() -> None:
    server = get_external_mcp_server()

    async with server:
        result = await server.call_tool(
            "get_external_data",
            {"query": "Arsenal"},
        )

    assert result
    assert not result.is_error


@pytest.mark.asyncio
async def test_fpl_mcp_stdio_tool_call() -> None:
    server = get_fpl_mcp_server()

    async with server:
        result = await server.call_tool(
            "get_fixtures",
            {},
        )

    assert result
    assert not result.is_error
    assert result.content