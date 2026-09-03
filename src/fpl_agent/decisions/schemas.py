from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DecisionEvidence(BaseModel):
    """Evidence supporting an FPL decision."""

    model_config = ConfigDict(extra="forbid")

    metric: str
    value: float
    reason: str


class RiskSummary(BaseModel):
    """Risk information attached to a decision."""

    model_config = ConfigDict(extra="forbid")

    overall_risk: float = Field(ge=0.0, le=1.0)
    risk_level: str
    signals: list[str] = Field(default_factory=list)


class TransferDecision(BaseModel):
    """Structured transfer recommendation."""

    model_config = ConfigDict(extra="forbid")

    player_id: int
    score: float
    expected_points: float
    form: float
    fixture_difficulty: float
    price: float
    risk: RiskSummary
    evidence: list[DecisionEvidence] = Field(default_factory=list)


class CaptaincyDecision(BaseModel):
    """Structured captaincy recommendation."""

    model_config = ConfigDict(extra="forbid")

    player_id: int
    score: float
    expected_points: float
    fixture_difficulty: float
    form: float
    risk: RiskSummary
    evidence: list[DecisionEvidence] = Field(default_factory=list)