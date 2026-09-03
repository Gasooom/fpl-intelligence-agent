from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FPLAgentContext:
    """Runtime context available to the FPL decision agent."""

    user_id: str | None = None
    gameweek: int | None = None
    free_transfers: int = 1
    available_budget: float | None = None

    def describe(self) -> str:
        """Return a concise human-readable description of the context."""
        parts: list[str] = []

        if self.user_id is not None:
            parts.append(f"user_id={self.user_id}")

        if self.gameweek is not None:
            parts.append(f"gameweek={self.gameweek}")

        parts.append(f"free_transfers={self.free_transfers}")

        if self.available_budget is not None:
            parts.append(
                f"available_budget={self.available_budget:.1f}"
            )

        return ", ".join(parts)