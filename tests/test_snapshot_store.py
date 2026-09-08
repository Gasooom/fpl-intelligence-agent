from __future__ import annotations

from pathlib import Path

import pytest

from fpl_agent.decisions.snapshot import DecisionSnapshot, SnapshotPlayer, SnapshotTransfer
from fpl_agent.persistence.snapshot_store import (
    DB_PATH_ENV_VAR,
    DEFAULT_DB_PATH,
    SnapshotStore,
    resolve_default_db_path,
)


def make_snapshot(
    entry_id: int = 8731757,
    gameweek: int = 3,
    best_transfer: SnapshotTransfer | None = None,
) -> DecisionSnapshot:
    return DecisionSnapshot(
        entry_id=entry_id,
        gameweek=gameweek,
        generated_at="2026-08-10T09:00:00+00:00",
        decision_engine_version="v1",
        confidence="Low",
        captain_player_id=1,
        captain_web_name="Cherki",
        vice_captain_player_id=2,
        vice_captain_web_name="Haaland",
        starting_xi=[
            SnapshotPlayer(
                player_id=1, web_name="Cherki", position_type=3, expected_points=10.31,
            ),
            SnapshotPlayer(
                player_id=2, web_name="Haaland", position_type=4, expected_points=8.25,
            ),
        ],
        bench=[
            SnapshotPlayer(
                player_id=3, web_name="Kinsky", position_type=1, expected_points=3.0,
            ),
        ],
        best_transfer=best_transfer,
    )


def test_get_snapshot_returns_none_when_nothing_is_stored() -> None:
    store = SnapshotStore(":memory:")

    assert store.get_snapshot(entry_id=8731757, gameweek=3) is None


def test_save_and_get_snapshot_round_trips_every_field() -> None:
    store = SnapshotStore(":memory:")
    transfer = SnapshotTransfer(
        sell_player_id=20,
        sell_web_name="Neto",
        buy_player_id=21,
        buy_web_name="Gakpo",
        expected_improvement=9.64,
        priority="essential",
    )
    snapshot = make_snapshot(best_transfer=transfer)

    written = store.save_snapshot_if_absent(snapshot)
    retrieved = store.get_snapshot(entry_id=8731757, gameweek=3)

    assert written is True
    assert retrieved == snapshot


def test_save_snapshot_round_trips_a_none_best_transfer() -> None:
    store = SnapshotStore(":memory:")
    snapshot = make_snapshot(best_transfer=None)

    store.save_snapshot_if_absent(snapshot)
    retrieved = store.get_snapshot(entry_id=8731757, gameweek=3)

    assert retrieved is not None
    assert retrieved.best_transfer is None


def test_save_snapshot_if_absent_never_overwrites_an_existing_snapshot() -> None:
    store = SnapshotStore(":memory:")
    original = make_snapshot(gameweek=3)
    later_attempt = DecisionSnapshot(
        entry_id=original.entry_id,
        gameweek=3,
        generated_at="2026-08-12T09:00:00+00:00",
        decision_engine_version="v2",
        confidence="High",
        captain_player_id=99,
        captain_web_name="Someone Else",
        vice_captain_player_id=98,
        vice_captain_web_name="Another Player",
        starting_xi=[],
        bench=[],
        best_transfer=None,
    )

    first_write = store.save_snapshot_if_absent(original)
    second_write = store.save_snapshot_if_absent(later_attempt)
    retrieved = store.get_snapshot(entry_id=original.entry_id, gameweek=3)

    assert first_write is True
    assert second_write is False
    assert retrieved == original
    assert retrieved is not None
    assert retrieved.captain_player_id == 1


def test_snapshots_are_stored_independently_per_gameweek() -> None:
    store = SnapshotStore(":memory:")
    gw3 = make_snapshot(gameweek=3)
    gw4 = make_snapshot(gameweek=4)

    store.save_snapshot_if_absent(gw3)
    store.save_snapshot_if_absent(gw4)

    assert store.get_snapshot(entry_id=8731757, gameweek=3) == gw3
    assert store.get_snapshot(entry_id=8731757, gameweek=4) == gw4


def test_snapshots_are_stored_independently_per_entry() -> None:
    store = SnapshotStore(":memory:")
    entry_a = make_snapshot(entry_id=111)
    entry_b = make_snapshot(entry_id=222)

    store.save_snapshot_if_absent(entry_a)
    store.save_snapshot_if_absent(entry_b)

    assert store.get_snapshot(entry_id=111, gameweek=3) == entry_a
    assert store.get_snapshot(entry_id=222, gameweek=3) == entry_b


def test_schema_survives_being_initialized_twice_against_the_same_file(tmp_path: Path) -> None:
    """A second SnapshotStore instance against the same file (as would
    happen across two application restarts) must see prior data, not
    fail because the table already exists."""
    db_path = tmp_path / "decisions.db"
    snapshot = make_snapshot()

    first_store = SnapshotStore(db_path)
    first_store.save_snapshot_if_absent(snapshot)

    second_store = SnapshotStore(db_path)
    retrieved = second_store.get_snapshot(entry_id=8731757, gameweek=3)

    assert retrieved == snapshot


def test_default_db_path_is_used_when_the_environment_is_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(DB_PATH_ENV_VAR, raising=False)

    assert resolve_default_db_path() == DEFAULT_DB_PATH


def test_environment_overrides_the_default_db_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Containers point this at a mounted volume so write-once
    snapshots outlive the container's writable layer."""
    monkeypatch.setenv(DB_PATH_ENV_VAR, "/data/decisions.db")

    assert resolve_default_db_path() == "/data/decisions.db"


def test_empty_environment_value_falls_back_to_the_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unset variable and one set to the empty string arrive
    identically in most container runtimes, so both must fall back
    rather than trying to open a database at "" ."""
    monkeypatch.setenv(DB_PATH_ENV_VAR, "")

    assert resolve_default_db_path() == DEFAULT_DB_PATH


def test_store_without_an_explicit_path_writes_to_the_configured_location(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configured = tmp_path / "configured.db"
    monkeypatch.setenv(DB_PATH_ENV_VAR, str(configured))
    snapshot = make_snapshot()

    SnapshotStore().save_snapshot_if_absent(snapshot)

    assert configured.exists()
    assert SnapshotStore().get_snapshot(entry_id=8731757, gameweek=3) == snapshot


def test_list_snapshot_gameweeks_returns_empty_when_nothing_is_stored() -> None:
    store = SnapshotStore(":memory:")

    assert store.list_snapshot_gameweeks(entry_id=8731757) == []


def test_list_snapshot_gameweeks_returns_newest_first() -> None:
    store = SnapshotStore(":memory:")
    store.save_snapshot_if_absent(make_snapshot(gameweek=3))
    store.save_snapshot_if_absent(make_snapshot(gameweek=5))
    store.save_snapshot_if_absent(make_snapshot(gameweek=4))

    assert store.list_snapshot_gameweeks(entry_id=8731757) == [5, 4, 3]


def test_list_snapshot_gameweeks_is_scoped_to_one_entry() -> None:
    store = SnapshotStore(":memory:")
    store.save_snapshot_if_absent(make_snapshot(entry_id=111, gameweek=3))
    store.save_snapshot_if_absent(make_snapshot(entry_id=222, gameweek=4))
    store.save_snapshot_if_absent(make_snapshot(entry_id=222, gameweek=5))

    assert store.list_snapshot_gameweeks(entry_id=111) == [3]
    assert store.list_snapshot_gameweeks(entry_id=222) == [5, 4]


def test_explicit_path_wins_over_the_environment(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The test suite and any caller passing a path must stay immune to
    ambient configuration - otherwise a set FPL_DB_PATH would silently
    redirect tests that pass `:memory:`."""
    ignored = tmp_path / "ignored.db"
    explicit = tmp_path / "explicit.db"
    monkeypatch.setenv(DB_PATH_ENV_VAR, str(ignored))

    SnapshotStore(explicit).save_snapshot_if_absent(make_snapshot())

    assert explicit.exists()
    assert not ignored.exists()
