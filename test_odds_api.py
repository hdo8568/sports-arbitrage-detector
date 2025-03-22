from OddsAPIHandler import OddsAPIHandler
from OddsSQLHandler import OddsSQLHandler
from arbitrage import detect_arbitrage, save_arbitrage_to_db  # Import arbitrage functions

"""
There will be too many things outputted, so best practice
is to comment out print(odds_data) or step 2 test and do
one at a time.
"""

# Step 1 test
api_handler = OddsAPIHandler()
odds_data = api_handler.get_odds("basketball_nba")
print(odds_data)

# Step 2 test: Inserting odds data into the database
sql_handler = OddsSQLHandler("test_odds.db")
sql_handler.insert_odds(odds_data)
all_odds = sql_handler.fetch_all_odds()

# Print all odds fetched from the database
for row in all_odds:
    print(row)

# Step 3: Detect arbitrage opportunities
print("Detecting arbitrage opportunities...")
arbitrage_bets = detect_arbitrage(odds_data)

if arbitrage_bets:
    print(f"Found {len(arbitrage_bets)} arbitrage opportunities!")
    for bet in arbitrage_bets:
        print(f"Event: {bet['home_team']} vs {bet['away_team']}")
        print(f"Best Odds: {bet['best_odds']}")
        print(f"Profit Percentage: {bet['profit_percentage']}%")
        print(f"Bookmakers: {bet['bookmakers']}\n")
    # Optionally save the arbitrage opportunities to the database
    save_arbitrage_to_db(arbitrage_bets)
else:
    print("No arbitrage opportunities found.")

sql_handler.close_connection()
