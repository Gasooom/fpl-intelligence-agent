from fpl_agent.decisions.schemas import (
    CaptaincyDecision,
    DecisionEvidence,
    FPLDecisionOutput,
    RiskSummary,
    TransferDecision,
)


def test_transfer_decision_is_valid_structured_output() -> None:
    decision = TransferDecision(
        player_id=123,
        score=7.5,
        expected_points=8.0,
        form=6.5,
        fixture_difficulty=2.0,
        price=7.0,
        risk=RiskSummary(
            overall_risk=0.2,
            risk_level="low",
            signals=[],
        ),
        evidence=[
            DecisionEvidence(
                metric="expected_points",
                value=8.0,
                reason="Strong projected output.",
            )
        ],
    )

    assert decision.player_id == 123
    assert decision.score == 7.5


def test_captaincy_decision_is_valid_structured_output() -> None:
    decision = CaptaincyDecision(
        player_id=456,
        score=8.5,
        expected_points=9.0,
        fixture_difficulty=1.0,
        form=7.0,
        risk=RiskSummary(
            overall_risk=0.1,
            risk_level="low",
            signals=[],
        ),
        evidence=[
            DecisionEvidence(
                metric="expected_points",
                value=9.0,
                reason="Highest projected output.",
            )
        ],
    )

    assert decision.player_id == 456
    assert decision.score == 8.5


def test_fpl_decision_output_supports_transfer() -> None:
    output = FPLDecisionOutput(
        transfer=TransferDecision(
            player_id=123,
            score=7.5,
            expected_points=8.0,
            form=6.5,
            fixture_difficulty=2.0,
            price=7.0,
            risk=RiskSummary(
                overall_risk=0.2,
                risk_level="low",
                signals=[],
            ),
        )
    )

    assert output.transfer is not None
    assert output.transfer.player_id == 123
    assert output.captaincy is None


def test_fpl_decision_output_supports_captaincy() -> None:
    output = FPLDecisionOutput(
        captaincy=CaptaincyDecision(
            player_id=456,
            score=8.5,
            expected_points=9.0,
            fixture_difficulty=1.0,
            form=7.0,
            risk=RiskSummary(
                overall_risk=0.1,
                risk_level="low",
                signals=[],
            ),
        )
    )

    assert output.captaincy is not None
    assert output.captaincy.player_id == 456
    assert output.transfer is None


def test_empty_fpl_decision_output_is_valid() -> None:
    output = FPLDecisionOutput()

    assert output.transfer is None
    assert output.captaincy is None