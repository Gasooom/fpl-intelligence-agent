from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PlayerDecisionResponse(BaseModel):
    """API representation of a deterministic player decision."""

    model_config = ConfigDict(extra="forbid")

    player_id: int
    web_name: str
    position_type: int
    team_id: int
    price: float

    form: float
    points_per_game: float
    points_per_90: float
    xgi_per_90: float

    fixture_difficulty: float
    expected_points: float

    minutes_risk: float
    availability_risk: float
    overall_risk: float
    risk_level: str

    captaincy_score: float


class SquadDecisionResponse(BaseModel):
    """API response containing the complete deterministic FPL decision."""

    model_config = ConfigDict(extra="forbid")

    starting_xi: list[PlayerDecisionResponse] = Field(
        min_length=11,
        max_length=11,
    )
    bench: list[PlayerDecisionResponse] = Field(
        min_length=0,
        max_length=4,
    )
    captain: PlayerDecisionResponse
    vice_captain: PlayerDecisionResponse
    must_play: list[PlayerDecisionResponse] 