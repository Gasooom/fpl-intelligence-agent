from __future__ import annotations

import pytest

from fpl_agent.decisions.evaluation import (
    STATUS_EVALUATED,
    STATUS_NO_SNAPSHOT,
    STATUS_NOT_COMPLETED,
    MissingOutcomeDataError,
    build_captain_evaluation,
    build_gameweek_evaluation,
    build_missing_snapshot_evaluation,
    build_not_completed_evaluation,
    build_player_evaluations,
    build_starting_xi_evaluation,
    build_transfer_evaluation,
)
from fpl_agent.decisions.outcomes import PlayerActualOutcome
from fpl_agent.decisions.snapshot import DecisionSnapshot, SnapshotPlayer, SnapshotTransfer


def outcomes(*points: tuple[int, int]) -> dict[int, PlayerActualOutcome]:
    return {
        player_id: PlayerActualOutcome(player_id=player_id, gameweek=3, actual_points=total)
        for player_id, total in points
    }


def player(
    player_id: int,
    expected_points: float,
    position_type: int = 3,
) -> SnapshotPlayer:
    return SnapshotPlayer(
        player_id=player_id,
        web_name=f"Player {player_id}",
        position_type=position_type,
        expected_points=expected_points,
    )


def make_snapshot(
    captain_id: int = 1,
    vice_id: int = 2,
    starting_xi: list[SnapshotPlayer] | None = None,
    bench: list[SnapshotPlayer] | None = None,
    best_transfer: SnapshotTransfer | None = None,
) -> DecisionSnapshot:
    return DecisionSnapshot(
        entry_id=8731757,
        gameweek=3,
        generated_at="2026-08-10T09:00:00+00:00",
        decision_engine_version="v1",
        confidence="Low",
        captain_player_id=captain_id,
        captain_web_name=f"Player {captain_id}",
        vice_captain_player_id=vice_id,
        vice_captain_web_name=f"Player {vice_id}",
        starting_xi=starting_xi if starting_xi is not None else [player(1, 10.31)],
        bench=bench if bench is not None else [],
        best_transfer=best_transfer,
    )


# --- Captain evaluation ---


def test_captain_outcome_is_correct_when_captain_outscores_vice() -> None:
    snapshot = make_snapshot(captain_id=1, vice_id=2)
    evaluation = build_captain_evaluation(snapshot, outcomes((1, 12), (2, 4)))

    assert evaluation.captain_actual_points == 12
    assert evaluation.vice_captain_actual_points == 4
    assert evaluation.outcome == "correct"


def test_captain_outcome_is_missed_when_vice_outscores_captain() -> None:
    snapshot = make_snapshot(captain_id=1, vice_id=2)
    evaluation = build_captain_evaluation(snapshot, outcomes((1, 2), (2, 9)))

    assert evaluation.outcome == "missed"


def test_captain_outcome_is_tied_when_captain_and_vice_score_equally() -> None:
    snapshot = make_snapshot(captain_id=1, vice_id=2)
    evaluation = build_captain_evaluation(snapshot, outcomes((1, 6), (2, 6)))

    assert evaluation.outcome == "tied"


def test_captain_outcome_uses_raw_points_not_a_multiplier() -> None:
    """A captain who scores fewer raw points than the vice is "missed",
    even though the FPL multiplier would have doubled the captain's
    score - see CaptainEvaluation's docstring for why raw points are
    used."""
    snapshot = make_snapshot(captain_id=1, vice_id=2)
    evaluation = build_captain_evaluation(snapshot, outcomes((1, 3), (2, 5)))

    assert evaluation.outcome == "missed"


def test_captain_evaluation_raises_on_missing_outcome_data() -> None:
    snapshot = make_snapshot(captain_id=1, vice_id=2)

    with pytest.raises(MissingOutcomeDataError):
        build_captain_evaluation(snapshot, outcomes((1, 12)))


# --- Starting XI evaluation ---


def test_starting_xi_evaluation_computes_actual_totals_and_difference() -> None:
    snapshot = make_snapshot(
        starting_xi=[player(1, 5.0), player(2, 4.0)],
        bench=[player(3, 2.0)],
    )
    evaluation = build_starting_xi_evaluation(snapshot, outcomes((1, 8), (2, 3), (3, 15)))

    assert evaluation.starting_xi_actual_total == 11
    assert evaluation.bench_actual_total == 15
    assert evaluation.difference == -4


def test_starting_xi_evaluation_computes_prediction_error_from_snapshot_expected_points() -> None:
    snapshot = make_snapshot(
        starting_xi=[player(1, 5.0), player(2, 4.0)],
        bench=[],
    )
    evaluation = build_starting_xi_evaluation(snapshot, outcomes((1, 8), (2, 3)))

    assert evaluation.starting_xi_expected_total == 9.0
    assert evaluation.starting_xi_actual_total == 11
    assert evaluation.prediction_error == 2.0


def test_starting_xi_evaluation_handles_an_empty_bench() -> None:
    snapshot = make_snapshot(starting_xi=[player(1, 5.0)], bench=[])
    evaluation = build_starting_xi_evaluation(snapshot, outcomes((1, 5)))

    assert evaluation.bench_actual_total == 0
    assert evaluation.difference == 5


# --- Transfer evaluation ---


def test_transfer_evaluation_positive_direction_when_buy_outscores_sell() -> None:
    transfer = SnapshotTransfer(
        sell_player_id=20,
        sell_web_name="Neto",
        buy_player_id=21,
        buy_web_name="Gakpo",
        expected_improvement=8.13,
        priority="essential",
    )
    evaluation = build_transfer_evaluation(transfer, outcomes((20, 1), (21, 7)))

    assert evaluation.sell_actual_points == 1
    assert evaluation.buy_actual_points == 7
    assert evaluation.actual_improvement == 6
    assert evaluation.prediction_error == pytest.approx(6 - 8.13)
    assert evaluation.direction == "positive"


def test_transfer_evaluation_matches_the_worked_example_from_the_spec() -> None:
    """Expected +8.13, actual +6.00 -> error -2.13, direction positive -
    directionally beneficial even though the exact gain was
    overestimated."""
    transfer = SnapshotTransfer(
        sell_player_id=20,
        sell_web_name="Neto",
        buy_player_id=21,
        buy_web_name="Gakpo",
        expected_improvement=8.13,
        priority="essential",
    )
    evaluation = build_transfer_evaluation(transfer, outcomes((20, 0), (21, 6)))

    assert evaluation.actual_improvement == 6
    assert evaluation.prediction_error == pytest.approx(-2.13)
    assert evaluation.direction == "positive"


def test_transfer_evaluation_negative_direction_when_sell_outscores_buy() -> None:
    transfer = SnapshotTransfer(
        sell_player_id=20,
        sell_web_name="Neto",
        buy_player_id=21,
        buy_web_name="Gakpo",
        expected_improvement=5.0,
        priority="strong",
    )
    evaluation = build_transfer_evaluation(transfer, outcomes((20, 10), (21, 2)))

    assert evaluation.actual_improvement == -8
    assert evaluation.direction == "negative"


def test_transfer_evaluation_neutral_direction_when_scores_are_equal() -> None:
    transfer = SnapshotTransfer(
        sell_player_id=20,
        sell_web_name="Neto",
        buy_player_id=21,
        buy_web_name="Gakpo",
        expected_improvement=5.0,
        priority="strong",
    )
    evaluation = build_transfer_evaluation(transfer, outcomes((20, 4), (21, 4)))

    assert evaluation.actual_improvement == 0
    assert evaluation.direction == "neutral"


# --- Top-level status states ---


def test_not_completed_evaluation_has_no_sub_evaluations() -> None:
    evaluation = build_not_completed_evaluation(entry_id=8731757, gameweek=4)

    assert evaluation.status == STATUS_NOT_COMPLETED
    assert evaluation.captain is None
    assert evaluation.starting_xi is None
    assert evaluation.best_transfer is None
    assert "not completed" in evaluation.message.lower()


def test_missing_snapshot_evaluation_has_no_sub_evaluations() -> None:
    evaluation = build_missing_snapshot_evaluation(entry_id=8731757, gameweek=3)

    assert evaluation.status == STATUS_NO_SNAPSHOT
    assert evaluation.captain is None
    assert evaluation.starting_xi is None
    assert evaluation.best_transfer is None
    assert "no decision snapshot" in evaluation.message.lower()


def test_gameweek_evaluation_combines_all_sub_evaluations_when_a_transfer_exists() -> None:
    transfer = SnapshotTransfer(
        sell_player_id=20,
        sell_web_name="Neto",
        buy_player_id=21,
        buy_web_name="Gakpo",
        expected_improvement=8.13,
        priority="essential",
    )
    snapshot = make_snapshot(
        captain_id=1,
        vice_id=2,
        starting_xi=[player(1, 10.0), player(2, 8.0)],
        bench=[player(3, 2.0)],
        best_transfer=transfer,
    )

    evaluation = build_gameweek_evaluation(
        snapshot,
        outcomes((1, 12), (2, 4), (3, 1), (20, 0), (21, 6)),
    )

    assert evaluation.status == STATUS_EVALUATED
    assert evaluation.entry_id == 8731757
    assert evaluation.gameweek == 3
    assert evaluation.decision_generated_at == "2026-08-10T09:00:00+00:00"
    assert evaluation.captain is not None
    assert evaluation.captain.outcome == "correct"
    assert evaluation.starting_xi is not None
    assert evaluation.starting_xi.starting_xi_actual_total == 16
    assert evaluation.best_transfer is not None
    assert evaluation.best_transfer.direction == "positive"


def test_gameweek_evaluation_omits_best_transfer_when_none_was_recommended() -> None:
    snapshot = make_snapshot(best_transfer=None)

    evaluation = build_gameweek_evaluation(snapshot, outcomes((1, 12), (2, 4)))

    assert evaluation.status == STATUS_EVALUATED
    assert evaluation.best_transfer is None
    # Only real, present data is shown - no invented transfer.


# --- Player-level evaluation ---


def test_every_squad_player_is_evaluated_individually() -> None:
    snapshot = make_snapshot(
        starting_xi=[player(1, 10.31, 1), player(2, 5.0, 2)],
        bench=[player(3, 2.0, 3), player(4, 1.0, 4)],
    )
    outcome_data = outcomes((1, 12), (2, 5), (3, 0), (4, 9))

    xi = build_player_evaluations(snapshot.starting_xi, outcome_data)
    bench = build_player_evaluations(snapshot.bench, outcome_data)

    assert len(xi) == 2
    assert len(bench) == 2
    assert [p.player_id for p in xi] == [1, 2]
    assert [p.player_id for p in bench] == [3, 4]


def test_player_evaluation_uses_snapshot_expected_points_and_real_actual_points() -> None:
    snapshot = make_snapshot(starting_xi=[player(1, 10.31)], bench=[])

    result = build_player_evaluations(snapshot.starting_xi, outcomes((1, 12)))[0]

    assert result.web_name == "Player 1"
    assert result.expected_points == 10.31
    assert result.actual_points == 12
    assert result.prediction_error == 1.69


def test_player_prediction_error_is_negative_when_a_player_underperforms() -> None:
    snapshot = make_snapshot(starting_xi=[player(20, 1.71)], bench=[])

    result = build_player_evaluations(snapshot.starting_xi, outcomes((20, 1)))[0]

    assert result.prediction_error == -0.71


def test_player_prediction_error_is_zero_when_the_projection_lands_exactly() -> None:
    snapshot = make_snapshot(starting_xi=[player(1, 6.0)], bench=[])

    result = build_player_evaluations(snapshot.starting_xi, outcomes((1, 6)))[0]

    assert result.prediction_error == 0.0


def test_player_evaluation_preserves_position_grouping_order_from_the_snapshot() -> None:
    """GK -> DEF -> MID -> FWD is part of the recorded decision, and a
    higher-scoring player must never be promoted up the list."""
    snapshot = make_snapshot(
        starting_xi=[player(1, 3.0, 1), player(2, 4.0, 2), player(3, 9.0, 3), player(4, 2.0, 4)],
        bench=[],
    )

    result = build_player_evaluations(
        snapshot.starting_xi,
        outcomes((1, 1), (2, 2), (3, 20), (4, 0)),
    )

    assert [p.position_type for p in result] == [1, 2, 3, 4]
    assert [p.player_id for p in result] == [1, 2, 3, 4]


def test_player_evaluation_raises_when_a_player_has_no_actual_result() -> None:
    snapshot = make_snapshot(starting_xi=[player(1, 5.0), player(99, 5.0)], bench=[])

    with pytest.raises(MissingOutcomeDataError):
        build_player_evaluations(snapshot.starting_xi, outcomes((1, 5)))


def test_captain_evaluation_reports_expected_points_from_the_snapshot() -> None:
    snapshot = make_snapshot(
        captain_id=1,
        vice_id=2,
        starting_xi=[player(1, 10.31), player(2, 8.25)],
    )

    result = build_captain_evaluation(snapshot, outcomes((1, 12), (2, 4)))

    assert result.captain_expected_points == 10.31
    assert result.captain_actual_points == 12


def test_gameweek_evaluation_includes_every_player_in_both_groups() -> None:
    snapshot = make_snapshot(
        captain_id=1,
        vice_id=2,
        starting_xi=[player(1, 10.0), player(2, 8.0)],
        bench=[player(3, 2.0)],
    )

    result = build_gameweek_evaluation(snapshot, outcomes((1, 12), (2, 4), (3, 1)))

    assert [p.player_id for p in result.starting_xi_players] == [1, 2]
    assert [p.player_id for p in result.bench_players] == [3]


def test_non_evaluated_states_carry_no_player_evaluations() -> None:
    not_completed = build_not_completed_evaluation(entry_id=8731757, gameweek=4)
    no_snapshot = build_missing_snapshot_evaluation(entry_id=8731757, gameweek=3)

    assert not_completed.starting_xi_players == []
    assert not_completed.bench_players == []
    assert no_snapshot.starting_xi_players == []
    assert no_snapshot.bench_players == []
