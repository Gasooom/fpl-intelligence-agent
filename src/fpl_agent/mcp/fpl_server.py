from __future__ import annotations

from typing import Any

from mcp.server import MCPServer

from fpl_agent.agent.errors import FPLMCPError
from fpl_agent.data.client import FPLClient

mcp = MCPServer("FPL Decision Intelligence")


@mcp.tool()
async def get_bootstrap_static() -> dict[str, Any]:
    """Fetch the official FPL bootstrap dataset."""
    try:
        client = FPLClient()
        data = await client.get_bootstrap_static()

        return data.model_dump()
    except Exception as exc:
        raise FPLMCPError(
            "The FPL bootstrap data could not be retrieved."
        ) from exc


@mcp.tool()
async def get_fixtures() -> list[dict[str, Any]]:
    """Fetch the official FPL fixture dataset."""
    try:
        client = FPLClient()
        fixtures = await client.get_fixtures()

        return [fixture.model_dump() for fixture in fixtures]
    except Exception as exc:
        raise FPLMCPError(
            "The FPL fixture data could not be retrieved."
        ) from exc


if __name__ == "__main__":
    mcp.run()