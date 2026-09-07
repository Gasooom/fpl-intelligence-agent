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
    # expected_points * 2 for the selected captain only, per the FPL
    # captain multiplier - expected_points unmultiplied (1x) for every
    # other player, including the vice-captain: this deterministic
    # system does not model the vice automatically becoming captain,
    # so there is no rule under which their effective_points would
    # differ from their expected_points. See
    # analysis.captaincy_scoring for how this differs from
    # captaincy_score.
    effective_points: float


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
    """API representation of a deterministic sell -> buy transfer pair.

    `net_improvement` (a selection-score delta - points, form,
    confidence, and risk blended together) and `priority` are preserved
    from before this project added real transfer economics.
    `expected_point_gain`/`hit_cost`/`net_value` are the new, purely
    points-based economics: raw points gain, the FPL hit cost (in
    points, always >= 0) of making this transfer given the manager's
    free-transfer allowance, and what's left after that cost.
    `hit_cost`/`net_value` are null exactly when the request did not
    supply `free_transfers_available` (see
    GameweekDecisionResponse.free_transfers_available) - in that case
    `priority` also falls back to the pre-existing selection-score
    classification rather than the new economics-based one.
    """

    model_config = ConfigDict(extra="forbid")

    sell: SellCandidateResponse
    buy: BuyCandidateResponse

    net_improvement: float
    risk_change: float
    price_change: float
    within_budget: bool | None

    priority: str
    reasons: list[str]

    expected_point_gain: float
    hit_cost: float | None
    net_value: float | None


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

    # The manager's real transfer context for this decision.
    # in_the_bank comes from the FPL entry's own data and is null only
    # when that's absent. free_transfers_available has no public FPL
    # API source - it is null unless explicitly supplied as a request
    # parameter (see GET /api/v1/decision/{entry_id}), and is never
    # guessed at.
    free_transfers_available: int | None
    in_the_bank: float | None

    # Mirrors official FPL gameweek scoring: starting_xi_expected_points
    # is the raw sum of the 11 starters' expected_points (bench
    # excluded); projected_gameweek_points adds one extra copy of the
    # captain's expected_points for the captain multiplier - the
    # captain is counted exactly twice across the two fields combined,
    # never more.
    starting_xi_expected_points: float
    projected_gameweek_points: float

    confidence: str
    decision_summary: str
    evidence: list[EvidenceResponse]
