from __future__ import annotations

from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient

from app.api import routes
from app.main import app
from fpl_agent.decisions.squad_analysis import (
    SquadDecision,
    SquadPlayerAnalysis,
)


def make_player(
    player_id: int,
    position_type: int,
    team_id: int,
) -> SquadPlayerAnalysis:
    """Create a deterministic test player."""
    return SquadPlayerAnalysis(
        player_id=player_id,
        web_name=f"Player {player_id}",
        position_type=position_type,
        team_id=team_id,
        price=5.0,
        form=5.0,
        points_per_game=5.0,
        points_per_90=5.0,
        xgi_per_90=0.5,
        fixture_difficulty=2.0,
        expected_points=6.0,
        minutes_risk=0.0,
        overall_risk=0.2,
        risk_level="low",
        captaincy_score=5.0 + player_id / 100,
    )


def make_decision() -> SquadDecision:
    """Create a valid deterministic squad decision for API tests."""
    players = [
        make_player(1, 1, 1),
        make_player(2, 2, 1),
        make_player(3, 2, 2),
        make_player(4, 2, 3),
        make_player(5, 2, 4),
        make_player(6, 3, 1),
        make_player(7, 3, 2),
        make_player(8, 3, 3),
        make_player(9, 3, 4),
        make_player(10, 3, 5),
        make_player(11, 4, 1),
        make_player(12, 4, 2),
        make_player(13, 4, 3),
        make_player(14, 2, 5),
        make_player(15, 3, 6),
    ]

    starting_xi = players[:11]
    bench = players[11:]

    return SquadDecision(
        starting_xi=starting_xi,
        bench=bench,
        captain=starting_xi[10],
        vice_captain=starting_xi[9],
        must_play=[
            player
            for player in starting_xi
            if player.overall_risk < 0.4
        ],
    )


@dataclass
class FakeDecisionService:
    """Fake decision service for API tests."""

    decision: SquadDecision
    should_raise: bool = False

    async def analyze_squad(
        self,
        entry_id: int,
        gameweek: int | None = None,
    ) -> SquadDecision:
        """Return the configured test decision."""
        if self.should_raise:
            raise ValueError("Gameweek 99 was not found.")

        return self.decision


@pytest.fixture
def client() -> TestClient:
    """Create a FastAPI test client."""
    return TestClient(app)


def test_health_endpoint(client: TestClient) -> None:
    """Health endpoint should report a healthy API."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_decision_endpoint_returns_deterministic_decision(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Decision endpoint should return the deterministic squad decision."""
    decision = make_decision()
    fake_service = FakeDecisionService(decision=decision)

    monkeypatch.setattr(
        routes,
        "decision_service",
        fake_service,
    )

    response = client.get("/api/v1/decision/123456")

    assert response.status_code == 200

    body = response.json()

    assert len(body["starting_xi"]) == 11
    assert len(body["bench"]) == 4

    assert body["captain"]["player_id"] == 11
    assert body["vice_captain"]["player_id"] == 10

    assert len(body["must_play"]) == 11

    assert body["starting_xi"][0]["player_id"] == 1
    assert body["starting_xi"][0]["web_name"] == "Player 1"
    assert body["starting_xi"][0]["expected_points"] == 6.0


def test_decision_endpoint_passes_entry_and_gameweek_to_service(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Decision endpoint should pass request parameters to the service."""
    decision = make_decision()

    class RecordingDecisionService:
        def __init__(self) -> None:
            self.entry_id: int | None = None
            self.gameweek: int | None = None

        async def analyze_squad(
            self,
            entry_id: int,
            gameweek: int | None = None,
        ) -> SquadDecision:
            self.entry_id = entry_id
            self.gameweek = gameweek
            return decision

    fake_service = RecordingDecisionService()

    monkeypatch.setattr(
        routes,
        "decision_service",
        fake_service,
    )

    response = client.get(
        "/api/v1/decision/987654?gameweek=7"
    )

    assert response.status_code == 200
    assert fake_service.entry_id == 987654
    assert fake_service.gameweek == 7


def test_decision_endpoint_returns_bad_request_for_value_error(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Service validation errors should become HTTP 400 responses."""
    fake_service = FakeDecisionService(
        decision=make_decision(),
        should_raise=True,
    )

    monkeypatch.setattr(
        routes,
        "decision_service",
        fake_service,
    )

    response = client.get(
        "/api/v1/decision/123456?gameweek=99"
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Gameweek 99 was not found."
    }


def test_decision_endpoint_rejects_invalid_gameweek(
    client: TestClient,
) -> None:
    """Gameweek below one should fail FastAPI validation."""
    response = client.get(
        "/api/v1/decision/123456?gameweek=0"
    )

    assert response.status_code == 422


def test_decision_endpoint_rejects_invalid_entry_id(
    client: TestClient,
) -> None:
    """A non-integer entry ID should fail FastAPI validation."""
    response = client.get(
        "/api/v1/decision/not-an-id"
    )

    assert response.status_code == 422