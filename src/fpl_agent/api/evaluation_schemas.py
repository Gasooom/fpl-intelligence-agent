from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PlayerEvaluationResponse(BaseModel):
    """One squad player's expected points vs. what he actually scored."""

    model_config = ConfigDict(extra="forbid")

    player_id: int
    web_name: str
    position_type: int
    expected_points: float
    actual_points: int
    prediction_error: float


class CaptainEvaluationResponse(BaseModel):
    """Predicted captain/vice-captain vs. their real gameweek points."""

    model_config = ConfigDict(extra="forbid")

    captain_player_id: int
    captain_web_name: str
    captain_expected_points: float
    vice_captain_player_id: int
    vice_captain_web_name: str
    captain_actual_points: int
    vice_captain_actual_points: int
    outcome: str


class StartingXIEvaluationResponse(BaseModel):
    """Starting XI vs. bench, by real points actually scored."""

    model_config = ConfigDict(extra="forbid")

    starting_xi_actual_total: int
    bench_actual_total: int
    difference: int
    starting_xi_expected_total: float
    prediction_error: float


class TransferEvaluationResponse(BaseModel):
    """The recommended best transfer's projected vs. actual improvement."""

    model_config = ConfigDict(extra="forbid")

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


class GameweekEvaluationResponse(BaseModel):
    """The full evaluation of one entry's gameweek decision.

    `status` is one of "not_completed", "no_snapshot", or "evaluated".
    Anything other than "evaluated" means every sub-evaluation below is
    null, and `message` explains why in plain language.
    """

    model_config = ConfigDict(extra="forbid")

    entry_id: int
    gameweek: int
    status: str
    message: str
    decision_generated_at: str | None

    captain: CaptainEvaluationResponse | None
    starting_xi: StartingXIEvaluationResponse | None
    best_transfer: TransferEvaluationResponse | None

    # In the snapshot's own order: the starting XI already grouped
    # goalkeeper -> defender -> midfielder -> forward, and the bench in
    # substitute order. Empty unless status is "evaluated".
    starting_xi_players: list[PlayerEvaluationResponse]
    bench_players: list[PlayerEvaluationResponse]


class LatestCompletedEvaluationResponse(BaseModel):
    """The most recent completed gameweek's evaluation, if one exists yet.

    Separate from GameweekEvaluationResponse's own not_completed/
    no_snapshot statuses: `available` is False exactly when no completed
    gameweek before the current one has a recorded decision snapshot at
    all, in which case `evaluation` is null rather than a fabricated
    placeholder. When `available` is True, `evaluation.status` is always
    "evaluated".
    """

    model_config = ConfigDict(extra="forbid")

    available: bool
    evaluation: GameweekEvaluationResponse | None
