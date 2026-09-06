from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.api.routes import get_decision_service
from app.main import app
from fpl_agent.decisions.squad_analysis import SquadDecision, SquadPlayerAnalysis


def make_player(
    player_id: int,
    position_type: int,
    team_id: int,
    expected_points: float = 6.0,
    captaincy_score: float = 5.0,
) -> SquadPlayerAnalysis:
    """Create a deterministic test player analysis."""
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
    """Create a complete deterministic squad decision for route tests."""
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
        must_play=[starting_xi[10], starting_xi[9]],
    )


class FakeDecisionService:
    """Test double standing in for FPLDecisionService.

    Never calls the live FPL API. Records the arguments it was invoked
    with so tests can assert entry_id/gameweek propagation, and can be
    configured to raise instead of returning a decision.
    """

    def __init__(
        self,
        decision: SquadDecision | None = None,
        error: Exception | None = None,
    ) -> None:
        self.decision = decision
        self.error = error
        self.calls: list[dict[str, int | None]] = []

    async def analyze_squad(
        self,
        entry_id: int,
        gameweek: int | None = None,
    ) -> SquadDecision:
        self.calls.append({"entry_id": entry_id, "gameweek": gameweek})

        if self.error is not None:
            raise self.error

        assert self.decision is not None
        return self.decision


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Provide a TestClient with dependency overrides cleaned up after use."""
    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_valid_request_returns_deterministic_decision(
    client: TestClient,
) -> None:
    fake_service = FakeDecisionService(decision=make_decision())
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    response = client.get("/api/v1/decision/8731757")

    assert response.status_code == 200

    payload = response.json()
    assert len(payload["starting_xi"]) == 11
    assert len(payload["bench"]) == 4
    assert payload["captain"]["player_id"] == 11
    assert payload["vice_captain"]["player_id"] == 10
    assert [p["player_id"] for p in payload["must_play"]] == [11, 10]


def test_entry_id_and_default_gameweek_propagation(
    client: TestClient,
) -> None:
    fake_service = FakeDecisionService(decision=make_decision())
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    response = client.get("/api/v1/decision/8731757")

    assert response.status_code == 200
    assert fake_service.calls == [{"entry_id": 8731757, "gameweek": None}]


def test_gameweek_query_parameter_propagation(
    client: TestClient,
) -> None:
    fake_service = FakeDecisionService(decision=make_decision())
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    response = client.get("/api/v1/decision/8731757", params={"gameweek": 5})

    assert response.status_code == 200
    assert fake_service.calls == [{"entry_id": 8731757, "gameweek": 5}]


def test_service_value_error_returns_http_400(
    client: TestClient,
) -> None:
    fake_service = FakeDecisionService(
        error=ValueError("Gameweek 99 was not found."),
    )
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    response = client.get(
        "/api/v1/decision/8731757",
        params={"gameweek": 99},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Gameweek 99 was not found."


def test_invalid_entry_id_returns_http_422(client: TestClient) -> None:
    fake_service = FakeDecisionService(decision=make_decision())
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    response = client.get("/api/v1/decision/not-an-int")

    assert response.status_code == 422
    assert fake_service.calls == []


def test_non_positive_gameweek_returns_http_422(client: TestClient) -> None:
    fake_service = FakeDecisionService(decision=make_decision())
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    response = client.get(
        "/api/v1/decision/8731757",
        params={"gameweek": 0},
    )

    assert response.status_code == 422
    assert fake_service.calls == []


def test_response_matches_deterministic_schema_and_hides_internal_fields(
    client: TestClient,
) -> None:
    fake_service = FakeDecisionService(decision=make_decision())
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    response = client.get("/api/v1/decision/8731757")
    payload = response.json()

    assert set(payload.keys()) == {
        "starting_xi",
        "bench",
        "captain",
        "vice_captain",
        "must_play",
    }

    captain_fields = set(payload["captain"].keys())
    assert "selection_score" not in captain_fields
    assert "sample_confidence" not in captain_fields
    assert "form_uncertainty" not in captain_fields
    assert "fixture_risk" not in captain_fields
    assert captain_fields == {
        "player_id",
        "web_name",
        "position_type",
        "team_id",
        "price",
        "form",
        "points_per_game",
        "points_per_90",
        "xgi_per_90",
        "fixture_difficulty",
        "expected_points",
        "minutes_risk",
        "availability_risk",
        "overall_risk",
        "risk_level",
        "captaincy_score",
    }


def test_default_dependency_wiring_resolves_to_module_singleton() -> None:
    """The application should wire the route to the shared service by default."""
    from app.api.routes import decision_service

    assert isinstance(get_decision_service(), type(decision_service))
    assert get_decision_service() is decision_service
