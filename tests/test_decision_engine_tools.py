from __future__ import annotations

from fpl_agent.agent.tools import (
    get_captaincy_score,
    get_fixture_difficulty,
    get_player_projection,
    get_risk_signals,
    get_transfer_candidate_score,
)


def test_get_fixture_difficulty_is_registered() -> None:
    assert get_fixture_difficulty.name == "get_fixture_difficulty"
    assert get_fixture_difficulty.params_json_schema["type"] == "object"


def test_get_player_projection_is_registered() -> None:
    assert get_player_projection.name == "get_player_projection"
    assert get_player_projection.params_json_schema["type"] == "object"


def test_get_transfer_candidate_score_is_registered() -> None:
    assert (
        get_transfer_candidate_score.name
        == "get_transfer_candidate_score"
    )
    assert (
        get_transfer_candidate_score.params_json_schema["type"]
        == "object"
    )


def test_get_captaincy_score_is_registered() -> None:
    assert get_captaincy_score.name == "get_captaincy_score"
    assert get_captaincy_score.params_json_schema["type"] == "object"


def test_get_risk_signals_is_registered() -> None:
    assert get_risk_signals.name == "get_risk_signals"
    assert get_risk_signals.params_json_schema["type"] == "object"


def test_get_fixture_difficulty_has_required_parameters() -> None:
    schema = get_fixture_difficulty.params_json_schema

    assert "fixtures" in schema["properties"]
    assert "team_id" in schema["properties"]
    assert "limit" in schema["properties"]


def test_get_player_projection_has_required_parameters() -> None:
    schema = get_player_projection.params_json_schema

    assert "player_id" in schema["properties"]
    assert "points_per_game" in schema["properties"]
    assert "points_per_90" in schema["properties"]
    assert "xgi_per_90" in schema["properties"]
    assert "fixture_difficulty" in schema["properties"]


def test_get_transfer_candidate_score_has_required_parameters() -> None:
    schema = get_transfer_candidate_score.params_json_schema

    assert "player_id" in schema["properties"]
    assert "expected_points" in schema["properties"]
    assert "form" in schema["properties"]
    assert "fixture_difficulty" in schema["properties"]
    assert "price" in schema["properties"]


def test_get_captaincy_score_has_required_parameters() -> None:
    schema = get_captaincy_score.params_json_schema

    assert "player_id" in schema["properties"]
    assert "expected_points" in schema["properties"]
    assert "form" in schema["properties"]
    assert "fixture_difficulty" in schema["properties"]


def test_get_risk_signals_has_required_parameters() -> None:
    schema = get_risk_signals.params_json_schema

    assert "minutes" in schema["properties"]
    assert "form" in schema["properties"]
    assert "fixture_difficulty" in schema["properties"]