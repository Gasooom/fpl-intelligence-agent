import pytest
from pydantic import ValidationError

from fpl_agent.decisions.schemas import (
    CaptaincyDecision,
    DecisionEvidence,
    RiskSummary,
    TransferDecision,
)


def test_decision_evidence() -> None:
    evidence = DecisionEvidence(
        metric="expected_points",
        value=7.5,
        reason="Strong projected output.",
    )

    assert evidence.metric == "expected_points"
    assert evidence.value == 7.5


def test_risk_summary() -> None:
    risk = RiskSummary(
        overall_risk=0.35,
        risk_level="medium",
        signals=["limited_minutes"],
    )

    assert risk.overall_risk == 0.35
    assert risk.risk_level == "medium"
    assert risk.signals == ["limited_minutes"]


def test_transfer_decision() -> None:
    decision = TransferDecision(
        player_id=123,
        score=7.2,
        expected_points=8.0,
        form=6.5,
        fixture_difficulty=2.0,
        price=7.0,
        risk=RiskSummary(
            overall_risk=0.2,
            risk_level="low",
        ),
        evidence=[
            DecisionEvidence(
                metric="form",
                value=6.5,
                reason="Strong recent form.",
            )
        ],
    )

    assert decision.player_id == 123
    assert decision.score == 7.2
    assert len(decision.evidence) == 1


def test_captaincy_decision() -> None:
    decision = CaptaincyDecision(
        player_id=456,
        score=8.1,
        expected_points=9.0,
        fixture_difficulty=2.0,
        form=7.0,
        risk=RiskSummary(
            overall_risk=0.15,
            risk_level="low",
        ),
    )

    assert decision.player_id == 456
    assert decision.score == 8.1
    assert decision.evidence == []


def test_risk_must_be_between_zero_and_one() -> None:
    with pytest.raises(ValidationError):
        RiskSummary(
            overall_risk=1.5,
            risk_level="high",
        )


def test_decision_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        TransferDecision(
            player_id=123,
            score=7.0,
            expected_points=8.0,
            form=6.0,
            fixture_difficulty=2.0,
            price=7.0,
            risk=RiskSummary(
                overall_risk=0.2,
                risk_level="low",
            ),
            unknown_field="not_allowed",
        )


def test_decision_serialization() -> None:
    decision = TransferDecision(
        player_id=123,
        score=7.2,
        expected_points=8.0,
        form=6.5,
        fixture_difficulty=2.0,
        price=7.0,
        risk=RiskSummary(
            overall_risk=0.2,
            risk_level="low",
        ),
    )

    data = decision.model_dump()

    assert data["player_id"] == 123
    assert data["risk"]["overall_risk"] == 0.2