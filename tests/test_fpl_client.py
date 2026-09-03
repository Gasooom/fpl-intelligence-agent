import pytest

from fpl_agent.data.client import FPLClient
from fpl_agent.data.models import BootstrapData


@pytest.mark.asyncio
async def test_get_bootstrap_static() -> None:
    client = FPLClient()

    data = await client.get_bootstrap_static()

    assert isinstance(data, BootstrapData)
    assert len(data.elements) > 0
    assert len(data.teams) == 20
    assert len(data.events) > 0


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