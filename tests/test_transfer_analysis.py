from __future__ import annotations

import pytest

from fpl_agent.data.models import Fixture, Player, Team
from fpl_agent.decisions.squad_analysis import SquadPlayerAnalysis
from fpl_agent.decisions.transfer_analysis import (
    BuyCandidate,
    SellCandidate,
    build_available_pool_analyses,
    build_transfer_pairs,
    classify_transfer_priority,
    extract_bank_balance,
    rank_buy_candidates,
    rank_sell_candidates,
)


def make_analysis(
    player_id: int,
    web_name: str,
    position_type: int,
    team_id: int,
    expected_points: float,
    overall_risk: float = 0.2,
    availability_risk: float = 0.0,
    sample_confidence: float = 1.0,
    fixture_difficulty: float = 2.0,
    form: float = 5.0,
    price: float = 5.0,
    risk_level: str = "low",
) -> SquadPlayerAnalysis:
    """Directly construct a SquadPlayerAnalysis for transfer-analysis tests."""
    selection_score = round(
        expected_points
        + form * 0.15
        + (sample_confidence - 0.5) * 0.5
        - overall_risk * 2.0,
        2,
    )

    return SquadPlayerAnalysis(
        player_id=player_id,
        web_name=web_name,
        position_type=position_type,
        team_id=team_id,
        price=price,
        form=form,
        points_per_game=5.0,
        points_per_90=5.0,
        xgi_per_90=0.5,
        fixture_difficulty=fixture_difficulty,
        expected_points=expected_points,
        minutes_risk=0.0,
        form_uncertainty=0.0,
        fixture_risk=0.0,
        availability_risk=availability_risk,
        overall_risk=overall_risk,
        risk_level=risk_level,
        sample_confidence=sample_confidence,
        captaincy_score=expected_points,
        selection_score=selection_score,
    )


# --- rank_sell_candidates -----------------------------------------------


def test_rank_sell_candidates_orders_worst_first() -> None:
    strong = make_analysis(
        1, "Strong", 3, 1, expected_points=8.0, overall_risk=0.1,
    )
    average = make_analysis(
        2, "Average", 3, 2, expected_points=5.0, overall_risk=0.3,
    )
    weak = make_analysis(
        3, "Weak", 3, 3, expected_points=1.0, overall_risk=0.7,
    )

    ranked = rank_sell_candidates([strong, average, weak])

    assert [candidate.web_name for candidate in ranked] == [
        "Weak",
        "Average",
        "Strong",
    ]
    assert [candidate.rank for candidate in ranked] == [1, 2, 3]
    assert all(isinstance(c, SellCandidate) for c in ranked)
    assert ranked[0].reasons


def test_sell_candidate_reasons_reflect_weakest_signal_first() -> None:
    high_risk_low_projection = make_analysis(
        1,
        "P",
        3,
        1,
        expected_points=0.0,
        overall_risk=0.9,
    )

    ranked = rank_sell_candidates([high_risk_low_projection])

    assert "High overall risk" in ranked[0].reasons[0]


# --- rank_buy_candidates ---------------------------------------------------


def test_rank_buy_candidates_filters_by_position() -> None:
    pool = [
        make_analysis(1, "GK", 1, 1, expected_points=5.0),
        make_analysis(2, "Def1", 2, 2, expected_points=6.0),
        make_analysis(3, "Def2", 2, 3, expected_points=8.0),
        make_analysis(4, "Mid", 3, 4, expected_points=7.0),
    ]

    result = rank_buy_candidates(pool, position_type=2, limit=10)

    assert [candidate.web_name for candidate in result] == ["Def2", "Def1"]
    assert all(isinstance(c, BuyCandidate) for c in result)
    assert [candidate.rank for candidate in result] == [1, 2]


def test_rank_buy_candidates_respects_limit() -> None:
    pool = [
        make_analysis(i, f"P{i}", 3, i, expected_points=float(i))
        for i in range(1, 6)
    ]

    result = rank_buy_candidates(pool, position_type=3, limit=2)

    assert len(result) == 2
    assert result[0].web_name == "P5"
    assert result[1].web_name == "P4"


def test_rank_buy_candidates_includes_all_positions_when_unspecified() -> None:
    pool = [
        make_analysis(1, "GK", 1, 1, expected_points=5.0),
        make_analysis(2, "Def", 2, 2, expected_points=5.0),
    ]

    result = rank_buy_candidates(pool, position_type=None, limit=10)

    assert {candidate.web_name for candidate in result} == {"GK", "Def"}


# --- classify_transfer_priority -------------------------------------------


def test_classify_transfer_priority_essential_on_large_gain() -> None:
    assert (
        classify_transfer_priority(
            net_improvement=2.5,
            sell_availability_risk=0.0,
            buy_availability_risk=0.0,
        )
        == "essential"
    )


def test_classify_transfer_priority_essential_on_availability_upgrade() -> None:
    assert (
        classify_transfer_priority(
            net_improvement=0.1,
            sell_availability_risk=0.9,
            buy_availability_risk=0.0,
        )
        == "essential"
    )


def test_classify_transfer_priority_strong() -> None:
    assert (
        classify_transfer_priority(
            net_improvement=1.2,
            sell_availability_risk=0.0,
            buy_availability_risk=0.0,
        )
        == "strong"
    )


def test_classify_transfer_priority_optional() -> None:
    assert (
        classify_transfer_priority(
            net_improvement=0.5,
            sell_availability_risk=0.0,
            buy_availability_risk=0.0,
        )
        == "optional"
    )


def test_classify_transfer_priority_avoid() -> None:
    assert (
        classify_transfer_priority(
            net_improvement=0.1,
            sell_availability_risk=0.0,
            buy_availability_risk=0.0,
        )
        == "avoid"
    )


@pytest.mark.parametrize(
    ("net_improvement", "expected_priority"),
    [
        (2.0, "essential"),
        (1.999, "strong"),
        (1.0, "strong"),
        (0.999, "optional"),
        (0.3, "optional"),
        (0.299, "avoid"),
        (0.0, "avoid"),
        (-1.0, "avoid"),
    ],
)
def test_classify_transfer_priority_exact_thresholds(
    net_improvement: float,
    expected_priority: str,
) -> None:
    """Thresholds are inclusive on their lower bound (>=), so the exact
    boundary value belongs to the higher tier, not the lower one.
    """
    assert (
        classify_transfer_priority(
            net_improvement=net_improvement,
            sell_availability_risk=0.0,
            buy_availability_risk=0.0,
        )
        == expected_priority
    )


# --- build_transfer_pairs --------------------------------------------------


def test_build_transfer_pairs_matches_worst_sell_with_best_buy() -> None:
    squad = [
        make_analysis(1, "WeakDef", 2, 1, expected_points=2.0, overall_risk=0.6),
    ]
    pool = [
        make_analysis(10, "StrongDef", 2, 5, expected_points=8.0, overall_risk=0.1),
    ]

    sell_candidates = rank_sell_candidates(squad)
    pairs = build_transfer_pairs(
        sell_candidates=sell_candidates,
        pool_analyses=pool,
        squad_analyses=squad,
    )

    assert len(pairs) == 1
    assert pairs[0].sell.web_name == "WeakDef"
    assert pairs[0].buy.web_name == "StrongDef"
    assert pairs[0].net_improvement > 0
    assert pairs[0].priority in {"essential", "strong", "optional"}
    assert pairs[0].reasons


def test_build_transfer_pairs_respects_three_player_team_limit() -> None:
    squad = [
        make_analysis(1, "WeakDef", 2, 5, expected_points=2.0, overall_risk=0.6),
        make_analysis(2, "T9A", 3, 9, expected_points=5.0),
        make_analysis(3, "T9B", 3, 9, expected_points=5.0),
        make_analysis(4, "T9C", 3, 9, expected_points=5.0),
    ]
    pool = [
        make_analysis(
            10, "PoolDefT9", 2, 9, expected_points=8.0, overall_risk=0.1,
        ),
        make_analysis(
            11, "PoolDefT3", 2, 3, expected_points=7.5, overall_risk=0.1,
        ),
    ]

    sell_candidates = rank_sell_candidates(squad)
    pairs = build_transfer_pairs(
        sell_candidates=sell_candidates,
        pool_analyses=pool,
        squad_analyses=squad,
    )

    assert len(pairs) == 1
    assert pairs[0].buy.web_name == "PoolDefT3"


def test_build_transfer_pairs_does_not_reuse_buy_candidate() -> None:
    squad = [
        make_analysis(1, "WeakA", 2, 1, expected_points=2.0, overall_risk=0.6),
        make_analysis(2, "WeakB", 2, 2, expected_points=2.5, overall_risk=0.5),
    ]
    pool = [
        make_analysis(10, "Buy1", 2, 5, expected_points=8.0, overall_risk=0.1),
        make_analysis(11, "Buy2", 2, 6, expected_points=7.0, overall_risk=0.1),
    ]

    sell_candidates = rank_sell_candidates(squad)
    pairs = build_transfer_pairs(
        sell_candidates=sell_candidates,
        pool_analyses=pool,
        squad_analyses=squad,
    )

    assert len(pairs) == 2
    buy_ids = {pair.buy.player_id for pair in pairs}
    assert buy_ids == {10, 11}


def test_build_transfer_pairs_filters_out_tiny_improvements() -> None:
    squad = [
        make_analysis(1, "Sell", 2, 1, expected_points=5.0, overall_risk=0.2),
    ]
    pool = [
        make_analysis(10, "Buy", 2, 5, expected_points=5.1, overall_risk=0.2),
    ]

    sell_candidates = rank_sell_candidates(squad)
    pairs = build_transfer_pairs(
        sell_candidates=sell_candidates,
        pool_analyses=pool,
        squad_analyses=squad,
    )

    assert pairs == []


def test_build_transfer_pairs_respects_max_pairs() -> None:
    squad = [
        make_analysis(1, "Sell1", 1, 1, expected_points=1.0, overall_risk=0.6),
        make_analysis(2, "Sell2", 2, 2, expected_points=1.0, overall_risk=0.6),
        make_analysis(3, "Sell3", 3, 3, expected_points=1.0, overall_risk=0.6),
    ]
    pool = [
        make_analysis(10, "Buy1", 1, 5, expected_points=8.0, overall_risk=0.1),
        make_analysis(11, "Buy2", 2, 6, expected_points=8.0, overall_risk=0.1),
        make_analysis(12, "Buy3", 3, 7, expected_points=8.0, overall_risk=0.1),
    ]

    sell_candidates = rank_sell_candidates(squad)
    pairs = build_transfer_pairs(
        sell_candidates=sell_candidates,
        pool_analyses=pool,
        squad_analyses=squad,
        max_pairs=1,
    )

    assert len(pairs) == 1


def test_build_transfer_pairs_within_budget_reflects_entry_bank() -> None:
    squad = [
        make_analysis(
            1, "Sell", 2, 1, expected_points=3.0, overall_risk=0.2, price=5.0,
        ),
    ]
    pool = [
        make_analysis(
            10, "Buy", 2, 5, expected_points=6.0, overall_risk=0.2, price=6.0,
        ),
    ]
    sell_candidates = rank_sell_candidates(squad)

    affordable = build_transfer_pairs(
        sell_candidates=sell_candidates,
        pool_analyses=pool,
        squad_analyses=squad,
        entry_bank=1.0,
    )
    assert affordable[0].within_budget is True

    unaffordable = build_transfer_pairs(
        sell_candidates=sell_candidates,
        pool_analyses=pool,
        squad_analyses=squad,
        entry_bank=0.5,
    )
    assert unaffordable[0].within_budget is False

    unknown_budget = build_transfer_pairs(
        sell_candidates=sell_candidates,
        pool_analyses=pool,
        squad_analyses=squad,
        entry_bank=None,
    )
    assert unknown_budget[0].within_budget is None


# --- extract_bank_balance --------------------------------------------------


def test_extract_bank_balance_converts_tenths_of_million() -> None:
    assert extract_bank_balance({"bank": 15}) == 1.5


def test_extract_bank_balance_handles_missing_or_invalid_data() -> None:
    assert extract_bank_balance(None) is None
    assert extract_bank_balance({}) is None
    assert extract_bank_balance({"bank": "unknown"}) is None
    assert extract_bank_balance({"bank": True}) is None


# --- build_available_pool_analyses -----------------------------------------


def _make_pool_test_player(
    player_id: int,
    element_type: int,
    team_id: int,
    minutes: int = 900,
    total_points: int = 50,
    status: str = "a",
    can_select: bool = True,
) -> Player:
    return Player(
        id=player_id,
        first_name="Test",
        second_name=f"Player {player_id}",
        web_name=f"P{player_id}",
        team=team_id,
        element_type=element_type,
        status=status,
        can_select=can_select,
        now_cost=50,
        total_points=total_points,
        minutes=minutes,
        goals_scored=5,
        assists=5,
        clean_sheets=5,
        goals_conceded=10,
        own_goals=0,
        penalties_saved=0,
        penalties_missed=0,
        yellow_cards=0,
        red_cards=0,
        saves=0,
        bonus=5,
        form="5.0",
        points_per_game="5.0",
        selected_by_percent="10.0",
        transfers_in=100,
        transfers_out=50,
        expected_goals="5.0",
        expected_assists="5.0",
        expected_goal_involvements="10.0",
        expected_goals_conceded="10.0",
        influence="50.0",
        creativity="50.0",
        threat="50.0",
        ict_index="50.0",
    )


def _make_pool_test_teams() -> list[Team]:
    return [
        Team(
            id=team_id,
            name=f"Team {team_id}",
            short_name=f"T{team_id}",
            code=team_id,
            strength=3,
            strength_overall_home=3,
            strength_overall_away=3,
            strength_attack_home=3,
            strength_attack_away=3,
            strength_defence_home=3,
            strength_defence_away=3,
            played=1,
            win=1,
            draw=0,
            loss=0,
            points=3,
        )
        for team_id in range(1, 6)
    ]


def _make_pool_test_fixtures() -> list[Fixture]:
    return [
        Fixture(
            id=team_id,
            event=1,
            team_h=team_id,
            team_a=team_id,
            finished=False,
            team_h_difficulty=2,
            team_a_difficulty=2,
        )
        for team_id in range(1, 6)
    ]


def test_build_available_pool_analyses_excludes_squad_unavailable_and_idle() -> (
    None
):
    squad_player = _make_pool_test_player(1, 2, 1)
    unavailable_player = _make_pool_test_player(2, 2, 2, status="i")
    idle_player = _make_pool_test_player(3, 2, 3, minutes=0)
    valid_pool_player = _make_pool_test_player(4, 2, 4)

    players = [squad_player, unavailable_player, idle_player, valid_pool_player]

    result = build_available_pool_analyses(
        players=players,
        teams=_make_pool_test_teams(),
        fixtures=_make_pool_test_fixtures(),
        exclude_player_ids={1},
    )

    assert [analysis.player_id for analysis in result] == [4]
    assert result[0].position_type == 2
    assert isinstance(result[0].selection_score, float)


def test_build_available_pool_analyses_excludes_tiny_minute_samples() -> None:
    """A one-minute cameo with a bonus point must not distort per-90 stats.

    total_points/minutes*90 has no floor, so 2 points in 1 minute would
    otherwise extrapolate to 180 points per 90 - a nonsensical buy
    candidate. Requiring at least one full match's worth of minutes
    screens this out.
    """
    cameo_player = _make_pool_test_player(
        5, 2, 5, minutes=1, total_points=2,
    )
    full_match_player = _make_pool_test_player(
        6, 2, 6, minutes=90, total_points=8,
    )

    result = build_available_pool_analyses(
        players=[cameo_player, full_match_player],
        teams=_make_pool_test_teams(),
        fixtures=_make_pool_test_fixtures(),
        exclude_player_ids=set(),
    )

    assert [analysis.player_id for analysis in result] == [6]
    assert result[0].selection_score < 20.0
