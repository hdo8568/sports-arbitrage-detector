import pytest
from fastapi.testclient import TestClient

from api import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_odds_latest_first(temp_db):
    rows = client.get("/odds").json()
    assert len(rows) == 3
    assert rows[0]["bookmaker"] == "FanDuel"  # newest last_update


def test_odds_filter_by_sport_and_limit(temp_db):
    nba = client.get("/odds", params={"sport": "basketball_nba"}).json()
    assert {row["sport_key"] for row in nba} == {"basketball_nba"}
    assert len(nba) == 2

    by_title = client.get("/odds", params={"sport": "NFL"}).json()
    assert [row["team"] for row in by_title] == ["Jets"]

    assert len(client.get("/odds", params={"limit": 1}).json()) == 1


def test_odds_missing_db_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("ODDS_DB_PATH", str(tmp_path / "nope.db"))
    assert client.get("/odds").json() == []
    assert not (tmp_path / "nope.db").exists()  # API must not create the file


def test_arbitrage_has_suggested_stakes(temp_db):
    arbs = client.get("/arbitrage").json()
    assert len(arbs) == 1
    arb = arbs[0]
    assert arb["best_odds"] == {"home": 2.10, "away": 2.05}
    assert arb["bookmakers"] == {"home": "DraftKings", "away": "FanDuel"}
    assert arb["suggested_stakes"]["home"] == pytest.approx(49.40, abs=0.01)
    assert arb["suggested_stakes"]["payout"] == pytest.approx(103.73, abs=0.01)


def test_arbitrage_custom_total_stake(temp_db):
    arb = client.get("/arbitrage", params={"total_stake": 1000}).json()[0]
    stakes = arb["suggested_stakes"]
    assert stakes["home"] + stakes["away"] == pytest.approx(1000, abs=0.01)


def test_kelly_endpoint():
    response = client.get("/kelly", params={"odds": 2.0, "prob": 0.6, "bankroll": 1000})
    assert response.status_code == 200
    body = response.json()
    assert body["fraction"] == 0.25
    assert body["full_kelly_fraction"] == pytest.approx(0.2)
    assert body["stake"] == pytest.approx(50.0)


def test_kelly_endpoint_no_edge():
    body = client.get("/kelly", params={"odds": 1.91, "prob": 0.5, "bankroll": 1000, "fraction": 1}).json()
    assert body["stake"] == 0


def test_kelly_endpoint_rejects_bad_input():
    assert client.get("/kelly", params={"odds": 1.0, "prob": 0.5, "bankroll": 100}).status_code == 422
    assert client.get("/kelly", params={"odds": 2.0, "prob": 1.5, "bankroll": 100}).status_code == 422
    assert client.get("/kelly", params={"odds": 2.0, "prob": 0.5}).status_code == 422
