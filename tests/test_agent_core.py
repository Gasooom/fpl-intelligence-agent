from __future__ import annotations

from agents import Agent, FunctionTool

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
        "transfer_specialist",
        "captain_specialist",
        "risk_specialist",
    }

    assert tool_names == expected_tool_names


def test_transfer_specialist_tool_is_function_tool() -> None:
    agent = create_fpl_agent()

    transfer_tool = next(
        tool for tool in agent.tools
        if tool.name == "transfer_specialist"
    )

    assert isinstance(transfer_tool, FunctionTool)


def test_captain_specialist_tool_is_function_tool() -> None:
    agent = create_fpl_agent()

    captain_tool = next(
        tool for tool in agent.tools
        if tool.name == "captain_specialist"
    )

    assert isinstance(captain_tool, FunctionTool)


def test_risk_specialist_tool_is_function_tool() -> None:
    agent = create_fpl_agent()

    risk_tool = next(
        tool for tool in agent.tools
        if tool.name == "risk_specialist"
    )

    assert isinstance(risk_tool, FunctionTool)


def test_fpl_agent_exposes_transfer_specialist_as_tool() -> None:
    agent = create_fpl_agent()

    transfer_tool = next(
        tool for tool in agent.tools
        if tool.name == "transfer_specialist"
    )

    assert transfer_tool.name == "transfer_specialist"
    assert transfer_tool.params_json_schema["type"] == "object"
    assert "input" in transfer_tool.params_json_schema["properties"]


def test_fpl_agent_exposes_captain_specialist_as_tool() -> None:
    agent = create_fpl_agent()

    captain_tool = next(
        tool for tool in agent.tools
        if tool.name == "captain_specialist"
    )

    assert captain_tool.name == "captain_specialist"
    assert captain_tool.params_json_schema["type"] == "object"
    assert "input" in captain_tool.params_json_schema["properties"]


def test_fpl_agent_exposes_risk_specialist_as_tool() -> None:
    agent = create_fpl_agent()

    risk_tool = next(
        tool for tool in agent.tools
        if tool.name == "risk_specialist"
    )

    assert risk_tool.name == "risk_specialist"
    assert risk_tool.params_json_schema["type"] == "object"
    assert "input" in risk_tool.params_json_schema["properties"]


def test_fpl_agent_has_mcp_servers() -> None:
    agent = create_fpl_agent()

    assert len(agent.mcp_servers) == 2
    assert {server.name for server in agent.mcp_servers} == {
        "FPL Decision Intelligence",
        "FPL External Data",
    }