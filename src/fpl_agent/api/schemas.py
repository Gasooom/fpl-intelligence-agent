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


class SellCandidateResponse(BaseModel):
    """API representation of a deterministic sell candidate."""

    model_config = ConfigDict(extra="forbid")

    player_id: int
    web_name: str
    position_type: int
    team_id: int
    price: float

    expected_points: float
    form: float
    fixture_difficulty: float

    overall_risk: float
    availability_risk: float
    risk_level: str
    sample_confidence: float

    selection_score: float
    score: float
    rank: int
    reasons: list[str]


class BuyCandidateResponse(BaseModel):
    """API representation of a deterministic buy candidate."""

    model_config = ConfigDict(extra="forbid")

    player_id: int
    web_name: str
    position_type: int
    team_id: int
    price: float

    expected_points: float
    form: float
    fixture_difficulty: float

    overall_risk: float
    availability_risk: float
    risk_level: str
    sample_confidence: float

    selection_score: float
    value_score: float
    rank: int
    reasons: list[str]


class TransferRecommendationResponse(BaseModel):
    """API representation of a deterministic sell -> buy transfer pair."""

    model_config = ConfigDict(extra="forbid")

    sell: SellCandidateResponse
    buy: BuyCandidateResponse

    net_improvement: float
    risk_change: float
    price_change: float
    within_budget: bool | None

    priority: str
    reasons: list[str]


class EvidenceResponse(BaseModel):
    """Structured, dynamically generated evidence for one recommendation."""

    model_config = ConfigDict(extra="forbid")

    player_id: int
    decision: str
    score: float
    reasons: list[str]


class GameweekDecisionResponse(BaseModel):
    """The unified deterministic gameweek action plan."""

    model_config = ConfigDict(extra="forbid")

    gameweek: int
    generated_at: str
    decision_engine_version: str
    data_source: str

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

    sell_candidates: list[SellCandidateResponse]
    buy_candidates: list[BuyCandidateResponse]
    transfer_recommendations: list[TransferRecommendationResponse]
    transfer_count: int
    best_transfer: TransferRecommendationResponse | None

    confidence: str
    decision_summary: str
    evidence: list[EvidenceResponse]
