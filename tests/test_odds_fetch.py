from datetime import datetime, timezone

import pytest
import requests
from conftest import EVENT_ID, FakeResponse

import fair_price
from odds_fetch import OddsFetchError, fetch_event_odds

AFTER_TIP_OFF = datetime(2026, 11, 26, 1, 0, tzinfo=timezone.utc)  # sample game starts 00:10


def test_fetch_by_team_names_asks_every_region_in_decimal(boost_env, fake_odds_api):
    event = fetch_event_odds("basketball_nba", "Celtics @ Lakers", "h2h", "test-key-not-real")
    assert event["id"] == EVENT_ID
    call = fake_odds_api[0]
    assert call["url"].endswith("/v4/sports/basketball_nba/odds")
    assert call["params"]["apiKey"] == "test-key-not-real"
    assert "eu" in call["params"]["regions"].split(",")  # Pinnacle lives in eu
    assert call["params"]["markets"] == "h2h"
    assert call["params"]["oddsFormat"] == "decimal"
    assert call["timeout"]


def test_fetch_by_event_id_uses_event_endpoint(boost_env, fake_odds_api):
    event = fetch_event_odds("basketball_nba", EVENT_ID, "totals", "k")
    assert event["id"] == EVENT_ID
    assert fake_odds_api[0]["url"].endswith(f"/events/{EVENT_ID}/odds")


def test_fetch_no_matching_game(boost_env, fake_odds_api):
    with pytest.raises(OddsFetchError, match="Knicks"):
        fetch_event_odds("basketball_nba", "Knicks @ Nets", "h2h", "k")


def test_fetch_rejects_odd_sport_key(boost_env, fake_odds_api):
    with pytest.raises(ValueError):
        fetch_event_odds("../../secret", "Celtics", "h2h", "k")
    assert fake_odds_api == []


def test_fetch_api_error_never_shows_the_key(boost_env, monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *a, **k: FakeResponse(401, {"message": "bad key"}))
    with pytest.raises(OddsFetchError) as err:
        fetch_event_odds("basketball_nba", "Celtics", "h2h", "super-secret-key")
    assert "401" in str(err.value)
    assert "super-secret-key" not in str(err.value)


def test_fetch_network_failure_never_shows_the_key(boost_env, monkeypatch):
    def boom(*a, **k):
        raise requests.ConnectionError("failed: https://api.the-odds-api.com/?apiKey=super-secret-key")

    monkeypatch.setattr(requests, "get", boom)
    with pytest.raises(OddsFetchError) as err:
        fetch_event_odds("basketball_nba", "Celtics", "h2h", "super-secret-key")
    assert "super-secret-key" not in str(err.value)
    assert err.value.__cause__ is None  # the original error (with the URL) is not chained


def test_fetch_by_event_id_refuses_a_started_game(boost_env, fake_odds_api, monkeypatch):
    monkeypatch.setattr(fair_price, "utc_now", lambda: AFTER_TIP_OFF)
    with pytest.raises(OddsFetchError, match="already started"):
        fetch_event_odds("basketball_nba", EVENT_ID, "h2h", "k")


def test_fetch_by_team_names_refuses_a_started_game(boost_env, fake_odds_api, monkeypatch):
    monkeypatch.setattr(fair_price, "utc_now", lambda: AFTER_TIP_OFF)
    with pytest.raises(OddsFetchError, match="already started"):
        fetch_event_odds("basketball_nba", "Celtics @ Lakers", "h2h", "k")
