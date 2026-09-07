import pytest

from fpl_agent.data.client import FPLClient
from fpl_agent.data.models import BootstrapData, EventLiveResponse


@pytest.mark.asyncio
async def test_get_bootstrap_static() -> None:
    client = FPLClient()

    data = await client.get_bootstrap_static()

    assert isinstance(data, BootstrapData)
    assert len(data.elements) > 0
    assert len(data.teams) == 20
    assert len(data.events) > 0


@pytest.mark.asyncio
async def test_get_event_live_returns_actual_points_for_a_finished_gameweek() -> None:
    """Gameweek 1 of any Premier League season is always long finished."""
    client = FPLClient()

    data = await client.get_event_live(1)

    assert isinstance(data, EventLiveResponse)
    assert len(data.elements) > 0
    assert all(isinstance(element.stats.total_points, int) for element in data.elements)


def test_player_model() -> None:
    player = {
        "id": 1,
        "first_name": "Test",
        "second_name": "Player",
        "web_name": "Player",
        "team": 1,
        "element_type": 3,
        "now_cost": 50,
        "total_points": 100,
        "minutes": 1000,
        "goals_scored": 10,
        "assists": 5,
        "clean_sheets": 8,
        "goals_conceded": 10,
        "own_goals": 0,
        "penalties_saved": 0,
        "penalties_missed": 0,
        "yellow_cards": 1,
        "red_cards": 0,
        "saves": 0,
        "bonus": 10,
        "form": "5.0",
        "points_per_game": "5.0",
        "selected_by_percent": "10.0",
        "transfers_in": 100,
        "transfers_out": 50,
        "expected_goals": "5.0",
        "expected_assists": "3.0",
        "expected_goal_involvements": "8.0",
        "expected_goals_conceded": "10.0",
        "influence": "100.0",
        "creativity": "100.0",
        "threat": "100.0",
        "ict_index": "100.0",
    }

    from fpl_agent.data.models import Player

    result = Player.model_validate(player)

    assert result.id == 1
    assert result.web_name == "Player"


def test_event_live_response_model_ignores_unmodeled_stats() -> None:
    """Only total_points is modeled; the rest of the real stats block
    (minutes, bps, ICT, xG, in_dreamteam, ...) should be ignored, not
    rejected."""
    payload = {
        "elements": [
            {
                "id": 599,
                "stats": {
                    "minutes": 90,
                    "goals_scored": 1,
                    "total_points": 8,
                    "bps": 34,
                    "in_dreamteam": True,
                },
                "explain": [{"fixture": 1, "stats": []}],
            },
        ],
    }

    result = EventLiveResponse.model_validate(payload)

    assert len(result.elements) == 1
    assert result.elements[0].id == 599
    assert result.elements[0].stats.total_points == 8