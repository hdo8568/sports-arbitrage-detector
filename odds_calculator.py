#odds_calculator.py
# american_to_decimal
# decimal_to_american
# calculate_implied_probability
# calculate_no_vig_probabilities
# calculate_vig
# convert_odds
class OddsCalculator:
    @staticmethod
    def american_to_decimal(american_odds):
        """
        Convert American odds to decimal odds
        :param american_odds: American odds (e.g., +150 or -150)
        :return: Decimal odds (e.g., 2.50 or 1.67)
        """
        try:
            if american_odds > 0:
                return (american_odds / 100) + 1
            else:
                return (100 / abs(american_odds)) + 1
        except (TypeError, ZeroDivisionError):
            raise ValueError("Invalid American odds value")

    @staticmethod
    def decimal_to_american(decimal_odds):
        """
        Convert decimal odds to American odds
        :param decimal_odds: Decimal odds (e.g., 2.50)
        :return: American odds (e.g., +150 or -150)
        """
        try:
            if decimal_odds <= 1:
                raise ValueError("Decimal odds must be greater than 1")

            if decimal_odds >= 2:
                return round((decimal_odds - 1) * 100)
            else:
                return round(-100 / (decimal_odds - 1))
        except (TypeError, ZeroDivisionError):
            raise ValueError("Invalid decimal odds value")

    @staticmethod
    def calculate_implied_probability(odds, odds_format="decimal"):
        """
        Convert odds to implied probability.
        :param odds: Odds value (decimal or American)
        :param odds_format: 'decimal' or 'american'
        :return: Implied probability (e.g., 0.555...)
        """
        try:
            if odds_format == "american":
                decimal_odds = OddsCalculator.american_to_decimal(odds)
            else:
                decimal_odds = float(odds)

            if decimal_odds <= 0:
                raise ValueError("Invalid odds value")

            return 1 / decimal_odds
        except (TypeError, ZeroDivisionError):
            raise ValueError("Invalid odds value")

    @staticmethod
    def calculate_no_vig_probabilities(implied_probs):
        """
        Remove the bookmaker's vig (margin) and calculate fair probabilities.
        :param implied_probs: Dictionary of team -> implied probability
        :return: No-vig probabilities
        """
        try:
            if not implied_probs:
                raise ValueError("Empty probabilities dictionary")

            total = sum(implied_probs.values())

            if total <= 0:
                raise ValueError("Total probabilities must be positive")

            return {team: prob / total for team, prob in implied_probs.items()}
        except (TypeError, ZeroDivisionError):
            raise ValueError("Invalid probability values")

    @staticmethod
    def calculate_vig(implied_probs):
        """
        Calculate the vig (juice) from a set of implied probabilities
        :param implied_probs: Dictionary of team -> implied probability
        :return: Vig as a percentage (e.g., 0.05 for 5% vig)
        """
        try:
            total_prob = sum(implied_probs.values())
            return total_prob - 1
        except (TypeError):
            raise ValueError("Invalid probability values")

    @staticmethod
    def convert_odds(odds, from_format="american", to_format="decimal"):
        """
        Convert odds between different formats
        :param odds: Odds value to convert
        :param from_format: Original format ('american' or 'decimal')
        :param to_format: Target format ('american' or 'decimal')
        :return: Converted odds value
        """
        if from_format == to_format:
            return odds

        if from_format == "american" and to_format == "decimal":
            return OddsCalculator.american_to_decimal(odds)
        elif from_format == "decimal" and to_format == "american":
            return OddsCalculator.decimal_to_american(odds)
        else:
            raise ValueError("Invalid odds format specified")