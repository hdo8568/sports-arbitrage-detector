#boost_store.py
# The boosts table: every promo Boost Desk looked at, what it worked out, and
# (filled in later) whether Henry placed it and how it went.
# Lives in its own SQLite file (BOOSTS_DB_PATH, default boosts.db) so the tracked
# odds_data.db never changes.

import sqlite3
from datetime import datetime, timedelta, timezone

from config import get_boosts_db_path

# Column names are fixed here, never taken from input, so the SQL below is safe to build.
COLUMNS = {
    "created_at": "TEXT",
    "book": "TEXT",
    "sport_key": "TEXT",
    "event": "TEXT",
    "market": "TEXT",
    "selection": "TEXT",
    "point": "REAL",
    "promo_type": "TEXT",
    "boosted_odds": "REAL",
    "boost_pct": "REAL",
    "max_stake": "REAL",
    "stake": "REAL",
    "event_id": "TEXT",
    "event_name": "TEXT",
    "commence_time": "TEXT",
    "base_odds": "REAL",
    "effective_odds": "REAL",
    "fair_prob": "REAL",
    "fair_source": "TEXT",
    "ev": "REAL",
    "hedge_book": "TEXT",
    "hedge_selection": "TEXT",
    "hedge_odds": "REAL",
    "hedge_stake": "REAL",
    "locked_profit": "REAL",
    "conversion_pct": "REAL",
    "flags": "TEXT",
    "placed": "INTEGER NOT NULL DEFAULT 0",   # 0 = no, 1 = yes
    "actual_result": "TEXT",                  # won / lost / push / void
    "actual_profit": "REAL",                  # dollars actually kept, after the hedge
}


def _connect():
    conn = sqlite3.connect(get_boosts_db_path())
    conn.row_factory = sqlite3.Row
    columns = ", ".join(f"{name} {kind}" for name, kind in COLUMNS.items())
    conn.execute(f"CREATE TABLE IF NOT EXISTS boosts (id INTEGER PRIMARY KEY AUTOINCREMENT, {columns})")
    return conn


def _to_dict(row):
    data = dict(row)
    data["flags"] = data["flags"].split(",") if data["flags"] else []
    data["placed"] = bool(data["placed"])
    return data


def save_boost(row):
    """Insert one evaluated promo. Returns its id."""
    values = dict(row)
    values["flags"] = ",".join(values.get("flags") or [])
    values["placed"] = 1 if values.get("placed") else 0
    values.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    names = list(COLUMNS)
    sql = f"INSERT INTO boosts ({', '.join(names)}) VALUES ({', '.join('?' for _ in names)})"
    conn = _connect()
    try:
        with conn:
            cursor = conn.execute(sql, [values.get(name) for name in names])
        return cursor.lastrowid
    finally:
        conn.close()


def get_boost(boost_id):
    conn = _connect()
    try:
        row = conn.execute("SELECT * FROM boosts WHERE id = ?", (boost_id,)).fetchone()
    finally:
        conn.close()
    return _to_dict(row) if row else None


def ranked_boosts(hours=24):
    """
    Promos added in the last `hours` and not placed yet, best first:
    highest locked profit, then highest EV. Promos with no hedge go last.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    conn = _connect()
    try:
        rows = [_to_dict(r) for r in conn.execute("SELECT * FROM boosts WHERE placed = 0")]
    finally:
        conn.close()

    fresh = [r for r in rows if datetime.fromisoformat(r["created_at"]) >= cutoff]

    def best_first(r):
        locked = r["locked_profit"]
        ev = r["ev"]
        return (locked is None, -(locked or 0), ev is None, -(ev or 0))

    return sorted(fresh, key=best_first)
