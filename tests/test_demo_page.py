from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_demo_page_returns_html() -> None:
    """The demo page must be served without touching the FPL API or the
    decision service - it is static content that only calls the
    existing JSON API client-side.
    """
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

    body = response.text
    assert "Fantasy Decision Intelligence" in body
    assert 'id="entry-id"' in body
    assert 'id="gameweek"' in body
    assert 'id="query-form"' in body


def test_demo_page_calls_the_existing_decision_endpoint() -> None:
    """The page's client-side fetch must target the real, tested API
    route rather than a duplicate or hardcoded path.
    """
    with TestClient(app) as client:
        response = client.get("/")

    assert "/api/v1/decision/" in response.text


def test_demo_page_does_not_prefill_a_default_entry_id() -> None:
    """8731757 may appear only as a placeholder hint (e.g. "e.g. 8731757"),
    never as a pre-filled input value that would submit automatically -
    the manual smoke-test entry must not become a baked-in default.
    """
    with TestClient(app) as client:
        response = client.get("/")

    assert 'value="8731757"' not in response.text
    assert "entry-id" in response.text
    assert 'placeholder="e.g. 8731757"' in response.text
