from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

from fpl_agent.decisions.snapshot import DecisionSnapshot, SnapshotPlayer, SnapshotTransfer

# A plain local SQLite file is enough for this project's scale - one
# manager, one gameweek, one row - and keeps the dependency footprint
# at zero (sqlite3 is part of the Python standard library). Already
# gitignored (*.db) so it never gets committed.
DEFAULT_DB_PATH = "decisions.db"

# Containers must keep this file on a mounted volume instead of the
# image's writable layer, which is discarded when the container is
# recreated - snapshots are write-once records of what was
# recommended before a deadline, so losing them destroys the
# evaluation history permanently.
DB_PATH_ENV_VAR = "FPL_DB_PATH"


def resolve_default_db_path() -> str:
    """Return the configured SQLite location, or the local default.

    Read at call time rather than import time so that a process which
    sets the variable after this module is imported still gets the
    configured location. An unset or empty value falls back to the
    original local ``decisions.db``, so existing local runs and the
    test suite behave exactly as before.
    """
    return os.environ.get(DB_PATH_ENV_VAR) or DEFAULT_DB_PATH

_SCHEMA = """
CREATE TABLE IF NOT EXISTS decision_snapshots (
    entry_id INTEGER NOT NULL,
    gameweek INTEGER NOT NULL,
    payload TEXT NOT NULL,
    PRIMARY KEY (entry_id, gameweek)
)
"""


def _serialize(snapshot: DecisionSnapshot) -> str:
    best_transfer: dict[str, Any] | None = (
        {
            "sell_player_id": snapshot.best_transfer.sell_player_id,
            "sell_web_name": snapshot.best_transfer.sell_web_name,
            "buy_player_id": snapshot.best_transfer.buy_player_id,
            "buy_web_name": snapshot.best_transfer.buy_web_name,
            "expected_improvement": snapshot.best_transfer.expected_improvement,
            "priority": snapshot.best_transfer.priority,
        }
        if snapshot.best_transfer is not None
        else None
    )

    payload = {
        "entry_id": snapshot.entry_id,
        "gameweek": snapshot.gameweek,
        "generated_at": snapshot.generated_at,
        "decision_engine_version": snapshot.decision_engine_version,
        "confidence": snapshot.confidence,
        "captain_player_id": snapshot.captain_player_id,
        "captain_web_name": snapshot.captain_web_name,
        "vice_captain_player_id": snapshot.vice_captain_player_id,
        "vice_captain_web_name": snapshot.vice_captain_web_name,
        "starting_xi": [
            {
                "player_id": player.player_id,
                "web_name": player.web_name,
                "position_type": player.position_type,
                "expected_points": player.expected_points,
            }
            for player in snapshot.starting_xi
        ],
        "bench": [
            {
                "player_id": player.player_id,
                "web_name": player.web_name,
                "position_type": player.position_type,
                "expected_points": player.expected_points,
            }
            for player in snapshot.bench
        ],
        "best_transfer": best_transfer,
    }

    return json.dumps(payload)


def _deserialize(payload: str) -> DecisionSnapshot:
    data: dict[str, Any] = json.loads(payload)
    best_transfer_data: dict[str, Any] | None = data["best_transfer"]

    return DecisionSnapshot(
        entry_id=data["entry_id"],
        gameweek=data["gameweek"],
        generated_at=data["generated_at"],
        decision_engine_version=data["decision_engine_version"],
        confidence=data["confidence"],
        captain_player_id=data["captain_player_id"],
        captain_web_name=data["captain_web_name"],
        vice_captain_player_id=data["vice_captain_player_id"],
        vice_captain_web_name=data["vice_captain_web_name"],
        starting_xi=[
            SnapshotPlayer(
                player_id=item["player_id"],
                web_name=item["web_name"],
                position_type=item["position_type"],
                expected_points=item["expected_points"],
            )
            for item in data["starting_xi"]
        ],
        bench=[
            SnapshotPlayer(
                player_id=item["player_id"],
                web_name=item["web_name"],
                position_type=item["position_type"],
                expected_points=item["expected_points"],
            )
            for item in data["bench"]
        ],
        best_transfer=(
            SnapshotTransfer(
                sell_player_id=best_transfer_data["sell_player_id"],
                sell_web_name=best_transfer_data["sell_web_name"],
                buy_player_id=best_transfer_data["buy_player_id"],
                buy_web_name=best_transfer_data["buy_web_name"],
                expected_improvement=best_transfer_data["expected_improvement"],
                priority=best_transfer_data["priority"],
            )
            if best_transfer_data is not None
            else None
        ),
    )


class SnapshotStore:
    """SQLite-backed store for deterministic decision snapshots.

    One row per (entry_id, gameweek), written at most once -
    `save_snapshot_if_absent` never overwrites an existing row, so a
    gameweek's original recommendation is permanent once recorded.
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        # An explicit path always wins, so tests passing `:memory:` or
        # a tmp_path are unaffected by the environment; only the
        # unconfigured case consults FPL_DB_PATH.
        resolved_path = resolve_default_db_path() if db_path is None else db_path

        # A single long-lived connection: sqlite3's `:memory:` database
        # is per-connection, so tests that pass `:memory:` need every
        # call on this instance to reuse the same connection rather
        # than opening (and losing) a fresh one each time.
        self._connection = sqlite3.connect(str(resolved_path), check_same_thread=False)
        self._connection.execute(_SCHEMA)
        self._connection.commit()

    def save_snapshot_if_absent(self, snapshot: DecisionSnapshot) -> bool:
        """Insert the snapshot unless one already exists for this entry/gameweek.

        Returns True if a new row was written, False if a snapshot was
        already on record.
        """
        cursor = self._connection.execute(
            "INSERT OR IGNORE INTO decision_snapshots (entry_id, gameweek, payload) "
            "VALUES (?, ?, ?)",
            (snapshot.entry_id, snapshot.gameweek, _serialize(snapshot)),
        )
        self._connection.commit()

        return cursor.rowcount > 0

    def get_snapshot(self, entry_id: int, gameweek: int) -> DecisionSnapshot | None:
        """Return the stored snapshot for this entry/gameweek, if any."""
        cursor = self._connection.execute(
            "SELECT payload FROM decision_snapshots WHERE entry_id = ? AND gameweek = ?",
            (entry_id, gameweek),
        )
        row = cursor.fetchone()

        return _deserialize(row[0]) if row is not None else None

    def list_snapshot_gameweeks(self, entry_id: int) -> list[int]:
        """Return every gameweek with a recorded snapshot for this entry.

        Newest first, so callers looking for the latest evaluable
        gameweek (see FPLDecisionService.evaluate_latest_completed_gameweek)
        can take the first one that also satisfies their own criteria
        (e.g. "finished") without loading every snapshot's full payload.
        """
        cursor = self._connection.execute(
            "SELECT gameweek FROM decision_snapshots WHERE entry_id = ? "
            "ORDER BY gameweek DESC",
            (entry_id,),
        )

        return [row[0] for row in cursor.fetchall()]
