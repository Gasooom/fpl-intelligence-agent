from __future__ import annotations

import pytest

from fpl_agent.data.models import Fixture, Player, Team
from fpl_agent.decisions.squad_analysis import (
    SquadPlayerAnalysis,
    build_squad_decision,
    select_bench,
    select_captains,
    select_must_play,
)


def make_analysis_player(
    player_id: int,
    web_name: str,
    element_type: int,
    expected_points: float,
    form: float,
    overall_risk: float,
    availability_risk: float,
    captaincy_score: float,
    sample_confidence: float = 1.0,
) -> SquadPlayerAnalysis:
    return SquadPlayerAnalysis(
        player_id=player_id,
        web_name=web_name,
        position_type=element_type,
        team_id=player_id,
        price=10.0,
        form=form,
        points_per_game=5.0,
        points_per_90=6.0,
        xgi_per_90=0.5,
        fixture_difficulty=2.0,
        expected_points=expected_points,
        minutes_risk=0.0,
        form_uncertainty=0.0,
        fixture_risk=0.0,
        availability_risk=availability_risk,
        overall_risk=overall_risk,
        risk_level="low",
        sample_confidence=sample_confidence,
        captaincy_score=captaincy_score,
        selection_score=(
            expected_points
            + form * 0.15
            + (sample_confidence - 0.5) * 0.5
            - overall_risk * 2.0
        ),
    )


def test_select_captains_returns_highest_two_captaincy_scores() -> None:
    players = [
        make_analysis_player(
            1,
            "A",
            3,
            7.0,
            6.0,
            0.2,
            0.0,
            8.0,
        ),
        make_analysis_player(
            2,
            "B",
            3,
            6.0,
            5.0,
            0.2,
            0.0,
            7.0,
        ),
        make_analysis_player(
            3,
            "C",
            3,
            5.0,
            4.0,
            0.2,
            0.0,
            5.0,
        ),
    ]

    captain, vice = select_captains(players)

    assert captain.web_name == "A"
    assert vice.web_name == "B"


def test_select_captains_uses_expected_points_as_tiebreaker() -> None:
    players = [
        make_analysis_player(
            1,
            "A",
            3,
            8.0,
            4.0,
            0.2,
            0.0,
            7.0,
        ),
        make_analysis_player(
            2,
            "B",
            3,
            7.0,
            4.0,
            0.2,
            0.0,
            7.0,
        ),
        make_analysis_player(
            3,
            "C",
            3,
            6.0,
            4.0,
            0.2,
            0.0,
            5.0,
        ),
    ]

    captain, vice = select_captains(players)

    assert captain.web_name == "A"
    assert vice.web_name == "B"


def test_select_must_play_returns_low_risk_available_players() -> None:
    players = [
        make_analysis_player(
            1,
            "Safe",
            3,
            7.0,
            6.0,
            0.2,
            0.0,
            7.0,
        ),
        make_analysis_player(
            2,
            "Risky",
            3,
            8.0,
            6.0,
            0.5,
            0.0,
            8.0,
        ),
    ]

    result = select_must_play(players)

    assert [player.web_name for player in result] == ["Safe"]


def test_select_must_play_excludes_availability_risk() -> None:
    players = [
        make_analysis_player(
            1,
            "Available",
            3,
            7.0,
            6.0,
            0.2,
            0.0,
            7.0,
        ),
        make_analysis_player(
            2,
            "Doubtful",
            3,
            9.0,
            7.0,
            0.2,
            0.5,
            9.0,
        ),
    ]

    result = select_must_play(players)

    assert [player.web_name for player in result] == ["Available"]


def test_select_must_play_currently_excludes_exact_point_four_risk() -> None:
    players = [
        make_analysis_player(
            1,
            "Borderline",
            3,
            8.0,
            6.0,
            0.4,
            0.0,
            8.0,
        ),
    ]

    result = select_must_play(players)

    assert result == []


def test_select_must_play_requires_sufficient_sample_confidence() -> None:
    players = [
        make_analysis_player(
            1,
            "HighConfidence",
            3,
            7.0,
            6.0,
            0.2,
            0.0,
            7.0,
            sample_confidence=1.0,
        ),
        make_analysis_player(
            2,
            "LowConfidence",
            3,
            8.0,
            7.0,
            0.2,
            0.0,
            8.0,
            sample_confidence=0.25,
        ),
    ]

    result = select_must_play(players)

    assert [player.web_name for player in result] == [
        "HighConfidence",
    ]


def test_selection_score_rewards_confidence_but_stays_bounded() -> None:
    low_confidence = make_analysis_player(
        1,
        "Low",
        3,
        7.0,
        5.0,
        0.2,
        0.0,
        7.0,
        sample_confidence=0.0,
    )

    high_confidence = make_analysis_player(
        2,
        "High",
        3,
        7.0,
        5.0,
        0.2,
        0.0,
        7.0,
        sample_confidence=1.0,
    )

    assert (
        high_confidence.selection_score
        - low_confidence.selection_score
        == 0.5
    )


def test_selection_score_has_zero_confidence_bonus_at_half() -> None:
    player = make_analysis_player(
        1,
        "Neutral",
        3,
        7.0,
        5.0,
        0.2,
        0.0,
        7.0,
        sample_confidence=0.5,
    )

    expected = round(
        7.0
        + 5.0 * 0.15
        - 0.2 * 2.0,
        2,
    )

    assert player.selection_score == expected


def test_select_bench_prioritizes_goalkeeper_and_top_outfield_players() -> None:
    starting = [
        make_analysis_player(
            1,
            "Starter GK",
            1,
            6.0,
            5.0,
            0.2,
            0.0,
            6.0,
        ),
        make_analysis_player(
            2,
            "Starter DEF",
            2,
            6.0,
            5.0,
            0.2,
            0.0,
            6.0,
        ),
    ]

    analyses = [
        *starting,
        make_analysis_player(
            3,
            "Bench GK",
            1,
            5.0,
            5.0,
            0.2,
            0.0,
            5.0,
        ),
        make_analysis_player(
            4,
            "Bench DEF",
            2,
            5.0,
            5.0,
            0.2,
            0.0,
            5.0,
        ),
        make_analysis_player(
            5,
            "Bench MID",
            3,
            4.0,
            5.0,
            0.2,
            0.0,
            4.0,
        ),
        make_analysis_player(
            6,
            "Bench FWD",
            4,
            3.0,
            5.0,
            0.2,
            0.0,
            3.0,
        ),
        make_analysis_player(
            7,
            "Extra",
            3,
            2.0,
            5.0,
            0.2,
            0.0,
            2.0,
        ),
    ]

    bench = select_bench(
        analyses=analyses,
        starting_xi=starting,
    )

    assert [player.web_name for player in bench] == [
        "Bench GK",
        "Bench DEF",
        "Bench MID",
        "Bench FWD",
    ]


def test_select_bench_returns_fewer_than_four_when_not_enough_players_exist() -> None:
    starting = [
        make_analysis_player(
            1,
            "Starter",
            3,
            7.0,
            5.0,
            0.2,
            0.0,
            7.0,
        ),
    ]

    analyses = [
        *starting,
        make_analysis_player(
            2,
            "Bench",
            3,
            5.0,
            5.0,
            0.2,
            0.0,
            5.0,
        ),
    ]

    bench = select_bench(
        analyses=analyses,
        starting_xi=starting,
    )

    assert [player.web_name for player in bench] == ["Bench"]


def _make_test_player(
    player_id: int,
    element_type: int,
    team_id: int,
    status: str = "a",
    can_select: bool = True,
    chance_of_playing_next_round: int | None = None,
) -> Player:
    return Player(
        id=player_id,
        first_name="Test",
        second_name=f"Player {player_id}",
        web_name=f"P{player_id}",
        team=team_id,
        element_type=element_type,
        status=status,
        chance_of_playing_next_round=chance_of_playing_next_round,
        now_cost=50,
        total_points=50,
        minutes=900,
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


def _make_test_teams() -> list[Team]:
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
        for team_id in range(1, 16)
    ]


def _make_test_fixtures() -> list[Fixture]:
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
        for team_id in range(1, 16)
    ]


def test_build_squad_decision_uses_only_supplied_fpl_picks() -> None:
    players = [
        _make_test_player(1, 1, 1),
        _make_test_player(2, 2, 2),
        _make_test_player(3, 2, 3),
        _make_test_player(4, 2, 4),
        _make_test_player(5, 2, 5),
        _make_test_player(6, 3, 6),
        _make_test_player(7, 3, 7),
        _make_test_player(8, 3, 8),
        _make_test_player(9, 3, 9),
        _make_test_player(10, 3, 10),
        _make_test_player(11, 4, 11),
        _make_test_player(12, 4, 12),
        _make_test_player(13, 3, 13),
        _make_test_player(14, 2, 14),
        _make_test_player(15, 3, 15),
    ]

    result = build_squad_decision(
        players=players,
        teams=_make_test_teams(),
        fixtures=_make_test_fixtures(),
        picks=list(range(1, 16)),
    )

    result_ids = {
        player.player_id
        for player in [
            *result.starting_xi,
            *result.bench,
        ]
    }

    assert result_ids == set(range(1, 16))


def test_build_squad_decision_excludes_unavailable_player() -> None:
    players = [
        _make_test_player(1, 1, 1),
        _make_test_player(2, 2, 2),
        _make_test_player(3, 2, 3),
        _make_test_player(4, 2, 4),
        _make_test_player(5, 2, 5),
        _make_test_player(6, 3, 6),
        _make_test_player(7, 3, 7),
        _make_test_player(8, 3, 8),
        _make_test_player(9, 3, 9),
        _make_test_player(10, 3, 10),
        _make_test_player(11, 4, 11),
        _make_test_player(12, 4, 12),
        _make_test_player(
            13,
            3,
            13,
            status="u",
            can_select=False,
            chance_of_playing_next_round=0,
        ),
        _make_test_player(14, 2, 14),
        _make_test_player(15, 3, 15),
    ]

    result = build_squad_decision(
        players=players,
        teams=_make_test_teams(),
        fixtures=_make_test_fixtures(),
        picks=list(range(1, 16)),
    )

    result_ids = {
        player.player_id
        for player in [
            *result.starting_xi,
            *result.bench,
        ]
    }

    assert 13 not in result_ids
    assert len(result_ids) == 14


def test_build_squad_decision_rejects_unknown_player_id() -> None:
    player = _make_test_player(1, 1, 1)

    with pytest.raises(ValueError, match="Unknown player IDs"):
        build_squad_decision(
            players=[player],
            teams=_make_test_teams(),
            fixtures=_make_test_fixtures(),
            picks=[1, 999],
        )


def test_build_squad_decision_rejects_duplicate_player_ids() -> None:
    """A malformed pick list must fail clearly, not silently double-count
    the same real-world player as two distinct starting-XI slots.
    """
    players = [
        _make_test_player(1, 1, 1),
        _make_test_player(2, 2, 2),
        _make_test_player(3, 2, 3),
    ]

    with pytest.raises(ValueError, match="Duplicate player IDs"):
        build_squad_decision(
            players=players,
            teams=_make_test_teams(),
            fixtures=_make_test_fixtures(),
            picks=[1, 2, 2, 3],
        )