from __future__ import annotations

from fpl_agent.analysis.confidence import LIMITED_SAMPLE_MINUTES
from fpl_agent.analysis.sell_scoring import SellScore
from fpl_agent.data.models import Fixture, Player, Team
from fpl_agent.decisions.gameweek_decision import (
    DATA_SOURCE,
    DECISION_ENGINE_VERSION,
    GameweekDecision,
    RecommendationEvidence,
    _aggregate_confidence,
    build_evidence_basis,
    build_gameweek_decision,
    select_best_transfer,
)
from fpl_agent.decisions.squad_analysis import SquadPlayerAnalysis
from fpl_agent.decisions.transfer_analysis import (
    BuyCandidate,
    SellCandidate,
    TransferPair,
)


def _squad_player_analysis(
    player_id: int,
    sample_confidence: float,
    overall_risk: float = 0.2,
) -> SquadPlayerAnalysis:
    """A minimal SquadPlayerAnalysis for exercising _aggregate_confidence
    directly, without building a full gameweek decision."""
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
        expected_points=5.0,
        minutes_risk=0.0,
        form_uncertainty=0.0,
        fixture_risk=0.0,
        availability_risk=0.0,
        overall_risk=overall_risk,
        risk_level="low",
        sample_confidence=sample_confidence,
        captaincy_score=5.0,
        selection_score=5.0,
    )


def _player(
    player_id: int,
    element_type: int,
    team_id: int,
    form: str = "5.0",
    points_per_game: str = "5.0",
    total_points: int = 50,
    minutes: int = 900,
    now_cost: int = 50,
    expected_goals: str = "5.0",
    expected_assists: str = "5.0",
    status: str = "a",
    can_select: bool = True,
) -> Player:
    return Player(
        id=player_id,
        first_name="Test",
        second_name=f"Player {player_id}",
        web_name=f"Player{player_id}",
        team=team_id,
        element_type=element_type,
        status=status,
        can_select=can_select,
        now_cost=now_cost,
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
        form=form,
        points_per_game=points_per_game,
        selected_by_percent="10.0",
        transfers_in=100,
        transfers_out=50,
        expected_goals=expected_goals,
        expected_assists=expected_assists,
        expected_goal_involvements="10.0",
        expected_goals_conceded="10.0",
        influence="50.0",
        creativity="50.0",
        threat="50.0",
        ict_index="50.0",
    )


def _teams() -> list[Team]:
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
        for team_id in range(1, 26)
    ]


def _fixtures() -> list[Fixture]:
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
        for team_id in range(1, 26)
    ]


def _squad_players() -> list[Player]:
    return [
        _player(1, 1, 1),
        _player(
            2,
            2,
            2,
            form="1.0",
            points_per_game="1.0",
            total_points=5,
            expected_goals="0.0",
            expected_assists="0.0",
        ),
        _player(3, 2, 3),
        _player(4, 2, 4),
        _player(5, 2, 5),
        _player(6, 3, 6),
        _player(7, 3, 7),
        _player(8, 3, 8),
        _player(9, 3, 9),
        _player(10, 3, 10),
        _player(11, 4, 11),
        _player(12, 4, 12),
        _player(13, 3, 13),
        _player(14, 2, 14),
        _player(15, 3, 15),
    ]


def _pool_players() -> list[Player]:
    return [
        _player(
            101,
            2,
            20,
            form="9.0",
            points_per_game="9.0",
            total_points=150,
            expected_goals="10.0",
            expected_assists="8.0",
        ),
        _player(102, 3, 21, form="7.0", points_per_game="7.0"),
        _player(103, 4, 22, form="7.0", points_per_game="7.0"),
    ]


def test_build_gameweek_decision_returns_full_structure() -> None:
    players = [*_squad_players(), *_pool_players()]

    decision = build_gameweek_decision(
        players=players,
        teams=_teams(),
        fixtures=_fixtures(),
        picks=list(range(1, 16)),
        gameweek=5,
    )

    assert isinstance(decision, GameweekDecision)
    assert decision.gameweek == 5
    assert decision.decision_engine_version == DECISION_ENGINE_VERSION
    assert decision.data_source == DATA_SOURCE
    assert decision.generated_at

    assert len(decision.starting_xi) == 11
    assert len(decision.bench) == 4
    assert decision.captain.player_id != decision.vice_captain.player_id

    assert len(decision.sell_candidates) == 15
    assert decision.sell_candidates[0].player_id == 2

    squad_ids = {
        player.player_id
        for player in [*decision.starting_xi, *decision.bench]
    }
    assert decision.buy_candidates
    assert all(
        candidate.player_id not in squad_ids
        for candidate in decision.buy_candidates
    )

    assert decision.transfer_recommendations
    assert decision.transfer_count == len(decision.transfer_recommendations)

    top_pair = decision.transfer_recommendations[0]
    assert top_pair.sell.player_id == 2
    assert top_pair.buy.player_id == 101
    assert top_pair.priority in {"essential", "strong", "optional"}

    assert decision.best_transfer is not None
    assert decision.best_transfer in decision.transfer_recommendations
    assert "Best single transfer" in decision.decision_summary

    assert decision.confidence in {"High", "Medium", "Low"}
    assert "Captain" in decision.decision_summary
    # The confidence label travels as a structured field, never as
    # prose in the summary - restating it there duplicated vocabulary
    # the presentation layer owns and let the two drift apart.
    assert "confidence" not in decision.decision_summary.lower()

    assert decision.evidence
    assert all(
        isinstance(item, RecommendationEvidence) for item in decision.evidence
    )
    decisions_present = {item.decision for item in decision.evidence}
    assert "captain" in decisions_present
    assert "vice_captain" in decisions_present
    assert "sell" in decisions_present
    assert "buy" in decisions_present


def test_build_gameweek_decision_is_deterministic_apart_from_timestamp() -> None:
    players = [*_squad_players(), *_pool_players()]
    teams = _teams()
    fixtures = _fixtures()
    picks = list(range(1, 16))

    first = build_gameweek_decision(
        players=players,
        teams=teams,
        fixtures=fixtures,
        picks=picks,
        gameweek=5,
    )
    second = build_gameweek_decision(
        players=players,
        teams=teams,
        fixtures=fixtures,
        picks=picks,
        gameweek=5,
    )

    assert [p.player_id for p in first.starting_xi] == [
        p.player_id for p in second.starting_xi
    ]
    assert first.captain.player_id == second.captain.player_id
    assert [c.player_id for c in first.sell_candidates] == [
        c.player_id for c in second.sell_candidates
    ]
    assert first.decision_summary == second.decision_summary
    assert first.confidence == second.confidence


def test_build_gameweek_decision_handles_no_worthwhile_transfers() -> None:
    players = _squad_players()

    decision = build_gameweek_decision(
        players=players,
        teams=_teams(),
        fixtures=_fixtures(),
        picks=list(range(1, 16)),
        gameweek=1,
    )

    assert decision.transfer_recommendations == []
    assert decision.transfer_count == 0
    assert decision.buy_candidates == []
    assert decision.best_transfer is None
    assert "No worthwhile transfers" in decision.decision_summary
    assert "Best single transfer" not in decision.decision_summary


# --- select_best_transfer ---------------------------------------------------


def _make_pair(
    pair_id: int,
    priority: str,
    net_improvement: float,
) -> TransferPair:
    sell = SellCandidate(
        player_id=pair_id * 10,
        web_name=f"Sell{pair_id}",
        position_type=2,
        team_id=1,
        price=5.0,
        expected_points=2.0,
        form=3.0,
        fixture_difficulty=3.0,
        overall_risk=0.3,
        availability_risk=0.0,
        risk_level="medium",
        sample_confidence=0.5,
        selection_score=1.0,
        sell_score=SellScore(
            player_id=pair_id * 10,
            score=3.0,
            risk_penalty=1.0,
            low_projection_penalty=1.0,
            difficult_fixture_penalty=0.0,
            availability_penalty=0.0,
            low_confidence_penalty=1.0,
        ),
        rank=pair_id,
        reasons=["Weak projected output"],
    )

    buy = BuyCandidate(
        player_id=pair_id * 10 + 1,
        web_name=f"Buy{pair_id}",
        position_type=2,
        team_id=2,
        price=5.5,
        expected_points=6.0,
        form=6.0,
        fixture_difficulty=2.0,
        overall_risk=0.1,
        availability_risk=0.0,
        risk_level="low",
        sample_confidence=1.0,
        selection_score=1.0 + net_improvement,
        value_score=0.1,
        rank=pair_id,
        reasons=["Higher expected points"],
    )

    return TransferPair(
        sell=sell,
        buy=buy,
        net_improvement=net_improvement,
        risk_change=0.2,
        price_change=0.5,
        within_budget=True,
        priority=priority,
        reasons=["Higher expected points"],
        expected_point_gain=buy.expected_points - sell.expected_points,
        hit_cost=None,
        net_value=None,
    )


def test_select_best_transfer_prefers_higher_priority_tier() -> None:
    optional_big_gain = _make_pair(1, "optional", net_improvement=5.0)
    strong_small_gain = _make_pair(2, "strong", net_improvement=1.1)

    best = select_best_transfer([optional_big_gain, strong_small_gain])

    assert best is strong_small_gain


def test_select_best_transfer_breaks_ties_within_tier_by_net_improvement() -> (
    None
):
    strong_a = _make_pair(1, "strong", net_improvement=1.2)
    strong_b = _make_pair(2, "strong", net_improvement=1.8)

    best = select_best_transfer([strong_a, strong_b])

    assert best is strong_b


def test_select_best_transfer_returns_none_for_empty_list() -> None:
    assert select_best_transfer([]) is None


def test_build_gameweek_decision_every_evidence_item_has_nonempty_reasons() -> None:
    """Regression guard for the full evidence pipeline: captain,
    vice-captain, sell, and buy evidence entries must each carry at
    least one reason, exactly as the deterministic reason-builders in
    transfer_analysis.py guarantee. This is what backs the "Decision
    evidence", "Why X -> Y", and "Backend reasoning" sections of the
    frontend - an empty reasons list here would surface as an empty
    bullet list there."""
    players = [*_squad_players(), *_pool_players()]

    decision = build_gameweek_decision(
        players=players,
        teams=_teams(),
        fixtures=_fixtures(),
        picks=list(range(1, 16)),
        gameweek=5,
    )

    assert decision.evidence
    empty_items = [item for item in decision.evidence if not item.reasons]
    assert empty_items == []


def test_narrative_and_best_transfer_field_report_the_same_expected_gain() -> None:
    """Regression guard: decision_summary's "Best single transfer" line
    and best_transfer.expected_point_gain (the same field the API
    response and frontend card read) must always agree - they
    previously came from two different formulas (net_improvement, a
    selection-score delta, vs expected_point_gain, a pure points
    delta) and could show two different numbers for the same pair."""
    players = [*_squad_players(), *_pool_players()]

    decision = build_gameweek_decision(
        players=players,
        teams=_teams(),
        fixtures=_fixtures(),
        picks=list(range(1, 16)),
        gameweek=5,
    )

    assert decision.best_transfer is not None
    gain = decision.best_transfer.expected_point_gain
    signed_gain = f"+{gain}" if gain >= 0 else str(gain)
    expected_fragment = f"({signed_gain} expected points, {decision.best_transfer.priority})"

    assert expected_fragment in decision.decision_summary
    # And the narrative must not be quoting the other formula instead.
    if decision.best_transfer.net_improvement != gain:
        assert f"+{decision.best_transfer.net_improvement} expected points" not in (
            decision.decision_summary
        )


# --- Starting XI expected-points total / projected Gameweek total ---


def test_starting_xi_expected_points_is_the_sum_of_exactly_the_11_starters() -> None:
    """H: bench players are never included in the subtotal."""
    players = [*_squad_players(), *_pool_players()]

    decision = build_gameweek_decision(
        players=players,
        teams=_teams(),
        fixtures=_fixtures(),
        picks=list(range(1, 16)),
        gameweek=5,
    )

    assert len(decision.starting_xi) == 11
    expected = round(sum(p.expected_points for p in decision.starting_xi), 2)
    assert decision.starting_xi_expected_points == expected

    # Adding a bench player's expected_points must never change the total.
    inflated = expected + sum(p.expected_points for p in decision.bench)
    assert decision.starting_xi_expected_points != round(inflated, 2) or not decision.bench


def test_projected_gameweek_points_adds_exactly_one_extra_captain_copy() -> None:
    """G + I: the captain is doubled (counted once inside the XI
    subtotal, once again as the bonus) - never tripled, never left
    single."""
    players = [*_squad_players(), *_pool_players()]

    decision = build_gameweek_decision(
        players=players,
        teams=_teams(),
        fixtures=_fixtures(),
        picks=list(range(1, 16)),
        gameweek=5,
    )

    expected_total = round(
        decision.starting_xi_expected_points + decision.captain.expected_points,
        2,
    )
    assert decision.projected_gameweek_points == expected_total

    # Exactly one extra copy: total minus the raw XI subtotal must equal
    # precisely one captain expected_points, not two, not zero.
    extra = round(decision.projected_gameweek_points - decision.starting_xi_expected_points, 2)
    assert extra == decision.captain.expected_points


def test_projected_gameweek_points_matches_the_worked_example() -> None:
    """The exact figures from the spec: XI 47.70, captain 7.17,
    projected total 54.87."""
    starting_xi_expected = round(
        4.00 + 4.80 + 4.04 + 3.03 + 1.92 + 6.19 + 4.34 + 4.28 + 2.98 + 7.17 + 4.95,
        2,
    )
    assert starting_xi_expected == 47.70
    assert round(starting_xi_expected + 7.17, 2) == 54.87


def test_starting_xi_expected_points_only_counts_the_captain_once_at_1x() -> None:
    """I: within the raw XI subtotal itself (before the captain bonus
    is added), the captain contributes exactly his own expected_points
    - the same as every other starter, not doubled at this stage."""
    players = [*_squad_players(), *_pool_players()]

    decision = build_gameweek_decision(
        players=players,
        teams=_teams(),
        fixtures=_fixtures(),
        picks=list(range(1, 16)),
        gameweek=5,
    )

    without_captain = round(
        decision.starting_xi_expected_points - decision.captain.expected_points,
        2,
    )
    rest_of_xi = round(
        sum(
            p.expected_points
            for p in decision.starting_xi
            if p.player_id != decision.captain.player_id
        ),
        2,
    )
    assert without_captain == rest_of_xi


# --- Decision confidence: strength of evidence only, never risk ---


def test_aggregate_confidence_is_low_when_sample_evidence_is_genuinely_thin() -> None:
    """Early-season case: every starter has the minimum minutes-based
    sample_confidence bucket (0.25, e.g. gameweek 3). Confidence must be
    Low, and this must hold true even when risk is uniformly LOW - proving
    the Low label reflects thin evidence, not risk."""
    starting_xi = [
        _squad_player_analysis(player_id=i, sample_confidence=0.25, overall_risk=0.05)
        for i in range(11)
    ]

    assert _aggregate_confidence(starting_xi) == "Low"


def test_aggregate_confidence_is_medium_with_adequate_sample_evidence() -> None:
    starting_xi = [
        _squad_player_analysis(player_id=i, sample_confidence=0.5)
        for i in range(11)
    ]

    assert _aggregate_confidence(starting_xi) == "Medium"


def test_aggregate_confidence_is_high_with_strong_sample_evidence() -> None:
    starting_xi = [
        _squad_player_analysis(player_id=i, sample_confidence=0.75)
        for i in range(11)
    ]

    assert _aggregate_confidence(starting_xi) == "High"


def test_aggregate_confidence_is_not_downgraded_by_high_risk() -> None:
    """Regression test: confidence measures evidence strength only, per
    the Projection / Risk / Confidence / Decision separation - risk must
    never disguise itself as low confidence. A starting XI with strong
    sample evidence but high risk (e.g. rotation/fixture doubt) must still
    report High confidence; risk stays visible separately via each
    player's own overall_risk/risk_level."""
    starting_xi = [
        _squad_player_analysis(player_id=i, sample_confidence=1.0, overall_risk=0.95)
        for i in range(11)
    ]

    assert _aggregate_confidence(starting_xi) == "High"


def test_aggregate_confidence_boundary_values() -> None:
    just_below_medium = [
        _squad_player_analysis(player_id=i, sample_confidence=0.49)
        for i in range(11)
    ]
    just_below_high = [
        _squad_player_analysis(player_id=i, sample_confidence=0.74)
        for i in range(11)
    ]

    assert _aggregate_confidence(just_below_medium) == "Low"
    assert _aggregate_confidence(just_below_high) == "Medium"


def test_aggregate_confidence_is_low_for_an_empty_starting_xi() -> None:
    assert _aggregate_confidence([]) == "Low"


# --- Evidence basis: the figures behind the confidence label ---
#
# These exist so the label can be explained truthfully downstream. The
# contract they protect is that the basis *is* the calculation, not a
# parallel description of it that could drift away from the label.


def test_evidence_basis_level_always_matches_the_confidence_label() -> None:
    """The basis explains the label, so it must never disagree with it."""
    for sample_confidence in (0.0, 0.25, 0.49, 0.5, 0.74, 0.75, 1.0):
        starting_xi = [
            _squad_player_analysis(player_id=i, sample_confidence=sample_confidence)
            for i in range(11)
        ]

        basis = build_evidence_basis(starting_xi)

        assert basis.level == _aggregate_confidence(starting_xi)


def test_evidence_basis_reports_the_average_it_actually_compared() -> None:
    starting_xi = [
        _squad_player_analysis(player_id=0, sample_confidence=0.25),
        _squad_player_analysis(player_id=1, sample_confidence=0.75),
    ]

    basis = build_evidence_basis(starting_xi)

    assert basis.average_sample_confidence == 0.5
    assert basis.level == "Medium"


def test_evidence_basis_band_counts_partition_the_starting_xi() -> None:
    """Every starter lands in exactly one band, so the three counts add
    up to players_considered - a UI can quote them as "N of M" safely."""
    starting_xi = [
        _squad_player_analysis(player_id=0, sample_confidence=0.0),
        _squad_player_analysis(player_id=1, sample_confidence=0.25),
        _squad_player_analysis(player_id=2, sample_confidence=0.5),
        _squad_player_analysis(player_id=3, sample_confidence=0.75),
        _squad_player_analysis(player_id=4, sample_confidence=1.0),
    ]

    basis = build_evidence_basis(starting_xi)

    assert basis.players_considered == 5
    assert basis.limited_sample_players == 2
    assert basis.partial_sample_players == 1
    assert basis.full_sample_players == 2
    assert (
        basis.limited_sample_players
        + basis.partial_sample_players
        + basis.full_sample_players
        == basis.players_considered
    )


def test_evidence_basis_exposes_the_thresholds_that_decided_the_label() -> None:
    starting_xi = [
        _squad_player_analysis(player_id=i, sample_confidence=0.25)
        for i in range(11)
    ]

    basis = build_evidence_basis(starting_xi)

    assert basis.medium_threshold == 0.5
    assert basis.high_threshold == 0.75
    assert basis.average_sample_confidence < basis.medium_threshold
    assert basis.limited_sample_minutes == LIMITED_SAMPLE_MINUTES


def test_evidence_basis_is_not_affected_by_risk() -> None:
    """Same separation the confidence label itself enforces: the basis
    describes evidence only, so high risk must not change any figure."""
    low_risk = [
        _squad_player_analysis(player_id=i, sample_confidence=1.0, overall_risk=0.05)
        for i in range(11)
    ]
    high_risk = [
        _squad_player_analysis(player_id=i, sample_confidence=1.0, overall_risk=0.95)
        for i in range(11)
    ]

    assert build_evidence_basis(low_risk) == build_evidence_basis(high_risk)


def test_evidence_basis_for_an_empty_starting_xi_reports_no_evidence() -> None:
    """Conservative Low with genuinely zero counts - never a fabricated
    average that would imply evidence exists."""
    basis = build_evidence_basis([])

    assert basis.level == "Low"
    assert basis.average_sample_confidence == 0.0
    assert basis.players_considered == 0
    assert basis.limited_sample_players == 0
    assert basis.partial_sample_players == 0
    assert basis.full_sample_players == 0


def test_built_decision_carries_a_basis_consistent_with_its_confidence() -> None:
    """End-to-end: the decision the engine actually produces exposes a
    basis describing that decision's own starting XI, and its level is
    the confidence label the decision reports."""
    players = [*_squad_players(), *_pool_players()]

    decision = build_gameweek_decision(
        players=players,
        teams=_teams(),
        fixtures=_fixtures(),
        picks=list(range(1, 16)),
        gameweek=5,
    )

    basis = decision.evidence_basis

    assert basis.level == decision.confidence
    assert basis.players_considered == len(decision.starting_xi)
    assert basis == build_evidence_basis(decision.starting_xi)


def test_decision_summary_carries_no_confidence_terminology() -> None:
    """Regression guard for user-facing wording.

    The dashboard presents evidence strength in its own vocabulary
    ("Evidence: Limited"). A summary that also said "Decision
    confidence: Low." put stale, contradictory wording on screen, so
    the summary must stay free of that terminology entirely.
    """
    players = [*_squad_players(), *_pool_players()]

    decision = build_gameweek_decision(
        players=players,
        teams=_teams(),
        fixtures=_fixtures(),
        picks=list(range(1, 16)),
        gameweek=5,
    )

    summary = decision.decision_summary.lower()

    assert "confidence" not in summary
    assert "decision confidence" not in summary
    for label in ("low", "medium", "high"):
        assert f"confidence: {label}" not in summary

    # The summary still carries its real content.
    assert "Captain:" in decision.decision_summary
    assert decision.confidence in {"High", "Medium", "Low"}
