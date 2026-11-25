#kelly.py
# Bet sizing.
#
# 1. Kelly criterion for a single +EV bet.
#    b = decimal odds - 1 (what you win per $1), p = fair win probability, q = 1 - p.
#    Full Kelly says bet  f = (b*p - q) / b  of your bankroll.
#    Full Kelly swings hard, so we default to a quarter of it (fraction = 0.25).
#    If the edge is zero or negative, the answer is 0: don't bet.
#
# 2. Stake split for a two-way arbitrage.
#    Put stake_i = total * (1/odds_i) / (1/odds_home + 1/odds_away) on each side,
#    so the payout is the same whichever team wins.

from odds_calculator import OddsCalculator


def kelly_fraction(odds, prob):
    """
    Full Kelly fraction of bankroll for one bet.
    :param odds: decimal odds (e.g. 2.10)
    :param prob: fair win probability, 0 to 1
    :return: fraction of bankroll to bet (0 when there is no edge)
    """
    if odds <= 1:
        raise ValueError("Decimal odds must be greater than 1")
    if prob < 0 or prob > 1:
        raise ValueError("Probability must be between 0 and 1")

    b = odds - 1
    q = 1 - prob
    f = (b * prob - q) / b
    return max(f, 0.0)


def kelly_stake(odds, prob, bankroll, fraction=0.25):
    """
    Dollar stake using fractional Kelly.
    :param fraction: share of full Kelly to bet (1.0 = full Kelly, 0.25 = quarter Kelly)
    :return: dict with full Kelly fraction, the fraction used, and the stake in dollars
    """
    if bankroll < 0:
        raise ValueError("Bankroll can't be negative")
    if fraction <= 0 or fraction > 1:
        raise ValueError("Fraction must be above 0 and at most 1")

    full = kelly_fraction(odds, prob)
    used = full * fraction
    return {
        "full_kelly_fraction": round(full, 6),
        "fraction_of_bankroll": round(used, 6),
        "stake": round(bankroll * used, 2),
        "edge": round(prob * odds - 1, 6),  # expected profit per $1 bet
    }


def fair_probability(odds_by_team, team):
    """
    Fair (no-vig) win probability for one team, using the existing
    OddsCalculator math. odds_by_team is one book's decimal odds,
    e.g. {"Lakers": 1.91, "Celtics": 1.91}.
    """
    implied = {
        name: OddsCalculator.calculate_implied_probability(price)
        for name, price in odds_by_team.items()
    }
    no_vig = OddsCalculator.calculate_no_vig_probabilities(implied)
    return no_vig[team]


def arbitrage_stakes(home_odds, away_odds, total_stake=100.0):
    """
    Split total_stake across both sides so the payout is equal either way.
    :return: dict with home stake, away stake, payout and profit
    """
    if home_odds <= 1 or away_odds <= 1:
        raise ValueError("Decimal odds must be greater than 1")
    if total_stake < 0:
        raise ValueError("Total stake can't be negative")

    inv_home = 1 / home_odds
    inv_away = 1 / away_odds
    total_inv = inv_home + inv_away

    home_stake = total_stake * inv_home / total_inv
    away_stake = total_stake * inv_away / total_inv
    payout = total_stake / total_inv  # same as home_stake * home_odds

    return {
        "total_stake": round(total_stake, 2),
        "home": round(home_stake, 2),
        "away": round(away_stake, 2),
        "payout": round(payout, 2),
        "profit": round(payout - total_stake, 2),
    }
