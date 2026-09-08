from __future__ import annotations

from fpl_agent.data.client import FPLClient
from fpl_agent.data.models import Fixture, Gameweek
from fpl_agent.decisions.evaluation import (
    GameweekEvaluation,
    build_gameweek_evaluation,
    build_missing_snapshot_evaluation,
    build_not_completed_evaluation,
)
from fpl_agent.decisions.gameweek_decision import (
    GameweekDecision,
    build_gameweek_decision,
)
from fpl_agent.decisions.outcomes import build_actual_outcomes, index_actual_outcomes
from fpl_agent.decisions.snapshot import build_decision_snapshot
from fpl_agent.decisions.squad_analysis import (
    SquadDecision,
    build_squad_decision,
)
from fpl_agent.persistence.snapshot_store import SnapshotStore


class FPLDecisionService:
    """Application service for deterministic FPL squad decisions."""

    def __init__(
        self,
        client: FPLClient | None = None,
        snapshot_store: SnapshotStore | None = None,
    ) -> None:
        self.client = client or FPLClient()
        self.snapshot_store = snapshot_store or SnapshotStore()

    async def analyze_squad(
        self,
        entry_id: int,
        gameweek: int | None = None,
    ) -> SquadDecision:
        """Fetch FPL data and produce a deterministic squad decision.

        Kept for callers that only need starting XI/bench/captaincy.
        Prefer analyze_gameweek for the full gameweek action plan,
        including transfer intelligence.
        """
        bootstrap = await self.client.get_bootstrap_static()

        target_gameweek = self._resolve_gameweek(
            bootstrap.events,
            gameweek,
        )

        entry = await self.client.get_entry(entry_id)

        picks_response = await self.client.get_entry_picks(
            entry_id=entry.id,
            gameweek=target_gameweek,
        )

        fixtures = await self.client.get_fixtures()

        return build_squad_decision(
            players=bootstrap.elements,
            teams=bootstrap.teams,
            fixtures=fixtures,
            picks=picks_response.picks,
        )

    async def analyze_gameweek(
        self,
        entry_id: int,
        gameweek: int | None = None,
        free_transfers_available: int | None = None,
    ) -> GameweekDecision:
        """Fetch FPL data and produce the unified deterministic gameweek decision.

        Combines the squad decision (starting XI, bench, captaincy,
        must-play) with deterministic sell/buy transfer intelligence.

        `free_transfers_available` has no public FPL API source (see
        transfer_analysis.build_transfer_pairs) - when the caller
        supplies it, transfer priority reflects real hit-cost economics;
        when omitted, it falls back to the pre-existing
        selection-score-based classification, unchanged.
        """
        bootstrap = await self.client.get_bootstrap_static()

        target_gameweek = self._resolve_gameweek(
            bootstrap.events,
            gameweek,
        )

        # A future gameweek has no squad of its own yet, so the squad
        # being planned with is the manager's latest available one. Only
        # that gameweek's picks are ever requested - asking FPL for a
        # future gameweek's picks answers 404, which is what the
        # "squad ... was not found" failure was.
        source_picks_gameweek = self._resolve_source_picks_gameweek(
            bootstrap.events,
            target_gameweek,
        )

        entry = await self.client.get_entry(entry_id)

        picks_response = await self.client.get_entry_picks(
            entry_id=entry.id,
            gameweek=source_picks_gameweek,
        )

        fixtures = await self.client.get_fixtures()

        decision = build_gameweek_decision(
            players=bootstrap.elements,
            teams=bootstrap.teams,
            fixtures=self._fixtures_for_projection(
                fixtures,
                target_gameweek=target_gameweek,
                source_picks_gameweek=source_picks_gameweek,
            ),
            picks=picks_response.picks,
            gameweek=target_gameweek,
            source_picks_gameweek=source_picks_gameweek,
            entry_history=picks_response.entry_history,
            free_transfers_available=free_transfers_available,
        )

        if not self._is_gameweek_finished(bootstrap.events, target_gameweek):
            # Snapshot only a not-yet-played gameweek: recomputing a
            # decision for one that has already finished would use
            # today's bootstrap data (updated form, price, points),
            # not what was true before that gameweek's deadline, so it
            # would not be a faithful record of "what was recommended
            # at the time" - see decisions/snapshot.py.
            self.snapshot_store.save_snapshot_if_absent(
                build_decision_snapshot(entry_id, decision),
            )

        return decision

    async def evaluate_gameweek(
        self,
        entry_id: int,
        gameweek: int | None = None,
    ) -> GameweekEvaluation:
        """Compare a recorded decision snapshot against real gameweek outcomes.

        Returns an honest non-evaluated state - never a fabricated
        result - when the gameweek has not finished yet, or when no
        decision snapshot was recorded for it.
        """
        bootstrap = await self.client.get_bootstrap_static()

        target_gameweek = self._resolve_gameweek(
            bootstrap.events,
            gameweek,
        )

        if not self._is_gameweek_finished(bootstrap.events, target_gameweek):
            return build_not_completed_evaluation(entry_id, target_gameweek)

        snapshot = self.snapshot_store.get_snapshot(entry_id, target_gameweek)

        if snapshot is None:
            return build_missing_snapshot_evaluation(entry_id, target_gameweek)

        live = await self.client.get_event_live(target_gameweek)
        outcomes = index_actual_outcomes(build_actual_outcomes(target_gameweek, live))

        return build_gameweek_evaluation(snapshot, outcomes)

    async def evaluate_latest_completed_gameweek(
        self,
        entry_id: int,
    ) -> GameweekEvaluation | None:
        """Evaluate the most recent completed gameweek with a recorded snapshot.

        Lets the dashboard showcase evaluation even while the current
        gameweek is still `not_completed`, without ever fabricating a
        result: this looks only at gameweeks strictly before the current
        (or next, if none is current) one, and only at those with both a
        recorded snapshot and finished results. It reuses the exact same
        snapshot -> actual outcomes -> build_gameweek_evaluation pipeline
        as evaluate_gameweek; only the choice of gameweek differs.

        Returns None - never a placeholder - when no such gameweek
        exists yet, e.g. before the first completed decision cycle.
        """
        bootstrap = await self.client.get_bootstrap_static()

        try:
            reference_gameweek: int | None = self._resolve_gameweek(
                bootstrap.events,
                None,
            )
        except ValueError:
            # No current or next gameweek is known (e.g. between
            # seasons) - fall back to considering every finished
            # gameweek rather than refusing to show any history.
            reference_gameweek = None

        finished_gameweeks = {event.id for event in bootstrap.events if event.finished}

        candidate_gameweek = next(
            (
                gw
                for gw in self.snapshot_store.list_snapshot_gameweeks(entry_id)
                if gw in finished_gameweeks
                and (reference_gameweek is None or gw < reference_gameweek)
            ),
            None,
        )

        if candidate_gameweek is None:
            return None

        snapshot = self.snapshot_store.get_snapshot(entry_id, candidate_gameweek)

        if snapshot is None:
            return None

        live = await self.client.get_event_live(candidate_gameweek)
        outcomes = index_actual_outcomes(build_actual_outcomes(candidate_gameweek, live))

        return build_gameweek_evaluation(snapshot, outcomes)

    @staticmethod
    def _resolve_source_picks_gameweek(
        events: list[Gameweek],
        target_gameweek: int,
    ) -> int:
        """Return the latest gameweek at or before the target whose squad exists.

        A manager's picks only come into existence once a gameweek's
        deadline has passed, which bootstrap reports as that gameweek
        being finished or current. Predicting a gameweek beyond that
        therefore plans with the squad the manager actually has now -
        never an invented future squad, and never a picks request FPL
        would answer 404 for.

        Deliberately independent of `_resolve_gameweek`, which decides
        *what* to predict and is unchanged: this only decides which
        real squad that prediction is built from.

        Falls back to the target gameweek when no gameweek has started
        yet (pre-season), so the caller still gets FPL's own honest
        "not found" for the gameweek they actually asked about rather
        than a silently different one.
        """
        started = [
            event.id
            for event in events
            if event.id <= target_gameweek and (event.finished or event.is_current)
        ]

        return max(started) if started else target_gameweek

    @staticmethod
    def _fixtures_for_projection(
        fixtures: list[Fixture],
        target_gameweek: int,
        source_picks_gameweek: int,
    ) -> list[Fixture]:
        """Scope the fixture list to the gameweek actually being predicted.

        Only applies to a genuine forward prediction. The projection
        layer uses a team's *next unfinished* fixture, which for a
        target beyond the current gameweek would otherwise be a
        still-unplayed fixture from the gameweek in progress rather
        than the one being predicted.

        Fixtures at or after the target are kept rather than only the
        target's own, so a team with no fixture that gameweek falls
        back to its next real one instead of registering as "no fixture
        found" - which the projection scale reads as the most
        favourable fixture possible, and would overstate a player who
        is not even playing.
        """
        if target_gameweek <= source_picks_gameweek:
            return fixtures

        return [
            fixture
            for fixture in fixtures
            if fixture.event is None or fixture.event >= target_gameweek
        ]

    @staticmethod
    def _is_gameweek_finished(events: list[Gameweek], gameweek: int) -> bool:
        """Return whether the given gameweek has finished, per bootstrap data."""
        return any(event.id == gameweek and event.finished for event in events)

    @staticmethod
    def _resolve_gameweek(
        events: list[Gameweek],
        requested_gameweek: int | None,
    ) -> int:
        """Resolve the requested gameweek or the current FPL gameweek."""
        if requested_gameweek is not None:
            if requested_gameweek < 1:
                raise ValueError(
                    "Gameweek must be greater than zero.",
                )

            if not any(
                event.id == requested_gameweek
                for event in events
            ):
                raise ValueError(
                    f"Gameweek {requested_gameweek} was not found.",
                )

            return requested_gameweek

        current_events = [
            event
            for event in events
            if event.is_current
        ]

        if current_events:
            return current_events[0].id

        next_events = [
            event
            for event in events
            if event.is_next
        ]

        if next_events:
            return next_events[0].id

        raise ValueError(
            "Unable to determine the current or next gameweek.",
        )