from __future__ import annotations

import sys
from pathlib import Path

from agents.mcp import MCPServer, MCPServerStdio

PROJECT_ROOT = Path(__file__).resolve().parents[4]


def get_fpl_mcp_server() -> MCPServer:
    """Create an Agents SDK MCP connection to the FPL MCP server."""
    return MCPServerStdio(
        params={
            "command": sys.executable,
            "args": [
                "-m",
                "fpl_agent.mcp.fpl_server",
            ],
            "cwd": str(PROJECT_ROOT),
        },
        name="FPL Decision Intelligence",
        cache_tools_list=True,
        require_approval={
            "get_bootstrap_static": "never",
            "get_fixtures": "never",
        },
    )


def get_external_mcp_server() -> MCPServer:
    """Create an Agents SDK MCP connection to the external-data MCP server."""
    return MCPServerStdio(
        params={
            "command": sys.executable,
            "args": [
                "-m",
                "fpl_agent.mcp.external_server",
            ],
            "cwd": str(PROJECT_ROOT),
        },
        name="FPL External Data",
        cache_tools_list=True,
        require_approval={
            "get_external_data": "never",
        },
    )


def get_mcp_servers() -> list[MCPServer]:
    """Return all MCP servers available to the FPL agent."""
    return [
        get_fpl_mcp_server(),
        get_external_mcp_server(),
    ]