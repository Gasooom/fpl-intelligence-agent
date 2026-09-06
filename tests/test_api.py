from __future__ import annotations

from fpl_agent.api.decision import (
    _player_to_response,
    squad_decision_to_response,
)
from fpl_agent.api.schemas import (
    PlayerDecisionResponse,
    SquadDecisionResponse,
)
from fpl_agent.decisions.squad_analysis import (
    SquadDecision,
    SquadPlayerAnalysis,
)


def make_player(
    player_id: int,
    position_type: int,
    team_id: int,
    expected_points: float = 6.0,
    captaincy_score: float = 5.0,
) -> SquadPlayerAnalysis:
    """Create a deterministic test player."""
    form = 5.0
    overall_risk = 0.2
    sample_confidence = 1.0

    selection_score = (
        expected_points
        + form * 0.15
        + (sample_confidence - 0.5) * 0.5
        - overall_risk * 2.0
    )

    return SquadPlayerAnalysis(
        player_id=player_id,
        web_name=f"Player {player_id}",
        position_type=position_type,
        team_id=team_id,
        price=5.0,
        form=form,
        points_per_game=5.0,
        points_per_90=5.0,
        xgi_per_90=0.5,
        fixture_difficulty=2.0,
        expected_points=expected_points,
        minutes_risk=0.0,
        form_uncertainty=0.0,
        fixture_risk=0.0,
        availability_risk=0.0,
        overall_risk=overall_risk,
        risk_level="low",
        sample_confidence=sample_confidence,
        captaincy_score=captaincy_score,
        selection_score=selection_score,
    )


def make_decision() -> SquadDecision:
    """Create a deterministic squad decision for API tests."""
    starting_xi = [
        make_player(1, 1, 1, 6.0, 5.01),
        make_player(2, 2, 2, 6.0, 5.02),
        make_player(3, 2, 3, 6.0, 5.03),
        make_player(4, 2, 4, 6.0, 5.04),
        make_player(5, 2, 5, 6.0, 5.05),
        make_player(6, 3, 1, 6.0, 5.06),
        make_player(7, 3, 2, 6.0, 5.07),
        make_player(8, 3, 3, 6.0, 5.08),
        make_player(9, 3, 4, 6.0, 5.09),
        make_player(10, 3, 5, 6.0, 5.10),
        make_player(11, 4, 1, 6.0, 5.11),
    ]

    bench = [
        make_player(12, 1, 2, 5.0, 4.12),
        make_player(13, 2, 3, 5.0, 4.13),
        make_player(14, 3, 4, 5.0, 4.14),
        make_player(15, 4, 5, 5.0, 4.15),
    ]

    return SquadDecision(
        starting_xi=starting_xi,
        bench=bench,
        captain=starting_xi[10],
        vice_captain=starting_xi[9],
        must_play=[
            starting_xi[10],
            starting_xi[9],
        ],
    )


def test_player_to_response_returns_expected_schema() -> None:
    """A player analysis should convert to the public API schema."""
    player = make_player(
        player_id=7,
        position_type=3,
        team_id=4,
        expected_points=8.5,
        captaincy_score=9.2,
    )

    response = _player_to_response(player)

    assert isinstance(response, PlayerDecisionResponse)

    assert response.player_id == 7
    assert response.web_name == "Player 7"
    assert response.position_type == 3
    assert response.team_id == 4
    assert response.price == 5.0

    assert response.form == 5.0
    assert response.points_per_game == 5.0
    assert response.points_per_90 == 5.0
    assert response.xgi_per_90 == 0.5

    assert response.fixture_difficulty == 2.0
    assert response.expected_points == 8.5

    assert response.minutes_risk == 0.0
    assert response.availability_risk == 0.0
    assert response.overall_risk == 0.2
    assert response.risk_level == "low"

    assert response.captaincy_score == 9.2


def test_player_to_response_does_not_expose_internal_fields() -> None:
    """Internal decision fields should not leak into the API response."""
    player = make_player(
        player_id=1,
        position_type=1,
        team_id=1,
    )

    response = _player_to_response(player)

    payload = response.model_dump()

    assert "form_uncertainty" not in payload
    assert "fixture_risk" not in payload
    assert "sample_confidence" not in payload
    assert "selection_score" not in payload


def test_squad_decision_to_response_returns_complete_response() -> None:
    """A complete deterministic decision should map to the API schema."""
    decision = make_decision()

    response = squad_decision_to_response(decision)

    assert isinstance(response, SquadDecisionResponse)

    assert len(response.starting_xi) == 11
    assert len(response.bench) == 4

    assert (
        response.captain.player_id
        == decision.captain.player_id
    )

    assert (
        response.vice_captain.player_id
        == decision.vice_captain.player_id
    )

    assert [
        player.player_id
        for player in response.must_play
    ] == [
        player.player_id
        for player in decision.must_play
    ]


def test_squad_decision_to_response_preserves_starting_xi_order() -> None:
    """Starting XI order should remain unchanged during conversion."""
    decision = make_decision()

    response = squad_decision_to_response(decision)

    assert [
        player.player_id
        for player in response.starting_xi
    ] == list(range(1, 12))


def test_squad_decision_to_response_preserves_bench_order() -> None:
    """Bench order should remain unchanged during conversion."""
    decision = make_decision()

    response = squad_decision_to_response(decision)

    assert [
        player.player_id
        for player in response.bench
    ] == [12, 13, 14, 15]


def test_squad_decision_response_rejects_invalid_starting_xi_size() -> None:
    """The API schema should enforce exactly eleven starters."""
    decision = make_decision()

    payload = squad_decision_to_response(decision).model_dump()

    payload["starting_xi"] = payload["starting_xi"][:10]

    try:
        SquadDecisionResponse.model_validate(payload)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected SquadDecisionResponse validation to fail."
        )


def test_squad_decision_response_allows_empty_bench() -> None:
    """The API schema should allow decisions with no bench players."""
    decision = make_decision()

    payload = squad_decision_to_response(decision).model_dump()
    payload["bench"] = []

    response = SquadDecisionResponse.model_validate(payload)

    assert response.bench == []