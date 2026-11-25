#promo_math.py
# The money math for one sportsbook promo. No network, no database.
#
# Promo types:
#   profit_boost                  cash bet, the profit part of the payout is boosted
#   odds_boost                    cash bet at a boosted price
#   bonus_bet_stake_not_returned  free bet: a win pays only the profit, the stake is gone
#
# Hedge (bet the other side so you make the same money either way):
#   S = promo stake, E = promo decimal odds, H = hedge decimal odds, h = hedge stake
#   cash promo:  promo wins S*E - S - h,  hedge wins h*H - h - S   ->  h = S*E / H
#   bonus bet:   promo wins S*(E-1) - h,  hedge wins h*(H-1)       ->  h = S*(E-1) / H

PROMO_TYPES = ("profit_boost", "odds_boost", "bonus_bet_stake_not_returned")
BONUS = "bonus_bet_stake_not_returned"


def _check_type(promo_type):
    if promo_type not in PROMO_TYPES:
        raise ValueError(f"Unknown promo type '{promo_type}'. Use one of {', '.join(PROMO_TYPES)}.")


def effective_odds(promo_type, boosted_odds=None, boost_pct=None, base_odds=None):
    """
    Decimal odds the promo actually pays.
    :param boosted_odds: the boosted price, if the book shows it
    :param boost_pct: profit boost in percent (50 means profit x 1.5), applied to base_odds
    :param base_odds: the book's normal price for the selection
    """
    _check_type(promo_type)
    if promo_type == BONUS and boost_pct is not None:
        raise ValueError("A bonus bet has no boost percent; give its odds instead")
    if boosted_odds is not None:
        return boosted_odds
    if boost_pct is not None:
        if base_odds is None:
            raise ValueError("Boost percent needs the book's normal price, and none was found")
        return 1 + (base_odds - 1) * (1 + boost_pct / 100)
    if promo_type == BONUS and base_odds is not None:
        return base_odds
    raise ValueError("Give the boosted odds or the boost percent")


def promo_stake(max_stake, stake=None):
    """Stake to use: the max unless a smaller stake is asked for. Over the max is capped."""
    if max_stake <= 0 or (stake is not None and stake <= 0):
        raise ValueError("Stake must be more than 0")
    if stake is None:
        return max_stake, []
    if stake > max_stake:
        return max_stake, ["stake_capped_at_max"]
    return stake, []


def hedge(promo_type, stake, odds, hedge_odds):
    """
    Hedge stake that locks the same profit on both outcomes.
    :return: dict with hedge_stake, locked_profit, conversion_pct (bonus bets only), flags
    """
    _check_type(promo_type)
    if hedge_odds is None:
        return {"hedge_stake": None, "locked_profit": None, "conversion_pct": None,
                "flags": ["no_opposite_price"]}

    if promo_type == BONUS:
        hedge_stake = stake * (odds - 1) / hedge_odds
        locked = stake * (odds - 1) - hedge_stake
        conversion = round(100 * locked / stake, 2)
    else:
        hedge_stake = stake * odds / hedge_odds
        locked = stake * odds - stake - hedge_stake
        conversion = None

    flags = ["hedge_loses_money"] if locked < 0 else []
    return {
        "hedge_stake": round(hedge_stake, 2),
        "locked_profit": round(locked, 2),
        "conversion_pct": conversion,
        "flags": flags,
    }


def expected_value(promo_type, stake, odds, fair_prob):
    """Expected profit in dollars of the promo bet alone (no hedge). None without a fair price."""
    _check_type(promo_type)
    if fair_prob is None:
        return None
    if promo_type == BONUS:
        return round(fair_prob * stake * (odds - 1), 2)
    return round(stake * (fair_prob * odds - 1), 2)
