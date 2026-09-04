from __future__ import annotations

from typing import Any

from mcp.server import MCPServer

from fpl_agent.agent.errors import ExternalMCPError
from fpl_agent.data.external_client import ExternalDataClient

mcp = MCPServer("FPL External Data")


@mcp.tool()
async def get_external_data(query: str) -> dict[str, Any]:
    """Search external football data for a team."""
    try:
        client = ExternalDataClient()
        teams = await client.search_team(query)

        return {
            "query": query,
            "source": "TheSportsDB",
            "teams": teams,
        }
    except Exception as exc:
        raise ExternalMCPError(
            "The external football data could not be retrieved."
        ) from exc


if __name__ == "__main__":
    mcp.run()