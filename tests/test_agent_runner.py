from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from fpl_agent.agent.context import FPLAgentContext
from fpl_agent.agent.errors import FPLAgentRunError
from fpl_agent.agent.runner import run_fpl_agent
from fpl_agent.decisions.schemas import (
    CaptaincyDecision,
    FPLDecisionOutput,
    RiskSummary,
)


def test_run_fpl_agent_passes_context() -> None:
    async def run_test() -> None:
        context = FPLAgentContext(
            user_id="user-123",
            gameweek=5,
            free_transfers=2,
            available_budget=8.5,
        )

        with (
            patch(
                "fpl_agent.agent.runner.Runner.run",
                new=AsyncMock(return_value="result"),
            ) as mock_run,
            patch(
                "fpl_agent.agent.runner.MCPServerManager",
            ) as mock_manager,
        ):
            mock_manager.return_value.__aenter__ = AsyncMock()
            mock_manager.return_value.__aexit__ = AsyncMock(
                return_value=False,
            )

            result = await run_fpl_agent(
                "Recommend a transfer",
                context=context,
            )

        assert result == "result"
        mock_run.assert_awaited_once()

        kwargs = mock_run.await_args.kwargs
        assert kwargs["context"] is context

        mock_manager.assert_called_once()

    asyncio.run(run_test())


def test_run_fpl_agent_creates_default_context() -> None:
    async def run_test() -> None:
        with (
            patch(
                "fpl_agent.agent.runner.Runner.run",
                new=AsyncMock(return_value="result"),
            ) as mock_run,
            patch(
                "fpl_agent.agent.runner.MCPServerManager",
            ) as mock_manager,
        ):
            mock_manager.return_value.__aenter__ = AsyncMock()
            mock_manager.return_value.__aexit__ = AsyncMock(
                return_value=False,
            )

            result = await run_fpl_agent("Recommend a captain")

        assert result == "result"
        mock_run.assert_awaited_once()

        kwargs = mock_run.await_args.kwargs
        context = kwargs["context"]

        assert isinstance(context, FPLAgentContext)
        assert context.user_id is None
        assert context.gameweek is None
        assert context.free_transfers == 1
        assert context.available_budget is None

        mock_manager.assert_called_once()

    asyncio.run(run_test())


@pytest.mark.asyncio
async def test_run_fpl_agent_wraps_runner_error() -> None:
    runner_error = RuntimeError("SDK failure")

    with (
        patch(
            "fpl_agent.agent.runner.Runner.run",
            new=AsyncMock(side_effect=runner_error),
        ),
        patch(
            "fpl_agent.agent.runner.MCPServerManager",
        ) as mock_manager,
        pytest.raises(
            FPLAgentRunError,
        ) as exc_info,
    ):
        mock_manager.return_value.__aenter__ = AsyncMock()
        mock_manager.return_value.__aexit__ = AsyncMock(
            return_value=False,
        )

        await run_fpl_agent("Recommend a captain")

    assert str(exc_info.value) == (
        "The FPL decision agent failed to complete the run."
    )
    assert exc_info.value.__cause__ is runner_error


@pytest.mark.asyncio
async def test_run_fpl_agent_wraps_tool_error() -> None:
    tool_error = ValueError("Tool failed")

    with (
        patch(
            "fpl_agent.agent.runner.Runner.run",
            new=AsyncMock(side_effect=tool_error),
        ),
        patch(
            "fpl_agent.agent.runner.MCPServerManager",
        ) as mock_manager,
        pytest.raises(FPLAgentRunError) as exc_info,
    ):
        mock_manager.return_value.__aenter__ = AsyncMock()
        mock_manager.return_value.__aexit__ = AsyncMock(
            return_value=False,
        )

        await run_fpl_agent(
            "Analyze this player",
            context=FPLAgentContext(gameweek=5),
        )

    assert exc_info.value.__cause__ is tool_error


@pytest.mark.asyncio
async def test_run_fpl_agent_returns_runner_result() -> None:
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

    with (
        patch(
            "fpl_agent.agent.runner.Runner.run",
            new=AsyncMock(return_value=output),
        ) as mock_run,
        patch(
            "fpl_agent.agent.runner.MCPServerManager",
        ) as mock_manager,
    ):
        mock_manager.return_value.__aenter__ = AsyncMock()
        mock_manager.return_value.__aexit__ = AsyncMock(
            return_value=False,
        )

        result = await run_fpl_agent("Recommend a captain")

    assert result is output
    mock_run.assert_awaited_once()
    mock_manager.assert_called_once()