import pytest

from conftest import EVENT_ID
from devig import devig
from fair_price import evaluate, fair_probability, find_event

HENRYS_BOOKS = ["draftkings", "fanduel", "betmgm"]

CELTICS_BOOST = {
    "book": "fanduel",
    "sport_key": "basketball_nba",
    "event": "Celtics @ Lakers",
    "market": "h2h",
    "selection": "Boston Celtics",
    "promo_type": "profit_boost",
    "boost_pct": 50,
    "max_stake": 50,
}


# ---------- finding the game ----------

@pytest.mark.parametrize("text", ["Celtics @ Lakers", "lakers vs celtics", "Celtics", "Boston Celtics v LA Lakers"])
def test_find_event_by_team_names(sample_event, text):
    assert find_event([sample_event], text)["id"] == EVENT_ID


def test_find_event_no_match(sample_event):
    with pytest.raises(LookupError, match="Knicks"):
        find_event([sample_event], "Knicks @ Nets")


# ---------- fair price ----------

def test_fair_probability_prefers_pinnacle(sample_event):
    prob, source = fair_probability(sample_event, "h2h", "Boston Celtics", None)
    assert prob == pytest.approx(devig([1.5, 2.6])[1])
    assert source == "pinnacle"


def test_fair_probability_falls_back_to_consensus(sample_event):
    # Pinnacle's total is 220.5 but the NY books are at 221.5, so average the books at 221.5
    prob, source = fair_probability(sample_event, "totals", "Over", 221.5)
    expected = (devig([1.91, 1.91])[0] + devig([1.87, 1.95])[0]) / 2
    assert prob == pytest.approx(expected)
    assert source == "consensus of 2 books"


def test_fair_probability_none_when_no_full_market(sample_event):
    assert fair_probability(sample_event, "totals", "Over", 230.5) == (None, None)


# ---------- evaluating a promo ----------

def test_evaluate_profit_boost(sample_event):
    # FanDuel Celtics 2.70 with a 50% profit boost = 1 + 1.70 * 1.5 = 3.55.
    # Best Lakers price across Henry's books: FanDuel 1.48.
    # Hedge = 50 * 3.55 / 1.48 = 119.93. Locked = 177.50 - 50 - 119.93 = 7.57.
    result = evaluate(CELTICS_BOOST, sample_event, HENRYS_BOOKS)
    fair = devig([1.5, 2.6])[1]
    assert result["base_odds"] == 2.70
    assert result["effective_odds"] == pytest.approx(3.55)
    assert result["hedge_book"] == "FanDuel"
    assert result["hedge_selection"] == "Los Angeles Lakers"
    assert result["hedge_odds"] == 1.48
    assert result["hedge_stake"] == pytest.approx(119.93, abs=0.005)
    assert result["locked_profit"] == pytest.approx(7.57, abs=0.005)
    assert result["ev"] == pytest.approx(round(50 * (fair * 3.55 - 1), 2))
    assert result["fair_source"] == "pinnacle"
    assert result["event_id"] == EVENT_ID
    assert result["event_name"] == "Boston Celtics @ Los Angeles Lakers"
    assert result["flags"] == []


def test_evaluate_bonus_bet_uses_book_price(sample_event):
    # $100 bonus on Celtics at BetMGM 2.80. Hedge Lakers 1.48 at FanDuel.
    # Hedge = 100 * 1.80 / 1.48 = 121.62. Locked = 180 - 121.62 = 58.38, 58.38% of face.
    promo = dict(CELTICS_BOOST, book="BetMGM", promo_type="bonus_bet_stake_not_returned",
                 boost_pct=None, max_stake=100)
    result = evaluate(promo, sample_event, HENRYS_BOOKS)
    assert result["effective_odds"] == 2.80
    assert result["hedge_stake"] == pytest.approx(121.62, abs=0.005)
    assert result["locked_profit"] == pytest.approx(58.38, abs=0.005)
    assert result["conversion_pct"] == pytest.approx(58.38, abs=0.005)


def test_evaluate_totals_hedges_the_under_at_same_line(sample_event):
    promo = dict(CELTICS_BOOST, book="draftkings", market="totals", selection="Over", point=221.5,
                 promo_type="odds_boost", boost_pct=None, boosted_odds=2.2, max_stake=25)
    result = evaluate(promo, sample_event, ["draftkings", "fanduel"])
    assert result["hedge_selection"] == "Under"
    assert result["hedge_odds"] == 1.95
    assert result["hedge_book"] == "FanDuel"


def test_evaluate_spread_hedges_other_team_at_opposite_point(sample_event):
    promo = dict(CELTICS_BOOST, book="draftkings", market="spreads", selection="Boston Celtics", point=4.5,
                 promo_type="odds_boost", boost_pct=None, boosted_odds=2.3, max_stake=25)
    result = evaluate(promo, sample_event, ["draftkings"])
    assert result["hedge_selection"] == "Los Angeles Lakers"
    assert result["hedge_odds"] == 1.91
    assert result["fair_source"] == "pinnacle"


def test_evaluate_spread_needs_a_point(sample_event):
    promo = dict(CELTICS_BOOST, market="spreads")
    with pytest.raises(ValueError, match="point"):
        evaluate(promo, sample_event, HENRYS_BOOKS)


def test_evaluate_no_opposite_side_in_three_way_market(soccer_event):
    promo = dict(CELTICS_BOOST, sport_key="soccer_epl", promo_type="odds_boost",
                 boost_pct=None, boosted_odds=4.5)
    result = evaluate(promo, soccer_event, ["fanduel"])
    assert result["hedge_stake"] is None
    assert result["locked_profit"] is None
    assert "no_opposite_price" in result["flags"]
    assert result["ev"] is not None  # three-way devig still gives a fair price


def test_evaluate_hedge_too_short_flags_negative(sample_event):
    # Boosted only to 2.60 on Celtics; best Lakers hedge 1.48 -> 130 / 1.48 = 87.84, locked -7.84
    promo = dict(CELTICS_BOOST, promo_type="odds_boost", boost_pct=None, boosted_odds=2.6)
    result = evaluate(promo, sample_event, HENRYS_BOOKS)
    assert result["locked_profit"] == pytest.approx(-7.84, abs=0.005)
    assert "hedge_loses_money" in result["flags"]


def test_evaluate_stake_over_max_is_capped(sample_event):
    result = evaluate(dict(CELTICS_BOOST, stake=200), sample_event, ["fanduel"])
    assert result["stake"] == 50
    assert "stake_capped_at_max" in result["flags"]


def test_evaluate_without_books_flags_it(sample_event):
    result = evaluate(CELTICS_BOOST, sample_event, [])
    assert result["hedge_stake"] is None
    assert result["flags"] == ["books_not_set"]


def test_evaluate_boost_pct_needs_the_book_price(sample_event):
    promo = dict(CELTICS_BOOST, book="caesars")  # not in this game's data
    with pytest.raises(ValueError, match="normal price"):
        evaluate(promo, sample_event, ["fanduel"])
