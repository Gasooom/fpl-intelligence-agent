from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Comma-separated list of origins allowed to call this API from a
# browser. Deployment-specific values (the eventual Vercel URL) belong
# here at run time, never in this source file - the frontend's domain
# is a property of the environment, not of the application.
CORS_ORIGINS_ENV_VAR = "CORS_ALLOWED_ORIGINS"

# Used only when the variable above is unset or contains no usable
# entries. These are the Vite dev server's own defaults (`npm run dev`
# on 5173, `npm run preview` on 4173), so a developer running the
# frontend against a local backend works with no configuration while
# the deployed API still refuses every unknown origin.
#
# Deliberately not ["*"]: a wildcard would let any site on the internet
# read this API's responses from a visitor's browser.
DEFAULT_ALLOWED_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
)

# Every endpoint this API exposes is a read-only GET. OPTIONS is listed
# so the preflight response advertises accurately; it is handled by the
# middleware itself rather than by any route.
ALLOWED_METHODS = ("GET", "OPTIONS")

# The frontend sends plain GETs with no custom headers (see the
# frontend's api/client.ts), so only the two standard content
# negotiation headers are permitted rather than "*".
ALLOWED_HEADERS = ("Accept", "Content-Type")

WILDCARD_ORIGIN = "*"


class CORSConfigurationError(ValueError):
    """Raised when `CORS_ALLOWED_ORIGINS` holds an unusable value.

    Raised during application startup rather than per request, so a
    misconfigured deployment fails to boot with a clear message
    instead of coming up and quietly serving a permissive policy.
    """


def parse_allowed_origins(raw: str) -> list[str]:
    """Split a comma-separated origin list into clean entries.

    Surrounding whitespace is stripped from each entry and empty
    entries are dropped, so ``"a, ,b,"`` and ``"a,b"`` are equivalent.
    Order is preserved and duplicates are removed, which keeps the
    resulting configuration identical for any input that means the
    same thing.
    """
    candidates = (origin.strip() for origin in raw.split(","))

    # dict.fromkeys de-duplicates while preserving first-seen order.
    return list(dict.fromkeys(origin for origin in candidates if origin))


def resolve_allowed_origins() -> list[str]:
    """Return the origins permitted to call this API from a browser.

    Read at call time rather than import time, matching
    ``resolve_default_db_path`` in the persistence layer, so a process
    that configures the environment late still gets the right value.

    An unset variable - and one whose entries are all blank - falls
    back to `DEFAULT_ALLOWED_ORIGINS` rather than to "allow everything"
    or "allow nothing": an unconfigured deployment stays safe, and an
    unconfigured laptop still works.

    A wildcard is rejected outright rather than filtered out. Silently
    dropping it would leave the operator believing they had opened the
    API up while it actually stayed closed; failing loudly makes the
    disagreement visible at startup.
    """
    configured = os.environ.get(CORS_ORIGINS_ENV_VAR)

    if configured is None:
        return list(DEFAULT_ALLOWED_ORIGINS)

    origins = parse_allowed_origins(configured)

    if WILDCARD_ORIGIN in origins:
        raise CORSConfigurationError(
            f'{CORS_ORIGINS_ENV_VAR} must not contain the wildcard "*". '
            "A wildcard would let any website read this API's responses "
            "from a visitor's browser. List the frontend's exact origin "
            "instead (for example https://your-frontend.vercel.app), or "
            "leave the variable unset to fall back to local development "
            "origins.",
        )

    return origins or list(DEFAULT_ALLOWED_ORIGINS)


def configure_cors(app: FastAPI) -> None:
    """Attach the CORS policy to `app`.

    Credentials are deliberately not allowed: this API has no browser
    authentication flow, no cookies and no session, so permitting them
    would widen the policy for no benefit and would additionally
    forbid ever using a wildcard origin.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolve_allowed_origins(),
        allow_credentials=False,
        allow_methods=list(ALLOWED_METHODS),
        allow_headers=list(ALLOWED_HEADERS),
    )
