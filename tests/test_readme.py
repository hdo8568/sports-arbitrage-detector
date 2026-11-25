from pathlib import Path

from promo_math import effective_odds, hedge

README = (Path(__file__).parent.parent / "README.md").read_text()


def test_readme_has_boost_desk_section():
    assert "## Boost Desk" in README
    assert "python boost_desk.py add" in README
    assert "python boost_desk.py rank" in README
    assert "BOOKS=" in README


def test_readme_worked_example_matches_the_math():
    # The README example: FanDuel 50% profit boost on the Celtics at 2.70, $50 max,
    # hedged on the Lakers at 1.48. The numbers written there must be what the code says.
    odds = effective_odds("profit_boost", boost_pct=50, base_odds=2.70)
    result = hedge("profit_boost", 50, odds, 1.48)
    assert f"{odds:.2f}" in README
    assert f"${result['hedge_stake']:.2f}" in README
    assert f"${result['locked_profit']:.2f}" in README
