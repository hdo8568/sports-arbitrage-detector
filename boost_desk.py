#boost_desk.py
# Boost Desk: is today's profit boost, odds boost or bonus bet worth it, and how
# do I hedge it?
#
#   python boost_desk.py add --book fanduel --sport basketball_nba --event "Celtics @ Lakers" \
#       --selection "Boston Celtics" --boost-pct 50 --max-stake 50 --type profit_boost
#   python boost_desk.py rank
#
# add: pulls the game's odds from The Odds API, works out the fair price, EV, the best
#      hedge at your books (BOOKS in .env) and the locked profit, then logs it.
# rank: today's promos that aren't placed yet, best locked profit first, then EV.

import argparse
import sys

from boost_store import get_boost, ranked_boosts, save_boost
from config import get_books, get_odds_api_key
from fair_price import MARKETS, evaluate
from odds_fetch import OddsFetchError, fetch_event_odds
from promo_math import PROMO_TYPES

FLAG_TEXT = {
    "stake_capped_at_max": "stake was over the promo max, so it uses the max",
    "no_opposite_price": "none of your books has a single other side to hedge",
    "hedge_loses_money": "the hedge price is too short, so hedging loses money",
    "no_fair_price": "no book has this full line, so there's no fair price or EV",
    "books_not_set": "BOOKS isn't set in .env, so no hedge was looked for",
    "stale_price": "the hedge book's or Pinnacle's odds are over 5 minutes old; re-check before betting",
}


def add_boost(promo):
    """Fetch odds, evaluate the promo, save it. Returns the saved row."""
    api_key = get_odds_api_key()  # clear RuntimeError if ODDS_API_KEY is missing
    event = fetch_event_odds(promo["sport_key"], promo["event"], promo["market"], api_key)
    result = evaluate(promo, event, get_books())
    return get_boost(save_boost({**promo, **result}))


def money(amount):
    if amount is None:
        return "n/a"
    return f"-${abs(amount):,.2f}" if amount < 0 else f"${amount:,.2f}"


def print_boost(row):
    print(f"#{row['id']} {row['event_name']}, starts {row['commence_time']}")
    base = f" (book price {row['base_odds']})" if row["base_odds"] else ""
    print(f"{row['book']} {row['promo_type']}: {row['selection']} ({row['market']}), "
          f"{money(row['stake'])} at {row['effective_odds']}{base}")
    if row["fair_prob"] is not None:
        print(f"Fair chance {row['fair_prob']:.1%} ({row['fair_source']}), EV {money(row['ev'])}")
    if row["hedge_stake"] is not None:
        print(f"Hedge: {money(row['hedge_stake'])} on {row['hedge_selection']} "
              f"at {row['hedge_book']} ({row['hedge_odds']})")
        print(f"Locked profit: {money(row['locked_profit'])}")
    if row["conversion_pct"] is not None:
        print(f"Bonus conversion: {row['conversion_pct']}% of face value")
    for flag in row["flags"]:
        print(f"Heads up: {FLAG_TEXT.get(flag, flag)}")


def print_ranked(rows):
    if not rows:
        print("No open promos from the last day. Add one with: python boost_desk.py add ...")
        return
    for row in rows:
        locked = "no hedge" if row["locked_profit"] is None else f"{money(row['locked_profit'])} locked"
        flags = f"  [{', '.join(row['flags'])}]" if row["flags"] else ""
        print(f"#{row['id']}  {locked}  EV {money(row['ev'])}  "
              f"{row['book']} {row['selection']} ({row['market']}) {row['event_name']}{flags}")


def build_parser():
    parser = argparse.ArgumentParser(prog="boost_desk.py", description="Value and hedge sportsbook promos.")
    commands = parser.add_subparsers(dest="command", required=True)

    add = commands.add_parser("add", help="add a promo and work out its value")
    add.add_argument("--book", required=True, help="book offering the promo, e.g. fanduel")
    add.add_argument("--sport", required=True, help="The Odds API sport key, e.g. basketball_nba")
    add.add_argument("--event", required=True, help='team names like "Celtics @ Lakers", or the event id')
    add.add_argument("--market", default="h2h", choices=MARKETS)
    add.add_argument("--selection", required=True, help='team name, or "Over" / "Under" for totals')
    add.add_argument("--point", type=float, help="line for spreads and totals, e.g. 4.5 or 221.5")
    add.add_argument("--boosted-odds", type=float, help="boosted decimal odds, if the book shows them")
    add.add_argument("--boost-pct", type=float, help="profit boost percent, e.g. 50")
    add.add_argument("--max-stake", type=float, required=True, help="most the promo lets you bet")
    add.add_argument("--stake", type=float, help="bet less than the max (defaults to the max)")
    add.add_argument("--type", required=True, choices=PROMO_TYPES, dest="promo_type")

    rank = commands.add_parser("rank", help="today's open promos, best first")
    rank.add_argument("--hours", type=float, default=24, help="how far back to look (default 24)")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "add":
            promo = {
                "book": args.book, "sport_key": args.sport, "event": args.event,
                "market": args.market, "selection": args.selection, "point": args.point,
                "boosted_odds": args.boosted_odds, "boost_pct": args.boost_pct,
                "max_stake": args.max_stake, "stake": args.stake, "promo_type": args.promo_type,
            }
            print_boost(add_boost(promo))
        else:
            print_ranked(ranked_boosts(args.hours))
    except (RuntimeError, OddsFetchError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
