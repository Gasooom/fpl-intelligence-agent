from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from app.cors import (
    CORS_ORIGINS_ENV_VAR,
    DEFAULT_ALLOWED_ORIGINS,
    CORSConfigurationError,
    configure_cors,
    parse_allowed_origins,
    resolve_allowed_origins,
)
from app.main import app as production_app

FRONTEND_ORIGIN = "https://frontend.example.app"
OTHER_ORIGIN = "https://somewhere-else.example.com"


def build_app() -> FastAPI:
    """A minimal app carrying the real CORS policy.

    Built per test because the policy is fixed at the moment the
    middleware is added, so each test can configure the environment
    first. Using a throwaway route also keeps these tests off the
    decision endpoints, and therefore off the live FPL API.
    """
    app = FastAPI()
    configure_cors(app)

    @app.get("/probe")
    async def probe() -> dict[str, str]:
        return {"status": "ok"}

    return app


def test_parse_strips_whitespace_and_drops_empty_entries() -> None:
    assert parse_allowed_origins(" https://a.example ,, https://b.example , ") == [
        "https://a.example",
        "https://b.example",
    ]


def test_parse_removes_duplicates_while_preserving_order() -> None:
    assert parse_allowed_origins("https://b.example,https://a.example,https://b.example") == [
        "https://b.example",
        "https://a.example",
    ]


def test_parse_of_a_blank_value_yields_nothing() -> None:
    assert parse_allowed_origins("   ,  , ") == []


def test_unset_variable_falls_back_to_the_local_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(CORS_ORIGINS_ENV_VAR, raising=False)

    assert resolve_allowed_origins() == list(DEFAULT_ALLOWED_ORIGINS)


def test_blank_variable_falls_back_to_the_local_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A variable set but empty is the shape a half-finished deployment
    config produces; it must not mean "allow nothing" or "allow all"."""
    monkeypatch.setenv(CORS_ORIGINS_ENV_VAR, "  , ,")

    assert resolve_allowed_origins() == list(DEFAULT_ALLOWED_ORIGINS)


def test_configured_variable_replaces_the_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(CORS_ORIGINS_ENV_VAR, f"{FRONTEND_ORIGIN}, {OTHER_ORIGIN}")

    assert resolve_allowed_origins() == [FRONTEND_ORIGIN, OTHER_ORIGIN]


def test_defaults_are_never_a_wildcard() -> None:
    assert "*" not in DEFAULT_ALLOWED_ORIGINS
    assert all(origin.startswith("http://") for origin in DEFAULT_ALLOWED_ORIGINS)


def test_a_bare_wildcard_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(CORS_ORIGINS_ENV_VAR, "*")

    with pytest.raises(CORSConfigurationError, match=CORS_ORIGINS_ENV_VAR):
        resolve_allowed_origins()


def test_a_padded_wildcard_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """Whitespace is stripped before validation, so a wildcard cannot
    slip through by being padded."""
    monkeypatch.setenv(CORS_ORIGINS_ENV_VAR, "  *  ")

    with pytest.raises(CORSConfigurationError):
        resolve_allowed_origins()


def test_a_wildcard_mixed_with_a_valid_origin_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(CORS_ORIGINS_ENV_VAR, f"{FRONTEND_ORIGIN}, *")

    with pytest.raises(CORSConfigurationError):
        resolve_allowed_origins()


def test_a_wildcard_is_rejected_rather_than_silently_dropped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Filtering the wildcard out would leave the operator believing
    they had opened the API up while it had actually stayed closed."""
    monkeypatch.setenv(CORS_ORIGINS_ENV_VAR, f"{FRONTEND_ORIGIN}, *")

    with pytest.raises(CORSConfigurationError):
        resolve_allowed_origins()

    # The valid half of the value must not survive as a partial policy.
    monkeypatch.setenv(CORS_ORIGINS_ENV_VAR, FRONTEND_ORIGIN)
    assert resolve_allowed_origins() == [FRONTEND_ORIGIN]


def test_wildcard_rejection_message_explains_the_fix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(CORS_ORIGINS_ENV_VAR, "*")

    with pytest.raises(CORSConfigurationError) as exc_info:
        resolve_allowed_origins()

    message = str(exc_info.value)

    assert CORS_ORIGINS_ENV_VAR in message
    assert "exact origin" in message


def test_building_an_app_with_a_wildcard_fails_loudly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The application refuses to start rather than coming up with a
    permissive policy."""
    monkeypatch.setenv(CORS_ORIGINS_ENV_VAR, "*")

    with pytest.raises(CORSConfigurationError):
        configure_cors(FastAPI())


def test_parsing_itself_still_returns_the_wildcard_verbatim() -> None:
    """`parse_allowed_origins` stays a pure string helper - rejection
    lives at the configuration boundary, so parsing keeps reporting
    exactly what was written."""
    assert parse_allowed_origins("*") == ["*"]


def test_an_origin_merely_containing_an_asterisk_is_not_the_wildcard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Only a standalone "*" is the wildcard. A pattern-looking origin
    is passed through to Starlette, which matches origins exactly and
    will simply never match it."""
    monkeypatch.setenv(CORS_ORIGINS_ENV_VAR, "https://*.vercel.app")

    assert resolve_allowed_origins() == ["https://*.vercel.app"]


def test_configured_origin_receives_an_allow_origin_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(CORS_ORIGINS_ENV_VAR, FRONTEND_ORIGIN)
    client = TestClient(build_app())

    response = client.get("/probe", headers={"Origin": FRONTEND_ORIGIN})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == FRONTEND_ORIGIN


def test_unconfigured_origin_receives_no_allow_origin_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The request still succeeds server-side - it is the *absence* of
    the header that makes the browser withhold the response from the
    calling page."""
    monkeypatch.setenv(CORS_ORIGINS_ENV_VAR, FRONTEND_ORIGIN)
    client = TestClient(build_app())

    response = client.get("/probe", headers={"Origin": OTHER_ORIGIN})

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_credentials_are_not_advertised(monkeypatch: pytest.MonkeyPatch) -> None:
    """There is no browser authentication flow, so the API must not
    invite cookies to be sent with cross-origin requests."""
    monkeypatch.setenv(CORS_ORIGINS_ENV_VAR, FRONTEND_ORIGIN)
    client = TestClient(build_app())

    response = client.get("/probe", headers={"Origin": FRONTEND_ORIGIN})

    assert "access-control-allow-credentials" not in response.headers


def test_preflight_from_an_allowed_origin_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(CORS_ORIGINS_ENV_VAR, FRONTEND_ORIGIN)
    client = TestClient(build_app())

    response = client.options(
        "/probe",
        headers={
            "Origin": FRONTEND_ORIGIN,
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == FRONTEND_ORIGIN
    assert "GET" in response.headers["access-control-allow-methods"]


def test_preflight_from_a_disallowed_origin_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(CORS_ORIGINS_ENV_VAR, FRONTEND_ORIGIN)
    client = TestClient(build_app())

    response = client.options(
        "/probe",
        headers={
            "Origin": OTHER_ORIGIN,
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_preflight_for_a_method_the_api_does_not_expose_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Methods are scoped to the read-only surface this API actually
    has, so a write method is rejected even from an allowed origin."""
    monkeypatch.setenv(CORS_ORIGINS_ENV_VAR, FRONTEND_ORIGIN)
    client = TestClient(build_app())

    response = client.options(
        "/probe",
        headers={
            "Origin": FRONTEND_ORIGIN,
            "Access-Control-Request-Method": "DELETE",
        },
    )

    assert response.status_code == 400


def test_default_configuration_allows_the_local_dev_server(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(CORS_ORIGINS_ENV_VAR, raising=False)
    client = TestClient(build_app())

    response = client.get("/probe", headers={"Origin": "http://localhost:5173"})

    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_default_configuration_refuses_an_arbitrary_origin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unconfigured deployment fails closed against the internet
    rather than open."""
    monkeypatch.delenv(CORS_ORIGINS_ENV_VAR, raising=False)
    client = TestClient(build_app())

    response = client.get("/probe", headers={"Origin": OTHER_ORIGIN})

    assert "access-control-allow-origin" not in response.headers


def test_production_app_has_cors_middleware_installed() -> None:
    """The policy is wired into the real application object, not only
    into the app these tests build for themselves."""
    assert any(
        middleware.cls is CORSMiddleware for middleware in production_app.user_middleware
    )


def test_production_app_health_endpoint_is_unchanged_by_cors() -> None:
    """Existing behaviour must be untouched: same status, same body,
    with and without an Origin header."""
    with TestClient(production_app) as client:
        without_origin = client.get("/health")
        with_origin = client.get("/health", headers={"Origin": "http://localhost:5173"})

    assert without_origin.status_code == 200
    assert without_origin.json() == {"status": "ok"}
    assert with_origin.status_code == 200
    assert with_origin.json() == {"status": "ok"}


def test_production_app_refuses_an_unknown_origin() -> None:
    """Assumes CORS_ALLOWED_ORIGINS is unset in the test environment,
    which is the case for a plain `pytest` run: the production app's
    policy is fixed when app.main is imported."""
    with TestClient(production_app) as client:
        response = client.get("/health", headers={"Origin": OTHER_ORIGIN})

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
