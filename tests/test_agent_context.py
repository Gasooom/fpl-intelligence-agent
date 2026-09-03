from __future__ import annotations

from fpl_agent.agent.context import FPLAgentContext


def test_default_context() -> None:
    context = FPLAgentContext()

    assert context.user_id is None
    assert context.gameweek is None
    assert context.free_transfers == 1
    assert context.available_budget is None


def test_context_stores_runtime_state() -> None:
    context = FPLAgentContext(
        user_id="user-123",
        gameweek=5,
        free_transfers=2,
        available_budget=8.5,
    )

    assert context.user_id == "user-123"
    assert context.gameweek == 5
    assert context.free_transfers == 2
    assert context.available_budget == 8.5


def test_context_description() -> None:
    context = FPLAgentContext(
        user_id="user-123",
        gameweek=5,
        free_transfers=2,
        available_budget=8.5,
    )

    assert (
        context.describe()
        == "user_id=user-123, gameweek=5, "
        "free_transfers=2, available_budget=8.5"
    )


def test_context_description_without_optional_values() -> None:
    context = FPLAgentContext()

    assert context.describe() == "free_transfers=1"