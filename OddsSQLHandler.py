#OddsSQLHandler.py

import sqlite3
import datetime

"""
Step 2: provides functionality to create a SQL table,
insert odds into it by putting our odds_data that we fetched
from our API, and then also fetching our data that we have inserted.
This works with our Step 1, since we are now taking the data which we have
fetched from our API in Step 1 and now putting it into our SQL database.
"""


class OddsSQLHandler:
    def __init__(self, db_name = "odds_data.db"):
        #creates a CONNECTION OBJECT to our sql database
        self.conn = sqlite3.connect(db_name)
        self.cursor= self.conn.cursor()
        self.create_table()

    def create_table(self):
        """
        We create our tables with the given column types.
        We use PRIMARY KEY to prevent duplicates. However,
        there is an issue because, what if we want to update
        our data if the odds have changed for a specific event?
        The solution is that for insert_odds, we apply ON CONFLICT
        to replace. Therefore, there is no issue, and there will
        be no duplicates. This was pasted from ChatGPT since I am not
        feeling like writing all of this.
        """
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS odds (
                event_id TEXT,
                sport_key TEXT,
                sport_title TEXT,
                commence_time TEXT,
                home_team TEXT,
                away_team TEXT,
                bookmaker TEXT,
                market_type TEXT,
                team TEXT,
                odds REAL,
                last_update TEXT,
                PRIMARY KEY (event_id, bookmaker, market_type, team)
            )
        ''')
        self.conn.commit()

    def insert_odds(self, odds_data):
        for event in odds_data:
            event_id = event["id"]
            sport_key = event["sport_key"]
            sport_title = event["sport_title"]
            commence_time = event["commence_time"]
            home_team = event["home_team"]
            away_team = event["away_team"]

            for bookmaker in event["bookmakers"]:
                bookmaker_name = bookmaker["title"]
                last_update = bookmaker["last_update"]

                for market in bookmaker["markets"]:
                    market_type = market["key"]

                    for outcome in market["outcomes"]:
                        team = outcome["name"]
                        odds = outcome["price"]

                        self.cursor.execute('''
                            INSERT INTO odds (event_id, sport_key, sport_title, commence_time, home_team, away_team, bookmaker, market_type, team, odds, last_update)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(event_id, bookmaker, market_type, team) DO UPDATE SET
                                odds=excluded.odds,
                                last_update=excluded.last_update
                        ''', (event_id, sport_key, sport_title, commence_time, home_team, away_team, bookmaker_name, market_type, team, odds, last_update))

        self.conn.commit()

    def fetch_all_odds(self):
        self.cursor.execute("SELECT * FROM odds")
        return self.cursor.fetchall()

    def close_connection(self):
        self.conn.close()







