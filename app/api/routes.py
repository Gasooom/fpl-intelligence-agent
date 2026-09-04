from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from fpl_agent.api.decision import squad_decision_to_response
from fpl_agent.api.schemas import SquadDecisionResponse
from fpl_agent.decisions.service import FPLDecisionService

router = APIRouter(prefix="/api/v1", tags=["decisions"])

decision_service = FPLDecisionService()


@router.get(
    "/decision/{entry_id}",
    response_model=SquadDecisionResponse,
)
async def get_squad_decision(
    entry_id: int,
    gameweek: int | None = Query(
        default=None,
        ge=1,
        description="FPL gameweek to analyze. Defaults to the current gameweek.",
    ),
) -> SquadDecisionResponse:
    """Return a deterministic FPL squad decision."""
    try:
        decision = await decision_service.analyze_squad(
            entry_id=entry_id,
            gameweek=gameweek,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return squad_decision_to_response(decision)