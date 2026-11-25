#odds_fetch.py
# Gets current odds for one game from The Odds API (v4).
# Docs: https://the-odds-api.com/liveapi/guides/v4/
#
# Cost: one credit per region per market. With the default 5 regions, one promo
# costs 5 credits. Set ODDS_REGIONS in .env to spend less.
#
# The API key goes in the query string, so error messages here never include the
# URL or the original requests error (which would print the key).

import re

import requests

from config import get_odds_regions
from fair_price import find_event

BASE_URL = "https://api.the-odds-api.com/v4/sports"
SPORT_KEY = re.compile(r"^[a-z0-9_]+$")
EVENT_ID = re.compile(r"^[a-f0-9]{32}$")
TIMEOUT_SECONDS = 15


class OddsFetchError(Exception):
    pass


def _get(url, params):
    try:
        response = requests.get(url, params=params, timeout=TIMEOUT_SECONDS)
    except requests.RequestException:
        raise OddsFetchError("Could not reach The Odds API. Check the internet connection.") from None

    if response.status_code != 200:
        try:
            reason = response.json().get("message", "")
        except (ValueError, AttributeError):
            reason = ""
        raise OddsFetchError(f"The Odds API said {response.status_code}. {reason}".strip())
    return response.json()


def fetch_event_odds(sport_key, event, market, api_key):
    """
    :param sport_key: The Odds API sport key, e.g. basketball_nba or soccer_epl
    :param event: The Odds API event id, or team names like "Celtics @ Lakers"
    :param market: h2h, spreads or totals
    :return: one game in The Odds API format, with every book's prices
    """
    if not SPORT_KEY.match(sport_key or ""):
        raise ValueError("Sport key looks wrong; use The Odds API key, e.g. basketball_nba")

    params = {
        "apiKey": api_key,
        "regions": get_odds_regions(),
        "markets": market,
        "oddsFormat": "decimal",
    }

    if EVENT_ID.match(event):
        return _get(f"{BASE_URL}/{sport_key}/events/{event}/odds", params)

    events = _get(f"{BASE_URL}/{sport_key}/odds", params)
    try:
        return find_event(events, event)
    except LookupError as e:
        raise OddsFetchError(str(e)) from None
