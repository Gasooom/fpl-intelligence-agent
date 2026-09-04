from __future__ import annotations

import os

import pytest
from agents import Agent, Runner

from fpl_agent.agent.specialists import (
    CAPTAIN_SPECIALIST_INSTRUCTIONS,
    RISK_SPECIALIST_INSTRUCTIONS,
    TRANSFER_SPECIALIST_INSTRUCTIONS,
    create_captain_specialist,
    create_risk_specialist,
    create_transfer_specialist,
)


def test_create_transfer_specialist() -> None:
    agent = create_transfer_specialist()

    assert isinstance(agent, Agent)
    assert agent.name == "Transfer Specialist"
    assert agent.model == "gpt-5-mini"


def test_transfer_specialist_has_instructions() -> None:
    agent = create_transfer_specialist()

    assert agent.instructions == TRANSFER_SPECIALIST_INSTRUCTIONS
    assert "Fantasy Premier League" in agent.instructions
    assert "Do not invent" in agent.instructions


def test_transfer_specialist_has_decision_tools() -> None:
    agent = create_transfer_specialist()

    tool_names = {tool.name for tool in agent.tools}

    expected_tool_names = {
        "get_player_performance",
        "get_fixture_difficulty",
        "get_player_projection",
        "get_transfer_candidate_score",
        "get_risk_signals",
    }

    assert tool_names == expected_tool_names


def test_transfer_specialist_can_be_exposed_as_tool() -> None:
    agent = create_transfer_specialist()

    tool = agent.as_tool(
        tool_name="transfer_specialist",
        tool_description="Analyze an FPL transfer candidate.",
    )

    assert tool.name == "transfer_specialist"
    assert tool.params_json_schema["type"] == "object"
    assert "input" in tool.params_json_schema["properties"]


@pytest.mark.asyncio
async def test_transfer_specialist_as_tool_can_run() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY is not set")

    specialist = Agent(
        name="Test Transfer Specialist",
        model="gpt-5-mini",
        instructions="Return exactly: TRANSFER_SPECIALIST_OK",
    )

    tool = specialist.as_tool(
        tool_name="transfer_specialist",
        tool_description="Test transfer specialist.",
    )

    manager = Agent(
        name="Test Manager",
        model="gpt-5-mini",
        instructions=(
            "Call the transfer_specialist tool once. "
            "Return exactly the tool's result."
        ),
        tools=[tool],
    )

    result = await Runner.run(
        manager,
        "Use the transfer specialist now.",
    )

    assert result.final_output == "TRANSFER_SPECIALIST_OK"


def test_create_captain_specialist() -> None:
    agent = create_captain_specialist()

    assert isinstance(agent, Agent)
    assert agent.name == "Captain Specialist"
    assert agent.model == "gpt-5-mini"


def test_captain_specialist_has_instructions() -> None:
    agent = create_captain_specialist()

    assert agent.instructions == CAPTAIN_SPECIALIST_INSTRUCTIONS
    assert "Fantasy Premier League" in agent.instructions
    assert "Do not invent" in agent.instructions


def test_captain_specialist_has_decision_tools() -> None:
    agent = create_captain_specialist()

    tool_names = {tool.name for tool in agent.tools}

    expected_tool_names = {
        "get_player_performance",
        "get_fixture_difficulty",
        "get_player_projection",
        "get_captaincy_score",
        "get_risk_signals",
    }

    assert tool_names == expected_tool_names


def test_captain_specialist_can_be_exposed_as_tool() -> None:
    agent = create_captain_specialist()

    tool = agent.as_tool(
        tool_name="captain_specialist",
        tool_description="Analyze an FPL captaincy candidate.",
    )

    assert tool.name == "captain_specialist"
    assert tool.params_json_schema["type"] == "object"
    assert "input" in tool.params_json_schema["properties"]


def test_create_risk_specialist() -> None:
    agent = create_risk_specialist()

    assert isinstance(agent, Agent)
    assert agent.name == "Risk Specialist"
    assert agent.model == "gpt-5-mini"


def test_risk_specialist_has_instructions() -> None:
    agent = create_risk_specialist()

    assert agent.instructions == RISK_SPECIALIST_INSTRUCTIONS
    assert "Fantasy Premier League" in agent.instructions
    assert "Do not invent" in agent.instructions


def test_risk_specialist_has_decision_tools() -> None:
    agent = create_risk_specialist()

    tool_names = {tool.name for tool in agent.tools}

    expected_tool_names = {
        "get_player_performance",
        "get_fixture_difficulty",
        "get_risk_signals",
    }

    assert tool_names == expected_tool_names


def test_risk_specialist_can_be_exposed_as_tool() -> None:
    agent = create_risk_specialist()

    tool = agent.as_tool(
        tool_name="risk_specialist",
        tool_description="Assess risk for an FPL decision.",
    )

    assert tool.name == "risk_specialist"
    assert tool.params_json_schema["type"] == "object"
    assert "input" in tool.params_json_schema["properties"]