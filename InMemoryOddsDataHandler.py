#InMemoryOddsDataHandler.py
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime
 
class OddsSQLHandler:
    def __init__(self, db_name="odds_db.db"):
        if db_name == "mock_api":
          self.db_name = "mock_db.db"
        else:
          self.db_name = db_name

        self.create_odds_table()  # Automatically create table on initialization


    def create_odds_table(self) -> None:
        """
        Create the OddsTable in the database if it doesn't already exist.
        Added more fields for better data tracking.
        """
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()

        create_table_query = """
        CREATE TABLE IF NOT EXISTS OddsTable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sport_title TEXT NOT NULL,
            team TEXT NOT NULL,
            bookmaker TEXT NOT NULL,
            odds REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            event_date TEXT,
            event_id TEXT,
            market_type TEXT,
            UNIQUE(sport_title, team, bookmaker, event_id)
        )
        """

        cursor.execute(create_table_query)
        connection.commit()
        connection.close()


    ##Placeholder function, will be later replaced with API fetch
    def fetch_mock_odds_data(self) -> List[Dict[str, Any]]:
        """
        Simulate fetching odds data from an API.
        Replace this with real API calls in production.
        """
        return [
            {
                "sport_title": "basketball_nba",
                "team": "Warriors",
                "bookmaker": "draftkings",
                "odds": 1.80,
                "event_date": "2024-01-20",
                "event_id": "nba_123",
                "market_type": "moneyline"
            },
            # Add more mock data...
        ]

    def save_odds_to_db(self, odds_data: List[Dict[str, Any]]) -> None:
        """
        Save odds data to the OddsTable in the database.
        :param odds_data: List of odds dictionaries.
        """
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()

        insert_query = """
        INSERT OR REPLACE INTO OddsTable
        (sport_title, team, bookmaker, odds, event_date, event_id, market_type)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        try:
            for event in odds_data:
                cursor.execute(insert_query, (
                    event["sport_title"],
                    event["team"],
                    event["bookmaker"],
                    event["odds"],
                    event.get("event_date"),
                    event.get("event_id"),
                    event.get("market_type")
                ))
            connection.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            connection.rollback()
        finally:
            connection.close()

    def get_odds_by_sport(self, sport_title: str) -> List[Dict[str, Any]]:
        """
        Retrieve odds for a specific sport.
        """
        connection = sqlite3.connect(self.db_name)
        connection.row_factory = sqlite3.Row  # This enables column access by name
        cursor = connection.cursor()

        query = "SELECT * FROM OddsTable WHERE sport_title = ? ORDER BY timestamp DESC"
        cursor.execute(query, (sport_title,))
        results = [dict(row) for row in cursor.fetchall()]
        connection.close()
        return results


    def get_odds_by_team(self, team: str) -> List[Dict[str, Any]]:
        """
        Retrieve odds for a specific team.
        """
        connection = sqlite3.connect(self.db_name)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        query = "SELECT * FROM OddsTable WHERE team = ? ORDER BY timestamp DESC"
        cursor.execute(query, (team,))
        results = [dict(row) for row in cursor.fetchall()]
        connection.close()
        return results

    def get_latest_odds(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve the most recent odds entries.
        """
        connection = sqlite3.connect(self.db_name)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        query = "SELECT * FROM OddsTable ORDER BY timestamp DESC LIMIT ?"
        cursor.execute(query, (limit,))
        results = [dict(row) for row in cursor.fetchall()]
        connection.close()
        return results

    def delete_old_odds(self, days: int = 7) -> None:
        """
        Delete odds data older than specified days.
        """
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()

        query = """
        DELETE FROM OddsTable
        WHERE timestamp < datetime('now', '-? days')
        """

        cursor.execute(query, (days,))
        connection.commit()
        connection.close()