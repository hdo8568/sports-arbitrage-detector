## One-time fix for previous problem

import sqlite3

conn = sqlite3.connect("odds_data.db")
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS arbitrage_bets")
conn.commit()
conn.close()

print("✅ arbitrage_bets table dropped!")
