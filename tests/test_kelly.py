import pytest

from kelly import arbitrage_stakes, fair_probability, kelly_fraction, kelly_stake


# Textbook Kelly values: f = (b*p - q) / b with b = decimal odds - 1

def test_kelly_even_money_60_percent():
    # Even money (2.0), 60% to win: f = (0.6 - 0.4) / 1 = 0.20
    assert kelly_fraction(2.0, 0.6) == pytest.approx(0.20)


def test_kelly_plus_200_40_percent():
    # +200 (3.0), 40% to win: f = (2*0.4 - 0.6) / 2 = 0.10
    assert kelly_fraction(3.0, 0.4) == pytest.approx(0.10)


def test_kelly_zero_edge_is_zero():
    # Fair coin at even money: no edge
    assert kelly_fraction(2.0, 0.5) == 0
    assert kelly_stake(2.0, 0.5, 1000)["stake"] == 0


def test_kelly_negative_edge_is_zero():
    assert kelly_fraction(1.91, 0.5) == 0
    assert kelly_stake(1.91, 0.5, 1000, fraction=1.0)["stake"] == 0


def test_kelly_full_stake():
    result = kelly_stake(2.0, 0.6, 1000, fraction=1.0)
    assert result["stake"] == pytest.approx(200.0)
    assert result["edge"] == pytest.approx(0.2)


def test_kelly_quarter_is_default():
    # Quarter Kelly of 20% is 5% of a $1,000 bankroll = $50
    result = kelly_stake(2.0, 0.6, 1000)
    assert result["full_kelly_fraction"] == pytest.approx(0.20)
    assert result["fraction_of_bankroll"] == pytest.approx(0.05)
    assert result["stake"] == pytest.approx(50.0)


def test_kelly_half():
    assert kelly_stake(3.0, 0.4, 500, fraction=0.5)["stake"] == pytest.approx(25.0)


def test_kelly_rejects_bad_inputs():
    with pytest.raises(ValueError):
        kelly_fraction(1.0, 0.5)
    with pytest.raises(ValueError):
        kelly_fraction(2.0, 1.5)
    with pytest.raises(ValueError):
        kelly_stake(2.0, 0.6, 1000, fraction=0)
    with pytest.raises(ValueError):
        kelly_stake(2.0, 0.6, -5)


def test_fair_probability_uses_no_vig():
    # -110 both ways (1.909...) is a 50/50 market once the vig is removed
    dec = 1 + 100 / 110
    assert fair_probability({"Lakers": dec, "Celtics": dec}, "Lakers") == pytest.approx(0.5)


def test_fair_probability_feeds_kelly():
    # Sharp book says 1.80 / 2.10. Fair prob for the dog, then Kelly at a softer 2.30.
    p = fair_probability({"Fav": 1.80, "Dog": 2.10}, "Dog")
    assert p == pytest.approx((1 / 2.10) / (1 / 1.80 + 1 / 2.10))
    assert kelly_fraction(2.30, p) > 0
    assert kelly_fraction(2.10, p) == 0  # no edge at the sharp book's own price


# Arbitrage stake split

def test_arbitrage_split_equal_payout():
    stakes = arbitrage_stakes(2.10, 2.05, 100)
    assert stakes["home"] + stakes["away"] == pytest.approx(100, abs=0.01)
    assert stakes["home"] * 2.10 == pytest.approx(stakes["payout"], abs=0.02)
    assert stakes["away"] * 2.05 == pytest.approx(stakes["payout"], abs=0.02)
    assert stakes["profit"] > 0


def test_arbitrage_split_known_values():
    # 2.10 / 2.05: payout = 100 / (1/2.10 + 1/2.05) = 103.73
    stakes = arbitrage_stakes(2.10, 2.05, 100)
    assert stakes["home"] == pytest.approx(49.40, abs=0.01)
    assert stakes["away"] == pytest.approx(50.60, abs=0.01)
    assert stakes["payout"] == pytest.approx(103.73, abs=0.01)
    assert stakes["profit"] == pytest.approx(3.73, abs=0.01)


def test_arbitrage_split_long_shot():
    # Big favourite vs big underdog still pays the same both ways
    stakes = arbitrage_stakes(1.29, 19.0, 1000)
    assert stakes["home"] * 1.29 == pytest.approx(stakes["away"] * 19.0, abs=0.1)


def test_arbitrage_split_rejects_bad_odds():
    with pytest.raises(ValueError):
        arbitrage_stakes(1.0, 2.0)
