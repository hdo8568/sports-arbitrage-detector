#config.py
# Reads secrets and settings from the environment.
# If python-dotenv is installed, a .env file next to this file is loaded first,
# so cron on EC2 picks it up no matter which folder it runs from.
# Copy .env.example to .env and fill in your own values. Never commit .env.

import os

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(PROJECT_DIR, ".env"))
except ImportError:
    pass


def get_odds_api_key():
    key = os.environ.get("ODDS_API_KEY")
    if not key:
        raise RuntimeError(
            "ODDS_API_KEY is not set. Copy .env.example to .env and add your Odds API key."
        )
    return key


def get_db_path():
    return os.environ.get("ODDS_DB_PATH", os.path.join(PROJECT_DIR, "odds_data.db"))


def get_arb_total_stake():
    # Total amount to split across both sides of an arbitrage in the alerts
    return float(os.environ.get("ARB_TOTAL_STAKE", "100"))


def get_books():
    # The sportsbooks Henry can bet at, e.g. BOOKS=draftkings,fanduel,betmgm
    # Names are The Odds API bookmaker keys or titles, any case. Empty list if unset.
    raw = os.environ.get("BOOKS", "")
    return [name.strip().lower() for name in raw.split(",") if name.strip()]


def get_odds_regions():
    # Boost Desk asks every region so Pinnacle (eu) is there for the fair price.
    # Each region costs one Odds API credit per market, so trim this to save credits.
    return os.environ.get("ODDS_REGIONS", "us,us2,uk,eu,au")


def get_boosts_db_path():
    # Boost Desk keeps its own SQLite file so the tracked odds_data.db never changes
    return os.environ.get("BOOSTS_DB_PATH", os.path.join(PROJECT_DIR, "boosts.db"))
