from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.api.routes import router
from app.cors import configure_cors
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

# The React frontend is deployed separately, so the browser calls this
# API cross-origin. Allowed origins come from the environment - see
# app/cors.py - so no deployment URL is baked into this source tree.
configure_cors(app)

app.include_router(router)

_DEMO_PAGE = (Path(__file__).parent / "static" / "index.html").read_text(
    encoding="utf-8",
)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    """Return API health status."""
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse, tags=["demo"])
async def demo_page() -> str:
    """Serve the portfolio demo page.

    A single self-contained static HTML/CSS/JS file that calls the
    existing JSON API (GET /api/v1/decision/{entry_id}) client-side
    and renders the response. No templating engine, no additional
    dependencies, and no decision logic here - this route only serves
    static content and never computes anything itself.
    """
    return _DEMO_PAGE


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