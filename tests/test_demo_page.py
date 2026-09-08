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


def test_demo_page_filters_blank_reasons_before_rendering_a_list() -> None:
    """Every reason list on the page must go through the blank filter, so
    a reason the API returned empty can never render as a bullet with
    nothing beside it.
    """
    with TestClient(app) as client:
        body = client.get("/").text

    assert "function nonEmptyReasons(" in body
    assert "function reasonsListHtml(" in body


def test_demo_page_filters_marker_only_reasons() -> None:
    """Entries that are nothing but a marker glyph ("-", "*", "•") pass a
    whitespace check but say nothing, and rendered as bare bullets on
    the deployed page. The filter requires a letter or a digit, which
    covers every dash and separator variant while keeping real wording
    such as "Higher expected points: 7.42" intact.
    """
    with TestClient(app) as client:
        body = client.get("/").text

    assert r"/[\p{L}\p{N}]/u.test(reason)" in body


def test_demo_page_never_renders_reason_lists_unfiltered() -> None:
    """Regression: the transfer and candidate lists previously mapped the
    raw reasons array straight into <li> elements, so a blank entry
    became an empty bullet. That pattern must not come back.
    """
    with TestClient(app) as client:
        body = client.get("/").text

    assert "bestTransfer.reasons.map(" not in body
    assert "pair.reasons.map(" not in body
    assert "c.reasons.join(" not in body


def test_demo_page_omits_a_reason_list_entirely_when_nothing_survives() -> None:
    """An emptied-out list renders as nothing at all rather than an empty
    <ul> or a stray bullet.
    """
    with TestClient(app) as client:
        body = client.get("/").text

    assert "if (!items.length) {" in body
    assert 'return "";' in body


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
