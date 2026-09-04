from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.main import run_application
from fpl_agent.agent.context import FPLAgentContext
from fpl_agent.decisions.schemas import (
    CaptaincyDecision,
    FPLDecisionOutput,
    RiskSummary,
)


def build_decision_output() -> FPLDecisionOutput:
    """Build a deterministic structured output for application tests."""
    return FPLDecisionOutput(
        transfer=None,
        captaincy=CaptaincyDecision(
            player_id=10,
            score=8.5,
            expected_points=7.2,
            fixture_difficulty=2.0,
            form=6.5,
            risk=RiskSummary(
                overall_risk=0.2,
                risk_level="low",
                signals=["Stable minutes"],
            ),
            evidence=[],
        ),
    )


def build_result(final_output: object) -> SimpleNamespace:
    """Build the minimal result contract required by the application."""
    return SimpleNamespace(final_output=final_output)


@pytest.mark.asyncio
async def test_run_application_returns_structured_output() -> None:
    expected_output = build_decision_output()
    mocked_result = build_result(expected_output)

    with patch(
        "app.main.run_fpl_agent",
        new=AsyncMock(return_value=mocked_result),
    ) as mock_run:
        result = await run_application("Who should I captain?")

    assert result is expected_output
    mock_run.assert_awaited_once_with(
        input_text="Who should I captain?",
        context=None,
    )


@pytest.mark.asyncio
async def test_run_application_passes_context() -> None:
    expected_output = build_decision_output()
    mocked_result = build_result(expected_output)

    context = FPLAgentContext(
        user_id="test-user",
        gameweek=5,
        free_transfers=2,
        available_budget=1.5,
    )

    with patch(
        "app.main.run_fpl_agent",
        new=AsyncMock(return_value=mocked_result),
    ) as mock_run:
        result = await run_application(
            "Analyze my captaincy options.",
            context=context,
        )

    assert result is expected_output
    mock_run.assert_awaited_once_with(
        input_text="Analyze my captaincy options.",
        context=context,
    )


@pytest.mark.asyncio
async def test_run_application_rejects_unexpected_output_type() -> None:
    mocked_result = build_result(
        {"unexpected": "output"},
    )

    with (
        patch(
            "app.main.run_fpl_agent",
            new=AsyncMock(return_value=mocked_result),
        ),
        pytest.raises(
            TypeError,
            match="unexpected output type",
        ),
    ):
        await run_application("Analyze my team.")