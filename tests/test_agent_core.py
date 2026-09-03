from agents import Agent

from fpl_agent.agent.core import create_fpl_agent
from fpl_agent.agent.instructions import FPL_AGENT_INSTRUCTIONS
from fpl_agent.decisions.schemas import FPLDecisionOutput


def test_create_fpl_agent() -> None:
    agent = create_fpl_agent()

    assert isinstance(agent, Agent)
    assert agent.name == "FPL Decision Intelligence Agent"
    assert agent.model == "gpt-5-mini"


def test_fpl_agent_has_instructions() -> None:
    agent = create_fpl_agent()

    assert agent.instructions == FPL_AGENT_INSTRUCTIONS
    assert "Fantasy Premier League" in agent.instructions
    assert "evidence-driven" in agent.instructions
    assert "Do not invent" in agent.instructions


def test_fpl_agent_has_structured_output() -> None:
    agent = create_fpl_agent()

    assert agent.output_type is FPLDecisionOutput


def test_fpl_agent_has_all_decision_engine_tools() -> None:
    agent = create_fpl_agent()

    tool_names = {tool.name for tool in agent.tools}

    expected_tool_names = {
        "get_agent_capabilities",
        "get_agent_context",
        "get_player_performance",
        "get_fixture_difficulty",
        "get_player_projection",
        "get_transfer_candidate_score",
        "get_captaincy_score",
        "get_risk_signals",
    }

    assert tool_names == expected_tool_names