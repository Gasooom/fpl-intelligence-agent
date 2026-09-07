from __future__ import annotations

from fpl_agent.api.evaluation_schemas import (
    CaptainEvaluationResponse,
    GameweekEvaluationResponse,
    PlayerEvaluationResponse,
    StartingXIEvaluationResponse,
    TransferEvaluationResponse,
)
from fpl_agent.decisions.evaluation import (
    CaptainEvaluation,
    GameweekEvaluation,
    PlayerEvaluation,
    StartingXIEvaluation,
    TransferEvaluation,
)


def _player_evaluation_to_response(
    evaluation: PlayerEvaluation,
) -> PlayerEvaluationResponse:
    return PlayerEvaluationResponse(
        player_id=evaluation.player_id,
        web_name=evaluation.web_name,
        position_type=evaluation.position_type,
        expected_points=evaluation.expected_points,
        actual_points=evaluation.actual_points,
        prediction_error=evaluation.prediction_error,
    )


def _captain_evaluation_to_response(
    evaluation: CaptainEvaluation,
) -> CaptainEvaluationResponse:
    return CaptainEvaluationResponse(
        captain_player_id=evaluation.captain_player_id,
        captain_web_name=evaluation.captain_web_name,
        captain_expected_points=evaluation.captain_expected_points,
        vice_captain_player_id=evaluation.vice_captain_player_id,
        vice_captain_web_name=evaluation.vice_captain_web_name,
        captain_actual_points=evaluation.captain_actual_points,
        vice_captain_actual_points=evaluation.vice_captain_actual_points,
        outcome=evaluation.outcome,
    )


def _starting_xi_evaluation_to_response(
    evaluation: StartingXIEvaluation,
) -> StartingXIEvaluationResponse:
    return StartingXIEvaluationResponse(
        starting_xi_actual_total=evaluation.starting_xi_actual_total,
        bench_actual_total=evaluation.bench_actual_total,
        difference=evaluation.difference,
        starting_xi_expected_total=evaluation.starting_xi_expected_total,
        prediction_error=evaluation.prediction_error,
    )


def _transfer_evaluation_to_response(
    evaluation: TransferEvaluation,
) -> TransferEvaluationResponse:
    return TransferEvaluationResponse(
        sell_player_id=evaluation.sell_player_id,
        sell_web_name=evaluation.sell_web_name,
        buy_player_id=evaluation.buy_player_id,
        buy_web_name=evaluation.buy_web_name,
        expected_improvement=evaluation.expected_improvement,
        sell_actual_points=evaluation.sell_actual_points,
        buy_actual_points=evaluation.buy_actual_points,
        actual_improvement=evaluation.actual_improvement,
        prediction_error=evaluation.prediction_error,
        direction=evaluation.direction,
    )


def gameweek_evaluation_to_response(
    evaluation: GameweekEvaluation,
) -> GameweekEvaluationResponse:
    """Convert a deterministic gameweek evaluation to an API response."""
    return GameweekEvaluationResponse(
        entry_id=evaluation.entry_id,
        gameweek=evaluation.gameweek,
        status=evaluation.status,
        message=evaluation.message,
        decision_generated_at=evaluation.decision_generated_at,
        captain=(
            _captain_evaluation_to_response(evaluation.captain)
            if evaluation.captain is not None
            else None
        ),
        starting_xi=(
            _starting_xi_evaluation_to_response(evaluation.starting_xi)
            if evaluation.starting_xi is not None
            else None
        ),
        best_transfer=(
            _transfer_evaluation_to_response(evaluation.best_transfer)
            if evaluation.best_transfer is not None
            else None
        ),
        starting_xi_players=[
            _player_evaluation_to_response(player)
            for player in evaluation.starting_xi_players
        ],
        bench_players=[
            _player_evaluation_to_response(player)
            for player in evaluation.bench_players
        ],
    )
