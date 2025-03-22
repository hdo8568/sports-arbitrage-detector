##data_handler.py

class InMemoryDataHandler:
    def __init__(self):
        self.events = []  # A list to store odds data (each event is a dictionary)

    def load_data(self, odds_data):
        """
        Load odds data into the handler.
        :param odds_data: List of dictionaries, each representing an event
        """
        self.events = odds_data

    def get_events(self):
        """
        Retrieve all loaded events.
        :return: List of all events
        """
        return self.events

    def filter_events_by_sport(self, sport_key):
        """
        Filter events by sport (e.g., 'basketball_nba').
        :param sport_key: Sport key to filter by
        :return: Filtered list of events
        """
        return [event for event in self.events if event.get("sport_key") == sport_key]

    def filter_events_by_team(self, team_name):
        """
        Filter events to find those involving a specific team.
        :param team_name: Name of the team to search for
        :return: Filtered list of events
        """
        return [event for event in self.events if team_name in event.get("teams", [])]

    def filter_events_by_bookmaker(self, bookmaker):
        """
        Filter events to include only those with odds from a specific bookmaker.
        :param bookmaker: Name of the bookmaker (e.g., 'draftkings')
        :return: Filtered list of events
        """
        return [event for event in self.events if bookmaker in event.get("odds", {})]

    def sort_events_by_odds(self, team_name, descending=True):
        """
        Sort events by the odds of a specific team.
        :param team_name: Name of the team
        :param descending: Sort in descending order (default: True)
        :return: Sorted list of events
        """
        return sorted(
            self.events,
            key=lambda event: event.get("odds", {}).get(team_name, float("-inf")),
            reverse=descending
        )

    def get_best_odds(self):
        """
        Get the best odds for each team across all bookmakers.
        :return: Dictionary of team -> best odds
        """
        best_odds = {}

        for event in self.events:
            for bookmaker, teams_odds in event.get("odds", {}).items():
                # Ensure that odds are stored as a nested dictionary
                if isinstance(teams_odds, dict):
                    for team, odds in teams_odds.items():
                        if team not in best_odds or odds > best_odds[team]:
                            best_odds[team] = odds
                else:
                    print(f"Warning: Unexpected odds format in event {event['event']} (Bookmaker: {bookmaker})")

        return best_odds



"""
    def get_best_odds(self):
        best_odds = {}
        for event in self.events:
            for team, odds in event.get("odds", {}).items():
                if team not in best_odds or odds > best_odds[team]:
                    best_odds[team] = odds
        return best_odds"
"""
