from __future__ import annotations


class FPLAgentError(Exception):
    """Base exception for the FPL decision agent."""


class FPLAgentRunError(FPLAgentError):
    """Raised when an FPL agent run fails."""


class MCPError(FPLAgentError):
    """Base exception for MCP-related failures."""


class FPLMCPError(MCPError):
    """Raised when the FPL MCP capability fails."""


class ExternalMCPError(MCPError):
    """Raised when the external-data MCP capability fails."""