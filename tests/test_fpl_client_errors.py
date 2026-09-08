from __future__ import annotations

import httpx
import pytest

from fpl_agent.data.client import FPLClient
from fpl_agent.data.errors import (
    FPLRateLimitedError,
    FPLResourceNotFoundError,
    FPLUpstreamError,
    FPLUpstreamTimeoutError,
)

# The upstream body FPL would return alongside a failure. Asserted
# against so that a regression which starts forwarding upstream text to
# callers is caught rather than silently shipped.
UPSTREAM_BODY = {"detail": "upstream-only diagnostic text"}


def client_answering(status_code: int, json_body: object = UPSTREAM_BODY) -> FPLClient:
    """An FPLClient whose upstream always answers with `status_code`."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json=json_body)

    return FPLClient(transport=httpx.MockTransport(handler))


def client_failing_with(error: Exception) -> FPLClient:
    """An FPLClient whose upstream always raises a transport failure."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise error

    return FPLClient(transport=httpx.MockTransport(handler))


@pytest.mark.asyncio
async def test_upstream_404_becomes_a_resource_not_found_error() -> None:
    """FPL answers 404 for an entry that does not exist and for a
    gameweek whose squad has not been picked yet."""
    client = client_answering(404)

    with pytest.raises(FPLResourceNotFoundError):
        await client.get_entry_picks(entry_id=8731757, gameweek=4)


@pytest.mark.asyncio
async def test_not_found_message_does_not_leak_upstream_or_httpx_detail() -> None:
    client = client_answering(404)

    with pytest.raises(FPLResourceNotFoundError) as exc_info:
        await client.get_entry_picks(entry_id=8731757, gameweek=4)

    message = str(exc_info.value)

    assert "upstream-only diagnostic text" not in message
    assert "httpx" not in message.lower()
    assert "https://" not in message
    assert "fantasy.premierleague.com" not in message
    assert "Traceback" not in message
    # The caller's own inputs are still echoed back, so the message is
    # actionable rather than merely opaque.
    assert "8731757" in message
    assert "gameweek 4" in message


@pytest.mark.asyncio
async def test_upstream_500_is_not_reported_as_not_found() -> None:
    """A broken upstream says nothing about whether the requested
    resource exists, so it must not become a 404."""
    client = client_answering(500)

    with pytest.raises(FPLUpstreamError) as exc_info:
        await client.get_entry_picks(entry_id=8731757, gameweek=4)

    assert not isinstance(exc_info.value, FPLResourceNotFoundError)


@pytest.mark.asyncio
async def test_unrecognised_4xx_is_not_reported_as_not_found() -> None:
    client = client_answering(403)

    with pytest.raises(FPLUpstreamError) as exc_info:
        await client.get_entry(entry_id=8731757)

    assert not isinstance(exc_info.value, FPLResourceNotFoundError)


@pytest.mark.asyncio
async def test_upstream_429_becomes_a_rate_limited_error() -> None:
    client = client_answering(429)

    with pytest.raises(FPLRateLimitedError):
        await client.get_bootstrap_static()


@pytest.mark.asyncio
async def test_timeout_becomes_a_timeout_error_and_not_a_not_found() -> None:
    client = client_failing_with(httpx.ReadTimeout("timed out"))

    with pytest.raises(FPLUpstreamTimeoutError) as exc_info:
        await client.get_entry_picks(entry_id=8731757, gameweek=4)

    assert not isinstance(exc_info.value, FPLResourceNotFoundError)
    assert "httpx" not in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_network_failure_becomes_an_upstream_error_and_not_a_not_found() -> None:
    client = client_failing_with(httpx.ConnectError("connection refused"))

    with pytest.raises(FPLUpstreamError) as exc_info:
        await client.get_bootstrap_static()

    assert not isinstance(exc_info.value, FPLResourceNotFoundError)
    assert "connection refused" not in str(exc_info.value)


@pytest.mark.asyncio
async def test_timeout_is_distinguished_from_a_generic_upstream_failure() -> None:
    """`FPLUpstreamTimeoutError` subclasses `FPLUpstreamError`, so the
    ordering of the client's except clauses is what keeps them apart."""
    timeout_client = client_failing_with(httpx.ConnectTimeout("timed out"))
    network_client = client_failing_with(httpx.ConnectError("refused"))

    with pytest.raises(FPLUpstreamTimeoutError):
        await timeout_client.get_fixtures()

    with pytest.raises(FPLUpstreamError) as exc_info:
        await network_client.get_fixtures()

    assert not isinstance(exc_info.value, FPLUpstreamTimeoutError)


@pytest.mark.asyncio
async def test_successful_response_is_still_parsed_normally() -> None:
    """The translation layer must be invisible on the happy path."""
    client = client_answering(200, json_body=[])

    assert await client.get_fixtures() == []
