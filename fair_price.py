#fair_price.py
# Pure functions over one game in The Odds API format. No network, no database.
#
#   find_event        pick the game that matches "Celtics @ Lakers" from a list
#   fair_probability  fair chance of a selection: Pinnacle devigged if it has the
#                     same line, else the average of every book that has it
#   evaluate          one promo -> price, EV, best hedge at Henry's books, locked profit

from datetime import datetime, timedelta, timezone

from devig import devig
from promo_math import effective_odds, expected_value, hedge, promo_stake

MARKETS = ("h2h", "spreads", "totals")
SHARP_BOOK = "pinnacle"
SEPARATORS = (" @ ", " vs. ", " vs ", " v ", " at ")
STALE_AFTER = timedelta(minutes=5)


def utc_now():
    """The only clock in this module; tests swap it for a fixed time."""
    return datetime.now(timezone.utc)


def _time(text):
    return datetime.fromisoformat(str(text).replace("Z", "+00:00"))


def has_started(event, now=None):
    return _time(event["commence_time"]) <= (now or utc_now())


def _norm(text):
    return str(text).strip().lower()


def _part_matches_team(part, team):
    """Every word of part (3+ letters) is a whole word of the team: "Nets" is not "Hornets"."""
    words = [w for w in _norm(part).split() if len(w) >= 3]
    return bool(words) and all(w in _norm(team).split() for w in words)


def find_event(events, text, now=None):
    """
    Game whose teams match text, e.g. "Celtics @ Lakers", "lakers vs celtics" or "Celtics".
    Games that already started are skipped. The soonest one wins if several match.
    Raises LookupError if none do.
    """
    parts = [_norm(text)]
    for sep in SEPARATORS:
        if sep in parts[0]:
            parts = parts[0].split(sep)
            break

    matches = [
        event for event in events
        if all(_part_matches_team(p, event["home_team"]) or _part_matches_team(p, event["away_team"])
               for p in parts)
    ]
    if not matches:
        raise LookupError(f"No upcoming game matches '{text}'")
    upcoming = [event for event in matches if not has_started(event, now)]
    if not upcoming:
        raise LookupError(f"'{text}' already started; promos need a game that hasn't started yet")
    return min(upcoming, key=lambda event: event["commence_time"])


def resolve_selection(event, selection):
    """
    Full team name for a team pick like "Celtics". An exact team name or "Draw" passes
    through. Raises ValueError if it fits neither team or both.
    """
    home, away = event["home_team"], event["away_team"]
    if _norm(selection) in (_norm(home), _norm(away), "draw"):
        return selection
    teams = [team for team in (away, home) if _part_matches_team(selection, team)]
    if len(teams) != 1:
        raise ValueError(f"Selection '{selection}' must name one team: {away} or {home}")
    return teams[0]


def _same_point(a, b):
    return a is not None and b is not None and abs(a - b) < 1e-9


def _line(bookmaker, market, selection, point):
    """
    One book's full line for the selection.
    :return: (prices, index of the selection, the other outcomes) or None if the book
             doesn't have that line. For spreads the other side is at -point; for totals
             it is the same point.
    """
    outcomes = next((m["outcomes"] for m in bookmaker["markets"] if m["key"] == market), None)
    if not outcomes:
        return None

    if market == "h2h":
        line = outcomes
    else:
        want_other = -point if market == "spreads" else point
        line = [
            o for o in outcomes
            if (_norm(o["name"]) == _norm(selection) and _same_point(o.get("point"), point))
            or (_norm(o["name"]) != _norm(selection) and _same_point(o.get("point"), want_other))
        ]

    names = [_norm(o["name"]) for o in line]
    if _norm(selection) not in names or len(line) < 2:
        return None
    index = names.index(_norm(selection))
    others = [o for i, o in enumerate(line) if i != index]
    return [o["price"] for o in line], index, others


def fair_probability(event, market, selection, point):
    """
    :return: (fair probability, source) where source is 'pinnacle' or
             'consensus of N books'; (None, None) if no book has the full line.
    """
    lines = {}
    for bookmaker in event["bookmakers"]:
        line = _line(bookmaker, market, selection, point)
        if line:
            lines[bookmaker["key"]] = line

    if SHARP_BOOK in lines:
        prices, index, _ = lines[SHARP_BOOK]
        return devig(prices)[index], SHARP_BOOK
    if not lines:
        return None, None

    probs = [devig(prices)[index] for prices, index, _ in lines.values()]
    count = len(probs)
    return sum(probs) / count, f"consensus of {count} book{'s' if count != 1 else ''}"


def _is_book(bookmaker, names):
    return _norm(bookmaker["key"]) in names or _norm(bookmaker["title"]) in names


def book_price(event, book, market, selection, point):
    """The promo book's normal price for the selection, or None."""
    for bookmaker in event["bookmakers"]:
        if _is_book(bookmaker, [_norm(book)]):
            line = _line(bookmaker, market, selection, point)
            if line:
                prices, index, _ = line
                return prices[index]
    return None


def best_hedge(event, market, selection, point, books):
    """
    Best price on the single other side across Henry's books.
    :return: (book title, other side's name, price) or (None, None, None). A three-way
             market (e.g. soccer with a draw) has no single other side.
    """
    best = (None, None, None)
    names = [_norm(b) for b in books]
    for bookmaker in event["bookmakers"]:
        if not _is_book(bookmaker, names):
            continue
        line = _line(bookmaker, market, selection, point)
        if not line or len(line[2]) != 1:
            continue
        other = line[2][0]
        if best[2] is None or other["price"] > best[2]:
            best = (bookmaker["title"], other["name"], other["price"])
    return best


def _stale(event, hedge_book, fair_source, now):
    """True if the hedge book's or Pinnacle's (when it set the fair price) odds are over 5 minutes old."""
    now = now or utc_now()
    for bookmaker in event["bookmakers"]:
        used = bookmaker["title"] == hedge_book or (fair_source == SHARP_BOOK and bookmaker["key"] == SHARP_BOOK)
        if used and bookmaker.get("last_update") and now - _time(bookmaker["last_update"]) > STALE_AFTER:
            return True
    return False


def evaluate(promo, event, books, now=None):
    """
    Everything Henry needs to decide on one promo.
    :param promo: dict with book, market, selection, point (spreads/totals), promo_type,
                  boosted_odds or boost_pct, max_stake and optional stake
    :param event: the game in The Odds API format
    :param books: the books he can hedge at (from BOOKS in .env)
    :param now: the time to judge stale prices against (default: the clock)
    """
    market = promo["market"]
    point = promo.get("point")
    if market not in MARKETS:
        raise ValueError(f"Market must be one of {', '.join(MARKETS)}")
    if market != "h2h" and point is None:
        raise ValueError("Spreads and totals need a point, e.g. 4.5 or 221.5")

    promo_type = promo["promo_type"]
    selection = promo["selection"] if market == "totals" else resolve_selection(event, promo["selection"])
    stake, flags = promo_stake(promo["max_stake"], promo.get("stake"))
    base = book_price(event, promo["book"], market, selection, point)
    odds = effective_odds(promo_type, promo.get("boosted_odds"), promo.get("boost_pct"), base)

    fair, source = fair_probability(event, market, selection, point)
    if fair is None:
        flags.append("no_fair_price")

    hedge_book, hedge_selection, hedge_odds = best_hedge(event, market, selection, point, books)
    locked = hedge(promo_type, stake, odds, hedge_odds)
    if not books:
        locked["flags"] = ["books_not_set"]
    if _stale(event, hedge_book, source, now):
        flags.append("stale_price")

    return {
        "event_id": event["id"],
        "event_name": f"{event['away_team']} @ {event['home_team']}",
        "commence_time": event["commence_time"],
        "selection": selection,
        "stake": stake,
        "base_odds": base,
        "effective_odds": round(odds, 4),
        "fair_prob": None if fair is None else round(fair, 4),
        "fair_source": source,
        "ev": expected_value(promo_type, stake, odds, fair),
        "hedge_book": hedge_book,
        "hedge_selection": hedge_selection,
        "hedge_odds": hedge_odds,
        "hedge_stake": locked["hedge_stake"],
        "locked_profit": locked["locked_profit"],
        "conversion_pct": locked["conversion_pct"],
        "flags": flags + locked["flags"],
    }
