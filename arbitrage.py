# arbitrage.py
#detects arbitrage from 

import sqlite3
from datetime import datetime
from kelly import arbitrage_stakes
from config import get_arb_total_stake

def detect_arbitrage(odds_data, total_stake=None):
    """
    Detects arbitrage opportunities from the given odds data.
    :param odds_data: List of events with odds from multiple sportsbooks.
    :param total_stake: amount to split across both sides for the suggested
                        stakes (defaults to ARB_TOTAL_STAKE, or $100).
    :return: List of arbitrage opportunities.
    """
    if total_stake is None:
        total_stake = get_arb_total_stake()

    arbitrage_bets = []

    for event in odds_data:
        event_id = event["id"]
        home_team = event["home_team"]
        away_team = event["away_team"]
        best_odds = {"home": 0, "away": 0}  # Store best odds for home and away team
        bookmakers_used = {"home": "", "away": ""}

        # Loop through the bookmakers for the same outcome (home or away)
        for bookmaker in event["bookmakers"]:
            for market in bookmaker["markets"]:
                if market["key"] == "h2h":  # Moneyline market (home vs away)
                    for outcome in market["outcomes"]:
                        team = outcome["name"]
                        odds = outcome["price"]

                        # Compare odds for home vs away team across sportsbooks
                        if team == home_team and odds > best_odds["home"]:
                            best_odds["home"] = odds
                            bookmakers_used["home"] = bookmaker["title"]
                        if team == away_team and odds > best_odds["away"]:
                            best_odds["away"] = odds
                            bookmakers_used["away"] = bookmaker["title"]

        # Only if we have both home and away odds
        if best_odds["home"] > 0 and best_odds["away"] > 0:
            implied_prob = (1 / best_odds["home"]) + (1 / best_odds["away"])
            print(f"\n{home_team} vs {away_team}")
            print(f"  Home odds: {best_odds['home']} (Bookmaker: {bookmakers_used['home']})")
            print(f"  Away odds: {best_odds['away']} (Bookmaker: {bookmakers_used['away']})")
            print(f"  Implied probability: {implied_prob:.4f}")


            if implied_prob < 1:  # Arbitrage exists!
                profit_percentage = (1 - implied_prob) * 100
                arbitrage_bets.append({
                    "event_id": event_id,
                    "home_team": home_team,
                    "away_team": away_team,
                    "best_odds": best_odds,
                    "profit_percentage": round(profit_percentage, 2),
                    "bookmakers": bookmakers_used,
                    # How much to put on each side so both pay the same
                    "suggested_stakes": arbitrage_stakes(
                        best_odds["home"], best_odds["away"], total_stake
                    )
                })

    return arbitrage_bets




def save_arbitrage_to_db(arbitrage_bets, db_name="odds_data.db"):
    """
    Saves arbitrage opportunities to an SQLite database.
    """
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()

    # Create table for arbitrage bets if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS arbitrage_bets (
            event_id TEXT PRIMARY KEY,
            home_team TEXT,
            away_team TEXT,
            best_odds TEXT,
            profit_percentage REAL,
            bookmakers TEXT
        )
    ''')

    for arb in arbitrage_bets:
        cursor.execute('''
            INSERT OR REPLACE INTO arbitrage_bets 
            (event_id, home_team, away_team, best_odds, profit_percentage, bookmakers)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            arb["event_id"],
            arb["home_team"],
            arb["away_team"],
            str(arb["best_odds"]),
            arb["profit_percentage"],
            str(arb["bookmakers"])
        ))

    connection.commit()
    connection.close()


def fetch_odds_from_db(db_name="odds_data.db"):
    """
    Fetches stored odds from the database to analyze for arbitrage.
    """
    connection = sqlite3.connect(db_name)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM odds")
    rows = cursor.fetchall()
    connection.close()

    # Convert database rows back into a structured dictionary
    odds_data = {}
    for row in rows:
        event_id = row["event_id"]
        if event_id not in odds_data:
            odds_data[event_id] = {
                "id": event_id,
                "home_team": row["home_team"],
                "away_team": row["away_team"],
                "bookmakers": []
            }

        # Add odds for each bookmaker
        odds_data[event_id]["bookmakers"].append({
            "title": row["bookmaker"],
            "markets": [
                {
                    "key": row["market_type"],
                    "outcomes": [
                        {"name": row["team"], "price": row["odds"]}
                    ]
                }
            ]
        })

    return list(odds_data.values())


if __name__ == "__main__":
    
    print("Fetching stored odds from database...")
    print(f"\n[{datetime.now()}] Fetching stored odds from database...")
    odds_data = fetch_odds_from_db()
    print(f"Number of events fetched: {len(odds_data)}")

    
    print("Detecting arbitrage opportunities...")
    arbitrage_bets = detect_arbitrage(odds_data)

    if arbitrage_bets:
        print(f"Found {len(arbitrage_bets)} arbitrage opportunities!")
        save_arbitrage_to_db(arbitrage_bets)
    else:
        print("No arbitrage opportunities found this time.")
