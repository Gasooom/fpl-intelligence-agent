from __future__ import annotations

from fpl_agent.data.models import Fixture, Player, Team
from fpl_agent.decisions.gameweek_decision import (
    DATA_SOURCE,
    DECISION_ENGINE_VERSION,
    GameweekDecision,
    RecommendationEvidence,
    build_gameweek_decision,
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

    assert decision.confidence in {"High", "Medium", "Low"}
    assert "Captain" in decision.decision_summary
    assert "Decision confidence" in decision.decision_summary

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
    assert "No worthwhile transfers" in decision.decision_summary
