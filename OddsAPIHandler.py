#OddsAPIHandler.py
import requests
import json

#Step 1: We are requesting the odd by calling the API from the
#GET odds portion from the link: https://the-odds-api.com/liveapi/guides/v4/#parameters-2,
#which provides us with the query parameters for the different queries.
#The next step is Step 2, where we will store the data from the method
#get_odds to our SQL database

class OddsAPIHandler:

    def __init__(self, api_key = "68994e1e474031a43c0644933b8be139",
                 sport_key = "basketball_nba", region = "us",
                 markets = "h2h,spreads,totals", odds_format = "decimal",
                 date_format = "iso"):
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4/sports/"
        #our self params denote our query parameters, which we
        #can find here: https://the-odds-api.com/liveapi/guides/v4/#parameters-2
        #just do ctrl f "parameters"
        #The query parameters are:
        #sport, apiKey, regions, markets, dateFormat, oddsFormat,
        #eventIds, bookmakers, commenceTimeFrom, commenceTimeTo,
        #includeLinks, includeSids, includeBetLimits
        #the final three contain boolean values, if true we include
        #links, source IDs, and BetLimits, respectively
        #We are using this set of parameters because we are doing
        #GET odds, since we have to collect odds
        self.params = {
            "api_key": self.api_key,
            "regions": region,
            "markets": markets,
            "oddsFormat": odds_format,
            "dateFormat": date_format
        }

    def handle_error(self, response):
        print(f"API Error {response.status_code}: {response.text}")
        return None

    def get_odds(self, sport = "basketball_nba"):
        url = f"{self.base_url}/{sport}/odds"
        response = requests.get(url, params = self.params)
        if response.status_code == 200:
            return response.json()
        else:
            return self.handle_error(response)

