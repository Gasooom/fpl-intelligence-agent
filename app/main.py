from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import router
from fpl_agent.agent.context import FPLAgentContext
from fpl_agent.agent.runner import run_fpl_agent
from fpl_agent.decisions.schemas import FPLDecisionOutput

app = FastAPI(
    title="Fantasy Decision Intelligence API",
    description=(
        "Deterministic Fantasy Premier League decision intelligence "
        "based on official FPL data."
    ),
    version="0.1.0",
)

app.include_router(router)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    """Return API health status."""
    return {"status": "ok"}


async def run_application(
    input_text: str,
    context: FPLAgentContext | None = None,
) -> FPLDecisionOutput:
    """Run the legacy FPL agent application boundary."""
    result = await run_fpl_agent(
        input_text=input_text,
        context=context,
    )

    if not isinstance(result.final_output, FPLDecisionOutput):
        raise TypeError(
            "The FPL agent returned an unexpected output type."
        )

    return result.final_output