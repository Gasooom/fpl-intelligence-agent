from __future__ import annotations


class FPLAgentError(Exception):
    """Base exception for the FPL decision agent."""


class FPLAgentRunError(FPLAgentError):
    """Raised when an FPL agent run fails."""