from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from fpl_agent.api.decision import gameweek_decision_to_response
from fpl_agent.api.evaluation import (
    gameweek_evaluation_to_response,
    latest_completed_evaluation_to_response,
)
from fpl_agent.api.evaluation_schemas import (
    GameweekEvaluationResponse,
    LatestCompletedEvaluationResponse,
)
from fpl_agent.api.schemas import GameweekDecisionResponse
from fpl_agent.data.errors import (
    FPLDataError,
    FPLRateLimitedError,
    FPLResourceNotFoundError,
    FPLUpstreamTimeoutError,
)
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


def _http_error_for(exc: FPLDataError) -> HTTPException:
    """Map a data-layer failure onto its client-facing status code.

    Shared by both endpoints so they can never answer differently for
    the same upstream condition. The detail is the exception's own
    message, which `FPLClient` composes from this project's wording
    only - upstream exception text and response bodies never reach a
    client.

    Anything that is not one of these three stays a 502: an
    unreachable or misbehaving FPL API is a server-side problem, and
    reporting it as 404 would wrongly tell the caller their entry ID
    or gameweek was invalid. Exceptions that are not `FPLDataError` at
    all are left to propagate, so genuine bugs still surface as 500
    rather than being disguised as an upstream fault.
    """
    if isinstance(exc, FPLResourceNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))

    if isinstance(exc, FPLRateLimitedError):
        return HTTPException(status_code=429, detail=str(exc))

    if isinstance(exc, FPLUpstreamTimeoutError):
        return HTTPException(status_code=504, detail=str(exc))

    return HTTPException(status_code=502, detail=str(exc))


@router.get(
    "/decision/{entry_id}",
    response_model=GameweekDecisionResponse,
)
async def get_gameweek_decision(
    entry_id: int,
    gameweek: int | None = Query(
        default=None,
        ge=1,
        description="FPL gameweek to analyze. Defaults to the current gameweek.",
    ),
    free_transfers_available: int | None = Query(
        default=None,
        ge=0,
        description=(
            "The manager's free transfers available, from their own FPL app - "
            "no public FPL endpoint exposes this. When supplied, transfer "
            "priority reflects real hit-cost economics (essential / "
            "recommended / optional); when omitted, priority falls back to "
            "the selection-score-based classification."
        ),
    ),
    service: FPLDecisionService = Depends(get_decision_service),
) -> GameweekDecisionResponse:
    """Return the unified deterministic FPL gameweek decision.

    Covers starting XI, bench, captaincy, and must-play alongside
    deterministic sell/buy transfer intelligence. This endpoint is a
    thin HTTP boundary: it delegates entirely to the deterministic
    decision service and response conversion, and contains no decision
    logic of its own. No LLM is involved in producing any field of
    this response.
    """
    try:
        decision = await service.analyze_gameweek(
            entry_id=entry_id,
            gameweek=gameweek,
            free_transfers_available=free_transfers_available,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except FPLDataError as exc:
        raise _http_error_for(exc) from exc

    return gameweek_decision_to_response(decision)


@router.get(
    "/evaluation/{entry_id}",
    response_model=GameweekEvaluationResponse,
)
async def get_gameweek_evaluation(
    entry_id: int,
    gameweek: int | None = Query(
        default=None,
        ge=1,
        description="FPL gameweek to evaluate. Defaults to the current gameweek.",
    ),
    service: FPLDecisionService = Depends(get_decision_service),
) -> GameweekEvaluationResponse:
    """Compare a previously recorded decision against real gameweek outcomes.

    Evaluation only exists once both a decision snapshot was recorded
    for this entry/gameweek (see `FPLDecisionService.analyze_gameweek`)
    and the gameweek has actually finished - otherwise this returns an
    honest non-evaluated status and message rather than fabricating a
    result. This endpoint is a thin HTTP boundary like
    `/decision/{entry_id}`: it delegates entirely to
    `FPLDecisionService.evaluate_gameweek` and contains no evaluation
    logic of its own.
    """
    try:
        evaluation = await service.evaluate_gameweek(
            entry_id=entry_id,
            gameweek=gameweek,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except FPLDataError as exc:
        raise _http_error_for(exc) from exc

    return gameweek_evaluation_to_response(evaluation)


@router.get(
    "/evaluation/{entry_id}/latest-completed",
    response_model=LatestCompletedEvaluationResponse,
)
async def get_latest_completed_evaluation(
    entry_id: int,
    service: FPLDecisionService = Depends(get_decision_service),
) -> LatestCompletedEvaluationResponse:
    """Return the evaluation of the most recent completed gameweek that has
    a recorded decision snapshot for this entry.

    Independent of whichever gameweek `/evaluation/{entry_id}` currently
    resolves to: this exists so a dashboard can still showcase real
    evaluation history while the current gameweek is `not_completed`.
    `available` is False and `evaluation` is null - never a fabricated
    result - when no completed gameweek before the current one has a
    recorded snapshot yet. This endpoint is a thin HTTP boundary like
    the others here: it delegates entirely to
    `FPLDecisionService.evaluate_latest_completed_gameweek`.
    """
    try:
        evaluation = await service.evaluate_latest_completed_gameweek(
            entry_id=entry_id,
        )
    except FPLDataError as exc:
        raise _http_error_for(exc) from exc

    return latest_completed_evaluation_to_response(evaluation)