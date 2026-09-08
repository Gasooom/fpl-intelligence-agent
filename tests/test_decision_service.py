from __future__ import annotations

import pytest

from fpl_agent.data.errors import FPLResourceNotFoundError
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
        fixtures: list[Fixture] | None = None,
        picks_available_for: set[int] | None = None,
    ) -> None:
        self.bootstrap = bootstrap
        self.picks = picks
        self.live_by_gameweek = live_by_gameweek or {}
        self.fixtures = fixtures or []
        # None means "every gameweek has picks", which is how the real
        # API behaves for any gameweek whose deadline has passed and
        # what the pre-existing tests assume. Supplying a set models
        # FPL's real 404 for a gameweek the manager has not picked yet.
        self.picks_available_for = picks_available_for
        self.get_event_live_calls: list[int] = []
        self.get_entry_picks_calls: list[int] = []

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
        self.get_entry_picks_calls.append(gameweek)

        if (
            self.picks_available_for is not None
            and gameweek not in self.picks_available_for
        ):
            raise FPLResourceNotFoundError(
                f"The squad for FPL entry {entry_id} in gameweek {gameweek} "
                "was not found in the official FPL API.",
            )

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
        return self.fixtures

    async def get_event_live(self, gameweek: int) -> EventLiveResponse:
        self.get_event_live_calls.append(gameweek)
        return self.live_by_gameweek[gameweek]


def make_fixtures(
    gameweek: int,
    difficulty: int,
    finished: bool = False,
) -> list[Fixture]:
    """One fixture per pair of teams for a gameweek, at a fixed difficulty.

    Both sides carry the same difficulty so a player's projected
    fixture difficulty is the same regardless of which side his team
    is on - keeping assertions about *which gameweek* was projected
    free of home/away noise. Covers every team the squad fixtures use.
    """
    return [
        Fixture(
            id=gameweek * 100 + home_team,
            event=gameweek,
            team_h=home_team,
            team_a=home_team + 1,
            finished=finished,
            team_h_difficulty=difficulty,
            team_a_difficulty=difficulty,
        )
        for home_team in range(1, 20, 2)
    ]


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


# --- Predicting an upcoming gameweek from the latest available squad ---
#
# The manager has picks for gameweek 3 (current, in progress) but none
# for gameweek 4, which is exactly what FPL returns before a deadline.


def make_upcoming_client(
    picks_available_for: set[int] | None = None,
    current_gameweek_difficulty: int = 5,
    target_gameweek_difficulty: int = 2,
) -> FakeFPLClient:
    """A world where GW3 is current/unplayed and GW4 is next.

    The two gameweeks carry deliberately different fixture difficulty so
    a projection can be traced back to the gameweek it actually used.
    GW3's fixtures are unfinished, so a prediction that ignored the
    target gameweek would still find them first.
    """
    bootstrap = make_bootstrap(
        [
            make_gameweek(3, finished=False, is_current=True),
            make_gameweek(4, finished=False),
        ],
    )

    return FakeFPLClient(
        bootstrap,
        PICKS,
        fixtures=[
            *make_fixtures(3, difficulty=current_gameweek_difficulty),
            *make_fixtures(4, difficulty=target_gameweek_difficulty),
        ],
        picks_available_for=(
            {3} if picks_available_for is None else picks_available_for
        ),
    )


@pytest.mark.asyncio
async def test_current_gameweek_prediction_still_uses_its_own_picks() -> None:
    client = make_upcoming_client()
    service = FPLDecisionService(client=client, snapshot_store=SnapshotStore(":memory:"))  # type: ignore[arg-type]

    decision = await service.analyze_gameweek(entry_id=ENTRY_ID)

    assert decision.gameweek == 3
    assert decision.source_picks_gameweek == 3
    assert decision.is_future_gameweek is False
    assert client.get_entry_picks_calls == [3]


@pytest.mark.asyncio
async def test_future_gameweek_uses_the_latest_available_entry_picks() -> None:
    client = make_upcoming_client()
    service = FPLDecisionService(client=client, snapshot_store=SnapshotStore(":memory:"))  # type: ignore[arg-type]

    decision = await service.analyze_gameweek(entry_id=ENTRY_ID, gameweek=4)

    assert decision.gameweek == 4
    assert decision.source_picks_gameweek == 3
    assert client.get_entry_picks_calls == [3]


@pytest.mark.asyncio
async def test_future_gameweek_never_requests_picks_that_do_not_exist_yet() -> None:
    """The exact failure the dashboard hit: asking FPL for a future
    gameweek's squad answers 404, so it must never be asked for."""
    client = make_upcoming_client()
    service = FPLDecisionService(client=client, snapshot_store=SnapshotStore(":memory:"))  # type: ignore[arg-type]

    await service.analyze_gameweek(entry_id=ENTRY_ID, gameweek=4)

    assert 4 not in client.get_entry_picks_calls


@pytest.mark.asyncio
async def test_gw3_to_gw4_prediction_no_longer_fails_with_squad_not_found() -> None:
    """Regression for the reported scenario: selecting gameweek 4 while
    gameweek 3 is the latest with a squad."""
    client = make_upcoming_client()
    service = FPLDecisionService(client=client, snapshot_store=SnapshotStore(":memory:"))  # type: ignore[arg-type]

    decision = await service.analyze_gameweek(entry_id=ENTRY_ID, gameweek=4)

    assert len(decision.starting_xi) == 11
    assert decision.projected_gameweek_points > 0


@pytest.mark.asyncio
async def test_future_gameweek_projection_uses_target_gameweek_fixtures() -> None:
    """GW4's fixtures decide a GW4 projection - never the still-unplayed
    GW3 fixtures, which the projection layer would otherwise reach
    first as the team's next unfinished fixture."""
    client = make_upcoming_client(
        current_gameweek_difficulty=5,
        target_gameweek_difficulty=2,
    )
    service = FPLDecisionService(client=client, snapshot_store=SnapshotStore(":memory:"))  # type: ignore[arg-type]

    upcoming = await service.analyze_gameweek(entry_id=ENTRY_ID, gameweek=4)
    current = await service.analyze_gameweek(entry_id=ENTRY_ID, gameweek=3)

    assert {player.fixture_difficulty for player in upcoming.starting_xi} == {2.0}
    assert {player.fixture_difficulty for player in current.starting_xi} == {5.0}


@pytest.mark.asyncio
async def test_future_gameweek_squad_contains_only_real_picked_players() -> None:
    """Nothing is invented: every player planned for the upcoming
    gameweek comes from the squad the manager actually owns."""
    client = make_upcoming_client()
    service = FPLDecisionService(client=client, snapshot_store=SnapshotStore(":memory:"))  # type: ignore[arg-type]

    decision = await service.analyze_gameweek(entry_id=ENTRY_ID, gameweek=4)

    squad_ids = {
        player.player_id
        for player in [*decision.starting_xi, *decision.bench]
    }
    assert squad_ids <= set(PICKS)


@pytest.mark.asyncio
async def test_explicit_past_gameweek_still_uses_that_gameweeks_own_picks() -> None:
    bootstrap = make_bootstrap(
        [
            make_gameweek(2, finished=True),
            make_gameweek(3, finished=False, is_current=True),
        ],
    )
    client = FakeFPLClient(bootstrap, PICKS, picks_available_for={2, 3})
    service = FPLDecisionService(client=client, snapshot_store=SnapshotStore(":memory:"))  # type: ignore[arg-type]

    decision = await service.analyze_gameweek(entry_id=ENTRY_ID, gameweek=2)

    assert decision.gameweek == 2
    assert decision.source_picks_gameweek == 2
    assert decision.is_future_gameweek is False
    assert client.get_entry_picks_calls == [2]


@pytest.mark.asyncio
async def test_a_far_future_gameweek_still_plans_from_the_current_squad() -> None:
    bootstrap = make_bootstrap(
        [
            make_gameweek(3, finished=False, is_current=True),
            make_gameweek(4, finished=False),
            make_gameweek(5, finished=False),
        ],
    )
    client = FakeFPLClient(bootstrap, PICKS, picks_available_for={3})
    service = FPLDecisionService(client=client, snapshot_store=SnapshotStore(":memory:"))  # type: ignore[arg-type]

    decision = await service.analyze_gameweek(entry_id=ENTRY_ID, gameweek=5)

    assert decision.gameweek == 5
    assert decision.source_picks_gameweek == 3
    assert decision.is_future_gameweek is True
    assert client.get_entry_picks_calls == [3]


@pytest.mark.asyncio
async def test_predicting_an_upcoming_gameweek_records_a_snapshot_for_that_gameweek() -> None:
    """A prediction made before the deadline is a real pre-gameweek
    decision, so it becomes evaluable later under its own gameweek."""
    store = SnapshotStore(":memory:")
    client = make_upcoming_client()
    service = FPLDecisionService(client=client, snapshot_store=store)  # type: ignore[arg-type]

    await service.analyze_gameweek(entry_id=ENTRY_ID, gameweek=4)

    snapshot = store.get_snapshot(entry_id=ENTRY_ID, gameweek=4)
    assert snapshot is not None
    assert snapshot.gameweek == 4


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
async def test_evaluation_reads_the_snapshot_and_never_refetches_entry_picks() -> None:
    """Historical evaluation stays snapshot -> actual outcomes. It must
    not touch the picks endpoint, whose squad has moved on since."""
    store = SnapshotStore(":memory:")

    unfinished = make_bootstrap([make_gameweek(3, finished=False, is_current=True)])
    seed_service = FPLDecisionService(  # type: ignore[arg-type]
        client=FakeFPLClient(unfinished, PICKS),
        snapshot_store=store,
    )
    decision = await seed_service.analyze_gameweek(entry_id=ENTRY_ID, gameweek=3)

    live_scores = {player.player_id: 5 for player in decision.starting_xi}
    live_scores.update({player.player_id: 1 for player in decision.bench})

    finished = make_bootstrap([make_gameweek(3, finished=True)])
    client_after = FakeFPLClient(
        finished,
        PICKS,
        live_by_gameweek={3: make_live(*live_scores.items())},
    )
    service_after = FPLDecisionService(client=client_after, snapshot_store=store)  # type: ignore[arg-type]

    evaluation = await service_after.evaluate_gameweek(entry_id=ENTRY_ID, gameweek=3)

    assert evaluation.status == STATUS_EVALUATED
    assert client_after.get_entry_picks_calls == []


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


# --- evaluate_latest_completed_gameweek orchestration ---


@pytest.mark.asyncio
async def test_latest_completed_evaluation_picks_the_most_recent_evaluable_gameweek() -> None:
    """Snapshots exist for gameweeks 3 and 4, both now finished, with
    gameweek 5 the current (unfinished) one - the latest completed
    evaluation must be gameweek 4, not 3, and must not fetch live
    results for any other gameweek."""
    store = SnapshotStore(":memory:")

    for gw in (3, 4):
        unfinished = make_bootstrap([make_gameweek(gw, finished=False, is_current=True)])
        service = FPLDecisionService(
            client=FakeFPLClient(unfinished, PICKS),  # type: ignore[arg-type]
            snapshot_store=store,
        )
        await service.analyze_gameweek(entry_id=ENTRY_ID, gameweek=gw)

    now_bootstrap = make_bootstrap(
        [
            make_gameweek(3, finished=True),
            make_gameweek(4, finished=True),
            make_gameweek(5, finished=False, is_current=True),
        ],
    )
    client = FakeFPLClient(
        now_bootstrap,
        PICKS,
        live_by_gameweek={4: make_live(*{player_id: 5 for player_id in PICKS}.items())},
    )
    service = FPLDecisionService(client=client, snapshot_store=store)  # type: ignore[arg-type]

    evaluation = await service.evaluate_latest_completed_gameweek(entry_id=ENTRY_ID)

    assert evaluation is not None
    assert evaluation.gameweek == 4
    assert evaluation.status == STATUS_EVALUATED
    assert client.get_event_live_calls == [4]


@pytest.mark.asyncio
async def test_latest_completed_evaluation_skips_a_finished_gameweek_with_no_snapshot() -> None:
    """Gameweek 4 finished but was never recorded (no snapshot); the
    latest evaluable gameweek must fall back to gameweek 3, never
    reconstructing a decision for 4 from today's data."""
    store = SnapshotStore(":memory:")
    unfinished = make_bootstrap([make_gameweek(3, finished=False, is_current=True)])
    seed_service = FPLDecisionService(
        client=FakeFPLClient(unfinished, PICKS),  # type: ignore[arg-type]
        snapshot_store=store,
    )
    await seed_service.analyze_gameweek(entry_id=ENTRY_ID, gameweek=3)

    now_bootstrap = make_bootstrap(
        [
            make_gameweek(3, finished=True),
            make_gameweek(4, finished=True),
            make_gameweek(5, finished=False, is_current=True),
        ],
    )
    client = FakeFPLClient(
        now_bootstrap,
        PICKS,
        live_by_gameweek={3: make_live(*{player_id: 5 for player_id in PICKS}.items())},
    )
    service = FPLDecisionService(client=client, snapshot_store=store)  # type: ignore[arg-type]

    evaluation = await service.evaluate_latest_completed_gameweek(entry_id=ENTRY_ID)

    assert evaluation is not None
    assert evaluation.gameweek == 3
    assert client.get_event_live_calls == [3]


@pytest.mark.asyncio
async def test_latest_completed_evaluation_is_none_when_current_gameweek_not_completed_and_no_history() -> None:
    """Current gameweek not completed, and there is no historical
    snapshot at all yet - must return None, never a fabricated result."""
    bootstrap = make_bootstrap([make_gameweek(5, finished=False, is_current=True)])
    client = FakeFPLClient(bootstrap, PICKS)
    service = FPLDecisionService(client=client, snapshot_store=SnapshotStore(":memory:"))  # type: ignore[arg-type]

    evaluation = await service.evaluate_latest_completed_gameweek(entry_id=ENTRY_ID)

    assert evaluation is None
    assert client.get_event_live_calls == []


@pytest.mark.asyncio
async def test_latest_completed_evaluation_returns_history_when_current_gameweek_not_completed() -> None:
    """Current gameweek (5) is not completed, but gameweek 3 was
    recorded and has since finished - the dashboard's historical section
    must still have something real to show."""
    store = SnapshotStore(":memory:")
    unfinished = make_bootstrap([make_gameweek(3, finished=False, is_current=True)])
    seed_service = FPLDecisionService(
        client=FakeFPLClient(unfinished, PICKS),  # type: ignore[arg-type]
        snapshot_store=store,
    )
    await seed_service.analyze_gameweek(entry_id=ENTRY_ID, gameweek=3)

    now_bootstrap = make_bootstrap(
        [
            make_gameweek(3, finished=True),
            make_gameweek(5, finished=False, is_current=True),
        ],
    )
    client = FakeFPLClient(
        now_bootstrap,
        PICKS,
        live_by_gameweek={3: make_live(*{player_id: 5 for player_id in PICKS}.items())},
    )
    service = FPLDecisionService(client=client, snapshot_store=store)  # type: ignore[arg-type]

    current_evaluation = await service.evaluate_gameweek(entry_id=ENTRY_ID)
    latest_completed = await service.evaluate_latest_completed_gameweek(entry_id=ENTRY_ID)

    assert current_evaluation.status == STATUS_NOT_COMPLETED
    assert latest_completed is not None
    assert latest_completed.gameweek == 3
    assert latest_completed.status == STATUS_EVALUATED


@pytest.mark.asyncio
async def test_latest_completed_evaluation_never_treats_the_current_gameweeks_own_snapshot_as_history() -> None:
    """A snapshot recorded for the current gameweek itself - even once
    that gameweek finishes and is still reported as current - must not
    be surfaced by the *latest completed* lookup, which only looks at
    gameweeks strictly before the current one."""
    store = SnapshotStore(":memory:")
    unfinished = make_bootstrap([make_gameweek(5, finished=False, is_current=True)])
    seed_service = FPLDecisionService(
        client=FakeFPLClient(unfinished, PICKS),  # type: ignore[arg-type]
        snapshot_store=store,
    )
    await seed_service.analyze_gameweek(entry_id=ENTRY_ID)

    finished_still_current = make_bootstrap(
        [make_gameweek(5, finished=True, is_current=True)],
    )
    client = FakeFPLClient(finished_still_current, PICKS)
    service = FPLDecisionService(client=client, snapshot_store=store)  # type: ignore[arg-type]

    evaluation = await service.evaluate_latest_completed_gameweek(entry_id=ENTRY_ID)

    assert evaluation is None
    assert client.get_event_live_calls == []


@pytest.mark.asyncio
async def test_latest_completed_evaluation_expected_points_come_from_the_snapshot() -> None:
    """Same guarantee as evaluate_gameweek: expected_points on the
    latest-completed path are read verbatim from the recorded snapshot,
    never recomputed from today's bootstrap data."""
    store = SnapshotStore(":memory:")
    unfinished = make_bootstrap([make_gameweek(3, finished=False, is_current=True)])
    seed_service = FPLDecisionService(
        client=FakeFPLClient(unfinished, PICKS),  # type: ignore[arg-type]
        snapshot_store=store,
    )
    await seed_service.analyze_gameweek(entry_id=ENTRY_ID, gameweek=3)
    snapshot = store.get_snapshot(entry_id=ENTRY_ID, gameweek=3)
    assert snapshot is not None
    snapshot_expected = {p.player_id: p.expected_points for p in snapshot.starting_xi}

    now_bootstrap = make_bootstrap(
        [
            make_gameweek(3, finished=True),
            make_gameweek(5, finished=False, is_current=True),
        ],
    )
    live = make_live(*{p.player_id: 5 for p in snapshot.starting_xi}.items())
    client = FakeFPLClient(now_bootstrap, PICKS, live_by_gameweek={3: live})
    service = FPLDecisionService(client=client, snapshot_store=store)  # type: ignore[arg-type]

    evaluation = await service.evaluate_latest_completed_gameweek(entry_id=ENTRY_ID)

    assert evaluation is not None
    for player in evaluation.starting_xi_players:
        assert player.expected_points == snapshot_expected[player.player_id]


# --- Gameweek resolution regression (explicit / current / next unaffected) ---


@pytest.mark.asyncio
async def test_resolution_regression_explicit_gameweek_still_wins_over_current() -> None:
    bootstrap = make_bootstrap(
        [
            make_gameweek(3, finished=True),
            make_gameweek(4, finished=False, is_current=True),
        ],
    )
    client = FakeFPLClient(bootstrap, PICKS, live_by_gameweek={3: make_live()})
    service = FPLDecisionService(client=client, snapshot_store=SnapshotStore(":memory:"))  # type: ignore[arg-type]

    evaluation = await service.evaluate_gameweek(entry_id=ENTRY_ID, gameweek=3)

    assert evaluation.gameweek == 3


@pytest.mark.asyncio
async def test_resolution_regression_defaults_to_current_gameweek() -> None:
    bootstrap = make_bootstrap([make_gameweek(4, finished=False, is_current=True)])
    client = FakeFPLClient(bootstrap, PICKS)
    service = FPLDecisionService(client=client, snapshot_store=SnapshotStore(":memory:"))  # type: ignore[arg-type]

    evaluation = await service.evaluate_gameweek(entry_id=ENTRY_ID)

    assert evaluation.gameweek == 4


@pytest.mark.asyncio
async def test_resolution_regression_falls_back_to_next_gameweek_with_no_current() -> None:
    gw = Gameweek(
        id=6,
        name="Gameweek 6",
        deadline_time="2026-08-10T10:00:00Z",
        finished=False,
        is_previous=False,
        is_current=False,
        is_next=True,
    )
    bootstrap = make_bootstrap([gw])
    client = FakeFPLClient(bootstrap, PICKS)
    service = FPLDecisionService(client=client, snapshot_store=SnapshotStore(":memory:"))  # type: ignore[arg-type]

    evaluation = await service.evaluate_gameweek(entry_id=ENTRY_ID)

    assert evaluation.gameweek == 6
    assert evaluation.status == STATUS_NOT_COMPLETED


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
