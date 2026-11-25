import sqlite3

import pytest

import email_alerts
from arbitrage import detect_arbitrage, save_arbitrage_to_db


def make_event(home_odds_by_book, away_odds_by_book):
    bookmakers = []
    for book in set(home_odds_by_book) | set(away_odds_by_book):
        outcomes = []
        if book in home_odds_by_book:
            outcomes.append({"name": "Lakers", "price": home_odds_by_book[book]})
        if book in away_odds_by_book:
            outcomes.append({"name": "Celtics", "price": away_odds_by_book[book]})
        bookmakers.append({"title": book, "markets": [{"key": "h2h", "outcomes": outcomes}]})
    return {"id": "e1", "home_team": "Lakers", "away_team": "Celtics", "bookmakers": bookmakers}


def test_detects_arbitrage_with_suggested_stakes():
    event = make_event({"DraftKings": 2.10, "FanDuel": 1.80}, {"DraftKings": 1.75, "FanDuel": 2.05})
    arbs = detect_arbitrage([event], total_stake=200)

    assert len(arbs) == 1
    arb = arbs[0]
    assert arb["best_odds"] == {"home": 2.10, "away": 2.05}
    assert arb["bookmakers"] == {"home": "DraftKings", "away": "FanDuel"}

    stakes = arb["suggested_stakes"]
    assert stakes["total_stake"] == 200
    assert stakes["home"] + stakes["away"] == pytest.approx(200, abs=0.01)
    assert stakes["home"] * 2.10 == pytest.approx(stakes["away"] * 2.05, abs=0.05)


def test_default_total_stake_from_env(monkeypatch):
    monkeypatch.setenv("ARB_TOTAL_STAKE", "50")
    event = make_event({"A": 2.10}, {"B": 2.05})
    assert detect_arbitrage([event])[0]["suggested_stakes"]["total_stake"] == 50


def test_no_arbitrage_when_books_agree():
    event = make_event({"A": 1.91}, {"A": 1.91})
    assert detect_arbitrage([event]) == []


def test_save_still_works_with_stakes(tmp_path):
    # Stakes are extra info; the arbitrage_bets table is unchanged
    db = tmp_path / "arb.db"
    arbs = detect_arbitrage([make_event({"A": 2.10}, {"B": 2.05})])
    save_arbitrage_to_db(arbs, db_name=str(db))
    rows = sqlite3.connect(db).execute("SELECT event_id, profit_percentage FROM arbitrage_bets").fetchall()
    assert rows == [("e1", arbs[0]["profit_percentage"])]


def test_email_body_includes_stakes():
    arbs = detect_arbitrage([make_event({"DraftKings": 2.10}, {"FanDuel": 2.05})], total_stake=100)
    body = email_alerts.build_email_body(arbs)
    assert "Suggested stakes (total $100.00)" in body
    assert "Lakers at DraftKings: $49.40" in body
    assert "Celtics at FanDuel: $50.60" in body
    assert "Payout either way: $103.73" in body


def test_email_skips_without_credentials(monkeypatch, capsys):
    monkeypatch.setattr(email_alerts, "EMAIL_USER", None)
    monkeypatch.setattr(email_alerts, "EMAIL_PASS", None)
    arbs = detect_arbitrage([make_event({"A": 2.10}, {"B": 2.05})])
    email_alerts.send_arbitrage_email(arbs)  # must not try to connect
    assert "skipping email" in capsys.readouterr().out


def test_odds_api_key_comes_from_env(monkeypatch):
    import config
    from OddsAPIHandler import OddsAPIHandler

    monkeypatch.setenv("ODDS_API_KEY", "test-key-123")
    assert OddsAPIHandler().api_key == "test-key-123"

    monkeypatch.delenv("ODDS_API_KEY")
    with pytest.raises(RuntimeError):
        config.get_odds_api_key()
