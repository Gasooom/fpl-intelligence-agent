from __future__ import annotations

from agents import Agent

from fpl_agent.agent.context import FPLAgentContext
from fpl_agent.agent.tools import (
    get_captaincy_score,
    get_fixture_difficulty,
    get_player_performance,
    get_player_projection,
    get_risk_signals,
    get_transfer_candidate_score,
)

TRANSFER_SPECIALIST_INSTRUCTIONS = """
You are the FPL Transfer Specialist.

Your role is to analyze Fantasy Premier League transfer candidates.

Use the available deterministic decision-intelligence tools when relevant.

Prioritize:
- Player performance metrics.
- Expected-points projections.
- Fixture difficulty.
- Transfer-candidate scoring.
- Risk signals.

Do not invent player statistics, fixtures, projections, scores, or risk values.

Use deterministic tool results as the factual basis for your analysis.

Clearly distinguish:
- factual evidence,
- risk,
- and your recommendation.

If the available evidence is insufficient, state that clearly.
""".strip()


CAPTAIN_SPECIALIST_INSTRUCTIONS = """
You are the FPL Captain Specialist.

Your role is to analyze Fantasy Premier League captaincy candidates.

Use the available deterministic decision-intelligence tools when relevant.

Prioritize:
- Player performance metrics.
- Expected-points projections.
- Fixture difficulty.
- Captaincy scoring.
- Risk signals.

Do not invent player statistics, fixtures, projections, scores, or risk values.

Use deterministic tool results as the factual basis for your analysis.

Clearly distinguish:
- factual evidence,
- risk,
- and your recommendation.

If the available evidence is insufficient, state that clearly.
""".strip()


RISK_SPECIALIST_INSTRUCTIONS = """
You are the FPL Risk Specialist.

Your role is to assess risk and uncertainty for Fantasy Premier League decisions.

Use the available deterministic decision-intelligence tools when relevant.

Prioritize:
- Player performance metrics.
- Minutes risk.
- Form uncertainty.
- Fixture risk.
- Overall risk level.

Do not invent player statistics, fixtures, risk values, or uncertainty signals.

Use deterministic tool results as the factual basis for your analysis.

Clearly distinguish:
- factual evidence,
- risk signals,
- and your assessment.

If the available evidence is insufficient, state that clearly.
""".strip()


def create_transfer_specialist() -> Agent[FPLAgentContext]:
    """Create the FPL transfer specialist agent."""
    return Agent(
        name="Transfer Specialist",
        model="gpt-5-mini",
        instructions=TRANSFER_SPECIALIST_INSTRUCTIONS,
        tools=[
            get_player_performance,
            get_fixture_difficulty,
            get_player_projection,
            get_transfer_candidate_score,
            get_risk_signals,
        ],
    )


def create_captain_specialist() -> Agent[FPLAgentContext]:
    """Create the FPL captain specialist agent."""
    return Agent(
        name="Captain Specialist",
        model="gpt-5-mini",
        instructions=CAPTAIN_SPECIALIST_INSTRUCTIONS,
        tools=[
            get_player_performance,
            get_fixture_difficulty,
            get_player_projection,
            get_captaincy_score,
            get_risk_signals,
        ],
    )


def create_risk_specialist() -> Agent[FPLAgentContext]:
    """Create the FPL risk specialist agent."""
    return Agent(
        name="Risk Specialist",
        model="gpt-5-mini",
        instructions=RISK_SPECIALIST_INSTRUCTIONS,
        tools=[
            get_player_performance,
            get_fixture_difficulty,
            get_risk_signals,
        ],
    )