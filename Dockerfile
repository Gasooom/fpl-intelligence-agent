# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Builder
#
# Installs the project and its dependencies into a self-contained virtualenv.
# Kept as a separate stage so pip, the setuptools build backend, and any
# transient compilers never end up in the runtime image.
# ---------------------------------------------------------------------------
FROM python:3.13-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_ROOT_USER_ACTION=ignore

WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# pyproject.toml is the single source of dependency truth. There is
# deliberately no requirements.txt: a second dependency list would be free
# to drift out of sync with the one the test suite actually runs against.
#
# Only pyproject.toml and src/ are needed to build the wheel - the
# [tool.setuptools.packages.find] section packages src/ alone, so app/ is
# intentionally absent from this stage.
COPY pyproject.toml ./
COPY src ./src

RUN pip install .


# ---------------------------------------------------------------------------
# Runtime
# ---------------------------------------------------------------------------
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Keep the SQLite database on the mounted volume rather than in the
# container's writable layer, which is discarded on every recreate. Decision
# snapshots are write-once records of what was recommended before a deadline,
# so losing them would permanently destroy the evaluation history.
# See src/fpl_agent/persistence/snapshot_store.py.
ENV FPL_DB_PATH=/data/decisions.db

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

# app/ is not an installed package (pyproject packages src/ only), so it is
# imported from the working directory. app/static/index.html is read at
# import time by app.main, so the application cannot start without it.
COPY app ./app

# /data is the database's home and must be writable by the unprivileged
# runtime user. Creating and chowning it here means a fresh named volume
# inherits the correct ownership when Docker seeds it from the image.
RUN mkdir -p /data \
    && useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /data

USER appuser

# Declared so that even a plain `docker run` without an explicit mount keeps
# the database outside the container layer. docker-compose.yml overrides this
# with the named volume defined there.
VOLUME ["/data"]

EXPOSE 8000

# Uses the standard library rather than adding curl to the image purely to
# health-check it.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8000') + '/health').read()"

# Shell form so container hosts that inject $PORT (Cloud Run, Railway,
# Render) are honoured, defaulting to 8000 locally. `exec` replaces the
# shell so uvicorn runs as PID 1 and receives SIGTERM directly, letting the
# container shut down promptly instead of being killed after a timeout.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
