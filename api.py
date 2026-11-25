#api.py
# A small read-only API over the odds database.
# Run with:  uvicorn api:app --reload
# Then open http://127.0.0.1:8000/docs to try every endpoint.

import ast
import os
import sqlite3
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query

from config import get_db_path
from kelly import arbitrage_stakes, kelly_stake

app = FastAPI(title="Sports Arbitrage Detector")


def query_db(sql, params=()):
    """Run a SELECT against the odds database. Returns [] if the DB or table isn't there yet."""
    db_path = get_db_path()
    if not os.path.exists(db_path):
        return []

    # Open read-only so the API can never change the data
    connection = sqlite3.connect(Path(db_path).resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(sql, params).fetchall()
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            return []
        raise
    finally:
        connection.close()
    return [dict(row) for row in rows]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/odds")
def get_odds(
    sport: Optional[str] = Query(None, description="e.g. basketball_nba or NBA"),
    limit: int = Query(50, ge=1, le=1000),
):
    """Latest odds rows, newest update first."""
    if sport:
        sql = """
            SELECT * FROM odds
            WHERE sport_key = ? OR sport_title = ?
            ORDER BY last_update DESC
            LIMIT ?
        """
        return query_db(sql, (sport, sport, limit))
    return query_db("SELECT * FROM odds ORDER BY last_update DESC LIMIT ?", (limit,))


@app.get("/arbitrage")
def get_arbitrage(total_stake: float = Query(100.0, gt=0)):
    """Stored arbitrage opportunities, each with suggested stakes for total_stake."""
    rows = query_db("SELECT * FROM arbitrage_bets ORDER BY profit_percentage DESC")

    results = []
    for row in rows:
        # best_odds and bookmakers are saved as Python dict strings by arbitrage.py
        best_odds = ast.literal_eval(row["best_odds"])
        bookmakers = ast.literal_eval(row["bookmakers"])
        results.append({
            "event_id": row["event_id"],
            "home_team": row["home_team"],
            "away_team": row["away_team"],
            "best_odds": best_odds,
            "bookmakers": bookmakers,
            "profit_percentage": row["profit_percentage"],
            "suggested_stakes": arbitrage_stakes(
                best_odds["home"], best_odds["away"], total_stake
            ),
        })
    return results


@app.get("/kelly")
def get_kelly(
    odds: float = Query(..., gt=1, description="Decimal odds, e.g. 2.10"),
    prob: float = Query(..., ge=0, le=1, description="Fair win probability, 0 to 1"),
    bankroll: float = Query(..., ge=0),
    fraction: float = Query(0.25, gt=0, le=1, description="Share of full Kelly to bet"),
):
    """Kelly stake for a single bet. Stake is 0 when there's no edge."""
    try:
        result = kelly_stake(odds, prob, bankroll, fraction)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"odds": odds, "prob": prob, "bankroll": bankroll, "fraction": fraction, **result}
