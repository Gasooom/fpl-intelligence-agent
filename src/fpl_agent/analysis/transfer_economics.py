from __future__ import annotations

from dataclasses import dataclass

# The same bar transfer_analysis._MIN_WORTHWHILE_IMPROVEMENT already
# uses to decide whether a sell -> buy pair's selection-score
# improvement is worth recommending at all - reused here, on the same
# reasoning, as the minimum real (expected-points) net value for a
# transfer to be classified as more than "optional". A transfer with a
# technically-positive but negligible net value should not be promoted
# to essential/recommended just because it clears zero.
MIN_WORTHWHILE_NET_VALUE = 0.3

# The standard FPL cost of one transfer beyond the manager's free
# allowance.
HIT_COST_PER_PAID_TRANSFER = 4.0

_TIER_ESSENTIAL = "essential"
_TIER_RECOMMENDED = "recommended"
_TIER_OPTIONAL = "optional"


@dataclass(frozen=True)
class TransferEconomics:
    """Deterministic economics for making one transfer.

    `expected_point_gain` is the raw projected points gain from the
    swap (buy.expected_points - sell.expected_points) - independent of
    cost. `hit_cost` is the points lost to paying for transfers beyond
    the manager's free allowance, always represented as a positive
    cost (never a signed adjustment). `net_value` is what's left after
    that cost - the number that should actually drive whether a
    transfer is worth making, not the raw gain alone.
    """

    expected_point_gain: float
    hit_cost: float
    net_value: float
    requires_hit: bool


def calculate_hit_cost(transfer_count: int, free_transfers_available: int) -> float:
    """Deterministic FPL hit-cost formula for making `transfer_count` transfers.

    free_transfers_used = min(transfer_count, free_transfers_available)
    paid_transfers = max(0, transfer_count - free_transfers_available)
    hit_cost = paid_transfers * 4

    Always a non-negative cost - callers subtract it explicitly rather
    than adding a signed value, so it can never be subtracted twice by
    accident.
    """
    paid_transfers = max(0, transfer_count - free_transfers_available)
    return paid_transfers * HIT_COST_PER_PAID_TRANSFER


def calculate_transfer_economics(
    sell_expected_points: float,
    buy_expected_points: float,
    free_transfers_available: int,
    transfer_count: int = 1,
) -> TransferEconomics:
    """Calculate the real economics of making one recommended transfer.

    This project does not model bundled multi-transfer plans - every
    TransferPair is evaluated as the single transfer a manager would be
    making if they acted on it alone (`transfer_count` defaults to 1,
    matching how `best_transfer`/`transfer_recommendations` already
    present each pair as its own independent option, never a combined
    package). `calculate_hit_cost` itself is general for any transfer
    count, for callers that do have one.
    """
    hit_cost = calculate_hit_cost(transfer_count, free_transfers_available)
    expected_point_gain = round(buy_expected_points - sell_expected_points, 2)
    net_value = round(expected_point_gain - hit_cost, 2)

    return TransferEconomics(
        expected_point_gain=expected_point_gain,
        hit_cost=hit_cost,
        net_value=net_value,
        requires_hit=hit_cost > 0.0,
    )


def classify_transfer_tier(net_value: float, requires_hit: bool) -> str:
    """Classify a transfer's priority from its real economics.

    ESSENTIAL: net_value clears MIN_WORTHWHILE_NET_VALUE and is fully
    covered by free transfers (no hit needed).
    RECOMMENDED: net_value clears the same bar but needs at least one
    paid transfer to make.
    OPTIONAL: net_value is zero, negative, or below the worthwhile bar
    - a technically-positive but marginal gain never counts as
    essential or recommended on its own.
    """
    if net_value < MIN_WORTHWHILE_NET_VALUE:
        return _TIER_OPTIONAL

    return _TIER_RECOMMENDED if requires_hit else _TIER_ESSENTIAL
