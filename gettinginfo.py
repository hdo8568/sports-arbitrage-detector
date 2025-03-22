#gettinginfo.py

# As we have it right now, we have three kinds of data that we 
# are extracting. We are extracting the title/key for each sport 
# that we can get at the current iteration. 
# Next, we get the available sports books in our region for basketball,
# which is the USA.
# Last, we get all available markets in the US for basketball.

import requests

API_KEY = "20767e49a8e749476d531a49ff701e6e"

sports_response = requests.get(
    'https://api.the-odds-api.com/v4/sports',
    params={'api_key': API_KEY}
)
if sports_response.status_code == 200:
    sports = sports_response.json()
    for sport in sports:
        print(sport['title'], ":", sport['key'])
else:
    print(f"Error: {sports_response.status_code}, {sports_response.text}")

### print('List of in season sports:', sports_response.json())


print("\n")
print("\n")
print("\n")


regions_response = requests.get(
    'https://api.the-odds-api.com/v4/sports/basketball_nba/odds',  # Use an actual sport with odds
    params={'api_key': API_KEY, 'regions': 'us'}
)
if regions_response.status_code == 200:
    regions_data = regions_response.json()
    regions_set = set() ##stores empty set for us to fill
    for event in regions_data:
        if 'bookmakers' in event:
            for bookmaker in event['bookmakers']:
                regions_set.add(bookmaker['title'])
        else:
            print("Seemed to have error with bookmakers")
            break
    print("Available sportsbooks", regions_set)
else:
    print(f"Error: {regions_response.status_code}, {regions_response.text}")


print("\n")
print("\n")
print("\n")



markets_response = requests.get(
    'https://api.the-odds-api.com/v4/sports/basketball_nba/odds',  # Use a valid odds endpoint
    params={'api_key': API_KEY, 'regions': 'us'}
)
if markets_response.status_code == 200:
    odds_data = markets_response.json()

    markets_set = set()
    print("\nAvailable Markets:")
    for event in odds_data:
        if 'bookmakers' in event:
            for bookmaker in event.get('bookmakers', []):  # Ensure bookmakers exist
                for market in bookmaker.get('markets', []):  # Ensure markets exist
                    markets_set.add(market['key'])  # Add market key to set
        else:
            print("bookmakers has another error")
            break

        for market in sorted(markets_set):
            print(market)

else:
    print(f"Error: {markets_response.status_code}, {markets_response.text}")


