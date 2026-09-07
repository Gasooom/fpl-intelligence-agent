from __future__ import annotations

from dataclasses import dataclass

from fpl_agent.decisions.outcomes import PlayerActualOutcome
from fpl_agent.decisions.snapshot import DecisionSnapshot, SnapshotPlayer, SnapshotTransfer

# Status values. Plain strings, not an enum, to match the rest of the
# API surface (risk_level, confidence, priority, evidence.decision are
# all plain backend strings elsewhere in this project too).
STATUS_NOT_COMPLETED = "not_completed"
STATUS_NO_SNAPSHOT = "no_snapshot"
STATUS_EVALUATED = "evaluated"

_OUTCOME_CORRECT = "correct"
_OUTCOME_MISSED = "missed"
_OUTCOME_TIED = "tied"

_DIRECTION_POSITIVE = "positive"
_DIRECTION_NEUTRAL = "neutral"
_DIRECTION_NEGATIVE = "negative"


class MissingOutcomeDataError(ValueError):
    """Raised when a snapshot references a player absent from actual outcomes.

    The live FPL endpoint returns every element in the game, so this
    should not happen in practice; if it does, that is a genuine data
    problem that must be surfaced, never papered over with a fabricated
    0.
    """


@dataclass(frozen=True)
class PlayerEvaluation:
    """One squad player's prediction measured against what he scored.

    `expected_points` is read verbatim from the decision snapshot, so
    it is what the engine predicted at decision time - never a figure
    recomputed from today's data. `prediction_error` is actual minus
    expected: negative simply means the player scored less than
    predicted, which is a projection miss, not a failed decision.
    """

    player_id: int
    web_name: str
    position_type: int
    expected_points: float
    actual_points: int
    prediction_error: float


@dataclass(frozen=True)
class CaptainEvaluation:
    """Predicted captain/vice-captain vs. their real gameweek points.

    `outcome` is decided purely from raw actual points - never from
    the pre-gameweek expected points - because the question this
    answers is "did the captain call work out", not "was the
    projection accurate".
    """

    captain_player_id: int
    captain_web_name: str
    captain_expected_points: float
    vice_captain_player_id: int
    vice_captain_web_name: str
    captain_actual_points: int
    vice_captain_actual_points: int
    outcome: str


@dataclass(frozen=True)
class StartingXIEvaluation:
    """Starting XI vs. bench, by real points actually scored.

    `difference` is the one comparison number a caller needs; the sign
    alone determines whether the XI outscored the bench, without this
    module asserting a verdict like "successful" for what may simply
    be a close, ordinary week. `prediction_error` is only meaningful
    because expected_points for every starting player was preserved in
    the snapshot at decision time.
    """

    starting_xi_actual_total: int
    bench_actual_total: int
    difference: int
    starting_xi_expected_total: float
    prediction_error: float


@dataclass(frozen=True)
class TransferEvaluation:
    """The recommended best transfer's projected vs. actual improvement.

    `direction` reflects whether the transfer actually helped
    (buy scored more than sell, in real points) regardless of how
    close the actual improvement came to the pre-gameweek projection -
    a transfer can be directionally positive even when the engine
    overestimated (or underestimated) the exact size of the gain.
    """

    sell_player_id: int
    sell_web_name: str
    buy_player_id: int
    buy_web_name: str
    expected_improvement: float
    sell_actual_points: int
    buy_actual_points: int
    actual_improvement: int
    prediction_error: float
    direction: str


@dataclass(frozen=True)
class GameweekEvaluation:
    """The full evaluation of one entry's gameweek decision.

    `status` gates which of the sub-evaluations are populated:
    anything other than "evaluated" means every sub-evaluation is
    None, and `message` explains why in plain language grounded in
    real system state - never a fabricated result.
    """

    entry_id: int
    gameweek: int
    status: str
    message: str
    decision_generated_at: str | None
    captain: CaptainEvaluation | None
    starting_xi: StartingXIEvaluation | None
    best_transfer: TransferEvaluation | None
    # Both preserve the snapshot's own order - the starting XI arrives
    # already grouped goalkeeper -> defender -> midfielder -> forward,
    # and the bench in substitute order. Nothing here re-sorts or ranks
    # players by what they scored.
    starting_xi_players: list[PlayerEvaluation]
    bench_players: list[PlayerEvaluation]


def _actual_points(
    player_id: int,
    outcomes: dict[int, PlayerActualOutcome],
) -> int:
    outcome = outcomes.get(player_id)

    if outcome is None:
        raise MissingOutcomeDataError(
            f"No actual outcome data was returned for player_id={player_id}.",
        )

    return outcome.actual_points


def _captain_outcome(captain_points: int, vice_points: int) -> str:
    if captain_points > vice_points:
        return _OUTCOME_CORRECT

    if captain_points < vice_points:
        return _OUTCOME_MISSED

    return _OUTCOME_TIED


def build_player_evaluations(
    players: list[SnapshotPlayer],
    outcomes: dict[int, PlayerActualOutcome],
) -> list[PlayerEvaluation]:
    """Measure each snapshot player's prediction against his real points.

    Returns them in the snapshot's own order - grouping and bench order
    are part of the recorded decision, so they are preserved rather
    than re-sorted by score or error.
    """
    evaluations: list[PlayerEvaluation] = []

    for player in players:
        actual_points = _actual_points(player.player_id, outcomes)
        evaluations.append(
            PlayerEvaluation(
                player_id=player.player_id,
                web_name=player.web_name,
                position_type=player.position_type,
                expected_points=player.expected_points,
                actual_points=actual_points,
                prediction_error=round(actual_points - player.expected_points, 2),
            ),
        )

    return evaluations


def _snapshot_expected_points(snapshot: DecisionSnapshot, player_id: int) -> float:
    """Look up one player's expected points as recorded at decision time."""
    for player in [*snapshot.starting_xi, *snapshot.bench]:
        if player.player_id == player_id:
            return player.expected_points

    raise MissingOutcomeDataError(
        f"player_id={player_id} is not present in the recorded squad snapshot.",
    )


def build_captain_evaluation(
    snapshot: DecisionSnapshot,
    outcomes: dict[int, PlayerActualOutcome],
) -> CaptainEvaluation:
    """Compare the predicted captain and vice-captain's real points.

    Deliberately uses raw player points, not the FPL captain multiplier
    - see the module docstring in decisions/evaluation.py's
    CaptainEvaluation for why.
    """
    captain_points = _actual_points(snapshot.captain_player_id, outcomes)
    vice_points = _actual_points(snapshot.vice_captain_player_id, outcomes)

    return CaptainEvaluation(
        captain_player_id=snapshot.captain_player_id,
        captain_web_name=snapshot.captain_web_name,
        captain_expected_points=_snapshot_expected_points(
            snapshot,
            snapshot.captain_player_id,
        ),
        vice_captain_player_id=snapshot.vice_captain_player_id,
        vice_captain_web_name=snapshot.vice_captain_web_name,
        captain_actual_points=captain_points,
        vice_captain_actual_points=vice_points,
        outcome=_captain_outcome(captain_points, vice_points),
    )


def build_starting_xi_evaluation(
    snapshot: DecisionSnapshot,
    outcomes: dict[int, PlayerActualOutcome],
) -> StartingXIEvaluation:
    """Compare the starting XI's and bench's real points."""
    xi_actual_total = sum(
        _actual_points(player.player_id, outcomes) for player in snapshot.starting_xi
    )
    bench_actual_total = sum(
        _actual_points(player.player_id, outcomes) for player in snapshot.bench
    )
    expected_total = round(
        sum(player.expected_points for player in snapshot.starting_xi),
        2,
    )

    return StartingXIEvaluation(
        starting_xi_actual_total=xi_actual_total,
        bench_actual_total=bench_actual_total,
        difference=xi_actual_total - bench_actual_total,
        starting_xi_expected_total=expected_total,
        prediction_error=round(xi_actual_total - expected_total, 2),
    )


def _transfer_direction(actual_improvement: int) -> str:
    if actual_improvement > 0:
        return _DIRECTION_POSITIVE

    if actual_improvement < 0:
        return _DIRECTION_NEGATIVE

    return _DIRECTION_NEUTRAL


def build_transfer_evaluation(
    transfer: SnapshotTransfer,
    outcomes: dict[int, PlayerActualOutcome],
) -> TransferEvaluation:
    """Compare the recommended best transfer's projected vs. actual improvement."""
    sell_points = _actual_points(transfer.sell_player_id, outcomes)
    buy_points = _actual_points(transfer.buy_player_id, outcomes)
    actual_improvement = buy_points - sell_points

    return TransferEvaluation(
        sell_player_id=transfer.sell_player_id,
        sell_web_name=transfer.sell_web_name,
        buy_player_id=transfer.buy_player_id,
        buy_web_name=transfer.buy_web_name,
        expected_improvement=transfer.expected_improvement,
        sell_actual_points=sell_points,
        buy_actual_points=buy_points,
        actual_improvement=actual_improvement,
        prediction_error=round(actual_improvement - transfer.expected_improvement, 2),
        direction=_transfer_direction(actual_improvement),
    )


def build_not_completed_evaluation(entry_id: int, gameweek: int) -> GameweekEvaluation:
    """The honest state for a gameweek that has not finished yet."""
    return GameweekEvaluation(
        entry_id=entry_id,
        gameweek=gameweek,
        status=STATUS_NOT_COMPLETED,
        message=(
            f"Gameweek {gameweek} is not completed yet. Evaluation becomes "
            "possible once the gameweek finishes and actual results exist."
        ),
        decision_generated_at=None,
        captain=None,
        starting_xi=None,
        best_transfer=None,
        starting_xi_players=[],
        bench_players=[],
    )


def build_missing_snapshot_evaluation(entry_id: int, gameweek: int) -> GameweekEvaluation:
    """The honest state for a finished gameweek with no recorded decision."""
    return GameweekEvaluation(
        entry_id=entry_id,
        gameweek=gameweek,
        status=STATUS_NO_SNAPSHOT,
        message=(
            f"Gameweek {gameweek} has results, but no decision snapshot was "
            "recorded for this entry, so this decision cannot be evaluated."
        ),
        decision_generated_at=None,
        captain=None,
        starting_xi=None,
        best_transfer=None,
        starting_xi_players=[],
        bench_players=[],
    )


def build_gameweek_evaluation(
    snapshot: DecisionSnapshot,
    outcomes: dict[int, PlayerActualOutcome],
) -> GameweekEvaluation:
    """Build the full evaluation from a recorded snapshot and real outcomes."""
    best_transfer_evaluation = (
        build_transfer_evaluation(snapshot.best_transfer, outcomes)
        if snapshot.best_transfer is not None
        else None
    )

    return GameweekEvaluation(
        entry_id=snapshot.entry_id,
        gameweek=snapshot.gameweek,
        status=STATUS_EVALUATED,
        message=f"Evaluated against actual gameweek {snapshot.gameweek} results.",
        decision_generated_at=snapshot.generated_at,
        captain=build_captain_evaluation(snapshot, outcomes),
        starting_xi=build_starting_xi_evaluation(snapshot, outcomes),
        best_transfer=best_transfer_evaluation,
        starting_xi_players=build_player_evaluations(snapshot.starting_xi, outcomes),
        bench_players=build_player_evaluations(snapshot.bench, outcomes),
    )
