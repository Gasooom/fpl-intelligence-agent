from __future__ import annotations

from agents import Agent

from fpl_agent.agent.context import FPLAgentContext
from fpl_agent.agent.instructions import FPL_AGENT_INSTRUCTIONS
from fpl_agent.agent.specialists import (
    create_captain_specialist,
    create_risk_specialist,
    create_transfer_specialist,
)
from fpl_agent.agent.tools import (
    get_agent_capabilities,
    get_agent_context,
    get_captaincy_score,
    get_fixture_difficulty,
    get_player_performance,
    get_player_projection,
    get_risk_signals,
    get_transfer_candidate_score,
)
from fpl_agent.decisions.schemas import FPLDecisionOutput
from fpl_agent.mcp.server import get_mcp_servers


def create_fpl_agent() -> Agent[FPLAgentContext]:
    """Create the Fantasy Premier League decision agent."""
    transfer_specialist = create_transfer_specialist()
    captain_specialist = create_captain_specialist()
    risk_specialist = create_risk_specialist()

    transfer_specialist_tool = transfer_specialist.as_tool(
        tool_name="transfer_specialist",
        tool_description=(
            "Analyze an FPL transfer candidate using "
            "deterministic performance, projection, fixture, "
            "transfer-score, and risk analysis."
        ),
    )

    captain_specialist_tool = captain_specialist.as_tool(
        tool_name="captain_specialist",
        tool_description=(
            "Analyze an FPL captaincy candidate using "
            "deterministic performance, projection, fixture, "
            "captaincy-score, and risk analysis."
        ),
    )

    risk_specialist_tool = risk_specialist.as_tool(
        tool_name="risk_specialist",
        tool_description=(
            "Assess risk and uncertainty for an FPL decision "
            "using deterministic risk signals."
        ),
    )

    return Agent(
        name="FPL Decision Intelligence Agent",
        model="gpt-5-mini",
        instructions=FPL_AGENT_INSTRUCTIONS,
        output_type=FPLDecisionOutput,
        tools=[
            get_agent_capabilities,
            get_agent_context,
            get_player_performance,
            get_fixture_difficulty,
            get_player_projection,
            get_transfer_candidate_score,
            get_captaincy_score,
            get_risk_signals,
            transfer_specialist_tool,
            captain_specialist_tool,
            risk_specialist_tool,
        ],
        mcp_servers=get_mcp_servers(),
    )