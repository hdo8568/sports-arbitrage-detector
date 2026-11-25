import pytest

from promo_math import effective_odds, expected_value, hedge, promo_stake

# Hand-worked examples. American to decimal: -110 = 1.909091, -120 = 1.833333, -350 = 1.285714.


# ---------- effective odds ----------

def test_profit_boost_from_percent():
    # +100 (2.0) with a 50% profit boost: profit 1.00 becomes 1.50, so odds 2.50
    assert effective_odds("profit_boost", boost_pct=50, base_odds=2.0) == pytest.approx(2.5)


def test_profit_boost_from_percent_on_minus_110():
    # -110 pays 0.909091 profit; 25% boost makes it 1.136364, odds 2.136364
    assert effective_odds("profit_boost", boost_pct=25, base_odds=1 + 100 / 110) == pytest.approx(2.136364, abs=1e-6)


def test_boosted_odds_given_directly_win():
    assert effective_odds("odds_boost", boosted_odds=2.5, base_odds=2.0) == 2.5


def test_bonus_bet_uses_book_price_when_no_odds_given():
    assert effective_odds("bonus_bet_stake_not_returned", base_odds=4.0) == 4.0


def test_needs_some_odds():
    with pytest.raises(ValueError):
        effective_odds("profit_boost")
    with pytest.raises(ValueError):
        effective_odds("profit_boost", boost_pct=50)  # percent but no base price


def test_bonus_bet_does_not_take_a_boost_percent():
    with pytest.raises(ValueError):
        effective_odds("bonus_bet_stake_not_returned", boost_pct=50, base_odds=2.0)


def test_unknown_promo_type():
    with pytest.raises(ValueError):
        effective_odds("free_money", boosted_odds=2.0)


# ---------- stake cap ----------

def test_stake_defaults_to_max():
    assert promo_stake(50) == (50, [])


def test_stake_over_max_is_capped_and_flagged():
    assert promo_stake(50, 80) == (50, ["stake_capped_at_max"])


def test_stake_under_max_is_kept():
    assert promo_stake(50, 20) == (20, [])


def test_stake_must_be_positive():
    with pytest.raises(ValueError):
        promo_stake(0)
    with pytest.raises(ValueError):
        promo_stake(50, -5)


# ---------- hedge ----------

def test_profit_boost_hedge_hand_worked():
    # $50 at boosted 2.50, hedge the other side at -110.
    # Hedge stake = 50 * 2.5 / 1.909091 = 65.48
    # Promo wins: 125 - 50 - 65.48 = 9.52. Hedge wins: 65.48 * 0.909091 - 50 = 9.52.
    result = hedge("profit_boost", 50, 2.5, 1 + 100 / 110)
    assert result["hedge_stake"] == pytest.approx(65.48, abs=0.005)
    assert result["locked_profit"] == pytest.approx(9.52, abs=0.005)
    assert result["conversion_pct"] is None
    assert result["flags"] == []


def test_odds_boost_hedge_hand_worked():
    # $25 at boosted 2.50, hedge at -120 (1.833333).
    # Hedge stake = 62.5 / 1.833333 = 34.09. Locked = 62.5 - 25 - 34.09 = 3.41.
    result = hedge("odds_boost", 25, 2.5, 1 + 100 / 120)
    assert result["hedge_stake"] == pytest.approx(34.09, abs=0.005)
    assert result["locked_profit"] == pytest.approx(3.41, abs=0.005)


def test_bonus_bet_hedge_hand_worked():
    # $100 bonus bet at +300 (4.0), stake not returned. Hedge at -350 (1.285714).
    # Hedge stake = 100 * 3 / 1.285714 = 233.33. Bonus wins: 300 - 233.33 = 66.67.
    # Hedge wins: 233.33 * 0.285714 = 66.67. That's 66.67% of the $100 face value.
    result = hedge("bonus_bet_stake_not_returned", 100, 4.0, 1 + 100 / 350)
    assert result["hedge_stake"] == pytest.approx(233.33, abs=0.005)
    assert result["locked_profit"] == pytest.approx(66.67, abs=0.005)
    assert result["conversion_pct"] == pytest.approx(66.67, abs=0.005)


def test_hedge_too_short_reports_negative_and_flags():
    # $100 at 2.00 with the hedge only at 1.80: hedge 111.11, lose 11.11 either way.
    result = hedge("odds_boost", 100, 2.0, 1.8)
    assert result["hedge_stake"] == pytest.approx(111.11, abs=0.005)
    assert result["locked_profit"] == pytest.approx(-11.11, abs=0.005)
    assert "hedge_loses_money" in result["flags"]


def test_no_opposite_price():
    result = hedge("profit_boost", 50, 2.5, None)
    assert result["hedge_stake"] is None
    assert result["locked_profit"] is None
    assert result["flags"] == ["no_opposite_price"]


# ---------- expected value ----------

def test_ev_cash_promo():
    # $50 at 2.50 with a fair 50% chance: 0.5 * 75 - 0.5 * 50 = 12.50
    assert expected_value("profit_boost", 50, 2.5, 0.5) == pytest.approx(12.5)


def test_ev_bonus_bet_stake_not_returned():
    # $100 bonus at 4.0, fair 22%: 0.22 * 300 = 66.00 (nothing lost when it loses)
    assert expected_value("bonus_bet_stake_not_returned", 100, 4.0, 0.22) == pytest.approx(66.0)


def test_ev_without_fair_probability_is_none():
    assert expected_value("profit_boost", 50, 2.5, None) is None
