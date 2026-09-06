from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from fpl_agent.api.decision import squad_decision_to_response
from fpl_agent.api.schemas import SquadDecisionResponse
from fpl_agent.decisions.service import FPLDecisionService

router = APIRouter(prefix="/api/v1", tags=["decisions"])

decision_service = FPLDecisionService()


def get_decision_service() -> FPLDecisionService:
    """Provide the deterministic decision service.

    Exposed as a FastAPI dependency so tests can override it with a
    fake/mocked service via ``app.dependency_overrides`` instead of
    monkeypatching the module-level singleton.
    """
    return decision_service


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
    service: FPLDecisionService = Depends(get_decision_service),
) -> SquadDecisionResponse:
    """Return a deterministic FPL squad decision.

    This endpoint is a thin HTTP boundary: it delegates entirely to the
    deterministic decision service and response conversion, and contains
    no decision logic of its own.
    """
    try:
        decision = await service.analyze_squad(
            entry_id=entry_id,
            gameweek=gameweek,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return squad_decision_to_response(decision)