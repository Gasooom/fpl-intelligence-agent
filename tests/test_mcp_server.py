from __future__ import annotations

import pytest

from fpl_agent.mcp.server import (
    get_external_mcp_server,
    get_fpl_mcp_server,
    get_mcp_servers,
)


def test_get_fpl_mcp_server() -> None:
    server = get_fpl_mcp_server()

    assert server.name == "FPL Decision Intelligence"


def test_get_external_mcp_server() -> None:
    server = get_external_mcp_server()

    assert server.name == "FPL External Data"


def test_get_mcp_servers_returns_all_servers() -> None:
    servers = get_mcp_servers()

    assert len(servers) == 2
    assert {server.name for server in servers} == {
        "FPL Decision Intelligence",
        "FPL External Data",
    }


@pytest.mark.asyncio
async def test_fpl_mcp_server_tools_are_discoverable() -> None:
    server = get_fpl_mcp_server()

    async with server:
        tools = await server.list_tools()

    assert {tool.name for tool in tools} == {
        "get_bootstrap_static",
        "get_fixtures",
    }


@pytest.mark.asyncio
async def test_external_mcp_server_tools_are_discoverable() -> None:
    server = get_external_mcp_server()

    async with server:
        tools = await server.list_tools()

    assert {tool.name for tool in tools} == {
        "get_external_data",
    }