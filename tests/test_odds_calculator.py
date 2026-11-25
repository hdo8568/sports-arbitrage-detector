import pytest

from odds_calculator import OddsCalculator


def test_american_to_decimal():
    assert OddsCalculator.american_to_decimal(150) == pytest.approx(2.50)
    assert OddsCalculator.american_to_decimal(-150) == pytest.approx(1.6667, abs=1e-4)
    assert OddsCalculator.american_to_decimal(100) == pytest.approx(2.0)


def test_decimal_to_american():
    assert OddsCalculator.decimal_to_american(2.50) == 150
    assert OddsCalculator.decimal_to_american(1.50) == -200
    assert OddsCalculator.decimal_to_american(2.0) == 100


def test_decimal_to_american_rejects_bad_odds():
    with pytest.raises(ValueError):
        OddsCalculator.decimal_to_american(1.0)


def test_convert_odds_round_trip():
    dec = OddsCalculator.convert_odds(-110, "american", "decimal")
    assert OddsCalculator.convert_odds(dec, "decimal", "american") == -110


def test_implied_probability():
    assert OddsCalculator.calculate_implied_probability(2.0) == pytest.approx(0.5)
    assert OddsCalculator.calculate_implied_probability(-110, "american") == pytest.approx(110 / 210)


def test_no_vig_removes_the_juice():
    # Both sides at -110: implied 52.38% each, fair is 50/50
    p = 110 / 210
    implied = {"Lakers": p, "Celtics": p}
    fair = OddsCalculator.calculate_no_vig_probabilities(implied)
    assert fair["Lakers"] == pytest.approx(0.5)
    assert sum(fair.values()) == pytest.approx(1.0)
    assert OddsCalculator.calculate_vig(implied) == pytest.approx(2 * p - 1)


def test_no_vig_uneven_market():
    implied = {"A": 0.6, "B": 0.5}  # 10% overround
    fair = OddsCalculator.calculate_no_vig_probabilities(implied)
    assert fair["A"] == pytest.approx(0.6 / 1.1)
    assert fair["B"] == pytest.approx(0.5 / 1.1)


def test_no_vig_rejects_empty():
    with pytest.raises(ValueError):
        OddsCalculator.calculate_no_vig_probabilities({})
