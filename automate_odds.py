#automate_odds.py
# Using OddsAPIHandler and OddsSQLHandler objects, we 
# fetch odds from an API and then store those odds into our 
# SQL object.
# We do so every 600 seconds, and the SQL database is then
# appended with something every 10 minutes.

import time
from OddsAPIHandler import OddsAPIHandler
from OddsSQLHandler import OddsSQLHandler
from arbitrage import detect_arbitrage, save_arbitrage_to_db
from email_alerts import send_arbitrage_email


 
#with open("/home/ec2-user/test_cron.txt", "w") as f:
    #f.write("Cron job ran!\n")

#with open("/home/ec2-user/test_cron.txt", "a") as f:
    #f.write("Cron started\n")

print("Top of script reached", flush=True)



api_handler = OddsAPIHandler()
db_handler = OddsSQLHandler()

def fetch_and_store_odds():
    print("Fetching odds...", flush=True)
    odds_data = api_handler.get_odds("basketball_nba")

    if odds_data:
        db_handler.insert_odds(odds_data)
        print("Odds successfully stored.", flush=True)

        db_handler.delete_old_events()
        print("Passed odds already removed.", flush=True)

        arbitrage_bets = detect_arbitrage(odds_data)
        if arbitrage_bets:
            print(f"Found {len(arbitrage_bets)} arbitrage opportunities.", flush=True)
            save_arbitrage_to_db(arbitrage_bets)
            send_arbitrage_email(arbitrage_bets)

        else:
            print("No arbitrage opportunities found.", flush=True)
    else:
        print("No odds data retrieved.", flush=True)

INTERVAL = 600

if __name__ == "__main__":
    while True:
        fetch_and_store_odds()
        print("Waiting for next update...", flush=True)
        time.sleep(INTERVAL)

