from __future__ import annotations

from dataclasses import dataclass

from fpl_agent.decisions.gameweek_decision import GameweekDecision


@dataclass(frozen=True)
class SnapshotPlayer:
    """The fields of a squad player needed to evaluate a decision later.

    `position_type` is stored rather than looked up later for the same
    reason as `web_name`: a player-by-player evaluation has to group
    the squad exactly as the original decision did, and today's data is
    not a safe source for what was true at decision time.
    """

    player_id: int
    web_name: str
    position_type: int
    expected_points: float


@dataclass(frozen=True)
class SnapshotTransfer:
    """The best-transfer fields needed to evaluate a decision later."""

    sell_player_id: int
    sell_web_name: str
    buy_player_id: int
    buy_web_name: str
    # buy.expected_points - sell.expected_points (same figure the
    # Recommended Plan card shows as "expected points" - never the
    # net_improvement selection-score delta).
    expected_improvement: float
    priority: str


@dataclass(frozen=True)
class DecisionSnapshot:
    """Enough of a gameweek decision, preserved verbatim, to evaluate it later.

    The live FPL API only ever describes the current state of the
    world - it cannot say what the deterministic engine recommended
    three days ago, because bootstrap data (form, price, total points)
    keeps moving forward. This is the fix: a snapshot written once,
    before the gameweek is played, and never overwritten, so a later
    evaluation always measures the decision that was actually made
    rather than one recomputed today from data that has since changed.

    Player names are stored alongside the IDs for the same reason: a
    decision recomputed today can legitimately recommend different
    players than the snapshot did, so an evaluation cannot rely on the
    current decision response to name the players it is evaluating.
    """

    entry_id: int
    gameweek: int
    generated_at: str
    decision_engine_version: str
    confidence: str
    captain_player_id: int
    captain_web_name: str
    vice_captain_player_id: int
    vice_captain_web_name: str
    starting_xi: list[SnapshotPlayer]
    bench: list[SnapshotPlayer]
    best_transfer: SnapshotTransfer | None


def build_decision_snapshot(
    entry_id: int,
    decision: GameweekDecision,
) -> DecisionSnapshot:
    """Extract exactly the fields needed to evaluate this decision later."""
    best_transfer = (
        SnapshotTransfer(
            sell_player_id=decision.best_transfer.sell.player_id,
            sell_web_name=decision.best_transfer.sell.web_name,
            buy_player_id=decision.best_transfer.buy.player_id,
            buy_web_name=decision.best_transfer.buy.web_name,
            # expected_point_gain (buy.expected_points - sell.expected_points)
            # is the same figure shown to users as "expected points" on the
            # Recommended Plan card - never net_improvement, a
            # selection-score delta that also factors in form/confidence/
            # risk and is not comparable to actual_points on the same scale.
            expected_improvement=decision.best_transfer.expected_point_gain,
            priority=decision.best_transfer.priority,
        )
        if decision.best_transfer is not None
        else None
    )

    return DecisionSnapshot(
        entry_id=entry_id,
        gameweek=decision.gameweek,
        generated_at=decision.generated_at,
        decision_engine_version=decision.decision_engine_version,
        confidence=decision.confidence,
        captain_player_id=decision.captain.player_id,
        captain_web_name=decision.captain.web_name,
        vice_captain_player_id=decision.vice_captain.player_id,
        vice_captain_web_name=decision.vice_captain.web_name,
        starting_xi=[
            SnapshotPlayer(
                player_id=player.player_id,
                web_name=player.web_name,
                position_type=player.position_type,
                expected_points=player.expected_points,
            )
            for player in decision.starting_xi
        ],
        bench=[
            SnapshotPlayer(
                player_id=player.player_id,
                web_name=player.web_name,
                position_type=player.position_type,
                expected_points=player.expected_points,
            )
            for player in decision.bench
        ],
        best_transfer=best_transfer,
    )
