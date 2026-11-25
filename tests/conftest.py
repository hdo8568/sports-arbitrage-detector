import smtplib
import sqlite3

import pytest
import requests


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Tests must never call the real Odds API or send email."""
    def blocked(*args, **kwargs):
        raise RuntimeError("Network call blocked in tests")

    monkeypatch.setattr(requests, "get", blocked)
    monkeypatch.setattr(smtplib, "SMTP_SSL", blocked)
    monkeypatch.setattr(smtplib, "SMTP", blocked)


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """A temporary SQLite file with the same tables the app creates, plus a few rows."""
    db_path = tmp_path / "test_odds.db"
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE odds (
            event_id TEXT, sport_key TEXT, sport_title TEXT, commence_time TEXT,
            home_team TEXT, away_team TEXT, bookmaker TEXT, market_type TEXT,
            team TEXT, odds REAL, last_update TEXT,
            PRIMARY KEY (event_id, bookmaker, market_type, team)
        )
    """)
    conn.execute("""
        CREATE TABLE arbitrage_bets (
            event_id TEXT PRIMARY KEY, home_team TEXT, away_team TEXT,
            best_odds TEXT, profit_percentage REAL, bookmakers TEXT
        )
    """)
    odds_rows = [
        ("e1", "basketball_nba", "NBA", "2026-01-01T00:00:00Z", "Lakers", "Celtics",
         "DraftKings", "h2h", "Lakers", 2.10, "2026-01-01T00:00:01Z"),
        ("e1", "basketball_nba", "NBA", "2026-01-01T00:00:00Z", "Lakers", "Celtics",
         "FanDuel", "h2h", "Celtics", 2.05, "2026-01-01T00:00:03Z"),
        ("e2", "americanfootball_nfl", "NFL", "2026-01-02T00:00:00Z", "Jets", "Bills",
         "BetMGM", "h2h", "Jets", 3.00, "2026-01-01T00:00:02Z"),
    ]
    conn.executemany("INSERT INTO odds VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", odds_rows)
    conn.execute(
        "INSERT INTO arbitrage_bets VALUES (?, ?, ?, ?, ?, ?)",
        ("e1", "Lakers", "Celtics", str({"home": 2.10, "away": 2.05}), 3.65,
         str({"home": "DraftKings", "away": "FanDuel"})),
    )
    conn.commit()
    conn.close()

    monkeypatch.setenv("ODDS_DB_PATH", str(db_path))
    return db_path
