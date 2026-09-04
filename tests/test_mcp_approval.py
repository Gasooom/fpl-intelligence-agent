from __future__ import annotations

from fpl_agent.mcp.server import (
    get_external_mcp_server,
    get_fpl_mcp_server,
)


def test_fpl_mcp_read_tools_do_not_require_approval() -> None:
    server = get_fpl_mcp_server()

    assert server._needs_approval_policy == {
        "get_bootstrap_static": False,
        "get_fixtures": False,
    }


def test_external_mcp_read_tool_does_not_require_approval() -> None:
    server = get_external_mcp_server()

    assert server._needs_approval_policy == {
        "get_external_data": False,
    }