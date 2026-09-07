from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.api.routes import get_decision_service
from app.main import app
from fpl_agent.decisions.evaluation import (
    CaptainEvaluation,
    GameweekEvaluation,
    PlayerEvaluation,
    StartingXIEvaluation,
    TransferEvaluation,
    build_missing_snapshot_evaluation,
    build_not_completed_evaluation,
)


def make_player_evaluation(
    player_id: int = 1,
    position_type: int = 3,
    expected_points: float = 10.31,
    actual_points: int = 12,
) -> PlayerEvaluation:
    return PlayerEvaluation(
        player_id=player_id,
        web_name=f"Player {player_id}",
        position_type=position_type,
        expected_points=expected_points,
        actual_points=actual_points,
        prediction_error=round(actual_points - expected_points, 2),
    )


class FakeDecisionService:
    """Test double standing in for FPLDecisionService. Never calls the live API."""

    def __init__(
        self,
        evaluation: GameweekEvaluation | None = None,
        error: Exception | None = None,
    ) -> None:
        self.evaluation = evaluation
        self.error = error
        self.calls: list[dict[str, int | None]] = []

    async def evaluate_gameweek(
        self,
        entry_id: int,
        gameweek: int | None = None,
    ) -> GameweekEvaluation:
        self.calls.append({"entry_id": entry_id, "gameweek": gameweek})

        if self.error is not None:
            raise self.error

        assert self.evaluation is not None
        return self.evaluation


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_not_completed_gameweek_returns_honest_status(client: TestClient) -> None:
    fake_service = FakeDecisionService(
        evaluation=build_not_completed_evaluation(entry_id=8731757, gameweek=4),
    )
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    response = client.get("/api/v1/evaluation/8731757", params={"gameweek": 4})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "not_completed"
    assert payload["captain"] is None
    assert payload["starting_xi"] is None
    assert payload["best_transfer"] is None
    assert "not completed" in payload["message"].lower()


def test_missing_snapshot_returns_honest_status(client: TestClient) -> None:
    fake_service = FakeDecisionService(
        evaluation=build_missing_snapshot_evaluation(entry_id=8731757, gameweek=3),
    )
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    response = client.get("/api/v1/evaluation/8731757", params={"gameweek": 3})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "no_snapshot"
    assert payload["captain"] is None
    assert "no decision snapshot" in payload["message"].lower()


def test_evaluated_gameweek_returns_full_prediction_vs_actual_response(client: TestClient) -> None:
    evaluation = GameweekEvaluation(
        entry_id=8731757,
        gameweek=3,
        status="evaluated",
        message="Evaluated against actual gameweek 3 results.",
        decision_generated_at="2026-08-10T09:00:00+00:00",
        captain=CaptainEvaluation(
            captain_player_id=1,
            captain_web_name="Cherki",
            captain_expected_points=10.31,
            vice_captain_player_id=2,
            vice_captain_web_name="Haaland",
            captain_actual_points=12,
            vice_captain_actual_points=4,
            outcome="correct",
        ),
        starting_xi=StartingXIEvaluation(
            starting_xi_actual_total=55,
            bench_actual_total=6,
            difference=49,
            starting_xi_expected_total=60.5,
            prediction_error=-5.5,
        ),
        best_transfer=TransferEvaluation(
            sell_player_id=20,
            sell_web_name="Neto",
            buy_player_id=21,
            buy_web_name="Gakpo",
            expected_improvement=8.13,
            sell_actual_points=0,
            buy_actual_points=6,
            actual_improvement=6,
            prediction_error=-2.13,
            direction="positive",
        ),
        starting_xi_players=[make_player_evaluation()],
        bench_players=[make_player_evaluation(player_id=12, position_type=1)],
    )
    fake_service = FakeDecisionService(evaluation=evaluation)
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    response = client.get("/api/v1/evaluation/8731757", params={"gameweek": 3})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "evaluated"
    assert payload["captain"]["outcome"] == "correct"
    assert payload["starting_xi"]["difference"] == 49
    assert payload["best_transfer"]["direction"] == "positive"
    assert payload["best_transfer"]["prediction_error"] == -2.13


def test_evaluation_omits_best_transfer_when_none_was_recommended(client: TestClient) -> None:
    evaluation = GameweekEvaluation(
        entry_id=8731757,
        gameweek=3,
        status="evaluated",
        message="Evaluated against actual gameweek 3 results.",
        decision_generated_at="2026-08-10T09:00:00+00:00",
        captain=CaptainEvaluation(
            captain_player_id=1,
            captain_web_name="Cherki",
            captain_expected_points=10.31,
            vice_captain_player_id=2,
            vice_captain_web_name="Haaland",
            captain_actual_points=12,
            vice_captain_actual_points=4,
            outcome="correct",
        ),
        starting_xi=StartingXIEvaluation(
            starting_xi_actual_total=55,
            bench_actual_total=6,
            difference=49,
            starting_xi_expected_total=60.5,
            prediction_error=-5.5,
        ),
        best_transfer=None,
        starting_xi_players=[make_player_evaluation()],
        bench_players=[],
    )
    fake_service = FakeDecisionService(evaluation=evaluation)
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    response = client.get("/api/v1/evaluation/8731757", params={"gameweek": 3})

    assert response.json()["best_transfer"] is None


def test_entry_id_and_gameweek_propagation(client: TestClient) -> None:
    fake_service = FakeDecisionService(
        evaluation=build_not_completed_evaluation(entry_id=8731757, gameweek=5),
    )
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    client.get("/api/v1/evaluation/8731757", params={"gameweek": 5})

    assert fake_service.calls == [{"entry_id": 8731757, "gameweek": 5}]


def test_gameweek_defaults_to_none_when_not_supplied(client: TestClient) -> None:
    fake_service = FakeDecisionService(
        evaluation=build_not_completed_evaluation(entry_id=8731757, gameweek=5),
    )
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    client.get("/api/v1/evaluation/8731757")

    assert fake_service.calls == [{"entry_id": 8731757, "gameweek": None}]


def test_service_value_error_returns_http_400(client: TestClient) -> None:
    fake_service = FakeDecisionService(error=ValueError("Gameweek 99 was not found."))
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    response = client.get("/api/v1/evaluation/8731757", params={"gameweek": 99})

    assert response.status_code == 400
    assert response.json()["detail"] == "Gameweek 99 was not found."


def test_invalid_entry_id_returns_http_422(client: TestClient) -> None:
    fake_service = FakeDecisionService(
        evaluation=build_not_completed_evaluation(entry_id=8731757, gameweek=5),
    )
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    response = client.get("/api/v1/evaluation/not-an-int")

    assert response.status_code == 422
    assert fake_service.calls == []


def test_non_positive_gameweek_returns_http_422(client: TestClient) -> None:
    fake_service = FakeDecisionService(
        evaluation=build_not_completed_evaluation(entry_id=8731757, gameweek=5),
    )
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    response = client.get("/api/v1/evaluation/8731757", params={"gameweek": 0})

    assert response.status_code == 422
    assert fake_service.calls == []


def test_response_matches_deterministic_schema(client: TestClient) -> None:
    fake_service = FakeDecisionService(
        evaluation=build_not_completed_evaluation(entry_id=8731757, gameweek=5),
    )
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    response = client.get("/api/v1/evaluation/8731757", params={"gameweek": 5})
    payload = response.json()

    assert set(payload.keys()) == {
        "entry_id",
        "gameweek",
        "status",
        "message",
        "decision_generated_at",
        "captain",
        "starting_xi",
        "best_transfer",
        "starting_xi_players",
        "bench_players",
    }
