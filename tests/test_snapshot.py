from __future__ import annotations

from fpl_agent.analysis.sell_scoring import SellScore
from fpl_agent.decisions.gameweek_decision import GameweekDecision
from fpl_agent.decisions.snapshot import SnapshotPlayer, SnapshotTransfer, build_decision_snapshot
from fpl_agent.decisions.squad_analysis import SquadPlayerAnalysis
from fpl_agent.decisions.transfer_analysis import BuyCandidate, SellCandidate, TransferPair


def make_player(player_id: int, expected_points: float) -> SquadPlayerAnalysis:
    return SquadPlayerAnalysis(
        player_id=player_id,
        web_name=f"Player {player_id}",
        position_type=3,
        team_id=1,
        price=5.0,
        form=5.0,
        points_per_game=5.0,
        points_per_90=5.0,
        xgi_per_90=0.5,
        fixture_difficulty=2.0,
        expected_points=expected_points,
        minutes_risk=0.0,
        form_uncertainty=0.0,
        fixture_risk=0.0,
        availability_risk=0.0,
        overall_risk=0.2,
        risk_level="low",
        sample_confidence=1.0,
        captaincy_score=5.0,
        selection_score=5.0,
    )


def make_transfer_pair() -> TransferPair:
    sell = SellCandidate(
        player_id=20,
        web_name="Weak Player",
        position_type=2,
        team_id=6,
        price=4.5,
        expected_points=1.71,
        form=3.3,
        fixture_difficulty=5.0,
        overall_risk=0.7,
        availability_risk=0.5,
        risk_level="high",
        sample_confidence=0.25,
        selection_score=-0.5,
        sell_score=SellScore(
            player_id=20,
            score=5.5,
            risk_penalty=2.8,
            low_projection_penalty=2.5,
            difficult_fixture_penalty=0.5,
            availability_penalty=1.5,
            low_confidence_penalty=0.5,
        ),
        rank=1,
        reasons=["High overall risk"],
    )
    buy = BuyCandidate(
        player_id=21,
        web_name="Strong Target",
        position_type=2,
        team_id=7,
        price=5.5,
        expected_points=9.73,
        form=9.3,
        fixture_difficulty=2.0,
        overall_risk=0.1,
        availability_risk=0.0,
        risk_level="medium",
        sample_confidence=1.0,
        selection_score=8.6,
        value_score=0.15,
        rank=1,
        reasons=["Expected points: 9.73"],
    )
    return TransferPair(
        sell=sell,
        buy=buy,
        # Deliberately different from expected_point_gain below (mirrors
        # the live Coppola -> Bogle case: net_improvement 9.70 vs
        # expected_point_gain 8.08) so a snapshot that wrongly reads
        # net_improvement is caught by the assertion below.
        net_improvement=9.7,
        risk_change=0.6,
        price_change=1.0,
        within_budget=True,
        priority="essential",
        reasons=["Higher expected points"],
        expected_point_gain=8.08,
        hit_cost=None,
        net_value=None,
    )


def make_decision(best_transfer: TransferPair | None) -> GameweekDecision:
    starting_xi = [make_player(1, 10.31), make_player(2, 8.25)]
    bench = [make_player(3, 3.0)]

    return GameweekDecision(
        gameweek=3,
        generated_at="2026-08-10T09:00:00+00:00",
        decision_engine_version="v1",
        data_source="official-fpl-api",
        starting_xi=starting_xi,
        bench=bench,
        captain=starting_xi[0],
        vice_captain=starting_xi[1],
        must_play=[],
        sell_candidates=[],
        buy_candidates=[],
        transfer_recommendations=[best_transfer] if best_transfer else [],
        transfer_count=1 if best_transfer else 0,
        best_transfer=best_transfer,
        free_transfers_available=None,
        in_the_bank=None,
        starting_xi_expected_points=18.56,
        projected_gameweek_points=28.87,
        confidence="Low",
        decision_summary="...",
        evidence=[],
    )


def test_build_decision_snapshot_preserves_captain_vice_and_squad_ids() -> None:
    decision = make_decision(best_transfer=None)

    snapshot = build_decision_snapshot(entry_id=8731757, decision=decision)

    assert snapshot.entry_id == 8731757
    assert snapshot.gameweek == 3
    assert snapshot.generated_at == "2026-08-10T09:00:00+00:00"
    assert snapshot.decision_engine_version == "v1"
    assert snapshot.confidence == "Low"
    assert snapshot.captain_player_id == 1
    assert snapshot.captain_web_name == "Player 1"
    assert snapshot.vice_captain_player_id == 2
    assert snapshot.vice_captain_web_name == "Player 2"
    assert snapshot.starting_xi == [
        SnapshotPlayer(player_id=1, web_name="Player 1", position_type=3, expected_points=10.31),
        SnapshotPlayer(player_id=2, web_name="Player 2", position_type=3, expected_points=8.25),
    ]
    assert snapshot.bench == [
        SnapshotPlayer(player_id=3, web_name="Player 3", position_type=3, expected_points=3.0),
    ]


def test_build_decision_snapshot_preserves_best_transfer() -> None:
    pair = make_transfer_pair()
    decision = make_decision(best_transfer=pair)

    snapshot = build_decision_snapshot(entry_id=8731757, decision=decision)

    assert snapshot.best_transfer == SnapshotTransfer(
        sell_player_id=20,
        sell_web_name="Weak Player",
        buy_player_id=21,
        buy_web_name="Strong Target",
        expected_improvement=8.08,
        priority="essential",
    )


def test_snapshot_expected_improvement_uses_expected_point_gain_not_net_improvement() -> None:
    """Regression test: the Decision Evaluation "Expected" figure must be
    the same buy.expected_points - sell.expected_points value shown on the
    Recommended Plan card, never the net_improvement selection-score delta -
    otherwise "Expected" and "Prediction error" are computed against a
    number the user never actually saw."""
    pair = make_transfer_pair()
    assert pair.net_improvement != pair.expected_point_gain
    decision = make_decision(best_transfer=pair)

    snapshot = build_decision_snapshot(entry_id=8731757, decision=decision)

    assert snapshot.best_transfer is not None
    assert snapshot.best_transfer.expected_improvement == pair.expected_point_gain
    assert snapshot.best_transfer.expected_improvement != pair.net_improvement


def test_build_decision_snapshot_allows_no_best_transfer() -> None:
    decision = make_decision(best_transfer=None)

    snapshot = build_decision_snapshot(entry_id=8731757, decision=decision)

    assert snapshot.best_transfer is None
