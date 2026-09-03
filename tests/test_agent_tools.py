from agents import FunctionTool

from fpl_agent.agent.core import create_fpl_agent
from fpl_agent.agent.tools import (
    get_agent_capabilities,
    get_agent_context,
)


def test_get_agent_capabilities_is_registered() -> None:
    assert isinstance(get_agent_capabilities, FunctionTool)
    assert get_agent_capabilities.name == "get_agent_capabilities"

    schema = get_agent_capabilities.params_json_schema

    assert schema["type"] == "object"
    assert schema["properties"] == {}
    assert schema["additionalProperties"] is False


def test_get_agent_capabilities_has_description() -> None:
    assert get_agent_capabilities.description is not None
    assert (
        "capabilities currently available"
        in get_agent_capabilities.description
    )


def test_get_agent_context_is_registered() -> None:
    assert isinstance(get_agent_context, FunctionTool)
    assert get_agent_context.name == "get_agent_context"

    schema = get_agent_context.params_json_schema

    assert schema["type"] == "object"


def test_agent_has_capability_tools() -> None:
    agent = create_fpl_agent()

    tool_names = {tool.name for tool in agent.tools}

    assert "get_agent_capabilities" in tool_names
    assert "get_agent_context" in tool_names