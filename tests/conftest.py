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


# ---------- Boost Desk fixtures ----------

EVENT_ID = "0123456789abcdef0123456789abcdef"


def _book(key, title, markets):
    return {"key": key, "title": title, "last_update": "2026-11-25T18:00:00Z", "markets": markets}


def _h2h(home, away, draw=None):
    outcomes = [{"name": "Los Angeles Lakers", "price": home}, {"name": "Boston Celtics", "price": away}]
    if draw:
        outcomes.append({"name": "Draw", "price": draw})
    return {"key": "h2h", "outcomes": outcomes}


def _totals(point, over, under):
    return {"key": "totals", "outcomes": [
        {"name": "Over", "price": over, "point": point},
        {"name": "Under", "price": under, "point": point},
    ]}


def _spreads(point, home, away):
    return {"key": "spreads", "outcomes": [
        {"name": "Los Angeles Lakers", "price": home, "point": point},
        {"name": "Boston Celtics", "price": away, "point": -point},
    ]}


@pytest.fixture
def sample_event():
    """One NBA game in The Odds API shape. Pinnacle is the sharp book; the rest are NY books."""
    return {
        "id": EVENT_ID,
        "sport_key": "basketball_nba",
        "sport_title": "NBA",
        "commence_time": "2026-11-26T00:10:00Z",
        "home_team": "Los Angeles Lakers",
        "away_team": "Boston Celtics",
        "bookmakers": [
            _book("pinnacle", "Pinnacle", [_h2h(1.5, 2.6), _spreads(-4.5, 1.95, 1.95), _totals(220.5, 1.90, 1.95)]),
            _book("draftkings", "DraftKings", [_h2h(1.45, 2.75), _spreads(-4.5, 1.91, 1.91), _totals(221.5, 1.91, 1.91)]),
            _book("fanduel", "FanDuel", [_h2h(1.48, 2.70), _totals(221.5, 1.87, 1.95)]),
            _book("betmgm", "BetMGM", [_h2h(1.44, 2.80)]),
        ],
    }


@pytest.fixture
def soccer_event():
    """A three-way market (home / away / draw), so there is no single other side to hedge."""
    return {
        "id": "fedcba9876543210fedcba9876543210",
        "sport_key": "soccer_epl",
        "sport_title": "EPL",
        "commence_time": "2026-11-26T15:00:00Z",
        "home_team": "Los Angeles Lakers",
        "away_team": "Boston Celtics",
        "bookmakers": [
            _book("pinnacle", "Pinnacle", [_h2h(2.1, 3.6, 3.4)]),
            _book("fanduel", "FanDuel", [_h2h(2.0, 3.5, 3.3)]),
        ],
    }


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)

    def json(self):
        return self._payload


@pytest.fixture
def boost_env(tmp_path, monkeypatch):
    """Test key, Henry's book list and a temp boosts database."""
    monkeypatch.setenv("ODDS_API_KEY", "test-key-not-real")
    monkeypatch.setenv("BOOKS", "draftkings, FanDuel ,betmgm")
    db_path = tmp_path / "boosts.db"
    monkeypatch.setenv("BOOSTS_DB_PATH", str(db_path))
    return db_path


@pytest.fixture
def fake_odds_api(monkeypatch, sample_event):
    """Stand-in for The Odds API. Records each call and returns sample_event."""
    calls = []

    def fake_get(url, params=None, timeout=None):
        calls.append({"url": url, "params": params, "timeout": timeout})
        if url.endswith("/events/" + sample_event["id"] + "/odds"):
            return FakeResponse(200, sample_event)
        return FakeResponse(200, [sample_event])

    monkeypatch.setattr(requests, "get", fake_get)
    return calls
