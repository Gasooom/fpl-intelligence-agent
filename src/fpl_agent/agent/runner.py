from __future__ import annotations

from agents import Runner, RunResult

from fpl_agent.agent.context import FPLAgentContext
from fpl_agent.agent.core import create_fpl_agent
from fpl_agent.agent.errors import FPLAgentRunError


async def run_fpl_agent(
    input_text: str,
    context: FPLAgentContext | None = None,
) -> RunResult:
    """Run the FPL decision agent with optional runtime context."""
    agent = create_fpl_agent()

    if context is None:
        context = FPLAgentContext()

    try:
        return await Runner.run(
            agent,
            input_text,
            context=context,
        )
    except Exception as exc:
        raise FPLAgentRunError(
            "The FPL decision agent failed to complete the run."
        ) from exc