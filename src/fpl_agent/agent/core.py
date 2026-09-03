from __future__ import annotations

from agents import Agent

from fpl_agent.agent.context import FPLAgentContext
from fpl_agent.agent.instructions import FPL_AGENT_INSTRUCTIONS
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


def create_fpl_agent() -> Agent[FPLAgentContext]:
    """Create the Fantasy Premier League decision agent."""
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
        ],
    )