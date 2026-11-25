#devig.py
# Turn one book's decimal odds for a full market into fair (no-vig) probabilities.
#
# Power method: find k so that (1/odds_1)**k + (1/odds_2)**k + ... = 1, then the
# fair chance of each outcome is (1/odds_i)**k. It puts more of the vig on the
# longshot, which is how books actually shade lines (the favourite-longshot bias).
# The plain "divide by the total" version is OddsCalculator.calculate_no_vig_probabilities.
#
# No PyPI package was worth adding for this: penaltyblog has a power devig but
# pulls in numpy, scipy and pandas for about 15 lines of math.


def devig(odds):
    """
    :param odds: list of decimal odds, one per outcome, covering the whole market
    :return: list of fair probabilities in the same order, summing to 1
    """
    if len(odds) < 2:
        raise ValueError("Need prices for at least two outcomes to remove the vig")
    if any(price <= 1 for price in odds):
        raise ValueError("Decimal odds must be greater than 1")

    implied = [1 / price for price in odds]

    # sum(p**k) falls as k grows (every p is below 1): it is n - 1 above zero at
    # k = 0 and heads to -1 for big k, so bisection finds the one k where it is 0.
    lo, hi = 0.0, 100.0
    for _ in range(200):
        k = (lo + hi) / 2
        if sum(p ** k for p in implied) > 1:
            lo = k
        else:
            hi = k
    k = (lo + hi) / 2
    return [p ** k for p in implied]
