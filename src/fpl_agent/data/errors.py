from __future__ import annotations


class FPLDataError(Exception):
    """Base exception for failures fetching data from the official FPL API.

    These are deliberately transport-agnostic: the data layer raises
    them, and the HTTP boundary decides what status code each one
    deserves. That keeps `FPLClient` usable outside FastAPI (scripts,
    the MCP servers, tests) without importing a web framework, and
    keeps status-code policy in one place at the edge.

    Every message on these exceptions is written by this project and
    is safe to return to a client. Upstream exception text, request
    URLs, and upstream response bodies are never interpolated into
    them - see `FPLClient._get_json`.
    """


class FPLResourceNotFoundError(FPLDataError):
    """Raised when the FPL API reports that a resource does not exist.

    The common causes are a manager entry ID that was never issued and
    a gameweek whose squad has not been picked yet - both of which are
    the caller's mistake to correct, not a server fault, so this maps
    to a 404 rather than a 500.
    """


class FPLRateLimitedError(FPLDataError):
    """Raised when the FPL API rejects a request for rate limiting.

    Distinguished from a generic upstream failure because the caller's
    correct response differs: retry later, rather than treat the
    service as broken.
    """


class FPLUpstreamError(FPLDataError):
    """Raised when the FPL API is unreachable or answered with a failure.

    Covers network failures and any upstream status this project does
    not translate more specifically. The request itself may be
    perfectly valid, so this stays a server-side failure and must
    never be reported as a 404.
    """


class FPLUpstreamTimeoutError(FPLUpstreamError):
    """Raised when a request to the FPL API exceeded its timeout.

    A subclass of `FPLUpstreamError` so callers that only care about
    "upstream did not work" can catch the base class, while the HTTP
    boundary can still answer 504 instead of 502.
    """
