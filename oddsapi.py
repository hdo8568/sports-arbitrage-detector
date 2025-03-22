#oddsapi.py
# Fetches data from API URL. Extracrts only certain parameters,
# displays number of requests remaining and those used.
# Lastly, parse json file and add each parameter type to 
# corresponding column in panda dataframe. Then, we can
# print out the panda dataframe.


import requests
import json
import pandas as pd

API_KEY = "20767e49a8e749476d531a49ff701e6e"

# Setting parameters for NBA Basketball odds and spreads
SPORT = 'basketball_nba' # NBA sport key
REGIONS = 'us' # Focusing on US region
MARKETS = 'spreads' # Focusing on spreads market
ODDS_FORMAT = 'decimal' # Using decimal format for odds
DATE_FORMAT = 'iso' # Using ISO format for dates

# Fetching in-season sports (optional step, but useful for confirmation)
sports_response = requests.get(
    'https://api.the-odds-api.com/v4/sports',
    params={'api_key': API_KEY}
)

"""
if sports_response.status_code == 200:
    print('List of in season sports:', sports_response.json())
else:
    print(f'Failed to get sports: status_code {sports_response.status_code}, response body {sports_response.text}')
"""

odds_response = requests.get(
    f'https://api.the-odds-api.com/v4/sports/{SPORT}/odds',
    params = {
    'api_key' : API_KEY,
    'regions' : REGIONS,
    'markets' : MARKETS,
    'oddsFormat': ODDS_FORMAT,
    'dateFormat' : DATE_FORMAT,
    }
)

if odds_response.status_code == 200:
    odds_json = odds_response.json()
    print('Number of NBA events:', len(odds_json))
    print(odds_json)
    print("Remaining requests:", odds_response.headers['x-requests-remaining'])
    print("Used request", odds_response.headers['x-requests-used'])
else:
    print(f'Failed to get odds: status_code {odds_response.status_code}, response body {odds_response.text}')



odds_data = odds_json
events = []
for event in odds_data:
    event_id = event['id']
    event_sport_key = event['sport_key']
    event_sport_title = event['sport_title']
    event_commence_time = event['commence_time']
    event_home_team = event['home_team']
    event_away_team = event['away_team']
    for bookmaker in event['bookmakers']:
        bookmaker_key = bookmaker['key']
        bookmaker_title = bookmaker['title']
        bookmaker_last_update = bookmaker['last_update']
        for market in bookmaker['markets']:
            market_key = market['key']
            market_last_update = market['last_update']
            for outcome in market['outcomes']:
                outcome_name = outcome['name']
                outcome_price = outcome['price']

                events.append([event_id, event_sport_key, event_sport_title,
                               event_commence_time, event_home_team,
                               event_away_team, bookmaker_key, bookmaker_title,
                               bookmaker_last_update, market_key, market_last_update,
                               outcome_name, outcome_price])

columns = ['Event ID', 'Event Sport Key', 'Event Sport Title', 'Event Commence Time',
           'Event Home Team', 'Event Away Team', 'Bookmaker Key', 'Bookmaker Title',
           'Bookmaker Last Update', 'Market Key', 'Market Last Update', 'Outcome Name',
           'Outcome Price']

df = pd.DataFrame(events, columns = columns)
print(df)
