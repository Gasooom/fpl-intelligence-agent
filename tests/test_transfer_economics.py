from __future__ import annotations

from fpl_agent.analysis.transfer_economics import (
    MIN_WORTHWHILE_NET_VALUE,
    calculate_hit_cost,
    calculate_transfer_economics,
    classify_transfer_tier,
)

# --- calculate_hit_cost ----------------------------------------------------


def test_one_free_transfer_one_transfer_costs_nothing() -> None:
    """Case 1: the transfer is covered by the free allowance."""
    assert calculate_hit_cost(transfer_count=1, free_transfers_available=1) == 0.0


def test_zero_free_transfers_one_transfer_costs_one_hit() -> None:
    """Case 2: the single transfer has to be paid for."""
    assert calculate_hit_cost(transfer_count=1, free_transfers_available=0) == 4.0


def test_zero_free_transfers_two_transfers_cost_two_hits() -> None:
    """Case 3: both transfers are paid."""
    assert calculate_hit_cost(transfer_count=2, free_transfers_available=0) == 8.0


def test_two_free_transfers_two_transfers_cost_nothing() -> None:
    """Case 4: the free allowance exactly covers both."""
    assert calculate_hit_cost(transfer_count=2, free_transfers_available=2) == 0.0


def test_more_transfers_than_free_transfers_only_charges_the_excess() -> None:
    assert calculate_hit_cost(transfer_count=3, free_transfers_available=1) == 8.0


def test_spare_free_transfers_are_never_a_negative_cost() -> None:
    """Unused free transfers never become a discount - a hit cost is
    always a non-negative amount of points lost."""
    assert calculate_hit_cost(transfer_count=1, free_transfers_available=5) == 0.0
    assert calculate_hit_cost(transfer_count=0, free_transfers_available=2) == 0.0


# --- calculate_transfer_economics ------------------------------------------


def test_net_value_equals_gain_minus_hit_cost_with_a_free_transfer() -> None:
    economics = calculate_transfer_economics(
        sell_expected_points=1.0,
        buy_expected_points=8.0,
        free_transfers_available=1,
    )

    assert economics.expected_point_gain == 7.0
    assert economics.hit_cost == 0.0
    assert economics.net_value == 7.0
    assert economics.requires_hit is False


def test_net_value_equals_gain_minus_hit_cost_when_a_hit_is_needed() -> None:
    """The worked example from the spec: gain 7.0, cost 4.0, net 3.0 -
    the cost is subtracted exactly once, never double-counted."""
    economics = calculate_transfer_economics(
        sell_expected_points=1.0,
        buy_expected_points=8.0,
        free_transfers_available=0,
    )

    assert economics.expected_point_gain == 7.0
    assert economics.hit_cost == 4.0
    assert economics.net_value == 3.0
    assert economics.requires_hit is True


def test_gain_smaller_than_the_hit_cost_produces_a_negative_net_value() -> None:
    """Case 5: a positive raw gain that does not cover the hit."""
    economics = calculate_transfer_economics(
        sell_expected_points=4.0,
        buy_expected_points=6.0,
        free_transfers_available=0,
    )

    assert economics.expected_point_gain == 2.0
    assert economics.hit_cost == 4.0
    assert economics.net_value == -2.0


def test_net_value_can_be_exactly_zero() -> None:
    """Boundary: a gain that exactly cancels the hit cost."""
    economics = calculate_transfer_economics(
        sell_expected_points=2.0,
        buy_expected_points=6.0,
        free_transfers_available=0,
    )

    assert economics.expected_point_gain == 4.0
    assert economics.hit_cost == 4.0
    assert economics.net_value == 0.0


def test_a_downgrade_produces_a_negative_expected_point_gain() -> None:
    economics = calculate_transfer_economics(
        sell_expected_points=8.0,
        buy_expected_points=5.0,
        free_transfers_available=1,
    )

    assert economics.expected_point_gain == -3.0
    assert economics.hit_cost == 0.0
    assert economics.net_value == -3.0


def test_multiple_transfers_are_costed_against_the_shared_allowance() -> None:
    economics = calculate_transfer_economics(
        sell_expected_points=1.0,
        buy_expected_points=8.0,
        free_transfers_available=0,
        transfer_count=2,
    )

    assert economics.hit_cost == 8.0
    assert economics.net_value == -1.0


# --- classify_transfer_tier ------------------------------------------------


def test_positive_net_value_covered_by_free_transfers_is_essential() -> None:
    """Case 1's tier."""
    assert classify_transfer_tier(net_value=7.0, requires_hit=False) == "essential"


def test_positive_net_value_requiring_a_hit_is_recommended() -> None:
    """Case 2's tier: still worth doing, but it costs something."""
    assert classify_transfer_tier(net_value=3.0, requires_hit=True) == "recommended"


def test_negative_net_value_is_optional_even_without_a_hit() -> None:
    assert classify_transfer_tier(net_value=-2.0, requires_hit=False) == "optional"
    assert classify_transfer_tier(net_value=-2.0, requires_hit=True) == "optional"


def test_zero_net_value_is_optional() -> None:
    """Boundary: breaking even is not a reason to act."""
    assert classify_transfer_tier(net_value=0.0, requires_hit=False) == "optional"
    assert classify_transfer_tier(net_value=0.0, requires_hit=True) == "optional"


def test_marginal_positive_net_value_is_optional_not_essential() -> None:
    """A raw positive gain must never automatically mean "essential" -
    it has to clear the worthwhile bar first."""
    marginal = MIN_WORTHWHILE_NET_VALUE / 2

    assert classify_transfer_tier(net_value=marginal, requires_hit=False) == "optional"


def test_exactly_at_the_worthwhile_threshold_is_not_marginal() -> None:
    """Boundary: the threshold itself counts as worthwhile."""
    assert (
        classify_transfer_tier(net_value=MIN_WORTHWHILE_NET_VALUE, requires_hit=False)
        == "essential"
    )
    assert (
        classify_transfer_tier(net_value=MIN_WORTHWHILE_NET_VALUE, requires_hit=True)
        == "recommended"
    )
