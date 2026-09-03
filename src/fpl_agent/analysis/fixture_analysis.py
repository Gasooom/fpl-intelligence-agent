from __future__ import annotations

from dataclasses import dataclass

from fpl_agent.data.models import Fixture


@dataclass(frozen=True)
class TeamFixtureDifficulty:
    """Upcoming fixture difficulty for a team."""

    team_id: int
    fixture_id: int
    gameweek: int | None
    opponent_team_id: int
    is_home: bool
    difficulty: int


def fixture_difficulty(
    fixture: Fixture,
    team_id: int,
) -> TeamFixtureDifficulty:
    """Return the fixture difficulty from a team's perspective."""
    if team_id == fixture.team_h:
        return TeamFixtureDifficulty(
            team_id=team_id,
            fixture_id=fixture.id,
            gameweek=fixture.event,
            opponent_team_id=fixture.team_a,
            is_home=True,
            difficulty=fixture.difficulty,
        )

    if team_id == fixture.team_a:
        return TeamFixtureDifficulty(
            team_id=team_id,
            fixture_id=fixture.id,
            gameweek=fixture.event,
            opponent_team_id=fixture.team_h,
            is_home=False,
            difficulty=fixture.difficulty,
        )

    raise ValueError(
        f"Team {team_id} is not involved in fixture {fixture.id}"
    )


def upcoming_fixtures_for_team(
    fixtures: list[Fixture],
    team_id: int,
) -> list[TeamFixtureDifficulty]:
    """Return unfinished fixtures for a team ordered by gameweek."""
    upcoming = [
        fixture_difficulty(fixture, team_id)
        for fixture in fixtures
        if not fixture.finished
        and (fixture.team_h == team_id or fixture.team_a == team_id)
    ]

    return sorted(
        upcoming,
        key=lambda fixture: (
            fixture.gameweek is None,
            fixture.gameweek if fixture.gameweek is not None else 0,
        ),
    )


def average_fixture_difficulty(
    fixtures: list[Fixture],
    team_id: int,
    limit: int | None = None,
) -> float:
    """Calculate average upcoming fixture difficulty for a team."""
    upcoming = upcoming_fixtures_for_team(fixtures, team_id)

    if limit is not None:
        upcoming = upcoming[:limit]

    if not upcoming:
        return 0.0

    return sum(item.difficulty for item in upcoming) / len(upcoming)