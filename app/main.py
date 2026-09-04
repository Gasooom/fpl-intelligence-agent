from __future__ import annotations

from fpl_agent.agent.context import FPLAgentContext
from fpl_agent.agent.runner import run_fpl_agent
from fpl_agent.decisions.schemas import FPLDecisionOutput


async def run_application(
    input_text: str,
    context: FPLAgentContext | None = None,
) -> FPLDecisionOutput:
    """Run the FPL decision application and return its structured output."""
    result = await run_fpl_agent(
        input_text=input_text,
        context=context,
    )

    if not isinstance(result.final_output, FPLDecisionOutput):
        raise TypeError(
            "The FPL agent returned an unexpected output type."
        )

    return result.final_output