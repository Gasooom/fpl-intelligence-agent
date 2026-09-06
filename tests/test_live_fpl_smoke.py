from __future__ import annotations

import os
import time

import pytest

from fpl_agent.decisions.service import FPLDecisionService

# Public FPL entry used throughout development as the manual smoke-test
# subject. Not used anywhere in production decision logic - this file is
# the only place it appears.
DEMO_ENTRY_ID = 8731757


@pytest.mark.asyncio
async def test_real_fpl_gameweek_decision_smoke() -> None:
    """Manual real-FPL smoke test.

    Skipped by default because it calls the live Fantasy Premier League
    API and is therefore excluded from normal test/CI runs. Run it
    explicitly with:

        RUN_LIVE_FPL_SMOKE=1 .venv/Scripts/python.exe -m pytest \\
            tests/test_live_fpl_smoke.py -v

    Verifies the full deterministic pipeline end to end against a real
    manager entry: bootstrap/entry/picks/fixtures all load, exactly the
    manager's 15 supplied picks are analyzed (never the full ~650
    player pool - see decisions/squad_analysis.py), and every
    GameweekDecision field is produced without the request hanging.
    """
    if os.environ.get("RUN_LIVE_FPL_SMOKE") != "1":
        pytest.skip(
            "Live FPL smoke test skipped. Set RUN_LIVE_FPL_SMOKE=1 to run "
            "it against the real Fantasy Premier League API.",
        )

    service = FPLDecisionService()

    started = time.monotonic()
    decision = await service.analyze_gameweek(entry_id=DEMO_ENTRY_ID)
    elapsed = time.monotonic() - started

    assert len(decision.starting_xi) == 11
    assert 0 <= len(decision.bench) <= 4
    assert decision.captain.player_id != decision.vice_captain.player_id
    assert decision.sell_candidates
    assert decision.confidence in {"High", "Medium", "Low"}
    assert decision.decision_summary
    assert decision.transfer_count == len(decision.transfer_recommendations)
    assert decision.decision_engine_version

    # The engine must never optimize across the full player pool - it
    # should complete in well under the time an exhaustive search over
    # ~650 players would take, and the API must never hang.
    assert elapsed < 15.0
