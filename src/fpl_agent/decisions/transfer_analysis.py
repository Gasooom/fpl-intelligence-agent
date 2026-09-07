from __future__ import annotations

from dataclasses import dataclass

from fpl_agent.analysis.sell_scoring import SellScore, score_sell_candidate
from fpl_agent.analysis.transfer_economics import (
    calculate_transfer_economics,
    classify_transfer_tier,
)
from fpl_agent.analysis.transfer_scoring import score_transfer_candidate
from fpl_agent.data.models import Fixture, Player, Team
from fpl_agent.decisions.squad_analysis import (
    SquadPlayerAnalysis,
    build_player_analysis,
    is_player_available,
    player_fixture_difficulty,
)

# Below this deterministic net-improvement threshold (in selection-score
# points) a transfer is judged not worth recommending. Keeps the engine
# from surfacing noise per Phase 5's "decision usefulness, not lots of
# recommendations" goal.
_MIN_WORTHWHILE_IMPROVEMENT = 0.3
_MAX_TEAM_PLAYERS = 3

# Per-90 stats (player_metrics/projections) extrapolate raw minutes with
# no floor, so a player with only a handful of minutes and one bonus
# point can produce a wildly inflated points-per-90 figure (e.g. 2
# points in 1 minute extrapolates to 180 points per 90). Real squads
# rarely surface this since managers don't own single-minute cameo
# players, but the wider buy-candidate pool does. Requiring at least a
# full match's worth of minutes bounds the extrapolation multiplier to
# roughly 1x and screens out these nonsensical candidates, without
# touching the shared, already-validated projection formula itself.
_MIN_POOL_MINUTES = 90


@dataclass(frozen=True)
class SellCandidate:
    """A current squad player ranked as a deterministic sell candidate."""

    player_id: int
    web_name: str
    position_type: int
    team_id: int
    price: float
    expected_points: float
    form: float
    fixture_difficulty: float
    overall_risk: float
    availability_risk: float
    risk_level: str
    sample_confidence: float
    selection_score: float
    sell_score: SellScore
    rank: int
    reasons: list[str]


@dataclass(frozen=True)
class BuyCandidate:
    """A player-pool candidate ranked as a deterministic buy target."""

    player_id: int
    web_name: str
    position_type: int
    team_id: int
    price: float
    expected_points: float
    form: float
    fixture_difficulty: float
    overall_risk: float
    availability_risk: float
    risk_level: str
    sample_confidence: float
    selection_score: float
    value_score: float
    rank: int
    reasons: list[str]


@dataclass(frozen=True)
class TransferPair:
    """A deterministic sell -> buy transfer recommendation.

    `net_improvement` (selection-score delta) and the historical
    threshold-based `priority` remain exactly as before when
    `free_transfers_available` is unknown - see build_transfer_pairs.
    `expected_point_gain`/`hit_cost`/`net_value` are the real transfer
    economics: raw points gain, the FPL hit cost (positive, in points)
    of making this transfer given the manager's free-transfer
    allowance, and what's left after that cost. `hit_cost`/`net_value`
    are None exactly when free_transfers_available was not supplied -
    an unknown FT count is never assumed to be any particular number.
    """

    sell: SellCandidate
    buy: BuyCandidate
    net_improvement: float
    risk_change: float
    price_change: float
    within_budget: bool | None
    priority: str
    reasons: list[str]
    expected_point_gain: float
    hit_cost: float | None
    net_value: float | None


def _build_sell_reasons(
    sell_score: SellScore,
    player: SquadPlayerAnalysis,
) -> list[str]:
    """Build human-readable reasons from the sell-score breakdown.

    Reasons are derived dynamically from whichever penalty components
    are non-zero, ranked by contribution, never hardcoded per player.
    """
    components = [
        (
            sell_score.risk_penalty,
            f"High overall risk ({player.risk_level}, {player.overall_risk})",
        ),
        (
            sell_score.low_projection_penalty,
            f"Weak projected output ({player.expected_points} expected points)",
        ),
        (
            sell_score.difficult_fixture_penalty,
            f"Difficult fixture (difficulty {player.fixture_difficulty})",
        ),
        (
            sell_score.availability_penalty,
            "Availability risk (doubtful or unavailable)",
        ),
        (
            sell_score.low_confidence_penalty,
            f"Low minutes confidence ({player.sample_confidence})",
        ),
    ]

    reasons = [
        text
        for value, text in sorted(
            components,
            key=lambda component: component[0],
            reverse=True,
        )
        if value > 0.0
    ]

    if not reasons:
        reasons.append("Weakest deterministic selection score in the squad")

    return reasons


def _build_buy_reasons(player: SquadPlayerAnalysis) -> list[str]:
    """Build human-readable reasons a player is a strong buy target."""
    reasons = [f"Expected points: {player.expected_points}"]

    if player.fixture_difficulty <= 2.5:
        reasons.append(
            f"Favorable fixture difficulty: {player.fixture_difficulty}",
        )

    if player.sample_confidence >= 0.75:
        reasons.append("Strong minutes confidence")
    elif player.sample_confidence >= 0.5:
        reasons.append("Adequate minutes confidence")

    if player.risk_level == "low":
        reasons.append("Low overall risk")

    if player.form >= 6.0:
        reasons.append(f"Strong recent form: {player.form}")

    return reasons


def _build_pair_reasons(
    sell: SellCandidate,
    buy: BuyCandidate,
) -> list[str]:
    """Build comparative reasons a buy target improves on a sell candidate."""
    reasons: list[str] = []

    if buy.expected_points > sell.expected_points:
        reasons.append(
            f"Higher expected points ({buy.expected_points} vs "
            f"{sell.expected_points})",
        )

    if buy.fixture_difficulty < sell.fixture_difficulty:
        reasons.append(
            f"Better fixture (difficulty {buy.fixture_difficulty} vs "
            f"{sell.fixture_difficulty})",
        )

    if buy.overall_risk < sell.overall_risk:
        reasons.append(f"Lower risk ({buy.risk_level} vs {sell.risk_level})")

    if buy.sample_confidence > sell.sample_confidence:
        reasons.append("Stronger minutes confidence")

    if buy.form > sell.form:
        reasons.append(f"Better recent form ({buy.form} vs {sell.form})")

    buy_value = buy.expected_points / buy.price if buy.price > 0 else 0.0
    sell_value = sell.expected_points / sell.price if sell.price > 0 else 0.0

    if buy_value > sell_value:
        reasons.append("Better points-per-price value")

    if not reasons:
        reasons.append("Higher deterministic selection score")

    return reasons


def build_available_pool_analyses(
    players: list[Player],
    teams: list[Team],
    fixtures: list[Fixture],
    exclude_player_ids: set[int],
) -> list[SquadPlayerAnalysis]:
    """Build deterministic analysis for buy-eligible players outside the squad.

    Filters cheaply (availability, minutes played, squad exclusion) before
    running the per-player projection/risk/confidence pipeline, and never
    performs combinatorial search over the pool - each candidate is scored
    independently in O(1) relative to the others.
    """
    candidates = [
        player
        for player in players
        if player.id not in exclude_player_ids
        and player.minutes >= _MIN_POOL_MINUTES
        and is_player_available(player)
    ]

    return [
        build_player_analysis(
            player=player,
            fixture_difficulty=player_fixture_difficulty(
                player=player,
                teams=teams,
                fixtures=fixtures,
            ),
        )
        for player in candidates
    ]


def rank_sell_candidates(
    squad_analyses: list[SquadPlayerAnalysis],
) -> list[SellCandidate]:
    """Rank every current squad player as a deterministic sell candidate."""
    scored = [
        (player, score_sell_candidate(
            player_id=player.player_id,
            expected_points=player.expected_points,
            overall_risk=player.overall_risk,
            availability_risk=player.availability_risk,
            sample_confidence=player.sample_confidence,
            fixture_difficulty=player.fixture_difficulty,
        ))
        for player in squad_analyses
    ]

    scored.sort(key=lambda item: item[1].score, reverse=True)

    return [
        SellCandidate(
            player_id=player.player_id,
            web_name=player.web_name,
            position_type=player.position_type,
            team_id=player.team_id,
            price=player.price,
            expected_points=player.expected_points,
            form=player.form,
            fixture_difficulty=player.fixture_difficulty,
            overall_risk=player.overall_risk,
            availability_risk=player.availability_risk,
            risk_level=player.risk_level,
            sample_confidence=player.sample_confidence,
            selection_score=player.selection_score,
            sell_score=sell_score,
            rank=rank,
            reasons=_build_sell_reasons(sell_score, player),
        )
        for rank, (player, sell_score) in enumerate(scored, start=1)
    ]


def rank_buy_candidates(
    pool_analyses: list[SquadPlayerAnalysis],
    position_type: int | None = None,
    limit: int = 10,
) -> list[BuyCandidate]:
    """Rank the strongest deterministic buy candidates from the pool.

    Filters to a position first when given (bounding the ranked set),
    then sorts by the same selection_score used for squad selection so
    buy ranking stays coherent with how starting XI quality is judged.
    """
    candidates = [
        player
        for player in pool_analyses
        if position_type is None or player.position_type == position_type
    ]

    ranked = sorted(
        candidates,
        key=lambda player: player.selection_score,
        reverse=True,
    )[:limit]

    results: list[BuyCandidate] = []

    for rank, player in enumerate(ranked, start=1):
        transfer_score = score_transfer_candidate(
            player_id=player.player_id,
            expected_points=player.expected_points,
            form=player.form,
            fixture_difficulty=player.fixture_difficulty,
            price=player.price,
        )

        results.append(
            BuyCandidate(
                player_id=player.player_id,
                web_name=player.web_name,
                position_type=player.position_type,
                team_id=player.team_id,
                price=player.price,
                expected_points=player.expected_points,
                form=player.form,
                fixture_difficulty=player.fixture_difficulty,
                overall_risk=player.overall_risk,
                availability_risk=player.availability_risk,
                risk_level=player.risk_level,
                sample_confidence=player.sample_confidence,
                selection_score=player.selection_score,
                value_score=transfer_score.value_score,
                rank=rank,
                reasons=_build_buy_reasons(player),
            ),
        )

    return results


def classify_transfer_priority(
    net_improvement: float,
    sell_availability_risk: float,
    buy_availability_risk: float,
) -> str:
    """Classify a transfer pair as essential, strong, optional, or avoid.

    "essential" covers both a large projected gain and the case of
    replacing a doubtful/unavailable player with a fully available one,
    since that risk removal matters regardless of the points delta.
    """
    replaces_unavailable = (
        sell_availability_risk >= 0.8 and buy_availability_risk == 0.0
    )

    if replaces_unavailable or net_improvement >= 2.0:
        return "essential"

    if net_improvement >= 1.0:
        return "strong"

    if net_improvement >= _MIN_WORTHWHILE_IMPROVEMENT:
        return "optional"

    return "avoid"


def _team_composition(
    squad_analyses: list[SquadPlayerAnalysis],
) -> dict[int, int]:
    """Count current squad players per FPL team."""
    counts: dict[int, int] = {}

    for player in squad_analyses:
        counts[player.team_id] = counts.get(player.team_id, 0) + 1

    return counts


def extract_bank_balance(
    entry_history: dict[str, object] | None,
) -> float | None:
    """Extract the manager's remaining bank balance if present.

    FPL reports bank in tenths of a million (e.g. 5 -> 0.5). Returns
    None when the field is absent or not a usable number rather than
    guessing - callers must treat an unknown budget as unknown, not as
    unlimited or zero.
    """
    if not entry_history:
        return None

    bank = entry_history.get("bank")

    if isinstance(bank, bool) or not isinstance(bank, int | float):
        return None

    return round(bank / 10.0, 1)


def build_transfer_pairs(
    sell_candidates: list[SellCandidate],
    pool_analyses: list[SquadPlayerAnalysis],
    squad_analyses: list[SquadPlayerAnalysis],
    entry_bank: float | None = None,
    free_transfers_available: int | None = None,
    max_pairs: int = 5,
    candidates_per_position: int = 10,
) -> list[TransferPair]:
    """Build ranked sell -> buy transfer pairs respecting squad constraints.

    Each sell candidate is matched against the best same-position,
    affordable buy candidate that would not push any FPL team above
    three players in the resulting squad. A candidate that is
    *definitely* unaffordable (entry_bank is known and doesn't cover
    the price change) is skipped in favor of the next-best one, the
    same way an already-used or team-limit-breaking candidate already
    is - an unknown bank is never treated as unaffordable. Pairs below
    the worthwhile-improvement threshold are dropped rather than
    padding the recommendation list.

    `priority` reflects real transfer economics - essential /
    recommended / optional, from net_value and free-transfer coverage
    (see analysis/transfer_economics.py) - when `free_transfers_available`
    is supplied by the caller. No public FPL endpoint exposes a
    manager's free-transfer count (only the authenticated, per-manager
    my-team endpoint does, which this project does not access), so it
    can only come from the manager themselves. When it is not
    supplied, `priority` falls back to the pre-existing
    selection-score-based classification (essential / strong /
    optional via classify_transfer_priority), unchanged from before
    this economics work.
    """
    team_counts = _team_composition(squad_analyses)
    used_buy_ids: set[int] = set()
    pairs: list[TransferPair] = []

    for sell in sell_candidates:
        position_pool = rank_buy_candidates(
            pool_analyses,
            position_type=sell.position_type,
            limit=candidates_per_position,
        )

        best_buy: BuyCandidate | None = None

        for buy in position_pool:
            if buy.player_id in used_buy_ids:
                continue

            if buy.selection_score <= sell.selection_score:
                continue

            projected_team_count = team_counts.get(buy.team_id, 0)
            if buy.team_id != sell.team_id:
                projected_team_count += 1

            if projected_team_count > _MAX_TEAM_PLAYERS:
                continue

            candidate_price_change = round(buy.price - sell.price, 1)
            if entry_bank is not None and candidate_price_change > entry_bank:
                continue

            best_buy = buy
            break

        if best_buy is None:
            continue

        net_improvement = round(
            best_buy.selection_score - sell.selection_score,
            2,
        )
        risk_change = round(sell.overall_risk - best_buy.overall_risk, 2)
        price_change = round(best_buy.price - sell.price, 1)

        legacy_priority = classify_transfer_priority(
            net_improvement=net_improvement,
            sell_availability_risk=sell.availability_risk,
            buy_availability_risk=best_buy.availability_risk,
        )

        if legacy_priority == "avoid":
            continue

        within_budget = (
            None if entry_bank is None else price_change <= entry_bank
        )

        # expected_point_gain never depends on free_transfers_available,
        # so it's always computed - passing 0 when the count is unknown
        # is only a placeholder to satisfy calculate_hit_cost's int
        # parameter; the resulting hit_cost/net_value are discarded
        # below in that case, never exposed as if 0 free transfers were
        # a known fact.
        economics = calculate_transfer_economics(
            sell_expected_points=sell.expected_points,
            buy_expected_points=best_buy.expected_points,
            free_transfers_available=free_transfers_available or 0,
        )

        hit_cost: float | None
        net_value: float | None

        if free_transfers_available is None:
            priority = legacy_priority
            hit_cost = None
            net_value = None
        else:
            priority = classify_transfer_tier(
                net_value=economics.net_value,
                requires_hit=economics.requires_hit,
            )
            hit_cost = economics.hit_cost
            net_value = economics.net_value

        used_buy_ids.add(best_buy.player_id)
        team_counts[sell.team_id] = team_counts.get(sell.team_id, 0) - 1
        team_counts[best_buy.team_id] = (
            team_counts.get(best_buy.team_id, 0) + 1
        )

        pairs.append(
            TransferPair(
                sell=sell,
                buy=best_buy,
                net_improvement=net_improvement,
                risk_change=risk_change,
                price_change=price_change,
                within_budget=within_budget,
                priority=priority,
                reasons=_build_pair_reasons(sell, best_buy),
                expected_point_gain=economics.expected_point_gain,
                hit_cost=hit_cost,
                net_value=net_value,
            ),
        )

        if len(pairs) >= max_pairs:
            break

    return pairs
