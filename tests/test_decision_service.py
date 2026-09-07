from __future__ import annotations

import pytest

from fpl_agent.data.models import (
    BootstrapData,
    EventLiveElement,
    EventLiveElementStats,
    EventLiveResponse,
    Fixture,
    FPLEntry,
    Gameweek,
    SquadPick,
    SquadPicksResponse,
)
from fpl_agent.decisions.evaluation import (
    STATUS_EVALUATED,
    STATUS_NO_SNAPSHOT,
    STATUS_NOT_COMPLETED,
)
from fpl_agent.decisions.service import FPLDecisionService
from fpl_agent.persistence.snapshot_store import SnapshotStore

ENTRY_ID = 8731757


def make_gameweek(gw_id: int, finished: bool, is_current: bool = False) -> Gameweek:
    return Gameweek(
        id=gw_id,
        name=f"Gameweek {gw_id}",
        deadline_time="2026-08-10T10:00:00Z",
        finished=finished,
        is_previous=False,
        is_current=is_current,
        is_next=not is_current and not finished,
    )


def make_player(
    player_id: int,
    element_type: int = 3,
    team_id: int = 1,
    minutes: int = 900,
) -> dict[str, object]:
    return {
        "id": player_id,
        "first_name": "Test",
        "second_name": f"Player{player_id}",
        "web_name": f"Player {player_id}",
        "team": team_id,
        "element_type": element_type,
        "now_cost": 50,
        "total_points": 50,
        "minutes": minutes,
        "goals_scored": 1,
        "assists": 1,
        "clean_sheets": 1,
        "goals_conceded": 5,
        "own_goals": 0,
        "penalties_saved": 0,
        "penalties_missed": 0,
        "yellow_cards": 0,
        "red_cards": 0,
        "saves": 0,
        "bonus": 2,
        "form": "5.0",
        "points_per_game": "5.0",
        "selected_by_percent": "10.0",
        "transfers_in": 0,
        "transfers_out": 0,
        "expected_goals": "1.0",
        "expected_assists": "1.0",
        "expected_goal_involvements": "2.0",
        "expected_goals_conceded": "5.0",
        "influence": "50.0",
        "creativity": "50.0",
        "threat": "50.0",
        "ict_index": "15.0",
    }


def make_bootstrap(gameweeks: list[Gameweek]) -> BootstrapData:
    from fpl_agent.data.models import Player, Team

    # 1 GK + 4 DEF + 5 MID + 1 FWD = a valid 11-player formation, each
    # on a distinct team so the max-3-per-team constraint is trivially
    # satisfied.
    positions = [1, 2, 2, 2, 2, 3, 3, 3, 3, 3, 4]
    players = [
        Player.model_validate(make_player(player_id, element_type, team_id=player_id))
        for player_id, element_type in zip(
            range(1, len(positions) + 1),
            positions,
            strict=True,
        )
    ]
    teams = [
        Team(
            id=team_id,
            name=f"Team {team_id}",
            short_name=f"T{team_id}",
            code=team_id,
            played=0,
            win=0,
            draw=0,
            loss=0,
            points=0,
        )
        for team_id in range(1, 21)
    ]

    return BootstrapData(elements=players, teams=teams, events=gameweeks)


class FakeFPLClient:
    """Test double standing in for FPLClient. Never calls the live API."""

    def __init__(
        self,
        bootstrap: BootstrapData,
        picks: list[int],
        live_by_gameweek: dict[int, EventLiveResponse] | None = None,
    ) -> None:
        self.bootstrap = bootstrap
        self.picks = picks
        self.live_by_gameweek = live_by_gameweek or {}
        self.get_event_live_calls: list[int] = []

    async def get_bootstrap_static(self) -> BootstrapData:
        return self.bootstrap

    async def get_entry(self, entry_id: int) -> FPLEntry:
        return FPLEntry(
            id=entry_id,
            player_first_name="Test",
            player_last_name="Manager",
            summary_overall_points=100,
            summary_event_points=50,
        )

    async def get_entry_picks(self, entry_id: int, gameweek: int) -> SquadPicksResponse:
        return SquadPicksResponse(
            picks=[
                SquadPick(
                    element=player_id,
                    position=index + 1,
                    multiplier=1,
                    is_captain=False,
                    is_vice_captain=False,
                    element_type=1,
                )
                for index, player_id in enumerate(self.picks)
            ],
            entry_history={},
        )

    async def get_fixtures(self) -> list[Fixture]:
        return []

    async def get_event_live(self, gameweek: int) -> EventLiveResponse:
        self.get_event_live_calls.append(gameweek)
        return self.live_by_gameweek[gameweek]


def make_live(*points: tuple[int, int]) -> EventLiveResponse:
    return EventLiveResponse(
        elements=[
            EventLiveElement(id=player_id, stats=EventLiveElementStats(total_points=total))
            for player_id, total in points
        ],
    )


PICKS = list(range(1, 12))


# --- Snapshot persistence side effect of analyze_gameweek ---


@pytest.mark.asyncio
async def test_analyze_gameweek_persists_a_snapshot_for_an_unfinished_gameweek() -> None:
    bootstrap = make_bootstrap([make_gameweek(3, finished=False, is_current=True)])
    client = FakeFPLClient(bootstrap, PICKS)
    store = SnapshotStore(":memory:")
    service = FPLDecisionService(client=client, snapshot_store=store)  # type: ignore[arg-type]

    decision = await service.analyze_gameweek(entry_id=ENTRY_ID)

    snapshot = store.get_snapshot(entry_id=ENTRY_ID, gameweek=3)
    assert snapshot is not None
    assert snapshot.captain_player_id == decision.captain.player_id
    assert snapshot.vice_captain_player_id == decision.vice_captain.player_id


@pytest.mark.asyncio
async def test_analyze_gameweek_does_not_persist_a_snapshot_for_a_finished_gameweek() -> None:
    """Recomputing a decision for an already-finished gameweek uses
    today's bootstrap data, not what was true before that gameweek's
    deadline - it must never be recorded as if it were the original
    recommendation."""
    bootstrap = make_bootstrap([make_gameweek(3, finished=True)])
    client = FakeFPLClient(bootstrap, PICKS)
    store = SnapshotStore(":memory:")
    service = FPLDecisionService(client=client, snapshot_store=store)  # type: ignore[arg-type]

    await service.analyze_gameweek(entry_id=ENTRY_ID, gameweek=3)

    assert store.get_snapshot(entry_id=ENTRY_ID, gameweek=3) is None


@pytest.mark.asyncio
async def test_analyze_gameweek_never_overwrites_an_existing_snapshot() -> None:
    bootstrap = make_bootstrap([make_gameweek(3, finished=False, is_current=True)])
    client = FakeFPLClient(bootstrap, PICKS)
    store = SnapshotStore(":memory:")
    service = FPLDecisionService(client=client, snapshot_store=store)  # type: ignore[arg-type]

    await service.analyze_gameweek(entry_id=ENTRY_ID)
    first_snapshot = store.get_snapshot(entry_id=ENTRY_ID, gameweek=3)

    await service.analyze_gameweek(entry_id=ENTRY_ID)
    second_snapshot = store.get_snapshot(entry_id=ENTRY_ID, gameweek=3)

    assert first_snapshot == second_snapshot


# --- evaluate_gameweek orchestration ---


@pytest.mark.asyncio
async def test_evaluate_gameweek_reports_not_completed_for_an_unfinished_gameweek() -> None:
    bootstrap = make_bootstrap([make_gameweek(3, finished=False, is_current=True)])
    client = FakeFPLClient(bootstrap, PICKS)
    service = FPLDecisionService(client=client, snapshot_store=SnapshotStore(":memory:"))  # type: ignore[arg-type]

    evaluation = await service.evaluate_gameweek(entry_id=ENTRY_ID)

    assert evaluation.status == STATUS_NOT_COMPLETED
    assert client.get_event_live_calls == []


@pytest.mark.asyncio
async def test_evaluate_gameweek_reports_no_snapshot_for_a_finished_gameweek_with_none_recorded() -> None:
    bootstrap = make_bootstrap([make_gameweek(3, finished=True)])
    client = FakeFPLClient(bootstrap, PICKS, live_by_gameweek={3: make_live()})
    service = FPLDecisionService(client=client, snapshot_store=SnapshotStore(":memory:"))  # type: ignore[arg-type]

    evaluation = await service.evaluate_gameweek(entry_id=ENTRY_ID, gameweek=3)

    assert evaluation.status == STATUS_NO_SNAPSHOT
    assert client.get_event_live_calls == []


@pytest.mark.asyncio
async def test_evaluate_gameweek_returns_a_real_evaluation_once_snapshot_and_results_both_exist() -> None:
    store = SnapshotStore(":memory:")

    unfinished_bootstrap = make_bootstrap([make_gameweek(3, finished=False, is_current=True)])
    client = FakeFPLClient(unfinished_bootstrap, PICKS)
    service = FPLDecisionService(client=client, snapshot_store=store)  # type: ignore[arg-type]
    decision = await service.analyze_gameweek(entry_id=ENTRY_ID)

    live_scores = {player.player_id: 5 for player in decision.starting_xi}
    live_scores.update({player.player_id: 1 for player in decision.bench})

    finished_bootstrap = make_bootstrap([make_gameweek(3, finished=True)])
    client_after = FakeFPLClient(
        finished_bootstrap,
        PICKS,
        live_by_gameweek={3: make_live(*live_scores.items())},
    )
    service_after = FPLDecisionService(client=client_after, snapshot_store=store)  # type: ignore[arg-type]

    evaluation = await service_after.evaluate_gameweek(entry_id=ENTRY_ID, gameweek=3)

    assert evaluation.status == STATUS_EVALUATED
    assert evaluation.captain is not None
    assert client_after.get_event_live_calls == [3]


@pytest.mark.asyncio
async def test_evaluate_gameweek_evaluates_every_player_in_the_recorded_squad() -> None:
    """The full squad recorded in the snapshot - starters and bench -
    must each come back with expected, actual, and prediction error."""
    store = SnapshotStore(":memory:")

    unfinished = make_bootstrap([make_gameweek(3, finished=False, is_current=True)])
    service = FPLDecisionService(  # type: ignore[arg-type]
        client=FakeFPLClient(unfinished, PICKS),
        snapshot_store=store,
    )
    decision = await service.analyze_gameweek(entry_id=ENTRY_ID)

    squad = [*decision.starting_xi, *decision.bench]
    live_scores = {player.player_id: 4 for player in squad}

    finished = make_bootstrap([make_gameweek(3, finished=True)])
    service_after = FPLDecisionService(  # type: ignore[arg-type]
        client=FakeFPLClient(finished, PICKS, live_by_gameweek={3: make_live(*live_scores.items())}),
        snapshot_store=store,
    )

    evaluation = await service_after.evaluate_gameweek(entry_id=ENTRY_ID, gameweek=3)

    evaluated_ids = [
        player.player_id
        for player in [*evaluation.starting_xi_players, *evaluation.bench_players]
    ]
    assert sorted(evaluated_ids) == sorted(player.player_id for player in squad)
    assert len(evaluation.starting_xi_players) == len(decision.starting_xi)
    assert len(evaluation.bench_players) == len(decision.bench)

    for player in evaluation.starting_xi_players:
        assert player.actual_points == 4
        assert player.prediction_error == round(4 - player.expected_points, 2)


@pytest.mark.asyncio
async def test_evaluation_expected_points_come_from_the_snapshot_not_todays_data() -> None:
    """The snapshot is the historical record: even when the engine
    would now project something different, the evaluation must measure
    the prediction that was actually made."""
    store = SnapshotStore(":memory:")

    unfinished = make_bootstrap([make_gameweek(3, finished=False, is_current=True)])
    service = FPLDecisionService(  # type: ignore[arg-type]
        client=FakeFPLClient(unfinished, PICKS),
        snapshot_store=store,
    )
    await service.analyze_gameweek(entry_id=ENTRY_ID)

    snapshot = store.get_snapshot(entry_id=ENTRY_ID, gameweek=3)
    assert snapshot is not None
    snapshot_expected = {p.player_id: p.expected_points for p in snapshot.starting_xi}

    # Rebuild the world with players who now score far more per game,
    # so a recomputed projection would differ from the recorded one.
    from fpl_agent.data.models import Player

    finished = make_bootstrap([make_gameweek(3, finished=True)])
    inflated = [
        Player.model_validate(
            {
                **make_player(p.id, p.element_type, team_id=p.team),
                "points_per_game": "99.0",
                "total_points": 9999,
                "form": "99.0",
            },
        )
        for p in finished.elements
    ]
    finished_inflated = BootstrapData(
        elements=inflated,
        teams=finished.teams,
        events=finished.events,
    )

    live = make_live(*{p.player_id: 5 for p in snapshot.starting_xi}.items())
    service_after = FPLDecisionService(  # type: ignore[arg-type]
        client=FakeFPLClient(finished_inflated, PICKS, live_by_gameweek={3: live}),
        snapshot_store=store,
    )

    evaluation = await service_after.evaluate_gameweek(entry_id=ENTRY_ID, gameweek=3)

    for player in evaluation.starting_xi_players:
        assert player.expected_points == snapshot_expected[player.player_id]
