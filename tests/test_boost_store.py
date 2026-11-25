import sqlite3
from datetime import datetime, timedelta, timezone

from boost_store import get_boost, ranked_boosts, save_boost


def _row(locked, ev, hours_ago=1, placed=False):
    created = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()
    return {"book": "fanduel", "sport_key": "basketball_nba", "event": "Celtics @ Lakers",
            "market": "h2h", "selection": "Boston Celtics", "promo_type": "profit_boost",
            "max_stake": 50, "locked_profit": locked, "ev": ev, "flags": ["stake_capped_at_max"],
            "created_at": created, "placed": placed}


def test_save_and_read_back(boost_env):
    boost_id = save_boost(_row(7.57, 3.1))
    row = get_boost(boost_id)
    assert row["locked_profit"] == 7.57
    assert row["flags"] == ["stake_capped_at_max"]
    assert row["placed"] is False
    assert row["actual_result"] is None
    assert row["actual_profit"] is None


def test_table_has_tracking_columns(boost_env):
    save_boost(_row(1.0, 1.0))
    cols = {r[1] for r in sqlite3.connect(boost_env).execute("PRAGMA table_info(boosts)")}
    assert {"placed", "actual_result", "actual_profit", "locked_profit", "ev"} <= cols


def test_ranked_by_locked_profit_then_ev(boost_env):
    save_boost(_row(5.0, 2.0))
    save_boost(_row(None, 30.0))   # no hedge goes last
    save_boost(_row(10.0, 1.0))
    save_boost(_row(5.0, 4.0))
    save_boost(_row(50.0, 9.0, hours_ago=48))  # yesterday's promo, left out
    save_boost(_row(80.0, 9.0, placed=True))   # already placed, left out
    ranked = ranked_boosts()
    assert [(r["locked_profit"], r["ev"]) for r in ranked] == [(10.0, 1.0), (5.0, 4.0), (5.0, 2.0), (None, 30.0)]


def test_ranked_empty_when_nothing_saved(boost_env):
    assert ranked_boosts() == []
