import pytest

from devig import devig


def test_even_market_is_fifty_fifty():
    # -110 / -110 (1.909091 each): same price both sides, so 50 / 50 once the vig is out
    assert devig([1 + 100 / 110, 1 + 100 / 110]) == pytest.approx([0.5, 0.5])


def test_power_recovers_known_probabilities():
    # Power model: implied = fair ** k. Take fair 0.6 / 0.4 and k = 0.95:
    # 0.6 ** 0.95 = 0.615522 -> odds 1.624637, 0.4 ** 0.95 = 0.418752 -> odds 2.388048.
    # Implied total 1.034274, so there's 3.4% vig. Devig must give back 0.6 / 0.4.
    odds = [1.624637, 2.388048]
    assert sum(1 / o for o in odds) == pytest.approx(1.034274, abs=1e-5)
    assert devig(odds) == pytest.approx([0.6, 0.4], abs=1e-5)


def test_power_three_way_recovers_known_probabilities():
    # Soccer-style three-way market built the same way: fair 0.5 / 0.3 / 0.2, k = 0.9
    true_probs = [0.5, 0.3, 0.2]
    odds = [1 / (p ** 0.9) for p in true_probs]
    assert devig(odds) == pytest.approx(true_probs, abs=1e-6)


def test_power_puts_more_vig_on_the_longshot():
    # 1.50 / 2.60. Splitting the vig in proportion would give the favourite 0.634146.
    # Power leaves the favourite more than that, because books shade longshots harder.
    fair = devig([1.5, 2.6])
    assert sum(fair) == pytest.approx(1.0)
    assert fair[0] > 0.634146


@pytest.mark.parametrize("bad", [[], [2.0], [1.0, 2.0], [0.5, 3.0]])
def test_rejects_bad_prices(bad):
    with pytest.raises(ValueError):
        devig(bad)


def test_odds_near_one_still_sum_to_one():
    # 1.0001 each side means k is about 6931, far past the old search bound of 100,
    # which gave 0.99 + 0.99 = 1.98. The answer must still be a fair 50 / 50.
    fair = devig([1.0001, 1.0001])
    assert sum(fair) == pytest.approx(1.0, abs=1e-6)
    assert fair == pytest.approx([0.5, 0.5], abs=1e-6)
