from __future__ import annotations

from collections.abc import Generator

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.routes import get_decision_service
from app.main import app
from fpl_agent.analysis.sell_scoring import SellScore
from fpl_agent.data.client import FPLClient
from fpl_agent.data.errors import (
    FPLRateLimitedError,
    FPLResourceNotFoundError,
    FPLUpstreamError,
    FPLUpstreamTimeoutError,
)
from fpl_agent.decisions.gameweek_decision import (
    GameweekDecision,
    RecommendationEvidence,
    build_evidence_basis,
)
from fpl_agent.decisions.service import FPLDecisionService
from fpl_agent.decisions.squad_analysis import SquadPlayerAnalysis
from fpl_agent.decisions.transfer_analysis import (
    BuyCandidate,
    SellCandidate,
    TransferPair,
)
from fpl_agent.persistence.snapshot_store import SnapshotStore


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


def make_squad() -> tuple[list[SquadPlayerAnalysis], list[SquadPlayerAnalysis]]:
    """Build a deterministic 11 + 4 squad for gameweek-decision tests."""
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

    return starting_xi, bench


def make_transfer_pair() -> TransferPair:
    """Build one deterministic transfer pair for response-shape tests."""
    sell = SellCandidate(
        player_id=20,
        web_name="Weak Player",
        position_type=2,
        team_id=6,
        price=4.5,
        expected_points=1.0,
        form=2.0,
        fixture_difficulty=4.0,
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
        reasons=["High overall risk (high, 0.7)"],
    )

    buy = BuyCandidate(
        player_id=21,
        web_name="Strong Target",
        position_type=2,
        team_id=7,
        price=5.5,
        expected_points=8.0,
        form=7.0,
        fixture_difficulty=2.0,
        overall_risk=0.1,
        availability_risk=0.0,
        risk_level="low",
        sample_confidence=1.0,
        selection_score=8.6,
        value_score=0.15,
        rank=1,
        reasons=["Expected points: 8.0", "Low overall risk"],
    )

    return TransferPair(
        sell=sell,
        buy=buy,
        net_improvement=9.1,
        risk_change=0.6,
        price_change=1.0,
        within_budget=True,
        priority="essential",
        reasons=["Higher expected points (8.0 vs 1.0)"],
        expected_point_gain=7.0,
        hit_cost=None,
        net_value=None,
    )


def make_gameweek_decision(
    gameweek: int = 5,
    transfer_recommendations: list[TransferPair] | None = None,
    evidence: list[RecommendationEvidence] | None = None,
    free_transfers_available: int | None = None,
    in_the_bank: float | None = None,
    source_picks_gameweek: int | None = None,
) -> GameweekDecision:
    """Build a complete deterministic gameweek decision for route tests.

    `source_picks_gameweek` defaults to the target gameweek - the
    ordinary case, where the squad being planned is the one the manager
    already picked for it.
    """
    starting_xi, bench = make_squad()
    pairs = transfer_recommendations or []
    captain = starting_xi[10]
    starting_xi_expected_points = round(sum(p.expected_points for p in starting_xi), 2)
    resolved_source_gameweek = (
        gameweek if source_picks_gameweek is None else source_picks_gameweek
    )

    return GameweekDecision(
        gameweek=gameweek,
        source_picks_gameweek=resolved_source_gameweek,
        is_future_gameweek=resolved_source_gameweek < gameweek,
        generated_at="2026-01-01T00:00:00+00:00",
        decision_engine_version="v1",
        data_source="official-fpl-api",
        starting_xi=starting_xi,
        bench=bench,
        captain=captain,
        vice_captain=starting_xi[9],
        must_play=[starting_xi[10], starting_xi[9]],
        sell_candidates=[pair.sell for pair in pairs],
        buy_candidates=[pair.buy for pair in pairs],
        transfer_recommendations=pairs,
        transfer_count=len(pairs),
        best_transfer=pairs[0] if pairs else None,
        free_transfers_available=free_transfers_available,
        in_the_bank=in_the_bank,
        starting_xi_expected_points=starting_xi_expected_points,
        projected_gameweek_points=round(starting_xi_expected_points + captain.expected_points, 2),
        confidence="High",
        # Built by the real aggregation from this same starting XI, so
        # the fixture can never describe a basis the engine would not
        # have produced.
        evidence_basis=build_evidence_basis(starting_xi),
        decision_summary="Captain: Player 11 (6.0 expected points). Vice-captain: Player 10.",
        evidence=evidence or [],
    )


class FakeDecisionService:
    """Test double standing in for FPLDecisionService.

    Never calls the live FPL API. Records the arguments it was invoked
    with so tests can assert entry_id/gameweek propagation, and can be
    configured to raise instead of returning a decision.
    """

    def __init__(
        self,
        decision: GameweekDecision | None = None,
        error: Exception | None = None,
    ) -> None:
        self.decision = decision
        self.error = error
        self.calls: list[dict[str, int | None]] = []

    async def analyze_gameweek(
        self,
        entry_id: int,
        gameweek: int | None = None,
        free_transfers_available: int | None = None,
    ) -> GameweekDecision:
        self.calls.append(
            {
                "entry_id": entry_id,
                "gameweek": gameweek,
                "free_transfers_available": free_transfers_available,
            },
        )

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
    fake_service = FakeDecisionService(decision=make_gameweek_decision())
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    response = client.get("/api/v1/decision/8731757")

    assert response.status_code == 200

    payload = response.json()
    assert payload["gameweek"] == 5
    assert payload["decision_engine_version"] == "v1"
    assert payload["data_source"] == "official-fpl-api"
    assert len(payload["starting_xi"]) == 11
    assert len(payload["bench"]) == 4
    assert payload["captain"]["player_id"] == 11
    assert payload["vice_captain"]["player_id"] == 10
    assert [p["player_id"] for p in payload["must_play"]] == [11, 10]
    # The FPL 2x captain multiplier is explicit in the response and
    # applies only to the captain, never the vice.
    assert payload["captain"]["effective_points"] == payload["captain"]["expected_points"] * 2
    assert payload["vice_captain"]["effective_points"] == payload["vice_captain"]["expected_points"]
    assert payload["transfer_count"] == 0
    assert payload["transfer_recommendations"] == []
    assert payload["best_transfer"] is None
    assert payload["confidence"] == "High"


def test_response_includes_transfer_recommendation_details(
    client: TestClient,
) -> None:
    pair = make_transfer_pair()
    fake_service = FakeDecisionService(
        decision=make_gameweek_decision(transfer_recommendations=[pair]),
    )
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    response = client.get("/api/v1/decision/8731757")
    payload = response.json()

    assert payload["transfer_count"] == 1
    recommendation = payload["transfer_recommendations"][0]
    assert recommendation["sell"]["player_id"] == 20
    assert recommendation["buy"]["player_id"] == 21
    assert recommendation["priority"] == "essential"
    assert recommendation["net_improvement"] == 9.1
    # Exact content and order, not just truthiness - a lossy converter
    # (e.g. slicing to one item, or dropping the list on re-serialize)
    # would still pass a bare `assert recommendation["reasons"]`.
    assert recommendation["reasons"] == pair.reasons
    assert recommendation["sell"]["reasons"] == pair.sell.reasons
    assert recommendation["buy"]["reasons"] == pair.buy.reasons

    assert payload["best_transfer"]["sell"]["player_id"] == 20
    assert payload["best_transfer"]["buy"]["player_id"] == 21
    assert payload["best_transfer"]["reasons"] == pair.reasons

    assert payload["sell_candidates"][0]["player_id"] == 20
    assert payload["sell_candidates"][0]["reasons"] == pair.sell.reasons
    assert payload["buy_candidates"][0]["player_id"] == 21
    assert payload["buy_candidates"][0]["reasons"] == pair.buy.reasons


def test_response_preserves_evidence_reasons_exactly(client: TestClient) -> None:
    """Every evidence entry's reasons list must round-trip through the
    API byte-for-byte - this is what "Decision evidence" and "View all
    evidence" render directly on the frontend."""
    evidence = [
        RecommendationEvidence(
            player_id=11,
            decision="captain",
            score=9.2,
            reasons=["Highest captaincy score", "8.5 expected points", "Fixture difficulty 2.0"],
        ),
        RecommendationEvidence(
            player_id=10,
            decision="vice_captain",
            score=8.1,
            reasons=["Second-highest captaincy score"],
        ),
    ]
    fake_service = FakeDecisionService(
        decision=make_gameweek_decision(evidence=evidence),
    )
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    response = client.get("/api/v1/decision/8731757")
    payload = response.json()

    assert len(payload["evidence"]) == 2
    assert payload["evidence"][0]["decision"] == "captain"
    assert payload["evidence"][0]["reasons"] == evidence[0].reasons
    assert payload["evidence"][1]["decision"] == "vice_captain"
    assert payload["evidence"][1]["reasons"] == evidence[1].reasons
    assert all(item["reasons"] for item in payload["evidence"])


def test_entry_id_and_default_gameweek_propagation(
    client: TestClient,
) -> None:
    fake_service = FakeDecisionService(decision=make_gameweek_decision())
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    response = client.get("/api/v1/decision/8731757")

    assert response.status_code == 200
    assert fake_service.calls == [
        {"entry_id": 8731757, "gameweek": None, "free_transfers_available": None},
    ]


def test_gameweek_query_parameter_propagation(
    client: TestClient,
) -> None:
    fake_service = FakeDecisionService(decision=make_gameweek_decision())
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    response = client.get("/api/v1/decision/8731757", params={"gameweek": 5})

    assert response.status_code == 200
    assert fake_service.calls == [
        {"entry_id": 8731757, "gameweek": 5, "free_transfers_available": None},
    ]


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
    fake_service = FakeDecisionService(decision=make_gameweek_decision())
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    response = client.get("/api/v1/decision/not-an-int")

    assert response.status_code == 422
    assert fake_service.calls == []


def test_non_positive_gameweek_returns_http_422(client: TestClient) -> None:
    fake_service = FakeDecisionService(decision=make_gameweek_decision())
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
    fake_service = FakeDecisionService(decision=make_gameweek_decision())
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    response = client.get("/api/v1/decision/8731757")
    payload = response.json()

    assert set(payload.keys()) == {
        "gameweek",
        "source_picks_gameweek",
        "is_future_gameweek",
        "generated_at",
        "decision_engine_version",
        "data_source",
        "starting_xi",
        "bench",
        "captain",
        "vice_captain",
        "must_play",
        "sell_candidates",
        "buy_candidates",
        "transfer_recommendations",
        "transfer_count",
        "best_transfer",
        "free_transfers_available",
        "in_the_bank",
        "starting_xi_expected_points",
        "projected_gameweek_points",
        "confidence",
        "evidence_basis",
        "decision_summary",
        "evidence",
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
        "effective_points",
    }


def test_default_dependency_wiring_resolves_to_module_singleton() -> None:
    """The application should wire the route to the shared service by default."""
    from app.api.routes import decision_service

    assert isinstance(get_decision_service(), type(decision_service))
    assert get_decision_service() is decision_service


def test_response_exposes_manager_transfer_context(client: TestClient) -> None:
    """Case 7: free transfers and money in the bank travel to the client
    as first-class fields, not buried inside a recommendation."""
    fake_service = FakeDecisionService(
        decision=make_gameweek_decision(
            free_transfers_available=1,
            in_the_bank=2.5,
        ),
    )
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    payload = client.get("/api/v1/decision/8731757").json()

    assert payload["free_transfers_available"] == 1
    assert payload["in_the_bank"] == 2.5


def test_response_identifies_the_gameweek_being_predicted(client: TestClient) -> None:
    """An ordinary decision plans the squad already picked for that
    gameweek, so target and source are the same and nothing is
    forward-looking."""
    fake_service = FakeDecisionService(decision=make_gameweek_decision(gameweek=3))
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    payload = client.get("/api/v1/decision/8731757").json()

    assert payload["gameweek"] == 3
    assert payload["source_picks_gameweek"] == 3
    assert payload["is_future_gameweek"] is False


def test_response_distinguishes_a_predicted_upcoming_gameweek(client: TestClient) -> None:
    """Predicting gameweek 4 from the gameweek 3 squad must say so, so a
    client never implies the upcoming gameweek's picks already exist."""
    fake_service = FakeDecisionService(
        decision=make_gameweek_decision(gameweek=4, source_picks_gameweek=3),
    )
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    payload = client.get("/api/v1/decision/8731757", params={"gameweek": 4}).json()

    assert payload["gameweek"] == 4
    assert payload["source_picks_gameweek"] == 3
    assert payload["is_future_gameweek"] is True


def test_response_exposes_recommendation_economics(client: TestClient) -> None:
    """Case 7: expected gain, hit cost, and net value are all present on
    each recommendation, and net_value is internally consistent."""
    pair = make_transfer_pair()
    fake_service = FakeDecisionService(
        decision=make_gameweek_decision(transfer_recommendations=[pair]),
    )
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    payload = client.get("/api/v1/decision/8731757").json()
    recommendation = payload["transfer_recommendations"][0]

    assert recommendation["expected_point_gain"] == pair.expected_point_gain
    assert recommendation["hit_cost"] == pair.hit_cost
    assert recommendation["net_value"] == pair.net_value
    assert recommendation["priority"] == pair.priority
    assert recommendation["within_budget"] == pair.within_budget


def test_free_transfers_available_query_parameter_propagation(
    client: TestClient,
) -> None:
    """The manager's own free-transfer count is the only source for a
    value no public FPL endpoint exposes, so it has to reach the
    deterministic service intact."""
    fake_service = FakeDecisionService(decision=make_gameweek_decision())
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    response = client.get(
        "/api/v1/decision/8731757",
        params={"free_transfers_available": 2},
    )

    assert response.status_code == 200
    assert fake_service.calls == [
        {"entry_id": 8731757, "gameweek": None, "free_transfers_available": 2},
    ]


def test_negative_free_transfers_available_returns_http_422(
    client: TestClient,
) -> None:
    fake_service = FakeDecisionService(decision=make_gameweek_decision())
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    response = client.get(
        "/api/v1/decision/8731757",
        params={"free_transfers_available": -1},
    )

    assert response.status_code == 422
    assert fake_service.calls == []


def test_upstream_not_found_returns_http_404(client: TestClient) -> None:
    """An entry ID FPL has never issued, or a gameweek whose squad is
    not picked yet, is the caller's mistake - not an internal fault."""
    fake_service = FakeDecisionService(
        error=FPLResourceNotFoundError(
            "FPL entry 8731757 was not found in the official FPL API.",
        ),
    )
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    response = client.get("/api/v1/decision/8731757")

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "FPL entry 8731757 was not found in the official FPL API."
    )


def test_upstream_not_found_response_hides_internal_detail(client: TestClient) -> None:
    fake_service = FakeDecisionService(
        error=FPLResourceNotFoundError(
            "FPL entry 8731757 was not found in the official FPL API.",
        ),
    )
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    body = client.get("/api/v1/decision/8731757").text

    assert "httpx" not in body.lower()
    assert "Traceback" not in body
    assert "raise_for_status" not in body
    assert "fantasy.premierleague.com" not in body


def test_upstream_failure_returns_http_502_rather_than_404(client: TestClient) -> None:
    """A broken upstream must not be reported as "not found", which
    would wrongly tell the caller their entry ID was invalid."""
    fake_service = FakeDecisionService(
        error=FPLUpstreamError("The official FPL API could not return fpl entry 8731757."),
    )
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    response = client.get("/api/v1/decision/8731757")

    assert response.status_code == 502


def test_upstream_timeout_returns_http_504_rather_than_404(client: TestClient) -> None:
    fake_service = FakeDecisionService(
        error=FPLUpstreamTimeoutError(
            "Timed out fetching fpl entry 8731757 from the official FPL API.",
        ),
    )
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    response = client.get("/api/v1/decision/8731757")

    assert response.status_code == 504


def test_upstream_rate_limit_returns_http_429(client: TestClient) -> None:
    fake_service = FakeDecisionService(
        error=FPLRateLimitedError(
            "The official FPL API is rate limiting this service. Please try again shortly.",
        ),
    )
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    response = client.get("/api/v1/decision/8731757")

    assert response.status_code == 429


def test_upstream_404_reaches_the_client_as_http_404_end_to_end(
    client: TestClient,
) -> None:
    """The whole chain, with only the network faked: an httpx 404 from
    a real `FPLClient`, through a real `FPLDecisionService`, to the
    HTTP response. Guards against any layer in between swallowing or
    re-wrapping the error back into a 500.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "upstream-only diagnostic text"})

    service = FPLDecisionService(
        client=FPLClient(transport=httpx.MockTransport(handler)),
        snapshot_store=SnapshotStore(":memory:"),
    )
    app.dependency_overrides[get_decision_service] = lambda: service

    response = client.get("/api/v1/decision/8731757")

    assert response.status_code == 404
    assert "upstream-only diagnostic text" not in response.text
    assert "httpx" not in response.text.lower()


def test_upstream_500_reaches_the_client_as_http_502_end_to_end(
    client: TestClient,
) -> None:
    """Same chain, but a failing upstream must not be reported as a
    404 - that would wrongly blame the caller's entry ID."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"detail": "upstream is down"})

    service = FPLDecisionService(
        client=FPLClient(transport=httpx.MockTransport(handler)),
        snapshot_store=SnapshotStore(":memory:"),
    )
    app.dependency_overrides[get_decision_service] = lambda: service

    response = client.get("/api/v1/decision/8731757")

    assert response.status_code == 502
    assert "upstream is down" not in response.text


def test_unexpected_application_error_still_returns_http_500() -> None:
    """The translation layer must not swallow genuine bugs. A plain
    RuntimeError is not an `FPLDataError`, so it has to stay a 500
    rather than being disguised as an upstream fault."""
    fake_service = FakeDecisionService(error=RuntimeError("a genuine bug"))
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    # raise_server_exceptions=False so the response is observed the way
    # a real client would see it, instead of the error propagating out
    # of the test client.
    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.get("/api/v1/decision/8731757")

    app.dependency_overrides.clear()

    assert response.status_code == 500


def test_decision_response_exposes_the_basis_behind_its_confidence(
    client: TestClient,
) -> None:
    """The confidence label is only explainable client-side if the
    figures behind it travel with it - the starting XI's per-player
    sample_confidence is deliberately not exposed, so this object is
    the only honest source for that explanation."""
    fake_service = FakeDecisionService(decision=make_gameweek_decision())
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    payload = client.get("/api/v1/decision/8731757").json()
    basis = payload["evidence_basis"]

    assert set(basis.keys()) == {
        "level",
        "average_sample_confidence",
        "medium_threshold",
        "high_threshold",
        "players_considered",
        "limited_sample_players",
        "partial_sample_players",
        "full_sample_players",
        "limited_sample_minutes",
    }

    # The basis describes the very label shipped alongside it.
    assert basis["level"] == payload["confidence"]
    assert basis["players_considered"] == len(payload["starting_xi"])
    assert (
        basis["limited_sample_players"]
        + basis["partial_sample_players"]
        + basis["full_sample_players"]
        == basis["players_considered"]
    )


def test_evidence_basis_does_not_leak_per_player_sample_confidence(
    client: TestClient,
) -> None:
    """Adding the basis must not widen the squad-player contract: sample
    confidence stays an aggregate, never a per-starter figure."""
    fake_service = FakeDecisionService(decision=make_gameweek_decision())
    app.dependency_overrides[get_decision_service] = lambda: fake_service

    payload = client.get("/api/v1/decision/8731757").json()

    for player in payload["starting_xi"]:
        assert "sample_confidence" not in player
