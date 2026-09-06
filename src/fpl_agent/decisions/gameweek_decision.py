from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from fpl_agent.data.models import Fixture, Player, SquadPick, Team
from fpl_agent.decisions.squad_analysis import (
    SquadDecision,
    SquadPlayerAnalysis,
    build_squad_decision,
)
from fpl_agent.decisions.transfer_analysis import (
    BuyCandidate,
    SellCandidate,
    TransferPair,
    build_available_pool_analyses,
    build_transfer_pairs,
    extract_bank_balance,
    rank_buy_candidates,
    rank_sell_candidates,
)

# Bumped whenever the deterministic scoring/decision rules change, so a
# stored or logged decision can always be traced back to the rules that
# produced it.
DECISION_ENGINE_VERSION = "v1"
DATA_SOURCE = "official-fpl-api"

_HIGH_CONFIDENCE_SAMPLE = 0.75
_HIGH_CONFIDENCE_RISK = 0.3
_MEDIUM_CONFIDENCE_SAMPLE = 0.5
_MEDIUM_CONFIDENCE_RISK = 0.5
_STRONG_FORM = 6.0

# Used only to rank already-accepted transfer pairs against one another
# when picking the single best one - not used anywhere else, and does
# not affect which pairs are accepted or classified as "avoid".
_PRIORITY_RANK = {"essential": 3, "strong": 2, "optional": 1, "avoid": 0}


@dataclass(frozen=True)
class RecommendationEvidence:
    """Structured, dynamically generated evidence for one recommendation.

    Never hardcoded per player: reasons are derived from the same
    deterministic metrics that produced the decision.
    """

    player_id: int
    decision: str
    score: float
    reasons: list[str]


@dataclass(frozen=True)
class GameweekDecision:
    """The unified deterministic gameweek action plan.

    The deterministic engine remains the sole decision authority for
    every field here - starting XI, captaincy, and transfers alike.
    No LLM is involved in producing any of these values.
    """

    gameweek: int
    generated_at: str
    decision_engine_version: str
    data_source: str

    starting_xi: list[SquadPlayerAnalysis]
    bench: list[SquadPlayerAnalysis]
    captain: SquadPlayerAnalysis
    vice_captain: SquadPlayerAnalysis
    must_play: list[SquadPlayerAnalysis]

    sell_candidates: list[SellCandidate]
    buy_candidates: list[BuyCandidate]
    transfer_recommendations: list[TransferPair]
    transfer_count: int
    best_transfer: TransferPair | None

    confidence: str
    decision_summary: str
    evidence: list[RecommendationEvidence]


def _aggregate_confidence(starting_xi: list[SquadPlayerAnalysis]) -> str:
    """Aggregate starting-XI confidence and risk into one deterministic label.

    High: strong average sample confidence and low average risk.
    Medium: adequate confidence and moderate risk.
    Low: everything else - deliberately the conservative default.
    """
    if not starting_xi:
        return "Low"

    avg_confidence = sum(
        player.sample_confidence for player in starting_xi
    ) / len(starting_xi)
    avg_risk = sum(player.overall_risk for player in starting_xi) / len(
        starting_xi,
    )

    if avg_confidence >= _HIGH_CONFIDENCE_SAMPLE and avg_risk < _HIGH_CONFIDENCE_RISK:
        return "High"

    if (
        avg_confidence >= _MEDIUM_CONFIDENCE_SAMPLE
        and avg_risk < _MEDIUM_CONFIDENCE_RISK
    ):
        return "Medium"

    return "Low"


def _captain_reasons(player: SquadPlayerAnalysis) -> list[str]:
    reasons = [
        "Highest captaincy score",
        f"{player.expected_points} expected points",
        f"Fixture difficulty {player.fixture_difficulty}",
    ]

    if player.form >= _STRONG_FORM:
        reasons.append(f"Strong recent form ({player.form})")

    return reasons


def _vice_captain_reasons(player: SquadPlayerAnalysis) -> list[str]:
    reasons = [
        "Second-highest captaincy score",
        f"{player.expected_points} expected points",
    ]

    if player.form >= _STRONG_FORM:
        reasons.append(f"Strong recent form ({player.form})")

    return reasons


def _must_play_reasons(player: SquadPlayerAnalysis) -> list[str]:
    return [
        "No availability risk",
        f"Overall risk: {player.risk_level}",
        f"Sample confidence: {player.sample_confidence}",
    ]


def _build_evidence(
    squad_decision: SquadDecision,
    transfer_pairs: list[TransferPair],
) -> list[RecommendationEvidence]:
    """Build structured evidence for every key recommendation.

    Sell/buy candidates that are not part of an actual recommended
    pair already carry their own reasons on SellCandidate/BuyCandidate;
    this list covers the decisions the engine is actively recommending.
    """
    evidence = [
        RecommendationEvidence(
            player_id=squad_decision.captain.player_id,
            decision="captain",
            score=squad_decision.captain.captaincy_score,
            reasons=_captain_reasons(squad_decision.captain),
        ),
        RecommendationEvidence(
            player_id=squad_decision.vice_captain.player_id,
            decision="vice_captain",
            score=squad_decision.vice_captain.captaincy_score,
            reasons=_vice_captain_reasons(squad_decision.vice_captain),
        ),
    ]

    evidence.extend(
        RecommendationEvidence(
            player_id=player.player_id,
            decision="must_play",
            score=player.selection_score,
            reasons=_must_play_reasons(player),
        )
        for player in squad_decision.must_play
    )

    evidence.extend(
        RecommendationEvidence(
            player_id=pair.sell.player_id,
            decision="sell",
            score=pair.sell.sell_score.score,
            reasons=pair.sell.reasons,
        )
        for pair in transfer_pairs
    )

    evidence.extend(
        RecommendationEvidence(
            player_id=pair.buy.player_id,
            decision="buy",
            score=pair.buy.selection_score,
            reasons=pair.reasons,
        )
        for pair in transfer_pairs
    )

    return evidence


def select_best_transfer(
    transfer_pairs: list[TransferPair],
) -> TransferPair | None:
    """Pick the single best transfer if only one transfer can be made.

    Ranks accepted pairs by priority tier first (essential > strong >
    optional), then by net_improvement within a tier. Every candidate
    in transfer_pairs has already cleared build_transfer_pairs' own
    worthwhile-improvement and "avoid" filtering, so this only decides
    which of the already-worthwhile pairs is the single strongest move.
    """
    if not transfer_pairs:
        return None

    return max(
        transfer_pairs,
        key=lambda pair: (
            _PRIORITY_RANK.get(pair.priority, 0),
            pair.net_improvement,
        ),
    )


def _build_summary(
    squad_decision: SquadDecision,
    transfer_pairs: list[TransferPair],
    best_transfer: TransferPair | None,
    confidence: str,
) -> str:
    """Build a deterministic natural-language summary from computed facts.

    No LLM is used here: this is plain string formatting over already
    -computed deterministic values.
    """
    captain = squad_decision.captain
    vice_captain = squad_decision.vice_captain

    parts = [
        (
            f"Captain: {captain.web_name} "
            f"({captain.expected_points} expected points)."
        ),
        f"Vice-captain: {vice_captain.web_name}.",
    ]

    if transfer_pairs:
        transfer_bits = ", ".join(
            f"{pair.sell.web_name} -> {pair.buy.web_name} ({pair.priority})"
            for pair in transfer_pairs
        )
        parts.append(
            f"{len(transfer_pairs)} transfer recommendation(s): "
            f"{transfer_bits}.",
        )
    else:
        parts.append("No worthwhile transfers found this gameweek.")

    if best_transfer is not None:
        parts.append(
            f"Best single transfer: {best_transfer.sell.web_name} -> "
            f"{best_transfer.buy.web_name} "
            f"(+{best_transfer.net_improvement} expected points, "
            f"{best_transfer.priority}).",
        )

    parts.append(f"Decision confidence: {confidence}.")

    return " ".join(parts)


def build_gameweek_decision(
    players: list[Player],
    teams: list[Team],
    fixtures: list[Fixture],
    picks: list[SquadPick] | list[int],
    gameweek: int,
    entry_history: dict[str, object] | None = None,
    buy_candidates_limit: int = 10,
    max_transfer_pairs: int = 5,
) -> GameweekDecision:
    """Build the unified deterministic gameweek decision.

    Combines the existing squad decision (starting XI, bench,
    captaincy, must-play - unchanged) with deterministic sell/buy
    transfer intelligence into one coherent, evidence-backed action
    plan. The starting-XI optimizer still runs only over the supplied
    15 picks; the buy-candidate pool is scored player-by-player
    (O(n), no combinatorial search) rather than optimized jointly with
    the squad.
    """
    squad_decision = build_squad_decision(
        players=players,
        teams=teams,
        fixtures=fixtures,
        picks=picks,
    )

    full_squad = [*squad_decision.starting_xi, *squad_decision.bench]
    squad_player_ids = {player.player_id for player in full_squad}

    pool_analyses = build_available_pool_analyses(
        players=players,
        teams=teams,
        fixtures=fixtures,
        exclude_player_ids=squad_player_ids,
    )

    sell_candidates = rank_sell_candidates(full_squad)

    entry_bank = extract_bank_balance(entry_history)

    transfer_pairs = build_transfer_pairs(
        sell_candidates=sell_candidates,
        pool_analyses=pool_analyses,
        squad_analyses=full_squad,
        entry_bank=entry_bank,
        max_pairs=max_transfer_pairs,
    )

    buy_candidates = rank_buy_candidates(
        pool_analyses,
        position_type=None,
        limit=buy_candidates_limit,
    )

    best_transfer = select_best_transfer(transfer_pairs)

    confidence = _aggregate_confidence(squad_decision.starting_xi)

    evidence = _build_evidence(squad_decision, transfer_pairs)

    decision_summary = _build_summary(
        squad_decision,
        transfer_pairs,
        best_transfer,
        confidence,
    )

    return GameweekDecision(
        gameweek=gameweek,
        generated_at=datetime.now(UTC).isoformat(),
        decision_engine_version=DECISION_ENGINE_VERSION,
        data_source=DATA_SOURCE,
        starting_xi=squad_decision.starting_xi,
        bench=squad_decision.bench,
        captain=squad_decision.captain,
        vice_captain=squad_decision.vice_captain,
        must_play=squad_decision.must_play,
        sell_candidates=sell_candidates,
        buy_candidates=buy_candidates,
        transfer_recommendations=transfer_pairs,
        transfer_count=len(transfer_pairs),
        best_transfer=best_transfer,
        confidence=confidence,
        decision_summary=decision_summary,
        evidence=evidence,
    )
